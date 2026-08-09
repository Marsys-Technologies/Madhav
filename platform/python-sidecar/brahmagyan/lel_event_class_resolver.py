"""
brahmagyan.lel_event_class_resolver — L6 LEL→event_class resolver.

SAMPURTI Campaign, Lane L0f, G14a (2026-08-10).

Maps a life_events row (category, domain) → event_class from
`brahma_event_ontology` (27 classes; SSoT = l0_ghatana.EVENT_CLASSES).

Design
------
The resolver is fully DETERMINISTIC — no LLM calls, no fuzzy matching.
Two rule tiers, evaluated in order:

  TIER 1 — domain exact match:
    `life_events.domain` is matched against an evidence-cited
    DOMAIN_TO_EVENT_CLASS lookup table. A domain value that maps to exactly
    one event_class yields confidence=EXACT.

  TIER 2 — category + keyword disambiguation:
    When the domain carries no tier-1 match (or is NULL), the resolver
    inspects `category` (→ narrows to a candidate set of event classes
    sharing that lel_category) and then applies keyword rules to the domain
    string itself. If a single class is unambiguously indicated,
    confidence=KEYWORD. If two or more candidate classes remain and
    keyword rules cannot distinguish them, confidence=AMBIGUOUS.

Circularity Guard (R16 / CRITICAL RAIL)
-----------------------------------------
This resolver feeds SCORING only. It MUST NOT be wired into:
  - ka_kshetra field inputs (temporal scoring context)
  - any bodha layer field (interpretive layer inputs)
  - chart_facts rows (L1 is sealed, R19)
Never import or call this module from a writer that feeds those surfaces.

Coverage assertion
------------------
resolved_count + ambiguous_count == total_input_count (exact; no silent drops).
`assert_coverage(rows)` enforces this and raises CoverageAssertionError if
any row is absent from the output.

Versioning
----------
RESOLVER_VERSION = "l0f_v1.0" — increment on any rule change.
Every output row carries this version in its audit trail so a re-run
after a rule change is detectable (old rows in the side table carry the
prior version; a backfill script applies the new version forward).

R16 — every claim cites its detector:
  confidence=EXACT   → domain in DOMAIN_TO_EVENT_CLASS (exact dict lookup)
  confidence=KEYWORD → keyword_rule field names the matched keyword/rule
  confidence=AMBIGUOUS → reason field lists the candidate classes
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

RESOLVER_VERSION = "l0f_v1.0"

CONFIDENCE_EXACT = "EXACT"         # tier-1 domain exact match
CONFIDENCE_KEYWORD = "KEYWORD"     # tier-2 keyword-assisted
CONFIDENCE_AMBIGUOUS = "AMBIGUOUS" # cannot deterministically resolve


# ── Tier-1: domain exact match table ──────────────────────────────────────────
#
# Keys = life_events.domain values (exactly as stored in the DB).
# Values = event_class_id from brahma_event_ontology (l0_ghatana.EVENT_CLASSES).
#
# Evidence rule: a domain string is admitted to this table ONLY when its text
# directly names the event_class's own classical concept (per BPHS citations
# on brahma_event_ontology.signature_model) AND no other event_class in the
# ontology has an equal claim. Every entry carries an inline evidence note.

DOMAIN_TO_EVENT_CLASS: dict[str, str] = {
    # ── birth anchor ────────────────────────────────────────────────────────
    "other/birth": "birth_anchor",
    # The domain literally names the natal epoch; birth_anchor.lel_category='other'
    # matches, and it is the ONLY class with lel_category='other'.

    # ── career entries ───────────────────────────────────────────────────────
    "career/first_job_joined": "career_entry",
    # "first job" = literal career_entry; no other career-domain class fits.
    "career/corporate_job_joined": "career_entry",
    # Joining a corporate role after a break = career_entry (re-entry).

    "career/first_job_exited": "career_change",
    # Exiting a first job to pivot (IIT re-prep) = career_change; the exit
    # precipitates a domain/trajectory shift, not merely a setback.

    "career/employer_switch": "career_change",
    # Explicit switch between employers = career_change (adjacency in ontology).

    "career/employer_instability": "career_setback",
    # Company instability / crash forcing a job search = career_setback signature:
    # adverse condition on 10th, forced exit not chosen — matches
    # career_setback.lel_category='career' + magnitude_floor='significant'.

    "career/entrepreneurship_founded": "business_launch",
    # "Entrepreneurship / founded" = direct business_launch event.
    # business_launch.lel_category='career'; milestone_template covers
    # decision → registration → first_revenue.

    "career/business_stalled": "career_setback",
    # A business that could not be made operational = career_setback (adverse
    # outcome affecting the 10th/7th/11th houses).

    "career/business_milestone_major": "career_advancement",
    # A major concrete business milestone (operation launch) = career_advancement:
    # benefic transit to 10th/11th, dhana-yoga. It is an advancement milestone,
    # NOT a new business_launch (the business was already founded).

    "career/business_milestone_clearance": "career_advancement",
    # Regulatory clearance = advancement milestone; clears path for the
    # established enterprise (the quarry was already acquired/attempted).

    "career/business_project_closed": "career_setback",
    # A project wrapping up with no successor = career_setback (adverse outcome
    # on the entrepreneurial arc). Not career_change: there is no new role.

    "career/award_selection": "achievement_recognition",
    # Explicit award / selection = achievement_recognition (domain and
    # lel_category='creative' per ontology; not career_advancement, which is
    # career_lel_category — see F-1 disposition cited in event_class_resolution.ts).

    # ── education ────────────────────────────────────────────────────────────
    "education/entrance_exam_preparation": "education_milestone",
    # Preparation phase is part of the education_milestone chain
    # (exam_written milestone). Not exam_outcome alone.
    "education/entrance_exam_preparation_ended": "education_milestone",
    # End of exam-prep phase = completion milestone in the education arc.
    "education/advanced_course_partial": "education_milestone",
    # Joining a course (even if partial) = education_milestone enrollment.
    "education/engineering_completed": "education_milestone",
    # Degree completion = education_milestone.irreversibility_milestone='completion'.
    "education/mba_admission": "education_milestone",
    # Admission secured = enrollment milestone in education_milestone chain.
    "education/mba_enrolled": "education_milestone",
    # Formal enrollment = education_milestone.
    "education/mba_graduation": "education_milestone",
    # Graduation = irreversibility_milestone='completion'.
    "education/leadership_role": "achievement_recognition",
    # Elected to a student leadership role = achievement_recognition
    # (recognition domain, not an education credential per se).
    "education/opportunity_declined": "education_milestone",
    # A declined educational opportunity (CMU exchange) marks a decision node
    # in the education arc — still an education_milestone event (the
    # exam/result/enrollment chain touches this decision).
    "education/executive_education_completed": "education_milestone",
    # Executive MBA completion = education_milestone.

    # ── family ───────────────────────────────────────────────────────────────
    "family/marriage": "marriage",
    # Literal marriage event. marriage.lel_category='relationship', but the
    # life_events.category is 'family' (the mismatch documented in F-1 of
    # event_class_resolution.ts; resolved here by domain, not category).
    "family/child_birth": "childbirth",
    # Birth of children = childbirth.
    "family/parent_illness_onset": "parental_event",
    # Parent's illness onset = parental_event (4th/9th lord dasha;
    # interval duration_prior present in ontology).

    # ── relationship ─────────────────────────────────────────────────────────
    "relationship/romantic_long_term_started": "romantic_start",
    # Romantic relationship start = romantic_start.
    "relationship/romantic_concurrent": "romantic_start",
    # Concurrent romantic relationship (also a start event for that relationship).
    "relationship/romantic_concurrent_ended": "separation",
    # End of a relationship = separation class (dissolution of the 7th/5th
    # house bond; adverse dasha signature).
    "relationship/marital_status_current": "separation",
    # Marital separation / current status = separation event class
    # (physical_separation milestone in the chain).

    # ── loss ─────────────────────────────────────────────────────────────────
    "loss/grandparent_passing": "bereavement",
    # Passing of a grandparent = bereavement (maraka/8th house).
    "loss/parent_passing": "bereavement",
    # Passing of a parent = bereavement.
    "loss/financial_deception": "financial_deception",
    # Explicit deception/fraud loss = financial_deception class
    # (distinct from major_loss by the Rahu/fraud signature).

    # ── finance ──────────────────────────────────────────────────────────────
    "finance/family_windfall": "major_gain",
    # Windfall = major_gain (BPHS ch.2,11; dhana-bhava). Cited in F-1.
    "finance/business_milestone_windfall": "major_gain",
    # Business windfall = major_gain. Cited in F-1.

    # ── health ───────────────────────────────────────────────────────────────
    "health/surgery_minor": "surgery",
    # Minor surgery = surgery event class (Mars/Ketu dasha-transit).
    "health/chronic_onset": "chronic_onset",
    # Chronic illness onset = chronic_onset (Sade-Sati / Saturn dasha).
    "health/chronic_resolution": "chronic_onset",
    # Resolution of a chronic illness = still part of the chronic_onset arc
    # (the interval's end). No dedicated 'chronic_resolution' class exists;
    # chronic_onset is the closest owning class (interval temporal_shape).
    "health/panic_anxiety_episode": "illness_acute",
    # Panic/anxiety episode = acute illness (point event; adverse transit to
    # lagna / 6th house — Mars/Saturn trigger matches illness_acute).

    # ── spiritual ────────────────────────────────────────────────────────────
    "spiritual/transmission": "spiritual_turn",
    # Spiritual transmission / paternal dialogues = spiritual_turn (9th/12th
    # house; Ketu/Jupiter dasha; interval).
    "spiritual/sadhana_initiation": "spiritual_turn",
    # Initiation into a sadhana practice = spiritual_turn.
    "spiritual/devata_adoption": "spiritual_turn",
    # Adoption of a devata (Ugratara, Mahadev, Kamlatmika) = spiritual_turn.
    "spiritual/devotional_shift": "spiritual_turn",
    # Devotional shift (Vishnu/Venkateshwara) = spiritual_turn.
    "spiritual/practice_intensification": "spiritual_turn",
    # Intensification of daily practice = spiritual_turn (interval; dharma
    # chapter deepening over time).
    "spiritual/ritual_infrastructure": "spiritual_turn",
    # Establishing ritual infrastructure (yantra mandala) = spiritual_turn.

    # ── creative ─────────────────────────────────────────────────────────────
    "creative/award": "achievement_recognition",
    # Award in a creative domain = achievement_recognition.
    "creative/modeling": "achievement_recognition",
    # Modeling engagement = achievement_recognition (5th/10th house recognition).

    # ── residential + travel ─────────────────────────────────────────────────
    "residential+travel/foreign_move_start": "foreign_settlement",
    # Moving to the US on work deputation for 4 years = foreign_settlement
    # (R15 ruling: counts as genuine foreign settlement; 12th/9th house).
    "residential+travel/foreign_return": "relocation",
    # Return from foreign settlement = relocation (4th/3rd/12th house; Moon/Rahu).

    # ── travel ───────────────────────────────────────────────────────────────
    "travel/first_foreign_trip": "travel_event",
    # First international trip (Thailand) = travel_event (discrete travel,
    # not foreign_settlement; duration is a trip, not residency).

    # ── psychological ─────────────────────────────────────────────────────────
    "psychological/speech_pattern_arc": "psychological_arc",
    # Stammering arc = psychological_arc (1st/6th/12th; Moon/Mercury/Saturn).
    "psychological/chronic_episode": "psychological_arc",
    # Vertigo/chronic psychological episode = psychological_arc.

    # ── other ────────────────────────────────────────────────────────────────
    "other/psychological_shift": "psychological_arc",
    # Sustained psychological shift (focus, one-pointed attention) =
    # psychological_arc (same 1L/lagna pattern; interval-duration arc).
}


# ── Tier-2: category → candidate classes (lel_category index) ────────────────
#
# Built from l0_ghatana.EVENT_CLASSES lel_category fields.
# Used ONLY when tier-1 yields no match.

CATEGORY_TO_CANDIDATES: dict[str, list[str]] = {
    "career":       ["career_entry", "career_advancement", "career_change",
                     "career_setback", "business_launch"],
    "education":    ["education_milestone", "exam_outcome"],
    "relationship": ["marriage", "romantic_start", "separation"],
    "family":       ["childbirth", "parental_event", "marriage"],
    # 'marriage' in family because life_events.category='family' for the
    # marriage row (domain disambiguates via tier-1).
    "loss":         ["bereavement", "major_loss", "financial_deception"],
    "finance":      ["major_gain", "property_acquisition"],
    "health":       ["illness_acute", "chronic_onset", "surgery"],
    "spiritual":    ["spiritual_turn"],
    "creative":     ["achievement_recognition"],
    "residential+travel": ["relocation", "foreign_settlement"],
    "travel":       ["travel_event", "foreign_settlement"],
    "travel_event": ["travel_event"],
    "psychological": ["psychological_arc"],
    "other":        ["birth_anchor", "psychological_arc"],
}

# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class ResolutionResult:
    """Output of resolving one life_events row to an event_class.

    Attributes:
        event_id:        life_events.event_id (caller-supplied; passed through).
        category:        life_events.category (input).
        domain:          life_events.domain (input; may be None).
        event_class:     Resolved event_class_id, or None when AMBIGUOUS.
        confidence:      EXACT | KEYWORD | AMBIGUOUS.
        rule_matched:    Human-readable name of the rule that matched.
        matched_tokens:  Domain string or keyword that triggered the match.
        candidates:      Non-empty only when AMBIGUOUS; lists the candidates.
        resolver_version: RESOLVER_VERSION constant.
        audit_trail:     Structured dict for the JSON audit column.
    """
    event_id: str
    category: str
    domain: Optional[str]
    event_class: Optional[str]
    confidence: str
    rule_matched: str
    matched_tokens: str
    candidates: list[str] = field(default_factory=list)
    resolver_version: str = RESOLVER_VERSION

    @property
    def resolved(self) -> bool:
        return self.confidence != CONFIDENCE_AMBIGUOUS

    @property
    def audit_trail(self) -> dict:
        return {
            "resolver_version": self.resolver_version,
            "confidence": self.confidence,
            "rule_matched": self.rule_matched,
            "matched_tokens": self.matched_tokens,
            "candidates": self.candidates,
            "domain_input": self.domain,
            "category_input": self.category,
        }


# ── Coverage assertion ────────────────────────────────────────────────────────

class CoverageAssertionError(Exception):
    """Raised when output row count != input row count (silent-drop guard)."""
    pass


def assert_coverage(
    input_rows: list[dict],
    results: list[ResolutionResult],
) -> None:
    """Assert that every input row has exactly one output row.

    Mirrors the 'every input row must resolve or be explicitly listed as
    AMBIGUOUS — no silent drops' discipline from event_class_resolution.ts.

    Args:
        input_rows: list of dicts with at least 'event_id' key.
        results:    output of resolve_batch(input_rows).

    Raises:
        CoverageAssertionError if len(results) != len(input_rows) or any
        event_id in input_rows is absent from results.
    """
    if len(results) != len(input_rows):
        raise CoverageAssertionError(
            f"Coverage assertion failed: {len(input_rows)} input rows but "
            f"{len(results)} output rows — silent drop detected."
        )
    result_ids = {r.event_id for r in results}
    input_ids = {row["event_id"] for row in input_rows}
    missing = input_ids - result_ids
    if missing:
        raise CoverageAssertionError(
            f"Coverage assertion failed: {len(missing)} event_id(s) present in "
            f"input but absent from output (silent drop): "
            f"{sorted(missing)}"
        )


# ── Core resolver ─────────────────────────────────────────────────────────────

def resolve_event_class(
    event_id: str,
    category: str,
    domain: Optional[str],
) -> ResolutionResult:
    """Resolve one life_events row to an event_class.

    Deterministic; no DB access; no LLM calls.

    Args:
        event_id:  life_events.event_id (passed through for audit).
        category:  life_events.category (NOT NULL in schema).
        domain:    life_events.domain (nullable; preferred input).

    Returns:
        ResolutionResult with confidence=EXACT, KEYWORD, or AMBIGUOUS.
        AMBIGUOUS rows carry candidates list and event_class=None.
        NEVER raises — all error paths produce AMBIGUOUS with a reason.
    """
    domain_clean = domain.strip() if domain else None

    # ── Tier 1: domain exact match ────────────────────────────────────────
    if domain_clean and domain_clean in DOMAIN_TO_EVENT_CLASS:
        matched_class = DOMAIN_TO_EVENT_CLASS[domain_clean]
        return ResolutionResult(
            event_id=event_id,
            category=category,
            domain=domain,
            event_class=matched_class,
            confidence=CONFIDENCE_EXACT,
            rule_matched="tier1_domain_exact",
            matched_tokens=domain_clean,
            candidates=[],
        )

    # ── Tier 2: category + keyword disambiguation ─────────────────────────
    candidates = list(CATEGORY_TO_CANDIDATES.get(category, []))

    if not candidates:
        # Unknown category — cannot resolve
        return ResolutionResult(
            event_id=event_id,
            category=category,
            domain=domain,
            event_class=None,
            confidence=CONFIDENCE_AMBIGUOUS,
            rule_matched="tier2_unknown_category",
            matched_tokens=category,
            candidates=[],
        )

    if len(candidates) == 1:
        # Only one possible class for this category — unambiguous
        return ResolutionResult(
            event_id=event_id,
            category=category,
            domain=domain,
            event_class=candidates[0],
            confidence=CONFIDENCE_KEYWORD,
            rule_matched="tier2_single_candidate",
            matched_tokens=f"category={category!r}",
            candidates=[],
        )

    # Multiple candidates: apply keyword rules on domain string
    if domain_clean:
        domain_lower = domain_clean.lower()

        # ── Tier-2 keyword helper ─────────────────────────────────────────
        # domain values use underscore-separated tokens (e.g. "career/company_founded").
        # Python's \b treats '_' as a word char, so \b\bfound\b won't match
        # "company_founded". We use plain substring search (no \b) which is safe
        # because the rules below are ordered most-specific first within each
        # category, so an earlier rule's specificity prevents false matches.

        def _kw(*roots: str) -> bool:
            """True iff any root string appears as a substring of domain_lower."""
            return any(root in domain_lower for root in roots)

        # ── Career keyword rules ──────────────────────────────────────────
        if category == "career":
            # Order matters: most specific first to avoid wrong early exit.
            if _kw("entrepreneur", "founded", "launch", "startup", "start_up"):
                return _keyword_result(event_id, category, domain, "business_launch",
                                       "tier2_kw_business_launch", domain_clean)
            if _kw("first_job", "first_corporate", "joined", "job_joined", "entry"):
                return _keyword_result(event_id, category, domain, "career_entry",
                                       "tier2_kw_career_entry", domain_clean)
            if _kw("switch", "changed", "transition", "pivot", "exited", "exit"):
                return _keyword_result(event_id, category, domain, "career_change",
                                       "tier2_kw_career_change", domain_clean)
            if _kw("setback", "stalled", "crash", "instab", "failed", "closed",
                   "project_closed", "lost", "could_not", "collapsed"):
                return _keyword_result(event_id, category, domain, "career_setback",
                                       "tier2_kw_career_setback", domain_clean)
            if _kw("advance", "promot", "elevat", "award", "recognition", "milestone",
                   "clearance"):
                return _keyword_result(event_id, category, domain, "career_advancement",
                                       "tier2_kw_career_advancement", domain_clean)

        # ── Education keyword rules ───────────────────────────────────────
        if category == "education":
            if _kw("exam", "test", "result", "score", "rank", "iit", "entrance",
                   "assessment", "attempt"):
                return _keyword_result(event_id, category, domain, "exam_outcome",
                                       "tier2_kw_exam_outcome", domain_clean)
            # Default education → education_milestone
            return _keyword_result(event_id, category, domain, "education_milestone",
                                   "tier2_kw_education_default", domain_clean)

        # ── Loss keyword rules ────────────────────────────────────────────
        if category == "loss":
            if _kw("decept", "fraud", "scam", "cheat", "steal"):
                return _keyword_result(event_id, category, domain, "financial_deception",
                                       "tier2_kw_financial_deception", domain_clean)
            if _kw("financ", "money", "wealth", "fund"):
                return _keyword_result(event_id, category, domain, "major_loss",
                                       "tier2_kw_major_loss", domain_clean)
            if _kw("passing", "passed", "death", "died", "bereav", "dead",
                   "relative", "parent", "grandparent"):
                return _keyword_result(event_id, category, domain, "bereavement",
                                       "tier2_kw_bereavement", domain_clean)

        # ── Finance keyword rules ─────────────────────────────────────────
        if category == "finance":
            if _kw("property", "land", "house", "home", "flat", "acquisition"):
                return _keyword_result(event_id, category, domain, "property_acquisition",
                                       "tier2_kw_property_acquisition", domain_clean)
            # Default finance → major_gain
            return _keyword_result(event_id, category, domain, "major_gain",
                                   "tier2_kw_finance_default", domain_clean)

        # ── Health keyword rules ──────────────────────────────────────────
        if category == "health":
            if _kw("surg", "operat", "procedure", "arthroscop"):
                return _keyword_result(event_id, category, domain, "surgery",
                                       "tier2_kw_surgery", domain_clean)
            if _kw("chronic", "onset", "persist", "long_term", "resol"):
                return _keyword_result(event_id, category, domain, "chronic_onset",
                                       "tier2_kw_chronic_onset", domain_clean)
            # Default health → illness_acute
            return _keyword_result(event_id, category, domain, "illness_acute",
                                   "tier2_kw_illness_acute_default", domain_clean)

        # ── Relationship / family keyword rules ───────────────────────────
        if category == "family" or category == "relationship":
            if _kw("marr", "wed", "nuptial", "vivah"):
                return _keyword_result(event_id, category, domain, "marriage",
                                       "tier2_kw_marriage", domain_clean)
            if _kw("birth", "born", "child", "daughter", "twin"):
                return _keyword_result(event_id, category, domain, "childbirth",
                                       "tier2_kw_childbirth", domain_clean)
            if _kw("parent", "father", "mother", "illness", "sick", "hospital"):
                return _keyword_result(event_id, category, domain, "parental_event",
                                       "tier2_kw_parental_event", domain_clean)
            if _kw("separat", "divorc", "split", "dissolv", "status_current", "ended"):
                return _keyword_result(event_id, category, domain, "separation",
                                       "tier2_kw_separation", domain_clean)
            if _kw("romantic", "affair", "relationship", "started", "begun", "concurrent"):
                return _keyword_result(event_id, category, domain, "romantic_start",
                                       "tier2_kw_romantic_start", domain_clean)

        # ── Residential+travel keyword rules ──────────────────────────────
        if category == "residential+travel":
            if _kw("move_start", "foreign_move", "settled", "abroad", "deput"):
                return _keyword_result(event_id, category, domain, "foreign_settlement",
                                       "tier2_kw_foreign_settlement", domain_clean)
            if _kw("return", "came_back", "back_to"):
                return _keyword_result(event_id, category, domain, "relocation",
                                       "tier2_kw_relocation", domain_clean)

        # ── Travel keyword rules ──────────────────────────────────────────
        if category == "travel":
            if _kw("settl", "deput", "long_stay", "visa"):
                return _keyword_result(event_id, category, domain, "foreign_settlement",
                                       "tier2_kw_foreign_settlement_travel", domain_clean)
            # Default travel → travel_event
            return _keyword_result(event_id, category, domain, "travel_event",
                                   "tier2_kw_travel_default", domain_clean)

    # ── Fallthrough: AMBIGUOUS ─────────────────────────────────────────────
    # Keyword rules exhausted or domain is NULL; cannot deterministically choose.
    return ResolutionResult(
        event_id=event_id,
        category=category,
        domain=domain,
        event_class=None,
        confidence=CONFIDENCE_AMBIGUOUS,
        rule_matched="tier2_ambiguous_no_keyword_match",
        matched_tokens=domain_clean or "(null domain)",
        candidates=candidates,
    )


def _keyword_result(
    event_id: str,
    category: str,
    domain: Optional[str],
    event_class: str,
    rule_name: str,
    matched: str,
) -> ResolutionResult:
    """Helper: build a KEYWORD-confidence ResolutionResult."""
    return ResolutionResult(
        event_id=event_id,
        category=category,
        domain=domain,
        event_class=event_class,
        confidence=CONFIDENCE_KEYWORD,
        rule_matched=rule_name,
        matched_tokens=matched,
        candidates=[],
    )


# ── Batch resolver ────────────────────────────────────────────────────────────

def resolve_batch(rows: list[dict]) -> list[ResolutionResult]:
    """Resolve a list of life_events rows.

    Each dict must have 'event_id', 'category', and optionally 'domain'.
    Returns one ResolutionResult per input row, in the same order.
    Followed by assert_coverage() to enforce no-silent-drop discipline.

    Args:
        rows: list of dicts with keys event_id, category, domain (optional).

    Returns:
        list[ResolutionResult] — same length as rows, same order.
    """
    results = []
    for row in rows:
        results.append(
            resolve_event_class(
                event_id=row["event_id"],
                category=row.get("category", ""),
                domain=row.get("domain"),
            )
        )
    assert_coverage(rows, results)
    return results
