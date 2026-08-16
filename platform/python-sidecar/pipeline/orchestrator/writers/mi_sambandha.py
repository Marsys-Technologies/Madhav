"""
mi_sambandha — Manifestation-Grammar Builder (L5 Mīmāṃsā)
==========================================================
Learns per-native channel propensity from the outcomes recorded in
mimamsa_manifestation_sets + mimamsa_calibration. Seeds prior propensities
from signal-family binding specs when no empirical data exists.

Table: mimamsa_manifestation_grammar
PER-CHART scope: DELETE WHERE chart_id = %s, then re-insert.
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

GRAMMAR_FORMULA_VERSION = "mi_sambandha_v1.0"

# Prior channel propensities by domain (when no empirical data)
_PRIOR_PROPENSITIES: dict[str, dict[str, float]] = {
    "career":       {"ch_career_verbal": 0.40, "ch_career_material": 0.35, "ch_career_relational": 0.25},
    "health":       {"ch_health_bodily": 0.50, "ch_health_mental": 0.30, "ch_health_social": 0.20},
    "relationship": {"ch_rel_partnership": 0.45, "ch_rel_family": 0.35, "ch_rel_social": 0.20},
    "wealth":       {"ch_fin_income": 0.40, "ch_fin_asset": 0.35, "ch_fin_loss": 0.25},
    "travel":       {"ch_travel_short": 0.50, "ch_travel_long": 0.50},
    "education":    {"ch_edu_formal": 0.60, "ch_edu_informal": 0.40},
    "spirituality": {"ch_spirit_practice": 0.55, "ch_spirit_insight": 0.45},
    "default":      {"ch_default_literal": 0.50, "ch_default_symbolic": 0.50},
}


@register("mi_sambandha")
class MiSambandhaWriter(WriterBase):
    """
    Builds per-native manifestation-channel propensity grammar.
    Reads manifestation_sets + calibration; learns fire_count / opportunity_count.
    Falls back to priors for domains with insufficient data.
    """

    asset_id = "mi_sambandha"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id: str = ctx.config["chart_id"]

        # Load manifestation sets (which channels were assigned to predictions)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT ms.prediction_id, ms.channel_id, ms.domain, ms.is_literal, "
                "       c.composite_verdict, c.manifestation_channel "
                "FROM mimamsa_manifestation_sets ms "
                "LEFT JOIN mimamsa_calibration c "
                "   ON c.chart_id = ms.chart_id AND c.prediction_id = ms.prediction_id "
                "WHERE ms.chart_id = %s",
                (chart_id,),
            )
            mset_rows = cur.fetchall()

        # Aggregate fire_count / opportunity_count per (origin_kind, origin_ref, channel, domain)
        # origin_kind = 'prediction_set', origin_ref = domain for now
        counts: dict[tuple, dict] = {}

        for row in mset_rows:
            channel_id = row["channel_id"]
            domain = row["domain"]
            key = ("prediction_set", domain, channel_id, domain)

            if key not in counts:
                counts[key] = {"fire": 0, "opp": 0, "scored": 0}

            counts[key]["opp"] += 1
            verdict = row.get("composite_verdict") or ""
            ch_fired = row.get("manifestation_channel") or ""
            if verdict in ("confirmed", "partial", "denied"):
                counts[key]["scored"] += 1
            if verdict in ("confirmed", "partial") and ch_fired == channel_id:
                counts[key]["fire"] += 1

        # Build grammar rows
        rows: list[tuple] = []

        for (origin_kind, origin_ref, channel_id, domain), cnts in counts.items():
            opp = cnts["opp"]
            fire = cnts["fire"]
            scored = cnts["scored"]
            propensity = fire / opp if opp > 0 else None
            prior = _PRIOR_PROPENSITIES.get(domain, _PRIOR_PROPENSITIES["default"]).get(channel_id, 0.5)
            delta = round(propensity - prior, 4) if propensity is not None else None
            n = opp
            grade = (
                "empirical" if scored >= 5
                else "assignment_only" if opp >= 5
                else "prior_only"
            )
            conf_lo = max(0.0, (propensity or prior) - 0.1)
            conf_hi = min(1.0, (propensity or prior) + 0.1)

            rows.append((
                chart_id,
                origin_kind,
                origin_ref,
                channel_id,
                domain,
                fire,
                opp,
                scored,
                round(propensity, 4) if propensity is not None else None,
                round(prior, 4),
                delta,
                n,
                f"[{round(conf_lo,2)},{round(conf_hi,2)})" if n >= 5 else None,
                grade,
                json.dumps({"method": "fire_over_opportunity"}),
                GRAMMAR_FORMULA_VERSION,
            ))

        # Seed domains with no empirical data from priors
        covered_domains = {r[3] for r in rows}  # channel_id position is 3 in row... actually domain pos
        # Actually let's seed all prior domains that have no row yet
        empirical_keys = {(r[1], r[2], r[3], r[4]) for r in rows}  # origin_kind,ref,channel,domain

        for domain, channel_priors in _PRIOR_PROPENSITIES.items():
            if domain == "default":
                continue
            for channel_id, prior in channel_priors.items():
                key = ("prediction_set", domain, channel_id, domain)
                if key in empirical_keys:
                    continue
                conf_lo = max(0.0, prior - 0.10)
                conf_hi = min(1.0, prior + 0.10)
                rows.append((
                    chart_id,
                    "prediction_set",
                    domain,
                    channel_id,
                    domain,
                    0,
                    0,
                    0,
                    None,
                    round(prior, 4),
                    None,
                    0,
                    None,
                    "prior_only",
                    json.dumps({"method": "prior_from_kula"}),
                    GRAMMAR_FORMULA_VERSION,
                ))

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                                duration_seconds=time.time() - t0,
                                notes=f"dry_run: would insert {len(rows)} grammar rows")

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_manifestation_grammar WHERE chart_id = %s", (chart_id,)
            )

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no data — 0 grammar rows")

        SQL = """
            INSERT INTO mimamsa_manifestation_grammar (
                chart_id, origin_kind, origin_ref, channel_id, domain,
                fire_count, opportunity_count, scored_count, channel_propensity, prior_propensity,
                propensity_delta, n_support, confidence_band, evidence_grade,
                citation_ref, grammar_formula_version
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::numrange,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(SQL, rows)

        logger.info("[mi_sambandha] %d grammar rows for chart %s", len(rows), chart_id)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(rows),
            duration_seconds=time.time() - t0,
        )
