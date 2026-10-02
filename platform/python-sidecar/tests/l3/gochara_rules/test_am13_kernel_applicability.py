"""AM-13 (ruled) + Codex round 6 R4/R5: activity_kernel@1.1.0 — validated geometry, fail-closed orb, flat lossless
encoding, version-exact dispatch. Assertions run the production registry/evaluator; nothing is re-implemented here."""
import copy
import math
import pathlib
import re

import pytest

from services.gochara_rules import flat_selector as FS
from services.gochara_rules import kernel_factor as K
from services.gochara_rules import registry
from services.gochara_rules.kernel_factor import (
    KernelFactorConfigError, TargetKindMismatch, activity_kernel,
)
from services.gochara_rules.registry import (
    ANGULAR_OBJECT_KINDS, FACTORS, KERNEL_VERSION, RULE_PATHS, RULE_VERSION, SPAN_OBJECT_KINDS,
    SUPERSEDED_FACTORS, SUPERSEDED_PATHS, composite_ref,
)

REF = composite_ref("activity_kernel", KERNEL_VERSION)
MIG = pathlib.Path(__file__).resolve().parents[4] / "migrations"


def ratified_row(monkeypatch, orb=2.0, status="ratified", ref="ruling:nd_orb_x"):
    row = copy.deepcopy(FACTORS[REF])
    row["applicability"]["angular"].update({"orb_deg": orb, "orb_status": status})
    if ref:
        row["applicability"]["angular"]["orb_decision_ref"] = ref
    else:
        row["applicability"]["angular"].pop("orb_decision_ref", None)
    monkeypatch.setitem(FACTORS, REF, row)


def _db_object_kinds():
    sql = (MIG / "1155_gochara_relationship_record.sql").read_text()
    m = re.search(r"kgrr_object_kind_ck CHECK \(object_kind IN\s*\((.*?)\)\)", sql, re.S)
    return set(re.findall(r"'([a-z_]+)'", m.group(1)))


# ── extents: membership from VALIDATED geometry ───────────────────────────────────────────────
def test_sign_and_star_extents_take_the_membership_step_from_the_longitude():
    assert set(SPAN_OBJECT_KINDS) == {"sign_span", "house_span", "star"} and "star" not in ANGULAR_OBJECT_KINDS
    # Libra = span:7 = [180°, 210°); star:1 (Aśvinī) = [0°, 13°20′); star:27 = [346°40′, 360°)
    assert activity_kernel("sign_span", "span:7", factor_ref=REF, body_longitude_deg=180.0)["value"] == 1.0
    assert activity_kernel("sign_span", "span:7", factor_ref=REF, body_longitude_deg=209.999)["value"] == 1.0
    assert activity_kernel("sign_span", "span:7", factor_ref=REF, body_longitude_deg=210.0)["value"] == 0.0      # 0 is a computed value
    assert activity_kernel("house_span", "span:12", factor_ref=REF, body_longitude_deg=359.5)["value"] == 1.0
    assert activity_kernel("star", "star:1", factor_ref=REF, body_longitude_deg=13.3)["value"] == 1.0
    assert activity_kernel("star", "star:1", factor_ref=REF, body_longitude_deg=13.34)["value"] == 0.0
    assert activity_kernel("star", "star:27", factor_ref=REF, body_longitude_deg=359.9)["value"] == 1.0


def test_aspect_ray_membership_uses_the_directed_ray_not_the_body_position():
    # Jupiter at 100° (Cancer) casting its 9th aspect (240°) lands at 340° = Pisces (span:12), not Cancer
    assert activity_kernel("sign_span", "span:12", factor_ref=REF, body_longitude_deg=100.0, aspect_angle_deg=240.0)["value"] == 1.0
    assert activity_kernel("sign_span", "span:4", factor_ref=REF, body_longitude_deg=100.0, aspect_angle_deg=240.0)["value"] == 0.0
    # the ray wraps the seam: 350° + 60° = 50°
    assert activity_kernel("sign_span", "span:2", factor_ref=REF, body_longitude_deg=350.0, aspect_angle_deg=60.0)["value"] == 1.0
    assert activity_kernel("sign_span", "span:2", factor_ref=REF, body_longitude_deg=350.0, aspect_angle_deg=float("nan"))["reason"] == "aspect_angle_invalid"


def test_missing_or_invalid_longitude_is_unqualified_never_outside():
    for lon in (None, float("nan"), float("inf"), -1.0, 360.0, True, "180"):
        r = activity_kernel("sign_span", "span:7", factor_ref=REF, body_longitude_deg=lon)
        assert r["value"] is None and r["reason"] == "body_longitude_missing_or_invalid", lon


