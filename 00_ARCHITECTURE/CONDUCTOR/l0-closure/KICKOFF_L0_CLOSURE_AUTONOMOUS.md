# L0 Brahmagyan — Autonomous Closure Pass (Audit → Fix → Enrich → Recommend)

**Paste this entire file as the kickoff prompt in Claude Code (Antigravity). It is a single, long-running,
FULLY AUTONOMOUS pass. No human gates until completion; the native reviews ONCE at the end.**

---

## ROLE + OBJECTIVE

You are the Sūtradhāra conductor for the **L0 Brahmagyan Closure Pass**. Take L0 — which grew to ~21 assets
across ~40 reference tables via the autonomous subsystem program, built incrementally and never viewed whole
— and make it **sound, maximal, coherent, and CLOSED**. Run four phases in order, fully autonomously, spawning
sub-agents (Agent tool) for parallel work. Halt-and-log ONLY on a hard structural block. Produce, at the end,
`00_ARCHITECTURE/L0_BRAHMAGYAN_CLOSURE_v1_0.md` (the sealed record) for the single native end-review.

Read first: `00_ARCHITECTURE/L0_BRAHMAGYAN_CLOSURE_PASS_v1_0.md` (the governing plan — A/B/C/D), CLAUDE.md §C,
CURRENT_STATE + git for true state. Standards (inherited, enforced by you not a human): computed-and-cited
HARD GATE (a datum stored only if deterministically computed + classically cited; uncited → floor NULL+reason,
NEVER fabricate); canonical-or-floor (no non-canonical substitutes — a value computed by a different method
than the cited rule FAILS the gate); L0 ON-CONFLICT idempotency; orchestrator-native (@register, FROZEN
contract — HALT if a contract change seems needed); surgical migrations only (NEVER deploy.yml-auto / bulk
migrate.ts); seed-consistency MANDATORY (every registry change → patch `asset_registry_seed.ts`); no silent
failures (logger.warning not debug); only `482012f1-710e-4a25-994a-93821f5871aa` for native-anchored checks;
`362f9f17` is a dead phantom; merge-verify every PR (`gh pr view N --json mergeCommit,state`).

---

## PHASE 1 — FULL INTEGRITY AUDIT (read-only discovery → findings table)

Enumerate the TRUE current L0 set: `SELECT asset_id, layer, count_sql, target_floor, catalog_status,
is_active, scope, asset_type FROM asset_registry WHERE layer='brahmagyan'` on prod (Cloud SQL proxy; password
from Secret Manager `amjis-db-password/3`). For EVERY L0 asset, check (produce a findings table: asset × check
× pass/fail × evidence):

1. **count_sql VALID** — execute each asset's count_sql; flag SYNTAX ERRORS (known red: `bg_prashna_rules`
   "Praśna-sūtrāvalī", `bg_vastu_directions` "Vastu-dik" — both FAILED with "syntax error at or near"; likely
   malformed multi-table SUM assembly). Fix-target.
2. **target_floor == achieved count** — flag every asset where count > target_floor (bar overfills): known
   `bg_texts` 10,651/8,193, `bg_dasha_systems` 18/15, `bg_compendium_index` 9,538/1,755, `bg_transit_rules`
   41/37. target_floor must be set to the achieved count (floors-aspirational). Fix-target.
3. **build-state (asset_throughput) fresh** — flag "build-state stale" / Last-Built "—" despite full data:
   known `bg_transit_engine` (9/9 stale), `bg_nakshatra_medical` (27/27 stale). The throughput row is out of
   sync with the data. Fix-target.
4. **catalog_status = 'CURRENT'** for every built asset (the systematic DRAFT-omission gap). Fix-target.
5. **SEED-vs-REGISTRY-vs-PROD consistency** — the asset must be in ALL THREE (`asset_registry_seed.ts`, prod
   `asset_registry`, and have a populated data table). **Known divergence: `bg_transit_engine`,
   `bg_transit_rules`, `bg_prashna_rules`, `bg_vastu_directions`, `bg_medical_mappings` are BUILT via migration
   but ABSENT from the seed** → a re-seed would lose them. Backfill the seed for EVERY built-but-unseeded
   asset. Fix-target.
