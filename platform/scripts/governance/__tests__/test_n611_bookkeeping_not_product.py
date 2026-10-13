"""test_n611_bookkeeping_not_product.py: SS N-611 (REGISTRY_REVISION 31, Build.dag revision 5): an orchestrator BOOKKEEPING table is never produced by an asset.

The incident: Kala migrations 1353-1356 put `public.build_runs` in the count_sql of ka_jivana_parva, ka_kala_darshana and ka_kalasutra (the count follows the newest build run). build_table_owners made every
active writer-backed asset "own" its target_table PLUS each FROM/JOIN relation of its count_sql, so build_runs became a table PRODUCED by those three assets, and ga_vichara_writer's
`SELECT created_at FROM build_runs WHERE id = %s` read as a back-read of another (downstream) asset's table: Build.dag FAIL for a read of orchestrator bookkeeping.

The fix skips BOOKKEEPING_TABLES in build_table_owners (target_table AND count_sql relations). These tests pin it end to end (owner map, then the real Build.dag detector through produced_table_owners), pin that a
REAL undeclared read still fails (the fix cannot hide one), and run paired mutants of the function: each wrong exclusion is caught. Offline: the `_stub_layer` harness plus a python-sidecar tree on disk; no database.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as pa  # noqa: E402
import test_e6_gh_declared_service_and_reads_match as gh  # noqa: E402  (the Build.dag harness of work-list item (h))

# The three Kala rows exactly as migrations 1353-1356 left them in the registry (count_sql shape, abbreviated to the part that names the relations).
_KA_COUNT = ("SELECT COUNT(*) FROM ( SELECT chart_id,'legacy'::text generation FROM public.{t} UNION ALL SELECT chart_id,generation FROM public.{t}_candidate ) model_rows "
             "WHERE chart_id = $1 AND generation=COALESCE(( SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END FROM public.build_runs b "
             "LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1 ),'legacy')")
KA_ROWS = [("ka_jivana_parva", "kala_jivana_parva", _KA_COUNT.format(t="kala_jivana_parva"), True),
           ("ka_kala_darshana", "kala_darshana", _KA_COUNT.format(t="kala_darshana"), True),
           ("ka_kalasutra", "kala_activation", _KA_COUNT.format(t="kala_activation"), True)]
KA_OWNED = {"kala_jivana_parva": ["ka_jivana_parva"], "kala_jivana_parva_candidate": ["ka_jivana_parva"],
            "kala_darshana": ["ka_kala_darshana"], "kala_darshana_candidate": ["ka_kala_darshana"],
            "kala_activation": ["ka_kalasutra"], "kala_activation_candidate": ["ka_kalasutra"],
            "kala_layer_candidate": ["ka_jivana_parva", "ka_kala_darshana", "ka_kalasutra"]}

# ga_vichara_writer.py:1002 reads the build's creation time; the reader here is the existing harness asset `ka_up`.
READS_BUILD_RUNS = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
                    '        ctx.db_conn.execute("SELECT created_at FROM build_runs WHERE id = %s", (1,))\n')
READS_BUILD_RUNS_AND_UP_T = READS_BUILD_RUNS + '        ctx.db_conn.execute("SELECT x FROM up_t WHERE chart_id = %s", (1,))\n'


# ───────────────────────────────────── the owner map ─────────────────────────────────────

def test_the_kala_count_sql_joins_of_build_runs_do_not_make_those_assets_its_owners():
    got = ac.build_table_owners(KA_ROWS + [("ga_vichara", "chart_vichara", "SELECT COUNT(*) FROM chart_vichara", True)])
    assert "build_runs" not in got, got
    assert got == {**KA_OWNED, "chart_vichara": ["ga_vichara"]}, got      # every other relation keeps its owners; only build_runs changed


def test_every_bookkeeping_table_is_skipped_in_either_position_and_in_any_spelling():
    assert ac.BOOKKEEPING_TABLES == frozenset({"asset_throughput", "build_runs", "build_run_assets", "build_substep_progress", "asset_provenance_receipts", "orchestrator_event_register"})
    for t in sorted(ac.BOOKKEEPING_TABLES):
        rows = [("a_count", "real_a", f"SELECT COUNT(*) FROM real_a JOIN public.{t.upper()} x ON x.id = real_a.id", True),
                ("a_target", t, "SELECT COUNT(*) FROM real_b", True),
                ("a_target_cased", t.title(), "", True)]
        assert ac.build_table_owners(rows) == {"real_a": ["a_count"], "real_b": ["a_target"]}, t


def test_an_asset_whose_only_table_is_a_bookkeeping_table_owns_nothing_and_nothing_crashes():
    assert ac.build_table_owners([("ka_only_bk", "build_runs", "SELECT COUNT(*) FROM build_runs", True)]) == {}
    assert ac.build_table_owners([("ka_only_bk", "build_runs", None, True), ("ka_none", None, None, True), ("ka_empty", "", "", True)]) == {}


def test_a_real_table_whose_name_merely_contains_build_is_still_owned():
    got = ac.build_table_owners([("a", "chart_build_notes", "SELECT COUNT(*) FROM chart_build_notes", True), ("b", "kala_rebuild_log", "", True)])
    assert got == {"chart_build_notes": ["a"], "kala_rebuild_log": ["b"]}, got


def test_a_writerless_asset_still_owns_nothing():
    assert ac.build_table_owners([("lel_events", "life_events", "SELECT COUNT(*) FROM life_events", False)]) == {}


# ───────────────────────────── Build.dag through the real owner map ─────────────────────────────

def _dag(monkeypatch, tmp_path, body, rows, *, graph=None, depends_on=()):
    """Build.dag record of the reader asset `ka_up` over registry `rows` [(asset_id, target_table, count_sql, has_writer)]: the owners come from the REAL
    produced_table_owners (its registry JSON read patched), not from a hand-written map."""
    gh._side(monkeypatch, tmp_path, body)
    reg = {"ka_up": pa._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up", depends_on=depends_on)}
    for aid, t, c, w in rows:
        reg[aid] = pa._reg_row(aid, t, has_writer=w, count_sql=c)
    pa._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    blob = json.dumps([dict(a=aid, t=t, c=c or "", w=w) for aid, t, c, w in [("ka_up", "kala_up", "SELECT count(*) FROM kala_up", True), *rows]])
    real_scalar = ac.scalar

    def scalar(sql):
        return blob if "json_agg(json_build_object('a',asset_id" in sql else real_scalar(sql)
    monkeypatch.setattr(ac, "scalar", scalar)
    if graph is not None:
        monkeypatch.setattr(ac, "dependency_graph", lambda: dict(graph))
    c = ac.measure("L0")
    return next(a for a in c["assets"] if a["asset_id"] == "ka_up")["measurements"]["Build.dag"]


def test_incident_a_writer_reading_build_runs_stays_pass_when_kala_count_sql_joins_it(monkeypatch, tmp_path):
    rec = _dag(monkeypatch, tmp_path, READS_BUILD_RUNS, KA_ROWS)
    assert rec["v"] == ac.PASS, rec
    assert not rec.get("missing_edges"), rec


def test_a_real_undeclared_read_still_fails_beside_the_build_runs_read(monkeypatch, tmp_path):
    rows = KA_ROWS + [("bg_up", "up_t", "SELECT count(*) FROM up_t", True)]
    rec = _dag(monkeypatch, tmp_path, READS_BUILD_RUNS_AND_UP_T, rows)
    assert rec["v"] == ac.FAIL, rec
    assert [(m["table"], m["needs"], m["kind"]) for m in rec["missing_edges"]] == [("up_t", "bg_up", "missing_edge")], rec      # only the real table; build_runs is no finding


def test_a_real_back_read_of_a_downstream_assets_table_still_fails(monkeypatch, tmp_path):
    """The same shape as the incident, with a table that IS produced: bg_up depends on ka_up and owns up_t, so ka_up reading up_t is a back_read, not hidden by the fix."""
    rows = KA_ROWS + [("bg_up", "up_t", "SELECT count(*) FROM up_t", True)]
    rec = _dag(monkeypatch, tmp_path, READS_BUILD_RUNS_AND_UP_T, rows, graph={"ka_up": [], "bg_up": ["ka_up"], **{r[0]: [] for r in KA_ROWS}})
    assert rec["v"] == ac.FAIL, rec
    assert [(m["table"], m["kind"]) for m in rec["missing_edges"]] == [("up_t", "back_read")], rec


def test_an_assets_own_bookkeeping_target_table_is_no_owner_and_the_read_is_not_a_finding(monkeypatch, tmp_path):
    rows = [("ka_bk", "build_runs", "SELECT COUNT(*) FROM build_runs", True)]
    rec = _dag(monkeypatch, tmp_path, READS_BUILD_RUNS, rows)
    assert rec["v"] == ac.PASS, rec


def test_the_registry_text_carries_the_sentence_and_the_revision():
    e = ac.CRITERION_REGISTRY["Build.dag"]
    assert e["revision"] == 5 and ac.REGISTRY_REVISION >= 31
    sentence = "orchestrator bookkeeping tables (BOOKKEEPING_TABLES) are never produced by an asset: a read of one is not a read of another asset's table"
    assert e["applicability"].count(sentence) == 1 and e["applicability"].endswith(sentence)
    assert e["applicability"].startswith("always; SS 2026-10-05 R-d:")       # the earlier text is kept verbatim in front of the one appended sentence


# ───────────────────────────────────────── paired mutants ─────────────────────────────────────────

_REAL_SRC = inspect.getsource(ac.build_table_owners)
_SKIP = ("            if t.lower() in BOOKKEEPING_TABLES:\n"
         "                continue          # N-611: an orchestrator-written table is never a product of an asset (see the docstring)\n")


def _mutant(new_skip: str):
    """build_table_owners with the exclusion block replaced by `new_skip`; the site must exist exactly once (a mutant that changes nothing is a mistake, not a survivor)."""
    assert _REAL_SRC.count(_SKIP) == 1, "the exclusion block moved: update _SKIP"
    mutated = _REAL_SRC.replace(_SKIP, new_skip)
    assert mutated != _REAL_SRC
    ns = dict(vars(ac))
    exec(compile(mutated, "<mutant>", "exec"), ns)
    return ns["build_table_owners"]


def _violations(fn, monkeypatch, tmp_path) -> list[str]:
    """What a build_table_owners must satisfy for the incident AND for the guarantees the fix may not cost; the failed items, by name."""
    bad: list[str] = []
    monkeypatch.setattr(ac, "build_table_owners", fn)
    probes = {
        "incident count_sql join": lambda: "build_runs" not in fn(KA_ROWS),
        "target_table bookkeeping": lambda: fn([("x", "build_runs", "", True)]) == {},
        "target_table bookkeeping, cased": lambda: fn([("x", "Build_Runs", "", True)]) == {},
        "count_sql keeps the other relations": lambda: fn(KA_ROWS) == KA_OWNED,
        "name with 'build' stays owned": lambda: fn([("a", "chart_build_notes", "", True)]) == {"chart_build_notes": ["a"]},
        "writerless owns nothing": lambda: fn([("l", "life_events", "", False)]) == {},
    }
    for name, probe in probes.items():
        try:
            ok = probe()
        except Exception as exc:                                # noqa: BLE001 (a crash is a violation)
            ok = False
            name = f"{name} (raised {type(exc).__name__})"
        if not ok:
            bad.append(name)
    return bad


def test_the_real_function_satisfies_every_probe(monkeypatch, tmp_path):
    assert _violations(ac.build_table_owners, monkeypatch, tmp_path) == []


def _cond(expr: str) -> str:
    return _SKIP.replace("t.lower() in BOOKKEEPING_TABLES", expr)


MUTANTS = {
    "remove the exclusion": "",
    "exclude every table with 'build' in the name": _cond('"build" in t.lower()'),
    "exclude only the target_table, not the count_sql relations": _cond("t == target and t.lower() in BOOKKEEPING_TABLES"),
    "exclude only the count_sql relations, not the target_table": _cond("t != target and t.lower() in BOOKKEEPING_TABLES"),
    "compare case-sensitively": _cond("t in BOOKKEEPING_TABLES"),
    "drop the rest of the asset's tables when it names a bookkeeping table": _SKIP.replace("continue          #", "break          #"),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_wrong_exclusion_is_caught(name, monkeypatch, tmp_path):
    assert _violations(_mutant(MUTANTS[name]), monkeypatch, tmp_path), f"mutant survived: {name}"


def test_the_mutant_without_the_exclusion_also_turns_the_real_dag_detector_red(monkeypatch, tmp_path):
    """Run THROUGH produced_table_owners and Build.dag, the mutant without the exclusion reproduces the incident verdict (the detector end of the same pair)."""
    monkeypatch.setattr(ac, "build_table_owners", _mutant(""))
    rec = _dag(monkeypatch, tmp_path, READS_BUILD_RUNS, KA_ROWS)
    assert rec["v"] == ac.FAIL, rec
    assert [m["table"] for m in rec["missing_edges"]] == ["build_runs"], rec
