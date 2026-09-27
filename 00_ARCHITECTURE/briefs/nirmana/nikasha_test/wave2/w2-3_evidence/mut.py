"""Mutation runner. usage: mut.py LABEL SPEC.json TEST_SELECTOR...
SPEC.json: {"old": "...", "new": "..."} — exactly one occurrence in asset_census.py.
Applies, runs the named tests (expects failure), restores byte-identically (md5), re-runs the offline suite."""
import hashlib, json, subprocess, sys, pathlib, datetime
REPO = pathlib.Path("/Users/Dev/madhav-nikasha")
F = REPO / "platform/scripts/governance/asset_census.py"
LOG = pathlib.Path(__file__).parent / "mutation_runs.log"
label, spec_path, *tests = sys.argv[1:]
spec = json.load(open(spec_path))
orig = F.read_bytes(); md5 = hashlib.md5(orig).hexdigest()
src = orig.decode()
n = src.count(spec["old"])
assert n == 1, f"{label}: old occurs {n} times"
F.write_text(src.replace(spec["old"], spec["new"]))
env = dict(**__import__("os").environ); env.pop("PGHOST", None)
r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests], cwd=REPO,
                   capture_output=True, text=True, env=env)
tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED") or " passed" in l or " failed" in l][-12:]
F.write_bytes(orig)
md5b = hashlib.md5(F.read_bytes()).hexdigest()
s = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "platform/scripts/governance/__tests__"],
                   cwd=REPO, capture_output=True, text=True, env=env)
suite = [l for l in s.stdout.splitlines() if " passed" in l][-1:]
with LOG.open("a") as f:
    f.write(f"\n=== {datetime.datetime.now().isoformat(timespec='seconds')} {label}\n")
    f.write(f"mutation: {json.dumps(spec)[:600]}\n")
    f.write(f"named tests: {' '.join(tests)}\n")
    f.write("under mutation (rc=%d):\n  " % r.returncode + "\n  ".join(tail) + "\n")
    f.write(f"reverted: md5 before {md5} after {md5b} -> {'BYTE-IDENTICAL' if md5 == md5b else 'MISMATCH'}\n")
    f.write(f"offline suite after revert: {suite}\n")
print(label, "rc", r.returncode, "|", tail[-1] if tail else "", "| revert", md5 == md5b, "| suite", suite)
