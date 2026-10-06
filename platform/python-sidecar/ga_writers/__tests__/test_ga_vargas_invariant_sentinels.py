"""ga_vargas writes its six INVARIANT scope-cap sentinels once per build (TI-l1-writer-fixes-001).

Data-plane rehearsal: ``ga_vargas`` reported 38,620 rows for 38,596 distinct stored rows.  The
difference (24) is the six ``ayanamsha_id='INVARIANT'`` ``scope_cap`` sentinels (D81 + five floored
bodies): every one of the five ayanamsha sub-steps deleted all six and re-emitted them, so five
sub-steps reported 30 sentinel rows for six stored rows (24 overwrites, none dropped).  Same class
as the ``ga_strength`` finding.

These tests drive the REAL registered writer (all five ``GaVargasWriter`` sub-steps behind the real
``l1_producer_contract`` runtime boundary) on a SYNTHETIC chart against a stateful in-memory
``chart_divisionals`` that models the unique key, ``ON CONFLICT DO NOTHING``, and the writer's
DELETEs.  They assert: reported == stored distinct == distinct identities written, and that the
INVARIANT sentinels are present exactly once and survive the later sub-steps.
"""
from __future__ import annotations

import collections

import pytest

import ga_writers.ga_vargas_writer as gv
from pipeline.orchestrator.writers import ContextSpec, discover_all, list_writers


@pytest.fixture(scope="module", autouse=True)
def _data_plane_build_path_on():
    """N-165: the data-plane build path is OFF by default. This module drives the dormant
    complete_l1_data_plane_partition row-count contract (its ``built`` fixture is module
    scoped), so it switches the one switch on for the whole module."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("ga_writers.data_plane_contracts.DATA_PLANE_BUILD_PATH_ENABLED", True)
        yield

CHART = "aaaaaaaa-1111-4222-8333-000000000001"  # synthetic: not a real chart id
BUILD = "bbbbbbbb-1111-4222-8333-000000000001"
SYNTHETIC_BP = {
    "datetime_iso": "1991-07-19T06:20:00",
    "latitude_deg": 18.52,
    "longitude_deg": 73.86,
    "tz_offset_hours": 5.5,
    "place_name": "synthetic",
    "subject_label": "syn",
}
# The seven-column key of the live chart_divisionals unique index once F-A2 (Q-L1-01, PR #2858) is
# applied -- the state the S-L1 rebuild runs in.  The five floored-body sentinels differ ONLY in
# fact_subject, so under the pre-F-A2 six-column key four of them collide on one stored row; that is
# F-A2's defect and is not modelled here.
KEY = (
    "chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key", "fact_subject",
)


# ga_sensitive's kn_rao karaka_chara_position rows as ga_vargas now READS them (#2878: ga_vargas reads the
# karaka assignment, it no longer derives it): (subject, key, text, num), a clean 1..8 permutation.
_KARAKA_ROWS = [
    (subj, key, text, num)
    for rank, (subj, graha) in enumerate([
        ("ATMAKARAKA", "Moon"), ("AMATYAKARAKA", "Saturn"), ("BHRATRIKARAKA", "Sun"),
        ("MATRIKARAKA", "Venus"), ("PITRIKARAKA", "Mars"), ("PUTRAKARAKA", "Rahu"),
        ("GNATIKARAKA", "Jupiter"), ("DARAKARAKA", "Mercury"),
    ], start=1)
    for key, text, num in (("assigned_graha", graha, None), ("karaka_rank", None, float(rank)))
]


class _Result:
    def __init__(self, row=None, rowcount=0, rows=()):
        self._row = row
        self._rows = list(rows)
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Table:
    """In-memory chart_divisionals: unique on KEY, DO NOTHING on conflict."""

    def __init__(self):
        self.rows: dict[tuple, dict] = {}
        self.landed = 0  # rows the "database" reported as inserted, across the whole build
        self.identities: set[tuple] = set()  # every distinct identity ever written

    def insert(self, rows):
        n = 0
        for r in rows:
            k = tuple(r.get(c) for c in KEY)
            if k in self.rows:
                continue
            self.rows[k] = r
            self.identities.add(k)
            n += 1
        self.landed += n
        return n

    def delete(self, pred):
        gone = [k for k, r in self.rows.items() if pred(r)]
        for k in gone:
            del self.rows[k]
        return len(gone)


class _Cursor:
    def __init__(self, conn):
        self._conn = conn
        self.rowcount = 0
        self._last = _Result()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        res = self._conn._run(sql, params)
        self._last = res
        self.rowcount = res.rowcount
        return res

    def fetchall(self):
        return self._last.fetchall()

    def executemany(self, sql, rows):
        assert "INSERT INTO chart_divisionals" in sql
        self.rowcount = self._conn.table.insert(list(rows))

    def fetchone(self):
        return None


class _DivisionalsConn:
    """Recording double for the writer's SQL plus a model of the L1 partition-completion check."""

    _l1_contract_test_double = True

    def __init__(self):
        self.table = _Table()
        self.reported: list[tuple[str, int]] = []

    def cursor(self, *a, **k):
        return _Cursor(self)

    def execute(self, sql, params=None):
        return self._run(sql, params)

    def _run(self, sql, params):
        s = " ".join(sql.split())
        if s.startswith("DELETE FROM chart_divisionals"):
            if "ayanamsha_id = 'INVARIANT'" in s:
                n = self.table.delete(
                    lambda r: r["chart_id"] == params[0] and r["ayanamsha_id"] == "INVARIANT")
            else:  # replace_prior_chart_divisionals: chart + varga[s] (+ ayanamsha[s])
                cid, vargas = params[0], params[1]
                ays = params[2] if len(params) > 2 else None
                n = self.table.delete(
                    lambda r: r["chart_id"] == cid and r["varga"] in vargas
                    and (ays is None or r["ayanamsha_id"] in ays))
            return _Result(rowcount=n)
        if s.startswith("SELECT COUNT(*) FROM chart_divisionals"):
            cid, ay, varga, _build = params
            n = sum(1 for r in self.table.rows.values()
                    if r["chart_id"] == cid and r["ayanamsha_id"] == ay and r["varga"] == varga)
            return _Result(row={"count": n})
        if "FROM chart_facts" in s and "karaka_chara_position" in s:
            return _Result(rows=_KARAKA_ROWS)
        if "FROM pg_indexes" in s:  # F-A2's fail-closed index-grain check, when that writer is present
            return _Result(row={"indexdef": "CREATE UNIQUE INDEX chart_divisionals_unique_idx ON "
                                f"public.chart_divisionals ({', '.join(KEY)})"})
        if "complete_l1_data_plane_partition" in s:
            self.reported.append((params[3], params[-1]))
        return _Result()


