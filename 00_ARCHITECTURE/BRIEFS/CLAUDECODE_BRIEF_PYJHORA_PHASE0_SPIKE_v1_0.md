---
brief_id: PYJHORA_PHASE0_SPIKE_v1_0
status: ACTIVE
authored_by: Cowork (planning)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-06-01
model_directive: Use Gemini Pro or DeepSeek. Anthropic banned per native standing order.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (single checkout — research spike)
work_branch: none (the spike directory is gitignored; report committed at end on a small docs PR)
estimated_loc: ~250 LOC across 6 spike files + 1 report
estimated_wallclock: 4-8 hours
---

# CLAUDECODE_BRIEF — PyJHora Phase 0 Verification Spike

## Why

Before any architecture commitment to PyJHora (forking it, integrating it,
or building an adapter layer), five facts must be verified empirically:

1. **License** — sources conflict between MIT and AGPL. AGPL has SaaS
   source-disclosure implications for a hosted MARSYS.
2. **Headless imports** — `jhora.panchanga.*` and `jhora.horoscope.chart.*`
   must import cleanly without PyQt6 / without DISPLAY. If they don't,
   the fork-and-strip approach is required.
3. **Multi-ayanamsha isolation** — `drik.set_ayanamsa_mode()` is package-global.
   `multiprocessing.Pool` isolation must work; threading.Lock serializes
   and is too slow.
4. **Output shapes** — PyJHora returns heterogeneous shapes (tuples, indices,
   localized strings). Each function we'd call needs its shape captured so
   the adapter layer can be sized.
5. **Spot-comparison vs natal_engine** — PyJHora's planet positions should
   agree with the existing `natal_engine.positions` to arc-second level
   for the same inputs (both call pyswisseph underneath). Material divergence
   means something is configured differently and needs investigation.

This spike answers all five with empirical data. Output: a single report
file the operator can read in ≤10 minutes to make the integration decision.

## Scope

