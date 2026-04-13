"""Tests for audio generation and splitting."""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from ..pipeline.audio import _build_word_alignment
from ..pipeline.splitter import _compute_boundaries, _nearest_word_boundary
from ..models.scene import SceneDefinition, SceneType


# --- _build_word_alignment ---

def test_build_word_alignment_simple():
    raw = {
        "characters": list("hello world"),
        "character_start_times_seconds": [i * 0.05 for i in range(11)],
        "character_end_times_seconds": [(i + 1) * 0.05 for i in range(11)],
    }
    words = _build_word_alignment(raw)
    assert len(words) == 2
    assert words[0]["word"] == "hello"
    assert words[1]["word"] == "world"
    assert words[0]["start_time"] == 0.0


def test_build_word_alignment_empty():
    assert _build_word_alignment({}) == []


# --- _nearest_word_boundary ---

def test_nearest_word_boundary():
    alignment = [
        {"word": "hello", "start_time": 0.0, "end_time": 0.5},
        {"word": "world", "start_time": 0.5, "end_time": 1.0},
        {"word": "foo", "start_time": 1.0, "end_time": 1.5},
    ]
    # target 800ms — nearest word end is 1000ms (world ends at 1s)
    result = _nearest_word_boundary(alignment, 800)
    assert result == 1000


# --- _compute_boundaries ---

def test_compute_boundaries_produces_correct_count():
    alignment = [
        {"word": "w1", "start_time": 0.0, "end_time": 1.0},
        {"word": "w2", "start_time": 1.0, "end_time": 2.0},
        {"word": "w3", "start_time": 2.0, "end_time": 3.0},
    ]
    scene_plan = [
        SceneDefinition(scene=1, type=SceneType.avatar, duration_sec=18, content="x"),
        SceneDefinition(scene=2, type=SceneType.visual, duration_sec=20, content="y", visual_cue="img"),
        SceneDefinition(scene=3, type=SceneType.avatar, duration_sec=18, content="z"),
    ]
    boundaries = _compute_boundaries(alignment, scene_plan)
    assert len(boundaries) == 3
    # First boundary starts at 0
    assert boundaries[0][0] == 0
    # Last boundary ends at total audio ms
    assert boundaries[-1][1] == 3000


def test_compute_boundaries_fallback_no_alignment():
    scene_plan = [
        SceneDefinition(scene=1, type=SceneType.avatar, duration_sec=18, content="x"),
        SceneDefinition(scene=2, type=SceneType.avatar, duration_sec=18, content="y"),
    ]
    boundaries = _compute_boundaries([], scene_plan)
    assert len(boundaries) == 2
    assert boundaries[0] == (0, 18000)
    assert boundaries[1] == (18000, 36000)
