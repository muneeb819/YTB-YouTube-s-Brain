import time

from fastapi.testclient import TestClient

from conftest import JOB_SETTLE_SECONDS
from ytb.main import app

ADMIN_EMAIL = "admin@testdev.ytb"
ADMIN_PASSWORD = "test-admin-pass"


def _admin_headers(client: TestClient) -> dict:
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "ytb"


def test_auth_flow():
    with TestClient(app) as client:
        r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
        assert r.status_code == 401

        headers = _admin_headers(client)

        r = client.post("/api/auth/register", json={"email": "new@testdev.ytb", "password": "pw12345678"})
        assert r.status_code == 201
        assert r.json()["email"] == "new@testdev.ytb"

        r = client.post("/api/auth/register", json={"email": "new@testdev.ytb", "password": "pw12345678"})
        assert r.status_code == 409

        r = client.post("/api/auth/login", json={"email": "new@testdev.ytb", "password": "pw12345678"})
        assert r.status_code == 200
        user_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = client.get("/api/auth/me", headers=user_headers)
        assert r.status_code == 200
        assert r.json()["is_admin"] is False


def test_unauthorized_access():
    with TestClient(app) as client:
        assert client.get("/api/projects").status_code == 401
        assert client.post("/api/projects", json={"name": "x"}).status_code == 401


def test_project_and_media_flow():
    with TestClient(app) as client:
        headers = _admin_headers(client)

        r = client.post("/api/projects", headers=headers, json={"name": "Project A", "brief": "brief"})
        assert r.status_code == 200
        project_id = r.json()["id"]

        r = client.get("/api/projects", headers=headers)
        assert r.status_code == 200
        assert project_id in [p["id"] for p in r.json()]

        r = client.post("/api/projects", headers=headers, json={"name": "Stay out"})
        other_id = r.json()["id"]

        fake = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 4096
        r = client.post(
            f"/api/media/upload/{project_id}",
            headers=headers,
            files={"file": ("vid.mp4", fake, "video/mp4")},
        )
        assert r.status_code == 200, r.text
        asset_id = r.json()["id"]
        assert r.json()["filename"].startswith("_") is False

        # upload must fail for projects you don't own
        r = client.post("/api/auth/register", json={"email": "other@testdev.ytb", "password": "pw12345678"})
        assert r.status_code == 201
        r = client.post("/api/auth/login", json={"email": "other@testdev.ytb", "password": "pw12345678"})
        other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        r = client.post("/api/projects", headers=other_headers, json={"name": "Not admin's"})
        assert r.status_code == 200
        foreign_project_id = r.json()["id"]

        r = client.post(
            f"/api/media/upload/{foreign_project_id}",
            headers=headers,
            files={"file": ("vid.mp4", fake, "video/mp4")},
        )
        assert r.status_code == 404

        # rights status update
        r = client.post(f"/api/media/{asset_id}/rights", headers=headers, json={"status": "BLOCKED"})
        assert r.status_code == 200
        assert r.json()["rights_status"] == "BLOCKED"

        # preflight summary reflects the blocked asset
        r = client.get(f"/api/projects/{project_id}/preflight", headers=headers)
        assert r.status_code == 200
        assert r.json()["verdict"] == "BLOCK"

        # download source
        r = client.get(f"/api/media/{asset_id}/download", headers=headers)
        assert r.status_code == 200

        # asset + job listing endpoints
        r = client.get(f"/api/projects/{project_id}/assets", headers=headers)
        assert r.status_code == 200
        assert [a["id"] for a in r.json()] == [asset_id]

        r = client.get(f"/api/projects/{project_id}/jobs", headers=headers)
        assert r.status_code == 200 and isinstance(r.json(), list)

        r = client.get(f"/api/projects/999999/assets", headers=headers)
        assert r.status_code == 404


def test_render_validation_and_preflight_gate():
    with TestClient(app) as client:
        headers = _admin_headers(client)

        r = client.post("/api/projects", headers=headers, json={"name": "Render Project"})
        assert r.status_code == 200
        project_id = r.json()["id"]

        fake = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 4096
        r = client.post(
            f"/api/media/upload/{project_id}",
            headers=headers,
            files={"file": ("vid.mp4", fake, "video/mp4")},
        )
        assert r.status_code == 200
        asset_id = r.json()["id"]

        # negative inputs must be rejected
        r = client.post(
            "/api/jobs/render",
            headers=headers,
            json={"project_id": project_id, "asset_id": asset_id, "start": -1, "duration": -2},
        )
        assert r.status_code == 422

        # blocked asset must not render
        client.post(f"/api/media/{asset_id}/rights", headers=headers, json={"status": "BLOCKED"})
        r = client.post(
            "/api/jobs/render",
            headers=headers,
            json={"project_id": project_id, "asset_id": asset_id, "start": 0},
        )
        assert r.status_code == 403

        # compliant asset can queue a render
        client.post(f"/api/media/{asset_id}/rights", headers=headers, json={"status": "COMPLIANT"})
        r = client.post(
            "/api/jobs/render",
            headers=headers,
            json={"project_id": project_id, "asset_id": asset_id, "start": 0, "duration": 1},
        )
        # ffmpeg may be missing on CI; the render should either complete or fail cleanly
        assert r.status_code == 200, r.text
        job_id = r.json()["job_id"]

        time.sleep(JOB_SETTLE_SECONDS)
        r = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["state"] in ("COMPLETED", "FAILED")

        # download of a non-completed output is 404 when there is no output yet
        if r.json()["state"] != "COMPLETED":
            d = client.get(f"/api/jobs/{job_id}/download", headers=headers)
            assert d.status_code == 404
        else:
            assert r.json()["output"].get("path")

        # foreign job access
        r = client.get("/api/jobs/999999", headers=headers)
        assert r.status_code == 404