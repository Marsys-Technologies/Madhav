"""
test_ga_sensitive_tier_honesty.py -- Q03 / SS N-62 honest-tier tests for ga_sensitive.

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md (v1.1) §2.1 / §5 (TS-DEFAULT, TS-VERDICT, TS-FLOOR,
TS-EXT). DB-free: drives the real per-ayanamsha builder with a stubbed `compute_chart`
(a fixed fixture chart), so every builder runs through the real `_make_row`.

Each tier assertion is paired with a mutant: the `*_mutant_*` tests demonstrate in-process that
the mutation (constant comparison, deleted verdict, restored default) masks the failure the
assertion is meant to catch; the lane's mutation runs (source text mutated, tests re-run, all
KILLED) are listed in the lane report.
"""
from __future__ import annotations

import collections
import copy
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from brahmagyan import verification_tiers as T  # noqa: E402
from brahmagyan.verification_vocab import two_pass_verdict  # noqa: E402
from ga_writers import ga_sensitive_writer as W  # noqa: E402

CHART_ID = "test-chart-tier-honesty"  # NOT the canonical id -> FORENSIC gate is skipped
AYA_KEY = "lahiri_chitrapaksha"
BUILD_ID = "tier-honesty-build"

# Sun 280.0 -> exact solar-upagraha longitudes (BPHS Ch.3, exact 133 deg 20' constant)
_SUN = 280.0
_DHUMA = (_SUN + 133.0 + 20.0 / 60.0) % 360.0
_VYATIPATA = (360.0 - _DHUMA) % 360.0
_PARIVESHA = (_VYATIPATA + 180.0) % 360.0
_INDRACHAPA = (360.0 - _PARIVESHA) % 360.0
_UPAKETU = (_SUN - 30.0) % 360.0


def _sp(lon: float) -> dict:
    return {"longitude_deg": lon, "sign": "x", "sign_id": 1, "degree_in_sign": lon % 30.0}


def _chart_data() -> dict:
    return {
        "grahas": [
            {"name": "Sun", "longitude_deg": _SUN},
            {"name": "Moon", "longitude_deg": 321.0},
            {"name": "Mars", "longitude_deg": 195.0},
            {"name": "Mercury", "longitude_deg": 275.0},
            {"name": "Jupiter", "longitude_deg": 120.0},
            {"name": "Venus", "longitude_deg": 300.0},
            {"name": "Saturn", "longitude_deg": 210.0},
            {"name": "Rahu", "longitude_deg": 180.0},
            {"name": "Ketu", "longitude_deg": 0.0},
        ],
        "ascendant": {"longitude_deg": 5.0},
        "panchanga": {"vara": 0, "vara_id": 0, "vara_name": "Sunday", "tithi": 3, "nakshatra": 25},
        "positions": {},
        "sensitive_points": {
            "kaala": _sp(304.13),
            "mrityu": _sp(30.0),
            "artha_prabhakara": _sp(45.0),
            "yama": _sp(60.0),
            "gulika": _sp(74.89),
            "maandi": _sp(84.26),
            "dhuma": _sp(_DHUMA),
            "vyatipaata": _sp(_VYATIPATA),
            "parivesha": _sp(_PARIVESHA),
            "indrachaapa": _sp(_INDRACHAPA),
            "upaketu": _sp(_UPAKETU),
        },
        "midheaven": _sp(272.98),
        "special_lagnas": {
            "bhava_lagna": _sp(356.4), "hora_lagna": _sp(60.9), "ghati_lagna": _sp(254.2),
            "vighati_lagna": _sp(197.8), "indu_lagna": _sp(237.1), "sree_lagna": _sp(202.9),
            "pranapada_lagna": _sp(138.4), "bhrigu_bindhu_lagna": _sp(188.0),
            "kunda_lagna": _sp(286.9), "varnada_lagna": _sp(102.4),
        },
    }


_BIRTH = {
    "datetime_iso": "1984-02-05T10:43:00",
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "tz_offset_hours": 5.5,
}


def _build(monkeypatch, chart_data: dict | None = None) -> list[dict]:
    cd = chart_data if chart_data is not None else _chart_data()
    monkeypatch.setattr(W, "compute_chart", lambda inputs, ayanamsha_id: copy.deepcopy(cd))
    monkeypatch.setattr(W, "_derive_is_day_birth", lambda bp: True)
    return W._build_all_sensitive_rows_for_ayanamsha(
        ayanamsha_key=AYA_KEY, ayanamsha_id="lahiri", chart_id=CHART_ID, build_id=BUILD_ID,
        eng_ver="test-eng", birth_params=dict(_BIRTH), prereqs={}, halt_log_path="HALT.md",
    )


