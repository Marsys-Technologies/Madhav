"""
tests/l3/ka_kshetra/fake_db.py — a minimal in-memory stand-in for the sidecar's
Postgres connection, sufficient to drive `KaKshetraWriter` end to end.

WHY THIS EXISTS RATHER THAN AN INTEGRATION-ONLY TEST. The two things this lane
most needs to prove — that the field is deterministic and that it never reads the
lived-history corpus — are both statements about the SQL the writer issues and
the rows it produces. A fake connection that RECORDS every statement makes both
directly assertable on every CI run, with no database, no proxy tunnel and no
`@pytest.mark.integration` skip that quietly never runs (the exact gap the
ṢAḌ-DARŚANA circularity-guard workflow was created to close for the W1 test).

It is deliberately NOT a SQL engine. It pattern-matches the specific statements
`services/ka_kshetra/*` issues and nothing else; an unrecognized statement RAISES
rather than returning an empty result, so a new query added to the writer cannot
silently read as "no rows" and pass a test it was never exercised by.
"""
from __future__ import annotations

import re
from typing import Any, Optional


class FakeCursor:
    def __init__(self, conn: 'FakeConn'):
        self._conn = conn
        self._rows: list[dict] = []
        self.description: Optional[list] = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    # ── the dispatcher ───────────────────────────────────────────────────────

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._conn.executed.append(sql)
        s = ' '.join(sql.split())
        t = self._conn.tables

        if s.startswith('DELETE FROM'):
            table = re.match(r'DELETE FROM (\w+)', s).group(1)
            self._conn.deletes.append(table)
            # The lel_derived carve-out is emulated, not ignored: `kala_insights`
            # is SHARED with Lane E's biographical-join refresh, and a fake that
            # cleared the whole table would let a blanket per-chart delete pass a
            # test the real database would fail Lane E on.
            if 'lel_derived = FALSE' in s:
                t[table] = [r for r in t.get(table, []) if r.get('lel_derived') is not False]
            else:
                t[table] = []
            self._rows = []
            return

        if s.startswith('INSERT INTO'):
            table = re.match(r'INSERT INTO (\w+)', s).group(1)
            self._conn.inserts.setdefault(table, []).append(params)
            cols = re.search(r'INSERT INTO \w+ \(([^)]*)\)', s)
            if cols:
                names = [c.strip() for c in cols.group(1).split(',')]
                row = dict(zip(names, params))
                key = self._conn.natural_keys.get(table)
                rows = t.setdefault(table, [])
                if key:
                    ident = tuple(row.get(k) for k in key)
                    rows[:] = [r for r in rows
                               if tuple(r.get(k) for k in key) != ident]
                rows.append(row)
            self._rows = []
            return

        if 'FROM kala_field_weight_versions' in s:
            self._rows = [{'version_id': r['version_id']}
                          for r in t.get('kala_field_weight_versions', [])
                          if r.get('status') == 'active']
            return
        if 'FROM kala_field_weights' in s:
            self._rows = [dict(r) for r in t.get('kala_field_weights', [])
                          if r['version_id'] == params[0]]
            return
        if 'FROM public.charts' in s:
            self._rows = [dict(r) for r in t.get('charts', [])]
            return
        if 'MAX(build_id' in s and 'FROM bg_synthetic_cohort' in s:
            rows = t.get('bg_synthetic_cohort', [])
            self._rows = [{'b': max((r['build_id'] for r in rows), default=None)}]
            return
        if 'FROM bg_synthetic_cohort_md' in s:
            rows = t.get('bg_synthetic_cohort_md', [])
            versions = {r.get('chain_version') for r in rows}
            self._rows = [{'md_rows': len(rows),
                           'chain_version': min(versions) if versions else None,
                           'n_chain_versions': len(versions)}]
            return
        if 'FROM bg_synthetic_cohort' in s:
            # The §6.3 content-fingerprint aggregate. The fixture cohort is
            # DELIBERATELY tiny, so `cohort_base_rate` takes its own designed
            # `cohort_below_minimum` path and returns p=None. That is the honest
            # branch the salience vector must handle (Informativeness NULL,
            # renormalized out) — fabricating a 10,000-row cohort here would
            # test a population that does not exist.
            rows = t.get('bg_synthetic_cohort', [])
            methods = {r.get('sampling_method') for r in rows if r.get('sampling_method')}
            self._rows = [{
                'n_total': len(rows),
                'n_sampling_methods': len(methods),
                'sampling_method': min(methods) if methods else None,
                'ayanamsha_key': 'lahiri',
                'positions_digest': None,
            }]
            return
        if 'DISTINCT event_class_id FROM bodha_pratijna' in s:
            self._rows = [{'event_class_id': ec} for ec in sorted({
                r['event_class_id'] for r in t.get('bodha_pratijna', [])
                if r.get('status') in ('promised', 'conditional')
            })]
            return
        if 'FROM kala_field_routes' in s:
            self._rows = [dict(r) for r in t.get('kala_field_routes', [])
                          if r['event_class'] == params[1]]
            return
        if 'FROM build_substep_progress' in s:
            self._rows = [dict(r) for r in t.get('build_substep_progress', [])]
            return
        if 'FROM brahma_event_ontology' in s:
            self._rows = [dict(r) for r in t.get('brahma_event_ontology', [])
                          if r.get('event_class_id') == params[0]]
            return
        if 'FROM brahma_class_priors' in s:
            # The RESERVED COORDINATE is four predicates, not two — see
            # `stage4_field.load_class_lifetime_count`. Emulating only the first
            # two here would let a narrower-coordinate row satisfy a query that
            # in production excludes it, which is exactly the class of drift
            # this fake exists to make impossible.
            rows = [dict(r) for r in t.get('brahma_class_priors', [])
                    if r.get('signal_type_class') == params[0]
                    and r.get('fact_kind') == 'lifetime_count_per_100y']
            if "source_subsystem = '*'" in s:
                rows = [r for r in rows if r.get('source_subsystem') == '*']
            if "signal_tradition = '*'" in s:
                rows = [r for r in rows if r.get('signal_tradition') == '*']
            self._rows = sorted(rows, key=lambda r: (
                tuple(-ord(c) for c in str(r.get('prior_version', ''))),
                str(r.get('source_subsystem', '')), str(r.get('signal_tradition', ''))))
            return
        if 'FROM kala_field_clocks' in s:
            self._rows = [dict(r) for r in t.get('kala_field_clocks', [])]
            return
        if 'MIN(sigma_t_days)' in s:
            vals = [r['sigma_t_days'] for r in t.get('kala_field_boundaries', [])
                    if r.get('sigma_t_days') is not None]
            self._rows = [{'s': min(vals) if vals else None}]
            return
        if 'FROM kala_field_boundaries' in s and 'level = ANY' in s:
            # The stage-8 read deliberately does NOT filter precision_state: the
            # spec builder needs the unsupported rows in order to COUNT them in
            # its coverage. Emulating a filter here would hide that.
            levels = set(params[1])
            self._rows = [dict(r) for r in t.get('kala_field_boundaries', [])
                          if r.get('level') in levels]
            return
        if 'FROM kala_field_boundaries' in s:
            self._rows = [dict(r) for r in t.get('kala_field_boundaries', [])
                          if r.get('precision_state') != 'precision_unsupported']
            return
        if 'FROM kala_field_primitives' in s:
            self._rows = [dict(r) for r in t.get('kala_field_primitives', [])]
            return
        if 'DISTINCT ayanamsha_id FROM kala_field_kinematics' in s:
            self._rows = [{'ayanamsha_id': a} for a in sorted(
                {r['ayanamsha_id'] for r in t.get('kala_field_kinematics', [])})]
            return
        if 'DISTINCT t_days FROM kala_field_kinematics' in s:
            self._rows = [{'t_days': v} for v in sorted(
                {r['t_days'] for r in t.get('kala_field_kinematics', [])})]
            return
        if 'FROM kala_gochara_authority' in s and 'AS gen' in s:
            # A1 pin: SELECT COALESCE((SELECT authoritative_generation ...), 'v1') AS gen
            # (not the legacy crosscheck's subquery, which also references this table)
            rows = [r for r in t.get('kala_gochara_authority', [])
                    if str(r.get('chart_id')) == str(params[0])]
            self._rows = [{'gen': rows[0]['authoritative_generation'] if rows else 'v1'}]
            return
        if 'calibration_state' in s and 'COUNT(*)' in s and 'FROM kala_gochara_windows' in s:
            # A1 pin: SELECT calibration_state, COUNT(*) AS n FROM kala_gochara_windows
            #         WHERE chart_id=%s AND generation=%s GROUP BY calibration_state ...
            chart_id, generation = params[0], params[1]
            matching = [r for r in t.get('kala_gochara_windows', [])
                        if str(r.get('chart_id')) == str(chart_id)
                        and r.get('generation', 'v1') == generation]
            if not matching:
                self._rows = []
            else:
                from collections import Counter
                counts = Counter(r.get('calibration_state', 'structural_prior')
                                 for r in matching)
                top = counts.most_common(1)[0]
                self._rows = [{'calibration_state': top[0], 'n': top[1]}]
            return
        if 'FROM kala_gochara_windows' in s:
            self._rows = [dict(r) for r in t.get('kala_gochara_windows', [])
                          if r.get('event_class') == params[1]]
            return
        if 'FROM gochara_resonance_map' in s and 'md5' in s:
            # A1 pin: SELECT md5(COUNT(*)::text || '|' || ...) AS digest
            rows = [r for r in t.get('gochara_resonance_map', [])
                    if str(r.get('chart_id')) == str(params[0])]
            import hashlib
            digest_input = (f"{len(rows)}|"
                            + (max((str(r.get('computed_at', '')) for r in rows), default=''))
                            + '|'
                            + (str(max((r.get('id', 0) for r in rows), default=''))
                               if rows else ''))
            self._rows = [{'digest': hashlib.md5(digest_input.encode()).hexdigest()
                           if rows else 'digest_unavailable'}]
            return
        if 'FROM chart_facts' in s and "fact_category = 'lagna'" in s:
            self._rows = [dict(r) for r in t.get('chart_facts', [])
                          if r.get('fact_category') == 'lagna'
                          and r.get('fact_key') == 'longitude']
            return
        if 'FROM chart_facts' in s:
            wanted = set(params[1])
            resolved = {r['fact_id'] for r in t.get('chart_facts', [])
                        if r['fact_id'] in wanted}
            if 'COUNT' in s:
                # _citation_resolution shape: SELECT COUNT(DISTINCT fact_id) AS n
                self._rows = [{'n': len(resolved)}]
            else:
                # _write_windows_batch shape: SELECT DISTINCT fact_id
                self._rows = [{'fact_id': fid} for fid in sorted(resolved)]
            return
        if 'FROM kala_field_salience' in s:
            self._rows = [dict(r) for r in t.get('kala_field_salience', [])]
            return
        if 'FROM kala_timeline_spec' in s:
            self._rows = [dict(r) for r in t.get('kala_timeline_spec', [])]
            return
        if 'FROM kala_insights' in s:
            rows = [dict(r) for r in t.get('kala_insights', [])]
            if 'lel_derived = FALSE' in s:
                rows = [r for r in rows if r.get('lel_derived') is False]
            self._rows = rows
            return
        if 'COUNT(*) AS n FROM kala_field' in s:
            self._rows = [{'n': sum(1 for r in t.get('kala_field', [])
                                    if r['event_class'] == params[1])}]
            return
        if 'FROM kala_field_windows' in s:
            self._rows = [dict(r) for r in t.get('kala_field_windows', [])]
            return
        if 'FROM kala_field_provenance' in s:
            self._rows = [dict(r) for r in t.get('kala_field_provenance', [])]
            return
        if 'FROM kala_field_null' in s:
            self._rows = [dict(r) for r in t.get('kala_field_null', [])]
            return
        if 'FROM kala_field' in s:
            rows = [dict(r) for r in t.get('kala_field', [])]
            if len(params) > 1:
                rows = [r for r in rows if r['event_class'] == params[1]]
            self._rows = sorted(rows, key=lambda r: (r['t_start'], r['segment_index']))
            return

        raise AssertionError(
            f'FakeConn has no handler for this statement — add one deliberately '
            f'rather than letting it read as "no rows":\n{s[:300]}'
        )

    def fetchall(self) -> list[dict]:
        return self._rows

    def fetchone(self) -> Optional[dict]:
        return self._rows[0] if self._rows else None

    def executemany(self, sql: str, params_seq) -> None:
        """Batch insert — delegate to execute() for each param tuple.
        Added by L1e fix (stage4 batch-insert pattern matching stage3 L1d).
        """
        for params in params_seq:
            self.execute(sql, params)


