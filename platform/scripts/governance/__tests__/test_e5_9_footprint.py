"""test_e5_9_footprint.py -- Suvarna E5.9: transitive write/delete footprint from the pg_constraint closure.

Fixture-only: no database. The loader is exercised against a fake DB-API cursor.

Golden closures
  FIXTURE_2026_09_30  the closure measured on 2026-09-30 (TRACK_E_BRIEF section 4a): eight FKs into
                      bodha_msr_signals from seven tables, all ON DELETE CASCADE (migrations 403 / 404);
                      kala_convergence -> kala_darshana, kala_obstruction, phala_anchors (CASCADE) and
                      kala_bhavishya (SET NULL); phala_anchors -> phala_pramana, phala_sankrama, phala_sodhana,
                      phala_suddha_sodhana (CASCADE) and phala_mitigation, phala_muhurta (SET NULL).
                      HISTORICAL: migration 1214 dropped five of the kala_* keys afterwards.
  FIXTURE_POST_1214   the same closure with the five kala_* -> bodha_msr_signals keys removed (what is current
                      on main: platform/supabase/migrations/1214_f3_drop_kala_msr_signal_fks.sql).
"""
from __future__ import annotations

import json
import pathlib
import random
import sys
import threading

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_level_wave as slw  # noqa: E402


# ───────────────────────── fixture builders ─────────────────────────

def E(child, parent, on_delete="CASCADE", columns=None, not_null=(), constraint=None, on_update="NO ACTION"):
    cols = list(columns) if columns is not None else [parent.split(".")[-1] + "_id"]
    return {
        "child_table": child, "parent_table": parent, "on_delete": on_delete, "on_update": on_update,
        "columns": cols, "child_columns_not_null": list(not_null),
        "constraint": constraint or f"{child.split('.')[-1]}_{'_'.join(cols)}_fkey",
    }


def _msr_edges_pre_1214():
    p = "public.bodha_msr_signals"
    return [
        E("public.kala_activation", p, "CASCADE", ["signal_id"], not_null=["signal_id"]),
        E("public.kala_bhavishya", p, "CASCADE", ["signal_id"]),
        E("public.kala_convergence", p, "CASCADE", ["signal_id"]),
        E("public.kala_darshana", p, "CASCADE", ["signal_id"]),
        E("public.kala_obstruction", p, "CASCADE", ["signal_id"]),
        E("public.bodha_contradictions", p, "CASCADE", ["signal_a_id"], not_null=["signal_a_id"]),
        E("public.bodha_contradictions", p, "CASCADE", ["signal_b_id"], not_null=["signal_b_id"]),
        E("public.bodha_signal_embeddings", p, "CASCADE", ["signal_id"], not_null=["signal_id"]),
    ]


def _downstream_edges():
    kc, pa = "public.kala_convergence", "public.phala_anchors"
    return [
        E("public.kala_darshana", kc, "CASCADE", ["convergence_id"]),
        E("public.kala_obstruction", kc, "CASCADE", ["convergence_id"]),
        E("public.phala_anchors", kc, "CASCADE", ["convergence_id"]),
        E("public.kala_bhavishya", kc, "SET NULL", ["convergence_id"]),
        E("public.phala_pramana", pa, "CASCADE", ["anchor_id"], not_null=["anchor_id"]),
        E("public.phala_sankrama", pa, "CASCADE", ["source_anchor_id"]),
        E("public.phala_sodhana", pa, "CASCADE", ["anchor_id"], not_null=["anchor_id"]),
        E("public.phala_suddha_sodhana", pa, "CASCADE", ["anchor_id"], not_null=["anchor_id"]),
        E("public.phala_mitigation", pa, "SET NULL", ["linked_anchor_id"]),
        E("public.phala_muhurta", pa, "SET NULL", ["linked_anchor_id"]),
    ]


FIXTURE_2026_09_30 = _msr_edges_pre_1214() + _downstream_edges()
_DROPPED_1214 = {"kala_activation", "kala_bhavishya", "kala_convergence", "kala_darshana", "kala_obstruction"}
FIXTURE_POST_1214 = [
    e for e in FIXTURE_2026_09_30
    if not (e["parent_table"] == "public.bodha_msr_signals" and e["child_table"].split(".")[-1] in _DROPPED_1214)
]

