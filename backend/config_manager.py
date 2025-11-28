import json
import os
from typing import Dict, Any

CONFIG_FILE = os.path.join("config", "user_config.json")

class ConfigManager:
    def __init__(self):
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "openai_api_key": "",
            "model": "gpt-5-mini",
            "review_prompt": "당신은 화장품 마케팅 전문가입니다. 아래 리뷰 데이터를 보고 다음을 분석해주세요:\n1. 고객이 가장 선호하는 제품 특징\n2. 개선이 필요한 부분\n3. 리뷰에서 반복적으로 등장하는 핵심 키워드\n4. 마케팅 메시지에 활용 가능한 표현이나 문구\n5. 제품 경쟁력 포인트 요약\n표 또는 목록 형식으로 정리",
            "image_prompt": "당신은 화장품 리뷰어입니다. 아래 제품 이미지를 보고 소비자 관점에서 다음을 작성해 주세요:\n1. 제품을 사용하면 기대되는 효과\n2. 포장/디자인이 주는 인상\n3. 제품 이미지에서 강조되는 성분이나 기능\n4. 이미지에서 느껴지는 브랜드 컨셉\n5. 구매욕을 자극할만한 시각적 포인트\n표로 정리하거나 요약 가능"
        }

        if not os.path.exists(CONFIG_FILE):
            return default_config
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Merge defaults for any missing keys
                for key, value in default_config.items():
                    if key not in loaded_config or not loaded_config[key]: # If missing or empty
                        loaded_config[key] = value
                return loaded_config
        except Exception:
            return default_config

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        current_config = self.load_config()
        current_config.update(config)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, ensure_ascii=False, indent=2)
