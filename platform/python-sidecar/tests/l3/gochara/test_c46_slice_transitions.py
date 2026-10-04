"""C46 / A5.5g — scope transitions between a TEST SLICE and a full build, through the writer's own substeps.

Codex P1-1 on PR 3110: slice contacts could survive a later full build (the class-level replace keeps a contact another class
still references, and the contact insert used to be `ON CONFLICT DO NOTHING`). PR 3132 (A5.5f) replaces the whole unsealed
chart x generation chain at the `snapshot` substep and refuses a different row on a contact conflict; these tests prove that
every scope transition the slice introduces ends equal to a FRESH build over the same scope:

  slice -> full, full -> slice, slice -> a slice with a different scope, an end clip, a start clip, and the orphans a crashed
  slice leaves — plus the real verification-job entry point (`check_preconditions`) refusing a sliced manifest by name.

Only two of the 26 classes are executed (the marker names all 26 for `all_classes_1y`, as the writer requires); the substeps are
the writer's own, on the real migration chain, with the pinned Swiss corpus (conftest)."""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import verification_job as vj

from .conftest import EPHE_PATH
from .test_a55_replace_chain import (CHART_ID, CLASSES, FULLL, GEN, LEFT, LONG, PATHS, SHORT, _World,  # noqa: F401
                                     _same, fresh, template)

ALL_1Y = "all_classes_1y"


def _iso(h):
    return [h[0].isoformat(), h[1].isoformat()]


class _SliceWorld(_World):
    """A world that can run substeps under a slice marker held in build_runs.plan_manifest (read by build id)."""

    def __init__(self, template):
        super().__init__(template)
        with self.conn.transaction():
            self.conn.execute("CREATE TABLE IF NOT EXISTS public.build_runs"
                              " (id text PRIMARY KEY, plan_manifest jsonb, plan_manifest_digest text)")
        self._n = 0

    def run_id(self, marker=None) -> str:
        """A fresh build id; with a marker its plan_manifest carries it, without one the manifest is an empty object."""
        self._n += 1
        rid = f"run-{self._n}"
        manifest = {} if marker is None else {writer_mod.TEST_SLICE_KEY: marker}
        with self.conn.transaction():
            self.conn.execute("INSERT INTO public.build_runs (id, plan_manifest, plan_manifest_digest) VALUES (%s, %s::jsonb, %s)",
                              (rid, json.dumps(manifest), writer_mod._manifest_digest(manifest)))
        return rid

    def stamp(self):
        """What the candidate manifest says about itself: (stored_scope, test_slice component or None, horizon)."""
        v, lo, hi = self.conn.execute(
            "SELECT input_generation_vector, lower(horizon), upper(horizon) FROM public.kala_gochara_publication"
            " WHERE generation = %s", (GEN,)).fetchone()
        return v.get("stored_scope"), v.get("test_slice"), (lo, hi)

    def ctx_of(self, build_id, horizon=None):
        cfg = {"chart_id": CHART_ID, "ephe_path": EPHE_PATH}
        if horizon is not None:
            cfg["horizon"] = horizon
        return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=build_id, db_conn=self.conn, dry_run=False, config=cfg)

    def step_as(self, key, build_id, horizon=None):
        cfg = {"chart_id": CHART_ID, "ephe_path": EPHE_PATH}
        if horizon is not None:
            cfg["horizon"] = horizon
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=build_id, db_conn=self.conn, dry_run=False, config=cfg)
        with self.conn.transaction():
            return self._w.run_substep(ctx, SubStep(key=key, label=key))

    def build_as(self, build_id, horizon=None, classes=CLASSES, paths=PATHS, head=True):
        if head:
            self.step_as(writer_mod.MANIFEST_SUBSTEP, build_id, horizon)
            self.step_as(writer_mod.SNAPSHOT_SUBSTEP, build_id, horizon)
        for cls in classes:
            self.step_as(f"inventory:{cls}", build_id, horizon)
            self.step_as(f"coverage:{cls}", build_id, horizon)
            for p in paths:
                self.step_as(f"record:{cls}:{p}", build_id, horizon)

    def marker_for(self, horizon):
        return {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": ALL_1Y, "horizon": _iso(horizon),
                "classes": list(writer_mod.SCORED_CLASSES)}

    def slice_build(self, horizon, **kw):
        self.build_as(self.run_id(self.marker_for(horizon)), horizon=None, **kw)

    def full_build(self, horizon, **kw):
        self.build_as(self.run_id(None), horizon=horizon, **kw)


@pytest.fixture()
def sworld(template):
    w = _SliceWorld(template)
    try:
        yield w
    finally:
        w.close()


