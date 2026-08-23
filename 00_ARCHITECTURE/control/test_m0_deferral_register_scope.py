#!/usr/bin/env python3
"""WRITE-SCOPE REGRESSION TEST for 00_ARCHITECTURE/control/m0_deferral_register.py.

    Run:  python3 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py
    Exit: 0 = all checks passed · 1 = a check failed (details on stdout)

WHY THIS FILE EXISTS
────────────────────
KĀRAKA M0-T62, Standing Queue SQ-12, on ADHIKĀRIN ruling D-44 part 4.

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

SAFETY: nothing here touches the live tree. Every run happens inside a temporary
directory that is a COPY, and the live residuals JSON is only ever READ.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
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


def main() -> int:
    print("WRITE-SCOPE REGRESSION TEST — m0_deferral_register.py  (M0-T62 / SQ-12 / D-44 part 4)")
    print(f"repo root: {ROOT}")
    t1_declaration()
    t2_t3_real_run()
    t4_write_refuses()
    t5_static_no_bypass()
    t6_mutation_control()
    print("\n" + "─" * 78)
    if FAILURES:
        print(f"FAILED — {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  · {f}")
        return 1
    print("ALL CHECKS PASSED. The generator's declared write scope is enforced, the "
          "residuals JSON is untouched by a run, and the detector was shown to go red "
          "on two deliberately broken copies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
