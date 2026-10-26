"""SR-W4-SIBLING-DRYRUN-ADMISSION (ruling, option B): a W4 shard's `verification_job` is admitted on the SAME window's V01 dry run.

The ruling (verbatim): "The rule is narrow: same window's V01 dry run COMPLETED at the same reviewed_commit + image digest + job definition, and the request names this
ruling id; fail-on-revert tests for unrelated window / other head-image-definition / unnamed ruling; the per-shard requirement stays the default elsewhere. The meter, G-5
and the 0.75x rule stay on every real pass."  Sources of the expected values: the ruling above; the launch record shape of fleet/verification_launch.py (`ky.verification_launch/1`:
image_digest, definition_check, report_only_run.ok / .report_only) as printed in the real V01 dry run's output; root CLAUDE.md §N.8 (every green is computed by a detector that
can read false) and §N.7.6.

One oracle per distinct production claim; each passes on the real executor and FAILS on a copy of executor.py with that ONE claim's line reverted (as in
test_executor_rebuild_dryrun_detector.py):
  Z1 admitted: a V03 request citing the LATEST V01 dry run (same item, chart, generation, reviewed_commit; image digest as named; definition CONFORMS; report-only ok)
  Z2 the request must name the ruling id (unnamed / another ruling refuses)
  Z3 the cited dry run must be V01's (a dry run of another shard, V02, refuses)
  Z4 another reviewed_commit refuses
  Z5 another image digest than the dry run's refuses
  Z6 a NEWER V01 dry-run receipt (another window) refuses; a newer receipt of another shard does not
  Z7 a dry run that did not COMPLETE refuses
  Z8 a dry run whose definition_check was not CONFORMS refuses
  Z9 a dry run whose report-only run was not ok refuses
  Z10 the dry run's launch record must be that operation's own (a copied record of another operation refuses)
  Z11 the field is admitted only for kind verification_job
  Z12 the request must be one shard of the partition (no shard / an unknown shard id refuses)
  Z13 the default is unchanged: no field -> a V03 request citing V01's dry run is refused exactly as before
  L1 (launcher) the real dispatch refuses when the job's image digest is not the one sibling_dryrun names ("same job definition"); with the field absent it is unchanged
"""
import json
import pytest

import test_executor_mechanical_production as M
import test_executor_verification_launch as base
from test_executor_table import CANONICAL_CHART

RULING = "SR-W4-SIBLING-DRYRUN-ADMISSION"
IMAGE = "sha256:" + "a" * 64
OTHER_IMAGE = "sha256:" + "c" * 64
EXPECTED_REFUSAL = "the dry run did not COMPLETE OK (exit 0, complete output, bound archived request) for this request's identity"


def archive(w, oid, shard="V01", image=IMAGE, status="COMPLETED", exit_code=0, ts_s=-60, definition="CONFORMS", ok=True, report_only=True,
            commit=None, launch_oid=None, kind="verification_job_dryrun"):
    """A `verification_job_dryrun` request archived in done/ with its receipt and complete output (the launcher's launch record, then the job's report line)."""
    commit = commit or w.reviewed
    dreq = {"operation_id": oid, "kind": kind, "item_id": "J-5s", "idempotency_key": "k-" + oid, "requested_by": "adhikarin", "kyd": "KYD-1",
            "args": {"generation": "5.0", "shard": shard}, "chart_id": CANONICAL_CHART, "reviewed_commit": commit}
    (w.mod.DONE / f"{oid}.json").write_text(json.dumps(dreq))
    digest = w.mod.request_digest(dreq)
    launch = {"schema": "ky.verification_launch/1", "status": "DRY_RUN", "mode": "dry_run", "operation_id": launch_oid or oid, "request_sha256": digest,
              "reviewed_commit": commit, "chart_id": CANONICAL_CHART, "generation": "5.0", "image_digest": image, "definition_check": definition,
              "shard": {"id": shard}, "report_only_run": {"ok": ok, "report_only": report_only, "outcome": "SUCCEEDED"}}
    output = json.dumps(launch) + "\n" + json.dumps({"classes": {}, "generation": "5.0", "report_only": True, "status": "REPORT_ONLY"}) + "\n"
    (w.mod.REC / f"{oid}.output.txt").write_text(output)
    record = {"operation_id": oid, "kind": kind, "item_id": "J-5s", "status": status, "reason": "", "exit_code": exit_code, "ts": M.iso(seconds=ts_s),
              "reviewed_commit": commit, "request_sha256": digest, "output_sha256": M.sha(output)}
    body = json.dumps(record, indent=1).encode()
    (w.mod.REC / f"{oid}.json").write_bytes(body)
    return {"name": f"{oid}.json", "sha256": M.sha(body)}


