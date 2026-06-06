"""
Feature Extractor — converts raw keystroke events into ML-ready feature vectors.
Processes data in 5-minute windows.
"""

import time
import numpy as np
import pandas as pd
from loguru import logger

from collector.database import get_connection

WINDOW_SECONDS = 300  # 5 minutes
BURST_GAP_THRESHOLD_MS = 3000   # gap > 3s = new burst or idle
IDLE_GAP_THRESHOLD_MS = 3000    # gap > 3s = idle period


def extract_window_features(window_start: float, window_end: float) -> dict | None:
    """
    Extract features from keystroke events in a given time window.
    Returns a feature dict or None if insufficient data.
    """
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT timestamp, iki_ms, is_backspace, active_app
        FROM keystroke_events
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp ASC
    """, conn, params=(window_start, window_end))
    conn.close()

    if len(df) < 10:
        logger.debug(f"Skipping window — only {len(df)} events (need >= 10)")
        return None

    ikis = df['iki_ms'].dropna()
    total_keys = len(df)
    backspaces = df['is_backspace'].sum()

    # WPM: assume avg word = 5 keystrokes
    duration_minutes = (window_end - window_start) / 60
    wpm = (total_keys / 5) / duration_minutes if duration_minutes > 0 else 0

    # Burst analysis
    burst_count = 0
    idle_gap_count = 0
    for iki in ikis:
        if iki > BURST_GAP_THRESHOLD_MS:
            burst_count += 1
        if iki > IDLE_GAP_THRESHOLD_MS:
            idle_gap_count += 1

    features = {
        "window_start": window_start,
        "window_end": window_end,
        "mean_iki_ms": float(ikis.mean()) if len(ikis) > 0 else 0.0,
        "std_iki_ms": float(ikis.std()) if len(ikis) > 1 else 0.0,
        "wpm": round(wpm, 2),
        "backspace_ratio": round(backspaces / total_keys, 4) if total_keys > 0 else 0.0,
        "burst_count": int(burst_count),
        "idle_gap_count": int(idle_gap_count),
        "total_keystrokes": int(total_keys),
    }

    logger.debug(f"Features extracted: {features}")
    return features


def save_feature_window(features: dict, anomaly_score: float = None, fatigue_level: str = None):
    """Persist feature window to DB."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO feature_windows
        (window_start, window_end, mean_iki_ms, std_iki_ms, wpm,
         backspace_ratio, burst_count, idle_gap_count, total_keystrokes,
         anomaly_score, fatigue_level)
        VALUES
        (:window_start, :window_end, :mean_iki_ms, :std_iki_ms, :wpm,
         :backspace_ratio, :burst_count, :idle_gap_count, :total_keystrokes,
         :anomaly_score, :fatigue_level)
    """, {**features, "anomaly_score": anomaly_score, "fatigue_level": fatigue_level})
    conn.commit()
    conn.close()


def run_extraction_cycle():
    """Extract features for the last completed 5-minute window."""
    now = time.time()
    window_end = now - (now % WINDOW_SECONDS)      # floor to last 5-min boundary
    window_start = window_end - WINDOW_SECONDS

    features = extract_window_features(window_start, window_end)
    if features:
        save_feature_window(features)
        logger.info(f"✅ Feature window saved: WPM={features['wpm']}, backspace_ratio={features['backspace_ratio']}")
    return features


if __name__ == "__main__":
    result = run_extraction_cycle()
    if result:
        print("Feature window:", result)
    else:
        print("Not enough data yet. Keep typing for 5 minutes and try again.")
