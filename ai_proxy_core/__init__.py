"""
AI Proxy Core - Reusable AI service handlers
"""
from .completions import CompletionsHandler  # Keeping for backward compatibility warning
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

__version__ = "0.3.0"
__all__ = [
    # Legacy (will deprecate)
    "CompletionsHandler",
    
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
]