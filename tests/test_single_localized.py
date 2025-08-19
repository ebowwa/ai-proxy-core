"""
Test single localized app icon generation with text
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


def generate_english_icon_with_text():
    """Generate English app icon with CleanShots text"""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return False
    
    print("🔧 Initializing GPT-4o Image Provider...")
    provider = GPT4oImageProvider(api_key=api_key)
    
    # English version with "CleanShots" text
    prompt = """
    Generate a modern iOS app icon for CleanShots, a privacy-focused camera application:
    - Square format with iOS-style rounded corners
    - Vibrant turquoise/teal gradient background (#00AFAA to #00CFCC)
    - Large white camera icon in the center (simplified, geometric style)
    - Text "CleanShots" integrated below the camera icon
    - Font should be clean, modern, and readable (like SF Pro or Helvetica)
    - White text color to match the camera icon
    - Small sparkle or star accent near top-right for the "clean" privacy aspect
    - Professional, polished appearance suitable for App Store
    - Ensure text is clearly legible and well-balanced with the icon
    """
    
    print("🎨 Generating English icon with 'CleanShots' text...")
    
    try:
        # Generate the icon
        response = provider.generate(
            prompt=prompt,
            size=ImageSize.SQUARE,
            quality=ImageQuality.HD,
            style=ImageStyle.VIVID  # Vivid for more vibrant colors
        )
        
        # Create output directory
        output_dir = Path(__file__).parent / "test_output" / "localized_icons"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the image
        output_path = output_dir / "cleanshots_en_with_text.png"
        with open(output_path, 'wb') as f:
            f.write(response['image'])
        
        print(f"✅ Icon saved to: {output_path}")
        
        # Save the revised prompt
        if response.get('revised_prompt'):
            print(f"\n📝 Revised prompt: {response['revised_prompt'][:200]}...")
        
        # Open the image
        print("\n🖼️ Opening generated icon...")
        os.system(f"open {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating icon: {e}")
        return False


def generate_japanese_icon_with_text():
    """Generate Japanese app icon with katakana text"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    provider = GPT4oImageProvider(api_key=api_key)
    
    # Japanese version with katakana
    prompt = """
    Generate a modern iOS app icon for a privacy-focused camera application with Japanese text:
    - Square format with iOS-style rounded corners
    - Vibrant turquoise/teal gradient background (#00AFAA to #00CFCC)
    - Large white camera icon in the center (simplified, geometric style)
    - Japanese text "クリーンショット" (Clean Shot in Katakana) below the camera
    - Use a clean, modern Japanese font that's clearly readable
    - White text color to match the camera icon
    - Small sparkle accent for privacy/cleanliness
    - Professional appearance suitable for Japanese App Store
    - Ensure Japanese characters are properly sized and balanced
    """
    
    print("\n🎌 Generating Japanese icon with 'クリーンショット' text...")
    
    try:
        response = provider.generate(
            prompt=prompt,
            size=ImageSize.SQUARE,
            quality=ImageQuality.HD,
            style=ImageStyle.VIVID
        )
        
        output_dir = Path(__file__).parent / "test_output" / "localized_icons"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "cleanshots_ja_with_text.png"
        with open(output_path, 'wb') as f:
            f.write(response['image'])
        
        print(f"✅ Icon saved to: {output_path}")
        
        # Open the image
        print("🖼️ Opening generated icon...")
        os.system(f"open {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("="*50)
    print("Localized App Icon Generation with Text")
    print("="*50)
    
    # Generate English version
    english_success = generate_english_icon_with_text()
    
    # Generate Japanese version
    japanese_success = generate_japanese_icon_with_text()
    
    print("\n" + "="*50)
    print("Results:")
    print("="*50)
    print(f"{'✅' if english_success else '❌'} English (CleanShots)")
    print(f"{'✅' if japanese_success else '❌'} Japanese (クリーンショット)")
    
    if english_success and japanese_success:
        print("\n🎉 Both localized icons generated successfully!")