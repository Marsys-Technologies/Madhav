"""Synthetic-only regression tests for the historical confidence review command."""
import io
import json

import pytest

from brahmagyan.bodha.f184_confidence_review import confidence_summary, main


def test_exact_count_and_mean_without_signal_or_source_output():
    result = confidence_summary({"fixture-a": {"match_confidence": 0.5},
                                 "fixture-b": {"match_confidence": 1.0}}, expected_count=2)
    assert result == {"signal_count": 2, "mean_match_confidence": 0.75}


@pytest.mark.parametrize("confidence", [None, True, "0.5", float("nan"), float("inf"), -0.1, 1.1])
def test_missing_or_invalid_confidence_never_becomes_a_default(confidence):
    with pytest.raises(ValueError):
        confidence_summary({"fixture-a": {"match_confidence": confidence}}, expected_count=1)


def test_missing_confidence_and_incomplete_input_fail():
    for signals, count in [({"fixture-a": {}}, 1), ({}, 1), ({}, 0), ({}, True),
                           ({"fixture-a": {"match_confidence": 0.5}}, 2),
                           ({"": {"match_confidence": 0.5}}, 1)]:
        with pytest.raises(ValueError):
            confidence_summary(signals, expected_count=count)


def test_cli_valid_input_is_offline_arithmetic_only(capsys):
    assert main(["--expected-count", "1"], stdin=io.BytesIO(b'{"fixture-a":{"match_confidence":0.5}}')) == 0
    assert json.loads(capsys.readouterr().out) == {"signal_count": 1, "mean_match_confidence": 0.5}


@pytest.mark.parametrize("raw", [b'NOT_PRIVATE_JSON', b'{"fixture-a":{},"fixture-a":{}}',
                                  b'{"fixture-a":{"match_confidence":NaN}}',
                                  b'{"fixture-a":{"match_confidence":null}}'])
def test_cli_refusal_has_no_raw_input_or_identifiers(raw, capsys):
    assert main(["--expected-count", "1"], stdin=io.BytesIO(raw)) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "invalid_confidence_input"}


def test_expected_count_is_explicit(capsys):
    with pytest.raises(SystemExit) as error:
        main([], stdin=io.BytesIO(b'{}'))
    assert error.value.code == 2


def test_deep_json_refuses_with_the_same_fixed_cli_error(capsys):
    raw = b'[' * 2000 + b'0' + b']' * 2000
    assert main(["--expected-count", "1"], stdin=io.BytesIO(raw)) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "invalid_confidence_input"}


def test_huge_integer_confidence_is_a_value_error():
    with pytest.raises(ValueError):
        confidence_summary({"fixture-a": {"match_confidence": 10 ** 10000}}, expected_count=1)
