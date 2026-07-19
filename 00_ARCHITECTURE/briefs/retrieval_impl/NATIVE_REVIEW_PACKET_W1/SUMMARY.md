---
artifact: SUMMARY.md
canonical_id: NATIVE_REVIEW_PACKET_W1_SUMMARY
version: 1.0
status: NATIVE REVIEW PACKET — §F human gate deliverable 5/5 (read this one first)
governing_brief: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §F
generated_for_native: 2026-07-20
---

# Native Review Packet W1 — Executive Summary

**What this is:** the §F human gate deliverable for the Retrieval Plane Elevation implementation
campaign. W0 (safety items S-1..S-5) and W1 (concept spine + census — 4 parallel lanes: L1a
concept-ledger infra, L1b harvest pipeline, L1c service manifests, L1d census + reachability) are
both closed, verifier-ACCEPTed, and deployed. This packet is the "can we see the whole system"
checkpoint before W2 (One Catalog — the actual serving-surface migration) opens. Every number below
traces to a generated artifact under `00_ARCHITECTURE/briefs/retrieval_impl/` or
`platform/src/generated/` — nothing here is a hand-typed estimate.

## What W0+W1 delivered

- **W0:** 5 safety items shipped and live-verified (PII scrub extension, 13→20-file fail-closed
  token guard unification, plan-surface entitlement, `parity_check` disposition, description-hygiene
  scan v1), the §B baseline probe suite, a read-only census DSN, envelope-codegen CI parity test.
  Went through 3 verifier fix-cycles (2 REJECT-WITH-FINDINGS, 1 ACCEPT) — see `STATE.md` for the
  full defect trail; nothing was silently waved through.
- **W1:** a `concept_ledger` schema + TS access layer (355 rows staged, not yet applied live); a
  hardcoded-list lint that caught 5 real duplicated-enum offenders (`CHART_FACTS_CATEGORIES` in
  `coverage_matrix.ts` is the flagship, 158 hand-typed strings); 9 new optional `CapabilityDescriptor`
  fields (type-only, zero of the 118 existing descriptors touched); a 4-extractor harvest pipeline
  (E1 registry-declared, E2 DB-truth, E3 fact-category reconciliation, E4 signal-class); a mechanical
  cross-diff producing the adjudication queue; a full service manifest for the Python sidecar (20
  routers / 49 endpoints, live-snapshot-verified); an 8-axis tool census (4 axes genuinely computed,
  4 honestly stubbed as not-yet-assessed); a reachability matrix over 314 concepts; a dark-set wiring
  design (no implementation).

## Headline numbers (real, source-traceable)

| metric | value | source |
|---|---:|---|
| Live capabilities (`getCatalog()`) | **118** | `e1_declared.json`, `tool_census_v1.json` |
| Live `chart_facts.fact_category` values | **218** | `e3_fact_category_reconciliation.json`, live DB query |
| — documented in `coverage_matrix.ts`'s list | 152 | same |
| — SERVED-UNDOCUMENTED (queryable but on no static list) | 66 | same |
| — planner-known (referenced by a vidhi primitive) | 0 | `concept_reachability_v1.json` |
| Real DARK tables (zero TS-registry serving route) | **77** | `adjudication_queue.json` |
| — INTERNAL-BY-DESIGN (deliberately unserved) | 24 | `TABLE_CONCEPT_DISPOSITIONS_v1_0.md` |
| — SERVED, corrected this wave (false-dark) | 2 | same |
| — NEEDS-OWNER (honest, undecided) | 51 | same |
| DRIFT (declared table_hint, no real table) | **0** | `adjudication_queue.json` — a genuine positive result post backtick-scan fix |
| Confirmed cross-plane `signal_class` values | **19** | `e4_signal_classes.json` (`bodha_msr_signals.signal_type_class`) |
| Sidecar routers / endpoints | **20 / 49** (+`/health`=50) | `service_manifest.json`, live `/openapi.json` snapshot — exact match, 0 missing/extra |
| Tool-census axis A3 (v3 envelope conformance) | **0/118** implement it yet | `tool_census_v1.json` — 1 repo-wide `buildRetrievalEnvelope()` call site |
| Tool-census axis A8 (`projection_tags` populated) | **0/118** | same |
| W0 verifier fix-cycles | 3 (2 REJECT, 1 ACCEPT) | `STATE.md` |

