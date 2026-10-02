#!/usr/bin/env python3
"""Mutation proof: neuter one refusal at a time in a COPY of the executor and show that its test goes RED.

  python3 tests/mutation_proof.py [name-substring ...]      (no argument: every mutation)

For each mutation: copy the folder to a temp dir, apply ONE exact-string replacement to ONE file of the copy
(asserting the string was present exactly once), run the named tests there, and require a non-zero pytest exit (red).
The un-mutated copy must be green first. Prints one line per mutation. The repository file is never modified.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent

MUTATIONS = [
    # (name, file, old, new, pytest -k expression)
    # ---- v1.1 rules (unchanged)
    ("P5 no-build-in-flight neutered", "orphan_receipts_exec.py",
     'chk("P5_no_build_in_flight", len(inflight) == 0,', 'chk("P5_no_build_in_flight", True,', "build_in_flight"),
    ("P3 --min-build-after comparison neutered", "orphan_receipts_exec.py",
     "after_min = (min_after is None) or (", "after_min = True or (", "older_than_min_build_after or build_created_before_min"),
    ("V resolver verdict-diff check neutered", "orphan_receipts_exec.py",
     'chk("V_verdict_diff_is_exactly_the_asset", vdiff == {asset: list(EXPECTED_VERDICT)},',
     'chk("V_verdict_diff_is_exactly_the_asset", True,', "extra_asset or does_not_become_resolved"),
    ("A ACL-diff check neutered", "orphan_receipts_exec.py",
     'chk("A_acl_diff_empty", acl_diff == [],', 'chk("A_acl_diff_empty", True,', "drift_mid_flight"),
    ("P1 registry-declares-partition (orphan by definition) neutered", "orphan_receipts_exec.py",
     'chk("P1_registry_declares_partition", declares,', 'chk("P1_registry_declares_partition", True,',
     "registry_declares_no_partition or whole_asset_key_itself"),
    ("--expect-evidence made optional at --apply (parse_args)", "orphan_receipts_exec.py",
     "    if a.apply and not a.expect_evidence:\n        p.error(", "    if False and not a.expect_evidence:\n        p.error(",
     "apply_requires_expect_plan"),
    ("--expect-evidence made optional at --apply (execute)", "orphan_receipts_exec.py",
     "            if not args.expect_evidence:\n                refuse(o,", "            if False:\n                refuse(o,",
     "apply_requires_expect_plan or missing_expect_evidence"),
    ("E evidence-digest comparison neutered", "orphan_receipts_exec.py",
     'chk("E_evidence_digest_matches_expected", args.expect_evidence == evidence_digest,',
     'chk("E_evidence_digest_matches_expected", True,', "wrong_evidence_digest"),
    ("execute() asset/chart validation removed", "orphan_receipts_exec.py",
     "    if validate_params(args.asset, args.chart) != args.chart:", "    if False:", "execute_validates"),
    ("resolver: receipt-build split check removed", "resolver_verdicts.sql",
     "count(DISTINCT receipt_build_id) <> 1\n           OR ", "", "different_receipt_builds"),
    ("resolver: spec-digest split check removed", "resolver_verdicts.sql",
     "\n           OR count(DISTINCT output_digest_spec_sha256) <> 1", "", "different_spec_digests"),
    # ---- v3: GATE_V2 launch binding
    ("launch check removed from main()", "orphan_receipts_exec.py",
     "    gate_fp = launch_gate()             # FIRST: before the arguments are even parsed\n    args = parse_args(sys.argv[1:] if argv is None else argv)",
     "    gate_fp = es.fingerprint()\n    args = parse_args(sys.argv[1:] if argv is None else argv)", "started_directly"),
    ("launch check moved AFTER argument parsing", "orphan_receipts_exec.py",
     "    gate_fp = launch_gate()             # FIRST: before the arguments are even parsed\n    args = parse_args(sys.argv[1:] if argv is None else argv)",
     "    args = parse_args(sys.argv[1:] if argv is None else argv)\n    gate_fp = launch_gate()", "started_directly"),
    ("marker verification bypassed (require_gate_launch not called)", "orphan_receipts_exec.py",
     "    return es.require_gate_launch(environ, expected_gate_sha=GATE_PINS[\"prerun_gate.py\"],\n                                  expected_launcher_sha=GATE_PINS[\"run_gated.sh\"])",
     "    return es.fingerprint()", "launch_gate_refuses_without or started_directly or forged or stale"),
    ("gate sha pin not enforced (expected_gate_sha=None)", "orphan_receipts_exec.py",
     'expected_gate_sha=GATE_PINS["prerun_gate.py"],', "expected_gate_sha=None,", "differ_from_the_pins or edited_gate_file"),
    ("launcher sha pin not enforced (expected_launcher_sha=None)", "orphan_receipts_exec.py",
     'expected_launcher_sha=GATE_PINS["run_gated.sh"])', "expected_launcher_sha=None)", "differ_from_the_pins"),
    ("executor_standards.py pin check neutered", "orphan_receipts_exec.py",
     'if es.sha256_file(es.__file__) != GATE_PINS["executor_standards.py"]:', "if False:",
     "differ_from_the_pins or edited_executor_standards"),
    ("pinned prerun_gate.py sha changed by one character", "orphan_receipts_exec.py",
     '"prerun_gate.py": "ba65d82a338', '"prerun_gate.py": "aa65d82a338', "byte_identical_gate_v2"),
    ("gate file edited (no longer byte-identical to gate_v2)", "prerun_gate.py",
     "GATE_VERSION = \"GATE_V2\"", "GATE_VERSION = \"GATE_V2\"  # edited", "byte_identical_gate_v2 or edited_gate_file"),
    # ---- v3: plan hash binds the gate
    ("plan hash no longer folds in the gate fingerprint", "orphan_receipts_exec.py",
     '{"gate_sha256": gate["prerun_gate.py"], "run_gated_sha256": gate["run_gated.sh"]})',
     '{"gate_sha256": "0" * 64, "run_gated_sha256": "0" * 64})', "changing_any_gate_file_sha or binds_the_executor"),
    ("plan text no longer names executor_standards.py sha", "orphan_receipts_exec.py",
     'gate["prerun_gate.py"], gate["run_gated.sh"], gate["executor_standards.py"]),',
     'gate["prerun_gate.py"], gate["run_gated.sh"], "0" * 64),', "plan_text_names_the_three or plan_txt_is_the_rendering"),
    # ---- v3: outcome.json in every mode
    ("dry run no longer declares its outcome", "orphan_receipts_exec.py",
     'return 0, conclude(o, result, "dry_run", digest)', "return 0, result", "writes_outcome_dry_run"),
    ("apply no longer declares its outcome", "orphan_receipts_exec.py",
     'return 0, conclude(o, result, "applied", digest)', "return 0, result", "writes_outcome_applied"),
    ("failed outcome loses the failed check names", "orphan_receipts_exec.py",
     'o.fail(list(checks) or ["refused_unspecified"], digest)', 'o.fail(["refused_unspecified"], digest)',
     "refused_apply_writes_failed or refused_dry_run_writes_failed or lock_timeout_failure"),
    ("counterfactual dry run recorded as a dry_run outcome", "orphan_receipts_exec.py",
     'return 3, conclude(o, result, "failed", digest, ["counterfactual_no_min_build_after"])',
     'return 3, conclude(o, result, "dry_run", digest)', "counterfactual_dry_run_is_never"),
    ("argument refusals no longer name their check", "orphan_receipts_exec.py",
     '    o.fail([check])\n    raise SystemExit("REFUSED: " + message)', '    raise SystemExit("REFUSED: " + message)',
     "argument_refusals_write or hash_mismatch_on_apply or missing_expect_evidence_at_execute or valid_marker"),
    ("naive-timezone refusal no longer recorded", "orphan_receipts_exec.py",
     '            o.fail(["args_min_build_after_not_tz_aware"])\n', "", "argument_refusals_write"),
    ("outcome file write error masks the real result (SafeOutcome)", "orphan_receipts_exec.py",
     "        except OSError as exc:\n            self.write_error = type(exc).__name__", "        except ZeroDivisionError as exc:\n            self.write_error = type(exc).__name__",
     "unwritable_outcome_never_masks or silent_return_and_unwritable"),
    ("run directory reused on collision (outcome of another run overwritten)", "orphan_receipts_exec.py",
     "        d.mkdir(mode=0o700)               # NOT exist_ok", "        d.mkdir(mode=0o700, exist_ok=True)               # NOT exist_ok", "same_second"),
    ("outcome_guard no longer records an exception / SystemExit (standards copy)", "executor_standards.py",
     "        if exc_type is not None and not self.done:", "        if False:",
     "failure_to_connect or exception_inside or systemexit_inside or lock_timeout_failure"),
    ("outcome_guard no longer records a silent return (standards copy)", "executor_standards.py",
     "        elif not self.done:\n            self._write(\"failed\", None, [\"no_outcome_recorded\"])", "        elif False:\n            pass",
     "silent_return_and_unwritable"),
    # ---- v3: ORPH_TEST_EVIDENCE_ROOT
    ("evidence-root variable honoured outside pytest (refusal removed)", "orphan_receipts_exec.py",
     "    if PYTEST_ENV not in environ:\n", "    if False:\n", "outside_pytest or stray or cli_refuses_the_stray"),
    ("empty evidence-root variable falls back to the real root", "orphan_receipts_exec.py",
     "    if not root:\n", "    if False:\n", "empty_inside_pytest"),
    # ---- rev2 (adversarial review of the gate and this executor)
    ("D twin-integrity check neutered", "orphan_receipts_exec.py",
     'chk("D_twin_integrity_unchanged", twin_before == twin_after,', 'chk("D_twin_integrity_unchanged", True,', "only_the_pairing_breaks"),
    ("commit not marked on the outcome guard (failed written after a committed apply)", "orphan_receipts_exec.py",
     "                    o.mark_committed(digest)                                  # IMMEDIATELY after the commit",
     "                    pass", "after_commit or first_step_after_the_commit or during_commit"),
    ("SafeOutcome no longer records applied for a committed run that was interrupted", "orphan_receipts_exec.py",
     "        if self.committed and not self.done:", "        if False:", "after_commit or first_step_after_the_commit or during_commit or signal_handlers"),
    ("signals not held around the COMMIT", "orphan_receipts_exec.py",
     "                signal.pthread_sigmask(signal.SIG_BLOCK, _HELD_SIGNALS)", "                pass", "during_commit"),
    ("SIGTERM / SIGHUP handlers not installed", "orphan_receipts_exec.py",
     "        signal.signal(sig, _on_terminate)", "        pass", "signal_handlers"),
    ("execute() not given the launch fingerprint (under_test lost)", "orphan_receipts_exec.py",
     "execute(args, connect_admin, gate_fp=gate_fp)", "execute(args, connect_admin)", "passes_the_launch_fingerprint or marker_and_the_executor_accepts"),
    ("outcome.json does not record under_test (standards copy)", "executor_standards.py",
     '"under_test": bool(gate_fp.get("under_test", False)),', '"under_test": False,', "under_test_from_the_launch or marker_and_the_executor_accepts"),
    ("verifier accepts an under_test marker outside tests (standards copy)", "executor_standards.py",
     '    if ut == "1" and not verifier_under_test(environ):', "    if False:", "under_test_marker_in_an_operators"),
    ("evidence-root flag honoured without the test env var", "orphan_receipts_exec.py",
     "    if TEST_EVIDENCE_ENV not in environ:\n        return EVIDENCE_ROOT", "    if TEST_EVIDENCE_ENV not in environ:\n        return flag or EVIDENCE_ROOT",
     "evidence_root_flag_is_ignored"),
]


def run(workdir, expr):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(workdir / "tests"), "-k", expr],
                          capture_output=True, text=True, cwd=workdir)


def main():
    bad = 0
    only = [a.lower() for a in sys.argv[1:]]
    for name, fname, old, new, expr in MUTATIONS:
        if only and not any(o in name.lower() for o in only):
            continue
        with tempfile.TemporaryDirectory(prefix="mut_") as t:
            w = pathlib.Path(t) / "orphan_receipts"
            shutil.copytree(SRC, w, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "evidence"))
            green = run(w, expr)
            f = w / fname
            text = f.read_text()
            assert text.count(old) == 1, "mutation target not found exactly once: %r" % old
            f.write_text(text.replace(old, new))
            red = run(w, expr)
            ok = green.returncode == 0 and red.returncode != 0
            tail = [l for l in red.stdout.splitlines() if l.startswith(("FAILED", "ERROR")) or " failed" in l][:3]
            print("%-62s baseline=%s mutant=%s  %s" % (name, "green" if green.returncode == 0 else "RED(!)", "RED" if red.returncode else "GREEN(!)",
                                                      "OK" if ok else "NOT PROVEN"), flush=True)
            for l in tail:
                print("      ", l, flush=True)
            bad += 0 if ok else 1
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
