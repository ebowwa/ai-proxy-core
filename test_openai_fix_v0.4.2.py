#!/usr/bin/env python3
"""
Test script to verify OpenAI provider fix for system_instruction parameter issue.
This tests the fix for GitHub issue #32.
"""

import asyncio
import os
import sys

# Add the src directory to path to import the local version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.completion_client import CompletionClient


async def test_openai_with_system_instruction():
    """Test that OpenAI provider properly filters out system_instruction parameter"""
    
    # Check if API key is available
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found in environment variables")
        print("   Skipping OpenAI test - set OPENAI_API_KEY to run this test")
        return False
    
    try:
        # Initialize client
        client = CompletionClient()
        
        # Test messages
        messages = [
            {"role": "user", "content": "Say 'Hello, this test passed!' and nothing else."}
        ]
        
        print("Testing OpenAI provider with system_instruction parameter...")
        
        # This should NOT fail anymore - system_instruction should be filtered out
        response = await client.create_completion(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=50,
            system_instruction="This is a Gemini-specific parameter that should be filtered out"
        )
        
        print("✅ Test passed! OpenAI provider correctly filtered out system_instruction")
        print(f"Response: {response['choices'][0]['message']['content']}")
        return True
        
    except Exception as e:
        if "unexpected keyword argument 'system_instruction'" in str(e):
            print(f"❌ Test failed! The fix didn't work - still getting system_instruction error")
            print(f"Error: {e}")
            return False
        else:
            print(f"❌ Test failed with unexpected error: {e}")
            return False


async def test_openai_normal_operation():
    """Test that normal OpenAI operations still work correctly"""
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Skipping normal operation test - OPENAI_API_KEY not set")
        return False
    
    try:
        client = CompletionClient()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Reply with just the number."}
        ]
        
        print("\nTesting normal OpenAI operation...")
        
        response = await client.create_completion(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=0,
            max_tokens=10
        )
        
        content = response['choices'][0]['message']['content'].strip()
        print(f"✅ Normal operation test passed!")
        print(f"Response: {content}")
        return True
        
    except Exception as e:
        print(f"❌ Normal operation test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing fix for GitHub Issue #32")
    print("OpenAI provider system_instruction parameter filtering")
    print("=" * 60)
    
    results = []
    
    # Test the main fix
    results.append(await test_openai_with_system_instruction())
    
    # Test normal operation still works
    results.append(await test_openai_normal_operation())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed! The fix is working correctly.")
    else:
        print("❌ Some tests failed. Please review the output above.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())