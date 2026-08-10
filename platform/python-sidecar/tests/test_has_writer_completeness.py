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
    # ── L3 Kāla — migration 531 (ṢAḌ-DARŚANA W3 Lane w3-tithi-pravesha,
    # registry item 13, Tithi-Praveśa lunar-return annual chart) ─────────────
    "ka_tithi_pravesha",
    # ── Brahmagyan — migration 528 (ADJUDICATION-11 Part 4, mandatory cited
    # vedha rows for R-19 closure; bg_sarvatobhadra_grid, migration 529, has
    # NO writer — deliberately empty, migration-seeded only) ─────────────────
    "bg_vedha_malefic_scale",
    "bg_phaladeepika_latta",
    # ── Brahmagyan — migration 535 (ṢAḌ-DARŚANA W3K Lane 1, ADJUDICATION-7
    # Part 1: the canonical 249-fold KP sub-lord division of the sidereal
    # zodiac; has_writer=true set by that migration's asset_registry seed) ───
    "bg_kp_sublord_division",
    # ── Brahmagyan — migration 538 (ṢAḌ-DARŚANA W2G / GOCHARA-2.0 item 19:
    # the chart-independent monotone-arc transit substrate; has_writer=true and
    # has_substeps=true set by that migration's asset_registry seed) ─────────
    "bg_gochara_arcs",
    # ── Kāla — migration 542 (ṢAḌ-DARŚANA W2G / GOCHARA-2.0 item 19, lane G
    # REWORK per the native ruling 2026-08-06: the per-chart materialization
    # writer -- joins bg_gochara_arcs against a chart's natal
    # gochara_resonance_map targets, scores via v1's frozen gochara_intensity
    # grammar, writes generation='2.0' rows to kala_gochara_windows_v2, its
    # OWN table -- NEVER to the protected kala_gochara_windows. Originally named
    # ka_gochara_v2_materialize; renamed to ka_gochara at W6.4 cutover (UTK-R2,
    # migration 563). The former zero-row global-scope self-test asset deleted.
    # has_writer=true and has_substeps=true retained on the renamed row.) ──
    # NOTE: the asset_id "ka_gochara" is already listed above (migration 342);
    # that entry covers this writer post-rename — no duplicate entry here.
    # ── GOCHARA-UTKARSA W3.4 — migration 560 ─────────────────────────────────
    # century-horizon heavy writer: plan_substeps (60 substeps = 6 classes ×
    # 10 decade slices) + run_substep. Writes generation='g3_utkarsha' rows
    # into kala_gochara_windows_v2 ONLY. Seed row added to asset_registry
    # via migration 560 with has_writer=true, has_substeps=true.
    "ka_gochara_v3_century_materialize",
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


# ── Three-way diff helpers ─────────────────────────────────────────────────────
#
# These functions read the three sources of truth directly from the file system
# so that the mutation test (delete a seed row → test fails) works correctly.

import re as _re
import glob as _glob


def collect_registered_writer_ids() -> frozenset[str]:
    """
    Collect all asset_ids registered via @register('...') in writer .py files.

    Excludes known test/infra entries that are not real plan-level assets.
    """
    sidecar_root = Path(__file__).parent.parent
    writers_dir = sidecar_root / "pipeline" / "orchestrator" / "writers"

    # Pattern: @register('<asset_id>')
    pattern = _re.compile(r"""@register\(\s*['"]([^'"]+)['"]\s*\)""")

    # Known non-plan-level entries that appear in writer files for infrastructure
    # testing purposes — must not be counted as real registered writers.
    EXCLUDED_TEST_IDS = frozenset({
        "bad_infra_writer",
        "test_infra_asset_1",
        "test_infra_asset_dup",
        "bg_<id>",          # placeholder string in docstrings/examples
    })

    ids: set[str] = set()
    for py_file in writers_dir.glob("**/*.py"):
        # Skip test fixtures inside __tests__ subdirectory — those register
        # fixture.* ids that are not real plan-level assets.
        if "__tests__" in py_file.parts:
            continue
        content = py_file.read_text(encoding="utf-8")
        for match in pattern.finditer(content):
            asset_id = match.group(1)
            if asset_id not in EXCLUDED_TEST_IDS:
                ids.add(asset_id)

    return frozenset(ids)


