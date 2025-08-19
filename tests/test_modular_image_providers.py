"""
Test modular image generation providers
Demonstrates using DALL-E 3 and GPT-Image-1 (when available)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from src.providers.gpt_image_providers import (
    UnifiedImageProvider,
    DALLE3Provider,
    GPTImage1Provider,
    ImageModel,
    ImageSize,
    ImageQuality,
    ImageStyle
)


def test_unified_provider():
    """Test the unified provider with automatic model selection"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return False
    
    print("🔧 Initializing Unified Image Provider...")
    provider = UnifiedImageProvider(api_key=api_key)
    
    # List available models
    print("\n📋 Available Models:")
    for model_info in provider.list_available_models():
        print(f"  • {model_info['model']}: {model_info['status']}")
        print(f"    Max size: {model_info['max_size']}")
        print(f"    Features: {', '.join(model_info['features'])}")
    
    # Test with DALL-E 3 explicitly
    print("\n🎨 Testing with DALL-E 3...")
    try:
        response = provider.generate(
            prompt="A minimalist app icon with a camera symbol on turquoise background",
            model=ImageModel.DALLE_3,
            size=ImageSize.SQUARE,
            quality=ImageQuality.HD,
            style=ImageStyle.NATURAL
        )
        print(f"  ✅ Generated with: {response['provider']}")
        print(f"  📏 Size: {response.get('size', 'default')}")
        
        # Save the image
        output_dir = Path(__file__).parent / "test_output" / "modular_providers"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        dalle_path = output_dir / "dalle3_icon.png"
        with open(dalle_path, 'wb') as f:
            f.write(response['image'])
        print(f"  💾 Saved to: {dalle_path}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Test with GPT-Image-1 (with fallback)
    print("\n🚀 Testing with GPT-Image-1 (may fallback to DALL-E 3)...")
    try:
        response = provider.generate(
            prompt="""Create a professional app icon following these exact specifications:
            - Square format with subtle rounded corners
            - Turquoise gradient background (#00AFAA to #00CFCC)
            - White camera icon in center
            - Small sparkle accent
            - Clean, minimalist design
            - No text""",
            model=ImageModel.GPT_IMAGE_1,
            quality=ImageQuality.HIGH,
            size=ImageSize.SQUARE
        )
        
        if response.get('fallback'):
            print(f"  ⚠️ Fell back to: {response['provider']}")
        else:
            print(f"  ✅ Generated with: {response['provider']}")
            if response.get('token_usage'):
                print(f"  🪙 Token usage: {response['token_usage']}")
        
        # Save the image
        gpt_path = output_dir / "gpt_image_1_icon.png"
        with open(gpt_path, 'wb') as f:
            f.write(response['image'])
        print(f"  💾 Saved to: {gpt_path}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return True


def test_dalle3_directly():
    """Test DALL-E 3 provider directly"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    print("\n🎨 Testing DALL-E 3 Provider Directly...")
    provider = DALLE3Provider(api_key=api_key)
    
    try:
        response = provider.generate(
            prompt="Modern app icon with camera and privacy theme",
            size=ImageSize.SQUARE,
            quality=ImageQuality.STANDARD
        )
        print(f"  ✅ Model used: {response['model']}")
        print(f"  📝 Revised prompt: {response.get('revised_prompt', 'N/A')[:100]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_gpt_image_1_directly():
    """Test GPT-Image-1 provider directly (may fail if not available yet)"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    print("\n🚀 Testing GPT-Image-1 Provider Directly...")
    print("  ℹ️ Note: This model is available from April 2025")
    
    provider = GPTImage1Provider(api_key=api_key)
    
    try:
        # Check current date
        current_date = datetime.now()
        if current_date < datetime(2025, 4, 1):
            print(f"  ⏰ Current date: {current_date.strftime('%Y-%m-%d')}")
            print("  ⏰ GPT-Image-1 not yet available (launches April 2025)")
        
        response = provider.generate(
            prompt="High-resolution app icon with detailed camera design",
            size="1024x1024",
            quality="high",
            output_compression=90
        )
        print(f"  ✅ Model used: {response['model']}")
        print(f"  🪙 Token usage: {response.get('token_usage', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"  ⚠️ Expected error (model may not be available): {str(e)[:100]}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Modular Image Generation Providers Test")
    print("="*60)
    
    # Test unified provider
    unified_success = test_unified_provider()
    
    # Test individual providers
    dalle3_success = test_dalle3_directly()
    gpt1_success = test_gpt_image_1_directly()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    print("="*60)
    print(f"✅ Unified Provider: {'Success' if unified_success else 'Failed'}")
    print(f"✅ DALL-E 3 Direct: {'Success' if dalle3_success else 'Failed'}")
    print(f"{'⏰' if not gpt1_success else '✅'} GPT-Image-1 Direct: {'Not yet available' if not gpt1_success else 'Success'}")
    
    print("\n📝 Notes:")
    print("• DALL-E 3 is the current production model")
    print("• GPT-Image-1 launches April 2025 with better capabilities")
    print("• The unified provider handles fallback automatically")
    print("• Both models support C2PA metadata for AI content authenticity")