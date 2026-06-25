"""Orchestrator Convergence Phase 3 — GA writer conformance to the frozen contract.

Proves the 9 L1 Gaṇita writers are orchestrator-native:
  A. all 9 register and resolve via get_writer (discoverable);
  B. each adapter threads ctx.db_conn / chart_id / build_id into its writer
     (connection ownership inverted to the caller);
  C. heavy writers expose sub-steps (ga_dashas 35 chunks + post-pass; ga_vargas
     per-ayanamsha);
  D. on an INJECTED connection a writer does NOT commit, does NOT close, and does
     NOT write asset_throughput (proven on ga_positions, the canonical light
     writer; the 6 other light writers share the identical owns_conn pattern); on
     an OWNED connection it commits (legacy CLI path preserved).
"""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.writers import (  # noqa: E402
    discover_all, get_writer, ContextSpec, WriterResult, SubStep,
)

ALL_GA = [
    'ga_positions', 'ga_strength', 'ga_panchanga', 'ga_sensitive',
    'ga_structural', 'ga_sade_sati', 'ga_tajaka', 'ga_vargas', 'ga_dashas',
]
HEAVY = {'ga_dashas', 'ga_vargas', 'ga_structural', 'ga_sensitive'}


class _Sentinel:
    """Stands in for ctx.db_conn — identity-checked, never used as a real conn."""


def _ctx(conn):
    return ContextSpec(asset_id='x', build_id='build-XYZ', db_conn=conn,
                       config={'chart_id': 'chart-C'})


# ── A. Discovery ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('asset_id', ALL_GA)
def test_all_ga_writers_resolve(asset_id):
    discover_all()
    cls = get_writer(asset_id)
    assert cls is not None, f'{asset_id} not registered'
    assert cls.asset_id == asset_id
    # provenance points at the real ga_writers/ module, not the adapter
    assert cls.source_paths and 'ga_writers/' in cls.source_paths[0]


@pytest.mark.parametrize('asset_id', ALL_GA)
def test_has_substeps_flag(asset_id):
    cls = get_writer(asset_id)
    assert bool(getattr(cls, 'has_substeps', False)) is (asset_id in HEAVY)


# ── C. Heavy sub-step plans ──────────────────────────────────────────────────────

def test_ga_dashas_plan_is_35_chunks_plus_postpass():
    steps = get_writer('ga_dashas')().plan_substeps(_ctx(_Sentinel()))
    assert len(steps) == 36                     # 7 systems × 5 ayanamshas + post-pass
    assert steps[-1].key == '__concurrency_post_pass__'
    assert all(isinstance(s, SubStep) for s in steps)


def test_ga_vargas_plan_is_per_ayanamsha():
    steps = get_writer('ga_vargas')().plan_substeps(_ctx(_Sentinel()))
    assert len(steps) == 5                       # 5 canonical ayanamshas
    assert all(isinstance(s, SubStep) for s in steps)


# ── B. Adapter threads ctx.db_conn into the writer ──────────────────────────────

_LIGHT_FN = {
    'ga_positions':  ('ga_writers.ga_positions_writer',  'build_ga_positions'),
    'ga_strength':   ('ga_writers.ga_strength_writer',   'build_ga_strength'),
    'ga_panchanga':  ('ga_writers.ga_panchanga_writer',  'build_ga_panchanga'),
    'ga_sade_sati':  ('ga_writers.ga_sade_sati_writer',  'build_ga_sade_sati'),
    'ga_tajaka':     ('ga_writers.ga_tajaka_writer',     'build_ga_tajaka'),
}


@pytest.mark.parametrize('asset_id', list(_LIGHT_FN))
def test_light_adapter_threads_injected_conn(asset_id, monkeypatch):
    import importlib
    mod_name, fn_name = _LIGHT_FN[asset_id]
    mod = importlib.import_module(mod_name)
    seen = {}

    def stub(*, chart_id, build_id, conn, **kw):
        seen.update(chart_id=chart_id, build_id=build_id, conn=conn)
        return {'total_chart_facts_rows': 7,
                'total_rows': 7, 'inserted_rows': 7, 'total_rows_written': 7}

    monkeypatch.setattr(mod, fn_name, stub)
    sentinel = _Sentinel()
    res = get_writer(asset_id)().run(_ctx(sentinel))

    assert seen['conn'] is sentinel          # ctx.db_conn flows to the writer
    assert seen['chart_id'] == 'chart-C'
    assert seen['build_id'] == 'build-XYZ'
    assert isinstance(res, WriterResult)
    assert res.asset_id == asset_id


