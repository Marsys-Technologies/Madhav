#!/usr/bin/env python3
"""check_entrypoint_guard_ratchet.py — a NEW unguarded top-level `main()` fails the build.

Nirmāṇa WORK_QUEUE **M0-T66**, ruling **D-67 part 3** (finding F-5) with the mandatory shape of
**D-67 part 4** and the mandatory detector shape of **D-71 part 7**.

Sibling to `check_earned_signal.py` and `check_fact_category_pinning.py`, and deliberately built
to the same shape: bundled PASS/FAIL fixtures + `--self-test`, an allowlist-aware repo scan,
`--strict`, `--json`, stdlib only, no DB, no network.

═══════════════════════════════════════════════════════════════════════════════════════════════
WHAT DEFECT THIS EXISTS FOR
═══════════════════════════════════════════════════════════════════════════════════════════════

A `.ts` file under `platform/scripts` that calls `main()` at module top level with no entrypoint
guard **runs its whole program when anything imports it**. M0-T60 found the live instance: an
`import` of `scripts/migrate.ts`'s pure helpers applied every pending migration; nothing was
applied to production only because that particular shell had no `DATABASE_URL`. M0-T64 triaged
the population by blast radius on import — 58 of 76 files acquire a credential, open a
connection, or call `process.exit` **on import**.

Ruling D-67 part 3: *"a class we just closed with no detector against reintroduction will
reopen — F-5 is not hypothetical, it is the default."*

═══════════════════════════════════════════════════════════════════════════════════════════════
WHY IT IS A RATCHET AND NOT A GATE  (D-67 part 4 — a CONDITION, not a suggestion)
═══════════════════════════════════════════════════════════════════════════════════════════════

    "A guard that fires on 76 files is PERMANENTLY RED FROM ITS FIRST RUN, and D-39 part 2
     establishes that a permanently-red gate trains every agent who sees it to ignore it, which
     is worse than no gate because it occupies the place where a real one would go. So: AN
     ITEMISED ALLOWLIST OF EXACTLY TODAY'S POPULATION, GENERATED FROM THE MEASUREMENT AND NEVER
     HAND-TYPED, WITH ITS COUNT RECORDED SO SHRINKAGE IS VISIBLE. PAY-DOWN ONLY: a file leaves
     the list when repaired; NOTHING IS EVER ADDED. A new unguarded top-level main() fails the
     build."

Three mechanisms implement that, and each has a detector rather than a promise:

  1. **GENERATED, NEVER HAND-TYPED.** `--regenerate` writes `entrypoint_ratchet_allowlist.json`
     from THIS script's own scan of the tree. There is no code path that appends a name.
  2. **NOTHING NEW IS EVER ADDED — checked on EVERY run, not only at regeneration.** The
     allowlist must be a SUBSET of M0-T64's settled 76-file baseline
     (`00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json` → `ratchet_allowlist.files`, proven
     identical against ADHIKĀRIN's independent derivation, ruling D-71 part 3). A hand-added
     entry — even one naming a genuinely unguarded file — fails the run. The ratchet cannot be
     loosened by editing the list it gates on.
  3. **SHRINKAGE IS VISIBLE.** The allowlist records `baseline_count`, its own `count`, and the
     itemised `paid_down` set (baseline − current). `--json` reports all three.
  4. **THE PAWL — THE ALLOWLIST MAY ONLY SHRINK (ruling D-87, from PARĪKṢAKA's finding F-T).**
     Mechanism 2 is MEMBERSHIP IN A STATIC BASELINE, and D-87 names the gap exactly: it asks
     *"is every unguarded file one of the original 76?"* and **never asks "has the allowlist
     GROWN since last time?"** — so a REPAIRED file stays a permissible member of the baseline
     forever and can be re-added, then stripped of its guard, with nothing objecting. Every run
     therefore ALSO asserts that the allowlist is a subset of **its own previous committed
     value**, read from git (`HEAD` when the working tree carries an uncommitted edit, `HEAD^`
     on a clean checkout, `HEAD` for `--regenerate`). This is what makes the ratchet a ratchet;
     without it the ratchet is a size comparison. It looks at nothing but the DELTA, so it is
     green today with the whole 71-file residual present — see the PAWL section below.

Stale entries — allowlisted files that are now clean, or that no longer exist — are REPORTED
loudly on every run and fail only under `--strict`. They are the good direction; making them
blocking would turn a repair into a red build (D-39 part 2 again), and the honest place to
resolve them is a `--regenerate` commit.

═══════════════════════════════════════════════════════════════════════════════════════════════
THE DETECTOR  (D-71 part 7 — also a REQUIREMENT, not a suggestion)
═══════════════════════════════════════════════════════════════════════════════════════════════

    "(a) leading-whitespace-tolerant over the full caller set, (b) MINUS an explicit guard
     determination that recognises all five idioms INCLUDING the same-line placement, (c)
     restricted to code paths, excluding .md and fenced blocks, and (d) proven with a paired
     fixture: an INDENTED unguarded main() must go red, and a same-line-guarded main() must stay
     green. A ratchet that cannot go red on an indented reintroduction is a ratchet that admits
     exactly what it was built to catch, silently and permanently."

(a) **NOT LINE-ANCHORED AT ALL.** Column 0 is what made 76 look like the whole population. This
    detector is brace-aware: it finds every `main(` call token, computes its enclosing block
    stack, and asks whether the enclosing stack is *executable at module load*. Indentation is
    not consulted anywhere. A call inside a function body — at any indentation — is not a
    top-level executor and is not reported.

(b) **FIVE GUARD IDIOMS**, exactly the five ADHIKĀRIN enumerated in D-71 part 4, each with its
    own named rule so the report says WHICH one matched and `--self-test` asserts all five are
    live:

        isDirectEntrypoint  ·  IMPORT_ONLY  ·  argv-regex `.test()` / `.endsWith()`
        isEntrypoint / isMain boolean  ·  require.main === module / import.meta.main

    Guardedness is decided over the *guard context* — every enclosing block header plus the
    same-statement prefix — so a SAME-LINE guard (`if (require.main === module) void main()`,
    three of which exist in this tree and appear in NEITHER the 86 NOR the 76) is recognised.

    The RETIRED `process.env.NODE_ENV !== 'test'` sentinel is deliberately **not** a guard. It
    asks the wrong question (ruling D-9 / M0-T60) and a fixture pins that it still fails.

(c) **CODE PATHS ONLY.** `.ts` / `.mts` / `.cts` under the scan roots; no `.md`, no
    `00_ARCHITECTURE/**`, no `99_ARCHIVE/**`. Within a file, `//` and `/* */` comment bodies AND
    string / template-literal bodies are blanked to spaces before anything is matched, so a
    fenced example, a documented form, or a `main()` inside a log message cannot produce a hit.
    This is ADHIKĀRIN's D-72 caution — *a grep for a defective form cannot tell code that has
    the defect from prose that documents it* — and its false-positive rate RISES as files get
    fixed, because the prose population grows while the code population shrinks. The 14th
    guard-bearing file found during D-71's own reconciliation was `A3_env_matrix.md`:
    documentation, defeating both a pattern filter and a `.ts:` path filter.

(d) Paired fixtures live in `entrypoint_ratchet_fixtures/{pass,fail}` and are run by
    `--self-test`. Both directions D-71 names are there by name:
    `fail/indented_unguarded.ts` and `pass/guarded_same_line_require_main.ts`.

═══════════════════════════════════════════════════════════════════════════════════════════════
WHAT THIS GUARD DOES **NOT** COVER — stated, because an unstated limit reads as coverage
═══════════════════════════════════════════════════════════════════════════════════════════════

1. **SCOPE IS `platform/scripts` ONLY** (the default root; `--roots` overrides). That is where
   M0-T64 measured the population and where the hazard was found. A new unguarded top-level
   `main()` under `platform/src`, `platform-mcp/`, or anywhere else is NOT caught by the default
   invocation. This is a real hole and it is deliberate rather than accidental: widening the
   root without a measured baseline for it would produce exactly the permanently-red gate D-67
   part 4 forbids.
2. **IT IS NOT A TYPESCRIPT PARSER.** Blanking is a scanner, not a lexer with full escape/regex
   -literal semantics. A `main()` inside a regex literal, or a brace inside one, could in
   principle mislead the brace stack. No such construct exists in the scanned tree today (the
   scan reproduces the settled 76-file baseline exactly), but a sufficiently exotic file could
   defeat it in either direction.
3. **IT SAYS NOTHING ABOUT MODULE-SCOPE EFFECTS THAT ARE NOT `main()`.** M0-T65's finding F-1 is
   that `dedupe_charts.ts` and `_archived/seed-abhisek.ts` still run `dotenv.config(...)` and
   construct a `Pool` at module scope AFTER their repair. Those are real import side effects and
   this guard is blind to all of them. "Guarded" here means exactly "its `main()` does not run on
   import", and nothing more.
4. **IT DOES NOT PROVE A GUARD FIRES AT RUNTIME.** It is a source-text detector. M0-T65 was
   explicit that structural presence is strictly weaker than execution, and that limit is
   inherited here unchanged.
5. **IT DOES NOT GRADE BLAST RADIUS.** Tier 1 / 2 / 3 live in M0-T64's triage; this guard treats
   every unguarded file identically.

Exit codes: 0 = pass · 1 = a NEW (non-allowlisted) violation, an allowlist that GREW
(either beyond the settled baseline or beyond its own previous committed value), a file the
scanner could not parse, a previous committed value that could not be READ, or `--strict`
with any residual.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

ALLOWLIST_PATH = HERE / "entrypoint_ratchet_allowlist.json"
FIXTURE_DIR = HERE / "entrypoint_ratchet_fixtures"
BASELINE_PATH = REPO_ROOT / "00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json"

DEFAULT_ROOTS = ["platform/scripts"]
#: The GATED population's file suffixes. Exactly `.ts`, because M0-T64's population command ends
#: `| grep '\.ts$'` and ruling D-71 part 5 settled THAT list as the ratchet baseline. Widening
#: this without widening the baseline would make the guard red on files it may not allowlist.
CODE_SUFFIXES = (".ts",)
#: Scanned and REPORTED, never gated — see `out_of_scope_suffix_observations` and finding F-P.
EXTENDED_SUFFIXES = (".mts", ".cts")

#: Directories never scanned. The guard's own fixtures are excluded BY NAME and deliberately:
#: they contain unguarded top-level `main()` calls on purpose, and a fixture that the guard
#: reported would make `--self-test` and the repo scan contradict each other.
EXCLUDED_DIR_NAMES = frozenset({"node_modules", ".git", "out", "dist", ".next"})
EXCLUDED_PATH_FRAGMENTS = ("governance/entrypoint_ratchet_fixtures/",)


# ═══════════════════════════════════════════════════════════════════════════════════════════
# (c) CODE-ONLY: blank comments and string bodies, preserving offsets and newlines
# ═══════════════════════════════════════════════════════════════════════════════════════════


#: A `/` starts a REGEX LITERAL rather than a division when the previous significant character
#: is one of these (or there is none). Getting this wrong is not cosmetic: `replace(/^["\']|["\']$/g, '')`
#: — a real line in `scripts/audit/replay.ts` — contains four quote characters, and a scanner
#: that treats them as string delimiters desynchronises and blanks the REST OF THE FILE. That is
#: exactly what the first draft of this scanner did, and it silently reported TWELVE files of the
#: settled 76 as clean. A detector whose failure mode is "reports nothing" is the worst possible
#: shape for a ratchet, so the balance check below exists to make that failure loud instead.
_REGEX_PRECEDERS = set("(,=:[!&|?{};+-*%~^<>") | {""}
_REGEX_PRECEDING_WORDS = ("return", "typeof", "case", "in", "of", "delete", "void", "instanceof")


def blank_noncode(src: str) -> str:
    """Return `src` with comment, string and regex-literal bodies replaced by spaces.

    Length and newline positions are preserved EXACTLY, so every offset computed on the result
    is a valid offset into the original and line numbers are reportable without a second pass.

    Delimiters are kept (a blanked string is still `\'\'`), so the brace/paren scanner sees
    well-formed syntax. `${...}` interpolations inside template literals are NOT re-entered —
    their contents are blanked with everything else, which is the conservative direction for a
    detector whose job is to avoid false positives from prose.
    """
    out = list(src)
    i, n = 0, len(src)
    prev = ""  # last significant CODE character emitted

    def preceding_word(pos: int) -> str:
        """The identifier immediately before `pos`, skipping whitespace. `return /re/` and
        `case /re/` are regex positions even though the previous character is a letter."""
        j = pos
        while j > 0 and src[j - 1].isspace():
            j -= 1
        end = j
        while j > 0 and (src[j - 1].isalnum() or src[j - 1] in "_$"):
            j -= 1
        return src[j:end]

    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if src[k] != "\n":
                    out[k] = " "
            i = j
        elif c == "/" and (
            prev in _REGEX_PRECEDERS or preceding_word(i) in _REGEX_PRECEDING_WORDS
        ):
            # Regex literal: scan to the unescaped closing `/`, honouring character classes.
            j = i + 1
            in_class = False
            closed = False
            while j < n and src[j] != "\n":
                ch = src[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                elif ch == "/" and not in_class:
                    closed = True
                    break
                j += 1
            if not closed:
                # Not a regex after all (an unterminated one cannot exist in valid TS) — it was
                # a division. Fall through and treat the `/` as an ordinary operator.
                prev = c
                i += 1
                continue
            for k in range(i + 1, j):
                out[k] = " "
            prev = "/"
            i = j + 1
        elif c in "\'\"`":
            quote = c
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == quote:
                    break
                if quote != "`" and src[j] == "\n":
                    break  # ' and " never span lines in valid TS; fail closed, not runaway
                j += 1
            for k in range(i + 1, min(j, n)):
                if src[k] != "\n":
                    out[k] = " "
            prev = quote
            i = min(j, n) + 1
        else:
            if not c.isspace():
                prev = c
            i += 1
    return "".join(out)


# ═══════════════════════════════════════════════════════════════════════════════════════════
# (b) THE FIVE GUARD IDIOMS — D-71 part 4 enumerated exactly these, and no others exist
# ═══════════════════════════════════════════════════════════════════════════════════════════

GUARD_IDIOMS: Tuple[Tuple[str, re.Pattern], ...] = (
    (
        "isDirectEntrypoint",
        re.compile(r"\bisDirectEntrypoint\s*\("),
    ),
    (
        "IMPORT_ONLY",
        re.compile(r"\bIMPORT_ONLY\b"),
    ),
    (
        "argv-regex",
        # `process.argv[1] && /citation_verify_gate\.(ts|…)$/.test(process.argv[1])`, and the
        # `.endsWith(...)` / `.includes(...)` spellings of the same question.
        re.compile(r"process\.argv\s*\[\s*1\s*\]"),
    ),
    (
        "isEntrypoint/isMain",
        # A precomputed boolean. Word-boundary anchored so `isMainThread` does not match.
        re.compile(r"\bis(?:Entry[Pp]oint|Main|DirectRun|CliRun)\b(?!\w)"),
    ),
    (
        "require.main===module",
        # Including the same-line placement that no line-anchored pattern can see, and the
        # ESM `import.meta.main` / `import.meta.url === ...` spellings of the same test.
        re.compile(
            r"require\.main\s*===\s*module"
            r"|module\s*===\s*require\.main"
            r"|import\.meta\.main\b"
            r"|import\.meta\.url\s*===",
        ),
    ),
)

#: NOT a guard, and pinned by a fixture. `process.env.NODE_ENV !== 'test'` asks whether we are in
#: a test run, not whether this module is the entrypoint — ruling D-9 / M0-T60's F-2. Listed here
#: only so `--self-test` can assert it is still rejected.
RETIRED_NON_GUARD = re.compile(r"process\.env\.NODE_ENV")

#: Block headers whose body does NOT execute at module load. A `main()` inside one of these is a
#: call site, not a top-level executor.
#:
#: Deliberately SHORT. The first draft also listed `catch(`, `then(`, `describe(`, `it(` and
#: `test(` for callback bodies — and `\btest\s*\(` then matched the `.test(process.argv[1])` in
#: an argv-regex GUARD, so the whole guarded block was treated as an opaque callback and its
#: `main()` was never examined at all. A PASS fixture caught it (`guarded_argv_regex.ts`
#: attributed no idiom), which is the entire reason each fixture declares WHICH idiom it expects
#: rather than merely "produced no violation": a detector that skips a construct looks identical
#: to one that approves it, and only the positive assertion tells them apart.
#:
#: Every callback body in practice opens with `=>` or `function`, both of which are covered, so
#: nothing was lost by dropping them.
OPAQUE_HEADER = re.compile(
    r"\bfunction\b"
    r"|=>\s*$"
    r"|\bclass\b"
    # An object/class method shorthand: `run(args) {`. Not a control-flow header.
    r"|^(?!(?:if|for|while|switch|catch|with|else|do|try)\b)[\w$]+\s*\([^{]*\)$",
)

#: A `main` identifier that is a CALL, not a declaration and not a property access.
MAIN_CALL = re.compile(r"(?<![\w.$])main\s*\(")

#: Text immediately before a `main(` that means "this is the declaration".
DECLARATION_PREFIX = re.compile(r"(?:function|const|let|var|class)\s+$")


@dataclass
class Occurrence:
    """One top-level `main()` call site."""

    line: int
    guarded_by: Optional[str]
    context: str


@dataclass
class FileResult:
    path: str  # repo-relative, POSIX
    unguarded: List[Occurrence] = field(default_factory=list)
    guarded: List[Occurrence] = field(default_factory=list)
    #: True when the brace stack did not return to empty — the block structure this file's
    #: analysis rests on was wrong, so "no violation" here means "unknown", never "clean".
    analysis_error: bool = False


def _match_guard(context: str) -> Optional[str]:
    for name, pat in GUARD_IDIOMS:
        if pat.search(context):
            return name
    return None


def analyse(src: str) -> Tuple[List[Occurrence], List[Occurrence], bool]:
    """Return (unguarded, guarded) top-level `main()` occurrences in one source string.

    Brace-aware, never line-anchored. For every `{` we record the *header* — the text since the
    previous statement boundary — and push it. A `main(` occurrence is:

      * IGNORED when any enclosing header is `OPAQUE_HEADER` (it is inside a function/class/
        callback body, so it does not run at module load) or when it is the declaration itself;
      * GUARDED when the concatenation of its enclosing headers and its own same-statement
        prefix matches one of the five idioms;
      * UNGUARDED otherwise.
    """
    code = blank_noncode(src)
    n = len(code)

    stack: List[str] = []          # enclosing block headers, outermost first
    stmt_start = 0                 # offset of the current statement's first character
    unguarded: List[Occurrence] = []
    guarded: List[Occurrence] = []

    # Pre-compute line starts for O(log n) line lookup.
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

    i = 0
    while i < n:
        c = code[i]
        if c == "{":
            header = code[stmt_start:i].strip()
            stack.append(header)
            stmt_start = i + 1
        elif c == "}":
            if stack:
                stack.pop()
            stmt_start = i + 1
        elif c == ";":
            stmt_start = i + 1
        elif c == "m":
            m = MAIN_CALL.match(code, i)
            if m:
                prefix = code[stmt_start:i]
                if DECLARATION_PREFIX.search(prefix):
                    i = m.end()
                    continue
                if any(OPAQUE_HEADER.search(h) for h in stack):
                    i = m.end()
                    continue
                context = " ".join(stack) + " ~ " + prefix.strip()
                idiom = _match_guard(context)
                occ = Occurrence(
                    line=line_of(i),
                    guarded_by=idiom,
                    context=re.sub(r"\s+", " ", context).strip()[-160:],
                )
                (guarded if idiom else unguarded).append(occ)
                i = m.end()
                continue
        i += 1

    # ── THE SCANNER MUST BE ABLE TO SAY IT FAILED ──────────────────────────────────────────
    # If the brace stack does not return to empty, the block structure this analysis rests on
    # was wrong somewhere, and every "no violation found" conclusion drawn from it is worthless.
    # The first draft of `blank_noncode` desynchronised on a regex literal containing quote
    # characters and reported TWELVE of the settled 76 files as clean — silently, because a
    # detector that skips a file and one that approves it produce the same empty list. Callers
    # MUST treat a non-empty stack as an analysis error, never as a clean result (§N.8).
    return unguarded, guarded, len(stack) != 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Repo scan
# ═══════════════════════════════════════════════════════════════════════════════════════════


def iter_code_files(
    root: Path, scan_roots: Sequence[str], suffixes: Sequence[str] = CODE_SUFFIXES
) -> Iterable[Path]:
    for rel in scan_roots:
        base = root / rel
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix not in suffixes:
                continue
            parts = set(p.relative_to(root).parts)
            if parts & EXCLUDED_DIR_NAMES:
                continue
            posix = p.relative_to(root).as_posix()
            if any(frag in posix for frag in EXCLUDED_PATH_FRAGMENTS):
                continue
            yield p


def scan(root: Path, scan_roots: Sequence[str]) -> Dict[str, FileResult]:
    results: Dict[str, FileResult] = {}
    for p in iter_code_files(root, scan_roots):
        try:
            src = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        unguarded, guarded, broken = analyse(src)
        if unguarded or guarded or broken:
            rel = p.relative_to(root).as_posix()
            results[rel] = FileResult(
                path=rel, unguarded=unguarded, guarded=guarded, analysis_error=broken
            )
    return results


# ═══════════════════════════════════════════════════════════════════════════════════════════
# The ratchet
# ═══════════════════════════════════════════════════════════════════════════════════════════


def load_baseline() -> List[str]:
    """M0-T64's settled 76-file baseline. Ruling D-71 part 5 authorised this exact list, after
    ADHIKĀRIN diffed it against an independent derivation and got zero differences."""
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return sorted(data["ratchet_allowlist"]["files"])


def load_allowlist(path: Path) -> Dict:
    if not path.exists():
        return {"files": [], "count": 0, "baseline_count": None}
    return json.loads(path.read_text(encoding="utf-8"))


def regenerate(root: Path, scan_roots: Sequence[str], out: Path) -> int:
    """Write the allowlist FROM THE SCAN. There is no code path here that appends a name."""
    baseline = set(load_baseline())
    results = scan(root, scan_roots)
    measured = sorted(rel for rel, r in results.items() if r.unguarded)

    added = [f for f in measured if f not in baseline]
    if added:
        print(
            "check_entrypoint_guard_ratchet: REFUSING to regenerate — the scan found "
            f"{len(added)} unguarded file(s) that are NOT in M0-T64's settled baseline. "
            "PAY-DOWN ONLY: nothing is ever added to this list (D-67 part 4). Repair them, or "
            "bring the discrepancy to ADHIKĀRIN as a finding:",
            file=sys.stderr,
        )
        for f in added:
            print(f"  + {f}", file=sys.stderr)
        return 1

    # ── ASSERTION (ii), AS A PRECONDITION OF WRITING (ruling D-87) ──────────────────────────
    # Without this, `--regenerate` IS the exploit in one command: strip a repaired file's guard,
    # regenerate, and the scan puts that file straight back on the list. Every name it would add
    # is inside the settled baseline, so the subset check above has nothing to say about it.
    pawl = pawl_check(out, measured, None, mode="regenerate")
    if not pawl.ok:
        if not pawl.determined:
            print(
                "check_entrypoint_guard_ratchet: REFUSING to regenerate — "
                f"{pawl.reason}",
                file=sys.stderr,
            )
            return 1
        print(
            f"check_entrypoint_guard_ratchet: REFUSING to regenerate — the scan would ADD "
            f"{len(pawl.added)} file(s) that the PREVIOUS COMMITTED allowlist "
            f"({pawl.previous_commit}, {pawl.previous_count} entries) does not carry. THE "
            "ALLOWLIST MAY ONLY SHRINK (D-67 part 4, D-87). A file that left this list was "
            "repaired; its reappearance means the repair was UNDONE, and regenerating would "
            "record that as permitted:",
            file=sys.stderr,
        )
        for f in pawl.added:
            print(f"  + {f}", file=sys.stderr)
        return 1

    paid_down = sorted(baseline - set(measured))
    payload = {
        "schema_version": "1.0",
        "$comment": (
            "Allowlist for check_entrypoint_guard_ratchet.py. Ruling D-67 part 4: an itemised "
            "allowlist of exactly today's population, GENERATED FROM THE MEASUREMENT AND NEVER "
            "HAND-TYPED, with its count recorded so shrinkage is visible. PAY-DOWN ONLY: a file "
            "leaves this list when repaired; NOTHING IS EVER ADDED. TWO assertions enforce that "
            "on every run of the guard, not only at regeneration (ruling D-87): (i) `files` is a "
            "SUBSET of `baseline_files`, so a hand-added NEW name fails the build; and (ii) "
            "`files` is a SUBSET OF ITS OWN PREVIOUS COMMITTED VALUE, read from git — the PAWL, "
            "which is what catches an already-REPAIRED file being put back. (i) alone is "
            "membership in a static baseline and permits a repaired file to return forever. "
            "Regenerate with "
            "`python platform/scripts/governance/check_entrypoint_guard_ratchet.py --regenerate`."
        ),
        "generated_by": "check_entrypoint_guard_ratchet.py --regenerate",
        "baseline_source": "00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json :: ratchet_allowlist.files",
        "baseline_authority": "ruling D-71 part 5 (two independent derivations, diff IDENTICAL)",
        "baseline_count": len(baseline),
        "count": len(measured),
        "paid_down_count": len(paid_down),
        "paid_down": paid_down,
        "files": measured,
        "baseline_files": sorted(baseline),
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"check_entrypoint_guard_ratchet: wrote {out.name} — "
        f"{len(measured)} allowlisted / {len(baseline)} baseline / {len(paid_down)} paid down."
    )
    return 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# THE PAWL — assertion (ii): the committed allowlist may only SHRINK  (ruling D-87)
# ═══════════════════════════════════════════════════════════════════════════════════════════
#
# PARĪKṢAKA's finding F-T, ruled on at D-87: the check above (`files ⊆ baseline_files`) is
# MEMBERSHIP AGAINST A STATIC BASELINE, which is a strictly weaker claim than the pay-down
# invariant D-67 part 4 and the amended SQ-29 both state. It asks "is every unguarded file one
# of the original 76?" and NEVER asks "has the allowlist GROWN since last time?". Under it a
# REPAIRED file stays a permissible member of the baseline forever, so it can be re-added, then
# have its guard stripped, and nothing objects. Reproduced end to end on `set-password.ts` — a
# credential-writing file that Wave 1 had already repaired.
#
#     D-87: "The gate needs TWO assertions, not one: (i) CURRENT POPULATION ⊆ COMMITTED
#      ALLOWLIST — exists today, catches a NEW unguarded file; (ii) COMMITTED ALLOWLIST ⊆ ITS
#      OWN PREVIOUS COMMITTED VALUE — MISSING, and it is the pawl. It catches a repaired file
#      RETURNING."
#
# WHERE "ITS OWN PREVIOUS COMMITTED VALUE" COMES FROM, AND WHY.
# The allowlist is a committed artifact and git is its ledger (D-87 part 4), so the previous
# value is read FROM GIT — never from the working tree, which proves nothing about what was
# there before, and never from a second copy of the list, which is just the same list twice.
# Which ref depends on what is being compared, and both cases are the same question asked from
# the two places the guard actually runs:
#
#   * WORKING TREE DIFFERS FROM `HEAD` (an agent has edited the list and not yet committed):
#     the previous value is `HEAD`. The growth is caught BEFORE it is ever committed.
#   * WORKING TREE EQUALS `HEAD` (a clean checkout — i.e. every CI run): comparing against
#     `HEAD` would be comparing a value with itself, which is exactly the vacuous shape this
#     ruling exists to remove. The previous value is `HEAD^` — the FIRST PARENT. On a
#     `pull_request` run that parent is the BASE BRANCH's tip, so the assertion made is
#     precisely "this change may not grow the allowlist relative to the branch it merges into".
#   * `--regenerate` writes a NEW value, so its predecessor is `HEAD`'s committed value
#     regardless of the working tree. Without this, `--regenerate` is the whole exploit in one
#     command: strip a repaired file's guard, regenerate, and the scan puts it back on the list
#     — every entry it would add is in the baseline, so the (i) check has nothing to say.
#
# WHAT IT ASSUMES ABOUT CI, STATED BECAUSE IT IS A REAL PRECONDITION AND NOT A DETAIL.
# `HEAD^` must exist in the checkout. `actions/checkout@v4` defaults to `fetch-depth: 1`, which
# fetches ONE commit and no parent — under it this check could not resolve a previous value at
# all. The job in `.github/workflows/nirmana-m0-guards.yml` therefore sets `fetch-depth: 2`
# explicitly, and this file's own verification of that is the failure mode below: when the
# previous value CANNOT BE READ the pawl is UNDETERMINED, and UNDETERMINED IS FATAL. It is
# never green. A baseline that cannot be read is an unknown, and §N.8's whole subject is that a
# check which cannot answer must not return the answer that happens to look clean — the same
# shape M0-T66 applied to unparsed files, and the shape that caught M0-T67 when a reference
# went `null` and a differential test compared `null` to `null`.
#
# WHAT IT DOES NOT DO, which is why it can be BLOCKING TODAY (D-87 part 3): it does not look at
# the 71 residual at all. Those are already in the committed allowlist, and this fires only when
# the allowlist GROWS. It is green on a clean tree with the entire backlog present and
# untouched. No `--strict`, no permanently-red gate, no waiting on the pay-down.

#: How far back the NON-GATING history observation walks. Bounded so the guard's cost cannot
#: grow with the repo's history.
HISTORY_SCAN_LIMIT = 200


@dataclass
class PawlResult:
    """The outcome of assertion (ii). `determined=False` is a FAILURE, never a pass."""

    determined: bool
    ok: bool
    comparison: str
    added: List[str] = field(default_factory=list)
    current_count: int = 0
    previous_ref: Optional[str] = None
    previous_commit: Optional[str] = None
    previous_count: Optional[int] = None
    reason: str = ""


def _git(repo: Path, *args: str) -> Tuple[int, str]:
    """Run git in `repo`. Returns (returncode, stdout). Never raises for a git-level failure."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return 127, ""
    return proc.returncode, proc.stdout


