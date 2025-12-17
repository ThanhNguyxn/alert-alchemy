"""Tests for the incident loader module."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from alert_alchemy.loader import load_incidents, load_incident_file, parse_incident


class TestLoadIncidents:
    """Tests for the load_incidents function."""
    
    def test_load_from_nonexistent_directory(self) -> None:
        """Should return empty list for nonexistent directory."""
        result = load_incidents("/nonexistent/path/that/does/not/exist")
        assert result == []
    
    def test_load_from_empty_directory(self, tmp_path: Path) -> None:
        """Should return empty list for empty directory."""
        result = load_incidents(str(tmp_path))
        assert result == []
    
    def test_load_single_incident_yaml(self, tmp_path: Path) -> None:
        """Should load a single incident from YAML file."""
        incident_data = {
            "id": "INC-001",
            "title": "High CPU Usage",
            "description": "CPU usage is above 90%",
            "severity": "high",
            "metrics": {
                "cpu_usage": 95.0,
                "error_rate": 5.0,
            },
            "available_actions": ["scale_up", "restart_service", "investigate"],
            "correct_action": "scale_up",
        }
        
        yaml_file = tmp_path / "incident.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(incident_data, f)
        
        result = load_incidents(str(tmp_path))
        
        assert len(result) == 1
        assert result[0].id == "INC-001"
        assert result[0].title == "High CPU Usage"
        assert result[0].severity == "high"
        assert result[0].metrics.cpu_usage == 95.0
        assert result[0].correct_action == "scale_up"
    
    def test_load_multiple_incidents_from_list(self, tmp_path: Path) -> None:
        """Should load multiple incidents from a YAML list."""
        incidents_data = [
            {
                "id": "INC-001",
                "title": "Incident 1",
                "description": "First incident",
                "severity": "high",
            },
            {
                "id": "INC-002",
                "title": "Incident 2",
                "description": "Second incident",
                "severity": "low",
            },
        ]
        
        yaml_file = tmp_path / "incidents.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(incidents_data, f)
        
        result = load_incidents(str(tmp_path))
        
        assert len(result) == 2
        assert result[0].id == "INC-001"
        assert result[1].id == "INC-002"
    
    def test_load_incidents_with_wrapper_key(self, tmp_path: Path) -> None:
        """Should load incidents from a dict with 'incidents' key."""
        incidents_data = {
            "incidents": [
                {
                    "id": "INC-001",
                    "title": "Wrapped Incident",
                    "description": "Has wrapper",
                    "severity": "medium",
                },
            ]
        }
        
        yaml_file = tmp_path / "wrapped.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(incidents_data, f)
        
        result = load_incidents(str(tmp_path))
        
        assert len(result) == 1
        assert result[0].id == "INC-001"
    
    def test_load_from_multiple_files(self, tmp_path: Path) -> None:
        """Should load from multiple YAML files."""
        # File 1
        with open(tmp_path / "a_first.yaml", "w") as f:
            yaml.dump({"id": "INC-A", "title": "A", "description": "", "severity": "low"}, f)
        
        # File 2
        with open(tmp_path / "b_second.yaml", "w") as f:
            yaml.dump({"id": "INC-B", "title": "B", "description": "", "severity": "high"}, f)
        
        result = load_incidents(str(tmp_path))
        
        assert len(result) == 2
        # Should be sorted by filename
        assert result[0].id == "INC-A"
        assert result[1].id == "INC-B"
    
    def test_load_yml_extension(self, tmp_path: Path) -> None:
        """Should also load .yml files."""
        incident_data = {
            "id": "INC-YML",
            "title": "YML Incident",
            "description": "From .yml file",
            "severity": "critical",
        }
        
        yml_file = tmp_path / "incident.yml"
        with open(yml_file, "w") as f:
            yaml.dump(incident_data, f)
        
        result = load_incidents(str(tmp_path))
        
        assert len(result) == 1
        assert result[0].id == "INC-YML"


class TestParseIncident:
    """Tests for the parse_incident function."""
    
    def test_parse_minimal_incident(self) -> None:
        """Should parse incident with minimal data."""
        data = {
            "id": "INC-MIN",
            "title": "Minimal",
        }
        
        result = parse_incident(data)
        
        assert result.id == "INC-MIN"
        assert result.title == "Minimal"
        assert result.description == ""
        assert result.severity == "medium"  # Default
        assert result.resolved is False
    
    def test_parse_full_incident(self) -> None:
        """Should parse incident with all fields."""
        data = {
            "id": "INC-FULL",
            "title": "Full Incident",
            "description": "Complete data",
            "severity": "critical",
            "metrics": {
                "error_rate": 25.0,
                "p95_latency": 2500.0,
                "cpu_usage": 80.0,
                "memory_usage": 70.0,
                "request_count": 1000,
            },
            "available_actions": ["action1", "action2"],
            "correct_action": "action1",
            "logs": ["log1", "log2"],
            "traces": ["trace1"],
        }
        
        result = parse_incident(data)
        
        assert result.id == "INC-FULL"
        assert result.severity == "critical"
        assert result.metrics.error_rate == 25.0
        assert result.metrics.p95_latency == 2500.0
        assert len(result.available_actions) == 2
        assert result.correct_action == "action1"
        assert len(result.logs) == 2
        assert len(result.traces) == 1


class TestLoadIncidentFile:
    """Tests for the load_incident_file function."""
    
    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Should return empty list for invalid YAML."""
        bad_file = tmp_path / "bad.yaml"
        with open(bad_file, "w") as f:
            f.write("{ invalid yaml: [")
        
        result = load_incident_file(bad_file)
        assert result == []
    
    def test_empty_file(self, tmp_path: Path) -> None:
        """Should return empty list for empty file."""
        empty_file = tmp_path / "empty.yaml"
        with open(empty_file, "w") as f:
            f.write("")
        
        result = load_incident_file(empty_file)
        assert result == []
