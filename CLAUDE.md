# Learner Agent Core — Project Context

## What This Is

**Learner Agent Core** is a minimal, distributable MVP that demonstrates the fundamental concept of a "learning AI agent." This is a **simplified extraction** from the full educational platform ([Learner Agent](https://github.com/yourusername/learner-agent)) designed for:

- **Easy distribution** (Docker-based, 3-step setup)
- **Concept demonstration** (teaching an AI that knows nothing)
- **Reusable core** (knowledge graph + extraction modules)
- **Quick prototyping** (no teams, no curriculum, no diagnostics)

---

## Core Concept

Unlike traditional AI tutors that already "know everything," this agent starts with **zero knowledge**. You teach it about any topic, and it builds structured knowledge in real-time.

**The Learning Loop:**

1. User creates a session with a free-form topic (e.g., "Pizza Recipe")
2. Agent greets user: "I know nothing about Pizza Recipe. Teach me!"
3. User explains concepts
4. Knowledge Builder (background LLM) extracts:
   - **Concepts**: Names + definitions
   - **Relationships**: How concepts connect
   - **Evidence**: Exact quotes from user
5. Agent asks clarifying questions using only what it learned
6. When done, agent demonstrates knowledge using ONLY the knowledge graph
7. If agent can't answer something, it means user didn't teach it

**Pedagogical Insight:** Teaching reveals knowledge gaps better than any test.

---

## What Was Simplified (vs. Full Platform)

| Feature | Full Platform | Core MVP |
|---------|---------------|----------|
| **Topics** | Predefined curriculum (Fotosíntesis, etc.) | Free-form user input |
| **Teams** | Multiple teams, challenges, scoreboard | Single user |
| **Diagnostics** | Fuzzy match vs. curriculum reference | None |
| **Challenge Mode** | Teams ask questions to rival agents | None |
| **Database** | Multi-table (teams, topics, sessions, challenges) | Single table (sessions) |
| **i18n** | Spanish + English with language enforcement | English-only prompts |
| **Admin** | Team management, session history, comparison | Basic session list |

**What Stays the Same:**

✅ Knowledge graph structure (concepts, relationships, evidence)
✅ Knowledge extraction logic (KnowledgeBuilder)
✅ Learner agent conversation (LearnerAgent)
✅ Assessment architecture (agent uses ONLY graph)
✅ WebSocket real-time chat
✅ SQLite persistence

---

## Architecture

### Tech Stack

- **Backend:** FastAPI + Python 3.12+
- **WebSocket:** Real-time bidirectional (teaching sessions)
- **Database:** SQLite (local file, single table)
- **LLM:** Anthropic Claude
  - **Learner:** `claude-sonnet-4-20250514` (conversation)
  - **Extractor:** `claude-haiku-4-5-20251001` (knowledge building)
- **Frontend:** Vanilla HTML/CSS/JavaScript (no build)
- **Deployment:** Docker + Docker Compose

### File Structure

```
learner-agent-core/
├── Dockerfile                    # Container image
├── docker-compose.yml            # Orchestration
├── pyproject.toml                # Python dependencies
├── .env.example                  # Config template
├── README.md                     # User documentation
├── CLAUDE.md                     # This file (dev context)
├── LICENSE                       # MIT
├── src/
│   ├── __init__.py
│   ├── knowledge_graph.py       # Copied from full platform
│   ├── knowledge_builder.py     # Copied from full platform
│   ├── learner_agent.py         # Copied from full platform
│   ├── prompts.py               # Simplified (no curriculum refs)
│   ├── database.py              # Simplified (single table)
│   └── web/
│       ├── __init__.py
│       ├── api.py               # FastAPI app (4 endpoints)
│       ├── websocket_handler.py # Teaching session WebSocket
│       └── static/
│           ├── index.html       # Single-page UI
│           ├── style.css        # Minimal styling
│           └── app.js           # WebSocket client
└── data/
    └── .gitkeep                 # Database goes here
```

### Database Schema (Simplified)

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT NOT NULL,              -- Free-form topic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_turns INTEGER DEFAULT 0,
    duration_minutes REAL,
    concepts_extracted INTEGER DEFAULT 0,
    relationships_extracted INTEGER DEFAULT 0,
    knowledge_graph_json TEXT,             -- JSON blob
    conversation_history_json TEXT         -- JSON array
);
```

**No foreign keys, no teams, no topics table, no challenges.**

### API Endpoints (4 Total)

```
POST   /api/sessions           # Create new session
GET    /api/sessions           # List all sessions
GET    /api/sessions/{id}      # Get session + knowledge graph
DELETE /api/sessions/{id}      # Delete session
GET    /api/stats              # Overall stats
GET    /health                 # Docker health check

WebSocket /ws/teach/{id}       # Real-time teaching
```

### Knowledge Graph JSON Structure

```json
{
  "concepts": {
    "concept_name": {
      "name": "concept_name",
      "definition": "user's definition",
      "category": "core|supporting|detail",
      "confidence": 0.0-1.0,
      "definition_history": ["v1", "v2"]
    }
  },
  "relationships": [
    {
      "source": "concept_a",
      "target": "concept_b",
      "type": "functional|hierarchical|spatial|temporal|causal",
      "label": "verb",
      "confidence": 0.0-1.0
    }
  ],
  "evidence": [
    {
      "concept": "concept_name",
      "quote": "exact user quote",
      "type": "definition|example|explanation"
    }
  ]
}
```

### WebSocket Protocol

**Client → Server:**

```json
{
  "type": "student_message",
  "content": "Photosynthesis is when plants make food"
}

{
  "type": "command",
  "content": "/graph" | "/done" | "/quit"
}
```

**Server → Client:**

```json
{
  "type": "agent_message",
  "content": "Oh, so plants create their own food? How?"
}

{
  "type": "stats_update",
  "content": {"total_concepts": 5, "total_relationships": 8}
}

{
  "type": "knowledge_graph",
  "content": { /* full graph JSON */ }
}

{
  "type": "assessment",
  "content": {
    "assessment": "text explanation from agent",
    "stats": {...},
    "knowledge_graph": {...}
  }
}

{
  "type": "status",
  "content": "Session saved"
}

{
  "type": "error",
  "content": "Error message"
}
```

---

## How It Works (Session Flow)

### 1. Session Creation

User clicks "Create New Agent" → enters topic name → `POST /api/sessions`

```python
session_id = db.create_session(topic_name="Pizza Recipe")
# Returns session ID, connects to WebSocket
```

### 2. Teaching Loop (WebSocket)

```python
# Server side (websocket_handler.py)
knowledge_graph = KnowledgeGraph(topic_name)
learner_agent = LearnerAgent(api_key, model)
knowledge_builder = KnowledgeBuilder(api_key, extractor_model)

while connected:
    # Receive user message
    student_message = await websocket.receive_json()

    # Extract knowledge (async, doesn't block)
    asyncio.create_task(
        knowledge_builder.extract_and_update(
            student_message,
            knowledge_graph,
            topic_name
        )
    )

    # Generate agent response
    system_prompt = get_learner_system_prompt(topic_name, turn_count, concepts)
    agent_response = await learner_agent.generate_response(
        message=student_message,
        system_prompt=system_prompt,
        conversation_history=[...]
    )

    # Send response
    await websocket.send_json({
        "type": "agent_message",
        "content": agent_response
    })

    # Auto-save every 5 turns
    if turn_count % 5 == 0:
        db.update_session(session_id, knowledge_graph_json=...)
```

### 3. Knowledge Extraction (Background)

```python
# knowledge_builder.py
async def extract_and_update(self, student_message, knowledge_graph, topic_name):
    current_graph_json = json.dumps(knowledge_graph.to_dict())

    prompt = f"""Extract concepts, relationships, evidence from:
    "{student_message}"

    Current graph: {current_graph_json}

    Return JSON: {{"new_concepts": [...], "new_relationships": [...], "evidence": [...]}}
    """

    response = await self.client.messages.create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": prompt}]
    )

    extracted = json.loads(response.content[0].text)

    # Update graph
    for concept in extracted["new_concepts"]:
        knowledge_graph.add_concept(
            name=concept["name"],
            definition=concept["definition"],
            category=concept["category"],
            confidence=concept["confidence"]
        )

    for rel in extracted["new_relationships"]:
        knowledge_graph.add_relationship(
            source=rel["source"],
            target=rel["target"],
            rel_type=rel["type"],
            label=rel["label"],
            confidence=rel["confidence"]
        )
