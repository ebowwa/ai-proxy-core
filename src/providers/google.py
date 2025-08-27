"""
Google (Gemini) completions provider
"""
import os
import base64
import io
import logging
import mimetypes
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
        "gemini-pro-vision": "models/gemini-pro-vision",
        "gemini-2.5-flash-image-preview": "models/gemini-2.5-flash-image-preview",
        "gemini-2.5-flash-image": "models/gemini-2.5-flash-image-preview",
        "g2.5-flash-image": "models/gemini-2.5-flash-image-preview",
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
        if isinstance(content, str):
            return [content]
        
        parts = []
        for item in content:
            t = item.get("type")
            if t == "text":
                parts.append(item.get("text", ""))
            elif t == "image_url":
                image_data = item.get("image_url", {}).get("url")
                if not image_data:
                    continue
                if isinstance(image_data, str) and image_data.startswith("data:"):
                    header, base64_data = image_data.split(",", 1)
                    image_bytes = base64.b64decode(base64_data)
                    image = PIL.Image.open(io.BytesIO(image_bytes))
                    parts.append(image)
                else:
                    parts.append({"mime_type": "image/jpeg", "data": image_data})
            elif t == "audio_url":
                audio_data = item.get("audio_url", {}).get("url")
                if not audio_data or not isinstance(audio_data, str):
                    continue
                if audio_data.startswith("data:"):
                    header, base64_data = audio_data.split(",", 1)
                    mime = "audio/mp3"
                    try:
                        mime = header.split("data:")[1].split(";")[0] or "audio/mp3"
                    except Exception:
                        pass
                    audio_bytes = base64.b64decode(base64_data)
                    parts.append({"mime_type": mime, "data": audio_bytes})
            elif t == "input_audio":
                audio_obj = item.get("input_audio", {}) if "input_audio" in item else item
                base64_payload = audio_obj.get("data") or audio_obj.get("base64")
                fmt = audio_obj.get("format")
                if not base64_payload:
                    continue
                mime = None
                if fmt:
                    f = str(fmt).lower()
                    if f in ("wav", "pcm"):
                        mime = "audio/wav" if f == "wav" else "audio/pcm"
                    elif f in ("mp3", "mpeg"):
                        mime = "audio/mpeg"
                    elif f in ("aac",):
                        mime = "audio/aac"
                    elif f in ("ogg", "vorbis", "oga"):
                        mime = "audio/ogg"
                    elif f in ("flac",):
                        mime = "audio/flac"
                if not mime:
                    mime = "audio/mpeg"
                try:
                    audio_bytes = base64.b64decode(base64_payload)
                except Exception:
                    continue
                parts.append({"mime_type": mime, "data": audio_bytes})
            elif t == "pdf":
                pdf_data = item.get("pdf", {})
                if "data" in pdf_data:
                    if isinstance(pdf_data["data"], str) and pdf_data["data"].startswith("data:"):
                        header, base64_data = pdf_data["data"].split(",", 1)
                        pdf_bytes = base64.b64decode(base64_data)
                    else:
                        pdf_bytes = base64.b64decode(pdf_data["data"])
                    parts.append({"mime_type": "application/pdf", "data": pdf_bytes})
                elif "file_path" in pdf_data:
                    file_path = pdf_data["file_path"]
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            pdf_bytes = f.read()
                        parts.append({"mime_type": "application/pdf", "data": pdf_bytes})
            elif t == "video":
                video_data = item.get("video", {})
                if "data" in video_data:
                    if isinstance(video_data["data"], str) and video_data["data"].startswith("data:"):
                        header, base64_data = video_data["data"].split(",", 1)
                        mime_type = header.split("data:")[1].split(";")[0] or "video/mp4"
                        video_bytes = base64.b64decode(base64_data)
                    else:
                        video_bytes = base64.b64decode(video_data["data"])
                        mime_type = video_data.get("mime_type", "video/mp4")
                    
                    parts.append({"mime_type": mime_type, "data": video_bytes})
                elif "file_path" in video_data:
                    file_path = video_data["file_path"]
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            video_bytes = f.read()
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if not mime_type or not mime_type.startswith("video/"):
                            mime_type = "video/mp4"
                        parts.append({"mime_type": mime_type, "data": video_bytes})
            elif t == "document":
                doc_data = item.get("document", {})
                if "data" in doc_data:
                    if isinstance(doc_data["data"], str) and doc_data["data"].startswith("data:"):
                        header, base64_data = doc_data["data"].split(",", 1)
                        doc_bytes = base64.b64decode(base64_data)
                        mime_type = header.split("data:")[1].split(";")[0]
                    else:
                        doc_bytes = base64.b64decode(doc_data["data"])
                        mime_type = doc_data.get("mime_type", "text/plain")
                    parts.append({"mime_type": mime_type, "data": doc_bytes})
                elif "file_path" in doc_data:
                    file_path = doc_data["file_path"]
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if not mime_type:
                            mime_type = "text/plain"
                        with open(file_path, 'rb') as f:
                            doc_bytes = f.read()
                        parts.append({"mime_type": mime_type, "data": doc_bytes})
        
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
        
        logger.debug(f"GoogleCompletions received messages (count={len(messages)})")
        try:
            client_ctx = kwargs.get("client_context") or {}
            client_attrs = {
                "client.app": client_ctx.get("app"),
                "client.device": client_ctx.get("device"),
                "client.id": client_ctx.get("client_id"),
                "client.ip": client_ctx.get("ip"),
            }
            base_attrs = {"model": model, "provider": "google"}
            base_attrs_with_client = {**base_attrs, **{k: v for k, v in client_attrs.items() if v}}
            with self.telemetry.track_duration("completion", base_attrs_with_client):
                contents_parts: List[Any] = []
                for msg in messages:
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        contents_parts.append(content)
                    elif isinstance(content, list):
                        contents_parts.extend(self._parse_content(content))
                contents = contents_parts if contents_parts else "Hello"
                
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
                
                def _is_image_part(p):
                    try:
                        import PIL.Image as _PIL
                        if isinstance(p, _PIL.Image.Image):
                            return True
                    except Exception:
                        pass
                    return isinstance(p, dict) and isinstance(p.get("mime_type"), str) and p["mime_type"].startswith("image/")
                
                wants_images = (
                    ("gemini-2.5-flash-image" in model) or
                    bool(kwargs.get("return_images")) or
                    any(_is_image_part(p) for p in contents_parts if not isinstance(p, str))
                )
                if wants_images:
                    config.response_modalities = ["TEXT", "IMAGE"]
                
                # Get model name
                model_name = self.MODEL_MAPPING.get(model, f"models/{model}")
                
                if "gemini-2.5-flash-image" in model:
                    try:
                        _ = self.client.models.get(model=model_name)
                    except Exception as availability_err:
                        raise RuntimeError(
                            "Gemini 2.5 Flash Image is not available for this API key/project (preview/special access required). "
                            f"Original error: {availability_err}"
                        )

                # Generate response
                response = await self.client.aio.models.generate_content(

                    model=model_name,
                    contents=contents,
                    config=config
                )
                
                # Extract response content and images
                response_content = ""
                image_parts: List[Dict[str, Any]] = []
                try:
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if getattr(part, "text", None):
                                    if not response_content:
                                        response_content = part.text
                                elif getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                                    img_bytes = part.inline_data.data
                                    mime = getattr(part.inline_data, "mime_type", "image/jpeg")
                                    image_parts.append({"data": img_bytes, "mime_type": mime})
                    elif hasattr(response, 'text') and response.text:
                        response_content = response.text
                except Exception as e:
                    logger.error(f"Error extracting response: {e}")
                    response_content = str(e)
                
                self.telemetry.request_counter.add(
                    1, 
                    {**base_attrs_with_client, "status": "success"}
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
                            "content": response_content or ""
                        },
                        "finish_reason": "stop"
                    }],
                    "images": (image_parts[0] if len(image_parts) == 1 else (image_parts if image_parts else None)),
                    "usage": None  # Could be extracted if needed
                }
            
        except Exception as e:
            logger.error(f"Completion error: {e}")
            self.telemetry.request_counter.add(
                1, 
                {**base_attrs_with_client, "status": "error", "error_type": type(e).__name__}
            )
            raise
    
    async def list_models(self) -> List[str]:
        """List available Gemini models from the API"""
        try:
            # Query the actual Google Gemini API for available models
            models_response = await self.client.aio.models.list()
            model_names = []
            async for model in models_response:
                # Extract the model name without the "models/" prefix
                model_id = model.name.replace("models/", "") if hasattr(model, 'name') else str(model)
                if model_id and not model_id.startswith("tunedModels/"):
                    model_names.append(model_id)
            
            return model_names if model_names else list(self.MODEL_MAPPING.keys())
                
        except Exception as e:
            logger.warning(f"Could not fetch models from Google API: {e}")
            # Fall back to hardcoded list if API call fails
            return list(self.MODEL_MAPPING.keys())
