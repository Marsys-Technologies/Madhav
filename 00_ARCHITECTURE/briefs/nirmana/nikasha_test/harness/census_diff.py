#!/usr/bin/env python3.13
"""Diff two census JSONs (prod vs sandbox) per asset per check.

Usage: census_diff.py <prod.json> <sandbox.json> <out.md> <sampled_tables...>
Expected differences: checks whose verdict depends on row counts of SAMPLED tables.
Any other disagreement is a finding (fidelity break).
"""
import json, sys

prod = json.load(open(sys.argv[1]))
sand = json.load(open(sys.argv[2]))
out = sys.argv[3]
sampled = set(sys.argv[4:])

def assets(doc):
    # census JSON: {"<layer>": {..., "assets": [...]}}
    if isinstance(doc, dict):
        for v in doc.values():
            if isinstance(v, dict) and 'assets' in v:
                return {a['asset_id']: a for a in v['assets']}
        if 'assets' in doc:
            return {a['asset_id']: a for a in doc['assets']}
    return doc

def checks(a):
    return a.get('measurements', {}) if isinstance(a, dict) else {}

P, S = assets(prod), assets(sand)

def verdict(c):
    if isinstance(c, dict):
        return c.get('v') or c.get('verdict') or c.get('status')
    return c

count_dependent = {'Count.floor', 'Build.completion', 'Dens.served', 'Complete.depth', 'Cost.baseline'}

lines = ["# Fidelity diff: production vs sandbox census", "",
         f"- prod: {sys.argv[1]}", f"- sandbox: {sys.argv[2]}",
         f"- sampled tables (count-dependent diffs expected): {', '.join(sorted(sampled)) or '(none)'}", "",
         "| asset | check | prod | sandbox | class |", "|---|---|---|---|---|"]
n_diff = n_unexpected = n_missing = 0
for aid in sorted(set(P) | set(S)):
    if aid not in P:
        lines.append(f"| {aid} | (asset) | ABSENT | present | UNEXPECTED |"); n_unexpected += 1; continue
    if aid not in S:
        lines.append(f"| {aid} | (asset) | present | ABSENT | UNEXPECTED |"); n_unexpected += 1; continue
    pa, sa = P[aid], S[aid]
    tt = set()
    for src in (pa, sa):
        v = src.get('target_table') or src.get('target_tables') or []
        tt |= {v} if isinstance(v, str) else set(v)
    is_sampled = bool(tt & sampled)
    for ck in sorted(set(checks(pa)) | set(checks(sa))):
        pv, sv = verdict(checks(pa).get(ck, {})), verdict(checks(sa).get(ck, {}))
        if pv == sv:
            continue
        n_diff += 1
        if is_sampled and ck in count_dependent:
            cls = "EXPECTED (sampled)"
        elif pv is None or sv is None:
            cls = "MISSING-CHECK"; n_missing += 1
        else:
            cls = "UNEXPECTED"; n_unexpected += 1
        lines.append(f"| {aid} | {ck} | {pv} | {sv} | {cls} |")

lines += ["", f"**Totals:** {n_diff} differing cells; {n_unexpected} UNEXPECTED; {n_missing} MISSING-CHECK."]
open(out, 'w').write("\n".join(lines) + "\n")
print(f"diffs={n_diff} unexpected={n_unexpected} missing={n_missing} -> {out}")
