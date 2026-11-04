---
agent: 'agent'
description: 'Review the SQL Server objects the catalog cannot see into and record their dependencies, with file:line evidence, in inferred_edges.csv.'
---

# Lineage gap review

Exports folder: ${input:exports:Folder with the lineage CSV exports, e.g. lineage\out}
SQL source folder: ${input:source:Folder with the repository .sql files, e.g. src\sql}

Use the `sql-server-lineage` skill. Review only these items from `lineage.json` in the exports
folder: warnings with code `dynamic_sql`, `unresolved_reference`, `read_write_unavailable`,
`read_write_unknown` and `job_step_not_parsed`.

For each item:

1. Find the object's definition in the SQL source folder (`CREATE` or `ALTER` statement).
2. Read the code and identify the tables it reads, the tables it writes and the procedures it calls,
   including inside dynamic SQL strings.
3. Append one row per dependency to `inferred_edges.csv` in the exports folder, creating it with the
   header `from,to,kind,evidence` if missing:
   - `reads`: `from` is the table or view, `to` is the module.
   - `writes`: `from` is the module, `to` is the table.
   - `executes`: `from` is the caller, `to` is the called procedure.
   - `references`: direction cannot be determined.
   - `evidence`: repository-relative `path:line` where the dependency is visible.
   - Use `schema.name`; only objects listed in `objects.csv`.

Rules:

- Never guess a name assembled at runtime (variables, configuration tables, loops). Report it as an
  open question with its `path:line`.
- Do not edit the SQL and do not run any SQL.
- Do not add an edge you cannot cite.

Then rerun `build_lineage.py` as in Step 2 of the skill and report:

- edges added, grouped by object;
- objects still unresolved and why;
- open questions for the data owner, each with `path:line`.
