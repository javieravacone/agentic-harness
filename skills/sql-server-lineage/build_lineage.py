#!/usr/bin/env python3
"""Build a dependency/lineage graph from SQL Server catalog exports.

Inputs (a folder of exports produced by the scripts in ./sql):
  objects.csv          required  01_objects.sql
  dependencies.csv     required  02_dependencies.sql
  read_write.csv       optional  03_read_write.sql
  jobs.csv             optional  04_jobs.sql
  dynamic_sql.csv      optional  05_dynamic_sql.sql
  inferred_edges.csv   optional  hand-written: from,to,kind,evidence (evidence = file:line)

Accepts sqlcmd output (pipe separated, header dash row, NULL literals) and
SSMS "Save Results As" CSV (comma separated). Standard library only.

Usage:
  python build_lineage.py --in out --out out/lineage.json
  python build_lineage.py --in out --out out/issue.json --focus dw.PnL --mermaid out/issue.md
"""

import argparse
import csv
import io
import json
import re
import sys
from collections import deque
from pathlib import Path

REQUIRED = ("objects.csv", "dependencies.csv")
OPTIONAL = ("read_write.csv", "jobs.csv", "dynamic_sql.csv", "inferred_edges.csv")

KINDS = {
    "U": "table",
    "V": "view",
    "P": "procedure",
    "FN": "function",
    "IF": "function",
    "TF": "function",
    "TR": "trigger",
    "SN": "synonym",
}
INFERRED_KINDS = {"reads", "writes", "executes", "references"}
GAP_FLAGS = (
    ("uses_sp_executesql", "sp_executesql"),
    ("uses_exec_string", "exec_string"),
    ("uses_openquery", "openquery"),
)
DASH_CELL = re.compile(r"^-+$")
ROWS_AFFECTED = re.compile(r"^\(\d+ rows? affected\)$")
EVIDENCE = re.compile(r".+:\d+$")
REPO_DDL = re.compile(
    r"^\s*(?:CREATE(?:\s+OR\s+ALTER)?|ALTER)\s+"
    r"(?:PROCEDURE|PROC|VIEW|FUNCTION|TRIGGER|TABLE|SYNONYM)\s+([^\s(]+)",
    re.IGNORECASE,
)


class InputError(Exception):
    """Invalid or missing input; the CLI exits with code 2."""


# --------------------------------------------------------------------------- reading


def read_text(path):
    data = Path(path).read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def _value(cell):
    cell = cell.strip()
    return None if cell in ("", "NULL") else cell


def read_table(path):
    """Read a sqlcmd (pipe) or SSMS (comma) export into a list of dicts."""
    lines = [line for line in read_text(path).splitlines() if line.strip()]
    if not lines:
        return []
    pipe = "|" in lines[0]
    reader = csv.reader(
        io.StringIO("\n".join(lines)),
        delimiter="|" if pipe else ",",
        quoting=csv.QUOTE_NONE if pipe else csv.QUOTE_MINIMAL,
    )
    header = [cell.strip() for cell in next(reader)]
    rows = []
    for cells in reader:
        stripped = [cell.strip() for cell in cells]
        if all(DASH_CELL.match(cell) for cell in stripped if cell):
            continue
        if len(stripped) == 1 and ROWS_AFFECTED.match(stripped[0]):
            continue
        stripped += [""] * (len(header) - len(stripped))
        rows.append({name: _value(cell) for name, cell in zip(header, stripped)})
    return rows


def load_inputs(folder):
    folder = Path(folder)
    inputs = {}
    for name in REQUIRED:
        path = folder / name
        if not path.is_file():
            raise InputError(f"missing required input {path}")
        inputs[name] = read_table(path)
    for name in OPTIONAL:
        path = folder / name
        inputs[name] = read_table(path) if path.is_file() else []
    return inputs


# --------------------------------------------------------------------------- graph


def object_id(database, schema, name, server=None):
    parts = [server] if server else []
    parts += [database or "?", schema or "?", name]
    return ".".join(parts).lower()


class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.warnings = []

    def add_node(self, node_id, **fields):
        if node_id not in self.nodes:
            fields.setdefault("gaps", [])
            self.nodes[node_id] = {"id": node_id, **fields}
        return self.nodes[node_id]

    def add_edge(self, source, target, kind, confidence="catalog", **extra):
        key = (source, target, kind)
        if key not in self.edges:
            self.edges[key] = {"from": source, "to": target, "kind": kind, "confidence": confidence, **extra}

    def warn(self, code, message, obj=None):
        warning = {"code": code, "message": message}
        if obj:
            warning["object"] = obj
        if warning not in self.warnings:
            self.warnings.append(warning)


