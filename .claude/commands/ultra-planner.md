---
name: ultra-planner
description: Multi-agent debate-based planning with /ultra-planner command
argument-hint: [feature-description] or --refine [issue-no] [refine-comments] or --from-issue [issue-no]
---

ultrathink

# Ultra Planner Command

**IMPORTANT**: Keep a correct mindset when this command is invoked.

0. This workflow is intended to be as hands-off as possible, do your best
  - NOT TO STOP until the plan is finalized
  - NOT TO ask user for design decisions. Choose the one you think the most reasonable.
    If it is bad plan, user will feed it later.

1. This is a **planning tool only**. It takes a feature description as input and produces
a consensus implementation plan as output. It does NOT make any code changes or implement features.
Even if user is telling you "build...", "add...", "create...", "implement...", or "fix...",
you must interpret these as making a plan for how to have these achieved, not actually doing them!
  - **DO NOT** make any changes to the codebase!

2. This command uses a **multi-agent debate system** to generate high-quality plans.
**No matter** how simple you think the request is, always strictly follow the multi-agent
debase workflow below to do a thorough analysis of the request throughout the whole code base.
Sometimes what seems simple at first may have hidden complexities or breaking changes that
need to be uncovered via a debate and thorough codebase analysis.
  - **DO** follow the following multi-agent debate workflow exactly as specified.

Create implementation plans through multi-agent debate, combining innovation, critical analysis,
and simplification into a balanced consensus plan.

Invoke the command: `/ultra-planner [feature-description]` or `/ultra-planner --refine [issue-no] [refine-comments]`

## What This Command Does

This command orchestrates a multi-agent debate system to generate high-quality implementation plans:

1. **Context gathering**: Launch understander agent to gather codebase context
2. **Dual proposers**: Launch bold-proposer and paranoia-proposer in parallel (with context)
3. **Five-agent analysis**: Launch critique, proposal-reducer, and code-reducer to analyze both proposals
4. **Combine reports**: Merge all five perspectives into single document
5. **External consensus**: Invoke external-consensus skill to synthesize balanced plan(s)
6. **Multiple plans**: If no consensus, provide multiple plan options for developer choice
7. **Draft issue creation**: Automatically create draft GitHub issue via open-issue skill

## Inputs

**This command only accepts feature descriptions for planning purposes. It does not execute implementation.**

**From arguments ($ARGUMENTS):**

- To avoid expanding ARGUMENTS multiple times, later we will use `{FEATURE_DESC}` to refer to it.

**Default mode:**
```
/ultra-planner Add user authentication with JWT tokens and role-based access control
```

**Refinement mode:**

```
/ultra-planner --refine <issue-no> <description>
```
- Refines an existing plan by running it through the debate system again

**From-issue mode:**

```
/ultra-planner --from-issue <issue-no>
```
- Creates a plan for an existing issue (typically a feature request)
- Reads the issue title and body as the feature description
- Updates the existing issue with the consensus plan (no new issue created)
- Used by the server for automatic feature request planning

**From conversation context:**
- If `$ARGUMENTS` is empty, extract feature description from recent messages
- Look for: "implement...", "add...", "create...", "build..." statements

## Outputs

**This command produces planning documents only. No code changes are made.**

**Files created:**
- `.tmp/issue-[refine-]{N}-context.md` - Understander context summary
- `.tmp/issue-[refine-]{N}-bold.md` - Bold proposer agent report (with code diffs)
- `.tmp/issue-[refine-]{N}-paranoia.md` - Paranoia proposer agent report (with code diffs)
- `.tmp/issue-[refine-]{N}-critique.md` - Critique agent report
- `.tmp/issue-[refine-]{N}-proposal-reducer.md` - Proposal reducer agent report
- `.tmp/issue-[refine-]{N}-code-reducer.md` - Code reducer agent report
- `.tmp/issue-[refine-]{N}-debate.md` - Combined five-agent report
- `.tmp/issue-[refine-]{N}-consensus.md` - Final balanced plan(s)

`[refine-]` is optional for refine mode.

**GitHub issue:**
- Created via open-issue skill if user approves

**Terminal output:**
- Debate summary from all three agents
- Consensus plan summary
- GitHub issue URL (if created)

## Workflow

### Step 1: Parse Arguments and Extract Feature Description

Accept the $ARGUMENTS.

**Refinement mode:** If we have `--refine` at the beginning, the next number is the issue number to be refined,
and the rest are issue refine comments. You should fetch the issue to incorporate the users comments.
```bash
gh issue view <issue-no>
```

