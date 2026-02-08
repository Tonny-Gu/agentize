"""Mega-planner: 7-stage multi-agent debate pipeline.

Standalone script that orchestrates dual-proposer debate with 5 analysis agents
and external AI consensus synthesis. Uses only agentize.workflow.api.

Usage:
    python scripts/mega-planner.py --feature-desc "..."
    python scripts/mega-planner.py --from-issue 42
    python scripts/mega-planner.py --refine-issue 42 --feature-desc "focus on X"
    python scripts/mega-planner.py --resolve-issue 42 --selections "1B,2A"
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# PYTHONPATH bootstrap: ensure python/ is importable
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_PYTHON_DIR = _REPO_ROOT / "python"
if str(_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_PYTHON_DIR))

from agentize.workflow.api import run_acw
from agentize.workflow.api import gh as gh_utils
from agentize.workflow.api import path as path_utils
from agentize.workflow.api import prompt as prompt_utils
from agentize.workflow.api.session import Session, StageResult


# ============================================================
# Constants
# ============================================================

PROMPTS_DIR = path_utils.relpath(__file__, "prompts")

AGENT_PROMPTS = {
    "understander": "understander.md",
    "bold": "mega-bold-proposer.md",
    "paranoia": "mega-paranoia-proposer.md",
    "critique": "mega-proposal-critique.md",
    "proposal-reducer": "mega-proposal-reducer.md",
    "code-reducer": "mega-code-reducer.md",
}

STAGES_WITH_PLAN_GUIDELINE = {"bold", "paranoia", "critique", "proposal-reducer", "code-reducer"}

DEFAULT_BACKENDS = {
    "understander": ("claude", "sonnet"),
    "bold": ("claude", "opus"),
    "paranoia": ("claude", "opus"),
    "critique": ("claude", "opus"),
    "proposal-reducer": ("claude", "opus"),
    "code-reducer": ("claude", "opus"),
    "consensus": ("claude", "opus"),
}

STAGE_TOOLS = {
    "understander": "Read,Grep,Glob",
    "bold": "Read,Grep,Glob,WebSearch,WebFetch",
    "paranoia": "Read,Grep,Glob",
    "critique": "Read,Grep,Glob,Bash",
    "proposal-reducer": "Read,Grep,Glob",
    "code-reducer": "Read,Grep,Glob",
    "consensus": "Read,Grep,Glob",
}

STAGE_PERMISSION_MODE = {
    "bold": "plan",
}


# ============================================================
# Prompt Rendering
# ============================================================


def _read_agent_prompt(stage: str) -> str:
    """Read an agent prompt from co-located prompts directory."""
    prompt_file = PROMPTS_DIR / AGENT_PROMPTS[stage]
    return prompt_utils.read_prompt(prompt_file, strip_frontmatter=True)


def _read_plan_guideline() -> str | None:
    """Read plan-guideline if available."""
    plan_guideline_path = (
        _REPO_ROOT / ".claude-plugin/skills/plan-guideline/SKILL.md"
    )
    if plan_guideline_path.exists():
        return prompt_utils.read_prompt(plan_guideline_path, strip_frontmatter=True)
    return None


def _render_stage_prompt(
    stage: str,
    feature_desc: str,
    previous_output: str | None = None,
) -> str:
    """Render the input prompt for a single-input stage."""
    parts = [_read_agent_prompt(stage)]

    if stage in STAGES_WITH_PLAN_GUIDELINE:
        guideline = _read_plan_guideline()
        if guideline:
            parts.append("\n---\n")
            parts.append("# Planning Guidelines\n")
            parts.append(guideline)

    parts.append("\n---\n")
    parts.append("# Feature Request\n")
    parts.append(feature_desc)

    if previous_output:
        parts.append("\n---\n")
        parts.append("# Previous Stage Output\n")
        parts.append(previous_output)

    return "\n".join(parts)


def _render_dual_input_prompt(
    stage: str,
    feature_desc: str,
    bold_output: str,
    paranoia_output: str,
) -> str:
    """Render input for stages that receive both proposals."""
    parts = [_read_agent_prompt(stage)]

    if stage in STAGES_WITH_PLAN_GUIDELINE:
        guideline = _read_plan_guideline()
        if guideline:
            parts.append("\n---\n")
            parts.append("# Planning Guidelines\n")
            parts.append(guideline)

    parts.append("\n---\n")
    parts.append("# Feature Request\n")
    parts.append(feature_desc)
    parts.append("\n---\n")
    parts.append("# Bold Proposal\n")
    parts.append(bold_output)
    parts.append("\n---\n")
    parts.append("# Paranoia Proposal\n")
    parts.append(paranoia_output)

    return "\n".join(parts)


def _build_debate_report(
    feature_name: str,
    bold_output: str,
    paranoia_output: str,
    critique_output: str,
    proposal_reducer_output: str,
    code_reducer_output: str,
) -> str:
    """Build the combined 5-agent debate report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# Multi-Agent Debate Report (Mega-Planner): {feature_name}