def _git_toplevel(start: Path) -> Optional[Path]:
    rc, out = _git(start, "rev-parse", "--show-toplevel")
    if rc != 0 or not out.strip():
        return None
    return Path(out.strip())


def _blob_at(repo: Path, ref: str, rel: str) -> Optional[str]:
    """The file's content at `ref`, or None if the ref or the path is not there."""
    rc, out = _git(repo, "show", f"{ref}:{rel}")
    return out if rc == 0 else None


def _files_of(raw: Optional[str]) -> Optional[List[str]]:
    """The `files` list out of an allowlist blob. None if it cannot be read — which is an
    UNKNOWN and must never be treated as an empty (i.e. maximally strict) list."""
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    files = data.get("files")
    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        return None
    return files


def _nearest_existing(repo: Path, start_ref: str, rel: str) -> Tuple[Optional[str], Optional[str]]:
    """(commit sha, blob) for the newest commit reachable from `start_ref` — inclusive — in
    which `rel` exists.

    The walk-back is not a nicety. Without it, DELETING the allowlist in one commit and
    re-adding a grown one in the next would present "no previous value" and read as a birth;
    with it, the deletion is walked straight through to the last commit that really had the
    list, and the growth is caught."""
    raw = _blob_at(repo, start_ref, rel)
    if raw is not None:
        rc, out = _git(repo, "rev-parse", start_ref)
        return (out.strip() if rc == 0 else start_ref), raw
    rc, out = _git(repo, "rev-list", f"--max-count={HISTORY_SCAN_LIMIT}", start_ref, "--", rel)
    if rc != 0:
        return None, None
    for sha in out.split():
        raw = _blob_at(repo, sha, rel)
        if raw is not None:
            return sha, raw
    return None, None


