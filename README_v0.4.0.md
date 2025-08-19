# ai-proxy-core v0.4.0
## Abstract GPT-4o Image Generation Provider

### Overview
This release adds abstract wrapper support for OpenAI's GPT-4o native image generation capabilities (March 2025), maintaining consistency with ai-proxy-core's design philosophy of providing abstract, extensible AI provider interfaces.

### Installation
```bash
pip install ai-proxy-core==0.4.0
```

### Quick Start

```python
from ai_proxy_core import GPT4oImageProvider, ImageSize, ImageQuality

# Initialize provider
provider = GPT4oImageProvider(api_key="your-api-key")

# Generate image
response = provider.generate(
    prompt="A modern minimalist app icon",
    size=ImageSize.SQUARE,
    quality=ImageQuality.HD
)

# Access image data
image_bytes = response.image_data
c2pa_metadata = response.c2pa_metadata
```

### Abstract Models

The library provides abstract models that work across providers:

```python
from ai_proxy_core import ImageGenerationRequest, ImageGenerationResponse

# Create abstract request
request = ImageGenerationRequest(
    prompt="Generate an image",
    provider="openai",
    model="gpt-4o",
    size="1024x1024",
    context={"previous_messages": [...]}
)

# Convert to provider format
provider_request = request.to_provider_format("openai")
```

### Provider Implementations

#### OpenAI GPT-4o
```python
from ai_proxy_core import GPT4oImageProvider

provider = GPT4oImageProvider(api_key="sk-...")
```

#### Azure OpenAI
```python
from ai_proxy_core import AzureGPT4oImageProvider

provider = AzureGPT4oImageProvider(
    api_key="...",
    resource_name="myresource",
    deployment_name="gpt-image-1",
    api_version="2025-04-15"
)
```

### Image Editing

```python
# Edit existing image
edited = provider.edit(
    image=original_bytes,
    prompt="Change the background to turquoise",
    mask=mask_bytes  # Optional
)
```

### Context-Aware Generation

```python
# Generate with context
response = provider.generate(
    prompt="Create a similar style icon",
    context={
        "images": [reference_image_bytes],
        "messages": previous_chat_history
    }
)
```

### C2PA Metadata

All generated images include C2PA (Content Authenticity) metadata:

```python
metadata = provider.extract_c2pa_metadata(response)
print(metadata["generator"])  # "OpenAI GPT-4o"
print(metadata["is_ai_generated"])  # True
```

### Extending the Abstract Provider

Create your own implementation:

```python
from ai_proxy_core import GPT4oImageProvider

class CustomImageProvider(GPT4oImageProvider):
    def generate(self, prompt, **kwargs):
        # Add custom preprocessing
        prompt = self.preprocess_prompt(prompt)
        
        # Call parent implementation
        response = super().generate(prompt, **kwargs)
        
        # Add custom postprocessing
        return self.postprocess_response(response)
```

### What's New in v0.4.0

- **GPT-4o Native Generation**: Not DALL-E, uses autoregressive method
- **Image Editing**: Modify existing images with natural language
- **Context Awareness**: Use chat history and reference images
- **C2PA Metadata**: Built-in content authenticity
- **Azure Support**: Full Azure OpenAI integration
- **Abstract Models**: Provider-agnostic request/response models

### Migration from v0.3.x

```python
# Old (v0.3.x)
from ai_proxy_core import DallEProvider
provider = DallEProvider(api_key="key")

# New (v0.4.0)
from ai_proxy_core import GPT4oImageProvider
provider = GPT4oImageProvider(api_key="key")
```

### License
MIT

### Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Branch**: `feature/app-store-internationalization-v0.4.0`  
**Release**: v0.4.0  
**Issue**: #30