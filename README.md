# AI Proxy Core

A unified Python package providing a single interface for AI completions across multiple providers (OpenAI, Gemini, Ollama). Features intelligent model management, automatic provider routing, and zero-config setup.

> 💡 **Why not LangChain?** Read our [philosophy and architectural rationale](https://github.com/ebowwa/ai-proxy-core/issues/13) for choosing simplicity over complexity.

> 🎯 **What's Next?** See our [wrapper layer roadmap](https://github.com/ebowwa/ai-proxy-core/issues/14) for planned features and what belongs in a clean LLM wrapper.

## Installation

Basic (Google Gemini only):
```bash
pip install ai-proxy-core
```

With specific providers:
```bash
pip install "ai-proxy-core[openai]"     # OpenAI support
pip install "ai-proxy-core[anthropic]"  # Anthropic support (coming soon)
pip install "ai-proxy-core[telemetry]"  # OpenTelemetry support
pip install "ai-proxy-core[all]"        # Everything
```

Or install from source:
```bash
git clone https://github.com/ebowwa/ai-proxy-core.git
cd ai-proxy-core
pip install -e .
# With all extras: pip install -e ".[all]"
```

## Quick Start

### Unified Interface (Recommended)

```python
from ai_proxy_core import CompletionClient

# Single client for all providers
client = CompletionClient()

# Works with any model - auto-detects provider
response = await client.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4"  # Auto-routes to OpenAI
)

response = await client.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gemini-1.5-flash"  # Auto-routes to Gemini
)

response = await client.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama2"  # Auto-routes to Ollama
)

# All return the same standardized format
print(response["choices"][0]["message"]["content"])
```

### Intelligent Model Selection

```python
# Find the best model for your needs
best_model = await client.find_best_model({
    "multimodal": True,
    "min_context_limit": 32000,
    "local_preferred": False
})

response = await client.create_completion(
    messages=[{"role": "user", "content": "Describe this image"}],
    model=best_model["id"]
)
```

### Model Discovery

```python
# List all available models across providers
models = await client.list_models()
for model in models:
    print(f"{model['id']} ({model['provider']}) - {model['context_limit']:,} tokens")

# List models from specific provider
openai_models = await client.list_models(provider="openai")
```

## Advanced Usage

### Provider-Specific Completions

If you need provider-specific features, you can still use the individual clients:

```python
from ai_proxy_core import GoogleCompletions, OpenAICompletions, OllamaCompletions

# Google Gemini with safety settings
google = GoogleCompletions(api_key="your-gemini-api-key")
response = await google.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gemini-1.5-flash",
    safety_settings=[{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}]
)

# OpenAI with tool calling
openai = OpenAICompletions(api_key="your-openai-key")
response = await openai.create_completion(
    messages=[{"role": "user", "content": "What's the weather?"}],
    model="gpt-4",
    tools=[{"type": "function", "function": {"name": "get_weather"}}]
)

# Ollama with streaming
ollama = OllamaCompletions(base_url="http://localhost:11434")
response = await ollama.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama2",
    stream=True
)
```

### OpenAI-Compatible Endpoints

```python
# Works with any OpenAI-compatible API (Groq, Anyscale, Together, etc.)
groq = OpenAICompletions(
    api_key="your-groq-key",
    base_url="https://api.groq.com/openai/v1"
)

response = await groq.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="mixtral-8x7b-32768"
)
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
from ai_proxy_core import CompletionClient

app = FastAPI()
client = CompletionClient()

class CompletionRequest(BaseModel):
    messages: list
    model: str = "gemini-1.5-flash"
    temperature: float = 0.7

@app.post("/api/chat/completions")
async def create_completion(request: CompletionRequest):
    try:
        response = await client.create_completion(
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

### 🚀 **Unified Interface**
- **Single client for all providers** - No more provider-specific code
- **Automatic provider routing** - Detects provider from model name
- **Intelligent model selection** - Find best model based on requirements
- **Zero-config setup** - Auto-detects available providers from environment

### 🧠 **Model Management**
- **Cross-provider model discovery** - List models from OpenAI, Gemini, Ollama
- **Rich model metadata** - Context limits, capabilities, multimodal support
- **Automatic model provisioning** - Downloads Ollama models as needed
- **Model compatibility checking** - Ensures models support requested features

### 🔧 **Developer Experience**
- **No framework dependencies** - Use with FastAPI, Flask, or any Python app
- **Async/await support** - Modern async Python
- **Type hints** - Full type annotations
- **Easy testing** - Mock the unified client in your tests
- **Backward compatible** - All existing provider-specific code continues to work

### 🎯 **Advanced Features**
- **WebSocket support** - Real-time audio/text streaming with Gemini Live
- **Built-in tools** - Code execution and Google Search with simple flags
- **Custom functions** - Add your own function declarations
- **Optional telemetry** - OpenTelemetry integration for production monitoring
- **Provider-specific optimizations** - Access advanced features when needed

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

## Project Structure

> 📝 **Note:** Full documentation of the project structure is being tracked in [Issue #12](https://github.com/ebowwa/ai-proxy-core/issues/12)

This project serves dual purposes:
- **Python Library** (`/ai_proxy_core`): Installable via pip for use in Python applications
- **Web Service** (`/api`): FastAPI endpoints for REST API access

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