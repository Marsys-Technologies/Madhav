"""
test_fact_identity_parser.py — ADHIṢṬHĀNA Campaign A, Lane A5 (THE FACT
IDENTITY INDEX). TDD unit tests for `brahmagyan/fact_identity_parser.py`.

Every case below is a REAL string pulled from a live reconnaissance pass
over `chart_facts` on all three canonical charts (`482012f1-710e-4a25-
994a-93821f5871aa`, `1c826d5a-41cb-4450-b4dc-59d440e5f75a`,
`cb73cd3d-9eba-4220-9902-0de91566e980`) BEFORE this parser was written —
per the lane brief's explicit TDD mandate ("write the test cases from real
observed strings first, watch them fail against no implementation, then
build the parser to pass them"). None of these are synthetic/invented
shapes. See `A5_COVERAGE_REPORT_v1_0.md` for the full shape inventory these
were drawn from.
"""
from __future__ import annotations

import pytest

from brahmagyan.fact_identity_parser import (
    ALL_30_VARGAS,
    IdentityMatch,
    classify_unparsed_subject,
    parse_fact_identity,
)


# ── graha (bare) ──────────────────────────────────────────────────────

@pytest.mark.parametrize("subject,expected_code", [
    ("SUN", "SUN"), ("MOON", "MOON"), ("MAR", "MAR"), ("MER", "MER"),
    ("JUP", "JUP"), ("VEN", "VEN"), ("SAT", "SAT"),
    ("RAH_MEAN", "RAH_MEAN"), ("KET_MEAN", "KET_MEAN"), ("LAGNA", "LAGNA"),
])
def test_bare_graha_subject(subject, expected_code):
    r = parse_fact_identity(subject, "grade", "sambandha_grade")
    assert r == IdentityMatch(
        entity_kind="graha", parse_rule="bare_graha_subject",
        graha_code=expected_code,
    )


def test_bare_graha_long_form_normalizes():
    # 'JUPITER' (long form) observed in graha_avastha_* categories.
    r = parse_fact_identity("JUPITER", "grade", "some_category")
    assert r.graha_code == "JUP"


# ── graha + varga (fact_key carries the varga, subject is bare graha) ──

def test_graha_subject_varga_bare_key():
    r = parse_fact_identity("JUP", "D9", "graha_avastha_baladi_per_varga")
    assert r.entity_kind == "graha_in_varga"
    assert r.graha_code == "JUP"
    assert r.varga_id == "D9"


def test_graha_subject_d_all_key_is_floor_not_a_varga():
    # D_ALL means "all vargas floor row" — NOT a literal varga D<something>.
    # The parser must not misparse this as a varga id (lane brief's
    # explicit warning, drawn from ga_condition_writer.py ~1128).
    r = parse_fact_identity("JUPITER", "D_ALL", "graha_avastha_jagradadi_per_varga")
    assert r.entity_kind == "graha"
    assert r.graha_code == "JUP"
    assert r.varga_id is None
    assert "d_all_floor" in r.parse_rule


# ── graha + house ────────────────────────────────────────────────────

def test_hyphen_graha_house():
    r = parse_fact_identity("MAR-HOUSE_5", "aspects_house", "graha_house_aspect")
    assert r == IdentityMatch(
        entity_kind="graha_in_house", parse_rule="hyphen_graha_house",
        graha_code="MAR", house_num=5,
    )


def test_underscore_graha_in_house():
    r = parse_fact_identity("VEN_IN_HOUSE_9", "some_key", "some_category")
    assert r.entity_kind == "graha_in_house"
    assert r.graha_code == "VEN"
    assert r.house_num == 9


def test_graha_subject_house_bare_key():
    # aspect_parashari_given/received: subject=JUP, key='house_1' (bare,
    # exact match only — must NOT substring-collide with house_10/11/12,
    # the documented DB10 defect class in SIDDHANTA_STATE.md).
    r = parse_fact_identity("JUP", "house_1", "aspect_parashari_given")
    assert r.entity_kind == "graha_in_house"
    assert r.graha_code == "JUP"
    assert r.house_num == 1


