"""Offline MB-3 reassembler: readback_sql output -> exactly what read_candidate returns.

The one statement in fleet/sql/mb3-capture-read.sql (run through the existing
read-only readback_sql kind; one statement is one snapshot) yields tab-separated
rows `section, row_json`. This module needs no connection: it restores the
Python types read_candidate would have received and calls the same
assemble_candidate, so every refusal and every byte of the bundle is shared.
A missing or repeated section is a named refusal, never a zero.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime

from . import measuring_capture as mc

SECTIONS = ("binding", "manifest", "sealed", "published", "contact", "record", "window")


class _Range:
    """Duck-typed like a psycopg Range (mc._plain); deliberately not a tuple, which _plain would flatten."""

    def __init__(self, lower, upper, bounds, isempty):
        self.lower, self.upper, self.bounds, self.isempty = lower, upper, bounds, isempty


def _ts(value):
    return None if value is None else datetime.fromisoformat(value)


def _contact(row):
    return {**row, "t_in": _ts(row["t_in"]), "t_out": _ts(row["t_out"]), "t_exact": _ts(row["t_exact"]),
            "delta_lambda": None if row["delta_lambda"] is None else float(row["delta_lambda"])}


def _record(row):
    supports = [_Range(_ts(i["lo"]), _ts(i["hi"]), i["bounds"], i["empty"]) for i in row["temporal_support_intervals"]]
    return {**row, "temporal_support_intervals": supports}


def reassemble_candidate(tsv, *, run_id, source_commit, stretch_sink):
    """tsv: readback_sql stdout (header + rows). Same return and refusals as read_candidate."""
    csv.field_size_limit(sys.maxsize)
    rows = list(csv.reader(io.StringIO(tsv, newline=""), delimiter="\t"))
    if not rows or rows[0] != ["section", "row_json"]:
        raise mc.CaptureRefused("readback_header_invalid")
    got = {name: [] for name in SECTIONS}
    for line in rows[1:]:
        if len(line) != 2 or line[0] not in got:
            raise mc.CaptureRefused("readback_row_invalid")
        got[line[0]].append(json.loads(line[1]))
    for name in ("binding", "sealed", "published"):
        if len(got[name]) != 1:
            raise mc.CaptureRefused(f"readback_section_missing_or_repeated: {name}")
    binding = got["binding"][0]
    manifests = [{**m, "lo": _ts(m["lo"]), "hi": _ts(m["hi"])} for m in got["manifest"]]
    return mc.assemble_candidate(
        chart_id=binding["chart_id"], generation=binding["generation"], run_id=run_id, source_commit=source_commit,
        stretch_sink=stretch_sink, manifests=manifests, sealed_count=got["sealed"][0]["n"],
        published_count=got["published"][0]["n"], contacts=[_contact(r) for r in got["contact"]],
        records=[_record(r) for r in got["record"]],
        windows=[{**w, "lo": _ts(w["lo"]), "hi": _ts(w["hi"])} for w in got["window"]])


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tsv", required=True, help="readback_sql output file")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--stretch-sink", required=True, help="JSON list of exported STRETCH_SINK records")
    ap.add_argument("--out", required=True, help="new golden directory (created once)")
    a = ap.parse_args(argv)
    with open(a.tsv, encoding="utf-8", newline="") as f:
        tsv = f.read()
    with open(a.stretch_sink, encoding="utf-8") as f:
        sink = json.load(f)
    bundle = reassemble_candidate(tsv, run_id=a.run_id, source_commit=a.source_commit, stretch_sink=sink)
    print(json.dumps(mc.write_bundle(a.out, bundle), sort_keys=True))


if __name__ == "__main__":
    main()
