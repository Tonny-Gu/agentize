#!/usr/bin/env python3
"""
Sandbox session manager with tmux-based worktree + container management.

This script manages sandboxes that combine:
- Git worktrees for isolated code branches
- Persistent containers with tmux sessions
- SQLite database for state tracking

Subcommands:
- new: Create new worktree + container
- ls: List all sandboxes
- rm: Delete worktree + container
- attach: Attach to tmux session

Container runtime is detected in priority order:
1. Local config file (sandbox/agentize.toml or ./agentize.toml)
2. ~/.config/agentize/agentize.toml config file
3. CONTAINER_RUNTIME environment variable
4. Auto-detection (podman preferred if available)
5. Default to docker
"""

import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Python 3.11+ has tomllib built-in, older versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# Cache file to store image hash for rebuild detection
CACHE_DIR = Path.home() / ".cache" / "agentize"
CACHE_FILE = CACHE_DIR / "sandbox-image.json"

IMAGE_NAME = "agentize-sandbox"

# Files that trigger rebuild when modified (relative to context/sandbox directory)
BUILD_TRIGGER_FILES = [
    "Dockerfile",
    "install.sh",
    "entrypoint.sh",
]

# Container naming prefix
CONTAINER_PREFIX = "agentize-sb-"

# Worktree directory name
WORKTREE_DIR = ".wt"

# Database file name
DB_FILE = ".sandbox_db.sqlite"


# =============================================================================
# SQLite State Management
# =============================================================================


class SandboxDB:
    """SQLite database for sandbox state management."""

    def __init__(self, repo_base: Path):
        self.db_path = repo_base / DB_FILE
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sandboxes (
                    name TEXT PRIMARY KEY,
                    branch TEXT NOT NULL,
                    container_id TEXT,
                    worktree_path TEXT NOT NULL,
                    ccr_mode INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def create(self, name: str, branch: str, worktree_path: str, ccr_mode: bool = False) -> None:
        """Create a new sandbox record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO sandboxes (name, branch, worktree_path, ccr_mode)
                   VALUES (?, ?, ?, ?)""",
                (name, branch, worktree_path, 1 if ccr_mode else 0),
            )
            conn.commit()

    def update_container_id(self, name: str, container_id: str) -> None:
        """Update container ID for a sandbox."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE sandboxes SET container_id = ?, updated_at = ?
                   WHERE name = ?""",
                (container_id, datetime.now().isoformat(), name),
            )
            conn.commit()

    def get(self, name: str) -> Optional[dict]:
        """Get sandbox by name."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sandboxes WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_all(self) -> list[dict]:
        """List all sandboxes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sandboxes ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete(self, name: str) -> None:
        """Delete a sandbox record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sandboxes WHERE name = ?", (name,))
            conn.commit()


def get_container_runtime() -> str:
    """Determine the container runtime to use.

    Priority:
    1. Local config file (sandbox/agentize.toml or ./agentize.toml)
    2. ~/.config/agentize/agentize.toml config file
    3. CONTAINER_RUNTIME environment variable
    4. Auto-detection (podman preferred if available)
    5. Default to docker
    """
    # Priority 1: Local config file
    script_dir = Path(__file__).parent.resolve()
    local_configs = [
        script_dir / "agentize.toml",
        script_dir.parent / "agentize.toml",
    ]
    for config_path in local_configs:
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    config = tomllib.load(f)
                if "container" in config and "runtime" in config["container"]:
                    return config["container"]["runtime"]
            except Exception:
                pass

    # Priority 2: Global config file
    config_path = Path.home() / ".config" / "agentize" / "agentize.toml"
    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
            if "container" in config and "runtime" in config["container"]:
                return config["container"]["runtime"]
        except Exception:
            pass

    # Priority 3: Environment variable
    runtime = os.environ.get("CONTAINER_RUNTIME")
    if runtime:
        return runtime

    # Priority 4: Auto-detection
    if shutil.which("podman"):
        return "podman"

    # Default to docker
    return "docker"


def get_host_architecture() -> str:
    """Map platform.machine() to standard architecture names."""
    arch = platform.machine().lower()

    # Normalize architecture names
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "armv8l": "arm64",
    }
    return arch_map.get(arch, arch)


def is_interactive() -> bool:
    """Check if running interactively (has TTY and not piping)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def calculate_files_hash(files: list[Path]) -> str:
    """Calculate a hash of the contents of the given files."""
    hasher = hashlib.sha256()
    for file_path in files:
        if file_path.exists():
            with open(file_path, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()


def get_image_hash() -> Optional[str]:
    """Get the cached image hash."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
            return data.get("hash")
        except Exception:
            pass
    return None


def save_image_hash(image_hash: str) -> None:
    """Save the image hash to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"hash": image_hash}, f)


