"""Tests for the scoring module."""

import pytest

from alert_alchemy.models import ActionRecord, GameState, Incident, Metrics
from alert_alchemy.scoring import (
    BASE_SCORE,
    BONUS_QUICK_RESOLVE,
    PENALTY_PER_STEP,
    PENALTY_WORSEN,
    PENALTY_WRONG_ACTION,
    calculate_blast_radius,
    calculate_score,
    get_score_breakdown,
)


class TestCalculateScore:
    """Tests for the calculate_score function."""
    
    def test_base_score_at_start(self) -> None:
        """Score should be BASE_SCORE at start with no actions."""
        state = GameState(
            current_step=0,
            score=100,
            incidents=[],
            actions_taken=[],
        )
        
        score = calculate_score(state)
        assert score == BASE_SCORE
    
    def test_step_penalty(self) -> None:
        """Each step should apply -10 penalty."""
        state = GameState(
            current_step=5,
            score=100,
            incidents=[],
            actions_taken=[],
        )
        
        score = calculate_score(state)
        expected = BASE_SCORE - (5 * PENALTY_PER_STEP)
        assert score == expected
    
    def test_wrong_action_penalty(self) -> None:
        """Wrong actions should apply -15 penalty each."""
        state = GameState(
            current_step=0,
            score=100,
            incidents=[],
            actions_taken=[
                ActionRecord(
                    step=1,
                    incident_id="INC-001",
                    action="wrong_action",
                    was_correct=False,
                ),
            ],
        )
        
        score = calculate_score(state)
        expected = BASE_SCORE - PENALTY_WRONG_ACTION
        assert score == expected
    
    def test_worsen_penalty(self) -> None:
        """Worsening actions should apply -5 penalty."""
        state = GameState(
            current_step=0,
            score=100,
            incidents=[],
            actions_taken=[
                ActionRecord(
                    step=1,
                    incident_id="INC-001",
                    action="bad_action",
                    was_correct=False,
                    worsened=True,
                ),
            ],
        )
        
        score = calculate_score(state)
        expected = BASE_SCORE - PENALTY_WRONG_ACTION - PENALTY_WORSEN
        assert score == expected
    
    def test_quick_resolve_bonus(self) -> None:
        """Resolving within 2 steps should give +10 bonus."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="high",
            resolved=True,
            resolved_at_step=2,
        )
        
        state = GameState(
            current_step=2,
            score=100,
            incidents=[incident],
            actions_taken=[
                ActionRecord(
                    step=2,
                    incident_id="INC-001",
                    action="correct_action",
                    was_correct=True,
                ),
            ],
        )
        
        score = calculate_score(state)
        expected = BASE_SCORE - (2 * PENALTY_PER_STEP) + BONUS_QUICK_RESOLVE
        assert score == expected
    
    def test_no_bonus_for_slow_resolve(self) -> None:
        """No bonus for resolving after 2 steps."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="high",
            resolved=True,
            resolved_at_step=5,
        )
        
        state = GameState(
            current_step=5,
            score=100,
            incidents=[incident],
            actions_taken=[
                ActionRecord(
                    step=5,
                    incident_id="INC-001",
                    action="correct_action",
                    was_correct=True,
                ),
            ],
        )
        
        score = calculate_score(state)
        # No quick resolve bonus
        expected = BASE_SCORE - (5 * PENALTY_PER_STEP)
        assert score == expected
    
    def test_combined_penalties_and_bonuses(self) -> None:
        """Test multiple penalties and bonuses combined."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="high",
            resolved=True,
            resolved_at_step=2,
        )
        
        state = GameState(
            current_step=3,
            score=100,
            incidents=[incident],
            actions_taken=[
                ActionRecord(
                    step=1,
                    incident_id="INC-001",
                    action="wrong",
                    was_correct=False,
                    worsened=True,
                ),
                ActionRecord(
                    step=2,
                    incident_id="INC-001",
                    action="correct",
                    was_correct=True,
                ),
            ],
        )
        
        score = calculate_score(state)
        expected = (
            BASE_SCORE
            - (3 * PENALTY_PER_STEP)  # -30 for 3 steps
            - PENALTY_WRONG_ACTION     # -15 for wrong action
            - PENALTY_WORSEN           # -5 for worsening
            + BONUS_QUICK_RESOLVE      # +10 for quick resolve
        )
        assert score == expected
    
    def test_score_can_go_negative(self) -> None:
        """Score should be able to go negative."""
        state = GameState(
            current_step=20,  # -200 penalty
            score=100,
            incidents=[],
            actions_taken=[
                ActionRecord(step=i, incident_id="", action="", was_correct=False)
                for i in range(5)  # 5 wrong actions = -75
            ],
        )
        
        score = calculate_score(state)
        assert score < 0


class TestCalculateBlastRadius:
    """Tests for the calculate_blast_radius function."""
    
    def test_blast_radius_from_error_rate(self) -> None:
        """High error rate should increase blast radius."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="medium",
            metrics=Metrics(error_rate=50.0),  # At critical threshold
        )
        
        blast_radius = calculate_blast_radius(incident)
        assert blast_radius == 50  # 50% of max contribution from error_rate
    
    def test_blast_radius_from_latency(self) -> None:
        """High latency should increase blast radius."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="medium",
            metrics=Metrics(p95_latency=5000.0),  # At critical threshold
        )
        
        blast_radius = calculate_blast_radius(incident)
        assert blast_radius == 50  # 50% of max contribution from latency
    
    def test_blast_radius_combined(self) -> None:
        """Both error rate and latency should contribute."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="medium",
            metrics=Metrics(error_rate=50.0, p95_latency=5000.0),
        )
        
        blast_radius = calculate_blast_radius(incident)
        assert blast_radius == 100  # Max combined
    
    def test_blast_radius_capped_at_100(self) -> None:
        """Blast radius should be capped at 100."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="medium",
            metrics=Metrics(error_rate=100.0, p95_latency=10000.0),  # Above thresholds
        )
        
        blast_radius = calculate_blast_radius(incident)
        assert blast_radius == 100
    
    def test_blast_radius_fallback_to_severity(self) -> None:
        """Should use severity when no metrics available."""
        for severity, expected in [
            ("critical", 80),
            ("high", 60),
            ("medium", 40),
            ("low", 20),
        ]:
            incident = Incident(
                id="INC-001",
                title="Test",
                description="",
                severity=severity,
                metrics=Metrics(),  # No metrics
            )
            
            blast_radius = calculate_blast_radius(incident)
            assert blast_radius == expected, f"Failed for severity: {severity}"
    
    def test_blast_radius_zero_metrics(self) -> None:
        """Zero metrics should give zero blast radius from metrics."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="medium",
            metrics=Metrics(error_rate=0.0, p95_latency=0.0),
        )
        
        blast_radius = calculate_blast_radius(incident)
        assert blast_radius == 0


