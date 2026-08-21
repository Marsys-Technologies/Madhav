"""
mi_darshana — Insight Retrieval Surface (L5 Mīmāṃsā)
=====================================================
HEAVY writer: three substeps per chart:
  1. "insight_units"  — synthesize calibrated + discovery + grammar data into
                         retrievable insight_unit rows with full provenance
  2. "embeddings"     — mark rows for embedding (actual vectors require external
                         embedding model call — [EXTERNAL_COMPUTATION_REQUIRED])
  3. "views_verify"   — count-check against views and log gaps

Tables written: mimamsa_insight_units (+ embedding stubs if model available)
PER-CHART scope.

B.10 note: embedding vectors require an external embedding model. The writer
inserts insight_units in full; mimamsa_insight_embeddings rows are NOT inserted
here — that requires an external embedding service call tagged
[EXTERNAL_COMPUTATION_REQUIRED].

FROZEN orchestrator contract: @register, plan_substeps + run_substep.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

# v1.2: F-147 addendum — unmeasured channel_propensity narrated as unmeasured,
#       not as the prior dressed up as an empirically-learned rate.
# v1.1: F-143 per-discovery_class evidence grading
SURFACE_FORMULA_VERSION = "mi_darshana_v1.2"
LEL_VERSION = "v1.7"

_INSIGHT_TYPES = {
    "calibrated_outlook": "Calibrated confidence from prediction-event matching",
    "manifestation_grammar": "Learned channel propensity for this native",
    "emergent_law": "Pattern candidate from discovery mining",
    "load_bearing": "Load-bearing conclusion from signal sensitivity map",
    "negative_knowledge": "What definitively does NOT hold for this native",
    "verdict_object": "Per-event-class promise verdict with ranked evidence, contradictions, and tradition concordance",
    "retrodiction": "Historical-anchor probe against a known past event (mi_pariksha retrodiction substep)",
}

# ── F-143: discovery evidence grading ────────────────────────────────────────
# `mimamsa_discoveries.n_support` does NOT mean the same thing across discovery
# classes, so one shared `n >= 5` threshold cannot grade both honestly:
#
#   emergent_law  (mi_pariksha._substep_discovery) — n_support = the number of
#       mimamsa_attribution rows for a (signal_id, dimension) pair. Those are
#       ASSIGNMENTS of analytic credit, one per prediction↔event match the signal
#       appears in — including matches whose verdict is UNRESOLVED (observation
#       window not yet elapsed, adjudication can still flip) or FALSE_ALARM
#       (control window). Counting them as scored outcomes is exactly the F-35
#       defect: 'empirical' claimed from assignment volume. The only count that
#       can earn 'empirical' is `evidence_refs.n_scored_matches` — distinct
#       matches with an adjudicated verdict — which mi_pariksha now records.
#
#   retrodiction  (mi_pariksha._substep_retrodiction) — n_support = matched
#       historical anchors, hard-capped at 3 by the query's LIMIT 3, so `n >= 5`
#       is structurally unreachable and every row grades 'prior_only' forever.
#       The threshold is not merely too strict, it is the wrong axis. But the fix
#       is NOT to lower the bar: a "match" here is only "an anchor in the same
#       domain had opened before the event date". The declared T−90d blinding is
#       never applied as a filter, the anchor window is not checked to contain the
#       event, and the anchor's event type is never compared to what happened. No
#       detector adjudicates the hit (§N.8), so nothing in the current pipeline
#       earns 'empirical' for this class — it is a deterministic structural probe
#       and is graded 'structural', the tier this schema already uses for
#       deterministically-derived, non-outcome-scored rows. What WOULD earn
#       'empirical' here: a real cutoff-filtered recomputation plus an adjudicated
#       hit criterion (window containment + event-class agreement) over ≥5 events.
#
# Threshold mirrors F-35 / migration 573 ("empirical requires scored_count >= 5").
_EMPIRICAL_SCORED_MIN = 5

_GRADE_EMPIRICAL = "empirical"
_GRADE_ASSIGNMENT_ONLY = "assignment_only"
_GRADE_PRIOR_ONLY = "prior_only"
_GRADE_STRUCTURAL = "structural"


def _discovery_evidence_grade(
    discovery_class: str, n_support: int, evidence_refs
) -> tuple[str, dict]:
    """Grade one mimamsa_discoveries row, per discovery_class (F-143).

    Returns (evidence_grade, grade_basis) — the basis dict is stored in the
    insight unit's provenance_chain so the reason is auditable at serve time and
    never has to be re-derived from the grade label alone.
    """
    refs = evidence_refs if isinstance(evidence_refs, dict) else {}

    if discovery_class == "retrodiction":
        return _GRADE_STRUCTURAL, {
            "rule": "retrodiction_never_empirical",
            "n_support_means": "matched historical anchors (query LIMIT 3)",
            "reason": (
                "anchor match is not an adjudicated hit and the declared T−90d "
                "blinding is not enforced — no detector scores this probe, so no "
                "count of it can earn an empirical grade"
            ),
            "anchors_matched": n_support,
        }

    raw_scored = refs.get("n_scored_matches")
    n_scored = (
        int(raw_scored)
        if isinstance(raw_scored, int) and not isinstance(raw_scored, bool)
        else None
    )

    if n_scored is None:
        # Either a pre-F-143 row (written before mi_pariksha recorded the scored
        # count) or a discovery class that carries no scored count at all. An
        # honest lower tier, never a promotion on an unknown (§N.7 item 6).
        grade = (
            _GRADE_ASSIGNMENT_ONLY
            if discovery_class == "emergent_law" and n_support >= _EMPIRICAL_SCORED_MIN
            else _GRADE_PRIOR_ONLY
        )
        return grade, {
            "rule": "no_scored_count_available",
            "n_support": n_support,
            "n_scored_matches": None,
            "reason": (
                "evidence_refs carries no n_scored_matches — cannot distinguish "
                "adjudicated outcomes from attribution assignments; graded down, "
                "never up (rebuild mi_pariksha to populate it)"
            ),
        }

    if n_scored >= _EMPIRICAL_SCORED_MIN:
        grade = _GRADE_EMPIRICAL
    elif n_support >= _EMPIRICAL_SCORED_MIN:
        grade = _GRADE_ASSIGNMENT_ONLY
    else:
        grade = _GRADE_PRIOR_ONLY
    return grade, {
        "rule": "scored_matches_threshold",
        "n_support": n_support,
        "n_scored_matches": n_scored,
        "empirical_min": _EMPIRICAL_SCORED_MIN,
    }


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


@register("mi_darshana")
class MiDarshanaWriter(WriterBase):
    """
    Synthesizes L5 data into retrievable insight units.
    HEAVY: insight_units → embeddings → views_verify (3 substeps).
    """

    asset_id = "mi_darshana"
    has_substeps = True

    def plan_substeps(self, ctx) -> list[SubStep]:
        self._chart_id = ctx.config["chart_id"]
        return [
            SubStep(key="insight_units", label="synthesize insight units"),
            SubStep(key="embeddings", label="mark embedding stubs"),
            SubStep(key="views_verify", label="verify views"),
        ]

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id = self._chart_id

        if step.key == "insight_units":
            return self._substep_insight_units(conn, chart_id, t0)
        if step.key == "embeddings":
            return self._substep_embeddings(conn, chart_id, t0)
        if step.key == "views_verify":
            return self._substep_views_verify(conn, chart_id, t0)
        raise ValueError(f"unknown substep: {step.key}")

    # ── insight_units ────────────────────────────────────────────────────────

    def _substep_insight_units(self, conn, chart_id: str, t0: float) -> WriterResult:
        rows: list[tuple] = []
        now = datetime.utcnow()

        # ── 1. Calibrated-outlook insights from reliability strata ────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT stratum_key, predicted_prob_bin, observed_rate, n, "
                "       brier_score, evidence_grade, held_out_validity "
                "FROM mimamsa_reliability WHERE chart_id = %s",
                (chart_id,),
            )
            rel_rows = cur.fetchall()

        for i, r in enumerate(rel_rows):
            n = r.get("n") or 0
            if n < 2:
                continue
            # observed_rate + brier_score are DB numeric columns → Decimal in
            # Python. Coerce to float at point of use so downstream float
            # arithmetic (conf_lo/conf_hi) and json.dumps() never see a Decimal.
            # (Native charts carry real calibrated values; Abhinandan's were NULL,
            # which fell through to the 0.5 float default and masked this.)
            observed_raw = r.get("observed_rate")
            observed = float(observed_raw) if observed_raw is not None else None
            brier_raw = r.get("brier_score")
            brier = float(brier_raw) if brier_raw is not None else None
            grade = r.get("evidence_grade", "prior_only")
            statement = (
                f"In predictions scored {r['predicted_prob_bin']}, "
                f"the observed outcome rate is {observed:.1%} across {n} events "
                f"(evidence: {grade})."
            ) if observed is not None else (
                f"Stratum {r['stratum_key']}: {n} predictions, insufficient events to compute rate."
            )
            insight_id = f"cal_{r['stratum_key'].replace('|','_')[:50]}_{i}"
            obs = observed if observed is not None else 0.5
            conf_lo = max(0.0, obs - 0.1)
            conf_hi = min(1.0, obs + 0.1)
            rows.append((
                chart_id, insight_id, "calibrated_outlook",
                None, None, None,   # domain, horizon, question_lens
                statement,
                float(obs),
                f"[{round(conf_lo,2)},{round(conf_hi,2)})",
                n,
                "not_assessed",
                grade,
                LEL_VERSION,
                None,   # last_calibrated_at
                json.dumps({"stratum": r["stratum_key"], "brier": brier}),
                False,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 2. Manifestation-grammar insights ────────────────────────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT channel_id, domain, channel_propensity, prior_propensity, "
                "       n_support, scored_count, evidence_grade "
                "FROM mimamsa_manifestation_grammar WHERE chart_id = %s "
                "AND evidence_grade IN ('empirical', 'assignment_only') ORDER BY n_support DESC LIMIT 20",
                (chart_id,),
            )
            gram_rows = cur.fetchall()

        for i, r in enumerate(gram_rows):
            ch = r["channel_id"]
            dom = r.get("domain", "unknown")
            # P2 mislabel/drift fix (same file as P0-10, same truthiness pattern):
            # channel_propensity (migration 352) is nullable and a genuinely
            # computed 0.0 means "this channel never fires" — a real value, not
            # an absence marker. Only fall back to prior_propensity (NOT NULL)
            # when channel_propensity is actually missing (None).
            _channel_prop_raw = r.get("channel_propensity")
            propensity_measured = _channel_prop_raw is not None
            if propensity_measured:
                prop = float(_channel_prop_raw)
            else:
                _prior_prop_raw = r.get("prior_propensity")
                prop = float(_prior_prop_raw) if _prior_prop_raw is not None else 0.5
            n = r.get("n_support") or 0
            grade = r.get("evidence_grade", "prior_only")
            scored = r.get("scored_count") or 0
            if grade == "empirical" and not propensity_measured:
                # F-147 addendum (§N.7 item 6): a row can earn 'empirical' on
                # scored_count while channel_propensity stays NULL, because
                # mi_pramana._score_manifestation() is still a stub and never
                # records WHICH channel an outcome manifested through
                # (mi_sambandha emits citation_ref.propensity_null_reason =
                # 'no_manifestation_channel_recorded' for exactly this case).
                # Narrating `prop` here would print the PRIOR as though it were
                # the empirically-learned rate — a worse invention than the 0.0
                # this addendum removed. Say the gap instead.
                statement = (
                    f"For {dom} events, {scored} predictions on the '{ch}' channel have been "
                    f"outcome-scored, but none recorded which channel the outcome actually "
                    f"manifested through — so this channel's firing propensity is UNMEASURED, "
                    f"not zero. Prior-based estimate only: {prop:.0%}."
                )
            elif grade == "empirical":
                statement = (
                    f"For {dom} events, the '{ch}' channel fires with {prop:.0%} propensity "
                    f"(n={scored} outcome-scored predictions, empirical learning)."
                )
            else:  # assignment_only — honest, not a promoted 'empirical' claim (§N.7 item 6)
                statement = (
                    f"For {dom} events, the '{ch}' channel has been assigned to {n} predictions "
                    f"with no outcomes scored yet — insufficient evidence for an empirical grade "
                    f"(prior-based estimate: {prop:.0%})."
                )
            insight_id = f"gram_{dom}_{ch[:20]}_{i}"
            rows.append((
                chart_id, insight_id, "manifestation_grammar",
                dom, None, None,
                statement,
                prop,
                None,   # confidence_band
                n,
                "not_assessed",
                grade,
                LEL_VERSION,
                now,
                # rank_consequence (NOT NULL, top-level column) still carries the
                # prior when the measured value is absent; provenance records
                # which it is so a consumer can never read a prior as a
                # measurement. F-147 GA-5 finding: this dict used to also embed
                # a "rank_consequence" key duplicating that same value — the
                # third instance of the P3-b duplicate-key leak (see
                # query_insights.ts's suppressIfNotCalibrated comment). Removed:
                # propensity_source already carries the disclosure, and the
                # top-level column is the one callers/suppressors read.
                json.dumps({
                    "channel": ch,
                    "domain": dom,
                    "propensity": prop if propensity_measured else None,
                    "propensity_source": "measured" if propensity_measured else "prior_fallback",
                }),
                False,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 3. Emergent-law insights from discoveries ─────────────────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT discovery_id, discovery_class, statement, strength, n_support, "
                "       confidence_band, activation_status, evidence_refs "
                "FROM mimamsa_discoveries WHERE chart_id = %s ORDER BY strength DESC NULLS LAST",
                (chart_id,),
            )
            disc_rows = cur.fetchall()

        for r in disc_rows:
            insight_id = f"disc_{r['discovery_id'][:50]}"
            strength = float(r.get("strength") or 0.5)
            n = r.get("n_support") or 0
            discovery_class = r.get("discovery_class") or "emergent_law"
            is_neg = False
            # F-143: `"empirical" if n >= 5 else "prior_only"` read n_support as a
            # count of scored outcomes for every discovery class alike. It is not —
            # see _discovery_evidence_grade for what each class's n_support means and
            # why one shared threshold cannot grade both honestly.
            grade, grade_basis = _discovery_evidence_grade(
                discovery_class, n, r.get("evidence_refs")
            )
            rows.append((
                chart_id, insight_id, discovery_class,
                None, None, None,
                r["statement"],
                strength,
                r.get("confidence_band"),
                n,
                "not_assessed",
                grade,
                LEL_VERSION,
                now,
                json.dumps({
                    "discovery_id": r["discovery_id"],
                    "status": r.get("activation_status"),
                    "discovery_class": discovery_class,
                    "grade_basis": grade_basis,
                }),
                is_neg,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 4. Load-bearing signal insights ──────────────────────────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT conclusion_id, signal_id, sensitivity, role "
                "FROM mimamsa_load_bearing WHERE chart_id = %s ORDER BY sensitivity DESC",
                (chart_id,),
            )
            lb_rows = cur.fetchall()

        for r in lb_rows:
            insight_id = f"lb_{r['conclusion_id'][:50]}"
            sens = float(r["sensitivity"])
            statement = (
                f"Signal '{r['signal_id']}' is {r['role']} for conclusion '{r['conclusion_id']}' "
                f"(sensitivity={sens:.2f}). Removing this signal would materially alter the reading."
            )
            rows.append((
                chart_id, insight_id, "load_bearing",
                None, None, None,
                statement,
                sens,
                None,
                1,
                "not_assessed",
                "structural",
                LEL_VERSION,
                None,
                json.dumps({"signal_id": r["signal_id"], "role": r["role"]}),
                False,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 5. Verdict-object rows from P3B bodha data ───────────────────────────
        # Assembles one mimamsa_insight_unit per event_class (per BA-P4 spec):
        # status + grade from bodha_pratijna, ranked evidence from bodha_msr_signals,
        # contradictions from bodha_contradictions, tradition concordance from bodha_triangulation.
        if _table_exists(conn, "bodha_pratijna") and _table_exists(conn, "bodha_triangulation"):
            CANONICAL_AYA = "lahiri_chitrapaksha"

            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute("""
                    SELECT bp.event_class_id, bp.status, bp.grade,
                           bp.supporting_signal_ids, bp.contradicting_signal_ids,
                           bp.derivation, beo.name_en, beo.domain
                    FROM bodha_pratijna bp
                    JOIN brahma_event_ontology beo USING (event_class_id)
                    WHERE bp.chart_id = %s AND bp.ayanamsha_id = %s
                    ORDER BY bp.grade DESC NULLS LAST
                    LIMIT 40
                """, (chart_id, CANONICAL_AYA))
                pratijna_rows = cur.fetchall()

            if pratijna_rows:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute("""
                        SELECT signal_id, signal_type_id, computed_salience, signature_tier AS tier,
                               constituent_facts_array, classical_sources_array
                        FROM bodha_msr_signals
                        WHERE chart_id = %s AND ayanamsha_id = %s
                        ORDER BY computed_salience DESC NULLS LAST
                    """, (chart_id, CANONICAL_AYA))
                    signal_by_id = {str(r["signal_id"]): r for r in cur.fetchall()}

                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute("""
                        SELECT signal_a_id, signal_b_id, tension_class,
                               domains_affected_array, combined_salience,
                               resolution_hint_jsonb, verification_pass_status
                        FROM bodha_contradictions
                        WHERE chart_id = %s AND ayanamsha_id = %s
                        ORDER BY combined_salience DESC NULLS LAST, contradiction_id ASC LIMIT 100
                    """, (chart_id, CANONICAL_AYA))
                    all_contradictions = cur.fetchall()

                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute("""
                        SELECT question_class, tradition, concordance_score, signal_ids
                        FROM bodha_triangulation
                        WHERE chart_id = %s AND ayanamsha_id = %s
                    """, (chart_id, CANONICAL_AYA))
                    trad_by_class: dict[str, dict] = {}
                    for tr in cur.fetchall():
                        qc = tr["question_class"]
                        if qc not in trad_by_class:
                            trad_by_class[qc] = {}
                        trad_by_class[qc][tr["tradition"]] = {
                            "concordance_score": float(tr.get("concordance_score") or 0),
                            "signal_count": len(tr.get("signal_ids") or []),
                        }

                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(DISTINCT ayanamsha_id) FROM bodha_pratijna WHERE chart_id = %s",
                        (chart_id,),
                    )
                    aya_row = cur.fetchone()
                    aya_count = int(aya_row["count"]) if aya_row else 0

                for pr in pratijna_rows:
                    event_class_id = pr["event_class_id"]
                    domain = pr.get("domain") or "unknown"
                    name_en = pr.get("name_en") or event_class_id
                    status = pr.get("status", "conditional")
                    # D4_GRADE_INVERSION fix (P0-10): `pr.get("grade") or 5.0` used
                    # Python truthiness, which treats a genuinely computed 0.0 grade
                    # (per bodha_pratijna migration 391: "0=strongly denied,
                    # 10=strongly promised") as absent and silently substitutes the
                    # neutral default. Only an actually-missing grade (None) should
                    # fall back to 5.0.
                    _raw_grade = pr.get("grade")

                    # L7-SERVING / R8 (ŚABDA-ŚUDDHI): bo_pratijna v2.0 introduces
                    # status='no_evidence' for event classes with zero supporting or
                    # contradicting signals. grade IS NULL by design for these rows —
                    # it cannot be scored because there is nothing to score.
                    # §N.7 item 6: "an honest null beats an invented judgment."
                    # Branching early: no_evidence rows must not run through the
                    # grade→verdict_note→statement flow that would fabricate a
                    # "grade 5.0/10. Conditional." statement from a null grade.
                    if status == "no_evidence":
                        _ne_sup_ids = [str(s) for s in (pr.get("supporting_signal_ids") or [])][:5]
                        _ne_verdict_content = {
                            "event_class_id": event_class_id,
                            "event_class_name": name_en,
                            "domain": domain,
                            "activation_state": "no_evidence",
                            "grade": None,
                            "ayanamsha_robustness": aya_count,
                            "canonical_ayanamsha_id": CANONICAL_AYA,
                            "ranked_evidence": [],
                            "contradictions": [],
                            "tradition_concordance": {},
                        }
                        rows.append((
                            chart_id,
                            f"verdict_{event_class_id[:50]}",
                            "verdict_object",
                            domain, None, event_class_id,
                            f"{name_en}: no evidence — no supporting or contradicting signals available for this event class.",
                            0.0,       # rank_consequence: lowest, but row is still written (R6)
                            None,      # confidence_band: no band computable from a null grade
                            0,         # n_support: genuinely zero
                            "not_assessed",
                            "structural",
                            LEL_VERSION,
                            None,
                            json.dumps(_ne_verdict_content),
                            False,
                            SURFACE_FORMULA_VERSION,
                        ))
                        continue

                    grade = float(_raw_grade) if _raw_grade is not None else 5.0

                    sup_ids = [str(s) for s in (pr.get("supporting_signal_ids") or [])][:5]
                    ranked_evidence = [
                        {
                            "signal_id": sid,
                            "signal_type_id": signal_by_id[sid].get("signal_type_id"),
                            "salience": float(signal_by_id[sid].get("computed_salience") or 0),
                            "tier": signal_by_id[sid].get("tier"),
                            "fact_ids": signal_by_id[sid].get("constituent_facts_array") or [],
                            "classical_sources": signal_by_id[sid].get("classical_sources_array") or [],
                        }
                        for sid in sup_ids if sid in signal_by_id
                    ]

                    # PRATIJÑĀ v4 Lane B4 fallback: the v4 bo_pratijna engine
                    # never populates supporting_signal_ids (it never reads
                    # bodha_msr_signals at all — see bo_pratijna.py's module
                    # docstring). Without this, ranked_evidence would be
                    # silently empty for every promised/conditional/denied
                    # row, contradicting a "Strong evidence" verdict_note with
                    # zero cited evidence. v4's real evidence for the class is
                    # its own derivation.factor_ledger (§2 of
                    # V4_RUBRIC_SPEC_v1_0.md) — a real, deterministic,
                    # per-factor classical citation, never invented here.
                    if not ranked_evidence:
                        factor_ledger = (pr.get("derivation") or {}).get("factor_ledger")
                        if isinstance(factor_ledger, list):
                            ranked = sorted(
                                (f for f in factor_ledger if isinstance(f, dict)),
                                key=lambda f: float(f.get("contribution") or 0.0),
                                reverse=True,
                            )
                            ranked_evidence = [
                                {
                                    "signal_id": None,
                                    "signal_type_id": None,
                                    "salience": float(f.get("contribution") or 0.0),
                                    "tier": f.get("dignity_state"),
                                    "fact_ids": [],
                                    "classical_sources": [],
                                    "slot": f.get("slot"),
                                    "graha": f.get("graha") or f.get("lord"),
                                }
                                for f in ranked[:5]
                            ]

                    domain_contras = [
                        {
                            "signal_a_id": str(c.get("signal_a_id")),
                            "signal_b_id": str(c.get("signal_b_id")),
                            "tension_class": c.get("tension_class"),
                            "combined_salience": float(c.get("combined_salience") or 0),
                            "resolution": c.get("resolution_hint_jsonb"),
                            "verification_status": c.get("verification_pass_status"),
                        }
                        for c in all_contradictions
                        if domain in (c.get("domains_affected_array") or [])
                    ][:3]

                    # SV-5 fix (ŚUDDHA-VĀCA parked finding, NIḤŚEṢA Track B): `trad_by_class`
                    # is keyed by `question_class`, which bo_sangati.py always populates as
                    # `domain` (never `event_class_id` — see bo_sangati.py's bodha_triangulation
                    # INSERT, "question_class": domain). The `trad_by_class.get(event_class_id)`
                    # lookup this line used to try first was therefore unreachable for 100% of
                    # rows — dead code implying an event-class-level granularity that does not
                    # exist. Removed; the only real lookup is by domain.
                    tradition_concordance = trad_by_class.get(domain) or {}

                    g_norm = grade / 10.0
                    if grade >= 6.0:
                        conf_lo = round(max(0.0, g_norm - 0.2), 2)
                        conf_hi = round(min(1.0, g_norm + 0.1), 2)
                    elif grade >= 3.0:
                        conf_lo = round(max(0.0, g_norm - 0.15), 2)
                        conf_hi = round(min(1.0, g_norm + 0.15), 2)
                    else:
                        conf_lo = round(max(0.0, g_norm), 2)
                        conf_hi = round(min(1.0, g_norm + 0.2), 2)

                    # SV-5 fix continued: the old single-axis verdict_note said "across
                    # traditions" purely from `grade >= 6.0`, regardless of whether
                    # `tradition_concordance` (just above) actually held any cross-tradition
                    # data — an invented judgment, not a restatement of a cited fact (§N.7
                    # item 6: "an honest null beats an invented judgment"). Restructured
                    # across both axes the source finding named: grade tier AND whether
                    # `bodha_triangulation` actually produced concordance data for this
                    # domain. When there is no data, the note says so explicitly instead of
                    # implying a cross-tradition check that never ran.
                    has_tradition_data = bool(tradition_concordance)
                    if grade >= 6.0:
                        verdict_note = (
                            "Strong evidence, corroborated across traditions."
                            if has_tradition_data
                            else "Strong evidence (single-tradition basis; no cross-tradition concordance data)."
                        )
                    elif grade < 3.0:
                        verdict_note = (
                            "Mixed or insufficient evidence, disputed across traditions."
                            if has_tradition_data
                            else "Mixed or insufficient evidence."
                        )
                    else:
                        verdict_note = (
                            "Conditional — context-dependent, per cross-tradition concordance."
                            if has_tradition_data
                            else "Conditional — context-dependent."
                        )

                    statement = f"{name_en}: {status} (grade {grade:.1f}/10). {verdict_note}"

                    verdict_content = {
                        "event_class_id": event_class_id,
                        "event_class_name": name_en,
                        "domain": domain,
                        "activation_state": status,
                        "grade": grade,
                        "ayanamsha_robustness": aya_count,
                        "canonical_ayanamsha_id": CANONICAL_AYA,
                        "ranked_evidence": ranked_evidence,
                        "contradictions": domain_contras,
                        "tradition_concordance": tradition_concordance,
                    }

                    rows.append((
                        chart_id,
                        f"verdict_{event_class_id[:50]}",
                        "verdict_object",
                        domain, None, event_class_id,
                        statement,
                        g_norm,
                        f"[{conf_lo},{conf_hi})",
                        len(ranked_evidence),
                        "not_assessed",
                        "structural",
                        LEL_VERSION,
                        None,
                        json.dumps(verdict_content),
                        False,
                        SURFACE_FORMULA_VERSION,
                    ))

        # Idempotency: delete prior insight units and their embeddings
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_insight_embeddings WHERE chart_id = %s", (chart_id,))
            cur.execute("DELETE FROM mimamsa_insight_units WHERE chart_id = %s", (chart_id,))

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no source data — 0 insight units")

        SQL = """
            INSERT INTO mimamsa_insight_units (
                chart_id, insight_id, insight_type, domain, horizon, question_lens,
                statement, rank_consequence, confidence_band, n_support,
                leakage_status, evidence_grade, freshness_lel_version,
                last_calibrated_at, provenance_chain, is_negative_knowledge,
                surface_formula_version
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,
                %s::numrange,
                %s,%s,%s,%s,%s,%s,%s,%s
            )
        """
        BATCH = 500
        with conn.cursor() as cur:
            for i in range(0, len(rows), BATCH):
                cur.executemany(SQL, rows[i:i+BATCH])

        logger.info("[mi_darshana:insight_units] %d insight units for chart %s",
                    len(rows), chart_id)
        self._insight_count = len(rows)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── embeddings ───────────────────────────────────────────────────────────

    def _substep_embeddings(self, conn, chart_id: str, t0: float) -> WriterResult:
        # Per B.10: generating vector embeddings requires an external embedding model.
        # This substep logs the requirement but does NOT insert fake vectors.
        # [EXTERNAL_COMPUTATION_REQUIRED]: call embedding model (e.g. text-embedding-3-small)
        # on each mimamsa_insight_units.statement and INSERT into mimamsa_insight_embeddings.
        insight_count = getattr(self, "_insight_count", 0)
        logger.warning(
            "[mi_darshana:embeddings] %d insight units require external embedding calls "
            "[EXTERNAL_COMPUTATION_REQUIRED]. "
            "Run the embedding service against mimamsa_insight_units WHERE chart_id = '%s' "
            "to populate mimamsa_insight_embeddings.",
            insight_count, chart_id,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=(
                f"[EXTERNAL_COMPUTATION_REQUIRED] {insight_count} insight units need embedding. "
                "INSERT into mimamsa_insight_embeddings via external model call."
            ),
        )

    # ── views_verify ─────────────────────────────────────────────────────────

    def _substep_views_verify(self, conn, chart_id: str, t0: float) -> WriterResult:
        counts = {}
        for view in [
            "vw_mimamsa_insight_by_domain",
            "vw_mimamsa_insight_by_horizon",
            "vw_mimamsa_insight_by_lens",
            "vw_mimamsa_negative_knowledge",
        ]:
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {view} WHERE chart_id = %s", (chart_id,))
                    r = cur.fetchone()
                    counts[view] = r["count"] if r else 0
            except Exception as exc:
                counts[view] = f"ERROR: {exc}"

        logger.info("[mi_darshana:views_verify] chart %s view counts: %s", chart_id, counts)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=f"view counts: {counts}",
        )
