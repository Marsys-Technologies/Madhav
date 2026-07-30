#!/usr/bin/env python3
"""check_earned_signal.py — the standing §N.8 Earned-Signal guard (SAMĀPTI, lane B-N8-LINT).

Sibling to `check_fact_category_pinning.py` (#840, the D1 fact_key guard) and
deliberately built to the same shape: bundled PASS/FAIL fixtures + `--self-test`,
an allowlist-aware repo scan, `--strict`, `--json`, and the same exit-code policy.

The doctrine it enforces
------------------------
`CLAUDE.md §N.8` (Earned-Signal Principle):

    "Every status, grade, or PASS must be computed by a detector that measures
     the specific claim it asserts; a signal without such a detector is null,
     not green."

The operational corollary this lint mechanises — and the ONLY one it mechanises:

    A field whose NAME asserts a status / verification / grade / verdict / gate /
    violation-count must not be assigned a value that is fixed at edit time.
    The sanctioned value for a signal with no detector is the null sentinel
    (`None` in Python, `null` / `undefined` in TypeScript) — never a constant,
    in EITHER polarity. A hardcoded `'PASS'` is an unearned green; a hardcoded
    `false` is an equally uninformative unearned red (§N.8's CANNOT-FAIL GATE
    class explicitly includes "the inverse: an always-red gate, whose red is
    equally uninformative"). Both are flagged. `None`/`null`/`undefined` is not.

============================================================================
WHAT THIS LINT CATCHES  (exhaustive — if a pattern is not on this list, it is
                         not caught, whatever the field is named)
============================================================================

ONE class only: **LITERAL** — a signal-named field bound to an expression whose
value is decided entirely at edit time, because the expression contains no name
reference, no attribute access, no subscript, no call, and no comprehension. No
program input, DB row, or argument can change it.

Python (`--py-globs`, default `platform/python-sidecar/**/*.py`), via the `ast`
module (not regex), at these five binding sites:

  (P-a) dict-literal entry with a `str` key      `{"verification_pass_status": "PASS"}`
  (P-b) keyword argument at a call site          `emit(passed=True)`
  (P-c) assignment to a bare name                `views_verified = True`
  (P-d) assignment to an attribute               `self.gate_open = True`
  (P-e) assignment to a constant-string subscript `row["lel_zero_leak_pass"] = True`

  ...where the bound value is constant-folded: `ast.Constant` (except `None`),
  or any `BoolOp`/`BinOp`/`UnaryOp`/`Compare`/`Tuple`/`List`/`Set`/`JoinedStr`
  built exclusively out of such constants (so `0 == 0`, `True and True`, and
  `f"PASS"` are caught alongside the bare literals).

TypeScript (`--ts-globs`, default `platform-mcp/src/**/*.ts` +
`platform/src/**/*.ts`), via a line-scoped regex (there is no TS parser in this
stdlib-only script — see the bounds section):

  (T-a) object-literal property with a literal value
        `stale: false,`   `verdict: 'PASS',`   `accounted_pct: "100%",`
  (T-b) plain assignment to a literal
        `result.orientation_ok = true;`

Name matching is by the curated vocabulary block below — `SIGNAL_NAMES_EXACT`,
`SIGNAL_NAME_SUFFIXES`, `SIGNAL_NAME_CONTAINS`, and the `COUNTER_*` rule
(`*_count`/`*_total` whose name also carries a defect word such as
`leak`/`violation`/`divergen`). The vocabulary is deliberately a closed list,
not a heuristic: see "does not catch" item 1.

Ground truth it was calibrated against (SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0),
stated as MEASURED against the live tree, not as intended:
  F-11  `ga_nakshatra.py:87`          `verification_pass_status: "PASS"`  → CAUGHT (P-a)
  F-09  `bo_pramana_mapa.py:278`      `trap2_narration_leak_count: 0`     → CAUGHT (P-a)
  F-10  `bo_pramana_mapa.py:262`      `divergent_flagged_count: 0`        → CAUGHT (P-a)
  F-23  consult `route.ts:711-737`    hardcoded planner metrics           → CAUGHT (T-a)
  F-15  `bo_chart_gestalt.py:333-338` `fragility_class="multi_ayanamsha_tested"`
                                      → NOT caught — name outside the vocabulary
  F-20  `kala_envelope.ts:248-272`    `freshness.stale`
                                      → NOT caught in the live code. The source
                                      writes `let stale` then assigns in branches;
                                      the LITERAL-ness of F-20 is a dataflow fact
                                      (no caller ever passes `params.staleAfter`),
                                      which is class 3 above. The `stale: false`
                                      OBJECT-LITERAL form is caught, and the FAIL
                                      fixture pins that — but do not read the
                                      fixture as a claim on F-20 itself.

============================================================================
WHAT THIS LINT EXPLICITLY DOES **NOT** CATCH
============================================================================
Stated at length on purpose. This lint closes ONE of the five §N.8 finding
classes. A green from this lint is NOT evidence that a status field is earned —
it is evidence only that the field is not a bare constant. Claiming otherwise
would make this lint itself an §N.8 violation (SAMĀPTI v2.0 §7.5).

Of the 40 confirmed findings in SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0, this
lint's rule can reach the LITERAL class only — roughly a quarter of them. The
four classes it CANNOT reach, each with the register's own example:

 1. **Any signal whose name is outside the curated vocabulary.** The vocabulary
    is a closed list of ~40 names/suffixes. A new field called
    `fragility_class` (F-15) or `linking_mechanism` (F-16) asserts a status in
    prose but not in the vocabulary, and is invisible to this lint. Widening the
    vocabulary to "any field" is not possible without flagging every constant in
    the codebase. **Mitigation: when a lane adds a new status-shaped field name,
    it adds the name to the vocabulary block.** This lint's coverage is a
    maintained list, not an inference.

 2. **PROXY** — a real, falsifiable detector that measures something adjacent to
    the claim. `lel_zero_leak_pass = trap1_count == 0` (F-07) claims "no LEL
    leaked into the deterministic base" and actually counts citation-array gaps,
    never reading `life_events` at all. It is a runtime-dependent expression, so
    this lint passes it. **Detecting a proxy requires knowing what the field's
    name means — that is a human/audit judgement, and there is no syntactic
    signal for it.** The same applies to F-14, F-21, F-22.

 3. **TAUTOLOGY reachable only by dataflow.** `pillars_pass = msr_count > 0`
    (F-08) is unfalsifiable because `msr_count == 0` raises ~160 lines earlier —
    but the expression itself references a runtime name, so it passes this
    lint's constant-folding test. Proving it requires interprocedural reachability
    analysis (undecidable in general, and out of scope for a CI regex/AST lint).
    Same for F-19 (`accounted === slice_size` where both operands come from the
    same precompiled bundle) and F-24 (`dbCount >= messageIds.length` where
    `dbCount` is not id-filtered).

 4. **CANNOT-FAIL GATE.** A check that runs but whose failure cannot propagate:
    `mi_darshana._substep_views_verify` (F-18) catches every exception into a
    notes string and returns success; `hard_gates_check.sh` (F-26) claims to
    "return 1 if any RED" and contains zero `exit` statements; `icr_weekly_scan.yml`
    (F-27) suppresses its only non-zero exit path with `--dry-run`; a guard that
    is simply never invoked in CI at all (F-02). None of these is a constant
    assignment; none is caught here.

 5. **Anything outside the scanned globs.** Shell scripts, YAML workflows, SQL
    migrations, `.tsx`, notebooks, and the whole of `platform/scripts/**` are NOT
    scanned. F-02 and F-26/F-27 live in exactly those places.

Known false-negative mechanics — the six deliberate suppressions, each measured
against the live tree at base `a7dfefcb` (SUPPRESSED COUNT in brackets):

  N1. **Branch-guarded constants** [~144]. A constant inside `if`/`else`, an
      `except` handler, a `match` case, or a loop `else` is a control-flow
      OUTCOME, not a frozen signal: `except Exception as exc: checks.append({...
      "passed": False, "error": str(exc)})` is a correct failure record. Cost:
      `if x: s='PASS'` / `else: s='PASS'` — constant in every branch — is missed.
  N2. **CONSTANT_CASE dict tables** [~605]. A dict literal assigned to a
      CONSTANT_CASE name is a lookup/weight/seed table, and its entries are data:
      `VERIFICATION_RESCALE = {"two_pass_verified": 1.00, "single_pass": 0.85}`.
      This suppression also covers the six `brahmagyan/bodha/l2_grounded_batch_*.py`
      seed corpora (569 `"grounding_status": "GROUNDED"` rows inside
      `GROUNDED_SIGNALS: dict[...] = {...}`). **Named explicitly because it is
      the single largest thing this lint chooses not to see.** Whether those
      authored rows were actually grounded is a real §N.8 question about the
      SEEDING process — it is an audit question, not a syntax question, and this
      lint does not answer it.
  N3. **CONSTANT_CASE field names** [~6]. `ACHARYA_GRADE = 'A'`,
      `FALSIFIER_GATE = true` — the naming convention IS the declaration that
      the value is fixed. Whether a consumer then passes the constant off as a
      computed signal is a different (uncaught) analysis.
  N4. **`expected_*` / `want_*` / `golden_*` names** [~30]. An authored
      expectation is the left-hand side of a comparison, not its result;
      hardcoding it is correct for that role.
  N5. **Rebound / mutable bindings**. Python: a bare-name assignment (P-c) is
      skipped when the name is re-bound elsewhere in the same function
      (`n = 0` … `n += 1`); a dict entry (P-a) is skipped when the same key is
      also written via subscript in that file; an attribute or subscript target
      written more than once in a file is skipped. TypeScript: an assignment to
      an identifier declared `let`/`var` anywhere in the file is skipped
      (`let stale = false` … `stale = true`).
  N6. **SQL inside TypeScript template literals** [~4]. Any TS line carrying
      SQL keywords is skipped — `COUNT(*) FILTER (WHERE composite_verdict =
      'confirmed')` is query text, not an assignment.

Further false-negative mechanics:
  - Python: a constant that reaches the field through an intermediate module
    constant (`STATUS = "PASS"` … `{"verification_pass_status": STATUS}`) is a
    name reference, so it is NOT flagged. Indirection defeats this lint.
  - TypeScript: no parser. A property split across lines, a value built by a
    ternary of two constants, a spread that injects the constant from elsewhere,
    or a constant reached through a helper is not seen. There is also no
    branch-guard analysis on the TS side (N1 is Python-only).

Known false-positive mechanics:
  - TypeScript: a string-literal union in a type position (`status?: 'a' | 'b'`)
    is filtered by the `?:`/trailing-`|` heuristics, but an unusual formatting
    could slip through. `.d.ts` files are excluded outright.
  - Python: a constant passed as a keyword to a *test double* or a builder in
    non-test code (e.g. seeding a fixture row from a script) is a legitimate
    hardcode, flagged anyway. Disposition is via the allowlist, with a written
    justification — the same convention as #840.

============================================================================
State against the live tree at rollout (base `a7dfefcb`, 2026-07-31)
============================================================================
**Not clean — 169 pre-existing violations across 81 (file, field) groups**, all
recorded in `earned_signal_allowlist.json` with a stated disposition category.
They are carried as FROZEN debt (`max_occurrences`), not hidden and not used to
block this lint's own merge. Reading the allowlist is the point: it is the
backlog.

The scan independently rediscovered six register findings without being told
where to look, which is this lint's ground-truth check:
  F-09/F-10 `bo_pramana_mapa.py` literal counters · F-11 `ga_nakshatra.py:87`
  `verification_pass_status: "PASS"` · F-19 `dossier.ts` `synthesis_gate` ·
  F-22 `registry_bridge.ts` `orientation_ok` · F-23 consult `route.ts`
  `fallback_used` / `parsing_success` / `planning_confidence`.
It did NOT rediscover F-07, F-08, F-13, F-14, F-18, F-21, F-24, F-26, F-27 —
exactly the classes listed as uncaught above. That asymmetry is the honest
measure of this lint's reach.

Maintenance obligation this lint places on future lanes: when you add a
status/verification-shaped field, add its NAME to the vocabulary block. Coverage
here is a maintained list, not an inference.

Modes
-----
  --self-test   Run the bundled fixtures under earned_signal_fixtures/{pass,fail}/.
                Exit 0 iff every PASS fixture is silent and every FAIL fixture is
                flagged. DB-free, repo-free — the hermetic CI gate, and the
                lint's own can-fail proof.
  (default)     Scan the live repo tree. Reports every violation; only NEW
                (non-allowlisted) violations fail the build. Pre-existing
                violations found at rollout are recorded in
                earned_signal_allowlist.json with a written justification.
  --strict      Fail on ANY violation, including allowlisted ones.

Exit codes
----------
  0  clean (or self-test pass)
  1  non-allowlisted violation(s) found (or self-test fail)
  2  invocation / config error
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # platform/scripts/governance -> repo root
FIXTURE_DIR = SCRIPT_DIR / "earned_signal_fixtures"
ALLOWLIST_PATH = SCRIPT_DIR / "earned_signal_allowlist.json"

DEFAULT_PY_GLOBS = ["platform/python-sidecar/**/*.py"]
DEFAULT_TS_GLOBS = ["platform-mcp/src/**/*.ts", "platform/src/**/*.ts"]

# Mirrors check_fact_category_pinning.py's exclusion discipline: never scan this
# lint's own fixtures (they are deliberately-unsafe examples), nor test/generated
# trees — a test asserting `expect(x.passed).toBe(true)` or building a fixture row
# with a hardcoded status is not the defect class.
EXCLUDE_SUBSTRINGS = (
    "earned_signal_fixtures/",
    "fact_category_pin_fixtures/",
    "/__tests__/",
    "/tests/",
    "/test/",
    "/node_modules/",
    "/generated/",
    "/__pycache__/",
    ".test.ts",
    ".spec.ts",
    ".d.ts",
    "/conftest.py",
)
EXCLUDE_BASENAME_PREFIXES = ("test_",)


# ---------------------------------------------------------------------------
# The signal-name vocabulary — a CLOSED, CURATED LIST, not a heuristic.
#
# Every entry traces to a confirmed finding in
# SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0 or to CLAUDE.md §N.7 item 4 / §N.8.
# Adding a status-shaped field to the codebase means adding its name here — the
# lint's coverage is maintained, not inferred (see docstring "does not catch" 1).
# ---------------------------------------------------------------------------

# Exact field names (case-insensitive; TS camelCase handled by normalisation).
SIGNAL_NAMES_EXACT: frozenset = frozenset(
    {
        "passed",
        "verified",
        "verdict",
        "gate_open",
        "gateopen",
        "gate_passed",
        "orientation_ok",
        "fully_accounted",
        "parsing_success",
        "fallback_used",
        "stale",
        "is_stale",
        "verification_status",
        "verification_pass_status",
        "epistemic_grade",
        "planning_confidence",
        "two_pass_verified",
        "no_pre_answer_pass",
        "health_status",
        "grounding_status",
    }
)

# Name suffixes. A field ending in one of these asserts a status about itself.
SIGNAL_NAME_SUFFIXES: Tuple[str, ...] = (
    "_pass",
    "_passed",
    "_verified",
    "_verdict",
    "_grade",
    "_gate",
    "_gate_open",
    "_ok",
    "_pass_status",
    "_verification_status",
    "_health",
    "_clean",
    "_conformant",
    "_compliant",
)

# Substrings that make an otherwise-generic name a verification claim. Kept
# narrow on purpose: bare `status` / `confidence` / `flag` are NOT in the
# vocabulary — they are far too common in this codebase (job states, LLM
# metadata, feature toggles) and including them produced overwhelmingly
# non-defect hits during rollout calibration. See the calibration note below.
SIGNAL_NAME_CONTAINS: Tuple[str, ...] = (
    "verification_pass",
    "verified_fraction",
    "zero_leak",
    "no_threshold_drop",
    "reachability_pass",
    "byte_equal",
    "byte_identical",
)

# Violation counters: a `*_count` / `*_total` whose name also names a defect.
# A literal 0 here asserts "we looked and found none" (F-09, F-10).
COUNTER_SUFFIXES: Tuple[str, ...] = ("_count", "_total", "_pct", "_percent")
COUNTER_DEFECT_WORDS: Tuple[str, ...] = (
    "leak",
    "violation",
    "divergen",
    "inversion",
    "mismatch",
    "contamination",
    "drift",
    "orphan",
    "unresolved",
    "breach",
    "tamper",
)

# ---------------------------------------------------------------------------
# ROLLOUT CALIBRATION NOTE (be honest about how this vocabulary was chosen).
#
# The first draft matched any name ending in `_status`, `_flag`, or
# `_confidence`, plus bare `status` / `ok` / `confidence` / `success`. Measured
# against the live tree at base `a7dfefcb` that draft produced hundreds of hits
# that were overwhelmingly NOT the defect class: job/queue lifecycle states
# (`status="queued"`), LLM response metadata, feature toggles, HTTP status
# constants, and default-argument-shaped call kwargs. A lint whose output is
# mostly noise gets allowlisted wholesale and stops being read — which is how a
# gate becomes a CANNOT-FAIL gate (§N.8's own fourth class).
#
# The vocabulary above is therefore the calibrated subset: names that assert a
# VERIFICATION result about the data or the build, rather than a lifecycle or
# transport state. The cost is stated plainly in "does not catch" item 1 — a
# status-shaped field with a name outside this list is invisible, and keeping
# the list current is a maintenance obligation on every lane that adds one.
# ---------------------------------------------------------------------------


# Names that match the vocabulary above but are provably not the defect class.
# Each is here for a stated reason — this list is small and closed on purpose,
# because a growing exclusion list is how a lint quietly stops enforcing.
NAME_EXCLUSIONS: frozenset = frozenset(
    {
        # stdlib/library keyword arguments that happen to end in `_ok`.
        "exist_ok",
        "ok",
        # an auth/profile attribute of a user record, not a chart/build signal.
        "email_verified",
    }
)

# A name beginning with `expected_` is, by definition, an AUTHORED expectation —
# the left-hand side of a comparison, not its result. Eval corpora and golden
# fixtures are full of them (`expected_verdict: 'PASS'`), and a hardcoded
# expectation is the correct shape for that role.
EXCLUDED_NAME_PREFIXES: Tuple[str, ...] = ("expected_", "want_", "golden_")


def _is_constant_case(name: str) -> bool:
    """CONSTANT_CASE (`ACHARYA_GRADE`, `_CREATE_VIEW_CLEAN`, `FALSIFIER_GATE`) is
    the language's own declaration that a value is a fixed constant. Flagging a
    declared constant for being constant is noise, not a finding — the §N.8
    question for a module constant is whether a *consumer* passes it off as a
    computed signal, which is a different (uncaught) analysis."""
    stripped = name.lstrip("_")
    return bool(stripped) and stripped.upper() == stripped and any(c.isalpha() for c in stripped)


def _normalise_name(name: str) -> str:
    """camelCase/PascalCase -> snake_case, lowercased. `gateOpen` -> `gate_open`."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return s.lower()


