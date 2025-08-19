"""
OpenAI Image Generation Provider - Explicit model selection
Supports DALL-E 2, DALL-E 3, and GPT-Image-1
Part of ai-proxy-core v0.4.1
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
import base64
import os
import requests
import json

from .base import BaseCompletions


class ImageModel(str, Enum):
    """Available OpenAI image generation models"""
    DALLE_2 = "dall-e-2"
    DALLE_3 = "dall-e-3"
    GPT_IMAGE_1 = "gpt-image-1"


class ImageSize(str, Enum):
    """Supported image sizes by model"""
    # DALL-E 2 sizes
    SMALL = "256x256"      # DALL-E 2
    MEDIUM = "512x512"     # DALL-E 2
    LARGE = "1024x1024"    # DALL-E 2 & 3
    
    # DALL-E 3 sizes
    SQUARE = "1024x1024"
    LANDSCAPE = "1792x1024"
    PORTRAIT = "1024x1792"
    
    # GPT-Image-1 sizes
    GPT_SQUARE = "1024x1024"
    GPT_LANDSCAPE = "1536x1024"
    GPT_PORTRAIT = "1024x1536"
    GPT_HIGH_RES = "4096x4096"


class ImageQuality(str, Enum):
    """Image quality settings"""
    # DALL-E quality
    STANDARD = "standard"
    HD = "hd"
    
    # GPT-Image-1 quality
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AUTO = "auto"


class ImageStyle(str, Enum):
    """Generation style options (DALL-E 3 only)"""
    VIVID = "vivid"
    NATURAL = "natural"


class OpenAIImageProvider(BaseCompletions):
    """
    OpenAI Image Generation Provider
    Explicitly specify which model to use for each request
    """
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_completion(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        """Async completion for compatibility with base class"""
        raise NotImplementedError("Use generate() for image generation")
    
    def list_models(self):
        """List available image generation models"""
        return [
            {
                "id": ImageModel.DALLE_2.value,
                "capabilities": {
                    "sizes": ["256x256", "512x512", "1024x1024"],
                    "features": ["text-to-image", "edit", "variations"],
                    "max_prompt": 1000
                }
            },
            {
                "id": ImageModel.DALLE_3.value,
                "capabilities": {
                    "sizes": ["1024x1024", "1792x1024", "1024x1792"],
                    "features": ["text-to-image", "styles", "quality"],
                    "max_prompt": 4000
                }
            },
            {
                "id": ImageModel.GPT_IMAGE_1.value,
                "capabilities": {
                    "sizes": ["1024x1024", "1536x1024", "1024x1536", "4096x4096"],
                    "features": ["text-to-image", "image-to-image", "token-pricing"],
                    "max_prompt": "unlimited (token-based)"
                }
            }
        ]
    
    def generate(
        self,
        model: Union[str, ImageModel],
        prompt: str,
        size: Optional[Union[str, ImageSize]] = None,
        quality: Optional[Union[str, ImageQuality]] = None,
        style: Optional[Union[str, ImageStyle]] = None,
        n: int = 1,
        response_format: str = "url",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image with explicit model selection
        
        Args:
            model: REQUIRED - The model to use (dall-e-2, dall-e-3, or gpt-image-1)
            prompt: Text description for generation
            size: Image dimensions (model-specific)
            quality: Quality setting (model-specific)
            style: Style option (DALL-E 3 only)
            n: Number of images (DALL-E 2 supports 1-10, others only 1)
            response_format: "url" or "b64_json"
            
        Returns:
            Generated image(s) with metadata
        """
        # Convert string to enum if needed
        if isinstance(model, str):
            try:
                model = ImageModel(model)
            except ValueError:
                raise ValueError(f"Invalid model: {model}. Must be one of: {[m.value for m in ImageModel]}")
        
        # Validate parameters for specific models
        if model == ImageModel.DALLE_2:
            return self._generate_dalle2(prompt, size, n, response_format, **kwargs)
        elif model == ImageModel.DALLE_3:
            return self._generate_dalle3(prompt, size, quality, style, response_format, **kwargs)
        elif model == ImageModel.GPT_IMAGE_1:
            return self._generate_gpt_image_1(prompt, size, quality, response_format, **kwargs)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    def _generate_dalle2(
        self,
        prompt: str,
        size: Optional[Union[str, ImageSize]] = None,
        n: int = 1,
        response_format: str = "url",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with DALL-E 2"""
        endpoint = f"{self.base_url}/images/generations"
        
        # DALL-E 2 specific sizes
        valid_sizes = ["256x256", "512x512", "1024x1024"]
        size_value = size.value if hasattr(size, 'value') else (size or "1024x1024")
        
        if size_value not in valid_sizes:
            raise ValueError(f"DALL-E 2 only supports sizes: {valid_sizes}")
        
        payload = {
            "model": ImageModel.DALLE_2.value,
            "prompt": prompt[:1000],  # DALL-E 2 has 1000 char limit
            "size": size_value,
            "n": min(n, 10),  # DALL-E 2 supports up to 10 images
            "response_format": response_format
        }
        
        return self._make_request(endpoint, payload, ImageModel.DALLE_2)
    
    def _generate_dalle3(
        self,
        prompt: str,
        size: Optional[Union[str, ImageSize]] = None,
        quality: Optional[Union[str, ImageQuality]] = None,
        style: Optional[Union[str, ImageStyle]] = None,
        response_format: str = "url",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with DALL-E 3"""
        endpoint = f"{self.base_url}/images/generations"
        
        # DALL-E 3 specific sizes
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        size_value = size.value if hasattr(size, 'value') else (size or "1024x1024")
        
        if size_value not in valid_sizes:
            size_value = "1024x1024"  # Default to square
        
        # Map quality
        quality_value = quality.value if hasattr(quality, 'value') else (quality or "standard")
        if quality_value not in ["standard", "hd"]:
            quality_value = "standard"
        
        # Style
        style_value = style.value if hasattr(style, 'value') else (style or "vivid")
        
        payload = {
            "model": ImageModel.DALLE_3.value,
            "prompt": prompt[:4000],  # DALL-E 3 has 4000 char limit
            "size": size_value,
            "quality": quality_value,
            "style": style_value,
            "n": 1,  # DALL-E 3 only supports n=1
            "response_format": response_format
        }
        
        return self._make_request(endpoint, payload, ImageModel.DALLE_3)
    
    def _generate_gpt_image_1(
        self,
        prompt: str,
        size: Optional[Union[str, ImageSize]] = None,
        quality: Optional[Union[str, ImageQuality]] = None,
        response_format: str = "url",
        output_compression: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with GPT-Image-1"""
        endpoint = f"{self.base_url}/images/generations"
        
        # GPT-Image-1 specific sizes
        valid_sizes = ["1024x1024", "1536x1024", "1024x1536", "4096x4096"]
        size_value = size.value if hasattr(size, 'value') else (size or "1024x1024")
        
        if size_value not in valid_sizes:
            size_value = "1024x1024"  # Default to square
        
        # Quality for GPT-Image-1
        quality_value = quality.value if hasattr(quality, 'value') else (quality or "auto")
        if quality_value not in ["low", "medium", "high", "auto"]:
            quality_value = "auto"
        
        payload = {
            "model": ImageModel.GPT_IMAGE_1.value,
            "prompt": prompt,  # No char limit for GPT-Image-1
            "size": size_value,
            "quality": quality_value,
            "n": 1  # GPT-Image-1 only supports n=1
        }
        
        # GPT-Image-1 may not support response_format parameter
        # Only add if explicitly requested
        if response_format != "url" and "response_format" in kwargs:
            payload["response_format"] = response_format
        
        if output_compression is not None:
            payload["output_compression"] = output_compression
        
        # Add any additional kwargs specific to GPT-Image-1
        payload.update(kwargs)
        
        return self._make_request(endpoint, payload, ImageModel.GPT_IMAGE_1)
    
    def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        model: ImageModel
    ) -> Dict[str, Any]:
        """Make API request and process response"""
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Process response based on format
            images = []
            for img_data in data['data']:
                if "url" in img_data:
                    # Download image from URL
                    img_response = requests.get(img_data['url'])
                    img_response.raise_for_status()
                    image_bytes = img_response.content
                    images.append({
                        "data": image_bytes,
                        "url": img_data['url'],
                        "revised_prompt": img_data.get('revised_prompt')
                    })
                else:
                    # Base64 encoded image
                    image_bytes = base64.b64decode(img_data['b64_json'])
                    images.append({
                        "data": image_bytes,
                        "b64_json": img_data['b64_json'],
                        "revised_prompt": img_data.get('revised_prompt')
                    })
            
            # Return single image if n=1, otherwise return list
            result = {
                "model": model.value,
                "created": data.get('created'),
                "images": images[0] if len(images) == 1 else images,
                "usage": data.get('usage'),  # GPT-Image-1 returns token usage
                "c2pa_metadata": {
                    "claim_generator": f"OpenAI {model.value}",
                    "timestamp": data.get('created'),
                    "is_ai_generated": True
                }
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                error_data = e.response.json() if e.response.content else {}
                raise Exception(f"OpenAI API error ({model.value}): {e.response.status_code} - {error_data.get('error', {}).get('message', str(e))}")
            raise Exception(f"OpenAI API error ({model.value}): {str(e)}")
    
    def edit(
        self,
        image: Union[str, bytes],
        prompt: str,
        mask: Optional[Union[str, bytes]] = None,
        model: ImageModel = ImageModel.DALLE_2,
        size: Optional[str] = None,
        n: int = 1,
        response_format: str = "url"
    ) -> Dict[str, Any]:
        """
        Edit an existing image (DALL-E 2 only)
        
        Args:
            image: Original image (base64 or bytes)
            prompt: Edit instructions
            mask: Optional mask for inpainting
            model: Currently only DALL-E 2 supports edits
            size: Output size
            n: Number of variations
            
        Returns:
            Edited image(s)
        """
        if model != ImageModel.DALLE_2:
            raise ValueError("Only DALL-E 2 supports image editing")
        
        endpoint = f"{self.base_url}/images/edits"
        
        # Prepare files for multipart upload
        files = {
            "model": (None, model.value),
            "image": ("image.png", image if isinstance(image, bytes) else base64.b64decode(image), "image/png"),
            "prompt": (None, prompt),
            "n": (None, str(n)),
        }
        
        if size:
            files["size"] = (None, size)
        
        if mask:
            files["mask"] = ("mask.png", mask if isinstance(mask, bytes) else base64.b64decode(mask), "image/png")
        
        if response_format:
            files["response_format"] = (None, response_format)
        
        # For multipart, only auth header
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = requests.post(endpoint, headers=headers, files=files)
            response.raise_for_status()
            
            data = response.json()
            return self._process_response(data, model)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI edit error: {str(e)}")
    
    def _process_response(self, data: Dict, model: ImageModel) -> Dict[str, Any]:
        """Process API response consistently"""
        images = []
        for img_data in data['data']:
            if "url" in img_data:
                img_response = requests.get(img_data['url'])
                img_response.raise_for_status()
                images.append({
                    "data": img_response.content,
                    "url": img_data['url']
                })
            else:
                images.append({
                    "data": base64.b64decode(img_data['b64_json']),
                    "b64_json": img_data['b64_json']
                })
        
        return {
            "model": model.value,
            "created": data.get('created'),
            "images": images[0] if len(images) == 1 else images
        }