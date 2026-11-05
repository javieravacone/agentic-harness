---
agent: 'agent'
description: 'Export the SQL Server catalog and build the lineage of the objects an issue touches (steps 1 and 2 of the sql-server-lineage skill).'
---

# Lineage map

Server: ${input:server:SQL Server instance, e.g. MYSERVER\INSTANCE}
Database: ${input:database:Database name}
Objects: ${input:objects:Objects the issue touches as schema.name, comma separated}
SQL source folder: ${input:source:Repository folder with the .sql files, e.g. src\sql}
Issue folder name: ${input:issue:Short name for the output folder, e.g. issue-123}

Use the `sql-server-lineage` skill in `.github\skills\sql-server-lineage\`. Read its `SKILL.md`
before starting and follow it.

1. Check the tools: `sqlcmd -?` and `python --version`. If `sqlcmd` is missing, stop and explain
   the SSMS export alternative from the skill. If Python is missing, stop.
2. Run Step 1 of the skill against the server and database above, writing to `lineage\out`.
   Run one `sqlcmd` command at a time, asking for approval before each one. If a command fails,
   stop and show the full error; do not edit the SQL scripts to make it pass.
3. Run Step 2 once for the issue:
   - one `--focus` per object listed above;
   - `--repo-sql` with the SQL source folder;
   - `--out lineage\<issue>\lineage.json` and `--mermaid lineage\<issue>\lineage.md`.
   If it exits with code 2, show the error and stop.
4. Open `lineage\<issue>\lineage.md` in the Markdown preview.

Rules:

- Read-only: run only the scripts in the skill's `sql\` folder. Never run other SQL and never
  modify the database.
- Do not commit anything.

Report:

- the summary line printed by `build_lineage.py`;
- the warnings grouped by code, with the action the skill gives for each;
- the `repo` section (objects deployed but missing from the repository, and the reverse);
- the next step: `/lineage-gap-review` if there are `dynamic_sql`, `unresolved_reference`,
  `read_write_unavailable`, `read_write_unknown` or `job_step_not_parsed` warnings.
