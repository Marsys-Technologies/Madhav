#!/usr/bin/env python3
"""AM-10 re-pin tool — the §4.0 daśā read contract, one command when the L1 rebuild lands.

Draft AM-10 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-10) rules: ONE pin, no auto-follow; a
re-pin is by EVIDENCE only, in one small PR; any class flip / lord flip / anchor failure is
a STOP, not a re-pin. This tool produces the evidence and, only with --apply and only when
nothing stops it, performs the single change.

    python3 scripts/gochara/repin_dasha_contract.py --new-build-id <uuid> \\
        [--chart-id 482012f1-…] [--out evidence.md] [--forensic-report path]
        [--settled-notice notice.json]      # Suvarṇa's SETTLED-1 notice: expected per-level shift + a STATED tolerance — the measured shift must match or the verdict is STOP
        [--capture-new new.json --new-build-id <uuid>]  # AFTER SETTLED-1 (read-only): the durable POST record of the new build, in the capture format (same snapshot discipline as --capture-old)
        [--capture-old old.json]             # BEFORE S-L1 (read-only): save the pinned build's rows — the old rows may not exist afterwards; then pass --old-rows old.json
        [--old-rows old.json]                # the old rows come from this capture (sha256-checked) instead of the database
        [--dry-run]                          # print the full report and the test-literal matches; write NOTHING
        [--apply --settled-received <steward message id> [--rulings rulings.json]]

ST-SL1-HOLD (steward M20261002T223058-f6e4; split by Codex R17-6): from the start of Suvarṇa's S-L1 window until the steward announces the hold LIFTED (after SETTLED-1 AND the reviewed re-pin is merged),
no Gochara build / verification / brief / resonance run / measurement extract runs against production chart 482012f1. This tool is local PREPARATION: the read-only comparison and --apply (a local patch of the
checkout) need only the steward's announcement that SETTLED-1 was RECEIVED (`--settled-received <message id>`); it does NOT lift the hold. Test literals equal to an old boundary are listed and --apply STOPS
before writing anything until --rulings classifies each `path:line` as rewrite or keep (the steward's ruling).

READ-ONLY against the database (the connection is set READ ONLY); --apply edits only
files in this repository:
  * services/gochara_kernel/inventory_verifier.py: the verifier's INDEPENDENT pin `_C_BUILD` (the second site — Fable F-R17-2; --apply STOPS naming it if the file is absent or the line is not unique);
  * services/gochara_rules/permission.py: DASHA_READ_CONTRACT['build_id'] and the MD/AD/PD
    reference-row tuples (re-measured from the new build, matched by (level, parent path, index));
  * tests/l3/**/*.py: ONLY the reference rows' ids (also when a line wrap splits one — rewritten character for character) and the old pin's build id (exact-string, ONE pass). An old boundary INSTANT in a test is NOT rewritten — it may be an event date
    that merely equals a boundary (D8) — it is printed as `REVIEW path:line old -> new` for a human;
  * a generated tests/l3/gochara_rules/test_am10_repin_<build8>.py asserting the OLD id is refused
    (DashaReadConflict) and the NEW id accepted (rule 2(g)).
The frozen v1.4 spec/oracle JSON are never edited (rule 3).

MOSHIER → SWISS (Suvarṇa addendum 4; steward M20261002T222913-35c5): the stored rows were built on the Moshier fallback; at S-L1 the Vimśottarī BOUNDARIES move by ≈ 1.94 h while lords and
row counts hold. So a MOVED boundary is not a flip: the STOP is a different lord (or a missing/extra row) at ANY matched (level, parent path, index) row (D7); the oracle instants whose lord
differs only because an edge moved are reported as BOUNDARY-SENSITIVE (D8), and the per-level old → new shift is in the evidence.

G6 (steward M20261002T223036-02f0): a mixed L1 state — more than one Vimśottarī build — is REFUSED by the writer AND the verifier since Stream A's 699638fbe (`dasha_builds_mixed` / `dasha_build_not_pinned`). This
tool applies the same condition BEFORE the re-pin: the verdict is STOP unless chart_dashas holds EXACTLY ONE Vimśottarī build (Lahiri, levels 1–3, any tier) and it is the SETTLED-1 build; --apply asserts the
re-pinned constant equals that build and the old pin is gone.
VERIFIER-PREDICATE MIRROR (vi) (steward ST-REPIN-PATCH-GO): every Vimśottarī / Lahiri row of the chart — ALL levels, ALL tiers, NULL build included — must be exactly the SETTLED-1 build (the verifier's own
query in `validate_consumed_dasha_population`), so the tool cannot report CLEAN where the verifier would refuse after the re-pin; never relaxed. THE POST-S-L1 SHAPE IS FIXED (Codex ASTRA_REVIEW_REPIN_TOOL_DELTA): 45 + 1 partitions and exactly the SETTLED-1 build; no notice field overrides it (the notice REFUSES expected_partitions_* / expected_dasha_build_ids as unknown).
SETTLED-1 mechanical guard (steward M20261002T224436-82bd; Suvarṇa addendum 6) — the pre-flight REFUSES unless, read-only for the chart: (ii) `chart_dashas` has exactly ONE distinct build_id (whole
table, every system); (iii) the complete shape — 45 non-scope system×ayanāṃśa partitions + 1 scope-cap; (iv) `asset_throughput.state` = 'lit' for ga_dashas and ga_positions; (v) that single
build id equals the SETTLED-1 build id (and --apply sets the constant to it and asserts so).

Exit codes: 0 evidence clean (and applied if asked) · 3 STOP (a stop reason is listed) · 2 usage.
Evidence item (e) — the seven FORENSIC anchors — is supplied by the L1 owner as --forensic-report
(this tool does not recompute foundational chart facts; CLAUDE.md §B); without it the verdict is
'incomplete' and --apply is refused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import time
from decimal import Decimal, InvalidOperation
import uuid
import os
import re
import statistics
import tempfile
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
SIDECAR = HERE.parents[2]
sys.path.insert(0, str(SIDECAR))

from services.gochara_grammar import dasha_data as DD                       # noqa: E402
from services.gochara_rules import permission as PERM                       # noqa: E402

LEVEL_NAME = {1: "MD", 2: "AD", 3: "PD", 4: "L4"}
MIN_TOLERANCE_SECONDS = 1
WINDOW_START_ISO, WINDOW_END_ISO = "1950-01-01T00:00:00Z", "2100-12-31T00:00:00Z"      # the writer's calculation window (ga_dashas_writer.py:96–97): the first/last row of every level is CLIPPED to it
CANONICAL_SYSTEM, CANONICAL_AYANAMSHA = "vimshottari", "lahiri_chitrapaksha"
LEVELS_IN_SCOPE = (1, 2, 3)          # Vimśottarī Lahiri MD/AD/PD only (steward M20261002T230554 / Suvarṇa addendum 7): lords and row counts must be EQUAL here; level 4 is out of scope


# ── pure helpers (unit-tested) ───────────────────────────────────────────────
def _t(s) -> datetime:
    """Any instant -> UTC. A `datetime` object without tzinfo is UTC by this tool's convention (psycopg returns aware ones); a STRING without an offset is REFUSED by name — `fromisoformat(...).astimezone()` would
    read it as MACHINE-LOCAL time (an IST machine turns `15:50:23` into `10:20:23Z`; Fable F-R19-4). Every stored or imported instant must carry `Z` or an explicit offset."""
    if isinstance(s, datetime):
        return s.astimezone(timezone.utc) if s.tzinfo else s.replace(tzinfo=timezone.utc)
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError(f"instant without an offset: {s!r} (an ISO instant must end in 'Z' or carry an explicit offset such as '+00:00'; it is never read as local time)")
    return d.astimezone(timezone.utc)


def iso(s) -> str:
    """WHOLE-SECOND UTC `…Z` — ONLY for the permission.py literals (their lexicographic comparison needs this form). Never used to measure."""
    return _t(s).strftime("%Y-%m-%dT%H:%M:%SZ")


def full_iso(s) -> str:
    """FULL-precision UTC `…Z` (microseconds kept when present) — captures and shift measurement (Codex R17-3: truncating before measuring can move an out-of-tolerance observation inside the interval)."""
    t = _t(s)
    return t.strftime("%Y-%m-%dT%H:%M:%S") + (f".{t.microsecond:06d}" if t.microsecond else "") + "Z"


def norm_rows(rows: list[dict]) -> list[dict]:
    """DB rows -> plain strings: UUIDs as text, instants as FULL-precision UTC `…Z` (the permission literals are whole-second-formatted separately, at --apply only)."""
    return [{**r, "dasha_row_id": str(r["dasha_row_id"]),
             "parent_row_id": None if r.get("parent_row_id") is None else str(r["parent_row_id"]),
             "start_iso": full_iso(r["start_iso"]), "end_iso": full_iso(r["end_iso"]),
             "build_id": None if r.get("build_id") is None else str(r["build_id"]),            # a real row carries a uuid.UUID — JSON-serialisable text only
             "level_n": int(r["level_n"])} for r in rows]


def tree_problems(rows: list[dict], label: str) -> list[str]:
    """Codex R17-4: the §4.0 tree must be WELL-FORMED before any comparison — unique ids; level-1 rows are roots (no parent); a level-n row (n > 1) has a parent that EXISTS at level n−1; no
    self-parenting; no cycle; every row reachable from a root; every in-scope row indexed EXACTLY once. A malformed side stops the comparison (a row unreachable from a root would otherwise
    vanish from the row-count and lord-change checks)."""
    out: list[str] = []
    by_id: dict[str, dict] = {}
    for r in rows:
        if r["dasha_row_id"] in by_id:
            out.append(f"{label}: duplicate row id {r['dasha_row_id']}")
        by_id[r["dasha_row_id"]] = r
        if int(r["level_n"]) not in LEVELS_IN_SCOPE:
            out.append(f"{label}: row {r['dasha_row_id']} is at level {r['level_n']}, outside the in-scope levels {list(LEVELS_IN_SCOPE)}")
    for r in rows:
        lv, pid = int(r["level_n"]), r.get("parent_row_id")
        if lv == 1:
            if pid is not None:
                out.append(f"{label}: level-1 row {r['dasha_row_id']} has a parent ({pid}); a level-1 row is a root")
            continue
        if pid is None:
            out.append(f"{label}: level-{lv} row {r['dasha_row_id']} has NO parent (it is unreachable from any root)")
        elif pid == r["dasha_row_id"]:
            out.append(f"{label}: row {pid} is its own parent")
        elif pid not in by_id:
            out.append(f"{label}: level-{lv} row {r['dasha_row_id']} has a missing parent {pid}")
        elif int(by_id[pid]["level_n"]) != lv - 1:
            out.append(f"{label}: row {r['dasha_row_id']} (level {lv}) has a parent at level {by_id[pid]['level_n']}, expected {lv - 1}")
    # cycles / reachability: walk every row up to a root with a bound
    for r in rows:
        seen, cur = set(), r
        while cur is not None and cur.get("parent_row_id") is not None:
            if cur["dasha_row_id"] in seen:
                out.append(f"{label}: a parent cycle through {cur['dasha_row_id']}"); break
            seen.add(cur["dasha_row_id"])
            cur = by_id.get(cur["parent_row_id"])
    if not out and len(index_paths(rows)) != len(rows):
        out.append(f"{label}: {len(rows)} rows but {len(index_paths(rows))} reachable and indexed — every in-scope row must be indexed exactly once")
    return out


def level_totals(rows: list[dict]) -> dict[int, int]:
    return {lv: sum(1 for r in rows if int(r["level_n"]) == lv) for lv in LEVELS_IN_SCOPE}


def index_paths(rows: list[dict]) -> dict[tuple, dict]:
    """(level, path) -> row, where path = the chain of (LORD, occurrence) from the MD down. Rows are paired ONLY by this STRUCTURE — never by `dasha_row_id` (every id changes at S-L1:
    delete + re-insert) and never by a bare sibling index: within a parent the children are keyed by their LORD (the Vimśottarī order is fixed), the n-th child of that lord being `(lord, n)`.
    Siblings are ordered by start. Rows must be one build, §4.0-canonical."""
    by_parent: dict = {}
    for r in rows:
        by_parent.setdefault(r.get("parent_row_id"), []).append(r)
    for sibs in by_parent.values():
        sibs.sort(key=lambda r: _t(r["start_iso"]))
    out: dict[tuple, dict] = {}

    def walk(parent_id, path):
        seen: dict[str, int] = {}
        for r in by_parent.get(parent_id, []):
            lord = r["lord_graha"]
            k = seen.get(lord, 0)
            seen[lord] = k + 1
            p = path + ((lord, k),)
            out[(int(r["level_n"]), p)] = r
            walk(r["dasha_row_id"], p)
    walk(None, ())
    return out


def subtree_refusals(old_idx: dict, new_idx: dict) -> list[dict]:
    """Suvarṇa's hardening (steward M20261003T003504-c27f): where a parent's CHILD SET differs old vs new (a different count, or a different lord sequence) that subtree is REFUSED and LISTED —
    never best-guessed. Reported at the highest differing parent only (the deeper differences are its consequence). Any count difference at levels 1–3 is UNEXPECTED and stops the whole re-pin."""
    def children(idx):
        out: dict[tuple, list] = {}
        for (lv, path) in idx:
            out.setdefault(path[:-1], []).append((lv, path[-1][0]))
        return {k: [x for x in v] for k, v in out.items()}
    oc, nc = children(old_idx), children(new_idx)
    diffs = [{"parent": p, "old": [l for _, l in oc.get(p, [])], "new": [l for _, l in nc.get(p, [])]} for p in sorted(set(oc) | set(nc), key=lambda p: (len(p), p))
             if [l for _, l in oc.get(p, [])] != [l for _, l in nc.get(p, [])]]
    refused: list[dict] = []
    for d in diffs:
        if not any(d["parent"][:len(r["parent"])] == r["parent"] and len(d["parent"]) > len(r["parent"]) for r in refused):
            refused.append(d)
    return refused


def under_refused(key: tuple, refusals: list[dict]) -> bool:
    lv, path = key
    return any(path[:len(r["parent"])] == r["parent"] and len(path) > len(r["parent"]) for r in refusals)


def integrity(rows: list[dict]) -> dict:
    ids = {r["dasha_row_id"] for r in rows}
    orphans = [r["dasha_row_id"] for r in rows if r.get("parent_row_id") is not None and r["parent_row_id"] not in ids]
    keys: dict = {}
    dup = 0
    for r in rows:
        k = (r["level_n"], r.get("parent_row_id"), r["start_iso"], r["lord_graha"])
        dup += k in keys
        keys[k] = 1
    return {"rows": len(rows), "orphans": orphans, "duplicates": dup,
            "by_level": {lv: sum(1 for r in rows if int(r["level_n"]) == lv) for lv in sorted({int(r["level_n"]) for r in rows})}}


def match(old: dict, new: dict) -> dict:
    keys_old, keys_new = set(old), set(new)
    return {"matched": sorted(keys_old & keys_new), "only_old": sorted(keys_old - keys_new), "only_new": sorted(keys_new - keys_old)}


def edge_clipped(row: dict, side: str) -> bool:
    """Is this row's start/end edge CLIPPED to the writer's window? True when the writer flagged it (`trunc_start` / `trunc_end`) OR the instant IS the window bound. The flags alone are not enough:
    the writer passes them only at levels 1–2 — every level-3 row reads False although its first/last row is clipped at the same bounds (the independent verifier documents it as a confirmed
    engine quirk) — so the bound instant is the cross-check that catches those."""
    flag = bool(row.get("trunc_start" if side == "start" else "trunc_end"))
    bound = WINDOW_START_ISO if side == "start" else WINDOW_END_ISO
    return flag or _t(row["start_iso" if side == "start" else "end_iso"]) == _t(bound)


def edge_report(old: dict, new: dict, matched: list) -> dict:
    """Window-edge accounting for the matched pairs: per level the number of edges clipped on BOTH builds (EXCLUDED from the shift statistics — they must not move) and the PROBLEMS: an edge clipped on
    ONE build only ('window-edge status changed'), a clipped edge whose instant moved, a flag set where the instant is not the bound."""
    clipped: dict[int, dict[str, int]] = {}
    problems: list[str] = []
    for k in matched:
        lv = k[0]
        for side in ("start", "end"):
            o, n = old[k], new[k]
            co, cn = edge_clipped(o, side), edge_clipped(n, side)
            bound = _t(WINDOW_START_ISO if side == "start" else WINDOW_END_ISO)
            for label, row, c in (("old", o, co), ("new", n, cn)):
                if bool(row.get("trunc_start" if side == "start" else "trunc_end")) and _t(row["start_iso" if side == "start" else "end_iso"]) != bound:
                    problems.append(f"{LEVEL_NAME.get(lv, lv)} {side} edge of the {label} row is FLAGGED truncated but its instant is not the window bound")
            if co and cn:
                clipped.setdefault(lv, {"start": 0, "end": 0})[side] += 1
                if _t(o["start_iso" if side == "start" else "end_iso"]) != _t(n["start_iso" if side == "start" else "end_iso"]):
                    problems.append(f"{LEVEL_NAME.get(lv, lv)} {side} edge is clipped on both builds but its instant MOVED")
            elif co != cn:
                problems.append(f"window-edge status changed: the {LEVEL_NAME.get(lv, lv)} {side} edge of {k[1]} is clipped on the {'old' if co else 'new'} build only")
    return {"clipped": {lv: clipped[lv] for lv in sorted(clipped)}, "problems": sorted(set(problems))}


def shift_stats(old: dict, new: dict, matched: list) -> dict:
    """Per-level start/end shift statistics over the UNCLIPPED edges only — an edge clipped to the window on BOTH builds shifts 0 s by construction and is excluded (see `edge_report`); a side with
    no unclipped measurement is absent from the result (and `shift_problems` refuses it)."""
    per: dict[int, dict[str, list[float]]] = {}
    for k in matched:
        lv = k[0]
        d = per.setdefault(lv, {"start": [], "end": []})
        for side in ("start", "end"):
            key = "start_iso" if side == "start" else "end_iso"
            if edge_clipped(old[k], side) and edge_clipped(new[k], side):
                continue
            d[side].append((_t(new[k][key]) - _t(old[k][key])).total_seconds())
    return {lv: {side: {"min": min(v), "max": max(v), "mean": statistics.fmean(v), "n": len(v)} for side, v in d.items() if v}
            for lv, d in sorted(per.items())}


def lords_at(rows: list[dict], t: str) -> dict:
    """MD/AD/PD lords at instant t (half-open [start,end), parent-linked)."""
    tt, out, parent = _t(t), {}, None
    for lv in (1, 2, 3):
        hit = [r for r in rows if int(r["level_n"]) == lv and r.get("parent_row_id") == parent
               and _t(r["start_iso"]) <= tt < _t(r["end_iso"])]
        if len(hit) != 1:
            out[LEVEL_NAME[lv]] = None if not hit else "CONFLICT"
            break
        out[LEVEL_NAME[lv]] = hit[0]["lord_graha"]
        parent = hit[0]["dasha_row_id"]
    return out


def lord_flips(old_rows: list[dict], new_rows: list[dict], instants: list[str]) -> list[dict]:
    flips = []
    for t in instants:
        a, b = lords_at(old_rows, t), lords_at(new_rows, t)
        if a != b:
            flips.append({"instant": t, "old": a, "new": b})
    return flips


def fetch_vimshottari_builds(conn, chart_id: str, ayanamsha_id: str = "lahiri_chitrapaksha") -> dict[str, int]:
    """READ-ONLY: every Vimśottarī build present for the chart at the Lahiri levels 1–3, ANY tier -> row count. A mixed state (more than one build) is refused by the writer and the verifier since
    `699638fbe`; the re-pin proceeds only when exactly ONE build, the SETTLED-1 one, is present — G6."""
    cur = conn.cursor()
    cur.execute("SELECT build_id::text, count(*) FROM public.chart_dashas WHERE chart_id = %s AND system_id = 'vimshottari' AND ayanamsha_id = %s AND level_n IN (1, 2, 3) GROUP BY 1 ORDER BY 1",
                (chart_id, ayanamsha_id))
    return {str(b): int(n) for b, n in cur.fetchall()}


EXPECTED_NON_SCOPE_PARTITIONS, EXPECTED_SCOPE_PARTITIONS = 45, 1       # 9 systems × 5 ayanāṃśas + the scope-cap partition (Suvarṇa addendum 6)


def fetch_preflight_facts(conn, chart_id: str) -> dict:
    """READ-ONLY (steward M20261002T224436-82bd): the SETTLED-1 mechanical guard's facts for the chart — (ii) the distinct build ids across the WHOLE of `chart_dashas`; (iii) the shape: distinct
    (system, ayanāṃśa) partitions, non-scope and scope-cap; (iv) `asset_throughput.state` of `ga_dashas` and `ga_positions`."""
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT build_id::text FROM public.chart_dashas WHERE chart_id = %s ORDER BY 1", (chart_id,))
    builds = [str(r[0]) for r in cur.fetchall()]
    cur.execute("SELECT count(*) FILTER (WHERE system_id <> 'scope_cap'), count(*) FILTER (WHERE system_id = 'scope_cap') "
                "FROM (SELECT DISTINCT system_id, ayanamsha_id FROM public.chart_dashas WHERE chart_id = %s) p", (chart_id,))
    non_scope, scope = cur.fetchone()
    cur.execute("SELECT asset_id, state FROM public.asset_throughput WHERE chart_id = %s AND asset_id IN ('ga_dashas', 'ga_positions') ORDER BY 1", (chart_id,))
    return {"builds": builds, "non_scope": int(non_scope), "scope": int(scope), "throughput": {str(a): str(st) for a, st in cur.fetchall()}}


def preflight_problems(facts: dict, new_id: str, pinned_constant: str | None = None) -> list[str]:
    """G6 closure, exact form (steward M20261002T224436-82bd; Suvarṇa addendum 6) — every one REFUSES: (ii) exactly ONE distinct build_id across chart_dashas; (iii) the complete shape, 45 non-scope
    system×ayanāṃśa partitions + 1 scope-cap; (iv) `ga_dashas` and `ga_positions` are `lit` for the chart; (v) that single build id equals the SETTLED-1 build id (the re-pin constant is set to it
    by --apply, which asserts it)."""
    out = []
    if len(facts["builds"]) != 1:
        out.append(f"(ii) chart_dashas holds {len(facts['builds'])} distinct build_id(s) {facts['builds']}; exactly ONE is required (a part-failed or unfinished L1 rebuild leaves a mix)")
    elif facts["builds"][0] != new_id:
        out.append(f"(v) the single chart_dashas build {facts['builds'][0]} is not the SETTLED-1 build {new_id}")
    if (facts["non_scope"], facts["scope"]) != (EXPECTED_NON_SCOPE_PARTITIONS, EXPECTED_SCOPE_PARTITIONS):
        out.append(f"(iii) incomplete shape: {facts['non_scope']} non-scope + {facts['scope']} scope-cap partition(s); expected {EXPECTED_NON_SCOPE_PARTITIONS} + {EXPECTED_SCOPE_PARTITIONS}")
    for asset in ("ga_dashas", "ga_positions"):
        st = facts["throughput"].get(asset)
        if st != "lit":
            out.append(f"(iv) asset_throughput.state of {asset} is {st!r}, not 'lit'")
    return out


def fetch_verifier_builds(conn, chart_id: str) -> list[str]:
    """READ-ONLY: the verifier's OWN predicate (`inventory_verifier.validate_consumed_dasha_population`): the distinct build ids — NULL included — of EVERY Vimśottarī / Lahiri row of the chart, at ALL
    levels and ALL tiers. The verifier refuses (`dasha_builds_mixed` / `dasha_build_not_pinned`) unless this is exactly ONE build and it is the pin; the G6(a) check above reads levels 1–3 only."""
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT coalesce(build_id::text, 'NULL') FROM public.chart_dashas WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s ORDER BY 1",
                (chart_id, CANONICAL_SYSTEM, CANONICAL_AYANAMSHA))
    return [str(r[0]) for r in cur.fetchall()]


def verifier_build_problems(builds: list[str], new_id: str) -> list[str]:
    """Mirror of the verifier's refusal (steward ST-REPIN-PATCH-GO): every Vimśottarī / Lahiri row of the chart — all levels, all tiers, NULL included — is ONE build and it is the SETTLED-1 build, so the tool
    cannot say CLEAN where the verifier would refuse after the re-pin. NEVER relaxed."""
    if builds == [new_id]:
        return []
    return [f"(vi) the verifier's own predicate (every Vimśottarī / Lahiri row of the chart, ALL levels and tiers, NULL build included) sees build(s) {builds}; exactly ONE — the SETTLED-1 build {new_id} — is required "
            "or the verifier refuses (dasha_builds_mixed / dasha_build_not_pinned) after the re-pin"]


def build_problems(builds: dict[str, int], new_id: str) -> list[str]:
    """G6 (a): exactly ONE Vimśottarī build exists for the chart (Lahiri, levels 1–3) and it is the SETTLED-1 build."""
    if set(builds) == {new_id}:
        return []
    return [f"chart_dashas holds Vimśottarī build(s) {sorted(builds)} (Lahiri levels 1–3); exactly ONE — the SETTLED-1 build {new_id} — must exist (G6: a mixed L1 state is refused by the writer and the verifier, and the re-pin proceeds only on a settled one)"]


def _rows_digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def selection_contract() -> dict:
    """The selection a capture is MADE UNDER — recorded in the capture and bound into its checksum: the Vimśottarī / Lahiri / `two_pass_verified` read of levels 1–3 and the ten natal longitudes."""
    return {"system_id": CANONICAL_SYSTEM, "ayanamsha_id": CANONICAL_AYANAMSHA, "tier": PERM.DASHA_READ_CONTRACT["tier"], "levels": list(LEVELS_IN_SCOPE),
            "natal": {"category": "graha_position", "key": "longitude_sidereal", "ayanamsha_id": CANONICAL_AYANAMSHA, "subjects": sorted(NATAL_SUBJECTS)}}


def _capture_digest(chart_id: str, build_id: str, rows: list[dict], natal: list[dict] | None) -> str:
    """SHA-256 of the canonical JSON of the capture's IDENTITY (chart, pinned build, selection contract) AND its data (rows, natal) — Codex R18-1: the chart/build/selection can no longer be edited
    without invalidating it. The timing/provenance in `meta` is deliberately outside it, so the same L1 state gives the same digest on every capture."""
    body = {"chart_id": chart_id, "build_id": build_id, "selection": selection_contract(), "rows": rows, "natal": natal or []}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


_ROW_STR_KEYS = ("dasha_row_id", "lord_graha", "start_iso", "end_iso", "system_id", "verification_pass_status", "build_id")


def chart_id_problem(value) -> str | None:
    """Codex v1.8 P1-4: a chart id is canonical lower-case hyphenated UUID text — validated before dispatch (CLI), in a W0 file and in capture validation, never merely compared."""
    if not isinstance(value, str) or not value:
        return f"chart id {value!r} is not a string"
    try:
        ok = str(uuid.UUID(value)) == value
    except ValueError:
        ok = False
    return None if ok else f"chart id {value!r} is not canonical UUID text (lower-case, hyphenated)"


def strict_rows_problems(rows, label: str = "rows") -> list[str]:
    """Codex v1.7 P1-1: ONE strict row schema, applied BEFORE any coercion (`int(...)`, `_t(...)`) to every row source — a loaded capture, both acquisitions and the W0 import all end in
    `validate_capture`. Per row: an object; `level_n` an INTEGER (not a bool, a float, a string); `dasha_row_id` / `lord_graha` / `start_iso` / `end_iso` / `system_id` /
    `verification_pass_status` / `build_id` non-empty STRINGS; ids canonical UUID text; `start_iso` / `end_iso` strings carrying an explicit offset, start strictly before end; `parent_row_id` a UUID
    string or null; `trunc_start` / `trunc_end` booleans or null; the optional `index` an integer and `merged_row_ids` a list of strings. NOTHING is converted — a malformed value is a named problem."""
    if not isinstance(rows, list):
        return [f"{label}: not a list"]
    out: list[str] = []
    for i, r in enumerate(rows):
        who = f"{label}[{i}]"
        if not isinstance(r, dict):
            out.append(f"{who}: not an object"); continue
        lv = r.get("level_n")
        if isinstance(lv, bool) or not isinstance(lv, int):
            out.append(f"{who}: level_n must be an integer (got {lv!r})")
        for k in _ROW_STR_KEYS:
            if not isinstance(r.get(k), str) or not r[k].strip():
                out.append(f"{who}: {k} must be a non-empty string (got {r.get(k)!r})")
        for k in ("dasha_row_id", "parent_row_id", "build_id"):
            v = r.get(k)
            if isinstance(v, str) and v.strip():
                try:
                    uuid.UUID(v)
                except ValueError:
                    out.append(f"{who}: {k} is not a UUID ({v!r})")
        if r.get("parent_row_id") is not None and not isinstance(r.get("parent_row_id"), str):
            out.append(f"{who}: parent_row_id must be a string or null (got {r.get('parent_row_id')!r})")
        for k in ("trunc_start", "trunc_end"):
            if r.get(k) is not None and not isinstance(r.get(k), bool):                # absent / null = not flagged (as `edge_clipped` reads it); anything else but a boolean is refused
                out.append(f"{who}: {k} must be true, false or null (got {r.get(k)!r})")
        if "index" in r and (isinstance(r["index"], bool) or not isinstance(r["index"], int)):
            out.append(f"{who}: index must be an integer (got {r['index']!r})")
        if "merged_row_ids" in r and not (isinstance(r["merged_row_ids"], list) and all(isinstance(x, str) for x in r["merged_row_ids"])):
            out.append(f"{who}: merged_row_ids must be a list of strings (got {r['merged_row_ids']!r})")
        try:
            a_, b_ = _t(r["start_iso"]), _t(r["end_iso"])
            if not a_ < b_:
                out.append(f"{who}: start_iso is not before end_iso")
        except (KeyError, TypeError, ValueError, AttributeError):
            out.append(f"{who}: start_iso / end_iso are not instants with an explicit offset ({r.get('start_iso')!r}, {r.get('end_iso')!r})")
    return out


def strict_natal_problems(natal) -> list[str]:
    """Codex v1.7 P1-1: the same discipline for the ten natal rows — objects; `fact_subject`, `fact_id`, `tier` non-empty strings; `build_id` a string or null; `longitude` a FINITE number or numeric
    text in [0, 360) — never NaN, infinity, an object, a bool or empty."""
    if not isinstance(natal, list):
        return ["natal: not a list"]
    out: list[str] = []
    for i, n in enumerate(natal):
        who = f"natal[{i}]"
        if not isinstance(n, dict):
            out.append(f"{who}: not an object"); continue
        for k in ("fact_subject", "fact_id", "tier"):
            if not isinstance(n.get(k), str) or not n[k].strip():
                out.append(f"{who}: {k} must be a non-empty string (got {n.get(k)!r})")
        if n.get("build_id") is not None and not isinstance(n.get("build_id"), str):
            out.append(f"{who}: build_id must be a string or null (got {n.get('build_id')!r})")
        v = n.get("longitude")
        ok = False
        if isinstance(v, bool) or v is None:
            ok = False
        elif isinstance(v, float):
            ok = math.isfinite(v) and not (v == 0.0 and math.copysign(1.0, v) < 0) and 0.0 <= v < 360.0     # a JSON `-1e-9999` arrives here as -0.0 (lossy at parse): a signed zero is refused
        elif isinstance(v, int):
            ok = 0 <= v < 360
        elif isinstance(v, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", v):             # plain ASCII decimal text only: no sign, space, underscore, Unicode digit, NaN or hex
            try:
                d_ = Decimal(v)                                                                              # EXACT: no float conversion, so `-1e-9999` stays a negative number
            except InvalidOperation:
                d_ = None
            ok = d_ is not None and d_.is_finite() and not d_.is_signed() and Decimal(0) <= d_ < Decimal(360)   # signed zero / any negative is refused
        if not ok:
            out.append(f"{who}: longitude must be a finite number in [0, 360) (got {v!r})")
    return out


def row_contract_problems(rows: list[dict], build_id: str, label: str) -> list[str]:
    """EVERY row against the build and the read contract: its own `build_id` is the expected build (no foreign or mixed build), system Vimśottarī, tier `two_pass_verified`, level 1–3 (Codex R18-1).
    NOT checkable per row: `ayanamsha_id` — the §4.0 reader does not return it. The ayanāṃśa is established by the SQL predicate of the capture, recorded in the selection contract (bound into the checksum) and
    cross-checked indirectly: the ten `permission.py` reference ids exist in the capture with their lords, which a wrong-ayanāṃśa file would not satisfy."""
    out: list[str] = []
    tier = PERM.DASHA_READ_CONTRACT["tier"]
    for r in rows:
        try:
            b = canon_uuid(r.get("build_id"))
        except ValueError:
            b = None
        if b != build_id:
            out.append(f"{label}: row {r.get('dasha_row_id')} carries build {r.get('build_id')!r}, expected {build_id} (a foreign or mixed build)")
        if r.get("system_id") != CANONICAL_SYSTEM:
            out.append(f"{label}: row {r.get('dasha_row_id')} is system {r.get('system_id')!r}, expected {CANONICAL_SYSTEM!r}")
        if r.get("verification_pass_status") != tier:
            out.append(f"{label}: row {r.get('dasha_row_id')} is tier {r.get('verification_pass_status')!r}, expected {tier!r}")
        try:
            lv = int(r["level_n"])
        except (KeyError, TypeError, ValueError):
            lv = None
        if lv not in LEVELS_IN_SCOPE:
            out.append(f"{label}: row {r.get('dasha_row_id')} is level {r.get('level_n')!r}, expected one of {list(LEVELS_IN_SCOPE)}")
    return out


def build_capture(chart_id: str, build_id: str, rows: list[dict], natal: list[dict] | None, meta: dict | None = None) -> dict:
    """The capture envelope: {chart_id, build_id, selection, rows, natal, meta, sha256} — `sha256` binds identity + selection + rows + natal (see `_capture_digest`); `meta` records provenance (tool commit,
    per-level counts, the separate daśā and natal build ids, the census from the same snapshot, isolation, snapshot, timing)."""
    meta = dict(meta or {})
    meta.setdefault("counts_by_level", {str(k): v for k, v in level_totals(rows).items()})
    meta.setdefault("dasha_build_ids", sorted({str(r.get("build_id")) for r in rows}))
    meta.setdefault("natal_build_ids", sorted({str(n.get("build_id")) for n in (natal or [])}))
    return {"chart_id": chart_id, "build_id": build_id, "selection": selection_contract(), "rows": rows, "natal": natal or [], "meta": meta, "sha256": _capture_digest(chart_id, build_id, rows, natal)}


def validate_capture(d: dict, chart_id: str, build_id: str) -> list[str]:
    """THE ONE validation, run at ACQUISITION (before anything is written) AND at LOAD (Codex R18-1/R18-2): identity, selection, checksum over identity + data, every row against the build and the
    read contract, a well-formed tree, every reference-row id present with its lord, flags consistent, at least one UNCLIPPED start and end at every in-scope level (R19-2), the ten natal rows, and the
    recorded per-level counts."""
    out: list[str] = []
    if not isinstance(d, dict) or not d.get("rows"):
        return ["the capture is empty or not an object"]
    bad_chart = chart_id_problem(d.get("chart_id")) or chart_id_problem(chart_id)
    if bad_chart:
        return out + [bad_chart]
    if d.get("chart_id") != chart_id:
        out.append(f"the capture is for chart {d.get('chart_id')!r}, expected {chart_id}")
    try:
        cb = canon_uuid(d.get("build_id"))
    except ValueError:
        cb = None
    if cb != build_id:
        out.append(f"the capture envelope names build {d.get('build_id')!r}, expected the pinned {build_id}")
    if d.get("selection") != selection_contract():
        out.append("the capture's selection contract is not the expected one (Vimśottarī / Lahiri / two_pass_verified / levels 1–3 / the ten natal subjects)")
    if d.get("sha256") != _capture_digest(d.get("chart_id"), d.get("build_id"), d["rows"], d.get("natal")):
        out.append("the capture's sha256 does not match its identity, selection, rows and natal longitudes")
    strict = strict_rows_problems(d["rows"], "captured old rows") + strict_natal_problems(d.get("natal") or [])
    if strict:                                                                            # Codex v1.7 P1-1: refuse BEFORE any int()/_t() coercion; the checksum is not evidence of well-formedness
        return out + strict[:12]
    out += row_contract_problems(d["rows"], build_id, "captured old rows")
    try:
        out += capture_problems(d["rows"], reference=(build_id == PERM.DASHA_READ_CONTRACT["build_id"])) + coverage_problems(d["rows"]) + natal_problems(d.get("natal") or [])
    except (ValueError, KeyError, TypeError) as exc:
        out.append(f"the capture's rows cannot be read ({exc.__class__.__name__}: {exc})")                       # e.g. an instant without an offset: a named STOP, never a traceback
    counts = (d.get("meta") or {}).get("counts_by_level")
    if counts is not None and counts != {str(k): v for k, v in level_totals(d["rows"]).items()}:
        out.append("the capture's recorded per-level counts do not match its rows")
    return out


def write_atomic(path, text: str) -> None:
    """The ONLY way this tool writes a file (Codex v1.6): the text is encoded as STRICT UTF-8 FIRST (a lone surrogate or any unencodable character raises ValueError before the disk is touched), the destination
    must be a (new or existing) FILE in an EXISTING directory, and the bytes go to a temp file in that directory that is `os.replace`d onto the destination only after a successful flush + fsync — so an
    interrupted or refused write never leaves a half-written file under the real name."""
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"the text for {path} cannot be encoded as UTF-8 (a lone surrogate or an unencodable character); nothing written") from None
    p = Path(path)
    if p.is_dir():
        raise ValueError(f"{path} is a directory, not a file; nothing written")
    if not p.parent.is_dir():
        raise ValueError(f"the directory of {path} does not exist; nothing written")
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=p.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def output_path_problem(path) -> str | None:
    """VALIDATION-PHASE check of an output destination (no write): not a directory, directory exists."""
    p = Path(path)
    if p.is_dir():
        return f"output path {path} is a directory, not a file"
    if not p.parent.is_dir():
        return f"the directory of output path {path} does not exist"
    return None


def write_capture(path: str, d: dict) -> str:
    """Writes a validated capture envelope; returns the DATA sha256. The whole-file checksum is a SEPARATE fact (printed by the caller from the written bytes; keep it with the file)."""
    write_atomic(path, json.dumps(d, indent=1, sort_keys=True))
    return d["sha256"]


def _no_duplicate_keys(pairs):
    """`object_pairs_hook`: a JSON object with a repeated key is REFUSED at EVERY depth (plain `json` keeps the last value silently, so a second `tolerance_seconds` could hide the first, or a second
    `expected_shift_seconds` an earlier object's typo — Codex v1.3)."""
    out: dict = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key {k!r} (a repeated key would let the last value silently win)")
        out[k] = v
    return out


def _refuse_json_constant(token: str):
    """`parse_constant`: NaN / Infinity / -Infinity tokens are REFUSED at parse time (they are not JSON)."""
    raise ValueError(f"the JSON constant {token} is not accepted")


def _require_utf8_strings(node) -> None:
    """Every string in the document — keys and values, at any depth — must be encodable as UTF-8 (a JSON `\\ud800` escape decodes to a lone surrogate that no report, capture or evidence file could carry; Codex v1.6)."""
    stack = [node]
    while stack:
        n = stack.pop()
        if isinstance(n, str):
            try:
                n.encode("utf-8")
            except UnicodeEncodeError:
                raise ValueError("a string in the document contains a lone surrogate (not encodable as UTF-8)") from None
        elif isinstance(n, dict):
            stack.extend(n.keys()); stack.extend(n.values())
        elif isinstance(n, list):
            stack.extend(n)


def strict_json_loads(text: str):
    """The ONE JSON reader for every operator-supplied file (the SETTLED-1 notice, the rulings, the W0 baseline, the capture envelope): duplicate keys at any depth and NaN/Infinity tokens are refused."""
    try:
        doc = json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_refuse_json_constant)
        _require_utf8_strings(doc)
        return doc
    except ValueError:
        raise                                                  # malformed JSON, duplicate keys, NaN/Infinity tokens, bad UTF-8: already the named refusal
    except RecursionError:                                     # a hostile document nested ~100,000 deep (Codex v1.4): a refusal, never a traceback
        raise ValueError("the JSON is nested too deeply to be read safely") from None
    except MemoryError:
        raise ValueError("the JSON is too large to be read safely") from None
    except Exception as exc:                                   # any other parser failure
        raise ValueError(f"the JSON could not be parsed ({type(exc).__name__})") from None


