#!/usr/bin/env python3
"""check_reconciliation_cadence.py — PARIŚODHANA Phase C2, the standing reconciliation cadence.

Why this exists
----------------
PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md §0 documents a confirmed recurring drift class,
"ships-but-register-never-flips": a fix lands in code and is verified live, but the prose
register's Status column is never updated, so downstream machinery (the planner's completeness
receipt, a future audit, a human reader) keeps treating a shipped capability as an open gap — or,
the mirror-image failure, a register gets annotated ALREADY-FIXED while the code that decides
what's citable never learns about it. POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md's own
standing note (§ "Standing note (recurring drift class)") names three confirmed prior instances
(CR-56, CR-54/CR-59) and recommends exactly this: "a lightweight periodic reconciliation pass —
grep every `known_gap: 'CR-N'` citation in `registry_data.ts` against the CR's live disposition."
This script IS that pass, generalized to every register this repo keeps in a similar shape, plus
two invariants the recommendation didn't anticipate: cr_status.ts is maintained as TWO sibling
copies (`platform/src/lib/vidhi/cr_status.ts` and `platform-mcp/src/resources/vidhi/cr_status.ts`,
the latter being what the deployed MCP server actually imports at runtime per
`platform-mcp/src/lib/completeness_receipt.ts`), and `registry_data.ts` is maintained the same way
— if the two copies disagree, the existing `registry_completeness.test.ts` (which only imports the
`platform` copy) cannot see it.

What this script checks (read-only against every source it scans)
-------------------------------------------------------------------
1. STATIC reconciliation (no network, always runs, safe for any machine):
   a. Parses `cr_status.ts` (both copies) for its three exported allowlists: OPEN_CRS, LOGGED_CRS,
      CLOSED_CRS.
   b. Parses `registry_data.ts` (both copies) for every `known_gap: 'CR-N'` citation.
   c. Parses the prose registers' `| ID | ... | Status |` (or `Disposition`) tables — currently
      `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md` and `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` —
      plus a coarser prose scan of `ELEVATION_REGISTER_v1_0.md`'s `**EL-nn ·` blocks (which do not
      carry a structured Status column; see `classify_elevation_block` for the honest limitation).
   d. Classifies each register row's status text and cross-references it against the code-side
      allowlists, reporting six divergence classes (`DivergenceKind` below) — the headline one
      being `REGISTER_NOT_FLIPPED`: exactly the "ships-but-register-never-flips" class named above.
   e. Compares the two `cr_status.ts` copies and the two `registry_data.ts` copies against each
      other directly (`DUAL_COPY_DRIFT`) — a check the campaign's own artifacts did not anticipate
      needing, found by this script's author while building it (see PR description for the live
      finding: the two `cr_status.ts` copies have already diverged on CR-24/CR-67/CR-69).
2. LIVE reconciliation (`--live`, opt-in, requires network + `MCP_CANARY_KEY`): for register rows
   this pass flags as divergent (or, with `--live-all-open`, every row still classified `open`),
   attempts to extract a concrete `` `tool_name(arg=value, ...)` `` call from the row's own cited
   evidence text and replays it against the live MCP server (same JSON-RPC-over-HTTP transport
   `evals/r5-w4-full-battery/battery_runner.ts` uses), then applies a best-effort, clearly-labeled
   HEURISTIC comparison against what the row's prose says should be true (empty vs non-empty,
   "returns N rows" vs what came back). This is deliberately conservative: where no clean call can
   be extracted, or the heuristic can't form an expectation, the row is reported
   `COULD_NOT_CHECK` — never silently skipped, never guessed.

What this script is NOT
------------------------
- It does not fix anything, and it never writes to any register or source file it scans — the only
  file it writes is its own optional `--out` report.
- It is NOT part of the default CI gate (`ci.yml`). `--live` performs real network calls against
  production and needs a live secret (`MCP_CANARY_KEY`) — a different risk profile than a static
  lint, so this script is standalone and manually/scheduled-invokable only. See
  `.github/workflows/reconciliation-cadence.yml` (opt-in `workflow_dispatch` + optional `schedule`,
  static-only unless the secret is configured).
- The static pass's table parser is a regex/line scanner, not a Markdown AST — it recognizes the
  house style actually used in these three files (a header row containing an `ID` column and a
  `Status`/`Disposition` column, immediately followed by a `|---|` separator row). A register that
  uses a different shape will simply not be found; add its path to `--register` explicitly and this
  script will attempt it with the same generic parser before falling back to reporting 0 rows.

Modes
-----
  --self-test   Run the bundled fixtures under `reconciliation_cadence_fixtures/`. Exit 0 iff the
                parser + classifier + cross-reference logic reproduces the fixture's known,
                hand-verified divergence set exactly. DB-free, repo-free, network-free.
  (default)     Run the static pass against the live repo tree.
  --live        Also attempt the live MCP probes described above. Requires `MCP_CANARY_URL`
                (defaults to the same prod URL `battery_runner.ts` uses) and `MCP_CANARY_KEY`
                (no default — must be set, or the script exits 2 rather than silently skipping).
  --live-all-open   With --live, probe every `open`-classified register row with an extractable
                call, not just rows already flagged as a static divergence.
  --json        Emit a single machine-readable JSON document instead of the human-readable report.
  --out PATH    Also write the report (same content as stdout) to PATH.

Exit codes
----------
  0  clean — no divergence found (or self-test pass)
  1  divergence(s) found (or self-test fail)
  2  invocation / config error (e.g. --live without MCP_CANARY_KEY set)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # platform/scripts/governance -> repo root
FIXTURE_DIR = SCRIPT_DIR / "reconciliation_cadence_fixtures"

CR_STATUS_PATHS = [
    "platform/src/lib/vidhi/cr_status.ts",
    "platform-mcp/src/resources/vidhi/cr_status.ts",
]
REGISTRY_DATA_PATHS = [
    "platform/src/lib/vidhi/registry_data.ts",
    "platform-mcp/src/resources/vidhi/registry_data.ts",
]
DEFAULT_TABLE_REGISTERS = [
    "00_ARCHITECTURE/llm_consumption_audit/POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md",
    "00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md",
]
ELEVATION_REGISTER_PATH = "00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md"

DEFAULT_MCP_URL = "https://amjis-mcp-qm256lasva-el.a.run.app/mcp"
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

Disposition = str  # 'open' | 'closed' | 'not_reproducible' | 'unknown'


@dataclass(frozen=True)
class RegisterRow:
    item_id: str
    file: str
    line: int
    status_raw: str
    disposition: Disposition


@dataclass(frozen=True)
class CrStatusFile:
    file: str
    open_crs: Set[str]
    logged_crs: Set[str]
    closed_crs: Set[str]
    duplicates: Set[str]  # ids appearing in >1 of the three lists (self-contradiction)


@dataclass(frozen=True)
class KnownGapCitation:
    file: str
    line: int
    primitive_id: str
    cr_id: str


@dataclass
class Divergence:
    kind: str
    item_id: str
    severity: str  # CRIT | HIGH | MED
    detail: str
    sources: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# cr_status.ts parsing
# ---------------------------------------------------------------------------

_ARRAY_BLOCK_RE = re.compile(
    r"export const (OPEN_CRS|LOGGED_CRS|CLOSED_CRS)\s*=\s*\[(?P<body>.*?)\]\s*as const;",
    re.DOTALL,
)
_QUOTED_ID_RE = re.compile(r"'([A-Za-z][A-Za-z0-9]*-[A-Za-z0-9]+)'")


def _strip_ts_comments_but_keep_strings(body: str) -> str:
    """Remove `// ...` line comments (which may themselves reference CR-ids in prose, e.g.
    "CR-54 and CR-59 were in this list") without touching quoted string literals, so only real
    array *entries* are left for `_QUOTED_ID_RE` to find. A line-oriented strip is sufficient here
    — this file has no multi-line `/* */` comments and no `//` occurring inside a string literal."""
    out_lines = []
    for line in body.splitlines():
        idx = line.find("//")
        out_lines.append(line[:idx] if idx != -1 else line)
    return "\n".join(out_lines)


def parse_cr_status_ts(path: Path, rel: str) -> Optional[CrStatusFile]:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    lists: Dict[str, Set[str]] = {"OPEN_CRS": set(), "LOGGED_CRS": set(), "CLOSED_CRS": set()}
    for m in _ARRAY_BLOCK_RE.finditer(text):
        name = m.group(1)
        body = _strip_ts_comments_but_keep_strings(m.group("body"))
        lists[name] |= set(_QUOTED_ID_RE.findall(body))

    all_ids = list(lists["OPEN_CRS"]) + list(lists["LOGGED_CRS"]) + list(lists["CLOSED_CRS"])
    seen: Set[str] = set()
    dupes: Set[str] = set()
    for i in all_ids:
        if i in seen:
            dupes.add(i)
        seen.add(i)

    return CrStatusFile(
        file=rel,
        open_crs=lists["OPEN_CRS"],
        logged_crs=lists["LOGGED_CRS"],
        closed_crs=lists["CLOSED_CRS"],
        duplicates=dupes,
    )


# ---------------------------------------------------------------------------
# registry_data.ts known_gap parsing
# ---------------------------------------------------------------------------

_PRIMITIVE_ID_RE = re.compile(r"primitive_id:\s*'([^']+)'")
_KNOWN_GAP_RE = re.compile(r"known_gap:\s*(null|'([^']+)')")


def parse_known_gap_citations(path: Path, rel: str) -> List[KnownGapCitation]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    # Split into per-primitive blocks on primitive_id occurrences so a known_gap always resolves
    # to the primitive it actually belongs to (not merely "the nearest one in the file").
    markers = [(m.start(), m.group(1)) for m in _PRIMITIVE_ID_RE.finditer(text)]
    citations: List[KnownGapCitation] = []
    for idx, (start, primitive_id) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
        block = text[start:end]
        gm = _KNOWN_GAP_RE.search(block)
        if not gm:
            continue
        cr_id = gm.group(2)
        if not cr_id:
            continue
        line = text.count("\n", 0, start + gm.start()) + 1
        citations.append(KnownGapCitation(file=rel, line=line, primitive_id=primitive_id, cr_id=cr_id))
    return citations


# ---------------------------------------------------------------------------
# Status-text classification
# ---------------------------------------------------------------------------

# Rightmost-keyword-wins: these registers append PARIŚODHANA/wave annotations to the END of a
# Status cell rather than replacing the leading token (e.g. "OPEN [... Disposition: ALREADY-FIXED
# ...]"). The row's CURRENT disposition is whatever closure/openness keyword occurs LAST in the
# cell, not the first — verified against real rows (CR-1, CR-5, CR-73) during this script's
# authoring; see PR description for the worked examples.
_STATUS_KEYWORD_RE = re.compile(
    r"\b(?P<not_repro>NOT-REPRODUCIBLE)\b"
    r"|\b(?P<closed>CLOSED_WITH_EVIDENCE|CLOSED|ALREADY-FIXED|STALE-CORRECTED|FIXED|ADDRESSED|RESOLVED)\b"
    r"|\b(?P<open>LIVE-OPEN|OPEN|PARKED-HONEST|PARKED|DEFERRED|PENDING|VERIFIED-STILL-OPEN)\b"
)


def classify_status(text: str) -> Disposition:
    last_kind: Optional[str] = None
    for m in _STATUS_KEYWORD_RE.finditer(text):
        if m.group("not_repro"):
            last_kind = "not_reproducible"
        elif m.group("closed"):
            last_kind = "closed"
        elif m.group("open"):
            last_kind = "open"
    return last_kind or "unknown"


# ---------------------------------------------------------------------------
# Generic `| ID | ... | Status |` table parser
# ---------------------------------------------------------------------------

_ID_HEADER_RE = re.compile(r"^\s*id\s*$", re.IGNORECASE)
_STATUS_HEADER_RE = re.compile(r"^\s*(status|disposition)\s*$", re.IGNORECASE)
_SEPARATOR_ROW_RE = re.compile(r"^\|[\s:|-]+\|?\s*$")
_ITEM_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9]+[a-z]?$")


def _split_row(line: str) -> List[str]:
    # Rows look like "| a | b | c |" (or occasionally missing the trailing "|"). Strip one
    # leading/trailing "|" if present, then split on "|" — cells may themselves contain escaped
    # pipes as literal backslash-pipe in this house style's tables, but none of the three target
    # registers use that escape, so a plain split is sufficient and matches naming_lint.py's own
    # "regex scanner, not a Markdown AST" honesty precedent.
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def parse_pipe_table_registers(path: Path, rel: str) -> List[RegisterRow]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows: List[RegisterRow] = []
    i = 0
    n = len(lines)
    while i < n - 1:
        header_line = lines[i]
        sep_line = lines[i + 1]
        if header_line.lstrip().startswith("|") and _SEPARATOR_ROW_RE.match(sep_line.strip()):
            headers = [h.strip("* ") for h in _split_row(header_line)]
            id_idx = next((j for j, h in enumerate(headers) if _ID_HEADER_RE.match(h)), None)
            status_idx = next((j for j, h in enumerate(headers) if _STATUS_HEADER_RE.match(h)), None)
            if id_idx is not None and status_idx is not None:
                j = i + 2
                while j < n and lines[j].lstrip().startswith("|"):
                    cells = _split_row(lines[j])
                    if len(cells) > max(id_idx, status_idx):
                        raw_id = cells[id_idx].strip("* ")
                        if _ITEM_ID_RE.match(raw_id):
                            status_raw = cells[status_idx]
                            rows.append(
                                RegisterRow(
                                    item_id=raw_id,
                                    file=rel,
                                    line=j + 1,
                                    status_raw=status_raw,
                                    disposition=classify_status(status_raw),
                                )
                            )
                    j += 1
                i = j
                continue
        i += 1
    return rows


# ---------------------------------------------------------------------------
# ELEVATION_REGISTER_v1_0.md — coarse prose-block parser (no structured Status column)
# ---------------------------------------------------------------------------

_EL_BLOCK_HEADER_RE = re.compile(r"\*\*(EL-\d+)\s*[·.]")


def parse_elevation_register(path: Path, rel: str) -> List[RegisterRow]:
    """EL-nn items are free-form prose blocks, not table rows (confirmed: this file has zero
    `| ID | ... | Status |` tables). Per the file's own reading guide, "Status: OPEN unless
    stated" — so this parser's honest limitation is: it can positively confirm a CLOSED-class
    keyword appearing inside an item's block (closure IS structured enough to grep for), but a
    block with no such keyword is reported `open` on the reading guide's own stated default,
    which is a weaker guarantee than the pipe-table parser's — a closure phrased without any of
    the recognized keywords would be missed. This is disclosed, not silently assumed."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = [(m.start(), m.group(1)) for m in _EL_BLOCK_HEADER_RE.finditer(text)]
    rows: List[RegisterRow] = []
    for idx, (start, el_id) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
        block = text[start:end]
        line = text.count("\n", 0, start) + 1
        disposition = classify_status(block)
        if disposition == "unknown":
            disposition = "open"  # reading guide's stated default
        rows.append(
            RegisterRow(
                item_id=el_id,
                file=rel,
                line=line,
                status_raw=block[:200].replace("\n", " "),
                disposition=disposition,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Cross-reference — the actual reconciliation logic
# ---------------------------------------------------------------------------


def _index_rows_by_id(rows: Sequence[RegisterRow]) -> Dict[str, List[RegisterRow]]:
    out: Dict[str, List[RegisterRow]] = {}
    for r in rows:
        out.setdefault(r.item_id, []).append(r)
    return out


def cross_reference(
    cr_status_files: Sequence[CrStatusFile],
    known_gaps: Sequence[KnownGapCitation],
    register_rows: Sequence[RegisterRow],
) -> List[Divergence]:
    divergences: List[Divergence] = []
    by_id = _index_rows_by_id(register_rows)

    # 1. Self-contradiction within a single cr_status.ts copy.
    for cf in cr_status_files:
        for dup_id in sorted(cf.duplicates):
            in_lists = []
            if dup_id in cf.open_crs:
                in_lists.append("OPEN_CRS")
            if dup_id in cf.logged_crs:
                in_lists.append("LOGGED_CRS")
            if dup_id in cf.closed_crs:
                in_lists.append("CLOSED_CRS")
            divergences.append(
                Divergence(
                    kind="SELF_CONTRADICTION",
                    item_id=dup_id,
                    severity="HIGH",
                    detail=f"{dup_id} appears in more than one allowlist in the same file: {', '.join(in_lists)}.",
                    sources=[cf.file],
                )
            )

    # 2. Dual-copy drift: the N>=2 cr_status.ts copies disagree on an id's classification.
    if len(cr_status_files) >= 2:
        all_ids: Set[str] = set()
        for cf in cr_status_files:
            all_ids |= cf.open_crs | cf.logged_crs | cf.closed_crs
        for item_id in sorted(all_ids):

            def _classify(cf: CrStatusFile, i: str = item_id) -> str:
                if i in cf.closed_crs:
                    return "CLOSED"
                if i in cf.open_crs:
                    return "OPEN"
                if i in cf.logged_crs:
                    return "LOGGED"
                return "ABSENT"

            classes = {cf.file: _classify(cf) for cf in cr_status_files}
            if len(set(classes.values())) > 1:
                divergences.append(
                    Divergence(
                        kind="DUAL_COPY_DRIFT",
                        item_id=item_id,
                        severity="HIGH",
                        detail=(
                            f"{item_id} is classified differently across the cr_status.ts copies: "
                            + "; ".join(f"{f}={c}" for f, c in classes.items())
                            + ". These copies are supposed to be kept identical (platform-mcp's is "
                            "what the deployed MCP server actually imports, per completeness_receipt.ts)."
                        ),
                        sources=list(classes.keys()),
                    )
                )

    # 3. Known-gap citations vs the allowlists (defense-in-depth for registry_completeness.test.ts,
    #    which only ever checks the `platform` copy — this also covers the platform-mcp copy).
    for kg in known_gaps:
        # known_gap citations live in registry_data.ts; find the SIBLING cr_status.ts in the same
        # tree (platform/... or platform-mcp/...) to judge citability against the copy that
        # actually ships alongside this known_gap citation.
        sibling = _sibling_cr_status(kg.file, cr_status_files)
        if sibling is None:
            continue
        if kg.cr_id in sibling.closed_crs:
            divergences.append(
                Divergence(
                    kind="KNOWN_GAP_CITES_CLOSED",
                    item_id=kg.cr_id,
                    severity="CRIT",
                    detail=(
                        f"registry_data.ts primitive '{kg.primitive_id}' cites known_gap: '{kg.cr_id}', "
                        f"but {sibling.file} lists {kg.cr_id} in CLOSED_CRS — forbidden per "
                        "registry_completeness.test.ts's own invariant."
                    ),
                    sources=[kg.file, sibling.file],
                )
            )
        elif kg.cr_id not in (sibling.open_crs | sibling.logged_crs):
            divergences.append(
                Divergence(
                    kind="KNOWN_GAP_NOT_CITABLE",
                    item_id=kg.cr_id,
                    severity="MED",
                    detail=(
                        f"registry_data.ts primitive '{kg.primitive_id}' cites known_gap: '{kg.cr_id}', "
                        f"which is not present in {sibling.file}'s OPEN_CRS or LOGGED_CRS at all."
                    ),
                    sources=[kg.file, sibling.file],
                )
            )

    # 4. The headline check: CLOSED_CRS says fixed, but the register row was never flipped.
    all_closed: Dict[str, List[str]] = {}
    all_open_or_logged: Dict[str, List[str]] = {}
    for cf in cr_status_files:
        for i in cf.closed_crs:
            all_closed.setdefault(i, []).append(cf.file)
        for i in cf.open_crs | cf.logged_crs:
            all_open_or_logged.setdefault(i, []).append(cf.file)

    for item_id, code_files in sorted(all_closed.items()):
        for row in by_id.get(item_id, []):
            if row.disposition == "open":
                divergences.append(
                    Divergence(
                        kind="REGISTER_NOT_FLIPPED",
                        item_id=item_id,
                        severity="HIGH",
                        detail=(
                            f"{', '.join(code_files)} lists {item_id} in CLOSED_CRS, but "
                            f"{row.file}:{row.line} still classifies its Status cell as OPEN "
                            f"(raw: {row.status_raw[:220]!r}). This is the 'ships-but-register-"
                            "never-flips' drift class named in POST_REMEDIATION_CONSUMPTION_"
                            "REGISTER_v1_0.md's standing note."
                        ),
                        sources=[row.file] + code_files,
                    )
                )

    # 5. The mirror-image: a register row now reads closed/already-fixed, but the code side still
    #    treats the id as an open/logged (citable) known_gap.
    for item_id, code_files in sorted(all_open_or_logged.items()):
        for row in by_id.get(item_id, []):
            if row.disposition == "closed":
                divergences.append(
                    Divergence(
                        kind="CODE_NOT_UPDATED",
                        item_id=item_id,
                        severity="MED",
                        detail=(
                            f"{row.file}:{row.line} classifies {item_id} as CLOSED/ALREADY-FIXED "
                            f"(raw: {row.status_raw[:220]!r}), but {', '.join(code_files)} still "
                            f"lists it in OPEN_CRS/LOGGED_CRS — a primitive could still cite it as "
                            "a live known_gap."
                        ),
                        sources=[row.file] + code_files,
                    )
                )

    return divergences


def _sibling_cr_status(registry_data_rel: str, cr_status_files: Sequence[CrStatusFile]) -> Optional[CrStatusFile]:
    tree = "platform-mcp" if registry_data_rel.startswith("platform-mcp") else "platform"
    for cf in cr_status_files:
        if cf.file.startswith(tree):
            return cf
    return None


# ---------------------------------------------------------------------------
# Live MCP probe (opt-in) — same JSON-RPC-over-HTTP transport as
# evals/r5-w4-full-battery/battery_runner.ts, ported to stdlib Python so this script has no new
# runtime dependency.
# ---------------------------------------------------------------------------

_TOOL_CALL_RE = re.compile(r"`(?P<tool>[a-z][a-z0-9_]*)\((?P<args>[^()`]*)\)`")
_KNOWN_TOOL_VERB_RE = re.compile(r"(_get|_query|_read|query_|get_|assess_|judgment_query|dossier)")


def extract_tool_calls(text: str) -> List[Tuple[str, Dict[str, str]]]:
    """Best-effort extraction of `` `tool_name(k=v, k2=v2)` `` snippets from register prose. Only
    returns calls whose tool name looks like a real MCP tool identifier (contains a recognized
    verb/suffix) — this filters out incidental backtick-quoted code identifiers (function names,
    file paths) that are NOT callable tools, at the cost of a real but bounded false-negative rate
    on any tool-name shape not in `_KNOWN_TOOL_VERB_RE` (disclosed, not hidden)."""
    calls: List[Tuple[str, Dict[str, str]]] = []
    for m in _TOOL_CALL_RE.finditer(text):
        tool = m.group("tool")
        if not _KNOWN_TOOL_VERB_RE.search(tool):
            continue
        args: Dict[str, str] = {}
        raw_args = m.group("args").strip()
        if raw_args:
            for part in raw_args.split(","):
                part = part.strip()
                if "=" not in part:
                    continue
                k, v = part.split("=", 1)
                args[k.strip()] = v.strip().strip("'\"")
        calls.append((tool, args))
    return calls


def mcp_call(url: str, key: str, tool: str, args: Dict[str, str], timeout: float = 30.0) -> Dict:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": args},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": str(e), "raw": None}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "status": 0, "error": str(e), "raw": None}

    data_line = next((ln for ln in body_text.splitlines() if ln.startswith("data:")), None)
    json_text = data_line[len("data:") :].strip() if data_line else body_text
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        return {"ok": status < 400, "status": status, "error": "unparseable body", "raw": body_text[:500]}

    result = parsed.get("result") if isinstance(parsed, dict) else None
    rpc_error = parsed.get("error") if isinstance(parsed, dict) else None
    content = None
    if isinstance(result, dict):
        struct = result.get("structuredContent")
        if isinstance(struct, dict) and "object" in struct:
            content = struct["object"]
        else:
            texts = result.get("content")
            if isinstance(texts, list) and texts and isinstance(texts[0], dict):
                text_val = texts[0].get("text")
                if isinstance(text_val, str) and not text_val.startswith("[large payload"):
                    try:
                        content = json.loads(text_val)
                    except json.JSONDecodeError:
                        content = text_val
    is_error = bool(isinstance(result, dict) and result.get("isError"))
    return {
        "ok": status < 400 and rpc_error is None and not is_error,
        "status": status,
        "error": rpc_error,
        "isError": is_error,
        "content": content,
    }