```

### 4. Assessment (On `/done`)

```python
# Generate assessment
system_prompt = get_assessment_system_prompt(
    topic_name,
    json.dumps(knowledge_graph.to_dict())
)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=system_prompt,
    messages=[{"role": "user", "content": f"Explain {topic_name}"}]
)

assessment_text = response.content[0].text

# Save to database
db.update_session(
    session_id,
    completed_at=datetime.now().isoformat(),
    knowledge_graph_json=...,
    conversation_history_json=...
)

# Send to client
await websocket.send_json({
    "type": "assessment",
    "content": {
        "assessment": assessment_text,
        "stats": knowledge_graph.get_stats(),
        "knowledge_graph": knowledge_graph.to_dict()
    }
})
```

---

## Critical Design Principles

### 1. Knowledge Suppression

**The Hard Problem:** The agent (Claude) already knows about most topics. How do we prevent it from "leaking" pretrained knowledge?

**Solution (2-layer approach):**

1. **Learner Agent Prompt:**
   ```
   You know ABSOLUTELY NOTHING about {topic}.
   You must NEVER introduce factual information the teacher hasn't told you.
   Ask questions from REAL confusion.
   ```

2. **Assessment Isolation:**
   ```
   YOUR ONLY SOURCE OF KNOWLEDGE is this knowledge graph:
   {knowledge_graph_json}

   If asked about something not in the graph, say "I don't think my teacher taught me that."
   ```

**Key:** Assessment agent receives ONLY the JSON graph, not the conversation history.

### 2. Asynchronous Knowledge Extraction

**Why:** Knowledge extraction takes 1-3 seconds. If synchronous, user waits for agent response.

**Solution:**

```python
# Fire-and-forget extraction
asyncio.create_task(extract_knowledge_async(...))

