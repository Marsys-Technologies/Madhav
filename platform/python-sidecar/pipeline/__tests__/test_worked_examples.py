"""
test_worked_examples.py — G28: Tests for classical worked-examples library.

Minimum 25 assertions covering:
  - Dataset completeness (≥15 entries)
  - Required key presence on every entry
  - Source-based lookup correctness
  - Yoga-based lookup correctness
  - list_all_examples() completeness
  - get_example() by ID
  - birth_data dict structure
  - classical_predictions list presence
  - Multi-source coverage
"""

import pytest
from pipeline.worked_examples import (
    WORKED_EXAMPLES,
    get_example,
    get_examples_by_source,
    get_examples_by_yoga,
    list_all_examples,
)

# ── Required keys that every entry must carry ──────────────────────────────
REQUIRED_KEYS = {
    "id",
    "name",
    "birth_data",
    "lagna",
    "notable_placements",
    "classical_predictions",
    "outcomes",
    "source",
    "yoga_demonstrated",
    "notes",
}

# ── BIRTH_DATA sub-keys ────────────────────────────────────────────────────
BIRTH_DATA_KEYS = {"year", "month", "day", "approximate", "note"}


# ==========================================================================
# 1. Dataset-size assertions
# ==========================================================================

class TestDatasetSize:
    def test_minimum_15_examples(self):
        """WORKED_EXAMPLES must contain at least 15 entries."""  # assertion 1
        assert len(WORKED_EXAMPLES) >= 15

    def test_all_examples_have_unique_ids(self):
        """Every entry must have a unique 'id' value."""  # assertion 2
        ids = [ex["id"] for ex in WORKED_EXAMPLES]
        assert len(ids) == len(set(ids))

    def test_list_all_examples_returns_full_list(self):
        """list_all_examples() must return all entries."""  # assertion 3
        assert len(list_all_examples()) == len(WORKED_EXAMPLES)

    def test_list_all_examples_returns_list_type(self):
        """list_all_examples() must return a list."""  # assertion 4
        assert isinstance(list_all_examples(), list)


# ==========================================================================
# 2. Required-key presence on every entry
# ==========================================================================

class TestRequiredKeys:
    @pytest.mark.parametrize("key", sorted(REQUIRED_KEYS))
    def test_every_entry_has_required_key(self, key):
        """Every entry must carry every required key."""  # assertion 5–14
        for ex in WORKED_EXAMPLES:
            assert key in ex, (
                f"Entry '{ex.get('id', '?')}' is missing required key '{key}'"
            )

    def test_ids_are_strings(self):
        """All IDs must be strings."""  # assertion 15
        for ex in WORKED_EXAMPLES:
            assert isinstance(ex["id"], str), f"id is not str in entry {ex}"

    def test_yoga_demonstrated_is_list(self):
        """yoga_demonstrated must be a list on every entry."""  # assertion 16
        for ex in WORKED_EXAMPLES:
            assert isinstance(ex["yoga_demonstrated"], list), (
                f"yoga_demonstrated not a list in entry '{ex['id']}'"
            )

    def test_yoga_demonstrated_nonempty(self):
        """yoga_demonstrated must be non-empty on every entry."""  # assertion 17
        for ex in WORKED_EXAMPLES:
            assert len(ex["yoga_demonstrated"]) > 0, (
                f"yoga_demonstrated is empty in entry '{ex['id']}'"
            )


# ==========================================================================
# 3. birth_data sub-structure
# ==========================================================================

class TestBirthData:
    def test_birth_data_is_dict(self):
        """birth_data must be a dict on every entry."""  # assertion 18
        for ex in WORKED_EXAMPLES:
            assert isinstance(ex["birth_data"], dict), (
                f"birth_data is not a dict in entry '{ex['id']}'"
            )

    def test_birth_data_has_required_keys(self):
        """birth_data must contain year, month, day, approximate, note."""  # assertion 19
        for ex in WORKED_EXAMPLES:
            missing = BIRTH_DATA_KEYS - ex["birth_data"].keys()
            assert not missing, (
                f"Entry '{ex['id']}' birth_data missing keys: {missing}"
            )

    def test_birth_data_approximate_is_bool(self):
        """birth_data.approximate must be a bool."""  # assertion 20
        for ex in WORKED_EXAMPLES:
            val = ex["birth_data"]["approximate"]
            assert isinstance(val, bool), (
                f"approximate is not bool in entry '{ex['id']}'"
            )


