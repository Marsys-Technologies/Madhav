"""A5.5f (G7) — the chain replace on a POPULATED chain, as the BUILDER role, on a deployment-faithful mirror.

The round-1 review of PR 3132 (Codex P2, Fable P2-c): the first test file never built windows or verification rows, so it
could not show that the replace copes with everything a real candidate carries. Here the world holds, for the generation,
windows, window memberships, relationship records, record prerequisites, contacts, the event-class coverage partition and
BOTH verification tables (1206 inventory, 1240 window), plus a Moon on-demand coverage partition and a second generation.
The writer's real `snapshot` substep then runs as `data_plane_builder` (the faithful mirror: the principal exists when the
migrations run, PUBLIC EXECUTE revoked), and:

  * what it replaces is the whole chain of (chart, generation) — verification rows included — and what it keeps is the Moon
    partition and every other generation;
  * rebuilding afterwards ends EQUAL to a world built once, fresh;
  * a failure inside the substep, after the deletes, rolls the deletes back (the chain is intact)."""
from __future__ import annotations

import json

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory_verifier as inv_v
from services.gochara_kernel import record_store as rs
from services.gochara_kernel.inventory_store import InventoryStore

from .test_a53_builder_restricted_flow import STUBS
from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN, _world
from .test_a53_window_verification_gate import CLS, SPANS, _boot_p3, _windows
from .test_a53_window_verification_roles import (_consistent_sky, _qualification_policy,  # noqa: F401  (autouse)
                                                 as_role, rworld)

OTHER_GEN = "5.9"
CHAIN_TABLES = ("ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_relationship_record",
                "ka_gochara_record_prerequisite", "ka_gochara_contact", "ka_gochara_eval_window_verification",
                "ka_gochara_search_inventory_verification", "ka_gochara_search_inventory")


def _count(conn, table, generation=GEN, extra=""):
    return conn.execute(f"SELECT count(*) FROM public.{table} WHERE generation = %s {extra}", (generation,)).fetchone()[0]


def _coverage(conn, generation=GEN):
    return conn.execute("SELECT partition_kind, partition_key FROM public.kala_gochara_coverage"
                        " WHERE generation = %s ORDER BY 1, 2", (generation,)).fetchall()


_NATURAL_KEY = ("event_class", "path_id", "rule_version", "occurrence_ordinal", "contact_id", "record_id", "window_id",
                "prerequisite", "ordinal", "body", "relation_kind")


def _rows(conn, table, generation=GEN, drop=()):
    """A table's rows for the generation as comparable JSON, without the columns that legitimately differ between two
    otherwise identical builds (timestamps and build identities), ordered by the table's NATURAL KEY so two builds pair
    row for row (never by digest text, which would pair unlike rows)."""
    rows = []
    for (j,) in conn.execute(f"SELECT to_jsonb(t) FROM public.{table} t WHERE generation = %s", (generation,)).fetchall():
        d = {k: v for k, v in j.items() if not k.endswith("_at") and k not in ("build_id", "created_by") and k not in drop}
        rows.append((tuple(str(d.get(k)) for k in _NATURAL_KEY), json.dumps(d, sort_keys=True)))
    return [r[1] for r in sorted(rows)]


#: Columns that bind a verification row to THIS database's L1 stub identities (the consumed fact and daśā row ids are random
#: per database). They are compared in the same-database check below and left out only of the cross-database one.
_INSTANCE_BOUND = ("input_digest", "derivation_inputs_digest", "rederived_inventory_digest", "inventory_digest", "ledger_digest")


def _state(conn, drop=()):
    s = {t: _rows(conn, t, drop=drop) for t in CHAIN_TABLES}
    s["coverage"] = [c for c in _coverage(conn) if c[0] == "event_class"]       # the Moon survivor is checked on its own
    return s


def _builder(w):
    """The mirror's L1 stubs are owned by the fixture owner: the builder is granted SELECT on them exactly as the
    builder-restricted flow does (production's builder already holds these reads)."""
    for table in STUBS:
        w.conn.execute(f"GRANT SELECT ON public.{table} TO data_plane_builder")
    return as_role(w.conn, "data_plane_builder")


def _persist_inventory_verification(w):
    digest = w.conn.execute("SELECT inventory_digest FROM public.ka_gochara_search_inventory WHERE generation = %s AND event_class = %s",
                            (GEN, CLS)).fetchone()[0]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SELECT public.ka_gochara_lock_global_shared()")
        inv_v.write_verification(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, rederived_digest=digest)


def _populate(w):
    """A candidate carrying everything: windows, memberships, records, prerequisites, contacts, coverage, both verifications."""
    _boot_p3(w)
    _windows(w)                                  # superuser: the builder's window steps + the 1240 rows the job would persist
    _persist_inventory_verification(w)