@pytest.fixture()
def rows(monkeypatch):
    return _build(monkeypatch)


def _tiers_by_category(rows: list[dict]) -> dict[str, collections.Counter]:
    out: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in rows:
        out[r["fact_category"]][r["verification_pass_status"]] += 1
    return out


def _is_valueless(r: dict) -> bool:
    return (
        r["fact_value_num"] is None and r["fact_value_text"] is None
        and r["fact_value_jsonb"] is None
    )


# ── TS-DEFAULT ────────────────────────────────────────────────────────────────


def test_make_row_default_is_unverified_default():
    """`_make_row()` with no explicit status returns `single` (UNVERIFIED_DEFAULT)."""
    r = W._make_row("midpoint", "X", "k", 1.0, None, None, CHART_ID, AYA_KEY, BUILD_ID, "e")
    assert r["verification_pass_status"] == T.UNVERIFIED_DEFAULT == "single"


def test_only_the_earned_families_differ_from_single(rows):
    """Status set per category equals the audit §2.1 table: TPV only for the five-subject
    upagraha family; floored only for valueless rows; computed_extension only for
    YAMAGANDA_SPHUTA; everything else `single` (plus the pre-existing honest no-value tiers)."""
    allowed_non_single = {
        T.TWO_PASS_VERIFIED: {("upagraha_position", s) for s in
                              ("DHUMA", "VYATIPATA", "PARIVESHA", "INDRACHAPA", "UPAKETU")},
        T.COMPUTED_EXTENSION: {("saturn_derived_point", "YAMAGANDA_SPHUTA")},
    }
    no_value_tiers = {T.FLOORED, T.EXTERNAL_COMPUTATION_REQUIRED, T.SKIPPED_MALFORMED_SOURCE}
    seen = collections.defaultdict(set)
    for r in rows:
        st = r["verification_pass_status"]
        if st in (T.SINGLE, *no_value_tiers):
            continue
        seen[st].add((r["fact_category"], r["fact_subject"]))
    assert dict(seen) == allowed_non_single, dict(seen)


def test_no_two_pass_verified_outside_upagraha_and_none_divergent(rows):
    tpv = [r for r in rows if r["verification_pass_status"] == T.TWO_PASS_VERIFIED]
    assert tpv and {r["fact_category"] for r in tpv} == {"upagraha_position"}
    assert not [r for r in rows if r["verification_pass_status"] == T.DIVERGENT_FLAGGED]


def test_unearned_categories_are_single(rows):
    by_cat = _tiers_by_category(rows)
    for cat in (
        "esoteric_point_bhrigu_bindu", "esoteric_point_yogi", "esoteric_point_avayogi",
        "esoteric_point_mrityu", "esoteric_point_pranapada_sphuta", "saham_position",
        "karaka_chara_position", "karakamsa_position", "swamsa_position", "arudha_pada",
        "bhava_arudha", "midpoint", "kp_ruling_planets_natal", "kp_cuspal_significators",
        "aprakasha_position", "tajik_hadda_lord", "tajik_triraashipathi",
        "tajik_vargottama_specific", "bhrigu_nadi_point", "nakshatra_pada_sensitive",
        "sensitive_point_gulika_mandi", "sun_derived_upagraha", "special_lagna",
        "esoteric_point_sphuta_fertility", "esoteric_point_yogi_system",
    ):
        assert cat in by_cat, f"category {cat} produced no rows in the fixture build"
        non_single = {k: v for k, v in by_cat[cat].items()
                      if k not in (T.SINGLE, T.FLOORED, T.EXTERNAL_COMPUTATION_REQUIRED,
                                   T.SKIPPED_MALFORMED_SOURCE)}
        assert non_single == {}, f"{cat} carries an unearned tier: {non_single}"
        assert sum(by_cat[cat].values()) > 0, cat


def test_yogi_system_rows_are_single_not_literal_tpv(rows):
    ys = [r for r in rows if r["fact_category"] == "esoteric_point_yogi_system"]
    assert ys and {r["verification_pass_status"] for r in ys} == {T.SINGLE}


