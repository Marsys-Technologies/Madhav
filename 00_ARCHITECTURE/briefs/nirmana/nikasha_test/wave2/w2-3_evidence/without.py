"""usage: without.py LABEL REV TEST_SELECTOR... — run tests with asset_census.py at REV, then restore."""
import hashlib, subprocess, sys, pathlib, datetime, os
REPO = pathlib.Path("/Users/Dev/madhav-nikasha")
F = REPO / "platform/scripts/governance/asset_census.py"
LOG = pathlib.Path(__file__).parent / "mutation_runs.log"
label, rev, *tests = sys.argv[1:]
orig = F.read_bytes(); md5 = hashlib.md5(orig).hexdigest()
F.write_bytes(subprocess.run(["git", "show", f"{rev}:platform/scripts/governance/asset_census.py"], cwd=REPO,
                             capture_output=True, check=True).stdout)
env = dict(os.environ); env.pop("PGHOST", None)
r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests], cwd=REPO,
                   capture_output=True, text=True, env=env)
tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED") or l.startswith("ERROR") or " passed" in l or " failed" in l][-14:]
F.write_bytes(orig)
ok = hashlib.md5(F.read_bytes()).hexdigest() == md5
with LOG.open("a") as f:
    f.write(f"\n=== {datetime.datetime.now().isoformat(timespec='seconds')} {label} (WITHOUT the change: asset_census.py at {rev})\n")
    f.write(f"named tests: {' '.join(tests)}\n  " + "\n  ".join(tail) + f"\nrestored byte-identical: {ok}\n")
print(label, "rc", r.returncode, "|", tail[-1] if tail else "", "| restored", ok)
