const API_BASE = '/api';

// Default Prompts (hardcoded in frontend)
const DEFAULT_REVIEW_PROMPT = `당신은 화장품 마케팅 전문가입니다. 아래 리뷰 데이터를 보고 다음을 분석해주세요:

1. 고객이 가장 선호하는 제품 특징
2. 개선이 필요한 부분
3. 리뷰에서 반복적으로 등장하는 핵심 키워드
4. 마케팅 메시지에 활용 가능한 표현이나 문구
5. 제품 경쟁력 포인트 요약

각 항목을 명확한 제목과 함께 글머리 기호(•)를 사용한 목록 형식으로 정리해주세요. 
표는 사용하지 마세요.
요청한 분석만 제공하고, 추가 제안이나 질문은 하지 마세요.`;

const DEFAULT_IMAGE_PROMPT = `당신은 화장품 연구원입니다. 제품 상세 이미지를 분석하여 다음 4가지 핵심 정보를 추출해주세요.

**1. 원포인트 (One-Point)**
• 제품을 한마디로 정의하는 메인 카피나 슬로건
• 가장 강조하고 있는 핵심 컨셉

**2. 임상 (Clinical)**
• 효능/효과를 객관적으로 입증하는 임상 시험 결과를 **누락없이** 모두 추출
• 구체적인 수치(%, 개선율, 만족도, 배 증가 등)가 있다면 **반드시 포함**
• **시간 정보 필수**: "사용 전", "사용 직후", "즉시", "1회 사용 후", "X일 후", "X주 후", "X개월 사용" 등 측정 시점이 명시된 경우 **반드시 함께 기록**
• 예시: "사용 2주 후 주름 개선 87%", "즉시 보습력 120% 증가", "4주 사용 후 탄력 개선"
• "검증된", "테스트 완료", "임상 실험", "피부과 테스트" 등의 문구 확인
• ⚠️ **제외**: 단순 가격, 용량, 할인율, 세트 구성 등 판매 정보는 제외

**3. 소재 (Material)**
• 제품만의 특별한 성분이나 기술력
• 특허 성분, 독자 개발 원료 등 차별화된 소재 정보

**4. 리뷰 (Review)**
• 상세 페이지 내에 판매자가 선별하여 포함시킨 'Best 리뷰'나 '사용자 후기' 내용
• 실제 사용자의 목소리로 강조된 포인트

**주의사항:**
- 제품명, 가격, 용량, 1+1 구성 등 단순 판매 정보는 제외하세요.
- 수치는 '효능 입증'과 관련된 것만 기록하세요.
- 각 항목은 글머리 기호(•)로 정리해주세요.
- 표는 사용하지 마세요.
- 분석이 불가능한 항목은 "정보 없음"으로 표시하세요.`;

// State
let isPolling = false;
let pollInterval = null;
let currentAnalysisResult = ''; // Store current analysis result
let currentViewMode = 'markdown'; // 'text' or 'markdown'

// Helper Functions
function compressOliveyoungUrl(url) {
    try {
        if (!url) return url;
        
        const urlObj = new URL(url);
        if (!urlObj.hostname.includes('oliveyoung.co.kr')) {
            return url;
        }
        
        // Extract goodsNo parameter
        const goodsNo = urlObj.searchParams.get('goodsNo');
        if (goodsNo) {
            // Create clean URL with only goodsNo
            const baseUrl = 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do';
            return `${baseUrl}?goodsNo=${goodsNo}`;
        }
        
        return url;
    } catch (e) {
        console.error('URL compression failed:', e);
        return url;
    }
}

// DOM Elements
const keywordForm = document.getElementById('keyword-form');
const urlForm = document.getElementById('url-form');
const liveStatus = document.getElementById('live-status');
const progressBar = document.getElementById('progress-bar');
const progressPercent = document.getElementById('progress-percent');
const currentAction = document.getElementById('current-action');
const logWindow = document.getElementById('log-window');
const systemStatusDot = document.getElementById('system-status-dot');
const systemStatusText = document.getElementById('system-status-text');

// Navigation
document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        // Check if we're leaving the AI tab before switching
        const previousTab = document.querySelector('.tab-content.active')?.id;
        
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');

        // Clear AI analysis results when leaving AI tab
        if (previousTab === 'ai-tab' && btn.dataset.tab !== 'ai') {
            clearAnalysisResults();
            hideAnalysisStatus();
        }

        if (btn.dataset.tab === 'history') {
            loadHistory();
        }
    });
});

