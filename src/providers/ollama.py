"""
Ollama (local LLM) completions provider
"""
import os
import json
import logging
import time
from typing import Optional, List, Dict, Any

from .base import BaseCompletions
from ..telemetry import get_telemetry

logger = logging.getLogger(__name__)


class OllamaCompletions(BaseCompletions):
    """Ollama local LLM completions handler"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL. Falls back to OLLAMA_HOST env var or localhost:11434
        """
        try:
            import aiohttp
            self.aiohttp = aiohttp
        except ImportError:
            raise ImportError(
                "aiohttp library not installed. Install with: pip install aiohttp"
            )
        
        self.base_url = base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.telemetry = get_telemetry()
        self._available_models = None
    
    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "llama2",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
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
            base_attrs = {"model": model, "provider": "ollama"}
            base_attrs_with_client = {**base_attrs, **{k: v for k, v in client_attrs.items() if v}}
            with self.telemetry.track_duration("completion", base_attrs_with_client):
                
                # Build request payload
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                    }
                }
                
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
                
                # Add any additional options
                if "options" in kwargs:
                    payload["options"].update(kwargs["options"])
                
                # Make the API call
                async with self.aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Ollama API error: {response.status} - {error_text}")
                        
                        data = await response.json()
                
                self.telemetry.request_counter.add(
                    1, 
                    {**base_attrs_with_client, "status": "success"}
                )
                
                # Return standardized response
                return {
                    "id": f"ollama-{int(time.time()*1000)}",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": data.get("message", {}).get("content", "")
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    } if "eval_count" in data else None
                }
            
        except Exception as e:
            logger.error(f"Ollama completion error: {e}")
            self.telemetry.request_counter.add(
                1, 
                {**base_attrs_with_client, "status": "error", "error_type": type(e).__name__}
            )
            raise
    
    async def list_models_async(self) -> List[str]:
        """Fetch available models from Ollama server"""
        try:
            async with self.aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
                    else:
                        logger.warning(f"Could not fetch Ollama models: {response.status}")
                        return []
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            return []
    
    def list_models(self) -> List[str]:
        """List available Ollama models from the server"""
        import asyncio
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.list_models_async())
                    return future.result()
            except RuntimeError:
                # No running loop, we can use asyncio.run
                return asyncio.run(self.list_models_async())
        except Exception as e:
            logger.error(f"Failed to fetch models from Ollama: {e}")
            return []
