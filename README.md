# Agentic harness

Prompts, skills and working rules for AI-assisted engineering with GitHub Copilot inside a restricted
client environment. The model proposes; certified data, tests, reviewers and owners decide.

## Contents

| Folder | What lives there |
| --- | --- |
| [`prompts/`](prompts/README.md) | Copilot prompt files (`*.prompt.md`) and their registry |
| [`skills/`](skills/README.md) | Agent skills (`SKILL.md` + scripts) and their registry |

## Environment assumptions

- Allowed: custom agents, subagents, `AGENTS.md`, skills, prompt files.
- Not allowed: MCP servers, hooks, plugins. Do not try to work around this.
- Terminal commands run only with explicit approval.

## What never goes in this repository

Client data, code, object or table names, architecture, metrics, incidents, exports, screenshots,
credentials or prompts with internal context. Everything here must be safe to publish. Client-specific
values are `${input:...}` placeholders filled inside the client environment, and every output stays in
the client's repositories.

## Using it in the client environment

1. Clone or download this repository with an approved tool.
2. Copy the skills you need to `.github/skills/` and the prompts to `.github/prompts/` of the work
   repository.
3. Run a prompt in Copilot Chat with `/<prompt-name>`.

## Tests

```bash
python -m unittest discover -s skills/sql-server-lineage/tests
```
