#!/bin/bash

# Bootstrap script for Python SDK template
# This script initializes the SDK by making necessary modifications to the template files
# After completion, it deletes itself

set -e

echo "Bootstrapping Python SDK..."

# Get environment variables passed from make agentize
PROJECT_NAME="${AGENTIZE_PROJECT_NAME:-unknown}"
SOURCE_PATH="${AGENTIZE_SOURCE_PATH:-src}"

echo "  Project name: $PROJECT_NAME"
echo "  Source path: $SOURCE_PATH"

# Rename project_name directory to actual project name
if [ -d "project_name" ]; then
    echo "  Renaming project_name/ to $PROJECT_NAME/..."
    mv project_name "$PROJECT_NAME"

    # Update test file to import the correct module name
    if [ -f "tests/test_main.py" ]; then
        sed -i.bak "s/project_name/$PROJECT_NAME/g" tests/test_main.py
        rm -f tests/test_main.py.bak
        echo "  Updated tests/test_main.py"
    fi
else
    echo "  Warning: project_name/ directory not found, skipping rename"
fi

# Parameterize git-msg-tags.md if it's a template
if [ -f "docs/git-msg-tags.md.template" ]; then
    echo "  Parameterizing docs/git-msg-tags.md..."
    sed -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" \
        -e "/{{#if_python}}/d" \
        -e "/{{\/if_python}}/d" \
        -e "/{{#if_c_or_cxx}}/,/{{\/if_c_or_cxx}}/d" \
        docs/git-msg-tags.md.template > docs/git-msg-tags.md
    rm docs/git-msg-tags.md.template
fi

echo "Bootstrap completed successfully!"

# Delete this bootstrap script using AGENTIZE_PROJECT_PATH
if [ -n "$AGENTIZE_PROJECT_PATH" ]; then
    echo "Cleaning up bootstrap script..."
    rm -f "$AGENTIZE_PROJECT_PATH/bootstrap.sh"
fi
