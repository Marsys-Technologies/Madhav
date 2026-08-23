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
  2. **NOTHING IS EVER ADDED — checked on EVERY run, not only at regeneration.** The allowlist
     must be a SUBSET of M0-T64's settled 76-file baseline
     (`00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json` → `ratchet_allowlist.files`, proven
     identical against ADHIKĀRIN's independent derivation, ruling D-71 part 3). A hand-added
     entry — even one naming a genuinely unguarded file — fails the run. The ratchet cannot be
     loosened by editing the list it gates on.
  3. **SHRINKAGE IS VISIBLE.** The allowlist records `baseline_count`, its own `count`, and the
     itemised `paid_down` set (baseline − current). `--json` reports all three.

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

Exit codes: 0 = pass · 1 = a NEW (non-allowlisted) violation, or `--strict` with any residual.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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

    paid_down = sorted(baseline - set(measured))
    payload = {
        "schema_version": "1.0",
        "$comment": (
            "Allowlist for check_entrypoint_guard_ratchet.py. Ruling D-67 part 4: an itemised "
            "allowlist of exactly today's population, GENERATED FROM THE MEASUREMENT AND NEVER "
            "HAND-TYPED, with its count recorded so shrinkage is visible. PAY-DOWN ONLY: a file "
            "leaves this list when repaired; NOTHING IS EVER ADDED. Every run of the guard — not "
            "only --regenerate — asserts that `files` is a SUBSET of `baseline_files`, so a "
            "hand-added entry fails the build rather than widening the hole. Regenerate with "
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
# Self-test
# ═══════════════════════════════════════════════════════════════════════════════════════════

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

    if failures:
        print("check_entrypoint_guard_ratchet: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    print(
        f"check_entrypoint_guard_ratchet: SELF-TEST PASS ({n_pass} pass fixture(s) silent, "
        f"{n_fail} fail fixture(s) caught, {len(declared)}/{len(declared)} guard idioms exercised)."
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

    # ── THE "NOTHING IS EVER ADDED" DETECTOR, run on EVERY invocation ────────────────────────
    hand_added = sorted(allowed - baseline)

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
        "unparsed_files": unparsed,
        "out_of_scope_suffix_observations": extended,
    }

    # An unparsed file is UNKNOWN, not clean, and is therefore blocking. See §N.8: a detector
    # that cannot answer must not return the answer that happens to look green.
    fail = (
        bool(new)
        or bool(hand_added)
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
