#!/usr/bin/env python3
"""Mutation proof: neuter one refusal at a time in a COPY of the executor and show that its test goes RED.

  python3 tests/mutation_proof.py

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
     "        if not args.expect_evidence:\n            raise SystemExit(", "        if False:\n            raise SystemExit(",
     "apply_requires_expect_plan"),
    ("E evidence-digest comparison neutered", "orphan_receipts_exec.py",
     'chk("E_evidence_digest_matches_expected", args.expect_evidence == evidence_digest,',
     'chk("E_evidence_digest_matches_expected", True,', "wrong_evidence_digest"),
    ("execute() asset/chart validation removed", "orphan_receipts_exec.py",
     "    if validate_params(args.asset, args.chart) != args.chart:", "    if False:", "execute_validates"),
    ("evidence-root flag honoured without the test env var", "orphan_receipts_exec.py",
     "return (flag or env) if env else EVIDENCE_ROOT", "return flag or env or EVIDENCE_ROOT", "evidence_root_flag_is_ignored"),
    ("resolver: receipt-build split check removed", "resolver_verdicts.sql",
     "count(DISTINCT receipt_build_id) <> 1\n           OR ", "", "different_receipt_builds"),
    ("resolver: spec-digest split check removed", "resolver_verdicts.sql",
     "\n           OR count(DISTINCT output_digest_spec_sha256) <> 1", "", "different_spec_digests"),
    ("gate: counts no longer block", "prerun_gate.py",
     'if vals["deploy_runs_not_completed"] != 0 or vals["build_runs_in_flight"] != 0:', "if False:",
     "deploy_in_flight_blocks or build_in_flight_blocks or both_in_flight"),
    ("gate: read failure no longer fails closed", "prerun_gate.py",
     "    if errs:\n        print(", "    if False:\n        print(", "read_failure_or_malformed"),
]


def run(workdir, expr):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(workdir / "tests"), "-k", expr],
                          capture_output=True, text=True, cwd=workdir)


def main():
    bad = 0
    for name, fname, old, new, expr in MUTATIONS:
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
                                                      "OK" if ok else "NOT PROVEN"))
            for l in tail:
                print("      ", l)
            bad += 0 if ok else 1
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
