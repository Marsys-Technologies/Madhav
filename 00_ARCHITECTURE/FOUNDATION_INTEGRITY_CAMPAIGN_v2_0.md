---
artifact: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md
canonical_id: FOUNDATION_INTEGRITY_CAMPAIGN
version: 2.0
status: CURRENT — supersedes v1.0. The COMPLETE-coverage plan: finish the full deep audit (gap-fill) → consolidate → full DAG-respecting rebuild → seal L0–L4. L5 OUT of scope until sealed.
authored_by: Cowork 2026-06-23
supersedes: FOUNDATION_INTEGRITY_CAMPAIGN_v1_0.md (partial-audit version)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The governing plan to take L0–L4 to a PROVABLY-SOUND foundation with COMPLETE audit coverage (the v1
  audit was uneven — L0 deep, L1–L4 mostly PENDING). Native rulings (2026-06-23): (1) DEEP on all 69 but
  REUSE the already-proven (16 WRONG + Gate-A SOUND) — gap-fill only; (2) mostly-sequential, parallel-where-
  safe, RESUMABLE, layer-by-layer, low-concurrency execution (the prior 14-agent fan-out died 12/14);
  (3) L5 ENTIRELY OUT until L0–L4 is sealed — it's the next campaign, not this one; (4) data is DISPOSABLE
  (code is the deliverable, §1.5 carried from v1); (5) full DAG-respecting rebuild so all assets are in sync,
  no cross-layer consistency issues.
---

# Foundation Integrity Campaign v2.0 — Complete Coverage

## §1 — Why v2 (the v1 audit was uneven)
The v1 targeted audit ran PARTIAL (12/14 agents died on API overload) and was UNEVEN by design: L0 got a
full deep audit, but L1–L4 are mostly "PENDING DEEP AUDIT" in FOUNDATION_ROOT_CAUSE_MAP.md (L1: 13 of 16
pending; L2: 7 pending; L3: ~6 pending; L4: 6 pending), and the cheap census never returned data for
L1/L2/L3. So we have 16 CONFIRMED-WRONG root causes but NOT complete coverage — a hidden bug could sit in
any of the ~30+ un-deep-audited assets (the ka_sangam lesson: the worst bug hid in an asset that LOOKED
fine). v2 closes the coverage gap to "no scope for assumption," then remediates everything as one
consolidated, DAG-respecting rebuild.

## §1.5 — Doctrine (carried from v1, reaffirmed)
DATA-FIRST not docs/code. DATA IS DISPOSABLE — code is the deliverable; the goal is every writer's LOGIC
correct so ANY build is sound. DIAGNOSE COMPLETELY BEFORE FIXING. FIX RIGHT, GROUND-UP, FULL LATITUDE.
ASSESS ≠ FIX, gated. VERIFY against data (re-derivation now; the final build later). L5 OUT until L0–L4 sealed.

## §2 — The three phases

