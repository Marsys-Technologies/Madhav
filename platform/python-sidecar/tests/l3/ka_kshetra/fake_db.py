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
        if 'FROM bg_synthetic_cohort' in s:
            rows = t.get('bg_synthetic_cohort', [])
            self._rows = [{'b': max((r['build_id'] for r in rows), default=None)}]
            return
        if 'DISTINCT event_class FROM kala_field_routes' in s:
            self._rows = [{'event_class': ec} for ec in sorted(
                {r['event_class'] for r in t.get('kala_field_routes', [])})]
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
            self._rows = [dict(r) for r in t.get('brahma_class_priors', [])
                          if r.get('signal_type_class') == params[0]
                          and r.get('fact_kind') == 'lifetime_count_per_100y']
            return
        if 'FROM kala_field_clocks' in s:
            self._rows = [dict(r) for r in t.get('kala_field_clocks', [])]
            return
        if 'MIN(sigma_t_days)' in s:
            vals = [r['sigma_t_days'] for r in t.get('kala_field_boundaries', [])
                    if r.get('sigma_t_days') is not None]
            self._rows = [{'s': min(vals) if vals else None}]
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
        if 'FROM kala_gochara_windows' in s:
            self._rows = [dict(r) for r in t.get('kala_gochara_windows', [])
                          if r.get('event_class') == params[1]]
            return
        if 'FROM chart_facts' in s:
            wanted = set(params[1])
            self._rows = [{'n': len({r['fact_id'] for r in t.get('chart_facts', [])
                                     if r['fact_id'] in wanted})}]
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
        'build_substep_progress': ('chart_id', 'asset_id', 'substep_key'),
    }

    def __init__(self, tables: dict[str, list[dict]]):
        self.tables = tables
        self.executed: list[str] = []
        self.inserts: dict[str, list[tuple]] = {}
        self.deletes: list[str] = []

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

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
