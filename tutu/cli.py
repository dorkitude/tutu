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

from .models import get_session, TutuItem, TutuItemStep

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
def list():
    """List all TutuItems that aren't done"""
    session = get_session()
    
    items = session.query(TutuItem).filter(
        TutuItem.status != 'done'
    ).order_by(TutuItem.updated_at.desc()).all()
    
    if not items:
        console.print("🎉 [yellow]No pending items![/yellow]")
        return
    
    table = Table(title="📋 Tutu Items", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Steps", style="green", justify="center")
    table.add_column("Updated", style="blue")
    
    for item in items:
        steps_count = len(item.steps)
        completed_steps = sum(1 for step in item.steps if step.status == 'done')
        steps_info = f"{completed_steps}/{steps_count}"
        
        updated = item.updated_at.strftime("%Y-%m-%d %H:%M")
        
        table.add_row(
            str(item.id),
            item.title,
            item.status,
            steps_info,
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
    
    console.print(f"\n🔍 [bold cyan]TutuItem #{item.id}[/bold cyan]\n")
    console.print(f"[bold]Title:[/bold] {item.title}")
    console.print(f"[bold]Status:[/bold] {item.status}")
    console.print(f"[bold]Created:[/bold] {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"[bold]Updated:[/bold] {item.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if item.first_progress_at:
        console.print(f"[bold]First Progress:[/bold] {item.first_progress_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if item.description:
        console.print(f"\n[bold]Description:[/bold]\n{item.description}")
    
    if item.context:
        console.print(f"\n[bold]Context:[/bold]\n{item.context}")
    
    if item.steps:
        console.print(f"\n[bold]Steps:[/bold]")
        steps_table = Table(show_header=True, header_style="bold")
        steps_table.add_column("ID", style="cyan", width=6)
        steps_table.add_column("Description", style="white")
        steps_table.add_column("Status", style="yellow")
        steps_table.add_column("Created", style="blue")
        
        for step in item.steps:
            steps_table.add_row(
                str(step.id),
                step.description,
                step.status,
                step.created_at.strftime("%Y-%m-%d %H:%M")
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
        item.first_progress_at = datetime.utcnow()
    
    session.commit()
    
    console.print(f"🚀 [bold green]Starting Claude Code session for TutuItem #{item.id}[/bold green]\n")
    
    # Read README.md
    readme_path = Path(__file__).parent.parent / "README.md"
    readme_content = ""
    if readme_path.exists():
        readme_content = readme_path.read_text()
    
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
    
    context += f"\n---\n\n{readme_content}"
    
    # Start Claude Code with the context
    cmd = ["/opt/homebrew/bin/claude", "--dangerously-skip-permissions"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            text=True,
            cwd=original_cwd  # Explicitly set the working directory
        )
        
        # Send the context to Claude Code
        process.communicate(input=context)
        
    except Exception as e:
        console.print(f"❌ [red]Error starting Claude Code: {e}[/red]")

@app.command()
def add_step(item_id: int, description: str):
    """Add a step to a TutuItem"""
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
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

def main():
    app()

if __name__ == "__main__":
    main()