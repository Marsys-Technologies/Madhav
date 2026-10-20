"""J-4c F-LEANNESS — the record store sends each write group in ONE network round trip (libpq pipeline mode).

THE FINDING (SR-J3D-LEANNESS-ROW, J-3d report): the six tiny classes (<= 38 intervals) cost 30-320 s each against ~1,400 s for a large
class, because a class's cost is not its interval count but the records its contacts mint: ~2,000 records, 14 statements each, every
statement its own round trip to a remote database. The statements are unchanged; this tier proves the claims that make the batching safe.

CLAIMS (each has ONE oracle below; the classical rules do not apply — this is transport, and the oracle is "the sequential path"):

  C1  a pipelined grain stores byte-identical rows to the one-statement-at-a-time grain (contact chain, records, prerequisites with their
      results and the admission state the real F5 finalisation checks at COMMIT);
  C2  the named refusals still fire with their OWN error and before any dependent write (IdentityCollisionError for an object whose
      natural key is taken by another id; ContactRowMismatch for a differing stored contact) — which is why the object and the identity
      are separate write groups;
  C3  the batching is really in effect: no statement of the per-record chain travels alone, and a record costs at most five write groups;
  C4  a connection without `pipeline()` (or a libpq without pipeline support) runs the same chain sequentially to the same rows;
  C5  the P1 anchor-column catalogue probe is read once per store, not once per record, and a fresh store reads it again;
  C7  the orchestrator's own connection shape (not autocommit, dict rows, wrapped to tuple rows by `native_connection`) pipelines too, and the
      real F5 finalisation at COMMIT accepts what the pipelined groups wrote.

The window store's single-group claim is in test_a53_j4c_leanness_window_pipeline.py (it needs that module's fixtures)."""
from __future__ import annotations

import contextlib
import json
import uuid
from datetime import timedelta

import pytest

from services.gochara_kernel import record_store as rs
from services.gochara_kernel.substrate import IdentityCollisionError, physical_object_id

from .test_a53_record_store import (CHART_ID, DAY, PG_GEN, PG_GEN_P4, T0,  # noqa: F401  (fixtures: pg, _pg_dsn)
                                    _pg_dsn, _pg_p1_run, _pg_p4_run, _sky_convention_id, pg)

# every statement of the per-record chain (writes and their read-backs), by the text that identifies it
CHAIN = (
    "INSERT INTO public.ka_gochara_physical_object", "SELECT physical_object_id FROM public.ka_gochara_physical_object",
    "INSERT INTO public.ka_gochara_contact_identity", "SELECT physical_object_id, occurrence_ordinal FROM public.ka_gochara_contact_identity",
    "INSERT INTO public.ka_gochara_contact (", "SELECT physical_object_id, occurrence_ordinal, convention_id, body, relation_kind",
    "INSERT INTO public.ka_gochara_relationship_record", "SELECT chart_id::text, generation, event_class, path_id, rule_version",
    "INSERT INTO public.ka_gochara_record_prerequisite", "SELECT predicate_id, predicate_rule_version FROM public.ka_gochara_record_prerequisite",
    "UPDATE public.ka_gochara_record_prerequisite", "SELECT result FROM public.ka_gochara_record_prerequisite",
    "UPDATE public.ka_gochara_relationship_record SET admission_state",
)


class _Counting:
    """Delegates to a real connection; logs every statement with whether it ran inside a pipeline group, and counts the groups."""

    def __init__(self, conn):
        self._conn = conn
        self.log: list[tuple[str, bool]] = []
        self.groups = 0
        self._depth = 0

    def execute(self, query, params=None, **kwargs):
        self.log.append((" ".join(str(query).split()), self._depth > 0))
        return self._conn.execute(query, params, **kwargs)

    @contextlib.contextmanager
    def pipeline(self):
        self.groups += 1
        self._depth += 1
        try:
            with self._conn.pipeline():
                yield
        finally:
            self._depth -= 1

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def chain_statements(self):
        """The per-record chain's statements of the GRAIN only: the log from the grain's own delete on (the sky-substrate seeding that
        precedes it runs the same physical-object SQL through another store and is not under test)."""
        start = next(i for i, (sql, _g) in enumerate(self.log) if sql.startswith("DELETE FROM public.ka_gochara_relationship_record"))
        return [(sql, grouped) for sql, grouped in self.log[start:] if sql.startswith(CHAIN)]


