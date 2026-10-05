"""
mi_bhavisya — Frozen Prediction Bundle (L5 Mīmāṃsā)
=====================================================
Freezes L4 Phala predictions into mimamsa_predictions (immutable bundle) and
captures manifestation sets from L4 outcome channels.

APPEND-ONLY (SS N-104, an application of N-46) -- DOCUMENTED EXCEPTION TO §N.3
-------------------------------------------------------------------------------
CLAUDE.md §N.3 says L1+ writers are per-chart delete-then-insert. That standard
does NOT apply to this writer. ``mimamsa_predictions`` and
``mimamsa_manifestation_sets`` are calibration HISTORY, not rebuildable state:
a prediction is a claim issued at a point in time, and the whole point of the
table is to be compared with what later happened. Deleting it, or re-stamping
its ``emitted_at`` / ``frozen_bundle_hash``, turns a frozen claim into a
hindsight artefact. So this writer:

* never DELETEs a row of either table (pending, due, stale or otherwise);
* never UPDATEs a row of either table (so ``emitted_at``,
  ``frozen_bundle_hash``, ``source_pramana_id``, ... of an existing row keep
  their bytes);
* INSERTs a prediction only when none exists yet for the anchor, and a
  manifestation set only for a prediction inserted in the same run.

Natural key. The only unique constraint is the primary key
``(chart_id, prediction_id)`` and ``prediction_id = 'pred_' || anchor_id``, but
the anchor id a prediction was frozen under is NOT stable across the table's
life: migration 680 re-pointed ``source_pramana_id`` to the deterministic
anchor id while ``prediction_id`` kept the original id. A PK-only check would
therefore re-insert a second copy of every already-frozen claim. The writer
treats an anchor as ALREADY FROZEN when, for the same chart, either
``prediction_id = 'pred_<anchor_id>'`` (the freeze-time key) or
``source_pramana_id = '<anchor_id>'`` (the current anchor reference) exists.
The insert itself is ``ON CONFLICT (chart_id, prediction_id) DO NOTHING`` as a
belt over that check. A prediction whose anchor has since vanished or moved is
left alone here; recording that reference gap is the job of a separate
computed side ledger, never of a rewrite of the frozen row.

Consequences a reader should not be surprised by: ``rows_inserted`` is the
number of rows ADDED this run (0 on a no-op rebuild; the asset's ``count_sql``
and integrity SQL read the table, not this figure); an existing prediction that
carries ``chart_context_stale_at`` still blocks a fresh insert for the same
anchor (reported in the result notes, never "fixed" by rewriting it).

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

    APPEND-ONLY (SS N-104): inserts only the predictions (and their manifestation
    sets) that are absent; never DELETEs or UPDATEs an existing row. See the module
    docstring for the natural key and the documented exception to CLAUDE.md §N.3.
    """

    asset_id = "mi_bhavisya"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id: str = ctx.config["chart_id"]

        # A6 (L5-W3, adjudication #1738).  "L4 not yet built" is no longer a
        # reachable state: L4 Phala is CLOSED and ph_pramana / ph_nimitta /
        # ph_phaladesa are DECLARED dependencies of this asset.  A missing table
        # is a deployment defect.  Critically, the per-chart-empty case -- a
        # chart that genuinely has no anchors -- is already handled separately
        # below, so this branch had no legitimate purpose beyond masking a schema
        # failure, and the two outcomes were indistinguishable downstream.
        if not _table_exists(conn, "phala_anchors"):
            raise RuntimeError(
                "mi_bhavisya: phala_anchors table not found — L4 Phala is not "
                "deployed. ph_pramana/ph_nimitta/ph_phaladesa are DECLARED "
                "dependencies, so a missing table is a deployment defect. Zero "
                "frozen predictions here would be indistinguishable from a chart "
                "that genuinely has no anchors (handled separately below)."
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

        # ------------------------------------------------------------------
        # Append-only (SS N-104): read what is already frozen for this chart and
        # emit only the anchors that have no prediction yet.  Nothing below ever
        # DELETEs or UPDATEs an existing row of either table.
        # ------------------------------------------------------------------
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT prediction_id, source_pramana_id, "
                "(chart_context_stale_at IS NOT NULL) AS is_stale "
                "FROM mimamsa_predictions WHERE chart_id = %s",
                (chart_id,),
            )
            existing = cur.fetchall()
        frozen_prediction_ids = {str(r["prediction_id"]) for r in existing}
        frozen_anchor_refs = {str(r["source_pramana_id"]) for r in existing}
        stale_prediction_ids = {str(r["prediction_id"]) for r in existing if r["is_stale"]}
        stale_anchor_refs = {str(r["source_pramana_id"]) for r in existing if r["is_stale"]}

        new_pred_rows: list[tuple] = []
        skipped_existing = 0
        skipped_existing_stale = 0
        for row in pred_rows:
            prediction_id, anchor_id = row[1], row[2]
            if prediction_id in frozen_prediction_ids or anchor_id in frozen_anchor_refs:
                skipped_existing += 1
                if prediction_id in stale_prediction_ids or anchor_id in stale_anchor_refs:
                    skipped_existing_stale += 1
                continue
            new_pred_rows.append(row)
        new_pred_ids = {r[1] for r in new_pred_rows}
        new_mset_rows = [m for m in mset_rows if m[1] in new_pred_ids]

        existing_note = (
            f"{skipped_existing} anchor(s) already frozen left untouched "
            f"({skipped_existing_stale} of them stale-marked); "
            f"{len(existing)} existing prediction row(s) for chart never deleted or rewritten"
        )

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(new_pred_rows) + len(new_mset_rows),
                duration_seconds=time.time() - t0,
                notes=(
                    f"dry_run: would freeze {len(new_pred_rows)} new predictions, "
                    f"{len(new_mset_rows)} manifestation_sets; {existing_note}"
                ),
            )

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
            ON CONFLICT (chart_id, prediction_id) DO NOTHING
        """
        MSET_SQL = """
            INSERT INTO mimamsa_manifestation_sets (
                chart_id, prediction_id, channel_id, domain, source, citation_ref, is_literal, frozen_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (chart_id, prediction_id, channel_id) DO NOTHING
        """

        # One statement per row so the count of rows actually added is exact
        # (a DO NOTHING conflict reports rowcount 0).  A set is added only for a
        # prediction that was really inserted by this statement.
        preds_inserted = 0
        msets_inserted = 0
        mset_by_pred = {m[1]: m for m in new_mset_rows}
        with conn.cursor() as cur:
            for row in new_pred_rows:
                cur.execute(PRED_SQL, row)
                if cur.rowcount == 1:
                    preds_inserted += 1
                    mset = mset_by_pred.get(row[1])
                    if mset is not None:
                        cur.execute(MSET_SQL, mset)
                        if cur.rowcount == 1:
                            msets_inserted += 1

        logger.info(
            "[mi_bhavisya] froze %d new predictions, %d manifestation_sets for chart %s; %s",
            preds_inserted, msets_inserted, chart_id, existing_note,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=preds_inserted + msets_inserted,
            rows_skipped=skipped_existing,
            duration_seconds=time.time() - t0,
            notes=(
                f"append-only (SS N-104): {preds_inserted} predictions + "
                f"{msets_inserted} manifestation_sets added; {existing_note}"
            ),
        )
