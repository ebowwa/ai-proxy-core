"""
Base provider class for all AI providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseCompletions(ABC):
    """Base class for all completion providers"""
    
    @abstractmethod
    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a completion from messages.
        
        All providers must return a standardized response format:
        {
            "id": str,
            "created": int,
            "model": str,
            "choices": [{
                "index": int,
                "message": {"role": str, "content": str},
                "finish_reason": str
            }],
            "usage": {
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int
            } or None
        }
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models for this provider"""
        pass