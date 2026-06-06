"""
Unit tests for feature extractor.
Run with: pytest tests/
"""

import pytest
from features.extractor import extract_window_features
from model.detector import predict_fatigue, _rule_based_fallback


def test_rule_based_healthy():
    features = {
        "mean_iki_ms": 150,
        "std_iki_ms": 80,
        "wpm": 60,
        "backspace_ratio": 0.04,
        "burst_count": 5,
        "idle_gap_count": 2,
    }
    score, level = _rule_based_fallback(features)
    assert level == "low"
    assert score > 0.6


def test_rule_based_fatigued():
    features = {
        "mean_iki_ms": 600,
        "std_iki_ms": 500,
        "wpm": 10,
        "backspace_ratio": 0.30,
        "burst_count": 20,
        "idle_gap_count": 15,
    }
    score, level = _rule_based_fallback(features)
    assert level in ("medium", "high")
    assert score < 0.6


def test_fatigue_levels():
    from model.detector import score_to_fatigue_level
    assert score_to_fatigue_level(0.8) == "low"
    assert score_to_fatigue_level(0.45) == "medium"
    assert score_to_fatigue_level(0.1) == "high"
