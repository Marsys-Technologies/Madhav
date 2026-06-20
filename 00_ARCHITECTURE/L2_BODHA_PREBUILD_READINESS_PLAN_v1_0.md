---
artifact: L2_BODHA_PREBUILD_READINESS_PLAN_v1_0.md
canonical_id: L2_BODHA_PREBUILD_READINESS_PLAN
version: 1.0
status: PLAN_FOR_NATIVE_REVIEW (everything to do BEFORE the L2 Bodha buildout begins in Antigravity)
authored_by: Cowork (grounded in live repo state) 2026-06-19
purpose: >
  The complete, sequenced readiness plan to take L2 Bodha from "all 9 briefs authored (planning done)" to
  "ready to execute in Antigravity." Covers: git/branch housekeeping (the uncommitted work + the recovery
  branch), the schema-migration build (the empty bodha_* tables → enriched contract), the new assets (bo_drishti,
  bo_anveshana), the orchestrator/registry/seed wiring, prod-verification, the build-order, and the seal. Plus
  surfaced items the native may not have listed.
grounded_against:
  - git: on branch `recovery/pre-l2-stash-salvage`, 16 commits BEHIND origin/main, 18 untracked files (all our L2 docs)
  - orchestrator: @register + WriterBase (FROZEN), 8 bo_*.py scaffold files present
  - asset_registry_seed.ts (the DAG depends_on + seed) + numbered registry migrations
  - migration trees: platform/migrations/ is CANONICAL (max 324); platform/supabase/migrations/ is OLDER (max 241)
  - no L2_BODHA_CLOSE artifact exists yet
---

# L2 Bodha — Pre-Build Readiness Plan v1.0

## §0 — Where we are (verified)
**Planning is COMPLETE: all 9 per-asset briefs + 6 governing docs authored.** But NOTHING is built or committed.
The work sits UNCOMMITTED on branch `recovery/pre-l2-stash-salvage` (16 commits behind main, 18 untracked files).
The 8 original bo_*.py are SCAFFOLDS (our briefs specify rewrites); bo_drishti + bo_anveshana are NEW (no files
yet). The bodha_* tables exist (mig 226) but EMPTY and at the OLD schema (our redesign supersedes them).

## §1 — HOUSEKEEPING / HYGIENE (do FIRST — the foundation everything sits on)

### H1 — Commit the planning work + get onto a clean branch (the uncommitted-changes fix)
The 18 untracked L2 docs are valuable and UNCOMMITTED on a recovery branch behind main. Steps:
1. **Sync with main first.** `recovery/pre-l2-stash-salvage` is 16 behind origin/main — rebase/merge main in (or
   better: cut a FRESH branch off origin/main and move the docs there). The L2 build must start from current main
   (which has ga_structural v2.0, the 14 L1 assets, the retrieval layer, migrations through 324).
2. **Create the L2 working branch** off current main: `feature/l2-bodha` (or per the branch-isolation policy —
   each parallel stream owns its branch).
3. **Commit the planning docs** (the 9 briefs + 6 governing docs + this plan) as a docs-only commit. They are the
   governing artifacts the build executes against — they belong in the repo, on main eventually.
4. **`test-results/`** is junk (untracked) — gitignore or delete; do not commit.

### H2 — Resolve the two-migration-tree confusion (a real footgun)
**`platform/migrations/` is the CANONICAL tree (max 324); `platform/supabase/migrations/` is OLDER (max 241).**
The bodha_* tables (mig 226) live in supabase/migrations. New L2 migrations MUST go in `platform/migrations/`
numbered from 325+. **Document which tree is authoritative in every migration-writing brief** (avoid the
"two migrations both numbered 174" bug from the L0FR era). Verify the actual max on PROD before numbering.

### H3 — Prod == main verification (the seed→prod-divergence guard)
Before building: confirm `git log origin/main` HEAD == what's deployed on prod (the seed→prod path has diverged
before — handoff warns of it). Confirm migrations through 324 are APPLIED on prod, not just on disk. Use
`/api/cockpit/stats?chart_id=482012f1-...` for live asset state.