def sibling_request(w, ref, shard="V03", ruling=RULING, image=IMAGE, kind="verification_job", **more):
    req = {"operation_id": "op-v03", "kind": kind, "item_id": "J-5s", "requested_by": "adhikarin", "kyd": "KYD-1", "chart_id": CANONICAL_CHART, "reviewed_commit": w.reviewed,
           "args": {"generation": "5.0", "shard": shard}, "dryrun_receipt": ref, "sibling_dryrun": {"ruling": ruling, "image_digest": image}}
    req.update(more)
    return req


def oracle_z1_admitted(w, table):
    ref = archive(w, "dry-v01")
    why, evidence = w.mod.dry_run_check(sibling_request(w, ref), table)
    assert why is None, why
    assert evidence["operation_id"] == "dry-v01" and evidence["sibling_dryrun"] == {"ruling": RULING, "image_digest": IMAGE, "shard": "V01"}
    assert w.mod.dry_run_check(sibling_request(w, ref, shard="V07"), table)[0] is None, "any shard of the window rides on the one V01 dry run"


def oracle_z2_ruling_must_be_named(w, table):
    ref = archive(w, "dry-v01")
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] is None, "control failed — the refusals below would be vacuous"
    for ruling in ("", "SR-SOMETHING-ELSE", None):
        why, _ = w.mod.dry_run_check(sibling_request(w, ref, ruling=ruling), table)
        assert why == f"sibling_dryrun must name the ruling {RULING}", (ruling, why)
    bare = sibling_request(w, ref); bare["sibling_dryrun"] = {"image_digest": IMAGE}
    assert w.mod.dry_run_check(bare, table)[0] == "sibling_dryrun must carry exactly ruling and image_digest"


def oracle_z3_the_cited_dry_run_must_be_v01s(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    ref = archive(w, "dry-v02", shard="V02", ts_s=-30)
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] == EXPECTED_REFUSAL, "V03 may not ride on V02's dry run"
    assert w.mod.dry_run_check(sibling_request(w, ref, shard="V02"), table)[0] == EXPECTED_REFUSAL, "even V02's own dry run is not the window's V01 rehearsal under the ruling"


def oracle_z4_another_reviewed_commit_refuses(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    other = "e" * 40
    ref = archive(w, "dry-other-head", commit=other, ts_s=-30)
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] == EXPECTED_REFUSAL


def oracle_z5_another_image_digest_refuses(w, table):
    ref = archive(w, "dry-v01")
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] is None, "control failed — the refusal below would be vacuous"
    why, _ = w.mod.dry_run_check(sibling_request(w, ref, image=OTHER_IMAGE), table)
    assert why == "the V01 dry run ran at another image digest than sibling_dryrun names", why


def oracle_z6_a_newer_v01_dry_run_is_another_window(w, table):
    ref = archive(w, "dry-v01", ts_s=-600)
    archive(w, "dry-v02-newer", shard="V02", ts_s=-100)                       # another shard's dry run, newer: no effect
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] is None, "control failed — the refusal below would be vacuous"
    archive(w, "dry-v01-newer", status="FAILED", exit_code=1, ts_s=-10)         # a newer V01 attempt of ANY status starts another window
    why, _ = w.mod.dry_run_check(sibling_request(w, ref), table)
    assert why and why.startswith("a newer V01 dry run exists"), why


def oracle_z7_the_dry_run_must_have_completed(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    ref = archive(w, "dry-failed", status="FAILED", exit_code=0, ts_s=-30)       # exit 0 yet FAILED: the executor fails a run whose output proves nothing (an exit status alone proves nothing)
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] == EXPECTED_REFUSAL


def oracle_z8_the_definition_must_have_conformed(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    ref = archive(w, "dry-nonconforming", definition="NONCONFORMING", ts_s=-30)
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] == "the V01 dry run did not find the job definition CONFORMING"


