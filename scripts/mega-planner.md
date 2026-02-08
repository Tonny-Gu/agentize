# Script: mega-planner.py

Standalone 7-stage multi-agent debate pipeline for implementation planning.

## External Interfaces

### `run_mega_pipeline()`

```python
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
) -> dict[str, StageResult]
```

Orchestrates the full 7-stage pipeline:

1. **Understander** (sequential): Gathers codebase context
2. **Bold + Paranoia** (parallel): Dual proposers generate competing approaches
3. **Critique + Proposal Reducer + Code Reducer** (parallel): Three analyzers evaluate both proposals
4. **Consensus** (sequential): External AI synthesizes unified plan from debate report

Parameters:
- `report_paths`: If provided, skips debate stages 1-3 and loads existing reports (resolve mode)
- `consensus_path`: Previous consensus plan for resolve/refine context
- `history_path`: Selection & refine history for iterative planning
- `skip_consensus`: Return after debate stages without running consensus

### CLI Modes

```bash
# Default: create new plan from description
python scripts/mega-planner.py --feature-desc "Add dark mode"

# From-issue: plan from existing GitHub issue
python scripts/mega-planner.py --from-issue 42

# Refine: re-run debate with refinement focus on existing plan
python scripts/mega-planner.py --refine-issue 42 --feature-desc "focus on X"

# Resolve: fast-path resolution using existing debate reports
python scripts/mega-planner.py --resolve-issue 42 --selections "1B,2A"
```

## Internal Helpers

### Prompt Rendering

- `_render_stage_prompt()`: Single-input stages (understander, bold, paranoia)
- `_render_dual_input_prompt()`: Dual-input stages (critique, proposal-reducer, code-reducer)
- `_render_consensus_prompt()`: Template rendering for external-synthesize prompt
- `_build_debate_report()`: Combines 5 agent outputs into unified debate report

### CLI Helpers

- `_resolve_commit_hash()`: Git commit hash for plan provenance
- `_append_plan_footer()` / `_strip_plan_footer()`: Plan footer management
- `_extract_plan_title()`: Parse plan title from consensus output
- `_extract_feature_name()`: Short feature name from description

## Dependencies

Uses only `agentize.workflow.api`:
- `Session` / `StageResult` from `session.py`
- `run_acw` from `acw.py`
- `prompt.read_prompt()` / `prompt.render()` for prompt handling
- `path.relpath()` for co-located prompt resolution
- `gh.*` for GitHub issue management
