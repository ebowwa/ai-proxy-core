"""
Unified completions API - Single endpoint for all AI completions
Routes to appropriate provider based on model
"""
import os
import logging
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

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
    # Basic safety settings
    safety_settings: Optional[List[Dict[str, str]]] = Field(None, description="Safety settings")


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
    
    async def create_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Create a completion from messages - delegates to CompletionClient"""
        try:
            # Convert Pydantic messages to dict format
            messages = [msg.dict() for msg in request.messages]
            
            # Call the unified completion client
            result = await self.client.create_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format,
                system_instruction=request.system_instruction,
                safety_settings=request.safety_settings
            )
            
            # Convert result dict to CompletionResponse
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
async def create_chat_completion(request: CompletionRequest) -> CompletionResponse:
    """OpenAI-compatible chat completions endpoint"""
    handler = get_handler()
    
    # TODO: Authentication implementation point
    # When security module is complete, add optional auth here:
    # 
    # from fastapi import Header
    # authorization: Optional[str] = Header(None)
    # 
    # if handler.auth_enabled:  # Check if auth is configured
    #     if not authorization:
    #         raise HTTPException(status_code=401, detail="Authorization required")
    #     
    #     # Validate Bearer token
    #     token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    #     token_info = handler.auth.verify_token(token)
    #     
    #     if not token_info:
    #         raise HTTPException(status_code=401, detail="Invalid or expired token")
    #     
    #     # Check rate limits
    #     if not handler.auth.check_rate_limit(token_info):
    #         raise HTTPException(status_code=429, detail="Rate limit exceeded")
    #     
    #     # Could also add usage tracking, audit logging, etc.
    #     # logger.info(f"API call from client: {token_info.client_id}")
    
    return await handler.create_completion(request)


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