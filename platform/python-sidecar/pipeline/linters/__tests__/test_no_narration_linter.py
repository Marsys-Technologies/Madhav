"""
INF8-S1: No-narration linter tests
[BUILD-ORCH-INF8-S1]
"""

import pytest
from pipeline.linters.no_narration_linter import (
    lint,
    lint_rows,
    check,
    NoNarrationViolationError,
    Violation,
)


# ── Positive cases (violations that MUST be caught) ──────────────────────────

class TestViolationDetection:

    def test_indicates_singular(self):
        with pytest.raises(NoNarrationViolationError) as exc_info:
            lint("Sun in 10H indicates a strong career.")
        assert exc_info.value.violations[0].offending_phrase.lower().startswith('indicate')

    def test_indicates_plural(self):
        with pytest.raises(NoNarrationViolationError):
            lint("These factors indicate wealth accumulation.")

    def test_suggests(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Moon in Cancer suggests emotional sensitivity.")

    def test_implies(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Retrograde Saturn implies delays.")

    def test_means_that(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Lagna lord in 12H means that losses are likely.")

    def test_denotes(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Exaltation denotes maximum strength.")

    def test_reveals(self):
        with pytest.raises(NoNarrationViolationError):
            lint("The chart reveals an artistic temperament.")

    def test_shows(self):
        with pytest.raises(NoNarrationViolationError):
            lint("This placement shows leadership qualities.")

    def test_demonstrates(self):
        with pytest.raises(NoNarrationViolationError):
            lint("The stellium demonstrates concentrated focus.")

    def test_points_to(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Ketu in 9H points to past-life wisdom.")

    def test_signifies(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Jupiter in Lagna signifies wisdom and teaching.")

    def test_represents(self):
        with pytest.raises(NoNarrationViolationError):
            lint("The 10H represents career and public status.")

    def test_symbolizes(self):
        with pytest.raises(NoNarrationViolationError):
            lint("Rahu symbolizes worldly desires and foreign connections.")

    def test_case_insensitive_upper(self):
        with pytest.raises(NoNarrationViolationError):
            lint("INDICATES a strong chart.")

    def test_case_insensitive_mixed(self):
        with pytest.raises(NoNarrationViolationError):
            lint("This SUGGESTS success.")


# ── Negative cases (clean text that must NOT trigger violations) ──────────────

class TestCleanText:

    def test_clean_factual_statement(self):
        lint("Sun: sign=Capricorn house=10 longitude=280.5 nakshatra=Uttara_Ashadha")

    def test_clean_list_format(self):
        lint("| Planet | Sign | House |\n| Sun | Capricorn | 10 |")

    def test_clean_citation(self):
        lint("[FORENSIC §3.1] Sun in Capricorn — birth data verified.")

    def test_clean_number_only(self):
        lint("Shadbala: 423.5 rupas. Rank: 1/9.")

    def test_clean_dasha_record(self):
        lint("Mercury Mahadasha: 2023-04-01 to 2040-04-01. Running period.")

    def test_empty_string(self):
        lint("")

    def test_multi_line_clean(self):
        lint(
            "Sun: Capricorn, 10H\n"
            "Moon: Pisces, 2H\n"
            "Mars: Scorpio, 11H (own sign)\n"
        )

    def test_word_boundary_no_false_positive(self):
        # "showing" should NOT trigger because pattern requires word boundary '\bshows?\b'
        # "showing" = shows + ing — does not match \bshows?\b
        lint("Showing data as requested.")

    def test_word_shows_not_caught_in_showing(self):
        # 'shows?' matches 'show' and 'shows' only (not 'showing')
        lint("The showing of results is complete.")


# ── Line number accuracy ──────────────────────────────────────────────────────

class TestLineNumbers:

    def test_reports_correct_line_number_line_3(self):
        text = "Line 1: clean\nLine 2: clean\nLine 3 indicates a pattern."
        with pytest.raises(NoNarrationViolationError) as exc_info:
            lint(text)
        assert exc_info.value.violations[0].line_number == 3

    def test_reports_first_violation_only_in_strict_mode(self):
        text = "Line 1 indicates X.\nLine 2 suggests Y."
        with pytest.raises(NoNarrationViolationError) as exc_info:
            lint(text, strict=True)
        assert len(exc_info.value.violations) == 1

    def test_reports_all_violations_in_non_strict_mode(self):
        text = "Line 1 indicates X.\nLine 2 suggests Y.\nLine 3 clean."
        with pytest.raises(NoNarrationViolationError) as exc_info:
            lint(text, strict=False)
        assert len(exc_info.value.violations) == 2

    def test_offending_phrase_in_error(self):
        with pytest.raises(NoNarrationViolationError) as exc_info:
            lint("This indicates strength.", source_hint='section_planets')
        err = str(exc_info.value)
        assert 'line 1' in err.lower()
        assert 'indicates' in err.lower()
        assert 'section_planets' in err


# ── check() non-raising variant ──────────────────────────────────────────────

class TestCheck:

    def test_returns_empty_for_clean_text(self):
        violations = check("Sun in Capricorn, 10H.")
        assert violations == []

    def test_returns_violations_list(self):
        violations = check("This indicates something.")
        assert len(violations) == 1
        assert isinstance(violations[0], Violation)
        assert violations[0].line_number == 1
        assert 'indicates' in violations[0].offending_phrase.lower()

    def test_returns_multiple_violations(self):
        violations = check("This indicates X.\nThis suggests Y.")
        assert len(violations) == 2


# ── lint_rows() bulk scanner ──────────────────────────────────────────────────

class TestLintRows:

    def test_empty_rows_no_failures(self):
        result = lint_rows([])
        assert result == []

    def test_clean_rows_no_failures(self):
        rows = [
            {'fact_id': 'f1', 'fact_value_text': 'Sun: Capricorn'},
            {'fact_id': 'f2', 'fact_value_text': 'Moon: Pisces'},
        ]
        result = lint_rows(rows)
        assert result == []

    def test_violating_row_returned(self):
        rows = [
            {'fact_id': 'f1', 'fact_value_text': 'Sun: Capricorn'},
            {'fact_id': 'f2', 'fact_value_text': 'This indicates strong career.'},
        ]
        result = lint_rows(rows)
        assert len(result) == 1
        row_id, violation = result[0]
        assert row_id == 'f2'
        assert 'indicates' in violation.offending_phrase.lower()

    def test_null_text_field_skipped(self):
        rows = [{'fact_id': 'f1', 'fact_value_text': None}]
        result = lint_rows(rows)
        assert result == []

    def test_missing_text_field_skipped(self):
        rows = [{'fact_id': 'f1', 'fact_value_num': 42.0}]
        result = lint_rows(rows)
        assert result == []

    def test_custom_field_name(self):
        rows = [{'id': 'r1', 'content': 'This suggests a strong result.'}]
        result = lint_rows(rows, text_field='content', id_field='id')
        assert len(result) == 1
        assert result[0][0] == 'r1'
