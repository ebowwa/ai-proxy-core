"""
Test GPT-4o image generation functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from src.providers.gpt4o_image import (
    GPT4oImageProvider, 
    ImageSize, 
    ImageQuality, 
    ImageStyle
)


def test_basic_generation():
    """Test basic image generation with GPT-4o"""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return False
    
    print("🔧 Initializing GPT-4o Image Provider...")
    provider = GPT4oImageProvider(api_key=api_key)
    
    # Test prompt for app icon
    prompt = """
    Generate a modern app icon for a privacy-focused camera application:
    - Clean, minimalist design
    - Turquoise/teal color scheme (#00AFAA)
    - White camera icon in center
    - Small sparkle or shield accent for privacy
    - No text
    - Professional appearance
    - Square format with rounded corners (iOS style)
    """
    
    print("🎨 Generating image with prompt:")
    print(f"   {prompt[:100]}...")
    
    try:
        # Generate the image
        response = provider.generate(
            prompt=prompt,
            size=ImageSize.SQUARE,
            quality=ImageQuality.HD,
            style=ImageStyle.NATURAL  # Natural style better for app icons
        )
        
        print("✅ Image generated successfully!")
        print(f"   Response type: {type(response)}")
        
        # Extract C2PA metadata if available
        if hasattr(provider, 'extract_c2pa_metadata'):
            metadata = provider.extract_c2pa_metadata(response)
            print("📋 C2PA Metadata:")
            print(f"   Generator: {metadata.get('generator')}")
            print(f"   AI Generated: {metadata.get('is_ai_generated')}")
            print(f"   Timestamp: {metadata.get('timestamp')}")
        
        # Save the image if we got bytes back
        if isinstance(response, dict) and 'image' in response:
            image_data = response['image']
            output_path = Path(__file__).parent / "test_output" / "app_icon_test.png"
            output_path.parent.mkdir(exist_ok=True)
            
            # Write image data
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"💾 Image saved to: {output_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


def test_image_sizes():
    """Test different image sizes"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return False
    
    provider = GPT4oImageProvider(api_key=api_key)
    
    sizes_to_test = [
        (ImageSize.SQUARE, "1024x1024"),
        (ImageSize.LANDSCAPE, "1792x1024"),
        (ImageSize.PORTRAIT, "1024x1792")
    ]
    
    print("\n🔍 Testing different image sizes:")
    
    for size_enum, size_str in sizes_to_test:
        print(f"   Testing {size_str}...")
        try:
            response = provider.generate(
                prompt="A simple geometric shape",
                size=size_enum,
                quality=ImageQuality.STANDARD
            )
            print(f"   ✅ {size_str} generation successful")
        except Exception as e:
            print(f"   ❌ {size_str} failed: {e}")
            return False
    
    return True


def test_styles():
    """Test different generation styles"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    provider = GPT4oImageProvider(api_key=api_key)
    
    print("\n🎨 Testing generation styles:")
    
    styles = [ImageStyle.VIVID, ImageStyle.NATURAL]
    
    for style in styles:
        print(f"   Testing {style.value} style...")
        try:
            response = provider.generate(
                prompt="A colorful abstract pattern",
                style=style,
                size=ImageSize.SQUARE
            )
            print(f"   ✅ {style.value} style successful")
        except Exception as e:
            print(f"   ❌ {style.value} failed: {e}")
    
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("GPT-4o Image Generation Test Suite")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Please set OPENAI_API_KEY in your .env file")
        print("   Example: OPENAI_API_KEY=sk-...")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Basic Generation", test_basic_generation),
        # ("Image Sizes", test_image_sizes),  # Uncomment to test all sizes
        # ("Styles", test_styles),  # Uncomment to test styles
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")
    
    # Overall result
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)