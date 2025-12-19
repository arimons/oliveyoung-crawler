import os
import shutil
import re
import json
from typing import List, Dict, Set, Any, Optional
from datetime import datetime

class HistoryService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = os.path.abspath(data_dir)

    def _get_all_folders(self) -> List[str]:
        if not os.path.exists(self.data_dir):
            return []
        return [f for f in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, f))]

    def cleanup_temp_folders(self) -> Dict[str, int]:
        """
        Delete temporary folders matching pattern like '251126_product_20251126_111043'
        or empty folders.
        """
        folders = self._get_all_folders()
        deleted_count = 0
        
        # Pattern: YYMMDD_product_YYYYMMDD_HHMMSS
        # Or just containing "product_" and timestamp if that's the failure mode
        temp_pattern = re.compile(r"^\d{6}_product_\d{8}_\d{6}$")
        
        for folder in folders:
            folder_path = os.path.join(self.data_dir, folder)
            
            # Check if it matches temp pattern
            if temp_pattern.match(folder):
                try:
                    shutil.rmtree(folder_path)
                    deleted_count += 1
                    print(f"[Cleanup] Deleted temp folder: {folder}")
                except Exception as e:
                    print(f"[Cleanup] Failed to delete {folder}: {e}")
                continue
                
            # Optional: Check for empty folders? 
            # Maybe risky if crawler is currently running and just created a folder.
            # We'll skip empty folder check for now to be safe, unless user explicitly asked.
            # User asked: "기존에 존재하는 임시폴더를 다 지워주는 로직" -> implies temp pattern.
            
        return {"deleted_count": deleted_count}

    def merge_specific_product(self, product_name: str) -> Optional[str]:
        """특정 상품명을 가진 폴더들을 하나로 병합"""
        folders = self._get_all_folders()
        product_folders = []
        
        for folder in folders:
            match = re.match(r"^(\d{6})_(.+)$", folder)
            if match and match.group(2) == product_name:
                product_folders.append(folder)
        
        if len(product_folders) < 2:
            return product_folders[0] if product_folders else None
            
        # 최신 폴더(날짜가 가장 큰 것)를 타겟으로 함
        product_folders.sort(reverse=True)
        target_folder = product_folders[0]
        source_folders = product_folders[1:]
        
        self._perform_merge(target_folder, source_folders)
        return os.path.join(self.data_dir, target_folder)

    def merge_duplicates(self) -> Dict[str, Any]:
        """중복된 상품명을 가진 모든 폴더들에 대해 병합 수행"""
        folders = self._get_all_folders()
        groups: Dict[str, List[str]] = {}
        
        for folder in folders:
            match = re.match(r"^(\d{6})_(.+)$", folder)
            if match:
                product_name = match.group(2)
                if product_name.startswith("product_20"): continue
                if product_name not in groups: groups[product_name] = []
                groups[product_name].append(folder)
        
        merged_count = 0
        total_groups = 0
        
        for product_name, folder_list in groups.items():
            if len(folder_list) < 2: continue
            total_groups += 1
            folder_list.sort(reverse=True)
            target = folder_list[0]
            sources = folder_list[1:]
            self._perform_merge(target, sources)
            merged_count += len(sources)
            
        return {"merged_groups": total_groups, "deleted_folders": merged_count}

    def _perform_merge(self, target_folder: str, source_folders: List[str]):
        """실제 병합 작업 수행 (리뷰 텍스트, 이미지, 분석 결과 등)"""
        target_path = os.path.join(self.data_dir, target_folder)
        
        # 1. 리뷰 텍스트 병합 (reviews.txt)
        all_review_texts = self._load_reviews_txt(target_path)
        seen_contents = set(all_review_texts)
        
        for src in source_folders:
            src_path = os.path.join(self.data_dir, src)
            src_texts = self._load_reviews_txt(src_path)
            for txt in src_texts:
                if txt not in seen_contents:
                    seen_contents.add(txt)
                    all_review_texts.append(txt)
        
        self._save_reviews_txt(target_path, all_review_texts)
        
        # 2. 관련 파일 복사 (이미지, 분석 결과 등)
        important_files = [
            "thumbnail.jpg", "product_detail_merged.jpg",
            "product_detail_merged_part1.jpg", "product_detail_merged_part2.jpg",
            "image_analysis.txt", "review_analysis.txt", "product_info.json"
        ]
        
        for src in source_folders:
            src_path = os.path.join(self.data_dir, src)
            for filename in important_files:
                target_file = os.path.join(target_path, filename)
                src_file = os.path.join(src_path, filename)
                if not os.path.exists(target_file) and os.path.exists(src_file):
                    try: shutil.copy2(src_file, target_file)
                    except: pass
            
            # 상세 이미지 폴더
            src_details = os.path.join(src_path, "detail_images")
            target_details = os.path.join(target_path, "detail_images")
            if not os.path.exists(target_details) and os.path.exists(src_details):
                try: shutil.copytree(src_details, target_details)
                except: pass
            
            # 원본 폴더 삭제
            try: shutil.rmtree(src_path)
            except: pass

        # 3. 최종 개수 업데이트
        self._update_review_count(target_path, len(all_review_texts))

    def _load_reviews_txt(self, folder_path: str) -> List[str]:
        txt_path = os.path.join(folder_path, "reviews.txt")
        if not os.path.exists(txt_path): return []
        
        reviews = []
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # [리뷰 N]으로 시작하고 --- 로 끝나는 블록 분리
                blocks = re.split(r'\[리뷰 \d+\]', content)
                for b in blocks:
                    clean = b.replace('-'*80, '').strip()
                    if clean: reviews.append(clean)
        except: pass
        return reviews

    def _save_reviews_txt(self, folder_path: str, reviews: List[str]):
        txt_path = os.path.join(folder_path, "reviews.txt")
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"총 {len(reviews)}개의 리뷰\n")
                f.write("=" * 80 + "\n\n")
                for i, txt in enumerate(reviews):
                    f.write(f"[리뷰 {i+1}]\n{txt}\n{'-'*80}\n")
        except: pass

    def _update_review_count(self, folder_path: str, count: int):
        info_path = os.path.join(folder_path, "product_info.json")
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                info["수집된_리뷰_개수"] = count
                info["병합시각"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
            except: pass

    def _make_review_signature(self, review: Dict) -> str:
        parts = [str(review.get("text", ""))]
        return "|".join(parts)
