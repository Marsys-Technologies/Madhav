"""E6.3 -- ELEVATED, exact (plan 1.1; Track E brief 8): the four conditions, each failing independently, terminal
dispositions, and the certificate-currency rules, against throw-away git repos (no database, no working tree).

Every test builds the default world (ga_alpha fully certified, bg_beta with one declared addition, ka_gamma terminally
retired), changes ONE thing, commits, and asserts the exact set `elevated_assets` returns. A test that only
asserted the positive case would pass a function that returns everything; each negative case therefore names the
asset it removes and asserts the others are untouched.
"""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _e6_3_fixtures import (MINI_CENSUS, MINI_FLOOR, mini_patch, NA_NULL, World, cert, disp, gap, inval,  # noqa: E402
                            load_tracker)

T = load_tracker()
REAL_FLOOR = dict(T.E63_REQUIRED_FLOOR)
REAL_PINS = dict(T.E63_REQUIRED_CRITERIA)
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def mini_floor(monkeypatch):
    """The mini registry has fewer criteria than the real one: pin the floor it satisfies (real-registry tests ask
    for `real_floor` instead)."""
    mini_patch(monkeypatch, T)


@pytest.fixture
def real_floor(monkeypatch):
    monkeypatch.setattr(T, "E63_REQUIRED_FLOOR", REAL_FLOOR)
    monkeypatch.setattr(T, "E63_REQUIRED_CRITERIA", REAL_PINS)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def got(w):
    w.commit()
    return w.elevated(T)


def test_baseline_all_four_conditions_met_and_a_terminal_asset(w):
    assert got(w) == ALL


def test_a_world_with_nothing_elevated_returns_the_empty_set_not_an_error(tmp_path):
    w = World(tmp_path)
    w.asset("ga_alpha", disposition="unresolved")
    assert got(w) == set()


# ───────────────────────── condition 1: every required core-gate criterion certified ─────────────────────────

@pytest.mark.parametrize("crit", ["Ldgr.src", "Idem.pat", "Idem.alt", "Null.x", "Build.any", "Build.target", "Build.reg"])
def test_c1_a_missing_certificate_for_any_required_criterion_drops_only_that_asset(w, crit):
    w.drop("ga_alpha", crit)
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_build_reg_is_not_required_of_an_l0_asset_because_its_layers_exclude_L0(w):
    # bg_beta has no Build.reg certificate and is still elevated: the requirement comes from the registry's layers
    assert not any(c["asset"] == "bg_beta" and c["criterion"] == "Build.reg" for c in w.certs)
    assert "bg_beta" in got(w)


@pytest.mark.parametrize("verdict", ["FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED"])
def test_c1_only_PASS_or_a_computed_NA_counts(w, verdict):
    w.find("ga_alpha", "Idem.pat").update(verdict=verdict, semantic_fingerprint=None)
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_a_later_generation_that_FAILs_replaces_the_earlier_PASS(w):
    w.certs.append(cert("ga_alpha", "Idem.pat", "FAIL", gen=2))
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_an_NA_whose_rule_is_not_declared_in_the_registry_is_not_satisfied(w):
    w.find("ga_alpha", "Null.x").update(na=dict(NA_NULL, rule_id="Null.x#asset_kinds"))
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_an_NA_with_the_wrong_decision_id_is_not_satisfied(w):
    w.find("ga_alpha", "Null.x").update(na=dict(NA_NULL, decision_id="N-99"))
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_a_typed_NA_with_no_na_block_is_not_satisfied(w):
    w.find("ga_alpha", "Null.x").update(na=None)
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_an_NA_of_another_criterion_does_not_borrow_a_rule(w):
    w.find("ga_alpha", "Idem.alt").update(verdict="N/A", na=dict(NA_NULL), citation_state=None,      # rule belongs to Null.x
                                                     citation_state_caveat=False)       # (an N/A carries no state)
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_a_PASS_on_a_capped_Null_criterion_is_not_a_PASS(w):
    w.find("ga_alpha", "Null.x").update(verdict="PASS", na=None)               # the rollup caps Null.* at PARTIAL
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_a_PASS_with_detector_NONE_is_not_a_PASS(w):
    w.find("ga_alpha", "Idem.pat").update(detector="NONE")
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_a_PASS_on_a_criterion_whose_registry_detector_is_NONE_is_not_a_PASS(tmp_path):
    census = MINI_CENSUS.replace('"Idem.alt":  dict(gate="Idem",  check="alt",  detector="census"',
                                 '"Idem.alt":  dict(gate="Idem",  check="alt",  detector="NONE"')
    assert census != MINI_CENSUS
    w = World(tmp_path, census=census).default()
    assert got(w) == {"ka_gamma"}


