/**
 * IncidentScene - Detail overlay for inspecting and acting on incidents
 */
class IncidentScene extends Phaser.Scene {
    constructor() {
        super({ key: 'IncidentScene' });
        this.incident = null;
        this.activeTab = 'briefing';
    }

    init(data) {
        this.incidentId = data.incidentId;
    }

    create() {
        this.incident = gameState.getIncidentById(this.incidentId);
        if (!this.incident) {
            this.closeScene();
            return;
        }

        const { width, height } = this.cameras.main;

        // Dark overlay
        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.7);
        overlay.fillRect(0, 0, width, height);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, width, height), Phaser.Geom.Rectangle.Contains);

        // Main panel
        this.panelX = 80;
        this.panelY = 50;
        this.panelWidth = width - 160;
        this.panelHeight = height - 100;

        const panel = this.add.graphics();
        panel.fillStyle(COLORS.panel, 1);
        panel.lineStyle(2, COLORS.accent, 1);
        panel.fillRoundedRect(this.panelX, this.panelY, this.panelWidth, this.panelHeight, 16);
        panel.strokeRoundedRect(this.panelX, this.panelY, this.panelWidth, this.panelHeight, 16);

        // Close button
        const closeBtn = this.add.text(this.panelX + this.panelWidth - 40, this.panelY + 20, '✕', {
            fontSize: '28px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#a0a0a0'
        }).setInteractive({ useHandCursor: true });
        closeBtn.on('pointerdown', () => this.closeScene());
        closeBtn.on('pointerover', () => closeBtn.setColor('#e8e8e8'));
        closeBtn.on('pointerout', () => closeBtn.setColor('#a0a0a0'));

        // Header
        this.createHeader();

        // Tabs
        this.createTabs();

        // Tab content area
        this.contentY = this.panelY + 170;
        this.showTabContent();

        // Action cards
        this.createActionCards();

        // Bottom buttons
        this.createBottomButtons();
    }

    createHeader() {
        const x = this.panelX + 30;
        const y = this.panelY + 25;

        // Severity badge
        const severity = this.incident.severity?.toLowerCase() || 'medium';
        const colors = { critical: COLORS.danger, high: COLORS.warning, medium: COLORS.accent, low: COLORS.success };
        const color = colors[severity] || COLORS.accent;

        const badge = this.add.graphics();
        badge.fillStyle(color, 1);
        badge.fillRoundedRect(x, y, 80, 28, 6);

        this.add.text(x + 40, y + 14, severity.toUpperCase(), {
            fontSize: '12px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: ['low', 'medium'].includes(severity) ? '#000' : '#fff'
        }).setOrigin(0.5);

        // ID and Title
        this.add.text(x + 100, y + 5, this.incident.id, {
            fontSize: '20px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#06b6d4'
        });

        this.add.text(x, y + 45, this.incident.title || 'Incident', {
            fontSize: '22px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#e8e8e8',
            wordWrap: { width: 500 }
        });

        // Impact bar
        const blast = gameState.calculateBlastRadius(this.incident);
        this.add.text(x + 550, y + 10, `Impact: ${blast}/100`, {
            fontSize: '15px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#a0a0a0'
        });

        // Impact bar visual
        const barWidth = 160;
        const barBg = this.add.graphics();
        barBg.fillStyle(0x0a0a12, 1);
        barBg.fillRoundedRect(x + 550, y + 35, barWidth, 14, 5);

        const fillColor = blast >= 70 ? COLORS.danger : (blast >= 40 ? COLORS.warning : COLORS.success);
        const barFill = this.add.graphics();
        barFill.fillStyle(fillColor, 1);
        barFill.fillRoundedRect(x + 550, y + 35, (blast / 100) * barWidth, 14, 5);

        // Resolved badge
        if (this.incident.resolved) {
            this.add.text(x + 750, y + 20, '✓ RESOLVED', {
                fontSize: '18px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                fontStyle: 'bold',
                color: '#10b981'
            });
        }
    }

    createTabs() {
        // Renamed tabs: Briefing, Clues, Vitals, Timeline
        const tabs = [
            { id: 'briefing', label: '📋 Briefing' },
            { id: 'clues', label: '🔍 Clues', locked: !this.incident.investigated },
            { id: 'vitals', label: '📊 Vitals' },
            { id: 'timeline', label: '⏱️ Timeline', locked: !this.incident.investigated }
        ];

        const tabWidth = 130;
        const startX = this.panelX + 30;
        const y = this.panelY + 125;

        tabs.forEach((tab, i) => {
            const x = startX + i * (tabWidth + 10);
            const isActive = this.activeTab === tab.id;
            const isLocked = tab.locked;

            const bg = this.add.graphics();
            bg.fillStyle(isActive ? COLORS.accent : (isLocked ? 0x1a1a2e : 0x2a2a4a), 1);
            bg.fillRoundedRect(x, y, tabWidth, 38, 8);

            const label = isLocked ? '🔒' : tab.label;
            this.add.text(x + tabWidth / 2, y + 19, label, {
                fontSize: '14px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                color: isActive ? '#000' : (isLocked ? '#666' : '#e8e8e8')
            }).setOrigin(0.5);

            if (!isLocked) {
                const hitArea = this.add.rectangle(x + tabWidth / 2, y + 19, tabWidth, 38)
                    .setInteractive({ useHandCursor: true });
                hitArea.on('pointerdown', () => {
                    soundManager.play('click');
                    this.activeTab = tab.id;
                    this.scene.restart({ incidentId: this.incidentId });
                });
            }
        });

        // Inspect button (if not yet investigated)
        if (!this.incident.investigated && !this.incident.resolved) {
            const invX = this.panelX + this.panelWidth - 200;
            const invBg = this.add.graphics();
            invBg.fillStyle(0x8b5cf6, 1);
            invBg.fillRoundedRect(invX, y, 160, 38, 8);

            this.add.text(invX + 80, y + 19, '🔍 Inspect First', {
                fontSize: '14px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                fontStyle: 'bold',
                color: '#fff'
            }).setOrigin(0.5);

            this.add.rectangle(invX + 80, y + 19, 160, 38)
                .setInteractive({ useHandCursor: true })
                .on('pointerover', () => {
                    invBg.clear();
                    invBg.fillStyle(0x9d6eff, 1);
                    invBg.fillRoundedRect(invX, y, 160, 38, 8);
                })
                .on('pointerout', () => {
                    invBg.clear();
                    invBg.fillStyle(0x8b5cf6, 1);
                    invBg.fillRoundedRect(invX, y, 160, 38, 8);
                })
                .on('pointerdown', () => {
                    soundManager.play('click');
                    gameState.investigate(this.incidentId);
                    // Add friendly event message
                    gameState.state.events.unshift({
                        time: Date.now(),
                        text: formatEventMessage('inspect', { id: this.incident.id })
                    });
                    gameState.saveState();
                    this.incident.investigated = true;
                    this.scene.restart({ incidentId: this.incidentId });
                });
        }
    }

    showTabContent() {
        const x = this.panelX + 30;
        const y = this.contentY + 10;
        const maxWidth = 520;

        switch (this.activeTab) {
            case 'briefing':
                const desc = this.incident.description || this.incident.short_summary || 'No briefing available.';
                this.add.text(x, y, desc, {
                    fontSize: '15px',
                    fontFamily: 'system-ui, Segoe UI, sans-serif',
                    color: '#e8e8e8',
                    wordWrap: { width: maxWidth },
                    lineSpacing: 6
                });

                if (this.incident.services?.length) {
                    this.add.text(x, y + 100, 'Affected Systems:', {
                        fontSize: '14px',
                        fontFamily: 'system-ui, Segoe UI, sans-serif',
                        fontStyle: 'bold',
                        color: '#a0a0a0'
                    });
                    this.add.text(x, y + 125, this.incident.services.join(', '), {
                        fontSize: '14px',
                        fontFamily: 'system-ui, Segoe UI, sans-serif',
                        color: '#e8e8e8'
                    });
                }
                break;

            case 'clues':
                const logs = this.incident.logs || [];
                if (logs.length === 0) {
                    this.add.text(x, y, 'No clues available yet.', {
                        fontSize: '15px',
                        fontFamily: 'system-ui, Segoe UI, sans-serif',
                        color: '#a0a0a0'
                    });
                } else {
                    const logText = logs.slice(0, 8).join('\n');
                    this.add.text(x, y, logText, {
                        fontSize: '13px',
                        fontFamily: 'Consolas, monospace',
                        color: '#a0a0a0',
                        wordWrap: { width: maxWidth },
                        lineSpacing: 4
                    });
                }
                break;

            case 'vitals':
                const metrics = this.incident.metrics || {};
                let my = y;
                const entries = Object.entries(metrics).filter(([k, v]) => v != null);

                if (entries.length === 0) {
                    this.add.text(x, y, 'No vitals available.', {
                        fontSize: '15px',
                        fontFamily: 'system-ui, Segoe UI, sans-serif',
                        color: '#a0a0a0'
                    });
                } else {
                    entries.forEach(([key, value]) => {
                        const label = getMetricLabel(key);
                        this.add.text(x, my, `${label}:`, {
                            fontSize: '14px',
                            fontFamily: 'system-ui, Segoe UI, sans-serif',
                            color: '#a0a0a0'
                        });
                        this.add.text(x + 150, my, typeof value === 'number' ? value.toFixed(1) : value, {
                            fontSize: '14px',
                            fontFamily: 'system-ui, Segoe UI, sans-serif',
                            fontStyle: 'bold',
                            color: '#e8e8e8'
                        });
                        my += 32;
                    });
                }
                break;

            case 'timeline':
                const traces = this.incident.traces || [];
                if (traces.length === 0) {
                    this.add.text(x, y, 'No timeline data available.', {
                        fontSize: '15px',
                        fontFamily: 'system-ui, Segoe UI, sans-serif',
                        color: '#a0a0a0'
                    });
                } else {
                    const traceText = traces.slice(0, 8).join('\n');
                    this.add.text(x, y, traceText, {
                        fontSize: '13px',
                        fontFamily: 'Consolas, monospace',
                        color: '#a0a0a0',
                        wordWrap: { width: maxWidth },
                        lineSpacing: 4
                    });
                }
                break;
        }
    }

    createActionCards() {
        if (this.incident.resolved) return;

        const actions = this.incident.available_actions || this.incident.default_actions || ['rollback', 'restart', 'scale'];
        const startX = this.panelX + 600;
        const y = this.contentY;
        const cardWidth = 220;
        const cardHeight = 90;

        this.add.text(startX, y - 25, '⚡ Choose Your Move', {
            fontSize: '18px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#e8e8e8'
        });

        actions.slice(0, 4).forEach((actionId, i) => {
            const cardY = y + 15 + i * (cardHeight + 12);
            const display = getActionDisplay(actionId);

            const card = this.add.graphics();
            card.fillStyle(COLORS.panelLight, 1);
            card.lineStyle(2, COLORS.accent, 0.4);
            card.fillRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
            card.strokeRoundedRect(startX, cardY, cardWidth, cardHeight, 10);

            // Icon
            this.add.text(startX + 15, cardY + 12, display.icon, { fontSize: '24px' });

            // Friendly name
            this.add.text(startX + 50, cardY + 15, display.name, {
                fontSize: '15px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                fontStyle: 'bold',
                color: '#e8e8e8'
            });

            // Description
            this.add.text(startX + 15, cardY + 45, display.desc, {
                fontSize: '12px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                color: '#a0a0a0',
                wordWrap: { width: cardWidth - 30 }
            });

            // Effect hint
            this.add.text(startX + cardWidth - 15, cardY + 15, display.effect, {
                fontSize: '11px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                color: display.effect === 'risky' ? '#ef4444' : '#10b981'
            }).setOrigin(1, 0);

            // Recommended hint if investigated
            if (this.incident.investigated) {
                const correct = gameState.getCorrectAction(this.incident);
                if (actionId === correct) {
                    this.add.text(startX + cardWidth - 15, cardY + cardHeight - 18, '⭐ Best choice', {
                        fontSize: '11px',
                        fontFamily: 'system-ui, Segoe UI, sans-serif',
                        color: '#FFDD00'
                    }).setOrigin(1, 0);
                }
            }

            // Interactive
            const hitArea = this.add.rectangle(startX + cardWidth / 2, cardY + cardHeight / 2, cardWidth, cardHeight)
                .setInteractive({ useHandCursor: true });

            hitArea.on('pointerover', () => {
                card.clear();
                card.fillStyle(0x1f3460, 1);
                card.lineStyle(2, COLORS.accent, 1);
                card.fillRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
                card.strokeRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
            });

            hitArea.on('pointerout', () => {
                card.clear();
                card.fillStyle(COLORS.panelLight, 1);
                card.lineStyle(2, COLORS.accent, 0.4);
                card.fillRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
                card.strokeRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
            });

            hitArea.on('pointerdown', () => this.executeAction(actionId));
        });
    }

    executeAction(actionId) {
        const display = getActionDisplay(actionId);
        const result = gameState.takeAction(this.incidentId, actionId);

        // Clear old event and add friendly one
        if (gameState.state.events.length > 0) {
            gameState.state.events.shift();
        }

        if (result.success) {
            soundManager.play('resolve');
            gameState.state.events.unshift({
                time: Date.now(),
                text: formatEventMessage('action_success', { id: this.incident.id, action: actionId })
            });
            gameState.state.events.unshift({
                time: Date.now(),
                text: formatEventMessage('resolve', { id: this.incident.id })
            });
            this.createResolveParticles();
        } else {
            const msgType = result.delta < -15 ? 'action_worsen' : 'action_fail';
            soundManager.play(result.delta < -15 ? 'error' : 'warning');
            gameState.state.events.unshift({
                time: Date.now(),
                text: formatEventMessage(msgType, { id: this.incident.id, action: actionId })
            });
            if (result.delta < -15) {
                this.cameras.main.shake(200, 0.008);
            }
        }

        gameState.saveState();

        // Show floating score delta
        this.showScoreDelta(result.delta);

        // Close and refresh world
        this.time.delayedCall(800, () => {
            this.closeScene();
        });
    }

    createResolveParticles() {
        const { width, height } = this.cameras.main;
        for (let i = 0; i < 25; i++) {
            const x = width / 2 + Phaser.Math.Between(-150, 150);
            const y = height / 2 + Phaser.Math.Between(-80, 80);
            const colors = [COLORS.success, COLORS.accent, COLORS.accentAlt];
            const particle = this.add.circle(x, y, Phaser.Math.Between(4, 10), Phaser.Math.RND.pick(colors), 0.9);

            this.tweens.add({
                targets: particle,
                x: x + Phaser.Math.Between(-200, 200),
                y: y + Phaser.Math.Between(-200, 200),
                alpha: 0,
                scale: 0,
                duration: 700,
                ease: 'Power2'
            });
        }
    }

    showScoreDelta(delta) {
        if (!delta) return;
        const { width, height } = this.cameras.main;
        const text = (delta > 0 ? '+' : '') + delta;
        const color = delta > 0 ? '#10b981' : '#ef4444';

        const scoreText = this.add.text(width / 2, height / 2 - 120, text, {
            fontSize: '56px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color
        }).setOrigin(0.5);

        this.tweens.add({
            targets: scoreText,
            y: height / 2 - 200,
            alpha: 0,
            duration: 1000,
            ease: 'Power2'
        });
    }

    createBottomButtons() {
        const y = this.panelY + this.panelHeight - 50;

        // Back button
        this.createButton(this.panelX + 140, y, '← Back to War Room', () => this.closeScene());
    }

    createButton(x, y, text, callback) {
        const bg = this.add.graphics();
        bg.fillStyle(COLORS.panelLight, 1);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(x - 100, y - 20, 200, 40, 8);
        bg.strokeRoundedRect(x - 100, y - 20, 200, 40, 8);

        this.add.text(x, y, text, {
            fontSize: '14px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        this.add.rectangle(x, y, 200, 40)
            .setInteractive({ useHandCursor: true })
            .on('pointerdown', () => {
                soundManager.play('click');
                callback();
            });
    }

    closeScene() {
        this.scene.stop();
        this.scene.resume('WorldScene');
        this.scene.get('WorldScene').scene.restart();
    }
}
