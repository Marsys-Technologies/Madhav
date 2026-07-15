"""Unit tests for bodha_writers/bhavat_bhavam_registry.py (D-1.5b Lane B-4, CR-97).

Run: python -m pytest platform/python-sidecar/bodha_writers/__tests__/test_bhavat_bhavam_registry.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from bodha_writers.bhavat_bhavam_registry import (
    BHAVAT_BHAVAM_MAP,
    ODD_HOUSES,
    EVEN_HOUSES,
    derived_houses,
    is_odd_house,
)


def test_all_twelve_houses_present():
    assert set(BHAVAT_BHAVAM_MAP.keys()) == set(range(1, 13))


@pytest.mark.parametrize("house,expected", [
    (1, (1, 7)),
    (3, (2, 8)),
    (5, (3, 9)),
    (7, (4, 10)),
    (9, (5, 11)),
    (11, (6, 12)),
])
def test_odd_houses_get_the_brief_verbatim_map(house, expected):
    assert derived_houses(house) == expected


@pytest.mark.parametrize("house", [2, 4, 6, 8, 10, 12])
def test_even_houses_receive_nothing(house):
    """Hard rule, not an oversight: even primary houses never get a derived house."""
    assert derived_houses(house) == ()


def test_odd_even_partition_is_exhaustive_and_disjoint():
    assert set(ODD_HOUSES) | set(EVEN_HOUSES) == set(range(1, 13))
    assert set(ODD_HOUSES) & set(EVEN_HOUSES) == set()


def test_is_odd_house():
    for h in ODD_HOUSES:
        assert is_odd_house(h) is True
    for h in EVEN_HOUSES:
        assert is_odd_house(h) is False


def test_invalid_house_raises():
    with pytest.raises(ValueError):
        derived_houses(0)
    with pytest.raises(ValueError):
        derived_houses(13)
