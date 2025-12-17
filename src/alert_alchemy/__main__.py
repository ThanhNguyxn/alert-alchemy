"""Module entrypoint for Alert Alchemy.

Enables running the package as a module: python -m alert_alchemy
"""

from alert_alchemy.cli import app

if __name__ == "__main__":
    app()