class FakeConn:
    """An in-memory connection. `executed` records every statement, which is what
    the Circularity Guard's dynamic half asserts over."""

    #: Natural keys used to emulate ON CONFLICT DO UPDATE per table.
    natural_keys = {
        'kala_field': ('chart_id', 'event_class', 'segment_index'),
        'kala_field_windows': ('chart_id', 'window_id'),
        'kala_field_provenance': ('chart_id', 'field_snapshot_id', 'target_kind',
                                  'target_id', 'term_key'),
        'kala_field_null': ('chart_id', 'event_class', 'bucket_days', 'field_snapshot_id'),
        'kala_field_snapshots': ('chart_id', 'field_snapshot_id'),
        'kala_field_salience': ('chart_id', 'window_id'),
        'kala_insights': ('chart_id', 'insight_id'),
        'kala_timeline_spec': ('chart_id', 'generated_for', 'field_snapshot_id'),
        'build_substep_progress': ('chart_id', 'asset_id', 'substep_key'),
    }

    def __init__(self, tables: dict[str, list[dict]]):
        self.tables = tables
        self.executed: list[str] = []
        self.inserts: dict[str, list[tuple]] = {}
        self.deletes: list[str] = []

    # `cursor_factory` / `row_factory` are accepted and ignored: this fake always
    # yields dict rows, which is what every real call site asks for anyway.
    def cursor(self, *args, **kwargs) -> FakeCursor:
        return FakeCursor(self)

    # psycopg3 allows calling execute() directly on the connection object;
    # delegate to FakeCursor so the same dispatch logic applies.
    def execute(self, sql: str, params=None) -> FakeCursor:
        cur = FakeCursor(self)
        cur.execute(sql, params if params is not None else ())
        return cur

    # The FROZEN contract forbids the writer touching any of these. Each raises
    # so a violation is a test failure at the exact call site, not a subtle
    # behavioural difference discovered in production.
    def commit(self):
        raise AssertionError('FROZEN CONTRACT VIOLATION: the writer called commit() on '
                             'ctx.db_conn. The orchestrator owns the transaction.')

    def rollback(self):
        raise AssertionError('FROZEN CONTRACT VIOLATION: the writer called rollback().')

    def close(self):
        raise AssertionError('FROZEN CONTRACT VIOLATION: the writer called close().')


class FakeCtx:
    def __init__(self, conn: FakeConn, chart_id: str, dry_run: bool = False):
        self.db_conn = conn
        self.config = {'chart_id': chart_id}
        self.dry_run = dry_run
        self.asset_id = 'ka_kshetra'
        self.build_id = 'test-build'
