# Prompts Directory

Co-located agent prompt files for the mega-planner pipeline (`scripts/mega-planner.py`).

These are verbatim copies of prompt files from `.claude-plugin/agents/` and `.claude-plugin/skills/external-synthesize/`, co-located here so the standalone script can resolve them via `path_utils.relpath(__file__, "prompts")` without depending on the plugin directory structure.

## Files

| File | Source | Role |
|------|--------|------|
| `understander.md` | `.claude-plugin/agents/understander.md` | Context gathering before debate |
| `mega-bold-proposer.md` | `.claude-plugin/agents/mega-bold-proposer.md` | Innovative SOTA-driven proposals with code diffs |
| `mega-paranoia-proposer.md` | `.claude-plugin/agents/mega-paranoia-proposer.md` | Destructive refactoring proposals with code diffs |
| `mega-proposal-critique.md` | `.claude-plugin/agents/mega-proposal-critique.md` | Feasibility analysis of both proposals |
| `mega-proposal-reducer.md` | `.claude-plugin/agents/mega-proposal-reducer.md` | Simplification of both proposals |
| `mega-code-reducer.md` | `.claude-plugin/agents/mega-code-reducer.md` | Code footprint analysis |
| `external-synthesize-prompt.md` | `.claude-plugin/skills/external-synthesize/external-synthesize-prompt.md` | Consensus synthesis template |

## Synchronization

These files are copies, not symlinks. When the originals in `.claude-plugin/` are updated, these copies should be refreshed. The originals remain in place for the plugin command system.
