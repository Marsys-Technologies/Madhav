#!/usr/bin/env python3
"""AM-10 re-pin tool — the §4.0 daśā read contract, one command when the L1 rebuild lands.

Draft AM-10 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-10) rules: ONE pin, no auto-follow; a
re-pin is by EVIDENCE only, in one small PR; any class flip / lord flip / anchor failure is
a STOP, not a re-pin. This tool produces the evidence and, only with --apply and only when
nothing stops it, performs the single change.

    python3 scripts/gochara/repin_dasha_contract.py --new-build-id <uuid> \\
        [--chart-id 482012f1-…] [--out evidence.md] [--forensic-report path] [--apply]

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

Exit codes: 0 evidence clean (and applied if asked) · 3 STOP (a stop reason is listed) · 2 usage.
Evidence item (e) — the seven FORENSIC anchors — is supplied by the L1 owner as --forensic-report
(this tool does not recompute foundational chart facts; CLAUDE.md §B); without it the verdict is
'incomplete' and --apply is refused.
"""
from __future__ import annotations

import argparse
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


def decide(*, new_tier_ok: bool, new_integrity: dict, m: dict, flips: list, ref_problems: list, forensic_report: str | None) -> list[str]:
    stops = []
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


def apply_repin(new_id: str, maps: list[dict], repo_root: Path, review: list[str] | None = None) -> list[str]:
    """Rewrites (a) permission.py: the pin, the reference rows' ids and instants — one pass; (b) tests/l3: ONLY the unambiguous literals (the reference rows' ids and the pin's build id).
    An OLD BOUNDARY INSTANT found in a test is NOT rewritten (it may be an event date that merely equals a boundary — D8): it is appended to `review` as `path:line literal -> new`."""
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
    s = rewrite_once(s, {**ids, **instants, f'"build_id": "{old_id}"': f'"build_id": "{new_id}"'})
    perm.write_text(s, encoding="utf-8")
    changed.append(str(perm.relative_to(repo_root)))
    for p in sorted((SIDECAR / "tests" / "l3").rglob("*.py")):
        txt = p.read_text(encoding="utf-8")
        new_txt = rewrite_once(txt, {**ids, old_id: new_id})
        if review is not None:
            for ln, line in enumerate(txt.splitlines(), 1):
                for a_, b_ in instants.items():
                    if a_ in line:
                        review.append(f"{p.relative_to(repo_root)}:{ln} {a_} -> {b_}")
        if new_txt != txt:
            p.write_text(new_txt, encoding="utf-8"); changed.append(str(p.relative_to(repo_root)))
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
def main(argv=None, *, conn=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--new-build-id", required=True)
    ap.add_argument("--chart-id", default=PERM.DASHA_READ_CONTRACT["chart_id"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--forensic-report", default=None)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    old_id = PERM.DASHA_READ_CONTRACT["build_id"]
    if a.new_build_id == old_id:
        print("new build equals the current pin — nothing to re-pin", file=sys.stderr); return 2
    if conn is None:
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"]); conn.set_session(readonly=True)
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
    stops = decide(new_tier_ok=new_tier_ok, new_integrity=integrity(new_rows), m=m, flips=flips,
                   ref_problems=ref_problems, forensic_report=a.forensic_report)
    report = render(old_id=old_id, new_id=a.new_build_id, chart_id=a.chart_id, o_int=integrity(old_rows),
                    n_int=integrity(new_rows), m=m, stats=stats, flips=flips, sensitive=sensitive, maps=maps, stops=stops)
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    if stops:
        print("STOP — not re-pinning.", file=sys.stderr); return 3
    if a.apply:
        review: list[str] = []
        for f in apply_repin(a.new_build_id, maps, SIDECAR.parents[1], review=review):
            print("changed:", f)
        for r in review:
            print("REVIEW (NOT rewritten — a human decides whether this literal is a daśā boundary or an event date):", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
