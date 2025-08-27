"""
AI Proxy Core - Reusable AI service handlers
"""
from .completion_client import CompletionClient
from .gemini_live import GeminiLiveSession
from .models import ModelInfo, ModelProvider, ModelManager
from .providers import (
    GoogleCompletions,
    OpenAICompletions, 
    OllamaCompletions,
    BaseCompletions,
    OpenAIModelProvider,
    OllamaModelProvider,
    GeminiModelProvider
)
# Image generation providers
try:
    from .providers.openai_image import (
        OpenAIImageProvider,
        ImageModel,
        ImageSize,
        ImageQuality,
        ImageStyle
    )
except ImportError:
    # Image providers are optional
    pass

__version__ = "0.4.4"
__all__ = [
    # Unified completion interface
    "CompletionClient",
    
    # Current
    "GeminiLiveSession",
    
    # New provider-specific handlers
    "GoogleCompletions",
    "OpenAICompletions",
    "OllamaCompletions",
    "BaseCompletions",
    
    # Model management
    "ModelInfo",
    "ModelProvider", 
    "ModelManager",
    "OpenAIModelProvider",
    "OllamaModelProvider",
    "GeminiModelProvider",
    
    # Image generation (if available)
    "OpenAIImageProvider",
    "ImageModel",
    "ImageSize",
    "ImageQuality",
    "ImageStyle",
]
