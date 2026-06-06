"""
Flask API — serves cognitive load data to the dashboard frontend.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
from collector.database import get_connection

app = Flask(__name__)
CORS(app)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/today")
def today():
    """Return today's feature windows for the timeline chart."""
    import time
    from datetime import datetime, timedelta
    today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT window_start, window_end, wpm, backspace_ratio,
               mean_iki_ms, anomaly_score, fatigue_level, total_keystrokes
        FROM feature_windows
        WHERE window_start >= ?
        ORDER BY window_start ASC
    """, conn, params=(today_start,))
    conn.close()

    return jsonify(df.to_dict(orient="records"))


@app.route("/api/weekly")
def weekly():
    """Return last 7 days aggregated by day."""
    import time
    week_ago = time.time() - (7 * 86400)

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT window_start, fatigue_level, anomaly_score, wpm
        FROM feature_windows
        WHERE window_start >= ?
        ORDER BY window_start ASC
    """, conn, params=(week_ago,))
    conn.close()

    return jsonify(df.to_dict(orient="records"))


@app.route("/api/alerts")
def alerts():
    """Return recent alerts."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 20
    """, conn)
    conn.close()
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/stats/summary")
def summary():
    """High-level stats for the summary cards."""
    import time
    today_start = time.time() - 86400

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT fatigue_level, COUNT(*) as count, AVG(wpm) as avg_wpm,
               AVG(anomaly_score) as avg_score
        FROM feature_windows
        WHERE window_start >= ?
        GROUP BY fatigue_level
    """, conn, params=(today_start,))
    conn.close()

    return jsonify(df.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
