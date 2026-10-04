#!/usr/bin/env python3
"""Offline helper (no database, no credential): turn a rehearsal-style patched function text (a complete CREATE OR REPLACE FUNCTION, e.g. the
rehearsal worker's patch B / patch C files) into the DATA the combined executor consumes: a list of hunks (name, old, new), each `old` asserted to
occur EXACTLY ONCE in the shipped live definition, plus the bound md5 / sha256 / zero-context diff digest / hunk count of the result.

  python3 make_function_patch.py --live live_defs/<fn>.LIVE.sql --patched <patched.sql> --prefix B [--min-context 1]

It PRINTS the Python literal to paste into FUNCTION_PATCHES (one FunctionPatch) and writes nothing. Admitting a hunk to the plan is a decision of
Strategic Suvarna, not of this tool: the executor's FUNCTION_PATCHES holds only reviewed hunks. The result is re-applied and compared with the
patched text before anything is printed, so a printed hunk list provably reproduces the patched function from the live one."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def _pa():
    spec = importlib.util.spec_from_file_location("d6_capture_patch_a_helper", HERE / "d6_capture_patch_a.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def normalise_patched(text: str, live: str) -> str:
    """psql prints `$function$;` for a statement and pg_get_functiondef prints `$function$` + newline: make the patched text end like the live one."""
    body = text.rstrip()
    if body.endswith("$function$;"):
        body = body[:-1]
    tail = live[len(live.rstrip()):]
    return body + (tail or "\n")


def derive_hunks(live: str, patched: str, prefix: str = "X", min_context: int = 1):
    a, b = live.splitlines(True), patched.splitlines(True)
    ops = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op[0] != "equal"]
    groups = [[i1, i2, j1, j2] for _, i1, i2, j1, j2 in ops]

    def expand(g):
        c = min_context
        while True:
            lo, hi = max(g[0] - c, 0), min(g[1] + c, len(a))
            old = "".join(a[lo:hi])
            if old and live.count(old) == 1:
                return lo, hi, c
            if lo == 0 and hi == len(a):
                raise ValueError("no unique anchor exists for a change")
            c += 1

    while True:
        spans = [expand(g) for g in groups]
        for k in range(1, len(groups)):
            if spans[k][0] < spans[k - 1][1]:                       # overlapping anchors: merge the two groups and retry
                groups[k - 1:k + 1] = [[groups[k - 1][0], groups[k][1], groups[k - 1][2], groups[k][3]]]
                break
        else:
            break
    hunks = []
    for n, (g, (lo, hi, c)) in enumerate(zip(groups, spans), 1):
        old = "".join(a[lo:hi])
        new = "".join(b[g[2] - (g[0] - lo): g[3] + (hi - g[1])])
        hunks.append((f"{prefix}{n}", old, new))
    return hunks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--live", required=True)
    ap.add_argument("--patched", required=True)
    ap.add_argument("--prefix", default="X")
    ap.add_argument("--min-context", type=int, default=1)
    a = ap.parse_args(argv)
    pa = _pa()
    live = pathlib.Path(a.live).read_bytes().decode("utf-8")
    patched = normalise_patched(pathlib.Path(a.patched).read_bytes().decode("utf-8"), live)
    hunks = derive_hunks(live, patched, a.prefix, a.min_context)
    rebuilt = pa.apply_hunks(live, hunks)
    if rebuilt != patched:
        print("REFUSED: the derived hunks do not reproduce the patched text", file=sys.stderr)
        return 1
    print("# derived from", a.live, "->", a.patched)
    print(f"# live md5 {hashlib.md5(live.encode()).hexdigest()} len {len(live)} sha256 {hashlib.sha256(live.encode()).hexdigest()}")
    print(f"# patched md5 {hashlib.md5(patched.encode()).hexdigest()} sha256 {hashlib.sha256(patched.encode()).hexdigest()}")
    print(f"# zero-context diff: {len(pa.unified_hunks(live, patched))} hunks, sha256 {pa.diff_digest(live, patched)}")
    print("HUNKS = (")
    for name, old, new in hunks:
        print(f"    ({name!r},\n     {old!r},\n     {new!r}),")
    print(")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
