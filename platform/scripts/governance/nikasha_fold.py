#!/usr/bin/env python3
"""nikasha_fold.py — Suvarna E5.2: the fold script (Scribe tooling).

Folding is "register row states, ledger emit (with the withholding list), tallies, fingerprints, drift check"
(arch §4.3 / ROLE_SCRIBE "What you do" 1-7; Track E brief §7 row E5.2). Everything here is deterministic bookkeeping;
the judgement (gate verdict, which state a row earns) is an input, never something this script decides.

What it writes, and the only ways it can write it:

  * the register (`NIKASHA_CHANGE_REGISTER_v2_0.md`): `set-state` edits exactly ONE row's state cell (a transition from
    the TRANSITIONS table, a reason, evidence, and — for the forward states — the gate reviewer's committed ACCEPT) and
    recomputes the header tallies in the same atomic write; `tally --write` recomputes the header alone. A header
    count is NEVER typed: it is derived from the rows (the register-tally drift of 2.7 was a typed number).
  * the gap ledger (`asset_gaps.jsonl`): ONLY by `emit-gaps`, which runs `asset_census.emit_gaps_summary` — the one
    ledger writer — over a census with every WITHHELD (asset, criterion) cell removed first, on a staging COPY, checks
    the staged result (old bytes an exact prefix, nothing for a withheld gap id), and only then appends the new bytes
    to the real ledger under an exclusive lock. A withheld pair gets no transition in either direction: no OPEN, no
    RE-OPEN and, above all, no CLOSED credit from a PASS the register says is unearned (R244: bo_upaya's Idem.pattern).
  * never `asset_certs.jsonl` (E5.1's `nikasha_certify.append_records` is the one write path for certificates), never
    the withholding list (a lift or an addition is a reviewed PR on a recorded SS decision), never the manifest.

`asset_gaps.jsonl` is append-only but NOT hash-chained (only `asset_certs.jsonl` is); append-only is therefore checked as
byte-prefix preservation, against the staging copy and, for a ledger inside a git work tree, against HEAD.

`NIKASHA_WITHHOLDING.json` (no written spec existed; chosen for compatibility with the tracker's membership test
`entry in data["entries"]`, detectors.py:_withholding_has_entry):
    {"version": 1, "doc": "...", "entries": {"<asset>-<criterion>": {"asset", "criterion", "register_row"?, "reason",
                                                                  "condition", "decided_by"}}}
`entries` is an OBJECT keyed by gap id: membership on a dict tests its keys, so a string entry such as
"bo_upaya-Idem.pattern" matches (a list of objects would not).

Usage (every path is overridable; tests and rehearsals run on copies):
  nikasha_fold.py set-state R244 --to DEFERRED --reason "..." --evidence "<decision id>"
  nikasha_fold.py tally [--write | --check]
  nikasha_fold.py emit-gaps --census <file under the trusted census root> [--layer L2] [--assets a,b] [--dry-run]
  nikasha_fold.py fingerprint [--out FILE]      nikasha_fold.py verify FILE
  nikasha_fold.py drift [--census FILE]         nikasha_fold.py withholding --check
Exit: 0 ok · 1 drift / verify mismatch / tally drift found (stdout JSON) · 2 refused (stderr `REFUSED <code>: ...`,
nothing written) · 5 script error · 75 lock held (EX_TEMPFAIL).
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import copy
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asset_census as ac  # noqa: E402  (the one ledger writer and the criterion registry; read/call only)
import nikasha_certify as nc  # noqa: E402  (census loader and the certification ledger reader; read only)

REGISTER_REL = "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md"
GAPS_REL = "00_ARCHITECTURE/control/asset_gaps.jsonl"
CERTS_REL = "00_ARCHITECTURE/control/asset_certs.jsonl"
WITHHOLDING_REL = "00_ARCHITECTURE/control/NIKASHA_WITHHOLDING.json"
CUTOVER_REL = "00_ARCHITECTURE/control/E4.3/CUTOVER.json"
REVIEWS_REL = "00_ARCHITECTURE/briefs/suvarna/reviews/"
ENV_LOCK = "SUVARNA_CENSUS_LOCK"
EX_TEMPFAIL = 75

# Mirrors suvarna_tracker.detectors.STATE_CLASSES, ORDER INCLUDED (classification is first-prefix-wins, so
# CLOSED_ON_BRANCH must precede CLOSED). The tracker is not importable from `main` (it lives in the control checkout).
STATE_CLASSES = ("CLOSED_ON_BRANCH", "OPEN", "CLOSED", "DONE", "PARTIAL", "MEASURED",
                 "DEFERRED", "WITHDRAWN", "IN_PROGRESS")
STATE_DISPLAY_ORDER = ("OPEN", "IN_PROGRESS", "CLOSED_ON_BRANCH", "PARTIAL", "DEFERRED", "DONE", "CLOSED",
                       "MEASURED", "WITHDRAWN")
STATE_LABEL = {c: c for c in STATE_CLASSES}
STATE_LABEL["MEASURED"] = "MEASURED in P6"                       # the register's own label for it
LABEL_STATE = {v: k for k, v in STATE_LABEL.items()}
SEVERITIES = ("BLOCKS_FREEZE", "BLOCKS_LAYER", "DEGRADES", "COSMETIC")
PIPE_SPLIT = re.compile(r"(?<!\\)\|")

# Default policy (design Q1; the sources carry no table): what a fold may move a row to. MEASURED is never a target
# (a legacy P6 label); WITHDRAWN is terminal; a closed row reopens only as a regression, with a reason.
_ANY_FORWARD = {"OPEN", "IN_PROGRESS", "PARTIAL", "CLOSED_ON_BRANCH", "DONE", "CLOSED", "DEFERRED", "WITHDRAWN"}
TRANSITIONS: dict[str, frozenset] = {
    "OPEN": frozenset(_ANY_FORWARD - {"OPEN"}),
    "IN_PROGRESS": frozenset(_ANY_FORWARD - {"IN_PROGRESS"}),
    "PARTIAL": frozenset(_ANY_FORWARD - {"PARTIAL"}),
    "CLOSED_ON_BRANCH": frozenset({"OPEN", "PARTIAL", "DONE", "CLOSED"}),
    "DEFERRED": frozenset({"OPEN", "IN_PROGRESS", "DONE", "CLOSED", "WITHDRAWN"}),
    "DONE": frozenset({"OPEN"}),
    "CLOSED": frozenset({"OPEN"}),
    "MEASURED": frozenset({"OPEN", "DONE", "CLOSED"}),
    "WITHDRAWN": frozenset(),
}
NEEDS_REVIEW = frozenset({"CLOSED", "DONE", "CLOSED_ON_BRANCH", "PARTIAL"})                    # "no verdict, no fold"
NEEDS_EVIDENCE = frozenset({"CLOSED", "DONE", "CLOSED_ON_BRANCH", "PARTIAL", "DEFERRED", "WITHDRAWN"})
LIVE = ac.LIVE_GAP_STATES
LEDGER_STATES = ("OPEN", "IN_PROGRESS", "CLOSED", "WITHDRAWN")


class FoldRefused(ValueError):
    """The request was refused; nothing was written. `code` is the stable, test-pinned reason slug."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _refuse(code: str, message: str):
    raise FoldRefused(code, message)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_paths(root: Path | None = None) -> dict:
    r = Path(root) if root else repo_root()
    return dict(register=r / REGISTER_REL, gaps=r / GAPS_REL, certs=r / CERTS_REL, withholding=r / WITHHOLDING_REL)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


