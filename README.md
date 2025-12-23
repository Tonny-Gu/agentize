# AI-powered SDK for Software Development

## Quick Start

1. Clone this repository:
```bash
git clone https://github.com/SyntheSys-Lab/agentize.git
```
2. Use this repository to create an SDK for your project.
```
make agentize \
   AGENTIZE_PROJECT_NAME="your_project_name" \
   AGENTIZE_PROJECT_PATH="/path/to/your/project" \
   AGENTIZE_PROJECT_LANG="c" \
   AGENTIZE_MODE="init"
```

This will create an initial SDK structure in the specified project path.
For more details of the variables and options available, refer to our
[usage document](./docs/OPTIONS.md).

## Core Phylosophy

1. Plan first, code later: Use AI to generate a detailed plan before writing any code.
  - Plan is put on Github Issues for tracking.
2. Build [skills](https://agentskills.io/), do not build agents.
  - Skills are modular reusable, formal, and lightweighted flow definitions.
3. Bootstrapping via self-improvment: We have `.claude` linked to our `claude` rules
   directory. We use these rules to develop these rules further.

## Project Organization

```plaintext
agentize/
├── docs/                   # Document
|   ├── draft/              # Draft documents for local development
|   ├── OPTIONS.md          # Document for make options
|   └── git-msg-tags.md     # Used by \git-commit skill and command to write meaningful commit messages
├── templates/              # Templates for SDK generation
├── claude/                 # Core agent rules for Claude Code
├── tests/                  # Test cases
├── .gitignore              # Git ignore file
├── Makefile                # Makefile for creating SDKs
└── README.md               # This readme file
```
