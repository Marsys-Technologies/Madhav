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
    certified, fixes = [], {}
    for aid in sorted(all_assets):
        cells = all_assets[aid]
        bad = []
        for name in sorted(cells):
            ck = cells[name]
            if ck["v"] == PASS or is_ruled_na(ck):
                continue
            bad.append(dict(layer=ref[aid][0], criterion=name, verdict=ck["v"], cause=ck["cause"],
                            cause_class=classify(name, ck["v"], ck.get("state") or "", ck["cause"])))
        if bad:
            fixes[aid] = bad
        else:
            certified.append(dict(asset=aid, layer=ref[aid][0], revision=rev, census=ref[aid][1],
                                  measured_pass=sum(c["v"] == PASS for c in cells.values()),
                                  ruled_na=sum(is_ruled_na(c) for c in cells.values()), date=date,
                                  findings=str(findings.get(aid, ""))))
    return dict(registry_revision=rev, registry_fingerprint=loaded[0]["fp"], db_identity=dict(zip(("database", "system_id_sha256"), loaded[0]["db"])),
                layers=sorted(layers), date=date,
                tool=[dict(tool_commit=c, tool_dirty=dirty) for c, dirty in sorted({x["tool"] for x in loaded}, key=str)], assets=len(all_assets), certified=certified, fix_list=fixes)


def _cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\t", " ")


def tool_str(r: dict) -> str:
    return ",".join(f"{str(t['tool_commit'])[:9]}{'(dirty)' if t['tool_dirty'] else ''}" for t in r["tool"])


def render_certified(r: dict) -> str:
    out = [f"# CERTIFIED_LIST", f"registry revision {r['registry_revision']} (fingerprint {r['registry_fingerprint'][:12]}); layers {','.join(r['layers'])}; "
           f"date {r['date']}; tool {tool_str(r)}; {len(r['certified'])} of {r['assets']} assets certified", "",
           "| asset | revision | census file | measured PASS | ruled N/A | date | known findings |", "|---|---|---|---|---|---|---|"]
    out += [f"| {_cell(c['asset'])} | {c['revision']} | {_cell(c['census'])} | {c['measured_pass']} | {c['ruled_na']} | {c['date']} | {_cell(c['findings'])} |"
            for c in r["certified"]]
    return "\n".join(out) + "\n"


def totals(r: dict) -> dict:
    """layer -> cause class -> number of fix-list items"""
    t: dict = {}
    for items in r["fix_list"].values():
        for it in items:
            t.setdefault(it["layer"], {}).setdefault(it["cause_class"], 0)
            t[it["layer"]][it["cause_class"]] += 1
    return {l: dict(sorted(c.items())) for l, c in sorted(t.items())}


def render_fix(r: dict) -> str:
    out = ["# FIX_LIST", f"registry revision {r['registry_revision']}; date {r['date']}; tool {tool_str(r)}; {len(r['fix_list'])} of {r['assets']} assets not certified", ""]
    for aid, items in r["fix_list"].items():
        out.append(f"## {aid} ({len(items)} open)")
        for cls in CLASS_ORDER:
            sel = [i for i in items if i["cause_class"] == cls]
            if sel:
                out.append(f"- {cls}")
                out += [f"  - {i['criterion']} {i['verdict']}: {_cell(i['cause'])}" for i in sel]
        out.append("")
    return "\n".join(out)


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
    head = {k: v for k, v in res.items() if k not in ("certified", "fix_list")}
    a.out_dir.mkdir(parents=True, exist_ok=True)
    dump = lambda o: json.dumps(o, indent=1, sort_keys=True) + "\n"
    (a.out_dir / "CERTIFIED_LIST.md").write_text(render_certified(res))
    (a.out_dir / "CERTIFIED_LIST.json").write_text(dump(dict(head, certified=res["certified"])))
    (a.out_dir / "FIX_LIST.md").write_text(render_fix(res))
    (a.out_dir / "FIX_LIST.json").write_text(dump(dict(head, fix_list=res["fix_list"])))
    print(f"revision {res['registry_revision']}: {len(res['certified'])} of {res['assets']} CERTIFIED")
    for l, cs in res["totals_by_layer_and_class"].items():
        print(f"  {l}: " + "; ".join(f"{c} {n}" for c, n in cs.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
