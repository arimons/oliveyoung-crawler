# v4.0 Update (2025-11-27)

## 🚀 Major Improvements

### 1. Robust Review Collection (Shadow DOM & Virtual Scrolling)
- **Shadow DOM Support:** Implemented recursive JavaScript traversal (`findElementRecursive`) to reliably locate elements (sort buttons, review items) hidden deep within Shadow DOM structures.
- **Real-time Collection:** Refactored the review crawling logic to collect reviews *iteratively* during the scrolling process. This solves the issue where virtual scrolling unloads early reviews from the DOM, causing them to be missed if collected only at the end.
- **Initial Review Capture:** Optimized the loop to capture reviews *before* the first scroll to ensure the most recent reviews (visible immediately after sorting) are not skipped.
- **Precise Date Filtering:** Implemented immediate date checking during extraction. The crawler now stops *exactly* when the `end_date` is reached.

### 2. Data Integrity & Stability
- **Duplicate Prevention:** Added a `Set` based duplicate check to ensure unique reviews are saved.
- **Enhanced Waits:** Increased wait times for critical actions (sorting, scrolling) to account for network latency and DOM rendering.
- **Error Handling:** Added `None` checks for product names to prevent crashes during folder creation.

### 3. Project Structure
- **Backend/Frontend Separation:** Introduced a `backend/` directory for FastAPI services and a `frontend/` directory for static assets and templates.
- **Entry Points:**
    - `run_server.py`: New entry point for the Web UI version.
    - `main.py`: Retained for CLI usage.

## 🛠️ Technical Details
- **File:** `src/review_crawler.py`
    - Added `crawl_reviews_infinite_scroll` with recursive JS and iterative collection.
    - Added `save_review` for immediate file writing.
    - Updated `__init__` for logging callbacks.
- **File:** `src/oliveyoung_crawler.py`
    - Improved folder management and error handling.

## 🗑️ Removed
- Legacy documentation (`USAGE_GUIDE.md`, `USAGE_SIMPLE.md`)
- Deprecated scripts (`app_v3.py`, `translate.py`)
