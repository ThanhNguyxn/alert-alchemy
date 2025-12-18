/**
 * MenuScene - Main menu with Play/Continue/Reset buttons
 */
class MenuScene extends Phaser.Scene {
    constructor() {
        super({ key: 'MenuScene' });
    }

    create() {
        const { width, height } = this.cameras.main;

        // Background grid effect
        this.drawGrid();

        // Title
        this.add.text(width / 2, 120, '🧪 Alert Alchemy', {
            fontSize: '64px',
            fontFamily: 'Segoe UI, system-ui, sans-serif',
            color: '#06b6d4',
            fontStyle: 'bold'
        }).setOrigin(0.5);

        // Subtitle
        this.add.text(width / 2, 190, 'Incident Response Simulator', {
            fontSize: '24px',
            color: '#a0a0a0'
        }).setOrigin(0.5);

        // Menu buttons
        const buttonY = 320;
        const buttonSpacing = 70;

        // Play button
        this.createButton(width / 2, buttonY, '▶  PLAY', async () => {
            soundManager.init();
            soundManager.play('click');
            await gameState.loadIncidents();
            gameState.startNewGame();
            this.scene.start('WorldScene');
        });

        // Continue button (if saved state exists)
        if (gameState.hasSavedState()) {
            this.createButton(width / 2, buttonY + buttonSpacing, '↺  CONTINUE', async () => {
                soundManager.init();
                soundManager.play('click');
                await gameState.loadIncidents();
                gameState.loadState();
                this.scene.start('WorldScene');
            }, true);
        }

        // Reset button
        this.createButton(width / 2, buttonY + buttonSpacing * (gameState.hasSavedState() ? 2 : 1), '🔄  RESET', () => {
            soundManager.play('click');
            gameState.resetGame();
            this.scene.restart();
        }, true);

        // Sound toggle
        this.soundIcon = this.add.text(width - 60, 40, '🔊', {
            fontSize: '32px'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true });

        this.soundIcon.on('pointerdown', () => {
            const enabled = soundManager.toggle();
            this.soundIcon.setText(enabled ? '🔊' : '🔇');
            soundManager.play('click');
        });

        // How to Play button
        this.add.text(width / 2, height - 100, '❓ How to Play', {
            fontSize: '20px',
            color: '#a0a0a0'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true })
            .on('pointerover', function () { this.setColor('#e8e8e8'); })
            .on('pointerout', function () { this.setColor('#a0a0a0'); })
            .on('pointerdown', () => this.showHowToPlay());

        // Buy Me a Coffee
        this.add.text(width / 2, height - 50, '☕ buymeacoffee.com/thanhnguyxn', {
            fontSize: '16px',
            color: '#FFDD00'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true })
            .on('pointerdown', () => {
                window.open('https://buymeacoffee.com/thanhnguyxn', '_blank');
            });

        // Floating particles
        this.createParticles();
    }

    drawGrid() {
        const graphics = this.add.graphics();
        graphics.lineStyle(1, COLORS.grid, 0.3);

        for (let x = 0; x < GAME_WIDTH; x += 50) {
            graphics.moveTo(x, 0);
            graphics.lineTo(x, GAME_HEIGHT);
        }
        for (let y = 0; y < GAME_HEIGHT; y += 50) {
            graphics.moveTo(0, y);
            graphics.lineTo(GAME_WIDTH, y);
        }
        graphics.strokePath();
    }

    createButton(x, y, text, callback, secondary = false) {
        const bg = this.add.graphics();
        const width = 280;
        const height = 55;

        const drawButton = (hover = false) => {
            bg.clear();
            if (secondary) {
                bg.fillStyle(hover ? 0x2a2a4a : 0x1a1a2e, 1);
                bg.lineStyle(2, 0x3a3a5a, 1);
            } else {
                bg.fillGradientStyle(0x06b6d4, 0x06b6d4, 0x8b5cf6, 0x8b5cf6, 1);
            }
            bg.fillRoundedRect(x - width / 2, y - height / 2, width, height, 12);
            if (secondary) bg.strokeRoundedRect(x - width / 2, y - height / 2, width, height, 12);
        };

        drawButton();

        const label = this.add.text(x, y, text, {
            fontSize: '22px',
            fontFamily: 'Segoe UI, system-ui, sans-serif',
            color: '#ffffff',
            fontStyle: 'bold'
        }).setOrigin(0.5);

        const hitArea = this.add.rectangle(x, y, width, height).setInteractive({ useHandCursor: true });

        hitArea.on('pointerover', () => drawButton(true));
        hitArea.on('pointerout', () => drawButton(false));
        hitArea.on('pointerdown', callback);
    }

    createParticles() {
        // Simple floating dots
        for (let i = 0; i < 20; i++) {
            const x = Phaser.Math.Between(0, GAME_WIDTH);
            const y = Phaser.Math.Between(0, GAME_HEIGHT);
            const dot = this.add.circle(x, y, Phaser.Math.Between(1, 3), COLORS.accent, 0.3);

            this.tweens.add({
                targets: dot,
                y: y - 100,
                alpha: 0,
                duration: Phaser.Math.Between(3000, 6000),
                repeat: -1,
                yoyo: false,
                onRepeat: () => {
                    dot.x = Phaser.Math.Between(0, GAME_WIDTH);
                    dot.y = GAME_HEIGHT + 20;
                    dot.alpha = 0.3;
                }
            });
        }
    }

    showHowToPlay() {
        const modal = new Modal(this, 'How to Play', [
            '1️⃣ Click incidents to investigate',
            '2️⃣ Choose actions wisely',
            '3️⃣ Resolve before time runs out!',
            '',
            '💡 Investigating unlocks more info',
            '⚡ Quick resolves = bonus points'
        ]);
        modal.show();
    }
}
