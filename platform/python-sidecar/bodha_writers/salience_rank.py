"""bodha_writers.salience_rank — the one in-memory salience-percentile pass.

NIRMĀṆA L2-W3 (L2_W2_DECIDE_v1_0.md N-16 / W1 finding D5).

`bodha_msr_signals.salience_pctl_in_class` is the column the D-SALIENCE tail lane
ranks on: a rare-class leader is a row in the top decile *of its own class* that
sits below the chart-wide salience fold. W1 measured the column as honestly computed
(1,308 distinct values on the canonical chart) — but NULL on exactly 149 rows, and
those 149 are the six RAREST classes in the layer:

    sudarshana_agreement 45 · nakshatra_semantic 45 · arudha 25 ·
    special_lagna 20 · dhana_axis 10 · vargottama_amplification 4

They are NULL because each is written by its own satellite writer, and only
`bo_laksana` ran the percentile pass. So the rare-class-leader predicate silently
excluded precisely the population it exists to surface — a tail lane blind to the
tail.

This module exists so the pass has ONE implementation. The alternative — copying
`bo_laksana`'s version into five satellite writers — is the defect this same wave
removed elsewhere in the layer (two dead copies of `HOUSE_WEIGHT` / `_av_multiplier`
shadowing `formulas.py`, one of which had drifted into a units bug nobody noticed).

Scope note, stated because it is load-bearing rather than incidental: each satellite
writer owns its class ENTIRELY — `bo_sudarshana` writes every `sudarshana_agreement`
row for a chart and ayanamsha and nothing else does. So a percentile computed over
one writer's own rows for one ayanamsha IS the true class-scoped percentile, not an
approximation of it. That equivalence is what makes a per-writer in-memory pass
correct here; it would NOT hold for a class written by two writers.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def set_salience_pctl_in_class(rows: list[dict]) -> None:
    """Set `salience_pctl_in_class` in place, per (signal_type_class).

    The in-memory equivalent of
    ``PERCENT_RANK() OVER (PARTITION BY chart_id, ayanamsha_id, signal_type_class
    ORDER BY computed_salience)``. Callers pass rows already scoped to a single
    (chart_id, ayanamsha_id) — every Bodha MSR writer processes one ayanamsha per
    substep — so partitioning by `signal_type_class` alone is equivalent.

    PERCENT_RANK semantics, matched exactly: RANK() with ties sharing the minimum
    rank, and a single-row partition yielding 0.0.

    Computed in memory rather than by a post-insert UPDATE for a measured reason
    (BA-P3, 2026-07-06): updating one scalar column on ~28K freshly-inserted rows
    ran 600s+, CPU/IO bound, because it forces a full-row rewrite against this
    table's 20 indexes including 3 GIN on jsonb arrays. Done here it costs nothing —
    the value rides the INSERT that was happening anyway.

    Rows missing `computed_salience` are left untouched with an unset percentile
    rather than defaulted to 0.0, which would place them at the bottom of their
    class as though measured.
    """
    by_class: dict[Any, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("computed_salience") is None:
            continue
        by_class[row.get("signal_type_class")].append(row)

    for cls_rows in by_class.values():
        n = len(cls_rows)
        if n <= 1:
            for row in cls_rows:
                row["salience_pctl_in_class"] = 0.0
            continue
        # RANK with ties sharing the minimum: ascending, a value's rank is
        # 1 + (count of strictly smaller values) = the 1-based index of its first
        # occurrence in the sorted order.
        ordered = sorted(cls_rows, key=lambda r: r["computed_salience"])
        rank_by_salience: dict[Any, int] = {}
        for i, row in enumerate(ordered):
            salience = row["computed_salience"]
            if salience not in rank_by_salience:
                rank_by_salience[salience] = i + 1
        for row in cls_rows:
            rank = rank_by_salience[row["computed_salience"]]
            row["salience_pctl_in_class"] = round((rank - 1) / (n - 1), 6)
