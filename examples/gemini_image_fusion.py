import base64
import os
import asyncio
from ai_proxy_core import CompletionClient

def to_data_url(img_path: str) -> str:
    with open(img_path, "rb") as f:
        b = f.read()
    mime = "image/png" if img_path.lower().endswith(".png") else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(b).decode("utf-8")

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
    img1 = os.environ.get("FUSE_IMG1", "sample1.jpg")
    img2 = os.environ.get("FUSE_IMG2", "sample2.jpg")
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": to_data_url(img1)}},
            {"type": "image_url", "image_url": {"url": to_data_url(img2)}},
            {"type": "text", "text": "Blend these into a single realistic composition"}]
    }]
    resp = await client.create_completion(
        messages=messages,
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    img = resp.get("images")
    if isinstance(img, list):
        img = img[0] if img else None
    if img and img.get("data"):
        out = os.path.abspath("gemini_fusion.jpg")
        with open(out, "wb") as f:
            f.write(img["data"])
        print(f"Saved {out}")
    else:
        print("No image returned; response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
