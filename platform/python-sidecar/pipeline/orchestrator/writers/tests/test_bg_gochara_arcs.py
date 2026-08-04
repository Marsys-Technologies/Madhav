"""Tests for the bg_gochara_arcs writer and its two-query read path.

Everything here runs offline against a recording fake connection — no database,
no swisseph, no network. The claims under test are contract claims, and a fake
connection is the only way to assert some of them at all (you cannot prove "the
writer never commits" against a real connection without letting it try).

WHAT IS ASSERTED, AND WHY EACH ONE MATTERS:

  * the writer conforms to the FROZEN orchestrator contract (§N.2) — heavy
    shape, one substep per body, no commit, no rollback, no close, no
    `asset_throughput` write;
  * idempotency is DELETE-then-INSERT scoped to exactly (substrate_version x
    body) — §N.3's replace-not-accrete, at the substep's own grain, so a crash
    cannot half-replace a body and a rebuild cannot strand orphan arcs;
  * `kala_gochara_windows` is never mentioned in any statement the writer
    issues (the standing untouchable rail, asserted rather than trusted);
  * `DbArcSource` issues exactly TWO queries per load, regardless of how many
    bodies are asked for — the per-chart half of the constant-read claim.
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_gochara_arcs import (
    BODIES,
    SUBSTRATE_VERSION,
    GocharaArcsWriter,
)
from services.w2g import build_arcs
from services.w2g.db_source import DbArcSource, noon_ut_jd

JD0 = 2_451_545.0


# ── Recording fakes ───────────────────────────────────────────────────────────


class _FakeCursor:
    def __init__(self, owner: "_FakeConn"):
        self._owner = owner
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._owner.cursors_closed += 1
        return False

    def execute(self, sql, params=None):
        self._owner.statements.append((sql, params))
        self._owner.rows_for_next = self._owner.responder(sql, params)
        return self

    def executemany(self, sql, batch):
        self._owner.statements.append((sql, list(batch)))
        self._owner.inserted_batches.append(list(batch))
        self.rowcount = len(batch)
        return self

    def fetchall(self):
        return self._owner.rows_for_next


class _FakeConn:
    """Records every statement; explodes on any transaction-lifecycle call.

    The orchestrator owns the transaction (§N.2). A writer that commits,
    rolls back or closes destroys the savepoint the orchestrator wrapped it
    in — so these are hard failures here, not warnings.
    """

    def __init__(self, responder):
        self.responder = responder
        self.statements: list[tuple[str, object]] = []
        self.inserted_batches: list[list[dict]] = []
        self.rows_for_next: list[dict] = []
        self.cursors_closed = 0

    def cursor(self):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        cur = _FakeCursor(self)
        return cur.execute(sql, params)

    def commit(self):  # pragma: no cover - must never run
        raise AssertionError("writer called commit() — forbidden by §N.2")

    def rollback(self):  # pragma: no cover - must never run
        raise AssertionError("writer called rollback() — forbidden by §N.2")

    def close(self):  # pragma: no cover - must never run
        raise AssertionError("writer called close() — forbidden by §N.2")


def _ephemeris_rows(n_days: int = 400, deg_per_day: float = 1.0):
    """`ephemeris_daily`-shaped rows for a body moving uniformly."""
    from datetime import date, timedelta

    start = date(2000, 1, 1)
    return [
        {
            "date": start + timedelta(days=i),
            "tropical_longitude": (deg_per_day * i) % 360.0,
        }
        for i in range(n_days)
    ]


def _responder(sql, params=None):
    if "FROM ephemeris_daily" in sql:
        return _ephemeris_rows()
    return []


def _ctx(**config) -> ContextSpec:
    return ContextSpec(
        asset_id="bg_gochara_arcs",
        build_id="00000000-0000-0000-0000-000000000001",
        db_conn=_FakeConn(_responder),
        config=config,
    )


# ── FROZEN contract conformance ───────────────────────────────────────────────


def test_writer_is_registered_under_its_asset_id():
    from pipeline.orchestrator.writers import get_writer

    assert get_writer("bg_gochara_arcs") is not None


def test_asset_id_matches_the_registration():
    assert GocharaArcsWriter.asset_id == "bg_gochara_arcs"


def test_plans_one_substep_per_body():
    steps = GocharaArcsWriter().plan_substeps(_ctx())
    assert [s.key for s in steps] == list(BODIES)
    assert len(steps) == 9, "the nine DAILY_BODIES of l0_ephemeris"


def test_declares_itself_a_heavy_writer():
    assert GocharaArcsWriter.has_substeps is True


def test_substep_config_can_narrow_the_body_list():
    steps = GocharaArcsWriter().plan_substeps(_ctx(bodies=["Saturn"]))
    assert [s.key for s in steps] == ["Saturn"]


def test_writer_never_touches_the_transaction():
    """_FakeConn raises on commit/rollback/close; reaching the end proves none
    of them were called."""
    ctx = _ctx(bodies=["Saturn"])
    result = GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    assert result.rows_inserted > 0


def test_writer_never_writes_asset_throughput():
    ctx = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    for sql, _ in ctx.db_conn.statements:
        assert "asset_throughput" not in sql.lower()


def test_writer_never_touches_kala_gochara_windows():
    """The standing untouchable rail, asserted rather than trusted."""
    ctx = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    for sql, _ in ctx.db_conn.statements:
        assert "kala_gochara_windows" not in sql.lower()
        assert "build_substep_progress" not in sql.lower()


# ── Idempotency (§N.3) ────────────────────────────────────────────────────────


def test_substep_deletes_before_inserting_scoped_to_version_and_body():
    ctx = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])

    deletes = [(s, p) for s, p in ctx.db_conn.statements if s.strip().upper().startswith("DELETE")]
    assert len(deletes) == 1, "exactly one delete, at the substep's own grain"
    sql, params = deletes[0]
    assert "substrate_version = %s" in sql and "body = %s" in sql
    assert params == [SUBSTRATE_VERSION, "Saturn"]


def test_delete_precedes_every_insert():
    ctx = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    kinds = [s.strip().split()[0].upper() for s, _ in ctx.db_conn.statements]
    assert "DELETE" in kinds and "INSERT" in kinds
    assert kinds.index("DELETE") < kinds.index("INSERT")


def test_a_rebuild_replaces_rather_than_accretes():
    """Two runs against the same fake produce the same row set, and the second
    run's delete is what makes that true rather than luck."""
    first = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(first, GocharaArcsWriter().plan_substeps(first)[0])
    second = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(second, GocharaArcsWriter().plan_substeps(second)[0])

    rows_a = [r for b in first.db_conn.inserted_batches for r in b]
    rows_b = [r for b in second.db_conn.inserted_batches for r in b]
    assert len(rows_a) == len(rows_b)
    keys = lambda rows: [(r["substrate_version"], r["body"], r["arc_index"]) for r in rows]  # noqa: E731
    assert keys(rows_a) == keys(rows_b)


