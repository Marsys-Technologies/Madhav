#!/usr/bin/env python3
"""WRITE-SCOPE REGRESSION TEST for 00_ARCHITECTURE/control/m0_deferral_register.py.

    Run:  python3 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py
    Exit: 0 = all checks passed · 1 = a check failed (details on stdout)

WHY THIS FILE EXISTS
────────────────────
KĀRAKA M0-T62, Standing Queue SQ-12, on ADHIKĀRIN ruling D-44 part 4 (T1-T6).
KĀRAKA M0-T69, on M0-T63's finding F-T63-2 and ADHIKĀRIN ruling D-89 (T7-T8).

`m0_deferral_register.py` used to write four `deferred_rule_disclosures*` keys into
`platform/scripts/governance/asset_catalogue_disclosed_residuals.json` as a SIDE EFFECT,
outside the scope its own docstring and PROVENANCE both declared. That side effect

  * put a correctly-behaving agent (M0-T46) in front of `git checkout --`, the command the
    campaign's standing restore rule forbids; and
  * had become destructive, because the live block is no longer the generator's output —
    M0-T49/T51/T55 wrote D-54's fifteen AUTHORISED disclosures into it on D-57's corrected
    ground (certified V-35/V-37) and `DISCLOSURE_DRAFT` was never updated to match. A run
    would have deleted three authorised entries and reverted twelve to unauthorised ones,
    and it would have looked like a clean generator run while doing it.

M0-T62 removed the write. This file is the detector that keeps it removed. Per CLAUDE.md
§N.8 the fix is not finished until something would go red if the defect returned — a scope
declaration with no detector behind it is the defect, not the cure, and closing one
undetected claim by adding another would be the same mistake one layer out.

WHAT IT PROVES, AND HOW
───────────────────────
  T1  the declaration is machine-readable and names exactly the two register outputs
  T2  a REAL RUN, in a throwaway copy of the tree, changes only the declared paths
  T3  the residuals JSON is BYTE-IDENTICAL after that run (the specific regression)
  T4  `_write()` refuses an undeclared path, raising before any bytes are written
  T5  no write call anywhere in the source bypasses `_write()`   (static, AST)
  T6  MUTATION CONTROL — the checks above are re-run against two DELIBERATELY BROKEN
      copies of the generator, and this test FAILS unless they go red. A test that has
      never been shown to fail is an unearned green (§N.8); T6 is the earning.
  T7  the 15-CELL CROSS-CHECK — `origin_tally()`'s reconstruction from per-entry
      provenance stamps against `_meta.reading_history[0]`, the v1.0 tally M0-T31
      recorded at write time by a completely different mechanism. Both sides are
      ANCHORED INDEPENDENTLY before a single cell is compared (D-89).
  T8  MUTATION CONTROL FOR T7 — four one-sided mutations, two per side: a wrong-but-
      well-formed side must be caught by the COMPARISON, an absent side by that side's
      OWN ANCHOR. If only one side's mutations fire, the other side is unanchored and
      T7 is half a test.

SAFETY: nothing here touches the live tree. Every run happens inside a temporary
directory that is a COPY, and the live residuals JSON and register JSON are only ever
READ. No file is mutated in place, so this test opens no D-77 mutation window: every
deliberately broken generator is a throwaway copy in a temporary directory, and every
deliberately broken tally is an in-memory dict.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "00_ARCHITECTURE/control/m0_deferral_register.py"
RESIDUALS_REL = "platform/scripts/governance/asset_catalogue_disclosed_residuals.json"
OUT_MD_REL = "00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.md"
OUT_JSON_REL = "00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.json"

FAILURES: list[str] = []
NOTES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(f"{label}{(' — ' + detail) if detail else ''}")
    return ok


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("m0dr_under_test", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # import is side-effect-free: no I/O at module level
    return mod


def load_mutated_generator(extra_source: str):
    """Load a DELIBERATELY BROKEN copy of the generator, from a throwaway sandbox.

    The live file is never edited. D-77 requires a KĀRAKA to announce an in-place
    mutation window; this test opens none, because the mutation only ever exists in a
    temporary directory that is deleted before this function returns. (The module object
    survives the directory: the generator does no file I/O at import time.)
    """
    with tempfile.TemporaryDirectory(prefix="m0t69-mutate-") as td:
        tmp = pathlib.Path(td).resolve()
        script = build_sandbox(tmp, GENERATOR.read_text(encoding="utf-8") + extra_source)
        spec = importlib.util.spec_from_file_location("m0dr_mutated", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


# ── sandbox ──────────────────────────────────────────────────────────────────
def build_sandbox(tmp: pathlib.Path, generator_source: str) -> pathlib.Path:
    """A throwaway tree with exactly the files the generator reads or writes."""
    (tmp / "00_ARCHITECTURE/control").mkdir(parents=True)
    (tmp / "platform/scripts/governance").mkdir(parents=True)
    (tmp / "00_ARCHITECTURE/control/m0_deferral_register.py").write_text(
        generator_source, encoding="utf-8")
    for rel in (OUT_MD_REL, OUT_JSON_REL, RESIDUALS_REL):
        src = ROOT / rel
        if src.exists():
            shutil.copy2(src, tmp / rel)
    return tmp / "00_ARCHITECTURE/control/m0_deferral_register.py"


def snapshot(tmp: pathlib.Path) -> dict[str, str]:
    return {str(p.relative_to(tmp)): sha(p) for p in sorted(tmp.rglob("*")) if p.is_file()}


def run_sandbox(generator_source: str) -> tuple[int, str, dict[str, str], dict[str, str]]:
    """Run a (possibly mutated) generator in a fresh sandbox. Returns rc, output, before, after."""
    with tempfile.TemporaryDirectory(prefix="m0t62-scope-") as td:
        tmp = pathlib.Path(td).resolve()
        script = build_sandbox(tmp, generator_source)
        before = snapshot(tmp)
        proc = subprocess.run([sys.executable, str(script)], capture_output=True,
                              text=True, cwd=str(tmp))
        after = snapshot(tmp)
        return proc.returncode, (proc.stdout + proc.stderr), before, after


def changed_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return ({k for k in after if before.get(k) != after[k]}
            | {k for k in before if k not in after})


# ── T1 ───────────────────────────────────────────────────────────────────────
def t1_declaration() -> None:
    print("\nT1 — the declaration is machine-readable and says what it should")
    mod = load_generator()
    declared = getattr(mod, "DECLARED_WRITES", None)
    if not check(declared is not None, "DECLARED_WRITES exists"):
        return
    rels = sorted(str(pathlib.Path(p).resolve().relative_to(ROOT)) for p in declared)
    check(rels == sorted([OUT_MD_REL, OUT_JSON_REL]),
          "DECLARED_WRITES names exactly the two register outputs", f"got {rels}")
    check(hasattr(mod, "_write"), "_write() exists (the declaration's detector)")
    check(hasattr(mod, "_report_disclosure_divergence"),
          "_report_disclosure_divergence() exists (the read-only replacement)")
    check(not hasattr(mod, "_write_disclosure_block"),
          "_write_disclosure_block() is GONE (the removed side effect)")
    resid = getattr(mod, "RESIDUALS_JSON", None)
    check(resid is not None and pathlib.Path(resid) not in {pathlib.Path(p) for p in declared},
          "the residuals JSON is NOT in the declared write scope")


# ── T2 / T3 ──────────────────────────────────────────────────────────────────
def t2_t3_real_run() -> None:
    print("\nT2/T3 — a real run in a throwaway copy of the tree")
    rc, out, before, after = run_sandbox(GENERATOR.read_text(encoding="utf-8"))
    check(rc == 0, "the generator exits 0", f"rc={rc}; {out.strip()[:400]}")
    changed = changed_paths(before, after)
    allowed = {OUT_MD_REL, OUT_JSON_REL}
    check(changed <= allowed, "only declared paths changed",
          f"changed={sorted(changed)}")
    check(before.get(RESIDUALS_REL) == after.get(RESIDUALS_REL),
          "T3 — asset_catalogue_disclosed_residuals.json is BYTE-IDENTICAL after the run",
          f"before={before.get(RESIDUALS_REL, '')[:16]} after={after.get(RESIDUALS_REL, '')[:16]}")
    check("READ, NOT WRITTEN" in out,
          "the run REPORTS the divergence instead of reconciling it")
    NOTES.append("sandbox run stdout tail: " + out.strip().splitlines()[-1][:200]
                 if out.strip() else "no output")


# ── T4 ───────────────────────────────────────────────────────────────────────
def t4_write_refuses() -> None:
    print("\nT4 — _write() refuses an undeclared path, before any bytes are written")
    mod = load_generator()
    with tempfile.TemporaryDirectory(prefix="m0t62-refuse-") as td:
        victim = pathlib.Path(td) / "undeclared.json"
        try:
            mod._write(victim, "this must never land")
        except Exception as exc:                                   # noqa: BLE001
            check(exc.__class__.__name__ == "ScopeViolation",
                  "raises ScopeViolation", f"raised {exc.__class__.__name__}")
        else:
            check(False, "raises ScopeViolation", "no exception raised — THE WRITE SUCCEEDED")
        check(not victim.exists(), "the refused write left NO file on disk")


# ── T5 ───────────────────────────────────────────────────────────────────────
def t5_static_no_bypass() -> None:
    print("\nT5 — static: no write call in the source bypasses _write()")
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = None
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        if name in {"write_text", "write_bytes"} or (
                name == "open" and any(isinstance(a, ast.Constant)
                                       and isinstance(a.value, str)
                                       and ("w" in a.value or "a" in a.value)
                                       for a in node.args[1:])):
            # permitted only inside _write itself
            offenders.append(f"line {node.lineno}: {name}(...)")
    inside_write = _lines_of_function(tree, "_write")
    real = [o for o in offenders if int(o.split()[1].rstrip(":")) not in inside_write]
    check(not real, "every write call in the module lives inside _write()",
          f"offenders outside _write: {real}")
    check(bool(offenders), "at least one write call was found (the scanner is not vacuous)")


def _lines_of_function(tree: ast.AST, fname: str) -> set[int]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fname:
            return set(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return set()


# ── T6 — the mutation control: prove the checks above CAN fail ───────────────
MUTATION_BYPASS = '''
# ── DELIBERATE MUTATION (test only) — a raw write that bypasses _write() ──
import json as _mj
RESIDUALS_JSON.write_text(_mj.dumps({"mutated": True}, indent=2) + "\\n", encoding="utf-8")
'''

MUTATION_VIA_WRITE = '''
# ── DELIBERATE MUTATION (test only) — an undeclared path routed through _write() ──
_write(RESIDUALS_JSON, "mutated\\n")
'''


def t6_mutation_control() -> None:
    print("\nT6 — MUTATION CONTROL: the detector must go RED on a deliberately broken copy")
    src = GENERATOR.read_text(encoding="utf-8")

    # M1 — a raw write_text that bypasses the guard entirely.
    m1 = src + MUTATION_BYPASS
    rc, out, before, after = run_sandbox(m1)
    m1_runtime_caught = before.get(RESIDUALS_REL) != after.get(RESIDUALS_REL)
    check(m1_runtime_caught,
          "M1 (raw write bypassing _write) is CAUGHT by the byte comparison",
          "the residuals copy was NOT modified — the sandbox check would not have noticed")
    m1_tree = ast.parse(m1)
    m1_offenders = [n for n in ast.walk(m1_tree)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "write_text"
                    and n.lineno not in _lines_of_function(m1_tree, "_write")]
    check(bool(m1_offenders), "M1 is ALSO caught by the static AST scan (T5)",
          "T5 would have stayed green on a bypassing write")

    # M2 — an undeclared path routed through _write(): the guard itself must stop it.
    rc2, out2, before2, after2 = run_sandbox(src + MUTATION_VIA_WRITE)
    check(rc2 != 0, "M2 (undeclared path via _write) makes the generator EXIT NON-ZERO",
          f"rc={rc2}")
    check("ScopeViolation" in out2, "M2 names ScopeViolation in its failure output",
          out2.strip()[-300:])
    check(before2.get(RESIDUALS_REL) == after2.get(RESIDUALS_REL),
          "M2 left the residuals copy untouched (the guard refused before writing)")


# ── T7 — the 15-cell cross-check, with an anchor on EACH side ────────────────
#
# WHY THIS EXISTS
# M0-T63 (SQ-14) replaced a hardcoded "down from 11 in v1.0" with a figure DERIVED from
# per-entry provenance stamps (`origin_bucket()` / `origin_tally()`). Its corroboration was
# that the derivation reproduces, in all 15 bucket cells across the three splits, what
# `_meta.reading_history[0]` recorded at v1.0 write time BY A COMPLETELY DIFFERENT
# MECHANISM — a snapshot taken then, not a reconstruction computed now. M0-T63 then filed
# F-T63-2 against its own work: "the 15/15 cross-check that validates my work HAS NO
# DETECTOR; I ran it by hand." A corroboration nothing re-runs and nothing would notice
# failing is exactly the shape §N.8 exists to refuse. T7 is that detector.
#
# D-89 BINDS THIS TEST DIRECTLY, and it is the part most likely to go wrong. This is a
# two-sided comparison and BOTH sides can evaporate: the stamps can go missing (derived
# side) and `reading_history` can be absent or empty (recorded side). A COMPARISON OF TWO
# EMPTY THINGS PASSES — T8 reproduces exactly that, on purpose, to show what the anchors
# are for. So each side is anchored INDEPENDENTLY, on its SHAPE (three splits × five
# buckets = 15 cells, exact bucket keys, integer cells, split sums equal to the entry
# populations, total = criteria + rules), before a single cell is compared; and T8 proves
# each anchor fires on its own. A single anchor on a two-sided comparison is not a weaker
# version of the right thing — it is a test of one side wearing the costume of a comparison.
SPLITS = ("criteria", "rules", "total")


def origin_side(mod) -> dict:
    """Side A — RECONSTRUCTED NOW from the generator's own per-entry provenance stamps."""
    oc, orr = mod.origin_tally(mod.CRITERIA), mod.origin_tally(mod.RULES)
    return {"criteria": oc, "rules": orr,
            "total": {b: oc.get(b, 0) + orr.get(b, 0) for b in mod.BUCKETS}}


