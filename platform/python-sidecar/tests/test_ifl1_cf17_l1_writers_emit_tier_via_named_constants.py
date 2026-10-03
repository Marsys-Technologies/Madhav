"""I.FL1 tests-first, HELD until PR #2984 merges: fix CF-17 residual / I-27 -- the L1 writers that
still EMIT a verification tier as a bare string literal.

Rule being tested (CLAUDE.md section N.4, last bullet, S7 ruling; INDEX CF-17 design; decision
Q-L1-16(a)): a writer emits a verification tier / provenance through a named constant
(`brahmagyan.verification_vocab` or its sibling `brahmagyan.verification_tiers`, or the `entry_for()`
lookup the vocabulary documents), never as a quoted string at the emission site.

Scope, stated so the test is not itself an overclaim:

* It looks at EMISSION sites only (CF-17 design: "a quoted tier string assigned to
  verification_pass_status / provenance / verification outside the vocabulary import; comparisons
  allowlisted by reason"): a string literal that is a vocabulary tier word and is (a) the value of a
  dict entry / keyword / assignment / parameter default whose NAME contains `verif`, `provenance`,
  `prov` or `tier`, or (b) a `return` inside a function whose name contains `verif`, `provenance`,
  `prov` or `tier`. A tier word used as a dict KEY (`"floored": True`) or in a comparison is not an
  emission and is not counted (the ratchet in `test_verification_tier_literal_guard.py`, which lives
  in PR #2984, counts every occurrence; this test is the narrower, designed end state).
* Files: `ga_writers/ga_*_writer.py` and `pipeline/orchestrator/writers/ga_*.py`.
* Files that PR #2984 already converts (ga_panchanga, ga_sade_sati, ga_sensitive,
  ga_sensitive_degree, ga_strength, ga_structural, ga_tajaka) are NOT parametrised here: their own
  tests live in #2984. Measured 2026-10-03 on #2984's tip (`git archive`, no checkout): exactly
  four files keep emission literals after it -- ga_ayurdaya (2), ga_condition (5), ga_positions (3),
  ga_vargas (7) -- and those are the xfail cases below. Every other L1 writer file reads 0 today
  and is a plain regression guard.

How the hold works: the four residual cases are `xfail(strict=True)`. CI stays green now. When the
conversion lands, the case XPASSes and strict mode turns that into a loud failure, so the mark has
to be removed in the fix PR -- it cannot be forgotten. Run `pytest --runxfail <this file>` to see
the real failure text on today's code.

No output change: the emitted STRING is identical either way; the defect is the source text's
resilience to drift (a constant can be checked against the vocabulary at import; a literal cannot).
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan import verification_vocab as vocab  # noqa: E402

#: vocabulary members that are tiers (PASS/pass are a different field's check words)
_TIER_WORDS = frozenset(vocab.ALL_STATUSES) - frozenset(vocab.PROHIBITED_STATUSES)

#: names that mark an emission target
_EMIT_NAME = re.compile(r"verif|provenance|(^|_)prov(_|$)|(^|_)tier(_|$)", re.IGNORECASE)

#: Files #2984 converts (their coverage is #2984's); excluded from this file.
_CONVERTED_BY_2984 = frozenset({
    "ga_writers/ga_panchanga_writer.py",
    "ga_writers/ga_sade_sati_writer.py",
    "ga_writers/ga_sensitive_degree_writer.py",
    "ga_writers/ga_sensitive_writer.py",
    "ga_writers/ga_strength_writer.py",
    "ga_writers/ga_structural_writer.py",
    "ga_writers/ga_tajaka_writer.py",
})

#: Files that keep emission literals after #2984 (measured on its tip): the held cases.
_RESIDUAL = (
    "ga_writers/ga_ayurdaya_writer.py",
    "ga_writers/ga_condition_writer.py",
    "ga_writers/ga_positions_writer.py",
    "ga_writers/ga_vargas_writer.py",
)


def _l1_writer_files() -> list[str]:
    out: list[str] = []
    for pattern in ("ga_writers/ga_*_writer.py", "pipeline/orchestrator/writers/ga_*.py"):
        out.extend(p.relative_to(_SIDECAR).as_posix() for p in sorted(_SIDECAR.glob(pattern)))
    return out


_CLEAN_TODAY = tuple(
    rel for rel in _l1_writer_files() if rel not in _RESIDUAL and rel not in _CONVERTED_BY_2984
)


def _str_leaves(node: ast.AST | None) -> list[tuple[str, int]]:
    """String constants a value expression can evaluate to (literal, ternary, or/and)."""
    if node is None:
        return []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [(node.value, node.lineno)]
    if isinstance(node, ast.IfExp):
        return _str_leaves(node.body) + _str_leaves(node.orelse)
    if isinstance(node, ast.BoolOp):
        return [leaf for v in node.values for leaf in _str_leaves(v)]
    return []


def _target_name(t: ast.AST) -> str | None:
    if isinstance(t, ast.Name):
        return t.id
    if isinstance(t, ast.Attribute):
        return t.attr
    if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str):
        return t.slice.value
    return None


def emission_literals(source: str) -> list[tuple[int, str, str]]:
    """(lineno, target-or-function, tier word) for every bare tier literal at an emission site."""
    tree = ast.parse(source)
    found: set[tuple[int, str, str]] = set()

    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and _EMIT_NAME.search(fn.name):
            for r in ast.walk(fn):
                if isinstance(r, ast.Return):
                    for word, line in _str_leaves(r.value):
                        if word in _TIER_WORDS:
                            found.add((line, f"return in {fn.name}()", word))

    for n in ast.walk(tree):
        pairs: list[tuple[str | None, ast.AST | None]] = []
        if isinstance(n, ast.Assign):
            pairs = [(_target_name(t), n.value) for t in n.targets]
        elif isinstance(n, ast.AnnAssign):
            pairs = [(_target_name(n.target), n.value)]
        elif isinstance(n, ast.Dict):
            pairs = [
                (k.value, v) for k, v in zip(n.keys, n.values)
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            ]
        elif isinstance(n, ast.keyword):
            pairs = [(n.arg, n.value)]
        elif isinstance(n, ast.arguments):
            names = n.args + n.kwonlyargs
            defaults = [None] * (len(n.args) - len(n.defaults)) + list(n.defaults) + list(n.kw_defaults)
            pairs = [(a.arg, d) for a, d in zip(names, defaults) if d is not None]
        for name, value in pairs:
            if name and _EMIT_NAME.search(name):
                for word, line in _str_leaves(value):
                    if word in _TIER_WORDS:
                        found.add((line, name, word))
    return sorted(found)


def _read(rel: str) -> str:
    return (_SIDECAR / rel).read_text(encoding="utf-8")


def _explain(rel: str, sites: list[tuple[int, str, str]]) -> str:
    listing = "\n".join(f"  {rel}:{line}  {name} = {word!r}" for line, name, word in sites)
    return (
        f"{len(sites)} bare verification-tier literal(s) at emission sites in {rel}. CLAUDE.md "
        "section N.4 / CF-17: emit the tier through a named constant from "
        "brahmagyan.verification_vocab (UNVERIFIED_DEFAULT, CLASSICAL_MATCH, TWO_PASS_VERIFIED via "
        "two_pass_verdict(), ...) or brahmagyan.verification_tiers, or look it up with "
        "verification_vocab.entry_for(); never a quoted string. The stored value is identical, so "
        "this is a no-output-change fix.\n" + listing
    )


# -- the detector itself must catch what it claims to (mutation proof, runs always) ------------------


def test_detector_flags_bare_emission_and_ignores_constants_keys_and_comparisons():
    bad = (
        "def f(x):\n"
        "    row = {'verification_pass_status': 'single', 'floored': True}\n"
        "    return dict(provenance='classical_match')\n"
        "def _verification_for(x):\n"
        "    return 'single'\n"
        "def g(prov='single'):\n"
        "    pass\n"
    )
    sites = emission_literals(bad)
    assert {(name, word) for _, name, word in sites} == {
        ("verification_pass_status", "single"),
        ("provenance", "classical_match"),
        ("return in _verification_for()", "single"),
        ("prov", "single"),
    }, sites
    good = (
        "from brahmagyan import verification_vocab as V\n"
        "def f(x):\n"
        "    if x.verification_pass_status == 'single':\n"   # a comparison is not an emission
        "        pass\n"
        "    row = {'verification_pass_status': V.UNVERIFIED_DEFAULT, 'floored': True}\n"
        "    return dict(provenance=V.CLASSICAL_MATCH)\n"
    )
    assert emission_literals(good) == []


def test_every_residual_and_converted_path_still_exists():
    """A renamed file must not silently drop out of the parametrisation."""
    for rel in (*_RESIDUAL, *_CONVERTED_BY_2984):
        assert (_SIDECAR / rel).is_file(), f"stale path in this test: {rel}"


# -- the L1 writers that are clean today stay clean (plain regression guard) ---------------------------


@pytest.mark.parametrize("rel", _CLEAN_TODAY)
def test_clean_l1_writer_has_no_bare_tier_literal_at_emission_sites(rel):
    sites = emission_literals(_read(rel))
    assert sites == [], _explain(rel, sites)


# -- the four writers that still emit literals after #2984: HELD ----------------------------------------


@pytest.mark.parametrize("rel", _RESIDUAL)
@pytest.mark.xfail(
    strict=True,
    reason="held until #2984 merges: fix CF-17 residual / I-27 (bare tier literals at emission sites "
           "-> named constants; no output change)",
)
def test_residual_l1_writer_emits_tier_via_named_constants(rel):
    sites = emission_literals(_read(rel))
    assert sites == [], _explain(rel, sites)