def _assert_sliced(w, horizon):
    """After a sliced build the manifest states, in clear, that it is a test slice: scope, component (run, classes, horizon,
    digest) and the horizon itself."""
    scope, comp, (lo, hi) = w.stamp()
    marker = w.marker_for(horizon)
    assert scope == writer_mod.TEST_SLICE_SCOPE, scope
    assert comp is not None and comp["run"] == ALL_1Y and comp["classes"] == list(writer_mod.SCORED_CLASSES)
    assert comp["horizon"] == [horizon[0].isoformat(), horizon[1].isoformat()] and comp["schema"] == writer_mod.TEST_SLICE_SCHEMA
    assert comp["marker_digest"] == writer_mod._validate_test_slice(marker).digest
    assert (lo, hi) == tuple(horizon)


def _assert_default(w, horizon):
    """After a default build the manifest carries NO slice stamp at all."""
    scope, comp, (lo, hi) = w.stamp()
    assert scope == "stored_non_moon" and comp is None, (scope, comp)
    assert (lo, hi) == tuple(horizon)




def test_the_sliced_substeps_build_what_a_full_build_over_the_same_horizon_builds(sworld, fresh):
    """The slice changes the identity (scope, marker), never the geometry: its chain equals a fresh full build's."""
    sworld.slice_build(FULLL)
    _same(sworld.state(), fresh(FULLL), "slice over FULLL")
    _assert_sliced(sworld, FULLL)


def test_slice_then_full_leaves_no_slice_contact_behind(sworld, fresh):
    """THE Codex P1-1 case: an end-clipped slice (SHORT), then the full interval (LONG)."""
    sworld.slice_build(SHORT)
    _assert_sliced(sworld, SHORT)
    sworld.full_build(LONG)
    _same(sworld.state(), fresh(LONG), "slice SHORT then full LONG")
    _assert_default(sworld, LONG)


def test_full_then_slice_replaces_the_full_chain_with_the_slice(sworld, fresh):
    sworld.full_build(LONG)
    _assert_default(sworld, LONG)
    sworld.slice_build(SHORT)
    _assert_sliced(sworld, SHORT)
    state = sworld.state()
    assert not [c for c in state["contacts"] if c[2] is not None and c[2] > SHORT[1]]
    _same(state, fresh(SHORT), "full LONG then slice SHORT")


def test_slice_then_a_slice_with_a_different_scope(sworld, fresh):
    """Start clip then end-clipped-start: LEFT (start-clipped, new contact ids) then the earlier start FULLL."""
    sworld.slice_build(LEFT)
    _assert_sliced(sworld, LEFT)
    sworld.slice_build(FULLL)
    _same(sworld.state(), fresh(FULLL), "slice LEFT then slice FULLL")
    _assert_sliced(sworld, FULLL)


def test_slice_slice_full_in_one_chart(sworld, fresh):
    sworld.slice_build(SHORT)
    sworld.slice_build(LEFT)
    _assert_sliced(sworld, LEFT)
    sworld.full_build(LONG)
    _same(sworld.state(), fresh(LONG), "slice, slice, full")
    _assert_default(sworld, LONG)


def test_orphans_of_a_crashed_slice_are_replaced_by_the_next_full_build(sworld, fresh):
    sworld.slice_build(SHORT)
    with sworld.conn.transaction():
        sworld.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE generation = %s", (GEN,))
    assert sworld.conn.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0] >= 5
    sworld.full_build(LONG)
    _same(sworld.state(), fresh(LONG), "crashed slice then full")


def test_the_real_verification_entry_point_refuses_a_sliced_manifest_by_name(sworld):
    """Codex: the earlier test called verify_inputs directly. This one goes through the verification JOB's own precondition
    (`check_preconditions`) on a manifest the writer itself built under a slice: refused POSITIVELY (Fable P2-2), by name."""
    sworld.slice_build(FULLL, classes=(CLASSES[0],), paths=())          # manifest, snapshot, inventory + coverage of one class
    with pytest.raises(vj.VerificationRefused) as exc:
        vj.check_preconditions(sworld.conn, chart_id=CHART_ID, generation=GEN, classes=[CLASSES[0]],
                               ephe_path=EPHE_PATH, modules=iv.IMPLEMENTATION_MODULES,
                               path_refs=list(rr.BOUND_PATH_REFS))
    assert exc.value.code == "test_slice_candidate"
    assert "test_slice" in exc.value.detail and "stored_scope" in exc.value.detail


