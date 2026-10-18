"""J-2a M12: the executor's production (and lane) tree carries the CI-generated writer-digest overlay of the reviewed commit.

A5 D-33: platform/src/generated/nirmana-writer-digests.json is machine-owned; main's committed bytes are deliberately
non-authoritative and CI/deploy overlay freshly generated ones. One oracle per distinct claim:
  1. the generator the executor runs produces the runtime writer hash for ka_gochara_v5 (real sidecar, independent re-measurement);
  2. the production worktree holds the overlay bytes before the script reads them;
  3. a generation failure refuses the operation before the script runs;
  4. a non-production kind never runs the generator;
  5. the lane (dry-run) tree gets the same overlay;
  6. the receipt records the overlay manifest digest the executor measured.
Claims 2-6 run the real execute()/execute_lane()/receipt() against a throwaway git repository whose generator is a minimal
stand-in for the sidecar's; claim 1 is the only one that needs the real sidecar and its ephemeris path.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
EXECUTOR_PY = FLEET / "executor.py"
REPO = Path(os.environ.get("KY_OVERLAY_TEST_REPO", FLEET.parents[3]))
DIGESTS = "platform/src/generated/nirmana-writer-digests.json"
ASSET = "ka_gochara_v5"
STALE = {"writers": {ASSET: "0" * 64}}
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_OPTIONAL_LOCKS": "0"}
KY_VENV_PY = Path("/Users/Dev/kalayantra/venv/bin/python")
EPHE = Path("/Users/Dev/kalayantra/ephe")

GENERATOR = '''import hashlib, json, pathlib, sys
SIDECAR = pathlib.Path(__file__).resolve().parents[2]
OUTPUT = SIDECAR.parent / "src/generated/nirmana-writer-digests.json"
doc = {"writers": {"ka_gochara_v5": hashlib.sha256((SIDECAR / "writer.txt").read_bytes()).hexdigest()}}
text = json.dumps(doc, indent=2, sort_keys=True) + "\\n"
if "--check" in sys.argv:
    sys.exit(0 if OUTPUT.read_text() == text else 1)
OUTPUT.write_text(text)
'''
FAILING_GENERATOR = "import sys\nsys.stderr.write('generator fixture refuses\\n')\nsys.exit(3)\n"
SCRIPT = '''import os, pathlib
root = pathlib.Path(os.environ["KY_ROOT"])
seen = pathlib.Path("platform/src/generated/nirmana-writer-digests.json").read_text()
(root / "script_ran.marker").write_text(seen)
print("script saw", seen)
'''
ADAPTER = '''import pathlib
print("adapter saw", pathlib.Path("platform/src/generated/nirmana-writer-digests.json").read_text())
'''


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


FRESH = json.dumps({"writers": {ASSET: sha("writer v1\n")}}, indent=2, sort_keys=True) + "\n"
PRODUCTION_OP = {"script": "platform/scripts/read_digest.py", "needs": "none", "production": True}


def git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       capture_output=True, text=True, env=GIT_ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def make_repo(tmp_path, generator=GENERATOR):
    src = tmp_path / "src"
    files = {
        "platform/python-sidecar/pipeline/__init__.py": "",
        "platform/python-sidecar/pipeline/orchestrator/__init__.py": "",
        "platform/python-sidecar/pipeline/orchestrator/provenance_inventory.py": generator,
        "platform/python-sidecar/writer.txt": "writer v1\n",
        "platform/scripts/read_digest.py": SCRIPT,
        "00_ARCHITECTURE/briefs/kalayantra/fleet/lane_adapter.py": ADAPTER,
        DIGESTS: json.dumps(STALE, indent=2, sort_keys=True) + "\n",
    }
    for rel, body in files.items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    git(tmp_path, "init", "-q", str(src))
    git(src, "add", "-A")
    git(src, "commit", "-q", "-m", "fixture")
    return src, git(src, "rev-parse", "HEAD")


def load_executor(tmp_path, source_repo):
    saved = {k: os.environ.get(k) for k in ("KY_ROOT", "KY_SOURCE_REPO")}
    os.environ["KY_ROOT"] = str(tmp_path / "ky")
    os.environ["KY_SOURCE_REPO"] = str(source_repo)
    try:
        spec = importlib.util.spec_from_file_location(f"ky_executor_overlay_{abs(hash(str(tmp_path)))}", EXECUTOR_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    for directory in (mod.REC, mod.TMP, mod.EXEC, mod.KY_ROOT / "logs"):
        directory.mkdir(parents=True, exist_ok=True)
    mod.PY = sys.executable
    return mod


def production_request(commit, oid="op-overlay"):
    return {"operation_id": oid, "kind": "fixture_production", "item_id": "X", "reviewed_commit": commit,
            "idempotency_key": "k", "requested_by": "adhikarin", "kyd": "kyd-1", "args": {}}


# 1 ── the generator the executor runs yields the runtime writer hash (real sidecar; independent re-measurement)
def test_overlay_digest_equals_the_runtime_writer_hash_for_ka_gochara_v5(tmp_path):
    py = str(KY_VENV_PY if KY_VENV_PY.exists() else sys.executable)
    root = tmp_path / "tree"
    root.mkdir()
    archive = subprocess.run(["git", "-C", str(REPO), "archive", "HEAD", "platform/python-sidecar", DIGESTS],
                             capture_output=True, env=GIT_ENV)
    assert archive.returncode == 0, archive.stderr
    subprocess.run(["tar", "-x", "-C", str(root)], input=archive.stdout, check=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "SE_EPHE_PATH": os.environ.get("SE_EPHE_PATH", str(EPHE))}
    env.pop("PYTHONPATH", None)
    sidecar = root / "platform/python-sidecar"
    code = ("from pipeline.orchestrator.asset_runner import get_writer_source_hash as g\n"
            "from pipeline.orchestrator.writers import discover_all\n"
            f"discover_all(); print(g({ASSET!r}))\n")
    runtime = subprocess.run([py, "-c", code], cwd=sidecar, env=env, capture_output=True, text=True)
    if runtime.returncode:
        pytest.skip("sidecar dependencies or ephemeris unavailable here: " + runtime.stderr[-200:])
    digests = root / DIGESTS
    digests.write_text(json.dumps(STALE, indent=2, sort_keys=True) + "\n")          # whatever main carries, the overlay must fix it
    mod = load_executor(tmp_path, tmp_path)
    mod.PY = py
    proof, why = mod.apply_generated_overlay(root, "c" * 40, env)
    assert proof is not None, why
    written = json.loads(digests.read_text())["writers"][ASSET]
    assert written == runtime.stdout.strip().splitlines()[-1] != "0" * 64
    assert proof["files"] == {DIGESTS: hashlib.sha256(digests.read_bytes()).hexdigest()}


# 2 ── the production worktree holds the overlay bytes before the script reads them
def test_production_script_runs_on_the_generated_overlay_not_the_committed_bytes(tmp_path):
    src, commit = make_repo(tmp_path)
    mod = load_executor(tmp_path, src)
    rc, out = mod.execute(production_request(commit), dict(PRODUCTION_OP))
    assert rc == 0, out
    assert git(src, "show", f"{commit}:{DIGESTS}") != FRESH.strip(), "premise: the committed bytes are stale"
    assert (mod.KY_ROOT / "script_ran.marker").read_text() == FRESH
    assert not list(mod.EXEC.iterdir()), "operation worktree survived"


# 3 ── a generation failure refuses before the script runs
def test_generation_failure_refuses_the_operation_before_the_script_runs(tmp_path):
    src, commit = make_repo(tmp_path, generator=FAILING_GENERATOR)
    mod = load_executor(tmp_path, src)
    rc, out = mod.execute(production_request(commit), dict(PRODUCTION_OP))
    assert rc == 126 and out.startswith("generated overlay refused: ") and "generator fixture refuses" in out, (rc, out)
    assert not (mod.KY_ROOT / "script_ran.marker").exists(), "the script ran after the overlay was refused"
    assert "op-overlay" not in mod.overlay_proofs()
    assert not list(mod.EXEC.iterdir()), "operation worktree survived"


# 4 ── a non-production kind never runs the generator
def test_non_production_kind_does_not_run_the_generator(tmp_path, monkeypatch):
    src, commit = make_repo(tmp_path)
    mod = load_executor(tmp_path, src)

    def forbidden(*args, **kwargs):
        raise AssertionError("generator ran for a non-production kind")
    monkeypatch.setattr(mod, "apply_generated_overlay", forbidden)
    rc, out = mod.execute(production_request(commit, "op-readonly"), dict(PRODUCTION_OP, production=False))
    assert rc == 127 and "not on origin/main" in out, (rc, out)     # the unchanged non-production branch ran, not the generator


# 5 ── lane (dry-run) parity: the exported tree gets the same overlay
def test_lane_tree_gets_the_same_overlay(tmp_path, monkeypatch):
    src, commit = make_repo(tmp_path)
    mod = load_executor(tmp_path, src)
    monkeypatch.setattr(mod, "validate_lane", lambda req, op, reserved=False: None)
    req = dict(production_request(commit, "op-lane"), lane_target={"fixture": True})
    op = {"lane_dry_run": {"script": "00_ARCHITECTURE/briefs/kalayantra/fleet/lane_adapter.py"}}
    rc, out = mod.execute_lane(req, op)
    assert rc == 0, out
    assert "adapter saw " + FRESH in out
    assert mod.overlay_proofs().pop("op-lane")["files"] == {DIGESTS: sha(FRESH)}


# 6 ── the receipt records the manifest digest the executor measured
def test_receipt_records_the_overlay_manifest_digest(tmp_path):
    src, commit = make_repo(tmp_path)
    mod = load_executor(tmp_path, src)
    req = production_request(commit)
    rc, out = mod.execute(req, dict(PRODUCTION_OP))
    assert rc == 0, out
    mod.receipt(req, "COMPLETED", "", rc, out)
    record = json.loads((mod.REC / "op-overlay.json").read_text())
    expected = {"schema": "ky.generated_overlay/1", "source_sha": commit, "files": {DIGESTS: sha(FRESH)}}
    assert record["generated_overlay"] == dict(
        expected, manifest_sha256=sha(json.dumps(expected, sort_keys=True, separators=(",", ":"))))