# ───────────────────────────── register parsing ─────────────────────────────

def classify_state(cell: str) -> str:
    t = cell.strip().lstrip("*").strip().upper()
    for k in STATE_CLASSES:
        if t.startswith(k):
            return k
    return "OTHER"


class Row:
    __slots__ = ("id", "idx", "cells", "severity", "state_cell", "state_class", "malformed", "state_col", "pipes")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def parse_register(text: str) -> dict:
    """Rows keyed by id (header-aware exactly as the tracker's parse: the severity and state columns are located by
    name in the most recent `| # |` table header, a row whose cell count differs from its header is malformed), plus
    `lines`, the malformed ids, duplicate ids and `order`. Only rows in the `## 2` register section are rows."""
    lines = text.split("\n")
    rows: dict[str, Row] = {}
    order, malformed, dups = [], [], []
    layout = {"n": 9, "severity": 4, "state": 7}
    in_tally = False
    for i, line in enumerate(lines):
        if line.startswith("### 0.1"):
            in_tally = True
            continue
        if in_tally and line.startswith("###"):
            in_tally = False
        if in_tally:
            continue
        if re.match(r"^\|\s*#\s*\|", line):
            names = [c.strip().lower() for c in PIPE_SPLIT.split(line)]
            if "severity" in names and "state" in names:
                layout = {"n": len(names), "severity": names.index("severity"), "state": names.index("state")}
            continue
        m = re.match(r"^\| (R\d+) \|", line)
        if not m:
            continue
        cells = [c.strip() for c in PIPE_SPLIT.split(line)]
        bad = len(cells) != layout["n"]
        rid = m.group(1)
        get = (lambda j: cells[j] if j < len(cells) else "")
        r = Row(id=rid, idx=i, cells=cells, severity=get(layout["severity"]).strip("*").strip(),
                state_cell=get(layout["state"]), state_class=classify_state(get(layout["state"])),
                malformed=bad, state_col=layout["state"], pipes=[p.start() for p in re.finditer(r"(?<!\\)\|", line)])
        if rid in rows:
            dups.append(rid)
        else:
            order.append(rid)
        if bad:
            malformed.append(rid)
        rows[rid] = r
    return dict(rows=rows, order=order, lines=lines, malformed=malformed, duplicates=dups)


def _rid_key(rid: str) -> int:
    return int(rid[1:])


def computed_counts(reg: dict) -> dict:
    rows = reg["rows"]
    by_state = collections.Counter(r.state_class for r in rows.values())
    by_sev = collections.Counter(r.severity for r in rows.values())
    open_sev = collections.Counter(r.severity for r in rows.values() if r.state_class == "OPEN")
    open_ids = sorted((r.id for r in rows.values() if r.state_class == "OPEN" and r.severity == "BLOCKS_FREEZE"),
                      key=_rid_key)
    return dict(total=len(rows), by_state=dict(by_state), by_severity=dict(by_sev),
                open_by_severity=dict(open_sev), open_total=by_state.get("OPEN", 0), blocks_freeze_open_ids=open_ids)


def _open_line(n_total: int, c: dict) -> str:
    parts = []
    for sev in SEVERITIES:
        s = f"{sev} {c['open_by_severity'].get(sev, 0)}"
        if sev == "BLOCKS_FREEZE" and c["blocks_freeze_open_ids"]:
            s += f" ({', '.join(c['blocks_freeze_open_ids'])})"
        parts.append(s)
    return f"All {n_total} rows, every state. **Open rows only ({c['open_total']}):** " + " · ".join(parts) + "."


