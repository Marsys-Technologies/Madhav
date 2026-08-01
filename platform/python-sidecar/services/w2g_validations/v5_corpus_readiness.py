"""
W2G V5 — v1 corpus completeness and provenance-stamp readiness.

Design §6 V5: "v1 corpus completeness state + provenance stamps ready for
corpus role."
Design §3.1: "v1's fully-materialized century table is ground truth."
ADJUDICATION-6: "2.0 writes generation-stamped rows beside v1 — never over
them. `kala_gochara_windows` data is an untouchable ... every served row
carries its `generation`."

THIS VALIDATION IS READ-ONLY. It touches no row of `kala_gochara_windows`.

It tests two separable claims, and reports which one fails:

  COMPLETENESS — is the corpus actually fully materialized? Row counts alone
  cannot answer this (§N.8: a proxy is not the claim). The real detector is
  the writer's OWN substep plan: `ka_gochara_sweep` plans
  `n_event_classes x _N_YEARS` substeps, and `build_substep_progress` records
  which committed. A chart with rows but with missing substeps has a corpus
  with holes in it, and using it as "ground truth" would silently
  manufacture class-(b) divergences out of years v1 never swept.

  Both `_N_YEARS` and the event-class set are READ FROM THE PRODUCTION CODE
  AND DATA respectively, never restated here (CLAUDE.md §N.7 item 3).

  PROVENANCE — can 2.0 write generation-stamped siblings at all? That needs
  a discriminator. This module DETECTS one rather than assuming: a
  generation-ish column on `kala_gochara_windows`, or the sibling-table
  pattern already precedented in production
  (`kala_gochara_windows__ssv_20260728c`, cited by ADJUDICATION-6). If no
  per-row discriminator exists, the ruling's "every served row carries its
  `generation`" is not yet satisfiable and that is a finding the writer lane
  must close before it writes anything.
"""
from __future__ import annotations

from typing import Any

from ._db import QueryFn, column_names, table_exists
from .types import FAIL, INDETERMINATE, PASS, ValidationResult

WINDOWS_TABLE = "kala_gochara_windows"
PROGRESS_TABLE = "build_substep_progress"
RESONANCE_TABLE = "gochara_resonance_map"
SWEEP_ASSET_ID = "ka_gochara_sweep"

# Column names that would serve as a per-row generation discriminator.
_GENERATION_COLUMN_CANDIDATES = (
    "generation",
    "generation_id",
    "writer_generation",
    "engine_generation",
    "provenance_generation",
)


def _planned_substeps_per_event_class() -> int | None:
    """`_N_YEARS` from the v1 writer itself. Returns None if the orchestrator
    package cannot be imported here — in which case completeness is reported
    as unmeasurable rather than checked against a guessed number."""
    try:
        from services.ka_gochara_sweep.writer import _N_YEARS

        return int(_N_YEARS)
    except Exception:  # noqa: BLE001
        return None


def _detect_generation_discriminator(query: QueryFn) -> dict[str, Any]:
    cols = column_names(query, WINDOWS_TABLE)
    matched = [c for c in cols if c in _GENERATION_COLUMN_CANDIDATES]
    siblings = query(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name LIKE %s AND table_name <> %s "
        "ORDER BY table_name",
        [f"{WINDOWS_TABLE}\\_\\_%", WINDOWS_TABLE],
    )
    return {
        "columns_present": cols,
        "generation_columns_found": matched,
        "candidates_searched": list(_GENERATION_COLUMN_CANDIDATES),
        "sibling_tables": [r["table_name"] for r in siblings],
        "per_row_discriminator_exists": bool(matched),
    }