def _add_survivors(w):
    """Rows the replace must NOT touch: a Moon on-demand partition of this generation and a whole other generation."""
    store = rs.RecordStore(w.conn)
    kala = store.ensure_kala_convention()
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        store.write_moon_coverage(
            chart_id=CHART_ID, generation=GEN, partition_key="moon-q1", convention_id=kala, horizon=(H0, H1),
            resolution=3600.0, relations_searched=["residence"], targets_requested=1, targets_resolved=1,
            state_counts={"searched_complete": 1}, unavailable_inputs={}, unsearched_reason=None, build_id="moon-q1")
        for table in ("ka_gochara_contact", "kala_gochara_coverage"):
            w.conn.execute(f"CREATE TEMP TABLE _s AS SELECT * FROM public.{table} WHERE generation = %s"
                           + (" AND partition_kind = 'event_class'" if table == "kala_gochara_coverage" else "")
                           + " LIMIT 1", (GEN,))
            w.conn.execute("UPDATE _s SET generation = %s", (OTHER_GEN,))
            w.conn.execute(f"INSERT INTO public.{table} SELECT * FROM _s")
            w.conn.execute("DROP TABLE _s")


def test_the_populated_fixture_really_holds_every_table(rworld):
    w = rworld
    _populate(w)
    _add_survivors(w)
    for t in CHAIN_TABLES:
        assert _count(w.conn, t) >= 1, f"{t} is empty — the fixture does not populate it"
    assert _count(w.conn, "ka_gochara_eval_window") >= 1 and _count(w.conn, "ka_gochara_relationship_record") >= 1
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] >= 1       # memberships
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_record_prerequisite").fetchone()[0] >= 1
    assert ("moon_on_demand", "moon-q1") in _coverage(w.conn)
    assert _count(w.conn, "ka_gochara_contact", OTHER_GEN) == 1 and _coverage(w.conn, OTHER_GEN)


def test_the_builder_replaces_a_populated_chain_and_keeps_the_survivors(rworld):
    w = rworld
    _populate(w)
    _add_survivors(w)
    other_before = {t: _rows(w.conn, t, OTHER_GEN) for t in ("ka_gochara_contact",)}
    other_cov_before = _coverage(w.conn, OTHER_GEN)
    with _builder(w):
        w.step("snapshot")                       # THE writer's substep, as the builder, over the populated chain
    for t in ("ka_gochara_eval_window", "ka_gochara_relationship_record", "ka_gochara_contact",
              "ka_gochara_search_inventory_verification", "ka_gochara_eval_window_verification"):
        assert _count(w.conn, t) == 0, f"{t} survived the replace"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_record_prerequisite").fetchone()[0] == 0
    assert _coverage(w.conn) == [("moon_on_demand", "moon-q1")]                      # event-class partitions gone, Moon kept
    assert {t: _rows(w.conn, t, OTHER_GEN) for t in ("ka_gochara_contact",)} == other_before
    assert _coverage(w.conn, OTHER_GEN) == other_cov_before


def test_rebuilding_after_the_builders_replace_equals_what_was_there_and_a_fresh_build(rworld, monkeypatch, tmp_path):
    w = rworld
    _populate(w)
    _add_survivors(w)
    before = _state(w.conn)
    before_loose = _state(w.conn, drop=_INSTANCE_BOUND)
    with _builder(w):
        w.step("snapshot")
    assert _state(w.conn) != before                         # the replace really removed the chain
    _populate(w)                                 # the rebuild: the whole head again, then windows and verification
    # (1) the SAME database: replace-then-rebuild reproduces the chain it replaced, every column
    assert _state(w.conn) == before, "replace then rebuild did not reproduce the original chain"
    # (2) a FRESH database built once (the instance-bound digests excluded, see _INSTANCE_BOUND)
    gen = _world(monkeypatch, tmp_path / "fresh", True)
    fresh = next(gen)
    try:
        # `_world` re-patches the sky with a flat stand-in; put the CONSISTENT sky back (the same function the autouse
        # fixture installs) so the control is built over the same geometry as the world under test
        from datetime import datetime, timezone

        def calc(body, jd, ephe):
            t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=timezone.utc)
            return (195.0 if any(a <= t < b for a, b in SPANS.get(body.lower(), ())) else 15.0), 2
        monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc)
        fresh.result_policy = "window_qualification/1"
        _populate(fresh)
        control = _state(fresh.conn, drop=_INSTANCE_BOUND)
    finally:
        gen.close()
    rebuilt = _state(w.conn, drop=_INSTANCE_BOUND)
    for table in control:
        assert rebuilt[table] == control[table], f"{table}: the rebuilt chain differs from a fresh build"
    assert before_loose == rebuilt
    assert ("moon_on_demand", "moon-q1") in _coverage(w.conn)                         # the survivor is still there


def test_a_failure_inside_the_snapshot_substep_rolls_the_deletes_back(rworld, monkeypatch):
    w = rworld
    _populate(w)
    before = _state(w.conn)
    assert all(before[t] for t in CHAIN_TABLES)

    def boom(self, **kw):
        raise RuntimeError("injected failure after the chain was deleted")
    monkeypatch.setattr(InventoryStore, "insert_snapshot", boom)
    with _builder(w):
        with pytest.raises(RuntimeError, match="injected failure"):
            w.step("snapshot")
    assert _state(w.conn) == before, "the deletes were not rolled back with the failed substep"
