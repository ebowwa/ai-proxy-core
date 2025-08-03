"""
AI Proxy Core - Reusable AI service handlers
"""
from .completions import CompletionsHandler  # Keeping for backward compatibility warning
from .gemini_live import GeminiLiveSession
from .providers import (
    GoogleCompletions,
    OpenAICompletions, 
    OllamaCompletions,
    BaseCompletions
)

__version__ = "0.1.9"
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
]