# ==========================================================================
# 4. classical_predictions structure
# ==========================================================================

class TestClassicalPredictions:
    def test_classical_predictions_is_list(self):
        """classical_predictions must be a list on every entry."""  # assertion 21
        for ex in WORKED_EXAMPLES:
            assert isinstance(ex["classical_predictions"], list), (
                f"classical_predictions not a list in entry '{ex['id']}'"
            )

    def test_classical_predictions_nonempty(self):
        """classical_predictions must be non-empty on every entry."""  # assertion 22
        for ex in WORKED_EXAMPLES:
            assert len(ex["classical_predictions"]) > 0, (
                f"classical_predictions is empty in entry '{ex['id']}'"
            )

    def test_each_prediction_has_text_key(self):
        """Each prediction dict must have a 'text' key."""  # assertion 23
        for ex in WORKED_EXAMPLES:
            for pred in ex["classical_predictions"]:
                assert "text" in pred, (
                    f"Prediction in entry '{ex['id']}' missing 'text' key"
                )

    def test_each_prediction_has_yoga_key(self):
        """Each prediction dict must have a 'yoga' key."""  # assertion 24
        for ex in WORKED_EXAMPLES:
            for pred in ex["classical_predictions"]:
                assert "yoga" in pred, (
                    f"Prediction in entry '{ex['id']}' missing 'yoga' key"
                )


# ==========================================================================
# 5. Source-based lookup
# ==========================================================================

class TestGetExamplesBySource:
    def test_bphs_returns_at_least_2(self):
        """get_examples_by_source('BPHS') must return ≥2 entries."""  # assertion 25
        results = get_examples_by_source("BPHS")
        assert len(results) >= 2

    def test_phaladeepika_returns_at_least_2(self):
        """get_examples_by_source('Phaladeepika') must return ≥2 entries."""  # assertion 26
        results = get_examples_by_source("Phaladeepika")
        assert len(results) >= 2

    def test_raman_300_returns_at_least_1(self):
        """get_examples_by_source('Raman_300') must return ≥1 entry."""  # assertion 27
        results = get_examples_by_source("Raman_300")
        assert len(results) >= 1

    def test_ks_charak_returns_at_least_1(self):
        """get_examples_by_source('KS_Charak') must return ≥1 entry."""  # assertion 28
        results = get_examples_by_source("KS_Charak")
        assert len(results) >= 1

    def test_source_lookup_returns_list(self):
        """get_examples_by_source must return a list."""  # assertion 29
        assert isinstance(get_examples_by_source("BPHS"), list)

    def test_unknown_source_returns_empty(self):
        """An unknown source must return an empty list."""  # assertion 30
        assert get_examples_by_source("UnknownText_XYZ") == []

    def test_source_case_insensitive(self):
        """Source lookup must be case-insensitive."""  # assertion 31
        lower = get_examples_by_source("bphs")
        upper = get_examples_by_source("BPHS")
        assert len(lower) == len(upper)


# ==========================================================================
# 6. Yoga-based lookup
# ==========================================================================