MSR = "public.bodha_msr_signals"
PHALA_CASCADED = ["public.phala_pramana", "public.phala_sankrama", "public.phala_sodhana",
                  "public.phala_suddha_sodhana"]


def _names(entries, key="table"):
    return [e[key] for e in entries]


def _entry(entries, table, key="table"):
    hits = [e for e in entries if e[key] == table]
    assert len(hits) == 1, (table, hits)
    return hits[0]


def _hop_tables(path):
    return [path[0]["from"]] + [h["to"] for h in path]


# ───────────────────────── golden closure: 2026-09-30 ─────────────────────────

def test_golden_msr_closure_2026_09_30_delete_cascades():
    fp = slw.transitive_footprint(["bodha_msr_signals"], FIXTURE_2026_09_30)
    assert fp["write_tables"] == [MSR]
    # eight FKs from seven tables: all seven direct, plus the Phala cascade reached through kala_convergence.
    assert _names(fp["delete_cascades"]) == sorted([
        "public.bodha_contradictions", "public.bodha_signal_embeddings", "public.kala_activation",
        "public.kala_bhavishya", "public.kala_convergence", "public.kala_darshana", "public.kala_obstruction",
        "public.phala_anchors", *PHALA_CASCADED])
    assert fp["counts"]["delete_cascades"] == 12
    direct = [e for e in fp["delete_cascades"] if e["depth"] == 1]
    assert len(direct) == 7  # eight FKs, seven tables (bodha_contradictions has two)


def test_golden_paths_are_full_chains():
    fp = slw.transitive_footprint([MSR], FIXTURE_2026_09_30)
    pramana = _entry(fp["delete_cascades"], "public.phala_pramana")
    assert pramana["depth"] == 3
    assert _hop_tables(pramana["path"]) == [MSR, "public.kala_convergence", "public.phala_anchors",
                                            "public.phala_pramana"]
    assert [h["on_delete"] for h in pramana["path"]] == ["CASCADE"] * 3
    assert pramana["path"][-1]["columns"] == ["anchor_id"]
    assert _entry(fp["delete_cascades"], "public.kala_activation")["depth"] == 1


def test_golden_set_null_leaves_and_also_deleted_flag():
    fp = slw.transitive_footprint([MSR], FIXTURE_2026_09_30)
    assert _names(fp["set_null"]) == ["public.kala_bhavishya", "public.phala_mitigation", "public.phala_muhurta"]
    bhav = _entry(fp["set_null"], "public.kala_bhavishya")
    # kala_bhavishya is also CASCADE-deleted via the signal key: its null-out is moot and the entry says so.
    assert bhav["child_also_deleted"] is True
    assert bhav["columns"] == ["convergence_id"]
    mit = _entry(fp["set_null"], "public.phala_mitigation")
    assert mit["child_also_deleted"] is False
    assert mit["violates_not_null"] is False
    assert mit["not_null_columns"] == []
    assert _hop_tables(mit["path"]) == [MSR, "public.kala_convergence", "public.phala_anchors",
                                        "public.phala_mitigation"]
    assert mit["path"][-1]["on_delete"] == "SET NULL"
    assert fp["refusing"] == []
    assert fp["counts"]["set_null"] == 3 and fp["counts"]["refusing"] == 0


def test_golden_wave_ka_sangam_write_set_is_kala_convergence():
    fp = slw.transitive_footprint(["public.kala_convergence"], FIXTURE_2026_09_30)
    assert _names(fp["delete_cascades"]) == sorted(
        ["public.kala_darshana", "public.kala_obstruction", "public.phala_anchors", *PHALA_CASCADED])
    assert _names(fp["set_null"]) == ["public.kala_bhavishya", "public.phala_mitigation", "public.phala_muhurta"]
    assert _entry(fp["set_null"], "public.kala_bhavishya")["child_also_deleted"] is False


# ───────────────────────── golden closure: post-1214 ─────────────────────────

def test_post_1214_msr_wave_no_longer_cascades_into_kala():
    assert len(FIXTURE_POST_1214) == len(FIXTURE_2026_09_30) - 5
    fp = slw.transitive_footprint([MSR], FIXTURE_POST_1214)
    assert _names(fp["delete_cascades"]) == ["public.bodha_contradictions", "public.bodha_signal_embeddings"]
    assert fp["set_null"] == [] and fp["refusing"] == []
    # the dropped keys are exactly the references the catalog can no longer see: never read as "clean".
    assert fp["dangling_after_rewrite"]["status"] == "unknown_not_in_catalog"
    assert fp["fk_closure_status"] == "COMPLETE"


