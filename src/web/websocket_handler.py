"""
WebSocket handler for teaching sessions (simplified MVP version).
Handles real-time conversation with knowledge extraction.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

import src.database as db
from src.knowledge_graph import KnowledgeGraph
from src.knowledge_builder import KnowledgeBuilder
from src.learner_agent import LearnerAgent
from src.prompts import get_learner_system_prompt, get_assessment_system_prompt


# Get models from environment variables
LEARNER_MODEL = os.getenv("LEARNER_MODEL", "claude-sonnet-4-20250514")
EXTRACTOR_MODEL = os.getenv("EXTRACTOR_MODEL", "claude-haiku-4-5-20251001")
API_KEY = os.getenv("ANTHROPIC_API_KEY")


async def handle_teaching_session(websocket: WebSocket, session_id: int):
    """
    Handle a WebSocket teaching session.

    Args:
        websocket: WebSocket connection
        session_id: Session ID from database
    """
    await websocket.accept()

    # Load session from database
    session = db.get_session_by_id(session_id)
    if not session:
        await websocket.send_json({
            "type": "error",
            "content": f"Session {session_id} not found"
        })
        await websocket.close()
        return

    topic_name = session["topic_name"]
    language = session.get("language", "en")  # Default to English if not set

    # Initialize knowledge graph
    knowledge_graph = KnowledgeGraph()

    # Load existing knowledge if session is being resumed
    if session["knowledge_graph_json"]:
        try:
            kg_data = json.loads(session["knowledge_graph_json"])
            # Restore knowledge graph from JSON
            for concept_name, concept_data in kg_data.get("concepts", {}).items():
                knowledge_graph.add_concept(
                    name=concept_data["name"],
                    definition=concept_data["definition"],
                    category=concept_data.get("category", "core"),
                    confidence=concept_data.get("confidence", 0.8)
                )
            for rel in kg_data.get("relationships", []):
                knowledge_graph.add_relationship(
                    source=rel["source"],
                    target=rel["target"],
                    rel_type=rel["type"],
                    label=rel["label"],
                    confidence=rel.get("confidence", 0.8)
                )
        except Exception as e:
            print(f"Warning: Could not restore knowledge graph: {e}")

    # Initialize agents
    from anthropic import Anthropic
    client = Anthropic(api_key=API_KEY)

    learner_agent = LearnerAgent(
        client=client,
        topic_name=topic_name
    )

    knowledge_builder = KnowledgeBuilder(
        client=client,
        topic_name=topic_name
    )

    # Conversation history
    conversation_history = []
    if session["conversation_history_json"]:
        try:
            conversation_history = json.loads(session["conversation_history_json"])
        except Exception:
            pass

    turn_count = session["total_turns"]
    session_start_time = datetime.now()

    # Send welcome message
    await websocket.send_json({
        "type": "status",
        "content": f"Connected to teaching session for '{topic_name}'"
    })

    # If starting fresh, send agent's opening message
    if turn_count == 0:
        opening_message = learner_agent.get_initial_greeting()

        conversation_history.append({"role": "agent", "content": opening_message})

        await websocket.send_json({
            "type": "agent_message",
            "content": opening_message
        })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data["type"] == "student_message":
                student_message = data["content"]

                # Add to history
                conversation_history.append({"role": "student", "content": student_message})
                turn_count += 1

                # Extract knowledge in background (async)
                asyncio.create_task(
                    extract_knowledge_async(
                        knowledge_builder,
                        knowledge_graph,
                        topic_name,
                        student_message,
                        websocket
                    )
                )

                # Generate agent response
                agent_response = learner_agent.generate_response(
                    student_message=student_message,
                    knowledge_graph=knowledge_graph
                )

                conversation_history.append({"role": "agent", "content": agent_response})

                # Send agent response
                await websocket.send_json({
                    "type": "agent_message",
                    "content": agent_response
                })

                # Auto-save every 5 turns
                if turn_count % 5 == 0:
                    await save_session_state(
                        session_id,
                        turn_count,
                        knowledge_graph,
                        conversation_history,
                        session_start_time
                    )

            elif data["type"] == "command":
                command = data["content"]

                if command == "/graph":
                    # Send knowledge graph
                    await websocket.send_json({
                        "type": "knowledge_graph",
                        "content": knowledge_graph.to_dict()
                    })

                elif command == "/done":
                    # Finalize session and generate assessment
                    await finalize_session(
                        websocket,
                        session_id,
                        turn_count,
                        knowledge_graph,
                        conversation_history,
                        session_start_time,
                        topic_name
                    )
                    break

                elif command == "/quit":
                    # Save and exit
                    await save_session_state(
                        session_id,
                        turn_count,
                        knowledge_graph,
                        conversation_history,
                        session_start_time
                    )
                    await websocket.send_json({
                        "type": "status",
                        "content": "Session saved. Goodbye!"
                    })
                    break

    except WebSocketDisconnect:
        # Save on disconnect
        await save_session_state(
            session_id,
            turn_count,
            knowledge_graph,
            conversation_history,
            session_start_time
        )
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"Error: {str(e)}"
        })
        await websocket.close()


async def extract_knowledge_async(
    knowledge_builder: KnowledgeBuilder,
    knowledge_graph: KnowledgeGraph,
    topic_name: str,
    student_message: str,
    websocket: WebSocket
):
    """Extract knowledge in background and send updates."""
    try:
        # Run synchronous extraction in executor to not block
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            knowledge_builder.process_student_message,
            student_message,
            knowledge_graph
        )

        # Send updated stats
        stats = knowledge_graph.get_stats()
        await websocket.send_json({
            "type": "stats_update",
            "content": stats
        })

    except Exception as e:
        print(f"Knowledge extraction error: {e}")


async def save_session_state(
    session_id: int,
    turn_count: int,
    knowledge_graph: KnowledgeGraph,
    conversation_history: List[Dict],
    session_start_time: datetime
):
    """Save current session state to database."""
    duration = (datetime.now() - session_start_time).total_seconds() / 60.0
    stats = knowledge_graph.get_stats()

    db.update_session(
        session_id=session_id,
        total_turns=turn_count,
        duration_minutes=duration,
        concepts_extracted=stats["concepts"],
        relationships_extracted=stats["relationships"],
        knowledge_graph_json=json.dumps(knowledge_graph.to_dict(), ensure_ascii=False),
        conversation_history_json=json.dumps(conversation_history, ensure_ascii=False)
    )


async def finalize_session(
    websocket: WebSocket,
    session_id: int,
    turn_count: int,
    knowledge_graph: KnowledgeGraph,
    conversation_history: List[Dict],
    session_start_time: datetime,
    topic_name: str
):
    """Finalize session and generate assessment."""
    # Save final state
    duration = (datetime.now() - session_start_time).total_seconds() / 60.0
    stats = knowledge_graph.get_stats()

    db.update_session(
        session_id=session_id,
        total_turns=turn_count,
        duration_minutes=duration,
        concepts_extracted=stats["concepts"],
        relationships_extracted=stats["relationships"],
        knowledge_graph_json=json.dumps(knowledge_graph.to_dict(), ensure_ascii=False),
        conversation_history_json=json.dumps(conversation_history, ensure_ascii=False),
        completed_at=datetime.now().isoformat()
    )

    # Generate assessment (agent demonstrates what it learned)
    await websocket.send_json({
        "type": "status",
        "content": "Generating assessment..."
    })

    # Create assessment using same learner agent
    from anthropic import Anthropic
    client = Anthropic(api_key=API_KEY)

    system_prompt = get_assessment_system_prompt(
        topic_name,
        json.dumps(knowledge_graph.to_dict(), ensure_ascii=False)
    )

    response = client.messages.create(
        model=LEARNER_MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Please explain what you learned about {topic_name}."}
        ]
    )

    assessment_text = response.content[0].text

    await websocket.send_json({
        "type": "assessment",
        "content": {
            "assessment": assessment_text,
            "stats": stats,
            "knowledge_graph": knowledge_graph.to_dict()
        }
    })

    await websocket.send_json({
        "type": "status",
        "content": "Session completed!"
    })
