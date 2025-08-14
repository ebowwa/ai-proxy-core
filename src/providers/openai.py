"""
OpenAI completions provider
"""
import os
import logging
import time
from typing import Optional, List, Dict, Any

from .base import BaseCompletions
from ..telemetry import get_telemetry

logger = logging.getLogger(__name__)


class OpenAICompletions(BaseCompletions):
    """OpenAI completions handler"""
    
    AVAILABLE_MODELS = [
        "gpt-4-turbo-preview",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, use_secure_storage: bool = False):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: Optional API key. Falls back to OPENAI_API_KEY env var.
            base_url: Optional base URL for OpenAI-compatible endpoints (e.g., Groq, Anyscale)
            use_secure_storage: Whether to use secure key storage if available.
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install ai-proxy-core[openai] "
                "or pip install openai"
            )
        
        self.use_secure_storage = use_secure_storage
        self.key_manager = None
        
        # TODO: Complete secure storage implementation (same as GoogleCompletions)
        # See google.py for detailed implementation comments
        if use_secure_storage:
            logger.info("Secure storage requested but not yet implemented - using standard env vars")
            self.key_manager = None
        
        # Fall back to standard behavior
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not provided")
        
        # Store key (encrypted if using secure storage)
        if self.key_manager:
            self.api_key = None  # Don't store in plain text
            self._encrypted_key = self.key_manager.encryption.encrypt_key(api_key)
        else:
            self.api_key = api_key
        
        # Support custom endpoints (OpenAI-compatible APIs)
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.telemetry = get_telemetry()
    
    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a completion from messages"""
        
        try:
            client_ctx = kwargs.get("client_context") or {}
            client_attrs = {
                "client.app": client_ctx.get("app"),
                "client.device": client_ctx.get("device"),
                "client.id": client_ctx.get("client_id"),
                "client.ip": client_ctx.get("ip"),
            }
            base_attrs = {"model": model, "provider": "openai"}
            base_attrs_with_client = {**base_attrs, **{k: v for k, v in client_attrs.items() if v}}
            with self.telemetry.track_duration("completion", base_attrs_with_client):
                # Build request parameters
                params = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }
                
                if max_tokens:
                    params["max_tokens"] = max_tokens
                
                if response_format:
                    params["response_format"] = response_format
                
                if tools:
                    params["tools"] = tools
                    if tool_choice:
                        params["tool_choice"] = tool_choice
                
                # Add any additional kwargs
                params.update(kwargs)
                
                # Make the API call
                response = await self.client.chat.completions.create(**params)
                
                self.telemetry.request_counter.add(
                    1, 
                    {**base_attrs_with_client, "status": "success"}
                )
                
                # Return standardized response
                return {
                    "id": response.id,
                    "created": response.created,
                    "model": response.model,
                    "choices": [{
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content,
                            "tool_calls": choice.message.tool_calls if hasattr(choice.message, 'tool_calls') else None
                        },
                        "finish_reason": choice.finish_reason
                    } for choice in response.choices],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    } if response.usage else None
                }
            
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            self.telemetry.request_counter.add(
                1, 
                {**base_attrs_with_client, "status": "error", "error_type": type(e).__name__}
            )
            raise
    
    def list_models(self) -> List[str]:
        """List available OpenAI models"""
        return self.AVAILABLE_MODELS
