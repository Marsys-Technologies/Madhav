---
artifact: MARSYS_CONSOLIDATED_RUNWAY_v1_0.md
canonical_id: MARSYS_CONSOLIDATED_RUNWAY
version: 1.0
status: CURRENT — the single "you are here + what's next" surface
authored_by: Cowork (planning) 2026-06-12
purpose: >
  After many reactive turns of L1-completeness + cockpit repair, consolidate ALL remaining work into
  one dependency-ordered runway, so sequencing is deliberate (not discovered turn-by-turn). Captures
  done / pending / blocked, the gates between them, and the systemic seed-apply hardening that would
  stop the recurring prod-divergence class.
read_with: feedback-l1-l2-relationship-architecture (memory) + the per-area briefs/audits it cites
---

# MARSYS-JIS — Consolidated Forward Runway v1.0

## §0 — Where we are (verified)
The keystone is built: **ga_structural is the complete deterministic relational fabric** — all 30
vargas × 5 ayanamshas, Rahu/Ketu, 8 relationship families, argala, catalog-driven labels, real
fact_ids, two-pass, FORENSIC 7/7, 74,644 rows. **A10/MSR is respecced to projection** (v1.2). The
**Asset Atlas** is built + verified (client-name dropdown, live counts, reconcile-against-count_sql).
The **cockpit progress bar** now reconciles against real data. The architecture is settled
(enumeration-not-predicates; ga_structural=engine, MSR=projection; B.1/SIG.MSR.377 purged).

## §1 — The honest open backlog (everything not done)
Grouped; the §2 sequence orders them.

**A. Verification owed (cheap, immediate):**
- A1. Apply migration 228 (reactivate the 4 chart_facts assets) + confirm /api/cockpit/stats shows 39 assets, the four lit. (Code fix done; prod apply + verify pending.)
- A2. ga_strength count reconciliation — does count_sql now return the writer's 1,330, or still 2,184 (over-broad LIKE filter)? One query.

**B. Pending REBUILD WAVE (the stale cascade — gates L2):**
- B1. ga_strength re-run correctly cascaded `lit→stale` to ga_structural, ga_sade_sati, and ALL L2 Bodha assets. They have data but are marked stale. A rebuild pass must bring them back to `lit` before they're trustworthy / before L2 work resumes.

**C. Systemic hardening (stops the recurring divergence class):**
- C1. **Seed→prod apply hardening.** FOUR times prod registry/throughput diverged from seed/code intent (bo_samvada never-applied; stale throughput; is_active flip; the line-1248 auto-deactivate-on-null-target_table rule). Each cost a diagnostic cycle. ONE-TIME fix: make seed-apply atomic + verified (assert post-state == intended) + no silent state-mutating rules. This is the highest-leverage non-feature item — it prevents future turns being eaten by divergence-chasing.

**D. L1 completeness/hygiene tail (small, real):**
- D1. KP cuspal significators silently dropped on malformed JSON (ga_sensitive) — fix JSON or store flagged skip-row (no-silent-drop).
- D2. `ganita_positions` legacy dual-write — deprecate (obsolete vs chart_facts).
- D3. Scope-cap markers — Prana dasha / D81 "intentionally-not-computed" flags so absence ≠ bug.
- D4. (the two parked items) Mercury vargottama confirmed; bg_signal_type_registry retired — DONE, listed for closure-completeness.

**E. Retrievability pillar (the second pillar — entirely ahead):**
- E1. The new query/retrieval layer over the now-complete L1 base — the whole reason creation was fixed first. Tools that expose every stored category to the LLM (the data-integrity audit found ~30% coverage on the legacy tools, being rebuilt). This is a major workstream, scoped after L1 is sealed + the rebuild wave clears.

**F. L2 Bodha return (the original destination):**
- F1. bo_laksana as a PURE PROJECTION over the corrected ga_structural (no re-firing) — the respecced A10 model. Then the rest of the Bodha DAG (bo_sangati/bimba/karanajala/upaya/samskara/samvada-UCD/pramana_mapa) per the L2 campaign + the §13 design philosophy (convergence/contradiction first-class, graph deepest).

## §2 — The sequenced runway (dependency-ordered; gates marked)

```
WAVE 0 — Stabilize + verify (cheap, unblocks trust)
  A1 apply migration 228 + verify 4 lit ──┐
  A2 ga_strength count reconcile ──────────┤ (both quick; do first)
                                           │
WAVE 1 — Seal L1 (do BEFORE the rebuild wave, so we rebuild on a sound base)
  C1 seed-apply hardening ★ (systemic — stops divergence recurring) ─┐
  D1 KP-JSON silent-drop fix                                          │
  D2 ganita_positions deprecation · D3 scope-cap markers             │
                                                                     │
WAVE 2 — Clear the rebuild wave (GATE for L2)
  B1 rebuild ga_structural + ga_sade_sati + L2 placeholders → lit     │  (needs L1 sealed: WAVE 1)
                                                                     ↓
WAVE 3 — Retrievability layer (the 2nd pillar)
  E1 new query/retrieval tools over the complete L1 base             (needs L1 sealed + rebuild clear)
                                                                     ↓
WAVE 4 — L2 Bodha (the destination)
  F1 bo_laksana projection → then the Bodha DAG                      (needs B1 lit + ideally E1 for serve-time)
```

**Gate logic:**
- WAVE 0 is independent + immediate (verify what just shipped).
- **WAVE 1 (seal L1) before WAVE 2 (rebuild)** — pointless to rebuild ga_structural if the seed path still flips state on re-apply (C1), or before the KP/hygiene fixes, since the rebuild would just have to repeat.
- **WAVE 2 (rebuild) gates WAVE 4 (L2)** — bo_laksana projects ga_structural; it must be `lit` + final first.
- **WAVE 3 (retrievability) can run parallel to WAVE 4's start** but is most valuable once L1 is sealed; it's the second pillar and a major workstream of its own.

## §3 — The single highest-leverage item
**C1 (seed-apply hardening).** It's not a feature, but it's the root of four diagnostic cycles this
arc. Hardening seed→prod (atomic, verified, no silent state flips) converts "discover the next
divergence when the cockpit looks wrong" into "the apply asserts its own correctness." Recommend
doing it in WAVE 1 before any rebuild, so WAVE 2 lands on a trustworthy base.

## §4 — What this runway deliberately does NOT do
- No new GA8 amendments (ga_structural is complete; resist further scope creep there).
- No L3 Kāla / dasha-temporal (deferred by decision — it's a Kāla concern, post-L2).
- No re-opening settled architecture (enumeration/projection/B.1-purge are locked).

## §5 — Recommended next action
Start **WAVE 0** (apply migration 228 + verify the four light up; run the ga_strength count
reconcile query) — closes the loop on what just shipped. Then author the **WAVE 1 seal-L1 brief**
led by C1 (seed-apply hardening). Everything downstream (rebuild → retrievability → L2) sequences
cleanly from there.

---
*End of MARSYS_CONSOLIDATED_RUNWAY v1.0. One picture: ga_structural keystone DONE; remaining =
Wave 0 verify → Wave 1 seal L1 (seed-hardening ★ + hygiene) → Wave 2 clear the stale rebuild cascade
→ Wave 3 retrievability → Wave 4 L2 Bodha. The seed-apply hardening (C1) is the highest-leverage item
— it ends the recurring prod-divergence class that ate four diagnostic cycles. Drive from this, not
turn-by-turn.*
