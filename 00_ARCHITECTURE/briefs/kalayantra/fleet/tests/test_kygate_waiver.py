"""Owner waiver: replace final acceptance only; release, holds and N stay strict.

Uses the existing gate world's real fixture Git repository and recording version
checker. The original test_kygate.py stays untouched.
"""
import copy
import json

import pytest

import test_kygate as legacy

template = legacy.template
w = legacy.w


def save(path, doc):
    path.write_text(json.dumps(doc))


@pytest.fixture
def boot(w):
    w.bootstrap = copy.deepcopy(w.manifest)
    w.bootstrap["mode"] = "bootstrap"
    w.bootstrap["manifest_sha256"] = legacy.digest_without(w.bootstrap, "manifest_sha256")
    save(w.run / "VERSIONS.bootstrap.json", w.bootstrap)
    (w.run / "VERSIONS.json").unlink()
    w.install = {"mode": "bootstrap", "manifest": {"manifest_sha256": w.bootstrap["manifest_sha256"]}}
    save(w.run / "INSTALL_RECEIPT.json", w.install)
    w.resume["approved_bundle_digest"] = w.bootstrap["manifest_sha256"]
    w.resume["waiver"] = {
        "final_acceptance": True,
        "decided_by": {"kind": "owner", "id": "abhisek"},
        "reason": "Start implementation; final acceptance is deferred by the owner.",
        "ts": "2026-10-13T20:09:54Z",
    }
    w.write_resume_only()
    return w


def waived_codes(result):
    return sorted(line.split(":", 1)[0] for line in legacy.fields(result).get("waived", []))


def test_owner_waiver_opens_bootstrap_and_reports_every_final_finding(boot):
    result = boot.gate()
    legacy.assert_status(result, "OPEN")
    assert legacy.fields(result)["final_acceptance"] == ["waived_by_owner"]
    assert legacy.fields(result)["bootstrap_manifest_digest"] == [boot.bootstrap["manifest_sha256"]]
    assert legacy.fields(result)["final_manifest_digest"] == [""]
    assert waived_codes(result) == sorted([
        "final_manifest_missing", "bootstrap_only_installation", "absent_rehearsal",
        "stale_tested_hashes", "missing_coverage", "backfill_unvalidated", "final_acceptance_unverified",
    ])
    assert boot.calls() == ["argc=1 argv=--bootstrap"]


@pytest.mark.parametrize("where", ["resume", "waiver"])
def test_surrogate_cannot_waive_final_acceptance(boot, where):
    record = boot.resume if where == "resume" else boot.resume["waiver"]
    record["decided_by"]["kind"] = "surrogate_decision"
    boot.write_resume_only()
    result = boot.gate()
    assert result.returncode == 75
    assert "bootstrap_only_installation" in legacy.codes(result)
    assert "final_acceptance" not in legacy.fields(result)
    assert waived_codes(result) == []
    assert boot.calls() == ["argc=2 argv=--expected-manifest-digest " + boot.bootstrap["manifest_sha256"]]


@pytest.mark.parametrize("field,value,code", [
    ("approved_bundle_digest", "9" * 64, "resume_bundle_mismatch"),
    ("release_receipt_digest", "9" * 64, "stale_resume"),
    ("binding", "N-468", "resume_binding"),
    ("ts", "2026-10-13T20:09:54+05:30", "resume_ts_not_utc"),
    ("ts", "2026-02-30T20:09:54Z", "resume_ts_not_utc"),
])
def test_waiver_keeps_every_resume_binding_strict(boot, field, value, code):
    boot.resume[field] = value
    boot.write_resume_only()
    result = boot.gate()
    legacy.assert_wait(result, code)
    assert boot.calls() == ["argc=1 argv=--bootstrap"]


def test_waiver_cannot_ignore_bad_release_content_digest(boot):
    boot.receipt["conditions"]["pins"]["evidence"]["rebuild_run"] = "changed"
    save(boot.run / "RELEASE_RECEIPT.json", boot.receipt)
    legacy.assert_wait(boot.gate(), "receipt_digest_mismatch", "stale_resume")


@pytest.mark.parametrize("when", ["before", "during"])
def test_waiver_keeps_global_hold_strict(boot, when):
    if when == "before":
        (boot.root / "HOLD").touch()
    else:
        legacy.Path(str(boot.kyversion) + ".create").write_text(str(boot.root / "HOLD"))
    legacy.assert_wait(boot.gate(), "global_hold")


def test_hold_merges_allows_owner_waived_build_gate(boot):
    (boot.run / "HOLD_MERGES").touch()
    result = boot.gate()
    legacy.assert_status(result, "OPEN")
    assert legacy.fields(result)["hold_merges"] == ["present"]


def test_bootstrap_version_failure_is_required_and_never_waived(boot):
    legacy.Path(str(boot.kyversion) + ".rc").write_text("1")
    result = boot.gate()
    legacy.assert_wait(result, "bootstrap_acceptance_unverified")
    assert legacy.reason(result, "bootstrap_acceptance_unverified") == [
        "bootstrap_acceptance_unverified: kyversion.sh --bootstrap ended rc=1"]


def test_missing_version_checker_is_required(boot):
    boot.kyversion.unlink()
    legacy.assert_wait(boot.gate(), "bootstrap_acceptance_unverified")


