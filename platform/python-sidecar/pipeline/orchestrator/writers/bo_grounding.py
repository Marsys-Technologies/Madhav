"""
bo_grounding — D-GROUNDING tier-assignment writer (L2 Bodha)
================================================================
Adjudication #2258 (2026-09-07), structural rulings (a) target_kind v1 scope,
(b) new dedicated writer, (c) DAG dependency scope, all ruled by the
Conductor; tier-assignment semantics ruled by native (D-NATIVE-09). Populates
`bodha_grounding_matches` (migration 897) by running
`bodha_writers.grounding_matcher`'s real detector against the two v1 target
classes:
  - yoga_dosha_firing, sourced from `ga_yoga_firings` (fired=true)
  - msr_signal, sourced from `bodha_msr_signals`

PURE L2 DERIVATION — reads existing L1 (`ga_yoga_firings`) and L2
(`bodha_msr_signals`) rows plus the classical rule corpus (`sutravali_rules`);
computes no new astronomical facts and edits no upstream writer's own output.

DAG dependency: `ga_yoga` (source of `ga_yoga_firings`) + `bo_laksana`
(source of `bodha_msr_signals`) only — ruled (c), deliberately narrower than
`bo_laksana_rerank`'s 24-ancestor gate (same "narrowest sufficient ancestor
set" precedent `bo_sudarshana` established under #1770).

See `grounding_matcher.py`'s own module docstring for the two live
data-integrity findings (sutravali_rules mistagging; ga_yoga_firings
constituent_fact_ids staleness) that shaped the detector design this writer
calls unmodified — this file is orchestration/IO only, no classification
logic of its own.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register
from bodha_writers.grounding_matcher import classify_yoga_dosha_firing, classify_msr_signal

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_grounding_v1.0"

CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "raman",
    "krishnamurti",
    "surya_siddhanta_classical",
    "true_chitra",
]


def _fetch_sutravali_rules(conn: Any) -> list[dict[str, Any]]:
    """Not ayanamsha-scoped -- the classical rule corpus is fetched once per
    run() call, not once per ayanamsha (it doesn't vary by ayanamsha)."""
    rows = conn.execute(
        """SELECT rule_id, text_id, verse_ref, antecedent_jsonb, predicate_jsonb, yoga_canonical_id
           FROM sutravali_rules"""
    ).fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _fetch_fired_yogas(conn: Any, chart_id: str, aya: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT id, yoga_canonical_id, constituent_planets, constituent_houses
           FROM ga_yoga_firings
           WHERE chart_id = %s AND ayanamsha_id = %s AND fired = true""",
        [chart_id, aya],
    ).fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _fetch_msr_signals(conn: Any, chart_id: str, aya: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT signal_id, classical_sources_jsonb
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _match_to_row(match, chart_id: str, ayanamsha_id: str, build_id: str, now: str) -> dict[str, Any]:
    return {
        "match_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "target_kind": match.target_kind,
        "target_id": match.target_id,
        "grounding_tier": match.grounding_tier,
        "citation_granularity": match.citation_granularity,
        "grounding_evidence_jsonb": json.dumps(match.grounding_evidence_jsonb) if match.grounding_evidence_jsonb is not None else None,
        "derivation_chain": match.derivation_chain,
        "matched_rule_id": match.matched_rule_id,
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }


@register("bo_grounding")
class BoGroundingWriter(WriterBase):
    """bo_grounding: D-GROUNDING tier-assignment matches for the v1 target scope."""
    asset_id = "bo_grounding"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_grounding_matches

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn = ctx.db_conn
        now = datetime.now(timezone.utc).isoformat()
        total = 0

        rules = _fetch_sutravali_rules(conn)
        if ctx.dry_run:
            logger.info("[bo_grounding dry_run] %d sutravali_rules loaded", len(rules))

        for aya in CANONICAL_AYANAMSHAS:
            firings = _fetch_fired_yogas(conn, chart_id, aya)
            signals = _fetch_msr_signals(conn, chart_id, aya)

            if ctx.dry_run:
                logger.info(
                    "[bo_grounding dry_run] %s — %d fired yogas, %d msr_signals",
                    aya, len(firings), len(signals),
                )
                continue

            rows: list[dict] = []
            for f in firings:
                match = classify_yoga_dosha_firing(
                    firing_id=f["id"],
                    constituent_planets=f.get("constituent_planets") or [],
                    constituent_houses=f.get("constituent_houses") or [],
                    candidate_rules=rules,
                )
                rows.append(_match_to_row(match, chart_id, aya, build_id, now))

            for s in signals:
                match = classify_msr_signal(
                    signal_id=s["signal_id"],
                    classical_sources_jsonb=s.get("classical_sources_jsonb"),
                )
                rows.append(_match_to_row(match, chart_id, aya, build_id, now))

            if not rows:
                continue

            deleted = replace_prior_grounding_matches(conn, chart_id, aya)
            logger.info(
                "[bo_grounding] %s — deleted %d prior, inserting %d matches",
                aya, deleted, len(rows),
            )

            for row in rows:
                conn.execute(_INSERT_SQL, row)
            total += len(rows)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total)


_INSERT_SQL = """
INSERT INTO bodha_grounding_matches (
  match_id, chart_id, ayanamsha_id, build_id,
  target_kind, target_id,
  grounding_tier, citation_granularity, grounding_evidence_jsonb,
  derivation_chain, matched_rule_id,
  computed_at, engine_version
) VALUES (
  %(match_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(target_kind)s, %(target_id)s,
  %(grounding_tier)s, %(citation_granularity)s, %(grounding_evidence_jsonb)s::jsonb,
  %(derivation_chain)s, %(matched_rule_id)s,
  %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, target_kind, target_id, build_id)
DO NOTHING
"""
