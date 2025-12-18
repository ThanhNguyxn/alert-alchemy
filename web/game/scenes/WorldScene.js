/**
 * WorldScene - Main game view with incident nodes and HUD
 */
class WorldScene extends Phaser.Scene {
    constructor() {
        super({ key: 'WorldScene' });
        this.incidentNodes = [];
        this.hud = null;
    }

    create() {
        const { width, height } = this.cameras.main;

        // Background
        this.drawBackground();

        // Create HUD
        this.hud = new HUD(this);

        // Create incident nodes
        this.createIncidentNodes();

        // Event feed panel
        this.createEventFeed();

        // Bottom action buttons
        this.createActionButtons();

        // Check for game end
        if (gameState.state?.ended) {
            this.showGameEnd();
        }
    }

    drawBackground() {
        const graphics = this.add.graphics();

        // Grid
        graphics.lineStyle(1, COLORS.grid, 0.2);
        for (let x = 0; x < GAME_WIDTH; x += 40) {
            graphics.moveTo(x, 0);
            graphics.lineTo(x, GAME_HEIGHT);
        }
        for (let y = 0; y < GAME_HEIGHT; y += 40) {
            graphics.moveTo(0, y);
            graphics.lineTo(GAME_WIDTH, y);
        }
        graphics.strokePath();

        // Title
        this.add.text(20, 20, '🗺️ War Room', {
            fontSize: '28px',
            fontFamily: 'Segoe UI, system-ui, sans-serif',
            color: '#e8e8e8',
            fontStyle: 'bold'
        });
    }

    createIncidentNodes() {
        const incidents = gameState.state?.incidents || [];
        const startX = 150;
        const startY = 200;
        const spacingX = 280;
        const spacingY = 180;

        incidents.forEach((incident, index) => {
            const col = index % 3;
            const row = Math.floor(index / 3);
            const x = startX + col * spacingX;
            const y = startY + row * spacingY;

            this.createIncidentNode(x, y, incident);
        });
    }

