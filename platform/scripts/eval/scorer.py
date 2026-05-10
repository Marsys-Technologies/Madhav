"""
scorer.py — eval-harness scoring functions.

Three primitives:
  - keyword_recall_score: case-insensitive substring presence
  - signal_recall_score:  exact MSR.NNN / SIG.MSR.NNN match
  - synthesis_score:      Haiku-as-judge against gold_answer_summary

Plus a weighted_score combiner that respects per-fixture weights.

Haiku model id is sourced from platform/src/lib/models/registry.ts
(`TITLE_MODEL_ID = 'claude-haiku-4-5'`) — read at import time, no
hardcoded literal here.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

# ── Haiku model resolution (from codebase, not a literal) ─────────────────────

REGISTRY_PATH_REL = "platform/src/lib/models/registry.ts"
HAIKU_RE = re.compile(r"TITLE_MODEL_ID\s*=\s*'([^']+)'")


def resolve_haiku_model(repo_root: Path | None = None) -> str:
    """
    Read the Haiku model id from the TS registry. Falls back to a documented
    default only if the file is unreadable, and prints a warning to stderr.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    registry = repo_root / REGISTRY_PATH_REL
    try:
        m = HAIKU_RE.search(registry.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    except OSError as err:
        print(f"[scorer] WARNING: could not read {registry}: {err}", file=sys.stderr)
    print(
        f"[scorer] WARNING: Haiku model not found in {registry}; "
        "falling back to claude-haiku-4-5",
        file=sys.stderr,
    )
    return "claude-haiku-4-5"


HAIKU_MODEL = resolve_haiku_model()

# ── Primitive scorers ─────────────────────────────────────────────────────────

SIG_RE = re.compile(r"\bSIG\.MSR\.(\d{1,4})\b|\bMSR\.(\d{1,4})\b")


def keyword_recall_score(response_text: str, fixture: dict[str, Any]) -> float:
    expected: list[str] = fixture.get("expected_keywords") or []
    if not expected:
        return 1.0
    haystack = response_text.lower()
    found = sum(1 for kw in expected if kw.lower() in haystack)
    return found / len(expected)


def _normalize_signal(token: str) -> str:
    digits = re.sub(r"\D", "", token)
    return f"SIG.MSR.{int(digits):03d}" if digits else token


def signal_recall_score(response_text: str, fixture: dict[str, Any]) -> float:
    expected: list[str] = fixture.get("expected_signals") or []
    if not expected:
        return 1.0
    found_set: set[str] = set()
    for match in SIG_RE.finditer(response_text):
        digits = match.group(1) or match.group(2)
        found_set.add(f"SIG.MSR.{int(digits):03d}")
    expected_set = {_normalize_signal(s) for s in expected}
    if not expected_set:
        return 1.0
    hits = sum(1 for sig in expected_set if sig in found_set)
    return hits / len(expected_set)


# Truncation raised 800 → 2000 (P3 D.3.3) — remedial / holistic answers'
# operative reasoning routinely appears past the 800-char mark; the legacy
# cap caused the judge to score on the preamble only.
JUDGE_RESPONSE_TRUNCATION = 2000


GEMINI_JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL", "gemini-2.5-flash")


def synthesis_score(
    response_text: str,
    fixture: dict[str, Any],
    model: str | None = None,
    rubric: str = "jyotish",
    judge: str = "gemini",
) -> float:
    """
    Score the candidate answer on a 0.0-1.0 scale. On any failure return 0.5.

    judge:
      'gemini'    — Gemini judge (default; uses GOOGLE_GENERATIVE_AI_API_KEY)
      'anthropic' — legacy Haiku judge (uses ANTHROPIC_API_KEY)
      'none'      — skip judge, return 0.5
    """
    if judge == "none":
        return 0.5
    if judge == "gemini":
        return _gemini_synthesis_score(response_text, fixture, model or GEMINI_JUDGE_MODEL, rubric)
    return _anthropic_synthesis_score(response_text, fixture, model or HAIKU_MODEL, rubric)


def _anthropic_synthesis_score(
    response_text: str, fixture: dict[str, Any], model: str, rubric: str
) -> float:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "[scorer] WARNING: ANTHROPIC_API_KEY not set; "
            "synthesis_score returning 0.5",
            file=sys.stderr,
        )
        return 0.5

    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        print(
            "[scorer] WARNING: anthropic SDK not installed; "
            "synthesis_score returning 0.5",
            file=sys.stderr,
        )
        return 0.5

    gold = fixture.get("gold_answer_summary", "")
    truncated_answer = response_text[:JUDGE_RESPONSE_TRUNCATION]
    expected_signals = ", ".join(fixture.get("expected_signals") or []) or "(none specified)"
    fixture_class = fixture.get("type", "unknown")

    if rubric == "legacy":
        user_prompt = f"Gold: {gold}\nAnswer: {truncated_answer}"
        system_prompt = (
            "You are an expert Jyotish evaluator. Score this answer from 0.0 to 1.0 "
            "on synthesis quality given the gold answer summary. Output JSON: "
            '{"score": 0.0-1.0, "reason": "<one sentence>"}. Be strict.'
        )
        max_tokens = 200
    else:
        user_prompt = (
            f"Query class: {fixture_class}\n"
            f"Expected signals: {expected_signals}\n"
            f"Gold answer summary: {gold}\n\n"
            f"Candidate answer:\n{truncated_answer}"
        )
        system_prompt = (
            "You are an expert Jyotish (Vedic astrology) evaluator. Score the candidate "
            "answer on FOUR axes (each 0.0-1.0), then return a final weighted score.\n\n"
            "AXIS A — Astrological grounding (weight 0.30): Did the answer cite specific "
            "signals (SIG.MSR.NNN), houses, planets, or divisional charts that match the "
            "gold answer's expected signals?\n\n"
            "AXIS B — Reasoning chain (weight 0.30): Did the answer show inference "
            "(e.g. AK→D9 Karakamsa→deity for spiritual queries; mahadasha→sub-period→event "
            "for temporal; planet→remedy for remedial) rather than just listing facts?\n\n"
            "AXIS C — Calibration discipline (weight 0.20): Did the answer state confidence "
            "('strong indication', 'moderate', 'tentative') or use hedging ('suggests', "
            "'indicates') rather than absolute claims?\n\n"
            "AXIS D — B.10 ledger / B.11 whole-chart (weight 0.20): Did the answer cite "
            "chart facts with IDs OR explicitly mark [EXTERNAL_COMPUTATION_REQUIRED] for "
            "missing data?\n\n"
            "Return ONLY JSON: {\"axis_a\": 0.0-1.0, \"axis_b\": 0.0-1.0, "
            "\"axis_c\": 0.0-1.0, \"axis_d\": 0.0-1.0, \"final\": <weighted_sum>, "
            "\"rationale\": \"<one sentence>\"}.\n"
            "Note: 'final' = 0.30*axis_a + 0.30*axis_b + 0.20*axis_c + 0.20*axis_d. "
            "Be strict but fair."
        )
        max_tokens = 400

    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(
            getattr(block, "text", "") for block in msg.content if hasattr(block, "text")
        ).strip()
    except Exception as err:  # noqa: BLE001 — judge calls are best-effort
        print(f"[scorer] WARNING: Haiku judge call failed: {err}", file=sys.stderr)
        return 0.5

    return _parse_score(text, rubric=rubric)


