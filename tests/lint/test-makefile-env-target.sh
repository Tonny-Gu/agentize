#!/usr/bin/env bash
# Test: Makefile env target prints correct environment exports

source "$(dirname "$0")/../common.sh"

test_info "Makefile env target prints correct environment exports"

cd "$PROJECT_ROOT"

# Clear MAKEFLAGS to avoid jobserver inheritance issues when invoked via make
unset MAKEFLAGS MAKELEVEL

# Capture make env output
ENV_OUTPUT=$(make env 2>&1)

# Verify AGENTIZE_HOME export is present with $(CURDIR) resolved
if ! echo "$ENV_OUTPUT" | grep -q 'export AGENTIZE_HOME='; then
  test_fail "make env missing AGENTIZE_HOME export"
fi

# Verify PYTHONPATH export is present
if ! echo "$ENV_OUTPUT" | grep -q 'export PYTHONPATH='; then
  test_fail "make env missing PYTHONPATH export"
fi

# Verify the output is valid shell (can be eval'd without error)
eval "$ENV_OUTPUT" 2>/dev/null
if [ $? -ne 0 ]; then
  test_fail "make env output is not valid shell syntax"
fi

# Verify AGENTIZE_HOME was actually set after eval
if [ -z "$AGENTIZE_HOME" ]; then
  test_fail "AGENTIZE_HOME not set after eval \$(make env)"
fi

test_pass "make env prints valid environment exports"
