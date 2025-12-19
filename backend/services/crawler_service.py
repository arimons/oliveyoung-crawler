import sys
import os
import threading
import queue
from typing import Optional, Dict, List, Any
import time

# Add src to path to import existing crawler modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from oliveyoung_crawler import OliveyoungIntegratedCrawler
from backend.services.history_service import HistoryService

class CrawlerService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CrawlerService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.crawler: Optional[OliveyoungIntegratedCrawler] = None
        self.is_running = False
        self.current_action = "Idle"
        self.progress = 0.0
        self.logs = []
        self.last_result = None
        self._initialized = True
        self.pending_confirms = {} # {id: bool}
        self.confirm_events = {} # {id: threading.Event}

    def wait_for_user_confirmation(self, confirm_id: str, timeout: int = 60) -> bool:
        """프론트엔드로부터 특정 확인 응답이 올 때까지 대기"""
        event = threading.Event()
        self.confirm_events[confirm_id] = event
        
        # event.wait() returns True if the flag is set, False on timeout
        success = event.wait(timeout=timeout)
        
        response = self.pending_confirms.pop(confirm_id, False) if success else False
        self.confirm_events.pop(confirm_id, None)
        return response

    def set_user_confirmation(self, confirm_id: str, response: bool):
        """프론트엔드에서 보내온 확인 응답을 설정"""
        self.pending_confirms[confirm_id] = response
        if confirm_id in self.confirm_events:
            self.confirm_events[confirm_id].set()

    def start_crawler_instance(self, headless: bool = False):
        """Initialize the Selenium crawler if not already running."""
        # 기존 크롤러가 있지만 세션이 죽었는지 확인
        if self.crawler is not None:
            if not self.crawler.base_crawler.is_alive():
                self.log("⚠️ Previous session is invalid (browser closed?). Restarting...")
                self.stop_crawler_instance()

        if self.crawler is None:
            self.log("Initializing crawler...")
            try:
                self.crawler = OliveyoungIntegratedCrawler(
                    headless=headless, 
                    log_callback=self.log,
                    confirmation_callback=self.wait_for_user_confirmation,
                    merge_callback=HistoryService().merge_specific_product
                )
                self.crawler.start()
                self.log("Crawler initialized successfully.")
            except Exception as e:
                self.log(f"Error initializing crawler: {str(e)}")
                raise e

    def stop_crawler_instance(self):
        """Stop the Selenium crawler."""
        if self.crawler:
            self.log("Stopping crawler...")
            try:
                self.crawler.stop()
            except Exception as e:
                self.log(f"Error stopping crawler: {str(e)}")
            finally:
                self.crawler = None
                self.is_running = False # Force reset state
                self.log("Crawler stopped.")

    def log(self, message: str):
        """Add a log message."""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        print(full_message)
        self.logs.append(full_message)
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs.pop(0)

    def set_status(self, action: str, progress: float):
        self.current_action = action
        self.progress = progress

    def crawl_keyword(self, keyword: str, max_products: int = 10, save_format: str = "both", split_mode: str = "conservative", collect_reviews: bool = False, review_end_date: str = None, reviews_only: bool = False, max_reviews: int = 300):
        if self.is_running:
            raise Exception("Crawler is already running")

        self.is_running = True
        self.logs = [] # Clear logs for new run
        self.last_result = None
        
        thread = threading.Thread(target=self._crawl_keyword_task, args=(keyword, max_products, save_format, split_mode, collect_reviews, review_end_date, reviews_only, max_reviews), daemon=True)
        thread.start()

    def _crawl_keyword_task(self, keyword: str, max_products: int, save_format: str, split_mode: str, collect_reviews: bool, review_end_date: str, reviews_only: bool, max_reviews: int):
        try:
            self.start_crawler_instance(headless=False) # Always show browser for now as per user preference usually
            
            self.set_status(f"Searching for '{keyword}'...", 0.1)
            self.log(f"Starting crawl for keyword: {keyword}")
            
            result = self.crawler.crawl_product_by_keyword(
                keyword, 
                save_format,
                split_mode=split_mode,
                collect_reviews=collect_reviews,
                review_end_date=review_end_date,
                reviews_only=reviews_only,
                max_reviews=max_reviews
            )
            
            self.last_result = result
            self.set_status("Completed", 1.0)
            self.log("Crawl completed successfully.")

        except Exception as e:
            self.log(f"Error during crawl: {str(e)}")
            self.set_status("Error", 0.0)
            self.stop_crawler_instance() # Force cleanup on error
        finally:
            self.stop_crawler_instance() # Auto-close browser after task
            self.is_running = False

    def crawl_url(self, url: str, product_name: Optional[str] = None, save_format: str = "both", split_mode: str = "conservative", collect_reviews: bool = False, review_end_date: str = None, reviews_only: bool = False, max_reviews: int = 300):
        if self.is_running:
            raise Exception("Crawler is already running")

        self.is_running = True
        self.logs = []
        self.last_result = None

        thread = threading.Thread(target=self._crawl_url_task, args=(url, product_name, save_format, split_mode, collect_reviews, review_end_date, reviews_only, max_reviews), daemon=True)
        thread.start()

    def _crawl_url_task(self, url: str, product_name: Optional[str], save_format: str, split_mode: str, collect_reviews: bool, review_end_date: str, reviews_only: bool, max_reviews: int):
        try:
            self.start_crawler_instance(headless=False)
            
            self.set_status("Navigating to URL...", 0.1)
            self.log(f"Starting crawl for URL: {url}")

            result = self.crawler.crawl_product_by_url(
                url, 
                product_name, 
                save_format,
                split_mode=split_mode,
                collect_reviews=collect_reviews,
                review_end_date=review_end_date,
                reviews_only=reviews_only,
                max_reviews=max_reviews
            )
            
            self.last_result = result
            self.set_status("Completed", 1.0)
            self.log("Crawl completed successfully.")

        except Exception as e:
            self.log(f"Error during crawl: {str(e)}")
            self.set_status("Error", 0.0)
            # stop_crawler_instance is now in finally
        finally:
            self.stop_crawler_instance() # Auto-close browser after task
            self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "current_action": self.current_action,
            "progress": self.progress,
            "logs": self.logs,
            "last_result": self.last_result
        }

crawler_service = CrawlerService()
