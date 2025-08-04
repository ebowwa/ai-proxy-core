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
DEFAULT_MODEL = "gemini-2.0-flash-exp"

# Default configuration - start with text only for simplicity
DEFAULT_CONFIG = types.LiveConnectConfig(
    response_modalities=["TEXT"],
    generation_config=types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=1000
    )
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
                # Use the deprecated send method for now (works until Q3 2025)
                # TODO: Migrate to send_realtime_input when documentation is clearer
                await self.session.send(input=msg, end_of_turn=True)
                logger.info(f"Sent to Gemini: {msg.get('mime_type', 'unknown')} message")
            except Exception as e:
                logger.error(f"Error sending to Gemini: {e}")
                break
    
    async def receive_from_gemini(self):
        """Receive responses from Gemini and forward to client"""
        try:
            while True:
                try:
                    logger.info("Waiting for Gemini response...")
                    
                    if not self.session:
                        logger.error("Session is None in receive_from_gemini")
                        break
                        
                    turn = self.session.receive()
                    async for response in turn:
                        logger.info(f"Received response from Gemini: {response}")
                        
                        # Handle audio data
                        if hasattr(response, 'data') and response.data:
                            logger.info(f"Received audio data: {len(response.data)} bytes")
                            await self.websocket.send_json({
                                "type": "audio",
                                "data": base64.b64encode(response.data).decode() if isinstance(response.data, bytes) else response.data,
                                "format": "pcm16",
                                "sampleRate": 24000
                            })
                        
                        # Handle text responses
                        if hasattr(response, 'text') and response.text:
                            logger.info(f"Received text: {response.text[:50]}...")
                            await self.websocket.send_json({
                                "type": "response",
                                "text": response.text
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
                    logger.error(f"Error in receive turn: {e}")
                    break
        except Exception as e:
            logger.error(f"Fatal error in receive_from_gemini: {e}")
    
    async def handle_client_message(self, message: dict):
        """Process messages from the client"""
        msg_type = message.get("type")
        data = message.get("data")
        
        if msg_type == "config":
            # Handle configuration updates
            await self.update_config(data)
        elif msg_type == "audio":
            # Handle audio data - Gemini expects specific format
            try:
                if isinstance(data, str):
                    # Base64 encoded audio from client
                    audio_bytes = base64.b64decode(data)
                else:
                    audio_bytes = data
                
                # Gemini Live expects audio in realtime chunks, not as a complete file
                # For WebM recorded audio, we need to send it properly
                await self.out_queue.put({
                    "mime_type": "audio/pcm",
                    "data": audio_bytes
                })
                logger.info(f"Queued audio data: {len(audio_bytes)} bytes")
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await self.websocket.send_json({
                    "type": "error", 
                    "data": f"Audio error: {str(e)}"
                })
        elif msg_type == "text" or msg_type == "message":
            # Send text message with end_of_turn
            # Handle both 'text' and 'message' types for compatibility
            text_content = data if isinstance(data, str) else data.get("text", "")
            if text_content:
                logger.info(f"Sending text to Gemini: {text_content[:50]}...")
                try:
                    # Check if session is still alive
                    if not self.session:
                        logger.error("Session is not initialized")
                        await self.websocket.send_json({
                            "type": "error",
                            "data": "Session not initialized"
                        })
                        return
                    
                    await self.session.send(input=text_content, end_of_turn=True)
                    logger.info("Text sent successfully, waiting for response...")
                    
                except asyncio.CancelledError:
                    logger.info("Send operation cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Error sending text: {e}")
                    await self.websocket.send_json({
                        "type": "error",
                        "data": f"Failed to send text: {str(e)}"
                    })
        elif msg_type == "function_result":
            # Send function result
            await self.session.send(input=data, end_of_turn=True)
    
    async def update_config(self, config_data: Dict[str, Any]):
        """Update session configuration"""
        # Config is set at connection time and can't be changed for Gemini Live
        # Just acknowledge the client's config
        logger.info(f"Received config from client: {config_data}")
        await self.websocket.send_json({
            "type": "config_success",
            "message": "Configuration acknowledged (set at connection time)"
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
                    generation_config=DEFAULT_CONFIG.generation_config,
                    tools=tools
                )
            
            # Properly await the async context manager
            logger.info(f"Connecting to Gemini with model: {model}")
            self.session = await client.aio.live.connect(
                model=model,
                config=config
            ).__aenter__()
            logger.info("Successfully connected to Gemini Live")
            
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
        
        # Close session - it's already an AsyncSession, not a context manager
        if self.session:
            try:
                await self.session.close()
            except:
                pass  # Session might already be closed


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