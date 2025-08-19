"""
ai-proxy-core v0.4.0
Abstract AI provider wrapper with unified interface
"""

__version__ = "0.4.0"

# Core providers
from .providers.openai.gpt4o_image import (
    GPT4oImageProvider,
    AzureGPT4oImageProvider,
    ImageSize,
    ImageQuality,
    ImageStyle
)

# Abstract models
from .models.image import (
    ImageGenerationRequest,
    ImageEditRequest,
    ImageGenerationResponse,
    BatchImageRequest,
    LocalizationConfig
)

# Base classes
from .base import BaseProvider, ProviderRegistry

# Utilities
from .utils import encode_image, decode_response

__all__ = [
    # Version
    "__version__",
    
    # Providers
    "GPT4oImageProvider",
    "AzureGPT4oImageProvider",
    
    # Enums
    "ImageSize",
    "ImageQuality", 
    "ImageStyle",
    
    # Models
    "ImageGenerationRequest",
    "ImageEditRequest",
    "ImageGenerationResponse",
    "BatchImageRequest",
    "LocalizationConfig",
    
    # Base
    "BaseProvider",
    "ProviderRegistry",
    
    # Utils
    "encode_image",
    "decode_response"
]