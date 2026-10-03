"""
Per-ayanamsha process isolation.

PyJHora / Swiss-Ephemeris hold sidereal mode as *global* process state
(`swe.set_sid_mode`). Computing five ayanamshas in one process risks state
bleed across calls. `per_ayanamsha` fans the work out to a 5-worker pool so each
ayanamsha computes in its own process with a clean global sidereal mode.

Start-method note: Swiss-Ephemeris (via PyJHora) keeps its ephemeris + sidereal
state as initialised C-level global state. A 'spawn' child re-imports the
package fresh but does NOT inherit that initialised ephemeris state, which makes
swisseph fall back to a mis-ranged Moshier path and raise. 'fork' children
inherit the parent's fully-initialised swisseph state and compute correctly, so
we PREFER 'fork' here. We fall back to 'forkserver'/'spawn' only if 'fork' is
unavailable (the worker is module-level so it stays picklable for those cases).
The package import in ._jhora guarantees swisseph is initialised in the parent
before any fork.

Swiss backend (TI-ephemeris-fix-001): on Linux the swisseph C state (ephemeris path, sidereal
mode) is THREAD-local, and a forked worker inherits only whatever the forking thread had
pinned, which nothing ever probed.  So the worker's first line (``_worker``) calls
``ensure_swiss_backend(jd_ut)`` in the process/thread that computes (fail-closed: an unusable
corpus or an out-of-window date raises in the worker and propagates through ``pool.map``).  It is
the task, not a Pool ``initializer``, on purpose: an initializer that raises makes
``multiprocessing.Pool`` respawn its workers forever (a hang), a task that raises just fails the
map.  The Pool is created while holding the Swiss state lock, so no other thread can hold it at
fork time (a fork-inherited, never-released lock would deadlock the child's ``ensure``).
"""
from __future__ import annotations

import multiprocessing as mp
from typing import Any, Callable

# Ensure swisseph is initialised in the parent before any fork.
from . import _jhora  # noqa: F401
from panchang_engine.swiss_backend import ensure_swiss_backend
from panchang_engine.swiss_state import swiss_state_scope

AYANAMSHAS = ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]


def _worker(args):
    fn, jd_ut, ayanamsha_id, kwargs = args
    ensure_swiss_backend(jd_ut)  # this process/thread computes: pin + probe it here (module doc)
    return fn(jd_ut, ayanamsha_id=ayanamsha_id, **kwargs)


def _get_ctx() -> "mp.context.BaseContext":
    for method in ("fork", "forkserver", "spawn"):
        try:
            return mp.get_context(method)
        except ValueError:
            continue
    return mp.get_context()


def per_ayanamsha(fn: Callable, jd_ut: float, **kwargs) -> dict[str, Any]:
    """Run `fn(jd_ut, ayanamsha_id=<a>, **kwargs)` for each of the five
    canonical ayanamshas in isolated processes. Returns
    {ayanamsha_id -> result}.
    """
    ctx = _get_ctx()
    payload = [(fn, jd_ut, a, kwargs) for a in AYANAMSHAS]
    with swiss_state_scope():  # no other thread may hold the Swiss lock while the children fork
        pool = ctx.Pool(processes=5)
    with pool:
        results = pool.map(_worker, payload)
    return dict(zip(AYANAMSHAS, results))
