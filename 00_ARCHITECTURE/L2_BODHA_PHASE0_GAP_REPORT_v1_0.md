---
artifact: L2_BODHA_PHASE0_GAP_REPORT_v1_0.md
canonical_id: L2_BODHA_PHASE0_GAP_REPORT
version: 1.1
status: CURRENT
authored_by: Cowork (audit) 2026-06-12
changelog:
  - v1.1 (2026-06-12): Corrected 3 factual errors found by the Antigravity reverse-citation pass
    + recorded the native decisions. (1) `l25_*` tables = migration **137** (live in prod),
    not "migration 206, 6 empty stubs" — repo grep finds **21 distinct l25_ definitions** (6 core
    + staging + lattice/derivation/divergence variants); the live count is V1's job. (2)
    `bodha_signals` HAS A LIVE READER — `platform/src/app/api/chat/consult/route.ts:22` runs
    `SELECT signal_id, signal_name, signal_text FROM bodha_signals` — so V3 is NOT clean and a
    blind DROP would have broken the chat consult API. (3) The reconciliation spans **two separate
    migration trees** (`platform/supabase/migrations/` baseline for legacy `bodha_*`;
    `platform/migrations/_archive/137` for `l25_*`) with different shapes/locations. §6 decisions
    recorded: §13.1 amendments APPROVED; bo_samvada = Option A; author briefs now + Phase-5 E2E as
    build-time gate; P0.1 = repoint-not-drop (corrected disposition, §2/§6).
  - v1.0 (2026-06-12): initial pre-brief readiness audit.
authored_for: the L2 Bodha campaign — the pre-brief readiness audit
purpose: >
  One authoritative "have vs need vs who-builds vs prod-verify" gap report for the L2 Bodha
  Phase-0 prerequisites, so no per-asset brief is written against an assumption. Code-plane
  facts are verified against the repo at main HEAD; every live-DB fact is marked
  NEEDS-PROD-VERIFY with the exact query Antigravity runs.
read_in_combination_with:
  - 00_ARCHITECTURE/L2_BODHA_BUILD_CAMPAIGN_v1_0.md (the campaign this audits Phase-0 for)
  - 00_ARCHITECTURE/A10_MSR_SPEC_v1_0.md … A14 (the spec the tables must match)
audit_scope_caveat: >
  Cowork audits the CODE-PLANE authoritatively (migrations, seed, writers, helpers, formulas).
  The DATA-PLANE is always prod via the Cloud SQL proxy and is NOT reachable from Cowork
  (feedback-localhost-codeplane-prod-dataplane). Every prod fact below is therefore marked
  NEEDS-PROD-VERIFY with the exact psql/cockpit query to confirm it before the relevant brief
  executes. Do not treat a code-plane DDL as proof the table is live — applied-migration state
  must be checked against prod.
---

# L2 Bodha — Phase-0 Gap Report (v1.1 — corrected)

> **v1.1 correction banner.** Three v1.0 facts were wrong and are fixed inline below (see
> frontmatter changelog). The load-bearing one: **`bodha_signals` has a LIVE READER**
> (`consult/route.ts:22`), so the "DROP both sets" path v1.0 floated would have **broken the
> chat consult API in production.** The native's "report before drop" instruction is what caught
> this. Corrected disposition = **repoint-not-drop, prod-gated, table-by-table** (§2 P0.1 + §6).

## §0 — Headline (read this first)

**Phase-0 is a THREE-WAY table reconciliation, not the clean `l25_*`→`bodha_*` rename the
campaign §3.1 first assumed.** The repo audit found three coexisting, mutually-inconsistent
representations of the Bodha tables, **across two separate migration trees**:

1. **Legacy Wave-1/Wave-2 `bodha_*` tables** (9 of them) defined in the prod baseline
   `platform/supabase/migrations/0001_brahma_baseline.sql` — coarse, hand-authored-era shapes
   (`bodha_signals` carries `signal_text`, `claim_text`, fused `confidence`/`salience`,
   `grounding_status` — **the exact contaminated structure the MSR_UCN_CONTAMINATION_AUDIT
   flagged** — and it **has a live reader in the chat consult API**, so it CANNOT be dropped
   blind). These are the names the 8
   seed rows already point at. **They may hold prod data** (Wave-1 writers populated them) —
   disposition must be decided, not assumed.
