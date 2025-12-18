/**
 * Alert Alchemy - Web Game
 * Pure client-side game logic with localStorage persistence
 */

// ═══════════════════════════════════════════════════════════════
// Game State
// ═══════════════════════════════════════════════════════════════

const STORAGE_KEY = 'alertAlchemyState';
const BASE_SCORE = 100;
const PENALTY_PER_STEP = 10;
const PENALTY_WRONG_ACTION = 15;
const PENALTY_WORSEN = 5;
const BONUS_QUICK_RESOLVE = 10;

let gameState = null;
let incidentsData = [];
let selectedIncidentId = null;

// ═══════════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkExistingGame();
});

function initEventListeners() {
    // Landing screen
    document.getElementById('btn-start').addEventListener('click', startGame);
    document.getElementById('btn-how-to-play').addEventListener('click', showHowToPlay);
    document.getElementById('btn-close-how-to').addEventListener('click', hideHowToPlay);
    document.querySelector('.overlay-close').addEventListener('click', hideHowToPlay);
    
    // Game screen
    document.getElementById('btn-end-game').addEventListener('click', endGame);
    document.getElementById('btn-tick').addEventListener('click', tick);
    document.getElementById('btn-close-detail').addEventListener('click', closeDetail);
    document.getElementById('btn-take-action').addEventListener('click', takeAction);
    
    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Game end screen
    document.getElementById('btn-share').addEventListener('click', shareScore);
    document.getElementById('btn-play-again').addEventListener('click', playAgain);
}

function checkExistingGame() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
        try {
            gameState = JSON.parse(saved);
            if (!gameState.ended) {
                // Resume existing game
                loadIncidentsAndResume();
                return;
            }
        } catch (e) {
            console.error('Failed to parse saved state:', e);
        }
    }
    // Show landing
    showScreen('landing');
}

// ═══════════════════════════════════════════════════════════════
// Screen Management
// ═══════════════════════════════════════════════════════════════

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => {
        s.classList.remove('active');
        s.classList.add('hidden');
    });
    const screen = document.getElementById(screenId);
    screen.classList.remove('hidden');
    screen.classList.add('active');
}

function showHowToPlay() {
    document.getElementById('how-to-play-overlay').classList.remove('hidden');
}

function hideHowToPlay() {
    document.getElementById('how-to-play-overlay').classList.add('hidden');
}

// ═══════════════════════════════════════════════════════════════
// Game Logic
// ═══════════════════════════════════════════════════════════════

async function loadIncidents() {
    try {
        const response = await fetch('./data/incidents.json');
        if (!response.ok) throw new Error('Failed to load incidents');
        incidentsData = await response.json();
        return true;
    } catch (e) {
        console.error('Error loading incidents:', e);
        showToast('Failed to load incidents. Please try again.', 'error');
        return false;
    }
}

async function startGame() {
    const loaded = await loadIncidents();
    if (!loaded) return;
    
    // Initialize game state
    gameState = {
        currentStep: 0,
        score: BASE_SCORE,
        incidents: incidentsData.map(inc => ({
            ...inc,
            resolved: false,
            resolvedAtStep: null,
            actionsTaken: []
        })),
        actionsTaken: [],
        startedAt: new Date().toISOString(),
        ended: false,
        endedAt: null
    };
    
    saveState();
    showScreen('game');
    renderGame();
    showToast('🎮 Game started! Good luck!', 'success');
}

async function loadIncidentsAndResume() {
    const loaded = await loadIncidents();
    if (!loaded) {
        showScreen('landing');
        return;
    }
    showScreen('game');
    renderGame();
    showToast('Welcome back! Game resumed.', 'success');
}

function tick() {
    if (!gameState || gameState.ended) return;
    
    gameState.currentStep++;
    gameState.score = calculateScore();
    saveState();
    renderGame();
    showToast(`⏰ Time advanced to step ${gameState.currentStep}`, 'success');
}

function takeAction() {
    if (!gameState || gameState.ended || !selectedIncidentId) return;
    
    const actionSelect = document.getElementById('action-select');
    const actionName = actionSelect.value;
    
    if (!actionName) {
        showToast('Please select an action!', 'error');
        return;
    }
    
    const incident = gameState.incidents.find(inc => inc.id === selectedIncidentId);
    if (!incident || incident.resolved) {
        showToast('Incident already resolved!', 'error');
        return;
    }
    
    // Advance time
    gameState.currentStep++;
    
    // Check if action is correct
    const correctAction = getCorrectAction(incident);
    const isCorrect = actionName === correctAction;
    const worsened = didActionWorsen(incident, actionName);
    
    // Record action
    const actionRecord = {
        step: gameState.currentStep,
        incidentId: incident.id,
        action: actionName,
        wasCorrect: isCorrect,
        worsened: worsened
    };
    gameState.actionsTaken.push(actionRecord);
    incident.actionsTaken.push(actionName);
    
    if (isCorrect) {
        incident.resolved = true;
        incident.resolvedAtStep = gameState.currentStep;
        showToast(`✓ ${incident.id} resolved!`, 'success');
    } else {
        showToast(worsened ? '⚠️ Action taken, situation may have worsened!' : 'Action taken, but not resolved.', 'error');
    }
    
    // Update score
    gameState.score = calculateScore();
    saveState();
    renderGame();
    
    // Check if all resolved
    const allResolved = gameState.incidents.every(inc => inc.resolved);
    if (allResolved) {
        setTimeout(() => endGame(), 1000);
    }
}

