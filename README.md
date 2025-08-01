# AI Proxy Core

A minimal Python package providing reusable AI service handlers for Gemini and other LLMs. No web framework dependencies - just the core logic.

## Installation

```bash
pip install ai-proxy-core
```

Or install from source:
```bash
git clone https://github.com/ebowwa/ai-proxy-core.git
cd ai-proxy-core
pip install -e .
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

# Create session
session = GeminiLiveSession(api_key="your-gemini-api-key")

# Set up callbacks
session.on_audio = lambda data: print(f"Received audio: {len(data)} bytes")
session.on_text = lambda text: print(f"Received text: {text}")

# Start session
await session.start()

# Send audio/text
await session.send_audio(audio_data)
await session.send_text("Hello!")

# Stop when done
await session.stop()
```

### Integration with FastAPI

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

## Features

- **No framework dependencies** - Use with FastAPI, Flask, or any Python app
- **Async/await support** - Modern async Python
- **Type hints** - Full type annotations
- **Minimal surface area** - Just the core logic you need
- **Easy testing** - Mock the handlers in your tests

## Development

### Building the Package

When building the package for distribution, use `setup.py` directly instead of `python -m build` to avoid pip isolation issues:

```bash
python setup.py sdist bdist_wheel
```

This will create both source distribution and wheel files in the `dist/` directory.

### Publishing to PyPI

```bash
twine upload dist/*
```

## License

MIT