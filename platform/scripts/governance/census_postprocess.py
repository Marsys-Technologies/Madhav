#!/usr/bin/env python3
"""census_postprocess.py -- the smallest census post-processor (owner decision N-152: one line per asset, no ledger).

Reads the stamped census files of ONE layer set at ONE registry revision and writes two outputs (each as .md + .json, deterministic,
the only date is the --date argument, no clock is read):
  CERTIFIED_LIST  one line per CERTIFIED asset: asset, revision, census file ref (name + sha256 prefix), measured-PASS count,
                  ruled-N/A count, date, known findings text (from the optional --findings JSON, asset -> text).
  FIX_LIST        every other asset: each non-PASS, non-ruled-N/A criterion with verdict and census cause text, grouped by asset then
                  by cause class (CAUSE_CLASSES below; unknown text is a visible 'unclassified', never dropped).
CERTIFIED = every rollup criterion is PASS, or an N/A that carries a rule_id AND a decision (a ruled N/A) (N-154: Build.history too).
Never certified with a FAIL / PARTIAL / NO_DETECTOR / INCONCLUSIVE / unstamped / undecided cell. Build.history is read as the census
states it (not re-implemented here); tool_commit / tool_dirty are recorded in the header, never refused on.  REFUSES (exit 2, one message) on: unstamped input, a synthetic/scratch/scoped census, mixed
revisions / fingerprints / databases, a missing, extra or duplicate layer, a head/rollup stamp mismatch, duplicate assets, an asset in
the rollup but not in the layer list (or vice versa), a non-uniform criterion set, or an asset count differing from --assets-expected.
Read-only: no database, no network.  Usage: census_postprocess.py --census F [F ...] --date YYYY-MM-DD --out-dir D
[--layers L0,L1,L2] [--assets-expected 82] [--criteria-expected 25] [--findings findings.json]"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

PASS, NA = "PASS", "N/A"
SCRATCH_LABEL = re.compile(r"synthetic|scratch|fixture|sandbox", re.I)
SCRATCH_DB = re.compile(r"^(nt_|scratch|synthetic|fixture|sandbox|disposable)", re.I)
UNCLASSIFIED = "(?) unclassified"
# Build.completion PASS that rests on count equality alone: the cell's measured text carries no integrity statement (asset_census `_completion_integrity` appends
# "the declared integrity_check_sql holds (...)" to a PASS only when the asset declares an integrity_check_sql and it ran and held). REPORTING ONLY: no verdict moves.
BUILD_COMPLETION = "Build.completion"
INTEGRITY_HOLDS = "integrity_check_sql holds"
COUNTS_ONLY_LIMITATION = "Build.completion: counts only (no integrity statement)"
# Carr ceilings: a ruled N/A under one of these rule ids certifies the asset AT A CEILING; the limitation is shown on its line (SS N-156)
CEILING_RULES = {"Carr.D3#measured:single-derivation": "Carr: single-derivation",
                 "Carr.D1#measured:transcription-not-verified": "D1: unverified transcription",
                 # N-177 (SS 2026-10-07): the closed-list residual UNSOURCED_DECLARED of Ldgr.source_presence: a CHECKED, declared "no traceable source" reading is a ruled N/A that certifies the asset AT a ceiling, exactly as the Carr ceilings
                 "Ldgr.source_presence#measured:unsourced-declared": "Ldgr: unsourced (declared)"}

# Ordered cause-class table: first row whose predicate holds wins.  (class, test on (criterion, verdict, state, text))
CAUSE_CLASSES = (
    ("(b) declaration missing: prose_fields", lambda c, v, s, t: "prose_fields" in t and "undeclared" in t),
    ("(c) ruling or declaration", lambda c, v, s, t: "N/A rule undecided" in t or "applicability undecidable" in t
        or v == NA),    # only unruled N/A cells are classified (a ruled one never reaches here): it needs a ruling
    ("(d) needs a rebuild", lambda c, v, s, t: "unclassified NULL" in t or "no recorded duration" in t),
    ("(a) detector/declaration (carriage)", lambda c, v, s, t: c.startswith("Carr.") and "not measured (applies)" in t),
    ("(a) detector", lambda c, v, s, t: v == "PARTIAL" and (   # by-design PARTIAL ("never PASS" / "structural only"): a missing PASS path, not a defect
        "never PASS" in t or "never reads PASS" in t or "structural only" in t)),
    ("(e) defect in data or code", lambda c, v, s, t: v in ("FAIL", "PARTIAL") and s == "MEASURED"),
    ("(a) detector", lambda c, v, s, t: v in ("NO_DETECTOR", "FAIL", "PARTIAL")),   # the catch-all for a known non-passing verdict
)
CLASS_ORDER = [c for c, _ in CAUSE_CLASSES if c != "(a) detector"][:5] + ["(a) detector", UNCLASSIFIED]


class Refused(Exception):
    pass


def classify(criterion: str, verdict: str, state: str, text: str) -> str:
    for name, test in CAUSE_CLASSES:
        if test(criterion, verdict, state, text or ""):
            return name
    return UNCLASSIFIED      # e.g. INCONCLUSIVE or an unknown verdict: visible, never dropped


def is_counts_only_completion(cells: dict) -> bool:
    """True when the asset's Build.completion cell is a PASS whose measured text states no integrity result (count equality alone)."""
    ck = cells.get(BUILD_COMPLETION)
    return bool(ck) and ck.get("v") == PASS and INTEGRITY_HOLDS not in str(ck.get("cause") or "")


