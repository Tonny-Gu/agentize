#!/usr/bin/env bash
# Test: Makefile help target documents env targets

source "$(dirname "$0")/../common.sh"

test_info "Makefile help target documents env targets"

cd "$PROJECT_ROOT"

# Clear MAKEFLAGS to avoid jobserver inheritance issues when invoked via make
unset MAKEFLAGS MAKELEVEL

# Capture make help output
HELP_OUTPUT=$(make help 2>&1)

# Verify env target is documented in help
if ! echo "$HELP_OUTPUT" | grep -q "make env"; then
  test_fail "make help missing 'make env' documentation"
fi

# Verify eval usage hint is present
if ! echo "$HELP_OUTPUT" | grep -q "eval"; then
  test_fail "make help missing eval usage hint for env target"
fi

test_pass "make help documents env targets"