**Generated**: {timestamp}

This document combines five perspectives from the mega-planner dual-proposer debate system:
1. **Bold Proposer**: Innovative, SOTA-driven approach
2. **Paranoia Proposer**: Destructive refactoring approach
3. **Critique**: Feasibility analysis of both proposals
4. **Proposal Reducer**: Simplification of both proposals
5. **Code Reducer**: Code footprint analysis
6. **Previous Consensus Plan**: The plan being refined (if resolve/refine mode)
7. **Selection & Refine History**: History table with current task in last row (if resolve/refine mode)

---

## Part 1: Bold Proposer

{bold_output}

---

## Part 2: Paranoia Proposer

{paranoia_output}

---

## Part 3: Critique

{critique_output}

---

## Part 4: Proposal Reducer

{proposal_reducer_output}

---

## Part 5: Code Reducer

{code_reducer_output}

---
"""


def _render_consensus_prompt(
    feature_name: str,
    debate_report: str,
    dest_path: Path,
) -> str:
    """Render the external-synthesize prompt template."""
    template_path = PROMPTS_DIR / "external-synthesize-prompt.md"
    return prompt_utils.render(
        template_path,
        {
            "FEATURE_NAME": feature_name,
            "FEATURE_DESCRIPTION": feature_name,
            "COMBINED_REPORT": debate_report,
        },
        dest_path,
        strip_frontmatter=True,
    )


def _extract_feature_name(feature_desc: str, max_len: int = 80) -> str:
    """Extract a short feature name from description."""
    first_line = feature_desc.strip().split("\n")[0]
    normalized = " ".join(first_line.split())
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[:max_len]}..."


# ============================================================
# Pipeline Orchestration
# ============================================================


def run_mega_pipeline(
    feature_desc: str,
    *,
    output_dir: str | Path = ".tmp",
    backends: dict[str, tuple[str, str]] | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = run_acw,
    prefix: str | None = None,
    output_suffix: str = "-output.md",
    skip_consensus: bool = False,
    report_paths: dict[str, Path] | None = None,
    consensus_path: Path | None = None,
    history_path: Path | None = None,
) -> dict[str, StageResult]:
    """Execute the 7-stage mega-planner pipeline.

    If report_paths is provided, skip the debate stages and use
    existing report files for consensus (resolve mode).
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if prefix is None:
        prefix = datetime.now().strftime("%Y%m%d-%H%M%S")

    stage_backends = {**DEFAULT_BACKENDS}
    if backends:
        stage_backends.update(backends)

    session = Session(
        output_dir=output_path,
        prefix=prefix,
        runner=runner,
        output_suffix=output_suffix,
    )

    def _log(msg: str) -> None:
        session._log(msg)

    def _backend_label(stage: str) -> str:
        p, m = stage_backends[stage]
        return f"{p}:{m}"

    results: dict[str, StageResult] = {}

    # --- Resolve mode: skip debate, load existing reports ---
    if report_paths is not None:
        bold_output = report_paths["bold"].read_text()
        paranoia_output = report_paths["paranoia"].read_text()
        critique_output = report_paths["critique"].read_text()
        proposal_reducer_output = report_paths["proposal-reducer"].read_text()
        code_reducer_output = report_paths["code-reducer"].read_text()
    else:
        # --- Tier 1: Understander ---
        _log(f"Stage 1/7: Running understander ({_backend_label('understander')})")
        understander_prompt = _render_stage_prompt("understander", feature_desc)
        results["understander"] = session.run_prompt(
            "understander",
            understander_prompt,
            stage_backends["understander"],
            tools=STAGE_TOOLS.get("understander"),
            permission_mode=STAGE_PERMISSION_MODE.get("understander"),
        )
        understander_output = results["understander"].text()

        # --- Tier 2: Bold + Paranoia in parallel ---
        _log(
            f"Stage 2-3/7: Running bold + paranoia in parallel "
            f"({_backend_label('bold')}, {_backend_label('paranoia')})"
        )
        bold_prompt = _render_stage_prompt("bold", feature_desc, understander_output)
        paranoia_prompt = _render_stage_prompt("paranoia", feature_desc, understander_output)

        parallel_2 = session.run_parallel(
            [
                session.stage("bold", bold_prompt, stage_backends["bold"],
                              tools=STAGE_TOOLS.get("bold"),
                              permission_mode=STAGE_PERMISSION_MODE.get("bold")),
                session.stage("paranoia", paranoia_prompt, stage_backends["paranoia"],
                              tools=STAGE_TOOLS.get("paranoia"),
                              permission_mode=STAGE_PERMISSION_MODE.get("paranoia")),
            ],
            max_workers=2,
        )
        results.update(parallel_2)
        bold_output = results["bold"].text()
        paranoia_output = results["paranoia"].text()

        # --- Tier 3: Critique + Proposal Reducer + Code Reducer in parallel ---
        _log(
            f"Stage 4-6/7: Running critique + reducers in parallel "
            f"({_backend_label('critique')}, {_backend_label('proposal-reducer')}, "
            f"{_backend_label('code-reducer')})"
        )
        critique_prompt = _render_dual_input_prompt(
            "critique", feature_desc, bold_output, paranoia_output
        )
        proposal_reducer_prompt = _render_dual_input_prompt(
            "proposal-reducer", feature_desc, bold_output, paranoia_output
        )
        code_reducer_prompt = _render_dual_input_prompt(
            "code-reducer", feature_desc, bold_output, paranoia_output
        )

        parallel_3 = session.run_parallel(
            [
                session.stage("critique", critique_prompt, stage_backends["critique"],
                              tools=STAGE_TOOLS.get("critique"),
                              permission_mode=STAGE_PERMISSION_MODE.get("critique")),
                session.stage("proposal-reducer", proposal_reducer_prompt,
                              stage_backends["proposal-reducer"],
                              tools=STAGE_TOOLS.get("proposal-reducer"),
                              permission_mode=STAGE_PERMISSION_MODE.get("proposal-reducer")),
                session.stage("code-reducer", code_reducer_prompt,
                              stage_backends["code-reducer"],
                              tools=STAGE_TOOLS.get("code-reducer"),
                              permission_mode=STAGE_PERMISSION_MODE.get("code-reducer")),
            ],
            max_workers=3,
        )
        results.update(parallel_3)
        critique_output = results["critique"].text()
        proposal_reducer_output = results["proposal-reducer"].text()
        code_reducer_output = results["code-reducer"].text()

    if skip_consensus:
        return results

    # --- Tier 4: Consensus via external AI ---
    feature_name = _extract_feature_name(feature_desc)
    debate_report = _build_debate_report(
        feature_name,
        bold_output, paranoia_output,
        critique_output, proposal_reducer_output, code_reducer_output,
    )

    # Append resolve/refine context if provided
    if consensus_path and consensus_path.exists():
        prev_plan = consensus_path.read_text()
        debate_report += (
            f"\n## Part 6: Previous Consensus Plan\n\n"
            f"The following is the previous consensus plan being refined:\n\n"
            f"{prev_plan}\n\n---\n"
        )
    if history_path and history_path.exists():
        history_content = history_path.read_text()
        debate_report += (
            f"\n## Part 7: Selection & Refine History\n\n"
            f"**IMPORTANT**: The last row of the table below contains the current task requirement.\n"
            f"Apply the current task to the previous consensus plan to generate the updated plan.\n\n"
            f"{history_content}\n\n---\n"
        )

    # Save debate report
    debate_file = output_path / f"{prefix}-debate.md"
    debate_file.write_text(debate_report)

    def _write_consensus_prompt(path: Path) -> str:
        return _render_consensus_prompt(feature_name, debate_report, path)

    _log(f"Stage 7/7: Running consensus ({_backend_label('consensus')})")
    results["consensus"] = session.run_prompt(
        "consensus",
        _write_consensus_prompt,
        stage_backends["consensus"],
        tools=STAGE_TOOLS.get("consensus"),
        permission_mode=STAGE_PERMISSION_MODE.get("consensus"),
    )

    return results


