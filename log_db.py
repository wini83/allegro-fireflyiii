import json
import sqlite3
from datetime import datetime
from typing import Any

DB_FILE = "log.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS matched_tx (
            id INTEGER PRIMARY KEY,
            tx_id TEXT,
            tx_date TEXT,
            tx_amount REAL,
            matched_count INTEGER,
            applied INTEGER,
            match_date TEXT,
            details TEXT
        )'''
    )
    conn.commit()
    conn.close()


def log_matched_transaction(tx, match_count: int, applied: bool, details: Any):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        (
            "INSERT INTO matched_tx (tx_id, tx_date, tx_amount, matched_count, "
            "applied, match_date, details) VALUES (?, ?, ?, ?, ?, ?, ?)"
        ),
        (
            tx.tx.id,
            tx.tx.date.isoformat(),
            tx.tx.amount,
            match_count,
            1 if applied else 0,
            datetime.now().isoformat(),
            json.dumps(details),
        ),
    )
    conn.commit()
    conn.close()


def load_matched_log(limit: int = 50):
    try:
        conn = sqlite3.connect(DB_FILE)
        df = None
        try:
            import pandas as pd

            df = pd.read_sql(
                "SELECT * FROM matched_tx ORDER BY match_date DESC LIMIT ?",
                conn,
                params=(limit,),
            )
        finally:
            conn.close()
        return df
    except Exception:
        return None