def test_c1_an_inconclusive_PASS_is_not_a_PASS(w):
    w.find("ga_alpha", "Idem.pat")["inconclusive"] = True
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_an_unrecognised_basis_is_never_honoured(w):
    w.find("ga_alpha", "Build.target")["basis"] = "Declaration"           # case-exact
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_basis_declaration_is_honoured_only_where_the_registry_defines_it(w):
    # Build.target on a SERVICE asset: a PASS by declaration. Anywhere else a declaration is not a PASS.
    w.find("ga_alpha", "Build.target")["basis"] = "declaration"
    assert got(w) == ALL - {"ga_alpha"}                       # ga_alpha is a data asset in the registry
    w.seed_extra = {"ga_alpha": "service"}
    assert got(w) == ALL                                       # now a declared service
    w.find("ga_alpha", "Idem.pat")["basis"] = "declaration"   # Idem.pat has no declaration basis, service or not
    assert got(w) == ALL - {"ga_alpha"}


def test_c1_a_declaration_basis_on_an_addition_is_not_honoured(w):
    w.find("bg_beta", "D-GROUNDING", "addition")["basis"] = "declaration"
    assert got(w) == ALL - {"bg_beta"}


def test_c1_a_criterion_outside_the_core_gates_is_not_required(w):
    assert not any(c["criterion"] in ("Cost.base", "Reach.f") for c in w.certs)
    assert got(w) == ALL


# ───────────────────────── condition 2: every declared addition certified ─────────────────────────

def test_c2_a_declared_addition_with_no_certificate_blocks_only_its_asset(w):
    w.drop("bg_beta", "D-GROUNDING", kind="addition")
    assert got(w) == ALL - {"bg_beta"}


@pytest.mark.parametrize("verdict", ["FAIL", "PARTIAL", "NO_DETECTOR", "N/A"])
def test_c2_an_addition_needs_a_PASS_there_is_no_registry_rule_for_its_NA(w, verdict):
    w.find("bg_beta", "D-GROUNDING", "addition").update(verdict=verdict, na=dict(NA_NULL))
    assert got(w) == ALL - {"bg_beta"}


def test_c2_an_addition_cannot_be_NA_even_if_a_rule_id_for_it_were_declared(tmp_path):
    census = MINI_CENSUS.replace('"Null.x#columns_any": "N-22a"', '"Null.x#columns_any": "N-22a", "D-GROUNDING#columns_any": "N-22b"')
    assert census != MINI_CENSUS
    w = World(tmp_path, census=census).default()
    w.find("bg_beta", "D-GROUNDING", "addition").update(
        verdict="N/A", na=dict(rule_id="D-GROUNDING#columns_any", decision_id="N-22b"))
    assert got(w) == ALL - {"bg_beta"}


def test_c2_an_addition_certificate_that_nobody_declared_is_ignored(w):
    w.certs.append(cert("ga_alpha", "D-TIME", kind="addition", verdict="FAIL"))
    assert got(w) == ALL


def test_c2_a_declaration_added_later_with_no_certificate_blocks(w):
    w.disps.append(disp("ga_alpha", "keep", additions=["D-TIME"]))
    assert got(w) == ALL - {"ga_alpha"}


# ───────────────────────── condition 3: no open gap on a core gate or a declared addition ─────────────────────────

@pytest.mark.parametrize("state", ["OPEN", "IN_PROGRESS"])
def test_c3_an_open_gap_on_a_core_gate_blocks(w, state):
    w.gaps.append(gap("ga_alpha", "Idem.pat", state=state))
    assert got(w) == ALL - {"ga_alpha"}


