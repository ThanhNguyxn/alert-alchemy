"""Tests for the game engine resolution logic."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from alert_alchemy.engine import Engine
from alert_alchemy.models import ActionRecord, GameState, Incident, Metrics
from alert_alchemy.state import STATE_FILENAME


@pytest.fixture
def sample_incident() -> Incident:
    """Create a sample incident for testing."""
    return Incident(
        id="INC-001",
        title="High Error Rate",
        description="Error rate is above threshold",
        severity="high",
        metrics=Metrics(error_rate=25.0, p95_latency=1500.0),
        available_actions=["scale_up", "restart_service", "rollback"],
        correct_action="rollback",
    )


@pytest.fixture
def sample_state(sample_incident: Incident) -> GameState:
    """Create a sample game state for testing."""
    return GameState(
        current_step=0,
        score=100,
        incidents=[sample_incident],
        actions_taken=[],
        started_at="2024-01-01T00:00:00",
        ended=False,
    )


@pytest.fixture
def engine_with_state(tmp_path: Path, sample_state: GameState):
    """Create an engine with pre-populated state."""
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    # Write state file
    state_file = tmp_path / STATE_FILENAME
    with open(state_file, "w") as f:
        json.dump(sample_state.to_dict(), f)
    
    engine = Engine()
    
    yield engine
    
    # Cleanup
    os.chdir(original_cwd)


class TestEngineResolve:
    """Tests for engine resolution logic."""
    
    def test_take_correct_action_resolves_incident(
        self, engine_with_state: Engine
    ) -> None:
        """Taking the correct action should resolve the incident."""
        success, message = engine_with_state.take_action("INC-001", "rollback")
        
        assert success is True
        assert "resolved" in message.lower()
        
        # Check incident is resolved
        incident = engine_with_state._find_incident("INC-001")
        assert incident is not None
        assert incident.resolved is True
        assert incident.resolved_at_step == 1
    
    def test_take_wrong_action_does_not_resolve(
        self, engine_with_state: Engine
    ) -> None:
        """Taking a wrong action should not resolve the incident."""
        success, message = engine_with_state.take_action("INC-001", "scale_up")
        
        assert success is True
        assert "not resolved" in message.lower()
        
        incident = engine_with_state._find_incident("INC-001")
        assert incident is not None
        assert incident.resolved is False
    
    def test_action_advances_time(self, engine_with_state: Engine) -> None:
        """Taking an action should advance time by +1."""
        initial_step = engine_with_state.state.current_step
        
        engine_with_state.take_action("INC-001", "scale_up")
        
        assert engine_with_state.state.current_step == initial_step + 1
    
    def test_action_records_are_created(self, engine_with_state: Engine) -> None:
        """Actions should create action records."""
        engine_with_state.take_action("INC-001", "scale_up")
        
        assert len(engine_with_state.state.actions_taken) == 1
        record = engine_with_state.state.actions_taken[0]
        
        assert record.incident_id == "INC-001"
        assert record.action == "scale_up"
        assert record.was_correct is False
    
    def test_correct_action_recorded_correctly(
        self, engine_with_state: Engine
    ) -> None:
        """Correct actions should be marked as correct."""
        engine_with_state.take_action("INC-001", "rollback")
        
        record = engine_with_state.state.actions_taken[0]
        assert record.was_correct is True
    
    def test_action_on_nonexistent_incident_fails(
        self, engine_with_state: Engine
    ) -> None:
        """Action on nonexistent incident should fail."""
        success, message = engine_with_state.take_action("NONEXISTENT", "scale_up")
        
        assert success is False
        assert "not found" in message.lower()
    
    def test_invalid_action_fails(self, engine_with_state: Engine) -> None:
        """Invalid action should fail."""
        success, message = engine_with_state.take_action("INC-001", "invalid_action")
        
        assert success is False
        assert "not available" in message.lower()
    
    def test_action_on_resolved_incident_fails(
        self, engine_with_state: Engine
    ) -> None:
        """Cannot take action on already resolved incident."""
        # First resolve it
        engine_with_state.take_action("INC-001", "rollback")
        
        # Try again
        success, message = engine_with_state.take_action("INC-001", "scale_up")
        
        assert success is False
        assert "already resolved" in message.lower()


class TestEngineTick:
    """Tests for the engine tick functionality."""
    
    def test_tick_advances_time(self, engine_with_state: Engine) -> None:
        """Tick should advance time by +1."""
        initial_step = engine_with_state.state.current_step
        
        engine_with_state.tick()
        
        assert engine_with_state.state.current_step == initial_step + 1
    
    def test_tick_updates_score(self, engine_with_state: Engine) -> None:
        """Tick should update score (decrease due to time penalty)."""
        initial_score = engine_with_state.state.score
        
        engine_with_state.tick()
        
        # Score should decrease (-10 per step)
        assert engine_with_state.state.score < initial_score


class TestEngineEndGame:
    """Tests for the end game functionality."""
    
    def test_end_game_sets_ended(self, engine_with_state: Engine) -> None:
        """Ending game should set ended flag."""
        engine_with_state.end_game()
        
        assert engine_with_state.state.ended is True
        assert engine_with_state.state.ended_at is not None
    
    def test_cannot_act_after_end(self, engine_with_state: Engine) -> None:
        """Cannot take actions after game ended."""
        engine_with_state.end_game()
        
        success, _ = engine_with_state.take_action("INC-001", "rollback")
        assert success is False
    
    def test_cannot_tick_after_end(self, engine_with_state: Engine) -> None:
        """Cannot tick after game ended."""
        engine_with_state.end_game()
        
        success, _ = engine_with_state.tick()
        assert success is False


class TestEngineResolveIncident:
    """Tests for the resolve_incident method."""
    
    def test_resolve_returns_correctness(self, engine_with_state: Engine) -> None:
        """resolve_incident should return whether action was correct."""
        success, message, was_correct = engine_with_state.resolve_incident(
            "INC-001", "rollback"
        )
        
        assert success is True
        assert was_correct is True
    
    def test_resolve_wrong_action_returns_false(
        self, engine_with_state: Engine
    ) -> None:
        """resolve_incident with wrong action returns was_correct=False."""
        success, message, was_correct = engine_with_state.resolve_incident(
            "INC-001", "scale_up"
        )
        
        assert success is True
        assert was_correct is False


class TestEngineWorsenDetection:
    """Tests for worsening action detection."""
    
    def test_restart_without_correct_action_worsens(
        self, engine_with_state: Engine
    ) -> None:
        """Restart action when not correct should mark as worsened."""
        # Add restart as available action
        incident = engine_with_state._find_incident("INC-001")
        incident.available_actions.append("restart_pods")
        
        engine_with_state.take_action("INC-001", "restart_pods")
        
        record = engine_with_state.state.actions_taken[0]
        assert record.worsened is True
    
    def test_correct_action_does_not_worsen(
        self, engine_with_state: Engine
    ) -> None:
        """Correct action should not be marked as worsened."""
        engine_with_state.take_action("INC-001", "rollback")
        
        record = engine_with_state.state.actions_taken[0]
        assert record.worsened is False


class TestEngineNoState:
    """Tests for engine behavior without state."""
    
    def test_action_without_state_fails(self, tmp_path: Path) -> None:
        """Actions should fail when no state exists."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            engine = Engine()
            success, message = engine.take_action("INC-001", "scale_up")
            
            assert success is False
            assert "start" in message.lower()
        finally:
            os.chdir(original_cwd)
    
    def test_tick_without_state_fails(self, tmp_path: Path) -> None:
        """Tick should fail when no state exists."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            engine = Engine()
            success, message = engine.tick()
            
            assert success is False
            assert "start" in message.lower()
        finally:
            os.chdir(original_cwd)