def oracle_z9_the_report_only_run_must_have_been_ok(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    ref = archive(w, "dry-not-ok", ok=False, ts_s=-30)
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] == "the V01 dry run's report-only run was not ok"


def oracle_z10_the_launch_record_must_be_that_operations_own(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    ref = archive(w, "dry-copied", launch_oid="dry-somebody-else", ts_s=-30)
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] == "the V01 dry run's launch record does not bind that operation and its request"


def oracle_z11_only_for_verification_job(w, table):
    assert w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01")), table)[0] is None, "control failed — the refusal below would be vacuous"
    for kind in ("orchestrator_rebuild", "smalltest_dispatch", "backup_snapshot"):      # backup_snapshot has no dry-run kind: the field still refuses
        why, _ = w.mod.dry_run_check(sibling_request(w, archive(w, "dry-v01"), kind=kind), table)
        assert why == "sibling_dryrun is admitted only for kind verification_job", (kind, why)


def oracle_z12_the_request_must_be_one_shard_of_the_partition(w, table):
    ref = archive(w, "dry-v01")
    assert w.mod.dry_run_check(sibling_request(w, ref), table)[0] is None, "control failed — the refusals below would be vacuous"
    whole = sibling_request(w, ref); whole["args"] = {"generation": "5.0"}
    assert w.mod.dry_run_check(whole, table)[0] == "a sibling dry run admits only a request for one shard (args exactly generation and shard)"
    why, _ = w.mod.dry_run_check(sibling_request(w, ref, shard="all"), table)
    assert why == "a sibling dry run admits only a request for one shard (args exactly generation and shard)", why


def oracle_z13_the_default_is_unchanged(w, table):
    ref = archive(w, "dry-v01")
    v01 = sibling_request(w, ref, shard="V01"); del v01["sibling_dryrun"]
    assert w.mod.dry_run_check(v01, table)[0] is None, "control failed — the default path still admits a request for the very shard that was rehearsed"
    v03 = sibling_request(w, ref); del v03["sibling_dryrun"]
    assert w.mod.dry_run_check(v03, table)[0] == EXPECTED_REFUSAL, "without the ruling a V03 request needs its own V03 dry run, exactly as before"


ORACLES = {
    "z1": (oracle_z1_admitted,
           ('    if "sibling_dryrun" in req: return sibling_dry_run_check(req, table)\n', '')),
    "z2": (oracle_z2_ruling_must_be_named,
           ('    if sibling["ruling"] != SIBLING_DRYRUN_RULING: return f"sibling_dryrun must name the ruling {SIBLING_DRYRUN_RULING}"\n', '')),
    "z3": (oracle_z3_the_cited_dry_run_must_be_v01s,
           ('    probe["args"] = {**req["args"], "shard": SIBLING_DRYRUN_SHARD}\n', '    probe["args"] = dict(req["args"])\n')),
    "z4": (oracle_z4_another_reviewed_commit_refuses,
           ('              and rec.get("reviewed_commit") == archived.get("reviewed_commit") == req.get("reviewed_commit")\n'      # the commit is bound twice (this triple, and DRYRUN_IDENTITY_FIELDS): the one plant removes both
            '              and all(canonical_sha(archived.get(f)) == canonical_sha(req.get(f)) for f in DRYRUN_IDENTITY_FIELDS))\n',
            '              and all(canonical_sha(archived.get(f)) == canonical_sha(req.get(f)) for f in ("item_id", "chart_id", "args")))\n')),
    "z5": (oracle_z5_another_image_digest_refuses,
           ('    if launch.get("image_digest") != sibling["image_digest"]: return "the V01 dry run ran at another image digest than sibling_dryrun names"\n', '')),
    "z6": (oracle_z6_a_newer_v01_dry_run_is_another_window,
           ('        if newer: return f"a newer V01 dry run exists', '        if False: return f"a newer V01 dry run exists')),
    "z7": (oracle_z7_the_dry_run_must_have_completed,
           ('rec.get("status") == "COMPLETED" and ', '')),
    "z8": (oracle_z8_the_definition_must_have_conformed,
           ('    if launch.get("definition_check") != "CONFORMS": return "the V01 dry run did not find the job definition CONFORMING"\n', '')),
    "z9": (oracle_z9_the_report_only_run_must_have_been_ok,
           ('    if not (isinstance(ran, dict) and ran.get("ok") is True and ran.get("report_only") is True): return "the V01 dry run\'s report-only run was not ok"\n', '')),
    "z10": (oracle_z10_the_launch_record_must_be_that_operations_own,
            ('launch.get("operation_id") == dry_oid and launch.get("request_sha256") == rec.get("request_sha256")', 'True')),
    "z11": (oracle_z11_only_for_verification_job,
            ('    if req["kind"] != "verification_job": return "sibling_dryrun is admitted only for kind verification_job", None\n', '')),
    "z12": (oracle_z12_the_request_must_be_one_shard_of_the_partition,
            ('isinstance(args["shard"], str) and re.fullmatch(r"V\\d{2}", args["shard"])', 'True')),
    "z13": (oracle_z13_the_default_is_unchanged,
            ('    if "sibling_dryrun" in req: return sibling_dry_run_check(req, table)\n', '    if kind == "verification_job": return sibling_dry_run_check(req, table)\n')),
}