@pytest.mark.parametrize("key,expected_house", [
    ("house_1", 1), ("house_10", 10), ("house_11", 11), ("house_12", 12),
])
def test_bare_house_key_no_substring_collision(key, expected_house):
    # The DB10 defect class: 'house_1' must never be matched by a
    # substring/prefix check against 'house_10'/'house_11'/'house_12'.
    # Exact string equality on the whole fact_key value is the fix.
    r = parse_fact_identity("SAT", key, "aspect_parashari_given")
    assert r.house_num == expected_house


def test_house_key_and_house_10_are_distinct_rows():
    r1 = parse_fact_identity("SAT", "house_1", "aspect_parashari_given")
    r10 = parse_fact_identity("SAT", "house_10", "aspect_parashari_given")
    assert r1.house_num == 1
    assert r10.house_num == 10
    assert r1.house_num != r10.house_num


# ── house (bare, no graha) — all 6+ encodings ───────────────────────

@pytest.mark.parametrize("subject,expected_house", [
    ("HOUSE_10", 10), ("HOUSE_07", 7), ("HOUSE_7", 7), ("HOUSE_1", 1),
    ("BHAVA_01", 1), ("BHAVA_12", 12),
    ("CUSP_10", 10), ("CUSP_02", 2),
    ("SARVA-HOUSE_1", 1), ("SARVA-HOUSE_12", 12),
])
def test_bare_house_encodings(subject, expected_house):
    r = parse_fact_identity(subject, "some_key", "some_category")
    assert r.entity_kind == "house"
    assert r.house_num == expected_house
    assert r.graha_code is None


# ── graha + varga (compound subject, underscore + dot) ─────────────

@pytest.mark.parametrize("subject,varga,graha", [
    ("D9_MAR", "D9", "MAR"), ("D108_VEN", "D108", "VEN"),
    ("D60_SAT", "D60", "SAT"), ("D150_JUP", "D150", "JUP"),
    ("D2700_KET_MEAN", "D2700", "KET_MEAN"),
])
def test_varga_graha_underscore_compound(subject, varga, graha):
    r = parse_fact_identity(subject, "dignity_state", "graha_dignity_per_varga")
    assert r == IdentityMatch(
        entity_kind="graha_in_varga", parse_rule="varga_graha_underscore",
        varga_id=varga, graha_code=graha,
    )


def test_varga_graha_dot_compound_precedent_shape():
    # Not observed live (see coverage report), but supported per the
    # ga_vargas_writer.py ~916 `f"{vid}.{subject}"` precedent.
    r = parse_fact_identity("D1.SUN", "sign", "varga_position")
    assert r.entity_kind == "graha_in_varga"
    assert r.varga_id == "D1"
    assert r.graha_code == "SUN"


# ── graha + sign ─────────────────────────────────────────────────────

def test_hyphen_graha_sign():
    r = parse_fact_identity("MOON-SIGN_1", "score", "some_category")
    assert r.entity_kind == "graha_in_sign"
    assert r.graha_code == "MOON"
    assert r.sign_num == 1


# ── varga + house ────────────────────────────────────────────────────

def test_varga_house_long():
    r = parse_fact_identity("D108_HOUSE_10", "total_edges", "convergence_count")
    assert r == IdentityMatch(
        entity_kind="varga_house", parse_rule="varga_house_long",
        varga_id="D108", house_num=10,
    )


def test_varga_house_short():
    r = parse_fact_identity("D60_H5", "lord_placement", "lord_in_house_per_varga")
    assert r == IdentityMatch(
        entity_kind="varga_house", parse_rule="varga_house_short",
        varga_id="D60", house_num=5,
    )


def test_varga_house_pair():
    r = parse_fact_identity("D108_HOUSE_10_to_HOUSE_1", "grade", "sambandha_grade")
    assert r.entity_kind == "varga_house_pair"
    assert r.varga_id == "D108"
    assert r.house_num == 10
    assert r.house_num_secondary == 1


# ── varga + sign (two shapes: numeric and Title-case name) ─────────

def test_varga_sign_numeric():
    r = parse_fact_identity("D9_SIGN_4", "from_sign_1_offset_1", "argala_natal_matrix")
    assert r == IdentityMatch(
        entity_kind="varga_sign", parse_rule="varga_sign_numeric",
        varga_id="D9", sign_num=4,
    )


