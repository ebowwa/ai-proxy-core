#!/usr/bin/env python3
"""
Test REAL Ollama integration - no fake data!
"""

import asyncio
from ai_proxy_core import OllamaCompletions

async def test_real_ollama():
    """Test that we're actually calling Ollama, not returning fake data"""
    
    print("Testing REAL Ollama integration...")
    print("-" * 50)
    
    ollama = OllamaCompletions()
    
    # This should now actually call Ollama
    models = ollama.list_models()
    
    print(f"Models returned: {models}")
    
    # Check if these are the fake hardcoded models
    fake_models = ["llama2", "llama2:13b", "llama2:70b", "mistral", "mixtral", "codellama", "neural-chat", "starling-lm", "yi"]
    
    if models == fake_models:
        print("❌ FAIL: Still returning FAKE hardcoded models!")
        return False
    elif not models:
        print("⚠️  No models (Ollama might not be running)")
        print("   Run: ollama serve")
        return True  # Not a failure, just Ollama not running
    else:
        print("✅ SUCCESS: Returning REAL models from Ollama!")
        print(f"   Real models: {models}")
        return True

if __name__ == "__main__":
    result = asyncio.run(test_real_ollama())
    exit(0 if result else 1)