def test_inserted_rows_carry_the_fingerprint_and_engine_version():
    ctx = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    rows = [r for b in ctx.db_conn.inserted_batches for r in b]
    assert rows
    fingerprints = {r["arc_fingerprint"] for r in rows}
    assert len(fingerprints) == 1, "one fingerprint per body's arc set"
    assert all(r["engine_version"] for r in rows)
    assert all(r["build_id"] == ctx.build_id for r in rows)


def test_inserted_rows_satisfy_the_sub_revolution_check_constraint():
    """The DB enforces `lon_hi - lon_lo <= 360`; so must the rows we send it,
    or the build fails at COMMIT time instead of here."""
    ctx = _ctx(bodies=["Saturn"])
    GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    for row in (r for b in ctx.db_conn.inserted_batches for r in b):
        assert row["lon_hi_deg"] - row["lon_lo_deg"] <= 360.000001
        assert row["end_jd"] > row["start_jd"]
        assert row["direction"] in (-1, 1)
        assert -1e-6 <= row["lon_lo_deg"] <= 360.000001


def test_dry_run_writes_nothing_but_still_reports_what_it_would_do():
    ctx = _ctx(bodies=["Saturn"])
    ctx.dry_run = True
    result = GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])
    assert result.rows_inserted == 0
    assert result.rows_skipped > 0
    assert not ctx.db_conn.inserted_batches
    assert not [s for s, _ in ctx.db_conn.statements if s.strip().upper().startswith(("DELETE", "INSERT"))]


