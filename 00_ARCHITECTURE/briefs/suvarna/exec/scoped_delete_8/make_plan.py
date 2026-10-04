#!/usr/bin/env python3
"""Offline (no database, no credential, no launch marker): print the executor sha, the SQL sha, the bound gate shas and the UNBOUND and BOUND plan hashes, and with
--write re-render plan.txt. The plan hash binds the SQL file (and with it the 8 ids, the chart and the fingerprint), the gate pins and the executor sha: any edit to
any of them changes it."""
import argparse
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    spec = importlib.util.spec_from_file_location("scoped_delete_8_exec", HERE / "scoped_delete_8_exec.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    text = m.render_plan()
    if a.write:
        (HERE / "plan.txt").write_text(text + "\n")
    print("executor sha256      :", m.exec_sha())
    print("sql sha256           :", m.forward_leg().sql_sha256)
    print("gate pins            :", m.GATE_PINS)
    print("UNBOUND PLAN HASH    :", m.plan_hash_unbound())
    print("BOUND PLAN HASH      :", m.plan_hash())
    return 0


if __name__ == "__main__":
    sys.exit(main())
