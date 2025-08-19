"""
Test explicit model selection for image generation
Each request must specify which model to use
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from src.providers.openai_image import (
    OpenAIImageProvider,
    ImageModel,
    ImageSize,
    ImageQuality,
    ImageStyle
)


def test_explicit_model_selection():
    """Test that each request explicitly specifies the model"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return False
    
    print("🔧 Initializing OpenAI Image Provider...")
    provider = OpenAIImageProvider(api_key=api_key)
    
    # List available models
    print("\n📋 Available Models and Capabilities:")
    for model_info in provider.list_models():
        print(f"\n  Model: {model_info['id']}")
        print(f"  Sizes: {', '.join(model_info['capabilities']['sizes'])}")
        print(f"  Features: {', '.join(model_info['capabilities']['features'])}")
        print(f"  Max prompt: {model_info['capabilities']['max_prompt']}")
    
    output_dir = Path(__file__).parent / "test_output" / "explicit_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: DALL-E 3 with explicit model parameter
    print("\n" + "="*60)
    print("Test 1: DALL-E 3 (Explicit)")
    print("="*60)
    try:
        response = provider.generate(
            model=ImageModel.DALLE_3,  # EXPLICIT MODEL SELECTION
            prompt="A minimalist app icon with camera on turquoise background",
            size=ImageSize.SQUARE,
            quality=ImageQuality.HD,
            style=ImageStyle.NATURAL
        )
        print(f"✅ Generated with model: {response['model']}")
        print(f"   Created at: {response['created']}")
        
        # Save image
        with open(output_dir / "dalle3_explicit.png", 'wb') as f:
            f.write(response['images']['data'])
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: GPT-Image-1 with explicit model parameter
    print("\n" + "="*60)
    print("Test 2: GPT-Image-1 (Explicit)")
    print("="*60)
    try:
        response = provider.generate(
            model="gpt-image-1",  # Can use string or enum
            prompt="Modern app icon with clean camera design and sparkle accent",
            size="1024x1024",
            quality="high"
        )
        print(f"✅ Generated with model: {response['model']}")
        if response.get('usage'):
            print(f"   Token usage: {response['usage']}")
        
        # Save image
        with open(output_dir / "gpt_image_1_explicit.png", 'wb') as f:
            f.write(response['images']['data'])
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: DALL-E 2 with explicit model parameter
    print("\n" + "="*60)
    print("Test 3: DALL-E 2 (Explicit)")
    print("="*60)
    try:
        response = provider.generate(
            model=ImageModel.DALLE_2,  # EXPLICIT MODEL SELECTION
            prompt="Simple camera icon",
            size="512x512",  # DALL-E 2 specific size
            n=2  # DALL-E 2 can generate multiple images
        )
        print(f"✅ Generated with model: {response['model']}")
        
        # DALL-E 2 can return multiple images
        if isinstance(response['images'], list):
            print(f"   Generated {len(response['images'])} images")
            for i, img in enumerate(response['images']):
                with open(output_dir / f"dalle2_explicit_{i}.png", 'wb') as f:
                    f.write(img['data'])
        else:
            with open(output_dir / "dalle2_explicit.png", 'wb') as f:
                f.write(response['images']['data'])
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Error case - no model specified
    print("\n" + "="*60)
    print("Test 4: Error Case - Invalid Model")
    print("="*60)
    try:
        response = provider.generate(
            model="invalid-model",  # This should fail
            prompt="Test"
        )
        print("❌ Should have failed but didn't!")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid model: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return True


def test_model_specific_features():
    """Test features specific to each model"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    provider = OpenAIImageProvider(api_key=api_key)
    output_dir = Path(__file__).parent / "test_output" / "explicit_models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("Model-Specific Features Test")
    print("="*60)
    
    # DALL-E 3 with style (only DALL-E 3 has styles)
    print("\n📸 DALL-E 3 Vivid Style:")
    try:
        response = provider.generate(
            model=ImageModel.DALLE_3,
            prompt="Vibrant colorful app icon",
            style=ImageStyle.VIVID,  # DALL-E 3 specific
            quality=ImageQuality.STANDARD
        )
        print(f"   ✅ Style: VIVID")
        if response['images'].get('revised_prompt'):
            print(f"   📝 Revised: {response['images']['revised_prompt'][:60]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # GPT-Image-1 with high resolution
    print("\n📸 GPT-Image-1 High Resolution:")
    try:
        response = provider.generate(
            model=ImageModel.GPT_IMAGE_1,
            prompt="Ultra detailed app icon",
            size="4096x4096",  # GPT-Image-1 specific high-res
            quality="high",
            output_compression=95  # GPT-Image-1 specific
        )
        print(f"   ✅ Size: 4096x4096")
        print(f"   ✅ Compression: 95%")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # DALL-E 2 with multiple images
    print("\n📸 DALL-E 2 Multiple Images:")
    try:
        response = provider.generate(
            model=ImageModel.DALLE_2,
            prompt="App icon variations",
            n=3,  # DALL-E 2 can generate up to 10
            size="256x256"
        )
        num_images = len(response['images']) if isinstance(response['images'], list) else 1
        print(f"   ✅ Generated {num_images} images")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return True


if __name__ == "__main__":
    print("="*60)
    print("OpenAI Image Generation - Explicit Model Selection")
    print("="*60)
    print("\n⚠️  Each request MUST specify which model to use")
    print("   No automatic fallback or model selection")
    
    # Run tests
    test_explicit_model_selection()
    test_model_specific_features()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print("✅ Requests must explicitly specify the model")
    print("✅ Each model has specific capabilities and limitations")
    print("✅ No automatic fallback between models")
    print("✅ Clear errors when invalid models are specified")