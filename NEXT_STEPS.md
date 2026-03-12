# 🎯 Next Steps - Getting Started with Learner Agent Core

This document guides you through testing, deploying, and sharing your new MVP.

---

## ✅ What's Been Created

Your `learner-agent-core` repository is ready with:

- ✅ Complete Docker setup (Dockerfile + docker-compose.yml)
- ✅ FastAPI backend with WebSocket support
- ✅ Minimal web UI (single-page app)
- ✅ Core learning modules (knowledge_graph, knowledge_builder, learner_agent)
- ✅ SQLite database (local persistence)
- ✅ Multi-language support (English/Spanish agent responses)
- ✅ Token usage tracking with cost estimation
- ✅ Session continuation with full conversation history
- ✅ Comprehensive README.md and CLAUDE.md
- ✅ MIT License
- ✅ Git repository initialized with commits

**Location:** `/Users/ernestolaval/Documents/Prototipos/learner-agent-core`

---

## 📋 Immediate Next Steps

### Step 1: Configure Your API Key

```bash
cd /Users/ernestolaval/Documents/Prototipos/learner-agent-core

# Copy the example .env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# You can use nano, vim, or VS Code:
code .env
# or
nano .env
```

Edit the file to look like this:

```env
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ACTUAL_KEY_HERE
```

**Get your API key:** https://console.anthropic.com

---

### Step 2: Test with Docker

```bash
# Build the Docker image
# Note: Docker Desktop uses "docker compose" (space), not "docker-compose"
docker compose build

# This will:
# - Download Python 3.12
# - Install all dependencies
# - Create the container
# Takes ~2-3 minutes on first run

# Start the container
docker compose up

# You should see:
# ✅ ANTHROPIC_API_KEY configured
# 🚀 Learner Agent Core API starting...
# 📊 Database: /app/data/learner_agent.db
# Uvicorn running on http://0.0.0.0:8000
```

**Note:** If you're using older Docker Compose V1 (standalone), use `docker-compose` (with hyphen) instead.

**Open your browser:** http://localhost:8000

---

### Step 3: Test a Teaching Session

1. Click **"+ Create New Agent"**
2. Enter a topic, for example: **"How to Make Pizza"**
3. Select language: **English** or **Español**
4. Click **"Start Teaching"**
5. The agent will greet you: *"Hi! I'm excited to learn about How to Make Pizza..."*
6. Teach the agent:
   ```
   You: Pizza is a flatbread topped with tomato sauce, cheese, and toppings, then baked in an oven.

   Agent: Oh interesting! What kind of cheese is used? And what toppings are common?

   You: Mozzarella cheese is the most common. Popular toppings include pepperoni, mushrooms, and bell peppers.

   Agent: I see! So the mozzarella goes on top of the sauce? What temperature do you bake it at?
   ```
7. After teaching, type `/done`
8. Review the assessment — the agent explains pizza using ONLY what you taught
9. **See token usage** and estimated cost at the bottom of the assessment

---

### Step 4: Verify Knowledge Extraction

During teaching, click **"📊 Show Graph"** to see:

- **Concepts**: "pizza", "mozzarella", "pepperoni", "oven", etc.
- **Relationships**: "pizza" → uses → "mozzarella cheese"
- **Evidence**: Your exact quotes

If the graph is empty or incomplete:
- Check backend logs: `docker-compose logs -f`
- Ensure `ANTHROPIC_API_KEY` is set correctly
- Verify you have API credits at https://console.anthropic.com

---

### Step 5: Test Session Continuation

1. Create a new session and teach 3-4 concepts
2. Type `/quit` (not `/done`) to save and exit
3. Click **"View All Sessions"** on the home page
4. Click **"Continue Teaching"** on your session
5. Your entire conversation history should be restored
6. Continue teaching from where you left off

### Step 6: Stop the Container

```bash
# Press Ctrl+C in the terminal

# Or stop in background:
docker compose down
```

Your data is saved in `./data/learner_agent.db` and persists between runs.

---

## 🧪 Testing Checklist

Run through these scenarios to validate the MVP:

### Basic Functionality

- [ ] Create a session with a simple topic (e.g., "Bicycles")
- [ ] Select language (English or Spanish)
- [ ] Teach the agent 3-5 concepts
- [ ] Use `/graph` to view knowledge graph
- [ ] Use `/done` to see assessment
- [ ] Verify agent can explain the topic
- [ ] Check token usage and cost estimation in assessment

