"""Module entrypoint for Alert Alchemy.

Enables running the package as a module: python -m alert_alchemy

When run with no arguments, automatically starts interactive play mode
for non-technical users.
"""

import sys

from alert_alchemy.cli import app


def main():
    """Main entrypoint with auto-play support."""
    # If no arguments provided (just the program name), start interactive mode
    if len(sys.argv) == 1:
        # Insert 'play' as the default command
        sys.argv.append("play")
    
    app()


if __name__ == "__main__":
    main()
