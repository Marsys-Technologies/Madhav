"""
eval_runner.py — DeepSeek-based answer:eval for MARSYS-JIS.

Reads a query+response pair (from a JSON file or stdin), calls DeepSeek API
with the eval rubric prompt, and returns a scored rubric JSON.

Usage:
    python3 platform/scripts/eval/eval_runner.py --input path/to/qr.json
    python3 platform/scripts/eval/eval_runner.py --question "..." --answer "..."
    echo '{"question": "...", "answer": "..."}' | python3 platform/scripts/eval/eval_runner.py

Environment:
    DEEPSEEK_API_KEY   — required; DeepSeek API key
    DEEPSEEK_BASE_URL  — optional; default https://api.deepseek.com/v1

Output:
    JSON rubric result to stdout. Non-zero exit on API error.

Scaffold status: RUNNABLE. Created M5-A-S1 (2026-05-13).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

SCRIPT_DIR = Path(__file__).resolve().parent
RUBRIC_PATH = SCRIPT_DIR / "eval_rubric_v1_0.json"
PROMPT_PATH = SCRIPT_DIR / "eval_prompt_v1_0.txt"

DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = "deepseek-chat"
MAX_TOKENS = 1024
TEMPERATURE = 0.1


def load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_eval_prompt(question: str, answer: str) -> str:
    template = load_prompt_template()
    return template.replace("{{question}}", question).replace("{{answer}}", answer)


def call_deepseek(prompt: str, api_key: str) -> str:
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urlrequest.Request(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
    except urlerror.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {err_body}") from exc


def compute_weighted_score(rubric: dict) -> float:
    weights = {
        "b11_whole_chart_read": 0.30,
        "citation_completeness": 0.20,
        "calibration_language": 0.20,
        "b10_no_fabricated_computation": 0.20,
        "overall": 0.10,
    }
    total = 0.0
    for dim, weight in weights.items():
        score = rubric.get(dim, {}).get("score", 0)
        total += score * weight
    return round(total, 3)


def run_eval(question: str, answer: str, api_key: str) -> dict:
    prompt = build_eval_prompt(question, answer)
    raw = call_deepseek(prompt, api_key)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek returned non-JSON: {raw[:500]}") from exc

    if "weighted_score" not in result:
        result["weighted_score"] = compute_weighted_score(result)
    if "pass" not in result:
        result["pass"] = result["weighted_score"] >= 7.0
    if "eval_timestamp" not in result:
        result["eval_timestamp"] = datetime.now(timezone.utc).isoformat()
    if "evaluator_model" not in result:
        result["evaluator_model"] = "deepseek"

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="MARSYS-JIS answer:eval (DeepSeek)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--input", help="Path to JSON file with {question, answer}")
    group.add_argument("--question", help="Question text (use with --answer)")
    parser.add_argument("--answer", help="Answer text (use with --question)")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    if args.input:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        question = data["question"]
        answer = data["answer"]
    elif args.question and args.answer:
        question = args.question
        answer = args.answer
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            parser.print_help()
            sys.exit(1)
        data = json.loads(raw)
        question = data["question"]
        answer = data["answer"]

    result = run_eval(question, answer, api_key)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("pass", False):
        sys.exit(2)


if __name__ == "__main__":
    main()
