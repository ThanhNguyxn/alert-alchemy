"""CLI for Alert Alchemy - Incident Response Simulator Game.

Commands:
- start: Initialize a new game
- status: Show current incidents (does not advance time)
- logs: Show incident logs (does not advance time)
- metrics: Show metrics table (does not advance time)
- traces: Show traces (does not advance time)
- action: Take an action on an incident (advances time +1)
- tick: Advance time without action (advances time +1)
- end: End the current game
- reset: Clear game state
"""

from typing import Optional

import typer
from rich.console import Console

from alert_alchemy.engine import Engine
from alert_alchemy.render import (
    console,
    render_action_result,
    render_game_end,
    render_incident_detail,
    render_logs,
    render_metrics,
    render_no_state_message,
    render_status,
    render_traces,
)
from alert_alchemy.state import load_state, state_exists

app = typer.Typer(
    name="alert-alchemy",
    help="🧪 Alert Alchemy - Incident Response Simulator Game",
    add_completion=False,
)


def get_engine() -> Engine:
    """Get an engine instance."""
    return Engine()


def require_state(func):
    """Decorator to require an active game state."""
    def wrapper(*args, **kwargs):
        if not state_exists():
            render_no_state_message()
            raise typer.Exit(1)
        return func(*args, **kwargs)
    return wrapper


@app.command()
def start(
    incidents_path: str = typer.Option(
        "./incidents",
        "--incidents", "-i",
        help="Path to incidents directory",
    ),
) -> None:
    """Start a new game session."""
    if state_exists():
        existing = load_state()
        if existing and not existing.ended:
            overwrite = typer.confirm(
                "A game is already in progress. Start a new one?",
                default=False,
            )
            if not overwrite:
                console.print("[yellow]Keeping existing game.[/yellow]")
                raise typer.Exit(0)
    
    engine = Engine(incidents_path=incidents_path)
    state = engine.start_game()
    
    console.print("[bold green]🎮 New game started![/bold green]")
    console.print(f"Loaded [bold]{len(state.incidents)}[/bold] incident(s).")
    
    if state.incidents:
        console.print("\n[yellow]Use 'alert-alchemy status' to view incidents.[/yellow]")
    else:
        console.print("\n[dim]No incidents found. Add YAML files to the incidents directory.[/dim]")


@app.command()
def status() -> None:
    """Show current game status and incidents (does NOT advance time)."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    state = load_state()
    if state is None:
        render_no_state_message()
        raise typer.Exit(1)
    
    render_status(state)


@app.command()
def logs() -> None:
    """Show incident logs (does NOT advance time)."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    state = load_state()
    if state is None:
        render_no_state_message()
        raise typer.Exit(1)
    
    render_logs(state)


@app.command()
def metrics() -> None:
    """Show metrics table for all incidents (does NOT advance time)."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    state = load_state()
    if state is None:
        render_no_state_message()
        raise typer.Exit(1)
    
    render_metrics(state)


@app.command()
def traces() -> None:
    """Show traces for active incidents (does NOT advance time)."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    state = load_state()
    if state is None:
        render_no_state_message()
        raise typer.Exit(1)
    
    render_traces(state)


@app.command()
def action(
    incident_id: str = typer.Argument(..., help="ID of the incident to act on"),
    action_name: str = typer.Argument(..., help="Name of the action to take"),
) -> None:
    """Take an action on an incident (advances time +1)."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    engine = get_engine()
    
    if engine.state and engine.state.ended:
        console.print("[yellow]Game has ended. Use 'alert-alchemy reset' to start fresh.[/yellow]")
        raise typer.Exit(1)
    
    success, message = engine.take_action(incident_id, action_name)
    render_action_result(success, message)
    
    if success and engine.state:
        console.print(f"[dim]Step: {engine.state.current_step} | Score: {engine.state.score}[/dim]")


@app.command()
def tick() -> None:
    """Advance time by one step without taking an action (advances time +1)."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    engine = get_engine()
    
    if engine.state and engine.state.ended:
        console.print("[yellow]Game has ended. Use 'alert-alchemy reset' to start fresh.[/yellow]")
        raise typer.Exit(1)
    
    success, message = engine.tick()
    render_action_result(success, message)
    
    if success and engine.state:
        console.print(f"[dim]Score: {engine.state.score}[/dim]")


@app.command()
def end() -> None:
    """End the current game and show final score."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    engine = get_engine()
    
    if engine.state and engine.state.ended:
        console.print("[yellow]Game has already ended.[/yellow]")
        render_game_end(engine.state)
        raise typer.Exit(0)
    
    success, message = engine.end_game()
    
    if success and engine.state:
        render_game_end(engine.state)
    else:
        console.print(f"[red]{message}[/red]")


@app.command()
def reset(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Reset/clear the current game state."""
    if not state_exists():
        console.print("[dim]No game state to reset.[/dim]")
        raise typer.Exit(0)
    
    if not force:
        confirm = typer.confirm("Are you sure you want to reset the game?", default=False)
        if not confirm:
            console.print("[yellow]Reset cancelled.[/yellow]")
            raise typer.Exit(0)
    
    engine = get_engine()
    success, message = engine.reset_game()
    
    console.print(f"[green]{message}[/green]")


@app.command()
def show(
    incident_id: str = typer.Argument(..., help="ID of the incident to show"),
) -> None:
    """Show detailed information about a specific incident."""
    if not state_exists():
        render_no_state_message()
        raise typer.Exit(1)
    
    state = load_state()
    if state is None:
        render_no_state_message()
        raise typer.Exit(1)
    
    for incident in state.incidents:
        if incident.id == incident_id:
            render_incident_detail(incident)
            return
    
    console.print(f"[red]Incident '{incident_id}' not found.[/red]")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
