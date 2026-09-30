"""Frozen random-control experiment (protocol v2.3 §7).

ONE frozen experiment, seed 482012, materialised: 20 intervals per held-out
event, each a rolling span of the event's own actual span length in days;
start offset drawn as randrange(0, H − span + 1) (inclusive integer range
[0, H − span]); any-shared-day overlap; unweighted.

The harness never trusts a supplied controls file: it re-draws the experiment
from (registry, merged extract windows) and requires the supplied file to
reproduce the declared draws exactly (same seed, same per-event span lengths,
same draw dates, same per-draw admission). Any mismatch rejects the file.
"""
from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path

from .extract import Extract
from .registry import H_DAYS, H0, Registry

CONTROLS_SEED = 482012
DRAWS_PER_EVENT = 20

EXPERIMENT_DESCRIPTION = (
    "rolling spans at each event's own actual span length in days; domain "
    "randrange(0, H-span+1) inclusive; any-shared-day overlap; unweighted")


class ControlsMismatch(ValueError):
    """A supplied controls file does not reproduce the declared frozen draws."""


def draw_controls(registry: Registry, extract: Extract) -> list[dict]:
    """Re-draw the frozen experiment. Draw order is registry held-event order;
    the RNG stream depends on it, so this must match the pinned draw exactly."""
    rng = random.Random(CONTROLS_SEED)
    ctrl = []
    for e in registry.held:
        lo, hi = e.span()
        span = (hi - lo).days + 1
        hits = 0
        dates = []
        admitted = []
        for _ in range(DRAWS_PER_EVENT):
            off = rng.randrange(0, H_DAYS - span + 1)
            cd = H0 + dt.timedelta(days=off)
            dates.append(cd.isoformat())
            chi = cd + dt.timedelta(days=span - 1)
            hit = any(w.ws <= chi and w.we >= cd
                      for w in extract.merged.get(e.cls, []))
            admitted.append(hit)
            hits += hit
        ctrl.append({"eid": e.eid, "cls": e.cls, "span_days": span,
                     "control_hits": hits, "dates": dates,
                     "_admitted": admitted})
    return ctrl


def verify_controls_file(path: str | Path, registry: Registry,
                         extract: Extract) -> dict:
    """Verify a supplied controls file reproduces the declared draws.

    Returns {"status": "REPRODUCED", "seed": ..., "total_hits": ...,
    "total_draws": ...}. Raises ControlsMismatch on any deviation: wrong seed,
    wrong event set/order, wrong span length, wrong draw dates, or wrong
    admission count.
    """
    path = Path(path)
    doc = json.loads(path.read_text())
    if doc.get("seed") != CONTROLS_SEED:
        raise ControlsMismatch(
            f"controls seed {doc.get('seed')} != frozen seed {CONTROLS_SEED}")
    supplied = doc.get("controls")
    if not isinstance(supplied, list):
        raise ControlsMismatch("controls file has no controls list")

    expected = draw_controls(registry, extract)
    if len(supplied) != len(expected):
        raise ControlsMismatch(
            f"controls count {len(supplied)} != expected {len(expected)}")

    for got, want in zip(supplied, expected):
        for key in ("eid", "cls", "span_days", "control_hits", "dates"):
            if got.get(key) != want[key]:
                raise ControlsMismatch(
                    f"controls draw mismatch for {want['eid']} field {key!r}: "
                    f"file has {got.get(key)!r}, frozen draw gives {want[key]!r}")

    total = sum(c["control_hits"] for c in expected)
    return {"status": "REPRODUCED", "seed": CONTROLS_SEED, "file": path.name,
            "total_hits": total, "total_draws": DRAWS_PER_EVENT * len(expected)}
