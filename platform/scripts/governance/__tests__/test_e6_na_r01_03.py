"""test_e6_na_r01_03.py: REGISTRY_REVISION 9, SS ruling N-65 (from the N-22 / N-22a ruling table): the first three N/A rules are declared.

  R01  Build.history#measured:never-run                         (N-22 row 20, APPROVED)
  R02  Dens.served#measured:no-served-surface                   (N-22 row 19, AMENDED, after the Dens scanner repair)
  R03  Narr.{agree,checkable,fidelity_test,lint}#measured:no-prose   (N-22 row 17, AMENDED; assets with prose_fields [])

A rule turns an N/A into an N/A only when the measurement itself says N/A with that cause AND the id is declared; nothing here
widens a rule beyond the approved assets. Also: rollup_excluded applies the same release rule, so an undeclared N/A reads
NO_DETECTOR there too. Offline; the saved-census tests skip when the evidence directory is absent (CI)."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

pytestmark = pytest.mark.skip(reason="the E6.3 certificate reader was dropped by owner decision N-152; the module stays importable, its tests are not run in CI")

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

NARR = ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint")
N65_IDS = frozenset({
    "Build.history#measured:never-run",
    "Dens.served#measured:no-served-surface",
    *(f"{c}#measured:no-prose" for c in NARR),
})
PIN10_IDS = frozenset({"Build.dep_liveness#measured:no-declared-dependencies", "Earn.service_state#measured:not-a-service"})   # SS N-72
S2_IDS = frozenset(f"Carr.D{i}#measured:not-the-declared-carriage" for i in (1, 2, 3))              # SS N-72 S2, N-73
S3_IDS = frozenset({"Vocab.alias#measured:no-alias-class", "Ldgr.source_presence#measured:no-classical-claim"})   # SS N-72 S3, N-73 (1)/(4)
N151_IDS = frozenset({"Ldgr.source_presence#measured:no-data", "Ldgr.source_presence#measured:no-claims"})              # SS N-151 (REGISTRY_REVISION 26): N/A only by a checked declaration
N150_R1_IDS = frozenset({"Null.schema_default#measured:no-prose-declared", "Null.blank_rows#measured:no-prose-declared"})          # SS N-150 R1: released only through the checked prose_none block
N150_R2_IDS = frozenset({"Narr.lint#measured:lint-not-applicable"})                                                                  # SS N-150 R2: only with a declared lint_none AND the lint scan's agreement
N150_R5_IDS = frozenset({"Build.registered#measured:no-writer-registry-agrees", "Build.contract#measured:no-writer-registry-agrees",   # SS N-150 R5: only with a declared has_writer false AND the registry row
                         "Idem.pattern#measured:no-writer-registry-agrees", "Build.exercised#measured:never-run-no-writer",            # and the @register scan agreeing
                         "Build.exercised#measured:never-executed-no-writer"})
N150_IDS = N150_R1_IDS | N150_R2_IDS | N150_R5_IDS
N156_IDS = frozenset({"Carr.D1#measured:not-a-transcription", "Carr.D3#measured:single-derivation", "Carr.D1#measured:transcription-not-verified", "Carr.D2#measured:no-per-witness-values"})       # SS N-156 (the Carr declared ceiling)
SS_IDEM_UPDATE_ONLY_IDS = frozenset({"Idem.pattern#measured:update-only-by-intent"})      # SS 2026-10-05 Idem update-only: declaration-keyed, checked against the writer scan
SS_NO_TABLE_IDS = frozenset(f"{c}#measured:no-table-no-prose" for c in ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint", "Null.schema_default", "Null.blank_rows", "Vocab.identity"))      # SS 2026-10-05 no-table-no-prose
SS_BUILD_RECORD_IDS = frozenset({"Earn.build_record#measured:no-writer-registry-agrees"})      # SS 2026-10-05 build_record no-writer/static: declaration-keyed, checked against the registry row, the scan and the attempts
SS_R_IDS = frozenset({"Build.exercised#measured:legacy-attempts-no-writer", "Build.completion#measured:service-no-writer-no-count-sql", "Build.count_integrity#measured:service-no-writer-no-count-sql",
                      "Build.dep_liveness#measured:static-data-existence-only",
                      "Earn.build_record#measured:declared-probe-runs-verified"})      # SS 2026-10-05 R-c / R-d: declaration-keyed and checked (registry row, @register scan, attempts / migration)
N176_IDS = frozenset({"Vocab.alias#measured:no-vocabulary-values"})                 # SS N-176 (2026-10-07): Vocab.alias is value-keyed; N/A only on the checked bounded value reading
N270_IDS = frozenset({"Vocab.alias#measured:honest-null"})                      # SS N-270: every empty synonym set lifted by a declared, CHECKED vocab_alias_honest_null; N/A (nothing to check), never PASS
N177_IDS = frozenset({"Ldgr.source_presence#measured:unsourced-declared"})          # SS N-177 (2026-10-07): the closed-list residual UNSOURCED_DECLARED; declaration-keyed and checked
N211_IDS = frozenset({"Dens.served#measured:dens-not-served", "Dens.served#measured:dens-owned-by-sibling"})       # SS N-211 (E2 / E3 ii): Dens.served N/A for a declared dens_not_served, CHECKED against the capability scan and the registry
N235_IDS = frozenset(f"Carr.D{i}#measured:ratified_judgment" for i in (1, 2, 3))      # SS N-235 (2026-10-08): the ratified-judgment seeds read Carr.D1/D2/D3 N/A; declaration-keyed (nature ratified_judgment + ruling N-235) and checked
N283_IDS = frozenset(f"Carr.D{i}#measured:no-table-no-prose" for i in (1, 2, 3))      # SS N-283: a table-less service probe stores no value; declaration-keyed (no_table), checked
N430_IDS = frozenset({"Idem.pattern#measured:passive-projection", "Build.count_integrity#measured:passive-projection-constant-count"})      # SS N-430 (views): a declared passive_projection, CHECKED against the writer scan and the live catalog
N431_IDS = frozenset(f"{c}#measured:corpus-derived" for c in ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Null.schema_default", "Null.blank_rows"))      # SS N-431 (R1/R3, revision 28): a corpus_derived table, declaration-keyed and CHECKED by regeneration
DECLARED_IDS = N431_IDS | N430_IDS | N283_IDS | N235_IDS | N65_IDS | PIN10_IDS | S2_IDS | S3_IDS | N151_IDS | N150_IDS | N156_IDS | SS_BUILD_RECORD_IDS | SS_IDEM_UPDATE_ONLY_IDS | SS_NO_TABLE_IDS | SS_R_IDS | N176_IDS | N177_IDS | N211_IDS | N270_IDS     # the exact production table since REGISTRY_REVISION 26
R01_ASSETS = ("bg_gochara_citation_resolution", "bg_nakshatra_medical", "bg_sarvatobhadra_grid", "bg_sign_medical",
              "bg_transit_engine", "lel_events")
R02_ASSETS = ("bg_gochara_arcs", "bg_kota_chakra_rings", "bg_kp_sublord_division")
# REGISTRY_REVISION 14 (SS N-74(a)): the scan tells a SELECT from a LABEL; two more DATA assets are named only as labels in the serving modules (bg_cohort too, but a comment in the same module names it: it stays NO_DETECTOR, SS DENS L2).
# (bg_ephemeris_engine and bg_panchanga are named only by their service_probe envelope but are registry kind `service`: that is a reach, they stay NO_DETECTOR.)
R02_LABEL_ASSETS = ("bg_phaladeepika_latta", "bg_vedha_malefic_scale")
R02_ALL = R02_ASSETS + R02_LABEL_ASSETS
R03_ASSETS = ("bg_doshas", "bg_ontology", "bg_yogas", "bo_laksana_rerank")
# L0-WAVE batch 2 (test_e6_l0_batch2_declarations.py): two more assets declare prose_fields [] and read the four Narr checks N/A under R03 on the saved censuses
R03_BATCH2 = ("bg_transit_engine", "bg_kp_sublord_division")
NA, NO_DET = ac.NA, ac.NO_DET


def _na(cause):
    return dict(v=NA, measured="m", cause=cause)


# ───────────────────────── the declared set ─────────────────────────

def test_exactly_the_approved_rules_are_declared_and_they_validate():
    assert set(ac.NA_RULE_DECISIONS) == DECLARED_IDS
    ac.validate_na_rule_decisions()
    for rid, why in ac.NA_RULE_DECISIONS.items():
        assert re.fullmatch(r"[A-Za-z]+\.[A-Za-z0-9_]+#measured:[a-z0-9-]+", rid), rid          # cause-keyed, nothing else
        crit, _, cause = rid.partition("#measured:")
        assert cause in ac.NA_CAUSES[crit], rid
        if rid in SS_R_IDS:
            assert why.startswith(("SS 2026-10-05 R-", "SS 2026-10-05 probe_attempts")), (rid, why)
            continue
        if rid in N151_IDS | N150_IDS:
            assert ("N-151" if rid in N151_IDS else "N-150") in why, (rid, why)                                                 # the N-151 rules cite their own ruling
            continue
        if rid in N430_IDS:
            assert "N-430" in why, (rid, why)                                                                                    # SS N-430: cites its own ruling
            continue
        if rid in N431_IDS:
            assert "N-431" in why, (rid, why)                                                                                    # SS N-431: cites its own ruling
            continue
        if rid in N270_IDS:
            assert "N-270" in why, (rid, why)                                                                                    # SS N-270: cites its own ruling
            continue
        if rid in N176_IDS | N177_IDS:
            assert ("N-176" if rid in N176_IDS else "N-177") in why, (rid, why)                                                 # SS 2026-10-07: each cites its own ruling
            continue
        assert ("N-22" in why) or (rid in N156_IDS and "N-156" in why), (rid, why)                                                      # every rule cites its decisions
        assert ("N-65" if rid in N65_IDS else "N-156" if rid in N156_IDS else "N-72") in why, (rid, why)                      # ... and the ruling that approved it (per rule)


def test_no_rule_beyond_the_ruling_is_declared():
    ids = set(ac.NA_RULE_DECISIONS)
    assert not [i for i in ids if i.startswith(("Count.", "Complete.")) or (i.startswith("Idem.") and i not in N150_R5_IDS | N430_IDS)]
    assert {i for i in ids if i.startswith("Null.")} == N150_R1_IDS | {i for i in N431_IDS if i.startswith("Null.")}
    assert {i for i in ids if i.startswith("Narr.") and "lint-not-applicable" in i} == N150_R2_IDS
    assert {i for i in ids if i.startswith(("Vocab.", "Ldgr."))} == S3_IDS | N151_IDS | N176_IDS | N177_IDS | N270_IDS   # S3: the declaration-keyed words (+ the two N-151 checked-declaration words), never a column pattern
    assert not [i for i in ids if i.endswith(("#columns_any", "#asset_kinds"))]        # A5: no applicability-pattern N/A is declared anywhere
    assert not [i for i in ids if i.startswith("Carr.") and i not in S2_IDS | N156_IDS]            # no no-carriage / not-chosen / ratified_judgment rule
    assert not [i for i in ids if i.startswith("Earn.") and i != "Earn.service_state#measured:not-a-service"]    # Earn.build_record stays held
    assert not [i for i in ids if i.startswith("Build.") and i not in ("Build.history#measured:never-run",
                                                                      "Build.dep_liveness#measured:no-declared-dependencies") and i not in N150_R5_IDS | N430_IDS]
    assert not [i for i in ids if "user_data" in i or "write-nothing" in i or "rolling_horizon" in i or "no-carriage" in i]


def test_revision_is_at_least_9():
    assert ac.REGISTRY_REVISION >= 9


# ───────────────────────── positive: the declared rule releases exactly its own N/A ─────────────────────────

def test_R02_a_measured_dens_na_with_its_cause_reads_na_in_the_cell():
    cell = ac.rollup_asset("L0", {"Dens.served": _na("no-served-surface")})["Dens"]
    assert cell["v"] == NA and cell["checks"][0]["rule_id"] == "Dens.served#measured:no-served-surface"


def test_R03_all_four_narr_checks_na_need_a_checked_prose_none_block_to_make_the_narr_cell_na():
    full = {c: _na("no-prose") for c in NARR}
    assert ac.rollup_asset("L2", full)["Narr"]["v"] == NO_DET                                   # N-150 R1: a plain no-prose N/A with no checked block is no release (no grandfather)
    block = dict(checked=True, tables=["t"], open=[], contradicted=[], unread=[])
    checked = {c: dict(v, prose_none=dict(block)) for c, v in full.items()}
    assert ac.rollup_asset("L2", checked)["Narr"]["v"] == NA
    for missing in NARR:
        part = {c: v for c, v in checked.items() if c != missing}
        assert ac.rollup_asset("L2", part)["Narr"]["v"] == NO_DET, missing                      # absence is never N/A


def test_R01_a_never_run_history_check_reads_na_but_does_not_make_the_build_cell_na():
    cell = ac.rollup_asset("L0", {"Build.history": _na("never-run")})["Build"]
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.history")
    assert chk["v"] == NA and chk["rule_id"] == "Build.history#measured:never-run"
    assert cell["v"] == NO_DET                                                           # the other Build checks are unmeasured


def test_the_real_dens_scan_releases_the_three_approved_assets_with_the_serving_roots_only():
    for aid in R02_ASSETS:
        cap = ac.capability_scan(ac.CAPS_ROOTS, [aid], shared=frozenset(), columns={}, outside_roots=ac.DENS_OUTSIDE_ROOTS)
        g = ac._grade_dens(cap, aid)
        assert g["v"] == NA and g["cause"] == "no-served-surface", (aid, g)
        assert ac.rollup_asset("L0", {"Dens.served": g})["Dens"]["v"] == NA, aid


@pytest.mark.parametrize("aid", R03_ASSETS)
def test_the_real_writers_of_the_four_declared_no_prose_assets_emit_the_four_na_and_the_narr_cell_reads_na(aid):
    decl = ac.load_asset_declarations()
    assert decl[aid]["prose_fields"] == []
    L = {"bo_laksana_rerank": "L2"}.get(aid, "L0")
    reg = ac.registered_ids("")
    units, _ = ac._delegation_scope(aid, reg[aid])
    # the registry's own tables per asset (target table first, then every table its count_sql reads)
    tables = {"bg_doshas": ["brahma_dosha_catalog", "brahma_ontology", "reference_doshas"], "bg_ontology": ["brahma_ontology"],
              "bg_yogas": ["brahma_yoga_catalog", "brahma_ontology", "reference_yogas", "brahma_yoga_source_chunks"],
              "bo_laksana_rerank": ["bodha_msr_signals"]}[aid]
    ctx = dict(table=tables[0], own={}, tests=(), vocabulary=ac.prose_vocabulary(decl), counts=None,
               paths=[u["path"] for u in units], written=ac.written_columns(units, tables))
    ms = ac.prose_checks(aid, decl[aid], ctx)
    assert {c: ms[c]["v"] for c in NARR} == {c: NA for c in NARR}, ms
    assert all(ms[c]["cause"] == "no-prose" for c in NARR)
    assert ac.rollup_asset(L, ms, ac.declared_facts(decl, aid))["Narr"]["v"] == NA


# ───────────────────────── the reverse leg still FAILs a narration column (bg_yogas, bg_ontology are final at []) ─────────────────────────

@pytest.mark.parametrize("aid", R03_ASSETS)
def test_a_narration_column_in_the_writes_of_a_declared_no_prose_asset_reads_fail_never_na_even_with_the_rules_declared(aid):
    decl = ac.load_asset_declarations()
    vocab = ac.prose_vocabulary(decl)
    assert "citation_human" in vocab
    ctx = dict(table="t", own={}, tests=(), vocabulary=vocab, counts=None, paths=[], written={"t": {"id", "citation_human"}})
    ms = ac.prose_checks(aid, decl[aid], ctx)
    assert ms["Narr.agree"]["v"] == ac.FAIL and "citation_human" in ms["Narr.agree"]["measured"], ms["Narr.agree"]
    assert all(ms[c]["v"] == NO_DET for c in NARR[1:])
    cell = ac.rollup_asset("L0", ms)["Narr"]
    assert cell["v"] == ac.FAIL, cell                    # worst-of: the FAIL holds the cell; no N/A anywhere
    assert all(c["v"] != NA for c in cell["checks"])


@pytest.mark.parametrize("aid", ["bg_yogas", "bg_ontology"])
def test_bg_yogas_and_bg_ontology_stay_final_at_empty_prose_fields(aid):
    assert ac.load_asset_declarations()[aid]["prose_fields"] == []


# ───────────────────────── negative ─────────────────────────

@pytest.mark.parametrize("crit, cause, gate", [("Dens.served", "no-served-surface", "Dens"), ("Narr.agree", "no-prose", "Narr"),
                                               ("Build.history", "never-run", "Build")])
def test_cause_emitted_but_rule_not_declared_is_no_na(monkeypatch, crit, cause, gate):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
    cell = ac.rollup_asset("L2", {crit: _na(cause)})[gate]
    chk = next(c for c in cell["checks"] if c["criterion"] == crit)
    assert chk["v"] == NO_DET and "undecided" in chk["reason"]
    assert cell["v"] != NA


@pytest.mark.parametrize("crit, bad_v", [("Dens.served", ac.FAIL), ("Dens.served", ac.PARTIAL), ("Dens.served", ac.PASS),
                                         ("Build.history", ac.FAIL), ("Build.history", ac.PARTIAL), ("Narr.agree", ac.FAIL),
                                         ("Narr.lint", ac.PARTIAL)])
def test_rule_declared_but_condition_false_the_measured_verdict_stands(crit, bad_v):
    gate = crit.split(".")[0]
    cell = ac.rollup_asset("L2", {crit: dict(v=bad_v, measured="x")})[gate]
    chk = next(c for c in cell["checks"] if c["criterion"] == crit)
    assert chk["v"] == bad_v, chk                      # none of these criteria is detector NONE or capped: the verdict is as measured
    assert chk["v"] != NA and cell["v"] != NA


@pytest.mark.parametrize("crit, wrong", [("Dens.served", "no-module-references-target"), ("Dens.served", "no_served_surface"),
                                         ("Build.history", "never-run-no-writer"), ("Narr.agree", "no-prose-declared"),
                                         ("Build.history", None), ("Dens.served", "")])
def test_a_different_or_missing_cause_on_the_same_criterion_is_not_released(crit, wrong):
    rec = dict(v=NA, measured="m")
    if wrong is not None:
        rec["cause"] = wrong
    chk = next(c for c in ac.rollup_asset("L2", {crit: rec})[crit.split(".")[0]]["checks"] if c["criterion"] == crit)
    assert chk["v"] == NO_DET


def test_the_held_rules_are_not_released_even_though_their_causes_are_registered():
    """Null (N-22 row 33), Earn, Carr no-carriage stay NO_DETECTOR: causes exist, no rule is declared."""
    ms = {"Null.schema_default": _na("no-prose-declared"), "Null.blank_rows": _na("no-prose-declared"),
          "Earn.build_record": _na("healthy-non-execution"), **{f"Carr.D{i}": _na("no-carriage") for i in (1, 2, 3)}}
    cells = ac.rollup_asset("L2", ms)
    for g in ("Null", "Earn", "Carr"):
        assert cells[g]["v"] == NO_DET, g
    for chk in sum((cells[g]["checks"] for g in ("Null", "Earn", "Carr")), []):
        assert chk["v"] != NA


def test_count_floor_target_floor_zero_and_other_registered_causes_stay_unreleased():
    for crit, cause in (("Build.target", "service-no-target-table"), ("Build.exercised", "never-run-no-writer"),
                        ("Build.completion", "no-writer-no-count-sql")):
        chk = next(c for c in ac.rollup_asset("L0", {crit: _na(cause)})["Build"]["checks"] if c["criterion"] == crit)
        assert chk["v"] == NO_DET, crit


# ───────────────────────── rollup_excluded is rule-aware ─────────────────────────

def test_rollup_excluded_an_undeclared_na_reads_no_detector_not_na():
    ms = {"Count.floor": _na("target-floor-zero")}
    assert ac.rollup_excluded("L3", ms) == {"Count.floor": NO_DET}


def test_rollup_excluded_na_without_a_cause_or_with_an_unregistered_cause_reads_no_detector():
    assert ac.rollup_excluded("L3", {"Count.floor": dict(v=NA, measured="m")}) == {"Count.floor": NO_DET}
    assert ac.rollup_excluded("L3", {"Count.floor": _na("invented")}) == {"Count.floor": NO_DET}


def test_rollup_excluded_releases_a_declared_registered_cause_exactly_like_the_cells(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {**ac.NA_RULE_DECISIONS, "Count.floor#measured:target-floor-zero": "test"})
    assert ac.rollup_excluded("L3", {"Count.floor": _na("target-floor-zero")}) == {"Count.floor": NA}
    assert ac.rollup_excluded("L3", {"Count.floor": _na("other")}) == {"Count.floor": NO_DET}


def test_rollup_excluded_reports_every_other_verdict_as_measured_and_still_skips_the_nine_gates():
    ms = {"Count.floor": dict(v=ac.FAIL, measured="m"), "Complete.depth": dict(v=ac.PASS, measured="m"),
          "Complete.width": dict(v=ac.NOT_GENERIC, measured="m"), "Reach.fields": dict(v=NO_DET, measured="m"),
          "Build.history": _na("never-run")}
    assert ac.rollup_excluded("L3", ms) == {"Count.floor": ac.FAIL, "Complete.depth": ac.PASS, "Complete.width": ac.NOT_GENERIC,
                                            "Reach.fields": NO_DET}


def test_rollup_excluded_agrees_with_the_cell_rule_on_every_registered_na_cause(monkeypatch):
    """Same predicate as _check_contribution: for each (criterion, cause) pair the verdict an excluded criterion reads equals
    what _na_released says, whether or not a rule is declared."""
    pairs = [(c, k) for c, cs in ac.NA_CAUSES.items() if c in ac.CRITERION_REGISTRY and ac.CRITERION_REGISTRY[c]["gate"] not in ac.CELL_GATES
             for k in cs] + [("Count.floor", "x-unregistered")]
    for decl in ({}, {"Count.floor#measured:target-floor-zero": "t"}):
        monkeypatch.setattr(ac, "NA_RULE_DECISIONS", dict(decl))
        for crit, cause in pairs:
            rec = _na(cause)
            assert (ac.rollup_excluded("L3", {crit: rec})[crit] == NA) == ac._na_released(crit, rec), (crit, cause, decl)


# ───────────────────────── ledger: a released N/A closes the matching OPEN rows, nothing else ─────────────────────────

def _row(aid, crit, state="OPEN"):
    return dict(asset=aid, gap_id=f"{aid}-{crit}", kind="gap", criterion=crit, what="w", change="c",
                detector="asset_census.py", owner="asset_census", gate="g", state=state, ts="t0")


def _ledger(tmp_path, rows):
    (tmp_path / "asset_gaps.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _closed(tmp_path):
    rows = [json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return sorted(r["gap_id"] for r in rows if r["state"] == "CLOSED" and r["ts"] != "t0")


def _census(**by_asset):
    return dict(layer="L0", assets=[dict(asset_id=a, measurements=m) for a, m in by_asset.items()])


def test_emit_gaps_closes_the_open_rows_of_a_released_na_only(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    _ledger(tmp_path, [_row("bg_sign_medical", "Build.history"), _row("bg_gochara_arcs", "Dens.served"),
                       _row("bg_doshas", "Narr.agree"), _row("bg_other", "Build.history"),          # measured FAIL: stays open
                       _row("bg_nullrule", "Null.blank_rows"), _row("bg_floor", "Count.floor"),
                       _row("bg_sign_medical", "Build.exercised")])
    census = _census(bg_sign_medical={"Build.history": _na("never-run")}, bg_gochara_arcs={"Dens.served": _na("no-served-surface")},
                     bg_doshas={"Narr.agree": _na("no-prose")}, bg_other={"Build.history": dict(v=ac.FAIL, measured="m")},
                     bg_nullrule={"Null.blank_rows": _na("no-prose-declared")}, bg_floor={"Count.floor": _na("target-floor-zero")})
    ac.emit_gaps(census)
    assert _closed(tmp_path) == ["bg_doshas-Narr.agree", "bg_gochara_arcs-Dens.served", "bg_sign_medical-Build.history"]


def test_emit_gaps_closes_nothing_when_the_rules_are_not_declared(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
    _ledger(tmp_path, [_row("bg_sign_medical", "Build.history"), _row("bg_gochara_arcs", "Dens.served")])
    ac.emit_gaps(_census(bg_sign_medical={"Build.history": _na("never-run")}, bg_gochara_arcs={"Dens.served": _na("no-served-surface")}))
    assert _closed(tmp_path) == []


# ───────────────────────── the saved Track A censuses: exactly the listed gate cells move (seven at revision 9, twelve at 14), all NO_DETECTOR -> N/A ─────────────────────────

_DENS_FX = json.loads((HERE / "fixtures" / "dens_scan_inputs_2026-10-02.json").read_text(encoding="utf-8"))
KIND = {r["asset_id"]: r.get("asset_kind") for d in _DENS_FX["layers"].values() for r in d["assets"]}      # the registry kind (the saved Track A censuses predate it)
EV = pathlib.Path("/Users/Dev/suvarna-evidence")
_SAVED = {L: EV / ("census2" if L in ("L1", "L2") else "census") / f"census_{L}.json" for L in ac.LAYERS}
saved = pytest.mark.skipif(not all(p.exists() for p in _SAVED.values()), reason="saved Track A census JSONs not on this machine")


def _attributed(measurements):
    """The saved censuses predate `cause`: give a measured N/A the cause the current code emits for it (E6.1 cause table).
    Only Build.history's `never run` text is mapped here; every other N/A stays cause-less (so it reads NO_DETECTOR)."""
    m = copy.deepcopy(measurements)
    h = m.get("Build.history")
    if h and h["v"] == NA and str(h.get("measured", "")).startswith("never run"):
        h["cause"] = "never-run"
    return m