def pawl_check(
    allowlist_path: Path, current_files: Iterable[str], current_raw: Optional[str], mode: str
) -> PawlResult:
    """Assertion (ii): the value about to stand may not be a SUPERSET of the previous committed
    one. `mode` is 'scan' (the gate) or 'regenerate' (the writer's own precondition)."""
    current = set(current_files)
    repo = _git_toplevel(allowlist_path.parent)
    if repo is None:
        return PawlResult(
            determined=False,
            ok=False,
            comparison="none",
            current_count=len(current),
            reason=(
                "the allowlist is not inside a git working tree, so its PREVIOUS COMMITTED "
                "VALUE cannot be read. D-87 part 4: the allowlist is a committed artifact and "
                "git is its ledger."
            ),
        )
    try:
        rel = allowlist_path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:  # pragma: no cover — allowlist outside its own repo
        return PawlResult(
            determined=False,
            ok=False,
            comparison="none",
            current_count=len(current),
            reason="the allowlist resolves outside the git toplevel that contains it.",
        )

    head_raw = _blob_at(repo, "HEAD", rel)
    if mode == "regenerate":
        start_ref, comparison = "HEAD", "regenerate-vs-HEAD"
    elif head_raw is None or head_raw != current_raw:
        start_ref, comparison = "HEAD", "worktree-vs-HEAD"
    else:
        start_ref, comparison = "HEAD^", "HEAD-vs-parent"

    commit, raw = _nearest_existing(repo, start_ref, rel)
    previous = _files_of(raw)
    if previous is None:
        hint = (
            "`HEAD^` did not resolve to a commit carrying the allowlist. In CI this is almost "
            "always a SHALLOW checkout: actions/checkout@v4 defaults to fetch-depth 1, which "
            "fetches no parent — the job must set `fetch-depth: 2`."
            if start_ref == "HEAD^"
            else "no commit reachable from HEAD carries a readable allowlist."
        )
        return PawlResult(
            determined=False,
            ok=False,
            comparison=comparison,
            current_count=len(current),
            previous_ref=start_ref,
            previous_commit=commit,
            reason=(
                f"the PREVIOUS COMMITTED VALUE could not be read ({hint}) An unavailable "
                "baseline is UNKNOWN, never clean (§N.8), so this is a FAILURE and not a skip."
            ),
        )

    added = sorted(current - set(previous))
    return PawlResult(
        determined=True,
        ok=not added,
        comparison=comparison,
        added=added,
        current_count=len(current),
        previous_ref=start_ref,
        previous_commit=commit,
        previous_count=len(previous),
        reason=(
            "no entry was added relative to the previous committed value."
            if not added
            else f"{len(added)} entry/entries were ADDED relative to the previous committed value."
        ),
    )


