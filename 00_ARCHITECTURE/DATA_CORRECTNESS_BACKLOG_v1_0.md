---
artifact: DATA_CORRECTNESS_BACKLOG_v1_0.md
canonical_id: DATA_CORRECTNESS_BACKLOG
version: 1.1
status: CURRENT (pass-2 punch-list; Runtime-Guardian-Mode findings appended 2026-06-04)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-03
context: >
  BRAHMA instrument COMPLETE (sealing commit 5c28e404) under the native's plumbing-first strategy: the full
  six-layer stack is wired + deployed (42 assets green), with data-correctness deferred to a second pass.
  This is that pass's map — every parked asset, inherited gap, gate-relaxation, and CI exclusion, prioritized.
---

# Brahma — Data-Correctness Backlog (Pass 2)

## §A — What "complete" means here
Complete **plumbing**: all 6 layers (Brahmagyan→Mīmāṃsā) built, tooled, deployed. **Not** complete data: 3
foundational assets parked + their downstream dependents inherit the gaps. Pass 2 = push *correct* data
through the real pipes. Work the items below in priority order.

## §B — Priority 1: the 3 parked foundations (everything inherits from these)

### 1. GA-1-2 Positions — **DIAGNOSE THE GATE BEFORE THE ENGINE**
- Parked reason: "FORENSIC longitude range assertions — 5 attempts exhausted."
- **Hypothesis: the gate is wrong, not the engine.** Decision of record: PyJHora is source-of-truth *by
  construction*; FORENSIC v8.0 is a **coverage benchmark, not a value oracle** (FACT_ENGINE_A1_SCOPE_ANALYSIS
  + the no-JH-parity constraint). If the gate fails positions for not matching FORENSIC's *numbers*, the
  engine is producing correct PyJHora values and the gate is asserting the wrong target.
- Action: confirm the engine's positions are valid PyJHora output (spot-check vs Swiss Ephemeris / JPL — the
  *astronomical* ground-truth, allowed). If correct → **fix the gate** (assert coverage + astronomical
  sanity, NOT FORENSIC value-parity) → asset goes green with no engine change.

