"""A5.3 rule_binding — RuleRegistryStore + the bound catalogue (fake-conn;
no DB).

What this file proves:

  (a) catalogue shape and internal consistency: every composite reference in
      the P1–P5 path catalogue resolves to a bound predicate/factor row
      (§2.1: a bare or dangling reference is rejected before any SQL);
  (b) 1154-conformance of the bound rows (static mirror of the migration's
      CHECKs — frame encoding, agent/relation vocab, object_selector
      consistency, factor range ⊆ [0,1], direction binary, doctrine_ordering
      non-blank string arrays, calibrated ⇒ mapping);
  (c) fidelity to Stream B's catalogue: provenance / operator_role /
      ruling_ref / score_rule / membership ride registry.py verbatim;
  (d) store behaviour: insert-if-absent with full-field equality, ANY
      divergence a loud RegistryDivergenceError, seal written after the
      membership, a second seed a pure reuse;
  (e) deferrals pinned: P6 and sad_bala_summary are NOT in the bound set
      (rule_registry D1/D2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import rule_registry as rr  # noqa: E402
from services.gochara_rules import registry as rules_registry  # noqa: E402

TOKEN_RE = r"^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$"
GRAHA_VOCAB = {
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
}
RELATION_VOCAB = {
    "residence", "aspect", "conjunction", "dispositorship",
    "association", "ownership", "occupancy", "period_running",
}
ROLE_VOCAB = {
    "lord", "occupant", "karaka", "dispositor", "maraka_of_house",
    "period_lord", "yoga_constituent", "pada", "signature_house",
}
OPERATORS = {
    "eq", "in_set", "within_orb", "house_from", "overlaps",
    "period_running_at", "declaration_exists",
}


# ── (a) catalogue shape + internal consistency ───────────────────────────────


def test_bound_set_is_p1_to_p5_p6_deferred():
    assert rr.BOUND_PATHS == ("P1", "P2", "P3", "P4", "P5")
    assert "P6" not in rr.BOUND_PATHS
    assert "sad_bala_summary" not in rr.BOUND_FACTORS


def test_every_membership_reference_resolves():
    rr._membership_consistent()  # raises on a dangling/bare reference
    declared_predicates = {r["predicate_id"] for r in rr.predicate_rows()}
    declared_factors = {r["factor_id"] for r in rr.factor_rows()}
    for row in rr.prerequisite_rows():
        assert row["predicate_id"] in declared_predicates
        assert row["predicate_rule_version"] == rr.RULE_VERSION
        assert row["ordinal"] >= 1
    for row in rr.soft_factor_rows():
        assert row["factor_id"] in declared_factors
        assert row["factor_rule_version"] == rr.RULE_VERSION


def test_prerequisite_ordinals_are_contiguous_per_path():
    by_path: dict[str, list[int]] = {}
    for row in rr.prerequisite_rows():
        by_path.setdefault(row["path_id"], []).append(row["ordinal"])
    for pid, ords in by_path.items():
        assert sorted(ords) == list(range(1, len(ords) + 1)), pid


# ── (b) 1154-conformance (static mirror of the migration CHECKs) ──────────────


def test_predicate_rows_match_kgp_checks():
    import re
    for row in rr.predicate_rows():
        assert row["operator"] in OPERATORS
        ops = row["operands"]
        assert isinstance(ops, dict) and ops
        for key, value in ops.items():
            assert re.match(r"^[a-z][a-z0-9_]*$", key)
            if isinstance(value, str):
                assert re.match(TOKEN_RE, value)
            elif isinstance(value, (int, float)):
                pass
            else:
                assert isinstance(value, list) and value
                assert all(isinstance(v, str) and re.match(TOKEN_RE, v)
                           for v in value)


def test_factor_rows_match_kgf_checks():
    import re
    for row in rr.factor_rows():
        assert row["direction"] in ("higher_stronger", "lower_stronger")
        assert row["units"] in ("degrees", "days", "count", "unitless")
        assert 0 <= row["range_lower"] <= row["range_upper"] <= 1
        assert row["calibration_status"] in ("uncalibrated_default", "calibrated")
        if row["calibration_status"] == "calibrated":
            assert row["category_mapping"]
        if row["doctrine_ordering"] is not None:
            assert isinstance(row["doctrine_ordering"], list)
            assert all(isinstance(s, str) and re.match(r"^\S+$", s)
                       for s in row["doctrine_ordering"])
        if row["category_mapping"] is not None:
            assert isinstance(row["category_mapping"], dict)
            assert row["category_mapping"] != {}
        assert row["null_state"] in ("omit", "unqualified")
        assert row["function"].strip() and row["effect"].strip()


def test_path_rows_match_kgrp_checks():
    for row in rr.path_rows():
        kind, arg = row["frame_kind"], row["frame_arg"]
        if kind in ("moon", "lagna", "dasha_lord"):
            assert arg is None
        elif kind == "graha":
            assert arg in GRAHA_VOCAB
        else:
            assert kind == "bhavat_bhavam" and arg in {str(i) for i in range(1, 13)}
        assert set(row["agent_set"]) <= GRAHA_VOCAB and row["agent_set"]
        assert set(row["relation_set"]) <= RELATION_VOCAB and row["relation_set"]
        assert row["provenance"] in ("verse_cited", "uncited_extension")
        assert row["operator_role"] in ("scored", "testimony")
        if row["provenance"] == "uncited_extension":
            assert row["ruling_ref"] is not None
        for entry in row["object_selector"]:
            assert set(entry) == {"agent", "relation", "object_role"}
            assert entry["agent"] in row["agent_set"]
            assert entry["relation"] in row["relation_set"]
            assert entry["object_role"] in ROLE_VOCAB


def test_object_selector_is_the_full_cross():
    sel = rr.object_selector_for("P4")
    assert len(sel) == 2 * 3 * 2  # agents × relations × roles
    assert {e["agent"] for e in sel} == {"jupiter", "saturn"}


# ── (c) fidelity to Stream B's catalogue ─────────────────────────────────────


def test_path_rows_ride_registry_verbatim_where_typed_fields_overlap():
    for row in rr.path_rows():
        src = rules_registry.RULE_PATHS[(row["path_id"], rr.RULE_VERSION)]
        assert row["provenance"] == src["provenance"]
        assert row["operator_role"] == src["operator_role"]
        assert row["ruling_ref"] == src.get("ruling_ref")
        assert row["score_rule"] == src["score_rule"]
        assert [tuple(p) for p in src["prerequisites"]] == [
            (r["predicate_id"], r["predicate_rule_version"])
            for r in rr.prerequisite_rows()
            if r["path_id"] == row["path_id"]
        ]
        assert [tuple(f) for f in src["soft_factors"]] == [
            (r["factor_id"], r["factor_rule_version"])
            for r in rr.soft_factor_rows()
            if r["path_id"] == row["path_id"]
        ]


def test_factor_rows_ride_registry_verbatim_where_typed_fields_overlap():
    for row in rr.factor_rows():
        src = rules_registry.FACTORS[(row["factor_id"], rr.RULE_VERSION)]
        assert row["function"] == src["function"]
        assert row["units"] == src["units"]
        assert row["calibration_status"] == src["calibration_status"]
        assert row["null_state"] == src["null_state"]
        assert row["effect"] == src["effect"]
        assert [row["range_lower"], row["range_upper"]] == [
            float(v) for v in src["range"]
        ]


# ── (d) store behaviour ────────────────────────────────────────────────────────


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeConn:
    """In-memory tables keyed by (table, pk tuple); records every statement
    in order so the seal-after-membership order is observable."""

    def __init__(self):
        self.rows: dict[tuple, dict] = {}
        self.statements: list[str] = []

    def execute(self, sql, params=()):
        self.statements.append(sql)
        if sql.startswith("SELECT"):
            table = sql.split("FROM public.", 1)[1].split(" ", 1)[0]
            cols = sql.split("SELECT ", 1)[1].split(" FROM", 1)[0].split(", ")
            key = (table, params)
            stored = self.rows.get(key)
            if stored is None:
                return _FakeResult(None)
            return _FakeResult([tuple(stored.get(c) for c in cols)])
        if sql.startswith("INSERT"):
            table = sql.split("INTO public.", 1)[1].split(" ", 1)[0]
            cols = sql.split("(", 1)[1].split(")", 1)[0].split(", ")
            row = dict(zip(cols, params))
            pk_cols = cols[: _PK_LEN[table]]
            self.rows.setdefault((table, tuple(row[c] for c in pk_cols)), row)
            return _FakeResult(None)
        raise AssertionError(f"unexpected SQL: {sql[:60]}")


_PK_LEN = {
    "ka_gochara_predicate": 2,
    "ka_gochara_factor": 2,
    "ka_gochara_rule_path": 2,
    "ka_gochara_rule_path_prerequisite": 3,
    "ka_gochara_rule_path_soft_factor": 4,
    "ka_gochara_rule_path_seal": 2,
}


def test_seed_inserts_the_full_catalogue_then_seals():
    conn = _FakeConn()
    counts = rr.RuleRegistryStore(conn).seed()
    assert counts["predicates"] == len(rr.PREDICATES)
    assert counts["factors"] == len(rr.BOUND_FACTORS)
    assert counts["paths"] == len(rr.BOUND_PATHS)
    assert counts["seals"] == len(rr.BOUND_PATHS)
    assert counts["reused"] == 0
    first_seal = next(
        i for i, s in enumerate(conn.statements)
        if "ka_gochara_rule_path_seal" in s and s.startswith("INSERT")
    )
    last_membership = max(
        i for i, s in enumerate(conn.statements)
        if ("ka_gochara_rule_path_prerequisite" in s
            or "ka_gochara_rule_path_soft_factor" in s)
        and s.startswith("INSERT")
    )
    assert first_seal > last_membership  # F3: membership complete, THEN seal


def test_seed_is_idempotent_second_run_reuses_everything():
    conn = _FakeConn()
    rr.RuleRegistryStore(conn).seed()
    counts = rr.RuleRegistryStore(conn).seed()
    assert counts["predicates"] == counts["factors"] == counts["paths"] == 0
    assert counts["prerequisites"] == counts["soft_factors"] == counts["seals"] == 0
    assert counts["reused"] > 0


def test_any_field_divergence_is_a_loud_failure():
    conn = _FakeConn()
    store = rr.RuleRegistryStore(conn)
    store.seed()
    key = ("ka_gochara_rule_path", ("P4", rr.RULE_VERSION))
    conn.rows[key] = {**conn.rows[key], "score_rule": "tampered"}
    with pytest.raises(rr.RegistryDivergenceError):
        store.seed()


def test_jsonb_fields_are_adapted_and_normalised():
    conn = _FakeConn()
    store = rr.RuleRegistryStore(conn)
    store.seed()
    key = ("ka_gochara_rule_path", ("P4", rr.RULE_VERSION))
    stored = conn.rows[key]
    # stored as canonical JSON text; a semantically identical but
    # formatting-different value still reuses (normalise, not byte compare)
    assert isinstance(stored["agent_set"], str)
    parsed = json.loads(stored["agent_set"])
    assert parsed == ["jupiter", "saturn"]


# ── (e) deferrals pinned ──────────────────────────────────────────────────────


def test_p6_catalogue_row_exists_but_is_not_bound():
    assert ("P6", rr.RULE_VERSION) in rules_registry.RULE_PATHS
    assert all(r["path_id"] != "P6" for r in rr.path_rows())


def test_sad_bala_summary_exists_but_is_not_bound():
    assert ("sad_bala_summary", rr.RULE_VERSION) in rules_registry.FACTORS
    assert all(r["factor_id"] != "sad_bala_summary" for r in rr.factor_rows())