def test_varga_sign_name():
    r = parse_fact_identity("D2_Leo", "grade", "sambandha_grade")
    assert r.entity_kind == "varga_sign"
    assert r.varga_id == "D2"
    assert r.sign_num == 5  # Leo is the 5th rashi


# ── varga alone (SARVA subject, no graha) ───────────────────────────

def test_varga_bare_key_non_graha_subject():
    r = parse_fact_identity("SARVA", "D9", "ashtakavarga_pinda_sarva_per_varga")
    assert r.entity_kind == "varga"
    assert r.varga_id == "D9"
    assert r.graha_code is None


def test_varga_chart_subject():
    r = parse_fact_identity("D9_CHART", "cluster_id", "chart_cluster")
    assert r.entity_kind == "varga"
    assert r.varga_id == "D9"


def test_varga_domain_word():
    r = parse_fact_identity("D10_wealth", "concordance_value", "karaka_bhava_concordance")
    assert r.entity_kind == "varga_domain"
    assert r.varga_id == "D10"
    assert r.graha_code is None
    assert r.house_num is None  # must NOT fabricate a house from the domain word


def test_bare_domain_word_no_varga():
    r = parse_fact_identity("wealth", "composite_strength", "karakatva_strength_per_significance")
    assert r.entity_kind == "domain"
    assert r.varga_id is None


def test_unknown_lowercase_word_is_not_swallowed_as_domain():
    r = parse_fact_identity("not_a_real_domain_xyz", "some_key", "some_category")
    assert r is None


# ── arudha pada (house-keyed) ────────────────────────────────────────

@pytest.mark.parametrize("subject,expected_house", [
    ("BHAVA_ARUDHA_A1", 1), ("BHAVA_ARUDHA_A12", 12),
    ("BHAVA_ARUDHA_AL", 1),  # AL = Arudha Lagna = A1
    ("ARUDHA_A2", 2), ("ARUDHA_A10", 10),
])
def test_arudha_pada_house_keyed(subject, expected_house):
    r = parse_fact_identity(subject, "sign", "bhava_arudha")
    assert r.entity_kind == "arudha_pada"
    assert r.house_num == expected_house


def test_arudha_pada_graha_keyed_2letter_distinct_from_house_keyed():
    # ARUDHA_JU (2-letter graha shorthand) must NOT be confused with
    # ARUDHA_A<n> (house-keyed) — different Jaimini concept entirely.
    r = parse_fact_identity("ARUDHA_JU", "house_d1", "arudha_pada")
    assert r.entity_kind == "graha_arudha_pada"
    assert r.graha_code == "JUP"
    assert r.house_num is None


@pytest.mark.parametrize("subject,expected_graha", [
    ("ARUDHA_SU", "SUN"), ("ARUDHA_MO", "MOON"), ("ARUDHA_MA", "MAR"),
    ("ARUDHA_ME", "MER"), ("ARUDHA_JU", "JUP"), ("ARUDHA_VE", "VEN"),
    ("ARUDHA_SA", "SAT"),
])
def test_arudha_2letter_all_codes(subject, expected_graha):
    r = parse_fact_identity(subject, "house_d1", "arudha_pada")
    assert r.graha_code == expected_graha


def test_swamsa_house():
    r = parse_fact_identity("SWAMSA_HOUSE_4", "aspected_by_SUN", "aspect_received_by_special_point")
    assert r.entity_kind == "swamsa_house"
    assert r.house_num == 4


# ── graha pairs (four separator conventions) ────────────────────────

def test_hyphen_graha_pair():
    r = parse_fact_identity("MOON-JUP", "orb_deg", "midpoint")
    assert r.entity_kind == "graha_pair"
    assert r.graha_code == "MOON"
    assert r.graha_code_secondary == "JUP"


def test_hyphen_asc_graha_pair_asc_resolves_to_lagna():
    r = parse_fact_identity("ASC-VEN", "orb_deg", "midpoint")
    assert r.graha_code == "LAGNA"
    assert r.graha_code_secondary == "VEN"


