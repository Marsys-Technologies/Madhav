"""A5.5f (G7) — a rebuild REPLACES the whole unsealed candidate chart x generation output chain; it never accretes.

THE CONTRACT these tests pin: every dispatch of the asset is a WHOLE-BUILD REPLAY. The orchestrator drives the full plan on
every dispatch (it calls `_drive_substeps` without `completed_keys`), so the `snapshot` substep always runs, always before any
substep that writes chain rows, and a failed build restarts from zero on retry. There is no resume. The replace therefore lives
in the snapshot substep; a head-skipping invocation (harness, CLI, a future resume) is not a supported mode and the horizon
guard refuses one that would mix horizons.

Two tiers.

  * no database: the delete order and scope, the sealed and candidate-only refusals, the contact-row comparison, and the
    plan shape (the snapshot precedes every chain-writing substep);
  * the writer's OWN substeps on the real migration chain (the A5.3 AM-5 harness): the sky-event substrate is built once into
    a template database and cloned per test; manifest, snapshot, inventory, coverage and record grains are production code, the
    Swiss library is the pinned corpus (conftest). Every scenario compares the rebuilt state with a FRESH build over the same
    horizon: a rebuild must equal a first build, byte for byte on contact ids and bounds. The populated-chain, builder-role case
    (windows, memberships, prerequisites, both verification tables) is in test_a55_replace_chain_populated.py.

The reproduction behind it (2026-10-04, Stream A): two classes share one physical contact (18 of the 26 classes share
Saturn-in-the-7th); rebuilding both at a longer horizon left the contact's end at the OLD clipped value, because the
contact insert was `ON CONFLICT DO NOTHING` and the class replace keeps a contact another class still references."""
from __future__ import annotations

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
from .test_a53_record_store import _tables_deleted

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

class _Rec:
    """Records every statement; answers the sealed probe and the candidate-manifest lookup; every DELETE reports a rowcount."""

    def __init__(self, sealed=False, status="candidate", manifest=True):
        self.sealed, self.status, self.manifest = sealed, status, manifest
        self.statements: list[str] = []

    def execute(self, sql, params=None):
        flat = " ".join(sql.split())
        self.statements.append(flat)
        conn = self

        class _R:
            rowcount = 1

            def fetchone(self_inner):
                if "ka_gochara_generation_is_sealed" in flat:
                    return (conn.sealed,)
                if "FROM kala_gochara_publication" in flat:
                    return (uuid.uuid4(), conn.status) if conn.manifest else None
                return None

            def fetchall(self_inner):
                return []
        return _R()


def test_generation_chain_delete_is_dependency_ordered_and_chart_generation_scoped():
    conn = _Rec()
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


def test_a_sealed_generation_is_refused_first_and_by_the_new_delete():
    conn = _Rec(sealed=True)
    with pytest.raises(rs.SealedGenerationError, match=r"generation chain replace: .*SEALED"):
        rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
    assert _tables_deleted(conn) == []
    assert any("ka_gochara_generation_is_sealed" in st for st in conn.statements)    # how the code knows


def test_only_a_candidate_manifest_may_be_replaced():
    """Unsealed is not enough: a published-but-unsealed manifest is refused too, and so is a generation with no manifest."""
    from services.gochara_kernel import ledger
    for status in ("published", "superseded", "rolled_back"):
        conn = _Rec(status=status)
        with pytest.raises(ledger.PublishedGenerationRefusal, match="not 'candidate'"):
            rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
        assert _tables_deleted(conn) == [], status
    conn = _Rec(manifest=False)
    with pytest.raises(ValueError, match="no manifest"):
        rs.RecordStore(conn).delete_generation_chain(chart_id=CHART_ID, generation="5.0")
    assert _tables_deleted(conn) == []


_ROW = ("po-1", 1, "conv", "mars", "residence", Y(1, 1), Y(1, 20), Y(1, 5), "swiss_refined", 0.00027777778, 1e-9, "regime",
        {"truncated": False})
_I = {n: i for i, n in enumerate(rs._CONTACT_ROW_COLUMNS)}


