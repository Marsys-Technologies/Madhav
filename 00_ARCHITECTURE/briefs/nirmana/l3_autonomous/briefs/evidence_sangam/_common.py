"""Falsifier harness (v2, post RR-01). Every script states ONE proposition and EXITS NONZERO when it is
contradicted or its evidence is missing. Run with NEG=1 to execute the script's negative control: an
inverted/mutated check that MUST fail — proving the detector can return false. Read-only; no DB; no
writes outside stdout."""
import sys, os, re, pathlib
ROOT = pathlib.Path(__file__).resolve()
while ROOT.name != 'readiness' and ROOT.parent != ROOT: ROOT = ROOT.parent
SIDECAR = ROOT / 'platform' / 'python-sidecar'; sys.path.insert(0, str(SIDECAR))
NEG = os.environ.get('NEG') == '1'
_fails = []
def src(rel): return (SIDECAR / rel).read_text(encoding='utf-8', errors='replace').splitlines()
def grep(rel, pat): return [(i, l) for i, l in enumerate(src(rel), 1) if re.search(pat, l)]
def head(t): print("=" * 78 + f"\n{t}" + ("   [NEGATIVE CONTROL — must FAIL]" if NEG else "") + "\n" + "=" * 78)
def prop(name, cond, detail=""):
    """Assert a named proposition. Records failure; final verdict via done()."""
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond: _fails.append(name)
def done(kind="PRE-FIX DEFECT PRESENT"):
    """kind: what a PASS means — 'PRE-FIX DEFECT PRESENT' (baseline evidence) or 'POST-FIX BEHAVIOUR'."""
    if _fails:
        print(f"VERDICT: FAIL ({len(_fails)} proposition(s) contradicted: {', '.join(_fails)})"); sys.exit(1)
    print(f"VERDICT: PASS — {kind}"); sys.exit(0)
