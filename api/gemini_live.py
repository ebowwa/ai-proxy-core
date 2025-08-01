"""
Gemini Live WebSocket API - Clean proxy implementation
Reference: https://claude.ai/share/d45e444e-b16b-441a-a80a-0333a80ac95a
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

# Default model for live sessions
DEFAULT_MODEL = "models/gemini-2.0-flash-exp"

# Default configuration
DEFAULT_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
)


class GeminiLiveSession:
    """Minimal Gemini Live session handler"""
    
    def __init__(
        self, 
        websocket: WebSocket,
        enable_code_execution: bool = False,
        enable_google_search: bool = False,
        custom_tools: Optional[list] = None
    ):
        self.websocket = websocket
        self.enable_code_execution = enable_code_execution
        self.enable_google_search = enable_google_search
        self.custom_tools = custom_tools or []
        self.session = None
        self.out_queue = None
        self.tasks = []
        
    def get_client(self):
        """Get Gemini client with API key"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        return genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
    
    def _build_tools(self) -> Optional[list]:
        """Build tools configuration from enabled options"""
        tools = []
        
        # Add built-in tools if enabled
        if self.enable_code_execution:
            tools.append(types.Tool(code_execution={}))
        
        if self.enable_google_search:
            tools.append(types.Tool(google_search={}))
            
        # Add custom tools
        tools.extend(self.custom_tools)
        
        return tools if tools else None
    
    async def send_to_gemini(self):
        """Send queued messages to Gemini"""
        while True:
            try:
                msg = await self.out_queue.get()
                if msg is None:
                    break
                await self.session.send(input=msg)
            except Exception as e:
                logger.error(f"Error sending to Gemini: {e}")
                break
    
    async def receive_from_gemini(self):
        """Receive responses from Gemini and forward to client"""
        while True:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Handle audio data
                    if data := response.data:
                        await self.websocket.send_json({
                            "type": "audio",
                            "data": base64.b64encode(data).decode() if isinstance(data, bytes) else data,
                            "format": "pcm16",
                            "sampleRate": 24000
                        })
                    
                    # Handle text responses
                    if text := response.text:
                        await self.websocket.send_json({
                            "type": "text",
                            "data": text
                        })
                    
                    # Handle function calls
                    if hasattr(response, 'function_calls') and response.function_calls:
                        for function_call in response.function_calls:
                            await self.websocket.send_json({
                                "type": "function_call",
                                "data": {
                                    "name": function_call.name,
                                    "args": function_call.args
                                }
                            })
                            
            except Exception as e:
                logger.error(f"Error receiving from Gemini: {e}")
                break
    
    async def handle_client_message(self, message: dict):
        """Process messages from the client"""
        msg_type = message.get("type")
        data = message.get("data")
        
        if msg_type == "config":
            # Handle configuration updates
            await self.update_config(data)
        elif msg_type == "audio":
            # Forward audio data
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        elif msg_type == "text":
            # Send text with end_of_turn
            await self.session.send(input=data, end_of_turn=True)
        elif msg_type == "function_result":
            # Send function result
            await self.session.send(input=data, end_of_turn=True)
    
    async def update_config(self, config_data: Dict[str, Any]):
        """Update session configuration"""
        # This would handle config updates if needed
        # For now, just acknowledge
        await self.websocket.send_json({
            "type": "config_updated",
            "data": config_data
        })
    
    async def start(self):
        """Start the Gemini Live session"""
        try:
            # Initialize client and session
            client = self.get_client()
            
            # Get model from client config or use default
            model = DEFAULT_MODEL
            
            # Build tools configuration
            tools = self._build_tools()
            
            # Create config with tools if any are enabled
            config = DEFAULT_CONFIG
            if tools:
                config = types.LiveConnectConfig(
                    response_modalities=DEFAULT_CONFIG.response_modalities,
                    speech_config=DEFAULT_CONFIG.speech_config,
                    tools=tools
                )
            
            self.session = client.aio.live.connect(
                model=model,
                config=config
            )
            await self.session.__aenter__()
            
            # Initialize queue
            self.out_queue = asyncio.Queue()
            
            # Start background tasks
            self.tasks.append(asyncio.create_task(self.send_to_gemini()))
            self.tasks.append(asyncio.create_task(self.receive_from_gemini()))
            
            # Process client messages
            async for message in self.websocket.iter_json():
                await self.handle_client_message(message)
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Session error: {e}")
            await self.websocket.send_json({
                "type": "error",
                "data": str(e)
            })
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up session resources"""
        # Stop queue processing
        if self.out_queue:
            await self.out_queue.put(None)
        
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close session
        if self.session:
            await self.session.__aexit__(None, None, None)


@router.websocket("/gemini/ws")
async def gemini_websocket(
    websocket: WebSocket,
    enable_code_execution: bool = False,
    enable_google_search: bool = False
):
    """WebSocket endpoint for Gemini Live sessions with optional built-in tools"""
    await websocket.accept()
    session = GeminiLiveSession(
        websocket,
        enable_code_execution=enable_code_execution,
        enable_google_search=enable_google_search
    )
    await session.start()