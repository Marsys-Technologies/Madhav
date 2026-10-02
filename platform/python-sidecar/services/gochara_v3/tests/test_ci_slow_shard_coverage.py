"""C23 — shard-coverage guard (steward ruling M20261002T182324-6b9a): every
file under services/gochara_v3/tests that carries the slow_real_ephemeris
marker must appear in exactly one slow shard of the governance-gates-gochara
job in .github/workflows/ci.yml — a NEW slow file must FAIL here (loudly)
instead of being silently unrun, and a dropped shard must fail the same way.

Pure: parses the workflow YAML as text and the test directory as files;
imports nothing from the engine. Runs in the job's fast leg (it carries no
slow/benchmark marker itself).
"""
from __future__ import annotations

import re
from pathlib import Path

SIDECAR = Path(__file__).resolve().parents[3]
REPO_ROOT = SIDECAR.parents[1]
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
GOCHARA_TESTS = SIDECAR / "services" / "gochara_v3" / "tests"

SHARD_FILES_RE = re.compile(r'shard_files:\s*"([^"]+)"')
SLOW_MARK_RE = re.compile(
    r"pytestmark\s*=\s*pytest\.mark\.slow_real_ephemeris"
    r"|@pytest\.mark\.slow_real_ephemeris"
)


def _slow_marked_files() -> set[str]:
    # actual marker usage only — a mere mention in a docstring (this file's own
    # header, for instance) does not make a file slow.
    return {
        path.name
        for path in GOCHARA_TESTS.glob("test_*.py")
        if SLOW_MARK_RE.search(path.read_text(encoding="utf-8"))
    }


def _sharded_files() -> list[str]:
    ci = CI_YML.read_text(encoding="utf-8")
    files: list[str] = []
    for group in SHARD_FILES_RE.findall(ci):
        files.extend(
            Path(token).name
            for token in group.split()
            if token.startswith("services/gochara_v3/tests/")
        )
    return files


def test_every_slow_real_ephemeris_file_is_in_exactly_one_ci_shard():
    slow = _slow_marked_files()
    sharded = _sharded_files()
    assert slow, "sanity: at least one slow_real_ephemeris file must exist"
    assert sharded, "sanity: ci.yml must declare shard_files entries"
    missing = slow - set(sharded)
    assert not missing, (
        f"slow_real_ephemeris files in NO governance-gates-gochara shard: "
        f"{sorted(missing)} — add them to a shard_files entry in "
        ".github/workflows/ci.yml (and rebalance), or they are never run"
    )
    extras = set(sharded) - slow
    assert not extras, (
        f"shard_files entries that are NOT slow-marked files: {sorted(extras)} "
        "— a stale shard list shrinks coverage silently"
    )
    duplicates = sorted({f for f in sharded if sharded.count(f) > 1})
    assert not duplicates, f"files in more than one shard: {duplicates}"