def test_hyphen_graha_short_node_forms():
    r = parse_fact_identity("MAR-RAH", "orb_deg", "midpoint")
    assert r.graha_code == "MAR"
    assert r.graha_code_secondary == "RAH_MEAN"


def test_maitri_graha_pair():
    r = parse_fact_identity("MAITRI_JUP_MAR", "compound_relation", "panchadha_maitri")
    assert r.entity_kind == "graha_pair"
    assert r.graha_code == "JUP"
    assert r.graha_code_secondary == "MAR"


def test_bare_underscore_graha_pair():
    r = parse_fact_identity("JUP_VEN", "orb_deg", "conjunction_within_orb")
    assert r.entity_kind == "graha_pair"
    assert r.graha_code == "JUP"
    assert r.graha_code_secondary == "VEN"


def test_graha_v_graha_pair():
    r = parse_fact_identity("VEN_v_MAR", "winner", "graha_yuddha")
    assert r.entity_kind == "graha_pair"
    assert r.graha_code == "VEN"
    assert r.graha_code_secondary == "MAR"


def test_pakka_ghar_graha():
    r = parse_fact_identity("PAKKA_GHAR_JUP", "house", "lal_kitab_special_point")
    assert r.entity_kind == "graha"
    assert r.graha_code == "JUP"


# ── varga + two grahas ──────────────────────────────────────────────

def test_varga_graha_pair():
    r = parse_fact_identity("D2_MAR_VEN", "aspect_type", "conjunction_per_varga")
    assert r.entity_kind == "varga_graha_pair"
    assert r.varga_id == "D2"
    assert r.graha_code == "MAR"
    assert r.graha_code_secondary == "VEN"


def test_varga_graha_pair_nodal_axis():
    r = parse_fact_identity("D60_RAH_MEAN_KET_MEAN", "axis_state", "kala_sarpa_per_varga")
    assert r.entity_kind == "varga_graha_pair"
    assert r.varga_id == "D60"
    assert r.graha_code == "RAH_MEAN"
    assert r.graha_code_secondary == "KET_MEAN"


def test_varga_graha_to_graha_significator_path():
    r = parse_fact_identity("D1_JUP_to_KET_MEAN", "shortest_path_length", "significator_path")
    assert r.entity_kind == "varga_graha_pair"
    assert r.varga_id == "D1"
    assert r.graha_code == "JUP"
    assert r.graha_code_secondary == "KET_MEAN"


# ── identity-free classification (must be explicit, not a silent drop) ──

@pytest.mark.parametrize("subject", [
    "MANDI", "MRITYU_SPHUTA", "BRAHMA_POINT", "SARVA", "CHART",
    "DHWAJA", "BHAVA_LAGNA", "GHATI_LAGNA", "UPAPADA_LAGNA",
    "AGASTYA_SPHUTA", "RP_ASC_LORD", "PANCHAKA_AGNI",
])
def test_known_special_points_are_identity_free_not_unparsed(subject):
    assert parse_fact_identity(subject, "some_key", "some_category") is None
    cls = classify_unparsed_subject(subject, "some_category")
    assert cls is not None
    assert cls != "real_gap"


@pytest.mark.parametrize("subject", [
    "ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "DARAKARAKA", "STRIKARAKA",
])
def test_karaka_roles_are_identity_free(subject):
    assert parse_fact_identity(subject, "graha", "karaka_chara_position") is None
    assert classify_unparsed_subject(subject, "karaka_chara_position") == "jaimini_karaka_role_label"


def test_saham_labels_are_identity_free():
    assert parse_fact_identity("SAHAM_VIVAHA", "value", "saham_position") is None
    assert classify_unparsed_subject("SAHAM_VIVAHA") == "saham_arabic_part_label"


def test_kakshya_index_not_treated_as_house():
    # KAKSHYA_1..8 (ashtakavarga sub-lord order) must NOT be conflated with
    # a bhava/house number — different dimension, same numeral range.
    assert parse_fact_identity("KAKSHYA_1", "lord", "ashtakavarga_kakshya_boundary") is None
    assert classify_unparsed_subject("KAKSHYA_1", "ashtakavarga_kakshya_boundary") == "ashtakavarga_kakshya_index_not_house"


