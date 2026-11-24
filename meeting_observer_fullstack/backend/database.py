import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def get_connection(database_path):
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database(database_path):
    connection = get_connection(database_path)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            meeting_date TEXT,
            team TEXT,
            transcript_excerpt TEXT,
            analysis_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    connection.commit()
    connection.close()

def save_meeting(database_path, title, team, transcript, analysis):
    connection = get_connection(database_path)
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = connection.execute(
        """INSERT INTO meetings
        (title, meeting_date, team, transcript_excerpt, analysis_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            title,
            created_at[:10],
            team,
            transcript[:500],
            json.dumps(analysis, ensure_ascii=False),
            created_at
        )
    )
    meeting_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return meeting_id

def list_meetings(database_path):
    connection = get_connection(database_path)
    rows = connection.execute(
        "SELECT id, title, meeting_date, team, created_at, analysis_json FROM meetings ORDER BY id DESC"
    ).fetchall()
    connection.close()

    meetings = []
    for row in rows:
        analysis = json.loads(row["analysis_json"])
        meetings.append({
            "id": row["id"],
            "title": row["title"],
            "date": row["meeting_date"],
            "team": row["team"],
            "created_at": row["created_at"],
            "summary": analysis.get("summary", ""),
            "action_count": len(analysis.get("action_items", [])),
            "decision_count": len(analysis.get("decisions", [])),
            "risk_count": len(analysis.get("risks", [])),
            "source": "saved"
        })
    return meetings

def get_meeting(database_path, meeting_id):
    connection = get_connection(database_path)
    row = connection.execute(
        "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
    ).fetchone()
    connection.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "title": row["title"],
        "date": row["meeting_date"],
        "team": row["team"],
        "transcript_excerpt": row["transcript_excerpt"],
        "created_at": row["created_at"],
        "analysis": json.loads(row["analysis_json"]),
        "source": "saved"
    }
