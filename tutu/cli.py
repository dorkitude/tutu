import typer
from typing import Optional
from datetime import datetime
import subprocess
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from .models import get_session, TutuItem, TutuItemStep, get_pacific_now
from .utils import format_relative_time

app = typer.Typer()
console = Console()

@app.command()
def add():
    """Add a new TutuItem interactively"""
    session = get_session()
    
    console.print("\n✨ [bold cyan]Creating a new TutuItem[/bold cyan] ✨\n")
    
    title = Prompt.ask("📝 Title")
    console.print("📄 Description (press Ctrl+D when done):")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    description = "\n".join(lines)
    
    console.print("\n🌟 Context (press Ctrl+D when done):")
    
    context_lines = []
    try:
        while True:
            line = input()
            context_lines.append(line)
    except EOFError:
        pass
    
    context = "\n".join(context_lines)
    
    item = TutuItem(
        title=title,
        description=description,
        context=context,
        status='pending'
    )
    
    session.add(item)
    session.commit()
    
    console.print(f"\n✅ [bold green]TutuItem created with ID: {item.id}[/bold green]")
    console.print(f"\n[bold]Title:[/bold] {item.title}")
    console.print(f"[bold]Description:[/bold]\n{item.description}")
    if item.context:
        console.print(f"[bold]Context:[/bold]\n{item.context}")

@app.command()
def list(all: bool = typer.Option(False, "--all", help="Show all items including completed ones")):
    """List all TutuItems (by default, only shows pending items)"""
    session = get_session()
    
    if all:
        items = session.query(TutuItem).order_by(TutuItem.updated_at.desc()).all()
    else:
        items = session.query(TutuItem).filter(
            TutuItem.status != 'done'
        ).order_by(TutuItem.updated_at.desc()).all()
    
    if not items:
        if all:
            console.print("📭 [yellow]No items found![/yellow]")
        else:
            console.print("🎉 [yellow]No pending items![/yellow]")
        return
    
    title = "📋 All Tutu Items" if all else "📋 Pending Tutu Items"
    table = Table(title=title, show_header=True, header_style="bold magenta", expand=False)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Title", style="white", max_width=40, no_wrap=True, overflow="ellipsis")
    table.add_column("Status", style="yellow", width=7)
    table.add_column("Steps", style="green", justify="center", width=6)
    table.add_column("Created", style="blue", no_wrap=True, width=30)
    table.add_column("Updated", style="blue", no_wrap=True, width=30)
    
    for item in items:
        steps_count = len(item.steps)
        completed_steps = sum(1 for step in item.steps if step.status == 'done')
        steps_info = f"{completed_steps}/{steps_count}"
        
        created_relative = format_relative_time(item.created_at)
        updated_relative = format_relative_time(item.updated_at)
        created = f"{created_relative} • {item.created_at.strftime('%m/%d %H:%M')}"
        updated = f"{updated_relative} • {item.updated_at.strftime('%m/%d %H:%M')}"
        
        table.add_row(
            str(item.id),
            item.title,
            item.status,
            steps_info,
            created,
            updated
        )
    
    console.print(table)

