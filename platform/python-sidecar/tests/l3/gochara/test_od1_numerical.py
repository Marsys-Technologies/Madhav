"""OD-1 (SR-OD1-NUMERICAL): the century build is the first NUMERICAL-policy build — `window_qualification/1` end to end.

Doctrine/source for each claim: root CLAUDE.md §N.8 (a green is earned by a detector that can read false), MEASURING_BUILD_CONTRACT OO-4 ("result policy (OD-1) -> where
FB-5's oracle can run: all-null; cannot run here") and plan_model.json (`vacuous_under_policy under all_null_candidate/1; never green; real duty returns with OD-1 on the
final-rules candidate`); the policy table itself is `window_sweep.draft_windows`' frozen `window_qualification/1` (R8-4), re-implemented independently in `window_verifier`.
Each claim has ONE oracle and a planted reversion that makes it fail (the reversion is named in the docstring; proofs are recorded in the job result):

  1. the table is frozen: the three copies of its digest (builder, independent vector verifier, seal-brief check script) agree, and the digest moves with the table
                                                                                                    — revert: edit one rule of QUALIFICATION_TABLE
  2. the manifest binds the table under `window_qualification/1` and nothing under all-null (all-null vectors stay byte-identical)
                                                                                                    — revert: bind the component for every policy
  3. a `window_qualification/1` build stores NON-BLANK strength, peak and valence through the writer's window phase (rows that declare their inputs), all-null stays blank
                                                                                                    — revert: the window phase reads a constant policy instead of the manifest's
  4. (test_a53_input_vector.py) the independent verifier refuses a manifest whose bound table is not the frozen one — revert: drop the verifier's comparison
  5. (test_a53_r12_seal_job.py) the verification job refuses a mismatched table through the live-input drift check — revert: leave the table out of build_input_vector
  6. (test_a53_r12_seal_job.py) the sealing job ACCEPTS `window_qualification/1` with the table bound, refuses a mismatched table, and still accepts nothing else unknown
                                                                                                    — revert: restore the single required policy / drop the table check
  7. (test_a53_r12_seal_job.py, `test_n1`…`test_n10`; test_gochara_seal_approval_scripts.py) the NUMERICAL-WINDOW GATE (SR-OD1-DESIGN): the independent job re-derives every window and
     attests it; a blank where the table yields a value, a stub policy, a changed table, a seal / brief without the gate PASSED each REFUSE; honest nulls are counted by reason code;
     the all-null path is unchanged (the claim list is at the head of that block, with each planted reversion)
"""
from __future__ import annotations

import json

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator import seal_job
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import result_policy as rp
from services.gochara_kernel import seal_flow as sf
from services.gochara_kernel import verification_job as vj
from services.gochara_kernel import window_sweep as ws

QUAL, ALL_NULL = rp.POLICY_QUALIFICATION, rp.POLICY_ALL_NULL
PINNED_DIGEST = "5bbc65bb5fc98547bf0bea5d1ff90c76965155f3166a7042a11ab34772e6a80f"      # this test's OWN literal (a fourth copy: it is what the others are compared with)


# ── 1. the table is frozen ─────────────────────────────────────────────────────────────────────────────────────────

def test_the_frozen_table_digest_is_one_value_in_every_copy_and_moves_with_the_table():
    from importlib import util
    from pathlib import Path
    script = Path(__file__).resolve().parents[5] / "platform/scripts/gochara_seal_brief_check.py"
    spec = util.spec_from_file_location("gochara_seal_brief_check_od1", script)
    bc = util.module_from_spec(spec)
    spec.loader.exec_module(bc)
    component = {"schema": rp.QUALIFICATION_TABLE_SCHEMA, "digest": PINNED_DIGEST}
    assert rp.qualification_table_digest() == PINNED_DIGEST
    assert rp.qualification_table_component(QUAL) == component == ivv.QUALIFICATION_TABLE_BINDING == bc.QUALIFICATION_TABLE_BINDING
    assert rp.qualification_table_component(ALL_NULL) is None
    assert rp.DYNAMIC_SWITCH_REASON == ws.DYNAMIC_SWITCH_REASON                    # the table names the sweep's own switch
    edited = json.loads(json.dumps(rp.QUALIFICATION_TABLE))
    edited["rules"][1]["then"] = "stored as a number"
    assert rp.qualification_table_digest(edited) != PINNED_DIGEST                   # a changed rule is a changed identity


def test_the_policy_vocabulary_is_closed_and_the_century_accepts_exactly_the_named_ones():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "platform/scripts"))
    import v5_small_test_shared as shared
    assert rp.RESULT_POLICIES == (ALL_NULL, QUAL) == shared.CENTURY_RESULT_POLICIES == sf.ACCEPTED_POLICIES
    assert writer_mod.CENTURY_CONFIG_SCHEMA == "gochara_v5_century_config/2" and "result_policy" in writer_mod._CENTURY_CONFIG_FIELDS


# ── the DB world: window phase, manifest, verifier, job ─────────────────────────────────────────────────────────────