def is_signal_name(raw_name: str) -> bool:
    if _is_constant_case(raw_name):
        return False
    name = _normalise_name(raw_name)
    if name in NAME_EXCLUSIONS:
        return False
    if any(name.startswith(p) for p in EXCLUDED_NAME_PREFIXES):
        return False
    if name in SIGNAL_NAMES_EXACT:
        return True
    if any(name.endswith(sfx) for sfx in SIGNAL_NAME_SUFFIXES):
        return True
    if any(frag in name for frag in SIGNAL_NAME_CONTAINS):
        return True
    if any(name.endswith(sfx) for sfx in COUNTER_SUFFIXES) and any(
        w in name for w in COUNTER_DEFECT_WORDS
    ):
        return True
    return False


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    file: str  # repo-relative POSIX path
    line: int  # 1-indexed
    lang: str  # "python" | "typescript"
    kind: str  # binding-site code, e.g. "dict_entry"
    field: str
    snippet: str
    message: str

    def key(self) -> str:
        return f"{self.file}|{self.kind}|{self.field}|{self.snippet}"


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def _excluded(rel: str) -> bool:
    if any(s in rel for s in EXCLUDE_SUBSTRINGS):
        return True
    base = rel.rsplit("/", 1)[-1]
    return any(base.startswith(p) for p in EXCLUDE_BASENAME_PREFIXES)