def test_post_1214_known_non_fk_references_are_reported_not_dropped():
    known = [{"referencing_table": "kala_activation", "column": "signal_id", "referenced_table": "bodha_msr_signals"},
             {"referencing_table": "kala_obstruction", "column": "signal_id", "referenced_table": "bodha_msr_signals"},
             {"referencing_table": "elsewhere", "column": "x", "referenced_table": "other_table"}]
    fp = slw.transitive_footprint([MSR], FIXTURE_POST_1214, known_non_fk_references=known)
    d = fp["dangling_after_rewrite"]
    assert d["status"] == "unknown_not_in_catalog"
    assert [(r["referencing_table"], r["column"]) for r in d["known_non_fk_references"]] == [
        ("public.kala_activation", "signal_id"), ("public.kala_obstruction", "signal_id")]


# ───────────────────────── synthetic cases ─────────────────────────

def test_cascade_chain_depth_3_with_paths():
    edges = [E("s.b", "s.a"), E("s.c", "s.b"), E("s.d", "s.c")]
    fp = slw.transitive_footprint(["s.a"], edges)
    assert _names(fp["delete_cascades"]) == ["s.b", "s.c", "s.d"]
    d = _entry(fp["delete_cascades"], "s.d")
    assert d["depth"] == 3 and _hop_tables(d["path"]) == ["s.a", "s.b", "s.c", "s.d"]
    assert fp["counts"]["delete_cascades"] == 3


def test_set_null_leaf_does_not_propagate_deletes_further():
    edges = [E("s.leaf", "s.a", "SET NULL", ["a_id"]), E("s.under_leaf", "s.leaf", "CASCADE")]
    fp = slw.transitive_footprint(["s.a"], edges)
    assert fp["delete_cascades"] == []          # a nulled row is not a deleted row
    assert _names(fp["set_null"]) == ["s.leaf"]
    assert fp["set_null"][0]["violates_not_null"] is False


def test_set_null_on_not_null_column_is_a_blocker_not_a_quiet_null():
    edges = [E("s.leaf", "s.a", "SET NULL", ["a_id"], not_null=["a_id"])]
    fp = slw.transitive_footprint(["s.a"], edges)
    sn = fp["set_null"][0]
    assert sn["violates_not_null"] is True and sn["not_null_columns"] == ["a_id"]
    assert [r["kind"] for r in fp["refusing"]] == ["SET_NULL_ON_NOT_NULL"]
    assert fp["refusing"][0]["child_table"] == "s.leaf"


@pytest.mark.parametrize("code,kind", [("NO ACTION", "NO ACTION"), ("RESTRICT", "RESTRICT")])
def test_no_action_and_restrict_edges_are_refusing_blockers(code, kind):
    edges = [E("s.child", "s.a", code, ["a_id"])]
    fp = slw.transitive_footprint(["s.a"], edges)
    assert [(r["kind"], r["child_table"], r["parent_table"]) for r in fp["refusing"]] == [(kind, "s.child", "s.a")]
    assert fp["delete_cascades"] == [] and fp["counts"]["refusing"] == 1
    assert fp["has_blockers"] is True


def test_refusing_edge_below_a_cascade_is_found_with_its_path():
    edges = [E("s.b", "s.a"), E("s.c", "s.b", "RESTRICT", ["b_id"])]
    fp = slw.transitive_footprint(["s.a"], edges)
    r = fp["refusing"][0]
    assert r["parent_table"] == "s.b" and r["child_table"] == "s.c"
    assert _hop_tables(r["path"]) == ["s.a", "s.b", "s.c"]
    assert r["path"][-1]["on_delete"] == "RESTRICT"


def test_set_default_is_reported_in_its_own_category():
    edges = [E("s.child", "s.a", "SET DEFAULT", ["a_id"])]
    fp = slw.transitive_footprint(["s.a"], edges)
    assert _names(fp["set_default"]) == ["s.child"] and fp["counts"]["set_default"] == 1
    assert fp["set_null"] == [] and fp["refusing"] == []


