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
        [--apply --hold-lifted <steward message id> [--rulings rulings.json]]

ST-SL1-HOLD (steward M20261002T223058-f6e4): from the start of Suvarṇa's S-L1 window until the steward announces 'SETTLED-1 received AND daśā re-pin merged', no Gochara build / verification /
brief / resonance run / measurement extract runs against production chart 482012f1. --apply is REFUSED (exit 2) without --hold-lifted <the announcement's message id>. Test literals equal to
an old boundary are listed and --apply STOPS before writing anything until --rulings classifies each `path:line` as rewrite or keep (the steward's ruling).

READ-ONLY against the database (the connection is set READ ONLY); --apply edits only
files in this repository:
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


# ── pure helpers (unit-tested) ───────────────────────────────────────────────
def _t(s) -> datetime:
    if isinstance(s, datetime):
        return s.astimezone(timezone.utc) if s.tzinfo else s.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso(s) -> str:
    return _t(s).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_rows(rows: list[dict]) -> list[dict]:
    """DB rows -> plain strings: UUIDs as text, instants as whole-second UTC `…Z` (the pinned-literal form)."""
    return [{**r, "dasha_row_id": str(r["dasha_row_id"]),
             "parent_row_id": None if r.get("parent_row_id") is None else str(r["parent_row_id"]),
             "start_iso": iso(r["start_iso"]), "end_iso": iso(r["end_iso"]),
             "level_n": int(r["level_n"])} for r in rows]


def index_paths(rows: list[dict]) -> dict[tuple, dict]:
    """(level, path) -> row, where path = the chain of sibling indices from the MD down
    (siblings ordered by start_iso under their parent). Rows must be one build, §4.0-canonical."""
    by_parent: dict = {}
    for r in rows:
        by_parent.setdefault(r.get("parent_row_id"), []).append(r)
    for sibs in by_parent.values():
        sibs.sort(key=lambda r: _t(r["start_iso"]))
    out: dict[tuple, dict] = {}

    def walk(parent_id, path):
        for i, r in enumerate(by_parent.get(parent_id, [])):
            p = path + (i,)
            out[(int(r["level_n"]), p)] = r
            walk(r["dasha_row_id"], p)
    walk(None, ())
    return out


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


def write_capture(path: str, chart_id: str, build_id: str, rows: list[dict]) -> str:
    """The OLD build's rows, captured READ-ONLY BEFORE S-L1 (the old rows may no longer exist afterwards): {chart_id, build_id, sha256, rows} — the file is the evidence the comparison uses."""
    d = {"chart_id": chart_id, "build_id": build_id, "rows": rows, "sha256": _rows_digest(rows)}
    Path(path).write_text(json.dumps(d, indent=1, sort_keys=True), encoding="utf-8")
    return d["sha256"]


def load_capture(path: str, chart_id: str, build_id: str) -> list[dict]:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if d.get("chart_id") != chart_id or d.get("build_id") != build_id or not d.get("rows") or d.get("sha256") != _rows_digest(d["rows"]):
        raise ValueError("the captured old-rows file is not for this chart and the pinned build, is empty, or its sha256 does not match its rows")
    return d["rows"]


class NeedsRuling(Exception):
    """--apply found test literals nobody has ruled on: nothing was written."""
    def __init__(self, unclassified: list[str]):
        super().__init__(f"{len(unclassified)} test literal(s) need the steward's ruling")
        self.unclassified = unclassified


def load_notice(path: str) -> dict:
    """Suvarṇa's SETTLED-1 notice as JSON: {"settled_1": true, "new_build_id": "<uuid>", "expected_shift_seconds": {"1": 6993, "2": 6993, "3": 6993}, "tolerance_seconds": 2}
    (a level may instead give {"start": n, "end": n}). The tolerance is STATED by the notice — there is no default."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if d.get("settled_1") is not True or not isinstance(d.get("expected_shift_seconds"), dict) or not isinstance(d.get("tolerance_seconds"), (int, float)) or isinstance(d.get("tolerance_seconds"), bool) or d["tolerance_seconds"] < 0:
        raise ValueError("the SETTLED-1 notice must carry settled_1: true, expected_shift_seconds per level and a stated tolerance_seconds >= 0")
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
                if abs(got - want[side]) > tol:
                    out.append(f"level {LEVEL_NAME.get(lv, lv)} {side} {stat} shift {got:.0f} s is outside the notice's {want[side]} s ± {tol} s")
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


def decide(*, new_tier_ok: bool, new_integrity: dict, m: dict, flips: list, ref_problems: list, forensic_report: str | None, shift_issues: list[str] | None = None) -> list[str]:
    stops = list(shift_issues or [])
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
def render(*, old_id, new_id, chart_id, o_int, n_int, m, stats, flips, maps, stops, sensitive=()) -> str:
    L = [f"# AM-10 re-pin evidence — chart {chart_id}", "",
         f"* old pin: `{old_id}`  →  new build: `{new_id}`", f"* verdict: **{'CLEAN' if not stops else 'STOP'}**", ""]
    if stops:
        L += ["## Stops", *[f"* {s}" for s in stops], ""]
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
            assert _WHOLE_SECOND_Z.fullmatch(n[side]), f"new instant {n[side]!r} is not whole-second …Z (permission.py compares these lexicographically)"
            instants[o[side]] = n[side]
    matches = scan_test_literals(instants, repo_root)
    ruled = {**{k: "rewrite" for k in (rulings or {}).get("rewrite", [])}, **{k: "keep" for k in (rulings or {}).get("keep", [])}}
    unclassified = [f"{p}:{ln} {a_} -> {b_}" for p, ln, a_, b_ in matches if f"{p}:{ln}" not in ruled]
    if review is not None:
        review.extend(f"{p}:{ln} {a_} -> {b_} [{ruled.get(f'{p}:{ln}', 'UNRULED')}]" for p, ln, a_, b_ in matches)
    if unclassified:
        raise NeedsRuling(unclassified)                                              # nothing has been written
    s = rewrite_once(s, {**ids, **instants, f'"build_id": "{old_id}"': f'"build_id": "{new_id}"'})
    assert s.count(f'"build_id": "{new_id}"') == 1 and f'"build_id": "{old_id}"' not in s, "the re-pin constant must equal the SETTLED-1 build and the old pin must be gone (G6 b)"
    perm.write_text(s, encoding="utf-8")
    changed.append(str(perm.relative_to(repo_root)))
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


def test_pin_is_the_new_build_and_the_old_one_is_refused():
    assert DASHA_READ_CONTRACT["build_id"] == NEW
    assert select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"], rows(NEW))["build_id"] == NEW
    with pytest.raises(DashaReadConflict):
        select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"], rows(OLD))
'''


# ── CLI ──────────────────────────────────────────────────────────────────────
def _capture_old(a, conn) -> int:
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    if conn is None:
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"]); conn.set_session(readonly=True)
    rows = norm_rows(DD.fetch_dasha_periods_multilevel(conn, a.chart_id, systems=["vimshottari"], build_id=old_id, levels=(1, 2, 3, 4)))
    if not rows:
        print(f"STOP — the pinned build {old_id} has no rows to capture", file=sys.stderr); return 3
    print(f"captured {len(rows)} rows of {old_id} -> {a.capture_old} sha256 {write_capture(a.capture_old, a.chart_id, old_id, rows)}")
    return 0


def main(argv=None, *, conn=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--new-build-id", required=True)
    ap.add_argument("--chart-id", default=PERM.DASHA_READ_CONTRACT["chart_id"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--forensic-report", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the full report and the test-literal matches; write NOTHING (no --out, no --apply)")
    ap.add_argument("--settled-notice", default=None, help="JSON of Suvarṇa's SETTLED-1 notice: expected per-level shift + a stated tolerance (see load_notice)")
    ap.add_argument("--hold-lifted", default=None, help="the steward's message id announcing 'SETTLED-1 received AND daśā re-pin merged' — ST-SL1-HOLD; REQUIRED for --apply")
    ap.add_argument("--capture-old", default=None, help="READ-ONLY: write the OLD (pinned) build's rows to this file BEFORE S-L1 and exit — the old rows may not exist afterwards")
    ap.add_argument("--old-rows", default=None, help="the file written by --capture-old: the old build's rows when the DB no longer holds them")
    ap.add_argument("--rulings", default=None, help="JSON {rewrite: [path:line…], keep: [path:line…]} — the steward's ruling on test literals that equal an old boundary")
    a = ap.parse_args(argv)
    if a.capture_old:
        return _capture_old(a, conn)
    if a.dry_run and a.apply:
        print("--dry-run and --apply are mutually exclusive", file=sys.stderr); return 2
    if a.apply and not a.hold_lifted:
        print("--apply refused: ST-SL1-HOLD — pass --hold-lifted <steward message id> once the steward has announced 'SETTLED-1 received AND daśā re-pin merged'", file=sys.stderr); return 2
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    if a.new_build_id == old_id:
        print("new build equals the current pin — nothing to re-pin", file=sys.stderr); return 2
    if conn is None:
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"]); conn.set_session(readonly=True)
    if a.old_rows:
        try:
            old_rows = load_capture(a.old_rows, a.chart_id, old_id)
        except (OSError, ValueError) as exc:
            print(f"STOP — {exc}", file=sys.stderr); return 3
    else:
        old_rows = norm_rows(DD.fetch_dasha_periods_multilevel(conn, a.chart_id, systems=["vimshottari"], build_id=old_id, levels=(1, 2, 3, 4)))
    new_rows = norm_rows(DD.fetch_dasha_periods_multilevel(conn, a.chart_id, systems=["vimshottari"], build_id=a.new_build_id, levels=(1, 2, 3, 4)))
    # tier is pinned IN the query (two_pass_verified): an empty result means the new build is absent or at another tier
    new_tier_ok = bool(new_rows) and all(r.get("verification_pass_status") == PERM.DASHA_READ_CONTRACT["tier"] for r in new_rows)
    old_idx, new_idx = index_paths(old_rows), index_paths(new_rows)
    m = match(old_idx, new_idx)
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
    if not old_rows:
        extra_stops.append("the OLD build's rows are absent from the database and no --old-rows capture was supplied (capture them BEFORE S-L1 with --capture-old)")
    stops = decide(new_tier_ok=new_tier_ok, new_integrity=integrity(new_rows), m=m, flips=flips,
                   ref_problems=ref_problems, forensic_report=a.forensic_report, shift_issues=shift_problems(stats, notice))
    stops += extra_stops
    if notice is not None and notice.get("new_build_id") not in (None, a.new_build_id):
        stops.append(f"the SETTLED-1 notice names build {notice.get('new_build_id')}, not {a.new_build_id}")
    report = render(old_id=old_id, new_id=a.new_build_id, chart_id=a.chart_id, o_int=integrity(old_rows),
                    n_int=integrity(new_rows), m=m, stats=stats, flips=flips, sensitive=sensitive, maps=maps, stops=stops)
    if a.out and not a.dry_run:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    if stops:
        print("STOP — not re-pinning.", file=sys.stderr); return 3
    if a.dry_run or not a.apply:
        # list every test literal equal to an old boundary so the ruling can be prepared (nothing is written)
        inst = {x["old"][side]: x["new"][side] for x in maps for side in ("start_iso", "end_iso")}
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
        print(f"ST-SL1-HOLD lifted per {a.hold_lifted}")
        for r in review:
            print("ruled:", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
