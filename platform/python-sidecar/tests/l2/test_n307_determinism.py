"""test_n307_determinism.py: SS N-307 (lane A) the writer-level determinism fixes found by reading the code against main 95a2a6825.

Three defects, each proved RED before the fix and GREEN after:

1. bo_cgm_motifs `_detect_stellia`: `"edge_ids": list(set(conj_edges))` followed the per-process string hash seed, so the stellium motif's edge order (copied unchanged into bo_yantra_mechanism's
   digested `member_edge_ids_array`) differed between runs. Fixed with `sorted(set(...))`. The test runs the real function in subprocesses under different PYTHONHASHSEED values.
2. bo_grounding `_fetch_sutravali_rules`: no ORDER BY, and the matcher takes the FIRST matching rule, so `matched_rule_id` / `derivation_chain` / the evidence followed physical row order. The fetch now
   carries a total ORDER BY. The test drives the real `run()` against a fake connection that HONOURS the ORDER BY it is sent and otherwise returns rows in a seed-dependent shuffled order.
3. bo_grounding yoga `target_id`: was `str(ga_yoga_firings.id)`, a SERIAL ga_yoga renumbers on every rebuild (delete then insert), so the digested KEY moved on identical content. It is now the firing's
   natural key `yoga_canonical_id` (UNIQUE per chart and ayanamsha, migration 240). The test rebuilds the same firings under different serial ids and requires identical rows.

No database. The migration and the integrity detector are tested on a disposable PostgreSQL in platform/scripts/governance/__tests__/test_n307_grounding_integrity_migration.py.
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import bo_grounding as bg

SIDECAR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHART = "482012f1-710e-4a25-994a-93821f5871aa"

# ───────────────────────── 1. the stellium edge order must not depend on the hash seed ─────────────────────────

STELLIUM_SNIPPET = textwrap.dedent("""
    import json
    from pipeline.orchestrator.writers import bo_cgm_motifs as m

    nodes = [{"node_id": f"node-{i}", "node_subject": f"G{i}", "position_in_chart_jsonb": {"house": 7}} for i in range(5)]
    edges = {}
    for i in range(5):
        edges[f"node-{i}"] = [{"edge_id": f"edge-{i}-{j}-{k}", "edge_type": "conjunction", "to_node_id": f"node-{j}"}
                              for j in range(5) if j != i for k in range(2)]
    got = m._detect_stellia(nodes, edges)
    print(json.dumps([x["edge_ids"] for x in got]))
