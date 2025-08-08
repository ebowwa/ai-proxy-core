"""
Model provider implementations for different AI services
"""
import os
import logging
from typing import List, Dict, Any, Optional

from ..models import ModelProvider, ModelInfo
from ..telemetry import get_telemetry

logger = logging.getLogger(__name__)


class OpenAIModelProvider(ModelProvider):
    """OpenAI model provider for model discovery and management"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize OpenAI model provider.
        
        Args:
            api_key: Optional API key. Falls back to OPENAI_API_KEY env var.
            base_url: Optional base URL for OpenAI-compatible endpoints
        """
        try:
            import openai
            self._openai = openai
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install ai-proxy-core[openai] "
                "or pip install openai"
            )
        
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided")
        
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
        self.telemetry = get_telemetry()
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def supports_local_deployment(self) -> bool:
        return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available OpenAI models"""
        try:
            response = await self.client.models.list()
            models = []
            
            for model in response.data:
                # Extract model capabilities based on model ID
                capabilities = self._get_model_capabilities(model.id)
                context_limit = self._get_context_limit(model.id)
                
                model_info = ModelInfo(
                    id=model.id,
                    name=model.id,
                    provider=self.name,
                    context_limit=context_limit,
                    capabilities=capabilities,
                    status="available",
                    description=f"OpenAI model {model.id}"
                )
                models.append(model_info)
            
            return models
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {e}")
            return []
    
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed info about a specific OpenAI model"""
        try:
            model = await self.client.models.retrieve(model_id)
            capabilities = self._get_model_capabilities(model.id)
            context_limit = self._get_context_limit(model.id)
            
            return ModelInfo(
                id=model.id,
                name=model.id,
                provider=self.name,
                context_limit=context_limit,
                capabilities=capabilities,
                status="available",
                description=f"OpenAI model {model.id}"
            )
        except Exception as e:
            logger.error(f"Error getting OpenAI model info for {model_id}: {e}")
            raise
    
    async def ensure_model_available(self, model_id: str) -> None:
        """Ensure OpenAI model exists and is available"""
        try:
            await self.client.models.retrieve(model_id)
        except Exception as e:
            raise ValueError(f"OpenAI model {model_id} not available: {e}")
    
    def _get_model_capabilities(self, model_id: str) -> Dict[str, bool]:
        """Get capabilities based on model ID"""
        capabilities = {
            "multimodal": False,
            "tools": False,
            "streaming": True,
            "json_mode": False
        }
        
        # Vision models
        if "vision" in model_id.lower() or "gpt-4" in model_id.lower():
            capabilities["multimodal"] = True
        
        # Tool calling support
        if any(x in model_id.lower() for x in ["gpt-4", "gpt-3.5-turbo"]):
            capabilities["tools"] = True
            capabilities["json_mode"] = True
        
        return capabilities
    
    def _get_context_limit(self, model_id: str) -> int:
        """Get context limit based on model ID"""
        context_limits = {
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
        }
        
        for model_prefix, limit in context_limits.items():
            if model_id.startswith(model_prefix):
                return limit
        
        # Default context limit
        return 4096


class OllamaModelProvider(ModelProvider):
    """Ollama model provider for local LLM management"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama model provider.
        
        Args:
            base_url: Ollama server URL. Falls back to OLLAMA_HOST env var or localhost:11434
        """
        try:
            import aiohttp
            self.aiohttp = aiohttp
        except ImportError:
            raise ImportError("aiohttp library not installed. Install with: pip install aiohttp")
        
        self.base_url = base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.telemetry = get_telemetry()
    
    @property
    def name(self) -> str:
        return "ollama"
    
    @property
    def supports_local_deployment(self) -> bool:
        return True
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models"""
        try:
            async with self.aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        logger.warning(f"Could not fetch Ollama models: {response.status}")
                        return []
                    
                    data = await response.json()
                    models = []
                    
                    for model_data in data.get("models", []):
                        model_name = model_data["name"]
                        capabilities = self._get_model_capabilities(model_name)
                        context_limit = self._get_context_limit(model_name)
                        
                        model_info = ModelInfo(
                            id=model_name,
                            name=model_name,
                            provider=self.name,
                            context_limit=context_limit,
                            capabilities=capabilities,
                            status="available",
                            version=model_data.get("digest", "")[:12] if model_data.get("digest") else None,
                            description=f"Ollama local model {model_name}"
                        )
                        models.append(model_info)
                    
                    return models
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []
    
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed info about a specific Ollama model"""
        try:
            async with self.aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_id}
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Model {model_id} not found")
                    
                    data = await response.json()
                    capabilities = self._get_model_capabilities(model_id)
                    context_limit = self._get_context_limit(model_id)
                    
                    return ModelInfo(
                        id=model_id,
                        name=model_id,
                        provider=self.name,
                        context_limit=context_limit,
                        capabilities=capabilities,
                        status="available",
                        description=data.get("details", {}).get("family", f"Ollama model {model_id}")
                    )
        except Exception as e:
            logger.error(f"Error getting Ollama model info for {model_id}: {e}")
            raise
    
    async def ensure_model_available(self, model_id: str) -> None:
        """Ensure Ollama model is downloaded and available"""
        try:
            # First check if model exists locally
            await self.get_model_info(model_id)
        except:
            # Model not available locally, try to pull it
            logger.info(f"Pulling Ollama model: {model_id}")
            async with self.aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_id}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Failed to pull Ollama model {model_id}: {error_text}")
                    
                    # Stream the pull progress (could be enhanced to show progress)
                    async for line in response.content:
                        if line:
                            logger.debug(f"Pull progress: {line.decode().strip()}")
    
    def _get_model_capabilities(self, model_name: str) -> Dict[str, bool]:
        """Get capabilities based on model name"""
        capabilities = {
            "multimodal": False,
            "tools": False,
            "streaming": True,
            "json_mode": False
        }
        
        # Vision models
        if any(x in model_name.lower() for x in ["vision", "llava", "bakllava"]):
            capabilities["multimodal"] = True
        
        # Some models support tool calling
        if any(x in model_name.lower() for x in ["mistral", "mixtral", "llama3"]):
            capabilities["tools"] = True
            capabilities["json_mode"] = True
        
        return capabilities
    
    def _get_context_limit(self, model_name: str) -> int:
        """Get context limit based on model name"""
        # Common context limits for popular models
        if "32k" in model_name.lower():
            return 32768
        elif "16k" in model_name.lower():
            return 16384
        elif any(x in model_name.lower() for x in ["llama2", "mistral-7b"]):
            return 4096
        elif "mixtral" in model_name.lower():
            return 32768
        elif "codellama" in model_name.lower():
            return 16384
        
        # Default context limit
        return 4096


