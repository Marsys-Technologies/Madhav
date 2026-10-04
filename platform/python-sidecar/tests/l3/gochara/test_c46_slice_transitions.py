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
            self.conn.execute("CREATE TABLE IF NOT EXISTS public.build_runs (id text PRIMARY KEY, plan_manifest jsonb)")
        self._n = 0

    def run_id(self, marker=None) -> str:
        """A fresh build id; with a marker its plan_manifest carries it, without one the manifest is an empty object."""
        self._n += 1
        rid = f"run-{self._n}"
        manifest = {} if marker is None else {writer_mod.TEST_SLICE_KEY: marker}
        with self.conn.transaction():
            self.conn.execute("INSERT INTO public.build_runs (id, plan_manifest) VALUES (%s, %s::jsonb)",
                              (rid, json.dumps(manifest)))
        return rid

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

    def slice_build(self, horizon, **kw):
        marker = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": ALL_1Y, "horizon": _iso(horizon),
                  "classes": list(writer_mod.SCORED_CLASSES)}
        self.build_as(self.run_id(marker), horizon=None, **kw)

    def full_build(self, horizon, **kw):
        self.build_as(self.run_id(None), horizon=horizon, **kw)


@pytest.fixture()
def sworld(template):
    w = _SliceWorld(template)
    try:
        yield w
    finally:
        w.close()


def test_the_sliced_substeps_build_what_a_full_build_over_the_same_horizon_builds(sworld, fresh):
    """The slice changes the identity (scope, marker), never the geometry: its chain equals a fresh full build's."""
    sworld.slice_build(FULLL)
    _same(sworld.state(), fresh(FULLL), "slice over FULLL")


def test_slice_then_full_leaves_no_slice_contact_behind(sworld, fresh):
    """THE Codex P1-1 case: an end-clipped slice (SHORT), then the full interval (LONG)."""
    sworld.slice_build(SHORT)
    sworld.full_build(LONG)
    _same(sworld.state(), fresh(LONG), "slice SHORT then full LONG")


def test_full_then_slice_replaces_the_full_chain_with_the_slice(sworld, fresh):
    sworld.full_build(LONG)
    sworld.slice_build(SHORT)
    state = sworld.state()
    assert not [c for c in state["contacts"] if c[2] is not None and c[2] > SHORT[1]]
    _same(state, fresh(SHORT), "full LONG then slice SHORT")


def test_slice_then_a_slice_with_a_different_scope(sworld, fresh):
    """Start clip then end-clipped-start: LEFT (start-clipped, new contact ids) then the earlier start FULLL."""
    sworld.slice_build(LEFT)
    sworld.slice_build(FULLL)
    _same(sworld.state(), fresh(FULLL), "slice LEFT then slice FULLL")


def test_slice_slice_full_in_one_chart(sworld, fresh):
    sworld.slice_build(SHORT)
    sworld.slice_build(LEFT)
    sworld.full_build(LONG)
    _same(sworld.state(), fresh(LONG), "slice, slice, full")


def test_orphans_of_a_crashed_slice_are_replaced_by_the_next_full_build(sworld, fresh):
    sworld.slice_build(SHORT)
    with sworld.conn.transaction():
        sworld.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE generation = %s", (GEN,))
    assert sworld.conn.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0] >= 5
    sworld.full_build(LONG)
    _same(sworld.state(), fresh(LONG), "crashed slice then full")


def test_the_real_verification_entry_point_refuses_a_sliced_manifest_by_name(sworld):
    """Codex: the earlier test called verify_inputs directly. This one goes through the verification JOB's own
    precondition (`check_preconditions`) on a manifest the writer itself built under a slice."""
    sworld.slice_build(FULLL, classes=(CLASSES[0],), paths=())          # manifest, snapshot, inventory + coverage of one class
    with pytest.raises(vj.VerificationRefused) as exc:
        vj.check_preconditions(sworld.conn, chart_id=CHART_ID, generation=GEN, classes=[CLASSES[0]],
                               ephe_path=EPHE_PATH, modules=iv.IMPLEMENTATION_MODULES,
                               path_refs=list(rr.BOUND_PATH_REFS))
    assert exc.value.code == "stale_inputs"
    assert "stored_scope" in exc.value.detail and "test_slice" in exc.value.detail


def test_a_default_manifest_passes_the_same_entry_point_precondition_on_inputs(sworld):
    """The control: the same entry point does NOT refuse a manifest built without a marker for its scope."""
    sworld.full_build(FULLL, classes=(CLASSES[0],), paths=())
    try:
        out = vj.check_preconditions(sworld.conn, chart_id=CHART_ID, generation=GEN, classes=[CLASSES[0]],
                                     ephe_path=EPHE_PATH, modules=iv.IMPLEMENTATION_MODULES,
                                     path_refs=list(rr.BOUND_PATH_REFS))
    except vj.VerificationRefused as exc:
        assert "stored_scope" not in str(exc), f"the default manifest was refused for its scope: {exc}"
        return                      # refused LATER for another honest reason (stub chain), never for the scope
    assert out["inputs"] == "independently re-derived"
