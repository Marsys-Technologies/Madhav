"""test_e5_9_footprint_steps.py -- the footprint resolver's cost, bounded DETERMINISTICALLY (E6.1 follow-up hardening, item 1).

The FP2 rounds guarded the resolver against quadratic / exponential blow-ups with wall-clock asserts (`elapsed < 5.0`), which had to be loosened
to blow-up detectors for a loaded CI box. The resolver has its own work counter, `_WriteScan._steps` (bindings + expression nodes visited; the
hard cap is `MAX_RESOLVER_STEPS`, past it a file is NOT scanned), so the right assertion is on the counter: no clock, no flake, and a regression
that makes the resolver do 10x the work on a file shape fails here even when the box is fast enough to hide it from a timer. The wall-clock asserts in
the older files stay as a generous backstop (they still catch work the counter does not count: regex scans of a hostile literal).

Earned signal: a bound that cannot fail proves nothing, so each bound has a mutation test: memoisation disabled (the layered DAG goes exponential) and a
`_step` that counts but never raises (a hostile file runs past the cap). Both must make the bound assertion FAIL.

Offline: ast only; nothing is imported or executed from the sources scanned.
"""
from __future__ import annotations

import ast
import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import suvarna_level_wave as slw  # noqa: E402
from _fp2r3_corpus import COMMENT_PARTIAL, COMMENT_SETS, PARTIAL as PARTIAL3  # noqa: E402
from _fp2r4_corpus import HIDDEN, PARTIAL as PARTIAL4, SETS  # noqa: E402
from test_e5_9_footprint_inverted import _reviewer_dag  # noqa: E402

OWN = 'OWN = "INSERT INTO t_a (x) VALUES (1)"\n'
CAP = slw._WriteScan.MAX_RESOLVER_STEPS

# Measured on this tree (2026-10-03): the 740 reviewer-corpus cases cost at most 2.4 steps per source line; the linear hostile shapes 2 to 3.5; the layered DAG
# (10 names per layer, 7 layers: 70 assignments of 10 terms each, memoised) 28, 66 since the constant evaluator reads each of those names once too. The bounds below are ~2x the measurement: tight enough that a resolver that
# loses a memo or re-walks a class per reference fails, loose enough that an honest new form of a few extra steps does not.
CORPUS_STEPS_PER_LINE = 6
LINEAR_STEPS_PER_LINE = 6
DAG_STEPS_PER_LINE = 100


def work(src: str, *, params: bool = True) -> tuple[int, int, "slw._WriteScan"]:
    """(steps, source lines, the scan) for a module's text: the constructor does the whole provenance pass; `resolve_param_calls({})` is the second stage
    `scan_writer_tables` always runs (no helper table: parameters of the file's own functions are judged at their call sites)."""
    body = textwrap.dedent(src)
    sc = slw._WriteScan(ast.parse(body))
    if params:
        sc.resolve_param_calls({})
    return sc.work_steps, body.count("\n") + 1, sc


def assert_bounded(src: str, per_line: float, *, label: str = "") -> int:
    """The deterministic cost assertion: steps stay under the per-line budget AND under the hard cap (a file inside the cap that still costs more than its
    budget is a performance regression, a file that reached the cap is the capped path, tested on its own)."""
    steps, lines, _ = work(src)
    assert steps <= per_line * lines, (label, "resolver work", steps, "steps for", lines, "lines (budget", per_line, "per line)")
    assert steps <= CAP, (label, steps, CAP)
    return steps


def test_the_counter_is_a_read_only_view_of_the_one_the_cap_reads():
    _, _, sc = work(OWN + "def r(cur):\n    q = 'SELECT 1'\n    cur.execute(q)\n")
    assert sc.work_steps == sc._steps > 0
    with pytest.raises(AttributeError):
        sc.work_steps = 0                                          # a property without a setter: tests cannot reset it, nothing writes it but `_step`


# ───────────────────── the reviewer corpora (FP2 rounds 3 and 4): every case, steps per line ─────────────────────

CORPUS = ([("r3." + k, v) for k, v in sorted(PARTIAL3.items())] + [("r3c." + k, v) for k, v in sorted(COMMENT_PARTIAL.items())]
          + [("r4." + k, v) for k, v in sorted(PARTIAL4.items())] + [("r4h." + k, v) for k, v in sorted(HIDDEN.items())]
          + [("r4s." + k, v[0]) for k, v in sorted(SETS.items())] + [("r3s." + k, v[0]) for k, v in sorted(COMMENT_SETS.items())])


def test_the_corpus_is_the_whole_reviewer_set():
    assert len(CORPUS) == len(PARTIAL3) + len(COMMENT_PARTIAL) + len(PARTIAL4) + len(HIDDEN) + len(SETS) + len(COMMENT_SETS) >= 700
    assert len({k for k, _ in CORPUS}) == len(CORPUS)


def test_every_reviewer_corpus_case_is_resolved_within_its_step_budget():
    worst = []
    for cid, src in CORPUS:
        steps, lines, _ = work(OWN + src)
        worst.append((steps / lines, cid))
        assert steps <= CORPUS_STEPS_PER_LINE * lines, (cid, steps, lines)
        assert steps <= CAP, cid
    assert max(worst)[0] <= CORPUS_STEPS_PER_LINE                  # the measured maximum was 2.4: the budget is a ceiling, not a target


# ───────────────────── the hostile shapes whose wall-clock bounds were loosened ─────────────────────

def _repeat(unit: str, n: int) -> str:
    return unit * n


