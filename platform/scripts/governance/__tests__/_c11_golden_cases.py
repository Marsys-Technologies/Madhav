"""_c11_golden_cases.py: the cases whose Carr.D1 records C1-1 (the Carr harness refactor) must leave BYTE-IDENTICAL.

`build_cases(d1_module)` runs `d1_measure` for the bg_phaladeepika_latta declaration (the committed spec in asset_declarations.json) against the
committed chunk + row fixture (fixtures/phaladeepika_latta_d1_fixture.json), and against a fixed list of seeded defects, and returns
{case_name: record}. The golden (fixtures/c1_1_latta_d1_golden_main_adb0db29d.json) was produced by running this function against the
carriage_d1.py of origin/main adb0db29d (a `git archive` of that commit, before any C1-1 edit); test_e6_c11_carr_harness.py re-runs it against
the working-tree module and compares the JSON text, so a changed key, a changed key ORDER or a changed value fails.

To regenerate (only ever against a reviewed change to the D1 record; never to make a test pass):
    python3 _c11_golden_cases.py <dir holding the carriage_d1.py to measure> > golden.json
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
FIXTURE = HERE / "fixtures" / "phaladeepika_latta_d1_fixture.json"
DECLARATIONS = GOV / "asset_declarations.json"
AID = "bg_phaladeepika_latta"
STATE = "sourced_ocr_unverified"


def load_d1(directory):
    """carriage_d1.py loaded by file path from `directory` (under a private module name, so the working-tree module and a snapshot never collide)."""
    p = pathlib.Path(directory) / "carriage_d1.py"
    spec = importlib.util.spec_from_file_location(f"carriage_d1_golden_{hashlib.sha256(str(p).encode()).hexdigest()[:8]}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inputs():
    """(spec, chunks_by_id, rows) as committed: the declaration's own spec, the fixture's two chunks, the fixture's eight rows."""
    spec = json.loads(DECLARATIONS.read_text(encoding="utf-8"))["assets"][AID]["carriage"]["spec"]
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return spec, {c["chunk_id"]: c for c in fx["classical_text_chunks"]}, fx["bg_phaladeepika_latta"]


def build_cases(d1):
    spec, chunks, rows = inputs()

    def run(name, state=STATE, rws=rows, chs=chunks, table="bg_phaladeepika_latta", sp=spec, out=None):
        out[name] = d1.d1_measure(sp, state, copy.deepcopy(chs), copy.deepcopy(rws) if rws is not None else None, table)

    out = {}
    run("pass", out=out)
    moon = copy.deepcopy(rows)
    [r.update(count_from_graha=21) for r in moon if r["graha"] == "Moon"]
    run("partial_moon_count", rws=moon, out=out)
    swapped = copy.deepcopy(rows)
    [r.update(direction="forward") for r in swapped if r["direction"] == "backward"]
    run("partial_direction", rws=swapped, out=out)
    suffix = copy.deepcopy(rows)
    [r.update(effect_description=(r["effect_description"] or "") + " and more") for r in suffix if r["effect_description"]]
    run("partial_effect_suffix", rws=suffix, out=out)
    run("partial_dropped_row", rws=rows[:-1], out=out)
    run("partial_extra_row", rws=rows + [dict(rows[0], graha="Ketu")], out=out)
    run("partial_duplicate_claimant", rws=rows + [dict(rows[0])], out=out)
    run("no_det_unsourced", state="unsourced", out=out)
    run("no_det_refuted", state="refuted", out=out)
    run("no_det_wrong_table", table="some_other_table", out=out)
    run("no_det_empty_rows", rws=[], out=out)
    run("no_det_rows_unreadable", rws=None, out=out)
    gone = {k: v for k, v in chunks.items() if k != "phaladeepika_pg0339_c01"}
    run("no_det_missing_chunk", chs=gone, out=out)
    bad = copy.deepcopy(chunks)
    bad["phaladeepika_pg0338_c01"]["content_sha256"] = "0" * 64
    run("no_det_bad_hash", chs=bad, out=out)
    nomark = copy.deepcopy(spec)
    nomark["span"] = {"start": "no such marker in the passage"}
    run("no_det_span_marker_absent", sp=nomark, out=out)
    return out


if __name__ == "__main__":
    mod = load_d1(sys.argv[1])
    print(json.dumps(build_cases(mod), ensure_ascii=False, indent=1))
