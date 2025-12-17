"""Incident loader from YAML files."""

import os
import sys
from pathlib import Path
from typing import Optional

import yaml

from alert_alchemy.models import Incident, Metrics


def get_incidents_path(custom_path: str | None = None) -> Path:
    """Get the path to the incidents directory.
    
    Search order:
    1. Custom path if provided
    2. ./incidents relative to current working directory
    3. incidents next to the executable (when frozen via PyInstaller)
    4. Fallback: incidents/ in the package directory (for development)
    
    Args:
        custom_path: Optional custom path to incidents directory.
        
    Returns:
        Path to the incidents directory.
    """
    # 1. Custom path takes priority
    if custom_path:
        custom = Path(custom_path)
        if custom.exists():
            return custom
    
    # 2. Check ./incidents relative to cwd
    cwd_incidents = Path.cwd() / "incidents"
    if cwd_incidents.exists():
        return cwd_incidents
    
    # 3. When running as frozen executable (PyInstaller)
    if getattr(sys, 'frozen', False):
        # _MEIPASS is the temp folder for PyInstaller bundles
        bundle_dir = Path(sys._MEIPASS)  # type: ignore
        frozen_incidents = bundle_dir / "incidents"
        if frozen_incidents.exists():
            return frozen_incidents
        
        # Also check next to the executable itself
        exe_dir = Path(sys.executable).parent
        exe_incidents = exe_dir / "incidents"
        if exe_incidents.exists():
            return exe_incidents
    
    # 4. Fallback: check relative to this module (development mode)
    module_dir = Path(__file__).parent
    # Go up to repo root: src/alert_alchemy -> src -> repo_root
    repo_root = module_dir.parent.parent
    dev_incidents = repo_root / "incidents"
    if dev_incidents.exists():
        return dev_incidents
    
    # Return cwd/incidents as default (may not exist)
    return cwd_incidents


def load_incidents(path: str | Path | None = None) -> list[Incident]:
    """Load incidents from YAML files in the specified directory.
    
    Args:
        path: Path to the incidents directory. If None, uses get_incidents_path().
        
    Returns:
        List of loaded incidents.
    """
    if path is None:
        incidents_dir = get_incidents_path()
    else:
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
