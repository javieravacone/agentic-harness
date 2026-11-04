---
agent: 'agent'
description: 'Turn a focused lineage.json from the sql-server-lineage skill into an explorable Archify dataflow diagram.'
---

# Lineage to Archify

Lineage file: ${input:lineage:Path to a focused lineage.json, e.g. lineage\issue\lineage.json}
Diagram title: ${input:title:What the diagram explains, e.g. Impact of changing the PnL calculation}

Use the `archify` skill with diagram type `dataflow`. Before running it, set
`$env:ARCHIFY_UPDATE_CHECK_DISABLED = "1"` so it makes no network call.

Map `lineage.json` without adding or dropping meaning:

- One diagram node per `nodes[]` entry. Keep its `label` and show its `kind` (table, view, procedure,
  function, job, external).
- One relationship per `edges[]` entry, labelled with its `kind`. Edges with `confidence` `inferred`
  must be visibly different and keep their `evidence` as the source reference.
- Mark nodes with non-empty `gaps` as needing manual review.
- Order the layout by `waves` (left to right) when it reads clearly.
- Add a legend that explains edge kinds and the inferred style.

If the file has more than about 40 nodes, stop and ask to narrow `--focus` or `--depth` instead of
drawing an unreadable diagram. Never invent nodes or dependencies that are not in the file.

Report the HTML path and any part of the lineage that could not be represented.
