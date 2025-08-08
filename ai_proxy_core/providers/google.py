"""
Google (Gemini) completions provider
"""
import os
import base64
import io
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import PIL.Image
from google import genai
from google.genai import types

from .base import BaseCompletions
from ..telemetry import get_telemetry

logger = logging.getLogger(__name__)


class GoogleCompletions(BaseCompletions):
    """Google Gemini completions handler"""
    
    # Model mapping for convenience
    MODEL_MAPPING = {
        "gemini-2.0-flash": "models/gemini-2.0-flash-exp",
        "gemini-1.5-flash": "models/gemini-1.5-flash",
        "gemini-1.5-pro": "models/gemini-1.5-pro",
        "gemini-pro": "models/gemini-pro",
        "gemini-pro-vision": "models/gemini-pro-vision"
    }
    
    def __init__(self, api_key: Optional[str] = None, use_secure_storage: bool = False):
        """
        Initialize Google Gemini client.
        
        Args:
            api_key: Optional API key. Falls back to GEMINI_API_KEY env var.
            use_secure_storage: Whether to use secure key storage if available.
        """
        self.use_secure_storage = use_secure_storage
        self.key_manager = None
        
        # TODO: Complete secure storage implementation
        # When security module is ready, this will:
        # 1. Import SecureKeyManager from ai_proxy_core.security
        # 2. Initialize with chosen storage backend (Vault, AWS Secrets, OS Keyring, etc.)
        # 3. Retrieve encrypted keys and decrypt only when needed
        # 4. Support key rotation without service restart
        # 
        # Example implementation:
        # if use_secure_storage:
        #     try:
        #         from ..security import SecureKeyManager, KeyProvider
        #         # Auto-detect best available provider
        #         provider = KeyProvider.VAULT if os.getenv("VAULT_URL") else KeyProvider.ENVIRONMENT
        #         self.key_manager = SecureKeyManager(provider=provider)
        #         api_key = await self.key_manager.get_api_key("gemini")
        #     except (ImportError, Exception) as e:
        #         logger.debug(f"Secure storage not available: {e}")
        
        # For now, just flag intent to use secure storage
        if use_secure_storage:
            logger.info("Secure storage requested but not yet implemented - using standard env vars")
            self.key_manager = None
        
        # Fall back to standard behavior - check both GEMINI_API_KEY and GOOGLE_API_KEY
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not provided")
        
        # Store key (encrypted if using secure storage)
        if self.key_manager:
            self.api_key = None  # Don't store in plain text
            self._encrypted_key = self.key_manager.encryption.encrypt_key(api_key)
        else:
            self.api_key = api_key
            
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
        self.telemetry = get_telemetry()
    
    def _parse_content(self, content: Union[str, List[Dict[str, Any]]]) -> List[Any]:
        """Parse message content into Gemini-compatible format"""
        if isinstance(content, str):
            return [content]
        
        parts = []
        for item in content:
            if item["type"] == "text":
                parts.append(item["text"])
            elif item["type"] == "image_url":
                # Handle base64 or URL images
                image_data = item["image_url"]["url"]
                if image_data.startswith("data:"):
                    # Extract base64 data
                    base64_data = image_data.split(",")[1]
                    image_bytes = base64.b64decode(base64_data)
                    image = PIL.Image.open(io.BytesIO(image_bytes))
                    parts.append(image)
                else:
                    # Handle URL
                    parts.append({"mime_type": "image/jpeg", "data": image_data})
        
        return parts
    
    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1000,
        response_format: Optional[Union[str, Dict[str, Any]]] = "text",
        system_instruction: Optional[str] = None,
        safety_settings: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a completion from messages"""
        
        # Debug logging
        print(f"DEBUG: GoogleCompletions received messages: {messages}")
        print(f"DEBUG: Message types: {[type(m) for m in messages]}")
        if messages:
            print(f"DEBUG: First message: {messages[0]}")
            print(f"DEBUG: First message keys: {list(messages[0].keys()) if isinstance(messages[0], dict) else 'Not a dict'}")
        
        try:
            # Track request start
            with self.telemetry.track_duration("completion", {"model": model, "provider": "google"}):
                # Convert messages to Gemini format - use simple string format
                # Extract just the text content from each message
                prompt_text = ""
                for msg in messages:
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        prompt_text += content + " "
                    else:
                        # For complex content, extract text parts
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    prompt_text += item.get("text", "") + " "
                
                # Use simple string prompt for google-genai
                contents = prompt_text.strip() if prompt_text.strip() else "Hello"
                
                # Configure generation
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    system_instruction=system_instruction
                )
                
                # Handle JSON response format
                if isinstance(response_format, dict) and response_format.get("type") == "json_object":
                    config.response_mime_type = "application/json"
                
                # Add safety settings if provided
                if safety_settings:
                    safety_config = []
                    for setting in safety_settings:
                        safety_config.append(types.SafetySetting(
                            category=setting.get("category"),
                            threshold=setting.get("threshold", "BLOCK_MEDIUM_AND_ABOVE")
                        ))
                    config.safety_settings = safety_config
                
                # Get model name
                model_name = self.MODEL_MAPPING.get(model, f"models/{model}")
                
                # Generate response
                response = await self.client.aio.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                
                # Extract response content
                response_content = ""
                try:
                    if hasattr(response, 'text') and response.text:
                        response_content = response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_content = part.text
                                    break
                except Exception as e:
                    logger.error(f"Error extracting response: {e}")
                    response_content = str(e)
                
                # Increment success counter
                self.telemetry.request_counter.add(
                    1, 
                    {"model": model, "status": "success", "provider": "google"}
                )
                
                # Return standardized response
                return {
                    "id": f"comp-{datetime.now().timestamp()}",
                    "created": int(datetime.now().timestamp()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": None  # Could be extracted if needed
                }
            
        except Exception as e:
            logger.error(f"Completion error: {e}")
            # Increment error counter
            self.telemetry.request_counter.add(
                1, 
                {"model": model, "status": "error", "provider": "google", "error_type": type(e).__name__}
            )
            raise
    
    def list_models(self) -> List[str]:
        """List available Gemini models"""
        return list(self.MODEL_MAPPING.keys())