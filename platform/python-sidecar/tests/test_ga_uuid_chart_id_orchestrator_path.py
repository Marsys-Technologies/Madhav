"""ga_dashas / ga_tajaka: a REAL ``uuid.UUID`` chart_id reaches the writers (REHEARSAL-LINUX P1).

Defect (on main since #2607, 2026-09-16): ``run_asset`` puts ``run["chart_id"]`` in
``ctx.config['chart_id']`` unconverted, and psycopg decodes a ``uuid`` column to
``uuid.UUID``. ``ga_dashas`` (substep and post-pass) and ``ga_tajaka`` then fed it to
``stable_uuid`` / ``stabilize_hierarchical_uuids`` -> ``canonical_json``, which refuses a UUID::

    ContractError: value is not canonical JSON: Object of type UUID is not JSON serializable

Every earlier test passed a ``str`` (``'chart-C'``), so nothing saw it. These tests drive the
REAL registered adapters with a REAL ``uuid.UUID`` (and no DB: a recording fake connection,
the DB-side helpers stubbed) and pin three things:

* the adapter completes (no ``ContractError``);
* the writer receives a ``str`` (the adapter converts at the boundary);
* every row identity is the SAME as the one a ``str`` chart_id produces (``str(UUID)`` is the
  canonical text form, so converting changes no stored id).

The fix lives in TWO places on purpose. The adapters convert at the orchestrator boundary (the reviewed
proposal; the adapter tests assert the writer RECEIVES a ``str``). The writer entry points (``build_system``,
``write_dasha_scope_cap_sentinels``, ``build_ga_tajaka``) normalise too: the adapter modules are not part of a
writer's code digest (``source_paths`` names the ga_writers module), so a fix only in an adapter would be invisible to
the manifest ``expected_code_digest`` / delta-skip guard; the direct-writer tests below fail without the writer-level fix.

Mutation proof (recorded in the commit message): reverting the adapter ``str(...)`` or the writer-level ``str(...)``
makes the matching tests fail; reverting both makes every UUID test fail with the ContractError above.
"""
from __future__ import annotations

import sys
import pathlib
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as gdw  # noqa: E402
from ga_writers import ga_tajaka_writer as gtw  # noqa: E402
from ga_writers.data_plane_contracts import ContractError, canonical_json  # noqa: E402
from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator.writers import (  # noqa: E402
    ContextSpec, SubStep, discover_all, get_writer,
)

# Synthetic chart: NOT the native's; birth values are an arbitrary mid-latitude date.
CHART_UUID = uuid.UUID('aaaaaaaa-1111-4222-8333-000000000009')
CHART_STR = str(CHART_UUID)
BUILD_ID = 'build-uuid-regression'
BIRTH = {
    'datetime_iso': '2011-02-06T11:00:00',
    'latitude_deg': 23.26,
    'longitude_deg': 77.41,
    'tz_offset_hours': 5.5,
    'place_name': 'synthetic',
    'subject_label': 'syn',
}