_STATE_ROW = re.compile(r"^(\|\s*)([A-Za-z_ 0-9]+?)(\s*\|\s*)(\d+)(\s*\|.*)$")
_TOTAL_ROW = re.compile(r"^(\|\s*\*\*total\*\*\s*\|\s*\*\*)(\d+)(\*\*\s*\|.*)$")
_SEV_ROW = re.compile(r"^(\|\s*)(BLOCKS_FREEZE|BLOCKS_LAYER|DEGRADES|COSMETIC)(\s*\|\s*)(\d+)(\s*\|.*)$")
_TOTAL_LINE = re.compile(r"\*\*Total rows: (\d+)\*\*")
_OPEN_LINE = re.compile(r"^All (\d+) rows, every state\. \*\*Open rows only \((\d+)\):\*\* (.*)$")


def read_header(lines: list) -> dict:
    """What the register's header currently claims (`state`: label -> n, `total`, `severity`, `total_line`, `open_line`)."""
    h = dict(state={}, total=None, severity={}, total_line=None, open_line=None, open_line_text=None)
    sec = None
    for line in lines:
        if line.startswith("### 0.1"):
            sec = "state"
            continue
        if line.startswith("### 0.2"):
            sec = "sev"
            continue
        if line.startswith("###") or line.startswith("## "):
            sec = None
        if sec == "state":
            m = _TOTAL_ROW.match(line)
            if m:
                h["total"] = int(m.group(2))
                continue
            m = _STATE_ROW.match(line)
            if m and m.group(2).strip().lower() != "state":
                h["state"][m.group(2).strip()] = int(m.group(4))
        elif sec == "sev":
            m = _SEV_ROW.match(line)
            if m:
                h["severity"][m.group(2)] = int(m.group(4))
        m = _TOTAL_LINE.search(line)
        if m and h["total_line"] is None:
            h["total_line"] = int(m.group(1))
        m = _OPEN_LINE.match(line)
        if m:
            h["open_line"] = (int(m.group(1)), int(m.group(2)))
            h["open_line_text"] = line
    return h


def header_drift(text: str) -> list:
    """Every cell of the header that disagrees with the rows (empty = consistent). Each: (what, claimed, computed)."""
    reg = parse_register(text)
    c = computed_counts(reg)
    h = read_header(reg["lines"])
    out = []
    if not h["state"]:
        out.append(("state table", "missing", "required"))
    for label, n in h["state"].items():
        cls = LABEL_STATE.get(label)
        if cls is None:
            out.append((f"state label {label!r}", "unknown", "a known state class"))
            continue
        if c["by_state"].get(cls, 0) != n:
            out.append((f"state {label}", n, c["by_state"].get(cls, 0)))
    claimed_classes = {LABEL_STATE.get(x) for x in h["state"]}
    for cls, n in c["by_state"].items():
        if n and cls not in claimed_classes:
            out.append((f"state {STATE_LABEL.get(cls, cls)}", "no header row", n))
    if h["total"] != c["total"]:
        out.append(("state table total", h["total"], c["total"]))
    if h["total_line"] != c["total"]:
        out.append(("Total rows line", h["total_line"], c["total"]))
    for sev in SEVERITIES:
        if h["severity"].get(sev) != c["by_severity"].get(sev, 0):
            out.append((f"severity {sev}", h["severity"].get(sev), c["by_severity"].get(sev, 0)))
    want = _open_line(c["total"], c)
    if h["open_line_text"] != want:
        out.append(("open-rows line", h["open_line_text"], want))
    return out


def apply_tally(text: str) -> str:
    """The register text with every header tally recomputed from its rows; everything else byte-identical."""
    reg = parse_register(text)
    if reg["duplicates"]:
        _refuse("register_duplicate_rows", f"duplicate row ids {sorted(set(reg['duplicates']))}: a tally over them is meaningless")
    c = computed_counts(reg)
    unknown_sev = sorted(s for s in c["by_severity"] if s not in SEVERITIES)
    if unknown_sev:
        _refuse("unknown_severity", f"rows carry severities outside {SEVERITIES}: {unknown_sev}")
    other = sorted(r.id for r in reg["rows"].values() if r.state_class == "OTHER")
    if other:
        _refuse("unclassifiable_state", f"rows {other} have a state the tracker cannot classify")
    lines = list(reg["lines"])
    sec = None
    seen_state_labels, total_at, last_state_row = set(), None, None
    seen_open_line = seen_total_line = False
    for i, line in enumerate(lines):
        if line.startswith("### 0.1"):
            sec = "state"
            continue
        if line.startswith("### 0.2"):
            sec = "sev"
            continue
        if line.startswith("###") or line.startswith("## "):
            sec = None
        if sec == "state":
            m = _TOTAL_ROW.match(line)
            if m:
                lines[i] = f"{m.group(1)}{c['total']}{m.group(3)}"
                total_at = i
                continue
            m = _STATE_ROW.match(line)
            if m and m.group(2).strip().lower() != "state":
                label = m.group(2).strip()
                cls = LABEL_STATE.get(label)
                if cls is None:
                    _refuse("header_label_unknown", f"state-table label {label!r} is not a known state class")
                lines[i] = f"{m.group(1)}{m.group(2)}{m.group(3)}{c['by_state'].get(cls, 0)}{m.group(5)}"
                seen_state_labels.add(cls)
                last_state_row = i
        elif sec == "sev":
            m = _SEV_ROW.match(line)
            if m:
                lines[i] = f"{m.group(1)}{m.group(2)}{m.group(3)}{c['by_severity'].get(m.group(2), 0)}{m.group(5)}"
        m = _TOTAL_LINE.search(lines[i])
        if m and not seen_total_line:
            lines[i] = _TOTAL_LINE.sub(f"**Total rows: {c['total']}**", lines[i], count=1)
            seen_total_line = True
        if _OPEN_LINE.match(line):
            lines[i] = _open_line(c["total"], c)
            seen_open_line = True
    if total_at is None or not seen_total_line or not seen_open_line:
        _refuse("header_missing", "the register header lacks its state-table total, `Total rows` line or open-rows line: "
                                  "refusing to invent a header")
    missing = [cls for cls in STATE_DISPLAY_ORDER if c["by_state"].get(cls) and cls not in seen_state_labels]
    for cls in reversed(missing):
        lines.insert(total_at, f"| {STATE_LABEL[cls]} | {c['by_state'][cls]} |")
    return "\n".join(lines)


