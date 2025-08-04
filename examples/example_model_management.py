#!/usr/bin/env python3
"""
Example usage of the Model Management abstraction
"""
import asyncio
import os
from ai_proxy_core import ModelManager, OpenAIModelProvider, OllamaModelProvider, GeminiModelProvider


async def main():
    """Demonstrate model management functionality"""
    
    # Create model manager
    model_manager = ModelManager()
    
    # Register providers (only register those with valid API keys/connections)
    print("Registering model providers...")
    
    # OpenAI provider (if API key available)
    if os.environ.get("OPENAI_API_KEY"):
        openai_provider = OpenAIModelProvider()
        model_manager.register_provider(openai_provider)
        print("✓ Registered OpenAI provider")
    else:
        print("⚠ Skipped OpenAI provider (no API key)")
    
    # Ollama provider (if server is running)
    try:
        ollama_provider = OllamaModelProvider()
        model_manager.register_provider(ollama_provider)
        print("✓ Registered Ollama provider")
    except Exception as e:
        print(f"⚠ Skipped Ollama provider: {e}")
    
    # Gemini provider (if API key available)
    if os.environ.get("GEMINI_API_KEY"):
        try:
            gemini_provider = GeminiModelProvider()
            model_manager.register_provider(gemini_provider)
            print("✓ Registered Gemini provider")
        except Exception as e:
            print(f"⚠ Skipped Gemini provider: {e}")
    else:
        print("⚠ Skipped Gemini provider (no API key)")
    
    print(f"\nRegistered providers: {model_manager.get_providers()}")
    
    # List all available models
    print("\n" + "="*50)
    print("DISCOVERING MODELS")
    print("="*50)
    
    all_models = await model_manager.list_all_models()
    print(f"Found {len(all_models)} models across all providers:")
    
    for model in all_models[:10]:  # Show first 10 models
        print(f"  • {model.id} ({model.provider}) - {model.context_limit:,} tokens")
        capabilities = [k for k, v in model.capabilities.items() if v]
        if capabilities:
            print(f"    Capabilities: {', '.join(capabilities)}")
    
    if len(all_models) > 10:
        print(f"    ... and {len(all_models) - 10} more models")
    
    # Find best model for specific requirements
    print("\n" + "="*50)
    print("INTELLIGENT MODEL SELECTION")
    print("="*50)
    
    requirements = {
        "multimodal": True,
        "min_context_limit": 16000,
        "local_preferred": False
    }
    
    print(f"Looking for model with requirements: {requirements}")
    best_model = await model_manager.find_best_model(requirements)
    
    if best_model:
        print(f"✓ Best match: {best_model.id} ({best_model.provider})")
        print(f"  Context limit: {best_model.context_limit:,} tokens")
        print(f"  Capabilities: {best_model.capabilities}")
    else:
        print("✗ No models match the requirements")
    
    # Test model availability
    print("\n" + "="*50)
    print("MODEL AVAILABILITY TESTING")
    print("="*50)
    
    # Test with different providers
    test_models = [
        ("gpt-3.5-turbo", "openai"),
        ("llama2", "ollama"),
        ("gemini-1.5-flash", "gemini")
    ]
    
    for model_id, provider_name in test_models:
        if provider_name in model_manager.get_providers():
            try:
                print(f"Ensuring {model_id} is available...")
                await model_manager.ensure_model_ready(model_id, provider_name)
                print(f"✓ {model_id} is ready")
                
                # Get detailed model info
                model_info = await model_manager.get_model_info(model_id, provider_name)
                if model_info:
                    print(f"  Description: {model_info.description}")
            except Exception as e:
                print(f"✗ {model_id} failed: {e}")
        else:
            print(f"⚠ Skipping {model_id} (provider {provider_name} not available)")
    
    # Provider-specific model listing
    print("\n" + "="*50)
    print("PROVIDER-SPECIFIC MODELS")
    print("="*50)
    
    for provider_name in model_manager.get_providers():
        models = await model_manager.list_all_models(provider_filter=provider_name)
        print(f"\n{provider_name.upper()} models ({len(models)} total):")
        for model in models[:5]:  # Show first 5 from each provider
            print(f"  • {model.id} - {model.context_limit:,} tokens")
        if len(models) > 5:
            print(f"    ... and {len(models) - 5} more")
    
    print("\n" + "="*50)
    print("EXAMPLE COMPLETE")
    print("="*50)
    print("The model management abstraction is working!")
    print("You can now use this to discover, manage, and select AI models")
    print("across OpenAI, Ollama, and Gemini providers.")


if __name__ == "__main__":
    # Set up basic logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run the example
    asyncio.run(main())