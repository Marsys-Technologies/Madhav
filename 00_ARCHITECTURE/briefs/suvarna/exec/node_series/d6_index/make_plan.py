#!/usr/bin/env python3
"""Offline (no database, no credential): render plan.txt, print the executor and migration sha256 and the plan hash.

  python3 make_plan.py [--write]

Re-run with --write after ANY edit to node_index_exec.py or to platform/migrations/1227_*.sql: the plan embeds both digests,
so the hash changes with the code; update the hash quoted in PLAN.md (a test pins it) and get the new hash re-approved.
"""
import argparse
import pathlib

import node_index_exec as ex

HERE = pathlib.Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    sha, msha = ex.exec_sha(), ex.sha_file(ex.mig_path())
    text = ex.render_plan(sha, msha)
    if a.write:
        (HERE / "plan.txt").write_text(text + "\n")
    print("executor sha256:", sha)
    print("migration 1227 sha256:", msha)
    print("plan hash:", ex.plan_hash(sha, msha))
    print("DIFF:", ex.EXPECTED_DIFF)


if __name__ == "__main__":
    main()
