<div align="center">

# 🧪 Alert Alchemy

**Incident Response Simulator Game**

Train your on-call instincts by triaging alerts, investigating clues, and resolving production incidents before they spiral out of control.

[![Play in Browser](https://img.shields.io/badge/▶_Play_in_Browser-06b6d4?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnD3dpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiPjxwb2x5Z29uIHBvaW50cz0iNSAzIDIzIDEyIDUgMjEgNSAzIi8+PC9zdmc+)](https://thanhnguyxn.github.io/alert-alchemy/)
[![Download](https://img.shields.io/badge/Download-Windows%20|%20macOS%20|%20Linux-8b5cf6?style=for-the-badge)](https://github.com/ThanhNguyxn/alert-alchemy/releases/latest)
[![Buy Me a Coffee](https://img.shields.io/badge/☕_Buy_Me_a_Coffee-FFDD00?style=for-the-badge)](https://buymeacoffee.com/thanhnguyxn)

</div>

---

## 🎮 Play Now (No Install)

**[▶ Click here to play in your browser](https://thanhnguyxn.github.io/alert-alchemy/)**

- Works on any device with a modern browser
- Progress saved locally in your browser
- No account required

---

## 📦 Download & Run (Offline)

Download from the [Releases page](https://github.com/ThanhNguyxn/alert-alchemy/releases/latest).

### Windows (Recommended)

1. Download `alert-alchemy-windows.zip`
2. Extract to a folder
3. **Double-click `alert-alchemy-gui.exe`** — opens a graphical window
4. Or run `alert-alchemy.exe` for CLI mode

### macOS / Linux

1. Download `alert-alchemy-macos.zip` or `alert-alchemy-linux.zip`
2. Extract and run `./alert-alchemy` in terminal
3. The interactive menu will guide you

### Via Python (Any OS)

```bash
pip install git+https://github.com/ThanhNguyxn/alert-alchemy.git
alert-alchemy        # CLI mode
```

For the GUI (Windows):
```bash
pip install "alert-alchemy[gui]"
alert-alchemy-gui
```

---

## 🕹️ How to Play

1. **Pick an incident** from the war room
2. **Inspect** to unlock clues (logs, metrics, traces)
3. **Choose an action** (rollback, scale, restart, etc.)
4. **Watch the outcome** — correct actions resolve incidents
5. **Finish your shift** before time runs out

### Tips

- 🔍 **Inspecting first** increases your success rate
- ⏰ Every action advances time (costs score)
- 🎲 Random events keep each run fresh
- 🌟 Same seed = same run (use for challenges)

---

## 📋 Game Features

| Feature | Description |
|---------|-------------|
| **Replay Variety** | Seeded runs, random events, difficulty modes |
| **30+ Incidents** | Auto-generated incident pack with diverse scenarios |
| **Difficulty Modes** | Easy, Normal, Hard |
| **Incident Subset** | Choose 3, 5, or 8 incidents per run |
| **Random Events** | Traffic spikes, cache stampedes, DB failovers... |
| **Action Outcomes** | Success, partial, no effect, backfired |

---

## 🛠️ For Developers

### Setup

```bash
git clone https://github.com/ThanhNguyxn/alert-alchemy.git
cd alert-alchemy
pip install -e ".[dev]"
```

### Commands

```bash
alert-alchemy --help       # See all commands
alert-alchemy start        # Start new game
alert-alchemy play         # Interactive mode
alert-alchemy status       # Check current game
pytest                     # Run tests
```

### Project Structure

```
alert-alchemy/
├── src/alert_alchemy/    # Python source
├── incidents/            # Hand-written YAML incidents
├── incidents/generated/  # Auto-generated incidents (build-time)
├── web/                  # Browser game (Phaser 3)
├── scripts/              # Build scripts
└── tests/                # Pytest tests
```

### Incidents

Incidents are YAML files in `incidents/`. Each has:

```yaml
id: "INC-001"
title: "High latency in checkout API"
severity: critical
description: "Users are reporting slow checkout..."
services: ["payment-api", "postgres"]
metrics:
  error_rate: 25
  p95_latency: 3500
logs: ["[ERROR] Timeout...", "..."]
traces: ["[span] api → db: 2340ms"]
actions:
  - name: rollback
    note: "Revert to last deploy"
```

The build generates 30 additional incidents for variety.

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

- 🐛 [Report bugs](https://github.com/ThanhNguyxn/alert-alchemy/issues)
- 💡 [Request features](https://github.com/ThanhNguyxn/alert-alchemy/issues)
- 📖 [Security policy](SECURITY.md)
- 📜 [Code of Conduct](CODE_OF_CONDUCT.md)

---

<div align="center">

Made with ☕ by [ThanhNguyxn](https://github.com/ThanhNguyxn)

**[▶ Play Now](https://thanhnguyxn.github.io/alert-alchemy/)** · **[Download](https://github.com/ThanhNguyxn/alert-alchemy/releases)**

</div>
