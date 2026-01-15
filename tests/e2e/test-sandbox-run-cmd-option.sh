#!/bin/bash

set -e

echo "=== Testing sandbox run.sh --cmd option ==="

# Build the Docker image first (required by run.sh)
echo "Building Docker image..."
docker build -t agentize-sandbox ./sandbox

# Test 1: Verify run.sh exists and is executable
echo "Test 1: Verifying run.sh exists and is executable..."
if [ ! -x "./sandbox/run.sh" ]; then
    echo "FAIL: sandbox/run.sh is not executable"
    exit 1
fi
echo "PASS: run.sh is executable"

# Test 2: Non-interactive command execution
echo "Test 2: Testing non-interactive command execution..."
OUTPUT=$(./sandbox/run.sh -- --cmd ls /workspace 2>&1)
if echo "$OUTPUT" | grep -q "agentize"; then
    echo "PASS: --cmd ls /workspace executed successfully"
else
    echo "FAIL: Non-interactive command failed"
    echo "Output: $OUTPUT"
    exit 1
fi

# Test 3: Command with arguments
echo "Test 3: Testing command with arguments..."
OUTPUT=$(./sandbox/run.sh -- --cmd bash -c "echo hello && pwd" 2>&1)
if echo "$OUTPUT" | grep -q "hello" && echo "$OUTPUT" | grep -q "/workspace"; then
    echo "PASS: Command with arguments executed successfully"
else
    echo "FAIL: Command with arguments failed"
    echo "Output: $OUTPUT"
    exit 1
fi

# Test 4: Which command
echo "Test 4: Testing 'which' command..."
OUTPUT=$(./sandbox/run.sh -- --cmd which gh 2>&1)
if echo "$OUTPUT" | grep -q "gh"; then
    echo "PASS: 'which gh' executed successfully"
else
    echo "FAIL: 'which gh' failed"
    echo "Output: $OUTPUT"
    exit 1
fi

# Test 5: Normal mode still works (--help)
echo "Test 5: Testing normal mode (--help)..."
OUTPUT=$(./sandbox/run.sh -- --help 2>&1)
if echo "$OUTPUT" | grep -q "Usage:"; then
    echo "PASS: Normal mode still works"
else
    echo "FAIL: Normal mode broken"
    echo "Output: $OUTPUT"
    exit 1
fi

# Test 6: Verify -it flag is preserved in docker command
# This is a static check - we can't test interactive mode in CI
echo "Test 6: Verifying -it flag handling (static check)..."
if grep -q "INTERACTIVE_FLAGS" ./sandbox/run.sh; then
    echo "PASS: INTERACTIVE_FLAGS handling found in script"
else
    echo "FAIL: INTERACTIVE_FLAGS handling not found"
    exit 1
fi

echo "=== All sandbox run.sh --cmd option tests passed ==="