from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from backend.models.schemas import CrawlKeywordRequest, CrawlUrlRequest, CrawlerStatus, CrawlParallelRequest
from backend.services.crawler_service import CrawlerService
from backend.services.parallel_crawler_service import ParallelCrawlerService
from backend.services.ai_service import AIAnalysisService
from backend.services.history_service import HistoryService
from backend.config_manager import ConfigManager
import os
import subprocess
import platform
import json
import re
from typing import Optional
from pydantic import BaseModel
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime

router = APIRouter()
crawler_service = CrawlerService()
parallel_crawler_service = ParallelCrawlerService()
history_service = HistoryService()
config_manager = ConfigManager()

# Pydantic Models
class ConfigRequest(BaseModel):
    openai_api_key: Optional[str] = None

class AnalysisRequest(BaseModel):
    product_folder: str
    prompt: Optional[str] = None
    model: Optional[str] = "gpt-4o-mini"

# Helper Functions
def clean_oliveyoung_url(url: str) -> str:
    """Remove 'tab' parameter from Olive Young URL"""
    try:
        if not url:
            return url
            
        parsed = urlparse(url)
        if "oliveyoung.co.kr" not in parsed.netloc:
            return url
            
        query = parse_qs(parsed.query)
        if 'tab' in query:
            del query['tab']
            
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
    except Exception as e:
        print(f"URL cleaning failed: {e}")
        return url

# Crawling Endpoints
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
    
    cleaned_url = clean_oliveyoung_url(request.url)
    
    try:
        crawler_service.crawl_url(
            cleaned_url, 
            request.product_name, 
            request.save_format,
            request.split_mode,
            request.collect_reviews,
            request.review_end_date,
            request.reviews_only
        )
        return {"message": "Crawl started", "url": cleaned_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl/parallel")
async def start_crawl_parallel(request: CrawlParallelRequest, background_tasks: BackgroundTasks):
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    cleaned_urls = [clean_oliveyoung_url(url) for url in request.urls]
        
    def run_parallel_crawl():
        parallel_crawler_service.start_parallel_crawl(
            urls=cleaned_urls,
            max_workers=request.concurrency,
            save_format=request.save_format,
            split_mode=request.split_mode,
            collect_reviews=request.collect_reviews,
            review_end_date=request.review_end_date,
            reviews_only=request.reviews_only
        )
        
    background_tasks.add_task(run_parallel_crawl)
    return {"message": "Parallel crawl started in background", "task_count": len(cleaned_urls)}

@router.get("/status", response_model=CrawlerStatus)
async def get_status():
    return crawler_service.get_status()

@router.get("/crawl/parallel/status")
async def get_parallel_status():
    return parallel_crawler_service.get_status()

@router.post("/stop")
async def stop_crawler():
    crawler_service.stop_crawler_instance()
    return {"message": "Crawler stopped"}

# Results & History Endpoints
@router.get("/results")
async def list_results():
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        return []
    
    results = []
    for folder in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder)
        if os.path.isdir(folder_path):
            json_path = os.path.join(folder_path, "product_info.json")
            info = {}
            if os.path.exists(json_path):
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
        if system == "Darwin":
            subprocess.run(["open", folder_path])
        elif system == "Windows":
            subprocess.run(["explorer", folder_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", folder_path])
        return {"message": "Folder opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open-data-dir")
async def open_data_dir():
    data_dir = os.path.join(os.getcwd(), "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", data_dir])
        elif system == "Windows":
            subprocess.run(["explorer", data_dir])
        elif system == "Linux":
            subprocess.run(["xdg-open", data_dir])
        return {"message": "Data directory opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image/{folder_name}")
async def get_image(folder_name: str):
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, folder_name)
    
    thumb_path = os.path.join(folder_path, "thumbnail.jpg")
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path)
        
    image_path = os.path.join(folder_path, "product_detail_merged.jpg")
    if os.path.exists(image_path):
        return FileResponse(image_path)
        
    raise HTTPException(status_code=404, detail="Image not found")

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

# Configuration Endpoints
@router.get("/config")
async def get_config():
    config = config_manager.load_config()
    if config.get("openai_api_key"):
        key = config["openai_api_key"]
        if len(key) > 10:
            config["openai_api_key"] = key[:3] + "..." + key[-4:]
    return config

@router.post("/config")
async def save_config(request: ConfigRequest):
    print(f"💾 Saving config: api_key={'SET' if request.openai_api_key else 'EMPTY'}")
    config_manager.save_config({
        "openai_api_key": request.openai_api_key
    })
    print(f"✅ Config saved successfully")
    return {"message": "Configuration saved"}

@router.get("/prompts")
async def get_prompts():
    """Get default prompts"""
    return config_manager.get_default_prompts()