def test_one_letter_catalog_codes_are_normalised():
    edges = [dict(E("s.b", "s.a"), on_delete="c"), dict(E("s.n", "s.a", columns=["x"]), on_delete="n"),
             dict(E("s.r", "s.a", columns=["y"]), on_delete="r"), dict(E("s.k", "s.a", columns=["z"]), on_delete="a")]
    fp = slw.transitive_footprint(["s.a"], edges)
    assert _names(fp["delete_cascades"]) == ["s.b"] and _names(fp["set_null"]) == ["s.n"]
    assert sorted(r["kind"] for r in fp["refusing"]) == ["NO ACTION", "RESTRICT"]


def test_invalid_on_delete_code_fails_loudly():
    with pytest.raises(ValueError):
        slw.transitive_footprint(["s.a"], [dict(E("s.b", "s.a"), on_delete="x")])


def _run_with_timeout(fn, seconds=5):
    box = {}

    def target():
        box["v"] = fn()

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(seconds)
    assert not t.is_alive(), "footprint did not terminate (cycle not guarded)"
    return box["v"]


def test_cycle_terminates_and_each_table_is_reported_once():
    edges = [E("s.b", "s.a"), E("s.c", "s.b"), E("s.a", "s.c")]  # a -> b -> c -> a
    fp = _run_with_timeout(lambda: slw.transitive_footprint(["s.a"], edges))
    assert _names(fp["delete_cascades"]) == ["s.b", "s.c"]     # a is the write set itself, not a side effect
    assert _entry(fp["delete_cascades"], "s.c")["depth"] == 2


def test_self_referencing_cascade_terminates():
    fp = _run_with_timeout(lambda: slw.transitive_footprint(["s.a"], [E("s.a", "s.a", "CASCADE", ["parent_id"])]))
    assert fp["delete_cascades"] == [] and fp["unknown_tables"] == []


def test_cycle_that_does_not_include_the_write_table():
    edges = [E("s.b", "s.a"), E("s.c", "s.b"), E("s.b", "s.c")]
    fp = _run_with_timeout(lambda: slw.transitive_footprint(["s.a"], edges))
    assert _names(fp["delete_cascades"]) == ["s.b", "s.c"]


def test_table_missing_from_the_catalog_is_unknown_not_silent():
    fp = slw.transitive_footprint(["s.a", "s.ghost"], [E("s.b", "s.a")])
    assert [u["table"] for u in fp["unknown_tables"]] == ["s.ghost"]
    assert fp["counts"]["unknown_tables"] == 1
    assert fp["fk_closure_status"] == "INCOMPLETE"
    assert any("s.ghost" in r for r in fp["incomplete_reasons"])
    assert _names(fp["delete_cascades"]) == ["s.b"]   # the known part is still computed


def test_empty_edge_list_is_incomplete_never_an_empty_clean_reading():
    fp = slw.transitive_footprint(["s.a", "s.b"], [])
    assert fp["fk_closure_status"] == "INCOMPLETE"
    assert [u["table"] for u in fp["unknown_tables"]] == ["s.a", "s.b"]
    assert fp["counts"]["edges_considered"] == 0
    assert any("empty" in r.lower() for r in fp["incomplete_reasons"])
    assert fp["delete_cascades"] == [] and fp["has_blockers"] is False


def test_known_tables_distinguishes_confirmed_no_fk_from_not_in_catalog():
    edges = [E("s.b", "s.a")]
    fp = slw.transitive_footprint(["s.lonely", "s.ghost"], edges, known_tables=["s.a", "s.b", "s.lonely"])
    assert fp["no_fk_edges_tables"] == ["s.lonely"]
    assert [u["table"] for u in fp["unknown_tables"]] == ["s.ghost"]
    assert fp["universe"]["source"] == "catalog_table_list"


def test_empty_edge_list_with_known_tables_is_a_computed_zero():
    fp = slw.transitive_footprint(["s.a"], [], known_tables=["s.a"])
    assert fp["no_fk_edges_tables"] == ["s.a"] and fp["unknown_tables"] == []
    assert fp["fk_closure_status"] == "COMPLETE"   # catalog listed, the table really has no FK edges


def test_without_known_tables_a_fk_free_table_is_unknown_because_the_universe_is_edges_only():
    fp = slw.transitive_footprint(["s.lonely"], [E("s.b", "s.a")])
    assert [u["table"] for u in fp["unknown_tables"]] == ["s.lonely"]
    assert fp["universe"]["source"] == "edges_only"


