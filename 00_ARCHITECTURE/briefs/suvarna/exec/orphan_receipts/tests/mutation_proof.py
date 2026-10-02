#!/usr/bin/env python3
"""Mutation proof: neuter one refusal at a time in a COPY of the executor and show that its test goes RED.

  python3 tests/mutation_proof.py

For each mutation: copy the folder to a temp dir, apply ONE exact-string replacement to the copy's orphan_receipts_exec.py
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
    ("P5 no-build-in-flight neutered",
     'chk("P5_no_build_in_flight", len(inflight) == 0,', 'chk("P5_no_build_in_flight", True,',
     "build_in_flight"),
    ("P3 --min-build-after comparison neutered",
     "after_min = (min_after is None) or (", "after_min = True or (",
     "older_than_min_build_after or build_created_before_min"),
    ("V resolver verdict-diff check neutered",
     'chk("V_verdict_diff_is_exactly_the_asset", vdiff == {asset: list(EXPECTED_VERDICT)},',
     'chk("V_verdict_diff_is_exactly_the_asset", True,',
     "extra_asset or does_not_become_resolved"),
    ("A ACL-diff check neutered",
     'chk("A_acl_diff_empty", acl_diff == [],', 'chk("A_acl_diff_empty", True,',
     "drift_mid_flight"),
    ("P1 registry-declares-partition (orphan by definition) neutered",
     "chk(\"P1_registry_declares_partition\", declares,", "chk(\"P1_registry_declares_partition\", True,",
     "registry_declares_no_partition or whole_asset_key_itself"),
]


def run(workdir, expr):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(workdir / "tests"), "-k", expr],
                          capture_output=True, text=True, cwd=workdir)


def main():
    bad = 0
    for name, old, new, expr in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="mut_") as t:
            w = pathlib.Path(t) / "orphan_receipts"
            shutil.copytree(SRC, w, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "evidence"))
            green = run(w, expr)
            f = w / "orphan_receipts_exec.py"
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