def expand_globs(root: Path, globs: Sequence[str]) -> List[Path]:
    out: Set[Path] = set()
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
# Python scanner — ast-based
# ---------------------------------------------------------------------------

# Node types that may appear in a constant-folded expression. Anything else
# (Name, Attribute, Call, Subscript, comprehension, Await, Lambda, Starred, ...)
# means the value depends on a runtime input, and the site is NOT flagged.
_CONST_CONTAINER_NODES = (
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Tuple,
    ast.List,
    ast.Set,
    ast.Dict,
    ast.JoinedStr,
    ast.IfExp,
    ast.And,
    ast.Or,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.Invert,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    ast.FormattedValue,
    ast.Load,  # expression-context nodes are yielded by ast.walk
    ast.Store,
)


def is_edit_time_constant(node: ast.AST) -> bool:
    """True iff `node`'s value is fixed at edit time.

    Definition (the whole rule, stated precisely): every node in the subtree is
    either an `ast.Constant` or one of the pure container/operator nodes above.
    A single `Name`, `Attribute`, `Call`, `Subscript`, comprehension, `Await`,
    `Lambda` or `Starred` anywhere in the subtree disqualifies it — that is the
    lint's entire notion of "a detector exists", and it is a presence test, not
    a relevance test (docstring, "does not catch" items 2 and 3).

    `None` is excluded by the caller, not here: `None` is the SANCTIONED value
    for a signal with no detector, per §N.8.
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant):
            continue
        if isinstance(sub, _CONST_CONTAINER_NODES):
            continue
        return False
    return True


def _is_none(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _collect_branch_guarded(tree: ast.AST) -> Set[int]:
    """Ids of nodes that sit inside a CONDITIONAL region of the source.

    Why this matters, and why it is a principled narrowing rather than a
    convenience: a constant chosen by control flow is not an unearned signal.

        except Exception as exc:
            checks.append({"id": "AC5", "passed": False, "error": str(exc)})

    `passed: False` there is the *outcome* of a runtime condition — the handler
    only runs because something failed. The defect class this lint targets is a
    constant on an UNCONDITIONAL path (`ga_nakshatra.py:87` stamps `"PASS"` on
    every row, every chart, always). Measured against the live tree, this single
    rule removed ~90 hits that were all of the branch-outcome shape.

    Conditional regions: `If.body`/`If.orelse`, `IfExp.body`/`IfExp.orelse`,
    `Try.handlers`/`Try.orelse`, `For`/`While`.`orelse`, and every `match_case`.
    Loop *bodies* are NOT conditional for this purpose — a constant stamped on
    every row of a loop is precisely F-11. A nested function's body resets the
    flag: the function runs whenever it is called, regardless of where it was
    defined.

    Honest cost: `if x: s = 'PASS'` / `else: s = 'PASS'` — a constant in every
    branch — is a real violation this rule lets through. Whole-branch constant
    folding would be needed to catch it; that is not implemented.
    """
    guarded: Set[int] = set()

    def walk(node: ast.AST, is_guarded: bool) -> None:
        if is_guarded:
            guarded.add(id(node))
        for field, value in ast.iter_fields(node):
            child_guarded = is_guarded
            if isinstance(node, (ast.If, ast.IfExp)) and field in ("body", "orelse"):
                child_guarded = True
            elif isinstance(node, ast.Try) and field in ("handlers", "orelse"):
                child_guarded = True
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)) and field == "orelse":
                child_guarded = True
            elif isinstance(node, ast.ExceptHandler):
                child_guarded = True
            elif node.__class__.__name__ == "match_case":
                child_guarded = True
            elif (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
                and field == "body"
            ):
                child_guarded = False

            items: Iterable = value if isinstance(value, list) else [value]
            for item in items:
                if isinstance(item, ast.AST):
                    walk(item, child_guarded)

    walk(tree, False)
    return guarded


class _RebindCollector(ast.NodeVisitor):
    """Collect names re-bound anywhere inside a function body, and dict keys
    written via subscript anywhere in the module. Both feed false-positive
    suppression (docstring, "known false-negative mechanics")."""

    def __init__(self) -> None:
        self.subscript_key_writes: dict = {}
        self.attr_writes: dict = {}

    @property
    def subscript_string_keys(self) -> Set[str]:
        return set(self.subscript_key_writes)

    def visit_Assign(self, node: ast.Assign) -> None:
        for tgt in node.targets:
            if (
                isinstance(tgt, ast.Subscript)
                and isinstance(tgt.slice, ast.Constant)
                and isinstance(tgt.slice.value, str)
            ):
                k = tgt.slice.value
                self.subscript_key_writes[k] = self.subscript_key_writes.get(k, 0) + 1
            elif isinstance(tgt, ast.Attribute):
                self.attr_writes[tgt.attr] = self.attr_writes.get(tgt.attr, 0) + 1
        self.generic_visit(node)


def _names_bound_more_than_once(scope: ast.AST) -> Set[str]:
    """Names that are assigned/augmented/looped/with-bound more than once (or
    at least once by a non-Assign binder) inside `scope`."""
    counts: dict = {}

    def bump(name: str, weight: int = 1) -> None:
        counts[name] = counts.get(name, 0) + weight

    for sub in ast.walk(scope):
        if isinstance(sub, ast.Assign):
            for tgt in sub.targets:
                if isinstance(tgt, ast.Name):
                    bump(tgt.id)
        elif isinstance(sub, ast.AugAssign):
            if isinstance(sub.target, ast.Name):
                bump(sub.target.id, 2)  # an augment implies a prior binding
        elif isinstance(sub, ast.For):
            if isinstance(sub.target, ast.Name):
                bump(sub.target.id, 2)
        elif isinstance(sub, ast.withitem):
            if isinstance(sub.optional_vars, ast.Name):
                bump(sub.optional_vars.id, 2)
    return {n for n, c in counts.items() if c > 1}


def scan_python_text(text: str) -> List[Tuple[int, str, str, str]]:
    """Return (line, kind, field, snippet) for every LITERAL signal binding.

    Raises nothing: a file that fails to parse is reported as no hits (a syntax
    error is another gate's problem, not this one's).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    src_lines = text.splitlines()
    collector = _RebindCollector()
    collector.visit(tree)
    subscript_keys = collector.subscript_string_keys
    branch_guarded = _collect_branch_guarded(tree)

    # A dict literal assigned to a CONSTANT_CASE name is a lookup/weight table
    # (`VERIFICATION_RESCALE = {"two_pass_verified": 1.00, "single_pass": 0.85}`,
    # `_TIER_RANK = {...}`). Its keys are vocabulary terms and its values are the
    # table's data — not a signal being stamped on a row. Suppressed wholesale.
    const_table_dicts: Set[int] = set()
    for n in ast.walk(tree):
        tgts = (
            n.targets
            if isinstance(n, ast.Assign)
            else [n.target] if isinstance(n, ast.AnnAssign) else []
        )
        value = getattr(n, "value", None)
        if isinstance(value, ast.Dict) and any(
            isinstance(t, ast.Name) and _is_constant_case(t.id) for t in tgts
        ):
            for sub in ast.walk(value):
                if isinstance(sub, ast.Dict):
                    const_table_dicts.add(id(sub))

    # Per-scope rebind sets, computed lazily per enclosing function.
    scope_rebinds: dict = {}

    def rebinds_for(scope: ast.AST) -> Set[str]:
        key = id(scope)
        if key not in scope_rebinds:
            scope_rebinds[key] = _names_bound_more_than_once(scope)
        return scope_rebinds[key]

    # Map every node to its nearest enclosing function/module scope.
    parent_scope: dict = {}

    def annotate(scope: ast.AST) -> None:
        for child in ast.iter_child_nodes(scope):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annotate(child)
            else:
                for sub in ast.walk(child):
                    parent_scope.setdefault(id(sub), scope)
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        annotate(sub)
                parent_scope.setdefault(id(child), scope)

    annotate(tree)

    def snippet_at(node: ast.AST) -> str:
        ln = getattr(node, "lineno", 1)
        raw = src_lines[ln - 1] if 0 < ln <= len(src_lines) else ""
        return " ".join(raw.split())[:160]

    hits: List[Tuple[int, str, str, str]] = []

    def record(node: ast.AST, kind: str, field: str) -> None:
        hits.append((getattr(node, "lineno", 1), kind, field, snippet_at(node)))

    for node in ast.walk(tree):
        if id(node) in branch_guarded:
            continue  # a constant selected by control flow is a branch outcome

        # (P-a) dict-literal entries
        if isinstance(node, ast.Dict):
            if id(node) in const_table_dicts:
                continue
            for k, v in zip(node.keys, node.values):
                if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                    continue
                if not is_signal_name(k.value):
                    continue
                if _is_none(v) or not is_edit_time_constant(v):
                    continue
                if k.value in subscript_keys:
                    continue  # possibly overwritten later in this file
                record(k, "dict_entry", k.value)

        # (P-b) keyword arguments at call sites
        elif isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg is None or not is_signal_name(kw.arg):
                    continue
                if _is_none(kw.value) or not is_edit_time_constant(kw.value):
                    continue
                record(kw.value, "call_kwarg", kw.arg)

        # (P-c) bare-name assignment / (P-d) attribute assignment /
        # (P-e) constant-string subscript assignment
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is None or _is_none(value) or not is_edit_time_constant(value):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for tgt in targets:
                if isinstance(tgt, ast.Name):
                    if not is_signal_name(tgt.id):
                        continue
                    scope = parent_scope.get(id(node), tree)
                    if tgt.id in rebinds_for(scope):
                        continue  # initialiser pattern, later rebound
                    record(node, "name_assign", tgt.id)
                elif isinstance(tgt, ast.Attribute):
                    if not is_signal_name(tgt.attr):
                        continue
                    if collector.attr_writes.get(tgt.attr, 0) > 1:
                        continue  # overwritten elsewhere in this file
                    record(node, "attr_assign", tgt.attr)
                elif (
                    isinstance(tgt, ast.Subscript)
                    and isinstance(tgt.slice, ast.Constant)
                    and isinstance(tgt.slice.value, str)
                    and is_signal_name(tgt.slice.value)
                ):
                    if collector.subscript_key_writes.get(tgt.slice.value, 0) > 1:
                        continue  # placeholder later overwritten in this file
                    record(node, "subscript_assign", tgt.slice.value)

    return sorted(set(hits))


