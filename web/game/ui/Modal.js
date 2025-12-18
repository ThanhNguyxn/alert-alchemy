/**
 * Modal - Simple modal dialog for overlays
 */
class Modal {
    constructor(scene, title, lines) {
        this.scene = scene;
        this.title = title;
        this.lines = lines;
        this.container = null;
    }

    show() {
        const { width, height } = this.scene.cameras.main;

        // Overlay
        const overlay = this.scene.add.graphics();
        overlay.fillStyle(0x000000, 0.8);
        overlay.fillRect(0, 0, width, height);
        overlay.setInteractive(new Phaser.Geom.Rectangle(0, 0, width, height), Phaser.Geom.Rectangle.Contains);
        overlay.on('pointerdown', () => this.close(overlay, panel, titleText, contentTexts, closeBtn));

        // Panel
        const panelWidth = 450;
        const panelHeight = 320;
        const panelX = (width - panelWidth) / 2;
        const panelY = (height - panelHeight) / 2;

        const panel = this.scene.add.graphics();
        panel.fillStyle(COLORS.panel, 1);
        panel.lineStyle(2, COLORS.accent, 1);
        panel.fillRoundedRect(panelX, panelY, panelWidth, panelHeight, 16);
        panel.strokeRoundedRect(panelX, panelY, panelWidth, panelHeight, 16);

        // Title
        const titleText = this.scene.add.text(width / 2, panelY + 35, this.title, {
            fontSize: '28px',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5);

        // Content
        const contentTexts = [];
        this.lines.forEach((line, i) => {
            const text = this.scene.add.text(panelX + 30, panelY + 80 + i * 30, line, {
                fontSize: '16px',
                color: '#e8e8e8'
            });
            contentTexts.push(text);
        });

        // Close button
        const closeBtn = this.scene.add.text(width / 2, panelY + panelHeight - 45, 'Got it!', {
            fontSize: '18px',
            fontStyle: 'bold',
            color: '#06b6d4'
        }).setOrigin(0.5).setInteractive({ useHandCursor: true });

        closeBtn.on('pointerdown', () => this.close(overlay, panel, titleText, contentTexts, closeBtn));
    }

    close(overlay, panel, titleText, contentTexts, closeBtn) {
        overlay.destroy();
        panel.destroy();
        titleText.destroy();
        contentTexts.forEach(t => t.destroy());
        closeBtn.destroy();
    }
}