def test_c3_an_open_gap_on_a_gate_with_a_sub_criterion_blocks(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat.deeper"))
    assert got(w) == ALL - {"ga_alpha"}


def test_c3_an_open_gap_on_a_declared_addition_blocks(w):
    w.gaps.append(gap("bg_beta", "D-GROUNDING"))
    assert got(w) == ALL - {"bg_beta"}


def test_c3_a_row_with_no_kind_reads_as_a_gap(w):
    row = gap("ga_alpha", "Idem.pat")
    del row["kind"]
    w.gaps.append(row)
    assert got(w) == ALL - {"ga_alpha"}


def test_c3_opportunity_rows_never_block_even_on_a_core_gate_or_an_addition(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", kind="opportunity"))
    w.gaps.append(gap("bg_beta", "D-GROUNDING", kind="opportunity", gap_id="bg_beta-x"))
    assert got(w) == ALL


def test_c3_info_rows_never_block(w):
    w.gaps.append(gap("ga_alpha", "Cost.base", kind="info"))
    w.gaps.append(gap("ga_alpha", "Reach.fields", kind="info", gap_id="ga_alpha-r"))
    assert got(w) == ALL


def test_c3_an_open_gap_row_on_a_non_gate_criterion_family_does_not_block(w):
    w.gaps.append(gap("ga_alpha", "Cost.base"))
    w.gaps.append(gap("ga_alpha", "Reach.fields", gap_id="ga_alpha-r"))
    assert got(w) == ALL


def test_c3_an_open_gap_row_nobody_can_classify_blocks(w):
    w.gaps.append(gap("ga_alpha", "Architecture.layering"))
    assert got(w) == ALL - {"ga_alpha"}
    w.gaps[-1]["criterion"] = ""
    assert got(w) == ALL - {"ga_alpha"}


@pytest.mark.parametrize("closing", ["CLOSED", "WITHDRAWN"])
def test_c3_a_later_row_for_the_same_gap_id_closes_it(w, closing):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="g1"))
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="g1", state=closing))
    assert got(w) == ALL


def test_c3_a_regression_row_after_a_closure_reopens_it(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="g1", state="CLOSED"))
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="g1", state="OPEN"))
    assert got(w) == ALL - {"ga_alpha"}


def test_c3_an_open_row_folded_into_a_closed_gap_is_refused_not_silently_resolved(w):
    # (final delta review) the open state of a gap must not vanish by folding it into a closed row
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="old", superseded_by="new"))
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="new", state="CLOSED"))
    w.commit()
    with pytest.raises(T.ElevatedInputError):
        w.elevated(T)


def test_c3_a_closed_row_folded_into_a_closed_gap_is_fine(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="old", superseded_by="new", state="CLOSED"))
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="new", state="CLOSED"))
    assert got(w) == ALL


def test_c3_a_row_folded_into_an_open_gap_still_blocks_through_the_target(w):
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="old", superseded_by="new"))
    w.gaps.append(gap("ga_alpha", "Idem.pat", gap_id="new"))
    assert got(w) == ALL - {"ga_alpha"}


def test_c3_a_gap_on_another_asset_does_not_block(w):
    w.seed_extra = {"ka_other": "data"}
    w.gaps.append(gap("ka_other", "Idem.pat"))
    assert got(w) == ALL


# ───────────────────────── condition 4: a disposition is recorded ─────────────────────────

def test_c4_no_recorded_disposition_blocks(w):
    w.disps = [d for d in w.disps if d["asset"] != "ga_alpha"]
    assert got(w) == ALL - {"ga_alpha"}


def test_c4_an_unresolved_disposition_is_not_a_recorded_one(w):
    w.disps.append(disp("ga_alpha", "unresolved"))
    assert got(w) == ALL - {"ga_alpha"}


@pytest.mark.parametrize("d", ["keep", "integrate", "enrich", "qualify", "historical"])
def test_c4_any_resolved_non_terminal_disposition_satisfies(w, d):
    w.disps.append(disp("ga_alpha", d, additions=[]))
    assert got(w) == ALL


def test_c4_the_latest_disposition_row_governs(w):
    w.disps.append(disp("ga_alpha", "unresolved"))
    w.disps.append(disp("ga_alpha", "enrich"))
    assert got(w) == ALL


# ───────────────────────── terminal dispositions ─────────────────────────