def test_empty_write_set_is_rejected():
    with pytest.raises(ValueError):
        slw.transitive_footprint([], [E("s.b", "s.a")])


def test_bare_names_resolve_to_public_schema():
    fp = slw.transitive_footprint(["a"], [E("public.b", "public.a")])
    assert fp["write_tables"] == ["public.a"] and _names(fp["delete_cascades"]) == ["public.b"]


def test_dangling_after_rewrite_is_always_unknown_and_names_tables_without_inbound_fk():
    fp = slw.transitive_footprint(["s.a", "s.z"], [E("s.b", "s.a"), E("s.z", "s.b", "SET NULL", ["b_id"])])
    d = fp["dangling_after_rewrite"]
    assert d["status"] == "unknown_not_in_catalog"
    assert d["write_tables_with_no_inbound_fk"] == ["s.z"]


def test_write_set_child_of_another_write_table_is_flagged_not_hidden():
    edges = [E("s.child", "s.a", "RESTRICT", ["a_id"])]
    fp = slw.transitive_footprint(["s.a", "s.child"], edges)
    assert fp["refusing"][0]["child_in_write_set"] is True
    assert fp["refusing"][0]["child_also_deleted"] is True


# ───────────────────────── determinism ─────────────────────────

def test_output_is_byte_reproducible_across_shuffled_input():
    base = json.dumps(slw.transitive_footprint([MSR, "public.kala_convergence"], FIXTURE_2026_09_30),
                      sort_keys=True)
    rng = random.Random(1214)
    for _ in range(25):
        edges = list(FIXTURE_2026_09_30)
        rng.shuffle(edges)
        writes = [MSR, "public.kala_convergence"]
        rng.shuffle(writes)
        out = json.dumps(slw.transitive_footprint(writes, edges), sort_keys=True)
        assert out == base


def test_shortest_path_tie_break_is_independent_of_edge_order():
    # two equal-length routes a->b->d and a->c->d: the reported path must not depend on input order.
    edges = [E("s.b", "s.a"), E("s.c", "s.a"), E("s.d", "s.b", columns=["b_id"]), E("s.d", "s.c", columns=["c_id"])]
    outs = set()
    rng = random.Random(7)
    for _ in range(20):
        shuffled = list(edges)
        rng.shuffle(shuffled)
        outs.add(json.dumps(slw.transitive_footprint(["s.a"], shuffled), sort_keys=True))
    assert len(outs) == 1
    fp = json.loads(next(iter(outs)))
    assert _hop_tables(_entry(fp["delete_cascades"], "s.d")["path"]) == ["s.a", "s.b", "s.d"]


def test_delete_cascades_are_sorted_by_table_name_not_by_discovery_order():
    # a -> z (depth 1) and z -> b (depth 2): discovery order is [z, b]; the reported order must be [b, z].
    fp = slw.transitive_footprint(["s.a"], [E("s.z", "s.a"), E("s.b", "s.z")])
    assert _names(fp["delete_cascades"]) == ["s.b", "s.z"]


def test_output_is_byte_identical_across_processes_with_different_hash_seeds():
    # Set / dict iteration order of str keys differs per process (PYTHONHASHSEED). Same input -> same bytes.
    import os
    import subprocess
    script = (
        "import sys, json; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]);"
        "import suvarna_level_wave as slw; import test_e5_9_footprint as t;"
        "edges = t.FIXTURE_2026_09_30 + [t.E('s.b','s.a'), t.E('s.c','s.a'), t.E('s.d','s.b',columns=['b_id']),"
        " t.E('s.d','s.c',columns=['c_id']), t.E('s.e','s.d', 'RESTRICT', ['d_id'])];"
        "print(slw.footprint_to_json(slw.transitive_footprint([t.MSR, 'public.kala_convergence', 's.a'], edges)))")
    outs = set()
    for seed in ("0", "1", "2", "3", "4", "5", "11", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", script, str(HERE.parent), str(HERE)], capture_output=True,
                           text=True, env=env, timeout=60)
        assert r.returncode == 0, r.stderr
        outs.add(r.stdout)
    assert len(outs) == 1


