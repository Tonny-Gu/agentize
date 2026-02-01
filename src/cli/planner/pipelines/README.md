# Pipeline Descriptors

This directory contains YAML pipeline descriptors that define the multi-agent debate workflows for the planner.

## Files

- `ultra.yaml` - Ultra-Planner (4-agent single-proposer debate)
- `mega.yaml` - Mega-Planner (5-agent dual-proposer debate)

## Structure

Each pipeline YAML defines:

- `name`: Pipeline identifier
- `description`: Human-readable description
- `stages`: Ordered list of execution stages

Each stage contains:

- `name`: Stage identifier
- `label`: Progress label shown during execution
- `agents`: List of agents to run (parallel if multiple)

Each agent specifies:

- `name`: Agent output identifier (used for input resolution)
- `agent_md`: Path to agent prompt markdown
- `backend_key`: Key for backend override lookup
- `default_backend`: Fallback backend (provider:model)
- `tools`: Comma-separated tool list
- `permission_mode`: Optional permission mode (e.g., "plan")
- `plan_guideline`: Whether to include plan-guideline in prompt
- `inputs`: List of previous agent names whose outputs become context

## Usage

The `_planner_run_pipeline` function accepts a `pipeline-type` parameter:

```bash
_planner_run_pipeline "feature description" "true" "false" "" "ultra"
_planner_run_pipeline "feature description" "true" "false" "" "mega"
```

Pipelines are parsed by `_planner_load_pipeline` using inline Python and executed by `_planner_exec_pipeline`.