class _RecConn:
    """Recording stand-in for the orchestrator's psycopg connection (not psycopg-module: the
    L1 data-plane SQL wrapper stays off, exactly as in the other adapter-level tests)."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self.commits = 0

    def cursor(self):
        return self

    def execute(self, sql, *args, **kwargs):
        self.statements.append((sql, args))
        return self

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks = getattr(self, 'rollbacks', 0) + 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _ctx(chart_id, conn) -> ContextSpec:
    return ContextSpec(asset_id='x', build_id=BUILD_ID, db_conn=conn,
                       config={'chart_id': chart_id, 'birth_params': dict(BIRTH)})


def test_premise_canonical_json_rejects_a_uuid():
    """The guard is not weakened: a UUID is still refused, a str is accepted (convert at the boundary)."""
    with pytest.raises(ContractError, match="not canonical JSON"):
        canonical_json([CHART_UUID])
    assert canonical_json([CHART_STR]) == f'["{CHART_STR}"]'


# ── ga_dashas ─────────────────────────────────────────────────────────────────────

def _capture_dashas(monkeypatch):
    seen: dict = {'sentinel_rows': [], 'system_rows': [], 'chart_ids': []}

    def fake_upsert_rows(conn, rows, system_id, ayanamsha_id, *, commit=True):
        key = 'sentinel_rows' if system_id == 'scope_cap' else 'system_rows'
        seen[key].extend(dict(r) for r in rows)
        return len(rows)

    monkeypatch.setattr(gdw, '_upsert_rows', fake_upsert_rows)
    monkeypatch.setattr(gdw, '_run_concurrency_post_pass_db', lambda chart_id, build_id, *, conn=None:
                        seen['chart_ids'].append(('post_pass', chart_id)))
    monkeypatch.setattr(gdw, '_activate_natal_context', lambda chart_id, ayanamsha_id, conn:
                        seen['chart_ids'].append(('natal_context', chart_id)))
    monkeypatch.setattr(gdw, '_activate_karaka_roles', lambda chart_id, ayanamsha_id, conn:
                        seen['chart_ids'].append(('karaka_roles', chart_id)))
    monkeypatch.setattr(gdw, '_get_karaka_role', lambda chart_id, ayanamsha_id, lord: None)
    monkeypatch.setattr(gdw, '_get_karakas_active', lambda chart_id, ayanamsha_id, lord, parent=None: [])
    return seen


def _post_pass(monkeypatch, chart_id):
    discover_all()
    seen = _capture_dashas(monkeypatch)
    writer = get_writer('ga_dashas')()
    res = writer.run_substep(_ctx(chart_id, _RecConn()), SubStep(key='__concurrency_post_pass__'))
    return seen, res


def test_ga_dashas_post_pass_accepts_a_real_uuid_chart_id(monkeypatch):
    seen, res = _post_pass(monkeypatch, CHART_UUID)
    assert res.rows_inserted == 2
    assert [c for _, c in seen['chart_ids']] == [CHART_STR]
    assert all(type(c) is str for _, c in seen['chart_ids']), "writer must receive a str chart_id"
    assert len(seen['sentinel_rows']) == 1


def test_ga_dashas_post_pass_ids_equal_the_str_chart_id_ids(monkeypatch):
    from_uuid, _ = _post_pass(monkeypatch, CHART_UUID)
    from_str, _ = _post_pass(monkeypatch, CHART_STR)
    assert from_uuid['sentinel_rows'][0]['dasha_row_id'] == from_str['sentinel_rows'][0]['dasha_row_id']


@pytest.mark.parametrize('step_key', ['naisargika:lahiri_chitrapaksha', 'yogini:lahiri_chitrapaksha'])
def test_ga_dashas_substep_accepts_a_real_uuid_chart_id(monkeypatch, step_key):
    """The first-substep failure of the rehearsal: build_system -> stabilize_hierarchical_uuids
    (identity field ``chart_id``) -> stable_uuid -> canonical_json."""
    discover_all()
    def run(chart_id):
        seen = _capture_dashas(monkeypatch)
        writer = get_writer('ga_dashas')()
        res = writer.run_substep(_ctx(chart_id, _RecConn()), SubStep(key=step_key))
        return seen, res

    seen_u, res_u = run(CHART_UUID)
    seen_s, res_s = run(CHART_STR)
    assert res_u.rows_inserted == res_s.rows_inserted > 0
    assert {c for _, c in seen_u['chart_ids']} == {CHART_STR}
    assert all(type(r['chart_id']) is str for r in seen_u['system_rows'])
    ids_u = sorted((r['dasha_row_id'], r['parent_row_id'] or '') for r in seen_u['system_rows'])
    ids_s = sorted((r['dasha_row_id'], r['parent_row_id'] or '') for r in seen_s['system_rows'])
    assert ids_u == ids_s, "UUID5 identities must not depend on the chart_id's Python type"


# ── ga_tajaka ─────────────────────────────────────────────────────────────────────

def _run_tajaka(monkeypatch, chart_id):
    discover_all()
    monkeypatch.setattr(gtw, 'CANONICAL_AYANAMSHAS', {'lahiri_chitrapaksha': 'lahiri'})
    monkeypatch.setattr(gtw, '_effective_reference_year', lambda reference_year: 2012)
    monkeypatch.setattr(gtw, '_read_trirashipathi', lambda conn, cid, aya: None)
    monkeypatch.setattr(gtw, 'replace_prior_tajik_varsha', lambda conn, rows: 0)
    captured: list[dict] = []
    monkeypatch.setattr(gtw, '_insert_rows', lambda conn, rows: (captured.extend(dict(r) for r in rows), len(rows))[1])
    writer = get_writer('ga_tajaka')()
    res = writer.run(_ctx(chart_id, _RecConn()))
    return res, captured


def test_ga_tajaka_accepts_a_real_uuid_chart_id(monkeypatch):
    res, rows = _run_tajaka(monkeypatch, CHART_UUID)
    assert res.rows_inserted == len(rows) > 0
    assert all(type(r['chart_id']) is str and r['chart_id'] == CHART_STR for r in rows)


def test_ga_tajaka_ids_equal_the_str_chart_id_ids(monkeypatch):
    _, rows_u = _run_tajaka(monkeypatch, CHART_UUID)
    _, rows_s = _run_tajaka(monkeypatch, CHART_STR)
    assert [r['varsha_id'] for r in rows_u] == [r['varsha_id'] for r in rows_s]


# ── orchestrator driver level: the registered writer behind _run_data_writer ─────

class _FakeCur:
    def __init__(self) -> None:
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return []

    def fetchone(self):
        return None


def test_run_data_writer_drives_ga_tajaka_with_a_uuid_chart_id(monkeypatch):
    """ONE driver-level test: ``_run_data_writer`` (the function run_asset delegates to) builds the
    real ContextSpec from the chart_id it was given -- a uuid.UUID, as run["chart_id"] is -- and
    runs the REAL registered ga_tajaka adapter. The state it records must be 'lit', not 'error'."""
    discover_all()
    errors: list[str] = []
    captured: list[dict] = []
    monkeypatch.setattr(gtw, 'CANONICAL_AYANAMSHAS', {'lahiri_chitrapaksha': 'lahiri'})
    monkeypatch.setattr(gtw, '_effective_reference_year', lambda reference_year: 2012)
    monkeypatch.setattr(gtw, '_read_trirashipathi', lambda conn, cid, aya: None)
    monkeypatch.setattr(gtw, 'replace_prior_tajik_varsha', lambda conn, rows: 0)
    monkeypatch.setattr(gtw, '_insert_rows', lambda conn, rows: (captured.extend(dict(r) for r in rows), len(rows))[1])
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)
    monkeypatch.setattr(ar, 'fetch_birth_params', lambda conn, cid: dict(BIRTH))
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, aid, cid: 'hash-upstream')
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda aid: 'hash-writer')
    monkeypatch.setattr(ar, 'compute_downstream_closure', lambda cur, aid: [])
    monkeypatch.setattr(ar, 'mark_asset_error',
                        lambda conn, cur, run, chart, asset, error: errors.append(error))

    class _Conn(_RecConn):
        pass

    ok = ar._run_data_writer(_Conn(), _FakeCur(), BUILD_ID, CHART_UUID, 'ga_tajaka')
    assert errors == []
    assert ok is True
    assert captured, "the adapter must have produced rows"


# ── the writer entry points themselves (digest-bound fix, independent of the adapters) ─────────────

def test_write_dasha_scope_cap_sentinels_accepts_a_real_uuid_directly(monkeypatch):
    seen = _capture_dashas(monkeypatch)
    n = gdw.write_dasha_scope_cap_sentinels(CHART_UUID, BUILD_ID, conn=_RecConn())
    seen_str = _capture_dashas(monkeypatch)
    gdw.write_dasha_scope_cap_sentinels(CHART_STR, BUILD_ID, conn=_RecConn())
    assert n == 2 and seen['sentinel_rows'][0]['chart_id'] == CHART_STR and type(seen['sentinel_rows'][0]['chart_id']) is str
    assert seen['sentinel_rows'][0]['dasha_row_id'] == seen_str['sentinel_rows'][0]['dasha_row_id']


@pytest.mark.parametrize('system', ['naisargika', 'yogini'])
def test_build_system_accepts_a_real_uuid_directly(monkeypatch, system):
    seen = _capture_dashas(monkeypatch)
    res = gdw.build_system(system, 'lahiri_chitrapaksha', CHART_UUID, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH))
    seen_str = _capture_dashas(monkeypatch)
    res_s = gdw.build_system(system, 'lahiri_chitrapaksha', CHART_STR, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH))
    assert res['rows_written'] == res_s['rows_written'] > 0
    assert all(type(r['chart_id']) is str for r in seen['system_rows'])
    assert sorted(r['dasha_row_id'] for r in seen['system_rows']) == sorted(r['dasha_row_id'] for r in seen_str['system_rows'])


def test_build_ga_tajaka_accepts_a_real_uuid_directly(monkeypatch):
    def run(chart_id):
        monkeypatch.setattr(gtw, 'CANONICAL_AYANAMSHAS', {'lahiri_chitrapaksha': 'lahiri'})
        monkeypatch.setattr(gtw, '_read_trirashipathi', lambda conn, cid, aya: None)
        monkeypatch.setattr(gtw, 'replace_prior_tajik_varsha', lambda conn, rows: 0)
        captured: list[dict] = []
        monkeypatch.setattr(gtw, '_insert_rows', lambda conn, rows: (captured.extend(dict(r) for r in rows), len(rows))[1])
        summary = gtw.build_ga_tajaka(chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH), reference_year=2012)
        return summary, captured
    s_u, rows_u = run(CHART_UUID)
    s_s, rows_s = run(CHART_STR)
    assert s_u['chart_id'] == CHART_STR and type(s_u['chart_id']) is str and s_u['total_rows_written'] == s_s['total_rows_written'] > 0
    assert [r['varsha_id'] for r in rows_u] == [r['varsha_id'] for r in rows_s]


def test_the_ga_tajaka_adapter_hands_the_writer_a_str(monkeypatch):
    """The adapter-level half of the fix (the rows' chart_id is a str either way because the writer normalises too)."""
    discover_all()
    handed: list[object] = []
    real = gtw.build_ga_tajaka

    def spy(chart_id, *a, **kw):
        handed.append(chart_id)
        return real(chart_id, *a, **kw)

    monkeypatch.setattr(gtw, 'build_ga_tajaka', spy)
    monkeypatch.setattr(gtw, 'CANONICAL_AYANAMSHAS', {'lahiri_chitrapaksha': 'lahiri'})
    monkeypatch.setattr(gtw, '_effective_reference_year', lambda reference_year: 2012)
    monkeypatch.setattr(gtw, '_read_trirashipathi', lambda conn, cid, aya: None)
    monkeypatch.setattr(gtw, 'replace_prior_tajik_varsha', lambda conn, rows: 0)
    monkeypatch.setattr(gtw, '_insert_rows', lambda conn, rows: len(rows))
    get_writer('ga_tajaka')().run(_ctx(CHART_UUID, _RecConn()))
    assert handed == [CHART_STR] and type(handed[0]) is str
