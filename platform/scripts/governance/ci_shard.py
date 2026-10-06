#!/usr/bin/env python3
"""ci_shard.py: deterministic, complete, disjoint partition of the governance test files across CI shards.

The `Governance Tool Tests (pytest)` job outgrew its 10-minute ceiling as the Nikaṣa suites grew (median ~8.5 min, max ~10 min on main).
It now runs as K parallel shard jobs (test steps only) plus an aggregate job that keeps the ORIGINAL job name, so the required check and
every `ci_job_passed` plan detector that names it keep meaning "the whole governance test directory passed".

  python3 ci_shard.py --index I --count K     print the test files of shard I (1-based), one per line
  python3 ci_shard.py --count K --verify      fail unless the K shards together are exactly every test file, each once

Assignment: every `test_*.py` / `*_test.py` under `__tests__/` (the files pytest would collect), heaviest file first (a size proxy for run
time, replaced by measured seconds for the few files in CI_SECONDS; ties by path), each placed on the currently lightest shard (ties: lowest index). Pure function of the tree: no timings, no randomness,
so a shard's content does not move between runs. A new test file lands in some shard automatically; nothing is listed by hand.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent / "__tests__"


def test_files(root: Path = TESTS) -> list[Path]:
    """Exactly what pytest's default collection takes from the directory (test_*.py, *_test.py), by repo-relative sorted path."""
    found = {p for pat in ("test_*.py", "*_test.py") for p in root.rglob(pat) if p.is_file()}
    return sorted(found, key=lambda p: p.as_posix())


# File size is a poor proxy for run time for a few files: the mutation-testing suites of the E5.7 drill run their mutants in a process pool and take
# minutes on a CI runner while being no larger than their neighbours. For the 15 files that dominate, the measured CI run time (seconds, from the
# 2026-10-05 shard logs and a full timing run, re-measured on the 2026-10-05 merge-group runs of the L0-L2 build-out (files of 20 s or more; the build-out made the census-rollup suites 3-4x slower) after the mutant suites were parallelised: the mirror wiring file went from 330 s to about 80 s; the serial files were about half their time on a loaded workstation) replaces the size proxy, converted
# to "bytes" at BYTES_PER_SECOND so one greedy pass still orders everything. Still a pure function of the tree plus this table: no timings are read
# at run time, a shard's content does not move between runs. A listed name that is not a test file fails test_ci_shard (the table cannot rot silently).
BYTES_PER_SECOND = 3300
CI_SECONDS = {
    "test_e5_7_mirror_wiring.py": 252,
    "test_e1_9_assets_scope.py": 25,
    "test_e6_1_p2a_census_facts_rollup_cli.py": 20,
    "test_e6_c11_carr_harness.py": 20,
    "test_e6_1_p1_registry_rollup.py": 111,
    "test_e1_7_census_db_identity.py": 56,
    "test_e6_1_declarations.py": 35,
    "test_e6_3_report_and_dispositions.py": 1,
    "test_e5_7_null_narr_pass.py": 75,
    "test_e5_6_rehearsal.py": 72,
    "test_e6_a_na_causes.py": 40,
    "test_e1_8_decl_stamp.py": 28,
    "test_gate_v2_prerun_gate.py": 62,
    "test_e1_1_scorecard.py": 57,
    "test_drift_detector_h35_h38.py": 56,
    "test_e6_n99_build_completion_integrity.py": 54,
    "test_e5_9_footprint.py": 50,
    "test_e1_7_nikasha_plant.py": 47,
    "test_ci_changes.py": 35,
    "test_e6_narr_guard.py": 33,
    "test_flip_detector_mutations.py": 33,
    "test_e5_7_fingerprint_declarations.py": 31,
    "test_e5_9_footprint_round4.py": 31,
    "test_e6_gh_review_corrections.py": 31,
    "test_e6_s3_alias_ldgr.py": 31,
    "test_w2_2_latest_row_registration_timing.py": 30,
    "test_e5_2_fold.py": 28,
    "test_e6_na_pin10.py": 28,
    "test_e6_1_dens_repair.py": 26,
    "test_e5_6_rehearsal_guard.py": 24,
    "test_e1_8_psql_parse.py": 22,
    "test_e6_1_narr_reaudit.py": 22,
    "test_e6_dens_label_select.py": 20,
    "test_e5_1_certify.py": 1,
    "test_e5_5_stale_certs.py": 1,
    "test_e6_3_citation_parity.py": 1,
    "test_e6_3_citation_state.py": 1,
    "test_e6_3_declarations_binding.py": 1,
    "test_e6_3_delta_fixes.py": 1,
    "test_e6_3_dispositions.py": 1,
    "test_e6_3_e51_gate.py": 1,
    "test_e6_3_e5_reconcile.py": 1,
    "test_e6_3_elevated_exact.py": 1,
    "test_e6_3_review_fixes.py": 1,
    "test_e6_3_tracker_interface.py": 1,
    "test_e6_emit_gaps_withholding.py": 1,
    "test_e6_na_r01_03.py": 1,
    "test_e6_s1_cert_writer.py": 1,
    "test_e6_s1_elevation_reader.py": 1,
    "test_e6_s3_cert_writer.py": 1,
}


def weight(path: Path) -> int:
    """The balancing weight of a test file: the file size, or for a file in CI_SECONDS its measured seconds converted to size units."""
    return CI_SECONDS[path.name] * BYTES_PER_SECOND if path.name in CI_SECONDS else path.stat().st_size


def partition(files: list[Path], count: int) -> list[list[Path]]:
    if count < 1:
        raise ValueError("count must be >= 1")
    shards: list[list[Path]] = [[] for _ in range(count)]
    load = [0] * count
    for f in sorted(files, key=lambda p: (-weight(p), p.as_posix())):
        i = min(range(count), key=lambda k: (load[k], k))
        shards[i].append(f)
        load[i] += weight(f)
    return [sorted(s, key=lambda p: p.as_posix()) for s in shards]


def verify(files: list[Path], shards: list[list[Path]]) -> list[str]:
    flat = [f for s in shards for f in s]
    problems = []
    if len(flat) != len(set(flat)):
        problems.append("a test file is in more than one shard: " + ", ".join(sorted({f.as_posix() for f in flat if flat.count(f) > 1})))
    missing = set(files) - set(flat)
    if missing:
        problems.append("test files in no shard: " + ", ".join(sorted(f.as_posix() for f in missing)))
    extra = set(flat) - set(files)
    if extra:
        problems.append("shard files that are not test files: " + ", ".join(sorted(f.as_posix() for f in extra)))
    empty = [i + 1 for i, s in enumerate(shards) if not s]
    if empty:
        problems.append(f"empty shard(s): {empty}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--index", type=int, help="1-based shard index to print")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--root", type=Path, default=TESTS)
    a = ap.parse_args(argv)
    files = test_files(a.root)
    shards = partition(files, a.count)
    if a.verify:
        probs = verify(files, shards)
        for p in probs:
            print(f"ci_shard: {p}", file=sys.stderr)
        print(f"ci_shard: {len(files)} test files in {a.count} shards: " + ", ".join(str(len(s)) for s in shards) + (" OK" if not probs else " FAIL"))
        return 1 if probs else 0
    if a.index is None or not 1 <= a.index <= a.count:
        print("ci_shard: --index must be between 1 and --count", file=sys.stderr)
        return 2
    base = a.root.parent.parent.parent.parent if a.root == TESTS else Path.cwd()
    for f in shards[a.index - 1]:
        try:
            print(f.relative_to(base).as_posix())
        except ValueError:
            print(f.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
