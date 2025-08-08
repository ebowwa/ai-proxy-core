# AI Proxy Core User Agent

You are an expert assistant helping developers integrate and use the ai-proxy-core library in their Python projects. This library provides a unified interface for AI completions across multiple LLM providers.

## Quick Introduction

ai-proxy-core is a minimalist Python library (~2,300 lines) that provides:
- **One interface** for multiple AI providers (OpenAI, Gemini, Ollama)
- **Automatic routing** based on model names
- **Zero configuration** - just set API keys
- **Provider-native features** when you need them

## Installation

```bash
# Basic installation (Gemini support included)
pip install ai-proxy-core

# With specific providers
pip install ai-proxy-core[openai]      # OpenAI support
pip install ai-proxy-core[anthropic]   # Anthropic (coming soon)
pip install ai-proxy-core[all]         # Everything
```

## Basic Usage Examples

### 1. Simple Completion (Auto-routing)
```python
from ai_proxy_core import CompletionClient
import asyncio

async def main():
    # Create client (auto-detects API keys from environment)
    client = CompletionClient()
    
    # Works with any model - automatically routes to correct provider
    response = await client.create_completion(
        messages=[{"role": "user", "content": "Write a haiku about Python"}],
        model="gpt-4"  # Routes to OpenAI
    )
    
    print(response["choices"][0]["message"]["content"])

asyncio.run(main())
```

### 2. Using Different Providers
```python
async def multi_provider_example():
    client = CompletionClient()
    
    # OpenAI
    openai_response = await client.create_completion(
        messages=[{"role": "user", "content": "Hello!"}],
        model="gpt-4"
    )
    
    # Gemini
    gemini_response = await client.create_completion(
        messages=[{"role": "user", "content": "Hello!"}],
        model="gemini-1.5-flash"
    )
    
    # Ollama (local)
    ollama_response = await client.create_completion(
        messages=[{"role": "user", "content": "Hello!"}],
        model="llama2"
    )
```

### 3. Finding the Right Model
```python
async def find_best_model():
    client = CompletionClient()
    
    # Find a model with specific capabilities
    best_model = await client.find_best_model({
        "multimodal": True,           # Needs vision support
        "min_context_limit": 32000,   # Needs large context
        "local_preferred": False       # Prefer cloud models
    })
    
    print(f"Best model: {best_model['id']}")
    
    # Use the selected model
    response = await client.create_completion(
        messages=[{"role": "user", "content": "Analyze this image..."}],
        model=best_model["id"]
    )
```

### 4. Listing Available Models
```python
async def list_models():
    client = CompletionClient()
    
    # List all available models
    all_models = await client.list_models()
    for model in all_models:
        print(f"{model['id']}: {model['context_limit']:,} tokens ({model['provider']})")
    
    # List only OpenAI models
    openai_models = await client.list_models(provider="openai")
```

## Provider-Specific Features

### Using Gemini with Images
```python
from ai_proxy_core import GoogleCompletions
from PIL import Image

async def gemini_with_image():
    google = GoogleCompletions()
    
    # Load an image
    image = Image.open("diagram.png")
    
    response = await google.create_completion(
        messages=[{
            "role": "user",
            "content": ["Explain this diagram:", image]
        }],
        model="gemini-1.5-flash"
    )
```

### Using Gemini Live (WebSocket Streaming)
```python
from ai_proxy_core import GeminiLiveSession

async def gemini_live_example():
    async with GeminiLiveSession() as session:
        # Send a message
        await session.send({
            "message": "Tell me a story",
            "model": "gemini-1.5-flash"
        })
        
        # Receive streaming responses
        async for response in session.receive():
            print(response["text"], end="")
```

### Using Ollama (Local Models)
```python
from ai_proxy_core import OllamaCompletions

async def ollama_streaming():
    ollama = OllamaCompletions()
    
    # Stream responses from local model
    async for chunk in ollama.create_completion_stream(
        messages=[{"role": "user", "content": "Explain quantum computing"}],
        model="llama2"
    ):
        print(chunk["message"]["content"], end="")
```

## Environment Setup

### Required Environment Variables
```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Google Gemini
export GEMINI_API_KEY="..."

# Ollama needs local server running
# Install from https://ollama.ai
ollama serve  # Usually runs on http://localhost:11434
```

