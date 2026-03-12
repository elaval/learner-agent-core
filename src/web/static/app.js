// Learner Agent Core - Client-side JavaScript

const API_BASE = window.location.origin;

// Global state
let currentSessionId = null;
let websocket = null;

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    showLanding();
});

// ===== VIEW NAVIGATION =====

function showView(viewId) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.add('hidden');
    });
    document.getElementById(viewId).classList.remove('hidden');
}

function showLanding() {
    showView('landing-view');
    loadStats();
}

function showCreateAgent() {
    showView('create-view');
    document.getElementById('topic-input').focus();
}

function showSessionsList() {
    showView('sessions-view');
    loadSessions();
}

// ===== STATS =====

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const stats = await response.json();

        document.getElementById('total-sessions').textContent =
            Math.round(stats.total_sessions || 0);
        document.getElementById('total-topics').textContent =
            Math.round(stats.unique_topics || 0);
        document.getElementById('avg-concepts').textContent =
            (stats.avg_concepts || 0).toFixed(1);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ===== CREATE AGENT =====

async function createAgent(event) {
    event.preventDefault();

    const topicName = document.getElementById('topic-input').value.trim();
    if (!topicName) return;

    try {
        const response = await fetch(`${API_BASE}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic_name: topicName })
        });

        if (!response.ok) {
            throw new Error('Failed to create session');
        }

        const session = await response.json();
        currentSessionId = session.id;

        // Start teaching
        startTeachingSession(session);

    } catch (error) {
        console.error('Error creating agent:', error);
        alert('Error creating agent. Please try again.');
    }
}

// ===== SESSIONS LIST =====

async function loadSessions() {
    const listContainer = document.getElementById('sessions-list');
    listContainer.innerHTML = '<p class="loading">Loading sessions...</p>';

    try {
        const response = await fetch(`${API_BASE}/api/sessions?limit=50`);
        const sessions = await response.json();

        if (sessions.length === 0) {
            listContainer.innerHTML = '<p class="loading">No sessions yet. Create your first agent!</p>';
            return;
        }

        listContainer.innerHTML = '';

        sessions.forEach(session => {
            const card = document.createElement('div');
            card.className = 'session-card';

            const completed = session.completed_at ? '✅' : '🔄';
            const date = new Date(session.created_at).toLocaleDateString();

            card.innerHTML = `
                <div class="session-info">
                    <h3>${completed} ${session.topic_name}</h3>
                    <div class="session-meta">
                        <span>📅 ${date}</span>
                        <span>💬 ${session.total_turns} turns</span>
                        <span>🧠 ${session.concepts_extracted} concepts</span>
                    </div>
                </div>
                <div class="session-actions">
                    <button class="btn btn-secondary" onclick="continueSession(${session.id})">
                        ${session.completed_at ? 'View' : 'Continue'}
                    </button>
                    <button class="btn-command" onclick="deleteSession(${session.id})">
                        🗑️
                    </button>
                </div>
            `;

            listContainer.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading sessions:', error);
        listContainer.innerHTML = '<p class="loading">Error loading sessions</p>';
    }
}

async function continueSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
        const session = await response.json();

        currentSessionId = session.id;
        startTeachingSession(session);

    } catch (error) {
        console.error('Error loading session:', error);
        alert('Error loading session');
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Delete this session? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadSessions();
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        alert('Error deleting session');
    }
}

// ===== TEACHING SESSION =====

function startTeachingSession(session) {
    showView('teaching-view');

    document.getElementById('teaching-topic').textContent = session.topic_name;
    document.getElementById('stat-turns').textContent = `${session.total_turns} turns`;
    document.getElementById('stat-concepts').textContent = `${session.concepts_extracted} concepts`;
    document.getElementById('stat-relationships').textContent = `${session.relationships_extracted} relationships`;

    // Clear chat
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('chat-input').value = '';

    // Connect WebSocket
    connectWebSocket(session.id);
}

function connectWebSocket(sessionId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/teach/${sessionId}`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('WebSocket connected');
        addStatusMessage('Connected to teaching session');
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addStatusMessage('Connection error');
    };

    websocket.onclose = () => {
        console.log('WebSocket closed');
        addStatusMessage('Session ended');
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'agent_message':
            addAgentMessage(data.content);
            break;

        case 'status':
            addStatusMessage(data.content);
            break;

        case 'stats_update':
            updateStats(data.content);
            break;

        case 'knowledge_graph':
            showKnowledgeGraph(data.content);
            break;

        case 'assessment':
            showAssessment(data.content);
            break;

        case 'error':
            addStatusMessage(`Error: ${data.content}`);
            break;
    }
}

function addAgentMessage(content) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-agent';
    messageDiv.innerHTML = `
        <div class="message-role">Agent</div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addStudentMessage(content) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-student';
    messageDiv.innerHTML = `
        <div class="message-role">You</div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addStatusMessage(content) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-status';
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(content)}</div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');

    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'message message-agent';
    indicator.innerHTML = `
        <div class="message-role">Agent</div>
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;

    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function updateStats(stats) {
    document.getElementById('stat-turns').textContent = `${stats.total_concepts || 0} turns`;
    document.getElementById('stat-concepts').textContent = `${stats.total_concepts || 0} concepts`;
    document.getElementById('stat-relationships').textContent = `${stats.total_relationships || 0} relationships`;
}

// ===== CHAT INPUT =====

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message || !websocket) return;

    // Add to chat
    addStudentMessage(message);

    // Send via WebSocket
    websocket.send(JSON.stringify({
        type: 'student_message',
        content: message
    }));

    // Clear input
    input.value = '';

    // Show typing indicator
    showTypingIndicator();
    setTimeout(hideTypingIndicator, 60000); // Remove after 1 minute max
}

function sendCommand(command) {
    if (!websocket) return;

    websocket.send(JSON.stringify({
        type: 'command',
        content: command
    }));

    if (command === '/graph') {
        addStatusMessage('Generating knowledge graph...');
    } else if (command === '/done') {
        addStatusMessage('Finalizing session and generating assessment...');
    }
}

function handleChatKeydown(event) {
    // Send on Enter (without Shift)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function endTeaching() {
    if (websocket) {
        websocket.close();
        websocket = null;
    }
    showLanding();
}

// ===== KNOWLEDGE GRAPH MODAL =====

function showKnowledgeGraph(graphData) {
    const modal = document.getElementById('graph-modal');
    const content = document.getElementById('graph-content');

    let html = '<h4>Concepts</h4>';
    html += '<ul class="concept-list">';

    for (const [name, concept] of Object.entries(graphData.concepts || {})) {
        html += `
            <li class="concept-item">
                <div class="concept-name">${escapeHtml(name)}</div>
                <div class="concept-definition">${escapeHtml(concept.definition || '')}</div>
            </li>
        `;
    }

    html += '</ul>';

    if (graphData.relationships && graphData.relationships.length > 0) {
        html += '<h4 style="margin-top: 1.5rem;">Relationships</h4>';
        html += '<div class="relationships-list">';

        graphData.relationships.forEach(rel => {
            html += `
                <div class="relationship-item">
                    <strong>${escapeHtml(rel.source)}</strong>
                    ${escapeHtml(rel.label)}
                    <strong>${escapeHtml(rel.target)}</strong>
                </div>
            `;
        });

        html += '</div>';
    }

    content.innerHTML = html;
    modal.classList.remove('hidden');
}

// ===== ASSESSMENT MODAL =====

function showAssessment(assessmentData) {
    const modal = document.getElementById('assessment-modal');
    const content = document.getElementById('assessment-content');

    let html = `
        <div style="background: #eff6ff; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
            <h4 style="color: #2563eb; margin-bottom: 1rem;">What the Agent Learned</h4>
            <p style="white-space: pre-wrap;">${escapeHtml(assessmentData.assessment)}</p>
        </div>
    `;

    html += `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${assessmentData.stats.total_concepts}</div>
                <div class="stat-label">Concepts Learned</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${assessmentData.stats.total_relationships}</div>
                <div class="stat-label">Relationships</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${assessmentData.stats.total_evidence}</div>
                <div class="stat-label">Evidence</div>
            </div>
        </div>
    `;

    content.innerHTML = html;
    modal.classList.remove('hidden');

    // Close WebSocket
    if (websocket) {
        websocket.close();
        websocket = null;
    }
}

// ===== MODAL UTILITIES =====

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// ===== UTILITIES =====

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