6. **CITED + canonical** — sample each asset's rows: every datum has a classical_source; no uncited values; no
   non-canonical substitutes (a value computed by a method ≠ the cited rule). Per the canonical-or-floor rule.
7. **No silent failures** — grep every L0 writer for `logger.debug`-swallowed DB exceptions + phantom-column
   patterns (the ga_condition `INTRANS_INERROR` class); confirm no asset has silently-empty components. Flip
   swallowed-DB-error logging to `logger.warning`. Fix-target.
8. **Malformed-INSERT class** — audit each registry migration's column-list/values alignment (migration 292
   had this); confirm no mis-set count_sql/depends_on/scope.
9. **Idempotency** — L0 ON-CONFLICT correct; re-run = 0 inserts.
10. **Orchestrator-resolvable** — `get_writer` resolves each L0 writer; the deployed Cloud Run Job image
    contains all of them.
11. **Fragmentation / dead tables** — flag old-vs-new table pairs (e.g. `reference_nakshatras` (old, writes
    disabled) vs `reference_nakshatra` (new)); confirm one authority, no dead/duplicate tables.
12. **FORENSIC** — native-anchored static facts correct (e.g. Purva Bhadrapada nakshatra attrs).

Output Phase-1: `00_ARCHITECTURE/CONDUCTOR/l0-closure/L0_INTEGRITY_FINDINGS_v1_0.md` — the full findings table
+ a prioritized fix-list. (Read-only — no changes yet.)

---

## PHASE 2 — FIX (remediate every Phase-1 finding, autonomously)

Fix every finding from Phase 1, in dependency-safe order, each as a surgical change:
- **count_sql syntax errors** → correct the malformed count queries (the 2 red ones + any others found).
- **target_floor** → `UPDATE asset_registry SET target_floor = <achieved count>` per over-target asset.
- **build-state stale** → re-sync the asset_throughput rows (re-run the orchestrator build for those assets so
  the throughput update + last_built land, OR a targeted throughput-fix migration).
- **catalog_status** → set 'CURRENT' for every built asset missing it.
- **seed divergence** → add every built-but-unseeded asset to `asset_registry_seed.ts` (full correct entry:
  count_sql, target_floor, catalog_status, depends_on, scope, asset_type) so a re-seed is faithful.
- **silent-failure logging** → flip swallowed-DB-error `logger.debug` → `logger.warning` across L0 writers.
- **malformed INSERTs / fragmentation / dead tables** → corrective migrations; reconcile to one authority.
Each fix: surgical migration applied to prod (recorded in `_migrations_applied`) + the seed patched + a PR.
Batch related fixes; CI green; merge-verify each. Re-run the relevant cockpit/count checks to confirm GREEN.
After Phase 2: every L0 asset shows correct count, lit/green, fresh build-state, on prod. Verify on localhost
cockpit (`/clients/482012f1/nirmana`, expand Brahma Jñāna — all 21 green, no red/stale/overfill).

---

## PHASE 3 — ENRICHMENT AUDIT + BUILD (maximize each asset, esp. the new ones)

