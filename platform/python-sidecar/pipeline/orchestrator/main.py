"""
pipeline.orchestrator.main — CLI entrypoint
============================================

Invoked by Cloud Run Job `brahma-build-pipeline-job` with:
  --run-id <build_runs.id UUID>

  OR for L0FR global build (L0FR Stream A step 8-9):
  --global-build  [--run-id <optional uuid>]

F4.b (SM-R-11): --run-id is REQUIRED for chart builds. No-args invocation is
FORBIDDEN — use the ratified canary dispatch script (dispatch_ka_kshetra_canary.py),
never raw `gcloud run jobs execute` without --args.

Exit codes:
  0  run completed, stopped, or paused cleanly
  2  invocation error (no --run-id, or run not found)
  3  chart locked by another running job (defer-to-existing)
  1  unexpected fatal error
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Guarantee the sidecar root is on sys.path so local packages (muhurat, panchang_engine,
# services, etc.) are importable regardless of how the Cloud Run Job invokes this entry
# point. `python -m pipeline.orchestrator.main` adds the package parent but Cloud Run
# jobs may configure a different working directory.
_SIDECAR_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    # F4.b (SM-R-11): catch no-args invocation before argparse. A Cloud Run Job
    # dispatched without --args exits 2 here instead of silently succeeding.
    # '--global-build' without '--run-id' is the one legitimate no-run-id case.
    if len(sys.argv) == 1:
        logger.error(
            "[orchestrator] No arguments provided. --run-id is required for chart builds. "
            "Use the ratified canary dispatch script, never raw `gcloud run jobs execute`. "
            "(F4.b, SM-R-11)"
        )
        sys.exit(2)

    parser = argparse.ArgumentParser(description="Brahma build pipeline orchestrator")
    # required=False: --global-build mode legitimately runs without --run-id.
    # Enforce --run-id below for the chart-build path.
    parser.add_argument("--run-id", required=False, help="UUID of the build_runs row to execute")
    parser.add_argument(
        "--global-build",
        action="store_true",
        default=False,
        help=(
            "L0FR global build mode: acquire pg_advisory_lock(hashtext('global')), "
            "walk asset_registry rows where scope='global', run their writers, release lock. "
            "Used for L0 brahmagyan foundation data builds that are chart-independent."
        ),
    )
    args = parser.parse_args()

    if args.global_build:
        from .global_runner import execute_global_build
        try:
            execute_global_build(run_id=args.run_id)
        except SystemExit:
            raise
        except Exception as exc:
            logger.error("[orchestrator] global-build fatal: %s", exc, exc_info=True)
            sys.exit(1)
        return

    if not args.run_id:
        # F4.b (SM-R-11): enforce --run-id for chart builds. Exit 2 (invocation error).
        logger.error(
            "[orchestrator] --run-id is required for chart builds. "
            "Use the ratified canary dispatch script. (F4.b, SM-R-11)"
        )
        sys.exit(2)

    from .runner import execute_run

    try:
        execute_run(args.run_id)
    except SystemExit:
        raise
    except Exception as exc:
        logger.error("[orchestrator] fatal: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
