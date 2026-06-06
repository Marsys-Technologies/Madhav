"""
pipeline.orchestrator.main — CLI entrypoint
============================================

Invoked by Cloud Run Job `brahma-build-pipeline-job` with:
  --run-id <build_runs.id UUID>

Exit codes:
  0  run completed, stopped, or paused cleanly
  2  run not found
  3  chart locked by another running job (defer-to-existing)
  1  unexpected fatal error
"""
from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Brahma build pipeline orchestrator")
    parser.add_argument("--run-id", required=True, help="UUID of the build_runs row to execute")
    args = parser.parse_args()

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