def image_exists(runtime: str, image_name: str) -> bool:
    """Check if the container image exists."""
    try:
        subprocess.run(
            [runtime, "image", "inspect", image_name],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def build_image(runtime: str, image_name: str, context: Path) -> bool:
    """Build the container image."""
    print(f"Building {image_name} with {runtime}...", file=sys.stderr)
    try:
        subprocess.run(
            [runtime, "build", "-t", image_name, str(context)],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to build image: {e}", file=sys.stderr)
        return False


def ensure_image(runtime: str, context: Path) -> bool:
    """Ensure the container image exists and is up-to-date."""
    # Check if image exists
    if not image_exists(runtime, IMAGE_NAME):
        print(f"Image {IMAGE_NAME} not found, building...", file=sys.stderr)
        return build_image(runtime, IMAGE_NAME, context)

    # Calculate current hash of build trigger files
    trigger_paths = [context / f for f in BUILD_TRIGGER_FILES]
    current_hash = calculate_files_hash(trigger_paths)
    cached_hash = get_image_hash()

    if cached_hash != current_hash:
        print(f"Build files changed, rebuilding {IMAGE_NAME}...", file=sys.stderr)
        if build_image(runtime, IMAGE_NAME, context):
            save_image_hash(current_hash)
            return True
        return False

    return True


# =============================================================================
# Git Worktree Management
# =============================================================================


def validate_git_repo(repo_base: Path) -> bool:
    """Validate that repo_base is a git repository."""
    git_dir = repo_base / ".git"
    return git_dir.exists()


def create_worktree(repo_base: Path, name: str, branch: str) -> Path:
    """Create a git worktree for the sandbox."""
    wt_dir = repo_base / WORKTREE_DIR
    wt_dir.mkdir(exist_ok=True)

    worktree_path = wt_dir / name

    # Create worktree
    subprocess.run(
        ["git", "-C", str(repo_base), "worktree", "add", str(worktree_path), branch],
        check=True,
    )

    return worktree_path


def remove_worktree(repo_base: Path, name: str) -> None:
    """Remove a git worktree."""
    worktree_path = repo_base / WORKTREE_DIR / name

    if worktree_path.exists():
        subprocess.run(
            ["git", "-C", str(repo_base), "worktree", "remove", str(worktree_path), "--force"],
            check=True,
        )


# =============================================================================
# Container Management
# =============================================================================


def get_container_name(name: str) -> str:
    """Get container name from sandbox name."""
    return f"{CONTAINER_PREFIX}{name}"


def get_uid_gid_args(runtime: str) -> list[str]:
    """Get UID/GID mapping arguments for the container runtime."""
    if runtime == "podman":
        return ["--userns=keep-id"]
    else:
        # Docker
        uid = os.getuid()
        gid = os.getgid()
        return ["--user", f"{uid}:{gid}"]


def container_exists(runtime: str, container_name: str) -> bool:
    """Check if a container exists."""
    try:
        result = subprocess.run(
            [runtime, "container", "inspect", container_name],
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def container_running(runtime: str, container_name: str) -> bool:
    """Check if a container is running."""
    try:
        result = subprocess.run(
            [runtime, "container", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False


def start_container(runtime: str, container_name: str) -> bool:
    """Start a stopped container."""
    try:
        subprocess.run([runtime, "start", container_name], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def stop_container(runtime: str, container_name: str) -> bool:
    """Stop a running container."""
    try:
        subprocess.run([runtime, "stop", container_name], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def remove_container(runtime: str, container_name: str) -> bool:
    """Remove a container."""
    try:
        subprocess.run([runtime, "rm", "-f", container_name], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def create_sandbox_container(
    runtime: str,
    container_name: str,
    worktree_path: Path,
    ccr_mode: bool,
) -> str:
    """Create and start a persistent sandbox container with tmux."""
    cmd = [runtime, "run", "-d"]  # Detached mode, no --rm

    # Interactive mode for tmux
    cmd.extend(["-it"])

    # Container name
    cmd.extend(["--name", container_name])

    # UID/GID mapping
    cmd.extend(get_uid_gid_args(runtime))

    # Volume mounts
    home = Path.home()

    # CCR config
    ccr_config = home / ".claude-code-router" / "config.json"
    if ccr_config.exists():
        cmd.extend(["-v", f"{ccr_config}:/home/agentizer/.claude-code-router/config.json:ro"])
        cmd.extend(["-v", f"{ccr_config}:/home/agentizer/.claude-code-router/config-router.json:ro"])

    # GitHub CLI credentials
    gh_config_yml = home / ".config" / "gh" / "config.yml"
    if gh_config_yml.exists():
        cmd.extend(["-v", f"{gh_config_yml}:/home/agentizer/.config/gh/config.yml:ro"])

    gh_hosts = home / ".config" / "gh" / "hosts.yml"
    if gh_hosts.exists():
        cmd.extend(["-v", f"{gh_hosts}:/home/agentizer/.config/gh/hosts.yml:ro"])

    # Git credentials
    git_creds = home / ".git-credentials"
    if git_creds.exists():
        cmd.extend(["-v", f"{git_creds}:/home/agentizer/.git-credentials:ro"])

    git_config = home / ".gitconfig"
    if git_config.exists():
        cmd.extend(["-v", f"{git_config}:/home/agentizer/.gitconfig:ro"])

    # Worktree directory
    cmd.extend(["-v", f"{worktree_path}:/workspace"])

    # Environment variables
    if "GITHUB_TOKEN" in os.environ:
        cmd.extend(["-e", f"GITHUB_TOKEN={os.environ['GITHUB_TOKEN']}"])

    if not ccr_mode:
        if "ANTHROPIC_API_KEY" in os.environ:
            cmd.extend(["-e", f"ANTHROPIC_API_KEY={os.environ['ANTHROPIC_API_KEY']}"])
        if "ANTHROPIC_BASE_URL" in os.environ:
            cmd.extend(["-e", f"ANTHROPIC_BASE_URL={os.environ['ANTHROPIC_BASE_URL']}"])

    # Working directory
    cmd.extend(["-w", "/workspace"])

    # Image and entrypoint with tmux
    cmd.extend(["--entrypoint", "/usr/local/bin/entrypoint"])
    cmd.append(IMAGE_NAME)
    cmd.append("--tmux")
    if ccr_mode:
        cmd.append("--ccr")

    # Run container
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


# =============================================================================
# Subcommand Handlers
# =============================================================================


def cmd_new(args) -> int:
    """Handle 'new' subcommand: Create new worktree + container."""
    repo_base = Path(args.repo_base).resolve()
    runtime = get_container_runtime()

    # Validate git repo
    if not validate_git_repo(repo_base):
        print(f"Error: {repo_base} is not a git repository", file=sys.stderr)
        return 1

    # Check for name conflicts
    db = SandboxDB(repo_base)
    if db.get(args.name):
        print(f"Error: Sandbox '{args.name}' already exists", file=sys.stderr)
        return 1

    # Ensure image exists
    script_dir = Path(__file__).parent.resolve()
    if not ensure_image(runtime, script_dir):
        print("Failed to ensure container image", file=sys.stderr)
        return 1

    print(f"Creating sandbox '{args.name}' on branch '{args.branch}'...")

    # Create worktree
    try:
        worktree_path = create_worktree(repo_base, args.name, args.branch)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create worktree: {e}", file=sys.stderr)
        return 1

    # Record in database
    db.create(args.name, args.branch, str(worktree_path), args.ccr)

    # Create container
    container_name = get_container_name(args.name)
    try:
        container_id = create_sandbox_container(
            runtime, container_name, worktree_path, args.ccr
        )
        db.update_container_id(args.name, container_id)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create container: {e}", file=sys.stderr)
        # Cleanup worktree on failure
        remove_worktree(repo_base, args.name)
        db.delete(args.name)
        return 1

    print(f"Sandbox '{args.name}' created successfully")
    print(f"  Worktree: {worktree_path}")
    print(f"  Container: {container_name}")
    print(f"  Attach with: run.py --repo_base {repo_base} attach -n {args.name}")
    return 0


def cmd_ls(args) -> int:
    """Handle 'ls' subcommand: List all sandboxes."""
    repo_base = Path(args.repo_base).resolve()
    runtime = get_container_runtime()

    if not validate_git_repo(repo_base):
        print(f"Error: {repo_base} is not a git repository", file=sys.stderr)
        return 1

    db = SandboxDB(repo_base)
    sandboxes = db.list_all()

    if not sandboxes:
        print("No sandboxes found")
        return 0

    # Print header
    print(f"{'NAME':<15} {'BRANCH':<20} {'CONTAINER':<12} {'STATUS':<10} {'CREATED'}")
    print("-" * 80)

    for sb in sandboxes:
        container_name = get_container_name(sb["name"])
        if container_running(runtime, container_name):
            status = "running"
        elif container_exists(runtime, container_name):
            status = "stopped"
        else:
            status = "no container"

        created = sb["created_at"][:16] if sb["created_at"] else "unknown"
        print(f"{sb['name']:<15} {sb['branch']:<20} {container_name:<12} {status:<10} {created}")

    return 0


def cmd_rm(args) -> int:
    """Handle 'rm' subcommand: Delete worktree + container."""
    repo_base = Path(args.repo_base).resolve()
    runtime = get_container_runtime()

    if not validate_git_repo(repo_base):
        print(f"Error: {repo_base} is not a git repository", file=sys.stderr)
        return 1

    db = SandboxDB(repo_base)
    sandbox = db.get(args.name)

    if not sandbox:
        print(f"Error: Sandbox '{args.name}' not found", file=sys.stderr)
        return 1

    container_name = get_container_name(args.name)
    print(f"Removing sandbox '{args.name}'...")

    # Stop and remove container
    if container_exists(runtime, container_name):
        stop_container(runtime, container_name)
        remove_container(runtime, container_name)

    # Remove worktree
    try:
        remove_worktree(repo_base, args.name)
    except subprocess.CalledProcessError as e:
        if not args.force:
            print(f"Failed to remove worktree: {e}", file=sys.stderr)
            return 1

    # Remove from database
    db.delete(args.name)
    print(f"Sandbox '{args.name}' removed")
    return 0


def cmd_attach(args) -> int:
    """Handle 'attach' subcommand: Attach to tmux session."""
    repo_base = Path(args.repo_base).resolve()
    runtime = get_container_runtime()

    if not validate_git_repo(repo_base):
        print(f"Error: {repo_base} is not a git repository", file=sys.stderr)
        return 1

    db = SandboxDB(repo_base)
    sandbox = db.get(args.name)

    if not sandbox:
        print(f"Error: Sandbox '{args.name}' not found", file=sys.stderr)
        return 1

    container_name = get_container_name(args.name)

    # Check container state
    if not container_exists(runtime, container_name):
        print(f"Error: Container '{container_name}' does not exist", file=sys.stderr)
        return 1

    # Start container if stopped
    if not container_running(runtime, container_name):
        print(f"Starting container '{container_name}'...")
        if not start_container(runtime, container_name):
            print(f"Failed to start container", file=sys.stderr)
            return 1

    # Attach to tmux session
    cmd = [runtime, "exec", "-it", container_name, "tmux", "attach", "-t", "main"]
    print(f"Attaching to sandbox '{args.name}'...")
    os.execvp(cmd[0], cmd)


# =============================================================================
# Argument Parser
# =============================================================================


def main():
    """Main entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="Sandbox session manager with tmux-based worktree + container management.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo_base",
        required=True,
        help="Base path of the git repository",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'new' subcommand
    new_parser = subparsers.add_parser("new", help="Create new worktree + container")
    new_parser.add_argument("-n", "--name", required=True, help="Sandbox name")
    new_parser.add_argument("-b", "--branch", default="main", help="Branch to checkout")
    new_parser.add_argument("--ccr", action="store_true", help="Run in CCR mode")

    # 'ls' subcommand
    subparsers.add_parser("ls", help="List all sandboxes")

    # 'rm' subcommand
    rm_parser = subparsers.add_parser("rm", help="Delete worktree + container")
    rm_parser.add_argument("-n", "--name", required=True, help="Sandbox name")
    rm_parser.add_argument("--force", action="store_true", help="Force removal")

    # 'attach' subcommand
    attach_parser = subparsers.add_parser("attach", help="Attach to tmux session")
    attach_parser.add_argument("-n", "--name", required=True, help="Sandbox name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to subcommand handler
    handlers = {
        "new": cmd_new,
        "ls": cmd_ls,
        "rm": cmd_rm,
        "attach": cmd_attach,
    }

    handler = handlers.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
