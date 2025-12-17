"""Tests for interactive module and smart action functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from alert_alchemy.engine import Engine
from alert_alchemy.models import GameState, Incident, Metrics
from alert_alchemy.interactive import (
    get_active_incidents,
    get_incident_by_highest_blast_radius,
    smart_action,
    render_actions_list,
    is_interactive,
)
from alert_alchemy.state import delete_state


@pytest.fixture
def sample_incidents():
    """Create sample incidents for testing."""
    return [
        Incident(
            id="INC-001",
            title="Memory Leak",
            description="Memory issue",
            severity="high",
            metrics=Metrics(error_rate=25.0, p95_latency=2000),
            available_actions=["rollback", "restart", "scale"],
            correct_action="rollback",
            resolved=False,
        ),
        Incident(
            id="INC-002",
            title="Database Issue",
            description="DB connection pool",
            severity="critical",
            metrics=Metrics(error_rate=40.0, p95_latency=3000),
            available_actions=["increase-pool", "restart", "rollback"],
            correct_action="increase-pool",
            resolved=False,
        ),
        Incident(
            id="INC-003",
            title="Config Error",
            description="Bad config",
            severity="low",
            metrics=Metrics(error_rate=5.0, p95_latency=500),
            available_actions=["disable-flag", "rollback"],
            correct_action="disable-flag",
            resolved=True,  # Already resolved
        ),
    ]


@pytest.fixture(autouse=True)
def cleanup_state():
    """Clean up game state before and after each test."""
    delete_state()
    yield
    delete_state()


class TestGetActiveIncidents:
    """Tests for get_active_incidents function."""
    
    def test_filters_resolved_incidents(self, sample_incidents):
        """Should return only unresolved incidents."""
        state = GameState(incidents=sample_incidents)
        active = get_active_incidents(state)
        
        assert len(active) == 2
        assert all(not inc.resolved for inc in active)
        assert "INC-001" in [inc.id for inc in active]
        assert "INC-002" in [inc.id for inc in active]
        assert "INC-003" not in [inc.id for inc in active]
    
    def test_empty_when_all_resolved(self):
        """Should return empty list when all incidents resolved."""
        incidents = [
            Incident(
                id="INC-001",
                title="Test",
                description="",
                severity="low",
                resolved=True,
            )
        ]
        state = GameState(incidents=incidents)
        active = get_active_incidents(state)
        
        assert len(active) == 0


class TestGetIncidentByHighestBlastRadius:
    """Tests for get_incident_by_highest_blast_radius function."""
    
    def test_returns_highest_blast_radius(self, sample_incidents):
        """Should return incident with highest blast radius."""
        # INC-002 has higher error_rate (40%) so higher blast radius
        active = [inc for inc in sample_incidents if not inc.resolved]
        result = get_incident_by_highest_blast_radius(active)
        
        assert result is not None
        assert result.id == "INC-002"
    
    def test_returns_none_for_empty_list(self):
        """Should return None for empty list."""
        result = get_incident_by_highest_blast_radius([])
        assert result is None


class TestSmartAction:
    """Tests for smart_action function."""
    
    def test_action_with_single_incident(self, tmp_path: Path):
        """Should auto-select when only one active incident."""
        # Create a test incident
        incident_data = {
            "id": "INC-SINGLE",
            "title": "Single Incident",
            "description": "Test",
            "severity": "high",
            "available_actions": ["rollback", "restart"],
            "correct_action": "rollback",
        }
        
        # Create incidents directory
        incidents_dir = tmp_path / "incidents"
        incidents_dir.mkdir()
        
        import yaml
        with open(incidents_dir / "test.yaml", "w") as f:
            yaml.dump(incident_data, f)
        
        # Start game
        engine = Engine(incidents_path=str(incidents_dir))
        engine.start_game()
        
        # Call smart_action with only action name
        success, message = smart_action("rollback", None, engine)
        
        assert success is True
        assert "resolved" in message.lower()
    
    def test_action_with_explicit_incident_id(self, tmp_path: Path):
        """Should work with explicit incident ID."""
        incident_data = {
            "id": "INC-EXPLICIT",
            "title": "Test Incident",
            "description": "Test",
            "severity": "medium",
            "available_actions": ["restart"],
            "correct_action": "restart",
        }
        
        incidents_dir = tmp_path / "incidents"
        incidents_dir.mkdir()
        
        import yaml
        with open(incidents_dir / "test.yaml", "w") as f:
            yaml.dump(incident_data, f)
        
        engine = Engine(incidents_path=str(incidents_dir))
        engine.start_game()
        
        success, message = smart_action("restart", "INC-EXPLICIT", engine)
        
        assert success is True
    
    def test_action_with_invalid_incident_id(self, tmp_path: Path):
        """Should fail with invalid incident ID."""
        incident_data = {
            "id": "INC-001",
            "title": "Test",
            "description": "",
            "severity": "low",
            "available_actions": ["restart"],
            "correct_action": "restart",
        }
        
        incidents_dir = tmp_path / "incidents"
        incidents_dir.mkdir()
        
        import yaml
        with open(incidents_dir / "test.yaml", "w") as f:
            yaml.dump(incident_data, f)
        
        engine = Engine(incidents_path=str(incidents_dir))
        engine.start_game()
        
        success, message = smart_action("restart", "INVALID-ID", engine)
        
        assert success is False
        assert "not found" in message.lower()
    
    def test_action_fails_without_game(self):
        """Should fail when no game is active."""
        delete_state()
        engine = Engine()
        
        success, message = smart_action("rollback", None, engine)
        
        assert success is False
        assert "no active game" in message.lower()


class TestRenderActionsList:
    """Tests for render_actions_list function."""
    
    def test_renders_without_error(self, sample_incidents, capsys):
        """Should render actions list without error."""
        state = GameState(incidents=sample_incidents)
        
        # This should not raise an exception
        render_actions_list(state)
    
    def test_renders_filtered_by_incident(self, sample_incidents, capsys):
        """Should filter by incident ID when provided."""
        state = GameState(incidents=sample_incidents)
        
        # Should not raise an exception
        render_actions_list(state, "INC-001")
    
    def test_handles_invalid_incident_id(self, sample_incidents, capsys):
        """Should handle invalid incident ID gracefully."""
        state = GameState(incidents=sample_incidents)
        
        # Should print error message but not raise
        render_actions_list(state, "INVALID-ID")


class TestIsInteractive:
    """Tests for is_interactive function."""
    
    def test_returns_boolean(self):
        """Should return a boolean value."""
        result = is_interactive()
        assert isinstance(result, bool)