def recorded_side(doc) -> dict | None:
    """Side B — RECORDED THEN by M0-T31: reading 1's own tally, written at v1.0."""
    hist = ((doc.get("_meta") or {}).get("reading_history") or [])
    if not hist:
        return None
    return (hist[0] or {}).get("tally")


def anchor_problems(side, name: str, buckets, n_criteria: int, n_rules: int) -> list[str]:
    """D-89 anchor: what must be TRUE of this side for a comparison to MEAN anything.

    Shape, not truthiness. An empty dict, a missing split, a renamed bucket, a split whose
    cells do not account for every entry, or a total that is not its own two parts, each
    make the 15-cell comparison meaningless rather than merely wrong.
    """
    if not isinstance(side, dict) or not side:
        return [f"{name}: absent or empty ({side!r}) — there is nothing to compare"]
    expected_sum = {"criteria": n_criteria, "rules": n_rules, "total": n_criteria + n_rules}
    problems: list[str] = []
    for split in SPLITS:
        cells = side.get(split)
        if not isinstance(cells, dict) or not cells:
            problems.append(f"{name}.{split}: absent or empty")
        elif set(cells) != set(buckets):
            problems.append(f"{name}.{split}: buckets are {sorted(cells)}, expected {sorted(buckets)}")
        elif any(not isinstance(v, int) or isinstance(v, bool) for v in cells.values()):
            problems.append(f"{name}.{split}: non-integer cell(s) — {cells}")
        elif sum(cells.values()) != expected_sum[split]:
            problems.append(f"{name}.{split}: cells sum to {sum(cells.values())}, expected "
                            f"{expected_sum[split]} (every entry lands in exactly one bucket)")
    if not problems:
        for b in buckets:
            if side["total"][b] != side["criteria"][b] + side["rules"][b]:
                problems.append(f"{name}.total/{b}: {side['total'][b]} is not "
                                f"{side['criteria'][b]} + {side['rules'][b]}")
    return problems


