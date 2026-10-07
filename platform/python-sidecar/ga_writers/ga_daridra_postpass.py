"""Daridra dosha_label post-pass: the one ga_structural fact that must be emitted DOWNSTREAM.

Why this module exists (TI-ga-structural-cycle-001, Strategic Suvarna ruling: "circular read move",
design: POST/FIX_LIST_TRIAGE.md section 4).  The daridra cancellation (bhanga) grounds read two
products that DEPEND ON ga_structural:

  * chart_vichara (ga_vichara): the wealth varga_ratification row, whose d1_dignity is the
    "11th lord exalted" ground;
  * ga_yoga_firings (ga_yoga): the fired dhana-family yogas, the "dhana structure fires" ground.

ga_structural reading them made ga_structural -> ga_vichara -> ga_structural a cycle and the verdict
build-order dependent (a clean build read None / [] and silently skipped the cancellation).  With no new
DAG edge, the read now lives here and ga_vichara (which already depends on ga_structural and ga_yoga)
runs emit_daridra_label_post_pass after it has written its own chart_vichara rows.

What is guaranteed unchanged: the row is built by the SAME ga_structural_writer._build_dosha_rows
code path (same bespoke detector, same constituent-fact resolver, same row shape), so the natural key
(dosha_label / daridra / dosha_name), therefore the deterministic fact_id, and every
stored value equal what a correctly ordered ga_structural build produced.  Only the PRODUCER (and so
build_id) changes.  The three functions below were moved VERBATIM from ga_structural_writer.py.

Scope of the write: ONE row per (chart, ayanamsha), chart_facts category dosha_label, subject
daridra.  The delete is scoped to that subject (never the whole category, which ga_structural owns).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from brahmagyan.verification_tiers import emit_tier
from brahmagyan.verification_vocab import assert_legal
from ga_writers import ga_structural_writer as _gsw
from ga_writers._idempotency import authorize_chart_fact_delete
from ga_writers.ga_structural_writer import (
    EXALTATION_SIGNS,
    PLANET_TO_SUBJECT,
    _get_house_lord,
    _graha_in_sign,
)

logger = logging.getLogger(__name__)

DARIDRA = "daridra"

# The INSERT of the daridra row. The statement is the one ga_structural's `_CF_INSERT_SQL` has (a test pins the two
# texts equal); it is repeated here so this module's write is a plain column-list INSERT whose parameters are a
# LITERAL TUPLE built row by row, which is what the writer-source scan can follow (ga_structural's
# `tuples.append(tuple(row.get(c) for c in COLS))` before an executemany it cannot).
_DARIDRA_INSERT_SQL = """
    INSERT INTO chart_facts
      (fact_id, chart_id, ayanamsha_id, build_id,
       fact_category, fact_subject, fact_key,
       fact_value_text, fact_value_num, fact_value_jsonb,
       unit, citation_ref, citation_human,
       source_calculation, verification_pass_status,
       engine_version, computed_at, formula_provenance_text)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
    WHERE formula_id IS NULL
    DO UPDATE SET
      fact_id          = EXCLUDED.fact_id,
      fact_value_num   = EXCLUDED.fact_value_num,
      fact_value_text  = EXCLUDED.fact_value_text,
      fact_value_jsonb = EXCLUDED.fact_value_jsonb,
      citation_ref     = EXCLUDED.citation_ref,
      citation_human   = EXCLUDED.citation_human,
      verification_pass_status = EXCLUDED.verification_pass_status,
      engine_version   = EXCLUDED.engine_version,
      computed_at      = EXCLUDED.computed_at,
      formula_provenance_text = EXCLUDED.formula_provenance_text
