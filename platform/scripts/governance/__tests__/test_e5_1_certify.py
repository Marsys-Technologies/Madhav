"""test_e5_1_certify.py — Suvarna E5.1: the certification-record writer (`nikasha_certify.py`).

A certification record is what ELEVATED rests on (plan 1.1; arch 12.16), so this writer's job is mostly to REFUSE.
For kind=gate the verdict is NEVER a caller assertion: it is read from the census record (a FILE under the control
directory or a census archive, sha256 recorded) for that asset and criterion; a caller-passed verdict is only a
cross-check that must equal it. kind=addition keeps its caller verdict (no census cell exists for it).
Refusal list, each with its own tests below:
  R1  a PASS whose criterion has `detector: NONE` (and any non-NO_DETECTOR verdict under a NONE detector);
  R2  any record with no census run id in its evidence (PASS included; a naive or non-ISO id counts as none);
  R3  an N/A the registry did not compute (typed, undeclared rule id, wrong rule id, applicable, unknown facts,
      an addition, a measured cause the census cell does not carry);
  R4  a criterion the registry does not know, a gate that disagrees with it, an out-of-layer criterion, a detector
      that disagrees with the registry;
  R5  a PASS the census itself would not honour (Null.* / Narr.fidelity_test cap, INCONCLUSIVE, unknown basis);
  R6  a PASS with no semantic fingerprint, no VERIFIED writer hashes (without a stated, census-corroborated reason)
      or malformed ones;
  R7  upstream certification ids that are unknown, not the latest generation, not passing, self, or malformed;
  R8  the census gate: none supplied, not a trusted file, no such asset/cell, run id / layer / registry mismatch,
      caller verdict/basis/facts that differ from it;
  R9  a ledger that is missing, a symlink, torn, tampered (chain, generation gap, id mismatch) or unreadable.
Every refusal also proves NOTHING WAS WRITTEN (the ledger bytes are identical). Idempotence and append-only are
proved on a tmp ledger copy: an unchanged measurement appends nothing; a changed one appends generation+1; old
bytes are never touched.

Offline: tmp ledgers, tmp census files, a tmp writer repo; no database, no network.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import pathlib
import subprocess
import sys
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402

RUN = "2026-10-01T10:00:00+05:30"
RUN2 = "2026-10-02T10:00:00+05:30"
FP = "a" * 64
FP2 = "b" * 64
W1 = "platform/python-sidecar/pipeline/orchestrator/writers/bg_ontology.py"
W2 = "platform/python-sidecar/pipeline/orchestrator/writers/bg_other.py"
W1_BYTES = b"# bg_ontology writer\n"
W2_BYTES = b"# bg_other writer\n"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


WH = {W1: sha(W1_BYTES)}
ENV = types.SimpleNamespace(ctrl=None, repo=None, tmp=None)
_N = itertools.count()


# ───────────────────────── harness ─────────────────────────

@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    """A tmp control dir (the trusted census root), a tmp writer repo, no ambient env overrides."""
    ctrl = tmp_path / "control"
    ctrl.mkdir()
    repo = tmp_path / "repo"
    for rel, b in ((W1, W1_BYTES), (W2, W2_BYTES)):
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b)
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.delenv("NIKASHA_CENSUS_ARCHIVE", raising=False)
    monkeypatch.delenv("NIKASHA_CERTS_LEDGER", raising=False)
    ENV.ctrl, ENV.repo, ENV.tmp = ctrl, repo, tmp_path
    return ENV


@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "asset_certs.jsonl"
    p.write_text(json.dumps({"asset": "_schema", "_doc": "test ledger"}) + "\n", encoding="utf-8")
    return p


def write_census_file(measurements, asset="bg_ontology", layer="L0", generated=RUN, rec=None, head=None,
                      directory=None, name=None):
    """A census JSON file shaped like asset_census.measure() output (one asset record). `rec` updates the asset record
    (a value of `...` removes the key); `head` updates the census head."""
    record = dict(asset_id=asset, layer=layer, has_writer=True, writer_files=[W1], asset_kind="data",
                  target_columns=None, measurements=measurements)
    for k, v in (rec or {}).items():
        if v is ...:
            record.pop(k, None)
        else:
            record[k] = v
    c = dict(generated=generated, layer=layer, assets=[record])
    c.update(head or {})
    p = (directory or ENV.ctrl) / (name or f"census_{next(_N)}.json")
    p.write_text(json.dumps(c), encoding="utf-8")
    return p


def kw(ledger, **over):
    """A valid PASS request. `over` replaces fields (a value of `...` deletes the key). Special keys build the census
    FILE the request reads its verdict from: cell= (dict merged into the census cell, or `...` for no cell),
    rec= (asset-record fields), head= (census-head fields), generated=. Passing census_path/census explicitly
    disables the auto-built census (for the census-gate tests)."""
    cell = over.pop("cell", {})
    rec = over.pop("rec", None)
    head = over.pop("head", None)
    generated = over.pop("generated", None)
    d = dict(asset="bg_ontology", layer="L0", criterion="Build.registered", verdict="PASS",
             evidence=dict(census_run_id=RUN, measured="registered writer agrees"),
             verified_by="census-run", writer_files=[W1], writer_repo=ENV.repo, semantic_fingerprint=FP,
             ledger_path=ledger, verified_on="2026-10-01T11:00:00+05:30")
    for k, v in over.items():
        if v is ...:
            d.pop(k, None)
        else:
            d[k] = v
    if "census_path" not in over and "census" not in over and d.get("kind", "gate") == "gate":
        ev = d.get("evidence")
        run = generated or (ev.get("census_run_id") if isinstance(ev, dict) and isinstance(ev.get("census_run_id"), str)
                            else RUN)
        crit, v = d.get("criterion"), d.get("verdict")
        ms = {}
        if cell is not ... and isinstance(crit, str):
            c = dict(v=v if isinstance(v, str) and v in nc.VERDICTS else "PASS", measured="m")
            c.update(cell)
            ms[crit] = c
        asset = d.get("asset") if isinstance(d.get("asset"), str) else "bg_ontology"
        layer = d.get("layer") if isinstance(d.get("layer"), str) else "L0"
        d["census_path"] = write_census_file(ms, asset=asset, layer=layer, generated=run, rec=rec, head=head)
    return d


def lines(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def refused(ledger, code, **over):
    """The request is refused with `code` and the ledger bytes are identical afterwards."""
    before = ledger.read_bytes() if ledger.exists() else None
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger, **over))
    assert ei.value.code == code, (ei.value.code, str(ei.value))
    after = ledger.read_bytes() if ledger.exists() else None
    assert before == after, "a refused request changed the ledger"
    return ei.value


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
    assert rec["job_image_tag"] == "img-7" and rec["writer_hashes"] == WH and rec["writer_hashes_verified"] is True
    assert rec["semantic_fingerprint"] == FP and rec["upstream_cert_ids"] == []
    assert rec["generation"] == 1 and rec["cert_key"] == "bg_ontology|gate|Build.registered"
    assert rec["cert_id"] == "bg_ontology|gate|Build.registered@1"
    assert rec["verified_by"] == "census-run" and rec["verified_on"] == "2026-10-01T11:00:00+05:30"
    assert rec["na"] is None and rec["record_version"] == nc.RECORD_VERSION
    assert rec["cross_checked"] is True and rec["inconclusive"] is False and rec["transitive_only"] is False
    assert rec["registry_binding"] == "census_unbound"           # today's census head carries no registry fields


def test_the_record_binds_the_census_file_by_hash_and_the_chain_starts_at_the_schema_row(ledger):
    d = kw(ledger)
    cf = d["census_path"]
    rec = nc.write_certification(**d).record
    assert rec["evidence"]["census_sha256"] == sha(pathlib.Path(cf).read_bytes())
    assert rec["evidence"]["census_file"] == str(pathlib.Path(cf).resolve())
    raw = ledger.read_bytes().split(b"\n")
    assert rec["prev_sha256"] == sha(raw[0])                      # the schema row, byte for byte


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
    refused(ledger, "bad_verified_on", verified_on="yesterday")
    refused(ledger, "bad_verified_on", verified_on="2026-10-01T11:00:00")        # naive


# ───────────────────────── R1: detector NONE ─────────────────────────

def test_r1_pass_on_a_detector_none_criterion_is_refused(ledger):
    assert ac.CRITERION_REGISTRY["Carr.D1"]["detector"] == "NONE"
    refused(ledger, "detector_none", criterion="Carr.D1")


def test_r1_a_census_cell_reading_pass_on_a_detector_none_criterion_is_refused_too(ledger):
    refused(ledger, "detector_none", criterion="Carr.D1", verdict=None, cell=dict(v="PASS"))


@pytest.mark.parametrize("verdict", ["FAIL", "PARTIAL", "ERRORED", "N/A"])
def test_r1_detector_none_admits_only_no_detector(ledger, verdict):
    refused(ledger, "detector_none", criterion="Carr.D2", verdict=verdict)
    assert len(lines(ledger)) == 1


def test_r1_no_detector_is_recordable_under_a_none_detector_when_the_census_cell_says_so(ledger):
    r = nc.write_certification(**kw(ledger, criterion="Carr.D3", verdict="NO_DETECTOR", cell=dict(v="NO_DETECTOR"),
                                    semantic_fingerprint=None, writer_files=...))
    assert r.record["verdict"] == "NO_DETECTOR" and r.record["detector"] == "NONE"


def test_r1_no_detector_without_a_census_cell_is_refused_not_derived_from_absence(ledger):
    refused(ledger, "census_cell_missing", criterion="Carr.D3", verdict="NO_DETECTOR", cell=...,
            semantic_fingerprint=None, writer_files=...)


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
    dict(census_run_id=["x"]),
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


def test_r2_unknown_verdict_is_refused_and_a_gate_may_omit_it(ledger):
    refused(ledger, "bad_verdict", verdict="pass")
    refused(ledger, "bad_verdict", verdict="NOT_GENERIC")
    r = nc.write_certification(**kw(ledger, verdict=None))             # derived from the census cell
    assert r.record["verdict"] == "PASS"


# ───────────────────────── R8: the census gate (the verdict is not a caller assertion) ─────────────────────────

def test_gate_pass_without_census_refused(ledger):
    refused(ledger, "census_required", census_path=None)
    refused(ledger, "census_required", census_path=None, census=None)
    refused(ledger, "census_required", verdict="FAIL", census_path=None, semantic_fingerprint=None, writer_files=...)
    assert len(lines(ledger)) == 1


def test_a_census_dict_without_its_source_file_is_refused(ledger):
    d = dict(generated=RUN, layer="L0",
             assets=[dict(asset_id="bg_ontology", has_writer=True, measurements=dict(
                 {"Build.registered": dict(v="PASS", measured="m")}))])
    refused(ledger, "census_unsourced", census_path=None, census=d)


def test_a_census_dict_must_equal_the_bytes_of_its_source_file(ledger):
    p = write_census_file({"Build.registered": dict(v="PASS", measured="m")})
    forged = json.loads(p.read_text())
    forged["assets"][0]["measurements"]["Build.registered"]["v"] = "PASS"
    assert nc.write_certification(**kw(ledger, census_path=p, census=forged)).status == "appended"
    forged["assets"][0]["has_writer"] = False
    refused(ledger, "census_mismatch", semantic_fingerprint=FP2, census_path=p, census=forged)


def test_census_file_key_not_typable(ledger):
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, census_file="census.json"))
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, census_sha256="0" * 64))
    refused(ledger, "bad_evidence", census_path=None, evidence=dict(census_run_id=RUN, census_file="census.json"))
    refused(ledger, "bad_evidence", kind="addition", criterion="D-X", detector="d.py", criterion_version=1,
            evidence=dict(census_run_id=RUN, census_file="census.json"))


def test_the_census_must_be_a_file_under_the_control_dir_or_an_archive(ledger, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    out = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, directory=elsewhere, name="c.json")
    refused(ledger, "census_untrusted", census_path=out)                          # forged-in-a-temp-dir
    assert nc.write_certification(**kw(ledger, census_path=out, census_archive_dir=elsewhere)).status == "appended"
    monkeypatch.setenv("NIKASHA_CENSUS_ARCHIVE", str(elsewhere))                  # the env default
    nc.write_certification(**kw(ledger, census_path=out, semantic_fingerprint=FP2))
    monkeypatch.delenv("NIKASHA_CENSUS_ARCHIVE")
    refused(ledger, "census_untrusted", census_path=out, semantic_fingerprint="c" * 64)


def test_a_sibling_directory_sharing_a_prefix_is_not_the_archive(ledger, tmp_path):
    arch, evil = tmp_path / "arch", tmp_path / "arch2"
    arch.mkdir()
    evil.mkdir()
    out = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, directory=evil, name="c.json")
    refused(ledger, "census_untrusted", census_path=out, census_archive_dir=arch)


def test_a_symlink_inside_the_control_dir_to_an_outside_file_is_not_trusted(ledger, tmp_path):
    out = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, directory=tmp_path, name="outside.json")
    link = ENV.ctrl / "link.json"
    link.symlink_to(out)
    refused(ledger, "census_untrusted", census_path=link)


def test_a_missing_or_non_json_census_file_is_refused(ledger, tmp_path):
    refused(ledger, "bad_census", census_path=ENV.ctrl / "no_such.json")
    bad = ENV.ctrl / "bad.json"
    bad.write_text("{not json")
    refused(ledger, "bad_census", census_path=bad)
    arr = ENV.ctrl / "arr.json"
    arr.write_text("[1, 2]")
    refused(ledger, "bad_census", census_path=arr)
    refused(ledger, "bad_census", census_path=ENV.ctrl)                           # a directory


def test_duplicate_json_keys_in_the_census_are_refused(ledger):
    p = ENV.ctrl / "dup.json"
    p.write_text('{"generated": "%s", "generated": "%s", "layer": "L0", "assets": []}' % (RUN, RUN2))
    refused(ledger, "bad_census", census_path=p)
    q = ENV.ctrl / "dup2.json"
    q.write_text('{"generated": "%s", "layer": "L0", "assets": [{"asset_id": "bg_ontology", "measurements": '
                 '{"Build.registered": {"v": "FAIL", "v": "PASS"}}}]}' % RUN)
    refused(ledger, "bad_census", census_path=q)


def test_a_missing_cell_is_refused_not_read_as_a_verdict(ledger):
    refused(ledger, "census_cell_missing", cell=...)
    refused(ledger, "census_cell_missing", verdict=None, cell=...)


def test_the_run_id_must_equal_the_census_own_generated(ledger):
    refused(ledger, "census_run_id_mismatch", generated=RUN2)                     # evidence says RUN
    refused(ledger, "census_run_id_mismatch", evidence=dict(census_run_id=RUN2), generated=RUN)
    refused(ledger, "census_run_id_mismatch", head=dict(generated="not-a-timestamp"))
    assert nc.write_certification(**kw(ledger, evidence=dict(census_run_id=RUN2), generated=RUN2)).status == "appended"


def test_a_caller_verdict_is_only_a_cross_check_and_must_equal_the_census(ledger):
    refused(ledger, "census_mismatch", cell=dict(v="FAIL"))                       # caller PASS, census FAIL
    refused(ledger, "census_mismatch", verdict="FAIL", cell=dict(v="PASS"))
    refused(ledger, "census_mismatch", verdict="PARTIAL", cell=dict(v="PASS"))
    r = nc.write_certification(**kw(ledger, verdict=None, cell=dict(v="FAIL"), semantic_fingerprint=None,
                                    writer_files=...))
    assert r.record["verdict"] == "FAIL"                                          # derived, caller said nothing


def test_the_census_cell_must_carry_a_recordable_verdict(ledger):
    refused(ledger, "census_mismatch", verdict=None, cell=dict(v="NOT_GENERIC"))
    refused(ledger, "census_mismatch", verdict=None, cell=dict(v=None))
    refused(ledger, "census_mismatch", verdict=None, cell=dict(v=["PASS"]))


def test_the_census_must_hold_exactly_that_asset_and_layer(ledger):
    cm = {"Build.registered": dict(v="PASS", measured="m")}
    refused(ledger, "census_mismatch", census_path=write_census_file(cm, asset="bg_other"))
    refused(ledger, "census_mismatch", census_path=write_census_file(cm, layer="L1"))
    p = ENV.ctrl / "two.json"
    rec = dict(asset_id="bg_ontology", measurements=cm)
    p.write_text(json.dumps(dict(generated=RUN, layer="L0", assets=[rec, rec])))
    refused(ledger, "census_mismatch", census_path=p)
    q = ENV.ctrl / "none.json"
    q.write_text(json.dumps(dict(generated=RUN, layer="L0")))
    refused(ledger, "census_mismatch", census_path=q)
    r = ENV.ctrl / "nomeas.json"
    r.write_text(json.dumps(dict(generated=RUN, layer="L0", assets=[dict(asset_id="bg_ontology")])))
    refused(ledger, "census_mismatch", census_path=r)


def test_a_census_measurement_flagged_inconclusive_blocks_a_pass(ledger):
    refused(ledger, "inconclusive", cell=dict(inconclusive=True))


def test_inconclusive_and_transitive_only_are_stored_and_are_currency(ledger):
    r = nc.write_certification(**kw(ledger, verdict="FAIL", criterion="Build.dag",
                                    cell=dict(inconclusive=True, transitive_only=True), semantic_fingerprint=None,
                                    writer_files=...))
    assert r.record["inconclusive"] is True and r.record["transitive_only"] is True
    r2 = nc.write_certification(**kw(ledger, verdict="FAIL", criterion="Build.dag", cell=dict(), semantic_fingerprint=None,
                                     writer_files=...))
    assert r2.status == "appended" and r2.record["generation"] == 2
    assert r2.record["inconclusive"] is False and r2.record["transitive_only"] is False


# ───────────────────────── registry binding of the census (item 3) ─────────────────────────

def test_census_registry_fields_must_match_the_current_registry_when_present(ledger):
    rr, fp = ac.REGISTRY_REVISION, ac.registry_fingerprint()
    refused(ledger, "census_mismatch", head=dict(registry_revision=rr + 1, registry_fingerprint=fp))
    refused(ledger, "census_mismatch", head=dict(registry_revision=rr, registry_fingerprint="0" * 64))
    refused(ledger, "census_mismatch", head=dict(registry_revision=rr))                  # half a binding
    refused(ledger, "census_mismatch", head=dict(registry_fingerprint=fp))
    refused(ledger, "census_mismatch", head=dict(registry_revision=True, registry_fingerprint=fp))
    refused(ledger, "census_mismatch", head=dict(registry_revision="7", registry_fingerprint=fp))
    rec = nc.write_certification(**kw(ledger, head=dict(registry_revision=rr, registry_fingerprint=fp))).record
    assert rec["registry_binding"] == "census_bound"


def test_a_census_without_registry_fields_is_recorded_as_unbound_and_binding_is_currency(ledger):
    a = nc.write_certification(**kw(ledger))
    assert a.record["registry_binding"] == "census_unbound"
    again = nc.write_certification(**kw(ledger))
    assert again.status == "unchanged"
    b = nc.write_certification(**kw(ledger, head=dict(registry_revision=ac.REGISTRY_REVISION,
                                                      registry_fingerprint=ac.registry_fingerprint())))
    assert b.status == "appended" and b.record["generation"] == 2 and b.record["registry_binding"] == "census_bound"


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


def test_r4_pass_on_a_criterion_the_census_facts_disprove_is_refused(ledger):
    # the census record's target_columns carry no citation column: Ldgr.source_presence is NOT_APPLICABLE, so a
    # measured PASS contradicts the registry
    refused(ledger, "not_applicable_pass", criterion="Ldgr.source_presence", rec=dict(target_columns=["a", "b"]))


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


def test_r5_unknown_basis_is_refused(ledger):
    refused(ledger, "bad_basis", cell=dict(basis="Declaration"))
    refused(ledger, "bad_basis", cell=dict(basis="measured"))


def test_pass_basis_declaration_without_census_refused(ledger):
    """A PASS by declaration comes from the census cell, never from the caller."""
    refused(ledger, "census_mismatch", basis="declaration")                       # typed; the cell carries none
    refused(ledger, "census_required", basis="declaration", census_path=None)
    refused(ledger, "bad_basis", kind="addition", criterion="D-DECL", detector="d.py", criterion_version=1,
            basis="declaration")


def test_pass_by_declaration_is_taken_from_the_census_cell_where_the_registry_defines_it(ledger):
    svc = dict(criterion="Build.target", cell=dict(basis="declaration"), rec=dict(asset_kind="service", has_writer=False),
               writer_files=..., writer_hashes_reason="service_no_writer")
    rec = nc.write_certification(**kw(ledger, **svc)).record
    assert rec["verdict"] == "PASS" and rec["basis"] == "declaration"
    # the same declaration on an asset kind / criterion the registry does not define it for is refused
    refused(ledger, "bad_basis", **dict(svc, rec=dict(asset_kind="data", has_writer=False)))
    refused(ledger, "bad_basis", **dict(svc, criterion="Build.dag"))                 # a different criterion
    # a caller basis is only a cross-check: it may restate the cell's basis, never supply or contradict it
    d = kw(ledger, **dict(svc, asset="bg_panchanga", basis="declaration"))
    assert nc.write_certification(**d).record["basis"] == "declaration"
    refused(ledger, "census_mismatch", **dict(svc, asset="bg_third", cell=dict(basis="declaration"), basis="other"))


# ───────────────────────── R6: what makes a PASS able to go stale ─────────────────────────

def test_r6_pass_needs_a_semantic_fingerprint(ledger):
    refused(ledger, "missing_fingerprint", semantic_fingerprint=None)
    refused(ledger, "bad_fingerprint", semantic_fingerprint="abc")
    refused(ledger, "bad_fingerprint", semantic_fingerprint="Z" * 64)
    refused(ledger, "bad_fingerprint", semantic_fingerprint="A" * 64)     # canonical form is lower-case hex
    refused(ledger, "bad_fingerprint", semantic_fingerprint=["a" * 64])


def test_r6_fail_may_carry_no_fingerprint_but_a_given_one_is_validated(ledger):
    r = nc.write_certification(**kw(ledger, verdict="FAIL", semantic_fingerprint=None, writer_files=...))
    assert r.record["semantic_fingerprint"] is None and r.record["writer_hashes"] == {}
    assert r.record["writer_hashes_verified"] is None
    refused(ledger, "bad_fingerprint", verdict="FAIL", semantic_fingerprint="nope", criterion="Build.contract")


def test_r6_pass_needs_writer_hashes_or_a_stated_reason(ledger):
    refused(ledger, "missing_writer_hashes", writer_files=...)
    refused(ledger, "missing_writer_hashes", writer_files=[], writer_hashes={})
    refused(ledger, "missing_writer_hashes", writer_files=..., writer_hashes_reason="  ", rec=dict(has_writer=False))
    r = nc.write_certification(**kw(ledger, writer_files=..., writer_hashes_reason="service asset: no writer file",
                                    rec=dict(has_writer=False)))
    assert r.record["writer_hashes"] == {} and r.record["writer_hashes_reason"].startswith("service asset")


def test_r6_malformed_writer_hashes_are_refused(ledger):
    for bad in ({"/abs/path.py": "c" * 64}, {"../up.py": "c" * 64}, {"a/b.py": "short"}, {"a/b.py": "C" * 64},
                ["a/b.py"], {"": "c" * 64}, {"a//b.py": "c" * 64}):
        refused(ledger, "bad_writer_hashes", writer_files=..., writer_hashes=bad)
    refused(ledger, "bad_writer_hashes", writer_files="a/b.py")                      # a bare string, not a list
    refused(ledger, "bad_writer_hashes", writer_files=["../x.py"])
    refused(ledger, "bad_writer_hashes", writer_files=["platform/missing.py"])       # not a file in the repo


def test_writer_hashes_reason_is_refused_when_the_census_says_the_asset_has_a_writer(ledger):
    refused(ledger, "writer_reason_refused", writer_files=..., writer_hashes_reason="service asset: no writer file")
    refused(ledger, "writer_reason_refused", writer_files=..., writer_hashes_reason="service_no_writer")
    refused(ledger, "writer_reason_refused", verdict="FAIL", semantic_fingerprint=None, writer_files=...,
            writer_hashes_reason="no writer, honest")                                 # refused on any verdict


def test_a_census_without_has_writer_admits_only_the_documented_reasons(ledger):
    assert set(nc.WRITER_REASONS) == {"service_no_writer", "global_reference_data"}
    refused(ledger, "writer_reason_refused", writer_files=..., rec=dict(has_writer=...),
            writer_hashes_reason="trust me, no writer")
    r = nc.write_certification(**kw(ledger, writer_files=..., rec=dict(has_writer=...),
                                    writer_hashes_reason="global_reference_data"))
    assert r.record["writer_hashes_reason"] == "global_reference_data"


def test_typed_writer_hash_mismatching_the_file_is_refused(ledger):
    refused(ledger, "writer_hash_mismatch", writer_files=..., writer_hashes={W1: "d" * 64})          # repo given
    refused(ledger, "writer_hash_mismatch", writer_files=[W1], writer_hashes={W1: "d" * 64})
    ok = nc.write_certification(**kw(ledger, writer_files=..., writer_hashes=dict(WH))).record
    assert ok["writer_hashes"] == WH and ok["writer_hashes_verified"] is True


def test_typed_writer_hashes_with_no_repo_to_verify_against_do_not_satisfy_a_pass(ledger):
    refused(ledger, "unverified_writer_hashes", writer_files=..., writer_repo=..., writer_hashes=dict(WH))
    # a verdict that needs no writer evidence stores them honestly as unverified
    r = nc.write_certification(**kw(ledger, verdict="FAIL", semantic_fingerprint=None, writer_files=..., writer_repo=...,
                                    writer_hashes=dict(WH)))
    assert r.record["writer_hashes"] == WH and r.record["writer_hashes_verified"] is False


def test_computed_hashes_are_verified_and_win_the_merge(ledger):
    r = nc.write_certification(**kw(ledger, writer_files=[W1, W2])).record
    assert r.get("writer_hashes") == {W1: sha(W1_BYTES), W2: sha(W2_BYTES)} and r["writer_hashes_verified"] is True


def test_r6_hash_writer_files_working_tree_and_committed_ref(tmp_path):
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

NA_COLS = ["id", "name"]                                  # no citation column -> Ldgr.source_presence#columns_any
NA_RID = "Ldgr.source_presence#columns_any"


def na_kw(ledger, **over):
    base = dict(criterion="Ldgr.source_presence", verdict="N/A", na_rule_id=NA_RID, cell=...,
                rec=dict(target_columns=list(NA_COLS)), semantic_fingerprint=None, writer_files=...)
    base.update(over)
    return base


def na_call(ledger, **over):
    return nc.write_certification(**kw(ledger, **na_kw(ledger, **over)))


def na_refused(ledger, code, **over):
    return refused(ledger, code, **na_kw(ledger, **over))


def test_r3_the_registry_really_yields_that_rule_id_for_those_facts():
    ap = ac.criterion_applicability("Ldgr.source_presence", "L0", dict(columns=NA_COLS))
    assert ap["state"] == "NOT_APPLICABLE" and ap["rule_id"] == NA_RID


def test_r3_na_is_refused_while_no_rule_is_declared_the_real_state_today(ledger):
    assert ac.NA_RULE_DECISIONS == {}, "N-22 declared a rule: update this test to the declared state"
    e = na_refused(ledger, "na_not_computed")
    assert "undecided" in str(e)
    assert len(lines(ledger)) == 1


def test_r3_na_computed_by_the_registry_under_a_declared_rule_is_recorded(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    rec = na_call(ledger).record
    assert rec["verdict"] == "N/A"
    assert rec["na"] == dict(rule_id=NA_RID, decision_id="N-22.test", basis="applicability_facts", cause=None,
                             facts=dict(columns=["id", "name"], asset_kind="data"))        # the CENSUS record's facts


def test_r3_a_typed_na_with_no_rule_id_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    na_refused(ledger, "na_not_computed", na_rule_id=None)
    na_refused(ledger, "na_not_computed", na_rule_id="")


def test_r3_an_absent_cell_with_no_na_claim_is_a_missing_cell_not_an_na(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    refused(ledger, "census_cell_missing", criterion="Ldgr.source_presence", verdict=None, cell=...,
            rec=dict(target_columns=list(NA_COLS)), semantic_fingerprint=None, writer_files=...)


def test_r3_a_non_na_caller_verdict_with_no_census_cell_is_not_turned_into_an_na(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    for v in ("PASS", "FAIL", "NO_DETECTOR"):
        na_refused(ledger, "census_cell_missing", verdict=v)
    assert na_call(ledger, verdict=None).record["verdict"] == "N/A"          # the rule id alone, registry-confirmed


def test_r3_a_rule_id_that_is_not_the_one_the_registry_yields_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test", "Earn.service_state#asset_kinds": "N-22.other"})
    na_refused(ledger, "na_not_computed", na_rule_id="Ldgr.source_presence#asset_kinds")
    na_refused(ledger, "na_not_computed", na_rule_id="Earn.service_state#asset_kinds")   # declared, not this criterion's
    na_refused(ledger, "na_not_computed", na_rule_id="Ldgr.source_presence#measured")
    assert "not a rule of" in str(na_refused(ledger, "na_not_computed", na_rule_id="Nope#columns_any"))


def test_r3_na_on_a_criterion_that_applies_or_is_unknown_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    na_refused(ledger, "na_not_computed", rec=dict(target_columns=["id", "source_citation"]))      # applies
    na_refused(ledger, "na_not_computed", rec=dict(target_columns=None))                            # unknown
    na_refused(ledger, "na_not_computed", rec=dict(target_columns=[]))
    na_refused(ledger, "na_not_computed", rec=dict(target_columns=...))
    na_refused(ledger, "na_not_computed", rec=dict(target_columns="id,name"))                       # unusable


def test_r3_applicability_facts_come_from_the_census_record_and_caller_facts_that_conflict_are_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    na_refused(ledger, "facts_conflict", facts=dict(columns=["id", "source_citation"]))             # census says id,name
    na_refused(ledger, "facts_conflict", facts=dict(asset_kind="service"))                          # census says data
    na_refused(ledger, "facts_conflict", facts=dict(columns_known=True))                            # not carried
    na_refused(ledger, "facts_conflict", rec=dict(target_columns=None), facts=dict(columns=list(NA_COLS)))  # caller fills a gap
    rec = na_call(ledger, facts=dict(columns=["name", "id"], asset_kind="data")).record               # agrees (any order)
    assert rec["na"]["facts"]["columns"] == ["id", "name"]
    refused(ledger, "facts_conflict", criterion="Ldgr.source_presence", rec=dict(target_columns=["a", "b"]),
            facts=dict(columns=["source_citation"]))                                               # PASS path too


def test_r3_a_declared_rule_that_the_inspector_cannot_issue_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Bogus#columns_any": "N-22.test"})
    na_refused(ledger, "na_rules_invalid")


def test_r3_na_needs_a_census_run_id_too(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    na_refused(ledger, "no_census_run_id", evidence=dict(measured="x"))


def test_r3_a_measured_record_for_the_criterion_takes_precedence_over_applicability(ledger, monkeypatch):
    # the rollup reads a measurement before any applicability rule; so must this writer
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {NA_RID: "N-22.test"})
    na_refused(ledger, "na_not_computed", cell=dict(v="PASS", measured="m"))


def test_r3_additions_have_no_registry_rule_so_no_na(ledger):
    refused(ledger, "na_not_computed", kind="addition", criterion="D-TIME", detector="d.py", verdict="N/A",
            criterion_version=1, na_rule_id="D-TIME#columns_any", semantic_fingerprint=None, writer_files=...)


MEAS_NA = "Narr.agree#measured:no-prose"


def measured_na(**over):
    base = dict(criterion="Narr.agree", verdict="N/A", na_rule_id=MEAS_NA,
                cell=dict(v="N/A", measured="no prose", cause="no-prose"))
    base.update(over)
    return base


def test_r3_a_measured_cause_na_is_recorded_only_from_the_census_cell_and_a_declared_rule(ledger, monkeypatch):
    e = refused(ledger, "na_not_computed", **measured_na())                  # rule undeclared (real state)
    assert "undecided" in str(e)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {MEAS_NA: "N-22.nr"})
    rec = nc.write_certification(**kw(ledger, **measured_na())).record
    assert rec["na"] == dict(rule_id=MEAS_NA, decision_id="N-22.nr", basis="measured_cause", cause="no-prose", facts=None)
    # the rule id and the verdict may be left to the census cell
    rec2 = nc.write_certification(**kw(ledger, **measured_na(na_rule_id=None, verdict=None, asset="bg_panchanga"))).record
    assert rec2["verdict"] == "N/A" and rec2["na"]["rule_id"] == MEAS_NA


def test_r3_a_measured_cause_na_without_the_census_cell_is_refused(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {MEAS_NA: "N-22.nr"})
    refused(ledger, "census_required", **measured_na(census_path=None))
    refused(ledger, "na_not_computed", **measured_na(cell=...))              # applicability path: not a rule form


def test_r3_measured_na_cause_must_match_census_and_be_registered(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {MEAS_NA: "N-22.nr"})
    e = refused(ledger, "na_not_computed", **measured_na(cell=dict(v="N/A", cause="never-attempted")))
    assert "registered N/A cause" in str(e)
    e = refused(ledger, "na_not_computed", **measured_na(verdict=None, na_rule_id=None,
                                                        cell=dict(v="N/A", cause="never-attempted")))
    assert "registered N/A cause" in str(e)                      # named as unregistered, not merely undeclared
    refused(ledger, "na_not_computed", **measured_na(cell=dict(v="PASS", measured="m")))
    refused(ledger, "na_not_computed", **measured_na(na_rule_id="Narr.agree#measured:made-up"))
    refused(ledger, "na_not_computed", **measured_na(cell=dict(v="N/A", cause=None)))
    refused(ledger, "na_not_computed", **measured_na(verdict=None, na_rule_id=None, cell=dict(v="N/A", cause="made-up")))


def test_r3_a_declared_rule_id_of_another_criterion_cannot_release_this_one(ledger, monkeypatch):
    # Narr.checkable shares the cause slug `no-prose`; its declared rule must not release a Narr.agree record
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Narr.checkable#measured:no-prose": "N-22.nr"})
    refused(ledger, "na_not_computed", **measured_na(na_rule_id="Narr.checkable#measured:no-prose"))


def test_r3_measured_na_needs_a_fingerprint_because_the_measurement_read_rows(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {MEAS_NA: "N-22.nr"})
    refused(ledger, "missing_fingerprint", **measured_na(semantic_fingerprint=None))


def test_r3_measured_na_needs_writer_hashes_too(ledger, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {MEAS_NA: "N-22.nr"})
    refused(ledger, "missing_writer_hashes", **measured_na(writer_files=...))


# ───────────────────────── additions ─────────────────────────

def add_kw(ledger, **over):
    base = dict(kind="addition", criterion="D-GROUNDING", detector="grounding_probe.py", criterion_version=1)
    base.update(over)
    return base


def add_call(ledger, **over):
    return nc.write_certification(**kw(ledger, **add_kw(ledger, **over)))


def add_refused(ledger, code, **over):
    return refused(ledger, code, **add_kw(ledger, **over))


def test_additions_are_recorded_with_their_own_detector_and_version(ledger):
    rec = add_call(ledger).record
    assert rec["kind"] == "addition" and rec["gate"] is None and rec["detector"] == "grounding_probe.py"
    assert rec["criterion_version"] == 1 and rec["registry_revision"] is None and rec["registry_fingerprint"] is None
    assert rec["cert_id"] == "bg_ontology|addition|D-GROUNDING@1"
    assert rec["registry_binding"] is None and rec["cross_checked"] is False
    assert "census_sha256" not in rec["evidence"]


def test_an_addition_verdict_is_the_callers_and_is_required(ledger):
    add_refused(ledger, "bad_verdict", verdict=None)
    add_refused(ledger, "bad_verdict", verdict="pass")
    assert add_call(ledger, verdict="FAIL", semantic_fingerprint=None, writer_files=...).record["verdict"] == "FAIL"


@pytest.mark.parametrize("det", [None, "", "  ", "NONE", "none", "None", "ＮＯＮＥ", "ｎｏｎｅ", "N​ONE", "NO­NE",
                                 "​", " NONE ", "﻿NONE", " ⁠ ", "N‍O‌NE", "---"])
def test_additions_never_pass_without_a_real_detector(ledger, det):
    add_refused(ledger, "detector_none", detector=det)


def test_a_non_ascii_detector_is_refused_as_a_possible_homoglyph(ledger):
    add_refused(ledger, "bad_detector", detector="dеtector.py")                # Cyrillic e
    add_refused(ledger, "bad_detector", detector="NОНE")                       # Cyrillic О, Н


def test_additions_need_a_version_and_a_well_formed_id(ledger):
    add_refused(ledger, "bad_criterion_version", criterion_version=None)
    add_refused(ledger, "bad_criterion_version", criterion_version=0)
    add_refused(ledger, "bad_criterion_version", criterion_version="1")
    add_refused(ledger, "bad_criterion_version", criterion_version=True)
    add_refused(ledger, "bad_criterion_version", criterion_version=1.0)
    add_refused(ledger, "bad_criterion_id", criterion="has space|pipe@1")


@pytest.mark.parametrize("crit", ["Build.registered", "build.registered", "BUILD.REGISTERED", "bUiLd.ReGiStErEd",
                                  "ＢＵＩＬＤ.registered", "Build.registered​", "ＢＵＩＬＤ．ｒｅｇｉｓｔｅｒｅｄ"])
def test_an_addition_id_cannot_shadow_a_registered_criterion_by_case_or_unicode(ledger, crit):
    add_refused(ledger, "bad_criterion_id", criterion=crit)


@pytest.mark.parametrize("crit", ["D-GROUNDÍNG", "D-​TIME", "D-ТIME", "é", "D-GROUNDING\n", "D-G\x00"])
def test_addition_ids_must_be_ascii(ledger, crit):
    e = add_refused(ledger, "bad_criterion_id", criterion=crit)
    assert ("non-ASCII" in str(e)) == (not crit.isascii())


def test_an_addition_may_cite_a_census_file_for_its_run_id_and_it_is_then_checked_and_hashed(ledger):
    p = write_census_file({}, name="add.json")
    rec = add_call(ledger, census_path=p).record
    assert rec["evidence"]["census_sha256"] == sha(p.read_bytes()) and rec["cross_checked"] is False
    add_refused(ledger, "census_run_id_mismatch", census_path=write_census_file({}, generated=RUN2), asset="bg_other")
    add_refused(ledger, "census_unsourced", census=dict(generated=RUN), asset="bg_third")
    outside = write_census_file({}, directory=ENV.tmp, name="outside.json")
    add_refused(ledger, "census_untrusted", census_path=outside, asset="bg_fourth")


def test_an_addition_writer_hashes_reason_must_be_a_documented_one(ledger):
    add_refused(ledger, "writer_reason_refused", writer_files=..., writer_hashes_reason="no writer")
    r = add_call(ledger, writer_files=..., writer_hashes_reason="service_no_writer")
    assert r.record["writer_hashes_reason"] == "service_no_writer"


def test_a_gate_record_cannot_claim_a_criterion_version_that_is_not_the_registrys(ledger):
    refused(ledger, "bad_criterion_version", criterion_version=99)
    refused(ledger, "bad_criterion_version", criterion_version=True)                 # True == 1 must not pass
    assert nc.write_certification(**kw(ledger, criterion_version=ac.CRITERION_REGISTRY["Build.registered"]["revision"])
                                  ).status == "appended"


# ───────────────────────── type confusion is a refusal, never a TypeError ─────────────────────────

@pytest.mark.parametrize("over,code", [
    (dict(layer=["L0"]), "bad_layer"),
    (dict(layer={"L0": 1}), "bad_layer"),
    (dict(layer=None), "bad_layer"),
    (dict(kind=["gate"]), "bad_kind"),
    (dict(asset=["bg_x"]), "bad_asset"),
    (dict(asset=None), "bad_asset"),
    (dict(criterion=["Build.registered"]), "unregistered_criterion"),
    (dict(criterion=None), "unregistered_criterion"),
    (dict(verdict=["PASS"]), "bad_verdict"),
    (dict(verdict={"v": "PASS"}), "bad_verdict"),
    (dict(criterion_version=True), "bad_criterion_version"),
    (dict(criterion_version=[1]), "bad_criterion_version"),
    (dict(facts={"columns": {"a", "b"}}), "bad_facts"),
    (dict(facts=["columns"]), "bad_facts"),
    (dict(facts={"columns": [object()]}), "bad_facts"),
    (dict(facts={"columns": float("nan")}), "bad_facts"),
    (dict(verified_on=5), "bad_verified_on"),
    (dict(verified_by=5), "bad_verified_by"),
    (dict(job_image_tag=5), "bad_job_image_tag"),
    (dict(semantic_fingerprint=["a" * 64]), "bad_fingerprint"),
    (dict(semantic_fingerprint=5), "bad_fingerprint"),
    (dict(writer_files=[5]), "bad_writer_hashes"),
    (dict(writer_files=...,  writer_hashes={5: "c" * 64}), "bad_writer_hashes"),
    (dict(writer_files=..., writer_hashes={W1: ["c" * 64]}), "bad_writer_hashes"),
    (dict(writer_hashes_reason=5), "bad_writer_hashes"),
    (dict(upstream_cert_ids=[["x"]]), "bad_upstream"),
    (dict(upstream_cert_ids=[{"a": 1}]), "bad_upstream"),
    (dict(upstream_cert_ids=5), "bad_upstream"),
    (dict(inconclusive="yes"), "bad_request"),
    (dict(inconclusive=["x"]), "bad_request"),
    (dict(basis=["declaration"]), "census_mismatch"),
    (dict(evidence=dict(census_run_id=RUN, measured=["x"])), "bad_evidence"),
    (dict(evidence={5: "x", "census_run_id": RUN}), "bad_evidence"),
    (dict(gate=["Build"]), "gate_mismatch"),
    (dict(detector=["asset_census.py:measure()"]), "detector_mismatch"),
    (dict(census_path=5), "bad_census"),
])
def test_malformed_input_types_are_refusals_not_exceptions(ledger, over, code):
    refused(ledger, code, **over)


def test_unserialisable_facts_on_an_addition_and_a_nan_evidence_are_refusals(ledger):
    add_refused(ledger, "bad_facts", facts={"columns": {"a"}})
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, measured=float("nan")))


# ───────────────────────── idempotence + append-only (3) ─────────────────────────

EXPECTED_CURRENCY = {"verdict", "criterion_version", "registry_revision", "registry_fingerprint", "registry_binding",
                     "detector", "writer_hashes", "writer_hashes_verified", "writer_hashes_reason", "upstream_cert_ids",
                     "semantic_fingerprint", "na", "basis", "inconclusive", "transitive_only"}
PROVENANCE_ONLY = {"evidence", "job_image_tag", "verified_by", "verified_on", "cross_checked", "prev_sha256", "cert_id",
                   "cert_key", "generation", "asset", "layer", "kind", "gate", "criterion", "record_version"}


def test_the_currency_fields_are_exactly_the_documented_set_and_provenance_is_excluded():
    assert len(nc.CURRENCY_FIELDS) == len(set(nc.CURRENCY_FIELDS))
    assert set(nc.CURRENCY_FIELDS) == EXPECTED_CURRENCY
    assert not (set(nc.CURRENCY_FIELDS) & PROVENANCE_ONLY)


def test_rewriting_the_identical_record_appends_nothing(ledger):
    r1 = nc.write_certification(**kw(ledger))
    snap = ledger.read_bytes()
    r2 = nc.write_certification(**kw(ledger))
    assert r1.status == "appended" and r2.status == "unchanged"
    assert r2.record == r1.record and r2.cert_id == r1.cert_id
    assert ledger.read_bytes() == snap


def test_a_remeasurement_that_changes_no_currency_field_appends_nothing(ledger):
    # same verdict, writer hashes, upstream, semantic fingerprint under a NEWER census run (a different census file,
    # other evidence text, another operator): an idempotent rebuild must leave every downstream certificate current
    # (arch 12.16), so no new generation
    nc.write_certification(**kw(ledger))
    snap = ledger.read_bytes()
    r = nc.write_certification(**kw(ledger, evidence=dict(census_run_id=RUN2, measured="different words",
                                                          inspector_commit="abc123", note="n"),
                                    generated=RUN2, verified_by="someone-else",
                                    verified_on="2026-10-05T00:00:00+05:30", job_image_tag="img-9",
                                    cell=dict(measured="other measurement text")))
    assert r.status == "unchanged" and r.record["generation"] == 1
    assert r.record["evidence"]["census_run_id"] == RUN                  # provenance of the generation that first carried it
    assert ledger.read_bytes() == snap


@pytest.mark.parametrize("change", [
    dict(semantic_fingerprint=FP2),
    dict(writer_files=[W2]),
    dict(writer_files=[W1, W2]),
    dict(verdict="FAIL"),
    dict(verdict="PARTIAL"),
    dict(head=dict(registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint())),
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
    refused(ledger, "census_required", census_path=None)
    assert len(lines(ledger)) == 2


def test_concurrent_identical_writers_append_exactly_one_record(ledger):
    import threading
    n, results, errs = 12, [], []
    gate = threading.Barrier(n)
    reqs = [kw(ledger) for _ in range(n)]                               # census files built up front

    def go(i):
        try:
            gate.wait()
            results.append(nc.write_certification(**reqs[i]).status)
        except Exception as e:                                          # noqa: BLE001
            errs.append(e)

    ts = [threading.Thread(target=go, args=(i,)) for i in range(n)]
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
    req = kw(ledger)
    with open(ledger, "rb") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        t = threading.Thread(target=lambda: out.append(nc.write_certification(**req).status))
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


def test_stale_upstream_refused_even_when_the_record_is_otherwise_identical(ledger):
    up = upstream_ledger(ledger)
    nc.write_certification(**kw(ledger, upstream_cert_ids=[up]))                              # X@1 resting on dep@1
    nc.write_certification(**kw(ledger, asset="bg_dependency", semantic_fingerprint=FP2))     # dep@1 superseded
    assert nc.write_certification(**kw(ledger, upstream_cert_ids=["bg_dependency|gate|Build.registered@2"])
                                  ).record["generation"] == 2
    refused(ledger, "upstream_stale", upstream_cert_ids=[up])         # identical to nothing: the cited id is stale
    nc.write_certification(**kw(ledger, asset="bg_dependency", semantic_fingerprint="c" * 64))     # dep@3
    refused(ledger, "upstream_stale", upstream_cert_ids=["bg_dependency|gate|Build.registered@2"])   # == X@2's own citation


def test_r7_a_pass_cannot_rest_on_a_non_passing_upstream(ledger):
    nc.write_certification(**kw(ledger, asset="bg_dependency", verdict="FAIL", semantic_fingerprint=None,
                                writer_files=...))
    refused(ledger, "upstream_not_passing", upstream_cert_ids=["bg_dependency|gate|Build.registered@1"])
    # a FAIL record may name it (it records a fact about a failing chain, it certifies nothing)
    r = nc.write_certification(**kw(ledger, verdict="FAIL", semantic_fingerprint=None, writer_files=...,
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
    refused(tmp_path / "no_dir" / "x.jsonl", "ledger_missing", init=True)               # parent missing: a refusal


def test_r9_init_creates_the_ledger_with_a_schema_line_first(tmp_path):
    p = tmp_path / "new.jsonl"
    nc.write_certification(**kw(p, init=True))
    rows = lines(p)
    assert rows[0]["asset"] == "_schema" and "append-only" in rows[0]["_doc"].lower()
    assert rows[1]["generation"] == 1
    nc.write_certification(**kw(p, init=True))                              # init never rewrites an existing ledger
    assert len(lines(p)) == 2


def test_the_schema_row_and_the_append_are_byte_stable(tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    d = kw(a, init=True)
    nc.write_certification(**d)
    nc.write_certification(**dict(d, ledger_path=b))
    assert a.read_bytes() == b.read_bytes()                                  # same request, same bytes, both lines
    schema = a.read_bytes().split(b"\n")[0]
    assert schema == (json.dumps({"asset": "_schema", "_doc": nc.SCHEMA_DOC}, ensure_ascii=False)).encode()
    snap = a.read_bytes()
    nc.write_certification(**d)
    assert a.read_bytes() == snap


def test_r9_a_refused_request_does_not_create_the_ledger_even_with_init(tmp_path):
    p = tmp_path / "new.jsonl"
    with pytest.raises(nc.CertificationRefused):
        nc.write_certification(**kw(p, init=True, criterion="Carr.D1"))
    assert not p.exists()
    refused(p, "census_required", init=True, census_path=None)
    assert not p.exists()


def test_zero_byte_ledger_with_init_recovers(tmp_path):
    p = tmp_path / "zero.jsonl"
    p.write_bytes(b"")
    nc.write_certification(**kw(p, init=True))
    rows = lines(p)
    assert rows[0]["asset"] == "_schema" and rows[1]["generation"] == 1 and rows[1]["prev_sha256"] == sha(
        p.read_bytes().split(b"\n")[0])
    assert nc.write_certification(**kw(p, init=True)).status == "unchanged"


def test_zero_byte_ledger_without_init_is_refused_and_a_refused_init_never_removes_a_pre_existing_file(tmp_path):
    p = tmp_path / "zero.jsonl"
    p.write_bytes(b"")
    refused(p, "bad_ledger")
    refused(p, "upstream_unknown", init=True, upstream_cert_ids=["bg_x|gate|Build.registered@1"])
    refused(p, "detector_none", init=True, criterion="Carr.D1")
    assert p.exists() and p.read_bytes() == b""                              # untouched, NOT unlinked


def test_a_symlinked_ledger_path_is_refused_and_neither_link_nor_target_changes(ledger, tmp_path):
    link = tmp_path / "link.jsonl"
    link.symlink_to(ledger)
    refused(link, "bad_ledger_path")
    refused(link, "bad_ledger_path", init=True)
    assert link.is_symlink() and len(lines(ledger)) == 1


def test_a_dangling_symlink_ledger_path_is_refused_and_creates_nothing(tmp_path):
    target = tmp_path / "nowhere.jsonl"
    link = tmp_path / "dangling.jsonl"
    link.symlink_to(target)
    refused(link, "bad_ledger_path", init=True)
    assert link.is_symlink() and not target.exists()
    refused(link, "bad_ledger_path")                                         # without init as well
    assert not target.exists()


def test_a_directory_as_the_ledger_path_is_refused(tmp_path):
    d = tmp_path / "adir"
    d.mkdir()
    for init in (False, True):
        with pytest.raises(nc.CertificationRefused) as ei:
            nc.write_certification(**kw(d, init=init))
        assert ei.value.code == "bad_ledger_path"
    assert d.is_dir() and not list(d.iterdir())


def test_r9_malformed_or_unreadable_ledgers_are_refused(ledger):
    ledger.write_text(ledger.read_text() + "{not json\n")
    refused(ledger, "bad_ledger")


def test_r9_non_utf8_and_duplicate_key_ledger_lines_are_refused(ledger):
    ledger.write_bytes(ledger.read_bytes() + b'{"asset": "\xff"}\n')
    refused(ledger, "bad_ledger")
    ledger.write_bytes(ledger.read_bytes().split(b"\n")[0] + b'\n{"asset": "x", "asset": "y"}\n')
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


def three_records(ledger):
    nc.write_certification(**kw(ledger))                                     # A@1
    nc.write_certification(**kw(ledger, criterion="Build.contract"))         # B@1
    nc.write_certification(**kw(ledger, semantic_fingerprint=FP2))           # A@2


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


def rechain(parts):
    """Rebuild a ledger from raw lines with CORRECT prev_sha256 values: what a forger who knows the chain would write."""
    out, prev = [parts[0]], sha(parts[0])
    for raw in parts[1:]:
        if not raw.strip():
            continue
        r = dict(json.loads(raw), prev_sha256=prev)
        line = json.dumps(r, ensure_ascii=False).encode()
        out.append(line)
        prev = sha(line)
    return b"\n".join(out) + b"\n"


def test_a_forger_who_recomputes_the_chain_is_still_stopped_by_the_generation_and_id_checks(ledger):
    three_records(ledger)
    parts = ledger.read_bytes().split(b"\n")                         # [schema, A1, B1, A2, b""]
    ledger.write_bytes(rechain(parts))
    assert len(nc.read_ledger(ledger)) == 2                           # the rechain helper itself yields a valid ledger
    ledger.write_bytes(rechain([parts[0], parts[2], parts[3]]))       # A1 removed, A2 stays (chain valid, gap in 1..n)
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger" and "generations" in str(ei.value)
    bad = json.loads(parts[1])
    bad["cert_id"] = "bg_ontology|gate|Build.registered@9"
    ledger.write_bytes(rechain([parts[0], json.dumps(bad).encode(), parts[2], parts[3]]))
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger" and "cert_key/generation/cert_id" in str(ei.value)


def test_each_record_chains_the_sha256_of_the_previous_line(ledger):
    three_records(ledger)
    raw = ledger.read_bytes().split(b"\n")
    rows = lines(ledger)
    assert [r["prev_sha256"] for r in rows[1:]] == [sha(raw[0]), sha(raw[1]), sha(raw[2])]
    assert len(nc.read_ledger(ledger)) == 2


def test_edit_of_earlier_record_detected(ledger):
    three_records(ledger)
    good = ledger.read_bytes()
    parts = good.split(b"\n")
    edited = parts[1].replace(b'"verdict": "PASS"', b'"verdict": "FAIL"')
    assert edited != parts[1]
    ledger.write_bytes(b"\n".join([parts[0], edited] + parts[2:]))
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "bad_ledger" and "chain" in str(ei.value)
    before = ledger.read_bytes()
    refused(ledger, "bad_ledger")
    assert ledger.read_bytes() == before


def test_edit_of_the_schema_row_and_deletion_or_reordering_are_detected(ledger):
    three_records(ledger)
    parts = ledger.read_bytes().split(b"\n")                                  # [schema, A1, B1, A2, b""]
    for tampered in (
        [parts[0].replace(b"test ledger", b"other ledger"), *parts[1:]],       # schema row edited
        [parts[0], parts[2], parts[1], parts[3], parts[4]],                     # reordered (generations stay valid)
        [parts[0], parts[2], parts[3], parts[4]],                               # first record deleted
        [parts[0], parts[1], parts[3], parts[4]],                               # a middle record deleted
    ):
        ledger.write_bytes(b"\n".join(tampered))
        with pytest.raises(nc.CertificationRefused) as ei:
            nc.read_ledger(ledger)
        assert ei.value.code == "bad_ledger"


def test_a_record_without_a_chain_field_or_a_second_schema_row_is_refused(ledger):
    nc.write_certification(**kw(ledger))
    parts = ledger.read_bytes().split(b"\n")
    rec = json.loads(parts[1])
    rec.pop("prev_sha256")
    ledger.write_bytes(parts[0] + b"\n" + json.dumps(rec).encode() + b"\n")
    refused(ledger, "bad_ledger")
    ledger.write_bytes(b"\n".join(parts[:2]) + b"\n" + parts[0] + b"\n")
    refused(ledger, "bad_ledger")


def test_torn_partial_json_last_line_refused_and_not_extended(ledger):
    nc.write_certification(**kw(ledger))
    torn = ledger.read_bytes() + b'{"asset": "bg_ontology", "layer": "L0", "ki'
    ledger.write_bytes(torn)
    e = refused(ledger, "torn_ledger", semantic_fingerprint=FP2)
    assert "torn" in str(e).lower()
    assert ledger.read_bytes() == torn                                       # not extended, not repaired
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.read_ledger(ledger)
    assert ei.value.code == "torn_ledger"


def test_r9_a_last_line_with_no_newline_is_appended_after_not_glued_to(ledger):
    nc.write_certification(**kw(ledger))
    ledger.write_bytes(ledger.read_bytes().rstrip(b"\n"))
    r = nc.write_certification(**kw(ledger, semantic_fingerprint=FP2))
    assert r.record["generation"] == 2 and len(lines(ledger)) == 3
    assert len(nc.read_ledger(ledger)["bg_ontology|gate|Build.registered"]) == 2      # the chain still verifies


def test_an_unexpected_exception_while_building_the_record_is_a_refusal_not_a_crash(ledger, monkeypatch):
    def boom(**_):
        raise TypeError("unhashable type: 'list'")
    monkeypatch.setattr(nc, "build_record", boom)
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**kw(ledger))
    assert ei.value.code == "bad_request" and ledger.read_bytes() == before


def test_a_refused_init_never_even_creates_the_file(tmp_path, monkeypatch):
    created = []
    real_open = os.open

    def spy(path, flags, *a, **k):
        if flags & os.O_CREAT:
            created.append(path)
        return real_open(path, flags, *a, **k)

    monkeypatch.setattr(os, "open", spy)
    p = tmp_path / "fresh.jsonl"
    refused(p, "upstream_unknown", init=True, upstream_cert_ids=["bg_x|gate|Build.registered@1"])
    assert created == [] and not p.exists()                         # validated against an empty ledger BEFORE creating
    nc.write_certification(**kw(p, init=True))
    assert created == [p]


def test_r9_evidence_that_cannot_be_serialised_is_refused_before_any_write(ledger):
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, measured={"a", "set"}))
    refused(ledger, "bad_evidence", evidence=dict(census_run_id=RUN, secret_extra="x"))


def test_r9_a_refusal_under_init_on_a_fresh_ledger_leaves_no_file_behind(tmp_path):
    p = tmp_path / "fresh.jsonl"
    e = refused(p, "upstream_unknown", init=True, upstream_cert_ids=["bg_x|gate|Build.registered@1"])
    assert not p.exists()


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


def cli_args(ledger, *extra, cell=None, census=True):
    """A valid CLI PASS: census file under the tmp archive dir, writer hashes computed from the tmp repo."""
    args = ["--ledger", str(ledger), "--asset", "bg_ontology", "--layer", "L0", "--criterion", "Build.registered",
            "--verdict", "PASS", "--measured", "registered writer agrees",
            "--verified-by", "census-run", "--semantic-fingerprint", FP,
            "--writer-repo", str(ENV.repo), "--writer-file", W1, "--verified-on", "2026-10-01T11:00:00+05:30",
            "--census-archive-dir", str(ENV.ctrl)]
    if census:
        cf = write_census_file({"Build.registered": dict(v="PASS", measured="m", **(cell or {}))})
        args += ["--census", str(cf)]
    return args + list(extra)


def test_cli_appends_then_reports_unchanged_and_exits_zero(ledger):
    p = cli(cli_args(ledger))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["status"] == "appended" and out["cert_id"] == "bg_ontology|gate|Build.registered@1"
    q = cli(cli_args(ledger))
    assert q.returncode == 0 and json.loads(q.stdout)["status"] == "unchanged"
    assert len(lines(ledger)) == 2
    assert lines(ledger)[1]["evidence"]["census_run_id"] == RUN              # derived from the census file


def test_cli_refusal_exits_2_names_the_code_and_writes_nothing(ledger):
    before = ledger.read_bytes()
    args = cli_args(ledger)
    args[args.index("Build.registered")] = "Carr.D1"
    p = cli(args)
    assert p.returncode == 2 and "detector_none" in p.stderr
    assert ledger.read_bytes() == before


def test_cli_a_pass_with_no_census_file_is_refused_and_the_ledger_is_unchanged(ledger):
    before = ledger.read_bytes()
    p = cli(cli_args(ledger, "--census-run-id", RUN, census=False))
    assert p.returncode == 2 and "census_required" in p.stderr
    assert ledger.read_bytes() == before


def test_cli_missing_run_id_exits_2(ledger):
    p = cli(cli_args(ledger, census=False))
    assert p.returncode == 2 and "no_census_run_id" in p.stderr
    assert len(lines(ledger)) == 1


def test_cli_an_explicit_run_id_that_differs_from_the_census_is_refused(ledger):
    before = ledger.read_bytes()
    p = cli(cli_args(ledger, "--census-run-id", RUN2))
    assert p.returncode == 2 and "census_run_id_mismatch" in p.stderr
    assert ledger.read_bytes() == before


def test_cli_census_file_supplies_the_run_id_and_is_cross_checked(ledger):
    cf = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, name="c.json")
    args = cli_args(ledger, census=False) + ["--census", str(cf)]
    p = cli(args)
    assert p.returncode == 0, p.stderr
    assert lines(ledger)[1]["evidence"]["census_run_id"] == RUN
    cf.write_text(json.dumps(dict(generated=RUN, layer="L0", assets=[dict(
        asset_id="bg_ontology", has_writer=True, measurements={"Build.registered": dict(v="FAIL", measured="m")})])))
    q = cli(args)
    assert q.returncode == 2 and "census_mismatch" in q.stderr


def test_cli_a_census_outside_the_control_dir_and_archive_is_refused(ledger, tmp_path):
    out = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, directory=tmp_path, name="o.json")
    args = cli_args(ledger, census=False) + ["--census", str(out)]
    p = cli(args)
    assert p.returncode == 2 and "census_untrusted" in p.stderr
    assert len(lines(ledger)) == 1


def test_cli_the_census_archive_env_is_honoured(ledger, tmp_path):
    arch = tmp_path / "arch"
    arch.mkdir()
    out = write_census_file({"Build.registered": dict(v="PASS", measured="m")}, directory=arch, name="o.json")
    args = cli_args(ledger, census=False)
    i = args.index("--census-archive-dir")
    del args[i:i + 2]
    env = dict(os.environ, NIKASHA_CENSUS_ARCHIVE=str(arch), NIKASHA_CONTROL_DIR=str(ENV.ctrl))
    p = cli(args + ["--census", str(out)], env=env)
    assert p.returncode == 0, p.stderr


def test_cli_a_typed_writer_hash_is_verified_against_the_repo_or_does_not_count(ledger):
    args = cli_args(ledger)
    i = args.index("--writer-file")
    del args[i:i + 2]
    p = cli(args + ["--writer-hash", f"{W1}={'d' * 64}"])
    assert p.returncode == 2 and "writer_hash_mismatch" in p.stderr
    j = args.index("--writer-repo")
    del args[j:j + 2]
    q = cli(args + ["--writer-hash", f"{W1}={WH[W1]}"])
    assert q.returncode == 2 and "unverified_writer_hashes" in q.stderr
    assert len(lines(ledger)) == 1


def test_cli_script_errors_exit_5(tmp_path):
    notdir = tmp_path / "afile"
    notdir.write_text("x")
    p = cli(cli_args(notdir / "ledger.jsonl", "--init"))                    # parent is a file: an OS error, not a refusal
    assert p.returncode == 5


def test_cli_n_a_typed_by_hand_is_refused(ledger):
    args = cli_args(ledger, "--na-rule-id", NA_RID, census=False)
    args[args.index("PASS")] = "N/A"
    args[args.index("Build.registered")] = "Ldgr.source_presence"
    cf = write_census_file({}, rec=dict(target_columns=list(NA_COLS)))
    p = cli(args + ["--census", str(cf)])
    assert p.returncode == 2 and "na_not_computed" in p.stderr
    assert len(lines(ledger)) == 1


def test_cli_duplicate_keys_in_facts_json_are_refused(ledger):
    args = cli_args(ledger, "--facts-json", '{"columns": ["a"], "columns": ["b"]}')
    p = cli(args)
    assert p.returncode == 2 and "bad_facts" in p.stderr
    assert len(lines(ledger)) == 1
    q = cli(cli_args(ledger, "--facts-json", "[1, 2"))
    assert q.returncode == 2 and "bad_facts" in q.stderr


def test_cli_an_addition_takes_its_run_id_and_verdict_from_the_caller(ledger):
    args = ["--ledger", str(ledger), "--asset", "bg_ontology", "--layer", "L0", "--kind", "addition",
            "--criterion", "D-GROUNDING", "--criterion-version", "1", "--detector", "grounding_probe.py",
            "--verdict", "FAIL", "--census-run-id", RUN, "--verified-by", "census-run"]
    p = cli(args)
    assert p.returncode == 0, p.stderr
    assert lines(ledger)[1]["kind"] == "addition"