@pytest.mark.parametrize("d", ["retire", "consolidate"])
def test_terminal_retire_or_consolidate_with_a_reason_is_honoured_without_certificates(w, d):
    w.disps.append(disp("ka_delta", d, reason="folded into ka_gamma"))
    assert got(w) == ALL | {"ka_delta"}


def test_terminal_is_honoured_even_with_failing_certs_and_open_gaps(w):
    w.certs.append(cert("ka_gamma", "Idem.pat", "FAIL"))
    w.gaps.append(gap("ka_gamma", "Idem.pat"))
    assert "ka_gamma" in got(w)


@pytest.mark.parametrize("reason", ["", "   "])
def test_a_retire_with_no_reason_is_not_terminal(w, reason):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason=reason)]
    assert got(w) == ALL - {"ka_gamma"}


@pytest.mark.parametrize("d", ["keep", "historical", "unresolved", "qualify"])
def test_other_dispositions_are_not_terminal(w, d):
    w.disps = [x for x in w.disps if x["asset"] != "ka_gamma"] + [disp("ka_gamma", d, reason="because")]
    assert "ka_gamma" not in got(w)


def test_a_terminal_row_superseded_by_a_later_non_terminal_row_is_no_longer_terminal(w):
    w.disps.append(disp("ka_gamma", "keep"))
    assert "ka_gamma" not in got(w)


# ───────────────────────── currency: a stale certificate is not current ─────────────────────────

def test_stale_writer_file_changed_since_certification(w):
    w.writer_versions["ga_alpha"] = 2
    assert got(w) == ALL - {"ga_alpha"}


def test_stale_writer_file_absent_at_the_ref_is_stale_not_an_error(w):
    w.find("ga_alpha", "Idem.pat")["writer_hashes"] = {"platform/python-sidecar/gone.py": "e" * 64}
    assert got(w) == ALL - {"ga_alpha"}


def test_stale_a_newer_generation_must_itself_be_current(w):
    # generation 2 carries no writer hashes and no stated reason for having none: it could never go stale
    w.certs.append(cert("ga_alpha", "Idem.pat", gen=2, writer=False, writer_hashes_reason=None))
    assert got(w) == ALL - {"ga_alpha"}


def test_stale_an_earlier_generation_is_not_current_once_a_newer_one_exists(w):
    w.certs.append(cert("ga_alpha", "Idem.pat", gen=2))
    sha = w.commit()
    facts = T._e63_registry_facts(str(w.repo), sha)
    led = T._e63_parse_certs(T._e63_show(str(w.repo), sha, "00_ARCHITECTURE/control/asset_certs.jsonl"), facts)
    by_key = led.by_key
    state = T.LedgerState(str(w.repo), sha, facts, by_key, {}, led.pos)
    ok1, why1 = T.certificate_currency(by_key["ga_alpha|gate|Idem.pat"][0], state)
    ok2, _ = T.certificate_currency(by_key["ga_alpha|gate|Idem.pat"][1], state)
    assert (ok1, ok2) == (False, True) and "not the latest" in why1


def test_stale_an_invalidation_row_for_the_current_generation(w):
    w.invals.append(inval("ga_alpha|gate|Idem.pat@1"))
    assert got(w) == ALL - {"ga_alpha"}


def test_an_invalidation_of_an_old_generation_does_not_touch_the_current_one(w):
    w.certs.append(cert("ga_alpha", "Idem.pat", gen=2))
    w.invals.append(inval("ga_alpha|gate|Idem.pat@1"))
    assert got(w) == ALL


def test_stale_a_pass_with_no_semantic_fingerprint_could_never_go_stale_so_it_is_not_current(w):
    w.find("ga_alpha", "Idem.pat")["semantic_fingerprint"] = None
    assert got(w) == ALL - {"ga_alpha"}


def test_stale_the_criterion_revision_moved(w):
    w.find("ga_alpha", "Idem.pat")["criterion_version"] = 1         # the registry is at revision 2
    assert got(w) == ALL - {"ga_alpha"}


def later(w, asset, crit):
    """Re-certify `asset`/`crit` AFTER everything else (a dependant is certified after what it cites)."""
    rec = w.find(asset, crit)
    w.certs.remove(rec)
    w.certs.append(rec)


