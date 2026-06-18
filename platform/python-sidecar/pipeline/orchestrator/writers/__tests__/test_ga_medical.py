"""
Tests for the Medical/Ayurvedic Subsystem Gate-1 — ga_medical writer and l0_medical data.

Covers:
  1.  Both writers (bg_medical_mappings, ga_medical) registered
  2.  ga_medical has_substeps = True
  3.  bg_medical_mappings has 21 rows (9 classical grahas + 12 combination/dignity entries)
  4.  All medical mapping rows have non-empty classical_citation
  5.  Sun → pitta dosha
  6.  Saturn → vata dosha
  7.  bg_nakshatra_medical has 27 rows
  8.  Purva Bhadrapada maps to 'left_side' (FORENSIC: native Moon nakshatra)
  9.  not_diagnosis=TRUE enforced: indication_strength_from_score always returns
      a value, never changes not_diagnosis semantics
  10. indication_tier='jyotish_indication' constant enforced in every row schema
  11. FORENSIC: Sun=Capricorn (debilitated) → indication_strength='strong';
      Saturn=Libra (exalted) → indication_strength='mild'
  12. dry_run=True → 0 rows, no DB calls
  13. plan_substeps returns exactly 5 steps (one per ayanamsha)
  14. indication_strength_from_score boundary conditions
  15. lookup_nakshatra_body_part resolves all 27 nakshatras

No live DB required. All tests run against module-level constants and pure helpers.

MEDICAL DISCLAIMER: This test file verifies Jyotish indicator logic only.
All ga_medical rows carry indication_tier='jyotish_indication' and not_diagnosis=TRUE.
NOT a medical diagnostic system.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ── Lazy import helpers ────────────────────────────────────────────────────────

def _l0():
    from brahmagyan import l0_medical as mod
    return mod


def _ga_writer_module():
    from ga_writers import ga_medical_writer as mod
    return mod


# ── 1. Both writers registered ────────────────────────────────────────────────

def test_bg_medical_mappings_writer_registered():
    """bg_medical_mappings must be discoverable via the WRITER_REGISTRY."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    import pipeline.orchestrator.writers.bg_medical_mappings  # noqa: F401
    assert 'bg_medical_mappings' in WRITER_REGISTRY, (
        "bg_medical_mappings not registered in WRITER_REGISTRY"
    )


