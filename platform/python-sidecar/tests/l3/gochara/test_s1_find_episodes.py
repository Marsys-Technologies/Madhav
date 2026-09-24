"""WP7 S-1/S-2 — GocharaTransitService.find_episodes + directed contact events.

Hermetic: the ledger path runs against an in-memory FakeConn (emulating the
authority seam, relation/body/target filters and the t_exact range), the Moon
on-demand path runs against synthetic knots + a stubbed kernel solver (no
Swiss, no DB). The find_aspects duck-typed contract is asserted unchanged.
"""
from __future__ import annotations

import inspect
from datetime import date

import pytest
import swisseph as swe

from services.gochara_kernel import episodes as gk_episodes
from services.gochara_kernel import knots as gk_knots
from services.ka_gochara.service import (
    EPISODE_RELATIONS,
    GocharaTransitService,
    Horizon,
    TargetRef,
)

CHART_ID = '00000000-0000-4000-8000-0000000000s1'.replace('s1', '51')
H0, H1 = 2460000.0, 2460030.0


def _iso(svc, jd):
    return svc._horizon_text(Horizon(jd, jd)).strip('[]()').split(',')[0]


class _Cur:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params):
        self._rows = self.conn.route(' '.join(sql.split()), list(params or []))

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    """Emulates the three find_episodes reads. A query this fake does not
    recognise raises — never reads as 'no rows'."""

    def __init__(self, authority=(), contacts=(), coverage=()):
        self.authority = list(authority)
        self.contacts = list(contacts)
        self.coverage = list(coverage)
        self.statements = []

    def cursor(self, *a, **k):
        return _Cur(self)

    def route(self, s, params):
        self.statements.append(s)
        if 'FROM kala_gochara_authority' in s:
            return [r for r in self.authority
                    if str(r['chart_id']) == str(params[0])]
        if 'FROM kala_gochara_contacts' in s:
            chart_id, generation, relations, t0, t1 = params[:5]
            rest = params[5:]
            bodies = None
            if 'AND body = ANY' in s:
                bodies = rest[0]
                rest = rest[1:]
            rows = [
                r for r in self.contacts
                if str(r['chart_id']) == str(chart_id)
                and r['generation'] == generation
                and r['relation'] in relations
                and t0 <= r['t_exact'] < t1
                and (bodies is None or r['body'] in bodies)
            ]
            if 'target_type = %s AND target_ref = %s' in s:
                pairs = {(rest[i], rest[i + 1]) for i in range(0, len(rest), 2)}
                rows = [r for r in rows
                        if (r['target_type'], r['target_ref']) in pairs]
            return sorted(rows, key=lambda r: (r['t_exact'], r['contact_id']))
        if 'FROM kala_gochara_coverage' in s:
            return [r for r in self.coverage
                    if str(r['chart_id']) == str(params[0])
                    and r['generation'] == params[1]]
        raise AssertionError(f'FakeConn: unrouted statement: {s[:200]}')


def _contact(body='Saturn', relation='drishti_contact', aspect=60.0,
             t_exact='2023-03-15T12:00:00Z', target_ref='graha:sun',
             completeness='confirmed'):
    return {
        'chart_id': CHART_ID, 'generation': '4.0',
        'contact_id': f'sha256:{"ab" * 32}',
        'independence_group': 'ig:1', 'body': body, 'relation': relation,
        'aspect_deg': aspect, 'target_type': 'graha', 'target_ref': target_ref,
        'target_resolution_state': 'resolved', 'target_longitude_deg': 12.75,
        't_in': '2023-03-14T12:00:00Z', 't_exact': t_exact,
        't_out': '2023-03-16T12:00:00Z', 'branch': 'direct',
        'truncated_at_horizon': None, 'completeness_state': completeness,
        'claim_grain': 'contact', 'convention_id': 'sha256:conv',
    }


@pytest.fixture()
def svc():
    return GocharaTransitService(swe)


# ── S-1 ledger path ──────────────────────────────────────────────────────────

