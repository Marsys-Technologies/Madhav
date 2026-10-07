#!/usr/bin/env bash
# B-0 — verify the pinned plan documents against the sha256 values in the charter frontmatter. Writes run/SPEC_HASHES_OK on
# success (the detector of B-0) and exits 1 on any mismatch or missing file (the one failure that stops a launch).
set -euo pipefail
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; CAMP="$KY_ROOT/wt/campaign"; mkdir -p "$KY_ROOT/run"
/opt/homebrew/bin/python3 - "$CAMP" "$KY_ROOT/run/SPEC_HASHES_OK" <<'PYEOF'
import hashlib, pathlib, re, subprocess, sys, time
camp, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
charter = (camp / "00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md").read_text()
front = charter.split("\n---\n", 1)[0]
pins = re.findall(r"(00_ARCHITECTURE/\S+\.md) \(sha256 ([0-9a-f]{64})\)", front)
assert len(pins) == 5, f"expected 5 pinned documents in the charter frontmatter, found {len(pins)}"
rows, bad = [], 0
for path, want in pins:
    f = camp / path
    have = hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else "MISSING"
    ok = have == want; bad += (not ok)
    rows.append(f"{'OK ' if ok else 'BAD'}  {path}\n     pinned {want}\n     found  {have}")
print("\n".join(rows))
if bad:
    out.unlink(missing_ok=True); print(f"\nSPEC HASHES: {bad} MISMATCH — the campaign does not launch on unverified specifications"); sys.exit(1)
head = subprocess.run(["git", "-C", str(camp), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
out.write_text(f"verified {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} at {head}\n\n" + "\n".join(rows) + "\n")
print(f"\nSPEC HASHES OK → {out}")
PYEOF