def test_hadda_index_not_treated_as_house():
    # HADDA_1..30+ (Tajik term/degree-boundary index) — well beyond the
    # 1-12 house range, must never be parsed as a house number.
    assert parse_fact_identity("HADDA_30", "lord", "tajik_hadda_lord") is None
    assert classify_unparsed_subject("HADDA_30", "tajik_hadda_lord") == "tajik_hadda_degree_term_index_not_house"


def test_sade_sati_cycle_phase_not_treated_as_lagna_house():
    # Sade Sati phase labels (JANMA/ANUMUKHA/VISHAKHA = 12th/1st/2nd from
    # MOON, not lagna-relative) must not populate house_num (which this
    # index defines as lagna-relative only) — would silently corrupt the
    # column's meaning for every other consumer.
    for subj in ("CYCLE_1", "CYCLE_1.JANMA", "CYCLE_2.VISHAKHA.Q1", "CYCLE_3.ANUMUKHA.RETRO_1"):
        assert parse_fact_identity(subj, "saturn_sign", "sade_sati_phase") is None
        cls = classify_unparsed_subject(subj, "sade_sati_phase")
        assert cls == "sade_sati_cycle_phase_label_moon_relative_not_lagna_house"


def test_dhaiya_subperiod_not_treated_as_lagna_house():
    assert parse_fact_identity("DHAIYA_4H_1", "saturn_sign", "dhaiya_period") is None
    assert classify_unparsed_subject("DHAIYA_4H_1", "dhaiya_period") == "dhaiya_subperiod_label_moon_relative_not_lagna_house"


def test_bhrigu_chakra_index_not_treated_as_house():
    assert parse_fact_identity("BHRIGU_CHAKRA_1", "sign", "bhrigu_nadi_point") is None
    assert classify_unparsed_subject("BHRIGU_CHAKRA_1", "bhrigu_nadi_point") == "bhrigu_nadi_chakra_index_not_house"


def test_yoga_dosha_catalog_labels_are_open_ended_by_category():
    # yoga_label / dosha_label are open-ended classical catalogs — gated by
    # CATEGORY, not a fixed enumerated set, so a brand-new yoga name added
    # by a future writer is still correctly classified without a code
    # change here.
    assert parse_fact_identity("some_brand_new_yoga_name", "yoga_name", "yoga_label") is None
    assert classify_unparsed_subject("some_brand_new_yoga_name", "yoga_label") == "yoga_label_catalog_label"
    assert classify_unparsed_subject("manglik", "dosha_label") == "dosha_label_catalog_label"


def test_reference_lookup_table_rows_not_natal_placement():
    assert parse_fact_identity("TRANSIT_NAK_ANU", "tara_class", "tara_bala_natal_baseline") is None
    assert classify_unparsed_subject("TRANSIT_NAK_ANU") == "fixed_reference_lookup_table_row_not_natal_placement"
    assert classify_unparsed_subject("TRANSIT_SIGN_DHANU") == "fixed_reference_lookup_table_row_not_natal_placement"


def test_panchanga_birth_constants_are_identity_free():
    for subj in ("TITHI_BIRTH", "VARA_BIRTH", "KARANA_BIRTH", "YOGA_BIRTH",
                 "RAHU_KALAM_BIRTH_DAY", "ABHIJIT_MUHURTA_BIRTH_DAY"):
        assert parse_fact_identity(subj, "some_key", "panchanga_x") is None
        assert classify_unparsed_subject(subj) == "panchanga_constant_label"


def test_nakshatra_name_bare_subject_is_out_of_scope_not_a_gap():
    # 'Purva Bhadrapada' — the native's own birth Moon nakshatra (FORENSIC
    # anchor #2) — appears as a bare subject in nakshatra_co_tenancy /
    # nakshatra_conjunction. Nakshatra identity is a genuine fifth
    # dimension outside this lane's graha/house/varga/sign scope. Uses a
    # fact_key that carries no identity of its own ('bodies_list'), unlike
    # the 'co_<GRAHA>_<GRAHA>' key shape covered by
    # test_nakshatra_co_tenancy_graha_pair_key below — that shape DOES
    # parse, via the key, even though the subject alone does not.
    assert parse_fact_identity("Purva Bhadrapada", "bodies_list", "nakshatra_conjunction") is None
    assert classify_unparsed_subject("Purva Bhadrapada") == "nakshatra_name_fifth_dimension_out_of_scope"
    assert parse_fact_identity("Vishakha", "some_other_key", "nakshatra_conjunction") is None
    assert classify_unparsed_subject("Vishakha") == "nakshatra_name_fifth_dimension_out_of_scope"


