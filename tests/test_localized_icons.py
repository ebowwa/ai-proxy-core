"""
Test localized app icon generation with text
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


def generate_localized_icons():
    """Generate app icons with localized text"""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return False
    
    print("🔧 Initializing GPT-4o Image Provider...")
    provider = GPT4oImageProvider(api_key=api_key)
    
    # Define localizations with their text
    localizations = {
        "en": {
            "text": "CleanShots",
            "prompt": """
            Generate a modern app icon for a privacy-focused camera application:
            - Turquoise/teal gradient background (#00AFAA to #00CFCC)
            - White camera icon in center
            - Text "CleanShots" in clean, modern font below the camera
            - Small sparkle accent for privacy
            - Professional appearance
            - iOS app store style with rounded corners
            - Text should be clearly readable and well-integrated
            """
        },
        "ja": {
            "text": "クリーンショット",
            "prompt": """
            Generate a modern app icon for a privacy-focused camera application:
            - Turquoise/teal gradient background (#00AFAA to #00CFCC)
            - White camera icon in center
            - Japanese text "クリーンショット" (Clean Shot in Katakana) in clean, modern font below the camera
            - Small sparkle accent for privacy
            - Professional appearance
            - iOS app store style with rounded corners
            - Japanese text should be clearly readable with appropriate font weight
            """
        },
        "es": {
            "text": "FotosLimpias",
            "prompt": """
            Generate a modern app icon for a privacy-focused camera application:
            - Turquoise/teal gradient background (#00AFAA to #00CFCC)
            - White camera icon in center
            - Spanish text "FotosLimpias" in clean, modern font below the camera
            - Small sparkle accent for privacy
            - Professional appearance
            - iOS app store style with rounded corners
            - Text should be clearly readable and well-integrated
            """
        },
        "fr": {
            "text": "PhotosPropres",
            "prompt": """
            Generate a modern app icon for a privacy-focused camera application:
            - Turquoise/teal gradient background (#00AFAA to #00CFCC)
            - White camera icon in center
            - French text "PhotosPropres" in clean, elegant font below the camera
            - Small sparkle accent for privacy
            - Professional appearance
            - iOS app store style with rounded corners
            - Text should be clearly readable with French aesthetic
            """
        },
        "zh": {
            "text": "清洁拍摄",
            "prompt": """
            Generate a modern app icon for a privacy-focused camera application:
            - Turquoise/teal gradient background (#00AFAA to #00CFCC)
            - White camera icon in center
            - Chinese text "清洁拍摄" (Clean Shot in Simplified Chinese) in clean, modern font below the camera
            - Small sparkle accent for privacy
            - Professional appearance
            - iOS app store style with rounded corners
            - Chinese characters should be clearly readable with appropriate stroke weight
            """
        }
    }
    
    # Create output directory
    output_dir = Path(__file__).parent / "test_output" / "localized_icons"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for locale, config in localizations.items():
        print(f"\n🌍 Generating icon for locale: {locale}")
        print(f"   Text: {config['text']}")
        
        try:
            # Generate the icon
            response = provider.generate(
                prompt=config['prompt'],
                size=ImageSize.SQUARE,
                quality=ImageQuality.HD,
                style=ImageStyle.NATURAL  # Natural style for text clarity
            )
            
            # Save the image
            output_path = output_dir / f"app_icon_{locale}.png"
            with open(output_path, 'wb') as f:
                f.write(response['image'])
            
            print(f"   ✅ Saved to: {output_path}")
            
            # Also save the revised prompt for reference
            if response.get('revised_prompt'):
                prompt_path = output_dir / f"prompt_{locale}.txt"
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(f"Original prompt:\n{config['prompt']}\n\n")
                    f.write(f"Revised prompt:\n{response['revised_prompt']}")
            
            results.append((locale, True))
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((locale, False))
    
    # Generate a comparison grid HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Localized App Icons</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            h1 {
                text-align: center;
                color: #00AFAA;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 30px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .icon-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .icon-card img {
                width: 150px;
                height: 150px;
                border-radius: 30px;
                margin-bottom: 10px;
            }
            .locale {
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
            .text {
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <h1>CleanShot Localized App Icons</h1>
        <div class="grid">
    """
    
    for locale, config in localizations.items():
        icon_path = f"app_icon_{locale}.png"
        if (output_dir / icon_path).exists():
            html_content += f"""
            <div class="icon-card">
                <img src="{icon_path}" alt="{locale} icon">
                <div class="locale">{locale.upper()}</div>
                <div class="text">{config['text']}</div>
            </div>
            """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    html_path = output_dir / "index.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML comparison page saved to: {html_path}")
    
    # Summary
    print("\n" + "="*50)
    print("Localization Results:")
    print("="*50)
    for locale, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {locale}: {'Success' if success else 'Failed'}")
    
    return all(r[1] for r in results)


if __name__ == "__main__":
    print("="*50)
    print("Localized App Icon Generation")
    print("="*50)
    
    success = generate_localized_icons()
    
    if success:
        print("\n🎉 All localized icons generated successfully!")
        print("\nOpening comparison page...")
        os.system("open tests/test_output/localized_icons/index.html")
    else:
        print("\n⚠️ Some localizations failed")