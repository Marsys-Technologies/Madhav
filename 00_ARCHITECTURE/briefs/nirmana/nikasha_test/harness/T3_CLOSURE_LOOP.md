---
artifact: NIKASHA_TEST_T3_CLOSURE_LOOP
version: "1.0"
status: FINAL
campaign_id: nikasha-test
phase: 3
test: T3 (the closure loop — never run before)
date: 2026-09-26
target: sandbox only (db nikasha_sandbox; ledgers: harness/sandbox_control/)
---

# T3 — The closure loop, run end to end for the first time

Question (register R33): can a Nikaṣa gap row be **closed by measurement** — census → CLOSED →
cert record → tracker increments — and can it **re-open** when the defect returns?

**Answer: not with the stock tooling (two blocking defects, R57), and yes with a small,
specified change — proven end to end in the sandbox: `bg_nakshatra_medical` went
GAPS_REGISTERED → ELEVATED (0/360 → 9/360 gates) and back on regression.**

## 1. The three gaps chosen (ledger rows quoted)

**Data gap** — `bg_ontology-Vocab.alias` (also hand-written `bg_ontology-G07`):
> "measured: 16 class(es); empty alias sets: dosha 79/79 / required: the Vocab gate's claim"

**Registry gap** — `bg_nakshatra_medical-Build.registered`:
> "measured: @register in bg_medical_mappings.py but registry says has_writer=false / required:
> the Build gate's claim"

**Detector gap** — `bg_doshas-Idem.pattern`:
> "measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify
> there / required: the Idem gate's claim"

## 2. Fixes applied (sandbox, exactly as production would)

| fix | kind | exact change |
|---|---|---|
| F1 | data | `harness/t3_seed_dosha_aliases.py` — deterministic seeder: synonyms for all 79 dosha rows derived from each row's canonical_name_en/sa (lowercase, diacritic-folded, parentheticals split, "dosha"-stripped variants). 79/79 empty → 0/79 empty. Idempotent by construction. |
| F2 | registry | `UPDATE asset_registry SET has_writer=true WHERE asset_id='bg_nakshatra_medical'` |
| F3 | detector | `harness/asset_census_closing.py` — scratch copy of the inspector; `idem_scan` follows the writer's `from brahmagyan.* import …` delegation one hop and scans the seeder's SQL. bg_doshas → PASS ("idempotent in delegated seeder l0_doshas.py: DELETE-then-INSERT (layer convention is upsert — mechanism differs, property holds)"). |
| F4 | data+run | `harness/t3_run_writer.py` — **actually ran** `BgMedicalMappingsWriter.run()` against the sandbox inside a real build_runs row (`c0db4bc1-…`, scope=asset_set, harness owns the transaction as the orchestrator would): 60 rows inserted across 3 tables; build_run_assets `complete` rows for the 3 covered assets; asset_throughput updated from the measured run (rps = live/duration). |
| F5 | code | `density_contract: { paginated: false, facets: [...], empty_reason: true }` added to `query_nakshatra_medical.ts` (L1 convention copied from get_condition_composite.ts). **Reverted after measurement.** |
| F6 | detector+data | `harness/sandbox_control/detectors/bg_nakshatra_medical_D1.py` (D1 source correspondence: every citation must resolve to an admitted text). First run **FAILED — it can fail**: `'ashtanga hridayam' cited by 27 row(s), not in text registry`. Fix: admitted `ashtanga_hridayam` to brahma_ontology text class (15→16). Detector → PASS 27/27. |

## 3. What happened to the rows on re-run

Stock inspector `emit_gaps` (read at platform/scripts/governance/asset_census.py:576): appends
OPEN rows with deterministic ids, **skips any id already present — there is no closure path at
all**. Stock tracker (`asset_elevation_tracker.py:200`) reads state **per row**, so even an
appended CLOSED row would not close the earlier OPEN row. Two defects, together = R57.

Scratch versions: `asset_census_closing.py` (append-only ledger; emits CLOSED rows when a
previously-OPEN deterministic-id row's check now passes, and RE-OPENED rows when a closed check
fails again) and `tracker_sandbox.py` (ledger dir redirected by `NIKASHA_CONTROL_DIR`; gap state
= latest row per gap_id).

Run 1 (F1+F2+F3 applied): **25 rows closed by measurement**, 4 appended, 184 already present.
The three chosen rows:

- `bg_ontology-Vocab.alias` → **CLOSED** ("empty alias sets: none")
- `bg_nakshatra_medical-Build.registered` → **CLOSED** ("@register in bg_medical_mappings.py; registry agrees")
- `bg_doshas-Idem.pattern` → **CLOSED** (seeder-following)

Plus 22 more `Idem.pattern` rows closed — the detector fix generalizes across every delegating
L0 writer (bg_rules, bg_yogas, bg_reference, …).

