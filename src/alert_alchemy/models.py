"""Data models for Alert Alchemy game state and incidents."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Metrics:
    """Metrics associated with an incident."""
    
    error_rate: float | None = None  # Percentage 0-100
    p95_latency: float | None = None  # Milliseconds
    cpu_usage: float | None = None  # Percentage 0-100
    memory_usage: float | None = None  # Percentage 0-100
    request_count: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_rate": self.error_rate,
            "p95_latency": self.p95_latency,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "request_count": self.request_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Metrics":
        """Create from dictionary."""
        return cls(
            error_rate=data.get("error_rate"),
            p95_latency=data.get("p95_latency"),
            cpu_usage=data.get("cpu_usage"),
            memory_usage=data.get("memory_usage"),
            request_count=data.get("request_count"),
        )


@dataclass
class Incident:
    """Represents an incident in the game."""
    
    id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low
    metrics: Metrics = field(default_factory=Metrics)
    available_actions: list[str] = field(default_factory=list)
    correct_action: str = ""
    resolved: bool = False
    resolved_at_step: int | None = None
    logs: list[str] = field(default_factory=list)
    traces: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "metrics": self.metrics.to_dict(),
            "available_actions": self.available_actions,
            "correct_action": self.correct_action,
            "resolved": self.resolved,
            "resolved_at_step": self.resolved_at_step,
            "logs": self.logs,
            "traces": self.traces,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Incident":
        """Create from dictionary."""
        metrics_data = data.get("metrics", {})
        metrics = Metrics.from_dict(metrics_data) if metrics_data else Metrics()
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            severity=data.get("severity", "medium"),
            metrics=metrics,
            available_actions=data.get("available_actions", []),
            correct_action=data.get("correct_action", ""),
            resolved=data.get("resolved", False),
            resolved_at_step=data.get("resolved_at_step"),
            logs=data.get("logs", []),
            traces=data.get("traces", []),
        )


@dataclass
class ActionRecord:
    """Record of an action taken during the game."""
    
    step: int
    incident_id: str
    action: str
    was_correct: bool
    worsened: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step": self.step,
            "incident_id": self.incident_id,
            "action": self.action,
            "was_correct": self.was_correct,
            "worsened": self.worsened,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionRecord":
        """Create from dictionary."""
        return cls(
            step=data["step"],
            incident_id=data["incident_id"],
            action=data["action"],
            was_correct=data["was_correct"],
            worsened=data.get("worsened", False),
        )


@dataclass
class GameState:
    """Complete state of a game session."""
    
    current_step: int = 0
    score: int = 100  # Base score
    incidents: list[Incident] = field(default_factory=list)
    actions_taken: list[ActionRecord] = field(default_factory=list)
    started_at: str = ""
    ended: bool = False
    ended_at: str | None = None
    
    def __post_init__(self) -> None:
        """Set started_at if not provided."""
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_step": self.current_step,
            "score": self.score,
            "incidents": [inc.to_dict() for inc in self.incidents],
            "actions_taken": [act.to_dict() for act in self.actions_taken],
            "started_at": self.started_at,
            "ended": self.ended,
            "ended_at": self.ended_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Create from dictionary."""
        return cls(
            current_step=data.get("current_step", 0),
            score=data.get("score", 100),
            incidents=[Incident.from_dict(inc) for inc in data.get("incidents", [])],
            actions_taken=[ActionRecord.from_dict(act) for act in data.get("actions_taken", [])],
            started_at=data.get("started_at", ""),
            ended=data.get("ended", False),
            ended_at=data.get("ended_at"),
        )