def pawl_history(allowlist_path: Path) -> List[Dict]:
    """NON-GATING. Every step in the allowlist's committed history where the list GREW.

    Reported, never gated, and the reason is D-39 part 2 rather than timidity: a growth step
    already in history stays in history, so gating on it would be permanently red from the
    commit after it — the exact attrition trap the pawl above is shaped to avoid. Its value is
    that it names a growth the gate could have missed, e.g. one committed on a branch whose
    pushes do not run this workflow."""
    repo = _git_toplevel(allowlist_path.parent)
    if repo is None:
        return []
    try:
        rel = allowlist_path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:  # pragma: no cover
        return []
    rc, out = _git(repo, "rev-list", f"--max-count={HISTORY_SCAN_LIMIT}", "HEAD", "--", rel)
    if rc != 0:
        return []
    revs = out.split()
    seen: List[Tuple[str, List[str]]] = []
    for sha in revs:
        files = _files_of(_blob_at(repo, sha, rel))
        if files is not None:
            seen.append((sha, files))
    growths: List[Dict] = []
    for (newer_sha, newer), (older_sha, older) in zip(seen, seen[1:]):
        added = sorted(set(newer) - set(older))
        if added:
            growths.append({"commit": newer_sha, "parent_revision": older_sha, "added": added})
    return growths


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Self-test
# ═══════════════════════════════════════════════════════════════════════════════════════════