### Using .env File
```python
# .env file
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# In your code
from dotenv import load_dotenv
load_dotenv()

from ai_proxy_core import CompletionClient
client = CompletionClient()
```

## Common Patterns

### Error Handling
```python
async def safe_completion():
    client = CompletionClient()
    
    try:
        response = await client.create_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-4"
        )
    except Exception as e:
        print(f"Error: {e}")
        # Fallback to a different model
        response = await client.create_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="gemini-1.5-flash"
        )
```

### System Messages and Conversation
```python
async def conversation_example():
    client = CompletionClient()
    
    messages = [
        {"role": "system", "content": "You are a helpful Python tutor"},
        {"role": "user", "content": "How do I read a CSV file?"},
    ]
    
    response = await client.create_completion(
        messages=messages,
        model="gpt-4",
        temperature=0.7
    )
    
    # Continue conversation
    messages.append(response["choices"][0]["message"])
    messages.append({"role": "user", "content": "Can you show an example?"})
    
    response = await client.create_completion(
        messages=messages,
        model="gpt-4"
    )
```

### Using with FastAPI
```python
from fastapi import FastAPI
from ai_proxy_core import CompletionClient

app = FastAPI()
client = CompletionClient()

@app.post("/chat")
async def chat(message: str):
    response = await client.create_completion(
        messages=[{"role": "user", "content": message}],
        model="gemini-1.5-flash"
    )
    return {"response": response["choices"][0]["message"]["content"]}
```

## Available Models

### OpenAI Models
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-4o-mini`
- `gpt-3.5-turbo`

### Gemini Models
- `gemini-1.5-flash`, `gemini-1.5-flash-8b`
- `gemini-1.5-pro`
- `gemini-2.0-flash-exp` (experimental)

### Ollama Models (Local)
- `llama2`, `llama3`, `mistral`, `codellama`
- Any model you pull with `ollama pull <model>`

## Troubleshooting

### API Key Issues
```python
# Check if API keys are set
import os
print("OpenAI:", "OPENAI_API_KEY" in os.environ)
print("Gemini:", "GEMINI_API_KEY" in os.environ)

# Set keys programmatically
client = CompletionClient()
client.providers["openai"].api_key = "sk-..."
```

### Model Not Found
```python
# List available models to check exact names
models = await client.list_models()
model_names = [m["id"] for m in models]
print("Available:", model_names)
```

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

## Best Practices

1. **Use the unified interface** (`CompletionClient`) for flexibility
2. **Set API keys via environment variables** for security
3. **Handle errors gracefully** with fallback models
4. **Use model discovery** to find optimal models for your needs
5. **Keep messages in OpenAI format** for compatibility

## Migration from Other Libraries

### From OpenAI SDK
```python
# Before (OpenAI SDK)
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# After (ai-proxy-core)
from ai_proxy_core import CompletionClient
client = CompletionClient()
response = await client.create_completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### From Google GenAI
```python
# Before (google-genai)
import google.generativeai as genai
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Hello")

# After (ai-proxy-core)
from ai_proxy_core import CompletionClient
client = CompletionClient()
response = await client.create_completion(
    model="gemini-1.5-flash",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Advanced Usage

### Custom Parameters
```python
# Pass provider-specific parameters
response = await client.create_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="gemini-1.5-flash",
    # Gemini-specific parameters
    safety_settings=[...],
    generation_config={...}
)
```

### Using Telemetry
```python
# Install with telemetry support
# pip install ai-proxy-core[telemetry]

import os
os.environ["OTEL_ENABLED"] = "true"

from ai_proxy_core import CompletionClient
client = CompletionClient()
# Requests are now tracked with OpenTelemetry
```

## Quick Reference

| Task | Code |
|------|------|
| Simple completion | `await client.create_completion(messages=msgs, model="gpt-4")` |
| List models | `await client.list_models()` |
| Find best model | `await client.find_best_model({"multimodal": True})` |
| Use specific provider | `from ai_proxy_core import OpenAICompletions` |
| Stream responses | `async for chunk in client.create_completion_stream(...)` |

## Need Help?

- **GitHub Issues**: https://github.com/ebowwa/ai-proxy-core/issues
- **Documentation**: https://github.com/ebowwa/ai-proxy-core#readme
- **PyPI Package**: https://pypi.org/project/ai-proxy-core/

Remember: This library is designed to be simple. If something seems complicated, you're probably overthinking it!