@saved
def test_saved_censuses_only_the_listed_gate_cells_move_and_all_of_them_no_detector_to_na(monkeypatch):
    decl = ac.load_asset_declarations()
    vocab = ac.prose_vocabulary(decl)
    reg = ac.registered_ids("")
    moved, released_checks, dens_na = [], [], []
    for L in ac.LAYERS:
        census = json.loads(_SAVED[L].read_text(encoding="utf-8"))[L]
        for a in census["assets"]:
            aid = a["asset_id"]
            m = _attributed(a["measurements"])
            m.pop("Carr.detector", None)
            tbl = a.get("target_table")
            toks = list(dict.fromkeys([t for t in ([tbl] if tbl else []) + list(a.get("count_sql_tables") or []) + [aid] if t]))
            cols = {tbl: list(a["reach"]["exposed"]) + list(a["reach"]["dark"])} if tbl and a.get("reach") else {}
            g = ac._grade_dens(ac.capability_scan(ac.CAPS_ROOTS, toks, shared=frozenset(), columns=cols,
                                                  outside_roots=ac.DENS_OUTSIDE_ROOTS, service=(KIND.get(aid) == "service")), tbl or aid)
            if g["v"] == NA:
                dens_na.append(aid)
            m["Dens.served"] = g
            if decl[aid]["prose_fields"] == []:
                units, _ = ac._delegation_scope(aid, reg[aid])
                ctx = dict(table=tbl, own={}, tests=(), vocabulary=vocab, counts=None, paths=[u["path"] for u in units],
                           written=ac.written_columns(units, [tbl] + list(a.get("count_sql_tables") or [])))
                m.update(ac.prose_checks(aid, decl[aid], ctx))
            facts = ac.facts_for_asset(a, decl)
            with_rules = ac.rollup_asset(L, m, facts)
            monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
            without = ac.rollup_asset(L, m, facts)
            monkeypatch.undo()
            for gate in ac.CELL_GATES:
                if with_rules[gate]["v"] != without[gate]["v"]:
                    moved.append((aid, gate, without[gate]["v"], with_rules[gate]["v"]))
                for c in with_rules[gate]["checks"]:
                    if c["v"] == NA and next(x for x in without[gate]["checks"] if x["criterion"] == c["criterion"])["v"] != NA:
                        released_checks.append((aid, c["criterion"], (m.get(c["criterion"]) or {}).get("v")))
    assert sorted(moved) == sorted([(a, "Dens", NO_DET, NA) for a in R02_ALL] + [(a, "Narr", NO_DET, NA) for a in R03_ASSETS + R03_BATCH2]), moved
    assert sorted(dens_na) == sorted(R02_ALL), dens_na                                                      # the scan fires on no other asset
    assert all(v == NA for (_, _, v) in released_checks), released_checks                                   # nothing measured FAIL/PARTIAL/PASS was released
    by = {}
    for aid, crit, _ in released_checks:
        by.setdefault(crit.split(".")[0], set()).add(aid)
    assert by == {"Build": set(R01_ASSETS), "Dens": set(R02_ALL), "Narr": set(R03_ASSETS + R03_BATCH2)}, by
    assert len(released_checks) == 6 + 5 + 16 + 8


