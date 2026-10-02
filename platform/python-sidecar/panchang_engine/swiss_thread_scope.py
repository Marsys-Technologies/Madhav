"""Per-thread Swiss Ephemeris state preparation (C26).

On Linux the Swiss sidereal mode and ephemeris path are PER-THREAD C state
(macOS: process-global): a fresh thread that never called ``set_sid_mode``
computes in the library default ayanamsha (Fagan/Bradley, ~0.88° off Lahiri),
and a REUSED pool thread computes with whatever mode an earlier user of that
thread left behind. Production and CI are Linux and the orchestrator runs
writers in pool threads (pipeline/orchestrator/runner.py), so every function
that computes sidereally must prepare its OWN thread first.

``@serialized_swiss_state`` (panchang_engine.swiss_state) is ONLY a lock: it
serializes callers against each other and sets NO sidereal mode and NO
ephemeris path. A fully serialized function running on a fresh or
contaminated thread still computes in the wrong ayanamsha unless the thread's
own state is prepared — the lock and the preparation do different jobs.

This module is deliberately separate from swiss_state.py: swiss_state is in
the import closure of most L1 writers (changing it moves their code digests),
while nothing may import swiss_thread_scope except computing call sites that
need it. It imports SWISS_STATE_LOCK from swiss_state, never the reverse.

Call discipline: the helpers set path and mode on EVERY call, not once per
thread. Per-call setting is the safe pattern — beyond mode/path, Suvarṇa's
S-L1 measurements observed further per-thread state (delta-T / tidal
acceleration latched by the first SWIEPH call) shifting ``get_ayanamsa_ut``
by ~3.5e-7°, so "this thread was prepared earlier" is never a sound
assumption on a pooled worker.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import swisseph as swe

from panchang_engine.swiss_state import SWISS_STATE_LOCK


def prepare_swiss_thread(ephe_path: str | None, sid_mode: int) -> None:
    """Prepare the CALLING thread's Swiss Ephemeris state for sidereal calcs.

    Sets the ephemeris path (only when one is configured) and the sidereal
    mode on the thread that invokes this function. On Linux both are
    per-thread C state, so this must run in every thread before its first
    sidereal ``calc_ut`` — a mode/path set by another thread does not apply,
    and a reused pool thread may carry a DIFFERENT mode left by an earlier
    caller. Idempotent; on macOS (process-global state) it re-asserts the
    same values and changes nothing.

    The mutation itself is serialized under SWISS_STATE_LOCK like every other
    Swiss state write (DP-SD-010); callers already holding the lock
    (e.g. under ``@serialized_swiss_state`` — which is only a lock and sets
    no mode) re-enter the same RLock.
    """
    with SWISS_STATE_LOCK:
        if ephe_path is not None:
            swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(sid_mode)


@contextmanager
def swiss_calc_scope(ephe_path: str | None, sid_mode: int) -> Iterator[None]:
    """Take SWISS_STATE_LOCK, then prepare the calling thread inside it.

    The one-call critical section for a thread that is about to do sidereal
    Swiss work and has not provably set its own mode/path yet: the lock
    serializes against other threads' state selection, and
    ``prepare_swiss_thread`` fixes this thread's per-thread state.
    """
    with SWISS_STATE_LOCK:
        prepare_swiss_thread(ephe_path, sid_mode)
        yield
