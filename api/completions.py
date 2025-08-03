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
        self.client = CompletionClient()
    
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
    return await handler.create_completion(request)