class _NoPipeline:
    """A connection object with no `pipeline()` at all (a unit-test fake, or a driver without it)."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        if name == "pipeline":
            raise AttributeError(name)
        return getattr(self._conn, name)


_TABLES = {
    "contact": "SELECT to_jsonb(t) - 'created_at' FROM public.ka_gochara_contact t WHERE generation = %(g)s",
    "identity": "SELECT to_jsonb(t) - 'created_at' FROM public.ka_gochara_contact_identity t WHERE contact_id IN"
               " (SELECT contact_id FROM public.ka_gochara_contact WHERE generation = %(g)s)",
    "object": "SELECT to_jsonb(t) - 'created_at' FROM public.ka_gochara_physical_object t WHERE physical_object_id IN"
              " (SELECT physical_object_id FROM public.ka_gochara_contact WHERE generation = %(g)s)",
    "record": "SELECT to_jsonb(t) - 'created_at' FROM public.ka_gochara_relationship_record t WHERE generation = %(g)s",
    "prerequisite": "SELECT to_jsonb(t) FROM public.ka_gochara_record_prerequisite t WHERE generation = %(g)s",
}


def fingerprint(conn, generation) -> dict[str, list[str]]:
    """Every stored column of every chain row of the generation, minus the DB clock, sorted: the byte-level state."""
    return {name: sorted(json.dumps(r[0], sort_keys=True, default=str) for r in conn.execute(sql, {"g": generation}).fetchall())
            for name, sql in _TABLES.items()}


P1_RUNNING = {"venus": [{"start_iso": T0, "end_iso": T0 + 300 * DAY}]}
P1_NOT_RUNNING = {"venus": [{"start_iso": T0 + 500 * DAY, "end_iso": T0 + 600 * DAY}]}
SCENARIOS = [
    # (id, runner, generation, expected admission states) — states chosen so the result UPDATE and the admission UPDATE both matter
    ("p1_admitted", lambda c: _pg_p1_run(c, P1_RUNNING, "venus"), PG_GEN, {"admitted"}),
    ("p1_not_admitted", lambda c: _pg_p1_run(c, P1_NOT_RUNNING, "venus"), PG_GEN, {"not_admitted"}),
    ("p4_double_transit", lambda c: _pg_p4_run(c, ["jupiter", "saturn"]), PG_GEN_P4, {"admitted"}),
]


@pytest.mark.parametrize("name,run,generation,states", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_c1_a_pipelined_grain_stores_the_rows_the_sequential_grain_stores(pg, monkeypatch, name, run, generation, states):
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", False)
    run(pg)                                                       # the one-statement-at-a-time chain: the oracle
    sequential = fingerprint(pg, generation)
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", True)
    counting = _Counting(pg)
    run(counting)                                                 # the same grain, replaced and rebuilt with batched groups
    assert counting.groups > 0, "the pipelined run never entered a pipeline group — the comparison would prove nothing"
    batched = fingerprint(pg, generation)
    assert sequential["record"] and sequential["prerequisite"] and sequential["contact"], "no rows: the comparison is vacuous"
    for table in sequential:
        assert batched[table] == sequential[table], f"{name}: {table} rows differ between the pipelined and the sequential chain"
    admission = {json.loads(r)["admission_state"] for r in batched["record"]}
    assert admission == states, f"{name}: the scenario no longer reaches {states} (got {admission})"


def test_c2_an_object_collision_raises_its_own_error_before_the_identity_is_written(pg):
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(pg).seed()
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(pg)
        poid = physical_object_id(body="saturn", relation_kind="residence", canonical_target="span:9", convention_id=sky_cid)
        rival = str(uuid.uuid4())
        assert rival != str(poid.uuid)
        # the natural key of the derived object is TAKEN by another id — the identity bytes collide
        pg.execute("INSERT INTO public.ka_gochara_physical_object (physical_object_id, body, relation_kind, canonical_target,"
                   " convention_id) VALUES (%s::uuid, %s, %s, %s, %s)",
                   (rival, rs.DB_BODY.get(poid.body, poid.body.lower()), poid.relation_kind, poid.canonical_target, poid.convention_id))
    contact_id = uuid.uuid4()
    store = rs.RecordStore(_Counting(pg))
    with pytest.raises(IdentityCollisionError, match="physical object"):
        with pg.transaction():
            pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            store._ensure_object_and_identity(poid, contact_id, 1)
    assert pg.execute("SELECT count(*) FROM public.ka_gochara_contact_identity WHERE contact_id = %s::uuid",
                      (str(contact_id),)).fetchone()[0] == 0, "the identity was written although the object check had to refuse first"


def test_c2_a_differing_stored_contact_is_refused_by_name_under_the_pipelined_group(pg):
    _pg_p4_run(pg, ["jupiter", "saturn"])
    row = pg.execute("SELECT chart_id::text, generation, contact_id::text, physical_object_id::text, occurrence_ordinal,"
                     " convention_id, body, relation_kind, t_in, t_out, t_exact, solver_method, delta_lambda, delta_t,"
                     " precision_regime, coverage::text FROM public.ka_gochara_contact WHERE generation = %s"
                     " ORDER BY contact_id LIMIT 1", (PG_GEN_P4,)).fetchone()
    assert row is not None
    mutated = list(row)
    mutated[9] = row[9] + timedelta(days=2)                      # t_out later by two days
    store = rs.RecordStore(_Counting(pg))
    with pytest.raises(rs.ContactRowMismatch, match="t_out"):
        with pg.transaction():
            pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            store._insert_contact_row(tuple(mutated))
    kept = pg.execute("SELECT t_out FROM public.ka_gochara_contact WHERE contact_id = %s::uuid", (row[2],)).fetchone()[0]
    assert kept == row[9], "the stored contact was overwritten"


def test_c3_no_statement_of_the_per_record_chain_travels_alone(pg):
    counting = _Counting(pg)
    counts, _rows = _pg_p4_run(counting, ["jupiter", "saturn"])
    assert counts["records"] == 2 and counts["contacts"] == 2
    chain = counting.chain_statements()
    assert chain, "no chain statement was observed — the oracle is blind"
    alone = [sql[:90] for sql, grouped in chain if not grouped]
    assert not alone, f"{len(alone)} per-record statement(s) were sent as their own round trip: {alone[:3]}"
    # object, identity, contact | record (+ prerequisites + read-backs) | one result group per prerequisite (P4 has one): at most 5 per record
    assert 0 < counting.groups <= 5 * counts["records"], f"{counting.groups} write groups for {counts['records']} records"


def test_c4_a_connection_without_pipeline_runs_the_same_chain_to_the_same_rows(pg, monkeypatch):
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", False)
    _pg_p4_run(pg, ["jupiter", "saturn"])
    sequential = fingerprint(pg, PG_GEN_P4)
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", True)             # enabled, but the connection cannot do it
    bare = _NoPipeline(pg)
    assert not hasattr(bare, "pipeline")
    _pg_p4_run(bare, ["jupiter", "saturn"])
    assert fingerprint(pg, PG_GEN_P4) == sequential and sequential["record"]


def test_c4_a_libpq_without_pipeline_support_falls_back_the_same_way(pg, monkeypatch):
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", False)
    _pg_p4_run(pg, ["jupiter", "saturn"])
    sequential = fingerprint(pg, PG_GEN_P4)
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", True)
    monkeypatch.setattr(rs, "_pipeline_supported", lambda: False)
    counting = _Counting(pg)
    _pg_p4_run(counting, ["jupiter", "saturn"])
    assert counting.groups == 0, "a libpq that cannot pipeline must never be asked to"
    assert fingerprint(pg, PG_GEN_P4) == sequential


def test_c5_the_anchor_column_probe_is_read_once_per_store(pg):
    counting = _Counting(pg)
    counts, _ = _pg_p4_run(counting, ["jupiter", "saturn"])
    assert counts["records"] == 2
    probes = [sql for sql, _g in counting.log if "FROM pg_attribute" in sql and "ka_gochara_relationship_record" in sql]
    assert len(probes) == 1, f"the catalogue was read {len(probes)} times for 2 records in one store"
    fresh = rs.RecordStore(counting)
    assert fresh.p1_anchor_columns_available() is True and fresh.p1_anchor_columns_available() is True
    probes = [sql for sql, _g in counting.log if "FROM pg_attribute" in sql and "ka_gochara_relationship_record" in sql]
    assert len(probes) == 2, "a fresh store (the next substep) must read the applied schema again, not inherit a stale answer"


def test_c7_the_orchestrators_connection_shape_pipelines_and_stores_the_same_rows(_pg_dsn, monkeypatch):
    import psycopg
    from psycopg.rows import dict_row

    from services.gochara_kernel.native_conn import native_connection

    raw = psycopg.connect(_pg_dsn, autocommit=False, row_factory=dict_row, connect_timeout=3)   # as the runner hands it to a writer
    try:
        monkeypatch.setattr(rs, "PIPELINE_ENABLED", False)
        _pg_p4_run(native_connection(raw), ["jupiter", "saturn"])
        raw.commit()                                              # the deferred F5 finalisation runs here
        sequential = fingerprint(native_connection(raw), PG_GEN_P4)
        raw.commit()
        assert sequential["record"]

        monkeypatch.setattr(rs, "PIPELINE_ENABLED", True)
        counting = _Counting(native_connection(raw))
        _pg_p4_run(counting, ["jupiter", "saturn"])
        raw.commit()                                              # ... and accepts the pipelined groups' rows
        assert counting.groups > 0 and not [s for s, grouped in counting.chain_statements() if not grouped]
        assert fingerprint(native_connection(raw), PG_GEN_P4) == sequential
        raw.commit()
    finally:
        raw.close()
