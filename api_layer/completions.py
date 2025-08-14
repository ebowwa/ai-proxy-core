"""
Unified completions API - Single endpoint for all AI completions
Routes to appropriate provider based on model
"""
import os
import logging
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Request

from datetime import datetime
from ai_proxy_core import CompletionClient

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Model to provider mapping moved to CompletionClient


class Message(BaseModel):
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="Text string or array of content parts")


class CompletionRequest(BaseModel):
    model: str = Field(default="gemini-1.5-flash", description="Model to use")
    messages: List[Message] = Field(..., description="Array of messages")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=8192)
    stream: bool = Field(default=False, description="Stream the response")
    response_format: Optional[Union[str, Dict[str, Any]]] = Field(
        default="text", 
        description="Response format: 'text' or {'type': 'json_object'} for structured output"
    )
    system_instruction: Optional[str] = Field(None, description="System instruction for the model")
    safety_settings: Optional[List[Dict[str, str]]] = Field(None, description="Safety settings")
    app: Optional[str] = None
    client_id: Optional[str] = None
    device: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None


class CompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class CompletionsHandler:
    """FastAPI wrapper for unified CompletionClient"""
    
    def __init__(self):
        # Check if secure storage should be enabled
        use_secure = os.environ.get("USE_SECURE_STORAGE", "false").lower() == "true"
        self.client = CompletionClient(use_secure_storage=use_secure)
        
        # TODO: Initialize authentication when security module is complete
        # self.auth_enabled = os.environ.get("REQUIRE_AUTH", "false").lower() == "true"
        # self.auth = None
        # if self.auth_enabled:
        #     try:
        #         from ai_proxy_core.security import APIGatewayAuth
        #         self.auth = APIGatewayAuth()
        #         logger.info("API authentication enabled")
        #     except ImportError:
        #         logger.warning("Auth requested but security module not available")
        #         self.auth_enabled = False
    
    async def create_completion(self, request: CompletionRequest, client_context: Optional[Dict[str, Any]] = None) -> CompletionResponse:
        """Create a completion from messages - delegates to CompletionClient"""
        try:
            messages = [msg.dict() for msg in request.messages]
            result = await self.client.create_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format,
                system_instruction=request.system_instruction,
                safety_settings=request.safety_settings,
                client_context=client_context
            )
            return CompletionResponse(**result)
            
        except ValueError as e:
            # Provider/model not available
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Handler will be initialized on first use
_handler = None


def get_handler():
    """Get or create handler instance"""
    global _handler
    if _handler is None:
        _handler = CompletionsHandler()
    return _handler


@router.post("/chat/completions")
async def create_chat_completion(request: CompletionRequest, http_request: Request) -> CompletionResponse:
    """OpenAI-compatible chat completions endpoint"""
    handler = get_handler()
    headers = http_request.headers

    def parse_forwarded_ip(forwarded_val: str) -> Optional[str]:
        for part in forwarded_val.split(","):
            for kv in part.split(";"):
                k, sep, v = kv.strip().partition("=")
                if k.lower() == "for" and sep:
                    v = v.strip().strip('"').strip("'")
                    if v.startswith("[") and v.endswith("]"):
                        v = v[1:-1]
                    return v
        return None

    xff = headers.get("x-forwarded-for", "")
    forwarded = headers.get("forwarded", "")
    x_real_ip = headers.get("x-real-ip", "")
    ip = None
    if xff:
        ip = xff.split(",")[0].strip()
    if not ip and forwarded:
        ip = parse_forwarded_ip(forwarded)
    if not ip and x_real_ip:
        ip = x_real_ip.strip()
    if not ip and http_request.client:
        ip = http_request.client.host

    body_ctx: Dict[str, Optional[str]] = {
        "app": request.app,
        "client_id": request.client_id,
        "device": request.device,
        "user_id": request.user_id,
        "session_id": request.session_id,
        "request_id": request.request_id,
    }
    header_ctx: Dict[str, Optional[str]] = {
        "app": headers.get("x-app"),
        "client_id": headers.get("x-client-id"),
        "device": headers.get("x-device"),
        "user_id": headers.get("x-user-id"),
        "session_id": headers.get("x-session-id"),
        "request_id": headers.get("x-request-id"),
    }
    client_context = {k: (body_ctx.get(k) or header_ctx.get(k)) for k in body_ctx.keys()}
    client_context["ip"] = ip
    if not client_context.get("client_id") and ip:
        client_context["client_id"] = ip

    return await handler.create_completion(request, client_context)


@router.get("/models")
async def list_models(provider: Optional[str] = Query(None, description="Filter by provider name")) -> Dict[str, Any]:
    """List available models from all providers or a specific provider"""
    handler = get_handler()
    
    try:
        models = await handler.client.list_models(provider=provider)
        return {
            "object": "list",
            "data": models
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
