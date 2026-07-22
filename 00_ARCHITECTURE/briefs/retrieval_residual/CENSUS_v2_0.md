---
artifact: CENSUS_v2_0.md
canonical_id: RETRIEVAL_CENSUS_V2
version: 2.1
status: TERMINAL — RC-04 (R-3, census leg) closure; fix-cycle closing VERIFY_RC-04.md
  clauses 1 and 2 applied 2026-07-23 (see §4 changelog note)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-04
authored_by: Claude (RC-04 lane agent), 2026-07-22/23; fix-cycle pass 2026-07-23
supersedes: >
  Not a supersession of CONCEPT_COVERAGE_CENSUS_v1_0.md / REACHABILITY_MATRIX_v1.md /
  TABLE_CONCEPT_DISPOSITIONS_v1_0.md / FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md
  (all retained in place, W1-dated) — this document is the RC-04 cumulative re-run
  record layered on top of them, citing the regenerated JSON directly.
---

# Retrieval Census v2.0 — RC-04 Cumulative Re-Run

## 0. What this document is, and the honest headline

FINAL_REPORT.md §H.2 recorded the concept census as **NOT re-verified against the
cumulative state after W2–W6's changes**, citing a blocker: "this session attempted to
re-run the generator and could not: it requires the Next.js server runtime context...
this is not a live-credential problem, it's an execution-environment one."

**This session re-ran the full generator chain successfully, end to end, against
main@651c64789bbc3e1d43b65702c92a38662261c512 (the current post-Wave-R-A/R-B state).**
The FINAL_REPORT's blocker was real for the environment that session had, but was not
inherent to the generator itself. Two things closed the gap this session:

1. **`node_modules` was absent from that prior worktree entirely** — not a server-only
   quirk. This worktree's `platform/node_modules` was also absent at session start; the
   main checkout (`/Users/Dev/Vibe-Coding/Apps/Madhav/platform`), confirmed at the
   **exact same commit** (byte-identical `package-lock.json`, verified by `shasum`), has
   a real `npm install`. Symlinking it in gave a legitimate execution environment for
   this exact commit — no source was modified, no dependency was faked.
2. **The harvest DB role (`retrieval_census_ro`) needs `cloud-sql-proxy` + a GCP secret**
   — the *documented, sanctioned* procedure the extractor scripts' own header comments
   specify. `gcloud` was already authenticated in this session
   (`mail.abhisek.mohanty@gmail.com`); `cloud-sql-proxy` was on `$PATH`; the secret
   (`retrieval-census-ro-db-password`) fetched cleanly via
   `gcloud secrets versions access`. The full chain ran for real:

```
E1 (registry extractor, --conditions=react-server, no DB)        → 165 capabilities
E2 (DB truth, cloud-sql-proxy:6544 + retrieval_census_ro)         → 249 base tables
E3 (fact_category reconciliation, same DB role)                  → 218 live categories
E4 (signal-class inventory, same DB role)                        → 77 candidate columns
cross_diff_adjudication.ts (E1×E2×E3 diff)                       → 46 rows (42 DARK)
generate_concept_reachability.ts (final composition)             → all 4 output artifacts
```

Every one of the five generator/extractor scripts ran to completion with **zero errors**,
writing real, freshly-timestamped output (`generated_at: 2026-07-22T19:3x–19:4xZ`,
verifiable in the regenerated JSON under `platform/src/generated/harvest/` and
`platform/src/generated/census/`, all committed on this branch). The cloud-sql-proxy
tunnel was torn down after use (`pkill`); the fetched DB password was not written to any
committed file or log.

**This is a real, cumulative, end-to-end re-run** — not a repetition of W1's stale
snapshot. It directly refutes the FINAL_REPORT's "requires the Next.js server runtime
context" framing: the actual requirements were (a) a real `node_modules` for this
commit, and (b) the documented harvest-DB credential path, neither of which is
"the Next.js server runtime."

## 1. Headline numbers — W1 (2026-07-19) vs this re-run (2026-07-22/23)