**The loop talks back:** fixing the registry gap opened a new measured row —
`bg_nakshatra_medical-Build.exercised` OPEN ("registered with a writer and the orchestrator has
NEVER run it") — true and correct: the registry now promises a writer the orchestrator never
dispatched. F4 (really running it) closed it. Also appended: 3 `Count.floor` rows
(bg_cohort/bg_ephemeris/bg_muhurta_lattice) that are **sandbox-sampling artifacts** — floors are
declared for production scale; a census pointed at a sampled sandbox should not emit them (R62).

Run 2 (F4–F6 applied): 11 more closures. bg_nakshatra_medical's ledger: **all 7 rows CLOSED**
(6 original + the exercised row the registry fix opened).

## 4. Certification and the tracker

9 cert records written to the sandbox copy of `asset_certs.jsonl` (its `_schema` shape:
asset/criterion/criterion_version/detector/evidence/verdict/verified_by/verified_on) — one per
gate (Ldgr, Idem, Earn, Null, Vocab, Carr, Narr=N/A no prose, Dens, Build), evidence = census
run file, detector run id, or the hand query. Hand-verified where the inspector has no generic
check: Null (no nulls/sentinels, numbers 1–27 complete), Ldgr (classical_citation 27/27 — the
inspector never emits Ldgr for this asset: its citation-column list misses the singular
`classical_citation` — R60).

Tracker (sandbox copy, sandbox DSN, sandbox ledgers):

| | ELEVATED | open gaps | gates certified |
|---|---|---|---|
| before (production baseline, Phase 0) | 0/40 | 239 | 0/360 |
| after fixes + certs | **1/40** | 207 | **9/360** |

`bg_nakshatra_medical`: GAPS_REGISTERED → **ELEVATED** ("every gate certified or disposed; no
open gap").

## 5. Regression — the loop counts down

`UPDATE asset_registry SET has_writer=false` → re-run closing inspector: `Build.registered`
FAIL → **1 row RE-OPENED** (append-only: a new OPEN row under the same gap_id). Tracker:
**ELEVATED 1→0**, open gaps 207→208, asset state ELEVATED → CERTIFIED_GAPS_OPEN ("1 gap(s)
open"). Re-apply the fix → 1 row closed → ELEVATED 1/40 again. A loop that only counts up is
not a loop; this one counts both ways.

## 6. Restore (sandbox hygiene)

All sandbox DB changes reverted and verified (dosha synonyms 79/79 empty, text class back to
15, has_writer=false, T3 build run rows deleted, throughput rps back to NULL);
`query_nakshatra_medical.ts` reverted; `git status` clean for `platform/` and
`00_ARCHITECTURE/control/`; production ledgers untouched (263/1 lines throughout). The proof
lives in `harness/sandbox_control/` (ledgers with the full OPEN→CLOSED→OPEN→CLOSED history) and
`census/t3_*.json`.

## 7. What had to be built to make the loop work — the implementation-plan core

1. **Ledger redirection** — both stock tools hardcode `00_ARCHITECTURE/control/`; the closing
   variants take `NIKASHA_CONTROL_DIR`. (Same defect class as R47.)
2. **Closure semantics in emit_gaps** — last-row-per-gap_id state; append CLOSED when the
   detector now passes, append RE-OPENED when a closed check fails again. ~40 lines.
3. **Last-wins gap resolution in the tracker** — collapse ledger by gap_id before counting
   open rows. ~6 lines. Without this, append-only closure is invisible.
4. **Seeder-following idem_scan** — resolve `from <package> import …` in the writer and scan
   the seeder module's SQL; report the mechanism and whether it matches the layer convention.
   ~25 lines.
5. **A per-asset Carr detector convention** — `<control>/detectors/<asset>_D<n>.py`, run by the
   inspector, verdict adopted; a registered detector that cannot run is not a pass.
6. **A harness orchestrator pass** (`t3_run_writer.py`) — the only honest way to close
   Build.exercised / instrument Earn: run the writer for real and record the run.
7. **A deterministic alias seeder** (`t3_seed_dosha_aliases.py`) — the data-fix shape.

## 8. Findings → register rows

R57 (closure impossible in stock tooling — the campaign's headline finding; fixed-during-campaign
in scratch copies, production adoption specified above), R58 (hand-written gap rows carry no
detector binding — they can never close by measurement), R59 (Ashtanga Hridayam cited but not
admitted — found by the first real D1 detector), R60 (Ldgr citation-column list misses the
singular `classical_citation`), R61 (registry repairs cascade into newly-true gaps — loop must
handle cascades; it did), R62 (sandbox census emits prod-scale Count.floor rows — target-aware
floors needed). R33 → CLOSED.
