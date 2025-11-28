import os
import base64
from typing import List, Dict, Optional
from openai import OpenAI

class AIAnalysisService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def analyze_reviews(self, review_text: str, prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Analyze product reviews using OpenAI API.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes product reviews."},
                    {"role": "user", "content": f"{prompt}\n\nReviews:\n{review_text}"}
                ],
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing reviews: {str(e)}"

    def analyze_images(self, image_paths: List[str], prompt: str, model: str = "gpt-4o-mini") -> str:
        """
        Analyze product images using OpenAI API.
        """
        try:
            content = [{"type": "text", "text": prompt}]
            
            for img_path in image_paths[:5]:  # Limit to 5 images to avoid token limits/costs
                if os.path.exists(img_path):
                    with open(img_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        })

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes product images."},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing images: {str(e)}"
