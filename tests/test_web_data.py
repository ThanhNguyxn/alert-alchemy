"""Tests for web data scripts (generator and export)."""

import json
import tempfile
from pathlib import Path

import pytest


def test_generate_incident_pack_creates_files():
    """Test that generate_incident_pack creates YAML files."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    
    from generate_incident_pack import generate_incident, generate_seed_rng, write_yaml
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        rng = generate_seed_rng("test-seed")
        
        # Generate 5 incidents
        for i in range(1, 6):
            incident = generate_incident(rng, i)
            filepath = output_dir / f"{incident['id']}.yaml"
            write_yaml(incident, filepath)
        
        # Verify files created
        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) == 5
        
        # Verify content
        content = yaml_files[0].read_text()
        assert "id:" in content
        assert "title:" in content
        assert "severity:" in content


def test_generate_incident_pack_deterministic():
    """Test that same seed produces same incidents."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    
    from generate_incident_pack import generate_incident, generate_seed_rng
    
    rng1 = generate_seed_rng("same-seed")
    incident1 = generate_incident(rng1, 1)
    
    rng2 = generate_seed_rng("same-seed")
    incident2 = generate_incident(rng2, 1)
    
    assert incident1["id"] == incident2["id"]
    assert incident1["title"] == incident2["title"]
    assert incident1["severity"] == incident2["severity"]


def test_export_produces_valid_json():
    """Test that export produces valid JSON with required fields."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    
    repo_root = Path(__file__).parent.parent
    output_file = repo_root / "web" / "data" / "incidents.json"
    
    # Run export (assuming incidents exist)
    from export_web_data import main
    result = main()
    assert result == 0
    
    # Verify JSON
    assert output_file.exists()
    with open(output_file) as f:
        incidents = json.load(f)
    
    assert isinstance(incidents, list)
    assert len(incidents) >= 1
    
    # Check required fields
    for inc in incidents:
        assert "id" in inc
        assert "title" in inc
        assert "severity" in inc
        assert "severity_rank" in inc


def test_incident_has_derived_fields():
    """Test that exported incidents have derived fields."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    
    from export_web_data import load_incident
    
    repo_root = Path(__file__).parent.parent
    yaml_files = list((repo_root / "incidents").glob("*.yaml"))
    
    if yaml_files:
        incident = load_incident(yaml_files[0])
        assert incident is not None
        assert "short_summary" in incident
        assert "severity_rank" in incident