from .test_a53_inventory import CHART_ID  # noqa: E402
from .test_a53_p1_support import GEN, world  # noqa: E402,F401
from .test_a53_window_verification_gate import (CLS, SPANS, _boot_p3, _windows, _rows)  # noqa: E402,F401


@pytest.fixture(autouse=True)
def _fuzzed_sky(world, monkeypatch):
    """The gate suites' consistent-sky stand-in, widened by half a second at each end of a span. A numeric window makes the sweep ask the geometry whether the
    target is still inside 1 µs before the stored end — finer than a Julian-day float can state (~40 µs at JD 2.46e6) — so the exact stand-in answers 'outside'. The
    verifier's own probes are a whole second inside/outside each end, which the half-second fuzz still separates."""
    from datetime import datetime, timedelta, timezone
    SPANS.clear()
    fuzz = timedelta(milliseconds=500)

    def calc(body, jd, ephe):
        t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=timezone.utc)
        return (195.0 if any(a - fuzz <= t < b + fuzz for a, b in SPANS.get(body.lower(), ())) else 15.0), 2
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc)


def _declared_1_1_0(self, path, version):
    """The ACTUAL 1.1.0 catalogue rows (they declare applicability), bound in place of the 1.0.0 rows the grain's records carry — the same stand-in
    `test_a53_window_sweep_pg._declared_rows` uses; today's final-rules rows declare none (see the job notes)."""
    return [dict(r) for r in ws.registry_factor_rows(path, "1.1.0")]


def _window(w):
    return w.conn.execute("SELECT score, evidence_for, evidence_against, peak_instant, outcome_valence_for_native, qualification ->> 'policy',"
                          " lower(interval) FROM public.ka_gochara_eval_window WHERE path_id = 'P3'").fetchone()


@pytest.mark.parametrize("policy", [QUAL, ALL_NULL])
def test_the_window_phase_stores_the_manifests_policy_blank_or_not(world, monkeypatch, policy):
    """Claim 3 — through the writer's own window phase and the verifier's persisted VERIFIED row. Under `window_qualification/1` the P3 window carries strength
    (score, evidence_for), a peak at the earliest plateau instant and a stored valence (marriage is a gain class: favourable); under all-null the SAME grain is blank.
    (revert: `_run_window_phase` ignores the manifest and drafts under one constant policy — one of the two parametrisations fails)"""
    w = world
    w.result_policy = policy
    monkeypatch.setattr(writer_mod.RuleRegistryStore, "bound_factor_rows", _declared_1_1_0)
    _boot_p3(w)
    _windows(w, ("P3",))
    score, ev_for, ev_against, peak, valence, stored_policy, lo = _window(w)
    assert stored_policy == policy
    if policy == QUAL:
        assert (score, ev_for, ev_against) == (1.0, 1.0, 0.0) and peak == lo and valence == "favourable"
    else:
        assert (score, ev_for, ev_against, peak) == (None, None, None, None) and valence == "unqualified"
    assert [r for r in _rows(w) if r[0] == "P3"] == [("P3", "VERIFIED", 1, 1, 1, 0, policy)]


# ── 2. the manifest binds the table ─────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("policy,bound", [(QUAL, {"schema": rp.QUALIFICATION_TABLE_SCHEMA, "digest": PINNED_DIGEST}), (ALL_NULL, None)])
def test_the_manifest_vector_binds_the_table_only_under_the_qualification_policy(world, policy, bound):
    """Claim 2 (revert: bind it for every policy — the all-null row fails; never bind it — the qualification row fails)."""
    w = world
    w.result_policy = policy
    _boot_p3(w)
    vector = w.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication").fetchone()[0]
    assert vector["result_policy"] == policy and vector.get("qualification_table") == bound
    assert rp.table_problem(vector) is None
    assert rp.require_bound_table(w.conn, CHART_ID, GEN) == policy


def _tamper_table(w, digest="0" * 64):
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set("
                       "input_generation_vector, '{qualification_table,digest}', to_jsonb(%s::text))", (digest,))


def test_a_manifest_that_binds_another_table_is_a_named_mismatch_and_so_is_a_missing_or_unexpected_one(world):
    w = world
    w.result_policy = QUAL
    _boot_p3(w)
    _tamper_table(w)
    with pytest.raises(rp.QualificationTableMismatch, match="qualification_table"):
        rp.require_bound_table(w.conn, CHART_ID, GEN)
    good = {"result_policy": QUAL, "qualification_table": {"schema": rp.QUALIFICATION_TABLE_SCHEMA, "digest": PINNED_DIGEST}}
    assert rp.table_problem(good) is None
    assert rp.table_problem({"result_policy": QUAL}) is not None                                # qualification numbers with no table bound
    assert rp.table_problem({**good, "result_policy": ALL_NULL}) is not None                    # a table beside the all-null policy
    assert rp.table_problem({**good, "qualification_table": {**good["qualification_table"], "schema": "other/1"}}) is not None
