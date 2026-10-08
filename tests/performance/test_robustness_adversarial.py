"""Robustness, adversarial, and edge-case testing suite (Phase 12)."""

from fastapi.testclient import TestClient


def test_adversarial_zero_width_spaces(client: TestClient):
    """Text with zero-width spaces attempting to evade tokenization."""
    # Obfuscated toxic phrase with \u200B zero-width spaces
    adversarial_text = "y\u200bo\u200bu\u200b \u200ba\u200br\u200be\u200b \u200ba\u200bn\u200b \u200bi\u200bd\u200bi\u200bo\u200bt"
    resp = client.post("/moderate", json={"text": adversarial_text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "block"
    assert data["label"] == "toxic"


def test_adversarial_excessive_repeated_characters(client: TestClient):
    """Excessive character repetitions (e.g. 'baaaaaaad') should be handled without crashing."""
    text = "You are a suuuuuper stuuuupid clooown and a reeeepulsive looooser"
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "block"


def test_adversarial_mixed_casing(client: TestClient):
    """SpongeBob-style alternating mixed casing."""
    text = "yOu ArE a CoMpLeTe IdIoT aNd A mOrOn"
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "block"


def test_edge_case_emojis_and_unicode(client: TestClient):
    """Text with diverse Unicode emojis and special characters."""
    text = "Have a great day! 🌟🎉 Good luck with the deployment! 🚀"
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"


def test_edge_case_code_and_shell_commands(client: TestClient):
    """Benign technical code snippets containing apparent violence/destructive verbs."""
    text = "To gracefully stop the worker process, run kill -TERM $PID or terminate thread."
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"


def test_edge_case_sql_and_script_injection(client: TestClient):
    """SQL injection / script attempts should be parsed cleanly without error."""
    text = "<script>alert('xss')</script> OR 1=1; DROP TABLE users;--"
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    assert "decision" in resp.json()


def test_edge_case_near_max_payload(client: TestClient):
    """Payload close to the maximum allowed boundary (9,500 characters)."""
    text = "Benign discussion text. " * 380  # ~9,120 chars
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"


def test_edge_case_multilingual_benign(client: TestClient):
    """Benign multilingual greetings should be processed stably without server error."""
    text = "Bonjour tout le monde! ¡Buenos días! Guten Tag! こんにちは!"
    resp = client.post("/moderate", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert "decision" in data
    assert "confidence" in data
