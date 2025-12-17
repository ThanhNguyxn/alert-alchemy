"""Scoring logic for Alert Alchemy game.

Scoring rules:
- Base score: 100
- Per elapsed step: -10
- Per wrong action: -15
- If action worsens situation: -5
- If resolved within <=2 steps: +10

Blast radius: 0-100 derived from error_rate and p95_latency
"""

from alert_alchemy.models import GameState, Incident

# Scoring constants
BASE_SCORE = 100
PENALTY_PER_STEP = 10
PENALTY_WRONG_ACTION = 15
PENALTY_WORSEN = 5
BONUS_QUICK_RESOLVE = 10
QUICK_RESOLVE_THRESHOLD = 2

# Blast radius thresholds
ERROR_RATE_CRITICAL = 50.0  # Error rate above this is critical
P95_LATENCY_CRITICAL = 5000.0  # 5 seconds p95 is critical


def calculate_score(state: GameState) -> int:
    """Calculate the current score based on game state.
    
    Args:
        state: Current game state.
        
    Returns:
        Calculated score (can be negative).
    """
    score = BASE_SCORE
    
    # Penalty for elapsed time
    score -= state.current_step * PENALTY_PER_STEP
    
    # Penalty for wrong actions
    for action in state.actions_taken:
        if not action.was_correct:
            score -= PENALTY_WRONG_ACTION
        if action.worsened:
            score -= PENALTY_WORSEN
    
    # Bonus for quick resolutions
    for incident in state.incidents:
        if incident.resolved and incident.resolved_at_step is not None:
            if incident.resolved_at_step <= QUICK_RESOLVE_THRESHOLD:
                score += BONUS_QUICK_RESOLVE
    
    return score


def calculate_blast_radius(incident: Incident) -> int:
    """Calculate blast radius (0-100) for an incident based on metrics.
    
    Blast radius represents the potential impact of an incident.
    Higher values indicate more severe impact.
    
    Args:
        incident: The incident to evaluate.
        
    Returns:
        Blast radius value between 0 and 100.
    """
    metrics = incident.metrics
    components = []
    
    # Error rate contribution (0-50 points)
    if metrics.error_rate is not None:
        error_contribution = min(50, (metrics.error_rate / ERROR_RATE_CRITICAL) * 50)
        components.append(error_contribution)
    
    # P95 latency contribution (0-50 points)
    if metrics.p95_latency is not None:
        latency_contribution = min(50, (metrics.p95_latency / P95_LATENCY_CRITICAL) * 50)
        components.append(latency_contribution)
    
    # If no metrics available, use severity as fallback
    if not components:
        severity_map = {
            "critical": 80,
            "high": 60,
            "medium": 40,
            "low": 20,
        }
        return severity_map.get(incident.severity.lower(), 40)
    
    # Sum components and clamp to 0-100
    blast_radius = sum(components)
    return max(0, min(100, int(blast_radius)))


def get_score_breakdown(state: GameState) -> dict[str, int]:
    """Get a detailed breakdown of the score calculation.
    
    Args:
        state: Current game state.
        
    Returns:
        Dictionary with score components.
    """
    breakdown = {
        "base": BASE_SCORE,
        "step_penalty": -state.current_step * PENALTY_PER_STEP,
        "wrong_action_penalty": 0,
        "worsen_penalty": 0,
        "quick_resolve_bonus": 0,
    }
    
    for action in state.actions_taken:
        if not action.was_correct:
            breakdown["wrong_action_penalty"] -= PENALTY_WRONG_ACTION
        if action.worsened:
            breakdown["worsen_penalty"] -= PENALTY_WORSEN
    
    for incident in state.incidents:
        if incident.resolved and incident.resolved_at_step is not None:
            if incident.resolved_at_step <= QUICK_RESOLVE_THRESHOLD:
                breakdown["quick_resolve_bonus"] += BONUS_QUICK_RESOLVE
    
    breakdown["total"] = sum(breakdown.values())
    return breakdown
