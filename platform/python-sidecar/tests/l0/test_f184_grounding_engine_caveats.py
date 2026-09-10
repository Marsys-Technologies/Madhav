"""
test_f184_grounding_engine_caveats.py
======================================

PARIŚEṢA-V4 F-184 — wire `caveats` through `ground_signal()`.

`ground_signal()` (`brahmagyan/bodha/_grounding_engine.py`) built a plain
7-key `dict[str, Any]` return on both its branches and never read the
`caveats` field that has been present on the in-memory WS-3 rule dict all
along (`load_all_rules()` appends each `data["rules"]` element verbatim —
`caveats` included). This guard is the real-behaviour detector for the fix:
it constructs a signal/rule pair, drives it through the actual scoring path
(`find_best_rule` → `score_match`), and asserts the returned dict carries the
matched rule's own `caveats` value — not a re-derived or hand-typed one
(CLAUDE.md §N.8: a flag/field needs a real detector behind it, or it is
dead weight).

WHAT THIS GUARD DOES **NOT** CLAIM (say the honest scope, per CLAUDE.md
§N.8): `ground_signal()` / `ground_signals()` have no production callers
anywhere in this repository as of this fix — the engine's real outputs are
the frozen static `l2_grounded_batch_{1..6}.py` modules, which this PR does
NOT regenerate (see F184_L2_GROUNDED_BATCH_REGEN_PACKET). So this test
proves the function's return shape is correct; it does not, and cannot,
prove any served surface changed, because none currently reads this
function's output.

A second, independent guard in this file exercises the `load_all_rules()`
`except Exception` fix — a whole rule-corpus YAML file used to be dropped
with a bare `pass`; it must now log at ERROR with the failing filename, so
a corpus break is diagnosable instead of surfacing only as a silently
missing rule three layers downstream.
"""
from __future__ import annotations

import logging

import pytest

from brahmagyan.bodha import _grounding_engine as ge


# ── caveats plumbing ─────────────────────────────────────────────────────────

def _signal(signal_id: str = "SIG.TEST.001") -> dict:
    return {
        "signal_id": signal_id,
        "signal_type": "yoga",
        "classical_source": "BPHS",
        "signal_name": "Test Yoga Signal",
        "entities_involved": [],
        "domains_affected": [],
    }


def _rule(rule_id: str = "TEST.CAVEAT.1", **extra) -> dict:
    rule = {
        "rule_id": rule_id,
        "scope": "yoga",
        "school": "parashari",
        "source_verse": {
            "canonical_id": "BPHS",
            "verse_ref": "1.1",
            "text_excerpt": "x",
        },
        "assertion": "test assertion text long enough words",
        "condition": "test condition",
        "confidence": 0.9,
    }
    rule.update(extra)
    return rule


class TestGroundSignalCaveats:
    def test_matched_rule_caveats_pass_through_verbatim(self):
        """A rule that scores above the GROUNDED threshold and carries a real
        `caveats` string must have that exact string echoed in the result —
        not summarised, not truncated, not re-derived."""
        rule = _rule(caveats="This is a real provenance caveat, verbatim.")
        result = ge.ground_signal(_signal(), [rule])

        # Sanity: this rule really did win the match (score computed from the
        # real scope/school/keyword-overlap algorithm, not assumed).
        assert result["rule_id"] == "TEST.CAVEAT.1"
        assert result["grounding_status"] == "GROUNDED"
        assert result["caveats"] == "This is a real provenance caveat, verbatim."

    def test_matched_rule_with_no_caveats_key_returns_none(self):
        """Most rules in the corpus have no `caveats` at all (or an explicit
        YAML `null`) — the field must be `None`, never a KeyError, never a
        fabricated placeholder string (CLAUDE.md §N.7 item 6)."""
        rule = _rule()  # no "caveats" key
        result = ge.ground_signal(_signal(), [rule])

        assert result["rule_id"] == "TEST.CAVEAT.1"
        assert result["caveats"] is None

    def test_explicit_null_caveats_returns_none(self):
        """`caveats: null` in YAML round-trips to Python `None` via
        `yaml.safe_load` — confirm the plumbing treats that the same as a
        missing key rather than raising."""
        rule = _rule(caveats=None)
        result = ge.ground_signal(_signal(), [rule])

        assert result["caveats"] is None

    def test_no_matching_rule_returns_none_caveats_not_a_crash(self):
        """The UNGROUNDED_NO_MATCH early-return branch has no `best_rule` at
        all — `caveats` must still be present in the returned dict (so every
        consumer can rely on the key always existing) and must be `None`."""
        result = ge.ground_signal(_signal(), [])

        assert result["rule_id"] is None
        assert result["grounding_status"] == "UNGROUNDED_NO_MATCH"
        assert "caveats" in result
        assert result["caveats"] is None

    def test_both_branches_emit_the_same_key_set(self):
        """Regression guard for the shape itself: both return statements in
        `ground_signal()` must emit identical key sets, `caveats` included —
        this is what F-184 was actually missing (7 keys on both branches,
        `caveats` on neither)."""
        matched = ge.ground_signal(_signal(), [_rule(caveats="x")])
        unmatched = ge.ground_signal(_signal(), [])

        assert set(matched.keys()) == set(unmatched.keys())
        assert "caveats" in matched
        assert "caveats" in unmatched


# ── load_all_rules() §N.8 error-logging fix ─────────────────────────────────

class TestLoadAllRulesErrorLogging:
    def test_broken_yaml_file_logs_at_error_with_filename(self, tmp_path, monkeypatch, caplog):
        """Before this fix, `load_all_rules()` swallowed any per-file parse
        exception with a bare `except Exception: pass` — a whole rule file
        could vanish with zero trace. It must now log at ERROR, naming the
        file, so the failure is diagnosable instead of surfacing only as a
        mysteriously-missing rule three layers downstream."""
        bad = tmp_path / "broken_rules.yaml"
        bad.write_text("rules: [unclosed", encoding="utf-8")

        # WS3_DIR is joined with os.path.dirname(__file__) inside
        # load_all_rules(); os.path.join discards the first component when
        # the second is absolute, so pointing WS3_DIR at an absolute tmp_path
        # redirects the real loader's glob without touching the real corpus.
        monkeypatch.setattr(ge, "WS3_DIR", str(tmp_path))

        with caplog.at_level(logging.ERROR, logger=ge.__name__):
            rules = ge.load_all_rules()

        assert rules == []
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert error_records, "expected at least one ERROR log record"
        assert any("broken_rules.yaml" in r.getMessage() for r in error_records)

    def test_one_broken_file_does_not_block_a_valid_sibling(self, tmp_path, monkeypatch, caplog):
        """The per-file try/except must stay scoped to one file — a break in
        one YAML must not prevent a valid sibling file's rules from loading."""
        bad = tmp_path / "broken_rules.yaml"
        bad.write_text("rules: [unclosed", encoding="utf-8")
        good = tmp_path / "good_rules.yaml"
        good.write_text(
            "rules:\n  - rule_id: GOOD.1\n    scope: yoga\n    school: parashari\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(ge, "WS3_DIR", str(tmp_path))

        with caplog.at_level(logging.ERROR, logger=ge.__name__):
            rules = ge.load_all_rules()

        assert [r["rule_id"] for r in rules] == ["GOOD.1"]
        assert any("broken_rules.yaml" in r.getMessage() for r in caplog.records)
