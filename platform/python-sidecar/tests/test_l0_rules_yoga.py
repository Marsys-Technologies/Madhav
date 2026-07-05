"""
test_l0_rules_yoga.py — Unit tests for brahmagyan.l0_rules yoga-name detection
(JL-011 / BA Phase 2.5 J1: detect_yoga_reference + extract_rules_from_chunk wiring).

Tests:
    1. Bigram match: "<word> Yoga"/"<word> yoga" resolves to a slugged canonical_id.
    2. Tier-1 bare match: a ratified proper noun matches WITHOUT a trailing "Yoga".
    3. Tier-1 canonical_id overrides resolve to the real brahma_yoga_catalog id,
       not a naive slug (regression guard for the five corrected entries).
    4. Hard-exclusion word does NOT match bare (only "<word> Yoga" form counts).
    5. No match at all -> yoga_canonical_id None, not ambiguous.
    6. Collision (two candidates resolving to different canonical_ids in the
       same window) -> yoga_canonical_id NULL, ambiguous flag set, candidates
       logged.
    7. extract_rules_from_chunk populates yoga_canonical_id on a real yielded
       rule row when a yoga reference appears near the pattern match.
"""

from __future__ import annotations


def _get_module():
    from brahmagyan import l0_rules as mod
    return mod


class TestBigramMatch:
    def test_capitalized_word_yoga(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("This forms Dharma Yoga in the chart.")
        assert result["yoga_canonical_id"] == "dharma"
        assert result["yoga_ambiguous"] is False
        assert "Dharma Yoga" in result["yoga_match_surface"]

    def test_lowercase_word_yoga(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("this gives rise to a dharma yoga effect.")
        assert result["yoga_canonical_id"] == "dharma"
        assert result["yoga_ambiguous"] is False


class TestTier1BareMatch:
    def test_bare_gajakesari_no_trailing_yoga(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("The native has Gajakesari formed by Moon-Jupiter kendra.")
        assert result["yoga_canonical_id"] == "gajakesari"
        assert result["yoga_ambiguous"] is False

    def test_bare_ruchaka(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("Ruchaka is formed when Mars occupies its own sign in a kendra.")
        assert result["yoga_canonical_id"] == "ruchaka"


class TestCanonicalIdOverrides:
    """Regression guard: these five Tier-1 names have a catalog canonical_id
    that differs from the naive `_yoga_slug(name)` output. If someone
    "simplifies" TIER1_YOGA_NAMES back to a bare list without re-checking
    brahma_yoga_catalog, these assertions catch the silent FK-validation
    null-out regression."""

    def test_neechabhanga_maps_to_raja_yoga_id(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("Neechabhanga cancels the debilitation here.")
        assert result["yoga_canonical_id"] == "neecha_bhanga_raja_yoga"

    def test_kemadruma_maps_to_aristha_id(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("This chart shows Kemadruma with no supporting planets.")
        assert result["yoga_canonical_id"] == "kemadruma_aristha"

    def test_kala_sarpa_maps_to_yoga_suffixed_id(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("All planets are hemmed between Rahu and Ketu forming Kala Sarpa.")
        assert result["yoga_canonical_id"] == "kala_sarpa_yoga"

    def test_adhi_maps_to_adhi_yoga_id(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("Adhi is present with benefics in 6th, 7th, 8th from Moon.")
        assert result["yoga_canonical_id"] == "adhi_yoga"

    def test_mridanga_maps_to_mridanga_yoga_id(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("Mridanga arises from own-sign lords in kendras and trikonas.")
        assert result["yoga_canonical_id"] == "mridanga_yoga"


class TestHardExclusions:
    def test_raja_bare_does_not_match(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("This is a powerful raja in the tenth house.")
        assert result["yoga_canonical_id"] is None
        assert result["yoga_ambiguous"] is False

    def test_raja_yoga_bigram_does_match(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("This is a powerful Raja Yoga in the tenth house.")
        assert result["yoga_canonical_id"] == "raja"

    def test_sarpa_bare_does_not_match(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("The sarpa formation is not complete without Rahu.")
        assert result["yoga_canonical_id"] is None


class TestNoMatch:
    def test_plain_text_no_yoga_reference(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("Mars is exalted in Capricorn in the tenth house.")
        assert result["yoga_canonical_id"] is None
        assert result["yoga_ambiguous"] is False
        assert result["yoga_candidates"] == []


class TestCollisionAmbiguity:
    def test_kala_sarpa_yoga_collides_with_sarpa_bigram(self):
        mod = _get_module()
        # "Kala Sarpa" (Tier-1 -> kala_sarpa_yoga) vs "Sarpa Yoga" (bigram -> sarpa)
        # are two distinct canonical_ids in one window -> genuinely ambiguous.
        result = mod.detect_yoga_reference("This forms Kala Sarpa Yoga across the chart.")
        assert result["yoga_canonical_id"] is None
        assert result["yoga_ambiguous"] is True
        assert len(result["yoga_candidates"]) >= 2
        ids = {c["canonical_id"] for c in result["yoga_candidates"]}
        assert "kala_sarpa_yoga" in ids
        assert "sarpa" in ids


class TestExtractRulesWiring:
    """Confirms detect_yoga_reference is actually wired into
    extract_rules_from_chunk so yoga_canonical_id lands on real yielded rows,
    not just on the standalone detector function."""

    def test_yielded_rule_carries_yoga_canonical_id(self):
        mod = _get_module()
        chunk = {
            "id": "11111111-1111-1111-1111-111111111111",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.1",
            "content_en": (
                "Mars in the 10th house gives Ruchaka and confers great authority "
                "and command over others."
            ),
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        assert rows, "expected at least one extracted rule from a planet-in-house match"
        yoga_ids = {r.get("yoga_canonical_id") for r in rows}
        assert "ruchaka" in yoga_ids, f"expected 'ruchaka' among yielded yoga_canonical_ids, got {yoga_ids}"

    def test_yielded_rule_yoga_canonical_id_none_when_absent(self):
        mod = _get_module()
        chunk = {
            "id": "22222222-2222-2222-2222-222222222222",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.2",
            "content_en": "Mars in the 10th house gives great authority and command over others.",
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        assert rows
        for r in rows:
            assert r.get("yoga_canonical_id") is None