For EACH L0 asset (focus on the NEW subsystem ones — transit, prashna, vastu, medical, dignity, nakshatra —
where depth is most likely incomplete), against its subsystem master plan + classical scope, identify whether
it is at FULL computable-and-cited depth or has gaps. Produce per-asset:
- what the tradition offers that's deterministic + citable,
- what's currently captured,
- the GAP (missing attributes/rows/relationships that COULD be computed+cited but aren't).
Apply the hard gate: a gap counts only if genuinely computable + citable (not interpretive). Examples of likely
gaps in the new assets: bg_transit_rules (missing Ashtakavarga-Kakshya rows? all-planet special-cycles?),
bg_prashna_rules (all Prashna-Lagna methods present? full Tajik judgment set?), bg_vastu_directions (45-devata
mandala + marma complete?), bg_medical_mappings (all graha→dhatu/organ + drekkana/D6 body-parts?),
bg_dignity_reference (lajjitaadi/sayanadi were deferred — still gaps?), bg_nakshatra (any attribute still null
that should be computed?).

**BUILD the high-value, clearly-deterministic+citable gaps now** (new reference rows/tables, cited, ON-CONFLICT,
seed-patched, registry-registered with correct count_sql/target_floor/catalog_status/CURRENT). **LOG the lower-
value or ambiguous gaps** in the enrichment register for a v2 native decision. Output:
`00_ARCHITECTURE/CONDUCTOR/l0-closure/L0_ENRICHMENT_REGISTER_v1_0.md`.

---

## PHASE 4 — CROSS-ASSET SYNERGY HUNT + RECOMMENDATIONS (strict layer-classification)

Find deterministic relationships BETWEEN L0 assets that no single asset holds. For each candidate synergy:
describe it (which assets combine → what deterministic fact emerges, e.g. nakshatra-deity × medical-body-part
→ deity→health-domain bridge; dignity-reference × transit-rules → static transit-strength-by-dignity table;
yoga-catalog × dosha-catalog → static yoga-dosha-conflict pairs; vastu-direction × graha → direction-strength).
**CLASSIFY each by the layer it TRULY belongs to (strict — when in doubt, the downstream/stricter layer wins):**
- **truly STATIC + chart-agnostic** → a NEW L0 reference → BUILD it (cited, idempotent, seeded, registered).
- **depends on THE CHART** → an L1 opportunity → LOG only (do NOT build in L0).
- **interpretive RELATIONSHIP/synthesis** → an L2 Bodha opportunity → LOG only (do NOT build in L0).
The layer boundary is the prime guardrail — an interpretive synergy NEVER goes in L0 (the contamination
guardrail). Output: `00_ARCHITECTURE/CONDUCTOR/l0-closure/L0_SYNERGY_REGISTER_v1_0.md` — synergy × assets ×
emergent-fact × layer-classification × built-or-logged. The L1/L2-classified entries become the OPPORTUNITY
REGISTER that feeds the eventual L1 closure pass + L2 Bodha architecture.

Also produce **RECOMMENDATIONS** (forward-looking, not built): anything structural you'd advise for L0's
long-term coherence (table consolidation, a unified directional authority backing Dik-Bala/Disha-Shul/Vastu,
naming standardization, etc.) — logged, not executed without native sign-off.

---

## CLOSE

When Phases 1–4 are complete (L0 sound + maximal + synergies-classified):
- Emit `00_ARCHITECTURE/L0_BRAHMAGYAN_CLOSURE_v1_0.md`: final asset inventory (count + per-asset row counts),
  the integrity attestation (all Phase-1 findings resolved), the enrichment built + the deferred-gap register,
  the static synergies added, the **L1/L2 opportunity register**, and the recommendations.
- Run a Vimarśaka IS.8(b) red-team across the closed L0.
- Update CURRENT_STATE; SEAL L0 (validly, for the first time — it was never properly closed before).
- Present to the native for the SINGLE end-review with: the findings table, what was fixed, what was enriched,
  the synergy/opportunity register, and the recommendations.

---

## AUTONOMY + RAILS

Fully autonomous; spawn sub-agents for parallel audit + fix work; per-phase Smṛti notes in
`00_ARCHITECTURE/CONDUCTOR/l0-closure/smriti/`. MAX_FIX_ATTEMPTS 5 per finding, then HALT-and-log. Halt-and-log
ONLY on: a frozen-contract change appearing necessary (native decision); an uncited value that can't be sourced
(floor it — only a structural block halts); a count that can't be reconciled; context budget (re-paste this file
to resume — the registers + Smṛti persist progress). Enforce the hard gate (uncited → floor, never fabricate)
and canonical-or-floor (no substitutes) throughout — these are the integrity spine, especially in Phase 3
enrichment. Phase 4's layer-classification strictness is non-negotiable: L2's job never leaks into L0. One
native review, at the very end.

Begin: Phase 1, the full integrity audit (read-only). Report the findings table before opening Phase 2.
