"""
test_lel_event_class_resolver.py — SAMPURTI L0f (G14a).

Unit tests for brahmagyan.lel_event_class_resolver.

Test strategy (per mission TDD requirement):
  1. Resolver unit tests per rule class (tier-1 exact, tier-2 keyword, tier-2 single-candidate).
  2. Coverage assertion: resolve_batch(64 rows) == 64 results.
  3. Unknown category → AMBIGUOUS, not a guess.
  4. NULL domain → no tier-1 match, falls through to tier-2.
  5. DOMAIN_TO_EVENT_CLASS keys all resolve to valid event_class_ids from EVENT_CLASSES.
  6. Every event_class produced by the resolver exists in EVENT_CLASSES.

No live DB access — all tests are pure/deterministic.
"""
from __future__ import annotations

import pytest

from brahmagyan.l0_ghatana import EVENT_CLASSES
from brahmagyan.lel_event_class_resolver import (
    CONFIDENCE_AMBIGUOUS,
    CONFIDENCE_EXACT,
    CONFIDENCE_KEYWORD,
    DOMAIN_TO_EVENT_CLASS,
    RESOLVER_VERSION,
    CoverageAssertionError,
    ResolutionResult,
    assert_coverage,
    resolve_batch,
    resolve_event_class,
)

# ── Ground-truth set of valid event_class_ids ─────────────────────────────────
VALID_EVENT_CLASS_IDS = {e["event_class_id"] for e in EVENT_CLASSES}


# ── 1. Resolver constants sanity ──────────────────────────────────────────────

def test_resolver_version_is_string():
    assert isinstance(RESOLVER_VERSION, str)
    assert RESOLVER_VERSION.startswith("l0f_")


# ── 2. Tier-1: domain exact match ─────────────────────────────────────────────