# ───────────────────────── F1: an empty write scan is not evidence of "no narration write" ─────────────────────────

def test_F1_a_no_prose_asset_whose_dml_the_scan_cannot_see_reads_no_detector_never_na():
    assert ac.written_columns([], ["t"]) == {}                      # what the scan returns when it sees no INSERT/UPDATE at all
    ctx = dict(table="t", own={}, tests=(), vocabulary={"citation_human"}, counts=None, paths=[], written={})
    ms = ac.prose_checks("bg_yogas", {"prose_fields": []}, ctx)
    assert all(r["v"] == NO_DET for r in ms.values()), ms
    cells = ac.rollup_asset("L0", ms)
    assert cells["Narr"]["v"] == NO_DET and cells["Null"]["v"] == NO_DET
    assert all(c["v"] != NA for g in ("Narr", "Null") for c in cells[g]["checks"])
    # unreadable (None) reads the same, and a readable write set that holds no narration column is still the N/A candidate
    assert all(r["v"] == NO_DET for r in ac.prose_checks("bg_yogas", {"prose_fields": []}, dict(ctx, written=None)).values())
    assert ac.prose_checks("bg_yogas", {"prose_fields": []}, dict(ctx, written={"t": {"id"}}))["Narr.agree"]["v"] == NA


# ───────────────────────── F3: the exact Dens N/A set, always on (no saved-census directory needed) ─────────────────────────

