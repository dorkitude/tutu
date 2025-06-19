# Tutu Context for Claude Code

This file contains the context that gets injected when starting a Claude Code session via `tutu start`.

## Working with TutuItems

When you're working on a TutuItem through Claude Code, here are the commands you can use:

### Managing Steps

To add a new step to the current TutuItem:
```bash
# Interactive mode (prompts for multi-line description)
tutu add-step <item_id>

# Or with --description option
tutu add-step <item_id> --description "Description of the step"
```

To mark a step as complete:
```bash
tutu complete-step <step_id>
```

### Completing the Task

When you've finished working on the TutuItem:
```bash
tutu done <item_id>
```

### Checking Status

To see the current status of the TutuItem:
```bash
tutu status <item_id>
```

### Other Useful Commands

List all pending items:
```bash
tutu list
```

Edit the current TutuItem (title, description, context):
```bash
tutu edit <item_id>
```

## Important Instructions for Claude Code

1. **Always track your progress** by adding steps as you work
2. **Mark steps as complete** when you finish them. Print the name of the step you completed, plus a checkmark emoji.
3. **Use `tutu done`** only when the entire task is complete
4. The item ID and step IDs are shown in the initial context when the session starts
5. **Make sure all of your internal Todo list steps also update TutuItem and TutuItemStep**
6. **Tutu location**: The absolute path to tutu is `/Users/dorkitude/Library/Python/3.11/bin/tutu`
7. **Print steps after updates**: Always run `tutu status <item_id>` after adding or completing steps to show the current progress

## Example Workflow

1. You'll see the TutuItem details when the session starts
2. As you work, add steps: `tutu add-step 1 --description "Implemented user authentication"`
3. Complete steps as you go: `tutu complete-step 1`
4. When everything is done: `tutu done 1`

## Integration with Claude's Todo System

Remember that when using Claude Code's built-in Todo system, you should mirror those todos as TutuItem steps. This ensures that progress is tracked both in Claude's session and in the persistent Tutu database.