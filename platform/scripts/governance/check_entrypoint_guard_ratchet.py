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
  4. **THE FLOOR — THE ALLOWLIST MAY ONLY SHRINK RELATIVE TO A PERSISTED LOW-WATER MARK
     (ruling D-95, superseding D-87 part 3).** D-87 first closed this gap by asserting the
     allowlist is a subset of its own previous COMMITTED value, read from git (`HEAD^` on a
     clean checkout). PARĪKṢAKA's V-64 measured that reference SLIDES: one commit after a
     growth lands, `HEAD^` has itself absorbed it and the comparison passes vacuously —
     caught live when `origin/main` brought three unguarded files in via M0-T16's merge; red
     at the merge commit, green the very next one. D-95's fix: the reference is not a git
     ref at all. It is a separate committed artifact, `entrypoint_guard_floor.json`, holding
     the SMALLEST allowlist ever committed. Every run asserts CURRENT ⊆ FLOOR; a real
     pay-down (current a STRICT subset of floor) makes the SAME command that records it also
     sync the floor to match. Growth beyond the floor is RED AND STAYS RED — no ref to slide
     behind. See THE FLOOR section below, including the floor's own protection against being
     hand-widened.

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

Exit codes: 0 = pass · 1 = a NEW (non-allowlisted) violation, an allowlist that GREW beyond
the settled baseline OR beyond the persisted FLOOR, a floor that is WIDER than any value its
own committed history has ever held, a file the scanner could not parse, a current-allowlist
or floor value that could not be READ, or `--strict` with any residual.
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
#: THE FLOOR (ruling D-95) — the smallest allowlist ever committed. See THE FLOOR section
#: below for the full mechanism. Written ONLY by `write_floor` (called from `sync_floor`,
#: itself called from `--regenerate` on a real pay-down, or standalone via `--sync-floor`).
FLOOR_PATH = HERE / "entrypoint_guard_floor.json"
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

    # A SCAN THAT COULD NOT ANSWER MAY NOT WRITE THE LIST. The repo scan already treats an
    # unparsed file as UNKNOWN and fails; regeneration did not, and it is the more dangerous of
    # the two — a file the scanner mis-reads produces NO occurrences, so it drops OUT of the
    # measured set and the written allowlist SHRINKS. A shrink is the good direction, so neither
    # the subset check nor the floor pre-check objects, and the pay-down would be recorded as
    # real (§N.8:
    # the detector that cannot answer must not write the answer that looks like progress). This
    # is the exact failure mode M0-T66's F-Q found in this scanner: twelve of the settled 76
    # reported clean by a desynchronised blanker.
    unparsed = sorted(rel for rel, r in results.items() if r.analysis_error)
    if unparsed:
        print(
            f"check_entrypoint_guard_ratchet: REFUSING to regenerate — {len(unparsed)} file(s) "
            "did NOT PARSE. Their result is UNKNOWN, and a file the scanner cannot read looks "
            "exactly like a file that was repaired, so regenerating would record a pay-down "
            "that did not happen:",
            file=sys.stderr,
        )
        for f in unparsed:
            print(f"  ? {f}", file=sys.stderr)
        return 1

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

    # ── THE FLOOR PRE-CHECK (ruling D-95, superseding D-87's "ASSERTION (ii)" here) ─────────
    # Without this, `--regenerate` is the exploit in one command: strip a repaired file's
    # guard, regenerate, and the scan puts that file straight back on the list. D-87 caught
    # this against the allowlist's own previous committed value; D-95 moves the reference to
    # the FLOOR, which — unlike that value — does not slide one commit after a growth lands.
    floor_on_disk = read_current_side(FLOOR_PATH)
    if floor_on_disk is not None:
        beyond_floor = sorted(set(measured) - set(floor_on_disk))
        if beyond_floor:
            print(
                f"check_entrypoint_guard_ratchet: REFUSING to regenerate — the scan would "
                f"ADD {len(beyond_floor)} file(s) the FLOOR ({len(floor_on_disk)} entries) "
                "does not carry. THE ALLOWLIST MAY ONLY SHRINK RELATIVE TO THE FLOOR (D-67 "
                "part 4, D-95). A file the floor does not carry was either never on it or "
                "was repaired and left it; its reappearance means the repair was UNDONE, "
                "and regenerating would record that as permitted:",
                file=sys.stderr,
            )
            for f in beyond_floor:
                print(f"  + {f}", file=sys.stderr)
            return 1
    else:
        print(
            "check_entrypoint_guard_ratchet: NOTE — no floor exists yet "
            f"({FLOOR_PATH.name} not found). Writing the allowlist below without a floor "
            "check; run --sync-floor once it is committed."
        )

    paid_down = sorted(baseline - set(measured))
    payload = {
        "schema_version": "1.0",
        "$comment": (
            "Allowlist for check_entrypoint_guard_ratchet.py. Ruling D-67 part 4: an itemised "
            "allowlist of exactly today's population, GENERATED FROM THE MEASUREMENT AND NEVER "
            "HAND-TYPED, with its count recorded so shrinkage is visible. PAY-DOWN ONLY: a file "
            "leaves this list when repaired; NOTHING IS EVER ADDED. TWO assertions enforce that "
            "on every run of the guard, not only at regeneration (ruling D-95, superseding "
            "D-87 part 3): (i) `files` is a SUBSET of `baseline_files`, so a hand-added NEW "
            "name fails the build; and (ii) `files` is a SUBSET OF THE PERSISTED FLOOR "
            "(entrypoint_guard_floor.json — the smallest allowlist ever committed), which is "
            "what catches an already-REPAIRED file being put back, without depending on a "
            "git ref that slides one commit after the growth it was meant to catch. (i) "
            "alone is membership in a static baseline and permits a repaired file to return "
            "forever. Regenerate with "
            "`python platform/scripts/governance/check_entrypoint_guard_ratchet.py --regenerate` "
            "— a real pay-down syncs the floor in the same command."
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

    # ── THE SELF-UPDATE (ruling D-95 point 3): sync the floor IN THE SAME INVOCATION ─────────
    # so the pay-down and the floor's new low-water mark land in one working-tree diff and
    # whoever commits, commits both together — by construction, not by remembering a second
    # step. `sync_floor` is itself shrink-only (D-96): it cannot be the path growth reaches
    # the floor through, because it refuses outright the instant its target is not a subset
    # of the value already on disk.
    if floor_on_disk is not None and set(measured) < set(floor_on_disk):
        return sync_floor(FLOOR_PATH, measured, source="--regenerate scan")
    return 0


# ═══════════════════════════════════════════════════════════════════════════════════════════
# THE FLOOR — assertion (ii): the current allowlist may only shrink relative to a
# PERSISTED LOW-WATER MARK, never a sliding git ref  (ruling D-95, superseding D-87 part 3)
# ═══════════════════════════════════════════════════════════════════════════════════════════
#
# D-87 (PARĪKṢAKA's finding F-T) first closed the gap in assertion (i): membership in the
# static M0-T64 baseline never asks "has the allowlist grown SINCE LAST TIME", so a repaired
# file could return, then be stripped of its guard again, forever. D-87's fix compared the
# allowlist to ITS OWN PREVIOUS COMMITTED VALUE, read from git: `HEAD` when the working tree
# carries an uncommitted edit, `HEAD^` (the first parent) on a clean checkout.
#
# ADHIKĀRIN's D-95 (PARĪKṢAKA's V-64) found that reference SLIDES. `HEAD^` is the commit
# immediately before HEAD — and one commit after a growth lands, HEAD^ IS the growth commit,
# so "current ⊆ HEAD^" becomes a comparison against itself and passes vacuously. This is not
# hypothetical: `origin/main` brought THREE unguarded files into this branch via M0-T16's
# merge. The gate was red at the merge commit (HEAD^ was the campaign's pre-merge tip, which
# did not carry them) and green the very next commit (HEAD^ became the merge commit itself,
# which did). A pawl whose reference slides one commit behind the growth is, in D-95's words,
# "a ratchet whose pawl engages for one commit and then releases" — most of the way back to
# no pawl at all.
#
# D-95's FIX: THE REFERENCE IS NOT A GIT REF AT ALL. It is a separate, independently
# committed artifact — `entrypoint_guard_floor.json` — holding the SMALLEST allowlist ever
# committed. Every run of this script asserts:
#
#     CURRENT ALLOWLIST  ⊆  FLOOR
#
# both read directly off disk (the same way `read_current_side` already reads the allowlist —
# whatever is on disk right now, dirty or clean, IS "current"). The floor does not move on
# its own; it moves only when something DELIBERATELY moves it (see "THE SELF-UPDATE" below).
# A growth beyond the floor is therefore RED AND STAYS RED across every subsequent commit
# until it is paid back — there is no adjacent commit whose HEAD^ has quietly absorbed it,
# because the floor was never a function of HEAD^ in the first place.
#
# WHY THIS IS NOT D-39 PART 2's forbidden permanently-red gate (D-95's own distinction, and
# it is about CLEARABILITY, not redness): a red on "the committed allowlist's history once
# contained a growth" is UNCLEARABLE — no forward action erases a fact about history, and H2
# forbids rewriting it. A red on "the CURRENT allowlist is larger than the floor" is
# clearable by the obvious forward action: RE-GUARD THE FILE. That shrinks current back to
# ⊆ floor and the gate goes green again, on the merits, exactly as D-84 ordered for `.mts`
# and D-73/D-84 ordered generally: the test is always "can this be cleared by doing the
# right thing", never "did this ever happen".
#
# THE SELF-UPDATE — keeping the floor equal to the smallest current has ever been, in the
# SAME commit that earns it (see `sync_floor` below). D-96 forbids an exemption field of any
# kind — "a bypass with a ruling-id painted on it is a bypass" — so there is NO flag anywhere
# that lets a commit declare its own growth authorised; the ONLY way the floor is ever
# allowed to grow is the same forward action stated above, never a data field. Concretely:
#
#   * `--regenerate` (T66's writer) computes `measured` from a fresh scan, same as always.
#     If `measured` is not a subset of the FLOOR on disk, it refuses to write — the same
#     shape as its existing refusal against the M0-T64 baseline, just against the new
#     reference. If `measured` IS a subset, and STRICTLY smaller (a real pay-down), the SAME
#     invocation ALSO rewrites `entrypoint_guard_floor.json` to equal `measured`. One
#     command, one working-tree diff touching both files — whoever stages and commits does
#     so together BY CONSTRUCTION, not by remembering a second step.
#   * `--sync-floor` is the standalone form of the same write: it takes the currently
#     committed allowlist (never a hand value) as its target and applies the identical
#     shrink-only rule. It exists for the one case `--regenerate` cannot cover by itself:
#     creating the floor for the first time (this session's own job — see the report for the
#     measured seed value) and any future manual recovery. It is NEVER invoked automatically
#     by a bare check run; a read-only gate never writes a file (D-77's spirit extended: a
#     check does not mutate the tree it is checking).
#
# Neither writer can ever WIDEN the floor: both compute their target from a MEASUREMENT (a
# fresh scan, or the already-validated on-disk allowlist), both refuse outright the instant
# the target is not a subset of the floor's current on-disk value, and neither ever reads a
# "requested" or "declared" value from anywhere a hand could reach. The only way growth ever
# reaches the floor file is a genuine, generated shrink landing through one of these paths.
#
# THE FLOOR'S OWN INTEGRITY — a floor that anything could hand-widen is the same defect T68
# built and D-89 named, one layer up (§N.8: "a signal without a real detector is null, not
# green"). `floor_monotone_check` below is that detector, and it is deliberately NOT shaped
# like D-87's adjacent HEAD-vs-HEAD^ comparison — an adjacent-only check on the floor's OWN
# history would inherit the EXACT one-commit-release flaw D-95 exists to remove, one file
# over. Instead it walks the floor's ENTIRE committed history (bounded by
# `HISTORY_SCAN_LIMIT`, the same bound `pawl_history` below already uses) and asserts the
# CURRENT floor is a subset of EVERY value it has ever held — a hand-widened commit is
# caught not only at the moment it lands but at every commit after it, for as long as the
# widening still stands, closing exactly the gap that let D-87's single-step version go
# quiet. It is clearable the same way as the main gate: shrink the floor back to ⊆
# everything before it, and it is green again.
#
# WHAT IT DOES NOT DO, stated because an unstated limit reads as coverage: it does not look
# at the 71 residual at all — those already sit inside the floor by construction, so this
# fires only when the current allowlist grows PAST what the floor has ever recorded. It is
# green on a clean tree with the entire backlog present and untouched. No `--strict`, no
# permanently-red gate, no waiting on the pay-down.


#: How far back the NON-GATING history observation walks. Bounded so the guard's cost cannot
#: grow with the repo's history.
HISTORY_SCAN_LIMIT = 200


@dataclass
class FloorResult:
    """The outcome of one floor-side assertion (`check` is 'containment' or 'monotonicity').
    `determined=False` is a FAILURE, never a pass — the same §N.8 discipline `PawlResult`
    (D-87, now superseded by D-95) was built on: an unknown must never read as clean."""

    determined: bool
    ok: bool
    check: str
    added: List[str] = field(default_factory=list)
    current_count: int = 0
    violations: List[Dict] = field(default_factory=list)
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


def read_current_side(allowlist_path: Path) -> Optional[List[str]]:
    """A JSON `files` list read straight off disk — or **None**, meaning it could not be read.
    Generic over WHICH file: called on the allowlist AND on the floor, since D-95 reads both
    "the same way" (straight off disk, dirty or clean).

    Deliberately NOT `load_allowlist`, which substitutes an empty `files` for a missing file so
    that the rest of a run can still report. An empty list is a well-formed operand, so handing
    that substitution to a subset comparison would make DELETING the file compare ∅ ⊆ anything
    and PASS — the empty-operand pass ruling D-89 forbids. The distinction between "absent" and
    "empty" lives here, in one function, with a self-test case on it."""
    if not allowlist_path.exists():
        return None
    try:
        data = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError):
        return None
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        return None
    return list(files)


def write_floor(path: Path, files: Sequence[str], note: str) -> None:
    """Write the floor artifact. THE ONLY WRITER is `sync_floor` — it only ever calls this
    with a target that is a subset of (never wider than) the value already on disk, or with
    no prior value at all (first-time creation). No other code path in this file ever writes
    to `FLOOR_PATH`."""
    payload = {
        "schema_version": "1.0",
        "$comment": (
            "Floor for check_entrypoint_guard_ratchet.py — ruling D-95, superseding D-87 "
            "part 3. Holds the SMALLEST allowlist ever committed. Every run asserts CURRENT "
            "ALLOWLIST \u2286 FLOOR (floor_containment) and FLOOR \u2286 EVERY VALUE ITS OWN "
            "COMMITTED HISTORY HAS EVER HELD (floor_monotone_check). The floor moves ONLY "
            "via `--regenerate` (auto-sync on a real pay-down) or `--sync-floor` "
            "(standalone) — both refuse to write anything that is not a subset of the value "
            "already on disk. D-96: no field anywhere in this file authorises a widening — "
            "the only sanctioned path is guard-the-file-then-shrink, or a brand new "
            "explicitly-ruled baseline, never a flag here."
        ),
        "generated_by": "check_entrypoint_guard_ratchet.py --regenerate / --sync-floor",
        "note": note,
        "count": len(files),
        "files": sorted(files),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sync_floor(floor_path: Path, target_files: Sequence[str], source: str) -> int:
    """Bring the floor to equal `target_files` — SHRINK-ONLY, print+return 0/1 like the rest
    of this file's writers. Never widens: refuses outright if `target_files` carries
    anything the existing floor does not, so growth cannot reach the floor through this door
    either. First-time creation (no floor on disk yet) is the one case with no prior value
    to violate, and it is exactly this session's own act — see the report for the measured
    seed."""
    target = sorted(set(target_files))
    floor_disk = read_current_side(floor_path)
    if floor_disk is None:
        if floor_path.exists():
            print(
                f"check_entrypoint_guard_ratchet: REFUSING to sync floor — {floor_path.name} "
                "exists but is unreadable (unparsable, or missing a well-formed `files` "
                "list). An unreadable floor is UNKNOWN, never a blank slate to overwrite "
                "(\u00a7N.8).",
                file=sys.stderr,
            )
            return 1
        write_floor(floor_path, target, note=f"initial floor, seeded from {source}")
        print(
            f"check_entrypoint_guard_ratchet: created {floor_path.name} — {len(target)} "
            f"entries (seeded from {source})."
        )
        return 0
    added = sorted(set(target) - set(floor_disk))
    if added:
        print(
            f"check_entrypoint_guard_ratchet: REFUSING to sync floor — {source} carries "
            f"{len(added)} entry/entries the existing floor ({len(floor_disk)}) does not. "
            "THE FLOOR MAY ONLY SHRINK (D-95; D-96 — no exemption exists for this). Repair "
            "the file(s) so the source no longer needs them, or bring a NEW "
            "explicitly-ruled baseline to ADHIKĀRIN:",
            file=sys.stderr,
        )
        for f in added:
            print(f"  + {f}", file=sys.stderr)
        return 1
    if set(target) == set(floor_disk):
        print(
            f"check_entrypoint_guard_ratchet: floor already in sync ({len(floor_disk)} "
            "entries) — nothing to do."
        )
        return 0
    write_floor(floor_path, target, note=f"pay-down synced from {source}")
    print(
        f"check_entrypoint_guard_ratchet: floor synced — {len(floor_disk)} \u2192 "
        f"{len(target)} ({len(floor_disk) - len(target)} paid down, from {source})."
    )
    return 0


def floor_containment(
    current_files: Optional[Iterable[str]], floor_files: Optional[Iterable[str]]
) -> FloorResult:
    """Assertion: the current allowlist is a subset of the floor. D-89 anchoring: either
    side being unreadable is UNDETERMINED, never a vacuous pass — the same rule `pawl_check`
    (D-87, now superseded) was built on, applied here to two different files instead of one
    file across two points in time."""
    if current_files is None or floor_files is None:
        return FloorResult(
            determined=False,
            ok=False,
            check="containment",
            reason=(
                "the current allowlist or the floor could not be read (missing, unparsable, "
                "or no well-formed `files` list) — an absent operand cannot make a subset "
                "comparison return true or false (D-89), so this is UNDETERMINED."
            ),
        )
    current = set(current_files)
    floor = set(floor_files)
    added = sorted(current - floor)
    return FloorResult(
        determined=True,
        ok=not added,
        check="containment",
        added=added,
        current_count=len(current),
        reason=(
            "the current allowlist is a subset of the floor."
            if not added
            else f"{len(added)} entry/entries in the current allowlist are NOT covered by the floor."
        ),
    )


def floor_monotone_check(floor_path: Path, current_files: Optional[Iterable[str]]) -> FloorResult:
    """Assertion: the floor is a subset of EVERY value its own committed history has ever
    held — not merely its immediate parent (`HEAD^`), which is precisely the shape that let
    D-87's version of this idea slide one commit after a growth landed (D-95). Walking the
    FULL history (bounded by `HISTORY_SCAN_LIMIT`) means a hand-widened commit stays caught
    for as long as the widening stands, not only at the instant it lands.

    `current_files=None` is UNDETERMINED, never a pass (D-89's anchor-both-sides rule)."""
    if current_files is None:
        return FloorResult(
            determined=False,
            ok=False,
            check="monotonicity",
            reason=(
                "the floor could not be read from disk (missing, unparsable, or no "
                "well-formed `files` list). An absent floor is UNKNOWN, not a pass (\u00a7N.8)."
            ),
        )
    current = set(current_files)
    repo = _git_toplevel(floor_path.parent)
    if repo is None:
        return FloorResult(
            determined=False,
            ok=False,
            check="monotonicity",
            current_count=len(current),
            reason="the floor is not inside a git working tree, so its committed history cannot be read.",
        )
    try:
        rel = floor_path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:  # pragma: no cover — floor outside its own repo
        return FloorResult(
            determined=False,
            ok=False,
            check="monotonicity",
            current_count=len(current),
            reason="the floor resolves outside the git toplevel that contains it.",
        )
    rc, out = _git(repo, "rev-list", f"--max-count={HISTORY_SCAN_LIMIT}", "HEAD", "--", rel)
    if rc != 0:
        return FloorResult(
            determined=False,
            ok=False,
            check="monotonicity",
            current_count=len(current),
            reason="`git rev-list` could not walk the floor's committed history.",
        )
    violations: List[Dict] = []
    for sha in out.split():
        raw = _blob_at(repo, sha, rel)
        if raw is None:
            # The floor did not exist at this commit (before it was first written, or a
            # delete-then-readd gap) — nothing to compare against. Skip, don't fail; this is
            # the same not-a-violation shape the old delete-then-readd walk-back relied on.
            continue
        files = _files_of(raw)
        if files is None:
            # The floor EXISTED at this commit but did not parse. A PRESENT, unreadable
            # value is not an absence — fail rather than silently treat it as agreeing.
            return FloorResult(
                determined=False,
                ok=False,
                check="monotonicity",
                current_count=len(current),
                reason=(
                    f"commit {sha[:9]} carries an unreadable floor — cannot verify "
                    "monotonicity through it."
                ),
            )
        added = sorted(current - set(files))
        if added:
            violations.append({"commit": sha, "added": added})
    return FloorResult(
        determined=True,
        ok=not violations,
        check="monotonicity",
        added=sorted({f for v in violations for f in v["added"]}),
        current_count=len(current),
        violations=violations,
        reason=(
            "the current floor is a subset of every value its committed history has ever held."
            if not violations
            else (
                f"the current floor is WIDER than {len(violations)} historical commit(s) — "
                "it was hand-widened and never fully paid back."
            )
        ),
    )


def pawl_history(allowlist_path: Path) -> List[Dict]:
    """NON-GATING. Every step in the allowlist's committed history where the list GREW.

    Reported, never gated, and the reason is D-39 part 2 rather than timidity: a growth step
    already in history stays in history, so gating on it would be permanently red from the
    commit after it — the exact attrition trap THE FLOOR above is shaped to avoid by testing
    CLEARABILITY instead of "did this ever happen". Its value is that it names a growth the
    gate could have missed, e.g. one committed on a branch whose pushes do not run this
    workflow. Called on both `ALLOWLIST_PATH` (unchanged, D-67 part 4) and `FLOOR_PATH`
    (`floor_history_growth_steps`, new under D-95) — same non-gating diagnostic, either file."""
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

def _git_fixture_repo(
    tmp: Path,
    versions: Sequence[Sequence[str]],
    filename: str = "entrypoint_ratchet_allowlist.json",
) -> Optional[Path]:
    """A throwaway git repo whose `filename` is committed once per entry in `versions`.

    Shared by the containment/monotonicity self-tests for BOTH the allowlist and the floor —
    the mechanics of "a JSON file with a `files` list, committed N times" do not care which
    artifact it stands in for.

    Hermetic: `git init` in a temp dir, identity passed per-command, no global config read,
    no network, nothing outside `tmp`."""
    repo = tmp / "repo"
    (repo / "platform/scripts/governance").mkdir(parents=True, exist_ok=True)
    target = repo / "platform/scripts/governance" / filename
    env_args = [
        "-c", "user.name=ratchet-self-test",
        "-c", "user.email=ratchet@self.test",
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

def run_floor_self_test() -> Tuple[List[str], int]:
    """THE FLOOR's own detector, proven in both directions (rulings D-95, D-96; the same
    discipline D-87 part 6 required — 'where a ruling states an invariant, the test that
    enforces it must be named in the same breath'). The two cases that matter most: a merge
    that lands growth must STAY red past the next commit (closing the exact release D-95
    found), and nothing may ever widen the floor by any path other than a genuine, measured
    shrink landing (D-96)."""
    failures: List[str] = []
    checks = 0

    if _git(Path(tempfile.gettempdir()), "--version")[0] != 0:
        return (
            [
                "git is not available, so THE FLOOR's self-test cannot run. That is "
                "UNKNOWN, not clean (\u00a7N.8)."
            ],
            0,
        )

    with tempfile.TemporaryDirectory(prefix="floor-selftest-") as td:
        tmp = Path(td)

        # ── CASE 1/2 — CONTAINMENT, direct. ─────────────────────────────────────────────
        checks += 1
        r = floor_containment(["a.ts", "b.ts"], ["a.ts", "b.ts", "c.ts"])
        if not (r.determined and r.ok):
            failures.append(f"CONTAINMENT: a real subset must PASS — got {r.reason}")
        checks += 1
        r = floor_containment(["a.ts", "b.ts", "z.ts"], ["a.ts", "b.ts"])
        if r.determined and r.ok:
            failures.append("CONTAINMENT: a file beyond the floor must FAIL")
        elif r.added != ["z.ts"]:
            failures.append(f"CONTAINMENT: expected added=['z.ts'], got {r.added}")

        # ── CASE 3/4 — D-89 ANCHORING: either side missing is UNDETERMINED, never a pass. ─
        checks += 1
        r = floor_containment(None, ["a.ts"])
        if r.determined or r.ok:
            failures.append("CONTAINMENT: a missing CURRENT side must be UNDETERMINED and FATAL")
        checks += 1
        r = floor_containment(["a.ts"], None)
        if r.determined or r.ok:
            failures.append("CONTAINMENT: a missing FLOOR side must be UNDETERMINED and FATAL")

        # ── CASE 5 — MONOTONICITY, SHRINK-ONLY HISTORY. Must PASS at every step. ─────────
        target = _git_fixture_repo(
            tmp / "shrink", [["a.ts", "b.ts", "c.ts"], ["a.ts", "b.ts"], ["a.ts"]],
            filename="entrypoint_guard_floor.json",
        )
        checks += 1
        if target is None:
            failures.append("FLOOR self-test could not build the SHRINK fixture repo")
        else:
            r = floor_monotone_check(target, ["a.ts"])
            if not (r.determined and r.ok):
                failures.append(f"MONOTONICITY-SHRINK: a shrink-only history must PASS — got {r.reason}")

        # ── CASE 6 — THE D-95 MOTIVATING SCENARIO: a merge lands growth, and it must STAY
        # red one commit AFTER the merge too — not release the way D-87's version did. ────
        # v0: shared ancestor, floor=[a,b,c]. v1: campaign branch pays down to [a,b]. v2: a
        # merge-shaped commit that (like M0-T16's real merge) resurrects the wider value
        # from the other side. v3: an unrelated commit that does NOT touch the floor — "the
        # campaign kept working" — proving the check still fires with the floor untouched.
        checks += 1
        env_args = [
            "-c", "user.name=ratchet-self-test", "-c", "user.email=ratchet@self.test",
            "-c", "commit.gpgsign=false",
        ]
        repo = tmp / "merge" / "repo"
        (repo / "platform/scripts/governance").mkdir(parents=True, exist_ok=True)
        target = repo / "platform/scripts/governance/entrypoint_guard_floor.json"
        ok_repo = _git(repo, "init", "-q")[0] == 0

        def _commit(files_for_floor, extra_file, msg):
            if files_for_floor is not None:
                target.write_text(
                    json.dumps({"files": files_for_floor}, indent=2) + "\n", encoding="utf-8"
                )
            if extra_file is not None:
                (repo / extra_file).write_text("x", encoding="utf-8")
            if _git(repo, "add", "-A")[0] != 0:
                return False
            return _git(repo, *env_args, "commit", "-q", "-m", msg)[0] == 0

        if ok_repo:
            ok_repo = _commit(["a.ts", "b.ts", "c.ts"], None, "v0 shared ancestor")
        if ok_repo:
            ok_repo = _commit(["a.ts", "b.ts"], None, "v1 campaign pays down")
        if ok_repo:
            ok_repo = _commit(["a.ts", "b.ts", "c.ts"], None, "v2 merge resurrects the wider value")
        if ok_repo:
            ok_repo = _commit(None, "README.txt", "v3 campaign keeps working, floor untouched")

        if not ok_repo:
            failures.append("FLOOR self-test could not build the MERGE fixture repo")
        else:
            r = floor_monotone_check(target, ["a.ts", "b.ts", "c.ts"])
            if r.determined and r.ok:
                failures.append(
                    "MERGE: a floor resurrecting a wider historical value must FAIL — the "
                    "exact M0-T16 shape (D-95) — evaluated one commit AFTER the merge with "
                    "nothing further done, which is what this fixture actually checks"
                )
            if not (r.determined and not r.ok and r.violations):
                failures.append("MERGE: expected a determined, non-ok result naming the violated commit")

            # ── CASE 7 — RECOVERY. Shrinking back to ⊆ everything before it clears the
            # check — proves this is CLEARABLE, not the D-39-part-2 permanently-red shape. ─
            checks += 1
            ok_recover = _commit(["a.ts", "b.ts"], None, "v4 recovery: shrink back to \u2286 v1")
            if not ok_recover:
                failures.append("FLOOR self-test could not extend the MERGE repo with a recovery commit")
            else:
                r2 = floor_monotone_check(target, ["a.ts", "b.ts"])
                if not (r2.determined and r2.ok):
                    failures.append(
                        "RECOVERY: shrinking back to \u2286 every historical value must PASS "
                        f"even though history contains a growth step — got {r2.reason}"
                    )

        # ── CASE 8 — HAND-WIDENED, UNCOMMITTED. Must FAIL before it ever lands. ──────────
        checks += 1
        target = _git_fixture_repo(tmp / "dirty", [["a.ts", "b.ts"]], filename="entrypoint_guard_floor.json")
        if target is None:
            failures.append("FLOOR self-test could not build the DIRTY fixture repo")
        else:
            r = floor_monotone_check(target, ["a.ts", "b.ts", "z.ts"])
            if r.ok:
                failures.append("DIRTY: an uncommitted widening must FAIL before it is committed")

        # ── CASE 9 — CURRENT SIDE ABSENT. Must be UNDETERMINED, never a vacuous pass. ────
        checks += 1
        r = floor_monotone_check(tmp / "nonexistent" / "entrypoint_guard_floor.json", None)
        if r.determined or r.ok:
            failures.append("ABSENT-CURRENT: a None current side must be UNDETERMINED and FATAL (D-89)")

        # ── CASE 10 — sync_floor NEVER WIDENS (D-96). ─────────────────────────────────────
        checks += 1
        floor_file = tmp / "sync" / "entrypoint_guard_floor.json"
        floor_file.parent.mkdir(parents=True, exist_ok=True)
        write_floor(floor_file, ["a.ts", "b.ts"], note="seed")
        rc = sync_floor(floor_file, ["a.ts", "b.ts", "z.ts"], source="self-test")
        if rc == 0:
            failures.append("SYNC-FLOOR: a target carrying a file the floor lacks must be REFUSED")
        after = read_current_side(floor_file)
        if after != ["a.ts", "b.ts"]:
            failures.append("SYNC-FLOOR: a refused sync must leave the floor UNCHANGED on disk")

        # ── CASE 11 — sync_floor DOES shrink, and DOES create on first run. ──────────────
        checks += 1
        rc = sync_floor(floor_file, ["a.ts"], source="self-test")
        if rc != 0 or read_current_side(floor_file) != ["a.ts"]:
            failures.append("SYNC-FLOOR: a genuine subset target must be written")
        fresh = tmp / "sync" / "fresh_floor.json"
        rc = sync_floor(fresh, ["a.ts", "b.ts"], source="self-test")
        if rc != 0 or read_current_side(fresh) != ["a.ts", "b.ts"]:
            failures.append("SYNC-FLOOR: first-time creation (no prior floor) must succeed and write the target")

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

    # ── THE FLOOR's OWN DETECTOR, proven in both directions (rulings D-95, D-96) ──────────
    floor_failures, floor_checks = run_floor_self_test()
    failures.extend(floor_failures)

    if failures:
        print("check_entrypoint_guard_ratchet: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"check_entrypoint_guard_ratchet: SELF-TEST PASS ({n_pass} pass fixture(s) silent, "
        f"{n_fail} fail fixture(s) caught, {len(declared)}/{len(declared)} guard idioms "
        f"exercised, {floor_checks} floor case(s) proven in both directions)."
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
        "--sync-floor",
        action="store_true",
        help=(
            "Sync entrypoint_guard_floor.json to the currently on-disk allowlist "
            "(shrink-only; creates the floor on first run). Ruling D-95."
        ),
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

    if args.sync_floor:
        target = read_current_side(ALLOWLIST_PATH)
        if target is None:
            print(
                "check_entrypoint_guard_ratchet: REFUSING to sync floor — the on-disk "
                f"allowlist ({ALLOWLIST_PATH.name}) could not be read.",
                file=sys.stderr,
            )
            return 1
        return sync_floor(FLOOR_PATH, target, source=f"on-disk {ALLOWLIST_PATH.name}")

    if args.regenerate:
        return regenerate(root, scan_roots, ALLOWLIST_PATH)

    allowlist = load_allowlist(ALLOWLIST_PATH)
    allowed = set(allowlist.get("files", []))
    baseline = set(allowlist.get("baseline_files") or load_baseline())
    # THE CURRENT SIDE'S ANCHOR (D-89) — see `read_current_side`, which is where "absent" is
    # kept distinct from "empty". The first draft of this anchor collapsed the two and a DELETED
    # allowlist still passed; it was found by deleting the file end to end, not by reading it.
    current_side = read_current_side(ALLOWLIST_PATH)
    floor_disk = read_current_side(FLOOR_PATH)

    # ── ASSERTION (i): a NEW name in the allowlist. Static-baseline membership. ──────────────
    hand_added = sorted(allowed - baseline)

    # ── ASSERTION (ii): THE FLOOR (ruling D-95, superseding D-87 part 3). Current allowlist
    # ⊆ floor, AND floor ⊆ every value its own committed history has ever held. (i) alone
    # cannot see a repaired file returning — it is still a member of the settled baseline.
    # See THE FLOOR section above.
    floor_contain = floor_containment(current_side, floor_disk)
    floor_mono = floor_monotone_check(FLOOR_PATH, floor_disk)
    history_growth = pawl_history(ALLOWLIST_PATH)
    floor_history_growth = pawl_history(FLOOR_PATH)

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
        "floor": {
            "path": FLOOR_PATH.name,
            "exists": floor_disk is not None,
            "count": len(floor_disk) if floor_disk is not None else None,
            "containment": {
                "determined": floor_contain.determined,
                "pass": floor_contain.ok,
                "added_beyond_floor": floor_contain.added,
                "reason": floor_contain.reason,
            },
            "monotonicity": {
                "determined": floor_mono.determined,
                "pass": floor_mono.ok,
                "violations": floor_mono.violations,
                "reason": floor_mono.reason,
            },
        },
        "committed_history_growth_steps": history_growth,
        "floor_history_growth_steps": floor_history_growth,
        "unparsed_files": unparsed,
        "out_of_scope_suffix_observations": extended,
    }

    # An unparsed file is UNKNOWN, not clean, and is therefore blocking. See §N.8: a detector
    # that cannot answer must not return the answer that happens to look green.
    fail = (
        bool(new)
        or bool(hand_added)
        or not floor_contain.ok
        or not floor_mono.ok
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
    if floor_contain.determined and floor_contain.ok and floor_mono.determined and floor_mono.ok:
        print(
            f"  floor: allowlist ({len(current_side or [])}) \u2286 floor "
            f"({len(floor_disk or [])}), and the floor \u2286 every value its own committed "
            "history has ever held — neither grew."
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

    if not floor_contain.ok:
        if not floor_contain.determined:
            print(
                "check_entrypoint_guard_ratchet: THE FLOOR CONTAINMENT CHECK COULD NOT RUN — "
                f"{floor_contain.reason} FAIL.",
                file=sys.stderr,
            )
        else:
            print(
                f"check_entrypoint_guard_ratchet: {len(floor_contain.added)} allowlist "
                "entry/entries are NOT covered by the FLOOR "
                f"({FLOOR_PATH.name}, {len(floor_disk or [])} entries). THE ALLOWLIST MAY "
                "ONLY SHRINK RELATIVE TO THE FLOOR (D-67 part 4, D-71 part 7, D-95). Every "
                "one of these is either NEW or a REPAIRED file returning; putting it back "
                "re-opens a hole that was closed, and the static-baseline check cannot see "
                "it because a repaired file remains a member of the settled baseline "
                "forever. THIS IS RED AND STAYS RED until it is paid back — re-guard the "
                "file(s) below, or bring a new explicitly-ruled baseline to ADHIKĀRIN (D-96: "
                "no exemption field exists for this). FAIL.",
                file=sys.stderr,
            )
            for f in floor_contain.added:
                print(f"  + {f}", file=sys.stderr)

    if not floor_mono.ok:
        if not floor_mono.determined:
            print(
                "check_entrypoint_guard_ratchet: THE FLOOR'S OWN MONOTONICITY CHECK COULD "
                f"NOT RUN — {floor_mono.reason} FAIL.",
                file=sys.stderr,
            )
        else:
            print(
                f"check_entrypoint_guard_ratchet: the floor is WIDER than "
                f"{len(floor_mono.violations)} commit(s) in its own committed history — it "
                "was hand-widened and never fully paid back. THE FLOOR MAY ONLY SHRINK "
                "(D-95, D-96). FAIL.",
                file=sys.stderr,
            )
            for v in floor_mono.violations[:10]:
                print(f"  ! {v['commit'][:9]} does not cover {', '.join(v['added'])}", file=sys.stderr)

    if history_growth:
        print(
            f"  NOTE — the allowlist's committed history contains {len(history_growth)} step(s) "
            "in which it GREW. Reported, NOT gated: a growth already in history stays in "
            "history, so gating on it would be permanently red from the next commit onward "
            "(D-39 part 2). Bring it to ADHIKĀRIN:"
        )
        for g in history_growth:
            print(f"    ! {g['commit'][:9]} added {', '.join(g['added'])}")

    if floor_history_growth:
        print(
            f"  NOTE — the floor's OWN committed history contains {len(floor_history_growth)} "
            "single-step growth event(s) (the gating check above walks FULL history, not "
            "just adjacent steps). Diagnostic only:"
        )
        for g in floor_history_growth:
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
