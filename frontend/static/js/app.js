const API_BASE = '/api';

// State
let isPolling = false;
let pollInterval = null;

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
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');

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
    const urls = [
        document.getElementById('parallel-url-1').value,
        document.getElementById('parallel-url-2').value,
        document.getElementById('parallel-url-3').value,
        document.getElementById('parallel-url-4').value,
        document.getElementById('parallel-url-5').value
    ].map(u => u.trim()).filter(u => u); // Remove empty values

    const concurrency = document.getElementById('concurrency-slider').value;

    // Common Settings
    const saveFormat = document.getElementById('common-save-format').value;
    const splitMode = "aggressive"; // Always aggressive
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
                reviews_only: false, // Always false, handled by smart skip
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
    const splitMode = "aggressive"; // Always aggressive
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
                reviews_only: false,
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
    const url = document.getElementById('url-input').value;
    const productName = document.getElementById('product-name-input').value;

    // Common Settings
    const saveFormat = document.getElementById('common-save-format').value;
    const splitMode = "aggressive"; // Always aggressive
    const collectReviews = document.getElementById('common-collect-reviews').checked;
    // reviewsOnly removed
    let reviewEndDate = null;

    if (collectReviews) {
        const dateInput = document.getElementById('common-review-end-date').value;
        if (dateInput) {
            reviewEndDate = dateInput.replace(/-/g, '.');
        }
    }

    if (!url) {
        alert('URL을 입력해주세요');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/crawl/url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                product_name: productName || null,
                save_format: saveFormat,
                split_mode: splitMode,
                collect_reviews: collectReviews,
                reviews_only: false,
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
            <div class="history-card">
                <div class="card-img">
                    ${item.image_path ? `<img src="${API_BASE}/image/${item.folder_name}" alt="${item.product_name}">` : '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)"><i class="fa-solid fa-image"></i></div>'}
                </div>
                <div class="card-content">
                    <h4>${item.product_name}</h4>
                    <div class="meta-info">
                        <span><i class="fa-solid fa-star"></i> ${item.rating}</span>
                        <span><i class="fa-solid fa-comment"></i> ${item.review_count}</span>
                    </div>
                    <div class="card-actions">
                        <button class="btn-sm" onclick="openFolder('${item.folder_name}')">
                            <i class="fa-solid fa-folder-open"></i> 폴더 열기
                        </button>
                    </div>
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
async function loadConfig() {
    try {
        // Load API key and model
        const res = await fetch(`${API_BASE}/config`);
        if (res.ok) {
            const config = await res.json();
            document.getElementById('openai-api-key').value = config.openai_api_key || '';
        }

        // Load default prompts
        const promptsRes = await fetch(`${API_BASE}/prompts`);
        if (promptsRes.ok) {
            const prompts = await promptsRes.json();
            document.getElementById('review-prompt').value = prompts.review_prompt || '';
            document.getElementById('image-prompt').value = prompts.image_prompt || '';
        }
    } catch (e) {
        console.error('Config load failed', e);
    }
}

async function saveConfig() {
    const apiKey = document.getElementById('openai-api-key').value;
    const reviewPrompt = document.getElementById('review-prompt').value;
    const imagePrompt = document.getElementById('image-prompt').value;
    const model = document.getElementById('ai-model-select').value;

    try {
        const res = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                openai_api_key: apiKey,
                review_prompt: reviewPrompt,
                image_prompt: imagePrompt
            })
        });

        if (res.ok) {
            alert('설정이 저장되었습니다.');
        } else {
            alert('설정 저장 실패');
        }
    } catch (e) {
        alert('설정 저장 중 오류 발생: ' + e.message);
    }
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
        // Simple markdown rendering (replace newlines with <br> for now, or use a library if available)
        // For better UX, we'll just wrap in pre-wrap for now
        resultArea.innerHTML = `<div style="white-space: pre-wrap; font-family: sans-serif; line-height: 1.6;">${data.result}</div>`;

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
        resultArea.innerHTML = `<div style="white-space: pre-wrap; font-family: sans-serif; line-height: 1.6;">${data.result}</div>`;

    } catch (e) {
        resultArea.innerHTML = `<div style="color:var(--danger)">오류 발생: ${e.message}</div>`;
    }
}

function loadProductPreview() {
    // Optional: Show selected product thumbnail or info
}

// Initial load
loadHistory();
loadConfig();
loadProductList();

// Set default review end date to 1 week ago
function setDefaultReviewDate() {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const dateStr = oneWeekAgo.toISOString().split('T')[0];
    document.getElementById('common-review-end-date').value = dateStr;
}

setDefaultReviewDate();

// Refresh product list when switching to AI tab
document.querySelector('button[data-tab="ai"]').addEventListener('click', loadProductList);

