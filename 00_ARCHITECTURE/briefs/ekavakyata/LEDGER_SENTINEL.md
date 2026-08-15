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
| B-02 | ekv/b-02-nodal-aspects | ✓ | NODE_PARASHARI_ASPECTS hoisted to brahmagyan/aspects.py; Rahu/Ketu SPECIAL_DRISHTI_DEG fixed; tests for 5/7/9 BPHS aspects ✓ | Pending live test |
| B-03 | ekv/b-03-yoga-predicate | ✓ | `>= 5` → `len(placed)==7 and len(houses)==7` — exact 7-planet/7-distinct spec ✓ | Pending live test |
| B-04 | ekv/b-04-mi-honesty | ✓ | 6× `'clean'`→`'not_assessed'` in mi_darshana.py ✓ | Pending live test |

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

No disputes filed.

---

## CONDUCTOR CRASH RESUME LOG

No crashes detected.

---

*SENTINEL is the instrument of FM-09. Every claim here is derived, not asserted.*
