"""Alert Alchemy - Incident Response Simulator Game.

A terminal/CLI incident-response simulator where you 'brew' fixes from noisy alerts.
"""

__version__ = "0.1.0"
__author__ = "Alert Alchemy Contributors"

from alert_alchemy.models import Incident, GameState
from alert_alchemy.engine import Engine
from alert_alchemy.loader import load_incidents
from alert_alchemy.scoring import calculate_score, calculate_blast_radius

__all__ = [
    "__version__",
    "Incident",
    "GameState",
    "Engine",
    "load_incidents",
    "calculate_score",
    "calculate_blast_radius",
]