### PHASE A2 — COMPLETE the deep audit (gap-fill; reuse the proven)
Deep-audit ONLY the assets not yet deep-covered. REUSE as settled: the 16 confirmed-WRONG, the Gate-A
verified-SOUND (ga_positions, ga_structural, the L0 set per L0_SOUNDNESS_REPORT). Deep-audit the rest +
run the never-completed L1/L2/L3 cheap census. Per-asset method = the SPEC §5 deep unit (census → stratified
sample → read writer → re-derive from upstream → 3 lenses → null/FK → silent-default scan → verdict
SOUND/SUSPECT/WRONG; WRONG/DEFERRED/SOUND for ambiguous) + the downstream-impact chain for each WRONG.
Run layer-by-layer (L1 → L2 → L3 → L4), mostly sequential / parallel-where-file-disjoint, RESUMABLE,
low-concurrency, findings written incrementally. Each layer's gap-fill report comes back for review.
**The ~30+ assets needing deep audit (from the map's PENDING lists):** L1 (~13 ga_* not yet deep), L2 (7
pending), L3 (~6 pending), L4 (6 pending) — exact lists in the gap-fill prompts.
**L5:** OUT. Not audited in this campaign. (A separate one-line structural note only: "L5 untouched; opens
after L0–L4 seal per L5_MIMAMSA_ONBOARDING_HANDOFF.")
**Output:** updated FOUNDATION_ROOT_CAUSE_MAP.md → status COMPLETE-COVERAGE: every L0–L4 asset has a
verdict, every WRONG has an impact chain, the master rebuild schedule is final. → GATE A2 (native+Cowork review).

### PHASE B — CONSOLIDATED REMEDIATION (fix all code, ground-up)
After Gate A2: fix every confirmed-WRONG writer's LOGIC, bottom-up L0→L4, full latitude, per the map's
proposed fixes. Verify each fix by RE-DERIVATION against the existing (buggy) data — prove the fixed code
WOULD produce correct output that differs correctly from what's stored — NO builds during fixing (data is
disposable; builds are deferred to Phase C). Fix code in dependency order so each layer's logic is
validated against correct upstream understanding. Gate at the L2 convergence root (it's been mis-diagnosed
twice; everything above inherits it).

### PHASE C — FULL DAG-RESPECTING REBUILD + SEAL
One end-to-end Build of the native's chart via the Nirmāṇa tracker / orchestrator, running ALL fixed
writers in DAG dependency order in one pass → every asset rebuilt from correct code on correct upstream =
all layers in sync, no cross-layer consistency issues (the native's explicit requirement). SEAL-GRADE
verification (§7.9 live-deployment guard): all assets lit with rows on the live revision == merge SHA, zero
errors, NO degenerate distributions on key columns, FORENSIC 7/7, the campaign watch-list all clear.
→ L0–L4 SEALED SOUND. Native authorizes the seal (not autonomous).

## §3 — THEN (the next campaign, not this one)
L5 Mīmāṃsā opens on the sealed, provably-sound L0–L4 foundation, per L5_MIMAMSA_ONBOARDING_HANDOFF_v1_0.md.
Building it now would be HARMFUL — it would calibrate against corrupted predictions and bake the bugs into
a feedback loop. L5 is the reward for completing this campaign, not part of it.

## §4 — Sequence
```
PHASE A2 — complete the audit (gap-fill, reuse proven, resumable layer-by-layer)
  A2.1  L1 gap-fill deep audit (~13 ga_*) + L1 cheap census   → L1_SOUNDNESS_REPORT → review
  A2.2  L2 gap-fill (7 pending) + L2 cheap census             → L2_SOUNDNESS_REPORT → review
  A2.3  L3 gap-fill (~6 pending) + L3 cheap census            → L3_SOUNDNESS_REPORT → review
  A2.4  L4 gap-fill (6 pending) + confirm L4 census           → L4_SOUNDNESS_REPORT → review
  A2.5  CONSOLIDATE → FOUNDATION_ROOT_CAUSE_MAP status COMPLETE-COVERAGE + final rebuild schedule → GATE A2
PHASE B — fix all code ground-up (re-derivation-verified, no builds), L2 gate → GATE B
PHASE C — one full DAG-respecting rebuild → seal-grade verify → L0–L4 SEALED
THEN  L5 campaign opens.
```

## §5 — What this guarantees the native
Complete coverage (no un-audited asset hiding a bug), a single consolidated fix plan (not piecemeal), a
DAG-respecting rebuild (all layers in sync, no consistency issues), and a sealed foundation — so the L5
investment, when it comes, rests on proven ground. The empty-system window (only the native's chart + unbuilt
demos) makes this the one-time chance to do it with zero migration debt.

---
*End v2.0. Complete the deep audit (gap-fill the ~30+ PENDING assets, reuse the 16 WRONG + Gate-A SOUND),
consolidate to COMPLETE-COVERAGE, fix all code ground-up (re-derivation-verified), one full DAG-respecting
rebuild + seal. L5 entirely out until sealed. Data disposable; code is the deliverable.*
