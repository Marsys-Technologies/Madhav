"""TRIAL_READY T22 (TR-BIND): the lane ledger checker's own proof, run as a test.

`lane_ledger_selftest.py` builds a throwaway git repository with fake review result files and proves two things per scenario (N.8): the checker CAN read true (the control), and each
single planted defect -- a patch that differs from the reviewed one, a merge parent that is not the reviewed head, a squash that carries unreviewed content, an open BLOCKING finding,
a review file changed after the ledger, a stale ledger, a lane with no review, a missing lane, an unreadable ref -- flips it to false (or, for an unreadable ref, to null: exit 2).
This file only runs that proof under pytest so the registry can bind T22 to it; the checker itself is `lane_ledger_check.py`.
"""
import os
import subprocess
import sys
from pathlib import Path

GOV = Path(__file__).resolve().parents[1]


def test_every_planted_lane_ledger_defect_flips_the_checker_and_the_control_reads_true(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["TMPDIR"] = str(tmp_path)
    r = subprocess.run([sys.executable, "-I", str(GOV / "lane_ledger_selftest.py")], capture_output=True, text=True, env=env, timeout=600)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-1500:]
    assert "scenarios behaved" in r.stdout and "FAIL" not in r.stdout, r.stdout[-3000:]