class TestTier1DomainExactMatch:
    """Tier-1: every key in DOMAIN_TO_EVENT_CLASS resolves EXACT."""

    def test_domain_table_values_are_all_valid_event_class_ids(self):
        invalid = {v for v in DOMAIN_TO_EVENT_CLASS.values()
                   if v not in VALID_EVENT_CLASS_IDS}
        assert not invalid, (
            f"DOMAIN_TO_EVENT_CLASS maps to unknown event_class_ids: {invalid}"
        )

    def test_birth_anchor(self):
        r = resolve_event_class("ev1", "other", "other/birth")
        assert r.event_class == "birth_anchor"
        assert r.confidence == CONFIDENCE_EXACT
        assert r.rule_matched == "tier1_domain_exact"
        assert r.resolved is True

    def test_career_first_job_joined(self):
        r = resolve_event_class("ev2", "career", "career/first_job_joined")
        assert r.event_class == "career_entry"
        assert r.confidence == CONFIDENCE_EXACT

    def test_family_marriage(self):
        r = resolve_event_class("ev3", "family", "family/marriage")
        assert r.event_class == "marriage"
        assert r.confidence == CONFIDENCE_EXACT

    def test_family_child_birth(self):
        r = resolve_event_class("ev4", "family", "family/child_birth")
        assert r.event_class == "childbirth"
        assert r.confidence == CONFIDENCE_EXACT

    def test_career_entrepreneurship_founded(self):
        r = resolve_event_class("ev5", "career", "career/entrepreneurship_founded")
        assert r.event_class == "business_launch"
        assert r.confidence == CONFIDENCE_EXACT

    def test_loss_grandparent_passing(self):
        r = resolve_event_class("ev6", "loss", "loss/grandparent_passing")
        assert r.event_class == "bereavement"
        assert r.confidence == CONFIDENCE_EXACT

    def test_loss_financial_deception(self):
        r = resolve_event_class("ev7", "loss", "loss/financial_deception")
        assert r.event_class == "financial_deception"
        assert r.confidence == CONFIDENCE_EXACT

    def test_finance_family_windfall(self):
        r = resolve_event_class("ev8", "finance", "finance/family_windfall")
        assert r.event_class == "major_gain"
        assert r.confidence == CONFIDENCE_EXACT

    def test_finance_business_milestone_windfall(self):
        r = resolve_event_class("ev9", "finance", "finance/business_milestone_windfall")
        assert r.event_class == "major_gain"
        assert r.confidence == CONFIDENCE_EXACT

    def test_health_surgery_minor(self):
        r = resolve_event_class("ev10", "health", "health/surgery_minor")
        assert r.event_class == "surgery"
        assert r.confidence == CONFIDENCE_EXACT

    def test_health_chronic_onset(self):
        r = resolve_event_class("ev11", "health", "health/chronic_onset")
        assert r.event_class == "chronic_onset"
        assert r.confidence == CONFIDENCE_EXACT

    def test_residential_travel_foreign_move_start(self):
        r = resolve_event_class("ev12", "residential+travel",
                                "residential+travel/foreign_move_start")
        assert r.event_class == "foreign_settlement"
        assert r.confidence == CONFIDENCE_EXACT

    def test_residential_travel_foreign_return(self):
        r = resolve_event_class("ev13", "residential+travel",
                                "residential+travel/foreign_return")
        assert r.event_class == "relocation"
        assert r.confidence == CONFIDENCE_EXACT

    def test_travel_first_foreign_trip(self):
        r = resolve_event_class("ev14", "travel", "travel/first_foreign_trip")
        assert r.event_class == "travel_event"
        assert r.confidence == CONFIDENCE_EXACT

    def test_spiritual_devata_adoption(self):
        r = resolve_event_class("ev15", "spiritual", "spiritual/devata_adoption")
        assert r.event_class == "spiritual_turn"
        assert r.confidence == CONFIDENCE_EXACT

    def test_psychological_speech_pattern_arc(self):
        r = resolve_event_class("ev16", "psychological",
                                "psychological/speech_pattern_arc")
        assert r.event_class == "psychological_arc"
        assert r.confidence == CONFIDENCE_EXACT

    def test_career_award_selection_maps_to_achievement_recognition(self):
        r = resolve_event_class("ev17", "career", "career/award_selection")
        assert r.event_class == "achievement_recognition"
        assert r.confidence == CONFIDENCE_EXACT

    def test_education_leadership_role_maps_to_achievement_recognition(self):
        r = resolve_event_class("ev18", "education", "education/leadership_role")
        assert r.event_class == "achievement_recognition"
        assert r.confidence == CONFIDENCE_EXACT

    def test_all_domain_table_keys_resolve_exact(self):
        """Every entry in DOMAIN_TO_EVENT_CLASS resolves EXACT."""
        for domain_val, expected_class in DOMAIN_TO_EVENT_CLASS.items():
            # infer a plausible category from the domain prefix
            category = domain_val.split("/")[0]
            r = resolve_event_class(f"_test_{domain_val}", category, domain_val)
            assert r.confidence == CONFIDENCE_EXACT, (
                f"domain={domain_val!r} expected EXACT, got {r.confidence!r}"
            )
            assert r.event_class == expected_class, (
                f"domain={domain_val!r}: expected {expected_class!r}, "
                f"got {r.event_class!r}"
            )


# ── 3. Tier-2: single-candidate categories ────────────────────────────────────

class TestTier2SingleCandidate:
    """Categories with exactly one possible event class resolve KEYWORD."""

    def test_spiritual_category_no_domain(self):
        # 'spiritual' → only spiritual_turn candidate
        r = resolve_event_class("ev20", "spiritual", None)
        assert r.event_class == "spiritual_turn"
        assert r.confidence == CONFIDENCE_KEYWORD
        assert r.rule_matched == "tier2_single_candidate"

    def test_psychological_category_no_domain(self):
        # 'psychological' → only psychological_arc candidate
        r = resolve_event_class("ev21", "psychological", None)
        assert r.event_class == "psychological_arc"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_creative_category_no_domain(self):
        # 'creative' → only achievement_recognition candidate
        r = resolve_event_class("ev22", "creative", None)
        assert r.event_class == "achievement_recognition"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_travel_event_category_no_domain(self):
        # 'travel_event' → only travel_event candidate
        r = resolve_event_class("ev23", "travel_event", None)
        assert r.event_class == "travel_event"
        assert r.confidence == CONFIDENCE_KEYWORD


# ── 4. Tier-2: keyword disambiguation ─────────────────────────────────────────

