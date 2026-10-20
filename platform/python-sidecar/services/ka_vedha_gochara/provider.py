"""Writer-side vedha provider (SR-K9-PUBLISHABLE D2; closes the SR-A4-01 follow-on).

Under orchestrator dispatch the runner hands a writer `chart_id` and
`birth_params` only (asset_runner.py: `ContextSpec.config`), so the typed
`VedhaPayload` cannot arrive through config. This provider derives it from what
the writer legitimately owns: the build's candidate row (generation + natal
pin), the database (natal Moon fact, L0 pair and latta authorities) and the
sky seam (`kala_core.sky`, pinned Swiss corpus). It adds no computation: it
only gathers the typed inputs `candidate.build_candidate_payload` already
consumes, with the sky's own coverage, so a horizon the sky cannot answer is
`unsearched` (typed null), never a clean "no vedha".

The horizon is the writer's historical scan window around `now_date`
(HORIZON_BACK_DAYS / HORIZON_FORWARD_DAYS), anchored at noon UT.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

import swisseph as swe
from psycopg.rows import dict_row, tuple_row

from services.gochara_kernel.arcs import ArcIndex
from services.gochara_kernel.knots import EphemerisBackendError
from services.gochara_kernel.lifecycle import ArcIndexRegistry
from services.ka_vedha_gochara.candidate import VedhaPayload, build_candidate_payload
from services.ka_vedha_gochara.writer import HORIZON_BACK_DAYS, HORIZON_FORWARD_DAYS, _config_horizon_date
from services.kala_core.manifest import Candidate
from services.kala_core.overlays import sky_residences
from services.kala_core.sky import SkyConvention, boundary_events, coverage_of, ephemeris_at
from services.kala_core.sky.events import REFINED_BACKEND

SUBSTRATE_VERSION = 'ka_vedha_provider/1'
# House-vedha obstructors/primaries; the Moon is on-demand testimony, never stored.
HOUSE_BODIES = ('Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu')

_MOON_SQL = ("SELECT fact_id, fact_value_num FROM chart_facts WHERE chart_id = %s AND build_id = %s "
             "AND ayanamsha_id = %s AND fact_category = 'graha_position' AND fact_subject = 'MOON' "
             "AND fact_key = 'longitude_sidereal' ORDER BY fact_id")
# Identical read sets to storage.replace_candidate's source pins.
_PAIRS_SQL = ("SELECT graha, primary_house, vedha_house, classical_citation, rule_type "
              "FROM bg_transit_rules WHERE vedha_house IS NOT NULL")
_LATTA_SQL = "SELECT graha, count_from_graha, direction, source_citation, verse_ref FROM bg_phaladeepika_latta"


def _noon(day: date) -> float:
    return float(swe.julday(day.year, day.month, day.day, 12.0))


def _residences(bodies, relation, horizon, start: date, end: date, convention: SkyConvention,
                ephe_path: str | None):
    """({body: spans}, coverage) from the sky seam; an unanswerable sky is typed absent."""
    registry = ArcIndexRegistry(ephe_path=ephe_path)
    out: dict[str, tuple] = {}
    coverage = None
    for body in bodies:
        try:
            # One day of margin each side keeps the requested interval inside the knot domain.
            index: ArcIndex = registry.get(body, SUBSTRATE_VERSION, start - timedelta(days=1),
                                           end + timedelta(days=1))
        except (EphemerisBackendError, RuntimeError):
            body_cov = coverage_of(horizon, None, backend=REFINED_BACKEND, convention_id=convention.convention_id)
            coverage = coverage or body_cov
            out[body] = ()
            continue
        events = boundary_events(index, body, (relation,), horizon, convention.convention_id,
                                 ephe_path=ephe_path)
        initial = ephemeris_at(horizon[0], convention, ephe_path=ephe_path)
        coverage = coverage or events.coverage
        out[body] = sky_residences(events, initial, body, relation)
    return out, coverage


def derive_payload(ctx: Any, candidate: Candidate, *, ephe_path: str | None = None) -> VedhaPayload:
    """The typed payload for this build's candidate, from config + database + sky only.

    The sky corpus is the pinned `SE_EPHE_PATH`; without it the Swiss seam falls
    back to Moshier, which the kernel refuses, and the horizon is typed absent.
    """
    ephe_path = ephe_path if ephe_path is not None else os.environ.get('SE_EPHE_PATH')
    conn = ctx.db_conn
    chart = str(ctx.config['chart_id'])
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SELECT conventions FROM kala_layer_candidate WHERE chart_id = %s AND generation = %s '
                    'AND build_id = %s', (chart, candidate.generation, candidate.build_id))
        row = cur.fetchone()
        pin = ((row or {}).get('conventions') or {}).get('natal') or {}
        if not pin.get('build_id') or not pin.get('ayanamsha_id'):
            raise ValueError('candidate natal build/ayanamsha pin required')
        cur.execute(_MOON_SQL, (chart, pin['build_id'], pin['ayanamsha_id']))
        facts = cur.fetchall()
        if len(facts) > 1:
            raise ValueError('contradictory natal Moon facts')
        janma = facts[0] if facts else None
        cur.execute(_LATTA_SQL)
        latta = [dict(r) for r in cur.fetchall()]
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(_PAIRS_SQL)
        pairs_rows = [list(r) for r in cur.fetchall()]

    today = _config_horizon_date(ctx.config.get('now_date')) or date.today()
    start, end = today - timedelta(days=HORIZON_BACK_DAYS), today + timedelta(days=HORIZON_FORWARD_DAYS)
    horizon = (_noon(start), _noon(end))
    convention = SkyConvention(ayanamsha_id=pin['ayanamsha_id'])

    residence, coverage = _residences(HOUSE_BODIES, 'sign_ingress', horizon, start, end, convention, ephe_path)
    latta_bodies = tuple(r['graha'] for r in latta if r['graha'] in
                         ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu'))
    nakshatra, nak_coverage = _residences(latta_bodies, 'nakshatra_ingress', horizon, start, end,
                                          convention, ephe_path)
    coverage = coverage or nak_coverage or coverage_of(horizon, None, backend=REFINED_BACKEND,
                                                      convention_id=convention.convention_id)
    return build_candidate_payload(
        chart_id=chart, generation=candidate.generation, ayanamsha_id=pin['ayanamsha_id'],
        natal_build_id=pin['build_id'], janma_fact=janma, coverage=coverage, residence=residence,
        pairs_rows=pairs_rows, nakshatra_residence=nakshatra, latta_rules=latta, enrichment=None)


__all__ = ['HOUSE_BODIES', 'SUBSTRATE_VERSION', 'derive_payload']
