# L1 Gaṇita — Autonomous Closure Pass (Audit → Fix → Enrich-verify → Synergy → Seal)

**Paste this entire file as the kickoff prompt in Claude Code (Antigravity). Single, long-running, FULLY
AUTONOMOUS pass. No human gates until completion; the native reviews ONCE at the end. This is the L0 closure
template (proven — L0 sealed @ `a6f564cc`) applied to L1, updated with everything learned since.**

---

## ROLE + OBJECTIVE

You are the Sūtradhāra conductor for the **L1 Gaṇita Closure Pass**. Take L1 — the per-chart deterministic fact
layer — and make it **sound, coherent, and CLOSED**, as L0 was. Run five phases in order, fully autonomously,
spawning sub-agents (Agent tool) for parallel work. Halt-and-log ONLY on a hard structural block. Produce, at
the end, `00_ARCHITECTURE/L1_GANITA_CLOSURE_v2_0.md` (re-sealed record — supersedes the premature v1.0) for the
single native end-review.

**Read first:** `L0_BRAHMAGYAN_CLOSURE_PASS_v1_0.md` (the A/B/C/D method this mirrors); `L0_BRAHMAGYAN_CLOSURE_
v1_0.md` §5 (the **L1 Opportunity Register** — INPUT to Phase 4); `L1_ENRICHMENT_AMENDMENTS_v2_0.md` (the
per-varga strength/avastha + sensitive-point enrichment — ALREADY BUILT + sealed @ PR #298, Phase 3 here
VERIFIES it); `SIX_SUBSYSTEM_BUILD_CLOSE_v1_0.md` (**Gate-3 already PASSED** — the 8 subsystem assets are built
+ prod-verified for the native; Phase 1 here VERIFIES, does not rebuild); `OPEN_ITEMS_REGISTER_v1_0.md` (the
cockpit findings + hygiene items this pass sweeps — esp. Group A0); `L1_GANITA_CLOSURE_v1_0.md` (PREMATURE seal —
read for the 9-asset inventory + canonical row counts, SUPERSEDED); CLAUDE.md §C, CURRENT_STATE + git.

**CRITICAL CONTEXT — what is ALREADY DONE (do NOT rebuild; VERIFY):**
- **Gate-3 (8 subsystem assets) is BUILT + SEALED** for 482012f1: ga_yoga(5), ga_prashna(0-correct),
  ga_structural(75,168), ga_condition(45), ga_transit_anchors(45), ga_vastu(40), ga_medical(45),
  ga_sade_sati(11,019). FORENSIC 7/7, Vimarśaka clean. Phase 1 confirms these are lit on prod; it does NOT
  rebuild them.
