---
artifact: FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md
canonical_id: FACT_CATEGORY_ENUMERATION_RECONCILIATION
version: 1.0
status: GENERATED — v1 (design note; no source files were changed this wave)
generator: platform/scripts/census/generate_concept_reachability.ts
generated_at: 2026-07-19T21:18:10.804Z
---

# Fact-Category Enumeration Reconciliation v1.0 (W-23)

Per RETRIEVAL_PLANE_ELEVATION_PLAN §9.4 W-23: "Reconcile the three chart_facts category enumerations... into ONE generated source consumed by all three consumers." This note picks the authoritative source and documents why the others disagree. **No source file was modified to execute this migration** — this lane's scope is must_not_touch `chart_facts` semantics; wiring real consumers to the new authoritative artifact is future work (see recommendation below), not done here.

**The plan's own framing understates the problem.** It names three sources (SCHEMA.json, coverage_matrix.ts, "37" prose). L1b's E3 extractor found a real fourth (`platform/python-sidecar/ga_writers/CHART_FACTS_SCHEMA.json`, 191 — a byte-DIFFERENT copy of the "same" file). This lane found a real **fifth**: `platform/src/lib/ganita/types.ts` also defines a `CHART_FACTS_CATEGORIES` constant (26 entries) — imported by `facts_store.ts` but only re-exported, never used to gate a write or a read. None of the five static/near-static sources gates the live *serving* path — `chart_facts_query`'s category filter does `fact_category = ANY($n::text[])` directly from the caller's raw string, with no enum check against any of the five lists. They are pure (currently wrong) documentation from the runtime's perspective; one of them (`coverage_matrix.ts`) does have a real non-runtime consumer — see table below (import-site counts are from this generator's own repo-wide `scanImportSites()` scan, not a hand-typed claim).

## The five sources, real counts

| source | count | import sites (repo-wide scan) | gates the runtime serving path? |
|---|---|---|---|
| **Live DB** (`SELECT DISTINCT fact_category FROM chart_facts`) | **218** | — | — (this IS the runtime) |
| `CHART_FACTS_SCHEMA.json` (00_ARCHITECTURE canonical + platform/scripts/governance mirror, byte-identical) | 147 | not scanned (JSON, not a TS import) | no |
| `CHART_FACTS_SCHEMA.json` (`platform/python-sidecar/ga_writers/`, undocumented 3rd copy) | 191 | not verified this pass — Python sidecar out of TS-registry scan scope | not verified this pass — Python sidecar out of TS-registry scan scope |
| `coverage_matrix.ts` `CHART_FACTS_CATEGORIES` | 158 | **1** (`platform/tests/retrieval/coverage_gate.test.ts:15`) | **no** — not consulted by `chart_facts_query`'s serving path; its one real import site is `coverage_gate.test.ts`, a live CI *test-time* coverage gate, not a runtime serve-path consumer |
| `ganita/types.ts` `CHART_FACTS_CATEGORIES` (5th source, found this lane, not cited by the plan) | 26 | **2** (`platform/src/lib/ganita/facts_store.ts:33`, `platform/src/lib/ganita/facts_store.ts:518`) | no — imported by `facts_store.ts` but only re-exported |

## Authoritative source: the live DB (218 categories)

Chosen per CLAUDE.md §N.5 generalized: `chart_facts` (the table) is the ground truth for `chart_facts` (the category enum), not a hand-typed mirror of it, and the live set is what every one of the other four sources is trying (and failing) to describe. The full generated list ships at `platform/src/generated/census/chart_facts_categories_authoritative_v1.json` (218 categories, with live row counts per category).

## Migration recommendation (design only — not executed this wave)

Retire the three/four/five static `CHART_FACTS_CATEGORIES`-shaped constants as sources of truth; point future consumers at the generated JSON (or a live query) instead. `coverage_matrix.ts`'s own array is already L1a's flagship HIGH catch in `no_hardcoded_concept_lists.ts` — this reconciliation gives the eventual fix its target artifact. Regenerate on every L1 build (or on a cadence) so the file stays honest as the live set drifts. Wiring real call sites (chart_facts_query's description text's enumerated examples, coverage_matrix.ts's completeness gate, the governance CHART_FACTS_SCHEMA.json mirror) to consume it is a W2 migration item, not this wave's.

---

*End of FACT_CATEGORY_ENUMERATION_RECONCILIATION v1.0 — Lane L1d, W1. Authoritative list at `platform/src/generated/census/chart_facts_categories_authoritative_v1.json`.*