function switchInputMode(mode) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active'); // Assumes event is available

    const multiUrlForm = document.getElementById('multi-url-form');

    keywordForm.classList.add('hidden');
    urlForm.classList.add('hidden');
    multiUrlForm.classList.add('hidden');

    if (mode === 'keyword') {
        keywordForm.classList.remove('hidden');
    } else if (mode === 'url') {
        urlForm.classList.remove('hidden');
    } else if (mode === 'multi-url') {
        multiUrlForm.classList.remove('hidden');
    }
}

async function startParallelCrawl() {
    // Collect URLs from 5 individual input fields
    const inputUrls = [
        document.getElementById('parallel-url-1').value,
        document.getElementById('parallel-url-2').value,
        document.getElementById('parallel-url-3').value,
        document.getElementById('parallel-url-4').value,
        document.getElementById('parallel-url-5').value
    ].map(u => u.trim()).filter(u => u); // Remove empty values

    // Compress all URLs
    const urls = inputUrls.map(url => compressOliveyoungUrl(url));
    
    // Update input fields with compressed URLs
    const inputFields = [
        'parallel-url-1', 'parallel-url-2', 'parallel-url-3', 
        'parallel-url-4', 'parallel-url-5'
    ];
    
    urls.forEach((compressedUrl, index) => {
        if (compressedUrl && inputUrls[index] && compressedUrl !== inputUrls[index]) {
            document.getElementById(inputFields[index]).value = compressedUrl;
            console.log(`URL ${index + 1} 압축됨: ${inputUrls[index]} → ${compressedUrl}`);
        }
    });

    const concurrency = document.getElementById('concurrency-slider').value;

    // Common Settings
    const saveFormat = document.getElementById('common-save-format').value;
    const splitMode = "conservative"; // Always conservative (최대한 합치기)
    const collectReviews = document.getElementById('common-collect-reviews').checked;
    let reviewEndDate = null;

    if (collectReviews) {
        const dateInput = document.getElementById('common-review-end-date').value;
        if (dateInput) {
            reviewEndDate = dateInput.replace(/-/g, '.');
        }
    }

    if (urls.length === 0) {
        alert('최소 1개의 URL을 입력해주세요');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/crawl/parallel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                urls: urls,
                concurrency: parseInt(concurrency),
                save_format: saveFormat,
                split_mode: splitMode,
                collect_reviews: collectReviews,
                reviews_only: document.getElementById('common-reviews-only').checked,
                review_end_date: reviewEndDate
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }

        const data = await res.json();

        // Start polling for parallel crawl progress
        startParallelPolling();

    } catch (e) {
        alert(`오류: ${e.message}`);
    }
}

function startParallelPolling() {
    liveStatus.classList.remove('hidden');

    const interval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/crawl/parallel/status`);
            const status = await res.json();

            // Update UI
            const pct = Math.round(status.progress * 100);
            progressBar.style.width = `${pct}%`;
            progressPercent.textContent = `${pct}%`;
            currentAction.textContent = `병렬 크롤링 중... (${status.completed_tasks}/${status.total_tasks})`;

            if (!status.is_running && status.completed_tasks > 0) {
                clearInterval(interval);
                alert(`병렬 크롤링 완료!\n완료: ${status.completed_tasks}개`);
                loadHistory();
                resetUI();
            }
        } catch (e) {
            console.error('Parallel polling error', e);
        }
    }, 2000); // Poll every 2 seconds
}

function toggleCommonReviewDate() {
    const checkbox = document.getElementById('common-collect-reviews');
    const container = document.getElementById('common-review-date-container');
    if (checkbox.checked) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
}

// API Calls
async function startKeywordCrawl() {
    const keyword = document.getElementById('keyword-input').value;
    const maxProducts = document.getElementById('max-products').value;

    // Common Settings
    const saveFormat = document.getElementById('common-save-format').value;
    const splitMode = "conservative"; // Always conservative (최대한 합치기)
    const collectReviews = document.getElementById('common-collect-reviews').checked;
    // reviewsOnly removed
    let reviewEndDate = null;

    if (collectReviews) {
        const dateInput = document.getElementById('common-review-end-date').value;
        if (dateInput) {
            reviewEndDate = dateInput.replace(/-/g, '.');
        }
    }

    if (!keyword) {
        alert('검색어를 입력해주세요');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/crawl/keyword`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                keyword,
                max_products: parseInt(maxProducts),
                save_format: saveFormat,
                split_mode: splitMode,
                collect_reviews: collectReviews,
                reviews_only: document.getElementById('common-reviews-only').checked,
                review_end_date: reviewEndDate
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }

        startPolling();
    } catch (e) {
        alert(`오류: ${e.message}`);
    }
}

