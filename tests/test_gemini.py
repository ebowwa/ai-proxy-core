#!/usr/bin/env python3
"""Test that Gemini works without legacy completions.py"""
import asyncio
from ai_proxy_core import CompletionClient

async def test_gemini():
    client = CompletionClient()
    
    response = await client.create_completion(
        messages=[{"role": "user", "content": "Say exactly: Gemini works without legacy completions.py!"}],
        model="gemini-1.5-flash",
        temperature=0.1
    )
    
    print("Response:", response["choices"][0]["message"]["content"])
    return "works" in response["choices"][0]["message"]["content"].lower()

if __name__ == "__main__":
    result = asyncio.run(test_gemini())
    print(f"✅ Test passed!" if result else "❌ Test failed")