def _pawl_fixture_repo(tmp: Path, versions: Sequence[Sequence[str]]) -> Optional[Path]:
    """A throwaway git repo whose allowlist is committed once per entry in `versions`.

    Hermetic: `git init` in a temp dir, identity passed per-command, no global config read, no
    network, nothing outside `tmp`."""
    repo = tmp / "repo"
    (repo / "platform/scripts/governance").mkdir(parents=True, exist_ok=True)
    target = repo / "platform/scripts/governance/entrypoint_ratchet_allowlist.json"
    env_args = [
        "-c", "user.name=pawl-self-test",
        "-c", "user.email=pawl@self.test",
        "-c", "commit.gpgsign=false",
    ]
    if _git(repo, "init", "-q")[0] != 0:
        return None
    for i, files in enumerate(versions):
        target.write_text(json.dumps({"files": list(files)}, indent=2) + "\n", encoding="utf-8")
        if _git(repo, "add", "-A")[0] != 0:
            return None
        if _git(repo, *env_args, "commit", "-q", "-m", f"v{i}")[0] != 0:
            return None
    return target


def run_pawl_self_test() -> Tuple[List[str], int]:
    """Assertion (ii)'s own detector, proven in both directions on throwaway repos.

    D-87 part 6: *"Where a ruling states an invariant, the test that enforces it must be named
    in the same breath and checked against the words — otherwise the invariant lives only in
    prose."* This is that test. Four cases, and the two that matter most are the NEGATIVE ones:
    a repaired file RETURNING must be caught, and an unreadable previous value must FAIL rather
    than pass."""
    failures: List[str] = []
    checks = 0
    if _git(Path(tempfile.gettempdir()), "--version")[0] != 0:
        return (
            [
                "git is not available, so the PAWL's self-test cannot run. That is UNKNOWN, not "
                "clean (§N.8): the pawl reads the previous committed value from git and a run "
                "that cannot prove its own detector must not report a pass."
            ],
            0,
        )

    with tempfile.TemporaryDirectory(prefix="pawl-selftest-") as td:
        tmp = Path(td)

        # ── CASE 1 — SHRINK (a pay-down). Must PASS. ────────────────────────────────────────
        target = _pawl_fixture_repo(tmp / "shrink", [["a.ts", "b.ts", "c.ts"], ["a.ts", "b.ts"]])
        checks += 1
        if target is None:
            failures.append("pawl self-test could not build the SHRINK fixture repo")
        else:
            r = pawl_check(target, {"a.ts", "b.ts"}, target.read_text(encoding="utf-8"), "scan")
            if r.comparison != "HEAD-vs-parent":
                failures.append(
                    f"SHRINK: a CLEAN tree must compare HEAD against its parent, not "
                    f"'{r.comparison}' — comparing HEAD with itself is vacuous"
                )
            if not (r.determined and r.ok):
                failures.append(f"SHRINK: a pay-down must PASS the pawl — got {r.reason}")

        # ── CASE 2 — GROWTH, COMMITTED (F-T's exact sequence). Must FAIL. ──────────────────
        # v0 carries a repaired file's name; v1 re-adds it. This is `set-password.ts` returning.
        target = _pawl_fixture_repo(
            tmp / "grow", [["a.ts", "b.ts"], ["a.ts", "b.ts", "set-password.ts"]]
        )
        checks += 1
        if target is None:
            failures.append("pawl self-test could not build the GROWTH fixture repo")
        else:
            r = pawl_check(
                target,
                {"a.ts", "b.ts", "set-password.ts"},
                target.read_text(encoding="utf-8"),
                "scan",
            )
            if not r.determined:
                failures.append(f"GROWTH: the pawl was undetermined — {r.reason}")
            elif r.ok or r.added != ["set-password.ts"]:
                failures.append(
                    "GROWTH: a REPAIRED file returning to the allowlist must FAIL the pawl "
                    f"(added={r.added}, ok={r.ok}). This is finding F-T and it is the whole "
                    "reason this check exists."
                )

        # ── CASE 3 — GROWTH, UNCOMMITTED IN THE WORKING TREE. Must FAIL. ──────────────────
        target = _pawl_fixture_repo(tmp / "dirty", [["a.ts", "b.ts"]])
        checks += 1
        if target is None:
            failures.append("pawl self-test could not build the DIRTY fixture repo")
        else:
            grown = json.dumps({"files": ["a.ts", "b.ts", "set-password.ts"]}, indent=2) + "\n"
            target.write_text(grown, encoding="utf-8")
            r = pawl_check(target, {"a.ts", "b.ts", "set-password.ts"}, grown, "scan")
            if r.comparison != "worktree-vs-HEAD":
                failures.append(
                    f"DIRTY: an uncommitted edit must be compared against HEAD, got '{r.comparison}'"
                )
            if r.ok:
                failures.append("DIRTY: an uncommitted growth must FAIL the pawl before it lands")

        # ── CASE 4 — THE VACUOUS CASE. No previous value ⇒ FAIL, never pass. ──────────────
        # One commit only, so `HEAD^` does not exist. This is the shape of a SHALLOW CI
        # checkout (`fetch-depth: 1`), and it must be loud rather than clean.
        target = _pawl_fixture_repo(tmp / "orphan", [["a.ts", "b.ts"]])
        checks += 1
        if target is None:
            failures.append("pawl self-test could not build the ORPHAN fixture repo")
        else:
            r = pawl_check(target, {"a.ts", "b.ts"}, target.read_text(encoding="utf-8"), "scan")
            if r.determined or r.ok:
                failures.append(
                    "VACUOUS: with no previous committed value the pawl must be UNDETERMINED "
                    f"and FATAL, got determined={r.determined} ok={r.ok}. An unavailable "
                    "baseline is UNKNOWN, never clean (§N.8)."
                )

        # ── CASE 5 — DELETE-THEN-READD must not read as a birth. Must FAIL. ───────────────
        target = _pawl_fixture_repo(tmp / "deleted", [["a.ts", "b.ts"]])
        checks += 1
        if target is None:
            failures.append("pawl self-test could not build the DELETE fixture repo")
        else:
            repo = target.parents[3]
            target.unlink()
            _git(repo, "add", "-A")
            _git(
                repo, "-c", "user.name=pawl-self-test", "-c", "user.email=pawl@self.test",
                "-c", "commit.gpgsign=false", "commit", "-q", "-m", "delete the allowlist",
            )
            grown = json.dumps({"files": ["a.ts", "b.ts", "set-password.ts"]}, indent=2) + "\n"
            target.write_text(grown, encoding="utf-8")
            r = pawl_check(target, {"a.ts", "b.ts", "set-password.ts"}, grown, "scan")
            if r.ok:
                failures.append(
                    "DELETE-THEN-READD: deleting the allowlist and re-adding a GROWN one must "
                    "not read as a birth — the pawl must walk back to the last commit that "
                    "carried it"
                )

    return failures, checks

