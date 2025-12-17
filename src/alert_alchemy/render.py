"""Rich console rendering utilities for Alert Alchemy."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from alert_alchemy.models import GameState, Incident
from alert_alchemy.scoring import calculate_blast_radius, get_score_breakdown

console = Console()


def get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        "critical": "red",
        "high": "orange1",
        "medium": "yellow",
        "low": "green",
    }
    return colors.get(severity.lower(), "white")


def render_status(state: GameState) -> None:
    """Render the current game status."""
    console.print()
    console.print(Panel(
        f"[bold cyan]Alert Alchemy[/bold cyan] - Step [bold]{state.current_step}[/bold]",
        subtitle=f"Score: {state.score}",
    ))
    
    if state.ended:
        console.print("[yellow]Game has ended.[/yellow]")
        return
    
    active_incidents = [inc for inc in state.incidents if not inc.resolved]
    resolved_incidents = [inc for inc in state.incidents if inc.resolved]
    
    if not active_incidents:
        console.print("[green]No active incidents. All clear![/green]")
    else:
        console.print(f"\n[bold red]Active Incidents: {len(active_incidents)}[/bold red]")
        for incident in active_incidents:
            render_incident_summary(incident)
    
    if resolved_incidents:
        console.print(f"\n[bold green]Resolved: {len(resolved_incidents)}[/bold green]")


def render_incident_summary(incident: Incident) -> None:
    """Render a brief summary of an incident."""
    severity_color = get_severity_color(incident.severity)
    blast_radius = calculate_blast_radius(incident)
    
    console.print(Panel(
        f"[bold]{incident.title}[/bold]\n"
        f"{incident.description}\n\n"
        f"Blast Radius: [bold]{blast_radius}[/bold]/100",
        title=f"[{severity_color}]{incident.severity.upper()}[/{severity_color}] - {incident.id}",
        border_style=severity_color,
    ))


def render_incident_detail(incident: Incident) -> None:
    """Render detailed incident information."""
    severity_color = get_severity_color(incident.severity)
    blast_radius = calculate_blast_radius(incident)
    
    console.print(Panel(
        f"[bold]{incident.title}[/bold]\n\n"
        f"{incident.description}\n\n"
        f"Blast Radius: [bold]{blast_radius}[/bold]/100\n"
        f"Status: {'[green]Resolved[/green]' if incident.resolved else '[red]Active[/red]'}",
        title=f"[{severity_color}]{incident.severity.upper()}[/{severity_color}] - {incident.id}",
        border_style=severity_color,
    ))
    
    if incident.available_actions:
        console.print("\n[bold]Available Actions:[/bold]")
        for i, action in enumerate(incident.available_actions, 1):
            console.print(f"  {i}. {action}")


def render_logs(state: GameState) -> None:
    """Render logs for all active incidents."""
    console.print("\n[bold cyan]📋 Incident Logs[/bold cyan]\n")
    
    active_incidents = [inc for inc in state.incidents if not inc.resolved]
    
    if not active_incidents:
        console.print("[dim]No active incidents.[/dim]")
        return
    
    for incident in active_incidents:
        console.print(f"[bold]{incident.id}[/bold] - {incident.title}")
        if incident.logs:
            for log in incident.logs:
                console.print(f"  [dim]{log}[/dim]")
        else:
            console.print("  [dim]No logs available.[/dim]")
        console.print()


def render_metrics(state: GameState) -> None:
    """Render metrics table for all incidents."""
    console.print("\n[bold cyan]📊 Incident Metrics[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Incident")
    table.add_column("Error Rate", justify="right")
    table.add_column("P95 Latency", justify="right")
    table.add_column("CPU", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Blast Radius", justify="right")
    
    for incident in state.incidents:
        metrics = incident.metrics
        blast_radius = calculate_blast_radius(incident)
        
        table.add_row(
            incident.id,
            f"{metrics.error_rate:.1f}%" if metrics.error_rate is not None else "-",
            f"{metrics.p95_latency:.0f}ms" if metrics.p95_latency is not None else "-",
            f"{metrics.cpu_usage:.1f}%" if metrics.cpu_usage is not None else "-",
            f"{metrics.memory_usage:.1f}%" if metrics.memory_usage is not None else "-",
            f"{blast_radius}/100",
        )
    
    console.print(table)


def render_traces(state: GameState) -> None:
    """Render traces for all active incidents."""
    console.print("\n[bold cyan]🔍 Incident Traces[/bold cyan]\n")
    
    active_incidents = [inc for inc in state.incidents if not inc.resolved]
    
    if not active_incidents:
        console.print("[dim]No active incidents.[/dim]")
        return
    
    for incident in active_incidents:
        console.print(f"[bold]{incident.id}[/bold] - {incident.title}")
        if incident.traces:
            for trace in incident.traces:
                console.print(f"  [cyan]{trace}[/cyan]")
        else:
            console.print("  [dim]No traces available.[/dim]")
        console.print()


def render_score_breakdown(state: GameState) -> None:
    """Render detailed score breakdown."""
    breakdown = get_score_breakdown(state)
    
    console.print("\n[bold cyan]🏆 Score Breakdown[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Component")
    table.add_column("Points", justify="right")
    
    table.add_row("Base Score", f"+{breakdown['base']}")
    table.add_row("Time Penalty", str(breakdown['step_penalty']))
    table.add_row("Wrong Actions", str(breakdown['wrong_action_penalty']))
    table.add_row("Worsen Penalty", str(breakdown['worsen_penalty']))
    table.add_row("Quick Resolve Bonus", f"+{breakdown['quick_resolve_bonus']}")
    table.add_row("[bold]Total[/bold]", f"[bold]{breakdown['total']}[/bold]")
    
    console.print(table)


def render_game_end(state: GameState) -> None:
    """Render game end summary."""
    console.print("\n")
    console.print(Panel(
        "[bold]🎮 Game Over![/bold]",
        style="bold cyan",
    ))
    
    resolved = len([inc for inc in state.incidents if inc.resolved])
    total = len(state.incidents)
    
    console.print(f"\nIncidents Resolved: [bold]{resolved}/{total}[/bold]")
    console.print(f"Total Steps: [bold]{state.current_step}[/bold]")
    console.print(f"Actions Taken: [bold]{len(state.actions_taken)}[/bold]")
    
    render_score_breakdown(state)


def render_no_state_message() -> None:
    """Render message when no game state exists."""
    console.print(Panel(
        "[yellow]No active game found.[/yellow]\n\n"
        "Run [bold cyan]alert-alchemy start[/bold cyan] to begin a new game.",
        title="Alert Alchemy",
    ))


def render_action_result(success: bool, message: str) -> None:
    """Render the result of an action."""
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
