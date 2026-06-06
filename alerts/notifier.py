"""
Alert & Notification System.
Sends desktop notifications when fatigue stays HIGH for 10+ consecutive minutes.
"""

import time
from loguru import logger
from plyer import notification

from collector.database import get_connection

ALERT_COOLDOWN_SECONDS = 600   # Don't spam — min 10 mins between alerts
HIGH_FATIGUE_THRESHOLD = 2     # 2 consecutive high-fatigue windows = alert
_last_alert_time = 0
_consecutive_high_count = 0


def send_notification(title: str, message: str):
    """Send a desktop notification."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Cognitive Load Monitor",
            timeout=10,
        )
        logger.info(f"🔔 Notification sent: {title}")
    except Exception as e:
        logger.warning(f"Could not send notification: {e}")
        # Fallback: print to console
        print(f"\n⚠️  [{title}] {message}\n")


def log_alert(fatigue_level: str, message: str):
    """Save alert to DB for dashboard display."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO alerts (timestamp, fatigue_level, message)
        VALUES (?, ?, ?)
    """, (time.time(), fatigue_level, message))
    conn.commit()
    conn.close()


def evaluate_and_alert(fatigue_level: str):
    """
    Evaluate current fatigue level and send alert if needed.
    Called after every feature window is scored.
    """
    global _last_alert_time, _consecutive_high_count

    if fatigue_level == "high":
        _consecutive_high_count += 1
    else:
        _consecutive_high_count = 0  # reset streak

    now = time.time()
    time_since_last = now - _last_alert_time
    cooldown_passed = time_since_last >= ALERT_COOLDOWN_SECONDS

    if _consecutive_high_count >= HIGH_FATIGUE_THRESHOLD and cooldown_passed:
        message = (
            f"You've been in high cognitive load for "
            f"{_consecutive_high_count * 5} minutes.\n"
            "Consider taking a 5–10 minute break. 🧘"
        )
        send_notification("🧠 Cognitive Load Alert", message)
        log_alert("high", message)
        _last_alert_time = now
        _consecutive_high_count = 0  # reset after alert

    elif fatigue_level == "medium" and cooldown_passed and _consecutive_high_count == 0 and _consecutive_medium_count >= 2:
        # Gentle medium-fatigue nudge (less urgent)
        message = "Cognitive load is moderate. Stay hydrated and stretch. 💧"
        send_notification("🟡 Heads Up", message)
        log_alert("medium", message)
        _last_alert_time = now


if __name__ == "__main__":
    # Test notification
    send_notification("Test Alert", "Cognitive Load Monitor is working correctly! ✅")