async function startUrlCrawl() {
    const inputUrl = document.getElementById('url-input').value;
    const productName = document.getElementById('product-name-input').value;

    // Common Settings
    const saveFormat = document.getElementById('common-save-format').value;
    const splitMode = "conservative"; // Always conservative (최대한 합치기)
    const collectReviews = document.getElementById('common-collect-reviews').checked;
    // reviewsOnly removed
    let reviewEndDate = null;

    if (collectReviews) {
        const dateInput = document.getElementById('common-review-end-date').value;
        if (dateInput) {
            reviewEndDate = dateInput.replace(/-/g, '.');
        }
    }

    if (!inputUrl) {
        alert('URL을 입력해주세요');
        return;
    }

    // URL 압축하기
    const compressedUrl = compressOliveyoungUrl(inputUrl);
    
    // 원본 URL과 다르면 사용자에게 알림
    if (compressedUrl !== inputUrl) {
        console.log(`URL 압축됨: ${inputUrl} → ${compressedUrl}`);
        // 입력 필드도 압축된 URL로 업데이트
        document.getElementById('url-input').value = compressedUrl;
    }

    try {
        const res = await fetch(`${API_BASE}/crawl/url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: compressedUrl,
                product_name: productName || null,
                save_format: saveFormat,
                split_mode: splitMode,
                collect_reviews: collectReviews,
                reviews_only: document.getElementById('common-reviews-only').checked,
                review_end_date: reviewEndDate
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }

        startPolling();
    } catch (e) {
        alert(`오류: ${e.message}`);
    }
}

function startPolling() {
    if (isPolling) return;
    isPolling = true;
    liveStatus.classList.remove('hidden');

    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/status`);
            const status = await res.json();

            updateStatusUI(status);

            if (!status.is_running) {
                stopPolling();

                if (status.progress >= 1.0) {
                    alert('크롤링이 완료되었습니다!');
                    loadHistory(); // Refresh history
                    resetUI(); // Initialize screen
                }
            }

        } catch (e) {
            console.error('Polling error', e);
        }
    }, 10000); // Poll every 10 seconds
}

function stopPolling() {
    isPolling = false;
    if (pollInterval) clearInterval(pollInterval);
    systemStatusDot.classList.remove('running');
    systemStatusText.textContent = '대기 중';
}

function updateStatusUI(status) {
    // System Status
    if (status.is_running) {
        systemStatusDot.classList.add('running');
        systemStatusText.textContent = '실행 중';
    } else {
        systemStatusDot.classList.remove('running');
        systemStatusText.textContent = '대기 중';
    }

    // Progress
    const pct = Math.round(status.progress * 100);
    progressBar.style.width = `${pct}%`;
    progressPercent.textContent = `${pct}%`;
    currentAction.textContent = status.current_action;

    // Logs
    logWindow.innerHTML = status.logs.map(log => `<div>${log}</div>`).join('');
    logWindow.scrollTop = logWindow.scrollHeight;
}

function resetUI() {
    // Hide status card and reset values
    liveStatus.classList.add('hidden');
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    currentAction.textContent = '-';
    logWindow.innerHTML = '';

    // Reset system status
    systemStatusDot.classList.remove('running');
    systemStatusText.textContent = '대기 중';
}

async function loadHistory() {
    // Auto-cleanup temp folders on load
    try {
        await fetch(`${API_BASE}/history/cleanup`, { method: 'POST' });
    } catch (e) {
        console.warn('Cleanup failed', e);
    }

    const grid = document.getElementById('history-grid');
    grid.innerHTML = '<div style="color:var(--text-muted)">로딩 중...</div>';

    try {
        const res = await fetch(`${API_BASE}/results`);
        const results = await res.json();

        grid.innerHTML = results.map(item => `
            <div class="history-card" data-folder="${item.folder_name}">
                <input type="checkbox" class="history-checkbox" data-folder="${item.folder_name}" 
                    style="position: absolute; top: 10px; left: 10px; width: 20px; height: 20px; cursor: pointer; z-index: 10;"
                    onchange="updateDeleteButton()">
                <div class="card-img" onclick="viewHistoryDetail('${item.folder_name}')" style="cursor: pointer;">
                    ${item.image_path ? `<img src="${API_BASE}/image/${item.folder_name}" alt="${item.product_name}">` : '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)"><i class="fa-solid fa-image"></i></div>'}
                </div>
                <div class="card-content" onclick="viewHistoryDetail('${item.folder_name}')" style="cursor: pointer;">
                    <h4>${item.product_name}</h4>
                    <div class="meta-info">
                        <span><i class="fa-solid fa-star"></i> ${item.rating}</span>
                        <span><i class="fa-solid fa-comment"></i> ${item.review_count}</span>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn-sm" onclick="event.stopPropagation(); openFolder('${item.folder_name}')">
                        <i class="fa-solid fa-folder-open"></i> 폴더 열기
                    </button>
                </div>
            </div>
        `).join('');

        // Note: Image loading from local path is tricky in browser due to security.
        // We might need an endpoint to serve images or just show placeholder.
        // For now, I'll leave it as is, but in a real app we'd serve images via static route.
        // Actually, we can't serve arbitrary paths outside static folder easily without configuration.
        // I'll skip image preview for now or assume they are copied to static.
        // Wait, the 'image_path' is absolute path. Browser won't load it.
        // I should probably add an endpoint to serve image by folder name.

    } catch (e) {
        grid.innerHTML = `<div style="color:var(--danger)">히스토리 로딩 오류: ${e.message}</div>`;
    }
}

