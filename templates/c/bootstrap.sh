#!/bin/bash

# Bootstrap script for C SDK template
# This script initializes the SDK by making necessary modifications to the template files
# After completion, it deletes itself

set -e

echo "Bootstrapping C SDK..."

# Get environment variables passed from make agentize
PROJECT_NAME="${AGENTIZE_PROJECT_NAME:-unknown}"
SOURCE_PATH="${AGENTIZE_SOURCE_PATH:-src}"

echo "  Project name: $PROJECT_NAME"
echo "  Source path: $SOURCE_PATH"

# If custom source path is specified, rename src/ directory and update references
if [ "$SOURCE_PATH" != "src" ]; then
    if [ -d "src" ]; then
        echo "  Renaming src/ to $SOURCE_PATH/..."
        mv src "$SOURCE_PATH"

        # Update CMakeLists.txt to reference the new source path
        if [ -f "CMakeLists.txt" ]; then
            sed -i.bak "s|src/|$SOURCE_PATH/|g" CMakeLists.txt
            rm -f CMakeLists.txt.bak
            echo "  Updated CMakeLists.txt"
        fi
    else
        echo "  Warning: src/ directory not found, skipping rename"
    fi
fi

# Parameterize git-msg-tags.md if it's a template
if [ -f "docs/git-msg-tags.md.template" ]; then
    echo "  Parameterizing docs/git-msg-tags.md..."
    sed -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" \
        -e "/{{#if_c_or_cxx}}/d" \
        -e "/{{\/if_c_or_cxx}}/d" \
        -e "/{{#if_python}}/,/{{\/if_python}}/d" \
        docs/git-msg-tags.md.template > docs/git-msg-tags.md
    rm docs/git-msg-tags.md.template
fi

echo "Bootstrap completed successfully!"

# Delete this bootstrap script using AGENTIZE_PROJECT_PATH
if [ -n "$AGENTIZE_PROJECT_PATH" ]; then
    echo "Cleaning up bootstrap script..."
    rm -f "$AGENTIZE_PROJECT_PATH/bootstrap.sh"
fi
