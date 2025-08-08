#!/usr/bin/env python3
"""
Test Gemini Live API connection
"""
import os
import asyncio
from google import genai
from google.genai import types

async def test_gemini_live():
    """Test basic Gemini Live connection"""
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment")
        return
    
    print(f"API Key found: {api_key[:10]}...")
    
    # Create client
    client = genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=api_key,
    )
    
    # Simple config
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
    )
    
    try:
        print("Connecting to Gemini Live...")
        
        # Connect to Gemini Live
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp",
            config=config
        ) as session:
            print("Connected successfully!")
            
            # Send a test message
            print("Sending test message...")
            await session.send(input="Hello, can you hear me?", end_of_turn=True)
            
            # Receive response
            print("Waiting for response...")
            turn = session.receive()
            async for response in turn:
                if response.text:
                    print(f"Gemini says: {response.text}")
                    break
            
            print("Test completed successfully!")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini_live())