"""The comparator of the station golden (`station_golden_matrix.compare`) — no ephemeris, no database, runs everywhere.

It must be EXACT on everything discrete and tolerant (per kind: occurrences 1e-8 day, station/arc/segment/ingress roots 5e-8 day, longitudes 1e-8 degree) only on continuous values: a platform last-bit difference passes, a missing or an extra
occurrence, a changed discrete value or a time just outside the tolerance fails."""
import copy
import html
import importlib.util
import json
import pathlib

from . import station_golden_matrix as matrix

OCC, ROOT, DEG = matrix.TOLERANCES["occurrence_days"], matrix.TOLERANCES["root_days"], matrix.TOLERANCES["longitude_deg"]


def _cases():
    return {
        "Mars|index": {"n": 1, "rows": [[["S"], [2450000.5]], [["A", 0, 1, 0, True], [2450000.5, 2450010.5, 10.0, 12.0]], [["G", 0, 1, True], [2450000.5, 2450010.5]]]},
        "Mars|domain|conjunction|5.39": {"n": 2, "rows": [[[1, "cid-1", False, "swiss_refined"], [10000.25, 10000.0, 10000.5]],
                                                       [[2, "cid-2", True, "clipped_truncated"], [None, 10100.0, 10100.5]]]},
        "Mars|sign_ingress": {"n": 1, "rows": [[["R", 3], [30.0, 2450005.25, 2450005.2500001]]]},
    }


def test_identical_matrices_have_no_difference():
    assert matrix.compare(_cases(), copy.deepcopy(_cases())) == []


def test_a_platform_difference_inside_each_kinds_tolerance_is_not_a_difference():
    got = _cases()
    got["Mars|domain|conjunction|5.39"]["rows"][0][1][0] += OCC / 2                # an occurrence instant: 0.43 ms
    got["Mars|domain|conjunction|5.39"]["rows"][1][1][2] -= OCC / 2
    got["Mars|index"]["rows"][0][1][0] += ROOT / 2                                  # a station
    got["Mars|index"]["rows"][1][1][1] += ROOT / 2                                  # an arc end instant
    got["Mars|index"]["rows"][2][1][0] += ROOT / 2                                  # a segment start
    got["Mars|index"]["rows"][1][1][2] += DEG / 2                                   # an arc longitude
    got["Mars|sign_ingress"]["rows"][0][1][1] -= ROOT / 2                           # an ingress root
    got["Mars|sign_ingress"]["rows"][0][1][0] += DEG / 2                            # its level
    assert matrix.compare(_cases(), got) == []


def test_a_value_just_outside_its_kinds_tolerance_is_a_difference_for_every_kind_of_continuous_value():
    for case, row, col, amount in (("Mars|domain|conjunction|5.39", 0, 0, 2 * OCC), ("Mars|domain|conjunction|5.39", 0, 1, 2 * OCC), ("Mars|domain|conjunction|5.39", 1, 2, 2 * OCC),
                                   ("Mars|index", 0, 0, 2 * ROOT), ("Mars|index", 1, 0, 2 * ROOT), ("Mars|index", 1, 1, 2 * ROOT), ("Mars|index", 2, 0, 2 * ROOT),
                                   ("Mars|index", 2, 1, 2 * ROOT), ("Mars|index", 1, 2, 2 * DEG), ("Mars|index", 1, 3, 2 * DEG),
                                   ("Mars|sign_ingress", 0, 0, 2 * DEG), ("Mars|sign_ingress", 0, 1, 2 * ROOT), ("Mars|sign_ingress", 0, 2, 2 * ROOT)):
        got = _cases()
        got[case]["rows"][row][1][col] += amount
        assert len(matrix.compare(_cases(), got)) == 1, (case, row, col)


