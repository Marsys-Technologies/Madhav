#!/usr/bin/env python3
"""C50 — SETTLED-1 intake checker (LOCAL, offline: no database, no network).

Takes the two capture files PR #2903's re-pin tool writes — one made BEFORE S-L1
(`--capture-old`, the pinned old build) and one made AFTER it — plus the values from
Suvarṇa's SETTLED-1 notice as arguments, and reports PASS/STOP per rule:

  R1  Vimśottarī lords AND row counts unchanged at levels 1–3 (matched by the tool's
      (level, parent path, index) path index — row ids are not trusted across builds);
  R2  every boundary shift within the stated tolerance of the stated per-level shift
      (the tool's own `shift_stats` / `shift_problems` — the production rule, reused);
  R3  level-4 changes are ALLOWED and counted: the captures carry none by contract;
      a `--expected-shift 4=…` entry is echoed as declared-and-not-compared;
  R4  the natal graha_position fact_ids are unchanged (addendum 2: they are build-independent);
  R5  the post-S-L1 capture's daśā build id equals the notice's new build id.

Each capture is validated with the tool's own `validate_capture` (identity, selection
contract, checksum over identity + data, every row against the read contract, the tree,
the reference rows, the ten natal rows) — a malformed or self-inconsistent capture is a
STOP, never a guess.

Exit 0 = every rule PASS · 1 = a STOP · 2 = a usage/argument refusal.

    python3 scripts/gochara/settled1_intake_check.py --old pre.json --new post.json \
        --new-build-id <uuid> --expected-shift 1=6993 --expected-shift 2=6993 \
        --expected-shift 3=6993 --tolerance 5 [--chart-id <uuid>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repin_dasha_contract as R  # noqa: E402

LEVELS_REQUIRED = ("1", "2", "3")


def _parse_shift(text: str) -> tuple[str, int]:
    level, sep, seconds = text.partition("=")
    if not sep or level not in ("1", "2", "3", "4"):
        raise ValueError(f"--expected-shift must be LEVEL=SECONDS with LEVEL in 1..4, got {text!r}")
    try:
        value = int(seconds)
    except ValueError:
        raise ValueError(f"--expected-shift seconds must be a whole number, got {seconds!r}") from None
    return level, value


def _load_capture(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read the capture {path}: {exc}") from None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SETTLED-1 intake checker — two captures + the notice values, PASS/STOP per rule")
    ap.add_argument("--old", required=True, help="the pre-S-L1 capture (the pinned old build)")
    ap.add_argument("--new", required=True, help=" the post-S-L1 capture (the SETTLED-1 build)")
    ap.add_argument("--new-build-id", required=True, help="the new daśā build id from the SETTLED-1 notice")
    ap.add_argument("--expected-shift", action="append", required=True, metavar="LEVEL=SECONDS",
                    help="the notice's expected per-level boundary shift (levels 1, 2, 3 required; 4 echoed, never compared)")
    ap.add_argument("--tolerance", type=int, required=True, help="the notice's stated tolerance in seconds")
    ap.add_argument("--chart-id", default=None, help="expected chart (default: the old capture's)")
    args = ap.parse_args(argv)

    stops: list[str] = []

    def stop(rule: str, why: str) -> None:
        print(f"STOP {rule} — {why}")
        stops.append(rule)

    def passed(rule: str, what: str) -> None:
        print(f"PASS {rule} {what}")

    try:
        new_build = R.canon_uuid(args.new_build_id)
    except ValueError:
        print(f"REFUSAL: --new-build-id {args.new_build_id!r} is not a uuid", file=sys.stderr)
        return 2
    if args.tolerance < R.MIN_TOLERANCE_SECONDS:
        print(f"REFUSAL: --tolerance must be at least {R.MIN_TOLERANCE_SECONDS} s (the tool's floor), got {args.tolerance}",
              file=sys.stderr)
        return 2
    try:
        shifts = dict(_parse_shift(s) for s in args.expected_shift)
    except ValueError as exc:
        print(f"REFUSAL: {exc}", file=sys.stderr)
        return 2
    missing = [lv for lv in LEVELS_REQUIRED if lv not in shifts]
    if missing:
        print(f"REFUSAL: --expected-shift is missing level(s) {', '.join(missing)} "
              "(the notice states an expected shift for every in-scope level)", file=sys.stderr)
        return 2

    try:
        old_d, new_d = _load_capture(args.old), _load_capture(args.new)
    except ValueError as exc:
        stop("capture-load", str(exc))
        return 1

    chart = args.chart_id or old_d.get("chart_id")
    if not chart:
        stop("capture-old", "the old capture names no chart and --chart-id was not given")
        return 1

    # ── acquisition/load validation, the tool's own rule ────────────────────
    old_pin = R.canon_uuid(R.PERM.DASHA_READ_CONTRACT["build_id"])
    bad = R.validate_capture(old_d, chart, old_pin)
    if bad:
        stop("capture-old", "the pre-S-L1 capture is invalid: " + "; ".join(bad[:6]))
        return 1
    passed("capture-old", f"pre-S-L1 capture valid (chart {chart}, pinned build {old_pin})")
    bad = R.validate_capture(new_d, chart, new_build)
    if bad:
        stop("capture-new", "the post-S-L1 capture is invalid: " + "; ".join(bad[:6]))
        return 1
    passed("capture-new", "post-S-L1 capture valid (same chart, the notice's selection contract)")

    # ── R5: the daśā build id equals the notice's ───────────────────────────
    if R.canon_uuid(new_d["build_id"]) == new_build:
        passed("R5-build-id", f"daśā build id is the notice's {new_build}")
    else:
        stop("R5-build-id", f"the post-S-L1 capture carries build {new_d.get('build_id')}, the notice says {new_build}")

    # ── R1: lords and row counts unchanged at levels 1–3 ────────────────────
    old_idx, new_idx = R.index_paths(old_d["rows"]), R.index_paths(new_d["rows"])
    m = R.match(old_idx, new_idx)
    counts_old, counts_new = R.level_totals(old_d["rows"]), R.level_totals(new_d["rows"])
    problems = []
    if counts_old != counts_new:
        problems.append(f"row counts changed: {counts_old} -> {counts_new}")
    if m["only_old"] or m["only_new"]:
        problems.append(f"the row SETS differ: {len(m['only_old'])} only-old, {len(m['only_new'])} only-new")
    flips = [(k, old_idx[k]["lord_graha"], new_idx[k]["lord_graha"]) for k in m["matched"]
             if old_idx[k]["lord_graha"] != new_idx[k]["lord_graha"]]
    for k, a, b in flips[:5]:
        problems.append(f"lord flip at level {k[0]} path {k[1:]}: {a} -> {b}")
    if problems:
        stop("R1-lords-counts", "; ".join(problems))
    else:
        passed("R1-lords-counts",
               f"levels 1–3 keep every lord and count ({counts_old}); {len(m['matched'])} rows matched by path")

    # ── R2: every boundary shift within tolerance of the stated shift ───────
    if m["matched"]:
        stats = R.shift_stats(old_idx, new_idx, m["matched"])
        notice = {"expected_shift_seconds": {lv: s for lv, s in shifts.items() if lv != "4"},
                  "tolerance_seconds": args.tolerance}
        sp = R.shift_problems(stats, notice)
        if sp:
            stop("R2-shift", "; ".join(sp))
        else:
            passed("R2-shift",
                   f"every measured boundary shift is within ±{args.tolerance} s of the notice's per-level shift")
    else:
        stop("R2-shift", "no rows matched — no shift can be measured")

    # ── R3: level-4 changes allowed and counted ─────────────────────────────
    l4 = sum(1 for r in old_d["rows"] + new_d["rows"] if int(r["level_n"]) >= 4)
    note = f"; the notice declares a level-4 shift of {shifts['4']} s — allowed, never compared" if "4" in shifts else ""
    passed("R3-level4-allowed",
           f"level 4 is out of scope ({l4} level-4 rows in the captures; changes there are allowed, not judged){note}")

    # ── R4: natal graha_position fact_ids unchanged ─────────────────────────
    old_ids = {n.get("fact_id") for n in old_d.get("natal", [])}
    new_ids = {n.get("fact_id") for n in new_d.get("natal", [])}
    if old_ids == new_ids and None not in old_ids:
        passed("R4-natal-fact-ids", f"all ten natal fact_ids unchanged ({len(old_ids)} ids)")
    else:
        stop("R4-natal-fact-ids",
             f"natal fact_ids changed: only-old {sorted(old_ids - new_ids)}, only-new {sorted(new_ids - old_ids)}")

    if stops:
        print(f"settled1-intake: {len(stops)} STOP(s)", file=sys.stderr)
        return 1
    print("settled1-intake: every rule PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
