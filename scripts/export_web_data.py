#!/usr/bin/env python3
"""Export incidents from YAML files to JSON for the web app.

Reads all YAML files from the incidents/ directory and produces
web/data/incidents.json for the browser-based game.
"""

import json
import sys
from pathlib import Path

import yaml


def get_severity_order(severity: str) -> int:
    """Return sort order for severity (lower = more severe)."""
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(severity.lower() if severity else "", 2)


def parse_logs(logs_data) -> list[str]:
    """Parse logs from various formats to a list of strings."""
    if not logs_data:
        return []
    
    if isinstance(logs_data, list):
        result = []
        for entry in logs_data:
            if isinstance(entry, dict):
                # Format: {timestamp, level, service, message}
                ts = entry.get("timestamp", "")
                level = entry.get("level", "INFO")
                service = entry.get("service", "app")
                msg = entry.get("message", "")
                result.append(f"[{ts}] [{level}] [{service}] {msg}")
            else:
                result.append(str(entry))
        return result
    
    return [str(logs_data)]


def parse_traces(traces_data) -> list[str]:
    """Parse traces from various formats to a list of strings."""
    if not traces_data:
        return []
    
    if isinstance(traces_data, list):
        result = []
        for entry in traces_data:
            if isinstance(entry, dict):
                # Format: {service, duration_ms, status, timestamp, span_id, ...}
                service = entry.get("service", "unknown")
                duration = entry.get("duration_ms", 0)
                status = entry.get("status", "OK")
                span_id = entry.get("span_id", "")
                result.append(f"[{span_id[:8] if span_id else '???'}] {service}: {duration}ms ({status})")
            else:
                result.append(str(entry))
        return result
    
    return [str(traces_data)]


def parse_metrics(metrics_data) -> dict:
    """Parse metrics to a flat dict of numeric values."""
    if not metrics_data:
        return {}
    
    if isinstance(metrics_data, dict):
        return {
            k: v for k, v in metrics_data.items()
            if isinstance(v, (int, float))
        }
    
    return {}


def load_incident(filepath: Path) -> dict | None:
    """Load and normalize a single incident YAML file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data or not isinstance(data, dict):
            return None
        
        # Extract and normalize fields
        incident = {
            "id": data.get("id", filepath.stem),
            "title": data.get("title", "Untitled Incident"),
            "severity": data.get("severity", "medium"),
            "description": data.get("description", ""),
            "services": data.get("services", data.get("affected_services", [])),
            "metrics": parse_metrics(data.get("metrics", {})),
            "logs": parse_logs(data.get("logs", [])),
            "traces": parse_traces(data.get("traces", [])),
            "available_actions": data.get("available_actions", []),
            "correct_action": data.get("correct_action", ""),
        }
        
        # Derived fields for game
        desc = incident["description"]
        incident["short_summary"] = desc.split(".")[0] + "." if desc and "." in desc else desc
        incident["severity_rank"] = get_severity_order(incident["severity"])
        
        # Default actions if none provided
        if not incident["available_actions"]:
            incident["default_actions"] = ["rollback", "restart", "scale", "disable-flag", "clear-cache"]
        
        # Actions with notes (if structured actions exist)
        if "actions" in data and isinstance(data["actions"], list):
            incident["actions"] = data["actions"]
        
        # Passthrough other useful fields
        for key in ["resolution", "playbook", "optimal_resolution_steps", "timeline"]:
            if key in data:
                incident[key] = data[key]
        
        return incident
    except Exception as e:
        print(f"Warning: Failed to load {filepath}: {e}", file=sys.stderr)
        return None


def main():
    """Main entry point."""
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    incidents_dir = repo_root / "incidents"
    output_dir = repo_root / "web" / "data"
    output_file = output_dir / "incidents.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all incidents
    incidents = []
    yaml_files = list(incidents_dir.glob("*.yaml")) + list(incidents_dir.glob("*.yml"))
    
    if not yaml_files:
        print(f"Warning: No YAML files found in {incidents_dir}", file=sys.stderr)
    
    for filepath in yaml_files:
        incident = load_incident(filepath)
        if incident:
            incidents.append(incident)
    
    # Sort by severity (critical first), then by id
    incidents.sort(key=lambda x: (get_severity_order(x["severity"]), x["id"]))
    
    # Write JSON output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(incidents, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Exported {len(incidents)} incidents to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
