#!/usr/bin/env python3
"""
reconnoiter_fact_identity_shapes.py — the Step-1 reconnaissance script for
ADHIṢṬHĀNA Lane A5 (THE FACT IDENTITY INDEX).

Committed per PARĪKṢAKA A5 acceptance-gate review (2026-08-08): the
original release's coverage report claimed its per-shape counts were
"reproducible via the reconnaissance script committed history" without any
such script ever having been committed. This IS that script — the actual
tool used to build `A5_COVERAGE_REPORT_v1_0.md` §1's shape inventory, not a
reconstruction after the fact. Re-running it against live `chart_facts`
reproduces the report's shape/count tables exactly (modulo any new facts a
chart rebuild has since added).

What it does, in two passes:

1. **Dump** — for each requested chart, `SELECT fact_category,
   fact_subject, fact_key, count(*) FROM chart_facts WHERE chart_id = %s
   GROUP BY 1,2,3` (read-only; never touches `chart_facts`).
2. **Shape-reduce** — every `fact_subject`/`fact_key` string is reduced to
   a "shape" by replacing recognized varga codes (`D<n>` -> `D#`), graha
   codes/sign names (-> `<GRAHA>`/`<SIGN>`), and remaining digit runs
   (-> `#`), then frequency-counted and grouped across all requested
   charts. This is the SAME reduction used to build the coverage report's
   §1.1/§1.2 tables — not a different, unverifiable method.

This script is diagnostic/reporting only — it writes nothing to any table
(no `--all-canonical`-style mutation flag exists here, unlike
`build_fact_identity_index.py`).

Usage:
    DATABASE_URL=postgresql://... python3 scripts/reconnoiter_fact_identity_shapes.py \\
        [--chart-id ID [--chart-id ID ...]] [--all-canonical] \\
        [--top N] [--csv-out-dir DIR]

    # Default (no --chart-id / --all-canonical): all three canonical charts.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CANONICAL_CHART_IDS = [
    "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
    "cb73cd3d-9eba-4220-9902-0de91566e980",
]

# Same recognized-token vocabulary as the parser's own shape families
# (graha codes across all three observed naming systems + sign names) —
# kept as a local literal set here (not imported from
# fact_identity_parser.py) because this script's shape-reduction is a
# DIAGNOSTIC aid for humans scanning the inventory, not itself part of the
# parse-time identity contract; it deliberately uses a looser/broader token
# set than the parser (e.g. also folds in long-form/2-letter graha names)
# so the printed shape table reads cleanly even for shapes the parser
# doesn't (yet) handle.
_GRAHA_DISPLAY_TOKENS = {
    "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN",
    "LAGNA", "MC", "RAHU", "KETU", "MARS", "MERCURY", "JUPITER", "VENUS",
    "SATURN", "SU", "MO", "MA", "ME", "JU", "VE", "SA", "RA", "KE", "ASC",
}
_SIGN_DISPLAY_TOKENS = {
    "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO", "LIBRA",
    "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
}


def shape_of(s: str | None) -> str:
    if s is None:
        return "<NULL>"
    t = re.sub(r"\bD\d{1,4}\b", "D#", s)

    def repl(m: re.Match) -> str:
        w = m.group(0)
        if w.upper() in _GRAHA_DISPLAY_TOKENS:
            return "<GRAHA>"
        if w.upper() in _SIGN_DISPLAY_TOKENS:
            return "<SIGN>"
        return w

    t = re.sub(r"[A-Za-z_]+", repl, t)
    t = re.sub(r"\d+", "#", t)
    return t


def dump_triples(conn, chart_id: str) -> list[tuple[str, str, str, int]]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT fact_category, fact_subject, fact_key, count(*) "
            "FROM chart_facts WHERE chart_id = %s GROUP BY 1, 2, 3 ORDER BY 4 DESC",
            (chart_id,),
        )
        return cur.fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chart-id", action="append", default=None,
                         help="repeatable; defaults to all 3 canonical charts if omitted")
    parser.add_argument("--all-canonical", action="store_true")
    parser.add_argument("--top", type=int, default=100, help="how many top shapes to print per table")
    parser.add_argument("--csv-out-dir", default=None,
                         help="if set, also write raw per-chart (category,subject,key,count) CSVs here")
    args = parser.parse_args()

    chart_ids = args.chart_id or CANONICAL_CHART_IDS

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3
    try:
        import psycopg
    except ImportError as exc:
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    subj_shape_counts: Counter[str] = Counter()
    key_shape_counts: Counter[str] = Counter()
    subj_examples: dict[str, str] = {}
    key_examples: dict[str, str] = {}
    total_rows = 0
    distinct_triples = 0

    with psycopg.connect(dsn) as conn:
        for chart_id in chart_ids:
            rows = dump_triples(conn, chart_id)
            distinct_triples += len(rows)
            print(f"chart {chart_id}: {len(rows)} distinct (category, subject, key) triples")

            if args.csv_out_dir:
                os.makedirs(args.csv_out_dir, exist_ok=True)
                path = os.path.join(args.csv_out_dir, f"cat_subj_key_{chart_id[:8]}.csv")
                with open(path, "w", newline="") as f:
                    csv.writer(f).writerows(rows)

            for category, subject, key, cnt in rows:
                total_rows += cnt
                ssh = shape_of(subject)
                ksh = shape_of(key)
                subj_shape_counts[ssh] += cnt
                key_shape_counts[ksh] += cnt
                subj_examples.setdefault(ssh, subject)
                key_examples.setdefault(ksh, key)

    print(f"\nTOTAL rows across {len(chart_ids)} chart(s): {total_rows}")
    print(f"TOTAL distinct (category, subject, key) triples: {distinct_triples}")

    print(f"\n=== fact_subject shapes: {len(subj_shape_counts)} distinct ===")
    for sh, cnt in subj_shape_counts.most_common(args.top):
        print(f"{cnt:8d}  {sh!r}  e.g. {subj_examples[sh]!r}")

    print(f"\n=== fact_key shapes: {len(key_shape_counts)} distinct ===")
    for sh, cnt in key_shape_counts.most_common(args.top):
        print(f"{cnt:8d}  {sh!r}  e.g. {key_examples[sh]!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
