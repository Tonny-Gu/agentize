# Sandbox

Development environment container for agentize SDK with tmux-based session management.

## Purpose

This directory contains the Docker sandbox environment used for:
- Testing the agentize SDK in a controlled environment
- Development workflows requiring isolated dependencies
- CI/CD pipeline validation
- **Persistent, detachable Claude/CCR sessions via tmux**

## Contents

- `Dockerfile` - Docker image definition with all required tools (including tmux)
- `install.sh` - Claude Code installation script (copied into container)
- `entrypoint.sh` - Container entrypoint with tmux session support
- `run.py` - Python-based sandbox manager with subcommand architecture
- `pyproject.toml` - Python project configuration

## User

The container runs with UID/GID mapping to match the host user, ensuring worktrees are readable/writable both inside and outside the container.

## Installed Tools

- Node.js 20.x LTS
- Python 3.12 with uv package manager
- SDKMAN for Java/SDK management
- Git, curl, wget, and other base utilities
- Playwright with bundled Chromium
- claude-code-router
- Claude Code
- GitHub CLI
- **tmux** (for persistent sessions)

## Container Runtime

This sandbox supports both Docker and Podman. The runtime is detected in priority order:

1. **Local config file**: `sandbox/agentize.toml` or `./agentize.toml`
2. **Global config file**: `~/.config/agentize/agentize.toml`
3. **CONTAINER_RUNTIME** environment variable
4. **Auto-detection**: Podman preferred if available, falls back to Docker

### Local Config File Format

Create `sandbox/agentize.toml`:

```toml
[container]
runtime = "podman"  # or "docker"
```

## Automatic Build

The `run.py` script automatically handles container image building:

- **First run**: Builds the image automatically if it doesn't exist
- **File changes**: Rebuilds when `Dockerfile`, `install.sh`, or `entrypoint.sh` change
- **Force rebuild**: Use `--build` flag to force a rebuild

## CLI Interface

```
run.py --repo_base <base_path> <subcommand> [options]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `new -n <name> [--ccr] [-b <branch>]` | Create new worktree + container |
| `ls` | List all worktree + container combinations |
| `rm -n <name>` | Delete worktree + container |
| `attach -n <name>` | Attach to tmux session via exec -it |

### Examples

```bash
# Create a new sandbox with worktree
uv run sandbox/run.py --repo_base /path/to/repo new -n feature-x -b main

# Create sandbox in CCR mode
uv run sandbox/run.py --repo_base /path/to/repo new -n feature-y --ccr

# List all sandboxes
uv run sandbox/run.py --repo_base /path/to/repo ls

# Attach to a running sandbox
uv run sandbox/run.py --repo_base /path/to/repo attach -n feature-x

# Remove a sandbox
uv run sandbox/run.py --repo_base /path/to/repo rm -n feature-x
```

## Directory Structure

```
<repo_base>/
├── .git/                    # Main git repository
├── .wt/                     # Worktrees directory
│   ├── feature-x/           # Worktree for sandbox "feature-x"
│   └── ...
├── .sandbox_db.sqlite       # Sandbox state database
└── ...
```

## State Management

Sandbox state is stored in `<repo_base>/.sandbox_db.sqlite`:

```sql
CREATE TABLE sandboxes (
    name TEXT PRIMARY KEY,
    branch TEXT NOT NULL,
    container_id TEXT,
    worktree_path TEXT NOT NULL,
    ccr_mode INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Build

```bash
# Build/rebuild the image (uses local config or auto-detection)
make sandbox-build
uv ./sandbox/run.py --build

# Build with custom architecture
podman build --build-arg HOST_ARCH=arm64 -t agentize-sandbox ./sandbox
```

## Volume Mounts

The sandbox automatically mounts:
- `~/.claude-code-router/config.json` -> container CCR config (read-only)
- `~/.config/gh/` -> container GH CLI config (read-only)
- `~/.git-credentials` -> container git credentials (read-only)
- `~/.gitconfig` -> container git config (read-only)
- Worktree directory -> `/workspace` (read-write)
- `GITHUB_TOKEN` environment variable (if set)

## UID/GID Mapping

Container user matches host user for seamless file access:

**Docker:**
```bash
docker run --user $(id -u):$(id -g) ...
```

**Podman:**
```bash
podman run --userns=keep-id ...
```

## Tmux Session

Each sandbox runs a tmux session named `main` inside the container. This enables:
- Detaching from sessions without stopping the container
- Attaching from multiple terminals
- Persistent work state across reconnections

## Testing

```bash
# Run sandbox session management tests
./tests/sandbox-session-test.sh

# Run PATH verification tests
./tests/sandbox-path-test.sh

# Run full sandbox build and verification tests
./tests/e2e/test-sandbox-build.sh
```