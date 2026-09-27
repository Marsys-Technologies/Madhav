#!/usr/bin/env python3
"""Surgical replace: sub.py FILE < spec ; spec = OLD\n=====>>>\nNEW (exactly one occurrence required)."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); spec = sys.stdin.read()
old, new = spec.split("\n=====>>>\n", 1)
if new.endswith("\n"): new = new[:-1]  # the heredoc's own trailing newline
txt = p.read_text(encoding="utf-8")
n = txt.count(old)
if n != 1:
    sys.exit(f"expected exactly 1 occurrence, found {n}")
p.write_text(txt.replace(old, new, 1), encoding="utf-8")
print(f"ok: {p.name} ({len(old)} -> {len(new)} chars)")
