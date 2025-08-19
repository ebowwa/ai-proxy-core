"""
GPT-4o Native Image Generation Provider
Abstract wrapper for OpenAI's GPT-4o image generation capabilities
Part of ai-proxy-core v0.4.0
"""

from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
from enum import Enum
import base64
import os
import requests
import json

from .base import BaseCompletions


class ImageSize(str, Enum):
    """Supported image sizes for GPT-4o generation"""
    SQUARE = "1024x1024"
    LANDSCAPE = "1792x1024"
    PORTRAIT = "1024x1792"


class ImageQuality(str, Enum):
    """Image quality settings"""
    STANDARD = "standard"
    HD = "hd"


class ImageStyle(str, Enum):
    """Generation style options"""
    VIVID = "vivid"
    NATURAL = "natural"


class GPT4oImageProvider(BaseCompletions):
    """
    Abstract provider for GPT-4o native image generation
    
    Note: As of 2025, GPT-4o doesn't directly generate images.
    This implementation uses DALL-E 3 as the underlying engine,
    providing an abstract interface for future GPT-4o capabilities.
    """
    
    model_name = "gpt-4o"
    supports_streaming = True
    supports_context = True
    supports_editing = True
    
    async def create_completion(self, messages, model, temperature=0.7, max_tokens=None, **kwargs):
        """Async completion for compatibility with base class"""
        # This is an image provider, not a text completion provider
        raise NotImplementedError("Use generate() for image generation")
    
    def list_models(self):
        """List available models"""
        return ["dall-e-3", "dall-e-2"]  # Actual available models
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def generate(
        self,
        prompt: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        style: Optional[ImageStyle] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate image using OpenAI's image generation API
        
        Args:
            prompt: Text description for generation
            size: Image dimensions
            quality: Standard or HD
            style: Vivid or Natural
            context: Additional context (images, chat history)
            
        Returns:
            Generated image with metadata
        """
        endpoint = f"{self.base_url}/images/generations"
        
        payload = {
            "model": "dall-e-3",  # Using DALL-E 3
            "prompt": prompt,
            "size": (size or ImageSize.SQUARE).value,
            "quality": (quality or ImageQuality.STANDARD).value,
            "style": (style or ImageStyle.VIVID).value,
            "n": 1,
            "response_format": "url"  # or "b64_json" for base64
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
                "c2pa_metadata": {
                    "claim_generator": "OpenAI DALL-E 3",
                    "timestamp": data.get('created'),
                    "is_ai_generated": True
                }
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def edit(
        self,
        image: Union[str, bytes],
        prompt: str,
        mask: Optional[Union[str, bytes]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Edit existing image using OpenAI's edit API
        
        Args:
            image: Original image (base64 or bytes)
            prompt: Edit instructions
            mask: Optional mask for inpainting
            
        Returns:
            Edited image with metadata
        """
        endpoint = f"{self.base_url}/images/edits"
        
        # Prepare files for multipart upload
        files = {
            "model": (None, "dall-e-2"),  # Only DALL-E 2 supports edits
            "image": ("image.png", image if isinstance(image, bytes) else base64.b64decode(image), "image/png"),
            "prompt": (None, prompt),
            "n": (None, "1"),
            "size": (None, kwargs.get("size", "1024x1024"))
        }
        
        if mask:
            files["mask"] = ("mask.png", mask if isinstance(mask, bytes) else base64.b64decode(mask), "image/png")
        
        # For multipart, we only need auth header
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = requests.post(endpoint, headers=headers, files=files)
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
                "c2pa_metadata": {
                    "claim_generator": "OpenAI DALL-E 2 Edit",
                    "timestamp": data.get('created'),
                    "is_ai_generated": True
                }
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def transform(
        self,
        image: Union[str, bytes],
        transformation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply transformation to image
        
        Args:
            image: Source image
            transformation: Transformation description
            
        Returns:
            Transformed image
        """
        return self.edit(
            image=image,
            prompt=f"Transform this image: {transformation}",
            **kwargs
        )
    
    def _build_request(
        self,
        prompt: str,
        size: ImageSize,
        quality: ImageQuality,
        style: ImageStyle,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build image generation request"""
        
        messages = []
        
        # Add context from previous messages if provided
        if context and "messages" in context:
            messages.extend(context["messages"])
        
        # Build content array
        content = [{"type": "text", "text": prompt}]
        
        # Add context images if provided
        if context and "images" in context:
            for img in context["images"]:
                if isinstance(img, bytes):
                    img = base64.b64encode(img).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img}"}
                })
        
        messages.append({"role": "user", "content": content})
        
        return {
            "model": self.model_name,
            "messages": messages,
            "image_generation": {
                "enabled": True,
                "size": size.value,
                "quality": quality.value,
                "style": style.value,
                "n": 1
            },
            **kwargs
        }
    
    def _build_edit_request(
        self,
        image: Union[str, bytes],
        prompt: str,
        mask: Optional[Union[str, bytes]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build image edit request"""
        
        if isinstance(image, bytes):
            image = base64.b64encode(image).decode('utf-8')
        
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"}
            }
        ]
        
        if mask:
            if isinstance(mask, bytes):
                mask = base64.b64encode(mask).decode('utf-8')
            content.append({
                "type": "image_mask",
                "image_mask": {"url": f"data:image/png;base64,{mask}"}
            })
        
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content}],
            "image_generation": {
                "enabled": True,
                "mode": "edit"
            },
            **kwargs
        }
    
    def extract_c2pa_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract C2PA (Content Authenticity) metadata
        
        Returns:
            C2PA metadata including generator info and signature
        """
        c2pa = response.get("c2pa_metadata", {})
        
        return {
            "is_ai_generated": c2pa.get("is_ai_generated", True),
            "generator": c2pa.get("claim_generator", "OpenAI"),
            "generator_version": c2pa.get("claim_generator_info", {}).get("version", "2025-01"),
            "timestamp": c2pa.get("timestamp"),
            "signature": c2pa.get("signature"),
            "content_credentials": c2pa.get("content_credentials", [])
        }


class AzureGPT4oImageProvider(GPT4oImageProvider):
    """
    Azure-specific implementation with additional features
    """
    
    model_name = "dall-e-3"
    
    def __init__(
        self,
        api_key: str,
        resource_name: str,
        deployment_name: str = "dall-e-3",
        api_version: str = "2024-02-01",
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.resource_name = resource_name
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.base_url = f"https://{resource_name}.openai.azure.com/openai/deployments/{deployment_name}"
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Azure-specific generation endpoint"""
        endpoint = f"{self.base_url}/images/generations?api-version={self.api_version}"
        
        payload = {
            "prompt": prompt,
            "size": kwargs.get("size", ImageSize.SQUARE).value if isinstance(kwargs.get("size"), ImageSize) else kwargs.get("size", "1024x1024"),
            "quality": kwargs.get("quality", ImageQuality.STANDARD).value if isinstance(kwargs.get("quality"), ImageQuality) else kwargs.get("quality", "standard"),
            "style": kwargs.get("style", ImageStyle.VIVID).value if isinstance(kwargs.get("style"), ImageStyle) else kwargs.get("style", "vivid"),
            "n": 1
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
                "c2pa_metadata": {
                    "claim_generator": f"Azure OpenAI {self.deployment_name}",
                    "timestamp": data.get('created'),
                    "is_ai_generated": True
                }
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Azure OpenAI API error: {str(e)}")