# ── R4: the kind/target agreement is a validated contract ─────────────────────────────────────
def test_a_point_mislabelled_as_an_extent_is_refused_not_evaluated():
    with pytest.raises(TargetKindMismatch):
        activity_kernel("house_span", "point:198.52", factor_ref=REF, body_longitude_deg=198.52)    # the Codex bypass
    with pytest.raises(TargetKindMismatch):
        activity_kernel("sign_span", "star:3", factor_ref=REF, body_longitude_deg=10.0)
    with pytest.raises(TargetKindMismatch):
        activity_kernel("star", "span:3", factor_ref=REF, body_longitude_deg=10.0)
    for bad in ("span:0", "span:13", "span:", "span:1.5", "star:28", "star:0", "", None):
        with pytest.raises(TargetKindMismatch):
            activity_kernel("star" if str(bad).startswith("star") else "sign_span", bad, factor_ref=REF, body_longitude_deg=10.0)
    for bad in ("span:7", "point:360", "point:-1", "point:abc", "point:", "star:1"):
        with pytest.raises(TargetKindMismatch):
            activity_kernel("degree_point", bad, factor_ref=REF, body_longitude_deg=10.0)


def test_point_stays_unqualified_until_a_ratified_orb_is_on_the_row():
    for kind in ANGULAR_OBJECT_KINDS:
        r = activity_kernel(kind, "point:198.52", factor_ref=REF, body_longitude_deg=198.52)
        assert r["value"] is None and r["reason"] == "orb_not_ratified", kind
    with pytest.raises(TypeError):                                                       # the evaluator takes no orb
        activity_kernel("degree_point", "point:1.0", factor_ref=REF, body_longitude_deg=1.0, orb_deg=5.0)  # type: ignore[call-arg]


@pytest.mark.parametrize("bad", [0, 0.0, -1, -0.5, float("nan"), float("inf"), float("-inf"), True, "5"])
def test_an_invalid_ratified_orb_fails_closed_and_never_scores(monkeypatch, bad):
    ratified_row(monkeypatch, orb=bad)
    with pytest.raises(KernelFactorConfigError):
        activity_kernel("degree_point", "point:198.52", factor_ref=REF, body_longitude_deg=198.0)


def test_an_orb_without_ratified_status_or_decision_reference_fails_closed(monkeypatch):
    ratified_row(monkeypatch, orb=2.0, status="unratified_nd_orb_open")
    with pytest.raises(KernelFactorConfigError):
        activity_kernel("degree_point", "point:198.52", factor_ref=REF, body_longitude_deg=198.0)
    ratified_row(monkeypatch, orb=2.0, status="ratified", ref=None)
    with pytest.raises(KernelFactorConfigError):
        activity_kernel("degree_point", "point:198.52", factor_ref=REF, body_longitude_deg=198.0)
    # status says ratified but no orb is present
    row = copy.deepcopy(FACTORS[REF]); row["applicability"]["angular"]["orb_status"] = "ratified"
    monkeypatch.setitem(FACTORS, REF, row)
    with pytest.raises(KernelFactorConfigError):
        activity_kernel("degree_point", "point:198.52", factor_ref=REF, body_longitude_deg=198.0)


def test_with_a_ratified_orb_the_angular_kernel_is_linear_and_seam_safe(monkeypatch):
    ratified_row(monkeypatch, orb=2.0)
    assert activity_kernel("degree_point", "point:198.0", factor_ref=REF, body_longitude_deg=198.0)["value"] == 1.0
    assert activity_kernel("degree_point", "point:198.0", factor_ref=REF, body_longitude_deg=199.0)["value"] == 0.5
    assert activity_kernel("saham", "point:198.0", factor_ref=REF, body_longitude_deg=201.0)["value"] == 0.0     # outside the orb: computed 0
    # seam: target 359.5°, body 0.5° ⇒ Δ = 1.0°, not 359°
    assert activity_kernel("degree_point", "point:359.5", factor_ref=REF, body_longitude_deg=0.5)["value"] == 0.5
    # along an aspect ray: Saturn at 150° casting the 10th aspect (270°) reaches 60°; target 61° ⇒ Δ = 1°
    assert activity_kernel("derived_point", "point:61.0", factor_ref=REF, body_longitude_deg=150.0, aspect_angle_deg=270.0)["value"] == 0.5


