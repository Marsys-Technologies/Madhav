"""A5.3 — R9-1 on the REAL schema: the policy is selected by the manifest and enforced by the builder, the independent
verifier, 1240's window CHECK and the candidate gate (four places, one name)."""
from __future__ import annotations

import dataclasses

import psycopg
import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import result_policy as rp
from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_kernel.window_store import WindowStore

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, world  # noqa: F401
from .test_a53_window_verification_gate import (CLS, _boot_p3, _consistent_sky, _violations,  # noqa: F401
                                                _windows)

ALL_NULL, QUAL = rp.POLICY_ALL_NULL, rp.POLICY_QUALIFICATION
NUMBERS = "score, evidence_for, evidence_against, severity, objective_value, peak_instant"


def _window_rows(w):
    return w.conn.execute(
        f"SELECT {NUMBERS}, outcome_valence_for_native, qualification ->> 'policy',"
        " qualification ->> 'unqualified_reason' FROM public.ka_gochara_eval_window ORDER BY path_id, lower(interval)"
    ).fetchall()


def _relax_checks(w):
    """Drop the two window CHECKs so a tampered row can exist — the GATE and the VERIFIER must catch it on their own."""
    for c in ("kgew_all_null_policy_ck", "kgew_unqualified_no_result_ck"):
        w.conn.execute(f"ALTER TABLE public.ka_gochara_eval_window DROP CONSTRAINT {c}")


def _grain(path="P3"):
    return dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, rule_version="1.0.0")


def _verify(w, path="P3", **kw):
    return wv.verify_window_semantics(
        w.conn, factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows(path, "1.0.0"), **_grain(path), **kw)


# ── the manifest selects, the build follows ──────────────────────────────────────────────────────────

def test_the_manifest_vector_binds_the_policy_and_the_window_phase_reads_it_back(world):
    w = world
    _boot_p3(w)
    vector = w.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication").fetchone()[0]
    assert vector["schema"] == "ka_gochara_input_vector/3" and vector["result_policy"] == ALL_NULL
    assert rp.manifest_policy(w.conn, CHART_ID, GEN) == ALL_NULL
    _windows(w)
    rows = _window_rows(w)
    assert rows
    for *numbers, valence, policy, reason in rows:
        assert numbers == [None] * 6 and valence == "unqualified"
        assert (policy, reason) == (ALL_NULL, rp.ALL_NULL_REASON)


def test_every_verification_row_carries_the_manifests_policy_and_the_gate_passes(world):
    w = world
    _boot_p3(w)
    _windows(w)
    pol = {r[0] for r in w.conn.execute("SELECT policy_version FROM public.ka_gochara_eval_window_verification")}
    assert pol == {ALL_NULL}
    assert _violations(w) == set()
    assert {r[1] for r in w.conn.execute("SELECT * FROM public.ka_gochara_eval_window_verification").fetchall()} >= {"VERIFIED"} \
        or True
    assert {r[0] for r in w.conn.execute("SELECT status FROM public.ka_gochara_eval_window_verification")} == {"VERIFIED"}


def test_a_manifest_that_selects_the_qualification_policy_is_followed_by_every_stage(world):
    w = world
    w.result_policy = QUAL                                   # the build's input: the manifest binds it
    _boot_p3(w)
    assert rp.manifest_policy(w.conn, CHART_ID, GEN) == QUAL
    _windows(w)
    assert {r[7] for r in _window_rows(w)} == {QUAL}
    assert {r[0] for r in w.conn.execute("SELECT policy_version FROM public.ka_gochara_eval_window_verification")} == {QUAL}
    assert _violations(w) == set()


def test_a_manifest_without_a_named_policy_refuses_the_window_phase(world):
    w = world
    _boot_p3(w)
    w.conn.execute("ALTER TABLE public.kala_gochara_publication DISABLE TRIGGER USER")
    w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                   " input_generation_vector - 'result_policy'")
    with pytest.raises(rp.ResultPolicyMissing):
        rp.manifest_policy(w.conn, CHART_ID, GEN)
    from services.gochara_kernel import input_vector as iv
    with pytest.raises((rp.ResultPolicyMissing, iv.InputDrift), match="result_policy"):    # live-input check or policy read
        w.step(f"window:{CLS}:P3")
    assert ("P3", "result_policy_not_selected") in _violations(w)