# AI Analysis Endpoints
@router.post("/analyze/reviews")
async def analyze_reviews(request: AnalysisRequest):
    config = config_manager.load_config()
    api_key = config.get("openai_api_key")
    model = request.model or 'gpt-4o-mini'
    
    prompts = config_manager.get_default_prompts()
    default_prompt = prompts['review_prompt']
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key is required")
        
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, request.product_folder)
    print(f"🔍 Analyzing reviews for folder: {request.product_folder}")
    
    # Load reviews
    reviews = []
    json_path = os.path.join(folder_path, "reviews.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load reviews.json: {e}")
    
    if not reviews:
        txt_path = os.path.join(folder_path, "reviews.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
                    print(f"✅ Loaded reviews.txt ({len(full_text)} chars)")
                    full_text = full_text[:200000]
            except:
                pass
        
        if 'full_text' not in locals() or not full_text:
            print("⚠️ No reviews found to analyze")
            return {"result": "리뷰 데이터가 없습니다."}
    else:
        print(f"✅ Loaded {len(reviews)} reviews from json")
        review_texts = [r.get("content", "") for r in reviews]
        full_text = "\n".join(review_texts)[:200000]

    # Clean text
    full_text = re.sub(r'^[=\-]{10,}$', '', full_text, flags=re.MULTILINE)
    full_text = re.sub(r'^총 \d+개의 리뷰.*$', '', full_text, flags=re.MULTILINE)
    full_text = re.sub(r'\[\d{4}[.-]\d{2}[.-]\d{2}\]', '', full_text)
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    full_text = full_text.strip()
    
    print(f"📝 Cleaned text length: {len(full_text)} chars")

    # Call AI Service
    try:
        print(f"🚀 Calling AI Service with model: {model}")
        ai_service = AIAnalysisService(api_key)
        result = ai_service.analyze_reviews(full_text, request.prompt or default_prompt, model=model)
        print(f"✅ AI Analysis complete. Result length: {len(result)}")
        
        # Save result to file
        analysis_file = os.path.join(folder_path, "review_analysis.txt")
        try:
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(f"=== 리뷰 분석 결과 ===\n")
                f.write(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"사용 모델: {model}\n")
                f.write(f"분석 리뷰 수: {len(full_text)} chars\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(result)
            print(f"💾 Analysis saved to: {analysis_file}")
        except Exception as e:
            print(f"⚠️ Failed to save analysis: {e}")
        
        return {"result": result}
    except Exception as e:
        print(f"❌ AI Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/images")
async def analyze_images(request: AnalysisRequest):
    print(f"🔍 Analyzing images for folder: {request.product_folder}")
    config = config_manager.load_config()
    api_key = config.get("openai_api_key")
    model = request.model or 'gpt-4o-mini'
    
    prompts = config_manager.get_default_prompts()
    default_prompt = prompts['image_prompt']
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key is required")
        
    data_dir = os.path.join(os.getcwd(), "data")
    folder_path = os.path.join(data_dir, request.product_folder)
    print(f"📂 Target folder path: {folder_path}")
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder does not exist: {folder_path}")
        raise HTTPException(status_code=404, detail="Product folder not found")
    
    # Collect images
    image_paths = []
    
    merged_path = os.path.join(folder_path, "product_detail_merged.jpg")
    if os.path.exists(merged_path):
        image_paths.append(merged_path)
        print(f"✅ Found merged image: {merged_path}")
    else:
        print(f"⚠️ Merged image not found at: {merged_path}")
        
    detail_dir = os.path.join(folder_path, "detail_images")
    if os.path.exists(detail_dir):
        print(f"📂 Checking detail_images dir: {detail_dir}")
        for img in sorted(os.listdir(detail_dir)):
            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_paths.append(os.path.join(detail_dir, img))
    else:
        print(f"⚠️ Detail images dir not found at: {detail_dir}")

    if not image_paths:
        print(f"🔍 Checking main folder for product_detail*.jpg: {folder_path}")
        for img in sorted(os.listdir(folder_path)):
            if img.lower().startswith("product_detail") and img.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_paths.append(os.path.join(folder_path, img))
                print(f"  Found image: {img}")
                
    if not image_paths:
        print("❌ No images found to analyze")
        raise HTTPException(status_code=404, detail="No images found for this product")
        
    print(f"🚀 Calling AI Service with {len(image_paths)} images")
    try:
        ai_service = AIAnalysisService(api_key)
        result = ai_service.analyze_images(image_paths, request.prompt or default_prompt, model=model)
        print("✅ Image analysis complete")
        
        # Save result to file
        analysis_file = os.path.join(folder_path, "image_analysis.txt")
        try:
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(f"=== 이미지 분석 결과 ===\n")
                f.write(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"사용 모델: {model}\n")
                f.write(f"분석 이미지 수: {len(image_paths)}\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(result)
            print(f"💾 Analysis saved to: {analysis_file}")
        except Exception as e:
            print(f"⚠️ Failed to save analysis: {e}")
        
        return {"result": result}
    except Exception as e:
        print(f"❌ Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