@app.command()
def status(item_id: int):
    """Show full status report for a TutuItem"""
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    # Create a cute header with sparkles
    header = Text()
    header.append("✨ ", style="bright_yellow")
    header.append(f"TUTU STATUS infodump.   Full deets inbound.", style="bold bright_white")
    header.append(" ✨", style="bright_yellow")
    console.print(Panel(header, border_style="bright_yellow", padding=(0, 2)))
    console.print()
    
    # Title section with cute box
    title_text = Text()
    title_text.append("🎯 ", style="bright_cyan")
    title_text.append(f"TutuItem #{item.id}: ", style="bold bright_cyan")
    title_text.append(item.title, style="bold bright_white")
    console.print(Panel(title_text, border_style="cyan", padding=(0, 1)))
    console.print()
    
    # Status info table
    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("Label", style="bold", no_wrap=True)
    status_table.add_column("Value", style="bright_white")
    
    # Status badge with emoji
    status_emoji = "🚀" if item.status == "in_progress" else "✅" if item.status == "completed" else "📋"
    status_color = "yellow" if item.status == "in_progress" else "green" if item.status == "completed" else "blue"
    status_table.add_row(
        f"{status_emoji} Status:",
        f"[{status_color}]{item.status}[/{status_color}]"
    )
    
    # Time information with relative times
    created_relative = format_relative_time(item.created_at)
    updated_relative = format_relative_time(item.updated_at)
    
    status_table.add_row(
        "🕐 Created:",
        f"[dim]{created_relative}[/dim] • [bright_blue]{item.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/bright_blue]"
    )
    
    status_table.add_row(
        "🕑 Updated:",
        f"[dim]{updated_relative}[/dim] • [bright_blue]{item.updated_at.strftime('%Y-%m-%d %H:%M:%S')}[/bright_blue]"
    )
    
    if item.first_progress_at:
        progress_relative = format_relative_time(item.first_progress_at)
        status_table.add_row(
            "🏁 First Progress:",
            f"[dim]{progress_relative}[/dim] • [bright_green]{item.first_progress_at.strftime('%Y-%m-%d %H:%M:%S')}[/bright_green]"
        )
    
    console.print(status_table)
    
    # Description section with cute formatting
    if item.description:
        console.print()
        desc_panel = Panel(
            item.description,
            title="📝 Description",
            title_align="left",
            border_style="bright_magenta",
            padding=(1, 2)
        )
        console.print(desc_panel)
    
    # Context section with cute formatting
    if item.context:
        console.print()
        context_panel = Panel(
            item.context,
            title="🌟 Context",
            title_align="left",
            border_style="bright_yellow",
            padding=(1, 2)
        )
        console.print(context_panel)
    
    if item.steps:
        console.print()
        console.print("📝 [bold]Steps:[/bold]")
        steps_table = Table(show_header=True, header_style="bold magenta", expand=False)
        steps_table.add_column("ID", style="cyan", width=4)
        steps_table.add_column("Description", style="white", max_width=50)
        steps_table.add_column("Status", style="yellow", width=8)
        steps_table.add_column("Created", style="blue", no_wrap=True)
        steps_table.add_column("Updated", style="blue", no_wrap=True)
        
        for step in item.steps:
            created_relative = format_relative_time(step.created_at)
            updated_relative = format_relative_time(step.updated_at)
            
            # Status emoji
            step_emoji = "✅" if step.status == "done" else "⏳"
            status_display = f"{step_emoji} {step.status}"
            
            steps_table.add_row(
                str(step.id),
                step.description,
                status_display,
                f"{created_relative} • {step.created_at.strftime('%m/%d %H:%M')}",
                f"{updated_relative} • {step.updated_at.strftime('%m/%d %H:%M')}"
            )
        
        console.print(steps_table)
    else:
        console.print("\n[yellow]No steps yet![/yellow]")

@app.command()
def start(item_id: int):
    """Start a Claude Code session with TutuItem context"""
    # Capture the current working directory before any operations
    original_cwd = os.getcwd()
    
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    # Update status and first_progress_at
    item.status = 'in_progress'
    if not item.first_progress_at:
        item.first_progress_at = get_pacific_now()
    
    session.commit()
    
    console.print(f"🚀 [bold green]Starting Claude Code session for TutuItem #{item.id}[/bold green]\n")
    
    # Read README.md
    readme_path = Path(__file__).parent.parent / "README.md"
    readme_content = ""
    if readme_path.exists():
        readme_content = readme_path.read_text()
    
    # Read TUTU_START_PROMPT.md
    tutu_prompt_path = Path(__file__).parent.parent / "TUTU_START_PROMPT.md"
    tutu_prompt_content = ""
    if tutu_prompt_path.exists():
        tutu_prompt_content = tutu_prompt_path.read_text()
    
    # Prepare context for Claude Code
    context = f"""# TutuItem #{item.id}: {item.title}

## Status: {item.status}

## Description:
{item.description}

## Context:
{item.context}

## Steps:
"""
    
    for step in item.steps:
        context += f"- [{step.status}] Step #{step.id}: {step.description}\n"
    
    if not item.steps:
        context += "No steps defined yet.\n"
    
    context += f"\n---\n<README>\n{readme_content}\n</README>\n\n---\n{tutu_prompt_content}\n"
    
    # Start Claude Code with the context using cly function
    # First, source the daemon-wrappers script and then run cly
    cmd = [
        "/bin/zsh",
        "-c",
        f"source /Users/dorkitude/a/scripts/daemon-wrappers.zsh && cly"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            text=True,
            cwd=original_cwd,  # Explicitly set the working directory
            env={**os.environ}  # Pass environment variables
        )
        
        # Send the context to Claude Code
        process.communicate(input=context)
        
    except Exception as e:
        console.print(f"❌ [red]Error starting Claude Code: {e}[/red]")

