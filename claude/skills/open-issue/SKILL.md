---
name: open-issue
description: Create GitHub issues from conversation context with proper formatting and tag selection
---

# Open Issue

This skill instructs AI agents on how to create GitHub issues from conversation context
with meaningful titles, proper formatting, and appropriate tag selection. The AI agent
should analyze the conversation, extract issue details, and confirm with the user before
creating the issue.

## Issue Format

GitHub issues created by this skill must follow this exact structure:

```markdown
# [prefix][tag]: A Brief Summary of the Issue

## Description

Provide a detailed description of this issue, including the related modules and the
problem statement.

## Steps to Reproduce

(Optional, only for bug reports)
Provide a minimized step to reproduce the bug.

## Proposed Solution

(Optional, but mandatory for [plan] issues)
Provide a detailed proposed solution or plan to address the issue.

- The plan SHOULD NOT include code audits! Code audits are part of the result of planning.
- The plan SHOULD include the related files to be modified, added, or deleted.

## Related PR

(Optional, but mandatory when Proposed Solution is provided)
This can be a placeholder upon creating the issue, however, once the PR is created,
update the PR# here.
```

## Tag Selection

A `git-msg-tags.md` file should appear in `{ROOT_PROJ}/docs/git-msg-tags.md` which
defines the tags related to the corresponding modules or modifications. The AI agent
**MUST** refer to this file to select the appropriate tag for the issue title.

If the file does not exist, reject the issue creation and ask the user to provide a
list of tags in `docs/git-msg-tags.md`.

### Tag Prefix Logic

The AI agent must determine which prefix and tag combination to use based on the issue type:

**Use `[plan][tag]` when:**
- The issue includes a "Proposed Solution" section
- The proposed solution outlines specific files to modify, add, or delete
- The tag is from `git-msg-tags.md` (e.g., `feat`, `sdk`, `bugfix`, `docs`, `test`, `refactor`, `chore`, `agent.skill`, `agent.command`, `agent.settings`, `agent.workflow`)
- Example: `[plan][feat]: Add TypeScript SDK template support`

**Use standalone `[tag]` when:**
- The issue is about a change but doesn't include implementation details
- It's a simple bug report or feature request without a plan
- The tag is from `git-msg-tags.md`
- Example: `[bugfix]: Pre-commit hook fails to run tests`

**Use `[bug report]`, `[feature request]`, or `[improvement]` when:**
- The issue doesn't fit standard git-msg-tags categories
- It's a high-level request without technical implementation details
- Example: `[feature request]: Add support for custom plugins`

## Workflow for AI Agents

When this skill is invoked, the AI agent **MUST** follow these steps:

### 1. Context Analysis Phase

Review the entire conversation history to extract issue details:
- Identify the problem/request being discussed
- Extract key details: what, why, affected modules
- Determine if this is a bug, feature request, or improvement plan
- Check if the user has provided implementation steps or solution proposals

Context signals for issue type:
- Bug report signals: "doesn't work", "error", "crash", "unexpected", "broken"
- Feature request signals: "add", "new", "would be nice", "enhancement", "support for"
- Improvement signals: "refactor", "optimize", "clean up", "better way"
- Plan signals: "let's implement", "step 1:", "we should create", "modify these files"

### 2. Tag Selection Phase

- Read `docs/git-msg-tags.md` to understand available tags
- Analyze the issue type and scope
- Apply the tag prefix logic described above
- If multiple tags could apply, choose the most specific one
- If the tag is ambiguous, ask the user to choose from 2-3 most relevant options

### 3. Issue Draft Construction

Build the issue following the format specification:

**Title:**
- Format: `[prefix][tag]: Brief Summary`
- Keep summary concise (max 80 characters for the summary portion)
- Ensure the summary clearly describes the issue

**Description section:**
- Provide detailed context about the issue
- Mention related modules or components affected
- Explain the problem statement clearly

**Steps to Reproduce section (only for bug reports):**
- Provide a minimized sequence of steps to reproduce the bug
- Be specific and actionable

**Proposed Solution section (mandatory for [plan] issues):**
- **DO NOT** include code audits as a step!
  Its already a part of planning by listing the specific files to be changed below!
