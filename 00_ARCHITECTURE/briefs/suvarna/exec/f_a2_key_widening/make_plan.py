#!/usr/bin/env python3
"""Offline (no database, no credential, no launch marker): print the executor sha, the bound shas and the PROVISIONAL plan hash, and with
--write re-render plan.txt. `--gate-dir <dir>` selects the folder holding executor_standards.py (default exec/gate_v2; before PR #2938 is
merged use tests/gate_fixture, whose files are byte-identical to gate_v2 rev3 (PR #2938 head 7f0db55c3)). The pins in GATE_PINS are TBD, so the hash is PROVISIONAL."""
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
    print("gate pins           :", m.GATE_PINS, "(TBD = provisional)" if any(v == m.GATE_TBD for v in m.GATE_PINS.values()) else "")
    print("plan hash unbound   :", m.plan_hash_unbound())
    print("PLAN HASH           :", m.plan_hash(), "(PROVISIONAL while the gate pins are TBD)" if any(v == m.GATE_TBD for v in m.GATE_PINS.values()) else "")
    # what the hash WOULD be if Strategic Suvarna binds the revision-3 pins by replacing the one GATE_PINS line with the literal values (binding edits the
    # executor source, so the executor sha changes too): computed on the source text, nothing is written
    src = (HERE / "d6_dataplane_capture_fa2_exec.py").read_text()
    old = 'GATE_PINS = {"prerun_gate.py": GATE_TBD, "run_gated.sh": GATE_TBD, "executor_standards.py": GATE_TBD}'
    if src.count(old) == 1:
        new = "GATE_PINS = " + repr(dict(m.GATE_REV3_PROPOSED))
        import hashlib
        sim_sha = hashlib.sha256(src.replace(old, new).encode()).hexdigest()
        print("IF BOUND (rev3)     : executor sha256", sim_sha, "| plan hash", m.plan_hash(sim_sha, dict(m.GATE_REV3_PROPOSED)))
        print("  binding edit      : replace the line  " + old + "\n                      with        " + new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