class GeminiModelProvider(ModelProvider):
    """Google Gemini model provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini model provider.
        
        Args:
            api_key: Optional API key. Falls back to GEMINI_API_KEY env var.
        """
        try:
            from google import genai
            self.genai = genai
        except ImportError:
            raise ImportError("Google GenAI library not installed. Install with: pip install google-generativeai")
        
        # Support both GEMINI_API_KEY and GOOGLE_API_KEY for compatibility
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not provided")
        
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=self.api_key,
        )
        self.telemetry = get_telemetry()
    
    @property
    def name(self) -> str:
        return "gemini"
    
    @property
    def supports_local_deployment(self) -> bool:
        return True  # Via AI Edge/Nano
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Gemini models"""
        try:
            response = await self.client.aio.models.list()
            models = []
            
            for model in response.models:
                capabilities = self._get_model_capabilities(model.name)
                context_limit = self._get_context_limit(model.name)
                
                model_info = ModelInfo(
                    id=model.name.replace("models/", ""),
                    name=model.display_name or model.name,
                    provider=self.name,
                    context_limit=context_limit,
                    capabilities=capabilities,
                    status="available",
                    version=model.version if hasattr(model, 'version') else None,
                    description=model.description if hasattr(model, 'description') else f"Gemini model {model.name}"
                )
                models.append(model_info)
            
            return models
        except Exception as e:
            logger.error(f"Error listing Gemini models: {e}")
            return []
    
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed info about a specific Gemini model"""
        try:
            model_name = f"models/{model_id}" if not model_id.startswith("models/") else model_id
            # Use the correct genai.get_model method
            import asyncio
            from google import genai
            model = await asyncio.to_thread(genai.get_model, model_name)
            
            capabilities = self._get_model_capabilities(model.name)
            context_limit = self._get_context_limit(model.name)
            
            return ModelInfo(
                id=model.name.replace("models/", ""),
                name=model.display_name or model.name,
                provider=self.name,
                context_limit=context_limit,
                capabilities=capabilities,
                status="available",
                version=model.version if hasattr(model, 'version') else None,
                description=model.description if hasattr(model, 'description') else f"Gemini model {model.name}"
            )
        except Exception as e:
            logger.error(f"Error getting Gemini model info for {model_id}: {e}")
            raise
    
    async def ensure_model_available(self, model_id: str) -> None:
        """Ensure Gemini model exists and is available"""
        try:
            await self.get_model_info(model_id)
        except Exception as e:
            raise ValueError(f"Gemini model {model_id} not available: {e}")
    
    def _get_model_capabilities(self, model_name: str) -> Dict[str, bool]:
        """Get capabilities based on model name"""
        capabilities = {
            "multimodal": True,  # Most Gemini models support multimodal
            "tools": True,
            "streaming": True,
            "json_mode": True,
            "thinking": False
        }
        
        # Thinking mode for specific models
        if "2.5" in model_name and "pro" in model_name.lower():
            capabilities["thinking"] = True
        
        return capabilities
    
    def _get_context_limit(self, model_name: str) -> int:
        """Get context limit based on model name"""
        # Gemini models have very large context windows
        if "2.5" in model_name or "2.0" in model_name:
            return 2097152  # 2M tokens
        elif "1.5" in model_name:
            return 1048576   # 1M tokens
        elif "pro" in model_name.lower():
            return 1048576   # 1M tokens
        
        # Default context limit
        return 32768