def test_contact_row_diffs_name_every_differing_column():
    assert rs._contact_row_diffs(_ROW, _ROW) == []
    changed = list(_ROW)
    changed[_I["t_out"]] = Y(1, 21)
    diffs = rs._contact_row_diffs(_ROW, tuple(changed))
    assert len(diffs) == 1 and diffs[0].startswith("t_out:")
    assert rs._contact_row_diffs(None, _ROW) == ["row absent after insert"]
    two = list(changed)
    two[_I["t_exact"]] = Y(1, 6)
    assert [d.split(":")[0] for d in rs._contact_row_diffs(_ROW, tuple(two))] == ["t_out", "t_exact"]


@pytest.mark.parametrize("column", ["t_out", "t_exact", "delta_lambda", "delta_t", "precision_regime"])
def test_a_null_transition_is_a_difference_in_both_directions(column):
    """NULL -> value and value -> NULL are both disagreements (an enrichment flip must not be silently kept or lost)."""
    nulled = list(_ROW)
    nulled[_I[column]] = None
    assert [d.split(":")[0] for d in rs._contact_row_diffs(tuple(nulled), _ROW)] == [column]       # stored NULL, derived value
    assert [d.split(":")[0] for d in rs._contact_row_diffs(_ROW, tuple(nulled))] == [column]       # stored value, derived NULL
    assert rs._contact_row_diffs(tuple(nulled), tuple(nulled)) == []                                # NULL = NULL agrees


def test_the_accuracy_columns_compare_at_float4_the_other_columns_exactly():
    exact = 1.0 / 3600.0                                     # the REAL column hands back 0.00027777778
    stored = list(_ROW)
    stored[_I["delta_lambda"]] = 0.00027777778
    derived = list(_ROW)
    derived[_I["delta_lambda"]] = exact
    assert rs._contact_row_diffs(tuple(stored), tuple(derived)) == []
    derived[_I["delta_lambda"]] = exact * 1.5
    assert [d.split(":")[0] for d in rs._contact_row_diffs(tuple(stored), tuple(derived))] == ["delta_lambda"]
    exact_t = list(_ROW)
    exact_t[_I["t_in"]] = Y(1, 1) + timedelta(microseconds=1)     # time columns are NOT rounded
    assert [d.split(":")[0] for d in rs._contact_row_diffs(_ROW, tuple(exact_t))] == ["t_in"]


def test_a_row_of_the_wrong_shape_is_refused_not_zipped_short():
    with pytest.raises(AssertionError, match="contact row shape"):
        rs._contact_row_diffs(_ROW[:-1], _ROW)


def test_the_snapshot_precedes_every_substep_that_writes_chain_rows():
    plan = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(ContextSpec(
        asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None, dry_run=True, config={"chart_id": CHART_ID}))]
    assert plan.count(writer_mod.SNAPSHOT_SUBSTEP) == 1
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
        self.dsn = make_conninfo(dsn, dbname=self.name)
        self.conn = psycopg.connect(self.dsn, autocommit=True, connect_timeout=3)
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
    """Moving the START of the horizon changes the bounds of the start-clipped contacts (a contact's identity is its
    physical object and occurrence ordinal, not the horizon). Whatever the identity does, the replaced chain must hold
    exactly the contacts a fresh build over the new horizon holds: no stale row and no overlapping duplicate beside it (a
    duplicate would still pass a union-based certification)."""
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
    with pytest.raises(rs.SealedGenerationError, match=r"generation chain replace: .*SEALED"):    # the NEW delete refused first
        world.step(writer_mod.SNAPSHOT_SUBSTEP, SHORT)          # the manifest's OWN horizon: the seal, not the horizon guard
    assert world.state() == before, "a sealed generation's chain was touched"


def test_a_partial_run_that_skips_the_head_does_not_over_delete(world, fresh):
    """NOT a resume (none exists: the orchestrator replays the whole plan on every dispatch). A partial run that skips the
    manifest/snapshot head, as a harness or a CLI could, builds a second class BESIDE the first: the replace does not run, so
    the first class's rows are untouched and the result equals one uninterrupted build. A whole-plan re-run then replaces and
    rebuilds, also equal."""
    world.build(SHORT, classes=(CLASSES[0],))                       # head (manifest, snapshot) + class one
    first = world.state()
    assert {r[0] for r in first["records"]} == {CLASSES[0]}
    world.build(SHORT, classes=(CLASSES[1],), head=False)           # no head: class two beside class one
    partial = world.state()
    assert {r[0] for r in partial["records"]} == set(CLASSES)
    assert {c[0] for c in first["contacts"]} <= {c[0] for c in partial["contacts"]}      # nothing of class one was wiped
    assert [r for r in partial["records"] if r[0] == CLASSES[0]] == [r for r in first["records"]]
    _same(partial, fresh(SHORT), "head-skipping partial run")
    world.build(SHORT)                                               # a whole-plan re-run: replaces, no accretion
    _same(world.state(), fresh(SHORT), "whole-plan re-run")