def test_ga_dashas_substep_threads_injected_conn(monkeypatch):
    import ga_writers.ga_dashas_writer as gdw
    seen = {}

    def stub_build_system(system, aya, chart_id, build_id, *, conn=None, **kw):
        seen.update(system=system, aya=aya, chart_id=chart_id,
                    build_id=build_id, conn=conn)
        return {'rows_written': 11}

    monkeypatch.setattr(gdw, 'build_system', stub_build_system)
    sentinel = _Sentinel()
    w = get_writer('ga_dashas')()
    res = w.run_substep(_ctx(sentinel), SubStep(key='vimshottari:lahiri_chitrapaksha'))

    assert seen['conn'] is sentinel
    assert seen['system'] == 'vimshottari'
    assert seen['aya'] == 'lahiri_chitrapaksha'
    assert res.rows_inserted == 11


def test_ga_vargas_substep_threads_injected_conn(monkeypatch):
    import ga_writers.ga_vargas_writer as gvw
    seen = {}

    def stub(*, chart_id, build_id, conn, ayanamsha_subset, **kw):
        seen.update(chart_id=chart_id, build_id=build_id, conn=conn,
                    subset=ayanamsha_subset)
        return {'total_rows_written': 99}

    monkeypatch.setattr(gvw, 'build_ga_vargas', stub)
    sentinel = _Sentinel()
    res = get_writer('ga_vargas')().run_substep(_ctx(sentinel), SubStep(key='lahiri'))

    assert seen['conn'] is sentinel
    assert seen['subset'] == ['lahiri']
    assert res.rows_inserted == 99


def test_ga_structural_plan_is_per_ayanamsha():
    steps = get_writer('ga_structural')().plan_substeps(_ctx(_Sentinel()))
    assert len(steps) == 5                       # 5 canonical ayanamshas
    assert all(isinstance(s, SubStep) for s in steps)
    assert all(s.key.startswith('ayanamsha_') for s in steps)


def test_ga_structural_substep_threads_injected_conn(monkeypatch):
    import ga_writers.ga_structural_writer as gsw
    seen = {}

    def stub(*, chart_id, build_id, ayanamsha_id, conn, **kw):
        seen.update(chart_id=chart_id, build_id=build_id, conn=conn,
                    ayanamsha_id=ayanamsha_id)
        return 42

    monkeypatch.setattr(gsw, 'build_ga_structural_substep', stub)
    sentinel = _Sentinel()
    res = get_writer('ga_structural')().run_substep(
        _ctx(sentinel), SubStep(key='ayanamsha_lahiri')
    )

    assert seen['conn'] is sentinel
    assert seen['ayanamsha_id'] == 'lahiri'
    assert res.rows_inserted == 42


def test_ga_sensitive_plan_is_per_ayanamsha():
    steps = get_writer('ga_sensitive')().plan_substeps(_ctx(_Sentinel()))
    assert len(steps) == 5                       # 5 canonical ayanamshas
    assert all(isinstance(s, SubStep) for s in steps)
    assert all(s.key.startswith('ayanamsha:') for s in steps)


def test_ga_sensitive_substep_threads_injected_conn(monkeypatch):
    import ga_writers.ga_sensitive_writer as gsw
    seen = {}

    def stub_ctx(birth_params, conn=None):
        return ({'G14_SAHAM': True, 'G41_LAL_KITAB': False, 'G44_NADI': False},
                'pyjhora/1.0.0')

    def stub_build(*, ayanamsha_key, ayanamsha_id, chart_id, build_id, conn,
                   birth_params, prereqs, eng_ver):
        seen.update(ayanamsha_key=ayanamsha_key, chart_id=chart_id,
                    build_id=build_id, conn=conn)
        return 1722

    monkeypatch.setattr(gsw, 'get_ga_sensitive_context', stub_ctx)
    monkeypatch.setattr(gsw, 'build_ga_sensitive_for_ayanamsha', stub_build)
    sentinel = _Sentinel()
    res = get_writer('ga_sensitive')().run_substep(
        _ctx(sentinel), SubStep(key='ayanamsha:lahiri_chitrapaksha')
    )

    assert seen['conn'] is sentinel
    assert seen['ayanamsha_key'] == 'lahiri_chitrapaksha'
    assert seen['chart_id'] == 'chart-C'
    assert res.rows_inserted == 1722