# ───────────────────────────── set-state ─────────────────────────────

_VERDICT = re.compile(r"(?im)^[\s>#*_\-]*verdict\b[\s*_:=\-—]*(ACCEPT_WITH_CORRECTIONS|ACCEPT|REJECT)\b")


def check_review(path, reviews_root: Path) -> str:
    """The gate reviewer's committed file: under the one review path (arch §12.6), whose LAST `verdict:` line is
    ACCEPT or ACCEPT_WITH_CORRECTIONS. Returns the verdict. (Format: design question Q3.)"""
    if not path:
        _refuse("review_required", "a forward state needs the gate reviewer's review file (--review): no verdict, no fold")
    p = Path(path)
    root = Path(os.path.realpath(reviews_root))
    rp = Path(os.path.realpath(p))
    try:
        rp.relative_to(root)
    except ValueError:
        _refuse("review_untrusted", f"{rp} is not under the review path {root}")
    if not rp.is_file():
        _refuse("review_missing", f"{rp} is not a file")
    found = _VERDICT.findall(rp.read_text(encoding="utf-8", errors="replace"))
    if not found:
        _refuse("review_no_verdict", f"{rp} carries no `verdict: ACCEPT|ACCEPT_WITH_CORRECTIONS|REJECT` line")
    v = found[-1].upper()
    if v == "REJECT":
        _refuse("review_rejected", f"{rp}: the last verdict is REJECT")
    return v


def _atomic_write(path: Path, data: bytes) -> None:
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        with contextlib.suppress(OSError):
            os.chmod(tmp, path.stat().st_mode & 0o7777)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _state_text(to: str, reason: str, evidence: str | None, review_verdict: str | None) -> str:
    t = f"{to} — {reason}"
    if evidence:
        t += f" [evidence: {evidence}]"
    if review_verdict:
        t += f" [gate: {review_verdict}]"
    return t


def set_state(register_path, row_id: str, to: str, reason: str, *, evidence: str | None = None, review=None,
              reviews_root: Path | None = None, write: bool = True) -> dict:
    p = Path(register_path)
    text = p.read_text(encoding="utf-8")
    reg = parse_register(text)
    if not re.fullmatch(r"R\d+", row_id or ""):
        _refuse("bad_row_id", f"{row_id!r} is not a register row id (R<number>)")
    if row_id not in reg["rows"]:
        _refuse("unknown_row", f"{row_id} is not in the register")
    row = reg["rows"][row_id]          # a duplicated id is refused by apply_tally below (`register_duplicate_rows`)
    if row.malformed:
        _refuse("row_malformed", f"{row_id} has a cell count that differs from its table header: fix it by hand first")
    if to not in STATE_CLASSES or to == "MEASURED":
        _refuse("bad_target_state", f"{to!r} is not a state a fold may set (one of {sorted(TRANSITIONS['OPEN'] | {'OPEN'})})")
    frm = row.state_class
    if frm == to:
        _refuse("no_change", f"{row_id} is already {to}")
    if to not in TRANSITIONS.get(frm, frozenset()):
        _refuse("illegal_transition", f"{row_id}: {frm} -> {to} is not an allowed transition "
                                      f"(from {frm}: {sorted(TRANSITIONS.get(frm, ()))})")
    reason = (reason or "").replace("\n", " ").strip()
    if not reason:
        _refuse("reason_required", "a state change carries its reason")
    evidence = (evidence or "").replace("\n", " ").strip() or None
    if to in NEEDS_EVIDENCE and not evidence:
        _refuse("evidence_required", f"{to} needs evidence (a commit, PR, path or decision id): --evidence")
    verdict = None
    if to in NEEDS_REVIEW:
        verdict = check_review(review, reviews_root if reviews_root is not None else repo_root() / REVIEWS_REL)
    new_cell = " " + _state_text(to, reason, evidence, verdict).replace("|", "\\|") + " "
    line = reg["lines"][row.idx]
    # cells[0] is the empty text before the first pipe, so cell i lies between pipes[i-1] and pipes[i]
    a, b = row.pipes[row.state_col - 1], row.pipes[row.state_col]
    new_line = line[: a + 1] + new_cell + line[b:]
    lines = list(reg["lines"])
    lines[row.idx] = new_line
    before_drift = header_drift(text)
    new_text = apply_tally("\n".join(lines))
    # self-checks before anything is written: the target row now classifies as `to`, no other row's cells moved.
    after = parse_register(new_text)
    if after["rows"][row_id].state_class != to:
        _refuse("self_check_failed", f"{row_id} would classify as {after['rows'][row_id].state_class}, not {to}")
    for rid, r in reg["rows"].items():
        if rid != row_id and (after["rows"][rid].cells != r.cells):
            _refuse("self_check_failed", f"row {rid} would change")
    if header_drift(new_text):
        _refuse("self_check_failed", f"header still drifts after the recompute: {header_drift(new_text)}")
    if write:
        _atomic_write(p, new_text.encode("utf-8"))
    return dict(row=row_id, from_state=frm, to_state=to, header_was_drifted=bool(before_drift),
                counts=computed_counts(after)["by_state"], written=bool(write))


def tally(register_path, *, write: bool) -> dict:
    p = Path(register_path)
    text = p.read_text(encoding="utf-8")
    drift = header_drift(text)
    new_text = apply_tally(text) if (write or not drift) else text
    changed = new_text != text
    if write and changed:
        _atomic_write(p, new_text.encode("utf-8"))
    reg = parse_register(new_text if write else text)
    return dict(drift=[dict(what=w, claimed=a, computed=b) for w, a, b in drift], written=bool(write and changed),
                counts=computed_counts(reg))