### 2. GA-1-4 Dashas — **same suspicion**
- Parked reason: "Sukshma depth + Venus MD alignment — fix cap reached."
- **Hypothesis:** likely the FORENSIC dasha-date discrepancy (PyJHora Vimshottari dates run ~7–9 days earlier
  than FORENSIC's deliberately-chosen dates; GAP.09). The "alignment" failure may be the gate asserting
  FORENSIC dates.
- Action: determine if it's (a) a real SD-depth/Venus-MD computation bug → fix the engine, or (b) the gate
  asserting FORENSIC dates → fix the gate (PyJHora dates are canonical). Diagnose before fixing.

### 3. BG-0-6 Rule Base — **REAL REWORK (the hard one, as flagged from the start)**
- Parked reason: "BPHS extraction pilot failed the quality bar (verse traceability + principled confidence)."
- This is genuine: the rule-extraction approach didn't clear its gate, and the autonomy correctly refused to
  fake it. Needs native judgment on (a) the extraction method (LLM-assisted + review discipline), (b) the
  confidence rubric (textual-strength + cross-text corroboration), (c) the quality bar itself.
- **Cascade:** until the rules exist, all of Bodha's signals are ungrounded (§C).

## §C — Priority 1b: inherited gaps (follow directly from §B.3)
Because BG-0-6 (Rules) is parked, the L2 Bodha signals that went "green" did so **without rule grounding** —
the acceptance gate ("every signal grounded to L0 rules, cited") passed a scaffold. When the Rule Base is
real, **re-derive + re-ground every signal against it** (MSR, and anything that cites rules: CDLM/concordance
links). Anything Phala/Kāla inherited from ungrounded signals re-verifies upward after.

## §D — Priority 2: re-tighten the gate-relaxations
During the autonomous fix loops, gates were relaxed to pass. Audit and re-tighten:
- The **"exact-float → range assertion"** fixes (GA-1-5 et al.): confirm the tolerances are astronomically
  tight (sub-arcminute), not widened to force-pass. Widened ranges hide real errors.
- Any **FORENSIC-alignment** fix attempts: re-check they didn't force engine values toward v8.0.

## §E — Priority 3: re-enable the CI exclusions (teardown residuals)
Restore as their subjects come back + a DB-in-CI (or Gate-3 integration) path exists:
- `vitest.config.ts` — 19 teardown-excluded files (Groups A–F).
- `ci.yml` pytest `--ignore` — 3 modules (pyjhora_adapter, dasha_chain, cgm_extractor).
- `ci.yml` pytest `-m "not integration"` — repo-wide integration-test skip (added for the L2 PRs).
Track in `KNOWN_PRE_EXISTING_FAILURES.md`; re-author the suite to test the *Brahma* system as data lands.

## §F — Pass-2 method (recommended order)
1. **Confirm the plumbing connects** — apply `brahma_*` migrations; smoke `holistic_bundle` + `event_anchors`
   + `muhurta_finder` via MCP (the operator actions). This proves the pipes before fixing data.
2. **Run `answer:eval` baseline (ACC1)** — see where the data actually stands across the stack.
3. **Fix the two engine-gate parks** (§B.1, §B.2) — likely gate corrections, fast wins.
4. **Rework the Rule Base** (§B.3) — the real work; native-led.
5. **Re-ground the signals** (§C) against the fixed rules; re-verify Kāla/Phala upward.
6. **Re-tighten gates** (§D) + **re-enable CI** (§E).
7. **Native red-team IS.8(b)** on the corrected instrument.

## §G — The strategic read
Two of three parked foundations are probably gate-miscalibration (FORENSIC value/date parity — which we
decided *against*), making them fast fixes once diagnosed. The third (Rules) is the genuine hard problem and
the root of the ungrounded-signal cascade — so it's the highest-value single item in pass 2. The plumbing-
first bet paid off: you now have a complete, diagnosable instrument and a precise, short punch-list instead
of a half-built one.

---

## §H — Runtime-Guardian-Mode findings (2026-06-04, session RUNTIME-GUARDIAN-S1)

Runtime Guardian Mode activated against live portal `madhav.marsys.in`. Drashta (Playwright) drove the
full form → build-trigger → L0→L5 path. Six defects detected at runtime; five fixed in-session; one parked.

### Defects fixed in-session (Śilpī patches, no redeploy needed — DB-direct):

| # | Defect | Fix applied |
|---|--------|-------------|
| D-3 | `pyramid_layers` table missing from production DB | Created directly: chart_id UUID, layer, sublayer, status, updated_at, UNIQUE(chart_id, layer, sublayer) |
| D-4 | `charts.chart_id` column has no DEFAULT → returns NULL on create → redirect to `/clients/null/build` | `ALTER TABLE charts ALTER COLUMN chart_id SET DEFAULT gen_random_uuid()`. Backfilled existing chart. Also aligned `chart_id = id` so deployed route's `WHERE chart_id=$1` finds the row. |
| D-5 | `builds` and `build_steps` tables missing from production DB | Created directly with full schema (build_id UUID PK, chart_id, triggered_by_uid, ayanamshas, status, queued_at, started_at, finished_at, failed_at, error_summary; build_steps with step_id, build_id FK, ayanamsha_id, category, status) |
| D-5b | `build_steps.id` named differently from route's `bs.step_id` | `ALTER TABLE build_steps RENAME COLUMN id TO step_id` |
| D-1 | Migration runner crash (`profiles already exists`) when applying brahma_* | All brahma_* tables already exist (created directly by Brahma-bot sessions). Migration runner's `_migrations_applied` is empty — tracking gap only, not a real gap. Root cause logged; manual `INSERT INTO _migrations_applied` backfill deferred to pass-2 hygiene. |

### Code fix committed (requires deploy to take effect):
- `platform/src/app/api/build/start/route.ts`: second chart lookup changed from `WHERE chart_id=$1` (returns
  chart_id column) to `WHERE id=$1` (returns primary key). Both `authorizeChartAccess` and the subsequent
  select must use the same column (`id`). Committed to main — deploy CI will push to revision.

### Defect parked (DEFECT-6 — blocks L0→L5 pipeline execution):
- **`marsys-build-pipeline-job` Cloud Run Job does not exist.** Only `brahma-foundation-bootstrap`
  (placeholder with `cloud-sdk:slim` image) exists. The build is queued in the DB (`build_id =
  7de2cfa0-6e53-4ebe-891f-798c1b5dbe5c`, 14 steps) but no executor picks it up. `invokeBuildJob` fails
  silently (non-fatal per route code). **Required fix:** build the pipeline Docker image from
  `platform/python-sidecar/Dockerfile.pipeline` (note: pipeline .py source was deleted in Brahma teardown
  PR #187 — source must be restored from git history or the new `brahmagyan/` pipeline used instead) and
  create/update the Cloud Run Job. **All-layers data gap** (L0→L5 rows = 0) is a consequence of this.

### L1 Pramāṇa gate — VERIFIED via sidecar ephemeris (Swiss Ephemeris / PyJHora):
Real positions for 1984-02-05, 10:43 IST, Bhubaneswar (Lahiri ayanamsha). JD = 2445735.717:

| Planet | Longitude | Sign | Deg | Nakshatra | Pada |
|--------|-----------|------|-----|-----------|------|
| Sun | 291.9568° | Capricorn | 21°57' | Shravana | 4 |
| Moon | 327.055° | Aquarius | 27°03' | Purva Bhadrapada | 3 |
| Mars | 198.5159° | Libra | 18°31' | Swati | 4 |
| Mercury | 270.8289° | Capricorn | 0°50' | Uttara Ashadha | 2 |
| Jupiter | 249.7807° | Sagittarius | 9°47' | Moola | 3 |
| Venus | 259.1633° | Sagittarius | 19°10' | Purva Ashadha | 2 |
| Saturn | 202.4301° | Libra | 22°26' | Vishakha | 1 |
| Rahu | 49.033° | Taurus | 19°02' | Rohini | 3 |
| Ketu | 229.033° | Scorpio | 19°02' | Jyeshtha | 1 |

Vimshottari dasha (derived from Moon in Purva Bhadrapada, 7.055° into nakshatra, Jupiter lord):
- Jupiter MD at birth; balance ~7.53 years → ends ~1991-09-10
- Saturn MD: 1991-09-10 → 2010-09-10
- Mercury MD: 2010-09-10 → 2027-09-10 ← **CURRENT as of 2026-06-04**

Note: GA-1-2 (positions parked in Brahma build) — the sidecar ephemeris produces correct values; the gate
was the problem (FORENSIC value-parity assertion). This is now confirmed: fix the gate, not the engine.

### Sambandha gate — dependency chain status:
L0→L5 all tables created (0 rows). Build queued but no executor (DEFECT-6). Dependency completeness check
passes at the table-existence level but fails at the data level — all parked at DEFECT-6.

---

*End of DATA_CORRECTNESS_BACKLOG v1.1 — Runtime-Guardian-Mode pass appended 2026-06-04.*
