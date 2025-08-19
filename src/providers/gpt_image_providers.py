"""
OpenAI Image Generation Providers - Modular support for multiple models
Supports both DALL-E 3 and GPT-Image-1
Part of ai-proxy-core v0.4.1
"""

from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
from enum import Enum
import base64
import os
import requests
import json

from .base import BaseCompletions


class ImageModel(str, Enum):
    """Available image generation models"""
    DALLE_2 = "dall-e-2"
    DALLE_3 = "dall-e-3"
    GPT_IMAGE_1 = "gpt-image-1"  # Available April 2025+


class ImageSize(str, Enum):
    """Supported image sizes"""
    # DALL-E sizes
    SQUARE = "1024x1024"
    LANDSCAPE = "1792x1024"  # DALL-E 3 only
    PORTRAIT = "1024x1792"   # DALL-E 3 only
    
    # GPT-Image-1 sizes
    GPT_SQUARE = "1024x1024"
    GPT_LANDSCAPE = "1536x1024"
    GPT_PORTRAIT = "1024x1536"
    
    # High-res (GPT-Image-1)
    HIGH_RES = "4096x4096"


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
    """Generation style options"""
    VIVID = "vivid"
    NATURAL = "natural"


class BaseImageProvider(BaseCompletions):
    """Base class for all image generation providers"""
    
    def __init__(self, api_key: str, model: ImageModel = ImageModel.DALLE_3, **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_completion(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        """Async completion for compatibility with base class"""
        raise NotImplementedError("Use generate() for image generation")
    
    def list_models(self):
        """List available models"""
        return [model.value for model in ImageModel]
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image - must be implemented by subclasses"""
        pass


class DALLE3Provider(BaseImageProvider):
    """
    DALL-E 3 Image Generation Provider
    Current production model for OpenAI image generation
    """
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, model=ImageModel.DALLE_3, **kwargs)
    
    def generate(
        self,
        prompt: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        style: Optional[ImageStyle] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3
        
        Args:
            prompt: Text description for generation
            size: SQUARE, LANDSCAPE, or PORTRAIT
            quality: STANDARD or HD
            style: VIVID or NATURAL
            
        Returns:
            Generated image with metadata
        """
        endpoint = f"{self.base_url}/images/generations"
        
        # Map quality if using GPT-Image-1 quality values
        dalle_quality = quality or ImageQuality.STANDARD
        if quality in [ImageQuality.LOW, ImageQuality.MEDIUM]:
            dalle_quality = ImageQuality.STANDARD
        elif quality in [ImageQuality.HIGH, ImageQuality.AUTO]:
            dalle_quality = ImageQuality.HD
        
        payload = {
            "model": self.model.value,
            "prompt": prompt,
            "size": (size or ImageSize.SQUARE).value,
            "quality": dalle_quality.value,
            "style": (style or ImageStyle.VIVID).value,
            "n": 1,
            "response_format": kwargs.get("response_format", "url")
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            image_url = data['data'][0]['url']
            
            # Download the image
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_data = image_response.content
            
            return {
                "image": image_data,
                "url": image_url,
                "revised_prompt": data['data'][0].get('revised_prompt'),
                "model": self.model.value,
                "c2pa_metadata": {
                    "claim_generator": f"OpenAI {self.model.value}",
                    "timestamp": data.get('created'),
                    "is_ai_generated": True
                }
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class GPTImage1Provider(BaseImageProvider):
    """
    GPT-Image-1 Provider
    Next-gen multimodal image generation (Available April 2025+)
    Features higher resolution, better instruction following, and token-based pricing
    """
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, model=ImageModel.GPT_IMAGE_1, **kwargs)
    
    def generate(
        self,
        prompt: str,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        output_compression: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image using GPT-Image-1
        
        Args:
            prompt: Detailed text description with instructions
            size: "1024x1024", "1536x1024", "1024x1536", or "4096x4096"
            quality: "low", "medium", "high", or "auto"
            output_compression: 0-100 (percentage)
            
        Returns:
            Generated image with metadata
        """
        endpoint = f"{self.base_url}/images/generations"
        
        # Use GPT-Image-1 specific sizes
        if size == ImageSize.LANDSCAPE:
            size = ImageSize.GPT_LANDSCAPE
        elif size == ImageSize.PORTRAIT:
            size = ImageSize.GPT_PORTRAIT
        
        payload = {
            "model": self.model.value,
            "prompt": prompt,
            "size": (size or ImageSize.GPT_SQUARE).value,
            "quality": (quality or ImageQuality.AUTO).value,
        }
        
        if output_compression is not None:
            payload["output_compression"] = output_compression
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle response format
            if "url" in data['data'][0]:
                image_url = data['data'][0]['url']
                # Download the image
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image_data = image_response.content
            else:
                # Base64 response
                image_data = base64.b64decode(data['data'][0]['b64_json'])
                image_url = None
            
            return {
                "image": image_data,
                "url": image_url,
                "model": self.model.value,
                "size": payload["size"],
                "quality": payload["quality"],
                "token_usage": data.get("usage"),  # GPT-Image-1 returns token usage
                "c2pa_metadata": {
                    "claim_generator": "OpenAI gpt-image-1",
                    "timestamp": data.get('created'),
                    "is_ai_generated": True
                }
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"GPT-Image-1 API error: {str(e)}")
    
    def generate_from_image(
        self,
        image: Union[str, bytes],
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate new image from existing image (image-to-image)
        GPT-Image-1 specific feature
        
        Args:
            image: Source image (base64 or bytes)
            prompt: Transformation instructions
            
        Returns:
            Generated image
        """
        if isinstance(image, bytes):
            image = base64.b64encode(image).decode('utf-8')
        
        # Build multimodal request
        endpoint = f"{self.base_url}/images/generations"
        
        payload = {
            "model": self.model.value,
            "prompt": prompt,
            "image": image,
            **kwargs
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return self._process_response(response.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"GPT-Image-1 image-to-image error: {str(e)}")
    
    def _process_response(self, data: Dict) -> Dict[str, Any]:
        """Process API response"""
        if "url" in data['data'][0]:
            image_url = data['data'][0]['url']
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_data = image_response.content
        else:
            image_data = base64.b64decode(data['data'][0]['b64_json'])
            image_url = None
        
        return {
            "image": image_data,
            "url": image_url,
            "model": self.model.value,
            "token_usage": data.get("usage"),
            "c2pa_metadata": {
                "claim_generator": "OpenAI gpt-image-1",
                "timestamp": data.get('created'),
                "is_ai_generated": True
            }
        }


class UnifiedImageProvider(BaseImageProvider):
    """
    Unified provider that automatically selects the best model
    Falls back gracefully from GPT-Image-1 to DALL-E 3
    """
    
    def __init__(self, api_key: str, prefer_model: Optional[ImageModel] = None, **kwargs):
        super().__init__(api_key, model=prefer_model or ImageModel.GPT_IMAGE_1, **kwargs)
        self._providers = {
            ImageModel.DALLE_3: DALLE3Provider(api_key, **kwargs),
            ImageModel.DALLE_2: DALLE3Provider(api_key, **kwargs),  # Use DALLE3Provider for DALLE2
            ImageModel.GPT_IMAGE_1: GPTImage1Provider(api_key, **kwargs)
        }
    
    def generate(self, prompt: str, model: Optional[ImageModel] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate image with automatic model selection
        
        Args:
            prompt: Image description
            model: Optional specific model to use
            **kwargs: Model-specific parameters
            
        Returns:
            Generated image with metadata
        """
        # Select model
        selected_model = model or self.model
        
        # Try primary model first
        try:
            provider = self._providers.get(selected_model)
            if provider:
                result = provider.generate(prompt, **kwargs)
                result["provider"] = selected_model.value
                return result
        except Exception as e:
            print(f"Warning: {selected_model.value} failed: {e}")
            
            # Fallback to DALL-E 3
            if selected_model == ImageModel.GPT_IMAGE_1:
                print("Falling back to DALL-E 3...")
                provider = self._providers[ImageModel.DALLE_3]
                result = provider.generate(prompt, **kwargs)
                result["provider"] = ImageModel.DALLE_3.value
                result["fallback"] = True
                return result
            
            raise
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models with their capabilities"""
        return [
            {
                "model": ImageModel.DALLE_3.value,
                "status": "available",
                "max_size": "1792x1024",
                "features": ["text-to-image", "styles", "quality-settings"]
            },
            {
                "model": ImageModel.GPT_IMAGE_1.value,
                "status": "available (April 2025+)",
                "max_size": "4096x4096",
                "features": ["text-to-image", "image-to-image", "token-pricing", "better-instructions"]
            }
        ]


# Backwards compatibility
GPT4oImageProvider = UnifiedImageProvider  # Alias for backwards compatibility
AzureGPT4oImageProvider = UnifiedImageProvider  # Can be extended for Azure-specific features