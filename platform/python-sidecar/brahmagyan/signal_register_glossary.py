"""
signal_register_glossary.py — Acharya-grade labels for raw signal token families
==================================================================================
Purpose (B-05 / A-14):
    A-14 will add a lint that enforces zero raw fact_category / fact_key / signal_type_id
    template strings in *_text / *_thesis / *_statement narrative fields. This module
    provides the human-readable mapping for every token family that the PP2 audit found
    leaking into those fields.

    Leaked-token families identified by PP2 findings F-114 and F-131:

    F-114 (TIER2-HONESTY): assess_marriage / assess_health signal lenses return raw
    signal_headline_text strings whose category segment is a bare fact_category name
    with snake_case and underscores. The top-10 ranked signals for the "marriage" lens
    consisted entirely of ga_sensitive Saturn rows whose category labels read, verbatim:
        "SAT: graha nakshatra join: nakshatra id ref = 16"
        "SAT: bhrigu nadi point: sign = Capricorn"
        "SAT: esoteric point shiva: sign = Aquarius"
        "SAT: upagraha position"
        "SAT: midpoint"
        "SAT: graha pada join"
        "SAT: saham position"
        "SAT: aprakasha position"
    The fact_category portion of each headline is a raw schema key, not an
    acharya-grade label. None named the 7th lord, Venus, or a marriage yoga.

    F-131 (TIER2-HONESTY): kala_priority_ranking_get returns priority signals whose
    signal_headline_text is also the raw MSR template:
        "SAT: arudha pada: sign = Aquarius [ga_sensitive]"
        "graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method
         [ga_structural]"
    The second is not even an astrological finding — it is an internal computation-
    abstention marker (the writer floored D14 cheshta bala per §B.10 because no
    verifiable classical per-varga formula exists for D14). That floor-reason string
    was scored and served as a priority signal to the native.

Usage:
    A-14's lint can import SIGNAL_TYPE_GLOSSARY and FACT_CATEGORY_GLOSSARY to:
      1. Assert that no *_text field in bodha_msr_signals / kala_priority_ranking rows
         contains a bare key from FACT_CATEGORY_GLOSSARY (the raw form is the violation).
      2. The serving layer (bo_laksana._build_headline_text) can optionally use
         FACT_CATEGORY_DISPLAY_LABEL to humanize the category segment before writing
         signal_headline_text to the DB, so the lint always passes.
      3. INTERNAL_MARKER_PATTERNS identifies strings that are NOT astrological findings
         and must be filtered out of priority-ranking results (F-131 remediation).

LIVE CONSUMER (F-131 remediation, 2026-08-21) — this module is no longer import-less:
    The surface F-131 was found on (kala_priority_ranking_get) is a TypeScript capability
    handler and cannot import Python. Rather than hand-copy these tables across the process
    boundary, they are GENERATED into TypeScript per the single-source-contract mandate
    (RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §19):

        source of truth : this file
        generator       : platform/scripts/generate_signal_glossary_mirror.ts
                          (`npm run codegen:signal-glossary`)
        generated mirror: platform/src/lib/retrieval/signal_glossary.generated.ts
        behaviour       : platform/src/lib/retrieval/signal_glossary.ts
        serving seam    : platform/src/lib/retrieval/registry/layers/L3_kala/
                          call_service_wrappers.ts :: callPriorityRankingCapability

    EDITING THIS FILE REQUIRES REGENERATING THE MIRROR. The generated module pins the
    sha256 of this file; `signal_glossary.parity.test.ts` re-hashes it and fails CI if the
    two have drifted, so an un-regenerated edit here is caught mechanically, not by review.

Authority:
    Labels are acharya-grade (§J standard: a senior Jyotish acharya should recognize
    the label as the correct classical term for the underlying concept).
    No label is fabricated — each maps to a well-established Jyotish technical term.
    Where a label would require qualification (e.g. "Bhrigu Nadi special point"), the
    classical term is given; the qualifier is in the detail comment.
"""
from __future__ import annotations

# ── Primary glossary: raw fact_category → acharya-grade display label ────────
# Keys are the exact strings that appear in fact_category / in the signal_headline_text
# template produced by bo_laksana._build_headline_text().
# Values are the classical labels A-14's lint expects to see in narrative text fields.

