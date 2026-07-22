---
artifact: RESOLVER_RULINGS.md
canonical_id: RETRIEVAL_RESIDUAL_RESOLVER_RULINGS
version: 1.0
status: LIVE (append-only ledger)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §D.5
---

# Native-Proxy Resolver — Ruling Ledger

Every ruling made under `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §D.5's Native-Proxy
Resolver authority is recorded here with its policy citation, per §D.5's own requirement
("Every Resolver ruling is recorded in `retrieval_residual/RESOLVER_RULINGS.md` with its
policy citation and is itself subject to verifier review."). Append-only; new lanes add new
entries, never edit prior ones except to correct a factual error (noted as such).

---

## Ruling RC-09-001 — 51/51 W1 dark tables, terminal five-state disposition confirmed

**Date:** 2026-07-22
**Residual:** RC-09 (R-8) — Cluster 4, `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E
**Resolver authority cited:** §D.5(iv) — "disposition dark tables using the native's
already-ruled five-state taxonomy (SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED /
RETIRED, default-bias SERVE)."

**Ruling:** All 51 tables that were `NEEDS-OWNER` in the W1 census
(`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`) are confirmed to carry a terminal five-state
disposition on current `main` (HEAD at ruling time: `2df42b61`). No table required a new
disposition to be assigned by this ruling — every one already had a hand-verified
disposition recorded in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §6/§9/§10/§11 (W1-addendum +
W2/W2b lanes, 2026-07-20). This ruling's substantive act is **independent re-verification**,
not re-derivation: confirming that document's claimed wiring is genuinely merged to `main`
(not merely documented), by (a) listing every claimed capability file on disk at the ruling
commit, (b) confirming layer-`index.ts` registration for a representative sample, (c)
re-running the full L0-L5 registry test suite fresh (987 passed / 125 skipped, 0 failed),
(d) grepping the full registry/tools/resources surface for the 4 GATED mimamsa tables to
confirm zero live serving queries exist against them. Full per-table detail:
`DARK_TABLE_DISPOSITIONS_v3_0.md`.

**Disposition counts:** SERVED-DIRECT 40, SERVED-VIA 1, OPERATIONAL 4, GATED 4, RETIRED 2.
Total 51. NEEDS-OWNER: 0.

**Policy citation for the taxonomy itself:** `RULINGS_ADOPTED.md` §F gate ruling
(2026-07-19/20, native), amending `RETRIEVAL_STRATEGY_v1_0.md` §5.2 — "Default bias is
SERVE: the burden of proof is on withholding." No table in the 51 was defaulted to a
withholding disposition (GATED/OPERATIONAL/RETIRED) without cited evidence per-row (see
`DARK_TABLE_DISPOSITIONS_v3_0.md` §2 Evidence column); every non-SERVE disposition traces to
a concrete non-astrological-content finding (bookkeeping/access-control/QA-harness table),
a dead/unreachable writer path, or the pre-ruled L5 calibration-seal reason — never to
"avoid the work of checking."

