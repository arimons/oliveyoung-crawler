import json
import os
from typing import Dict, Any

# Project root directory (backend/.. -> project_root)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "user_config.json")

class ConfigManager:
    def __init__(self):
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "openai_api_key": ""
        }

        if not os.path.exists(CONFIG_FILE):
            return default_config
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Only keep API key
                return {"openai_api_key": loaded_config.get("openai_api_key", "")}
        except Exception:
            return default_config

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file (only API key)."""
        # Only save API key
        config_to_save = {"openai_api_key": config.get("openai_api_key", "")}
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, ensure_ascii=False, indent=2)
    
    def get_default_prompts(self) -> Dict[str, str]:
        """Get default prompts (not stored in config file)."""
        return {
            "review_prompt": """당신은 화장품 마케팅 전문가입니다. 아래 리뷰 데이터를 보고 다음을 분석해주세요:

1. 고객이 가장 선호하는 제품 특징
2. 개선이 필요한 부분
3. 리뷰에서 반복적으로 등장하는 핵심 키워드
4. 마케팅 메시지에 활용 가능한 표현이나 문구
5. 제품 경쟁력 포인트 요약

각 항목을 명확한 제목과 함께 글머리 기호(•)를 사용한 목록 형식으로 정리해주세요. 
표는 사용하지 마세요.
요청한 분석만 제공하고, 추가 제안이나 질문은 하지 마세요.""",
            "image_prompt": """당신은 화장품 연구원입니다. 제품 상세 이미지를 분석하여 다음 4가지 핵심 정보를 추출해주세요.

**1. 원포인트 (One-Point)**
• 제품을 한마디로 정의하는 메인 카피나 슬로건
• 가장 강조하고 있는 핵심 컨셉

**2. 임상 (Clinical)**
• 효능/효과를 객관적으로 입증하는 임상 시험 결과를 **누락없이** 모두 추출
• 구체적인 수치(%, 개선율, 만족도, 배 증가 등)가 있다면 **반드시 포함**
• **시간 정보 필수**: "사용 전", "사용 직후", "즉시", "1회 사용 후", "X일 후", "X주 후", "X개월 사용" 등 측정 시점이 명시된 경우 **반드시 함께 기록**
• 예시: "사용 2주 후 주름 개선 87%", "즉시 보습력 120% 증가", "4주 사용 후 탄력 개선"
• "검증된", "테스트 완료", "임상 실험", "피부과 테스트" 등의 문구 확인
• ⚠️ **제외**: 단순 가격, 용량, 할인율, 세트 구성 등 판매 정보는 제외

**3. 소재 (Material)**
• 제품만의 특별한 성분이나 기술력
• 특허 성분, 독자 개발 원료 등 차별화된 소재 정보

**4. 리뷰 (Review)**
• 상세 페이지 내에 판매자가 선별하여 포함시킨 'Best 리뷰'나 '사용자 후기' 내용
• 실제 사용자의 목소리로 강조된 포인트

**주의사항:**
- 제품명, 가격, 용량, 1+1 구성 등 단순 판매 정보는 제외하세요.
- 수치는 '효능 입증'과 관련된 것만 기록하세요.
- 각 항목은 글머리 기호(•)로 정리해주세요.
- 표는 사용하지 마세요.
- 분석이 불가능한 항목은 "정보 없음"으로 표시하세요."""
        }