def test_the_tolerances_are_per_kind_occurrences_are_tighter_than_roots():
    assert OCC < ROOT and matrix.kind_of(1, 0) == "occurrence_days" and matrix.kind_of("S", 0) == "root_days" and matrix.kind_of("A", 2) == "longitude_deg"
    root_shift, occurrence_shift = _cases(), _cases()
    root_shift["Mars|index"]["rows"][0][1][0] += 2 * OCC                            # 2e-8: inside the root tolerance ...
    occurrence_shift["Mars|domain|conjunction|5.39"]["rows"][0][1][0] += 2 * OCC    # ... outside the occurrence tolerance
    assert matrix.compare(_cases(), root_shift) == [] and len(matrix.compare(_cases(), occurrence_shift)) == 1


def test_a_missing_or_an_extra_occurrence_is_always_a_failure():
    missing = _cases()
    missing["Mars|domain|conjunction|5.39"]["rows"].pop()
    missing["Mars|domain|conjunction|5.39"]["n"] = 1
    assert any("count 2 -> 1" in p for p in matrix.compare(_cases(), missing))
    extra = _cases()
    extra["Mars|domain|conjunction|5.39"]["rows"].append([[3, "cid-3", False, "swiss_refined"], [1.0, 0.5, 1.5]])
    extra["Mars|domain|conjunction|5.39"]["n"] = 3
    assert any("count 2 -> 3" in p for p in matrix.compare(_cases(), extra))
    rows_only = _cases()                                                    # a count that agrees while the rows do not
    rows_only["Mars|domain|conjunction|5.39"]["rows"].pop()
    assert any("row count" in p for p in matrix.compare(_cases(), rows_only))
    gone = _cases()
    del gone["Mars|sign_ingress"]
    assert any("key set differs" in p for p in matrix.compare(_cases(), gone))
    added = _cases()
    added["Mars|new"] = {"n": 0, "rows": []}
    assert any("key set differs" in p for p in matrix.compare(_cases(), added))


def test_every_discrete_value_is_compared_exactly():
    for case, row, col, value in (("Mars|domain|conjunction|5.39", 0, 0, 9), ("Mars|domain|conjunction|5.39", 0, 1, "cid-x"), ("Mars|domain|conjunction|5.39", 0, 2, True),
                                  ("Mars|domain|conjunction|5.39", 0, 3, "arc_index_bracket"), ("Mars|index", 1, 4, False), ("Mars|index", 1, 2, -1), ("Mars|sign_ingress", 0, 1, 4)):
        got = _cases()
        got[case]["rows"][row][0][col] = value
        assert any("discrete" in p for p in matrix.compare(_cases(), got)), (case, row, col)


def test_none_must_stay_none_and_a_value_must_stay_a_value():
    got = _cases()
    got["Mars|domain|conjunction|5.39"]["rows"][1][1][0] = 10100.25         # t_exact appears on a truncated row
    assert len(matrix.compare(_cases(), got)) == 1
    got = _cases()
    got["Mars|domain|conjunction|5.39"]["rows"][0][1][0] = None
    assert len(matrix.compare(_cases(), got)) == 1


def test_a_non_finite_value_is_a_failure_not_a_pass():
    got = _cases()
    got["Mars|index"]["rows"][0][1][0] = float("nan")
    assert len(matrix.compare(_cases(), got)) == 1


def _refusal(exc):
    return {"n": -1, "rows": [[matrix.refusal_identity(exc), []]]}


def test_a_refusal_must_stay_a_refusal():
    refused = _cases()
    refused["Mars|domain|conjunction|5.39"] = _refusal(RuntimeError("solver defect"))
    assert matrix.compare(_cases(), refused) != [] and matrix.compare(refused, _cases()) != []


