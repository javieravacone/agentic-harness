# Skills

Agent skills in the `SKILL.md` format that GitHub Copilot loads on demand.

Install a skill by copying its folder to one of:

- `.github/skills/<name>/` in the work repository (project skill, shared with the team);
- `~/.copilot/skills/<name>/` (personal skill, every repository).

## Registry

| Skill | Source | Needs | Status |
| --- | --- | --- | --- |
| [`sql-server-lineage`](sql-server-lineage/SKILL.md) | This repository | Python 3, `sqlcmd` or SSMS | Draft: script tested with fixtures; SQL scripts not yet run on a real server |
| `archify` | Third party, [tt-a1i/archify](https://github.com/tt-a1i/archify), MIT | Node 18+, Chrome or Edge, terminal | Pending audit; not copied here |

## Third-party skill audit

Before a third-party skill enters the client environment, record:

1. Source repository, version and license.
2. Every script it runs and what it executes (shell, browser, network).
3. Network calls and how to turn them off (Archify: `ARCHIFY_UPDATE_CHECK_DISABLED=1`).
4. Files it writes and where.
5. Who approved it and when.

A skill that needs MCP, hooks or plugins does not fit the current client restrictions.