def test_nakshatra_co_tenancy_graha_pair_key():
    # PARĪKṢAKA A5 acceptance-gate finding (2026-08-08): `nakshatra_co_
    # tenancy`'s fact_key carries a genuine two-graha-pair identity
    # (`co_<GRAHA>_<GRAHA>`) even though fact_subject is an out-of-scope
    # bare nakshatra name. All 12 live rows across the 3 canonical charts,
    # verified by direct query, exercised here.
    for subject, key, g1, g2 in [
        ("Revati", "co_MAR_VEN", "MAR", "VEN"),
        ("Purva Bhadrapada", "co_MER_SUN", "MER", "SUN"),
        ("Vishakha", "co_MAR_SAT", "MAR", "SAT"),
        ("Swati", "co_MER_SUN", "MER", "SUN"),
        ("Vishakha", "co_MER_VEN", "MER", "VEN"),
        ("Swati", "co_SUN_MER", "SUN", "MER"),
    ]:
        r = parse_fact_identity(subject, key, "nakshatra_co_tenancy")
        assert r is not None, f"{subject!r}/{key!r} should parse via the fact_key, not fall through to None"
        assert r.entity_kind == "graha_pair"
        assert r.parse_rule == "co_tenancy_graha_pair_key"
        assert r.graha_code == g1
        assert r.graha_code_secondary == g2
        # The nakshatra-name subject must not leak into any dimension.
        assert r.house_num is None
        assert r.varga_id is None
        assert r.sign_num is None


def test_bare_sign_name_is_parsed_not_identity_free():
    # Sign names ARE in this lane's scope (sign_num) — must be genuinely
    # parsed, not merely recognized-and-discarded like a nakshatra name.
    r = parse_fact_identity("Aquarius", "on_Virgo", "aspect_jaimini")
    assert r is not None
    assert r.entity_kind == "sign"
    assert r.sign_num == 11


def test_unrecognized_subject_is_a_real_gap():
    assert parse_fact_identity("SOME_TOTALLY_UNKNOWN_TOKEN_XYZ123", "k", "c") is None
    assert classify_unparsed_subject("SOME_TOTALLY_UNKNOWN_TOKEN_XYZ123", "c") is None


# ── edge cases ───────────────────────────────────────────────────────

def test_none_subject_returns_none():
    assert parse_fact_identity(None, "key", "cat") is None


def test_empty_subject_returns_none():
    assert parse_fact_identity("", "key", "cat") is None


def test_none_key_does_not_crash():
    r = parse_fact_identity("SUN", None, "graha_position")
    assert r.entity_kind == "graha"


def test_all_house_numbers_1_to_12_round_trip():
    for h in range(1, 13):
        r = parse_fact_identity(f"HOUSE_{h}", "k", "c")
        assert r.house_num == h
        r_padded = parse_fact_identity(f"HOUSE_{h:02d}", "k", "c")
        assert r_padded.house_num == h


# ── drift guard: the mirrored varga set must match the real writer's ───

def test_all_30_vargas_matches_writer_constant():
    """Prevents the mirrored ALL_30_VARGAS constant (kept local to avoid
    this lightweight parser importing ga_vargas_writer's full pyjhora_
    adapter/DB dependency chain) from silently drifting from its source of
    truth. CLAUDE.md §N.7 item 3: 'no wrapper-local constant may shadow an
    L1-computed value ... a constant can drift from its source; a
    reference cannot' — this test IS the reference-equivalent check."""
    from ga_writers.ga_vargas_writer import ALL_30_VARGAS as WRITER_ALL_30_VARGAS
    assert ALL_30_VARGAS == frozenset(WRITER_ALL_30_VARGAS)