def test_uncovered_kinds_and_the_1_0_0_row_are_unqualified_never_one():
    r = activity_kernel("varga_position", "anything", factor_ref=REF, body_longitude_deg=10.0)
    assert r["value"] is None and r["reason"] == "object_kind_not_covered_by_applicability"
    old = activity_kernel("sign_span", "span:7", factor_ref=composite_ref("activity_kernel", RULE_VERSION), body_longitude_deg=190.0)
    assert old["value"] is None and old["reason"] == "applicability_undeclared"          # exactly what is stored today
    with pytest.raises(ValueError):
        activity_kernel("sign_span", "span:7", factor_ref=composite_ref("graduated_drishti", KERNEL_VERSION), body_longitude_deg=190.0)
    with pytest.raises(ValueError):
        activity_kernel("sign_span", "span:7", factor_ref=("activity_kernel", "9.9.9"), body_longitude_deg=190.0)


def test_the_result_names_the_factor_version_that_was_asked_for():
    assert activity_kernel("sign_span", "span:7", factor_ref=REF, body_longitude_deg=190.0)["factor"] == REF
    assert activity_kernel("sign_span", "span:7", factor_ref=composite_ref("activity_kernel", RULE_VERSION),
                           body_longitude_deg=190.0)["factor"] == composite_ref("activity_kernel", RULE_VERSION)


def test_every_db_object_kind_is_classified_or_explicitly_left_out():
    declared = set(SPAN_OBJECT_KINDS) | set(ANGULAR_OBJECT_KINDS)
    assert declared <= _db_object_kinds() and _db_object_kinds() - declared == {"varga_position"}


# ── R5: flat, lossless, SQL-admissible encoding ──────────────────────────────────────────────
def test_the_flat_regexes_are_the_ones_in_migration_1154():
    sql = (MIG / "1154_gochara_rule_path_registry.sql").read_text()
    token = re.search(r"ka_gochara_selector_token_ok\(t text\).*?t ~ '([^']+)'", sql, re.S).group(1)
    key = re.search(r"e\.key !~ '([^']+)'", sql).group(1)
    assert token == FS.TOKEN_RE.pattern and key == FS.KEY_RE.pattern


def test_flat_problems_mirrors_the_sql_validator():
    ok = {"operand": "geometry:x", "n": 1, "arr": ["a", "b"], "f": 0.5}
    assert FS.flat_problems(ok) == []
    for bad in ({}, None, [], {"operand": {"nested": "x"}}, {"a": None}, {"a": True}, {"a": []}, {"a": ["Ok"]}, {"A": "x"},
                {"a": "Has Space"}, {"a": float("nan")}, {"a": [1]}, {"a": "1starts_with_digit"}):
        assert FS.flat_problems(bad), bad


@pytest.mark.parametrize("ref", [composite_ref("activity_kernel", KERNEL_VERSION), composite_ref("graduated_drishti", KERNEL_VERSION)])
def test_each_new_factor_row_declares_a_sql_admissible_flat_selector_that_round_trips(ref):
    row = FACTORS[ref]
    flat = row["operand_selector"]
    assert FS.flat_problems(flat) == []
    enc, dec = ((FS.encode_kernel, FS.decode_kernel) if ref[0] == "activity_kernel" else (FS.encode_drishti, FS.decode_drishti))
    assert dec(flat) == row["applicability"]                     # nested form = decode(flat) …
    assert enc(row["applicability"]) == flat                     # … and encode(decode(flat)) == flat: read-back equality
    assert "orb_deg" not in flat and flat["orb_state"] == "unratified_nd_orb_open" if ref[0] == "activity_kernel" else True


def test_a_ratified_orb_round_trips_and_an_unavailable_orb_is_omitted_not_null():
    nested = FS.decode_kernel(FACTORS[REF]["operand_selector"])
    nested["angular"].update({"orb_deg": 2.5, "orb_status": "ratified", "orb_decision_ref": "ruling:nd_orb_1"})
    flat = FS.encode_kernel(nested)
    assert flat["orb_deg"] == 2.5 and flat["orb_decision_ref"] == "ruling:nd_orb_1" and FS.flat_problems(flat) == []
    assert FS.decode_kernel(flat) == nested
    assert "orb_deg" not in FS.encode_kernel(FS.decode_kernel(FACTORS[REF]["operand_selector"]))


def test_the_numeric_form_is_described_as_the_piecewise_function_it_is():
    assert FACTORS[REF]["function"] == "piecewise_step_linear"


