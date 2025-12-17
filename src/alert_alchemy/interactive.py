"""Interactive play mode for Alert Alchemy.

Provides a guided, menu-driven interface for non-developer users.
"""

import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from alert_alchemy.engine import Engine
from alert_alchemy.models import GameState, Incident
from alert_alchemy.render import (
    console,
    render_action_result,
    render_game_end,
    render_incident_detail,
    render_logs,
    render_metrics,
    render_status,
    render_traces,
)
from alert_alchemy.scoring import calculate_blast_radius
from alert_alchemy.state import load_state, state_exists


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def get_active_incidents(state: GameState) -> list[Incident]:
    """Get list of active (unresolved) incidents."""
    return [inc for inc in state.incidents if not inc.resolved]


def get_incident_by_highest_blast_radius(incidents: list[Incident]) -> Optional[Incident]:
    """Get the incident with the highest blast radius."""
    if not incidents:
        return None
    return max(incidents, key=lambda inc: calculate_blast_radius(inc))


def render_compact_dashboard(state: GameState) -> None:
    """Render a compact dashboard showing game state."""
    active = get_active_incidents(state)
    resolved = len(state.incidents) - len(active)
    
    # Header info
    header = f"📊 Step: [bold cyan]{state.current_step}[/] | Score: [bold {'green' if state.score >= 50 else 'red'}]{state.score}[/] | Resolved: [bold]{resolved}/{len(state.incidents)}[/]"
    
    # Active incidents table
    if active:
        table = Table(title="🔥 Active Incidents", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Severity", justify="center")
        table.add_column("Blast", justify="center")
        
        for i, inc in enumerate(active, 1):
            blast = calculate_blast_radius(inc)
            sev_color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "green"}.get(inc.severity.lower(), "white")
            blast_color = "red" if blast >= 70 else ("yellow" if blast >= 40 else "green")
            table.add_row(
                str(i),
                inc.id,
                inc.title[:40] + ("..." if len(inc.title) > 40 else ""),
                f"[{sev_color}]{inc.severity}[/]",
                f"[{blast_color}]{blast}[/]",
            )
        
        console.print(Panel(header, border_style="blue"))
        console.print(table)
    else:
        console.print(Panel(header + "\n\n[green]✨ All incidents resolved![/]", border_style="green"))


def render_menu() -> None:
    """Render the main menu options."""
    menu = """
[bold]Choose an action:[/]
  [cyan]1[/]) status     - View all incidents
  [cyan]2[/]) logs       - View incident logs
  [cyan]3[/]) metrics    - View metrics table
  [cyan]4[/]) traces     - View distributed traces
  [cyan]5[/]) show       - Show incident details
  [cyan]6[/]) action     - Take an action on an incident
  [cyan]7[/]) tick       - Advance time (+1 step)
  [cyan]8[/]) end        - End game and see score
  [cyan]9[/]) reset      - Reset game state
  [dim]0[/]) exit       - Exit play mode
"""
    console.print(menu)


def select_incident(state: GameState, prompt_text: str = "Select incident") -> Optional[Incident]:
    """Prompt user to select an incident from active incidents."""
    active = get_active_incidents(state)
    
    if not active:
        console.print("[yellow]No active incidents.[/]")
        return None
    
    if len(active) == 1:
        console.print(f"[dim]Auto-selected: {active[0].id}[/]")
        return active[0]
    
    # Show numbered list
    console.print(f"\n[bold]{prompt_text}:[/]")
    default_inc = get_incident_by_highest_blast_radius(active)
    
    for i, inc in enumerate(active, 1):
        blast = calculate_blast_radius(inc)
        is_default = inc == default_inc
        marker = " [yellow](highest blast)[/]" if is_default else ""
        console.print(f"  [cyan]{i}[/]) {inc.id}: {inc.title[:35]}{marker}")
    
    default_idx = active.index(default_inc) + 1 if default_inc else 1
    
    try:
        choice = IntPrompt.ask("Enter number", default=default_idx)
        if 1 <= choice <= len(active):
            return active[choice - 1]
        console.print("[red]Invalid selection.[/]")
        return None
    except (KeyboardInterrupt, EOFError):
        return None


def select_action(incident: Incident) -> Optional[str]:
    """Prompt user to select an action for an incident."""
    actions = incident.available_actions
    
    if not actions:
        console.print("[yellow]No actions available for this incident.[/]")
        return None
    
    console.print(f"\n[bold]Available actions for {incident.id}:[/]")
    for i, action in enumerate(actions, 1):
        console.print(f"  [cyan]{i}[/]) {action}")
    
    try:
        choice = IntPrompt.ask("Enter number", default=1)
        if 1 <= choice <= len(actions):
            return actions[choice - 1]
        console.print("[red]Invalid selection.[/]")
        return None
    except (KeyboardInterrupt, EOFError):
        return None


def handle_action_command(engine: Engine) -> None:
    """Handle the action command in interactive mode."""
    state = engine.state
    if not state:
        console.print("[red]No active game.[/]")
        return
    
    incident = select_incident(state, "Which incident to act on?")
    if not incident:
        return
    
    action = select_action(incident)
    if not action:
        return
    
    success, message = engine.take_action(incident.id, action)
    render_action_result(success, message)
    
    if success and engine.state:
        console.print(f"[dim]Step: {engine.state.current_step} | Score: {engine.state.score}[/]")
        console.print("\n[dim]💡 Tip: Use 'status' or 'metrics' to check the situation.[/]")


def handle_show_command(state: GameState) -> None:
    """Handle the show command in interactive mode."""
    active = get_active_incidents(state)
    
    if not active:
        console.print("[yellow]No active incidents to show.[/]")
        return
    
    incident = select_incident(state, "Which incident to view?")
    if incident:
        render_incident_detail(incident)