# ---------------------------------------------------------------------------
# TypeScript scanner — line-scoped regex (no parser in this stdlib-only script)
# ---------------------------------------------------------------------------

_TS_LITERAL = r"""(?:true|false|-?\d+(?:\.\d+)?|'[^'\\\n]*'|"[^"\\\n]*"|`[^`$\\\n]*`)"""

# (T-a) object-literal property: `name: <literal>` terminated by , } ; or EOL.
_TS_PROP_RE = re.compile(
    r"(?P<indent>^\s*)(?P<name>[A-Za-z_$][\w$]*)\s*:\s*(?P<value>" + _TS_LITERAL + r")\s*(?P<tail>[,;}]|$)"
)
# (T-b) assignment: `x.name = <literal>;`
_TS_ASSIGN_RE = re.compile(
    r"(?:^|[\s.])(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?P<value>" + _TS_LITERAL + r")\s*(?P<tail>[,;)]|$)"
)

_TS_COMMENT_RE = re.compile(r"^\s*(//|/\*|\*)")
# SQL embedded in a template literal reads exactly like a TS assignment
# (`COUNT(*) FILTER (WHERE composite_verdict = 'confirmed')`). Skip any line
# carrying SQL keywords — this lint has no business inside query text.
_TS_SQL_CONTEXT_RE = re.compile(
    r"\b(SELECT|FROM|WHERE|FILTER\s*\(|GROUP\s+BY|ORDER\s+BY|INSERT\s+INTO|UPDATE\s+\w+\s+SET|COALESCE)\b",
    re.IGNORECASE,
)
# `let x = false` / `var x = false` declares a MUTABLE variable; the initialiser
# is a starting value, not a frozen signal, and later `x = true` reassignments in
# the same file are the ordinary accumulate-then-report pattern. Mirrors the
# Python bare-name rebind suppression.
_TS_MUTABLE_DECL_RE_TEMPLATE = r"\b(?:let|var)\s+{name}\b"
# Type-position markers: an optional property (`name?: 'a' | 'b'`) or a value
# followed by `|` is a string-literal union type, not a value binding.
_TS_OPTIONAL_PROP_RE = re.compile(r"^\s*[A-Za-z_$][\w$]*\s*\?\s*:")


