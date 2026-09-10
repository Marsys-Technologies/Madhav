"""Retired alternate global-build entry point.

All global and L0 work must be dispatched through a durable ``build_runs`` row
and the primary digest-verified DAG runner.  Keeping a fail-closed module makes
old imports produce an actionable error without preserving a second execution
path that can bypass receipts, waves, pause/resume, and campaign evidence.
"""
from __future__ import annotations


def execute_global_build(run_id: str | None = None) -> None:
    del run_id
    raise RuntimeError(
        "direct global builds are retired; create a canonical cockpit build_run and invoke --run-id"
    )
