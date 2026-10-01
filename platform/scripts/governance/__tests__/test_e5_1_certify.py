"""test_e5_1_certify.py — Suvarna E5.1: the certification-record writer (`nikasha_certify.py`).

A certification record is what ELEVATED rests on (plan 1.1; arch 12.16), so this writer's job is mostly to REFUSE.
Refusal list, each with its own tests below:
  R1  a PASS whose criterion has `detector: NONE` (and any non-NO_DETECTOR verdict under a NONE detector);
  R2  any record with no census run id in its evidence (PASS included; a naive or non-ISO id counts as none);
  R3  an N/A the registry did not compute (typed, undeclared rule id, wrong rule id, applicable, unknown facts,
      an addition, a measured cause with no census record behind it);
  R4  a criterion the registry does not know, a gate that disagrees with it, an out-of-layer criterion, a detector
      that disagrees with the registry;
  R5  a PASS the census itself would not honour (Null.* / Narr.fidelity_test cap, INCONCLUSIVE, unknown basis);
  R6  a PASS with no semantic fingerprint, no writer hashes (without a stated reason) or malformed ones;
  R7  upstream certification ids that are unknown, not the latest generation, not passing, self, or malformed;
  R8  a census cross-check that disagrees (run id, asset, criterion, verdict, cause);
  R9  a ledger that is missing, unreadable, tampered (generation gap, id mismatch) or holds a record it cannot read.
Every refusal also proves NOTHING WAS WRITTEN (the ledger bytes are identical). Idempotence and append-only are
proved on a tmp ledger copy: an unchanged measurement appends nothing; a changed one appends generation+1; old
bytes are never touched.

Offline: tmp ledgers only, no database, no network.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402

RUN = "2026-10-01T10:00:00+05:30"
RUN2 = "2026-10-02T10:00:00+05:30"
FP = "a" * 64
FP2 = "b" * 64
WH = {"platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py": "c" * 64}


# ───────────────────────── harness ─────────────────────────

@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "asset_certs.jsonl"
    p.write_text(json.dumps({"asset": "_schema", "_doc": "test ledger"}) + "\n", encoding="utf-8")
    return p


def kw(ledger, **over):
    """A valid PASS request; `over` replaces fields (a value of `...` deletes the key)."""
    d = dict(asset="bg_ontology", layer="L0", criterion="Build.registered", verdict="PASS",
             evidence=dict(census_run_id=RUN, measured="registered writer agrees"),
             verified_by="census-run", writer_hashes=dict(WH), semantic_fingerprint=FP,
             ledger_path=ledger, verified_on="2026-10-01T11:00:00+05:30")
    for k, v in over.items():
        if v is ...:
            d.pop(k, None)
        else:
            d[k] = v
    return d


def lines(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def refused(ledger, code, **over):
    """The request is refused with `code` and the ledger is byte-identical afterwards."""
    before = ledger.read_bytes() if ledger.exists() else None
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, **over))
    assert ei.value.code == code, (ei.value.code, str(ei.value))
    after = ledger.read_bytes() if ledger.exists() else None
    assert before == after, "a refused request changed the ledger"
    return ei.value


def census(measurements, asset="bg_ontology", layer="L0", generated=RUN):
    return dict(generated=generated, layer=layer,
                assets=[dict(asset_id=asset, layer=layer, measurements=measurements)])


# ───────────────────────── the record itself ─────────────────────────

def test_pass_appends_a_complete_record(ledger):
    r = nc.write_certification(**kw(ledger, job_image_tag="img-7"))
    assert r.status == "appended"
    rows = lines(ledger)
    assert len(rows) == 2 and rows[0]["asset"] == "_schema"
    rec = rows[1]
    assert rec == r.record
    assert rec["asset"] == "bg_ontology" and rec["layer"] == "L0" and rec["kind"] == "gate"
    assert rec["gate"] == "Build" and rec["criterion"] == "Build.registered"
    assert rec["detector"] == "asset_census.py:measure()" and rec["verdict"] == "PASS"
    assert rec["evidence"]["census_run_id"] == RUN
    assert rec["job_image_tag"] == "img-7" and rec["writer_hashes"] == WH
    assert rec["semantic_fingerprint"] == FP and rec["upstream_cert_ids"] == []
    assert rec["generation"] == 1 and rec["cert_key"] == "bg_ontology|gate|Build.registered"
    assert rec["cert_id"] == "bg_ontology|gate|Build.registered@1"
    assert rec["verified_by"] == "census-run" and rec["verified_on"] == "2026-10-01T11:00:00+05:30"
    assert rec["na"] is None and rec["record_version"] == nc.RECORD_VERSION


def test_registry_stamps_come_from_asset_census_not_the_caller(ledger):
    rec = nc.write_certification(**kw(ledger)).record
    e = ac.CRITERION_REGISTRY["Build.registered"]
    assert rec["criterion_version"] == e["revision"]
    assert rec["registry_revision"] == ac.REGISTRY_REVISION
    assert rec["registry_fingerprint"] == ac.registry_fingerprint()
    assert rec["detector"] == e["detector"]


def test_job_image_tag_is_an_honest_null_when_unknown_never_blank(ledger):
    assert nc.write_certification(**kw(ledger)).record["job_image_tag"] is None
    refused(ledger, "bad_job_image_tag", criterion="Build.contract", job_image_tag="  ")


def test_verified_by_is_required_and_verified_on_is_stamped_tz_aware(ledger):
    refused(ledger, "bad_verified_by", verified_by="")
    refused(ledger, "bad_verified_by", verified_by=None)
    d = kw(ledger)
    d.pop("verified_on")
    rec = nc.write_certification(**d).record
    import datetime as dt
    assert dt.datetime.fromisoformat(rec["verified_on"]).tzinfo is not None


# ───────────────────────── R1: detector NONE ─────────────────────────

def test_r1_pass_on_a_detector_none_criterion_is_refused(ledger):
    assert ac.CRITERION_REGISTRY["Carr.D1"]["detector"] == "NONE"
    refused(ledger, "detector_none", criterion="Carr.D1")


@pytest.mark.parametrize("verdict", ["FAIL", "PARTIAL", "ERRORED", "N/A"])
def test_r1_detector_none_admits_only_no_detector(ledger, verdict):
    over = dict(criterion="Carr.D2", verdict=verdict)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, **over))
    assert ei.value.code in ("detector_none", "na_not_computed")
    assert len(lines(ledger)) == 1


def test_r1_no_detector_is_recordable_under_a_none_detector(ledger):
    r = nc.write_certification(**kw(ledger, criterion="Carr.D3", verdict="NO_DETECTOR",
                                    semantic_fingerprint=None, writer_hashes=None))
    assert r.record["verdict"] == "NO_DETECTOR" and r.record["detector"] == "NONE"


def test_r1_registry_entry_turning_none_makes_a_pass_refused(ledger, monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Build.registered"] = dict(reg["Build.registered"], detector="NONE")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    refused(ledger, "detector_none")


def test_r1_a_caller_supplied_detector_cannot_override_the_registry(ledger):
    refused(ledger, "detector_mismatch", criterion="Carr.D1", detector="my_detector.py")
    refused(ledger, "detector_mismatch", detector="something_else")
    assert nc.write_certification(**kw(ledger, detector="asset_census.py:measure()")).status == "appended"


# ───────────────────────── R2: census run id ─────────────────────────

@pytest.mark.parametrize("ev", [
    dict(measured="x"),                                   # key absent
    dict(census_run_id="", measured="x"),
    dict(census_run_id="   ", measured="x"),
    dict(census_run_id=None),
    dict(census_run_id=12345),
    dict(census_run_id="yesterday"),                      # not an ISO timestamp
    dict(census_run_id="2026-10-01T10:00:00"),            # naive: the census's `generated` always carries an offset
])
def test_r2_pass_without_a_usable_census_run_id_is_refused(ledger, ev):
    refused(ledger, "no_census_run_id", evidence=ev)


@pytest.mark.parametrize("ev", [None, "census run 1", [], 7])
def test_r2_evidence_must_be_a_mapping(ledger, ev):
    refused(ledger, "no_census_run_id", evidence=ev)


@pytest.mark.parametrize("verdict", ["FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED"])
def test_r2_no_verdict_is_recorded_without_a_run_id(ledger, verdict):
    refused(ledger, "no_census_run_id", verdict=verdict, evidence=dict(measured="x"))


def test_r2_unknown_verdict_is_refused(ledger):
    refused(ledger, "bad_verdict", verdict="pass")
    refused(ledger, "bad_verdict", verdict="NOT_GENERIC")
    refused(ledger, "bad_verdict", verdict=None)


# ───────────────────────── R4: criterion binding ─────────────────────────

def test_r4_unregistered_criterion_is_refused(ledger):
    refused(ledger, "unregistered_criterion", criterion="Made.up")


def test_r4_a_gate_that_disagrees_with_the_registry_is_refused(ledger):
    refused(ledger, "gate_mismatch", gate="Ldgr")
    assert nc.write_certification(**kw(ledger, gate="Build")).record["gate"] == "Build"


def test_r4_out_of_layer_criterion_is_refused(ledger, monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Build.registered"] = dict(reg["Build.registered"], layers=("L1",))
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    refused(ledger, "out_of_layer")


def test_r4_pass_on_a_criterion_the_facts_disprove_is_refused(ledger):
    # no citation column among the supplied columns: Ldgr.source_presence is NOT_APPLICABLE, so a measured PASS
    # contradicts the registry
    refused(ledger, "not_applicable_pass", criterion="Ldgr.source_presence", facts=dict(columns=["a", "b"]))


def test_r4_bad_layer_asset_and_kind(ledger):
    refused(ledger, "bad_layer", layer="L9")
    refused(ledger, "bad_asset", asset="Bg Ontology")
    refused(ledger, "bad_asset", asset="")
    refused(ledger, "asset_layer_mismatch", asset="ga_positions")        # L0 expects bg_
    refused(ledger, "bad_kind", kind="criterion")


# ───────────────────────── R5: what the census itself would not honour ─────────────────────────

@pytest.mark.parametrize("crit", ["Null.blank_rows", "Null.schema_default", "Narr.fidelity_test"])
def test_r5_capped_criteria_cannot_read_pass(ledger, crit):
    assert ac.CRITERION_REGISTRY[crit]["detector"] != "NONE"
    refused(ledger, "capped_verdict", criterion=crit)


def test_r5_capped_criteria_may_be_recorded_partial(ledger):
    r = nc.write_certification(**kw(ledger, criterion="Null.blank_rows", verdict="PARTIAL"))
    assert r.record["verdict"] == "PARTIAL"


def test_r5_inconclusive_pass_or_partial_is_refused(ledger):
    refused(ledger, "inconclusive", inconclusive=True)
    refused(ledger, "inconclusive", inconclusive=True, verdict="PARTIAL")


def test_r5_unknown_basis_is_refused_and_declaration_is_recorded(ledger):
    refused(ledger, "bad_basis", basis="Declaration")
    refused(ledger, "bad_basis", basis="measured")
    rec = nc.write_certification(**kw(ledger, basis="declaration")).record
    assert rec["basis"] == "declaration"


# ───────────────────────── R6: what makes a PASS able to go stale ─────────────────────────

def test_r6_pass_needs_a_semantic_fingerprint(ledger):
    refused(ledger, "missing_fingerprint", semantic_fingerprint=None)
    refused(ledger, "bad_fingerprint", semantic_fingerprint="abc")
    refused(ledger, "bad_fingerprint", semantic_fingerprint="Z" * 64)
    refused(ledger, "bad_fingerprint", semantic_fingerprint="A" * 64)     # canonical form is lower-case hex


def test_r6_fail_may_carry_no_fingerprint_but_a_given_one_is_validated(ledger):
    r = nc.write_certification(**kw(ledger, verdict="FAIL", semantic_fingerprint=None, writer_hashes=None))
    assert r.record["semantic_fingerprint"] is None and r.record["writer_hashes"] == {}
    refused(ledger, "bad_fingerprint", verdict="FAIL", semantic_fingerprint="nope", criterion="Build.contract")


def test_r6_pass_needs_writer_hashes_or_a_stated_reason(ledger):
    refused(ledger, "missing_writer_hashes", writer_hashes=None)
    refused(ledger, "missing_writer_hashes", writer_hashes={})
    refused(ledger, "missing_writer_hashes", writer_hashes={}, writer_hashes_reason="  ")
    r = nc.write_certification(**kw(ledger, writer_hashes={}, writer_hashes_reason="service asset: no writer file"))
    assert r.record["writer_hashes"] == {} and r.record["writer_hashes_reason"].startswith("service asset")


def test_r6_malformed_writer_hashes_are_refused(ledger):
    refused(ledger, "bad_writer_hashes", writer_hashes={"/abs/path.py": "c" * 64})
    refused(ledger, "bad_writer_hashes", writer_hashes={"../up.py": "c" * 64})
    refused(ledger, "bad_writer_hashes", writer_hashes={"a/b.py": "short"})
    refused(ledger, "bad_writer_hashes", writer_hashes={"a/b.py": "C" * 64})
    refused(ledger, "bad_writer_hashes", writer_hashes=["a/b.py"])
    refused(ledger, "bad_writer_hashes", writer_hashes={"": "c" * 64})


def test_r6_hash_writer_files_working_tree_and_committed_ref(tmp_path):
    import hashlib
    repo = tmp_path / "r"
    (repo / "w").mkdir(parents=True)
    f = repo / "w" / "a.py"
    f.write_text("print(1)\n")
    run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                                    env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                                         "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                                         "HOME": str(tmp_path)})
    run("init", "-q")
    run("add", "w/a.py")
    run("commit", "-q", "-m", "x")
    committed = hashlib.sha256(b"print(1)\n").hexdigest()
    f.write_text("print(2)\n")                                            # dirty working tree
    assert nc.hash_writer_files(["w/a.py"], repo=repo) == {"w/a.py": hashlib.sha256(b"print(2)\n").hexdigest()}
    assert nc.hash_writer_files(["w/a.py"], repo=repo, ref="HEAD") == {"w/a.py": committed}
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.hash_writer_files(["w/missing.py"], repo=repo)
    assert ei.value.code == "bad_writer_hashes"
    with pytest.raises(nc.CertificationRefused):
        nc.hash_writer_files(["w/missing.py"], repo=repo, ref="HEAD")


# ───────────────────────── R3: N/A is computed, never typed ─────────────────────────

NA_FACTS = dict(columns=["id", "name"])                   # no citation column -> Ldgr.source_presence#columns_any
NA_RID = "Ldgr.source_presence#columns_any"


def na_kw(ledger, **over):
    base = dict(criterion="Ldgr.source_presence", verdict="N/A", facts=dict(NA_FACTS), na_rule_id=NA_RID,
                semantic_fingerprint=None, writer_hashes=None)
    base.update(over)
    return kw(ledger, **base)


def test_r3_the_registry_really_yields_that_rule_id_for_those_facts():
    ap = ac.criterion_applicability("Ldgr.source_presence", "L0", NA_FACTS)
    assert ap["state"] == "NOT_APPLICABLE" and ap["rule_id"] == NA_RID


def test_r3_na_is_refused_while_no_rule_is_declared_the_real_state_today(ledger):
    assert ac.NA_RULE_DECISIONS == {}, "N-22 declared a rule: update this test to the declared state"
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**na_kw(ledger))
    assert ei.value.code == "na_not_computed" and "undecided" in str(ei.value)
    assert len(lines(ledger)) == 1


def test_r3_na_computed_by_the_registry_under_a_declared_rule_is_recorded(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    rec = nc.write_certification(**na_kw(ledger)).record
    assert rec["verdict"] == "N/A"
    assert rec["na"] == dict(rule_id=NA_RID, decision_id="N-22.test", basis="applicability_facts", cause=None,
                             facts=dict(columns=["id", "name"]))


def test_r3_a_typed_na_with_no_rule_id_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    refused(ledger, "na_not_computed", **{k: v for k, v in na_kw(ledger).items() if k != "na_rule_id"})
    refused(ledger, "na_not_computed", **na_kw(ledger, na_rule_id=""))


def test_r3_a_rule_id_that_is_not_the_one_the_registry_yields_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test", "Earn.service_state#asset_kinds": "N-22.other"})
    refused(ledger, "na_not_computed", **na_kw(ledger, na_rule_id="Ldgr.source_presence#asset_kinds"))
    refused(ledger, "na_not_computed", **na_kw(ledger, na_rule_id="Earn.service_state#asset_kinds"))   # declared, not this criterion's
    refused(ledger, "na_not_computed", **na_kw(ledger, na_rule_id="Ldgr.source_presence#measured"))
    refused(ledger, "na_not_computed", **na_kw(ledger, na_rule_id="Nope#columns_any"))


def test_r3_na_on_a_criterion_that_applies_or_is_unknown_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    refused(ledger, "na_not_computed", **na_kw(ledger, facts=dict(columns=["id", "source_citation"])))   # applies
    refused(ledger, "na_not_computed", **na_kw(ledger, facts=None))                                       # unknown
    refused(ledger, "na_not_computed", **na_kw(ledger, facts={}))
    refused(ledger, "na_not_computed", **na_kw(ledger, facts=dict(columns="id,name")))                    # unusable


def test_r3_a_declared_rule_that_the_inspector_cannot_issue_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Bogus#columns_any": "N-22.test"})
    refused(ledger, "na_rules_invalid", **na_kw(ledger))


def test_r3_na_needs_a_census_run_id_too(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    refused(ledger, "no_census_run_id", **na_kw(ledger, evidence=dict(measured="x")))


def test_r3_a_measured_record_for_the_criterion_takes_precedence_over_applicability(ledger, monkeypatch):
    # the rollup reads a measurement before any applicability rule; so must this writer
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    c = census({"Ldgr.source_presence": dict(v="PASS", measured="m")})
    refused(ledger, "na_not_computed", **na_kw(ledger, census=c))


def test_r3_additions_have_no_registry_rule_so_no_na(ledger):
    refused(ledger, "na_not_computed", kind="addition", criterion="D-TIME", detector="d.py", verdict="N/A",
            criterion_version=1, na_rule_id="D-TIME#columns_any", semantic_fingerprint=None, writer_hashes=None)


def measured_na(ledger, **over):
    c = census({"Narr.agree": dict(v="N/A", measured="no prose", cause="no-prose")})
    base = dict(criterion="Narr.agree", verdict="N/A", na_rule_id="Narr.agree#measured:no-prose", census=c)
    base.update(over)
    return kw(ledger, **base)


def test_r3_a_measured_cause_na_is_recorded_only_with_the_census_record_and_a_declared_rule(ledger, monkeypatch):
    rid = "Narr.agree#measured:no-prose"
    with pytest.raises(nc.CertificationRefused) as ei:                    # rule undeclared (real state)
        nc.write_certification(**measured_na(ledger))
    assert ei.value.code == "na_not_computed"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {rid: "N-22.nr"})
    rec = nc.write_certification(**measured_na(ledger)).record
    assert rec["na"] == dict(rule_id=rid, decision_id="N-22.nr", basis="measured_cause", cause="no-prose", facts=None)


def test_r3_a_measured_cause_na_without_the_census_record_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Narr.agree#measured:no-prose": "N-22.nr"})
    refused(ledger, "na_not_computed", **measured_na(ledger, census=None))


def test_r3_measured_na_cause_must_match_census_and_be_registered(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Narr.agree#measured:no-prose": "N-22.nr"})
    other = census({"Narr.agree": dict(v="N/A", measured="m", cause="never-attempted")})
    refused(ledger, "na_not_computed", **measured_na(ledger, census=other))
    notna = census({"Narr.agree": dict(v="PASS", measured="m")})
    refused(ledger, "na_not_computed", **measured_na(ledger, census=notna))
    refused(ledger, "na_not_computed", **measured_na(ledger, na_rule_id="Narr.agree#measured:made-up"))


def test_r3_a_declared_rule_id_of_another_criterion_cannot_release_this_one(ledger, monkeypatch):
    # Narr.checkable shares the cause slug `no-prose`; its declared rule must not release a Narr.agree record
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Narr.checkable#measured:no-prose": "N-22.nr"})
    refused(ledger, "na_not_computed", **measured_na(ledger, na_rule_id="Narr.checkable#measured:no-prose"))


def test_r3_measured_na_needs_a_fingerprint_because_the_measurement_read_rows(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Narr.agree#measured:no-prose": "N-22.nr"})
    refused(ledger, "missing_fingerprint", **measured_na(ledger, semantic_fingerprint=None))


def test_r3_measured_na_needs_writer_hashes_too(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Narr.agree#measured:no-prose": "N-22.nr"})
    refused(ledger, "missing_writer_hashes", **measured_na(ledger, writer_hashes=None))


# ───────────────────────── R8: census cross-check ─────────────────────────

def test_r8_census_cross_check_accepts_the_matching_measurement(ledger):
    c = census({"Build.registered": dict(v="PASS", measured="m")})
    assert nc.write_certification(**kw(ledger, census=c)).status == "appended"


def test_r8_census_disagreements_are_refused(ledger):
    refused(ledger, "census_mismatch", census=census({"Build.registered": dict(v="PASS")}, generated=RUN2))
    refused(ledger, "census_mismatch", census=census({"Build.registered": dict(v="FAIL", measured="m")}))
    refused(ledger, "census_mismatch", census=census({"Build.contract": dict(v="PASS")}))
    refused(ledger, "census_mismatch", census=census({"Build.registered": dict(v="PASS")}, asset="bg_other"))
    refused(ledger, "census_mismatch", census=census({"Build.registered": dict(v="PASS")}, layer="L1"))
    refused(ledger, "census_mismatch", census=dict(generated=RUN))
    refused(ledger, "census_mismatch", census="not a census")


def test_r8_a_census_measurement_flagged_inconclusive_blocks_a_pass(ledger):
    c = census({"Build.registered": dict(v="PASS", measured="m", inconclusive=True)})
    refused(ledger, "inconclusive", census=c)


def test_r8_census_basis_and_cap_are_read_from_the_measurement_too(ledger):
    c = census({"Build.registered": dict(v="PASS", measured="m", basis="declaration")})
    assert nc.write_certification(**kw(ledger, census=c)).record["basis"] == "declaration"


# ───────────────────────── additions ─────────────────────────

def add_kw(ledger, **over):
    base = dict(kind="addition", criterion="D-GROUNDING", detector="grounding_probe.py", criterion_version=1)
    base.update(over)
    return kw(ledger, **base)


def test_additions_are_recorded_with_their_own_detector_and_version(ledger):
    rec = nc.write_certification(**add_kw(ledger)).record
    assert rec["kind"] == "addition" and rec["gate"] is None and rec["detector"] == "grounding_probe.py"
    assert rec["criterion_version"] == 1 and rec["registry_revision"] is None and rec["registry_fingerprint"] is None
    assert rec["cert_id"] == "bg_ontology|addition|D-GROUNDING@1"


@pytest.mark.parametrize("det", [None, "", "  ", "NONE", "none", "None"])
def test_additions_never_pass_without_a_real_detector(ledger, det):
    refused(ledger, "detector_none", **add_kw(ledger, detector=det))


def test_additions_need_a_version_and_a_well_formed_id(ledger):
    refused(ledger, "bad_criterion_version", **add_kw(ledger, criterion_version=None))
    refused(ledger, "bad_criterion_version", **add_kw(ledger, criterion_version=0))
    refused(ledger, "bad_criterion_version", **add_kw(ledger, criterion_version="1"))
    refused(ledger, "bad_criterion_id", **add_kw(ledger, criterion="has space|pipe@1"))


def test_an_addition_id_cannot_shadow_a_registered_criterion(ledger):
    refused(ledger, "bad_criterion_id", **add_kw(ledger, criterion="Build.registered"))


def test_a_gate_record_cannot_claim_a_criterion_version_that_is_not_the_registrys(ledger):
    refused(ledger, "bad_criterion_version", criterion_version=99)
    assert nc.write_certification(**kw(ledger, criterion_version=ac.CRITERION_REGISTRY["Build.registered"]["revision"])
                                  ).status == "appended"


# ───────────────────────── idempotence + append-only (3) ─────────────────────────

def test_rewriting_the_identical_record_appends_nothing(ledger):
    r1 = nc.write_certification(**kw(ledger))
    snap = ledger.read_bytes()
    r2 = nc.write_certification(**kw(ledger))
    assert r1.status == "appended" and r2.status == "unchanged"
    assert r2.record == r1.record and r2.cert_id == r1.cert_id
    assert ledger.read_bytes() == snap


def test_a_remeasurement_that_changes_no_currency_field_appends_nothing(ledger):
    # same verdict, writer hashes, upstream, semantic fingerprint under a NEWER census run by another operator:
    # an idempotent rebuild must leave every downstream certificate current (arch 12.16), so no new generation
    nc.write_certification(**kw(ledger))
    snap = ledger.read_bytes()
    r = nc.write_certification(**kw(ledger, evidence=dict(census_run_id=RUN2, measured="different words"),
                                    verified_by="someone-else", verified_on="2026-10-05T00:00:00+05:30",
                                    job_image_tag="img-9"))
    assert r.status == "unchanged" and r.record["generation"] == 1
    assert ledger.read_bytes() == snap


@pytest.mark.parametrize("change", [
    dict(semantic_fingerprint=FP2),
    dict(writer_hashes={"platform/x.py": "d" * 64}),
    dict(verdict="FAIL"),
    dict(verdict="PARTIAL"),
    dict(basis="declaration"),
])
def test_a_changed_measurement_appends_generation_plus_one_and_never_touches_old_bytes(ledger, change):
    nc.write_certification(**kw(ledger))
    before = ledger.read_bytes()
    r = nc.write_certification(**kw(ledger, **change))
    after = ledger.read_bytes()
    assert r.status == "appended" and r.record["generation"] == 2
    assert r.record["cert_id"] == "bg_ontology|gate|Build.registered@2"
    assert after.startswith(before) and len(after) > len(before), "append-only: the old bytes must be a prefix"
    assert len(lines(ledger)) == 3
    assert lines(ledger)[1]["generation"] == 1                          # the old line is still there, unedited


def test_a_to_b_to_a_is_three_generations_not_a_silent_revert(ledger):
    nc.write_certification(**kw(ledger))
    nc.write_certification(**kw(ledger, semantic_fingerprint=FP2))
    r = nc.write_certification(**kw(ledger))
    assert r.status == "appended" and r.record["generation"] == 3
    assert [x["generation"] for x in lines(ledger)[1:]] == [1, 2, 3]


def test_generations_are_per_key(ledger):
    nc.write_certification(**kw(ledger))
    nc.write_certification(**kw(ledger, semantic_fingerprint=FP2))
    other = nc.write_certification(**kw(ledger, criterion="Build.contract"))
    other_asset = nc.write_certification(**kw(ledger, asset="bg_panchanga"))
    assert other.record["generation"] == 1 and other_asset.record["generation"] == 1


def test_registry_revision_change_is_a_changed_measurement(ledger, monkeypatch):
    nc.write_certification(**kw(ledger))
    monkeypatch.setattr(ac, "REGISTRY_REVISION", ac.REGISTRY_REVISION + 1)
    r = nc.write_certification(**kw(ledger))
    assert r.status == "appended" and r.record["generation"] == 2
    assert r.record["registry_revision"] == ac.REGISTRY_REVISION


def test_a_refused_request_after_a_good_one_still_writes_nothing(ledger):
    nc.write_certification(**kw(ledger))
    refused(ledger, "detector_none", criterion="Carr.D1")
    refused(ledger, "no_census_run_id", evidence={})
    assert len(lines(ledger)) == 2


def test_concurrent_identical_writers_append_exactly_one_record(ledger):
    import threading
    n, results, errs = 12, [], []
    gate = threading.Barrier(n)

    def go():
        try:
            gate.wait()
            results.append(nc.write_certification(**kw(ledger)).status)
        except Exception as e:                                          # noqa: BLE001
            errs.append(e)

    ts = [threading.Thread(target=go) for _ in range(n)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs, errs
    assert sorted(results) == ["appended"] + ["unchanged"] * (n - 1)
    assert [r["generation"] for r in lines(ledger)[1:]] == [1]


def test_the_writer_waits_for_the_ledger_lock_deterministically(ledger):
    import fcntl
    import threading
    import time
    out = []
    with open(ledger, "rb") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        t = threading.Thread(target=lambda: out.append(nc.write_certification(**kw(ledger)).status))
        t.start()
        time.sleep(0.4)
        blocked = t.is_alive() and not out
        size_while_held = ledger.stat().st_size
        fcntl.flock(held, fcntl.LOCK_UN)
    t.join(5)
    assert blocked, "the writer did not wait for the exclusive lock"
    assert size_while_held == len(json.dumps({"asset": "_schema", "_doc": "test ledger"})) + 1
    assert out == ["appended"] and len(lines(ledger)) == 2


# ───────────────────────── R7: upstream certification ids ─────────────────────────

def upstream_ledger(ledger):
    nc.write_certification(**kw(ledger, asset="bg_dependency"))          # bg_dependency|gate|Build.registered@1
    return "bg_dependency|gate|Build.registered@1"


def test_r7_upstream_ids_are_recorded_sorted_and_deduplicated(ledger):
    up = upstream_ledger(ledger)
    nc.write_certification(**kw(ledger, asset="bg_other", criterion="Build.contract"))
    up2 = "bg_other|gate|Build.contract@1"
    rec = nc.write_certification(**kw(ledger, upstream_cert_ids=[up2, up, up])).record
    assert rec["upstream_cert_ids"] == sorted([up, up2])


def test_r7_a_changed_upstream_generation_is_a_changed_measurement(ledger):
    up = upstream_ledger(ledger)
    nc.write_certification(**kw(ledger, upstream_cert_ids=[up]))
    nc.write_certification(**kw(ledger, asset="bg_dependency", semantic_fingerprint=FP2))     # upstream -> generation 2
    r = nc.write_certification(**kw(ledger, upstream_cert_ids=["bg_dependency|gate|Build.registered@2"]))
    assert r.status == "appended" and r.record["generation"] == 2


def test_r7_unknown_upstream_is_refused(ledger):
    upstream_ledger(ledger)
    refused(ledger, "upstream_unknown", upstream_cert_ids=["bg_dependency|gate|Build.registered@7"])
    refused(ledger, "upstream_unknown", upstream_cert_ids=["bg_nobody|gate|Build.registered@1"])


def test_r7_a_non_latest_upstream_generation_is_stale_at_birth_and_refused(ledger):
    up = upstream_ledger(ledger)
    nc.write_certification(**kw(ledger, asset="bg_dependency", semantic_fingerprint=FP2))     # @1 is now superseded
    refused(ledger, "upstream_stale", upstream_cert_ids=[up])


def test_r7_a_pass_cannot_rest_on_a_non_passing_upstream(ledger):
    nc.write_certification(**kw(ledger, asset="bg_dependency", verdict="FAIL", semantic_fingerprint=None,
                                writer_hashes=None))
    refused(ledger, "upstream_not_passing", upstream_cert_ids=["bg_dependency|gate|Build.registered@1"])
    # a FAIL record may name it (it records a fact about a failing chain, it certifies nothing)
    r = nc.write_certification(**kw(ledger, verdict="FAIL", semantic_fingerprint=None, writer_hashes=None,
                                    criterion="Build.contract",
                                    upstream_cert_ids=["bg_dependency|gate|Build.registered@1"]))
    assert r.status == "appended"


def test_r7_self_reference_and_malformed_ids_are_refused(ledger):
    nc.write_certification(**kw(ledger))
    refused(ledger, "upstream_self", semantic_fingerprint=FP2, upstream_cert_ids=["bg_ontology|gate|Build.registered@1"])
    for bad in ("nonsense", "a|b@x", "a|gate|C.d@0", "a|gate|C.d@-1", "", None, 5):
        refused(ledger, "bad_upstream", upstream_cert_ids=[bad])
    refused(ledger, "bad_upstream", upstream_cert_ids="a|gate|C.d@1")                         # a bare string, not a list


# ───────────────────────── R9: the ledger itself ─────────────────────────

def test_r9_missing_ledger_is_refused_not_silently_created(tmp_path):
    p = tmp_path / "nope.jsonl"
    refused(p, "ledger_missing")
    assert not p.exists()


def test_r9_init_creates_the_ledger_with_a_schema_line_first(tmp_path):
    p = tmp_path / "new.jsonl"
    nc.write_certification(**kw(p, init=True))
    rows = lines(p)
    assert rows[0]["asset"] == "_schema" and "append-only" in rows[0]["_doc"].lower()
    assert rows[1]["generation"] == 1
    nc.write_certification(**kw(p, init=True))                              # init never rewrites an existing ledger
    assert len(lines(p)) == 2


def test_r9_a_refused_request_does_not_create_the_ledger_even_with_init(tmp_path):
    p = tmp_path / "new.jsonl"
    with pytest.raises(nc.CertificationRefused):
        nc.write_certification(**kw(p, init=True, criterion="Carr.D1"))
    assert not p.exists()


def test_r9_malformed_or_unreadable_ledgers_are_refused(ledger):
    ledger.write_text(ledger.read_text() + "{not json\n")
    refused(ledger, "bad_ledger")


def test_r9_first_line_must_be_the_schema_row(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_text(json.dumps({"asset": "bg_x", "cert_id": "bg_x|gate|Build.registered@1", "generation": 1}) + "\n")
    refused(p, "bad_ledger")
    p.write_text("")
    refused(p, "bad_ledger")


def test_r9_a_legacy_record_without_a_generation_is_refused_not_ignored(ledger):
    ledger.write_text(ledger.read_text() + json.dumps({"asset": "bg_x", "criterion": "Build.registered",
                                                       "verdict": "PASS"}) + "\n")
    refused(ledger, "bad_ledger")


def test_r9_tampered_generation_sequence_or_id_is_refused(ledger):
    nc.write_certification(**kw(ledger))
    nc.write_certification(**kw(ledger, semantic_fingerprint=FP2))
    rows = [json.loads(x) for x in ledger.read_text().splitlines()]
    gap = [rows[0], rows[2]]                                                 # generation 1 deleted from the history
    ledger.write_text("\n".join(json.dumps(x) for x in gap) + "\n")
    refused(ledger, "bad_ledger", semantic_fingerprint=FP)
    bad_id = [rows[0], dict(rows[1], cert_id="bg_ontology|gate|Build.registered@9")]
    ledger.write_text("\n".join(json.dumps(x) for x in bad_id) + "\n")
    refused(ledger, "bad_ledger")


def test_r9_a_last_line_with_no_newline_is_appended_after_not_glued_to(ledger):
    nc.write_certification(**kw(ledger))
    ledger.write_bytes(ledger.read_bytes().rstrip(b"\n"))
    r = nc.write_certification(**kw(ledger, semantic_fingerprint=FP2))
    assert r.record["generation"] == 2 and len(lines(ledger)) == 3


def test_r9_evidence_that_cannot_be_serialised_is_refused_before_any_write(ledger):
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, measured={"a", "set"}))
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, secret_extra="x"))


def test_r9_a_refusal_under_init_on_a_fresh_ledger_leaves_no_file_behind(tmp_path):
    p = tmp_path / "fresh.jsonl"
    with pytest.raises(nc.CertificationRefused) as ei:                   # ledger-dependent refusal: unknown upstream
        nc.write_certification(**kw(p, init=True, upstream_cert_ids=["bg_x|gate|Build.registered@1"]))
    assert ei.value.code == "upstream_unknown" and not p.exists()


# ───────────────────────── ledger path resolution (5) ─────────────────────────

def test_ledger_path_argument_beats_env_beats_default(tmp_path, monkeypatch):
    envp = tmp_path / "env.jsonl"
    monkeypatch.setenv("NIKASHA_CERTS_LEDGER", str(envp))
    assert nc.resolve_ledger_path(None) == envp
    argp = tmp_path / "arg.jsonl"
    assert nc.resolve_ledger_path(argp) == argp
    monkeypatch.delenv("NIKASHA_CERTS_LEDGER")
    assert nc.resolve_ledger_path(None) == ac.CTRL / "asset_certs.jsonl"
    assert nc.resolve_ledger_path(None).name == "asset_certs.jsonl"
    assert nc.resolve_ledger_path(None).parent.name == "control"


def test_env_override_is_what_write_certification_uses(tmp_path, monkeypatch, ledger):
    monkeypatch.setenv("NIKASHA_CERTS_LEDGER", str(ledger))
    d = kw(ledger)
    d.pop("ledger_path")
    assert nc.write_certification(**d).status == "appended"
    assert len(lines(ledger)) == 2


def test_with_no_argument_and_no_env_the_default_is_the_control_directory_ledger():
    assert nc.resolve_ledger_path(None, env={}) == ac.CTRL / "asset_certs.jsonl"


# ───────────────────────── CLI ─────────────────────────

SCRIPT = HERE.parent / "nikasha_certify.py"


def cli(args, **kw_):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, **kw_)


def cli_args(ledger, *extra):
    return ["--ledger", str(ledger), "--asset", "bg_ontology", "--layer", "L0", "--criterion", "Build.registered",
            "--verdict", "PASS", "--census-run-id", RUN, "--measured", "registered writer agrees",
            "--verified-by", "census-run", "--semantic-fingerprint", FP,
            "--writer-hash", "w/a.py=" + "c" * 64, "--verified-on", "2026-10-01T11:00:00+05:30", *extra]


def test_cli_appends_then_reports_unchanged_and_exits_zero(ledger):
    p = cli(cli_args(ledger))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["status"] == "appended" and out["cert_id"] == "bg_ontology|gate|Build.registered@1"
    q = cli(cli_args(ledger))
    assert q.returncode == 0 and json.loads(q.stdout)["status"] == "unchanged"
    assert len(lines(ledger)) == 2


def test_cli_refusal_exits_2_names_the_code_and_writes_nothing(ledger):
    before = ledger.read_bytes()
    args = cli_args(ledger)
    args[args.index("Build.registered")] = "Carr.D1"
    p = cli(args)
    assert p.returncode == 2 and "detector_none" in p.stderr
    assert ledger.read_bytes() == before


def test_cli_missing_run_id_exits_2(ledger):
    args = cli_args(ledger)
    i = args.index("--census-run-id")
    del args[i:i + 2]
    p = cli(args)
    assert p.returncode == 2 and "no_census_run_id" in p.stderr
    assert len(lines(ledger)) == 1


def test_cli_census_file_supplies_the_run_id_and_is_cross_checked(ledger, tmp_path):
    cf = tmp_path / "census.json"
    cf.write_text(json.dumps(census({"Build.registered": dict(v="PASS", measured="m")})))
    args = cli_args(ledger, "--census", str(cf))
    i = args.index("--census-run-id")
    del args[i:i + 2]
    p = cli(args)
    assert p.returncode == 0, p.stderr
    assert lines(ledger)[1]["evidence"]["census_run_id"] == RUN
    cf.write_text(json.dumps(census({"Build.registered": dict(v="FAIL", measured="m")})))
    q = cli(args)
    assert q.returncode == 2 and "census_mismatch" in q.stderr


def test_cli_script_errors_exit_5(tmp_path):
    p = cli(["--ledger", str(tmp_path / "x.jsonl"), "--asset", "bg_a", "--layer", "L0", "--criterion", "Build.registered",
             "--verdict", "PASS", "--census", str(tmp_path / "no_such_census.json")])
    assert p.returncode == 5


def test_cli_n_a_typed_by_hand_is_refused(ledger):
    args = cli_args(ledger, "--na-rule-id", NA_RID, "--facts-json", json.dumps(NA_FACTS))
    args[args.index("PASS")] = "N/A"
    args[args.index("Build.registered")] = "Ldgr.source_presence"
    p = cli(args)
    assert p.returncode == 2 and "na_not_computed" in p.stderr
    assert len(lines(ledger)) == 1
