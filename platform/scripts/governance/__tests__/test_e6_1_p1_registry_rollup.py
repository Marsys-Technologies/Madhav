"""test_e6_1_p1_registry_rollup.py — E6.1 packet 1 (+ E6.2 rollup), Track E brief §8.

Covers: `layers` / `columns_any` / `asset_kinds` on EVERY CRITERION_REGISTRY entry; N/A decided by a
declared rule (never by absence); the worst-of rollup (FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS);
a gate with no checks = NO_DETECTOR; cells versioned with the registry revision; and a regression
fixture over all 127 assets' committed census cells (verdict-only compaction of census_L0..L5.json).
Pure functions only; no database.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))
ALL_LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")

# Pinned registry content per revision. Changing ANY entry / rule / gate list without bumping
# REGISTRY_REVISION and adding the new pin here fails CI: the revision cannot lag the content.
PINNED_FINGERPRINTS = {
    1: "081076941ed6cec9abae08df5676e46e36c834764e84595f418f1155b701c909",
    # 2 (E6 packet a): measured-N/A rule ids are cause-keyed; NA_CAUSES joins the fingerprinted content
    2: "a0557b51341fdb5d86288b44ac459f1d19c6d9fd7f26eec15f28e8dbc05a99cf",
    # 3 (E6 review fix 2): Earn.build_record gains the cause no-registered-writer (healthy-non-execution narrowed)
    3: "7f30f61e123b473702eb37236b4c22628a5251ef7fd85a31cfb482ca304c6c5e",
    # 4 (E6.1 d): Dens.served revision 4 (contract AND a tier column in the served select; structural; cause no-served-surface)
    4: "5d96f986f927d9c4cb6f46edbc03e9762ba1889d0d71054bd8476b6807d583fc",
    # 5 (E6 packet c): Narr.agree/checkable/fidelity_test/lint and Null.schema_default/blank_rows registered; NA_CAUSES gains
    # no-prose / no-prose-declared (later branches re-pin on rebase: the pins are content-bound)
    5: "b44523131a5e9032f507f4df701af44e096f1b664852e8460a69723094bc5522",
    # 6 (E6 items g+h on top of packet c): Build.target rev 2 (declared service, PASS by declaration), Build.dag rev 2 (any-layer
    # unknown dep, cycle, reads-match aligned with dag_edge_guard), Idem.pattern rev 2 (one relative-import resolver)
    6: "62f08ad67334705860cf9bd4652a89efc4787f5e4eb3f1d0bab4fcad2ac0b8ce",
    # 7 (E6 item f): NA_CAUSES gains Carr.D1/D2/D3:no-carriage (the registry is unchanged; NA_CAUSES is fingerprinted)
    7: "118c3154f9fc136fb83a33f4568e49688f8cf639336cae346643127e101d52f9",
    # 8 (E6 item i, SS A2): Carr.detector RETIRED - removed from the registry (32 to 31 entries; Carr is exactly D1-D3)
    8: "0479f0cdaaa56c5838f2e1a4ce5ab3a59606b856ba0acd201d3f67725bed0842",
    # 9 (SS N-65): NA_RULE_DECISIONS declares R01 Build.history#measured:never-run, R02 Dens.served#measured:no-served-surface and
    # R03 Narr.{agree,checkable,fidelity_test,lint}#measured:no-prose (the registry and NA_CAUSES are unchanged; the rules are fingerprinted)
    9: "9bfe15eccdd096e0a8def9199a6794a99a241e9ebd8fb1c5aadafa61a526e499",
    # 10 (SS N-72): + Build.dep_liveness#measured:no-declared-dependencies (S4) and Earn.service_state#measured:not-a-service; NA_CAUSES gains
    # Earn.service_state:not-a-service (the registry criteria are unchanged)
    10: "1b980d1c48d19b53589db234ebeb5c2cbbffb6cddd5535ae7390b97b2a22666a",
    # 11 (SS N-72 S2, N-73; provisional): Carr.D1 gets a detector (revision 2), NA_CAUSES gains Carr.D1/D2/D3:not-the-declared-carriage and
    # :ratified_judgment, and the three not-the-declared-carriage rules are declared (inert until an asset declares a carriage check)
    11: "c066a88e36b61827422796ae98f59a679458bbcb8ba88e2d80d351d582a39940",
    # 12 (SS N-72 S3, N-73 (1)/(4), N-74 (b); provisional): Vocab.alias rev 2 / Ldgr.source_presence rev 3 (declared forms: an alias class measured against
    # bg_ontology class planet; a declared source column with its citation_state), NA_CAUSES gains Vocab.alias:no-alias-class and
    # Ldgr.source_presence:no-classical-claim, and the two declaration-keyed rules are declared (inert until an asset declares); columns_any unchanged
    12: "35b0e03e412d0d36d8af2840bd3d4d612af2859e56035c90342266c98e33ed3d",
    # 13 (SS N-72 S1, N-73, N-74; provisional): Null.schema_default / Null.blank_rows rev 2 (an asset that DECLARES `null_convention` gets the declared form:
    # the Null cap lifts per asset only when schema_default and blank_rows are clean AND the detector verifies the convention; the cap line itself is unchanged);
    # no N/A rule, NA_CAUSES unchanged, inert until an asset declares one
    13: "fdee1861e969d88dc1139cbd0ff040d7b217710db3684313e00277c8150a85f1",
    # 14 (SS N-74 item 5, N-74(a); provisional): Dens.served rev 5 (the scan tells a SELECT of the asset's table from a LABEL: an asset a serving module only
    # names in a provenance string / prose / type name / import path / label-keyed value / map key is not reached, so it can read the no-served-surface N/A;
    # every unclassifiable form stays a reach) and R02's decision text is cause-keyed ("an asset no served module selects rows from; being named only as a
    # provenance label is not a select"; N/A = "not served directly", not "unused"); a service-kind asset named in a service_probe envelope is a REACH, not a label
    # (bg_ephemeris_engine / bg_panchanga stay NO_DETECTOR); NA_CAUSES unchanged, asset_declarations.json unchanged
    14: "f4af0c6c1e24fd25e41409f8f33ffeac8333411df2936bc9270d438ca20bc0f2",
    # 15 (STAMP; provisional): `null_convention.stamp_columns: [{column, why}]`, a declared word for a write-time stamp column: the detector requires a NOT NULL timestamp /
    # timestamptz with no NULL row and no sentinel timestamp and exempts it from the constant test ONLY (nothing else exempted); Null.schema_default / Null.blank_rows revision 3 (applicability text);
    # NA_CAUSES / NA_RULE_DECISIONS unchanged, inert until an asset declares one
    15: "ef64d8b9b8ec924d724a13e249e7e6a5f049beeb2d51932c10fb0be557985345",
    # 16 (NARR-GUARD, N-94; provisional): `prose_coupling: {to: carriage_d1, columns, why, evidence}`, a declared word beside prose_fields []: the four Narr N/A releases of an asset that declares it stand
    # only while its own Carr.D1 reads PASS (else NO_DETECTOR); Narr.agree / checkable / fidelity_test / lint revision 2 (applicability text); NA_CAUSES / NA_RULE_DECISIONS unchanged, inert until declared
    16: "8b88e7b26f32fdf8f665533b96357c8c332fb142a7166a6468a0f64ec51cb97c",
    # 23 (DENS-TIER-GUARD, N-98; provisional; pin 23 is pre-allocated, pins 17-22 belong to other lanes): the Dens tier vocabulary is a CLOSED list: a column counts as a tier only when it is exactly `tier` /
    # `verification_pass_status`, or the asset declares it in density_tier_columns, and never when its name carries a deny-listed word (cost, price, pricing, plan, access, subscription, billing, fee, tariff);
    # Dens.served revision 6 (applicability text); NA_CAUSES / NA_RULE_DECISIONS unchanged, inert until an asset declares density_tier_columns
    23: "9a2b66cb84afcdf018a6ae0cde084756b42795d9e73b000c6526842bcaa855d4",
    # 24 (C2(ii), SS N-98; provisional; 23 is the Dens tier PR #3037, 17-22 belong to other lanes; the fingerprint carries both Dens.served rev 6 and Ldgr.source_presence rev 4): Ldgr.source_presence revision 4 (applicability text states the rule): the legacy undeclared
    # reading no longer counts a placeholder citation ('UNSOURCED ...', a tradition label, the closed no-source list) as a source; NA_CAUSES / NA_RULE_DECISIONS unchanged, asset_declarations.json untouched
    24: "11c95b0287421194cab6a609d3ac6dc7905a63f236ba139f3a9db41945d60640",
    # 25 (N-99; provisional; stacked on pin 24 (C2 Ldgr) and pin 23 (DENS-TIER-GUARD)): Build.completion revision 3 (applicability text): count equality alone no longer reads PASS when the asset declares an
    # integrity_check_sql that does not hold (false / refused / oversize / errored / timed out reads PARTIAL naming which; permission denied under the census role reads NO_DETECTOR); an undeclared asset is unchanged; NA_CAUSES / NA_RULE_DECISIONS unchanged
    25: "0e78e228d140d04920cb12bcd8b5bd9c8b33ca59ac8f9105853a139b8289d698",
    # 26 (the engine 100% build-out revision, N-150 / N-151; provisional): ONE revision for the whole build-out. Step 1 is the bare bump (content unchanged, so the fingerprint equals pin 25's);
    # each later detector commit of the build-out re-pins this line to the content it lands
    # (N-176 / N-177 / N-178, SS 2026-10-07; the engine-fixes-II branch re-pins this line ONCE: Vocab.alias rev 7 (the value-based detector, revised after its independent reviews, round 3: any chart reference keeps the chart scope, all produced filters ORed, an empty scoped read is vacuous; round 2: locale-independent SQL fold, rest-of-column existence read of every category, the measured-chart scope of every data read and the asset's own rows of a shared table; round 1: existence probe of incomplete columns, embedded terms and json keys, short aliases, one normalisation, spelling families; NA_CAUSES + a rule: no-vocabulary-values), Ldgr.source_presence rev 6 (the closed-list residual
    # UNSOURCED_DECLARED; NA_CAUSES + a rule: unsourced-declared), Build.completion rev 6 (the latest-attempt rule); the prose_none existence read changes no registry text); the FORM-GAP branch (SS N-191 / N-192, declarations 1.39.0-1.52.0) re-pins this line ONCE more: the six prose criteria's applicability text names the scaled closed-vocabulary / leaf-pattern bounds and the CHECKED forms run_stamp_columns, templated_columns, unset_columns, static_read and curated_corpus (Narr.agree rev 7, Narr.checkable rev 6, Narr.fidelity_test rev 6, Narr.lint rev 7, Null.schema_default rev 8, Null.blank_rows rev 8); REGISTRY_REVISION stays 26; the SAME re-pin also carries SS N-203: Build.registered rev 3 (the `writer_sibling` form: a registry sibling reads PASS only when its writer-backed primary shares the writer file and the sibling's tables are in the primary writer's produced set)
    # N-189 (SS, the forwarded-leaf detector, N-194 review rounds; rebased onto main after #3219): Null.schema_default and Null.blank_rows rev 8 (an asset that declares `forwarded_leaves` is also measured by the forwarded-leaf detector: its forwarded L1 leaves are compared with the cited L1 fact in one set-based join on the measured chart, the writer's whole-string uuid-v4 strip is mirrored exactly, the own fact / extra keys / composites / the divisional cross-check / every verification method are measured or named; a pass and clean data graders lift both Null checks over the static scan's empty-string fallbacks and dynamic-row caveat, only inside the declared covered code and at the pinned count); NA_CAUSES / NA_RULE_DECISIONS unchanged
    # N-212 + FORM-GAP merged (Dens.served rev 14 + Null.schema_default / Null.blank_rows rev 9): re-pinned once
    # N-233 (SS ruling; the engine-N233 branch re-pins this line ONCE): Vocab.alias rev 8 (a REGISTERED bg_ontology alias, read live from brahma_ontology, compared by plain case-fold over the English name, Sanskrit name and synonyms, counts as canonical; ruling A; SS N-235: the declared graha code column, the Carr.D1/D2/D3 ratified_judgment rules, and the UNSOURCED_DECLARED residual over a declared set of columns; SS N-236: the checked service wiring for Earn.service_state, the sibling credit for Build.exercised / Build.history / Earn.build_record, and the function-entry helper credit for Dens.served; SS N-239: Earn.service_state PASS needs a fresh (24 h) record, the Ldgr signal-id resolution uses the primary-key index, Narr.agree names an unread prose_excluded) and Build.history rev 3
    # (the certification window opens at the bottom-up pass, build run ca17639b; an error is explained only by a pinned run/cause list); the certification rule (census_postprocess) checks ruled residuals
    # against the engine's closed N/A rule list and changes no registry text
    # SS N-256: Vocab.alias gains the checked vocab_embedded_text exemption (criterion text only; the walk time budget and the Unknown-as-unread rule change no registry text); re-pinned once
    26: "dba753148765a91eb9c692430b1de9be63d16285a325347291a1e8b2f494d363",
}


# ───────────────────────── registry shape ─────────────────────────

def test_every_entry_declares_layers_columns_any_and_asset_kinds_explicitly():
    for crit, e in ac.CRITERION_REGISTRY.items():
        for k in ("layers", "columns_any", "asset_kinds"):
            assert k in e, f"{crit} missing explicit key {k}"
        assert isinstance(e["layers"], tuple) and e["layers"], crit
        assert set(e["layers"]) <= set(ac.LAYERS), crit
        for k in ("columns_any", "asset_kinds"):
            assert e[k] is None or (isinstance(e[k], tuple) and e[k] and all(isinstance(x, str) for x in e[k])), (crit, k)


def test_layers_cover_every_layer_where_the_criterion_is_measured_today():
    """Narrowing `layers` below a measured layer would silently drop committed verdicts."""
    for layer, assets in FIXTURE["layers"].items():
        for aid, ms in assets.items():
            for crit in ms:
                assert crit in ac.CRITERION_REGISTRY, (aid, crit)   # the fixture no longer carries the retired Carr.detector
                assert layer in ac.CRITERION_REGISTRY[crit]["layers"], (layer, aid, crit)


def test_column_patterns_are_the_ones_measure_already_uses():
    assert ac.CRITERION_REGISTRY["Ldgr.source_presence"]["columns_any"] == ac.CITATION_COLUMNS
    assert ac.CITATION_COLUMNS == ("source_citation", "source_text_id", "classical_citation",
                                   "classical_citations", "citation_ref")
    assert ac.CRITERION_REGISTRY["Vocab.alias"]["columns_any"] == ("synonyms",)
    assert ac.CRITERION_REGISTRY["Earn.service_state"]["asset_kinds"] == ("service",)
    assert ac.ALIAS_COLUMN == "synonyms"
    assert ac.CRITERION_REGISTRY["Vocab.alias"]["columns_any"] == (ac.ALIAS_COLUMN,)


def test_alias_census_reads_the_shared_alias_column_constant(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "ALIAS_COLUMN", "aka")
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: seen.append(sql) or [["(all)", "3", "1"]])
    assert ac.alias_census("t", ["id", "synonyms"]) is None          # the old literal is no longer the alias column
    assert ac.alias_census("t", ["id", "aka"]) == {"(all)": dict(rows=3, no_alias=1)}
    assert "aka IS NULL OR cardinality(aka)=0" in seen[0] and "synonyms" not in seen[0]


def _reg_row(aid, target_table=None):
    return dict(asset_id=aid, has_writer=False, target_table=target_table, count_sql="",
                has_integrity=False, depends_on=[], target_floor=None, catalog_status="", asset_kind="")


def _stub_layer(monkeypatch, ctrl, reg, tables):
    # same offline measure() harness as test_r60_ldgr_source_presence_singular_citation.py
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def test_measure_selects_the_first_of_citation_columns_when_a_table_has_two(monkeypatch, tmp_path):
    """Behavioural pin (replaces a substring check on measure()'s source): with two citation columns
    present, measure() must probe the FIRST of CITATION_COLUMNS, the one the registry declares first."""
    first, later = ac.CITATION_COLUMNS[0], ac.CITATION_COLUMNS[3]
    assert first != later
    # column order in the table is the reverse of CITATION_COLUMNS' priority, so a positional pick would differ
    _stub_layer(monkeypatch, tmp_path, {"bg_two": _reg_row("bg_two", "bg_two")},
                {"bg_two": (["id", later, first], [])})
    seen = []

    def fake_psql(sql, sep="\x1f", timeout=None):
        seen.append(sql)
        if "format_type(a.atttypid" in sql:
            return [["text"]]
        if "jsonb_build_object('rows'" in sql and '"bg_two"' in sql:
            return [['{"rows":48,"null":0,"placeholder":0}']]
        raise AssertionError(f"unexpected query: {sql[:100]}")

    monkeypatch.setattr(ac, "psql", fake_psql)
    census = ac.measure("L0")
    res = next(a for a in census["assets"] if a["asset_id"] == "bg_two")["measurements"]["Ldgr.source_presence"]
    assert {k: v for k, v in res.items() if k != "read_scope"} == dict(v=ac.PASS, measured=f"{first} populated on 48/48 rows")
    assert res["read_scope"] == {"bg_two": "whole table (global: no chart_id column)"}                  # the measured-chart scope stamp: no chart_id column, so global, said so
    cit_sql = [q for q in seen if "jsonb_build_object('rows'" in q]
    assert cit_sql == [ac.ldgr_legacy_count_sql("bg_two", first, "text")]       # C2(ii): exactly one read, of the FIRST column of the table (the SQL builder is the one definition)
    assert f'"{first}"::text AS v' in cit_sql[0] and f'"{later}"' not in cit_sql[0]


# ───────────────────────── applicability ─────────────────────────

def test_applicability_layer_columns_kind_and_unknown_are_distinct_states():
    f = ac.criterion_applicability
    assert f("Build.dag", "L2", None)["state"] == "APPLIES"
    # column pattern: facts absent -> UNKNOWN, never NOT_APPLICABLE
    assert f("Ldgr.source_presence", "L1", None)["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {})["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {"columns": ["id", "x"]})["state"] == "NOT_APPLICABLE"
    assert f("Ldgr.source_presence", "L1", {"columns": ["id", "classical_citation"]})["state"] == "APPLIES"
    assert f("Ldgr.source_presence", "L1", {"columns": []})["state"] == "UNKNOWN"
    assert f("Earn.service_state", "L3", None)["state"] == "UNKNOWN"
    assert f("Earn.service_state", "L3", {"asset_kind": "data"})["state"] == "NOT_APPLICABLE"
    assert f("Earn.service_state", "L3", {"asset_kind": "service"})["state"] == "APPLIES"
    # NOT_APPLICABLE dominates UNKNOWN when one fact disproves and the other is missing
    assert f("Earn.service_state", "L3", {"asset_kind": "data"})["rule_id"] == "Earn.service_state#asset_kinds"
    assert f("Ldgr.source_presence", "L1", {"columns": ["id"]})["rule_id"] == "Ldgr.source_presence#columns_any"


@pytest.mark.parametrize("bad_columns", [[], (), set(), "abc", "source_citation", 7, ["id", 3], {"columns": 1}])
def test_a_malformed_or_empty_columns_fact_is_not_evidence(bad_columns):
    """An empty list or a wrong-typed value is not a supplied fact: UNKNOWN, never NOT_APPLICABLE
    (and never APPLIES from a bare string whose substring matches)."""
    for layer in ("L1", "L0"):
        assert ac.criterion_applicability("Ldgr.source_presence", layer, {"columns": bad_columns})["state"] == "UNKNOWN"
    assert ac.rollup_asset("L1", {}, {"columns": bad_columns})["Ldgr"]["v"] != "N/A"


@pytest.mark.parametrize("bad_kind", ["", 3, None, ["service"], b"service"])
def test_a_malformed_or_empty_asset_kind_fact_is_not_evidence(bad_kind):
    assert ac.criterion_applicability("Earn.service_state", "L3", {"asset_kind": bad_kind})["state"] == "UNKNOWN"


def test_columns_known_true_makes_an_empty_column_list_evidence():
    f = ac.criterion_applicability
    r = f("Ldgr.source_presence", "L1", {"columns": [], "columns_known": True})
    assert r["state"] == "NOT_APPLICABLE" and r["rule_id"] == "Ldgr.source_presence#columns_any"
    # columns_known must be exactly True, and only relaxes the emptiness rule, not the type rule
    assert f("Ldgr.source_presence", "L1", {"columns": [], "columns_known": 1})["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {"columns": "abc", "columns_known": True})["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {"columns": ("id",), "columns_known": True})["state"] == "NOT_APPLICABLE"


def test_unknown_layer_raises_keyerror():
    with pytest.raises(KeyError):
        ac.criterion_applicability("Build.dag", "L9", None)
    with pytest.raises(KeyError):
        ac.criterion_applicability("Ldgr.source_presence", "", {"columns": ["id"]})


def test_out_of_layer_when_layer_not_declared(monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Build.dag"] = dict(reg["Build.dag"], layers=("L0",))
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    assert ac.criterion_applicability("Build.dag", "L2", None)["state"] == "OUT_OF_LAYER"
    assert ac.criterion_applicability("Build.dag", "L0", None)["state"] == "APPLIES"


def test_unregistered_criterion_raises():
    with pytest.raises(KeyError):
        ac.criterion_applicability("Nope.nope", "L0", None)


# ───────────────────────── rollup_verdicts ─────────────────────────

@pytest.mark.parametrize("vs,want", [
    (["PASS", "PASS"], "PASS"),
    (["PASS", "PARTIAL"], "PARTIAL"),
    (["PARTIAL", "NO_DETECTOR"], "NO_DETECTOR"),
    (["NO_DETECTOR", "ERRORED"], "ERRORED"),
    (["ERRORED", "FAIL", "PASS"], "FAIL"),
    (["FAIL", "N/A"], "FAIL"),
    (["PASS", "N/A"], "PASS"),
    (["N/A", "N/A"], "N/A"),
    ([], "NO_DETECTOR"),
])
def test_rollup_verdicts_worst_wins(vs, want):
    assert ac.rollup_verdicts(vs) == want
    assert ac.rollup_verdicts(list(reversed(vs))) == want


def test_rollup_order_constant():
    assert ac.ROLLUP_ORDER == ("FAIL", "ERRORED", "NO_DETECTOR", "PARTIAL", "PASS")


def test_rollup_verdicts_accepts_any_iterable_and_does_not_drain_it():
    assert ac.rollup_verdicts(iter(["FAIL"])) == "FAIL"
    assert ac.rollup_verdicts(("FAIL",)) == "FAIL"
    assert ac.rollup_verdicts(v for v in ["PASS", "PARTIAL"]) == "PARTIAL"
    assert ac.rollup_verdicts(iter([])) == "NO_DETECTOR"


def test_rollup_verdicts_rejects_a_bare_string():
    for bare in ("FAIL", "PASS", "N/A", ""):
        with pytest.raises(TypeError):
            ac.rollup_verdicts(bare)


@pytest.mark.parametrize("bad", ["NOT_GENERIC", "UNKNOWN", "pass", "", None])
def test_rollup_verdicts_rejects_a_verdict_outside_the_closed_set(bad):
    with pytest.raises(ValueError):
        ac.rollup_verdicts(["PASS", bad])


# ───────────────────────── rollup_asset ─────────────────────────

def _m(v, measured="x"):
    return dict(v=v, measured=measured)


def test_gate_with_no_measurement_is_no_detector():
    """Null and Narr gained their checks in E6 packet (c): with nothing measured every registered check is an
    unmeasured NO_DETECTOR contribution, so the cell still reads NO_DETECTOR (a gate with no checks does too)."""
    cells = ac.rollup_asset("L2", {})
    assert set(cells) == set(ac.CELL_GATES)
    for g in ("Null", "Narr"):
        assert cells[g]["v"] == "NO_DETECTOR"
        assert {c["criterion"] for c in cells[g]["checks"]} == {c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == g}
        assert all(c["v"] == "NO_DETECTOR" for c in cells[g]["checks"])
    assert ac.rollup_verdicts([]) == "NO_DETECTOR"


def test_all_pass_measurements_do_not_make_a_gate_pass_while_an_applicable_check_is_unmeasured():
    # Build: every Build.* criterion measured PASS -> PASS
    ms = {c: _m("PASS") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "PASS"
    # drop one applicable check: it is NOT dropped from the gate, it reads NO_DETECTOR
    ms.pop("Build.dag")
    cell = ac.rollup_asset("L2", ms)["Build"]
    assert cell["v"] == "NO_DETECTOR"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.dag")
    assert chk["v"] == "NO_DETECTOR" and "not measured" in chk["reason"]


def test_worst_measured_verdict_wins_in_a_gate():
    ms = {c: _m("PASS") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    ms["Build.completion"] = _m("PARTIAL")
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "PARTIAL"
    ms["Build.history"] = _m("FAIL")
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "FAIL"
    ms["Build.contract"] = _m("ERRORED")
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "FAIL"


NW = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])      # the three facts an N-150 R5 no-writer release rests on


def test_measured_na_is_not_na_without_a_declared_rule_and_is_na_with_one(monkeypatch):
    ms = {c: _m("PASS") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    ms["Build.registered"] = dict(_m("N/A"), cause="no-writer-registry-agrees", no_writer=NW)    # E6 (a): N/A carries a cause (N-150 R5: and the three facts)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
    cell = ac.rollup_asset("L2", ms)["Build"]
    assert cell["v"] == "NO_DETECTOR"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.registered")
    assert chk["v"] == "NO_DETECTOR" and "N/A rule undecided" in chk["reason"]
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:no-writer-registry-agrees": "N-22/test"})
    cell = ac.rollup_asset("L2", ms)["Build"]
    assert cell["v"] == "PASS"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.registered")
    assert chk["v"] == "N/A" and chk["decision"] == "N-22/test"


def test_a_gate_is_na_only_when_every_check_is_na_by_declared_rule(monkeypatch):
    crits = [c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Idem"]
    ms = {c: dict(_m("N/A"), cause="no-writer-registry-agrees", no_writer=NW) for c in crits}
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
    assert ac.rollup_asset("L2", ms)["Idem"]["v"] == "NO_DETECTOR"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-writer-registry-agrees": "N-22/test" for c in crits})
    assert ac.rollup_asset("L2", ms)["Idem"]["v"] == "N/A"


def test_not_applicable_by_supplied_fact_needs_a_declared_rule(monkeypatch):
    ms = {"Ldgr.source_presence": None}
    ms = {}
    facts = {"columns": ["id"]}
    cell = ac.rollup_asset("L1", ms, facts)["Ldgr"]
    assert cell["v"] == "NO_DETECTOR"
    assert cell["checks"][0]["state"] == "NOT_APPLICABLE" and "N/A rule undecided" in cell["checks"][0]["reason"]
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Ldgr.source_presence#columns_any": "N-22/test"})
    assert ac.rollup_asset("L1", ms, facts)["Ldgr"]["v"] == "N/A"


def test_absent_facts_never_yield_na_even_with_a_declared_rule(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Ldgr.source_presence#columns_any": "N-22/test"})
    cell = ac.rollup_asset("L1", {}, None)["Ldgr"]
    assert cell["v"] == "NO_DETECTOR"
    assert cell["checks"][0]["state"] == "UNKNOWN"


def test_detector_none_criterion_never_reaches_pass():
    # Carr.D2 is detector NONE (D1 got a detector in revision 11, D3 under N-156); even if some caller hands it a PASS it is capped.
    ms = {"Carr.D1": _m("PASS"), "Carr.D2": _m("PASS"), "Carr.D3": _m("PASS")}
    cell = ac.rollup_asset("L2", ms)["Carr"]
    assert cell["v"] == "NO_DETECTOR"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Carr.D2")
    assert chk["v"] == "NO_DETECTOR" and "detector NONE" in chk["reason"]
    d3 = next(c for c in cell["checks"] if c["criterion"] == "Carr.D3")
    assert d3["v"] == "NO_DETECTOR" and "without re-derivation evidence" in d3["reason"]       # a detector, but a BARE PASS carries no re-derivation evidence
    d1 = next(c for c in cell["checks"] if c["criterion"] == "Carr.D1")
    # D1 has a detector, but a BARE {v: PASS} is not a D1 result: it carries no verified passage evidence, so it is not honoured
    assert d1["v"] == "NO_DETECTOR" and "without verified passage evidence" in d1["reason"] and "no `d1` evidence" in d1["reason"]


def test_measured_criterion_outside_its_layers_raises_never_dropped(monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Build.dag"] = dict(reg["Build.dag"], layers=("L0",))
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    with pytest.raises(ValueError):
        ac.rollup_asset("L2", {"Build.dag": _m("FAIL")})


def test_unregistered_or_ungradable_measurement_raises():
    with pytest.raises(KeyError):
        ac.rollup_asset("L2", {"Made.up": _m("PASS")})
    with pytest.raises(ValueError, match="Build.dag"):   # the error names the offending criterion
        ac.rollup_asset("L2", {"Build.dag": _m("NOT_GENERIC")})


def test_non_cell_gates_are_excluded_visibly_not_dropped():
    ms = {"Count.floor": _m("FAIL"), "Cost.baseline": _m("PASS")}
    out = ac.rollup_asset("L2", ms)
    assert set(out) == set(ac.CELL_GATES)
    ex = ac.rollup_excluded("L2", ms)
    assert ex == {"Count.floor": "FAIL", "Cost.baseline": "PASS"}


def test_unknown_layer_raises():
    with pytest.raises(KeyError):
        ac.rollup_asset("L9", {})


# ───────────────────────── versioning ─────────────────────────

def test_cells_carry_registry_revision_and_fingerprint():
    cells = ac.rollup_asset("L2", {})
    for g, c in cells.items():
        assert c["gate"] == g
        assert c["registry_revision"] == ac.REGISTRY_REVISION
        assert c["registry_fingerprint"] == ac.registry_fingerprint()


def test_fingerprint_is_stable_and_changes_with_any_content(monkeypatch):
    fp = ac.registry_fingerprint()
    assert fp == ac.registry_fingerprint() and len(fp) == 64
    reg = {k: dict(v) for k, v in ac.CRITERION_REGISTRY.items()}
    reg["Build.dag"]["layers"] = ("L0",)
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    assert ac.registry_fingerprint() != fp
    monkeypatch.undo()
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.dag#measured:x": "d"})
    assert ac.registry_fingerprint() != fp
    monkeypatch.undo()
    monkeypatch.setattr(ac, "CELL_GATES", ac.CELL_GATES[:-1])
    assert ac.registry_fingerprint() != fp


def test_revision_pin_content_cannot_change_without_a_bump():
    assert isinstance(ac.REGISTRY_REVISION, int) and ac.REGISTRY_REVISION >= 1
    assert ac.REGISTRY_REVISION in PINNED_FINGERPRINTS, "bump: add the new revision's fingerprint pin"
    assert ac.registry_fingerprint() == PINNED_FINGERPRINTS[ac.REGISTRY_REVISION], (
        "the registry content changed: bump REGISTRY_REVISION and pin the new fingerprint")


# ───────────────────────── 127-asset regression ─────────────────────────

def _census_layer(layer):
    return {"layer": layer, "assets": [dict(asset_id=a, layer=layer, measurements={k: dict(v=v, measured="") for k, v in ms.items()})
                       for a, ms in FIXTURE["layers"][layer].items()]}


def test_fixture_is_the_127_asset_2330_cell_census():
    # 2457 before E6 item i removed the 127 retired Carr.detector cells
    assert sum(len(v) for v in FIXTURE["layers"].values()) == 127
    assert sum(len(ms) for v in FIXTURE["layers"].values() for ms in v.values()) == 2330


def test_rollup_over_all_127_assets_is_total_versioned_and_never_better_than_the_worst_measured_check():
    rank = {v: i for i, v in enumerate(ac.ROLLUP_ORDER)}
    n = 0
    for layer in ALL_LAYERS:
        out = ac.rollup_census(_census_layer(layer))
        assert set(out) == set(FIXTURE["layers"][layer])
        for aid, cells in out.items():
            assert set(cells) == set(ac.CELL_GATES)
            n += 1
            for g, c in cells.items():
                assert c["registry_revision"] == ac.REGISTRY_REVISION
                # no facts were supplied and no N/A rule is declared: no cell may read N/A
                assert c["v"] != "N/A", (aid, g)
                worst = [ms_v for crit, ms_v in FIXTURE["layers"][layer][aid].items()
                         if ac.CRITERION_REGISTRY[crit]["gate"] == g and ms_v in rank]
                for v in worst:
                    assert rank[c["v"]] <= rank[v], (aid, g, c["v"], v)
                # a FAIL measured in the gate is a FAIL cell (worst wins)
                if "FAIL" in worst:
                    assert c["v"] == "FAIL", (aid, g)
                # the fixture holds no Null/Narr measurement: every such check is unmeasured, the cell NO_DETECTOR
                if g in ("Null", "Narr"):
                    assert c["v"] == "NO_DETECTOR"
    assert n == 127


def test_rollup_over_the_fixture_never_changes_an_input_measurement():
    for layer in ALL_LAYERS:
        census = _census_layer(layer)
        before = json.dumps(census, sort_keys=True)
        ac.rollup_census(census)
        assert json.dumps(census, sort_keys=True) == before


def test_existing_pure_functions_are_unchanged_on_every_measured_cell():
    """gap_id_for / lookup_criterion on all 2,330 cells: identity form and gate/check/detector/revision
    are exactly what the registry declared before E6.1."""
    for layer, assets in FIXTURE["layers"].items():
        for aid, ms in assets.items():
            for crit in ms:
                assert ac.gap_id_for(aid, crit) == f"{aid}-{crit}"
                gid, e = ac.lookup_criterion(aid, None, crit)
                assert gid == f"{aid}-{crit}" and crit == f"{e['gate']}.{e['check']}"