HOSTILE_LINEAR = {
    "reassigned_name_each_executed": OWN + "def r(cur):\n" + _repeat("    q = 'DELETE FROM a'\n    cur.execute(q)\n", 8000),
    "just_under_the_cap": OWN + "def r(cur):\n" + _repeat("    q = 'SELECT 1'\n    cur.execute(q)\n", 6000),
    "class_with_thousands_of_sql_attributes": ("class B:\n" + "".join(f"    s{i}='DELETE FROM a{i}'\n" for i in range(5000))
                                               + "def run(cur):\n" + "".join(f"    cur.execute(B.s{i})\n" for i in range(5000))),
    "thousands_of_classes_sharing_a_method_name": ("".join(f"class C{i}:\n    sql='DELETE FROM a{i}'\n    def go(self, cur):\n        cur.execute(self.sql)\n"
                                                           for i in range(5000))
                                                  + "def run(cur):\n" + "".join(f"    C{i}().go(cur)\n" for i in range(5000))),
}


@pytest.mark.parametrize("name", sorted(HOSTILE_LINEAR))
def test_a_hostile_linear_file_costs_a_bounded_number_of_steps_per_line(name):
    steps = assert_bounded(HOSTILE_LINEAR[name], LINEAR_STEPS_PER_LINE, label=name)
    assert steps > 0


def test_the_layered_dag_is_memoised_so_its_cost_is_linear_in_its_edges():
    """70 names of 10 terms each: unmemoised resolution walks 10**7 paths; memoised it is each edge once (28 steps per line here)."""
    clean = _reviewer_dag(10, 7).replace("from sqls import Q", "Q = 'SELECT 1'")
    steps = assert_bounded(OWN + clean, DAG_STEPS_PER_LINE, label="layered_dag")
    assert steps < 10 * 7 * 10 * 8                                 # nodes x terms x a few steps per edge (resolver + constant evaluator), never anywhere near b ** levels


def test_a_file_over_the_cap_stops_at_the_cap_with_a_named_reason():
    src = OWN + "def r(cur):\n" + _repeat("    q = 'SELECT 1'\n    cur.execute(q)\n", 25_000)       # ~3.4 steps per statement: well past the 60k cap
    steps, lines, sc = work(src)
    assert any(u.startswith("resolver_work_cap") for u in sc.unresolved), sc.unresolved[:2]
    assert CAP < steps <= CAP + lines, (steps, CAP, lines)         # the counter passed the cap by at most one step per remaining SQL call, never unbounded
    # (the end-to-end reading of this file -- not scanned, never complete -- is test_e5_9_footprint_inverted's)


def test_an_honest_file_just_under_the_cap_is_not_capped():
    steps, _, sc = work(HOSTILE_LINEAR["just_under_the_cap"])
    assert steps < CAP and not sc.unresolved, (steps, sc.unresolved[:1])


# ───────────────────── mutation tests: the bound must be able to fail ─────────────────────

def test_MUTATION_without_memoisation_the_layered_dag_blows_the_step_bound(monkeypatch):
    clean = OWN + _reviewer_dag(10, 7).replace("from sqls import Q", "Q = 'SELECT 1'")
    assert_bounded(clean, DAG_STEPS_PER_LINE)                      # the real resolver passes
    monkeypatch.setattr(slw._WriteScan, "_memoised", lambda self, key, compute: compute())     # every key recomputed on every visit
    steps, lines, _ = work(clean)
    assert steps > DAG_STEPS_PER_LINE * lines                      # 10**7 paths against the cap: the counter shows it long before any clock would
    with pytest.raises(AssertionError, match="resolver work"):
        assert_bounded(clean, DAG_STEPS_PER_LINE)


def test_MUTATION_a_step_that_counts_but_never_raises_runs_a_hostile_file_past_the_cap(monkeypatch):
    src = HOSTILE_LINEAR["reassigned_name_each_executed"] + _repeat("    q = 'SELECT 1'\n    cur.execute(q)\n", 20_000)
    steps, lines, sc = work(src)
    assert any(u.startswith("resolver_work_cap") for u in sc.unresolved) and CAP < steps <= CAP + lines     # the real cap holds the file at the cap

    def counts_only(self):
        self._steps += 1

    monkeypatch.setattr(slw._WriteScan, "_step", counts_only)
    steps2, lines2, _ = work(src)
    assert steps2 > CAP + lines2                                   # the cap is gone: the same file now costs far more than cap + one step per call
    with pytest.raises(AssertionError):
        assert CAP < steps2 <= CAP + lines2, "the cap-respect assertion must fail without the cap"


def test_MUTATION_a_resolver_that_does_four_times_the_work_trips_the_per_line_budget(monkeypatch):
    """A regression that makes every provenance step cost four (here: three extra counted steps per step) must fail the per-line budget on a linear shape
    (a small instance: the multiplied counter must stay under the cap so the per-line bound, not the cap, is what catches it)."""
    src = OWN + "def r(cur):\n" + _repeat("    q = 'SELECT 1'\n    cur.execute(q)\n", 1500)
    assert_bounded(src, LINEAR_STEPS_PER_LINE)
    real = slw._WriteScan._step

    def four_times(self):
        real(self)
        self._steps += 3

    monkeypatch.setattr(slw._WriteScan, "_step", four_times)
    steps, lines, _ = work(src)
    assert steps > LINEAR_STEPS_PER_LINE * lines and steps < CAP
    with pytest.raises(AssertionError, match="resolver work"):
        assert_bounded(src, LINEAR_STEPS_PER_LINE)
