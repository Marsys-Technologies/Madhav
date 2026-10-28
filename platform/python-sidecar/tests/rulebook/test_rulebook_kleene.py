"""E1: strong Kleene truth tables and the NOT_ASSESSED sentinel."""

from __future__ import annotations

import itertools

import pytest

from services.rulebook.ast import NotAssessedError, Tri, k_and, k_not, k_or, render_tri

T, F, NA = Tri.TRUE, Tri.FALSE, Tri.NOT_ASSESSED

AND_TABLE = {
    (T, T): T,
    (T, F): F,
    (T, NA): NA,
    (F, T): F,
    (F, F): F,
    (F, NA): F,
    (NA, T): NA,
    (NA, F): F,
    (NA, NA): NA,
}
OR_TABLE = {
    (T, T): T,
    (T, F): T,
    (T, NA): T,
    (F, T): T,
    (F, F): F,
    (F, NA): NA,
    (NA, T): T,
    (NA, F): NA,
    (NA, NA): NA,
}
NOT_TABLE = {T: F, F: T, NA: NA}


@pytest.mark.parametrize("a,b", list(itertools.product((T, F, NA), repeat=2)))
def test_and_or_tables(a, b):
    assert k_and(a, b) is AND_TABLE[(a, b)]
    assert k_or(a, b) is OR_TABLE[(a, b)]


@pytest.mark.parametrize("a", (T, F, NA))
def test_not_table(a):
    assert k_not(a) is NOT_TABLE[a]


@pytest.mark.parametrize("vals", list(itertools.product((T, F, NA), repeat=3)))
def test_nary_matches_fold(vals):
    assert k_and(*vals) is AND_TABLE[(AND_TABLE[(vals[0], vals[1])], vals[2])]
    assert k_or(*vals) is OR_TABLE[(OR_TABLE[(vals[0], vals[1])], vals[2])]


def test_sentinel_raises_as_bool():
    with pytest.raises(NotAssessedError):
        bool(NA)
    with pytest.raises(NotAssessedError):
        if NA:  # noqa: SIM108 - the point is that this raises
            pass
    assert issubclass(NotAssessedError, TypeError)


def test_true_false_are_not_bools_either():
    for v in (T, F):
        with pytest.raises(TypeError):
            bool(v)


def test_na_is_never_false():
    assert NA is not F
    assert NA != F
    assert render_tri(NA) == "not_assessed"
    assert render_tri(F) == "false"


def test_connectives_reject_python_bools_and_empty():
    with pytest.raises(TypeError):
        k_and(T, True)
    with pytest.raises(TypeError):
        k_or(False)
    with pytest.raises(ValueError):
        k_and()
    with pytest.raises(TypeError):
        Tri.of(1)
    assert Tri.of(True) is T and Tri.of(False) is F
