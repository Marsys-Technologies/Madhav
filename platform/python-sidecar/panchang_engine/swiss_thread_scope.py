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


class SwissThreadBackendError(RuntimeError):
    """The calling thread's Swiss computations would NOT be served by the .se1 files.

    A server-side configuration fault (missing ephemeris path, or the library silently
    substituting Moshier/JPL), never a client error — same disclosure class as
    ``panchang_engine.swiss_backend.SwissBackendError``.
    """


_PROBE_JD_J2000 = 2451545.0


def ensure_swiss_thread_backend(ephe_path: str | None, sid_mode: int) -> None:
    """Fail-closed backend probe for the CALLING thread; path and mode re-set on EVERY call.

    Converges this module's per-thread preparation with swiss_backend's backend honesty
    (SS ruling N-28: Moshier is a fallback and must NEVER be silent) — for callers that
    compute through ``prepare_swiss_thread`` / ``swiss_calc_scope`` rather than the L1
    writer seam:

    * the .se1 path MUST be set (a ``None``/blank ``ephe_path`` raises — pyswisseph
      accepts any path string and silently substitutes Moshier, so an unconfigured path
      can never be treated as "the files will be found");
    * the path and the sidereal mode are re-asserted on the calling thread on EVERY call
      (Linux: both are per-thread C state; a reused pool thread may carry another caller's
      mode, and per Suvarṇa's S-L1 measurements "prepared earlier" is never a sound
      assumption on a pooled worker);
    * the backend is then PROBED on this thread: Sun (needs ``sepl_*.se1``) and TRUE_NODE
      (computed from the Moon, so it needs ``semo_*.se1``) at J2000 with FLG_SWIEPH. The
      returned flag is the discriminator — measured in swiss_backend's docstring: the
      Moon's flag lies (reports SWIEPH while serving the Moshier Moon), TRUE_NODE's does
      not, and MEAN_NODE is analytic. Anything other than swieph for BOTH raises
      ``SwissThreadBackendError``.

    The set + probe run under SWISS_STATE_LOCK like every other Swiss state mutation
    (DP-SD-010); callers already holding it re-enter the same RLock.
    """
    if ephe_path is None or not str(ephe_path).strip():
        raise SwissThreadBackendError(
            "the .se1 ephemeris path is not set on this call; refusing to compute — "
            "pyswisseph would silently fall back to the built-in Moshier ephemeris"
        )
    with SWISS_STATE_LOCK:
        swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(sid_mode)
        for body in (swe.SUN, swe.TRUE_NODE):
            _xx, retflag = swe.calc_ut(_PROBE_JD_J2000, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
            if retflag & swe.FLG_JPLEPH or retflag & swe.FLG_MOSEPH or not retflag & swe.FLG_SWIEPH:
                raise SwissThreadBackendError(
                    f"the calling thread's backend is not swieph for body {body} "
                    f"(retflag {retflag:#x}) at {ephe_path!r}: the result would NOT be served by the "
                    "Swiss .se1 files (the library substitutes Moshier/JPL silently)"
                )