def _gemini_synthesis_score(
    response_text: str, fixture: dict[str, Any], model: str, rubric: str
) -> float:
    api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "[scorer] WARNING: GOOGLE_GENERATIVE_AI_API_KEY not set; "
            "synthesis_score returning 0.5",
            file=sys.stderr,
        )
        return 0.5

    try:
        from google import genai  # type: ignore
        from google.genai import types as genai_types  # type: ignore
    except ImportError:
        print(
            "[scorer] WARNING: google-genai SDK not installed; "
            "synthesis_score returning 0.5",
            file=sys.stderr,
        )
        return 0.5

    gold = fixture.get("gold_answer_summary", "")
    truncated_answer = response_text[:JUDGE_RESPONSE_TRUNCATION]
    expected_signals = ", ".join(fixture.get("expected_signals") or []) or "(none specified)"
    fixture_class = fixture.get("type", "unknown")

    if rubric == "legacy":
        system_prompt = (
            "You are an expert Jyotish evaluator. Score this answer from 0.0 to 1.0 "
            "on synthesis quality given the gold answer summary. Output JSON: "
            '{"score": 0.0-1.0, "reason": "<one sentence>"}. Be strict.'
        )
        user_prompt = f"Gold: {gold}\nAnswer: {truncated_answer}"
    else:
        system_prompt = (
            "You are an expert Jyotish (Vedic astrology) evaluator. Score the candidate "
            "answer on FOUR axes (each 0.0-1.0), then return a final weighted score.\n\n"
            "AXIS A — Astrological grounding (weight 0.30): Did the answer cite specific "
            "signals (SIG.MSR.NNN), houses, planets, or divisional charts that match the "
            "gold answer's expected signals?\n\n"
            "AXIS B — Reasoning chain (weight 0.30): Did the answer show inference "
            "(e.g. AK→D9 Karakamsa→deity for spiritual queries; mahadasha→sub-period→event "
            "for temporal; planet→remedy for remedial) rather than just listing facts?\n\n"
            "AXIS C — Calibration discipline (weight 0.20): Did the answer state confidence "
            "('strong indication', 'moderate', 'tentative') or use hedging ('suggests', "
            "'indicates') rather than absolute claims?\n\n"
            "AXIS D — B.10 ledger / B.11 whole-chart (weight 0.20): Did the answer cite "
            "chart facts with IDs OR explicitly mark [EXTERNAL_COMPUTATION_REQUIRED] for "
            "missing data?\n\n"
            "Return ONLY JSON: {\"axis_a\": 0.0-1.0, \"axis_b\": 0.0-1.0, "
            "\"axis_c\": 0.0-1.0, \"axis_d\": 0.0-1.0, \"final\": <weighted_sum>, "
            "\"rationale\": \"<one sentence>\"}.\n"
            "Note: 'final' = 0.30*axis_a + 0.30*axis_b + 0.20*axis_c + 0.20*axis_d. "
            "Be strict but fair."
        )
        user_prompt = (
            f"Query class: {fixture_class}\n"
            f"Expected signals: {expected_signals}\n"
            f"Gold answer summary: {gold}\n\n"
            f"Candidate answer:\n{truncated_answer}"
        )

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=2000,
                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = (resp.text or "").strip()
    except Exception as err:  # noqa: BLE001 — judge calls are best-effort
        print(f"[scorer] WARNING: Gemini judge call failed: {err}", file=sys.stderr)
        return 0.5

    return _parse_score(text, rubric=rubric)