FACT_CATEGORY_DISPLAY_LABEL: dict[str, str] = {
    # ── ga_sensitive categories (F-114 / F-131 primary leaking families) ──────
    "graha_nakshatra_join":          "Graha–Nakshatra Junction",
    "bhrigu_nadi_point":             "Bhrigu Nadi Special Point",
    "esoteric_point_shiva":          "Esoteric Shiva Point",
    "upagraha_position":             "Upagraha (Shadow Planet) Position",
    # F-131 remediation, domain-correctness spot-check: this label read
    # "Midpoint (Sandhya Bindu)". "Sandhya bindu" is NOT a classical Jyotish term — sandhyā
    # means twilight, and the classical word for a junction is sandhi (rāśi-sandhi,
    # bhāva-sandhi), never "sandhya bindu" for a midpoint between two chart points. The live
    # facts confirm what the category actually is: chart_facts rows under
    # fact_category='midpoint' on the canonical chart carry 55 distinct fact_subject values,
    # each a PAIR — and the pairs are not all grahas: alongside SUN-MOON / MAR-SAT / VEN-RAH
    # there are nine ASC-* pairs (ASC-JUP, ASC-SUN, …) and nine MC-* pairs (MC-JUP, MC-SUN,
    # …). Lagna and Madhya-lagna are chart ANGLES, not grahas, so "graha-pair" would be
    # wrong for a third of the family. Keys are longitude_sidereal / sign / sign_lord /
    # house_d1; source_calculation is pyjhora_adapter.sensitive — i.e. the midpoint between
    # two chart points, a Western/Uranian-derived technique with no BPHS antecedent.
    # Per §J and §N.7 item 6 (an honest null beats an invented judgment), the invented
    # Sanskrit parenthetical is removed rather than replaced with a different guess, and the
    # label is scoped to what the data actually contains.
    "midpoint":                      "Chart-Point Pair Midpoint (graha/lagna/MC)",
    "graha_pada_join":               "Graha–Pada Junction",
    "saham_position":                "Saham (Arabic Lot) Position",
    "aprakasha_position":            "Aprakāśa (Dark Body) Position",
    "arudha_pada":                   "Arudha Pāda",
    # ── ga_structural categories ──────────────────────────────────────────────
    "graha_cheshta_bala_per_varga":  "Graha Ceṣṭā Bala per Varga",
    "graha_dignity_per_varga":       "Graha Dignity per Varga",
    "lord_in_house_per_varga":       "House Lord Placement per Varga",
    "lord_aspects_lord_per_varga":   "Inter-Lord Aspect per Varga",
    "karaka_house_lord_overlap_flag":"Kāraka–House-Lord Overlap",
    "argala_natal_matrix":           "Argala (Intervention) Matrix",
    "virodha_argala_natal_matrix":   "Virodha Argala (Counter-Intervention) Matrix",
    "aspect_parashari_natal":        "Pārāśarī Graha Drishti (Natal)",
    "aspect_jaimini_per_varga":      "Jaimini Rāśi Drishti per Varga",
    "bhava_chalit_rasi_divergence":  "Bhāva Chālit vs Rāśi Divergence",
    "graha_shadbala_total":          "Graha Ṣaḍbala (Six-Strength Total)",
    "house_bhava_bala_total":        "Bhāva Bala (House Strength) Total",
    "house_bhava_bala_subscore":     "Bhāva Bala Component Score",
    "panchamahapurusha_yoga":        "Pañcamahāpuruṣa Yoga",
    "maitri_graha_natural":          "Naisargika Graha Maitri (Natural Friendship)",
    # ── ga_positions categories ───────────────────────────────────────────────
    "graha_position":                "Graha Natal Position",
    "varga_position":                "Varga (Divisional) Position",
    # ── ga_structural yoga/condition categories ───────────────────────────────
    "yoga_natal_condition":          "Yoga Condition (Natal)",
    "yoga_fired":                    "Confirmed Yoga Firing",
    "dosha_natal":                   "Dosha (Natal)",
    "bhava_arudha":                  "Bhāva Arudha (Arudha Pāda of House)",
    # ── ga_strength categories ────────────────────────────────────────────────
    "graha_vimsopaka_shadvarga":     "Viṃśopaka Bala (Shadvarga)",
    "graha_vimsopaka_saptavarga":    "Viṃśopaka Bala (Saptavarga)",
    "graha_vimsopaka_dasavarga":     "Viṃśopaka Bala (Daśavarga)",
    "graha_vimsopaka_shodasavarga":  "Viṃśopaka Bala (Ṣoḍaśavarga)",
    "ashtakavarga_bindu":            "Ashtakavarga Bindu (Transit Score)",
    "ashtakavarga_pinda_sodhita":    "Pinda Shodhita (Purified Ashtaka Score)",
    # ── ga_nakshatra categories ───────────────────────────────────────────────
    "graha_nakshatra":               "Graha Nakshatra",
    "nakshatra_pada":                "Nakshatra Pāda",
    # ── ga_sensitive_degree categories ───────────────────────────────────────
    "sensitive_degree_check":        "Sensitive Degree Check (Puṣkara/Gaṇḍānta/Mṛtyu-bhāga/Kartari)",
    # ── ga_panchanga / lagna categories ──────────────────────────────────────
    "lagna_position":                "Lagna (Ascendant) Position",
    "panchanga_element":             "Pañcāṅga Element",
    "tithi":                         "Tithi (Lunar Day)",
    "vara":                          "Vara (Weekday)",
    "nakshatra_of_day":              "Janma Nakshatra",
    # ── ga_tajaka categories ──────────────────────────────────────────────────
    "tajaka_aspect":                 "Tājaka Aspect (Varṣaphala)",
    "tajaka_yoga":                   "Tājaka Yoga (Annual Chart Yoga)",
    # ── ga_special_lagna categories ──────────────────────────────────────────
    "special_lagna":                 "Special Lagna",
    # ── ga_vargas chart_divisionals categories ────────────────────────────────
    "varga_dignity":                 "Varga Dignity",
    "varga_house_lord":              "Varga House Lord",
    "varga_house_occupant":          "Varga House Occupant",
    "varga_vargottama_flag":         "Vargottama Flag",
}

