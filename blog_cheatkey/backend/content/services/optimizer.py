# d:\BlogCheatKey\blog_cheatkey_v2\blog_cheatkey\backend\content\services\optimizer.py
import re
import json
import logging
import time
import random
import traceback
from django.conf import settings
from konlpy.tag import Okt 
from anthropic import Anthropic
from backend.content.models import BlogContent, MorphemeAnalysis
from .formatter import ContentFormatter
from .substitution_generator import SubstitutionGenerator
from .morpheme_analyzer import MorphemeAnalyzer 

logger = logging.getLogger(__name__)

class ContentOptimizer:
    """
    Claude API를 사용한 블로그 콘텐츠 최적화 클래스
    주요 기능: 글자수, 키워드 출현 횟수 확인 및 최적화
    """

    def __init__(self):
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.model = "claude-3-5-sonnet-20240620" # 최신 모델 사용
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.okt = Okt() 
        self.substitution_generator = SubstitutionGenerator()
        self.morpheme_analyzer = MorphemeAnalyzer()

    def optimize_existing_content_v3(self, content_id):
        """
        기존 콘텐츠를 SEO 친화적으로 최적화

        Args:
            content_id (int): BlogContent 모델의 ID

        Returns:
            dict: 최적화 결과
        """
        try:
            blog_content = BlogContent.objects.get(id=content_id)
            original_content_text = blog_content.content # API 호출 전 원본 저장
            keyword = blog_content.keyword.keyword
            custom_morphemes_for_analysis = None # Assuming this is passed from higher level

            logger.info(f"콘텐츠 SEO 최적화 시작 (V3): content_id={content_id}, 키워드={keyword}")

            api_optimized_content = None
            best_api_analysis = self.morpheme_analyzer.analyze(original_content_text, keyword, custom_morphemes_for_analysis) # 초기 분석은 원본 기준

            api_attempts_count = 0

            for attempt in range(3): # Still keep a few API attempts for initial optimization
                api_attempts_count = attempt + 1
                try:
                    content_for_api_prompt = api_optimized_content if api_optimized_content else original_content_text
                    current_analysis_for_prompt = self.morpheme_analyzer.analyze(content_for_api_prompt, keyword, custom_morphemes_for_analysis)

                    if attempt == 0:
                        prompt = self._create_seo_optimization_prompt(content_for_api_prompt, keyword, custom_morphemes_for_analysis, current_analysis_for_prompt)
                        temp = 0.7
                    elif attempt == 1:
                        prompt = self._create_seo_readability_prompt(content_for_api_prompt, keyword, custom_morphemes_for_analysis, current_analysis_for_prompt)
                        temp = 0.5
                    else:
                        prompt = self._create_ultra_seo_prompt(content_for_api_prompt, keyword, custom_morphemes_for_analysis, current_analysis_for_prompt)
                        temp = 0.3
                    
                    logger.info(f"API 최적화 시도 #{attempt+1}/3, temperature={temp}")

                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        temperature=temp,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    current_api_output = response.content[0].text
                    analysis_of_api_output = self.morpheme_analyzer.analyze(current_api_output, keyword, custom_morphemes_for_analysis)
                    
                    logger.info(f"API 시도 #{attempt+1} 결과: 글자수={analysis_of_api_output['char_count']}, 목표형태소 유효={analysis_of_api_output['is_valid_morphemes']}")
                    
                    if self.morpheme_analyzer.is_better_optimization(analysis_of_api_output, best_api_analysis):
                        api_optimized_content = current_api_output
                        best_api_analysis = analysis_of_api_output
                        logger.info(f"새로운 최상의 API 결과 발견: 글자수={best_api_analysis['char_count']}, 목표형태소 유효={best_api_analysis['is_valid_morphemes']}")
                    
                    if best_api_analysis['is_fully_optimized']:
                        logger.info("API 최적화 성공: 모든 조건 충족")
                        break
                        
                except Exception as e:
                    logger.error(f"API 최적화 시도 #{attempt+1} 오류: {str(e)}")
                    logger.error(traceback.format_exc())
                    time.sleep(5)

            content_to_force_optimize = api_optimized_content if api_optimized_content else original_content_text
            
            logger.info("SEO 강제 최적화 시작")
            final_optimized_content = self.enforce_seo_optimization(content_to_force_optimize, keyword, custom_morphemes_for_analysis)
            
            final_analysis = self.morpheme_analyzer.analyze(final_optimized_content, keyword, custom_morphemes_for_analysis)
            logger.info(f"최종 결과: 글자수={final_analysis['char_count']}, 목표형태소 유효={final_analysis['is_valid_morphemes']}")
            
            formatter = ContentFormatter()
            mobile_formatted_content = formatter.format_for_mobile(final_optimized_content)
            
            blog_content.content = final_optimized_content
            blog_content.mobile_formatted_content = mobile_formatted_content
            blog_content.char_count = final_analysis['char_count']
            blog_content.is_optimized = final_analysis['is_fully_optimized']
            
            meta_data = {
                'original_char_count': len(original_content_text.replace(" ", "")),
                'final_char_count': final_analysis['char_count'],
                'is_valid_char_count': final_analysis['is_valid_char_count'],
                'is_valid_morphemes': final_analysis['is_valid_morphemes'],
                'optimization_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                'algorithm_version': 'v3_analyzer_focused_v3', # Updated version
                'api_attempts': api_attempts_count 
            }
            blog_content.meta_data = meta_data
            blog_content.save()
            
            blog_content.morpheme_analyses.all().delete()
            
            if 'morpheme_analysis' in final_analysis and 'counts' in final_analysis['morpheme_analysis']:
                for morpheme, info in final_analysis['morpheme_analysis']['counts'].items():
                    MorphemeAnalysis.objects.create(
                        content=blog_content,
                        morpheme=morpheme,
                        count=info.get('count', 0),
                        is_valid=info.get('is_valid', False),
                        morpheme_type=info.get('type', 'unknown')
                    )
            
            success_message = "콘텐츠가 성공적으로 SEO 최적화되었습니다."
            if not final_analysis['is_fully_optimized']:
                success_message += " (일부 조건 미달성)"
            
            logger.info(f"콘텐츠 SEO 최적화 완료: ID={content_id}, 글자수={final_analysis['char_count']}, 모든 목표형태소 유효={final_analysis['is_valid_morphemes']}")
                
            return {
                'success': True,
                'message': success_message,
                'content_id': content_id,
                'is_valid_char_count': final_analysis['is_valid_char_count'],
                'is_valid_morphemes': final_analysis['is_valid_morphemes'],
                'char_count': final_analysis['char_count'],
                'attempts': api_attempts_count,
                'algorithm_version': 'v3_analyzer_focused_v3'
            }
                
        except BlogContent.DoesNotExist:
            logger.error(f"ID {content_id}에 해당하는 콘텐츠를 찾을 수 없습니다.")
            return {
                'success': False,
                'message': f"ID {content_id}에 해당하는 콘텐츠를 찾을 수 없습니다.",
                'content_id': content_id
            }
        except Exception as e:
            logger.error(f"콘텐츠 최적화 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': f"콘텐츠 최적화 중 오류 발생: {str(e)}",
                'content_id': content_id
            }

    def enforce_seo_optimization(self, content, keyword, custom_morphemes=None):
        """
        SEO 최적화를 위한 강제 변환 (MorphemeAnalyzer 사용)

        Args:
            content (str): 최적화할 콘텐츠
            keyword (str): 주요 키워드
            custom_morphemes (list): 사용자 지정 형태소

        Returns:
            str: SEO 최적화된 콘텐츠
        """
        content_parts = self.separate_content_and_refs(content)
        content_without_refs = content_parts['content_without_refs']
        refs_section = content_parts['refs_section']

        initial_analysis = self.morpheme_analyzer.analyze(content_without_refs, keyword, custom_morphemes)
        logger.info(f"SEO 강제 최적화 시작: 글자수={initial_analysis['char_count']} (유효: {initial_analysis['is_valid_char_count']}), 목표형태소 유효={initial_analysis['is_valid_morphemes']}")

        if initial_analysis['is_fully_optimized']:
            logger.info("이미 SEO 최적화된 상태입니다.")
            if refs_section and "## 참고자료" not in content_without_refs:
                 return content_without_refs + "\n\n" + refs_section
            return content_without_refs

        optimized_content = content_without_refs
        optimized_content = self._improve_content_structure(optimized_content, keyword)
        optimized_content = self._optimize_headings(optimized_content, keyword)

        attempt = 0
        previous_content = ""
        max_safety_attempts = 100 # Safety break for infinite loop

        while attempt < max_safety_attempts:
            if optimized_content == previous_content:
                logger.warning("최적화 과정이 고착 상태에 빠졌습니다. 루프를 중단합니다.")
                break
            previous_content = optimized_content

            current_analysis = self.morpheme_analyzer.analyze(optimized_content, keyword, custom_morphemes)
            logger.info(f"강제 최적화 시도 #{attempt+1}: 글자수={current_analysis['char_count']} (유효: {current_analysis['is_valid_char_count']}), 목표형태소 유효={current_analysis['is_valid_morphemes']}")

            if current_analysis['is_fully_optimized']:
                logger.info("강제 최적화 성공: 모든 조건 충족")
                break

            needs_char_adjustment = not current_analysis['is_valid_char_count']
            needs_morpheme_adjustment = not current_analysis['is_valid_morphemes'] 

            # 형태소 조정이 우선순위가 높음
            if needs_morpheme_adjustment:
                logger.info("조정: 목표 형태소")
                optimized_content = self._enforce_exact_target_morpheme_count(
                    optimized_content, 
                    keyword, 
                    custom_morphemes,
                    current_analysis['morpheme_analysis']['counts'],
                    current_analysis['morpheme_analysis']['target_morphemes']
                )
            elif needs_char_adjustment:
                logger.info("조정: 글자수")
                target_chars_center = (self.morpheme_analyzer.target_min_chars + self.morpheme_analyzer.target_max_chars) // 2
                optimized_content = self._enforce_exact_char_count_v2(
                    optimized_content, 
                    target_chars_center, 
                    tolerance=100 + attempt * 10, # 허용 오차를 점진적으로 늘림
                    all_target_morphemes=current_analysis['morpheme_analysis']['target_morphemes'], # Pass categorized morphemes
                    current_morpheme_counts=current_analysis['morpheme_analysis']['counts']
                )
            
            attempt += 1
        
        # 👇 [개선] 최종적으로 20회를 초과하는 형태소가 없도록 강제 조정
        logger.info("최종 검증: 20회 초과 형태소 강제 조정 시작")
        optimized_content = self._enforce_absolute_max_count(optimized_content, keyword, custom_morphemes, max_count=20)
            
        optimized_content = self._optimize_paragraph_breaks(optimized_content)

        if refs_section and "## 참고자료" not in optimized_content:
            optimized_content = optimized_content + "\n\n" + refs_section
        return optimized_content

    def _enforce_absolute_max_count(self, content, keyword, custom_morphemes, max_count):
        """
        모든 목표 형태소가 지정된 최대 횟수(max_count)를 넘지 않도록 강제로 조정합니다.
        """
        safety_break = 0
        while safety_break < 20: # 무한 루프 방지
            analysis = self.morpheme_analyzer.analyze(content, keyword, custom_morphemes)
            morphemes_over_limit = []

            for morpheme, info in analysis['morpheme_analysis']['counts'].items():
                if info['count'] > max_count:
                    morphemes_over_limit.append((morpheme, info['count']))
            
            if not morphemes_over_limit:
                logger.info(f"최종 검증 완료: 모든 목표 형태소가 {max_count}회 이하입니다.")
                return content
            
            # 가장 많이 초과된 형태소부터 처리
            morphemes_over_limit.sort(key=lambda x: x[1], reverse=True)
            morpheme_to_reduce, current_count = morphemes_over_limit[0]
            
            logger.warning(f"최종 검증: 형태소 '{morpheme_to_reduce}'가 {max_count}회를 초과했습니다 ({current_count}회). 19회로 강제 조정합니다.")
            
            content = self._reduce_morpheme_to_target(
                content,
                morpheme_to_reduce,
                target_count=max_count - 1, # 목표 횟수를 19로 설정하여 확실히 줄임
                all_target_morphemes_dict=analysis['morpheme_analysis']['target_morphemes']
            )
            safety_break += 1
        
        logger.error(f"최종 검증 실패: {safety_break}회 시도 후에도 20회를 초과하는 형태소가 남아있습니다.")
        return content

    def _improve_content_structure(self, content, keyword):
        logger.debug(f"콘텐츠 구조 개선 시도: {keyword}")
        return content

    def _optimize_headings(self, content, keyword):
        logger.debug(f"제목 최적화 시도: {keyword}")
        return content

    def _optimize_paragraph_breaks(self, content):
        logger.debug("문단 간격 및 줄바꿈 최적화 시도")
        return content

    def _force_adjust_target_morphemes_extreme(self, content, keyword, custom_morphemes, current_morpheme_counts, target_morphemes_dict):
        """
        '목표' 형태소 출현 횟수를 마지막 수단으로 강제 조정 (MorphemeAnalyzer 사용)
        target_morphemes_dict now contains 'base' and 'compound' lists.
        """
        logger.warning("극단적 목표 형태소 조정 시작")
        adjusted_content = content
        
        base_morphemes = target_morphemes_dict['base']
        compound_morphemes = target_morphemes_dict['compound']
        all_target_morphemes_list = target_morphemes_dict['all_list']

        # Adjust base morphemes first
        for morpheme in base_morphemes:
            current_info = current_morpheme_counts.get(morpheme, {'count': 0, 'is_valid': False})
            current_count = current_info['count']
            
            target_min = self.morpheme_analyzer.target_min_base_count
            target_max = self.morpheme_analyzer.target_max_base_count
            target_count = random.randint(target_min, target_max) # Aim for a random valid count

            if current_count > target_max:
                logger.warning(f"핵심 기본 형태소 '{morpheme}' 과다: {current_count}회 -> 목표 {target_count}회로 줄임")
                adjusted_content = self._reduce_morpheme_to_target(
                    adjusted_content, 
                    morpheme, 
                    target_count, 
                    target_morphemes_dict # Pass the full dict
                )
            elif current_count < target_min:
                shortage = target_min - current_count
                logger.warning(f"핵심 기본 형태소 '{morpheme}' 부족: {current_count}회 -> {target_min}회로 늘림 (추가량: {shortage}회)")
                adjusted_content = self._add_morpheme_strategically(adjusted_content, morpheme, shortage)

        # Adjust compound morphemes next
        for morpheme in compound_morphemes:
            current_info = current_morpheme_counts.get(morpheme, {'count': 0, 'is_valid': False})
            current_count = current_info['count']
            
            target_min = self.morpheme_analyzer.target_min_compound_count
            target_max = self.morpheme_analyzer.target_max_compound_count
            target_count = random.randint(target_min, target_max) # Aim for a random valid count

            if current_count > target_max:
                logger.warning(f"복합 키워드/구문 '{morpheme}' 과다: {current_count}회 -> 목표 {target_count}회로 줄임")
                adjusted_content = self._reduce_morpheme_to_target(
                    adjusted_content, 
                    morpheme, 
                    target_count, 
                    target_morphemes_dict # Pass the full dict
                )
            elif current_count < target_min:
                shortage = target_min - current_count
                logger.warning(f"복합 키워드/구문 '{morpheme}' 부족: {current_count}회 -> {target_min}회로 늘림 (추가량: {shortage}회)")
                adjusted_content = self._add_morpheme_strategically(adjusted_content, morpheme, shortage)
        
        # Final verification log
        final_analysis_after_extreme = self.morpheme_analyzer.analyze(adjusted_content, keyword, custom_morphemes)
        logger.warning("극단적 목표 형태소 조정 후 최종 결과:")
        for morpheme_type_key, morphemes_list in target_morphemes_dict.items():
            if morpheme_type_key == 'all_list': continue
            for morpheme in morphemes_list:
                info = final_analysis_after_extreme['morpheme_analysis']['counts'].get(morpheme, {})
                count = info.get('count',0)
                if info.get('type') == 'base':
                    target_min = self.morpheme_analyzer.target_min_base_count
                    target_max = self.morpheme_analyzer.target_max_base_count
                else: # compound
                    target_min = self.morpheme_analyzer.target_min_compound_count
                    target_max = self.morpheme_analyzer.target_max_compound_count
                status = "적정" if target_min <= count <= target_max else "부적정"
                logger.warning(f"- '{morpheme}' ({info.get('type')}): {count}회 ({status})")
        return adjusted_content
    
    def _add_morpheme_strategically(self, content, morpheme, count_to_add):
        logger.info(f"형태소 '{morpheme}' {count_to_add}회 전략적으로 추가")
        paragraphs = content.split("\n\n")
        normal_paragraphs_indices = [i for i, p in enumerate(paragraphs)
                                     if not p.strip().startswith(('#', '##', '###')) and len(p.strip()) > 50]

        if not normal_paragraphs_indices:
            logger.warning(f"'{morpheme}' 추가할 적절한 긴 문단 없음. 마지막 문단에 추가 시도.")
            if paragraphs:
                idx_to_add = len(paragraphs) -1
            else:
                paragraphs.append("")
                idx_to_add = 0
            
            if len(paragraphs[idx_to_add]) < 50 :
                 paragraphs[idx_to_add] += self._generate_sentences_with_morpheme(morpheme, count_to_add)
            else:
                 paragraphs[idx_to_add] = self._inject_morpheme_into_paragraph(paragraphs[idx_to_add], morpheme, count_to_add)
            return "\n\n".join(paragraphs)

        add_counts_per_paragraph = {idx: 0 for idx in normal_paragraphs_indices}
        for i in range(count_to_add):
            idx_to_add = normal_paragraphs_indices[i % len(normal_paragraphs_indices)]
            add_counts_per_paragraph[idx_to_add] += 1
            
        for idx, num_to_add_in_para in add_counts_per_paragraph.items():
            if num_to_add_in_para > 0:
                paragraphs[idx] = self._inject_morpheme_into_paragraph(paragraphs[idx], morpheme, num_to_add_in_para)
        
        return "\n\n".join(paragraphs)

    def _generate_sentences_with_morpheme(self, morpheme, count):
        """ 형태소가 포함된 문장 생성 (간단 버전) """
        sentences = []
        templates = [
            f"또한, {morpheme}의 중요성을 간과해서는 안 됩니다.",
            f"이러한 맥락에서 {morpheme}은 핵심적인 역할을 합니다.",
            f"결과적으로 {morpheme}의 활용이 중요합니다.",
            f"많은 전문가들이 {morpheme}의 가치를 강조합니다.",
            f"특히 {morpheme}에 대한 이해가 필요합니다."
        ]
        for _ in range(count):
            sentences.append(random.choice(templates))
        return " ".join(sentences)

    def _inject_morpheme_into_paragraph(self, paragraph, morpheme, count_to_add):
        """ 기존 문단에 형태소를 자연스럽게 삽입 """
        sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
        if not sentences or not sentences[0]:
            return paragraph + " " + self._generate_sentences_with_morpheme(morpheme, count_to_add)

        for _ in range(count_to_add):
            insert_idx = random.randrange(len(sentences) + 1)
            prefix_phrases = ["덧붙여 말하자면, ", "중요한 점은 ", "예를 들어, "]
            suffix_phrases = [f" 역시 중요합니다.", f"도 고려해야 합니다.", f"의 활용도 생각해볼 수 있습니다."]
            
            new_phrase_templates = [
                f"{random.choice(prefix_phrases)}{morpheme}의 경우",
                f"{morpheme}{random.choice(suffix_phrases)}",
                f"{morpheme} 관련하여"
            ]
            new_phrase = random.choice(new_phrase_templates)

            if insert_idx == len(sentences):
                sentences[-1] = sentences[-1].rstrip('.!?') + f", 특히 {morpheme}의 중요성이 부각됩니다."
            elif insert_idx == 0:
                sentences[0] = f"{morpheme}에 대해 말하자면, " + sentences[0]
            else:
                sentences.insert(insert_idx, new_phrase)
        
        return " ".join(s.strip() for s in sentences if s.strip())

    def _ask_claude_for_sentence_reduction(self, sentence, morpheme_to_reduce):
        """
        Claude에게 특정 형태소를 문장에서 제거하거나 문장 전체를 삭제할지 문의하고,
        자연스러움을 유지하도록 요청합니다.
        """
        prompt = f"""
        당신은 전문 콘텐츠 편집자입니다. 주어진 문장에서 특정 단어/구문의 출현을 줄이면서
        문장의 자연스러움과 의미를 유지하는 것이 당신의 임무입니다.

        줄여야 할 단어/구문: "{morpheme_to_reduce}"
        문장: "{sentence}"

        문장을 분석하고 다음 중 하나를 결정하세요:
        1. 단어/구문 "{morpheme_to_reduce}"를 문장에서 제거해도 문장이 부자연스러워지거나
           필수적인 의미를 잃지 않습니까? 그렇다면 수정된 문장을 제공하세요.
        2. 단어/구문만 제거하면 문장이 부자연스러워지거나 의미가 크게 변합니까?
           그렇다면 블로그 게시물의 전체적인 흐름과 일관성에 영향을 주지 않고
           문장 전체를 제거할 수 있습니까? 그렇다면 빈 문자열을 출력하세요.
        3. 위 두 가지 모두 불가능한 경우 (즉, 단어/구문이 필수적이고 문장을 제거할 수 없는 경우),
           원래 문장을 변경하지 않고 그대로 반환하세요.

        수정된 문장만 출력하거나, 문장을 제거해야 한다면 빈 문자열을 출력하세요.
        어떤 설명이나 다른 텍스트도 추가하지 마세요.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude sentence reduction API error: {e}")
            return sentence

    def _reduce_morpheme_to_target(self, content, morpheme_to_reduce, target_count, all_target_morphemes_dict):
        """
        특정 형태소의 출현 횟수를 목표치(target_count)까지 줄입니다.
        클로드에게 문맥상 자연스러움을 확인하도록 요청합니다.
        """
        logger.info(f"형태소 '{morpheme_to_reduce}' 횟수를 목표치({target_count}회)에 맞게 제거 (클로드 문맥 고려)")

        # Determine counting method based on morpheme type (base or compound)
        temp_analysis_for_type = self.morpheme_analyzer.analyze(content, "", all_target_morphemes_dict['all_list'])
        morpheme_type = temp_analysis_for_type['morpheme_analysis']['counts'].get(morpheme_to_reduce, {}).get('type', 'base')

        if morpheme_type == 'base':
            count_func = self.morpheme_analyzer._count_substring
            pattern = re.escape(morpheme_to_reduce) # Substring pattern for finding sentences
        else: # compound
            count_func = self.morpheme_analyzer._count_exact_word
            if re.search(r'[가-힣]', morpheme_to_reduce):
                if ' ' in morpheme_to_reduce:
                    pattern = re.escape(morpheme_to_reduce)
                else:
                    pattern = rf'(?<![가-힣]){re.escape(morpheme_to_reduce)}(?![가-힣])'
            else:
                pattern = rf'\b{re.escape(morpheme_to_reduce)}\b'
        
        current_content = content
        previous_content = ""
        attempt = 0
        max_attempts = 30 # Safety break for infinite loop

        while attempt < max_attempts:
            if current_content == previous_content:
                logger.warning(f"'{morpheme_to_reduce}' 감소 과정이 고착 상태입니다. 루프를 중단합니다.")
                break
            previous_content = current_content

            current_count = count_func(morpheme_to_reduce, current_content)
            
            if current_count <= target_count:
                logger.info(f"형태소 '{morpheme_to_reduce}' 목표치({target_count}회) 달성 (현재 {current_count}회).")
                return current_content

            sentences = re.split(r'(?<=[.!?])\s+', current_content)
            
            sentences_with_morpheme_indices = []
            for i, s in enumerate(sentences):
                if re.search(pattern, s): # Use the correct pattern for finding sentences containing the morpheme
                    sentences_with_morpheme_indices.append(i)
            
            if not sentences_with_morpheme_indices:
                logger.warning(f"형태소 '{morpheme_to_reduce}'를 포함하는 문장을 찾을 수 없습니다. (현재 {current_count}회)")
                break

            # Send ALL relevant sentences to Claude for processing
            modified_sentences_map = {}
            for idx in sentences_with_morpheme_indices:
                original_sentence = sentences[idx]
                claude_modified_sentence = self._ask_claude_for_sentence_reduction(original_sentence, morpheme_to_reduce)
                modified_sentences_map[idx] = claude_modified_sentence
                
                if claude_modified_sentence != original_sentence:
                    logger.info(f"클로드: 문장 '{original_sentence[:30]}...'에서 형태소 '{morpheme_to_reduce}' 수정/제거 시도.")
                else:
                    logger.info(f"클로드: 문장 '{original_sentence[:30]}...' 변경 없음.")

            new_sentences = [modified_sentences_map.get(i, s) for i, s in enumerate(sentences)]
            
            current_content = " ".join(s for s in new_sentences if s) # Filter out empty strings from deleted sentences
            
            updated_count = count_func(morpheme_to_reduce, current_content)
            logger.info(f"형태소 '{morpheme_to_reduce}' 제거 시도 #{attempt+1}. 현재 횟수: {updated_count}")
            attempt += 1

        logger.warning(f"형태소 '{morpheme_to_reduce}' {max_attempts}회 시도 후에도 목표치({target_count}회) 미달성. 현재 {count_func(morpheme_to_reduce, current_content)}회.")
        return current_content

    def _get_enhanced_substitutions(self, morpheme):
        substitutions = self.substitution_generator.get_substitutions(morpheme)
        if len(substitutions) < 3:
            default_subs = ["이것", "그것", "해당 내용", "이 부분", "관련된 것"]
            if len(morpheme) > 3:
                default_subs.append("") 
            substitutions.extend(s for s in default_subs if s not in substitutions)
        return list(set(substitutions))

    def _enforce_exact_char_count_v2(self, content, target_char_count, tolerance=50, all_target_morphemes=None, current_morpheme_counts=None):
        current_char_count = len(content.replace(" ", ""))
        min_chars = target_char_count - tolerance
        max_chars = target_char_count + tolerance

        if min_chars <= current_char_count <= max_chars:
            return content
            
        paragraphs = re.split(r'(\n\n+)', content)
        
        processed_paragraphs = []
        temp_para = ""
        for part in paragraphs:
            if part == "\n\n" or part == "\n":
                if temp_para:
                    processed_paragraphs.append(temp_para)
                    temp_para = ""
                processed_paragraphs.append(part)
            else:
                temp_para += part
        if temp_para:
            processed_paragraphs.append(temp_para)

        content_paragraphs_with_indices = []
        for i, p_text in enumerate(processed_paragraphs):
            if not (p_text == "\n\n" or p_text == "\n") and p_text.strip():
                 if not p_text.strip().startswith(('#', '##', '###')):
                    content_paragraphs_with_indices.append({'original_idx': i, 'text': p_text, 'len': len(p_text.replace(" ",""))})
        
        if not content_paragraphs_with_indices:
            logger.warning("글자수 조정: 수정할 내용 문단 없음.")
            return content

        if current_char_count < min_chars:
            chars_to_add = min_chars - current_char_count
            logger.info(f"글자수 조정: {chars_to_add}자 추가 필요")
            
            content_paragraphs_with_indices.sort(key=lambda x: x['len'])
            
            added_chars_total = 0
            for para_info in content_paragraphs_with_indices:
                if added_chars_total >= chars_to_add: break
                
                current_para_add = (chars_to_add - added_chars_total) // (len(content_paragraphs_with_indices) - content_paragraphs_with_indices.index(para_info)) if len(content_paragraphs_with_indices) > content_paragraphs_with_indices.index(para_info) else (chars_to_add - added_chars_total)
                current_para_add = max(20, current_para_add)
                
                expanded_text = self._expand_paragraph(para_info['text'], current_para_add, all_target_morphemes, current_morpheme_counts)
                char_diff = len(expanded_text.replace(" ","")) - para_info['len']
                processed_paragraphs[para_info['original_idx']] = expanded_text
                added_chars_total += char_diff
                if added_chars_total >= chars_to_add: break
            
        elif current_char_count > max_chars:
            chars_to_remove = current_char_count - max_chars
            logger.info(f"글자수 조정: {chars_to_remove}자 제거 필요")

            content_paragraphs_with_indices.sort(key=lambda x: x['len'], reverse=True)
            removed_chars_total = 0
            for para_info in content_paragraphs_with_indices:
                if removed_chars_total >= chars_to_remove: break
                if para_info['len'] < 50 : continue

                current_para_remove = min(
                    (chars_to_remove - removed_chars_total) // (len(content_paragraphs_with_indices) - content_paragraphs_with_indices.index(para_info) if len(content_paragraphs_with_indices) > content_paragraphs_with_indices.index(para_info) else 1),
                    para_info['len'] // 3
                )
                current_para_remove = max(20, current_para_remove)

                if current_para_remove > 0:
                    reduced_text = self._reduce_paragraph(para_info['text'], current_para_remove, all_target_morphemes, current_morpheme_counts)
                    char_diff = para_info['len'] - len(reduced_text.replace(" ",""))
                    processed_paragraphs[para_info['original_idx']] = reduced_text
                    removed_chars_total += char_diff
                    if removed_chars_total >= chars_to_remove: break
            
        return "".join(processed_paragraphs)

    def _expand_paragraph(self, paragraph, chars_to_add, all_target_morphemes_dict, current_morpheme_counts):
        """
        문단을 확장하여 글자수를 늘립니다.
        과다하게 출현하는 목표 형태소가 재유입되지 않도록 주의합니다.
        """
        if chars_to_add <=0: return paragraph
        
        sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
        last_sentence = sentences[-1] if sentences and sentences[-1] else ""
        
        try:
            nouns = self.okt.nouns(last_sentence if last_sentence else paragraph)
            key_phrases = [n for n in nouns if len(n) > 1][:3]
        except Exception:
            key_phrases = ["이 주제", "관련 내용"]

        filtered_key_phrases = []
        if all_target_morphemes_dict and current_morpheme_counts:
            for phrase in key_phrases:
                is_over_represented = False
                if phrase in all_target_morphemes_dict['all_list']:
                    morpheme_info = current_morpheme_counts.get(phrase, {})
                    morpheme_type = morpheme_info.get('type')
                    count = morpheme_info.get('count', 0)
                    
                    if morpheme_type == 'base' and count >= self.morpheme_analyzer.target_max_base_count:
                        is_over_represented = True
                    elif morpheme_type == 'compound' and count >= self.morpheme_analyzer.target_max_compound_count:
                        is_over_represented = True
                
                if not is_over_represented:
                    filtered_key_phrases.append(phrase)
        else:
            filtered_key_phrases = key_phrases
        
        if not filtered_key_phrases:
            filtered_key_phrases = ["이 점", "이 부분", "해당 내용"]

        expansion_text = ""
        added_len = 0
        templates = [
            " 이에 더해, {phrase}에 대한 심층적인 이해가 필요합니다.",
            " 또한 {phrase}의 중요성을 강조하고 싶습니다.",
            " {phrase}와 관련하여 추가적인 정보를 제공하자면 다음과 같습니다.",
            " 실제로 {phrase}는 많은 영향을 미칩니다.",
            " 그리고 {phrase}에 대한 고려도 중요합니다."
        ]
        while added_len < chars_to_add:
            chosen_phrase = random.choice(filtered_key_phrases)
            sentence_to_add = random.choice(templates).format(phrase=chosen_phrase)
            
            contains_over_represented_in_new_sentence = False
            if all_target_morphemes_dict and current_morpheme_counts:
                temp_analysis = self.morpheme_analyzer.analyze(sentence_to_add, "", all_target_morphemes_dict['all_list'])
                for morpheme in all_target_morphemes_dict['all_list']:
                    morpheme_info_in_new_sentence = temp_analysis['morpheme_analysis']['counts'].get(morpheme, {})
                    count_in_new_sentence = morpheme_info_in_new_sentence.get('count', 0)
                    morpheme_type = morpheme_info_in_new_sentence.get('type')

                    if count_in_new_sentence > 0:
                        current_global_count = current_morpheme_counts.get(morpheme, {}).get('count', 0)
                        
                        if morpheme_type == 'base' and current_global_count >= self.morpheme_analyzer.target_max_base_count:
                            contains_over_represented_in_new_sentence = True
                            break
                        elif morpheme_type == 'compound' and current_global_count >= self.morpheme_analyzer.target_max_compound_count:
                            contains_over_represented_in_new_sentence = True
                            break
            
            if not contains_over_represented_in_new_sentence:
                expansion_text += sentence_to_add
                added_len += len(sentence_to_add.replace(" ", ""))
            
            if len(expansion_text) > chars_to_add * 1.5 : break

        return paragraph + expansion_text

    def _reduce_paragraph(self, paragraph, chars_to_remove, all_target_morphemes_dict, current_morpheme_counts):
        if chars_to_remove <= 0: return paragraph

        sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
        if len(sentences) <= 1:
            words = paragraph.split()
            reduced_len = 0
            while reduced_len < chars_to_remove and len(words) > 5:
                removed_word = words.pop()
                reduced_len += len(removed_word.replace(" ",""))
            return " ".join(words) + ("." if paragraph.endswith(".") else "")

        sentence_info = []
        for i, s in enumerate(sentences):
            score = 100 - len(s)
            if any(conj in s for conj in ["하지만", "그러나", "따라서", "결론적으로"]):
                score -= 50
            
            if all_target_morphemes_dict and current_morpheme_counts:
                temp_analysis = self.morpheme_analyzer.analyze(s, "", all_target_morphemes_dict['all_list'])
                for morpheme in all_target_morphemes_dict['all_list']:
                    morpheme_info_in_sentence = temp_analysis['morpheme_analysis']['counts'].get(morpheme, {})
                    count_in_sentence = morpheme_info_in_sentence.get('count', 0)
                    morpheme_type = morpheme_info_in_sentence.get('type')

                    if count_in_sentence > 0:
                        current_global_count = current_morpheme_counts.get(morpheme, {}).get('count', 0)
                        
                        if morpheme_type == 'base' and current_global_count > self.morpheme_analyzer.target_max_base_count:
                            score += 200
                            break
                        elif morpheme_type == 'compound' and current_global_count > self.morpheme_analyzer.target_max_compound_count:
                            score += 150
                            break

            sentence_info.append({'idx': i, 'text': s, 'score': score, 'len': len(s.replace(" ",""))})
        
        sentence_info.sort(key=lambda x: x['score'], reverse=True)

        removed_chars_count = 0
        removed_indices = set()
        new_sentences = list(sentences)

        for s_info in sentence_info:
            if removed_chars_count >= chars_to_remove: break
            if len(sentences) - len(removed_indices) <= 1 : break 

            if s_info['idx'] not in removed_indices:
                original_sentence = s_info['text']
                reconstructed_sentence = original_sentence
                
                patterns_to_remove = [
                    (r"매우\s+", ""), (r"정말\s+", ""), (r"아주\s+", ""),
                    (r"하는\s+것은", ""), (r"에\s+대하여", ""), (r"에\s+관한", ""),
                    (r"이라고\s+할\s+수\s+있다", ""), (r"라고\s+볼\s+수\s+있다", ""),
                    (r"~에\s+따르면", ""),
                    (r"~의\s+경우", ""),
                ]
                for pattern, replacement in patterns_to_remove:
                    reconstructed_sentence = re.sub(pattern, replacement, reconstructed_sentence)

                words = reconstructed_sentence.split()
                temp_words = []
                for word in words:
                    if word in all_target_morphemes_dict['all_list']:
                        temp_words.append(word)
                        continue
                    
                    substitutions = self.substitution_generator.get_substitutions(word)
                    safe_subs = [
                        sub for sub in substitutions
                        if not any(target_m in sub for target_m in all_target_morphemes_dict['all_list']) and len(sub) < len(word)
                    ]
                    if safe_subs and random.random() < 0.3:
                        new_word = random.choice(safe_subs)
                        temp_words.append(new_word)
                        removed_chars_count += len(word.replace(" ", "")) - len(new_word.replace(" ", ""))
                        logger.debug(f"단어 대체: '{word}' -> '{new_word}'")
                    else:
                        temp_words.append(word)
                reconstructed_sentence = " ".join(temp_words)

                char_diff_from_reconstruction = len(original_sentence.replace(" ", "")) - len(reconstructed_sentence.replace(" ", ""))
                if char_diff_from_reconstruction > 0:
                    new_sentences[s_info['idx']] = reconstructed_sentence
                    removed_chars_count += char_diff_from_reconstruction
                    logger.debug(f"문장 재구성: '{original_sentence}' -> '{reconstructed_sentence}' (줄어든 글자수: {char_diff_from_reconstruction})")
                else:
                    new_sentences[s_info['idx']] = original_sentence
                
                if s_info['idx'] not in removed_indices and (new_sentences[s_info['idx']] == original_sentence or char_diff_from_reconstruction < 5):
                    if s_info['len'] > 20 and removed_chars_count + s_info['len'] <= chars_to_remove:
                        removed_chars_count += s_info['len']
                        removed_indices.add(s_info['idx'])
                        logger.debug(f"문장 삭제: '{s_info['text']}'")
        
        final_sentences = [new_sentences[i] for i in range(len(new_sentences)) if i not in removed_indices]
        return " ".join(final_sentences)

    def _enforce_exact_target_morpheme_count(self, content, keyword, custom_morphemes, current_morpheme_counts, target_morphemes_dict):
        """
        '목표' 형태소 출현 횟수를 목표 범위 내로 조정 (MorphemeAnalyzer 사용)
        target_morphemes_dict now contains 'base' and 'compound' lists.
        """
        adjusted_content = content
        
        base_morphemes = target_morphemes_dict['base']
        compound_morphemes = target_morphemes_dict['compound']
        all_target_morphemes_list = target_morphemes_dict['all_list']

        # Adjust base morphemes first
        for morpheme in base_morphemes:
            current_count_for_morpheme = self.morpheme_analyzer._count_substring(morpheme, adjusted_content)
            
            target_min = self.morpheme_analyzer.target_min_base_count
            target_max = self.morpheme_analyzer.target_max_base_count

            if current_count_for_morpheme > target_max:
                target_count = (target_min + target_max) // 2
                logger.info(f"핵심 기본 형태소 '{morpheme}' 과다: {current_count_for_morpheme}회 -> 목표 {target_count}회로 줄임")
                adjusted_content = self._reduce_morpheme_to_target(
                    adjusted_content, 
                    morpheme, 
                    target_count, 
                    target_morphemes_dict # Pass the full dict
                )
            elif current_count_for_morpheme < target_min:
                shortage = target_min - current_count_for_morpheme
                logger.info(f"핵심 기본 형태소 '{morpheme}' 부족: {current_count_for_morpheme}회 -> {target_min}회로 늘림 (추가량: {shortage}회)")
                adjusted_content = self._add_morpheme_strategically(adjusted_content, morpheme, shortage)

        # Adjust compound morphemes next
        for morpheme in compound_morphemes:
            current_count_for_morpheme = self.morpheme_analyzer._count_exact_word(morpheme, adjusted_content)
            
            target_min = self.morpheme_analyzer.target_min_compound_count
            target_max = self.morpheme_analyzer.target_max_compound_count

            if current_count_for_morpheme > target_max:
                target_count = (target_min + target_max) // 2
                logger.info(f"복합 키워드/구문 '{morpheme}' 과다: {current_count_for_morpheme}회 -> 목표 {target_count}회로 줄임")
                adjusted_content = self._reduce_morpheme_to_target(
                    adjusted_content, 
                    morpheme, 
                    target_count, 
                    target_morphemes_dict # Pass the full dict
                )
            elif current_count_for_morpheme < target_min:
                shortage = target_min - current_count_for_morpheme
                logger.info(f"복합 키워드/구문 '{morpheme}' 부족: {current_count_for_morpheme}회 -> {target_min}회로 늘림 (추가량: {shortage}회)")
                adjusted_content = self._add_morpheme_strategically(adjusted_content, morpheme, shortage)
        
        return adjusted_content

    def _add_morpheme_naturally(self, content, morpheme, count_to_add):
        return self._add_morpheme_strategically(content, morpheme, count_to_add)

    def separate_content_and_refs(self, content):
        refs_pattern = r"(## 참고자료[\s\S]*)"
        refs_match = re.search(refs_pattern, content, re.MULTILINE)
        
        if refs_match:
            refs_section = refs_match.group(1)
            content_without_refs = content[:refs_match.start()].strip()
            return {
                'content_without_refs': content_without_refs,
                'refs_section': refs_section
            }
        else:
            return {
                'content_without_refs': content.strip(),
                'refs_section': None
            }
    
    def _create_seo_optimization_prompt(self, content, keyword, custom_morphemes, analysis_result):
        char_count = analysis_result['char_count']
        target_min_chars = self.morpheme_analyzer.target_min_chars
        target_max_chars = self.morpheme_analyzer.target_max_chars
        char_count_direction = ""
        if char_count < target_min_chars:
            char_count_direction = f"현재 {char_count}자. {target_min_chars - char_count}자 이상 늘려 {target_min_chars}-{target_max_chars}자 범위로 만들어주세요."
        elif char_count > target_max_chars:
            char_count_direction = f"현재 {char_count}자. {char_count - target_max_chars}자 이상 줄여 {target_min_chars}-{target_max_chars}자 범위로 만들어주세요."
        else:
            char_count_direction = f"현재 글자수 {char_count}자는 적절한 범위({target_min_chars}-{target_max_chars}자)입니다. 이 범위를 유지해주세요."

        morpheme_issues = []
        
        base_morphemes = analysis_result['morpheme_analysis']['target_morphemes']['base']
        compound_morphemes = analysis_result['morpheme_analysis']['target_morphemes']['compound']
        current_counts = analysis_result['morpheme_analysis']['counts']

        target_min_base_morph = self.morpheme_analyzer.target_min_base_count
        target_max_base_morph = self.morpheme_analyzer.target_max_base_count
        target_min_compound_morph = self.morpheme_analyzer.target_min_compound_count
        target_max_compound_morph = self.morpheme_analyzer.target_max_compound_count

        for morpheme in base_morphemes:
            info = current_counts.get(morpheme, {})
            count = info.get('count', 0)
            if not info.get('is_valid', True):
                morpheme_issues.append(f"• 핵심 기본 형태소 '{morpheme}': 현재 {count}회 → 목표 {target_min_base_morph}-{target_max_base_morph}회 (부족/과다)")
        
        for morpheme in compound_morphemes:
            info = current_counts.get(morpheme, {})
            count = info.get('count', 0)
            if not info.get('is_valid', True):
                morpheme_issues.append(f"• 복합 키워드/구문 '{morpheme}': 현재 {count}회 → 목표 {target_min_compound_morph}-{target_max_compound_morph}회 (부족/과다)")
        
        morpheme_text = "\n".join(morpheme_issues) if morpheme_issues else "모든 목표 형태소가 적정 범위 내에 있습니다."
        
        return f"""
        이 블로그 콘텐츠를 SEO와 가독성 측면에서 최적화해주세요. 아래 요구사항을 충족하면서 사용자 경험을 개선해야 합니다:

        1️⃣ 글자수 요구사항: {target_min_chars}-{target_max_chars}자 (공백 제외)
        {char_count_direction}

        2️⃣ 키워드 및 주요 형태소 최적화:
        {morpheme_text}

        3️⃣ 키워드 및 형태소 카운팅 방식:
           - 핵심 기본 형태소 (예: '엔진', '오일', '종류'): 문장 내에서 부분적으로 포함되어도 카운트됩니다. (예: '엔진오일종류'에서 '엔진' 1회, '오일' 1회, '종류' 1회)
           - 복합 키워드 및 구문 (예: '엔진오일', '엔진오일종류'): 정확히 해당 구문이 일치해야 카운트됩니다.

        4️⃣ SEO 최적화 전략:
        • 첫 번째 문단에 핵심 키워드 자연스럽게 포함
        • 주요 소제목에 키워드 관련 문구 포함
        • 짧고 간결한 문단 사용 (2-3문장 권장)
        • 핵심 키워드의 자연스러운 분포
        • 명확한 문단 구분과 소제목 활용
        • 모바일 친화적인 짧은 문장 사용

        5️⃣ 사용자 경험 개선:
        • 글머리 기호나 번호 매기기로 내용 구조화
        • 핵심 정보를 먼저 제시하는 역피라미드 구조
        • 전문 용어는 적절한 설명과 함께 사용
        • 직관적이고 명확한 표현 사용

        원본 콘텐츠:
        {content}

        최적화된 내용만 제공해 주세요. 설명이나 메모는 포함하지 마세요.
        """
    
    def _create_seo_readability_prompt(self, content, keyword, custom_morphemes, analysis_result):
        base_morphemes = analysis_result['morpheme_analysis']['target_morphemes']['base']
        compound_morphemes = analysis_result['morpheme_analysis']['target_morphemes']['compound']
        
        target_min_base_morph = self.morpheme_analyzer.target_min_base_count
        target_max_base_morph = self.morpheme_analyzer.target_max_base_count
        target_min_compound_morph = self.morpheme_analyzer.target_min_compound_count
        target_max_compound_morph = self.morpheme_analyzer.target_max_compound_count

        morpheme_instructions = []
        if base_morphemes:
            morpheme_instructions.append(f"핵심 기본 형태소 ({', '.join(base_morphemes)}): 각각 {target_min_base_morph}-{target_max_base_morph}회")
        if compound_morphemes:
            morpheme_instructions.append(f"복합 키워드 및 구문 ({', '.join(compound_morphemes)}): 각각 {target_min_compound_morph}-{target_max_compound_morph}회")

        morpheme_instruction_text = " 및 ".join(morpheme_instructions)

        return f"""
        이 블로그 콘텐츠를 사용자 친화적이고 SEO에 최적화된 형태로 개선해주세요. 최신 SEO 트렌드에 맞춰 다음 요소들에 집중하세요:

        1️⃣ 가독성 최적화:
        • 긴 문단을 2-3문장의 짧은 문단으로 분리
        • 복잡한 문장을 간결하게 재구성
        • 핵심 정보는 굵은 글씨나 강조 표시 활용
        • 명확한 소제목으로 콘텐츠 구조화
        • 모바일에서 읽기 쉬운 형식 적용

        2️⃣ 키워드 및 주요 형태소 최적화:
        • 주요 키워드 '{keyword}'와 다음 형태소들이 {morpheme_instruction_text} 출현하도록 조정해주세요.
        • 키워드 변형을 자연스럽게 배치
        • 키워드 스터핑(과도한 반복) 방지

        3️⃣ 구조적 최적화:
        • 주요 소제목(H2, H3)에 키워드 포함
        • 첫 문단에 핵심 키워드와 주제 명확히 제시
        • 글머리 기호와 번호 매기기로 내용 구조화
        • 시각적 여백과 분리를 통한 정보 구분

        4️⃣ 콘텐츠 품질 향상:
        • 전문적이고 신뢰할 수 있는 톤 유지
        • 불필요한 반복 제거
        • 핵심 가치와 중요 정보 강조
        • 행동 유도 문구(CTA) 적절히 배치

        원본 콘텐츠:
        {content}

        최적화된 콘텐츠만 제공해 주세요. 설명이나 메모는 포함하지 마세요.
        """

    def _create_ultra_seo_prompt(self, content, keyword, custom_morphemes, analysis_result):
        target_min_chars = self.morpheme_analyzer.target_min_chars
        target_max_chars = self.morpheme_analyzer.target_max_chars
        
        base_morphemes = analysis_result['morpheme_analysis']['target_morphemes']['base']
        compound_morphemes = analysis_result['morpheme_analysis']['target_morphemes']['compound']
        current_counts = analysis_result['morpheme_analysis']['counts']

        target_min_base_morph = self.morpheme_analyzer.target_min_base_count
        target_max_base_morph = self.morpheme_analyzer.target_max_base_count
        target_min_compound_morph = self.morpheme_analyzer.target_min_compound_count
        target_max_compound_morph = self.morpheme_analyzer.target_max_compound_count

        morpheme_instructions = []
        if base_morphemes:
            morpheme_instructions.append(f"핵심 기본 형태소 ({', '.join(base_morphemes)}): 각각 {target_min_base_morph}-{target_max_base_morph}회")
        if compound_morphemes:
            morpheme_instructions.append(f"복합 키워드 및 구문 ({', '.join(compound_morphemes)}): 각각 {target_min_compound_morph}-{target_max_compound_morph}회")

        morpheme_instruction_text = " 및 ".join(morpheme_instructions)

        morpheme_analysis_for_prompt = {
            "target_morphemes": analysis_result['morpheme_analysis']['target_morphemes'],
            "counts": analysis_result['morpheme_analysis']['counts']
        }

        return f"""
        이 블로그 글을 완전한 최적화 기준에 맞추어 재구성해 주세요. 최고의 SEO 성능을 위한 명확한 지침을 따라주세요:

        1️⃣ 절대적인 글자수 요구사항: 
        • 최종 글자수(공백 제외): {target_min_chars}-{target_max_chars}자 사이여야 함
        • 현재 글자수: {analysis_result['char_count']}자

        2️⃣ 엄격한 목표 형태소 출현 빈도:
        • 주요 키워드 '{keyword}'와 이와 관련된 주요 형태소들({morpheme_instruction_text})은 반드시 지정된 범위 내로 출현해야 합니다.
        • 현재 목표 형태소 분석 결과:
        {json.dumps(morpheme_analysis_for_prompt, ensure_ascii=False, indent=2)}

        3️⃣ 키워드 및 형태소 카운팅 방식:
           - 핵심 기본 형태소 (예: '엔진', '오일', '종류'): 문장 내에서 부분적으로 포함되어도 카운트됩니다. (예: '엔진오일종류'에서 '엔진' 1회, '오일' 1회, '종류' 1회)
           - 복합 키워드 및 구문 (예: '엔진오일', '엔진오일종류'): 정확히 해당 구문이 일치해야 카운트됩니다.

        4️⃣ 구조 최적화 (정확히 적용):
        • 첫 문단에 반드시 키워드와 그 변형어 포함
        • 모든 H2/H3 제목에 키워드 관련 용어 포함
        • 2-3문장 단위로 문단 분리
        • 중요 정보는 글머리 기호로 강조
        • 숫자는 리스트로 표시

        5️⃣ 모바일 최적화:
        • 4-5줄 이내의 짧은 문단
        • 복잡한 문장 단순화
        • 모바일에서 빠르게 스캔 가능한 형식

        6️⃣ 핵심 콘텐츠 구조:
        • 서론: 핵심 키워드로 시작, 독자 니즈 언급
        • 본론: 문제점과 해결책 제시
        • 결론: 핵심 키워드로 정리, 행동 유도

        원본 콘텐츠:
        {content}

        최적화된 콘텐츠만 제공해 주세요. 설명이나 메모는 포함하지 마세요.
        """