def test_saturn_derived_and_other_non_upagraha_single(rows):
    for subj in ("GULIKA_LAHIRI", "MANDI", "MAANDI"):
        sel = [r for r in rows if r["fact_category"] == "saturn_derived_point"
               and r["fact_subject"] == subj]
        assert sel and {r["verification_pass_status"] for r in sel} == {T.SINGLE}, subj
    kala = [r for r in rows if r["fact_category"] == "upagraha_position"
            and r["fact_subject"] == "KALA"]
    assert kala and {r["verification_pass_status"] for r in kala} == {T.SINGLE}


# ── TS-EXT ────────────────────────────────────────────────────────────────────


def test_yamaganda_sphuta_is_computed_extension(rows):
    sel = [r for r in rows if r["fact_category"] == "saturn_derived_point"
           and r["fact_subject"] == "YAMAGANDA_SPHUTA"]
    assert sel
    assert {r["verification_pass_status"] for r in sel} == {T.COMPUTED_EXTENSION}


# ── TS-FLOOR ──────────────────────────────────────────────────────────────────


def test_valueless_lal_kitab_and_maharsi_rows_are_floored(rows):
    for cat, key in (("lal_kitab_special_point", "house"),
                     ("maharsi_specific_point", "longitude_sidereal")):
        sel = [r for r in rows if r["fact_category"] == cat and r["fact_key"] == key]
        assert sel, cat
        assert all(_is_valueless(r) for r in sel)
        assert {r["verification_pass_status"] for r in sel} == {T.FLOORED}, cat
        # the stated-absence flag rows are values (text "true"), not floors
        flag = [r for r in rows if r["fact_category"] == cat
                and r["fact_key"] == "absent_prerequisite_flag"]
        assert flag and {r["verification_pass_status"] for r in flag} == {T.SINGLE}


def test_every_valueless_row_has_a_no_value_tier(rows):
    """TS-FLOOR: a row with no num/text/jsonb value is never `single` or TPV."""
    no_value_tiers = {T.FLOORED, T.EXTERNAL_COMPUTATION_REQUIRED, T.SKIPPED_MALFORMED_SOURCE}
    bad = [(r["fact_category"], r["fact_subject"], r["fact_key"], r["verification_pass_status"])
           for r in rows if _is_valueless(r) and r["verification_pass_status"] not in no_value_tiers]
    assert bad == []


def test_floor_mutant_is_caught(rows):
    """MUTANT: stamp a valueless row `single` -> the TS-FLOOR assertion fails."""
    mutated = copy.deepcopy(rows)
    victim = next(r for r in mutated if r["fact_category"] == "lal_kitab_special_point"
                  and r["fact_key"] == "house")
    victim["verification_pass_status"] = T.SINGLE
    no_value_tiers = {T.FLOORED, T.EXTERNAL_COMPUTATION_REQUIRED, T.SKIPPED_MALFORMED_SOURCE}
    bad = [r for r in mutated if _is_valueless(r)
           and r["verification_pass_status"] not in no_value_tiers]
    assert bad, "the TS-FLOOR detector must be able to fail"


# ── TS-VERDICT (upagraha two-pass) ────────────────────────────────────────────

_UPAGRAHA_SUBJECTS = {
    "DHUMA": "dhuma", "VYATIPATA": "vyatipaata", "PARIVESHA": "parivesha",
    "INDRACHAPA": "indrachaapa", "UPAKETU": "upaketu",
}