def test_F3_the_real_dens_scan_reads_na_on_exactly_the_approved_assets_over_all_127(monkeypatch):
    """The inputs of the 127 assets' scans are a committed fixture (verdict-free); the scan is the REAL one over the current
    source tree. A sixth N/A (a new unreferenced table, a served read removed, a new label-only mention) fails here and needs a
    ruling, not a widening; a served read added to one of the five also fails here (the rule no longer fits it). The five are
    the three that no served module references at all (N-65) plus the two DATA assets a serving module only NAMES as a label (SS N-74(a),
    REGISTRY_REVISION 14: bg_phaladeepika_latta, bg_vedha_malefic_scale; bg_cohort is label-only too but a comment in the same module blocks it). The two service-kind assets named only by their
    service_probe envelope (bg_ephemeris_engine, bg_panchanga) are a reach and stay NO_DETECTOR.
    File reads are cached for speed."""
    fx = json.loads((HERE / "fixtures" / "dens_scan_inputs_2026-10-02.json").read_text(encoding="utf-8"))
    real, cache = pathlib.Path.read_text, {}

    def cached(self, *a, **k):
        key = (str(self), a, tuple(sorted(k.items())))
        if key not in cache:
            cache[key] = real(self, *a, **k)
        return cache[key]
    monkeypatch.setattr(pathlib.Path, "read_text", cached)
    na, n = [], 0
    for L, d in fx["layers"].items():
        for r in d["assets"]:
            n += 1
            g = ac._grade_dens(ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"],
                                                  outside_roots=ac.DENS_OUTSIDE_ROOTS, service=(r.get("asset_kind") == "service")),
                               r["target_table"] or r["asset_id"])
            if g["v"] == NA:
                assert g["cause"] == "no-served-surface", (r["asset_id"], g)
                na.append(r["asset_id"])
    assert n == 127
    assert sorted(na) == sorted(R02_ALL), na