def scan_ts_text(text: str) -> List[Tuple[int, str, str, str]]:
    """Return (line, kind, field, snippet) for literal-bound signal fields."""
    hits: List[Tuple[int, str, str, str]] = []
    in_block_comment = False
    mutable_cache: dict = {}

    def declared_mutable(name: str) -> bool:
        if name not in mutable_cache:
            mutable_cache[name] = bool(
                re.search(_TS_MUTABLE_DECL_RE_TEMPLATE.format(name=re.escape(name)), text)
            )
        return mutable_cache[name]

    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")
        stripped = line.strip()

        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue
        if _TS_COMMENT_RE.match(line):
            continue
        # Strip a trailing line comment so `stale: false, // note` still matches
        # but `x; // stale: false` does not.
        code = line.split("//", 1)[0] if "//" in line else line
        if not code.strip():
            continue
        if _TS_SQL_CONTEXT_RE.search(code):
            continue

        snippet = " ".join(stripped.split())[:160]

        m = _TS_PROP_RE.search(code)
        if m and not _TS_OPTIONAL_PROP_RE.match(code):
            after = code[m.end():].lstrip()
            if not after.startswith("|") and is_signal_name(m.group("name")):
                hits.append((idx, "object_property", m.group("name"), snippet))
                continue

        m2 = _TS_ASSIGN_RE.search(code)
        if m2 and is_signal_name(m2.group("name")):
            after = code[m2.end():].lstrip()
            if not after.startswith("|") and not declared_mutable(m2.group("name")):
                hits.append((idx, "assignment", m2.group("name"), snippet))

    return hits


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