def test_duplicate_edges_do_not_change_the_result():
    edges = [E("s.b", "s.a")]
    assert slw.transitive_footprint(["s.a"], edges) == slw.transitive_footprint(["s.a"], edges + edges)


def test_footprint_to_json_is_sorted_and_stable():
    fp = slw.transitive_footprint([MSR], FIXTURE_2026_09_30)
    s = slw.footprint_to_json(fp)
    assert s == json.dumps(fp, sort_keys=True)
    assert json.loads(s) == fp


def test_input_edges_are_not_mutated():
    edges = json.loads(json.dumps(FIXTURE_2026_09_30))
    snapshot = json.loads(json.dumps(edges))
    slw.transitive_footprint([MSR], edges)
    assert edges == snapshot


# ───────────────────────── impact statement section ─────────────────────────

def test_impact_section_lists_each_category_with_paths():
    fp = slw.transitive_footprint([MSR], FIXTURE_2026_09_30)
    lines = slw.impact_statement_footprint_section(fp)
    text = "\n".join(lines)
    assert all(isinstance(x, str) for x in lines)
    assert "public.phala_pramana" in text and "public.kala_convergence" in text
    assert "CASCADE" in text and "SET NULL" in text
    assert "UNKNOWN" in text            # dangling references: unknown_not_in_catalog is stated, not omitted
    assert "unknown_not_in_catalog" in text


def test_impact_section_for_unknown_tables_never_reads_as_no_footprint():
    fp = slw.transitive_footprint(["s.ghost"], [])
    text = "\n".join(slw.impact_statement_footprint_section(fp))
    assert "INCOMPLETE" in text and "s.ghost" in text
    assert "no footprint" not in text.lower() and "no cascade" not in text.lower()


def test_impact_section_computed_zero_names_the_edge_count():
    fp = slw.transitive_footprint(["s.lonely"], [E("s.b", "s.a")], known_tables=["s.a", "s.b", "s.lonely"])
    text = "\n".join(slw.impact_statement_footprint_section(fp))
    assert "1 catalog FK edge" in text and "COMPLETE" in text


def test_impact_section_flags_refusing_blockers():
    fp = slw.transitive_footprint(["s.a"], [E("s.child", "s.a", "RESTRICT", ["a_id"])])
    text = "\n".join(slw.impact_statement_footprint_section(fp))
    assert "REFUS" in text and "s.child" in text


def test_impact_section_is_deterministic():
    fp = slw.transitive_footprint([MSR], FIXTURE_2026_09_30)
    assert slw.impact_statement_footprint_section(fp) == slw.impact_statement_footprint_section(fp)


# ───────────────────────── loader (fake cursor; no database) ─────────────────────────

class FakeCursor:
    def __init__(self, rows_by_marker):
        self.rows_by_marker = rows_by_marker
        self.executed = []
        self.closed = False
        self._rows = []

    def execute(self, sql, params=None):
        self.executed.append(sql)
        for marker, rows in self.rows_by_marker.items():
            if marker in sql:
                self._rows = rows
                return
        raise AssertionError("unexpected SQL: " + sql[:80])

    def fetchall(self):
        return list(self._rows)

    def close(self):
        self.closed = True


class FakeConn:
    def __init__(self, rows_by_marker):
        self.cursors = []
        self.rows_by_marker = rows_by_marker
        self.committed = self.closed = self.rolled_back = False

    def cursor(self):
        c = FakeCursor(self.rows_by_marker)
        self.cursors.append(c)
        return c

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def rollback(self):
        self.rolled_back = True


_EDGE_ROWS = [
    # conname, child, parent, confdeltype, confupdtype, child_columns, child_columns_not_null
    ("kala_activation_signal_id_fkey", "public.kala_activation", "public.bodha_msr_signals", "c", "a",
     ["signal_id"], ["signal_id"]),
    ("kala_bhavishya_convergence_id_fkey", "public.kala_bhavishya", "public.kala_convergence", "n", "a",
     ["convergence_id"], []),
    ("x_fkey", "public.x", "public.y", "r", "a", ["y_id"], []),
    ("z_fkey", "public.z", "public.y", "a", "c", ["y_id"], []),
    ("d_fkey", "public.d", "public.y", "d", "n", ["y_id"], []),
]


