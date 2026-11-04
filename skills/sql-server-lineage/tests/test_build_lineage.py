"""Tests for build_lineage.py. Run: python -m unittest discover -s skills/sql-server-lineage/tests"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAYBOOK = HERE.parent
SCRIPT = PLAYBOOK / "build_lineage.py"
SQLCMD = HERE / "fixtures" / "sqlcmd"
SSMS = HERE / "fixtures" / "ssms"
REPO = HERE / "fixtures" / "repo"

sys.path.insert(0, str(PLAYBOOK))
import build_lineage  # noqa: E402


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
    )


def edge_set(lineage, kind=None):
    return {
        (e["from"], e["to"], e["kind"])
        for e in lineage["edges"]
        if kind is None or e["kind"] == kind
    }


def wave_of(lineage, node_id):
    for index, wave in enumerate(lineage["waves"]):
        if node_id in wave:
            return index
    return None


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lineage-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copy_inputs(self, source=SQLCMD, skip=()):
        target = self.tmp / "in"
        target.mkdir()
        for path in source.iterdir():
            if path.name not in skip:
                shutil.copy(path, target / path.name)
        return target


class ReadTableTests(TempDirTestCase):
    def test_reads_sqlcmd_pipe_format_skipping_dash_row_and_nulls(self):
        rows = build_lineage.read_table(SQLCMD / "dependencies.csv")
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]["referencing_name"], "LoadPositions")
        self.assertIsNone(rows[0]["referenced_server_name"])

    def test_reads_ssms_comma_format(self):
        rows = build_lineage.read_table(SSMS / "objects.csv")
        self.assertEqual([r["object_name"] for r in rows], ["Orders", "LoadOrders"])

    def test_reads_utf16_unicode_output(self):
        path = self.tmp / "objects.csv"
        text = "database_name|schema_name|object_name|object_type|type_desc|modify_date\nDb|dbo|Café|U|USER_TABLE|x\n"
        path.write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))
        rows = build_lineage.read_table(path)
        self.assertEqual(rows[0]["object_name"], "Café")


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lineage = build_lineage.build(build_lineage.load_inputs(SQLCMD))

    def test_read_write_flags_set_data_flow_direction(self):
        edges = edge_set(self.lineage)
        self.assertIn(("warehousedb.stg.rawtrades", "warehousedb.dw.loadpositions", "reads"), edges)
        self.assertIn(("warehousedb.dw.calcpnl", "warehousedb.dw.pnl", "writes"), edges)
        self.assertIn(("warehousedb.dw.positions", "warehousedb.dw.calcpnl", "reads"), edges)

    def test_procedure_calls_become_executes_edges(self):
        self.assertIn(
            ("warehousedb.dw.rundaily", "warehousedb.dw.loadpositions", "executes"),
            edge_set(self.lineage),
        )

    def test_view_reads_without_read_write_rows(self):
        self.assertIn(("warehousedb.dw.pnl", "warehousedb.rpt.vpnl", "reads"), edge_set(self.lineage))

    def test_cross_database_reference_is_external_node(self):
        nodes = {n["id"]: n for n in self.lineage["nodes"]}
        self.assertEqual(nodes["refdb.ref.fxrates"]["kind"], "external")
        self.assertIn(("refdb.ref.fxrates", "warehousedb.dw.calcpnl", "reads"), edge_set(self.lineage))

    def test_failed_read_write_lookup_falls_back_to_references_with_warning(self):
        self.assertIn(
            ("warehousedb.dw.dynamicloader", "warehousedb.?.sometable", "references"),
            edge_set(self.lineage),
        )
        codes = {(w["code"], w.get("object")) for w in self.lineage["warnings"]}
        self.assertIn(("read_write_unavailable", "warehousedb.dw.dynamicloader"), codes)
        self.assertIn(("unresolved_reference", "warehousedb.?.sometable"), codes)

    def test_dynamic_sql_objects_are_marked_as_gaps(self):
        nodes = {n["id"]: n for n in self.lineage["nodes"]}
        self.assertEqual(nodes["warehousedb.dw.dynamicloader"]["gaps"], ["sp_executesql"])
        self.assertEqual(nodes["warehousedb.dw.calcpnl"]["gaps"], [])

    def test_job_steps_run_procedures_they_name(self):
        runs = [e for e in self.lineage["edges"] if e["kind"] == "runs"]
        targets = {(e["from"], e["to"], e["job_step"]) for e in runs}
        self.assertIn(("job:daily load", "warehousedb.dw.rundaily", 1), targets)
        self.assertTrue(all(e["confidence"] == "parsed" for e in runs))

    def test_job_step_schema_qualified_name_does_not_match_other_schema(self):
        runs = edge_set(self.lineage, "runs")
        self.assertFalse(any(source == "job:other job" for source, _, _ in runs))

    def test_ssis_and_truncated_job_steps_are_warned(self):
        codes = {w["code"] for w in self.lineage["warnings"]}
        self.assertIn("job_step_not_parsed", codes)
        self.assertIn("job_command_truncated", codes)

    def test_inferred_edges_keep_evidence_and_confidence(self):
        inferred = [e for e in self.lineage["edges"] if e["confidence"] == "inferred"]
        self.assertEqual(len(inferred), 1)
        self.assertEqual(inferred[0]["to"], "warehousedb.stg.positions")
        self.assertEqual(inferred[0]["evidence"], "sql/dw/DynamicLoader.sql:42")

    def test_waves_follow_data_order_and_ignore_in_place_updates(self):
        lineage = self.lineage
        self.assertEqual(wave_of(lineage, "warehousedb.stg.rawtrades"), 0)
        self.assertEqual(wave_of(lineage, "warehousedb.dw.loadpositions"), 1)
        self.assertEqual(wave_of(lineage, "warehousedb.dw.positions"), 2)
        self.assertEqual(wave_of(lineage, "warehousedb.dw.calcpnl"), 3)
        self.assertEqual(wave_of(lineage, "warehousedb.dw.pnl"), 4)
        self.assertEqual(wave_of(lineage, "warehousedb.rpt.vpnl"), 5)
        self.assertIsNone(wave_of(lineage, "job:daily load"))

    def test_cycle_shares_one_wave_and_is_warned(self):
        nodes = ["a", "b", "c"]
        depends = {"a": {"b"}, "b": {"a"}, "c": {"a"}}
        waves, cycles = build_lineage.compute_waves(nodes, depends)
        self.assertEqual(waves, [["a", "b"], ["c"]])
        self.assertEqual(cycles, [["a", "b"]])


class FocusTests(unittest.TestCase):
    def test_focus_keeps_upstream_downstream_and_callers(self):
        inputs = build_lineage.load_inputs(SQLCMD)
        lineage = build_lineage.build(inputs, focus=["dw.PnL"])
        ids = {n["id"] for n in lineage["nodes"]}
        expected = {
            "warehousedb.dw.pnl",
            "warehousedb.dw.calcpnl",
            "warehousedb.dw.positions",
            "warehousedb.dw.loadpositions",
            "warehousedb.stg.rawtrades",
            "refdb.ref.fxrates",
            "warehousedb.rpt.vpnl",
            "warehousedb.dw.rundaily",
            "job:daily load",
            "job:long job",
        }
        self.assertEqual(ids, expected)
        disabled = [e for e in lineage["edges"] if e["from"] == "job:long job"]
        self.assertEqual([e["job_enabled"] for e in disabled], [False])
        self.assertTrue(all(e["from"] in ids and e["to"] in ids for e in lineage["edges"]))

    def test_depth_limits_data_closure(self):
        inputs = build_lineage.load_inputs(SQLCMD)
        lineage = build_lineage.build(inputs, focus=["dw.PnL"], depth=1)
        ids = {n["id"] for n in lineage["nodes"]}
        self.assertIn("warehousedb.dw.calcpnl", ids)
        self.assertIn("warehousedb.rpt.vpnl", ids)
        self.assertNotIn("warehousedb.dw.positions", ids)

    def test_unknown_focus_is_an_input_error(self):
        inputs = build_lineage.load_inputs(SQLCMD)
        with self.assertRaises(build_lineage.InputError):
            build_lineage.build(inputs, focus=["dw.DoesNotExist"])


class RepoPresenceTests(unittest.TestCase):
    def test_compares_catalog_with_repository_sql(self):
        inputs = build_lineage.load_inputs(SQLCMD)
        lineage = build_lineage.build(inputs, repo_sql=REPO)
        not_in_db = {item["object"]: item["location"] for item in lineage["repo"]["in_repo_not_in_database"]}
        self.assertEqual(list(not_in_db), ["dw.legacy"])
        self.assertTrue(not_in_db["dw.legacy"].endswith("procs.sql:12"))
        missing = set(lineage["repo"]["in_database_not_in_repo"])
        self.assertIn("warehousedb.dw.rundaily", missing)
        self.assertNotIn("warehousedb.dw.loadpositions", missing)
        self.assertNotIn("warehousedb.dw.calcpnl", missing)
        self.assertNotIn("warehousedb.dw.positions", missing)


class CliTests(TempDirTestCase):
    def test_writes_json_and_mermaid(self):
        out = self.tmp / "lineage.json"
        md = self.tmp / "lineage.md"
        result = run_cli("--in", SQLCMD, "--out", out, "--mermaid", md)
        self.assertEqual(result.returncode, 0, result.stderr)
        lineage = json.loads(out.read_text(encoding="utf-8"))
        self.assertIn("waves", lineage)
        mermaid = md.read_text(encoding="utf-8")
        self.assertIn("```mermaid", mermaid)
        self.assertIn("-.->|writes|", mermaid)
        self.assertIn("[(stg.RawTrades)]", mermaid)

    def test_optional_inputs_may_be_missing(self):
        source = self.copy_inputs(skip={"read_write.csv", "jobs.csv", "dynamic_sql.csv", "inferred_edges.csv"})
        result = run_cli("--in", source, "--out", self.tmp / "lineage.json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_required_input_exits_2(self):
        source = self.copy_inputs(skip={"dependencies.csv"})
        result = run_cli("--in", source, "--out", self.tmp / "lineage.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("dependencies.csv", result.stderr)

    def test_inferred_edge_without_evidence_exits_2(self):
        source = self.copy_inputs()
        (source / "inferred_edges.csv").write_text(
            "from,to,kind,evidence\ndw.DynamicLoader,stg.Positions,writes,\n", encoding="utf-8"
        )
        result = run_cli("--in", source, "--out", self.tmp / "lineage.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("evidence", result.stderr)

    def test_inferred_edge_to_unknown_object_exits_2(self):
        source = self.copy_inputs()
        (source / "inferred_edges.csv").write_text(
            "from,to,kind,evidence\ndw.DynamicLoader,dw.Nope,writes,a.sql:1\n", encoding="utf-8"
        )
        result = run_cli("--in", source, "--out", self.tmp / "lineage.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("dw.Nope", result.stderr)


if __name__ == "__main__":
    unittest.main()