@pytest.mark.parametrize("claim", sorted(ORACLES, key=lambda c: int(c[1:])))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table = M.build(tmp_path, monkeypatch)
    ORACLES[claim][0](w, table)


@pytest.mark.parametrize("claim", sorted(ORACLES, key=lambda c: int(c[1:])))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table = M.build(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        oracle(w, table)


def test_the_ruling_is_admitted_through_the_mechanical_route_and_recorded(tmp_path, monkeypatch):
    """The evidence reaches the mechanical acceptance record (mechanical_problem calls dry_run_check): the record names the ruling."""
    w, table = M.build(tmp_path, monkeypatch)
    ref = archive(w, "dry-v01")
    template = {"kind": "verification_job",
                "fixed": {"kind": "verification_job", "item_id": "J-5s", "requested_by": "adhikarin", "kyd": "KYD-1", "chart_id": CANONICAL_CHART, "reviewed_commit": w.reviewed,
                          "args": {"generation": "5.0", "shard": "V03"}, "sibling_dryrun": {"ruling": RULING, "image_digest": IMAGE}},
                "fill": ["operation_id", "idempotency_key", "lease_id", "dryrun_receipt"]}
    M.publish(w, [template])
    req = M.fill_request(w, template, "mech-v03", dry=ref)
    why, evidence = w.mod.mechanical_problem(req, table)
    assert why is None, why
    assert evidence["dry_run"]["sibling_dryrun"]["ruling"] == RULING


# ───────────────────────────── L1: the launcher ─────────────────────────────

def launcher_request(image=IMAGE, **more):
    req = base.request("verification_job", args={"generation": "5.0", "shard": "V03"}, sibling_dryrun={"ruling": RULING, "image_digest": image}, **more)
    return req


def run_launch(tmp_path, req, cloud=None):
    return base.go(tmp_path, cloud, req, argv=("--generation", "5.0", "--shard", "V03"))


def test_l1_the_dispatch_refuses_when_the_job_was_redefined_after_the_dry_run(tmp_path):
    assert base.DIGEST == IMAGE, "fixture premise: the fake cloud's job runs at the image the dry run named"
    cloud, record, _ = run_launch(tmp_path / "ok", launcher_request())
    assert record["status"] == "LAUNCHED" and record["image_digest"] == IMAGE, "control failed — the refusal below would be vacuous"
    cloud = base.Cloud()
    with pytest.raises(base.vl.Refused, match="redefined after the V01 dry run"):
        run_launch(tmp_path / "redefined", launcher_request(image=OTHER_IMAGE), cloud)
    assert cloud.writes() == [] and not (tmp_path / "redefined" / "claims").exists(), "a refusal must precede the claim and the launch"


def test_l1_without_the_field_the_launch_is_exactly_as_before(tmp_path):
    cloud, record, _ = base.go(tmp_path, None, base.request("verification_job", args={"generation": "5.0", "shard": "V03"}), argv=("--generation", "5.0", "--shard", "V03"))
    assert record["status"] == "LAUNCHED" and len(cloud.writes()) == 1


def test_l1_a_malformed_field_refuses_too(tmp_path):
    req = launcher_request(); req["sibling_dryrun"] = "SR-W4-SIBLING-DRYRUN-ADMISSION"
    with pytest.raises(base.vl.Refused, match="redefined after the V01 dry run"):
        run_launch(tmp_path, req, base.Cloud())