function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.history-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);

    checkboxes.forEach(cb => cb.checked = !allChecked);
    updateDeleteButton();

    const btn = document.getElementById('select-all-btn');
    btn.innerHTML = allChecked ?
        '<i class="fa-solid fa-check-double"></i> 전체 선택' :
        '<i class="fa-solid fa-square"></i> 전체 해제';
}

function updateDeleteButton() {
    const checkboxes = document.querySelectorAll('.history-checkbox:checked');
    const deleteBtn = document.getElementById('delete-selected-btn');

    if (checkboxes.length > 0) {
        deleteBtn.style.display = 'inline-block';
        deleteBtn.innerHTML = `<i class="fa-solid fa-trash"></i> 선택 삭제 (${checkboxes.length})`;
    } else {
        deleteBtn.style.display = 'none';
    }
}

async function deleteSelected() {
    const checkboxes = document.querySelectorAll('.history-checkbox:checked');
    const folderNames = Array.from(checkboxes).map(cb => cb.dataset.folder);

    if (folderNames.length === 0) return;

    if (!confirm(`${folderNames.length}개 항목을 삭제하시겠습니까?`)) return;

    try {
        const res = await fetch(`${API_BASE}/history/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(folderNames)
        });

        const result = await res.json();
        alert(result.message);
        loadHistory();
    } catch (e) {
        alert(`삭제 실패: ${e.message}`);
    }
}

function viewHistoryDetail(folderName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById('history-detail-tab').classList.add('active');
    loadHistoryDetail(folderName);
}

async function loadHistoryDetail(folderName) {
    const container = document.getElementById('detail-container');
    const title = document.getElementById('detail-product-title');
    
    container.innerHTML = '<div style="color:var(--text-muted); text-align: center; padding: 2rem;"><i class="fa-solid fa-spinner fa-spin"></i> 로딩 중...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/history/detail/${folderName}`);
        if (!res.ok) {
            throw new Error('상품 정보를 불러올 수 없습니다');
        }
        
        const data = await res.json();
        const product = data.product_info;
        
        title.textContent = product.상품명 || '상품 상세 정보';
        
        container.innerHTML = `
            <div class="product-detail-layout">
                <div class="back-button-container">
                    <button class="btn-secondary" onclick="goBackToHistory()">
                        <i class="fa-solid fa-arrow-left"></i> 뒤로가기
                    </button>
                </div>
                
                <div class="product-detail-grid">
                    <!-- 상단 첫 번째: 섬네일 -->
                    <div class="product-thumbnail-section">
                        ${data.thumbnail ? 
                            `<img src="${API_BASE}/image/${folderName}" alt="${product.상품명}" class="thumbnail-image">` :
                            '<div class="thumbnail-placeholder"><i class="fa-solid fa-image fa-3x"></i></div>'
                        }
                    </div>
                    
                    <!-- 상단 두 번째: 상품 정보 -->
                    <div class="product-info-section">
                        <h3 class="product-title">${product.상품명 || '상품명 없음'}</h3>
                        <div class="product-prices">
                            ${product.정상가 && product.판매가 && product.정상가 !== product.판매가 ? 
                                `<p class="product-original-price">${product.정상가}원</p>
                                 <p class="product-sale-price">${product.판매가}원</p>` :
                                `<p class="product-price">${product.판매가 || product.정상가 || product.가격 || '가격 정보 없음'}</p>`
                            }
                        </div>
                        
                        <div class="product-meta-grid">
                            <div class="meta-row">
                                <div class="meta-item">
                                    <i class="fa-solid fa-star"></i>
                                    <span>${product.별점 || '0.0'}</span>
                                </div>
                                <div class="meta-item">
                                    <i class="fa-solid fa-comment"></i>
                                    <span>${product.리뷰_총개수 || '0'}개</span>
                                </div>
                            </div>
                            <div class="meta-item">
                                <i class="fa-solid fa-calendar"></i>
                                <span>수집일: ${product.수집시각 || '수집시각 없음'}</span>
                            </div>
                        </div>
                        
                        ${data.product_url ? `
                        <div class="meta-item">
                            <i class="fa-solid fa-link"></i>
                            <span><a href="${data.product_url}" target="_blank" style="color: var(--accent); text-decoration: none;">${data.product_url.length > 50 ? data.product_url.substring(0, 47) + '...' : data.product_url}</a></span>
                        </div>` : ''}
                    </div>
                    
                    <!-- 상단 세 번째: 화장품법 성분 정보 -->
                    <div class="product-ingredients-section">
                        <h4><i class="fa-solid fa-flask"></i> 화장품법 성분 정보</h4>
                        <div class="ingredients-scroll">
                            ${product['화장품법에 따라 기재해야 하는 모든 성분'] ? 
                                `<div class="ingredients-text">${product['화장품법에 따라 기재해야 하는 모든 성분']}</div>` :
                                '<p class="no-ingredients">성분 정보가 없습니다.</p>'
                            }
                            ${product['사용방법'] ? 
                                `<div class="usage-info">
                                    <h5><i class="fa-solid fa-info-circle"></i> 사용방법</h5>
                                    <div class="usage-text">${product['사용방법']}</div>
                                </div>` : ''
                            }
                        </div>
                    </div>
                    
                    <!-- 하단 첫 번째: 상품 이미지들 -->
                    <div class="product-images-section">
                        <h4><i class="fa-solid fa-images"></i> 상품 상세 이미지</h4>
                        ${data.detail_images && data.detail_images.length > 0 ? `
                        <div class="detail-images-scroll">
                            ${data.detail_images.map(img => `
                                <img src="${API_BASE}/file/${folderName}/${img}" 
                                     alt="상품 상세 이미지" 
                                     class="detail-image"
                                     onclick="openImageModal(this.src)">
                            `).join('')}
                        </div>` : '<p class="no-images">상품 이미지가 없습니다.</p>'}
                    </div>
                    
                    <!-- 하단 두 번째: 리뷰 텍스트 -->
                    <div class="product-reviews-section">
                        <h4><i class="fa-solid fa-comment-dots"></i> 리뷰 텍스트</h4>
                        ${data.review_text ? `
                        <div class="review-text-container">
                            ${data.review_text.substring(0, 5000)}${data.review_text.length > 5000 ? '...\n\n[리뷰가 길어 일부만 표시됩니다]' : ''}
                        </div>` : '<p class="no-reviews">리뷰가 없습니다.</p>'}
                    </div>
                </div>
            </div>
        `;
        
    } catch (e) {
        container.innerHTML = `<div style="color:var(--danger); text-align: center; padding: 2rem;">오류: ${e.message}</div>`;
    }
}