# ============================================================
# CLI Helpers
# ============================================================

_PLAN_HEADER_RE = re.compile(r"^#\s*(Implementation|Consensus) Plan:\s*(.+)$")
_PLAN_HEADER_HINT_RE = re.compile(r"(Implementation Plan:|Consensus Plan:)", re.IGNORECASE)
_PLAN_FOOTER_RE = re.compile(r"^Plan based on commit (?:[0-9a-f]+|unknown)$")


def _resolve_commit_hash(repo_root: Path) -> str:
    """Resolve the current git commit hash for provenance."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        if message:
            print(f"Warning: Failed to resolve git commit: {message}", file=sys.stderr)
        else:
            print("Warning: Failed to resolve git commit", file=sys.stderr)
        return "unknown"

    commit_hash = result.stdout.strip().lower()
    if not commit_hash or not re.fullmatch(r"[0-9a-f]+", commit_hash):
        print("Warning: Unable to parse git commit hash, using 'unknown'", file=sys.stderr)
        return "unknown"
    return commit_hash


def _append_plan_footer(path: Path, commit_hash: str) -> None:
    """Append the commit provenance footer to a consensus plan file."""
    footer_line = f"Plan based on commit {commit_hash}"
    try:
        content = path.read_text()
    except FileNotFoundError:
        print(f"Warning: Consensus plan missing, cannot append footer: {path}", file=sys.stderr)
        return
    trimmed = content.rstrip("\n")
    if trimmed.endswith(footer_line):
        return
    with path.open("a") as f:
        if content and not content.endswith("\n"):
            f.write("\n")
        f.write(f"{footer_line}\n")


def _strip_plan_footer(text: str) -> str:
    """Strip the trailing commit provenance footer from a plan body."""
    if not text:
        return text
    lines = text.splitlines()
    had_trailing_newline = text.endswith("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    if not _PLAN_FOOTER_RE.match(lines[-1].strip()):
        return text
    lines.pop()
    result = "\n".join(lines)
    if had_trailing_newline and result:
        result += "\n"
    return result


def _shorten_feature_desc(desc: str, max_len: int = 50) -> str:
    normalized = " ".join(desc.split())
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[:max_len]}..."


def _extract_plan_title(consensus_path: Path) -> str:
    try:
        for line in consensus_path.read_text().splitlines():
            match = _PLAN_HEADER_RE.match(line.strip())
            if match:
                return match.group(2).strip()
    except FileNotFoundError:
        return ""
    return ""


def _apply_issue_tag(plan_title: str, issue_number: str) -> str:
    issue_tag = f"[#{issue_number}]"
    if plan_title.startswith(issue_tag):
        return plan_title
    if plan_title.startswith(f"{issue_tag} "):
        return plan_title
    if plan_title:
        return f"{issue_tag} {plan_title}"
    return issue_tag


# ============================================================
# CLI Main
# ============================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mega-planner 7-stage pipeline")
    parser.add_argument("--feature-desc", default="", help="Feature description")
    parser.add_argument("--from-issue", default="", help="Plan from existing issue number")
    parser.add_argument("--refine-issue", default="", help="Refine existing plan issue")
    parser.add_argument("--resolve-issue", default="", help="Resolve disagreements in issue")
    parser.add_argument("--selections", default="", help="Option selections for resolve mode (e.g. 1B,2A)")
    parser.add_argument("--output-dir", default=".tmp")
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--skip-consensus", action="store_true")
    parser.add_argument("--issue-mode", default="true", choices=["true", "false"])
    args = parser.parse_args(argv)

    repo_root = _REPO_ROOT
    os.environ["AGENTIZE_HOME"] = str(repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    issue_mode = args.issue_mode == "true"

    issue_number: Optional[str] = None
    issue_url: Optional[str] = None
    feature_desc = args.feature_desc
    report_paths = None
    consensus_path = None
    history_path = None
    prefix: str

    def _log(msg: str) -> None:
        print(msg, file=sys.stderr)

    def _log_verbose(msg: str) -> None:
        if args.verbose:
            _log(msg)

    # --- Resolve mode ---
    if args.resolve_issue:
        issue_number = args.resolve_issue
        prefix = f"issue-{issue_number}"
        report_paths = {}
        for stage in ["bold", "paranoia", "critique", "proposal-reducer", "code-reducer"]:
            p = output_dir / f"{prefix}-{stage}-output.md"
            if not p.exists():
                _log(f"Error: Report file not found: {p}")
                return 1
            report_paths[stage] = p

        consensus_path = output_dir / f"{prefix}-consensus-output.md"
        history_path = output_dir / f"{prefix}-history.md"
        if not history_path.exists():
            history_path.write_text(
                "# Selection & Refine History\n\n"
                "| Timestamp | Type | Content |\n"
                "|-----------|------|---------|\n"
            )
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with history_path.open("a") as f:
            f.write(f"| {ts} | resolve | {args.selections} |\n")

        feature_desc = gh_utils.issue_body(issue_number, cwd=repo_root)
        feature_desc = _strip_plan_footer(feature_desc)

    # --- Refine mode ---
    elif args.refine_issue:
        issue_number = args.refine_issue
        issue_url = gh_utils.issue_url(issue_number, cwd=repo_root)
        prefix = f"issue-{issue_number}"
        issue_body = gh_utils.issue_body(issue_number, cwd=repo_root)
        issue_body = _strip_plan_footer(issue_body)
        if not _PLAN_HEADER_HINT_RE.search(issue_body):
            _log(
                f"Warning: Issue #{issue_number} does not look like a plan "
                "(missing Implementation/Consensus Plan headers)"
            )
        feature_desc = issue_body
        if args.feature_desc:
            feature_desc = f"{feature_desc}\n\nRefinement focus:\n{args.feature_desc}"
        history_path = output_dir / f"{prefix}-history.md"
        if not history_path.exists():
            history_path.write_text(
                "# Selection & Refine History\n\n"
                "| Timestamp | Type | Content |\n"
                "|-----------|------|---------|\n"
            )
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        summary = (args.feature_desc or "general refinement")[:80].replace("\n", " ")
        with history_path.open("a") as f:
            f.write(f"| {ts} | refine | {summary} |\n")

    # --- From-issue mode ---
    elif args.from_issue:
        issue_number = args.from_issue
        issue_url = gh_utils.issue_url(issue_number, cwd=repo_root)
        prefix = f"issue-{issue_number}"
        feature_desc = gh_utils.issue_body(issue_number, cwd=repo_root)

    # --- Default mode ---
    else:
        if not feature_desc:
            _log("Error: --feature-desc is required in default mode")
            return 1
        prefix = args.prefix or datetime.now().strftime("%Y%m%d-%H%M%S")
        if issue_mode:
            short_desc = _shorten_feature_desc(feature_desc, max_len=50)
            issue_number, issue_url = gh_utils.issue_create(
                f"[plan] placeholder: {short_desc}",
                feature_desc,
                cwd=repo_root,
            )
            if not issue_number:
                _log(f"Warning: Could not parse issue number from URL: {issue_url}")
            if issue_number:
                prefix = f"issue-{issue_number}"
                _log(f"Created placeholder issue #{issue_number}")
            else:
                _log("Warning: Issue creation failed, falling back to timestamp artifacts")

    _log("Starting mega-planner 7-stage debate pipeline...")
    _log(f"Feature: {_extract_feature_name(feature_desc)}")
    _log_verbose(f"Artifacts prefix: {prefix}")

    try:
        results = run_mega_pipeline(
            feature_desc,
            output_dir=output_dir,
            prefix=prefix,
            skip_consensus=args.skip_consensus,
            report_paths=report_paths,
            consensus_path=consensus_path,
            history_path=history_path,
        )
    except Exception as exc:
        _log(f"Error: {exc}")
        return 2

    consensus_result = results.get("consensus")
    if consensus_result:
        commit_hash = _resolve_commit_hash(repo_root)
        _append_plan_footer(consensus_result.output_path, commit_hash)

        if issue_mode and issue_number:
            _log(f"Publishing plan to issue #{issue_number}...")
            plan_title = _extract_plan_title(consensus_result.output_path)
            if not plan_title:
                plan_title = _shorten_feature_desc(feature_desc, max_len=50)
            plan_title = _apply_issue_tag(plan_title, issue_number)
            gh_utils.issue_edit(
                issue_number,
                title=f"[plan] {plan_title}",
                body_file=consensus_result.output_path,
                cwd=repo_root,
            )
            gh_utils.label_add(issue_number, ["agentize:plan"], cwd=repo_root)
            if issue_url:
                _log(f"See the full plan at: {issue_url}")

        try:
            consensus_display = str(consensus_result.output_path.relative_to(repo_root))
        except ValueError:
            consensus_display = str(consensus_result.output_path)
        _log(f"See the full plan locally at: {consensus_display}")
        print(str(consensus_result.output_path))

    _log("Pipeline complete!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