**From-issue mode:** If we have `--from-issue` at the beginning, the next number is the issue number to plan.
Fetch the issue title and body to use as the feature description:
```bash
gh issue view <issue-no> --json title,body
```
In this mode:
- The issue number is saved for Step 3 (skip placeholder creation, use existing issue)
- The feature description is extracted from the issue title and body
- After consensus, update the existing issue instead of creating a new one

### Step 2: Validate Feature Description

Ensure feature description is clear and complete:

**Check:**
- Non-empty (minimum 10 characters)
- Describes what to build (not just "add feature")
- Provides enough context for agents to analyze

**If unclear:**
```
The feature description is unclear or too brief.

Current description: {description}

Please provide more details:
- What functionality are you adding?
- What problem does it solve?
- Any specific requirements or constraints?
```

Ask user for clarification.

### Step 3: Create Placeholder Issue (or use existing issue for --from-issue mode)

**For `--from-issue` mode:**
Skip placeholder creation. Use the issue number from Step 1 as `ISSUE_NUMBER` for all artifact filenames.

**For default mode (new feature):**

**REQUIRED SKILL CALL (before agent execution):**

Create a placeholder issue to obtain the issue number for artifact naming:

```
Skill tool parameters:
  skill: "open-issue"
  args: "--auto"
```

**Provide context to open-issue skill:**
- Feature description: `FEATURE_DESC`
- Issue body: "Placeholder for multi-agent planning in progress. This will be updated with the consensus plan."

**Extract issue number from response:**
```bash
# Expected output: "GitHub issue created: #42"
ISSUE_URL=$(echo "$OPEN_ISSUE_OUTPUT" | grep -o 'https://[^ ]*')
ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -o '[0-9]*$')
```

**Use `ISSUE_NUMBER` for all artifact filenames going forward** (Steps 4-8).

**Error handling:**
- If placeholder creation fails, stop execution and report error (cannot proceed without issue number)

### Step 4: Invoke Understander Agent

**REQUIRED TOOL CALL (before Bold-Proposer):**

Use the Task tool to launch the understander agent to gather codebase context:

```
Task tool parameters:
  subagent_type: "understander"
  prompt: "Gather codebase context for the following feature request: {FEATURE_DESC}"
  description: "Gather codebase context"
  model: "sonnet"
```

**Wait for agent completion** (blocking operation, do not proceed to Step 5 until done).

**Extract output:**
- Generate filename: `CONTEXT_FILE=".tmp/issue-${ISSUE_NUMBER}-context.md"`
- Save the agent's full response to `$CONTEXT_FILE`
- Also store in variable `UNDERSTANDER_OUTPUT` for passing to Bold-proposer in Step 5

### Step 5: Invoke Bold-Proposer and Paranoia-Proposer Agents (Parallel)

**REQUIRED TOOL CALLS (in parallel):**

Use the Task tool to launch BOTH proposer agents in a SINGLE message with TWO Task tool calls:

**Task tool call #1 - Bold-Proposer Agent:**
```
Task tool parameters:
  subagent_type: "bold-proposer"
  prompt: "Research and propose an innovative solution for: {FEATURE_DESC}

CODEBASE CONTEXT (from understander):
{UNDERSTANDER_OUTPUT}

Use this context as your starting point for understanding the codebase.
Focus your exploration on SOTA research and innovation.
Output concrete code diffs, not LOC estimates."
  description: "Research SOTA solutions"
  model: "opus"
```

**Task tool call #2 - Paranoia-Proposer Agent:**
```
Task tool parameters:
  subagent_type: "paranoia-proposer"
  prompt: "Critically analyze and propose destructive refactoring for: {FEATURE_DESC}

CODEBASE CONTEXT (from understander):
{UNDERSTANDER_OUTPUT}

Use this context to identify code that needs to be rewritten or deleted.
Focus on extracting core requirements and eliminating unnecessary complexity.
Output concrete code diffs, not LOC estimates."
  description: "Propose destructive refactoring"
  model: "opus"
```

**Wait for both agents to complete** (blocking operation, do not proceed to Step 6 until done).

**Extract outputs:**
- Generate filename: `BOLD_FILE=".tmp/issue-${ISSUE_NUMBER}-bold-proposal.md"`
- Save bold-proposer's response to `$BOLD_FILE`
- Generate filename: `PARANOIA_FILE=".tmp/issue-${ISSUE_NUMBER}-paranoia-proposal.md"`
- Save paranoia-proposer's response to `$PARANOIA_FILE`
- Store both in variables `BOLD_PROPOSAL` and `PARANOIA_PROPOSAL` for passing to analyzers in Step 6

