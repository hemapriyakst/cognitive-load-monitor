"""
main.py — Entry point for the Cognitive Load Monitor.
Starts all components: collector, feature extractor, ML scorer, and alert system.
"""

import time
import schedule
from loguru import logger

from collector.keystroke_collector import start_collector, flush_buffer_to_db
from features.extractor import run_extraction_cycle
from model.detector import predict_fatigue, train_model
from alerts.notifier import evaluate_and_alert
from collector.database import initialize_db

# Configure logging
logger.add("data/app.log", rotation="1 week", retention="4 weeks", level="INFO")


def run_pipeline():
    """
    Full pipeline: extract features → score → alert.
    Runs every 5 minutes.
    """
    logger.info("⚙️  Running pipeline cycle...")

    features = run_extraction_cycle()
    if features is None:
        logger.info("Not enough data for this window. Waiting...")
        return

    score, fatigue_level = predict_fatigue(features)
    features_with_score = {**features, "anomaly_score": score, "fatigue_level": fatigue_level}

    from features.extractor import save_feature_window
    # Update the already saved window with score
    conn = __import__('collector.database', fromlist=['get_connection']).get_connection()
    conn.execute("""
        UPDATE feature_windows
        SET anomaly_score = ?, fatigue_level = ?
        WHERE window_start = ?
    """, (score, fatigue_level, features["window_start"]))
    conn.commit()
    conn.close()

    logger.info(f"📊 Score: {score:.3f} | Fatigue: {fatigue_level.upper()} | WPM: {features['wpm']}")
    evaluate_and_alert(fatigue_level)


def main():
    logger.info("🚀 Starting Cognitive Load Monitor...")
    initialize_db()

    # Start keystroke collector (background thread)
    listener = start_collector()

    # Schedule tasks
    schedule.every(60).seconds.do(flush_buffer_to_db)
    schedule.every(5).minutes.do(run_pipeline)

    # Retrain model weekly with accumulated data
    schedule.every().sunday.at("02:00").do(train_model)

    logger.info("✅ All systems running. Dashboard: http://localhost:5000")
    print("\n🧠 Cognitive Load Monitor is running silently.")
    print("📊 Open dashboard: http://localhost:5000")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        flush_buffer_to_db()
        logger.info("🛑 Monitor stopped gracefully.")
        print("\n✅ Stopped. All data saved.")


if __name__ == "__main__":
    main()
