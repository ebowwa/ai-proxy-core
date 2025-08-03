"""
Unified completions API - Single endpoint for all AI completions
Clean, minimal implementation without business logic
"""
import os
import base64
import io
import json
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import PIL.Image
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from google import genai
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Model mapping for convenience
MODEL_MAPPING = {
    "gemini-2.0-flash": "models/gemini-2.0-flash-exp",
    "gemini-1.5-flash": "models/gemini-1.5-flash",
    "gemini-1.5-pro": "models/gemini-1.5-pro",
    "gemini-pro": "models/gemini-pro",
    "gemini-pro-vision": "models/gemini-pro-vision"
}


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
    """Minimal completions handler"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize client if API key is available"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(
                http_options={"api_version": "v1beta"},
                api_key=api_key,
            )
        else:
            logger.warning("GEMINI_API_KEY not found in environment variables")
    
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
            # Add more content types as needed
        
        return parts
    
    async def create_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Create a completion from messages"""
        if not self.client:
            raise HTTPException(
                status_code=500, 
                detail="GEMINI_API_KEY not configured. Please set it in your environment variables."
            )
        
        try:
            # Convert messages to Gemini format
            contents = []
            for msg in request.messages:
                parts = self._parse_content(msg.content)
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": parts})
            
            # Configure generation
            config = types.GenerateContentConfig(
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                system_instruction=request.system_instruction
            )
            
            # Handle JSON response format
            if isinstance(request.response_format, dict) and request.response_format.get("type") == "json_object":
                config.response_mime_type = "application/json"
            
            # Add safety settings if provided
            if request.safety_settings:
                safety_config = []
                for setting in request.safety_settings:
                    safety_config.append(types.SafetySetting(
                        category=setting.get("category"),
                        threshold=setting.get("threshold", "BLOCK_MEDIUM_AND_ABOVE")
                    ))
                config.safety_settings = safety_config
            
            # Get model name
            model_name = MODEL_MAPPING.get(request.model, f"models/{request.model}")
            
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
            
            return CompletionResponse(
                id=f"comp-{datetime.now().timestamp()}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }]
            )
            
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