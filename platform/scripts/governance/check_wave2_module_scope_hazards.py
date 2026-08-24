#!/usr/bin/env python3
"""check_wave2_module_scope_hazards.py — a MEASUREMENT, not a repair, of Wave 2's 53 files.

Nirmāṇa WORK_QUEUE **M0-T85**, authorised by ruling **D-125** (F-V82-1: "GUARDED asserts one
thing — main() is not invoked on import. It does NOT assert the file is safe to import.") and
discharging **D-126 item 2 / D-80 section 5**'s outstanding recording obligation ("Wave 2
RECORDS IT PER FILE" — the env-mutation column that D-80 ordered and nothing checked was
written).

Sibling to `check_entrypoint_guard_ratchet.py` (same directory, same house style: bundled
PASS/FAIL fixtures, `--self-test`, `--json`, stdlib only, no DB, no network) — modelled on it
structurally per the M0-T85 task's own instruction, but a DIFFERENT SHAPE OF TOOL: the ratchet
is a pay-down GATE with an allowlist and a floor; this is a REPORT with no allowlist, no floor,
and (per D-125 explicitly) NO FATAL EXIT PATH for any of its findings. See "THE VERDICT-WIRING"
below — this is the part of the house style that must NOT be copied from the ratchet.

═══════════════════════════════════════════════════════════════════════════════════════════════
WHAT DEFECT THIS EXISTS FOR
═══════════════════════════════════════════════════════════════════════════════════════════════

D-123 found that Wave 2's entrypoint-guard repair can leave "guarded" meaning less than it
appears: two files (`audit/replay.ts`, `trace/trace_smoke.ts`) call `process.exit(1)` at MODULE
SCOPE, outside the guarded `main()` entirely — importing them with one env var unset still kills
the importing process, and the guard never gets a chance to stop it. D-125 (PARĪKṢAKA's V-82)
measured that pattern across all 53 of Wave 2's tier-1 files and found it in 4, found 6 files
that load a `.env.local` / `.env.rag` file into `process.env` at module scope (PRESUMED
credential-touching — D-125 section 5, conservative, unverified, and deliberately so: verifying
it would require reading a credential file, which is P4 and forbidden), and found 5 files that
construct a `pg.Pool` at module scope (D-80 section 5: TIER-2-EQUIVALENT, not tier-1 — `new
Pool()` opens no socket by itself).

D-125 authorised turning that one-off audit into a standing, re-runnable detector — "it converts
an unknown into a number I can rule on" — and D-126 item 2 folded in D-80 section 5's own
recording obligation, which had been ISSUED but never DISCHARGED: "ENV MUTATION IS ONE MORE
COLUMN IN THAT TABLE, and the expensive pass that would have paid for it has just been made."
This script is that table, built once, re-runnable, and itemised rather than a one-off count.

═══════════════════════════════════════════════════════════════════════════════════════════════
THE POPULATION — Wave 2's 53, derived fresh, never hand-typed
═══════════════════════════════════════════════════════════════════════════════════════════════

`00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json` → `records[].tier == 1` is 58 files
(`counts.tier_1`). Wave 1 already repaired 5 of those 58 (M0-T81/M0-T65's certified batch); this
script's population is the remaining 53 — `tier==1` MINUS the 5 named `WAVE_1_FILES` below,
computed at runtime from the live baseline file, never hand-typed as a 53-item list. See
`derive_wave2_population()`.

═══════════════════════════════════════════════════════════════════════════════════════════════
THE THREE PROPERTIES — each its own finding class, none blended into the others
═══════════════════════════════════════════════════════════════════════════════════════════════

  (a) MODULE-SCOPE CRASH-ON-IMPORT — `crash_process_exit` and `crash_throw`. A `process.exit(...)`
      call, or a bare `throw` statement, whose enclosing block is executable at module load (not
      inside any function/class/arrow/method body — the SAME opaqueness test
      `check_entrypoint_guard_ratchet.py`'s `analyse()` uses for `main()`, reused here for a
      different call class rather than re-derived, per CLAUDE.md §N.7's "one rule id, one
      implementation" spirit). A `throw` INSIDE a `try { }` is excluded — its own `catch` may
      handle it locally, so it is not unconditionally uncaught (see the docstring's "WHAT THIS
      DOES NOT COVER" for the honest limit of that exclusion). KNOWN POSITIVE (D-123/D-125,
      independently re-measured by M0-T82/V-82): 4/53 — `audit/replay.ts`, `audit/smoke.ts`,
      `bootstrap/bootstrap_multi_school_tajaka.ts`, `trace/trace_smoke.ts`.

  (b) MODULE-SCOPE CREDENTIAL/ENV-FILE LOAD — `env_credential`. A module-scope call to
      `loadEnv(...)` / `loadEnvFile(...)` / `dotenv.config(...)` (or an equivalent call name)
      whose argument names a file literally called `.env.local` or `.env.rag`. PRESUMED
      credential-touching per D-125 section 5 — this detector NEVER reads the contents of any
      such file (P4, forbidden); the presumption IS the ruling, and this script implements it,
      it does not test it. KNOWN POSITIVE: 6/53 — `audit/replay.ts`, `audit/smoke.ts`,
      `cutover/stage1_smoke.ts`, `governance/seed_tool_registry.ts`, `retrieval/probe_11c_b.ts`,
      `trace/trace_smoke.ts`.

  (c) MODULE-SCOPE `new Pool(...)` CONSTRUCTION — `pool_construction`. Graded TIER-2-EQUIVALENT
      per D-80 section 5, NOT tier-1: constructing a `pg.Pool` opens no socket by itself and is
      not credential-touching on its own. KNOWN POSITIVE: 5/53 — `audit/replay.ts`,
      `audit/smoke.ts`, `backfill_conversation_embeddings.ts`, `governance/seed_tool_registry.ts`,
      `trace/trace_smoke.ts`.

═══════════════════════════════════════════════════════════════════════════════════════════════
THE VERDICT-WIRING (D-109 §4's requirement, applied here per D-125 section 3)
═══════════════════════════════════════════════════════════════════════════════════════════════

EVERY FINDING THIS SCRIPT PRODUCES IS OBSERVATIONAL, NOT FATAL, AT BIRTH. There is no allowlist,
no floor, no `--strict`, and NO CODE PATH IN THIS FILE THAT RETURNS A NON-ZERO EXIT CODE FOR A
FINDING. The only reasons this script exits 1 are internal/scanner failures that make its own
output untrustworthy: the baseline (`M0-T64-triage.json`) could not be read, the derived
population is not exactly 53 (a population-derivation bug, not a finding about any file), a
scanned file could not be parsed (unbalanced brace stack — the SAME §N.8 discipline
`check_entrypoint_guard_ratchet.py` uses: a file the scanner cannot read must never look like a
file with nothing wrong), or `--self-test` itself fails.

WHY OBSERVATIONAL, IN D-125's OWN WORDS (section 3, quoted because the reasoning is load-bearing,
not incidental): "not because the residual is acceptable, but because REPAIRING these files is
new work outside the [currently-authorised] buckets, so a fatal gate would be red with NO
AUTHORISED PATH TO CLEAR IT. That is the permanently-red hazard arriving from unauthorisedness
rather than unfixability, and it is still H3 by attrition. IT BECOMES FATAL WHEN THE REPAIR IS
AUTHORISED; the residual is carried ITEMISED." This script's `--json` output itemises by
filename for exactly that reason — never a bare count — so that the moment a repair task IS
authorised, the residual it must clear is already named, not re-discovered.

This is also D-126 item 2's discharge point: the env-mutation column D-80 section 5 ordered
("Wave 2 RECORDS IT PER FILE") is property (b) below, computed in the SAME pass as (a) and (c)
rather than a separate task, per D-126's ruling that this is "an existing authorised obligation
being discharged late," not new scope.

Exit codes: 0 = scan completed (regardless of what it found — findings are observational, per
D-125, and never gate this script's own exit code); 1 = an internal failure that makes the
report untrustworthy (baseline unreadable, population count ≠ 53, a file did not parse,
`--self-test` failed).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

BASELINE_PATH = REPO_ROOT / "00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json"
FIXTURE_DIR = HERE / "wave2_module_scope_hazard_fixtures"

#: Wave 1's five files (M0-T81 batches, certified by PARĪKṢAKA per D-80's three preconditions).
#: Subtracted from the tier-1 58 to derive Wave 2's 53. Named here, exactly as the M0-T85 task
#: JSON names them, so the population is auditable against the task's own text — but the
#: SUBTRACTION happens against the LIVE baseline read at runtime, not a hand-typed 53-item list.
WAVE_1_FILES = frozenset(
    {
        "platform/scripts/_archived/seed-abhisek.ts",
        "platform/scripts/dedupe_charts.ts",
        "platform/scripts/dev/mint_session_cookie.ts",
        "platform/scripts/probe/ask.ts",
        "platform/scripts/set-password.ts",
    }
)

EXPECTED_WAVE2_COUNT = 53

#: KNOWN-POSITIVE SETS — D-123 / D-125 / M0-T82's independently-corroborated measurements,
#: reproduced here so `--json` can report MATCH/MISMATCH on every run, not only once in a
#: session transcript. A mismatch is reported loudly (stderr + a JSON field) but is NOT fatal by
#: itself — see THE VERDICT-WIRING above — because a mismatch could mean either "this detector
#: has a bug" or "the tree has changed since D-125" (e.g. a file was deleted or repaired since);
#: this script cannot tell those apart on its own, so it reports the discrepancy itemised and
#: lets a human/ADHIKĀRIN judge which. Per D-125 section 7 (STANDING): when a measurement is
#: revised, the discarded value and the reason are reported with it — this constant IS that
#: discipline, kept permanently rather than only in a transcript.
KNOWN_POSITIVE_CRASH = frozenset(
    {
        "platform/scripts/audit/replay.ts",
        "platform/scripts/audit/smoke.ts",
        "platform/scripts/bootstrap/bootstrap_multi_school_tajaka.ts",
        "platform/scripts/trace/trace_smoke.ts",
    }
)
KNOWN_POSITIVE_ENV_CREDENTIAL = frozenset(
    {
        "platform/scripts/audit/replay.ts",
        "platform/scripts/audit/smoke.ts",
        "platform/scripts/cutover/stage1_smoke.ts",
        "platform/scripts/governance/seed_tool_registry.ts",
        "platform/scripts/retrieval/probe_11c_b.ts",
        "platform/scripts/trace/trace_smoke.ts",
    }
)
KNOWN_POSITIVE_POOL = frozenset(
    {
        "platform/scripts/audit/replay.ts",
        "platform/scripts/audit/smoke.ts",
        "platform/scripts/backfill_conversation_embeddings.ts",
        "platform/scripts/governance/seed_tool_registry.ts",
        "platform/scripts/trace/trace_smoke.ts",
    }
)


# ═══════════════════════════════════════════════════════════════════════════════════════════
# BLANKING — comment / string / regex-literal bodies replaced by spaces, offsets preserved.
#
# IMPORTED from `check_entrypoint_guard_ratchet.py` (same directory), not copied. M0-T85's
# original hand-copy had already diverged textually from its source at birth (6688 vs 6766
# chars — stripped comments, including the note on why `${...}` interpolations are deliberately
# not re-entered), with no live behavioral bug found — but a parser copy sitting underneath two
# guards, one of them blocking, is exactly the risk ADHIKĀRIN D-127 closed: "when you find
# yourself preserving someone else's implementation because re-deriving it would be risky, that
# is the signal to IMPORT it, not to copy it" (CLAUDE.md §N.7 / D-94 §8's "one rule id, one
# implementation"). Both files are stdlib-only Python in this same directory, per the same
# same-directory sibling-import convention `drift_detector.py` / `schema_validator.py` /
# `check_asset_source_parity.py` already use in this folder.
# ═══════════════════════════════════════════════════════════════════════════════════════════

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from check_entrypoint_guard_ratchet import blank_noncode  # noqa: E402,PLC0415


#: Block headers whose body does NOT execute at module load — reused verbatim from
#: `check_entrypoint_guard_ratchet.py` (same opaqueness test, applied to a different call class).
OPAQUE_HEADER = re.compile(
    r"\bfunction\b"
    r"|=>\s*$"
    r"|\bclass\b"
    r"|^(?!(?:if|for|while|switch|catch|with|else|do|try)\b)[\w$]+\s*\([^{]*\)$",
)

#: A `try {` header specifically — used ONLY to exclude a `throw` that a local `catch` may
#: handle. Does NOT exclude `process.exit`/`new Pool` occurrences inside a try (those still run
#: unconditionally; a catch cannot stop a process.exit that already fired, and a Pool
#: construction that throws would itself be a `crash_throw` finding, not a reason to hide it).
TRY_HEADER = re.compile(r"^try\b")

#: THE SAME FIVE GUARD IDIOMS `check_entrypoint_guard_ratchet.py` enumerates (D-71 part 4),
#: reused here for a DIFFERENT PURPOSE than that script uses them for. There, a guard idiom
#: determines whether `main()` runs on import. Here, it determines whether a hazard call sits
#: inside an `if (isDirectEntrypoint(...)) { ... }`-shaped block (or one of its four siblings) —
#: i.e. code that only runs once the file is CONFIRMED to be the direct entrypoint, not on an
#: ordinary `import`. This is the exact distinction D-123 drew: "the guard gates main(), not
#: module scope" — code genuinely OUTSIDE any guard is the hazard; code correctly INSIDE one is
#: the guard doing its job. Without this, this detector's first draft flagged
#: `pariprashna/verify_captured_turn.ts`'s `process.exit` calls, which sit inside exactly such a
#: guard (`if (isDirectEntrypoint(import.meta.url, process.argv[1])) { main().then(...).catch(...
#: process.exit(2) ...) }`) — a FALSE POSITIVE caught by this script's own `--self-test`
#: (`run_known_positive_self_test`) before any number was reported, the same discipline D-125
#: section 7 made STANDING: a revised measurement reports the discarded value and why. See
#: `executes_on_import()` below for how this and `OPAQUE_HEADER` combine.
GUARD_IDIOMS: Tuple[re.Pattern, ...] = (
    re.compile(r"\bisDirectEntrypoint\s*\("),
    re.compile(r"\bIMPORT_ONLY\b"),
    re.compile(r"process\.argv\s*\[\s*1\s*\]"),
    re.compile(r"\bis(?:Entry[Pp]oint|Main|DirectRun|CliRun)\b(?!\w)"),
    re.compile(
        r"require\.main\s*===\s*module"
        r"|module\s*===\s*require\.main"
        r"|import\.meta\.main\b"
        r"|import\.meta\.url\s*===",
    ),
)

#: Text immediately before a candidate call token that means "this is a declaration, not a
#: call" — e.g. `function loadEnv(...)`. Without this, this detector's first draft flagged the
#: DEFINITION of the `loadEnv`/`loadEnvFile` helper functions themselves (every one of the six
#: known-positive files defines one) as if it were a call — also caught by `--self-test` before
#: being reported. Mirrors `check_entrypoint_guard_ratchet.py`'s `DECLARATION_PREFIX`.
FUNCTION_DECL_PREFIX = re.compile(r"\bfunction\s*$")

PROCESS_EXIT_RE = re.compile(r"\bprocess\.exit\s*\(")
NEW_POOL_RE = re.compile(r"\bnew\s+Pool\s*\(")
ENV_LOAD_CALL_RE = re.compile(r"\b(?:loadEnv|loadEnvFile)\s*\(|\bdotenv\.config\s*\(")
#: A bare `throw` keyword starting a statement (the text between the previous statement
#: boundary and this `throw` is empty once stripped) — distinguishes a genuine throw statement
#: from `throw` appearing as part of a larger token (which word-boundary anchoring already
#: prevents) or being examined mid-expression (not possible for a keyword, kept for clarity).
THROW_RE = re.compile(r"\bthrow\b")

#: How far past an env-load call's opening paren to search the ORIGINAL (unblanked) source for
#: a `.env.local` / `.env.rag` literal. Generous relative to every real call in the current
#: population (all single-line); documented as a real, stated limit rather than an unstated one
#: — see the module docstring's "WHAT THIS DOES NOT COVER".
ENV_ARG_WINDOW = 400
CREDENTIAL_FILE_RE = re.compile(r"\.env\.local|\.env\.rag")


@dataclass
class Hit:
    line: int
    kind: str  # "crash_process_exit" | "crash_throw" | "env_credential" | "pool_construction"
    detail: str
    context: str


@dataclass
class FileScan:
    path: str
    hits: List[Hit] = field(default_factory=list)
    analysis_error: bool = False

    def kinds(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for h in self.hits:
            counts[h.kind] = counts.get(h.kind, 0) + 1
        return counts

    @property
    def crash(self) -> bool:
        return any(h.kind in ("crash_process_exit", "crash_throw") for h in self.hits)

    @property
    def env_credential(self) -> bool:
        return any(h.kind == "env_credential" for h in self.hits)

    @property
    def pool_construction(self) -> bool:
        return any(h.kind == "pool_construction" for h in self.hits)


def analyse_module_scope(src: str) -> Tuple[List[Hit], bool]:
    """Walk `src`, brace-aware and never line-anchored (same discipline as
    `check_entrypoint_guard_ratchet.py`'s `analyse()`), and report every MODULE-SCOPE occurrence
    of the three tracked properties. Returns `(hits, analysis_error)` — `analysis_error=True`
    means the brace stack did not return to empty and every hit found is UNTRUSTED (the caller
    must treat this as "could not scan", never as "scanned clean" — §N.8)."""
    code = blank_noncode(src)
    n = len(code)

    stack: List[str] = []
    stmt_start = 0
    hits: List[Hit] = []

    line_starts = [0] + [m.end() for m in re.finditer(r"\n", code)]

    def line_of(pos: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def executes_on_import() -> bool:
        """True iff code at this point in the stack runs unconditionally on a plain `import` of
        this file — i.e. it is neither inside a function/class/arrow/method body (OPAQUE_HEADER)
        NOR inside a block gated by one of the five entrypoint-guard idioms (GUARD_IDIOMS). Both
        conditions were needed: the first false-positive this detector produced was a function
        DECLARATION site, the second was code correctly gated behind
        `isDirectEntrypoint(...)` — see the constants' own comments above."""
        if any(OPAQUE_HEADER.search(h) for h in stack):
            return False
        if any(any(p.search(h) for p in GUARD_IDIOMS) for h in stack):
            return False
        return True

    def in_try() -> bool:
        return any(TRY_HEADER.search(h) for h in stack)

    def context_of(pos: int) -> str:
        return re.sub(r"\s+", " ", (" ".join(stack) + " ~ " + code[stmt_start:pos])).strip()[-160:]

    i = 0
    while i < n:
        c = code[i]
        if c == "{":
            header = code[stmt_start:i].strip()
            stack.append(header)
            stmt_start = i + 1
            i += 1
            continue
        if c == "}":
            if stack:
                stack.pop()
            stmt_start = i + 1
            i += 1
            continue
        if c == ";":
            stmt_start = i + 1
            i += 1
            continue

        if c == "p":
            m = PROCESS_EXIT_RE.match(code, i)
            if m:
                if executes_on_import():
                    hits.append(
                        Hit(line_of(i), "crash_process_exit", "process.exit(...) at module scope", context_of(i))
                    )
                i = m.end()
                continue
        elif c == "t":
            m = THROW_RE.match(code, i)
            if m:
                prefix = code[stmt_start:i].strip()
                if not prefix and executes_on_import() and not in_try():
                    hits.append(
                        Hit(line_of(i), "crash_throw", "bare throw at module scope, outside try", context_of(i))
                    )
                i = m.end()
                continue
        elif c == "n":
            m = NEW_POOL_RE.match(code, i)
            if m:
                if executes_on_import():
                    hits.append(
                        Hit(line_of(i), "pool_construction", "new Pool(...) at module scope", context_of(i))
                    )
                i = m.end()
                continue
        elif c == "l" or c == "d":
            m = ENV_LOAD_CALL_RE.match(code, i)
            if m:
                if executes_on_import() and not FUNCTION_DECL_PREFIX.search(code[stmt_start:i]):
                    # Search the ORIGINAL (unblanked) source — not `code` — for the credential
                    # filename, since blank_noncode has blanked the string literal itself.
                    window = src[m.end() : m.end() + ENV_ARG_WINDOW]
                    cred = CREDENTIAL_FILE_RE.search(window)
                    if cred:
                        hits.append(
                            Hit(
                                line_of(i),
                                "env_credential",
                                f"module-scope call loads {cred.group(0)!r} into process.env "
                                "(PRESUMED credential-touching, D-125 §5 — contents never read)",
                                context_of(i),
                            )
                        )
                i = m.end()
                continue

        i += 1

    return hits, len(stack) != 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Population derivation — NEVER hand-typed. Read fresh from the M0-T64 baseline every run.
# ═══════════════════════════════════════════════════════════════════════════════════════════


def derive_wave2_population(baseline_path: Path = BASELINE_PATH) -> Optional[List[str]]:
    """Wave 2's 53: `records[].tier == 1` from the M0-T64 triage, minus `WAVE_1_FILES`. Returns
    `None` if the baseline could not be read or parsed — an absent/broken baseline is UNKNOWN,
    never an empty population that would silently report zero files with zero findings."""
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    records = data.get("records")
    if not isinstance(records, list):
        return None
    tier1 = []
    for r in records:
        if not isinstance(r, dict):
            return None
        if r.get("tier") == 1:
            f = r.get("file")
            if not isinstance(f, str):
                return None
            tier1.append(f)
    return sorted(set(tier1) - WAVE_1_FILES)


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════════════════════════════


def scan_population(root: Path, population: Sequence[str]) -> Dict[str, FileScan]:
    results: Dict[str, FileScan] = {}
    for rel in population:
        p = root / rel
        try:
            src = p.read_text(encoding="utf-8")
        except OSError:
            results[rel] = FileScan(path=rel, hits=[], analysis_error=True)
            continue
        hits, broken = analyse_module_scope(src)
        results[rel] = FileScan(path=rel, hits=hits, analysis_error=broken)
    return results


def reconcile(actual: frozenset, known: frozenset, label: str) -> Dict:
    """Compare a freshly-measured set against D-125's known-positive set. Never fatal by
    itself (a real change to the tree since D-125 is a legitimate reason to differ) — reported
    itemised, per D-125 section 7's STANDING rule that a revised measurement carries the
    discarded value and the reason."""
    missing = sorted(known - actual)  # known-positive no longer found
    added = sorted(actual - known)  # newly found, not in the known-positive set
    return {
        "property": label,
        "match": not missing and not added,
        "known_positive_count": len(known),
        "measured_count": len(actual),
        "no_longer_found": missing,
        "newly_found": added,
    }


def build_report(root: Path) -> Tuple[Optional[Dict], int]:
    population = derive_wave2_population()
    if population is None:
        return None, 1
    errors = 0
    pop_note = None
    if len(population) != EXPECTED_WAVE2_COUNT:
        pop_note = (
            f"population derivation returned {len(population)} file(s), expected "
            f"{EXPECTED_WAVE2_COUNT} (tier-1 58 minus Wave 1's 5). This is a DETECTOR BUG or a "
            "baseline/WAVE_1_FILES drift, not a finding about any file — treated as an internal "
            "failure (§N.8)."
        )
        errors += 1

    results = scan_population(root, population)
    unparsed = sorted(rel for rel, r in results.items() if r.analysis_error)
    if unparsed:
        errors += 1

    crash_files = frozenset(rel for rel, r in results.items() if r.crash)
    env_files = frozenset(rel for rel, r in results.items() if r.env_credential)
    pool_files = frozenset(rel for rel, r in results.items() if r.pool_construction)

    per_file = []
    for rel in population:
        r = results.get(rel)
        if r is None:
            continue
        per_file.append(
            {
                "file": rel,
                "analysis_error": r.analysis_error,
                "crash_process_exit": any(h.kind == "crash_process_exit" for h in r.hits),
                "crash_throw": any(h.kind == "crash_throw" for h in r.hits),
                "env_credential": r.env_credential,
                "pool_construction": r.pool_construction,
                "findings": [
                    {"line": h.line, "kind": h.kind, "detail": h.detail, "context": h.context}
                    for h in sorted(r.hits, key=lambda h: h.line)
                ],
            }
        )

    report = {
        "schema_version": "1.0",
        "task": "M0-T85",
        "authority": [
            "D-125 (authorises this detector as a MEASUREMENT, observational at birth)",
            "D-126 item 2 (discharges D-80 section 5's env-mutation recording obligation)",
            "D-123 (module-scope process.exit is tier-1, not closed by the entrypoint guard)",
            "D-80 section 5 (module-scope new Pool() is tier-2-equivalent, not tier-1)",
            "D-109 section 4 (verdict-wiring: every finding declares fatal-or-observational)",
            "CLAUDE.md §N.8 (a signal without a real detector is null, not green)",
        ],
        "verdict_wiring": {
            "crash_process_exit": "OBSERVATIONAL — see module docstring THE VERDICT-WIRING",
            "crash_throw": "OBSERVATIONAL — see module docstring THE VERDICT-WIRING",
            "env_credential": "OBSERVATIONAL — see module docstring THE VERDICT-WIRING",
            "pool_construction": "OBSERVATIONAL — see module docstring THE VERDICT-WIRING",
            "fatal_conditions": [
                "baseline (M0-T64-triage.json) unreadable",
                f"derived population ≠ {EXPECTED_WAVE2_COUNT}",
                "a scanned file did not parse (unbalanced brace stack)",
                "--self-test failed",
            ],
        },
        "population": {
            "source": "00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json :: records[].tier==1",
            "wave_1_files_subtracted": sorted(WAVE_1_FILES),
            "expected_count": EXPECTED_WAVE2_COUNT,
            "measured_count": len(population),
            "note": pop_note,
        },
        "counts": {
            "crash": len(crash_files),
            "env_credential": len(env_files),
            "pool_construction": len(pool_files),
            "population": len(population),
        },
        "itemised": {
            "crash": sorted(crash_files),
            "env_credential": sorted(env_files),
            "pool_construction": sorted(pool_files),
        },
        "unparsed_files": unparsed,
        "known_positive_reconciliation": [
            reconcile(crash_files, KNOWN_POSITIVE_CRASH, "crash"),
            reconcile(env_files, KNOWN_POSITIVE_ENV_CREDENTIAL, "env_credential"),
            reconcile(pool_files, KNOWN_POSITIVE_POOL, "pool_construction"),
        ],
        "per_file": per_file,
    }
    return report, (1 if errors else 0)


def print_human(report: Dict) -> None:
    print("check_wave2_module_scope_hazards: Wave-2 module-scope hazard survey (M0-T85)")
    print(f"  population: {report['counts']['population']} file(s)")
    for c in report["known_positive_reconciliation"]:
        flag = "MATCH" if c["match"] else "MISMATCH"
        print(
            f"  {c['property']}: {c['measured_count']}/{report['counts']['population']} "
            f"(known-positive {c['known_positive_count']}) — {flag}"
        )
        if not c["match"]:
            if c["no_longer_found"]:
                print(f"    no longer found: {c['no_longer_found']}")
            if c["newly_found"]:
                print(f"    newly found: {c['newly_found']}")
    if report["unparsed_files"]:
        print(f"  UNPARSED (untrusted result): {report['unparsed_files']}")
    print("  all findings are OBSERVATIONAL, not fatal — see module docstring THE VERDICT-WIRING")
    print("  itemised residual:")
    for prop in ("crash", "env_credential", "pool_construction"):
        print(f"    {prop}:")
        for f in report["itemised"][prop]:
            print(f"      - {f}")


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Self-test
# ═══════════════════════════════════════════════════════════════════════════════════════════


def run_fixture_self_test() -> List[str]:
    """Hermetic — no repo scan, no git, no network. Proves each of the three properties in BOTH
    directions: a fixture that MUST trigger the finding, and one that MUST NOT, per file. This is
    the D-71-part-7-style requirement the M0-T85 task asks this script to inherit from
    `check_entrypoint_guard_ratchet.py`."""
    failures: List[str] = []
    pass_dir, fail_dir = FIXTURE_DIR / "pass", FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        return [f"fixtures missing under {FIXTURE_DIR}"]

    expect_fail = {
        "module_scope_crash.ts": {"crash_process_exit"},
        "module_scope_throw.ts": {"crash_throw"},
        "module_scope_env_credential.ts": {"env_credential"},
        "module_scope_pool.ts": {"pool_construction"},
    }
    for name, want_kinds in expect_fail.items():
        p = fail_dir / name
        if not p.exists():
            failures.append(f"FAIL-fixture '{name}' is missing")
            continue
        hits, broken = analyse_module_scope(p.read_text(encoding="utf-8"))
        if broken:
            failures.append(f"FAIL-fixture '{name}' did not parse (unbalanced brace stack)")
        got_kinds = {h.kind for h in hits}
        if not want_kinds & got_kinds:
            failures.append(
                f"FAIL-fixture '{name}' produced NO finding of kind {want_kinds} "
                f"(false negative) — got {sorted(got_kinds)}"
            )

    expect_pass = [
        "function_scoped_crash.ts",
        "try_caught_throw.ts",
        "function_scoped_env_credential.ts",
        "function_scoped_pool.ts",
    ]
    for name in expect_pass:
        p = pass_dir / name
        if not p.exists():
            failures.append(f"PASS-fixture '{name}' is missing")
            continue
        hits, broken = analyse_module_scope(p.read_text(encoding="utf-8"))
        if broken:
            failures.append(f"PASS-fixture '{name}' did not parse (unbalanced brace stack)")
        if hits:
            failures.append(
                f"PASS-fixture '{name}' produced {len(hits)} finding(s) (false positive): "
                f"{[(h.kind, h.line) for h in hits]}"
            )

    return failures


def run_population_self_test() -> List[str]:
    """NOT hermetic — reads the live `M0-T64-triage.json` baseline (a governance artifact, not
    one of the 53 scanned scripts) and asserts the population derivation is exactly 53 and
    disjoint from `WAVE_1_FILES`. This does not touch, edit or run any of the 53 real files."""
    failures: List[str] = []
    population = derive_wave2_population()
    if population is None:
        failures.append(f"could not read/parse baseline at {BASELINE_PATH}")
        return failures
    if len(population) != EXPECTED_WAVE2_COUNT:
        failures.append(
            f"derived population is {len(population)}, expected {EXPECTED_WAVE2_COUNT}"
        )
    overlap = WAVE_1_FILES & set(population)
    if overlap:
        failures.append(f"Wave 1 file(s) leaked into the Wave 2 population: {sorted(overlap)}")
    return failures


def run_known_positive_self_test() -> List[str]:
    """NOT hermetic — scans the LIVE Wave-2 population (read-only) and asserts the detector
    reproduces D-125's known-positive sets exactly, per the M0-T85 task's own instruction:
    'If it does not reproduce all three sets exactly, your method has a gap — find and fix it
    before reporting final numbers.' Kept as a standing regression check rather than a one-off
    session step, so a future drift is caught the next time this runs, not only remembered."""
    failures: List[str] = []
    report, _ = build_report(REPO_ROOT)
    if report is None:
        failures.append("build_report could not run against the live tree")
        return failures
    for c in report["known_positive_reconciliation"]:
        if not c["match"]:
            failures.append(
                f"known-positive mismatch for '{c['property']}': "
                f"no_longer_found={c['no_longer_found']} newly_found={c['newly_found']}"
            )
    return failures


def run_self_test() -> int:
    failures: List[str] = []
    failures.extend(run_fixture_self_test())
    failures.extend(run_population_self_test())
    failures.extend(run_known_positive_self_test())

    if failures:
        print("check_wave2_module_scope_hazards: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        "check_wave2_module_scope_hazards: SELF-TEST PASS "
        "(4 fail-fixtures caught, 4 pass-fixtures silent, population==53 verified, "
        "known-positive sets reproduced exactly for crash/env_credential/pool_construction)."
    )
    return 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════════════


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--self-test", action="store_true", help="Run bundled fixtures (hermetic) plus a live population/known-positive check.")
    ap.add_argument("--root", default=str(REPO_ROOT), help="Repo root to scan.")
    ap.add_argument("--json", action="store_true", help="Emit a machine-readable report.")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    root = Path(args.root).resolve()
    report, rc = build_report(root)
    if report is None:
        print(
            f"check_wave2_module_scope_hazards: could not read baseline at {BASELINE_PATH}",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)

    if report["population"]["note"]:
        print(f"check_wave2_module_scope_hazards: {report['population']['note']}", file=sys.stderr)
    if report["unparsed_files"]:
        print(
            f"check_wave2_module_scope_hazards: {len(report['unparsed_files'])} file(s) did not "
            "parse — their result is UNKNOWN, not clean (§N.8): "
            f"{report['unparsed_files']}",
            file=sys.stderr,
        )
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