class TestTier2KeywordDisambiguation:
    """Keyword rules disambiguate within a multi-candidate category."""

    def test_career_founded_keyword(self):
        r = resolve_event_class("ev30", "career", "career/company_founded_misc")
        assert r.event_class == "business_launch"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_career_switch_keyword(self):
        r = resolve_event_class("ev31", "career", "career/job_switch_misc")
        assert r.event_class == "career_change"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_career_crash_keyword(self):
        r = resolve_event_class("ev32", "career", "career/company_crash")
        assert r.event_class == "career_setback"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_health_surgery_keyword(self):
        r = resolve_event_class("ev33", "health", "health/operation_misc")
        assert r.event_class == "surgery"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_health_chronic_keyword(self):
        r = resolve_event_class("ev34", "health", "health/chronic_condition")
        assert r.event_class == "chronic_onset"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_education_exam_keyword(self):
        r = resolve_event_class("ev35", "education", "education/iit_exam_attempt")
        assert r.event_class == "exam_outcome"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_loss_passing_keyword(self):
        r = resolve_event_class("ev36", "loss", "loss/relative_passing")
        assert r.event_class == "bereavement"
        assert r.confidence == CONFIDENCE_KEYWORD

    def test_loss_fraud_keyword(self):
        r = resolve_event_class("ev37", "loss", "loss/fraud_scam")
        assert r.event_class == "financial_deception"
        assert r.confidence == CONFIDENCE_KEYWORD


# ── 5. Unknown category → AMBIGUOUS, not a guess ─────────────────────────────

class TestUnknownCategoryIsAmbiguous:
    """Unknown categories must yield AMBIGUOUS, never a guess (per mission spec)."""

    def test_unknown_category_no_domain(self):
        r = resolve_event_class("ev40", "unknown_cat", None)
        assert r.confidence == CONFIDENCE_AMBIGUOUS
        assert r.event_class is None
        assert r.resolved is False

    def test_unknown_category_with_domain(self):
        r = resolve_event_class("ev41", "zzz_invented", "zzz_invented/something")
        assert r.confidence == CONFIDENCE_AMBIGUOUS
        assert r.event_class is None

    def test_empty_category_is_ambiguous(self):
        r = resolve_event_class("ev42", "", None)
        assert r.confidence == CONFIDENCE_AMBIGUOUS
        assert r.event_class is None


# ── 6. NULL domain falls through to tier-2 ───────────────────────────────────

class TestNullDomainFallthrough:
    def test_null_domain_career_ambiguous(self):
        # 'career' has 5 candidates and no keywords from a null domain
        r = resolve_event_class("ev50", "career", None)
        assert r.confidence == CONFIDENCE_AMBIGUOUS
        assert r.event_class is None
        assert len(r.candidates) > 1

    def test_null_domain_loss_ambiguous(self):
        # 'loss' has 3 candidates, null domain → ambiguous
        r = resolve_event_class("ev51", "loss", None)
        assert r.confidence == CONFIDENCE_AMBIGUOUS
        assert r.event_class is None

    def test_null_domain_spiritual_single_candidate(self):
        # 'spiritual' has 1 candidate → resolves even without domain
        r = resolve_event_class("ev52", "spiritual", None)
        assert r.event_class == "spiritual_turn"
        assert r.confidence == CONFIDENCE_KEYWORD


# ── 7. audit_trail structure ──────────────────────────────────────────────────

class TestAuditTrail:
    def test_exact_audit_trail_keys(self):
        r = resolve_event_class("ev60", "other", "other/birth")
        at = r.audit_trail
        assert "resolver_version" in at
        assert "confidence" in at
        assert "rule_matched" in at
        assert "matched_tokens" in at
        assert "candidates" in at
        assert "domain_input" in at
        assert "category_input" in at

    def test_ambiguous_candidates_non_empty(self):
        r = resolve_event_class("ev61", "career", None)
        assert r.audit_trail["candidates"]  # non-empty list

    def test_resolver_version_in_audit(self):
        r = resolve_event_class("ev62", "other", "other/birth")
        assert r.audit_trail["resolver_version"] == RESOLVER_VERSION


# ── 8. Output event classes exist in brahma_event_ontology ───────────────────

class TestOutputClassesExistInOntology:
    def test_all_resolved_classes_are_valid(self):
        """Every event_class produced by the resolver is a known class."""
        for domain_val, expected_class in DOMAIN_TO_EVENT_CLASS.items():
            assert expected_class in VALID_EVENT_CLASS_IDS, (
                f"DOMAIN_TO_EVENT_CLASS[{domain_val!r}] = {expected_class!r} "
                f"is NOT in EVENT_CLASSES"
            )


# ── 9. Coverage assertion ─────────────────────────────────────────────────────

