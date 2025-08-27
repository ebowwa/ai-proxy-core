# AI Proxy Core

A unified Python package providing a single interface for AI completions across multiple providers (OpenAI, Gemini, Ollama), plus **image generation capabilities** (v0.4.0+). Features intelligent model management, automatic provider routing, zero-config setup, and abstract image generation with DALL-E 3.

> 💡 **Why not LangChain?** Read our [philosophy and architectural rationale](https://github.com/ebowwa/ai-proxy-core/issues/13) for choosing simplicity over complexity.

> 🎯 **What's Next?** See our [wrapper layer roadmap](https://github.com/ebowwa/ai-proxy-core/issues/14) for planned features and what belongs in a clean LLM wrapper.

## Installation

Basic (Google Gemini only):
```bash
pip install ai-proxy-core
```

With specific providers (optional dependencies):
```bash
pip install ai-proxy-core[openai]     # OpenAI support (includes image generation)
pip install ai-proxy-core[anthropic]  # Anthropic support (coming soon)
pip install ai-proxy-core[telemetry]  # OpenTelemetry support
pip install ai-proxy-core[all]        # Everything
```

Or install from source:
```bash
git clone https://github.com/ebowwa/ai-proxy-core.git
cd ai-proxy-core
pip install -e .
# With all extras: pip install -e ".[all]"
```

## Quick Start

> 🤖 **AI Integration Help**: 
> - **Using the library?** Copy our [user agent prompt](.claude/agents/ai-proxy-core-user.md) to any LLM for instant integration guidance and code examples
> - **Developing the library?** Use our [developer agent prompt](.claude/agents/ai-proxy-core-developer.md) for architecture details and contribution help

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

## Ollama Integration

### Prerequisites
```bash
# Install Ollama from https://ollama.ai
# Start Ollama service
ollama serve

# Pull a model
ollama pull llama3.2
```

### Using Ollama with CompletionClient
```python
from ai_proxy_core import CompletionClient, ModelManager

# Option 1: Auto-detection (Ollama will be detected if running)
client = CompletionClient()

# Option 2: With custom ModelManager
manager = ModelManager()
client = CompletionClient(model_manager=manager)

# List Ollama models
models = await client.list_models(provider="ollama")
print(f"Available Ollama models: {[m['id'] for m in models]}")

# Create completion
response = await client.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama3.2",
    provider="ollama",  # Optional, auto-detected from model name
    temperature=0.7
)
```

### Direct Ollama Usage
```python
from ai_proxy_core import OllamaCompletions

ollama = OllamaCompletions()

# List available models
models = ollama.list_models()
print(f"Available models: {models}")

# Create completion
response = await ollama.create_completion(
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    model="llama3.2",
    temperature=0.7,
    max_tokens=500
)
```

See [examples/ollama_complete_guide.py](examples/ollama_complete_guide.py) for comprehensive examples including error handling, streaming, and advanced features.

## Image Generation (v0.4.1+)

### Generate Images with Explicit Model Selection

```python
from ai_proxy_core import OpenAIImageProvider, ImageModel, ImageSize, ImageQuality, ImageStyle

# Initialize the provider
provider = OpenAIImageProvider(api_key="your-openai-api-key")

# Generate with DALL-E 3 (explicitly specify model)
response = provider.generate(
    model=ImageModel.DALLE_3,   # Required: specify which model
    prompt="A modern app icon with turquoise background and camera symbol",
    size=ImageSize.SQUARE,       # 1024x1024
    quality=ImageQuality.HD,      # HD or STANDARD
    style=ImageStyle.VIVID        # VIVID or NATURAL (DALL-E 3 only)
)

# Generate with GPT-Image-1 (better instruction following)
response = provider.generate(
    model=ImageModel.GPT_IMAGE_1,  # Explicitly use GPT-Image-1
    prompt="Create a detailed app icon following these specifications...",
    size="4096x4096",              # Supports up to 4K resolution
    quality="high"                 # low, medium, high, or auto
)

# Access the generated image
with open("icon.png", "wb") as f:
    f.write(response["images"]["data"])

# Token usage for GPT-Image-1
if response.get("usage"):
    print(f"Tokens used: {response['usage']['total_tokens']}")
```

### Available Models

```python
# List available models and their capabilities
for model in provider.list_models():
    print(f"Model: {model['id']}")
    print(f"  Sizes: {model['capabilities']['sizes']}")
    print(f"  Features: {model['capabilities']['features']}")

# Models:
# - dall-e-2: Multiple images, editing, 256x256 to 1024x1024
# - dall-e-3: Styles, HD quality, up to 1792x1024
# - gpt-image-1: Token pricing, 4K resolution, better instructions
```

### Gemini 2.5 Flash Image (Preview)

```python
from ai_proxy_core import CompletionClient
import asyncio, base64, os

async def main():
    client = CompletionClient()
    # Text-to-image
    resp = await client.create_completion(
        messages=[{"role":"user","content":"Photoreal banana on a desk"}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,  # forces image modality even with text-only prompt
    )
    img = resp.get("images")
    if isinstance(img, list):
        img = img[0] if img else None
    if img and img.get("data"):
        with open("gemini_banana.jpg", "wb") as f:
            f.write(img["data"])

    # Edit (image + instruction)
    def to_data_url(p):
        with open(p, "rb") as f: b = f.read()
        return "data:image/jpeg;base64," + base64.b64encode(b).decode("utf-8")

    messages = [{
        "role": "user",
        "content": [
            {"type":"image_url","image_url":{"url": to_data_url("sample.jpg")}},
            {"type":"text","text":"Remove the background and add a soft shadow"}
        ]
    }]
    resp = await client.create_completion(
        messages=messages,
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    img = resp.get("images")
    if isinstance(img, list):
        img = img[0] if img else None
    if img and img.get("data"):
        with open("gemini_edit.jpg", "wb") as f:
            f.write(img["data"])

if __name__ == "__main__":
    asyncio.run(main())
```

- Response schema remains OpenAI-like and non-breaking:
  - Text (if any) in `choices[0].message.content`
  - Image bytes in `response["images"]` (single object) or a list if multiple
- Aliases: `gemini-2.5-flash-image`, `g2.5-flash-image` route to preview for now

### Edit Images (DALL-E 2 Only)

```python
# Image editing is only available with DALL-E 2
response = provider.edit(
    image=original_image_bytes,
    prompt="Add a sunset background",
    model=ImageModel.DALLE_2,  # Only DALL-E 2 supports editing
    mask=mask_bytes,           # Optional mask for inpainting
    n=2                        # Generate 2 variations
)
```

### Model-Specific Features

```python
# DALL-E 2: Generate multiple variations
response = provider.generate(
    model=ImageModel.DALLE_2,
    prompt="App icon variations",
    n=5,  # Generate 5 variations
    size="512x512"
)

# DALL-E 3: Use styles for different aesthetics
response = provider.generate(
    model=ImageModel.DALLE_3,
    prompt="Photorealistic app icon",
    style=ImageStyle.NATURAL,  # or VIVID
    quality=ImageQuality.HD
)

# GPT-Image-1: High resolution with compression
response = provider.generate(
    model=ImageModel.GPT_IMAGE_1,
    prompt="Ultra-detailed 4K app icon",
    size="4096x4096",
    quality="high",
    output_compression=95  # Optional compression
)
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

# Ollama for local models
ollama = OllamaCompletions()  # Auto-detects localhost:11434
response = await ollama.create_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama3.2",
    temperature=0.7
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
### Audio in Chat Completions (Gemini)

The completions endpoint supports audio inputs for Google/Gemini via multimodal content:
- data URL audio_url entries (e.g., data:audio/mp3;base64,...)
- OpenAI-style input_audio objects with base64 data and format

Example request messages:
```json
[
  {
    "role": "user",
    "content": [
      {"type": "text", "text": "Transcribe and summarize this audio:"},
      {
        "type": "audio_url",
        "audio_url": {
          "url": "data:audio/mp3;base64,AAA..."
        }
      }
    ]
  }
]
```

OpenAI-style input_audio:
```json
[
  {
    "role": "user",
    "content": [
      {"type": "text", "text": "Please analyze this clip."},
      {
        "type": "input_audio",
        "input_audio": {
          "data": "AAA...", 
          "format": "mp3"
        }
      }
    ]
  }
]
```

Supported formats include MP3, WAV, AAC, OGG, FLAC. For WebSocket (Live), only PCM is supported at this time; non-PCM will be rejected with a clear message.
```

#### WebSocket for Gemini Live (Fixed in v0.3.3)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
import asyncio

app = FastAPI()

@app.websocket("/api/gemini/ws")
async def gemini_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # Create Gemini client
    client = genai.Client(
        http_options={"api_version": "v1beta"},
        api_key="your-gemini-api-key"
    )
    
    # Configure for text (audio requires PCM format)
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        generation_config=types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1000
        )
    )
    
    # Connect using async context manager
    async with client.aio.live.connect(
        model="gemini-2.0-flash-exp",
        config=config
    ) as session:
        
        # Handle bidirectional communication
        async def receive_from_client():
            async for message in websocket.iter_json():
                if message["type"] in ["text", "message"]:
                    text = message.get("data", {}).get("text", "")
                    if text:
                        await session.send(input=text, end_of_turn=True)
        
        async def receive_from_gemini():
            while True:
                turn = session.receive()
                async for response in turn:
                    if hasattr(response, 'server_content'):
                        content = response.server_content
                        if hasattr(content, 'model_turn'):
                            for part in content.model_turn.parts:
                                if hasattr(part, 'text') and part.text:
                                    await websocket.send_json({
                                        "type": "response",
                                        "text": part.text
                                    })
        
        # Run both tasks concurrently
        task1 = asyncio.create_task(receive_from_client())
        task2 = asyncio.create_task(receive_from_gemini())
        
        # Wait for either to complete
        done, pending = await asyncio.wait(
            [task1, task2],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Clean up
        for task in pending:
            task.cancel()
```

**Try the HTML Demo:**
```bash
# Start the FastAPI server
uv run main.py

# Open the HTML demo in your browser
open examples/gemini_live_demo.html
```

The demo provides a full-featured chat interface with WebSocket connection to Gemini Live.

Note on audio (WebSocket):
- Audio input is supported for PCM only (16-bit PCM). Send base64-encoded PCM and it will be forwarded to Gemini Live.
- Non-PCM inputs (e.g., WebM/Opus) are rejected with: "Audio requires PCM format - WebM conversion not yet implemented".
- Example client payloads:
  - Raw base64 string: {"type": "audio", "data": "<base64_pcm>"}
  - Object form: {"type": "audio", "data": {"base64": "<base64_pcm>", "mime_type": "audio/pcm"}}

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
## Client identification and IP fallback

To attribute requests to a product/app or device, the API accepts optional client metadata on both REST and WebSocket paths. If client_id is not provided, the server uses the client IP as a fallback (works for curl/CLI users too).

- Optional fields (REST body and WS config message):
  - app
  - client_id
  - device
  - user_id
  - session_id
  - request_id

- Optional HTTP headers (used when body fields are absent):
  - X-App
  - X-Client-Id
  - X-Device
  - X-User-Id
  - X-Session-Id
  - X-Request-Id

- IP resolution order:
  1) X-Forwarded-For (first IP)
  2) Forwarded header (for= token, supports quotes and IPv6 [brackets])
  3) X-Real-IP
  4) Socket peer address

- Precedence:
  - Body values override headers.
  - If client_id is missing, it defaults to the resolved IP.

- Telemetry:
  - Providers tag counters/durations with:
    - client.app
    - client.device
    - client.id
    - client.ip

### REST example (no client_id provided)
```bash
curl -X POST http://localhost:8000/api/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"gemini-1.5-flash","messages":[{"role":"user","content":"Hello"}]}'
```
If behind a proxy, include X-Forwarded-For or X-Real-IP so the correct source IP is used.

### WebSocket example config
After connecting to ws://localhost:8000/api/gemini/ws send:
```json
{"type":"config","app":"caringmind","device":"cli"}
```
If no client_id is present, the server computes it from the IP and acknowledges with:
```json
{"type":"config_success","message":"Configuration acknowledged","client_id":"<derived-ip>","ip":"<derived-ip>"}
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
uv run python setup.py sdist bdist_wheel
twine upload dist/*
```

## License

MIT
