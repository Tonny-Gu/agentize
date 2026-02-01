#!/usr/bin/env bash
# Test: _planner_render_prompt with multiple context files

source "$(dirname "$0")/../common.sh"

PLANNER_CLI="$PROJECT_ROOT/src/cli/planner.sh"

test_info "_planner_render_prompt handles multiple context files"

export AGENTIZE_HOME="$PROJECT_ROOT"
source "$PLANNER_CLI"

TMP_DIR=$(make_temp_dir "test-render-prompt-multi-$$")
trap 'cleanup_dir "$TMP_DIR"' EXIT

# Create mock context files
echo "# First Context" > "$TMP_DIR/context1.txt"
echo "Content from first stage" >> "$TMP_DIR/context1.txt"

echo "# Second Context" > "$TMP_DIR/context2.txt"
echo "Content from second stage" >> "$TMP_DIR/context2.txt"

echo "# Third Context" > "$TMP_DIR/context3.txt"
echo "Content from third stage" >> "$TMP_DIR/context3.txt"

# Test with multiple context files
OUTPUT_FILE="$TMP_DIR/rendered-prompt.md"
FEATURE_DESC="Test feature for multi-input"

_planner_render_prompt "$OUTPUT_FILE" \
    ".claude-plugin/agents/proposal-critique.md" \
    "true" \
    "$FEATURE_DESC" \
    "$TMP_DIR/context1.txt" \
    "$TMP_DIR/context2.txt" \
    "$TMP_DIR/context3.txt"

# Verify all context files were included
grep -q "# Previous Stage Output" "$OUTPUT_FILE" || \
    test_fail "Missing 'Previous Stage Output' header"

grep -q "# Additional Context (2)" "$OUTPUT_FILE" || \
    test_fail "Missing 'Additional Context (2)' header"

grep -q "# Additional Context (3)" "$OUTPUT_FILE" || \
    test_fail "Missing 'Additional Context (3)' header"

grep -q "Content from first stage" "$OUTPUT_FILE" || \
    test_fail "Missing first context content"

grep -q "Content from second stage" "$OUTPUT_FILE" || \
    test_fail "Missing second context content"

grep -q "Content from third stage" "$OUTPUT_FILE" || \
    test_fail "Missing third context content"

grep -q "Test feature for multi-input" "$OUTPUT_FILE" || \
    test_fail "Missing feature description"

test_pass "_planner_render_prompt handles multiple context files"
