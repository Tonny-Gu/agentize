---
name: open-issue
description: Create GitHub issues from conversation context with proper formatting
argument-hint: [issue-details | file-path]
---

# Open Issue Command

Create GitHub issues with proper formatting from conversation context.
This command should accept either directly typing the issue details,
a markdown draft discussing the issue, or an implementation plan.

Invoke the command: /open-issue [issue-details | file-path]

If arguments are provided via $ARGUMENTS, the skill will use them as input instead of
relying solely on conversation context.

## What This Command Does

This command executes the `open-issue` skill to create a GitHub issue. The skill will:
1. Analyze conversation context to extract issue details.
    - If a file is given, read the file to determine if it is already a plan or a issue draft.
    - If no file is given, summarize the conversation to extract the issue details.
2. Review tag standards in `docs/git-msg-tags.md`
3. Determine the issue type and appropriate format
4. Draft the issue with proper formatting
5. Confirm with the user before creating via `gh issue create`

## Issue Types

**For [plan] issues:** If the conversation includes an implementation plan (created by
`make-a-plan` skill), the `open-issue` skill will use that plan as the "Proposed Solution"
section and tag the issue as `[plan][tag]`.

**For other issues:** Bug reports, feature requests, or improvements without detailed
plans will use simpler formats with appropriate tags.

## Workflow with Planning

If you need to create a [plan] issue but haven't created a plan yet:

1. First run: `/make-a-plan` to create the implementation plan
2. Review and approve the plan
3. Then run: `/open-issue` to create the GitHub issue with the plan

The `open-issue` skill will automatically detect the plan from conversation context
and include it in the issue.

## When to Use Each Approach

**Use make-a-plan → open-issue for:**
- New features requiring implementation details
- Refactoring tasks with multiple file changes
- Improvements with specific implementation approach
- Any issue that needs a `[plan][tag]` prefix

**Use open-issue directly for:**
- Bug reports (even if they need fixes)
- Simple feature requests without implementation details
- General improvements or suggestions
- Issues that use `[bug report]`, `[feature request]`, or standalone `[tag]` prefixes
