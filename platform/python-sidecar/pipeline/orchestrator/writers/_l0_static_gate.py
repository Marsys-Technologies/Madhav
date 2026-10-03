"""
Registration gate for the two L0 static-asset writers added by TI-L0-20 (bg_gochara_citation_resolution, bg_sarvatobhadra_grid).

WHY (independent review L0C H-1, SS N-113 ruling). The orchestrator's writer-gap pre-flight (runner.py `_check_writer_registry_gaps`, mode
`enforce` by default) makes EVERY run exit 1 when an @register()'d writer's asset_registry.has_writer is false. These two writers are
registered in code BEFORE the registry says has_writer = true (migration 1280). The orchestrator is FROZEN, so the guard cannot be taught
about this; instead the writers are made unreachable until the registry is known to be ready:

  * the registry flips FIRST (migration 1280: has_writer = true; harmless without a writer - the guard is one-directional);
  * the code deploys SECOND with the gate OFF (default): `register_when_enabled` does not call @register, the writers are not in
    WRITER_REGISTRY, the pre-flight sees nothing new, every existing run is unaffected;
  * SS verifies the registry in production (reader: has_writer = true for both ids) and ONLY THEN sets ORCHESTRATOR_L0_STATIC_WRITERS=1 on
    the sidecar/job image and redeploys; the writers register and become dispatchable.

Why an environment gate rather than a DB check at import: importing code must not open a database connection (writers/__init__ imports every
module at discovery; tests import without a DB). Why not rely on the CI ordering test alone: migrations can silently do nothing while a
deploy reports success (CLAUDE.md N.4, Trap 103) - the explicit flag puts a human read of the production structure between the flip and
the registration. Failure mode of forgetting the flag is benign (assets plannable, no writer: a plan reports them undispatchable), never
the run-wide exit(1) of the opposite order.
"""
from __future__ import annotations

import os

ENV_VAR = "ORCHESTRATOR_L0_STATIC_WRITERS"


def enabled() -> bool:
    return os.environ.get(ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def register_when_enabled(asset_id: str):
    """Decorator: @register(asset_id) only when the gate is on; otherwise the class is returned unregistered."""
    from pipeline.orchestrator.writers import register

    def _decorate(cls):
        return register(asset_id)(cls) if enabled() else cls

    return _decorate
