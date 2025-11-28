import multiprocessing
import time
from typing import List, Dict
from backend.services.crawler_service import CrawlerService
from concurrent.futures import ProcessPoolExecutor, as_completed

def _crawl_worker(url: str, product_name: str = None, save_format: str = "json", 
                 split_mode: str = "aggressive", collect_reviews: bool = False, 
                 review_end_date: str = None, reviews_only: bool = False) -> Dict:
    """
    Worker function to run in a separate process.
    Instantiates a new CrawlerService (and thus a new Chrome instance) for each task.
    """
    # Create a new service instance for this process
    service = CrawlerService()
    try:
        # Start crawler with headless=False to show browser windows
        service.start_crawler_instance(headless=False)
        
        result = service.crawler.crawl_product_by_url(
            url=url,
            product_name=product_name,
            save_format=save_format,
            split_mode=split_mode,
            collect_reviews=collect_reviews,
            review_end_date=review_end_date,
            reviews_only=reviews_only
        )
        return {"url": url, "status": "success", "result": result}
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}
    finally:
        service.stop_crawler_instance()

class ParallelCrawlerService:
    def __init__(self):
        self.executor = None
        self.futures = []
        self.total_tasks = 0
        self.completed_tasks = 0
        self.is_running = False
        self.results = []

    def start_parallel_crawl(self, urls: List[str], max_workers: int = 3, **kwargs) -> List[Dict]:
        """
        Start parallel crawling of multiple URLs.
        """
        self.is_running = True
        self.total_tasks = len(urls)
        self.completed_tasks = 0
        self.results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(_crawl_worker, url, **kwargs): url 
                for url in urls
            }
            
            # Wait for completion
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    self.results.append(data)
                except Exception as e:
                    self.results.append({"url": url, "status": "error", "error": str(e)})
                
                self.completed_tasks += 1
        
        self.is_running = False
        return self.results
    
    def get_status(self) -> Dict:
        """Get current parallel crawl status"""
        progress = self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
        return {
            "is_running": self.is_running,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "progress": progress,
            "results": self.results
        }
