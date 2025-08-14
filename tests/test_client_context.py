import json
import importlib.util
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_proxy_core import CompletionClient


def load_completions_router():
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "api_layer" / "completions.py"
    spec = importlib.util.spec_from_file_location("completions_mod", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.router


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(load_completions_router())
    return app


@pytest.mark.asyncio
async def test_client_context_ip_fallback_no_client_id(monkeypatch):
    captured: Dict[str, Any] = {}

    async def fake_create_completion(self, messages, model, **kwargs):
        captured["client_context"] = kwargs.get("client_context")
        return {
            "id": "test-1",
            "created": 0,
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": None,
        }

    monkeypatch.setattr(CompletionClient, "create_completion", fake_create_completion)

    client = TestClient(make_app())

    payload = {
        "model": "gemini-1.5-flash",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    resp = client.post("/chat/completions", json=payload)
    assert resp.status_code == 200
    ctx = captured.get("client_context")
    assert ctx is not None
    assert ctx.get("ip") is not None
    assert ctx.get("client_id") == ctx.get("ip")


@pytest.mark.asyncio
async def test_client_context_body_overrides_headers(monkeypatch):
    captured: Dict[str, Any] = {}

    async def fake_create_completion(self, messages, model, **kwargs):
        captured["client_context"] = kwargs.get("client_context")
        return {
            "id": "test-2",
            "created": 0,
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": None,
        }

    monkeypatch.setattr(CompletionClient, "create_completion", fake_create_completion)

    client = TestClient(make_app())

    payload = {
        "model": "gemini-1.5-flash",
        "messages": [{"role": "user", "content": "Hello"}],
        "client_id": "body_id",
    }
    headers = {"X-Client-Id": "header_id"}
    resp = client.post("/chat/completions", json=payload, headers=headers)
    assert resp.status_code == 200
    ctx = captured.get("client_context")
    assert ctx is not None
    assert ctx.get("client_id") == "body_id"
