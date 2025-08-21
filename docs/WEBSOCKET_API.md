# Gemini Live WebSocket API Documentation

## Overview

The Gemini Live WebSocket API provides real-time, bidirectional communication with Google's Gemini model, supporting both text and audio interactions. When using audio responses, Gemini provides **both** the audio data and text transcription simultaneously.

## Quick Start

### 1. Environment Setup

```bash
# Install the package
pip install ai-proxy-core==0.3.3

# Set your Gemini API key
export GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Start the Server

```bash
# Clone the repository
git clone https://github.com/ebowwa/ai-proxy-core.git
cd ai-proxy-core

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py
# Server runs on http://localhost:8000
```

### 3. Test with the HTML Demo

Open `examples/gemini_live_demo.html` in your browser for a full-featured chat interface.

## WebSocket Message Formats

### Client to Server Messages

#### Configuration Message (Optional)
```json
{
    "type": "config",
    "data": {
        "model": "gemini-2.0-flash-exp",
        "generation_config": {
            "temperature": 0.7,
            "max_output_tokens": 1000,
            "response_modalities": ["TEXT", "AUDIO"]
        },
        "voice": "Puck"
    }
}
```

#### Text Message
```json
{
    "type": "message",
    "data": {
        "text": "Hello, how are you?"
    }
}
```

Alternative format:
```json
{
    "type": "text",
    "text": "Hello, how are you?"
}
```

#### Audio Message (Not fully implemented)
```json
{
    "type": "audio",
    "data": "base64_encoded_audio_data"
}
```
**Note:** Audio input requires PCM 16-bit, 16kHz format. Browser WebM audio needs conversion.

### Server to Client Messages

#### Text Response
```json
{
    "type": "response",
    "text": "I'm doing great! How can I help you today?"
}
```

#### Audio Response (When audio modality is enabled)
```json
{
    "type": "audio",
    "data": "base64_encoded_pcm_audio",
    "format": "pcm16",
    "sampleRate": 24000
}
```

#### System Messages
```json
{
    "type": "system",
    "data": "Connected to Gemini Live"
}
```

#### Error Messages
```json
{
    "type": "error",
    "data": "Error description"
}
```

#### Configuration Acknowledgment
```json
{
    "type": "config_success",
    "message": "Configuration acknowledged"
}
```

## Client Connection Examples

### JavaScript/Browser Client

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/gemini/ws');

// Handle connection
ws.onopen = () => {
    console.log('Connected to Gemini Live');
    
    // Send optional configuration
    ws.send(JSON.stringify({
        type: 'config',
        data: {
            model: 'gemini-2.0-flash-exp',
            generation_config: {
                temperature: 0.7,
                max_output_tokens: 1000,
                response_modalities: ['TEXT']
            }
        }
    }));
};

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'response':
            console.log('Gemini says:', data.text);
            // Display text in UI
            break;
            
        case 'audio':
            console.log('Received audio data');
            // Play audio: new Audio('data:audio/wav;base64,' + data.data).play()
            break;
            
        case 'system':
            console.log('System:', data.data);
            break;
            
        case 'error':
            console.error('Error:', data.data);
            break;
    }
};

// Send text message
function sendMessage(text) {
    ws.send(JSON.stringify({
        type: 'message',
        data: { text: text }
    }));
}

// Send audio (requires PCM conversion)
function sendAudio(audioBlob) {
    const reader = new FileReader();
    reader.onloadend = () => {
        const base64Audio = reader.result.split(',')[1];
        ws.send(JSON.stringify({
            type: 'audio',
            data: base64Audio
        }));
    };
    reader.readAsDataURL(audioBlob);
}
```

### Python Client

