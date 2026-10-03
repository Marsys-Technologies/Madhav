#!/usr/bin/env python3
"""Mutation proof: neuter ONE rule at a time in a COPY of this folder and show that the tests go RED.

  python3 tests/mutation_proof.py [name-substring ...]      (no argument: every mutation)

For each mutation: copy the folder (and a `platform` symlink, the tests read migration 1035 and the writers from it) into a temp tree with the same depth,
apply ONE exact-string replacement to ONE file of the copy (asserting the old text occurs exactly once), optionally RECOMPUTE the bound md5/sha256/diff
constants (kind "recompute": so that a behavioural mutation of a hunk is not trivially caught by the EXPECTED_DIFF binding but must be caught by the
behavioural tests), run the named pytest selection there and require a non-zero exit. The un-mutated copy must be green first (the deliberate TBD-pin
test and the plan.txt re-render test are deselected). The repository files are never modified. Needs a local PostgreSQL (PG_BIN) like the tests."""
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
DESELECT = "not test_plan_txt_is_the_rendering_with_the_current_pins"      # it compares plan.txt with the (mutated) executor sha: a spurious red
PY311 = "tests/test_py311_and_interpreter.py"
IB = "tests/test_interpreter_binding.py"
FAST = "tests/test_plan_and_wiring.py tests/test_plan_docs.py tests/test_combined_exec.py tests/test_capture_shapes.py tests/test_dasha_partition_patches.py " + PY311 + " " + IB

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
WIRING = "tests/test_plan_and_wiring.py tests/test_plan_docs.py"
BCT = "tests/test_dasha_partition_patches.py"
BC = "d6_dasha_partition_patches.py"
VT = "tests/test_vichara_item5.py"
PQ = "tests/test_prereq_1255.py"
LM = "tests/test_limits.py"
DE = "tests/test_dasha_e2e.py"

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
    ("trigger re-attestation skipped", EX,
     "        cur.execute(f\"UPDATE {TRG_ATT} a SET definition_digest = encode(public.digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex') \"\n"
     "                    \"FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid \"\n"
     "                    \"WHERE a.table_name=%s AND a.trigger_name=%s AND c.relname=a.table_name AND t.tgname=a.trigger_name\", (ts.table, TRIGGER))\n",
     "        cur.execute(\"SELECT 1\")\n", None, COMBINED, None),
    ("immutability trigger not re-enabled after the function attestation", EX,
     '        cur.execute(f"ALTER TABLE {FN_ATT} ENABLE TRIGGER {FN_ATT_IMMUTABLE}")\n    for ts in leg.triggers:\n        if ts.change.swap_index:\n            cur.execute(f"CREATE UNIQUE INDEX',
     '    for ts in leg.triggers:\n        if ts.change.swap_index:\n            cur.execute(f"CREATE UNIQUE INDEX', None, COMBINED, None),
    # ---- EXPECTED_DIFF / byte-for-byte binding
    ("EXPECTED_DIFF neutered in the database (body and diff checks)", EX,
     "new_def == st.to_def and hashlib.md5(new_def.encode()).hexdigest() == st.to_md5,", "True,", None, COMBINED, "extra_byte"),
    ("EXPECTED_DIFF binding neutered before the database", EX, "        if got != want:\n", "        if False:\n", None, COMBINED + " " + WIRING, "tampered_hunk or ONLY_by or expected_diff"),
    ("live body byte-for-byte precondition neutered", EX, "md5 == st.from_md5 and definition == st.from_def,", "True,", None, COMBINED, "md5_differs"),
    ("only-the-patched-functions-changed identity check neutered (counts still satisfied)", EX,
     '    out.append(("post_changed_functions_are_exactly_the_patched_ones",\n                changed == {st.patch.regproc.replace("public.", "") for st in leg.functions}, sorted(changed)))',
     '    out.append(("post_changed_functions_are_exactly_the_patched_ones", True, sorted(changed)))', None, COMBINED, "change_accounting"),
    ("function change COUNT check neutered (identity check still there)", EX,
     '        out.append((f"post_exactly_{want}_{key}_entries_changed", len(removed) == want and len(added) == want, f"-{len(removed)} +{len(added)}"))',
     '        out.append((f"post_exactly_{want}_{key}_entries_changed", True, f"-{len(removed)} +{len(added)}"))', None, COMBINED, "change_accounting"),
    # ---- rollback
    ("rollback skipped (rollback leg re-applies the patched body)", EX,
     "    steps = tuple(FnStep(p, p.patched_def(), p.live_def(), p.patched_md5, p.live_md5, p.patched_sha256, p.live_sha256)",
     "    steps = tuple(FnStep(p, p.patched_def(), p.patched_def(), p.patched_md5, p.patched_md5, p.patched_sha256, p.patched_sha256)", None, COMBINED + " " + SHAPES, "rollback"),
    ("rollback does not restore the six-column index or the old trigger arguments", EX, "TrgStep(c, c.to_args, c.from_args, c.to_digest, c.from_digest)",
     "TrgStep(c, c.to_args, c.to_args, c.to_digest, c.from_digest)", None, COMBINED, "rollback"),
    ("rollback widened-row collision guard neutered", EX, "ck.chk(\"pre_no_widened_rows_collide_on_the_six_column_key\", dup == 0,", "ck.chk(\"pre_no_widened_rows_collide_on_the_six_column_key\", True,", None, COMBINED, "widened_rows"),
    # ---- comments (the SS condition)
    ("contract comments not applied", EX, "    for stmt in leg.comment_stmts:\n        cur.execute(stmt)\n", "", None, COMBINED + " " + SHAPES, None),
    ("comment diff check neutered, table comment text no longer states the precedence", EX, "precedence num, then text, then jsonb \"\n            \"(value_num", "order \"\n            \"(value_num", None, COMBINED, "verify_sql or apply_commits"),
    # ---- preconditions and gate
    ("function-missing precondition neutered", EX, 'present = ck.chk(f"pre_{tag}_present", row is not None,', 'present = ck.chk(f"pre_{tag}_present", True,', None, COMBINED, "function_is_missing"),
    ("function attestation row precondition neutered", EX, 'ck.chk(f"pre_{tag}_attestation_row", n == 1 and dg == st.from_sha,', 'ck.chk(f"pre_{tag}_attestation_row", True,', None, COMBINED, "attestation_row_is_missing"),
    ("owner precondition neutered", EX, 'ck.chk(f"pre_{tag}_owner_secdef_config_acl", (owner, secdef, config, acl) == (p.owner, p.secdef, p.config, p.acl),',
     'ck.chk(f"pre_{tag}_owner_secdef_config_acl", True,', None, COMBINED, "not_owned"),
    ("post-apply deploy-gate check neutered", EX, 'ck.chk("post_deploy_gate_green", not fa2.gate_red(gate_after),', 'ck.chk("post_deploy_gate_green", True,', None, COMBINED, "gate_going_red"),
    ("evidence digest comparison neutered", EX, 'ck.chk("evidence_digest_matches_expected", expect_evidence == digest,', 'ck.chk("evidence_digest_matches_expected", True,', None, COMBINED, "wrong_digest"),
    ("writer-first precondition neutered", EX, 'ck.chk("pre_writer_first", not problems,', 'ck.chk("pre_writer_first", True,', None, COMBINED, "writer_first"),
    ("--expect-plan comparison neutered", EX, "        if args.expect_plan != phash:\n", "        if False:\n", None, WIRING, "wrong_plan_hash"),
    ("launch check removed from main()", EX, "    gate_fp = launch_gate()                  # FIRST: before the arguments are even parsed\n", "    gate_fp = None\n", None, WIRING, "launch_gate_FIRST"),
    ("TBD pins no longer refused by launch_gate", EX, "    if any(v == GATE_TBD for v in GATE_PINS.values()):\n", "    if False:\n", None, WIRING, "tbd"),
    ("plan hash no longer binds the gate pins", EX, '{"gate_sha256": pins["prerun_gate.py"], "run_gated_sha256": pins["run_gated.sh"]})', '{"gate_sha256": "0" * 64, "run_gated_sha256": "0" * 64})', None, WIRING, "plan_hash_binds"),
    ("outcome after commit recorded as failed (committed flag not set)", EX, "                    o.mark_committed(digest)                                  # IMMEDIATELY after the commit\n", "                    pass\n", None, COMBINED, "interruption"),
    ("test evidence-root variable honoured outside pytest", EX, "    if PYTEST_ENV not in environ:\n        sys.stderr.write(f\"REFUSED: {TEST_EVIDENCE_ENV}", "    if False:\n        sys.stderr.write(f\"REFUSED: {TEST_EVIDENCE_ENV}", None, WIRING, "stray_test_variables"),
    ("under_test launch marker accepted outside pytest", EX, '    if gate_fp.get("under_test") and PYTEST_ENV not in environ:\n', "    if False:\n", None, WIRING, "under_test"),
    ("commit_state_unknown no longer recorded when commit() raises", EX, "                        o.mark_commit_unknown(digest, type(exc).__name__)\n                        raise\n",
     "                        raise\n", None, COMBINED, "commit_call"),
    ("second function: its re-attestation skipped (data-driven loop)", EX, "        cur.execute(fn_att_update_sql(st.patch.signature))\n", '        cur.execute("SELECT 1")\n', None, "tests/test_two_function_machinery.py", None),
    ("second function: its pre-state body check neutered", EX, "md5 == st.from_md5 and definition == st.from_def,", "True,", None, "tests/test_two_function_machinery.py", "byte_for_byte"),
    # ---- patches B and C (SS N-85): each neutered patch must be caught
    ("patch B: declaration neutered (recomputed constants)", BC, "  v_systems TEXT[];\\nBEGIN\\n'),", "  v_systems_x TEXT[];\\nBEGIN\\n'),", "recompute", BCT, None),
    ("patch B: one scope site left on the old single-system predicate (recomputed constants)", BC,
     "    AND (p_partition_key = '__concurrency_post_pass__' OR (\\n      d.system_id = ANY(v_systems) AND d.ayanamsha_id = v_ayanamsha_id\\n    ))\\n\"),",
     "    AND (p_partition_key = '__concurrency_post_pass__' OR (\\n      d.system_id = ANY(ARRAY[v_system_id]) AND d.ayanamsha_id = v_ayanamsha_id\\n    ))\\n\"),", "recompute", BCT, "semantics or reproduce or old_text"),
    ("patch B: vimshottari_kp no longer included (recomputed constants)", BC, "ARRAY['vimshottari','vimshottari_kp']::TEXT[]", "ARRAY['vimshottari']::TEXT[]", "recompute", BCT, "semantics or reproduce"),
    ("patch B: scope site neutered, constants NOT recomputed (EXPECTED_DIFF binding)", BC,
     "    AND (p_partition_key = '__concurrency_post_pass__' OR (\\n      d.system_id = ANY(v_systems) AND d.ayanamsha_id = v_ayanamsha_id\\n    ))\\n\"),",
     "    AND (p_partition_key = '__concurrency_post_pass__' OR (\\n      d.system_id = ANY(ARRAY[v_system_id]) AND d.ayanamsha_id = v_ayanamsha_id\\n    ))\\n\"),", None, BCT, "base_is_production or target_is_bound"),
    ("patch C: post-pass block neutered (recomputed constants)", BC, "IF p_asset_id = 'ga_dashas' AND p_partition_key", "IF p_asset_id = 'ga_dashas_x' AND p_partition_key", "recompute", BCT, "semantics or reproduce"),
    ("patch C: neutered, constants NOT recomputed (EXPECTED_DIFF binding)", BC, "IF p_asset_id = 'ga_dashas' AND p_partition_key", "IF p_asset_id = 'ga_dashas_x' AND p_partition_key", None, BCT, "base_is_production or target_is_bound"),
    ("patch B dropped from the plan (FUNCTION_PATCHES)", EX, "FUNCTION_PATCHES = (CAPTURE_PATCH, DASHA_CAPTURE_PATCH, COMPLETE_PATCH)", "FUNCTION_PATCHES = (CAPTURE_PATCH, COMPLETE_PATCH)", None, BCT + " " + WIRING, "in_the_plan or item_5 or expected_diff"),
    ("patch B: bound base md5 no longer the production md5 (base-md5 mismatch)", EX, 'live_md5="eee8d9d4f5fbbbbbd03a9abda7c62385"', 'live_md5="00000000000000000000000000000000"', None, BCT, "base_is_production"),
    ("patch C: its bound target md5 no longer what the hunks produce", EX, 'patched_md5="31d005e8ecacf40547f0537e24d717d5"', 'patched_md5="11111111111111111111111111111111"', None, BCT, "base_is_production or target_is_bound"),
    ("item 5 slot filled (a chart_vichara hunk smuggled in)", BC, "PATCH_C_HUNKS = (", "PATCH_C_HUNKS = (('X5_chart_vichara', 'BEGIN\\n', 'BEGIN\\n  -- chart_vichara\\n'), ", None, WIRING, "item_5"),
    # ---- item 5 (K1): the chart_vichara trigger leg, data-driven
    ("item 5: the chart_vichara argument list changed (target digest no longer what the live trigger text hashes to)", EX, 'VICHARA_NEW = VICHARA_OLD + ("constituent_fact_ids",)', 'VICHARA_NEW = VICHARA_OLD + ("constituent_facts_array",)', None, VT, None),
    ("item 5: the chart_vichara entry dropped from TRIGGER_CHANGES", EX, "TRIGGER_CHANGES = (FA2_TRIGGER, VICHARA_TRIGGER)", "TRIGGER_CHANGES = (FA2_TRIGGER,)", None, VT + " " + WIRING, "item_5 or vichara or expected_diff"),
    ("item 5: the chart_vichara trigger attestation row is not re-attested", EX, "    for ts in leg.triggers:                          # re-attest ONLY the rows of the changed tables\n",
     "    for ts in leg.triggers:                          # re-attest ONLY the rows of the changed tables\n        if ts.table == 'chart_vichara':\n            continue\n", None, VT, "post_apply or dry_run"),
    ("item 5: the base-trigger-text precondition neutered", EX, 'ck.chk(f"pre_trigger_shape_{ts.table}", bool(row) and trigger_args(row[0]) == ts.from_args,', 'ck.chk(f"pre_trigger_shape_{ts.table}", True,', None, VT, "bound_base"),
    ("item 5: the chart_vichara identity probe neutered", EX, '''                and probe["vichara_identities_live_args"] == probe["vichara_fixture_rows"]''', "                and True", None, VT, "collapses"),
    ("item 5: changed-attestation identity check neutered (counts alone would still say N)", EX, '''        out.append((name, tables == planned, sorted(tables)))''', "        out.append((name, True, sorted(tables)))", None, COMBINED, "wrong_table or extra_tables"),
    # ---- step 0 prerequisite (migration 1255), limits independent of the sha pin, B and C against a database
    ("step 0: owner brahma_yoga_catalog grant precondition neutered", EX, 'ck.chk("pre_prereq_1255_owner_can_read_brahma_yoga_catalog", not owner_missing,', 'ck.chk("pre_prereq_1255_owner_can_read_brahma_yoga_catalog", True,', None, PQ, "owner_grant"),
    ("step 0: builder seven-table precondition neutered", EX, 'ck.chk("pre_prereq_1255_builder_can_read_the_seven_reference_tables", not builder_missing,', 'ck.chk("pre_prereq_1255_builder_can_read_the_seven_reference_tables", True,', None, PQ, "seven_tables or missing_reference"),
    ("step 0: a missing reference table no longer counts as missing", EX, 'IS NOT NULL AND has_table_privilege(%s, to_regclass(%s), \'SELECT\')', 'IS NULL OR has_table_privilege(%s, to_regclass(%s), \'SELECT\')', None, PQ, "missing_reference"),
    ("step 0: the prerequisite dropped from the plan text", EX, ' + ", ".join(PREREQ_1255_BUILDER_TABLES) + ") else REFUSE naming 1255;', ' + ") else REFUSE naming 1255;', None, PQ + " " + WIRING, "1255 or verify_sql or plan_text or prerequisite"),
    ("limits: the window statement cap raised (no sha pin needed)", EX, "WINDOW_STATEMENT_BOUND = 100 ", "WINDOW_STATEMENT_BOUND = 1000 ", None, LM, "documented or really_sets"),
    ("limits: lock_timeout 5s raised to 500s (no sha pin needed)", EX, 'LOCK_TIMEOUT = "5s" ', 'LOCK_TIMEOUT = "500s" ', None, LM, "documented or really_sets"),
    ("limits: statement_timeout 120s raised (no sha pin needed)", EX, 'STATEMENT_TIMEOUT = "120s"\n', 'STATEMENT_TIMEOUT = "1200s"\n', None, LM, "documented or really_sets"),
    ("e2e: patch B no longer includes the vimshottari_kp rows (recomputed constants, database proof)", BC, "ARRAY['vimshottari','vimshottari_kp']::TEXT[]", "ARRAY['vimshottari']::TEXT[]", "recompute", DE, "B_after"),
    ("e2e: patch C post-pass block neutered (recomputed constants, database proof)", BC, "IF p_asset_id = 'ga_dashas' AND p_partition_key", "IF p_asset_id = 'ga_dashas_x' AND p_partition_key", "recompute", DE, "C_after"),
    ("python 3.11 floor: the nested same-quote f-string re-introduced (render_plan ITEM_LABELS line, line 470)", EX, "{ITEM_LABELS.get(p.signature, 'ITEM ? (add a label to ITEM_LABELS)')}", '{ITEM_LABELS.get(p.signature, "ITEM ? (add a label to ITEM_LABELS)")}', None, PY311, None),
    ("interpreter record: outcome.json no longer gets python_executable / python_version", EX, "                add_interpreter_to_outcome(self.path)\n", "                pass\n", None, PY311, "interpreter"),
    ("interpreter binding: the runtime removed from the evidence digest", EX, '        "runtime": runtime_record(), "before": before,', '        "before": before,', None, IB, "digest"),
    ("interpreter binding: the early precheck is no longer called", EX, "            interpreter_precheck(o, evidence_root, args.expect_evidence, lines)\n", "            pass\n", None, IB, "refuses_by_itself or rollback_under"),
    ("interpreter binding: a differing interpreter/driver field is no longer refused", EX, "        differs = [k for k in RUNTIME_KEYS if body[k] != now[k]]\n", "        differs = []\n", None, IB, "different_runtime or rollback_under"),
    ("interpreter binding: a missing field (old format) is no longer 'cannot compare'", EX, '        missing = [k for k in RUNTIME_KEYS if body.get(k) in (None, "")]\n', "        missing = []\n", None, IB, "cannot_be_compared or old_format"),
    ("interpreter binding: the refusal exit code is no longer the distinct 96", EX, "    raise SystemExit(EXIT_INTERPRETER)\n", "    raise SystemExit(1)\n", None, IB, "refuses_by_itself"),
    ("interpreter binding: psycopg / libpq versions dropped from the runtime record", EX, '"psycopg_version": psycopg.__version__,\n            "libpq_version": psycopg.pq.version()}', '"psycopg_version": "x",\n            "libpq_version": 0}', None, PY311 + " " + IB, "interpreter or runtime"),
    ("interpreter record failure: the message is again the misleading 'could not be written'", EX, "        if o.interpreter_record_error:\n", "        if False:\n", None, PY311, "failed_interpreter_record"),
    ("verify SQL: the plan text no longer names the verification files", EX, '        + "; ".join(f"{n} sha256 {sha_file(HERE / n)}" for n in VERIFY_FILES),', '        + "",', None, WIRING, "verify_files"),
]


