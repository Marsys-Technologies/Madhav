#!/usr/bin/env python3
"""Mutation proof: neuter one rule at a time in a COPY of the gate folder (inside a temp mini-repo that also holds the CI-collected tests) and show that its tests go RED.

  python3 tests/mutation_proof.py [name-substring ...]     (arguments run only the matching mutations, e.g. "rev3": run the proof in chunks)

For each mutation: copy the folder to a temp dir, apply ONE exact-string replacement to ONE file of the copy (asserting the
string is present exactly once), run the named tests there, and require a non-zero pytest exit (red). The un-mutated copy must be
green first. Prints one line per mutation and exits non-zero if any mutation is NOT PROVEN. The repository files are never modified.
The six rules the SS contract names are the REQUIRED lines; the rest are extra. The last block ("rev2") is one mutation per fix of the
second adversarial review (deploy ref/event, repo pin, malformed input, epoch bounds, under_test, database, target check).
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent                      # .../exec/gate_v2 (single source of truth for the gate files)
REPO = SRC.parents[4]
REL_GATE = SRC.relative_to(REPO)                                         # 00_ARCHITECTURE/briefs/suvarna/exec/gate_v2
REL_TESTS = pathlib.Path("platform/scripts/governance/__tests__")        # where CI collects the pytest files
TEST_FILES = ["gate_v2_helpers.py", "test_gate_v2_prerun_gate.py", "test_gate_v2_run_gated.py", "test_gate_v2_executor_standards.py"]

MUTATIONS = [
    # (name, file, old, new, pytest -k expression)
    ("REQUIRED a: pgenv sourcing no longer checked (falls through to ambient PG*)", "prerun_gate.py",
     "               '[ -r \"$f\" ] || exit 97; '\n               'source \"$f\" >/dev/null 2>&1 || exit 97; '",
     "               'source \"$f\" >/dev/null 2>&1; '", "pgenv"),
    ("REQUIRED b-limit: history asks --limit 20 instead of 100", "prerun_gate.py",
     "HISTORY_LIMIT = 1000", "HISTORY_LIMIT = 20", "limit_1000 or limit_passed_to_gh or beyond_position_20 or beyond_the_newest_100"),
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
     'exec -- "$@"\ndie "target_not_executable" 98', 'exec $*\ndie "target_not_executable" 98', "intact or word_split"),
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
     '        check_ok = _check(gate_sha, launcher_sha, epoch, nonce, ut == "1") == check', "        check_ok = True", "forged_check"),
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
    # ---- rev2 (adversarial review): one mutation per fix
    ("rev2-1: deploy query filtered to --branch main again (dispatch on a feature ref invisible)", "prerun_gate.py",
     '"--workflow", WORKFLOW, "--limit", str(HISTORY_LIMIT),', '"--workflow", WORKFLOW, "--branch", "main", "--limit", str(HISTORY_LIMIT),',
     "non_main_ref or gh_queries_history"),
    ("rev2-1: pull_request runs counted as in-flight deploys", "prerun_gate.py",
     '            if x.get("event") == EXCLUDED_EVENT:', "            if False:", "pull_request_run"),
    ("rev2-1: unknown / missing event excluded (fails open)", "prerun_gate.py",
     '            if x.get("event") == EXCLUDED_EVENT:', '            if x.get("event") != "workflow_run":', "unknown_or_missing_event or non_pull_request_run"),
    ("rev2-1: full per-status page of PR runs no longer fails closed", "prerun_gate.py",
     "        if saturation_matters and excluded and len(data) >= HISTORY_LIMIT:", "        if False:", "full_per_status"),
    ("rev2-2: repository no longer pinned with -R", "prerun_gate.py",
     '"run", "list", "-R", REPO, ', '"run", "list", ', "pins_the_repository or gh_queries_history"),
    ("rev2-2: GH_REPO / GH_HOST not stripped from gh's environment", "prerun_gate.py",
     "    return {k: v for k, v in environ.items() if k not in GH_STRIPPED_ENV}", "    return dict(environ)", "pins_the_repository"),
    ("rev2-3: catch-all removed (an unexpected error is a traceback again)", "prerun_gate.py",
     "    except BaseException as exc:\n        try:\n            say(", "    except ZeroDivisionError as exc:\n        try:\n            say(",
     "unexpected_exception or exception_while_printing"),
    ("rev2-3: gh output that is not UTF-8 no longer classified", "prerun_gate.py",
     "    except UnicodeDecodeError:\n        raise GateError(EXIT_READ_FAILED, label + \" output is not valid UTF-8\")",
     "    except ZeroDivisionError:\n        raise GateError(EXIT_READ_FAILED, label + \" output is not valid UTF-8\")", "read_failures_fail_closed"),
    ("rev2-3: RecursionError from a deeply nested JSON no longer classified", "prerun_gate.py",
     "    except (ValueError, RecursionError):", "    except ValueError:", "gh_read_failures_fail_closed"),
    ("rev2-3: psql count accepted with str.isdigit() (superscript two crashes int())", "prerun_gate.py",
     "count.isascii() and count.isdecimal()", "count.isdigit()", "psql_read_failures_fail_closed"),
    ("rev2-3: psql count length no longer bounded", "prerun_gate.py",
     "MAX_COUNT_DIGITS = 12", "MAX_COUNT_DIGITS = 100000", "psql_read_failures_fail_closed"),
    ("rev2-4: epoch no longer limited to 12 ASCII digits", "executor_standards.py",
     "1 <= len(epoch_s) <= MAX_EPOCH_DIGITS and epoch_s.isascii() and epoch_s.isdecimal()", "epoch_s.isdigit()", "epoch"),
    ("rev2-4: int()/ValueError of a huge epoch no longer caught", "executor_standards.py",
     "    except (ValueError, OverflowError):", "    except ZeroDivisionError:", "huge_epochs"),
    ("rev2-4: OverflowError in the age sum no longer caught", "executor_standards.py",
     "    except OverflowError:\n        return False, \"malformed_marker\"", "    except ZeroDivisionError:\n        return False, \"malformed_marker\"", "huge_epochs"),
    ("rev2-7: under_test flag not part of the marker check input", "executor_standards.py",
     '                                    "1" if under_test else "0"]).encode()).hexdigest()', '                                    "0"]).encode()).hexdigest()',
     "under_test"),
    ("rev2-7: verifier accepts an under_test marker outside tests", "executor_standards.py",
     '    if ut == "1" and not verifier_under_test(environ):', "    if False:", "under_test"),
    ("rev2-7: outcome.json does not record under_test", "executor_standards.py",
     '"under_test": bool(gate_fp.get("under_test", False)),', '"under_test": False,', "outcome_json_records_under_test"),
    ("rev2-7: run_gated.sh never marks the marker under_test", "run_gated.sh",
     'if [ "${GATE_V2_UNDER_TEST:-}" = "1" ]; then ut=1; fi', ":", "under_test_launch"),
    ("rev2-8a: database no longer compared with amjis", "prerun_gate.py",
     "    if database != EXPECTED_DATABASE:", "    if False:", "database"),
    ("rev2-8b: run_gated.sh exec without -- (a dash-named target is an exec option)", "run_gated.sh",
     'set +e\nshopt -s execfail\nexec -- "$@"', 'set +e\nshopt -s execfail\nexec "$@"', "dash"),
    ("rev2-8c: target not checked before the gate / OK line (98)", "run_gated.sh",
     'target_ok "$1" || die "target_not_executable" 98', 'target_ok "$1" || true', "98 or exec_ed"),
    ("rev2-8c: a failed final exec no longer exits 98", "run_gated.sh",
     'exec -- "$@"\ndie "target_not_executable" 98', 'exec -- "$@"', "cannot_be_exec"),
    # ---- rev3: one mutation per fix
    ("rev3-1: backstop fires at 100 instead of at the 1000 limit", "prerun_gate.py",
     "len(data) >= HISTORY_LIMIT:", "len(data) >= 100:", "full_per_status"),
    ("rev3-1: backstop removed (a full page of PR runs passes)", "prerun_gate.py",
     "        if saturation_matters and excluded and len(data) >= HISTORY_LIMIT:", "        if False:", "full_per_status"),
    ("rev3-5: no signal handlers installed (a SIGTERM kills the gate silently)", "prerun_gate.py",
     "        if signal.getsignal(sig) != signal.SIG_IGN:\n            signal.signal(sig, _on_signal)", "        pass", "termination_signal"),
    ("rev3-5: gh child not killed on a signal", "prerun_gate.py",
     "    except BaseException as exc:                           # the child must never outlive the gate (timeout, signal, anything)\n        try:\n            os.killpg(proc.pid, signal.SIGKILL)",
     "    except BaseException as exc:                           # the child must never outlive the gate (timeout, signal, anything)\n        try:\n            os.killpg(proc.pid, 0)", "termination_signal"),
    ("rev3-5: a second signal is not ignored during the cleanup", "prerun_gate.py",
     "        signal.signal(sig, signal.SIG_IGN)\n    raise GateSignal(signum)", "        pass\n    raise GateSignal(signum)", "second_signal"),
    ("rev3-5: an already ignored SIGHUP is replaced by a handler (nohup protection lost)", "prerun_gate.py",
     "        if signal.getsignal(sig) != signal.SIG_IGN:", "        if True:", "ignored_at_start"),
    ("rev3-6: exit 96 labelled read_failed again", "prerun_gate.py",
     'EXIT_ROLE: "wrong_role_or_database", ', "", "own_labels"),
    ("rev3-6: exit 97 labelled read_failed again", "prerun_gate.py",
     'EXIT_PGENV: "pgenv_failed", ', "", "own_labels"),
    ("rev3-6: GH_CONFIG_DIR / GH_PATH no longer stripped", "prerun_gate.py",
     ', "GH_CONFIG_DIR", "GH_PATH")', ")", "pins_the_repository"),
    ("rev3-3: commit_state_unknown is not a valid outcome status (standards copy)", "executor_standards.py",
     'STATUSES = ("dry_run", "applied", "failed", "commit_state_unknown")', 'STATUSES = ("dry_run", "applied", "failed")', "commit_state_unknown"),
]


def run(root, expr):
    tests = [str(root / REL_TESTS / f) for f in TEST_FILES if f.startswith("test_")]
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *tests, "-k", expr],
                          capture_output=True, text=True, cwd=root)


def main():
    bad = 0
    only = [a.lower() for a in sys.argv[1:]]                                   # optional name filters (run the proof in chunks)
    selected = [m for m in MUTATIONS if not only or any(o in m[0].lower() for o in only)]
    for name, fname, old, new, expr in selected:
        with tempfile.TemporaryDirectory(prefix="mut_") as t:
            root = pathlib.Path(t)                                              # a mini repo: same repo-relative layout as the real one
            w = root / REL_GATE
            shutil.copytree(SRC, w, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            (root / REL_TESTS).mkdir(parents=True)
            for tf in TEST_FILES:
                shutil.copy(REPO / REL_TESTS / tf, root / REL_TESTS / tf)
            green = run(root, expr)
            f = w / fname
            text = f.read_text()
            assert text.count(old) == 1, "mutation target not found exactly once: %r" % old
            f.write_text(text.replace(old, new))
            red = run(root, expr)
            ok = green.returncode == 0 and red.returncode != 0
            tail = [l for l in red.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))][:2]
            print("%-84s baseline=%s mutant=%s  %s" % (name, "green" if green.returncode == 0 else "RED(!)",
                                                      "RED" if red.returncode else "GREEN(!)", "OK" if ok else "NOT PROVEN"), flush=True)
            for l in tail:
                print("      ", l[:150])
            bad += 0 if ok else 1
    print("%d/%d mutations proven" % (len(selected) - bad, len(selected)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