class TestFindEpisodesLedger:
    def test_unpublished_chart_returns_coverage_never_bare_empty(self, svc):
        conn = FakeConn()  # no authority row
        batch = svc.find_episodes(
            conn, CHART_ID, [TargetRef('graha', 'graha:sun')], Horizon(H0, H1),
        )
        assert batch.episodes == []
        assert len(batch.coverage) == 1
        cov = batch.coverage[0]
        assert 'unpublished' in cov.unsearched_reason
        assert cov.targets_requested == 1 and cov.targets_resolved == 0

    def test_ledger_episodes_served_and_n14_rows_excluded(self, svc):
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
            contacts=[
                _contact(body='Saturn', relation='drishti_contact', aspect=60.0),
                # Pre-ruling generation row: nodes cast no dṛṣṭi (N-14) —
                # excluded from serving, counted in the coverage note.
                _contact(body='Rahu', relation='drishti_contact', aspect=180.0),
                _contact(body='Jupiter', relation='conjunction', aspect=None),
            ],
            coverage=[{
                'chart_id': CHART_ID, 'generation': '4.0',
                'partition_kind': 'body_target', 'partition_key': 'saturn:graha',
                'requested_horizon': '[2026-03-01,2026-04-01)',
                'completed_horizon': '[2026-03-01,2026-04-01)',
                'relations_searched': ['drishti_contact'],
                'targets_requested': 1, 'targets_resolved': 1,
                'targets_unresolved': 0, 'target_resolution_state_counts': {},
                'unavailable_inputs': {}, 'unsearched_reason': None,
            }],
        )
        batch = svc.find_episodes(conn, CHART_ID, [], Horizon(H0, H1))
        bodies = {(e.body, e.relation) for e in batch.episodes}
        assert ('Saturn', 'drishti_contact') in bodies
        assert ('Jupiter', 'conjunction') in bodies
        assert all(e.body != 'Rahu' or e.relation != 'drishti_contact'
                   for e in batch.episodes)
        assert batch.coverage[0].unavailable_inputs['n14_excluded_drishti_rows'] == 1
        sat = next(e for e in batch.episodes if e.body == 'Saturn')
        assert sat.aspect_deg == 60.0
        assert sat.contact_id == f'sha256:{"ab" * 32}'
        assert sat.target_longitude_deg == 12.75

    def test_empty_interval_carries_full_coverage(self, svc):
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
        )
        batch = svc.find_episodes(
            conn, CHART_ID, [TargetRef('graha', 'graha:sun')], Horizon(H0, H1),
            bodies=['Saturn'],
        )
        assert batch.episodes == []
        assert len(batch.coverage) == 1
        cov = batch.coverage[0]
        assert cov.relations_searched == list(EPISODE_RELATIONS)
        assert cov.unsearched_reason is not None  # honest: no manifest rows

    def test_target_and_relation_filters_reach_the_query(self, svc):
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
            contacts=[
                _contact(target_ref='graha:sun'),
                _contact(target_ref='graha:moon'),
            ],
        )
        batch = svc.find_episodes(
            conn, CHART_ID, [TargetRef('graha', 'graha:sun')], Horizon(H0, H1),
            relations=['drishti_contact'],
        )
        assert {e.target_ref for e in batch.episodes} == {'graha:sun'}


# ── S-1 Moon on-demand path ─────────────────────────────────────────────────

def _kernel_episode(t_in, t_exact, t_out, branch='direct'):
    return gk_episodes.Episode(
        body='Moon', relation='conjunction', aspect_deg=0.0, target_deg=100.0,
        level_deg=100.0, t_in=t_in, t_exact=t_exact, t_out=t_out,
        branch=branch, station_flag=False, exact_crossing=True,
        orb_max_deg=3.0, orb_source='orb_conj_moon', dwell_days=t_out - t_in,
        truncated_at_horizon=None, tolerance_arcsec=5.0, bracket_seconds=60,
        completeness_state='applied', near_station_unresolved=False,
    )


