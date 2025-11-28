import os
import shutil
import re
import json
from typing import List, Dict, Set, Any
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

    def merge_duplicates(self) -> Dict[str, Any]:
        """
        Merge folders with the same product name.
        Keep the newest folder, merge reviews from older folders, then delete older folders.
        """
        folders = self._get_all_folders()
        
        # Group by product name
        # Folder format: YYMMDD_ProductName
        # We need to extract ProductName.
        # Be careful if ProductName contains underscores.
        # The prefix is always 6 digits + underscore.
        
        groups: Dict[str, List[str]] = {}
        
        for folder in folders:
            # Check if folder starts with date prefix
            match = re.match(r"^(\d{6})_(.+)$", folder)
            if match:
                date_str = match.group(1)
                product_name = match.group(2)
                
                # Skip if it looks like a temp folder
                if product_name.startswith("product_20"):
                    continue
                    
                if product_name not in groups:
                    groups[product_name] = []
                groups[product_name].append(folder)
        
        merged_count = 0
        total_groups = 0
        
        for product_name, folder_list in groups.items():
            if len(folder_list) < 2:
                continue
                
            total_groups += 1
            
            # Sort by date descending (assuming folder name prefix YYMMDD is sortable)
            # If multiple folders have same date, sort by full name (timestamp usually not in name unless temp)
            # Actually, if same date, we might have collision or suffix? 
            # Let's just sort reverse=True.
            folder_list.sort(reverse=True)
            
            target_folder = folder_list[0]
            source_folders = folder_list[1:]
            
            print(f"[Merge] Merging {len(source_folders)} folders into {target_folder} for '{product_name}'")
            
            target_path = os.path.join(self.data_dir, target_folder)
            
            # Collect all reviews
            all_reviews = []
            seen_reviews = set() # To avoid duplicates
            
            # 1. Load reviews from target first (to keep them)
            target_reviews = self._load_reviews(target_path)
            for r in target_reviews:
                # Create a signature for deduplication
                # Assuming review has 'date', 'author', 'content' or similar
                # If it's just a list of dicts
                sig = self._make_review_signature(r)
                if sig not in seen_reviews:
                    seen_reviews.add(sig)
                    all_reviews.append(r)
            
            # 2. Load from sources
            for src_folder in source_folders:
                src_path = os.path.join(self.data_dir, src_folder)
                src_reviews = self._load_reviews(src_path)
                
                for r in src_reviews:
                    sig = self._make_review_signature(r)
                    if sig not in seen_reviews:
                        seen_reviews.add(sig)
                        all_reviews.append(r)
                        
                # We don't copy images, as per plan (keep newest only)
                
                # Delete source folder
                try:
                    shutil.rmtree(src_path)
                    print(f"[Merge] Deleted source: {src_folder}")
                except Exception as e:
                    print(f"[Merge] Failed to delete {src_folder}: {e}")
            
            # 3. Save merged reviews to target
            if all_reviews:
                self._save_reviews(target_path, all_reviews)
                
                # Update review count in product_info.json
                self._update_review_count(target_path, len(all_reviews))
            
            merged_count += len(source_folders)
            
        return {"merged_groups": total_groups, "deleted_folders": merged_count}

    def _load_reviews(self, folder_path: str) -> List[Dict]:
        # Try json first
        json_path = os.path.join(folder_path, "reviews.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Try csv? (Parsing CSV to dict is harder without pandas, maybe skip for now if JSON is primary)
        # The crawler saves both usually. We'll rely on JSON.
        return []

    def _save_reviews(self, folder_path: str, reviews: List[Dict]):
        json_path = os.path.join(folder_path, "reviews.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Merge] Failed to save reviews: {e}")

    def _update_review_count(self, folder_path: str, count: int):
        info_path = os.path.join(folder_path, "product_info.json")
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                
                info["리뷰_총개수"] = count # Update count
                info["병합됨"] = True
                info["병합시각"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
            except:
                pass

    def _make_review_signature(self, review: Dict) -> str:
        # Create a unique string for the review
        # Adjust fields based on actual review structure
        # Common fields: date, author, option, content, rating
        parts = [
            str(review.get("date", "")),
            str(review.get("author", "")),
            str(review.get("content", "")[:50]) # First 50 chars of content
        ]
        return "|".join(parts)