# ───────────────────────────── withholding ─────────────────────────────

def load_withholding(path, *, must_exist: bool = True) -> dict:
    p = Path(path)
    if not p.is_file():
        if must_exist:
            _refuse("withholding_missing", f"{p} does not exist: an emit is never made without the withholding list")
        return dict(version=1, entries={})
    try:
        data = nc.strict_json_loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        _refuse("withholding_malformed", f"{p} is not strict JSON ({e})")
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("entries"), dict):
        _refuse("withholding_malformed", "expected {'version': 1, 'entries': {<asset>-<criterion>: {...}}}")
    for key, e in data["entries"].items():
        if not isinstance(e, dict):
            _refuse("withholding_malformed", f"entry {key!r} is not an object")
        asset, crit = e.get("asset"), e.get("criterion")
        if not (isinstance(asset, str) and asset and isinstance(crit, str) and crit):
            _refuse("withholding_malformed", f"entry {key!r} needs a non-empty asset and criterion")
        if key != f"{asset}-{crit}":
            _refuse("withholding_malformed", f"entry key {key!r} is not <asset>-<criterion> = {asset}-{crit}")
        if crit not in ac.CRITERION_REGISTRY:
            _refuse("withholding_unknown_criterion", f"entry {key!r}: {crit!r} is not a registry criterion — a typo "
                                                     "here would silently withhold nothing")
        for f in ("reason", "condition", "decided_by"):
            if not (isinstance(e.get(f), str) and e[f].strip()):
                _refuse("withholding_malformed", f"entry {key!r} needs a non-empty {f}")
        rr = e.get("register_row")
        if rr is not None and not (isinstance(rr, str) and re.fullmatch(r"R\d+", rr)):
            _refuse("withholding_malformed", f"entry {key!r}: register_row {rr!r} is not R<number>")
    return data


def filter_census(census: dict, withheld: dict) -> tuple[dict, list, list]:
    """A copy of the layer census with every withheld (asset, criterion) cell removed. Returns (census, applied,
    not_measured): `applied` lists the cells actually removed with their verdict."""
    c = copy.deepcopy(census)
    pairs = {(e["asset"], e["criterion"]): k for k, e in withheld.items()}
    applied = []
    for a in c.get("assets", []):
        for crit in list(a.get("measurements", {})):
            key = pairs.get((a.get("asset_id"), crit))
            if key is not None:
                applied.append(dict(gap_id=key, verdict=a["measurements"][crit].get("v")))
                del a["measurements"][crit]
    got = {x["gap_id"] for x in applied}
    return c, applied, sorted(set(withheld) - got)


# ───────────────────────────── gap ledger ─────────────────────────────

def read_gap_ledger(path) -> dict:
    """The ledger as `emit_gaps` reads it: latest row per gap_id in FILE order, ids ever superseded; plus line errors."""
    data = Path(path).read_bytes()
    latest, ever_sup, errors, n = {}, set(), [], 0
    first = None
    for ln_no, ln in enumerate(data.decode("utf-8", "replace").split("\n"), 1):
        if not ln.strip():
            continue
        n += 1
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            errors.append((ln_no, "not JSON"))
            continue
        if not isinstance(r, dict):
            errors.append((ln_no, "not an object"))
            continue
        if first is None:
            first = r
        if r.get("gap_id"):
            latest[r["gap_id"]] = r
            if r.get("superseded_by"):
                ever_sup.add(r["gap_id"])
    return dict(latest=latest, ever_superseded=ever_sup, errors=errors, lines=n, first=first, bytes=len(data),
                trailing_newline=(not data) or data.endswith(b"\n"))


def ledger_metrics(path, certs_path=None) -> dict:
    g = read_gap_ledger(path)
    open_gaps = [r for gid, r in g["latest"].items() if gid not in g["ever_superseded"]
                 and str(r.get("state", "OPEN")).upper() in LIVE and str(r.get("kind", "gap")).lower() == "gap"]
    tracker_view = [r for gid, r in g["latest"].items() if r.get("state") in ("OPEN", "RE-OPENED")
                    and r.get("kind", "gap") == "gap" and not r.get("superseded_by")]
    m = dict(open_gaps=len(open_gaps), open_gaps_tracker_view=len(tracker_view), gap_ids=len(g["latest"]))
    if certs_path is not None and Path(certs_path).is_file():
        try:
            recs = nc.read_records(certs_path)
            m["certification_records"] = sum(1 for r in recs if nc._is_cert_line(r))
        except Exception as e:  # noqa: BLE001 — surfaced, never swallowed into a number
            m["certification_records"] = None
            m["certification_records_error"] = f"{type(e).__name__}: {e}"[:200]
    return m


def _stage_emit(census: dict, ledger_bytes: bytes, assets) -> tuple[dict, bytes]:
    """Run the one ledger writer on a COPY of the ledger (asset_census.CTRL pointed at a temp dir)."""
    with tempfile.TemporaryDirectory(prefix="fold_stage_") as d:
        sp = Path(d) / "asset_gaps.jsonl"
        sp.write_bytes(ledger_bytes)
        old = ac.CTRL
        ac.CTRL = Path(d)
        try:
            summary = ac.emit_gaps_summary(census, assets)
        except ac.ScopeError as e:
            _refuse("scope_error", str(e))
        finally:
            ac.CTRL = old
        return summary, sp.read_bytes()


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True)


