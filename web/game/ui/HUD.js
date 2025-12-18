/**
 * HUD - Heads-up display for game stats
 */
class HUD {
    constructor(scene) {
        this.scene = scene;
        this.x = 200;
        this.y = 20;

        this.create();
    }

    create() {
        const state = gameState.state;
        if (!state) return;

        // Panel background
        const bg = this.scene.add.graphics();
        bg.fillStyle(COLORS.panel, 0.9);
        bg.lineStyle(1, 0x3a3a5a, 1);
        bg.fillRoundedRect(this.x, this.y, 400, 50, 8);
        bg.strokeRoundedRect(this.x, this.y, 400, 50, 8);

        // Step
        this.createStat(this.x + 50, this.y + 25, 'STEP', state.currentStep);

        // Score
        this.createStat(this.x + 150, this.y + 25, 'SCORE', state.score);

        // Resolved
        const resolved = state.incidents.filter(i => i.resolved).length;
        const total = state.incidents.length;
        this.createStat(this.x + 280, this.y + 25, 'RESOLVED', `${resolved}/${total}`);

        // Sound toggle
        const soundIcon = this.scene.add.text(this.x + 370, this.y + 25, soundManager.enabled ? '🔊' : '🔇', {
            fontSize: '20px'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true });

        soundIcon.on('pointerdown', () => {
            soundManager.toggle();
            soundIcon.setText(soundManager.enabled ? '🔊' : '🔇');
        });
    }

    createStat(x, y, label, value) {
        this.scene.add.text(x, y - 10, label, {
            fontSize: '10px',
            color: '#a0a0a0',
            letterSpacing: 1
        }).setOrigin(0.5);

        this.scene.add.text(x, y + 10, value.toString(), {
            fontSize: '20px',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);
    }
}
