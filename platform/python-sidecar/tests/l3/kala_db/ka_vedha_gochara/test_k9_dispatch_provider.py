"""SR-K9-PUBLISHABLE D2: ka_vedha_gochara is live under orchestrator dispatch.

The runner hands a writer `chart_id` + `birth_params` only (asset_runner.py
`ContextSpec(config=...)`), so every case below builds its context exactly so
and drives the writer through the REAL `_drive_substeps`. Claims:

  1. dispatch writes the candidate headers/intervals and attests its three
     family grains under the CANDIDATE generation (publication.py:52-68);
  2. the derived residence is the sky's: contiguous over the horizon and the
     first sign equals an independent Swiss (Lahiri, mean node) sidereal sign
     at the horizon start (B.3: rasi = floor(sidereal longitude / 30) + 1);
  3. a build bound to no candidate stays inert (no legacy mutation);
  4. an unanswerable sky is typed absence: unsearched headers, zero_rows
     grains - never a clean "no vedha" (N.7.6 / B.10).

Sky-dependent cases need the pinned Swiss corpus (SE_EPHE_PATH).
"""
from datetime import date, timedelta
import os

import pytest
import swisseph as swe

from pipeline.orchestrator.asset_runner import _drive_substeps
from pipeline.orchestrator.writers import ContextSpec
from services.ka_vedha_gochara import provider
from services.ka_vedha_gochara.writer import (
    HORIZON_BACK_DAYS, HORIZON_FORWARD_DAYS, KaVedhaGocharaWriter)
from services.kala_core.sky import SkyConvention
from tests.l3.kala_db.ka_vedha_gochara.conftest import BUILD, CHART, NATAL

KINDS = ('house_vedha', 'latta', 'sarvatobhadra')
AYANAMSHA = 'lahiri_chitrapaksha'


def dispatch(conn, build=BUILD):
    conn.execute('CREATE TABLE IF NOT EXISTS asset_throughput '
                 '(chart_id uuid, asset_id text, last_built_at timestamptz, rows_written integer)')
    ctx = ContextSpec(asset_id='ka_vedha_gochara', build_id=build, db_conn=conn,
                      config={'chart_id': CHART, 'birth_params': {}})
    with conn.cursor() as cur:
        return _drive_substeps(conn, cur, build, CHART, 'ka_vedha_gochara',
                               KaVedhaGocharaWriter(), ctx, defer_commits=True)


def grains(conn):
    return dict(conn.execute('SELECT grain_key, result_state FROM kala_layer_candidate_grain '
                             "WHERE chart_id = %s AND generation = 'candidate-1'", (CHART,)).fetchall())


def test_dispatch_writes_headers_and_attests_all_family_grains_under_the_candidate(conn):
    legacy = conn.execute('SELECT to_jsonb(t) FROM kala_vedha_gochara t').fetchall()
    rows, _, _ = dispatch(conn)
    headers = conn.execute("SELECT vedha_kind FROM kala_vedha_gochara_candidate WHERE generation = 'candidate-1' "
                           'ORDER BY vedha_kind').fetchall()
    assert [h[0] for h in headers] == list(KINDS)
    assert set(grains(conn)) == {f'ka_vedha_gochara:{AYANAMSHA}:{k}' for k in KINDS}
    assert set(grains(conn).values()) <= {'rows', 'zero_rows'}
    intervals = conn.execute("SELECT count(*) FROM kala_vedha_gochara_interval WHERE generation = 'candidate-1'").fetchone()[0]
    assert rows == intervals + 3 and rows > 0, 'headers count as written rows: never a dormant no-op'
    assert conn.execute('SELECT to_jsonb(t) FROM kala_vedha_gochara t').fetchall() == legacy


def independent_sidereal_sign(body, jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    lon = swe.calc_ut(jd, {'Sun': swe.SUN, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
                           'Venus': swe.VENUS, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE,
                           'Ketu': swe.MEAN_NODE}[body], flags)[0][0]
    lon = (lon + 180.0) % 360.0 if body == 'Ketu' else lon
    return int(lon // 30) + 1


def test_residence_is_the_skys_over_the_whole_horizon():
    today = date.today()
    start, end = today - timedelta(days=HORIZON_BACK_DAYS), today + timedelta(days=HORIZON_FORWARD_DAYS)
    horizon = (provider._noon(start), provider._noon(end))
    residence, coverage = provider._residences(
        provider.HOUSE_BODIES, 'sign_ingress', horizon, start, end, SkyConvention(), os.environ['SE_EPHE_PATH'])
    assert coverage.complete and coverage.covered == horizon
    for body, spans in residence.items():
        assert spans, body
        assert spans[0][0] == independent_sidereal_sign(body, horizon[0]), body
        assert all(a[2] == b[1] for a, b in zip(spans, spans[1:])), f'{body}: residence has a gap'
        assert all((b[0] - a[0]) % 12 in (1, 11) for a, b in zip(spans, spans[1:])), f'{body}: sign skipped'


def test_build_bound_to_no_candidate_stays_inert(conn):
    before = conn.execute('SELECT to_jsonb(t) FROM kala_vedha_gochara t').fetchall()
    assert dispatch(conn, build=NATAL)[0] == 0
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone()[0] == 0
    assert conn.execute('SELECT count(*) FROM kala_layer_candidate_grain').fetchone()[0] == 0
    assert conn.execute('SELECT to_jsonb(t) FROM kala_vedha_gochara t').fetchall() == before


def test_unanswerable_sky_is_unsearched_never_clean(conn, monkeypatch, tmp_path):
    # An ephemeris directory with no corpus: Swiss falls back to Moshier, which
    # the kernel refuses, so the sky cannot answer any instant.
    pinned = os.environ['SE_EPHE_PATH']
    monkeypatch.setenv('SE_EPHE_PATH', str(tmp_path))
    try:
        dispatch(conn)
    finally:
        swe.set_ephe_path(pinned)
    assert set(grains(conn).values()) == {'zero_rows'}
    states = conn.execute("SELECT DISTINCT coverage->>'search_state', null_reason FROM kala_vedha_gochara_candidate "
                          "WHERE generation = 'candidate-1'").fetchall()
    assert states == [('unsearched', 'information_unavailable')]
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_interval').fetchone()[0] == 0
