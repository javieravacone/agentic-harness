# Prompts

Reusable Copilot prompt files. `/install-harness` (in [`../.github/prompts/`](../.github/prompts/))
copies them into `.github/prompts/` of a work repository together with their skill; then run them in
Copilot Chat with `/<file name without .prompt.md>`.

## Registry

Prompts that use the same skill are listed in the order you run them.

| Prompt | Purpose | Uses | Status | Last reviewed |
| --- | --- | --- | --- | --- |
| [`lineage-map`](lineage-map.prompt.md) | 1. Export the catalog and build the lineage of an issue | `sql-server-lineage` skill | Draft | 2026-11-05 |
| [`lineage-gap-review`](lineage-gap-review.prompt.md) | 2. Add cited dependencies the catalog cannot see | `sql-server-lineage` skill | Draft | 2026-11-04 |
| [`lineage-to-archify`](lineage-to-archify.prompt.md) | 3. Optional: draw the lineage as an Archify dataflow | `sql-server-lineage` and `archify` skills | Draft, Archify pending audit | 2026-11-04 |

Status values: `Draft` (not yet used on real work), `In use`, `Retired` (keep the file, say why).

## Adding a prompt

1. Copy [`TEMPLATE.md`](TEMPLATE.md) to `<kebab-case-name>.prompt.md`.
2. Start from a real problem: who, when, what it costs, what the symptom is.
3. Ask for evidence (`path:line`) and say what the model must not do.
4. Add a row to the registry. Update *Status* and *Last reviewed* after each real use.

Never put internal data, code, names, architecture or credentials from client work in a prompt.
Use `${input:...}` placeholders and fill them inside the client environment.
