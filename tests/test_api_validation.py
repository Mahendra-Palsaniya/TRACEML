"""API validation regression tests; substitute compute before importing main."""
import importlib
import sys
import types

from fastapi.testclient import TestClient


def build_client(monkeypatch):
    fake = types.ModuleType("compute")
    fake.moe = None
    fake.model_status = lambda: {"vae": "ready", "moe": "unavailable"}
    fake.predict = lambda rows: (_ for _ in ()).throw(ValueError("Missing required features"))
    fake.vae_feature_names = ["required"]
    fake.PIPELINE = types.SimpleNamespace(moe=None)
    monkeypatch.setitem(sys.modules, "compute", fake)
    fake_llm = types.ModuleType("llm")
    fake_llm.summarize_alert = lambda *_: {}
    monkeypatch.setitem(sys.modules, "llm", fake_llm)
    sys.modules.pop("main", None)
    app = importlib.import_module("main").app
    return TestClient(app)


def test_invalid_row_returns_422(monkeypatch):
    client = build_client(monkeypatch)
    response = client.post("/predict", json={"row": {}})
    assert response.status_code == 422
    assert "Missing required features" in response.json()["detail"]


def test_invalid_batch_returns_422(monkeypatch):
    client = build_client(monkeypatch)
    response = client.post("/analyze-batch", json={"rows": [{}]})
    assert response.status_code == 422


def test_summarize_rejects_non_objects(monkeypatch):
    client = build_client(monkeypatch)
    response = client.post("/summarize", json={"llm_payload": [], "model_output": {}})
    assert response.status_code == 422


def test_health_reports_degraded(monkeypatch):
    client = build_client(monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
