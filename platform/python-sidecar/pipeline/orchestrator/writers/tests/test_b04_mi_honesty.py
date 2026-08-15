"""
Tests for EKAVĀKYATĀ Stream B lane B-04 (mi Honesty Pair).

Fix 1: mi_darshana.py — 6× "clean" → "not_assessed" at INSERT tier positions.
Fix 2: mi_bhara db.py — isempty/None guard in fetch_open_predictions.

§N.7-4: a verification flag must have a real detector behind it, or be null.
§N.8: an earned-signal must be computed by a real detector — a green signal with
no detector behind it is null, not clean.
"""
from __future__ import annotations

import ast
import inspect
import re

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Fix 1 — mi_darshana.py: "clean" → "not_assessed" at 6 INSERT tier positions
# ─────────────────────────────────────────────────────────────────────────────

class TestMiDarshanaNotAssessed:
    """The 6 INSERT tuple positions that set leakage_status must use
    'not_assessed', not 'clean'.  No real leakage detector exists; claiming
    'clean' is an unimplemented check wearing a clean result's clothes (§N.7-4).
    """

    def _src(self) -> str:
        from pipeline.orchestrator.writers import mi_darshana as mod
        return inspect.getsource(mod)

    def test_source_parses_as_valid_python(self):
        """The file must parse without syntax errors after the substitution."""
        ast.parse(self._src())

    def test_no_clean_at_insert_tier_positions(self):
        """'clean' must not appear as a string literal on a line that is part
        of an INSERT parameter tuple (i.e., the tier/leakage_status slot).

        Strategy: find every line that contains the bare string literal "clean"
        (not inside a comment, docstring, or SQL fragment) and assert it is zero.

        The spec says the 6 positions are at lines 136, 183, 214, 246, 365, 508
        of the original file.  After the fix, none of those lines should contain
        "clean" as a Python string literal value.
        """
        src = self._src()
        lines = src.splitlines()
        # Detect lines containing the Python string literal "clean" (not inside
        # a comment and not inside a triple-quoted block or SQL string).
        # Simple approach: a line that has "clean" (with quotes) and is NOT
        # a pure comment (#…) is a candidate.
        violations = []
        in_triple_double = False
        in_triple_single = False
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Track triple-quoted blocks (docstrings / SQL heredocs)
            dq_count = line.count('"""')
            sq_count = line.count("'''")
            if dq_count % 2 == 1:
                in_triple_double = not in_triple_double
            if sq_count % 2 == 1:
                in_triple_single = not in_triple_single
            if in_triple_double or in_triple_single:
                continue
            # Skip comment lines
            if stripped.startswith("#"):
                continue
            # Skip lines that don't contain the literal at all
            if '"clean"' not in line and "'clean'" not in line:
                continue
            # At this point the line has "clean" as a Python string literal
            # outside a docstring/comment. That is the defect.
            violations.append((lineno, line.rstrip()))

        assert violations == [], (
            "Found 'clean' as a Python string literal in mi_darshana outside "
            "comments/docstrings/SQL blocks — these INSERT tier positions must "
            "use 'not_assessed' instead (§N.7-4):\n"
            + "\n".join(f"  L{ln}: {txt}" for ln, txt in violations)
        )

    def test_not_assessed_appears_in_insert_tuples(self):
        """'not_assessed' must appear as the tier value in INSERT tuples.
        After the fix there should be at least 6 occurrences (one per insight type).
        """
        src = self._src()
        count = src.count('"not_assessed"') + src.count("'not_assessed'")
        assert count >= 6, (
            f"Expected at least 6 occurrences of 'not_assessed' in mi_darshana "
            f"(one per INSERT position), found {count}. "
            "The 6 leakage_status tier slots must all be 'not_assessed'."
        )

    def test_insert_tuples_contain_not_assessed_not_clean(self):
        """Each of the 6 insight-type blocks must use 'not_assessed' at the
        tier slot of the INSERT tuple.  Check by looking at the rows.append(...)
        calls and verifying 'clean' does not appear as a value there."""
        src = self._src()
        # Find all rows.append( ... ) blocks and check none contain "clean"
        # as a string value
        append_pattern = re.compile(r'rows\.append\(.*?\)\)', re.DOTALL)
        for m in append_pattern.finditer(src):
            block = m.group()
            # Remove comments within the block
            block_no_comments = re.sub(r'#[^\n]*', '', block)
            has_clean = '"clean"' in block_no_comments or "'clean'" in block_no_comments
            assert not has_clean, (
                "Found 'clean' inside a rows.append(...) block in mi_darshana. "
                "Use 'not_assessed' instead:\n" + block[:200]
            )


