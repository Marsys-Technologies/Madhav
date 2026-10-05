"""
brahmagyan/mimamsa/l5_bigquery_export.py — DISABLED (refusing stub)
===================================================================

Asset:    mimamsa.bigquery_export (MI-5-5, legacy WS-2 l5-mimamsa export path)

STATUS:   DISABLED by SS N-109 / lifeevents-audit finding F1b. Nothing in this
          module reads data, writes a file, or contacts any external service.
          Every entry point raises `BigQueryExportDisabled`.

WHY:
    The previous implementation built its payload from the hard-coded in-source
    life-event corpus (the native's private events) and stamped whatever
    `chart_id` the caller supplied on every row. The `mimamsa_events` rows carried
    the people-entered free-text `description`; the per-event chart-state rows
    carried event ids, event dates and observed-outcome labels; everything was
    sent to BigQuery (`WRITE_APPEND`) or, as a fallback, written to a local JSONL
    file that ended up committed to git. `life_events` is PEOPLE-ENTERED, PRIVATE,
    chart-scoped data; none of that is acceptable, and the remaining non-text
    tables (chart-state index, calibration substrate, signal multipliers) are all
    derived from that same in-source corpus keyed on event ids/dates, so the whole
    module is neutered rather than partially kept (conservative, per the audit).

IF AN EXPORT IS EVER REQUIRED:
    Write a new module. It must be chart_id-scoped at the SQL level, select columns
    by a whitelist with NO free text and NO event ids/dates, gate on
    `life_events.pool_consent` plus a stated disclosure tier, and log to the real
    `mimamsa_export_log` (migration 355 shape).

The committed `bigquery_export_preview.jsonl` (a generated copy of the old
fallback output) is removed by a separate PR.
"""
from __future__ import annotations

from typing import Any, NoReturn

_DISABLED_MESSAGE = (
    "[STOP] l5_bigquery_export is disabled: life_events is people-entered, private, "
    "chart-scoped data and must never be exported (SS N-109, lifeevents-audit F1b). "
    "This module no longer builds payloads, writes JSONL, or contacts BigQuery/GCS."
)


class BigQueryExportDisabled(RuntimeError):
    """Raised by every entry point of the disabled l5_bigquery_export module."""


def _refuse() -> NoReturn:
    raise BigQueryExportDisabled(_DISABLED_MESSAGE)


def build_export_payload(*args: Any, **kwargs: Any) -> NoReturn:
    """Disabled: refuses to build any event-derived export payload."""
    _refuse()


def export_to_bigquery(*args: Any, **kwargs: Any) -> NoReturn:
    """Disabled: refuses to send anything to BigQuery."""
    _refuse()


def export_to_jsonl(*args: Any, **kwargs: Any) -> NoReturn:
    """Disabled: refuses to write any JSONL export file."""
    _refuse()


def run_export(*args: Any, **kwargs: Any) -> NoReturn:
    """Disabled: refuses to run the L5 OLAP export."""
    _refuse()


def main() -> None:
    """CLI entry point: exits non-zero with the refusal message."""
    raise SystemExit(_DISABLED_MESSAGE)


if __name__ == "__main__":
    main()
