"""
test_dasha_scope_cap_sentinel.py — SD-DASHA-1 (SAMĀPTI v2.0 §9.5) regression.

Defect: the 2 chart_dashas scope-cap sentinel rows (Prana Dasha 5th-level;
KP sub-period levels beyond sub_sub — both "intentionally not computed, so
absence != bug") were only ever written from build_ga_dashas(), the CLI/
full-build entry point. The orchestrator adapter
(pipeline/orchestrator/writers/ga_dashas.py), which drives every real
"click Build" chart, calls build_system()/_run_concurrency_post_pass_db()
directly in run_substep() and never called build_ga_dashas() at all — so
every orchestrator-built chart silently lacked both sentinel rows. Confirmed
live (2026-07-30): `SELECT chart_id, count(*) FROM chart_dashas WHERE
system_id='scope_cap' GROUP BY chart_id` returns ZERO rows for all 3 charts
in production (482012f1 canonical, 1c826d5a, cb73cd3d — all orchestrator-
built). Carried unfixed across two prior campaigns (PARKED_FINDINGS_CLOSE,
SATYA-DĪPA) per the register.

Fix: extract the sentinel-writing logic into a single conn-aware function,
`write_dasha_scope_cap_sentinels()`, following the exact owns_conn pattern
already established by `_run_concurrency_post_pass_db` in the same module
(conn=None -> opens+commits its own, legacy CLI path; conn injected -> runs
on the caller-owned connection without committing, FROZEN orchestrator
contract §N.2). Both build_ga_dashas() and the orchestrator's post-pass
substep now call this one function, so the two build paths cannot silently
diverge on this again.

NO DB required — uses monkeypatching to observe call shape, matching the
style of test_ga_orchestrator_conformance.py and test_ga_dashas_copy_upsert.py.
"""
from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as gdw  # noqa: E402
from pipeline.orchestrator.writers import (  # noqa: E402
    discover_all, get_writer, ContextSpec, SubStep,
)


class _Sentinel:
    """Stands in for ctx.db_conn — identity-checked, never used as a real conn.

    Accepts the SAVEPOINT / RELEASE / ROLLBACK TO SAVEPOINT statements that
    `write_dasha_scope_cap_sentinels` now issues around each sentinel write
    (see `test_dasha_sentinel_savepoint_isolation.py` for why they exist), but
    models no failure behaviour — every test in THIS module stubs
    `_upsert_rows` to always succeed, so nothing here ever aborts.
    """

    def __init__(self) -> None:
        self.commits = 0

    def cursor(self):
        return self

    def execute(self, sql, *args, **kwargs):
        return self

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _ctx(conn):
    return ContextSpec(asset_id='ga_dashas', build_id='build-XYZ', db_conn=conn,
                       config={'chart_id': 'chart-C'})


# ── A. write_dasha_scope_cap_sentinels() itself ─────────────────────────────────

def test_write_dasha_scope_cap_sentinels_writes_both_rows(monkeypatch):
    """Both the Prana (level_n=5) and KP-beyond-sub_sub (level_n=4) rows are
    built under system_id='scope_cap' / ayanamsha_id='INVARIANT', for the
    chart_id/build_id passed in — not hardcoded to any one chart.

    SCOPE: this asserts ROW CONSTRUCTION under a stub where `_upsert_rows`
    always succeeds. It is NOT a claim about production. In production the
    Prana row's level_n=5 violates `chart_dashas`.`cd_level_n_max4` and never
    lands — `written` is 1, not 2, and `system_id='scope_cap'` has held ZERO
    rows for every chart since the feature was written. See
    `test_dasha_sentinel_savepoint_isolation.py` for the real-semantics tests.
    """
    calls = []

    def fake_upsert_rows(conn, rows, system_id, ayanamsha_id, *, commit=True):
        calls.append({'conn': conn, 'rows': rows, 'system_id': system_id,
                       'ayanamsha_id': ayanamsha_id, 'commit': commit})
        return len(rows)

    monkeypatch.setattr(gdw, '_upsert_rows', fake_upsert_rows)

    sentinel = _Sentinel()
    written = gdw.write_dasha_scope_cap_sentinels('chart-XYZ', 'build-123', conn=sentinel)

    assert written == 2
    assert len(calls) == 2
    level_ns = sorted(c['rows'][0]['level_n'] for c in calls)
    assert level_ns == [4, 5]
    for c in calls:
        assert c['system_id'] == 'scope_cap'
        assert c['ayanamsha_id'] == 'INVARIANT'
        row = c['rows'][0]
        assert row['chart_id'] == 'chart-XYZ'
        assert row['build_id'] == 'build-123'
        assert row['system_id'] == 'scope_cap'
        assert row['ayanamsha_id'] == 'INVARIANT'
        assert row['verification_pass_status'] == 'scope_cap_sentinel'