# Agent responds immediately (doesn't wait for extraction)
agent_response = await learner_agent.generate_response(...)
await websocket.send_json({"type": "agent_message", ...})

# Later, extraction finishes and sends stats update
await websocket.send_json({"type": "stats_update", ...})
```

### 3. Conversation History Management

**Problem:** Long conversations exceed context window.

**Current Solution:** Keep full history (works for MVP sessions <50 turns)

**Future Enhancement (if needed):**
- Summarize old turns
- Keep only last N turns + knowledge graph
- Use RAG on conversation history

---

## Deployment (Docker)

### Build

```bash
docker-compose build
```

### Run

```bash
docker-compose up
```

### Environment Variables

Required:
- `ANTHROPIC_API_KEY`

Optional:
- `LEARNER_MODEL` (default: claude-sonnet-4-20250514)
- `EXTRACTOR_MODEL` (default: claude-haiku-4-5-20251001)
- `APP_ENV` (default: production)
- `LOG_LEVEL` (default: info)

### Volume Mounting

`./data:/app/data` - SQLite database persists on host

### Health Check

Docker polls `GET /health` every 30 seconds

---

## Cost Estimate

**Per session (20 turns, 15 minutes):**

- Learner Agent: 20 × $0.005 = **$0.10**
- Knowledge Extractor: 20 × $0.001 = **$0.02**
- Assessment: 1 × $0.01 = **$0.01**

**Total: ~$0.13 per session**

**100 sessions = $13 USD**

---

## Known Limitations

1. **No multi-user support** - Single user only (no authentication)
2. **No curriculum validation** - Can't compare against reference curriculum
3. **No challenge mode** - Can't test agent with hard questions
4. **Basic UI** - Minimal styling, no graphs/charts
5. **English-only prompts** - No i18n (though agent will respond in user's language)
6. **No session sharing** - Can't export/import sessions
7. **No voice input** - Text-only

**These are intentional simplifications.** For full features, see the [Learner Agent platform](https://github.com/yourusername/learner-agent).

---

## Future Extensions (If Needed)

Potential enhancements without breaking simplicity:

- [ ] **Export knowledge graph** as JSON/Markdown
- [ ] **Topic templates** (pre-fill some concepts for common topics)
- [ ] **Session sharing** (generate shareable link)
- [ ] **Voice input/output** (Whisper API + TTS)
- [ ] **Graph visualization** (D3.js force-directed graph)
- [ ] **Multi-language UI** (Spanish, Portuguese)
- [ ] **Assessment questions** (LLM generates quiz from graph)

---

## Reusable Core Modules

These 3 modules can be extracted and used in other projects:

### `knowledge_graph.py`

Pure Python dataclass-based knowledge graph:

```python
from src.knowledge_graph import KnowledgeGraph, Concept, Relationship, Evidence

