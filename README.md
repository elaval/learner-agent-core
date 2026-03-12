# 🧠 Learner Agent Core

> A minimal MVP for teaching AI agents that start knowing nothing.

**Learner Agent Core** is a simplified, containerized application that demonstrates the core concept of a "learning AI agent." Unlike traditional AI tutors, this agent starts with **zero knowledge** about your topic. You teach it, and it builds knowledge in real-time. At the end, it demonstrates what it learned.

---

## 🎯 Concept

Traditional AI assistants already "know" everything. This inverts that model:

1. **You create an agent** on any topic (your hometown, a recipe, a hobby, etc.)
2. **You teach the agent** through conversation
3. **The agent builds knowledge** (concepts, relationships, evidence) in the background
4. **You ask the agent questions** to verify what it learned
5. **Knowledge gaps reveal your teaching gaps** (if the agent can't answer, you didn't teach it)

This is based on the **protégé effect**: teaching others is one of the most effective ways to learn.

---

## ✨ Features

- ✅ **Blank Slate Learning** - Agent starts with zero knowledge
- ✅ **Real-time Knowledge Extraction** - Builds knowledge graph as you teach
- ✅ **WebSocket Chat Interface** - Natural conversation flow
- ✅ **Knowledge Graph Visualization** - See concepts and relationships
- ✅ **Assessment Mode** - Agent demonstrates what it learned
- ✅ **Session Persistence** - SQLite database, continue later
- ✅ **Docker Containerized** - One-command deployment
- ✅ **Free-form Topics** - Teach about anything

---

## 🚀 Quick Start (3 Steps)

### Prerequisites

