# External Consensus Review Task

You are an expert software architect tasked with synthesizing a consensus implementation plan from five different perspectives on the same feature.

## Context

Five specialized agents have analyzed the following requirement:

**Feature Request**: {{FEATURE_DESCRIPTION}}

Each agent provided a different perspective:
1. **Bold Proposer**: Innovative, SOTA-driven approach with code diffs, advocating for incremental improvement on existing code.
2. **Paranoia Proposer**: Destructive refactoring approach with code diffs, advocating for clean-slate rewrites and deletions.
3. **Critique Agent**: Feasibility analysis and risk assessment for BOTH proposals.
4. **Proposal Reducer**: Simplified approach focusing on minimizing the number of changes (fewer proposal items = fewer changes = lower risk).
5. **Code Reducer**: Code volume analysis focusing on limiting unreasonable code growth (allow large changes, but limit total code increase).

## Your Task

Review all five perspectives and synthesize implementation plan(s) that:

1. **Incorporates the best ideas** from each perspective
2. **Resolves conflicts** between the proposals
3. **Balances innovation with pragmatism**
4. **Maintains simplicity** while not sacrificing essential features
5. **Addresses critical risks** identified in the critique
6. **Verifies documentation accuracy** - ensure proposals cite `docs/` for current command interfaces

**IMPORTANT**: If the Bold and Paranoia proposals diverge significantly (fundamentally different approaches), you MUST provide multiple plan options instead of forcing a single consensus. This gives the developer choice.

## Input: Combined Report

Below is the combined report containing all three perspectives:

---

{{COMBINED_REPORT}}

---

## Output Requirements

**First, determine if consensus is achievable:**
- If Bold and Paranoia proposals are compatible (similar direction, different details) → Generate single consensus plan
- If Bold and Paranoia proposals diverge significantly (fundamentally different approaches) → Generate multiple plan options

### Option A: Single Consensus Plan (when perspectives align)

Generate a final implementation plan that follows the plan-guideline structure and rules:
- **Design-first TDD ordering**: Documentation → Tests → Implementation (never invert).
- **Use code diffs** in implementation steps (not LOC estimates).
- **Be concrete**: cite exact repo-relative files/sections; avoid vague audit steps.
- **Include dependencies** for each step so ordering is enforced.
- **For every step, list correspondence** to documentation and test cases (what it updates, depends on, or satisfies).
- **If this is a bug fix**, include Bug Reproduction (or explicit skip reason).

### Option B: Multiple Plan Options (when perspectives diverge)

Generate 2-3 alternative plans, each complete and implementable:
- **Plan A (Conservative)**: Based primarily on Bold proposal with Proposal-Reducer simplifications. Minimal changes, lower risk.
- **Plan B (Balanced)**: Hybrid approach incorporating elements from both proposals. Middle ground.
- **Plan C (Aggressive)**: Based primarily on Paranoia proposal with Code-Reducer optimizations. Maximum refactoring, higher reward/risk.

Each plan should follow the same structure as the single consensus plan.

