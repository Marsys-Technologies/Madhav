"""A5.3 — version-aware rule binding, on Stream B's ACTUAL 1.1.0 rows (Codex round 6 R5 / round 7 [4]).

ONE codec: `services.gochara_rules.flat_selector` (Stream B's). The binder has no codec of its own; it
persists the catalogue row's flat `operand_selector` VERBATIM, reads it back flat-to-flat, and requires
`decode(flat) == the declared applicability`. The successor rows are the real #2897/#2901/#2907 rows
(P2/P3/P4/P5@1.1.0, activity_kernel / graduated_drishti / vedha_attenuation @1.1.0) — nothing synthetic —
bound beside the 1.0.0 rows by the same deliberate edit of the explicit reference tuples that would bind
them in production (the production default stays @1.0.0 until they are accepted).

Each member keeps its OWN version; the selected path reference is passed through enumeration, inventory,
record materialisation and prerequisite results — never the global RULE_VERSION.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import inventory_verifier as ivr
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import window_sweep as ws
from services.gochara_rules import flat_selector as fs
from services.gochara_rules import registry as rules_registry

from ._bound_1_1_0 import SUCCESSOR_FACTORS, SUCCESSOR_PATHS, bind_successors
from .test_a53_record_store import (CHART, CHART_ID, HORIZON, _coverage_kwargs,  # noqa: F401
                                    _grain_kwargs, _house_from_lagna, _probe, _seed_saturn_crossings,
                                    _sky_convention_id)
from .test_a53_window_sweep_pg import pg  # noqa: F401  (fresh DB per test, 1081 + 1152–1157 applied)

REAL = {ref: rules_registry.FACTORS[ref] for ref in SUCCESSOR_FACTORS}


# ── ONE codec ────────────────────────────────────────────────────────────────────────────────────────

def test_the_binder_has_no_codec_of_its_own_it_calls_stream_bs():
    assert rr._flat is fs
    for gone in ("encode_applicability", "decode_applicability", "canonical_applicability"):
        assert not hasattr(rr, gone), f"{gone}: a second codec must not exist"
    assert rr._DECODE == {"activity_kernel": fs.decode_kernel, "graduated_drishti": fs.decode_drishti,
                          "vedha_attenuation": fs.decode_vedha}


@pytest.mark.parametrize("ref", SUCCESSOR_FACTORS)
def test_the_real_rows_persist_their_flat_selector_verbatim_and_decode_to_the_declaration(ref):
    row = REAL[ref]
    persisted = rr.factor_operand_selector(ref[0], row)
    assert persisted == row["operand_selector"]                     # verbatim — the flat form is the truth
    assert rr.decode_factor_selector(ref[0], persisted) == row["applicability"]
    assert None not in persisted.values()                           # no JSON null, ever
    assert fs.decode_kernel(persisted) == row["applicability"] if ref[0] == "activity_kernel" else True


def test_the_unchanged_1_0_0_rows_keep_their_plain_operand_token_and_declare_no_applicability():
    for fid in ("activity_kernel", "graduated_drishti", "vedha_attenuation"):
        src = rules_registry.FACTORS[(fid, "1.0.0")]
        sel = rr.factor_operand_selector(fid, src)
        assert set(sel) == {"operand"} and rr.decode_factor_selector(fid, sel) is None


def test_a_flat_selector_the_shared_codec_refuses_is_refused_by_the_binder():
    base = copy.deepcopy(REAL[("activity_kernel", "1.1.0")])
    bad_key = dict(base, operand_selector={**base["operand_selector"], "mystery": 1})
    with pytest.raises(rr.RegistryDivergenceError, match="refused"):
        rr.factor_operand_selector("activity_kernel", bad_key)
    # a numeric orb is admissible ONLY with orb_state=ratified AND a decision-ref token (the codec's rule)
    bare_orb = dict(base, operand_selector={**base["operand_selector"], "orb_deg": 5.0})
    with pytest.raises(rr.RegistryDivergenceError, match="refused"):
        rr.factor_operand_selector("activity_kernel", bare_orb)
    unknown_state = dict(base, operand_selector={**base["operand_selector"], "orb_state": "maybe"})
    with pytest.raises(rr.RegistryDivergenceError, match="refused"):
        rr.factor_operand_selector("activity_kernel", unknown_state)


# ── explicit composite references, each member at its OWN version ────────────────────────────────────

def test_no_row_is_selected_by_the_global_version_constant(monkeypatch):
    before = (rr.predicate_rows(), rr.factor_rows(), rr.path_rows(), rr.prerequisite_rows(),
              rr.soft_factor_rows())
    monkeypatch.setattr(rr, "RULE_VERSION", "9.9.9")          # a global bump must change NOTHING
    after = (rr.predicate_rows(), rr.factor_rows(), rr.path_rows(), rr.prerequisite_rows(),
             rr.soft_factor_rows())
    assert before == after


def test_the_default_binding_stays_at_1_0_0_until_the_successors_are_accepted():
    assert rr.BOUND_PATH_REFS == tuple((p, "1.0.0") for p in ("P1", "P2", "P3", "P4", "P5"))
    assert all(isinstance(r, tuple) and len(r) == 2 for r in
               rr.BOUND_PATH_REFS + rr.BOUND_FACTOR_REFS + rr.BOUND_PREDICATE_REFS)
    assert not set(SUCCESSOR_PATHS) & set(rr.BOUND_PATH_REFS)
    assert not set(SUCCESSOR_FACTORS) & set(rr.BOUND_FACTOR_REFS)


def test_the_catalogue_and_the_selection_are_read_at_call_time_never_captured(monkeypatch):
    assert rr.selected_path_version("marriage", "P3") == "1.0.0"
    bind_successors(monkeypatch)
    assert ("P3", "1.1.0") in rr.bound_path_refs()                 # bound into the CATALOGUE ...
    assert rr.selected_path_version("marriage", "P3") == "1.0.0"   # ... without changing what is SEARCHED
    monkeypatch.setattr(rr, "SELECTED_PATH_REFS", tuple(("P3", "1.1.0") if p == "P3" else (p, v)
                                                        for p, v in rr.SELECTED_PATH_REFS))
    assert rr.selected_path_version("marriage", "P3") == "1.1.0"
    with pytest.raises(KeyError):
        rr.selected_path_version("marriage", "P9")


def test_the_real_successors_bind_beside_the_old_versions_each_member_at_its_own_version(monkeypatch):
    bind_successors(monkeypatch)
    rr._membership_consistent()
    paths = {(r["path_id"], r["rule_version"]) for r in rr.path_rows()}
    assert set(SUCCESSOR_PATHS) | {("P3", "1.0.0")} <= paths
    soft = {(r["path_id"], r["rule_version"], r["factor_id"], r["factor_rule_version"])
            for r in rr.soft_factor_rows()}
    assert ("P3", "1.0.0", "activity_kernel", "1.0.0") in soft          # the old version is untouched
    assert ("P3", "1.1.0", "activity_kernel", "1.1.0") in soft
    assert ("P3", "1.1.0", "graduated_drishti", "1.1.0") in soft
    assert ("P2", "1.1.0", "vedha_attenuation", "1.1.0") in soft
    pre = {(r["path_id"], r["rule_version"], r["predicate_id"], r["predicate_rule_version"])
           for r in rr.prerequisite_rows()}
    # the prerequisite keeps ITS OWN version: path 1.1.0, predicate 1.0.0
    assert ("P3", "1.1.0", "p3_contact_house_or_lord", "1.0.0") in pre
    assert ("P4", "1.1.0", "p4_double_transit", "1.0.0") in pre
    sel = {(r["factor_id"], r["rule_version"]): r["operand_selector"] for r in rr.factor_rows()}
    assert sel[("activity_kernel", "1.1.0")] == REAL[("activity_kernel", "1.1.0")]["operand_selector"]
    assert set(sel[("activity_kernel", "1.0.0")]) == {"operand"}


def test_a_path_reference_to_an_unbound_member_version_is_refused_before_any_sql(monkeypatch):
    bind_successors(monkeypatch)
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


# ── on the REAL 1154 schema, with the ACTUAL rows ────────────────────────────────────────────────────

def test_the_real_schema_admits_the_actual_flat_rows_and_the_binder_reads_them_back(pg, monkeypatch):
    bind_successors(monkeypatch)
    store = rr.RuleRegistryStore(pg)
    counts = store.seed()
    assert counts["paths"] == 9 and counts["seals"] == 9                # P1..P5 @1.0.0 + P2..P5 @1.1.0
    rows = store.bound_factor_rows("P3", "1.1.0")
    by_id = {r["factor_id"]: r for r in rows}
    assert set(by_id) == {"activity_kernel", "graduated_drishti"}
    for fid, r in by_id.items():
        real = REAL[(fid, "1.1.0")]
        assert r["rule_version"] == "1.1.0"
        assert r["operand_selector"] == real["operand_selector"]        # flat-to-flat, as persisted
        assert r["applicability"] == real["applicability"]              # decode(flat) == the declaration
    assert by_id["activity_kernel"]["applicability"]["angular"]["orb_deg"] is None
    assert by_id["activity_kernel"]["applicability"]["span"]["inside"] == 1
    old = {r["factor_id"]: r for r in store.bound_factor_rows("P3", "1.0.0")}
    assert all(r["rule_version"] == "1.0.0" and "applicability" not in r for r in old.values())
    assert {r["direction"] for r in rows + list(old.values())} == {"higher = stronger"}
    assert ws.against_channel_state(rows) == "none_declared"
    assert store.seed()["reused"] > 0                                    # idempotent
    # the vedha successor binds through P2@1.1.0 too (its flat selector is the catalogue's)
    (vedha,) = store.bound_factor_rows("P2", "1.1.0")
    assert vedha["operand_selector"] == REAL[("vedha_attenuation", "1.1.0")]["operand_selector"]
    assert vedha["applicability"] == REAL[("vedha_attenuation", "1.1.0")]["applicability"]


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
                                      "orb_deg": None}),))                               # JSON null


def test_the_sweep_lights_up_from_the_persisted_declaration_alone(pg, monkeypatch):
    bind_successors(monkeypatch)
    store = rr.RuleRegistryStore(pg)
    store.seed()
    rec = lambda **kw: ws.SweepRecord(
        record_id="a", root_id="r", path_id="P3", rule_version=kw.pop("version"), relation="residence",
        object_kind="sign_span", agent="saturn", operator_role="scored", admission_state="admitted",
        supports=((datetime(2010, 1, 1, tzinfo=timezone.utc), datetime(2010, 1, 11, tzinfo=timezone.utc)),),
        canonical_target="span:7", longitude_at=lambda t: 190.0)
    for version, expect in (("1.0.0", None), ("1.1.0", 1.0)):
        (w,), _ = ws.draft_windows("marriage", [rec(version=version)],
                                   lambda p, v: store.bound_factor_rows(p, v))
        assert w.score == expect, (version, w)


def test_a_decoder_that_loses_the_declaration_is_caught_on_read_back(pg, monkeypatch):
    bind_successors(monkeypatch)
    store = rr.RuleRegistryStore(pg)
    store.seed()
    monkeypatch.setattr(rr, "_DECODE", {**rr._DECODE, "activity_kernel": lambda flat: {}})
    with pytest.raises(rr.RegistryDivergenceError, match="decoded applicability"):
        store.bound_factor_rows("P3", "1.1.0")


def test_a_persisted_selector_that_differs_from_the_declaration_is_caught_on_read_back(pg, monkeypatch):
    bind_successors(monkeypatch)
    store = rr.RuleRegistryStore(pg)
    store.seed()
    drifted = copy.deepcopy(rules_registry.FACTORS)
    ref = ("activity_kernel", "1.1.0")
    drifted[ref] = dict(drifted[ref], operand_selector={**drifted[ref]["operand_selector"],
                                                        "span_inside": 0})
    monkeypatch.setattr(rules_registry, "FACTORS", drifted)
    with pytest.raises(rr.RegistryDivergenceError, match="diverges"):
        store.bound_factor_rows("P3", "1.1.0")


# ── the selected path reference reaches enumeration, inventory and records (Codex round 7 [4]) ───────

def test_enumeration_carries_the_selected_path_version_for_every_path_and_class():
    for path in ("P1", "P2", "P3", "P4", "P5"):
        for version in ("1.0.0", "1.1.0") if path != "P1" else ("1.0.0",):
            edges = ev.enumerate_edges("marriage", path, CHART, rule_version=version)
            assert edges, (path, version)
            assert {e.rule_version for e in edges} == {version}, (path, version)
            assert {e.path_id for e in edges} == {path}
            citations = {e.source_text for e in edges if e.source_text is not None}
            assert citations <= {rules_registry.RULE_PATHS[(path, version)].get("source_text"), None,
                                 *(e.source_text for e in edges if e.operator_role == "testimony")}


def test_a_path_enumerated_at_a_version_missing_from_the_catalogue_refuses_loudly():
    with pytest.raises(KeyError):
        ev.enumerate_edges("marriage", "P3", CHART, rule_version="7.7.7")


def test_inventory_pins_and_obligation_ids_follow_the_selected_version_and_the_verifier_agrees():
    from .test_a53_inventory import CHART as INV_CHART
    from .test_a53_inventory import FULL, H0, H1, P5_EXCL
    sealed = [("P3", "1.1.0"), ("P4", "1.1.0")]
    plan = inv.plan_class_inventory(event_class="marriage", chart=INV_CHART, horizon=(H0, H1),
                                    sealed_paths=sealed, capability=FULL, dasha_rows=None,
                                    path_exclusions={"P5": P5_EXCL})
    assert {p.rule_version for p in plan.pins} == {"1.1.0"}
    assert plan.obligations and all(o.rule_version == "1.1.0" for o in plan.obligations)
    for o in plan.obligations:
        assert o.canonical_bytes.split("|")[2] == "1.1.0"
    # the verifier derives the same obligation bytes independently from the spec, at the SAME version
    vchart = {"lagna": INV_CHART["lagna_deg"],
              "natal": {k.lower(): v for k, v in INV_CHART["natal"].items()}}
    for pid, ver in sealed:
        pin = ivr.derive_path_pin("marriage", vchart, pid, ver, excluded_agents=("moon",), path_exclusions={},
                                  h_unknown_exclusion=None)
        mine = sorted(o.canonical_bytes for o in plan.obligations if o.path_id == pid)
        assert pin["obligations"] == mine and all(b.split("|")[2] == "1.1.0" for b in mine)


def _pg_grain_at(pg, monkeypatch, version):
    bind_successors(monkeypatch)
    rr.RuleRegistryStore(pg).seed()
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(pg)
        _seed_saturn_crossings(pg, sky_cid)
    store = rs.RecordStore(pg)
    kala_cid = store.ensure_kala_convention()
    edges = ev.enumerate_edges("marriage", "P3", CHART, rule_version=version)
    libra = [e for e in edges if e.transit and e.relation == "residence" and e.agent == "saturn"
             and e.obj.canonical_target == "span:7"]
    assert len(libra) == 1
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **{**_coverage_kwargs(store, kala_cid, sky_cid), "class_edges": edges})
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(
            store, **{**_grain_kwargs(store, sky_cid), "edges": libra, "chart": CHART,
                      "rule_version": version})
    return counts, store


@pytest.mark.parametrize("version", ["1.0.0", "1.1.0"])
def test_records_and_prerequisite_results_are_written_at_each_members_own_version(pg, monkeypatch, version):
    counts, _store = _pg_grain_at(pg, monkeypatch, version)
    assert counts["records"] == 1
    (rec_version,) = pg.execute(
        "SELECT DISTINCT rule_version FROM public.ka_gochara_relationship_record WHERE path_id = 'P3'"
    ).fetchone()
    assert rec_version == version
    rows = pg.execute(
        "SELECT p.predicate_id, p.predicate_rule_version, p.result"
        " FROM public.ka_gochara_record_prerequisite p ORDER BY p.ordinal").fetchall()
    assert rows, "the record's prerequisite membership must be persisted"
    for pid, pred_version, result in rows:
        assert pred_version == "1.0.0", (pid, pred_version)             # the PREDICATE's own version
        assert result is not None, f"{pid}: the result was never written (wrong predicate version?)"
    assert counts["prereq_evaluated"] == len(rows)


def test_a_grain_whose_edges_disagree_with_the_selected_version_refuses(pg, monkeypatch):
    bind_successors(monkeypatch)
    rr.RuleRegistryStore(pg).seed()
    store = rs.RecordStore(pg)
    old_edge = ev.enumerate_edges("marriage", "P3", CHART, rule_version="1.0.0")[0]
    with pytest.raises(ValueError, match="selected"):
        rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation="5.0", event_class="marriage", path_id="P3",
            edges=[old_edge], horizon=HORIZON, position_at=_probe([(10, 200)]),
            house_for=_house_from_lagna(CHART["lagna_deg"]), sky_convention_id="x",
            source_fact_ids=["fact-1"], rule_version="1.1.0")


def test_the_writer_selects_each_paths_version_from_the_selection_not_a_global(monkeypatch):
    import inspect

    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    src = inspect.getsource(writer_mod)
    assert "RULE_VERSION" not in src.replace("gk_rule_registry", "")
    assert "bound_path_version" not in src and "selected_path_version" in src
    bind_successors(monkeypatch)
    monkeypatch.setattr(rr, "SELECTED_PATH_REFS", tuple(("P3", "1.1.0") if p == "P3" else (p, v)
                                                        for p, v in rr.SELECTED_PATH_REFS))
    assert writer_mod.gk_rule_registry.selected_path_version("marriage", "P3") == "1.1.0"