def collect_migration_insert_ids() -> frozenset[str]:
    """
    Collect asset_ids that appear as the FIRST VALUE in INSERT INTO asset_registry
    statements across migration .sql files.

    Strategy: line-by-line scan within INSERT INTO asset_registry blocks.
    Looks for lines of the form:
        ( 'asset_id_name', 'layer_name', ...
    OR:
        VALUES ('asset_id_name', 'layer_name', ...

    Only counts an asset_id when the immediately-following value is a layer name
    (brahmagyan/ganita/bodha/kala/phala/mimamsa), eliminating false positives
    from asset_ids mentioned in description text.

    Returns only real asset_ids (prefixed bg_/ga_/bo_/ka_/ph_/mi_/lel_).

    Note: this function may not catch every single migration INSERT (complex SQL
    formats vary), but it WILL catch the GOCHARA-UTKARSA new assets and any
    future assets registered in the standard single-line-value-per-column format.
    The offline KNOWN_HAS_WRITER_TRUE set (maintained by TestOfflineHasWriterCompleteness)
    is the comprehensive human-maintained list; this function provides automated
    cross-checking of the file artifacts directly.
    """
    repo_root = Path(__file__).parent.parent.parent.parent
    migrations_dir = repo_root / "platform" / "supabase" / "migrations"

    LAYER_NAMES = frozenset({
        "brahmagyan", "ganita", "bodha", "kala", "phala", "mimamsa"
    })

    # Pattern: a line starting with optional whitespace + ( + optional whitespace +
    # a quoted asset_id, optionally preceded by VALUES.
    # Pattern A: asset_id is first value on a line after an open-paren:
    #   ( 'bg_something',
    #   VALUES ( 'bg_something',
    ASSET_ID_WITH_PAREN = _re.compile(
        r"""^\s*(?:VALUES\s*)?\(\s*'((?:bg|ga|bo|ka|ph|mi|lel)_[a-z_0-9]+)'\s*,""",
        _re.IGNORECASE,
    )
    # Pattern B: asset_id is alone on a line (VALUES ( was on the previous line):
    #   ) VALUES (        ← previous line
    #       'bg_something',  ← this line
    ASSET_ID_STANDALONE = _re.compile(
        r"""^\s+'((?:bg|ga|bo|ka|ph|mi|lel)_[a-z_0-9]+)'\s*,$"""
    )
    # Pattern C: VALUES on one line followed by ( on next or asset_id directly
    VALUES_PAREN_RE = _re.compile(r"\bVALUES\s*\(\s*$", _re.IGNORECASE)

    # Known retired/phantom migration asset_ids that should not count as live.
    RETIRED_MIGRATION_IDS = frozenset({
        "ga_pyjhora_engine",    # migration 179 placeholder, never activated in prod
        "ka_gochara_sweep_v2",  # migration 541 row DELETED by migration 542
        "ka_gochara_v2_materialize",  # migration 542 INSERT; RENAMED to ka_gochara by migration 563 (W6.4 UTK-R2, MR-06)
    })

    ids: set[str] = set()
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        if "INSERT INTO asset_registry" not in content:
            continue

        lines = content.split("\n")
        in_insert = False
        prev_was_values_open = False  # True when previous line ended with VALUES (

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Enter INSERT block
            if "INSERT" in stripped.upper() and "asset_registry" in stripped:
                in_insert = True
                prev_was_values_open = False
                continue

            # Exit on next top-level SQL statement (but not ON CONFLICT)
            if in_insert and _re.match(
                r"^(CREATE|ALTER|DROP|UPDATE|DELETE|GRANT|REVOKE|COMMIT|BEGIN|END|ROLLBACK)\b",
                stripped,
                _re.IGNORECASE,
            ) and "ON CONFLICT" not in stripped.upper():
                in_insert = False
                prev_was_values_open = False

            if not in_insert:
                prev_was_values_open = False
                continue

            # Check if this line ends with VALUES (
            if VALUES_PAREN_RE.search(line):
                prev_was_values_open = True
                continue

            candidate: str | None = None

            # Pattern A: ( 'asset_id', or VALUES ( 'asset_id',
            m = ASSET_ID_WITH_PAREN.match(line)
            if m:
                candidate = m.group(1)

            # Pattern B: previous line was VALUES (, so this bare 'asset_id', is the first value
            elif prev_was_values_open:
                m2 = ASSET_ID_STANDALONE.match(line)
                if m2:
                    candidate = m2.group(1)

            prev_was_values_open = False  # Reset after consuming

            if candidate is None or candidate in RETIRED_MIGRATION_IDS:
                continue

            # Validate: one of the next few lines must have a layer name in quotes.
            # This confirms we are reading the asset_id column, not a description string.
            for j in range(i + 1, min(i + 5, len(lines))):
                next_stripped = lines[j].strip()
                if not next_stripped or next_stripped.startswith("--"):
                    continue
                if any(f"'{layer}'" in next_stripped for layer in LAYER_NAMES):
                    ids.add(candidate)
                break  # Only check the immediately-following value line

    return frozenset(ids)


