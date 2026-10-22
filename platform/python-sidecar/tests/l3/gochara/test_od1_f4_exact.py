"""SR-F4-STORE-EXACT (PRETR-early D-C): a stored float4 maximum is the correctly rounded float4 of the EXACT double sum, and the independent prover accepts it.

The defect: the property_acquisition P3 verification refused three windows whose stored maxima were ONE float4 spacing from the prover's re-derivation. The
builder sums in double and the database rounds that sum once to REAL (the correctly rounded float4); the verifier then read the REAL back through the driver's
default TEXT path, which yields the SHORTEST DECIMAL that round-trips the float4 (1.9420573 for the stored 1.94205725…) — a double up to half a spacing away
from the number the database holds. `_f4_tol` (unchanged) models exactly ONE half-spacing of error (the single rounding of the sum), so the read-back's own
half-spacing stacked on it and a correct store read as a disagreement.

Every oracle states its source. The numbers are closed forms, never the code under test: a record at a constant angular distance d from a point target contributes
`1 − d / orb` (activity_kernel@1.1.0, AM-13 draft), and P3's objective is the sum over roots of the per-root maximum (PLAN §2.1; `path_channel_scores`). With
orb = 4 and d = k · 2⁻³⁰ every per-root value AT THE WINDOW START is a dyadic rational of 32 fractional bits, so the exact sum is a double with NO rounding (`math.fsum`
of the same values is the exact sum of the window's unrounded inputs) while float4 (24 bits) must round it. Every body recedes from its target, each term falls, so the
objective's maximum is its value at the window start (the earliest instant — frozen tie rule N-11).

CLAIMS and the single planted reversion that must FAIL each:

  F1  the stored maximum of a ≥5-summand window is `float32(exact sum)`                    revert: the builder's sum is taken over float4-rounded summands
  F2  the window VERIFIES on the independent checker (solver_check=True), the two           revert: the verifier reads the REAL back as text (no `::float8`)
      property_acquisition shapes (peak_value_mismatch) and the objective-exceeds shape
  F3  a 1-summand window stores the same value as before (no summation happens)             (holds under the F1 reversion too: asserted)
  F4  the columns the verifier reads are REAL (float4) in the applied schema               revert: n/a (a static read of migrations 1156 / 1240)

The three worlds are SYNTHETIC reproductions with the same float4 geometry as the report's three windows (the kept throwaway database was dropped by the PRETR
harness before this item; `PRETR_EARLY.md` §6): the offsets were searched for the property that the shortest-decimal read-back of the correctly rounded float4
falls OUTSIDE `_f4_tol` of the exact sum, in the direction of each reported finding.
"""
from __future__ import annotations

import dataclasses
import math
import re
import uuid
from pathlib import Path

import numpy as np
import pytest

from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_store as wstore
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX, MIGRATIONS
from .test_a53_window_sweep import _rec, _rows_declared
from .test_a53_window_sweep import _restore_factor_registry  # noqa: F401  (autouse: synthetic rows never outlive their test)
from .test_od1_s3_integration import GRAIN_P3, _Conn, _days, _member_rows

ORB = 4.0
Q = 2.0 ** -30                        # one unit of distance: 100 + k·Q is exact in a double for k < 2³², so is k·Q / 4
BODIES = ("jupiter", "saturn", "mars", "venus", "mercury", "sun", "moon")
POINT = 100.0                         # the default point target of the window-sweep fixtures
V = 0.125                             # every body recedes from its target at 1/8 deg/day (the solver needs a moving, monotone arc: H1), so F falls and its maximum is the start
ROWS = lambda p, v: _rows_declared(p, v, orb=ORB)          # noqa: E731

# distances (in units of Q) found by search — see the module docstring; each world also has float32(Σ float32(uᵢ)) ≠ float32(Σ uᵢ), so the F1 reversion shows. `above`: the shortest-decimal read-back is ABOVE the exact sum by more than the float4
# half-spacing (the prover's maximum check: peak_value_mismatch); `below`: it is BELOW (the upper-bound check: objective_exceeds_stored_maximum).
WORLDS = {
    "p3_5roots_1.919_above": [4130925407, 1352232589, 3778505621, 91056038, 3880448959],
    "p3_7roots_5.648_above": [478903138, 28793830, 699827412, 112599186, 1302279559, 2371933256, 811355502],
    "p3_2roots_1.125_below": [2003355180, 1755043546],
}


def _value(k: int) -> float:
    return 1.0 - (k * Q) / ORB


def _exact_sum(ks) -> float:
    return math.fsum(_value(k) for k in ks)


def _records(ks):
    return [_rec(f"r{i}", path="P3", version="1.0.0", relation="conjunction", kind="degree_point", agent=BODIES[i], root=f"R{i}", supports=((0, 10),),
                 longitude_at=(lambda t, _b=POINT + k * Q: _b + V * _days(t))) for i, k in enumerate(ks)]