```python
import asyncio
import json
import websockets
import base64

async def gemini_client():
    uri = "ws://localhost:8000/api/gemini/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to Gemini Live")
        
        # Send configuration
        config = {
            "type": "config",
            "data": {
                "model": "gemini-2.0-flash-exp",
                "generation_config": {
                    "temperature": 0.7,
                    "response_modalities": ["TEXT", "AUDIO"]
                }
            }
        }
        await websocket.send(json.dumps(config))
        
        # Handle responses
        async def receive_messages():
            async for message in websocket:
                data = json.loads(message)
                
                if data["type"] == "response":
                    print(f"Gemini: {data['text']}")
                    
                elif data["type"] == "audio":
                    # Save or play audio
                    audio_data = base64.b64decode(data["data"])
                    print(f"Received {len(audio_data)} bytes of audio")
                    # Note: When audio is enabled, you get BOTH audio and text
                    
                elif data["type"] == "error":
                    print(f"Error: {data['data']}")
        
        # Send messages
        async def send_messages():
            while True:
                text = input("You: ")
                if text.lower() == 'quit':
                    break
                    
                message = {
                    "type": "message",
                    "data": {"text": text}
                }
                await websocket.send(json.dumps(message))
        
        # Run both tasks
        receive_task = asyncio.create_task(receive_messages())
        send_task = asyncio.create_task(send_messages())
        
        await asyncio.gather(receive_task, send_task)

# Run the client
asyncio.run(gemini_client())
```

## Server Implementation

The server uses the Google GenAI SDK with proper async context management:

```python
from fastapi import WebSocket
from google import genai
from google.genai import types
import asyncio

@app.websocket("/api/gemini/ws")
async def gemini_websocket(websocket: WebSocket):
    await websocket.accept()
    
    client = genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],  # or ["TEXT", "AUDIO"]
        generation_config=types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1000
        )
    )
    
    async with client.aio.live.connect(
        model="gemini-2.0-flash-exp",
        config=config
    ) as session:
        # Handle bidirectional communication
        # See full implementation in api/gemini_live.py
```

## Testing with WebSocket Clients

### Using wscat (Command Line)

```bash
# Install wscat
npm install -g wscat

# Connect to the WebSocket
wscat -c ws://localhost:8000/api/gemini/ws

# Send a message (after connection)
{"type":"message","data":{"text":"Hello Gemini!"}}
```

### Using Postman

1. Create a new WebSocket request
2. Enter URL: `ws://localhost:8000/api/gemini/ws`
3. Click Connect
4. Send messages in JSON format

### Using the Debug Test Page

We provide a minimal debug page for testing:

```bash
# Start the debug server (runs on port 8001)
python debug_gemini_ws.py

# Open debug_test.html in your browser
```

## Important Notes

### Audio Support

1. **Dual Output**: When audio modality is enabled, Gemini provides **both** audio data and text transcription for responses
2. **Audio Format**: Gemini expects PCM 16-bit, 16kHz for input and outputs PCM 16-bit, 24kHz
3. **Browser Limitation**: Browser MediaRecorder produces WebM format, which needs server-side conversion to PCM
4. **Current Status**: Text chat fully working in v0.3.3, audio input pending PCM conversion implementation

### Connection Lifecycle

1. Client connects to WebSocket endpoint
2. Server establishes connection with Gemini Live API
3. Optional: Client sends configuration
4. Bidirectional message flow begins
5. Either party can close the connection

### Error Handling

- Connection errors are sent as error messages
- The session automatically handles reconnection to Gemini if needed
- Client should implement reconnection logic for robustness

## Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Ensure `GEMINI_API_KEY` environment variable is set
   - Check `.env` file is loaded if using python-dotenv

2. **Connection closes immediately**
   - Check server logs for detailed error messages
   - Verify API key is valid
   - Ensure model name is correct (e.g., "gemini-2.0-flash-exp")

3. **No response from Gemini**
   - Check response_modalities in config
   - Ensure messages are properly formatted as JSON
   - Verify `end_of_turn=True` is set when sending to Gemini

4. **Audio not working**
   - Audio input requires PCM format conversion
   - Check browser console for MediaRecorder errors
   - Verify microphone permissions are granted

## Examples Repository

Full working examples are available in the repository:

- `examples/gemini_live_demo.html` - Full-featured browser client
- `debug_gemini_ws.py` - Minimal debug server
- `debug_test.html` - Simple test interface
- `api/gemini_live.py` - Production server implementation

## Version History

- **v0.3.3** (2025-08-04): Fixed WebSocket implementation with proper async context management
- **v0.3.2** and earlier: WebSocket implementation had connection issues

## Support

For issues or questions:
- GitHub Issues: https://github.com/ebowwa/ai-proxy-core/issues
- Documentation: https://github.com/ebowwa/ai-proxy-core/docs