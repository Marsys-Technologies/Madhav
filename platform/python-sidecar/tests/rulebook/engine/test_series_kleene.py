"""Series (run-length) algebra, and agreement of the series evaluator with the E1 reference semantics."""

from __future__ import annotations

import itertools
import random

import pytest

from services.rulebook.ast import NOT_ASSESSED, And, Not, Or, Pred, Tri, evaluate, k_and, k_not, k_or
from services.rulebook.engine.series import Series

T, F, N = Tri.TRUE, Tri.FALSE, Tri.NOT_ASSESSED


def test_from_values_compresses_and_expands():
    s = Series.from_values([T, T, F, F, F, N, T])
    assert s.starts == [0, 2, 5, 6]
    assert s.expand() == [T, T, F, F, F, N, T]
    assert s.count(F) == 3 and s.count(N) == 1
    assert s.at(4) is F


def test_zip_merges_breakpoints_and_recompresses():
    a = Series.from_values([T, T, F, F])
    b = Series.from_values([T, F, F, F])
    z = Series.zip(k_and, a, b)
    assert z.expand() == [T, F, F, F]
    assert z.starts == [0, 1]


def test_series_validation():
    with pytest.raises(ValueError):
        Series(3, [1], [T])
    with pytest.raises(ValueError):
        Series(3, [0, 0], [T, F])
    with pytest.raises(ValueError):
        Series.zip(k_and, Series.const(3, T), Series.const(4, T))


def _gate():
    p = lambda i: Pred(f"p{i}", "natal_graha", "occupies", "natal", "janma_lagna", {}, graha="surya", bhavas=(1,))
    return Or((And((p(1), Not(p(2)))), p(3))), [f"p{i}" for i in (1, 2, 3)]


def _series_eval(node, env):
    if isinstance(node, Pred):
        return env[node.operand_id]
    if isinstance(node, And):
        return Series.zip(k_and, *(_series_eval(a, env) for a in node.args))
    if isinstance(node, Or):
        return Series.zip(k_or, *(_series_eval(a, env) for a in node.args))
    return _series_eval(node.arg, env).map(k_not)


def test_series_evaluation_equals_reference_evaluate_dayby_day():
    gate, ids = _gate()
    rnd = random.Random(20261029)
    n = 200
    env = {i: Series.from_values([rnd.choice([T, F, N]) for _ in range(n)]) for i in ids}
    got = _series_eval(gate, env).expand()
    for d in range(n):
        assignment = {i: env[i].at(d) for i in ids}
        assert got[d] is evaluate(gate, assignment), d


def test_all_leaf_combinations_match_reference():
    gate, ids = _gate()
    for combo in itertools.product([T, F, N], repeat=3):
        env = {i: Series.const(1, v) for i, v in zip(ids, combo)}
        assert _series_eval(gate, env).at(0) is evaluate(gate, dict(zip(ids, combo)))


def test_not_assessed_is_never_a_bool():
    with pytest.raises(TypeError):
        bool(NOT_ASSESSED)