def sh(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def build_tree(tmp: pathlib.Path) -> pathlib.Path:
    dest = tmp / REL
    shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    for sibling in SRC.parent.glob("*.md"):                  # the contract document sits one level up (exec/); the doc tests read it
        shutil.copy(sibling, dest.parent / sibling.name)
    (tmp / "platform").symlink_to(REPO / "platform")
    return dest


RECOMPUTE = r'''
import hashlib, importlib.util, pathlib, re, sys
d = pathlib.Path(sys.argv[1])
def load(n, f):
    s = importlib.util.spec_from_file_location(n, d / f); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
m = load("mut_exec", "d6_dataplane_capture_fa2_exec.py")
src = (d / "d6_dataplane_capture_fa2_exec.py").read_text()
for p in m.FUNCTION_PATCHES:                                  # every patched function: recompute ITS bound constants (a window after its signature)
    live = p.live_def()
    new = m.pa.apply_hunks(live, p.hunks)
    vals = {"patched_md5": hashlib.md5(new.encode()).hexdigest(), "patched_sha256": hashlib.sha256(new.encode()).hexdigest(),
            "diff_sha256": m.pa.diff_digest(live, new)}
    marker = 'signature="%s"' % p.signature if ('signature="%s"' % p.signature) in src else "signature=CAPTURE_FN_SIG"
    i = src.index(marker)
    j = src.index("diff_hunks=", i) + 40
    win = src[i:j]
    for k, v in vals.items():
        win, n = re.subn(r'(%s=")[0-9a-f]{32,64}(")' % k, r"\g<1>%s\g<2>" % v, win); assert n == 1, (p.signature, k)
    win, n = re.subn(r"diff_hunks=\d+", "diff_hunks=%d" % len(m.pa.unified_hunks(live, new)), win); assert n == 1
    src = src[:i] + win + src[j:]
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
            by = next((l.strip()[:150] for l in r.stdout.splitlines() if l.startswith(("FAILED", "ERROR"))), "")
            print(("RED   " if red else "GREEN (MUTATION SURVIVED!) ") + name + (f"   [{tail.strip()}] by {by}" if red else ""))
            bad += 0 if red else 1
            shutil.rmtree(tmp / f"m{i}", ignore_errors=True)
        print(f"{len(sel) - bad}/{len(sel)} mutations proven (each RED)")
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