# ═════════════════════════════════════════════════════════════════════════
# S-L1 rehearsal P3 (2026-10-03): the four categories the parser had no rule
# for after the S-L1 rebuilds. Every string below is a REAL row shape: the
# subjects/keys come from the rehearsal's own gap listing
# (rehearsal_final/out/gidx_output_final.txt) and the emitting ga_* writers.
# ═════════════════════════════════════════════════════════════════════════

_AV_PLANETS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT")
_AV_CONTRIBUTORS = _AV_PLANETS + ("LAGNA",)


@pytest.mark.parametrize("subject,planet,contributor,sign", [
    ("SUN-CONTRIBUTOR_SUN-SIGN_1", "SUN", "SUN", 1),          # the rehearsal's own gap example
    ("MOON-CONTRIBUTOR_LAGNA-SIGN_12", "MOON", "LAGNA", 12),
    ("SAT-CONTRIBUTOR_MER-SIGN_9", "SAT", "MER", 9),          # schema note: 'SUN-CONTRIBUTOR_MOON-SIGN_9' shape
    ("SUN-CONTRIBUTOR_MOON-SIGN_9", "SUN", "MOON", 9),
])
def test_ashtakavarga_contributor_natural_tuple_is_parsed(subject, planet, contributor, sign):
    r = parse_fact_identity(subject, "bindus", "ashtakavarga_bindu_contributor")
    assert r == IdentityMatch(
        entity_kind="graha_contributor_sign",
        parse_rule="ashtakavarga_contributor_graha_sign",
        graha_code=planet, graha_code_secondary=contributor, sign_num=sign,
    )
    # never tagged as a varga/house row: chart_reader_v4 selects on graha_code+varga_id
    assert r.varga_id is None and r.house_num is None


def test_ashtakavarga_contributor_full_672_grid_round_trips():
    seen = set()
    for p in _AV_PLANETS:
        for c in _AV_CONTRIBUTORS:
            for s in range(1, 13):
                r = parse_fact_identity(f"{p}-CONTRIBUTOR_{c}-SIGN_{s}", "bindus", "ashtakavarga_bindu_contributor")
                assert r is not None, (p, c, s)
                assert (r.graha_code, r.graha_code_secondary, r.sign_num) == (p, c, s)
                seen.add((r.graha_code, r.graha_code_secondary, r.sign_num))
    assert len(seen) == 7 * 8 * 12 == 672


@pytest.mark.parametrize("subject", [
    "SUN-CONTRIBUTOR_SUN-SIGN_0",        # sign out of 1..12 -> DB CHECK would reject; must be a gap, not a crash
    "SUN-CONTRIBUTOR_SUN-SIGN_13",
    "RAH_MEAN-CONTRIBUTOR_SUN-SIGN_1",   # AV has 7 grahas only (CHART_FACTS_SCHEMA applies_to_subjects)
    "SUN-CONTRIBUTOR_RAH_MEAN-SIGN_1",
    "SUN-CONTRIBUTOR_ASC-SIGN_1",        # contributor token is LAGNA after norm_graha, never ASC
    "SUN-CONTRIBUTOR_SUN",
    "SUN-CONTRIBUTOR_-SIGN_1",
])
def test_ashtakavarga_contributor_malformed_is_a_gap_not_a_guess(subject):
    assert parse_fact_identity(subject, "bindus", "ashtakavarga_bindu_contributor") is None
    assert classify_unparsed_subject(subject, "ashtakavarga_bindu_contributor") is None


def test_ashtakavarga_contributor_agrees_with_the_real_writer_subjects():
    """Writer-agreement detector: build real rows with the real writer
    function and require the parser to resolve every one of them."""
    ga_strength_writer = pytest.importorskip("ga_writers.ga_strength_writer")
    names = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    contribs = names + ("Lagna",)
    prastara = {n: {c: [1, 0] * 6 for c in contribs} for n in names}
    bav = {n: [0] * 12 for n in names}
    bav["SARVA"] = [0] * 12
    pinda = {n: {"sodhya": 0, "graha": 0, "raasi": 0} for n in names}
    rows = ga_strength_writer._build_ashtakavarga_rows(
        bav, pinda, "chart", "build", "lahiri_chitrapaksha", "2026-01-01T00:00:00Z",
        "test/0", "single", prastara=prastara,
    )
    contrib_rows = [r for r in rows if r["fact_category"] == "ashtakavarga_bindu_contributor"]
    assert len(contrib_rows) == 672
    for row in contrib_rows:
        m = parse_fact_identity(row["fact_subject"], row["fact_key"], row["fact_category"])
        assert m is not None and m.parse_rule == "ashtakavarga_contributor_graha_sign", row["fact_subject"]