# ── D. Injected conn ⇒ no commit / no close / no telemetry (ga_positions) ────────

class _RecordingConn:
    def __init__(self):
        self.commits = 0
        self.closed = False

    # context-manager so it can stand in for _conn() on the owned path
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.closed = True
        return False

    def commit(self):
        self.commits += 1


def _neuter_positions_compute(monkeypatch):
    import ga_writers.ga_positions_writer as gpw
    monkeypatch.setattr(gpw, 'compute_chart', lambda inputs, ayanamsha_id: {})
    monkeypatch.setattr(gpw, 'forensic_gate', lambda *a, **k: None)
    monkeypatch.setattr(gpw, '_build_position_rows', lambda *a, **k: [])
    monkeypatch.setattr(gpw, '_insert_chart_facts_rows', lambda *a, **k: 0)
    telem = {'n': 0}
    monkeypatch.setattr(gpw, '_update_asset_throughput',
                        lambda **k: telem.__setitem__('n', telem['n'] + 1))
    return gpw, telem


# Minimal NATIVE_BIRTH-shaped dict for non-native build paths in these tests.
_DUMMY_BIRTH = {
    "datetime_iso": "1990-06-15T14:30:00",
    "latitude_deg": 12.97,
    "longitude_deg": 77.59,
    "tz_offset_hours": 5.5,
    "place_name": "Test City",
    "subject_label": "Test Subject",
}


def test_non_native_without_birth_params_refuses_native_fallback(monkeypatch):
    """Contamination guard: a non-native chart_id with no birth_params must raise,
    never silently build the native (the ga_positions contamination bug)."""
    gpw, _ = _neuter_positions_compute(monkeypatch)
    conn = _RecordingConn()
    import pytest
    with pytest.raises(ValueError, match="refusing to fall back to NATIVE_BIRTH"):
        gpw.build_ga_positions(chart_id='some-non-native-uuid', build_id='b', conn=conn)


def test_native_without_birth_params_uses_native_default(monkeypatch):
    """The native chart_id is still allowed to use NATIVE_BIRTH when no birth_params
    are passed (it is the FORENSIC-guarded ground-truth chart)."""
    gpw, _ = _neuter_positions_compute(monkeypatch)
    conn = _RecordingConn()
    # Must NOT raise; native default permitted.
    gpw.build_ga_positions(chart_id=gpw.CANONICAL_CHART_ID, build_id='b', conn=conn)


def test_injected_conn_does_not_commit_close_or_write_throughput(monkeypatch):
    gpw, telem = _neuter_positions_compute(monkeypatch)
    conn = _RecordingConn()
    # Non-native chart_id requires explicit birth_params (post-contamination-fix:
    # the writer refuses to fall back to NATIVE_BIRTH for a non-native chart).
    gpw.build_ga_positions(chart_id='chart-C', build_id='b', conn=conn,
                           birth_params=_DUMMY_BIRTH)
    assert conn.commits == 0          # orchestrator owns the commit
    assert conn.closed is False       # caller owns the connection
    assert telem['n'] == 0            # orchestrator is the sole throughput writer


def test_owned_conn_commits_and_writes_throughput(monkeypatch):
    gpw, telem = _neuter_positions_compute(monkeypatch)
    owned = _RecordingConn()
    monkeypatch.setattr(gpw, '_conn', lambda: owned)   # legacy CLI path opens its own
    gpw.build_ga_positions(chart_id='chart-C', build_id='b',  # conn=None
                           birth_params=_DUMMY_BIRTH)
    assert owned.commits == 1         # legacy path commits
    assert telem['n'] == 1            # legacy path writes throughput