def _add_objects(graph, rows):
    for row in rows:
        node_id = object_id(row["database_name"], row["schema_name"], row["object_name"])
        graph.add_node(
            node_id,
            database=row["database_name"],
            schema=row["schema_name"],
            name=row["object_name"],
            kind=KINDS.get((row["object_type"] or "").upper(), "other"),
            label=f"{row['schema_name']}.{row['object_name']}",
        )


def _referenced_id(row):
    database = row["referenced_database_name"] or row["database_name"]
    return object_id(database, row["referenced_schema"], row["referenced_name"], row["referenced_server_name"])


def _read_write_index(graph, rows):
    index, failed = {}, set()
    for row in rows:
        source = object_id(row["database_name"], row["referencing_schema"], row["referencing_name"])
        status = row.get("status") or "ok"
        if status != "ok":
            failed.add(source)
            graph.warn(
                "read_write_unavailable",
                f"read/write flags unavailable ({status}); edges fall back to 'references'",
                source,
            )
            continue
        target = _referenced_id(row)
        selected, updated = index.get((source, target), (False, False))
        index[(source, target)] = (
            selected or row["is_selected"] == "1",
            updated or row["is_updated"] == "1",
        )
    return index, failed


def _add_referenced_node(graph, row, target):
    if target in graph.nodes:
        return graph.nodes[target]
    database = row["referenced_database_name"] or row["database_name"]
    schema, name = row["referenced_schema"], row["referenced_name"]
    if row["referenced_server_name"] or (row["referenced_database_name"] and row["referenced_database_name"].lower() != (row["database_name"] or "").lower()):
        kind, label = "external", ".".join(p for p in (row["referenced_server_name"], database, schema or "?", name) if p)
    elif schema is None:
        kind, label = "unresolved", f"?.{name}"
        graph.warn("unresolved_reference", "one-part name could not be bound to a schema; review manually", target)
    else:
        kind, label = "missing", f"{schema}.{name}"
        graph.warn("missing_object", "referenced object does not exist in the exported database", target)
    return graph.add_node(target, database=database, schema=schema, name=name, kind=kind, label=label)


def _add_dependencies(graph, rows, read_write, failed):
    for row in rows:
        source = object_id(row["database_name"], row["referencing_schema"], row["referencing_name"])
        if source not in graph.nodes:
            graph.warn("unknown_referencing_object", "referencing object missing from objects.csv", source)
            continue
        target = _referenced_id(row)
        target_kind = _add_referenced_node(graph, row, target)["kind"]
        source_kind = graph.nodes[source]["kind"]
        if target_kind == "procedure":
            graph.add_edge(source, target, "executes")
        elif target_kind == "function" or source_kind in ("view", "function"):
            graph.add_edge(target, source, "reads")
        elif (source, target) in read_write:
            selected, updated = read_write[(source, target)]
            if selected:
                graph.add_edge(target, source, "reads")
            if updated:
                graph.add_edge(source, target, "writes")
            if not (selected or updated):
                graph.add_edge(source, target, "references")
        else:
            graph.add_edge(source, target, "references")
            if source not in failed and source_kind in ("procedure", "trigger"):
                graph.warn("read_write_unknown", "no read/write row for this reference; direction unknown", source)


def _add_gaps(graph, rows):
    for row in rows:
        node_id = object_id(row["database_name"], row["schema_name"], row["object_name"])
        if node_id not in graph.nodes:
            continue
        gaps = [label for column, label in GAP_FLAGS if row.get(column) == "1"]
        if gaps:
            graph.nodes[node_id]["gaps"] = gaps
            graph.warn("dynamic_sql", f"uses {', '.join(gaps)}; the catalog cannot see these dependencies", node_id)


def _job_patterns(node):
    schema, name = re.escape(node["schema"]), re.escape(node["name"])
    patterns = [re.compile(rf"(?<![\w]){schema}\.{name}(?![\w])", re.IGNORECASE)]
    if node["schema"].lower() == "dbo":
        patterns.append(re.compile(rf"(?<![\w.]){name}(?![\w])", re.IGNORECASE))
    return patterns


def _add_jobs(graph, rows):
    procedures = [n for n in graph.nodes.values() if n["kind"] == "procedure"]
    patterns = {n["id"]: _job_patterns(n) for n in procedures}
    for row in rows:
        job_id = f"job:{row['job_name']}".lower()
        step = int(row["step_id"])
        if row["command_truncated"] == "1":
            graph.warn("job_command_truncated", f"step {step} command was truncated at export; review manually", job_id)
        if (row["subsystem"] or "").upper() != "TSQL":
            graph.warn("job_step_not_parsed", f"step {step} uses subsystem {row['subsystem']}; not parsed", job_id)
            continue
        command = (row["command"] or "").replace("[", "").replace("]", "")
        for node in procedures:
            if row["database_name"] and node["database"].lower() != row["database_name"].lower():
                continue
            if any(p.search(command) for p in patterns[node["id"]]):
                graph.add_node(job_id, database=None, schema=None, name=row["job_name"], kind="job", label=row["job_name"])
                graph.add_edge(
                    job_id,
                    node["id"],
                    "runs",
                    confidence="parsed",
                    job_step=step,
                    job_enabled=row["job_enabled"] == "1",
                )