- **DO NOT** include actual code snippets to save the context length.
- List specific files to modify, add, or delete
  - Bad Example: Audit the codebase to find the files to change.
  - Good Example: Modify `file_a.py:12-34` for X purpose.
- Provide high-level implementation approach
  - The files to be changed should be in the order of implementation steps
- Include the testing strategies for the proposed changes
  - Including files to add in `tests/` for new features or modifications, and
    clearly specify which aspect is being tested by each test file.
  - Bad Example: Add tests to cover the new feature.
  - Good Example: Modify `tests/test_xxx.py` to test this new features' specific behavior Y.

**Related PR section (when Proposed Solution exists):**
- Add placeholder text: "TBD - will be updated when PR is created"
- Or reference existing PR if available

### 4. User Confirmation Phase

**CRITICAL:** The AI agent **MUST** display the complete issue draft to the user
and wait for explicit confirmation before creating the issue.

Present the draft in a clear format:
```
I've prepared this GitHub issue:

---
[Full issue content here]
---

Should I create this issue?
```

- Wait for explicit "yes", "confirm", "create it", or similar affirmative response
- If the user requests modifications, update the draft and present again
- If the user declines, abort issue creation gracefully

### 5. GitHub Issue Creation

Once confirmed, create the issue using the GitHub CLI:

```bash
gh issue create --title "TITLE_HERE" --body "$(cat <<'EOF'
BODY_CONTENT_HERE
EOF
)"
```

**Important:**
- Use heredoc (`<<'EOF' ... EOF`) to preserve markdown formatting
- The body should include all sections from Description onwards (not the title)
- After successful creation, display the issue URL to the user
- Confirm: "GitHub issue created successfully: [URL]"

### 6. Error Handling

Handle common error scenarios gracefully:

**Missing git-msg-tags.md:**
```
Cannot create issue: docs/git-msg-tags.md not found.
Please create this file with your project's tag definitions.
```

**GitHub CLI not authenticated:**
```
GitHub CLI is not authenticated. Please run:
  gh auth login
```

**No conversation context:**
```
I don't have enough context to create an issue. Could you please provide:
- What is the issue about?
- Is this a bug, feature request, or improvement?
- Any additional details or proposed solutions?
```

**Issue creation failed:**
```
Failed to create GitHub issue: [error message]
Please check your GitHub CLI configuration and try again.
```

## Ownership

The AI agent **SHALL NOT** claim authorship or co-authorship of the GitHub issue.
The issue is created on behalf of the user, who is **FULLY** responsible for its content.

Do not add any "Created by AI" or similar attributions to the issue body unless
explicitly requested by the user.

## Examples

### Example 1: Plan Issue with Feature Tag

**Context:** User wants to add TypeScript SDK template support.

**Issue:**
```markdown
# [plan][feat]: Add TypeScript SDK template support

## Description

Add support for generating TypeScript SDK templates in the agentize project.
This will allow developers to bootstrap TypeScript-based agent SDKs alongside
the existing Python templates.

## Proposed Solution

To implement TypeScript SDK template support:
1. Create `templates/typescript/` directory structure
2. Add `templates/typescript/package.json` with default dependencies
3. Create `templates/typescript/tsconfig.json` with recommended settings
4. Add `templates/typescript/src/index.ts` as entry point
5. Update `claude/skills/sdk-init/SKILL.md` to support TypeScript option
6. Add tests in `tests/test_typescript_template.py`

## Related PR

TBD - will be updated when PR is created
```

### Example 2: Bug Report

**Context:** User reports that pre-commit hooks are not running tests.

**Issue:**
```markdown
# [bug report]: Pre-commit hook fails to run tests

## Description

The pre-commit hook defined in `.git/hooks/pre-commit` is not executing the
test suite before allowing commits. This allows broken code to be committed.

## Steps to Reproduce

1. Make changes to any Python file in `claude/skills/`
2. Run `git add .`
3. Run `git commit -m "test"`
4. Observe that no tests are executed before the commit succeeds

## Related PR

TBD
```

### Example 3: Feature Request

**Context:** User requests support for custom plugin architecture.

**Issue:**
```markdown
# [feature request]: Add support for custom plugins

## Description

Add a plugin system that allows users to extend agentize functionality with
custom plugins. This would enable community contributions and custom workflows
without modifying core code.
```
