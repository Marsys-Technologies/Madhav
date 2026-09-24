"""
GocharaTransitService — wraps transit-search functions for use by routers.

MR-09 NAMING NOTE: This module lives at services/ka_gochara/service.py and
its primary class is GocharaTransitService (renamed from KaGocharaService at
MR-09 to resolve the naming collision with the ka_gochara materializer writer
at pipeline/orchestrator/writers/ka_gochara.py).

The two things that share the "ka_gochara" prefix are DISTINCT:
  - This module (GocharaTransitService): a LIVE TRANSIT COMPUTATION ENGINE.
    Wraps Swiss-Ephemeris functions (pipeline.transit_search) to search for
    aspect, ingress, conjunction, station, and other transit events on demand.
    No DB table; no @register; no WriterBase.  Asset kind = 'service'.
  - pipeline/orchestrator/writers/ka_gochara.py (KaGocharaWriter): a PER-CHART
    DATA MATERIALIZER.  @register('ka_gochara') WriterBase subclass that joins
    bg_gochara_arcs against a chart's gochara_resonance_map and writes
    generation='2.0' rows into kala_gochara_windows_v2.

KaGocharaService is retained as a backward-compat alias (see bottom of module)
so existing callers (ka_sangam.py and tests) continue to work without change.

Thin orchestration layer over pipeline.transit_search. All numeric computation
happens in the pipeline module; this class handles dependency injection (swe).

WP7 S-1/S-2: `find_episodes` serves kernel episodes from the contact ledger
(`kala_gochara_contacts`) with F06-honest coverage, plus Moon-on-demand live
solving via the gochara_kernel (contact_id=None, `moon_on_demand` coverage
partition). `find_aspects` and every legacy method keep their exact shapes —
the four duck-typed call sites (kala_trigger/trigger.py:96,150,199,
ka_sangam/engine.py:464, scripts/kala_admission/currents.py:59) are untouched.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from pipeline.transit_search import (
    TransitEvent,
    find_aspect_events,
    find_conjunction_events,
    find_ingress_events,
    find_return_events,
    find_station_events,
    find_eclipse_proximity_events,
    find_multi_planet_confluence_events,
    find_transit_to_transit_events,
    search_long_horizon,
)

logger = logging.getLogger(__name__)

# J2000.0 epoch as a fixed reference point for the health probe computation.
# Using a well-known epoch (2000-01-01 12:00 UT) means any correct swe
# implementation returns a deterministic result — this is a connectivity /
# smoke test for the ephemeris, not an astronomical assertion.
_HEALTH_PROBE_JD = 2451545.0  # J2000.0

# WP1 §3.1 relation vocabulary.
EPISODE_RELATIONS = (
    'conjunction', 'drishti_contact', 'sign_ingress',
    'nakshatra_ingress', 'kakshya_cell_crossing', 'return',
)

# N-14 (RULED): Rāhu/Ketu cast no dṛṣṭi — not the 7th. They stay full agents
# and targets for every other relation.
N14_DRISHTI_EXCLUDED_BODIES = frozenset({'Rahu', 'Ketu'})

_BOUNDARY_RELATIONS = ('sign_ingress', 'nakshatra_ingress', 'kakshya_cell_crossing')

# Orb-table row per relation for the Moon on-demand path (WP1 §7).
_MOON_ORB_SOURCE = {
    'conjunction': 'orb_conj_moon',
    'drishti_contact': 'orb_drishti_moon',
    'return': 'orb_return_moon',
    'kakshya_cell_crossing': 'orb_kakshya',
    'sign_ingress': 'orb_ingress',
    'nakshatra_ingress': 'orb_ingress',
}


@dataclass(frozen=True)
class TargetRef:
    """One episode target (WP7 S-1 §2). `longitude_deg` is required only by
    the Moon on-demand live-solve path (the WP1 §2.2 resolution contract is
    the caller's job; targets without a longitude are reported unresolved in
    the moon_on_demand coverage, never silently solved)."""
    target_type: str
    target_ref: str
    target_fact_id: str | None = None
    longitude_deg: float | None = None


@dataclass(frozen=True)
class Horizon:
    start_jd: float
    end_jd: float


@dataclass(frozen=True)
class GocharaEpisode:
    """The unit the ledger persists (WP7 S-1 §2). `contact_id` is None only
    for live-computed (non-persisted, Moon on-demand) episodes.
    `target_longitude_deg` is additive over the packet interface: the ledger
    carries it as a reference copy and Saṅgam's aggregated form needs it."""
    contact_id: str | None
    independence_group: str
    body: str
    relation: str
    aspect_deg: float | None
    target_type: str
    target_ref: str
    target_resolution_state: str
    t_in: str
    t_exact: str | None
    t_out: str
    branch: str
    truncated_at_horizon: str | None
    completeness_state: str
    claim_grain: str
    convention_id: str
    target_longitude_deg: float | None = None


