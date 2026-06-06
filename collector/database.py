"""
Database setup and helper functions.
SQLite is used — local, private, zero setup required.
Raw keys are NEVER stored — only timing metadata.
"""

import sqlite3
import os
from pathlib import Path
from loguru import logger

DB_PATH = Path(__file__).parent.parent / "data" / "cognitive_load.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # allows dict-like access to rows
    return conn


def initialize_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Raw keystroke events (timing only — no actual keys)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keystroke_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   REAL    NOT NULL,   -- Unix epoch float
            iki_ms      REAL,               -- Inter-key interval in milliseconds
            is_backspace INTEGER DEFAULT 0, -- 1 if backspace was pressed
            active_app  TEXT                -- Active window/app name
        )
    """)

    # Aggregated 5-minute feature windows
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_windows (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            window_start        REAL    NOT NULL,  -- Unix epoch of window start
            window_end          REAL    NOT NULL,
            mean_iki_ms         REAL,
            std_iki_ms          REAL,
            wpm                 REAL,              -- Words per minute
            backspace_ratio     REAL,              -- backspaces / total keys
            burst_count         INTEGER,           -- Number of typing bursts
            idle_gap_count      INTEGER,           -- Gaps > 3 seconds
            total_keystrokes    INTEGER,
            anomaly_score       REAL,              -- Output from Isolation Forest (0-1)
            fatigue_level       TEXT               -- 'low', 'medium', 'high'
        )
    """)

    # Alert log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       REAL    NOT NULL,
            fatigue_level   TEXT,
            message         TEXT,
            acknowledged    INTEGER DEFAULT 0  -- 1 if user acted on it
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    initialize_db()
    print(f"✅ Database ready at: {DB_PATH}")