def is_ruled_na(ck: dict) -> bool:
    return ck.get("v") == NA and bool(ck.get("rule_id")) and bool(ck.get("decision"))


def load(path: pathlib.Path) -> dict:
    """Validate one census file; returns dict(layer, head, assets{aid: {criterion: cell+cause}}, ref)."""
    raw = pathlib.Path(path).read_bytes()
    try:
        d = json.loads(raw)
    except ValueError:
        raise Refused(f"{path.name}: not valid JSON")
    found = [k for k in d if re.fullmatch(r"L\d", k)] if isinstance(d, dict) else []
    if len(found) != 1 or not isinstance(d.get("rollup"), dict):
        raise Refused(f"{path.name}: expected exactly one layer key and a rollup (found layers {found})")
    layer, head, roll = found[0], d[found[0]], d["rollup"]
    if d.get("synthetic") or d.get("scratch") or head.get("synthetic") or head.get("scratch") \
            or SCRATCH_LABEL.search(str(d.get("label", "")) + str(head.get("label", "")) + str(head.get("census_label", ""))) \
            or "scope" in head or "scope" in roll:
        raise Refused(f"{path.name}: synthetic, scratch or scoped census (label); a certified list is read from full production censuses")
    ident = head.get("db_identity")
    if not (isinstance(ident, dict) and ident.get("schema") and ident.get("database") and ident.get("system_id_sha256")):
        raise Refused(f"{path.name}: unstamped (no usable db_identity stamp)")
    if SCRATCH_DB.search(ident["database"]):
        raise Refused(f"{path.name}: db_identity names a scratch database ({ident['database']})")
    rev, fp = head.get("registry_revision"), head.get("registry_fingerprint")
    if rev is None or not fp:
        raise Refused(f"{path.name}: unstamped (no registry_revision / registry_fingerprint in the layer head)")
    if (roll.get("registry_revision"), roll.get("registry_fingerprint")) != (rev, fp):
        raise Refused(f"{path.name}: the layer stamp (revision {rev}, fingerprint {str(fp)[:12]}) does not match the file's own rollup")
    rl = (roll.get("layers") or {}).get(layer)
    if set(roll.get("layers") or {}) != {layer} or not isinstance(rl, dict):
        raise Refused(f"{path.name}: the rollup does not cover exactly layer {layer}")
    listed = [a.get("asset_id") for a in head.get("assets") or []]
    if len(set(listed)) != len(listed):
        raise Refused(f"{path.name}: duplicate asset in the layer list")
    if set(listed) != set(rl):
        diff = sorted(set(listed) ^ set(rl))
        raise Refused(f"{path.name}: asset(s) {diff[:5]} are in only one of the layer list and the rollup")
    meas = {a["asset_id"]: a.get("measurements") or {} for a in head["assets"]}
    assets = {}
    for aid, gates in rl.items():
        cells = {}
        for g in gates.values():
            if (g.get("registry_revision"), g.get("registry_fingerprint")) != (rev, fp):
                raise Refused(f"{path.name}: {aid} gate {g.get('gate')} is unstamped or stamped with another revision/fingerprint")
            for ck in g.get("checks") or []:
                name = ck["criterion"]
                if name in cells:
                    raise Refused(f"{path.name}: {aid} has {name} twice")
                m = (meas[aid].get(name) or {}).get("measured") if ck.get("state") == "MEASURED" else None
                cells[name] = dict(ck, cause=m if isinstance(m, str) and m else (ck.get("reason") or ""))
        assets[aid] = cells
    return dict(layer=layer, rev=rev, fp=fp, tool=(head.get("tool_commit"), head.get("tool_dirty")), db=(ident["database"], ident["system_id_sha256"]), assets=assets,
                ref=f"{path.name}#{hashlib.sha256(raw).hexdigest()[:12]}")