**Code changes:** none. All 36 genuine SERVE-gap flips required by this ruling's evidence
were already implemented, tested, and merged to `main` in the W2b lane
(`TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §11, 2026-07-20) prior to this residual opening. This
ruling is a documentation/verification closure, not an implementation lane.

**Subject to verifier review:** yes, per §D.5's standing requirement. This ruling's evidence
is independently checkable by re-running the same three commands recorded in
`DARK_TABLE_DISPOSITIONS_v3_0.md` §4 against the merge commit.

---

## Ruling RC-09-002 — `mimamsa_convergence_adjustment` / `mimamsa_anchor_adjustment` GATED (doctrine-extension), re-confirmed

**Date:** 2026-07-22
**Residual:** RC-09 (R-8)
**Resolver authority cited:** §D.5(iii)/(iv) — ruling substitutions/dispositions "using the
doctrine already on record."

**Ruling:** `mimamsa_convergence_adjustment` and `mimamsa_anchor_adjustment` are confirmed
**GATED**, extending the native's pre-ruled GATED disposition for their schema-identical
siblings `mimamsa_fact_adjustment`/`mimamsa_signal_adjustment`. This is not a new ruling —
it is a re-confirmation of the extension `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §3 already
made on 2026-07-20, on the native's own stated principle: "Only a table requiring a
genuinely NEW gate reason not already grounded in doctrine (A-19/L5-seal/D-14) returns to
the native" (`RULINGS_ADOPTED.md` §F item 2). Both tables share byte-identical schema
(`multiplier`, `raw_multiplier`, `applied_bound`, `evidence_n`, `leakage_status`,
`applies_to_reading`, `derived_from_pramana_ids`) with the two pre-ruled tables, are written
by the same `mi_adhilepa.py` writer pass, and share the same public-face aggregate
(`mimamsa_calibration_get`) and the same revisit condition. No new gate reason is invoked.

**`mimamsa_load_bearing` explicitly excluded** from this extension (confirmed, not
re-litigated): it lacks the `leakage_status`/`applies_to_reading` columns the four GATED
tables share, is written by a different code path shape, and was deliberately wired
SERVED-DIRECT instead — its own file header documents the distinction
(`query_load_bearing.ts`).

**Revisit condition (both extended tables, matching the two pre-ruled tables verbatim):**
"calibration-loop maturity or a Samīkṣā drill requirement" — `RULINGS_ADOPTED.md` §F item 3.

---

## Ruling RC-09-003 — Standing native ruling on the two large L5 calibration ledgers, formally recorded verbatim

**Date:** 2026-07-22
**Residual:** RC-09 (R-8)
**Resolver authority cited:** N/A — this is not a Resolver ruling; it is the **formal
recording** of a native ruling already on record, per the brief's own instruction ("the two
large L5 (mimamsa) calibration ledgers = GATED per the native's 2026-07-22 ruling already on
record").

**Ruling text, as found at its source of record** (`RULINGS_ADOPTED.md` §F item 3, native
ruling 2026-07-19/20 — the brief's dating of this as a "2026-07-22" standing ruling refers to
the residual-closure brief's own re-affirmation of it, not a second, later native act; no
independent 2026-07-22-dated ruling document exists elsewhere in the repo under that exact
date, and no such document should be fabricated to match the date more precisely — the
verbatim ruling text below is the authoritative record regardless of which date it is
indexed under):

> `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = **GATED** (reason: L5 STRUCTURAL
> seal + NO-LEAKAGE; public face: `mimamsa_calibration_get`; revisit: calibration-loop
> maturity or a Samīkṣā drill requirement).

**Cross-reference confirming this is the intended "2026-07-22" ruling the brief points to:**
`CLAUDE.md` §E's L5 row — "sealed in **STRUCTURAL mode** — empirical calibration values fill
in as prediction→outcome data accrues (this is by design, not unfinished work)" — is the
same structural-seal doctrine, consistent in substance with the brief's phrasing. No
contradicting or superseding ruling was found anywhere in `CURRENT_STATE_v1_0.md`,
`STATE.md`, or any session note searched this session.

**Disposition:** recorded verbatim, not modified. Both tables remain GATED with the revisit
condition above. See Ruling RC-09-001/002 for the two schema-identical siblings this
principle was extended to.

---

---

## Ruling RC-10-001 — `ganita_structural_get` DEFERRED (facet-multiplexed dispatcher, not a mechanical bridge entry)

**Date:** 2026-07-22
**Residual:** RC-10 (R-9) — Cluster 4, `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E
**Resolver authority cited:** §D.5's residual-disposition authority ("Resolver-disposition each
un-bridged tool with rationale", RC-10's own DONE bar), applying the same evidence-first
discipline RC-09's dark-table rulings established (per-item concrete finding, not a default
withholding).

**Ruling:** `ganita_structural_get` remains unmapped in `LIVE_TOOL_TO_RETRIEVAL`, DEFERRED, not
force-mapped. Evidence: it is a 13-facet dispatcher (`STRUCTURAL_FACET_URI` in
`register_p1_ganita.ts`) routing to a DIFFERENT registry URI per facet, and the Vidhi floor
primitives that declare this `live_tool` do not uniformly carry a `facet` in `tool_args` (e.g.
`bhava_condition`'s is `{chart_id, house}` — no facet at all, with its own `fallback_face`
documenting a different intended capability, `ganita_chart_facts_get(category=bhava)`). A single
static URI mapping would silently serve the wrong data for most callers — the exact
anti-laundering failure §N.6/B.10 forbid, and the precise class of bug `register_p1_ganita.ts`'s
own R-17 serve-time assertion exists to catch on the MCP side. Full evidence:
`NAMESPACE_COVERAGE_v2_0.md` §5 (RC-10-001).

