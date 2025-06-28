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
from rich import box
import tempfile
import webbrowser

from .models import get_session, TutuItem, TutuItemStep, get_pacific_now
from .utils import format_relative_time

app = typer.Typer()
console = Console()

@app.command()
def add():
    """Add a new TutuItem interactively"""
    session = get_session()
    
    # Capture the current working directory
    current_dir = os.getcwd()
    
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
        status='pending',
        working_directory=current_dir
    )
    
    session.add(item)
    session.commit()
    
    console.print(f"\n✅ [bold green]TutuItem created with ID: {item.id}[/bold green]")
    console.print(f"\n[bold]Title:[/bold] {item.title}")
    console.print(f"[bold]Description:[/bold]\n{item.description}")
    if item.context:
        console.print(f"[bold]Context:[/bold]\n{item.context}")

@app.command()
def list(
    all: bool = typer.Option(False, "--all", help="Show all items including completed ones"),
    everywhere: bool = typer.Option(False, "--everywhere", help="Show items from all directories, not just current"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed information including descriptions")
):
    """List all TutuItems (by default, only shows pending items)"""
    session = get_session()
    current_dir = os.path.abspath(os.getcwd())
    
    if all:
        items = session.query(TutuItem).order_by(TutuItem.updated_at.desc()).all()
    else:
        items = session.query(TutuItem).filter(
            TutuItem.status != 'done'
        ).order_by(TutuItem.updated_at.desc()).all()
    
    # Filter items to only show those within the current directory hierarchy (unless --everywhere is used)
    if not everywhere:
        filtered_items = []
        for item in items:
            if item.working_directory:
                item_dir = os.path.abspath(item.working_directory)
                # Check if the item's directory is within the current directory or its subdirectories
                if item_dir.startswith(current_dir + os.sep) or item_dir == current_dir:
                    filtered_items.append(item)
        
        items = filtered_items
    
    if not items:
        if everywhere:
            if all:
                console.print(f"📭 [yellow]No items found anywhere![/yellow]")
            else:
                console.print(f"🎉 [yellow]No pending items found anywhere![/yellow]")
        else:
            if all:
                console.print(f"📭 [yellow]No items found in {current_dir} or its subdirectories![/yellow]")
            else:
                console.print(f"🎉 [yellow]No pending items in {current_dir} or its subdirectories![/yellow]")
        return
    
    title = "📋 All Tutu Items" if all else "📋 Pending Tutu Items"
    if everywhere:
        title += " (Everywhere)"
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=3)
    table.add_column("Title", style="white", max_width=30)
    table.add_column("Working Directory", style="dim white", no_wrap=False)
    if verbose:
        table.add_column("Description", style="bright_white", max_width=40, no_wrap=False)
    table.add_column("Status", style="yellow", width=7)
    table.add_column("Steps", style="green", justify="center", width=5)
    table.add_column("Created", style="blue", no_wrap=True, width=10)
    table.add_column("Updated", style="blue", no_wrap=True, width=10)
    
    for item in items:
        steps_count = len(item.steps)
        completed_steps = sum(1 for step in item.steps if step.status == 'done')
        steps_info = f"{completed_steps}/{steps_count}"
        
        # Shorter date format to fit in narrow columns
        created = item.created_at.strftime('%m/%d %H:%M')
        updated = item.updated_at.strftime('%m/%d %H:%M')
        
        # Show full working directory path
        working_dir = item.working_directory or "N/A"
        
        # Show description, truncated if needed
        description = item.description or ""
        
        # Build row data based on verbose flag
        row_data = [
            str(item.id),
            item.title,
            working_dir
        ]
        
        if verbose:
            row_data.append(description)
        
        row_data.extend([
            item.status,
            steps_info,
            created,
            updated
        ])
        
        table.add_row(*row_data)
    
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
    
    # Status info table - now using a proper table with borders
    status_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    status_table.add_column("Field", style="bold", no_wrap=True)
    status_table.add_column("Value", style="bright_white")
    
    # Status badge with emoji
    status_emoji = "🚀" if item.status == "in_progress" else "✅" if item.status == "completed" else "📋"
    status_color = "yellow" if item.status == "in_progress" else "green" if item.status == "completed" else "blue"
    status_table.add_row(
        f"{status_emoji} Status",
        f"[{status_color}]{item.status}[/{status_color}]"
    )
    
    # Time information with relative times
    created_relative = format_relative_time(item.created_at)
    updated_relative = format_relative_time(item.updated_at)
    
    status_table.add_row(
        "🕐 Created",
        f"[dim]{created_relative}[/dim] • [bright_blue]{item.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/bright_blue]"
    )
    
    status_table.add_row(
        "🕑 Updated",
        f"[dim]{updated_relative}[/dim] • [bright_blue]{item.updated_at.strftime('%Y-%m-%d %H:%M:%S')}[/bright_blue]"
    )
    
    if item.first_progress_at:
        progress_relative = format_relative_time(item.first_progress_at)
        status_table.add_row(
            "🏁 First Progress",
            f"[dim]{progress_relative}[/dim] • [bright_green]{item.first_progress_at.strftime('%Y-%m-%d %H:%M:%S')}[/bright_green]"
        )
    
    if item.working_directory:
        status_table.add_row(
            "📂 Working Directory",
            f"[bright_cyan]{item.working_directory}[/bright_cyan]"
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
        console.print("📝 [bold]TutuItemSteps:[/bold]")
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
    session = get_session()
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    # Use the item's working directory if available, otherwise use current directory
    working_dir = item.working_directory if item.working_directory else os.getcwd()
    
    # Update status and first_progress_at
    item.status = 'in_progress'
    if not item.first_progress_at:
        item.first_progress_at = get_pacific_now()
    
    session.commit()
    
    console.print(f"🚀 [bold green]Starting Claude Code session for TutuItem #{item.id}[/bold green]\n")
    
    if working_dir != os.getcwd():
        console.print(f"📂 [cyan]Changing to working directory: {working_dir}[/cyan]\n")
    
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

## Working Directory: {working_dir}

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
    # First, cd to working directory, then source the daemon-wrappers script and run cly
    cmd = [
        "/bin/zsh",
        "-c",
        f"cd '{working_dir}' && source /Users/dorkitude/a/scripts/daemon-wrappers.zsh && cly"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            text=True,
            cwd=working_dir,  # Use the item's working directory
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

@app.command(name="import")
def import_item(item_id: int):
    """Import a TutuItem by changing its working directory to the current directory"""
    session = get_session()
    current_dir = os.path.abspath(os.getcwd())
    
    item = session.query(TutuItem).filter(TutuItem.id == item_id).first()
    
    if not item:
        console.print(f"❌ [red]TutuItem with ID {item_id} not found[/red]")
        return
    
    # Store the old directory for display
    old_dir = item.working_directory or "(not set)"
    
    # Update the working directory
    item.working_directory = current_dir
    session.commit()
    
    console.print(f"\n✨ [bold green]Successfully imported TutuItem #{item.id}![/bold green]")
    console.print(f"[bold]Title:[/bold] {item.title}")
    console.print(f"[bold]Previous directory:[/bold] {old_dir}")
    console.print(f"[bold]New directory:[/bold] {current_dir}")

@app.command(name="start-all")
def start_all(
    everywhere: bool = typer.Option(False, "--everywhere", help="Process items from all directories, not just current")
):
    """Run all pending TutuItems in batch mode and generate HTML report"""
    session = get_session()
    current_dir = os.path.abspath(os.getcwd())
    
    # Get all pending items
    pending_items = session.query(TutuItem).filter(
        TutuItem.status.in_(['pending', 'in_progress'])
    ).order_by(TutuItem.created_at).all()
    
    # Filter items to only process those within the current directory hierarchy (unless --everywhere is used)
    if not everywhere:
        filtered_items = []
        for item in pending_items:
            if item.working_directory:
                item_dir = os.path.abspath(item.working_directory)
                # Check if the item's directory is within the current directory or its subdirectories
                if item_dir.startswith(current_dir + os.sep) or item_dir == current_dir:
                    filtered_items.append(item)
        
        pending_items = filtered_items
    
    if not pending_items:
        if everywhere:
            console.print(f"✨ [yellow]No pending TutuItems to process anywhere![/yellow]")
        else:
            console.print(f"✨ [yellow]No pending TutuItems to process in {current_dir} or its subdirectories![/yellow]")
        return
    
    console.print(f"🚀 [bold cyan]Starting batch processing of {len(pending_items)} items[/bold cyan]\n")
    
    # Read TUTU_START_ALL_COMMAND.md
    tutu_batch_prompt_path = Path(__file__).parent.parent / "TUTU_START_ALL_COMMAND.md"
    tutu_batch_prompt_content = ""
    if tutu_batch_prompt_path.exists():
        tutu_batch_prompt_content = tutu_batch_prompt_path.read_text()
    
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
    
    results = []
    
    for idx, item in enumerate(pending_items, 1):
        console.print(f"\n{'='*60}")
        console.print(f"[bold]Processing item {idx}/{len(pending_items)}: #{item.id} - {item.title}[/bold]")
        console.print(f"{'='*60}\n")
        
        # Update status and first_progress_at
        item.status = 'in_progress'
        if not item.first_progress_at:
            item.first_progress_at = get_pacific_now()
        session.commit()
        
        # Use the item's working directory
        working_dir = item.working_directory if item.working_directory else os.getcwd()
        
        # Prepare context for Claude Code
        context = f"""# TutuItem #{item.id}: {item.title}

## Status: {item.status}

## Working Directory: {working_dir}

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
        
        context += f"\n---\n<README>\n{readme_content}\n</README>\n\n---\n{tutu_prompt_content}\n\n---\n{tutu_batch_prompt_content}\n"
        
        # Run Claude Code in non-interactive mode
        # First cd to working directory
        cmd = [
            "/bin/zsh",
            "-c",
            f"cd '{working_dir}' && source /Users/dorkitude/a/scripts/daemon-wrappers.zsh && claude -p --dangerously-skip-permissions"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir,
                env={**os.environ}
            )
            
            # Send the context and get output
            stdout, stderr = process.communicate(input=context)
            
            # Refresh item from database to get latest status
            session.refresh(item)
            
            result = {
                'item': item,
                'stdout': stdout,
                'stderr': stderr,
                'return_code': process.returncode,
                'steps_completed': [step for step in item.steps if step.status == 'done']
            }
            results.append(result)
            
            console.print(f"✅ [green]Completed processing item #{item.id}[/green]")
            
        except Exception as e:
            console.print(f"❌ [red]Error processing item #{item.id}: {e}[/red]")
            results.append({
                'item': item,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'steps_completed': []
            })
    
    # Generate HTML report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{timestamp}.html"
    report_path = Path(os.getcwd()) / report_filename
    
    html_content = generate_html_report(results, pending_items)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    console.print(f"\n📊 [bold green]Report generated: {report_path}[/bold green]")
    
    # Open in browser
    webbrowser.open(f"file://{report_path}")
    console.print("🌐 [cyan]Opening report in browser...[/cyan]")

def generate_html_report(results, all_items):
    """Generate HTML report with Catppuccin Mocha theme"""
    
    # Catppuccin Mocha colors
    catppuccin_mocha = {
        'base': '#1e1e2e',
        'mantle': '#181825',
        'crust': '#11111b',
        'text': '#cdd6f4',
        'subtext0': '#a6adc8',
        'surface0': '#313244',
        'surface1': '#45475a',
        'surface2': '#585b70',
        'green': '#a6e3a1',
        'red': '#f38ba8',
        'yellow': '#f9e2af',
        'blue': '#89b4fa',
        'mauve': '#cba6f7',
        'teal': '#94e2d5',
        'peach': '#fab387',
        'maroon': '#eba0ac',
        'lavender': '#b4befe',
    }
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tutu Batch Processing Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</title>
    <style>
        :root {{
            --base: {catppuccin_mocha['base']};
            --mantle: {catppuccin_mocha['mantle']};
            --crust: {catppuccin_mocha['crust']};
            --text: {catppuccin_mocha['text']};
            --subtext0: {catppuccin_mocha['subtext0']};
            --surface0: {catppuccin_mocha['surface0']};
            --surface1: {catppuccin_mocha['surface1']};
            --surface2: {catppuccin_mocha['surface2']};
            --green: {catppuccin_mocha['green']};
            --red: {catppuccin_mocha['red']};
            --yellow: {catppuccin_mocha['yellow']};
            --blue: {catppuccin_mocha['blue']};
            --mauve: {catppuccin_mocha['mauve']};
            --teal: {catppuccin_mocha['teal']};
            --peach: {catppuccin_mocha['peach']};
            --lavender: {catppuccin_mocha['lavender']};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--base);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: var(--mauve);
            text-align: center;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }}
        
        .summary {{
            background-color: var(--mantle);
            border: 1px solid var(--surface0);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .summary h2 {{
            color: var(--blue);
            margin-bottom: 1rem;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        
        .stat-card {{
            background-color: var(--surface0);
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
        }}
        
        .stat-card .number {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--peach);
        }}
        
        .stat-card .label {{
            color: var(--subtext0);
            font-size: 0.9rem;
        }}
        
        .item {{
            background-color: var(--mantle);
            border: 1px solid var(--surface0);
            border-radius: 8px;
            margin-bottom: 2rem;
            overflow: hidden;
        }}
        
        .item-header {{
            background-color: var(--surface0);
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .item-title {{
            color: var(--lavender);
            font-size: 1.3rem;
            font-weight: bold;
        }}
        
        .status {{
            padding: 0.3rem 0.8rem;
            border-radius: 4px;
            font-size: 0.9rem;
            font-weight: bold;
        }}
        
        .status.done {{
            background-color: var(--green);
            color: var(--crust);
        }}
        
        .status.in_progress {{
            background-color: var(--yellow);
            color: var(--crust);
        }}
        
        .status.pending {{
            background-color: var(--surface2);
            color: var(--text);
        }}
        
        .item-content {{
            padding: 1.5rem;
        }}
        
        .section {{
            margin-bottom: 1.5rem;
        }}
        
        .section h3 {{
            color: var(--teal);
            margin-bottom: 0.5rem;
        }}
        
        .description, .context {{
            background-color: var(--surface0);
            padding: 1rem;
            border-radius: 4px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .steps {{
            margin-top: 0.5rem;
        }}
        
        .step {{
            padding: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .step.done {{
            color: var(--green);
        }}
        
        .step.pending {{
            color: var(--subtext0);
        }}
        
        .output {{
            background-color: var(--crust);
            border: 1px solid var(--surface1);
            border-radius: 4px;
            padding: 1rem;
            margin-top: 1rem;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-x: auto;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .error {{
            color: var(--red);
        }}
        
        .working-dir {{
            color: var(--blue);
            font-family: monospace;
            font-size: 0.9rem;
        }}
        
        .timestamp {{
            color: var(--subtext0);
            text-align: center;
            margin-top: 3rem;
            font-size: 0.9rem;
        }}
        
        .expand-button {{
            background-color: var(--surface1);
            color: var(--text);
            border: none;
            padding: 0.4rem 0.8rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background-color 0.2s;
        }}
        
        .expand-button:hover {{
            background-color: var(--surface2);
        }}
        
        .collapsible {{
            max-height: 200px;
            overflow: hidden;
            position: relative;
        }}
        
        .collapsible.expanded {{
            max-height: none;
        }}
        
        .collapsible::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 50px;
            background: linear-gradient(transparent, var(--crust));
            pointer-events: none;
        }}
        
        .collapsible.expanded::after {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Tutu Batch Processing Report</h1>
        
        <div class="summary">
            <h2>📊 Summary</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="number">{len(all_items)}</div>
                    <div class="label">Total Items</div>
                </div>
                <div class="stat-card">
                    <div class="number">{sum(1 for r in results if r['item'].status == 'done')}</div>
                    <div class="label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="number">{sum(1 for r in results if r['item'].status == 'in_progress')}</div>
                    <div class="label">In Progress</div>
                </div>
                <div class="stat-card">
                    <div class="number">{sum(len(r['steps_completed']) for r in results)}</div>
                    <div class="label">Steps Completed</div>
                </div>
            </div>
        </div>
"""
    
    for result in results:
        item = result['item']
        status_class = item.status.replace(' ', '_')
        
        html += f"""
        <div class="item">
            <div class="item-header">
                <div>
                    <span class="item-title">#{item.id}: {item.title}</span>
                    <div class="working-dir">📁 {item.working_directory}</div>
                </div>
                <span class="status {status_class}">{item.status.upper()}</span>
            </div>
            <div class="item-content">
                <div class="section">
                    <h3>Description</h3>
                    <div class="description">{item.description}</div>
                </div>
"""
        
        if item.context:
            html += f"""
                <div class="section">
                    <h3>Context</h3>
                    <div class="context">{item.context}</div>
                </div>
"""
        
        if item.steps:
            html += """
                <div class="section">
                    <h3>Steps</h3>
                    <div class="steps">
"""
            for step in item.steps:
                step_class = 'done' if step.status == 'done' else 'pending'
                icon = '✅' if step.status == 'done' else '⏳'
                html += f"""
                        <div class="step {step_class}">
                            {icon} Step #{step.id}: {step.description}
                        </div>
"""
            html += """
                    </div>
                </div>
"""
        
        # Add output section
        if result['stdout'] or result['stderr']:
            output_id = f"output_{item.id}"
            html += f"""
                <div class="section">
                    <h3>Output <button class="expand-button" onclick="toggleExpand('{output_id}')">Toggle Full Output</button></h3>
                    <div class="output collapsible" id="{output_id}">"""
            
            if result['stdout']:
                html += result['stdout']
            
            if result['stderr']:
                html += f"""\n\n<span class="error">Errors:\n{result['stderr']}</span>"""
            
            html += """
                    </div>
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += f"""
        <div class="timestamp">
            Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")} Pacific Time
        </div>
    </div>
    
    <script>
        function toggleExpand(id) {{
            const element = document.getElementById(id);
            element.classList.toggle('expanded');
        }}
    </script>
</body>
</html>
"""
    
    return html

def main():
    import sys
    
    # If no arguments provided (just 'tutu'), default to list command
    if len(sys.argv) == 1:
        sys.argv.append("list")
    
    app()

if __name__ == "__main__":
    main()