def cell_divergences(a, b, buckets) -> list[str]:
    """The 15 cells themselves. Pure, and DELIBERATELY unanchored — see T8's M5."""
    return [f"{split}/{bucket}: derived={(a.get(split) or {}).get(bucket)} "
            f"recorded={(b.get(split) or {}).get(bucket)}"
            for split in SPLITS for bucket in buckets
            if (a.get(split) or {}).get(bucket) != (b.get(split) or {}).get(bucket)]


def t7_origin_cross_check() -> None:
    print("\nT7 — 15-cell cross-check: origin_tally() reconstruction vs reading_history[0] (F-T63-2)")
    mod = load_generator()
    doc = json.loads((ROOT / OUT_JSON_REL).read_text(encoding="utf-8"))    # READ-ONLY
    n_c, n_r = len(mod.CRITERIA), len(mod.RULES)
    derived, recorded = origin_side(mod), recorded_side(doc)

    pa = anchor_problems(derived, "derived", mod.BUCKETS, n_c, n_r)
    pb = anchor_problems(recorded, "recorded", mod.BUCKETS, n_c, n_r)
    ok_a = check(not pa, f"ANCHOR A — the DERIVED side extracted {len(SPLITS)}×{len(mod.BUCKETS)} "
                         f"well-formed cells over {n_c}+{n_r} entries", "; ".join(pa))
    ok_b = check(not pb, f"ANCHOR B — the RECORDED side (reading_history[0]) extracted "
                         f"{len(SPLITS)}×{len(mod.BUCKETS)} well-formed cells", "; ".join(pb))
    if not (ok_a and ok_b):
        check(False, "T7 — comparison ABANDONED because a side did not extract",
              "D-89: comparing two absent sides passes and proves nothing; the anchor, "
              "not the comparison, is what caught this")
        return

    div = cell_divergences(derived, recorded, mod.BUCKETS)
    check(not div, f"T7 — all {len(SPLITS) * len(mod.BUCKETS)} bucket cells agree: the "
                   "reconstruction from per-entry stamps equals M0-T31's v1.0 snapshot",
          "; ".join(div))
    for split in SPLITS:
        print(f"        {split:>8}: {derived[split]}")

    # The arithmetic M0-T63 reported as "closing unaided": originally-UNEXAMINED minus
    # those since classified must equal what tally() counts today. NOT a tautology — it is
    # false the moment any entry is reclassified INTO UNEXAMINED, which is the movement
    # this register exists to make visible.
    ub = mod.UNEXAMINED
    since = sum(1 for e in mod.CRITERIA + mod.RULES
                if mod.origin_bucket(e) == ub and e["bucket"] != ub)
    live = mod.tally(mod.CRITERIA)[ub] + mod.tally(mod.RULES)[ub]
    check(derived["total"][ub] - since == live,
          "T7b — the arithmetic closes unaided: originally-UNEXAMINED minus since-classified "
          "equals what tally() independently counts today",
          f"{derived['total'][ub]} − {since} = {derived['total'][ub] - since}; "
          f"tally() counts {live}")


