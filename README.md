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

1. Clone this repository with an approved tool (for example GitHub Desktop) and open it in VS Code.
2. In Copilot Chat (agent mode) run `/install-harness`. It asks for the work repository path and the
   skills, then copies each skill to `.github/skills/` and its prompts to `.github/prompts/` there.
3. Open the work repository in VS Code and run its prompts in order.

### SQL Server lineage, in order

| Step | Command | Result |
| --- | --- | --- |
| 0 | `/install-harness` with skill `sql-server-lineage` (from this repository) | skill and prompts installed in the work repository |
| 1 | `/lineage-map` | catalog exports in `lineage\out`, issue lineage and Mermaid diagram in `lineage\<issue>` |
| 2 | `/lineage-gap-review` | cited dependencies the catalog cannot see, lineage rebuilt |
| 3 | `/lineage-to-archify` (optional) | explorable HTML diagram; needs the audited Archify skill |

## Tests

```bash
python -m unittest discover -s skills/sql-server-lineage/tests
```
