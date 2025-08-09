from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_stub():
    r = client.post("/chat", json={"message": "Hello"})
    assert r.status_code == 200
    assert "You said" in r.json()["reply"]


def test_upload_and_analyze_flow():
    csv_content = b"a,b\n1,2\n3,4\n"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    r = client.post("/upload-csv", files=files)
    assert r.status_code == 200
    data = r.json()
    session_id = data["sessionId"]
    assert data["columns"] == ["a", "b"]

    r2 = client.post(
        "/analyze", json={"sessionId": session_id, "question": "row count"}
    )
    assert r2.status_code == 200
    assert "Rows:" in r2.json()["answer"]

    # Chart generation
    r3 = client.post("/analyze", json={"sessionId": session_id, "question": "chart"})
    assert r3.status_code == 200
    data3 = r3.json()
    # chart may fail if matplotlib missing; ensure key present when answer indicates generation
    if "histogram" in data3["answer"].lower():
        assert "chart" in (data3.get("artifacts") or {})
