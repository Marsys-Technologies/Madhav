"""
test_has_writer_completeness — CI guard preventing has_writer drift.

WHAT THIS TEST PROTECTS AGAINST
────────────────────────────────
Migration 342 set has_writer=true for assets known at the time it was written.
Sixteen writers added later (4 L2 Bodha + 12 L5 Mīmāṃsā) were silently excluded
from every build plan because the plan resolver query gates on:
    WHERE is_active = true AND has_writer = true

This test makes that class of failure visible BEFORE a build attempt reveals it
as empty tables or cascade-blocked downstream assets.

TWO TEST MODES
──────────────
1. Offline (always runs): discovers WRITER_REGISTRY from the Python codebase and
   asserts that every registered asset_id either:
     (a) is known to have has_writer=true (the "known-good" set below), OR
     (b) is a declared sub-registration with no independent DB row.
   If a new writer is added without updating this file, this test fails.

2. Live (requires DATABASE_URL env var): queries asset_registry directly and
   asserts that every WRITER_REGISTRY key has has_writer=true in the DB.
   Run this locally and in CI where a Postgres connection is available.

KEEPING THIS FILE CURRENT
─────────────────────────
When you add a new writer via @register('<asset_id>'):
  Step 1: Write a migration that sets has_writer=true for the new asset_id.
  Step 2: Add the asset_id to KNOWN_HAS_WRITER_TRUE below.
Both steps are required. Forgetting step 1 → silent build exclusion.
Forgetting step 2 → this test fails immediately.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ── Offline reference sets ────────────────────────────────────────────────────

# All asset_ids for which a migration (342 or later) sets has_writer=true.
# Update this set whenever you add a new @register()+migration pair.
KNOWN_HAS_WRITER_TRUE: frozenset[str] = frozenset({
    # ── L0 Brahmagyan — migration 342 ────────────────────────────────────────
    "bg_compendium_index",
    "bg_concordance",
    "bg_dasha_systems",
    "bg_dignity_reference",
    "bg_doshas",
    "bg_ephemeris",
    "bg_medical_mappings",
    "bg_nakshatra",
    "bg_ontology",
    "bg_prashna_rules",
    "bg_reference",
    "bg_remedies",
    "bg_rules",
    "bg_text_index",
    "bg_texts",
    "bg_transit_rules",
    "bg_vastu_directions",
    "bg_yogas",
    # ── L0 Brahmagyan — migrations 387-389 (BA-P3A) ──────────────────────────
    "bg_class_priors",
    "bg_ghatana",
    "bg_formula_constants",
    # ── L0 Brahmagyan — migration 431 (WP-2.5 / LCA-16) ──────────────────────
    "bg_sign_medical",
    # ── L0/L1 Brahmagyan — migration 440 (D-2 Lane V-1, vidhi registry) ──────
    "bg_vidhi_primitives",
    "bg_vidhi_floors",
    # ── L0 Brahmagyan — migration 472 (ṢAḌ-DARŚANA item 22, synthetic cohort) ─
    "bg_cohort",
    # ── L0 Brahmagyan — migration 473 (ṢAḌ-DARŚANA item 3, sky-event calendar) ──
    "bg_sky_calendar",
    # ── L0 Brahmagyan — migration 484 (ṢAḌ-DARŚANA item 36-substrate, muhūrta lattice) ──
    "bg_muhurta_lattice",
    # ── L0 Brahmagyan — migration 485 (ṢAḌ-DARŚANA item 36-substrate/41, parihāra rules) ──
    "bg_parihara_rules",
    # ── L0 Brahmagyan — migration 522 (ṢAḌ-DARŚANA W2 / ADJUDICATION-2, N_e priors) ──
    # Step 1 (migration setting has_writer=true) is migration 522's asset_registry
    # INSERT, which carries `has_writer` true / `has_substeps` false: this writer
    # implements run(ctx), not plan_substeps.
    "bg_class_lifetime_counts",
    # ── L0 Brahmagyan — migration 523 (ṢAḌ-DARŚANA W3 Lane w3-kota-rings,
    # ADJUDICATION-9 — Kota-Chakra ring table moved to a versioned L0 asset) ──
    "bg_kota_chakra_rings",
    # ── L1 Gaṇita — migration 342 ────────────────────────────────────────────
    "ga_condition",
    "ga_dashas",
    "ga_medical",
    "ga_nakshatra",
    "ga_panchanga",
    "ga_positions",
    "ga_prashna",
    "ga_sade_sati",
    "ga_sensitive",
    "ga_strength",
    "ga_structural",
    "ga_tajaka",
    "ga_transit_anchors",
    "ga_vargas",
    "ga_vastu",
    "ga_yoga",
    # ── L1 Gaṇita — migration 432 (WP-2.5 / LCA-10) ──────────────────────────
    "ga_sensitive_degree",
    "ga_ayurdaya",
    # ── L1 Gaṇita — migration 435 (Doctrine Campaign Night-1, Lane 2) ────────
    "ga_vichara",
    # ── L2 Bodha — migration 342 ─────────────────────────────────────────────
    "bo_anveshana",
    "bo_bimba",
    "bo_drishti",
    "bo_karanajala",
    "bo_laksana",
    "bo_pramana_mapa",
    "bo_samskara",
    "bo_samvada",
    "bo_sangati",
    "bo_upaya",
    # ── L2 Bodha — migration 370 ─────────────────────────────────────────────
    "bo_cdlm_summary",
    "bo_cgm_motifs",
    "bo_cgm_paths",
    "bo_chart_gestalt",
    # ── L2 Bodha — migration 391 (BA-P3B) ────────────────────────────────────
    "bo_pratijna",
    # ── L2 Bodha — migration 438 (D-1.5b Lane B-3, CR-100 Sudarshana Chakra) ──
    "bo_sudarshana",
    # ── L2 Bodha — migrations 445/446 (D-2 Lane V-4, Mechanism object) ────────
    "bo_yantra_mechanism",
    "bo_laksana_rerank",
    # ── L2 Bodha — migrations 450-453 (D-2 Lane V-5, CR-26/64+61+76+36) ──────
    "bo_nakshatra_semantic",
    "bo_arudha",
    "bo_special_lagna",
    "bo_vargottama_dhana",
    # ── L3 Kāla — migration 342 ──────────────────────────────────────────────
    "ka_bhavishya_lekha",
    "ka_dasha_kala",
    "ka_gochara",
    "ka_graha_sancara",
    "ka_jivana_parva",
    "ka_kala_darshana",
    "ka_kalasutra",
    "ka_muhurta_seva",
    "ka_sangam",
    "ka_vighnakara",
    "ka_yojaka",
    # ── L3 Kāla — migration 370 ──────────────────────────────────────────────
    "ka_tulana",
    # ── L3 Kāla — migrations 395–396 (BA-P5A) ────────────────────────────────
    "ka_avadhi",
    "ka_taranga",
    # ── L3 Kāla — migration 459 (D-5 Lane G-1 Resonance Map) ─────────────────
    "ka_gochara_resonance",
    "ka_gochara_sweep",
    # ── L3 Kāla — migration 480 (ṢAḌ-DARŚANA W2 Lane C, the temporal field) ──
    "ka_kshetra",
    # ── L3 Kāla — migrations 520/521 (ṢAḌ-DARŚANA W3 Lane w3-kota-sudarshana,
    # registry items 16/17) ──────────────────────────────────────────────────
    "ka_kota_chakra",
    "ka_sudarshana_varsha",
    # ── L3 Kāla — migrations 525/526 (ṢAḌ-DARŚANA W3 Lane w3-moorti-vedha,
    # registry items 4/5) ─────────────────────────────────────────────────────
    "ka_moorti_nirnaya",
    "ka_vedha_gochara",
    # ── Brahmagyan — migration 528 (ADJUDICATION-11 Part 4, mandatory cited
    # vedha rows for R-19 closure; bg_sarvatobhadra_grid, migration 529, has
    # NO writer — deliberately empty, migration-seeded only) ─────────────────
    "bg_vedha_malefic_scale",
    "bg_phaladeepika_latta",
    # ── L4 Phala — migration 342 ─────────────────────────────────────────────
    "ph_muhurta",
    "ph_nimitta",
    "ph_phaladesa",
    "ph_pramana",
    "ph_pratikara",
    "ph_rectification",
    "ph_sankrama",
    "ph_sodhana",
    "ph_suddha_sodhana",
    # ── L5 Mīmāṃsā — migration 370 ───────────────────────────────────────────
    "mi_abhilekha",
    "mi_adhilepa",
    "mi_bhavisya",
    "mi_darshana",
    "mi_gunanaka",
    "mi_jivanaghatana",
    "mi_kula",
    "mi_pariksha",
    "mi_pramana",
    "mi_sambandha",
    "mi_seva",
    "mi_vistara",
    # ── L5 Mīmāṃsā — migration 483 (ṢAḌ-DARŚANA W2 Lane E, items 21/39) ──────
    # Stage 9 of the temporal-field pipeline: weight fitting, weights versioning,
    # temporal skill score, time-rescaling GOF, and the Living-LEL plane.
    # depends_on = ['ka_kshetra'] ONLY — never the reverse (KALA_W2_FIELD_DESIGN
    # §7.5: that edge would form an L3↔L5 cycle and topoSort would reject every
    # build plan containing either asset).
    "mi_bhara",
    # ── L5 Mīmāṃsā — migration 531 (ṢAḌ-DARŚANA W4 Lane S, item 42) ──────────
    # Unified Intervention Ledger: falsifier resolution against the LEL, study-arm
    # reclassification, and arm-4 (acted_without_election) origination. Filing
    # itself happens live, at serve time, through the sanctioned HTTP action
    # (platform-mcp/src/lib/intervention_filing.ts) — never inserted by this
    # writer. depends_on = ['ka_kshetra'] ONLY (KALA_W2_FIELD_DESIGN §7.5
    # acyclicity rule, mirrored from mi_bhara above).
    "mi_sankalpa",
})

# Sub-registrations that share a writer with their parent.
# They have no independent asset_registry row and are not plan-level assets.
KNOWN_SUBASSETS: frozenset[str] = frozenset({
    "bg_nakshatra_medical",   # sub-table inside bg_medical_mappings writer
    "bg_transit_engine",      # sub-table inside bg_transit_rules writer
})


def _import_writer_registry() -> dict:
    """Import WRITER_REGISTRY without requiring a live DB connection."""
    sidecar_root = Path(__file__).parent.parent
    if str(sidecar_root) not in sys.path:
        sys.path.insert(0, str(sidecar_root))
    from pipeline.orchestrator.writers import discover_all, WRITER_REGISTRY
    discover_all()
    return dict(WRITER_REGISTRY)


# ── Offline tests (always run) ────────────────────────────────────────────────

class TestOfflineHasWriterCompleteness:
    """
    Pure Python; no DB required. Fails if a new @register()'d writer is not in
    KNOWN_HAS_WRITER_TRUE (meaning the developer forgot to write the migration or
    forgot to update this file).
    """

    def _registry(self) -> dict:
        return _import_writer_registry()

    def test_no_registered_writer_is_missing_from_known_good_set(self):
        registry = self._registry()
        plan_level_ids = set(registry.keys()) - KNOWN_SUBASSETS
        uncovered = plan_level_ids - KNOWN_HAS_WRITER_TRUE
        assert not uncovered, (
            f"New writer(s) registered via @register() but NOT listed in "
            f"KNOWN_HAS_WRITER_TRUE (tests/test_has_writer_completeness.py) "
            f"AND not declared as a sub-asset. This means they also need a "
            f"migration setting has_writer=true in asset_registry. "
            f"Missing: {sorted(uncovered)}"
        )

    def test_known_good_set_has_no_phantom_entries(self):
        """
        Every asset_id in KNOWN_HAS_WRITER_TRUE must correspond to a real
        @register()'d writer OR a known sub-asset. Phantom entries in
        KNOWN_HAS_WRITER_TRUE silently mask missing writers.
        """
        registry = self._registry()
        all_known_ids = set(registry.keys())
        phantoms = KNOWN_HAS_WRITER_TRUE - all_known_ids
        assert not phantoms, (
            f"KNOWN_HAS_WRITER_TRUE contains asset_ids with NO corresponding "
            f"@register() writer. Remove them from KNOWN_HAS_WRITER_TRUE: "
            f"{sorted(phantoms)}"
        )

    def test_subassets_do_not_overlap_with_known_good_set(self):
        """A sub-asset cannot also be a plan-level asset."""
        overlap = KNOWN_SUBASSETS & KNOWN_HAS_WRITER_TRUE
        assert not overlap, (
            f"These asset_ids appear in both KNOWN_SUBASSETS and "
            f"KNOWN_HAS_WRITER_TRUE — pick one: {sorted(overlap)}"
        )


# ── Live tests (require DATABASE_URL) ────────────────────────────────────────

@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — live DB test skipped",
)
class TestLiveHasWriterCompleteness:
    """
    Queries asset_registry directly. Run locally and in CI where a Postgres
    connection is available. Catches gaps that the offline test cannot see
    (e.g. a migration that was written but not applied to the target DB).
    """

    def _db_rows(self) -> dict[str, bool]:
        import psycopg
        import psycopg.rows
        conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
        with conn.cursor() as cur:
            cur.execute("SELECT asset_id, has_writer FROM asset_registry")
            rows = {r["asset_id"]: r["has_writer"] for r in cur.fetchall()}
        conn.close()
        return rows

    def test_all_registered_writers_have_has_writer_true_in_db(self):
        registry = _import_writer_registry()
        plan_level_ids = set(registry.keys()) - KNOWN_SUBASSETS
        db_rows = self._db_rows()

        missing_row: list[str] = []
        has_writer_false: list[str] = []

        for aid in sorted(plan_level_ids):
            if aid not in db_rows:
                missing_row.append(aid)
            elif not db_rows[aid]:
                has_writer_false.append(aid)

        errors: list[str] = []
        if missing_row:
            errors.append(
                f"Writers registered in Python but NOT in asset_registry at all: "
                f"{missing_row}"
            )
        if has_writer_false:
            errors.append(
                f"Writers in asset_registry with has_writer=false (invisible to "
                f"plan resolver): {has_writer_false}. "
                f"Apply the migration that sets has_writer=true for these assets."
            )
        assert not errors, "\n".join(errors)