class TestMoonOnDemand:
    def _patch_kernel(self, monkeypatch, solved):
        monkeypatch.setattr(
            gk_knots, 'sample_knots',
            lambda body, start, end, ephe_path=None: gk_knots.KnotSeries(
                body='Moon', start_date=start, end_date=end,
                knot_jds=(H0, H0 + 10, H0 + 20, H1),
                longitudes_deg=(90.0, 100.0, 110.0, 120.0),
            ),
        )
        monkeypatch.setattr(
            gk_episodes, 'solve_episodes',
            lambda *a, **k: list(solved),
        )

    def test_moon_episodes_contact_id_null_and_coverage_partition(
            self, svc, monkeypatch):
        self._patch_kernel(monkeypatch, [_kernel_episode(H0 + 4, H0 + 5, H0 + 6)])
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
        )
        batch = svc.find_episodes(
            conn, CHART_ID,
            [TargetRef('graha', 'graha:mars', longitude_deg=100.0)],
            Horizon(H0, H1), relations=['conjunction'], moon=True,
        )
        assert len(batch.episodes) == 1
        ep = batch.episodes[0]
        assert ep.contact_id is None
        assert ep.body == 'Moon' and ep.claim_grain == 'on_demand_live'
        moon_cov = next(c for c in batch.coverage
                        if c.partition_kind == 'moon_on_demand')
        assert moon_cov.requested_horizon == moon_cov.completed_horizon
        assert moon_cov.targets_resolved == 1
        assert moon_cov.unsearched_reason is None

    def test_moon_target_without_longitude_is_unresolved_not_fabricated(
            self, svc, monkeypatch):
        self._patch_kernel(monkeypatch, [_kernel_episode(H0 + 4, H0 + 5, H0 + 6)])
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
        )
        batch = svc.find_episodes(
            conn, CHART_ID,
            [TargetRef('graha', 'graha:mars'),                      # no longitude
             TargetRef('graha', 'graha:venus', longitude_deg=100.0)],
            Horizon(H0, H1), relations=['conjunction'], moon=True,
        )
        moon_cov = next(c for c in batch.coverage
                        if c.partition_kind == 'moon_on_demand')
        assert moon_cov.targets_requested == 2
        assert moon_cov.targets_resolved == 1
        assert moon_cov.targets_unresolved == 1
        assert {e.target_ref for e in batch.episodes} == {'graha:venus'}

    def test_moon_zero_answer_still_writes_partition(self, svc, monkeypatch):
        self._patch_kernel(monkeypatch, [])  # nothing fires
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
        )
        batch = svc.find_episodes(
            conn, CHART_ID,
            [TargetRef('graha', 'graha:mars', longitude_deg=100.0)],
            Horizon(H0, H1), relations=['conjunction'], moon=True,
        )
        assert batch.episodes == []
        moon_cov = next(c for c in batch.coverage
                        if c.partition_kind == 'moon_on_demand')
        assert moon_cov.targets_resolved == 1  # searched, zero answer


# ── S-2 directed contact events ─────────────────────────────────────────────

class TestDirectedContactEvents:
    def test_concurrent_casters_group_into_one_event(self, svc):
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
            contacts=[
                _contact(body='Jupiter', aspect=120.0),
                _contact(body='Saturn', aspect=60.0),
            ],
        )
        out = svc.find_directed_contact_events(
            conn, CHART_ID, [TargetRef('graha', 'graha:sun')], Horizon(H0, H1),
        )
        assert len(out['events']) == 1
        ev = out['events'][0]
        assert ev['planets'] == ['Jupiter', 'Saturn']
        angles = {a['planet']: a['aspect_deg'] for a in ev['aspects']}
        assert angles == {'Jupiter': 120.0, 'Saturn': 60.0}
        assert ev['direction'] == 'to_target'
        assert ev['target']['longitude_deg'] == 12.75
        assert all(isinstance(a['strength'], float) for a in ev['aspects'])

    def test_nothing_fires_returns_zero_events_with_coverage(self, svc):
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
        )
        out = svc.find_directed_contact_events(
            conn, CHART_ID, [TargetRef('graha', 'graha:sun')], Horizon(H0, H1),
        )
        assert out['events'] == []
        assert out['coverage']  # F06: silence lives in coverage, never a 0.0 row

    def test_rahu_only_transit_produces_no_drishti_event(self, svc):
        conn = FakeConn(
            authority=[{'chart_id': CHART_ID, 'authoritative_generation': '4.0'}],
            contacts=[_contact(body='Rahu', aspect=180.0)],
        )
        out = svc.find_directed_contact_events(
            conn, CHART_ID, [TargetRef('graha', 'graha:sun')], Horizon(H0, H1),
        )
        assert out['events'] == []
        assert out['coverage'][0].unavailable_inputs.get(
            'n14_excluded_drishti_rows') == 1


# ── Ecosystem: find_aspects duck-typed contract unchanged ────────────────────

class TestEcosystemContract:
    def test_find_aspects_signature_is_the_legacy_shape(self):
        sig = inspect.signature(GocharaTransitService.find_aspects)
        assert list(sig.parameters) == [
            'self', 'transit_planet', 'target_lon', 'aspect_degrees',
            'orb', 'start_jd', 'end_jd',
        ]

    def test_legacy_positional_construction_still_works(self, svc):
        # kala_trigger / ka_sangam / currents.py construct with the swe module
        # alone; the ephe_path kwarg must stay optional.
        assert GocharaTransitService(swe)._ephe_path is None