""")


def _stellium_edge_ids(seed: int) -> list:
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    out = subprocess.run([sys.executable, "-c", STELLIUM_SNIPPET], cwd=SIDECAR, env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-600:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_the_stellium_edge_order_is_the_same_under_every_hash_seed():
    runs = [_stellium_edge_ids(seed) for seed in (0, 1, 2, 3, 4, 5, 6, 7)]
    assert all(r == runs[0] for r in runs), "the stellium motif's edge_ids differ between processes: the order follows the string hash seed"
    ids = runs[0][0]
    assert len(ids) == 40 and ids == sorted(set(ids))                       # 5 nodes x 4 neighbours x 2 edges, de-duplicated and in a total order


# ───────────────────────── 2. + 3. bo_grounding ─────────────────────────

RULES = [
    # two rules whose antecedent is EXACTLY the firing's constituent set: the FIRST one wins (sruti), so the order of the corpus decides matched_rule_id
    {"rule_id": "r-02", "text_id": "bphs", "verse_ref": "1.2", "antecedent_jsonb": [{"relation": "occupies", "planet": "Jupiter", "house": 1}], "predicate_jsonb": {}, "yoga_canonical_id": "x"},
    {"rule_id": "r-01", "text_id": "bphs", "verse_ref": "1.1", "antecedent_jsonb": [{"relation": "occupies", "planet": "Jupiter", "house": 1}], "predicate_jsonb": {}, "yoga_canonical_id": "x"},
    {"rule_id": "r-03", "text_id": "bphs", "verse_ref": "3.1", "antecedent_jsonb": [{"relation": "occupies", "planet": "Moon", "house": 4}], "predicate_jsonb": {}, "yoga_canonical_id": "y"},
]


def _firings(serial_base: int):
    return [
        {"id": serial_base + 1, "yoga_canonical_id": "gajakesari", "constituent_planets": ["Jupiter"], "constituent_houses": [1]},
        {"id": serial_base + 2, "yoga_canonical_id": "chandra_mangala", "constituent_planets": ["Moon"], "constituent_houses": [4]},
    ]


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    """Honours the ORDER BY a statement carries (sorting by exactly its keys) and otherwise returns the rows in a SEED-DEPENDENT shuffled order, like a heap whose physical order changed."""

    def __init__(self, firings, rules, seed):
        self.firings, self.rules, self.seed, self.sql = firings, rules, seed, []

    def execute(self, sql, params=None):
        self.sql.append(sql)
        compact = " ".join(sql.split())
        if "FROM sutravali_rules" in compact:
            rows = [dict(r) for r in self.rules]
            keys = re.search(r"ORDER BY ([a-z_, ]+)$", compact)
            if keys:
                cols = [c.strip() for c in keys.group(1).split(",")]
                rows.sort(key=lambda r: tuple(str(r[c]) for c in cols))
            else:
                random.Random(self.seed).shuffle(rows)
            return FakeCursor(rows)
        if "FROM ga_yoga_firings" in compact:
            rows = [dict(r) for r in self.firings]
            keys = re.search(r"ORDER BY ([a-z_, ]+)$", compact)
            if keys:
                cols = [c.strip() for c in keys.group(1).split(",")]
                rows.sort(key=lambda r: tuple(str(r[c]) for c in cols))
            else:
                random.Random(self.seed + 1).shuffle(rows)
            return FakeCursor(rows)
        if "FROM bodha_msr_signals" in compact:
            return FakeCursor([])
        return FakeCursor([])                                                                                     # the delete helper and inserts


class Capture:
    def __init__(self):
        self.rows = []


def _run(monkeypatch, firings, rules, seed):
    conn = FakeConn(firings, rules, seed)
    inserted = []
    monkeypatch.setattr("bodha_writers._idempotency.replace_prior_grounding_matches", lambda *a, **k: 0)
    real_execute = conn.execute

    def execute(sql, params=None):
        if sql is bg._INSERT_SQL:
            inserted.append(dict(params))
            return FakeCursor([])
        return real_execute(sql, params)
    conn.execute = execute
    ctx = SimpleNamespace(config={"chart_id": CHART}, build_id="b-1", db_conn=conn, dry_run=False)
    bg.BoGroundingWriter().run(ctx)
    return inserted


def _digested(rows):
    """What the output-digest spec (migration 946) covers: the key and value columns, NOT match_id / build_id / computed_at."""
    cols = ("chart_id", "ayanamsha_id", "target_kind", "target_id", "grounding_tier", "citation_granularity", "grounding_evidence_jsonb", "derivation_chain", "matched_rule_id", "engine_version")
    return sorted(json.dumps({c: r[c] for c in cols}, sort_keys=True, default=str) for r in rows)


def test_the_digested_columns_do_not_depend_on_the_corpus_row_order(monkeypatch):
    base = _digested(_run(monkeypatch, _firings(0), RULES, seed=0))
    assert base, "the fake run produced no rows"
    for seed in range(1, 12):
        assert _digested(_run(monkeypatch, _firings(0), RULES, seed=seed)) == base, f"seed {seed}: the corpus order changed the digested columns"
    first = json.loads(next(r for r in base if '"gajakesari"' in r))
    assert first["matched_rule_id"] == "r-01" and first["grounding_tier"] == "sruti"                 # two rules cover the firing exactly: the lowest rule_id wins, always


def test_the_sutravali_fetch_carries_a_total_order(monkeypatch):
    conn = FakeConn(_firings(0), RULES, 0)
    bg._fetch_sutravali_rules(conn)
    sql = " ".join(conn.sql[0].split())
    assert sql.endswith("ORDER BY rule_id, text_id, verse_ref") or "ORDER BY rule_id, text_id, verse_ref" in sql


def test_a_yoga_rows_target_id_is_the_natural_key_not_the_serial(monkeypatch):
    rows = _run(monkeypatch, _firings(0), RULES, seed=0)
    ids = sorted({r["target_id"] for r in rows if r["target_kind"] == "yoga_dosha_firing"})                 # five ayanamshas each get the same firings in this fake
    assert ids == ["chandra_mangala", "gajakesari"]
    assert not any(re.fullmatch(r"[0-9]+", r["target_id"]) for r in rows)


def test_renumbering_the_serial_ids_changes_nothing_that_is_digested_or_stored_as_identity(monkeypatch):
    before = _run(monkeypatch, _firings(0), RULES, seed=3)
    after = _run(monkeypatch, _firings(5000), RULES, seed=9)                  # ga_yoga rebuilt: same firings, new serial ids, different physical order
    assert _digested(before) == _digested(after)
    assert sorted(r["match_id"] for r in before) == sorted(r["match_id"] for r in after)         # the stable match uuid is derived from the same identity


def test_the_fetch_of_fired_yogas_is_ordered_too(monkeypatch):
    conn = FakeConn(_firings(0), RULES, 0)
    bg._fetch_fired_yogas(conn, CHART, "lahiri_chitrapaksha")
    assert "ORDER BY yoga_canonical_id" in " ".join(conn.sql[0].split())


def test_the_matcher_accepts_a_string_identity_and_reports_it_verbatim():
    from bodha_writers.grounding_matcher import classify_yoga_dosha_firing
    m = classify_yoga_dosha_firing(firing_id="gajakesari", constituent_planets=["Jupiter"], constituent_houses=[1], candidate_rules=RULES)
    assert m.target_id == "gajakesari" and m.target_kind == "yoga_dosha_firing"
    legacy = classify_yoga_dosha_firing(firing_id=12, constituent_planets=["Jupiter"], constituent_houses=[1], candidate_rules=RULES)
    assert legacy.target_id == "12"                                                                         # an integer is still stringified (callers outside bo_grounding)


# ───────────────────────── 4. bo_anveshana (Kāla #3368 follow-up): the same list(set()) defect on a digested array ─────────────────────────

ANVESHANA_SNIPPET = textwrap.dedent("""
    import json
    from pipeline.orchestrator.writers import bo_anveshana as m

    row = m._make_discovery(
        "482012f1-710e-4a25-994a-93821f5871aa", "lahiri_chitrapaksha", "b-1", "2026-10-10T00:00:00+00:00",
        "cluster", None, 0.5, 0.5, ["sig-1", "sig-2"], ["step"], "why", ["career"],
        "surface", "depth", "delta", "hypothesis", False, None,
        ["zeta_method", "alpha_method", "mid_method", "beta_method", "omega_method", "alpha_method"],
        "basis", 0.5, 0.5)
    print(json.dumps(row["corroborating_methods_array"]))
""")


def _anveshana_methods(seed: int) -> list:
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    out = subprocess.run([sys.executable, "-c", ANVESHANA_SNIPPET], cwd=SIDECAR, env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-600:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_the_discovery_corroborating_methods_are_the_same_under_every_hash_seed():
    runs = [_anveshana_methods(seed) for seed in range(8)]
    assert all(r == runs[0] for r in runs), "corroborating_methods_array follows the string hash seed"
    assert runs[0] == ["alpha_method", "beta_method", "mid_method", "omega_method", "zeta_method"]       # de-duplicated and in a total order
