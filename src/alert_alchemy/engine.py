"""Core game engine for Alert Alchemy."""

from datetime import datetime
from typing import Optional

from alert_alchemy.loader import load_incidents
from alert_alchemy.models import ActionRecord, GameState, Incident
from alert_alchemy.scoring import calculate_score
from alert_alchemy.state import delete_state, load_state, save_state


class Engine:
    """Core game engine managing game state and actions."""
    
    def __init__(self, incidents_path: str = "./incidents") -> None:
        """Initialize the engine.
        
        Args:
            incidents_path: Path to the incidents directory.
        """
        self.incidents_path = incidents_path
        self._state: Optional[GameState] = None
    
    @property
    def state(self) -> Optional[GameState]:
        """Get current game state, loading from disk if needed."""
        if self._state is None:
            self._state = load_state()
        return self._state
    
    def start_game(self) -> GameState:
        """Start a new game.
        
        Returns:
            The new game state.
        """
        incidents = load_incidents(self.incidents_path)
        
        self._state = GameState(
            current_step=0,
            score=100,
            incidents=incidents,
            actions_taken=[],
            started_at=datetime.now().isoformat(),
            ended=False,
        )
        
        save_state(self._state)
        return self._state
    
    def take_action(self, incident_id: str, action: str) -> tuple[bool, str]:
        """Take an action on an incident.
        
        This advances time by +1 step.
        
        Args:
            incident_id: ID of the incident to act on.
            action: The action to take.
            
        Returns:
            Tuple of (success, message).
        """
        if self.state is None:
            return False, "No active game. Run 'alert-alchemy start' first."
        
        if self.state.ended:
            return False, "Game has already ended."
        
        # Find the incident
        incident = self._find_incident(incident_id)
        if incident is None:
            return False, f"Incident '{incident_id}' not found."
        
        if incident.resolved:
            return False, f"Incident '{incident_id}' is already resolved."
        
        # Check if action is valid
        if action not in incident.available_actions:
            return False, f"Action '{action}' is not available for this incident."
        
        # Advance time
        self.state.current_step += 1
        
        # Check if action is correct
        is_correct = action == incident.correct_action
        worsened = self._did_action_worsen(incident, action)
        
        # Record the action
        record = ActionRecord(
            step=self.state.current_step,
            incident_id=incident_id,
            action=action,
            was_correct=is_correct,
            worsened=worsened,
        )
        self.state.actions_taken.append(record)
        
        # Resolve if correct
        if is_correct:
            incident.resolved = True
            incident.resolved_at_step = self.state.current_step
            message = f"✓ Incident '{incident_id}' resolved!"
        else:
            message = f"Action taken, but incident not resolved."
            if worsened:
                message += " The situation may have worsened."
        
        # Update score
        self.state.score = calculate_score(self.state)
        
        save_state(self.state)
        return True, message
    
    def tick(self) -> tuple[bool, str]:
        """Advance time by one step without taking an action.
        
        Returns:
            Tuple of (success, message).
        """
        if self.state is None:
            return False, "No active game. Run 'alert-alchemy start' first."
        
        if self.state.ended:
            return False, "Game has already ended."
        
        self.state.current_step += 1
        self.state.score = calculate_score(self.state)
        
        save_state(self.state)
        return True, f"Time advanced to step {self.state.current_step}."
    
    def end_game(self) -> tuple[bool, str]:
        """End the current game.
        
        Returns:
            Tuple of (success, message).
        """
        if self.state is None:
            return False, "No active game. Run 'alert-alchemy start' first."
        
        if self.state.ended:
            return False, "Game has already ended."
        
        self.state.ended = True
        self.state.ended_at = datetime.now().isoformat()
        self.state.score = calculate_score(self.state)
        
        save_state(self.state)
        return True, f"Game ended with final score: {self.state.score}"
    
    def reset_game(self) -> tuple[bool, str]:
        """Reset/delete the current game state.
        
        Returns:
            Tuple of (success, message).
        """
        deleted = delete_state()
        self._state = None
        
        if deleted:
            return True, "Game state reset."
        return True, "No game state to reset."
    
    def resolve_incident(self, incident_id: str, action: str) -> tuple[bool, str, bool]:
        """Attempt to resolve an incident with a specific action.
        
        Args:
            incident_id: ID of the incident.
            action: The action to attempt.
            
        Returns:
            Tuple of (success, message, was_correct).
        """
        success, message = self.take_action(incident_id, action)
        
        if not success:
            return success, message, False
        
        # Check if it was the correct action
        incident = self._find_incident(incident_id)
        was_correct = incident is not None and incident.resolved
        
        return success, message, was_correct
    
    def _find_incident(self, incident_id: str) -> Optional[Incident]:
        """Find an incident by ID.
        
        Args:
            incident_id: The incident ID to find.
            
        Returns:
            The incident or None if not found.
        """
        if self.state is None:
            return None
        
        for incident in self.state.incidents:
            if incident.id == incident_id:
                return incident
        return None
    
    def _did_action_worsen(self, incident: Incident, action: str) -> bool:
        """Check if an action worsened the incident.
        
        For now, this is a simple heuristic: certain keywords indicate worsening.
        
        Args:
            incident: The incident.
            action: The action taken.
            
        Returns:
            True if the action worsened the situation.
        """
        worsen_keywords = ["restart", "reboot", "delete", "drop", "kill"]
        action_lower = action.lower()
        
        # If it's not the correct action and contains worsen keywords
        if action != incident.correct_action:
            for keyword in worsen_keywords:
                if keyword in action_lower:
                    return True
        
        return False