def file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_capture_full(path: str, chart_id: str, build_id: str) -> dict:
    d = strict_json_loads(Path(path).read_text(encoding="utf-8"))
    bad = validate_capture(d, chart_id, build_id)
    if bad:
        raise ValueError("the captured old-rows file is invalid or malformed: " + "; ".join(bad[:8]))                  # Codex R17-4 / R18-1: a malformed or self-inconsistent capture STOPS the comparison
    return d


def load_capture(path: str, chart_id: str, build_id: str) -> list[dict]:
    return load_capture_full(path, chart_id, build_id)["rows"]


class ReaderRefused(Exception):
    """The §4.0 reader cannot be trusted for this read: a STOP by NAME (never by 'no rows')."""


class _LogCollector(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def read_truncation(conn, chart_id: str, build_id: str) -> dict:
    """`dasha_row_id -> (is_truncated_at_window_start, is_truncated_at_window_end)` for the build's Vimśottarī Lahiri levels 1–3 — a SECOND select in the SAME transaction (the reader's columns do not
    carry the flags)."""
    cur = conn.execute("SELECT dasha_row_id::text, is_truncated_at_window_start, is_truncated_at_window_end FROM public.chart_dashas"
                       " WHERE chart_id = %s AND build_id = %s::uuid AND system_id = %s AND ayanamsha_id = %s AND level_n IN (1, 2, 3)",
                       (chart_id, build_id, CANONICAL_SYSTEM, CANONICAL_AYANAMSHA))
    return {str(r[0]): (bool(r[1]), bool(r[2])) for r in cur.fetchall()}


def read_levels(conn, chart_id: str, build_id: str, label: str) -> list[dict]:
    """The Vimśottarī Lahiri levels 1–3 of ONE build through the REAL §4.0 reader — with three guards the reader itself does not give (Fable F-R17-1): (1) the connection must be psycopg (v3) — the reader
    calls `conn.execute()` and SWALLOWS any exception (an AttributeError on a psycopg2 connection included) into `[]`; (2) a `DashaReadConflict` is a named refusal; (3) an EMPTY read for any level the tool
    expects is a STOP quoting the reader's own logged reason — an empty read must never look like 'nothing changed'."""
    if not hasattr(conn, "execute"):
        raise ReaderRefused(f"{label}: the connection is not a psycopg (v3) connection (it has no execute()); the §4.0 reader is psycopg3-only and would turn that into an empty read")
    collector = _LogCollector()
    lg = logging.getLogger("services.gochara_grammar.dasha_data")
    old_level = lg.level
    lg.addHandler(collector); lg.setLevel(logging.INFO)
    try:
        try:
            rows = norm_rows(DD.fetch_dasha_periods_multilevel(conn, chart_id, systems=["vimshottari"], build_id=build_id, levels=LEVELS_IN_SCOPE))
        except DD.DashaReadConflict as exc:
            raise ReaderRefused(f"{label}: dasha read conflict for build {build_id}: {exc}") from exc
    finally:
        lg.removeHandler(collector); lg.setLevel(old_level)
    missing = [LEVEL_NAME[lv] for lv in LEVELS_IN_SCOPE if not any(int(r["level_n"]) == lv for r in rows)]
    if not missing:
        flags = read_truncation(conn, chart_id, build_id)
        no_flags = [r["dasha_row_id"] for r in rows if r["dasha_row_id"] not in flags]
        if no_flags:
            raise ReaderRefused(f"{label}: the window-truncation flags are missing for {len(no_flags)} of {len(rows)} rows of build {build_id} (e.g. {no_flags[0]})")
        for r in rows:
            r["trunc_start"], r["trunc_end"] = flags[r["dasha_row_id"]]
    if missing:
        why = f" (reader log: {' | '.join(collector.messages)})" if collector.messages else ""
        extra = " — capture them BEFORE S-L1 with --capture-old and pass --old-rows" if label == "old build" else ""
        raise ReaderRefused(f"{label}: the reader returned NO rows for level(s) {missing} of build {build_id}; an empty read is never 'nothing changed'{why}{extra}")
    return rows


def open_readonly_connection():
    """psycopg (v3), READ ONLY — the connection the §4.0 reader requires."""
    import psycopg
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    conn.read_only = True
    return conn


def canon_uuid(x) -> str:
    """`str(uuid.UUID(x))` — one canonical lower-case hyphenated form before ANY comparison (Fable F-R18-5b)."""
    return str(uuid.UUID(str(x)))


def capture_problems(rows: list[dict], reference: bool = True) -> list[str]:
    """What the COMPARISON will later need, checked at CAPTURE time (Fable F-R18-2) — a useless capture must be found NOW, while a re-capture is still possible: a well-formed tree, every `permission.py`
    reference-row id present with its lord, and no flag set off the window bound."""
    bad = strict_rows_problems(rows, "captured old rows")
    if bad:
        return bad[:12]
    out = tree_problems(rows, "captured old rows")
    by_id = {r["dasha_row_id"]: r for r in rows}
    for ref in (PERM.MD_ROWS + PERM.AD_ROWS + PERM.PD_ROWS if reference else []):       # `reference=False`: a capture of a build the contract does not pin yet (--capture-new before the re-pin)
        r = by_id.get(ref["row_id"])
        if r is None:
            out.append(f"reference row {ref['row_id']} ({ref['level']} {ref['lord']}) is NOT in the capture")
        elif r["lord_graha"] != ref["lord"]:
            out.append(f"reference row {ref['row_id']}: lord {r['lord_graha']} in the capture, {ref['lord']} in permission.py")
    for r in rows:
        for side in ("start", "end"):
            if bool(r.get("trunc_start" if side == "start" else "trunc_end")) and _t(r["start_iso" if side == "start" else "end_iso"]) != _t(WINDOW_START_ISO if side == "start" else WINDOW_END_ISO):
                out.append(f"row {r['dasha_row_id']}: flagged truncated at the window {side} but its {side} instant is not the window bound")
    return out


def coverage_problems(rows: list[dict]) -> list[str]:
    """Codex R19-2: a baseline that can NEVER support a clean comparison is refused at acquisition and at load, while a re-capture is still possible — every in-scope level must have at least ONE UNCLIPPED start
    and ONE UNCLIPPED end (`edge_clipped`: the writer's flag OR the window-bound instant, so unflagged level-3 edges count correctly). If the edges are clipped there is no measurement; if they cease to be clipped
    on the new build, the one-sided-clip rule refuses — waiting for replacement rows cannot repair such a baseline."""
    out: list[str] = strict_rows_problems(rows, "captured old rows")[:12]
    if out:
        return out
    for lv in LEVELS_IN_SCOPE:
        at = [r for r in rows if int(r["level_n"]) == lv]
        for side in ("start", "end"):
            if not any(not edge_clipped(r, side) for r in at):
                out.append(f"level {LEVEL_NAME[lv]} has NO UNCLIPPED {side} boundary in the capture ({len(at)} row(s), every {side} edge clipped to the writer window or the level is empty): no {side} shift can ever be measured there")
    return out


NATAL_SUBJECTS = ("LAGNA", "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")


class NatalRefused(Exception):
    """The ten natal graha_position longitudes could not be read exactly (a STOP by name)."""


def read_natal(conn, chart_id: str) -> list[dict]:
    """The ten L1 `graha_position` / `longitude_sidereal` / Lahiri facts (value, tier, build_id, fact_id) — READ in the SAME transaction as the daśā rows; exactly these ten subjects or a STOP."""
    cur = conn.execute("SELECT fact_id, fact_subject, fact_value_num, verification_pass_status, build_id::text FROM public.chart_facts"
                       " WHERE chart_id = %s AND ayanamsha_id = 'lahiri_chitrapaksha' AND fact_category = 'graha_position' AND fact_key = 'longitude_sidereal' ORDER BY fact_subject", (chart_id,))
    rows = [{"fact_id": str(r[0]), "fact_subject": str(r[1]), "longitude": None if r[2] is None else str(r[2]), "tier": str(r[3]), "build_id": None if r[4] is None else str(r[4])} for r in cur.fetchall()]
    got = sorted(r["fact_subject"] for r in rows)
    if got != sorted(NATAL_SUBJECTS) or any(r["longitude"] is None for r in rows):
        raise NatalRefused(f"the natal read returned subjects {got}, expected exactly {sorted(NATAL_SUBJECTS)} each with a longitude")
    return rows


def natal_problems(natal: list[dict]) -> list[str]:
    bad = strict_natal_problems(natal)
    if bad:
        return bad[:12]
    got = sorted(n.get("fact_subject", "") for n in natal)
    out = [] if got == sorted(NATAL_SUBJECTS) else [f"natal subjects {got}, expected exactly {sorted(NATAL_SUBJECTS)}"]
    out += [f"natal row {n.get('fact_subject')} has no longitude" for n in natal if n.get("longitude") in (None, "")]
    return out


def _w0_normalise(d: dict, old_id: str) -> tuple[list[dict], list[dict], list[str]]:
    """Suvarṇa's W0 file -> (rows, natal, notes). Accepts BOTH the capture's field names and the database column names (Fable F-R19-3): per row `trunc_start` / `trunc_end` OR
    `is_truncated_at_window_start` / `is_truncated_at_window_end` (they must agree when both are present); `system_id`, `verification_pass_status` and `build_id` are FILLED from the selection contract and the
    pinned build when absent (a PRESENT wrong value is still refused by `row_contract_problems`); level-4 (and deeper) rows are DROPPED, counted; natal `longitude` OR `value` OR `fact_value_num`, and `tier`
    OR `verification_pass_status`. Every fill / alias / drop is reported in `notes`. Raises ValueError (a named STOP) on anything it cannot interpret."""
    tier = PERM.DASHA_READ_CONTRACT["tier"]
    notes: list[str] = []
    filled: dict[str, int] = {}
    kept: list[dict] = []
    dropped = 0
    for r in d["rows"]:
        if not isinstance(r, dict):
            raise ValueError("a W0 row is not an object")
        raw_lv = r.get("level_n")
        if isinstance(raw_lv, bool) or not isinstance(raw_lv, int):                    # NO silent conversion: 1.5, "1", true, null, objects are all refused (Codex v1.6)
            raise ValueError(f"W0 row {r.get('dasha_row_id')!r} has no integer level_n (got {raw_lv!r})")
        lv = raw_lv
        for key in ("dasha_row_id", "lord_graha", "start_iso", "end_iso"):
            if not isinstance(r.get(key), str) or not r[key].strip():
                raise ValueError(f"W0 row {r.get('dasha_row_id')!r}: {key} must be a non-empty string (got {r.get(key)!r})")
        for key in ("parent_row_id", "system_id", "verification_pass_status", "build_id"):
            if r.get(key) is not None and not isinstance(r[key], str):
                raise ValueError(f"W0 row {r.get('dasha_row_id')!r}: {key} must be a string or null (got {r[key]!r})")
        for key in ("trunc_start", "trunc_end", "is_truncated_at_window_start", "is_truncated_at_window_end"):
            if r.get(key) is not None and not isinstance(r[key], bool):
                raise ValueError(f"W0 row {r.get('dasha_row_id')!r}: {key} must be true, false or null (got {r[key]!r})")
        if lv > max(LEVELS_IN_SCOPE):
            dropped += 1
            continue
        r = dict(r)
        for key, default in (("system_id", CANONICAL_SYSTEM), ("verification_pass_status", tier), ("build_id", old_id)):
            if r.get(key) is None:
                r[key] = default
                filled[key] = filled.get(key, 0) + 1
        for short, long in (("trunc_start", "is_truncated_at_window_start"), ("trunc_end", "is_truncated_at_window_end")):
            if short in r and long in r and bool(r[short]) != bool(r[long]):
                raise ValueError(f"W0 row {r.get('dasha_row_id')!r}: {short} and {long} disagree")
            if short not in r and long in r:
                r[short] = bool(r[long])
                filled[f"{short} (from {long})"] = filled.get(f"{short} (from {long})", 0) + 1
        kept.append(r)
    natal: list[dict] = []
    for n in d["natal"]:
        if not isinstance(n, dict):
            raise ValueError("a W0 natal entry is not an object")
        lon_key = next((k for k in ("longitude", "value", "fact_value_num") if n.get(k) not in (None, "")), None)
        if lon_key is not None:                                                          # a longitude is a finite number or a numeric string — never an object/list/bool (Codex v1.6)
            lon_v = n[lon_key]
            if isinstance(lon_v, bool) or not (isinstance(lon_v, (int, float)) or isinstance(lon_v, str)):
                raise ValueError(f"W0 natal entry {n.get('fact_subject')!r}: {lon_key} must be a number or a numeric string (got {lon_v!r})")
            try:
                ok_lon = math.isfinite(float(lon_v))
            except (ValueError, OverflowError):
                ok_lon = False
            if not ok_lon:
                raise ValueError(f"W0 natal entry {n.get('fact_subject')!r}: {lon_key} {lon_v!r} is not a finite number")
        for key in ("fact_subject",):
            if not isinstance(n.get(key), str) or not n[key].strip():
                raise ValueError(f"W0 natal entry: {key} must be a non-empty string (got {n.get(key)!r})")
        for key in ("fact_id", "tier", "verification_pass_status", "build_id"):
            if n.get(key) is not None and not isinstance(n[key], (str, int)) or isinstance(n.get(key), bool):
                raise ValueError(f"W0 natal entry {n.get('fact_subject')!r}: {key} must be a string or null (got {n.get(key)!r})")
        if lon_key not in (None, "longitude"):
            filled[f"natal longitude (from {lon_key})"] = filled.get(f"natal longitude (from {lon_key})", 0) + 1
        natal.append({"fact_id": None if n.get("fact_id") is None else str(n["fact_id"]), "fact_subject": n.get("fact_subject"),
                      "longitude": None if lon_key is None else str(n[lon_key]), "tier": n.get("tier", n.get("verification_pass_status")),
                      "build_id": None if n.get("build_id") is None else str(n["build_id"])})
    if filled:
        notes.append("filled / aliased: " + ", ".join(f"{k} on {v} row(s)" for k, v in sorted(filled.items())))
    if dropped:
        notes.append(f"dropped {dropped} row(s) at level 4 or deeper (out of scope)")
    return kept, natal, notes


def import_w0(path: str, checksum: str, out_path: str, chart_id: str) -> int:
    """The W0 import behind an EXCEPTION BOUNDARY (Codex v1.5): any problem — an unreadable file, a malformed structure, an unexpected exception anywhere in the read, normalisation, validation or write — is
    a named STOP, exit 3, never a traceback. (The detailed contract is `_import_w0`'s.)"""
    try:
        return _import_w0(path, checksum, out_path, chart_id)
    except OSError as exc:
        print(f"STOP — the W0 file or its output could not be read/written ({exc.__class__.__name__}); nothing was accepted", file=sys.stderr); return 3
    except Exception as exc:
        print(f"STOP — the W0 file could not be interpreted ({exc.__class__.__name__}: {exc}); nothing written", file=sys.stderr); return 3


def _import_w0(path: str, checksum: str, out_path: str, chart_id: str) -> int:
    """Suvarṇa's W0 FALLBACK baseline (Fable F-R18-4 / F-R19-3): a JSON file whose SHA-256 (of the file's bytes) is the checksum her SETTLED-1 names. THE ACCEPTED SHAPE, exactly:

        {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa", "build_id": "<the OLD pinned build>",
         "rows":  [{"dasha_row_id": "<uuid>", "level_n": 1, "parent_row_id": null, "lord_graha": "KETU",
                    "start_iso": "1983-11-05T10:20:23Z", "end_iso": "1990-11-05T10:20:23Z", "trunc_start": false, "trunc_end": false}, ...],
         "natal": [{"fact_id": "<uuid>", "fact_subject": "SUN", "longitude": "292.5", "tier": "single", "build_id": "<uuid>"}, ... exactly the ten subjects]}

    Rows: levels 1–3 of the old build, `dasha_row_id` / `level_n` / `parent_row_id` / `lord_graha` / `start_iso` / `end_iso` required; every instant MUST carry `Z` or an offset (an offset-less instant is refused by
    name, never read as local time); `trunc_start` / `trunc_end` may instead be the database names `is_truncated_at_window_start/end`; `system_id` ("vimshottari"), `verification_pass_status`
    ("two_pass_verified") and `build_id` (the old pin) are filled in when absent (a present wrong value is refused); level-4+ rows are dropped (counted). Natal: `longitude` may be named `value` or
    `fact_value_num`, `tier` may be `verification_pass_status`. Every fill/alias/drop is printed. The file is verified against the checksum, normalised, validated EXACTLY as a capture is (tree, every reference-row
    id present with its lord, flags consistent, an unclipped start and end at every level, the ten natal rows) and re-written in the tool's capture format with `meta.source = "w0"`; the comparison then uses
    it through --old-rows. Any problem exits 3 and writes nothing."""
    raw = Path(path).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != checksum.lower():
        print(f"STOP — the W0 file's sha256 is {got}, not the checksum {checksum} named by SETTLED-1", file=sys.stderr); return 3
    try:
        d = strict_json_loads(raw.decode("utf-8"))
    except ValueError as exc:                                  # a malformed / duplicate-keyed / NaN-bearing W0 file: a named STOP, nothing written
        print(f"STOP — the W0 file is not valid strict JSON: {exc}", file=sys.stderr); return 3
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    try:
        w0_build = canon_uuid(d.get("build_id")) if isinstance(d, dict) else None
    except ValueError:
        w0_build = None
    bad_chart = chart_id_problem(chart_id) or (chart_id_problem(d.get("chart_id")) if isinstance(d, dict) else None)
    if bad_chart:
        print(f"STOP — {bad_chart}; nothing written", file=sys.stderr); return 3
    if not isinstance(d, dict) or d.get("chart_id") != chart_id or w0_build != old_id or not isinstance(d.get("rows"), list) or not isinstance(d.get("natal"), list):
        print("STOP — the W0 file is not {chart_id, build_id, rows, natal} for this chart and the pinned build", file=sys.stderr); return 3
    try:
        kept, natal, notes = _w0_normalise(d, old_id)
        rows = norm_rows(kept)
    except (ValueError, KeyError, TypeError) as exc:
        print(f"STOP — the W0 file cannot be read ({exc.__class__.__name__}: {exc}); nothing written", file=sys.stderr); return 3
    for r_in, r_out in zip(kept, rows):
        r_out["trunc_start"], r_out["trunc_end"] = bool(r_in.get("trunc_start")), bool(r_in.get("trunc_end"))
    cap = build_capture(chart_id, old_id, rows, natal, {"source": "w0", "w0_sha256": got, "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tool_commit": _tool_commit()})
    bad = validate_capture(cap, chart_id, old_id)
    if bad:
        print("STOP — the W0 baseline could not later be compared (nothing written): " + "; ".join(bad[:8]), file=sys.stderr); return 3
    write_capture(out_path, cap)
    for line in notes:
        print("W0 import: " + line)
    print(f"imported {len(rows)} daśā rows and {len(natal)} natal longitudes from the W0 baseline (file sha256 {got}) -> {out_path}")
    print(f"sha256 {cap['sha256']}; whole-file sha256 {file_sha256(out_path)}")
    return 0


def open_capture_connection():
    """psycopg (v3) for the pre-S-L1 capture: REPEATABLE READ + READ ONLY (ONE snapshot for every statement), `application_name = repin_capture` (so a lingering session is visible)."""
    import psycopg
    conn = psycopg.connect(os.environ["DATABASE_URL"], application_name="repin_capture")
    conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
    conn.read_only = True
    return conn


class VerifierPinMissing(Exception):
    """--apply cannot rewrite/assert the verifier's independent pin: nothing was written."""


class NeedsRuling(Exception):
    """--apply found test literals nobody has ruled on: nothing was written."""
    def __init__(self, unclassified: list[str]):
        super().__init__(f"{len(unclassified)} test literal(s) need the steward's ruling")
        self.unclassified = unclassified


def _finite_number(v) -> bool:
    """A real, finite, FLOAT-REPRESENTABLE number (Codex v1.2): a JSON integer such as 10**1000 is not — `math.isfinite` raises OverflowError on it — so it is simply not acceptable, never an exception."""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return False
    try:
        return math.isfinite(float(v))
    except (OverflowError, ValueError):
        return False


# Codex ASTRA_REVIEW_REPIN_TOOL_DELTA: a declared shape could bless a broken rebuild (a declaration copied from the broken state) and counts/builds were accepted independently, so the post-S-L1 shape is FIXED
# (45 + 1 partitions, exactly the SETTLED-1 build). A notice carrying any of these fields is REFUSED, so nobody believes they have an effect.
_REFUSED_NOTICE_FIELDS = ("expected_partitions_non_scope", "expected_partitions_scope_cap", "expected_dasha_build_ids")
# The notice's top level is an ALLOW-LIST (Codex ASTRA_REVIEW_REPIN_TOOL_DELTA v1.1): EXACTLY these seven keys; every other key — unknown, misspelled, or one of the retired expected_* fields — is refused BY NAME.
_NOTICE_KEYS = ("settled_1", "source_message_id", "system_id", "ayanamsha_id", "new_build_id", "expected_shift_seconds", "tolerance_seconds")


_LEVEL_KEY = re.compile(r"[1-9]")        # a daśā LEVEL as a notice key: ONE decimal digit 1–9 (levels 1–3 are required and compared; 4 and deeper are tolerated, validated for shape, echoed, never compared)


def load_notice(path: str) -> dict:
    """The strict SETTLED-1 notice loader — EXCEPTION-PROOF (Codex v1.2): any content whatever yields either the notice or `ValueError("the SETTLED-1 notice is invalid: …")` (the CLI's STOP, exit 3, nothing
    written); no content can raise anything else. (An unreadable FILE is still an `OSError`, which the CLI also turns into a STOP.)"""
    try:
        return _load_notice(path)
    except (OSError, ValueError):
        raise
    except Exception as exc:                                  # RecursionError, OverflowError, TypeError … from hostile or malformed content: never an uncaught traceback
        raise ValueError(f"the SETTLED-1 notice is invalid: unreadable content ({type(exc).__name__})") from None


def _load_notice(path: str) -> dict:
    """Suvarṇa's SETTLED-1 notice as JSON: {"settled_1": true, "source_message_id": "<id>", "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha", "new_build_id": "<uuid>",
    "expected_shift_seconds": {"1": 6993, "2": 6993, "3": {"start": 6992, "end": 6994}}, "tolerance_seconds": 2}.
    STRICT ALLOW-LIST (Codex ASTRA_REVIEW_REPIN_TOOL_DELTA v1.1): the top level is EXACTLY the seven keys above — any other key (unknown, misspelled, the retired expected_* shape fields) is refused BY NAME.
    STRICT (Codex R17-3/R17-5, Fable F-R18-4): the notice is BOUND to what it describes — `system_id` must be `vimshottari`, `ayanamsha_id` `lahiri_chitrapaksha`, `source_message_id` non-empty (recorded in
    the evidence), `new_build_id` a valid UUID (canonicalised); `expected_shift_seconds` MUST name levels 1, 2 and 3, each a FINITE number or {start, end} — **`{start, end}` are the START-boundary and
    END-boundary shift expectations, NOT a range** — and ANY OTHER level (SETTLED-1 will declare level-4 deltas) is TOLERATED, echoed in the evidence and NEVER compared (this tool judges levels 1–3
    only); `tolerance_seconds` is a FINITE number >= 1 — NaN and infinities are refused; the tolerance is STATED by the notice — there is no default. The notice's sha256 is recorded."""
    raw = Path(path).read_bytes()
    try:
        d = strict_json_loads(raw.decode("utf-8"))
    except ValueError as exc:                                  # duplicate keys (any depth), NaN/Infinity tokens, malformed JSON, bad UTF-8
        raise ValueError(f"the SETTLED-1 notice is invalid: {exc}") from None
    problems = []
    if not isinstance(d, dict):
        raise ValueError("the SETTLED-1 notice is invalid: the notice must be a JSON object")
    unknown = sorted(k for k in d if k not in _NOTICE_KEYS)
    if unknown:                                               # EARLY refusal: no value of an unknown-key notice is read at all
        retired = [k for k in unknown if k in _REFUSED_NOTICE_FIELDS]
        other = [k for k in unknown if k not in _REFUSED_NOTICE_FIELDS]
        if retired:
            problems.append(f"{', '.join(retired)} NOT accepted: the post-S-L1 chart_dashas shape is fixed (45 + 1 partitions, exactly the SETTLED-1 build); no notice field may override it")
        if other:
            problems.append(f"unknown notice key(s) {', '.join(repr(k) for k in other)}: the notice allows EXACTLY {', '.join(_NOTICE_KEYS)}")
        raise ValueError("the SETTLED-1 notice is invalid: " + "; ".join(problems))
    if d.get("settled_1") is not True:
        problems.append("settled_1 must be true")
    if d.get("system_id") != CANONICAL_SYSTEM:
        problems.append(f"system_id must be {CANONICAL_SYSTEM!r} (this tool judges the Vimśottarī read only)")
    if d.get("ayanamsha_id") != CANONICAL_AYANAMSHA:
        problems.append(f"ayanamsha_id must be {CANONICAL_AYANAMSHA!r}")
    if not isinstance(d.get("source_message_id"), str) or not d["source_message_id"].strip():
        problems.append("source_message_id is required (the announcement the notice came with)")
    try:
        d["new_build_id"] = canon_uuid(d.get("new_build_id"))
    except ValueError:
        problems.append("new_build_id is required and must be a valid UUID (the settlement build identifier)")
    exp = d.get("expected_shift_seconds")
    if not isinstance(exp, dict) or not {str(lv) for lv in LEVELS_IN_SCOPE} <= set(exp):
        problems.append("expected_shift_seconds must name levels 1, 2 and 3")
    else:
        bad_keys = sorted((k for k in exp if not (isinstance(k, str) and _LEVEL_KEY.fullmatch(k))), key=repr)
        if bad_keys:                                          # a key that is not a LEVEL (a typo beside the levels) is refused by name
            problems.append(f"expected_shift_seconds key(s) {', '.join(repr(k) for k in bad_keys)} are not levels (a level is ONE decimal digit 1–9)")
        for k in sorted(k for k in exp if isinstance(k, str) and _LEVEL_KEY.fullmatch(k)):
            e = exp[k]
            ok = _finite_number(e) or (isinstance(e, dict) and set(e) == {"start", "end"} and _finite_number(e["start"]) and _finite_number(e["end"]))
            if not ok:
                problems.append(f"expected_shift_seconds[{k}] must be a finite number or exactly {{start, end}} of finite numbers (the two BOUNDARY expectations, not a range; no other key)")
    tol = d.get("tolerance_seconds")
    if not _finite_number(tol) or tol < MIN_TOLERANCE_SECONDS:
        problems.append(f"tolerance_seconds must be a FINITE number >= {MIN_TOLERANCE_SECONDS}")
    if problems:
        raise ValueError("the SETTLED-1 notice is invalid: " + "; ".join(problems))
    d["_ignored_levels"] = sorted(k for k in exp if k not in {str(lv) for lv in LEVELS_IN_SCOPE})
    d["expected_shift_seconds"] = {k: exp[k] for k in (str(lv) for lv in LEVELS_IN_SCOPE)}          # only levels 1–3 are ever compared
    d["_sha256"] = hashlib.sha256(raw).hexdigest()
    return d


def shift_problems(stats: dict, notice: dict | None) -> list[str]:
    """Steward M20261002T223121-b4d9 (d): the MEASURED per-level shift must match the EXPECTED one from the notice within its stated tolerance; an unexpected shift is a STOP, never silently
    'boundary-sensitive'. Every measured side's min AND max are checked; a level in the notice that has no measurement, or a measured level the notice does not name, is a problem."""
    if notice is None:
        return ["INCOMPLETE: no --settled-notice (the expected per-level shift from Suvarṇa's SETTLED-1 notice)"]
    exp, tol, out = notice["expected_shift_seconds"], notice["tolerance_seconds"], []
    for lv in sorted(set(stats) | {int(k) for k in exp}):
        e = exp.get(str(lv))
        if lv not in stats:
            out.append(f"level {LEVEL_NAME.get(lv, lv)}: named in the notice but not measured"); continue
        if e is None:
            out.append(f"level {LEVEL_NAME.get(lv, lv)}: measured but the notice states no expected shift"); continue
        want = {"start": e, "end": e} if isinstance(e, (int, float)) and not isinstance(e, bool) else e
        for side in ("start", "end"):
            if side not in stats[lv]:
                out.append(f"level {LEVEL_NAME.get(lv, lv)} {side}: ZERO unclipped measurements (every edge is clipped to the window) — nothing to judge the shift on")
                continue
            for stat in ("min", "max"):
                got = stats[lv][side][stat]
                if not (abs(got - want[side]) <= tol):                                         # NaN-safe: a NaN fails the comparison instead of passing it
                    out.append(f"level {LEVEL_NAME.get(lv, lv)} {side} {stat} shift {got:.3f} s is outside the notice's {want[side]} s ± {tol} s")
    return out


def path_lord_flips(old: dict, new: dict, matched: list) -> list[dict]:
    """D7 (steward M20261002T222913-35c5): EVERY matched (level, path) row — not only the pinned reference rows — must keep its lord. A boundary that MOVED (the Moshier → Swiss
    ≈ 1.94 h shift) is not a flip; a different lord at the same (level, path) is. Returns the differences (empty = lords hold)."""
    return [{"key": k, "old": old[k]["lord_graha"], "new": new[k]["lord_graha"]} for k in matched if old[k]["lord_graha"] != new[k]["lord_graha"]]


def oracle_instants(repo_tests: Path | None = None) -> list[str]:
    """Every instant the contract is exercised at: the pinned reference rows' edges (±1 s) and every
    ISO-8601 UTC literal in the gochara_rules / step06b tests (O-PP-1/2/3, worked events)."""
    iso_re = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b")
    found: set[str] = set()
    for rows in (PERM.MD_ROWS, PERM.AD_ROWS, PERM.PD_ROWS):
        for r in rows:
            for edge in (r["start_iso"], r["end_iso"]):
                found |= {iso(_t(edge) + timedelta(seconds=d)) for d in (-1, 0, 1)}        # the edge ±1 s, as the docstring says
    base = repo_tests or (SIDECAR / "tests" / "l3")
    for p in list(base.glob("gochara_rules/*.py")) + list(base.glob("gochara/test_step06b*.py")):
        found |= set(iso_re.findall(p.read_text(encoding="utf-8")))
    return sorted(found)


def remeasure_reference_rows(old: dict, new: dict) -> tuple[list[dict], list[str]]:
    """Each pinned reference row (by id) located in the OLD build's path index and re-found at the same
    (level, path) in the NEW build. Returns (mappings, problems)."""
    by_id = {r["dasha_row_id"]: k for k, r in old.items()}
    maps, problems = [], []
    for level_rows in (PERM.MD_ROWS, PERM.AD_ROWS, PERM.PD_ROWS):
        for ref in level_rows:
            k = by_id.get(ref["row_id"])
            if k is None:
                problems.append(f"reference row {ref['row_id']} not found in the old build"); continue
            n = new.get(k)
            if n is None:
                problems.append(f"reference row {ref['row_id']} {k} has no counterpart in the new build"); continue
            if n["lord_graha"] != ref["lord"]:
                problems.append(f"reference row {ref['row_id']}: lord {ref['lord']} -> {n['lord_graha']} (a LORD FLIP)")
            maps.append({"old": ref, "new": n, "key": k})
    return maps, problems


def decide(*, new_tier_ok: bool, new_integrity: dict, m: dict, flips: list, ref_problems: list, forensic_report: str | None, shift_issues: list[str] | None = None,
           tree_issues: list[str] | None = None, old_totals: dict | None = None, new_totals: dict | None = None, refused_subtrees: list[dict] | None = None, edge_issues: list[str] | None = None) -> list[str]:
    stops = list(shift_issues or []) + list(tree_issues or []) + list(edge_issues or [])
    for r in refused_subtrees or []:
        label = " → ".join(f"{l}#{k}" for l, k in r["parent"]) or "(roots)"
        stops.append(f"REFUSED SUBTREE under {label}: the child set differs (old {r['old']}, new {r['new']}) — never best-guessed; any count difference at levels 1–3 is UNEXPECTED")
    if old_totals is not None and new_totals is not None and old_totals != new_totals:
        stops.append(f"per-level row totals differ (old {old_totals}, new {new_totals}); lords AND row counts must be EQUAL at levels 1–3")
    if not new_tier_ok:
        stops.append("new build is not tier two_pass_verified")
    if new_integrity["orphans"]:
        stops.append(f"{len(new_integrity['orphans'])} orphaned rows (parent linkage broken)")
    if new_integrity["duplicates"]:
        stops.append(f"{new_integrity['duplicates']} duplicate rows under the §4.0 rules")
    if flips:
        stops.append(f"{len(flips)} lord flip(s) at matched (level, path) rows — a STOP, not a re-pin (CLAUDE.md §N.5; D7)")
    stops += ref_problems
    if m["only_old"] or m["only_new"]:
        stops.append(f"row-count difference needs an explanation: {len(m['only_old'])} only in old, {len(m['only_new'])} only in new")
    if not forensic_report:
        stops.append("INCOMPLETE: no --forensic-report (evidence item (e): the seven FORENSIC anchors)")
    return stops


# ── rendering / applying ─────────────────────────────────────────────────────
def render(*, old_id, new_id, chart_id, o_int, n_int, m, stats, flips, maps, stops, sensitive=(), evidence=()) -> str:
    L = [f"# AM-10 re-pin evidence — chart {chart_id}", "",
         f"* old pin: `{old_id}`  →  new build: `{new_id}`", f"* verdict: **{'CLEAN' if not stops else 'STOP'}**", ""]
    if stops:
        L += ["## Stops", *[f"* {s}" for s in stops], ""]
    if evidence:
        L += ["## Evidence bound to this verdict", *[f"* {e}" for e in evidence], ""]
    L += ["## (b) rows per level", "| level | old | new |", "|---|---|---|"]
    for lv in sorted(set(o_int["by_level"]) | set(n_int["by_level"])):
        L.append(f"| {LEVEL_NAME.get(lv, lv)} | {o_int['by_level'].get(lv, 0)} | {n_int['by_level'].get(lv, 0)} |")
    L += ["", f"matched {len(m['matched'])} · only-old {len(m['only_old'])} · only-new {len(m['only_new'])}", "",
          "## (c) integrity (new build)", f"* orphans: {len(n_int['orphans'])} · duplicates: {n_int['duplicates']}", "",
          "## (d) measured boundary shift (seconds, new − old, matched by (level, path))", "| level | side | min | max | mean | n |", "|---|---|---|---|---|---|"]
    for lv, d in stats.items():
        for side, v in d.items():
            L.append(f"| {LEVEL_NAME.get(lv, lv)} | {side} | {v['min']:.0f} | {v['max']:.0f} | {v['mean']:.1f} | {v['n']} |")
    L += ["", f"## (f) lord flips at matched (level, path) rows: {len(flips)} (D7 — any is a STOP)", *[f"* {LEVEL_NAME.get(f['key'][0], f['key'][0])} path {f['key'][1]}: {f['old']} → {f['new']}" for f in flips], "",
          f"## (f2) {len(sensitive)} BOUNDARY-SENSITIVE oracle instant(s): the lord at the instant differs old → new because a boundary MOVED, not because a lord changed (D8: re-run every event-dated comparison at these)",
          *[f"* {x['instant']}: {x['old']} → {x['new']}" for x in sensitive], "",
          "## (3) re-measured reference rows (every id in full)"]
    for x in maps:
        o, n = x["old"], x["new"]
        L.append(f"* {o['level']} {o['lord']}: `{o['row_id']}` {o['start_iso']}..{o['end_iso']}  →  `{n['dasha_row_id']}` {n['start_iso']}..{n['end_iso']}")
    return "\n".join(L) + "\n"


_WHOLE_SECOND_Z = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def rewrite_once(text: str, mapping: dict[str, str]) -> str:
    """ONE pass (never sequential `str.replace`: a new value equal to a later old one would be replaced twice), longest key first, exact strings only."""
    if not mapping:
        return text
    pat = re.compile("|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)))
    return pat.sub(lambda m_: mapping[m_.group(0)], text)


_IST = timezone(timedelta(hours=5, minutes=30))


def boundary_forms(old_z: str, new_z: str) -> list[tuple["re.Pattern[str]", "object"]]:
    """The NON-`Z` textual forms an old boundary instant takes in source (steward ruling 2026-10-04: the first apply found seven of them by hand — a `datetime(...)` constructor, a bare
    `T11:47:23` prefix, `+00:00`, a docstring time, a `< "…"` comparison, the sub-second `…22.999999+00:00` — the `Z`-only search could not see them). Each entry is (compiled pattern, replacement(match)).
    Forms: (1) date-time without a trailing `Z`/digit/dot, `T` or space separated (so `+00:00`, a bare prefix and a docstring all match; the `Z` literal is the exact scan's); (2) the second BEFORE
    the boundary, whole or with a `.9…` fraction, with or without `Z`/offset (a `just_before` literal); (3) the same two in IST (+05:30, date shift included); (4) a `datetime(y, m, d, h, mi, s`
    constructor; (5) epoch seconds; (6) compact `YYYYMMDDTHHMMSS` / `YYYYMMDDHHMMSS`. Julian-day numbers are NOT searched (a limit, stated in the report)."""
    o, n = _t(old_z), _t(new_z)
    forms: list[tuple[re.Pattern[str], object]] = []

    for tz in (timezone.utc, _IST):
        ot, nt = o.astimezone(tz), n.astimezone(tz)
        for delta, frac in ((timedelta(0), False), (timedelta(seconds=-1), True)):
            ob, nb = ot + delta, nt + delta
            head = re.escape(ob.strftime("%Y-%m-%d")) + r"([T ])" + re.escape(ob.strftime("%H:%M:%S"))
            if frac:                                                          # the second before: whole, or `.9…`, with or without `Z`
                forms.append((re.compile(head + r"(\.\d+)?(Z)?(?![\d])"),
                              lambda m_, nb=nb: nb.strftime("%Y-%m-%d") + m_.group(1) + nb.strftime("%H:%M:%S") + (m_.group(2) or "") + (m_.group(3) or "")))
            else:                                                             # the boundary itself, NOT followed by `Z`, a digit or a fraction (the `Z` literal is the exact scan's)
                forms.append((re.compile(head + r"(?!\d)(?!\.\d)(?!Z)"),
                              lambda m_, nb=nb: nb.strftime("%Y-%m-%d") + m_.group(1) + nb.strftime("%H:%M:%S")))
    # (4) datetime(y, m, d, h, mi, s — any zero padding, any spacing
    forms.append((re.compile(r"datetime\(\s*%d,\s*0?%d,\s*0?%d,\s*0?%d,\s*0?%d,\s*0?%d(?!\d)" % (o.year, o.month, o.day, o.hour, o.minute, o.second)),
                  lambda m_, n=n: "datetime(%d, %d, %d, %d, %d, %d" % (n.year, n.month, n.day, n.hour, n.minute, n.second)))
    # (5) epoch seconds
    forms.append((re.compile(r"(?<![\d.])%d(?![\d])" % int(o.timestamp())), lambda m_, n=n: str(int(n.timestamp()))))
    # (6) compact forms
    forms.append((re.compile(o.strftime("%Y%m%dT?%H%M%S") + r"(?!\d)"), lambda m_, n=n: n.strftime("%Y%m%dT%H%M%S") if "T" in m_.group(0) else n.strftime("%Y%m%d%H%M%S")))
    return forms


def _id_wrapped_pattern(row_id: str) -> "re.Pattern[str]":
    """An old row id that a line wrap split inside a comment/string: hyphen-joined groups with an optional newline + indentation + comment leader after any hyphen."""
    parts = row_id.split("-")
    gap = r"(?:\s*\n[ \t]*(?:#|//|\*)?[ \t]*)?"
    return re.compile(r"(?<![0-9a-f])" + ("-" + gap).join(re.escape(x) for x in parts) + r"(?![0-9a-f])")


def rewrite_wrapped_ids(text: str, ids: dict[str, str]) -> str:
    """Replace each (possibly line-wrapped) old row id by its new id CHARACTER BY CHARACTER, leaving the break, indentation and comment leader exactly as they were (old and new ids have the same
    36-character shape, so the break falls at the same place)."""
    for old, new in ids.items():
        def sub(m_: "re.Match[str]", new=new) -> str:
            it = iter(new)
            return "".join(next(it) if (c.isalnum() or c == "-") else c for c in m_.group(0)) if "\n" in m_.group(0) else new
        text = _id_wrapped_pattern(old).sub(sub, text)
    return text


def scan_wrapped_ids(ids: dict[str, str], repo_root: Path) -> list[tuple[str, int, str]]:
    out = []
    for p in sorted(q for q in (SIDECAR / "tests" / "l3").rglob("*.py") if q.is_file()):    # a DIRECTORY named *.py is not a file to scan or rewrite (the write plan refuses it)
        txt = p.read_text(encoding="utf-8")
        for old in ids:
            for m_ in _id_wrapped_pattern(old).finditer(txt):
                if "\n" in m_.group(0):
                    out.append((str(p.relative_to(repo_root)), txt.count("\n", 0, m_.start()) + 1, old))
    return out


def all_boundary_forms(instants: dict[str, str]) -> list[tuple["re.Pattern[str]", "object"]]:
    """`boundary_forms` for every old instant PLUS the bare UTC time of day (`11:47:23` in a docstring or comment) — only for a time of day that belongs to exactly ONE old instant (two instants
    sharing it would make the replacement ambiguous; those are left to the dated forms)."""
    forms = [f for a_, b_ in instants.items() for f in boundary_forms(a_, b_)]
    tods: dict[str, list[tuple[str, str]]] = {}
    for a_, b_ in instants.items():
        tods.setdefault(_t(a_).strftime("%H:%M:%S"), []).append((a_, b_))
    for tod, owners in tods.items():
        if len(owners) == 1:
            nb = _t(owners[0][1]).strftime("%H:%M:%S")
            forms.append((re.compile(r"(?<![\d:])" + re.escape(tod) + r"(?![\d:])(?!\.\d)"), lambda m_, nb=nb: nb))
    return forms


def line_spans(line: str, instants: dict[str, str], forms: list) -> list[tuple[int, int, str, str]]:
    """Every old-boundary match on one line as (start, end, matched text, replacement): the exact `…Z` literals (EVERY occurrence) plus the form matches, with a match that lies INSIDE a longer one
    on the same line dropped (the bare time of day inside `2020-02-14T11:47:23Z` is the same occurrence). Offsets are kept (Codex v1.7 P1-2): a ruling rewrites THESE spans and nothing else."""
    spans: list[tuple[int, int, str, str]] = []
    for a_, b_ in instants.items():
        i = line.find(a_)
        while i >= 0:
            spans.append((i, i + len(a_), a_, b_)); i = line.find(a_, i + 1)
    for pat, repl in forms:
        for m_ in pat.finditer(line):
            spans.append((m_.start(), m_.end(), m_.group(0), repl(m_)))
    keep = [x for x in spans if not any(y is not x and y[0] <= x[0] and x[1] <= y[1] and (y[1] - y[0]) > (x[1] - x[0]) for y in spans)]
    out, seen = [], set()
    for x in sorted(keep):
        if (x[0], x[1]) not in seen:
            seen.add((x[0], x[1])); out.append(x)
    return out


def line_matches(line: str, instants: dict[str, str], forms: list) -> list[tuple[str, str]]:
    """The distinct (matched text, replacement) pairs of `line_spans` — what the human sees in the ruling list."""
    seen, out = set(), []
    for _, _, a_, b_ in line_spans(line, instants, forms):
        if (a_, b_) not in seen:
            seen.add((a_, b_)); out.append((a_, b_))
    return out


def rewrite_spans(line: str, spans: list[tuple[int, int, str, str]]) -> str:
    """Replace EXACTLY the given spans (each must still read as its matched text) and not one other byte of the line — never a string replace over the line."""
    out = line
    for start, end, a_, b_ in sorted(spans, reverse=True):
        if out[start:end] != a_:
            raise ValueError(f"span {start}:{end} no longer reads {a_!r} (got {out[start:end]!r}); nothing written")
        out = out[:start] + b_ + out[end:]
    return out


def scan_test_spans(instants: dict[str, str], repo_root: Path) -> list[tuple[str, int, int, int, str, str]]:
    """Every old boundary in tests/l3 as (path, line, start, end, matched text, replacement): the exact `…Z` literal AND the non-`Z` forms of `boundary_forms`."""
    forms = all_boundary_forms(instants)
    out = []
    for p in sorted(q for q in (SIDECAR / "tests" / "l3").rglob("*.py") if q.is_file()):    # a DIRECTORY named *.py is not a file to scan or rewrite (the write plan refuses it)
        for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for st, en, a_, b_ in line_spans(line, instants, forms):
                out.append((str(p.relative_to(repo_root)), ln, st, en, a_, b_))
    return out


def scan_test_literals(instants: dict[str, str], repo_root: Path) -> list[tuple[str, int, str, str]]:
    """(path, line, matched text, replacement) — the ruling list (one entry per distinct pair per line)."""
    seen, out = set(), []
    for pth, ln, _, _, a_, b_ in scan_test_spans(instants, repo_root):
        if (pth, ln, a_, b_) not in seen:
            seen.add((pth, ln, a_, b_)); out.append((pth, ln, a_, b_))
    return out


WIDE_SCAN_SUFFIXES = (".py", ".ts", ".tsx", ".json", ".sql", ".sh", ".yml")


def scan_wide_literals(instants: dict[str, str], repo_root: Path) -> list[tuple[str, int, str, str]]:
    """REPORT-ONLY (never rewritten, never blocking): the same old-boundary forms OUTSIDE tests/l3 — `platform/tests/**`, every `__tests__` tree, the sidecar's other tests, scripts and services.
    These are KEEP candidates (independent synthetic fixtures, history comments); the first apply found three TypeScript `.db.test.ts` files and one governance fixture that seed their own old-instant rows."""
    forms = all_boundary_forms(instants)
    roots = [repo_root / "platform" / "tests", repo_root / "platform" / "scripts", SIDECAR / "tests", SIDECAR / "scripts", SIDECAR / "services"]
    skip = SIDECAR / "tests" / "l3"
    perm = SIDECAR / "services" / "gochara_rules" / "permission.py"
    seen, out = set(), []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix not in WIDE_SCAN_SUFFIXES or p in seen or p == perm or skip in p.parents:
                continue
            seen.add(p)
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            for ln, line in enumerate(lines, 1):
                for a_, b_ in line_matches(line, instants, forms):
                    out.append((str(p.relative_to(repo_root)), ln, a_, b_))
    return out


def write_all_or_restore(writes: list[tuple[Path, str]]) -> None:
    """Threat T-ATOMIC: an apply is ALL-OR-NOTHING. Each file is written atomically (`write_atomic`); if any write fails, the files already written are put back byte for byte (and files this apply
    CREATED are removed) before the error propagates, so a failed apply never leaves a half-re-pinned tree."""
    originals: dict[Path, bytes | None] = {p_: (p_.read_bytes() if p_.exists() else None) for p_, _ in writes}
    done: list[Path] = []
    try:
        for p_, txt_ in writes:
            write_atomic(p_, txt_)
            done.append(p_)
    except BaseException:
        for q in reversed(done):
            try:
                if originals[q] is None:
                    q.unlink()
                else:
                    write_atomic(q, originals[q].decode("utf-8"))
            except Exception:                    # noqa: BLE001 — best effort; the original error is what the operator needs
                pass
        raise


def validate_write_plan(writes: list[tuple[Path, str]]) -> None:
    """Everything `write_atomic` would refuse, found BEFORE any file is touched and before a CLEAN report is published: strict-UTF-8-encodable text; each destination a (new or existing) regular FILE
    — never a directory — inside an EXISTING, writable directory (`write_atomic` creates no directories); an existing destination writable. Raises `VerifierPinMissing` (a named STOP, nothing written)."""
    seen: set[str] = set()
    for p_, txt_ in writes:
        try:
            txt_.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise VerifierPinMissing(f"{p_}: the new text is not strict UTF-8 ({exc.reason}); nothing written") from exc
        if str(p_) in seen:
            raise VerifierPinMissing(f"{p_} appears twice in the write plan; nothing written")
        seen.add(str(p_))
        if p_.is_dir():
            raise VerifierPinMissing(f"{p_} is a directory; nothing written")
        if p_.exists() and (not p_.is_file() or not os.access(p_, os.W_OK)):
            raise VerifierPinMissing(f"{p_} exists and is not a writable regular file; nothing written")
        d = p_.parent
        if not d.is_dir() or not os.access(d, os.W_OK | os.X_OK):
            raise VerifierPinMissing(f"{d} (the directory of {p_.name}) does not exist or is not writable; nothing written")


def apply_repin(new_id: str, maps: list[dict], repo_root: Path, rulings: dict | None = None, review: list[str] | None = None, check_only: bool = False) -> list[str]:
    """Rewrites (a) permission.py: the pin, the reference rows' ids and instants — ONE pass; (b) tests/l3: the reference rows' ids and the old pin's build id (they ARE reference rows).
    An OLD BOUNDARY INSTANT found in a test is NEVER rewritten automatically (it may be an event date that merely equals a boundary — D8): each match is listed as `path:line old -> new`
    and --apply STOPS before writing ANYTHING (`NeedsRuling`) unless every match is classified in `rulings` = {"rewrite": ["path:line", …], "keep": ["path:line", …]} (the steward's ruling)."""
    changed = []
    perm = SIDECAR / "services" / "gochara_rules" / "permission.py"
    s = perm.read_text(encoding="utf-8")
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    assert s.count(f'"build_id": "{old_id}"') == 1
    ids: dict[str, str] = {}
    instants: dict[str, str] = {}
    for x in maps:
        o, n = x["old"], x["new"]
        ids[o["row_id"]] = n["dasha_row_id"]
        for side in ("start_iso", "end_iso"):
            literal = iso(n[side])          # whole-second UTC `…Z` — the permission.py literal form (measurement elsewhere keeps full precision)
            assert _WHOLE_SECOND_Z.fullmatch(literal), f"permission literal {literal!r} is not whole-second …Z (permission.py compares these lexicographically)"
            if instants.get(o[side], literal) != literal:
                raise VerifierPinMissing(f"literal conflict: the old instant {o[side]} maps to two different new instants ({instants[o[side]]} and {literal}) — nothing written")
            instants[o[side]] = literal
    ver = SIDECAR / "services" / "gochara_kernel" / "inventory_verifier.py"
    if not ver.is_file():
        raise VerifierPinMissing(f"{ver} is absent: the verifier's INDEPENDENT pin (`_C_BUILD`) cannot be rewritten — run the re-pin on a tree that carries the '5.0' kernel")
    ver_txt = ver.read_text(encoding="utf-8")
    ver_old_line = f'_C_BUILD = "{old_id}"'
    if ver_txt.count(ver_old_line) != 1:
        raise VerifierPinMissing(f"{ver}: expected exactly ONE `{ver_old_line}` line, found {ver_txt.count(ver_old_line)} (the verifier's pin is a second site; it must equal the permission.py pin before and after)")
    matches = scan_test_literals(instants, repo_root)
    if review is not None:
        review.extend(f"WRAPPED ID {p}:{ln} {o_} -> {ids[o_]} [rewritten character for character]" for p, ln, o_ in scan_wrapped_ids(ids, repo_root))
    ruled = {**{k: "rewrite" for k in (rulings or {}).get("rewrite", [])}, **{k: "keep" for k in (rulings or {}).get("keep", [])}}
    unclassified = [f"{p}:{ln} {a_} -> {b_}" for p, ln, a_, b_ in matches if f"{p}:{ln}" not in ruled]
    if review is not None:
        review.extend(f"{p}:{ln} {a_} -> {b_} [{ruled.get(f'{p}:{ln}', 'UNRULED')}]" for p, ln, a_, b_ in matches)
    if unclassified:
        raise NeedsRuling(unclassified)                                              # nothing has been written
    s = rewrite_once(s, {**ids, **instants, f'"build_id": "{old_id}"': f'"build_id": "{new_id}"'})
    assert s.count(f'"build_id": "{new_id}"') == 1 and f'"build_id": "{old_id}"' not in s, "the re-pin constant must equal the SETTLED-1 build and the old pin must be gone (G6 b)"
    new_ver = rewrite_once(ver_txt, {ver_old_line: f'_C_BUILD = "{new_id}"'})
    assert new_ver.count(f'_C_BUILD = "{new_id}"') == 1 and ver_old_line not in new_ver, "the verifier's _C_BUILD must equal the SETTLED-1 build and the old pin must be gone"
    writes: list[tuple[Path, str]] = [(perm, s), (ver, new_ver)]                    # every new text is built in memory FIRST; all are encoded/validated, then written atomically one by one
    changed.append(str(perm.relative_to(repo_root)))
    changed.append(str(ver.relative_to(repo_root)))
    by_file: dict[str, dict[int, list[tuple[int, int, str, str]]]] = {}
    for p, ln, st, en, a_, b_ in scan_test_spans(instants, repo_root):
        if ruled.get(f"{p}:{ln}") == "rewrite":
            by_file.setdefault(p, {}).setdefault(ln, []).append((st, en, a_, b_))
    gen = SIDECAR / "tests" / "l3" / "gochara_rules" / f"test_am10_repin_{new_id[:8]}.py"
    gen_text = GENERATED_TEST.format(old=old_id, new=new_id)
    if gen.exists() and gen.is_file() and gen.read_text(encoding="utf-8") != gen_text:             # Codex v1.8 P1-2: never replace a different existing file wholesale (it may hold ruled KEEP literals)
        raise VerifierPinMissing(f"{gen} already exists and differs from the generated test; refusing to replace it (move it aside or review it); nothing written")
    for p in sorted(q for q in (SIDECAR / "tests" / "l3").rglob("*.py") if q.is_file() and q != gen):    # a DIRECTORY named *.py is not a file to scan or rewrite; the generated test is written whole, never rewritten
        txt = p.read_text(encoding="utf-8")
        rel = str(p.relative_to(repo_root))
        lines = txt.splitlines(keepends=True)
        for ln, sp in by_file.get(rel, {}).items():
            body = lines[ln - 1]
            core = body.rstrip("\r\n")
            lines[ln - 1] = rewrite_spans(core, sp) + body[len(core):]                 # ONLY the ruled spans of the ruled lines (Codex v1.7 P1-2)
        new_txt = rewrite_once(rewrite_wrapped_ids("".join(lines), ids), {**ids, old_id: new_id})          # a wrapped old id is rewritten character for character first
        if new_txt != txt:
            writes.append((p, new_txt)); changed.append(rel)
    writes.append((gen, gen_text))
    changed.append(str(gen.relative_to(repo_root)))
    validate_write_plan(writes)                                                      # the COMPLETE plan — generated destinations and parent directories included — is validated first (Codex v1.7 P1-3)
    if check_only:                                                                   # every repository-state refusal AND every destination has been evaluated; nothing has been written
        return []
    write_all_or_restore(writes)
    return changed


GENERATED_TEST = '''"""AM-10 rule 2(g) — generated by scripts/gochara/repin_dasha_contract.py: the OLD build is refused, the NEW accepted."""
import importlib.util
import pathlib
import sys

import pytest

from services.gochara_grammar.dasha_data import DashaReadConflict
from services.gochara_kernel import inventory_verifier
from services.gochara_rules.permission import DASHA_READ_CONTRACT

_P = pathlib.Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover" / "step06a_class_context.py"
_spec = importlib.util.spec_from_file_location("step06a_class_context_am10", _P)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
select_dasha_read_contract = _mod.select_dasha_read_contract

OLD, NEW = "{old}", "{new}"


def rows(build):
    return [{{"system_id": "vimshottari", "build_id": build, "level_n": 1}}]


def test_the_verifiers_independent_pin_equals_the_read_contract_pin():
    assert inventory_verifier._C_BUILD == DASHA_READ_CONTRACT["build_id"] == NEW


def test_pin_is_the_new_build_and_the_old_one_is_refused():
    assert DASHA_READ_CONTRACT["build_id"] == NEW
    assert select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"], rows(NEW))["build_id"] == NEW
    with pytest.raises(DashaReadConflict):
        select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"], rows(OLD))
'''


# ── CLI ──────────────────────────────────────────────────────────────────────
def _mode_error(a) -> str | None:
    """Every mode combination is validated here, BEFORE any capture, connection or read (Codex R17-7): a dry run never writes, and capture mode is capture-only."""
    if a.system != "vimshottari" or a.max_level != 3:
        return (f"--system {a.system} --max-level {a.max_level} REFUSED: this tool judges the Vimśottarī Lahiri levels 1–3 only (other systems and level 4 are out of scope; level-4 row counts "
                "change by design at S-L1)")
    if a.import_w0 or a.w0_checksum or a.w0_capture_out:
        if not (a.import_w0 and a.w0_checksum and a.w0_capture_out):
            return "--import-w0 needs --w0-checksum and --w0-capture-out (and only those)"
        extra = [flag for flag, val in (("--new-build-id", a.new_build_id), ("--dry-run", a.dry_run), ("--apply", a.apply), ("--settled-notice", a.settled_notice), ("--old-rows", a.old_rows),
                                        ("--rulings", a.rulings), ("--forensic-report", a.forensic_report), ("--out", a.out), ("--settled-received", a.settled_received), ("--capture-old", a.capture_old), ("--capture-new", a.capture_new)) if val]
        return f"--import-w0 is an import-only mode; it cannot be combined with {', '.join(extra)}" if extra else None
    if a.capture_old:
        extra = [flag for flag, val in (("--new-build-id", a.new_build_id), ("--dry-run", a.dry_run), ("--apply", a.apply), ("--settled-notice", a.settled_notice), ("--old-rows", a.old_rows),
                                        ("--rulings", a.rulings), ("--forensic-report", a.forensic_report), ("--out", a.out), ("--settled-received", a.settled_received), ("--capture-new", a.capture_new)) if val]
        if extra:
            return f"--capture-old is a capture-only mode (read-only, writes only its own file); it cannot be combined with {', '.join(extra)}"
        return None
    if a.capture_new:
        extra = [flag for flag, val in (("--dry-run", a.dry_run), ("--apply", a.apply), ("--settled-notice", a.settled_notice), ("--old-rows", a.old_rows),
                                        ("--rulings", a.rulings), ("--forensic-report", a.forensic_report), ("--out", a.out), ("--settled-received", a.settled_received)) if val]
        if extra:
            return f"--capture-new is a capture-only mode (read-only, writes only its own file); it cannot be combined with {', '.join(extra)}"
        if not a.new_build_id:
            return "--capture-new needs --new-build-id <the build to capture>"
        try:
            a.new_build_id = canon_uuid(a.new_build_id)
        except ValueError:
            return f"--new-build-id {a.new_build_id!r} is not a valid UUID"
        return None
    if not a.new_build_id:
        return "--new-build-id is required for comparison and application (it is not used by --capture-old)"
    try:
        a.new_build_id = canon_uuid(a.new_build_id)                                  # one canonical form before ANY comparison
    except ValueError:
        return f"--new-build-id {a.new_build_id!r} is not a valid UUID"
    if a.apply and a.chart_id != PERM.DASHA_READ_CONTRACT["chart_id"]:
        return f"--apply is refused for chart {a.chart_id}: the pin belongs to the canonical chart {PERM.DASHA_READ_CONTRACT['chart_id']}"
    if a.dry_run and a.apply:
        return "--dry-run and --apply are mutually exclusive (a dry run writes nothing)"
    if a.apply and not a.settled_received:
        return "--apply refused: pass --settled-received <the steward's message id announcing 'SETTLED-1 received'> (local re-pin PREPARATION; production Gochara work stays held until the reviewed re-pin is merged and the steward lifts ST-SL1-HOLD)"
    if a.rulings and not a.apply:
        return "--rulings only applies with --apply"
    return None


def _tool_commit() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def capture_census(conn, chart_id: str) -> dict:
    """The asset-state / build census for the chart from the SAME snapshot (psycopg3 `execute` only): distinct `chart_dashas` build ids (every system), the non-scope / scope-cap partition counts, the
    `asset_throughput` state of ga_dashas and ga_positions, and the distinct natal build ids."""
    builds = [str(r[0]) for r in conn.execute("SELECT DISTINCT build_id::text FROM public.chart_dashas WHERE chart_id = %s ORDER BY 1", (chart_id,)).fetchall()]
    non_scope, scope = conn.execute("SELECT count(*) FILTER (WHERE system_id <> 'scope_cap'), count(*) FILTER (WHERE system_id = 'scope_cap') FROM (SELECT DISTINCT system_id, ayanamsha_id FROM public.chart_dashas WHERE chart_id = %s) p", (chart_id,)).fetchone()
    states = {str(a): str(st) for a, st in conn.execute("SELECT asset_id, state FROM public.asset_throughput WHERE chart_id = %s AND asset_id IN ('ga_dashas', 'ga_positions') ORDER BY 1", (chart_id,)).fetchall()}
    return {"chart_dashas_build_ids": builds, "partitions_non_scope": int(non_scope), "partitions_scope_cap": int(scope), "asset_throughput": states}


def _capture_old(a, conn) -> int:
    """`--capture-old`: the PINNED (old) build, BEFORE S-L1."""
    return _capture_build(a, conn, PERM.DASHA_READ_CONTRACT["build_id"], a.capture_old, "pinned build (capture)")


def _capture_new(a, conn) -> int:
    """`--capture-new --new-build-id <uuid>` (steward ST-REPIN-CAPTURE-NEW): the SAME single REPEATABLE READ / READ ONLY snapshot, the SAME acquisition validation and the SAME rollback-then-close-then-write
    discipline as `--capture-old`, for the NEW (SETTLED-1) build — the durable POST record in the capture format (the offline intake checker reads it). The reference-row check applies only when that build is
    the pinned one (i.e. after the re-pin); before it the new build has no pinned reference ids."""
    return _capture_build(a, conn, a.new_build_id, a.capture_new, "new build (capture)")


def _capture_build(a, conn, build_id: str, path: str, label: str) -> int:
    """ONE short read-only transaction (REPEATABLE READ, READ ONLY — one snapshot) reads the Vimśottarī Lahiri levels 1–3 of the pinned build (with the window-truncation flags), the ten natal
    graha_position rows and the asset-state/build census; the capture is VALIDATED — the same validation the comparison will apply — BEFORE anything is written (a malformed or unusable capture is a
    named STOP with NO artifact); the connection is rolled back and closed BEFORE the file is written; prints the data sha256, the whole-file sha256 and the elapsed time (Suvarṇa: in the hour BEFORE S-L1)."""
    started = time.monotonic()
    old_id = build_id
    own = conn is None
    if own:
        conn = open_capture_connection()
    meta: dict = {}
    stop = None
    try:
        try:
            if own:
                meta["snapshot_start"] = conn.execute("SELECT pg_current_snapshot()::text").fetchone()[0]           # the FIRST statement opens the transaction
                meta["transaction_isolation"] = conn.execute("SHOW transaction_isolation").fetchone()[0]
                meta["transaction_read_only"] = conn.execute("SHOW transaction_read_only").fetchone()[0]
                if meta["transaction_isolation"] != "repeatable read" or meta["transaction_read_only"] != "on":
                    raise ReaderRefused(f"the capture transaction is {meta['transaction_isolation']!r} / read_only {meta['transaction_read_only']!r}, not repeatable read / on")
            rows = read_levels(conn, a.chart_id, old_id, label)
            natal = read_natal(conn, a.chart_id)
            meta["census"] = capture_census(conn, a.chart_id)
            if own:
                meta["snapshot_end"] = conn.execute("SELECT pg_current_snapshot()::text").fetchone()[0]
                if meta["snapshot_end"] != meta["snapshot_start"]:
                    raise ReaderRefused("the snapshot changed during the capture — it was NOT one transaction")
        except (ReaderRefused, NatalRefused) as exc:
            stop = str(exc)
        except Exception as exc:                     # a database error mid-capture is a NAMED STOP too (the transaction is rolled back and closed below)
            stop = f"the capture read failed: {type(exc).__name__}: {exc}"
    finally:
        if own:
            try:
                conn.rollback()                      # a read-only transaction is ended, never committed
            finally:
                conn.close()
    if stop:
        print(f"STOP — {stop}", file=sys.stderr); return 3
    meta.update({"captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tool_commit": _tool_commit(), "tool_sha256": file_sha256(__file__),
                 "natal_build_ids": sorted({n["build_id"] for n in natal}), "dasha_build_ids": sorted({r["build_id"] for r in rows})})
    cap = build_capture(a.chart_id, old_id, rows, natal, meta)
    bad = validate_capture(cap, a.chart_id, old_id)                  # THE loader's validation, at acquisition (Codex R18-2)
    if bad:
        print("STOP — this capture could NOT later be used (nothing written; fix and re-capture while the old rows exist): " + "; ".join(bad[:8]), file=sys.stderr); return 3
    cap["meta"]["elapsed_seconds"] = round(time.monotonic() - started, 3)
    write_capture(path, cap)
    print(f"captured {len(rows)} daśā rows (levels 1–3) of {old_id} and {len(natal)} natal longitudes -> {path}")
    print(f"sha256 {cap['sha256']}   (data + identity + selection)")
    print(f"whole-file sha256 {file_sha256(path)}   (record it separately)")
    print(f"one {meta.get('transaction_isolation', 'injected')} read-only transaction, connection closed; elapsed {cap['meta']['elapsed_seconds']} s")
    return 0


_RULING_ENTRY = re.compile(r".+:[1-9][0-9]*")


def validate_rulings(r) -> dict:
    """The rulings file's STRUCTURE, validated in the single validation phase (Codex v1.5): an object whose ONLY keys are `rewrite` and `keep`, each (when present) a list of DISTINCT strings of the form
    `path:line`; no entry may be both rewritten and kept. Raises ValueError by name; never anything else."""
    if not isinstance(r, dict):
        raise ValueError("the rulings must be a JSON object {rewrite: [path:line…], keep: [path:line…]}")
    extra = sorted(k for k in r if k not in ("rewrite", "keep"))
    if extra:
        raise ValueError(f"unknown rulings key(s) {', '.join(repr(k) for k in extra)}: only 'rewrite' and 'keep' are allowed")
    for k in ("rewrite", "keep"):
        v = r.get(k, [])
        if not isinstance(v, list):
            raise ValueError(f"rulings[{k!r}] must be a list of 'path:line' strings")
        bad = [x for x in v if not (isinstance(x, str) and _RULING_ENTRY.fullmatch(x))]
        if bad:
            raise ValueError(f"rulings[{k!r}] entries must be 'path:line' strings; refused: {bad[:3]!r}")
        if len(set(v)) != len(v):
            raise ValueError(f"rulings[{k!r}] repeats an entry")
    both = sorted(set(r.get("rewrite", [])) & set(r.get("keep", [])))
    if both:
        raise ValueError(f"rulings classify {both[:3]!r} as BOTH rewrite and keep")
    return {"rewrite": list(r.get("rewrite", [])), "keep": list(r.get("keep", []))}


def _read_operator_inputs(a, old_id: str):
    """Reads and validates every operator-supplied input BEFORE any side effect: (notice | None, old-rows capture | None, rulings | None). Raises only OSError / ValueError (a named STOP)."""
    notice = load_notice(a.settled_notice) if a.settled_notice else None
    old_rows = load_capture(a.old_rows, a.chart_id, old_id) if a.old_rows else None
    rulings = None
    if a.rulings:
        try:
            raw_rulings = strict_json_loads(Path(a.rulings).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"the rulings file is not valid strict JSON: {exc}") from None
        try:
            rulings = validate_rulings(raw_rulings)
        except ValueError as exc:
            raise ValueError(f"the rulings file is invalid: {exc}") from None
    return notice, old_rows, rulings


def main(argv=None, *, conn=None) -> int:
    """The CLI behind ONE TOP-LEVEL GUARD (Codex v1.6): argparse usage errors keep their exit 2 (SystemExit) and Ctrl-C passes, but ANY other exception — from validation, I/O, encoding, a malformed input nobody
    anticipated — becomes `STOP: <Type>: <reason>`, exit 3, never a traceback. Every write goes through `write_atomic` (strict UTF-8, temp file + replace), so a refused or failed run leaves no half-written file."""
    try:
        return _main_impl(argv, conn=conn)
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException as exc:                                    # includes RecursionError / MemoryError / AssertionError
        try:
            print(f"STOP: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        except Exception:
            pass
        return 3


def cli_string_problems(a) -> list[str]:
    """Every string-valued CLI argument must be strict-UTF-8 text without NUL (a lone surrogate arrives from undecodable argv bytes and breaks encoding of the report, the evidence file or a path only
    AFTER the checks have passed). The value is never echoed — only the flag name."""
    out = []
    for k, v in sorted(vars(a).items()):
        if isinstance(v, str):
            try:
                v.encode("utf-8")
            except UnicodeEncodeError:
                out.append(f"--{k.replace('_', '-')} is not valid UTF-8 text (a lone surrogate)")
                continue
            if "\x00" in v:
                out.append(f"--{k.replace('_', '-')} contains a NUL character")
    return out


def _same_file(p: str | Path, q: str | Path) -> bool:
    """The same file by resolved path, or by identity when both exist (a symlink or a hard link to a source is the source)."""
    try:
        if os.path.realpath(p) == os.path.realpath(q):
            return True
        return os.path.exists(p) and os.path.exists(q) and os.path.samefile(p, q)
    except OSError:
        return False


def io_collision_problems(a) -> list[str]:
    """Codex v1.8 P1-1 (threat list T-OUT): no evidence/capture OUTPUT may be the same file as an INPUT, as another output, or as anything --apply rewrites — checked BEFORE any read or write. Without
    this an `--apply --out permission.py` overwrote the pin with its own CLEAN report. Reserved: every input file, permission.py, the verifier, the generated test, every tests/l3 `*.py` (the files an
    apply may rewrite) and this tool's own file."""
    outputs = [(f, v) for f, v in (("--out", a.out), ("--capture-old", a.capture_old), ("--capture-new", a.capture_new), ("--w0-capture-out", a.w0_capture_out)) if v]
    reserved: list[tuple[str, str | Path]] = [(f, v) for f, v in (("--forensic-report", a.forensic_report), ("--settled-notice", a.settled_notice), ("--old-rows", a.old_rows),
                                                                    ("--rulings", a.rulings), ("--import-w0", a.import_w0)) if v]
    reserved += [("permission.py", SIDECAR / "services" / "gochara_rules" / "permission.py"), ("inventory_verifier.py", SIDECAR / "services" / "gochara_kernel" / "inventory_verifier.py"),
                 ("the re-pin tool", Path(__file__))]
    if isinstance(a.new_build_id, str) and a.new_build_id:
        reserved.append(("the generated test", SIDECAR / "tests" / "l3" / "gochara_rules" / f"test_am10_repin_{a.new_build_id[:8]}.py"))
    tests = SIDECAR / "tests" / "l3"
    if tests.is_dir():
        reserved += [("a tests/l3 file", q) for q in tests.rglob("*.py") if q.is_file()]
    out: list[str] = []
    for i, (flag, path) in enumerate(outputs):
        for what, other in reserved:
            if _same_file(path, other):
                out.append(f"{flag} {path} is the same file as {what}")
        for flag2, path2 in outputs[i + 1:]:
            if _same_file(path, path2):
                out.append(f"{flag} and {flag2} name the same file ({path})")
    return out


def _write_failed_evidence(a, report: str, note: str) -> None:
    """With --apply the evidence file is written after the apply; when the apply does NOT succeed the comparison verdict is still recorded, but under a prominent failure header — a CLEAN report never
    stands alone beside a failed apply. Best effort (the failure itself is already reported on stderr)."""
    if a.out:
        try:
            write_atomic(a.out, f"# !!! RE-PIN NOT APPLIED — {note}\n\n" + report)
        except Exception:                                    # noqa: BLE001
            pass


def _output_problem(a) -> str | None:
    for flag, path in (("--out", a.out), ("--capture-old", a.capture_old), ("--capture-new", a.capture_new), ("--w0-capture-out", a.w0_capture_out)):
        if path:
            problem = output_path_problem(path)
            if problem:
                return f"{flag}: {problem}"
    collisions = io_collision_problems(a)
    if collisions:
        return "; ".join(collisions[:4])
    return None


def _main_impl(argv=None, *, conn=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--new-build-id", default=None, help="the SETTLED-1 build — REQUIRED for comparison/application, REFUSED with --capture-old")
    ap.add_argument("--chart-id", default=PERM.DASHA_READ_CONTRACT["chart_id"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--forensic-report", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the full report and the test-literal matches; write NOTHING (no --out, no --apply)")
    ap.add_argument("--settled-notice", default=None, help="JSON of Suvarṇa's SETTLED-1 notice: expected per-level shift + a stated tolerance (see load_notice)")
    ap.add_argument("--settled-received", default=None, help="the steward's message id announcing 'SETTLED-1 received' — REQUIRED for --apply (local patch PREPARATION). Production Gochara work stays held (ST-SL1-HOLD) until the reviewed re-pin is merged and the steward lifts the hold; this flag does NOT lift it")
    ap.add_argument("--system", default="vimshottari", help="REFUSED unless vimshottari — the pin is the Vimśottarī read; other systems are out of scope")
    ap.add_argument("--max-level", type=int, default=3, help="REFUSED unless 3 — levels 1–3 (MD/AD/PD) only; level-4 counts change by design at S-L1")
    ap.add_argument("--capture-old", default=None, help="READ-ONLY: write the OLD (pinned) build's rows to this file BEFORE S-L1 and exit — the old rows may not exist afterwards")
    ap.add_argument("--capture-new", default=None, help="READ-ONLY: with --new-build-id, write the NEW (SETTLED-1) build's rows to this file in the capture format (the durable POST record) and exit; same snapshot/validation discipline as --capture-old")
    ap.add_argument("--import-w0", default=None, help="Suvarṇa's W0 fallback baseline (JSON in this tool's capture fields); needs --w0-checksum and --w0-capture-out; re-written as a capture")
    ap.add_argument("--w0-checksum", default=None, help="the SHA-256 of the W0 file named by SETTLED-1")
    ap.add_argument("--w0-capture-out", default=None, help="where the imported capture is written")
    ap.add_argument("--old-rows", default=None, help="the file written by --capture-old: the old build's rows when the DB no longer holds them")
    ap.add_argument("--rulings", default=None, help="JSON {rewrite: [path:line…], keep: [path:line…]} — the steward's ruling on test literals that equal an old boundary")
    a = ap.parse_args(argv)
    bad_cli = cli_string_problems(a)         # Codex v1.7 P1-4: every CLI string is validated BEFORE any read, connection or write (JSON inputs get the same discipline in their own loaders)
    if bad_cli:
        print("STOP — " + "; ".join(bad_cli) + "; nothing was read or written", file=sys.stderr); return 3
    bad_chart = chart_id_problem(a.chart_id)                              # Codex v1.8 P1-4: BEFORE any dispatch, read or write
    if bad_chart:
        print(f"STOP — --chart-id: {bad_chart}; nothing was read or written", file=sys.stderr); return 3
    bad = _mode_error(a)                     # BEFORE any capture, connection or read (Codex R17-7)
    if bad:
        print(bad, file=sys.stderr); return 2
    bad_out = _output_problem(a)                                         # output destinations are validated BEFORE any read or write (a directory, a missing directory)
    if bad_out:
        print(f"STOP — {bad_out}; nothing was read or written", file=sys.stderr); return 3
    if a.import_w0:
        return import_w0(a.import_w0, a.w0_checksum, a.w0_capture_out, a.chart_id)
    if a.capture_old:
        return _capture_old(a, conn)
    if a.capture_new:
        return _capture_new(a, conn)
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    if a.chart_id != PERM.DASHA_READ_CONTRACT["chart_id"]:
        print(f"WARNING: --chart-id {a.chart_id} is not the canonical chart {PERM.DASHA_READ_CONTRACT['chart_id']}; the comparison is for evidence only and --apply is refused", file=sys.stderr)
    if a.new_build_id == old_id:
        print("new build equals the current pin — nothing to re-pin", file=sys.stderr); return 2
    if a.forensic_report is not None:
        fr = Path(a.forensic_report)
        if not fr.is_file() or fr.stat().st_size == 0:
            print(f"STOP — --forensic-report {a.forensic_report} does not exist or is empty (evidence item (e): the seven FORENSIC anchors)", file=sys.stderr); return 3
    # ONE VALIDATION PHASE (Codex v1.4): EVERY operator-supplied input — the SETTLED-1 notice, the rulings, the capture (--old-rows) — is read and validated HERE, before the connection, the first read, the first
    # report line, the first write and any CLEAN line. It can end only in a named exit 3 (never a traceback, never a partial write); a last-resort handler turns any unexpected exception into the same STOP.
    try:
        notice, old_rows_capture, rulings = _read_operator_inputs(a, old_id)
    except (OSError, ValueError) as exc:
        print(f"STOP — {exc}", file=sys.stderr); return 3
    except Exception as exc:                                    # last resort: anything unexpected while validating operator input
        print(f"STOP — invalid operator input ({type(exc).__name__}); nothing was read from the database and nothing was written", file=sys.stderr); return 3
    if conn is None:
        conn = open_readonly_connection()
    try:
        if a.old_rows:
            old_rows = old_rows_capture
        else:
            old_rows = read_levels(conn, a.chart_id, old_id, "old build")
        # (a capture that carries level-4 rows is REFUSED at load by validate_capture — there is nothing to filter here; a W0 file's level-4 rows are dropped, with a count, at import)
        new_rows = read_levels(conn, a.chart_id, a.new_build_id, "new build")
    except ReaderRefused as exc:
        print(f"STOP — {exc}", file=sys.stderr); return 3
    # tier is pinned IN the query (two_pass_verified): an empty result means the new build is absent or at another tier
    new_tier_ok = bool(new_rows) and all(r.get("verification_pass_status") == PERM.DASHA_READ_CONTRACT["tier"] for r in new_rows)
    tree_issues = (tree_problems(old_rows, "old build") + tree_problems(new_rows, "new build")           # Codex R17-4: well-formed trees BEFORE any comparison
                   + row_contract_problems(old_rows, old_id, "old build") + row_contract_problems(new_rows, a.new_build_id, "new build"))        # Codex R18-1: every row against its build and the read contract
    old_idx, new_idx = index_paths(old_rows), index_paths(new_rows)
    m = match(old_idx, new_idx)
    refusals = subtree_refusals(old_idx, new_idx)
    m = {**m, "matched": [k for k in m["matched"] if not under_refused(k, refusals)]}                          # a refused subtree is not paired at all (no best guess)
    edges = edge_report(old_idx, new_idx, m["matched"])                                # Fable F-R18-1: window-clipped edges are accounted, excluded from the statistics, required unchanged
    stats = shift_stats(old_idx, new_idx, m["matched"])
    flips = path_lord_flips(old_idx, new_idx, m["matched"])                       # D7: every matched row keeps its lord — the STOP
    sensitive = lord_flips(old_rows, new_rows, oracle_instants()) if new_rows else []   # instants whose lord differs because a boundary MOVED — reported, D8
    maps, ref_problems = remeasure_reference_rows(old_idx, new_idx)
    builds = fetch_vimshottari_builds(conn, a.chart_id)
    pre_facts = fetch_preflight_facts(conn, a.chart_id)
    verifier_builds = fetch_verifier_builds(conn, a.chart_id)
    extra_stops = (build_problems(builds, a.new_build_id) + verifier_build_problems(verifier_builds, a.new_build_id)
                   + preflight_problems(pre_facts, a.new_build_id))
    stops = decide(new_tier_ok=new_tier_ok, new_integrity=integrity(new_rows), m=m, flips=flips,
                   ref_problems=ref_problems, forensic_report=a.forensic_report, shift_issues=shift_problems(stats, notice),
                   tree_issues=tree_issues, old_totals=level_totals(old_rows), new_totals=level_totals(new_rows), refused_subtrees=refusals, edge_issues=edges["problems"])
    stops += extra_stops
    if notice is not None and notice.get("new_build_id") != a.new_build_id:                         # Codex R17-5: notice == --new-build-id == the database readback (the builds check above)
        stops.append(f"the SETTLED-1 notice names build {notice.get('new_build_id')}, not {a.new_build_id}")
    if a.apply and not stops:                                  # resolve EVERY apply-time refusal (test-literal rulings, the verifier's second pin site, literal conflicts) BEFORE the report is emitted or CLEAN is printed (Codex v1.5)
        try:
            apply_repin(a.new_build_id, maps, SIDECAR.parents[1], rulings=rulings, review=[], check_only=True)
        except NeedsRuling as exc:
            stops.append(f"{len(exc.unclassified)} test literal(s) equal to an old boundary need the steward's ruling (--rulings): " + "; ".join(exc.unclassified[:5]))
        except VerifierPinMissing as exc:
            stops.append(f"apply would be refused: {exc}")
        except Exception as exc:                               # an assertion or any unexpected failure while checking the repository state: a named STOP, nothing written
            stops.append(f"apply could not be checked ({exc.__class__.__name__}: {exc}); nothing was written")
    evidence = [f"window-clipped edges excluded from the shift statistics (clipped on BOTH builds, required unchanged), per level: "
                + (", ".join(f"{LEVEL_NAME.get(lv, lv)} start {c['start']} / end {c['end']}" for lv, c in edges["clipped"].items()) or "none")]
    evidence.append(f"chart_dashas shape: observed {pre_facts['non_scope']} non-scope + {pre_facts['scope']} scope-cap partition(s), builds {sorted(pre_facts['builds'])}; required: {EXPECTED_NON_SCOPE_PARTITIONS} + {EXPECTED_SCOPE_PARTITIONS} and exactly the SETTLED-1 build {a.new_build_id} (fixed; no notice field overrides it)")
    evidence.append(f"verifier predicate (every Vimśottarī / Lahiri row, all levels and tiers, NULL included): builds {verifier_builds} — "
                    + ("exactly the SETTLED-1 build" if verifier_builds == [a.new_build_id] else "NOT exactly the SETTLED-1 build"))
    if notice is not None:
        evidence.append(f"settled notice sha256: {notice['_sha256']}; source message {notice['source_message_id']}" + (f"; levels {notice['_ignored_levels']} in the notice were IGNORED (this tool judges levels 1–3 only)" if notice["_ignored_levels"] else ""))
    if a.forensic_report:
        evidence.append(f"forensic report sha256: {hashlib.sha256(Path(a.forensic_report).read_bytes()).hexdigest()} — this tool checks that the file EXISTS and is NON-EMPTY ONLY; CLEAN is NOT independent validation of the seven FORENSIC anchors (that evidence is the L1 owner's)")
    report = render(old_id=old_id, new_id=a.new_build_id, chart_id=a.chart_id, o_int=integrity(old_rows),
                    n_int=integrity(new_rows), m=m, stats=stats, flips=flips, sensitive=sensitive, maps=maps, stops=stops, evidence=evidence)
    if a.out and not a.dry_run and not (a.apply and not stops):
        write_atomic(a.out, report)                                       # with --apply the evidence is written AFTER the apply (below): a CLEAN report must not outlive a failed apply
    print(report)
    if stops:
        print("STOP — not re-pinning.", file=sys.stderr); return 3
    if a.dry_run or not a.apply:
        # list every test literal equal to an old boundary so the ruling can be prepared (nothing is written)
        inst = {x["old"][side]: iso(x["new"][side]) for x in maps for side in ("start_iso", "end_iso")}
        for p_, ln, a_, b_ in scan_test_literals(inst, SIDECAR.parents[1]):
            print(f"TEST LITERAL (needs ruling at --apply): {p_}:{ln} {a_} -> {b_}")
        ids_ = {x["old"]["row_id"]: x["new"]["dasha_row_id"] for x in maps}
        for p_, ln, o_ in scan_wrapped_ids(ids_, SIDECAR.parents[1]):
            print(f"WRAPPED ID (rewritten character for character at --apply; no ruling needed): {p_}:{ln} {o_} -> {ids_[o_]}")
        wide = scan_wide_literals(inst, SIDECAR.parents[1])
        for p_, ln, a_, b_ in wide:
            print(f"WIDE SCAN (report only: never rewritten, never blocking; a KEEP candidate or a follow-up): {p_}:{ln} {a_} -> {b_}")
        print(f"WIDE SCAN summary: {len(wide)} match(es) in {len({w[0] for w in wide})} file(s) outside tests/l3 (Julian-day numbers are not searched)")
    if a.apply:
        review: list[str] = []
        try:
            for f in apply_repin(a.new_build_id, maps, SIDECAR.parents[1], rulings=rulings, review=review):
                print("changed:", f)
        except NeedsRuling as exc:
            for r in exc.unclassified:
                print("NEEDS RULING (nothing written):", r, file=sys.stderr)
            _write_failed_evidence(a, report, "NEEDS RULING — nothing written")
            print("STOP — test literals equal to an old boundary need the steward's ruling (--rulings).", file=sys.stderr); return 3
        except VerifierPinMissing as exc:
            _write_failed_evidence(a, report, f"REFUSED — nothing written: {exc}")
            print(f"STOP (nothing written) — {exc}", file=sys.stderr); return 3
        except Exception as exc:                               # last resort: never a traceback; the apply restores what it had written (write_all_or_restore); inspect `git status` anyway
            _write_failed_evidence(a, report, f"APPLY FAILED ({exc.__class__.__name__}) — the files written so far were restored; inspect `git status`")
            print(f"STOP — the apply failed unexpectedly ({exc.__class__.__name__}: {exc}); written files were restored; inspect `git status`", file=sys.stderr); return 3
        if a.out:
            write_atomic(a.out, report)                       # the evidence of a SUCCESSFUL apply
        print(f"re-pin PREPARED locally on 'SETTLED-1 received' per {a.settled_received}. ST-SL1-HOLD REMAINS IN FORCE for production Gochara work until this re-pin is reviewed and merged and the steward announces the hold lifted.")
        print("BOTH pin constants were rewritten and verified equal to the SETTLED-1 build: services/gochara_rules/permission.py DASHA_READ_CONTRACT['build_id'] AND services/gochara_kernel/inventory_verifier.py _C_BUILD.")
        print("NEXT, in the SAME reviewed re-pin PR: regenerate the implementation lock — `python -m services.gochara_kernel.implementation_registry --write` (a changed governed module moves the implementation digest; the seal refuses an unregistered one) AND the golden brief fixtures that move with it — tests/l3/gochara/fixtures/golden_brief_stdout_1class.txt and golden_brief_log_entries_1class.json (regenerate them the way Stream A's tests document, then re-run the A5.3 suite).")
        for r in review:
            print("ruled:", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
