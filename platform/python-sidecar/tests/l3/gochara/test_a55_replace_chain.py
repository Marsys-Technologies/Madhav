"""A5.5f (gap G7) — a rebuild REPLACES the whole unsealed chart x generation output chain; it never accretes.

Two tiers.

  * no database: the delete order and scope, the sealed refusal, the contact-row comparison, and the plan shape
    (the replace sits in the `snapshot` substep, before every substep that writes chain rows);
  * the writer's OWN substeps on the real migration chain (the A5.3 AM-5 harness): the sky-event substrate is built once
    into a template database and cloned per test; manifest, snapshot, inventory, coverage and record grains are production
    code, the Swiss library is the pinned corpus (conftest). Every scenario compares the rebuilt state with a FRESH build
    over the same horizon: a rebuild must equal a first build, byte for byte on contact ids and bounds.

The reproduction behind it (2026-10-04, Stream A): two classes share one physical contact (18 of the 26 classes share
Saturn-in-the-7th); rebuilding both at a longer horizon left the contact's end at the OLD clipped value, because the
contact insert was `ON CONFLICT DO NOTHING` and the class replace keeps a contact another class still references."""
from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import contact_certify
from services.gochara_kernel import record_store as rs
from services.gochara_kernel.rule_registry import RuleRegistryStore

from . import test_a53_inventory as base
from .conftest import EPHE_PATH, _PROBLEMS, assert_real_ephemeris
from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database
from .test_a53_record_store import _RecordingConn, _tables_deleted

GEN = writer_mod.GENERATION
UTC = timezone.utc
Y = lambda m, d: datetime(2025, m, d, tzinfo=UTC)          # noqa: E731
SHORT = (Y(1, 1), Y(1, 20))      # mars / mercury / venus residence still running at the end: end-clipped contacts
LONG = (Y(1, 1), Y(3, 1))
LEFT = (Y(1, 10), Y(2, 1))       # start-clipped contacts (their identity falls back to the clipped t_in)
FULLL = (Y(1, 1), Y(2, 1))
CLASSES = ("marriage", "romantic_start")          # they share contacts (same agent / relation / target)
PATHS = ("P2", "P3")                              # P1 cannot pass on the stubbed L1 (the A5.3 timing harness measured it); P4 yields nothing here


# ── no database ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_generation_chain_delete_is_dependency_ordered_and_chart_generation_scoped():
    conn = _RecordingConn()
    out = rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
    assert _tables_deleted(conn) == ["ka_gochara_eval_window",          # membership cascades with it
                                     "ka_gochara_relationship_record",  # prerequisites cascade with it
                                     "ka_gochara_contact",              # ALL of the generation's contacts
                                     "kala_gochara_coverage"]           # last: records / windows reference it
    deletes = [st for st in conn.statements if st.startswith("DELETE FROM public.")]
    assert all("chart_id = %s AND generation = %s" in st for st in deletes)
    contact_delete = next(st for st in deletes if "ka_gochara_contact" in st)
    assert "NOT EXISTS" not in contact_delete and "ANY(" not in contact_delete     # orphans and shared contacts go too
    coverage_delete = next(st for st in deletes if "kala_gochara_coverage" in st)
    assert "partition_kind = 'event_class'" in coverage_delete                    # Moon query identities are kept
    assert set(out) == {"windows", "records", "contacts", "coverage"}


def test_a_sealed_generation_is_refused_before_any_delete():
    conn = _RecordingConn(sealed=True)
    with pytest.raises(rs.SealedGenerationError, match="SEALED"):
        rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
    assert _tables_deleted(conn) == []
    assert any("ka_gochara_generation_is_sealed" in st for st in conn.statements)    # how the code knows


