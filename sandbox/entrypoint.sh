#!/bin/bash
# Entrypoint script for agentize container
#
# Supports multiple modes:
# - Default: Runs 'claude' with plugin support
# - With --ccr flag: Runs 'ccr code' with plugin support
# - With --tmux flag: Runs command inside tmux session 'main'

# =============================================================================
# Fix permissions for mounted config files
# =============================================================================
# Issue #17: Host files may have restrictive permissions (600) that prevent
# the container's agentizer user from reading them. We copy them to a temp
# location and fix permissions.

fix_gh_config() {
    local src="$1"
    local dest="$2"
    if [ -f "$src" ]; then
        # Use sudo to read the file (in case it's mounted with host permissions)
        # and write to a temporary location that agentizer owns
        /usr/bin/sudo cp "$src" "$dest"
        /usr/bin/sudo chown agentizer:agentizer "$dest"
        chmod 600 "$dest"
    fi
}

# Fix GitHub CLI config permissions
if [ -d "/home/agentizer/.config/gh" ]; then
    GH_CONFIG_DIR="/home/agentizer/.config/gh"
    GH_TEMP_DIR="/tmp/gh-config"
    mkdir -p "$GH_TEMP_DIR"
    
    # Copy and fix permissions for gh config files
    fix_gh_config "$GH_CONFIG_DIR/config.yml" "$GH_TEMP_DIR/config.yml"
    fix_gh_config "$GH_CONFIG_DIR/hosts.yml" "$GH_TEMP_DIR/hosts.yml"
    
    # Override GH_CONFIG_DIR environment variable to use our temp location
    export GH_CONFIG_DIR="$GH_TEMP_DIR"
fi

# Fix CCR config permissions
CCR_DIR="/home/agentizer/.claude-code-router"

# Create CCR directory structure if it doesn't exist (logs dir needs to be writable)
# Silence errors for read-only mounted files - we only need the logs directory
/usr/bin/sudo mkdir -p "$CCR_DIR/logs" 2>/dev/null
/usr/bin/sudo chown -R agentizer:agentizer "$CCR_DIR" 2>/dev/null || true

# If config files are mounted with restrictive permissions, copy them with proper permissions
if [ -f "$CCR_DIR/config.json" ]; then
    if ! head -c 1 "$CCR_DIR/config.json" >/dev/null 2>&1; then
        # File is not readable, need to copy with sudo
        CCR_TEMP_DIR="/tmp/ccr-config"
        mkdir -p "$CCR_TEMP_DIR"
        /usr/bin/sudo cp "$CCR_DIR/config.json" "$CCR_TEMP_DIR/config.json"
        /usr/bin/sudo chown agentizer:agentizer "$CCR_TEMP_DIR/config.json"
        chmod 600 "$CCR_TEMP_DIR/config.json"
        export CCR_CONFIG_PATH="$CCR_TEMP_DIR/config.json"
    fi
fi

if [ -f "$CCR_DIR/config-router.json" ]; then
    if ! head -c 1 "$CCR_DIR/config-router.json" >/dev/null 2>&1; then
        # File is not readable, need to copy with sudo
        CCR_TEMP_DIR="/tmp/ccr-config"
        mkdir -p "$CCR_TEMP_DIR"
        /usr/bin/sudo cp "$CCR_DIR/config-router.json" "$CCR_TEMP_DIR/config-router.json"
        /usr/bin/sudo chown agentizer:agentizer "$CCR_TEMP_DIR/config-router.json"
        chmod 600 "$CCR_TEMP_DIR/config-router.json"
        export CCR_ROUTER_CONFIG_PATH="$CCR_TEMP_DIR/config-router.json"
    fi
fi

# =============================================================================
# Configure Claude CLI to auto-approve API keys and skip onboarding
# =============================================================================
# Add empty key ("") and current ANTHROPIC_API_KEY to approved list in ~/.claude.json
# Also set hasCompletedOnboarding to skip the initial setup wizard
CLAUDE_CONFIG="$HOME/.claude.json"
if command -v jq >/dev/null 2>&1; then
    # Get last 20 chars of API key (for privacy, Claude only stores suffix)
    API_KEY_SUFFIX="${ANTHROPIC_API_KEY: -20}"
    
    # Update claude.json to:
    # 1. Approve both empty key and current API key
    # 2. Set hasCompletedOnboarding to true
    (cat "$CLAUDE_CONFIG" 2>/dev/null || echo 'null') | \
        jq --arg key "$API_KEY_SUFFIX" '(. // {}) | .hasCompletedOnboarding = true | .customApiKeyResponses.approved |= ([.[]?, "", $key] | unique)' \
        > "$CLAUDE_CONFIG.tmp" && mv "$CLAUDE_CONFIG.tmp" "$CLAUDE_CONFIG"
fi

# =============================================================================
# Parse arguments
# =============================================================================
HAS_CCR=0
HAS_CMD=0
HAS_TMUX=0
ARGS=()

for arg in "$@"; do
    if [ "$arg" = "--ccr" ]; then
        HAS_CCR=1
    elif [ "$arg" = "--cmd" ]; then
        HAS_CMD=1
    elif [ "$arg" = "--tmux" ]; then
        HAS_TMUX=1
    else
        ARGS+=("$arg")
    fi
done

if [ $HAS_CMD -eq 1 ]; then
    # Custom command mode - execute the provided command
    exec "${ARGS[@]}"
elif [ $HAS_TMUX -eq 1 ]; then
    # Tmux session mode - create session and keep container running
    SESSION_NAME="main"

    # Use /tmp for socket
    SOCKET_PATH="/tmp/tmux-main"

    # Build the command to run inside tmux
    if [ $HAS_CCR -eq 1 ]; then
        TMUX_CMD="cd /workspace && ccr code --dangerously-skip-permissions --plugin-dir .claude-plugin ${ARGS[*]}"
    else
        TMUX_CMD="cd /workspace && claude --dangerously-skip-permissions --plugin-dir .claude-plugin ${ARGS[*]}"
    fi

    # Create tmux session
    tmux -S "$SOCKET_PATH" new-session -d -s "$SESSION_NAME" "$TMUX_CMD"
    
    # Make socket accessible to all users  
    chmod 777 "$SOCKET_PATH" 2>/dev/null || true
    
    # Keep container alive - wait forever until terminated
    exec tail -f /dev/null
elif [ $HAS_CCR -eq 1 ]; then
    exec ccr code --dangerously-skip-permissions --plugin-dir .claude-plugin "${ARGS[@]}"
else
    exec claude --dangerously-skip-permissions --plugin-dir .claude-plugin "$@"
fi