function openImageModal(imageSrc) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        cursor: pointer;
    `;
    
    // Create image element
    const img = document.createElement('img');
    img.src = imageSrc;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    `;
    
    modal.appendChild(img);
    document.body.appendChild(modal);
    
    // Close modal on click
    modal.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Close modal on ESC key
    const closeOnEsc = (e) => {
        if (e.key === 'Escape') {
            document.body.removeChild(modal);
            document.removeEventListener('keydown', closeOnEsc);
        }
    };
    document.addEventListener('keydown', closeOnEsc);
}

function goBackToHistory() {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById('history-tab').classList.add('active');
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.querySelector('.nav-item[data-tab="history"]').classList.add('active');
}

async function openFolder(folderName) {
    try {
        await fetch(`${API_BASE}/open-folder/${folderName}`, { method: 'POST' });
    } catch (e) {
        alert('폴더 열기 실패');
    }
}

async function openDataFolder() {
    try {
        await fetch(`${API_BASE}/open-data-dir`, { method: 'POST' });
    } catch (e) {
        alert('데이터 폴더 열기 실패');
    }
}

async function mergeHistory() {
    if (!confirm('중복된 상품 폴더를 병합하시겠습니까?\n(가장 최신 폴더를 기준으로 병합되며, 오래된 폴더는 삭제됩니다.)')) {
        return;
    }

    const grid = document.getElementById('history-grid');
    const originalContent = grid.innerHTML;
    grid.innerHTML = '<div style="color:var(--accent); text-align:center; padding:2rem;"><i class="fa-solid fa-spinner fa-spin"></i> 병합 중입니다...</div>';

    try {
        const res = await fetch(`${API_BASE}/history/merge`, { method: 'POST' });
        if (!res.ok) throw new Error('Merge failed');

        const data = await res.json();
        alert(`병합 완료!\n- 병합된 그룹: ${data.merged_groups}개\n- 삭제된 폴더: ${data.deleted_folders}개`);
        loadHistory(); // Refresh list
    } catch (e) {
        grid.innerHTML = originalContent;
        alert('병합 실패: ' + e.message);
    }
}

