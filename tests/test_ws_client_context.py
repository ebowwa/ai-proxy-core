import asyncio
import importlib.util
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def load_ws_router():
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "api_layer" / "gemini_live.py"
    spec = importlib.util.spec_from_file_location("gemini_ws_mod", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.router


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(load_ws_router())
    return app


class FakeSession:
    async def send(self, *args, **kwargs):
        return None

    def receive(self):
        async def _gen():
            while True:
                await asyncio.sleep(0.05)
                if False:
                    yield None
        return _gen()


class FakeConnectCtx:
    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeLive:
    def connect(self, *args, **kwargs):
        return FakeConnectCtx()


class FakeAio:
    def __init__(self):
        self.live = FakeLive()


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.aio = FakeAio()


@pytest.mark.asyncio
async def test_ws_config_ip_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")

    import google.genai as genai  # type: ignore
    monkeypatch.setattr(genai, "Client", FakeClient)

    app = make_app()
    client = TestClient(app)

    with client.websocket_connect("/gemini/ws") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "system"

        ws.send_json({"type": "config", "data": {"app": "test-cli"}})
        ack = ws.receive_json()
        assert ack["type"] == "config_success"
        assert ack.get("ip") is not None
        assert ack.get("client_id") == ack.get("ip")