```markdown
# Implementation Plan: {{FEATURE_NAME}}

## Consensus Status

**Consensus achieved**: [Yes/No]
**Reason**: [If No, explain why perspectives diverge significantly]
**Plans provided**: [1 if consensus, 2-3 if divergent]

## Consensus Summary

[2-3 sentences explaining the balanced approach chosen, or why multiple plans are needed]

## Goal
[1-2 sentence problem statement]

**Success criteria:**
- [Criterion 1]
- [Criterion 2]

**Out of scope:**
- [What we're not doing]
- However, it it a good idea for future work?
  - If so, briefly describe it here. ✅ Good to have in the future: Briefly describe it in 1-2 sentences.
  - If not, explain why it's excluded. ❌ Not needed: Explain why it is a bad idea.

## Bug Reproduction
*(Optional - include only for bug fixes where reproduction was attempted)*

**Steps tried:**
- [Command or action performed]
- [Files examined]

**Observed symptoms:**
- [Error messages, test failures, unexpected behavior]

**Environment snapshot:**
- [Relevant file state, dependencies, configuration]

**Root cause hypothesis:**
- [Diagnosis based on observations]

**Skip reason** *(if reproduction not attempted)*:
- [Why reproduction was skipped]

**Unreproducible constraints** *(if reproduction failed)*:
- [What was tried and why it didn't reproduce]
- [Hypothesis for proceeding without reproduction]

## Codebase Analysis

**Files verified (docs/code checked by agents):**
- [File path 1]: [What was verified]
- [File path 2]: [What was verified]

**File changes:**

| File | Level | Purpose |
|------|-------|---------|
| `path/to/file1` | major | Significant changes description |
| `path/to/file2` | medium | Moderate changes description |
| `path/to/file3` | minor | Small changes description |
| `path/to/new/file` (new) | major | New file purpose |
| `path/to/deprecated/file` | remove | Reason for removal |

**Modification level definitions:**
- **minor**: Cosmetic or trivial changes (comments, formatting, <10 LOC changed)
- **medium**: Moderate changes to existing logic (10-50 LOC, no interface changes)
- **major**: Significant structural changes (>50 LOC, interface changes, or new files)
- **remove**: File deletion

**Current architecture notes:**
[Key observations about existing code]

## Interface Design

**New interfaces:**
- Interface signatures and descriptions. Especially talk about:
  - Exposed functionalities to internal use or user usage
  - Internal implmentation based on the complexity
    - If it is less than 20 LoC, you can just talk about the semantics of the interface omit this
    - If it is with for loop and complicated conditional logics, put the steps here:
      - Step 1: Get ready for input
      - Step 2: Iterate over the input
        - Step 2.1: Check condition A
        - Step 2.2: Check condition B
        - Step 2.3: If condition A and B met, do X, if not go back to Step 2
        - Step 2.3: Return output based on conditionals
      - Step 3: Return final output
  - If any data structures or bookkeepings are needed, describe them here
    - What attributes are needed?
    - What are they recording?
    - Do they have any member methods associated?

**Modified interfaces:**
- [Before/after comparisons]
- It is preferred to have `diff` format if the change is less than 20 LoC:
```diff
- old line 1
- old line 2
+ new line 1
+ new line 2
```

**Documentation changes:**
- [Doc files to update with sections]

## Documentation Planning

**REQUIRED**: Explicitly identify all documentation impacts using these categories:

**High-level design docs (docs/):**
- `docs/workflows/*.md` — workflow and process documentation
- `docs/tutorial/*.md` — tutorial and getting-started guides
- `docs/architecture/*.md` — architectural design docs

**Folder READMEs:**
- `path/to/module/README.md` — module purpose and organization

**Interface docs:**
- Source file companion `.md` files documenting interfaces

Each document modifications should be as details as using `diff` format:
```diff
- Old document on interface(a, b, c)
+ New document on new_interface(a, b, c, d)
+ d handles the new feature by...
```

**Format:**
```markdown
## Documentation Planning

### High-level design docs (docs/)
- `docs/path/to/doc.md` — create/update [brief rationale]

### Folder READMEs
- `path/to/README.md` — update [what aspect]

### Interface docs
- `src/module/component.md` — update [which interfaces]
```

**Citation requirement:** When referencing existing command interfaces (e.g., `/ultra-planner`, `/issue-to-impl`), cite the actual `docs/` files (e.g., `docs/workflows/ultra-planner.md`, `docs/tutorial/02-issue-to-impl.md`) to ensure accuracy.

## Test Strategy

**Test modifications:**
- `test/file1` - What to test
  - Test case: Description
  - Test case: Description

**New test files:**
- `test/new_file` - Purpose
  - Test case: Description
  - Test case: Description

**Test data required:**
- [Fixtures, sample data, etc.]

## Implementation Steps

**Step 1: [Documentation change]**
- File changes with code diffs:
```diff
- old content
+ new content
```
Dependencies: None
Correspondence:
- Docs: [What this step adds/updates]
- Tests: [N/A or what this enables]

**Step 2: [Test case changes]**
- File changes with code diffs:
```diff
+ new test content
```
Dependencies: Step 1
Correspondence:
- Docs: [Which doc changes define these tests]
- Tests: [New/updated cases introduced here]

**Step 3: [Implementation change]**
- File changes with code diffs:
```diff
- old implementation
+ new implementation
```
Dependencies: Step 2
Correspondence:
- Docs: [Which doc behaviors are implemented here]
- Tests: [Which test cases this step satisfies]

...

**Recommended approach:** [Single session / Milestone commits]
**Milestone strategy** *(only if large)*:
- **M1**: [What to complete in milestone 1]
- **M2**: [What to complete in milestone 2]
- **Delivery**: [Final deliverable]

## Key Decisions from Agents

**From Bold Proposer:**
- [What was accepted and why]
- [What was rejected and why]

**From Paranoia Proposer:**
- [What was accepted and why]
- [What was rejected and why]

**From Critique:**
- [Risks addressed]
- [Risks accepted with mitigation]

**From Proposal Reducer:**
- [Simplifications applied]
- [Simplifications rejected and why]

**From Code Reducer:**
- [Code reductions applied]
- [Growth accepted and why]

## Success Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | [H/M/L] | [H/M/L] | [How to mitigate] |
| [Risk 2] | [H/M/L] | [H/M/L] | [How to mitigate] |

## Dependencies

[Any external dependencies or requirements]
```

### Multiple Plans Template (when consensus not achieved)

If perspectives diverge significantly, use this structure:

```markdown
# Implementation Plans: {{FEATURE_NAME}}

## Consensus Status

**Consensus achieved**: No
**Reason**: [Explain why Bold and Paranoia approaches are fundamentally incompatible]
**Plans provided**: [2 or 3]

---

# Plan A: Conservative (Minimal Changes)

## Summary
[Based primarily on Bold proposal with Proposal-Reducer simplifications]

[Full plan structure as above...]

---

# Plan B: Balanced (Middle Ground)

## Summary
[Hybrid approach incorporating elements from both proposals]

[Full plan structure as above...]

---

# Plan C: Aggressive (Maximum Refactoring)

## Summary
[Based primarily on Paranoia proposal with Code-Reducer optimizations]

[Full plan structure as above...]

---

## Recommendation

**Suggested plan**: [A/B/C]
**Rationale**: [Why this plan is recommended based on risk/reward analysis]

**When to choose Plan A:**
- [Conditions favoring conservative approach]

**When to choose Plan B:**
- [Conditions favoring balanced approach]

**When to choose Plan C:**
- [Conditions favoring aggressive approach]
```

## Evaluation Criteria

Your consensus plan(s) should:

✅ **Be balanced**: Not too bold, not too conservative (unless multiple plans provided)
✅ **Be practical**: Implementable with available tools/time
✅ **Be complete**: Include all essential components
✅ **Be clear**: Unambiguous implementation steps with code diffs
✅ **Address risks**: Mitigate critical concerns from critique
✅ **Stay simple**: Remove unnecessary complexity per reducers
✅ **Use code diffs**: Show concrete changes, not just LOC estimates
✅ **Accurate modification levels**: Every file must have correct level (minor/medium/major/remove)
✅ **Provide choice**: When perspectives diverge, give multiple plan options

❌ **Avoid**: Over-engineering, ignoring risks, excessive scope creep, vague specifications, or "audit the codebase" steps
❌ **Avoid**: Forcing consensus when Bold and Paranoia approaches are fundamentally incompatible

## Final Privacy Note

As this plan will be published in a Github Issue, ensure no sensitive or proprietary information is included.

- No absolute paths from `/` or `~` or some other user-specific directories included
  - Use relative path from the root of the repo instead
- No API keys, tokens, or credentials
- No internal project names or codenames
- No personal data of any kind of users or developers
- No confidential business information
