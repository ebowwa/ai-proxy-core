"""
Gemini Live WebSocket API - Fixed version based on working debug test
"""
import os
import asyncio
import base64
import json
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/gemini/ws")
async def gemini_websocket(websocket: WebSocket):
    """WebSocket endpoint for Gemini Live sessions"""
    await websocket.accept()
    logger.info("WebSocket connected")
    
    try:
        # Get API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            await websocket.send_json({"type": "error", "data": "No API key configured"})
            return
            
        logger.info(f"API key found: {api_key[:10]}...")
        
        # Create client
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
        
        # Simple config - text only for now
        config = types.LiveConnectConfig(
            response_modalities=["TEXT"],
            generation_config=types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1000
            )
        )
        
        logger.info("Connecting to Gemini...")
        
        # Connect to Gemini using async context manager
        async with client.aio.live.connect(
            model="gemini-2.0-flash-exp",
            config=config
        ) as session:
            logger.info("Connected to Gemini successfully")
            await websocket.send_json({"type": "system", "data": "Connected to Gemini Live"})
            
            # Create tasks for bidirectional communication
            async def receive_from_client():
                """Handle messages from the client"""
                try:
                    async for message in websocket.iter_json():
                        logger.info(f"Received from client: {message}")
                        
                        msg_type = message.get("type")
                        
                        if msg_type == "config":
                            # Just acknowledge config
                            await websocket.send_json({
                                "type": "config_success",
                                "message": "Configuration acknowledged"
                            })
                            
                        elif msg_type in ["text", "message"]:
                            # Handle text messages
                            data = message.get("data")
                            text = data.get("text", "") if isinstance(data, dict) else data
                            
                            if text:
                                logger.info(f"Sending to Gemini: {text}")
                                await session.send(input=text, end_of_turn=True)
                                logger.info("Sent to Gemini successfully")
                                
                        elif msg_type == "audio":
                            # Audio not supported yet
                            await websocket.send_json({
                                "type": "system",
                                "data": "Audio input not yet supported"
                            })
                            
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")
                    
            async def receive_from_gemini():
                """Handle responses from Gemini"""
                try:
                    while True:
                        logger.info("Waiting for Gemini response...")
                        turn = session.receive()
                        
                        async for response in turn:
                            logger.info(f"Got response: {response}")
                            
                            # Handle text responses
                            if hasattr(response, 'server_content') and response.server_content:
                                content = response.server_content
                                if hasattr(content, 'model_turn') and content.model_turn:
                                    for part in content.model_turn.parts:
                                        if hasattr(part, 'text') and part.text:
                                            logger.info(f"Sending text to client: {part.text}")
                                            await websocket.send_json({
                                                "type": "response",
                                                "text": part.text
                                            })
                            
                            # Handle audio (if present)
                            if hasattr(response, 'server_content') and response.server_content:
                                content = response.server_content
                                if hasattr(content, 'model_turn') and content.model_turn:
                                    for part in content.model_turn.parts:
                                        if hasattr(part, 'inline_data') and part.inline_data:
                                            logger.info(f"Received audio data")
                                            await websocket.send_json({
                                                "type": "audio",
                                                "data": base64.b64encode(part.inline_data.data).decode(),
                                                "format": "pcm16",
                                                "sampleRate": 24000
                                            })
                                
                except Exception as e:
                    logger.error(f"Error receiving from Gemini: {e}")
            
            # Run both tasks concurrently
            task1 = asyncio.create_task(receive_from_client())
            task2 = asyncio.create_task(receive_from_gemini())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            logger.info("One task completed, cleaning up")
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
    except Exception as e:
        logger.error(f"Session error: {e}")
        await websocket.send_json({"type": "error", "data": str(e)})
    finally:
        logger.info("WebSocket session ended")