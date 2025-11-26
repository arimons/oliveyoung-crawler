import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError


def translate_korean_to_japanese(text_to_translate: str):
    """
    .env에서 API 키를 로드하고 Gemini 모델을 사용하여
    주어진 한국어 문장을 일본어로 번역합니다.
    """
    # 1. .env 파일에서 환경 변수를 로드합니다.
    load_dotenv()

    # 2. GEMINI_API_KEY를 가져옵니다.
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해 주세요."
        )

    try:
        # 3. Gemini 클라이언트 초기화 (API 키 자동 사용)
        # client = genai.Client()를 사용하면 load_dotenv로 로드된 API 키를 자동으로 사용합니다.
        client = genai.Client(api_key=api_key)

        # 4. 모델에게 번역 요청을 위한 프롬프트 구성
        prompt = (
            f"주어진 한국어 문장 '{text_to_translate}'을(를) 존댓말을 사용하여 "
            "가장 자연스러운 일본어로 번역해 주세요. 번역 결과만 출력하세요."
        )

        # 5. API 호출 (텍스트 생성 요청)
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # 번역 및 텍스트 처리에 적합한 빠른 모델
            contents=prompt,
        )

        # 6. 번역 결과 출력
        print("--- 번역 결과 ---")
        print(f"원본 (한국어): {text_to_translate}")
        print(f"번역 (일본어): {response.text.strip()}")
        print("-----------------")

    except APIError as e:
        print(f"API 호출 중 오류가 발생했습니다: {e}")
        print(
            "API 키가 유효한지, 그리고 API 사용량 제한을 초과하지 않았는지 확인해 주세요."
        )
    except Exception as e:
        print(f"예기치 않은 오류 발생: {e}")


if __name__ == "__main__":
    korean_sentence = "안녕하세요"
    translate_korean_to_japanese(korean_sentence)