    createIncidentNode(x, y, incident) {
        const blast = gameState.calculateBlastRadius(incident);
        const severity = incident.severity?.toLowerCase() || 'medium';
        const colors = {
            critical: COLORS.danger,
            high: COLORS.warning,
            medium: COLORS.accent,
            low: COLORS.success
        };
        const color = colors[severity] || COLORS.accent;

        // Container for the node
        const container = this.add.container(x, y);

        // Glow effect (pulsing based on blast radius)
        const glow = this.add.circle(0, 0, 70, color, 0.15);
        container.add(glow);

        // Card background
        const bg = this.add.graphics();
        bg.fillStyle(incident.resolved ? 0x1a3a2a : COLORS.panelLight, 1);
        bg.lineStyle(3, incident.resolved ? COLORS.success : color, 1);
        bg.fillRoundedRect(-100, -60, 200, 120, 12);
        bg.strokeRoundedRect(-100, -60, 200, 120, 12);
        container.add(bg);

        // Severity badge
        const badge = this.add.graphics();
        badge.fillStyle(color, 1);
        badge.fillRoundedRect(-90, -52, 60, 22, 6);
        container.add(badge);

        this.add.text(x - 60, y - 41, severity.toUpperCase(), {
            fontSize: '11px',
            fontFamily: 'Segoe UI, system-ui, sans-serif',
            fontStyle: 'bold',
            color: severity === 'low' || severity === 'medium' ? '#000' : '#fff'
        }).setOrigin(0.5);

        // Resolved check
        if (incident.resolved) {
            this.add.text(x + 70, y - 40, '✓', {
                fontSize: '24px',
                color: '#10b981'
            }).setOrigin(0.5);
        }

        // ID
        this.add.text(x, y - 25, incident.id, {
            fontSize: '16px',
            fontFamily: 'Segoe UI, system-ui, sans-serif',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);

        // Title (truncated)
        const title = incident.title?.substring(0, 22) + (incident.title?.length > 22 ? '...' : '') || 'Incident';
        this.add.text(x, y + 5, title, {
            fontSize: '14px',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        // Blast radius bar
        const barWidth = 160;
        const barHeight = 8;
        const barBg = this.add.graphics();
        barBg.fillStyle(0x0a0a12, 1);
        barBg.fillRoundedRect(x - barWidth / 2, y + 30, barWidth, barHeight, 4);

        const barFill = this.add.graphics();
        const fillColor = blast >= 70 ? COLORS.danger : (blast >= 40 ? COLORS.warning : COLORS.success);
        barFill.fillStyle(fillColor, 1);
        barFill.fillRoundedRect(x - barWidth / 2, y + 30, (blast / 100) * barWidth, barHeight, 4);

        this.add.text(x + barWidth / 2 + 15, y + 34, blast, {
            fontSize: '12px',
            color: '#a0a0a0'
        }).setOrigin(0.5);

        // Pulse animation for unresolved
        if (!incident.resolved) {
            this.tweens.add({
                targets: glow,
                scale: { from: 0.9, to: 1.2 },
                alpha: { from: 0.2, to: 0.05 },
                duration: 1000 + blast * 20,
                repeat: -1,
                yoyo: true
            });
        }

        // Make interactive
        const hitArea = this.add.rectangle(x, y, 200, 120).setInteractive({ useHandCursor: true });

        hitArea.on('pointerover', () => {
            container.setScale(1.05);
            bg.clear();
            bg.fillStyle(incident.resolved ? 0x1a3a2a : 0x1f3460, 1);
            bg.lineStyle(3, incident.resolved ? COLORS.success : color, 1);
            bg.fillRoundedRect(-100, -60, 200, 120, 12);
            bg.strokeRoundedRect(-100, -60, 200, 120, 12);
        });

        hitArea.on('pointerout', () => {
            container.setScale(1);
            bg.clear();
            bg.fillStyle(incident.resolved ? 0x1a3a2a : COLORS.panelLight, 1);
            bg.lineStyle(3, incident.resolved ? COLORS.success : color, 1);
            bg.fillRoundedRect(-100, -60, 200, 120, 12);
            bg.strokeRoundedRect(-100, -60, 200, 120, 12);
        });

        hitArea.on('pointerdown', () => {
            soundManager.play('click');
            this.scene.launch('IncidentScene', { incidentId: incident.id });
            this.scene.pause();
        });

        this.incidentNodes.push({ container, incident });
    }

    createEventFeed() {
        const x = GAME_WIDTH - 250;
        const y = 80;
        const width = 230;
        const height = 400;

        // Panel background
        const bg = this.add.graphics();
        bg.fillStyle(COLORS.panel, 0.9);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(x, y, width, height, 8);
        bg.strokeRoundedRect(x, y, width, height, 8);

        this.add.text(x + 15, y + 15, '📡 Event Feed', {
            fontSize: '16px',
            fontStyle: 'bold',
            color: '#e8e8e8'
        });

        // Events
        const events = gameState.state?.events || [];
        events.slice(0, 12).forEach((event, i) => {
            const text = event.text.length > 28 ? event.text.substring(0, 28) + '...' : event.text;
            this.add.text(x + 15, y + 50 + i * 28, text, {
                fontSize: '13px',
                color: i === 0 ? '#e8e8e8' : '#a0a0a0'
            });
        });
    }

    createActionButtons() {
        const y = GAME_HEIGHT - 50;

        // Tick button
        this.createSmallButton(GAME_WIDTH - 350, y, '⏰ Tick (+1)', () => {
            gameState.tick();
            soundManager.play('click');
            this.scene.restart();
        });

        // End Game button
        this.createSmallButton(GAME_WIDTH - 200, y, '🏁 End Game', () => {
            soundManager.play('click');
            gameState.endGame();
            this.showGameEnd();
        });

        // Menu button
        this.createSmallButton(100, y, '🏠 Menu', () => {
            soundManager.play('click');
            this.scene.start('MenuScene');
        });
    }

    createSmallButton(x, y, text, callback) {
        const bg = this.add.graphics();
        bg.fillStyle(COLORS.panel, 1);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(x - 60, y - 18, 120, 36, 8);
        bg.strokeRoundedRect(x - 60, y - 18, 120, 36, 8);

        this.add.text(x, y, text, {
            fontSize: '14px',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        const hitArea = this.add.rectangle(x, y, 120, 36).setInteractive({ useHandCursor: true });
        hitArea.on('pointerdown', callback);
    }

    showGameEnd() {
        const { width, height } = this.cameras.main;

        // Overlay
        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.85);
        overlay.fillRect(0, 0, width, height);

        // Score
        const score = gameState.state?.score || 0;
        const resolved = gameState.state?.incidents.filter(i => i.resolved).length || 0;
        const total = gameState.state?.incidents.length || 0;

        this.add.text(width / 2, 200, '🏁 Game Over!', {
            fontSize: '48px',
            fontStyle: 'bold',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        this.add.text(width / 2, 300, score.toString(), {
            fontSize: '96px',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);

        this.add.text(width / 2, 380, `Incidents Resolved: ${resolved}/${total}`, {
            fontSize: '24px',
            color: '#a0a0a0'
        }).setOrigin(0.5);

        // Play Again
        const playAgain = this.add.text(width / 2, 480, '▶ Play Again', {
            fontSize: '28px',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true });

        playAgain.on('pointerdown', () => {
            gameState.resetGame();
            this.scene.start('MenuScene');
        });

        // Buy Me a Coffee
        this.add.text(width / 2, 550, '☕ Enjoyed it? buymeacoffee.com/thanhnguyxn', {
            fontSize: '18px',
            color: '#FFDD00'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true })
            .on('pointerdown', () => window.open('https://buymeacoffee.com/thanhnguyxn', '_blank'));
    }
}