@pytest.mark.parametrize("change", ["content", "field", "missing", "malformed", "mode"])
def test_bootstrap_digest_is_recomputed_and_never_trusted(boot, change):
    path = boot.run / "VERSIONS.bootstrap.json"
    if change == "content":
        boot.bootstrap["components"][0]["sha256"] = "c" * 64
        save(path, boot.bootstrap)
    elif change == "field":
        boot.bootstrap["manifest_sha256"] = "9" * 64
        boot.resume["approved_bundle_digest"] = "9" * 64
        boot.write_resume_only()
        save(path, boot.bootstrap)
    elif change == "missing":
        path.unlink()
    elif change == "malformed":
        path.write_text('{"mode":"bootstrap","mode":"bootstrap"}')
    else:
        boot.bootstrap["mode"] = "final"
        boot.bootstrap["manifest_sha256"] = legacy.digest_without(boot.bootstrap, "manifest_sha256")
        boot.resume["approved_bundle_digest"] = boot.bootstrap["manifest_sha256"]
        boot.write_resume_only()
        save(path, boot.bootstrap)
    legacy.assert_wait(boot.gate(), "bootstrap_manifest_invalid", "resume_bundle_mismatch")


def test_changed_bootstrap_manifest_is_detected_after_version_check(boot):
    legacy.Path(str(boot.kyversion) + ".append").write_text(str(boot.run / "VERSIONS.bootstrap.json"))
    legacy.assert_wait(boot.gate(), "inputs_changed")


@pytest.mark.parametrize("mode", legacy.MODES)
@pytest.mark.parametrize("bad", [None, True, [], {}, "owner", {"final_acceptance": True}])
def test_malformed_waiver_is_wait_in_both_modes(boot, mode, bad):
    boot.resume["waiver"] = bad
    boot.write_resume_only()
    result = boot.gate(mode)
    assert result.returncode == 75
    assert "resume_malformed" in legacy.codes(result)
    assert waived_codes(result) == []


@pytest.mark.parametrize("field,value", [
    ("final_acceptance", "true"), ("final_acceptance", 1),
    ("decided_by", {"kind": "owner", "id": " "}),
    ("decided_by", {"kind": "planner", "id": "x"}),
    ("decided_by", {"kind": "owner", "id": "x", "extra": True}),
    ("reason", ""), ("reason", " \n"), ("reason", 1),
    ("ts", "2026-10-13T20:09:54+05:30"), ("ts", "2026-02-30T20:09:54Z"),
    ("ts", 1), ("extra", True),
])
def test_malformed_waiver_field_is_never_honoured(boot, field, value):
    boot.resume["waiver"][field] = value
    boot.write_resume_only()
    result = boot.gate()
    assert result.returncode == 75
    assert "resume_malformed" in legacy.codes(result)
    assert waived_codes(result) == []


def test_false_waiver_does_not_waive(boot):
    boot.resume["waiver"]["final_acceptance"] = False
    boot.write_resume_only()
    result = boot.gate()
    assert "bootstrap_only_installation" in legacy.codes(result)
    assert waived_codes(result) == []
    assert "resume_malformed" not in legacy.codes(result)


def test_pre_resume_with_valid_owner_waiver_keeps_already_resumed_rule(boot):
    result = boot.gate("pre-resume")
    legacy.assert_wait(result, "already_resumed")
    assert boot.calls() == ["argc=1 argv=--bootstrap"]


@pytest.mark.parametrize("mode", legacy.MODES)
def test_absent_waiver_final_output_is_byte_identical_golden(w, mode):
    result = w.run_mode(mode)
    word = "OPEN" if mode == "full" else "READY_TO_START"
    assert result.returncode == 0
    assert result.stdout == (
        word + "\nrelease_id=REL-20261011-01\nrelease_receipt_digest=" + w.receipt["digest"]
        + "\nfinal_manifest_digest=" + w.manifest["manifest_sha256"]
        + "\nhold_merges=absent\nunobserved=" + legacy.UNOBSERVED + "\n")


@pytest.mark.parametrize("mode", legacy.MODES)
def test_absent_waiver_bootstrap_wait_is_byte_identical_golden(boot, mode):
    del boot.resume["waiver"]
    boot.with_resume = mode == "full"
    boot.write_resume_only()
    result = boot.gate(mode)
    assert result.returncode == 75
    extra = ("reason=resume_bundle_mismatch: the record approves bundle \""
             + boot.bootstrap["manifest_sha256"] + "\"; the final manifest's digest is unknown\n") if mode == "full" else ""
    assert result.stdout == (
        "WAIT\nrelease_id=REL-20261011-01\nrelease_receipt_digest=" + boot.receipt["digest"]
        + "\nfinal_manifest_digest=\nhold_merges=absent\nunobserved=" + legacy.UNOBSERVED
        + "\nreason=final_manifest_missing: " + str(boot.run / "VERSIONS.json")
        + "\nreason=bootstrap_only_installation: " + str(boot.run / "INSTALL_RECEIPT.json") + ' says mode "bootstrap", not "final"'
        + "\nreason=absent_rehearsal: rehearsal.results is absent"
        + "\nreason=stale_tested_hashes: rehearsal.tested_components is not a list"
        + '\nreason=missing_coverage: coverage.verdict is null, not "ACCEPTED"; coverage is absent; packets[] names no admitted packet'
        + "\nreason=backfill_unvalidated: backfill.validated is null, not true\n" + extra)
