"""
mi_kula — Signal-Family Registry + Negative-Control Battery (L5 Mīmāṃsā)
=========================================================================
Populates two global catalog tables:
  • mimamsa_signal_families — Jyotish evidence families with tier + prior weights
  • mimamsa_negative_controls — known-false signal battery for QA harness

GLOBAL scope: deletes all rows and re-seeds from the embedded catalog.
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
Deterministic: static catalog, no LLM.
"""
from __future__ import annotations

import json
import logging
import time

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

FORMULA_VERSION = "mi_kula_v1.0"

# ── Signal-family catalog ────────────────────────────────────────────────────
# Each entry: (family_id, display_name, layman_name, family_class,
#              evidence_tier, soundness_basis, binding_kind, default_state,
#              prior_weight, calibration_status, citation_refs_json,
#              binding_spec_json)
_FAMILIES = [
    (
        "fam_graha_natal",
        "Natal Graha Placement",
        "Birth Planet Positions",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "natal",
        "ON",
        1.0,
        "prior_only",
        json.dumps(["BPHS §3", "Saravali §4"]),
        json.dumps({"source": "chart_facts", "filter": "category='graha'"}),
    ),
    (
        "fam_dasha_period",
        "Vimshottari Dasha Period",
        "Planetary Time Period",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "lifetime_index",
        "ON",
        1.2,
        "prior_only",
        json.dumps(["BPHS §46", "Phaladeepika §20"]),
        json.dumps({"source": "chart_dashas", "system": "vimshottari"}),
    ),
    (
        "fam_yoga",
        "Yoga Combinations",
        "Planetary Yoga Patterns",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "natal",
        "ON",
        0.9,
        "prior_only",
        json.dumps(["BPHS §36", "Mansagari §5"]),
        json.dumps({"source": "chart_facts", "filter": "category='yoga'"}),
    ),
    (
        "fam_divisional",
        "Divisional Chart Placements",
        "Harmonic Chart Factors",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "natal",
        "ON",
        0.8,
        "prior_only",
        json.dumps(["BPHS §7", "Jaimini Sutras §1.3"]),
        json.dumps({"source": "chart_divisionals"}),
    ),
    (
        "fam_transit",
        "Graha Transit",
        "Current Planet Position",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "event_date",
        "ON",
        0.9,
        "prior_only",
        json.dumps(["BPHS §49", "Sarvartha Chintamani §10"]),
        json.dumps({"source": "kala_gochara", "method": "transit_to_natal"}),
    ),
    (
        "fam_convergence",
        "Multi-system Temporal Convergence",
        "Timing Cluster",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "event_date",
        "ON",
        1.1,
        "prior_only",
        json.dumps(["KP §8", "Jaimini §2.1"]),
        json.dumps({"source": "kala_convergence", "min_systems": 3}),
    ),
    (
        "fam_ashtakavarga",
        "Ashtakavarga",
        "Eight-Source Transit Strength",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "event_date",
        "ON",
        0.7,
        "prior_only",
        json.dumps(["BPHS §67"]),
        json.dumps({"source": "chart_facts", "filter": "category='ashtakavarga'"}),
    ),
    (
        "fam_msr_signal",
        "MSR Composite Signal",
        "Multi-System Resonance",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "natal",
        "ON",
        1.0,
        "prior_only",
        json.dumps(["MARSYS MSR §1"]),
        json.dumps({"source": "bodha_msr_signals"}),
    ),
    (
        "fam_anchor",
        "Phala Anchor Prediction",
        "Prediction Anchor",
        "classical",
        "CLASSICAL_CITED",
        "astrological",
        "lifetime_index",
        "ON",
        1.0,
        "prior_only",
        json.dumps(["MARSYS Phala §2"]),
        json.dumps({"source": "phala_anchors"}),
    ),
    (
        "fam_null_control",
        "Null / Random Control",
        "Random Baseline",
        "negative_control",
        "NEGATIVE_CONTROL",
        "scientific",
        "meta",
        "CONTROL_ONLY",
        0.0,
        "prior_only",
        json.dumps(["MARSYS Neg-Control §1"]),
        json.dumps({"source": "synthetic", "method": "random_uniform"}),
    ),
    (
        "fam_shuffled_birth",
        "Shuffled Birth-Data Control",
        "Swapped Birth Control",
        "negative_control",
        "NEGATIVE_CONTROL",
        "scientific",
        "meta",
        "CONTROL_ONLY",
        0.0,
        "prior_only",
        json.dumps(["MARSYS Neg-Control §2"]),
        json.dumps({"source": "synthetic", "method": "shuffle_birth_params"}),
    ),
]

# ── Negative-control battery ─────────────────────────────────────────────────
# (control_id, known_false_basis, citation_refs_json, binding_spec_json,
#  expected_score, tolerance)
_CONTROLS = [
    (
        "neg_random_uniform",
        "Uniformly-random event windows with no astrological grounding must score near chance.",
        json.dumps(["Shawn Carlson 1985, Nature 318:419"]),
        json.dumps({"method": "random_uniform_window", "n": 1000}),
        "near_zero",
        0.05,
    ),
    (
        "neg_shuffled_birth",
        "Signals computed from other charts' birth data must not predict this native's events.",
        json.dumps(["MARSYS Neg-Control design §2.1"]),
        json.dumps({"method": "shuffle_chart_id", "pool_size": 100}),
        "near_zero",
        0.05,
    ),
    (
        "neg_future_leak",
        "Signals anchored to post-event dates (simulated disclosure leak) must be excluded.",
        json.dumps(["MARSYS Leakage Protocol §1"]),
        json.dumps({"method": "backdated_signal_post_event", "n": 500}),
        "chance",
        0.10,
    ),
    (
        "neg_antiphase",
        "Anti-phase signals (exact complement of affirmed combinations) must score below baseline.",
        json.dumps(["MARSYS Neg-Control design §2.2"]),
        json.dumps({"method": "invert_yoga_combination", "n": 200}),
        "near_zero",
        0.08,
    ),
]


@register("mi_kula")
class MiKulaWriter(WriterBase):
    """
    Seeds global signal-family registry and negative-control battery.
    Idempotent: deletes all rows then re-inserts.
    """

    asset_id = "mi_kula"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(_FAMILIES) + len(_CONTROLS),
                duration_seconds=time.time() - t0,
                notes="dry_run: would seed signal families + negative controls",
            )

        # Idempotency: delete all (global catalog)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_negative_controls")
            cur.execute("DELETE FROM mimamsa_signal_families")

        FAM_SQL = """
            INSERT INTO mimamsa_signal_families (
                family_id, display_name, layman_name, family_class,
                evidence_tier, soundness_basis, binding_kind, default_state,
                prior_weight, calibration_status, citation_refs, binding_spec,
                is_active, formula_version
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s)
        """
        CTRL_SQL = """
            INSERT INTO mimamsa_negative_controls (
                control_id, known_false_basis, citation_refs, binding_spec,
                expected_score, tolerance, formula_version
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        fam_rows = [(*row, FORMULA_VERSION) for row in _FAMILIES]
        ctrl_rows = [(*row, FORMULA_VERSION) for row in _CONTROLS]

        with conn.cursor() as cur:
            cur.executemany(FAM_SQL, fam_rows)
            cur.executemany(CTRL_SQL, ctrl_rows)

        logger.info(
            "[mi_kula] seeded %d signal families + %d negative controls",
            len(_FAMILIES), len(_CONTROLS),
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(_FAMILIES) + len(_CONTROLS),
            duration_seconds=time.time() - t0,
        )
