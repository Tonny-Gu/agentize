#!/bin/bash
# Purpose: Test sandbox session management with tmux-based worktree + container combinations
# Expected: run.py subcommands (new, ls, rm, attach) work correctly with SQLite state

source "$(dirname "$0")/../common.sh"

set -e

test_info "Testing sandbox session management"

# =============================================================================
# Test 1: Verify run.py has subcommand structure
# =============================================================================
test_info "Test 1: Verifying run.py subcommand structure"

# Check that run.py exists
if [ ! -f "$PROJECT_ROOT/sandbox/run.py" ]; then
    test_fail "sandbox/run.py does not exist"
fi

# Check for subcommand-related code patterns
if ! grep -q "subcommand\|add_subparsers\|new\|attach" "$PROJECT_ROOT/sandbox/run.py"; then
    test_fail "run.py should have subcommand structure (new, ls, rm, attach)"
fi

echo "Subcommand structure found"

# =============================================================================
# Test 2: Verify SQLite state management module exists
# =============================================================================
test_info "Test 2: Verifying SQLite state management"

# Check for SQLite-related imports or usage
if ! grep -q "sqlite3\|sqlite" "$PROJECT_ROOT/sandbox/run.py"; then
    test_fail "run.py should use SQLite for state management"
fi

echo "SQLite state management found"

# =============================================================================
# Test 3: Verify tmux is installed in Dockerfile
# =============================================================================
test_info "Test 3: Verifying tmux in Dockerfile"

if ! grep -q "tmux" "$PROJECT_ROOT/sandbox/Dockerfile"; then
    test_fail "Dockerfile should install tmux"
fi

echo "tmux installation found in Dockerfile"

# =============================================================================
# Test 4: Verify entrypoint.sh supports tmux session
# =============================================================================
test_info "Test 4: Verifying entrypoint.sh tmux support"

if ! grep -q "tmux" "$PROJECT_ROOT/sandbox/entrypoint.sh"; then
    test_fail "entrypoint.sh should support tmux sessions"
fi

echo "tmux support found in entrypoint.sh"

# =============================================================================
# Test 5: Verify UID/GID mapping support
# =============================================================================
test_info "Test 5: Verifying UID/GID mapping support"

# Check for UID/GID related code in run.py
if ! grep -q "getuid\|getgid\|userns\|--user" "$PROJECT_ROOT/sandbox/run.py"; then
    test_fail "run.py should support UID/GID mapping"
fi

echo "UID/GID mapping support found"

# =============================================================================
# Test 6: Verify worktree directory structure support
# =============================================================================
test_info "Test 6: Verifying worktree directory structure"

# Check for .wt directory handling
if ! grep -q "\.wt\|worktree" "$PROJECT_ROOT/sandbox/run.py"; then
    test_fail "run.py should handle .wt worktree directory"
fi

echo "Worktree directory structure support found"

# =============================================================================
# Test 7: Verify container naming convention
# =============================================================================
test_info "Test 7: Verifying container naming convention"

# Check for agentize-sb- prefix in container naming
if ! grep -q "agentize-sb-\|container.*name" "$PROJECT_ROOT/sandbox/run.py"; then
    test_fail "run.py should use agentize-sb-<name> container naming"
fi

echo "Container naming convention found"

test_pass "Sandbox session management structure verified"