def git_preflight(ledger: Path, *, allow_dirty: bool = False) -> dict | None:
    """For a ledger inside a git work tree: tracked, its HEAD bytes a prefix of the file, no uncommitted change (one
    emit = one reviewable commit), and — for the canonical ledger path — the E4.3 cut-over landed. None outside git."""
    lp = Path(os.path.realpath(ledger))
    r = _git(lp.parent, "rev-parse", "--show-toplevel")
    if r.returncode != 0:
        return None
    top = Path(os.path.realpath(r.stdout.decode().strip()))
    rel = lp.relative_to(top).as_posix()
    if _git(top, "ls-files", "--error-unmatch", "--", rel).returncode != 0:
        _refuse("ledger_untracked", f"{rel} is not tracked: a ledger a fold appends to is committed so the append is a diff")
    h = _git(top, "show", f"HEAD:{rel}")
    if h.returncode != 0:
        _refuse("ledger_not_at_head", f"{rel} has no committed version at HEAD")
    cur = lp.read_bytes()
    if not cur.startswith(h.stdout):
        _refuse("ledger_not_append_only", f"{rel}: the committed (HEAD) bytes are not a prefix of the working file")
    if cur != h.stdout and not allow_dirty:
        _refuse("ledger_dirty", f"{rel} has uncommitted changes: commit the previous emit first (one emit per commit)")
    if rel == GAPS_REL and not (top / CUTOVER_REL).is_file():
        _refuse("cutover_not_landed", f"{CUTOVER_REL} is not on this checkout: no --emit-gaps before the E4.3 cut-over lands")
    return dict(top=str(top), rel=rel)


