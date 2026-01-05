# Hands-Off Mode

Enable automated workflows without manual permission prompts by setting `CLAUDE_HANDSOFF=true`. This mode auto-approves safe, local operations while maintaining strict safety boundaries for destructive or publish actions.

## Quick Start

```bash
# Enable hands-off mode
export HANDSOFF_MODE=true
export HANDSOFF_MAX_CONTINUATIONS=10  # Optional: set auto-continue limit

# Run full implementation workflow without prompts
# Both of them will run until deliveries without human intervention.
# Ideally, users only needs to look at issue/pr created at the end.
/ultra-planner "New feature plan"
/new # New session
/issue-to-impl 42
```

The temporary data is stored in `.tmp/claude-hooks/handsoff-sessions/<session-id>.json`.

## What Gets Handsoff?

### Permission Requests

It uses `.claude/hooks/permission-request.sh` to aut-approve safe operations.
It is a more powerful solution to `settings.json` as it only supports rigid regex patterns.

### Auto-continuations

Automatically continues workflows by tracking workflow state through `UserPromptSubmit`, `Stop`, and `PostToolUse` hooks.
The system detects `/ultra-planner` and `/issue-to-impl` workflows and stops continuation when the workflow reaches completion.
All these three hooks shall be implemented in Python as it is easier to:
1. manage complicated state logics;
2. parse JSON easily

