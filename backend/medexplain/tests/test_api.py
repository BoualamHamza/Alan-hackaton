"""End-to-end API tests using FastAPI TestClient with all external services mocked."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---- /extract ----

@patch("api.routes.extract.extract")
def test_extract_endpoint(mock_extract, sample_pdo):
    mock_extract.return_value = sample_pdo
    response = client.post("/extract", json={"report_text": "Compte rendu médical..."})
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["first_name"] == "Jean-Paul"


def test_extract_empty_report():
    response = client.post("/extract", json={"report_text": "   "})
    assert response.status_code == 422


# ---- /review/approve ----

def test_review_approve(sample_pdo):
    sample_pdo.doctor_approved = False
    sample_pdo.extraction_metadata.requires_doctor_review = False
    response = client.post("/review/approve", json={"pdo": sample_pdo.model_dump()})
    assert response.status_code == 200
    assert response.json()["doctor_approved"] is True


def test_review_approve_rejects_invalid_pdo(sample_pdo):
    # Remove visual_cue from a visual scene
    pdo_data = sample_pdo.model_dump()
    for s in pdo_data["video_1_disease"]["scene_plan"]:
        if s["type"] == "visual":
            s["visual_cue"] = None
            break
    pdo_data["doctor_approved"] = False
    pdo_data["extraction_metadata"]["requires_doctor_review"] = False
    response = client.post("/review/approve", json={"pdo": pdo_data})
    assert response.status_code == 422


# ---- /review/correct ----

def test_review_correct(sample_pdo):
    sample_pdo.doctor_approved = False
    sample_pdo.extraction_metadata.requires_doctor_review = False
    response = client.post(
        "/review/correct",
        json={
            "pdo": sample_pdo.model_dump(),
            "corrections": {"video_1_disease.severity.level": "mild"},
        },
    )
    assert response.status_code == 200
    assert response.json()["video_1_disease"]["severity"]["level"] == "mild"


# ---- /generate ----

@patch("api.routes.generate.run_pipeline")
@patch("api.routes.generate.generate_script")
def test_generate_endpoint(mock_generate_script, mock_run_pipeline, sample_pdo):
    mock_generate_script.side_effect = [
        ([(1, "narration 1")], "narration 1"),
        ([(1, "narration 2")], "narration 2"),
    ]
    mock_run_pipeline.return_value = (
        AsyncMock(return_value=("/output/video_1.mp4", "/output/video_2.mp4"))()
    )
    # Make it awaitable
    import asyncio
    async def fake_run(*args, **kwargs):
        return "/output/video_1.mp4", "/output/video_2.mp4"
    mock_run_pipeline.side_effect = fake_run

    response = client.post("/generate", json={"pdo": sample_pdo.model_dump()})
    assert response.status_code == 200
    data = response.json()
    assert "video_1_path" in data
    assert "video_2_path" in data


def test_generate_requires_approved_pdo(sample_pdo):
    sample_pdo.doctor_approved = False
    response = client.post("/generate", json={"pdo": sample_pdo.model_dump()})
    assert response.status_code == 422
    assert "approved" in response.json()["detail"].lower()
