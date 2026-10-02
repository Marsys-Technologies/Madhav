"""A5.3 — version-aware rule binding (Codex round 6, R5).

The binder selects EXPLICIT composite references; each prerequisite and soft factor keeps its OWN
version; an AM-13-shaped `applicability` declaration is encoded into 1154's FLAT `operand_selector`
(no nesting, no JSON null, a closed key schema), read back, decoded and compared; and what the sweep
consumes is the persisted declaration read back — never a global version constant.

The 1.1.0 rows themselves are Stream B's (#2897, not on main): the tests build a synthetic successor
version from the REAL 1.0.0 rows plus the applicability shape that PR declares, and run the real binder
and the real 1154 schema over it. A skip-guarded test binds the real rows the moment they exist.
"""
from __future__ import annotations

import copy
import re
from datetime import datetime, timezone

import pytest

from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import window_sweep as ws
from services.gochara_rules import registry as rules_registry

from .test_a53_window_sweep_pg import pg  # noqa: F401  (fresh DB per test, 1081 + 1152–1157 applied)

APPLICABILITY = {
    "span": {"object_kinds": ["sign_span", "house_span", "star"], "function": "step",
             "inside": 1.0, "outside": 0.0},
    "angular": {"object_kinds": ["degree_point", "derived_point", "saham", "house_lord"],
                "function": "linear", "formula": "1 - |Δλ|/orb", "orb_deg": None,
                "orb_status": "ND-ORB open: not ratified (draft AM-13)"},
}
TOKEN = re.compile(r"^[a-z][a-z0-9_]*([.:/][a-z0-9_]+)*$")
KEY = re.compile(r"^[a-z][a-z0-9_]*$")


def _mirror_named_operands_ok(sel: dict) -> bool:
    """A static mirror of ka_gochara_named_operands_ok (1154:221-240): the REAL function runs in the PG
    tests below; this keeps the unit tier honest about the same rule."""
    if not isinstance(sel, dict) or not sel:
        return False
    for k, v in sel.items():
        if not KEY.match(k):
            return False
        if isinstance(v, bool):
            return False
        if isinstance(v, str):
            ok = bool(TOKEN.match(v))
        elif isinstance(v, (int, float)):
            ok = True
        elif isinstance(v, list):
            ok = len(v) >= 1 and all(isinstance(x, str) and TOKEN.match(x) for x in v)
        else:
            ok = False
        if not ok:
            return False
    return True


# ── the flat applicability encoding ──────────────────────────────────────────────────────────────────

def test_the_flat_encoding_is_admissible_lossless_and_omits_an_unavailable_orb():
    flat = rr.encode_applicability(APPLICABILITY)
    assert _mirror_named_operands_ok({"operand": "geometry:delta_lambda_to_exact", **flat})
    assert "angular_orb_deg" not in flat and flat["angular_orb_state"] == "unratified"   # omitted, never null
    assert None not in flat.values()
    assert rr.decode_applicability(flat) == rr.canonical_applicability(APPLICABILITY)
    assert rr.decode_applicability(flat)["angular"]["orb_deg"] is None
    assert rr.decode_applicability(flat)["span"] == APPLICABILITY["span"]


def test_a_ratified_orb_is_carried_as_a_number_with_an_explicit_state():
    app = copy.deepcopy(APPLICABILITY)
    app["angular"]["orb_deg"] = 5.0
    app["angular"]["orb_decision_ref"] = "ruling:nd_orb_test"
    flat = rr.encode_applicability(app)
    assert flat["angular_orb_state"] == "ratified" and flat["angular_orb_deg"] == 5.0
    assert flat["angular_orb_decision_ref"] == "ruling:nd_orb_test"
    assert rr.decode_applicability(flat)["angular"]["orb_deg"] == 5.0
    assert rr.decode_applicability(flat)["angular"]["orb_decision_ref"] == "ruling:nd_orb_test"
    assert _mirror_named_operands_ok(flat)