### Knowledge Suppression

- [ ] Create session on topic agent "knows" (e.g., "Photosynthesis")
- [ ] Deliberately skip a key concept (e.g., don't mention chlorophyll)
- [ ] In assessment, ask: "What is chlorophyll?"
- [ ] Agent should say: "I don't think my teacher taught me about that"
- [ ] ✅ This proves no knowledge leakage

### Session Persistence

- [ ] Create a session and teach 5 concepts
- [ ] Type `/quit` (not `/done`)
- [ ] Click "📚 My Sessions"
- [ ] Click "Continue" on the incomplete session
- [ ] Verify conversation history is restored
- [ ] Continue teaching
- [ ] Use `/done` to complete

### Edge Cases

- [ ] Create session with very long topic name (100+ chars)
- [ ] Send very long message (500+ words)
- [ ] Type nonsense (e.g., "asdf qwerty") — agent should ask for clarification
- [ ] Disconnect during session (close browser) — verify auto-save worked

---

## 🚀 Deployment Options

### Option A: Share via GitHub (Recommended)

```bash
# Create a new repository on GitHub (via web interface)
# Name: learner-agent-core
# Visibility: Public or Private

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/learner-agent-core.git

# Push
git push -u origin main
```

Now anyone can:

```bash
git clone https://github.com/YOUR_USERNAME/learner-agent-core.git
cd learner-agent-core
cp .env.example .env
# Edit .env with their API key
docker-compose up
```

**Update README.md** line 78 with your actual GitHub URL.

---

### Option B: Share as ZIP File

```bash
# Create distributable zip (excludes .git and data)
zip -r learner-agent-core.zip . \
  -x "*.git*" "data/*.db" "__pycache__/*" "*.pyc" ".DS_Store"

# Send learner-agent-core.zip to colleagues
```

Recipients:
1. Unzip
2. Create `.env` with their API key
3. Run `docker-compose up`

---

### Option C: Deploy to Cloud

**Digital Ocean App Platform:**

```yaml
# app.yaml
name: learner-agent-core
services:
  - name: web
    github:
      repo: YOUR_USERNAME/learner-agent-core
      branch: main
    dockerfile_path: Dockerfile
    envs:
      - key: ANTHROPIC_API_KEY
        scope: RUN_TIME
        type: SECRET
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8000
```

**Fly.io:**

```bash
fly launch
fly secrets set ANTHROPIC_API_KEY=your_key
fly deploy
```

**Render.com:**
1. Connect GitHub repo
2. Create "Web Service"
3. Docker detected automatically
4. Add environment variable: `ANTHROPIC_API_KEY`
5. Deploy

---

## 🐛 Troubleshooting

### "Port 8000 is already in use"

**Symptoms:**
- Error: "bind: address already in use"
- Cannot access http://localhost:8000

**Fix:**

1. Check if port 8000 is available:
   ```bash
   ./scripts/check-port.sh 8000
   ```

2. If port is in use, the script will:
   - Identify the process using the port
   - Suggest an alternative port (e.g., 8001)

3. Use a different port:
   ```bash
   # Option 1: Update .env file
   echo "PORT=8001" >> .env
   docker compose up

   # Option 2: Use environment variable
   PORT=8001 docker compose up
   ```

4. Access the application at the new port:
   ```
   http://localhost:8001
   ```

**Note:** The application always listens on port 8000 inside the container. The `PORT` variable only changes the external port mapping.

---

### "Connection refused" at http://localhost:8000

```bash
# Check if container is running
docker ps

# View logs
docker compose logs -f

# If not running, start again
docker compose up
```

### "Knowledge graph is empty"

**Cause:** Knowledge extraction failing

**Fix:**

1. Check logs: `docker-compose logs -f`
2. Look for errors like:
   ```
   anthropic.AuthenticationError: Invalid API key
   ```
3. Verify `.env` file has correct key:
   ```bash
   cat .env
   ```
4. Restart container:
   ```bash
   docker-compose restart
   ```

### "Agent response is slow"

**Normal:** First response takes 5-10 seconds (model cold start)

**If always slow:**
- Check internet connection
- Check Anthropic API status: https://status.anthropic.com
- Try switching to Haiku for learner agent:
  ```env
  LEARNER_MODEL=claude-haiku-4-5-20251001
  ```

### "WebSocket disconnected"

**Cause:** Network issue or container crash

**Fix:**

1. Check backend logs
2. Refresh browser
3. Session should auto-save, continue from "My Sessions"

### "Database is locked"

**Cause:** Multiple containers accessing same SQLite file

**Fix:**

```bash
# Stop all containers
docker-compose down

# Remove lock file
rm data/*.db-wal data/*.db-journal

# Start fresh
docker-compose up
```

---

## 📊 Monitoring Costs

The application now automatically tracks token usage for every session.

**In-App Monitoring:**
- Token counts displayed at the end of each session assessment
- Estimated cost shown based on Claude API pricing
- Helps you stay within budget

**External Monitoring:**

Track your Anthropic API usage:

1. Visit https://console.anthropic.com
2. Go to "Usage" → "API Usage"
3. Monitor cumulative costs

**Budget alerts:**
- Set a monthly budget limit in Anthropic console
- ~$0.13 per teaching session (20 turns)
- 100 sessions = ~$13 USD
- Token tracking helps predict costs before completing sessions

---

## 🎓 Demo Script (for Presentations)

Use this script when showing the MVP to others:

### Opening (2 min)

"Traditional AI assistants already know everything. This is different — the agent starts knowing nothing. Let me show you."

### Demo (5 min)

1. **Create agent** on unusual topic (e.g., "How to Care for a Pet Iguana")
2. **Teach 3 concepts:**
   - "Iguanas are herbivorous reptiles"
   - "They need UVB light and temperatures of 85-95°F"
   - "Feed them leafy greens like collard and mustard greens"
3. **Show knowledge graph** (`/graph`) — point out concepts and relationships
4. **Finish** (`/done`) — show assessment

### Key Insight (1 min)

"Notice: I didn't mention calcium supplements. Watch what happens when I ask the agent about it..."

**Ask agent:** "What about calcium?"

**Agent responds:** "I don't think you taught me about calcium."

"This reveals my teaching gap. If I were a student, this would show I don't understand iguanas completely."

### Closing (1 min)

"This is the protégé effect: teaching reveals knowledge gaps better than any test. And it's containerized — you can run this on any computer with Docker in 3 commands."

---

## 🔄 Updating the MVP

### Adding a New Feature

1. Create a branch:
   ```bash
   git checkout -b feature/new-feature
   ```

2. Make changes

3. Test with Docker:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up
   ```

4. Commit:
   ```bash
   git add .
   git commit -m "Add new feature: description"
   ```

5. Merge:
   ```bash
   git checkout main
   git merge feature/new-feature
   ```

### Updating Dependencies

```bash
# Edit pyproject.toml
# Add new dependency

# Rebuild Docker image
docker-compose build --no-cache

# Test
docker-compose up
```

---

## 📞 Getting Help

If you encounter issues:

1. **Check logs:** `docker-compose logs -f`
2. **Review CLAUDE.md** for architecture details
3. **Check GitHub Issues** (if repository is public)
4. **Anthropic Community:** https://community.anthropic.com

---

## 🎉 Success Criteria

You'll know the MVP is working when:

- ✅ Agent starts with "I know nothing about {topic}"
- ✅ Agent responds in selected language (English or Spanish)
- ✅ Knowledge graph updates during teaching
- ✅ Assessment uses ONLY taught concepts
- ✅ Agent admits gaps: "You didn't teach me that"
- ✅ Sessions persist across restarts
- ✅ Conversation history restored when continuing
- ✅ Token usage tracked and displayed
- ✅ Total cost per session < $0.20

---

## Next Evolution

Once this MVP is validated, consider:

1. **Sharing with 3-5 beta testers** (educators, students, colleagues)
2. **Gathering feedback** on teaching experience
3. **Iterating on prompts** to improve agent questions
4. **Adding features** from the full platform (teams, challenges)
5. **Publishing** on GitHub for broader distribution

---

**Current Status:** ✅ MVP Ready for Testing (with token tracking & session continuation)

**Location:** `/Users/ernestolaval/Documents/Prototipos/learner-agent-core`

**First Command:** `docker compose up`

**Recent Updates:**
- ✅ Multi-language support (English/Spanish)
- ✅ Token usage tracking with cost estimation
- ✅ Session continuation with full history
- ✅ Updated Docker Compose commands (V2)
- ✅ Configurable port via environment variable
- ✅ Port availability checking script

Good luck! 🚀
