// Learner Agent Core - Client-side JavaScript

const API_BASE = window.location.origin;

// Global state
let currentSessionId = null;
let websocket = null;

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize i18n
    await i18n.init();

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
    const language = document.getElementById('language-select').value;
    if (!topicName) return;

    try {
        const response = await fetch(`${API_BASE}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic_name: topicName, language: language })
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
    listContainer.innerHTML = `<p class="loading">${i18n.t('sessions.loading')}</p>`;

    try {
        const response = await fetch(`${API_BASE}/api/sessions?limit=50`);
        const sessions = await response.json();

        if (sessions.length === 0) {
            listContainer.innerHTML = `<p class="loading">${i18n.t('sessions.empty')}</p>`;
            return;
        }

        listContainer.innerHTML = '';

        sessions.forEach(session => {
            const card = document.createElement('div');
            card.className = 'session-card';

            const completed = session.completed_at ? '✅' : '🔄';
            const date = new Date(session.created_at).toLocaleDateString();
            const statusText = session.completed_at ? i18n.t('sessions.completed') : i18n.t('sessions.inProgress');
            const turnsText = i18n.t('sessions.meta.turns');
            const conceptsText = i18n.t('sessions.meta.concepts');

            card.innerHTML = `
                <div class="session-info">
                    <h3>${completed} ${escapeHtml(session.topic_name)}</h3>
                    <div class="session-meta">
                        <span>📅 ${date}</span>
                        <span>💬 ${session.total_turns} ${turnsText}</span>
                        <span>🧠 ${session.concepts_extracted} ${conceptsText}</span>
                        <span style="color: ${session.completed_at ? '#16a34a' : '#ea580c'};">● ${statusText}</span>
                    </div>
                </div>
                <div class="session-actions">
                    <button class="btn btn-secondary" onclick="continueSession(${session.id})">
                        ${i18n.t('sessions.continueButton')}
                    </button>
                    <button class="btn-command" onclick="deleteSession(${session.id})" title="${i18n.t('sessions.deleteButton')}">
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
    if (!confirm(i18n.t('sessions.deleteConfirm'))) {
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
    document.getElementById('stat-turns').innerHTML = `${session.total_turns} <span data-i18n="teaching.stats.turns">${i18n.t('teaching.stats.turns')}</span>`;
    document.getElementById('stat-concepts').innerHTML = `${session.concepts_extracted} <span data-i18n="teaching.stats.concepts">${i18n.t('teaching.stats.concepts')}</span>`;
    document.getElementById('stat-relationships').innerHTML = `${session.relationships_extracted} <span data-i18n="teaching.stats.relationships">${i18n.t('teaching.stats.relationships')}</span>`;

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
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addStatusMessage(i18n.t('status.error', {message: 'Connection error'}));
    };

    websocket.onclose = () => {
        console.log('WebSocket closed');
        addStatusMessage(i18n.t('status.sessionEnded'));
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'agent_message':
            addAgentMessage(data.content);
            break;

        case 'student_message_history':
            addStudentMessage(data.content);
            break;

        case 'status':
            // Translate common status messages
            let statusMessage = data.content;

            // Match patterns and translate
            if (statusMessage.startsWith('Connected to teaching session for')) {
                const topic = statusMessage.match(/'([^']+)'/)?.[1];
                if (topic) {
                    statusMessage = i18n.t('status.connected', {topic});
                }
            } else if (statusMessage.startsWith('Resuming session with')) {
                const turns = statusMessage.match(/(\d+)/)?.[1];
                if (turns) {
                    statusMessage = i18n.t('status.resuming', {turns});
                }
            } else if (statusMessage.includes('Session saved')) {
                statusMessage = i18n.t('status.saved');
            } else if (statusMessage.includes('Generating assessment')) {
                statusMessage = i18n.t('status.generating');
            } else if (statusMessage.includes('Session completed')) {
                statusMessage = i18n.t('status.completed');
            }

            addStatusMessage(statusMessage);
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
            addStatusMessage(i18n.t('status.error', {message: data.content}));
            break;
    }
}

function addAgentMessage(content) {
    // Hide typing indicator when agent responds
    hideTypingIndicator();

    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-agent';
    messageDiv.innerHTML = `
        <div class="message-role">${i18n.t('teaching.messageRoles.agent')}</div>
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
        <div class="message-role">${i18n.t('teaching.messageRoles.you')}</div>
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
        <div class="message-role">${i18n.t('teaching.messageRoles.agent')}</div>
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
    document.getElementById('stat-concepts').innerHTML = `${stats.concepts || 0} <span data-i18n="teaching.stats.concepts">${i18n.t('teaching.stats.concepts')}</span>`;
    document.getElementById('stat-relationships').innerHTML = `${stats.relationships || 0} <span data-i18n="teaching.stats.relationships">${i18n.t('teaching.stats.relationships')}</span>`;
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
        addStatusMessage(i18n.t('status.generatingGraph'));
    } else if (command === '/done') {
        addStatusMessage(i18n.t('status.finalizingSession'));
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

    let html = `<h4>${i18n.t('graph.concepts')}</h4>`;
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
        html += `<h4 style="margin-top: 1.5rem;">${i18n.t('graph.relationships')}</h4>`;
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
            <h4 style="color: #2563eb; margin-bottom: 1rem;">${i18n.t('assessment.whatLearned')}</h4>
            <p style="white-space: pre-wrap;">${escapeHtml(assessmentData.assessment)}</p>
        </div>
    `;

    html += `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${assessmentData.stats.concepts || 0}</div>
                <div class="stat-label">${i18n.t('assessment.stats.conceptsLearned')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${assessmentData.stats.relationships || 0}</div>
                <div class="stat-label">${i18n.t('assessment.stats.relationships')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${assessmentData.stats.evidence || 0}</div>
                <div class="stat-label">${i18n.t('assessment.stats.evidence')}</div>
            </div>
        </div>
    `;

    // Add token usage section if available
    if (assessmentData.tokens) {
        const estimatedCost = (assessmentData.tokens.total / 1000000 * 3).toFixed(4);
        html += `
            <div style="margin-top: 1.5rem; padding: 1.5rem; background: #f9fafb; border-radius: 0.5rem; border: 1px solid #e5e7eb;">
                <h4 style="margin-bottom: 1rem; color: #374151;">${i18n.t('assessment.tokens.title')}</h4>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${assessmentData.tokens.input.toLocaleString()}</div>
                        <div class="stat-label">${i18n.t('assessment.tokens.input')}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${assessmentData.tokens.output.toLocaleString()}</div>
                        <div class="stat-label">${i18n.t('assessment.tokens.output')}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${assessmentData.tokens.total.toLocaleString()}</div>
                        <div class="stat-label">${i18n.t('assessment.tokens.total')}</div>
                    </div>
                </div>
                <p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
                    ${i18n.t('assessment.tokens.cost', {cost: estimatedCost})}
                    <br><small>${i18n.t('assessment.tokens.costNote')}</small>
                </p>
            </div>
        `;
    }

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

// ===== I18N =====

async function changeUILanguage(lang) {
    await i18n.changeLanguage(lang);
}

// ===== UTILITIES =====

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