- **L1 Enrichment Phase 3 is BUILT + SEALED** (PR #298): per-varga Ashtakavarga, per-varga Baladi/Deeptadi
  avastha, 5 sensitive-point categories; floored items carry `floored: ...` reasons. Phase 3 here VERIFIES on
  prod + folds into the inventory; it does NOT rebuild.

**Standards (enforced by you, not a human):** computed-and-cited HARD GATE (uncited → floor NULL+reason, NEVER
fabricate); canonical-or-floor (a value by a method ≠ the cited rule FAILS the gate); **L1 idempotency =
per-chart DELETE-then-INSERT scoped to (chart_id × natural key)** — rebuild REPLACES, never accretes;
**L1-is-authority within L1** (a ga_ asset citing another's fact REFERENCES the fact_id, never re-derives — the
MSR-drift / `dignity_status` trap); orchestrator-native (@register, FROZEN contract; the `owns_conn` guard means
the orchestrator owns the txn — writers never commit; HALT if a contract change seems needed); **surgical
migrations only — pick numbers ABOVE main's current max (main is at 307; start at 308)**; ledger-reconcile
(`_migrations_applied` with correct SHA — L0's lesson: data-effects can be on prod while the ledger isn't);
seed-consistency MANDATORY; **no silent failures** (logger.warning not debug — the wrong-WHERE-clause /
phantom-column / txn-poison class); only `482012f1`; FORENSIC 7/7 holds; merge-verify; **PROD-VERIFY before
claiming seal**.

---

## PHASE 1 — FULL INTEGRITY AUDIT (read-only → findings table)

Enumerate the TRUE current L1 set: `SELECT asset_id, count_sql, target_floor, catalog_status, is_active, scope,
asset_type FROM asset_registry WHERE layer='ganita'` on prod. For EVERY L1 asset (the 17 in the cockpit + service),
check (findings table: asset × check × pass/fail × evidence):

1. **count_sql VALID + CHART-SCOPED** — execute each; flag syntax errors AND any count not scoped to chart_id
   (the L1 trap → cockpit "NOT MIGRATED"). Fix-target.
2. **target_floor == achieved count** for 482012f1. KNOWN STALE/OVERFILL from cockpit inspection (Group A0-2/A0-4):
   **Graha-sthāna 530>50**, **Saṃracanā/Structural 87,169>74,644** (note: seed says 74,644 but prod shows 87,169
   — reconcile; ga_structural grew), **ga_yoga 5 but floor 50** (floor should be 5 — only Yuga Nabhasa fires,
   that is CORRECT not a gap). Set each floor = achieved count. Fix-target.
3. **build-state (asset_throughput) fresh** per chart. KNOWN STALE from cockpit (Group A0-3, ~5 assets):
   **Sāḍesātī, Saṃracanā, Nakṣatra-Paṭala (Last-Built "—"), Vastu-graha-dik-mapa, Gochara/transit-anchors** —
   data present + correct, throughput record stale (mostly subsystem assets built outside the orchestrator
   throughput-write path; same class as L0's bg_transit_engine fix). Re-sync. Fix-target.
4. **catalog_status='CURRENT'** for every built asset.
5. **The ga_prashna 0-rows render** (Group A0-4): ga_prashna=0 is CORRECT (natal chart, no horary → 0 rows,
   Vimarśaka RT-7). The cockpit renders 0-rows as "NOT BUILT red" — a DISPLAY bug, not a data bug. Audit whether
   the registry/state can signal "0-rows-is-valid-built" for ga_prashna (e.g. a state/catalog flag the cockpit
   reads) so it stops showing red. Log as a cockpit-render fix (may be a small UI change, separate PR) — do NOT
   fabricate prashna rows to make it green.
6. **CITED + canonical** — sample rows; floored items show reason not a fabricated value (the per-varga floors
   from PR #298: Kala/Cheshta, D1-only avasthas, Vighati).
7. **No silent failures** — grep L1 writers for `logger.debug`-swallowed DB exceptions + phantom-column /
   wrong-WHERE-clause patterns (the `dignity_status`→`dignity` class). Flip to warning.
8. **L1-is-authority WITHIN L1** — any ga_ asset consuming another's fact REFERENCES the fact_id (Deeptadi reads
   graha_dignity_per_varga; per-varga dignity reads ga_vargas placement). Sample-verify references resolve + agree.
9. **Idempotency** — DELETE-then-INSERT correct; re-run for 482012f1 = same counts, no accretion/dupes.
10. **Orchestrator-resolvable + the `owns_conn` guard** holds for every writer; deployed job image contains all.
11. **⭐ LIGHT→HEAVY writer audit (Group B6)** — ga_sensitive was converted light→heavy (5 per-ayanamsha substeps,
    independent commits) to be crash-resilient (the orphaned-txn incident). Audit which OTHER multi-ayanamsha L1
    writers still loop 5 ayanamshas in ONE transaction (same orphaned-txn + Cloud-SQL-timeout exposure that hit
    ga_sade_sati's 87-min build). Flag candidates for the same heavy split (build-it if clearly high-value, else
    LOG for a follow-up).
12. **Graha-naming heterogeneity** (SIX_SUBSYSTEM_CLOSE §6.2) — ga_condition uses 'Sun'/'Saturn' (cap),
    ga_transit_anchors uses 'sun'/'saturn' (lower), ga_yoga uses JSONB. Pre-existing convention gap. LOG for L2
    Bodha awareness (L2 normalizes via fact_subject on join) — fix in L1 only if cheap + safe; else log.
13. **Fragmentation / dead tables** — one authority; no dupes.
14. **FORENSIC 7/7** holds at L1.
15. **Canonical row-count reconcile** vs L1_GANITA_CLOSURE_v1_0 baselines + the Gate-3 (86,367) + enrichment rows;
    flag unexplained drift.

Output: `00_ARCHITECTURE/CONDUCTOR/l1-closure/L1_INTEGRITY_FINDINGS_v1_0.md` (read-only — no changes yet).

---

## PHASE 2 — FIX (remediate every Phase-1 finding)

Each surgical, dependency-safe, migration number ≥ 308, ledger reconciled, seed patched, PR, CI green,
merge-verify. Sweep: count_sql chart-scoping; **target_floors → achieved** (Graha-sthāna→530, Structural→actual
prod count, ga_yoga→5, + any others); **throughput re-sync** (the ~5 stale subsystem assets); catalog_status
CURRENT; logger.warning; fragmentation. **Also fold the two L0 floor touch-ups (Group A0-1):** bg_reference→1,485
and bg_ontology→623 had NULL floors → empty bars (sealed L0, so a tiny disclosed micro-fix migration, native
aware). The ga_prashna 0-rows cockpit-render fix (finding #5) may be a separate UI PR — coordinate, don't block
the data seal on it. After Phase 2: cockpit `/clients/482012f1/nirmana` Gaṇita panel all green — no red/stale/
overfill; bars filled; ga_prashna no longer false-red.

---

## PHASE 3 — ENRICHMENT: VERIFY-AND-FOLD (NOT rebuild)

The per-varga strength/avastha + sensitive-point completeness is already built + sealed (PR #298). Here:
1. **Verify on prod** for 482012f1: per-varga Ashtakavarga (~675), avastha_baladi/deeptadi per-varga, the 5
   sensitive categories; floored items show `floored: ...` NOT a number (the integrity gate, on prod).
2. **Fold into the closure inventory** (categories + counts + citations).
3. **Audit for any REMAINING computable+citable gap** across L1 assets vs their master plans (e.g. ga_medical
   lacking house-health + sign-body-part per-chart derivation — data-investigation Q8). BUILD high-value
   clearly-deterministic+citable gaps (delete-then-insert, cited, seed+registry patched); LOG the rest. Output:
   `00_ARCHITECTURE/CONDUCTOR/l1-closure/L1_ENRICHMENT_REGISTER_v1_0.md`.

---

## PHASE 4 — CROSS-ASSET SYNERGY HUNT + RECOMMENDATIONS (strict layer-classification)

CONSUME the input registers first: L0's §5 (L1-OPP-001 dignity×transit-rules; L1-OPP-002 nakshatra→vimshottari-
lord→dhatu chain) + the L1 enrichment register. Then hunt NEW deterministic relationships BETWEEN L1 assets
(e.g. per-varga strength × per-varga dignity → per-varga composite-fitness; sensitive-point × house-lord →
significator bridge). **CLASSIFY each strictly:**
- **per-chart deterministic** → an L1 fact → BUILD (delete-then-insert, cited, seeded, chart-scoped count_sql).
- **interpretive RELATIONSHIP/synthesis** → an L2 Bodha opportunity → LOG only (the contamination guardrail).
- (No static→L0 bucket — L0 is sealed. A genuinely-static gap → LOG as an L0-reopen recommendation for native
  sign-off; do NOT build into sealed L0.)
Output: `00_ARCHITECTURE/CONDUCTOR/l1-closure/L1_SYNERGY_REGISTER_v1_0.md` — synergy × assets × emergent-fact ×
layer-classification × built-or-logged. The L2-classified entries = the OPPORTUNITY REGISTER feeding L2 Bodha
(also fold in SIX_SUBSYSTEM_CLOSE §6.2 graha-naming normalization as an explicit L2 join note). Plus
RECOMMENDATIONS (forward-looking, logged, not built without sign-off).

---

## CLOSE

When Phases 1–4 complete:
- Emit `00_ARCHITECTURE/L1_GANITA_CLOSURE_v2_0.md` (supersedes v1.0): final asset inventory (per-asset row counts
  incl. Gate-3 subsystem assets + enrichment), integrity attestation (all Phase-1 findings resolved),
  enrichment-folded + deferred-gap register, per-chart synergies built, the **L2 Bodha opportunity register**,
  recommendations, the PROD-VERIFY table, FORENSIC 7/7 attestation.
- Vimarśaka IS.8(b) red-team across closed L1.
- Update CURRENT_STATE; SEAL L1 (validly — superseding the premature v1.0 seal).
- Present to native for the SINGLE end-review: findings table, fixes, enrichment-verified, synergy/opportunity
  register, recommendations, prod-verify table.

---

## AUTONOMY + RAILS

Fully autonomous; sub-agents for parallel audit+fix; per-phase Smṛti in `…/l1-closure/smriti/`. MAX_FIX_ATTEMPTS
5 per finding then HALT-and-log. Halt-and-log ONLY on: a frozen-contract change appearing necessary; an uncited
value that can't be sourced (floor it); a count that can't be reconciled; an L0-reopen needing sign-off; context
budget (re-paste to resume — registers + Smṛti persist). Enforce the hard gate + canonical-or-floor +
L1-delete-then-insert + L1-is-authority + prod-verify-before-seal + ledger-reconcile throughout. Phase 4's
layer-classification strictness is non-negotiable: L2's job never leaks into L1; sealed L0 is never silently
reopened. Never rebuild what's already sealed (Gate-3 subsystems, PR #298 enrichment) — VERIFY them. One native
review, at the end.

Begin: Phase 1, the full integrity audit (read-only). Report the findings table before opening Phase 2.
