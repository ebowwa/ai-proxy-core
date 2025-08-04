#!/usr/bin/env python3
"""
Example usage of the unified CompletionClient
"""
import asyncio
import os
from ai_proxy_core import CompletionClient


async def main():
    """Demonstrate unified completion client functionality"""
    
    print("🤖 AI Proxy Core - Unified Completion Client Example")
    print("=" * 60)
    
    # Create unified client
    client = CompletionClient()
    
    # Check available providers
    providers = client.get_available_providers()
    print(f"Available providers: {providers}")
    
    if not providers:
        print("❌ No providers available. Set API keys:")
        print("  - OPENAI_API_KEY for OpenAI models")
        print("  - GEMINI_API_KEY for Gemini models")
        print("  - Ensure Ollama is running for local models")
        return
    
    # Test message
    messages = [{"role": "user", "content": "Say hello and tell me your name in one sentence."}]
    
    # Test different models with unified interface
    test_models = [
        ("gpt-4", "OpenAI model"),
        ("gemini-1.5-flash", "Gemini model"), 
        ("llama2", "Ollama model")
    ]
    
    print(f"\n📝 Testing unified completion interface...")
    print("-" * 60)
    
    for model, description in test_models:
        try:
            print(f"\n🔄 Testing {description}: {model}")
            
            # Single unified interface for all providers!
            response = await client.create_completion(
                messages=messages,
                model=model,
                max_tokens=100,
                temperature=0.7
            )
            
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Response: {content[:100]}...")
            
        except Exception as e:
            print(f"⚠️  {model} failed: {e}")
    
    # Test model listing
    print(f"\n📋 Listing available models...")
    print("-" * 60)
    
    try:
        models = await client.list_models()
        print(f"Found {len(models)} models total:")
        
        # Group by provider
        by_provider = {}
        for model in models:
            provider = model.get("provider", "unknown")
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(model)
        
        for provider, provider_models in by_provider.items():
            print(f"\n{provider.upper()} ({len(provider_models)} models):")
            for model in provider_models[:3]:  # Show first 3
                model_id = model.get("id", model.get("name", "unknown"))
                capabilities = model.get("capabilities", {})
                caps = [k for k, v in capabilities.items() if v] if isinstance(capabilities, dict) else []
                caps_str = f" ({', '.join(caps)})" if caps else ""
                print(f"  • {model_id}{caps_str}")
            if len(provider_models) > 3:
                print(f"    ... and {len(provider_models) - 3} more")
                
    except Exception as e:
        print(f"❌ Could not list models: {e}")
    
    # Test intelligent model selection
    print(f"\n🧠 Testing intelligent model selection...")
    print("-" * 60)
    
    try:
        # Find best multimodal model
        requirements = {
            "multimodal": True,
            "min_context_limit": 16000
        }
        
        print(f"Looking for: {requirements}")
        best_model = await client.find_best_model(requirements)
        
        if best_model:
            print(f"✅ Best match: {best_model['id']} ({best_model['provider']})")
            print(f"   Context: {best_model['context_limit']:,} tokens")
            print(f"   Capabilities: {best_model['capabilities']}")
            
            # Test with the selected model
            print(f"\n🚀 Testing with selected model...")
            response = await client.create_completion(
                messages=[{"role": "user", "content": "Describe this task in one sentence."}],
                model=best_model['id'],
                max_tokens=50
            )
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Response: {content}")
            
        else:
            print("❌ No models match the requirements")
            
    except Exception as e:
        print(f"❌ Model selection failed: {e}")
    
    # Test explicit provider specification
    print(f"\n🎯 Testing explicit provider specification...")
    print("-" * 60)
    
    if "gemini" in providers:
        try:
            response = await client.create_completion(
                messages=[{"role": "user", "content": "What provider are you using?"}],
                model="gemini-1.5-flash",
                provider="gemini",  # Explicit provider
                max_tokens=50
            )
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Explicit Gemini: {content}")
        except Exception as e:
            print(f"❌ Explicit provider test failed: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎉 Unified Completion Client Demo Complete!")
    print("✨ Single interface works across all providers")
    print("🔍 Automatic model routing and provider detection")
    print("🧠 Intelligent model selection based on requirements")


if __name__ == "__main__":
    # Set up basic logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run the example
    asyncio.run(main())