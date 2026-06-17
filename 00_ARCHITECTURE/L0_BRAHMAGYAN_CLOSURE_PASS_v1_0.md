---
artifact: L0_BRAHMAGYAN_CLOSURE_PASS_v1_0.md
canonical_id: L0_BRAHMAGYAN_CLOSURE_PASS
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-17
authored_for: the L0 closure (Nirīkṣaka-driven audit + native-reviewed close)
purpose: >
  Consolidate and CLOSE L0 Brahmagyan properly before L1 re-close and L2 Bodha. L0 grew to ~20+ assets
  across ~40 reference tables via the autonomous subsystem program — built incrementally by different
  agents, never viewed whole. This pass runs three activities IN ORDER — (A) integrity audit, (B) per-asset
  enrichment-gap audit, (C) cross-asset synergy hunt (strict layer-classification) — then closes L0. It is
  the TEMPLATE for the subsequent L1 closure pass and informs L2 Bodha's projection architecture.
governing_principle: >
  Maximize the value of each L0 asset + find cross-asset synergies, WITHOUT blurring the layer boundary —
  L0 is STATIC GLOBAL reference. A synergy is added to L0 ONLY if it is genuinely chart-agnostic; chart-
  dependent → L1; interpretive-relationship → L2. The layer-separation discipline is the contamination
  guardrail ([[MSR contamination audit]]).
read_in_combination_with:
  - the L0 asset inventory (asset_registry + migrations) — ~20 assets, ~40 reference tables
  - SUBSYSTEM_PROGRAM_ROADMAP + the 7 subsystem master plans (what each L0 asset was SUPPOSED to be)
  - feedback-canonical-or-floor-rule, feedback-swallowed-exception-txn-poison (the integrity failure modes)
why_l0_first: L2 Bodha projects over the deterministic base; you can only design good projection once L0+L1 are coherent + their full offering is known. Closing L0 (then L1) IS L2's requirements-gathering.
---

# L0 Brahmagyan — Closure Pass (A + B + C) v1.0

## §0 — Why this pass exists (the diagnosis)

L0 grew organically: the original 15 bg_* assets + the subsystem program's additions (bg_nakshatra,
bg_transit_engine/rules, bg_prashna_rules + 6 prashna tables, bg_vastu_directions + remedials,
bg_medical_mappings, bg_dignity_reference + 4 sub-tables, bg_nakshatra_medical). Built incrementally by
different swarm agents, integration checked only at the seams. **Confirmed problems already visible:**
seed-vs-built divergence (5+ assets BUILT via migration but absent from `asset_registry_seed.ts` → a
re-seed would lose them); the catalog_status DRAFT gap (systematic); fragmented table surface. The layer
WORKS but is not COHERENT — and you cannot design Bodha's projection over an un-reconciled base. This pass
makes L0 whole, then closes it.

## §A — INTEGRITY AUDIT (Nirīkṣaka — is L0 actually sound?)