class TestCoverageAssertion:
    def test_assert_coverage_passes_matching_counts(self):
        rows = [{"event_id": "a", "category": "other", "domain": "other/birth"}]
        results = resolve_batch(rows)
        assert_coverage(rows, results)  # must not raise

    def test_assert_coverage_raises_on_count_mismatch(self):
        rows = [{"event_id": "a", "category": "other", "domain": "other/birth"},
                {"event_id": "b", "category": "other", "domain": "other/birth"}]
        # Fake a result with only one entry
        fake_results = [resolve_event_class("a", "other", "other/birth")]
        with pytest.raises(CoverageAssertionError):
            assert_coverage(rows, fake_results)

    def test_assert_coverage_raises_on_missing_event_id(self):
        rows = [{"event_id": "a", "category": "other", "domain": "other/birth"}]
        fake_results = [
            ResolutionResult(
                event_id="WRONG_ID",
                category="other",
                domain="other/birth",
                event_class="birth_anchor",
                confidence=CONFIDENCE_EXACT,
                rule_matched="tier1_domain_exact",
                matched_tokens="other/birth",
            )
        ]
        with pytest.raises(CoverageAssertionError):
            assert_coverage(rows, fake_results)


# ── 10. resolve_batch: exactly N results for N inputs ────────────────────────

class TestResolveBatch:
    def test_batch_same_length_as_input(self):
        rows = [
            {"event_id": "x1", "category": "other", "domain": "other/birth"},
            {"event_id": "x2", "category": "career", "domain": "career/first_job_joined"},
            {"event_id": "x3", "category": "spiritual", "domain": None},
        ]
        results = resolve_batch(rows)
        assert len(results) == 3

    def test_batch_order_preserved(self):
        rows = [
            {"event_id": "z1", "category": "other", "domain": "other/birth"},
            {"event_id": "z2", "category": "loss", "domain": "loss/parent_passing"},
        ]
        results = resolve_batch(rows)
        assert results[0].event_id == "z1"
        assert results[1].event_id == "z2"

    def test_batch_with_ambiguous_rows_does_not_raise(self):
        rows = [
            {"event_id": "a1", "category": "career", "domain": None},  # AMBIGUOUS
            {"event_id": "a2", "category": "other", "domain": "other/birth"},  # EXACT
        ]
        results = resolve_batch(rows)
        assert len(results) == 2
        ambig = next(r for r in results if r.event_id == "a1")
        exact = next(r for r in results if r.event_id == "a2")
        assert ambig.confidence == CONFIDENCE_AMBIGUOUS
        assert exact.confidence == CONFIDENCE_EXACT


# ── 11. The canonical chart's 64 rows — coverage and classification count ─────
#
# This test encodes the expected classification outcome for the 64 canonical
# life_events rows. It runs WITHOUT a live DB (rows are embedded here as a
# fixture to let CI run without DB access).
# The fixture was produced by the backfill preview script (L0F_RESOLVER_BACKFILL_PREVIEW_v1_0.md).