# ── Signal type ID glossary: raw signal_type_id patterns → display labels ────
# signal_type_id is a compound key built by bo_laksana from fact_category + fact_key
# (and optionally graha/varga prefix). The leaked token strings seen in F-114/F-131
# are the fact_category segment. A-14's lint should treat any signal_headline_text
# that contains a bare FACT_CATEGORY_DISPLAY_LABEL.key (the raw snake_case form)
# as a violation.

SIGNAL_TYPE_GLOSSARY: dict[str, str] = {
    # Exact leaked token strings from F-114 evidence
    # (verbatim from pp2-audit/evidence/E2_q1_raw_assess_marriage.json headline texts)
    "graha nakshatra join":              "Graha–Nakshatra Junction",
    "bhrigu nadi point":                 "Bhrigu Nadi Special Point",
    "esoteric point shiva":              "Esoteric Shiva Point",
    "upagraha position":                 "Upagraha (Shadow Planet) Position",
    "midpoint":                          "Chart-Point Pair Midpoint (graha/lagna/MC)",  # see FACT_CATEGORY_DISPLAY_LABEL note
    "graha pada join":                   "Graha–Pada Junction",
    "saham position":                    "Saham (Arabic Lot) Position",
    "aprakasha position":                "Aprakāśa (Dark Body) Position",
    "arudha pada":                       "Arudha Pāda",
    # Exact leaked token strings from F-131 evidence
    # (verbatim from pp2-audit/evidence/E3_read3_timing_trace.json headline texts)
    "graha cheshta bala per varga":      "Graha Ceṣṭā Bala per Varga",
    # Derived from the same F-131 internal-abstention marker pattern
    "no_canonical_per_varga_method":     "[COMPUTATION-ABSTENTION: no canonical classical"
                                         " formula for this varga — not an astrological finding]",
    "floored":                           "[FLOOR-VALUE: computation abstained per §B.10"
                                         " — not an astrological finding]",
}

# ── Internal computation-abstention markers (F-131 remediation) ───────────────
# These strings appearing in a signal_headline_text or signal_summary_text field
# identify rows that are NOT astrological findings — they are internal floor/abstention
# markers written by writers when no verifiable classical formula exists (§B.10 / §N.4).
# A-14's lint and/or the priority-ranking serving layer must EXCLUDE rows matching these
# patterns from the native-facing output (or reclassify them as system-status rows, never
# astrological priority signals).
#
# The F-131 finding: 'graha cheshta bala per varga: D14 = floored:
# no_canonical_per_varga_method [ga_structural]' was ranked #3 by priority_score and
# served as if it were a signal deserving the native's attention right now.

INTERNAL_MARKER_PATTERNS: list[str] = [
    "floored: no_canonical_per_varga_method",
    "no_canonical_per_varga_method",
    "floored:",
    "[COMPUTATION-ABSTENTION",
    "[FLOOR-VALUE",
    "floor_reason=",
    "requires_pass",        # yoga catalog-only rows not yet cross-verified
]

# ── Inverse index: display label → raw fact_category (for display→DB lookups) ─
DISPLAY_LABEL_TO_FACT_CATEGORY: dict[str, str] = {
    v: k for k, v in FACT_CATEGORY_DISPLAY_LABEL.items()
}
