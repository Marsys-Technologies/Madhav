#!/usr/bin/env python3
"""Governed cancel of ONE running Cloud Run execution of the VERIFICATION job (W3W4 pack verify E1; SR-PREBUILD-ALL; the verification counterpart of SR-J3-CANCEL-NULL 2(a)).

The verification job is its own Cloud Run job (`gochara-verification-job`, deployed by gochara-verification-job-deploy.yml), so this is measuring_cancel.py's engine pointed
at that job: the execution name must be `gochara-verification-job-<suffix>` (refused before any cloud call otherwise), the described execution must belong to that job, and the
record it prints is ONE `ky.verification_cancel/1` JSON line. The executor runs it for the fixed kind `verification_cancel` / `verification_cancel_dryrun`
(fleet/executor_ops.json) only after ITS admission (executor.cancel_problem) has bound the target to the execution named in the `verification_job` receipt (J-5s) and to an ABORT /
stall verdict cited by digest. Everything else (what each state means, the bounded polls, CANCELLED as the only success, the dry run that plans and calls nothing, the honest nulls)
is measuring_cancel.py's docstring."""
from __future__ import annotations

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cloudrun_readback as readback        # noqa: E402
import measuring_cancel as engine           # noqa: E402

SCHEMA = "ky.verification_cancel/1"
SPEC = engine.CancelSpec(SCHEMA, readback.VERIFICATION_JOB, readback.VERIFICATION_EXECUTION, "Governed cancel of ONE running Cloud Run execution of the verification job.")


def main(argv=None, environ=None, runner=readback.default_runner, sleep=time.sleep, out=sys.stdout) -> int:
    return engine.main(argv, environ, runner, sleep, out, spec=SPEC)


if __name__ == "__main__":
    sys.exit(main())
