#!/usr/bin/env python3
"""check_fact_subject_wellformedness.py — ADHIṢṬHĀNA Lane A6(ii) permanent
regression guard against Lane A1's exact defect class.

Lane A1 (MASTER_PLAN_v1_0.md §3) found and fixed six writer sites
(`ga_condition_writer.py` x5, `ga_vargas_writer.py` x1) that emitted
`fact_subject` for a graha by calling a bare `.upper()` on a Title-case long
name (`"Mars".upper()` -> `"MARS"`, wrong — the canonical system-A code is
`"MAR"`; worse, `"Rahu".upper()` -> `"RAHU"` when the canonical code is
`"RAH_MEAN"`, a different string entirely, not just a different case) instead
of routing through the SSoT normalizer (`PLANET_TO_SUBJECT` /
`brahmagyan.graha_vocabulary.norm_graha`). See
`platform/python-sidecar/tests/test_a1_producer_graha_subject_convergence.py`
for the value-level regression tests on the two files that were actually
fixed.

This script is the GENERAL, permanent guard: it scans every current AND
FUTURE writer file for the same shape, so a brand-new writer cannot
reintroduce the defect class Lane A1 spent an entire lane closing.

WHAT IS A VIOLATION
--------------------
A `fact_subject` dict-key value (`"fact_subject": <expr>`) or a `fact_subject`
variable assignment (`fact_subject = <expr>`) whose expression:
  (a) calls `.upper()` on an identifier that LOOKS graha/planet-shaped (the
      identifier's name contains "graha", "planet", "body", or "grh" —
      case-insensitive; this is exactly the naming convention the two real
      Lane A1 defects used: `graha.upper()` / `floored_body.upper()`), AND
  (b) contains NONE of the recognized SSoT-routing tokens anywhere in the
      same expression: `PLANET_TO_SUBJECT`, `BODY_TO_SUBJECT`, `norm_graha`,
      `to_title`, `graha_vocabulary`, `GRAHA_ALIASES`.

The established SAFE idiom in this codebase (post-Lane-A1) is
`PLANET_TO_SUBJECT.get(graha, graha.upper())` — the `.upper()` fallback is
still there (only used when `graha` is genuinely unknown to the map, e.g. a
floored non-graha body), but the expression ALSO references
`PLANET_TO_SUBJECT`, so it is not flagged. A regression that reverts to a
bare `graha.upper()` with no SSoT token in the expression IS flagged.

WHAT IS NOT A VIOLATION (scoped narrowly, by design)
------------------------------------------------------
`.upper()` on a fact_subject value whose source identifier is NOT
graha-shaped (e.g. `sign_name.upper()`, `nakshatra.upper()`) is not flagged —
this guard's job is Lane A1's exact defect class (graha identity), not a
blanket ban on `.upper()` in fact_subject construction. A vocabulary this
narrow may miss a genuinely mis-routed non-graha fact_subject, but a wider
net was measured (during calibration against the live tree, see below) to
have zero real targets and would invite exactly the kind of over-broad
false-positive noise `check_fact_category_pinning.py`'s own calibration note
warns against.

Calibration note: run against the live repo tree at authoring time (2026-08-08,
post-Lane-A1-merge), this scanner found ZERO violations — every existing
`.upper()`-on-a-graha-identifier site already routes through
`PLANET_TO_SUBJECT`/`BODY_TO_SUBJECT`. The baseline allowlist therefore starts
empty; any violation this scanner reports from here forward is real regression,
not legacy debt needing disposition.

Scanned directories (writer code only — matches the layers Lane A1 touched
and every layer that could repeat the same defect):
  platform/python-sidecar/ga_writers/**/*.py
  platform/python-sidecar/bodha_writers/**/*.py
  platform/python-sidecar/pipeline/orchestrator/writers/**/*.py

Known false-negative boundary (be honest — this is a regex scanner, not
semantic analysis, same discipline as check_fact_category_pinning.py):
  - Only single-line dict-key / assignment expressions are captured (the
    established codebase convention — every real fact_subject site found
    during calibration is one line). A `fact_subject` value expression that
    wraps across multiple lines is not captured.
  - Two-step construction (`subj = graha.upper(); row["fact_subject"] = subj`)
    is not caught — no cross-statement dataflow tracking, same boundary
    check_fact_category_pinning.py's TS scanner documents for its own
    two-step case.
  - An identifier that IS a graha but does not match the
    graha|planet|body|grh naming heuristic (e.g. a single-letter `p`) would
    be missed. All Lane A1 defect sites and every current writer in the
    live tree use one of the four recognized name fragments.

Modes
-----
  --self-test   Run the bundled fixtures under
                fact_subject_wellformedness_fixtures/{pass,fail}/. Exit 0 iff
                every PASS fixture is silent and every FAIL fixture
                (including a literal reproduction of both real Lane A1
                defect sites) is flagged. DB-free, repo-free — the hermetic
                CI gate.
  (default)     Scan the live repo tree. Reports every violation; only NEW
                (non-allowlisted) violations fail the build. The allowlist
                (fact_subject_wellformedness_allowlist.json) starts empty —
                see the calibration note above.
  --strict      Fail on ANY violation, including allowlisted ones.

Exit codes
----------
  0  clean (or self-test pass)
  1  non-allowlisted violation(s) found (or self-test fail)
  2  invocation / config error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # platform/scripts/governance -> repo root
FIXTURE_DIR = SCRIPT_DIR / "fact_subject_wellformedness_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "fact_subject_wellformedness_allowlist.json"

DEFAULT_PY_GLOBS = [
    "platform/python-sidecar/ga_writers/**/*.py",
    "platform/python-sidecar/bodha_writers/**/*.py",
    "platform/python-sidecar/pipeline/orchestrator/writers/**/*.py",
]

EXCLUDE_SUBSTRINGS = (
    "fact_subject_wellformedness_fixtures/",
    "/__tests__/",
    "/tests/",
    "/node_modules/",
    "/generated/",
)

# SSoT-routing tokens — a fact_subject expression containing ANY of these is
# considered safely routed, regardless of whether `.upper()` also appears
# (the established `X_TO_SUBJECT.get(graha, graha.upper())` idiom).
SAFE_TOKENS = (
    "PLANET_TO_SUBJECT",
    "BODY_TO_SUBJECT",
    "norm_graha",
    "to_title",
    "graha_vocabulary",
    "GRAHA_ALIASES",
)

# Identifier fragments that mark a `.upper()` receiver as "graha-shaped" —
# exactly the naming convention both real Lane A1 defects used
# (`graha.upper()`, `floored_body.upper()`).
_GRAHA_IDENT_FRAGMENT = r"(?:graha|planet|body|grh)"

_RE_BARE_UPPER_ON_GRAHA = re.compile(
    r"\b(\w*" + _GRAHA_IDENT_FRAGMENT + r"\w*)\s*\.\s*upper\s*\(\s*\)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    kind: str  # "dict_key" | "assignment"
    snippet: str
    message: str

    def key(self) -> str:
        return f"{self.file}|{self.kind}|{self.snippet}"


def _excluded(rel: str) -> bool:
    return any(s in rel for s in EXCLUDE_SUBSTRINGS)


def expand_globs(root: Path, globs: Sequence[str]) -> List[Path]:
    out: set[Path] = set()
    for pattern in globs:
        for match in root.glob(pattern):
            if not match.is_file():
                continue
            rel = match.relative_to(root).as_posix()
            if _excluded(rel):
                continue
            out.add(match)
    return sorted(out)


# ---------------------------------------------------------------------------
# Expression extraction — two shapes: dict-literal key, and bare assignment.
# ---------------------------------------------------------------------------

_RE_DICT_KEY = re.compile(r'"fact_subject"\s*:\s*([^,\n]+?)\s*,?\s*$', re.MULTILINE)
_RE_ASSIGNMENT = re.compile(r'(?<![.\w])fact_subject\s*=(?!=)\s*([^\n]+?)\s*$', re.MULTILINE)


def _is_unsafe_expr(expr: str) -> bool:
    """Pure predicate — True iff `expr` calls `.upper()` on a graha-shaped
    identifier and carries NONE of the recognized SSoT-routing tokens."""
    if not _RE_BARE_UPPER_ON_GRAHA.search(expr):
        return False
    return not any(tok in expr for tok in SAFE_TOKENS)


def scan_python_text(text: str) -> List[tuple]:
    """Return list of (line, kind, snippet) for unsafe fact_subject expressions."""
    hits: List[tuple] = []
    seen_spans: set[tuple[int, int]] = set()

    for m in _RE_DICT_KEY.finditer(text):
        expr = m.group(1).strip()
        if _is_unsafe_expr(expr):
            line = text.count("\n", 0, m.start()) + 1
            seen_spans.add((m.start(1), m.end(1)))
            hits.append((line, "dict_key", expr[:160]))

    for m in _RE_ASSIGNMENT.finditer(text):
        # Skip spans already captured as a dict-key hit (avoids double-count
        # when a dict-key regex and the looser assignment regex both match
        # the same physical text, which cannot happen given the differing
        # anchors, but keep the guard cheap and explicit).
        if (m.start(1), m.end(1)) in seen_spans:
            continue
        expr = m.group(1).strip()
        if _is_unsafe_expr(expr):
            line = text.count("\n", 0, m.start()) + 1
            hits.append((line, "assignment", expr[:160]))

    return hits


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def scan_repo(root: Path, py_globs: Sequence[str]) -> List[Violation]:
    violations: List[Violation] = []
    for path in expand_globs(root, py_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, snippet in scan_python_text(text):
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    kind=kind,
                    snippet=snippet,
                    message=(
                        "fact_subject is built from a bare .upper() call on a "
                        "graha-shaped identifier with no PLANET_TO_SUBJECT/"
                        "BODY_TO_SUBJECT/norm_graha/to_title routing in the same "
                        "expression — Lane A1's exact defect class "
                        "(MASTER_PLAN_v1_0.md §3 Lane A1)."
                    ),
                )
            )
    return violations


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def load_allowlist(path: Path) -> list:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("entries", [])


def _matches_entry(v: Violation, entry: dict) -> bool:
    if entry.get("file") != v.file:
        return False
    if "line" in entry and entry["line"] is not None:
        return int(entry["line"]) == v.line
    pattern = entry.get("pattern")
    if pattern:
        try:
            if re.search(pattern, v.snippet):
                return True
        except re.error:
            pass
        return pattern in v.snippet
    return False


def partition_allowlisted(violations: Sequence[Violation], allowlist: list):
    allowed, new = [], []
    for v in violations:
        if any(_matches_entry(v, e) for e in allowlist):
            allowed.append(v)
        else:
            new.append(v)
    return allowed, new


def print_violations(violations: Sequence[Violation], prefix: str = "") -> None:
    for v in violations:
        print(f"{prefix}[{v.kind}] {v.file}:{v.line} — {v.message}")
        print(f"{prefix}    {v.snippet}")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


def run_self_test() -> int:
    pass_dir = FIXTURE_DIR / "pass"
    fail_dir = FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        print("check_fact_subject_wellformedness: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2

    failures: List[str] = []

    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix != ".py":
            continue
        hits = scan_python_text(fixture.read_text(encoding="utf-8"))
        if hits:
            failures.append(f"PASS-fixture '{fixture.name}' was flagged (false positive): {hits}")

    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix != ".py":
            continue
        hits = scan_python_text(fixture.read_text(encoding="utf-8"))
        if not hits:
            failures.append(f"FAIL-fixture '{fixture.name}' produced NO violation (false negative)")

    if failures:
        print("check_fact_subject_wellformedness: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"check_fact_subject_wellformedness: SELF-TEST PASS "
        f"({len(list(pass_dir.iterdir()))} pass fixture(s) silent, "
        f"{len(list(fail_dir.iterdir()))} fail fixture(s) caught)."
    )
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="Run bundled fixtures (DB-free, hermetic).")
    ap.add_argument("--strict", action="store_true", help="Fail on ANY violation, including allowlisted.")
    ap.add_argument("--root", default=str(REPO_ROOT), help="Repo root to scan.")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    root = Path(args.root).resolve()
    violations = scan_repo(root, DEFAULT_PY_GLOBS)
    allowlist = load_allowlist(ALLOWLIST_PATH)
    allowed, new = partition_allowlisted(violations, allowlist)

    if args.json:
        strict_fail = args.strict and bool(violations)
        new_fail = bool(new)
        print(
            json.dumps(
                {
                    "total": len(violations),
                    "allowlisted": len(allowed),
                    "new": [v.__dict__ for v in new],
                    "allowed_violations": [v.__dict__ for v in allowed],
                    "strict": args.strict,
                    "pass": not (strict_fail or new_fail),
                },
                indent=2,
            )
        )
        return 1 if (strict_fail or new_fail) else 0

    if allowed:
        print(
            f"check_fact_subject_wellformedness: {len(allowed)} allowlisted violation(s) "
            f"(reported, not failing — see fact_subject_wellformedness_allowlist.json):"
        )
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(
            f"check_fact_subject_wellformedness: STRICT mode — {len(violations)} total "
            f"violation(s) (including allowlisted). FAIL.",
            file=sys.stderr,
        )
        print_violations(violations, prefix="  ")
        return 1

    if new:
        print(
            f"check_fact_subject_wellformedness: {len(new)} NON-ALLOWLISTED violation(s) "
            f"found. FAIL.",
            file=sys.stderr,
        )
        print_violations(new, prefix="  ")
        return 1

    print(
        f"check_fact_subject_wellformedness: 0 new violations "
        f"({len(allowed)} pre-existing, allowlisted). PASS."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