class _Replay(writer_mod.GocharaV5Writer):
    """The REAL writer driven by the REAL orchestrator driver over a SUBSET plan (the manifest, the snapshot, and two classes'
    inventory / coverage / record grains): the full plan is the full build, which this test must not run. `fail_at` injects
    one failure at a named substep."""
    fail_at = None

    def plan_substeps(self, ctx):
        keys = {writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP}
        for cls in CLASSES:
            keys |= {f"inventory:{cls}", f"coverage:{cls}"} | {f"record:{cls}:{p}" for p in PATHS}
        return [st for st in super().plan_substeps(ctx) if st.key in keys]

    def run_substep(self, ctx, step):
        if step.key == self.fail_at:
            raise RuntimeError(f"injected mid-build failure at {step.key}")
        return super().run_substep(ctx, step)


def test_a_retry_after_a_mid_build_failure_is_a_whole_plan_replay_and_equals_a_fresh_build(template, fresh):
    """THE real contract, through the REAL orchestrator driver (`asset_runner._drive_substeps`, called exactly as production
    calls it: no `completed_keys`, one commit per substep, a SAVEPOINT around each): the first dispatch fails part-way (earlier
    substeps stay committed), the retry replays the WHOLE plan from the manifest, and ends equal to a fresh build."""
    import psycopg
    from psycopg.rows import dict_row
    from pipeline.orchestrator import asset_runner
    w = _World(template)
    conn = None
    try:
        w.conn.execute("CREATE TABLE public.asset_throughput (chart_id uuid, asset_id text, state text,"
                       " last_built_at timestamptz, rows_written integer, last_error text)")
        w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s::uuid, %s, 'dormant', now(), 0, NULL)",
                       (CHART_ID, writer_mod.ASSET_ID))
        conn = psycopg.connect(w.dsn, autocommit=False, row_factory=dict_row, connect_timeout=3)   # the orchestrator's connection
        writer = _Replay()
        chart = uuid.UUID(CHART_ID)

        def dispatch(run_id):
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=run_id, db_conn=conn, dry_run=False,
                              config={"chart_id": chart, "horizon": SHORT, "ephe_path": EPHE_PATH})
            asset_runner._drive_substeps(conn, conn.cursor(), run_id, chart, writer_mod.ASSET_ID, writer, ctx)

        writer.fail_at = f"record:{CLASSES[1]}:P2"
        with pytest.raises(RuntimeError, match="injected mid-build failure"):
            dispatch("run-1")
        conn.rollback()                                              # what the orchestrator does on a failed dispatch
        partial = w.state()
        assert {r[0] for r in partial["records"]} == {CLASSES[0]}, "the failed dispatch left no committed earlier work"
        assert partial["contacts"], "no earlier substep was committed"
        writer.fail_at = None
        dispatch("run-2")                                            # the retry: the WHOLE plan again, from the manifest
        _same(w.state(), fresh(SHORT, CLASSES), "retry after a mid-build failure")
    finally:
        if conn is not None:
            conn.close()
        w.close()