For the input data from hooks, see [Claude Code Hooks documents](https://code.claude.com/docs/en/hooks).
A typical input data is from `stdin`, which can be read

```python
import sys
import json
raw_json =  json.load(sys.stdin.read())
```

which has the following fields, where `session_id` and `transcript_path` are the key fields to identify the session and store state:

```json
{
  // Common fields
  session_id: string
  transcript_path: string  // Path to conversation JSON
  cwd: string              // The current working directory when the hook is invoked
  permission_mode: string  // Current permission mode: "default", "plan", "acceptEdits", "dontAsk", or "bypassPermissions"

  // Event-specific fields
  hook_event_name: string
  ...
}
```

and the response is in JSONL format, where each single line is a JSON object like below:
```json
{
  {
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I assist you today?"
    }
  ],
  "model": "claude-sonnet-4-5",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 12,
    "output_tokens": 8
  }
}
```

We also designed a state file to track workflow state and continuation count:
```json
{
  "workflow": "ultra-planner",  // or "issue-to-impl"
  "state": "wip",               // or "done"
  "count": 3                    // number of continuations so far
}
```

**Hook behavior**:

- `UserPromptSubmit`: It reads the current `session_id` and find the `.tmp/claude-hooks/handsoff-sessions/<session_id>.json` state file (create one if not exists). It checks if the newest user prompt starts with `/ultra-planner` or `/issue-to-impl`, and if so, changes the `workflow` field accordingly, and initializes the `state` to `wip`.

- `PostToolUse`: Post tool use hook checks if the tool is related to the workflow state transitions. Specifically:
  - **ultra-planner**: As per our [ultra-planner workflow](../.claude/commands/ultra-planner.md) it uses `gh issue create` to create a placeholder issue, and later uses `gh issue --edit` to update the issue with implementation details. The hook detects these tool uses and updates the workflow state. Once it calls `gh issue --edit` with `--body` or `--file-body`, it marks the workflow state as `done`.
  - **issue-to-impl**: As per our [issue-to-implementation workflow](../.claude/commands/issue-to-impl.md), it creates milestones and pull requests. If it creates a git commit message with `[milestone]`, the state is still `wip`. Once it hit a `gh pr create` tool use, it marks the workflow state as `done`.

- `Stop`: This hook is the key to enable full hands-off auto-continuation. It reads the state file and checks:

If `state` is `done`, it responds with:
```json
{
  "decision": "block",
  "reason": "The task is done.",
}
```

Otherwise, the last 5 lines of `text` content from the transcript JSONL file, read from `transcript_path`, are fed to Haiku to determine what to do next.

Typically, we have the following:

`/ultra-planner` sometimes blocks itself after analyzing the issue.

1. Just simply give a "continue on plan making" decision here.

`/issue-to-impl` sometimes blocks itself after creating a milestone.

1. If it is not the last milestone of development, just give a simple "continue on the implementation of the latest milestone" decision here.
2. If it is the last milestone, we can say "/pull-request --open" where this command fuses the code review with the PR creation.
3. After code review is done, it will ask you to resolve the code review concerns, or create the PR.
   - Accordingly make the decision of "fix the code review comments" or "create the PR".
4. Once the PR content is created, it will ask you "Should I create the PR?" --- simply make a decision "yes, create the PR".
5. After PR is created, the workflow is done.

The response should be in such format:
```json
{
  "decision": undefined,
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "additionalContext": "<your decision description here>"
  }
}
```

For all unknown cases, just simply respond with a block decision to avoid any unsafe operations,
and leave a comment on the corresponding issue saying `@user, manual intervention is required for session <session_id>.`,
where `user` is the GitHub user who opened the issue, and `session_id` is the current session ID.

The response should be in such format:
```json
{
  "decision": "block",
  "reason": "Manual intervention required for session <session_id>.",
  "comment": "@user, manual intervention is required for session <session_id>."
}
```


## Debug Logging

When troubleshooting auto-continuation behavior, enable debug logging with `HANDSOFF_DEBUG=true`. This creates a per-session JSONL history file that records workflow state transitions, Stop decisions, and the reasons behind them.

**Enable debug logging:**
```bash
export HANDSOFF_DEBUG=true
```

**History file location:**
```
.tmp/claude-hooks/handsoff-sessions/history/<session_id>.jsonl
```

**JSONL schema:**
Each line is a JSON object with these fields:
- `timestamp`: ISO 8601 timestamp
- `session_id`: Session identifier
- `event`: Hook event type (`UserPromptSubmit`, `PostToolUse`, `Stop`)
- `workflow`: Workflow name (`ultra-planner`, `issue-to-impl`, or empty)
- `state`: Current workflow state (e.g., `planning`, `implementation`, `done`)
- `count`: Current continuation count
- `max`: Maximum continuations allowed
- `decision`: Hook decision (`allow`, `ask`, or empty for non-Stop events)
- `reason`: Reason code for Stop decisions (see below)
- `description`: Human-readable description from hook parameters
- `tool_name`: Tool name for PostToolUse events (e.g., `Skill`, `Bash`)
- `tool_args`: Tool arguments for PostToolUse events
- `new_state`: New workflow state after PostToolUse transitions

**Reason codes for Stop decisions:**
- `handsoff_disabled`: `CLAUDE_HANDSOFF` not set to `"true"`
- `no_state_file`: State file not found for session
- `workflow_done`: Workflow state is `done` (completion reached)
- `invalid_max`: `HANDSOFF_MAX_CONTINUATIONS` is non-numeric or ≤ 0
- `over_limit`: Continuation count exceeds max limit
- `under_limit`: Count ≤ max, auto-continue allowed

**Example history entry (Stop event):**
```json
{"timestamp":"2026-01-05T10:23:45Z","session_id":"abc123","event":"Stop","workflow":"issue-to-impl","state":"implementation","count":"3","max":"10","decision":"allow","reason":"under_limit","description":"Milestone 2 created","tool_name":"","tool_args":"","new_state":""}
```

**Privacy note:** History logs contain tool arguments and descriptions from hook parameters, which may include user content. Logging is opt-in; disable by unsetting `HANDSOFF_DEBUG` or setting it to any value other than `"true"`.


## Related Documentation

- [Claude Code Pre/Post Hooks](https://code.claude.com/docs/en/hooks)
- [Issue to Implementation Workflow](workflows/issue-to-implementation.md)
- [Issue-to-Impl Tutorial](tutorial/02-issue-to-impl.md)
- [Ultra Planner Workflow](workflows/ultra-planner.md)