"""


def insert_daridra_label_rows(conn: Any, rows: list[dict[str, Any]]) -> int:
    """INSERT the daridra dosha_label row(s); returns the number written. Never commits, never deletes
    (the subject-scoped delete is `replace_prior_daridra_label_rows`). Each row is bound as a literal tuple."""
    written = 0
    for r in rows:
        emit_tier(r["verification_pass_status"], table="chart_facts")        # Q-L1-16(a): refuse a bad tier before the write
        assert_legal(r["verification_pass_status"], table="chart_facts")
        v = r.get("fact_value_jsonb")
        jsonb = json.dumps(v) if isinstance(v, (dict, list)) else v
        with conn.cursor() as cur:
            cur.execute(_DARIDRA_INSERT_SQL, (
                r["fact_id"], r["chart_id"], r["ayanamsha_id"], r["build_id"],
                r["fact_category"], r["fact_subject"], r["fact_key"],
                r.get("fact_value_text"), r.get("fact_value_num"), jsonb,
                r.get("unit"), r.get("citation_ref"), r.get("citation_human"),
                r.get("source_calculation"), r["verification_pass_status"],
                r.get("engine_version"), r.get("computed_at"), r.get("formula_provenance_text"),
            ))
        written += 1
    return written


def _load_wealth_ratification(conn: Any, chart_id: str, ayanamsha_id: str, subj: str) -> dict[str, Any] | None:
    """Read ga_vichara's `varga_ratification` row (domain='wealth') for
    `subj` (a PLANET_TO_SUBJECT code) — this IS the '11L/2L strength' signal
    the brief calls for (cross-varga dignity agreement over the wealth-house
    lords + Jupiter karaka), computed once by ga_vichara and never
    re-derived here (§N.5 L1/L1.5-authority discipline). Returns None on any
    DB error/absence — an honest gap, not a fabricated strength."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT value_num, value_jsonb FROM chart_vichara
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND vichara_family = 'varga_ratification' AND domain = 'wealth' AND subject = %s
                LIMIT 1
            """, (chart_id, ayanamsha_id, subj))
            row = cur.fetchone()
    except Exception as exc:
        logger.warning(
            "[ga_structural_writer] chart_vichara unavailable for daridra cancellation (chart=%s ayanamsha=%s): %s",
            chart_id, ayanamsha_id, exc,
        )
        return None
    if not row:
        return None
    # Orchestrator connections use psycopg3's dict_row factory (pipeline/
    # orchestrator/db.py) — rows are dict-like, not tuples. See the sibling
    # fix in _dhana_yoga_fires_for for the same bug class (KeyError: 0).
    if isinstance(row, dict):
        value_num, value_jsonb = row.get("value_num"), row.get("value_jsonb")
    else:
        value_num, value_jsonb = row[0], row[1]
    if isinstance(value_jsonb, str):
        try:
            value_jsonb = json.loads(value_jsonb)
        except Exception:
            value_jsonb = {}
    return {"ratification_factor": value_num, **(value_jsonb or {})}


def _dhana_yoga_fires_for(conn: Any, chart_id: str, ayanamsha_id: str, planets: set[str]) -> list[str]:
    """Fired `ga_yoga_firings` rows whose canonical_id names a dhana-family
    yoga AND whose constituent_planets intersect `planets` — read-only L1
    consumption (§N.5), never a second dhana detector."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT yoga_canonical_id, constituent_planets FROM ga_yoga_firings
                WHERE chart_id = %s AND ayanamsha_id = %s AND fired = TRUE
                  AND yoga_canonical_id ILIKE %s
            """, (chart_id, ayanamsha_id, "%dhana%"))
            rows = cur.fetchall()
    except Exception as exc:
        logger.warning(
            "[ga_structural_writer] ga_yoga_firings unavailable for daridra cancellation (chart=%s ayanamsha=%s): %s",
            chart_id, ayanamsha_id, exc,
        )
        return []
    lowered = {p.lower() for p in planets}
    hits: list[str] = []
    for row in rows:
        # Orchestrator connections use psycopg3's dict_row factory (pipeline/
        # orchestrator/db.py) — rows are dict-like, not tuples. Access by
        # column name, with a defensive fallback for any caller that still
        # passes a tuple-row connection (e.g. a legacy standalone-CLI path).
        if isinstance(row, dict):
            cid, cp = row.get("yoga_canonical_id"), row.get("constituent_planets")
        else:
            cid, cp = row[0], row[1]
        if isinstance(cp, str):
            try:
                cp = json.loads(cp)
            except Exception:
                cp = []
        if any(str(p).lower() in lowered for p in (cp or [])):
            hits.append(cid)
    return hits


def _cancel_daridra(
    finding: dict[str, Any], chart_output: dict[str, Any],
    conn: Any, chart_id: str, ayanamsha_id: str,
) -> dict[str, Any]:
    """Mandatory cancellation — brahma_dosha_catalog's own stored
    cancellation_conditions for daridra ('dhana/raja yoga present' /
    '11th lord retrograde-strong'); this implementation encodes the brief's
    literal ground set (11L exalted / 2L-9L dhana structure fires), citing
    ga_vichara for the 11L-strength ground (design §11 varga_ratification IS
    the '11L/2L strength' signal) and ga_yoga_firings for the dhana-structure
    ground — never re-deriving either."""
    ref = "bphs:daridra:dhana_yoga_or_strong_wealth_lord_cancels"
    lord11 = finding["lord11"]
    lord9 = _get_house_lord(chart_output, 9)
    subj11 = PLANET_TO_SUBJECT.get(lord11, lord11.upper())

    grounds: list[str] = []

    # Ground A: 11L exalted — ga_vichara varga_ratification (domain=wealth)
    # is the cross-varga corroboration; fall back to the direct D1 sign
    # check (same source _detect_daridra already reads) if vichara is dark.
    vichara = _load_wealth_ratification(conn, chart_id, ayanamsha_id, subj11)
    d1_dignity = (vichara or {}).get("d1_dignity")
    if d1_dignity == "exalted":
        grounds.append(f"11L_{lord11}_exalted_per_ga_vichara_varga_ratification")
    elif EXALTATION_SIGNS.get(lord11) == _graha_in_sign(chart_output, lord11):
        grounds.append(f"11L_{lord11}_exalted_d1")

    # Ground B: 2L-9L (or 11L-anchored) dhana structure genuinely fires.
    dhana_hits = _dhana_yoga_fires_for(conn, chart_id, ayanamsha_id, {finding["lord2"], lord9, lord11})
    if dhana_hits:
        grounds.append(f"dhana_structure_fires:{','.join(sorted(set(dhana_hits)))}")

    if grounds:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": ";".join(grounds),
            "cancellation_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "brahma_dosha_catalog daridra cancellation_conditions ('dhana/raja yoga present'): "
                f"{'; '.join(grounds)} — Daridra does not serve as a finding."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "cancellation_na_reason": None,
        "citation_ref": ref,
        "citation_human": "Neither the 11th lord exaltation ground nor a fired dhana structure was found — Daridra stands uncancelled.",
    }


# ── Post-pass driver ──────────────────────────────────────────────────────────

def build_daridra_label_rows(
    conn: Any,
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    *,
    birth_params: dict[str, Any] | None = None,
    chart_output: dict[str, Any] | None = None,
    dosha_catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """The daridra dosha_label row(s) for one (chart, ayanamsha), built by ga_structural's own
    label-pass code with the downstream cancellation wired in.  Returns [] when daridra does not form
    for the chart (honest absence, exactly as before) or a READABLE catalog has no daridra entry.
    An EMPTY catalog (which is also what ga_structural's loader returns when the table is unreadable)
    raises: the caller deletes the prior daridra row afterwards, and "no catalog" is not "daridra does
    not form"."""
    catalog = dosha_catalog if dosha_catalog is not None else _gsw._load_dosha_catalog(conn)
    if not catalog:
        raise RuntimeError(
            "[ga_daridra_postpass] brahma_dosha_catalog is empty or unreadable for chart "
            f"{chart_id} ayanamsha {ayanamsha_id}: refusing to treat that as 'daridra does not form' "
            "(the prior daridra dosha_label row is left untouched; fix the catalog and rebuild ga_vichara)"
        )
    entries = [e for e in catalog if e["canonical_id"] == DARIDRA]
    if not entries:
        return []
    if chart_output is None:
        bp = _gsw.resolve_birth_params(chart_id, birth_params)
        chart_output = _gsw.compute_chart(inputs=bp, ayanamsha_id=_gsw.CANONICAL_AYANAMSHAS[ayanamsha_id])
        _gsw._validate_chart_output_complete(chart_output)
    return _gsw._build_dosha_rows(
        conn, chart_output, chart_id, build_id, ayanamsha_id,
        datetime.now(timezone.utc).isoformat(), _gsw.ENGINE_VERSION, entries,
        downstream_doshas=frozenset(),
        extra_cancellations={DARIDRA: _cancel_daridra},
    )


def replace_prior_daridra_label_rows(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    """Delete this chart's prior daridra dosha_label row(s) for one ayanamsha (subject-scoped:
    the rest of the dosha_label category belongs to ga_structural)."""
    authorize_chart_fact_delete(conn, chart_id, ["dosha_label"], [ayanamsha_id])
    cur = conn.execute(
        "DELETE FROM chart_facts WHERE chart_id = %s AND ayanamsha_id = %s "
        "AND fact_category = 'dosha_label' AND fact_subject = %s",
        [chart_id, ayanamsha_id, DARIDRA],
    )
    return getattr(cur, "rowcount", 0) or 0


def emit_daridra_label_post_pass(
    conn: Any,
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    *,
    birth_params: dict[str, Any] | None = None,
) -> int:
    """Delete-then-insert the daridra dosha_label row.  Must run AFTER ga_yoga (ga_yoga_firings)
    and after ga_vichara's own chart_vichara insert for this ayanamsha (it reads both).  Returns
    the number of chart_facts rows written (0 or 1): ga_vichara COUNTS it in its rows_written.  Never commits."""
    rows = build_daridra_label_rows(conn, chart_id, build_id, ayanamsha_id, birth_params=birth_params)
    deleted = replace_prior_daridra_label_rows(conn, chart_id, ayanamsha_id)
    if not rows:
        logger.info("[ga_daridra_postpass] chart=%s ayanamsha=%s: daridra does not form; deleted %d prior row(s)",
                    chart_id, ayanamsha_id, deleted)
        return 0
    _gsw._verify_no_duplicate_fact_ids(rows)
    _gsw._verify_citation_completeness(rows)
    _gsw._linter_check_rows(rows)
    written = insert_daridra_label_rows(conn, rows)
    logger.info("[ga_daridra_postpass] chart=%s ayanamsha=%s: wrote %d daridra dosha_label row(s) (deleted %d prior)",
                chart_id, ayanamsha_id, written, deleted)
    return written
