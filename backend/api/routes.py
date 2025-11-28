from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from backend.models.schemas import CrawlKeywordRequest, CrawlUrlRequest, CrawlerStatus, CrawlParallelRequest
from backend.services.crawler_service import CrawlerService
from backend.services.parallel_crawler_service import ParallelCrawlerService
from backend.services.ai_service import AIAnalysisService
from backend.config_manager import ConfigManager
import os
import subprocess
import platform
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()
crawler_service = CrawlerService()
parallel_crawler_service = ParallelCrawlerService()
config_manager = ConfigManager()

# ... (ConfigRequest, AnalysisRequest models) ...

@router.post("/crawl/parallel")
async def start_crawl_parallel(request: CrawlParallelRequest, background_tasks: BackgroundTasks):
    """
    Start parallel crawling of multiple URLs using background tasks.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
        
    def run_parallel_crawl():
        parallel_crawler_service.start_parallel_crawl(
            urls=request.urls,
            max_workers=request.concurrency,
            save_format=request.save_format,
            split_mode=request.split_mode,
            collect_reviews=request.collect_reviews,
            review_end_date=request.review_end_date,
            reviews_only=request.reviews_only
        )
        
    background_tasks.add_task(run_parallel_crawl)
    return {"message": "Parallel crawl started in background", "task_count": len(request.urls)}

@router.get("/crawl/parallel/status")
async def get_parallel_status():
    """Get parallel crawl status"""
    return parallel_crawler_service.get_status()


class ConfigRequest(BaseModel):
    openai_api_key: Optional[str] = None
    review_prompt: Optional[str] = None
    image_prompt: Optional[str] = None

class AnalysisRequest(BaseModel):
    product_folder: str
    prompt: Optional[str] = None

@router.get("/image/{folder_name}")
async def get_image(folder_name: str):
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, folder_name)
    
    # Try thumbnail first
    thumb_path = os.path.join(folder_path, "thumbnail.jpg")
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path)
        
    # Fallback to merged image
    image_path = os.path.join(folder_path, "product_detail_merged.jpg")
    if os.path.exists(image_path):
        return FileResponse(image_path)
        
    return HTTPException(status_code=404, detail="Image not found")


@router.post("/crawl/keyword")
async def start_crawl_keyword(request: CrawlKeywordRequest):
    if crawler_service.is_running:
        raise HTTPException(status_code=400, detail="Crawler is already running")
    
    try:
        crawler_service.crawl_keyword(
            request.keyword, 
            request.max_products, 
            request.save_format,
            request.split_mode,
            request.collect_reviews,
            request.review_end_date,
            request.reviews_only
        )
        return {"message": "Crawl started", "keyword": request.keyword}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl/url")
async def start_crawl_url(request: CrawlUrlRequest):
    if crawler_service.is_running:
        raise HTTPException(status_code=400, detail="Crawler is already running")
    
    try:
        crawler_service.crawl_url(
            request.url, 
            request.product_name, 
            request.save_format,
            request.split_mode,
            request.collect_reviews,
            request.review_end_date,
            request.reviews_only
        )
        return {"message": "Crawl started", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=CrawlerStatus)
async def get_status():
    return crawler_service.get_status()

@router.post("/stop")
async def stop_crawler():
    crawler_service.stop_crawler_instance()
    return {"message": "Crawler stopped"}

@router.get("/results")
async def list_results():
    # List folders in 'data' directory
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        return []
    
    results = []
    for folder in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder)
        if os.path.isdir(folder_path):
            # Try to read product_info.json
            json_path = os.path.join(folder_path, "product_info.json")
            info = {}
            if os.path.exists(json_path):
                import json
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                except:
                    pass
            
            results.append({
                "folder_name": folder,
                "product_name": info.get("상품명", folder),
                "image_path": info.get("썸네일_경로") or info.get("이미지_경로", ""),
                "review_count": info.get("리뷰_총개수", 0),
                "rating": info.get("별점", 0.0),
                "crawled_at": info.get("수집시각", "")
            })
    
    # Sort by folder name (date) descending
    results.sort(key=lambda x: x["folder_name"], reverse=True)
    return results

@router.post("/open-folder/{folder_name}")
async def open_folder(folder_name: str):
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, folder_name)
    
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")
        
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        elif system == "Windows":
            subprocess.run(["explorer", folder_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", folder_path])
        return {"message": "Folder opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_config():
    config = config_manager.load_config()
    # Mask API key for security
    if config.get("openai_api_key"):
        # Show only first 3 and last 4 chars
        key = config["openai_api_key"]
        if len(key) > 10:
            config["openai_api_key"] = key[:3] + "..." + key[-4:]
    return config

@router.post("/config")
async def save_config(request: ConfigRequest):
    config_manager.save_config({
        "openai_api_key": request.openai_api_key,
        "model": request.model,
        "review_prompt": request.review_prompt,
        "image_prompt": request.image_prompt
    })
    return {"message": "Configuration saved"}

@router.post("/analyze/reviews")
async def analyze_reviews(request: AnalysisRequest):
    config = config_manager.load_config()
    api_key = config.get("openai_api_key")
    model = config.get("model", "gpt-4o-mini")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key is required")
        
    # Load review text from product folder
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, request.product_folder)
    
    # Try multiple possible review files
    review_files = ["reviews.txt", "reviews.csv", "reviews.json"]
    review_text = ""
    
    for filename in review_files:
        path = os.path.join(folder_path, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    review_text = f.read()
                    # Limit text length to avoid token limits (approx 10000 chars)
                    if len(review_text) > 10000:
                        review_text = review_text[:10000] + "...(truncated)"
                break
            except:
                continue
                
    if not review_text:
        raise HTTPException(status_code=404, detail="No review data found for this product")
        
    ai_service = AIAnalysisService(api_key)
    result = ai_service.analyze_reviews(review_text, request.prompt or config.get("review_prompt"), model=model)
    return {"result": result}

@router.post("/analyze/images")
async def analyze_images(request: AnalysisRequest):
    config = config_manager.load_config()
    api_key = config.get("openai_api_key")
    model = config.get("model", "gpt-4o-mini")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key is required")
        
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, request.product_folder)
    
    # Collect images
    image_paths = []
    
    # 1. Merged image (priority)
    merged_path = os.path.join(folder_path, "product_detail_merged.jpg")
    if os.path.exists(merged_path):
        image_paths.append(merged_path)
        
    # 2. Detail images
    detail_dir = os.path.join(folder_path, "detail_images")
    if os.path.exists(detail_dir):
        for img in sorted(os.listdir(detail_dir)):
            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_paths.append(os.path.join(detail_dir, img))
                
    if not image_paths:
        raise HTTPException(status_code=404, detail="No images found for this product")
        
    ai_service = AIAnalysisService(api_key)
    result = ai_service.analyze_images(image_paths, request.prompt or config.get("image_prompt"), model=model)
    return {"result": result}

# History Management
from backend.services.history_service import HistoryService
history_service = HistoryService()

@router.post("/history/merge")
async def merge_history():
    try:
        result = history_service.merge_duplicates()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history/cleanup")
async def cleanup_history():
    try:
        result = history_service.cleanup_temp_folders()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