- **Docker Desktop** installed ([download here](https://www.docker.com/products/docker-desktop))
- **Anthropic API key** ([get one here](https://console.anthropic.com))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/learner-agent-core.git
cd learner-agent-core
```

### Step 2: Configure API Key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Example `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
```

### Step 3: Start with Docker

```bash
docker-compose up
```

Then open your browser to: **http://localhost:8000**

That's it! 🎉

---

## 📖 How to Use

### Create a New Agent

1. Click **"+ Create New Agent"**
2. Enter a topic (e.g., "The Water Cycle")
3. Click **"Start Teaching"**

### Teach the Agent

The agent will greet you and ask questions. You explain the topic:

```
Agent: Hi! I'm excited to learn about The Water Cycle. Can you explain what that is?

You: The water cycle is the continuous movement of water on, above, and below Earth's surface.

Agent: Wow, that's interesting! So water moves around? How does it move?

You: Water evaporates from the surface, forms clouds, and falls back as rain or snow.

Agent: Ah! So evaporation is when water goes up? What happens next?
```

### Commands During Teaching

- **Type `/graph`** - See the knowledge graph (concepts & relationships)
- **Type `/done`** - Finish teaching and generate assessment
- **Type `/quit`** - Save progress and exit

### Assessment

When you type `/done`, the agent will:

1. Explain the topic back to you using **only** what you taught
2. Show stats (concepts learned, relationships extracted)
3. Display the complete knowledge graph

If the agent can't explain something, **you didn't teach it!**

---

## 🏗️ Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (local file)
- **WebSocket**: Real-time bidirectional chat
- **LLM**: Anthropic Claude
  - **Learner Agent**: `claude-sonnet-4-20250514` (conversation)
  - **Knowledge Extractor**: `claude-haiku-4-5-20251001` (background processing)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no build step)

### How Knowledge Extraction Works

1. **You send a message** explaining the topic
2. **Learner Agent responds** with questions or confirmations
3. **Knowledge Builder (background)** extracts structured data:
   - **Concepts**: Names, definitions, categories
   - **Relationships**: How concepts connect (functional, hierarchical, etc.)
   - **Evidence**: Exact quotes from your teaching
4. **Knowledge Graph updates** in real-time
5. **Assessment uses ONLY the graph** (no pretrained knowledge leakage)

### Simplified Database Schema

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    topic_name TEXT,
    knowledge_graph_json TEXT,  -- JSON of concepts/relationships
    conversation_history_json TEXT,
    total_turns INTEGER,
    concepts_extracted INTEGER,
    relationships_extracted INTEGER,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

No teams, no challenges, no curriculum references — just teaching sessions.

---

## 📊 API Endpoints

### Sessions

- `POST /api/sessions` - Create new teaching session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details with knowledge graph
- `DELETE /api/sessions/{id}` - Delete a session

### Stats

- `GET /api/stats` - Overall statistics (total sessions, avg concepts, etc.)

### Teaching

- `WebSocket /ws/teach/{session_id}` - Real-time teaching conversation

### Health

- `GET /health` - Docker health check

---

## 🐳 Docker Details

### Build Image

```bash
docker-compose build
```

### Run Container

```bash
docker-compose up
```

### Run in Background

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
```

### Stop Container

```bash
docker-compose down
```

### Data Persistence

Your SQLite database is stored in `./data/learner_agent.db` (mounted as Docker volume).

To backup your sessions:

```bash
cp data/learner_agent.db data/backup_$(date +%Y%m%d).db
```

---

## 💻 Development (Without Docker)

If you want to run locally for development:

### 1. Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -e .
```

### 3. Set Environment Variables

```bash
export ANTHROPIC_API_KEY=your_key_here
# On Windows: set ANTHROPIC_API_KEY=your_key_here
```

### 4. Run the Server

```bash
uvicorn src.web.api:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

---

## 🧪 Example Use Cases

### Education

- **Student**: Teaches agent about photosynthesis
- **Agent**: Asks "What is chlorophyll? How does it capture light?"
- **Result**: If agent can't explain photosynthesis correctly, student realizes they missed key concepts

### Knowledge Verification

- **Professional**: Teaches agent about Kubernetes architecture
- **Agent**: Asks "What's a pod? How does it relate to containers?"
- **Result**: Verifies professional can explain concepts clearly (great for interview prep)

### Content Creation

- **Writer**: Teaches agent about their fictional world
- **Agent**: Asks "What are the rules of magic in your world?"
- **Result**: Reveals inconsistencies or gaps in worldbuilding

### Language Learning

- **Student**: Teaches agent Spanish vocabulary in context
- **Agent**: Asks "¿Qué significa 'la mesa'? ¿Es femenino o masculino?"
- **Result**: Tests active recall and ability to explain grammar rules

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all options:

```env
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional (defaults shown)
LEARNER_MODEL=claude-sonnet-4-20250514
EXTRACTOR_MODEL=claude-haiku-4-5-20251001
APP_ENV=production
LOG_LEVEL=info
```

### Models

You can use different Claude models by changing the environment variables:

- **Learner Agent** (conversation): `claude-sonnet-4-20250514` (recommended)
- **Knowledge Extractor** (background): `claude-haiku-4-5-20251001` (fast and cheap)

Using Haiku for extraction saves ~70% on API costs while maintaining quality.

---

## 💰 Cost Estimate

Typical 20-turn teaching session:

- **Learner Agent**: 20 calls × ~$0.005 = **$0.10**
- **Knowledge Extractor**: 20 calls × ~$0.001 = **$0.02**
- **Assessment**: 1 call × ~$0.01 = **$0.01**

**Total per session: ~$0.13**

For 100 sessions: ~$13 USD

---

## 📚 Core Modules (Reusable)

The following Python modules can be extracted and used in other projects:

### `src/knowledge_graph.py`

Dataclass-based knowledge graph with concepts, relationships, and evidence:

```python
from src.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph("My Topic")
kg.add_concept("photosynthesis", "process plants use to make food", "core")
kg.add_relationship("photosynthesis", "glucose", "functional", "produces")

print(kg.get_stats())
# {'total_concepts': 1, 'total_relationships': 1, ...}
```

### `src/knowledge_builder.py`

Async knowledge extraction using Claude:

```python
from src.knowledge_builder import KnowledgeBuilder

builder = KnowledgeBuilder(api_key="...", model="claude-haiku-4-5-20251001")
await builder.extract_and_update(
    student_message="Plants use sunlight to make glucose",
    knowledge_graph=kg,
    topic_name="Photosynthesis"
)
```

### `src/learner_agent.py`

Conversational agent with system prompts:

```python
from src.learner_agent import LearnerAgent

agent = LearnerAgent(api_key="...", model="claude-sonnet-4-20250514")
response = await agent.generate_response(
    message="Teach me about X",
    system_prompt="You know nothing about X...",
    conversation_history=[...]
)
```

---

## 🤝 Contributing

This is a minimal MVP. Contributions welcome!

### Ideas for Extensions

- [ ] Multi-user support (teachers assign topics to students)
- [ ] Export knowledge graph as JSON/Markdown
- [ ] Voice input/output (Whisper API integration)
- [ ] Comparison mode (diff two knowledge graphs)
- [ ] Curriculum validation (fuzzy match against reference curriculum)
- [ ] Challenge mode (ask hard questions to agent)

### Development Setup

See [Development section](#-development-without-docker) above.

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🙏 Credits

Built on the **protégé effect** research:
- Bargh & Schul (1980) - "On the cognitive benefits of teaching"
- Fiorella & Mayer (2013) - Meta-analysis of learning-by-teaching
- Chase et al. (2009) - Teaching improves knowledge organization

Powered by:
- [Anthropic Claude](https://www.anthropic.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLite](https://www.sqlite.org/)

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/learner-agent-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/learner-agent-core/discussions)

---

## 🎯 What's Next?

This is the **Core MVP**. For a full-featured educational platform with teams, challenges, curriculum diagnostics, and more, see:

👉 **[Learner Agent - Full Platform](https://github.com/yourusername/learner-agent)**

---

**Built with ❤️ for learning and teaching.**
