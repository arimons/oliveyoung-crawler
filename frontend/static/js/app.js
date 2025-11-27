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
    
    if (mode === 'keyword') {
        keywordForm.classList.remove('hidden');
        urlForm.classList.add('hidden');
    } else {
        keywordForm.classList.add('hidden');
        urlForm.classList.remove('hidden');
    }
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
    const splitMode = document.getElementById('common-split-mode').value;
    const collectReviews = document.getElementById('common-collect-reviews').checked;
    const reviewsOnly = document.getElementById('common-reviews-only').checked;
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
                reviews_only: reviewsOnly,
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
    const splitMode = document.getElementById('common-split-mode').value;
    const collectReviews = document.getElementById('common-collect-reviews').checked;
    const reviewsOnly = document.getElementById('common-reviews-only').checked;
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
                reviews_only: reviewsOnly,
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

async function stopCrawl() {
    try {
        await fetch(`${API_BASE}/stop`, { method: 'POST' });
    } catch (e) {
        console.error(e);
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

// Initialize review end date to 1 week ago
function initializeReviewDate() {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    // Format: YYYY-MM-DD
    const year = oneWeekAgo.getFullYear();
    const month = String(oneWeekAgo.getMonth() + 1).padStart(2, '0');
    const day = String(oneWeekAgo.getDate()).padStart(2, '0');
    const dateString = `${year}-${month}-${day}`;

    document.getElementById('common-review-end-date').value = dateString;
}

// Initial load
initializeReviewDate();
loadHistory();