_PY_MESSAGE = (
    "signal-named field bound to an edit-time constant — no program input can "
    "make it read differently, so no detector stands behind it (CLAUDE.md §N.8). "
    "Give it a real detector, or set it to None."
)
_TS_MESSAGE = (
    "signal-named field bound to a literal — no program input can make it read "
    "differently, so no detector stands behind it (CLAUDE.md §N.8). Give it a "
    "real detector, or set it to null."
)


def scan_repo(
    root: Path, py_globs: Sequence[str], ts_globs: Sequence[str]
) -> List[Violation]:
    violations: List[Violation] = []

    for path in expand_globs(root, py_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, field, snippet in scan_python_text(text):
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    lang="python",
                    kind=kind,
                    field=field,
                    snippet=snippet,
                    message=f"`{field}`: {_PY_MESSAGE}",
                )
            )

    for path in expand_globs(root, ts_globs):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line, kind, field, snippet in scan_ts_text(text):
            violations.append(
                Violation(
                    file=rel,
                    line=line,
                    lang="typescript",
                    kind=kind,
                    field=field,
                    snippet=snippet,
                    message=f"`{field}`: {_TS_MESSAGE}",
                )
            )

    return violations


# ---------------------------------------------------------------------------
# Allowlist (same schema + fail-closed semantics as #840's)
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
    if entry.get("field") and entry["field"] != v.field:
        return False
    if entry.get("line") is not None:
        return int(entry["line"]) == v.line
    pattern = entry.get("pattern")
    if pattern:
        try:
            if re.search(pattern, v.snippet):
                return True
        except re.error:
            pass
        return pattern in v.snippet
    # A file+field entry with neither line nor pattern is a deliberate
    # file-scoped disposition; require the field to have been named so an
    # entry can never match everything in a file by accident.
    return bool(entry.get("field"))


