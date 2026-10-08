#!/usr/bin/env python3
"""vocab_alias_report.py -- every non-canonical spelling the Vocab.alias detector found, per asset, and where it sits (SS ruling N-233 R2).

Reads ONE OR MORE census JSON files (the stamped files asset_census.py writes) and, for each asset whose Vocab.alias reading carries non-canonical spellings, lists
  asset . table.column (vocabulary class) -> each spelling, with its status under the N-233 R2 rule:
      REGISTERED   the exact string is in bg_ontology's alias set (the `synonyms` array or the `canonical_name_sa` of a brahma_ontology row): it counts as canonical, the cell no longer FAILs on it;
      UNREGISTERED it is not: a real FAIL, stays so;
  and WHERE it sits: the writer source (file:line) that carries the literal (the asset's writer file plus the transitive local imports the engine digests, i.e. the seed module) and the line that writes the table.

The registered set is the part that cannot be known offline. Give it as `--registered FILE` (the JSON text that
    psql -At -c "<the SQL printed by --print-registered-sql>"
answers against the live database, or the same JSON saved from the census role), OR leave it out and the report uses an OFFLINE STAND-IN built from the repo's own ontology source
(brahmagyan/l0_ontology.py ENTITIES: the rows brahma_ontology is seeded from) and says so in its first line; the live table is authoritative and may differ. Nothing is invented: no alias row is created.
Read-only: no database, no network. A static locator is best-effort (a spelling built at run time, or bound from a file that is not Python, is reported as 'no literal found in the writer source set').

Usage: vocab_alias_report.py --census census_L0.json census_L1.json census_L2.json [--registered live_aliases.json] [--out VOCAB_ALIAS_NONCANONICAL.md] [--json OUT.json]
       vocab_alias_report.py --print-registered-sql
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
_AC = None


def census_module():
    """asset_census loaded once by file path (it defines tables and helpers; importing it opens no connection)."""
    global _AC
    if _AC is None:
        _AC = sys.modules.get("asset_census")
        if _AC is None:
            spec = importlib.util.spec_from_file_location("asset_census", HERE / "asset_census.py")
            _AC = importlib.util.module_from_spec(spec)
            sys.modules["asset_census"] = _AC
            spec.loader.exec_module(_AC)
    return _AC


def extract(paths) -> list[dict]:
    """[{asset, layer, verdict, table, column, classes, spellings, unread}] for every found column of a Vocab.alias reading that carries non-canonical spellings. Pure over the files."""
    out = []
    for p in paths:
        d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        layers = [k for k in d if re.fullmatch(r"L\d", k)]
        if len(layers) != 1:
            raise ValueError(f"{p}: expected exactly one layer key, found {layers}")
        layer = layers[0]
        for a in d[layer].get("assets") or []:
            m = (a.get("measurements") or {}).get("Vocab.alias") or {}
            vv = m.get("vocab_values") or {}
            for f in vv.get("found") or []:
                sp = list(f.get("spellings") or [])
                if sp:
                    out.append(dict(asset=a["asset_id"], layer=layer, verdict=m.get("v"), table=f["table"], column=f["column"], classes=list(f.get("classes") or []),
                                    spellings=sp, unread=list(vv.get("unread") or [])))
    return sorted(out, key=lambda r: (r["asset"], r["table"], r["column"]))


def offline_registered() -> tuple[dict, str]:
    """(registered set, label): the stand-in built from the repo's ontology source, parsed exactly as the live JSON is."""
    ac = census_module()
    ont = ac._load_sidecar_module("brahmagyan/l0_ontology.py", "_vocab_report_ont")
    rows = [dict(c=e["entity_class"], id=e["canonical_id"], sa=e.get("canonical_name_sa"), syn=list(e.get("synonyms") or []))
            for e in ont.ENTITIES if e["entity_class"] in ac.VOCAB_REGISTERED_CLASSES]
    return ac.vocab_registered_parse(json.dumps(rows)), ("OFFLINE STAND-IN: the repo's brahmagyan/l0_ontology.py ENTITIES (the source brahma_ontology is seeded from), not a read of the live table")


def live_registered(path: pathlib.Path) -> tuple[dict, str]:
    ac = census_module()
    return ac.vocab_registered_parse(pathlib.Path(path).read_text(encoding="utf-8")), f"LIVE alias set read from {pathlib.Path(path).name} (the answer of the registered-alias SQL against brahma_ontology)"


def classify(spelling: str, registered: dict) -> dict:
    """{status: REGISTERED|UNREGISTERED, sources, ids} for one spelling (the exact string must be registered; a case variant or a padded form of a registered alias is not)."""
    ac = census_module()
    r = ac.vocab_registered_set(registered).get(spelling)
    return dict(status="REGISTERED", sources=r["sources"], ids=r["ids"]) if r else dict(status="UNREGISTERED", sources=[], ids=[])


def writer_paths(aid: str) -> list[pathlib.Path]:
    """The source files the engine digests for the asset's writer (registered file, declared source_paths, transitive local imports): where a seeded literal can live. [] when unknown."""
    ac = census_module()
    prefix = aid.split("_")[0] + "_"
    try:
        files = ac.registered_ids(prefix).get(aid) or []
        rels = ac._writer_code_paths(aid, files, True) if files else []
    except Exception:                                    # noqa: BLE001 -- a locator is best-effort, never a crash
        rels = []
    return [ac.ROOT / r for r in rels]


