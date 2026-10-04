"""Real-thread harness for Swiss Ephemeris per-thread-state tests (TI thread-fix lane, 2026-10-03).

On LINUX pyswisseph keeps the sidereal mode and the ephemeris path PER THREAD: a fresh thread starts
in Fagan-Bradley; a reused pool thread keeps whatever ayanamsha the previous task on it left.  On
macOS the same state is process-wide, so these helpers are only DISCRIMINATING on Linux (CI is
Linux); every primary assertion built on them also holds on macOS.  Nothing here is marked
``integration``: the py-sidecar CI job must run it.

Three ways to run a callable, all on a REAL thread, with the calling (main) thread deliberately
left in Fagan-Bradley by the ``main_thread_in_fagan`` fixture:

* ``run_in_fresh_thread(fn)``       - a brand-new ``threading.Thread`` (library default state);
* ``run_in_dirty_pool_thread(fn)``  - a ``ThreadPoolExecutor(max_workers=1)`` worker that a previous
  task left in a DIFFERENT ayanamsha (true_chitra), then reused for ``fn`` (reuse safety: the
  orchestrator's asset pool threads are reused across assets);
* ``run_in_lahiri_thread(fn)``      - the reference: a thread that selects Lahiri itself first.

``SiderealModeSpy`` records, for every sidereal ``swe.calc_ut`` call made while it is installed, the
ayanamsa value in force on the calling thread at that instant (``swe.get_ayanamsa_ut``).  It makes a
function's mode discipline observable even where its numeric result is mode-insensitive (e.g. the
SIGN of Saturn's longitude speed).
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import pytest
import swisseph as swe

# The shared pinned reference with Pravaha's SHA-pinned corpus: Sun, Lahiri, JD 2451545.0.
PINNED_SUN_LAHIRI_J2000 = 256.5156961838706
PINNED_JD = 2451545.0
# What an UNPREPARED fresh thread (library default = Fagan-Bradley) misses it by (deg).
PINNED_FRESH_THREAD_MISS_DEG = 0.8832076
# Flags of the pinned reference: the canonical .se1 backend, sidereal.
PINNED_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL


def _box_run(fn: Callable[[], Any]) -> Any:
    box: dict[str, Any] = {}

    def runner() -> None:
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller's thread
            box["error"] = exc

    t = threading.Thread(target=runner)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box["value"]


def run_in_fresh_thread(fn: Callable[[], Any]) -> Any:
    """Run ``fn`` on a brand-new thread (nothing selected on it)."""
    return _box_run(fn)


def run_in_dirty_pool_thread(fn: Callable[[], Any], *, dirty_sidm: int = swe.SIDM_TRUE_CITRA) -> Any:
    """Run ``fn`` on a REUSED pool thread whose previous task left ``dirty_sidm`` selected."""
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="asset") as pool:
        first = pool.submit(lambda: (swe.set_sid_mode(dirty_sidm), threading.get_ident())[1]).result()
        out = pool.submit(lambda: (threading.get_ident(), fn())).result()
        assert out[0] == first, "pool did not reuse its single worker thread"
        return out[1]


def run_in_lahiri_thread(fn: Callable[[], Any]) -> Any:
    """Reference: run ``fn`` on a thread that explicitly selected Lahiri first (raw swe AND PyJHora)."""
    def prepared() -> Any:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        try:
            from pyjhora_adapter._jhora import drik

            drik.set_ayanamsa_mode("LAHIRI")
        except Exception:  # pragma: no cover - PyJHora absent: raw swe reference only
            pass
        return fn()

    return _box_run(prepared)


def lahiri_ayanamsa_at(jd: float) -> float:
    """The Lahiri ayanamsa at ``jd``, read on a thread that selected Lahiri itself."""
    return _box_run(lambda: (swe.set_sid_mode(swe.SIDM_LAHIRI), swe.get_ayanamsa_ut(jd))[1])


class SiderealModeSpy:
    """Record the ayanamsa in force on the calling thread at every sidereal ``swe.calc_ut`` call."""

    def __init__(self, monkeypatch) -> None:
        self.calls: list[tuple[float, float]] = []  # (jd, ayanamsa in force)
        real = swe.calc_ut
        default_flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        spy = self

        def calc_ut(jd, planet, *args, **kwargs):
            flags = args[0] if args else kwargs.get("flags", default_flags)
            if flags & swe.FLG_SIDEREAL:
                spy.calls.append((float(jd), swe.get_ayanamsa_ut(jd)))
            return real(jd, planet, *args, **kwargs)

        monkeypatch.setattr(swe, "calc_ut", calc_ut)

    def wrong_mode_calls(self, *, tol: float = 1e-9) -> list[tuple[float, float, float]]:
        """(jd, ayanamsa seen, Lahiri ayanamsa) for every recorded call NOT made under Lahiri."""
        out = []
        for jd, seen in self.calls:
            want = lahiri_ayanamsa_at(jd)
            if abs(seen - want) > tol:
                out.append((jd, seen, want))
        return out


@pytest.fixture
def main_thread_in_fagan():
    """Leave the MAIN thread in Fagan-Bradley (the library default a fresh thread also starts in),
    so a function that wrongly inherits ambient state computes under the WRONG ayanamsha."""
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
    yield
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    try:
        from pyjhora_adapter._jhora import drik

        drik.set_ayanamsa_mode("LAHIRI")
    except Exception:  # pragma: no cover
        pass