def test_a_ratified_orb_without_its_decision_ref_or_with_a_non_token_ref_is_refused():
    base = copy.deepcopy(APPLICABILITY)
    base["angular"]["orb_deg"] = 5.0
    with pytest.raises(rr.RegistryDivergenceError, match="orb_decision_ref"):
        rr.encode_applicability(base)                                   # a bare number never gets in
    for bad in ("ruling:ND-ORB", "ND ORB", "Ruling:x"):
        with pytest.raises(rr.RegistryDivergenceError, match="selector token"):
            rr.encode_applicability(dict(base, angular=dict(base["angular"], orb_decision_ref=bad)))
    unratified = copy.deepcopy(APPLICABILITY)
    unratified["angular"]["orb_decision_ref"] = "ruling:nd_orb_test"
    with pytest.raises(rr.RegistryDivergenceError, match="incoherent"):
        rr.encode_applicability(unratified)                             # a ref with no orb


def test_relations_applicability_encodes_as_a_token_array():
    flat = rr.encode_applicability({"relations": ["aspect"]})
    assert flat == {"relations": ["aspect"]} and rr.decode_applicability(flat) == {"relations": ["aspect"]}


def test_an_unknown_key_or_formula_is_refused_never_guessed():
    for bad in ({"span": {"object_kinds": ["sign_span"], "function": "step", "inside": 1, "outside": 0,
                          "extra": 1}},
                {"mystery": 1},
                {"angular": {"object_kinds": ["saham"], "function": "linear", "formula": "sin(x)",
                             "orb_deg": None}}):
        with pytest.raises(rr.RegistryDivergenceError):
            rr.encode_applicability(bad)


def test_a_state_token_that_is_neither_ratified_nor_unratified_is_refused_on_decode():
    with pytest.raises(rr.RegistryDivergenceError):
        rr.decode_applicability({"angular_kinds": ["saham"], "angular_function": "linear",
                                 "angular_orb_state": "maybe"})


# ── explicit composite references, each member at its OWN version ────────────────────────────────────

def test_no_row_is_selected_by_the_global_version_constant(monkeypatch):
    before = (rr.predicate_rows(), rr.factor_rows(), rr.path_rows(), rr.prerequisite_rows(),
              rr.soft_factor_rows())
    monkeypatch.setattr(rr, "RULE_VERSION", "9.9.9")          # a global bump must change NOTHING
    after = (rr.predicate_rows(), rr.factor_rows(), rr.path_rows(), rr.prerequisite_rows(),
             rr.soft_factor_rows())
    assert before == after


def test_the_bound_references_are_explicit_composites():
    assert rr.BOUND_PATH_REFS == tuple((p, "1.0.0") for p in ("P1", "P2", "P3", "P4", "P5"))
    assert all(isinstance(r, tuple) and len(r) == 2 for r in
               rr.BOUND_PATH_REFS + rr.BOUND_FACTOR_REFS + rr.BOUND_PREDICATE_REFS)


@pytest.fixture()
def successor(monkeypatch):
    """A synthetic AM-13-shaped successor: activity_kernel@1.1.0 (REAL 1.0.0 row + applicability) and
    P3@1.2.0 — a path version DIFFERENT from its factors' (1.1.0) and its prerequisites' (1.0.0), so a
    binder that took the path's version for its members cannot pass."""
    factors = dict(rules_registry.FACTORS)
    paths = dict(rules_registry.RULE_PATHS)
    kernel = dict(factors[("activity_kernel", "1.0.0")], rule_version="1.1.0",
                  applicability=copy.deepcopy(APPLICABILITY))
    drishti = dict(factors[("graduated_drishti", "1.0.0")], rule_version="1.1.0",
                   applicability={"relations": ["aspect"]})
    factors[("activity_kernel", "1.1.0")] = kernel
    factors[("graduated_drishti", "1.1.0")] = drishti
    p3 = dict(paths[("P3", "1.0.0")], rule_version="1.2.0",
              soft_factors=[("activity_kernel", "1.1.0"), ("graduated_drishti", "1.1.0")])
    paths[("P3", "1.2.0")] = p3
    monkeypatch.setattr(rules_registry, "FACTORS", factors)
    monkeypatch.setattr(rules_registry, "RULE_PATHS", paths)
    monkeypatch.setattr(rr, "BOUND_FACTOR_REFS", rr.BOUND_FACTOR_REFS + (("activity_kernel", "1.1.0"),
                                                                       ("graduated_drishti", "1.1.0")))
    monkeypatch.setattr(rr, "BOUND_PATH_REFS", rr.BOUND_PATH_REFS + (("P3", "1.2.0"),))
    return p3


