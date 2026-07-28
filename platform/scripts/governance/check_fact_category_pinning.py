#!/usr/bin/env python3
"""check_fact_category_pinning.py — the C.7 systemic guard (ŚUDDHA-VĀCA Phase C,
lane:ci-lint).

Permanent CI enforcement of brief §5 C.7 (SUDDHA_VACA_BRIEF_v1_0.md), the
generalized fix for the entire "D1 defect class": a selector that picks a row
(or a set collapsed to one row) by `fact_category` alone, without pinning
`fact_key`, so which row is returned is undefined the moment chart_facts holds
more than one row for that (chart_id, ayanamsha_id, fact_category) tuple. The
concrete instances fixed individually this wave were `bo_laksana.py` (P0-5)
and `registry_bridge.ts` (P0-1, parked separately) — this script is the
general, permanent guard so the class does not recur anywhere else.

What it flags
--------------
Ground-truth calibration note: the brief's rule reads as a conjunction
("pins fact_key AND carries ORDER BY"), but running an AND-form draft of
this scanner against the live repo tree (pre-existing code, before this
wave's fixes land) produced ~90 false positives on a legitimate, widespread
pattern — a `fact_category` + `fact_key`-pinned SELECT that intentionally
returns many rows (one per `fact_subject`, e.g. one shadbala ratio per
graha) as a subject-keyed lookup, never reduced further. That pattern is NOT
the P0-5/P0-1 defect class: `fact_key` already disambiguates which
measurement is read, so it alone closes the non-determinism the two real
defects exhibited (both had NO fact_key pin at all). The rule below is
therefore a disjunction of independently-sufficient safety mechanisms,
calibrated against the two documented ground-truth defects
(`bo_laksana.py:831` / `registry_bridge.ts:3498`, SUDDHA_VACA_FIX_LEDGER_v1_0
P0-5/P0-1) rather than a literal parse of the brief sentence.

Python (scanned under python_scan_globs, default platform/python-sidecar/**/*.py):
    Any string literal that looks like a SQL SELECT against `chart_facts`
    filtering on `fact_category` (`fact_category = ...` / `fact_category IN
    (...)`) that carries NONE of:
      (a) a `fact_key = ...` / `fact_key IN (...)` pin,
      (b) a deterministic single-row reduction: `ORDER BY ... LIMIT 1`,
      (c) a `DISTINCT ON (...)` clause.

TypeScript (scanned under ts_scan_globs, default platform-mcp/src/**/*.ts and
platform/src/**/*.ts):
    Any `.find(...)` call, or `.filter(...)[0]` call, whose predicate text
    references `fact_category` and carries NEITHER:
      (a) a `fact_key` reference in the same predicate, NOR
      (b) a `.sort(...)` call chained immediately before the `.find`/`.filter`
          (a deterministic tiebreak establishing total order before the
          reduction to one element).

Known false-negative boundary (be honest about this — this is a regex/
bracket-matching scanner, not semantic analysis):
  - Dynamic query building (string concatenation / template interpolation
    assembling the WHERE clause across multiple statements, an ORM query
    builder with `.eq('fact_category', ...)` chained calls, ...) is NOT
    statically visible to this scanner and will NOT be flagged.
  - A `.find`/`.filter` predicate that references `fact_category` through an
    intermediate variable (`const cat = 'x'; arr.find(r => r.fact_category ===
    cat)`) is caught (the literal token `fact_category` still appears in the
    call). But a predicate built entirely from a variable holding the WHOLE
    predicate function is NOT caught (no `fact_category` token in the call
    text itself).
  - A two-step TS reduction — `const filtered = arr.filter(f =>
    f.fact_category === x); filtered[0]` — where the `[0]` is not
    syntactically attached to the `.filter(...)` call, is NOT caught (no
    cross-statement dataflow tracking).
  - A Python selection that pins `fact_key` but not any narrower identity
    (e.g. `fact_subject`) can still return >1 row in principle; this scanner
    treats `fact_key` + a deterministic ORDER BY/LIMIT 1 (or DISTINCT ON) as
    sufficient per the brief's literal wording ("pins fact_key AND carries a
    total ORDER BY") — it does not attempt to prove uniqueness against the
    live schema's actual constraints.
False-positive boundary:
  - A `.sort(...)` chained before `.find(...)` is accepted as "deterministic
    order" regardless of whether the sort key is actually total (e.g. sorting
    only by a field that itself has ties). This scanner cannot evaluate
    comparator semantics; it only checks for the presence of the call.

Modes
-----
  --self-test   Run the bundled fixtures under
                fact_category_pin_fixtures/{pass,fail}/. Exit 0 iff every
                PASS fixture is silent and every FAIL fixture is flagged.
                DB-free, repo-free — the hermetic CI gate.
  (default)     Scan the live repo tree. Reports every violation; only NEW
                (non-allowlisted) violations fail the build. Pre-existing
                violations found during the initial rollout are recorded in
                fact_category_pin_allowlist.json with a written justification
                (see schema in that file's header) rather than silently
                dropped.
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
FIXTURE_DIR = SCRIPT_DIR / "fact_category_pin_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "fact_category_pin_allowlist.json"

DEFAULT_PY_GLOBS = ["platform/python-sidecar/**/*.py"]
DEFAULT_TS_GLOBS = ["platform-mcp/src/**/*.ts", "platform/src/**/*.ts"]

# Never scan the lint's own fixtures, or test/generated trees, as live code —
# the fixtures are deliberately unsafe/safe examples, not real call sites, and
# test/generated code is out of this guard's scope (mirrors naming_lint.py's
# global_excludes discipline).
EXCLUDE_SUBSTRINGS = (
    "fact_category_pin_fixtures/",
    "/__tests__/",
    "/tests/",
    "/node_modules/",
    "/generated/",
    ".test.ts",
    ".spec.ts",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    file: str  # repo-relative POSIX path
    line: int  # 1-indexed
    lang: str  # "python" | "typescript"
    kind: str  # "sql_select" | "find" | "filter_index"
    snippet: str
    message: str

    def key(self) -> str:
        return f"{self.file}|{self.kind}|{self.snippet}"


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


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
# Python scanner — SQL string literals selecting on chart_facts.fact_category
# ---------------------------------------------------------------------------

# Triple-quoted strings (the observed convention for embedded multi-line SQL
# in this codebase, e.g. bo_laksana.py's _FETCH_INVARIANT_SQL) plus ordinary
# single-line quoted strings. DOTALL so triple-quoted blocks span lines.
_PY_STRING_RE = re.compile(
    r'"""(?P<t1>.*?)"""'
    r'|\'\'\'(?P<t2>.*?)\'\'\''
    r'|"(?P<d1>[^"\\\n]*(?:\\.[^"\\\n]*)*)"'
    r"|'(?P<d2>[^'\\\n]*(?:\\.[^'\\\n]*)*)'",
    re.DOTALL,
)

# Requires an actual SELECT ... FROM chart_facts shape, not merely the
# substring "chart_facts" anywhere in a string. Without this, module/function
# DOCSTRINGS that describe the chart_facts schema in prose (e.g. "Each row:
# fact_category='bodha.domain_links', fact_subject=cell_id...") were matching
# as if they were live queries — a real false-positive class found while
# calibrating this scanner against the live repo tree (~15 docstring hits in
# brahmagyan/bodha/*, brahmagyan/ganita/*, writer module headers). DELETE/
# INSERT/UPDATE statements are also excluded by this requirement — brief §5
# C.7 is scoped to SELECT misselection, not write-path scoping (a DELETE that
# under-scopes by fact_category is a different, real hazard — over-deletion —
# but not this guard's stated job).
_RE_SELECT_FROM_CHART_FACTS = re.compile(
    r"\bSELECT\b.*?\bFROM\s+chart_facts\b", re.IGNORECASE | re.DOTALL
)
_RE_CHART_FACTS = re.compile(r"\bchart_facts\b", re.IGNORECASE)
_RE_FACT_CATEGORY_FILTER = re.compile(r"\bfact_category\s*(=|==|\bIN\b)", re.IGNORECASE)
_RE_FACT_KEY_FILTER = re.compile(r"\bfact_key\s*(=|==|\bIN\b|\bLIKE\b)", re.IGNORECASE)
_RE_ORDER_BY = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)
_RE_LIMIT_1 = re.compile(r"\bLIMIT\s+1\b", re.IGNORECASE)
_RE_DISTINCT_ON = re.compile(r"\bDISTINCT\s+ON\s*\(", re.IGNORECASE)


def _is_unsafe_sql_block(sql: str) -> bool:
    """Pure predicate: True iff this SQL text is a fact_category selection
    against chart_facts that carries NONE of the three recognized safety
    mechanisms. Exposed standalone so the self-test can exercise it directly
    without file I/O.

    Safety mechanisms (ANY ONE is sufficient — this is a disjunction, not a
    conjunction; see the module docstring's "ground-truth calibration" note
    for why):
      (a) a `fact_key = ...` / `fact_key IN (...)` pin — this is what P0-5
          (`bo_laksana.py:831`) and P0-1 (`registry_bridge.ts:3498`) both
          lacked: without it, a category+subject pair can silently match
          more than one row (different fact_key variants of the same
          measurement) and whichever one the DB happens to return last wins
          the application-side dict/lookup assignment — the exact reported
          non-determinism.
      (b) a deterministic `ORDER BY ... LIMIT 1` — safe even without a
          fact_key pin, because the total order makes the one surviving row
          reproducible.
      (c) `DISTINCT ON (...)` — Postgres's native "one row per key by
          construction" idiom.

    A query that pins fact_key but fetches many rows (one per fact_subject,
    e.g. one shadbala ratio per graha) is NOT the defect class: fact_key
    already disambiguates which measurement is being read per subject, and
    the multi-row result is the intended shape (a subject-keyed lookup), not
    an ambiguous reduction. Requiring ORDER BY on top of that pin as well
    (the earlier, stricter draft of this rule) was measured against the live
    repo tree and produced ~90 false positives on exactly this legitimate
    pattern (`bo_upaya.py`, `ga_structural_writer.py`, ...) — see the ci-lint
    lane's session report. The disjunction is the calibrated rule.
    """
    if not _RE_SELECT_FROM_CHART_FACTS.search(sql):
        return False
    if not _RE_FACT_CATEGORY_FILTER.search(sql):
        return False
    has_fact_key = bool(_RE_FACT_KEY_FILTER.search(sql))
    has_order_limit = bool(_RE_ORDER_BY.search(sql)) and bool(_RE_LIMIT_1.search(sql))
    has_distinct_on = bool(_RE_DISTINCT_ON.search(sql))
    return not (has_fact_key or has_order_limit or has_distinct_on)


def scan_python_text(text: str) -> List[tuple]:
    """Return list of (line, snippet) for unsafe fact_category SQL blocks."""
    hits: List[tuple] = []
    for m in _PY_STRING_RE.finditer(text):
        content = next((g for g in m.groups() if g is not None), "")
        if not content or "chart_facts" not in content.lower():
            continue
        if _is_unsafe_sql_block(content):
            line = text.count("\n", 0, m.start()) + 1
            snippet = " ".join(content.split())[:160]
            hits.append((line, snippet))
    return hits


# ---------------------------------------------------------------------------
# TypeScript scanner — .find(...) / .filter(...)[0] on fact_category
# ---------------------------------------------------------------------------

_TS_CALL_RE = re.compile(r"\.(find|filter)\s*\(")
_RE_SORT_BEFORE = re.compile(r"\.sort\s*\(\s*[^)]*\)\s*(\.[a-zA-Z_]+\([^)]*\)\s*)*$")


def _extract_balanced(text: str, open_paren_idx: int) -> tuple:
    """Return (arg_text, index_just_after_the_matching_close_paren)."""
    depth = 0
    i = open_paren_idx
    start = open_paren_idx + 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    return text[start:], n


def _has_sort_before(text: str, call_start: int) -> bool:
    """Heuristic: is there a `.sort(...)` call chained in the statement
    immediately preceding this .find/.filter call? Looks backward from
    call_start to the nearest statement boundary (`;`, `{`, `}`, or blank
    line) and checks for a `.sort(` token in that window."""
    boundary_re = re.compile(r"[;{}]")
    window_start = 0
    for bm in boundary_re.finditer(text, 0, call_start):
        window_start = bm.end()
    window = text[window_start:call_start]
    return ".sort(" in window


def scan_ts_text(text: str) -> List[tuple]:
    """Return list of (line, kind, snippet) for unsafe fact_category
    .find(...)/.filter(...)[0] reductions."""
    hits: List[tuple] = []
    for m in _TS_CALL_RE.finditer(text):
        call_kind = m.group(1)  # "find" | "filter"
        open_idx = m.end() - 1
        arg_text, after_idx = _extract_balanced(text, open_idx)
        if "fact_category" not in arg_text:
            continue
        if call_kind == "filter":
            rest = text[after_idx : after_idx + 20]
            if not re.match(r"\s*\[\s*0\s*\]", rest):
                continue  # bare .filter(...) without [0] isn't a one-row reduction
            kind = "filter_index"
        else:
            kind = "find"
        has_fact_key = "fact_key" in arg_text
        has_sort = _has_sort_before(text, m.start())
        # Disjunction, mirroring the Python SQL rule: a fact_key check in the
        # SAME predicate already disambiguates which row can match (the P0-1
        # bug had neither), so it alone is sufficient even without a .sort()
        # — a .sort() alone (establishing total order before .find/.filter)
        # is also independently sufficient. See _is_unsafe_sql_block's
        # docstring for the calibration rationale (the AND-form over-flagged
        # on the live tree).
        if has_fact_key or has_sort:
            continue
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(arg_text.split())[:160]
        hits.append((line, kind, snippet))
    return hits


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def scan_repo(root: Path, py_globs: Sequence[str], ts_globs: Sequence[str]) -> List[Violation]:
    violations: List[Violation] = []

    for path in expand_globs(root, py_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, snippet in scan_python_text(text):
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    lang="python",
                    kind="sql_select",
                    snippet=snippet,
                    message=(
                        "SELECT against chart_facts filters by fact_category "
                        "with NONE of: a fact_key pin, a deterministic "
                        "ORDER BY ... LIMIT 1, or a DISTINCT ON reduction "
                        "(brief §5 C.7 — the D1 defect class)."
                    ),
                )
            )

    for path in expand_globs(root, ts_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, snippet in scan_ts_text(text):
            call = ".find(...)" if kind == "find" else ".filter(...)[0]"
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    lang="typescript",
                    kind=kind,
                    snippet=snippet,
                    message=(
                        f"{call} reduces a fact array by fact_category alone, "
                        "with NEITHER a fact_key check in the predicate NOR a "
                        ".sort(...) deterministic tiebreak chained beforehand "
                        "(brief §5 C.7 — the D1 defect class)."
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
        print(f"{prefix}[{v.lang}][{v.kind}] {v.file}:{v.line} — {v.message}")
        print(f"{prefix}    {v.snippet}")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


def run_self_test() -> int:
    pass_dir = FIXTURE_DIR / "pass"
    fail_dir = FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        print("check_fact_category_pinning: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2

    failures: List[str] = []

    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file():
            continue
        text = fixture.read_text(encoding="utf-8")
        if fixture.suffix == ".py":
            hits = scan_python_text(text)
        elif fixture.suffix == ".ts":
            hits = [(line, snippet) for line, _kind, snippet in scan_ts_text(text)]
        else:
            continue
        if hits:
            failures.append(f"PASS-fixture '{fixture.name}' was flagged (false positive): {hits}")

    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file():
            continue
        text = fixture.read_text(encoding="utf-8")
        if fixture.suffix == ".py":
            hits = scan_python_text(text)
        elif fixture.suffix == ".ts":
            hits = [(line, snippet) for line, _kind, snippet in scan_ts_text(text)]
        else:
            continue
        if not hits:
            failures.append(f"FAIL-fixture '{fixture.name}' produced NO violation (false negative)")

    if failures:
        print("check_fact_category_pinning: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"check_fact_category_pinning: SELF-TEST PASS "
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
    violations = scan_repo(root, DEFAULT_PY_GLOBS, DEFAULT_TS_GLOBS)
    allowlist = load_allowlist(ALLOWLIST_PATH)
    allowed, new = partition_allowlisted(violations, allowlist)

    # --json is a pure machine-readable report: emit exactly one JSON document
    # to stdout and nothing else (the human-readable prints below are for
    # non-JSON mode only), so callers can pipe this straight into `json.load`.
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
            f"check_fact_category_pinning: {len(allowed)} allowlisted violation(s) "
            f"(reported, not failing — see fact_category_pin_allowlist.json):"
        )
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(
            f"check_fact_category_pinning: STRICT mode — {len(violations)} total "
            f"violation(s) (including allowlisted). FAIL.",
            file=sys.stderr,
        )
        print_violations(violations, prefix="  ")
        return 1

    if new:
        print(
            f"check_fact_category_pinning: {len(new)} NON-ALLOWLISTED violation(s) "
            f"found. FAIL.",
            file=sys.stderr,
        )
        print_violations(new, prefix="  ")
        return 1

    print(
        f"check_fact_category_pinning: 0 new violations "
        f"({len(allowed)} pre-existing, allowlisted). PASS."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
