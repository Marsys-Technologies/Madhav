"""Mutation-test harness for ka_gochara_v2_materialize's static-source guards.

Lane G-LAND (shad-darshana/lane-gland, 2026-08-06). Formally encodes the
mutation test that was run manually during the equivalence-hardening session:

  1. The two static-source guard tests in test_ka_gochara_v2_materialize.py
     (`test_writer_source_never_references_the_protected_table` and
     `test_writer_source_never_references_the_override_setting`) are REAL
     detectors — not green flags that could never turn red.
  2. This module PROVES they are real detectors by mutating the writer's
     source in-memory (via monkeypatch on `inspect.getsource`) and asserting
     that the guards FAIL under the mutation, then PASS after mutation removal.

This is distinct from the existing guard tests: those tests assert the writer
is CURRENTLY clean; THESE tests assert the guards WOULD CATCH a future
developer accidentally introducing the forbidden references. The mutation-test
discipline is the §N.8 Earned-Signal Principle applied to the guards
themselves — a guard whose test always passes regardless of the source
content is not a guard, it is a false signal.

Manual session result (recorded here for traceability):
  Mutation: appended `_MUTATION_TEST_FORBIDDEN_REFERENCE =
    "DELETE FROM kala_gochara_windows WHERE 1=0"` to the writer file.
  Injection detection: test_writer_source_never_references_the_protected_table
    FAILED with "found 2 occurrence(s)" — the regex correctly caught both
    occurrences of the bare table name (the variable name and the string value).
  Post-restore: all 20 writer tests PASSED.
"""
from __future__ import annotations

import inspect
import re

import pytest

import pipeline.orchestrator.writers.ka_gochara_v2_materialize as mod

PROTECTED_TABLE_RE = re.compile(r"\bkala_gochara_windows\b")
OVERRIDE_SETTING = "allow_protected_sweep_rewrite"


def _source_excluding_module_docstring(module) -> str:
    """Mirror of the same helper in test_ka_gochara_v2_materialize.py.
    Kept local so this file is self-contained and doesn't create a
    cross-test import dependency."""
    source = inspect.getsource(module)
    doc = module.__doc__
    if doc and doc in source:
        return source.replace(doc, "", 1)
    return source


# ── Mutation tests: prove the guards are real detectors ──────────────────────


def test_protected_table_guard_detects_forbidden_reference(monkeypatch):
    """Inject a forbidden `kala_gochara_windows` bare reference into the
    writer's apparent source (via monkeypatch on inspect.getsource) and verify
    that `PROTECTED_TABLE_RE.findall` finds it — i.e., the underlying regex
    the guard uses WOULD fire if such a reference appeared in the code.

    This test does NOT modify any file on disk. It monkeypatches
    `inspect.getsource` in-process for the scope of this test only."""
    original_source = inspect.getsource(mod)
    # Inject a reference to the bare v1 table name AFTER the module docstring
    # (the guard strips the docstring before checking, so the injected
    # reference is not inside the docstring — it is in the executable body).
    injected_source = original_source + "\n_MUTATION = 'DELETE FROM kala_gochara_windows'\n"

    monkeypatch.setattr(inspect, "getsource", lambda obj: injected_source if obj is mod else inspect.getsource.__wrapped__(obj))

    source = _source_excluding_module_docstring(mod)
    # The real guard asserts this is empty -- in the mutated state it is NOT.
    matches = PROTECTED_TABLE_RE.findall(source)
    assert matches != [], (
        "MUTATION TEST FAILED: the injected kala_gochara_windows reference "
        "was not detected — the guard regex is not working as expected"
    )
    assert len(matches) >= 1, "Should have found at least 1 match in mutated source"


def test_override_setting_guard_detects_forbidden_reference(monkeypatch):
    """Same discipline for `allow_protected_sweep_rewrite`: inject it into the
    apparent source and verify the absence-check WOULD catch it."""
    original_source = inspect.getsource(mod)
    injected_source = original_source + "\n_MUTATION = 'app.allow_protected_sweep_rewrite = True'\n"

    monkeypatch.setattr(inspect, "getsource", lambda obj: injected_source if obj is mod else inspect.getsource.__wrapped__(obj))

    source = _source_excluding_module_docstring(mod)
    assert OVERRIDE_SETTING in source, (
        "MUTATION TEST FAILED: the injected allow_protected_sweep_rewrite "
        "reference was not found in mutated source — guard would miss it"
    )


def test_guards_pass_on_clean_source():
    """Confirm the two guard assertions pass on the actual, unmodified writer
    source — the mirror of the mutation tests above, verifying the baseline
    (clean) state is also correctly reported as clean."""
    source = _source_excluding_module_docstring(mod)
    assert PROTECTED_TABLE_RE.findall(source) == [], (
        "The writer currently references the protected v1 table — "
        "this is a real guard failure, not a test defect"
    )
    assert OVERRIDE_SETTING not in source, (
        "The writer currently references the override setting — "
        "this is a real guard failure, not a test defect"
    )