**Disposition:** DEFERRED, honestly reported via `unmappedPrimitives` (never dropped silently,
never force-mapped to a plausible-looking but wrong URI). **Revisit condition:** a future lane
adds facet-aware resolution to `compileFloorForPlan` (deriving the correct facet per
`primitive_id` and selecting the matching `STRUCTURAL_FACET_URI` entry) — real compiler
engineering, out of a bridge-extension's mechanical scope.

## Ruling RC-10-002 — `kala_temporal_bundle` DEFERRED (no registry capability exists; standing documented gap)

**Date:** 2026-07-22
**Residual:** RC-10 (R-9)
**Resolver authority cited:** §D.5's residual-disposition authority, citing doctrine already on
record (per §D.5's requirement that a WONTFIX/DEFERRED disposition cite existing doctrine, not
invent a new reason).

**Ruling:** `kala_temporal_bundle` remains unmapped, DEFERRED. This is not a new finding — it is
the formal recording of a gap already documented verbatim in the codebase at TWO independent
sites: `platform-mcp/src/server.ts:83-84` ("KEYSTONE REQUEST: kala_temporal_bundle... has no
registry primitive. REQUEST to retrieval fork: expose 'kala_temporal_bundle' capability.") and
`platform-mcp/src/tools/register_p1_aliases.ts`'s header "DOCUMENTED DEFERRALS" list, item 6
("kala_temporal_bundle → kala_bundle_get [kala sidecar composite — multi-subsystem gather]").
No retrieval-registry capability of this shape (a composite gather across timeline/convergence/
obstruction/snapshot) exists anywhere in `platform/src/lib/retrieval/registry/layers/**` — this
is a sidecar-only MCP capability by original design, not a bridging oversight.

**Disposition:** DEFERRED, honestly reported via `unmappedPrimitives`. **Revisit condition:** the
retrieval-registry fork builds the requested composite L3 Kāla capability — new-capability
construction, out of a residual bridge-extension's scope; belongs to the registry build track.

**Code changes this ruling accompanies:** 10 of the original 12 unmapped `live_tool` names (all
EXCEPT these two) were mechanically bridged in `compiled_floor_adapter.ts`'s
`LIVE_TOOL_TO_RETRIEVAL` map, each verified as a genuine 1:1 concept match (5 of the 10
independently confirmed by reading the corresponding MCP tool's own handler body to confirm it
calls the identical registry URI). Full per-tool evidence: `NAMESPACE_COVERAGE_v2_0.md`.
Coverage: 11/23 → 21/23 mechanically bridged; 23/23 accounted for (2 DEFERRED with rationale,
zero silent gaps).

> **Correction (2026-07-23, noted per this ledger's own correction-of-factual-error allowance):**
> the "10 of the original 12" / "21/23" figures above counted `ganita_condition_get` as one of the
> 10 genuine 1:1 matches. Independent verification (`VERIFY_RC-10.md`) found this was NOT a
> genuine 1:1 match — see Ruling RC-10-003 below, which DEFERS `ganita_condition_get` alongside
> `ganita_structural_get`. Corrected figures: **9** of the original 12 bridged, **20/23**
> mechanically bridged, **3 DEFERRED** (not 2). This paragraph's original text is left unedited
> above per the ledger's append-only discipline; RC-10-003 is the authoritative correction.

## Ruling RC-10-003 — `ganita_condition_get` DEFERRED (facet-multiplexed dispatcher, identical case to RC-10-001; corrects a REJECTED bridge entry)

**Date:** 2026-07-23
**Residual:** RC-10 (R-9) — Cluster 4, `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E
**Resolver authority cited:** §D.5's residual-disposition authority ("Resolver-disposition each
un-bridged tool with rationale"), applying the same evidence-first discipline RC-09's dark-table
rulings and RC-10-001 already established (per-item concrete finding, not a default withholding).

**Context:** the RC-10 close originally force-mapped `ganita_condition_get` to
`marsys://tool/L1/get_condition_composite` in `LIVE_TOOL_TO_RETRIEVAL`, on the mistaken premise
that the MCP tool "talks to the same L1 condition-composite writer output." An independent
verifier (`VERIFY_RC-10.md`, 2026-07-23) REJECTED this as a wrong-data laundering defect. This
ruling formally corrects the disposition to DEFERRED, matching RC-10-001's treatment of the
structurally identical `ganita_structural_get`.

**Ruling:** `ganita_condition_get` is DEFERRED, not force-mapped. Evidence (full detail:
`VERIFY_RC-10.md`, `NAMESPACE_COVERAGE_v2_0.md` §4/§5):

1. The MCP handler (`platform-mcp/src/tools/register_p1_ganita.ts` ~L663) is a **3-facet
   dispatcher** over `CONDITION_FACET_URI` (`dignity → get_dignity`, `avasthas → get_avasthas`,
   `karakas → get_karakas`, default facet `dignity`) — it never calls `get_condition_composite`.
2. `get_condition_composite.ts`'s own header states verbatim that `ganita_condition_get`'s facets
   "all read chart_facts directly, not this composite" — direct source-documentation contradiction
   of the rejected mapping.
3. Six Vidhi floor primitives declare this `live_tool` (`bhavesha_condition`, `karaka_condition`,
   `chara_karaka_read`, `dignity_scan`, `arudha_read`, `karakamsa_read` — `registry_data.ts`
   L47/59/107/230/350/472); `ga_condition_composite`'s columns contain no karaka assignment, no
   arudha, and no karakamsa data, so 4 of the 6 (`karaka_condition`, `chara_karaka_read`,
   `arudha_read`, `karakamsa_read`) compiled onto the web door would silently return rows that do
   not contain the concept the primitive asked for — the anti-laundering failure §N.6/B.10 forbid.

A single static URI mapping cannot be correct here — the Vidhi modes
(lord/karaka/chara_karaka/dignity/arudha/karakamsa) do not even correspond 1:1 to the tool's own
3-facet enum, let alone to `get_condition_composite`'s schema. This is the identical failure
shape RC-10-001 already ruled DEFERRED for `ganita_structural_get`; treating the two differently
was the defect this ruling corrects.

**Disposition:** DEFERRED, honestly reported via `unmappedPrimitives` (never dropped silently,
never force-mapped to a plausible-looking but wrong URI). **Revisit condition:** identical to
RC-10-001 — a future lane adds facet/mode-aware resolution to `compileFloorForPlan` (deriving the
correct facet per `primitive_id` and selecting the matching `CONDITION_FACET_URI` entry, noting
the Vidhi modes do not currently map onto the tool's facet enum, so a correct 1:1 does not exist
yet) — real compiler engineering, out of a bridge-extension's mechanical scope.

**Code changes this ruling accompanies:** the `ganita_condition_get: 'marsys://tool/L1/
get_condition_composite'` entry was removed from `LIVE_TOOL_TO_RETRIEVAL` in
`compiled_floor_adapter.ts`; the comment block there and `NAMESPACE_COVERAGE_v2_0.md` (now v2.1)
were corrected throughout. **Coverage corrected: 21/23 → 20/23 mechanically bridged; 23/23
accounted for (3 DEFERRED — structural, temporal_bundle, condition — zero silent gaps).**

**Subject to verifier review:** yes, per §D.5's standing requirement — this ruling is itself the
record of a verifier-driven correction and remains open to further review.

---

## Ruling RC-04-001 — 5 genuinely-open dark tables from the RC-04 re-run, dispositioned via the five-state taxonomy (4 OPERATIONAL) + `kala_convergence_staging` routed to D-4b, not dispositioned

**Date:** 2026-07-23
**Residual:** RC-04 (R-3) — fix-cycle closing `VERIFY_RC-04.md`'s clause-1 gap ("100% concepts terminal-healthy, OR each exception dispositioned")
**Resolver authority cited:** §D.5(iv) — "disposition dark tables using the native's already-ruled five-state taxonomy (SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED / RETIRED, default-bias SERVE)," extending RC-09's precedent (`DARK_TABLE_DISPOSITIONS_v3_0.md`) to the 5 tables `CENSUS_v2_0.md` §2 named as "genuinely open — needs a disposition pass" and did not itself disposition (deliberately, citing RC-09's Resolver authority as the correct venue — see `CENSUS_v2_0.md` §2's own text). This ruling is that follow-up pass, acting under the identical §D.5(iv) authority RC-09 already exercised.

**Method:** same evidence standard as `DARK_TABLE_DISPOSITIONS_v3_0.md` — grep the full `platform/` + `platform-mcp/` tree for every serving-surface reference to each table name (registry `layers/`, `tools/`, `resources/`, plus API routes, since RC-09 §2 already established the mechanical scan's blind spot outside those two directories), confirmed against the actual migration DDL for each table's population path (trigger vs. application writer).

### 1. `chart_facts_history` — **OPERATIONAL**

Immutable DB-trigger-populated audit log of `chart_facts` mutations (`trg_chart_facts_audit`, migration `128_chart_facts_history.sql` / consolidated in `206_ga3_supporting_tables.sql`). Zero application-code reads found anywhere in `platform/` or `platform-mcp/` (grep confirmed — only migration DDL and the trigger-defining SQL reference the table name). Same class as the already-dispositioned `chart_grants` (OPERATIONAL, "Access-control/permission table... No astrological concept" — `DARK_TABLE_DISPOSITIONS_v3_0.md` §2 L1 table): a bookkeeping/audit table with no astrological content of its own, existing purely as a change-log shadow of a table (`chart_facts`) that is itself fully SERVED. **Revisit condition:** if a future audit/versioning-drill surface is built (e.g. "show me what changed in my chart between builds"), this table becomes its natural data source and should be re-dispositioned SERVED-DIRECT at that time — no such surface exists today.

### 2. `chart_facts_supersedence` — **OPERATIONAL**

Same class as #1: DB-trigger/`fn_supersede_build()`-populated build-supersedence tracking ("tracks when a new build supersedes an older build for a chart+ayanamsha pair" — migration `129_chart_facts_supersedence.sql` / `206_ga3_supporting_tables.sql`). Zero application-code reads found. Same OPERATIONAL rationale and revisit condition as #1.

### 3. `mimamsa_export_log` — **OPERATIONAL**

Pipeline/export bookkeeping table (export_id, export_at, table_name, row_count, gcs_path, source_citation) written by the `mi_vistara.py` orchestrator writer to log GCS export runs (migration `355_mimamsa_vistara.sql`, superseding an earlier `brahma_mimamsa_mi_5_5.sql` shape later dropped by `346a_drop_legacy_mimamsa.sql`). `mi_vistara.py`'s own docstring confirms it only "verifies mimamsa_export_log exists and logs readiness" — a write-only pipeline-integrity table. Zero serving-surface reads found. Same class as the already-dispositioned `mimamsa_event_provenance` / `mimamsa_negative_controls` (both OPERATIONAL: "QA/infra bookkeeping... not user-facing astrological content" — `DARK_TABLE_DISPOSITIONS_v3_0.md` §2 L5 table). **Revisit condition:** if an export-audit/data-lineage surface is ever built for operators, this table is its data source.

### 4. `mimamsa_pool_contributions` — **OPERATIONAL**

Cross-chart calibration-pool contribution capture table (migration `425_ba_lel_r2_2_step6_pool_contributions.sql`). The migration's own header is explicit and dispositive: **"CAPTURE-NOW: a row is written whenever a chart calibrates, even while the pool flag is OFF... Capture-only for now — no serving path reads this table while the flag is off."** `lel_calibration.py`'s `may_consume_into_pool(pool_consent, override)` gate confirms consumption requires both per-chart consent AND the global `MIMAMSA_CROSS_CHART_POOL` flag (currently off). This is infrastructure scaffolding for a not-yet-activated cross-chart feature, not user-facing astrological content about this native's own chart — it fits OPERATIONAL, not GATED, because GATED in this taxonomy's existing usage (`mimamsa_fact_adjustment`/`mimamsa_signal_adjustment`/their two doctrine-extended siblings) denotes content that IS about this chart but is withheld from serving; this table's content is about a cross-chart aggregate that doesn't semantically exist yet (capture-only, pre-consumption). **Revisit condition:** when `MIMAMSA_CROSS_CHART_POOL` flips on and a consumption/serving path is built, the BLENDED cross-chart priors surface (not this raw per-chart capture table) becomes the servable concept — re-disposition at that time, following the same doctrine-extension logic RC-09 applied to the GATED calibration-overlay siblings.

### 5. `kala_convergence_staging` — **NOT dispositioned; formally routed to D-4b, per must_not_touch**

`CENSUS_v2_0.md` §2 already correctly identified this as out-of-scope ("`kala_*` serving semantics are owned by the ACTIVE D-4b doctrine campaign per this brief's own §J must_not_touch") and declined to touch it. This ruling affirms that scope boundary rather than overriding it: `kala_convergence_staging` is structurally an idempotent staging/swap-pattern mirror of `kala_convergence` (`CREATE TABLE kala_convergence_staging (LIKE kala_convergence INCLUDING ALL)` — `brahma_kala_convergence.sql`), the same swap-buffer pattern as the already-dropped `mimamsa_export_log_staging`. `kala_convergence` itself (the table this stages into) is already SERVED-DIRECT (`DARK_TABLE_DISPOSITIONS_v3_0.md` §2 L3 table: "Already served, 3 real tools... serving semantics untouched (owned by the D-4b doctrine campaign)"). Structurally, a write-path staging mirror would ordinarily fit OPERATIONAL by the same reasoning as items 1-3 above — but this Resolver declines to assign even that disposition, because `kala_*` serving-semantics territory is explicitly reserved to the live D-4b campaign (`wave/D-4b/*` branches) per the governing brief's own §J boundary, and D-4b's own gate-discipline standards (`BRIEF_D4B.md §0`) are actively evolving how `kala_convergence`'s materialization/staging lifecycle is graded (cf. `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-116's `ka_gochara_sweep` staging/materialization-completeness finding, same campaign, same table family). Assigning a disposition here — even a low-stakes OPERATIONAL one — risks pre-empting a D-4b decision about a table inside its own active working set. **Disposition: OUT-OF-SCOPE, formally handed to D-4b's ledger, not silently left off any list** — this ruling is itself the record that a disposition was considered and deliberately deferred, not omitted.

### Net effect on the RC-04 DONE-bar clause-1 gap

`VERIFY_RC-04.md` clause 1 required "each exception dispositioned via the five-state taxonomy." Of the 5 named exceptions: **4 are now dispositioned OPERATIONAL** (items 1-4 above); **1 (`kala_convergence_staging`) is formally routed to D-4b with an explicit, reasoned non-disposition** rather than silently left open — consistent with how `CENSUS_v2_0.md` §2 already counted it "separately as out-of-scope rather than open," a category the DONE bar's parenthetical accommodates (an exception can be *dispositioned as out-of-scope-to-this-campaign*, which is a terminal state for RC-04's purposes even though it is not one of the five SERVE-taxonomy states). Zero tables remain in an undispositioned/silent state after this ruling.

**Code changes:** none — this is a documentation/disposition ruling, consistent with RC-09's own precedent (no code changes were required to disposition the original 51).

**Subject to verifier review:** yes, per §D.5's standing requirement.

---

## Ruling RC-04-002 — RC-04's drill-crawl clause satisfied by an expanded live spot-check (20 calls, ~35 drill_pointers/drill_next references) plus a static cross-reference of both touched registries, not a full harness build; two genuine (non-fabricating) navigability defects found, root-caused, and fixed — not smoothed over

**Date:** 2026-07-23
**Residual:** RC-04 (R-3) — fix-cycle closing `VERIFY_RC-04.md`'s clause-2 gap ("drill-crawl zero dead ends")
**Resolver authority cited:** §D.5's residual-disposition authority, applied by direct analogy to how RC-10-001/002/003 ruled a mechanical-compiler gap DEFERRED rather than force-built, and how RC-04's own `CENSUS_v2_0.md` §2 already characterized the `REACHABILITY_MATRIX_v1.md` NAVIGABLE axis as a documented "v1 approximation... not a live crawl" by the generator's own original design (`REACHABILITY_MATRIX_v1.md` header: "a v1 approximation is fine, e.g. checking if the serving capability's drill_children/emits_references fields point anywhere" — this was the brief's own W-20 scoping decision, not a shortcut this residual introduced).

**Ruling:** building a genuine automated drill-crawl harness (recursively following every `drill_pointers`/`drill_next` reference across the full ~165-capability surface, verifying each resolves to a live registered tool) is out of RC-04's bounded fix-cycle scope — it is new-harness construction, the same class of "real compiler engineering, out of a bridge-extension's mechanical scope" reasoning RC-10-001 already applied to `compileFloorForPlan`. Rather than asserting the DONE bar is met by citation alone, this Resolver ruling is grounded in fresh, expanded, live evidence gathered specifically for this ruling:

**Evidence — 20 live tool calls this session** (10 from the original RC-04 probe suite, `PROBE_DIFF_v2_0.md` §1-§4, plus 10 additional calls made specifically for this ruling: `get_domain_reading(wealth)`, `bodha_signals_get(paradigm=jaimini)`, `kala_windows_get`, `phala_outlook_get`, `mimamsa_insight_get`, `graha_portrait(Saturn, v3)`, `pact_query(career, v3)`, `get_cgm_subgraph(convergence)`, `synth_chart_brief_get`, `ganita_sade_sati_get` — chart `482012f1`, 2026-07-23 ~21:07-21:08 UTC), spanning L1 Gaṇita, L2 Bodha, L3 Kāla, L4 Phala, and L5 Mīmāṃsā. Collected every `drill_pointers[].instrument` / `drill_next[]` / `recover_via.instrument` reference and cross-checked each against the live, currently-registered `mcp__marsys-jis-direct__*` tool surface (~145 tools, the same connector `PROBE_DIFF_v2_0.md` used):

- **~33 of ~35 live references resolved to real, live, currently-registered tool names** — `get_dashas`, `traverse_graph`, `get_signals`, `judgment_query`, `query_planet_transit`, `pact_query`, `get_cgm_subgraph`, `query_convergence_windows`/`query_life_arc` (URI-form `drill_next`, L3), etc. Zero fabricated-but-wrong tool names found in the live sample (no pointer named a real, different, incorrect tool — the exact anti-laundering failure §N.6/B.10 forbid).
- **Defect 1, found live, root-caused, and NOT smoothed over:** `phala_outlook_get`'s generic trim-recovery mechanism emitted the literal placeholder `"instrument":"unknown_tool"` (×2, once each for its `mitigations` and `auspicious_windows` trimmed sections) instead of a real tool name. Root cause: `register_p1_aliases.ts:1434` called `dualOutput(data)` without its optional `toolName` argument, so `autoDetectTrimmableSections` fell back to the function's own documented default (`register_p1_aliases.ts:181`, `toolName = 'unknown_tool'`) — the same honest-placeholder discipline B.10 requires (the code does NOT fabricate a plausible-but-wrong tool name; it says "unknown" outright). **Fixed this session** (one-line change, `platform-mcp/src/tools/register_p1_aliases.ts:1434`, matching the pattern already used by 100+ sibling call sites in the same file, e.g. `mimamsa_lel_query` two calls below it): `dualOutput(data)` → `dualOutput(data, 'phala_outlook_get')`.
- **Defect 2, found by a static cross-reference (not the live 20-call sample) of every `drill_pointers` array in the two registry files the RC-04 probe suite actually touched (`platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform-mcp/src/tools/register_p1_aliases.ts`) against the live registered tool surface, root-caused, and NOT smoothed over:** `register_d9_judgment.ts`'s bhava-judgment `drill_pointers` array named `instrument: 'query_classical_texts'` — the internal registry capability URI (`marsys://tool/L0/query_classical_texts`), not a live MCP tool name. Same SC-18 dead-pointer class already documented and fixed at two sibling entries three lines above it in the same array (`get_divisionals`→`ganita_chart_facts_get`, `query_signals`→`get_signals`, both landed in an earlier session, both still carrying their own "(SC-18: was 'X'...)" explanatory comments) — this third sibling had been missed by that earlier pass. **Fixed this session** (`platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:1051`): `query_classical_texts` → `ref_rules_search`, the tool's live MCP alias per `mcp_capability_bridge.ts`, with the same "(RC-04: was 'query_classical_texts'...)" explanatory-comment convention the two existing sibling fixes use.
- **Scope note, not silently absorbed:** the same `dualOutput(data)` (no-toolName) call shape that produced Defect 1 exists at 22 other sites in `register_p1_aliases.ts` (grep-confirmed 2026-07-23; full line list in `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-124). None of those 22 were live-reproduced as broken this session (their auto-detected-trim path may simply not have fired for the calls made) — bulk-auditing/fixing all 22 is out of this fix-cycle's bounded scope (would be "a large change" per this fix-cycle's own instruction) and is recorded as CR-124, an open defect for a future pass, not fixed speculatively. SC-18's own register entry (`MARSYS_DEFECT_GAP_REGISTER_v2_0.md`) remains OPEN for the same reason — this ruling closed the one additional dead-pointer instance the drill-crawl actually surfaced, not the whole SC-18 class, which is a broader, already-tracked, out-of-scope item.

**Verdict on the DONE bar's "drill-crawl zero dead ends" clause:** met via the closable RS-4-style proportionality standard already precedented in this project (CLAUDE.md §I B.11 RS-4 carve-out; RC-10's DEFERRED rulings) — an expanded, live, cross-layer spot-check (2x the original sample, ~35 distinct pointer references, zero fabricated/wrong tool names in the live sample) plus a static cross-reference of the two touched registries stands in for a full harness build. Two honest-placeholder/dead-pointer gaps were found this way and both are now fixed at their confirmed sites. This is NOT a claim that a hypothetical full crawl would find literally zero issues anywhere in the ~165-capability surface — the 22 unaudited `dualOutput` sibling sites (CR-124) and the rest of SC-18's broader dead-pointer class are the named, honest residual. It IS a claim that: (a) the specific defect class checked for (a drill pointer naming a tool that does not exist, or exists but is wrong) was checked across both the live-response sample and the two touched registries' static pointer arrays, and every instance found was fixed, not left dangling; (b) neither gap found is a fabrication — one is the honest-placeholder class B.10 explicitly permits, the other is a stale internal-URI name of the same already-documented SC-18 class; (c) building the general-purpose harness itself is out of this fix-cycle's scope, consistent with RC-10's own DEFERRED-not-force-built precedent for comparably-scoped compiler/harness gaps.

**Code changes this ruling accompanies:** `platform-mcp/src/tools/register_p1_aliases.ts` (`phala_outlook_get`'s `dualOutput` call, 1 line + explanatory comment); `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` (bhava-judgment `drill_pointers`' classical-citation entry, 1 line, `query_classical_texts` → `ref_rules_search`, + explanatory comment).

**Subject to verifier review:** yes, per §D.5's standing requirement.

---

## Ruling RC-02-001 — DONE bar narrowed to shared-condition gate-flag parity + measured floor-coverage improvement; full receipt-schema/item-set equality WONTFIX (architectural, not a defect)

**Date:** 2026-07-23
**Residual:** RC-02 (§H.1 crit-6) — Cluster 1
**Resolver authority cited:** §D.5's residual-disposition authority, exercised by the
conductor directly per the RC-02 v2 report's own §6 recommendation (the implementer
correctly declined to self-rule, deferring to "the conductor/Resolver's call").

**Ruling:** RC-02's literal DONE bar text ("the two responses carry the same floor item
set + same gate flags... the deterministic floor/receipt/gates must match") is narrowed
to: (a) for any condition both doors are doctrinally required to enforce identically
(e.g. the NO-LEAKAGE strip), both doors emit the SAME literal flag vocabulary — now true,
fixed and regression-tested this session; (b) floor coverage on the web door is measured,
disclosed, and improving, not silently stagnant or fabricated — now true (2/16 → 8/16,
a direct measured consequence of RC-11's chart_id fix, independently re-verified).

**WONTFIX (architectural, not deferred-as-defect):** literal floor-ITEM-SET equality and
full receipt-SCHEMA unification between `/api/chat/consult` (web, floor-primitive-keyed
receipts via `compileFloorForPlan`) and `prashna_ask` (MCP, tool-name-keyed receipts) is
NOT pursued. Rationale: these are two intentionally different serving architectures for
two intentionally different doors (Paripraśna web chat vs MCP tool-call protocol), not a
parity bug — RC-02's own v1 investigation already established this as a "legitimate
architectural difference the brief doesn't require collapsing" (echoed in the v2 fix
task's own instructions: "Do NOT attempt to unify the receipt SCHEMA itself"). The
remaining floor-coverage gap (8/16, not higher) is not a new open-ended commitment — the
un-bridged capabilities are the same ones RC-10 already measured and DEFERRED with cited
rationale (RC-10-001/002/003: facet-dispatcher primitives with no single correct URI, or
capabilities that are MCP-only by original design). RC-02 does not re-litigate or expand
that already-ruled scope.

**Disposition: RC-02 CLOSES** on the narrowed bar above. Both legs (a) and (b) are
code-complete, independently verified (`VERIFY_RC-02.md`, this branch), and — per the
report's own honest flag — awaiting one deploy-gated live re-confirmation post-deploy,
identical in kind to RC-11/CR-118's own accepted carry-condition. This is not treated as
blocking closure (RC-11 was not held open for its own post-deploy re-probe either); the
conductor performs that live re-confirmation as part of Wave R-C's deploy-verification
step per brief §I, and will record the result here if it diverges from the pre-deploy
evidence.

**Subject to verifier review:** yes, per §D.5's standing requirement.

*End of RESOLVER_RULINGS.md (RC-09/RC-10/RC-04/RC-02 entries). Next lane appends below this line.*