// AI Analysis Functions
function initializePrompts() {
    // Set prompts from hardcoded constants
    document.getElementById('review-prompt').value = DEFAULT_REVIEW_PROMPT;
    document.getElementById('image-prompt').value = DEFAULT_IMAGE_PROMPT;
}

async function loadProductList() {
    try {
        const res = await fetch(`${API_BASE}/results`);
        const results = await res.json();

        const select = document.getElementById('product-select');
        select.innerHTML = '<option value="">상품을 선택하세요...</option>';

        results.forEach(item => {
            const option = document.createElement('option');
            option.value = item.folder_name;
            option.textContent = item.product_name;
            select.appendChild(option);
        });
    } catch (e) {
        console.error('Failed to load product list', e);
    }
}

async function analyzeReviews() {
    const productFolder = document.getElementById('product-select').value;
    const prompt = document.getElementById('review-prompt').value;
    const resultArea = document.getElementById('ai-result-area');

    const model = document.getElementById('ai-model-select').value;

    if (!productFolder) {
        alert('분석할 상품을 선택해주세요.');
        return;
    }

    resultArea.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 분석 중입니다...</div>';

    try {
        const res = await fetch(`${API_BASE}/analyze/reviews`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_folder: productFolder,
                prompt: prompt,
                model: model
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }

        const data = await res.json();
        // Store result for view switching
        currentAnalysisResult = data.result;
        // Render based on current view mode
        renderResult();
        
        // Refresh load buttons to show the newly created analysis
        setTimeout(() => {
            const productFolder = document.getElementById('product-select').value;
            if (productFolder) {
                fetch(`${API_BASE}/analyze/${productFolder}/status`)
                    .then(res => res.json())
                    .then(status => {
                        const reviewBtn = document.getElementById('review-load-btn');
                        const imageBtn = document.getElementById('image-load-btn');
                        if (status.review_analysis.exists) reviewBtn.style.display = 'inline-block';
                        if (status.image_analysis.exists) imageBtn.style.display = 'inline-block';
                    });
            }
        }, 1000);

    } catch (e) {
        resultArea.innerHTML = `<div style="color:var(--danger)">오류 발생: ${e.message}</div>`;
    }
}

async function analyzeImages() {
    const productFolder = document.getElementById('product-select').value;
    const prompt = document.getElementById('image-prompt').value;
    const resultArea = document.getElementById('ai-result-area');

    const model = document.getElementById('ai-model-select').value;

    if (!productFolder) {
        alert('분석할 상품을 선택해주세요.');
        return;
    }

    resultArea.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 이미지 분석 중입니다... (시간이 걸릴 수 있습니다)</div>';

    try {
        const res = await fetch(`${API_BASE}/analyze/images`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_folder: productFolder,
                prompt: prompt,
                model: model
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }

        const data = await res.json();
        // Store result for view switching
        currentAnalysisResult = data.result;
        // Render based on current view mode
        renderResult();
        
        // Refresh load buttons to show the newly created analysis
        setTimeout(() => {
            const productFolder = document.getElementById('product-select').value;
            if (productFolder) {
                fetch(`${API_BASE}/analyze/${productFolder}/status`)
                    .then(res => res.json())
                    .then(status => {
                        const reviewBtn = document.getElementById('review-load-btn');
                        const imageBtn = document.getElementById('image-load-btn');
                        if (status.review_analysis.exists) reviewBtn.style.display = 'inline-block';
                        if (status.image_analysis.exists) imageBtn.style.display = 'inline-block';
                    });
            }
        }, 1000);

    } catch (e) {
        resultArea.innerHTML = `<div style="color:var(--danger)">오류 발생: ${e.message}</div>`;
    }
}

