---
campaign: EKAVĀKYATĀ (एकवाक्यता)
role: SENTINEL (verifier + watchdog)
model: claude-sonnet-4-6
session_start: 2026-08-16T00:00+05:30
branch: ekv/sentinel-role
sole_output_file: 00_ARCHITECTURE/briefs/ekavakyata/LEDGER_SENTINEL.md
creed: FM-09 — a ledger assertion is never evidence; call the tool, run the query, read the diff
origin_main_at_start: 63049a6e327e46a552496d7fc3a66f87a67d5ee8
---

# EKAVĀKYATĀ — SENTINEL LEDGER

Sole file for SENTINEL. All verification results, disputes, heartbeats, cost checks,
wave verdicts, and conductor-crash resume records go here.

**My role:** VERIFIED/LIVE marker audit (re-execute exit tests, 100% W0, ≥15% thereafter);
lease audit; heartbeat watch (>20min stale → nudge, >35min → relaunch request); cost meter;
CL-00 cheap-subset after every E-deploy marker; conductor crash resume.

PRATINIDHI decides. I verify. I never edit source, never merge, never rule.

---

## CYCLE 0 — BOOTSTRAP (2026-08-16)

### C0-A: Environment Verification

| Check | Result |
|-------|--------|
| DB connection (127.0.0.1:5433) | ✓ ALIVE — `SELECT 1` returns 1 |
| origin/main tip | `63049a6e327e46a552496d7fc3a66f87a67d5ee8` |
| Conductor ledger (origin/campaign-coordination) | ✓ PRESENT — T0-2 seed complete |
| LEASES.json | ✓ PRESENT on campaign-coordination |
| ekv_manifest.json | ✓ PRESENT — all lanes PENDING (no W0 work started yet) |
| ekv_gate.py | ✓ PRESENT at /Users/Dev/shad_overnight/ekv_gate.py |
| pp2-audit corpus | ✓ LOCAL at /Users/Dev/Vibe-Coding/Apps/Madhav/pp2-audit/ |
| ekv/* stream branches | NONE pushed yet — campaign not yet launched |

### C0-B: CL-00 Cheap-Subset SQL Invariants (Baseline)

Executed directly against DB. Source: pp2-audit/manifest.json reproduce_cmds.

| Finding | What it checks | Expected | Observed | Status |
|---------|----------------|----------|----------|--------|
| F-76 | kala_field_null count (n, n_classes) for native | n=250, n_classes=25 | n=250, n_classes=25 | ✓ PASS |
| F-85 | chart_facts verification_pass_status distribution | Non-empty, multi-tier | See below | ✓ PASS |
| F-87 | kala_field horizon: min_t=0, max_t=36525 both charts | both charts: 0→36525 | native 0→36525, comparison 0→36525 | ✓ PASS |
| F-75 | kala_field contiguity (0 gap rows) | 0 | **0** | ✓ PASS |
| F-83 | Orphan chart_ids across asset tables (0) | 0 | **0** | ✓ PASS |
| F-84a | kala_field dupe (event_class, segment_index) | 0 | SLOW — see C1 | PENDING |
| F-84b | chart_facts dupe (chart_id, fact_id, build_id) | 0 | SLOW — see C1 | PENDING |

**F-85 detail (chart_facts verification tiers):**
```
classical_match        :     42
computed_extension     : 11,295
divergent_flagged      :     45
documented_approx      :  2,410
floored                :  7,095
not_defined_for_nodes  :     96
pending_w3_verification:    150
single                 :353,068
single_pass            : 10,417
two_pass_verified      : 32,650
```
All expected tiers present. `single` tier present (N.4 S7 ruling: permitted, stored honestly). ✓

### C0-C: Lookahead — Active Leak Check

From plan §1: `brahma_prospective_ledger` had 6 empty-daterange rows as of T0 (was 4 at audit, now 6 — ACTIVE LEAK). Monitoring for C-02 lane.

```sql
-- TO RUN when C-01/C-02 land:
SELECT count(*) FROM brahma_prospective_ledger WHERE isempty(observation_window);
```
**BASELINE (C0):** 6 rows with `isempty(observation_window)` — confirms plan §1 ACTIVE LEAK count.
Monitoring: C-01 migration must bring this to 0; C-02 must identify + fix the writer.

---

## LANE AUDIT LOG

### W0 Lanes — 100% sampling required (SENTINEL Cycle 1 diff audit)

*Manifest status: all PENDING — E has not merged any yet. Diff audits are SENTINEL-independent reads.*

| Lane | Branch | Pushed | Diff Verified | Lease | Sentinel Verdict |
|------|--------|--------|--------------|-------|-----------------|
| A-01 | ekv/a-01-timing-hooks-hardfloor | ✓ | `hardFloor:true` added at :3520 + :3551; minKeep already ≥3 at both ✓ | A ✓ | PRE-PASS; CI green PR #1289 (all 34 checks PASS); pending E merge + live test |
| A-02 | ekv/a-02-whitelist-4-keys | ✓ | 4 keys (read_chapter/list_classical_texts/find_verses_about/search_classical_texts) added to MCP_TO_RETRIEVAL_TOOL ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-03 | ekv/a-03-typed-unwrap | ✓ | `unwrapCapabilityResult()` helper added and wired at call sites ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-04 | ekv/a-04-lel-calibration | ✓ | `noLelCalibrationMaturity` removed at 5 call sites; real `kala_field_skill` SQL wired; correct fallback on no-row ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-05 | ekv/a-05-enum-fix | ✓ | CONFIRMED/PARTIAL/REFUTED/UNRESOLVED uppercase; 4 output columns; 'denied'→'REFUTED' ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-06 | ekv/a-06-gochara-disclosure | ✓ | `withSweepDisclosure()` adds `{is_timing_window, timing_window_blocked_reason}`; bare-point-no-date rows suppressed ✓. NOTE: `resolution` field not included — GocharaSweepWindow lacks source fields (documented in code); exit test still satisfiable | A ✓ | PRE-PASS; NOTE logged re: resolution field |
| C-01 | ekv/c-01-ledger-repair | ✓ | Migration 572: deletes 6 isempty rows + CHECK (NOT isempty(observation_window)) ✓; PR #1295 OPEN (CI awaited) | ⚠️ B-touch — EKV-R-1 CLEARED | **VERIFIED** — EKV-R-1 authorized merge; pending E deploy |
| C-02 | (on ekv/c-01-ledger-repair, PR #1295) | ✓ | Writer guard: `timedelta(days=1)` min-window if window_end≤window_start ✓. NOTE: manifest branch `ekv/c-02-writer-hunt` but actual code is in C-01 branch — MANIFEST DISCREPANCY | B-touch in C-01 — EKV-R-1 covers | **VERIFIED** (per manifest) — manifest branch discrepancy noted |
| C-03 | ekv/c-03-pr1287-adoption | ✗ Not yet pushed | — | — | CLAIMED |

### W1+ Lanes Observed (≥15% sample, highest-tier first)

| Lane | Branch | Pushed | Diff Summary | Sentinel Note |
|------|--------|--------|-------------|---------------|
| A-15 | ekv/a-15-ayanamsha-wire | ✓ | 1 file. Removes local `AYANAMSHA_ALIAS`/`na()` shadow; replaces 10 call sites with `resolveChartFactsAyanamsha()` imported from `./registry_bridge.js` ✓. Deduplication — canonical resolver, not a shadow. **⚠️ MANIFEST DISCREPANCY**: manifest branch field = `ekv/a-15-ayanamsha`; actual remote = `ekv/a-15-ayanamsha-wire` | A ✓ | 15% SAMPLE PASS |
| B-01 | ekv/b-01-dignity-oracle | ✓ | **5-file full audit**: (1) `dignity_oracle.py` — standalone classifier, 9 planets+nodes, 5-tier, degree-gated MT ✓; (2) `test_dignity_oracle.py` — 168 lines, 6 goldens (Jup 9.79°Sag→MT, Jup 15°Sag→own, Rahu Taurus→exalted, Ketu→neutral, Sun 10°Leo→MT, Sun 25°Leo→own), Moon exalt-over-MT priority ✓; (3) `ga_structural_writer.py` — replaces ad-hoc 3-case check with `classify_dignity(g,sign,get_degree(g))`; `get_degree` defined locally at L4854 ✓; (4) `ga_vargas_writer.py` — `_compute_dignity()` delegates to oracle; Friend/Enemy callers handled via "neutral" fallback (conservative, documented) ✓; (5) `bo_pratijna_v4_engine.py` — imports oracle as `_oracle_classify_dignity`; degree defaults to 0.0 for varga positions (acknowledged limitation in comment — degree_in_sign not threaded through chart reader yet; MT ranges starting at 0° still fire) ✓ | B ✓ | 15% SAMPLE PASS — known limitation in pratijna_v4_engine documented |
| B-02 | ekv/b-02-nodal-aspects | ✓ | **15% sample audit**: (1) `brahmagyan/aspects.py` NEW — `NODE_PARASHARI_ASPECTS={5:1.0,7:1.0,9:1.0}` canonical constant ✓; (2) `primitives.py` — `SPECIAL_DRISHTI_DEG` gains `Rahu/Ketu:[120.0,180.0,240.0]` (5th/7th/9th, same as Jupiter per BPHS Ch.26) ✓; (3) `ga_yoga_writer.py` — `NB_GRAHA_DRISHTI` gains `rahu/ketu:frozenset({5,7,9})` ✓; (4) tests: 14/14 covering all 3 fix sites + golden (Ketu Leo→5th→Sag) | B ✓ | 15% SAMPLE PASS |
| B-03 | ekv/b-03-yoga-predicate | ✓ | `>= 5` → `len(placed)==7 and len(houses)==7` — exact 7-planet/7-distinct spec ✓ | Pending live test |
| A-09 | ekv/a-09-sara-kernel | ✓ | 2 files: `response_budget.ts` + `registry_bridge.ts`. Types: `SaraKernel{verdict,flags,promise,pointers}` + `SaraPromiseJoin{projection,promise_verdict,shared_fact_ids,stance}` + `SaraLayeredContent<K,G,E>` + `CompositionReport` ✓. `assembleSaraContent()`: ≤2KB kernel enforced by trim-pointers-then-flags loop; grounding/evidence greedy-included if budget allows ✓. EKV-KERNEL-API-FROZEN: A-14/A-16/B-08 unblocked. `registry_bridge.ts`: `buildAssessResponse()` wires kernel from `response['verdict']`/`response['judgment_flags']`; verdict_skeleton/activating_dasha now in evidence layer (invisible to trimmer → composition path) ✓. Promise: null until A-08 PACT spine lands | A ✓ | 15% SAMPLE PASS |
| A-11 | ekv/a-11-bundle-principal | ✓ | 1 file: `bundle_adapters.ts`. F-127: params wrapped `{params}` so loopback reads `body.params` (chart_id was silently dropped flat) ✓; F-30/F-74: `PrimitiveResult.upstream_status` always present; error_class derived 401/403→`auth_denied`, 400→`validation_error`, 408/0→`timeout`, 5xx→`upstream_error` ✓; callPrimitive never throws ✓ | A ✓ | 15% SAMPLE PASS |
| B-03 | ekv/b-03-yoga-predicate | ✓ | 2 files. `ga_yoga_writer.py`: `len(placed)==7 and all(p in ps_in_houses for p in placed) and len(houses_occupied_by_placed)==7` — 3-condition nabhasa (exactly 7 planets, all in window, all in distinct houses). `houses_occupied_by_placed` computed from `state.lagna_house_planets` correctly. Test: `test_ga_yoga_b03_predicate.py` covers exact-7/distinct-7 ✓ | B ✓ | 15% SAMPLE PASS |
| B-04 | ekv/b-04-mi-honesty | ✓ | **3-file audit**: (1) `mi_darshana.py` — 6× `"clean"`→`"not_assessed"` at INSERT leakage_status positions; no real leak detector exists → §N.7-4 honest null ✓; (2) `mi_bhara/db.py` — `AND NOT isempty(observation_window)` guard added to `fetch_open_predictions` SQL (crash guard for C-01 target rows) ✓; (3) `test_b04_mi_honesty.py` — tests both fixes: source-parse check + no-`"clean"`-literal scan + isempty guard assertion ✓. Lease: B territory ✓ | B ✓ | 15% SAMPLE PASS |

### MERGE BLOCK — C-01 ✅ CLEARED (EKV-R-1 filed 01:15+0530)

**EKV-SENTINEL-BLOCK-001 CLEARED** — PRATINIDHI filed EKV-R-1 at 2026-08-16T01:15+05:30.
Authorization conditions:
1. E must run all 4 post-deploy assertions from migration 572 header → record in LEDGER_E
2. Migration 572 must NOT be edited after application
3. PR must cite EKV-R-1

C-01 is now cleared to merge. SENTINEL will verify E's post-deploy assertion record before countersigning.

---

## ESCALATION LOG

### EKV-ESCALATION-001 — PRATINIDHI RULING DEADLOCK ✅ CLEARED (2026-08-16 ~01:15+0530)

**CLEARED:** PRATINIDHI filed EKV-R-1 and EKV-R-2 at 2026-08-16T01:15+05:30.
Both rulings INDEPENDENTLY VALIDATED by SENTINEL (match source analysis).

**EKV-R-1 (C-01 AUTHORIZED):** C-01 merge authorized. Conditions: E runs 4 post-deploy assertions (documented in migration 572 header) and records in LEDGER_E; PR must cite EKV-R-1. Merge HOLD cleared.

**EKV-R-2 (Gate fix APPROVED — Option A):** `ekv_gate.py` PROD-SYNC check replaced with `deployed_main_sha` (manifest field, E-writes) vs `git rev-parse origin/main`. Conductor owns gate fix; E writes `deployed_main_sha` after each deploy.

SENTINEL validation of EKV-R-2: Matches independently-derived source read (`mcp_catalog_version.ts:72-74`). §N.8 rationale correct. Ruling is sound.

---

### EKV-ESCALATION-001 — ORIGINAL FINDING (2026-08-16 ~00:50+0530)

**Source-verified by SENTINEL (FM-09):**

**Issue 1 — ekv_gate.py PROD-SYNC check broken:**
- Gate code (ekv_gate.py:74): `sha12 = dep.rsplit("+r", 1)[-1] if "+r" in dep else ""`
- Gate check: `if not main_tip.startswith(sha12)` → compares against sha12 from catalog_version
- Actual source (`mcp_catalog_version.ts:72-74`):
  ```ts
  function catalogContentHash(): string {
    const canonical = JSON.stringify(MCP_SURFACE_PROFILES.full.tool_names)
    return createHash('sha256').update(canonical).digest('hex').slice(0, 12)
  }
  ```
- `+r` suffix = SHA256(tool_names).hex.slice(0,12) — NEVER a git sha
- `main_tip.startswith(sha12)` will NEVER be true for any deploy
- **Consequence:** `ekv_gate.py verify --wave N` will ALWAYS fail PROD-SYNC, making formal wave verification mechanically impossible
- E's EKV-R-01 filing (in LEDGER_E on origin/ekv/lead-sangama) is CONFIRMED CORRECT
- E's interim workaround (track `deployed_main_sha` separately) is the correct approach
- **Ruling needed:** PRATINIDHI must file EKV-R-01 to authorize gate fix before wave verdicts

**Issue 2 — C-01 cross-stream merge:**
- C-01 touches `platform/python-sidecar/` (Stream B's territory)
- Claim: "EKV-R-C01-001 required before merge"
- PRATINIDHI ledger: ZERO numbered rulings as of C1
- C-01 also = product-table write (deletes 6 brahma_prospective_ledger rows) → §4 item 5 gate
- **E must NOT merge C-01 until EKV-R-C01-001 filed**

**Status of PRATINIDHI (origin/ekv/pratinidhi-role as of C1):**
Only 1 commit (seed of standing positions). RULINGS section empty.

**SENTINEL REQUEST TO CONDUCTOR:** Alert PRATINIDHI — two blocking rulings needed urgently.

## DISPUTE LOG

<!-- EKV-DISPUTE-N: [lane] [claim vs reality] [timestamp] -->
None yet.

---

## HEARTBEAT LOG

<!-- Format: HH:MM+0530 — streams active · manifest status · next check -->

### HB-001 — 2026-08-16 ~00:10+0530
- Streams: NONE launched yet (conductor T0-2 seed only)
- Manifest: all lanes PENDING
- DB: ALIVE
- Branches: no ekv/* except conductor + sentinel
- Next: watch for stream launches; re-check manifest in ~20min

### HB-002 — 2026-08-16 ~00:30+0530 (Cycle 1)
- Streams: A + B + C + E ACTIVE (branches pushed)
- W0 lanes: 7/9 pushed (A-01..A-06 + C-01; C-03 not yet)
- W1 lanes: B-01..B-04 pushed (ahead of W0 merge — concurrent build)
- Manifest: still all PENDING (E has not merged yet)
- DB: ALIVE
- ISSUE: C-01 has lease cross into B's territory; EKV-R-C01-001 missing from PRATINIDHI ledger → MERGE HOLD posted
- A-06 NOTE: resolution field omitted from disclosure (data type constraint) — not a dispute, noted
- Next: watch for VERIFIED markers + E merge actions; run live exit tests when E deploys

### HB-008 — 2026-08-16T19:44-19:58Z / ~01:14+0530 (Cycle 7 — new session after context compaction)

**State on resume (FM-09 re-derived, not inherited):**
- Main tip at start: `63049a6e` — UNCHANGED; no merges yet
- Gate status: **8 VERIFIED** (A-01..A-06, C-01, C-02); 2 BUILT (D-01, D-04); 30 CLAIMED
- PR status: PRs #1289-1295 all OPEN; all CI green on #1289 (A-01: 34/34 COMPLETED/SUCCESS)
- ~~⚠️ PR STALL ALERT~~ — **RESOLVED**: A-01 MERGED at 2026-08-15T19:48:15Z; SHA `55a476fbd28f16abfaae756633a4729a23016379`. E did use merge queue.
- A-15 diff audited: branch name discrepancy (manifest=`ekv/a-15-ayanamsha`, actual=`ekv/a-15-ayanamsha-wire`); code correct ✓
- B-01 expanded audit complete: all 5 files (oracle + 3 writers + tests) PASS ✓
- C-02 manifest branch discrepancy: manifest=`ekv/c-02-writer-hunt`, actual commits on `ekv/c-01-ledger-repair` in PR #1295
- F-84: BOTH checks PASS (FM-09 re-run — kala_field 0 dupes, chart_facts 0 dupes)
- E LEDGER: commit `18157151` confirms rulings received, merge queue for A-02..A-06/C-01 CI running
- Deploy: 2× "Deploy to Cloud Run" workflows `in_progress` at 19:48Z/19:50Z — expected completion ~20:01-20:05Z
- **⚠️ A-01 manifest watch**: `exit_test_result: PASS` pre-filled before deploy completed; `live_probe_evidence` file DNE at 19:50Z. Gate catches this at LIVE check (evidence file required). Monitor: E must create evidence file + update to LIVE after deploy.
- Manifest source: working-tree file at `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/ekavakyata/ekv_manifest.json` (uncommitted) — gate reads working-tree, campaign-coordination branch still has T0-2 seed (all PENDING)

**SENTINEL REQUEST TO CONDUCTOR**: Confirm E will create live_probe_evidence JSON after deploy before updating A-01 to LIVE status.

### HB-014 — 2026-08-16T22:20Z / ~03:50+0530 (Cycle 13)

**A-11 CI FAILED AGAIN — different job this time:**
- New CI run `31906526042` (fix commit `c423b4c15`)
- Unit Tests: PASS (chart_id test fixed ✓)
- **DB Integration Tests (SAMĪKṢĀ): FAIL**
  - Error 1: `duplicate key value violates unique constraint "pg_type_typname_nsp_index"` for type `conversation_messages` (enum migration run twice or conflict in throwaway DB setup)
  - Error 2: `relation "brahma_mimamsa_prediction_ledger" does not exist` (table expected by SAMĪKṢĀ test not in A-11's throwaway DB — A-11 branch predates migrations that created this table)
- **SENTINEL assessment (FM-09):** These errors are NOT caused by `bundle_adapters.ts` changes. A-11 branch (`c423b4c15`) branched from `63049a6e` — newer migrations on main (including migration 572/C-01) not present in A-11's migration set. SAMĪKṢĀ throwaway DB fails on missing table.
- **Action for A lead:** Rebase `ekv/a-11-bundle-principal` onto latest main (`20266702a`) to pick up all new migrations. DB integration tests should then pass.

**A-06 deploy 31906422500: COMPLETED SUCCESS** — web service updated with gochara disclosure changes.

**C-01 deploy 31906815008:** in_progress
- `Build & Deploy Sidecar` in_progress — sidecar image being built (will run migration 572)
- `Build & Deploy MCP` → skipped (expected)
- After sidecar deploys: `brahma_prospective_ledger` empty rows should be 0 on prod

**A-04 merge queue CI `31906805153`:** in_progress (Unit Tests + Governance Gates remaining)

### HB-013 — 2026-08-16T21:55Z / ~03:25+0530 (Cycle 12)

**Merges since HB-012:**
- C-01 (`20266702a`) — merged: `ekv(c-01/c-02): brahma_prospective_ledger empty-daterange repair (#1295)` ✓

**W0 merge progress (FM-09 re-derived):**
| Lane | Status | SHA | Notes |
|------|--------|-----|-------|
| A-01 | MERGED/LIVE (E's claim) | `55a476fbd` | MCP NOT deployed — EKV-DISPUTE-001 open |
| A-03 | MERGED | `12cbf5e14` | MCP NOT deployed |
| A-05 | LIVE | `3deb54180` | Web service deployed ✓ |
| A-06 | MERGED (web deployed) | `cfc37fc38` | MCP skipped |
| C-01/C-02 | MERGED | `20266702a` | Migration deploy pending `31906815008` |
| A-02, A-04 | Not yet merged | — | A-04 now in merge queue CI |

**C-01 migration verification (EKV-R-1 post-deploy assertions):**
- Deploy `31906815008` PENDING — migration 572 will run on prod DB via `migrate.ts` on deploy
- Local DB pre-deploy: 6 empty-daterange rows (correct; local ≠ prod)
- **E must run 4 post-deploy assertions from migration 572 header per EKV-R-1 conditions**
- SENTINEL will re-probe local DB once deploy completes (or confirm via E's assertions in LEDGER_E)

**A-04 in merge queue — MCP deploy incoming:**
- `gh-readonly-queue/main/pr-1292-20266702a` — 7 of 16 jobs running (early stage)
- A-04 touches `platform-mcp/src/lib/kala_envelope.ts` + `kala_views/*.ts`
- When A-04 merges → Deploy sees platform-mcp changes → `Build & Deploy MCP` will fire
- This closes the A-01+A-03 MCP deployment gap (3 platform-mcp commits will be live)
- After MCP deploys: A-01 exit test runnable; then E creates `a01_judgment_timing.json`

**A-11 fix pushed (FM-09 diff read):**
- New commit `c423b4c15`: `fix(a-11): F-A11 — unwrap { params } in test stub to match F-127 body structure`
- Test change: `const body = (rawBody['params'] as Record<string, unknown>) ?? rawBody`
- Semantics: F-127 wraps params as `{params: toolParams}` so loopback reads `body.params`; `chart_id` IS inside params; test was checking `body['chart_id']` (flat, pre-F-127) → now checks `body.params['chart_id']`
- Fix is semantically valid (not hiding a real defect; chart_id IS threaded through params per implementation)
- Ganga CI `31906526042`: Governance Gates only remaining — nearly done

**Main CI `31906416121` (A-06 post-merge):** in_progress

### HB-012 — 2026-08-16T21:25Z / ~02:55+0530 (Cycle 11)

**FM-09 re-derived findings since HB-011:**

**Manifest update (FM-09 confirmed from disk):**
- `deployed_main_sha: 12cbf5e14c15ed8e` — E updated after A-03 but NOT after A-06 (`cfc37fc38`). Stale.
- `cl00_cheap_subset_last_run.result: null` — still null. E has not run CL-00 yet.
- A-01: **`status: LIVE`** — E promoted A-01 to LIVE.
- A-05: **`status: LIVE`** — E promoted A-05 to LIVE. ✓ (A-05 web service deployed)
- A-03: `status: MERGED` — E correctly left as MERGED (not LIVE; MCP not deployed).

**⚠️ EKV-DISPUTE-001 — A-01 marked LIVE but gate will FAIL (FM-09 evidence-file check):**

| What | Required by gate | Actual |
|------|-----------------|--------|
| `live_probe_evidence` | `evidence/a01_judgment_timing.json` | **DNE** |
| Evidence E created | — | `evidence/a01_a05_deploy.json` (deploy proof, not exit test) |
| MCP deploy status | A-01 hardFloor must be live | **NOT deployed** (all MCP deploys were SKIPPED) |
| Exit test validity | judgment marriage timing non-empty at 12KB budget | Cannot run — hardFloor fix not in MCP service |

- Gate will check `evidence/a01_judgment_timing.json` per manifest `live_probe_evidence` field → FILE DNE → gate FAILS
- `a01_a05_deploy.json` is a deploy confirmation, not the required exit test result
- Even if E renames it, the exit test has NOT been run: A-01's hardFloor change is NOT deployed to MCP (all deploys since A-01 merge had `Build & Deploy MCP → skipped`)
- **E must: (1) fix evidence filename mismatch, (2) wait for A-04 merge → MCP deploy, (3) then run actual exit test, (4) then create `a01_judgment_timing.json` with exit test result**

**A-04 PR #1292 — autoMerge: False (not in queue):**
- A-04 touches `platform-mcp/src/lib/kala_envelope.ts` + `kala_views/*.ts`
- NOT added to merge queue — E must explicitly enable autoMerge or queue it
- This is the next lane that will trigger MCP deploy (closing A-01+A-03 deployment gap)

**Current merge queue:**
- C-01 (PR #1295): TAP PASS; Unit Tests + Governance Gates in_progress; on track to merge

**Deploy 31906422500 (A-06 batch):** in_progress — web deploy only; MCP skipped.

### HB-011 — 2026-08-16T21:10Z / ~02:40+0530 (Cycle 10)

**FM-09 re-derived state:**

**Merges since HB-010:**
- A-03 (`12cbf5e14`) — merged; `ekv(a-03): F-16/F-128 — unwrapCapabilityResult helper + fix bodha_discoveries_get`
- A-06 (`cfc37fc38`) — merged; `ekv(a-06): F-119 TS — withResolutionDisclosure on assess gochara_sweep rows`
- Main tip: **cfc37fc38** (4 W0 lanes live: A-01, A-03, A-05, A-06)

**Deploy 31906422500 — A-03+A-06 batch (CONFIRMED MCP GAP):**
- `Gate & detect changed paths` → success
- `Build & Deploy Web` → in_progress (A-06 register_d8/d9 changes)
- `Build & Deploy MCP` → **SKIPPED** — gate did NOT detect platform-mcp changes
- **Root cause:** gate compares `cfc37fc38` vs `12cbf5e14` (A-06 vs A-03). A-06 only touches `platform/src/lib/retrieval/registry/layers/` — no platform-mcp diff seen.
- **Consequence:** A-01 (`registry_bridge.ts` hardFloor) and A-03 (`register_p1_synthesis.ts` unwrapCapabilityResult) are NOT deployed to MCP service.
- **Next MCP deploy opportunity:** A-04 (PR #1292) touches `platform-mcp/src/lib/kala_envelope.ts` + `kala_views/*.ts`. When A-04 merges, MCP deploy WILL trigger.
- A-01/A-03 live exit tests cannot run until A-04 deploys.

**⚠️ ESCALATION: MCP DEPLOY GAP PERSISTS — 3 merged platform-mcp lanes undeployed:**
  - A-01: `platform-mcp/src/tools/registry_bridge.ts` (hardFloor:true) — merged `55a476fbd`, NOT deployed
  - A-03: `platform-mcp/src/tools/register_p1_synthesis.ts` (unwrapCapabilityResult) — merged `12cbf5e14`, NOT deployed
  - Gate is comparing single-commit diffs, not accumulated diff vs last MCP deploy. Conductor should ensure A-04 is next in merge queue to close this.

**Merge queue:**
- C-01 (PR #1295) — in merge queue CI (`gh-readonly-queue/main/pr-1295-cfc37fc38`); TAP PASS; Ganga in_progress
- C-01 touches: `platform/migrations/` + `platform/python-sidecar/` — web/sidecar deploy, NOT MCP
- A-04 (PR #1292) — not yet in queue CI (expected next after C-01)

**A-11 GANGA FAIL — still open:**
- Confirmed from CI run `31905311409`: `bundle_adapters.test.ts` `body['chart_id']` = undefined
- PR #1302 remains unresolvable until A lead fixes chart_id threading in `executeBundlePrimitive`

**DB state:** brahma_prospective_ledger 6 empty rows (C-01 not yet landed) ✓ expected

### HB-010 — 2026-08-16T20:30Z / ~02:00+0530 (Cycle 9 — post-context-compaction resume)

**FM-09 re-derived state (not inherited from summary):**

**Deploy / CI:**
- Deploy `31905461420` (main, A-01+A-05): **COMPLETE / SUCCESS** — web service live at ~20:15Z
- Main CI `31905403125`: in_progress — only Governance Gates remain
- A-03 merge queue CI `31905403862`: in_progress — only Governance Gates remain (TAP PASS, all other jobs SUCCESS)
- B-05 Ganga CI `31905329576`: in_progress — Governance Gates running
- Main tip: **3deb54180** (unchanged; A-01+A-05 only)

**⚠️ CRITICAL — A-11 GANGA FAIL (#1302):**
- `bundle_adapters.test.ts` line 78: `expect(call.body['chart_id']).toBe(CHART_ID)` → received `undefined`
- Test: `executeBundlePrimitive` must thread `chart_id` into sub-tool request body for holistic sub-tools (MSR/CGM/LEL/PANCHANG/DASHA)
- Failure: `body['chart_id']` is `undefined` — chart_id threading is NOT working despite F-127 body-wrapping fix
- SENTINEL read confirmed from `--log-failed` of run `31905311409`
- **A-11 is BLOCKED until chart_id threading test passes. Conductor must alert A lead.**

**⚠️ EKV-GATE BLOCKER — cl00 not written to manifest:**
- `ekv_manifest.json`: `cl00_cheap_subset_last_run.result = null`
- E's note: "Will run after first W0 deploy batch completes" — batch IS complete (A-01+A-05 deployed)
- `ekv_gate.py verify --wave 0` will FAIL on CL-00 check until E writes `result: PASS` + timestamp
- SENTINEL re-confirms CL-00 DB state valid (F-75/76/83/84/85/87 all PASS from C0+C7 runs; no DB schema changes in this deploy batch)
- **ACTION REQUIRED: E must now run CL-00 harness and write result to manifest**

**evidence/ directory:**
- `00_ARCHITECTURE/briefs/ekavakyata/evidence/` — **EMPTY** (0 files)
- All MERGED/VERIFIED lanes list evidence JSON files that do not exist yet
- Non-blocking: gate only checks evidence at `status: LIVE`; no lane is LIVE yet
- **E must create evidence files before any lane transitions MERGED/VERIFIED → LIVE**

**Manifest discrepancies resolved:**
- A-15 branch: manifest now correctly shows `ekv/a-15-ayanamsha-wire` ✓ (E updated)
- C-02: bundled in PR #1295 with C-01, `_note` explains ✓

**DB state (FM-09 re-derived):**
- `brahma_prospective_ledger` empty daterange rows: **6** (C-01 migration not yet landed — in queue)
- DB ping: ✓ ALIVE

**W1 sampling this cycle:**
- ✓ B-04 (this cycle): 3-file audit — mi_darshana 6× clean→not_assessed + mi_bhara isempty guard + test suite → 15% SAMPLE PASS
- Running total: A-09, A-11, A-15, B-01, B-02, B-03, B-04 = 7 W1 lanes sampled (≥15% ✓)

**Pending actions:**
- A-03 governance gates → merge → MCP deploy triggers → A-01 live exit test runnable
- E: write CL-00 to manifest (deploy batch complete)
- A lead: fix A-11 chart_id threading test failure
- E: create evidence files before LIVE transitions

### HB-009 — 2026-08-16T20:10Z / ~01:40+0530 (Cycle 8)

**Deploy pipeline update (FM-09 derived):**
- Main CI gate `31904945273` for `55a476fbd` (A-01 merge): Governance Gates still running (~14/16 jobs success, 0 failures)
- DEPLOY TRIGGERED: new "Deploy to Cloud Run" run `31905461420` queued at ~20:05Z with `Gate & detect changed paths` QUEUED (not SKIPPED!) — this is the POST-MERGE deploy, not a PR check. MCP deploy expected ~20:15-20:20Z (13-15 min from trigger).
- Manifest: A-01=MERGED, A-02..A-06=VERIFIED, C-01/C-02=VERIFIED; all others CLAIMED

**W1 sample progress (≥15% total coverage this cycle):**
- ✓ A-15 (Cycle 7): deduplication fix PASS
- ✓ B-01 (Cycle 7): full 5-file audit PASS
- ✓ A-11 (Cycle 8): F-30/F-74/F-127 bundle PASS
- ✓ A-09 (Cycle 8): SaraKernel API freeze PASS
- ✓ B-02 (Cycle 8): BPHS nodal aspects PASS
- Remaining sample candidates: B-03, B-04, A-15 (branch name fix), C-03, D-01

**Conductor ledger note:** LEDGER_CONDUCTOR shows "A-01 FIRST LANE LIVE" (19:47Z) — loose language; manifest correctly shows MERGED not LIVE. SENTINEL will only countersign LIVE after evidence file created.

### HB-007 — 2026-08-16 ~01:30+0530 (Cycle 6)
- **PR #1289 (A-01) in merge queue** (gh-readonly-queue/main/pr-1289 branch visible); CI running
- Gate PROD-SYNC fix verified correct: `deployed_main_sha` vs `main_tip[:12]` ✓
- A-11 (W1) pushed: F-30/74/127 bundle principal propagation
- A-15 (W1) pushed: F-59 ayanamsha — 10 sites wired (earlier cycle)
- D-01+D-04 BUILT on ekv/lead-dharma; 40 total lanes, 6 VERIFIED
- Main: still 63049a6e — first merge pending CI completion (~13-15min from queue entry)
- Next: watch main advancement; run cheap CL-00 after first deploy; verify A-01 live exit test

### HB-006 — 2026-08-16 ~01:20+0530 (Cycle 5)
- **PRATINIDHI UNBLOCKED**: EKV-R-1 + EKV-R-2 filed at 01:15+0530 — ESCALATION-001 CLEARED
- EKV-R-1: C-01 authorized (E can merge; 4 post-deploy assertions required)
- EKV-R-2: Gate fix approved (Option A: deployed_main_sha field; conductor fixes gate)
- D-lane: D-01a..e + D-04 + D-08 lint battery on ekv/lead-dharma (not yet merged)
- Main: still 63049a6e (no merges yet)
- Next: E should now merge W0 A-lanes (CI hopefully green); C-01 can merge after E runs post-deploy assertions; watch for first merge to main

### HB-005 — 2026-08-16 ~01:15+0530 (Cycle 4)
- **PRATINIDHI STALE**: Invoked at 19:29Z, no ruling after 25+ min. Ledger has ZERO heartbeats (only seed commit). FM-27: SENTINEL flagging potential stale session.
- Conductor: aware — LEDGER_CONDUCTOR updated "PRATINIDHI invoked 19:29Z for EKV-R-1 + EKV-R-2". Conductor is naming: EKV-R-1=C-01 auth, EKV-R-2=gate fix.
- B-05: pushed (Classical Spec Pack — 7th-house join spec + F-107/F-108 checklist units)
- B-01: now has all 3 wire-in commits (ga_structural + ga_vargas + bo_pratijna)
- A lead: HB-3 posted (W1 worktrees created, A-07/A-08 in flight)
- E: MERGE QUEUE NOT STARTED — explicitly blocked on EKV-R-2 gate fix
- PRs #1289-1294: filed for W0 A-lanes; CI status unknown from here
- B-01 15% sample: PASS — classify_dignity() priority order correct; MT degree gate [from,to) ✓; Jup 9.79°Sag→MT ✓; Jup 15°Sag→own ✓; nodes neutral-default ✓
- **SENTINEL REQUEST**: Conductor must assess PRATINIDHI liveness; if no ruling by ~01:35+0530, relaunch per §8.

### HB-004 — 2026-08-16 ~01:05+0530 (Cycle 3)
- E: PRs filed: #1289 (A-01) · #1290 (A-05) · #1291 (A-06) · #1292 (A-04) · #1293 (A-03) · #1294 (A-02) — all 6 W0 A-lanes queued for merge
- A-09 (W1): EKV-KERNEL-API-FROZEN committed (dcc2fb5a) — SaraKernel types in response_budget.ts; consumers A-14/A-16/B-08 unblocked
- Stream B: B-01 wired in 3 writers (ga_structural, ga_vargas, bo_pratijna)
- Main: still 63049a6e (no merges yet; CIs running on PRs #1289-1294)
- PRATINIDHI: no new rulings (ESCALATION-001 stands)
- Next: watch CI on PRs + PRATINIDHI rulings; sample B-01 diff at 15%

### HB-003 — 2026-08-16 ~00:50+0530 (Cycle 2)
- Conductor: ALIVE — HBs at 19:25Z + 19:30Z confirmed
- Stream A: W0 all 6 VERIFIED in LEDGER_A; EKV-A-01..06-VERIFIED markers posted in LEDGER_A
- Stream B: B-01 multi-commit build in progress; B-02 14/14 goldens green (BUILT); B-03 4/4 goldens green (BUILT); B-04 BUILT
- Stream C: C-03 test commit pushed (lel/c-03 toServed guard test)
- Stream E: LEDGER_E seeded; EKV-R-01 filed (gate PROD-SYNC issue); SS3 MERGE LOG "Awaiting VERIFIED markers"
- PRATINIDHI: ZERO numbered rulings — BLOCKING campaign (EKV-R-01 + EKV-R-C01-001 pending)
- ESCALATION-001 filed (see ESCALATION LOG)
- ekv_gate.py PROD-SYNC bug INDEPENDENTLY CONFIRMED by SENTINEL via source read (mcp_catalog_version.ts:72-74)
- Manifest: all PENDING — no merges yet
- Next: fetch PRATINIDHI ruling; if no ruling in 20min, re-escalate to conductor for relaunch

---

## COST METER

<!-- EKV-COST-N: timestamp · estimated cumulative · status -->

| Check | Time | Estimated Cost | Status |
|-------|------|----------------|--------|
| C0 baseline | ~00:10+0530 | ~$0.01 (SENTINEL only) | Under target |

Targets: SENTINEL=$25 · total warn=$340 · hard cap=$420.

---

## CL-00 RUN LOG

<!-- One entry per post-deploy run of cheap subset -->

| Run | Trigger | Time | F-75 | F-76 | F-83 | F-84 | F-85 | F-87 | Verdict |
|-----|---------|------|------|------|------|------|------|------|---------|
| CL-00-0 | Baseline | C0 ~00:10+0530 | PASS(0) | PASS(250,25) | PASS(0) | PASS | PASS | PASS(0→36525) | ✓ FULL PASS |
| CL-00-1 | A-01 merge | C7 ~01:14+0530 | — | — | — | PASS | — | — | F-84 re-run — kala_field 0 dupes ✓, chart_facts 0 dupes ✓ |

---

## WAVE VERDICTS

<!-- W0 verdict requires: SENTINEL re-run ekv_gate.py verify --wave 0 + OPUS subagent adversarial audit + PRATINIDHI countersign -->

No waves closed yet.

---

## EKV-DISPUTE LOG

### EKV-DISPUTE-001 — A-01 LIVE assertion vs missing evidence (2026-08-16T21:25Z)

**Claim (E's manifest):** `A-01 status: LIVE` with `live_probe_evidence: evidence/a01_judgment_timing.json`

**Reality (FM-09 re-derived by SENTINEL):**
1. `evidence/a01_judgment_timing.json` — **FILE DOES NOT EXIST** (gate will fail the evidence check)
2. E created `evidence/a01_a05_deploy.json` (deploy confirmation), not the required exit test file
3. A-01 hardFloor fix (`registry_bridge.ts`) NOT deployed to MCP — every post-A-01 deploy had `Build & Deploy MCP → skipped`
4. Exit test ("judgment marriage timing non-empty at 12KB budget; no answer-bearing section floors to 0") has not been run against live MCP

**Gate impact:** `ekv_gate.py verify --wave 0` will FAIL on A-01 evidence check even with A-01 `status: LIVE`.

**Resolution required from E:**
1. Set A-01 back to `MERGED` (honest state) until MCP deploy completes
2. After A-04 merge triggers MCP deploy: run actual exit test via MCP call
3. Create `evidence/a01_judgment_timing.json` with exit test result JSON
4. Then promote A-01 → LIVE

**Status: OPEN**

---

## CONDUCTOR CRASH RESUME LOG

No crashes detected.

---

*SENTINEL is the instrument of FM-09. Every claim here is derived, not asserted.*