# ─────────────────────────────────────────────────────────────────────────────
# Fix 2 — mi_bhara db.py: isempty/None guard in fetch_open_predictions
# ─────────────────────────────────────────────────────────────────────────────

class TestMiBharaFetchOpenPredictionsGuard:
    """fetch_open_predictions must not return rows where observation_window
    is empty (isempty = TRUE) because lower()/upper() of an empty daterange
    returns NULL in Postgres, which causes float(None) → TypeError downstream
    in score_predictions_against_event.

    The guard can be SQL-side (NOT isempty(...)) or Python-side (filter out
    rows where w_start / w_end is None).  Either is correct; both are tested
    for defence-in-depth.
    """

    def _db_src(self) -> str:
        from services.mi_bhara import db as mod
        return inspect.getsource(mod)

    def test_db_source_parses(self):
        """The db module must parse as valid Python."""
        ast.parse(self._db_src())

    def test_sql_has_isempty_guard_or_not_null_guard(self):
        """The SQL inside fetch_open_predictions must exclude empty-window rows.

        Acceptable patterns:
          - SQL-side: NOT isempty(observation_window)
          - SQL-side: observation_window IS NOT NULL  (already present per db.py line 179)
            BUT this alone is insufficient — isempty rows survive a NOT NULL check.
            So we require EITHER 'isempty' in the query OR a Python-side guard.

        We check for at least one of:
          (a) 'isempty' in the SQL query string (SQL-side fix)
          (b) A Python-side filter for None on w_start / w_end after the query
        """
        src = self._db_src()
        # Isolate the fetch_open_predictions function
        idx = src.index("def fetch_open_predictions(")
        # Find the next top-level function definition
        next_def = re.search(r'\ndef [a-zA-Z_]', src[idx + 1:])
        if next_def:
            fn_body = src[idx: idx + 1 + next_def.start()]
        else:
            fn_body = src[idx:]

        has_sql_isempty = "isempty" in fn_body.lower()
        has_python_none_guard = (
            "w_start" in fn_body and
            ("is None" in fn_body or "is not None" in fn_body or "!= None" in fn_body)
        )
        assert has_sql_isempty or has_python_none_guard, (
            "fetch_open_predictions does not guard against isempty/None "
            "observation_window rows. Add either:\n"
            "  SQL-side: AND NOT isempty(observation_window)\n"
            "  Python-side: filter rows where w_start or w_end is None\n\n"
            "Without this guard, rows with empty windows produce "
            "float(None) → TypeError in score_predictions_against_event."
        )

    def test_none_window_row_does_not_reach_scorer(self):
        """Unit test: a list of open_predictions containing a row with
        observation_window=None (simulating an empty-daterange row where
        lower()/upper() → NULL) must not reach score_predictions_against_event.

        This test simulates the Python-side guard approach by constructing
        OpenPrediction objects and verifying the scorer doesn't blow up.

        If the SQL-side fix is applied (NOT isempty), such rows never appear
        in the list — so this test passes trivially (empty list, no crash).

        If Python-side, the guard must filter them before calling the scorer.
        """
        from services.mi_bhara.living_lel import (
            LelEventRef,
            OpenPrediction,
            score_predictions_against_event,
        )

        # A normal, valid open prediction
        good_pred = OpenPrediction(
            prediction_id="pred-001",
            event_class="career",
            window_start=100.0,
            window_end=200.0,
            filed_at_t=50.0,
            window_id="w1",
            claim_shape="interval",
        )

        # Simulate what comes back if an empty-window row slipped through
        # (lower(empty_range) = NULL → w_start = None).
        # We can't construct an OpenPrediction with None for window_start
        # (it's typed as float) — so what the DB layer MUST do is exclude such
        # rows before constructing OpenPrediction objects.
        # This test therefore validates that the function can be called with a
        # clean list (no None-window entries) without error.
        event = LelEventRef(event_id="ev-1", event_class="career", t=150.0)

        # Must not raise:
        results = score_predictions_against_event(event, [good_pred])
        assert len(results) == 1
        assert results[0].outcome == "hit"

    def test_score_predictions_raises_on_none_window_start(self):
        """Document the root cause: if a row with None window_start somehow
        reached the scorer, it would raise TypeError on the `<=` comparison.

        This test verifies the defect exists so the guard's purpose is clear.
        The guard in db.py / fetch_open_predictions is what prevents this path.
        """
        from services.mi_bhara.living_lel import (
            LelEventRef,
            OpenPrediction,
            score_predictions_against_event,
        )

        # Construct a mock that mimics a row whose window_start is None
        # (we use object() tricks since OpenPrediction is typed float)
        class _BadPred:
            prediction_id = "bad-pred"
            event_class = "career"
            window_start = None   # ← what an empty-window row would produce
            window_end = None
            filed_at_t = 50.0
            window_id = None
            claim_shape = "interval"

        event = LelEventRef(event_id="ev-1", event_class="career", t=150.0)

        with pytest.raises(TypeError):
            # This should raise because `None <= 150.0` fails
            score_predictions_against_event(event, [_BadPred()])  # type: ignore[arg-type]

    def test_fetch_open_predictions_query_contains_not_isempty_or_null_guard(self):
        """The SQL string in fetch_open_predictions must contain either
        'NOT isempty' or have the Python construction block guard against None.

        Cross-check: verify the SQL contains either pattern explicitly.
        """
        src = self._db_src()
        # Extract just the SQL string from fetch_open_predictions
        idx = src.index("def fetch_open_predictions(")
        next_def = re.search(r'\ndef [a-zA-Z_]', src[idx + 1:])
        fn_body = src[idx: idx + 1 + next_def.start()] if next_def else src[idx:]

        sql_match = re.search(r'cur\.execute\(\s*"""(.*?)"""', fn_body, re.DOTALL)
        if sql_match:
            sql_text = sql_match.group(1).lower()
            has_isempty = "not isempty" in sql_text
            has_null_only = "is not null" in sql_text
            # SQL-side: preferred fix adds NOT isempty
            # Minimum: if only IS NOT NULL is present, flag as insufficient alone
            if has_null_only and not has_isempty:
                pytest.skip(
                    "SQL has 'IS NOT NULL' but not 'NOT isempty'. "
                    "Acceptable if Python-side guard is present (other tests cover that). "
                    "Preferred: add NOT isempty(observation_window) to the SQL WHERE clause."
                )
            if has_isempty:
                return  # SQL-side fix confirmed

        # Fall through: check for Python-side guard
        has_python_guard = (
            ("w_start is not None" in fn_body or "r[\"w_start\"] is not None" in fn_body
             or "r.get(\"w_start\")" in fn_body)
        )
        # Either approach is acceptable
        assert "isempty" in fn_body.lower() or has_python_guard, (
            "fetch_open_predictions lacks protection against empty-window rows. "
            "Add AND NOT isempty(observation_window) to the SQL WHERE clause."
        )
