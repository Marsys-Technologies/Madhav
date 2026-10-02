"""The node convention of the `ephemeris_daily` Rahu/Ketu series — pinned, not assumed.

`ephemeris_daily` stores the TRUE node (`brahmagyan/l0_ephemeris.py` calls
`swe.calc_ut(jd, 11, …)`; migration 1076 declares `node_mode='true'` on the Rahu/Ketu rows
only — the seven non-node bodies carry NULL). Native decision N-69 makes MEAN the system
standard; L0 will gain a second, MEAN, row set under a unique key that includes `node_mode`.
Until that lands every reader of the table has to say which series it means, or the day a
second row set exists it silently reads both (a duplicate date per node body — and, for the
retrograde-day SET in `ka_vedha_gochara`, TRUE and MEAN retrograde days UNIONED).

Two rules every reader here follows:

* NULL-safe pin. `node_mode` is NULL for Sun..Saturn, so a bare `node_mode = 'true'` on a
  multi-body query would silently DROP the seven non-node bodies. The predicate is
  `NODE_SERIES_PREDICATE`: node bodies must match the pinned mode, every other body passes.
* Loud, never merged. Two rows for one (body, date) in the pinned series is an ambiguity the
  caller cannot resolve — `assert_one_row_per_date` raises `NodeSeriesError` rather than let a
  later row overwrite or interleave with an earlier one.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

#: the convention of the series every Gochara-family reader consumes today
SERIES_NODE_MODE = "true"
#: the convention the kernel's own Swiss refinement computes (`knots.py` MEAN_NODE)
KERNEL_NODE_MODE = "mean"
NODE_BODIES: tuple[str, ...] = ("Rahu", "Ketu")

# Literal, not a bind parameter: the predicate is spliced into queries whose parameter lists
# are positional and shared with other code; a constant keeps those lists untouched.
NODE_SERIES_PREDICATE = f"(body NOT IN ('Rahu', 'Ketu') OR node_mode = '{SERIES_NODE_MODE}')"

#: reason recorded when a series root is kept un-refined because the kernel's objective is a
#: different node convention (never refine a TRUE-series root against a MEAN objective)
NODE_CONVENTION_MISMATCH_REASON = (
    f"node_convention_mismatch(series={SERIES_NODE_MODE},kernel={KERNEL_NODE_MODE})"
)


class NodeSeriesError(RuntimeError):
    """The pinned node series is absent or ambiguous for a requested body."""


def series_node_mode_for(body: str) -> str | None:
    """The convention a body's series is read under: the pinned mode for the nodes, None
    (NULL in the table — no convention applies) for every other body."""
    return SERIES_NODE_MODE if body in NODE_BODIES else None


def node_mode_differs_from_kernel(body: str) -> bool:
    """True when `body`'s series convention is not the kernel's own refinement convention."""
    mode = series_node_mode_for(body)
    return mode is not None and mode != KERNEL_NODE_MODE


def assert_one_row_per_date(rows: Iterable[Any], *, context: str) -> None:
    """Raise `NodeSeriesError` if any (body, date) appears twice among `rows`.

    `rows` are mappings or sequences exposing body and date as `row["body"]`/`row["date"]`
    (dict rows) or as the first two positions. Only Rahu/Ketu are checked — the other bodies
    have always been single-row-per-date by the table's unique key.
    """
    seen: set[tuple[str, Any]] = set()
    for row in rows:
        try:
            body, day = row["body"], row["date"]
        except (TypeError, KeyError, IndexError):
            body, day = row[0], row[1]
        if str(body) not in NODE_BODIES:
            continue
        key = (str(body), day)
        if key in seen:
            raise NodeSeriesError(
                f"{context}: two rows for ({body}, {day}) under node_mode="
                f"'{SERIES_NODE_MODE}' — the node series is ambiguous; refusing to merge"
            )
        seen.add(key)
