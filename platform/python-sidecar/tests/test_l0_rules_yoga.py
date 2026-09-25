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

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


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


class TestNadiTripleDeterminism:
    def test_planet_order_is_canonical_across_python_hash_seeds(self):
        script = (
            "import json; from brahmagyan import l0_rules as m; "
            "text='Mars, Ketu and Venus in Cancer. So, the native will take up a job'; "
            "match=m._P27.search(text); "
            "print(json.dumps([a['planet'] for a in m._p27_extract(match,text)['antecedent']]))"
        )
        observed = []
        for seed in ("0", "3"):
            env = {**os.environ, "PYTHONHASHSEED": seed}
            sidecar_root = str(Path(__file__).resolve().parents[1])
            env["PYTHONPATH"] = os.pathsep.join(
                path for path in (sidecar_root, env.get("PYTHONPATH")) if path
            )
            output = subprocess.check_output(
                [sys.executable, "-c", script],
                text=True,
                env=env,
            )
            observed.append(json.loads(output))

        assert observed == [["mars", "ketu"], ["mars", "ketu"]]


def test_seed_rules_propagates_insert_failure_instead_of_reporting_success(monkeypatch):
    """A failed PostgreSQL statement aborts the build; it is never skipped."""
    mod = _get_module()
    rule = {
        "rule_id": "11111111-1111-1111-1111-111111111111",
        "text_id": "bphs",
        "verse_ref": "BPHS 1.1",
        "antecedent_jsonb": "{}",
        "predicate_jsonb": "{}",
        "prediction_jsonb": "{}",
        "confidence": "two_pass_verified",
        "extracted_by": mod.EXTRACTED_BY,
        "extraction_pass_log": "{}",
        "quality_score": 1.0,
        "yoga_canonical_id": None,
        "dasha_system_id": None,
        "transit_marker": False,
        "_quality": 1.0,
    }
    monkeypatch.setattr(mod, "extract_rules_from_chunk", lambda *_a, **_k: iter([rule.copy()]))

    class Cursor:
        rowcount = 1

        def __init__(self):
            self.sql = ""
            self._chunks_returned = False

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def execute(self, sql, _params=None):
            self.sql = sql
            if "INSERT INTO sutravali_rules" in sql:
                raise RuntimeError("constraint violation")

        def fetchone(self):
            return {"count": 1}

        def fetchall(self):
            if "DISTINCT text_id" in self.sql:
                return [{"text_id": "bphs"}]
            if "brahma_dasha_systems" in self.sql:
                return [{"canonical_id": "vimshottari"}]
            if "brahma_yoga_catalog" in self.sql:
                return [{"canonical_id": "ruchaka"}]
            return []

        def fetchmany(self, _size):
            if self._chunks_returned:
                return []
            self._chunks_returned = True
            return [{
                "id": rule["rule_id"], "text_id": "bphs",
                "verse_ref": "BPHS 1.1", "content_en": "Mars gives authority",
            }]

    class Conn:
        def cursor(self):
            return Cursor()

    with pytest.raises(RuntimeError, match="constraint violation"):
        mod.seed_rules(Conn(), autocommit=False)


class TestWL03CitationParenSuppression:
    """W-L0-3: a parenthetical work-citation — "(Jataka Parijata, ch. 8)" —
    names a SOURCE TEXT, not a concept the rule qualifies. Matches inside a
    citation-marked paren (chapter/verse locator or digit) are suppressed;
    a bare parenthesized concept name like "(Sunapha)" stays eligible."""

    def test_tier1_name_inside_citation_paren_suppressed(self):
        mod = _get_module()
        result = mod.detect_yoga_reference(
            "The same result is stated elsewhere (Jataka Parijata, ch. 8)."
        )
        assert result["yoga_canonical_id"] is None
        assert result["yoga_ambiguous"] is False

    def test_tier1_name_inside_chapter_citation_paren_suppressed(self):
        mod = _get_module()
        result = mod.detect_yoga_reference("as given (Jataka Parijata, Ch. II) above")
        assert result["yoga_canonical_id"] is None

    def test_bigram_inside_citation_paren_suppressed(self):
        mod = _get_module()
        result = mod.detect_yoga_reference(
            "the results (Kusuma Yoga, ch. 3) are described here"
        )
        assert result["yoga_canonical_id"] is None

    def test_plain_paren_name_stays_eligible(self):
        mod = _get_module()
        result = mod.detect_yoga_reference(
            "(Sunapha) arises from the second house from the Moon."
        )
        assert result["yoga_canonical_id"] == "sunapha"


