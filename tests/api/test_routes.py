"""API endpoint unit and integration tests."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """GET /health should return 200 OK and status 'healthy'."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_ready_endpoint(client: TestClient):
    """GET /ready should return 200 OK, model_ready True, and telemetry."""
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["model_ready"] is True
    assert "model_info" in data
    assert "system" in data


def test_metrics_endpoint(client: TestClient):
    """GET /metrics should expose Prometheus text metrics."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "moderation_requests_total" in resp.text
    assert "moderation_latency_seconds" in resp.text


def test_moderate_allow(client: TestClient):
    """POST /moderate on benign text yields 'allow' decision."""
    payload = {
        "text": "Hope you have an awesome weekend with your family!",
        "text_id": "test-allow-100",
    }
    resp = client.post("/moderate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["text_id"] == "test-allow-100"
    assert data["decision"] == "allow"
    assert data["label"] == "non_toxic"
    assert data["confidence"] > 0.90
    assert data["inference_ms"] > 0.0
    assert data["total_latency_ms"] > 0.0


def test_moderate_block(client: TestClient):
    """POST /moderate on toxic text yields 'block' decision and policy tags."""
    payload = {
        "text": "You are a complete idiot, moron, and loser.",
        "text_id": "test-block-200",
    }
    resp = client.post("/moderate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["text_id"] == "test-block-200"
    assert data["decision"] == "block"
    assert data["label"] == "toxic"
    assert data["confidence"] > 0.90
    assert "insult" in data["policy_categories"]


def test_moderate_threat_violation(client: TestClient):
    """POST /moderate on explicit threat triggers threat category."""
    payload = {
        "text": "I am going to hunt you down and destroy you.",
        "text_id": "test-threat-300",
    }
    resp = client.post("/moderate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "block"
    assert "threat" in data["policy_categories"]


def test_moderate_request_id_propagation(client: TestClient):
    """Custom X-Request-ID header should be mirrored in response headers."""
    custom_id = "req-tracing-abc-123"
    resp = client.post(
        "/moderate",
        json={"text": "Hello world!"},
        headers={"X-Request-ID": custom_id},
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id


def test_moderate_batch(client: TestClient):
    """POST /moderate/batch processes multiple items in vector fashion."""
    items = [
        {"text": "Have a wonderful morning!", "text_id": "b-1"},
        {"text": "You are a stupid clown.", "text_id": "b-2"},
        {"text": "Please kill -9 the process.", "text_id": "b-3"},
    ]
    resp = client.post("/moderate/batch", json={"items": items})
    assert resp.status_code == 200
    data = resp.json()
    assert data["batch_size"] == 3
    assert len(data["results"]) == 3
    assert data["results"][0]["decision"] == "allow"
    assert data["results"][1]["decision"] == "block"
    assert data["results"][2]["decision"] == "allow"


def test_validation_errors(client: TestClient):
    """Validation errors return 422 Unprocessable Entity."""
    # 1. Missing text
    resp = client.post("/moderate", json={})
    assert resp.status_code == 422

    # 2. Empty text
    resp = client.post("/moderate", json={"text": ""})
    assert resp.status_code == 422

    # 3. Text exceeds 10,000 characters
    resp = client.post("/moderate", json={"text": "a" * 10001})
    assert resp.status_code == 422

    # 4. Batch exceeds 100 items
    huge_batch = [{"text": f"item {i}"} for i in range(101)]
    resp = client.post("/moderate/batch", json={"items": huge_batch})
    assert resp.status_code == 422
