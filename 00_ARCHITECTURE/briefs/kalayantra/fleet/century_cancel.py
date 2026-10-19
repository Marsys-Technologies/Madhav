#!/usr/bin/env python3
"""Governed cancel of ONE running Cloud Run execution of the CENTURY build (W3W4 pack verify E1; SR-PREBUILD-ALL; the century counterpart of SR-J3-CANCEL-NULL 2(a)).

The century launch is the measuring launch minus the test slice (century_launch.py), so its execution runs on the SAME Cloud Run job (`brahma-build-pipeline-job`) and
this is measuring_cancel.py's engine unchanged except for the record it prints: ONE `ky.century_cancel/1` JSON line. The executor runs it for the fixed kind
`century_cancel` / `century_cancel_dryrun` (fleet/executor_ops.json) only after ITS admission (executor.cancel_problem) has bound the target to the execution named in the
`century_dispatch` receipt (J-4e) and to an ABORT / stall verdict cited by digest. Everything else (what each state means, the bounded polls, CANCELLED as the only
success, the dry run that plans and calls nothing, the honest nulls) is measuring_cancel.py's docstring."""
from __future__ import annotations

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cloudrun_readback as readback        # noqa: E402
import measuring_cancel as engine           # noqa: E402

SCHEMA = "ky.century_cancel/1"
SPEC = engine.CancelSpec(SCHEMA, readback.JOB, readback.EXECUTION, "Governed cancel of ONE running Cloud Run execution of the century build.")


def main(argv=None, environ=None, runner=readback.default_runner, sleep=time.sleep, out=sys.stdout) -> int:
    return engine.main(argv, environ, runner, sleep, out, spec=SPEC)


if __name__ == "__main__":
    sys.exit(main())