@contextlib.contextmanager
def census_lock(lock_file):
    """Optional exclusive non-blocking flock (ARCH §12.15: ledger writers run under the census lock)."""
    if not lock_file:
        yield
        return
    p = Path(lock_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(p), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LockHeld(str(p)) from None
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class LockHeld(RuntimeError):
    pass


def emit_gaps_withheld(census: dict, ledger, withholding, *, assets=None, dry_run: bool = False,
                       allow_dirty: bool = False, lock_file=None) -> dict:
    """The withholding-aware `--emit-gaps`. `census` is a loaded, trusted layer census (see `load_trusted_census`)."""
    lp = Path(ledger)
    if not lp.is_file() or lp.is_symlink():
        _refuse("ledger_missing", f"{lp} is not a regular file")
    wh = withholding if isinstance(withholding, dict) else load_withholding(withholding)
    entries = wh["entries"]
    withheld_ids = set(entries)
    if not dry_run:
        git_preflight(lp, allow_dirty=allow_dirty)
    with census_lock(lock_file):
        orig = lp.read_bytes()
        if orig and not orig.endswith(b"\n"):
            _refuse("ledger_no_trailing_newline", "the ledger's last line is unterminated: an append would glue onto it")
        filtered, applied, not_measured = filter_census(census, entries)
        unfiltered_summary, _ = _stage_emit(census, orig, assets)
        summary, staged = _stage_emit(filtered, orig, assets)
        if not staged.startswith(orig):
            _refuse("ledger_not_append_only", "the staged emit does not preserve the old ledger bytes")
        new = staged[len(orig):]
        rows = []
        for ln in new.decode("utf-8").split("\n"):
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                _refuse("staged_row_invalid", f"a staged row is not JSON: {ln[:80]!r}")
            if not isinstance(r, dict):
                _refuse("staged_row_invalid", "a staged row is not a JSON object")
            if r.get("gap_id") in withheld_ids:
                _refuse("withheld_row_emitted", f"the staged emit would write a row for the withheld {r['gap_id']}")
            rows.append(dict(gap_id=r.get("gap_id"), state=r.get("state"), criterion=r.get("criterion")))
        status = "dry_run" if dry_run else ("appended" if new else "unchanged")
        if new and not dry_run:
            fd = os.open(str(lp), os.O_RDWR | os.O_APPEND)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                if lp.read_bytes() != orig:
                    _refuse("ledger_changed_during_fold", "the ledger changed between staging and append: re-run")
                os.write(fd, new)
                os.fsync(fd)
            finally:
                with contextlib.suppress(OSError):
                    fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
        after = orig + new if (new and not dry_run) else orig
        return dict(status=status, summary=summary, unfiltered_summary=unfiltered_summary, withheld_applied=applied,
                    withheld_not_measured=not_measured, rows=rows, lines_before=orig.count(b"\n"),
                    lines_after=after.count(b"\n"), sha256_before=_sha(orig), sha256_after=_sha(after))


def load_trusted_census(path, layer=None) -> dict:
    """The census for `emit-gaps`: loaded through E5.1's loader (committed or staged under the trusted root, strict JSON,
    registry-bound head), then the layer object selected."""
    try:
        src = nc._load_census(path, None)
        obj = src.obj
        if "assets" in obj and "generated" in obj:
            c = obj
            layer = c.get("layer")
        else:
            if not layer:
                _refuse("layer_required", "the census file is multi-layer: pass --layer")
            c = nc._select_layer(obj, layer)
        nc._check_census_head(c, layer, c.get("generated"), True)
    except nc.CertificationRefused as e:
        _refuse(e.code, e.message)
    return c


# ───────────────────────────── fingerprints ─────────────────────────────

def canonical_rows(text: str) -> dict:
    reg = parse_register(text)
    return {rid: " | ".join(re.sub(r"\s+", " ", c).strip() for c in reg["rows"][rid].cells[1:-1])
            for rid in sorted(reg["rows"], key=_rid_key)}


def row_fingerprint(text: str) -> tuple[str, dict]:
    rows = canonical_rows(text)
    per = {rid: _sha(json.dumps([rid, cells], ensure_ascii=False).encode())[:16] for rid, cells in rows.items()}
    blob = json.dumps(sorted(rows.items(), key=lambda kv: _rid_key(kv[0])), ensure_ascii=False, separators=(",", ":"))
    return _sha(blob.encode()), per


def _file_fp(path) -> dict | None:
    p = Path(path)
    if not p.is_file():
        return None
    b = p.read_bytes()
    return dict(lines=b.count(b"\n"), bytes=len(b), sha256=_sha(b), md5=_md5(b))


def fingerprints(paths: dict) -> dict:
    out = {}
    rp = Path(paths["register"])
    if rp.is_file():
        text = rp.read_text(encoding="utf-8")
        fp, per = row_fingerprint(text)
        out["register"] = dict(rows=len(per), row_fingerprint=fp, row_hashes=per, **_file_fp(rp))
    else:
        out["register"] = None
    out["gaps"] = _file_fp(paths["gaps"])
    out["certs"] = _file_fp(paths["certs"])
    out["withholding"] = _file_fp(paths["withholding"])
    return out


def verify_fingerprints(recorded: dict, paths: dict) -> list:
    """Differences between a recorded fingerprint document and the files now. Each (what, detail)."""
    now = fingerprints(paths)
    diffs = []
    for k in ("register", "gaps", "certs", "withholding"):
        a, b = recorded.get(k), now.get(k)
        if a is None and b is None:
            continue
        if (a is None) != (b is None):
            diffs.append((k, "present now" if b else "missing now"))
            continue
        if k == "register":
            if a["row_fingerprint"] != b["row_fingerprint"]:
                ch = sorted((r for r in set(a["row_hashes"]) | set(b["row_hashes"])
                             if a["row_hashes"].get(r) != b["row_hashes"].get(r)), key=_rid_key)
                diffs.append((k, f"rows changed: {', '.join(ch)}"))
            elif a["sha256"] != b["sha256"]:
                diffs.append((k, "header/prose changed, rows identical"))
        elif k in ("gaps", "certs"):
            if a["sha256"] == b["sha256"]:
                continue
            cur = Path(paths[k]).read_bytes()
            if len(cur) > a["bytes"] and _sha(cur[: a["bytes"]]) == a["sha256"]:
                diffs.append((k, f"appended only (+{b['lines'] - a['lines']} lines)"))
            else:
                diffs.append((k, "REWRITTEN (the recorded bytes are not a prefix)"))
        elif a["sha256"] != b["sha256"]:
            diffs.append((k, "changed"))
    return diffs


# ───────────────────────────── drift ─────────────────────────────

def drift(paths: dict, census: dict | None = None) -> list:
    """Register vs ledger vs withholding vs census disagreements. Each finding: dict(code, level ERROR|NOTE, detail)."""
    f = []

    def add(code, level, detail):
        f.append(dict(code=code, level=level, detail=detail))

    rp = Path(paths["register"])
    reg = None
    if not rp.is_file():
        add("register_missing", "ERROR", str(rp))
    else:
        text = rp.read_text(encoding="utf-8")
        reg = parse_register(text)
        for w, a, b in header_drift(text):
            add("tally_drift", "ERROR", f"{w}: header {a!r} vs rows {b!r}")
        if reg["malformed"]:
            add("register_malformed_rows", "ERROR", ", ".join(reg["malformed"]))
        if reg["duplicates"]:
            add("register_duplicate_rows", "ERROR", ", ".join(sorted(set(reg["duplicates"]))))
        other = sorted(r.id for r in reg["rows"].values() if r.state_class == "OTHER")
        if other:
            add("register_unclassifiable_state", "ERROR", ", ".join(other))
    wh = None
    try:
        wh = load_withholding(paths["withholding"], must_exist=True)
    except FoldRefused as e:
        add(f"withholding_{e.code}" if not e.code.startswith("withholding") else e.code, "ERROR", e.message)
    gp = Path(paths["gaps"])
    g = None
    if not gp.is_file():
        add("gaps_ledger_missing", "ERROR", str(gp))
    else:
        g = read_gap_ledger(gp)
        for ln, why in g["errors"]:
            add("gaps_ledger_bad_line", "ERROR", f"line {ln}: {why}")
        if g["first"] is None or g["first"].get("asset") != "_schema":
            add("gaps_ledger_no_schema_row", "ERROR", "the first row is not the _schema row")
        if not g["trailing_newline"]:
            add("gaps_ledger_no_trailing_newline", "ERROR", "the last line is unterminated")
        bad = sorted({str(r.get("state")) for r in g["latest"].values()} - set(LEDGER_STATES))
        if bad:
            add("gaps_ledger_unknown_state", "ERROR", ", ".join(bad))
        m = ledger_metrics(gp)
        if m["open_gaps"] != m["open_gaps_tracker_view"]:
            add("open_gaps_view_differs", "NOTE", f"emit_gaps semantics {m['open_gaps']} vs tracker view "
                                                  f"{m['open_gaps_tracker_view']} (IN_PROGRESS / superseded handling)")
    cp = Path(paths["certs"])
    if cp.is_file():
        try:
            nc.read_records(cp)
        except Exception as e:  # noqa: BLE001
            add("certs_ledger_unreadable", "ERROR", f"{type(e).__name__}: {e}"[:300])
    else:
        add("certs_ledger_missing", "NOTE", str(cp))
    if wh is not None:
        for key, e in wh["entries"].items():
            rr = e.get("register_row")
            if rr and reg is not None:
                row = reg["rows"].get(rr)
                if row is None:
                    add("withholding_row_missing", "ERROR", f"{key}: register row {rr} is not in the register")
                elif row.state_class in ("CLOSED", "DONE", "WITHDRAWN"):
                    add("withholding_outlives_row", "ERROR", f"{key}: {rr} is {row.state_class} but the withholding is "
                                                             "still in force (lifting needs a recorded SS decision)")
            if g is not None:
                last = g["latest"].get(key)
                if last is not None and str(last.get("state", "")).upper() == "CLOSED" and key not in g["ever_superseded"]:
                    add("withheld_gap_closed_in_ledger", "NOTE",
                        f"{key}: the ledger's latest row is CLOSED (credited before it was withheld); append-only, so "
                        "reported, not corrected — a correction is an SS decision")
    if census is not None and g is not None and wh is not None and gp.is_file():
        try:
            filtered, applied, _ = filter_census(census, wh["entries"])
            summ, _ = _stage_emit(filtered, gp.read_bytes(), None)
            if any(summ[k] for k in ("added", "closed", "reopened")):
                add("census_pending_emit", "NOTE", f"the census would change the ledger: {summ}")
            for a in applied:
                if a["verdict"] == "PASS":
                    add("withheld_cell_measures_pass", "NOTE", f"{a['gap_id']}: the census reads PASS — withheld, not credited")
        except FoldRefused as e:
            add(f"census_{e.code}", "ERROR", e.message)
    return f


# ───────────────────────────── CLI ─────────────────────────────

def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="nikasha_fold", description="Suvarna E5.2 fold script")
    ap.add_argument("--repo", default=None, help="repo root for the default paths (default: this checkout)")
    for k in ("register", "gaps", "certs", "withholding"):
        ap.add_argument(f"--{k}", default=None)
    ap.add_argument("--lock-file", default=None, help=f"census lock (default ${ENV_LOCK}); exit 75 when held")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set-state")
    s.add_argument("row")
    s.add_argument("--to", required=True)
    s.add_argument("--reason", default="")
    s.add_argument("--evidence", default=None)
    s.add_argument("--review", default=None)
    s.add_argument("--reviews-root", default=None)
    s.add_argument("--dry-run", action="store_true")
    t = sub.add_parser("tally")
    g = t.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    e = sub.add_parser("emit-gaps")
    e.add_argument("--census", required=True)
    e.add_argument("--layer", default=None)
    e.add_argument("--assets", default=None)
    e.add_argument("--dry-run", action="store_true")
    e.add_argument("--allow-dirty", action="store_true")
    f = sub.add_parser("fingerprint")
    f.add_argument("--out", default=None)
    v = sub.add_parser("verify")
    v.add_argument("file")
    d = sub.add_parser("drift")
    d.add_argument("--census", default=None)
    d.add_argument("--layer", default=None)
    w = sub.add_parser("withholding")
    w.add_argument("--check", action="store_true")
    return ap


