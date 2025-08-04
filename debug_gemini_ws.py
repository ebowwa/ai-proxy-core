#!/usr/bin/env python3
"""
Debug Gemini WebSocket connection issues
"""
import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket
from google import genai
from google.genai import types
import uvicorn

# Set up logging to see all details
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.websocket("/test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")
    
    try:
        # Get API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            await websocket.send_json({"error": "No API key"})
            return
            
        logger.info(f"API key found: {api_key[:10]}...")
        
        # Create client
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
        
        # Simple config
        config = types.LiveConnectConfig(
            response_modalities=["TEXT"],
        )
        
        logger.info("Connecting to Gemini...")
        
        # Connect to Gemini
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp",
            config=config
        ) as session:
            logger.info("Connected to Gemini successfully")
            await websocket.send_json({"status": "connected"})
            
            # Create tasks for bidirectional communication
            async def receive_from_client():
                try:
                    async for message in websocket.iter_json():
                        logger.info(f"Received from client: {message}")
                        
                        if message.get("type") == "text":
                            text = message.get("text", "")
                            logger.info(f"Sending to Gemini: {text}")
                            
                            # Send to Gemini
                            await session.send(input=text, end_of_turn=True)
                            logger.info("Sent to Gemini successfully")
                            
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")
                    
            async def receive_from_gemini():
                try:
                    while True:
                        logger.info("Waiting for Gemini response...")
                        turn = session.receive()
                        
                        async for response in turn:
                            logger.info(f"Got response: {response}")
                            
                            if hasattr(response, 'text') and response.text:
                                logger.info(f"Sending text to client: {response.text}")
                                await websocket.send_json({
                                    "type": "response",
                                    "text": response.text
                                })
                                
                except Exception as e:
                    logger.error(f"Error receiving from Gemini: {e}")
            
            # Run both tasks
            task1 = asyncio.create_task(receive_from_client())
            task2 = asyncio.create_task(receive_from_gemini())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            logger.info("One task completed, cancelling others")
            for task in pending:
                task.cancel()
                
    except Exception as e:
        logger.error(f"Session error: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        logger.info("Closing WebSocket")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")