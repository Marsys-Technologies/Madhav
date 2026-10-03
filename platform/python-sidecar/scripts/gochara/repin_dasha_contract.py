#!/usr/bin/env python3
"""AM-10 re-pin tool — the §4.0 daśā read contract, one command when the L1 rebuild lands.

Draft AM-10 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-10) rules: ONE pin, no auto-follow; a
re-pin is by EVIDENCE only, in one small PR; any class flip / lord flip / anchor failure is
a STOP, not a re-pin. This tool produces the evidence and, only with --apply and only when
nothing stops it, performs the single change.

    python3 scripts/gochara/repin_dasha_contract.py --new-build-id <uuid> \\
        [--chart-id 482012f1-…] [--out evidence.md] [--forensic-report path]
        [--settled-notice notice.json]      # Suvarṇa's SETTLED-1 notice: expected per-level shift + a STATED tolerance — the measured shift must match or the verdict is STOP
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
  * tests/l3/**/*.py: ONLY the reference rows' ids and the old pin's build id (exact-string, ONE pass). An old boundary INSTANT in a test is NOT rewritten — it may be an event date
    that merely equals a boundary (D8) — it is printed as `REVIEW path:line old -> new` for a human;
  * a generated tests/l3/gochara_rules/test_am10_repin_<build8>.py asserting the OLD id is refused
    (DashaReadConflict) and the NEW id accepted (rule 2(g)).
The frozen v1.4 spec/oracle JSON are never edited (rule 3).

MOSHIER → SWISS (Suvarṇa addendum 4; steward M20261002T222913-35c5): the stored rows were built on the Moshier fallback; at S-L1 the Vimśottarī BOUNDARIES move by ≈ 1.94 h while lords and
row counts hold. So a MOVED boundary is not a flip: the STOP is a different lord (or a missing/extra row) at ANY matched (level, parent path, index) row (D7); the oracle instants whose lord
differs only because an edge moved are reported as BOUNDARY-SENSITIVE (D8), and the per-level old → new shift is in the evidence.

G6 (steward M20261002T223036-02f0): the §4.0 read accepts the pinned build WHILE ITS ROWS ARE PRESENT even if another build coexists (dasha_read.py:44–49). So the verdict is STOP unless
chart_dashas holds EXACTLY ONE Vimśottarī build (Lahiri, levels 1–3, any tier) and it is the SETTLED-1 build; --apply asserts the re-pinned constant equals that build and the old pin is gone.
(The writer-side refusal when more than one two_pass_verified build is present is a separate Stream A code change.)
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
import uuid
import os
import re
import statistics
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
LEVELS_IN_SCOPE = (1, 2, 3)          # Vimśottarī Lahiri MD/AD/PD only (steward M20261002T230554 / Suvarṇa addendum 7): lords and row counts must be EQUAL here; level 4 is out of scope


# ── pure helpers (unit-tested) ───────────────────────────────────────────────
def _t(s) -> datetime:
    if isinstance(s, datetime):
        return s.astimezone(timezone.utc) if s.tzinfo else s.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


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


def shift_stats(old: dict, new: dict, matched: list) -> dict:
    per: dict[int, dict[str, list[float]]] = {}
    for k in matched:
        lv = k[0]
        d = per.setdefault(lv, {"start": [], "end": []})
        d["start"].append((_t(new[k]["start_iso"]) - _t(old[k]["start_iso"])).total_seconds())
        d["end"].append((_t(new[k]["end_iso"]) - _t(old[k]["end_iso"])).total_seconds())
    return {lv: {side: {"min": min(v), "max": max(v), "mean": statistics.fmean(v), "n": len(v)} for side, v in d.items()}
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
    """READ-ONLY: every Vimśottarī build present for the chart at the Lahiri levels 1–3, ANY tier -> row count. The §4.0 read accepts the pinned build WHILE ITS ROWS ARE PRESENT even if
    another build coexists (dasha_read.py:44–49), so after S-L1 a coexisting old build would be read silently — G6."""
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


def build_problems(builds: dict[str, int], new_id: str) -> list[str]:
    """G6 (a): exactly ONE Vimśottarī build exists for the chart (Lahiri, levels 1–3) and it is the SETTLED-1 build."""
    if set(builds) == {new_id}:
        return []
    return [f"chart_dashas holds Vimśottarī build(s) {sorted(builds)} (Lahiri levels 1–3); exactly ONE — the SETTLED-1 build {new_id} — must exist (G6: the read accepts the pinned OLD build while its rows are present, so a coexisting old build would be read silently)"]


def _rows_digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _capture_digest(rows: list[dict], natal: list[dict] | None) -> str:
    return hashlib.sha256(json.dumps({"rows": rows, "natal": natal or []}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def write_capture(path: str, chart_id: str, build_id: str, rows: list[dict], natal: list[dict] | None = None, meta: dict | None = None) -> str:
    """The OLD build's rows (+ the ten natal longitudes), captured READ-ONLY BEFORE S-L1 (the old rows may no longer exist afterwards): {chart_id, build_id, rows, natal, meta, sha256} — `sha256` covers
    `rows` AND `natal` (the canonical JSON); `meta` records how it was read (isolation, read-only, snapshot, elapsed). The file is the evidence the comparison uses."""
    d = {"chart_id": chart_id, "build_id": build_id, "rows": rows, "natal": natal or [], "meta": meta or {}, "sha256": _capture_digest(rows, natal)}
    Path(path).write_text(json.dumps(d, indent=1, sort_keys=True), encoding="utf-8")
    return d["sha256"]


def load_capture_full(path: str, chart_id: str, build_id: str) -> dict:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if d.get("chart_id") != chart_id or d.get("build_id") != build_id or not d.get("rows") or d.get("sha256") != _capture_digest(d["rows"], d.get("natal")):
        raise ValueError("the captured old-rows file is not for this chart and the pinned build, is empty, or its sha256 does not match its rows and natal longitudes")
    bad = tree_problems(d["rows"], "captured old rows")
    if bad:
        raise ValueError("the captured old-rows file is malformed: " + "; ".join(bad[:6]))                  # Codex R17-4: a malformed old capture STOPS the comparison
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
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def load_notice(path: str) -> dict:
    """Suvarṇa's SETTLED-1 notice as JSON: {"settled_1": true, "new_build_id": "<uuid>", "expected_shift_seconds": {"1": 6993, "2": 6993, "3": {"start": 6992, "end": 6994}}, "tolerance_seconds": 2}.
    STRICT (Codex R17-3/R17-5): `new_build_id` is REQUIRED and a valid UUID; `expected_shift_seconds` names EXACTLY levels 1, 2 and 3, each a FINITE number or {start, end} of finite numbers (both
    boundaries); `tolerance_seconds` is a FINITE number >= 1 (every instant on both sides is whole-second-formatted in the permission literals, and the notice's own are second-resolution) — NaN and
    infinities are refused; the tolerance is STATED by the notice — there is no default. The notice's sha256 is recorded in the tool's output."""
    raw = Path(path).read_bytes()
    d = json.loads(raw.decode("utf-8"))
    problems = []
    if d.get("settled_1") is not True:
        problems.append("settled_1 must be true")
    try:
        uuid.UUID(str(d.get("new_build_id")))
    except ValueError:
        problems.append("new_build_id is required and must be a valid UUID (the settlement build identifier)")
    exp = d.get("expected_shift_seconds")
    if not isinstance(exp, dict) or set(exp) != {str(lv) for lv in LEVELS_IN_SCOPE}:
        problems.append("expected_shift_seconds must name exactly levels 1, 2 and 3")
    else:
        for k, e in exp.items():
            ok = _finite_number(e) or (isinstance(e, dict) and set(e) == {"start", "end"} and _finite_number(e["start"]) and _finite_number(e["end"]))
            if not ok:
                problems.append(f"expected_shift_seconds[{k}] must be a finite number or {{start, end}} of finite numbers")
    tol = d.get("tolerance_seconds")
    if not _finite_number(tol) or tol < MIN_TOLERANCE_SECONDS:
        problems.append(f"tolerance_seconds must be a FINITE number >= {MIN_TOLERANCE_SECONDS}")
    if problems:
        raise ValueError("the SETTLED-1 notice is invalid: " + "; ".join(problems))
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
           tree_issues: list[str] | None = None, old_totals: dict | None = None, new_totals: dict | None = None, refused_subtrees: list[dict] | None = None) -> list[str]:
    stops = list(shift_issues or []) + list(tree_issues or [])
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


def scan_test_literals(instants: dict[str, str], repo_root: Path) -> list[tuple[str, int, str, str]]:
    out = []
    for p in sorted((SIDECAR / "tests" / "l3").rglob("*.py")):
        for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for a_, b_ in instants.items():
                if a_ in line:
                    out.append((str(p.relative_to(repo_root)), ln, a_, b_))
    return out


def apply_repin(new_id: str, maps: list[dict], repo_root: Path, rulings: dict | None = None, review: list[str] | None = None) -> list[str]:
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
            instants[o[side]] = literal
    ver = SIDECAR / "services" / "gochara_kernel" / "inventory_verifier.py"
    if not ver.is_file():
        raise VerifierPinMissing(f"{ver} is absent: the verifier's INDEPENDENT pin (`_C_BUILD`) cannot be rewritten — run the re-pin on a tree that carries the '5.0' kernel")
    ver_txt = ver.read_text(encoding="utf-8")
    ver_old_line = f'_C_BUILD = "{old_id}"'
    if ver_txt.count(ver_old_line) != 1:
        raise VerifierPinMissing(f"{ver}: expected exactly ONE `{ver_old_line}` line, found {ver_txt.count(ver_old_line)} (the verifier's pin is a second site; it must equal the permission.py pin before and after)")
    matches = scan_test_literals(instants, repo_root)
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
    perm.write_text(s, encoding="utf-8")
    ver.write_text(new_ver, encoding="utf-8")
    changed.append(str(perm.relative_to(repo_root)))
    changed.append(str(ver.relative_to(repo_root)))
    by_file: dict[str, dict[int, dict[str, str]]] = {}
    for p, ln, a_, b_ in matches:
        if ruled.get(f"{p}:{ln}") == "rewrite":
            by_file.setdefault(p, {}).setdefault(ln, {})[a_] = b_
    for p in sorted((SIDECAR / "tests" / "l3").rglob("*.py")):
        txt = p.read_text(encoding="utf-8")
        rel = str(p.relative_to(repo_root))
        lines = txt.splitlines(keepends=True)
        for ln, mp in by_file.get(rel, {}).items():
            lines[ln - 1] = rewrite_once(lines[ln - 1], mp)                            # ONLY the ruled lines
        new_txt = rewrite_once("".join(lines), {**ids, old_id: new_id})
        if new_txt != txt:
            p.write_text(new_txt, encoding="utf-8"); changed.append(rel)
    gen = SIDECAR / "tests" / "l3" / "gochara_rules" / f"test_am10_repin_{new_id[:8]}.py"
    gen.write_text(GENERATED_TEST.format(old=old_id, new=new_id), encoding="utf-8")
    changed.append(str(gen.relative_to(repo_root)))
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
    if a.capture_old:
        extra = [flag for flag, val in (("--new-build-id", a.new_build_id), ("--dry-run", a.dry_run), ("--apply", a.apply), ("--settled-notice", a.settled_notice), ("--old-rows", a.old_rows),
                                        ("--rulings", a.rulings), ("--forensic-report", a.forensic_report), ("--out", a.out), ("--settled-received", a.settled_received)) if val]
        if extra:
            return f"--capture-old is a capture-only mode (read-only, writes only its own file); it cannot be combined with {', '.join(extra)}"
        return None
    if not a.new_build_id:
        return "--new-build-id is required for comparison and application (it is not used by --capture-old)"
    try:
        uuid.UUID(a.new_build_id)
    except ValueError:
        return f"--new-build-id {a.new_build_id!r} is not a valid UUID"
    if a.dry_run and a.apply:
        return "--dry-run and --apply are mutually exclusive (a dry run writes nothing)"
    if a.apply and not a.settled_received:
        return "--apply refused: pass --settled-received <the steward's message id announcing 'SETTLED-1 received'> (local re-pin PREPARATION; production Gochara work stays held until the reviewed re-pin is merged and the steward lifts ST-SL1-HOLD)"
    if a.rulings and not a.apply:
        return "--rulings only applies with --apply"
    return None


def _capture_old(a, conn) -> int:
    """ONE short read-only transaction (REPEATABLE READ, READ ONLY — one snapshot) reads the Vimśottarī Lahiri levels 1–3 of the pinned build AND the ten natal graha_position rows; writes the file
    + sha256; the connection is closed (rolled back, never committed) BEFORE the tool returns; prints the elapsed time (Suvarṇa: run it in the hour BEFORE S-L1, never during the window)."""
    started = time.monotonic()
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    own = conn is None
    if own:
        conn = open_capture_connection()
    meta: dict = {}
    try:
        try:
            if own:
                meta["snapshot_start"] = conn.execute("SELECT pg_current_snapshot()::text").fetchone()[0]           # the FIRST statement opens the transaction
                meta["transaction_isolation"] = conn.execute("SHOW transaction_isolation").fetchone()[0]
                meta["transaction_read_only"] = conn.execute("SHOW transaction_read_only").fetchone()[0]
                if meta["transaction_isolation"] != "repeatable read" or meta["transaction_read_only"] != "on":
                    raise ReaderRefused(f"the capture transaction is {meta['transaction_isolation']!r} / read_only {meta['transaction_read_only']!r}, not repeatable read / on")
            rows = read_levels(conn, a.chart_id, old_id, "pinned build (capture)")
            natal = read_natal(conn, a.chart_id)
            if own:
                meta["snapshot_end"] = conn.execute("SELECT pg_current_snapshot()::text").fetchone()[0]
                if meta["snapshot_end"] != meta["snapshot_start"]:
                    raise ReaderRefused("the snapshot changed during the capture — it was NOT one transaction")
        except (ReaderRefused, NatalRefused) as exc:
            print(f"STOP — {exc}", file=sys.stderr); return 3
    finally:
        if own:
            try:
                conn.rollback()                      # a read-only transaction is ended, never committed
            finally:
                conn.close()
    meta["captured_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["elapsed_seconds"] = round(time.monotonic() - started, 3)
    digest = write_capture(a.capture_old, a.chart_id, old_id, rows, natal, meta)
    print(f"captured {len(rows)} daśā rows (levels 1–3) of {old_id} and {len(natal)} natal longitudes -> {a.capture_old}")
    print(f"sha256 {digest}")
    print(f"one {meta.get('transaction_isolation', 'injected')} read-only transaction, connection closed; elapsed {meta['elapsed_seconds']} s")
    return 0


def main(argv=None, *, conn=None) -> int:
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
    ap.add_argument("--old-rows", default=None, help="the file written by --capture-old: the old build's rows when the DB no longer holds them")
    ap.add_argument("--rulings", default=None, help="JSON {rewrite: [path:line…], keep: [path:line…]} — the steward's ruling on test literals that equal an old boundary")
    a = ap.parse_args(argv)
    bad = _mode_error(a)                     # BEFORE any capture, connection or read (Codex R17-7)
    if bad:
        print(bad, file=sys.stderr); return 2
    if a.capture_old:
        return _capture_old(a, conn)
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    if a.new_build_id == old_id:
        print("new build equals the current pin — nothing to re-pin", file=sys.stderr); return 2
    if a.forensic_report is not None:
        fr = Path(a.forensic_report)
        if not fr.is_file() or fr.stat().st_size == 0:
            print(f"STOP — --forensic-report {a.forensic_report} does not exist or is empty (evidence item (e): the seven FORENSIC anchors)", file=sys.stderr); return 3
    if conn is None:
        conn = open_readonly_connection()
    try:
        if a.old_rows:
            try:
                old_rows = load_capture(a.old_rows, a.chart_id, old_id)
            except (OSError, ValueError) as exc:
                print(f"STOP — {exc}", file=sys.stderr); return 3
        else:
            old_rows = read_levels(conn, a.chart_id, old_id, "old build")
        old_rows = [r for r in old_rows if int(r["level_n"]) in LEVELS_IN_SCOPE]        # a capture taken earlier may carry level 4: out of scope, never compared
        new_rows = read_levels(conn, a.chart_id, a.new_build_id, "new build")
    except ReaderRefused as exc:
        print(f"STOP — {exc}", file=sys.stderr); return 3
    # tier is pinned IN the query (two_pass_verified): an empty result means the new build is absent or at another tier
    new_tier_ok = bool(new_rows) and all(r.get("verification_pass_status") == PERM.DASHA_READ_CONTRACT["tier"] for r in new_rows)
    tree_issues = tree_problems(old_rows, "old build") + tree_problems(new_rows, "new build")          # Codex R17-4: well-formed trees BEFORE any comparison
    old_idx, new_idx = index_paths(old_rows), index_paths(new_rows)
    m = match(old_idx, new_idx)
    refusals = subtree_refusals(old_idx, new_idx)
    m = {**m, "matched": [k for k in m["matched"] if not under_refused(k, refusals)]}                          # a refused subtree is not paired at all (no best guess)
    stats = shift_stats(old_idx, new_idx, m["matched"])
    flips = path_lord_flips(old_idx, new_idx, m["matched"])                       # D7: every matched row keeps its lord — the STOP
    sensitive = lord_flips(old_rows, new_rows, oracle_instants()) if new_rows else []   # instants whose lord differs because a boundary MOVED — reported, D8
    maps, ref_problems = remeasure_reference_rows(old_idx, new_idx)
    try:
        notice = load_notice(a.settled_notice) if a.settled_notice else None
    except (OSError, ValueError) as exc:
        print(f"STOP — {exc}", file=sys.stderr); return 3
    builds = fetch_vimshottari_builds(conn, a.chart_id)
    extra_stops = build_problems(builds, a.new_build_id) + preflight_problems(fetch_preflight_facts(conn, a.chart_id), a.new_build_id)
    stops = decide(new_tier_ok=new_tier_ok, new_integrity=integrity(new_rows), m=m, flips=flips,
                   ref_problems=ref_problems, forensic_report=a.forensic_report, shift_issues=shift_problems(stats, notice),
                   tree_issues=tree_issues, old_totals=level_totals(old_rows), new_totals=level_totals(new_rows), refused_subtrees=refusals)
    stops += extra_stops
    if notice is not None and notice.get("new_build_id") != a.new_build_id:                         # Codex R17-5: notice == --new-build-id == the database readback (the builds check above)
        stops.append(f"the SETTLED-1 notice names build {notice.get('new_build_id')}, not {a.new_build_id}")
    evidence = []
    if notice is not None:
        evidence.append(f"settled notice sha256: {notice['_sha256']}")
    if a.forensic_report:
        evidence.append(f"forensic report sha256: {hashlib.sha256(Path(a.forensic_report).read_bytes()).hexdigest()} — this tool checks that the file EXISTS and is NON-EMPTY ONLY; CLEAN is NOT independent validation of the seven FORENSIC anchors (that evidence is the L1 owner's)")
    report = render(old_id=old_id, new_id=a.new_build_id, chart_id=a.chart_id, o_int=integrity(old_rows),
                    n_int=integrity(new_rows), m=m, stats=stats, flips=flips, sensitive=sensitive, maps=maps, stops=stops, evidence=evidence)
    if a.out and not a.dry_run:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    if stops:
        print("STOP — not re-pinning.", file=sys.stderr); return 3
    if a.dry_run or not a.apply:
        # list every test literal equal to an old boundary so the ruling can be prepared (nothing is written)
        inst = {x["old"][side]: iso(x["new"][side]) for x in maps for side in ("start_iso", "end_iso")}
        for p_, ln, a_, b_ in scan_test_literals(inst, SIDECAR.parents[1]):
            print(f"TEST LITERAL (needs ruling at --apply): {p_}:{ln} {a_} -> {b_}")
    if a.apply:
        rulings = json.loads(Path(a.rulings).read_text(encoding="utf-8")) if a.rulings else None
        review: list[str] = []
        try:
            for f in apply_repin(a.new_build_id, maps, SIDECAR.parents[1], rulings=rulings, review=review):
                print("changed:", f)
        except NeedsRuling as exc:
            for r in exc.unclassified:
                print("NEEDS RULING (nothing written):", r, file=sys.stderr)
            print("STOP — test literals equal to an old boundary need the steward's ruling (--rulings).", file=sys.stderr); return 3
        except VerifierPinMissing as exc:
            print(f"STOP (nothing written) — {exc}", file=sys.stderr); return 3
        print(f"re-pin PREPARED locally on 'SETTLED-1 received' per {a.settled_received}. ST-SL1-HOLD REMAINS IN FORCE for production Gochara work until this re-pin is reviewed and merged and the steward announces the hold lifted.")
        print("BOTH pin constants were rewritten and verified equal to the SETTLED-1 build: services/gochara_rules/permission.py DASHA_READ_CONTRACT['build_id'] AND services/gochara_kernel/inventory_verifier.py _C_BUILD.")
        print("NEXT, in the SAME reviewed re-pin PR: regenerate the implementation lock — `python -m services.gochara_kernel.implementation_registry --write` (a changed governed module moves the implementation digest; the seal refuses an unregistered one).")
        for r in review:
            print("ruled:", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