def test_a_refusal_is_identified_by_its_type_and_its_message_with_only_the_numbers_masked():
    base = _cases()
    base["Mars|domain|conjunction|5.39"] = _refusal(RuntimeError("Mars: a root [2451545.123456789, 2451546.5] lies outside its own span [2451547.0, 2451548.25] - solver defect"))
    same_text_other_floats = copy.deepcopy(base)
    same_text_other_floats["Mars|domain|conjunction|5.39"] = _refusal(RuntimeError("Mars: a root [2451545.123456781, 2451546.5000000003] lies outside its own span [2451547.0, 2451548.25] - solver defect"))
    assert matrix.compare(base, same_text_other_floats) == []                         # platform last bits inside a message are not a difference
    other_reason = copy.deepcopy(base)
    other_reason["Mars|domain|conjunction|5.39"] = _refusal(RuntimeError("Mars: no station-bounded segment contains the root's arc [2451547.0, 2451548.25] - arc index defect"))
    assert any("discrete" in p for p in matrix.compare(base, other_reason))           # a refusal for a DIFFERENT reason is a different refusal
    other_type = copy.deepcopy(base)
    other_type["Mars|domain|conjunction|5.39"] = _refusal(ValueError("Mars: a root [1.5, 2.5] lies outside its own span [3.5, 4.5] - solver defect"))
    assert any("discrete" in p for p in matrix.compare(base, other_type))
    assert matrix.refusal_identity(RuntimeError("x 1.25 y -3.5e-7 z 12")) == ["REFUSED", "RuntimeError", "x <num> y <num> z 12"]


def test_the_golden_carries_its_provenance_its_tolerances_and_the_measurement_they_rest_on():
    doc = json.loads((pathlib.Path(__file__).resolve().parent / "fixtures" / "station_matrix_golden_main.json").read_text())
    prov = doc["provenance"]
    assert len(prov["source_commit"]) == 40 and prov["source_tree_clean"] is True            # computed on a named, unmodified tree
    assert {"platform", "machine", "python", "numpy", "scipy", "pyswisseph", "generated_at_utc", "generator"} <= set(prov)
    assert set(prov["ephemeris_files_sha256"]) == {"sepl_18.se1", "semo_18.se1", "seas_18.se1"}
    assert doc["schema"] == matrix.SCHEMA and doc["tolerances"] == matrix.TOLERANCES
    measured = prov["cross_environment_measurement"]
    assert measured["tolerances"] == matrix.TOLERANCES and len(measured["pairs"]) == 2 and "ill-conditioned" in measured["reason"]
    for pair in measured["pairs"].values():
        assert pair["discrete_differences"] == 0 and pair["values"] > 60000 and {"platform", "python", "numpy", "scipy", "pyswisseph"} <= set(pair["environment"])
    for kind, headroom in measured["headroom_factor"].items():
        assert headroom >= 3.0, (kind, headroom)                                             # the tolerance is at least 3x the worst measured platform difference


# ── the mutation harness's classification (Astra STATION-ASTRA-2: a message that merely MENTIONS "DID NOT RAISE" is not detection) ──────────────────────────────────────
def _harness():
    path = pathlib.Path(__file__).resolve().parents[4] / "scripts" / "gochara" / "mutation_check_station_refine.py"
    spec = importlib.util.spec_from_file_location("mutation_check_station_refine", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _junit(message, kind="failure"):
    return f'<testsuites><testsuite><testcase classname="t" name="n"><{kind} message="{html.escape(message, quote=True)}">body</{kind}></testcase></testsuite></testsuites>'


def test_the_harness_counts_only_assertion_failures_as_caught():
    h = _harness()
    for message in ("assert 1 == 2", "AssertionError: computation changed", "Failed: DID NOT RAISE <class 'RuntimeError'>"):
        assert h.classify(1, "", _junit(message)) == "CAUGHT", message
    for message in ("psycopg.OperationalError: connection lost while the test said DID NOT RAISE", "TypeError: bad operand (DID NOT RAISE earlier)",
                    "RuntimeError: Failed: DID NOT RAISE was the old text"):
        assert h.classify(1, "", _junit(message)) == "UNEXPECTED-EXCEPTION", message
    assert h.classify(0, "", None) == "SURVIVED" and h.classify(1, "", None).startswith("INFRASTRUCTURE")
