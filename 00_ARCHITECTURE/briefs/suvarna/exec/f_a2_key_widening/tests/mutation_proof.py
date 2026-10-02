#!/usr/bin/env python3
"""Mutation proof: neuter ONE rule at a time in a COPY of this folder and show that the tests go RED.

  python3 tests/mutation_proof.py [name-substring ...]      (no argument: every mutation)

For each mutation: copy the folder (and a `platform` symlink, the tests read migration 1035 and the writers from it) into a temp tree with the same depth,
apply ONE exact-string replacement to ONE file of the copy (asserting the old text occurs exactly once), optionally RECOMPUTE the bound md5/sha256/diff
constants (kind "recompute": so that a behavioural mutation of a hunk is not trivially caught by the EXPECTED_DIFF binding but must be caught by the
behavioural tests), run the named pytest selection there and require a non-zero exit. The un-mutated copy must be green first (the deliberate TBD-pin
test is deselected). The repository files are never modified. Needs a local PostgreSQL (PG_BIN) like the tests."""
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent.parent
REPO = SRC.parents[4]
REL = SRC.relative_to(REPO)
DESELECT = "not test_gate_pins_are_bound"
FAST = "tests/test_plan_and_wiring.py tests/test_combined_exec.py tests/test_capture_shapes.py"

# (name, file, old, new, kind, test files, -k expression or None)
H3A_PRECEDENCE_OLD = """      IF v_value_num IS NOT NULL THEN
        v_typed_col := 'fact_value_num';
        v_companions := ARRAY[]::TEXT[]
          || CASE WHEN v_value_text IS NOT NULL THEN ARRAY['fact_value_text'] ELSE ARRAY[]::TEXT[] END
          || CASE WHEN v_value_jsonb IS NOT NULL THEN ARRAY['fact_value_jsonb'] ELSE ARRAY[]::TEXT[] END;
        v_value_text := NULL; v_value_jsonb := NULL;
      ELSE
        v_typed_col := 'fact_value_text';
        v_companions := ARRAY['fact_value_jsonb'];
        v_value_jsonb := NULL;
      END IF;"""
H3A_PRECEDENCE_TEXT_FIRST = """      IF v_value_text IS NOT NULL THEN
        v_typed_col := 'fact_value_text';
        v_companions := ARRAY[]::TEXT[]
          || CASE WHEN v_value_num IS NOT NULL THEN ARRAY['fact_value_num'] ELSE ARRAY[]::TEXT[] END
          || CASE WHEN v_value_jsonb IS NOT NULL THEN ARRAY['fact_value_jsonb'] ELSE ARRAY[]::TEXT[] END;
        v_value_num := NULL; v_value_jsonb := NULL;
      ELSE
        v_typed_col := 'fact_value_num';
        v_companions := ARRAY['fact_value_jsonb'];
        v_value_jsonb := NULL;
      END IF;"""
PA = "d6_capture_patch_a.py"
EX = "d6_dataplane_capture_fa2_exec.py"
SHAPES = "tests/test_capture_shapes.py"
COMBINED = "tests/test_combined_exec.py"
WIRING = "tests/test_plan_and_wiring.py"