# ── immutable versions ───────────────────────────────────────────────────────────────────────
def test_old_rows_are_untouched_and_new_versions_supersede_them():
    old = FACTORS[composite_ref("activity_kernel", RULE_VERSION)]
    assert "applicability" not in old and old["operand"] == "angular distance |Δλ| to exact contact" and old["function"] == "linear"
    for fid in ("activity_kernel", "graduated_drishti"):
        assert SUPERSEDED_FACTORS[composite_ref(fid, RULE_VERSION)]["superseded_by"] == composite_ref(fid, KERNEL_VERSION)
    for pid in ("P3", "P4", "P5"):
        assert SUPERSEDED_PATHS[composite_ref(pid, RULE_VERSION)]["superseded_by"] == composite_ref(pid, KERNEL_VERSION)
        old_p, new_p = RULE_PATHS[composite_ref(pid, RULE_VERSION)], RULE_PATHS[composite_ref(pid, KERNEL_VERSION)]
        assert new_p["rule_version"] == KERNEL_VERSION and new_p["prerequisites"] == old_p["prerequisites"]            # predicates unchanged
        assert {k: v for k, v in new_p.items() if k not in ("rule_version", "soft_factors")} == \
               {k: v for k, v in old_p.items() if k not in ("rule_version", "soft_factors")}
        assert composite_ref("activity_kernel", KERNEL_VERSION) in new_p["soft_factors"]
        assert composite_ref("activity_kernel", RULE_VERSION) not in new_p["soft_factors"]
    assert composite_ref("graduated_drishti", KERNEL_VERSION) in RULE_PATHS[composite_ref("P3", KERNEL_VERSION)]["soft_factors"]
    for pid in ("P1", "P6"):
        assert composite_ref(pid, KERNEL_VERSION) not in RULE_PATHS


def test_every_soft_factor_reference_resolves_and_each_path_names_its_exact_versions():
    for key, path in RULE_PATHS.items():
        for ref in path.get("soft_factors", []):
            assert ref in FACTORS, (key, ref)
    # version-exact: a 1.1.0 path never carries a 1.0.0 kernel/drishti membership
    for pid in ("P3", "P4", "P5"):
        for ref in RULE_PATHS[composite_ref(pid, KERNEL_VERSION)]["soft_factors"]:
            if ref[0] in ("activity_kernel", "graduated_drishti"):
                assert ref[1] == KERNEL_VERSION


# ── Codex round 7 [8] — exact nakṣatra / sign membership at every boundary ──────────────────────────
def _oracle_index(x: float, arc_arcsec: int) -> int:
    """Independent INTEGER-ONLY oracle: x as num/den (every finite float is exactly that), arcseconds compared
    by cross-multiplication — no Fraction, no float division, no shared code with kernel_factor."""
    num, den = x.as_integer_ratio()
    arcsec_num = (num * 3600) % (1_296_000 * den)                  # in units of 1/den arcsecond, within [0, 360°)
    return arcsec_num // (arc_arcsec * den) + 1


def _inside(kind, target, lon, **kw):
    return activity_kernel(kind, target, factor_ref=REF, body_longitude_deg=lon, **kw)["value"] == 1.0


def test_codex_reproduction_star4_at_exactly_forty_degrees():
    # 3 × 13°20′ = 40° exactly: the lower bound of star:4 is inclusive — star:4, never star:3
    assert _inside("star", "star:4", 40.0) is True
    assert _inside("star", "star:3", 40.0) is False


def test_all_27_nakshatra_boundaries_seam_and_adjacent_representable_values():
    seen_boundary_inside = 0
    for n in range(1, 28):
        b = (n - 1) * 40.0 / 3.0                                    # nominal float of the lower boundary (13°20′ = 40/3)
        for x in (b, math.nextafter(b, 360.0), math.nextafter(b, -1.0)):
            if not (0.0 <= x < 360.0):
                continue
            want = _oracle_index(x, 48_000)
            for star in range(1, 28):
                assert _inside("star", f"star:{star}", x) == (star == want), (n, x, star, want)
        if n in (1, 4, 7, 10, 13, 16, 19, 22, 25):                  # boundaries 40·k exactly representable: must be INSIDE star n
            assert _inside("star", f"star:{n}", (n - 1) * 40.0 / 3.0) is True
            seen_boundary_inside += 1
    assert seen_boundary_inside == 9
    # the seam: 0.0 is star 1, the largest float below 360 is star 27
    assert _inside("star", "star:1", 0.0) and _inside("star", "star:27", math.nextafter(360.0, 0.0))
    assert not _inside("star", "star:27", 0.0) and not _inside("star", "star:1", math.nextafter(360.0, 0.0))


