"""
Keystroke Collector — the heart of the data pipeline.

PRIVACY GUARANTEE:
- No actual keys are ever recorded or stored.
- Only timing metadata (inter-key intervals) is captured.
- Active app name is recorded to filter non-coding windows.
"""

import time
import sqlite3
from collections import deque
from pynput import keyboard
from loguru import logger
import psutil
import threading

from collector.database import get_connection, initialize_db

# Buffer to hold recent events before flushing to DB
_event_buffer = deque(maxlen=500)
_last_key_time = None
_lock = threading.Lock()


def _get_active_app() -> str:
    """Get the actual foreground window's process name on Windows."""
    try:
        import win32gui
        import win32process
        import psutil

        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        name = psutil.Process(pid).name()
        return name
    except Exception:
        return "unknown"


def _on_key_press(key):
    """Called on every key press. Extracts timing, never the key itself."""
    global _last_key_time

    now = time.time()
    is_backspace = int(key == keyboard.Key.backspace)
    active_app = _get_active_app()

    with _lock:
        iki_ms = None
        if _last_key_time is not None:
            iki_ms = (now - _last_key_time) * 1000  # convert to ms
            # Ignore IKI > 30s (user was idle, not typing slowly)
            if iki_ms > 30_000:
                iki_ms = None
        _last_key_time = now

        _event_buffer.append({
            "timestamp": now,
            "iki_ms": iki_ms,
            "is_backspace": is_backspace,
            "active_app": active_app,
        })


def flush_buffer_to_db():
    """Flush buffered events to SQLite. Called every 60 seconds by scheduler."""
    with _lock:
        if not _event_buffer:
            return
        events = list(_event_buffer)
        _event_buffer.clear()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO keystroke_events (timestamp, iki_ms, is_backspace, active_app)
        VALUES (:timestamp, :iki_ms, :is_backspace, :active_app)
    """, events)
    conn.commit()
    conn.close()
    logger.debug(f"Flushed {len(events)} keystroke events to DB")


def start_collector():
    """Start the background keystroke listener. Non-blocking."""
    initialize_db()
    logger.info("🎹 Keystroke collector started (no keys are recorded — timing only)")

    listener = keyboard.Listener(on_press=_on_key_press)
    listener.daemon = True
    listener.start()
    return listener


if __name__ == "__main__":
    import schedule

    listener = start_collector()

    # Flush to DB every 60 seconds
    schedule.every(60).seconds.do(flush_buffer_to_db)

    print("✅ Collector running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        flush_buffer_to_db()  # Final flush before exit
        print("\n🛑 Collector stopped. Final buffer flushed.")