def test_a_conflicting_contact_row_is_refused_by_name_not_kept(world):
    """Span contacts (residence) AND point contacts (conjunction): the same contact derived again with a different end, as a
    truncated row where an exact one is stored (value -> NULL) and as an exact row where a truncated one is stored (NULL ->
    value). The derived rows are COHERENT (the table's own checks tie t_exact to truncated / solver / coverage), so the
    refusal comes from the comparison, not from a check violation."""
    world.build(SHORT, classes=(CLASSES[0],))
    conn = world.conn
    store = rs.RecordStore(conn)
    cols = ("chart_id::text, generation, contact_id::text, physical_object_id::text, occurrence_ordinal, convention_id, body,"
            " relation_kind, t_in, t_out, t_exact, solver_method, delta_lambda, delta_t, precision_regime, coverage::text")

    def pick(relation, exact):
        return conn.execute(f"SELECT {cols} FROM public.ka_gochara_contact WHERE generation = %s AND relation_kind = %s"
                            f" AND t_exact {'IS NOT NULL' if exact else 'IS NULL'} AND t_out IS NOT NULL"
                            " ORDER BY contact_id LIMIT 1", (GEN, relation)).fetchone()

    def refused(stored, derived, label):
        with pytest.raises(rs.ContactRowMismatch, match=r"stored row differs from the derived one"):
            with conn.transaction():
                store._insert_contact_row(tuple(derived))
        kept = conn.execute("SELECT t_out, t_exact FROM public.ka_gochara_contact WHERE contact_id = %s::uuid",
                            (stored[2],)).fetchone()
        assert (kept[0], kept[1]) == (stored[9], stored[10]), f"{label}: the stored row was changed"

    seen = set()
    for relation in ("residence", "conjunction"):
        exact, truncated = pick(relation, True), pick(relation, False)
        if exact is not None:
            seen.add((relation, "exact"))
            with conn.transaction():
                store._insert_contact_row(tuple(exact))                  # the identical row again: a no-op, not an error
            moved = list(exact)
            moved[9] = exact[9] + timedelta(days=3)
            refused(exact, moved, f"{relation} / t_out moved")
            as_truncated = list(exact)                                    # value -> NULL: derived as a truncated row
            as_truncated[10:16] = [None, "clipped_truncated", None, None, None, '{"truncated": true}']
            refused(exact, as_truncated, f"{relation} / exact -> truncated")
        if truncated is not None and exact is not None:
            seen.add((relation, "truncated"))
            with conn.transaction():
                store._insert_contact_row(tuple(truncated))
            as_exact = list(truncated)                                    # NULL -> value: derived as an exact row
            as_exact[10] = truncated[8] + (truncated[9] - truncated[8]) / 2
            as_exact[11:16] = exact[11:16]
            refused(truncated, as_exact, f"{relation} / truncated -> exact")
    assert ("residence", "exact") in seen and ("conjunction", "exact") in seen, seen
    assert ("residence", "truncated") in seen, seen                       # the NULL -> value direction was exercised


def test_every_chain_writing_phase_refuses_a_horizon_that_is_not_its_manifests(world):
    """Nothing used to compare the configured horizon with the manifest's, so a head-skipping invocation could mix horizons.
    Every chain-writing phase refuses by name, writes nothing, for a horizon LONGER and for one SHORTER than the manifest's."""
    world.build(SHORT)
    before = world.state()
    cls = CLASSES[0]
    longer, shorter = LONG, (SHORT[0], SHORT[0] + timedelta(days=5))
    phases = (writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{cls}", f"coverage:{cls}", f"record:{cls}:P2",
              f"window:{cls}:P3", f"verify:{cls}")
    for key in phases:
        for other in (longer, shorter):
            with pytest.raises(writer_mod.HorizonMismatch, match="horizon guard"):
                world.step(key, other)
    assert world.state() == before, "a refused phase wrote something"
    world.step(f"coverage:{cls}", SHORT)                              # the manifest's own horizon is accepted


def test_a_published_but_unsealed_manifest_is_not_replaced(world):
    """Unsealed is not enough: only a CANDIDATE manifest's chain may be replaced."""
    from services.gochara_kernel import ledger
    world.build(SHORT)
    before = world.state()
    with world.conn.transaction():          # the published-but-unsealed world is set up behind the guards: it is the world under test
        world.conn.execute("SET LOCAL session_replication_role = replica")
        world.conn.execute("UPDATE public.kala_gochara_publication SET status = 'published', published_at = now()"
                           " WHERE generation = %s", (GEN,))
    with pytest.raises(ledger.PublishedGenerationRefusal, match="not 'candidate'"):
        with world.conn.transaction():
            rs.RecordStore(world.conn).delete_generation_chain(chart_id=CHART_ID, generation=GEN)
    assert world.state() == before


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
