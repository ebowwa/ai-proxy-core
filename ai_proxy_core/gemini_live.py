"""
Gemini Live Session Handler - Core logic without FastAPI dependencies
"""
import os
import asyncio
import base64
import json
import logging
import time
from typing import Optional, Dict, Any, Callable, Union

from google import genai
from google.genai import types

from .telemetry import get_telemetry

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO", "TEXT"],
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
        config: Optional[types.LiveConnectConfig] = None,
        system_instruction: Optional[Union[str, types.Content]] = None,
        enable_code_execution: bool = False,
        enable_google_search: bool = False,
        custom_tools: Optional[list] = None
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.config = config or DEFAULT_CONFIG
        self.system_instruction = system_instruction
        self.enable_code_execution = enable_code_execution
        self.enable_google_search = enable_google_search
        self.custom_tools = custom_tools or []
        self.session = None
        self.session_ctx = None  # Store context manager separately
        self.out_queue = None
        self.tasks = []
        self.session_start_time = None
        self.telemetry = get_telemetry()
        
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
                if self.on_error:
                    await self.on_error(str(e))
                break
    
    async def receive_from_gemini(self):
        """Receive responses from Gemini and trigger callbacks"""
        while True:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Log response attributes for debugging
                    logger.info(f"Response type: {type(response)}, attributes: {dir(response)}")
                    
                    # Handle audio data
                    if hasattr(response, 'data') and response.data:
                        if self.on_audio:
                            data = response.data
                            # Ensure data is base64 encoded
                            if isinstance(data, bytes):
                                data = base64.b64encode(data).decode()
                            await self.on_audio(data)
                    
                    # Handle text responses
                    if hasattr(response, 'text') and response.text:
                        if self.on_text:
                            await self.on_text(response.text)
                    
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
            
            # Build tools configuration
            tools = self._build_tools()
            
            # Create config with system instruction and tools
            config = self.config
            if self.system_instruction or tools:
                # Convert string to Content object if needed
                system_instruction_content = None
                if self.system_instruction:
                    if isinstance(self.system_instruction, str):
                        system_instruction_content = types.Content(
                            parts=[types.Part.from_text(text=self.system_instruction)],
                            role="user"
                        )
                    else:
                        system_instruction_content = self.system_instruction
                
                # Create a new config with system instruction and tools
                config = types.LiveConnectConfig(
                    response_modalities=self.config.response_modalities,
                    speech_config=self.config.speech_config,
                    system_instruction=system_instruction_content,
                    tools=tools
                )
            
            self.session_ctx = client.aio.live.connect(
                model=self.model,
                config=config
            )
            self.session = await self.session_ctx.__aenter__()
            
            # Initialize queue
            self.out_queue = asyncio.Queue()
            
            # Start background tasks
            self.tasks.append(asyncio.create_task(self.send_to_gemini()))
            self.tasks.append(asyncio.create_task(self.receive_from_gemini()))
            
            # Track session start time
            self.session_start_time = time.time()
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            if self.on_error:
                await self.on_error(str(e))
            raise
    
    async def stop(self):
        """Stop the session and clean up"""
        # Record session duration if session was started
        if self.session_start_time:
            session_duration_ms = (time.time() - self.session_start_time) * 1000
            session_attributes = {
                "model": self.model,
                "has_tools": bool(self._build_tools()),
                "has_system_instruction": bool(self.system_instruction)
            }
            self.telemetry.record_duration(
                "gemini_live_session",
                session_duration_ms,
                session_attributes
            )
            logger.info(f"Session ended. Duration: {session_duration_ms:.2f}ms")
        
        # Stop queue processing
        if self.out_queue:
            await self.out_queue.put(None)
        
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close session
        if self.session_ctx:
            await self.session_ctx.__aexit__(None, None, None)