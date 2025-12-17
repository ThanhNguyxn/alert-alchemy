"""State persistence for Alert Alchemy game."""

import json
from pathlib import Path
from typing import Optional

from alert_alchemy.models import GameState

STATE_FILENAME = ".alert_alchemy_state.json"


def get_state_path() -> Path:
    """Get the path to the state file in the current working directory."""
    return Path.cwd() / STATE_FILENAME


def save_state(state: GameState) -> None:
    """Save game state to the state file.
    
    Args:
        state: The game state to save.
    """
    state_path = get_state_path()
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)


def load_state() -> Optional[GameState]:
    """Load game state from the state file.
    
    Returns:
        The loaded game state, or None if no state file exists.
    """
    state_path = get_state_path()
    if not state_path.exists():
        return None
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GameState.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def delete_state() -> bool:
    """Delete the state file.
    
    Returns:
        True if the file was deleted, False if it didn't exist.
    """
    state_path = get_state_path()
    if state_path.exists():
        state_path.unlink()
        return True
    return False


def state_exists() -> bool:
    """Check if a state file exists.
    
    Returns:
        True if the state file exists.
    """
    return get_state_path().exists()