# ── T8 — MUTATION CONTROL for T7: prove EACH side's guard fires on its own ───
MUT_ORIGIN_IGNORES_STAMPS = '''
# ── DELIBERATE MUTATION (test only) — origin_bucket() forgets the provenance stamps ──
def origin_bucket(e):
    return e["bucket"]
'''

MUT_ORIGIN_EVAPORATES = '''
# ── DELIBERATE MUTATION (test only) — the derived side extracts NOTHING at all ──
def origin_tally(entries):
    return {}
'''


def t8_cross_check_mutation_control() -> None:
    print("\nT8 — MUTATION CONTROL for T7: each side must turn it RED on its own (D-89)")
    mod = load_generator()
    doc = json.loads((ROOT / OUT_JSON_REL).read_text(encoding="utf-8"))    # READ-ONLY
    n_c, n_r = len(mod.CRITERIA), len(mod.RULES)
    good_a, good_b = origin_side(mod), recorded_side(doc)
    anchor = lambda side, name: anchor_problems(side, name, mod.BUCKETS, n_c, n_r)

    # M3 — WRONG BUT WELL-FORMED, derived side only. Must reach the comparison and fail there.
    m3 = origin_side(load_mutated_generator(MUT_ORIGIN_IGNORES_STAMPS))
    check(not anchor(m3, "derived"),
          "M3 (origin_bucket ignores the stamps) still passes ANCHOR A — a wrong-but-"
          "well-formed side must reach the COMPARISON, not be swallowed by the anchor",
          "; ".join(anchor(m3, "derived")))
    check(bool(cell_divergences(m3, good_b, mod.BUCKETS)),
          "M3 turns T7 RED — the DERIVED side alone is enough to fail the comparison",
          f"{len(cell_divergences(m3, good_b, mod.BUCKETS))} of "
          f"{len(SPLITS) * len(mod.BUCKETS)} cells diverge under M3")

    # M4 — WRONG BUT WELL-FORMED, recorded side only. A unit moved between buckets, so
    # every sum and the total identity still hold: only the comparison can catch this.
    m4 = copy.deepcopy(good_b)
    for split in ("criteria", "total"):
        m4[split][mod.UNEXAMINED] -= 1
        m4[split][mod.REPAIRABLE] += 1
    check(not anchor(m4, "recorded"),
          "M4 (one entry moved between buckets in reading 1) still passes ANCHOR B",
          "; ".join(anchor(m4, "recorded")))
    check(bool(cell_divergences(good_a, m4, mod.BUCKETS)),
          "M4 turns T7 RED — the RECORDED side alone is enough to fail the comparison",
          f"{len(cell_divergences(good_a, m4, mod.BUCKETS))} of "
          f"{len(SPLITS) * len(mod.BUCKETS)} cells diverge under M4")

    # M5 — the DERIVED side EVAPORATES. The comparison cannot catch this; ANCHOR A must.
    m5 = origin_side(load_mutated_generator(MUT_ORIGIN_EVAPORATES))
    check(bool(anchor(m5, "derived")),
          "M5 (origin_tally returns nothing) is caught by ANCHOR A",
          "; ".join(anchor(m5, "derived")) or "NONE — the empty side passed its own anchor")
    check(not anchor(good_b, "recorded"),
          "M5 — and ANCHOR B stayed green, so the failure is attributable to side A alone")
    check(not cell_divergences({}, {}, mod.BUCKETS),
          "M5 — D-89 REPRODUCED: the bare 15-cell comparison of two ABSENT sides is a "
          "VACUOUS PASS; the anchors, not the comparison, are what catch it",
          f"bare comparison of {{}} vs {{}}: "
          f"{len(cell_divergences({}, {}, mod.BUCKETS))} divergences reported")

    # M6 — the RECORDED side EVAPORATES, three ways. ANCHOR B must catch each.
    for label, victim in (("no _meta", {}),
                          ("no reading_history", {"_meta": {}}),
                          ("empty reading_history", {"_meta": {"reading_history": []}}),
                          ("reading 1 carries no tally", {"_meta": {"reading_history": [{}]}})):
        check(bool(anchor(recorded_side(victim), "recorded")),
              f"M6 ({label}) is caught by ANCHOR B",
              "; ".join(anchor(recorded_side(victim), "recorded"))
              or "NONE — the absent side passed its own anchor")
    check(not anchor(good_a, "derived"),
          "M6 — and ANCHOR A stayed green, so the failure is attributable to side B alone")


def main() -> int:
    print("WRITE-SCOPE REGRESSION TEST — m0_deferral_register.py  (M0-T62 / SQ-12 / D-44 part 4)")
    print(f"repo root: {ROOT}")
    t1_declaration()
    t2_t3_real_run()
    t4_write_refuses()
    t5_static_no_bypass()
    t6_mutation_control()
    t7_origin_cross_check()
    t8_cross_check_mutation_control()
    print("\n" + "─" * 78)
    if FAILURES:
        print(f"FAILED — {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  · {f}")
        return 1
    print("ALL CHECKS PASSED. The generator's declared write scope is enforced, the "
          "residuals JSON is untouched by a run, the 15-cell origin cross-check holds "
          "with both sides anchored, and every detector here was shown to go red on a "
          "deliberately broken input — six of them, one-sided, two per side of T7.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
