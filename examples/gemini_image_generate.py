import base64
import os
import asyncio
from ai_proxy_core import CompletionClient

def _gemini_image_available() -> bool:
    try:
        from google import genai  # type: ignore
        client = genai.Client()
        try:
            for m in client.models.list():
                n = getattr(m, "name", None) or str(m)
                if isinstance(n, str) and "gemini-2.5-flash-image" in n:
                    return True
        except Exception:
            client.models.get(model="models/gemini-2.5-flash-image-preview")
            return True
    except Exception:
        return False

async def main():
    if not _gemini_image_available():
        print("Gemini 2.5 Flash Image is not available for this API key/project. This feature requires preview/special access.")
        return
    client = CompletionClient()
    prompt = "Photoreal banana on a wooden desk with soft studio lighting"
    resp = await client.create_completion(
        messages=[{"role": "user", "content": prompt}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    img = resp.get("images")
    if isinstance(img, list):
        img = img[0] if img else None
    if img and img.get("data"):
        out = os.path.abspath("gemini_banana.jpg")
        with open(out, "wb") as f:
            f.write(img["data"])
        print(f"Saved {out}")
    else:
        print("No image returned; response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
