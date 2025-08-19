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
from .providers.gpt4o_image import (
    GPT4oImageProvider,
    AzureGPT4oImageProvider,
    ImageSize,
    ImageQuality,
    ImageStyle
)

__version__ = "0.4.0"
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
    
    # Image generation
    "GPT4oImageProvider",
    "AzureGPT4oImageProvider",
    "ImageSize",
    "ImageQuality",
    "ImageStyle",
]