class TestGetExamplesByYoga:
    def test_gajakesari_returns_at_least_1(self):
        """get_examples_by_yoga('Gajakesari') must return ≥1 entry."""  # assertion 32
        results = get_examples_by_yoga("Gajakesari")
        assert len(results) >= 1

    def test_viparita_returns_at_least_1(self):
        """get_examples_by_yoga('Viparita') must return ≥1 entry."""  # assertion 33
        results = get_examples_by_yoga("Viparita")
        assert len(results) >= 1

    def test_hamsa_returns_at_least_1(self):
        """get_examples_by_yoga('Hamsa') must return ≥1 entry."""  # assertion 34
        results = get_examples_by_yoga("Hamsa")
        assert len(results) >= 1

    def test_mahapurusha_returns_multiple(self):
        """get_examples_by_yoga('Mahapurusha') should return multiple entries."""  # assertion 35
        results = get_examples_by_yoga("Mahapurusha")
        assert len(results) >= 3

    def test_yoga_lookup_returns_list(self):
        """get_examples_by_yoga must return a list."""  # assertion 36
        assert isinstance(get_examples_by_yoga("Gajakesari"), list)

    def test_unknown_yoga_returns_empty(self):
        """An unknown yoga must return an empty list."""  # assertion 37
        assert get_examples_by_yoga("CompletelyMadeUpYoga_ZZZ") == []

    def test_yoga_case_insensitive(self):
        """Yoga lookup must be case-insensitive."""  # assertion 38
        lower = get_examples_by_yoga("gajakesari")
        upper = get_examples_by_yoga("Gajakesari")
        assert len(lower) == len(upper)

    def test_kemadruma_returns_at_least_1(self):
        """get_examples_by_yoga('Kemadruma') must return ≥1 entry."""  # assertion 39
        results = get_examples_by_yoga("Kemadruma")
        assert len(results) >= 1

    def test_mangal_dosha_returns_at_least_1(self):
        """get_examples_by_yoga('Mangal') must return ≥1 entry."""  # assertion 40
        results = get_examples_by_yoga("Mangal")
        assert len(results) >= 1


# ==========================================================================
# 7. get_example by ID
# ==========================================================================

class TestGetExample:
    def test_known_id_returns_dict(self):
        """get_example with a known ID must return a dict."""  # assertion 41
        result = get_example("BPHS-001")
        assert isinstance(result, dict)

    def test_known_id_returns_correct_name(self):
        """get_example('BPHS-001') must return the Parashara entry."""  # assertion 42
        result = get_example("BPHS-001")
        assert result is not None
        assert "Parashara" in result["name"]

    def test_known_id_pd001_source_correct(self):
        """get_example('PD-001') must return source == 'Phaladeepika'."""  # assertion 43
        result = get_example("PD-001")
        assert result is not None
        assert result["source"] == "Phaladeepika"

    def test_known_id_raman001_lagna(self):
        """get_example('RAMAN-001') must return lagna == 'Gemini'."""  # assertion 44
        result = get_example("RAMAN-001")
        assert result is not None
        assert result["lagna"] == "Gemini"

    def test_unknown_id_returns_none(self):
        """get_example with an unknown ID must return None."""  # assertion 45
        result = get_example("NONEXISTENT-999")
        assert result is None

    def test_known_id_ksch001_yoga(self):
        """get_example('KSCH-001') must have Kemadruma in yoga_demonstrated."""  # assertion 46
        result = get_example("KSCH-001")
        assert result is not None
        assert any("Kemadruma" in y for y in result["yoga_demonstrated"])

    def test_known_id_anon004_source(self):
        """get_example('ANON-004') must return source 'KS_Charak'."""  # assertion 47
        result = get_example("ANON-004")
        assert result is not None
        assert result["source"] == "KS_Charak"


# ==========================================================================
# 8. Multi-source coverage
# ==========================================================================

class TestSourceCoverage:
    def test_at_least_4_distinct_sources(self):
        """Dataset must cover at least 4 distinct source texts."""  # assertion 48
        sources = {ex["source"] for ex in WORKED_EXAMPLES}
        assert len(sources) >= 4

    def test_dataset_has_brihat_jataka_or_uttara_kalam(self):
        """Dataset must include at least one entry from Brihat_Jataka or Uttara_Kalam."""  # assertion 49
        sources = {ex["source"] for ex in WORKED_EXAMPLES}
        assert sources & {"Brihat_Jataka", "Uttara_Kalam"}

    def test_outcomes_nonempty_on_all(self):
        """'outcomes' list must be non-empty on every entry."""  # assertion 50
        for ex in WORKED_EXAMPLES:
            assert len(ex.get("outcomes", [])) > 0, (
                f"outcomes is empty in entry '{ex['id']}'"
            )
