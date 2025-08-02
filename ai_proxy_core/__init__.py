"""
AI Proxy Core - Reusable AI service handlers
"""
from .completions import CompletionsHandler
from .gemini_live import GeminiLiveSession

__version__ = "0.1.7"
__all__ = ["CompletionsHandler", "GeminiLiveSession"]