def validate_v5_corpus_readiness(
    query: QueryFn,
    tier1_chart_ids: list[str],
    all_chart_ids: list[str] | None = None,
) -> ValidationResult:
    title = (
        "V5 — v1 `kala_gochara_windows` corpus completeness (against the writer's own "
        "substep plan) + generation-stamp readiness (ADJUDICATION-6)"
    )
    charts = list(dict.fromkeys(list(tier1_chart_ids) + list(all_chart_ids or [])))

    for table in (WINDOWS_TABLE, PROGRESS_TABLE, RESONANCE_TABLE):
        if not table_exists(query, table):
            return ValidationResult(
                validation_id="V5",
                title=title,
                status=INDETERMINATE,
                summary=f"`{table}` is not present in this database.",
                reason=f"corpus readiness is unmeasurable without `{table}`",
            )

    provenance = _detect_generation_discriminator(query)
    n_years = _planned_substeps_per_event_class()

    corpus_rows = query(
        f"SELECT chart_id::text AS chart_id, COUNT(*) AS n_rows, "
        f"MIN(window_start) AS first_window, MAX(window_end) AS last_window, "
        f"COUNT(DISTINCT event_class) AS n_event_classes, "
        f"COUNT(DISTINCT source) AS n_sources "
        f"FROM {WINDOWS_TABLE} WHERE chart_id::text = ANY(%s) GROUP BY chart_id",
        [charts],
    )
    corpus = {r["chart_id"]: r for r in corpus_rows}

    source_rows = query(
        f"SELECT chart_id::text AS chart_id, source, COUNT(*) AS n "
        f"FROM {WINDOWS_TABLE} WHERE chart_id::text = ANY(%s) "
        f"GROUP BY chart_id, source ORDER BY chart_id, source",
        [charts],
    )

    target_rows = query(
        f"SELECT chart_id::text AS chart_id, COUNT(DISTINCT event_class) AS n_event_classes "
        f"FROM {RESONANCE_TABLE} WHERE chart_id::text = ANY(%s) GROUP BY chart_id",
        [charts],
    )
    planned_classes = {r["chart_id"]: int(r["n_event_classes"]) for r in target_rows}

    committed_rows = query(
        f"SELECT chart_id::text AS chart_id, COUNT(*) AS n_substeps, "
        f"COUNT(DISTINCT build_fingerprint) AS n_fingerprints "
        f"FROM {PROGRESS_TABLE} WHERE asset_id = %s AND chart_id::text = ANY(%s) "
        f"GROUP BY chart_id",
        [SWEEP_ASSET_ID, charts],
    )
    committed = {r["chart_id"]: r for r in committed_rows}

    per_chart: dict[str, Any] = {}
    findings: list[str] = []
    incomplete_tier1: list[str] = []

    for chart_id in charts:
        c = corpus.get(chart_id)
        n_classes = planned_classes.get(chart_id, 0)
        comm = committed.get(chart_id)
        n_committed = int(comm["n_substeps"]) if comm else 0
        planned = n_classes * n_years if (n_years and n_classes) else None

        entry: dict[str, Any] = {
            "rows": int(c["n_rows"]) if c else 0,
            "first_window": str(c["first_window"])[:10] if c else None,
            "last_window": str(c["last_window"])[:10] if c else None,
            "event_classes_in_corpus": int(c["n_event_classes"]) if c else 0,
            "event_classes_planned": n_classes,
            "substeps_committed": n_committed,
            "substeps_planned": planned,
            "build_fingerprints": int(comm["n_fingerprints"]) if comm else 0,
            "sources": {
                r["source"]: int(r["n"]) for r in source_rows if r["chart_id"] == chart_id
            },
        }
        if planned:
            entry["substeps_missing"] = max(planned - n_committed, 0)
            entry["complete"] = n_committed >= planned
            entry["completeness_pct"] = round(100.0 * n_committed / planned, 2)
        else:
            entry["complete"] = None
            entry["substeps_missing"] = None
        per_chart[chart_id] = entry

        if entry["complete"] is False:
            msg = (
                f"chart {chart_id}: v1 corpus is INCOMPLETE — {n_committed}/{planned} "
                f"substeps committed ({entry['completeness_pct']}%), "
                f"{entry['substeps_missing']} missing. It holds {entry['rows']:,} rows, so a "
                "row-count check would call it populated; it is not fully materialized."
            )
            findings.append(msg)
            if chart_id in tier1_chart_ids:
                incomplete_tier1.append(chart_id)

    if n_years is None:
        findings.append(
            "Could not import `_N_YEARS` from `services.ka_gochara_sweep.writer`; "
            "completeness was NOT checked against a substituted constant."
        )

    if not provenance["per_row_discriminator_exists"]:
        findings.append(
            f"`{WINDOWS_TABLE}` carries NO per-row generation discriminator "
            f"(searched {list(_GENERATION_COLUMN_CANDIDATES)}). ADJUDICATION-6 requires "
            "that 2.0 write generation-stamped rows beside v1 and that 'every served row "
            "carries its generation', and that the authority flip be 'flipping one "
            "per-chart authoritative_generation pointer'. Neither is expressible against "
            "the current schema. The writer lane must land the discriminator (column or "
            "the precedented sibling-table pattern) BEFORE it writes a single 2.0 row — "
            "and additively, since v1 data is an untouchable."
        )

    distinct_sources = {s for e in per_chart.values() for s in e["sources"]}
    if len(distinct_sources) <= 1:
        findings.append(
            f"Every v1 row carries the same `source` value ({sorted(distinct_sources) or 'none'}), "
            "so `source` cannot serve as the generation discriminator: it has no "
            "discriminating power today and re-purposing it would mutate v1 rows, which "
            "the untouchable rail forbids."
        )

    tier1_missing_corpus = [c for c in tier1_chart_ids if per_chart.get(c, {}).get("rows", 0) == 0]
    if tier1_missing_corpus:
        findings.append(
            f"Tier-1 charts with NO v1 corpus at all: {tier1_missing_corpus}. "
            "ADJUDICATION-4 Tier 1 requires both canonical charts to carry a full-century "
            "corpus; equivalence work cannot start for a chart without one."
        )

    ready = (
        not incomplete_tier1
        and not tier1_missing_corpus
        and provenance["per_row_discriminator_exists"]
        and n_years is not None
    )

    if ready:
        summary = (
            f"Tier-1 corpora complete and a per-row generation discriminator exists "
            f"({provenance['generation_columns_found']})."
        )
    else:
        summary = (
            "v1 corpus is NOT ready for its ground-truth role: "
            + ("; ".join(
                filter(
                    None,
                    [
                        f"incomplete Tier-1 corpora {incomplete_tier1}" if incomplete_tier1 else "",
                        f"absent Tier-1 corpora {tier1_missing_corpus}" if tier1_missing_corpus else "",
                        "no per-row generation discriminator"
                        if not provenance["per_row_discriminator_exists"]
                        else "",
                    ],
                )
            ))
        )

    return ValidationResult(
        validation_id="V5",
        title=title,
        status=PASS if ready else FAIL,
        summary=summary,
        data={
            "windows_table": WINDOWS_TABLE,
            "tier1_chart_ids": list(tier1_chart_ids),
            "planned_substeps_per_event_class": n_years,
            "per_chart": per_chart,
            "provenance": provenance,
            "incomplete_tier1_charts": incomplete_tier1,
            "read_only": True,
        },
        findings=findings,
    )


__all__ = ["validate_v5_corpus_readiness", "WINDOWS_TABLE"]
