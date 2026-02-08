#!/usr/bin/env bash
# Test: Template Makefiles have env, env-script, and help targets

source "$(dirname "$0")/../common.sh"

test_info "Template Makefiles have env, env-script, and help targets"

TEMPLATES_DIR="$PROJECT_ROOT/templates"
FAILED=0

for lang in python c cxx; do
  MAKEFILE="$TEMPLATES_DIR/$lang/Makefile"

  if [ ! -f "$MAKEFILE" ]; then
    echo "FAIL: $MAKEFILE not found"
    FAILED=1
    continue
  fi

  # Check env target exists
  if ! grep -q '^env:' "$MAKEFILE"; then
    echo "FAIL: $lang/Makefile missing env target"
    FAILED=1
  fi

  # Check env-script target exists
  if ! grep -q '^env-script:' "$MAKEFILE"; then
    echo "FAIL: $lang/Makefile missing env-script target"
    FAILED=1
  fi

  # Check help target exists
  if ! grep -q '^help:' "$MAKEFILE"; then
    echo "FAIL: $lang/Makefile missing help target"
    FAILED=1
  fi

  # Check env target exports PROJECT_ROOT
  if ! grep -q 'PROJECT_ROOT' "$MAKEFILE"; then
    echo "FAIL: $lang/Makefile env target missing PROJECT_ROOT"
    FAILED=1
  fi

  # Check env-script generates setup.sh
  if ! grep -q 'setup.sh' "$MAKEFILE"; then
    echo "FAIL: $lang/Makefile env-script doesn't generate setup.sh"
    FAILED=1
  fi

  # Check .PHONY includes new targets
  if ! grep -q '^\.PHONY:.*env' "$MAKEFILE"; then
    echo "FAIL: $lang/Makefile .PHONY missing env"
    FAILED=1
  fi
done

# Verify language-specific exports
# Python: PYTHONPATH
if ! grep -q 'PYTHONPATH' "$TEMPLATES_DIR/python/Makefile"; then
  echo "FAIL: python/Makefile missing PYTHONPATH in env target"
  FAILED=1
fi

# C: C_INCLUDE_PATH
if ! grep -q 'C_INCLUDE_PATH' "$TEMPLATES_DIR/c/Makefile"; then
  echo "FAIL: c/Makefile missing C_INCLUDE_PATH in env target"
  FAILED=1
fi

# C++: CPLUS_INCLUDE_PATH
if ! grep -q 'CPLUS_INCLUDE_PATH' "$TEMPLATES_DIR/cxx/Makefile"; then
  echo "FAIL: cxx/Makefile missing CPLUS_INCLUDE_PATH in env target"
  FAILED=1
fi

if [ $FAILED -ne 0 ]; then
  test_fail "Some template Makefiles missing env/env-script/help targets"
fi

test_pass "All template Makefiles have env, env-script, and help targets with language-specific exports"
