"""Patch B (capture_l1_data_plane_dasha_partition: partition scope includes the vimshottari_kp rows ga_dashas legitimately writes in the vimshottari
partition) and patch C (complete_l1_data_plane_partition: the post-pass partition counts the dasha rows it inserts) are CANDIDATES written by the
19-lane rehearsal. They are NOT in the shipped FUNCTION_PATCHES: they enter the plan only after Strategic Suvarna has reviewed each one. These tests
(i) assert exactly that, (ii) prove the candidates' live bases are production's bytes, that the hunk derivation reproduces them, and (iii) prove on a
disposable database that the executor, with B and C admitted IN THE TEST ONLY, applies, attests and rolls back all three functions."""
from __future__ import annotations

import hashlib
import importlib.util
import sys

import pytest

import conftest as cf
import live_manifest as lm
from conftest import EXEC_DIR

CAND = EXEC_DIR / "candidates"
B_SIG = "capture_l1_data_plane_dasha_partition(uuid,text,text,integer)"
C_SIG = "complete_l1_data_plane_partition(uuid,text,text,text,integer)"
FILES = {B_SIG: ("capture_l1_data_plane_dasha_partition", "PATCH_B_CANDIDATE", "B"), C_SIG: ("complete_l1_data_plane_partition", "PATCH_C_CANDIDATE", "C")}


def helper():
    spec = importlib.util.spec_from_file_location("mfp", EXEC_DIR / "make_function_patch.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["mfp"] = m
    spec.loader.exec_module(m)
    return m


def read(name):
    return (CAND / name).read_bytes().decode("utf-8")


def build_patch(mod, sig):
    base, cand, prefix = FILES[sig]
    live, patched = read(f"{base}.LIVE.sql"), helper().normalise_patched(read(f"{base}.{cand}.sql"), read(f"{base}.LIVE.sql"))
    hunks = tuple(helper().derive_hunks(live, patched, prefix))
    md5, ln, owner, secdef, config, acl = lm.LIVE_L1_MANIFEST[sig]
    new = mod.pa.apply_hunks(live, hunks)
    assert new == patched
    return mod.FunctionPatch(
        signature=sig, live_md5=md5, live_len=ln, live_sha256=hashlib.sha256(live.encode()).hexdigest(), owner=owner, secdef=secdef, config=config,
        acl=acl, hunks=hunks, patched_md5=hashlib.md5(new.encode()).hexdigest(), patched_sha256=hashlib.sha256(new.encode()).hexdigest(),
        diff_sha256=mod.pa.diff_digest(live, new), diff_hunks=len(mod.pa.unified_hunks(live, new)))


def test_candidates_are_not_in_the_plan(mod):
    assert [p.signature for p in mod.FUNCTION_PATCHES] == ["l1_data_plane_capture_row()"]
    plan = mod.render_plan()
    assert "capture_l1_data_plane_dasha_partition" not in plan and "complete_l1_data_plane_partition" not in plan


@pytest.mark.parametrize("sig", [B_SIG, C_SIG])
def test_candidate_live_bases_are_production_bytes_and_the_hunks_reproduce_the_candidate(mod, sig):
    base = FILES[sig][0]
    live = read(f"{base}.LIVE.sql")
    md5, ln = lm.LIVE_L1_MANIFEST[sig][:2]
    assert hashlib.md5(live.encode()).hexdigest() == md5 and len(live) == ln
    p = build_patch(mod, sig)                                   # asserts apply_hunks(live, derived hunks) == the candidate text
    for name, old, new in p.hunks:
        assert live.count(old) == 1, name


def test_the_derivation_handles_overlapping_changes_and_refuses_an_unreproducible_hunk_list(mod):
    h = helper()
    live = "A\nB\nC\nD\nE\nF\nG\n$function$\n"
    patched = "A\nB2\nC\nD2\nE\nF\nG\n$function$\n"
    hunks = h.derive_hunks(live, patched, "T")
    assert mod.pa.apply_hunks(live, hunks) == patched
    for _, old, _ in hunks:
        assert live.count(old) == 1
    # the F-A2 + patch A hunks of the shipped plan are reproduced by the same derivation
    p = mod.CAPTURE_PATCH
    again = h.derive_hunks(p.live_def(), p.patched_def(), "R")
    assert mod.pa.apply_hunks(p.live_def(), again) == p.patched_def()


def test_the_executor_with_b_and_c_admitted_applies_attests_and_rolls_back_all_three(cluster, mod, db, tmp_path, monkeypatch):
    live_dir = tmp_path / "live_defs"
    live_dir.mkdir()
    (live_dir / mod.CAPTURE_PATCH.live_file.name).write_bytes(mod.CAPTURE_PATCH.live_file.read_bytes())
    pb, pc = build_patch(mod, B_SIG), build_patch(mod, C_SIG)
    for p in (pb, pc):
        (live_dir / f"{p.short}.LIVE.sql").write_bytes(read(f"{p.short}.LIVE.sql").encode())
    monkeypatch.setattr(mod, "LIVE_DEFS", live_dir)
    monkeypatch.setattr(mod, "FUNCTION_PATCHES", mod.FUNCTION_PATCHES + (pb, pc))
    runner = cf.Runner(cluster, mod, db, tmp_path)

    def fns():
        return cluster.su(db, "SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                              "WHERE n.nspname='public' AND (p.proname LIKE 'l1\\_data\\_plane\\_%' OR p.proname IN ('complete_l1_data_plane_partition',"
                              "'capture_l1_data_plane_dasha_partition')) ORDER BY 1")
    pre, pre_fn = runner.state(), fns()
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    assert res["checks"]["post_exactly_3_function_entries_changed"] and res["checks"]["post_exactly_3_function_attestation_entries_changed"]
    assert {a for a, b in set(fns()) - set(pre_fn)} == {"l1_data_plane_capture_row()", B_SIG, C_SIG}
    for p in (pb, pc):
        assert cluster.su(db, "SELECT definition_digest FROM public.l1_data_plane_function_attestations WHERE function_signature=%s", (p.signature,))[0][0] == p.patched_sha256
    code, rb = runner.run("rollback")
    assert code == 0 and rb["status"] == "COMMITTED", rb["details"]
    assert runner.state() == pre and fns() == pre_fn
