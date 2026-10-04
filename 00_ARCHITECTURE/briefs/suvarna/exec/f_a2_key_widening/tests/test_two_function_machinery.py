"""The executor machinery is DATA-DRIVEN: a second (or third) function hunk is added as DATA (one FunctionPatch + one live_defs file) and every
precondition, apply step, EXPECTED_DIFF commit condition, the generic rollback and the re-attestation follow. This proves it on a disposable
PostgreSQL with a SYNTHETIC second hunk (a comment-only edit of the real l1_data_plane_guard_generation_change body, a function that is NOT one of the plan's patched functions): it is a machinery proof, NOT part of the plan (the plan's functions are capture row, patch B, patch C)."""
from __future__ import annotations

import hashlib

import pytest

import conftest as cf

SIG2 = "l1_data_plane_guard_generation_change()"          # NOT one of the plan's patched functions
ANCHOR = "\n$function$\n"                                  # the closing line of the body: occurs exactly once
NEW = "\n  -- synthetic extra hunk (machinery proof)\n$function$\n"


@pytest.fixture()
def two(cluster, mod, db, tmp_path, monkeypatch):
    live = tmp_path / "live_defs"
    live.mkdir()
    for existing in mod.FUNCTION_PATCHES:
        (live / existing.live_file.name).write_bytes(existing.live_file.read_bytes())
    body = cluster.su(db, f"SELECT pg_get_functiondef('public.{SIG2}'::regprocedure)")[0][0]
    (live / "l1_data_plane_guard_generation_change.LIVE.sql").write_bytes(body.encode())
    owner, secdef, config, acl = cluster.su(db, "SELECT pg_get_userbyid(proowner), prosecdef, COALESCE(proconfig::text,''), COALESCE(proacl::text,'') "
                                                f"FROM pg_proc WHERE oid='public.{SIG2}'::regprocedure")[0]
    new = mod.pa.apply_hunks(body, [("S2_synthetic_comment", ANCHOR, NEW)])
    p2 = mod.FunctionPatch(
        signature=SIG2, live_md5=hashlib.md5(body.encode()).hexdigest(), live_len=len(body), live_sha256=hashlib.sha256(body.encode()).hexdigest(),
        owner=owner, secdef=secdef, config=config, acl=acl, hunks=(("S2_synthetic_comment", ANCHOR, NEW),),
        patched_md5=hashlib.md5(new.encode()).hexdigest(), patched_sha256=hashlib.sha256(new.encode()).hexdigest(),
        diff_sha256=mod.pa.diff_digest(body, new), diff_hunks=len(mod.pa.unified_hunks(body, new)))
    monkeypatch.setattr(mod, "LIVE_DEFS", live)
    monkeypatch.setattr(mod, "FUNCTION_PATCHES", mod.FUNCTION_PATCHES + (p2,))
    return p2


def fn_state(cluster, db):
    return cluster.su(db, "SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                          "WHERE n.nspname='public' AND (p.proname LIKE '%l1\\_data\\_plane\\_%' OR p.proname IN ('complete_l1_data_plane_partition',"
                          "'capture_l1_data_plane_dasha_partition')) ORDER BY 1")


def test_a_second_function_hunk_applies_attests_and_rolls_back_through_the_same_machinery(two, cluster, mod, db, tmp_path):
    runner = cf.Runner(cluster, mod, db, tmp_path)
    pre, pre_fn = runner.state(), fn_state(cluster, db)
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    for name in ("post_exactly_4_function_entries_changed", "post_exactly_4_function_attestation_entries_changed",
                 "post_l1_data_plane_guard_generation_change_body_is_exactly_the_bound_body",
                 "post_l1_data_plane_guard_generation_change_diff_is_exactly_the_planned_hunks",
                 "post_l1_data_plane_guard_generation_change_attestation_matches_live_function",
                 "post_l1_data_plane_guard_generation_change_attestation_is_the_bound_digest"):
        assert res["checks"][name] is True, name
    assert cluster.su(db, f"SELECT md5(pg_get_functiondef('public.{SIG2}'::regprocedure))")[0][0] == two.patched_md5
    assert cluster.su(db, "SELECT definition_digest FROM public.l1_data_plane_function_attestations WHERE function_signature=%s", (SIG2,))[0][0] == two.patched_sha256
    changed = {a for a, b in set(fn_state(cluster, db)) - set(pre_fn)}
    assert changed == {p.signature for p in mod.FUNCTION_PATCHES}                       # exactly the plan's patched functions, nothing else
    code, rb = runner.run("rollback")
    assert code == 0 and rb["status"] == "COMMITTED", rb["details"]
    assert runner.state() == pre and fn_state(cluster, db) == pre_fn             # every md5, every attestation row: the pre-state


def test_a_hunk_anchor_that_stopped_matching_the_live_body_is_refused_before_any_connection(two, mod):
    import dataclasses
    bad = dataclasses.replace(two, hunks=(("S2_synthetic_comment", ANCHOR + "no such text", NEW),))
    with pytest.raises(mod.ExpectedDiffError):
        bad.patched_def()


def test_the_second_function_pre_state_is_checked_byte_for_byte(two, cluster, mod, db, tmp_path):
    runner = cf.Runner(cluster, mod, db, tmp_path)
    # a different body in the database than the plan's: refused, nothing changed (exact bytes, not just the md5)
    body = cluster.su(db, f"SELECT pg_get_functiondef('public.{SIG2}'::regprocedure)")[0][0]
    drift = body.replace("\n$function$\n", "\n  -- drift\n$function$\n")
    cluster.su(db, drift)
    code, res = runner.run("apply")
    assert code != 0 and "pre_l1_data_plane_guard_generation_change_body_is_the_bound_body" in res["failed_checks"]
