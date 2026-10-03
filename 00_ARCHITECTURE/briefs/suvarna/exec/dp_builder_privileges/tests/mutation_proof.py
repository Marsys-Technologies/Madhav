#!/usr/bin/env python3
"""Mutation proof for the 1272/1273 executor: each mutation edits a COPY of the folder and the test suite must FAIL on it; the unmutated copy must PASS.

Run (the mirror environment variables as in conftest.py; DPBP_SIDECAR_PATH adds the end-to-end proof):
    python3 mutation_proof.py            # prints one line per mutation: KILLED (suite failed, with the first failing tests) or SURVIVED (suite passed: a hole)
Exit 0 only if the baseline passes and every mutation is killed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
FOLDER = HERE.parent


def recompute_bind_constants(folder: pathlib.Path) -> None:
    """After a mutation of bind_patch.py, re-bind the executor's constants to the mutated body (so the mutation is a coherent, self-consistent plan and the
    TESTS, not the hunk-constant check, are what must catch it)."""
    spec = importlib.util.spec_from_file_location("bp_m", folder / "bind_patch.py")
    bp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bp)
    live = (folder / "live_defs" / "bind_l2_exact_inputs.LIVE.sql").read_text()
    new = bp.apply_hunks(live, bp.BIND_HUNKS)
    src = (folder / "dp_builder_privileges_exec.py").read_text()
    src = re.sub(r'patched_md5="[0-9a-f]{32}"', f'patched_md5="{hashlib.md5(new.encode()).hexdigest()}"', src)
    src = re.sub(r'patched_sha256="[0-9a-f]{64}"', f'patched_sha256="{hashlib.sha256(new.encode()).hexdigest()}"', src)
    src = re.sub(r'diff_sha256="[0-9a-f]{64}", diff_hunks=\d+', f'diff_sha256="{bp.diff_digest(live, new)}", diff_hunks={len(bp.unified_hunks(live, new))}', src)
    (folder / "dp_builder_privileges_exec.py").write_text(src)


def edit(path: str, old: str, new: str, rebind: bool = False):
    def apply(folder: pathlib.Path):
        f = folder / path
        text = f.read_text()
        assert text.count(old) == 1, (path, old[:60], text.count(old))
        f.write_text(text.replace(old, new))
        if rebind:
            recompute_bind_constants(folder)
    return apply


EX = "dp_builder_privileges_exec.py"
MUTATIONS = {
    "M01 grant EXECUTE to PUBLIC instead of the builder": edit(EX, 'f"GRANT EXECUTE ON FUNCTION public.{sig} TO {BUILDER}"', 'f"GRANT EXECUTE ON FUNCTION public.{sig} TO PUBLIC"'),
    "M02 the bind shadows are granted to PUBLIC": edit("bind_patch.py", "TO data_plane_builder', v_table", "TO PUBLIC', v_table", rebind=True),
    "M03 the bind receipt is granted too (exclusion removed)": edit("bind_patch.py", "      AND c.relname <> 'l2_data_plane_bind_receipt'\\n", "", rebind=True),
    "M04 re-attestation skipped": edit(EX, "    cur.execute(fn_att_update_sql(p.signature))\n    att_rows = cur.rowcount", "    att_rows = 1"),
    "M05 transient membership never revoked": edit(EX, "    for r in transient:\n        cur.execute(f\"REVOKE {r} FROM CURRENT_USER\")", "    for r in []:\n        pass"),
    "M06 the build-in-flight precondition always passes": edit(EX, 'ck.chk("pre_no_build_in_flight", n == 0,', 'ck.chk("pre_no_build_in_flight", True,'),
    "M07 the evidence digest is not enforced": edit(EX, 'ck.chk("evidence_digest_matches_expected", expect_evidence == digest,', 'ck.chk("evidence_digest_matches_expected", True,'),
    "M08 the interpreter precheck is disabled": edit(EX, "        if args.mode in (\"apply\", \"rollback\"):\n            interpreter_precheck(o, evidence_root, args.expect_evidence, lines)", "        pass"),
    "M09 the gate pin check is skipped": edit(EX, 'if es.sha256_file(es.__file__) != GATE_PINS["executor_standards.py"]:', "if False:"),
    "M10 the asserting post-check is a no-op": edit(EX, "        cur.execute(\"DO $chk$ BEGIN IF \" + cond", "        cur.execute(\"SELECT 1 -- \" + cond"),
    "M11 the grants are issued as the wrong role": edit(EX, "    cur.execute(f\"SET LOCAL ROLE {IDENTITY_OWNER}\")", "    cur.execute(f\"SET LOCAL ROLE {OWNER_L2}\")"),
    "M12 the live-body precondition is dropped": edit(EX, 'ck.chk("pre_bind_body_is_the_bound_body", md5 == leg.from_md5 and definition == leg.from_def,', 'ck.chk("pre_bind_body_is_the_bound_body", True,'),
    "M13 the deploy gate result is ignored": edit(EX, 'ck.chk("post_deploy_gate_green", not gate_red(gate_after),', 'ck.chk("post_deploy_gate_green", True,'),
    "M14 the rollback does not revoke": edit(EX, 'f"REVOKE EXECUTE ON FUNCTION public.{sig} FROM {BUILDER}" if revoke else', 'f"SELECT 1" if revoke else'),
    "M15 the no-other-role check compares nothing": edit(EX, 'ck.chk("post_no_other_role_gains_execute_on_any_identity_function", got_gained == pairs and not got_lost,', 'ck.chk("post_no_other_role_gains_execute_on_any_identity_function", True,'),
}


def run_suite(folder: pathlib.Path, extra_env: dict) -> tuple[int, str]:
    env = dict(os.environ, DPBP_EXEC_PATH=str(folder / EX), **extra_env)
    r = subprocess.run([sys.executable, "-m", "pytest", str(folder / "tests"), "-q", "-p", "no:cacheprovider", "-x", "--no-header", "-rf"],
                       env=env, capture_output=True, text=True, cwd=str(folder))
    return r.returncode, r.stdout + r.stderr


REPO = FOLDER.parents[4]


def make_tree(dest: pathlib.Path) -> pathlib.Path:
    """A minimal repo tree at the same relative depth as the original: this folder, exec/gate_v2 and the gate's own table list the executor parses."""
    sub = dest / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec"
    sub.mkdir(parents=True)
    shutil.copytree(FOLDER, sub / FOLDER.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(FOLDER.parent / "gate_v2", sub / "gate_v2", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / "platform" / "scripts").mkdir(parents=True)
    shutil.copy(REPO / "platform" / "scripts" / "data-plane-ownership-preflight.ts", dest / "platform" / "scripts")
    return sub / FOLDER.name


def main() -> int:
    only = sys.argv[1:]
    ok = True
    with tempfile.TemporaryDirectory(prefix="dpbp_mut_") as td:
        td = pathlib.Path(td)
        base = make_tree(td / "base")
        rc, out = run_suite(base, {})
        print("BASELINE:", "pass" if rc == 0 else "FAIL", "|", out.strip().splitlines()[-1])
        if rc != 0:
            print(out[-3000:])
            return 1
        for name, mut in MUTATIONS.items():
            if only and not any(name.startswith(o) for o in only):
                continue
            work = make_tree(td / ("m_" + name.split()[0]))
            mut(work)
            rc, out = run_suite(work, {})
            failed = re.findall(r"^FAILED (\S+)", out, re.M)
            if rc == 0:
                ok = False
                print(f"SURVIVED  {name}")
            else:
                print(f"KILLED    {name}  <- {failed[0].split('::')[-1] if failed else out.strip().splitlines()[-1][:90]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
