"""
Complete guide for using Ollama with ai-proxy-core

This example demonstrates all the ways to use Ollama with the library,
including direct usage, model management, and error handling.
"""

import asyncio
import aiohttp
from typing import Optional, List, Dict, Any
from ai_proxy_core import OllamaCompletions, OllamaModelProvider, ModelManager, CompletionClient


async def check_ollama_status() -> bool:
    """Check if Ollama is running and accessible"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/version") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Ollama is running (version: {data.get('version', 'unknown')})")
                    return True
    except Exception as e:
        print(f"✗ Ollama is not accessible: {e}")
        print("\nTo install Ollama:")
        print("1. Visit https://ollama.ai")
        print("2. Download and install for your platform")
        print("3. Run: ollama serve")
        print("4. Pull a model: ollama pull llama3.2")
        return False


async def example_1_direct_ollama_usage():
    """Example 1: Direct usage of OllamaCompletions"""
    print("\n" + "="*60)
    print("Example 1: Direct OllamaCompletions Usage")
    print("="*60)
    
    # Initialize Ollama completions
    ollama = OllamaCompletions()
    
    # List available models
    models = ollama.list_models()
    print(f"\nAvailable models: {models}")
    
    if not models:
        print("No models found. Pull a model with: ollama pull llama3.2")
        return
    
    # Use the first available model
    model = models[0]
    print(f"\nUsing model: {model}")
    
    # Create a simple completion
    messages = [
        {"role": "user", "content": "What is 2+2? Answer in one word."}
    ]
    
    try:
        response = await ollama.create_completion(
            messages=messages,
            model=model,
            temperature=0.1
        )
        print(f"\nResponse: {response['content']}")
    except Exception as e:
        print(f"Error: {e}")


async def example_2_model_provider():
    """Example 2: Using OllamaModelProvider with ModelManager"""
    print("\n" + "="*60)
    print("Example 2: OllamaModelProvider with ModelManager")
    print("="*60)
    
    # Create model manager and register Ollama provider
    manager = ModelManager()
    provider = OllamaModelProvider()
    manager.register_provider(provider)
    
    # List all models through the manager
    model_infos = await manager.list_all_models()
    
    print("\nModels available through ModelManager:")
    for info in model_infos:
        print(f"  - {info.name} (provider: {info.provider}, status: {info.status})")
    
    if model_infos:
        # Ensure a model is ready
        model_name = model_infos[0].name
        print(f"\nEnsuring {model_name} is ready...")
        await manager.ensure_model_ready(model_name, "ollama")
        print(f"✓ {model_name} is ready for use")


async def example_3_completion_client():
    """Example 3: Using CompletionClient for unified interface"""
    print("\n" + "="*60)
    print("Example 3: CompletionClient Unified Interface")
    print("="*60)
    
    # Create completion client (it auto-detects Ollama)
    client = CompletionClient()
    
    # Check available providers
    providers = client.get_available_providers()
    print(f"\nAvailable providers: {providers}")
    
    if "ollama" not in providers:
        print("Ollama provider not available")
        return
    
    # List models
    models = await client.list_models(provider="ollama")
    if not models:
        print("No Ollama models available")
        return
    
    model_id = models[0]["id"]
    print(f"\nUsing model: {model_id}")
    
    # Create completion through unified interface
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": "Explain machine learning in one sentence."}
    ]
    
    try:
        response = await client.create_completion(
            messages=messages,
            model=model_id,
            provider="ollama",  # Explicitly specify Ollama
            temperature=0.7,
            max_tokens=100
        )
        print(f"\nResponse: {response['content']}")
    except Exception as e:
        print(f"Error: {e}")


async def example_4_streaming():
    """Example 4: Streaming responses from Ollama"""
    print("\n" + "="*60)
    print("Example 4: Streaming Responses")
    print("="*60)
    
    ollama = OllamaCompletions()
    models = ollama.list_models()
    
    if not models:
        print("No models available")
        return
    
    model = models[0]
    messages = [
        {"role": "user", "content": "Write a haiku about programming."}
    ]
    
    print(f"\nStreaming response from {model}:")
    print("-" * 40)
    
    # Note: Streaming implementation depends on Ollama's specific API
    # This is a placeholder for the streaming functionality
    try:
        response = await ollama.create_completion(
            messages=messages,
            model=model,
            temperature=0.9,
            stream=False  # Set to True when streaming is implemented
        )
        print(response['content'])
    except Exception as e:
        print(f"Error: {e}")


async def example_5_error_handling():
    """Example 5: Robust error handling and fallbacks"""
    print("\n" + "="*60)
    print("Example 5: Error Handling and Fallbacks")
    print("="*60)
    
    async def safe_completion(prompt: str, model: Optional[str] = None) -> str:
        """Create a completion with proper error handling"""
        try:
            ollama = OllamaCompletions()
            
            # Get available models
            models = ollama.list_models()
            if not models:
                return "Error: No models available. Please pull a model first."
            
            # Use specified model or first available
            model = model or models[0]
            
            # Create completion
            messages = [{"role": "user", "content": prompt}]
            response = await ollama.create_completion(
                messages=messages,
                model=model,
                temperature=0.7
            )
            
            return response.get('content', 'No response content')
            
        except ConnectionError:
            return "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
        except ValueError as e:
            return f"Error: Invalid parameters: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"
    
    # Test with various scenarios
    test_prompts = [
        "Hello, how are you?",
        "What is the capital of France?",
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        response = await safe_completion(prompt)
        print(f"Response: {response[:100]}...")  # Truncate long responses


async def example_6_advanced_usage():
    """Example 6: Advanced usage with custom parameters"""
    print("\n" + "="*60)
    print("Example 6: Advanced Usage")
    print("="*60)
    
    # Initialize with custom model manager
    manager = ModelManager()
    client = CompletionClient(model_manager=manager)
    
    # Register Ollama provider
    provider = OllamaModelProvider()
    manager.register_provider(provider)
    
    # Find best model for specific requirements
    requirements = {
        "min_context_limit": 4096,
        "multimodal": False,  # Text only
    }
    
    best_model = await client.find_best_model(requirements)
    if best_model:
        print(f"\nBest model for requirements: {best_model['name']}")
    
    # Use JSON response format (if supported by model)
    messages = [
        {
            "role": "user", 
            "content": "List 3 programming languages with their main use cases. "
                      "Format as JSON with 'language' and 'use_case' fields."
        }
    ]
    
    models = await client.list_models(provider="ollama")
    if models:
        try:
            response = await client.create_completion(
                messages=messages,
                model=models[0]["id"],
                provider="ollama",
                temperature=0.3,
                response_format={"type": "json_object"}  # Request JSON format
            )
            print(f"\nJSON Response: {response.get('content', 'No content')}")
        except Exception as e:
            print(f"Error with advanced features: {e}")


async def main():
    """Run all examples"""
    print("="*60)
    print("Ollama Integration Complete Guide")
    print("="*60)
    
    # Check Ollama status first
    if not await check_ollama_status():
        print("\n⚠️  Please install and start Ollama first")
        return
    
    # Run examples
    await example_1_direct_ollama_usage()
    await example_2_model_provider()
    await example_3_completion_client()
    await example_4_streaming()
    await example_5_error_handling()
    await example_6_advanced_usage()
    
    print("\n" + "="*60)
    print("Guide Complete!")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. OllamaCompletions - Direct, simple interface")
    print("2. OllamaModelProvider - Integration with ModelManager")
    print("3. CompletionClient - Unified interface for all providers")
    print("4. Always check if Ollama is running first")
    print("5. Handle errors gracefully with fallbacks")
    print("6. Use model_manager parameter for custom configurations")


if __name__ == "__main__":
    asyncio.run(main())