class TestGetScoreBreakdown:
    """Tests for the get_score_breakdown function."""
    
    def test_breakdown_contains_all_components(self) -> None:
        """Breakdown should contain all scoring components."""
        state = GameState(
            current_step=0,
            score=100,
            incidents=[],
            actions_taken=[],
        )
        
        breakdown = get_score_breakdown(state)
        
        assert "base" in breakdown
        assert "step_penalty" in breakdown
        assert "wrong_action_penalty" in breakdown
        assert "worsen_penalty" in breakdown
        assert "quick_resolve_bonus" in breakdown
        assert "total" in breakdown
    
    def test_breakdown_total_matches_score(self) -> None:
        """Total in breakdown should match calculated score."""
        incident = Incident(
            id="INC-001",
            title="Test",
            description="",
            severity="high",
            resolved=True,
            resolved_at_step=1,
        )
        
        state = GameState(
            current_step=3,
            score=100,
            incidents=[incident],
            actions_taken=[
                ActionRecord(step=1, incident_id="INC-001", action="x", was_correct=True),
                ActionRecord(step=2, incident_id="INC-002", action="y", was_correct=False),
            ],
        )
        
        breakdown = get_score_breakdown(state)
        calculated_score = calculate_score(state)
        
        assert breakdown["total"] == calculated_score
