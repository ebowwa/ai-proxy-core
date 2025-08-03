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
from ai_proxy_core.providers import GoogleCompletions, OpenAICompletions, OllamaCompletions

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Model to provider mapping
MODEL_PROVIDERS = {
    # OpenAI models
    "gpt-4": "openai",
    "gpt-4-turbo": "openai",
    "gpt-3.5-turbo": "openai",
    
    # Google models
    "gemini-1.5-flash": "google",
    "gemini-1.5-pro": "google",
    "gemini-2.0-flash": "google",
    "gemini-pro": "google",
    
    # Ollama models
    "llama2": "ollama",
    "mistral": "ollama",
    "codellama": "ollama",
    "mixtral": "ollama",
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
    """Multi-provider completions handler"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers based on environment"""
        # Google provider
        if os.environ.get("GEMINI_API_KEY"):
            try:
                self.providers["google"] = GoogleCompletions()
            except Exception as e:
                logger.warning(f"Could not initialize Google provider: {e}")
        
        # OpenAI provider
        if os.environ.get("OPENAI_API_KEY"):
            try:
                self.providers["openai"] = OpenAICompletions()
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI provider: {e}")
        
        # Ollama provider (always available for local)
        try:
            self.providers["ollama"] = OllamaCompletions()
        except Exception as e:
            logger.warning(f"Could not initialize Ollama provider: {e}")
        
        if not self.providers:
            logger.error("No providers available. Set API keys in environment.")
    
    def _get_provider_for_model(self, model: str):
        """Determine provider from model name"""
        # Check explicit mapping
        if model in MODEL_PROVIDERS:
            return MODEL_PROVIDERS[model]
        
        # Pattern matching
        if model.startswith("gpt"):
            return "openai"
        elif "gemini" in model.lower():
            return "google"
        elif model.startswith("claude"):
            return "anthropic"
        
        # Default to ollama for unknown models (might be local)
        return "ollama"
    
    
    async def create_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Create a completion from messages - routes to appropriate provider"""
        # Determine provider
        provider_name = self._get_provider_for_model(request.model)
        
        if provider_name not in self.providers:
            raise HTTPException(
                status_code=500,
                detail=f"Provider '{provider_name}' not available for model '{request.model}'. "
                       f"Available providers: {list(self.providers.keys())}"
            )
        
        provider = self.providers[provider_name]
        
        try:
            # Convert messages to dict format for provider
            messages = [msg.dict() for msg in request.messages]
            
            # Call provider's create_completion method
            result = await provider.create_completion(
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