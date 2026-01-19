import sqlite3
import os
from datetime import datetime

DB_PATH = "network_data.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Targets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Pings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            latency REAL,
            loss REAL NOT NULL,
            FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE CASCADE
        )
    """)

    # Hops table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hop_num INTEGER NOT NULL,
            ip TEXT NOT NULL,
            latency REAL,
            loss REAL,
            FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_target(address):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO targets (address) VALUES (?)", (address,))
        cursor.execute("UPDATE targets SET is_active = 1 WHERE address = ?", (address,))
        cursor.execute("SELECT id FROM targets WHERE address = ?", (address,))
        target_id = cursor.fetchone()[0]
        conn.commit()
        return target_id
    finally:
        conn.close()


def save_ping(target_id, latency, loss):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO pings (target_id, latency, loss) VALUES (?, ?, ?)",
            (target_id, latency, loss),
        )
        conn.commit()
    finally:
        conn.close()


def save_hop(target_id, hop_num, ip, latency, loss):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO hops (target_id, hop_num, ip, latency, loss) VALUES (?, ?, ?, ?, ?)",
            (target_id, hop_num, ip, latency, loss),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(address, hours=24):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM targets WHERE address = ?", (address,))
        row = cursor.fetchone()
        if not row:
            return []
        target_id = row[0]

        cursor.execute(
            """
            SELECT timestamp, latency, loss 
            FROM pings 
            WHERE target_id = ? AND timestamp > datetime('now', ?)
            ORDER BY timestamp ASC
        """,
            (target_id, f"-{hours} hours"),
        )

        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_active_targets():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT address FROM targets WHERE is_active = 1")
        return [r[0] for r in cursor.fetchall()]
    finally:
        conn.close()


def deactivate_target(address):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE targets SET is_active = 0 WHERE address = ?", (address,))
        conn.commit()
    finally:
        conn.close()


def clear_target_history(address):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM targets WHERE address = ?", (address,))
        row = cursor.fetchone()
        if row:
            target_id = row[0]
            cursor.execute("DELETE FROM pings WHERE target_id = ?", (target_id,))
            cursor.execute("DELETE FROM hops WHERE target_id = ?", (target_id,))
            conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