2. **`l25_*` tables** from **migration 137** (`platform/migrations/_archive/137_l25_tables.sql`)
   — **live in prod, NOT empty stubs** (the v1.0 "migration 206, 6 empty stubs" claim was
   wrong; 206 re-declares the same 6 `IF NOT EXISTS`, but 137 is the live origin). A repo grep
   finds **21 distinct `l25_` table definitions** (the 6 core `l25_msr_signals`/`_cdlm_cells`/
   `_cgm_nodes`/`_cgm_edges`/`_rm_resonances`/`_ucn_digests` + their `_staging` variants +
   extras: `l25_cdlm_links`, `l25_chart_lattice_snapshots`, `l25_derivation_graph_*`,
   `l25_divergence_ledger`, `l25_negative_space_map`, `l25_pattern_catalog`,
   `l25_vedha_anchor_interactions`, `l25_ucn_sections`). **How many are live + populated is V1's
   job** — do not assume.
3. **The rich LOCKED A10–A14 spec tables (~17, ~50-col MSR)** — **exist nowhere in code.**

So the canonical decision (native, 2026-06-12: `bodha_*` naming + LOCKED specs win) resolves to:
**build the rich A10–A14 spec schemas under the `bodha_*` name, reconciling away the legacy
`bodha_*` tables AND the `l25_*` tables — but by REPOINT-NOT-DROP** (a live reader exists; see
the v1.1 banner). This is a brownfield migration with a real data-disposition question and a
live-dependency, materially more careful work than a rename — and exactly the kind of thing that,
undetected, would have broken production mid-build.

