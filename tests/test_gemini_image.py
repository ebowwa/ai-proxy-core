import os
import base64
import asyncio
import pytest

from ai_proxy_core import CompletionClient

run_live = os.getenv("RUN_GEMINI_IMAGE_TESTS") == "1"

requires_key = pytest.mark.skipif(
    not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
    reason="GEMINI_API_KEY/GOOGLE_API_KEY not set"
)

requires_live = pytest.mark.skipif(
    not run_live,
    reason="Set RUN_GEMINI_IMAGE_TESTS=1 to run live Gemini image tests"
)

def _is_gemini_image_model_available() -> bool:
    try:
        from google import genai  # type: ignore
        client = genai.Client()
        try:
            names = []
            for m in client.models.list():
                n = getattr(m, "name", None) or getattr(m, "model", None) or str(m)
                if isinstance(n, str):
                    names.append(n)
            return any("gemini-2.5-flash-image" in n for n in names)
        except Exception:
            try:
                client.models.get(model="models/gemini-2.5-flash-image-preview")
                return True
            except Exception:
                return False
    except Exception:
        return False

requires_model = pytest.mark.skipif(
    not _is_gemini_image_model_available(),
    reason="Gemini 2.5 Flash Image model not available on this API key/project; requires preview/special access"
)

def data_url_from_bytes(b: bytes, mime="image/jpeg") -> str:
    return f"data:{mime};base64," + base64.b64encode(b).decode("utf-8")

@requires_key
@requires_live
@requires_model
@pytest.mark.asyncio
async def test_routing_to_gemini():
    client = CompletionClient()
    resp = await client.create_completion(
        messages=[{"role": "user", "content": "simple prompt"}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    assert "model" in resp
    assert resp["model"].startswith("gemini-2.5-flash-image")

@requires_key
@requires_live
@requires_model
@pytest.mark.asyncio
async def test_text_to_image_generates_image():
    client = CompletionClient()
    resp = await client.create_completion(
        messages=[{"role": "user", "content": "A banana on a desk"}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    img = resp.get("images")
    if isinstance(img, list):
        assert len(img) >= 1
        img = img[0]
    assert img and isinstance(img.get("data"), (bytes, bytearray)) and len(img["data"]) > 0

@requires_key
@requires_live
@requires_model
@pytest.mark.asyncio
async def test_edit_image_returns_image(tmp_path):
    sample_bytes = b"\x89PNG\r\n\x1a\n" + os.urandom(128)
    data_url = data_url_from_bytes(sample_bytes, mime="image/png")
    client = CompletionClient()
    resp = await client.create_completion(
        messages=[{"role":"user","content":[
            {"type":"image_url","image_url":{"url": data_url}},
            {"type":"text","text":"Add a soft shadow"}]}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    img = resp.get("images")
    if isinstance(img, list):
        img = img[0] if img else None
    assert img and isinstance(img.get("data"), (bytes, bytearray)) and len(img["data"]) > 0

@requires_key
@requires_live
@requires_model
@pytest.mark.asyncio
async def test_multi_image_fusion_returns_image():
    b1 = b"\x89PNG\r\n\x1a\n" + os.urandom(128)
    b2 = b"\x89PNG\r\n\x1a\n" + os.urandom(128)
    data1 = data_url_from_bytes(b1, mime="image/png")
    data2 = data_url_from_bytes(b2, mime="image/png")
    client = CompletionClient()
    resp = await client.create_completion(
        messages=[{"role":"user","content":[
            {"type":"image_url","image_url":{"url": data1}},
            {"type":"image_url","image_url":{"url": data2}},
            {"type":"text","text":"Blend into one realistic photo"}
        ]}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    img = resp.get("images")
    if isinstance(img, list):
        img = img[0] if img else None
    assert img and isinstance(img.get("data"), (bytes, bytearray)) and len(img["data"]) > 0

@requires_key
@requires_live
@requires_model
@pytest.mark.asyncio
async def test_nonbreaking_response_shape():
    client = CompletionClient()
    resp = await client.create_completion(
        messages=[{"role":"user","content":"Generate a banana icon"}],
        model="gemini-2.5-flash-image-preview",
        return_images=True,
    )
    assert "choices" in resp and isinstance(resp["choices"], list)
    assert "message" in resp["choices"][0] and "content" in resp["choices"][0]["message"]
    assert "images" in resp