@pytest.fixture(scope="module")
def built():
    discover_all()
    conn = _DivisionalsConn()
    writer = list_writers()["ga_vargas"]()
    ctx = ContextSpec(
        asset_id="ga_vargas", build_id=BUILD, db_conn=conn,
        config={"chart_id": CHART, "birth_params": SYNTHETIC_BP},
    )
    per_step = [(step.key, writer.run_substep(ctx, step).rows_inserted) for step in writer.plan_substeps(ctx)]
    return conn, per_step


def test_reported_equals_stored_distinct_equals_identities_written(built):
    conn, per_step = built
    reported = sum(n for _, n in per_step)
    assert len(per_step) == 5
    assert reported == len(conn.table.rows)            # sub-step total == rows stored
    assert reported == len(conn.table.identities)      # == distinct identities ever written
    assert reported == conn.table.landed               # nothing overwritten and re-counted
    assert [n for _, n in conn.reported] == [n for _, n in per_step]  # the boundary saw the same numbers


def test_invariant_sentinels_are_stored_once_and_reported_once(built):
    conn, per_step = built
    sentinels = [r for r in conn.table.rows.values() if r["ayanamsha_id"] == "INVARIANT"]
    assert len(sentinels) == 6, "D81 + five floored bodies"
    assert {r["fact_category"] for r in sentinels} == {"scope_cap"}
    # Only the first sub-step reports them: the other four sub-steps carry no INVARIANT row.
    first, *rest = (n for _, n in per_step)
    per_ay = collections.Counter(r["ayanamsha_id"] for r in conn.table.rows.values())
    non_sentinel = {ay: n for ay, n in per_ay.items() if ay != "INVARIANT"}
    assert sorted(non_sentinel.values())[0] > 0
    assert first - non_sentinel[per_step[0][0]] == 6
    for (key, n) in per_step[1:]:
        assert n == non_sentinel[key]


def test_a_later_substep_alone_leaves_existing_sentinels_untouched(built):
    """Resume case: re-running one non-first sub-step must not delete the sentinels."""
    conn, per_step = built
    before = {k for k, r in conn.table.rows.items() if r["ayanamsha_id"] == "INVARIANT"}
    writer = list_writers()["ga_vargas"]()
    ctx = ContextSpec(
        asset_id="ga_vargas", build_id=BUILD, db_conn=conn,
        config={"chart_id": CHART, "birth_params": SYNTHETIC_BP},
    )
    step = writer.plan_substeps(ctx)[-1]
    writer.run_substep(ctx, step)
    after = {k for k, r in conn.table.rows.items() if r["ayanamsha_id"] == "INVARIANT"}
    assert after == before and len(after) == 6


def test_reemitting_the_sentinels_every_pass_is_the_reported_vs_stored_gap(monkeypatch):
    """Mutation guard: the pre-fix behaviour (every pass emits) reports more rows than are stored."""
    monkeypatch.setattr(gv, "CANONICAL_AYANAMSHAS", _EveryPassIsFirst(gv.CANONICAL_AYANAMSHAS))
    discover_all()
    conn = _DivisionalsConn()
    writer = list_writers()["ga_vargas"]()
    ctx = ContextSpec(
        asset_id="ga_vargas", build_id=BUILD, db_conn=conn,
        config={"chart_id": CHART, "birth_params": SYNTHETIC_BP},
    )
    reported = 0
    for step in writer.plan_substeps(ctx):
        reported += writer.run_substep(ctx, step).rows_inserted
    assert reported - len(conn.table.rows) == 24  # 6 sentinels x 4 re-emissions


class _EveryPassIsFirst(dict):
    """A CANONICAL_AYANAMSHAS whose ``next(iter(...))`` is whichever sub-step is running."""

    def __init__(self, base):
        super().__init__(base)
        self._base = dict(base)

    def __iter__(self):
        # build_ga_vargas asks for the first key; answer with the key of the pass in flight.
        import inspect
        frame = inspect.currentframe().f_back
        ayan = frame.f_locals.get("ayan_id")
        return iter([ayan] if ayan else list(self._base))