def _paths(a) -> dict:
    p = default_paths(a.repo)
    for k in ("register", "gaps", "certs", "withholding"):
        if getattr(a, k):
            p[k] = Path(getattr(a, k))
    return p


def _out(obj) -> None:
    print(json.dumps(obj, indent=1, ensure_ascii=False))


def main(argv=None) -> int:
    a = _parser().parse_args(sys.argv[1:] if argv is None else list(argv))
    p = _paths(a)
    lock = a.lock_file or os.environ.get(ENV_LOCK)
    try:
        if a.cmd == "set-state":
            with census_lock(lock):
                r = set_state(p["register"], a.row, a.to.upper(), a.reason, evidence=a.evidence, review=a.review,
                              reviews_root=Path(a.reviews_root) if a.reviews_root else None, write=not a.dry_run)
            r["next_steps"] = ["manifest_fingerprint.py --write then --check", "drift_detector.py", "nikasha_fold.py drift"]
            _out(r)
            return 0
        if a.cmd == "tally":
            r = tally(p["register"], write=a.write)
            _out(r)
            return 1 if (r["drift"] and not a.write) else 0
        if a.cmd == "emit-gaps":
            c = load_trusted_census(a.census, a.layer)
            assets = [x for x in a.assets.split(",") if x] if a.assets else None
            r = emit_gaps_withheld(c, p["gaps"], p["withholding"], assets=assets, dry_run=a.dry_run,
                                   allow_dirty=a.allow_dirty, lock_file=lock)
            r["next_steps"] = ["git commit -- 00_ARCHITECTURE/control/asset_gaps.jsonl (one emit per commit)",
                               "nikasha_fold.py fingerprint", "nikasha_fold.py drift"]
            _out(r)
            return 0
        if a.cmd == "fingerprint":
            doc = fingerprints(p)
            if a.out:
                _atomic_write(Path(a.out), (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode())
            _out(doc)
            return 0
        if a.cmd == "verify":
            try:
                rec = nc.strict_json_loads(Path(a.file).read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                _refuse("bad_fingerprint_file", f"{a.file}: {e}")
            diffs = verify_fingerprints(rec, p)
            _out(dict(identical=not diffs, differences=[dict(what=k, detail=d) for k, d in diffs]))
            return 1 if diffs else 0
        if a.cmd == "drift":
            c = load_trusted_census(a.census, a.layer) if a.census else None
            fl = drift(p, c)
            _out(dict(findings=fl, errors=sum(1 for x in fl if x["level"] == "ERROR"),
                      metrics=ledger_metrics(p["gaps"], p["certs"]) if Path(p["gaps"]).is_file() else None))
            return 1 if any(x["level"] == "ERROR" for x in fl) else 0
        if a.cmd == "withholding":
            wh = load_withholding(p["withholding"])
            _out(dict(ok=True, entries=sorted(wh["entries"])))
            return 0
    except FoldRefused as e:
        print(f"REFUSED {e.code}: {e.message}", file=sys.stderr)
        return 2
    except LockHeld as e:
        print(f"census lock held: {e}", file=sys.stderr)
        return EX_TEMPFAIL
    return 5


if __name__ == "__main__":
    sys.exit(main())