def _parse_score(text: str, rubric: str = "jyotish") -> float:
    if not text:
        return 0.5
    match = re.search(r"\{.*\}", text, re.DOTALL)
    candidate = match.group(0) if match else text
    try:
        obj = json.loads(candidate)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0.5
    if rubric == "jyotish" and "final" in obj:
        try:
            return max(0.0, min(1.0, float(obj.get("final", 0.5))))
        except (TypeError, ValueError):
            pass
    try:
        score = float(obj.get("score", obj.get("final", 0.5)))
        return max(0.0, min(1.0, score))
    except (TypeError, ValueError):
        return 0.5


def weighted_score(
    keyword: float,
    signal: float,
    synthesis: float,
    weights: dict[str, float],
) -> float:
    return (
        keyword * float(weights.get("keyword_recall", 0.0))
        + signal * float(weights.get("signal_recall", 0.0))
        + synthesis * float(weights.get("synthesis", 0.0))
    )


def validate_weights(fixtures: Iterable[dict[str, Any]]) -> list[str]:
    """Return list of fixture_ids whose weights don't sum to 1.0 (±0.001)."""
    bad: list[str] = []
    for f in fixtures:
        w = f.get("scoring_weights", {})
        total = (
            float(w.get("keyword_recall", 0.0))
            + float(w.get("signal_recall", 0.0))
            + float(w.get("synthesis", 0.0))
        )
        if abs(total - 1.0) > 0.001:
            bad.append(f.get("fixture_id", "<unknown>"))
    return bad


if __name__ == "__main__":
    fixtures_path = Path(__file__).parent / "fixtures.json"
    data = json.loads(fixtures_path.read_text(encoding="utf-8"))
    bad = validate_weights(data["fixtures"])
    if bad:
        print(f"FAIL — weights do not sum to 1.0 for: {', '.join(bad)}")
        sys.exit(1)
    print(f"OK — {len(data['fixtures'])} fixtures, all weights sum to 1.0")
    print(f"Haiku model resolved: {HAIKU_MODEL}")