CANONICAL_CHART_FIXTURE = [
    # (event_id, category, domain)
    # Row order matches SELECT event_date ASC
    ("3e96c6da-3ad6-5329-a40b-0b9240a1cbdb-corr-congenital", "psychological", "psychological/speech_pattern_arc"),
    ("5d039007-0244-58c6-ad39-152c179c6ac8", "other", "other/birth"),
    ("0d03e02a-e619-52b5-8a78-8f26e13ba125", "creative", "creative/award"),
    ("3e96c6da-3ad6-5329-a40b-0b9240a1cbdb", "psychological", "psychological/speech_pattern_arc"),
    ("64c475da-5248-5332-9127-9331fae79f23", "health", "health/chronic_onset"),
    ("3a37fa76-cfc1-599b-bbdf-97cff784f5ac", "relationship", "relationship/romantic_long_term_started"),
    ("d5db1b9a-b8c5-5b90-9641-c9ae9b1c2035", "spiritual", "spiritual/transmission"),
    ("39f8395f-dfa6-5deb-9d3d-e4881c905e29", "education", "education/advanced_course_partial"),
    ("d5db1b9a-b8c5-5b90-9641-c9ae9b1c2035-corr-2001-initiation", "spiritual", "spiritual/transmission"),
    ("359944e3-908f-5eb0-ba38-6696bbbefbe6", "education", "education/entrance_exam_preparation"),
    ("62f0460d-0cf1-5eab-bedc-47ecfcb04657", "spiritual", "spiritual/sadhana_initiation"),
    ("123eee97-8885-5d50-b0f1-94281f8f2d49", "psychological", "psychological/chronic_episode"),
    ("4a1b1dc0-df38-56d8-a2c8-0383bb2acc7c", "education", "education/entrance_exam_preparation_ended"),
    ("45ba996d-5923-5570-8055-8cbf4a470636", "relationship", "relationship/romantic_concurrent"),
    ("cd68bc5c-c5fc-5914-bd95-e18ba639a5dc", "education", "education/opportunity_declined"),
    ("fd04fecc-21f7-5dfd-b68b-f1a6f1cd6bfa", "career", "career/first_job_joined"),
    ("8573c0ca-9fc5-52a0-8309-f1b324a51d4a-corr-day-lock", "health", "health/chronic_onset"),
    ("4e09e1e1-7925-5675-9af8-74e8eea6fe67", "health", "health/surgery_minor"),
    ("71af4f61-3efc-557b-949a-d855845a5ca5", "education", "education/engineering_completed"),
    ("8573c0ca-9fc5-52a0-8309-f1b324a51d4a", "health", "health/chronic_onset"),
    ("aed78f94-87ca-5347-a1d0-7f277a99b6c4", "career", "career/first_job_exited"),
    ("1dc207bc-a85e-5383-b39d-39be4629a582", "loss", "loss/grandparent_passing"),
    ("bd7f5711-8668-5315-8e25-94dc94f2a101", "finance", "finance/family_windfall"),
    ("132b61e0-3409-53fd-bb1a-80b4b6bdcc67", "spiritual", "spiritual/devata_adoption"),
    ("a1ef10c2-c52d-536e-9fd5-51342d58721e", "travel", "travel/first_foreign_trip"),
    ("4e96f4b9-fe3b-5b40-bdb3-c60e3024abfa", "education", "education/mba_admission"),
    ("95138517-2d23-51a6-b13b-71801e806a11", "education", "education/mba_enrolled"),
    ("cf0c918d-da71-504f-9c62-4920c48cd69e", "education", "education/leadership_role"),
    ("852d1420-e733-582b-a2ae-f7de33b8d38e", "creative", "creative/modeling"),
    ("aa591eb5-8e00-5600-b9c1-7177f7919ab8", "relationship", "relationship/romantic_concurrent"),
    ("c143ce2a-f1e1-5092-9c04-f659fa0de5e1", "education", "education/mba_graduation"),
    ("6f5ee9cb-8b35-5da9-a601-30430e8ad7d9", "career", "career/corporate_job_joined"),
    ("72fad18c-ad30-5f46-9418-c2ed28c4d9ac", "family", "family/parent_illness_onset"),
    ("b72f40f7-687e-51dd-a21d-06b184fc24c1", "family", "family/marriage"),
    ("56a1222d-8c88-5445-b2a2-1fd89d470719", "spiritual", "spiritual/devata_adoption"),
    ("b5ea6a4d-6e0a-5ed3-875c-e241d3cb50a5", "career", "career/employer_instability"),
    ("e3b2f1d5-5609-5dca-af84-d9fac54cd3cd", "career", "career/employer_switch"),
    ("b75c63f4-ead1-5d6d-9811-011277347d57", "loss", "loss/parent_passing"),
    ("928a1f56-0940-5428-a35a-8591f84fd5b4", "residential+travel", "residential+travel/foreign_move_start"),
    ("928a1f56-0940-5428-a35a-8591f84fd5b4-fs", "residential+travel", None),  # NULL domain shadow row
    ("974651b2-f743-56d9-b9e9-178e0b8e7431", "health", "health/panic_anxiety_episode"),
    ("56a1222d-8c88-5445-b2a2-1fd89d470719-corr-2021-04", "spiritual", "spiritual/devata_adoption"),
    ("b8884cbe-b894-588b-a70f-2c0a90fdeac5", "career", "career/award_selection"),
    ("74e527bb-1b22-51a8-bafb-8d4d7d80ae1d", "career", "career/business_stalled"),
    ("25a0f2ec-98fc-5bc9-a6e7-3916f35149a3", "family", "family/child_birth"),
    ("86cbb042-8c3b-54e0-bf79-8f51b5850c13", "relationship", "relationship/romantic_concurrent"),
    ("021e49f5-9c6a-5e0e-ad6c-84c8ea2ad83f-corr-2022-07-14", "relationship", "relationship/romantic_concurrent_ended"),
    ("021e49f5-9c6a-5e0e-ad6c-84c8ea2ad83f", "relationship", "relationship/romantic_concurrent_ended"),
    ("7f29458f-db56-5a4b-a564-6a4754d0821d", "residential+travel", "residential+travel/foreign_return"),
    ("d506f3e6-6188-5327-8920-d3896e630f08", "education", "education/executive_education_completed"),
    ("661c8535-5906-5333-8b38-e14305bddad6", "career", "career/entrepreneurship_founded"),
    ("836bb274-6a6f-5c29-a298-f3c476197b8a", "career", "career/business_milestone_major"),
    ("63e90113-eb35-5be4-9bce-1da7eda7d82d", "spiritual", "spiritual/practice_intensification"),
    ("d81fae4e-edf4-58d9-b201-cced7eae19d7", "loss", "loss/financial_deception"),
    ("275b0c18-a159-5560-95f7-2a6cfbec58c4", "spiritual", "spiritual/ritual_infrastructure"),
    ("a95552d7-0c6c-5188-8ab2-e972a8d13118", "health", "health/chronic_resolution"),
    ("acb209c7-8107-53e7-b6ea-b8596e0f07cb", "spiritual", "spiritual/devotional_shift"),
    ("4018cc05-6f8f-51c4-9ffc-3c1de800dc72", "finance", "finance/business_milestone_windfall"),
    ("3ea3a2fc-3568-56a9-963b-57c7e7b4755c", "spiritual", "spiritual/devata_adoption"),
    ("2bfb5b17-6901-5d15-ba80-5f0f1d5611f0", "other", "other/psychological_shift"),
    ("153d920e-640d-598c-9380-795a5d4efa63", "career", "career/business_project_closed"),
    ("732a4119-a333-5ce5-afbf-082453e1f6d5", "career", "career/business_milestone_clearance"),
    ("1f9c6775-30c2-5f92-b1a5-24512f5681a6", "relationship", "relationship/marital_status_current"),
    ("5278d97c-e769-529a-b0c2-be1e965c2d6b", "travel_event", "travel"),  # test fixture row
]

