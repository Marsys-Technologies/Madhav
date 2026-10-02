"""Patch B (capture_l1_data_plane_dasha_partition) and patch C (complete_l1_data_plane_partition), approved as DESIGN by SS decision N-85 to travel in the
same single D6 plan as option A and F-A2: data in d6_dasha_partition_patches.py, bound in FUNCTION_PATCHES. No database for the text tests; the database
tests run on the disposable replay of migration 1035 (the bound live bodies are production's bytes, asserted by test_replay_is_production_faithful)."""
from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import sys

import pytest

import conftest as cf
import live_manifest as lm
from conftest import EXEC_DIR

B_SIG = "capture_l1_data_plane_dasha_partition(uuid,text,text,integer)"
C_SIG = "complete_l1_data_plane_partition(uuid,text,text,text,integer)"
REHEARSAL = {B_SIG: "rehearsal_inputs/capture_l1_data_plane_dasha_partition.REHEARSAL_PATCHED_B.sql",
             C_SIG: "rehearsal_inputs/complete_l1_data_plane_partition.REHEARSAL_PATCHED_C.sql"}
SIGS = [B_SIG, C_SIG]


def patch(mod, sig):
    return {p.signature: p for p in mod.FUNCTION_PATCHES}[sig]


def helper():
    spec = importlib.util.spec_from_file_location("mfp_b", EXEC_DIR / "make_function_patch.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------------------ in the plan, as data
def test_b_and_c_are_in_the_plan_as_items_2_and_3_with_their_own_attestation_handling(mod):
    assert [p.signature for p in mod.FUNCTION_PATCHES] == ["l1_data_plane_capture_row()", B_SIG, C_SIG]
    assert mod.ITEM_LABELS[B_SIG].startswith("ITEM 2") and mod.ITEM_LABELS[C_SIG].startswith("ITEM 3")
    plan = mod.render_plan()
    for sig in SIGS:
        p = patch(mod, sig)
        assert f"CREATE OR REPLACE FUNCTION public.{sig}" in plan and p.live_md5 in plan and p.patched_md5 in plan and p.diff_sha256 in plan
        assert f"a.function_signature='{sig}'" in plan                                         # its own function-attestation re-attestation row
    assert plan.count("ALTER TABLE public.l1_data_plane_function_attestations DISABLE TRIGGER") == 3     # one re-attestation per patched function
    assert len(mod.EXPECTED_DIFF["functions"]) == 3 and "ITEM 5" in plan and "RESERVED" not in plan


@pytest.mark.parametrize("sig", SIGS)
def test_the_base_is_production_bytes_and_the_target_is_bound(mod, sig):
    p = patch(mod, sig)
    live = p.live_def()                                          # raises ExpectedDiffError unless md5, length and sha256 equal the bound live values
    md5, ln, owner, secdef, config, acl = lm.LIVE_L1_MANIFEST[sig]
    assert (hashlib.md5(live.encode()).hexdigest(), len(live)) == (md5, ln) == (p.live_md5, p.live_len)
    assert (p.owner, p.secdef, p.config, p.acl) == (owner, secdef, config, acl)
    new = p.patched_def()                                        # raises unless the patched md5, sha256, diff digest and hunk count equal the bound ones
    assert hashlib.md5(new.encode()).hexdigest() == p.patched_md5 != p.live_md5


@pytest.mark.parametrize("sig", SIGS)
def test_the_hunks_reproduce_the_rehearsal_workers_patched_text_byte_for_byte(mod, sig):
    p = patch(mod, sig)
    rehearsed = helper().normalise_patched((EXEC_DIR / REHEARSAL[sig]).read_text(), p.live_def())
    assert p.patched_def() == rehearsed


# ------------------------------------------------------------------------------------ old text false / new text true, mismatching shapes refused
@pytest.mark.parametrize("sig", SIGS)
def test_each_hunk_old_text_is_true_once_in_the_live_body_and_false_in_the_patched_one_and_new_text_the_reverse(mod, sig):
    p = patch(mod, sig)
    live, new = p.live_def(), p.patched_def()
    for name, old, repl in p.hunks:
        assert live.count(old) == 1 and repl not in live, name
        assert new.count(repl) == 1, name
        if not repl.startswith(old):                              # a pure insertion keeps its anchor; every replacement removes it
            assert old not in new, name


def test_the_semantics_of_b_and_c_in_the_bodies(mod):
    live_b, new_b = patch(mod, B_SIG).live_def(), patch(mod, B_SIG).patched_def()
    assert live_b.count("system_id = v_system_id") == 4 and "v_systems" not in live_b
    assert new_b.count("system_id = v_system_id") == 0 and new_b.count("ANY(v_systems)") == 4 and new_b.count("v_systems TEXT[];") == 1
    assert "WHEN v_system_id = 'vimshottari' THEN ARRAY['vimshottari','vimshottari_kp']::TEXT[] ELSE ARRAY[v_system_id]::TEXT[]" in new_b
    live_c, new_c = patch(mod, C_SIG).live_def(), patch(mod, C_SIG).patched_def()
    block = "IF p_asset_id = 'ga_dashas' AND p_partition_key = '__concurrency_post_pass__' THEN"
    assert block not in live_c and new_c.count(block) == 1
    assert "l1_data_plane_dasha_snapshots" in new_c[new_c.index(block):new_c.index(block) + 800]


@pytest.mark.parametrize("sig", SIGS)
def test_a_mismatching_shape_is_refused_not_patched(mod, sig):
    p = patch(mod, sig)
    live, new = p.live_def(), p.patched_def()
    name, old, repl = p.hunks[0]
    with pytest.raises(ValueError, match="occurs 0 times"):                         # an anchor that no longer matches
        mod.pa.apply_hunks(live.replace(old, old[:3] + "~" + old[3:], 1), p.hunks)
    with pytest.raises(ValueError):                                                 # already patched: the old text is gone / the new text is present
        mod.pa.apply_hunks(new, p.hunks)
    with pytest.raises(ValueError, match="occurs 2 times"):                         # an anchor that became ambiguous
        mod.pa.apply_hunks(live + old, p.hunks)
    bad = dataclasses.replace(p, live_md5="0" * 32)
    with pytest.raises(mod.ExpectedDiffError):                                      # the shipped live file is not the bound base
        bad.live_def()


# ------------------------------------------------------------------------------------------------------------------ disposable database
@pytest.mark.parametrize("sig", SIGS)
def test_a_live_body_that_differs_from_the_bound_base_is_refused_and_nothing_changes(cluster, mod, db, tmp_path, sig):
    runner = cf.Runner(cluster, mod, db, tmp_path)
    body = cluster.su(db, f"SELECT pg_get_functiondef('public.{sig}'::regprocedure)")[0][0]
    cluster.su(db, body.replace("\n$function$\n", "\n  -- drift\n$function$\n"))              # one extra comment line: a different md5
    pre = runner.state()
    code, res = runner.run("apply")
    short = patch(mod, sig).short
    assert code != 0 and f"pre_{short}_body_is_the_bound_body" in res["failed_checks"]
    assert runner.state() == pre


def test_after_the_apply_each_function_md5_is_its_target_attested_and_unchanged_otherwise(cluster, mod, db, tmp_path):
    runner = cf.Runner(cluster, mod, db, tmp_path)
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    assert res["checks"]["post_exactly_3_function_entries_changed"] and res["checks"]["post_exactly_3_function_attestation_entries_changed"]
    for p in mod.FUNCTION_PATCHES:
        md5, owner, secdef, cfg, acl = cluster.su(db, "SELECT md5(pg_get_functiondef(oid)), pg_get_userbyid(proowner), prosecdef, COALESCE(proconfig::text,''), "
                                                      f"COALESCE(proacl::text,'') FROM pg_proc WHERE oid='public.{p.signature}'::regprocedure")[0]
        assert md5 == p.patched_md5 and (owner, secdef, cfg, acl) == (p.owner, p.secdef, p.config, p.acl), p.signature
        assert cluster.su(db, "SELECT definition_digest FROM public.l1_data_plane_function_attestations WHERE function_signature=%s", (p.signature,))[0][0] == p.patched_sha256
        assert res["checks"][f"post_{p.short}_body_is_exactly_the_bound_body"] and res["checks"][f"post_{p.short}_attestation_matches_live_function"]
    assert res["checks"]["post_deploy_gate_green"] and res["checks"]["post_gate_function_digest_equals_stored"]      # attestation drift 0


def test_the_dry_run_and_the_rollback_rehearsal_cover_b_and_c(cluster, mod, db, tmp_path):
    runner = cf.Runner(cluster, mod, db, tmp_path)

    def md5s():
        return dict(cluster.su(db, "SELECT oid::regprocedure::text, md5(pg_get_functiondef(oid)) FROM pg_proc WHERE oid IN "
                                   + "(" + ",".join(f"'public.{p.signature}'::regprocedure" for p in mod.FUNCTION_PATCHES) + ")"))
    pre, pre_md5 = runner.state(), md5s()
    assert pre_md5 == {p.signature: p.live_md5 for p in mod.FUNCTION_PATCHES}
    code, dry = runner.run("dry-run")
    assert code == 0 and dry["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and runner.state() == pre      # the dry run leaves everything identical
    code, res = runner.run("apply")
    assert code == 0 and md5s() == {p.signature: p.patched_md5 for p in mod.FUNCTION_PATCHES}
    code, rd = runner.run("rollback-dry-run")
    assert code == 0 and md5s() == {p.signature: p.patched_md5 for p in mod.FUNCTION_PATCHES}
    code, rb = runner.run("rollback")
    assert code == 0 and rb["status"] == "COMMITTED", rb["details"]
    assert md5s() == pre_md5 and runner.state() == pre                                                      # md5s AND attestation rows equal the pre-state
    got = dict(cluster.su(db, "SELECT function_signature, definition_digest FROM public.l1_data_plane_function_attestations WHERE function_signature = ANY(%s)", ([B_SIG, C_SIG],)))
    assert got == {B_SIG: patch(mod, B_SIG).live_sha256, C_SIG: patch(mod, C_SIG).live_sha256}                 # re-attested back to the pre-state digests
