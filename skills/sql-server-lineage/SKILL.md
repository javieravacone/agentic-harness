---
name: sql-server-lineage
description: Map the objects, dependencies and execution order behind a change in a SQL Server database (procedures, views, functions, tables, SQL Agent jobs) and draw it. Use when asked for the lineage, impact, flow or migration order of SQL Server code that is not in dbt.
license: MIT
---

# SQL Server lineage

The dependencies come from the SQL Server catalog, not from reading code. Scripts extract them,
`build_lineage.py` joins and trims them, and the model only fills the gaps the catalog cannot see,
always citing `file:line`.

```
catalog exports (sql/*.sql) -> CSV -> [gap review, cited] -> build_lineage.py -> lineage.json -> diagram
```

## Rules

- Read-only. The scripts read catalog metadata (`sys.*`, `msdb`), never business data. Run them only
  in an environment the data owner authorized.
- Exports and diagrams stay in the work repository and its approved environment. Never paste them
  into chats, personal accounts or this harness repository.
- Every dependency the model adds needs `file:line` evidence. `build_lineage.py` rejects it otherwise.
- Do not edit or run the SQL being analyzed. Propose; the owner decides.

## Requirements

- `sqlcmd` (or SSMS to export results by hand), Python 3 (standard library only).
- `VIEW DEFINITION` on the database; read access to `msdb` for jobs.
- Optional: the Archify skill (Node 18+, Chrome or Edge) for an explorable HTML diagram.

## Step 1 · Export the catalog

Paths are relative to the repository root that holds this skill under `.github/skills/`.
`-u` writes UTF-16 with a BOM, which `build_lineage.py` reads; `-b` stops on SQL errors.

```powershell
$Sql = ".github\skills\sql-server-lineage\sql"; $Out = "lineage\out"; $S = "<server>"; $D = "<database>"
New-Item -ItemType Directory -Force $Out | Out-Null
sqlcmd -S $S -d $D -E -b -u -W -s "|" -i "$Sql\01_objects.sql"      -o "$Out\objects.csv"
sqlcmd -S $S -d $D -E -b -u -W -s "|" -i "$Sql\02_dependencies.sql" -o "$Out\dependencies.csv"
sqlcmd -S $S -d $D -E -b -u -W -s "|" -i "$Sql\03_read_write.sql"   -o "$Out\read_write.csv"
sqlcmd -S $S -d msdb -E -b -u -W -s "|" -i "$Sql\04_jobs.sql"       -o "$Out\jobs.csv"
sqlcmd -S $S -d $D -E -b -u -W -s "|" -i "$Sql\05_dynamic_sql.sql"  -o "$Out\dynamic_sql.csv"
```

Without `sqlcmd`: open each script in SSMS, run it, and use *Save Results As* → CSV with the same
file name (enable *Tools → Options → Query Results → SQL Server → Results to Grid → Include column
headers when copying or saving the results*). `objects.csv`
and `dependencies.csv` are required; the rest are optional but each one adds information.

| Script | Source | Adds |
| --- | --- | --- |
| `01_objects.sql` | `sys.objects` | every table, view, procedure, function, trigger, synonym |
| `02_dependencies.sql` | `sys.sql_expression_dependencies` | who references whom, whole database |
| `03_read_write.sql` | `sys.dm_sql_referenced_entities` | whether each reference reads or writes |
| `04_jobs.sql` | `msdb.dbo.sysjobs`, `sysjobsteps` | which job step runs which procedure |
| `05_dynamic_sql.sql` | `sys.sql_modules` | modules whose dependencies the catalog cannot see |

## Step 2 · Build the lineage

```powershell
python .github\skills\sql-server-lineage\build_lineage.py --in lineage\out --out lineage\out\lineage.json
```

For one issue, center on the objects it touches and compare with the `.sql` files in the repo:

```powershell
python .github\skills\sql-server-lineage\build_lineage.py --in lineage\out `
  --focus dw.CalcPnL --focus dw.PnL --out lineage\issue\lineage.json `
  --mermaid lineage\issue\lineage.md --repo-sql src\sql
```

`--focus` keeps everything upstream and downstream of those objects plus the procedures and jobs that
call them. `--depth N` limits the data hops. Exit code 2 means invalid input (message on stderr).

## Step 3 · Fill the gaps (model, cited)

Run the `lineage-gap-review` prompt. It reviews only the objects flagged in `lineage.json` warnings and
appends cited rows to `lineage\out\inferred_edges.csv`:

```csv
from,to,kind,evidence
dw.DynamicLoader,stg.Positions,writes,src/sql/dw/DynamicLoader.sql:42
```

Then rerun Step 2. Inferred edges keep `"confidence": "inferred"` and are drawn dashed.

## Step 4 · Draw

- Small graph: `lineage.md` (Mermaid) renders in VS Code preview and in the repository viewer.
- Explorable HTML: run the `lineage-to-archify` prompt (needs the Archify skill).
- Big graphs are unreadable: draw one issue or subdomain at a time; keep the whole inventory as
  `objects.csv` + `dependencies.csv` in a spreadsheet.

## Step 5 · Deliver

Commit `lineage\issue\` (scripts output, JSON, diagram) next to the change in the work repository.
The data owner confirms semantics: the diagram shows technical dependencies, not field meaning.

## Reading `lineage.json`

Arrows follow the data: `reads` goes from the source object to the module that reads it, `writes`
from the module to the table it changes.

| Edge kind | Meaning |
| --- | --- |
| `reads` | data flows from `from` into `to` |
| `writes` | `from` inserts/updates/deletes `to` |
| `executes` | procedure `from` calls procedure `to` |
| `runs` | SQL Agent job `from` runs procedure `to` (`job_step`, `job_enabled`) |
| `references` | referenced, direction unknown: review |

| Confidence | Source |
| --- | --- |
| `catalog` | SQL Server catalog |
| `parsed` | job step command text matched a procedure name |
| `inferred` | added in Step 3 with `evidence` |

`waves` is the migration order: wave 0 depends on nothing, wave N only on earlier waves. A procedure
that reads and writes the same table (in-place update) does not create a cycle; real cycles share one
wave and appear as a `cycle` warning.

| Warning | Action |
| --- | --- |
| `dynamic_sql` | review in Step 3 |
| `unresolved_reference` | one-part name the catalog could not bind; review in Step 3 |
| `read_write_unavailable` | module failed in `03`; edges are `references` |
| `read_write_unknown` | no `03` row for that reference |
| `missing_object` | referenced object does not exist in this database |
| `job_step_not_parsed` | SSIS/CmdExec/PowerShell step; export the package separately |
| `job_command_truncated` | step longer than 4000 characters; read it in SSMS |
| `cycle` | objects depend on each other |

`repo` (with `--repo-sql`) lists objects deployed but absent from the repository and the reverse.
It checks presence by name, not definition content.

## Limits

- Not visible to the catalog: dynamic SQL, temporary tables, names built at runtime, SSIS packages.
- Linked-server references carry partial information.
- Job steps are matched by name: a procedure is matched only when the step names its schema
  (`dw.Proc`), or with an unqualified name when the procedure is in `dbo`.

## Tests

```powershell
python -m unittest discover -s .github\skills\sql-server-lineage\tests
```
