"""C43 — tests for platform/scripts/gochara-sitting-evidence-pack.sh.

The pack is a LOCAL, OFFLINE helper: it verifies each phase's MANIFEST.sha256 against the files
present, writes SITTING_EVIDENCE_INDEX.md (check id, status, file, sha256, in emission order),
and writes a top-level MANIFEST.sha256 over everything. These tests build a synthetic evidence
tree — no network, no database.

Covered: the good tree (all four phases, STOP/REVIEW statuses from .stops/.reviews, a
RUNNER_SHA256 line, a --note); a tampered file is a MISMATCH (exit 1) and is marked TAMPERED in
the index; a missing phase is exit 1 without --allow-missing and recorded-but-passing with it; a
symlink escaping the evidence dir is an exit-2 refusal; the top manifest covers the index and
verifies with shasum -c.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/gochara-sitting-evidence-pack.sh"
PHASES = ("pre-window", "pre-train", "pre-dispatch", "post-window")

CHECKS = {
    "pre-window": [("W3-legacy-relations", "PASS"), ("R2-ledger-1243", "STOP")],
    "pre-train": [("R7-roles-exist", "PASS")],
    "pre-dispatch": [("R8-ledger-diff", "REVIEW")],
    "post-window": [("P9-ledger-diff", "PASS")],
}


def build_tree(root: Path, *, skip: tuple[str, ...] = ()) -> dict[tuple[str, str], str]:
    """A synthetic evidence tree; returns {(phase, check): file content} for later tampering."""
    contents = {}
    for phase in PHASES:
        if phase in skip:
            continue
        pdir = root / phase
        pdir.mkdir(parents=True)
        lines = []
        for check, status in CHECKS[phase]:
            body = f"{phase} {check} raw output\n"
            contents[(phase, check)] = body
            (pdir / f"{check}.out").write_text(body, encoding="utf-8")
            lines.append(f"{hashlib.sha256(body.encode()).hexdigest()}  {check}.out")
            if status == "STOP":
                (pdir / ".stops").write_text(check + "\n", encoding="utf-8")
            if status == "REVIEW":
                (pdir / ".reviews").write_text(check + "\n", encoding="utf-8")
        (pdir / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if phase == "pre-window":
            (pdir / "RUNNER_SHA256").write_text("ab" * 32 + "  gochara-window-readbacks.sh\n", encoding="utf-8")
    return contents


def run_pack(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PG", "DATABASE"))}
    return subprocess.run(["bash", str(SCRIPT), "--evidence-dir", str(root), *extra],
                          capture_output=True, text=True, timeout=60, env=env)


def test_good_tree_verifies_and_indexes_everything(tmp_path: Path) -> None:
    build_tree(tmp_path)
    note = tmp_path / "steward-note.md"
    note.write_text("the sitting was quiet\n", encoding="utf-8")
    r = run_pack(tmp_path, "--note", str(note))
    assert r.returncode == 0, r.stderr
    index = (tmp_path / "SITTING_EVIDENCE_INDEX.md").read_text(encoding="utf-8")
    assert "| W3-legacy-relations | PASS |" in index
    assert "| R2-ledger-1243 | STOP |" in index          # status from .stops
    assert "| R8-ledger-diff | REVIEW |" in index        # status from .reviews
    assert "runner script sha256: " + "ab" * 32 in index
    assert "> the sitting was quiet" in index            # the note is inlined
    # emission order within pre-window: W3 line precedes R2 line
    assert index.index("W3-legacy-relations") < index.index("R2-ledger-1243")
    top = (tmp_path / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert "./SITTING_EVIDENCE_INDEX.md" in top and "./pre-window/MANIFEST.sha256" in top
    check = subprocess.run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
                           cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert check.returncode == 0, check.stderr          # the top manifest itself verifies


def test_a_tampered_file_is_a_mismatch_and_marked_in_the_index(tmp_path: Path) -> None:
    build_tree(tmp_path)
    (tmp_path / "pre-window" / "W3-legacy-relations.out").write_text("tampered\n", encoding="utf-8")
    r = run_pack(tmp_path)
    assert r.returncode == 1
    assert "MANIFEST MISMATCH: pre-window/W3-legacy-relations.out" in r.stderr
    assert "| W3-legacy-relations | TAMPERED |" in (tmp_path / "SITTING_EVIDENCE_INDEX.md").read_text(encoding="utf-8")


def test_a_missing_phase_stops_unless_allowed(tmp_path: Path) -> None:
    build_tree(tmp_path, skip=("pre-train",))
    r = run_pack(tmp_path)
    assert r.returncode == 1
    assert "MISSING PHASE: pre-train" in r.stderr
    ok = run_pack(tmp_path, "--allow-missing", "pre-train")
    assert ok.returncode == 0, ok.stderr
    index = (tmp_path / "SITTING_EVIDENCE_INDEX.md").read_text(encoding="utf-8")
    assert "## Phase: pre-train" in index and "MISSING (allowed by --allow-missing)" in index


def test_a_symlink_escaping_the_dir_is_an_exit2_refusal(tmp_path: Path) -> None:
    build_tree(tmp_path)
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("nope\n", encoding="utf-8")
    (tmp_path / "pre-window" / "escape.out").symlink_to(outside)
    r = run_pack(tmp_path)
    assert r.returncode == 2
    assert "REFUSAL: symlink escapes --evidence-dir" in r.stderr


def test_a_missing_evidence_dir_is_an_exit2_refusal(tmp_path: Path) -> None:
    r = run_pack(tmp_path / "no-such-dir")
    assert r.returncode == 2
    assert "REFUSAL: --evidence-dir is not a directory" in r.stderr
