#!/usr/bin/env python3
"""Mutation proof: neuter one rule at a time in a COPY of the gate folder and show that its tests go RED.

  python3 tests/mutation_proof.py

For each mutation: copy the folder to a temp dir, apply ONE exact-string replacement to ONE file of the copy (asserting the
string is present exactly once), run the named tests there, and require a non-zero pytest exit (red). The un-mutated copy must be
green first. Prints one line per mutation and exits non-zero if any mutation is NOT PROVEN. The repository files are never modified.
The six rules the SS contract names are the first six lines (tagged REQUIRED); the rest are extra.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent

MUTATIONS = [
    # (name, file, old, new, pytest -k expression)
    ("REQUIRED a: pgenv sourcing no longer checked (falls through to ambient PG*)", "prerun_gate.py",
     "               '[ -r \"$f\" ] || exit 97; '\n               'source \"$f\" >/dev/null 2>&1 || exit 97; '",
     "               'source \"$f\" >/dev/null 2>&1; '", "pgenv"),
    ("REQUIRED b-limit: history asks --limit 20 instead of 100", "prerun_gate.py",
     "HISTORY_LIMIT = 100", "HISTORY_LIMIT = 20", "limit_100 or beyond_position_20 or beyond_the_newest_100"),
    ("REQUIRED b-per-status: per-status union queries removed", "prerun_gate.py",
     'NON_COMPLETED_STATUSES = ("queued", "in_progress", "waiting", "pending", "requested")', "NON_COMPLETED_STATUSES = ()",
     "per_non_completed_status or beyond_the_newest_100 or every_non_completed_status"),
    ("REQUIRED c: gate no longer refuses the test evidence root / pytest env", "prerun_gate.py",
     "    if bad:\n        say(", "    if False:\n        say(", "orph_test_evidence_root or pytest_current_test"),
    ("REQUIRED c: run_gated.sh no longer refuses the test evidence root", "run_gated.sh",
     'if [ -n "${ORPH_TEST_EVIDENCE_ROOT+x}" ]; then', "if false; then", "refuses_the_test_evidence_root"),
    ("REQUIRED d: run_gated.sh execs the target even when the gate fails", "run_gated.sh",
     'if [ "$rc" -ne 0 ]; then', "if false; then", "not_started"),
    ("REQUIRED d: run_gated.sh passes the args word-split (exec $* instead of exec \"$@\")", "run_gated.sh",
     'starting target" >&2\nexec "$@"', 'starting target" >&2\nexec $*', "intact or word_split"),
    ("d: run_gated.sh exits 0 after a failed gate", "run_gated.sh",
     '  exit "$rc"\nfi', "  exit 0\nfi", "not_started or exit_code_class"),
    ("REQUIRED role check: psql session role no longer compared with suvarna_reader", "prerun_gate.py",
     "    if role != EXPECTED_ROLE:", "    if False:", "role"),
    ("gate prints to stdout instead of stderr", "prerun_gate.py",
     'sys.stderr.write(line + "\\n")', 'sys.stdout.write(line + "\\n")', "zero_zero or nothing_secret or count_lines"),
    ("empty history list no longer fails closed", "prerun_gate.py",
     "    if not data and not allow_empty:", "    if False:", "empty_history"),
    ("ambient PG* variables reach the psql subshell", "prerun_gate.py",
     "if not k.startswith(\"PG\") and k not in", "if True and k not in", "ambient_pg"),
    ("a non-zero gh exit no longer fails closed", "prerun_gate.py",
     "        if rc != 0:\n            raise GateError(EXIT_READ_FAILED, \"%s failed", "        if False:\n            raise GateError(EXIT_READ_FAILED, \"%s failed",
     "nonzero_exit or gh_read_failures"),
    ("standards: marker check recomputation neutered", "executor_standards.py",
     "    if _check(gate_sha, launcher_sha, int(epoch_s), nonce) != check:", "    if False:", "forged_check"),
    ("standards: live gate sha comparison neutered", "executor_standards.py",
     '    if gate_sha != live["gate_sha256"]:', "    if False:", "edited_gate_file"),
    ("standards: marker age check neutered", "executor_standards.py",
     "    if age < -MAX_FUTURE_SKEW_S:", "    if False:", "stale_and_future"),
    ("standards: outcome file made world-readable", "executor_standards.py",
     "os.fchmod(fd, 0o600)", "os.fchmod(fd, 0o644)", "fields_and_permissions"),
    ("standards: guard no longer records a silent return as failed", "executor_standards.py",
     '            self._write("failed", None, ["no_outcome_recorded"])', "            pass", "silent_return"),
    ("run_gated.sh: launch marker never exported", "run_gated.sh",
     'export GATE_V2_LAUNCH="$marker"', ': "$marker"', "launch_marker_is_set"),
]


def run(workdir, expr):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(workdir / "tests"), "-k", expr],
                          capture_output=True, text=True, cwd=workdir)


def main():
    bad = 0
    for name, fname, old, new, expr in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="mut_") as t:
            w = pathlib.Path(t) / "gate_v2"
            shutil.copytree(SRC, w, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            green = run(w, expr)
            f = w / fname
            text = f.read_text()
            assert text.count(old) == 1, "mutation target not found exactly once: %r" % old
            f.write_text(text.replace(old, new))
            red = run(w, expr)
            ok = green.returncode == 0 and red.returncode != 0
            tail = [l for l in red.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))][:2]
            print("%-84s baseline=%s mutant=%s  %s" % (name, "green" if green.returncode == 0 else "RED(!)",
                                                      "RED" if red.returncode else "GREEN(!)", "OK" if ok else "NOT PROVEN"))
            for l in tail:
                print("      ", l[:150])
            bad += 0 if ok else 1
    print("%d/%d mutations proven" % (len(MUTATIONS) - bad, len(MUTATIONS)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
