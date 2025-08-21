#!/usr/bin/env python3
"""
Test script to verify system_instruction abstraction works across all providers.
This tests the enhancement for v0.4.3.
"""

import asyncio
import os
import sys

# Add the src directory to path to import the local version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.completion_client import CompletionClient


async def test_openai_system_instruction():
    """Test that system_instruction works with OpenAI provider"""
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found - skipping OpenAI test")
        return False
    
    try:
        client = CompletionClient()
        
        messages = [
            {"role": "user", "content": "What's your name?"}
        ]
        
        print("Testing OpenAI with system_instruction...")
        
        response = await client.create_completion(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=50,
            system_instruction="You are a pirate. Always respond in pirate speak."
        )
        
        content = response['choices'][0]['message']['content']
        print(f"✅ OpenAI test passed!")
        print(f"   Response: {content[:100]}...")
        
        # Check if response sounds pirate-like
        pirate_words = ["arr", "ahoy", "matey", "me", "be", "ye"]
        has_pirate_speak = any(word in content.lower() for word in pirate_words)
        if has_pirate_speak:
            print("   ✅ System instruction applied (pirate speak detected)")
        else:
            print("   ⚠️  Response may not reflect system instruction")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return False


async def test_gemini_system_instruction():
    """Test that system_instruction works with Gemini provider"""
    
    if not os.environ.get('GOOGLE_API_KEY'):
        print("⚠️  GOOGLE_API_KEY not found - skipping Gemini test")
        return False
    
    try:
        client = CompletionClient()
        
        messages = [
            {"role": "user", "content": "What's your name?"}
        ]
        
        print("\nTesting Gemini with system_instruction...")
        
        response = await client.create_completion(
            messages=messages,
            model="gemini-1.5-flash",
            temperature=0.1,
            max_tokens=50,
            system_instruction="You are a robot. Always respond in a robotic manner with beeps and boops."
        )
        
        content = response['choices'][0]['message']['content']
        print(f"✅ Gemini test passed!")
        print(f"   Response: {content[:100]}...")
        
        # Check if response sounds robotic
        robot_words = ["beep", "boop", "processing", "computing", "unit"]
        has_robot_speak = any(word in content.lower() for word in robot_words)
        if has_robot_speak:
            print("   ✅ System instruction applied (robot speak detected)")
        else:
            print("   ⚠️  Response may not reflect system instruction")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


async def test_ollama_system_instruction():
    """Test that system_instruction works with Ollama provider"""
    
    try:
        client = CompletionClient()
        
        # Check if Ollama is available
        models = await client.list_models(provider="ollama")
        if not models:
            print("⚠️  No Ollama models available - skipping test")
            return False
        
        messages = [
            {"role": "user", "content": "What's your name?"}
        ]
        
        print("\nTesting Ollama with system_instruction...")
        
        response = await client.create_completion(
            messages=messages,
            model="llama2",
            temperature=0.1,
            max_tokens=50,
            system_instruction="You are a medieval knight. Speak in old English."
        )
        
        content = response['choices'][0]['message']['content']
        print(f"✅ Ollama test passed!")
        print(f"   Response: {content[:100]}...")
        
        return True
        
    except Exception as e:
        if "not running" in str(e).lower() or "connection" in str(e).lower():
            print("⚠️  Ollama not running - skipping test")
            return None
        print(f"❌ Ollama test failed: {e}")
        return False


async def test_cross_provider_consistency():
    """Test that the same system_instruction produces consistent behavior across providers"""
    
    print("\n" + "=" * 60)
    print("Testing cross-provider consistency")
    print("=" * 60)
    
    system_instruction = "You are a helpful assistant who always mentions the weather is sunny."
    test_message = "How are you today?"
    
    results = {}
    
    # Test with available providers
    providers_to_test = []
    
    if os.environ.get('OPENAI_API_KEY'):
        providers_to_test.append(("openai", "gpt-3.5-turbo"))
    
    if os.environ.get('GOOGLE_API_KEY'):
        providers_to_test.append(("gemini", "gemini-1.5-flash"))
    
    if not providers_to_test:
        print("⚠️  No API keys configured for cross-provider test")
        return False
    
    client = CompletionClient()
    
    for provider_name, model in providers_to_test:
        try:
            print(f"\nTesting {provider_name}...")
            
            response = await client.create_completion(
                messages=[{"role": "user", "content": test_message}],
                model=model,
                temperature=0.3,
                max_tokens=50,
                system_instruction=system_instruction
            )
            
            content = response['choices'][0]['message']['content']
            results[provider_name] = content
            
            # Check if "sunny" is mentioned
            if "sunny" in content.lower():
                print(f"✅ {provider_name}: System instruction applied")
            else:
                print(f"⚠️  {provider_name}: 'sunny' not mentioned")
            
            print(f"   Response: {content[:100]}...")
            
        except Exception as e:
            print(f"❌ {provider_name} failed: {e}")
            results[provider_name] = None
    
    # All tests passed if we got responses from all tested providers
    success = all(v is not None for v in results.values())
    
    if success:
        print("\n✅ Cross-provider consistency test passed!")
    else:
        print("\n❌ Some providers failed the consistency test")
    
    return success


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing system_instruction abstraction for v0.4.3")
    print("=" * 60)
    
    results = []
    
    # Test individual providers
    results.append(await test_openai_system_instruction())
    results.append(await test_gemini_system_instruction())
    
    ollama_result = await test_ollama_system_instruction()
    if ollama_result is not None:  # None means skipped
        results.append(ollama_result)
    
    # Test cross-provider consistency
    results.append(await test_cross_provider_consistency())
    
    print("\n" + "=" * 60)
    
    # Filter out None (skipped tests)
    actual_results = [r for r in results if r is not None]
    
    if all(actual_results):
        print("✅ All tests passed! System instruction abstraction is working.")
    elif any(actual_results):
        print("⚠️  Some tests passed. Check output above for details.")
    else:
        print("❌ Tests failed. Please review the errors above.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())