@dataclass(frozen=True)
class EpisodeCoverage:
    partition_kind: str          # 'body_target' | 'event_class' | 'moon_on_demand'
    partition_key: str
    requested_horizon: str       # tstzrange text
    completed_horizon: str
    relations_searched: list
    targets_requested: int
    targets_resolved: int
    targets_unresolved: int
    target_resolution_state_counts: dict
    unavailable_inputs: dict = field(default_factory=dict)
    unsearched_reason: str | None = None


@dataclass(frozen=True)
class EpisodeBatch:
    episodes: list
    coverage: list               # one per partition searched, incl. moon_on_demand


def _jd_to_iso(swe, jd: float) -> str:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hour = int(h)
    minute_f = (h - hour) * 60.0
    minute = int(minute_f)
    second = (minute_f - minute) * 60.0
    dt = datetime(y, m, d, hour, minute, tzinfo=timezone.utc) + timedelta(seconds=second)
    return dt.isoformat().replace('+00:00', 'Z')


def _jd_to_date(swe, jd: float):
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return datetime(y, m, d, tzinfo=timezone.utc).date()


class GocharaTransitService:
    """Live transit computation engine wrapping Swiss-Ephemeris functions.

    MR-09: renamed from KaGocharaService to avoid ambiguity with the
    'ka_gochara' materializer writer (pipeline/orchestrator/writers/ka_gochara.py).
    KaGocharaService is kept as a backward-compat alias at the bottom of this
    module.
    """

    def __init__(self, swe, ephe_path: str | None = None):
        self.swe = swe
        # Optional .se1 directory for the gochara_kernel Moon on-demand path
        # (find_episodes(moon=True)). Additive kwarg — the duck-typed
        # find_aspects contract and all legacy call sites are unaffected.
        self._ephe_path = ephe_path

    def find_aspects(
        self,
        transit_planet: str,
        target_lon: float,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_aspect_events(self.swe, transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd)

    def find_conjunctions(
        self,
        planet_a: str,
        planet_b: str,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_conjunction_events(self.swe, planet_a, planet_b, orb, start_jd, end_jd)

    def find_ingresses(
        self,
        planet: str,
        target_sign: str,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_ingress_events(self.swe, planet, target_sign, start_jd, end_jd)

    def find_returns(
        self,
        planet: str,
        natal_lon: float,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_return_events(self.swe, planet, natal_lon, orb, start_jd, end_jd)

    def find_stations(
        self,
        planet: str,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_station_events(self.swe, planet, start_jd, end_jd)

    def find_eclipse_proximity(
        self,
        node_planet: str,
        luminary: str,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_eclipse_proximity_events(self.swe, node_planet, luminary, orb, start_jd, end_jd)

    def find_multi_planet_confluence(
        self,
        planets: list,
        target_lon: float,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_multi_planet_confluence_events(
            self.swe, planets, target_lon, aspect_degrees, orb, start_jd, end_jd
        )

    def find_transit_to_transit(
        self,
        planet_a: str,
        planet_b: str,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
    ) -> list[TransitEvent]:
        return find_transit_to_transit_events(
            self.swe, planet_a, planet_b, aspect_degrees, orb, start_jd, end_jd
        )

    def long_horizon_search(
        self,
        transit_planet: str,
        target_lon: float,
        aspect_degrees: list,
        orb: float,
        start_jd: float,
        end_jd: float,
        region_tile_days: int = 365,
    ) -> list[TransitEvent]:
        return search_long_horizon(
            self.swe, transit_planet, target_lon, aspect_degrees, orb,
            start_jd, end_jd, region_tile_days,
        )

    # ── WP7 S-1/S-2: episode serving ─────────────────────────────────────────

    def find_episodes(
        self,
        conn,
        chart_id: str,
        targets: list,
        horizon: Horizon,
        *,
        bodies: list | None = None,
        relations: list | None = None,
        moon: bool = False,
    ) -> EpisodeBatch:
        """Serve kernel episodes for (chart, targets, horizon) — WP7 S-1.

        Sourced from the contact ledger (`kala_gochara_contacts`) at the
        authoritative generation; never re-scans the ephemeris per call. The
        DB handle is passed per call because this service is otherwise
        DB-free (live-compute engine); `conn` needs the psycopg cursor idiom.

        Semantics:
          * absent `kala_gochara_authority` row ⇒ chart unpublished ⇒ empty
            episodes + a full coverage object with an honest unsearched_reason
            (N-10; same seam the MCP serving layer applies).
          * an interval with no persisted contacts returns an EMPTY episodes
            list WITH coverage stating what was searched — never a bare []
            (F06).
          * N-14: `drishti_contact` rows with body ∈ {Rahu, Ketu} are excluded
            from the served set and counted in the coverage note.
          * `moon=True` solves Moon episodes live via the gochara_kernel
            (R7: not persisted); they carry `contact_id=None` and a
            `moon_on_demand` coverage partition whose searched horizon equals
            the requested interval.
        """
        wanted_relations = list(relations) if relations else list(EPISODE_RELATIONS)
        horizon_text = self._horizon_text(horizon)

        generation = self._authoritative_generation(conn, chart_id)
        if generation is None:
            return EpisodeBatch(
                episodes=[],
                coverage=[EpisodeCoverage(
                    partition_kind='body_target',
                    partition_key='*',
                    requested_horizon=horizon_text,
                    completed_horizon='empty',
                    relations_searched=wanted_relations,
                    targets_requested=len(targets),
                    targets_resolved=0,
                    targets_unresolved=len(targets),
                    target_resolution_state_counts={},
                    unavailable_inputs={'authority': 'no kala_gochara_authority row'},
                    unsearched_reason='unpublished: absent kala_gochara_authority row (N-10)',
                )],
            )

        episodes, n14_excluded = self._ledger_episodes(
            conn, chart_id, generation, targets, horizon, bodies, wanted_relations,
        )
        coverage = self._ledger_coverage(conn, chart_id, generation, horizon_text)
        if n14_excluded:
            for cov in coverage:
                cov.unavailable_inputs.setdefault('n14_excluded_drishti_rows', n14_excluded)
        if not coverage:
            # F06: never a bare answer — state what was searched even when no
            # manifest row covers the horizon.
            coverage = [EpisodeCoverage(
                partition_kind='body_target',
                partition_key='|'.join(bodies) if bodies else '*',
                requested_horizon=horizon_text,
                completed_horizon=horizon_text,
                relations_searched=wanted_relations,
                targets_requested=len(targets),
                targets_resolved=len({(e.target_type, e.target_ref) for e in episodes}),
                targets_unresolved=0,
                target_resolution_state_counts={},
                unavailable_inputs=(
                    {'n14_excluded_drishti_rows': n14_excluded} if n14_excluded else {}
                ),
                unsearched_reason='no kala_gochara_coverage rows for this horizon',
            )]

        if moon and (bodies is None or 'Moon' in bodies):
            moon_eps, moon_cov = self._moon_on_demand(targets, horizon, wanted_relations)
            episodes = sorted([*episodes, *moon_eps], key=lambda e: (e.t_in, e.relation))
            coverage = [*coverage, moon_cov]

        return EpisodeBatch(episodes=episodes, coverage=coverage)

    def find_directed_contact_events(
        self,
        conn,
        chart_id: str,
        targets: list,
        horizon: Horizon,
        *,
        bodies: list | None = None,
        direction: str = 'to_target',
    ) -> dict:
        """S-2 aggregated directed dṛṣṭi events for Saṅgam (M-3).

        Groups the drishti_contact episodes of one target whose windows
        overlap into a single event: `planets` is the LIST of grahas that
        fired (never a scalar that drops concurrent casters), `aspects`
        carries each graha's classical angle and fractional strength.
        Strength interim (WP8-gated): 1.0 at the exact root under the declared
        orb — the span-aware legacy box reproduced over t_in/t_out; the
        dṛṣṭi-koṇa numeric decay is NOT ratified and is not invented here.
        An interval where nothing fires yields zero events and the coverage
        object only — never a fabricated 0.0 row (F06).
        """
        batch = self.find_episodes(
            conn, chart_id, targets, horizon,
            bodies=bodies, relations=['drishti_contact'],
        )
        by_target: dict = {}
        for ep in batch.episodes:
            by_target.setdefault((ep.target_type, ep.target_ref), []).append(ep)
        events = []
        for (t_type, t_ref), eps in by_target.items():
            eps = sorted(eps, key=lambda e: e.t_in)
            groups: list[list] = []
            for ep in eps:
                if groups and ep.t_in <= groups[-1][-1].t_out:
                    groups[-1].append(ep)
                else:
                    groups.append([ep])
            for g in groups:
                events.append({
                    'window': {'start': g[0].t_in, 'end': max(e.t_out for e in g)},
                    'target': {
                        'target_type': t_type,
                        'target_ref': t_ref,
                        'longitude_deg': g[0].target_longitude_deg,
                    },
                    'planets': sorted({e.body for e in g}),
                    'aspects': [
                        {'planet': e.body, 'aspect_deg': e.aspect_deg, 'strength': 1.0}
                        for e in g
                    ],
                    'direction': direction,
                    'completeness_state': (
                        'unqualified'
                        if any(e.completeness_state == 'unqualified' for e in g)
                        else g[0].completeness_state
                    ),
                    'contact_ids': [e.contact_id for e in g],
                })
        return {'events': events, 'coverage': batch.coverage}

    def _horizon_text(self, horizon: Horizon) -> str:
        return (f'[{_jd_to_iso(self.swe, horizon.start_jd)},'
                f'{_jd_to_iso(self.swe, horizon.end_jd)})')

    @staticmethod
    def _authoritative_generation(conn, chart_id: str) -> str | None:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT authoritative_generation FROM kala_gochara_authority '
                'WHERE chart_id = %s',
                (chart_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        gen = row['authoritative_generation'] if isinstance(row, dict) else row[0]
        return str(gen) if gen else None

    def _ledger_episodes(
        self, conn, chart_id, generation, targets, horizon, bodies, relations,
    ) -> tuple[list, int]:
        sql = (
            'SELECT contact_id, independence_group, body, relation, aspect_deg,'
            '       target_type, target_ref, target_resolution_state,'
            '       target_longitude_deg, t_in, t_exact, t_out, branch,'
            '       truncated_at_horizon, completeness_state, claim_grain,'
            '       convention_id'
            '  FROM kala_gochara_contacts'
            ' WHERE chart_id = %s AND generation = %s'
            '   AND relation = ANY(%s)'
            '   AND t_exact >= %s AND t_exact < %s'
        )
        params: list = [
            chart_id, generation, relations,
            _jd_to_iso(self.swe, horizon.start_jd), _jd_to_iso(self.swe, horizon.end_jd),
        ]
        if bodies:
            sql += ' AND body = ANY(%s)'
            params.append(list(bodies))
        if targets:
            clauses = ' OR '.join(
                '(target_type = %s AND target_ref = %s)' for _ in targets
            )
            sql += f' AND ({clauses})'
            for t in targets:
                params.extend([t.target_type, t.target_ref])
        sql += ' ORDER BY t_exact, contact_id'
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        episodes: list = []
        n14_excluded = 0
        for r in rows:
            r = dict(r)
            if r['relation'] == 'drishti_contact' and r['body'] in N14_DRISHTI_EXCLUDED_BODIES:
                # N-14: nodes cast no dṛṣṭi — these rows (from pre-ruling
                # generations) are never served as drishti_contact.
                n14_excluded += 1
                continue
            episodes.append(GocharaEpisode(
                contact_id=r['contact_id'],
                independence_group=r['independence_group'],
                body=r['body'],
                relation=r['relation'],
                aspect_deg=(float(r['aspect_deg'])
                            if r['relation'] == 'drishti_contact'
                            and r['aspect_deg'] is not None else None),
                target_type=r['target_type'],
                target_ref=r['target_ref'],
                target_resolution_state=r['target_resolution_state'],
                t_in=self._ts_to_iso(r['t_in']),
                t_exact=self._ts_to_iso(r['t_exact']) if r['t_exact'] is not None else None,
                t_out=self._ts_to_iso(r['t_out']),
                branch=r['branch'],
                truncated_at_horizon=r['truncated_at_horizon'],
                completeness_state=r['completeness_state'],
                claim_grain=r['claim_grain'],
                convention_id=r['convention_id'],
                target_longitude_deg=(float(r['target_longitude_deg'])
                                      if r['target_longitude_deg'] is not None else None),
            ))
        return episodes, n14_excluded

    @staticmethod
    def _ts_to_iso(ts) -> str:
        if isinstance(ts, str):
            return ts.replace('+00:00', 'Z')
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    def _ledger_coverage(self, conn, chart_id, generation, horizon_text) -> list:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT partition_kind, partition_key, requested_horizon,'
                '       completed_horizon, relations_searched, targets_requested,'
                '       targets_resolved, targets_unresolved,'
                '       target_resolution_state_counts, unavailable_inputs,'
                '       unsearched_reason'
                '  FROM kala_gochara_coverage'
                ' WHERE chart_id = %s AND generation = %s',
                (chart_id, generation),
            )
            rows = cur.fetchall()
        out = []
        for r in rows:
            r = dict(r)
            out.append(EpisodeCoverage(
                partition_kind=r['partition_kind'],
                partition_key=r['partition_key'],
                requested_horizon=str(r['requested_horizon']),
                completed_horizon=str(r['completed_horizon']),
                relations_searched=list(r['relations_searched'] or []),
                targets_requested=int(r['targets_requested']),
                targets_resolved=int(r['targets_resolved']),
                targets_unresolved=int(r['targets_unresolved']),
                target_resolution_state_counts=dict(r['target_resolution_state_counts'] or {}),
                unavailable_inputs=dict(r['unavailable_inputs'] or {}),
                unsearched_reason=r['unsearched_reason'],
            ))
        return out

    def _moon_on_demand(
        self, targets, horizon: Horizon, relations,
    ) -> tuple[list, EpisodeCoverage]:
        """Live Moon episodes via the gochara_kernel (R7: never persisted).

        contact_id=None on every returned episode; the coverage partition is
        `moon_on_demand` with searched horizon == requested horizon. Targets
        without an explicit longitude are counted unresolved (the WP1 §2.2
        resolution contract is the caller's job) — never fabricated.
        """
        from services.gochara_kernel import arcs as gk_arcs
        from services.gochara_kernel import convention as gk_convention
        from services.gochara_kernel import episodes as gk_episodes
        from services.gochara_kernel import knots as gk_knots

        moon_relations = [r for r in relations if r in _MOON_ORB_SOURCE]
        horizon_text = self._horizon_text(horizon)
        partition_key = f'moon:interval:{horizon_text}'
        resolvable = [t for t in targets if t.longitude_deg is not None]
        unresolved = len(targets) - len(resolvable)

        if not moon_relations or not resolvable:
            return [], EpisodeCoverage(
                partition_kind='moon_on_demand',
                partition_key=partition_key,
                requested_horizon=horizon_text,
                completed_horizon=horizon_text,
                relations_searched=moon_relations,
                targets_requested=len(targets),
                targets_resolved=0,
                targets_unresolved=unresolved,
                target_resolution_state_counts={},
                unavailable_inputs=(
                    {'target_longitudes': 'missing'} if unresolved else {}
                ),
                unsearched_reason=(
                    None if moon_relations
                    else 'no moon-eligible relations requested'
                ),
            )

        start = _jd_to_date(self.swe, horizon.start_jd) - timedelta(days=1)
        end = _jd_to_date(self.swe, horizon.end_jd) + timedelta(days=1)
        ks = gk_knots.sample_knots('Moon', start, end, ephe_path=self._ephe_path)
        index = gk_arcs.build_arc_index(
            'Moon', ks.knot_jds, ks.longitudes_deg,
            tolerance_arcsec=gk_convention.declared_tolerance('Moon', 'conjunction')
            ['tolerance_arcsec'],
        )
        span = (float(horizon.start_jd), float(horizon.end_jd))
        convention_id = gk_convention.canonical_convention_id()
        out: list = []
        for t in resolvable:
            for rel in moon_relations:
                if rel in _BOUNDARY_RELATIONS:
                    eps = gk_episodes.solve_boundary_episodes(
                        index, 'Moon', rel, span, ephe_path=self._ephe_path,
                    )
                else:
                    eps = gk_episodes.solve_episodes(
                        index, 'Moon', rel, float(t.longitude_deg), span,
                        _MOON_ORB_SOURCE[rel], ephe_path=self._ephe_path,
                    )
                for e in eps:
                    out.append(GocharaEpisode(
                        contact_id=None,
                        independence_group=(
                            f'moon_on_demand:{rel}:{t.target_ref}:'
                            f'{e.t_exact if e.t_exact is not None else e.t_in}'
                        ),
                        body='Moon',
                        relation=rel,
                        aspect_deg=(float(e.aspect_deg)
                                    if rel == 'drishti_contact' else None),
                        target_type=t.target_type,
                        target_ref=t.target_ref,
                        target_resolution_state='resolved',
                        t_in=_jd_to_iso(self.swe, e.t_in),
                        t_exact=(_jd_to_iso(self.swe, e.t_exact)
                                 if e.t_exact is not None else None),
                        t_out=_jd_to_iso(self.swe, e.t_out),
                        branch=e.branch,
                        truncated_at_horizon=(
                            e.truncated_at_horizon
                            if e.truncated_at_horizon in ('start', 'end') else None
                        ),
                        completeness_state=e.completeness_state,
                        claim_grain='on_demand_live',
                        convention_id=convention_id,
                        target_longitude_deg=float(t.longitude_deg),
                    ))
        out.sort(key=lambda ep: (ep.t_in, ep.relation))
        return out, EpisodeCoverage(
            partition_kind='moon_on_demand',
            partition_key=partition_key,
            requested_horizon=horizon_text,
            completed_horizon=horizon_text,
            relations_searched=moon_relations,
            targets_requested=len(targets),
            targets_resolved=len(resolvable),
            targets_unresolved=unresolved,
            target_resolution_state_counts={
                'resolved': len(resolvable),
                **({'unavailable': unresolved} if unresolved else {}),
            },
            unavailable_inputs=(
                {'target_longitudes': f'{unresolved} target(s) without longitude'}
                if unresolved else {}
            ),
            unsearched_reason=None,
        )


    def service_health(self) -> dict:
        """Transit service connectivity probe (MR-09 health check restore).

        The W6.4 migration retired the old ka_gochara self-test DB row but
        left no replacement.  This method is the replacement: it runs a
        deterministic, side-effect-free Julian Day computation against the
        bound swisseph instance to verify the ephemeris engine is live.

        Returns a dict with:
          "status"  — "ok" if the probe computation succeeded, "error" otherwise.
          "detail"  — human-readable description of what was checked / what failed.
          "probe"   — the test computation type (always "julday_j2000").
          "result"  — the computed JD value on success, None on error.

        This is NOT a DB self-test row (those were retired by design).
        It is a pure live-compute connectivity check on the swe engine.
        """
        try:
            # J2000.0: 2000-01-01 12:00 UT
            computed = self.swe.julday(2000, 1, 1, 12.0)
            # Sanity: J2000.0 must be within 1.0 JD of the known value
            if abs(computed - _HEALTH_PROBE_JD) > 1.0:
                return {
                    "status": "error",
                    "detail": (
                        f"julday(2000-01-01 12h) returned {computed!r}; "
                        f"expected ~{_HEALTH_PROBE_JD} (J2000.0).  "
                        "Ephemeris engine may be mis-configured."
                    ),
                    "probe": "julday_j2000",
                    "result": computed,
                }
            return {
                "status": "ok",
                "detail": (
                    f"julday(2000-01-01 12h) = {computed!r} "
                    f"(expected ~{_HEALTH_PROBE_JD}).  Ephemeris engine live."
                ),
                "probe": "julday_j2000",
                "result": computed,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("[GocharaTransitService.service_health] probe failed: %s", exc)
            return {
                "status": "error",
                "detail": f"julday probe raised: {exc}",
                "probe": "julday_j2000",
                "result": None,
            }


# ---------------------------------------------------------------------------
# Backward-compat alias (MR-09)
# ---------------------------------------------------------------------------
# ka_sangam.py and existing tests import by this name.  Keeping the alias
# here means no change is needed in those callers.  The PRIMARY class is
# GocharaTransitService; this alias exists for continuity only.
KaGocharaService = GocharaTransitService


__all__ = [
    "GocharaTransitService", "KaGocharaService",
    "TargetRef", "Horizon", "GocharaEpisode", "EpisodeCoverage", "EpisodeBatch",
    "EPISODE_RELATIONS", "N14_DRISHTI_EXCLUDED_BODIES",
]
