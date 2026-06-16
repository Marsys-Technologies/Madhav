---
artifact: MARSYS_CONSOLIDATED_RUNWAY_v1_0.md
canonical_id: MARSYS_CONSOLIDATED_RUNWAY
version: 1.1
status: CURRENT — the single "you are here + what's next" surface
execution_mode: CONTINUOUS / AUTONOMOUS — no human gate between waves (native directive 2026-06-12); only dependency gates + Tier-3 escalation rails apply
changelog:
  - v1.1 (2026-06-12): Waves 0-2 marked DONE; §2 rewritten as a CONTINUOUS autonomous runway — no human approval gate between waves (native directive); only dependency gates remain. Migration 229 in flight; Wave 3 (retrievability) → Wave 4 (L2 Bodha) run one after the other.
  - v1.0 (2026-06-12): initial consolidated runway.
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

## §2 — The sequenced runway (CONTINUOUS — no human gates between waves)

**Execution mode (native directive 2026-06-12): run waves continuously, one after the other, NO
human approval gate between them.** Antigravity proceeds Wave 0→1→2→3→4 autonomously under the §C
rails (per AUTONOMOUS_MODE). Only DEPENDENCY gates remain (a wave can't start before its inputs
exist) — those are correctness, not approval. The native reviews retrospectively via the cockpit/
Atlas + Smṛti, not synchronously at each boundary.

```
[DONE] WAVE 0 — Stabilize + verify
  A1 migration 228 applied (4 reactivated, 39 active) ✓ · A2 ga_strength count reconciled (2,184) ✓
[DONE] WAVE 1 — Seal L1
  C1 seed-apply hardening ✓ · D1 KP-JSON fix ✓ · D2 ganita_positions removed ✓ · D3 scope-cap sentinels ✓
[DONE] WAVE 2 — Clear rebuild cascade
  B1 ga_structural lit 75,168 ✓ · ga_sade_sati lit 11,019 ✓
[IN FLIGHT] migration 229 (reap 4 orphaned building→lit) — apply + auto-continue, no gate
─────────────────────────────────────────────────────────────────────────────────────
REMAINING — run CONTINUOUSLY, no stop between:
WAVE 3 — Retrievability layer (2nd pillar)
  E1 new query/retrieval tools over the complete L1 base   (dep: L1 sealed ✓ + rebuild clear ✓ → READY)
        │  continuous, no human gate
        ↓
WAVE 4 — L2 Bodha (destination)
  F1 bo_laksana projection → bo_sangati/bimba/karanajala/upaya/samskara/samvada(UCD)/pramana_mapa
        (dep gate only: bo_laksana needs ga_structural lit ✓; downstream Bodha assets need bo_laksana)
```

**Gate logic (DEPENDENCY gates only — no approval gates):**
- Waves 0–2 are complete. Migration 229 applies and execution continues without waiting for sign-off.
- WAVE 3 and WAVE 4 are both unblocked (L1 sealed + lit). They run continuously. Where they're
  independent they may overlap; where F1 depends on E1 outputs (serve-time exposure of Bodha signals)
  the dependency orders them, but neither waits for a human.
- Within WAVE 4, the Bodha DAG self-orders: bo_laksana first (root), then the fan-out, per the L2
  campaign — the orchestrator runs it from depends_on automatically.

## §3 — The single highest-leverage item
**C1 (seed-apply hardening).** It's not a feature, but it's the root of four diagnostic cycles this
arc. Hardening seed→prod (atomic, verified, no silent state flips) converts "discover the next
divergence when the cockpit looks wrong" into "the apply asserts its own correctness." Recommend
doing it in WAVE 1 before any rebuild, so WAVE 2 lands on a trustworthy base.

## §4 — What this runway deliberately does NOT do
- No new GA8 amendments (ga_structural is complete; resist further scope creep there).
- No L3 Kāla / dasha-temporal (deferred by decision — it's a Kāla concern, post-L2).
- No re-opening settled architecture (enumeration/projection/B.1-purge are locked).

## §5 — Next action (CONTINUOUS — autonomous)
Waves 0–2 are DONE. Migration 229 applies and execution **continues without a human gate** into:
**WAVE 3 (retrievability layer) → WAVE 4 (L2 Bodha), run one after the other autonomously** under the
§C rails. Cowork authors the WAVE 3 brief, then the WAVE 4/bo_laksana brief, and Antigravity executes
them continuously — no stop for sign-off between waves. The native reviews retrospectively via the
cockpit/Atlas + Smṛti. The only pauses are dependency gates (a wave's inputs must exist) and the
Tier-3 escalation rails (genuine ambiguity / destructive ops / architecture change) per AUTONOMOUS_MODE.

---
*End of MARSYS_CONSOLIDATED_RUNWAY v1.1. One picture: ga_structural keystone + L1-seal + cockpit-truth
DONE (Waves 0–2). Remaining runs CONTINUOUSLY with NO human gate between waves: migration 229 →
Wave 3 retrievability → Wave 4 L2 Bodha. The seed-apply hardening (C1) is the highest-leverage item
— it ends the recurring prod-divergence class that ate four diagnostic cycles. Drive from this, not
turn-by-turn.*
