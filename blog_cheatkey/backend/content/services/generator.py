# d:\BlogCheatKey\blog_cheatkey_v2\blog_cheatkey\backend\content\services\generator.py
import re
import json
import logging
import time
import traceback
from urllib.parse import urlparse
from django.conf import settings
from konlpy.tag import Okt
from anthropic import Anthropic
from backend.research.models import ResearchSource, StatisticData
from backend.key_word.models import Keyword, Subtopic
from backend.content.models import BlogContent, MorphemeAnalysis
from backend.accounts.models import User
from .substitution_generator import SubstitutionGenerator
from .morpheme_analyzer import MorphemeAnalyzer 

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    Claude API를 사용한 블로그 콘텐츠 생성 서비스
    - 생성과 동시에 최적화 조건을 만족하는 콘텐츠 생성
    """
    
    def __init__(self):
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.model = "claude-3-5-sonnet-20240620" # Model updated
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.okt = Okt()
        self.max_retries = 3 # API 호출 재시도 횟수
        self.retry_delay = 5 # 재시도 간격 (초)
        self.substitution_generator = SubstitutionGenerator()
        self.morpheme_analyzer = MorphemeAnalyzer() # Instance of the new MorphemeAnalyzer
    
    def generate_content(self, keyword_id, user_id, target_audience=None, business_info=None, custom_morphemes=None, subtopics_list=None):
        """
        키워드 기반 블로그 콘텐츠 생성 (최적화 조건 충족)
        
        Args:
            keyword_id (int): 키워드 ID
            user_id (int): 사용자 ID
            target_audience (dict): 타겟 독자 정보
            business_info (dict): 사업자 정보
            custom_morphemes (list): 사용자 지정 형태소 목록
            subtopics_list (list): 명시적으로 전달된 소제목 목록 (기본값 None)
            
        Returns:
            int: 생성된 BlogContent 객체의 ID, 실패 시 None
        """
        for attempt in range(self.max_retries):
            try:
                keyword_obj = Keyword.objects.get(id=keyword_id)
                keyword_text = keyword_obj.keyword
                user = User.objects.get(id=user_id)
                
                current_subtopics = subtopics_list
                if current_subtopics is None:
                    current_subtopics = list(keyword_obj.subtopics.order_by('order').values_list('title', flat=True))
                
                news_sources = ResearchSource.objects.filter(keyword=keyword_obj, source_type='news')
                academic_sources = ResearchSource.objects.filter(keyword=keyword_obj, source_type='academic')
                general_sources = ResearchSource.objects.filter(keyword=keyword_obj, source_type='general')
                statistics = StatisticData.objects.filter(source__keyword=keyword_obj)
                
                existing_content = BlogContent.objects.filter(
                    keyword=keyword_obj, 
                    user=user, 
                    title__contains="(생성 중...)"
                ).order_by('-created_at').first()
                
                data_for_prompt = {
                    "keyword": keyword_text,
                    "subtopics": current_subtopics,
                    "target_audience": target_audience or {
                        "primary": keyword_obj.main_intent or "일반 사용자",
                        "pain_points": keyword_obj.pain_points or ["정보 부족"]
                    },
                    "business_info": business_info or {
                        "name": user.username,
                        "expertise": user.profile.expertise if hasattr(user, 'profile') and hasattr(user.profile, 'expertise') else "관련 분야 전문가"
                    },
                    "custom_morphemes": custom_morphemes, 
                    "research_data": self._format_research_data(
                        news_sources, academic_sources, general_sources, statistics
                    )
                }
                
                logger.info(f"콘텐츠 생성 API 호출 시작 (시도 {attempt+1}/{self.max_retries}): 키워드={keyword_text}, 사용자={user.username}")
                logger.info(f"콘텐츠 생성에 사용되는 소제목: {current_subtopics}")

                prompt = self._create_optimized_content_prompt(data_for_prompt)
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                logger.info("콘텐츠 생성 API 호출 완료")
                
                generated_content_text = response.content[0].text
                
                initial_analysis = self.morpheme_analyzer.analyze(generated_content_text, keyword_text, custom_morphemes)
                
                final_content_to_save = generated_content_text
                final_analysis_for_db = initial_analysis

                if not initial_analysis['is_fully_optimized']:
                    logger.info("1차 생성 콘텐츠 최적화 필요. 추가 최적화 시도.")
                    logger.info(f"1차 검증 결과: 글자수={initial_analysis['char_count']} (유효: {initial_analysis['is_valid_char_count']}), 목표형태소 유효={initial_analysis['is_valid_morphemes']}")
                    
                    optimization_prompt = self._create_verification_optimization_prompt(
                        generated_content_text, 
                        keyword_text, 
                        custom_morphemes,
                        initial_analysis
                    )
                    
                    optimization_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        temperature=0.5,
                        messages=[{"role": "user", "content": optimization_prompt}]
                    )
                    
                    optimized_content_after_verify_prompt = optimization_response.content[0].text
                    analysis_after_verify_prompt = self.morpheme_analyzer.analyze(optimized_content_after_verify_prompt, keyword_text, custom_morphemes)
                    
                    logger.info(f"추가 최적화 시도 후 결과: 글자수={analysis_after_verify_prompt['char_count']}, 목표형태소 유효={analysis_after_verify_prompt['is_valid_morphemes']}")

                    if self.morpheme_analyzer.is_better_optimization(analysis_after_verify_prompt, initial_analysis):
                        final_content_to_save = optimized_content_after_verify_prompt
                        final_analysis_for_db = analysis_after_verify_prompt
                        logger.info("추가 최적화된 콘텐츠 사용: 더 나은 결과")
                    else:
                        logger.info("1차 생성 콘텐츠 사용: 추가 최적화 후 개선되지 않음")
                
                content_with_references = self._add_references(final_content_to_save, data_for_prompt['research_data'])
                mobile_formatted_content = self._format_for_mobile(content_with_references)
                references_list = self._extract_references(content_with_references)
                
                if existing_content:
                    existing_content.delete()
                
                blog_content = BlogContent.objects.create(
                    user=user,
                    keyword=keyword_obj,
                    title=f"{keyword_text} 완벽 가이드", 
                    content=content_with_references,
                    mobile_formatted_content=mobile_formatted_content,
                    references=references_list,
                    char_count=final_analysis_for_db['char_count'],
                    is_optimized=final_analysis_for_db['is_fully_optimized'] 
                )
                
                logger.info("형태소 분석 결과 저장 시작")
                if 'morpheme_analysis' in final_analysis_for_db and 'counts' in final_analysis_for_db['morpheme_analysis']:
                    for morpheme, info in final_analysis_for_db['morpheme_analysis']['counts'].items():
                        MorphemeAnalysis.objects.create(
                            content=blog_content,
                            morpheme=morpheme,
                            count=info.get('count', 0),
                            is_valid=info.get('is_valid', False),
                            morpheme_type=info.get('type', 'unknown') # Save morpheme type
                        )
                
                logger.info(f"콘텐츠 생성 완료: ID={blog_content.id}")
                return blog_content.id
                    
            except Exception as e:
                logger.error(f"콘텐츠 생성 중 오류 발생 (시도 {attempt+1}/{self.max_retries}): {str(e)}")
                logger.error(traceback.format_exc())
                
                if 'overloaded_error' in str(e).lower() and attempt < self.max_retries - 1:
                    logger.warning(f"서버가 혼잡합니다. {self.retry_delay}초 후 재시도합니다...")
                    time.sleep(self.retry_delay)
                elif attempt == self.max_retries - 1:
                    logger.error("최대 재시도 횟수 도달. 콘텐츠 생성 실패.")
                    if existing_content:
                        existing_content.title = f"{keyword_text} (생성 실패)"
                        existing_content.content = f"콘텐츠 생성 중 오류 발생: {str(e)}"
                        existing_content.save()
                    return None
                else:
                    time.sleep(self.retry_delay)
        
        logger.error(f"모든 ({self.max_retries}회) 시도 후에도 콘텐츠 생성 실패: 키워드 ID {keyword_id}")
        return None
                    
    def _format_research_data(self, news_sources, academic_sources, general_sources, statistics):
        research_data = {'news': [], 'academic': [], 'general': [], 'statistics': []}
        
        for source_type, sources in [('news', news_sources), ('academic', academic_sources), ('general', general_sources)]:
            for source in sources.order_by('-published_date')[:5]:
                research_data[source_type].append({
                    'title': source.title, 'url': source.url, 'snippet': source.snippet,
                    'date': source.published_date.isoformat() if source.published_date else '',
                    'source': source.author or urlparse(source.url).netloc
                })
        
        for stat in statistics.order_by('-source__published_date')[:5]:
            research_data['statistics'].append({
                'value': stat.value, 'context': stat.context, 'pattern_type': stat.pattern_type,
                'source_url': stat.source.url, 'source_title': stat.source.title,
                'source': stat.source.author or urlparse(stat.source.url).netloc,
                'date': stat.source.published_date.isoformat() if stat.source.published_date else ''
            })
        return research_data
    
    def _create_optimized_content_prompt(self, data):
        keyword = data["keyword"]
        custom_morphemes = data.get("custom_morphemes", [])

        # Use MorphemeAnalyzer to get categorized morphemes and their target ranges
        dummy_analysis = self.morpheme_analyzer.analyze("", keyword, custom_morphemes)
        base_morphemes = dummy_analysis['morpheme_analysis']['target_morphemes']['base']
        compound_morphemes = dummy_analysis['morpheme_analysis']['target_morphemes']['compound']

        target_min_base_morph = self.morpheme_analyzer.target_min_base_count
        target_max_base_morph = self.morpheme_analyzer.target_max_base_count
        target_min_compound_morph = self.morpheme_analyzer.target_min_compound_count
        target_max_compound_morph = self.morpheme_analyzer.target_max_compound_count

        target_min_chars = self.morpheme_analyzer.target_min_chars
        target_max_chars = self.morpheme_analyzer.target_max_chars

        keyword_instruction_parts = []
        
        # Instructions for base morphemes
        if base_morphemes:
            keyword_instruction_parts.append(f"- 핵심 기본 형태소 ({', '.join(base_morphemes)}): 각각 {target_min_base_morph}-{target_max_base_morph}회 이내로 자연스럽게 사용 (예: '엔진오일종류'에서 '엔진', '오일', '종류' 각각 카운트)")

        # Instructions for compound morphemes/phrases
        if compound_morphemes:
            keyword_instruction_parts.append(f"- 복합 키워드 및 구문 ({', '.join(compound_morphemes)}): 각각 {target_min_compound_morph}-{target_max_compound_morph}회 이내로 자연스럽게 사용 (예: '엔진오일', '엔진오일종류')")
        
        keyword_instruction = "\n".join(keyword_instruction_parts)
        
        research_text = ""
        target_audience = data.get('target_audience', {})
        business_info = data.get('business_info', {})
        research_data_dict = data.get('research_data', {})

        if isinstance(research_data_dict, dict):
            news = research_data_dict.get('news', [])[:2]
            academic = research_data_dict.get('academic', [])[:2]
            general = research_data_dict.get('general', [])[:2]
            
            if news:
                research_text += "📰 뉴스 자료:\n"
                for item in news: research_text += f"- {item.get('title', '')} ({item.get('source', '')}, {item.get('date','')}): {item.get('snippet', '')}\n"
            if academic:
                research_text += "\n📚 학술 자료:\n"
                for item in academic: research_text += f"- {item.get('title', '')} ({item.get('source', '')}, {item.get('date','')}): {item.get('snippet', '')}\n"
            if general:
                research_text += "\n🔍 일반 자료:\n"
                for item in general: research_text += f"- {item.get('title', '')} ({item.get('source', '')}, {item.get('date','')}): {item.get('snippet', '')}\n"

        statistics_text = ""
        if isinstance(research_data_dict.get('statistics'), list) and research_data_dict.get('statistics'):
            statistics_text = "\n💡 활용 가능한 통계 자료 (최소 1개 이상 본문에 자연스럽게 인용):\n"
            for stat in research_data_dict['statistics'][:3]:
                date_info = f" ({stat.get('date', '')[:4]}년)" if stat.get('date') and len(stat.get('date')) >=4 else ""
                statistics_text += f"- {stat.get('context', '')}{date_info} (출처: {stat.get('source_title', stat.get('source','알 수 없음'))})\n"
        else:
            statistics_text = "\n(활용 가능한 특정 통계 자료가 없습니다. 일반적인 경향이나 중요성을 언급해주세요.)\n"


        optimization_requirements = f"""
        ⚠️ 중요: 다음 최적화 조건을 반드시 준수해야 합니다.

        1. 글자수 조건: 정확히 {target_min_chars}-{target_max_chars}자 (공백 제외, 참고자료 섹션 제외)
        - 내용을 간결하게 유지하거나 필요시 확장하여 이 범위에 맞추기

        2. 키워드 및 주요 형태소 출현 횟수 조건:
        {keyword_instruction}
        - 중요: Ctrl+F로 검색했을 때 위에 언급된 모든 키워드와 형태소가 각각 지정된 범위 내에 있어야 합니다!

        3. 키워드 최적화 방법:
        - 지시어 활용: "{keyword}는" → "이것은" 등
        - 자연스러운 생략: 문맥상 이해 가능한 경우 생략
        - 동의어/유사어 대체: 과다 사용된 단어를 적절한 동의어로 대체 (단, 목표 형태소는 유지)

        ✓ 최종 검증: 생성 완료 후, 위에 언급된 모든 목표 키워드/형태소가 **각각** 지정된 범위 내에 있는지, 글자수가 맞는지 **반드시** 재확인하세요. **최대 횟수를 단 1회라도 초과해서는 안 됩니다. 차라리 최소 횟수보다 약간 부족한 것이 낫습니다.** 이 규칙은 절대적입니다.
        """
        logger.info(f"프롬프트에 전달되는 소제목: {data.get('subtopics', [])}")
        subtopics_for_prompt = data.get('subtopics', [])
        subtopic_lines = ""
        if subtopics_for_prompt:
            for i, st_title in enumerate(subtopics_for_prompt):
                subtopic_lines += f"        ### {st_title}\n"
        else:
            subtopic_lines = "        (소제목 없이 자유롭게 본론 구성)\n"


        prompt = f"""
        다음 조건들을 준수하여 전문성과 친근함이 조화된, 읽기 쉽고 실용적인 블로그 글을 작성해주세요:

        {optimization_requirements}

        필수 활용 자료 (본문에 자연스럽게 인용):
        {research_text if research_text else "(제공된 특정 뉴스/학술/일반 자료 없음. 일반적인 정보 활용 가능)"}
        
        통계 자료 (본문에 자연스럽게 인용):
        {statistics_text}

        **중요 참고자료 인용 지침:**
        1. 본문에서 [1], [2]와 같은 인용번호 표시는 절대 사용하지 마세요.
        2. 대신 "X 보고서에 따르면" 또는 "Y 연구 결과에 의하면" 등 출처 이름을 직접 언급하는 방식으로 인용하세요. (예: "한국석유공사 보고서에 따르면...")
        3. 참고자료의 출처명과 내용을 정확하게 언급해주세요.
        4. 링크는 글 하단의 참고자료 섹션에 자동으로 추가되므로 본문에 URL을 포함하지 마세요.
        5. 각 소제목 섹션에서 (또는 본론 전반에 걸쳐) 관련 참고자료를 출처를 명시하여 인용하세요.

        1. 글의 구조와 형식
        - 전체 구조: 서론(약 20%) - 본론(약 60%) - 결론(약 20%)
        - 각 소제목은 ### 마크다운으로 표시
        - 소제목 구성:
{subtopic_lines}
        - 전체 길이: {target_min_chars}-{target_max_chars}자 (공백 제외)

        2. [필수] 서론 작성 가이드 (전문성 및 흥미 유발 강화)
        서론은 다음 3단계 흐름을 반드시 따라야 합니다.
        1. 문제 제기 및 공감: 독자의 가장 큰 고민({', '.join(target_audience.get('pain_points', []))})을 직접 언급하며 시작하세요. 가능하다면 제공된 통계/연구 자료를 인용하여 문제의 심각성을 부각시키세요. (예: "혹시 {keyword} 때문에 골치 아프신가요? 최근 A 연구에 따르면, 많은 분들이 비슷한 어려움을 겪고 있습니다.")
        2. 전문가로서의 권위 제시 및 해결책 암시: {business_info.get('name', '저희')}의 전문성({business_info.get('expertise', '관련 분야의 깊은 경험')})을 간결하게 드러내세요. 단순히 '해결해 주겠다'가 아니라, '왜' 우리가 해결할 수 있는지 보여주는 것이 중요합니다. (예: "지난 N년간 이 분야를 다뤄온 전문가로서, 이 문제의 핵심 원인이 무엇인지 명확히 알고 있습니다. 사실, 대부분의 문제는 간단한 원칙 몇 가지만 알면 해결됩니다.")
        3. 기대감 증폭 및 본문으로 연결: 이 글을 단 5분만 투자해 끝까지 읽으시면, 더 이상 {keyword} 때문에 시간 낭비하지 않고, (독자가 얻을 구체적 이득)을 얻게 되실 겁니다. 본문에서는 그 핵심 비법을 소제목별로 자세히 알려드리겠습니다.")

        3. 글쓰기 스타일
        - 전문가의 지식을 쉽게 설명하듯이 편안한 톤 유지
        - 각 문단은 자연스럽게 다음 문단으로 연결
        - 스토리텔링 요소 활용 가능
        - 실제 사례나 비유를 통해 이해하기 쉽게 설명

        4. 핵심 키워드 활용 (위의 '키워드 및 주요 형태소 출현 횟수 조건' 참고)
        - 주 키워드: {keyword}
        - 각 목표 키워드/형태소를 지정된 범위 내에서 자연스럽게 사용
            
        5. [필수] 참고 자료 활용
        - 본론 전반에 걸쳐 관련 통계/연구 자료를 자연스럽게 인용
        - 인용할 때는 "~에 따르면", "~의 연구 결과", "~의 조사에 따르면" 등 명확한 표현 사용
        - 모든 통계와 수치는 출처를 구체적으로 명시 (예: "2024년 Z 기관의 조사에 따르면...")
        - 가능한 최신 자료를 우선적으로 활용
        - 통계나 수치를 인용할 때는 그 의미나 시사점도 함께 설명

        6. 본론 작성 가이드
        - 각 소제목마다 핵심 주제 한 줄 요약으로 시작 가능
        - 이론 → 사례 → 실천 방법 순으로 구성 가능
        - 참고 자료의 통계나 연구 결과를 자연스럽게 인용
        - 전문적 내용도 쉽게 풀어서 설명
        - 각 섹션 끝에서 다음 섹션으로 자연스러운 연결

        7. 결론 작성 가이드
        - 본론 내용 요약
        - 실천 가능한 다음 단계 제시
        - "{business_info.get('name', '저희')}가 도와드릴 수 있다는 메시지" (선택적)
        - 독자와의 상호작용 유도 (예: 질문, 댓글 요청)

        위 조건들을 바탕으로, 특히 타겟 독자({target_audience.get('primary', '')})의 어려움을 해결하는 데 초점을 맞추어 블로그 글을 작성해주세요.
        """
        return prompt
    
    def _create_verification_optimization_prompt(self, content, keyword, custom_morphemes, verification_result):
        morpheme_analysis_from_analyzer = verification_result.get('morpheme_analysis', {})
        
        base_morphemes = morpheme_analysis_from_analyzer['target_morphemes']['base']
        compound_morphemes = morpheme_analysis_from_analyzer['target_morphemes']['compound']
        current_counts = morpheme_analysis_from_analyzer['counts']

        target_min_base_morph = self.morpheme_analyzer.target_min_base_count
        target_max_base_morph = self.morpheme_analyzer.target_max_base_count
        target_min_compound_morph = self.morpheme_analyzer.target_min_compound_count
        target_max_compound_morph = self.morpheme_analyzer.target_max_compound_count

        target_min_chars = self.morpheme_analyzer.target_min_chars
        target_max_chars = self.morpheme_analyzer.target_max_chars
        
        morpheme_issues = []
        for morpheme in base_morphemes:
            info = current_counts.get(morpheme, {})
            count = info.get('count', 0)
            if not info.get('is_valid', True):
                morpheme_issues.append(f"- 핵심 기본 형태소 '{morpheme}': 현재 {count}회 → 목표 {target_min_base_morph}-{target_max_base_morph}회로 조정 필요")
        
        for morpheme in compound_morphemes:
            info = current_counts.get(morpheme, {})
            count = info.get('count', 0)
            if not info.get('is_valid', True):
                morpheme_issues.append(f"- 복합 키워드/구문 '{morpheme}': 현재 {count}회 → 목표 {target_min_compound_morph}-{target_max_compound_morph}회로 조정 필요")
        
        morpheme_issues_text = "\n".join(morpheme_issues) if morpheme_issues else "모든 목표 형태소가 적정 범위 내에 있습니다."
        
        char_count = verification_result['char_count']
        char_count_guidance = ""
        if char_count < target_min_chars:
            char_count_guidance = f"글자수가 부족합니다. 현재 {char_count}자. {target_min_chars-char_count}자 이상 늘려 {target_min_chars}-{target_max_chars}자로 만들어주세요."
        elif char_count > target_max_chars:
            char_count_guidance = f"글자수가 초과되었습니다. 현재 {char_count}자. {char_count-target_max_chars}자 이상 줄여 {target_min_chars}-{target_max_chars}자로 만들어주세요."
        else:
            char_count_guidance = f"글자수는 적정 범위({target_min_chars}-{target_max_chars}자)입니다. 형태소 조정 시 이 범위를 유지해주세요."
        
        optimization_strategies = self._generate_dynamic_optimization_strategies(keyword, current_counts, base_morphemes + compound_morphemes)
        
        return f"""
        다음 블로그 콘텐츠를 최적화해주세요. 다음 조건을 모두 충족하도록 수정해주세요:
        
        ========== 최적화 목표 ==========
        
        1. 글자수 조건: {target_min_chars}-{target_max_chars}자 (공백 제외)
           {char_count_guidance}
        
        2. 목표 형태소 출현 횟수 조건:
           {morpheme_issues_text}

        3. 키워드 및 형태소 카운팅 방식:
           - 핵심 기본 형태소 (예: '엔진', '오일', '종류'): 문장 내에서 부분적으로 포함되어도 카운트됩니다. (예: '엔진오일종류'에서 '엔진' 1회, '오일' 1회, '종류' 1회)
           - 복합 키워드 및 구문 (예: '엔진오일', '엔진오일종류'): 정확히 해당 구문이 일치해야 카운트됩니다.

        ========== 최적화 전략 ==========
        {optimization_strategies}
        
        ========== 중요 지침 ==========
        
        1. 콘텐츠의 핵심 메시지와 전문성은 유지하세요.
        2. 모든 소제목과 주요 섹션을 유지하세요.
        3. 자연스러운 문체와 흐름을 유지하세요.
        4. 모든 통계 자료 인용과 출처 표시를 유지하세요.
        5. 조정 후에는 반드시 위에 언급된 각 목표 형태소가 지정된 범위 내에서 사용되었는지, 글자수가 맞는지 확인하세요.
        6. 결과물만 제시하고 추가 설명은 하지 마세요.
        
        ========== 원본 콘텐츠 ==========
        {content}
        """
    
    def _generate_dynamic_optimization_strategies(self, keyword, current_morpheme_counts, all_target_morphemes_list):
        excess_morphemes = []
        lacking_morphemes = []
        
        # Use MorphemeAnalyzer to get target ranges for each type
        ma = self.morpheme_analyzer # shorthand
        
        for morpheme in all_target_morphemes_list:
            info = current_morpheme_counts.get(morpheme, {})
            count = info.get('count', 0)
            morpheme_type = info.get('type')

            if morpheme_type == 'base':
                target_min = ma.target_min_base_count
                target_max = ma.target_max_base_count
            elif morpheme_type == 'compound':
                target_min = ma.target_min_compound_count
                target_max = ma.target_max_compound_count
            else: # Should not happen with proper categorization
                continue

            if count > target_max:
                excess_morphemes.append(morpheme)
            elif count < target_min:
                lacking_morphemes.append(morpheme)
        
        strategies = """
        1. 과다 사용된 목표 형태소 감소 방법:
           - 동의어/유사어 대체: (단, 대체어는 목표 형태소가 아니어야 하며, 해당 형태소의 카운팅 방식(부분/정확)을 고려하여 대체)
           - 지시어 사용: "이것", "그것", "해당 내용" 등으로 대체
           - 자연스러운 생략: 문맥상 이해 가능한 경우 생략
           - 다른 표현으로 문장 재구성: 같은 의미를 다른 방식으로 표현
           - 해당 형태소가 포함된 문장 전체를 문맥상 자연스럽게 삭제하거나, 형태소만 제거하여 문장을 간결하게 만드세요.

        2. 부족한 목표 형태소 증가 방법:
           - 구체적인 예시나 사례 추가: 해당 목표 형태소가 포함된 예시 추가
           - 설명 확장: 핵심 개념에 대한 추가 설명 제공 (목표 형태소 사용)
           - 실용적인 팁이나 조언 추가: 목표 형태소가 포함된 팁 제시
           - 기존 문장 분리 또는 확장: 한 문장을 두 개로 나누거나 확장하여 목표 형태소 사용 기회 증가
        """
        
        substitution_text = "\n3. 유용한 대체어 예시 (과다 형태소 감소 시):"
        added_subs = False
        
        # Suggest substitutions for excess morphemes
        for morpheme in excess_morphemes:
            morpheme_substitutions = self.substitution_generator.get_substitutions(keyword, morpheme)
            if morpheme_substitutions:
                substitution_text += f"\n   - '{morpheme}' 대체어: {', '.join(morpheme_substitutions[:3])}"
                added_subs = True
        
        return strategies + (substitution_text if added_subs else "")
        
    def _add_references(self, content, research_data):
        if "## 참고자료" in content: return content
        
        references_to_add = []
        for source_type_key in ['news', 'academic', 'general']:
            for source_item in research_data.get(source_type_key, []):
                if self._find_citation_in_content(content, source_item):
                    if not any(ref['url'] == source_item.get('url') for ref in references_to_add if source_item.get('url')):
                        references_to_add.append({
                            'title': source_item.get('title', '제목 없음'),
                            'url': source_item.get('url', '#'),
                            'source': source_item.get('source', '')
                        })
        
        for stat_item in research_data.get('statistics', []):
            source_url = stat_item.get('source_url', '')
            source_title = stat_item.get('source_title', '')
            if source_url and source_title and (source_title.lower() in content.lower() or (stat_item.get('source','').lower() in content.lower() and stat_item.get('source',''))):
                if not any(ref['url'] == source_url for ref in references_to_add):
                     references_to_add.append({
                        'title': source_title,
                        'url': source_url,
                        'source': stat_item.get('source', '')
                    })

        if not references_to_add: return content
        
        reference_section_text = "\n\n## 참고자료\n"
        for i, ref_item in enumerate(references_to_add, 1):
            ref_source_text = f" - {ref_item['source']}" if ref_item['source'] else ""
            reference_section_text += f"{i}. [{ref_item['title']}]({ref_item['url']}){ref_source_text}\n"
        
        return content.strip() + reference_section_text

    def _extract_references(self, content_with_refs):
        extracted_refs = []
        if "## 참고자료" in content_with_refs:
            refs_section_text = content_with_refs.split("## 참고자료", 1)[1]
            link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)(?: - (.*?))?\n')
            matches = link_pattern.findall(refs_section_text)
            
            for title, url, source in matches:
                extracted_refs.append({
                    'title': title.strip(), 'url': url.strip(),
                    'source': source.strip() if source else ''
                })
        return extracted_refs

    def _format_for_mobile(self, content):
        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(line)
                continue
            
            if in_code_block or \
               stripped_line.startswith(('#', '##', '###')) or \
               not stripped_line or \
               stripped_line.startswith(('- ', '* ', '+ ')) or \
               re.match(r'^\d+\.\s', stripped_line) or \
               stripped_line.startswith('>'):
                formatted_lines.append(line)
                continue
            
            words = line.split()
            current_formatted_line = ""
            for word in words:
                temp_line_char_len = len((current_formatted_line + " " + word).replace(" ", ""))
                if temp_line_char_len > 23 and current_formatted_line:
                    formatted_lines.append(current_formatted_line)
                    current_formatted_line = word
                else:
                    current_formatted_line = (current_formatted_line + " " + word).strip()
            
            if current_formatted_line:
                formatted_lines.append(current_formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _find_citation_in_content(self, content_text, source_info_dict):
        content_lower = content_text.lower()
        
        source_name_candidates = [
            source_info_dict.get('source', '').lower(),
            source_info_dict.get('author', '').lower()
        ]
        source_name_candidates = [name for name in source_name_candidates if name and len(name) > 2]

        for name_candidate in source_name_candidates:
            if name_candidate in content_lower:
                return True
        
        title_lower = source_info_dict.get('title', '').lower()
        if title_lower:
            title_words = title_lower.split()
            for i in range(len(title_words) - 1):
                phrase = " ".join(title_words[i:i+2])
                if len(phrase) > 5 and phrase in content_lower: return True
            if len(title_words) >=3:
                phrase = " ".join(title_words[:3])
                if len(phrase) > 8 and phrase in content_lower: return True

        snippet_lower = source_info_dict.get('snippet', '').lower()
        if snippet_lower:
            numbers_in_snippet = re.findall(r'\d+(?:[.,]\d+)?%?', snippet_lower)
            key_phrases_in_snippet = re.findall(r'\b\w+\s\w+\s\w+\b', snippet_lower)

            citation_keywords = ["따르면", "연구", "조사", "보고서", "발표", "통계", "자료", "제시"]
            for num_in_snip in numbers_in_snippet:
                if num_in_snip in content_lower:
                    idx = content_lower.find(num_in_snip)
                    context_around_num = content_lower[max(0, idx-30):min(len(content_lower), idx+len(num_in_snip)+30)]
                    if any(cit_kw in context_around_num for cit_kw in citation_keywords):
                        return True
            
            for phrase_in_snip in key_phrases_in_snippet:
                if len(phrase_in_snip) > 8 and phrase_in_snip in content_lower:
                     idx = content_lower.find(phrase_in_snip)
                     context_around_phrase = content_lower[max(0, idx-30):min(len(content_lower), idx+len(phrase_in_snip)+30)]
                     if any(cit_kw in context_around_phrase for cit_kw in citation_keywords):
                        return True
        return False