assert len(CANONICAL_CHART_FIXTURE) == 64, (
    f"Fixture must have 64 rows, got {len(CANONICAL_CHART_FIXTURE)}"
)


def test_canonical_chart_fixture_has_64_rows():
    assert len(CANONICAL_CHART_FIXTURE) == 64


def test_canonical_chart_coverage_assertion_64_equals_classified_plus_ambiguous():
    """64 = classified + ambiguous (no silent drops)."""
    rows = [
        {"event_id": eid, "category": cat, "domain": dom}
        for eid, cat, dom in CANONICAL_CHART_FIXTURE
    ]
    results = resolve_batch(rows)
    assert len(results) == 64, f"Expected 64 results, got {len(results)}"

    classified = [r for r in results if r.confidence != CONFIDENCE_AMBIGUOUS]
    ambiguous = [r for r in results if r.confidence == CONFIDENCE_AMBIGUOUS]
    assert len(classified) + len(ambiguous) == 64


def test_canonical_chart_all_resolved_classes_exist_in_ontology():
    """Every non-AMBIGUOUS result carries a valid event_class_id."""
    rows = [
        {"event_id": eid, "category": cat, "domain": dom}
        for eid, cat, dom in CANONICAL_CHART_FIXTURE
    ]
    results = resolve_batch(rows)
    bad = [
        r for r in results
        if r.event_class is not None and r.event_class not in VALID_EVENT_CLASS_IDS
    ]
    assert not bad, (
        f"Resolved to unknown event_class_ids: "
        f"{[(r.event_id, r.event_class) for r in bad]}"
    )


def test_canonical_chart_ambiguous_rows_are_explicitly_listed():
    """Ambiguous rows carry a non-empty reason (no silent drop)."""
    rows = [
        {"event_id": eid, "category": cat, "domain": dom}
        for eid, cat, dom in CANONICAL_CHART_FIXTURE
    ]
    results = resolve_batch(rows)
    for r in results:
        if r.confidence == CONFIDENCE_AMBIGUOUS:
            assert r.rule_matched, f"AMBIGUOUS row {r.event_id} has empty rule_matched"
