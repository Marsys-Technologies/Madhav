"""O-wave exit-rehearsal criterion (d) (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md
§3.4): the writer-facing contract stays frozen while WP-1/WP-2/WP-3 touch the
orchestrator's internals around it. This test asserts the CONTRACT'S OWN
SHAPE and default behavior -- documented in WriterBase's own docstring and
ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 -- has not drifted, so a change
anywhere in the O-wave's permitted files that accidentally touched the
contract instead of just its internals fails loudly here.
"""
from __future__ import annotations

import dataclasses
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4]))

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
import pipeline.orchestrator.writers as writers_module


def _field_names(dc) -> set[str]:
    return {f.name for f in dataclasses.fields(dc)}


def test_context_spec_shape_is_frozen():
    assert _field_names(ContextSpec) == {"asset_id", "build_id", "db_conn", "config", "dry_run"}
    ctx = ContextSpec(asset_id="x", build_id="b", db_conn=None)
    assert ctx.config == {}
    assert ctx.dry_run is False


def test_writer_result_shape_is_frozen():
    assert _field_names(WriterResult) == {
        "asset_id", "rows_inserted", "rows_updated", "rows_skipped",
        "duration_seconds", "notes",
    }
    result = WriterResult(asset_id="x", rows_inserted=1)
    assert (result.rows_updated, result.rows_skipped, result.duration_seconds, result.notes) == (0, 0, 0.0, "")


def test_substep_shape_is_frozen():
    assert _field_names(SubStep) == {"key", "label"}
    step = SubStep(key="k")
    assert step.label == "k", "an empty label must default to the key"


def test_writer_base_class_attributes_are_frozen():
    assert WriterBase.asset_id == ""
    assert WriterBase.has_substeps is False


def test_default_plan_substeps_is_one_whole_asset_step():
    class _Light(WriterBase):
        asset_id = "_test_light"

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=1)

    instance = _Light()
    steps = instance.plan_substeps(ctx=None)
    assert len(steps) == 1
    assert steps[0].key == "_test_light"


def test_default_run_substep_delegates_to_run():
    calls: list[str] = []

    class _Light(WriterBase):
        asset_id = "_test_light_delegate"

        def run(self, ctx):
            calls.append("run")
            return WriterResult(asset_id=self.asset_id, rows_inserted=1)

    instance = _Light()
    step = SubStep(key=instance.asset_id)
    result = instance.run_substep(ctx=None, step=step)
    assert calls == ["run"]
    assert result.rows_inserted == 1


def test_a_writer_implementing_only_run_substep_gets_a_working_run_for_free():
    class _Heavy(WriterBase):
        asset_id = "_test_heavy"
        has_substeps = True

        def plan_substeps(self, ctx):
            return [SubStep(key="a"), SubStep(key="b")]

        def run_substep(self, ctx, step):
            return WriterResult(asset_id=self.asset_id, rows_inserted=1, rows_updated=2)

    instance = _Heavy()
    aggregated = instance.run(ctx=None)
    assert aggregated.rows_inserted == 2
    assert aggregated.rows_updated == 4


def test_a_writer_implementing_neither_run_nor_run_substep_raises():
    class _Incomplete(WriterBase):
        asset_id = "_test_incomplete"

    with pytest.raises(NotImplementedError):
        _Incomplete().run(ctx=None)


def test_register_decorator_populates_the_registry_and_returns_the_class(monkeypatch):
    registry: dict = {}
    monkeypatch.setattr(writers_module, "_REGISTRY", registry)

    @register("_test_contract_registration")
    class _Registered(WriterBase):
        asset_id = "_test_contract_registration"

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)

    assert registry["_test_contract_registration"] is _Registered


def test_register_decorator_is_idempotent_for_the_identical_class(monkeypatch):
    registry: dict = {}
    monkeypatch.setattr(writers_module, "_REGISTRY", registry)

    class _Registered(WriterBase):
        asset_id = "_test_contract_idempotent"

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)

    register("_test_contract_idempotent")(_Registered)
    register("_test_contract_idempotent")(_Registered)  # must not raise
    assert registry["_test_contract_idempotent"] is _Registered


def test_register_decorator_rejects_a_genuine_conflict(monkeypatch):
    registry: dict = {}
    monkeypatch.setattr(writers_module, "_REGISTRY", registry)

    class _First(WriterBase):
        asset_id = "_test_contract_conflict"

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)

    class _Second(WriterBase):
        asset_id = "_test_contract_conflict"

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0)

    register("_test_contract_conflict")(_First)
    with pytest.raises(ValueError):
        register("_test_contract_conflict")(_Second)