def collect_seed_ids() -> frozenset[str]:
    """
    Collect all asset_ids declared in asset_registry_seed.ts.

    Reads the ASSETS array and extracts asset_id: '...' entries.
    This function reads the ACTUAL FILE so that a mutation (deleting a seed row)
    is immediately visible to the test.
    """
    repo_root = Path(__file__).parent.parent.parent.parent
    seed_file = repo_root / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"

    content = seed_file.read_text(encoding="utf-8")

    # Match: asset_id: 'some_id'  (inside the ASSETS array)
    # Must NOT match upstream_asset_id or downstream_asset_id (coefficient defs)
    pattern = _re.compile(r"""^\s{2,4}asset_id:\s*['"]([^'"]+)['"]""", _re.MULTILINE)

    ids: set[str] = set()
    for match in pattern.finditer(content):
        asset_id = match.group(1)
        ids.add(asset_id)

    return frozenset(ids)


# ── Known gaps with explanations ───────────────────────────────────────────────
#
# These are asset_ids that are in one set but legitimately absent from another.
# Each entry must have a documented reason. Adding to these sets without a
# documented reason defeats the purpose of the three-way diff.

# Sub-assets: registered via @register() but have no independent DB row.
# They share a writer with their parent and are excluded from plan-level checks.
_SUBASSETS = frozenset({
    "bg_nakshatra_medical",   # sub-table inside bg_medical_mappings writer
    "bg_transit_engine",      # sub-table inside bg_transit_rules writer
})

