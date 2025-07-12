# d:\BlogCheatKey\blog_cheatkey_v2\blog_cheatkey\backend\content\services\morpheme_analyzer.py
import re
from konlpy.tag import Okt
import logging

logger = logging.getLogger(__name__)

class MorphemeAnalyzer:
    def __init__(self):
        self.okt = Okt()
        # Define target ranges for base and compound morphemes
        # 기본 형태소 (엔진, 오일, 종류)는 17~20회
        self.target_min_base_count = 17
        self.target_max_base_count = 20
        # 복합 형태소 (엔진오일, 엔진오일종류)는 0~15회 (16회 미만)
        self.target_min_compound_count = 0
        self.target_max_compound_count = 15 

        # General character count targets (adjust as needed)
        self.target_min_chars = 1500 
        self.target_max_chars = 2500 

    def analyze(self, content, keyword, custom_morphemes=None):
        char_count = len(content.replace(" ", ""))
        is_valid_char_count = self.target_min_chars <= char_count <= self.target_max_chars

        # 1. Identify base morphemes from the keyword
        # 키워드를 Okt.morphs로 분해하여 기본 형태소 추출
        base_morphemes_from_keyword = []
        try:
            base_morphemes_from_keyword = [m for m in self.okt.morphs(keyword) if len(m) >= 2]
        except Exception as e:
            logger.error(f"Okt morphs error for keyword '{keyword}': {e}")
            base_morphemes_from_keyword = []
        
        # 사용자 지정 형태소 중 단일 단어 형태를 기본 형태소에 추가
        effective_base_morphemes = list(set(base_morphemes_from_keyword))
        if custom_morphemes:
            for cm in custom_morphemes:
                if ' ' not in cm and cm not in effective_base_morphemes: # 공백 없는 단어만
                    effective_base_morphemes.append(cm)
        effective_base_morphemes.sort() # For consistent order

        # 2. Identify compound morphemes/phrases
        compound_morphemes = [keyword] # 전체 키워드는 항상 복합 형태소
        
        # 기본 형태소들의 조합으로 복합 형태소 생성 (예: 엔진 + 오일 -> 엔진오일)
        # 이 부분은 키워드에 따라 더 정교한 로직이 필요할 수 있습니다.
        # 현재는 간단히 Okt.morphs 결과의 연속된 두 단어를 조합합니다.
        if len(base_morphemes_from_keyword) > 1:
            for i in range(len(base_morphemes_from_keyword) - 1):
                combo = base_morphemes_from_keyword[i] + base_morphemes_from_keyword[i+1]
                if combo not in compound_morphemes and len(combo) > 2:
                    compound_morphemes.append(combo)
        
        # 사용자 지정 형태소 중 여러 단어 형태를 복합 형태소에 추가
        if custom_morphemes:
            for cm in custom_morphemes:
                if ' ' in cm and cm not in compound_morphemes: # 공백 있는 구문만
                    compound_morphemes.append(cm)
        compound_morphemes = list(set(compound_morphemes))
        compound_morphemes.sort() # For consistent order

        # 3. Count occurrences
        morpheme_counts = {}
        is_valid_morphemes = True

        # Count base morphemes (substring match)
        for morpheme in effective_base_morphemes:
            count = self._count_substring(morpheme, content)
            is_valid = self.target_min_base_count <= count <= self.target_max_base_count
            morpheme_counts[morpheme] = {'count': count, 'is_valid': is_valid, 'type': 'base'}
            if not is_valid:
                is_valid_morphemes = False

        # Count compound morphemes (exact word/phrase match)
        for morpheme in compound_morphemes:
            count = self._count_exact_word(morpheme, content)
            is_valid = self.target_min_compound_count <= count <= self.target_max_compound_count
            morpheme_counts[morpheme] = {'count': count, 'is_valid': is_valid, 'type': 'compound'}
            if not is_valid:
                is_valid_morphemes = False
        
        # Combine all target morphemes for easy iteration in optimizer
        all_target_morphemes_list = list(effective_base_morphemes) + list(compound_morphemes)

        is_fully_optimized = is_valid_char_count and is_valid_morphemes

        return {
            'char_count': char_count,
            'is_valid_char_count': is_valid_char_count,
            'is_valid_morphemes': is_valid_morphemes,
            'is_fully_optimized': is_fully_optimized,
            'morpheme_analysis': {
                'target_morphemes': {
                    'base': effective_base_morphemes,
                    'compound': compound_morphemes,
                    'all_list': all_target_morphemes_list # For convenience in optimizer
                },
                'counts': morpheme_counts
            }
        }

    def _count_substring(self, sub, text):
        """
        텍스트 내에서 부분 문자열(sub)의 출현 횟수를 카운트합니다.
        예: text="엔진오일종류", sub="엔진" -> 1
        """
        return len(re.findall(re.escape(sub), text))

    def _count_exact_word(self, word, text):
        """
        텍스트 내에서 정확한 단어/구문(word)의 출현 횟수를 카운트합니다.
        한글 단어는 비한글 문자 경계를, 영어/숫자는 단어 경계를 사용합니다.
        """
        if re.search(r'[가-힣]', word): # 한글 포함 여부 확인
            if ' ' in word: # 여러 단어로 구성된 한글 구문
                pattern = re.escape(word)
            else: # 단일 한글 단어
                # 한글 단어의 경우, 앞뒤에 한글이 아닌 문자가 와야 정확한 단어로 간주
                pattern = rf'(?<![가-힣]){re.escape(word)}(?![가-힣])'
        else: # 영어, 숫자 등 (표준 단어 경계)
            pattern = rf'\b{re.escape(word)}\b'
        
        return len(re.findall(pattern, text))

    def is_better_optimization(self, new_analysis, old_analysis):
        """
        새로운 분석 결과가 이전 분석 결과보다 더 나은지 판단합니다.
        - is_fully_optimized가 True면 최고
        - is_valid_morphemes가 True면 다음
        - is_valid_char_count가 True면 다음
        - 그 외에는 유효하지 않은 형태소 개수가 더 적은 쪽이 좋음
        """
        if new_analysis['is_fully_optimized'] and not old_analysis['is_fully_optimized']:
            return True
        if old_analysis['is_fully_optimized']: # old가 이미 최적화되어 있으면 더 나은 것은 없음
            return False

        # 형태소 유효성 우선
        if new_analysis['is_valid_morphemes'] and not old_analysis['is_valid_morphemes']:
            return True
        if old_analysis['is_valid_morphemes'] and not new_analysis['is_valid_morphemes']:
            return False

        # 글자수 유효성 다음
        if new_analysis['is_valid_char_count'] and not old_analysis['is_valid_char_count']:
            return True
        if old_analysis['is_valid_char_count'] and not new_analysis['is_valid_char_count']:
            return False

        # 유효하지 않은 형태소 개수 비교 (적을수록 좋음)
        new_invalid_morphemes_count = sum(1 for m_info in new_analysis['morpheme_analysis']['counts'].values() if not m_info['is_valid'])
        old_invalid_morphemes_count = sum(1 for m_info in old_analysis['morpheme_analysis']['counts'].values() if not m_info['is_valid'])
        if new_invalid_morphemes_count < old_invalid_morphemes_count:
            return True
        elif new_invalid_morphemes_count > old_invalid_morphemes_count:
            return False

        # 글자수 차이 비교 (목표 중앙값에 가까울수록 좋음)
        target_center = (self.target_min_chars + self.target_max_chars) // 2
        new_char_diff = abs(new_analysis['char_count'] - target_center)
        old_char_diff = abs(old_analysis['char_count'] - target_center)
        if new_char_diff < old_char_diff:
            return True
        
        return False # 동등하거나 더 나쁘면 False