_EXPECT_EMPTY_RE = re.compile(r"\b(returns?\s+(zero|0)\b|entirely empty|100% NULL|still zero|remain(?:s)? 0)", re.IGNORECASE)
_EXPECT_MIN_ROWS_RE = re.compile(r"\b(?:returns?|serves?|only)\s+(\d+)\s+(?:rows?|resonances|signals|mechanisms)", re.IGNORECASE)


def _count_hint(obj) -> Optional[int]:
    """Best-effort: find the most plausible 'row count' in a live payload — the longest list
    found anywhere at the top two levels of the structure. Heuristic, documented as such."""
    best: Optional[int] = None

    def _walk(o, depth: int) -> None:
        nonlocal best
        if depth > 2:
            return
        if isinstance(o, list):
            best = len(o) if best is None else max(best, len(o))
        elif isinstance(o, dict):
            for v in o.values():
                _walk(v, depth + 1)

    _walk(obj, 0)
    return best


def heuristic_compare(evidence_text: str, live_content) -> str:
    if _EXPECT_EMPTY_RE.search(evidence_text):
        n = _count_hint(live_content)
        if n is not None and n > 0:
            return f"EXPECTATION CONTRADICTED (heuristic) — row's evidence implies empty/zero, live payload's largest array has {n} entries."
        return "CONSISTENT (heuristic) — row's evidence implies empty/zero; live payload shows no populated array at the depth this heuristic inspects."
    m = _EXPECT_MIN_ROWS_RE.search(evidence_text)
    if m:
        expected = int(m.group(1))
        n = _count_hint(live_content)
        if n is not None and n == 0 and expected > 0:
            return f"EXPECTATION CONTRADICTED (heuristic) — row's evidence implies ~{expected} rows still being the (narrow/broken) case; live payload is empty."
        return f"INCONCLUSIVE (heuristic) — row cites ~{expected} rows; live payload's largest array has {n if n is not None else 'unknown'} entries; not a strict comparison."
    return "INCONCLUSIVE (heuristic) — could not extract a comparable expectation from the row's evidence text."


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_static_pass(root: Path, extra_registers: Sequence[str]) -> Tuple[List[Divergence], List[RegisterRow], List[CrStatusFile], List[KnownGapCitation]]:
    cr_status_files = [
        f for f in (parse_cr_status_ts(root / p, p) for p in CR_STATUS_PATHS) if f is not None
    ]
    known_gaps: List[KnownGapCitation] = []
    for p in REGISTRY_DATA_PATHS:
        known_gaps.extend(parse_known_gap_citations(root / p, p))

    register_rows: List[RegisterRow] = []
    for p in list(DEFAULT_TABLE_REGISTERS) + list(extra_registers):
        register_rows.extend(parse_pipe_table_registers(root / p, p))
    register_rows.extend(parse_elevation_register(root / ELEVATION_REGISTER_PATH, ELEVATION_REGISTER_PATH))

    divergences = cross_reference(cr_status_files, known_gaps, register_rows)
    return divergences, register_rows, cr_status_files, known_gaps


