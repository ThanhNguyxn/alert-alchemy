/**
 * IncidentScene - Detail overlay for inspecting and acting on incidents
 */
class IncidentScene extends Phaser.Scene {
    constructor() {
        super({ key: 'IncidentScene' });
        this.incident = null;
        this.activeTab = 'info';
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
        this.panelX = 100;
        this.panelY = 60;
        this.panelWidth = width - 200;
        this.panelHeight = height - 120;

        const panel = this.add.graphics();
        panel.fillStyle(COLORS.panel, 1);
        panel.lineStyle(2, COLORS.accent, 1);
        panel.fillRoundedRect(this.panelX, this.panelY, this.panelWidth, this.panelHeight, 16);
        panel.strokeRoundedRect(this.panelX, this.panelY, this.panelWidth, this.panelHeight, 16);

        // Close button
        const closeBtn = this.add.text(this.panelX + this.panelWidth - 40, this.panelY + 20, '✕', {
            fontSize: '28px',
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
        this.contentY = this.panelY + 160;
        this.showTabContent();

        // Action cards
        this.createActionCards();

        // Bottom buttons
        this.createBottomButtons();
    }

    createHeader() {
        const x = this.panelX + 30;
        const y = this.panelY + 30;

        // Severity badge
        const severity = this.incident.severity?.toLowerCase() || 'medium';
        const colors = { critical: COLORS.danger, high: COLORS.warning, medium: COLORS.accent, low: COLORS.success };
        const color = colors[severity] || COLORS.accent;

        const badge = this.add.graphics();
        badge.fillStyle(color, 1);
        badge.fillRoundedRect(x, y, 80, 26, 6);

        this.add.text(x + 40, y + 13, severity.toUpperCase(), {
            fontSize: '12px',
            fontStyle: 'bold',
            color: ['low', 'medium'].includes(severity) ? '#000' : '#fff'
        }).setOrigin(0.5);

        // ID and Title
        this.add.text(x + 100, y + 5, this.incident.id, {
            fontSize: '20px',
            fontStyle: 'bold',
            color: '#06b6d4'
        });

        this.add.text(x, y + 45, this.incident.title || 'Incident', {
            fontSize: '24px',
            fontStyle: 'bold',
            color: '#e8e8e8'
        });

        // Blast radius
        const blast = gameState.calculateBlastRadius(this.incident);
        this.add.text(x + 500, y + 10, `Blast Radius: ${blast}`, {
            fontSize: '16px',
            color: '#a0a0a0'
        });

        // Blast bar
        const barWidth = 150;
        const barBg = this.add.graphics();
        barBg.fillStyle(0x0a0a12, 1);
        barBg.fillRoundedRect(x + 500, y + 35, barWidth, 12, 4);

        const fillColor = blast >= 70 ? COLORS.danger : (blast >= 40 ? COLORS.warning : COLORS.success);
        const barFill = this.add.graphics();
        barFill.fillStyle(fillColor, 1);
        barFill.fillRoundedRect(x + 500, y + 35, (blast / 100) * barWidth, 12, 4);

        // Resolved badge
        if (this.incident.resolved) {
            this.add.text(x + 700, y + 20, '✓ RESOLVED', {
                fontSize: '18px',
                fontStyle: 'bold',
                color: '#10b981'
            });
        }
    }

    createTabs() {
        const tabs = [
            { id: 'info', label: '📋 Info' },
            { id: 'logs', label: '📜 Logs' },
            { id: 'metrics', label: '📊 Metrics' },
            { id: 'traces', label: '🔍 Traces' }
        ];

        const tabWidth = 120;
        const startX = this.panelX + 30;
        const y = this.panelY + 115;

        tabs.forEach((tab, i) => {
            const x = startX + i * (tabWidth + 10);
            const isActive = this.activeTab === tab.id;
            const isLocked = (tab.id === 'logs' || tab.id === 'traces') && !this.incident.investigated;

            const bg = this.add.graphics();
            bg.fillStyle(isActive ? COLORS.accent : (isLocked ? 0x1a1a2e : 0x2a2a4a), 1);
            bg.fillRoundedRect(x, y, tabWidth, 35, 8);

            const label = isLocked ? '🔒 ' + tab.label.split(' ')[1] : tab.label;
            this.add.text(x + tabWidth / 2, y + 17, label, {
                fontSize: '14px',
                color: isActive ? '#000' : (isLocked ? '#666' : '#e8e8e8')
            }).setOrigin(0.5);

            if (!isLocked) {
                const hitArea = this.add.rectangle(x + tabWidth / 2, y + 17, tabWidth, 35)
                    .setInteractive({ useHandCursor: true });
                hitArea.on('pointerdown', () => {
                    soundManager.play('click');
                    this.activeTab = tab.id;
                    this.scene.restart({ incidentId: this.incidentId });
                });
            }
        });

        // Investigate button (if not yet investigated)
        if (!this.incident.investigated && !this.incident.resolved) {
            const invX = this.panelX + this.panelWidth - 180;
            const invBg = this.add.graphics();
            invBg.fillStyle(0x8b5cf6, 1);
            invBg.fillRoundedRect(invX, y, 140, 35, 8);

            this.add.text(invX + 70, y + 17, '🔍 Investigate', {
                fontSize: '14px',
                fontStyle: 'bold',
                color: '#fff'
            }).setOrigin(0.5);

            this.add.rectangle(invX + 70, y + 17, 140, 35)
                .setInteractive({ useHandCursor: true })
                .on('pointerdown', () => {
                    soundManager.play('click');
                    gameState.investigate(this.incidentId);
                    this.incident.investigated = true;
                    this.scene.restart({ incidentId: this.incidentId });
                });
        }
    }

    showTabContent() {
        const x = this.panelX + 30;
        const y = this.contentY;
        const maxWidth = 500;

        switch (this.activeTab) {
            case 'info':
                const desc = this.incident.description || this.incident.short_summary || 'No description available.';
                this.add.text(x, y, desc, {
                    fontSize: '15px',
                    color: '#e8e8e8',
                    wordWrap: { width: maxWidth }
                });

                if (this.incident.services?.length) {
                    this.add.text(x, y + 80, 'Affected Services:', {
                        fontSize: '14px',
                        fontStyle: 'bold',
                        color: '#a0a0a0'
                    });
                    this.add.text(x, y + 105, this.incident.services.join(', '), {
                        fontSize: '14px',
                        color: '#e8e8e8'
                    });
                }
                break;

            case 'logs':
                const logs = this.incident.logs || [];
                const logText = logs.slice(0, 8).join('\n') || 'No logs available.';
                this.add.text(x, y, logText, {
                    fontSize: '13px',
                    fontFamily: 'Consolas, monospace',
                    color: '#a0a0a0',
                    wordWrap: { width: maxWidth }
                });
                break;

            case 'metrics':
                const metrics = this.incident.metrics || {};
                let my = y;
                Object.entries(metrics).forEach(([key, value]) => {
                    if (value != null) {
                        this.add.text(x, my, `${key.replace(/_/g, ' ')}: ${typeof value === 'number' ? value.toFixed(1) : value}`, {
                            fontSize: '15px',
                            color: '#e8e8e8'
                        });
                        my += 30;
                    }
                });
                if (Object.keys(metrics).length === 0) {
                    this.add.text(x, y, 'No metrics available.', { fontSize: '15px', color: '#a0a0a0' });
                }
                break;

            case 'traces':
                const traces = this.incident.traces || [];
                const traceText = traces.slice(0, 8).join('\n') || 'No traces available.';
                this.add.text(x, y, traceText, {
                    fontSize: '13px',
                    fontFamily: 'Consolas, monospace',
                    color: '#a0a0a0',
                    wordWrap: { width: maxWidth }
                });
                break;
        }
    }

    createActionCards() {
        if (this.incident.resolved) return;

        const actions = this.incident.available_actions || this.incident.default_actions || ['rollback', 'restart', 'scale'];
        const startX = this.panelX + 580;
        const y = this.contentY;
        const cardWidth = 180;
        const cardHeight = 100;

        this.add.text(startX, y - 30, '⚡ Take Action', {
            fontSize: '18px',
            fontStyle: 'bold',
            color: '#e8e8e8'
        });

        actions.slice(0, 4).forEach((action, i) => {
            const cardY = y + 20 + i * (cardHeight + 15);

            const card = this.add.graphics();
            card.fillStyle(COLORS.panelLight, 1);
            card.lineStyle(2, COLORS.accent, 0.5);
            card.fillRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
            card.strokeRoundedRect(startX, cardY, cardWidth, cardHeight, 10);

            // Icon based on action type
            const icons = {
                rollback: '↩️',
                restart: '🔄',
                scale: '📈',
                'increase-pool': '🔗',
                'disable-flag': '🚫',
                'clear-cache': '🗑️',
                'add-index': '📇'
            };
            const icon = icons[action] || '⚡';

            this.add.text(startX + 15, cardY + 15, icon, { fontSize: '24px' });
            this.add.text(startX + 50, cardY + 18, action, {
                fontSize: '16px',
                fontStyle: 'bold',
                color: '#e8e8e8'
            });

            // Hint if investigated
            if (this.incident.investigated) {
                const correct = gameState.getCorrectAction(this.incident);
                if (action === correct) {
                    this.add.text(startX + cardWidth - 35, cardY + 15, '⭐', { fontSize: '20px' });
                }
            }

            // Action note if available
            const actions_data = this.incident.actions || [];
            const actionData = actions_data.find(a => a.name === action);
            if (actionData?.note) {
                this.add.text(startX + 15, cardY + 55, actionData.note.substring(0, 25), {
                    fontSize: '11px',
                    color: '#a0a0a0'
                });
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
                card.lineStyle(2, COLORS.accent, 0.5);
                card.fillRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
                card.strokeRoundedRect(startX, cardY, cardWidth, cardHeight, 10);
            });

            hitArea.on('pointerdown', () => this.executeAction(action));
        });
    }

    executeAction(actionName) {
        const result = gameState.takeAction(this.incidentId, actionName);

        if (result.success) {
            soundManager.play('resolve');
            // Particle burst effect
            this.createResolveParticles();
        } else {
            soundManager.play(result.delta < -15 ? 'error' : 'warning');
            // Camera shake for worsening
            if (result.delta < -15) {
                this.cameras.main.shake(200, 0.01);
            }
        }

        // Show floating score delta
        this.showScoreDelta(result.delta);

        // Close and refresh world
        this.time.delayedCall(800, () => {
            this.closeScene();
        });
    }

    createResolveParticles() {
        const { width, height } = this.cameras.main;
        for (let i = 0; i < 20; i++) {
            const x = width / 2 + Phaser.Math.Between(-100, 100);
            const y = height / 2 + Phaser.Math.Between(-50, 50);
            const particle = this.add.circle(x, y, Phaser.Math.Between(3, 8), COLORS.success, 0.8);

            this.tweens.add({
                targets: particle,
                x: x + Phaser.Math.Between(-150, 150),
                y: y + Phaser.Math.Between(-150, 150),
                alpha: 0,
                scale: 0,
                duration: 600,
                ease: 'Power2'
            });
        }
    }

    showScoreDelta(delta) {
        if (!delta) return;
        const { width, height } = this.cameras.main;
        const text = (delta > 0 ? '+' : '') + delta;
        const color = delta > 0 ? '#10b981' : '#ef4444';

        const scoreText = this.add.text(width / 2, height / 2 - 100, text, {
            fontSize: '48px',
            fontStyle: 'bold',
            color
        }).setOrigin(0.5);

        this.tweens.add({
            targets: scoreText,
            y: height / 2 - 180,
            alpha: 0,
            duration: 1000,
            ease: 'Power2'
        });
    }

    createBottomButtons() {
        const y = this.panelY + this.panelHeight - 50;

        // Back button
        this.createButton(this.panelX + 120, y, '← Back to Map', () => this.closeScene());
    }

    createButton(x, y, text, callback) {
        const bg = this.add.graphics();
        bg.fillStyle(COLORS.panelLight, 1);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(x - 80, y - 18, 160, 36, 8);
        bg.strokeRoundedRect(x - 80, y - 18, 160, 36, 8);

        this.add.text(x, y, text, {
            fontSize: '14px',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        this.add.rectangle(x, y, 160, 36)
            .setInteractive({ useHandCursor: true })
            .on('pointerdown', () => {
                soundManager.play('click');
                callback();
            });
    }

    closeScene() {
        this.scene.stop();
        this.scene.resume('WorldScene');
        // Refresh WorldScene
        this.scene.get('WorldScene').scene.restart();
    }
}