def test_loader_maps_catalog_rows_to_edges():
    conn = FakeConn({"pg_constraint": _EDGE_ROWS})
    edges = slw.fk_edges_from_catalog(conn)
    assert edges[0] == {
        "constraint": "kala_activation_signal_id_fkey", "child_table": "public.kala_activation",
        "parent_table": "public.bodha_msr_signals", "on_delete": "CASCADE", "on_update": "NO ACTION",
        "columns": ["signal_id"], "child_columns_not_null": ["signal_id"]}
    assert [e["on_delete"] for e in edges] == ["CASCADE", "SET NULL", "RESTRICT", "NO ACTION", "SET DEFAULT"]
    assert [e["on_update"] for e in edges] == ["NO ACTION"] * 3 + ["CASCADE", "SET NULL"]
    # the edge list feeds the footprint directly
    fp = slw.transitive_footprint(["public.bodha_msr_signals"], edges)
    assert _names(fp["delete_cascades"]) == ["public.kala_activation"]


def test_loader_only_runs_select_and_never_commits_or_closes_the_connection():
    conn = FakeConn({"pg_constraint": _EDGE_ROWS})
    slw.fk_edges_from_catalog(conn)
    assert len(conn.cursors) == 1 and len(conn.cursors[0].executed) == 1
    sql = conn.cursors[0].executed[0]
    assert sql.lstrip().upper().startswith("SELECT") and "contype = 'f'" in sql
    assert conn.committed is False and conn.closed is False
    assert conn.cursors[0].closed is True            # its own cursor is released


def test_loader_accepts_dict_rows():
    rows = [dict(zip(slw.FK_EDGE_COLUMNS, r)) for r in _EDGE_ROWS]
    edges = slw.fk_edges_from_catalog(FakeConn({"pg_constraint": rows}))
    assert len(edges) == 5 and edges[1]["on_delete"] == "SET NULL"


def test_loader_unknown_delete_code_fails_loudly():
    bad = [("c", "public.a", "public.b", "?", "a", ["x"], [])]
    with pytest.raises(ValueError):
        slw.fk_edges_from_catalog(FakeConn({"pg_constraint": bad}))


def test_loader_zero_rows_returns_empty_list_for_the_footprint_to_flag():
    assert slw.fk_edges_from_catalog(FakeConn({"pg_constraint": []})) == []


def test_tables_loader_is_select_only_and_returns_sorted_unique_names():
    conn = FakeConn({"pg_class": [("public.b",), ("public.a",), ("public.b",)]})
    assert slw.tables_from_catalog(conn) == ["public.a", "public.b"]
    assert conn.cursors[0].executed[0].lstrip().upper().startswith("SELECT")
    assert conn.committed is False and conn.closed is False


@pytest.mark.parametrize("sql", [
    "DELETE FROM kala_convergence",
    "UPDATE kala_convergence SET signal_id = NULL",
    "INSERT INTO t VALUES (1)",
    "DROP TABLE t",
    "ALTER TABLE t DROP CONSTRAINT c",
    "TRUNCATE t",
    "SELECT 1; DROP TABLE t",
    "SELECT 1; SELECT 2",
    "WITH d AS (DELETE FROM t RETURNING *) SELECT * FROM d",
    "SELECT * INTO new_t FROM old_t",
    "SELECT pg_terminate_backend(1)",
    "SELECT 1 /* x */; delete from t",
    "  select 1 FOR UPDATE",
    "",
    "-- just a comment",
])
def test_assert_select_only_rejects_non_select(sql):
    with pytest.raises(ValueError):
        slw.assert_select_only(sql)


@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "  select a from pg_class;",
    "-- lead\nSELECT 1",
    "SELECT 'drop table x' AS note",   # a string literal naming a keyword is data, not a statement
])
def test_assert_select_only_accepts_plain_selects(sql):
    slw.assert_select_only(sql)


def test_loader_refuses_to_execute_a_non_select_statement(monkeypatch):
    monkeypatch.setattr(slw, "FK_EDGES_SQL", "DELETE FROM pg_constraint")
    conn = FakeConn({"pg_constraint": []})
    with pytest.raises(ValueError):
        slw.fk_edges_from_catalog(conn)
    assert conn.cursors == [] or conn.cursors[0].executed == []


def test_shipped_catalog_sql_passes_its_own_select_only_check():
    slw.assert_select_only(slw.FK_EDGES_SQL)
    slw.assert_select_only(slw.TABLES_SQL)