def build(files: list[pathlib.Path], layers: list[str], expected: int | None, criteria_expected: int | None,
          date: str, findings: dict) -> dict:
    loaded = [load(pathlib.Path(f)) for f in files]
    seen = [x["layer"] for x in loaded]
    for l in sorted(set(seen)):
        if seen.count(l) > 1:
            raise Refused(f"layer {l} given in more than one file")
    if set(seen) - set(layers):
        raise Refused(f"layer(s) {sorted(set(seen) - set(layers))} are outside the required layer set {layers}")
    if set(layers) - set(seen):
        raise Refused(f"missing required layer(s) {sorted(set(layers) - set(seen))}")
    if len({(x["rev"], x["fp"]) for x in loaded}) != 1:
        raise Refused("files are at different registry revisions or fingerprints: "
                      + ", ".join(f"{x['layer']}=r{x['rev']}/{x['fp'][:8]}" for x in loaded))
    if len({x["db"] for x in loaded}) != 1:
        raise Refused("files carry different db_identity stamps (not one database)")
    all_assets, ref = {}, {}
    for x in loaded:
        for aid, cells in x["assets"].items():
            if aid in all_assets:
                raise Refused(f"asset {aid} appears in more than one file")
            all_assets[aid], ref[aid] = cells, (x["layer"], x["ref"])
    if expected is not None and len(all_assets) != expected:
        raise Refused(f"expected {expected} assets, the files carry {len(all_assets)}")
    sets = {frozenset(c) for c in all_assets.values()}
    if len(sets) != 1 or (criteria_expected is not None and len(next(iter(sets))) != criteria_expected):
        raise Refused(f"the criterion set is not uniform across assets (or not {criteria_expected}): {sorted(len(s) for s in sets)}")
    rev = loaded[0]["rev"]
    certified, fixes, counts_only = [], {}, []
    for aid in sorted(all_assets):
        cells = all_assets[aid]
        limits = [COUNTS_ONLY_LIMITATION] if is_counts_only_completion(cells) else []
        bad = []
        for name in sorted(cells):
            ck = cells[name]
            if ck["v"] == PASS or is_ruled_na(ck):
                continue
            bad.append(dict(layer=ref[aid][0], criterion=name, verdict=ck["v"], cause=ck["cause"],
                            cause_class=classify(name, ck["v"], ck.get("state") or "", ck["cause"])))
        if limits:
            counts_only.append(dict(asset=aid, layer=ref[aid][0], certified=not bad))
        if bad:
            fixes[aid] = bad
        else:
            certified.append(dict(asset=aid, layer=ref[aid][0], revision=rev, census=ref[aid][1],
                                  measured_pass=sum(c["v"] == PASS for c in cells.values()),
                                  ruled_na=sum(is_ruled_na(c) for c in cells.values()), date=date,
                                  ceilings=sorted({CEILING_RULES[c["rule_id"]] for c in cells.values() if is_ruled_na(c) and c.get("rule_id") in CEILING_RULES}),
                                  limitations=limits, findings=str(findings.get(aid, ""))))
    d2 = [c.get("Carr.D2") for c in all_assets.values()]
    other = {}
    for c in d2:
        if not (c and is_ruled_na(c) and c.get("rule_id") == D2_NO_PER_WITNESS):
            k = (c or {}).get("v", "missing") if not (c and is_ruled_na(c)) else "ruled N/A under another rule"
            other[k] = other.get(k, 0) + 1
    carr_d2 = dict(assets=len(d2), na_no_per_witness=len(d2) - sum(other.values()), other=dict(sorted(other.items())))
    return dict(carr_d2=carr_d2, build_completion_counts_only=dict(limitation=COUNTS_ONLY_LIMITATION, assets_of=len(all_assets), count=len(counts_only), assets=counts_only),
                registry_revision=rev, registry_fingerprint=loaded[0]["fp"], db_identity=dict(zip(("database", "system_id_sha256"), loaded[0]["db"])),
                layers=sorted(layers), date=date,
                tool=[dict(tool_commit=c, tool_dirty=dirty) for c, dirty in sorted({x["tool"] for x in loaded}, key=str)], assets=len(all_assets), certified=certified, fix_list=fixes)