async function loadProductPreview() {
    const productFolder = document.getElementById('product-select').value;
    
    if (!productFolder) {
        // Hide analysis status indicators when no product selected
        hideAnalysisStatus();
        clearAnalysisResults();
        return;
    }
    
    // Check if existing analysis files exist and auto-load if available
    try {
        const res = await fetch(`${API_BASE}/analyze/${productFolder}/status`);
        if (res.ok) {
            const status = await res.json();
            showLoadButtonsIfExists(status);
        } else {
            hideAnalysisStatus();
            clearAnalysisResults();
        }
    } catch (e) {
        console.error('Failed to check analysis status:', e);
        hideAnalysisStatus();
        clearAnalysisResults();
    }
}

function showLoadButtonsIfExists(status) {
    const reviewBtn = document.getElementById('review-load-btn');
    const imageBtn = document.getElementById('image-load-btn');
    
    // Show buttons for existing analyses
    if (status.review_analysis.exists) {
        reviewBtn.style.display = 'inline-block';
    } else {
        reviewBtn.style.display = 'none';
    }
    
    if (status.image_analysis.exists) {
        imageBtn.style.display = 'inline-block';
    } else {
        imageBtn.style.display = 'none';
    }
    
    // Only clear results if there's no current analysis displayed
    if (!currentAnalysisResult) {
        clearAnalysisResults();
    }
}

function clearAnalysisResults() {
    currentAnalysisResult = '';
    const resultArea = document.getElementById('ai-result-area');
    resultArea.innerHTML = '<div class="placeholder-text">분석 결과가 여기에 표시됩니다.</div>';
}

function updateAnalysisStatus(status, loadedType = null) {
    // This function is no longer needed for auto-loading
    // but kept for compatibility if called elsewhere
}

function hideAnalysisStatus() {
    const reviewBtn = document.getElementById('review-load-btn');
    const imageBtn = document.getElementById('image-load-btn');
    if (reviewBtn) reviewBtn.style.display = 'none';
    if (imageBtn) imageBtn.style.display = 'none';
}

async function loadExistingAnalysisQuiet(analysisType) {
    const productFolder = document.getElementById('product-select').value;
    
    if (!productFolder) {
        throw new Error('No product selected');
    }
    
    const res = await fetch(`${API_BASE}/analyze/${productFolder}/load/${analysisType}`);
    
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail);
    }
    
    const data = await res.json();
    
    // Store result for view switching
    currentAnalysisResult = data.content;
    // Render based on current view mode
    renderResult();
    
    return data;
}

async function loadExistingAnalysis(analysisType) {
    const resultArea = document.getElementById('ai-result-area');
    
    try {
        resultArea.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 기존 분석 결과를 불러오는 중...</div>';
        
        await loadExistingAnalysisQuiet(analysisType);
        
        // Show success notification
        const typeText = analysisType === 'review' ? '리뷰' : '이미지';
        showNotification(`기존 ${typeText} 분석 결과를 불러왔습니다.`, 'success');
        
    } catch (e) {
        resultArea.innerHTML = `<div style="color:var(--danger)">기존 분석 결과 로드 실패: ${e.message}</div>`;
        showNotification(`분석 결과 로드 실패: ${e.message}`, 'error');
    }
}

// View toggle functions
function switchToTextView() {
    currentViewMode = 'text';
    updateToggleButtons();
    renderResult();
}

function switchToMarkdownView() {
    currentViewMode = 'markdown';
    updateToggleButtons();
    renderResult();
}

function updateToggleButtons() {
    const textBtn = document.getElementById('text-view-btn');
    const markdownBtn = document.getElementById('markdown-view-btn');
    
    if (currentViewMode === 'text') {
        textBtn.classList.add('active');
        markdownBtn.classList.remove('active');
    } else {
        textBtn.classList.remove('active');
        markdownBtn.classList.add('active');
    }
}

function renderResult() {
    const resultArea = document.getElementById('ai-result-area');
    
    if (!currentAnalysisResult) {
        resultArea.innerHTML = '<div class="placeholder-text">분석 결과가 여기에 표시됩니다.</div>';
        return;
    }
    
    if (currentViewMode === 'text') {
        // Text view with preserved line breaks
        resultArea.innerHTML = `<div class="text-result">${currentAnalysisResult}</div>`;
    } else {
        // Markdown view with improved bullet point formatting
        let processedContent = currentAnalysisResult;
        
        // Improve bullet point formatting: Add line breaks before bullet points that are on the same line
        // This handles cases like: "• item1 • item2 • item3" -> "• item1\n• item2\n• item3"
        processedContent = processedContent.replace(/(\S)\s*•\s*/g, '$1\n• ');
        
        // Also handle cases where bullets start a line but are concatenated
        processedContent = processedContent.replace(/^•\s*/gm, '• ');
        
        const htmlContent = marked.parse(processedContent);
        resultArea.innerHTML = `<div class="markdown-result">${htmlContent}</div>`;
    }
}