def run_live_pass(
    divergences: Sequence[Divergence],
    register_rows: Sequence[RegisterRow],
    probe_all_open: bool,
    mcp_url: str,
    mcp_key: str,
) -> List[Dict]:
    candidates: Dict[str, RegisterRow] = {}
    for d in divergences:
        for row in register_rows:
            if row.item_id == d.item_id:
                candidates[f"{row.file}:{row.line}:{row.item_id}"] = row
    if probe_all_open:
        for row in register_rows:
            if row.disposition == "open":
                candidates[f"{row.file}:{row.line}:{row.item_id}"] = row

    results: List[Dict] = []
    for key, row in sorted(candidates.items()):
        calls = extract_tool_calls(row.status_raw)
        if not calls:
            results.append(
                {
                    "item_id": row.item_id,
                    "file": row.file,
                    "line": row.line,
                    "verdict": "COULD_NOT_CHECK",
                    "reason": "no extractable `tool_name(args)` call in this row's Status/evidence text",
                }
            )
            continue
        tool, args = calls[0]
        call_args = dict(args)
        call_args.setdefault("chart_id", NATIVE_CHART_ID)
        live = mcp_call(mcp_url, mcp_key, tool, call_args)
        if not live.get("ok"):
            results.append(
                {
                    "item_id": row.item_id,
                    "file": row.file,
                    "line": row.line,
                    "tool": tool,
                    "args": call_args,
                    "verdict": "LIVE_PROBE_FAILED",
                    "detail": {"status": live.get("status"), "error": live.get("error")},
                }
            )
            continue
        comparison = heuristic_compare(row.status_raw, live.get("content"))
        results.append(
            {
                "item_id": row.item_id,
                "file": row.file,
                "line": row.line,
                "tool": tool,
                "args": call_args,
                "verdict": comparison,
            }
        )
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def render_report(
    divergences: Sequence[Divergence],
    register_rows: Sequence[RegisterRow],
    live_results: Optional[Sequence[Dict]],
) -> str:
    lines: List[str] = []
    lines.append("# Reconciliation Cadence Report")
    lines.append("")
    lines.append(f"Register rows scanned: {len(register_rows)}")
    open_count = sum(1 for r in register_rows if r.disposition == "open")
    closed_count = sum(1 for r in register_rows if r.disposition == "closed")
    lines.append(f"  - classified OPEN: {open_count}")
    lines.append(f"  - classified CLOSED/FIXED: {closed_count}")
    lines.append(f"  - classified NOT-REPRODUCIBLE/unknown: {len(register_rows) - open_count - closed_count}")
    lines.append("")
    lines.append(f"Divergences found: {len(divergences)}")
    lines.append("")
    by_kind: Dict[str, List[Divergence]] = {}
    for d in divergences:
        by_kind.setdefault(d.kind, []).append(d)
    for kind in sorted(by_kind):
        lines.append(f"## {kind} ({len(by_kind[kind])})")
        lines.append("")
        for d in by_kind[kind]:
            lines.append(f"- **{d.item_id}** [{d.severity}] — {d.detail}")
            lines.append(f"  - sources: {', '.join(d.sources)}")
        lines.append("")
    if live_results is not None:
        lines.append(f"## LIVE PROBE RESULTS ({len(live_results)})")
        lines.append("")
        for r in live_results:
            lines.append(f"- **{r['item_id']}** ({r['file']}:{r['line']}) — {r['verdict']}")
            if "tool" in r:
                lines.append(f"  - live call: `{r['tool']}({r['args']})`")
            if "detail" in r:
                lines.append(f"  - detail: {r['detail']}")
            if "reason" in r:
                lines.append(f"  - reason: {r['reason']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


def run_self_test() -> int:
    if not FIXTURE_DIR.exists():
        print("check_reconciliation_cadence: SELF-TEST — fixture dir missing", file=sys.stderr)
        return 2

    # `rel` strings deliberately mimic the real platform/ vs platform-mcp/ tree prefixes so
    # `_sibling_cr_status` (which resolves a registry_data.ts citation to its sibling cr_status.ts
    # by tree prefix) exercises the exact same path-matching logic it uses against the live repo.
    cr_status_a = parse_cr_status_ts(FIXTURE_DIR / "cr_status_a.ts", "platform/src/lib/vidhi/cr_status.ts")
    cr_status_b = parse_cr_status_ts(FIXTURE_DIR / "cr_status_b.ts", "platform-mcp/src/resources/vidhi/cr_status.ts")
    if cr_status_a is None or cr_status_b is None:
        print("check_reconciliation_cadence: SELF-TEST — fixture cr_status files unreadable", file=sys.stderr)
        return 2

    known_gaps = parse_known_gap_citations(FIXTURE_DIR / "registry_data_a.ts", "platform/src/lib/vidhi/registry_data.ts")
    register_rows = parse_pipe_table_registers(FIXTURE_DIR / "sample_register.md", "fixture/sample_register.md")

    failures: List[str] = []

    # Expected fixture facts (hand-verified, mirroring the real CR-55/CR-56/CR-73/CR-24 findings
    # this script surfaced against the live repo):
    #   FIX-1: CLOSED in both copies, register row still OPEN -> REGISTER_NOT_FLIPPED
    #   FIX-2: OPEN in copy A, CLOSED in copy B -> DUAL_COPY_DRIFT (+ possibly REGISTER_NOT_FLIPPED
    #          against whichever copy is CLOSED)
    #   FIX-3: register row CLOSED, but code copy A lists it OPEN -> CODE_NOT_UPDATED
    #   FIX-4: appears in both OPEN_CRS and CLOSED_CRS of copy A -> SELF_CONTRADICTION
    #   FIX-5: known_gap cites a CR closed in its sibling copy -> KNOWN_GAP_CITES_CLOSED
    #   FIX-6: clean row, closed everywhere, register flipped -> no divergence

    divergences = cross_reference([cr_status_a, cr_status_b], known_gaps, register_rows)
    kinds_by_id: Dict[str, Set[str]] = {}
    for d in divergences:
        kinds_by_id.setdefault(d.item_id, set()).add(d.kind)

    expected = {
        "FIX-1": {"REGISTER_NOT_FLIPPED"},
        "FIX-2": {"DUAL_COPY_DRIFT"},
        "FIX-3": {"CODE_NOT_UPDATED"},
        "FIX-4": {"SELF_CONTRADICTION"},
        "FIX-5": {"KNOWN_GAP_CITES_CLOSED"},
    }
    for item_id, expected_kinds in expected.items():
        actual_kinds = kinds_by_id.get(item_id, set())
        if not expected_kinds.issubset(actual_kinds):
            failures.append(f"{item_id}: expected kinds {expected_kinds} to be a subset of found {actual_kinds}")

    if "FIX-6" in kinds_by_id:
        failures.append(f"FIX-6: expected NO divergence, but found {kinds_by_id['FIX-6']}")

    # Classifier unit checks, isolated from the cross-reference machinery.
    classifier_cases = [
        ("OPEN", "open"),
        ("OPEN — ELEVATED", "open"),
        ("CLOSED_WITH_EVIDENCE [note]", "closed"),
        ("OPEN [ANNOTATION: ... Disposition: ALREADY-FIXED for this build.]", "closed"),
        ("OPEN → CLOSED_WITH_EVIDENCE [...]", "closed"),
        ("NOT-REPRODUCIBLE", "not_reproducible"),
        ("LIVE-OPEN", "open"),
    ]
    for text, expected_disp in classifier_cases:
        actual = classify_status(text)
        if actual != expected_disp:
            failures.append(f"classify_status({text!r}) = {actual!r}, expected {expected_disp!r}")

    # extract_tool_calls unit check.
    calls = extract_tool_calls("Live `bodha_remedies_get(chart_id=482012f1, domain=wealth)` returns 3 rows.")
    if calls != [("bodha_remedies_get", {"chart_id": "482012f1", "domain": "wealth"})]:
        failures.append(f"extract_tool_calls produced unexpected result: {calls}")

    if failures:
        print("check_reconciliation_cadence: SELF-TEST FAILED", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(
        f"check_reconciliation_cadence: SELF-TEST PASS "
        f"({len(register_rows)} fixture register rows, {len(divergences)} divergences reproduced correctly)."
    )
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="Run bundled fixtures (DB-free, network-free, hermetic).")
    ap.add_argument("--root", default=str(REPO_ROOT), help="Repo root to scan.")
    ap.add_argument("--register", action="append", default=[], help="Additional register .md path(s) (repo-relative) to scan with the generic table parser.")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    ap.add_argument("--out", default=None, help="Also write the report to this path.")
    ap.add_argument("--live", action="store_true", help="Also attempt live MCP probes (needs network + MCP_CANARY_KEY).")
    ap.add_argument("--live-all-open", action="store_true", help="With --live, probe every open-classified row, not just divergent ones.")
    ap.add_argument("--mcp-url", default=os.environ.get("MCP_CANARY_URL", DEFAULT_MCP_URL))
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    root = Path(args.root).resolve()
    divergences, register_rows, cr_status_files, known_gaps = run_static_pass(root, args.register)

    live_results = None
    if args.live:
        mcp_key = os.environ.get("MCP_CANARY_KEY", "")
        if not mcp_key:
            print(
                "check_reconciliation_cadence: --live requires MCP_CANARY_KEY to be set in the "
                "environment (this script never guesses or falls back silently for a live network "
                "credential). Exiting.",
                file=sys.stderr,
            )
            return 2
        live_results = run_live_pass(divergences, register_rows, args.live_all_open, args.mcp_url, mcp_key)

    if args.json:
        payload = {
            "register_rows_scanned": len(register_rows),
            "divergences": [d.__dict__ for d in divergences],
            "live_results": live_results,
            "pass": len(divergences) == 0,
        }
        out_text = json.dumps(payload, indent=2)
        print(out_text)
    else:
        out_text = render_report(divergences, register_rows, live_results)
        print(out_text)

    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")

    return 1 if divergences else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