MUTATIONS = [
    # ---- the hunks (behavioural: constants recomputed so only the BEHAVIOUR tests can catch them)
    ("H1 removed (declaration of v_typed_col / v_companions)", PA, '    ("H1_declare_v_typed_col_v_companions", H1_OLD, H1_NEW),\n', "", "recompute", SHAPES, None),
    ("H2 removed (all-null row floored/unavailable)", PA, '    ("H2_all_null_row_is_floored_or_unavailable", H2_OLD, H2_NEW),\n', "", "recompute", SHAPES, None),
    ("H3 removed (typed-value choice)", PA, '    ("H3a_typed_value_precedence_num_text_jsonb", H3A_OLD, H3A_NEW),\n', "", "recompute", SHAPES, None),
    ("H3b removed (companion marker site)", PA, '    ("H3b_grain_jsonb_records_kept_and_dropped_columns", H3B_OLD, H3B_NEW),\n', "", "recompute", SHAPES, None),
    ("precedence changed: text before num", PA, H3A_PRECEDENCE_OLD, H3A_PRECEDENCE_TEXT_FIRST, "recompute", SHAPES, None),
    ("companion marker dropped (typed_value_column key renamed)", PA, "ELSE jsonb_build_object('typed_value_column', v_typed_col,",
     "ELSE jsonb_build_object('typed_value_col_x', v_typed_col,", "recompute", SHAPES, None),
    ("companion list dropped (companion_value_columns key renamed)", PA, "'companion_value_columns', to_jsonb(v_companions)",
     "'companion_cols', to_jsonb(v_companions)", "recompute", SHAPES, None),
    # ---- the same hunk mutations are ALSO caught by the EXPECTED_DIFF binding when the constants are NOT recomputed
    ("H2 removed, constants NOT recomputed (EXPECTED_DIFF binding)", PA, '    ("H2_all_null_row_is_floored_or_unavailable", H2_OLD, H2_NEW),\n', "", None, WIRING + " " + COMBINED, None),
    # ---- re-attestation
    ("function re-attestation skipped", EX, "        cur.execute(fn_att_update_sql(st.patch.signature))\n", '        cur.execute("SELECT 1")\n', None, COMBINED + " " + SHAPES, None),
    ("trigger re-attestation skipped", EX, "    cur.execute(f\"UPDATE {TRG_ATT} a SET definition_digest = encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') \"\n"
     "                \"FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid \"\n"
     "                \"WHERE a.table_name=%s AND a.trigger_name=%s AND c.relname=a.table_name AND t.tgname=a.trigger_name\", (TABLE, TRIGGER))\n",
     "    cur.execute(\"SELECT 1\")\n", None, COMBINED, None),
    ("immutability trigger not re-enabled after the function attestation", EX,
     '        cur.execute(f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}")\n    cur.execute(f"CREATE UNIQUE INDEX', '    cur.execute(f"CREATE UNIQUE INDEX', None, COMBINED, None),
    # ---- EXPECTED_DIFF / byte-for-byte binding
    ("EXPECTED_DIFF neutered in the database (body and diff checks)", EX,
     "new_def == st.to_def and hashlib.md5(new_def.encode()).hexdigest() == st.to_md5,", "True,", None, COMBINED, "extra_byte"),
    ("EXPECTED_DIFF diff-digest check neutered in the database", EX,
     "pa.diff_digest(old_def, new_def) == p.diff_sha256 and len(pa.unified_hunks(old_def, new_def)) == p.diff_hunks,", "True,", None, COMBINED, "extra_byte"),
    ("EXPECTED_DIFF binding neutered before the database", EX, "        if got != want:\n", "        if False:\n", None, COMBINED + " " + WIRING, "tampered_hunk or ONLY_by or expected_diff"),
    ("live body byte-for-byte precondition neutered", EX, "md5 == st.from_md5 and definition == st.from_def,", "True,", None, COMBINED, "md5_differs"),
    ("only-the-patched-functions-changed check neutered", EX, 'changed == {st.patch.regproc.replace("public.", "") for st in leg.functions}, sorted(changed))',
     "True, sorted(changed))", None, COMBINED, "apply_commits"),
    # ---- rollback
    ("rollback skipped (rollback leg re-applies the patched body)", EX,
     "    steps = tuple(FnStep(p, p.patched_def(), p.live_def(), p.patched_md5, p.live_md5, p.patched_sha256, p.live_sha256)",
     "    steps = tuple(FnStep(p, p.patched_def(), p.patched_def(), p.patched_md5, p.patched_md5, p.patched_sha256, p.patched_sha256)", None, COMBINED + " " + SHAPES, "rollback"),
    ("rollback does not restore the six-column index", EX, "    return Leg(\"rollback\", steps, PATCHED_TRG_DIGEST, LIVE_TRG_DIGEST, NEW_COLS, OLD_COLS,",
     "    return Leg(\"rollback\", steps, PATCHED_TRG_DIGEST, LIVE_TRG_DIGEST, NEW_COLS, NEW_COLS,", None, COMBINED, "rollback"),
    ("rollback widened-row collision guard neutered", EX, "ck.chk(\"pre_no_widened_rows_collide_on_the_six_column_key\", dup == 0,", "ck.chk(\"pre_no_widened_rows_collide_on_the_six_column_key\", True,", None, COMBINED, "widened_rows"),
    # ---- comments (the SS condition)
    ("contract comments not applied", EX, "    for stmt in leg.comment_stmts:\n        cur.execute(stmt)\n", "", None, COMBINED + " " + SHAPES, None),
    ("comment diff check neutered, table comment text no longer states the precedence", EX, "precedence num, then text, then jsonb \"\n            \"(value_num", "order \"\n            \"(value_num", None, COMBINED, "verify_sql or apply_commits"),
    # ---- preconditions and gate
    ("function-missing precondition neutered", EX, 'present = ck.chk(f"pre_{tag}_present", row is not None,', 'present = ck.chk(f"pre_{tag}_present", True,', None, COMBINED, "function_is_missing"),
    ("function attestation row precondition neutered", EX, 'ck.chk(f"pre_{tag}_attestation_row", n == 1 and dg == st.from_sha,', 'ck.chk(f"pre_{tag}_attestation_row", True,', None, COMBINED, "attestation_row_is_missing"),
    ("owner precondition neutered", EX, 'ck.chk(f"pre_{tag}_owner_secdef_config_acl", (owner, secdef, config, acl) == (p.owner, p.secdef, p.config, p.acl),',
     'ck.chk(f"pre_{tag}_owner_secdef_config_acl", True,', None, COMBINED, "not_owned"),
    ("post-apply deploy-gate check neutered", EX, 'ck.chk("post_deploy_gate_green", not fa2.gate_red(gate_after),', 'ck.chk("post_deploy_gate_green", True,', None, COMBINED, "drift_is_zero or gate_is_green"),
    ("evidence digest comparison neutered", EX, 'ck.chk("evidence_digest_matches_expected", expect_evidence == digest,', 'ck.chk("evidence_digest_matches_expected", True,', None, COMBINED, "wrong_digest"),
    ("writer-first precondition neutered", EX, 'ck.chk("pre_writer_first", not problems,', 'ck.chk("pre_writer_first", True,', None, COMBINED, "writer_first"),
    ("--expect-plan comparison neutered", EX, "        if args.expect_plan != phash:\n", "        if False:\n", None, WIRING, "wrong_plan_hash"),
    ("launch check removed from main()", EX, "    gate_fp = launch_gate()                  # FIRST: before the arguments are even parsed\n", "    gate_fp = None\n", None, WIRING, "launch_gate_FIRST"),
    ("TBD pins no longer refused by launch_gate", EX, "    if any(v == GATE_TBD for v in GATE_PINS.values()):\n", "    if False:\n", None, WIRING, "tbd"),
    ("plan hash no longer binds the gate pins", EX, '{"gate_sha256": pins["prerun_gate.py"], "run_gated_sha256": pins["run_gated.sh"]})', '{"gate_sha256": "0" * 64, "run_gated_sha256": "0" * 64})', None, WIRING, "plan_hash_binds"),
    ("outcome after commit recorded as failed (committed flag not set)", EX, "                    o.mark_committed(digest)\n", "                    pass\n", None, COMBINED, "interruption"),
    ("test evidence-root variable honoured outside pytest", EX, "    if PYTEST_ENV not in environ:\n        sys.stderr.write(f\"REFUSED: {TEST_EVIDENCE_ENV}", "    if False:\n        sys.stderr.write(f\"REFUSED: {TEST_EVIDENCE_ENV}", None, WIRING, "stray_test_variables"),
]


