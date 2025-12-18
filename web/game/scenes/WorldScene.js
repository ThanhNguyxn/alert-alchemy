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

        // Show tutorial on first visit
        if (!localStorage.getItem(TUTORIAL_KEY)) {
            this.showTutorial();
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
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#e8e8e8',
            fontStyle: 'bold'
        });

        // Subtitle
        this.add.text(20, 55, 'Choose an incident to handle', {
            fontSize: '16px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#a0a0a0'
        });
    }

    createIncidentNodes() {
        const incidents = gameState.state?.incidents || [];
        const startX = 150;
        const startY = 180;
        const spacingX = 280;
        const spacingY = 200;

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
        const glow = this.add.circle(0, 0, 80, color, 0.15);
        container.add(glow);

        // Card background - taller for title wrapping
        const cardWidth = 220;
        const cardHeight = 140;
        const bg = this.add.graphics();
        bg.fillStyle(incident.resolved ? 0x1a3a2a : COLORS.panelLight, 1);
        bg.lineStyle(3, incident.resolved ? COLORS.success : color, 1);
        bg.fillRoundedRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 12);
        bg.strokeRoundedRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 12);
        container.add(bg);

        // Severity badge
        const badge = this.add.graphics();
        badge.fillStyle(color, 1);
        badge.fillRoundedRect(-cardWidth / 2 + 10, -cardHeight / 2 + 10, 70, 24, 6);
        container.add(badge);

        this.add.text(x - cardWidth / 2 + 45, y - cardHeight / 2 + 22, severity.toUpperCase(), {
            fontSize: '11px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: severity === 'low' || severity === 'medium' ? '#000' : '#fff'
        }).setOrigin(0.5);

        // Resolved check
        if (incident.resolved) {
            this.add.text(x + cardWidth / 2 - 25, y - cardHeight / 2 + 22, '✓', {
                fontSize: '24px',
                color: '#10b981'
            }).setOrigin(0.5);
        }

        // ID
        this.add.text(x, y - 30, incident.id, {
            fontSize: '16px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);

        // Title - wrapped to 2 lines
        const title = incident.title || 'Incident';
        this.add.text(x, y + 5, title, {
            fontSize: '14px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#e8e8e8',
            wordWrap: { width: cardWidth - 30 },
            align: 'center'
        }).setOrigin(0.5);

        // Impact bar with label
        const barWidth = cardWidth - 40;
        const barY = cardHeight / 2 - 30;

        this.add.text(x - barWidth / 2, y + barY - 5, 'Impact:', {
            fontSize: '11px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#a0a0a0'
        });

        const barBg = this.add.graphics();
        barBg.fillStyle(0x0a0a12, 1);
        barBg.fillRoundedRect(x - barWidth / 2 + 50, y + barY - 3, barWidth - 80, 10, 4);

        const barFill = this.add.graphics();
        const fillColor = blast >= 70 ? COLORS.danger : (blast >= 40 ? COLORS.warning : COLORS.success);
        barFill.fillStyle(fillColor, 1);
        barFill.fillRoundedRect(x - barWidth / 2 + 50, y + barY - 3, (blast / 100) * (barWidth - 80), 10, 4);

        this.add.text(x + barWidth / 2 - 5, y + barY + 2, `${blast}/100`, {
            fontSize: '11px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#a0a0a0'
        }).setOrigin(1, 0.5);

        // "Open" hint on hover
        const openHint = this.add.text(x, y + cardHeight / 2 + 15, '👆 Click to open', {
            fontSize: '12px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#666'
        }).setOrigin(0.5).setAlpha(0);

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
        const hitArea = this.add.rectangle(x, y, cardWidth, cardHeight).setInteractive({ useHandCursor: true });

        hitArea.on('pointerover', () => {
            container.setScale(1.05);
            openHint.setAlpha(1);
            bg.clear();
            bg.fillStyle(incident.resolved ? 0x1a3a2a : 0x1f3460, 1);
            bg.lineStyle(3, incident.resolved ? COLORS.success : color, 1);
            bg.fillRoundedRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 12);
            bg.strokeRoundedRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 12);
        });

        hitArea.on('pointerout', () => {
            container.setScale(1);
            openHint.setAlpha(0);
            bg.clear();
            bg.fillStyle(incident.resolved ? 0x1a3a2a : COLORS.panelLight, 1);
            bg.lineStyle(3, incident.resolved ? COLORS.success : color, 1);
            bg.fillRoundedRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 12);
            bg.strokeRoundedRect(-cardWidth / 2, -cardHeight / 2, cardWidth, cardHeight, 12);
        });

        hitArea.on('pointerdown', () => {
            soundManager.play('click');
            this.scene.launch('IncidentScene', { incidentId: incident.id });
            this.scene.pause();
        });

        this.incidentNodes.push({ container, incident });
    }

    createEventFeed() {
        const x = GAME_WIDTH - 280;
        const y = 80;
        const width = 260;
        const height = 420;

        // Panel background
        const bg = this.add.graphics();
        bg.fillStyle(COLORS.panel, 0.95);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(x, y, width, height, 10);
        bg.strokeRoundedRect(x, y, width, height, 10);

        this.add.text(x + 15, y + 15, '📡 Activity Feed', {
            fontSize: '16px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#e8e8e8'
        });

        // Events
        const events = gameState.state?.events || [];

        if (events.length === 0) {
            // Placeholder
            this.add.text(x + 15, y + 55, 'No activity yet.\n\nPick an incident and\nmake your first move!', {
                fontSize: '14px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                color: '#666',
                lineSpacing: 8
            });
        } else {
            events.slice(0, 10).forEach((event, i) => {
                const text = event.text.length > 32 ? event.text.substring(0, 32) + '...' : event.text;
                this.add.text(x + 15, y + 55 + i * 35, text, {
                    fontSize: '13px',
                    fontFamily: 'system-ui, Segoe UI, sans-serif',
                    color: i === 0 ? '#e8e8e8' : '#a0a0a0',
                    wordWrap: { width: width - 30 }
                });
            });
        }
    }

    createActionButtons() {
        const y = GAME_HEIGHT - 50;

        // Pass Time button (was Tick)
        this.createSmallButton(GAME_WIDTH - 380, y, '⏰ Pass Time', () => {
            gameState.state.events.unshift({
                time: Date.now(),
                text: formatEventMessage('tick', { step: gameState.state.currentStep + 1 })
            });
            gameState.tick();
            soundManager.play('click');
            this.scene.restart();
        });

        // Finish Shift button (was End Game)
        this.createSmallButton(GAME_WIDTH - 220, y, '🏁 Finish Shift', () => {
            soundManager.play('click');
            gameState.endGame();
            this.showGameEnd();
        });

        // Home button (was Menu)
        this.createSmallButton(80, y, '🏠 Home', () => {
            soundManager.play('click');
            this.scene.start('MenuScene');
        });

        // Tutorial button
        this.createSmallButton(200, y, '❓ Help', () => {
            soundManager.play('click');
            this.showTutorial();
        });
    }

    createSmallButton(x, y, text, callback) {
        const bg = this.add.graphics();
        bg.fillStyle(COLORS.panel, 1);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(x - 65, y - 20, 130, 40, 8);
        bg.strokeRoundedRect(x - 65, y - 20, 130, 40, 8);

        const label = this.add.text(x, y, text, {
            fontSize: '14px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        const hitArea = this.add.rectangle(x, y, 130, 40).setInteractive({ useHandCursor: true });

        hitArea.on('pointerover', () => {
            bg.clear();
            bg.fillStyle(0x2a2a4a, 1);
            bg.lineStyle(1, COLORS.accent, 1);
            bg.fillRoundedRect(x - 65, y - 20, 130, 40, 8);
            bg.strokeRoundedRect(x - 65, y - 20, 130, 40, 8);
        });

        hitArea.on('pointerout', () => {
            bg.clear();
            bg.fillStyle(COLORS.panel, 1);
            bg.lineStyle(1, 0x3a3a5a, 1);
            bg.fillRoundedRect(x - 65, y - 20, 130, 40, 8);
            bg.strokeRoundedRect(x - 65, y - 20, 130, 40, 8);
        });

        hitArea.on('pointerdown', callback);
    }

    showTutorial() {
        const { width, height } = this.cameras.main;

        // Overlay
        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.9);
        overlay.fillRect(0, 0, width, height);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, width, height), Phaser.Geom.Rectangle.Contains);

        // Panel
        const panelWidth = 500;
        const panelHeight = 380;
        const px = (width - panelWidth) / 2;
        const py = (height - panelHeight) / 2;

        const panel = this.add.graphics();
        panel.fillStyle(COLORS.panel, 1);
        panel.lineStyle(2, COLORS.accent, 1);
        panel.fillRoundedRect(px, py, panelWidth, panelHeight, 16);
        panel.strokeRoundedRect(px, py, panelWidth, panelHeight, 16);

        this.add.text(width / 2, py + 40, '🎮 Quick Tutorial', {
            fontSize: '28px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);

        const steps = [
            '1️⃣  Click an incident card to open it',
            '2️⃣  Press "Inspect" to unlock more clues',
            '3️⃣  Choose your move wisely',
            '4️⃣  Watch the Activity Feed for results',
            '',
            '💡 Inspecting first improves your chances!',
            '⏰ Each action or "Pass Time" advances the clock'
        ];

        steps.forEach((step, i) => {
            this.add.text(px + 40, py + 90 + i * 32, step, {
                fontSize: '16px',
                fontFamily: 'system-ui, Segoe UI, sans-serif',
                color: '#e8e8e8'
            });
        });

        // Got it button
        const btnY = py + panelHeight - 60;
        const btn = this.add.graphics();
        btn.fillGradientStyle(0x06b6d4, 0x06b6d4, 0x8b5cf6, 0x8b5cf6, 1);
        btn.fillRoundedRect(width / 2 - 80, btnY, 160, 45, 10);

        this.add.text(width / 2, btnY + 22, "Got it!", {
            fontSize: '18px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#fff'
        }).setOrigin(0.5);

        this.add.rectangle(width / 2, btnY + 22, 160, 45)
            .setInteractive({ useHandCursor: true })
            .on('pointerdown', () => {
                localStorage.setItem(TUTORIAL_KEY, 'true');
                overlay.destroy();
                panel.destroy();
                this.scene.restart();
            });
    }

    showGameEnd() {
        const { width, height } = this.cameras.main;

        // Overlay
        const overlay = this.add.graphics();
        overlay.fillStyle(0x000000, 0.85);
        overlay.fillRect(0, 0, width, height);

        // Confetti particles
        for (let i = 0; i < 30; i++) {
            const px = Phaser.Math.Between(100, width - 100);
            const colors = [COLORS.accent, COLORS.success, COLORS.warning, COLORS.accentAlt];
            const particle = this.add.circle(px, -20, Phaser.Math.Between(4, 10), Phaser.Math.RND.pick(colors), 0.8);

            this.tweens.add({
                targets: particle,
                y: height + 50,
                x: px + Phaser.Math.Between(-100, 100),
                rotation: Phaser.Math.Between(0, 6),
                duration: Phaser.Math.Between(2000, 4000),
                ease: 'Linear'
            });
        }

        // Score
        const score = gameState.state?.score || 0;
        const resolved = gameState.state?.incidents.filter(i => i.resolved).length || 0;
        const total = gameState.state?.incidents.length || 0;

        this.add.text(width / 2, 180, '🏁 Shift Complete!', {
            fontSize: '48px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        this.add.text(width / 2, 280, score.toString(), {
            fontSize: '96px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);

        this.add.text(width / 2, 350, 'Final Score', {
            fontSize: '20px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#a0a0a0'
        }).setOrigin(0.5);

        this.add.text(width / 2, 400, `Incidents Resolved: ${resolved}/${total}`, {
            fontSize: '22px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#e8e8e8'
        }).setOrigin(0.5);

        // Play Again
        const playAgain = this.add.text(width / 2, 480, '▶ Start New Shift', {
            fontSize: '24px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true });

        playAgain.on('pointerover', () => playAgain.setScale(1.05));
        playAgain.on('pointerout', () => playAgain.setScale(1));
        playAgain.on('pointerdown', () => {
            gameState.resetGame();
            this.scene.start('MenuScene');
        });

        // Buy Me a Coffee
        this.add.text(width / 2, 550, '☕ Enjoyed it? buymeacoffee.com/thanhnguyxn', {
            fontSize: '16px',
            fontFamily: 'system-ui, Segoe UI, sans-serif',
            color: '#FFDD00'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true })
            .on('pointerdown', () => window.open('https://buymeacoffee.com/thanhnguyxn', '_blank'));
    }
}