def partition_allowlisted(violations: Sequence[Violation], allowlist: list):
    """Split into (allowlisted, new).

    `max_occurrences` is this lint's addition over #840's line-keyed allowlist,
    and it is load-bearing. A file+field entry covering N pre-existing hits would
    otherwise silently absorb every FUTURE hit of the same field in that file —
    an allowlist that grows without anyone deciding to grow it is exactly the
    CANNOT-FAIL gate §N.8 warns about. With `max_occurrences` the backlog is
    FROZEN at its rollout size: hit N+1 in a covered group is reported as NEW and
    fails the build, so the debt can be paid down but not added to.
    """
    allowed, new = [], []
    used: dict = {}
    for v in sorted(violations, key=lambda x: (x.file, x.line, x.field)):
        matched = None
        for i, entry in enumerate(allowlist):
            if not _matches_entry(v, entry):
                continue
            cap = entry.get("max_occurrences")
            if cap is not None and used.get(i, 0) >= int(cap):
                continue  # this entry's frozen budget is spent
            matched = i
            break
        if matched is None:
            new.append(v)
        else:
            used[matched] = used.get(matched, 0) + 1
            allowed.append(v)
    return allowed, new


def print_violations(violations: Sequence[Violation], prefix: str = "") -> None:
    for v in violations:
        print(f"{prefix}[{v.lang}][{v.kind}] {v.file}:{v.line} — {v.message}")
        print(f"{prefix}    {v.snippet}")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