def _cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\t", " ")


def tool_str(r: dict) -> str:
    return ",".join(f"{str(t['tool_commit'])[:9]}{'(dirty)' if t['tool_dirty'] else ''}" for t in r["tool"])


D2_NO_PER_WITNESS = "Carr.D2#measured:no-per-witness-values"
D3_CEILING, D1_CEILING = CEILING_RULES["Carr.D3#measured:single-derivation"], CEILING_RULES["Carr.D1#measured:transcription-not-verified"]
LDGR_CEILING = CEILING_RULES["Ldgr.source_presence#measured:unsourced-declared"]


def ceiling_counts(r: dict) -> tuple:
    """(certified at the D3 ceiling only, at the D1 ceiling only, at both): the two CARR ceilings, as before (`Carr.D2` is NOT a ceiling and never counted here; `Carr.D1#measured:not-a-transcription` is a plain
    N/A). An asset that is also at the Ldgr ceiling still counts here by its Carr ceilings; `ldgr_ceiling_count` counts the Ldgr one."""
    a = sum(1 for c in r["certified"] if D3_CEILING in c["ceilings"] and D1_CEILING not in c["ceilings"])
    b = sum(1 for c in r["certified"] if D1_CEILING in c["ceilings"] and D3_CEILING not in c["ceilings"])
    both = sum(1 for c in r["certified"] if D3_CEILING in c["ceilings"] and D1_CEILING in c["ceilings"])
    return a, b, both


def ldgr_ceiling_count(r: dict) -> int:
    """Certified assets at the Ldgr ceiling (UNSOURCED_DECLARED, N-177)."""
    return sum(1 for c in r["certified"] if LDGR_CEILING in c["ceilings"])


def ceiling_summary(r: dict) -> str:
    a, b, both = ceiling_counts(r)
    n = sum(1 for c in r["certified"] if c["ceilings"])
    return (f"ceilings: {n} of {len(r['certified'])} certified assets are at a declared ceiling ({D3_CEILING} {a}; {D1_CEILING} {b}; both {both}; {LDGR_CEILING} {ldgr_ceiling_count(r)})")


def d2_line(r: dict) -> str:
    d = r["carr_d2"]
    if d["na_no_per_witness"] == d["assets"]:
        return "Carr.D2: N/A on every asset (no per-witness values stored, N-156)"
    return (f"Carr.D2: ruled N/A (no per-witness values stored, N-156) on {d['na_no_per_witness']} of {d['assets']} assets; "
            + ", ".join(f"{k} {v}" for k, v in sorted(d["other"].items())) + " on the rest")


def counts_only_summary(r: dict) -> str:
    c = r["build_completion_counts_only"]
    return f"Build.completion counts only (no integrity statement): {c['count']} of {c['assets_of']} assets"


def counts_only_footer(r: dict) -> list:
    """The output footer: the assets whose Build.completion PASS rests on count equality alone, each with where it sits (certified or on the fix list). Reporting only."""
    c = r["build_completion_counts_only"]
    out = ["", f"Known limitation, {c['limitation']}: {c['count']} of {c['assets_of']} assets have a Build.completion PASS that rests on count equality alone (its measured text states no "
            f"'{INTEGRITY_HOLDS}'). This is reporting only: no verdict changed."]
    out += [f"- {x['asset']} ({x['layer']}; {'CERTIFIED' if x['certified'] else 'on the FIX_LIST'})" for x in c["assets"]] or ["- (none)"]
    return out


