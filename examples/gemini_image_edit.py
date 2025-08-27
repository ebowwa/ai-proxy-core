import base64
import os
import asyncio
from ai_proxy_core import CompletionClient

def to_data_url(img_path: str) -> str:
    with open(img_path, "rb") as f:
        b = f.read()
    return "data:image/jpeg;base64," + base64.b64encode(b).decode("utf-8")

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
    image_path = os.environ.get("EDIT_IMAGE_PATH", "sample.jpg")
    data_url = to_data_url(image_path)
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": "Remove the background and add a soft shadow"}
        ]
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
        out = os.path.abspath("gemini_edit.jpg")
        with open(out, "wb") as f:
            f.write(img["data"])
        print(f"Saved {out}")
    else:
        print("No image returned; response:", resp)

if __name__ == "__main__":
    asyncio.run(main())
