# AI Proxy Core

A minimal Python package providing reusable AI service handlers for Gemini and other LLMs. No web framework dependencies - just the core logic.

## Installation

```bash
pip install ai-proxy-core
```

With telemetry support:
```bash
pip install "ai-proxy-core[telemetry]"
```

Or install from source:
```bash
git clone https://github.com/ebowwa/ai-proxy-core.git
cd ai-proxy-core
pip install -e .
# With telemetry: pip install -e ".[telemetry]"
```

## Usage

### Completions Handler

```python
from ai_proxy_core import CompletionsHandler

# Initialize handler
handler = CompletionsHandler(api_key="your-gemini-api-key")

# Create completion
response = await handler.create_completion(
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    model="gemini-1.5-flash",
    temperature=0.7
)

print(response["choices"][0]["message"]["content"])
```

### Gemini Live Session

```python
from ai_proxy_core import GeminiLiveSession

# Example 1: Basic session (no system prompt)
session = GeminiLiveSession(api_key="your-gemini-api-key")

# Example 2: Session with system prompt (simple string format)
session = GeminiLiveSession(
    api_key="your-gemini-api-key",
    system_instruction="You are a helpful voice assistant. Be concise and friendly."
)

# Example 3: Session with built-in tools enabled
session = GeminiLiveSession(
    api_key="your-gemini-api-key",
    enable_code_execution=True,      # Enable Python code execution
    enable_google_search=True,       # Enable web search
    system_instruction="You are a helpful assistant with access to code execution and web search."
)

# Example 4: Session with custom function declarations
from google.genai import types

def get_weather(location: str) -> dict:
    # Your custom function implementation
    return {"location": location, "temp": 72, "condition": "sunny"}

weather_function = types.FunctionDeclaration(
    name="get_weather",
    description="Get current weather for a location",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "location": types.Schema(type="STRING", description="City name")
        },
        required=["location"]
    )
)

session = GeminiLiveSession(
    api_key="your-gemini-api-key",
    custom_tools=[types.Tool(function_declarations=[weather_function])],
    system_instruction="You can help with weather information."
)

# Set up callbacks
session.on_audio = lambda data: print(f"Received audio: {len(data)} bytes")
session.on_text = lambda text: print(f"Received text: {text}")
session.on_function_call = lambda call: handle_function_call(call)

async def handle_function_call(call):
    if call["name"] == "get_weather":
        result = get_weather(**call["args"])
        await session.send_function_result(result)

# Start session
await session.start()

# Send audio/text
await session.send_audio(audio_data)
await session.send_text("What's the weather in Boston?")

# Stop when done
await session.stop()
```

### Integration with FastAPI

#### Chat Completions API
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ai_proxy_core import CompletionsHandler

app = FastAPI()
handler = CompletionsHandler()

class CompletionRequest(BaseModel):
    messages: list
    model: str = "gemini-1.5-flash"
    temperature: float = 0.7

@app.post("/api/chat/completions")
async def create_completion(request: CompletionRequest):
    try:
        response = await handler.create_completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### WebSocket for Gemini Live
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ai_proxy_core import GeminiLiveSession

app = FastAPI()

@app.websocket("/ws/gemini")
async def gemini_websocket(
    websocket: WebSocket,
    enable_code_execution: bool = False,
    enable_google_search: bool = False
):
    await websocket.accept()
    
    # Create session with tools if requested
    session = GeminiLiveSession(
        enable_code_execution=enable_code_execution,
        enable_google_search=enable_google_search
    )
    
    # Set up callbacks to forward to WebSocket
    session.on_audio = lambda data: websocket.send_json({
        "type": "audio", "data": data
    })
    session.on_text = lambda text: websocket.send_json({
        "type": "text", "data": text
    })
    
    await session.start()
    
    try:
        async for message in websocket.iter_json():
            if message["type"] == "audio":
                await session.send_audio(message["data"])
            elif message["type"] == "text":
                await session.send_text(message["data"])
    except WebSocketDisconnect:
        await session.stop()
```

## Features

- **No framework dependencies** - Use with FastAPI, Flask, or any Python app
- **Async/await support** - Modern async Python
- **Type hints** - Full type annotations
- **Minimal surface area** - Just the core logic you need
- **Easy testing** - Mock the handlers in your tests
- **Built-in tools** - Code execution and Google Search with simple flags
- **Custom functions** - Add your own function declarations
- **Reusable design** - Tools configured by consumers, not hardcoded
- **WebSocket support** - Real-time audio/text streaming with Gemini Live
- **Callback system** - Handle responses with custom callbacks
- **Optional telemetry** - OpenTelemetry integration for production monitoring

### Telemetry

Basic observability with OpenTelemetry (optional):

```python
# Install with: pip install "ai-proxy-core[telemetry]"

# Enable telemetry via environment variables
export OTEL_ENABLED=true
export OTEL_EXPORTER_TYPE=console  # or "otlp" for production
export OTEL_ENDPOINT=localhost:4317  # for OTLP exporter

# Automatic telemetry for:
# - Request counts by model/status
# - Request latency tracking
# - Session duration for WebSockets
# - Error tracking with types
```

The telemetry is completely optional and has zero overhead when disabled.

## Development

### Releasing New Versions

We provide an automated release script that handles version bumping, building, and publishing:

```bash
# Make the script executable (first time only)
chmod +x release.sh

# Release a new version
./release.sh 0.1.9
```

The script will:
1. Show current version and validate the new version format
2. Prompt for a release description (for CHANGELOG)
3. Update version in all necessary files (pyproject.toml, setup.py, __init__.py)
4. Update CHANGELOG.md with your description
5. Build the package
6. Upload to PyPI
7. Commit changes and create a git tag
8. Push to GitHub with the new tag

### Manual Build Process

If you prefer to build manually:

```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

## License

MIT