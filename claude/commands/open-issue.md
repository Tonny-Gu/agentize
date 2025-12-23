---
name: open-issue
description: Create GitHub issues from conversation context with proper formatting
---

# Open Issue Command

Execute the open-issue skill to create GitHub issues from conversation context with
meaningful titles and proper formatting.

Invoke the skill: /open-issue

This command will:
1. Analyze conversation context to extract issue details
2. Review the tag standards in `docs/git-msg-tags.md`
3. Draft a GitHub issue following the format defined in the open-issue skill
4. Confirm with the user before creating the issue via `gh issue create`
