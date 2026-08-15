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
| A-01 | ekv/a-01-timing-hooks-hardfloor | ✓ | `hardFloor:true` added at :3520 + :3551; minKeep already ≥3 at both ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-02 | ekv/a-02-whitelist-4-keys | ✓ | 4 keys (read_chapter/list_classical_texts/find_verses_about/search_classical_texts) added to MCP_TO_RETRIEVAL_TOOL ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-03 | ekv/a-03-typed-unwrap | ✓ | `unwrapCapabilityResult()` helper added and wired at call sites ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-04 | ekv/a-04-lel-calibration | ✓ | `noLelCalibrationMaturity` removed at 5 call sites; real `kala_field_skill` SQL wired; correct fallback on no-row ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-05 | ekv/a-05-enum-fix | ✓ | CONFIRMED/PARTIAL/REFUTED/UNRESOLVED uppercase; 4 output columns; 'denied'→'REFUTED' ✓ | A ✓ | PRE-PASS; pending E deploy + live test |
| A-06 | ekv/a-06-gochara-disclosure | ✓ | `withSweepDisclosure()` adds `{is_timing_window, timing_window_blocked_reason}`; bare-point-no-date rows suppressed ✓. NOTE: `resolution` field not included — GocharaSweepWindow lacks source fields (documented in code); exit test still satisfiable | A ✓ | PRE-PASS; NOTE logged re: resolution field |
| C-01+C-02 | ekv/c-01-ledger-repair | ✓ | Migration 572: deletes 6 isempty rows + CHECK (NOT isempty(observation_window)) ✓; writer guard: timedelta(days=1) min-window ✓. ⚠️ LEASE: touches `python-sidecar/` (B's territory) | ⚠️ B-touch — see BLOCK below | **MERGE HOLD: EKV-R-C01-001 not yet in PRATINIDHI ledger** |
| C-03 | ekv/c-03-pr1287-rebase | ✗ Not yet | — | — | Not yet pushed |

### W1+ Lanes Observed (≥15% sample, highest-tier first)

| Lane | Branch | Pushed | Diff Summary | Sentinel Note |
|------|--------|--------|-------------|---------------|
| B-01 | ekv/b-01-dignity-oracle | ✓ | 534 line diff — dignity oracle module | Pending 15% sample |
| B-02 | ekv/b-02-nodal-aspects | ✓ | NODE_PARASHARI_ASPECTS hoisted to brahmagyan/aspects.py; Rahu/Ketu SPECIAL_DRISHTI_DEG fixed; tests for 5/7/9 BPHS aspects ✓ | Pending live test |
| B-03 | ekv/b-03-yoga-predicate | ✓ | `>= 5` → `len(placed)==7 and len(houses)==7` — exact 7-planet/7-distinct spec ✓ | Pending live test |
| B-04 | ekv/b-04-mi-honesty | ✓ | 6× `'clean'`→`'not_assessed'` in mi_darshana.py ✓ | Pending live test |

### MERGE BLOCK — C-01

**EKV-SENTINEL-BLOCK-001 (2026-08-16 C1):**
C-01 branch touches `platform/python-sidecar/scripts/kala_admission/w45_post_fit_rebuild.py`,
which is Stream B's lease territory per LEASES.json. The commit self-declares this requires
"PRATINIDHI sign-off EKV-R-C01-001 before merge." PRATINIDHI ledger (origin/ekv/pratinidhi-role)
currently has ZERO numbered rulings — EKV-R-C01-001 does not exist.

**E must not merge C-01 until EKV-R-C01-001 appears in origin/ekv/pratinidhi-role.**
This is also a product-table write (deletes 6 rows from brahma_prospective_ledger) — double gate.

The fix itself looks correct (root cause correctly identified; migration idempotent; writer guard minimal).
Once PRATINIDHI files the ruling, SENTINEL will re-confirm and clear the block.

---

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
| CL-00-0 | Baseline | C0 ~00:10+0530 | PASS(0) | PASS(250,25) | PASS(0) | PENDING | PASS | PASS(0→36525) | PARTIAL — F-84 slow |

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
