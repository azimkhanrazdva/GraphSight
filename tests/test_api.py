from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from apps.api.graphsight_api.main import app


def test_upload_analyze_query(tmp_path: Path) -> None:
    image_path = tmp_path / "network.png"
    Image.new("RGB", (900, 420), "white").save(image_path)
    client = TestClient(app)

    with image_path.open("rb") as handle:
        upload = client.post("/api/v1/documents", files={"file": ("network.png", handle, "image/png")})

    assert upload.status_code == 200
    document_id = upload.json()["document"]["id"]

    analyze = client.post(f"/api/v1/documents/{document_id}/analyze")
    assert analyze.status_code == 200
    job_id = analyze.json()["job_id"]
    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "completed"

    query = client.post(
        f"/api/v1/graphs/{document_id}/query",
        json={"question": "What path connects Router A to Server C?"},
    )
    assert query.json()["answer"] == "Router A -> Firewall B -> Server C"

