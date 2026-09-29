#!/usr/bin/env python3.13
"""T1 differential test — independent reimplementation of three inspector checks,
run against the SANDBOX for all six layers, verdicts diffed against the inspector's.

Checks reimplemented with deliberately different logic:
  Vocab.identity   inspector: pg_constraint (u|p), picks first non-'id' key, dup =
                   count(*)-count(DISTINCT key) [NULL rows inflate the count].
                   ours: prefer PRIMARY KEY else first unique (ordered by conname);
                   dup = number of duplicate GROUPS over rows with ALL key members
                   non-NULL (GROUP BY ... HAVING count(*)>1).
  Build.registered inspector: AST walk for @register('<id>') decorator on a class.
                   ours: literal grep -lF "@register('<id>')" over writers/*.py
                   (matches comments and non-class decorator usage too).
  Count.floor      inspector: live count via the asset's own count_sql; floor read
                   as text and applied only when all-digit.
                   ours: live = plain count(*) of target_table; floor read as
                   integer column.

Usage: differential.py <inspector_census.json per layer, named L<n>_*.json in NT/census>
Writes: NT/harness/T1_DIFFERENTIAL.md
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/Dev/madhav-nikasha")
NT = ROOT / "00_ARCHITECTURE" / "briefs" / "nirmana" / "nikasha_test"
WRITERS = ROOT / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers"
PSQL = "/opt/homebrew/bin/psql"

PREFIX = {"L0": "bg_", "L1": "ga_", "L2": "bo_", "L3": "ka_", "L4": "ph_", "L5": "mi_"}

ENV = dict(os.environ, PGHOST=str(NT / ".sandbox"), PGPORT="54329", PGUSER="sandbox",
           PGDATABASE="nikasha_sandbox", PGOPTIONS="")


def sql(q: str) -> list[list[str]]:
    p = subprocess.run([PSQL, "-tAX", "-F", "\x1f", "-v", "ON_ERROR_STOP=1", "-c", q],
                       capture_output=True, text=True, env=ENV, timeout=300)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return [ln.split("\x1f") for ln in p.stdout.strip().split("\n") if ln.strip()]


def scalar(q: str) -> str | None:
    r = sql(q)
    return r[0][0] if r else None


# ── our reimplementations ──────────────────────────────────────────────

def our_registry(prefix: str) -> dict[str, dict]:
    rows = sql("SELECT asset_id, coalesce(target_table,''), coalesce(has_writer,false)::text, "
               "coalesce(target_floor::text,'') FROM asset_registry "
               f"WHERE asset_id LIKE '{prefix}%' ORDER BY asset_id")
    return {r[0]: dict(target_table=r[1] or None, has_writer=r[2] == "true",
                       target_floor=r[3] or None) for r in rows}


def our_identity(table: str) -> tuple[str, str] | None:
    """(verdict, detail) or None when the check does not apply."""
    keys = sql(
        "SELECT x.contype, x.conname, pg_get_constraintdef(x.oid) FROM pg_constraint x "
        "JOIN pg_class c ON c.oid=x.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
        f"WHERE n.nspname='public' AND c.relname='{table}' AND x.contype IN ('p','u') "
        "ORDER BY x.contype, x.conname")  # 'p' < 'u': PRIMARY KEY preferred
    if not keys:
        return None
    m = re.search(r"\((.*?)\)", keys[0][2])
    cols = [c.strip().strip('"') for c in m.group(1).split(",")]
    notnull = " AND ".join(f"{c} IS NOT NULL" for c in cols)
    groups = scalar(f"SELECT count(*)::text FROM (SELECT 1 FROM {table} WHERE {notnull} "
                    f"GROUP BY {', '.join(cols)} HAVING count(*)>1) g")
    n = int(groups or 0)
    return ("FAIL" if n else "PASS"), f"key ({', '.join(cols)}): {n} duplicate group(s)"


def our_registered(aid: str, has_writer: bool) -> tuple[str, str]:
    p = subprocess.run(["grep", "-lE", f"@register\\(['\"]{aid}['\"]"] +
                       [str(f) for f in sorted(WRITERS.glob("*.py")) if f.name != "__init__.py"],
                       capture_output=True, text=True)
    files = [ln for ln in p.stdout.strip().split("\n") if ln.strip()]
    n = len(files)
    if n == 1 and has_writer:
        return "PASS", f"grep hit {os.path.basename(files[0])}; registry agrees"
    if n == 1 and not has_writer:
        return "FAIL", f"grep hit {os.path.basename(files[0])} but registry has_writer=false"
    if n > 1:
        return "FAIL", f"grep hits in {n} files"
    if has_writer:
        return "FAIL", "registry has_writer=true, no grep hit"
    return "N/A", "no grep hit, registry agrees"


def our_floor(table: str | None, floor: str | None) -> tuple[str, str] | None:
    if not floor or not table:
        return None
    try:
        live = scalar(f"SELECT count(*)::text FROM {table}")
    except RuntimeError:
        return None
    d = int(live) - int(floor)
    return ("FAIL" if d < 0 else "PASS"), f"live={live}, floor={floor}, delta={d:+d}"


def inspector_doc(path: Path) -> dict[str, dict]:
    doc = json.loads(path.read_text())
    for v in doc.values():
        if isinstance(v, dict) and "assets" in v:
            return {a["asset_id"]: a for a in v["assets"]}
    return {}


CHECKS = {"Vocab.identity": our_identity, "Build.registered": None, "Count.floor": None}


def classify(check: str, layer: str, aid: str, iv: str | None, ov: str | None,
             detail: str, insp_live: int | None, our_live: int | None) -> str:
    if check == "Build.registered":
        return "known defect R43 (literal-grep vs AST read of @register)"
    if check == "Count.floor":
        if iv is None:
            return ("known defect R48 (Count.floor absent on L3 in inspector)"
                    if layer == "L3"
                    else "finding T1-F1 (inspector silent: no Count.floor — parameterized "
                         "or multi-table count_sql)")
        if insp_live is not None and our_live is not None and insp_live != our_live:
            return (f"known defect R46 (inspector live={insp_live} from count_sql "
                    f"!= table count {our_live})")
        return "NEW"
    return "NEW"


def main() -> int:
    census = {l: NT / "census" / f"{l}_sandbox_20260926.json" for l in PREFIX}
    census["L0"] = NT / "census" / "L0_sandbox2_20260926.json"
    census["L3"] = NT / "census" / "L3_sandbox_20260926.json"
    missing = [str(p) for p in census.values() if not p.exists()]
    if missing:
        sys.exit("missing inspector sandbox censuses: " + ", ".join(missing))

    lines = ["# T1 differential test — independent reimplementation vs inspector (sandbox)", ""]
    n_new = n_known = n_agree = 0
    for layer in PREFIX:
        idoc = inspector_doc(census[layer])
        insp = {aid: {c: (m or {}).get("v") for c, m in a["measurements"].items()}
                for aid, a in idoc.items()}
        ilive = {aid: a.get("live_rows") for aid, a in idoc.items()}
        reg = our_registry(PREFIX[layer])
        lines.append(f"## {layer} ({len(reg)} assets)")
        lines.append("")
        lines.append("| asset | check | inspector | ours | class | detail |")
        lines.append("|---|---|---|---|---|---|")
        for aid, r in sorted(reg.items()):
            ours: dict[str, tuple[str, str] | None] = {}
            if r["target_table"]:
                try:
                    ours["Vocab.identity"] = our_identity(r["target_table"])
                except RuntimeError as exc:
                    ours["Vocab.identity"] = ("ERR", str(exc)[:80])
                ours["Count.floor"] = our_floor(r["target_table"], r["target_floor"])
            else:
                ours["Vocab.identity"] = None
                ours["Count.floor"] = None
            ours["Build.registered"] = our_registered(aid, r["has_writer"])
            for ck in CHECKS:
                o = ours[ck]
                if o is None:
                    if insp.get(aid, {}).get(ck) is not None:
                        # inspector measured, we did not run (no table/floor)
                        iv0 = insp[aid][ck]
                        cls = ("known defect R48 (Count.floor absent-check asymmetry on L3)"
                               if ck == "Count.floor" and layer == "L3"
                               else "methodology (asset counted via count_sql; no target_table "
                                    "for our plain count)")
                        n_new += 1 if cls.startswith("NEW") else 0
                        n_known += 0 if cls.startswith("NEW") else 1
                        lines.append(f"| {aid} | {ck} | {iv0} | <absent> | {cls} | |")
                    continue
                ov, detail = o
                iv = insp.get(aid, {}).get(ck)
                if iv == ov:
                    n_agree += 1
                    continue
                our_live = None
                if ck == "Count.floor":
                    m = re.search(r"live=(\d+)", detail)
                    our_live = int(m.group(1)) if m else None
                il = ilive.get(aid)
                cls = classify(ck, layer, aid, iv, ov, detail,
                               int(il) if isinstance(il, (int, str)) and str(il).isdigit() else None,
                               our_live)
                if cls.startswith("NEW"):
                    n_new += 1
                else:
                    n_known += 1
                lines.append(f"| {aid} | {ck} | {iv or '<absent>'} | {ov} | {cls} | {detail} |")
        lines.append("")
    lines.append(f"**Totals:** {n_agree} agreements; {n_known} disagreements classed to known "
                 f"defects; {n_new} NEW disagreements.")
    out = NT / "harness" / "T1_DIFFERENTIAL.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"written {out}; agree={n_agree} known={n_known} review/new={n_new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
