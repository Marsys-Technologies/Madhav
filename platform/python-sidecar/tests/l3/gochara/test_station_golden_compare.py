"""The comparator of the station golden (`station_golden_matrix.compare`) — no ephemeris, no database, runs everywhere.

It must be EXACT on everything discrete and tolerant (1e-7 day / 1e-7 degree) only on continuous values: a platform last-bit difference passes, a missing or an extra
occurrence, a changed discrete value or a time just outside the tolerance fails."""
import copy

from . import station_golden_matrix as matrix

T = matrix.TOLERANCE_DAYS


def _cases():
    return {
        "Mars|index": {"n": 1, "rows": [[["S"], [2450000.5]], [["A", 0, 1, 0, True], [2450000.5, 2450010.5, 10.0, 12.0]], [["G", 0, 1, True], [2450000.5, 2450010.5]]]},
        "Mars|domain|conjunction|5.39": {"n": 2, "rows": [[[1, "cid-1", False, "swiss_refined"], [10000.25, 10000.0, 10000.5]],
                                                       [[2, "cid-2", True, "clipped_truncated"], [None, 10100.0, 10100.5]]]},
        "Mars|sign_ingress": {"n": 1, "rows": [[["R", 3], [30.0, 2450005.25, 2450005.2500001]]]},
    }


def test_identical_matrices_have_no_difference():
    assert matrix.compare(_cases(), copy.deepcopy(_cases())) == []


def test_a_platform_last_bit_difference_is_not_a_difference():
    got = _cases()
    got["Mars|domain|conjunction|5.39"]["rows"][0][1][0] += T / 2           # 4.3 ms
    got["Mars|index"]["rows"][0][1][0] += 1e-12                            # the measured platform order
    got["Mars|index"]["rows"][1][1][2] += matrix.TOLERANCE_DEG / 2
    got["Mars|sign_ingress"]["rows"][0][1][1] -= T / 2
    assert matrix.compare(_cases(), got) == []


def test_a_time_just_outside_the_tolerance_is_a_difference_for_every_kind_of_continuous_value():
    for case, row, col in (("Mars|domain|conjunction|5.39", 0, 0), ("Mars|domain|conjunction|5.39", 1, 2), ("Mars|index", 0, 0), ("Mars|index", 1, 1), ("Mars|index", 2, 1),
                           ("Mars|sign_ingress", 0, 2)):
        got = _cases()
        got[case]["rows"][row][1][col] += 2 * T
        assert len(matrix.compare(_cases(), got)) == 1, (case, row, col)
    got = _cases()
    got["Mars|index"]["rows"][1][1][3] += 2 * matrix.TOLERANCE_DEG        # a longitude column
    assert len(matrix.compare(_cases(), got)) == 1
    got = _cases()
    got["Mars|sign_ingress"]["rows"][0][1][0] += 2 * matrix.TOLERANCE_DEG  # a boundary level
    assert len(matrix.compare(_cases(), got)) == 1


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


def test_a_refusal_must_stay_a_refusal():
    refused = _cases()
    refused["Mars|domain|conjunction|5.39"] = {"n": -1, "rows": [[["REFUSED", "RuntimeError"], []]]}
    assert matrix.compare(_cases(), refused) != [] and matrix.compare(refused, _cases()) != []
