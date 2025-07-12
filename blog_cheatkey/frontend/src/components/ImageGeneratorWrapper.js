// src/components/ImageGeneratorWrapper.js
import React, { useState, useEffect, useCallback } from 'react';
import { imageGeneratorService } from '../api/imageGeneratorService';

// 디바운스 함수 정의
const debounce = (func, wait) => {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
};

const ImageGeneratorWrapper = ({ contentId, content }) => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [subtopics, setSubtopics] = useState([]);
  const [selectedSubtopic, setSelectedSubtopic] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [generationType, setGenerationType] = useState('all');
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [timeoutMessage, setTimeoutMessage] = useState(null);
  const [imageLoadStatus, setImageLoadStatus] = useState({});

  // 콘텐츠에서 소제목 추출
  useEffect(() => {
    if (content) {
      const subtopicPattern = /###\s+(.*?)\n/g;
      const matches = [...content.matchAll(subtopicPattern)];
      const extractedSubtopics = matches.map(match => match[1].trim());
      setSubtopics(extractedSubtopics);
      // 소제목이 추출되면 첫 번째 소제목을 기본으로 선택 (선택적)
      if (extractedSubtopics.length > 0) {
        setSelectedSubtopic(0);
      }
    }
  }, [content]);

  // 생성된 이미지 목록 조회 - 메모이제이션
  const loadGeneratedImages = useCallback(async () => {
    // 이미 로딩 중이면 실행하지 않음
    // loading 상태를 의존성 배열에 추가하여, loading 상태 변경 시 이 함수가 재생성되지 않도록 합니다.
    // 하지만, 이 함수는 loading 상태를 변경시키므로, 무한 루프를 피하기 위해 loading을 의존성에서 제외하거나,
    // 이 함수를 호출하는 로직에서 loading 상태를 확인하도록 합니다.
    // 여기서는 호출하는 쪽에서 loading을 확인하므로 의존성 배열에서 loading을 제외합니다.
    try {
      setLoading(true); // 로딩 시작
      setError(null); // 이전 에러 초기화
      const response = await imageGeneratorService.getGeneratedImages(contentId);
      
      if (response && response.data) {
        const imageData = Array.isArray(response.data) ? response.data : [];
        const uniqueImageData = imageData.filter((item, index, self) => 
          self.findIndex(t => (t.image === item.image) || (t.url === item.url)) === index
        );
        console.log('로드된 이미지 데이터:', uniqueImageData);
        setImages(uniqueImageData);
      } else {
        setImages([]);
      }
    } catch (error) {
      console.error('이미지 로드 실패:', error);
      setError('이미지를 불러오는 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'));
      setImages([]);
    } finally {
      setLoading(false); // 로딩 종료
      setIsFirstLoad(false);
    }
  }, [contentId]); // contentId가 변경될 때만 이 함수가 재생성되도록 합니다.

  // 디바운스된 이미지 로드 함수
  // loadGeneratedImages 함수가 useCallback으로 메모이즈되었으므로,
  // debouncedLoadImages의 의존성 배열에 loadGeneratedImages를 추가합니다.
  const debouncedLoadImages = useCallback(
    debounce(() => {
      loadGeneratedImages();
    }, 500),
    [loadGeneratedImages] 
  );

  // 초기 이미지 로드
  useEffect(() => {
    if (contentId && isFirstLoad) {
      loadGeneratedImages();
    }
  }, [contentId, loadGeneratedImages, isFirstLoad]);

  // 모든 소제목에 대한 이미지 생성
  const handleGenerateAllImages = useCallback(async () => {
    // loading 상태를 직접 확인하여 중복 실행 방지
    if (loading) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    setTimeoutMessage(null);
    setGenerationType('all');

    const timeoutAlert = setTimeout(() => {
      setTimeoutMessage('이미지 생성이 오래 걸리고 있습니다. 계속 기다려주세요...');
    }, 60000);

    try {
      const response = await imageGeneratorService.generateImagesForContent(contentId);
      
      clearTimeout(timeoutAlert);
      console.log('이미지 생성 응답:', response.data);
      
      if (response && response.data) {
        await loadGeneratedImages();
        setSuccess('모든 소제목에 대한 이미지가 성공적으로 생성되었습니다.');
      } else {
        setError('이미지 생성 결과가 올바른 형식이 아닙니다.');
      }
    } catch (error) {
      clearTimeout(timeoutAlert);
      if (error.message && error.message.includes('timeout')) {
        setError('이미지 생성 시간이 초과되었습니다. 서버에서는 계속 처리 중일 수 있으니 잠시 후 "이미지 새로고침" 버튼을 눌러보세요.');
      } else {
        setError('이미지 생성 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'));
      }
      console.error('이미지 생성 실패:', error);
    } finally {
      setLoading(false);
    }
  }, [contentId, loadGeneratedImages, loading]); // loading을 의존성 배열에 추가

  // 특정 소제목에 대한 이미지 생성
  const handleGenerateSingleImage = useCallback(async () => {
    if (loading) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    setTimeoutMessage(null);
    setGenerationType('single');

    const timeoutAlert = setTimeout(() => {
      setTimeoutMessage('이미지 생성이 오래 걸리고 있습니다. 계속 기다려주세요...');
    }, 60000);

    try {
      const response = await imageGeneratorService.generateImagesForContent(contentId, selectedSubtopic);
      
      clearTimeout(timeoutAlert);
      console.log('단일 이미지 생성 응답:', response.data);
      
      if (response && response.data) {
        await loadGeneratedImages();
        setSuccess('선택한 소제목에 대한 이미지가 성공적으로 생성되었습니다.');
      }
    } catch (error) {
      clearTimeout(timeoutAlert);
      if (error.message && error.message.includes('timeout')) {
        setError('이미지 생성 시간이 초과되었습니다. 서버에서는 계속 처리 중일 수 있으니 잠시 후 "이미지 새로고침" 버튼을 눌러보세요.');
      } else {
        setError('이미지 생성 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'));
      }
      console.error('이미지 생성 실패:', error);
    } finally {
      setLoading(false);
    }
  }, [contentId, selectedSubtopic, loadGeneratedImages, loading]); // loading 추가

  // 인포그래픽 생성
  const handleGenerateInfographic = useCallback(async () => {
    if (loading) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    setTimeoutMessage(null);
    setGenerationType('infographic');

    const timeoutAlert = setTimeout(() => {
      setTimeoutMessage('인포그래픽 생성이 오래 걸리고 있습니다. 계속 기다려주세요...');
    }, 60000);

    try {
      const response = await imageGeneratorService.generateInfographic(contentId, selectedSubtopic);
      
      clearTimeout(timeoutAlert);
      console.log('인포그래픽 생성 응답:', response.data);
      
      if (response && response.data) {
        await loadGeneratedImages();
        setSuccess('인포그래픽이 성공적으로 생성되었습니다.');
      }
    } catch (error) {
      clearTimeout(timeoutAlert);
      if (error.message && error.message.includes('timeout')) {
        setError('인포그래픽 생성 시간이 초과되었습니다. 서버에서는 계속 처리 중일 수 있으니 잠시 후 "이미지 새로고침" 버튼을 눌러보세요.');
      } else {
        setError('인포그래픽 생성 중 오류가 발생했습니다: ' + (error.message || '알 수 없는 오류'));
      }
      console.error('인포그래픽 생성 실패:', error);
    } finally {
      setLoading(false);
    }
  }, [contentId, selectedSubtopic, loadGeneratedImages, loading]); // loading 추가

  // 테스트 목적으로 이미지 데이터 확인
  const checkImageData = useCallback(() => {
    console.log('현재 이미지 데이터:', images);
    if (Array.isArray(images) && images.length > 0) {
      setSuccess(`현재 ${images.length}개의 이미지가 있습니다. 콘솔에서 데이터를 확인하세요.`);
    } else {
      setError('이미지 데이터가 없거나 배열이 아닙니다.');
    }
  }, [images]); // images가 변경될 때만 이 함수가 재생성되도록 합니다.

  // 이미지 로드 성공 핸들러
  const handleImageLoad = useCallback((imageId) => {
    setImageLoadStatus(prev => ({
      ...prev,
      [imageId]: 'loaded'
    }));
    console.log(`이미지 로드 성공: ${imageId}`);
  }, []); // 이 함수는 외부 값에 의존하지 않으므로 빈 배열

  // 이미지 다운로드 함수
  const handleDownloadImage = useCallback((imageUrl, fileName) => {
    const fullUrl = imageUrl.startsWith('/') 
      ? `${window.location.origin}${imageUrl}` 
      : imageUrl;
    
    fetch(fullUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP 오류: ${response.status}`);
        }
        return response.blob();
      })
      .then(blob => {
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = fileName || '이미지.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
      })
      .catch(err => {
        console.error('이미지 다운로드 실패:', err);
        alert('이미지 다운로드에 실패했습니다. 다시 시도해 주세요.');
      });
  }, []); // 이 함수는 외부 값에 의존하지 않으므로 빈 배열

  return (
    <div className="bg-white rounded-lg shadow p-6 mt-6">
      <h3 className="text-lg font-medium mb-3">이미지 생성</h3>
      
      {subtopics.length > 0 && (
        <div className="mb-4">
          <label htmlFor="subtopic-select" className="block text-sm font-medium text-gray-700 mb-2">
            소제목 선택
          </label>
          <select
            id="subtopic-select"
            value={selectedSubtopic}
            onChange={(e) => setSelectedSubtopic(parseInt(e.target.value))}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            disabled={loading}
          >
            {subtopics.map((subtopic, index) => (
              <option key={index} value={index}>
                {subtopic}
              </option>
            ))}
          </select>
        </div>
      )}
      
      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={handleGenerateAllImages}
          disabled={loading}
          className={`px-4 py-2 rounded ${
            loading && generationType === 'all'
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {loading && generationType === 'all' ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              처리 중...
            </span>
          ) : (
            '모든 소제목 이미지 생성'
          )}
        </button>
        
        <button
          onClick={handleGenerateSingleImage}
          disabled={loading || subtopics.length === 0}
          className={`px-4 py-2 rounded ${
            loading && generationType === 'single'
              ? 'bg-gray-400 cursor-not-allowed'
              : subtopics.length === 0
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-green-500 hover:bg-green-600 text-white'
          }`}
        >
          {loading && generationType === 'single' ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              처리 중...
            </span>
          ) : (
            '선택한 소제목 이미지 생성'
          )}
        </button>
        
        <button
          onClick={handleGenerateInfographic}
          disabled={loading || subtopics.length === 0}
          className={`px-4 py-2 rounded ${
            loading && generationType === 'infographic'
              ? 'bg-gray-400 cursor-not-allowed'
              : subtopics.length === 0
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-purple-500 hover:bg-purple-600 text-white'
          }`}
        >
          {loading && generationType === 'infographic' ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              처리 중...
            </span>
          ) : (
            '인포그래픽 생성'
          )}
        </button>
        
        <button
          onClick={checkImageData}
          className="px-4 py-2 rounded bg-gray-500 hover:bg-gray-600 text-white"
        >
          이미지 데이터 확인
        </button>
        
        <button
          onClick={debouncedLoadImages}
          disabled={loading}
          className={`px-4 py-2 rounded ${
            loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-yellow-500 hover:bg-yellow-600 text-white'
          }`}
        >
          이미지 새로고침
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
          {error}
        </div>
      )}
      
      {timeoutMessage && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
          {timeoutMessage}
          <div className="mt-2">
            <span className="inline-block bg-yellow-500 text-white text-xs px-2 py-1 rounded animate-pulse">
              이미지 생성에는 1-3분이 소요될 수 있습니다
            </span>
          </div>
        </div>
      )}
      
      {success && (
        <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4">
          {success}
          {Array.isArray(images) && images.length > 0 && (
            <p className="mt-2">이미지 {images.length}개가 있습니다. 아래에서 확인하세요.</p>
          )}
        </div>
      )}
      
      {loading && (
        <div className="flex justify-center my-4">
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4 py-1">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {Array.isArray(images) && images.length > 0 ? (
        <div className="mt-6">
          <h4 className="text-md font-medium mb-3">생성된 이미지 ({images.length}개)</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {images.map((image, index) => (
              <div key={`${image.id || index}-${image.image || image.url}`} className="border rounded-lg overflow-hidden">
                <img 
                  src={image.url || image.image} 
                  alt={image.alt_text || image.subtopic || '생성된 이미지'}
                  className="w-full h-auto object-cover"
                  loading="lazy"
                  onLoad={() => handleImageLoad(image.id || index)} // image.id가 없을 경우 index 사용
                  onError={(e) => {
                    if (e.target.src.includes('data:image')) return;
                    console.error('이미지 로드 오류:', image.url || image.image);
                    e.target.src = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22400%22%20height%3D%22300%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%22400%22%20height%3D%22300%22%20fill%3D%22%23eee%22%2F%3E%3Ctext%20x%3D%22200%22%20y%3D%22150%22%20font-family%3D%22Arial%22%20font-size%3D%2216%22%20text-anchor%3D%22middle%22%20alignment-baseline%3D%22middle%22%20fill%3D%22%23999%22%3E%EC%9D%B4%EB%AF%B8%EC%A7%80%20%EB%A1%9C%EB%93%9C%20%EC%8B%A4%ED%8C%A8%3C%2Ftext%3E%3C%2Fsvg%3E';
                    e.target.style.backgroundColor = '#f0f0f0';
                    e.target.style.border = '1px solid #ddd';
                    setImageLoadStatus(prev => ({
                      ...prev,
                      [image.id || index]: 'error' // image.id가 없을 경우 index 사용
                    }));
                  }}
                />
                <div className="p-3 bg-gray-50">
                  <div className="flex justify-between items-center">
                    <p className="font-medium text-sm">{image.subtopic || '소제목 정보 없음'}</p>
                    <button
                      onClick={() => handleDownloadImage(image.url || image.image, `${image.subtopic || '이미지'}.png`)}
                      className="text-xs bg-blue-500 hover:bg-blue-600 text-white py-1 px-2 rounded"
                    >
                      다운로드
                    </button>
                  </div>
                  
                  {image.image && (
                    <p className="text-xs text-gray-500 mt-1 truncate">이미지 경로: {image.image}</p>
                  )}
                  
                  {image.is_infographic && (
                    <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded mt-1">
                      인포그래픽
                    </span>
                  )}
                  
                  {imageLoadStatus[image.id || index] === 'error' && ( // image.id가 없을 경우 index 사용
                    <p className="text-xs text-red-500 mt-1">이미지 로드 실패</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : !loading && (
        <div className="text-center py-10 text-gray-500">
          <p>생성된 이미지가 없습니다. 위 버튼을 눌러 이미지를 생성해보세요.</p>
          <p className="text-xs mt-2">이미지 생성에는 시간이 다소 소요될 수 있습니다.</p>
        </div>
      )}
    </div>
  );
};

export default ImageGeneratorWrapper;