### Step 6: Invoke Critique, Proposal-Reducer, and Code-Reducer Agents (Parallel)

**REQUIRED TOOL CALLS #3, #4 & #5:**

**CRITICAL**: Launch ALL THREE agents in a SINGLE message with THREE Task tool calls to ensure parallel execution.

**Task tool call #1 - Critique Agent:**
```
Task tool parameters:
  subagent_type: "proposal-critique"
  prompt: "Analyze the following proposals for feasibility and risks:

Feature: {FEATURE_DESC}

BOLD PROPOSAL:
{BOLD_PROPOSAL}

PARANOIA PROPOSAL:
{PARANOIA_PROPOSAL}

Provide critical analysis of assumptions, risks, and feasibility for BOTH proposals."
  description: "Critique both proposals"
  model: "opus"
```

**Task tool call #2 - Proposal-Reducer Agent:**
```
Task tool parameters:
  subagent_type: "proposal-reducer"
  prompt: "Simplify the following proposals using 'less is more' philosophy:

Feature: {FEATURE_DESC}

BOLD PROPOSAL:
{BOLD_PROPOSAL}

PARANOIA PROPOSAL:
{PARANOIA_PROPOSAL}

Identify unnecessary complexity and propose simpler alternatives for BOTH proposals.
Your stance: Minimize the number of changes (fewer proposal items = fewer changes)."
  description: "Simplify both proposals"
  model: "opus"
```

**Task tool call #3 - Code-Reducer Agent:**
```
Task tool parameters:
  subagent_type: "code-reducer"
  prompt: "Analyze code volume and simplify the following proposals:

Feature: {FEATURE_DESC}

BOLD PROPOSAL:
{BOLD_PROPOSAL}

PARANOIA PROPOSAL:
{PARANOIA_PROPOSAL}

Allow large code changes but limit unreasonable code growth.
Your stance: Allow many changes, but ensure the final codebase doesn't grow unreasonably."
  description: "Reduce code complexity"
  model: "opus"
```

**Wait for all three agents to complete** (blocking operation).

**Extract outputs:**
- Generate filename: `CRITIQUE_FILE=".tmp/issue-${ISSUE_NUMBER}-critique.md"`
- Save critique agent's response to `$CRITIQUE_FILE`
- Generate filename: `PROPOSAL_REDUCER_FILE=".tmp/issue-${ISSUE_NUMBER}-proposal-reducer.md"`
- Save proposal-reducer agent's response to `$PROPOSAL_REDUCER_FILE`
- Generate filename: `CODE_REDUCER_FILE=".tmp/issue-${ISSUE_NUMBER}-code-reducer.md"`
- Save code-reducer agent's response to `$CODE_REDUCER_FILE`

**Expected agent outputs:**
- Bold proposer: Innovative proposal with code diffs
- Paranoia proposer: Destructive refactoring proposal with code diffs
- Critique: Risk analysis and feasibility assessment of BOTH proposals
- Proposal-reducer: Simplified version of BOTH proposals (minimize changes)
- Code-reducer: Code volume analysis of BOTH proposals (limit growth)

### Step 7: Invoke External Consensus Skill

**REQUIRED SKILL CALL:**

Use the Skill tool to invoke the external-consensus skill with the 5 report file paths:

```
Skill tool parameters:
  skill: "external-consensus"
  args: "{BOLD_FILE} {PARANOIA_FILE} {CRITIQUE_FILE} {PROPOSAL_REDUCER_FILE} {CODE_REDUCER_FILE}"
```

**Note:** The external-consensus skill will:
1. Combine the 5 agent reports into a single debate report (saved as `.tmp/issue-{N}-debate.md`)
2. Process the combined report through external AI review (Codex or Claude Opus)
3. Generate consensus plan(s) - single plan if consensus, multiple plans if perspectives diverge

NOTE: This consensus synthesis can take long time depending on the complexity of the debate report.
Give it 30 minutes timeout to complete, which is mandatory for **ALL DEBATES**!

**What this skill does:**
1. Combines the 5 agent reports into a single debate report (saved as `.tmp/issue-{N}-debate.md`)
2. Prepares external review prompt using `.claude/skills/external-consensus/external-review-prompt.md`
3. Invokes Codex CLI (preferred) or Claude API (fallback) for consensus synthesis
4. Parses and validates the consensus plan structure
5. If perspectives diverge significantly, generates multiple plan options:
   - **Plan A (Conservative)**: Minimal changes, lower risk
   - **Plan B (Balanced)**: Middle ground approach
   - **Plan C (Aggressive)**: Maximum refactoring, higher reward/risk
