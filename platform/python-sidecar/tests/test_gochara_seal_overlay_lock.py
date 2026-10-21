"""The seal workflow runs on the VERIFIED regenerated implementation lock (SR-CHURN-CUT 3 made the committed lock machine-owned and stale).

Oracle (ST-WIRE-2 item 3, seal_flow.check_own_checkout; root CLAUDE.md §N.8): the seal's own-checkout check must read FALSE for a raw checkout whose lock is
stale, TRUE once the verified ci-generated overlay (apply_generated_overlay.py, the tool the workflow's apply-generated-overlay action runs) is applied, and
FALSE again for an overlay that was altered, bound to another commit, or smuggles in a file that is not a generated path. The checkout is simulated in a
temp directory; the lock path the check reads is pointed at it. No database, no network.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from services.gochara_kernel import implementation_registry as reg
from services.gochara_kernel import seal_flow

GOVERNANCE = Path(__file__).resolve().parents[2] / "scripts" / "governance"
sys.path.insert(0, str(GOVERNANCE))
import ci_generated  # noqa: E402

TOOL = GOVERNANCE / "apply_generated_overlay.py"
LOCK = "platform/python-sidecar/services/gochara_kernel/implementation_digest.lock.json"
SHA = "c" * 40


def lock_text(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def stale_doc() -> dict:
    now = reg.compute()
    return {**now, "implementation_digest": "0" * 64, "stages": {s: "0" * 64 for s in now["stages"]}}


def apply(artifact: Path, root: Path, sha: str = SHA):
    return subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--artifact", str(artifact), "--sha", sha, "--root", str(root)],
                          capture_output=True, text=True, timeout=60)


@pytest.fixture
def seal_checkout(tmp_path, monkeypatch):
    """(raw checkout root, verified artifact dir): the raw checkout carries a STALE committed lock; the artifact is what CI would publish for SHA."""
    root, artifact = tmp_path / "checkout", tmp_path / "artifact"
    (root / LOCK).parent.mkdir(parents=True)
    (root / LOCK).write_text(lock_text(stale_doc()))
    for path in ci_generated.OUTPUTS:
        (artifact / path).parent.mkdir(parents=True, exist_ok=True)
        (artifact / path).write_text(lock_text(reg.compute()) if path == LOCK else f"generated:{path}\n")
    (artifact / ci_generated.MANIFEST).write_text(json.dumps(ci_generated.manifest(artifact, SHA, ci_generated.OUTPUTS), indent=2) + "\n")
    monkeypatch.setattr(reg, "LOCK_PATH", root / LOCK)
    return root, artifact


def refused_code() -> str:
    with pytest.raises(seal_flow.SealRefused) as caught:
        seal_flow.check_own_checkout()
    assert caught.value.exit_code == seal_flow.EXIT_IDENTITY
    return caught.value.code


def test_raw_checkout_with_the_stale_committed_lock_is_refused(seal_checkout):
    assert refused_code() == "own_checkout_digest_mismatch"


def test_verified_overlay_makes_the_same_checkout_pass(seal_checkout):
    root, artifact = seal_checkout
    assert refused_code() == "own_checkout_digest_mismatch"
    done = apply(artifact, root)
    assert done.returncode == 0, done.stderr
    assert seal_flow.check_own_checkout() == {"implementation_digest": reg.compute()["implementation_digest"]}


def test_overlay_with_an_altered_lock_is_refused_and_leaves_the_checkout_unchanged(seal_checkout):
    root, artifact = seal_checkout
    (artifact / LOCK).write_text(lock_text({**reg.compute(), "implementation_digest": "f" * 64}))      # bytes changed, manifest digest not
    done = apply(artifact, root)
    assert done.returncode == 1 and "overlay_unverified" in done.stderr and LOCK in done.stderr
    assert json.loads((root / LOCK).read_text())["implementation_digest"] == "0" * 64
    assert refused_code() == "own_checkout_digest_mismatch"


def test_overlay_of_another_commit_is_refused(seal_checkout):
    root, artifact = seal_checkout
    done = apply(artifact, root, sha="d" * 40)
    assert done.returncode == 1 and "source SHA" in done.stderr
    assert refused_code() == "own_checkout_digest_mismatch"


def test_a_self_consistent_overlay_for_other_code_still_fails_the_own_checkout_check(seal_checkout):
    """The overlay is trusted only as far as the running code agrees with it: a lock that belongs to different code is applied but the seal still refuses."""
    root, artifact = seal_checkout
    (artifact / LOCK).write_text(lock_text(stale_doc()))
    (artifact / ci_generated.MANIFEST).write_text(json.dumps(ci_generated.manifest(artifact, SHA, ci_generated.OUTPUTS), indent=2) + "\n")
    assert apply(artifact, root).returncode == 0
    assert refused_code() == "own_checkout_digest_mismatch"


def test_only_generated_paths_are_overlaid(seal_checkout):
    root, artifact = seal_checkout
    smuggled = artifact / "platform/python-sidecar/pipeline/orchestrator/seal_job.py"
    smuggled.parent.mkdir(parents=True, exist_ok=True)
    smuggled.write_text("raise SystemExit(0)\n")
    done = apply(artifact, root)
    assert done.returncode == 1 and "unlisted_file_in_artifact" in done.stderr
    assert not (root / "platform/python-sidecar/pipeline/orchestrator/seal_job.py").exists()
    assert json.loads((root / LOCK).read_text())["implementation_digest"] == "0" * 64        # nothing was copied
