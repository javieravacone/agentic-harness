# Prompts

Reusable Copilot prompt files. Each `*.prompt.md` works as is: copy it to `.github/prompts/` in the
work repository and run it in Copilot Chat with `/<file name without .prompt.md>`.

## Registry

| Prompt | Purpose | Uses | Status | Last reviewed |
| --- | --- | --- | --- | --- |
| [`lineage-gap-review`](lineage-gap-review.prompt.md) | Add cited dependencies the SQL Server catalog cannot see | `sql-server-lineage` skill | Draft | 2026-11-04 |
| [`lineage-to-archify`](lineage-to-archify.prompt.md) | Draw a focused lineage as an Archify dataflow | `archify` skill | Draft, Archify pending audit | 2026-11-04 |

Status values: `Draft` (not yet used on real work), `In use`, `Retired` (keep the file, say why).

## Adding a prompt

1. Copy [`TEMPLATE.md`](TEMPLATE.md) to `<kebab-case-name>.prompt.md`.
2. Start from a real problem: who, when, what it costs, what the symptom is.
3. Ask for evidence (`path:line`) and say what the model must not do.
4. Add a row to the registry. Update *Status* and *Last reviewed* after each real use.

Never put internal data, code, names, architecture or credentials from client work in a prompt.
Use `${input:...}` placeholders and fill them inside the client environment.
