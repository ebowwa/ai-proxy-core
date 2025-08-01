"""
Gemini Live Session Handler - Core logic without FastAPI dependencies
"""
import os
import asyncio
import base64
import json
import logging
from typing import Optional, Dict, Any, Callable

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

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
    """Gemini Live session handler - just the core logic"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "models/gemini-2.0-flash-exp",
        config: Optional[types.LiveConnectConfig] = None
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.config = config or DEFAULT_CONFIG
        self.session = None
        self.out_queue = None
        self.tasks = []
        
        # Callbacks for handling responses
        self.on_audio: Optional[Callable] = None
        self.on_text: Optional[Callable] = None
        self.on_function_call: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
    def get_client(self):
        """Get Gemini client with API key"""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")
        
        return genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=self.api_key,
        )
    
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
                if self.on_error:
                    await self.on_error(str(e))
                break
    
    async def receive_from_gemini(self):
        """Receive responses from Gemini and trigger callbacks"""
        while True:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Handle audio data
                    if data := response.data:
                        if self.on_audio:
                            # Ensure data is base64 encoded
                            if isinstance(data, bytes):
                                data = base64.b64encode(data).decode()
                            await self.on_audio(data)
                    
                    # Handle text responses
                    if text := response.text:
                        if self.on_text:
                            await self.on_text(text)
                    
                    # Handle function calls
                    if hasattr(response, 'function_calls') and response.function_calls:
                        if self.on_function_call:
                            for function_call in response.function_calls:
                                await self.on_function_call({
                                    "name": function_call.name,
                                    "args": function_call.args
                                })
                            
            except Exception as e:
                logger.error(f"Error receiving from Gemini: {e}")
                if self.on_error:
                    await self.on_error(str(e))
                break
    
    async def send_audio(self, audio_data: Union[str, bytes]):
        """Send audio data to Gemini"""
        if isinstance(audio_data, str):
            # Assume it's base64 encoded
            audio_data = base64.b64decode(audio_data)
        await self.out_queue.put({"data": audio_data, "mime_type": "audio/pcm"})
    
    async def send_text(self, text: str):
        """Send text to Gemini"""
        await self.session.send(input=text, end_of_turn=True)
    
    async def send_function_result(self, result: Any):
        """Send function result to Gemini"""
        await self.session.send(input=result, end_of_turn=True)
    
    async def start(self):
        """Start the Gemini Live session"""
        try:
            # Initialize client and session
            client = self.get_client()
            
            self.session = client.aio.live.connect(
                model=self.model,
                config=self.config
            )
            await self.session.__aenter__()
            
            # Initialize queue
            self.out_queue = asyncio.Queue()
            
            # Start background tasks
            self.tasks.append(asyncio.create_task(self.send_to_gemini()))
            self.tasks.append(asyncio.create_task(self.receive_from_gemini()))
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            if self.on_error:
                await self.on_error(str(e))
            raise
    
    async def stop(self):
        """Stop the session and clean up"""
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