def locate(aid: str, table: str, spelling: str, limit: int = 3) -> dict:
    """{literal: [file:line ...], table_write: [file:line ...]} best-effort over the writer's source set."""
    ac = census_module()
    lit = re.compile(r"""(['"])""" + re.escape(spelling) + r"""\1""")
    tab = re.compile(r"\b(?:INSERT\s+INTO|UPDATE|COPY)\s+(?:public\.)?" + re.escape(table) + r"\b", re.I)
    out = dict(literal=[], table_write=[])
    for p in writer_paths(aid):
        try:
            lines = p.read_text(encoding="utf-8").split("\n")
        except (OSError, UnicodeDecodeError):
            continue
        rel = p.relative_to(ac.ROOT).as_posix()
        for i, ln in enumerate(lines, 1):
            if len(out["literal"]) < limit and lit.search(ln):
                out["literal"].append(f"{rel}:{i}")
            if len(out["table_write"]) < 1 and tab.search(ln):
                out["table_write"].append(f"{rel}:{i}")
    return out


def report(paths, registered: dict, label: str, with_locations: bool = True) -> dict:
    rows = extract(paths)
    assets: dict = {}
    for r in rows:
        a = assets.setdefault(r["asset"], dict(asset=r["asset"], layer=r["layer"], verdict=r["verdict"], columns=[]))
        sp = []
        for s in r["spellings"]:
            c = classify(s, registered)
            sp.append(dict(spelling=s, **c, **(locate(r["asset"], r["table"], s) if with_locations else dict(literal=[], table_write=[]))))
        a["columns"].append(dict(table=r["table"], column=r["column"], classes=r["classes"], spellings=sp, unread=r["unread"]))
    for a in assets.values():
        unreg = [s for c in a["columns"] for s in c["spellings"] if s["status"] == "UNREGISTERED"]
        a["unregistered"] = len(unreg)
        a["after"] = "FAIL (unregistered spelling remains)" if unreg else ("PARTIAL (nothing unregistered, but part of the asset was unread)" if any(c["unread"] for c in a["columns"]) else "no longer FAIL on spelling (PASS or the next finding)")
    n_fail_before = len(assets)
    n_still = sum(1 for a in assets.values() if a["unregistered"])
    return dict(label=label, assets=dict(sorted(assets.items())), summary=dict(assets_with_noncanonical_spellings=n_fail_before, still_fail_after_rule=n_still, cleared_by_rule=n_fail_before - n_still,
                                                                               spellings=sum(len(c["spellings"]) for a in assets.values() for c in a["columns"]),
                                                                               registered=sum(1 for a in assets.values() for c in a["columns"] for s in c["spellings"] if s["status"] == "REGISTERED"),
                                                                               unregistered=sum(a["unregistered"] for a in assets.values())))


def render(rep: dict) -> str:
    s = rep["summary"]
    out = ["# VOCAB_ALIAS_NONCANONICAL", "", f"Registered alias set: {rep['label']}.", "",
           f"{s['assets_with_noncanonical_spellings']} asset(s) carry non-canonical spellings in a Vocab.alias reading; {s['spellings']} spelling(s) in all: {s['registered']} REGISTERED (count as canonical under N-233 R2), "
           f"{s['unregistered']} UNREGISTERED (real FAIL). {s['cleared_by_rule']} asset(s) have no unregistered spelling left; {s['still_fail_after_rule']} still FAIL.", "",
           "Spellings come from the census sample (the first rows of each column and the bounded existence read), so a column may hold more than listed.", ""]
    for aid, a in rep["assets"].items():
        out += [f"## {aid} ({a['layer']}, census reading {a['verdict']}; after the rule: {a['after']})"]
        for c in a["columns"]:
            out.append(f"- {c['table']}.{c['column']} ({'/'.join(c['classes'])})")
            for sp in c["spellings"]:
                st = sp["status"] + (f" via {'+'.join(sp['sources'])} of {', '.join(sp['ids'][:3])}" if sp["status"] == "REGISTERED" else "")
                loc = ", ".join(sp["literal"]) or "no literal found in the writer source set"
                tw = f"; table written at {sp['table_write'][0]}" if sp["table_write"] else ""
                out.append(f"  - `{sp['spelling']}`: {st}; literal at {loc}{tw}")
            if c["unread"]:
                out.append(f"  - unread: {'; '.join(c['unread'][:2])[:300]}")
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--census", nargs="+", type=pathlib.Path)
    ap.add_argument("--registered", type=pathlib.Path, help="JSON answer of the registered-alias SQL against the live brahma_ontology (default: an offline stand-in from the repo)")
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--json", type=pathlib.Path)
    ap.add_argument("--no-locations", action="store_true")
    ap.add_argument("--print-registered-sql", action="store_true")
    a = ap.parse_args(argv)
    if a.print_registered_sql:
        print(census_module().vocab_registered_sql())
        return 0
    if not a.census:
        ap.error("--census is required")
    registered, label = live_registered(a.registered) if a.registered else offline_registered()
    rep = report(a.census, registered, label, with_locations=not a.no_locations)
    txt = render(rep)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(txt + "\n", encoding="utf-8")
    if a.json:
        a.json.write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if not a.out:
        print(txt)
    print(json.dumps(rep["summary"], sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
