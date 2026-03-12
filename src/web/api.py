"""
Simplified FastAPI application for Learner Agent Core MVP.
Minimal endpoints: create session, list sessions, teach via WebSocket.
"""

import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path

# Import database and core modules
import src.database as db
from src.knowledge_graph import KnowledgeGraph


# Initialize FastAPI app
app = FastAPI(
    title="Learner Agent Core API",
    description="Minimal MVP for teaching AI agents",
    version="0.1.0"
)

# Initialize database
db.init_database()

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ===== PYDANTIC MODELS =====

class SessionCreate(BaseModel):
    topic_name: str


class SessionResponse(BaseModel):
    id: int
    topic_name: str
    created_at: str
    completed_at: Optional[str]
    total_turns: int
    duration_minutes: Optional[float]
    concepts_extracted: int
    relationships_extracted: int


class SessionDetailResponse(SessionResponse):
    knowledge_graph: Optional[dict]
    conversation_history: Optional[List[dict]]


# ===== HEALTH CHECK =====

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy", "version": "0.1.0"}


# ===== STATIC FILES =====

@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


# ===== SESSION ENDPOINTS =====

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    """
    Create a new teaching session.

    Args:
        session: SessionCreate with topic_name

    Returns:
        Created session details
    """
    session_id = db.create_session(session.topic_name)
    created_session = db.get_session_by_id(session_id)

    return SessionResponse(
        id=created_session["id"],
        topic_name=created_session["topic_name"],
        created_at=created_session["created_at"],
        completed_at=created_session["completed_at"],
        total_turns=created_session["total_turns"],
        duration_minutes=created_session["duration_minutes"],
        concepts_extracted=created_session["concepts_extracted"],
        relationships_extracted=created_session["relationships_extracted"]
    )


@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(limit: int = 50, topic: Optional[str] = None):
    """
    List recent sessions, optionally filtered by topic.

    Args:
        limit: Max number of sessions to return
        topic: Optional topic name filter

    Returns:
        List of sessions
    """
    sessions = db.list_sessions(limit=limit, topic_name=topic)

    return [
        SessionResponse(
            id=s["id"],
            topic_name=s["topic_name"],
            created_at=s["created_at"],
            completed_at=s["completed_at"],
            total_turns=s["total_turns"],
            duration_minutes=s["duration_minutes"],
            concepts_extracted=s["concepts_extracted"],
            relationships_extracted=s["relationships_extracted"]
        )
        for s in sessions
    ]


@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: int):
    """
    Get session details including knowledge graph and conversation.

    Args:
        session_id: Session ID

    Returns:
        Full session details
    """
    session = db.get_session_by_id(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Parse JSON fields
    knowledge_graph = None
    if session["knowledge_graph_json"]:
        knowledge_graph = json.loads(session["knowledge_graph_json"])

    conversation_history = None
    if session["conversation_history_json"]:
        conversation_history = json.loads(session["conversation_history_json"])

    return SessionDetailResponse(
        id=session["id"],
        topic_name=session["topic_name"],
        created_at=session["created_at"],
        completed_at=session["completed_at"],
        total_turns=session["total_turns"],
        duration_minutes=session["duration_minutes"],
        concepts_extracted=session["concepts_extracted"],
        relationships_extracted=session["relationships_extracted"],
        knowledge_graph=knowledge_graph,
        conversation_history=conversation_history
    )


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int):
    """
    Delete a session.

    Args:
        session_id: Session ID

    Returns:
        Success message
    """
    session = db.get_session_by_id(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    db.delete_session(session_id)
    return {"message": f"Session {session_id} deleted successfully"}


@app.get("/api/stats")
async def get_stats():
    """
    Get overall statistics across all sessions.

    Returns:
        Stats dict
    """
    return db.get_session_stats()


# ===== WEBSOCKET FOR TEACHING =====

# This will be in websocket_handler.py - just import and use
from src.web.websocket_handler import handle_teaching_session

@app.websocket("/ws/teach/{session_id}")
async def websocket_teach(websocket: WebSocket, session_id: int):
    """
    WebSocket endpoint for real-time teaching conversation.

    Args:
        websocket: WebSocket connection
        session_id: Session ID
    """
    await handle_teaching_session(websocket, session_id)


# ===== ERROR HANDLERS =====

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ===== STARTUP EVENT =====

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("🚀 Learner Agent Core API starting...")
    print(f"📊 Database: {db.DB_PATH}")
    print(f"🌐 Static files: {STATIC_DIR}")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set!")
    else:
        print("✅ ANTHROPIC_API_KEY configured")