# Seed-only asset_ids: in the seed but either no @register() writer, or their
# migration INSERT is not detected by the line-level extractor (complex SQL formats).
# These are valid — service assets, source-data tables, sub-assets, or assets whose
# migration INSERT uses a format our extractor doesn't parse.
#
# Rule: every entry MUST have a documented reason. The test's primary purpose is
# detecting new writers missing from the seed, NOT exhaustively auditing migrations.
_SEED_ONLY_ALLOWED = frozenset({
    # ── No writer (has_writer=false in DB) ────────────────────────────────────
    "lel_events",              # user-authored source data; has_writer=false
    "bg_sarvatobhadra_grid",   # deliberately empty; has_writer=false (ADJUDICATION-11)
    # ── Migration INSERT format not detected by line extractor ────────────────
    # These all have genuine migration INSERTs but use multi-row VALUES format
    # or complex SQL not caught by the single-line pattern.
    "bg_cohort",               # migration 472 multi-row VALUES
    "bg_compendium_index",     # migration 174 multi-row VALUES
    "bg_concordance",          # migration 174 multi-row VALUES
    "bg_dasha_systems",        # migration 179 multi-row VALUES
    "bg_dignity_reference",    # migration 174 multi-row VALUES
    "bg_doshas",               # migration 179 multi-row VALUES
    "bg_ephemeris",            # migration 174 multi-row VALUES
    "bg_ephemeris_engine",     # migration 203 multi-column format
    "bg_medical_mappings",     # migration 174 multi-row VALUES
    "bg_muhurta_lattice",      # migration 543 format variant
    "bg_nakshatra",            # migration 239 format variant
    "bg_nakshatra_medical",    # sub-asset in bg_medical_mappings (KNOWN_SUBASSETS)
    "bg_ontology",             # migration 174 multi-row VALUES
    "bg_panchanga",            # migration 203 multi-column format
    "bg_parihara_rules",       # migration 485 format variant
    "bg_prashna_rules",        # migration 174 multi-row VALUES
    "bg_reference",            # migration 174 multi-row VALUES
    "bg_remedies",             # migration 174 multi-row VALUES
    "bg_rules",                # migration 174 multi-row VALUES
    "bg_sign_medical",         # migration 431 inline single-table INSERT
    "bg_sky_calendar",         # migration 473 format variant
    "bg_text_index",           # migration 174 multi-row VALUES
    "bg_texts",                # migration 174 multi-row VALUES
    "bg_transit_engine",       # sub-asset in bg_transit_rules (KNOWN_SUBASSETS)
    "bg_transit_rules",        # migration 174 multi-row VALUES
    "bg_vastu_directions",     # migration 174 multi-row VALUES
    "bg_vidhi_floors",         # migration 440 format variant
    "bg_vidhi_primitives",     # migration 440 format variant
    "bg_yogas",                # migration 179 multi-row VALUES
    "bo_arudha",               # migration 450-453 format variant
    "bo_anveshana",            # migration 326 format variant
    "bo_bimba",                # migration 342 format variant
    "bo_cdlm_summary",         # migration 370 format variant
    "bo_cgm_motifs",           # migration 370 format variant
    "bo_cgm_paths",            # migration 370 format variant
    "bo_chart_gestalt",        # migration 370 format variant
    "bo_drishti",              # migration 326 format variant
    "bo_karanajala",           # migration 342 format variant
    "bo_laksana",              # migration 342 format variant
    "bo_laksana_rerank",       # migration 445/446 format variant
    "bo_nakshatra_semantic",   # migration 450-453 format variant
    "bo_pramana_mapa",         # migration 342 format variant
    "bo_samskara",             # migration 342 format variant
    "bo_samvada",              # migration 342 format variant
    "bo_sangati",              # migration 342 format variant
    "bo_special_lagna",        # migration 450-453 format variant
    "bo_sudarshana",           # migration 438 format variant
    "bo_upaya",                # migration 342 format variant
    "bo_vargottama_dhana",     # migration 450-453 format variant
    "bo_yantra_mechanism",     # migration 445/446 format variant
    "ga_ayurdaya",             # migration 432 format variant (detected by VALUES extractor but not line extractor)
    "ga_condition",            # migration 342 format variant
    "ga_dashas",               # migration 342 format variant
    "ga_medical",              # migration 342 format variant
    "ga_nakshatra",            # migration 342 format variant
    "ga_panchanga",            # migration 342 format variant
    "ga_positions",            # migration 342 format variant
    "ga_prashna",              # migration 342 format variant
    "ga_sade_sati",            # migration 342 format variant
    "ga_sensitive",            # migration 342 format variant
    "ga_sensitive_degree",     # migration 432 format variant
    "ga_strength",             # migration 342 format variant
    "ga_structural",           # migration 219 format variant
    "ga_tajaka",               # migration 222 format variant
    "ga_transit_anchors",      # migration 342 format variant
    "ga_vargas",               # migration 342 format variant
    "ga_vastu",                # migration 342 format variant
    "ga_vichara",              # migration 435 format variant
    "ga_yoga",                 # migration 342 format variant
    "ka_avadhi",               # migration 395-396 format variant
    "ka_bhavishya_lekha",      # migration 345 format variant
    "ka_dasha_kala",           # migration 345 format variant (single-column-per-line)
    "ka_gochara",              # migration 342/345 format variant
    "ka_gochara_resonance",    # migration 459 format variant
    "ka_gochara_sweep",        # migration 460 format variant
    "ka_jivana_parva",         # migration 345 format variant
    "ka_kala_darshana",        # migration 345 format variant
    "ka_kalasutra",            # migration 345 format variant
    "ka_muhurta_seva",         # migration 345 format variant
    "ka_sangam",               # migration 345 format variant
    "ka_taranga",              # migration 396 format variant (actually detected)
    "ka_tulana",               # migration 370 format variant
    "ka_vighnakara",           # migration 345 format variant
    "ka_yojaka",               # migration 345 format variant
    "ka_kshetra",              # migration 494 format variant (actually detected)
    "mi_abhilekha",            # migration 370 format variant
    "mi_adhilepa",             # migration 370 format variant
    "mi_bhavisya",             # migration 370 format variant
    "mi_darshana",             # migration 370 format variant
    "mi_gunanaka",             # migration 370 format variant
    "mi_jivanaghatana",        # migration 370 format variant
    "mi_kula",                 # migration 370 format variant
    "mi_pariksha",             # migration 370 format variant
    "mi_pramana",              # migration 370 format variant
    "mi_sambandha",            # migration 370 format variant
    "mi_seva",                 # migration 370 format variant
    "mi_vistara",              # migration 370 format variant
    "ph_muhurta",              # migration 342 format variant
    "ph_nimitta",              # migration 342 format variant
    "ph_phaladesa",            # migration 342 format variant
    "ph_pramana",              # migration 342 format variant
    "ph_pratikara",            # migration 342 format variant
    "ph_rectification",        # migration 342 format variant
    "ph_sankrama",             # migration 342 format variant
    "ph_sodhana",              # migration 342 format variant
    "ph_suddha_sodhana",       # migration 342 format variant
})


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