function getCorrectAction(incident) {
    // Check for explicit correct_action in data
    if (incident.correct_action) return incident.correct_action;
    
    // Check resolution/optimal_path
    if (incident.resolution?.optimal_path?.[0]) {
        return incident.resolution.optimal_path[0];
    }
    
    // Deterministic fallback based on severity and id
    const actions = incident.available_actions || ['rollback', 'restart', 'scale'];
    const hash = simpleHash(incident.id + incident.severity);
    return actions[hash % actions.length];
}

function didActionWorsen(incident, action) {
    const worsenKeywords = ['restart', 'reboot', 'delete', 'drop', 'kill'];
    const correctAction = getCorrectAction(incident);
    
    if (action !== correctAction) {
        return worsenKeywords.some(kw => action.toLowerCase().includes(kw));
    }
    return false;
}

function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash = hash & hash;
    }
    return Math.abs(hash);
}

function calculateScore() {
    let score = BASE_SCORE;
    
    // Penalty for elapsed time
    score -= gameState.currentStep * PENALTY_PER_STEP;
    
    // Penalty for wrong actions
    for (const action of gameState.actionsTaken) {
        if (!action.wasCorrect) score -= PENALTY_WRONG_ACTION;
        if (action.worsened) score -= PENALTY_WORSEN;
    }
    
    // Bonus for quick resolutions
    for (const incident of gameState.incidents) {
        if (incident.resolved && incident.resolvedAtStep <= 2) {
            score += BONUS_QUICK_RESOLVE;
        }
    }
    
    return score;
}

function calculateBlastRadius(incident) {
    const metrics = incident.metrics || {};
    let components = [];
    
    if (metrics.error_rate != null) {
        components.push(Math.min(50, (metrics.error_rate / 50) * 50));
    }
    if (metrics.p95_latency != null) {
        components.push(Math.min(50, (metrics.p95_latency / 5000) * 50));
    }
    
    if (components.length === 0) {
        const severityMap = { critical: 80, high: 60, medium: 40, low: 20 };
        return severityMap[incident.severity?.toLowerCase()] || 40;
    }
    
    return Math.min(100, Math.round(components.reduce((a, b) => a + b, 0)));
}

function endGame() {
    if (!gameState) return;
    
    gameState.ended = true;
    gameState.endedAt = new Date().toISOString();
    gameState.score = calculateScore();
    saveState();
    
    renderGameEnd();
    showScreen('game-end');
}

function playAgain() {
    localStorage.removeItem(STORAGE_KEY);
    gameState = null;
    selectedIncidentId = null;
    showScreen('landing');
}

// ═══════════════════════════════════════════════════════════════
// Rendering
// ═══════════════════════════════════════════════════════════════

function renderGame() {
    if (!gameState) return;
    
    // Update stats
    document.getElementById('stat-step').textContent = gameState.currentStep;
    document.getElementById('stat-score').textContent = gameState.score;
    
    const resolved = gameState.incidents.filter(inc => inc.resolved).length;
    document.getElementById('stat-resolved').textContent = `${resolved}/${gameState.incidents.length}`;
    
    // Render incidents list
    renderIncidentsList();
    
    // Update detail panel if incident selected
    if (selectedIncidentId) {
        renderDetailPanel();
    }
}

function renderIncidentsList() {
    const container = document.getElementById('incidents-list');
    container.innerHTML = '';
    
    // Sort by blast radius (highest first), then by resolved status
    const sorted = [...gameState.incidents].sort((a, b) => {
        if (a.resolved !== b.resolved) return a.resolved ? 1 : -1;
        return calculateBlastRadius(b) - calculateBlastRadius(a);
    });
    
    for (const incident of sorted) {
        const card = createIncidentCard(incident);
        container.appendChild(card);
    }
}

function createIncidentCard(incident) {
    const blast = calculateBlastRadius(incident);
    const blastClass = blast >= 70 ? 'blast-high' : (blast >= 40 ? 'blast-medium' : 'blast-low');
    
    const card = document.createElement('div');
    card.className = `incident-card${incident.resolved ? ' resolved' : ''}${selectedIncidentId === incident.id ? ' selected' : ''}`;
    card.innerHTML = `
        <div class="incident-card-header">
            <span class="incident-id">${incident.id}</span>
            <span class="severity-badge severity-${incident.severity?.toLowerCase() || 'medium'}">${incident.severity || 'Medium'}</span>
        </div>
        <div class="incident-title">${incident.title || 'Untitled Incident'}</div>
        <div class="blast-radius">
            <span>Blast:</span>
            <div class="blast-bar">
                <div class="blast-fill ${blastClass}" style="width: ${blast}%"></div>
            </div>
            <span>${blast}</span>
        </div>
        ${incident.resolved ? '<div style="color: var(--accent-success); font-size: 0.8rem; margin-top: 0.5rem;">✓ Resolved</div>' : ''}
    `;
    
    card.addEventListener('click', () => selectIncident(incident.id));
    return card;
}

