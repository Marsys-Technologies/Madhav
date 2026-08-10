"""
Test W2.9 — Citation resolution catalog.

Acceptance criteria (VERIFIER will recheck independently):

  AC1. CITATION_CATALOG is non-empty and covers entries from all known citation
       sources (citations.py constants, primitives.py families, bg_transit_rules
       dynamic entries).

  AC2. All 14 constants in citations.__all__ are represented in the catalog
       (source='citations_py').

  AC3. Both primitives_py (cited families) and uncited_extension families are
       represented in the catalog.

  AC4. compute() with enabled=False returns modifier=1.0 and zero sentences
       (toggle-safe; does not raise).

  AC5. compute() modifier is always 1.0 regardless of context or enabled state
       (this mechanism annotates, never gates lambda).

  AC6. get_all_citations() returns the same non-empty dict as CITATION_CATALOG
       (the seeding contract entry point is wired to the real catalog).

Additional unit tests:
  - catalog entries have required shape keys
  - uncited_extension entries are keyed with '_uncited:' prefix (not citation strings)
  - db_inherited entries point to citations.py fallback constants
  - bg_transit_rules dynamic entries exist and are keyed '_bg_transit_*'
  - compute() with a mock context records event_class in sentences
  - compute() sentences include catalog size and status counts
  - no citations.py constant is silently absent from the catalog
  - I2 compliance: gochara_grammar.citations imported read-only, not modified
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import services.gochara_grammar.citations as _C
from services.gochara_v3.mechanisms.w29_citation_resolution import (
    CITATION_CATALOG,
    MECHANISM_ID,
    TOGGLE_KEY,
    MechanismResult,
    compute,
    get_all_citations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _citations_py_entries(catalog: dict) -> dict:
    return {k: v for k, v in catalog.items() if v.get("source") == "citations_py"}


def _primitives_py_entries(catalog: dict) -> dict:
    return {k: v for k, v in catalog.items() if v.get("source") == "primitives_py"}


def _uncited_entries(catalog: dict) -> dict:
    return {k: v for k, v in catalog.items() if v.get("status") == "uncited_extension"}


def _bg_transit_entries(catalog: dict) -> dict:
    return {k: v for k, v in catalog.items() if k.startswith("_bg_transit_")}


# ---------------------------------------------------------------------------
# AC1: catalog is non-empty, covers all three sources
# ---------------------------------------------------------------------------

class TestCatalogIsNonempty:
    def test_catalog_has_entries(self):
        """CITATION_CATALOG must have at least as many entries as citations.__all__."""
        assert len(CITATION_CATALOG) > 0

    def test_catalog_larger_than_citations_py_alone(self):
        """Catalog includes primitives.py + bg_transit entries beyond raw constants."""
        assert len(CITATION_CATALOG) > len(_C.__all__)

    def test_citations_py_source_present(self):
        """At least one entry has source='citations_py'."""
        assert any(v.get("source") == "citations_py" for v in CITATION_CATALOG.values())

    def test_primitives_py_source_present(self):
        """At least one entry has source='primitives_py'."""
        assert any(v.get("source") == "primitives_py" for v in CITATION_CATALOG.values())

    def test_bg_transit_rules_source_present(self):
        """At least one entry has source='bg_transit_rules' (dynamic DB source)."""
        assert any(v.get("source") == "bg_transit_rules" for v in CITATION_CATALOG.values())


# ---------------------------------------------------------------------------
# AC2: all 14 citations.__all__ constants are represented
# ---------------------------------------------------------------------------

class TestAllSourcesRepresented:
    def test_all_citations_py_constants_in_catalog(self):
        """Every constant in citations.__all__ must appear as a catalog key."""
        missing = []
        for name in _C.__all__:
            value = getattr(_C, name)
            if value not in CITATION_CATALOG:
                missing.append(name)
        assert missing == [], (
            f"citations.py constants not in CITATION_CATALOG: {missing}"
        )

    def test_citations_py_entries_have_constant_name(self):
        """Every citations_py entry must carry constant_name back to its Python name."""
        for key, entry in _citations_py_entries(CITATION_CATALOG).items():
            assert "constant_name" in entry, (
                f"citations_py entry {key!r} missing 'constant_name'"
            )
            assert entry["constant_name"] in _C.__all__, (
                f"constant_name {entry['constant_name']!r} not in citations.__all__"
            )

    def test_uncited_extension_entries_present(self):
        """Uncited-extension families (degree_contact, eclipse_degree, planetary_return)
        must be cataloged even though they have no citation string."""
        uncited = _uncited_entries(CITATION_CATALOG)
        assert len(uncited) >= 3, (
            f"Expected at least 3 uncited_extension entries, found {len(uncited)}"
        )

    def test_uncited_entries_keyed_by_primitive(self):
        """Uncited entries must be keyed '_uncited:<primitive_name>' (not citation strings)."""
        uncited = _uncited_entries(CITATION_CATALOG)
        for key in uncited:
            assert key.startswith("_uncited:"), (
                f"Uncited entry {key!r} does not start with '_uncited:'"
            )

    def test_db_inherited_entries_present(self):
        """db_inherited usage (gochara_vedha_pair, av_threshold_state) must be traceable.

        These primitives use citations.py constants as their DB-inherited fallbacks.
        Because the citation strings are the same as citations_py constants, they are
        MERGED into the existing citations_py entry rather than creating a separate key.
        The merge records 'db_inherited' in the entry's 'usage_sources' list.
        """
        db_inherited_visible = [
            (k, v) for k, v in CITATION_CATALOG.items()
            if "db_inherited" in v.get("usage_sources", [])
            or v.get("source") == "db_inherited"
        ]
        assert len(db_inherited_visible) >= 2, (
            f"Expected at least 2 entries with db_inherited usage_sources, "
            f"found {len(db_inherited_visible)}"
        )

    def test_bg_transit_dynamic_entries_keyed_correctly(self):
        """bg_transit_rules dynamic entries are keyed '_bg_transit_*'."""
        bt_entries = _bg_transit_entries(CITATION_CATALOG)
        assert len(bt_entries) >= 2, (
            f"Expected at least 2 _bg_transit_* entries, found {len(bt_entries)}"
        )
        for key in bt_entries:
            assert key.startswith("_bg_transit_"), key


# ---------------------------------------------------------------------------
# AC3: required catalog entry shape
# ---------------------------------------------------------------------------

class TestCatalogEntryShape:
    def test_all_entries_have_status(self):
        for key, entry in CITATION_CATALOG.items():
            assert "status" in entry, f"Entry {key!r} missing 'status'"

    def test_all_entries_have_source(self):
        for key, entry in CITATION_CATALOG.items():
            assert "source" in entry, f"Entry {key!r} missing 'source'"

    def test_all_entries_have_verse_refs(self):
        """verse_refs must be present (list, possibly empty) — Wave 5 populates it."""
        for key, entry in CITATION_CATALOG.items():
            assert "verse_refs" in entry, f"Entry {key!r} missing 'verse_refs'"
            assert isinstance(entry["verse_refs"], list), (
                f"Entry {key!r} verse_refs must be a list"
            )

    def test_all_entries_have_note(self):
        for key, entry in CITATION_CATALOG.items():
            assert "note" in entry, f"Entry {key!r} missing 'note'"
            assert entry["note"], f"Entry {key!r} has empty 'note'"

    def test_status_values_are_known(self):
        known_statuses = {"resolved", "unresolved", "uncited_extension"}
        for key, entry in CITATION_CATALOG.items():
            assert entry["status"] in known_statuses, (
                f"Entry {key!r} has unknown status {entry['status']!r}"
            )

    def test_baseline_verse_refs_are_empty(self):
        """At baseline (no Wave 5 seeding), all verse_refs must be empty lists."""
        for key, entry in CITATION_CATALOG.items():
            assert entry["verse_refs"] == [], (
                f"Entry {key!r} has non-empty verse_refs at baseline: {entry['verse_refs']}"
            )


# ---------------------------------------------------------------------------
# AC4 / AC5: compute() — disabled path returns no sentences, modifier=1.0
# ---------------------------------------------------------------------------

class TestDisabledReturnsNoSentences:
    def test_disabled_sentences_empty(self):
        result = compute(None, 0.0, enabled=False)
        assert isinstance(result, MechanismResult)
        assert result.sentences == []

    def test_disabled_modifier_is_unit(self):
        result = compute(None, 0.0, enabled=False)
        assert result.modifier == 1.0

    def test_disabled_mechanism_id(self):
        result = compute(None, 0.0, enabled=False)
        assert result.mechanism_id == MECHANISM_ID

    def test_disabled_detail_records_enabled_false(self):
        result = compute(None, 0.0, enabled=False)
        assert result.detail.get("enabled") is False


# ---------------------------------------------------------------------------
# AC5: modifier always 1.0 (both enabled and disabled)
# ---------------------------------------------------------------------------

class TestModifierAlwaysUnit:
    def test_enabled_modifier_is_unit(self):
        result = compute(None, 0.0, enabled=True)
        assert result.modifier == 1.0

    def test_disabled_modifier_is_unit(self):
        result = compute(None, 0.0, enabled=False)
        assert result.modifier == 1.0

    def test_modifier_with_mock_context(self):
        ctx = MagicMock()
        ctx.event_class = "marriage"
        result = compute(ctx, 12345.0, enabled=True)
        assert result.modifier == 1.0


# ---------------------------------------------------------------------------
# AC6: get_all_citations() returns the catalog
# ---------------------------------------------------------------------------

class TestGetAllCitationsReturnsDict:
    def test_returns_nonempty_dict(self):
        result = get_all_citations()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_is_same_object_as_catalog(self):
        """get_all_citations() must return the same CITATION_CATALOG dict."""
        assert get_all_citations() is CITATION_CATALOG

    def test_contains_citations_py_entries(self):
        result = get_all_citations()
        citations_py = {k: v for k, v in result.items() if v.get("source") == "citations_py"}
        assert len(citations_py) == len(_C.__all__), (
            f"Expected {len(_C.__all__)} citations_py entries, "
            f"found {len(citations_py)}"
        )


# ---------------------------------------------------------------------------
# Additional: compute() enabled path — sentences and detail
# ---------------------------------------------------------------------------

class TestComputeEnabledSentences:
    def test_produces_at_least_one_sentence(self):
        result = compute(None, 0.0, enabled=True)
        assert len(result.sentences) >= 1

    def test_sentence_has_mechanism_id(self):
        result = compute(None, 0.0, enabled=True)
        for sentence in result.sentences:
            assert sentence["mechanism_id"] == MECHANISM_ID

    def test_sentence_has_total_catalog_entries(self):
        result = compute(None, 0.0, enabled=True)
        summary = result.sentences[0]
        assert summary["total_catalog_entries"] == len(CITATION_CATALOG)

    def test_sentence_status_counts_match_catalog(self):
        result = compute(None, 0.0, enabled=True)
        summary = result.sentences[0]
        total_from_counts = (
            summary["resolved_count"]
            + summary["unresolved_count"]
            + summary["uncited_extension_count"]
        )
        assert total_from_counts == len(CITATION_CATALOG)

    def test_sentence_records_event_class_from_context(self):
        ctx = MagicMock()
        ctx.event_class = "career_advancement"
        result = compute(ctx, 0.0, enabled=True)
        assert result.sentences[0]["event_class"] == "career_advancement"

    def test_detail_has_catalog_size(self):
        result = compute(None, 0.0, enabled=True)
        assert result.detail.get("catalog_size") == len(CITATION_CATALOG)

    def test_detail_has_status_counts(self):
        result = compute(None, 0.0, enabled=True)
        assert "status_counts" in result.detail
        assert isinstance(result.detail["status_counts"], dict)

    def test_detail_has_source_counts(self):
        result = compute(None, 0.0, enabled=True)
        assert "source_counts" in result.detail

    def test_no_db_access(self):
        """compute() must be callable with context=None and t_jd=0.0 without any DB."""
        # If this raises any DB-related exception, the fixture-only constraint is violated.
        result = compute(None, 0.0, enabled=True)
        assert isinstance(result, MechanismResult)


# ---------------------------------------------------------------------------
# I2 compliance
# ---------------------------------------------------------------------------

class TestI2NoV1ModulesEdited:
    def test_citations_module_constants_unchanged(self):
        """Verify citations.py constants are not mutated by importing this mechanism.

        I2: gochara_grammar.citations is imported READ-ONLY. We spot-check
        that GOCHARA_PHALA_BPHS_29 still has its canonical value after the
        mechanism module has been imported and the catalog built.
        """
        expected = "BPHS Ch.29 — Gochara Phala (transit results)"
        assert _C.GOCHARA_PHALA_BPHS_29 == expected, (
            "citations.GOCHARA_PHALA_BPHS_29 was mutated — I2 violation"
        )

    def test_citations_all_count_unchanged(self):
        """citations.__all__ must still have 14 entries (not grown/shrunk by import)."""
        assert len(_C.__all__) == 14, (
            f"citations.__all__ has {len(_C.__all__)} entries; expected 14"
        )

    def test_toggle_key_matches_mechanism_id(self):
        assert TOGGLE_KEY == MECHANISM_ID