def test_contact_row_diffs_name_every_differing_column():
    row = ("po-1", 1, "conv", "mars", "residence", Y(1, 1), Y(1, 20), None, "clipped_truncated", None, None, None,
           {"truncated": True})
    assert rs._contact_row_diffs(row, row) == []
    changed = list(row)
    changed[6] = Y(1, 21)
    diffs = rs._contact_row_diffs(row, tuple(changed))
    assert len(diffs) == 1 and diffs[0].startswith("t_out:")
    assert rs._contact_row_diffs(None, row) == ["row absent after insert"]
    # the accuracy columns are REAL: the database's float4 rounding of the derived value is NOT a disagreement …
    exact = 1.0 / 3600.0
    with_real = list(row)
    with_real[9], with_real[10] = 0.00027777778, 1e-9           # what the REAL column hands back (float4 text)
    derived_real = list(row)
    derived_real[9], derived_real[10] = exact, 1e-9
    assert rs._contact_row_diffs(tuple(with_real), tuple(derived_real)) == []
    # … a genuinely different accuracy still is
    derived_real[9] = exact * 1.5
    assert [d.split(":")[0] for d in rs._contact_row_diffs(tuple(with_real), tuple(derived_real))] == ["delta_lambda"]
    one_more = list(changed)
    one_more[7] = Y(1, 5)
    assert [d.split(":")[0] for d in rs._contact_row_diffs(row, tuple(one_more))] == ["t_out", "t_exact"]


def test_the_replace_is_in_the_snapshot_substep_and_only_there():
    src = inspect.getsource(writer_mod.GocharaV5Writer._run_inventory_phase)
    assert src.count("delete_generation_chain(") == 1
    snap = src[src.index("if step.key == SNAPSHOT_SUBSTEP:"):src.index("event_class = step.key.split")]
    assert "delete_generation_chain(" in snap
    assert "delete_class_chain" not in snap
    whole = inspect.getsource(writer_mod)
    assert whole.count("delete_generation_chain(") == 1


def test_the_snapshot_precedes_every_substep_that_writes_chain_rows():
    plan = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(ContextSpec(
        asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None, dry_run=True, config={"chart_id": CHART_ID}))]
    assert len(plan) == 298
    snap = plan.index(writer_mod.SNAPSHOT_SUBSTEP)
    writers = [i for i, k in enumerate(plan) if k.startswith(("inventory:", "coverage:", "record:", "window:", "verify:"))]
    assert writers and min(writers) > snap
    assert plan.index(writer_mod.MANIFEST_SUBSTEP) < snap


# ── the writer's own substeps on the real migration chain ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def template():
    if _PROBLEMS:
        assert_real_ephemeris()
        pytest.skip("pinned .se1 corpus unavailable")
    import psycopg
    admin, name, dsn = create_am5_database("a55rc")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        RuleRegistryStore(conn).seed()
        w = writer_mod.GocharaV5Writer()
        for key in [writer_mod.CONVENTION_SUBSTEP] + [f"{writer_mod.BODY_SUBSTEP_PREFIX}{b}"
                                                      for b in writer_mod.SUBSTRATE_BODIES]:
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="tpl", db_conn=conn, dry_run=False,
                              config={"chart_id": CHART_ID, "horizon": LONG, "ephe_path": EPHE_PATH})
            with conn.transaction():
                w.run_substep(ctx, SubStep(key=key, label=key))
    finally:
        conn.close()
    yield admin, name, dsn
    drop_am5_database(admin, name)


