# Tutu - Task Management System <�

Welcome to Tutu! This is a task management system designed to work seamlessly with Claude Code.

## For Claude Code Users >

When you're working on a TutuItem through Claude Code, here are the commands you can use:

### Managing Steps

To add a new step to the current TutuItem:
```bash
tutu add-step <item_id> "Description of the step"
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

## Important Notes for Claude Code =�

1. **Always track your progress** by adding steps as you work
2. **Mark steps as complete** when you finish them
3. **Use `tutu done`** only when the entire task is complete
4. The item ID and step IDs are shown in the initial context when the session starts
5. **Make sure all of your internal Todo list steps also update TutuItem and TutuItemStep**
6. **Tutu location**: The absolute path to tutu is `/Users/dorkitude/Library/Python/3.11/bin/tutu`
7. **Print steps after updates**: Always run `tutu status <item_id>` after adding or completing steps to show the current progress

## Example Workflow =�

1. You'll see the TutuItem details when the session starts
2. As you work, add steps: `tutu add-step 1 "Implemented user authentication"`
3. Complete steps as you go: `tutu complete-step 1`
4. When everything is done: `tutu done 1`

Remember: Good task tracking helps everyone understand the progress! =