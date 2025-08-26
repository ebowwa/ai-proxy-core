import base64
import os
import asyncio
from ai_proxy_core import CompletionClient

async def main():
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