def test_a_sliced_candidate_is_refused_by_each_of_the_four_vocabulary_lists_independently(sworld):
    """Fable P2-2: refusal used to rest on the scope being ABSENT from four separate lists, only one pinned. Each is pinned here
    against a real sliced candidate, so a new scope word added to any single one would fail a test, not silently verify a slice."""
    from services.gochara_kernel import input_vector_verifier as ivv
    from services.gochara_kernel import inventory_verifier as inv_v
    from services.gochara_kernel import scope_response as sr
    sworld.slice_build(FULLL, classes=(CLASSES[0],), paths=())
    conn = sworld.conn
    # 1. the input verifier's vocabulary
    assert ivv._KNOWN_SCOPES == ("stored_non_moon",)
    # 2. the inventory verifier's scope table
    assert set(inv_v.SCOPE_EXCLUDED_AGENTS) == {"stored_non_moon"}
    with pytest.raises(inv_v.Unverifiable, match="not a scope this verifier knows"):
        inv_v.excluded_agents_of_scope("test_slice")
    with pytest.raises(inv_v.Unverifiable, match="not a scope this verifier knows"):
        inv_v.bound_excluded_agents(conn, CHART_ID, GEN)                       # on the real sliced manifest
    # 3. serving's scope statement
    assert set(sr.SCOPE_STATEMENT) == {"stored_non_moon"}
    with pytest.raises(sr.ScopeMissing, match="not a scope this build can state"):
        sr.bound_stored_scope(conn, CHART_ID, GEN)
    # 4. migration 1232's Moon-scope violations (the seal gate's SQL half): `stored_scope_missing` is raised for a manifest that is
    #    being PUBLISHED without stored_scope = stored_non_moon. The template chain does not carry 1232, so the REAL file is applied
    #    to this clone first (as the moon-scope tests do), and the sliced candidate is evaluated as a published manifest.
    from .test_a53_inventory import MIGRATIONS
    conn.execute((MIGRATIONS / "1232_gochara_search_moon_scope_domain.sql").read_text())
    with conn.transaction():
        conn.execute("SET LOCAL session_replication_role = replica")             # the published-world is set up behind the guards
        conn.execute("UPDATE public.kala_gochara_publication SET status = 'published', published_at = now()"
                     " WHERE generation = %s", (GEN,))
        found = {v for _c, v, _d in conn.execute(
            "SELECT event_class, violation, detail FROM public.ka_gochara_search_moon_scope_violations(%s::uuid, %s)",
            (CHART_ID, GEN)).fetchall()}
    assert "stored_scope_missing" in found, found


def test_scenario_a_a_marker_removed_after_the_plan_is_fixed_is_refused_on_the_real_manifest_substep(sworld):
    """Fable P1 scenario A on a real database: the marker is staged and the plan narrowed to ONE class; the key is then removed
    from the stored manifest (the digest is not touched); the manifest substep must refuse and publish nothing."""
    marker = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "one_class_full", "horizon": _iso(writer_mod.DEFAULT_HORIZON),
              "classes": [CLASSES[0]]}
    rid = sworld.run_id(marker)
    plan = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(sworld.ctx_of(rid))]
    assert {k.split(":")[1] for k in plan if k.startswith("inventory:")} == {CLASSES[0]}        # the plan is narrowed
    with sworld.conn.transaction():
        sworld.conn.execute("UPDATE public.build_runs SET plan_manifest = plan_manifest - %s WHERE id = %s",
                            (writer_mod.TEST_SLICE_KEY, rid))
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        sworld.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
    assert sworld.conn.execute("SELECT count(*) FROM public.kala_gochara_publication WHERE generation = %s", (GEN,)).fetchone()[0] == 0


def test_scenario_b_a_marker_replaced_mid_run_is_refused_whether_or_not_the_digest_follows(sworld):
    a, b = CLASSES
    marker_a = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "one_class_full", "horizon": _iso(writer_mod.DEFAULT_HORIZON),
                "classes": [a]}
    marker_b = dict(marker_a, classes=[b])
    rid = sworld.run_id(marker_a)
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
    sworld.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid)
    # (1) the manifest changes, the stored digest does not
    with sworld.conn.transaction():
        sworld.conn.execute("UPDATE public.build_runs SET plan_manifest = %s::jsonb WHERE id = %s",
                            (json.dumps({writer_mod.TEST_SLICE_KEY: marker_b}), rid))
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        sworld.step_as(f"inventory:{a}", rid)
    # (2) the digest follows the manifest: the remaining grains of the OLD plan name a class the new marker does not
    with sworld.conn.transaction():
        sworld.conn.execute("UPDATE public.build_runs SET plan_manifest_digest = %s WHERE id = %s",
                            (writer_mod._manifest_digest({writer_mod.TEST_SLICE_KEY: marker_b}), rid))
    with pytest.raises(writer_mod.TestSliceRefusal, match="not in the run's validated marker"):
        sworld.step_as(f"inventory:{a}", rid)
    before = sworld.state()
    with pytest.raises(writer_mod.TestSliceRefusal):
        sworld.step_as(f"record:{a}:P2", rid)
    assert sworld.state() == before, "a refused grain wrote something"


