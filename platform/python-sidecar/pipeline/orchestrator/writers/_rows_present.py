"""Rows ACTUALLY PRESENT in an asset's declared produced-table set (WFIX-A).

Why this exists. The orchestrator records ``rows_written = rows_inserted + rows_updated`` (asset_runner.py). Several writers reported a
*changed* count instead: ``cur.rowcount`` of the last ``executemany`` (bg_ephemeris: 0 on a no-change rerun against 825,084 live rows), an
inserted-only figure (bg_cohort: 10,000 against 110,000 across its two tables), the rows an ``UPDATE`` touched (bg_text_index), and so on. The
census's Build.completion check compares the build record with the rows present in the asset's declared produced-table set, so a changed count
reads as a mismatch even when the data is complete.

The contract this module serves (CLAUDE.md section N.2, unchanged): a writer still returns the frozen ``WriterResult``; it reads the count on
``ctx.db_conn`` (same transaction, so it sees its own uncommitted writes) and never commits, closes, or writes through that read. ``rows_updated``
stays 0 so the orchestrator's ``rows_inserted + rows_updated`` is exactly the present count and is never double counted.

Why the SQL is NOT built here. Each writer carries its count as a LITERAL ``SELECT count(*) ...`` statement (a module constant) and executes it
itself: the census's reads-match / Idem scans are static, follow the writer's delegation chain, and read a table name built at run time as "named
dynamically, so the read is not resolvable" -- which would withdraw Build.dag's PASS and the dep-liveness N/A of every asset that used a generic
counting helper. A literal statement is parsed, attributed to the asset's own tables and checked. This module therefore holds only the one thing
that is not SQL: turning the fetched row into a trustworthy integer (a dict row from the orchestrator connection or a tuple row from a test
connection; never a silent zero for a missing or non-count answer).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def present_count(row: Any) -> int:
    """The single count column of ``row`` as an int; an error (never 0) for anything that is not a row count."""
    value = None if row is None else (next(iter(row.values())) if isinstance(row, Mapping) else row[0])
    if value is None or isinstance(value, bool) or int(value) != value or int(value) < 0:
        raise RuntimeError(f"rows_present: count query returned {value!r}, not a row count")
    return int(value)