### H4 — Branch/worktree hygiene (the 30+ stale branches)
There are 30+ branches (chore/*, feature/*, brahma/*). NOT blocking L2, but per the Tier-B branch audit
([[project-tier-b-branch-audit-pending]]) they should be triaged in their own session. Flag, don't block.

## §2 — THE SCHEMA BUILD (the bodha_* tables → the enriched contract)
The empty mig-226 tables are at the OLD schema; L2_BODHA_SCHEMA_REDESIGN supersedes them. Because they're EMPTY,
redefine freely.

### S1 — Author the migration set (platform/migrations/, 325+)
One migration (or a small set) that DROP+CREATEs (or ALTERs) every bodha_* table to the enriched schema, PLUS:
- the cross-cutting spine columns (fact_kind, source_l1_asset, **source_subsystem**, classical_sources_jsonb, epistemic_jsonb, signal_summary_text, signature_tier, valence, …);
- the NEW tables: bodha_question_lenses (bo_drishti), bodha_chart_gestalt (bo_samvada thin writer), bodha_discoveries + bodha_anomalies (bo_anveshana), the evidence-ledger columns/table (bo_sangati), the cross-subsystem edge support (bo_karanajala), bodha_central_dynamics + bodha_cdlm_pivots + bodha_cdlm_propagation (CDLM §C);
- drop the orphan signal_type_registry (G52 eliminated);
- the indexes (S5: every filter/rank column indexed; HNSW for vectors; chart_id leading for S2).
**The S2 NEXT_PUBLIC-style gotcha doesn't apply (server-side), but verify each promised table EXISTS after apply (the migration-promise-audit lesson).**

### S2 — The embedding shared-constant module (storage §4 / bo_samskara)
Create the single pinned embedding-config module (EMBEDDING_MODEL/VERSION/DIM) imported by bg_texts + bo_samskara; add the cross-layer consistency CI check. Do the classical_chunks cleanup (retire/repoint the stale ivfflat table).

## §3 — THE NEW + REWRITTEN WRITERS
- **Rewrite the 8 scaffold writers** per their briefs (bo_laksana full-projection; bo_sangati evidence-ledger; bo_karanajala graph + cross-subsystem edges; bo_bimba nodes-face; bo_samskara real Vertex embeddings; bo_upaya R1-R5; bo_samvada thin-writer gestalt; bo_pramana_mapa the conscience).
- **Author the 2 NEW writers:** bo_drishti (lens), bo_anveshana (discovery). Both `@register` + WriterBase conforming.
- **formulas.py additions:** evidence_ledger_formula_v1, gestalt_formula_v1, non_obviousness_formula_v1 (+ confirm salience/linkage/convergence/centrality/resonance present).

## §4 — ORCHESTRATOR / REGISTRY / SEED WIRING
### O1 — Orchestrator: NO contract change (FROZEN — confirmed).
All 10 writers (8 rewritten + 2 new) conform to @register + WriterBase. The orchestrator is untouched — it
self-discovers + self-orders from depends_on. **If any writer seems to need a contract change → STOP, raise.**

### O2 — asset_registry_seed.ts — the DAG + seed (this is where depends_on LIVES, not just migrations)
Update `platform/scripts/seed/asset_registry_seed.ts`:
- ADD the 2 new assets (bo_drishti, bo_anveshana) with their depends_on (drishti: [bo_laksana, bo_sangati, bo_karanajala]; anveshana: all producing bo_* ).
- The 2 SEED FIXES: bo_upaya owns bodha_rm_resonances + summed count_sql; bo_samvada → UCD/gestalt (off resonances).
- Each asset's count_sql = SUM across its tables (the multi-table summed-count rule); target_floor = achieved-after-build (aspirational).
- The DAG order: bo_laksana → fan-out (sangati/bimba/karanajala/samskara/samvada) → bo_upaya + bo_drishti → bo_anveshana → bo_pramana_mapa (last). Verify the orchestrator resolves this from depends_on.

### O3 — Registry migration — seed the new assets into asset_registry (a 325+ migration mirroring the .ts seed).

## §5 — RETRIEVAL LAYER (the second pillar — built WITH the assets, not after)
Extend `platform/src/lib/retrieval/registry/layers/L2_bodha/` with the tools each brief specifies (query_msr,
query_domain_evidence, query_cross_subsystem, query_lens, query_ucd, query_zoom, query_remedies,
query_discoveries, query_anomalies, the recursive-traversal primitive, semantic search, …) + extend the coverage
gate (every bodha_* table + every source_subsystem reachable). **F1 (the retrieval de-dup principle) is HELD for
the retrieval-strategy doc — note it, don't fold into per-asset briefs.**

## §6 — BUILD + VERIFY + SEAL
1. **Bring the Cloud SQL proxy up; apply the 325+ migrations surgically to prod; readback.**
2. **Run the layer via the orchestrator** for the native chart (bo_laksana FIRST + prove the anti-drift spine
   ALONE before fan-out — the load-bearing gate).
3. **Per-asset verification** (each brief's acceptance — anti-drift, no double-count, pillars-meet reachability,
   L0 grounding, embedding consistency, subsystem coverage, discovery-not-fabricated). Verify vs PROD + per-category
   + acharya correctness, NEVER raw counts.
4. **Cockpit/Atlas:** all 9 bo_ assets lit, summed counts true; target_floors = achieved.
5. **B6 SEMANTIC-COMPLETENESS EVAL HARNESS (gates the seal) — NOT YET BRIEFED (§7 surfaced item).**
6. **Promote bo_* DRAFT→CURRENT; author L2_BODHA_CLOSE (the seal artifact — does NOT exist yet) with the L3 Kāla
   onboarding contract; update CURRENT_STATE + SESSION_LOG.**

## §7 — SURFACED ITEMS (things not explicitly listed — flagging so nothing is missed)
1. **The B6 eval-harness brief is NOT YET WRITTEN.** It gates the seal (per the judgment strategy) and must now
   also test: discovery quality, cross-subsystem discovery, and F1 retrieval de-dup. **This is the one remaining
   PLANNING artifact** before execution is fully briefed.
2. **The retrieval-strategy doc is NOT YET WRITTEN** — where F1 (spine-organized, reference-don't-repeat) lands.
3. **No L2_BODHA_CLOSE seal artifact exists** — author at seal time (§6.6).
4. **The schema-migration set is NOT YET AUTHORED** — it's described in the schema-redesign doc but no actual
   325+ .sql exists. This is a build-time deliverable (Antigravity writes the DDL from the briefs).
5. **bo_drishti + bo_anveshana have no asset_registry seed rows yet** (§O2) + no scaffold writers (§3).
6. **The F2 residual** (verify brahma_remedy_corpus CONTENT has medical/vastu/nakshatra rows — possible L0 task).
7. **The cross-subsystem edges depend on L0 mappings being complete** (bg_nakshatra_medical verified; confirm the
   vastu/other cross-discipline mappings exist before bo_karanajala §XS runs).
8. **Volumetrics unknown until B1 runs** — the projection count is the load-bearing number; pin it with one prod
   query before coding (per bo_laksana §2.4).
9. **Execution surface:** Antigravity (Claude Code), NOT Cowork ([[feedback-cowork-vs-antigravity-split]]). These
   briefs are the pasteable inputs. Cowork's job (planning) is essentially DONE after the B6 + retrieval-strategy docs.
10. **Mirror discipline / governance:** if any change touches a mirror-pair (.geminirules etc.) — per CLAUDE.md §K
    — propagate. L2 build is mostly Claude-side; verify no mirror obligation at seal.

## §8 — THE RECOMMENDED SEQUENCE (what to do, in order)
1. **§7.1 + §7.2 — finish PLANNING:** author the B6 eval-harness brief + the retrieval-strategy doc (the last 2 Cowork artifacts).
2. **§1 — HOUSEKEEPING:** fresh branch off main, commit the planning docs, resolve the migration-tree authority, prod==main verify.
3. **§2 — schema migration set** (Antigravity, 325+) + the embedding shared-constant + classical_chunks cleanup.
4. **§3 + §4 — writers (rewrite 8 + author 2) + registry/seed/DAG wiring** (no orchestrator change).
5. **§5 — retrieval tools + coverage gate.**
6. **§6 — build (spine-first) → verify → cockpit → B6 eval → seal (L2_BODHA_CLOSE) → CURRENT_STATE/SESSION_LOG.**

---
*End of L2_BODHA_PREBUILD_READINESS_PLAN v1.0. Planning is done (9 briefs + 6 governing docs); nothing built or
committed. Before buildout: (1) finish the last 2 planning artifacts (B6 eval-harness brief + retrieval-strategy
doc); (2) housekeeping — fresh branch off main, commit the docs, resolve the platform/migrations-is-canonical tree
confusion, prod==main verify; (3) schema-migration set (325+) + embedding shared-constant + classical_chunks
cleanup; (4) rewrite 8 scaffolds + author bo_drishti & bo_anveshana + wire asset_registry_seed.ts (DAG + 2 seed
fixes + 2 new assets), NO orchestrator change; (5) retrieval tools + coverage gate; (6) build spine-first → verify
vs prod → B6 eval gate → seal L2_BODHA_CLOSE with L3 onboarding. Surfaced: B6 + retrieval-strategy + L2_CLOSE +
the migration DDL don't exist yet; F2 corpus-content residual; volumetrics pin; Antigravity is the execution surface.*
