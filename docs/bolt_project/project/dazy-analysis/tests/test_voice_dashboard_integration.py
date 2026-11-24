import os
import time
import pytest
from fastapi.testclient import TestClient
from dashboard.server import DashboardServer

def test_upgraded_app_html_elements():
    html_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "static", "app.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert "id=\"dazyOrb\"" in html
    assert "data-state=\"idle\"" in html
    assert "id=\"orbWaveform\"" in html
    assert "id=\"liveTranscriptBanner\"" in html
    assert "id=\"liveTranscriptText\"" in html
    assert "id=\"micWaveCanvas\"" in html
    assert "id=\"selfTestCard\"" in html
    assert "runVoiceSelfTest()" in html
    assert "updateVoiceState" in html
    assert "triggerBargeIn" in html

def test_voice_self_test_api_endpoint():
    server = DashboardServer()
    client = TestClient(server.app)
    token = "test_token_123"
    server._tokens[token] = time.time()

    res = client.post("/api/voice-self-test", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "microphone_ready" in data
    assert "stt_engine" in data
    assert "llm_provider" in data
    assert "tts_engine" in data
    assert "vad_engine" in data
    assert data["overall_status"] == "HEALTHY"

def test_interrupt_callback_wiring():
    server = DashboardServer()
    interrupted = False

    def on_interrupt():
        nonlocal interrupted
        interrupted = True

    server.set_interrupt_callback(on_interrupt)
    assert server._interrupt_callback is not None
    server._interrupt_callback()
    assert interrupted is True
