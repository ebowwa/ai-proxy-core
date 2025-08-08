#!/usr/bin/env python3
"""Test WebSocket connection to Gemini Live endpoint"""
import asyncio
import websockets
import json

async def test_gemini_websocket():
    uri = "ws://localhost:8000/api/gemini/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected to {uri}")
            
            # Send a test message
            message = {
                "type": "text",
                "data": {"text": "Hello, can you hear me?"}
            }
            await websocket.send(json.dumps(message))
            print(f"→ Sent: {message}")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"← Received: {response}")
            
            # Send another message
            message2 = {
                "type": "text", 
                "data": {"text": "Please say 'WebSocket is working!' in your response"}
            }
            await websocket.send(json.dumps(message2))
            print(f"→ Sent: {message2}")
            
            # Get response
            response2 = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"← Received: {response2}")
            
            print("✓ WebSocket test successful!")
            
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_websocket())