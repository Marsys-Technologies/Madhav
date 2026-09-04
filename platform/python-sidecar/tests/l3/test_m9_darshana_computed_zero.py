"""
NIRMĀṆA L3-W3 finding M9 (§N.7 item 6) — a computed zero is not a missing value.

THE DEFECT. `ka_kala_darshana` computed its effective score from `conv_score or 0.5`. That is
falsy-coalescing, not null-coalescing: a **computed zero** — an honest "these systems do not
converge in this window" — was silently rewritten to 0.5, a middling, favourable-sounding value
that nothing computed. §N.7 item 6 names exactly this: a fallback chosen for how it reads rather
than for being an established neutral convention, substituting a plausible default for "I don't
know" — except here it substituted for "I do know, and the answer is zero".

MEASURED at the time of the fix: `kala_convergence` holds **793 rows with convergence_score = 0**
and **zero NULLs**. So every firing of that default was mangling a real computed zero, and the
NULL case the expression was ostensibly written for has never occurred.

THE FIX. Zero survives. A genuine NULL is still substituted — the substitution remains an
invention either way — but it is now explicit and LOUD, so if the path ever fires, someone sees it.

This test fails against `conv_score or 0.5`.
"""
from __future__ import annotations

import inspect
import logging

import pytest

from pipeline.orchestrator.writers import ka_kala_darshana as mod


def test_source_no_longer_falsy_coalesces_the_convergence_score() -> None:
    """The specific expression, guarded by shape as well as by behaviour."""
    source = "\n".join(
        line.split("#", 1)[0] for line in inspect.getsource(mod).splitlines()
    )
    assert "conv_score or 0.5" not in source, (
        "falsy-coalescing default restored: a computed convergence_score of 0 would again be "
        "rewritten to 0.5 (§N.7 item 6)"
    )


def test_a_computed_zero_reaches_the_effective_score_unchanged() -> None:
    """
    The behavioural half. `_compute_effective_score(0.0, [])` must not equal
    `_compute_effective_score(0.5, [])` — if it did, the distinction the fix protects would be
    unobservable and the guard above would be cosmetic.
    """
    at_zero = mod._compute_effective_score(0.0, [])
    at_neutral = mod._compute_effective_score(0.5, [])
    assert at_zero != at_neutral, (
        "a computed zero and the 0.5 neutral produce the same effective score, so the M9 "
        "distinction is not observable downstream — re-check _compute_effective_score"
    )
    assert at_zero == pytest.approx(0.0), (
        "a zero convergence score with no obstructions should stay zero"
    )


def test_the_null_substitution_is_loud_if_it_ever_fires(caplog: pytest.LogCaptureFixture) -> None:
    """
    The NULL path is currently unreachable in production (0 NULLs measured). It must never
    become silent again: substituting 0.5 for an absent score is still an invention, so the
    only acceptable form is one that announces itself.
    """
    source = inspect.getsource(mod)
    assert "conv_score is None" in source, "the NULL case must be handled explicitly, not by falsiness"
    # The warning must name the asset and the identifier, so a log reader can find the row.
    warn_block = source[source.index("conv_score is None"):]
    assert "logger.warning" in warn_block[:800], "the NULL substitution must log a warning"
    assert "convergence_id" in warn_block[:800], "the warning must identify which row it mangled"