def resolve(graph, name):
    """Resolve 'schema.name', 'db.schema.name' or a node id to exactly one node id."""
    wanted = name.replace("[", "").replace("]", "").lower()
    if wanted in graph.nodes:
        return wanted
    matches = [node_id for node_id in graph.nodes if node_id.endswith("." + wanted)]
    if len(matches) != 1:
        problem = "not found" if not matches else f"ambiguous ({', '.join(sorted(matches))})"
        raise InputError(f"object {name} {problem}")
    return matches[0]


def _add_inferred(graph, rows):
    for number, row in enumerate(rows, start=2):
        evidence, kind = row.get("evidence"), (row.get("kind") or "").lower()
        if not evidence or not EVIDENCE.match(evidence):
            raise InputError(f"inferred_edges.csv line {number}: evidence must be file:line")
        if kind not in INFERRED_KINDS:
            raise InputError(f"inferred_edges.csv line {number}: kind must be one of {sorted(INFERRED_KINDS)}")
        source, target = resolve(graph, row["from"]), resolve(graph, row["to"])
        graph.add_edge(source, target, kind, confidence="inferred", evidence=evidence)


# --------------------------------------------------------------------------- analysis


def depends_on(nodes, edges):
    """Map each node to the nodes it needs first (data and call order)."""
    writes = {(e["from"], e["to"]) for e in edges if e["kind"] == "writes"}
    depends = {node_id: set() for node_id in nodes}
    for e in edges:
        source, target, kind = e["from"], e["to"], e["kind"]
        if source not in depends or target not in depends:
            continue
        if kind == "reads" and (target, source) not in writes:
            depends[target].add(source)
        elif kind == "writes":
            depends[target].add(source)
        elif kind in ("executes", "references"):
            depends[source].add(target)
    return depends


def compute_waves(nodes, depends):
    """Topological levels over strongly connected components (iterative Tarjan)."""
    index, low, on_stack, stack, components = {}, {}, set(), [], []
    counter = 0
    for root in sorted(nodes):
        if root in index:
            continue
        work = [(root, iter(sorted(depends.get(root, ()))))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            child = next(children, None)
            if child is not None:
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(depends.get(child, ())))))
                elif child in on_stack:
                    low[node] = min(low[node], index[child])
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(sorted(component))
    level, component_of = {}, {}
    for number, component in enumerate(components):
        for member in component:
            component_of[member] = number
    for number, component in enumerate(components):
        deps = {component_of[d] for m in component for d in depends.get(m, ()) if component_of[d] != number}
        level[number] = 1 + max((level[d] for d in deps), default=-1)
    waves = [[] for _ in range(1 + max(level.values(), default=-1))]
    for number, component in enumerate(components):
        waves[level[number]].extend(component)
    cycles = [c for c in components if len(c) > 1]
    return [sorted(w) for w in waves], sorted(cycles)


def _closure(start, neighbours, depth):
    seen, queue = set(start), deque((node, 0) for node in start)
    while queue:
        node, distance = queue.popleft()
        if depth is not None and distance >= depth:
            continue
        for nxt in neighbours.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, distance + 1))
    return seen


def focus_set(graph, focus, depth):
    start = {resolve(graph, name) for name in focus}
    edges = list(graph.edges.values())
    depends = depends_on(graph.nodes, edges)
    dependents = {}
    for node, needs in depends.items():
        for need in needs:
            dependents.setdefault(need, set()).add(node)
    keep = _closure(start, depends, depth) | _closure(start, dependents, depth)
    callers = {}
    for e in edges:
        if e["kind"] in ("executes", "runs"):
            callers.setdefault(e["to"], set()).add(e["from"])
    return keep | _closure(keep, callers, None)