def sh(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def build_tree(tmp: pathlib.Path) -> pathlib.Path:
    dest = tmp / REL
    shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    (tmp / "platform").symlink_to(REPO / "platform")
    return dest


RECOMPUTE = r'''
import hashlib, importlib.util, pathlib, re, sys
d = pathlib.Path(sys.argv[1])
def load(n, f):
    s = importlib.util.spec_from_file_location(n, d / f); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
m = load("mut_exec", "d6_dataplane_capture_fa2_exec.py")
p = m.CAPTURE_PATCH
live = p.live_def()
new = m.pa.apply_hunks(live, p.hunks)
vals = {"patched_md5": hashlib.md5(new.encode()).hexdigest(), "patched_sha256": hashlib.sha256(new.encode()).hexdigest(),
        "diff_sha256": m.pa.diff_digest(live, new)}
src = (d / "d6_dataplane_capture_fa2_exec.py").read_text()
for k, v in vals.items():
    src, n = re.subn(r'(%s=")[0-9a-f]{32,64}(")' % k, r"\g<1>%s\g<2>" % v, src); assert n == 1, k
src, n = re.subn(r"diff_hunks=\d+", "diff_hunks=%d" % len(m.pa.unified_hunks(live, new)), src); assert n == 1
(d / "d6_dataplane_capture_fa2_exec.py").write_text(src)
'''


def run_tests(tree: pathlib.Path, files: str, kexpr: str | None):
    k = DESELECT if not kexpr else f"({kexpr}) and {DESELECT}"
    cmd = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "-k", k] + files.split()
    return sh(cmd, tree)


def main(argv):
    filt = argv[1:]
    sel = [m for m in MUTATIONS if not filt or any(f in m[0] for f in filt)]
    with tempfile.TemporaryDirectory(prefix="dpfa2_mut_") as t:
        tmp = pathlib.Path(t)
        base = build_tree(tmp / "base")
        r = run_tests(base, FAST, None)
        if r.returncode != 0:
            print("BASELINE NOT GREEN:\n", r.stdout[-1500:], r.stderr[-500:])
            return 2
        print("baseline green:", r.stdout.strip().splitlines()[-1])
        bad = 0
        for i, (name, fname, old, new, kind, files, kexpr) in enumerate(sel):
            tree = build_tree(tmp / f"m{i}")
            f = tree / fname
            text = f.read_text()
            assert text.count(old) == 1, (name, text.count(old))
            f.write_text(text.replace(old, new))
            if kind == "recompute":
                rc = sh([sys.executable, "-c", RECOMPUTE, str(tree)], tree)
                assert rc.returncode == 0, rc.stderr[-600:]
            r = run_tests(tree, files, kexpr)
            red = r.returncode != 0
            tail = next((l for l in reversed(r.stdout.splitlines()) if "failed" in l or "error" in l), "")
            print(("RED   " if red else "GREEN (MUTATION SURVIVED!) ") + name + (f"   [{tail.strip()}]" if red else ""))
            bad += 0 if red else 1
            shutil.rmtree(tmp / f"m{i}", ignore_errors=True)
        print(f"{len(sel) - bad}/{len(sel)} mutations proven (each RED)")
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