def _position(ks):
    return lambda body, t: POINT + ks[BODIES.index(body.lower())] * Q + V * _days(t)


def _build(ks):
    (draft,), _ = ws.draft_windows("marriage", _records(ks), ROWS, solver=ws.PRODUCTION_SOLVER)
    return draft


# ── a disposable database with the window table's REAL columns (types read from migrations 1156 / 1240 by the static test below) ──────────

_DDL = """
CREATE TABLE public.ka_gochara_eval_window (
  window_id uuid, chart_id text, event_class text, generation text, path_id text, rule_version text, interval tstzrange,
  peak_instant timestamptz, score REAL, evidence_for REAL, evidence_against REAL, outcome_valence_for_native text, severity REAL,
  coverage_partition_kind text, coverage_partition_key text, coverage_facts jsonb, null_states_used text[],
  objective TEXT, objective_value REAL, qualification JSONB);
CREATE TABLE public.ka_gochara_eval_window_record (
  window_id uuid, record_id text, chart_id text, generation text, event_class text, path_id text, rule_version text);
"""


@pytest.fixture()
def pg():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}f4x_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
        conn.execute(_DDL)
        yield conn
    finally:
        if conn is not None:
            conn.close()
        assert name.startswith(DB_PREFIX), name
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


class _StubRecords:
    """The two RecordStore reads `replace_grain_windows` makes before it writes: no sealed generation, no stored coverage in this fixture."""
    def _refuse_if_sealed(self, *a, **kw):
        return None

    def stored_coverage_facts_json(self, **kw):
        return "{}"


def _store(pg, draft):
    """Write the draft through the PRODUCTION writer (its INSERT binds the double to the REAL column) and return the store's connection."""
    store = wstore.WindowStore(pg)
    store._records = _StubRecords()
    store.replace_grain_windows(chart_id="c", generation="g", event_class="marriage", path_id="P3", rule_version="1.0.0", drafts=[draft])


def _stored_exact(pg) -> float:
    """What the database HOLDS: the REAL widened to double (exact), never the driver's text round-trip."""
    return pg.execute("SELECT objective_value::float8 FROM public.ka_gochara_eval_window").fetchone()[0]


def _stored_as_text_read(pg) -> float:
    return pg.execute("SELECT objective_value FROM public.ka_gochara_eval_window").fetchone()[0]


class _PgWindows(_Conn):
    """`verify_window_semantics` over lists for everything but the window SELECT, which runs — as the verifier wrote it — against the real table."""
    def __init__(self, pg, window_id, records, rewrite=lambda sql: sql):
        super().__init__([(window_id,)], _member_rows(records), [(r.record_id, r.canonical_target) for r in records])
        self.pg, self.rewrite = pg, rewrite

    def execute(self, sql, params=()):
        if "FROM public.ka_gochara_eval_window WHERE" in sql and "ka_gochara_eval_window_record" not in sql:
            return self.pg.execute(self.rewrite(sql), params)
        return super().execute(sql, params)


def _verify(pg, ks, rewrite=lambda sql: sql):
    recs = _records(ks)
    wid = pg.execute("SELECT window_id::text FROM public.ka_gochara_eval_window").fetchone()[0]       # the id the production writer derived
    conn = _PgWindows(pg, wid, recs, rewrite)
    return wv.verify_window_semantics(conn, factor_rows=ROWS("P3", "1.0.0"), policy=wv.POLICY_VERSION, position_at=_position(ks), solver_check=True, **GRAIN_P3)


def _float4_sum_of_rounded_summands(ks) -> float:
    return sum(float(np.float32(_value(k))) for k in ks)


def _revert_to_sum_of_rounded_summands(monkeypatch, ks):
    """Planted reversion F1: the builder's maximum is the sum of FLOAT4-ROUNDED per-root values (what the report hypothesised)."""
    real = ws._solver.solve

    def solve(problem, **kw):
        res = real(problem, **kw)
        return dataclasses.replace(res, value=_float4_sum_of_rounded_summands(ks))
    monkeypatch.setattr(ws._solver, "solve", solve)


# ═════ F1: the builder stores float32(exact double sum) ═══════════════════════════════════════════════════════════════

@pytest.mark.parametrize("name", sorted(WORLDS))
def test_f1_the_stored_maximum_is_the_correctly_rounded_float4_of_the_exact_sum_of_the_unrounded_inputs(pg, name):
    ks = WORLDS[name]
    exact = _exact_sum(ks)
    draft = _build(ks)
    assert draft.unqualified_reason is None and draft.objective_value == pytest.approx(exact, abs=1e-12)       # the builder's own value is the double sum
    _store(pg, draft)
    assert _stored_exact(pg) == float(np.float32(exact))                                                        # computed here, from the inputs — no typed literal
    # the property that makes these worlds a reproduction: the driver's shortest-decimal read of that float4 is outside the prover's float4 interval of the exact sum
    assert abs(_stored_as_text_read(pg) - exact) > chk._f4_tol(exact)


