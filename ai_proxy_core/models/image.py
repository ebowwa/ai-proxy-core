"""
Abstract image generation models for ai-proxy-core
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


@dataclass
class ImageGenerationRequest:
    """Abstract request model for image generation"""
    prompt: str
    provider: str = "openai"
    model: str = "gpt-4o"
    size: Optional[str] = None
    quality: Optional[str] = None
    style: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_provider_format(self, provider: str) -> Dict[str, Any]:
        """Convert to provider-specific format"""
        if provider == "openai":
            return self._to_openai_format()
        elif provider == "azure":
            return self._to_azure_format()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI format"""
        return {
            "prompt": self.prompt,
            "size": self.size,
            "quality": self.quality,
            "style": self.style,
            "context": self.context
        }
    
    def _to_azure_format(self) -> Dict[str, Any]:
        """Convert to Azure format"""
        base = self._to_openai_format()
        base.update(self.metadata.get("azure", {}))
        return base


@dataclass
class ImageEditRequest:
    """Abstract request model for image editing"""
    image: Union[str, bytes]
    prompt: str
    mask: Optional[Union[str, bytes]] = None
    provider: str = "openai"
    model: str = "gpt-4o"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageGenerationResponse:
    """Abstract response model for image generation"""
    image_data: bytes
    image_url: Optional[str] = None
    provider: str = "openai"
    model: str = "gpt-4o"
    size: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    c2pa_metadata: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_ai_generated(self) -> bool:
        """Check if image is AI-generated based on C2PA metadata"""
        return self.c2pa_metadata is not None
    
    @property
    def generator_info(self) -> Optional[str]:
        """Get generator information from C2PA"""
        if self.c2pa_metadata:
            return self.c2pa_metadata.get("claim_generator")
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "image_url": self.image_url,
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "is_ai_generated": self.is_ai_generated,
            "generator_info": self.generator_info,
            "metadata": self.metadata
        }


@dataclass
class BatchImageRequest:
    """Request for batch image generation"""
    requests: List[ImageGenerationRequest]
    parallel: bool = True
    max_concurrent: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalizationConfig:
    """Configuration for image localization"""
    base_prompt: str
    locales: Dict[str, str]  # locale -> localized prompt
    cultural_adaptations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    size_variants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)