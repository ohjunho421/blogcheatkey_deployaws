// MobileFormatter.js
// 모바일 화면에 최적화된 줄바꿈 포맷팅을 위한 유틸리티 클래스

class MobileFormatter {
  /**
   * 모바일 화면에 최적화된 포맷으로 콘텐츠 변환
   * 한글 기준 적절한 위치에서 자연스럽게 줄바꿈 처리
   * 
   * @param {string} content - 변환할 원본 콘텐츠
   * @returns {string} - 모바일 최적화된 콘텐츠
   */
  static formatForMobile(content) {
    if (!content) return '';
    
    const lines = content.split('\n');
    const formattedLines = [];
    
    for (let line of lines) {
      const trimmedLine = line.trim();
      // 마크다운 제목, 빈 줄, 목록, 코드 블록 등은 그대로 유지
      if (trimmedLine.startsWith('#') || 
          !trimmedLine || 
          trimmedLine.match(/^(-\s|\*\s|\d+\.\s)/) || 
          trimmedLine.startsWith('```') || 
          trimmedLine.startsWith('---') || 
          trimmedLine.startsWith('|')) {
        formattedLines.push(line);
        continue;
      }
      
      this._addFormattedText(line, formattedLines);
    }
    
    return formattedLines.join('\n');
  }
  
  /**
   * 텍스트를 자연스러운 위치에서 줄바꿈하여 추가
   * 
   * @param {string} text - 줄바꿈할 텍스트
   * @param {Array} linesArray - 결과를 저장할 배열
   * @private
   */
  static _addFormattedText(text, linesArray) {
    if (!text.trim()) {
      linesArray.push(text);
      return;
    }
    
    const chunks = [];
    let currentChunk = '';
    let charCount = 0;
    const TARGET_LENGTH = 20;
    const words = text.split(' ');
    
    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      
      if (word.length > TARGET_LENGTH * 1.5) {
        if (currentChunk) {
          chunks.push(currentChunk);
          currentChunk = '';
          charCount = 0;
        }
        let remainingWord = word;
        while (remainingWord.length > TARGET_LENGTH) {
          chunks.push(remainingWord.substring(0, TARGET_LENGTH));
          remainingWord = remainingWord.substring(TARGET_LENGTH);
        }
        if (remainingWord) {
          currentChunk = remainingWord;
          charCount = remainingWord.length;
        }
        continue;
      }
      
      const wordLength = word.length;
      // 공백 포함한 길이로 계산하면 더 자연스러울 수 있으나, 여기서는 순수 글자 수 기준
      const newLength = charCount + (currentChunk ? 1 : 0) + wordLength; 
      
      // ESLint: no-mixed-operators 경고 해결을 위해 괄호 추가
      const shouldBreak = (newLength > TARGET_LENGTH) || 
                          ( (newLength > TARGET_LENGTH * 0.7) && 
                            ( currentChunk.endsWith(',') || 
                              currentChunk.endsWith('.') || 
                              currentChunk.endsWith('?') || 
                              currentChunk.endsWith('!') ||
                              currentChunk.endsWith(':') ||
                              currentChunk.endsWith(';') )
                          );
      
      if (shouldBreak && currentChunk) {
        chunks.push(currentChunk);
        currentChunk = word;
        charCount = wordLength;
      } else {
        if (currentChunk) {
          currentChunk += ' ' + word;
        } else {
          currentChunk = word;
        }
        // charCount는 순수 글자 수로 유지 (공백 제외)
        charCount = currentChunk.replace(/\s/g, '').length;
      }
    }
    
    if (currentChunk) {
      chunks.push(currentChunk);
    }
    
    linesArray.push(...chunks);
  }
  
  /**
   * HTML 콘텐츠에 모바일 최적화 포맷 적용
   * dangerouslySetInnerHTML과 함께 사용할 수 있는 형태로 변환
   * 
   * @param {string} htmlContent - HTML 형식의 콘텐츠
   * @returns {string} - 모바일 최적화된 HTML 콘텐츠
   */
  static formatHtmlForMobile(htmlContent) {
    if (!htmlContent) return '';
    
    let textContent = htmlContent.replace(/<br\s*\/?>/gi, '\n');
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = textContent;
    textContent = tempDiv.textContent || tempDiv.innerText || '';
    
    const formattedText = this.formatForMobile(textContent);
    
    return formattedText.replace(/\n/g, '<br>');
  }
}

export default MobileFormatter;
