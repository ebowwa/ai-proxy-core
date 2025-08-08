"""
Model management abstractions for AI providers
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about an AI model"""
    id: str
    name: str
    provider: str
    context_limit: int
    capabilities: Dict[str, bool]  # multimodal, tools, streaming, etc.
    status: str  # 'available', 'downloading', 'error'
    version: Optional[str] = None
    description: Optional[str] = None


class ModelProvider(ABC):
    """Abstract base class for model providers"""
    
    @property  
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'ollama', 'gemini')"""
        pass
    
    @property
    @abstractmethod
    def supports_local_deployment(self) -> bool:
        """Whether this provider supports local model deployment"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """Discover available models from this provider"""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_id: str) -> ModelInfo:
        """Get detailed info about a specific model"""
        pass
    
    @abstractmethod
    async def ensure_model_available(self, model_id: str) -> None:
        """Ensure model is ready for use (download if needed)"""
        pass


class ModelManager:
    """Central registry for managing AI models across providers"""
    
    def __init__(self):
        self.providers: Dict[str, ModelProvider] = {}
    
    def register_provider(self, provider: ModelProvider) -> None:
        """Register a model provider"""
        self.providers[provider.name] = provider
        logger.info(f"Registered model provider: {provider.name}")
    
    async def list_all_models(self, provider_filter: Optional[str] = None) -> List[ModelInfo]:
        """List models from all providers or specific provider"""
        models = []
        providers = [self.providers[provider_filter]] if provider_filter else self.providers.values()
        
        for provider in providers:
            try:
                provider_models = await provider.list_models()
                models.extend(provider_models)
            except Exception as e:
                logger.error(f"Error listing models from {provider.name}: {e}")
        
        return models
    
    async def get_model_info(self, model_id: str, provider_name: Optional[str] = None) -> Optional[ModelInfo]:
        """Get detailed info about a specific model"""
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Provider {provider_name} not registered")
            return await self.providers[provider_name].get_model_info(model_id)
        
        # Search across all providers
        for provider in self.providers.values():
            try:
                return await provider.get_model_info(model_id)
            except Exception:
                continue
        
        return None
    
    async def find_best_model(self, requirements: Dict[str, Any]) -> Optional[ModelInfo]:
        """Find best model matching requirements"""
        all_models = await self.list_all_models()
        return self._select_optimal_model(all_models, requirements)
    
    def _select_optimal_model(self, models: List[ModelInfo], requirements: Dict[str, Any]) -> Optional[ModelInfo]:
        """Select optimal model based on requirements"""
        if not models:
            return None
        
        # Simple scoring system - can be enhanced
        scored_models = []
        for model in models:
            score = 0
            
            # Check required capabilities
            if requirements.get("multimodal") and model.capabilities.get("multimodal", False):
                score += 10
            if requirements.get("tools") and model.capabilities.get("tools", False):
                score += 5
            if requirements.get("streaming") and model.capabilities.get("streaming", False):
                score += 3
            
            # Context limit preference
            min_context = requirements.get("min_context_limit", 0)
            if model.context_limit >= min_context:
                score += min(model.context_limit // 1000, 20)  # Cap at 20 points
            
            # Local preference
            if requirements.get("local_preferred", False):
                provider = next((p for p in self.providers.values() if p.name == model.provider), None)
                if provider and provider.supports_local_deployment:
                    score += 15
            
            # Only consider available models
            if model.status == "available":
                score += 5
            
            scored_models.append((score, model))
        
        # Return highest scoring model
        if scored_models:
            scored_models.sort(key=lambda x: x[0], reverse=True)
            return scored_models[0][1]
        
        return None
    
    async def ensure_model_ready(self, model_id: str, provider_name: str) -> None:
        """Ensure specific model is available for use"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")
        
        await self.providers[provider_name].ensure_model_available(model_id)
    
    def get_providers(self) -> List[str]:
        """Get list of registered provider names"""
        return list(self.providers.keys())