# ── YAMAKANTAKA: the same upagraha family as GULIKA / MANDI ──────────────

@pytest.mark.parametrize("key", [
    "longitude_sidereal", "sign", "sign_lord", "nakshatra", "nakshatra_lord", "pada", "house_d1",
])
def test_yamakantaka_is_classified_like_gulika_and_mandi(key):
    for subj in ("GULIKA", "MANDI", "YAMAKANTAKA"):
        assert parse_fact_identity(subj, key, "sensitive_point_gulika_mandi") is None
    assert classify_unparsed_subject("YAMAKANTAKA", "sensitive_point_gulika_mandi") == \
        classify_unparsed_subject("GULIKA", "sensitive_point_gulika_mandi") == \
        "special_point_or_aggregate_marker"


# ── panchanga_special_yoga_combinations (the YOGA_PANCHAKA gap) ──────────

def test_yoga_panchaka_is_recognised():
    for key in ("combination_name", "active_at_birth_flag", "constituent_facts_jsonb_atomic"):
        assert parse_fact_identity("YOGA_PANCHAKA", key, "panchanga_special_yoga_combinations") is None
    assert classify_unparsed_subject("YOGA_PANCHAKA", "panchanga_special_yoga_combinations") \
        == "special_point_or_aggregate_marker"


def test_special_yoga_subject_set_matches_the_panchang_engine_catalogue():
    """Drift detector (CLAUDE.md N.7/N.8): the recognised YOGA_* subjects are
    exactly the names `panchang_engine/special_yogas.py` can emit, plus the
    pre-existing YOGA_UNKNOWN fallback. A new engine yoga turns this red (and
    G-IDX would show it as a gap) instead of passing silently."""
    import pathlib
    import re
    from brahmagyan.fact_identity_parser import KNOWN_PANCHANGA_SPECIAL_YOGA_SUBJECTS
    src = (pathlib.Path(__file__).resolve().parents[1] / "panchang_engine" / "special_yogas.py").read_text(encoding="utf-8")
    names = set(re.findall(r'_yoga_dict\(\s*"([a-z_]+)"', src))
    assert len(names) == 9, names
    expected = {f"YOGA_{n.upper()}" for n in names}
    assert KNOWN_PANCHANGA_SPECIAL_YOGA_SUBJECTS == expected
    for subj in expected:
        assert classify_unparsed_subject(subj, "panchanga_special_yoga_combinations") == "special_point_or_aggregate_marker"
    assert classify_unparsed_subject("YOGA_UNKNOWN", "panchanga_special_yoga_combinations") == "special_point_or_aggregate_marker"


def test_unknown_special_yoga_name_is_a_gap():
    assert classify_unparsed_subject("YOGA_BRAND_NEW_ENGINE_YOGA", "panchanga_special_yoga_combinations") is None


# ── dasha_scope_cap: ONE explicit new identity-free reason ───────────────

def test_dasha_scope_cap_sentinel_has_its_own_explicit_reason():
    assert parse_fact_identity("PRANA_DASHA", "level_5_not_computed", "dasha_scope_cap") is None
    assert classify_unparsed_subject("PRANA_DASHA", "dasha_scope_cap") == "scope_cap_sentinel"


def test_scope_cap_sentinel_is_narrow_category_and_subject_both_required():
    assert classify_unparsed_subject("PRANA_DASHA", "some_other_category") is None
    assert classify_unparsed_subject("SOOKSHMA_DASHA", "dasha_scope_cap") is None
    assert classify_unparsed_subject("PRANA_DASHA") is None  # no category supplied