For EVERY L0 asset (enumerate the real current set from `asset_registry` WHERE layer='brahmagyan', NOT just
the seed), verify:
1. **Built + populated** — row count > 0 (or service health-probe GREEN); matches its master-plan/spec scope.
2. **Seed-vs-registry-vs-prod consistency** — the asset is in ALL THREE: `asset_registry_seed.ts`, the prod
   `asset_registry` table, and has its data table populated. **Flag every divergence** (the 5+ built-but-
   not-seeded assets are the known case — backfill the seed so a re-seed can't lose them).
3. **catalog_status='CURRENT'** for every built asset (the systematic DRAFT gap — [[project-subsystem-program]]
   catalog rail). DRAFT only if genuinely not-yet-built.
4. **Cited** — every datum has a classical_source (the computed-and-cited hard gate). Sample-audit for
   uncited values + non-canonical substitutes ([[feedback-canonical-or-floor-rule]]).
5. **No silent failures** — grep the L0 writers for `logger.debug`-swallowed DB exceptions / phantom-column
   patterns ([[feedback-swallowed-exception-txn-poison]]); confirm no asset has silently-empty components.
6. **FORENSIC where applicable** — the native-anchored static facts (e.g. nakshatra attrs for Purva
   Bhadrapada) correct.
7. **Idempotency** — ON CONFLICT (L0 pattern) correct; re-run = no duplicates.
8. **Registration completeness** — count_sql, depends_on, scope, asset_type all correctly set (the malformed-
   INSERT class — migration 292 had it).
9. **Orchestrator-resolvable** — get_writer resolves each; the deployed job image contains all L0 writers.
10. **Reconcile fragmentation** — e.g. `reference_nakshatra` (new) vs `reference_nakshatras` (old, writes
    disabled) — confirm one authority, no dead/duplicate tables; same for any other old/new table pairs.
Output: an integrity findings table (asset × each check × pass/fail), with fixes for every fail.

## §B — ENRICHMENT-GAP AUDIT (is each asset at its full computable+citable depth?)

For each L0 asset, against its master plan + classical scope: **is it maximal, or is there computable+citable
content still missing?** (The nakshatra gana/nadi/yoni-gap pattern, generalized.) Per asset, list:
- what the tradition offers that's deterministic + citable,
- what the asset currently captures,
- the GAP (missing attributes/rows/relationships that COULD be computed+cited but aren't).
Apply the hard gate: a gap is only a gap if it's genuinely computable+citable (not interpretive). Output a
per-asset enrichment-gap list, prioritized by value. (Build the high-value gaps now or log for a v2 pass —
native decides per gap.)

## §C — CROSS-ASSET SYNERGY HUNT (the novel value — STRICT layer-classification)

Now that L0 has ~20 assets, find deterministic relationships BETWEEN assets that no single asset holds —
but CLASSIFY each by which layer it truly belongs to (native decision: strict). For each candidate synergy:
- **Describe it:** which assets combine, what deterministic fact emerges (e.g. nakshatra-deity × medical-
  body-part → a deterministic deity→health-domain bridge; dignity-reference × transit-rules → a static
  transit-strength-by-dignity table; yoga-catalog × dosha-catalog → static yoga-dosha-conflict pairs).
- **CLASSIFY the layer it belongs in:**
  - **truly STATIC + chart-agnostic** → a NEW L0 reference (build it here).
  - **depends on THE CHART** → an L1 opportunity (log for the L1 closure pass — do NOT build in L0).
  - **interpretive RELATIONSHIP / synthesis** → an L2 Bodha opportunity (log for Bodha — do NOT build in L0).
- Only the static-classified synergies become new L0 assets/tables (cited, computed, idempotent). The
  L1/L2-classified ones become a logged opportunity register feeding the L1 + L2 closure passes.
This is the L2-Bodha philosophy (convergence/graph/cross-structure) applied WITHIN L0's static domain — but
the layer boundary is held strictly so L2's job doesn't leak into L0. Output: a synergy register (synergy ×
assets × emergent-fact × layer-classification × build-now-or-log).

## §D — CLOSE L0

After A (sound) + B (maximal, gaps built-or-logged) + C (static synergies built, L1/L2 synergies logged):
- All L0 assets: integrity-clean, CURRENT, seed-consistent, cited, FORENSIC-clean, idempotent, orchestrator-
  resolvable, no silent failures, fragmentation reconciled.
- Emit `L0_BRAHMAGYAN_CLOSURE_v1_0.md`: the definitive L0-closed record — final asset inventory (count +
  per-asset row counts), the integrity attestation, the enrichment-gaps-built + the deferred-gap log, the
  static synergies added, and the **L1/L2 opportunity register** (the synergies classified as belonging
  downstream — this is a direct INPUT to the L1 closure pass and the L2 Bodha architecture).
- SEAL L0 (the layer that was never validly sealed before — now it is). Native single end-review.

## §E — Method + rails
- **Nirīkṣaka-driven:** spawn audit sub-agents (read-only for A's discovery, then fix-PRs). The B + C
  audits are analysis → a register; building the static-synergies + high-value-gaps is execution.
- Standards: computed-and-cited hard gate; canonical-or-floor (no substitutes); L0 ON-CONFLICT idempotency;
  orchestrator-native; surgical migrations; seed-consistency mandatory (every registry change → seed patch);
  no silent failures (logger.warning, not debug); FORENSIC; only 482012f1 for native-anchored checks.
- **The layer boundary is the prime guardrail of §C** — when in doubt about a synergy's layer, the stricter
  (downstream) classification wins; an interpretive synergy NEVER goes in L0.
- This pass is the TEMPLATE: the L1 closure pass repeats A+B+C on L1 (consuming C's L1-opportunity register);
  then L2 Bodha is designed with full visibility of the closed L0+L1 offering + the accumulated opportunity
  register (the "clear picture for Bodha" the native wants).

---

*End. Close L0 properly: verify it's SOUND (A), make each asset MAXIMAL (B), find cross-asset SYNERGIES with
strict layer-classification (C) — only static ones in L0, the rest logged for L1/L2 — then SEAL. This makes
L0 coherent, surfaces the downstream opportunity register, and is the requirements-gathering for Bodha. Repeat
on L1, then design L2 with the full picture.*