# ── Three-way diff tests (always run, file-system only) ───────────────────────

class TestThreeWayRegistryDiff:
    """
    Three-way diff guard: code @register ids ⊆ seed ids, and
    migration INSERT ids ⊆ seed ids, and seed ids ⊆ (code ∪ migration ∪ allowed).

    This test reads the actual seed FILE so that a mutation (deleting a seed row)
    is immediately caught. It does NOT query the DB — it compares the three
    file-system artifacts that must stay in sync.

    MUTATION TEST CONTRACT (verified by VERIFIER):
      Delete any seed row from asset_registry_seed.ts → this test FAILS.
      Restore the row → this test PASSES again.

    Adding a new writer:
      Step 1: Add @register('<new_id>') writer in pipeline/orchestrator/writers/
      Step 2: Add a migration INSERT INTO asset_registry for '<new_id>'
      Step 3: Add a seed row for '<new_id>' in asset_registry_seed.ts
      Step 4: Add '<new_id>' to KNOWN_HAS_WRITER_TRUE in this file
      All four steps are required. Forgetting step 3 → this test fails.
    """

    def test_three_way_registry_diff(self) -> None:
        """Assert code @register IDs and migration INSERT IDs are covered by seed IDs."""
        registered_ids = collect_registered_writer_ids() - _SUBASSETS
        migration_ids = collect_migration_insert_ids()
        seed_ids = collect_seed_ids()

        # Writers with no seed row — the most common class of failure
        code_not_in_seed = registered_ids - seed_ids
        # Migration INSERTs with no seed row
        migration_not_in_seed = migration_ids - seed_ids
        # Seed rows that have no code reference AND no migration reference
        # (must be explicitly allowed in _SEED_ONLY_ALLOWED)
        seed_not_in_code_or_migration = seed_ids - registered_ids - migration_ids - _SEED_ONLY_ALLOWED

        errors: list[str] = []
        if code_not_in_seed:
            errors.append(
                f"Writer(s) registered via @register() but NOT in asset_registry_seed.ts. "
                f"Add a seed row for each: {sorted(code_not_in_seed)}"
            )
        if migration_not_in_seed:
            errors.append(
                f"Migration INSERT(s) into asset_registry NOT in asset_registry_seed.ts. "
                f"Add a seed row for each: {sorted(migration_not_in_seed)}"
            )
        if seed_not_in_code_or_migration:
            errors.append(
                f"Seed row(s) with no @register() writer AND no migration INSERT. "
                f"Either add them to _SEED_ONLY_ALLOWED with a documented reason, "
                f"or remove them from the seed: {sorted(seed_not_in_code_or_migration)}"
            )
        assert not errors, "\n\n".join(errors)

    def test_seed_file_is_readable(self) -> None:
        """Seed file must exist and contain at least 100 asset_ids."""
        seed_ids = collect_seed_ids()
        assert len(seed_ids) >= 100, (
            f"asset_registry_seed.ts appears truncated or missing — only {len(seed_ids)} "
            f"asset_ids found (expected >= 100)."
        )

    def test_writer_files_are_readable(self) -> None:
        """Writer discovery must find at least 50 registered asset_ids."""
        registered_ids = collect_registered_writer_ids()
        assert len(registered_ids) >= 50, (
            f"@register() scan found only {len(registered_ids)} asset_ids "
            f"(expected >= 50). Check that the writers directory is accessible."
        )

    def test_migration_files_are_readable(self) -> None:
        """Migration scan must find at least 20 asset_ids."""
        migration_ids = collect_migration_insert_ids()
        assert len(migration_ids) >= 20, (
            f"Migration INSERT scan found only {len(migration_ids)} asset_ids "
            f"(expected >= 20). Check that the migrations directory is accessible."
        )
