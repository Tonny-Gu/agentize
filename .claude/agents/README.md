# Agents

This directory contains agent definitions for Claude Code. Agents are specialized AI assistants for complex tasks requiring isolated context and specific model configurations.

## Purpose

Agents provide isolated execution environments for complex, multi-step tasks. Each agent is defined as a markdown file with YAML frontmatter configuration.

## Organization

- Each agent is a `.md` file in the `agents/` directory
- Agent files include:
  - YAML frontmatter: Configuration (name, description, model, tools, skills)
  - Markdown content: Agent behavior specification and workflow

## Available Agents

### Review & Analysis

- `code-quality-reviewer.md`: Comprehensive code review with enhanced quality standards using Opus model for long context analysis

### Debate-Based Planning

Multi-perspective planning agents for collaborative proposal development:

- `understander.md`: Gather codebase context before debate begins (feeds both proposers)
- `bold-proposer.md`: Research SOTA solutions and propose innovative, incremental improvements with code diffs
- `paranoia-proposer.md`: Propose destructive refactoring with code diffs, advocating for clean-slate rewrites
- `proposal-critique.md`: Validate assumptions and analyze technical feasibility of both proposals
- `proposal-reducer.md`: Simplify proposals following "less is more" philosophy (minimize changes)
- `code-reducer.md`: Simplify code while allowing large changes (limit unreasonable code growth)

These agents work together in the `/ultra-planner` workflow to generate well-balanced implementation plans through structured debate:
1. Understander runs first to gather context
2. Bold-proposer and Paranoia-proposer run in parallel with context
3. Critique, Proposal-reducer, and Code-reducer analyze both proposals in parallel
4. External consensus synthesizes final plan(s) - single plan if consensus, multiple options if perspectives diverge