def repo_presence(graph, repo_sql, keep):
    root = Path(repo_sql)
    found = {}
    for path in sorted(root.rglob("*.sql")):
        for number, line in enumerate(read_text(path).splitlines(), start=1):
            match = REPO_DDL.match(line)
            if not match:
                continue
            parts = match.group(1).replace("[", "").replace("]", "").split(".")
            if parts[-1].startswith("#"):
                continue
            key = ".".join((["dbo"] + parts)[-2:]).lower()
            found.setdefault(key, f"{path.relative_to(root).as_posix()}:{number}")
    catalog = {
        node_id: f"{n['schema']}.{n['name']}".lower()
        for node_id, n in graph.nodes.items()
        if n["kind"] not in ("external", "missing", "unresolved", "job")
    }
    known = set(catalog.values())
    return {
        "in_database_not_in_repo": sorted(i for i, key in catalog.items() if i in keep and key not in found),
        "in_repo_not_in_database": [
            {"object": key, "location": location} for key, location in sorted(found.items()) if key not in known
        ],
    }


def build(inputs, focus=None, depth=None, repo_sql=None):
    graph = Graph()
    _add_objects(graph, inputs["objects.csv"])
    read_write, failed = _read_write_index(graph, inputs.get("read_write.csv", []))
    _add_dependencies(graph, inputs["dependencies.csv"], read_write, failed)
    _add_gaps(graph, inputs.get("dynamic_sql.csv", []))
    _add_jobs(graph, inputs.get("jobs.csv", []))
    _add_inferred(graph, inputs.get("inferred_edges.csv", []))

    keep = focus_set(graph, focus, depth) if focus else set(graph.nodes)
    nodes = {i: n for i, n in graph.nodes.items() if i in keep}
    edges = sorted(
        (e for e in graph.edges.values() if e["from"] in keep and e["to"] in keep),
        key=lambda e: (e["from"], e["to"], e["kind"]),
    )
    data_nodes = [i for i, n in nodes.items() if n["kind"] != "job"]
    waves, cycles = compute_waves(data_nodes, depends_on(data_nodes, edges))
    warnings = [w for w in graph.warnings if w.get("object") is None or w["object"] in keep]
    for cycle in cycles:
        warnings.append({"code": "cycle", "message": "objects depend on each other; they share one wave", "objects": cycle})

    lineage = {
        "generated_by": "build_lineage.py",
        "focus": list(focus or []),
        "depth": depth,
        "nodes": [nodes[i] for i in sorted(nodes)],
        "edges": edges,
        "waves": waves,
        "warnings": warnings,
    }
    if repo_sql:
        lineage["repo"] = repo_presence(graph, repo_sql, keep)
    return lineage


# --------------------------------------------------------------------------- output

SHAPES = {
    "table": "[({})]",
    "view": "[/{}/]",
    "procedure": "[{}]",
    "trigger": "[{}]",
    "function": "[[{}]]",
    "synonym": "([{}])",
    "job": "{{{{{}}}}}",
}
SAFE_LABEL = re.compile(r"^[\w .:?-]+$")


def to_mermaid(lineage):
    ids = {node["id"]: f"n{number}" for number, node in enumerate(lineage["nodes"], start=1)}
    lines = ["flowchart LR"]
    for node in lineage["nodes"]:
        label = node["label"] if SAFE_LABEL.match(node["label"]) else '"' + node["label"].replace('"', "#quot;") + '"'
        lines.append(f"    {ids[node['id']]}{SHAPES.get(node['kind'], '>{}]').format(label)}")
    for edge in lineage["edges"]:
        arrow = "-->" if edge["confidence"] != "inferred" and edge["kind"] != "references" else "-.->"
        lines.append(f"    {ids[edge['from']]} {arrow}|{edge['kind']}| {ids[edge['to']]}")
    gaps = [ids[n["id"]] for n in lineage["nodes"] if n["gaps"]]
    if gaps:
        lines.append("    classDef gap stroke:#d97706,stroke-width:3px")
        lines.append(f"    class {','.join(gaps)} gap")
    legend = "Dashed arrows: inferred or direction unknown. Orange border: dynamic SQL, review manually."
    return "# Lineage\n\n" + legend + "\n\n```mermaid\n" + "\n".join(lines) + "\n```\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="source", required=True, help="folder with the CSV exports")
    parser.add_argument("--out", required=True, help="lineage JSON to write")
    parser.add_argument("--focus", action="append", help="object to center on (schema.name); repeatable")
    parser.add_argument("--depth", type=int, help="max data hops from the focus objects")
    parser.add_argument("--repo-sql", help="folder with the repository .sql files to compare against the catalog")
    parser.add_argument("--mermaid", help="also write a Markdown file with a Mermaid diagram")
    args = parser.parse_args(argv)
    try:
        lineage = build(load_inputs(args.source), focus=args.focus, depth=args.depth, repo_sql=args.repo_sql)
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lineage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.mermaid:
        Path(args.mermaid).write_text(to_mermaid(lineage), encoding="utf-8")
    print(
        f"{len(lineage['nodes'])} objects, {len(lineage['edges'])} edges, "
        f"{len(lineage['waves'])} waves, {len(lineage['warnings'])} warnings -> {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
