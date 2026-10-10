"""_keyed_fixture.py: the shared fixture of the keyed-exact-read tests (Nikasha lane W3, n430 ga_dashas).

A real table on the DISPOSABLE PostgreSQL shaped like chart_dashas: a bigserial primary key, a unique natural-key index that LEADS with the partitioning columns (a, b, id), 3 values of `a` x 2 of `b`,
a templated pointer column, a jsonb document column and a citation column. Nothing here touches any other database: `point_psql_at` removes every inherited PG* name and spells out the throw-away cluster.
"""
from __future__ import annotations

import asset_census as ac
from _disposable_pg import point_psql_at

CHART = "11111111-2222-3333-4444-555555555555"
OTHER = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
A_VALUES = (1, 2, 3)
B_VALUES = (1, 2)


def make_table(pg, monkeypatch, name="kt_dash", per_cell=500, index=True):
    """Create `name`: for each (a, b) `per_cell` rows of the measured chart (so 6 x per_cell rows: 3 partitions of 2 x per_cell by `a`, 6 of per_cell by (a, b)).
    Every row is clean: citation_ref 'ref.<n>@chart=<CHART>', doc {"cls": ["x"]}, citation_human 'Classical source'. Returns the table name."""
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {name}")
    ac.psql(f"CREATE TABLE {name} (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, a integer, b integer, citation_ref text, doc jsonb, citation_human text)")
    if index:
        ac.psql(f"CREATE UNIQUE INDEX {name}_nat ON {name} (a, b, id)")
    for a in A_VALUES:
        for b in B_VALUES:
            ac.psql(f"INSERT INTO {name} (chart_id, a, b, citation_ref, doc, citation_human) SELECT '{CHART}'::uuid, {a}, {b}, 'ref.' || g || '@chart={CHART}', "
                    f"'{{\"cls\":[\"x\"]}}'::jsonb, 'Classical source' FROM generate_series(1, {per_cell}) g")
    ac.psql(f"ANALYZE {name}")
    return name


def drop_table(name="kt_dash"):
    ac.psql(f"DROP TABLE IF EXISTS {name}")


def plant(name, set_sql, where_sql):
    """Plant a violation: UPDATE name SET <set_sql> WHERE <where_sql>."""
    ac.psql(f"UPDATE {name} SET {set_sql} WHERE {where_sql}")


class Clock:
    """A driven stand-in for the census wall clock `_chunk_clock`."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def spy_scalar(monkeypatch, rewrite=None, slow_marker=None, slow_secs=2):
    """Wrap the REAL `scalar` (so every statement still runs on the disposable cluster) and record each statement. `rewrite(sql, answer) -> answer` may alter an answer (to fake a plan whose counts do not add up);
    a statement containing `slow_marker` is preceded by `SELECT pg_sleep(slow_secs)`, which a tiny PGOPTIONS statement_timeout cancels (a genuine server-side timeout, not a simulated one)."""
    real = ac.scalar
    calls: list = []

    def fake(sql):
        calls.append(sql)
        if slow_marker is not None and slow_marker in sql:
            return real(f"SELECT pg_sleep({slow_secs}); " + sql)
        out = real(sql)
        return rewrite(sql, out) if rewrite else out
    monkeypatch.setattr(ac, "scalar", fake)
    fake.calls = calls
    return fake


def tiny_timeout(monkeypatch, ms=700):
    monkeypatch.setenv("PGOPTIONS", f"-c statement_timeout={ms}")


def shrink(monkeypatch, min_rows=500, target=2000):
    """Make the 3000-row fixture 'large': the threshold sits below it and the partition target lets the first key column suffice (target=2000) or forces the second (target < 1000)."""
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", min_rows)
    monkeypatch.setattr(ac, "KEYED_PARTITION_TARGET_ROWS", target)


def scope_to_chart(table, chart=CHART):
    ac.set_read_scope({table: dict(where=f"chart_id = '{chart}'::uuid", label="measured chart")})
