"""SR-OD1 R4 review fix B1 — migration 1402: the window `qualification` shape check admits R-4's combustion-inheritance record and the R-6/R-7 certificate.

Why a database oracle: `window_sweep.qualification()` puts the key `combustion_inheritance` into the jsonb that `ka_gochara_eval_window.qualification` stores,
and 1240's CHECK `kgew_qualification_shape_ck` (→ `ka_gochara_window_qualification_ok`) is a CLOSED key list — the first Form B window INSERT would fail. The
unit tests cannot see that; only the real constraint on a real window can.

The migration text is `platform/migrations/1402_gochara_qualification_provenance_certificate.sql` (placed by the cockpit; on the integration branch since merge-back wave 3a, so the
oracle no longer needs an override). `KALA_MIGRATION_1402` (a path to the file) still overrides it, and the test SKIPS honestly only when the file is missing. It runs on the disposable cluster
(`GOCHARA_A53_ADMIN_DSN`, like the other A5.3 database suites) on a built world whose chain stops at 1240 — so the "before" half is the real 1240 function.

Claims, each with its single planted reversion:
  M1 before 1402 the database refuses a window whose qualification carries `combustion_inheritance`         (the defect; 1240's body)
  M2 after 1402 the same UPDATE of a real built window is accepted, and the record round-trips unchanged      (revert: the key is not added to the allowed list)
  M3 the admitted record is still CLOSED and typed: a missing member, an unknown member, a non-numeric row id,
     a non-string digest are refused                                                                          (revert: the inner shape clause dropped)
  M4 the certificate member is admitted as an object and nothing else; an unknown top-level key is still refused (revert: `certificate` not in the list)
  M5 applying 1402 twice is a no-op, and a window with neither new key keeps satisfying the check              (idempotence; "only admits more")
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from .test_a53_p1_support import world  # noqa: F401
from .test_a53_window_verification_gate import _boot_p3, _consistent_sky, _windows  # noqa: F401

ENV = "KALA_MIGRATION_1402"
_PATH = os.environ.get(ENV) or str(Path(__file__).resolve().parents[4] / "migrations" / "1402_gochara_qualification_provenance_certificate.sql")
pytestmark = pytest.mark.skipif(not _PATH or not Path(_PATH).is_file(),
                                reason=f"NOT_RUN: the migration 1402 file is missing ({_PATH})")

CHECK = "kgew_qualification_shape_ck"
RECORD = {"orb_digest": "ab" * 32, "orb_row_ids": {"Moon": 1, "Mars": 2, "Saturn": 6}, "l1_module": "ga_writers.ga_condition_writer",
          "l1_module_digest": "cd" * 32}


def _migration() -> str:
    return Path(_PATH).read_text(encoding="utf-8")


def _ok(w, q) -> bool:
    return w.conn.execute("SELECT public.ka_gochara_window_qualification_ok(%s::jsonb)", (json.dumps(q),)).fetchone()[0]


def _window(w):
    """One window the real builder stored (its qualification is the policy's own shape) — the row the tests amend."""
    _boot_p3(w)
    _windows(w)
    row = w.conn.execute("SELECT window_id, qualification FROM public.ka_gochara_eval_window"
                         " WHERE qualification IS NOT NULL ORDER BY window_id LIMIT 1").fetchone()
    assert row is not None, "the built world stored no window with a qualification"
    return row


def _amend(w, window_id, extra) -> None:
    """Merge `extra` into the stored qualification of one window, exactly as an INSERT of that jsonb would be checked (user triggers off: only the CHECK is
    under test; the row is otherwise untouched)."""
    with w.conn.transaction():                       # a refused UPDATE rolls the whole block back, the trigger switch included
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_eval_window SET qualification = qualification || %s::jsonb WHERE window_id = %s",
                       (json.dumps(extra), window_id))
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window ENABLE TRIGGER USER")


def _refused(w, window_id, extra) -> bool:
    import psycopg
    try:
        _amend(w, window_id, extra)
    except psycopg.errors.CheckViolation as exc:
        assert CHECK in str(exc)
        return True
    return False


def test_m1_before_1402_the_database_refuses_the_combustion_inheritance_record(world):          # noqa: F811
    window_id, base = _window(world)
    body = world.conn.execute("SELECT prosrc FROM pg_proc WHERE oid = 'public.ka_gochara_window_qualification_ok(jsonb)'::regprocedure").fetchone()[0]
    if "combustion_inheritance" in body:
        pytest.skip("the chain under test already carries 1402")
    assert _ok(world, base) is True
    assert _ok(world, {**base, "combustion_inheritance": RECORD}) is False
    assert _refused(world, window_id, {"combustion_inheritance": RECORD}) is True