def render_certified(r: dict) -> str:
    out = [f"# CERTIFIED_LIST", f"registry revision {r['registry_revision']} (fingerprint {r['registry_fingerprint'][:12]}); layers {','.join(r['layers'])}; "
           f"date {r['date']}; tool {tool_str(r)}; {len(r['certified'])} of {r['assets']} assets certified", ceiling_summary(r), d2_line(r), counts_only_summary(r), "",
           "| asset | revision | census file | measured PASS | ruled N/A | date | ceilings | known limitations | known findings |", "|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {_cell(c['asset'])} | {c['revision']} | {_cell(c['census'])} | {c['measured_pass']} | {c['ruled_na']} | {c['date']} | {_cell('; '.join(c['ceilings']))} | {_cell('; '.join(c['limitations']))} | {_cell(c['findings'])} |"
            for c in r["certified"]]
    return "\n".join(out + counts_only_footer(r)) + "\n"


def totals(r: dict) -> dict:
    """layer -> cause class -> number of fix-list items"""
    t: dict = {}
    for items in r["fix_list"].values():
        for it in items:
            t.setdefault(it["layer"], {}).setdefault(it["cause_class"], 0)
            t[it["layer"]][it["cause_class"]] += 1
    return {l: dict(sorted(c.items())) for l, c in sorted(t.items())}


def render_fix(r: dict) -> str:
    out = ["# FIX_LIST", f"registry revision {r['registry_revision']}; date {r['date']}; tool {tool_str(r)}; {len(r['fix_list'])} of {r['assets']} assets not certified", counts_only_summary(r), ""]
    limited = {x["asset"] for x in r["build_completion_counts_only"]["assets"]}
    for aid, items in r["fix_list"].items():
        out.append(f"## {aid} ({len(items)} open)")
        if aid in limited:
            out.append(f"- known limitation: {COUNTS_ONLY_LIMITATION}")
        for cls in CLASS_ORDER:
            sel = [i for i in items if i["cause_class"] == cls]
            if sel:
                out.append(f"- {cls}")
                out += [f"  - {i['criterion']} {i['verdict']}: {_cell(i['cause'])}" for i in sel]
        out.append("")
    return "\n".join(out + counts_only_footer(r)) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--census", nargs="+", required=True, type=pathlib.Path)
    ap.add_argument("--layers", default="L0,L1,L2")
    ap.add_argument("--assets-expected", type=int)
    ap.add_argument("--criteria-expected", type=int)
    ap.add_argument("--date", required=True)
    ap.add_argument("--findings", type=pathlib.Path)
    ap.add_argument("--out-dir", required=True, type=pathlib.Path)
    a = ap.parse_args(argv)
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
            raise Refused("--date must be YYYY-MM-DD (it is an argument; no clock is read)")
        findings = json.loads(a.findings.read_bytes()) if a.findings else {}
        if not isinstance(findings, dict):
            raise Refused("--findings must be a JSON object asset -> text")
        res = build(a.census, a.layers.split(","), a.assets_expected, a.criteria_expected, a.date, findings)
    except (Refused, OSError, ValueError, KeyError) as e:
        print(f"REFUSED: {e if isinstance(e, Refused) else type(e).__name__ + ': ' + str(e)}", file=sys.stderr)
        return 2
    res["totals_by_layer_and_class"] = totals(res)
    res["certified_at_a_ceiling"] = sum(1 for c in res["certified"] if c["ceilings"])
    head = {k: v for k, v in res.items() if k not in ("certified", "fix_list")}
    a.out_dir.mkdir(parents=True, exist_ok=True)
    dump = lambda o: json.dumps(o, indent=1, sort_keys=True) + "\n"
    (a.out_dir / "CERTIFIED_LIST.md").write_text(render_certified(res))
    (a.out_dir / "CERTIFIED_LIST.json").write_text(dump(dict(head, certified=res["certified"])))
    (a.out_dir / "FIX_LIST.md").write_text(render_fix(res))
    (a.out_dir / "FIX_LIST.json").write_text(dump(dict(head, fix_list=res["fix_list"])))
    print(f"revision {res['registry_revision']}: {len(res['certified'])} of {res['assets']} CERTIFIED; {ceiling_summary(res)}; {d2_line(res)}; {counts_only_summary(res)}")
    for l, cs in res["totals_by_layer_and_class"].items():
        print(f"  {l}: " + "; ".join(f"{c} {n}" for c, n in cs.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
