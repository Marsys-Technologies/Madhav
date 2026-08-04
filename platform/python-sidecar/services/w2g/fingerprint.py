"""W2G — delta-aware invalidation fingerprints.

THE INCIDENT THIS PREVENTS (it already happened, once, expensively). v1's
`ka_gochara_sweep` computes ONE build fingerprint over, among other things,
the whole event-class list. Item 9 added a single event class (health/adverse).
The fingerprint changed, so the sweep took its full-replan branch: per-chart
delete-then-insert of `kala_gochara_windows` plus ALL ~606 substeps rather
than the ~303 genuinely new ones — a multi-dispatch, multi-hour rebuild per
chart, for a one-class addition. The ledger records the cost
(SHAD_DARSHANA_STATE.md, ADJUDICATION-14 §3 note).

W2G's design amendment 2 (lane (b), 2026-08-04) makes that structurally
impossible: fingerprints are computed PER CLASS and PER BODY, never once over
everything, so an invalidation is exactly as wide as the change that caused it.

The two directions are both tested, because delta-awareness that never
invalidates is worse than no delta-awareness at all:

  * changing ONE class's grammar version invalidates ONLY that class;
  * rebuilding the arc substrate invalidates EVERY class that reads it.

Set-valued inputs are canonicalized (sorted) before hashing, so a fingerprint
never depends on the order Postgres happened to return rows in.
"""
from __future__ import annotations

import hashlib
from typing import Iterable, Mapping

# Bumped whenever the arc-building maths changes in a way that would move a
# stored arc. A pure refactor does NOT bump it; a change to station detection,
# wrap splitting or the interpolant does.
ARC_ENGINE_VERSION = "w2g_arcs_v01"

FINGERPRINT_LENGTH = 16


def _digest(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"\x1f")  # unit separator: "ab|c" and "a|bc" must differ
    return h.hexdigest()[:FINGERPRINT_LENGTH]


def arc_fingerprint(
    body: str,
    epoch_start_jd: float,
    epoch_end_jd: float,
    knot_count: int,
    engine_version: str = ARC_ENGINE_VERSION,
) -> str:
    """Identity of one body's materialized arc set.

    Deliberately made of the INPUTS (body, epoch bounds, knot count, engine
    version) rather than of the output rows: it has to be computable BEFORE
    deciding whether to rebuild, which is the entire point of an invalidation
    fingerprint. Knot count is the cheap, honest proxy for "the ephemeris rows
    underneath changed" — an extended epoch or a backfilled gap both move it.
    """
    return _digest(
        engine_version,
        str(body),
        f"{float(epoch_start_jd):.6f}",
        f"{float(epoch_end_jd):.6f}",
        str(int(knot_count)),
    )


def class_fingerprint(
    event_class: str,
    grammar_version: str,
    target_refs: Iterable[str],
    bodies: Iterable[str],
    arc_fingerprints: Mapping[str, str],
) -> str:
    """Identity of one (chart, event_class) contact computation.

    Inputs, all of them and only them:
      * the class and its grammar version — a one-class grammar edit moves
        this class and nothing else;
      * the class's resonance targets — adding a target is a real change;
      * the bodies consulted, and the arc fingerprint of each — a substrate
        rebuild moves every class that reads the rebuilt body.

    `chart_id` is NOT an input: the fingerprint is stored per (chart_id,
    event_class) row, so folding the chart id into the hash would only make
    two identical computations look different.
    """
    bodies_sorted = sorted({str(b) for b in bodies})
    targets_sorted = sorted({str(t) for t in target_refs})
    substrate = ",".join(f"{b}={arc_fingerprints.get(b, 'ABSENT')}" for b in bodies_sorted)
    return _digest(
        str(event_class),
        str(grammar_version),
        ",".join(targets_sorted),
        substrate,
    )


def classes_needing_rebuild(
    stored: Mapping[str, str], computed: Mapping[str, str]
) -> list[str]:
    """The classes whose fingerprint moved, plus any class that is new.

    A class present in `stored` but absent from `computed` is NOT returned —
    it was removed, and removal is a delete, not a rebuild. Callers that need
    the removals ask for them explicitly rather than having them smuggled into
    a rebuild list.
    """
    out = [cls for cls, fp in computed.items() if stored.get(cls) != fp]
    return sorted(out)


__all__ = [
    "ARC_ENGINE_VERSION",
    "FINGERPRINT_LENGTH",
    "arc_fingerprint",
    "class_fingerprint",
    "classes_needing_rebuild",
]