def test_m2_after_1402_a_real_window_carries_the_record_and_it_round_trips(world):              # noqa: F811
    window_id, base = _window(world)
    world.conn.execute(_migration())
    _amend(world, window_id, {"combustion_inheritance": RECORD})
    stored = world.conn.execute("SELECT qualification FROM public.ka_gochara_eval_window WHERE window_id = %s", (window_id,)).fetchone()[0]
    assert stored == {**base, "combustion_inheritance": RECORD}


@pytest.mark.parametrize("label, record", [
    ("a member missing", {k: v for k, v in RECORD.items() if k != "l1_module_digest"}),
    ("an unknown member", {**RECORD, "note": "x"}),
    ("a non-numeric row id", {**RECORD, "orb_row_ids": {"Moon": "one"}}),
    ("row ids not an object", {**RECORD, "orb_row_ids": [1, 2]}),
    ("a non-string digest", {**RECORD, "orb_digest": 7}),
    ("not an object", "abc"),
])
def test_m3_the_admitted_record_stays_closed_and_typed(world, label, record):                   # noqa: F811
    window_id, _ = _window(world)
    world.conn.execute(_migration())
    assert _refused(world, window_id, {"combustion_inheritance": record}) is True, label


def test_m4_the_certificate_member_is_admitted_as_an_object_and_nothing_else_is(world):          # noqa: F811
    window_id, base = _window(world)
    world.conn.execute(_migration())
    cert = {"result_class": "INCONCLUSIVE", "cuts": [0.0, 1.5], "eval_count": 12}               # members are the R67 lane's; the outer shape is an object
    assert _ok(world, {**base, "certificate": cert}) is True
    assert _ok(world, {**base, "certificate": cert, "combustion_inheritance": RECORD}) is True
    assert _ok(world, {**base, "certificate": [1, 2]}) is False and _ok(world, {**base, "certificate": "x"}) is False
    assert _ok(world, {**base, "unknown_provenance": {}}) is False                                # the list is still closed
    _amend(world, window_id, {"certificate": cert})
    assert _refused(world, window_id, {"certificate": 3}) is True


def test_m5_applying_1402_twice_is_a_noop_and_windows_without_the_new_keys_still_pass(world):    # noqa: F811
    window_id, base = _window(world)
    world.conn.execute(_migration())
    first = world.conn.execute("SELECT prosrc, proacl::text FROM pg_proc WHERE oid = 'public.ka_gochara_window_qualification_ok(jsonb)'::regprocedure").fetchone()
    world.conn.execute(_migration())
    second = world.conn.execute("SELECT prosrc, proacl::text FROM pg_proc WHERE oid = 'public.ka_gochara_window_qualification_ok(jsonb)'::regprocedure").fetchone()
    assert first == second
    assert _ok(world, base) is True
    assert _ok(world, {**base, "policy": "other/1"}) is False and _ok(world, {"policy": base["policy"]}) is False       # the old rules still hold


def test_m6_the_certificate_the_production_sweep_stores_is_admitted_and_the_sweeps_own_objective_name_is_not(world):    # noqa: F811
    """Merge-back wave 3a (R67 x S3 seam): the window the PRODUCTION sweep (S3's solver adapter, `solver=PRODUCTION_SOLVER`) builds carries the R-7 certificate named by the SOLVER's
    objective (`min_of_group_max` for P4), which 1402's `ka_gochara_solver_certificate_ok` admits — a solved window and a budget-exhausted blank. The sweep's own objective label
    (`max_min_agent_activity`) is a different string the migration refuses: naming the certificate by it would make the first Form B/P4 window INSERT fail. (revert:
    `window_sweep` passes `objective=objective_name` to `stored_certificate`.)"""
    from . import test_od1_s3_integration as s3
    from services.gochara_kernel import window_sweep as ws
    _window_id, _base = _window(world)
    world.conn.execute(_migration())
    recs = s3._p4_records()
    (solved,) = ws.draft_windows("marriage", recs, s3.ROWS, solver=ws.PRODUCTION_SOLVER)[0]
    q = solved.qualification()
    assert q["solver_certificate"]["outcome"] == "solved" and q["solver_certificate"]["objective"] == "min_of_group_max"
    assert _ok(world, q) is True
    (blank,) = ws.draft_windows("marriage", recs, s3.ROWS, solver=ws.SolverConfig(max_evals=3))[0]
    qb = blank.qualification()
    assert qb["solver_certificate"]["outcome"] == "blank" and qb["solver_certificate"]["reason"] == "solver_budget_exhausted"
    assert _ok(world, qb) is True
    assert _ok(world, {**q, "solver_certificate": {**q["solver_certificate"], "objective": ws.OBJECTIVE_P4}}) is False

