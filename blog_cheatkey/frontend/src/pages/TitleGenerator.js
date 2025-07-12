// src/pages/TitleGenerator.js
import React, { useState, useEffect, useCallback } from 'react'; // useCallback 추가
import { titleService } from '../api/titleService';
import { keywordService } from '../api/keywordService';
import { contentService } from '../api/contentService';

const TitleGenerator = () => {
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState('');
  // const [titleCount, setTitleCount] = useState(5); // 사용되지 않으므로 주석 처리 또는 삭제
  // const [setTitleCount] = useState(5); // useState는 배열을 반환하므로 이렇게 사용하지 않습니다.
  const [titles, setTitles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [savedTitles, setSavedTitles] = useState([]);
  const [success, setSuccess] = useState(null);
  const [generationStatus, setGenerationStatus] = useState(null);
  const [statusCheckIntervalId, setStatusCheckIntervalId] = useState(null); // interval ID 저장
  const [selectedContentId, setSelectedContentId] = useState(null);

  // 키워드 및 저장된 제목 로드
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const keywordResponse = await keywordService.getKeywords();
        if (Array.isArray(keywordResponse.data)) {
          setKeywords(keywordResponse.data);
        } else if (keywordResponse.data?.results && Array.isArray(keywordResponse.data.results)) {
          setKeywords(keywordResponse.data.results);
        } else {
          setKeywords([]);
        }
      } catch (err) {
        setError('키워드를 불러오는 중 오류가 발생했습니다.');
        console.error('API 오류 (키워드):', err);
      }

      try {
        const savedTitlesResponse = await titleService.getTitles();
        if (Array.isArray(savedTitlesResponse.data)) {
          setSavedTitles(savedTitlesResponse.data);
        } else if (savedTitlesResponse.data?.results && Array.isArray(savedTitlesResponse.data.results)) {
          setSavedTitles(savedTitlesResponse.data.results);
        } else {
          setSavedTitles([]);
        }
      } catch (err) {
        console.error('저장된 제목을 불러오는 중 오류 발생:', err);
        setSavedTitles([]); // 오류 발생 시 빈 배열로 설정
      }
    };

    fetchInitialData();
    
    // 컴포넌트 언마운트 시 인터벌 정리
    return () => {
      if (statusCheckIntervalId) {
        clearInterval(statusCheckIntervalId);
      }
    };
  }, [statusCheckIntervalId]); // statusCheckIntervalId를 의존성 배열에 추가 (정리 로직 때문)

  // 상태 폴링 함수 (useCallback 적용)
  const startStatusPolling = useCallback((contentId) => {
    if (statusCheckIntervalId) {
      clearInterval(statusCheckIntervalId);
    }
    
    const intervalId = setInterval(async () => {
      try {
        const response = await titleService.getStatus(contentId);
        console.log('제목 생성 상태:', response.data);
        
        if (response.data.status === 'completed') {
          setTitles(response.data.data);
          setGenerationStatus('completed');
          setLoading(false);
          setSuccess('제목이 성공적으로 생성되었습니다.');
          clearInterval(intervalId);
          setStatusCheckIntervalId(null); // 인터벌 ID 초기화
        } else if (response.data.status === 'failed') {
            setGenerationStatus('failed');
            setError(response.data.error || '제목 생성에 실패했습니다.');
            setLoading(false);
            clearInterval(intervalId);
            setStatusCheckIntervalId(null);
        }
        // 'processing' 또는 'pending' 상태는 계속 폴링
      } catch (err) {
        console.error('상태 확인 오류:', err);
        // 오류 발생 시 인터벌 중단 또는 사용자에게 알림 등의 처리 추가 가능
        // clearInterval(intervalId);
        // setStatusCheckIntervalId(null);
        // setError('제목 생성 상태 확인 중 오류가 발생했습니다.');
      }
    }, 5000);
    
    setStatusCheckIntervalId(intervalId);
  }, [statusCheckIntervalId]); // statusCheckIntervalId를 의존성 배열에 추가

  // 제목 생성 (useCallback 적용)
  const handleGenerateTitles = useCallback(async () => {
    if (!selectedKeyword) {
      setError('키워드를 선택해주세요.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setGenerationStatus('preparing');
    setTitles([]); // 이전 제목 목록 초기화

    try {
      const contentResponse = await contentService.getContentsByKeyword(selectedKeyword);
      let contentData = [];
      if (Array.isArray(contentResponse.data)) {
        contentData = contentResponse.data;
      } else if (contentResponse.data?.results) {
        contentData = contentResponse.data.results;
      }
      
      if (!contentData || contentData.length === 0) {
        setError('선택한 키워드의 콘텐츠가 없습니다. 먼저 콘텐츠 관리 페이지에서 콘텐츠를 생성해주세요.');
        setLoading(false);
        setGenerationStatus(null);
        return;
      }
      
      const latestContent = contentData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];
      const contentId = latestContent.id;
      setSelectedContentId(contentId); // 폴링을 위해 contentId 저장
      setGenerationStatus('generating');
      
      const response = await titleService.generateTitles({ content_id: contentId });
      console.log('제목 생성 응답:', response.data);
      
      if (response.data.status === 'processing' || response.data.message?.includes('백그라운드')) {
        setGenerationStatus('processing');
        startStatusPolling(contentId);
      } else if (response.data?.data) {
        setTitles(response.data.data);
        setGenerationStatus('completed');
        setLoading(false);
        setSuccess('제목이 성공적으로 생성되었습니다.');
      } else {
        setError(response.data.error || '제목 생성 응답이 올바른 형식이 아닙니다.');
        setLoading(false);
        setGenerationStatus(null);
      }
    } catch (err) {
      console.error('제목 생성 실패:', err);
      if (err.message?.includes('timeout')) {
        setError('서버 응답 시간이 너무 깁니다. 제목은 백그라운드에서 계속 생성되고 있을 수 있습니다.');
        if (selectedContentId) { // selectedContentId가 설정된 경우에만 폴링 시작
            setGenerationStatus('processing');
            startStatusPolling(selectedContentId);
        } else {
            setLoading(false);
            setGenerationStatus(null);
        }
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
        setLoading(false);
        setGenerationStatus(null);
      } else {
        setError('제목 생성 중 오류가 발생했습니다.');
        setLoading(false);
        setGenerationStatus(null);
      }
    }
  }, [selectedKeyword, startStatusPolling, selectedContentId]); // selectedContentId 추가

  // 제목 체크 상태 (useCallback 적용)
  const checkTitleStatus = useCallback(async () => {
    if (!selectedContentId) {
      setError('먼저 제목 생성을 시작하거나, 생성된 콘텐츠가 있는지 확인해주세요.');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const response = await titleService.getStatus(selectedContentId);
      
      if (response.data.status === 'completed') {
        setTitles(response.data.data);
        setGenerationStatus('completed');
        setSuccess('제목이 성공적으로 생성되었습니다.');
      } else if (response.data.status === 'failed') {
        setGenerationStatus('failed');
        setError(response.data.error || '제목 생성에 실패했습니다.');
      } else {
        setGenerationStatus(response.data.status);
        setSuccess(response.data.message || '현재 상태: ' + response.data.status);
      }
    } catch (err) {
      setError('제목 상태 확인 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [selectedContentId]); // selectedContentId를 의존성 배열에 추가

  // 제목 저장 (useCallback 적용)
  const handleSaveTitle = useCallback(async (titleToSave) => { // 파라미터 이름 변경
    if (!selectedKeyword) {
      setError('키워드를 선택해주세요.');
      return;
    }
    // 저장 시에는 selectedContentId를 사용하거나, 다시 조회
    let contentIdToSave = selectedContentId;
    if (!contentIdToSave) {
        try {
            const contentResponse = await contentService.getContentsByKeyword(selectedKeyword);
            let contentData = [];
            if (Array.isArray(contentResponse.data)) contentData = contentResponse.data;
            else if (contentResponse.data?.results) contentData = contentResponse.data.results;

            if (!contentData || contentData.length === 0) {
                setError('선택한 키워드의 콘텐츠가 없습니다.');
                return;
            }
            const latestContent = contentData.sort((a,b) => new Date(b.created_at) - new Date(a.created_at))[0];
            contentIdToSave = latestContent.id;
        } catch (err) {
            setError('콘텐츠 ID 조회 중 오류 발생');
            return;
        }
    }


    try {
      const response = await titleService.saveTitle({
        content_id: contentIdToSave, // 조회된 contentId 사용
        title: titleToSave // 파라미터로 받은 title 사용
      });
      
      if (response.data) {
        setSavedTitles(prev => [...prev, response.data]); // 이전 상태를 기반으로 업데이트
        setError(null);
        setSuccess('제목이 성공적으로 저장되었습니다.');
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      console.error('제목 저장 실패:', err);
      setError('제목 저장 중 오류가 발생했습니다.');
    }
  }, [selectedKeyword, selectedContentId]); // selectedContentId를 의존성 배열에 추가

  const StatusIndicator = () => {
    if (!generationStatus || generationStatus === 'completed' || generationStatus === 'failed') return null;
    
    let message = '';
    let color = 'yellow';
    
    switch (generationStatus) {
      case 'preparing': message = '콘텐츠 정보를 조회 중입니다...'; break;
      case 'generating': message = '제목을 생성하는 중입니다...'; break;
      case 'processing': message = '제목이 백그라운드에서 생성 중입니다. 잠시 후 자동으로 표시됩니다...'; color = 'blue'; break;
      case 'pending': message = '제목 생성이 대기 중입니다.'; break;
      default: message = '처리 중입니다...';
    }
    
    return (
      <div className={`bg-${color}-100 border-l-4 border-${color}-500 text-${color}-700 p-4 mb-4`}>
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
          <p>{message}</p>
        </div>
      </div>
    );
  };

  const renderTitleLists = () => {
    if (!titles || Object.keys(titles).length === 0) return null;
    
    return (
      <div className="space-y-6">
        {Object.entries(titles).map(([type, typeItems]) => (
          <div key={type} className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-medium mb-2">
              {/* 제목 유형 한국어 매핑 */}
              { { general: '일반 상식 반박형', approval: '인정욕구 자극형', secret: '숨겨진 비밀형', trend: '트렌드 제시형', failure: '실패담 공유형', comparison: '비교형', warning: '경고형', blame: '남탓 공감형', beginner: '초보자 가이드형', benefit: '효과 제시형' }[type] || type }
            </h3>
            <ul className="space-y-2">
              {Array.isArray(typeItems) && typeItems.map((item, index) => ( // typeItems가 배열인지 확인
                <li key={index} className="flex justify-between items-center border-b pb-2">
                  <span>{item.suggestion || item.title}</span>
                  <button 
                    onClick={() => handleSaveTitle(item.suggestion || item.title)}
                    className="text-sm bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded"
                  >
                    저장
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  };

  const renderSavedTitles = () => {
    if (!savedTitles.length) return null;
    
    return (
      <div className="bg-white rounded-lg shadow p-4 mt-8">
        <h2 className="text-lg font-semibold mb-2">저장된 제목</h2>
        <ul className="space-y-2">
          {savedTitles.map(item => (
            <li key={item.id} className="flex justify-between items-center border-b pb-2">
              <div>
                <span>{item.suggestion || item.title}</span>
                {item.content_detail?.keyword_detail?.keyword && ( // 옵셔널 체이닝 사용
                  <span className="ml-2 text-sm text-gray-500">
                    ({item.content_detail.keyword_detail.keyword})
                  </span>
                )}
              </div>
              {item.created_at && (
                <span className="text-sm text-gray-500">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">제목 생성기</h1>
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
          {error}
        </div>
      )}
      
      {success && (
        <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4">
          {success}
        </div>
      )}
      
      <StatusIndicator />
      
      <div className="bg-white rounded-lg shadow p-4 mb-8">
        <h2 className="text-lg font-semibold mb-2">블로그 제목 생성</h2>
        
        <div className="mb-4">
          <label htmlFor="keyword-select-tg" className="block text-sm font-medium text-gray-700 mb-1">
            키워드 선택
          </label>
          <select 
            id="keyword-select-tg"
            className="w-full border rounded p-2"
            value={selectedKeyword}
            onChange={(e) => {
                setSelectedKeyword(e.target.value);
                setTitles([]); // 키워드 변경 시 생성된 제목 초기화
                setGenerationStatus(null); // 상태 초기화
                setSelectedContentId(null); // 선택된 콘텐츠 ID 초기화
                if(statusCheckIntervalId) clearInterval(statusCheckIntervalId); // 이전 폴링 중지
            }}
            disabled={loading}
          >
            <option value="">키워드 선택</option>
            {Array.isArray(keywords) && keywords.map(keyword => (
              <option key={keyword.id} value={keyword.id}>
                {keyword.keyword}
              </option>
            ))}
          </select>
          
          {keywords.length === 0 && !loading && ( // 로딩 중 아닐 때만 표시
            <div className="text-red-500 mt-1 p-2 bg-red-50 rounded">
              <p>분석된 키워드가 없습니다. 키워드 관리에서 키워드를 추가하고 분석해주세요.</p>
              <p className="text-sm mt-1">키워드가 이미 분석되었다면 '새로고침' 버튼을 눌러보세요.</p>
            </div>
          )}
        </div>
        
        <div className="flex flex-wrap gap-2 mt-4">
          <button 
            onClick={handleGenerateTitles}
            disabled={loading || !selectedKeyword}
            className={`${
              loading || !selectedKeyword
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600'
            } text-white px-4 py-2 rounded`}
          >
            {loading ? '생성 중...' : '제목 생성하기'}
          </button>
          
          {(generationStatus === 'processing' || generationStatus === 'generating' || generationStatus === 'pending') && selectedContentId && (
            <button 
              onClick={checkTitleStatus}
              disabled={loading}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
            >
              제목 생성 상태 확인
            </button>
          )}
          
          <button 
            onClick={() => window.location.reload()} // 간단한 새로고침
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
          >
            페이지 새로고침
          </button>
        </div>
      </div>
      
      {renderTitleLists()}
      {renderSavedTitles()}
    </div>
  );
};

export default TitleGenerator;
