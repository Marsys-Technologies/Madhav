#!/usr/bin/env python3
"""Offline (no database, no credential, no launch marker): print the executor sha, the bound shas and the plan hash (NOT FINAL before the freeze), and with
--write re-render plan.txt. `--gate-dir <dir>` selects the folder holding executor_standards.py (default exec/gate_v2; before PR #2938 is
merged use tests/gate_fixture, whose files are byte-identical to gate_v2 rev3 (PR #2938 head 7f0db55c3)). The pins in GATE_PINS are bound (N-86); the hash is still NOT FINAL until the freeze (the hunk set is not complete)."""
import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-dir")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.gate_dir:
        os.environ["PYTEST_CURRENT_TEST"] = "make_plan"      # the gate-dir override is a test/offline switch (refused for the real run)
        os.environ["DPFA2_TEST_GATE_DIR"] = str(pathlib.Path(a.gate_dir).resolve())
    import importlib.util
    spec = importlib.util.spec_from_file_location("d6_dataplane_capture_fa2_exec", HERE / "d6_dataplane_capture_fa2_exec.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    text = m.render_plan()
    if a.write:
        (HERE / "plan.txt").write_text(text + "\n")
    print("executor sha256     :", m.exec_sha())
    for p in m.FUNCTION_PATCHES:
        print(f"{p.signature}: live md5 {p.live_md5} -> patched md5 {p.patched_md5}; diff sha256 {p.diff_sha256} ({p.diff_hunks} hunks)")
    print("gate pins           :", m.GATE_PINS, "(UNBOUND: TBD)" if any(v == m.GATE_TBD for v in m.GATE_PINS.values()) else "(bound, N-86)")
    print("plan hash unbound   :", m.plan_hash_unbound())
    print("PLAN HASH           :", m.plan_hash(), "(NOT FINAL: the plan is not frozen)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