def test_stale_upstream_has_a_newer_generation(w):
    w.certs.append(cert("ga_alpha", "Ldgr.src", gen=2, fp="c" * 64))
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Ldgr.src@1"]
    later(w, "ga_alpha", "Idem.pat")
    assert got(w) == ALL - {"ga_alpha"}


def test_a_generation_bump_with_the_same_output_invalidates_nothing_downstream(w):
    # E5.5: E5.1 mints generation 2 when any currency field changes; identical semantic output leaves dependants current
    w.certs.append(cert("ga_alpha", "Ldgr.src", gen=2))                                  # same semantic_fingerprint (FP)
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Ldgr.src@1"]
    later(w, "ga_alpha", "Idem.pat")
    assert got(w) == ALL


def test_a_generation_bump_with_different_output_does_invalidate_downstream(w):
    w.certs.append(cert("ga_alpha", "Ldgr.src", gen=2, fp="b" * 64))
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Ldgr.src@1"]
    later(w, "ga_alpha", "Idem.pat")
    assert got(w) == ALL - {"ga_alpha"}


def test_a_same_output_bump_still_needs_the_latest_upstream_generation_to_be_current_and_passing(w):
    w.certs.append(cert("ga_alpha", "Ldgr.src", gen=2, writer=False, writer_hashes_reason=None))   # latest not current
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Ldgr.src@1"]
    later(w, "ga_alpha", "Idem.pat")
    assert got(w) == ALL - {"ga_alpha"}


def test_current_upstream_at_its_latest_generation_keeps_the_dependant_current(w):
    w.certs.append(cert("ga_alpha", "Ldgr.src", gen=2))
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["ga_alpha|gate|Ldgr.src@2"]
    later(w, "ga_alpha", "Idem.pat")
    assert got(w) == ALL


def test_stale_upstream_is_itself_invalidated(w):
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["bg_beta|gate|Ldgr.src@1"]
    later(w, "ga_alpha", "Idem.pat")
    w.invals.append(inval("bg_beta|gate|Ldgr.src@1", code="writer_hash"))
    assert got(w) == ALL - {"ga_alpha", "bg_beta"}      # both: bg_beta's own cert is invalidated, ga_alpha rests on it


def test_stale_upstream_that_no_longer_passes(w):
    w.certs.append(cert("bg_beta", "Ldgr.src", "FAIL", gen=2))
    w.find("ga_alpha", "Idem.pat")["upstream_cert_ids"] = ["bg_beta|gate|Ldgr.src@2"]
    later(w, "ga_alpha", "Idem.pat")
    assert got(w) == ALL - {"ga_alpha", "bg_beta"}


def test_a_stale_addition_certificate_blocks(w):
    w.writer_versions["bg_beta"] = 2
    assert got(w) == ALL - {"bg_beta"}


def test_stale_never_hides_a_terminal_asset(w):
    w.writer_versions["ka_gamma"] = 2
    assert "ka_gamma" in got(w)


# ───────────────────────── parity with the census rollup on the REAL registry ─────────────────────────

