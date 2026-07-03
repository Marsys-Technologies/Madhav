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

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

FORMULA_VERSION = "mi_kula_v2.0"

# BA-P6 C6 weight unification: prior_weight values are authoritative in brahma_class_priors.
# This map resolves family_id → (signal_type_class, source_subsystem) for the registry lookup.
# Fallback: the hardcoded prior_weight in _FAMILIES below if no registry match.
_FAMILY_TO_PRIOR_KEY: dict[str, tuple[str, str]] = {
    "fam_graha_natal":  ("position",        "*"),
    "fam_dasha_period": ("dasha_period",     "*"),
    "fam_yoga":         ("yoga",             "*"),
    "fam_divisional":   ("varga_pattern",    "*"),
    "fam_transit":      ("time_window",      "*"),
    "fam_convergence":  ("composite_state",  "*"),
    "fam_ashtakavarga": ("*",                "strength_ashtakavarga"),
    "fam_msr_signal":   ("configuration",    "*"),
    "fam_anchor":       ("time_window",      "*"),
}


def _load_registry_priors(conn) -> dict[str, float]:
    """
    Read prior weights from brahma_class_priors for each family_id via _FAMILY_TO_PRIOR_KEY.
    Returns {family_id: class_prior}. Falls back to empty dict on any error.
    """
    sp = "sp_kula_priors"
    result: dict[str, float] = {}
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(f"SAVEPOINT {sp}")
            cur.execute(
                "SELECT signal_type_class, source_subsystem, class_prior "
                "FROM brahma_class_priors "
                "WHERE prior_version = '1.0' "
                "  AND signal_tradition = '*' "
                "  AND fact_kind = '*'"
            )
            rows = cur.fetchall()
            cur.execute(f"RELEASE SAVEPOINT {sp}")
        # Index: (signal_type_class, source_subsystem) → class_prior
        idx: dict[tuple[str, str], float] = {
            (r["signal_type_class"], r["source_subsystem"]): float(r["class_prior"])
            for r in rows
        }
        for family_id, (stc, sub) in _FAMILY_TO_PRIOR_KEY.items():
            prior = idx.get((stc, sub)) or idx.get((stc, "*")) or idx.get(("*", sub))
            if prior is not None:
                result[family_id] = prior
    except Exception as e:
        try:
            with conn.cursor() as cur:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        logger.warning("[mi_kula] brahma_class_priors lookup failed (%s); using catalog defaults", e)
    return result


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

        # C6 weight unification: override prior_weight from brahma_class_priors registry
        registry_priors = _load_registry_priors(conn)

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

        # prior_weight (index 8) overridden from registry; catalog value is fallback
        fam_rows = []
        for row in _FAMILIES:
            family_id = row[0]
            row_list = list(row)
            registry_w = registry_priors.get(family_id)
            if registry_w is not None:
                row_list[8] = registry_w  # override prior_weight from brahma_class_priors
            fam_rows.append((*row_list, FORMULA_VERSION))

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