@pytest.mark.parametrize("shape", ["one_class_full", "all_classes_1y"])
def test_both_run_shapes_are_driven_through_plan_substeps_on_a_real_database(sworld, shape):
    """Fable P3: the plan narrowing and `one_class_full` over the FULL horizon, exercised on a real database THROUGH
    `plan_substeps` — the substeps executed are the PLAN's own keys, not hand-written ones — with the stamp asserted afterwards.
    (The plan's P1 grains cannot pass on the stubbed L1, so the plan is driven through the manifest, the snapshot and the first
    class's inventory and coverage.)"""
    if shape == "one_class_full":
        marker = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": shape, "horizon": _iso(writer_mod.DEFAULT_HORIZON),
                  "classes": [CLASSES[0]]}
    else:
        marker = sworld.marker_for(FULLL)
    rid = sworld.run_id(marker)
    plan = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(sworld.ctx_of(rid))]
    classes_in_plan = list(dict.fromkeys(k.split(":")[1] for k in plan if k.startswith("inventory:")))
    assert classes_in_plan == list(writer_mod._validate_test_slice(marker).classes)
    assert len(classes_in_plan) == (1 if shape == "one_class_full" else 26)
    first = classes_in_plan[0]
    driven = [k for k in plan if k in (writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP,
                                        f"inventory:{first}", f"coverage:{first}")]
    assert driven == [writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{first}", f"coverage:{first}"]
    for key in driven:
        sworld.step_as(key, rid)
    scope, comp, (lo, hi) = sworld.stamp()
    sl = writer_mod._validate_test_slice(marker)
    assert scope == writer_mod.TEST_SLICE_SCOPE and comp == writer_mod._slice_component(sl)
    assert (lo, hi) == tuple(sl.horizon)
    cov = sworld.conn.execute("SELECT partition_key, lower(completed_horizon), upper(completed_horizon) FROM public.kala_gochara_coverage"
                              " WHERE generation = %s AND partition_kind = 'event_class'", (GEN,)).fetchall()
    assert [(c[0], c[1], c[2]) for c in cov] == [(first, sl.horizon[0], sl.horizon[1])]


def test_the_marker_read_on_a_real_idle_non_autocommit_connection_never_commits_and_never_poisons(template):
    """Fable P3: `plan_substeps` can be the first thing the driver calls on a fresh connection. With the old helper
    `conn.transaction()` opened an OUTERMOST transaction there and COMMITTED it at exit (a writer-side commit); the manual
    savepoint leaves the connection's implicit transaction open — and a missing build_runs table does not poison it."""
    import psycopg
    w = _World(template)                                   # a clone WITHOUT build_runs: the absent-table path
    conn = None
    try:
        conn = psycopg.connect(w.dsn, autocommit=False, connect_timeout=3)
        assert conn.info.transaction_status.name == "IDLE"
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=conn, dry_run=False, config={"chart_id": CHART_ID})
        assert writer_mod._plan_manifest(ctx) is None                           # an absent table reads as 'no marker' …
        assert conn.info.transaction_status.name == "INTRANS", "the read committed or rolled back the connection's transaction"
        conn.execute("SELECT 1")                                                 # … and the connection is not poisoned
        assert conn.info.transaction_status.name == "INTRANS"
        conn.rollback()
        # the same on a connection where the table EXISTS and holds the row
        w.conn.execute("CREATE TABLE public.build_runs (id text PRIMARY KEY, plan_manifest jsonb, plan_manifest_digest text)")
        w.conn.execute("INSERT INTO public.build_runs VALUES ('r', %s::jsonb, %s)",
                       (json.dumps({"k": 1}), writer_mod._manifest_digest({"k": 1})))
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="r", db_conn=conn, dry_run=False, config={"chart_id": CHART_ID})
        assert conn.info.transaction_status.name == "IDLE"
        assert writer_mod._plan_manifest(ctx) == {"k": 1}
        assert conn.info.transaction_status.name == "INTRANS"
    finally:
        if conn is not None:
            conn.close()
        w.close()


