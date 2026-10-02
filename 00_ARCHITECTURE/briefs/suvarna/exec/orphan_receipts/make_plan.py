#!/usr/bin/env python3
"""Offline (no database, no credential): render plan.txt for one asset/chart, print the executor sha256 and the plan hash.

  python3 make_plan.py [--asset ga_positions] [--chart 482012f1-710e-4a25-994a-93821f5871aa] [--write]

Defaults are the S-L1 plan (ga_positions on the canonical chart). Re-run with --write after ANY edit to
orphan_receipts_exec.py or resolver_verdicts.sql: the plan embeds the executor sha256, so the hash changes with the code.
"""
import argparse
import pathlib

import orphan_receipts_exec as ex

HERE = pathlib.Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--asset", default="ga_positions")
    p.add_argument("--chart", default="482012f1-710e-4a25-994a-93821f5871aa")
    p.add_argument("--write", action="store_true", help="write plan.txt (only meaningful for the default asset/chart)")
    a = p.parse_args()
    sha = ex.exec_sha()
    text = ex.render_plan(a.asset, a.chart, sha)
    if a.write:
        (HERE / "plan.txt").write_text(text + "\n")
    print("asset:", a.asset, "chart:", a.chart)
    print("executor sha256:", sha)
    print("resolver_verdicts.sql sha256:", ex.sha_file(ex.VERDICT_SQL_FILE))
    print("plan hash:", ex.plan_hash(a.asset, a.chart, sha))
    print("DIFF:", ex.expected_diff(a.asset, a.chart))


if __name__ == "__main__":
    main()
