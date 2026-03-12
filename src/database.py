"""
Simplified database module for Learner Agent Core MVP.
Single table: sessions (no teams, no topics, no challenges).
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "learner_agent.db"


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection.

    Returns:
        SQLite connection with row_factory set to Row
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def init_database() -> None:
    """Create database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Sessions table (simplified - no foreign keys)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_turns INTEGER DEFAULT 0,
            duration_minutes REAL,
            concepts_extracted INTEGER DEFAULT 0,
            relationships_extracted INTEGER DEFAULT 0,
            tokens_input INTEGER DEFAULT 0,
            tokens_output INTEGER DEFAULT 0,
            knowledge_graph_json TEXT,
            conversation_history_json TEXT
        )
    """)

    # Add language column if it doesn't exist (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN language TEXT DEFAULT 'en'")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Add token tracking columns if they don't exist (migration)
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN tokens_input INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN tokens_output INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Create index for topic searches
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_topic ON sessions(topic_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at)")

    conn.commit()
    conn.close()


# ===== SESSION CRUD =====

def create_session(topic_name: str, language: str = "en") -> int:
    """
    Create a new teaching session.

    Args:
        topic_name: Free-form topic name (e.g., "My Hometown")
        language: Language code ('en' or 'es')

    Returns:
        Session ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (topic_name, language)
        VALUES (?, ?)
    """, (topic_name, language))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


def update_session(
    session_id: int,
    total_turns: int = None,
    duration_minutes: float = None,
    concepts_extracted: int = None,
    relationships_extracted: int = None,
    tokens_input: int = None,
    tokens_output: int = None,
    knowledge_graph_json: str = None,
    conversation_history_json: str = None,
    completed_at: str = None
) -> None:
    """
    Update a session with training results.

    Args:
        session_id: ID of the session to update
        total_turns: Number of conversation turns
        duration_minutes: Session duration
        concepts_extracted: Number of concepts extracted
        relationships_extracted: Number of relationships extracted
        tokens_input: Total input tokens used
        tokens_output: Total output tokens used
        knowledge_graph_json: JSON representation of knowledge graph
        conversation_history_json: JSON array of conversation messages
        completed_at: Completion timestamp (ISO format)
    """
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if total_turns is not None:
        updates.append("total_turns = ?")
        params.append(total_turns)

    if duration_minutes is not None:
        updates.append("duration_minutes = ?")
        params.append(duration_minutes)

    if concepts_extracted is not None:
        updates.append("concepts_extracted = ?")
        params.append(concepts_extracted)

    if relationships_extracted is not None:
        updates.append("relationships_extracted = ?")
        params.append(relationships_extracted)

    if tokens_input is not None:
        updates.append("tokens_input = ?")
        params.append(tokens_input)

    if tokens_output is not None:
        updates.append("tokens_output = ?")
        params.append(tokens_output)

    if knowledge_graph_json is not None:
        updates.append("knowledge_graph_json = ?")
        params.append(knowledge_graph_json)

    if conversation_history_json is not None:
        updates.append("conversation_history_json = ?")
        params.append(conversation_history_json)

    if completed_at is not None:
        updates.append("completed_at = ?")
        params.append(completed_at)

    if updates:
        params.append(session_id)
        cursor.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()


def get_session_by_id(session_id: int) -> Optional[Dict]:
    """
    Get a session by ID.

    Args:
        session_id: Session ID

    Returns:
        Session dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def list_sessions(limit: int = 50, topic_name: str = None) -> List[Dict]:
    """
    List recent sessions, optionally filtered by topic.

    Args:
        limit: Maximum number of sessions to return
        topic_name: Optional topic filter

    Returns:
        List of session dicts
    """
    conn = get_connection()
    cursor = conn.cursor()

    if topic_name:
        cursor.execute("""
            SELECT * FROM sessions
            WHERE topic_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (topic_name, limit))
    else:
        cursor.execute("""
            SELECT * FROM sessions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def delete_session(session_id: int) -> bool:
    """
    Delete a session.

    Args:
        session_id: ID of the session to delete

    Returns:
        True if successful
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


def get_session_stats() -> Dict:
    """
    Get overall statistics across all sessions.

    Returns:
        Dict with total_sessions, total_topics, avg_concepts, etc.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_sessions,
            COUNT(DISTINCT topic_name) as unique_topics,
            AVG(concepts_extracted) as avg_concepts,
            AVG(relationships_extracted) as avg_relationships,
            AVG(total_turns) as avg_turns,
            AVG(duration_minutes) as avg_duration
        FROM sessions
        WHERE completed_at IS NOT NULL
    """)

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else {}


# ===== UTILITY =====

def database_exists() -> bool:
    """Check if database file exists."""
    return DB_PATH.exists()
