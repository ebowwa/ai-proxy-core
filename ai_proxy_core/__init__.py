"""
AI Proxy Core - Reusable AI service handlers
"""
from .completions import CompletionsHandler  # Keeping for backward compatibility warning
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

__version__ = "0.2.0"
__all__ = [
    # Legacy (will deprecate)
    "CompletionsHandler",
    
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
]