def test_a_successor_binds_beside_the_old_version_each_member_at_its_own_version(successor):
    rr._membership_consistent()
    rows = {(r["path_id"], r["rule_version"]) for r in rr.path_rows()}
    assert {("P3", "1.0.0"), ("P3", "1.2.0")} <= rows
    soft = {(r["path_id"], r["rule_version"], r["factor_id"], r["factor_rule_version"])
            for r in rr.soft_factor_rows()}
    assert ("P3", "1.0.0", "activity_kernel", "1.0.0") in soft          # the old version is untouched
    assert ("P3", "1.2.0", "activity_kernel", "1.1.0") in soft          # path 1.2.0, member 1.1.0
    pre = {(r["path_id"], r["rule_version"], r["predicate_id"], r["predicate_rule_version"])
           for r in rr.prerequisite_rows()}
    assert ("P3", "1.2.0", "p3_contact_house_or_lord", "1.0.0") in pre   # the prerequisite keeps ITS version
    sel = {(r["factor_id"], r["rule_version"]): r["operand_selector"] for r in rr.factor_rows()}
    assert "span_kinds" in sel[("activity_kernel", "1.1.0")] and "span_kinds" not in sel[("activity_kernel", "1.0.0")]


def test_a_path_reference_to_an_unbound_member_version_is_refused_before_any_sql(successor, monkeypatch):
    monkeypatch.setattr(rr, "BOUND_FACTOR_REFS", tuple(r for r in rr.BOUND_FACTOR_REFS
                                                       if r != ("activity_kernel", "1.1.0")))
    with pytest.raises(ValueError, match="soft factor"):
        rr._membership_consistent()


def test_a_prerequisite_at_an_unbound_version_is_refused_before_any_sql(monkeypatch):
    paths = dict(rules_registry.RULE_PATHS)
    paths[("P3", "1.0.0")] = dict(paths[("P3", "1.0.0")],
                                  prerequisites=[("p3_contact_house_or_lord", "2.0.0")])
    monkeypatch.setattr(rules_registry, "RULE_PATHS", paths)
    with pytest.raises(ValueError, match="prerequisite"):
        rr._membership_consistent()


def test_a_bound_path_reference_that_is_not_in_the_catalogue_is_refused(monkeypatch):
    monkeypatch.setattr(rr, "BOUND_PATH_REFS", rr.BOUND_PATH_REFS + (("P3", "7.7.7"),))
    with pytest.raises(ValueError, match="not in the catalogue"):
        rr._membership_consistent()


# ── read-back ────────────────────────────────────────────────────────────────────────────────────────

class _LyingConn:
    """Stores nothing faithfully: every read returns a tampered row."""
    def __init__(self):
        self.inserted = []

    def execute(self, sql, params=()):
        if sql.lstrip().startswith("INSERT"):
            self.inserted.append(params)
            return _R(None)
        return _R(self.inserted[-1][:-1] + ("tampered",) if self.inserted else None)


class _R:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


def test_an_insert_that_reads_back_differently_is_a_divergence_not_a_success():
    store = rr.RuleRegistryStore(_LyingConn())
    row = {"predicate_id": "x", "rule_version": "1.0.0", "operator": "eq", "operands": {"a": "b:c"}}
    with pytest.raises(rr.RegistryDivergenceError, match="read-back"):
        store._bind("ka_gochara_predicate", ("predicate_id", "rule_version"), row)


# ── on the REAL 1154 schema ──────────────────────────────────────────────────────────────────────────