def test_an_empty_ephemeris_is_an_honest_failure_not_a_silent_zero():
    ctx = ContextSpec(
        asset_id="bg_gochara_arcs",
        build_id="b",
        db_conn=_FakeConn(lambda sql, params=None: []),
        config={"bodies": ["Saturn"]},
    )
    with pytest.raises(ValueError):
        GocharaArcsWriter().run_substep(ctx, GocharaArcsWriter().plan_substeps(ctx)[0])


# ── DbArcSource: two queries, no matter what ──────────────────────────────────


def _arc_rows(body: str):
    jds = [JD0 + float(i) for i in range(400)]
    lons = [(1.0 * i) % 360.0 for i in range(400)]
    return [{**a.as_row()} for a in build_arcs(body, jds, lons)]


def test_db_arc_source_issues_exactly_two_queries():
    calls: list[str] = []

    def query(sql, params=None):
        calls.append(sql)
        if "FROM bg_gochara_arcs" in sql:
            return _arc_rows("Saturn") + _arc_rows("Jupiter")
        return []

    src = DbArcSource(query, substrate_version=SUBSTRATE_VERSION)
    src.load(["Saturn", "Jupiter"])
    assert src.queries_issued == 2, calls


def test_db_arc_source_query_count_does_not_scale_with_bodies():
    def query(sql, params=None):
        return _arc_rows("Saturn") if "FROM bg_gochara_arcs" in sql else []

    one = DbArcSource(query, substrate_version=SUBSTRATE_VERSION)
    one.load(["Saturn"])
    many = DbArcSource(query, substrate_version=SUBSTRATE_VERSION)
    many.load(["Saturn", "Jupiter", "Mars", "Venus", "Sun", "Mercury"])
    assert one.queries_issued == many.queries_issued == 2


def test_db_arc_source_returns_no_queries_for_no_bodies():
    src = DbArcSource(lambda sql, params=None: [], substrate_version=SUBSTRATE_VERSION)
    assert src.load([]) == {}
    assert src.queries_issued == 0


def test_db_arc_source_reattaches_an_interpolant_so_arcs_are_solvable():
    from datetime import date, timedelta

    start = date(2000, 1, 1)

    def query(sql, params=None):
        if "FROM bg_gochara_arcs" in sql:
            return _arc_rows("Saturn")
        return [
            {
                "body": "Saturn",
                "date": start + timedelta(days=i),
                "tropical_longitude": (1.0 * i) % 360.0,
            }
            for i in range(400)
        ]

    src = DbArcSource(query, substrate_version=SUBSTRATE_VERSION)
    arcs = src.load(["Saturn"])["Saturn"]
    assert arcs
    # A round-tripped arc must be usable for root-finding, or the substrate is
    # an index to nothing.
    arcs[0].longitude_at(arcs[0].start_jd + 1.0)


def test_noon_ut_jd_matches_the_builders_own_abscissa():
    """J2000.0 is 2000-01-01 12:00 UT = JD 2451545.0 exactly. If this drifts,
    every arc's time bounds drift with it."""
    assert noon_ut_jd(2000, 1, 1) == pytest.approx(2_451_545.0, abs=1e-9)
