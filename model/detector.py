"""
Cognitive Load Detector using Isolation Forest (anomaly detection).
No labeled data needed — trains on YOUR normal typing baseline.
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from loguru import logger
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from collector.database import get_connection

MODEL_PATH = Path(__file__).parent / "isolation_forest.pkl"
SCALER_PATH = Path(__file__).parent / "scaler.pkl"

FEATURE_COLS = [
    "mean_iki_ms",
    "std_iki_ms",
    "wpm",
    "backspace_ratio",
    "burst_count",
    "idle_gap_count",
]


def load_training_data() -> pd.DataFrame:
    """Load all feature windows from DB for training."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM feature_windows
        ORDER BY window_start ASC
    """, conn)
    conn.close()
    return df


def train_model(contamination: float = 0.1):
    """
    Train Isolation Forest on collected baseline data.
    contamination = expected fraction of anomalous sessions (10% default).
    Call this after collecting ~3 days of data.
    """
    df = load_training_data()

    if len(df) < 20:
        logger.warning(f"Only {len(df)} windows available. Need at least 20 to train.")
        return None

    X = df[FEATURE_COLS].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Persist model and scaler
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    logger.info(f"✅ Model trained on {len(df)} windows and saved to {MODEL_PATH}")
    return model, scaler


def load_model():
    """Load trained model and scaler from disk."""
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        logger.warning("No trained model found. Run train_model() first.")
        return None, None

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def score_to_fatigue_level(score: float) -> str:
    """
    Convert anomaly score to human-readable fatigue level.
    Isolation Forest returns: -1 (anomaly) or 1 (normal).
    decision_function returns raw score — more negative = more anomalous.
    We normalize to 0–1 range.
    """
    if score >= 0.6:
        return "low"
    elif score >= 0.3:
        return "medium"
    else:
        return "high"


def predict_fatigue(features: dict) -> tuple[float, str]:
    """
    Given a feature dict, return (anomaly_score 0-1, fatigue_level).
    Falls back to rule-based scoring if model not trained yet.
    """
    model, scaler = load_model()

    if model is None:
        # Rule-based fallback (Week 1 bootstrap)
        return _rule_based_fallback(features)

    X = np.array([[features[col] for col in FEATURE_COLS]])
    X_scaled = scaler.transform(X)

    raw_score = model.decision_function(X_scaled)[0]
    # Normalize: typical range is roughly -0.5 to 0.5
    normalized = (raw_score + 0.5) / 1.0
    normalized = float(np.clip(normalized, 0.0, 1.0))

    fatigue_level = score_to_fatigue_level(normalized)
    return normalized, fatigue_level


def _rule_based_fallback(features: dict) -> tuple[float, str]:
    """
    Simple threshold-based fallback before model is trained.
    Used during the first few days of data collection.
    """
    score = 1.0  # start healthy

    if features["backspace_ratio"] > 0.15:
        score -= 0.3
    if features["mean_iki_ms"] > 400:
        score -= 0.2
    if features["std_iki_ms"] > 300:
        score -= 0.2
    if features["wpm"] < 20:
        score -= 0.2
    if features["idle_gap_count"] > 10:
        score -= 0.1

    score = max(0.0, score)
    return round(score, 3), score_to_fatigue_level(score)


if __name__ == "__main__":
    print("Training model on collected data...")
    result = train_model()
    if result:
        print("✅ Model trained successfully.")
    else:
        print("⚠️  Not enough data yet. Collect more sessions first.")