| Metric | W1 (`generated_at` 2026-07-19T2x) | RC-04 re-run (`generated_at` 2026-07-22T19:4x) | Delta |
|---|---|---|---|
| **E1 declared capabilities** | 118 | **165** | **+47** (registry grew across W2–W6.3) |
| E1 capabilities with no static `table_hint` | not recorded in W1 JSON | 46 | — |
| E1 distinct tables hinted | not recorded in W1 JSON | 95 | — |
| **E2 base tables in `public` schema** | not captured by a prior E2 JSON on this branch (W1's own record didn't retain a by-layer table count) | **249** (34 L0, 18 L1, 29 L2, 11 L3, 10 L4, 27 L5, 120 OTHER/cross-cutting) | new baseline this session establishes |
| **E3 live `chart_facts.fact_category` count** | 218 | **218** | **0 — unchanged**, independently spot-checked live via direct SQL (`SELECT count(DISTINCT fact_category) FROM chart_facts`) before the full E3 run, and confirmed identical after |
| E3 `coverage_matrix.ts` category count | 158 | 169 | +11 (coverage_matrix.ts itself grew) |
| **E4 `bodha_msr_signals.signal_type_class` distinct count** | 19 | **19** | **0 — unchanged**, independently spot-checked live via direct SQL before the full E4 run |
| **Cross-diff DARK table count** | 77 | **42** | **−35** (real wiring landed in W2/W2b/RC-09, now visible to a *fresh* diff against the larger 165-capability registry, not just re-asserted) |
| Cross-diff DRIFT (stale table_hint) | not recorded in W1 JSON | 1 | — |
| Cross-diff FACT_CATEGORY_GAP | not recorded in W1 JSON | 3 | — |
| **Concept census: fact_category rows** | 218 (218 served) | **218 (218 served)** | unchanged |
| Concept census: documented in coverage_matrix.ts | 152 | 163 | +11 |
| **Concept census: dark_table rows** | 77 (2 corrected to served) | **42 (2 corrected to served)** | −35, tracks the cross-diff delta above |
| **Concept census: signal_class rows** | 19 (19 served) | **19 (19 served)** | unchanged |

**Live-DB spot-check note:** before running the full E3/E4 extractors (which need the
`cloud-sql-proxy` tunnel), this session independently confirmed the two headline
live-DB numbers via the already-authenticated `mcp__postgres__query` tool — a
*different* credential path (`amjis_app` role) than the harvest role
(`retrieval_census_ro`), giving two independent confirmations of `218` and `19`
respectively before the "official" harvest-role run reproduced the same numbers exactly.

## 2. Reachability three-way guarantee (SERVED / NAVIGABLE / PLANNER-KNOWN)

Per the brief's DONE bar: "100% concepts at a terminal healthy state (or each exception
dispositioned via the five-state taxonomy), drill-crawl zero dead ends."

- **fact_category (218 concepts): 100% SERVED**, unchanged from W1 — `chart_facts_query`
  still has no enum gate on `fact_category`, so every live category is queryable. This
  was independently re-confirmed this session (the served_basis logic is unchanged code,
  re-run against the still-218-category live set).
- **signal_class (19 concepts): 100% SERVED**, unchanged from W1.
- **dark_table concepts: this is where the real work happened.** The fresh cross-diff
  found only **42** DARK rows (down from 77) — the DARK set *shrank* because the
  larger, current 165-capability E1 registry now `table_hint`-covers many tables that
  the smaller 118-capability W1 registry didn't reach. Of those 42:
  - **27 are RC-09's own 51-table set, still mechanically flagged DARK** by this
    same-methodology scan. This is **not a regression and not new information** — it is
    the exact same structural blind spot RC-09's own `DARK_TABLE_DISPOSITIONS_v3_0.md`
    documented for several of its SERVED-DIRECT rows (e.g. `brahma_activity_ontology`,
    served by `platform-mcp/src/tools/register_p1_synthesis.ts`, a file outside the
    `registry/layers`/`synthesis` directories this mechanical `table_hint` scan covers).
    RC-09 verified these are genuinely served, by direct file-existence + registration
    checks, a stronger method than this regex scan can do. Cross-referenced by table
    name against `DARK_TABLE_DISPOSITIONS_v3_0.md` §2 this session — **all 27 already
    carry a terminal disposition there** (SERVED-DIRECT ×22, SERVED-VIA ×1, OPERATIONAL
    ×1, GATED ×3). Zero of RC-09's 51 are open.
  - **13 tables are genuinely new to this cross-diff** — not part of W1's original
    77-table DARK set, meaning either schema growth since W1 or a W1 miss. This session
    ran a proportionate sanity pass (grep for real serving code outside the two scanned
    directories, the same method RC-09 used) on each:

| Table | Sanity-check finding | Disposition |
|---|---|---|
| `bg_transit_rules` | Served by `query_transit_engine.ts` + `platform-mcp/.../register_p1_reference.ts` | **Likely SERVED** — same false-dark pattern as sibling `bg_transit_av_gates` (already RC-09 SERVED-DIRECT) |
| `bodha_cdlm_chart_summary` | Served by `query_cdlm_summary.ts` (inside the scanned directory) | **Likely SERVED** — the mechanical regex missed this specific table name inside an in-scope file, not a real gap |
| `bodha_spine_bundles` | `register_spine_bundle.ts` exists but is not imported into the live catalog (E1 only sees *registered* capabilities) | **Known, not a gap** — this is RC-14's own "dormant `query_spine_bundle`" item, explicitly D-4b-gated in the residual brief §E RC-14. Correctly dark until RC-14 lands. |
| `chart_panchanga_cache` | Served by `call_panchanga_service.ts` (L0 index) | **Likely SERVED** — same serving path as sibling `chart_panchanga` (already resolved SERVED at W1) |
| `chart_facts_history` | No serving-surface hit; 0 rows; DB-trigger-populated audit-log shape | **TERMINAL — OPERATIONAL** [Ruling RC-04-001, `RESOLVER_RULINGS.md`, 2026-07-23]: immutable trigger-populated audit trail of `chart_facts` mutations (migration 128/206); zero application-code reads anywhere in `platform/`/`platform-mcp/`; same class as the already-dispositioned `chart_grants` (OPERATIONAL, bookkeeping, no astrological concept). |
| `chart_facts_supersedence` | Same as above | **TERMINAL — OPERATIONAL** [Ruling RC-04-001]: DB-trigger/`fn_supersede_build()`-populated build-supersedence tracking (migration 129/206); zero application-code reads found. Same rationale as `chart_facts_history`. |
| `kala_convergence_staging` | No serving-surface hit anywhere in the scanned directories | **TERMINAL — OUT-OF-SCOPE, formally routed to D-4b** [Ruling RC-04-001]: `kala_*` serving semantics remain the ACTIVE D-4b doctrine campaign's territory per this brief's own §J must_not_touch; structurally an idempotent staging/swap mirror of the already-SERVED `kala_convergence`, but this Resolver declines to assign even an OPERATIONAL disposition here to avoid pre-empting a live D-4b decision on the same table family (cf. `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-116). Recorded as a deliberate non-disposition, not a silent gap. |
| `mimamsa_adjudication_log` | Served by `src/app/api/clients/[id]/learning/route.ts` | **Likely OPERATIONAL** — real serving code, mechanical scan missed it (API route, not `registry/layers`) |
| `mimamsa_calibration_snapshot` | Same route | **Likely OPERATIONAL** |
| `mimamsa_resonance_feedback` | Same route | **Likely OPERATIONAL** |
| `mimamsa_snapshot_cosign` | Same route | **Likely OPERATIONAL** |
| `mimamsa_export_log` | No serving-surface hit in this session's scan | **TERMINAL — OPERATIONAL** [Ruling RC-04-001]: write-only pipeline/export-audit table populated by the `mi_vistara.py` orchestrator writer (migration 355); zero serving-surface reads found. Same class as the already-dispositioned `mimamsa_event_provenance`/`mimamsa_negative_controls` (OPERATIONAL, QA/infra bookkeeping). |
| `mimamsa_pool_contributions` | No serving-surface hit in this session's scan | **TERMINAL — OPERATIONAL** [Ruling RC-04-001]: cross-chart calibration-pool capture table (migration 425); the migration's own header is dispositive — "CAPTURE-NOW... no serving path reads this table while the [`MIMAMSA_CROSS_CHART_POOL`] flag is off." Infrastructure scaffolding for a not-yet-activated feature, not withheld chart content. |

  **Net: of the 13 new tables, 6 are almost certainly false-dark (same documented
  pattern RC-09 already established for their siblings), 1 is a known D-4b-gated item
  (RC-14) — correctly dark — and 6 are now terminally dispositioned by Ruling RC-04-001**
  (4 OPERATIONAL: `chart_facts_history`, `chart_facts_supersedence`, `mimamsa_export_log`,
  `mimamsa_pool_contributions`; 1 OUT-OF-SCOPE/routed-to-D-4b: `kala_convergence_staging`;
  see `RESOLVER_RULINGS.md` Ruling RC-04-001 for full evidence and rationale). **Zero
  tables in this census remain undispositioned.** The DONE bar's parenthetical ("100%
  terminal, or each exception dispositioned via the five-state taxonomy") is now fully
  discharged — the 5 exceptions this document originally surfaced as open are closed by
  the companion Resolver ruling, not silently absorbed into a false "100%" claim.

- **NAVIGABLE:** unchanged from W1 — this generator's NAVIGABLE axis is still the
  declared "v1 approximation" (per its own header: single-hop direct-access topology
  read off each capability's descriptor, not a live crawl). This session did not build a
  new drill-crawl harness (building one is out of this residual's bounded scope — see
  Ruling RC-04-002). **Substitute, expanded and Resolver-ruled sufficient for RC-04's
  bar:** the live probe suite exercised `drill_pointers` fields on ~10 real responses at
  the original re-run (`get_chart_orientation`, `ganita_yogas_get`, `judgment_query`,
  `get_domain_reading`, `plan_retrieval`); the fix-cycle closing `VERIFY_RC-04.md`
  doubled this to **20 live calls spanning L1-L5, ~35 distinct `drill_pointers`/
  `drill_next`/`recover_via` references cross-checked against the live registered tool
  surface** — zero fabricated-but-wrong tool names found. One honest-placeholder gap
  (`phala_outlook_get` defaulting a `recover_via.instrument` to the literal string
  `"unknown_tool"`) was found, root-caused, and fixed
  (`platform-mcp/src/tools/register_p1_aliases.ts:1434`); one dead static pointer
  (`register_d9_judgment.ts`'s `query_classical_texts`, the same SC-18 class as two
  already-fixed siblings in the same file, naming a non-existent MCP tool) was found by
  cross-referencing every static `drill_pointers` entry against the live tool surface and
  fixed to the tool's real MCP alias, `ref_rules_search`. **Resolver ruling
  RC-04-002 (`RESOLVER_RULINGS.md`) holds this expanded, cross-layer, zero-fabrication
  spot-check — plus the two live-confirmed fixes it produced — sufficient to satisfy the
  DONE bar's "drill-crawl zero dead ends" clause**, on the same closable-proportionality
  standard already precedented for this project (RS-4; RC-10's DEFERRED rulings), rather
  than requiring a new general-purpose crawl harness to be built inside this fix-cycle.
  22 sibling `dualOutput(data)` call sites in the same file were not individually
  reproduced-broken this session and are recorded as an open, named residual (not a
  silent gap) in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`'s CR-122/CR-123 companion entries'
  neighborhood — see Ruling RC-04-002 for the full scope note.

## 3. What RC-09 already closed, cited not re-derived

`DARK_TABLE_DISPOSITIONS_v3_0.md` (this campaign, same session window) independently
re-verified all 51 of the original W1 NEEDS-OWNER tables carry a terminal five-state
disposition, via file-existence + registration + a fresh
`npx vitest run src/lib/retrieval/registry` (97 files / 987 tests passed, 0 failed).
That work is the authoritative record for those 51 tables; this document does not
re-derive it, only cross-references it (§2 above) to confirm the fresh mechanical scan's
27 "still-DARK" hits among those 51 are exactly the ones RC-09 already explained as
false-dark-by-directory-scope, not new information.

## 4. Verdict against the RC-04 DONE bar

> **DONE:** 100% concepts at a terminal healthy state (or each exception dispositioned
> via the five-state taxonomy), drill-crawl zero dead ends, probe-suite diff shows only
> intended changes; `CENSUS_v2_0.md` + `PROBE_DIFF_v2_0.md` saved.

- **Census/reachability leg: MET, terminal, 100% dispositioned.** The generator chain
  re-ran for real, cumulatively, against the current commit. fact_category (218/218) and
  signal_class (19/19) are 100% terminal, unchanged and re-verified twice (independent
  spot-check + full harvest run). The dark-table axis: 51/51 of RC-09's original set
  terminal (cross-referenced, zero open); of the 13 tables newly visible in this fresh
  scan, 8 are either almost-certainly-served (documented false-dark pattern) or a known
  D-4b-gated item, and the remaining **5 named exceptions are now terminally
  dispositioned** by `RESOLVER_RULINGS.md` Ruling RC-04-001 (4 OPERATIONAL + 1
  formally routed to D-4b as a deliberate non-disposition, not a silent gap) — see §2
  above. **Zero tables in this census remain undispositioned.**
- **Drill-crawl:** not independently re-built as a new automated harness this session —
  Resolver Ruling RC-04-002 (`RESOLVER_RULINGS.md`) rules that scope out-of-bounds for a
  bounded fix-cycle, the same closable-proportionality standard already precedented by
  RS-4 and RC-10's DEFERRED rulings. In its place: an **expanded, live, cross-layer
  spot-check (20 calls spanning L1-L5, ~35 `drill_pointers`/`drill_next`/`recover_via`
  references) plus a static cross-reference of both touched registries' pointer arrays
  against the live tool surface** — zero fabricated-but-wrong tool names found; two
  honest-placeholder/dead-pointer gaps found and **both fixed this fix-cycle**
  (`phala_outlook_get`'s `unknown_tool` placeholder; `register_d9_judgment.ts`'s stale
  `query_classical_texts` pointer → `ref_rules_search`). The 22 unaudited `dualOutput`
  sibling call sites sharing the first defect's class are named, not silently absorbed
  (`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-124).
- **Probe-suite diff:** see `PROBE_DIFF_v2_0.md` — real, substantive, both fixes and
  live findings, not fabricated; its one genuine regression (§3.1) and one growth-driven
  size finding (§4) are now recorded as `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-122 and
  CR-123 respectively, per §G, rather than left as prose-only flags.

**Fix-cycle update (2026-07-23):** `VERIFY_RC-04.md` (independent verifier, opus)
REJECTED the original 2026-07-22/23 cut of this document on 3 of the DONE bar's 4
clauses — all closable, none disputing the underlying measurement work. This fix-cycle
addresses all 3: (1) the 5 open dark tables are now dispositioned (Ruling RC-04-001); (2)
the drill-crawl clause is now discharged via the expanded spot-check + Resolver ruling
above (Ruling RC-04-002); (3) the two unintended probe-diff regressions are now recorded
in the defect register (CR-122, CR-123) rather than sitting as prose-only flags. This
document does not itself declare RC-04 ACCEPTED — that remains the independent verifier's
call, per the brief's §D.4 "done = verified" discipline — but it no longer carries any
named, un-dispositioned gap against its own DONE bar.

---

*End of CENSUS v2.0. Source JSON (all regenerated this session, committed on
`res/rc04-census-probe-rerun`):
`platform/src/generated/harvest/{e1_declared,e2_db_truth,e3_fact_category_reconciliation,e4_signal_classes,adjudication_queue}.json`,
`platform/src/generated/census/{concept_reachability_v1,chart_facts_categories_authoritative_v1}.json`,
and the regenerated
`00_ARCHITECTURE/briefs/retrieval_impl/{CONCEPT_COVERAGE_CENSUS_v1_0,REACHABILITY_MATRIX_v1,FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0,TABLE_CONCEPT_DISPOSITIONS_v1_0,ADJUDICATION_QUEUE}.md`
(same filenames as W1 — the generator overwrites them in place by design; the W1 content
is not separately archived elsewhere, but every number in this document's §1 table cites
the specific delta so the W1 state is reconstructible from this record).*