def test_the_real_schema_admits_the_flat_encoding_and_the_binder_reads_it_back(pg, successor):
    store = rr.RuleRegistryStore(pg)
    counts = store.seed()
    assert counts["paths"] == 6 and counts["seals"] == 6                  # P1..P5 @1.0.0 + P3 @1.2.0
    rows = store.bound_factor_rows("P3", "1.2.0")
    by_id = {r["factor_id"]: r for r in rows}
    assert set(by_id) == {"activity_kernel", "graduated_drishti"}
    assert by_id["activity_kernel"]["rule_version"] == "1.1.0"
    assert by_id["activity_kernel"]["applicability"]["span"]["inside"] == 1.0
    assert by_id["activity_kernel"]["applicability"]["angular"]["orb_deg"] is None
    assert by_id["graduated_drishti"]["applicability"] == {"relations": ["aspect"]}
    old = {r["factor_id"]: r for r in store.bound_factor_rows("P3", "1.0.0")}
    assert all(r["rule_version"] == "1.0.0" and "applicability" not in r for r in old.values())
    # the prose `direction` the against-channel rule reads is the catalogue's at the SAME exact
    # reference (the DB's own direction is the binary CHECK vocabulary)
    assert {r["direction"] for r in rows + list(old.values())} == {"higher = stronger"}
    assert ws.against_channel_state(rows) == "none_declared"
    assert store.seed()["reused"] > 0                                    # idempotent


def test_the_real_schema_refuses_a_nested_or_null_applicability(pg):
    psycopg = pytest.importorskip("psycopg")
    import json
    base = ("INSERT INTO public.ka_gochara_factor (factor_id, rule_version, operand_selector, direction,"
            " function, range_lower, range_upper, units, null_state, effect) VALUES"
            " ('activity_kernel','9.0.0',%s::jsonb,'higher_stronger','linear',0,1,'unitless',"
            "'unqualified','x')")
    with pytest.raises(psycopg.errors.CheckViolation):
        pg.execute(base, (json.dumps({"operand": "geometry:delta_lambda_to_exact",
                                      "applicability": {"span": {"inside": 1}}}),))     # nested
    with pytest.raises(psycopg.errors.CheckViolation):
        pg.execute(base, (json.dumps({"operand": "geometry:delta_lambda_to_exact",
                                      "angular_orb_deg": None}),))                       # JSON null


def test_the_sweep_lights_up_from_the_persisted_declaration_alone(pg, successor):
    store = rr.RuleRegistryStore(pg)
    store.seed()
    rec = lambda **kw: ws.SweepRecord(
        record_id="a", root_id="r", path_id="P3", rule_version=kw.pop("version"), relation="residence",
        object_kind="sign_span", agent="saturn", operator_role="scored", admission_state="admitted",
        supports=((datetime(2010, 1, 1, tzinfo=timezone.utc), datetime(2010, 1, 11, tzinfo=timezone.utc)),),
        canonical_target="span:7", inside_at=lambda t: True)
    for version, expect in (("1.0.0", None), ("1.2.0", 1.0)):
        (w,), _ = ws.draft_windows("marriage", [rec(version=version)],
                                   lambda p, v: store.bound_factor_rows(p, v))
        assert w.score == expect, (version, w)


def test_a_decoder_that_loses_the_declaration_is_caught_on_read_back(pg, successor, monkeypatch):
    store = rr.RuleRegistryStore(pg)
    store.seed()
    monkeypatch.setattr(rr, "decode_applicability", lambda flat: {})
    with pytest.raises(rr.RegistryDivergenceError, match="decoded applicability"):
        store.bound_factor_rows("P3", "1.2.0")


@pytest.mark.skipif(("activity_kernel", "1.1.0") not in rules_registry.FACTORS,
                    reason="activity_kernel@1.1.0 (AM-13, PR #2897) not on main yet")
def test_the_real_1_1_0_rows_flatten_and_round_trip():
    row = rules_registry.FACTORS[("activity_kernel", "1.1.0")]
    flat = rr.encode_applicability(row["applicability"])
    assert _mirror_named_operands_ok(flat)
    assert rr.decode_applicability(flat) == rr.canonical_applicability(row["applicability"])