class _World:
    """A clone of the template with a `step(key, horizon)` that runs one real substep in its own transaction."""

    def __init__(self, template):
        import psycopg
        from psycopg.conninfo import make_conninfo
        self.admin, tpl, dsn = template
        self.name = f"{base.DB_PREFIX}a55c_{uuid.uuid4().hex[:8]}"
        self.admin.execute(f'CREATE DATABASE "{self.name}" TEMPLATE "{tpl}"')
        self.conn = psycopg.connect(make_conninfo(dsn, dbname=self.name), autocommit=True, connect_timeout=3)
        self._w = writer_mod.GocharaV5Writer()

    def step(self, key, horizon):
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-1", db_conn=self.conn, dry_run=False,
                          config={"chart_id": CHART_ID, "horizon": horizon, "ephe_path": EPHE_PATH})
        with self.conn.transaction():
            return self._w.run_substep(ctx, SubStep(key=key, label=key))

    def build(self, horizon, classes=CLASSES, paths=PATHS, head=True):
        """One build: manifest + snapshot (the plan's head), then each class chain in plan order."""
        if head:
            self.step(writer_mod.MANIFEST_SUBSTEP, horizon)
            self.step(writer_mod.SNAPSHOT_SUBSTEP, horizon)
        for cls in classes:
            self.step(f"inventory:{cls}", horizon)
            self.step(f"coverage:{cls}", horizon)
            for p in paths:
                self.step(f"record:{cls}:{p}", horizon)

    def state(self):
        c = self.conn
        return {
            "contacts": sorted(c.execute(
                "SELECT contact_id::text, t_in, t_out, t_exact, solver_method, coverage::text"
                " FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchall()),
            "records": c.execute(
                "SELECT event_class, path_id, count(*) FROM public.ka_gochara_relationship_record"
                " WHERE generation = %s GROUP BY 1, 2 ORDER BY 1, 2", (GEN,)).fetchall(),
            "coverage": c.execute(
                "SELECT partition_key, lower(completed_horizon), upper(completed_horizon)"
                " FROM public.kala_gochara_coverage WHERE generation = %s AND partition_kind = 'event_class'"
                " ORDER BY 1", (GEN,)).fetchall(),
        }

    def close(self):
        self.conn.close()
        assert self.name.startswith(base.DB_PREFIX), self.name
        self.admin.execute(f'DROP DATABASE IF EXISTS "{self.name}" WITH (FORCE)')


@pytest.fixture()
def world(template):
    w = _World(template)
    try:
        yield w
    finally:
        w.close()


@pytest.fixture(scope="module")
def fresh(template):
    """FRESH-build state per horizon, built once per module and cached: the control every rebuild must equal."""
    cache: dict = {}
    worlds: list = []

    def get(horizon, classes=CLASSES):
        key = (horizon, classes)
        if key not in cache:
            w = _World(template)
            worlds.append(w)
            w.build(horizon, classes=classes)
            cache[key] = w.state()
        return cache[key]

    yield get
    for w in worlds:
        w.close()


def _same(got, want, what):
    assert got["records"] == want["records"], f"{what}: records differ"
    assert got["coverage"] == want["coverage"], f"{what}: coverage partitions differ"
    gc, wc = {c[0]: c for c in got["contacts"]}, {c[0]: c for c in want["contacts"]}
    assert set(gc) == set(wc), (f"{what}: contact ids differ — extra {sorted(set(gc) - set(wc))}, "
                                f"missing {sorted(set(wc) - set(gc))}")
    stale = {k: (gc[k][1:3], wc[k][1:3]) for k in gc if gc[k] != wc[k]}
    assert not stale, f"{what}: {len(stale)} contact(s) kept stale columns (stored vs fresh): {list(stale.items())[:2]}"


def test_a_fresh_build_has_shared_end_clipped_contacts(fresh):
    """The scenario is real: contacts exist, and at least one is end-clipped at the SHORT horizon's end (otherwise the
    extension test below would prove nothing)."""
    s = fresh(SHORT)
    assert len(s["contacts"]) >= 5 and s["records"]
    assert any(c[2] == SHORT[1] for c in s["contacts"]), "no contact is clipped at the horizon end"
    assert {r[0] for r in s["records"]} == set(CLASSES)


def test_extending_the_horizon_moves_every_bound_the_two_classes_share(world, fresh):
    """THE reproduction: two classes share a contact; SHORT then LONG must equal a fresh LONG."""
    world.build(SHORT)
    before = world.state()
    world.build(LONG)
    after = world.state()
    assert before != after
    _same(after, fresh(LONG), "SHORT then LONG")


def test_narrowing_the_horizon_leaves_no_contact_beyond_the_new_end(world, fresh):
    world.build(LONG)
    world.build(SHORT)
    after = world.state()
    assert not [c for c in after["contacts"] if c[2] is not None and c[2] > SHORT[1]]
    _same(after, fresh(SHORT), "LONG then SHORT")


def test_a_later_start_then_an_earlier_start_leaves_no_extra_overlapping_contact(world, fresh):
    """Start-clipped contacts are identified by their clipped t_in, so a changed start makes a NEW contact id: the old
    one must not survive beside it (an overlapping duplicate would still pass a union-based certification)."""
    world.build(LEFT)
    world.build(FULLL)
    _same(world.state(), fresh(FULLL), "LEFT then FULL")


def test_an_orphan_contact_from_a_crashed_run_is_replaced_not_kept(world, fresh):
    """A crash after the contact substeps committed but before their records: contacts no record references."""
    world.build(SHORT)
    with world.conn.transaction():
        world.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE generation = %s", (GEN,))
    orphans = world.conn.execute(
        "SELECT count(*) FROM public.ka_gochara_contact c WHERE generation = %s AND NOT EXISTS"
        " (SELECT 1 FROM public.ka_gochara_relationship_record r WHERE r.contact_id = c.contact_id)", (GEN,)).fetchone()[0]
    assert orphans >= 5
    world.build(LONG)
    _same(world.state(), fresh(LONG), "orphans then LONG")


def test_a_sealed_generation_is_not_replaced(world):
    world.build(SHORT)
    before = world.state()
    mid = world.conn.execute("SELECT manifest_id FROM public.kala_gochara_publication"
                             " WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    with world.conn.transaction():           # the sealed world is set up behind the guards — it is the world under test
        world.conn.execute("SET LOCAL session_replication_role = replica")
        world.conn.execute("INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)"
                           " VALUES (%s::uuid, %s, %s::uuid)", (CHART_ID, GEN, mid))
    with pytest.raises(rs.SealedGenerationError, match="SEALED"):
        world.step(writer_mod.SNAPSHOT_SUBSTEP, LONG)
    assert world.state() == before, "a sealed generation's chain was touched"


def test_resume_within_one_build_keeps_what_its_earlier_substeps_wrote(world, fresh):
    """The orchestrator skips completed substeps on a resume (`completed_keys`), snapshot included, so the replace never
    re-runs: the first class's rows survive while the second class is built, and the result equals one uninterrupted build.
    Then a FRESH re-run (no completed keys) replaces and rebuilds everything: also equal."""
    world.build(SHORT, classes=(CLASSES[0],))                       # build 1: head (manifest, snapshot) + class one …
    first = world.state()
    assert {r[0] for r in first["records"]} == {CLASSES[0]}          # … then the timeout
    world.build(SHORT, classes=(CLASSES[1],), head=False)           # the resume: completed head skipped, class two runs
    resumed = world.state()
    assert {r[0] for r in resumed["records"]} == set(CLASSES)
    assert {c[0] for c in first["contacts"]} <= {c[0] for c in resumed["contacts"]}      # nothing of class one was wiped
    assert [r for r in resumed["records"] if r[0] == CLASSES[0]] == [r for r in first["records"]]
    _same(resumed, fresh(SHORT), "resumed build")
    world.build(SHORT)                                               # a fresh full re-run: replaces, no accretion
    _same(world.state(), fresh(SHORT), "fresh re-run")


def test_a_conflicting_contact_row_is_refused_by_name_not_kept(world):
    world.build(SHORT, classes=(CLASSES[0],))
    conn = world.conn
    row = conn.execute("SELECT chart_id::text, generation, contact_id::text, physical_object_id::text,"
                       " occurrence_ordinal, convention_id, body, relation_kind, t_in, t_out, t_exact, solver_method,"
                       " delta_lambda, delta_t, precision_regime, coverage::text FROM public.ka_gochara_contact"
                       " WHERE generation = %s AND t_out IS NOT NULL ORDER BY contact_id LIMIT 1", (GEN,)).fetchone()
    store = rs.RecordStore(conn)
    with conn.transaction():
        store._insert_contact_row(tuple(row))                         # the identical row again: a no-op, not an error
    moved = list(row)
    moved[9] = row[9] + timedelta(days=3)                              # the same contact, a different end
    with pytest.raises(rs.ContactRowMismatch, match=r"t_out: stored .* != derived"):
        with conn.transaction():
            store._insert_contact_row(tuple(moved))
    kept = conn.execute("SELECT t_out FROM public.ka_gochara_contact WHERE contact_id = %s::uuid", (row[2],)).fetchone()[0]
    assert kept == row[9]


# ── what the independent verification catches (the steward's question) ─────────────────────────────────────────────

def _position_at():
    jd0 = 2440587.5

    def position_at(body, t):
        lon, retflag = writer_mod.calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + jd0, EPHE_PATH)
        assert retflag & 2
        return lon
    position_at.cache_key = ("swiss", EPHE_PATH)
    return position_at


def _certify_problems(conn, horizon):
    """The REAL comparison `certify_contact_geometry` applies, per (body, relation, target) that has ledger contacts:
    reconstruct the intervals from the ephemeris and compare with the ledger's union, both clipped to the horizon.
    (The whole-class certification also demands every obligation the stub chain never materialises — P1 cannot pass on
    the stubbed L1 — so it cannot serve as a clean baseline here; the comparison function itself is the real one.)"""
    lo, hi = horizon
    pos = _position_at()
    ledger: dict = {}
    for body, rel, target, t_in, t_out, dl in conn.execute(
            "SELECT c.body, c.relation_kind, o.canonical_target, c.t_in, c.t_out, c.delta_lambda"
            " FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
            " ON o.physical_object_id = c.physical_object_id WHERE c.generation = %s", (GEN,)).fetchall():
        ledger.setdefault((body, rel, target), []).append(
            (max(t_in, lo), hi if t_out is None else min(t_out, hi), contact_certify.bm.accuracy_degrees(dl)))
    problems = []
    for (body, rel, target), have in sorted(ledger.items()):
        want = contact_certify.expected_intervals(pos, body, rel, target, lo, hi)
        problems += contact_certify.compare_contact_sets(pos, body, rel, target, want, sorted(have), lo, hi)
    return problems


def test_certification_of_a_correct_build_agrees_for_every_materialised_contact(world):
    world.build(LONG)
    assert _certify_problems(world.conn, LONG) == []


def test_certification_catches_a_stale_end_after_an_extension_loudly(world):
    """The extension defect: a contact still ending where the SHORT horizon clipped it, judged over LONG, is refused."""
    world.build(LONG)
    with world.conn.transaction():
        world.conn.execute("SET LOCAL session_replication_role = replica")
        n = world.conn.execute(
            "UPDATE public.ka_gochara_contact SET t_out = %s WHERE generation = %s AND t_in < %s AND t_out > %s",
            (SHORT[1], GEN, SHORT[1], SHORT[1])
        ).rowcount
    assert n >= 1
    problems = _certify_problems(world.conn, LONG)
    assert problems and all("is not a reconstructed interval" in p or "is not in the ledger" in p for p in problems)


def test_certification_does_NOT_catch_a_stale_end_beyond_a_narrowed_horizon(world):
    """The limit, stated by a test rather than a hope: the comparison clips the ledger to the class's horizon, so a
    contact whose stale end lies BEYOND the narrowed horizon passes silently. Only the chain replace prevents it."""
    world.build(SHORT)
    with world.conn.transaction():
        world.conn.execute("SET LOCAL session_replication_role = replica")
        n = world.conn.execute(
            "UPDATE public.ka_gochara_contact SET t_out = %s WHERE generation = %s AND t_out = %s",
            (SHORT[1] + timedelta(days=40), GEN, SHORT[1])).rowcount
    assert n >= 1
    assert _certify_problems(world.conn, SHORT) == []
