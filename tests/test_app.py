"""The product over HTTP, in process: what the web page calls."""

import base64
from pathlib import Path

from operonx.app import Application
from starlette.testclient import TestClient

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def test_upload_then_chat_then_the_dashboard_shows_both():
    app = Application.find(".")
    with TestClient(app.asgi()) as client:
        before = client.post("/api/dashboard", json={"client_id": "C01"}).json()["dashboard"]["net_worth"]["value"]
        content = base64.b64encode((SAMPLES / "vps_C01.csv").read_bytes()).decode()
        read = client.post("/api/statement", json={"client_id": "C01", "filename": "vps_C01.csv", "content": content})
        assert read.status_code == 200, read.text
        assert (read.json()["read"]["institution"], read.json()["read"]["count"]) == ("VPS", 3)
        said = {"client_id": "C01", "message": "Nhà tôi có 10 lượng vàng"}
        turn = client.post("/api/declare", json=said).json()["turn"]
        assert turn["recorded"][0]["data"]["qty"] == 10
        after = client.post("/api/dashboard", json={"client_id": "C01"}).json()["dashboard"]
        assert after["net_worth"]["value"] == before + read.json()["read"]["total"] + 10 * 150_000_000
        assert {s["source"]: s["status"] for s in after["sources"]}["statement"] == "connected"
        assert client.get("/samples/vps_C01.csv").status_code == 200
        assert (
            client.post("/api/statement", json={"client_id": "C01", "filename": "x.exe", "content": ""}).status_code
            == 500
        )
        assert client.post("/api/reset").json() == {"reset": True}


def test_the_specialist_team_and_the_advisory_record():
    app = Application.find(".")
    with TestClient(app.asgi()) as client:
        out = client.get("/api/advisory", params={"client_id": "C01"}).json()
        assert out["team"]["rm"]["email"] and len(out["team"]["specialists"]) == 5
        assert {a["id"] for a in out["tracking"]["agents"]} == {"news", "impact", "planner", "chat"}
        assert out["tracking"]["risk_tests"]
        assert client.get("/api/advisory", params={"client_id": "nobody"}).status_code == 404
        goals = client.post("/api/goals", json={"client_id": "C01"}).json()["goals"]
        assert goals and all("goal" in g for g in goals)
