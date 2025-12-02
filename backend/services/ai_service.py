import os
import base64
from typing import List, Dict, Optional
from openai import OpenAI
import google.generativeai as genai

class AIAnalysisService:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        
        if model.startswith('gemini'):
            # Configure Gemini client
            genai.configure(api_key=api_key)
            self.client = None  # Will use genai directly
        else:
            # Configure OpenAI client
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
        Analyze product reviews using OpenAI or Gemini API.
        """
        try:
            if model.startswith('gemini'):
                return self._analyze_with_gemini(review_text, prompt, model)
            else:
                return self._analyze_with_openai(review_text, prompt, model)
        except Exception as e:
            print(f"❌ AI Service Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return f"Error analyzing reviews: {str(e)}"

    def _analyze_with_gemini(self, review_text: str, prompt: str, model: str) -> str:
        """
        Analyze using Gemini API
        """
        print(f"📤 Sending to Gemini:")
        print(f"   Model: {model}")
        print(f"   Prompt length: {len(prompt)} chars")
        print(f"   Review text length: {len(review_text)} chars")
        
        # Create Gemini model instance
        model_instance = genai.GenerativeModel(model)
        
        # Prepare the full prompt
        full_prompt = f"You are a helpful assistant that analyzes product reviews.\n\n{prompt}\n\nReviews:\n{review_text}"
        
        # Generate response
        response = model_instance.generate_content(full_prompt)
        
        print(f"📥 Gemini Response received:")
        print(f"   Model: {model}")
        print(f"   Finish reason: {response.finish_reason if hasattr(response, 'finish_reason') else 'N/A'}")
        
        result = response.text if response.text else None
        
        if not result:
            print(f"⚠️ Empty response details:")
            print(f"   Full response: {response}")
            
        return result if result else "Gemini returned empty response"

    def _analyze_with_openai(self, review_text: str, prompt: str, model: str) -> str:
        """
        Analyze using OpenAI API
        """
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
        
        if not result:
            print(f"⚠️ Empty response details:")
            print(f"   Full response: {response}")
            
        return result if result else "OpenAI returned empty response"

    def analyze_images(self, image_paths: List[str], prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Analyze product images using OpenAI or Gemini API.
        Splits long vertical images into chunks to avoid resolution loss.
        """
        try:
            if model.startswith('gemini'):
                return self._analyze_images_with_gemini(image_paths, prompt, model)
            else:
                return self._analyze_images_with_openai(image_paths, prompt, model)
        except Exception as e:
            print(f"❌ AI Service Error: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return f"Error analyzing images: {str(e)}"

    def _analyze_images_with_gemini(self, image_paths: List[str], prompt: str, model: str) -> str:
        """
        Analyze images using Gemini API
        Splits long vertical images (height > 3000px) into chunks to fit Gemini's 3072x3072 limit
        NO RESIZING - only splits to preserve image detail
        """
        from PIL import Image
        import io
        
        print(f"📤 Sending to Gemini (Image Analysis):")
        print(f"   Model: {model}")
        print(f"   Prompt length: {len(prompt)} chars")
        print(f"   Image count: {len(image_paths[:5])}")
        
        # Create Gemini model instance
        model_instance = genai.GenerativeModel(model)
        
        # Prepare content with images
        content = [prompt]
        processed_count = 0
        
        for img_path in image_paths[:5]:  # Limit to 5 images
            if os.path.exists(img_path):
                try:
                    with Image.open(img_path) as img:
                        # Convert to RGB if needed
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        
                        width, height = img.size
                        
                        # Split long images (height > 3000px for Gemini's 3072x3072 limit)
                        if height > 3000:
                            chunk_height = 3000
                            overlap = 200
                            current_y = 0
                            chunk_count = 0
                            
                            while current_y < height:
                                # Calculate chunk end
                                end_y = min(current_y + chunk_height, height)
                                
                                # Crop chunk
                                chunk = img.crop((0, current_y, width, end_y))
                                
                                # Convert chunk to bytes for Gemini
                                buffered = io.BytesIO()
                                chunk.save(buffered, format="JPEG", quality=85, optimize=True)
                                file_size_mb = len(buffered.getvalue()) / (1024 * 1024)
                                
                                # Reload from bytes
                                buffered.seek(0)
                                processed_chunk = Image.open(buffered)
                                
                                content.append(processed_chunk)
                                chunk_count += 1
                                processed_count += 1
                                
                                print(f"   ✂️ Split chunk {chunk_count}: y={current_y}-{end_y}, size={file_size_mb:.2f}MB")
                                
                                # Move to next chunk with overlap
                                if end_y == height:
                                    break
                                current_y += (chunk_height - overlap)
                                
                                # Safety limit for chunks per image
                                if chunk_count > 30:
                                    print(f"   ⚠️ Reached chunk limit (30) for image")
                                    break
                        else:
                            # Image is small enough, send as is with compression
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG", quality=85, optimize=True)
                            file_size_mb = len(buffered.getvalue()) / (1024 * 1024)
                            
                            # Reload from bytes
                            buffered.seek(0)
                            processed_img = Image.open(buffered)
                            
                            content.append(processed_img)
                            processed_count += 1
                            print(f"   📦 Image size: {file_size_mb:.2f}MB")
                        
                except Exception as e:
                    print(f"⚠️ Failed to process image {img_path}: {e}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
        
        print(f"   ✅ Successfully processed {processed_count} images")
        
        # Generate response
        response = model_instance.generate_content(content)
        
        print(f"📥 Gemini Response received:")
        print(f"   Model: {model}")
        print(f"   Finish reason: {response.finish_reason if hasattr(response, 'finish_reason') else 'N/A'}")
        
        result = response.text if response.text else None
        
        if not result:
            print(f"⚠️ Empty response details:")
            print(f"   Full response: {response}")
            
        return result if result else "Gemini returned empty response"

    def _analyze_images_with_openai(self, image_paths: List[str], prompt: str, model: str) -> str:
        """
        Analyze images using OpenAI API
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
                                    if total_chunks > 30: 
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
