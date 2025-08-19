"""
Generate a proper Japanese localized app icon
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


def generate_proper_japanese_icon():
    """Generate a proper Japanese app icon with katakana text"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False
    
    provider = GPT4oImageProvider(api_key=api_key)
    
    # More explicit prompt for Japanese katakana
    prompt = """
    Create a modern app icon for a privacy-focused camera application:
    - Clean square format with subtle rounded corners
    - Vibrant turquoise/teal gradient background (#00AFAA to #00CFCC)
    - Large white simplified camera icon in the center (geometric, minimalist style)
    - Below the camera, add the text "クリーンショット" in Japanese Katakana characters
    - The text "クリーンショット" should be in clean white color
    - Use a modern, readable Japanese font (like Hiragino or Yu Gothic)
    - Add a small white sparkle or star accent for the privacy/cleanliness aspect
    - Professional, polished appearance
    - DO NOT include any English text
    - DO NOT include "iOS" or "E" badges
    - Make sure the Japanese text クリーンショット is clearly visible and properly rendered
    """
    
    print("🎌 Generating proper Japanese icon with katakana 'クリーンショット'...")
    
    try:
        response = provider.generate(
            prompt=prompt,
            size=ImageSize.SQUARE,
            quality=ImageQuality.HD,
            style=ImageStyle.NATURAL  # Natural for better text rendering
        )
        
        output_dir = Path(__file__).parent / "test_output" / "localized_icons"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "cleanshots_ja_fixed.png"
        with open(output_path, 'wb') as f:
            f.write(response['image'])
        
        print(f"✅ Icon saved to: {output_path}")
        
        if response.get('revised_prompt'):
            print(f"\n📝 Revised prompt: {response['revised_prompt'][:200]}...")
        
        # Open the image
        print("\n🖼️ Opening generated icon...")
        os.system(f"open {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("="*50)
    print("Japanese App Icon Generation Fix")
    print("="*50)
    print("\nNote: AI image generators often struggle with non-Latin text.")
    print("The text should be 'クリーンショット' (ku-ri-n-shotto) in Katakana.")
    print("")
    
    success = generate_proper_japanese_icon()
    
    if success:
        print("\n✅ Japanese icon generated!")
        print("\nPlease verify:")
        print("1. Text shows クリーンショット (not Chinese characters)")
        print("2. No 'iOS' or 'E' badges")
        print("3. Clean turquoise background with white camera icon")