**A note on "standardized across layers" (the native's point — preserved, not lost).** There are
two senses of standardization and v1.0 conflated them:
- **(A) asset-ids + the `WriterBase`/FROZEN-orchestrator contract + the `chart_facts`
  fact-grammar** (`bg_*`/`ga_*`/`bo_*`) — this is the *real, locked, cross-layer* standardization.
  Phase-0 *completes* it for L2; it is **never touched.**
- **(B) the legacy `bodha_signals` column-shape** (fused `confidence`/`salience`, `claim_text`,
  `grounding_status`) — this is the **pre-standard Wave-1 contaminated shape**, NOT the thing to
  protect. The A10 spec schema replaces it. Repointing the consult reader to the spec table (or a
  compat view) is what lets (B) retire without losing (A).

**Net Phase-0 readiness: ~0% built (spec-grade), 100% scoped.** No spec tables, no G52 registry,
no `bo_` writers, no formulas, no `bodha_writers/` idempotency helper exist yet. The *foundations
to build on* are all present and proven (orchestrator FROZEN, `ga_writers/_idempotency.py`
pattern, writers-dir `_auto_discover()`, L1 feed verified). Phase-0 is greenfield construction on
a proven base, plus one brownfield reconciliation (legacy + l25_ tables) that is repoint-gated.

---

## §1 — Code-plane facts (VERIFIED against the repo at main HEAD `00000587`)

| # | Fact | Status | Evidence |
|---|---|---|---|
| C1 | Rich A10–A14 spec tables (`bodha_msr_signals` ~50col, CDLM×5, CGM×5, RM×6) | **ABSENT** | no `CREATE TABLE` matches the spec schemas anywhere |
| C2 | Legacy coarse `bodha_*` tables (9: signals, domain_links, graph, graph_edges, graph_staging, remediation, remediation_staging, resonance, signal_embeddings) | **PRESENT in baseline** | `0001_brahma_baseline.sql` lines ~1116–1380; Wave-1/Wave-2 era, dot-notation `bodha.*` writer comments |
| C3 | `l25_*` tables (21 distinct defs: 6 core + staging + lattice/derivation/divergence extras) | **PRESENT, live (migration 137)** | `platform/migrations/_archive/137_l25_tables.sql` (live origin; 206 re-declares `IF NOT EXISTS`); `l25_msr_signals` ~12 cols vs A10's ~50. Live count = V1 |
| C3b | `bodha_signals` LIVE READER (the load-bearing finding) | **PRESENT — blocks blind DROP** | `platform/src/app/api/chat/consult/route.ts:22` runs `SELECT signal_id, signal_name, signal_text FROM bodha_signals WHERE signal_id IN (...)`. Repoint before retire. |
| C4 | `signal_type_registry` (G52, ~500–700 predicates) | **ABSENT** | no DDL, no seed, no code references anywhere |
| C5 | 8 `bo_` registry rows + DAG | **PRESENT** | `asset_registry_seed.ts` lines 685–810; migration 224 renamed `bodha.*`→`bo_*` + wired `depends_on` |
| C6 | 8 `bo_` `target_table`/`count_sql` | **PRESENT but point at LEGACY tables** | seed points `bo_laksana`→`bodha_signals` (the coarse legacy table), NOT a spec table — must be re-pointed in P0.3 |
| C7 | `bo_*` writer classes (`@register('bo_*')`) | **ABSENT** | no `bo_` writers; writers-dir holds only `bg_*` + `ga_*` |
| C8 | `bodha_writers/` package + idempotency helper | **ABSENT** | no `bodha_writers/`; but `ga_writers/_idempotency.py` exists as the pattern to mirror |
| C9 | `salience_formula_v1` / `resonance_score_v1` / `convergence_formula_v1` / `centrality_formula_v1` code | **ABSENT** | no formula code anywhere |
| C10 | Orchestrator FROZEN contract + `_auto_discover()` + `register()` | **PRESENT, proven** | `pipeline/orchestrator/writers/__init__.py` lines 166–232; `bo_` writers drop into this dir and auto-discover |
| C11 | L1 feed (`ga_structural` etc. writers) | **PRESENT, FROZEN-conformant** | all 9 `ga_*` writers in the writers dir; L1_GANITA_CLOSURE sealed |

---

## §2 — Per-Phase-0-item gap (HAVE / NEED / WHO-BUILDS)

### P0.1 — Canonical `bodha_*` spec tables (the reconciliation — REPOINT-NOT-DROP, native-decided 2026-06-12)
- **HAVE:** legacy `bodha_*` (C2, one with a live reader C3b) + live `l25_*` (C3). Neither matches spec.
- **NEED:** ~17 `bodha_*` tables to the A10–A14 schemas (renamed from the specs' `l25_` prefix),
  PLUS the §13.1 philosophy-extension tables (`bodha_convergence`, `bodha_contradictions`,
  `bodha_cgm_paths`) once spec-amended. Plus the 8 MVs (A10×3, A11×5).
- **DECIDED DISPOSITION (native, 2026-06-12 — corrected from the v1.0 "DROP both"):** nothing
  dropped blind. Per-set:

  | Set | Disposition |
  |---|---|
  | `bodha_signals` | **KEEP until repointed** — has a live reader (`consult/route.ts:22`). Repoint the consult route to the new spec table (or a compat view exposing `signal_id`/`signal_name`/`signal_text`) BEFORE retiring the legacy table. |
  | 8 other legacy `bodha_*` (no live reader found) | **DROP-eligible, prod-gated** on V1 (live?) + V2 (holds native data?) + a fresh V3 grep per table. |
  | `l25_*` (21 defs, migration 137) | **DROP-eligible, prod-gated** on V1 + a python-sidecar grep (V3-extended). |

  **Order (inside the P0.1 brief): repoint → prod-verify (V1/V2, operator-only) → table-by-table
  DROP of ONLY verified-safe tables → CREATE the spec-grade `bodha_*` tables.** The
  reverse-citation grep (V3) runs per table before each DROP
  (`[[feedback-destructive-brief-reverse-citation-gate]]`).
- **WHO-BUILDS:** Antigravity, surgical migration via Cloud SQL proxy, one table at a time,
  file-vs-live verified, tracker row recorded (`[[feedback-deploy-migrations-silent-noop]]`).
- **STANDARDIZATION NOTE:** this completes standardization-sense (A) (asset-id/WriterBase/
  fact-grammar) for L2; it retires only standardization-sense (B) (the legacy column-shape). See §0.

### P0.2 — G52 `signal_type_registry` (the layer-gating prereq)
- **HAVE:** nothing (C4).
- **NEED:** global table (A10 §5 schema) + a seed of ~500–700 data-driven predicate definitions
  across all 6 traditions + synthetics, + a writer, + an `asset_registry` row, + an explicit
  `depends_on` edge into `bo_laksana`.
- **WHO-BUILDS:** Antigravity. **Largest Phase-0 task; gates the entire layer** — `bo_laksana`
  cannot run without it. The ~500–700 predicate seed is itself a substantial sub-project (likely
  its own brief).

### P0.3 — Reconcile the 8 `bo_` seed rows → real spec tables
- **HAVE (verified 2026-06-12):** all 8 rows wired, but EVERY ONE points at a LEGACY coarse table,
  none at a spec table. Current mapping (all wrong vs spec):
  `bo_laksana`→`bodha_signals` (legacy 16-col, want `bodha_msr_signals` ~50-col) ·
  `bo_sangati`→`bodha_domain_links` (want `bodha_cdlm_cells` + 4 more incl. `bodha_convergence`) ·
  `bo_bimba`→`bodha_graph` (want `bodha_cgm_nodes`) ·
  `bo_karanajala`→`bodha_graph_edges` (want `bodha_cgm_edges` + sub_graphs/motifs/summary/`bodha_cgm_paths`) ·
  `bo_upaya`→`bodha_remediation` (want `bodha_rm_resonances` + 5 more) ·
  `bo_samvada`→`bodha_resonance` (Option A: NOT a writer — drop or thin-writer) ·
  `bo_samskara`→`bodha_signal_embeddings` (name matches; re-confirm shape) ·
  `bo_pramana_mapa`→`synthesis_quality_scorecard` (no DDL yet; name aligned).
- **NEED:** re-point each row's `target_table`/`count_sql`/`size_sql` to its real spec table(s);
  add `ga_structural` + `signal_type_registry` to `bo_laksana.depends_on` (currently `[bg_rules]`
  only — insufficient); keep rows DRAFT until their tables + writers exist.
- **`count_sql` basis = SUM across ALL the asset's tables** (native, 2026-06-12) — chart-scoped
  summed expression, not a single primary table. `target_floor` = achieved sum after build.
- **NOTE:** registry→table mapping being un-reconciled NOW is on-plan — Phase E is correctly gated
  after Phase B (spec tables exist) + Phase C (G52 exists). This row documents the verified current
  state, not a defect.
- **LOCKED TARGET MAP:** the exact asset→full-table-set→primary→summed-`count_sql`→corrected-
  `depends_on` is now authored as `L2_BODHA_BUILD_CAMPAIGN_v1_0.md §14`. Phase E transcribes it
  verbatim; Phase B creates exactly those tables. No re-derivation needed at Phase E.
- **WHO-BUILDS:** Antigravity, in the seed + a migration.

### P0.4 — Resolve `bo_samvada`/UCD open item
- **HAVE:** seed row `bo_samvada`→`bodha_resonance` (legacy), modelled as a UCN writer.
- **NEED:** native decision (campaign §3.3) — A14 RETIRES UCN; UCD is a read-side join. Recommend
  Option A: `bo_samvada` is not a UCN writer (UCD = `vw_chart_digest` + `query_ucd`, or a thin
  writer for the 5 folded columns).
- **WHO-DECIDES:** native, before the `bo_samvada` brief.

### P0.5 — Phase-5 E2E (non-native orchestrator build proof)
- **HAVE:** Phases 1–4 deployed; #266 fixed non-native builds. **But the live E2E runbook
  (`ORCHESTRATOR_CONVERGENCE_CLOSE §4`) is operator-only and NOT YET RUN**
  (`[[project-orchestrator-convergence-complete]]`).
- **NEED:** the E2E run green on a fresh non-native chart BEFORE L2 rides the same machinery.
- **WHO-BUILDS:** operator (native) + Antigravity. **A hard Phase-0 gate.**

### P0.6 — Shared `bodha_writers/_idempotency.py`
- **HAVE:** `ga_writers/_idempotency.py` as the exact pattern to mirror (`replace_prior_*(conn,
  rows)`, per-chart scoped delete-then-insert, no-op on empty, returns deleted count) (C8).
- **NEED:** a `bodha_writers/_idempotency.py` with `replace_prior_*` helpers for each `bodha_*`
  natural key.
- **WHO-BUILDS:** Antigravity.

### P0.7 — Versioned formula functions
- **HAVE:** nothing (C9). A10 §4 + A13 §3 define `salience_formula_v1` / `resonance_score_v1` in
  spec prose (pseudocode); §13.1 adds `convergence_formula_v1` + `centrality_formula_v1`.
- **NEED:** pure Python, versioned, unit-tested (known inputs→known outputs, reproducibility) —
  the deterministic core of Trap-2 avoidance.
- **WHO-BUILDS:** Antigravity.

---

## §3 — Prod-verification queries (run these in Antigravity BEFORE the dependent brief executes)

Each confirms a live-DB fact this report could only infer from code. Run via the Cloud SQL proxy.

| ID | Verifies | Query |
|---|---|---|
| V1 | Which legacy `bodha_*` tables exist live + their row counts (P0.1 disposition) | `SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE relname LIKE 'bodha\_%' OR relname LIKE 'l25\_%' ORDER BY relname;` |
| V2 | Do the legacy `bodha_*` tables hold NATIVE data (would be lost on DROP)? | `SELECT 'bodha_signals' t, count(*) FROM bodha_signals WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' UNION ALL SELECT 'bodha_graph', count(*) FROM bodha_graph WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';` (extend per table) |
| V3 | Is anything still READING the legacy / l25_ tables? (reverse-citation gate, P0.1 — run per table before each DROP) | code-plane grep, not SQL: `grep -rln "bodha_signals\|bodha_graph\|bodha_domain_links\|bodha_remediation\|bodha_resonance\|l25_" platform/src platform/platform-mcp platform/python-sidecar` → reclassify any live citation KEEP-OR-REPOINT before DROP. **KNOWN: `bodha_signals` ← `consult/route.ts:22` (repoint first).** |
| V4 | Applied-migration ledger — is 137 (l25_ tables) applied + which l25_/bodha_ tables are live? | `SELECT * FROM _migrations_applied WHERE name LIKE '%137%' OR name LIKE '%l25%';` (confirm the ledger table's real name first; pair with V1) |
| V5 | Live `asset_registry` rows for the 8 `bo_` assets (status, target_table, count_sql, depends_on) | `SELECT asset_id, layer, scope, target_table, count_sql, depends_on, is_active FROM asset_registry WHERE asset_id LIKE 'bo\_%' ORDER BY sort_order;` |
| V6 | Is `signal_type_registry` truly absent live? | `SELECT to_regclass('public.signal_type_registry');` (NULL = absent) |
| V7 | L1 native feed present + FORENSIC-anchored (the read contract) | `SELECT count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'; -- expect 27554` and `... WHERE category LIKE 'ga_structural%'` ≈ 6075 |
| V8 | Phase-5 E2E state — any non-native chart with lit `ga_*` rows? | `SELECT chart_id, count(*) FROM asset_throughput WHERE asset_id LIKE 'ga\_%' AND state='lit' AND chart_id <> '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY chart_id;` (rows = an E2E build happened) |
| V9 | Cloud Run revision matches main HEAD before any prod probe | `gcloud run services describe amjis-web --region asia-south1 --format='value(status.traffic[0].revisionName)'` then cross-check the merge SHA (`[[feedback-verify-cloud-run-revision-before-chrome-probe]]`) |

---

## §4 — The Phase-0 build order (dependency-correct)

```
P0.5 Phase-5 E2E green  ──┐ (hard gate — L2 must not ride unproven machinery)
P0.4 bo_samvada/UCD call ─┤ (native decision — unblocks one brief)
                          │
P0.1 reconcile tables ────┼─→ (REPOINT consult route → V1+V2+V3 per table → DROP verified-safe → CREATE spec tables)
  └ §13.1 spec amendments ┘    (CONVERGENCE/CONTRADICTION/GRAPH tables — APPROVED, author w/ briefs)
P0.2 G52 signal_type_registry ─→ (gates bo_laksana; largest task)
P0.6 idempotency helper ──┐
P0.7 versioned formulas ──┘ (parallel, small)
P0.3 re-point seed rows ──→ (after tables exist; flip DRAFT→CURRENT after writers)
                          ↓
              FIRST WRITER BRIEF: bo_laksana (Batch 1)
```

**Recommended authoring sequence for the Phase-0 briefs:** (1) the table-reconciliation brief
incl. the §13.1 spec amendments + the V1–V3 disposition gate; (2) the G52 registry brief (the
big one); (3) a small combined brief for the idempotency helper + the four formula functions;
(4) the seed-reconciliation brief. P0.4 + P0.5 are decisions/operator-runs, not authored writers.

---

## §5 — What is ALREADY solid (build on these, don't re-verify per brief)

- Orchestrator FROZEN + `_auto_discover()` + `register()` — `bo_` writers drop into
  `pipeline/orchestrator/writers/` and are discovered (C10).
- `ga_writers/_idempotency.py` — the exact idempotency pattern to mirror (C8).
- L1 Gaṇita sealed; `ga_structural` (6,075 native rows) + the full feed present + FORENSIC 7/7
  (C11; confirm live via V7).
- The 8 `bo_` asset-ids + DAG edges wired (migration 224) — the grain is right; only the
  `target_table`/`count_sql`/`depends_on` need re-pointing (C5, C6).
- The campaign + design philosophy (§13) + the two trap audits — the *intent* is fully settled.

---

## §6 — Decisions (RESOLVED by the native, 2026-06-12)

1. **Legacy-table disposition (P0.1):** ✅ **RESOLVED → repoint-not-drop, prod-gated, table-by-
   table** (corrected from the v1.0 "DROP both" recommendation, which would have broken
   production — `bodha_signals` has a live reader). Full disposition table in §2 P0.1.
2. **§13.1 spec amendments:** ✅ **APPROVED.** Add `bodha_convergence` / `bodha_contradictions` /
   `bodha_cgm_paths` + `convergence_formula_v1` / `centrality_formula_v1` as amendments to the
   LOCKED A10–A14 specs, authored alongside their writer briefs (version-bump per B.8).
3. **`bo_samvada`/UCD (P0.4):** ✅ **RESOLVED → Option A** (NOT a UCN writer; UCD = read-side
   join / `query_ucd`, or thin writer for the 5 folded columns).
4. **Phase-5 E2E (P0.5):** ✅ **RESOLVED → build-time gate** (not a blocking first action). The
   non-native E2E proof is required before the Bodha build *runs*, but brief-authoring proceeds
   now in parallel. V8 confirms current state.

---

*End of L2_BODHA_PHASE0_GAP_REPORT v1.1. Bottom line: the spec-grade Bodha layer is ~0% built but
100% scoped, on a fully-proven foundation. Two surprises caught before a single brief was written
— (a) three coexisting table representations rather than a clean rename, and (b) a LIVE READER on
`bodha_signals` that turns "DROP" into "repoint-first" — which is exactly what this pass was for.
All four §6 decisions are now RESOLVED. Next: author the Phase-0 briefs in the §4 order (P0.1
reconciliation against the corrected repoint-not-drop disposition → G52 → helper+formulas →
seed-repoint).*