def interactive_play_loop() -> None:
    """Main interactive play loop."""
    if not is_interactive():
        console.print("[red]Interactive mode requires a terminal.[/]")
        console.print("[dim]Use individual commands instead: alert-alchemy status, action, etc.[/]")
        return
    
    if not state_exists():
        console.print("[yellow]No game in progress. Starting a new game...[/]")
        engine = Engine()
        state = engine.start_game()
        console.print(f"[green]🎮 New game started! Loaded {len(state.incidents)} incident(s).[/]\n")
    
    engine = Engine()
    
    console.print("[bold cyan]═══════════════════════════════════════[/]")
    console.print("[bold cyan]  🧪 Alert Alchemy - Interactive Mode  [/]")
    console.print("[bold cyan]═══════════════════════════════════════[/]\n")
    
    while True:
        state = load_state()
        if not state:
            console.print("[red]Game state lost. Please restart.[/]")
            break
        
        if state.ended:
            console.print("[yellow]Game has ended.[/]")
            render_game_end(state)
            break
        
        render_compact_dashboard(state)
        render_menu()
        
        try:
            choice = Prompt.ask("Your choice", default="1")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting play mode.[/]")
            break
        
        console.print()  # Blank line
        
        # Reload state and engine for each action
        engine = Engine()
        state = load_state()
        if not state:
            break
        
        if choice == "1":
            render_status(state)
        elif choice == "2":
            render_logs(state)
        elif choice == "3":
            render_metrics(state)
        elif choice == "4":
            render_traces(state)
        elif choice == "5":
            handle_show_command(state)
        elif choice == "6":
            handle_action_command(engine)
        elif choice == "7":
            success, message = engine.tick()
            render_action_result(success, message)
            if success and engine.state:
                console.print(f"[dim]Score: {engine.state.score}[/]")
        elif choice == "8":
            success, message = engine.end_game()
            if success and engine.state:
                render_game_end(engine.state)
            else:
                console.print(f"[red]{message}[/]")
            break
        elif choice == "9":
            if Confirm.ask("Are you sure you want to reset?", default=False):
                engine.reset_game()
                console.print("[green]Game reset.[/]")
                break
        elif choice == "0":
            console.print("[dim]Exiting play mode. Game state preserved.[/]")
            break
        else:
            console.print("[yellow]Invalid choice. Try again.[/]")
        
        console.print()  # Blank line between iterations


def render_actions_list(state: GameState, incident_id: Optional[str] = None) -> None:
    """Render available actions for incidents."""
    incidents = state.incidents
    
    if incident_id:
        incidents = [inc for inc in incidents if inc.id == incident_id]
        if not incidents:
            console.print(f"[red]Incident '{incident_id}' not found.[/]")
            return
    
    table = Table(title="📋 Available Actions", show_header=True, header_style="bold magenta")
    table.add_column("Incident", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Blast", justify="center", width=6)
    table.add_column("Available Actions", style="white")
    
    for inc in incidents:
        blast = calculate_blast_radius(inc)
        status = "[green]✓ Resolved[/]" if inc.resolved else "[yellow]Active[/]"
        blast_color = "red" if blast >= 70 else ("yellow" if blast >= 40 else "green")
        actions_str = ", ".join(inc.available_actions) if inc.available_actions else "[dim]None[/]"
        
        table.add_row(
            f"{inc.id}\n[dim]{inc.title[:25]}...[/]" if len(inc.title) > 25 else f"{inc.id}\n[dim]{inc.title}[/]",
            status,
            f"[{blast_color}]{blast}[/]",
            actions_str,
        )
    
    console.print(table)


def smart_action(
    action_name: Optional[str],
    incident_id: Optional[str],
    engine: Engine,
) -> tuple[bool, str]:
    """Handle smart action with optional incident ID.
    
    Returns:
        Tuple of (success, message).
    """
    state = engine.state
    if not state:
        return False, "No active game. Run 'alert-alchemy start' first."
    
    if state.ended:
        return False, "Game has already ended."
    
    active = get_active_incidents(state)
    if not active:
        return False, "No active incidents to act on."
    
    # Determine target incident
    target_incident: Optional[Incident] = None
    
    if incident_id:
        # Explicit incident ID provided
        for inc in active:
            if inc.id == incident_id:
                target_incident = inc
                break
        if not target_incident:
            return False, f"Incident '{incident_id}' not found or already resolved."
    else:
        # No incident ID - auto-select or prompt
        if len(active) == 1:
            target_incident = active[0]
            console.print(f"[dim]→ Auto-selected incident: {target_incident.id}[/]")
        else:
            # Need interactive selection
            if not is_interactive():
                return False, (
                    f"Multiple active incidents. Please specify incident ID.\n"
                    f"Active: {', '.join(inc.id for inc in active)}\n"
                    f"Example: alert-alchemy action {active[0].id} {action_name or '<action>'}"
                )
            
            target_incident = select_incident(state, "Select incident")
            if not target_incident:
                return False, "No incident selected."
    
    # Determine action
    if not action_name:
        if not is_interactive():
            actions_str = ", ".join(target_incident.available_actions)
            return False, (
                f"Please specify an action.\n"
                f"Available for {target_incident.id}: {actions_str}\n"
                f"Example: alert-alchemy action {target_incident.id} {target_incident.available_actions[0] if target_incident.available_actions else '<action>'}"
            )
        
        action_name = select_action(target_incident)
        if not action_name:
            return False, "No action selected."
    
    # Take the action
    success, message = engine.take_action(target_incident.id, action_name)
    
    return success, message
