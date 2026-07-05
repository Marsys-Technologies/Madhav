"""
mi_bhavisya — Frozen Prediction Bundle (L5 Mīmāṃsā)
=====================================================
Freezes L4 Phala predictions into mimamsa_predictions (immutable bundle) and
captures manifestation sets from L4 outcome channels.

PER-CHART scope: DELETE WHERE chart_id = %s, then re-insert.
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
If L4 tables are absent or empty → 0 rows, WriterResult with note.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import date, datetime

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from pipeline.orchestrator.writers.mi_adhilepa import _signal_family_key

logger = logging.getLogger(__name__)

BUNDLE_FORMULA_VERSION = "mi_bhavisya_v1.0"


def _hash_bundle(chart_id: str, prediction_id: str, emitted_at: str) -> str:
    """Deterministic frozen-bundle hash."""
    raw = f"{chart_id}|{prediction_id}|{emitted_at}|{BUNDLE_FORMULA_VERSION}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = %s AND table_schema = 'public'",
            (table_name,),
        )
        return cur.fetchone() is not None


@register("mi_bhavisya")
class MiBhavisyaWriter(WriterBase):
    """
    Freezes L4 Phala prediction rows into mimamsa_predictions.
    Reads phala_anchors (primary) + bodha_msr_signals (driving signals).
    Builds mimamsa_manifestation_sets from phala outcome channel specs.
    """

    asset_id = "mi_bhavisya"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id: str = ctx.config["chart_id"]

        # Guard: L4 tables may not exist yet
        if not _table_exists(conn, "phala_anchors"):
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes="phala_anchors does not exist — L4 not yet built; 0 rows",
            )

        # Load L4 anchors for this chart
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT * FROM phala_anchors WHERE chart_id = %s ORDER BY anchor_id",
                (chart_id,),
            )
            anchors = cur.fetchall()

        if not anchors:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes="no phala_anchors rows for this chart; 0 predictions frozen",
            )

        # O2: Load MSR signals grouped by domain for domain-matched driving_signals.
        # Fetch all signals once upfront (ordered by salience); group by each entry in
        # domains_affected_array. This avoids one DB query per prediction row.
        # msr_by_domain maps domain → top-5 [{"signal_id": ..., "strength": salience}]
        msr_by_domain: dict[str, list[dict]] = {}
        msr_signals: dict[str, dict] = {}  # retained as fallback keyed by signal_id
        if _table_exists(conn, "bodha_msr_signals"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT signal_id, computed_salience, domains_affected_array, "
                    "signal_type_class, source_subsystem, source_l1_asset "
                    "FROM bodha_msr_signals WHERE chart_id = %s "
                    "ORDER BY computed_salience DESC NULLS LAST",
                    (chart_id,),
                )
                for r in cur.fetchall():
                    sid = str(r["signal_id"])
                    salience = float(r["computed_salience"] or 1.0)
                    msr_signals[sid] = dict(r)
                    # Resolve the pooled evidence-family id (fam_yoga, fam_graha_natal,
                    # etc.) via the same mapping mi_adhilepa already uses, so downstream
                    # hierarchical-shrinkage pooling (mi_gunanaka, mi_pariksha) operates on
                    # real signal families instead of falling through to signal_id (n=1).
                    family_id = _signal_family_key(dict(r))
                    domains_affected = r.get("domains_affected_array") or []
                    for dom in (domains_affected if isinstance(domains_affected, list) else []):
                        bucket = msr_by_domain.setdefault(str(dom), [])
                        if len(bucket) < 5:
                            bucket.append({"signal_id": sid, "strength": salience, "family_id": family_id})

        emitted_at = datetime.utcnow()
        emitted_str = emitted_at.isoformat()

        pred_rows: list[tuple] = []
        mset_rows: list[tuple] = []

        for anchor in anchors:
            anchor_id = str(anchor.get("anchor_id") or "")
            prediction_id = f"pred_{anchor_id}"

            # Derive observation window from anchor timing fields
            window_start = anchor.get("window_start") or anchor.get("start_date")
            window_end = anchor.get("window_end") or anchor.get("end_date")
            eval_date = anchor.get("eval_date") or window_end or date.today()

            if window_start is None or window_end is None:
                # Skip anchors without timing
                continue

            # phala_anchors has no outcome_claim / prediction_text / summary column.
            # Build a non-null outcome_claim from the actual columns:
            #   karmic_note  — human-readable karmic frame note (best narrative, may be None)
            #   event_type   — structured event label (always set by engine)
            #   direction    — suppressed / amplified / neutral
            #   domain       — life domain (career / financial / spiritual / …)
            _karmic_note = anchor.get("karmic_note")
            _event_type  = anchor.get("event_type") or "development"
            _direction   = anchor.get("direction") or ""
            _domain_raw  = anchor.get("domain") or anchor.get("life_domain") or "unknown"
            if _karmic_note:
                outcome_claim = str(_karmic_note)
            else:
                # Compose a readable label: e.g. "suppressed career activation"
                parts = [p for p in [_direction, _domain_raw, _event_type] if p]
                outcome_claim = " ".join(parts) if parts else "unspecified"
            domain = str(anchor.get("domain") or anchor.get("life_domain") or "unknown")
            magnitude_expected = str(anchor.get("magnitude") or "moderate")

            # Confidence band: use anchor's confidence or default [0.4, 0.7)
            conf_low = float(anchor.get("confidence_low") or 0.4)
            conf_high = float(anchor.get("confidence_high") or 0.7)

            # O2: domain-matched driving signals. Use signals tagged to this prediction's
            # domain (from msr_by_domain cache). Fall back to top-5 generic if no domain
            # match exists (e.g. domain="unknown" or no signals tagged for that domain).
            driving = msr_by_domain.get(domain) or [
                {"signal_id": sid, "strength": 1.0, "family_id": _signal_family_key(msr_signals[sid])}
                for sid in list(msr_signals.keys())[:5]
            ]

            falsifier = anchor.get("falsifier_spec") or anchor.get("falsifier") or {}
            if isinstance(falsifier, str):
                try:
                    falsifier = json.loads(falsifier)
                except Exception:
                    falsifier = {"raw": falsifier}

            bundle_hash = _hash_bundle(chart_id, prediction_id, emitted_str)

            pred_rows.append((
                chart_id,
                prediction_id,
                anchor_id,          # source_pramana_id
                outcome_claim,
                domain,
                f"[{window_start},{window_end})",   # daterange as string
                eval_date,
                f"[{conf_low},{conf_high})",         # numrange as string
                magnitude_expected,
                json.dumps(falsifier),
                None,               # base_rate — computed by mi_pramana
                emitted_at,
                "pending",
                json.dumps(driving),
                bundle_hash,
                BUNDLE_FORMULA_VERSION,
            ))

            # Manifestation sets: default literal channel per domain
            channel_id = f"ch_{domain}_verbal"
            mset_rows.append((
                chart_id,
                prediction_id,
                channel_id,
                domain,
                "phala_anchors",
                json.dumps({"anchor_id": anchor_id}),
                True,
                emitted_at,
            ))

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(pred_rows) + len(mset_rows),
                duration_seconds=time.time() - t0,
                notes=f"dry_run: would freeze {len(pred_rows)} predictions, {len(mset_rows)} manifestation_sets",
            )

        # Idempotency: delete per chart
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (chart_id,))
            cur.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (chart_id,))

        if not pred_rows:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes="no valid anchors with timing; 0 predictions",
            )

        PRED_SQL = """
            INSERT INTO mimamsa_predictions (
                chart_id, prediction_id, source_pramana_id, outcome_claim,
                domain, observation_window, eval_date, confidence_band,
                magnitude_expected, falsifier_jsonb, base_rate, emitted_at,
                lifecycle_status, driving_signals, frozen_bundle_hash, bundle_formula_version
            ) VALUES (
                %s,%s,%s,%s,%s,
                %s::daterange, %s,
                %s::numrange,
                %s,%s,%s,%s,%s,%s,%s,%s
            )
        """
        MSET_SQL = """
            INSERT INTO mimamsa_manifestation_sets (
                chart_id, prediction_id, channel_id, domain, source, citation_ref, is_literal, frozen_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        with conn.cursor() as cur:
            cur.executemany(PRED_SQL, pred_rows)
            cur.executemany(MSET_SQL, mset_rows)

        logger.info(
            "[mi_bhavisya] frozen %d predictions, %d manifestation_sets for chart %s",
            len(pred_rows), len(mset_rows), chart_id,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(pred_rows) + len(mset_rows),
            duration_seconds=time.time() - t0,
        )