@app.command()
def add_step(item_id: int, description: Optional[str] = None):
    """Add a step to a TutuItem"""
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    # Interactive mode if no description provided
    if description is None:
        console.print(f"\n📝 [bold cyan]Adding step to TutuItem #{item_id}: {item.title}[/bold cyan]\n")
        console.print("📄 Step description (press Ctrl+D when done):")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        description = "\n".join(lines).strip()
        
        if not description:
            console.print("❌ [red]Step description cannot be empty[/red]")
            return
    
    step = TutuItemStep(
        item_id=item_id,
        description=description,
        status='pending'
    )
    
    session.add(step)
    session.commit()
    
    console.print(f"✅ [green]Step added with ID: {step.id}[/green]")

@app.command()
def complete_step(step_id: int):
    """Mark a TutuItemStep as done"""
    session = get_session()
    
    step = session.query(TutuItemStep).filter(TutuItemStep.id == step_id).first()
    
    if not step:
        console.print(f"❌ [red]Step with ID {step_id} not found[/red]")
        return
    
    step.status = 'done'
    session.commit()
    
    console.print(f"✅ [green]Step #{step_id} marked as done[/green]")

@app.command()
def done(item_id: int):
    """Mark a TutuItem as done"""
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    item.status = 'done'
    session.commit()
    
    console.print(f"✅ [green]TutuItem #{item_id} marked as done![/green] 🎉")

@app.command()
def edit(item_id: int):
    """Edit a TutuItem interactively"""
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    console.print(f"\n✏️  [bold cyan]Editing TutuItem #{item.id}[/bold cyan] ✏️\n")
    
    # Show current values
    console.print(f"[dim]Current title:[/dim] {item.title}")
    new_title = Prompt.ask("📝 New title (press Enter to keep current)", default=item.title)
    
    console.print(f"\n[dim]Current description:[/dim]\n{item.description}")
    console.print("\n📄 New description (press Ctrl+D when done, or just Ctrl+D to keep current):")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    new_description = "\n".join(lines) if lines else item.description
    
    console.print(f"\n[dim]Current context:[/dim]\n{item.context if item.context else '(empty)'}")
    console.print("\n🌟 New context (press Ctrl+D when done, or just Ctrl+D to keep current):")
    
    context_lines = []
    try:
        while True:
            line = input()
            context_lines.append(line)
    except EOFError:
        pass
    
    new_context = "\n".join(context_lines) if context_lines else item.context
    
    # Update the item
    item.title = new_title
    item.description = new_description
    item.context = new_context
    
    session.commit()
    
    console.print(f"\n✅ [bold green]TutuItem #{item.id} updated successfully![/bold green]")
    console.print(f"\n[bold]Title:[/bold] {item.title}")
    console.print(f"[bold]Description:[/bold]\n{item.description}")
    if item.context:
        console.print(f"[bold]Context:[/bold]\n{item.context}")

def main():
    import sys
    
    # If no arguments provided (just 'tutu'), default to list command
    if len(sys.argv) == 1:
        sys.argv.append("list")
    
    app()

if __name__ == "__main__":
    main()