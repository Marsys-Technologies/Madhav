"""_n430_fakes.py -- the fake psql runner the SS N-430 hygiene tests share (not a test module).

`FakePsql` replaces `subprocess.run` / `asset_census._run_capped` (the only two places the census starts psql): it records every argv, answers from a script of
outcomes and never touches a database. `FakeClock` replaces `asset_census.time` so elapsed seconds and the retry pause are exact and nothing sleeps.
"""
from __future__ import annotations

import subprocess
import time as _real_time
import types


class FakeClock:
    """Stands in for the `time` module inside asset_census: monotonic() advances by the `step` the script gives, sleep() is recorded, everything else is the real module."""
    def __init__(self):
        self.now = 1000.0
        self.slept: list[float] = []
        self.advance_on_run = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, secs):
        self.slept.append(secs)

    def __getattr__(self, name):
        return getattr(_real_time, name)


def ok(stdout=b"1\n"):
    return dict(rc=0, out=stdout, err=b"")


def fail(stderr: str, rc: int = 2):
    return dict(rc=rc, out=b"", err=stderr.encode())


class FakePsql:
    """`script` is a list of outcomes (ok() / fail() / "timeout"); the last one repeats. `calls` holds every argv; `clock` (optional) is advanced by `elapsed` per call."""
    def __init__(self, monkeypatch, ac, script=None, clock: FakeClock | None = None, elapsed: float = 0.0):
        self.calls: list[list[str]] = []
        self.script = list(script or [ok()])
        self.clock, self.elapsed = clock, elapsed
        monkeypatch.setattr(ac.subprocess, "run", self._run)
        monkeypatch.setattr(ac, "_run_capped", self._run_capped)

    def _next(self, argv):
        self.calls.append(list(argv))
        if self.clock is not None:
            self.clock.now += self.elapsed
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if step == "timeout":
            raise subprocess.TimeoutExpired(argv, 1)
        return step

    def _run(self, argv, *a, **k):
        s = self._next(argv)
        return types.SimpleNamespace(returncode=s["rc"], stdout=s["out"], stderr=s["err"])

    def _run_capped(self, argv, env, limit, cap, stdin=None):
        s = self._next(argv)
        if stdin is not None:
            self.calls[-1].append("<<stdin:" + stdin.decode("utf-8") + ">>")
        return types.SimpleNamespace(returncode=s["rc"], stdout=s["out"], stderr=s["err"], over=False)

    def commands(self, i: int = -1) -> list[str]:
        """The `-c` arguments of call `i`."""
        argv = self.calls[i]
        return [argv[j + 1] for j, x in enumerate(argv) if x == "-c"]
