# 블로그치트키 (Blog CheatKey)
![블로그치트키 로고](https://imgur.com/a/wJW3dmu)
## 📝 서비스 소개

**블로그치트키**는 블로거와 콘텐츠 제작자들을 위한 AI 기반 콘텐츠 생성 플랫폼입니다. 키워드 분석부터 전문적인 블로그 콘텐츠 작성까지, 고품질 콘텐츠 제작 과정을 자동화하여 시간과 노력을 크게 절약해 드립니다.

### 왜 블로그치트키인가?

현대 디지털 마케팅 환경에서 콘텐츠는 왕입니다. 그러나 경쟁이 치열해지면서 단순한 콘텐츠만으로는 차별화가 어려워졌습니다. 블로그치트키는 이런 문제를 해결하기 위해 탄생했습니다:

1. **시간 절약**: 콘텐츠 리서치와 작성에 소요되는 시간을 최대 80%까지 절감
2. **전문성 강화**: AI가 해당 분야의 전문 지식을 바탕으로 깊이 있는 콘텐츠 생성
3. **SEO 최적화**: 키워드 분석을 통해 검색엔진 최적화된 콘텐츠 제작
4. **일관성 유지**: 브랜드 톤앤매너를 반영한 일관된 콘텐츠 생산

## 🚧 현재 개발 상태 

이 프로젝트는 현재 개발 중이며, 아래 기능들이 구현되어 있습니다:

- ✅ 키워드 분석 및 관리 기능
- ✅ AI 기반 콘텐츠 생성
- ✅ 업체 정보 관리 및 저장
- ✅ 콘텐츠 관리 및 보기

다음 기능들은 개발 예정입니다:

- 🔄 소셜 로그인 통합
- 🔄 도커화 및 배포 설정
- 🔄 고급 분석 대시보드
- 🔄 SEO 성능 추적

## ✨ 주요 기능

### 🔍 키워드 분석
- 키워드 의도 분석 (검색 의도 파악)
- 관련 키워드 추천
- 키워드 경쟁력 평가

### 📊 콘텐츠 생성
- AI 기반 전문 콘텐츠 자동 생성
- 업체/브랜드 정보 맞춤형 콘텐츠
- 섹션별 구조화된 콘텐츠 제작

### 🏷️ 제목 최적화
- 클릭을 유도하는 매력적인 제목 추천
- SEO 최적화된 제목 생성

### 💼 업체 정보 관리
- 업체 프로필 저장 및 관리
- 콘텐츠에 자동으로 전문성 반영

### 📱 반응형 인터페이스
- 모바일, 태블릿, 데스크톱 완벽 지원
- 직관적인 사용자 경험

## 🚀 서비스 효과

블로그치트키를 사용하면 다음과 같은 효과를 얻을 수 있습니다:

### 📈 콘텐츠 생산성 향상
- 일일 콘텐츠 생산량 3배 증가
- 아이디어 구상부터 발행까지 시간 단축

### 🔝 콘텐츠 품질 개선
- 전문성이 반영된 고품질 콘텐츠
- SEO 최적화로 검색 노출 증가

### 💰 마케팅 비용 절감
- 외부 콘텐츠 제작자 의존도 감소
- 콘텐츠 마케팅 ROI 개선

### 🛠️ 워크플로우 최적화
- 콘텐츠 제작 프로세스 간소화
- 팀 협업 효율성 증대

## 💻 기술 스택

### 프론트엔드
- React
- React Router
- Tailwind CSS
- Axios

### 백엔드
- Django
- Django REST Framework
- Celery (비동기 작업 처리)

### 데이터베이스
- SQLite (개발)
- PostgreSQL (프로덕션 예정)

### AI 통합
- OpenAI API
- Claude API

## 🔧 설치 및 실행

### 요구사항
- Python 3.8+
- Node.js 14+
- npm 또는 yarn

### 백엔드 설정
```bash
# 저장소 클론
git clone https://github.com/your-username/blog-cheatkey.git
cd blog-cheatkey

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 필요한 API 키 등 설정

# 데이터베이스 마이그레이션
python manage.py migrate

# 서버 실행
python manage.py runserver
```

### 프론트엔드 설정
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

## 📝 사용 가이드

1. **계정 생성**: 이메일 주소로 회원가입
2. **키워드 분석**: 타겟 키워드 입력 및 분석 시작
3. **콘텐츠 생성**: 분석된 키워드 선택 및 업체 정보 입력
4. **콘텐츠 관리**: 생성된 콘텐츠 확인, 수정, 삭제
5. **콘텐츠 활용**: HTML 형식으로 복사하여 블로그/웹사이트에 게시

## 🤝 기여하기

블로그치트키 프로젝트에 기여하고 싶으시다면:

1. 이 저장소를 포크합니다.
2. 새 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 열어주세요.

## 💡 향후 개발 계획

1. **소셜 로그인**: Google, Facebook, Kakao, Naver 로그인 통합
2. **도커화**: 개발 및 배포 환경 도커화
3. **고급 분석 대시보드**: 콘텐츠 성과 및 키워드 트렌드 분석
4. **API 확장**: 외부 서비스와의 통합을 위한 API 엔드포인트 확장
5. **배포 자동화**: CI/CD 파이프라인 구축

## 📜 라이선스

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 자세한 정보는 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 연락처

프로젝트 관리자 - wnsghcoswp@gmail.com

프로젝트 링크: [https://github.com/ohjunho421/blogcheatkey_web](https://github.com/ohjunho421/blogcheatkey_web)

## 🙏 감사의 말

- [OpenAI](https://openai.com)
- [Anthropic](https://anthropic.com)
- 모든 기여자분들과 사용자분들께 감사드립니다!

# 블로그치트키 설치 가이드

> **GitHub 저장소**: [https://github.com/ohjunho421/blogcheatkey_web](https://github.com/ohjunho421/blogcheatkey_web)

이 문서는 블로그치트키 서비스의 로컬 개발 환경 설정 과정을 설명합니다.

## 목차
1. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
2. [환경 변수 설정](#환경-변수-설정)
3. [문제 해결](#문제-해결)
4. [향후 개발 계획](#향후-개발-계획)

## 로컬 개발 환경 설정

### 사전 요구사항
- Python 3.8 이상
- Node.js 14 이상
- npm 또는 yarn
- Git

### 백엔드 설정

1. 저장소 클론
   ```bash
   git clone https://github.com/ohjunho421/blogcheatkey_web.git
   cd blogcheatkey_web
   ```

2. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   
   # macOS/Linux
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정
   ```bash
   cp .env.example .env
   ```
   
   `.env` 파일을 편집하여 필요한 API 키와 설정을 추가합니다.

5. 데이터베이스 마이그레이션
   ```bash
   python manage.py migrate
   ```

6. 개발 서버 실행
   ```bash
   python manage.py runserver
   ```
   
   백엔드 서버가 http://localhost:8000 에서 실행됩니다.

### 프론트엔드 설정

1. 프론트엔드 디렉토리로 이동
   ```bash
   cd frontend
   ```

2. 의존성 설치
   ```bash
   npm install
   # 또는
   yarn install
   ```

3. 개발 서버 실행
   ```bash
   npm start
   # 또는
   yarn start
   ```
   
   프론트엔드 개발 서버가 http://localhost:3000 에서 실행됩니다.

### API 클라이언트 설정

프로젝트의 `frontend/src/api/client.js` 파일을 확인하여 API 클라이언트가 올바르게 설정되어 있는지 확인합니다:

```javascript
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30초 타임아웃
});

// 인증 토큰이 있는 경우 헤더에 추가
client.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default client;
```

## 환경 변수 설정

`.env` 파일에 설정해야 하는 주요 환경 변수:

```
# Django 설정
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 외부 API 키
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## 문제 해결

### 일반적인 문제 해결

1. **"Broken pipe" 오류 발생 시**
   
   이 오류는 주로 네트워크 연결 문제 또는 요청 타임아웃으로 인해 발생합니다.
   
   **해결책**:
   - API 요청의 타임아웃 값을 늘리세요 (특히 콘텐츠 생성과 같은 장시간 작업)
   - 재시도 로직을 구현하세요:
     ```javascript
     // src/api/contentService.js에 재시도 로직 추가
     const requestWithRetry = async (requestFn, retryConfig = {}) => {
       const { 
         maxRetries = 3, 
         retryDelay = 1000, 
         timeout = 30000 
       } = retryConfig;
       
       let retries = 0;
       
       while (retries <= maxRetries) {
         try {
           // 요청 시도
           const response = await requestFn();
           return response;
         } catch (error) {
           retries++;
           
           // 최대 재시도 횟수 초과
           if (retries > maxRetries) {
             throw error;
           }
           
           console.log(`요청 실패, 재시도 중... (${retries}/${maxRetries})`);
           
           // 지수 백오프: 점점 더 길게 기다림
           const delay = retryDelay * Math.pow(2, retries - 1);
           await new Promise(r => setTimeout(r, delay));
         }
       }
     };
     ```
   - 백엔드의 타임아웃 설정 증가:
     ```python
     # settings.py
     DEFAULT_TIMEOUT = 300  # 5분으로 설정
     ```

2. **프론트엔드에서 API 연결 오류**
   
   **해결책**:
   - 백엔드 서버가 실행 중인지 확인
   - CORS 설정 확인 (settings.py에서 CORS_ALLOWED_ORIGINS 또는 CORS_ALLOW_ALL_ORIGINS 확인)
   - API 엔드포인트 URL 확인
   - 브라우저 콘솔에서 네트워크 오류 확인

3. **콘텐츠 생성 시간이 너무 길 때**
   
   **해결책**:
   - 상태 확인 주기 최적화:
     ```javascript
     // 콘텐츠 생성 상태 확인 로직 개선
     let retryDelay = 2000; // 초기 2초
     const maxDelay = 10000; // 최대 10초
     
     const checkContentStatus = async () => {
       // 상태 확인 로직...
       
       // 아직 생성 중이면 점점 더 긴 간격으로 다시 확인
       retryDelay = Math.min(retryDelay * 1.5, maxDelay);
       setTimeout(checkContentStatus, retryDelay);
     };
     ```
   - 로컬 캐싱 사용:
     ```javascript
     // 생성된 콘텐츠 로컬 캐싱
     localStorage.setItem('cachedContentData', JSON.stringify(contentData));
     ```

### 특정 문제 해결

1. **BusinessInfoSelector 컴포넌트 경로 오류**
   
   `ERROR in ./src/pages/ContentManagement.js 9:0-58 Module not found: Error: Can't resolve './BusinessInfoSelector'`
   
   **해결책**:
   - BusinessInfoSelector.js 파일을 올바른 경로에 생성했는지 확인
   - import 경로를 수정:
     ```javascript
     // 잘못된 경로
     import BusinessInfoSelector from './BusinessInfoSelector';
     
     // 올바른 경로 (components 폴더에 있는 경우)
     import BusinessInfoSelector from '../components/BusinessInfoSelector';
     ```
   - 또는 현재 폴더에 파일 생성:
     ```bash
     # ContentManagement.js와 같은 폴더에 파일 생성
     touch src/pages/BusinessInfoSelector.js
     ```

## 향후 개발 계획

### 소셜 로그인 구현 (예정)

향후 업데이트에서 구현될 소셜 로그인을 위한 설정 방법입니다:

1. 소셜 로그인 Provider 등록
   - Google: https://console.developers.google.com/
   - Facebook: https://developers.facebook.com/
   - Kakao: https://developers.kakao.com/
   - Naver: https://developers.naver.com/main/

2. Django settings.py에 추가 예정:
   ```python
   INSTALLED_APPS = [
       # 기존 앱들...
       'allauth',
       'allauth.account',
       'allauth.socialaccount',
       'allauth.socialaccount.providers.google',
       'allauth.socialaccount.providers.facebook',
       'allauth.socialaccount.providers.kakao',
       'allauth.socialaccount.providers.naver',
   ]
   ```

### 도커 설정 (예정)

향후 업데이트에서 구현될 도커 설정 계획:

1. 백엔드, 프론트엔드, 데이터베이스를 위한 개별 Dockerfile 생성
2. docker-compose.yml 파일로 다중 컨테이너 오케스트레이션
3. 개발 및 프로덕션 환경을 위한 분리된 설정

### 배포 설정 (예정)

향후 업데이트에서 구현될 배포 방법 계획:

1. AWS, GCP 또는 Azure와 같은 클라우드 서비스에 배포
2. PostgreSQL 데이터베이스로 마이그레이션
3. Nginx를 사용한 웹 서버 설정
4. CI/CD 파이프라인 구축

## 지원 및 문의

프로젝트 관련 질문이나 문제가 있으시면 이슈를 등록하거나 다음 연락처로 문의해 주세요:

- GitHub 이슈: [https://github.com/ohjunho421/blogcheatkey_web/issues](https://github.com/ohjunho421/blogcheatkey_web/issues)
- 이메일: wnsghcoswp@gmail.com# blog_cheatkey_optimize
