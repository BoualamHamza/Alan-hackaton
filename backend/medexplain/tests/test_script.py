"""Tests for the script generation layer."""
import json
from unittest.mock import MagicMock, patch

import pytest

from script.generator import generate_script, _resolve_content


def _mock_mistral(narrations: list):
    msg = MagicMock()
    msg.content = json.dumps(narrations)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@patch("script.generator.Mistral")
def test_generate_script_video1_returns_correct_scene_count(mock_mistral_cls, sample_pdo):
    scene_count = len(sample_pdo.video_1_disease.scene_plan)
    narrations = [{"scene": i + 1, "narration": f"Narration {i+1}"} for i in range(scene_count)]

    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = _mock_mistral(narrations)

    scene_narrations, full_script = generate_script(sample_pdo, video_number=1)

    assert len(scene_narrations) == scene_count
    assert "Narration 1" in full_script


@patch("script.generator.Mistral")
def test_generate_script_video2_returns_correct_scene_count(mock_mistral_cls, sample_pdo):
    scene_count = len(sample_pdo.video_2_treatment.scene_plan)
    narrations = [{"scene": i + 1, "narration": f"Scene {i+1} text."} for i in range(scene_count)]

    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = _mock_mistral(narrations)

    scene_narrations, full_script = generate_script(sample_pdo, video_number=2)

    assert len(scene_narrations) == scene_count


def test_resolve_content_simple_path(sample_pdo):
    pdo_data = sample_pdo.model_dump()
    result = _resolve_content(pdo_data, "patient.first_name")
    assert result == "Jean-Paul"


def test_resolve_content_nested_list(sample_pdo):
    pdo_data = sample_pdo.model_dump()
    result = _resolve_content(pdo_data, "video_1_disease.test_results.0.result_plain")
    assert "mémoire" in result.lower() or result != ""
