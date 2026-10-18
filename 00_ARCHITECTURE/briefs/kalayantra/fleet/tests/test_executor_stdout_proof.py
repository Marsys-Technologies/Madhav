"""J-3c blocker (2026-10-18): the measuring dry-run rollback proof is read from the child's STDOUT only.

Production evidence: dispatch_v5_measuring_job.py --dry-run printed one valid ky.measuring_staging/1 line on stdout while the staging
code printed advisory lines on stderr; the executor parsed stdout+"\\n"+stderr as one JSON document and refused a valid proof.

One oracle per distinct claim, each through the real run_one() -> execute() (a throwaway git repository and a real child process):
  1. valid proof on stdout + advisory text on stderr  -> COMPLETED with the proof bound as `staging`; the evidence file keeps both streams;
  2. a corrupted proof on stdout                      -> FAILED (the validation is unchanged);
  3. the same valid proof on stderr only              -> FAILED (the proof must come from stdout).
"""
import json
import subprocess
import sys

import pytest

from test_executor_overlay import GENERATOR, load_executor, make_repo, git

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
SCRIPT = "platform/scripts/fixture_measuring_dryrun.py"
CHILD = '''import os, pathlib, sys
root = pathlib.Path(os.environ["KY_ROOT"])
mode = (root / "mode.txt").read_text().strip()
proof = (root / "proof.txt").read_text().strip()
sys.stderr.write("[dry-run] staged plan for ka_gochara_v5\\n[dispatch] JOB IMAGE MUST MATCH the reviewed commit\\n[dispatch] READ THE RESULT\\n")
if mode == "stdout":
    print(proof)
elif mode == "stderr":
    sys.stderr.write(proof + "\\n")
'''
OP = {"script": SCRIPT, "needs": "none", "production": False}


def rig(tmp_path, monkeypatch, mode, tamper=None):
    src, commit = make_repo(tmp_path, generator=GENERATOR)
    (src / SCRIPT).write_text(CHILD)
    git(src, "add", "-A"); git(src, "commit", "-q", "-m", "fixture child")
    commit = git(src, "rev-parse", "HEAD")
    mod = load_executor(tmp_path, src)
    for directory in (mod.REQ, mod.DONE, mod.INFLIGHT, mod.ACC):
        directory.mkdir(parents=True, exist_ok=True)
    req = {"operation_id": "rollback-1", "kind": "measuring_dispatch_dryrun", "item_id": "J-3c", "reviewed_commit": commit,
           "idempotency_key": "k", "requested_by": "adhikarin", "kyd": "kyd-1", "args": {"run": "all_classes_full", "classes": "all"}}
    manifest = {"chart_id": CHART, "scope_target": "ka_gochara_v5", "gochara_v5_test_slice": {"run": "all_classes_full"}}
    proof = {"schema": "ky.measuring_staging/1", "status": "ROLLED_BACK", "rollback_confirmed": True, "operation_id": req["operation_id"],
             "request_sha256": mod.request_digest(req), "args": req["args"], "plan_manifest": manifest,
             "plan_manifest_digest": mod.digest_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())}
    if tamper:
        proof.update(tamper)
    (mod.KY_ROOT / "proof.txt").write_text(json.dumps(proof, sort_keys=True, separators=(",", ":")))
    (mod.KY_ROOT / "mode.txt").write_text(mode)
    for name, value in (("sync", lambda: None), ("load_table", lambda: {req["kind"]: OP}), ("capabilities", lambda table_on_main: {}),
                        ("validate", lambda *a, **k: None), ("mechanical_acceptance", lambda *a, **k: None)):
        monkeypatch.setattr(mod, name, value)
    path = mod.REQ / "rollback-1.json"; path.write_text(json.dumps(req))
    return mod, req, proof, path


def run(mod, req, path):
    mod.run_one(path, req, OP)
    return json.loads((mod.REC / "rollback-1.json").read_text())


def test_valid_proof_on_stdout_with_advisory_stderr_completes_with_staging_bound(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stdout")
    record = run(mod, req, path)
    assert record["status"] == "COMPLETED", record
    assert record["staging"] == proof
    evidence = (mod.REC / "rollback-1.output.txt").read_text()                 # the complete combined output stays the evidence
    assert json.dumps(proof, sort_keys=True, separators=(",", ":")) in evidence and "[dispatch] READ THE RESULT" in evidence


def test_corrupted_proof_on_stdout_fails(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stdout", tamper={"rollback_confirmed": False})
    record = run(mod, req, path)
    assert record["status"] == "FAILED" and "staging" not in record
    assert record["reason"] == "bound measuring staging rollback proof missing; reconcile transaction outcome"


def test_proof_printed_on_stderr_only_fails(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stderr")
    record = run(mod, req, path)
    assert record["status"] == "FAILED" and "staging" not in record