def _real_census_module():
    import importlib.util
    path = __import__("pathlib").Path(__file__).resolve().parents[1] / "asset_census.py"
    spec = importlib.util.spec_from_file_location("asset_census_for_e6_3", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["asset_census_for_e6_3"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_registry_facts_read_as_source_equal_the_imported_registry(tmp_path, real_floor):
    import pathlib
    ac = _real_census_module()
    w = World(tmp_path, census=(pathlib.Path(ac.__file__)).read_text(encoding="utf-8"))
    w.default()
    sha = w.commit()
    facts = T._e63_registry_facts(str(w.repo), sha)
    assert facts.cell_gates == tuple(ac.CELL_GATES)
    assert facts.na_rules == dict(ac.NA_RULE_DECISIONS)
    assert facts.layer_prefix == {k: v["prefix"] for k, v in ac.LAYERS.items()}
    assert set(facts.criteria) == set(ac.CRITERION_REGISTRY)
    for k, e in ac.CRITERION_REGISTRY.items():
        got_e = facts.criteria[k]
        assert (got_e["gate"], got_e["layers"], got_e["detector"], got_e["revision"]) == \
               (e["gate"], tuple(e["layers"]), e["detector"], e["revision"]), k


@pytest.mark.parametrize("layer,asset", [("L0", "bg_x"), ("L1", "ga_x"), ("L2", "bo_x"), ("L3", "ka_x"),
                                        ("L4", "ph_x"), ("L5", "mi_x")])
def test_real_registry_all_PASS_is_never_elevated_exactly_when_the_rollup_says_not_all_gates_pass(tmp_path, layer, asset, real_floor):
    """With every required criterion certified PASS on the real registry: the rollup caps Null.*/Narr.fidelity_test
    at PARTIAL and reads detector-NONE criteria NO_DETECTOR, so some gate cell is not PASS -- and the exact function
    must agree (an agreeing detector, not a hard-coded False: the second half flips both to elevated)."""
    import pathlib
    ac = _real_census_module()
    facts_req = {c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] in ac.CELL_GATES and layer in e["layers"]}
    rollup = ac.rollup_asset(layer, {c: {"v": "PASS"} for c in facts_req})
    all_gates_pass = all(cell["v"] in ("PASS", "N/A") for cell in rollup.values())
    w = World(tmp_path, census=(pathlib.Path(ac.__file__)).read_text(encoding="utf-8"))
    for c in sorted(facts_req):
        e = ac.CRITERION_REGISTRY[c]
        w.certs.append(cert(asset, c, "PASS", detector=e["detector"], layer=layer, revision=e["revision"],
                            gate=e["gate"]))
    w.disps.append(disp(asset, "keep"))
    w.commit()
    assert (asset in w.elevated(T)) == all_gates_pass
    assert all_gates_pass is False


def test_real_registry_an_asset_with_every_non_capped_non_NONE_criterion_PASS_and_the_rest_computed_NA(tmp_path, real_floor):
    """The exact function agrees with the rollup when the capped/NONE criteria are released by DECLARED N/A rules."""
    import pathlib
    ac = _real_census_module()
    layer, asset = "L1", "ga_x"
    req = {c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] in ac.CELL_GATES and layer in e["layers"]}
    blocked = {c for c in req if c.startswith("Null.") or c == "Narr.fidelity_test" or ac.CRITERION_REGISTRY[c]["detector"] == "NONE"}
    assert blocked, "the real registry has capped/NONE criteria today"
    src = (pathlib.Path(ac.__file__)).read_text(encoding="utf-8")
    rules = {f"{c}#measured:x-cause": "N-test" for c in blocked}
    src = src.replace("NA_RULE_DECISIONS: dict[str, str] = {}", f"NA_RULE_DECISIONS: dict[str, str] = {rules!r}")
    assert src != (pathlib.Path(ac.__file__)).read_text(encoding="utf-8")
    w = World(tmp_path, census=src)
    for c in sorted(req):
        e = ac.CRITERION_REGISTRY[c]
        if c in blocked:
            w.certs.append(cert(asset, c, "N/A", detector=e["detector"], layer=layer, revision=e["revision"], gate=e["gate"],
                                na=dict(rule_id=f"{c}#measured:x-cause", decision_id="N-test", basis="measured_cause",
                                        cause="x-cause", facts=None)))
        else:
            w.certs.append(cert(asset, c, "PASS", detector=e["detector"], layer=layer, revision=e["revision"], gate=e["gate"]))
    w.disps.append(disp(asset, "keep"))
    w.commit()
    assert asset in w.elevated(T)
    # and the rollup, given the same facts (each blocked criterion a measured N/A under a declared rule), agrees
    saved_causes = dict(ac.NA_CAUSES)
    ac.NA_RULE_DECISIONS.update(rules)
    try:
        for c in blocked:
            ac.NA_CAUSES[c] = tuple(ac.NA_CAUSES.get(c, ())) + ("x-cause",)
        meas = {c: ({"v": "N/A", "cause": "x-cause"} if c in blocked else {"v": "PASS"}) for c in req}
        cells = ac.rollup_asset(layer, meas)
        assert all(cell["v"] in ("PASS", "N/A") for cell in cells.values())
    finally:
        for r in rules:
            ac.NA_RULE_DECISIONS.pop(r, None)
        ac.NA_CAUSES.clear()
        ac.NA_CAUSES.update(saved_causes)