class TestWL03SentenceWindowTruncation:
    """W-L0-3: the detection window around a rule match is truncated at
    sentence boundaries ('. '), so a yoga named in a NEIGHBOURING sentence
    (chapter header, next verse) is no longer attributed to this rule."""

    def test_prior_sentence_yoga_not_attributed(self):
        mod = _get_module()
        chunk = {
            "id": "33333333-3333-3333-3333-333333333333",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.3",
            "content_en": (
                "Sunapha is described next. Mars in the 10th house gives "
                "great authority and command over others."
            ),
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        assert rows
        for r in rows:
            assert r.get("yoga_canonical_id") is None
            assert r.get("unlinked_reason") == "no_concept_reference_in_window"

    def test_next_sentence_yoga_not_attributed(self):
        mod = _get_module()
        chunk = {
            "id": "44444444-4444-4444-4444-444444444444",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.4",
            "content_en": (
                "Mars in the 10th house gives great authority and command "
                "over others. The next sloka explains Sunapha in detail."
            ),
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        assert rows
        for r in rows:
            assert r.get("yoga_canonical_id") is None
            assert r.get("unlinked_reason") == "no_concept_reference_in_window"


class TestWL03UnlinkedReason:
    """W-L0-3: every yielded rule carries unlinked_reason — NULL iff
    yoga_canonical_id is set, a reason string otherwise."""

    def test_no_reference_reason_emitted(self):
        mod = _get_module()
        chunk = {
            "id": "55555555-5555-5555-5555-555555555555",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.5",
            "content_en": "Mars in the 10th house gives great authority and command over others.",
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        assert rows
        for r in rows:
            assert r.get("yoga_canonical_id") is None
            assert r.get("unlinked_reason") == "no_concept_reference_in_window"

    def test_linked_reason_is_none(self):
        mod = _get_module()
        chunk = {
            "id": "66666666-6666-6666-6666-666666666666",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.6",
            "content_en": (
                "Mars in the 10th house gives Ruchaka and confers great "
                "authority and command over others."
            ),
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        linked = [r for r in rows if r.get("yoga_canonical_id") == "ruchaka"]
        assert linked, "expected at least one ruchaka-linked rule"
        for r in linked:
            assert r.get("unlinked_reason") is None

    def test_ambiguous_reference_reason(self):
        mod = _get_module()
        # "Kala Sarpa Yoga" collides: Tier-1 'Kala Sarpa' -> kala_sarpa_yoga
        # vs bigram 'Sarpa Yoga' -> sarpa, in the same sentence as the rule.
        chunk = {
            "id": "77777777-7777-7777-7777-777777777777",
            "text_id": "bphs",
            "verse_ref": "BPHS 1.7",
            "content_en": (
                "Mars in the 10th house forms Kala Sarpa Yoga and confers "
                "great authority and command over others."
            ),
        }
        rows = list(mod.extract_rules_from_chunk(chunk, valid_text_ids={"bphs"}))
        ambiguous = [r for r in rows if r.get("unlinked_reason") == "ambiguous_reference"]
        assert ambiguous, "expected at least one ambiguous_reference row"
        for r in ambiguous:
            assert r.get("yoga_canonical_id") is None


def test_seed_rules_labels_uncatalogued_yoga_reference(monkeypatch):
    """W-L0-3: a same-sentence yoga reference whose name is NOT in
    brahma_yoga_catalog is nulled by FK validation AND labelled
    'reference_not_in_catalog', so the NULL is distinguishable from
    'no_concept_reference_in_window'. The fixture rule row deliberately has
    no 'unlinked_reason' key — exercises the .get() default."""
    mod = _get_module()
    rule = {
        "rule_id": "11111111-1111-1111-1111-111111111111",
        "text_id": "bphs",
        "verse_ref": "BPHS 1.1",
        "antecedent_jsonb": "{}",
        "predicate_jsonb": "{}",
        "prediction_jsonb": "{}",
        "confidence": "two_pass_verified",
        "extracted_by": mod.EXTRACTED_BY,
        "extraction_pass_log": "{}",
        "quality_score": 1.0,
        "yoga_canonical_id": "uncatalogued_yoga",
        "dasha_system_id": None,
        "transit_marker": False,
        "_quality": 1.0,
    }
    monkeypatch.setattr(mod, "extract_rules_from_chunk", lambda *_a, **_k: iter([rule.copy()]))

    captured: dict = {}

    class Cursor:
        rowcount = 1

        def __init__(self):
            self.sql = ""
            self._chunks_returned = False

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def execute(self, sql, params=None):
            self.sql = sql
            if "INSERT INTO sutravali_rules" in sql:
                captured["params"] = params

        def fetchone(self):
            return {"count": 1}

        def fetchall(self):
            if "DISTINCT text_id" in self.sql:
                return [{"text_id": "bphs"}]
            if "brahma_dasha_systems" in self.sql:
                return [{"canonical_id": "vimshottari"}]
            if "brahma_yoga_catalog" in self.sql:
                return [{"canonical_id": "ruchaka"}]
            return []

        def fetchmany(self, _size):
            if self._chunks_returned:
                return []
            self._chunks_returned = True
            return [{
                "id": rule["rule_id"], "text_id": "bphs",
                "verse_ref": "BPHS 1.1", "content_en": "Mars gives authority",
            }]

    class Conn:
        def cursor(self):
            return Cursor()

    mod.seed_rules(Conn(), autocommit=False)

    params = captured["params"]
    # INSERT param order: ..., quality_score(9), yoga_canonical_id(10),
    # unlinked_reason(11), dasha_system_id(12), transit_marker(13), created_at(14)
    assert params[10] is None
    assert params[11] == "reference_not_in_catalog"
