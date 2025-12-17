"""Incident loader from YAML files."""

from pathlib import Path
from typing import Optional

import yaml

from alert_alchemy.models import Incident, Metrics


def load_incidents(path: str | Path = "./incidents") -> list[Incident]:
    """Load incidents from YAML files in the specified directory.
    
    Args:
        path: Path to the incidents directory.
        
    Returns:
        List of loaded incidents.
    """
    incidents_dir = Path(path)
    if not incidents_dir.exists():
        return []
    
    incidents: list[Incident] = []
    
    for yaml_file in sorted(incidents_dir.glob("*.yaml")):
        loaded = load_incident_file(yaml_file)
        if loaded:
            incidents.extend(loaded)
    
    for yml_file in sorted(incidents_dir.glob("*.yml")):
        loaded = load_incident_file(yml_file)
        if loaded:
            incidents.extend(loaded)
    
    return incidents


def load_incident_file(file_path: Path) -> list[Incident]:
    """Load incidents from a single YAML file.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        List of incidents from the file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return []
    
    if data is None:
        return []
    
    # Handle both single incident and list of incidents
    if isinstance(data, list):
        return [parse_incident(item) for item in data if item]
    elif isinstance(data, dict):
        # Check if it's a wrapper with "incidents" key
        if "incidents" in data:
            return [parse_incident(item) for item in data["incidents"] if item]
        # Otherwise treat as single incident
        return [parse_incident(data)]
    
    return []


def parse_incident(data: dict) -> Incident:
    """Parse a single incident from a dictionary.
    
    Args:
        data: Dictionary containing incident data.
        
    Returns:
        Parsed Incident object.
    """
    metrics_data = data.get("metrics", {})
    metrics = Metrics(
        error_rate=metrics_data.get("error_rate"),
        p95_latency=metrics_data.get("p95_latency"),
        cpu_usage=metrics_data.get("cpu_usage"),
        memory_usage=metrics_data.get("memory_usage"),
        request_count=metrics_data.get("request_count"),
    )
    
    return Incident(
        id=str(data.get("id", "")),
        title=data.get("title", "Untitled Incident"),
        description=data.get("description", ""),
        severity=data.get("severity", "medium"),
        metrics=metrics,
        available_actions=data.get("available_actions", []),
        correct_action=data.get("correct_action", ""),
        resolved=data.get("resolved", False),
        logs=data.get("logs", []),
        traces=data.get("traces", []),
    )