_EXPECT_RE = re.compile(r"EXPECT-VIOLATIONS:\s*(\d+)")
_EXPECT_GUARD_RE = re.compile(r"EXPECT-GUARD:\s*([\w./=~-]+)")


def run_self_test() -> int:
    failures: List[str] = []
    pass_dir, fail_dir = FIXTURE_DIR / "pass", FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        print(f"check_entrypoint_guard_ratchet: fixtures missing under {FIXTURE_DIR}", file=sys.stderr)
        return 1

    idioms_seen = set()
    n_pass = n_fail = 0

    for fx in sorted(pass_dir.iterdir()):
        if not fx.is_file() or fx.suffix not in CODE_SUFFIXES:
            continue
        n_pass += 1
        raw = fx.read_text(encoding="utf-8")
        unguarded, guarded, broken = analyse(raw)
        if broken:
            failures.append(f"PASS-fixture '{fx.name}' did not parse (unbalanced brace stack)")
        if unguarded:
            failures.append(
                f"PASS-fixture '{fx.name}' produced {len(unguarded)} violation(s) "
                f"(false positive): {[o.__dict__ for o in unguarded]}"
            )
        want = _EXPECT_GUARD_RE.search(raw)
        if want:
            got = {o.guarded_by for o in guarded}
            idioms_seen |= got
            if want.group(1) not in got:
                failures.append(
                    f"PASS-fixture '{fx.name}' declares EXPECT-GUARD: {want.group(1)} "
                    f"but the detector attributed {sorted(got)}"
                )

    for fx in sorted(fail_dir.iterdir()):
        if not fx.is_file() or fx.suffix not in CODE_SUFFIXES:
            continue
        n_fail += 1
        raw = fx.read_text(encoding="utf-8")
        unguarded, _guarded, broken = analyse(raw)
        if broken:
            failures.append(f"FAIL-fixture '{fx.name}' did not parse (unbalanced brace stack)")
        if not unguarded:
            failures.append(f"FAIL-fixture '{fx.name}' produced NO violation (false negative)")
            continue
        expected = _EXPECT_RE.search(raw)
        if expected and len(unguarded) != int(expected.group(1)):
            failures.append(
                f"FAIL-fixture '{fx.name}' declares EXPECT-VIOLATIONS: {expected.group(1)} "
                f"but produced {len(unguarded)}: {[o.line for o in unguarded]}"
            )

    # Every one of the five idioms must be exercised by a PASS fixture. Without this, an idiom
    # could be silently dropped from GUARD_IDIOMS and the suite would still be green — and the
    # tree's real guarded files would start being reported as violations.
    declared = {name for name, _ in GUARD_IDIOMS}
    missing = declared - idioms_seen
    if missing:
        failures.append(f"no PASS fixture exercises guard idiom(s): {sorted(missing)}")

    # The retired sentinel must NOT read as a guard.
    sentinel = "async function main() {}\nif (process.env.NODE_ENV !== 'test') {\n  main()\n}\n"
    if not analyse(sentinel)[0]:
        failures.append(
            "the RETIRED process.env.NODE_ENV sentinel was accepted as a guard "
            "(ruling D-9 / M0-T60: it asks the wrong question)"
        )

    # ── THE PAWL's OWN DETECTOR, proven in both directions (ruling D-87 part 6) ─────────────
    pawl_failures, pawl_checks = run_pawl_self_test()
    failures.extend(pawl_failures)

    if failures:
        print("check_entrypoint_guard_ratchet: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"check_entrypoint_guard_ratchet: SELF-TEST PASS ({n_pass} pass fixture(s) silent, "
        f"{n_fail} fail fixture(s) caught, {len(declared)}/{len(declared)} guard idioms "
        f"exercised, {pawl_checks} pawl case(s) proven in both directions)."
    )
    return 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════════════


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--self-test", action="store_true", help="Run bundled fixtures (hermetic).")
    ap.add_argument(
        "--regenerate",
        action="store_true",
        help="Rewrite the allowlist from the scan (pay-down only; refuses to add).",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Also fail on allowlisted residuals and on stale allowlist entries.",
    )
    ap.add_argument("--root", default=str(REPO_ROOT), help="Repo root to scan.")
    ap.add_argument("--roots", nargs="*", default=None, help="Override the scan roots.")
    ap.add_argument("--json", action="store_true", help="Emit a machine-readable report.")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    root = Path(args.root).resolve()
    scan_roots = args.roots if args.roots is not None else DEFAULT_ROOTS

    if args.regenerate:
        return regenerate(root, scan_roots, ALLOWLIST_PATH)

    allowlist = load_allowlist(ALLOWLIST_PATH)
    allowed = set(allowlist.get("files", []))
    baseline = set(allowlist.get("baseline_files") or load_baseline())
    allowlist_raw = ALLOWLIST_PATH.read_text(encoding="utf-8") if ALLOWLIST_PATH.exists() else None

    # ── ASSERTION (i): a NEW name in the allowlist. Static-baseline membership. ──────────────
    hand_added = sorted(allowed - baseline)

    # ── ASSERTION (ii): THE PAWL. The allowlist ⊆ its own PREVIOUS COMMITTED value. ──────────
    # (i) cannot see this one: a repaired file is still a member of the settled baseline, so
    # putting it back passes (i) forever. See the PAWL section above and ruling D-87.
    pawl = pawl_check(ALLOWLIST_PATH, allowed, allowlist_raw, mode="scan")
    history_growth = pawl_history(ALLOWLIST_PATH)

    results = scan(root, scan_roots)
    violating = {rel: r for rel, r in results.items() if r.unguarded}
    unparsed = sorted(rel for rel, r in results.items() if r.analysis_error)

    new = sorted(rel for rel in violating if rel not in allowed)
    residual = sorted(rel for rel in violating if rel in allowed)
    stale = sorted(f for f in allowed if f not in violating)

    # ── OUT-OF-SCOPE SUFFIXES, REPORTED BUT NOT GATED ───────────────────────────────────────
    # M0-T64's population command ends `| grep '\.ts$'`, which does not match `.mts` or `.cts`.
    # The gated population is therefore `.ts` only, so that it matches the settled baseline
    # exactly and the ratchet is green on day one (D-67 part 4). Files with the other TypeScript
    # module suffixes are scanned anyway and REPORTED — an unstated hole reads as coverage.
    extended: List[str] = []
    for p in iter_code_files(root, scan_roots, suffixes=EXTENDED_SUFFIXES):
        try:
            u, _g, _b = analyse(p.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        if u:
            extended.append(p.relative_to(root).as_posix())
    extended.sort()

    report = {
        "scan_roots": list(scan_roots),
        "files_with_top_level_main": len(results),
        "unguarded_files": len(violating),
        "guarded_files": sum(1 for r in results.values() if r.guarded and not r.unguarded),
        "allowlist_count": len(allowed),
        "baseline_count": len(baseline),
        "paid_down_count": len(baseline) - len(allowed),
        "new_violations": [
            {"file": rel, "lines": [o.line for o in violating[rel].unguarded]} for rel in new
        ],
        "residual_allowlisted": residual,
        "stale_allowlist_entries": stale,
        "hand_added_allowlist_entries": hand_added,
        "pawl": {
            "determined": pawl.determined,
            "pass": pawl.ok,
            "comparison": pawl.comparison,
            "previous_ref": pawl.previous_ref,
            "previous_commit": pawl.previous_commit,
            "previous_count": pawl.previous_count,
            "current_count": pawl.current_count,
            "added_since_previous_commit": pawl.added,
            "reason": pawl.reason,
        },
        "committed_history_growth_steps": history_growth,
        "unparsed_files": unparsed,
        "out_of_scope_suffix_observations": extended,
    }

    # An unparsed file is UNKNOWN, not clean, and is therefore blocking. See §N.8: a detector
    # that cannot answer must not return the answer that happens to look green.
    fail = (
        bool(new)
        or bool(hand_added)
        or not pawl.ok
        or bool(unparsed)
        or (args.strict and (residual or stale))
    )
    report["pass"] = not fail

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if fail else 0

    print(
        f"check_entrypoint_guard_ratchet: {len(results)} file(s) with a top-level main() under "
        f"{', '.join(scan_roots)} — {len(violating)} unguarded, "
        f"{report['guarded_files']} guarded."
    )
    print(
        f"  ratchet: {len(allowed)} allowlisted of M0-T64's {len(baseline)} baseline "
        f"({report['paid_down_count']} paid down)."
    )
    if pawl.determined and pawl.ok:
        print(
            f"  pawl: allowlist ({pawl.current_count}) ⊆ its previous committed value "
            f"({pawl.previous_ref} {(pawl.previous_commit or '')[:9]}, {pawl.previous_count}) — "
            "it did not grow."
        )

    if unparsed:
        print(
            f"check_entrypoint_guard_ratchet: {len(unparsed)} file(s) did NOT PARSE (unbalanced "
            "brace stack after comment/string/regex blanking). Their result is UNKNOWN, not "
            "clean, so the run fails rather than reporting a green it did not earn. FAIL.",
            file=sys.stderr,
        )
        for f_ in unparsed:
            print(f"  ? {f_}", file=sys.stderr)

    if extended:
        print(
            f"  NOTE — {len(extended)} file(s) with an unguarded top-level main() are OUTSIDE "
            "this ratchet's gated population because M0-T64's baseline was derived with a "
            "`.ts$` filter, which structurally cannot match `.mts`/`.cts`. They are reported "
            "here and NOT gated: D-67 part 4 forbids adding anything to the allowlist, so "
            "extending the baseline is ADHIKĀRIN's call, not this script's (finding F-P):"
        )
        for f_ in extended:
            print(f"    ! {f_}")

    if not pawl.ok:
        if not pawl.determined:
            print(
                "check_entrypoint_guard_ratchet: THE PAWL COULD NOT RUN — "
                f"{pawl.reason} FAIL.",
                file=sys.stderr,
            )
        else:
            print(
                f"check_entrypoint_guard_ratchet: {len(pawl.added)} allowlist entry/entries are "
                f"NOT in the PREVIOUS COMMITTED allowlist "
                f"({pawl.previous_ref} {(pawl.previous_commit or '')[:9]}, "
                f"{pawl.previous_count} entries). THE ALLOWLIST MAY ONLY SHRINK (D-67 part 4, "
                "D-71 part 7, D-87). Every one of these was on the list before and LEFT it, "
                "which means it was REPAIRED; putting it back re-opens a hole that was closed, "
                "and the static-baseline check cannot see it because a repaired file remains a "
                "member of the settled baseline forever. FAIL.",
                file=sys.stderr,
            )
            for f in pawl.added:
                print(f"  + {f}", file=sys.stderr)

    if history_growth:
        print(
            f"  NOTE — the allowlist's committed history contains {len(history_growth)} step(s) "
            "in which it GREW. Reported, NOT gated: a growth already in history stays in "
            "history, so gating on it would be permanently red from the next commit onward "
            "(D-39 part 2). Bring it to ADHIKĀRIN:"
        )
        for g in history_growth:
            print(f"    ! {g['commit'][:9]} added {', '.join(g['added'])}")

    if hand_added:
        print(
            f"check_entrypoint_guard_ratchet: {len(hand_added)} allowlist entry/entries are NOT "
            "in M0-T64's settled baseline. The list may only SHRINK (D-67 part 4). FAIL.",
            file=sys.stderr,
        )
        for f in hand_added:
            print(f"  + {f}", file=sys.stderr)

    if stale:
        print(f"  {len(stale)} allowlisted file(s) are now CLEAN — regenerate to record the pay-down:")
        for f in stale:
            print(f"    ✔ {f}")

    if new:
        print(
            f"check_entrypoint_guard_ratchet: {len(new)} NEW unguarded top-level main() — "
            "importing this file runs its program. FAIL.",
            file=sys.stderr,
        )
        for rel in new:
            for o in violating[rel].unguarded:
                print(f"  {rel}:{o.line}   [{o.context}]", file=sys.stderr)
        print(
            "  Fix: import { isDirectEntrypoint } from '<rel>/lib/entrypoint' and wrap the call:\n"
            "    if (isDirectEntrypoint(import.meta.url, process.argv[1])) { main() }\n"
            "  (A CI GATE whose hazard is FAILING to run uses the opposite IMPORT_ONLY contract "
            "instead — scripts/audit/A3_env_matrix.md Addendum A3.4.)",
            file=sys.stderr,
        )

    if args.strict and residual:
        print(
            f"check_entrypoint_guard_ratchet: STRICT — {len(residual)} allowlisted residual(s). FAIL.",
            file=sys.stderr,
        )

    if not fail:
        print("check_entrypoint_guard_ratchet: 0 new unguarded top-level main(). PASS.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