def _upagraha_tiers(rows: list[dict]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for r in rows:
        if r["fact_category"] == "upagraha_position":
            out[r["fact_subject"]].add(r["verification_pass_status"])
    return out


def test_upagraha_agreeing_paths_earn_two_pass_verified(rows):
    tiers = _upagraha_tiers(rows)
    for subj in _UPAGRAHA_SUBJECTS:
        assert tiers[subj] == {T.TWO_PASS_VERIFIED}, (subj, tiers[subj])
    assert tiers["KALA"] == {T.SINGLE}


def test_upagraha_with_the_real_bphs_constant_residual_still_agrees(monkeypatch):
    """The live residual: PyJHora native is exact (133 deg 20'), BPHS algebra uses 133.333333
    (0.0012" short). That must STILL agree (it is what 175 canon rows rest on)."""
    cd = _chart_data()
    rows_ = _build(monkeypatch, cd)
    dhuma = next(r for r in rows_ if r["fact_category"] == "upagraha_position"
                 and r["fact_subject"] == "DHUMA" and r["fact_key"] == "longitude_sidereal")
    assert 0.0 < dhuma["tolerance_arcsec"] < 0.01
    assert dhuma["verification_pass_status"] == T.TWO_PASS_VERIFIED


@pytest.mark.parametrize("delta_deg", [1.0 / 3600.0, 1.0])
@pytest.mark.parametrize("subj", list(_UPAGRAHA_SUBJECTS))
def test_perturbed_native_is_divergent_flagged(monkeypatch, subj, delta_deg):
    """A 1 arcsec or a 1 degree error in the PyJHora native value must surface."""
    cd = _chart_data()
    key = _UPAGRAHA_SUBJECTS[subj]
    cd["sensitive_points"][key]["longitude_deg"] = (cd["sensitive_points"][key]["longitude_deg"]
                                                    + delta_deg) % 360.0
    rows_ = _build(monkeypatch, cd)
    tiers = _upagraha_tiers(rows_)
    assert tiers[subj] == {T.DIVERGENT_FLAGGED}, tiers[subj]
    # the other four stay verified: the verdict is per subject
    for other in _UPAGRAHA_SUBJECTS:
        if other != subj:
            assert tiers[other] == {T.TWO_PASS_VERIFIED}


def test_upagraha_missing_native_is_floored_not_verified(monkeypatch):
    cd = _chart_data()
    del cd["sensitive_points"]["dhuma"]
    rows_ = _build(monkeypatch, cd)
    sel = [r for r in rows_ if r["fact_category"] == "upagraha_position"
           and r["fact_subject"] == "DHUMA"]
    assert [r["verification_pass_status"] for r in sel] == [T.FLOORED]


def test_verdict_mutant_constant_comparison_is_caught(monkeypatch):
    """MUTANT: replace the comparison with a constant (`two_pass_verdict(x, x)`). The perturbed
    case then stops returning divergent_flagged -> test_perturbed_native_is_divergent_flagged
    would fail. Here we run the mutant and assert it really does mask the perturbation."""
    cd = _chart_data()
    cd["sensitive_points"]["dhuma"]["longitude_deg"] += 1.0
    monkeypatch.setattr(W, "two_pass_verdict", lambda a, b: two_pass_verdict(a, a))
    rows_ = _build(monkeypatch, cd)
    assert _upagraha_tiers(rows_)["DHUMA"] == {T.TWO_PASS_VERIFIED}, (
        "mutant should have masked the divergence (so the real test above would FAIL on it)"
    )


def test_verdict_mutant_comparison_removed_drops_tier(monkeypatch):
    """MUTANT: the comparison is deleted (no verdict stamped) -> the tier is `single`, never
    `two_pass_verified`: the tier can only come from the verdict."""
    real = W._make_row

    def stripped(*a, **k):
        k.pop("verification_pass_status", None)
        return real(*a, **k)

    monkeypatch.setattr(W, "_make_row", stripped)
    rows_ = _build(monkeypatch)
    assert not [r for r in rows_ if r["verification_pass_status"] == T.TWO_PASS_VERIFIED]


def test_divergent_upagraha_halts_the_persist_path(monkeypatch):
    """A divergence is build-fatal (existing guard), so a bad PyJHora value cannot be stored."""
    cd = _chart_data()
    cd["sensitive_points"]["upaketu"]["longitude_deg"] += 1.0
    monkeypatch.setattr(W, "compute_chart", lambda inputs, ayanamsha_id: copy.deepcopy(cd))
    monkeypatch.setattr(W, "_derive_is_day_birth", lambda bp: True)
    monkeypatch.setattr(W, "_insert_rows", lambda conn, rows, commit=False: len(rows))
    with pytest.raises(ValueError, match="divergent_flagged"):
        W.build_ga_sensitive_for_ayanamsha(
            AYA_KEY, "lahiri", CHART_ID, BUILD_ID, None, dict(_BIRTH), {}, "e",
        )


def test_every_tier_ga_sensitive_emits_passes_emit_tier_for_chart_facts(rows):
    """floored / computed_extension / two_pass_verified / single / no-value tiers are all
    vocabulary members the chart_facts choke-point accepts (`data_error` is no longer emitted)."""
    for r in rows:
        T.emit_tier(r["verification_pass_status"], table="chart_facts")
