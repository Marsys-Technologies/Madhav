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

TIGHTENED 2026-09-05 (F-C14, issue #1750, Conductor ruling). The disjunction
above was too weak in one specific shape, and the calibration note explains
why the hole was not obvious: a query that REDUCES TO ONE ROW was allowed to
do so on `ORDER BY ... LIMIT 1` alone. That reasoning conflates DETERMINISM
with CORRECTNESS. `deriveShadbalaWeakestGraha` (L2_bodha/query_ucd.ts) takes
the MIN over `fact_category='graha_shadbala_total'`, which holds two
incommensurable `fact_key` populations -- every `ratio` (0.84-1.69) sorts
below every `rupa` (4.64-8.47) -- so the MIN can never land in `rupa` and a
ratio is reproducibly served under a field named `shadbala_rupa`. Stable,
repeatable, and wrong every single time.

So the rule now splits:
  * a query that reduces to one row MUST pin fact_key (the brief's literal
    conjunction -- and the ~90 false positives never had a LIMIT 1, so this
    branch costs none of them). `fact_key` counts as pinned when it appears in a
    filter OR in a `DISTINCT ON (...)` key list: `DISTINCT ON (fact_subject,
    fact_key)` returns one row PER fact_key and so cannot conflate two key
    populations at all. The first draft of this tightening missed that and turned
    `main` red on `bo_laksana.py:992`, a correct query (issue #1794);
  * a query that does not reduce keeps the original calibrated disjunction.

The same fix opened the second hole: TS SQL template literals were never
scanned at all (only `.find()`/`.filter()[0]`), so the canonical instance of
the defect class this guard exists for was invisible to it on two independent
counts. `scan_ts_sql_text` closes that, reusing `_is_unsafe_sql_block` so the
SQL rule cannot drift between host languages, and `run_self_test` now runs
BOTH TS scanners -- running only one is how a green self-test shipped
alongside a blind scanner.

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

MULTI-FORMULA RULE (formula-pins lane, INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md; SS decision
2026-10-01; hardened after the PR #2866 independent review). `fact_key` pinning closes fact_key-level
ambiguity but cannot see the FORMULA dimension: `ga_sensitive` writes one row per classical
`formula_id` for seven categories (declared in ONE place,
platform/python-sidecar/brahmagyan/canonical_formulas.py, which this lint loads by path), so a
(subject, key) pair legitimately holds several rows and a reader that pins fact_category + fact_key
still serves a physical-order-dependent winner. Every `SELECT ... FROM|JOIN [public.]chart_facts`
STATEMENT that names a declared category -- as a quoted literal, or by a `LIKE 'esoteric_point_%'` /
`~ '^esoteric_point_'` prefix a declared category starts with -- must EITHER
  (a) pin the formula in ITS OWN WHERE: `formula_id = ...` / `formula_id IN (...)` / `= ANY(...)`.
      NOT pins: `IS [NOT] NULL`, `<>`, `!=`, `NOT IN`, a comparison to a column, any occurrence in an
      ORDER BY (a `CASE WHEN formula_id = 'x'` canonical-first rank), and any occurrence inside a
      nested subselect (which is judged as its own statement); OR
  (b) disclose ALL variants: `formula_id` (or a bare `*`) in the SELECT list AND `formula_id` in the
      ORDER BY (a trailing UNION ORDER BY governs every branch).
Statements are judged ONE BY ONE: every UNION / INTERSECT / EXCEPT branch and every nested subselect
must satisfy the rule, so a pinned branch cannot mask an unpinned one. Exempt per statement: zero-row
availability probes (`LIMIT 0`) and aggregate-only `SELECT COUNT(...)`. TS SQL is read from template
literals AND '...' / "..." strings by a string- and comment-aware tokenizer (a `/*` inside a string is
not a comment; a backtick inside a comment does not misalign the literals after it).
A SECOND, structural check covers readers whose category set is dynamic (so no literal is visible
to a regex): every file listed under `readers` in multi_formula_readers.json must reference the
canonical_formulas module; EVERY chart_facts SELECT carrying one of its `select_markers` must be
formula-aware (mode pin: a WHERE pin; mode disclose: formula_id selected); and the file must hold an
ORDER BY naming formula_id AND every `order_tokens` entry (canonical-first rank, subject, fact_id), so
a total canonical-first order cannot be dropped. A marker that matches nothing fails loudly.
`known_open_readers` in the same file records, unenforced, the readers verified NOT yet
formula-aware. Honest scope: this does not prove every dynamically-assembled query; a new dynamic
multi-formula reader must be added to `readers`.

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
READERS_PATH = SCRIPT_DIR / "multi_formula_readers.json"
CANONICAL_FORMULAS_PY = REPO_ROOT / "platform" / "python-sidecar" / "brahmagyan" / "canonical_formulas.py"

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
# DISTINCT ON whose KEY LIST names fact_key. This is a fact_key pin, not merely a
# reduction: `DISTINCT ON (fact_subject, fact_key)` returns one row PER fact_key,
# so it cannot conflate two key populations the way an unpinned ORDER BY ... LIMIT 1
# can. Missing this distinction is what turned main red (issue #1794).
_RE_DISTINCT_ON_KEYED = re.compile(
    r"\bDISTINCT\s+ON\s*\([^)]*\bfact_key\b[^)]*\)", re.IGNORECASE
)


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
    # `fact_key` is pinned either by a filter (fact_key = ...) or by appearing in a
    # DISTINCT ON key list -- both make which row is returned unambiguous per key.
    has_fact_key = bool(_RE_FACT_KEY_FILTER.search(sql)) or bool(
        _RE_DISTINCT_ON_KEYED.search(sql)
    )
    has_order_limit = bool(_RE_ORDER_BY.search(sql)) and bool(_RE_LIMIT_1.search(sql))
    has_distinct_on = bool(_RE_DISTINCT_ON.search(sql))
    reduces_to_one_row = has_order_limit or has_distinct_on

    # TIGHTENED (F-C14, issue #1750). A query that REDUCES TO ONE ROW must ALSO
    # pin fact_key -- the reduction is no longer independently sufficient.
    #
    # The original rule accepted `ORDER BY ... LIMIT 1` on its own, reasoning
    # that "the total order makes the one surviving row reproducible". That
    # reasoning conflates DETERMINISM with CORRECTNESS. Reproducibly taking the
    # extremum across two incommensurable fact_key populations is deterministic,
    # stable, and wrong every single time -- which is exactly
    # deriveShadbalaWeakestGraha (L2_bodha/query_ucd.ts), where every `ratio`
    # (0.84-1.69) sorts below every `rupa` (4.64-8.47), so MIN can never land in
    # `rupa` and a ratio is served under a field named `shadbala_rupa`.
    #
    # CLAUDE.md §N.7 item 2 states it as a conjunction -- "pins fact_key AND
    # carries a total ORDER BY" -- and this branch is that conjunction.
    if reduces_to_one_row:
        return not has_fact_key

    # NON-reducing queries keep the ORIGINAL calibrated disjunction. This is
    # deliberate, not an oversight: the module docstring records that an
    # AND-form draft produced ~90 false positives on the legitimate, widespread
    # "fact_key-pinned multi-row subject lookup" pattern. Those queries do not
    # reduce to one row, so they cannot exhibit the defect above, and the
    # calibration that excluded them stands.
    return not (has_fact_key or has_order_limit or has_distinct_on)


# ---------------------------------------------------------------------------
# Multi-formula rule (formula_id pin / all-variants disclosure)
# ---------------------------------------------------------------------------

_MULTI_FORMULA_CACHE: List[str] = []


def load_multi_formula_categories(path: Path = CANONICAL_FORMULAS_PY) -> List[str]:
    """The declared multi-formula categories, read from the ONE declaration (the Python canonical-
    formula module, loaded by file path; stdlib-only so this works with no package install). Raises
    RuntimeError when the declaration cannot be read -- an unreadable table must fail the lint loudly
    (exit 2), never degrade to "nothing is multi-formula"."""
    if _MULTI_FORMULA_CACHE and path == CANONICAL_FORMULAS_PY:
        return list(_MULTI_FORMULA_CACHE)
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location("_canonical_formulas_for_lint", path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        cats = list(mod.CANONICAL_FORMULAS)
    except Exception as exc:  # noqa: BLE001 -- surface any load failure as a config error
        raise RuntimeError(f"cannot load multi-formula declaration {path}: {exc}") from exc
    if not cats:
        raise RuntimeError(f"multi-formula declaration {path} lists no categories")
    if path == CANONICAL_FORMULAS_PY:
        _MULTI_FORMULA_CACHE[:] = cats
    return cats


_RE_FROM_CHART_FACTS = re.compile(r"\b(?:FROM|JOIN)\s+(?:public\s*\.\s*)?\"?chart_facts\"?\b", re.IGNORECASE)
_RE_FROM_KW = re.compile(r"\bFROM\b", re.IGNORECASE)
_RE_SELECT_KW = re.compile(r"\bSELECT\b", re.IGNORECASE)
_RE_ORDER_BY_SPLIT = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)
_RE_SETOP = re.compile(r"\b(?:UNION|INTERSECT|EXCEPT)\b", re.IGNORECASE)
_RE_ZERO_ROW = re.compile(r"\bLIMIT\s+0\b", re.IGNORECASE)
_RE_COUNT_ONLY = re.compile(r"^\s*COUNT\s*\(", re.IGNORECASE)
# A formula PIN is an equality / IN against formula_id in the WHERE of THIS statement. Deliberately
# NOT a pin: `formula_id IS [NOT] NULL`, `<>`, `!=`, `NOT IN`, a comparison against a column, and
# any formula_id comparison that lives in a nested subselect (those are blanked before this runs).
_RE_FORMULA_PIN = re.compile(r"\bformula_id\s*(?:=(?!=)|\bIN\b)", re.IGNORECASE)
_RE_FORMULA_WORD = re.compile(r"\bformula_id\b", re.IGNORECASE)
# A bare `*` / `alias.*` select-list item (NOT the star inside COUNT(*), which selects no column).
_RE_SELECT_STAR_ITEM = re.compile(r"(?:^|,)\s*(?:\w+\.)?\*\s*(?:,|$)")
_RE_LIKE_PREFIX = re.compile(r"\b(?:I?LIKE)\s+'([^'%_]*)[%_]", re.IGNORECASE)
_RE_REGEX_PREFIX = re.compile(r"~\*?\s*'\^([A-Za-z0-9_]*)", re.IGNORECASE)


def _select_list_has_formula_id(select_list: str) -> bool:
    return bool(_RE_FORMULA_WORD.search(select_list)) or bool(_RE_SELECT_STAR_ITEM.search(select_list))


def _names_declared_category(sql: str, categories: Sequence[str]) -> bool:
    """True iff the statement text names a declared category: a quoted literal, or a LIKE / ILIKE /
    `~ '^...'` PREFIX that a declared category starts with (`fact_category LIKE 'esoteric_point_%'`
    reads the declared esoteric_point_* categories without ever spelling one)."""
    if any(re.search(r"['\"]" + re.escape(c) + r"['\"]", sql) for c in categories):
        return True
    prefixes = [m.group(1) for m in _RE_LIKE_PREFIX.finditer(sql)] + [m.group(1) for m in _RE_REGEX_PREFIX.finditer(sql)]
    return any(p and any(c.startswith(p) for c in categories) for p in prefixes)


def _paren_scan(sql: str):
    """(depth_at, group_close): per-index paren depth and, for each '(' index, its matching ')'.
    String-aware for SQL single quotes, so a '(' inside a literal does not count."""
    n = len(sql)
    depth_at = [0] * (n + 1)
    group_close: dict = {}
    stack: List[int] = []
    in_str = False
    for i, ch in enumerate(sql):
        if ch == "'":
            in_str = not in_str
        if not in_str:
            if ch == "(":
                stack.append(i)
            elif ch == ")" and stack:
                group_close[stack.pop()] = i
        depth_at[i + 1] = len(stack)
    return depth_at, group_close


def _blank_nested_selects(text: str) -> str:
    """Blank (with spaces, preserving length) every parenthesised group that starts with SELECT/WITH:
    a nested subselect is judged as its OWN statement and must not lend its WHERE (a `formula_id = x`
    inside `IN (SELECT ...)`) to the statement that contains it."""
    _depth, close = _paren_scan(text)
    out = list(text)
    for o, c in sorted(close.items()):
        if re.match(r"\s*(?:SELECT|WITH)\b", text[o + 1 : c], re.IGNORECASE):
            for k in range(o, c + 1):
                if out[k] != "\n":
                    out[k] = " "
    return "".join(out)


def _chart_facts_statements(sql: str):
    """Yield one dict per SELECT statement that reads chart_facts (FROM / JOIN, optionally
    `public.`-qualified): {own, select_list, where, order, setop}. Each SELECT keyword starts its own
    statement, ending at its enclosing ')' , the next same-depth UNION / INTERSECT / EXCEPT, or the
    end of the text -- so the branches of a UNION are judged SEPARATELY (a pinned second branch cannot
    mask an unpinned first) and a nested subselect is judged on its own text."""
    depth_at, group_close = _paren_scan(sql)
    # enclosing group close for each index: derive from the open->close map
    encl_end = [len(sql)] * (len(sql) + 1)
    for o, c in sorted(group_close.items(), key=lambda kv: kv[1] - kv[0], reverse=True):
        for k in range(o, c + 1):
            encl_end[k] = c
    stmts = []
    for m in _RE_SELECT_KW.finditer(sql):
        s = m.start()
        end = encl_end[s]
        ended_by_setop = False
        for u in _RE_SETOP.finditer(sql, s, end):
            if depth_at[u.start()] == depth_at[s]:
                end = u.start()
                ended_by_setop = True
                break
        text = sql[s:end]
        own = _blank_nested_selects(text)
        fm = _RE_FROM_CHART_FACTS.search(own)
        if not fm:
            stmts.append({"start": s, "end": end, "setop": ended_by_setop, "depth": depth_at[s], "cf": False})
            continue
        first_from = _RE_FROM_KW.search(own)
        select_list = own[len("SELECT") : first_from.start()] if first_from else ""
        tail = own[fm.end() :]
        parts = _RE_ORDER_BY_SPLIT.split(tail, maxsplit=1)
        stmts.append({
            "start": s, "end": end, "setop": ended_by_setop, "depth": depth_at[s], "cf": True,
            "own": own, "select_list": select_list, "where": parts[0],
            "order": parts[1] if len(parts) > 1 else "",
        })
    # a UNION chain's trailing ORDER BY (on the last branch) governs every branch
    for idx, st in enumerate(stmts):
        if st["cf"] and st["setop"] and not st["order"]:
            for later in stmts[idx + 1 :]:
                if later["depth"] == st["depth"] and later["cf"]:
                    st["order"] = later["order"]
                    if not later["setop"]:
                        break
    return [st for st in stmts if st["cf"]]


def _statement_satisfies(st: dict) -> bool:
    """(a) a formula pin in the statement's own WHERE, or (b) all-variants disclosure: formula_id
    (or a bare *) selected AND formula_id in the ORDER BY."""
    if _RE_FORMULA_PIN.search(st["where"]):
        return True
    return _select_list_has_formula_id(st["select_list"]) and bool(_RE_FORMULA_WORD.search(st["order"]))


def _is_formula_unpinned_block(sql: str, categories: Sequence[str]) -> bool:
    """Pure predicate: True iff ANY chart_facts SELECT statement in this SQL text names a declared
    multi-formula category (a quoted literal, or a LIKE / regex prefix) and satisfies NEITHER (a) a
    formula_id pin NOR (b) all-variants disclosure. Every statement is judged on its own: all UNION
    branches and all nested subselects must satisfy the rule. Exempt per statement: zero-row
    availability probes (`LIMIT 0`) and aggregate-only `SELECT COUNT(...)`."""
    if not _RE_FROM_CHART_FACTS.search(sql):
        return False
    for st in _chart_facts_statements(sql):
        if not _names_declared_category(st["own"], categories):
            continue
        if _RE_ZERO_ROW.search(st["own"]) or _RE_COUNT_ONLY.search(st["select_list"]):
            continue
        if not _statement_satisfies(st):
            return True
    return False


def scan_python_formula_text(text: str, categories: Sequence[str] = ()) -> List[tuple]:
    """(line, snippet) for Python SQL string literals that break the multi-formula rule."""
    cats = list(categories) or load_multi_formula_categories()
    hits: List[tuple] = []
    for m in _PY_STRING_RE.finditer(text):
        content = next((g for g in m.groups() if g is not None), "")
        if not content or "chart_facts" not in content.lower():
            continue
        if _is_formula_unpinned_block(content, cats):
            line = text.count("\n", 0, m.start()) + 1
            hits.append((line, " ".join(content.split())[:160]))
    return hits


def _ts_string_literals(text: str) -> List[tuple]:
    """[(start_index, raw_literal)] for every TS string literal -- backtick templates AND '...' / "..."
    strings -- found by a small state machine that is STRING-AWARE and COMMENT-AWARE: `//` and `/* */`
    inside a string are text, not comments (a `/*` in a SQL string cannot swallow the code after it),
    and a backtick quoted inside a comment cannot misalign the literals that follow. `${ ... }`
    template expressions are scanned as code (nested templates and strings included).
    Not handled (documented false-negative): regex literals containing quotes, and SQL assembled by
    concatenating several string literals (each fragment is judged alone)."""
    n = len(text)
    lits: List[tuple] = []

    def code(i: int, in_expr: bool) -> int:
        depth = 0
        while i < n:
            c = text[i]
            two = text[i : i + 2]
            if two == "//":
                j = text.find("\n", i)
                i = n if j < 0 else j
                continue
            if two == "/*":
                j = text.find("*/", i + 2)
                i = n if j < 0 else j + 2
                continue
            if c in "'\"":
                j = i + 1
                while j < n and text[j] != c and text[j] != "\n":
                    j += 2 if text[j] == "\\" else 1
                lits.append((i, text[i : j + 1]))
                i = j + 1
                continue
            if c == "`":
                i = template(i)
                continue
            if in_expr:
                if c == "{":
                    depth += 1
                elif c == "}":
                    if depth == 0:
                        return i
                    depth -= 1
            i += 1
        return i

    def template(i: int) -> int:
        start, j = i, i + 1
        while j < n:
            c = text[j]
            if c == "\\":
                j += 2
                continue
            if c == "`":
                lits.append((start, text[start : j + 1]))
                return j + 1
            if c == "$" and text[j + 1 : j + 2] == "{":
                j = code(j + 2, True) + 1
                continue
            j += 1
        lits.append((start, text[start:]))
        return n

    code(0, False)
    return lits


def scan_ts_formula_text(text: str, categories: Sequence[str] = ()) -> List[tuple]:
    """(line, kind, snippet) for TS SQL literals (templates and quoted strings) that break the
    multi-formula rule."""
    cats = list(categories) or load_multi_formula_categories()
    hits: List[tuple] = []
    for start, sql in _ts_string_literals(text):
        if "chart_facts" not in sql.lower():
            continue
        sql = sql.replace("\\'", "'").replace('\\"', '"')  # a quote escaped for the TS string is a plain quote in the SQL
        if _is_formula_unpinned_block(sql, cats):
            line = text.count("\n", 0, start) + 1
            hits.append((line, "formula_unpinned_sql", " ".join(sql.split())[:160]))
    return hits


def _all_sql_literals(text: str) -> List[str]:
    lits = [raw for _s, raw in _ts_string_literals(text)]
    lits.extend(
        next((g for g in m.groups() if g is not None), "") for m in _PY_STRING_RE.finditer(text)
    )
    return [x for x in lits if x]


def load_reader_contract(path: Path = READERS_PATH) -> dict:
    """Parse multi_formula_readers.json -> {"readers": [...], "known_open_readers": [...]}."""
    if not path.exists():
        raise RuntimeError(f"multi-formula reader list missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc
    readers = data.get("readers")
    if not isinstance(readers, list) or not readers:
        raise RuntimeError(f"{path} must list at least one reader under 'readers'")
    for r in readers:
        if not isinstance(r, dict) or not r.get("file") or not r.get("why"):
            raise RuntimeError(f"{path}: every reader needs a 'file' and a non-empty 'why'")
        if r.get("mode", "disclose") not in ("pin", "disclose"):
            raise RuntimeError(f"{path}: reader {r['file']} has mode {r.get('mode')!r}; use 'pin' or 'disclose'")
        if not r.get("select_markers") or not isinstance(r["select_markers"], list):
            raise RuntimeError(f"{path}: reader {r['file']} needs a non-empty 'select_markers' list")
        if not r.get("order_tokens") or not isinstance(r["order_tokens"], list):
            raise RuntimeError(f"{path}: reader {r['file']} needs a non-empty 'order_tokens' list")
    known = data.get("known_open_readers", [])
    if not isinstance(known, list):
        raise RuntimeError(f"{path}: 'known_open_readers' must be a list")
    listed = {r["file"] for r in readers}
    for k in known:
        if not isinstance(k, dict) or not k.get("file") or not k.get("status") or not k.get("why"):
            raise RuntimeError(f"{path}: every known_open_readers entry needs 'file', 'status' and 'why'")
        if k["file"] in listed:
            raise RuntimeError(f"{path}: {k['file']} is both an enforced reader and a known-open reader")
    return {"readers": readers, "known_open_readers": known}


def _norm(s: str) -> str:
    return " ".join(s.split())


def check_reader_contract(root: Path, contract) -> List["Violation"]:
    """Structural check for dynamic-category readers (see the module docstring). `contract` is the
    dict from load_reader_contract (or, for convenience, the bare readers list).

    Per listed reader: (1) the file references canonical_formulas; (2) EVERY `marker` statement -- each
    chart_facts SELECT whose own text contains one of `select_markers` -- is formula-aware: in mode
    "pin" it pins formula_id in its WHERE, in mode "disclose" it selects formula_id (or a bare *); and
    (3) the file holds an ORDER BY fragment that names formula_id AND every one of `order_tokens`
    (e.g. the canonical-first rank, fact_subject, fact_id), so a total, canonical-first order cannot
    be silently dropped. A missing marker is itself a violation (the anchor moved: re-aim it)."""
    readers = contract["readers"] if isinstance(contract, dict) else list(contract)
    out: List[Violation] = []

    def v(rel: str, snippet: str, msg: str) -> None:
        out.append(Violation(rel, 1, "typescript", "reader_contract", snippet, msg))

    for r in readers:
        rel = r["file"]
        path = root / rel
        if not path.is_file():
            v(rel, "(missing file)", f"listed multi-formula reader {rel} does not exist; fix or remove the entry in multi_formula_readers.json.")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        mode = r.get("mode", "disclose")
        if "canonical_formulas" not in text:
            v(rel, "(no canonical_formulas reference)",
              "listed multi-formula reader does not reference the canonical_formulas module: it cannot be choosing a canonical formula or labelling variants.")
        literals = _all_sql_literals(text)
        statements = [st for lit in literals if "chart_facts" in lit.lower() for st in _chart_facts_statements(lit)]
        for marker in r["select_markers"]:
            nm = _norm(marker)
            marked = [st for st in statements if nm in _norm(st["own"])]
            if not marked:
                v(rel, f"(select marker not found: {marker!r})",
                  "no chart_facts SELECT in this reader contains the marker declared in multi_formula_readers.json; the query moved or was renamed -- re-aim select_markers.")
                continue
            for st in marked:
                if mode == "pin" and not _RE_FORMULA_PIN.search(st["where"]):
                    v(rel, _norm(st["own"])[:140], "reader (mode pin) has a chart_facts SELECT with no `formula_id = ...` / `formula_id IN` pin in its WHERE.")
                if mode == "disclose" and not _select_list_has_formula_id(st["select_list"]):
                    v(rel, _norm(st["own"])[:140], "reader (mode disclose) has a chart_facts SELECT that does not select formula_id, so the variants it serves cannot be labelled.")
        order_fragments = [
            lit[m.end():]
            for lit in literals
            for m in _RE_ORDER_BY_SPLIT.finditer(lit)
        ]
        wanted = ["formula_id", *r["order_tokens"]]
        if not any(all(tok in frag for tok in wanted) for frag in order_fragments):
            v(rel, f"(no ORDER BY naming {wanted})",
              "reader has no ORDER BY fragment containing formula_id and every declared order token "
              f"{r['order_tokens']}: the total, canonical-first order was dropped or weakened.")
    return out


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


def scan_ts_sql_text(text: str) -> List[tuple]:
    """Return (line, kind, snippet) for unsafe chart_facts SQL in TS template literals.

    scan_ts_text below only ever inspected `.find(...)` / `.filter(...)[0]` over
    an in-memory fact array. Raw SQL in a backtick template literal -- which is
    how the serving layer actually queries chart_facts -- was never scanned at
    all, so `deriveShadbalaWeakestGraha` (L2_bodha/query_ucd.ts) was invisible
    to this guard on top of being permitted by the pre-tightening rule.

    `_is_unsafe_sql_block` is reused deliberately rather than reimplemented:
    one rule, two host languages, so the SQL rule cannot drift between them.
    """
    hits: List[tuple] = []
    for m in re.finditer(r"`[^`]*`", text, re.S):
        sql = m.group(0)
        if not _is_unsafe_sql_block(sql):
            continue
        line = text.count("\n", 0, m.start()) + 1
        snippet = " ".join(sql.split())[:160]
        hits.append((line, "sql_select", snippet))
    return hits


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


FORMULA_MESSAGE = (
    "SELECT against chart_facts names a declared multi-formula category (canonical_formulas.py) "
    "without pinning formula_id (`formula_id = ...` in the WHERE) and without disclosing all "
    "variants (formula_id selected AND in ORDER BY). `ga_sensitive` writes one row per formula_id, "
    "so fact_category + fact_key alone still returns a physical-order-dependent winner "
    "(INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md; SS decision 2026-10-01)."
)


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
                        "without a fact_key pin. A deterministic ORDER BY ... "
                        "LIMIT 1 / DISTINCT ON is NOT sufficient on its own: it "
                        "makes the result reproducible, not correct (§N.7 item 2 "
                        "— the D1 defect class; F-C14 / issue #1750)."
                    ),
                )
            )

    for path in expand_globs(root, py_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, snippet in scan_python_formula_text(text):
            violations.append(
                Violation(file=rel, line=line, lang="python", kind="formula_unpinned_sql",
                          snippet=snippet, message=FORMULA_MESSAGE)
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

        for line, kind, snippet in scan_ts_formula_text(text):
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    lang="typescript",
                    kind=kind,
                    snippet=snippet,
                    message=FORMULA_MESSAGE,
                )
            )

        for line, kind, snippet in scan_ts_sql_text(text):
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    lang="typescript",
                    kind=kind,
                    snippet=snippet,
                    message=(
                        "SQL template literal against chart_facts filters by "
                        "fact_category without a fact_key pin. A deterministic "
                        "ORDER BY ... LIMIT 1 / DISTINCT ON is NOT sufficient on "
                        "its own: it makes the result reproducible, not correct "
                        "(§N.7 item 2 — the D1 defect class; F-C14 / issue #1750)."
                    ),
                )
            )

    violations.extend(check_reader_contract(root, load_reader_contract()))

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

    try:
        cats = load_multi_formula_categories()
    except RuntimeError as exc:
        print(f"check_fact_category_pinning: SELF-TEST — {exc}", file=sys.stderr)
        return 2

    def _hits(fixture: Path) -> List[tuple]:
        text = fixture.read_text(encoding="utf-8")
        formula_only = fixture.name.startswith("formula_pin__")
        if fixture.suffix == ".py":
            old = [] if formula_only else scan_python_text(text)
            return old + scan_python_formula_text(text, cats)
        if fixture.suffix == ".ts":
            # Both TS scanners, so a fixture exercising SQL template literals is actually covered.
            # Running only scan_ts_text here is how the F-C14 gap could have shipped a green
            # self-test alongside a blind scanner. `formula_pin__*` fixtures exercise ONLY the
            # multi-formula rule (they pin fact_key, so the older rule is silent on them anyway).
            old = [] if formula_only else [
                (line, snippet) for line, _k, snippet in (scan_ts_text(text) + scan_ts_sql_text(text))
            ]
            return old + [(line, snippet) for line, _k, snippet in scan_ts_formula_text(text, cats)]
        return []

    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix not in (".py", ".ts"):
            continue
        hits = _hits(fixture)
        if hits:
            failures.append(f"PASS-fixture '{fixture.name}' was flagged (false positive): {hits}")

    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file() or fixture.suffix not in (".py", ".ts"):
            continue
        if not _hits(fixture):
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
    try:
        violations = scan_repo(root, DEFAULT_PY_GLOBS, DEFAULT_TS_GLOBS)
    except RuntimeError as exc:
        print(f"check_fact_category_pinning: CONFIG ERROR — {exc}", file=sys.stderr)
        return 2
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
