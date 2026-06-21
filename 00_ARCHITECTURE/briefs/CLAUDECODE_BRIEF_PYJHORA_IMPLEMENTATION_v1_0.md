---
artifact: CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md
brief_id: PYJHORA_IMPLEMENTATION
version: 1.0
status: ACTIVE
authored_at: 2026-06-01
authored_by: cowork-planner
authority: native_decision_2026-06-01
supersedes: CLAUDECODE_BRIEF_PYJHORA_PHASE0_SPIKE_v1_0.md (skipped — native declined spike)
implements: PyJHora as the sole chart-fact engine
implementation_surface: Claude Code in Google Antigravity IDE
human_gate: PR-to-main only. No prod deploy. No prod DB ops. No flag flips. No secret rotations.
may_touch:
  - platform/python-sidecar/requirements.txt
  - platform/python-sidecar/Dockerfile
  - platform/python-sidecar/pyjhora_adapter/         (CREATE)
  - platform/python-sidecar/pipeline/writers/*.py
  - platform/python-sidecar/pipeline/dispatcher.py
  - platform/python-sidecar/natal_engine/            (DELETE entire tree)
  - platform/python-sidecar/tests/test_pyjhora_adapter/  (CREATE)
  - 00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE.md
  - 00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE.md
  - 00_ARCHITECTURE/PLATFORM_MODERNIZATION_*.md      (architecture refresh only)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
must_not_touch:
  - src/                                              (frontend — out of scope)
  - platform/supabase/migrations/                     (no schema change in this PR)
  - platform/scripts/                                 (no infra change)
  - 00_ARCHITECTURE/PARIKSHA/                         (separate workstream)
  - any node_modules/, .next/, dist/
prime_directive: only computed facts. no narrative, no opinion, no judgement.
hard_bans:
  - No Anthropic models (native standing order)
  - No JH-parity test. Internal-consistency verification only
  - No `jh_oracle*`, `test_jh_parity*` references in NEW code
  - No production deploy
  - No `gcloud` commands
---

# PyJHora Implementation — direct replacement of `natal_engine/`

## Why this brief exists

Native has decided: **PyJHora is the sole chart-fact engine.** The existing
`natal_engine/` package (pyswisseph wrapper authored in BRIEF_1_1) is replaced
in this PR. No parallel run. No spike. No license gating (native's call).
No JH-parity oracle (per [[no-jh-parity-anywhere]]).

Verification is exclusively internal-consistency: row counts vs spec,
schema compliance, structural invariants, cross-asset FK integrity,
layer-completion gates, determinism (rebuild = byte-identical).

## Decisions (locked, do not re-negotiate)

| Question | Answer | Why |
|---|---|---|
| Engine | PyJHora | Native decision |
| Install method | `pip install PyJHora` | Direct, no fork |
| PyQt6 dependency | Allow at install, never import at runtime | Calculation modules don't need it |
| Replace `natal_engine/`? | Yes, in this PR | Clean cut |
| Parallel run? | No | Single source of truth |
| License check? | Skipped (native) | Not blocking |
| Spike? | Skipped (native) | Empirical discovery happens inline |
| Verification oracle? | Internal consistency only | [[no-jh-parity-anywhere]] |

## Scope — what ships in this PR

### Phase 1 · Dependency in place

1. Add `PyJHora` to `platform/python-sidecar/requirements.txt` (pin to a specific version — pick the latest stable PyJHora release at time of execution; record the exact version in the PR description).
2. Modify `platform/python-sidecar/Dockerfile`:
   - Install PyJHora.
   - **Do not** install system Qt6 libraries. We tolerate PyJHora's import-time PyQt6 reference because we never invoke the GUI modules. If import fails because PyQt6 can't initialise headlessly, add `QT_QPA_PLATFORM=offscreen` env var; if that still fails, lazy-import PyJHora's calculation submodules directly (`from jhora.panchanga import drik` etc., never `import jhora`).
   - Confirm container builds.

**Acceptance:** `docker build` succeeds locally and in CI. A one-liner test
inside the container — `python -c "from jhora.panchanga import drik; print(drik.__file__)"` — prints a path.

### Phase 2 · Adapter layer

Create `platform/python-sidecar/pyjhora_adapter/` with these modules. **Every
adapter function is typed (mypy strict) and returns plain Python primitives or
TypedDicts — never PyJHora's internal classes.** Numerics are `Decimal` or
integer arc-seconds where appropriate; never bare floats for chart facts.

```
pyjhora_adapter/
├── __init__.py            — re-exports
├── _ayanamsha.py          — set/reset PyJHora ayanamsha within a subprocess
├── _isolation.py          — multiprocessing.Pool(5) helper for parallel ayanamshas
├── positions.py           — planet ecliptic longitudes (9 grahas + 6 upagrahas)
├── houses.py              — Lagna + 12 cusps (Placidus default; KP-specific overrides per asset)
├── dignities.py           — exaltation/debilitation/mooltrikona/own-sign/etc.
├── vargas.py              — D1..D60 (Parashara + 16-varga set)
├── dashas.py              — Vimshottari + Yogini + Chara (Jaimini) + Kalachakra
├── panchanga.py           — tithi/vara/nakshatra/yoga/karana + sub-units
├── strength.py            — Shadbala (six-fold strength) + Bhava Bala + Ashtakavarga
├── sensitive_points.py    — Gulika/Mandi/Maandi + arudha pada + upagrahas
├── yogas.py               — classical yoga detection
├── transits.py            — current transit positions + aspect calc
└── reconciliation.py      — Lagna ↔ house-1 sign consistency + Rahu/Ketu 180° check
```

Each module exposes one or two top-level functions. Examples:

```python
# positions.py
def planet_positions(
    jd_ut: Decimal,            # Julian Day, UT
    ayanamsha_id: str,         # "lahiri" | "true_chitra" | "kp" | "raman" | "surya_siddhanta"
) -> PlanetPositions: ...

class PlanetPositions(TypedDict):
    sun:     PlanetState
    moon:    PlanetState
    mars:    PlanetState
    mercury: PlanetState
    jupiter: PlanetState
    venus:   PlanetState
    saturn:  PlanetState
    rahu:    PlanetState     # always Mean Node — explicit
    ketu:    PlanetState
    uranus:  PlanetState | None    # only if PyJHora returns it
    # ...

class PlanetState(TypedDict):
    longitude_arcsec: int            # integer arc-seconds, sidereal
    latitude_arcsec:  int
    speed_arcsec_per_day: int
    sign: Literal["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
    sign_lord: str
    nakshatra: str
    nakshatra_pada: Literal[1, 2, 3, 4]
    nakshatra_lord: str
    retrograde: bool
    combust: bool
```

**Adapter rules:**
- One PyJHora function per adapter function. No bundling.
- The adapter NEVER mutates global PyJHora state in a long-lived process —
  every ayanamsha change happens inside a child subprocess via `_isolation.py`.
- If a PyJHora function returns localized strings (e.g. nakshatra names in
  Devanagari), normalise to the canonical IAST/ASCII form used in the corpus.
- If a PyJHora function has under-documented return shape, the adapter
  authors a unit test that asserts the observed shape (this is the empirical
  discovery substitute for the deleted spike).
- For Tier-3 derived quantities (Shadbala, Ashtakavarga, etc.) there is no
  independent oracle. The adapter test asserts internal arithmetic only
  (e.g. Shadbala virupa column sums to total within rounding).

### Phase 3 · Multi-ayanamsha parallelism

`_isolation.py`:

```python
from multiprocessing import Pool

AYANAMSHAS = ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]

def per_ayanamsha(fn, jd_ut, **kwargs):
    """Run `fn(jd_ut, ayanamsha_id=..., **kwargs)` for all 5 ayanamshas
       in parallel subprocesses. Returns {ayanamsha_id: result}."""
    with Pool(processes=5) as pool:
        results = pool.starmap(
            fn,
            [(jd_ut, ayn, kwargs) for ayn in AYANAMSHAS],
        )
    return dict(zip(AYANAMSHAS, results))
```

Every writer that produces per-ayanamsha rows calls `per_ayanamsha(...)`
once and gets 5 results. Single global state per subprocess; clean teardown.

**Acceptance test:** `tests/test_pyjhora_adapter/test_isolation.py` runs
`planet_positions` for all 5 ayanamshas in parallel and asserts the Sun's
sidereal longitude differs between ayanamshas by the expected ayanamsha delta
(arithmetic relationship, no external oracle).

### Phase 4 · Writer rewiring

For every L1 writer in `platform/python-sidecar/pipeline/writers/`, replace
`from natal_engine.* import ...` with `from pyjhora_adapter.* import ...`.

Writers to rewire (matches BUILD_DAG):

```
forensic_writer.py        (CURRENTLY STUB — primary target)
panchanga_writer.py
positions_writer.py
houses_writer.py
dignities_writer.py
vargas_writer.py
dashas_writer.py
sensitive_points_writer.py
l25_builder.py            (depends on L1 outputs only — adapter calls
                           are read-only from chart_facts after L1)
```

Each writer follows the pattern:

```python
from pyjhora_adapter._isolation import per_ayanamsha
from pyjhora_adapter.positions import planet_positions

def write(chart_id, build_id, jd_ut):
    by_ayn = per_ayanamsha(planet_positions, jd_ut)
    rows = []
    for ayn, positions in by_ayn.items():
        for graha, state in positions.items():
            rows.append({
                "chart_id":    chart_id,
                "build_id":    build_id,
                "ayanamsha_id": ayn,
                "graha":       graha,
                "longitude_arcsec": state["longitude_arcsec"],
                # ...
            })
    upsert_rows("chart_facts", rows)
```

**Idempotency:** writers MUST check the actual write target (lesson
[[idempotency-guard-checks-write-target]]) — verify
`chart_facts WHERE chart_id=... AND ayanamsha_id=... AND build_id=...` before
re-inserting.

### Phase 5 · Delete `natal_engine/`

After every writer compiles against the adapter and every test passes:

```
git rm -r platform/python-sidecar/natal_engine/
```

Hard-delete. No deprecation window. No fallback flag.

Also delete (per [[no-jh-parity-anywhere]]):

```
git rm platform/python-sidecar/natal_engine/tests/test_jh_parity.py
git rm platform/python-sidecar/natal_engine/fixtures/jh_oracle.json
git rm platform/python-sidecar/natal_engine/fixtures/jh_oracle_loader.py
git rm platform/python-sidecar/natal_engine/fixtures/jh_oracle_schema.json
```

(These are under `natal_engine/` so the directory delete catches them. Listed
here only for explicit audit trail in the PR description.)

Run `grep -rn "natal_engine" platform/ src/` — must return zero hits.

Run `grep -rn "jh_parity\|jh_oracle\|JHORA_TRANSCRIPTION" platform/ src/` —
must return zero hits in code paths. (Hits in `00_ARCHITECTURE/` governance
audit trail are allowed; flag those for a follow-up cleanup arc.)

### Phase 6 · Architecture-doc refresh

Update these to describe the PyJHora-direct architecture and drop
`pyswisseph + natal_engine + PyJHora` framing:

- `00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE.md`
- `00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE.md`
- `00_ARCHITECTURE/PLATFORM_MODERNIZATION_*.md` (architecture sections only)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (bump revision; note PyJHora as engine)

Edits are minimal — the architecture *intent* always was PyJHora. We're
realigning the docs with what we're actually shipping.

### Phase 7 · End-to-end native chart

Run the native chart (`362f9f17-95a5-490b-a5a7-027d3e0efda0`) through the
new engine end-to-end against the local Cloud SQL Auth Proxy:

```bash
# 1. Start proxy
./platform/scripts/start_db_proxy.sh

# 2. Kick a build (uses existing /api/builds/start endpoint locally)
curl -X POST http://localhost:3000/api/builds/start \
  -H 'Cookie: __session=<minted>' \
  -d '{"chart_id":"362f9f17-95a5-490b-a5a7-027d3e0efda0"}'

# 3. Wait for build_complete
# 4. Query chart_facts and assert non-zero rows for each (asset × ayanamsha)
psql "$DB_URL" -c "
  SELECT asset_id, ayanamsha_id, COUNT(*)
    FROM chart_facts
   WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
     AND build_id = (SELECT MAX(build_id) FROM builds WHERE chart_id = '362f...')
   GROUP BY 1, 2
   ORDER BY 1, 2;
"
```

**Acceptance:** every (asset × ayanamsha) row has count > 0. None are
suspiciously low. forensic_writer no longer returns the 0-row stub state.

## Acceptance criteria (the whole brief)

A PR is mergeable when ALL of these are green:

1. `docker build` for `platform/python-sidecar/` passes.
2. `pytest platform/python-sidecar/tests/test_pyjhora_adapter/` passes
   (every adapter module has at least one test).
3. `pytest platform/python-sidecar/tests/` overall passes (writer tests
   re-pointed at adapter mocks).
4. `grep -rn "natal_engine" platform/ src/` → 0 hits.
5. `grep -rn "jh_parity\|jh_oracle" platform/ src/` → 0 hits in code paths.
6. Local end-to-end run on native chart: every (asset × ayanamsha) has
   `COUNT(*) > 0` in chart_facts.
7. Determinism: running Phase 7 twice with the same `chart_id` produces
   identical `md5(chart_facts)` for the asset-row payloads (excluding
   `build_id`, `created_at`).
8. PR description documents the exact PyJHora version pinned, the headless
   import strategy that worked (env var vs lazy import), and the architecture
   doc diff summary.

## Out of scope (explicit non-goals)

- JH-parity oracle. Will not be added.
- Spike of any kind.
- License check. Native's call.
- Schema migrations.
- Frontend changes.
- Pariksha integration (separate workstream).
- Cleanup of governance-doc references to natal_engine/jh-parity — separate cleanup arc.
- Renderer (R7 from [[FACT_ENGINE_BRIEF_REVIEW]]) — defer to a follow-on PR.
- L1.md regeneration. The chart_facts DB rows are the source of truth.

## Execution sequencing (Antigravity executor)

This is one autonomous arc, one PR, ~1 day of executor work.

```
Step 1  — branch:        git checkout -b feature/pyjhora-direct-engine
Step 2  — Phase 1 (deps): edit requirements.txt + Dockerfile; docker build
Step 3  — Phase 2 (adapter scaffolding): create empty modules + __init__
Step 4  — Phase 3 (isolation): _ayanamsha.py + _isolation.py + their tests
Step 5  — Phase 2 (positions.py + houses.py + tests)
Step 6  — Phase 2 (dignities, vargas, dashas + tests)
Step 7  — Phase 2 (panchanga, strength, sensitive_points, yogas + tests)
Step 8  — Phase 4 (writer rewire): one writer at a time, test each
Step 9  — Phase 5 (delete natal_engine/): only after every writer passes
Step 10 — Phase 7 (native chart e2e): proxy + build + verify
Step 11 — Phase 6 (arch docs): minimal diff to match shipped reality
Step 12 — open PR with all 8 acceptance criteria checked
HALT — native reviews and merges
```

## What goes wrong (failure modes)

- **PyJHora's PyQt6 init fails headlessly.** Try `QT_QPA_PLATFORM=offscreen`
  first; if that doesn't work, lazy-import the calculation submodules
  directly (never `import jhora` at top level). Document in PR description.
- **A PyJHora function returns localised Devanagari names.** Normalise
  inside the adapter to canonical IAST (the corpus standard). Don't push
  this responsibility into writers.
- **A PyJHora function's docstring lies about return shape.** Trust the
  empirical observation (adapter test). Document the actual shape.
- **An ayanamsha differs by more than the expected delta from another.**
  PyJHora is authoritative per native directive. The adapter records the
  value; verification is internal-arithmetic only (does the longitude +
  ayanamsha offset = tropical longitude?).
- **A writer produces zero rows after rewire.** Hard fail. Halt the build,
  surface a clear error to the cockpit. Do not silently skip.
- **`multiprocessing.Pool` deadlocks** (Linux fork semantics + PyJHora's
  module-level state). Switch to `spawn` start-method: `set_start_method('spawn')`
  before pool creation. Document in adapter.

## Memory hooks (executor should re-read at start)

- [[no-jh-parity-anywhere]]
- [[idempotency-guard-checks-write-target]]
- [[grep-check-is-not-compile-check]] — after delete, also run `tsc / pytest`
- [[never-rm-based-on-filename]] — diff content before deleting any non-natal_engine file
- [[silent-param-feature-toggle]] — required adapter args, not optional defaults

## Open follow-ups (not in this PR)

| ID | What | Why deferred |
|---|---|---|
| F1 | Renderer JSONL → FORENSIC-schema markdown | Separate PR |
| F2 | Governance-doc cleanup (40+ JH-parity grep hits in 00_ARCHITECTURE/) | Separate cleanup arc |
| F3 | Pariksha integration with PyJHora adapter | Pariksha is a separate workstream |
| F4 | Per-section ayanamsha map (R8 in [[FACT_ENGINE_BRIEF_REVIEW]]) | Need native input on KP-Krishnamurti vs Lahiri-default convention |

---

## Antigravity kickoff prompt (paste verbatim into a new Antigravity Claude Code chat)

```
You are executing CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md at
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md.

Read the brief end-to-end before any file edit. Honour every constraint in
the frontmatter (may_touch, must_not_touch, hard_bans). Re-read the memory
hooks listed in the brief at start.

Plan the work as the 12-step sequence in §Execution sequencing. Commit after
each step with a clear message. Push the branch after Step 8. Open the PR
after Step 12 with all 8 acceptance criteria checked in the PR description.

HALT at the PR. Do not deploy, do not merge, do not run gcloud, do not
modify production state. The native reviews and merges.

If you hit an unknown PyJHora API signature, do empirical discovery in a
scratch script under `platform/python-sidecar/tests/test_pyjhora_adapter/_scratch/`
(gitignored), then encode the discovered shape as a typed adapter function
+ test. Do not author a separate spike.

If `docker build` fails because of PyQt6, try `QT_QPA_PLATFORM=offscreen`
first, then lazy-import the calculation submodules. Document the working
strategy in the PR description.

Verification is internal-consistency ONLY. No JH-parity test. No external
oracle. Adapter tests assert structural invariants and arithmetic relationships.

Engine source of truth: PyJHora's computation IS the truth. Trust its outputs.
The adapter normalises shapes; it does not second-guess values.

When done: paste the PR URL + the 8-row acceptance-criteria checklist (all
green) + the chart_facts row-count query result for the native chart back
into chat. Stop there.
```

---

*End of CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md*
