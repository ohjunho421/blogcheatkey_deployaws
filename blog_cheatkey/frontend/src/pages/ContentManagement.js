// src/pages/ContentManagement.js
import React, { useState, useEffect, useCallback } from 'react';
import { contentService } from '../api/contentService';
import { keywordService } from '../api/keywordService';
import { researchService } from '../api/researchService';
import { useNavigate } from 'react-router-dom';
import BusinessInfoSelector from './BusinessInfoSelector'; // 경로 확인 필요

function ContentManagement() {
  const [contents, setContents] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [businessName, setBusinessName] = useState('');
  const [expertise, setExpertise] = useState('');
  const [customMorphemes, setCustomMorphemes] = useState('');
  const [generatingContent, setGeneratingContent] = useState(false);
  const [networkStatus, setNetworkStatus] = useState(navigator.onLine);
  const [statusCheckIntervalId, setStatusCheckIntervalId] = useState(null);
  const [collectingResearch, setCollectingResearch] = useState(false);
  const [researchCollected, setResearchCollected] = useState(false);
  const [researchStats, setResearchStats] = useState(null);
  const [processingStep, setProcessingStep] = useState('');
  const navigate = useNavigate();

  const loadData = useCallback(async (isRetry = false) => {
    const MAX_RETRIES = 3;
    let currentRetry = isRetry ? 1 : 0; 
    let loadErrorOccurred = false; // 에러 발생 여부 플래그

    if (!isRetry) {
        setLoading(true);
    }
    setRefreshing(true);
    setError(null);

    const attemptLoad = async () => {
      try {
        console.log(`데이터 로드 시도 (재시도: ${currentRetry})`);
        
        const keywordResponse = await keywordService.getKeywords();
        let keywordData = [];
        if (Array.isArray(keywordResponse.data)) {
          keywordData = keywordResponse.data;
        } else if (keywordResponse.data?.results && Array.isArray(keywordResponse.data.results)) {
          keywordData = keywordResponse.data.results;
        }
        const analyzedKeywords = keywordData.filter(k => k.main_intent);
        setKeywords(analyzedKeywords);
        
        const contentResponse = await contentService.getContents();
        let contentData = [];
        if (Array.isArray(contentResponse.data)) {
          contentData = contentResponse.data;
        } else if (contentResponse.data?.results && Array.isArray(contentResponse.data.results)) {
          contentData = contentResponse.data.results;
        }
        setContents(contentData);
        
        localStorage.setItem('cachedContentData', JSON.stringify(contentData));
        loadErrorOccurred = false; // 성공 시 에러 플래그 초기화

      } catch (err) {
        console.error('데이터 로드 실패:', err);
        loadErrorOccurred = true; // 에러 발생 플래그 설정
        currentRetry++;
        if (currentRetry < MAX_RETRIES && networkStatus) {
          setError(`데이터 로드 오류. 재시도 중... (${currentRetry}/${MAX_RETRIES})`);
          const retryDelay = 1000 * Math.pow(2, currentRetry - 1);
          await new Promise(r => setTimeout(r, retryDelay));
          return attemptLoad();
        } else if (!networkStatus) {
          setError('네트워크 연결이 끊겼습니다. 연결 후 다시 시도해주세요.');
        } else {
          setError('데이터를 불러오는 데 실패했습니다. 잠시 후 다시 시도해주세요.');
        }
      } finally {
        // 모든 시도 후 또는 성공 시 로딩 상태 해제
        if (currentRetry >= MAX_RETRIES || !loadErrorOccurred || !networkStatus) {
            setLoading(false);
            setRefreshing(false);
        }
      }
    };
    
    await attemptLoad();
  }, [networkStatus]);

  useEffect(() => {
    const handleOnline = () => {
      setNetworkStatus(true);
      console.log('네트워크 연결됨, 데이터 다시 로드 시도');
      if (error && error.includes('네트워크')) { 
        loadData(true);
      }
    };
    const handleOffline = () => {
      setNetworkStatus(false);
      console.log('네트워크 연결 끊김');
      setError('네트워크 연결이 끊겼습니다. 인터넷 연결을 확인해주세요.');
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [loadData, error]);

  useEffect(() => {
    try {
      const cachedData = localStorage.getItem('cachedContentData');
      if (cachedData) {
        const parsedData = JSON.parse(cachedData);
        setContents(parsedData);
        setLoading(false);
        console.log('캐시된 콘텐츠 데이터를 로드했습니다.');
      }
    } catch (err) {
      console.error('캐시된 데이터 복원 실패:', err);
    }
    loadData();
  }, [loadData]);

  function handleKeywordChange(e) {
    setSelectedKeyword(e.target.value);
    setResearchCollected(false);
    setResearchStats(null);
  }

  const collectResearchData = useCallback(async () => {
    if (!selectedKeyword) {
      setError('키워드를 선택해주세요.');
      return false;
    }
    if (!businessName.trim() || !expertise.trim()) {
      setError('업체명과 전문성/경력은 필수 입력 사항입니다.');
      return false;
    }
    
    try {
      setCollectingResearch(true);
      setProcessingStep('research');
      setError(null);
      
      const response = await researchService.collectResearch(selectedKeyword);
      
      if (response.data) {
        let isCompleted = false;
        let attempts = 0;
        const MAX_ATTEMPTS = 30;
        
        while (!isCompleted && attempts < MAX_ATTEMPTS) {
          attempts++;
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          try {
            const statusResponse = await researchService.checkResearchStatus(selectedKeyword);
            if (statusResponse.data.status === 'completed') {
              isCompleted = true;
              setResearchStats({
                newsCount: statusResponse.data.data?.news_count || 0,
                academicCount: statusResponse.data.data?.academic_count || 0,
                generalCount: statusResponse.data.data?.general_count || 0,
                statisticsCount: statusResponse.data.data?.statistics_count || 0
              });
              setResearchCollected(true);
              break;
            } else if (statusResponse.data.status === 'failed') {
              throw new Error(statusResponse.data.error || '연구 자료 수집 실패');
            }
          } catch (statusError) {
            console.error('상태 확인 중 오류:', statusError);
          }
        }
        
        if (!isCompleted) {
          setError('연구 자료 수집 시간이 초과되었습니다. 다시 시도해주세요.');
          setResearchCollected(false);
          setCollectingResearch(false);
          return false;
        }
        setCollectingResearch(false);
        return true;
      } else {
        throw new Error('응답 데이터가 없습니다');
      }
    } catch (err) {
      console.error('연구 자료 수집 실패:', err);
      setError('연구 자료 수집 중 오류가 발생했습니다: ' + (err.message || '알 수 없는 오류'));
      setCollectingResearch(false);
      return false;
    }
  }, [selectedKeyword, businessName, expertise]);

  const confirmSubtopics = useCallback(async () => {
    if (!selectedKeyword) {
      setError('키워드를 선택해주세요.');
      return false;
    }
    try {
      const keywordDetail = await keywordService.getKeyword(selectedKeyword);
      const subtopics = keywordDetail.data.subtopics || [];
      if (subtopics.length === 0) {
        return window.confirm('이 키워드에는 소제목이 없습니다. 계속 진행하시겠습니까?');
      }
      const subtopicsList = subtopics.map((st, idx) => `${idx+1}. ${st.title || st}`).join('\n');
      const confirmMsg = `다음 소제목을 기준으로 콘텐츠를 생성합니다:\n\n${subtopicsList}\n\n계속 진행하시겠습니까?`;
      return window.confirm(confirmMsg);
    } catch (err) {
      console.error('소제목 확인 중 오류:', err);
      setError('소제목 확인 중 오류가 발생했습니다.');
      return false;
    }
  }, [selectedKeyword]);

  const startStatusPolling = useCallback((keywordIdToPoll) => {
    if (statusCheckIntervalId) {
      clearInterval(statusCheckIntervalId);
    }
    
    const intervalId = setInterval(async () => {
      try {
        const statusResponse = await contentService.getContentGenerationStatus(keywordIdToPoll);
        console.log('상태 확인 응답:', statusResponse.data);
        
        if (statusResponse.data.status === 'completed') {
          clearInterval(intervalId);
          setStatusCheckIntervalId(null);
          setGeneratingContent(false);
          setLoading(false);
          loadData();
          setSelectedKeyword('');
          setBusinessName('');
          setExpertise('');
          setCustomMorphemes('');
          setResearchCollected(false);
          setResearchStats(null);
          setProcessingStep('');
        } else if (statusResponse.data.status === 'failed') {
          clearInterval(intervalId);
          setStatusCheckIntervalId(null);
          setError(statusResponse.data.error || '콘텐츠 생성 실패');
          setGeneratingContent(false);
          setLoading(false);
          setProcessingStep('');
        }
      } catch (err) {
        console.error('상태 확인 오류:', err);
      }
    }, 5000);
    
    setStatusCheckIntervalId(intervalId);
  }, [loadData, statusCheckIntervalId]);

  const handleContentGeneration = useCallback(async () => {
    const confirmed = await confirmSubtopics();
    if (!confirmed) return;

    if (!selectedKeyword) {
      setError('키워드를 선택해주세요.');
      return;
    }
    if (!businessName.trim() || !expertise.trim()) {
      setError('업체명과 전문성/경력은 필수 입력 사항입니다.');
      return;
    }
    
    let researchSuccess = researchCollected;
    if (!researchCollected) {
      researchSuccess = await collectResearchData();
      if (!researchSuccess) return;
    }
    
    try {
      setLoading(true);
      setGeneratingContent(true);
      setProcessingStep('content');
      setError(null);
      
      const morphemesArray = customMorphemes.trim() 
        ? customMorphemes.split(/\s+/).filter(m => m.trim() !== '') 
        : [];
      
      const requestData = {
        keyword_id: selectedKeyword,
        target_audience: {},
        business_info: { name: businessName, expertise: expertise },
        custom_morphemes: morphemesArray
      };
      
      const response = await contentService.createContent(requestData);
      console.log('콘텐츠 생성 응답:', response.data);
      
      startStatusPolling(selectedKeyword); 
      
    } catch (err) {
      console.error('콘텐츠 생성 실패:', err);
      setError('콘텐츠 생성 중 오류가 발생했습니다: ' + (err.message || '알 수 없는 오류'));
      setGeneratingContent(false);
      setLoading(false);
      setProcessingStep('');
    }
  }, [
    selectedKeyword, 
    businessName, 
    expertise, 
    customMorphemes, 
    researchCollected, 
    collectResearchData, 
    confirmSubtopics, 
    startStatusPolling
  ]);

  useEffect(() => {
    return () => {
      if (statusCheckIntervalId) {
        clearInterval(statusCheckIntervalId);
      }
    };
  }, [statusCheckIntervalId]);

  if (loading && !refreshing && !generatingContent && !collectingResearch) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2"></div>
          <p>로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">콘텐츠 관리</h1>
        <div className="flex items-center space-x-2">
          {!networkStatus && (
            <div className="bg-red-100 text-red-700 px-3 py-1 rounded-md text-sm">
              오프라인 모드
            </div>
          )}
          <button 
            onClick={() => loadData()}
            disabled={refreshing || !networkStatus}
            className={`px-4 py-2 rounded text-white ${
              refreshing || !networkStatus ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            {refreshing ? '새로고침 중...' : '데이터 새로고침'}
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 flex justify-between items-center">
          <div>{error}</div>
          {error.includes('데이터를 불러오는 중') && networkStatus && (
            <button 
              onClick={() => loadData(true)}
              className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 text-sm"
            >
              다시 시도
            </button>
          )}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow p-4 mb-8">
        <h2 className="text-lg font-semibold mb-2">새 콘텐츠 생성</h2>
        
        <div className="mb-4">
          <label htmlFor="keyword-select-cm" className="block text-gray-700 mb-2">키워드 선택</label>
          <select 
            id="keyword-select-cm"
            className="w-full border rounded p-2"
            value={selectedKeyword}
            onChange={handleKeywordChange}
            disabled={generatingContent || collectingResearch || !networkStatus}
          >
            <option value="">키워드 선택</option>
            {keywords.map((keyword) => (
              <option key={keyword.id} value={keyword.id}>
                {keyword.keyword}
              </option>
            ))}
          </select>
          
          {keywords.length === 0 && !loading && (
            <div className="text-red-500 mt-1 p-2 bg-red-50 rounded">
              <p>분석된 키워드가 없습니다. 키워드 관리에서 키워드를 추가하고 분석해주세요.</p>
              <p className="text-sm mt-1">키워드가 이미 분석되었다면 '데이터 새로고침' 버튼을 눌러보세요.</p>
            </div>
          )}
        </div>
        
        <BusinessInfoSelector
          businessName={businessName}
          setBusinessName={setBusinessName}
          expertise={expertise}
          setExpertise={setExpertise}
          disabled={generatingContent || collectingResearch || !networkStatus}
        />
        
        <div className="mb-4 mt-4">
          <label htmlFor="custom-morphemes-input" className="block text-gray-700 mb-2">
            추가 형태소 (선택사항)
          </label>
          <input
            id="custom-morphemes-input"
            type="text"
            className="w-full border rounded p-2"
            placeholder="추가하고 싶은 형태소를 띄어쓰기로 구분하여 입력하세요 (예: 자동차 수리 점검)"
            value={customMorphemes}
            onChange={(e) => setCustomMorphemes(e.target.value)}
            disabled={generatingContent || collectingResearch || !networkStatus}
          />
          <p className="text-sm text-gray-500 mt-1">
            콘텐츠에 추가로 포함시키고 싶은 핵심 단어나 형태소를 입력하세요.
          </p>
        </div>

        {selectedKeyword && (
          <button 
            onClick={handleContentGeneration}
            disabled={loading || generatingContent || collectingResearch || !businessName.trim() || !expertise.trim() || !networkStatus}
            className={`text-white px-4 py-2 rounded w-full mt-4 ${
              loading || generatingContent || collectingResearch || !businessName.trim() || !expertise.trim() || !networkStatus
                ? 'bg-gray-400 cursor-not-allowed' 
                : researchCollected 
                  ? 'bg-green-500 hover:bg-green-600'
                  : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            {generatingContent || collectingResearch 
              ? processingStep === 'research' 
                ? '연구 자료 수집 중...' 
                : '콘텐츠 생성 중...'
              : researchCollected
                ? '콘텐츠 생성 시작'
                : '자료 수집 후 콘텐츠 생성하기'
            }
          </button>
        )}
        
        {researchCollected && researchStats && (
          <div className="mt-4 bg-green-50 p-3 rounded border border-green-200">
            <p className="text-green-700 font-medium">연구 자료 수집 완료</p>
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div className="bg-white p-2 rounded border border-green-100">
                <p className="text-sm text-gray-600">뉴스 자료</p>
                <p className="font-bold text-green-600">{researchStats.newsCount} 개</p>
              </div>
              <div className="bg-white p-2 rounded border border-green-100">
                <p className="text-sm text-gray-600">학술 자료</p>
                <p className="font-bold text-green-600">{researchStats.academicCount} 개</p>
              </div>
              <div className="bg-white p-2 rounded border border-green-100">
                <p className="text-sm text-gray-600">일반 자료</p>
                <p className="font-bold text-green-600">{researchStats.generalCount} 개</p>
              </div>
              <div className="bg-white p-2 rounded border border-green-100">
                <p className="text-sm text-gray-600">통계 데이터</p>
                <p className="font-bold text-green-600">{researchStats.statisticsCount} 개</p>
              </div>
            </div>
          </div>
        )}
        
        {(generatingContent || collectingResearch) && (
          <div className="mt-4 bg-yellow-50 p-3 rounded border border-yellow-200">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-500 mr-2"></div>
              <div>
                {processingStep === 'research' ? (
                  <div>
                    <p className="text-yellow-700">연구 자료를 수집하고 있습니다. 이 작업은 30초 정도 소요될 수 있습니다.</p>
                    <p className="text-sm text-yellow-600">수집된 자료는 콘텐츠 생성에 활용됩니다.</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-yellow-700">
                      콘텐츠를 생성하고 있습니다. 이 작업은 1-2분 정도 소요될 수 있습니다.
                    </p>
                    <p className="text-sm text-yellow-600">
                      생성 중에는 페이지를 벗어나지 마세요. 완료되면 자동으로 목록이 새로고침됩니다.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">콘텐츠 목록</h2>
        
        {contents.length === 0 && !loading ? (
          <div className="bg-gray-50 p-4 rounded text-center">
            생성된 콘텐츠가 없습니다.
          </div>
        ) : (
          <div className="space-y-4">
            {contents.map((content) => (
              <div key={content.id} className="bg-white p-4 rounded-lg shadow">
                <h3 className="font-semibold text-lg">{content.title}</h3>
                <p className="text-gray-600 mb-2">키워드: {content.keyword?.keyword || '정보 없음'}</p>
                <p className="text-gray-600 mb-2">생성일: {new Date(content.created_at).toLocaleDateString()}</p>
                <div className="flex gap-2 mt-2">
                  <button
                    className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onClick={() => navigate(`/content/${content.id}`)}
                  >
                    상세보기
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg mt-4">
        <p><strong>로드된 키워드 수:</strong> {keywords.length}</p>
        <p><strong>로드된 콘텐츠 수:</strong> {contents.length}</p>
        <p><strong>네트워크 상태:</strong> {networkStatus ? '온라인' : '오프라인'}</p>
      </div>
    </div>
  );
}

export default ContentManagement;