def _scan_fixture(fixture: Path) -> Optional[List[tuple]]:
    text = fixture.read_text(encoding="utf-8")
    if fixture.suffix == ".py":
        return scan_python_text(text)
    if fixture.suffix == ".ts":
        return scan_ts_text(text)
    return None


_EXPECT_RE = re.compile(r"EXPECT-VIOLATIONS:\s*(\d+)")


def _expected_count(text: str) -> Optional[int]:
    """A FAIL fixture may declare `EXPECT-VIOLATIONS: N` in a comment. When it
    does, the self-test asserts the EXACT count, not merely 'at least one' —
    otherwise a fixture exercising five binding sites would keep passing after
    four of them silently regressed."""
    m = _EXPECT_RE.search(text)
    return int(m.group(1)) if m else None


def run_self_test() -> int:
    pass_dir = FIXTURE_DIR / "pass"
    fail_dir = FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        print("check_earned_signal: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2

    failures: List[str] = []
    n_pass = n_fail = 0

    for fixture in sorted(pass_dir.iterdir()):
        hits = _scan_fixture(fixture) if fixture.is_file() else None
        if hits is None:
            continue
        n_pass += 1
        if hits:
            failures.append(
                f"PASS-fixture '{fixture.name}' was flagged (false positive): {hits}"
            )

    for fixture in sorted(fail_dir.iterdir()):
        hits = _scan_fixture(fixture) if fixture.is_file() else None
        if hits is None:
            continue
        n_fail += 1
        if not hits:
            failures.append(
                f"FAIL-fixture '{fixture.name}' produced NO violation (false negative)"
            )
            continue
        expected = _expected_count(fixture.read_text(encoding="utf-8"))
        if expected is not None and len(hits) != expected:
            failures.append(
                f"FAIL-fixture '{fixture.name}' declares EXPECT-VIOLATIONS: {expected} "
                f"but produced {len(hits)}: {hits}"
            )

    if failures:
        print("check_earned_signal: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"check_earned_signal: SELF-TEST PASS "
        f"({n_pass} pass fixture(s) silent, {n_fail} fail fixture(s) caught)."
    )
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--self-test", action="store_true", help="Run bundled fixtures (DB-free, hermetic)."
    )
    ap.add_argument(
        "--strict", action="store_true", help="Fail on ANY violation, including allowlisted."
    )
    ap.add_argument("--root", default=str(REPO_ROOT), help="Repo root to scan.")
    ap.add_argument(
        "--py-globs", nargs="*", default=None, help="Override the Python scan globs."
    )
    ap.add_argument(
        "--ts-globs", nargs="*", default=None, help="Override the TypeScript scan globs."
    )
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    root = Path(args.root).resolve()
    py_globs = args.py_globs if args.py_globs is not None else DEFAULT_PY_GLOBS
    ts_globs = args.ts_globs if args.ts_globs is not None else DEFAULT_TS_GLOBS
    violations = scan_repo(root, py_globs, ts_globs)
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
            f"check_earned_signal: {len(allowed)} allowlisted violation(s) "
            f"(reported, not failing — see earned_signal_allowlist.json):"
        )
        print_violations(allowed, prefix="  ")

    if args.strict and violations:
        print(
            f"check_earned_signal: STRICT mode — {len(violations)} total violation(s) "
            f"(including allowlisted). FAIL.",
            file=sys.stderr,
        )
        print_violations(violations, prefix="  ")
        return 1

    if new:
        print(
            f"check_earned_signal: {len(new)} NON-ALLOWLISTED violation(s) found. FAIL.",
            file=sys.stderr,
        )
        print_violations(new, prefix="  ")
        return 1

    print(
        f"check_earned_signal: 0 new violations "
        f"({len(allowed)} pre-existing, allowlisted). PASS."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
