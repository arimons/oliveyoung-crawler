from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from backend.models.schemas import CrawlKeywordRequest, CrawlUrlRequest, CrawlerStatus
from backend.services.crawler_service import crawler_service
import os
import subprocess
import platform

router = APIRouter()

def get_data_dir():
    """프로젝트 루트의 DATA 폴더 경로를 반환"""
    # 현재 파일의 절대 경로에서 프로젝트 루트 찾기
    current_file = os.path.abspath(__file__)
    # backend/api/routes.py -> backend/api -> backend -> project_root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_dir = os.path.join(project_root, "data")
    return data_dir

@router.get("/image/{folder_name}")
async def get_image(folder_name: str):
    data_dir = get_data_dir()
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
    data_dir = get_data_dir()
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
    data_dir = get_data_dir()
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

@router.post("/open-data-dir")
async def open_data_dir():
    """데이터 폴더를 시스템 탐색기로 열기"""
    data_dir = get_data_dir()

    # 폴더가 없으면 생성
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", data_dir])
        elif system == "Windows":
            subprocess.run(["explorer", data_dir])
        elif system == "Linux":
            subprocess.run(["xdg-open", data_dir])
        return {"message": "Data folder opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
