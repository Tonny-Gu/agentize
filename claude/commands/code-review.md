---
name: code-review
description: Review code changes from current HEAD to main/HEAD following review standards
---

# Code Review Command

Execute the review-standard skill to perform comprehensive code review of changes on the current branch.

Invoke the skill: /code-review

## Inputs

**From git:**
- Current branch name (for validation and report header)
- Changed files: `git diff --name-only main...HEAD`
- Full diff: `git diff main...HEAD`

**From repository:**
- Documentation linter: `scripts/lint-documentation.sh`
- Existing utilities for reuse checks
- Project conventions and patterns

## Outputs

**Terminal output:**
- Structured review report with sections:
  - Phase 1: Documentation Quality Review
  - Phase 2: Code Quality & Reuse Review
  - Overall Assessment with recommendations

**Review categories:**
- ✅ APPROVED - Ready for merge
- ⚠️  NEEDS CHANGES - Minor issues to address
- ❌ CRITICAL ISSUES - Must fix before merge

## Skill Integration

### Step 1: Validate Current Branch

Check that the current branch is not main:

```bash
git branch --show-current
```

If on main branch:
```
Error: Cannot review changes on main branch.

Please switch to a development branch (e.g., issue-N-feature-name)
```
Stop execution.

### Step 2: Get Changed Files

Retrieve list of all files changed between main and current HEAD:

```bash
git diff --name-only main...HEAD
```

If no changes found:
```
No changes detected between main and current branch.

Nothing to review.
```
Stop execution.

### Step 3: Get Full Diff

Retrieve complete diff of all changes:

```bash
git diff main...HEAD
```

This provides the full context of changes for the review-standard skill.

### Step 4: Invoke Review-Standard Skill

Execute the review-standard skill with gathered context:

**Inputs to skill:**
- Current branch name
- List of changed files
- Full diff content
- Repository root path

**Skill performs:**
- Phase 1: Documentation Quality Review
  - Validate folder README.md files
  - Check source interface documentation
  - Verify test documentation
  - Check for design documentation needs
  - Run documentation linter

- Phase 2: Code Quality & Reuse Review
  - Check for code duplication
  - Identify local utility reuse opportunities
  - Identify external library reuse opportunities
  - Review imports and dependencies
  - Verify project conventions

**Skill output:**
- Structured review report with findings

### Step 5: Display Review Report

Present the formatted review report to the user with:
- Branch name and change summary
- Phase 1 findings (documentation quality)
- Phase 2 findings (code quality & reuse)
- Overall assessment (APPROVED / NEEDS CHANGES / CRITICAL ISSUES)
- Specific, actionable recommendations

Example output format:
```
# Code Review Report

**Branch**: issue-42-feature-name
**Changed files**: 8 files (+450, -120 lines)

---

## Phase 1: Documentation Quality

### ✅ Passed
- All folders have README.md files

### ❌ Issues Found
- src/utils/parser.py - No parser.md found

---

## Phase 2: Code Quality & Reuse

### ❌ Issues Found
- src/api/handler.py:67 - Reinventing the wheel

---

## Overall Assessment

**Status**: ⚠️  NEEDS CHANGES

**Recommended actions before merge**:
1. Create parser.md documenting interfaces
2. Use existing validate_json() utility
```

## Error Handling

### Not on Git Repository

```bash
git branch --show-current
# Error: not a git repository
```

**Response:**
```
Error: Not in a git repository.

Please run this command from within a git repository.
```
Stop execution.

### Main Branch Detection

```bash
git branch --show-current
# Output: main
```

**Response:**
```
Error: Cannot review changes on main branch.

Please switch to a development branch:
  git checkout -b issue-N-feature-name

Or switch to existing branch:
  git checkout issue-N-feature-name
```
Stop execution.

### No Changes Found

```bash
git diff --name-only main...HEAD
# Output: (empty)
```

**Response:**
```
No changes detected between main and current branch.

Your branch is synchronized with main. Nothing to review.
```
Stop execution.