// Initial load
loadHistory();
initializePrompts();
loadProductList();

// Set default review end date to 1 week ago
function setDefaultReviewDate() {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const dateStr = oneWeekAgo.toISOString().split('T')[0];
    document.getElementById('common-review-end-date').value = dateStr;
}

setDefaultReviewDate();

// API Key Management
let apiKeysCache = {};

async function loadApiKeysStatus() {
    try {
        const res = await fetch(`${API_BASE}/config/keys/status`);
        if (!res.ok) throw new Error('Failed to load API keys status');
        
        apiKeysCache = await res.json();
        updateApiKeyStatusUI();
        updateApiKeyInput(); // Load current model's API key
    } catch (e) {
        console.error('Failed to load API keys status:', e);
    }
}

function updateApiKeyStatusUI() {
    const geminiStatus = document.getElementById('gemini-status');
    const openaiStatus = document.getElementById('openai-status');
    
    // Update Gemini status
    if (apiKeysCache.google && apiKeysCache.google.exists) {
        geminiStatus.textContent = 'GEMINI OK';
        geminiStatus.style.background = '#28a745'; // Green
    } else {
        geminiStatus.textContent = 'GEMINI';
        geminiStatus.style.background = '#6c757d'; // Gray
    }
    
    // Update OpenAI status
    if (apiKeysCache.openai && apiKeysCache.openai.exists) {
        openaiStatus.textContent = 'OPENAI OK';
        openaiStatus.style.background = '#28a745'; // Green
    } else {
        openaiStatus.textContent = 'OPENAI';
        openaiStatus.style.background = '#6c757d'; // Gray
    }
}

function updateApiKeyInput() {
    const model = document.getElementById('ai-model-select').value;
    const apiKeyInput = document.getElementById('api-key-input');
    
    if (model.startsWith('gemini')) {
        // Show masked Gemini key
        if (apiKeysCache.google && apiKeysCache.google.masked) {
            apiKeyInput.value = apiKeysCache.google.masked;
            apiKeyInput.placeholder = "Google API Key";
        } else {
            apiKeyInput.value = '';
            apiKeyInput.placeholder = "Google API Key 입력";
        }
    } else {
        // Show masked OpenAI key
        if (apiKeysCache.openai && apiKeysCache.openai.masked) {
            apiKeyInput.value = apiKeysCache.openai.masked;
            apiKeyInput.placeholder = "OpenAI API Key";
        } else {
            apiKeyInput.value = '';
            apiKeyInput.placeholder = "OpenAI API Key 입력";
        }
    }
}

async function saveApiKey() {
    const model = document.getElementById('ai-model-select').value;
    const apiKey = document.getElementById('api-key-input').value.trim();
    
    if (!apiKey) {
        showNotification('API Key를 입력해주세요.', 'error');
        return;
    }
    
    // Skip if the value is a masked key
    if (apiKey.includes('*')) {
        showNotification('새 API Key를 입력해주세요. (마스킹된 키는 저장할 수 없습니다)', 'error');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/config/key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: model,
                key: apiKey
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }
        
        const data = await res.json();
        showNotification(`API Key가 성공적으로 저장되었습니다! (${model.startsWith('gemini') ? 'GOOGLE_API_KEY' : 'OPENAI_API_KEY'})`, 'success');
        
        // Clear input field to prevent accidental re-saves
        document.getElementById('api-key-input').value = '';
        
        // Reload status after saving with a slight delay to ensure server processes the change
        setTimeout(async () => {
            await loadApiKeysStatus();
            // Show updated masked key
            updateApiKeyInput();
        }, 500);
        
    } catch (e) {
        showNotification(`API Key 저장 실패: ${e.message}`, 'error');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    `;
    
    // Set color based on type
    switch(type) {
        case 'success':
            notification.style.background = '#28a745';
            break;
        case 'error':
            notification.style.background = '#dc3545';
            break;
        case 'warning':
            notification.style.background = '#ffc107';
            notification.style.color = '#212529';
            break;
        default:
            notification.style.background = '#17a2b8';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Remove after 4 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// Refresh product list when switching to AI tab and load API keys
document.querySelector('button[data-tab="ai"]').addEventListener('click', () => {
    loadProductList();
    // Force reload API keys status to get latest from .env
    setTimeout(loadApiKeysStatus, 100); // Small delay to ensure UI is ready
});

// Load API keys on page load
document.addEventListener('DOMContentLoaded', loadApiKeysStatus);

