"""The two-shard OVERLAP harness (SR-OD1 R8X; A10.1 B4; TRIAL_READY T17, R8X half).

Class shards are separate executions that run AT THE SAME TIME against ONE chart, and the verification job takes the chart lock per class transaction (`verification_job.take_locks`). Whether two
shards really run in parallel — or serialise on that lock — is what decides the effective (G-5) wall, so the harness launches the shards together (a barrier) on the disposable fixture and
reports, per shard, the wall SPLIT into LOCK WAIT (time inside the lock acquisitions: not work) and COMPUTE, and for the pair the overlap, the union (effective) wall and the speedup.

It is a library for tests and for the trial's disposable rehearsal; it holds no credential, opens no connection of its own and never touches anything but the callables it is given (each of which
must use its OWN connection). The Cloud Run two-shard measurement (the other half of T17) is the trial's: `fleet/verification_shards.py overlap` reads its dry-run records."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Callable

from services.gochara_kernel import verification_job as vj


def run_overlap(shards: dict[str, Callable[[], object]]) -> dict:
    """Run every shard callable on its own thread, released together. Returns {"shards": {name: {...}}, "overlapped", "overlap_s", "union_wall_s", "sum_wall_s", "speedup",
    "lock_wait_total_s", "compute_total_s"}. A shard that raised carries its exception under "error" (and no "result"); nothing is swallowed."""
    barrier = threading.Barrier(len(shards))
    out: dict[str, dict] = {}

    def go(name: str, fn: Callable[[], object]) -> None:
        wait0 = vj.lock_wait_s()                                  # per thread: a sibling's wait is never read here
        barrier.wait()
        t0, start = time.monotonic(), datetime.now(timezone.utc)
        rec: dict = {}
        try:
            rec["result"] = fn()
        except BaseException as exc:                              # noqa: BLE001 — reported, not swallowed
            rec["error"] = exc
        wall = time.monotonic() - t0
        wait = min(vj.lock_wait_s() - wait0, wall)
        rec.update(start=start, end=datetime.now(timezone.utc), wall_s=round(wall, 6), lock_wait_s=round(wait, 6), compute_s=round(wall - wait, 6))
        out[name] = rec

    threads = [threading.Thread(target=go, args=(n, f), name=f"overlap-{n}") for n, f in shards.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    spans = [(r["start"], r["end"]) for r in out.values()]
    first, last = min(s for s, _ in spans), max(e for _, e in spans)
    inter = (min(e for _, e in spans) - max(s for s, _ in spans)).total_seconds()
    union = (last - first).total_seconds()
    walls = [r["wall_s"] for r in out.values()]
    return {"shards": out, "overlapped": inter > 0, "overlap_s": round(max(inter, 0.0), 3), "union_wall_s": round(union, 3), "sum_wall_s": round(sum(walls), 3),
            "speedup": round(sum(walls) / union, 3) if union > 0 else None,
            "lock_wait_total_s": round(sum(r["lock_wait_s"] for r in out.values()), 6), "compute_total_s": round(sum(r["compute_s"] for r in out.values()), 6)}