kg = KnowledgeGraph("Topic")
kg.add_concept("name", "definition", "core", 0.9)
kg.add_relationship("source", "target", "functional", "verb", 0.8)
kg.add_evidence("concept", "quote", "definition")

stats = kg.get_stats()  # {'total_concepts': 1, ...}
data = kg.to_dict()     # Serializable dict
```

### `knowledge_builder.py`

LLM-based knowledge extraction:

```python
from src.knowledge_builder import KnowledgeBuilder

builder = KnowledgeBuilder(api_key="...", model="claude-haiku-4-5-20251001")

await builder.extract_and_update(
    student_message="Plants use sunlight",
    knowledge_graph=kg,
    topic_name="Photosynthesis"
)
```

### `learner_agent.py`

Conversational agent with streaming:

```python
from src.learner_agent import LearnerAgent

agent = LearnerAgent(api_key="...", model="claude-sonnet-4-20250514")

response = await agent.generate_response(
    message="User message",
    system_prompt="System prompt",
    conversation_history=[{"role": "user", "content": "..."}]
)
```

---

## Development

### Local Setup (Without Docker)

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
export ANTHROPIC_API_KEY=your_key
uvicorn src.web.api:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (when implemented)
pytest tests/

# Code formatting
black src/
ruff src/
```

---

## General Non-Functional Requirements

- Agent responds in **same language as user** (prompt instruction)
- Agent responses are **short** (2-4 sentences) - it's a student, not lecturer
- **API key security**: Never log or expose API key
- **Data privacy**: All data stays local (SQLite file)
- **Error handling**: Graceful degradation on LLM failures
- **WebSocket reconnection**: Client should handle disconnects

---

## Relationship to Full Platform

This MVP was extracted from the full [Learner Agent platform](https://github.com/yourusername/learner-agent) which includes:

- **Teams & Challenges** (protégé effect + elaborative interrogation)
- **Curriculum Diagnostics** (fuzzy matching vs. reference curriculum)
- **Scoreboard & Rankings** (competitive learning)
- **Multi-topic support** (Fotosíntesis, Sistema Solar, Ciclo del Agua)
- **i18n** (Spanish/English with language enforcement)
- **Admin features** (team management, session history, comparison)

**When to use Core vs. Full:**

| Use Case | Recommended Version |
|----------|-------------------|
| Demonstrating concept to stakeholders | **Core** |
| Personal learning/Feynman technique | **Core** |
| Quick prototyping new topics | **Core** |
| K-12 classroom deployment | **Full** |
| University course integration | **Full** |
| Research study with curriculum validation | **Full** |

---

**Current Version:** 0.1.0 (Initial MVP)

**Last Updated:** March 2026