@pytest.mark.parametrize("name", sorted(WORLDS))
def test_f1_reverted_to_a_sum_of_float4_rounded_summands_the_stored_value_is_not_the_rounded_exact_sum(pg, monkeypatch, name):
    ks = WORLDS[name]
    _revert_to_sum_of_rounded_summands(monkeypatch, ks)
    _store(pg, _build(ks))
    assert _stored_exact(pg) != float(np.float32(_exact_sum(ks)))          # the F1 oracle fails on the reverted builder


@pytest.mark.parametrize("name", sorted(WORLDS))
def test_f1_reverted_to_a_sum_of_float4_rounded_summands_the_independent_checker_disagrees(pg, monkeypatch, name):
    """The report's hypothesis made concrete: with the verifier reading the REAL exactly, a builder that summed float4-rounded values is a real disagreement."""
    ks = WORLDS[name]
    _revert_to_sum_of_rounded_summands(monkeypatch, ks)
    draft = _build(ks)
    _store(pg, draft)
    with pytest.raises(RuntimeError, match=r"peak_value_mismatch|objective_exceeds_stored_maximum"):
        _verify(pg, ks)


# ═════ F2: the window verifies on the independent checker ═════════════════════════════════════════════════════════════

@pytest.mark.parametrize("name", sorted(WORLDS))
def test_f2_the_stored_window_verifies_on_the_independent_checker(pg, name):
    ks = WORLDS[name]
    draft = _build(ks)
    _store(pg, draft)
    report = _verify(pg, ks)
    assert report["status"] == "VERIFIED" and report["solver_checked_windows"] == 1 and report["numeric_reproduced"] == 1
    assert abs(report["windows_detail"][0]["objective_value"] - _exact_sum(ks)) <= chk._f4_tol(_exact_sum(ks))        # the stored float4, read exactly, is inside its own interval


@pytest.mark.parametrize("name", sorted(WORLDS))
def test_f2_reverted_to_the_text_read_of_the_real_the_correct_store_is_a_disagreement_again(pg, name):
    """Planted reversion F2: the window SELECT as it was (`score`, `evidence_for`, … read without `::float8`)."""
    ks = WORLDS[name]
    draft = _build(ks)
    _store(pg, draft)
    with pytest.raises(RuntimeError, match=r"peak_value_mismatch|objective_exceeds_stored_maximum"):
        _verify(pg, ks, rewrite=lambda sql: sql.replace("::float8", ""))


def test_f2_the_findings_are_the_reported_kinds(pg):
    """The two shapes the report named: where the text read-back is ABOVE the sum the prover raises the maximum mismatch; where it is BELOW, the objective exceeds the stored maximum."""
    seen = {}
    for name, ks in WORLDS.items():
        pg.execute("DELETE FROM public.ka_gochara_eval_window"); pg.execute("DELETE FROM public.ka_gochara_eval_window_record")
        draft = _build(ks)
        _store(pg, draft)
        with pytest.raises(RuntimeError) as err:
            _verify(pg, ks, rewrite=lambda sql: sql.replace("::float8", ""))
        seen[name] = str(err.value)
    assert "peak_value_mismatch" in seen["p3_5roots_1.919_above"] and "peak_value_mismatch" in seen["p3_7roots_5.648_above"]
    assert "objective_exceeds_stored_maximum" in seen["p3_2roots_1.125_below"]


# ═════ F3: a 1-summand window is unchanged ════════════════════════════════════════════════════════════════════════════

def test_f3_a_one_summand_window_stores_the_same_value_as_before_and_verifies(pg, monkeypatch):
    ks = [1788325144]
    draft = _build(ks)
    _store(pg, draft)
    stored = _stored_exact(pg)
    assert stored == float(np.float32(_value(ks[0])))                                  # one value, one rounding: nothing is summed
    assert _verify(pg, ks)["status"] == "VERIFIED"
    # …and the F1 reversion changes nothing here (a sum of one float4-rounded value is that float4)
    pg.execute("DELETE FROM public.ka_gochara_eval_window"); pg.execute("DELETE FROM public.ka_gochara_eval_window_record")
    _revert_to_sum_of_rounded_summands(monkeypatch, ks)
    _store(pg, _build(ks))
    assert _stored_exact(pg) == stored


# ═════ F4: the columns are REAL in the applied schema ═════════════════════════════════════════════════════════════════

def test_f4_the_window_columns_the_verifier_reads_are_float4_in_the_migrations():
    base = (MIGRATIONS / "1156_gochara_eval_window.sql").read_text()
    gate = (MIGRATIONS / "1240_gochara_window_verification_gate.sql").read_text()
    for col in ("score", "evidence_for", "evidence_against", "severity"):
        assert re.search(rf"^\s*{col}\s+REAL\b", base, re.M), col
    assert re.search(r"ADD COLUMN objective_value REAL", gate)