6. Saves consensus plan(s) to `.tmp/issue-{N}-consensus.md`
7. Returns summary and file path

**Expected output structure from skill:**
```
External consensus review complete!

Consensus Plan Summary:
- Feature: {feature_name}
- Consensus: [Achieved / Multiple Plans]
- Plans: {count} (1 if consensus, 2-3 if divergent)

Key Decisions:
- From Bold Proposal: {accepted_innovations}
- From Paranoia Proposal: {accepted_destructions}
- From Critique: {risks_addressed}
- From Proposal-Reducer: {simplifications_applied}
- From Code-Reducer: {code_reductions_applied}

Consensus plan saved to: {CONSENSUS_PLAN_FILE}
```

**Extract:**
- Save the consensus plan file path as `CONSENSUS_PLAN_FILE`

### Step 8: Update Placeholder Issue with Consensus Plan

**REQUIRED SKILL CALL:**

Use the Skill tool to invoke the open-issue skill with update and auto flags:

```
Skill tool parameters:
  skill: "open-issue"
  args: "--update ${ISSUE_NUMBER} --auto {CONSENSUS_PLAN_FILE}"
```

**What this skill does:**
1. Reads consensus plan from file
2. Determines appropriate tag from `docs/git-msg-tags.md`
3. Formats issue with `[plan]` prefix and Problem Statement/Proposed Solution sections
4. Updates existing issue #${ISSUE_NUMBER} (created in Step 3) using `gh issue edit`
5. Returns issue number and URL

**Expected output:**
```
Plan issue #${ISSUE_NUMBER} updated with consensus plan.

Title: [plan][tag] {feature name}
URL: {issue_url}

To refine: /ultra-planner --refine ${ISSUE_NUMBER}
To implement: /issue-to-impl ${ISSUE_NUMBER}
```

### Step 9: Finalize Issue Labels

**REQUIRED BASH COMMAND:**

Add the "agentize:plan" label to mark the issue as a finalized plan:

```bash
gh issue edit ${ISSUE_NUMBER} --add-label "agentize:plan"
```

**For `--from-issue` mode only:** Also remove the "agentize:feat-request" label if present:

```bash
gh issue edit ${ISSUE_NUMBER} --remove-label "agentize:feat-request"
```

**What this does:**
1. Adds "agentize:plan" label to the issue (creates label if it doesn't exist)
2. Removes "agentize:feat-request" label (if from-issue mode) to prevent re-processing
3. Triggers hands-off state machine transition to `done` state
4. Marks the issue as ready for review/implementation

**Expected output:**
```
Label "agentize:plan" added to issue #${ISSUE_NUMBER}
```

Display the final output to the user. Command completes successfully.

## Usage Examples

### Example 1: Basic Feature Planning

**Input:**
```
/ultra-planner Add user authentication with JWT tokens and role-based access control
```

**Output:**
```
Starting multi-agent debate...

[Bold-proposer and Paranoia-proposer run in parallel - 3-5 minutes]
[Critique, Proposal-reducer, and Code-reducer run in parallel - 3-5 minutes]

Debate complete! Five perspectives:
- Bold: Incremental improvement with code diffs
- Paranoia: Destructive refactoring with code diffs
- Critique: High feasibility for Bold, Medium for Paranoia, 3 critical risks
- Proposal-Reducer: Recommends Bold base with simplifications
- Code-Reducer: Net code reduction of 15% possible

External consensus review...

Consensus: [Achieved / Multiple Plans]
- Plan A (Conservative): Minimal changes (~150 LOC net)
- Plan B (Balanced): Middle ground (~280 LOC net)
- Plan C (Aggressive): Full refactoring (~50 LOC net, but 400 LOC changed)

Draft GitHub issue created: #42
Title: [plan][feat] Add user authentication
URL: https://github.com/user/repo/issues/42

To refine: /ultra-planner --refine 42
To implement: /issue-to-impl 42
```

### Example 2: Plan Refinement

**Input:**
```
/ultra-planner --refine 42
```

**Output:**
```
Fetching issue #42...
Running debate on current plan to identify improvements...

[Debate completes]

Refined consensus plan:
- Reduced LOC: 280 → 210 (25% reduction)
- Removed: OAuth2 integration
- Added: Better error handling

Issue #42 updated with refined plan.
URL: https://github.com/user/repo/issues/42
```
