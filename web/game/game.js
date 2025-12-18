/**
 * Alert Alchemy - Phaser 3 Game
 * Main game configuration and state management
 */

// ═══════════════════════════════════════════════════════════════
// Game Constants
// ═══════════════════════════════════════════════════════════════

const GAME_WIDTH = 1280;
const GAME_HEIGHT = 720;
const STORAGE_KEY = 'alert-alchemy-web-state-v2';

const COLORS = {
    background: 0x0a0a12,
    panel: 0x1a1a2e,
    panelLight: 0x16213e,
    accent: 0x06b6d4,
    accentAlt: 0x8b5cf6,
    success: 0x10b981,
    warning: 0xf59e0b,
    danger: 0xef4444,
    text: 0xe8e8e8,
    textDim: 0xa0a0a0,
    grid: 0x1f1f3a
};

const SCORING = {
    base: 100,
    stepPenalty: 10,
    wrongPenalty: 15,
    worsenPenalty: 5,
    quickBonus: 10,
    investigateBonus: 5
};

const TUTORIAL_KEY = 'alert-alchemy-tutorial-seen';

// ═══════════════════════════════════════════════════════════════
// UI Friendly Mappings (display only - internal IDs unchanged)
// ═══════════════════════════════════════════════════════════════

const ACTION_DISPLAY = {
    'rollback': { icon: '↩️', name: 'Roll back release', desc: 'Undo the last deploy', effect: '↓ errors' },
    'scale': { icon: '📈', name: 'Scale up', desc: 'Add more instances', effect: '↓ latency' },
    'restart': { icon: '🔄', name: 'Restart service', desc: 'Quick reset (may not fix root cause)', effect: 'risky' },
    'disable-flag': { icon: '🧯', name: 'Turn off feature', desc: 'Disable risky feature flag', effect: '↓ errors' },
    'increase-pool': { icon: '🧱', name: 'Increase DB pool', desc: 'Raise max connections', effect: '↓ timeouts' },
    'increase_pool': { icon: '🧱', name: 'Increase DB pool', desc: 'Raise max connections', effect: '↓ timeouts' },
    'clear-cache': { icon: '🧼', name: 'Flush cache', desc: 'Clear stale hot keys', effect: '↓ errors' },
    'clear_cache': { icon: '🧼', name: 'Flush cache', desc: 'Clear stale hot keys', effect: '↓ errors' },
    'add-index': { icon: '🗂️', name: 'Add index', desc: 'Speed up slow query (takes time)', effect: '↓ latency' },
    'add_index': { icon: '🗂️', name: 'Add index', desc: 'Speed up slow query (takes time)', effect: '↓ latency' },
};

const METRIC_LABELS = {
    'error_rate': 'Error Rate',
    'p95_latency': 'Latency (p95)',
    'p99_latency': 'Latency (p99)',
    'cpu_usage': 'CPU Usage',
    'memory_usage': 'Memory',
    'request_rate': 'Requests/sec',
    'queue_depth': 'Queue Depth',
    'connection_pool': 'DB Connections'
};

function getActionDisplay(actionId) {
    return ACTION_DISPLAY[actionId] || {
        icon: '⚡',
        name: actionId.replace(/[-_]/g, ' '),
        desc: 'Take this action',
        effect: '?'
    };
}

