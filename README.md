# Tutu - Task Management System

Tutu is a task management system designed to help track work items and their associated steps. It integrates seamlessly with Claude Code to provide persistent task tracking across sessions.

## Installation

```bash
# Install using pip or uv
uv pip install -e .
```

## Basic Usage

### Managing Items

Create a new item:
```bash
tutu add
```
This will start an interactive session prompting for title, description, and context.

List all items:
```bash
tutu list
```

View item details:
```bash
tutu status <item_id>
```

Mark an item as complete:
```bash
tutu done <item_id>
```

Edit an existing item:
```bash
tutu edit <item_id>
```
This will start an interactive session to update the title, description, and context.

Start a Claude Code session with item context:
```bash
tutu start <item_id>
```

### Managing Steps

Add a step to an item:
```bash
# Interactive mode (prompts for multi-line description)
tutu add-step <item_id>

# Or with --description option
tutu add-step <item_id> --description "Description of the step"
```

Complete a step:
```bash
tutu complete-step <step_id>
```

## Claude Code Integration

Tutu is designed to work with Claude Code. When starting a Claude session with `tutu start`, it will:

1. Prompt you to select an active TutuItem to work on
2. Inject context about the item and its steps into the Claude session
3. Provide Claude with instructions on how to track progress using Tutu commands

## Database

Tutu uses SQLite to store items and steps locally. The database is created automatically on first use.