# ───────────────────────── F5: `never-run` needs the build-history source demonstrably present ─────────────────────────

import test_e6_a_na_causes as na_causes  # noqa: E402


def _measure_history(monkeypatch, tmp_path, reg, hist):
    ms = na_causes._m(monkeypatch, tmp_path, reg, hist=hist)
    return {a: m["Build.history"] for a, m in ms.items()}


def test_F5_a_wiped_or_absent_history_yields_no_na_and_closes_no_ledger_row(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x"), "y": na_causes._reg_row("y")}
    got = _measure_history(monkeypatch, tmp_path, reg, {})                  # build_run_assets empty for the whole census scope
    for aid, rec in got.items():
        assert rec["v"] == NO_DET and rec.get("cause") is None and "absent" in rec["measured"], (aid, rec)
        assert ac.rollup_asset("L0", {"Build.history": rec})["Build"]["checks"][-1]["v"] != NA
    # and it closes nothing: an OPEN Build.history row stays OPEN when the history is wiped
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    (tmp_path / "asset_gaps.jsonl").write_text(json.dumps(_row("x", "Build.history", "OPEN")) + "\n", encoding="utf-8")
    ac.emit_gaps(_census(x={"Build.history": got["x"]}))
    assert _closed(tmp_path) == []


def test_F5_one_asset_with_no_row_among_assets_that_do_have_rows_still_reads_never_run(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x"), "y": na_causes._reg_row("y")}
    got = _measure_history(monkeypatch, tmp_path, reg, {"y": na_causes._h_unstarted()})
    assert got["x"]["v"] == NA and got["x"]["cause"] == "never-run"
    assert got["y"]["v"] != NA
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    (tmp_path / "asset_gaps.jsonl").write_text(json.dumps(_row("x", "Build.history", "OPEN")) + "\n", encoding="utf-8")
    ac.emit_gaps(_census(x={"Build.history": got["x"]}))
    assert _closed(tmp_path) == ["x-Build.history"]