## The 3 things that most need the native's judgment call at this gate

1. **The 51 NEEDS-OWNER dark tables — genuinely ambiguous, not mechanically resolvable.**
   L1b's own scope statement is honest about this: 52/77 (51 after this wave's 2 corrections) were
   NOT individually researched — the naming-pattern rules (bg_* reference tables, bookkeeping
   suffixes) only auto-resolved 24. The highest-stakes ambiguity is the L5 pair
   `mimamsa_fact_adjustment` (121,100 rows) / `mimamsa_signal_adjustment` (97,504 rows) — the two
   largest DARK tables in the entire set, almost certainly calibration-ledger internals that
   `mimamsa_calibration_get` already aggregates over, but building anything against them without
   L5-seal-owner sign-off risks exposing raw adjustment rows as if they were settled facts (L5 is
   SEALED in STRUCTURAL mode per CLAUDE.md §E). This packet does not propose a disposition for these
   two — it flags them for the native.
2. **`bodha_cgm_sub_graphs` and its 3 sibling tables may already be served — needs a targeted
   re-scan, not a build decision.** Live MCP tools (`get_cgm_subgraph`, `bodha_graph_subgraph_get`,
   `bodha_graph_traverse_get`) already exist and strongly suggest the CGM graph plane IS served via
   a route the TS-registry-only scan couldn't see (same false-dark pattern this wave already caught
   twice for `bg_dignity_reference` and `chart_panchanga`). Recommend: re-run the census with
   `platform-mcp/src/tools/` included before treating this as a build gap at all.
3. **The D-5/G-4 sequencing assumption in the master brief §I.2 was already overtaken by events.**
   `STATE.md`'s coexistence check found G-4 (Gochara-Chitra's serving lane) had already merged to
   main *before* this campaign opened — the brief's originally-imagined path ("W2/W3 land before
   D-5 serving opens, D-5 becomes the commissioning contract's first live test") is foreclosed. The
   brief's own §I.2 fallback applies ("W2 absorbs the gochara tools in its migration"), but this is
   a live sequencing fact the native should confirm before W2 opens, not something the conductor
   should silently decide alone.

## Also worth a glance, lower stakes

- `chart_ayanamsha_reports` (named in the master brief's own aspirational examples) does not exist
  in the live DB — either the brief's naming is stale, or it refers to a computed report
  `chart_facts_query`'s `ayanamsha_id` filter already serves. No wiring plan is meaningful until
  this naming question is resolved.
- Two undocumented dark services surfaced beyond the brief's GT-50 ask: `ka_muhurta_seva`
  (`call_muhurta_score`, same stub shape as `ka_graha_sancara`) and a dead `pyjhora_adapter`
  Docker build target that has never existed in this repo's git history.
- 5 static `chart_facts` category-enumeration sources disagree with each other and with the live DB
  (147/191/158/26/218) — this wave picks the live DB as authoritative (design-only; no consumer was
  migrated to it yet, per must_not_touch on `chart_facts` semantics).

## Where to look next in this packet

- `ASSET_AND_CONCEPT_MAP.md` — every layer's concept inventory with real counts.
- `CONCEPT_TOOL_MAPPING.md` — the reachability matrix grouped by "reachable / dark / needs a call".
- `TOOL_SHAPE_DESIGN.md` — the projection topology, the 9 new descriptor fields, and 3 concrete
  worked examples (existing/elevated/new asset).
- `VISUALIZATION_DATA.json` — machine-readable lattice + topology + adjudication summary for a
  chart/graph rendering (full 314-concept lattice and full 118-tool census included, not sampled).

---

*End of SUMMARY v1.0 — NATIVE_REVIEW_PACKET_W1, deliverable 5/5. Per master brief §F: STOP here and
wait for native approval. Any corrections are absorbed as W1 addenda before W2 opens.*
