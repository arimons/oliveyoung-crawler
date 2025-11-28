from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CrawlKeywordRequest(BaseModel):
    keyword: str
    max_products: int = 10
    save_format: str = "both" # json, csv, both
    split_mode: str = "aggressive" # conservative, aggressive, tile
    collect_reviews: bool = False
    reviews_only: bool = False
    review_end_date: Optional[str] = None # YYYY.MM.DD

class CrawlUrlRequest(BaseModel):
    url: str
    product_name: Optional[str] = None
    save_format: str = "both"
    split_mode: str = "aggressive"
    collect_reviews: bool = False
    reviews_only: bool = False
    review_end_date: Optional[str] = None

class CrawlParallelRequest(BaseModel):
    urls: List[str]
    concurrency: int = 3
    save_format: str = "both"
    split_mode: str = "aggressive"
    collect_reviews: bool = False
    reviews_only: bool = False
    review_end_date: Optional[str] = None

class CrawlerStatus(BaseModel):
    is_running: bool
    current_action: str
    progress: float
    logs: List[str]
    last_result: Optional[Dict[str, Any]] = None

class ProductResult(BaseModel):
    product_name: str
    folder_path: str
    image_path: str
    review_count: int
    rating: float
