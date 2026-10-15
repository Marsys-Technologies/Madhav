#!/usr/bin/env python3
"""Test driver (B-0c control tests): run one `kyveto.py` command and SIGKILL the process at a chosen point.

    crash_tick.py <fleet dir> <point> <kyveto arguments…>

A real crash, not an exception: no `finally` runs, the decision lock stays behind with a dead owner and the
action record stays INTENDED — exactly what a restart has to recover from (plan §4a.1 "Recovery").

The process runs at the real wall clock: `kyveto.py tick` takes no time from its caller, and this driver gives
it none. The tests therefore place their proposals in the real past.

points:  before-execute   after `begin` of the execution action, before the capacity executor writes anything
         between-files    after the capacity executor has written KY_WORKERS, before it writes KY_VERIFIERS
         after-execute    after the capacity executor has written, before the observed result is recorded
         before-publish   after `begin` of the publication action, before `ky decide` is started
         after-publish    after `ky decide` has exited, before its exit status is recorded
"""
import os
import signal
import sys

fleet, point = sys.argv[1], sys.argv[2]
sys.path.insert(0, fleet)

import kyveto  # noqa: E402


def die():
    os.kill(os.getpid(), signal.SIGKILL)


capacity = kyveto.REGISTRY["capacity"]
real_execute, real_ky = capacity.execute, kyveto.run_ky

if point == "before-execute":
    capacity.execute = lambda params, ctx: die()
elif point == "between-files":
    real_write = kyveto.kyaction.write_atomic

    def write_then_die(path, data, mode=None):
        real_write(path, data, mode)
        if os.path.basename(str(path)) == "KY_WORKERS":
            die()
    kyveto.kyaction.write_atomic = write_then_die
elif point == "after-execute":
    def execute_then_die(params, ctx):
        real_execute(params, ctx)
        die()
    capacity.execute = execute_then_die
elif point == "before-publish":
    kyveto.run_ky = lambda argv, env: die()
elif point == "after-publish":
    def publish_then_die(argv, env):
        real_ky(argv, env)
        die()
    kyveto.run_ky = publish_then_die
else:
    sys.exit(64)

sys.exit(kyveto.main(sys.argv[3:]))
