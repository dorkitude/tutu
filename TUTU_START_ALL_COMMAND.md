# Tutu Start-All Context for Claude Code

This file contains the context and instructions for executing multiple TutuItems in sequence.

## Purpose

The `tutu start-all` command processes all pending TutuItems automatically by:
1. Looping through each TutuItem from `tutu list`
2. Running `tutu start` for each item in non-interactive mode
3. Gathering the output from each Claude Code session
4. Generating an HTML report with all results

## Instructions for Claude Code

You are running in batch mode to process multiple TutuItems. For each item:

1. **Work autonomously** - Complete the task without user interaction
2. **Track progress** - Use `tutu add-step` and `tutu complete-step` commands
3. **Complete tasks** - Mark items as done with `tutu done` when finished
4. **Provide clear output** - Your final output will be included in the batch report

## Batch Processing Guidelines

- You have full permissions to execute commands and make changes
- Focus on completing the task as described in the TutuItem
- If you encounter errors that prevent completion, document them clearly
- Your session output will be captured for the final report

## Important Notes

- This is a non-interactive session (--dangerously-skip-permissions flag is set)
- Complete each task to the best of your ability based on the item description
- Ensure all work is properly saved and committed if applicable
- The working directory will be set according to each TutuItem's configuration

## Report Output

Your work will be included in an HTML report with:
- Task title and description
- Steps completed
- Final status
- Full session output
- Any errors or issues encountered

Work efficiently and thoroughly on each assigned task! 🚀