`may_touch` (all under a gitignored spike directory):
- `platform/python-sidecar/spikes/pyjhora_phase0/` (NEW directory, gitignored)
- `00_ARCHITECTURE/PYJHORA_SPIKE_REPORT_v1_0.md` (NEW — committed at end)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_PHASE0_SPIKE_v1_0.md` (THIS file — append §6 evidence at end)

`must_not_touch`:
- `platform/python-sidecar/natal_engine/**` (read-only for comparison)
- `platform/python-sidecar/pipeline/**`
- `requirements.txt` (the spike uses its own venv, not the project's)
- Any application code
- Anything under `00_ARCHITECTURE/PARIKSHA/` or `00_ARCHITECTURE/CONDUCTOR/`
- Production DB

## Hard gates

- NO Anthropic models.
- NO modifying application code under any path other than the spike directory + the report file.
- NO `pip install` into the project's existing venv. Spike uses its own venv.
- NO requirement that the spike succeeds end-to-end — failures are FINDINGS.
  Report all failures honestly; don't paper over them.
- NO production calls. Pure local computation.
- NO commit of the spike directory contents to git. Spike artifacts are
  ephemeral (in .gitignore). Only the report is committed.

## §1 — Pre-flight: spike directory + venv

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin && git checkout main && git pull origin main

# Spike branch (just for the report PR at the end)
git checkout -b spike/pyjhora-phase0

mkdir -p platform/python-sidecar/spikes/pyjhora_phase0
cd platform/python-sidecar/spikes/pyjhora_phase0

# Add to gitignore at the spike directory level
cat > .gitignore <<'EOF'
*
!.gitignore
!*.py
!README.md
!*.txt
venv/
__pycache__/
*.pyc
output/
EOF

# Clean venv, isolated from project's
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

## §2 — License verification (the gating check)

```bash
# Method 1: clone repo, read LICENSE
cd /tmp
git clone --depth=1 https://github.com/naturalstupid/PyJHora.git pyjhora-license-check
cat pyjhora-license-check/LICENSE 2>&1 | head -30 || echo "LICENSE file not at root; search:"
find pyjhora-license-check -iname "LICENSE*" -o -iname "COPYING*" 2>/dev/null
rm -rf pyjhora-license-check

# Method 2: pip metadata
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/spikes/pyjhora_phase0
source venv/bin/activate
pip install PyJHora==3.9.3 --no-deps 2>&1 | tail -5
pip show PyJHora 2>&1 | grep -iE "license|home-page|author"

# Method 3: PyPI metadata via Python
python -c "
import importlib.metadata
m = importlib.metadata.metadata('PyJHora')
for k in ['License', 'License-Expression', 'License-File', 'Classifier', 'Home-page']:
    print(f'{k}: {m.get(k, \"(not set)\")}')
print()
print('Classifiers:')
for c in m.get_all('Classifier') or []:
    if 'License' in c:
        print(f'  {c}')
"
```

Write findings to `output/license_check.md` per template:

```markdown
# License verdict
LICENSE file contents (first 5 lines):
<verbatim>

pip metadata License field: <verbatim>
PyPI License classifier: <verbatim>

Verdict: <MIT | AGPL | Apache | Other>
SaaS implications: <none | source disclosure required | other>
Recommendation: <safe to adopt | requires legal review | reject>
```

**If verdict is AGPL or anything requiring legal review: halt the spike here.**
Write the report and exit. Do not run §3-§7. Operator decides whether to
proceed.

## §3 — Headless import verification

Goal: prove the calculation modules import cleanly without PyQt6 / without
a display.

```bash
cd platform/python-sidecar/spikes/pyjhora_phase0
source venv/bin/activate
pip install pyswisseph==2.10.3.2

# Confirm PyQt6 is NOT installed
pip list 2>&1 | grep -i pyqt && echo "PyQt6 IS installed" || echo "PyQt6 NOT installed"

# Try the calculation imports
unset DISPLAY
QT_QPA_PLATFORM=offscreen python -c "
import sys
print(f'Python: {sys.version}')
print(f'DISPLAY: {sys.modules.get(\"os\", __import__(\"os\")).environ.get(\"DISPLAY\", \"unset\")}')
print()

print('Trying jhora.panchanga.drik...')
from jhora.panchanga import drik
print('  OK')

print('Trying jhora.horoscope.chart.charts...')
from jhora.horoscope.chart import charts
print('  OK')

print('Trying jhora.horoscope.chart.house...')
from jhora.horoscope.chart import house
print('  OK')

print('Trying jhora.horoscope.chart.dhasa...')
from jhora.horoscope.chart import dhasa
print('  OK')

print('Trying jhora.horoscope.chart.strength...')
from jhora.horoscope.chart import strength
print('  OK')

print('Trying jhora.horoscope.chart.yoga...')
from jhora.horoscope.chart import yoga
print('  OK')

# Check that PyQt6 was NOT pulled in transitively
print()
qt_loaded = any('Qt' in m or 'PyQt' in m for m in sys.modules.keys())
print(f'Qt/PyQt6 loaded in sys.modules: {qt_loaded}')
" 2>&1 | tee output/headless_imports.log
```

Record findings:
- If all 6 imports succeed AND `Qt/PyQt6 loaded: False` → **clean headless mode works without PyQt6**
- If any import fails with "No module named PyQt6" → need to either install PyQt6 OR fork-and-strip
- If imports succeed but `Qt/PyQt6 loaded: True` → PyJHora eagerly imports Qt somewhere; fork-and-strip is mandatory

## §4 — Multi-ayanamsha isolation test

Goal: confirm subprocess-per-ayanamsha pattern works cleanly.

Write `multi_ayanamsha_test.py`:

```python
"""Verify multiprocessing isolation for PyJHora's global ayanamsha state."""
import os, json
from multiprocessing import Pool

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

NATIVE = {
    'chart_id': '362f9f17-95a5-490b-a5a7-027d3e0efda0',
    'birth_date': '1984-02-05',
    'birth_time': '10:43:00',
    'latitude': 20.2960,
    'longitude': 85.8246,
    'tz_offset': 5.5,
}

AYANAMSHAS = ['LAHIRI', 'KRISHNAMURTI', 'RAMAN', 'TRUE_CITRA', 'SURYA_SIDDHANTA']

def compute_for_ayanamsha(ayanamsha_name):
    from jhora.panchanga import drik
    drik.set_ayanamsa_mode(ayanamsha_name)
    # Compute the Moon's sidereal longitude as the canary value
    # Each ayanamsha should produce a DIFFERENT value for the same native birth.
    place = (NATIVE['latitude'], NATIVE['longitude'], NATIVE['tz_offset'])
    jd = drik.julian_day_number(NATIVE['birth_date'], NATIVE['birth_time'])
    # Adapt to PyJHora's actual API for sidereal_longitude
    # See PyJHora README for exact signature; fall back to inspect if uncertain.
    moon_lon = drik.sidereal_longitude(jd, 1)  # 1 = Moon in PyJHora's planet index
    return {
        'ayanamsha': ayanamsha_name,
        'moon_sidereal_longitude': moon_lon,
        'pid': os.getpid(),
    }

if __name__ == '__main__':
    # Test 1: sequential in one process — confirms ayanamsha switching works
    print('=== Sequential test ===')
    seq_results = [compute_for_ayanamsha(a) for a in AYANAMSHAS]
    for r in seq_results:
        print(f'  {r}')

    # Test 2: multiprocessing.Pool — confirms each subprocess has its own state
    print()
    print('=== Multiprocessing test ===')
    with Pool(processes=5) as pool:
        mp_results = pool.map(compute_for_ayanamsha, AYANAMSHAS)
    for r in mp_results:
        print(f'  {r}')

    # Test 3: did each subprocess actually get a different PID?
    print()
    print('=== Isolation verification ===')
    pids = set(r['pid'] for r in mp_results)
    print(f'  Distinct PIDs across 5 subprocesses: {len(pids)}')
    print(f'  Expected: 5 distinct PIDs (with Pool of 5 processes)')

    # Test 4: did each ayanamsha produce a different Moon longitude?
    longs = set(round(r['moon_sidereal_longitude'], 6) for r in mp_results)
    print(f'  Distinct Moon longitudes across 5 ayanamshas: {len(longs)}')
    print(f'  Expected: 5 distinct values (each ayanamsha has its own offset)')

    # Persist findings
    output = {
        'sequential': seq_results,
        'multiprocessing': mp_results,
        'distinct_pids': len(pids),
        'distinct_longitudes': len(longs),
        'isolation_pass': len(pids) == 5 and len(longs) == 5,
    }
    with open('output/multi_ayanamsha_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print()
    print(f'Isolation PASS: {output["isolation_pass"]}')
```

Run and capture:
```bash
mkdir -p output
python multi_ayanamsha_test.py 2>&1 | tee output/multi_ayanamsha.log
```

Findings:
- 5 distinct PIDs + 5 distinct longitudes = **multiprocessing isolation works**
- 5 distinct PIDs + <5 longitudes = state leaking via shared file/cache (investigate)
- <5 PIDs = Pool fell back to fewer processes; investigate
- Import errors = adjust API usage per PyJHora's actual signatures

If PyJHora's actual `drik.sidereal_longitude` signature differs from the assumed one, adjust based on:
- `python -c "from jhora.panchanga import drik; help(drik.sidereal_longitude)"`
- Or read the source: `python -c "import inspect; from jhora.panchanga import drik; print(inspect.getsourcefile(drik))"` and grep the file

## §5 — Output-shape inventory

For 6 candidate functions PyJHora would replace in the natal_engine, run each
once for the native's chart (Lahiri ayanamsha) and capture the return type
+ shape. Don't interpret the values; just record what comes back.

Functions to probe (adjust signatures per actual PyJHora API):

| Module | Function | Replaces |
|---|---|---|
| `jhora.panchanga.drik` | `sidereal_longitude(jd, planet_id)` | natal_engine.positions |
| `jhora.horoscope.chart.house` | `bhava_madhya_points(...)` or equivalent | natal_engine.houses |
| `jhora.horoscope.chart.charts` | `divisional_chart(...)` for D1 | natal_engine.vargas |
| `jhora.horoscope.chart.dhasa` | `vimsottari_dhasa(...)` | natal_engine.dashas |
| `jhora.horoscope.chart.strength` | `shadbala(...)` | currently writer-side |
| `jhora.panchanga.drik` | `tithi(...)`, `yogam(...)`, `karanam(...)` | natal_engine.panchanga |

For each, write to `output/shape_inventory.json`:
```json
{
  "function": "jhora.panchanga.drik.sidereal_longitude",
  "args": [...],
  "return_type": "float",
  "return_shape": "scalar",
  "sample_value": 12.345,
  "exceptions_raised": null
}
```

If a function's signature isn't clear: use `inspect.signature()`. If it raises:
record the exception and move to the next. Don't try to fix PyJHora; just inventory.

## §6 — Spot-comparison vs existing natal_engine

Pick 3 deterministic invariants and verify PyJHora agrees with natal_engine:

1. **Sun's sidereal longitude for native at Lahiri** — both engines call pyswisseph
2. **Moon's nakshatra index for native at Lahiri** — derivable from longitude
3. **Ascendant degree for native at Lahiri** — both engines compute this

```python
# In the spike venv, import BOTH and compare
import sys
sys.path.insert(0, '/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar')

# natal_engine (the project's existing code)
from natal_engine.positions import ...  # adjust to actual API

# PyJHora
from jhora.panchanga import drik

# For each invariant, compute both, diff
```

If agreement is to arc-second level (< 0.001°): the two engines are
consistent — both Swiss Ephemeris underneath, no surprise.

If material divergence (> 0.01°): something is configured differently
(ayanamsha pinning, MEAN_NODE vs TRUE_NODE for Rahu, ephemeris mode).
Document the divergence; don't try to fix in the spike.

## §7 — Write the spike report

`00_ARCHITECTURE/PYJHORA_SPIKE_REPORT_v1_0.md`:

```markdown
---
artifact: PYJHORA_SPIKE_REPORT_v1_0.md
version: 1.0
status: COMPLETE
authored_by: Phase 0 spike executor
authored_at: <ISO>
covers: PyJHora 3.9.3 (April 2026)
---

# PyJHora Phase 0 Spike Report

## Executive verdict

License:                       <MIT | AGPL | other>
Headless imports clean:        <YES | NO — reason>
Multi-ayanamsha isolation:     <YES — subprocess pattern works | NO — reason>
Output shapes captured:        <N functions inventoried>
Agreement with natal_engine:   <PASS within arc-second | DIVERGENT — details>

Recommendation: <ADOPT | ADOPT WITH FORK-AND-STRIP | REJECT — reason>

## Detailed findings

### License
<verbatim LICENSE file content, pip metadata, classifiers>

### Headless imports
<which 6 modules imported cleanly; sys.modules check for PyQt6>

### Multi-ayanamsha
<5 PIDs / 5 longitudes results from §4>

### Shape inventory
<table of the 6 functions × return type/shape>

### Spot-comparison
<table of 3 invariants: natal_engine value vs PyJHora value vs delta>

## Surprises and gotchas
<anything unexpected that hit during the spike>

## Recommended next step
<one paragraph: what the operator should do based on the verdict>
```

## §8 — Commit the report + close

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add 00_ARCHITECTURE/PYJHORA_SPIKE_REPORT_v1_0.md
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_PHASE0_SPIKE_v1_0.md
git status   # should NOT show platform/python-sidecar/spikes/ (gitignored)

git commit -m "spike(pyjhora): Phase 0 verification report

Five facts verified empirically before any PyJHora architecture commit:
  1. License: <verdict>
  2. Headless imports: <YES/NO>
  3. Multi-ayanamsha subprocess isolation: <YES/NO>
  4. Output shapes inventoried for 6 candidate functions
  5. Spot-comparison vs natal_engine: <agreement | divergence>

Recommendation: <ADOPT | ADOPT WITH FORK-AND-STRIP | REJECT>

Spike directory (platform/python-sidecar/spikes/pyjhora_phase0/) is
gitignored — ephemeral. Only the report is committed.

Brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_PHASE0_SPIKE_v1_0.md
Report: 00_ARCHITECTURE/PYJHORA_SPIKE_REPORT_v1_0.md"

git push -u origin spike/pyjhora-phase0

gh pr create --base main --head spike/pyjhora-phase0 \
  --title "spike(pyjhora): Phase 0 verification report" \
  --body "$(git log -1 --format=%B)"
```

## Acceptance criteria

- [ ] License verdict captured (verbatim + interpretation)
- [ ] Headless import test ran; result recorded
- [ ] Multi-ayanamsha test ran with 5 subprocesses; isolation verdict recorded
- [ ] Shape inventory captured for ≥4 of the 6 candidate functions (some may have unclear APIs — that itself is a finding)
- [ ] Spot-comparison ran for ≥1 invariant; agreement or divergence recorded
- [ ] `PYJHORA_SPIKE_REPORT_v1_0.md` written with the executive verdict block
- [ ] PR opened; spike directory not in the commit

## Hard gates (restate)

- NO Anthropic models.
- NO modifying application code outside the spike directory + report.
- NO production calls.
- NO papering over failures — failures are findings.
- If license check returns AGPL or unclear: HALT after §2; write the partial
  report; do not run §3-§7. Operator decides whether to proceed.

---

End of brief.
