"""SR-EXECUTOR-FRAMING (supersedes the J-3c #3738 stdout special case): the executor stores a child's stdout and stderr separately.

Production evidence: dispatch_v5_measuring_job.py --dry-run printed one valid ky.measuring_staging/1 line on stdout while the staging
code printed advisory lines on stderr; the executor stored stdout+"\\n"+stderr as the receipt output, so the proof did not parse as one
document (fixed narrowly in #3738) and every golden capture gained a framing newline.

One oracle per distinct claim, each through the real run_one() -> execute() (a throwaway git repository and a real child process):
  1. valid proof on stdout + advisory text on stderr  -> COMPLETED with the proof bound as `staging`;
  2. a corrupted proof on stdout                      -> FAILED (the validation is unchanged);
  3. the same valid proof on stderr only              -> FAILED (the proof must come from stdout);
  4. a child with stdout and stderr                   -> output_file == stdout byte for byte (no framing byte), stderr file == stderr,
                                                         each with its own sha256/bytes in the receipt, which still binds output_sha256;
  5. a receipt made before this change (one combined output file, no stderr_* fields) -> still verifies mechanically.
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
    assert json.loads((mod.REC / "rollback-1.output.txt").read_text()) == proof  # the output file is the proof document and nothing else


def test_corrupted_proof_on_stdout_fails(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stdout", tamper={"rollback_confirmed": False})
    record = run(mod, req, path)
    assert record["status"] == "FAILED" and "staging" not in record
    assert record["reason"] == "bound measuring staging rollback proof missing; reconcile transaction outcome"


def test_proof_printed_on_stderr_only_fails(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stderr")
    record = run(mod, req, path)
    assert record["status"] == "FAILED" and "staging" not in record


ADVISORY = "[dry-run] staged plan for ka_gochara_v5\n[dispatch] JOB IMAGE MUST MATCH the reviewed commit\n[dispatch] READ THE RESULT\n"


def test_output_file_is_stdout_exactly_and_stderr_is_its_own_file(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stdout")
    record = run(mod, req, path)
    stdout_bytes = (json.dumps(proof, sort_keys=True, separators=(",", ":")) + "\n").encode()     # what print(proof) wrote, and nothing else
    assert (mod.REC / "rollback-1.output.txt").read_bytes() == stdout_bytes
    assert (mod.REC / "rollback-1.stderr.txt").read_bytes() == ADVISORY.encode()
    assert record["output_file"] == str(mod.REC / "rollback-1.output.txt") and record["stderr_file"] == str(mod.REC / "rollback-1.stderr.txt")
    assert (record["output_sha256"], record["output_bytes"]) == (mod.digest_bytes(stdout_bytes), len(stdout_bytes))
    assert (record["stderr_sha256"], record["stderr_bytes"]) == (mod.digest_bytes(ADVISORY.encode()), len(ADVISORY.encode()))


def test_a_child_with_no_stderr_leaves_no_stderr_file(tmp_path, monkeypatch):
    mod, req, proof, path = rig(tmp_path, monkeypatch, "stdout")
    (mod.KY_ROOT / "quiet").write_text("1")
    src = tmp_path / "src"
    (src / SCRIPT).write_text(CHILD.replace('sys.stderr.write("[dry-run]', 'quiet = (root / "quiet").exists()\nif not quiet: sys.stderr.write("[dry-run]'))
    git(src, "add", "-A"); git(src, "commit", "-q", "-m", "quiet child")
    req["reviewed_commit"] = git(src, "rev-parse", "HEAD"); path.write_text(json.dumps(req))
    record = run(mod, req, path)
    assert "stderr_file" not in record and not (mod.REC / "rollback-1.stderr.txt").exists()


def test_a_receipt_made_before_the_change_still_verifies(tmp_path):
    from test_executor_mechanical_acceptance import World, sha
    w = World(tmp_path)
    req = w.request("old-1")
    w.run(req, out="rows=3\n")
    # rewrite the new-format artefacts as the pre-change executor wrote them: one combined output file, no stderr_* fields
    combined = "rows=3\n" + "\n" + "advisory on stderr\n"
    (w.mod.REC / "old-1.output.txt").write_text(combined)
    record = json.loads((w.mod.REC / "old-1.json").read_text())
    for key in ("stderr_file", "stderr_sha256", "stderr_bytes", "stderr_tail"):
        record.pop(key, None)
    record.update(output_sha256=sha(combined), output_bytes=len(combined))
    (w.mod.REC / "old-1.json").write_text(json.dumps(record, indent=1))
    post = w.mod.ACC / "old-1.post.json"; post.unlink()
    assert w.mod.mechanical_post_acceptance(req, w.mod.DONE / "old-1.json") is None
    assert json.loads(post.read_text())["output_sha256"] == sha(combined)