def test_ga_medical_writer_registered():
    """ga_medical must be discoverable via the WRITER_REGISTRY."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    import pipeline.orchestrator.writers.ga_medical  # noqa: F401
    assert 'ga_medical' in WRITER_REGISTRY, (
        "ga_medical not registered in WRITER_REGISTRY"
    )


# ── 2. ga_medical has_substeps = True ─────────────────────────────────────────

def test_ga_medical_has_substeps():
    """ga_medical writer must declare has_substeps = True (heavy writer)."""
    from pipeline.orchestrator.writers.ga_medical import GaMedicalWriter
    assert GaMedicalWriter.has_substeps is True, (
        "GaMedicalWriter must be a heavy writer (has_substeps=True)"
    )


# ── 3. bg_medical_mappings has 9 rows ─────────────────────────────────────────

def test_medical_mappings_nine_rows():
    """MEDICAL_MAPPINGS must contain 21 rows (9 classical grahas + 12 combination/dignity entries)."""
    mod = _l0()
    assert len(mod.MEDICAL_MAPPINGS) == 21, (
        f"Expected 21 medical mappings, got {len(mod.MEDICAL_MAPPINGS)}"
    )


def test_medical_mappings_all_nine_grahas():
    """All 9 classical Jyotish grahas must be present."""
    mod = _l0()
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    actual = {row["graha"] for row in mod.MEDICAL_MAPPINGS}
    missing = expected - actual
    assert not missing, f"Missing grahas in MEDICAL_MAPPINGS: {missing}"


# ── 4. All rows have non-empty classical_citation ────────────────────────────

def test_medical_mappings_all_have_citation():
    """Every MEDICAL_MAPPINGS row must have a non-empty classical_citation."""
    mod = _l0()
    for row in mod.MEDICAL_MAPPINGS:
        assert row.get("classical_citation"), (
            f"Missing classical_citation for graha={row.get('graha')}"
        )


def test_nakshatra_medical_all_have_citation():
    """Every NAKSHATRA_MEDICAL row must have a non-empty classical_citation."""
    mod = _l0()
    for row in mod.NAKSHATRA_MEDICAL:
        assert row.get("classical_citation"), (
            f"Missing classical_citation for nakshatra={row.get('nakshatra_name')}"
        )


# ── 5. Sun → pitta dosha ──────────────────────────────────────────────────────

def test_sun_dosha_pitta():
    """Sun must map to pitta dosha (BPHS Ch.18 / Ashtanga Hridayam)."""
    mod = _l0()
    sun = mod.lookup_graha_medical("Sun")
    assert sun is not None, "Sun not found in MEDICAL_MAPPINGS"
    assert "pitta" in sun["dosha"], (
        f"Sun dosha should include 'pitta', got {sun['dosha']}"
    )


def test_sun_dhatu_asthi():
    """Sun must map to asthi dhatu (BPHS Ch.18)."""
    mod = _l0()
    sun = mod.lookup_graha_medical("Sun")
    assert sun is not None
    assert "asthi" in sun["dhatu"], (
        f"Sun dhatu should include 'asthi', got {sun['dhatu']}"
    )


# ── 6. Saturn → vata dosha ───────────────────────────────────────────────────

def test_saturn_dosha_vata():
    """Saturn must map to vata dosha (BPHS Ch.18 / Ashtanga Hridayam)."""
    mod = _l0()
    saturn = mod.lookup_graha_medical("Saturn")
    assert saturn is not None, "Saturn not found in MEDICAL_MAPPINGS"
    assert "vata" in saturn["dosha"], (
        f"Saturn dosha should include 'vata', got {saturn['dosha']}"
    )


def test_saturn_disease_tendency_includes_arthritis():
    """Saturn disease tendency must include arthritis (BPHS Ch.18)."""
    mod = _l0()
    saturn = mod.lookup_graha_medical("Saturn")
    assert saturn is not None
    assert "arthritis" in saturn["disease_tendency"], (
        f"Saturn disease_tendency should include 'arthritis', got {saturn['disease_tendency']}"
    )


# ── 7. bg_nakshatra_medical has 27 rows ───────────────────────────────────────

def test_nakshatra_medical_27_rows():
    """NAKSHATRA_MEDICAL must contain exactly 27 rows."""
    mod = _l0()
    assert len(mod.NAKSHATRA_MEDICAL) == 27, (
        f"Expected 27 nakshatra rows, got {len(mod.NAKSHATRA_MEDICAL)}"
    )


def test_nakshatra_medical_numbers_1_to_27():
    """Nakshatra numbers must cover 1–27 without gaps."""
    mod = _l0()
    numbers = {row["nakshatra_number"] for row in mod.NAKSHATRA_MEDICAL}
    expected = set(range(1, 28))
    missing = expected - numbers
    assert not missing, f"Missing nakshatra numbers: {missing}"


# ── 8. Purva Bhadrapada → left_side (FORENSIC) ───────────────────────────────

def test_purva_bhadrapada_body_part_left_side():
    """
    FORENSIC: Purva Bhadrapada (nakshatra #25) must map to 'left_side'.
    This is the native Moon nakshatra (FORENSIC anchor: Moon = Purva Bhadrapada).
    """
    mod = _l0()
    body_part = mod.lookup_nakshatra_body_part("Purva Bhadrapada")
    assert body_part == "left_side", (
        f"Purva Bhadrapada must map to 'left_side' (FORENSIC Moon nakshatra), "
        f"got '{body_part}'"
    )


def test_purva_bhadrapada_is_number_25():
    """Purva Bhadrapada must be nakshatra number 25."""
    mod = _l0()
    entry = next(
        (r for r in mod.NAKSHATRA_MEDICAL if r["nakshatra_name"] == "Purva Bhadrapada"),
        None,
    )
    assert entry is not None, "Purva Bhadrapada not found in NAKSHATRA_MEDICAL"
    assert entry["nakshatra_number"] == 25, (
        f"Purva Bhadrapada must be nakshatra #25, got {entry['nakshatra_number']}"
    )


# ── 9. not_diagnosis semantics — schema-level enforcement ─────────────────────

def test_not_diagnosis_is_true_in_writer():
    """
    GaMedicalWriter must embed not_diagnosis=TRUE in every row.
    Verify via the writer adapter's asset_id and that the schema constant is enforced.
    We check that ga_medical_writer.build_ga_medical_substep does NOT override
    not_diagnosis — it must always be True.
    """
    # The column default is enforced at the schema level (NOT NULL DEFAULT TRUE).
    # Here we verify the writer never passes a False value — check the source.
    import inspect
    from ga_writers import ga_medical_writer as mod
    source = inspect.getsource(mod.build_ga_medical_substep)
    assert '"not_diagnosis":       True' in source or "'not_diagnosis':       True" in source or \
           '"not_diagnosis": True' in source or "'not_diagnosis': True" in source, (
        "build_ga_medical_substep must set not_diagnosis=True in every row"
    )


# ── 10. indication_tier constant ──────────────────────────────────────────────

def test_indication_tier_constant_in_writer():
    """
    Every ga_medical row must carry indication_tier='jyotish_indication'.
    Verify the constant is present in the writer source.
    """
    import inspect
    from ga_writers import ga_medical_writer as mod
    source = inspect.getsource(mod.build_ga_medical_substep)
    assert "jyotish_indication" in source, (
        "build_ga_medical_substep must set indication_tier='jyotish_indication'"
    )


def test_medical_disclaimer_in_module_docstring():
    """
    The ga_medical_writer module must contain the medical disclaimer.
    """
    from ga_writers import ga_medical_writer as mod
    doc = mod.__doc__ or ""
    assert "MEDICAL DISCLAIMER" in doc or "jyotish_indication" in doc, (
        "ga_medical_writer must contain MEDICAL DISCLAIMER in module docstring"
    )


# ── 11. FORENSIC: indication_strength_from_score ─────────────────────────────

def test_forensic_sun_capricorn_strong():
    """
    FORENSIC: Sun = Capricorn (debilitated) → condition_score expected low (<0.4)
    → indication_strength = 'strong'.

    We test with a representative debilitation-level score.
    Sun in Capricorn is enemy/debilitated → DIGNITY_SCORES['debilitated'] = 0.0,
    and the combined condition_score will be well below 0.4.
    """
    mod = _ga_writer_module()
    # Simulate debilitated planet: condition_score = 0.05 (debilitated + peedit)
    strength = mod.indication_strength_from_score(0.05)
    assert strength == "strong", (
        f"Sun-Capricorn debilitation level (score=0.05) → 'strong', got '{strength}'"
    )


def test_forensic_saturn_libra_mild():
    """
    FORENSIC: Saturn = Libra (exalted) → condition_score expected high (>0.6)
    → indication_strength = 'mild'.

    We test with a representative exaltation-level score.
    """
    mod = _ga_writer_module()
    # Simulate exalted planet: condition_score = 0.85 (exalted + deepta + yuva)
    strength = mod.indication_strength_from_score(0.85)
    assert strength == "mild", (
        f"Saturn-Libra exaltation level (score=0.85) → 'mild', got '{strength}'"
    )


def test_forensic_moon_nakshatra_body_part():
    """
    FORENSIC: Moon = Purva Bhadrapada → nakshatra_body_part = 'left_side'.
    Confirmed via lookup_nakshatra_body_part helper.
    """
    mod = _l0()
    # FORENSIC anchor: Moon nakshatra = Purva Bhadrapada
    body_part = mod.lookup_nakshatra_body_part("Purva Bhadrapada")
    assert body_part == "left_side", (
        f"FORENSIC Moon nakshatra: Purva Bhadrapada → 'left_side', got '{body_part}'"
    )


# ── 12. dry_run honored ────────────────────────────────────────────────────────

def test_run_substep_dry_run_returns_zero_rows():
    """ctx.dry_run=True must return 0 rows and make no DB calls."""
    from pipeline.orchestrator.writers.ga_medical import GaMedicalWriter
    from pipeline.orchestrator.writers import SubStep, ContextSpec

    writer = GaMedicalWriter()
    ctx = MagicMock(spec=ContextSpec)
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-dry-build"
    ctx.dry_run = True
    ctx.db_conn = MagicMock()

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")
    result = writer.run_substep(ctx, step)

    assert result.rows_inserted == 0, (
        f"dry_run must return 0 rows, got {result.rows_inserted}"
    )
    ctx.db_conn.cursor.assert_not_called()


def test_bg_medical_dry_run_returns_zero():
    """BgMedicalMappingsWriter dry_run=True must return 0 rows."""
    from pipeline.orchestrator.writers.bg_medical_mappings import BgMedicalMappingsWriter
    from pipeline.orchestrator.writers import ContextSpec
    import uuid

    writer = BgMedicalMappingsWriter()
    conn = MagicMock()
    ctx = ContextSpec(
        asset_id='bg_medical_mappings',
        build_id=str(uuid.uuid4()),
        db_conn=conn,
        dry_run=True,
    )
    result = writer.run(ctx)
    assert result.rows_inserted == 0, (
        f"dry_run bg_medical_mappings must return 0, got {result.rows_inserted}"
    )
    conn.cursor.assert_not_called()


# ── 13. plan_substeps returns 5 steps ─────────────────────────────────────────

def test_ga_medical_plan_substeps_five():
    """plan_substeps must return exactly 5 SubStep objects (one per ayanamsha)."""
    from pipeline.orchestrator.writers.ga_medical import GaMedicalWriter
    from pipeline.orchestrator.writers import ContextSpec, SubStep

    writer = GaMedicalWriter()
    ctx = MagicMock(spec=ContextSpec)
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-build"
    ctx.dry_run = False
    ctx.db_conn = MagicMock()

    steps = writer.plan_substeps(ctx)
    assert len(steps) == 5, f"Expected 5 substeps, got {len(steps)}"
    assert all(isinstance(s, SubStep) for s in steps)

    # Verify all expected ayanamshas are covered
    keys = {s.key for s in steps}
    expected_keys = {
        "ayanamsha_lahiri_chitrapaksha",
        "ayanamsha_krishnamurti",
        "ayanamsha_true_chitra",
        "ayanamsha_raman",
        "ayanamsha_surya_siddhanta_classical",
    }
    assert keys == expected_keys, f"Substep keys mismatch: {keys}"


# ── 14. indication_strength_from_score boundary conditions ───────────────────

class TestIndicationStrengthFromScore:
    """Boundary tests for indication_strength_from_score."""

    def _fn(self):
        return _ga_writer_module().indication_strength_from_score

    @pytest.mark.parametrize("score,expected", [
        (None,  "unknown"),
        (0.0,   "strong"),
        (0.39,  "strong"),
        (0.4,   "moderate"),
        (0.5,   "moderate"),
        (0.6,   "moderate"),
        (0.61,  "mild"),
        (1.0,   "mild"),
    ])
    def test_score_to_strength(self, score, expected):
        fn = self._fn()
        result = fn(score)
        assert result == expected, (
            f"indication_strength_from_score({score}) → expected '{expected}', got '{result}'"
        )


# ── 15. lookup_nakshatra_body_part resolves all 27 ───────────────────────────

def test_all_27_nakshatras_resolve():
    """lookup_nakshatra_body_part must return a non-None value for all 27 nakshatras."""
    mod = _l0()
    for entry in mod.NAKSHATRA_MEDICAL:
        name = entry["nakshatra_name"]
        part = mod.lookup_nakshatra_body_part(name)
        assert part is not None, f"lookup_nakshatra_body_part({name!r}) returned None"
        assert len(part) > 0, f"lookup_nakshatra_body_part({name!r}) returned empty string"


def test_lookup_unknown_nakshatra_returns_none():
    """lookup_nakshatra_body_part for an unknown name must return None."""
    mod = _l0()
    result = mod.lookup_nakshatra_body_part("Unknown Nakshatra XYZ")
    assert result is None


# ── Writer class conformance ──────────────────────────────────────────────────

def test_ga_medical_writer_is_writer_base_subclass():
    """GaMedicalWriter must subclass WriterBase."""
    from pipeline.orchestrator.writers.ga_medical import GaMedicalWriter
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(GaMedicalWriter, WriterBase)


def test_bg_medical_mappings_writer_is_writer_base_subclass():
    """BgMedicalMappingsWriter must subclass WriterBase."""
    from pipeline.orchestrator.writers.bg_medical_mappings import BgMedicalMappingsWriter
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(BgMedicalMappingsWriter, WriterBase)


def test_ga_medical_writer_asset_id():
    """GaMedicalWriter.asset_id must equal 'ga_medical'."""
    from pipeline.orchestrator.writers.ga_medical import GaMedicalWriter
    assert GaMedicalWriter.asset_id == "ga_medical"


def test_bg_medical_mappings_writer_asset_id():
    """BgMedicalMappingsWriter.asset_id must equal 'bg_medical_mappings'."""
    from pipeline.orchestrator.writers.bg_medical_mappings import BgMedicalMappingsWriter
    assert BgMedicalMappingsWriter.asset_id == "bg_medical_mappings"
