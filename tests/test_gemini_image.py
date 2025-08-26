import os
import base64
import asyncio
import pytest

from ai_proxy_core import CompletionClient

requires_key = pytest.mark.skipif(
    not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
    reason="GEMINI_API_KEY/GOOGLE_API_KEY not set"
)

def data_url_from_bytes(b: bytes, mime="image/jpeg") -> str:
    return f"data:{mime};base64," + base64.b64encode(b).decode("utf-8")

@requires_key
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
@pytest.mark.asyncio
async def test_edit_image_returns_image(tmp_path):
    sample_bytes = b"\xff\xd8\xff\xdb" + os.urandom(128) + b"\xff\xd9"
    data_url = data_url_from_bytes(sample_bytes, mime="image/jpeg")
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
@pytest.mark.asyncio
async def test_multi_image_fusion_returns_image():
    b1 = b"\xff\xd8\xff\xdb" + os.urandom(128) + b"\xff\xd9"
    b2 = b"\xff\xd8\xff\xdb" + os.urandom(128) + b"\xff\xd9"
    data1 = data_url_from_bytes(b1, mime="image/jpeg")
    data2 = data_url_from_bytes(b2, mime="image/jpeg")
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