def test_write_dasha_scope_cap_sentinels_injected_conn_does_not_commit(monkeypatch):
    """FROZEN orchestrator contract (§N.2): on an injected connection the
    writer must never commit — the orchestrator owns the transaction."""
    commits_seen = []

    def fake_upsert_rows(conn, rows, system_id, ayanamsha_id, *, commit=True):
        commits_seen.append(commit)
        return len(rows)

    monkeypatch.setattr(gdw, '_upsert_rows', fake_upsert_rows)

    sentinel = _Sentinel()
    gdw.write_dasha_scope_cap_sentinels('chart-XYZ', 'build-123', conn=sentinel)

    assert commits_seen == [False, False]


def test_write_dasha_scope_cap_sentinels_owned_conn_commits(monkeypatch):
    """Legacy CLI path (conn=None): opens its own connection and DOES commit.

    CHANGED with the savepoint fix, deliberately: the commit now happens ONCE
    on the connection after both sentinels, instead of once per `_upsert_rows`
    call. A COMMIT issued inside a savepoint would end the transaction and
    discard the savepoint, so the RELEASE/ROLLBACK could not run — which is the
    whole mechanism protecting the caller's transaction. The durable outcome is
    unchanged (the CLI path still commits its own work) and is now atomic
    across the sentinel pair rather than partially committed.
    """
    commits_seen = []

    def fake_upsert_rows(conn, rows, system_id, ayanamsha_id, *, commit=True):
        commits_seen.append(commit)
        return len(rows)

    owned = _Sentinel()
    monkeypatch.setattr(gdw, '_upsert_rows', fake_upsert_rows)
    monkeypatch.setattr(gdw, '_conn', lambda: owned)

    written = gdw.write_dasha_scope_cap_sentinels('chart-XYZ', 'build-123')

    assert written == 2
    # commit=False is now passed on BOTH paths (savepoint-compatible)...
    assert commits_seen == [False, False]
    # ...and the owned connection is committed exactly once, at the end.
    assert owned.commits == 1


# ── B. Orchestrator adapter threads the fix into the post-pass substep ─────────

def test_ga_dashas_postpass_substep_writes_scope_cap_sentinels(monkeypatch):
    """THE regression test for SD-DASHA-1: the orchestrator's post-pass
    sub-step must call write_dasha_scope_cap_sentinels() with the SAME
    injected ctx.db_conn used for the concurrency post-pass — proving the
    orchestrator build path no longer silently skips the sentinel rows.

    Pre-fix, ga_dashas.py's run_substep() for the post-pass key called only
    _run_concurrency_post_pass_db() and returned — this test fails against
    that code because write_dasha_scope_cap_sentinels is never invoked.
    """
    discover_all()
    seen_postpass = {}
    seen_sentinels = {}

    def stub_postpass(chart_id, build_id, *, conn=None):
        seen_postpass.update(chart_id=chart_id, build_id=build_id, conn=conn)

    def stub_sentinels(chart_id, build_id, *, conn=None):
        seen_sentinels.update(chart_id=chart_id, build_id=build_id, conn=conn)
        return 2

    monkeypatch.setattr(gdw, '_run_concurrency_post_pass_db', stub_postpass)
    monkeypatch.setattr(gdw, 'write_dasha_scope_cap_sentinels', stub_sentinels)

    sentinel = _Sentinel()
    w = get_writer('ga_dashas')()
    res = w.run_substep(_ctx(sentinel), SubStep(key='__concurrency_post_pass__'))

    assert seen_postpass['conn'] is sentinel
    assert seen_postpass['chart_id'] == 'chart-C'
    assert seen_postpass['build_id'] == 'build-XYZ'

    # The load-bearing assertion: the sentinel writer was actually called,
    # on the SAME injected connection, for the SAME chart/build.
    assert seen_sentinels['conn'] is sentinel
    assert seen_sentinels['chart_id'] == 'chart-C'
    assert seen_sentinels['build_id'] == 'build-XYZ'
    assert res.rows_inserted == 2