function getMetricLabel(key) {
    return METRIC_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatEventMessage(type, data) {
    const messages = {
        inspect: `🔍 You inspected ${data.id}. New clues unlocked in Vitals and Timeline.`,
        action_success: `✅ ${getActionDisplay(data.action).name} worked! ${data.id} is now stable.`,
        action_fail: `⚠️ ${getActionDisplay(data.action).name} applied. Watching for changes...`,
        action_worsen: `🔥 That made things worse! Consider a different approach.`,
        tick: `⏰ One minute passed. Step ${data.step}.`,
        resolve: `🎉 Great work! ${data.id} has been resolved.`
    };
    return messages[type] || data.text || 'Something happened.';
}

// ═══════════════════════════════════════════════════════════════
// Global State Manager
// ═══════════════════════════════════════════════════════════════

class GameStateManager {
    constructor() {
        this.state = null;
        this.incidents = [];
        this.soundEnabled = true;
    }

    async loadIncidents() {
        try {
            const response = await fetch('./data/incidents.json');
            if (!response.ok) throw new Error('Failed to load');
            this.incidents = await response.json();
            return true;
        } catch (e) {
            console.error('Failed to load incidents:', e);
            return false;
        }
    }

    hasSavedState() {
        return localStorage.getItem(STORAGE_KEY) !== null;
    }

    loadState() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                this.state = JSON.parse(saved);
                return true;
            }
        } catch (e) {
            console.error('Failed to load state:', e);
        }
        return false;
    }

    saveState() {
        if (this.state) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
        }
    }

    startNewGame() {
        this.state = {
            currentStep: 0,
            score: SCORING.base,
            incidents: this.incidents.map(inc => ({
                ...inc,
                resolved: false,
                resolvedAtStep: null,
                investigated: false,
                actionsTaken: []
            })),
            actionHistory: [],
            events: [],
            startedAt: Date.now(),
            ended: false
        };
        this.saveState();
    }

    resetGame() {
        localStorage.removeItem(STORAGE_KEY);
        this.state = null;
    }

    getActiveIncidents() {
        if (!this.state) return [];
        return this.state.incidents.filter(inc => !inc.resolved);
    }

    getIncidentById(id) {
        if (!this.state) return null;
        return this.state.incidents.find(inc => inc.id === id);
    }

    calculateBlastRadius(incident) {
        const metrics = incident.metrics || {};
        let blast = 0;
        if (metrics.error_rate != null) {
            blast += Math.min(50, (metrics.error_rate / 50) * 50);
        }
        if (metrics.p95_latency != null) {
            blast += Math.min(50, (metrics.p95_latency / 5000) * 50);
        }
        if (blast === 0) {
            const map = { critical: 80, high: 60, medium: 40, low: 20 };
            blast = map[incident.severity?.toLowerCase()] || 40;
        }
        return Math.min(100, Math.round(blast));
    }

    getCorrectAction(incident) {
        if (incident.correct_action) return incident.correct_action;
        const actions = incident.available_actions || incident.default_actions || ['rollback', 'restart', 'scale'];
        const hash = this.simpleHash(incident.id + incident.severity);
        return actions[hash % actions.length];
    }

    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash = hash & hash;
        }
        return Math.abs(hash);
    }

    takeAction(incidentId, actionName) {
        if (!this.state || this.state.ended) return { success: false, message: 'Game not active' };

        const incident = this.getIncidentById(incidentId);
        if (!incident || incident.resolved) {
            return { success: false, message: 'Invalid incident' };
        }

        this.state.currentStep++;

        const correct = this.getCorrectAction(incident);
        const isCorrect = actionName === correct;
        const isWorsening = !isCorrect && ['restart', 'reboot', 'kill'].some(k => actionName.includes(k));

        const record = {
            step: this.state.currentStep,
            incidentId: incident.id,
            action: actionName,
            wasCorrect: isCorrect,
            worsened: isWorsening
        };
        this.state.actionHistory.push(record);
        incident.actionsTaken.push(actionName);

        let message = '';
        let delta = 0;

        if (isCorrect) {
            incident.resolved = true;
            incident.resolvedAtStep = this.state.currentStep;
            message = `✓ ${incident.id} resolved!`;
            if (this.state.currentStep <= 2) delta = SCORING.quickBonus;
            if (incident.investigated) delta += SCORING.investigateBonus;
        } else {
            delta = -SCORING.wrongPenalty;
            if (isWorsening) {
                delta -= SCORING.worsenPenalty;
                message = '⚠️ Situation worsened!';
            } else {
                message = 'Action taken, not resolved.';
            }
        }

        this.state.score = this.calculateScore();
        this.addEvent(message);
        this.saveState();

        return { success: isCorrect, message, delta };
    }

    investigate(incidentId) {
        const incident = this.getIncidentById(incidentId);
        if (incident && !incident.investigated) {
            incident.investigated = true;
            this.addEvent(`🔍 Investigated ${incident.id}`);
            this.saveState();
        }
    }

    tick() {
        if (!this.state || this.state.ended) return;
        this.state.currentStep++;
        this.state.score = this.calculateScore();
        this.addEvent(`⏰ Time advanced to step ${this.state.currentStep}`);
        this.saveState();
    }

    endGame() {
        if (!this.state) return;
        this.state.ended = true;
        this.state.endedAt = Date.now();
        this.state.score = this.calculateScore();
        this.saveState();
    }

    calculateScore() {
        let score = SCORING.base;
        score -= this.state.currentStep * SCORING.stepPenalty;

        for (const action of this.state.actionHistory) {
            if (!action.wasCorrect) score -= SCORING.wrongPenalty;
            if (action.worsened) score -= SCORING.worsenPenalty;
        }

        for (const inc of this.state.incidents) {
            if (inc.resolved && inc.resolvedAtStep <= 2) {
                score += SCORING.quickBonus;
            }
            if (inc.resolved && inc.investigated) {
                score += SCORING.investigateBonus;
            }
        }

        return score;
    }

    addEvent(text) {
        if (!this.state) return;
        this.state.events.unshift({
            time: Date.now(),
            text
        });
        if (this.state.events.length > 20) {
            this.state.events.pop();
        }
    }

    allResolved() {
        if (!this.state) return false;
        return this.state.incidents.every(inc => inc.resolved);
    }
}

// Global instance
const gameState = new GameStateManager();

// ═══════════════════════════════════════════════════════════════
// Sound Manager (WebAudio beeps)
// ═══════════════════════════════════════════════════════════════

class SoundManager {
    constructor() {
        this.ctx = null;
        this.enabled = true;
    }

    init() {
        try {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('WebAudio not available');
        }
    }

    play(type) {
        if (!this.enabled || !this.ctx) return;

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.connect(gain);
        gain.connect(this.ctx.destination);

        switch (type) {
            case 'click':
                osc.frequency.value = 600;
                gain.gain.value = 0.1;
                osc.start();
                osc.stop(this.ctx.currentTime + 0.05);
                break;
            case 'resolve':
                osc.frequency.value = 880;
                gain.gain.value = 0.15;
                osc.start();
                osc.frequency.linearRampToValueAtTime(1320, this.ctx.currentTime + 0.1);
                osc.stop(this.ctx.currentTime + 0.15);
                break;
            case 'warning':
                osc.frequency.value = 220;
                osc.type = 'sawtooth';
                gain.gain.value = 0.1;
                osc.start();
                osc.stop(this.ctx.currentTime + 0.2);
                break;
            case 'error':
                osc.frequency.value = 150;
                osc.type = 'square';
                gain.gain.value = 0.08;
                osc.start();
                osc.stop(this.ctx.currentTime + 0.15);
                break;
        }
    }

    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }
}

const soundManager = new SoundManager();

// ═══════════════════════════════════════════════════════════════
// Phaser Game Config
// ═══════════════════════════════════════════════════════════════

const config = {
    type: Phaser.AUTO,
    width: GAME_WIDTH,
    height: GAME_HEIGHT,
    parent: 'game-container',
    backgroundColor: COLORS.background,
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    scene: [MenuScene, WorldScene, IncidentScene]
};

// Start the game
const game = new Phaser.Game(config);
