import os
import base64
from typing import List, Dict, Optional
from openai import OpenAI

class AIAnalysisService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def _get_token_param(self, model: str, max_tokens: int) -> Dict[str, int]:
        """
        모델에 따라 max_tokens 또는 max_completion_tokens 파라미터 반환
        o1 계열 및 gpt-5 계열 모델은 max_completion_tokens 사용
        """
        if model.startswith("o1-") or model.startswith("gpt-5"):
            return {"max_completion_tokens": max_tokens}
        return {"max_tokens": max_tokens}

    def analyze_reviews(self, review_text: str, prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Analyze product reviews using OpenAI API.
        """
        try:
            # GPT-5 models need much higher limits due to reasoning tokens
            if model.startswith("gpt-5"):
                max_tokens = 8000  # GPT-5 uses reasoning tokens internally
            else:
                max_tokens = 3000  # Other models
                
            token_param = self._get_token_param(model, max_tokens)
            
            print(f"📤 Sending to OpenAI:")
            print(f"   Model: {model}")
            print(f"   Prompt length: {len(prompt)} chars")
            print(f"   Review text length: {len(review_text)} chars")
            print(f"   Token param: {token_param}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes product reviews."},
                    {"role": "user", "content": f"{prompt}\n\nReviews:\n{review_text}"}
                ],
                **token_param
            )
            
            print(f"📥 OpenAI Response received:")
            print(f"   Response ID: {response.id}")
            print(f"   Model: {response.model}")
            print(f"   Finish reason: {response.choices[0].finish_reason}")
            
            result = response.choices[0].message.content
            # print(f"🔍 AI Response: {result[:200] if result else 'None'}...")  # Debug log removed
            
            if not result:
                print(f"⚠️ Empty response details:")
                print(f"   Full response: {response}")
                
            return result if result else "AI returned empty response"
        except Exception as e:
            print(f"❌ AI Service Error: {str(e)}")  # Debug log
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return f"Error analyzing reviews: {str(e)}"

    def analyze_images(self, image_paths: List[str], prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Analyze product images using OpenAI API.
        Splits long vertical images into chunks to avoid resolution loss.
        """
        try:
            from PIL import Image
            import io
            
            content = [{"type": "text", "text": prompt}]
            total_chunks = 0
            
            for img_path in image_paths[:5]:  # Limit to 5 source images
                if os.path.exists(img_path):
                    try:
                        with Image.open(img_path) as img:
                            # Convert to RGB if needed
                            if img.mode in ('RGBA', 'P'):
                                img = img.convert('RGB')
                                
                            width, height = img.size
                            
                            # Split long images (height > 2000px)
                            if height > 2000:
                                chunk_height = 2000
                                overlap = 200
                                current_y = 0
                                
                                while current_y < height:
                                    # Calculate chunk end
                                    end_y = min(current_y + chunk_height, height)
                                    
                                    # Crop chunk
                                    chunk = img.crop((0, current_y, width, end_y))
                                    
                                    # Convert chunk to base64
                                    buffered = io.BytesIO()
                                    chunk.save(buffered, format="JPEG", quality=85)
                                    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                    
                                    content.append({
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    })
                                    total_chunks += 1
                                    
                                    # Move to next chunk with overlap
                                    if end_y == height:
                                        break
                                    current_y += (chunk_height - overlap)
                                    
                                    # Safety limit for chunks per image
                                    if total_chunks > 10: 
                                        break
                            else:
                                # Small enough, send as is
                                buffered = io.BytesIO()
                                img.save(buffered, format="JPEG", quality=85)
                                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                })
                                total_chunks += 1
                                
                    except Exception as e:
                        print(f"⚠️ Failed to process image {img_path}: {e}")

            # GPT-5 models need higher limits due to reasoning tokens
            if model.startswith("gpt-5"):
                max_tokens = 5000
            else:
                max_tokens = 2000
                
            token_param = self._get_token_param(model, max_tokens)
            
            print(f"📤 Sending to OpenAI (Image Analysis):")
            print(f"   Model: {model}")
            print(f"   Prompt length: {len(prompt)} chars")
            print(f"   Image count: {len(image_paths[:5])}")
            print(f"   Total chunks sent: {total_chunks}")
            print(f"   Token param: {token_param}")

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes product images."},
                    {"role": "user", "content": content}
                ],
                **token_param
            )
            
            print(f"📥 OpenAI Response received:")
            print(f"   Response ID: {response.id}")
            print(f"   Model: {response.model}")
            print(f"   Finish reason: {response.choices[0].finish_reason}")
            
            result = response.choices[0].message.content
            # print(f"🔍 AI Response: {result[:200] if result else 'None'}...")
            
            if not result:
                print(f"⚠️ Empty response details:")
                print(f"   Full response: {response}")
                
            return result if result else "AI returned empty response"
        except Exception as e:
            print(f"❌ AI Service Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return f"Error analyzing images: {str(e)}"
