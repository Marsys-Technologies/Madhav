"""Duplicate-natural-key guard for chart_facts-shaped row batches.

``chart_facts`` has a unique natural key
``(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)`` (the partial
index ``chart_facts_unique_null_formula``) and a primary key on ``fact_id``.  Writers that
upsert (``ON CONFLICT ... DO UPDATE``/``DO NOTHING``) silently collapse two emitted rows for one
key into one stored row while still counting both in ``rows_inserted``.  The L1 data-plane
completion check (``complete_l1_data_plane_partition``) compares ``rows_inserted`` with the number of
distinct protected-capture row identities, so a collapse surfaces only there, after the whole
build, as an unexplained "reported N rows but protected capture contains M" failure.

TI-l1-writer-fixes-001: ``ga_strength`` emitted its ayanamsha-invariant rows (naisargika bala,
required shadbala rupa) once per ayanamsha batch instead of once per build -- 16 natural keys x 5
emissions = 64 surplus rows, with the ``required_rupa`` rows additionally carrying a different
``fact_id`` per emission for one stored row.  This guard turns that whole class into an immediate,
named failure at the writer, before any row is written.

The guard is deliberately NOT wired through ``_idempotency.py`` (imported by nearly every L1
writer); callers opt in, so only their own source digest moves.
"""

from __future__ import annotations

from typing import Any, Iterable

CHART_FACTS_NATURAL_KEY: tuple[str, ...] = (
    "chart_id",
    "ayanamsha_id",
    "fact_category",
    "fact_subject",
    "fact_key",
    "build_id",
)


class DuplicateNaturalKeyError(RuntimeError):
    """Two emitted rows share a natural key (or one fact_id names two natural keys)."""


def assert_unique_natural_keys(
    rows: Iterable[dict[str, Any]],
    seen: dict[tuple, str] | None = None,
    *,
    key_columns: tuple[str, ...] = CHART_FACTS_NATURAL_KEY,
    identity_column: str = "fact_id",
    context: str = "",
) -> int:
    """Raise :class:`DuplicateNaturalKeyError` naming the first offending key.

    ``seen`` maps natural key -> identity and is mutated, so one dict passed to every batch of a
    build also catches a key repeated ACROSS batches (the ga_strength failure mode).  A fact_id that
    resolves to two different natural keys is rejected too (a row-identity collision).
    Returns the number of rows checked.
    """
    if seen is None:
        seen = {}
    owners: dict[str, tuple] = {}
    for key, ident in seen.items():
        if ident is not None:
            owners[ident] = key
    prefix = f"{context}: " if context else ""
    checked = 0
    for row in rows:
        key = tuple(row.get(col) for col in key_columns)
        ident = row.get(identity_column)
        if key in seen:
            raise DuplicateNaturalKeyError(
                f"{prefix}duplicate natural key {dict(zip(key_columns, key))} "
                f"({identity_column} {seen[key]!r} then {ident!r}): two rows emitted for one fact key"
            )
        if ident is not None and ident in owners:
            raise DuplicateNaturalKeyError(
                f"{prefix}{identity_column} {ident!r} names two natural keys: "
                f"{dict(zip(key_columns, owners[ident]))} and {dict(zip(key_columns, key))}"
            )
        seen[key] = ident
        if ident is not None:
            owners[ident] = key
        checked += 1
    return checked
