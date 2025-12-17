# Writing an Incident for Alert Alchemy

This guide explains how to create incident YAML files for the Alert Alchemy game.

## File Location

Place incident files in the `incidents/` directory with naming convention:
```
incidents/NNN-short-name.yaml
```

## Required Schema

```yaml
id: INC-001                    # Unique identifier
title: "Short descriptive title"
severity: critical|high|medium|low
description: |
  Multi-line description of what's happening.
  Include: symptoms, impact, when it started.

services:
  - affected-service-1
  - affected-service-2

metrics:
  error_rate: 25.0           # Percentage (0-100)
  p95_latency: 2500          # Milliseconds
  cpu_usage: 80.0            # Percentage (optional)
  memory_usage: 70.0         # Percentage (optional)
  request_count: 10000       # Recent request count (optional)

logs:
  - "[timestamp] LEVEL service Message"
  - "[timestamp] ERROR service Error details"

traces:
  - "trace-id: Request path -> service (outcome)"

available_actions:
  - rollback
  - scale
  - restart
  - disable-flag
  - increase-pool
  - enable-cache

correct_action: rollback      # The optimal single action

timeline:
  - step: 0
    event: "Initial alert description"
  - step: 1
    action: some-action
    outcome: "What happens"
    trade_off: "Cost/benefit"
    resolved: true           # Optional, marks resolution
    worsens: true            # Optional, marks negative outcome

resolution:
  optimal_path: ["action1", "action2"]
  explanation: |
    Root cause analysis and why this path works.
```

## Scoring Impact

| Metric | Blast Radius Contribution |
|--------|---------------------------|
| `error_rate` at 50% | +50 points |
| `p95_latency` at 5000ms | +50 points |
| Combined max | 100 points |

If no metrics provided, severity determines blast radius:
- critical: 80
- high: 60  
- medium: 40
- low: 20

## Design Tips

1. **Make it solvable in 2-3 steps** - At least one path should resolve quickly for skilled players
2. **Include red herrings** - Actions that seem reasonable but don't fix the issue
3. **Add worsening actions** - Some actions should make things worse (e.g., scaling when DB is the bottleneck)
4. **Realistic logs/traces** - Help players diagnose before acting
5. **Trade-offs matter** - Every action should have a cost, even correct ones

## Example Actions

| Action | Typical Use Case |
|--------|------------------|
| `rollback` | Bad deploy, code regression |
| `scale` | Capacity issues (but not always!) |
| `restart` | Stuck processes, stale state |
| `disable-flag` | Feature flag caused the issue |
| `increase-pool` | Connection exhaustion |
| `enable-cache` | Reduce backend load |

## Testing Your Incident

```bash
# Start a game with your incidents
alert-alchemy start

# Check they loaded
alert-alchemy status

# Verify metrics display
alert-alchemy metrics
```
