from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CrawlKeywordRequest(BaseModel):
    keyword: str
    max_products: int = 10
    save_format: str = "both" # json, csv, both
    split_mode: str = "conservative" # conservative, aggressive, tile
    collect_reviews: bool = False
    reviews_only: bool = False
    review_end_date: Optional[str] = None # YYYY.MM.DD
    max_reviews: int = 300

class CrawlUrlRequest(BaseModel):
    url: str
    product_name: Optional[str] = None
    save_format: str = "both"
    split_mode: str = "conservative"
    collect_reviews: bool = False
    reviews_only: bool = False
    review_end_date: Optional[str] = None
    max_reviews: int = 300

class CrawlParallelRequest(BaseModel):
    urls: List[str]
    concurrency: int = 3
    save_format: str = "both"
    split_mode: str = "conservative"
    collect_reviews: bool = False
    reviews_only: bool = False
    review_end_date: Optional[str] = None
    max_reviews: int = 300

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

class AnalysisRequest(BaseModel):
    product_folder: str
    prompt: Optional[str] = None
    model: Optional[str] = "gpt-4o-mini"