def test_all_12_sign_boundaries_exact():
    for n in range(1, 13):
        b = (n - 1) * 30.0
        for x in (b, math.nextafter(b, 360.0), math.nextafter(b, -1.0)):
            if not (0.0 <= x < 360.0):
                continue
            want = _oracle_index(x, 108_000)
            for sign in range(1, 13):
                assert _inside("sign_span", f"span:{sign}", x) == (sign == want), (n, x, sign, want)
        assert _inside("sign_span", f"span:{n}", b) is True        # a sign's lower bound is inclusive, its upper exclusive


def test_aspect_ray_membership_is_exact_across_a_boundary_and_the_seam():
    # 10° + 30° = 40° exactly → star:4 along the ray; 330° + 40° wraps to 10° (seam) without float drift
    assert _inside("star", "star:4", 10.0, aspect_angle_deg=30.0) is True
    assert _inside("star", "star:1", 330.0, aspect_angle_deg=40.0) is True
    assert _inside("sign_span", "span:1", 330.0, aspect_angle_deg=30.0) is True      # 360 → 0: span 1, not span 12
    assert _inside("sign_span", "span:12", 330.0, aspect_angle_deg=29.999999999999) is True


def test_extent_index_matches_the_independent_oracle_on_a_dense_grid():
    for k in range(0, 3601):
        x = k * 0.1
        if x >= 360.0:
            break
        assert K.extent_index(x, None, 48_000) == _oracle_index(x, 48_000)
        assert K.extent_index(x, None, 108_000) == _oracle_index(x, 108_000)


# ── Codex R5 / steward M20261002T020529-6f18 (b): ONE codec; a numeric orb is admissible only with its decision-ref token ──
def _flat(**over):
    flat = copy.deepcopy(FACTORS[REF]["operand_selector"])
    flat.update(over)
    return flat


def test_the_final_flat_key_list_is_the_single_codec_and_the_registry_row_obeys_it():
    flat = FACTORS[REF]["operand_selector"]
    assert set(flat) == set(FS.KERNEL_FLAT_KEYS) and FS.kernel_flat_problems(flat) == []
    assert flat["orb_state"] == FS.ORB_UNRATIFIED and "orb_deg" not in flat and "orb_decision_ref" not in flat    # omitted, never null
    assert FS.encode_kernel(FS.decode_kernel(flat)) == flat                                                       # lossless round trip


def test_a_numeric_orb_needs_ratified_status_and_a_decision_ref():
    ok = _flat(orb_state=FS.ORB_RATIFIED, orb_deg=3.0, orb_decision_ref="ruling:nd_orb_x")
    assert FS.kernel_flat_problems(ok) == [] and FS.encode_kernel(FS.decode_kernel(ok)) == ok
    for bad in (_flat(orb_deg=3.0),                                                                  # number while unratified
                _flat(orb_state=FS.ORB_RATIFIED, orb_deg=3.0),                                      # ratified, no decision ref
                _flat(orb_state=FS.ORB_RATIFIED, orb_decision_ref="ruling:nd_orb_x"),               # ratified, no number
                _flat(orb_state=FS.ORB_RATIFIED, orb_deg=0, orb_decision_ref="ruling:nd_orb_x"),
                _flat(orb_state=FS.ORB_RATIFIED, orb_deg=-1.0, orb_decision_ref="ruling:nd_orb_x"),
                _flat(orb_state=FS.ORB_RATIFIED, orb_deg=float("inf"), orb_decision_ref="ruling:nd_orb_x"),
                _flat(orb_state=FS.ORB_RATIFIED, orb_deg=True, orb_decision_ref="ruling:nd_orb_x"),
                _flat(orb_state="maybe"),
                _flat(orb_decision_ref="ruling:nd_orb_x")):                                          # a ref while unratified
        assert FS.kernel_flat_problems(bad), bad
        with pytest.raises(ValueError):
            FS.decode_kernel(bad)


def test_foreign_key_names_are_refused_a_closed_schema_not_a_guess():
    for k in ("angular_orb_state", "angular_orb_deg", "angular_orb_decision_ref", "span_function", "angular_kinds"):
        assert any("unknown keys" in p for p in FS.kernel_flat_problems(_flat(**{k: "unratified"}))), k
    # and a missing key is refused too
    flat = _flat(); flat.pop("aspect_geometry")
    assert any("missing keys" in p for p in FS.kernel_flat_problems(flat))


def test_encoding_a_numeric_orb_without_a_decision_ref_is_refused():
    nested = FS.decode_kernel(FACTORS[REF]["operand_selector"])
    nested["angular"].update({"orb_deg": 3.0, "orb_status": "ratified"})                              # no orb_decision_ref
    with pytest.raises(ValueError, match="decision_ref"):
        FS.encode_kernel(nested)