function selectIncident(incidentId) {
    selectedIncidentId = incidentId;
    renderGame();
    renderDetailPanel();
    document.getElementById('detail-panel').classList.remove('hidden');
}

function closeDetail() {
    selectedIncidentId = null;
    document.getElementById('detail-panel').classList.add('hidden');
    renderIncidentsList();
}

function renderDetailPanel() {
    const incident = gameState.incidents.find(inc => inc.id === selectedIncidentId);
    if (!incident) return;
    
    // Header
    document.getElementById('detail-title').textContent = `${incident.id}: ${incident.title || 'Incident'}`;
    
    // Info tab
    document.getElementById('detail-description').innerHTML = `
        <p>${incident.description || 'No description available.'}</p>
    `;
    document.getElementById('detail-services').innerHTML = incident.services?.length ? `
        <h4>Affected Services</h4>
        <p>${incident.services.join(', ')}</p>
    ` : '';
    
    // Logs tab
    const logs = incident.logs || [];
    document.getElementById('detail-logs').textContent = logs.length ? logs.join('\n') : 'No logs available.';
    
    // Metrics tab
    const metrics = incident.metrics || {};
    const metricsHtml = Object.entries(metrics).filter(([k, v]) => v != null).map(([key, value]) => `
        <div class="metric-card">
            <div class="metric-value">${typeof value === 'number' ? value.toFixed(1) : value}</div>
            <div class="metric-label">${key.replace(/_/g, ' ')}</div>
        </div>
    `).join('');
    document.getElementById('detail-metrics').innerHTML = metricsHtml ? `<div class="metrics-grid">${metricsHtml}</div>` : 'No metrics available.';
    
    // Traces tab
    const traces = incident.traces || [];
    document.getElementById('detail-traces').textContent = traces.length ? traces.join('\n') : 'No traces available.';
    
    // Action area
    const correctAction = getCorrectAction(incident);
    document.getElementById('suggested-action').innerHTML = incident.resolved 
        ? '✓ This incident has been resolved.'
        : `💡 <strong>Suggested:</strong> Try <code>${correctAction}</code> based on the symptoms.`;
    
    // Populate action dropdown
    const select = document.getElementById('action-select');
    const actions = incident.available_actions || ['rollback', 'scale', 'restart', 'disable-flag', 'increase-pool', 'clear-cache'];
    select.innerHTML = '<option value="">Select an action...</option>' + 
        actions.map(a => `<option value="${a}">${a}</option>`).join('');
    select.disabled = incident.resolved;
    document.getElementById('btn-take-action').disabled = incident.resolved;
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.remove('active');
        p.classList.add('hidden');
    });
    
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    const pane = document.getElementById(`tab-${tabName}`);
    pane.classList.remove('hidden');
    pane.classList.add('active');
}

function renderGameEnd() {
    document.getElementById('final-score').textContent = gameState.score;
    
    // Score breakdown
    const resolved = gameState.incidents.filter(inc => inc.resolved).length;
    const wrongActions = gameState.actionsTaken.filter(a => !a.wasCorrect).length;
    const quickResolves = gameState.incidents.filter(inc => inc.resolved && inc.resolvedAtStep <= 2).length;
    
    document.getElementById('score-breakdown').innerHTML = `
        <div><span>Base score:</span><span>+${BASE_SCORE}</span></div>
        <div><span>Steps taken (${gameState.currentStep} × -${PENALTY_PER_STEP}):</span><span>-${gameState.currentStep * PENALTY_PER_STEP}</span></div>
        <div><span>Wrong actions (${wrongActions} × -${PENALTY_WRONG_ACTION}):</span><span>-${wrongActions * PENALTY_WRONG_ACTION}</span></div>
        <div><span>Quick resolves (${quickResolves} × +${BONUS_QUICK_RESOLVE}):</span><span>+${quickResolves * BONUS_QUICK_RESOLVE}</span></div>
        <div><span>Incidents resolved:</span><span>${resolved}/${gameState.incidents.length}</span></div>
    `;
}

// ═══════════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════════

function saveState() {
    if (gameState) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(gameState));
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function shareScore() {
    if (!gameState) return;
    
    const text = `🧪 Alert Alchemy Score: ${gameState.score}\n` +
        `Steps: ${gameState.currentStep} | ` +
        `Resolved: ${gameState.incidents.filter(i => i.resolved).length}/${gameState.incidents.length}\n` +
        `Play at: ${window.location.origin}${window.location.pathname}`;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('📋 Score copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}