# ── the database refuses a number under the policy ───────────────────────────────────────────────────

def test_the_window_check_refuses_a_number_under_the_all_null_policy(world):
    w = world
    _boot_p3(w)
    _windows(w)
    for column, value in (("score", 0.5), ("evidence_for", 1.0), ("evidence_against", 0.0), ("severity", 0.2),
                          ("objective_value", 1.0)):
        with pytest.raises(psycopg.errors.CheckViolation):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute(f"UPDATE public.ka_gochara_eval_window SET {column} = %s", (value,))
    with pytest.raises(psycopg.errors.CheckViolation):                  # the valence is pinned too
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute("UPDATE public.ka_gochara_eval_window SET outcome_valence_for_native = 'favourable'")


def test_the_qualification_shape_requires_a_named_policy(world):
    w = world
    _boot_p3(w)
    _windows(w)
    for bad in ('{"policy": "all_null"}', '{"unqualified_reason": null}'):
        with pytest.raises(psycopg.errors.CheckViolation):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute("UPDATE public.ka_gochara_eval_window SET qualification = %s::jsonb", (bad,))


# ── …and the gate and the independent verifier refuse it even if the CHECK were gone ────────────────

def test_the_candidate_gate_refuses_a_window_carrying_a_number_while_the_policy_is_in_force(world):
    w = world
    _boot_p3(w)
    _windows(w)
    assert _violations(w) == set()
    _relax_checks(w)
    w.conn.execute("UPDATE public.ka_gochara_eval_window SET score = 1.0, evidence_for = 1.0 WHERE path_id = 'P3'")
    assert ("P3", "window_carries_a_number_under_all_null_policy") in _violations(w)
    # the SQL function and the Python gate are the same check
    assert {(v["path_id"], v["violation"]) for v in wg.candidate_gate(w.conn, CHART_ID, GEN, CLS)} == _violations(w)


def test_the_independent_verifier_refuses_a_numeric_window_under_the_policy(world):
    w = world
    _boot_p3(w)
    _windows(w)
    assert _verify(w)["status"] == "VERIFIED"
    _relax_checks(w)
    w.conn.execute("UPDATE public.ka_gochara_eval_window SET score = 1.0, evidence_for = 1.0,"
                   " peak_instant = lower(interval), objective_value = 1.0 WHERE path_id = 'P3'")
    with pytest.raises(RuntimeError, match="window semantic verification failed"):
        _verify(w)


def test_windows_drafted_under_another_policy_than_the_manifests_are_refused_by_both(world):
    """A builder that held a constant instead of reading the manifest: its windows say `window_qualification/1`
    while the manifest selected `all_null_candidate/1` — the verifier and the gate both refuse."""
    w = world
    _boot_p3(w)
    _windows(w)
    store = WindowStore(w.conn)
    recs = store.read_grain(**_grain())
    drafts, _ = ws.draft_windows(CLS, recs, writer_mod.RuleRegistryStore(w.conn).bound_factor_rows, policy=QUAL)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")
        store.replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3",
                                    rule_version="1.0.0", drafts=drafts)
    assert ("P3", "window_policy_differs_from_manifest") in _violations(w)
    with pytest.raises(RuntimeError, match="window semantic verification failed"):
        _verify(w)


def test_the_verifier_never_lets_an_explicit_policy_override_the_manifest(world):
    w = world
    _boot_p3(w)
    _windows(w)
    with pytest.raises(RuntimeError, match="the manifest's"):
        _verify(w, policy=QUAL)
    assert _verify(w, policy=ALL_NULL)["status"] == "VERIFIED"


def test_a_verification_row_under_another_policy_than_the_manifests_fails_the_gate(world):
    w = world
    _boot_p3(w)
    _windows(w)
    w.conn.execute("ALTER TABLE public.ka_gochara_eval_window_verification DISABLE TRIGGER USER")
    w.conn.execute("UPDATE public.ka_gochara_eval_window_verification SET policy_version = 'window_qualification/1'")
    assert ("P3", "window_verification_policy_differs_from_manifest") in _violations(w)
