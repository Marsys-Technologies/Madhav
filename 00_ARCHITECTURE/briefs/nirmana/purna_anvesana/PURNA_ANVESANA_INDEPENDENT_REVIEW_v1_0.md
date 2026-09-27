---
artifact: PURNA_ANVESANA_INDEPENDENT_REVIEW
version: "1.0"
status: FOR_NATIVE_DECISION_REVIEW_AND_PLAN_ONLY
prepared_on: "2026-09-22"
evidence_cutoff: "2026-09-22T13:20:00Z"
campaign_id: madhav-purna-anvesana
responds_to: 00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF_v1_0.md
prepared_by: Claude Code (Claude Fable 5.1), independent review session
intended_reader: Native (product owner), for the product-strategy conversation
authority_exercised: >
  None beyond the handoff's review boundary. No file outside this artifact was created or
  changed. No PR, task, automation, IAM, secret, migration, deployment, or campaign record was
  touched. Production database access was read-only aggregate/metadata SQL as `amjis_app`
  through the pre-configured Postgres tool; one read-only live MCP tool call was made
  (`ganita_dashas_get`, limit 1) to confirm a diagnosis. No raw answer text, chart payload,
  birth data, or life-event content was retrieved or reproduced here.
source_revisions:
  candidate_head: 34991645b1d57926d97ac027d6fca59d8c2ecb53   # PR #2705, codex/purna-wealth-near-miss
  protected_main_at_review: c58e86662e692e678f64934f1689ccaa0fdcd7d7  # later moved to 50d49e19d (PR #2713) during review
  l3_branch: 5d8252dbefc053f9faa92aab693ad46310e0c5c5           # codex/madhav-l3-claude-code (PR #2695 head)
session_open:
  session_id: PURNA-ANVESANA-INDEPENDENT-REVIEW-2026-09-22
  cowork_thread_name: "Madhav — Pūrṇa Anveṣaṇa Independent Review"
  agent_name: claude-fable-5-1
  tool: "Claude Code (VS Code extension, non-interactive)"
  worktree_path: /Users/Dev/.codex/worktrees/purna-wealth-near-miss/Madhav (read) ; /Users/Dev/.codex/worktrees/0ee2/Madhav (this artifact only)
  step_number_or_macro_phase: REVIEW (no build layer touched)
  predecessor_session: Codex task 01a0b7d8-9a90-74f3-aab9-80014919f8b2 (Product Completion II) — not superseded by this session
  may_touch:
    - 00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md
  must_not_touch:
    - "platform/**"
    - "platform-mcp/**"
    - "00_ARCHITECTURE/briefs/nirmana/purna_anvesana/**"
    - ".github/**"
    - "**/migrations/**"
    - "everything else in every checkout"
  red_team_due: not_applicable (review session; no artifact promoted)
  mandatory_reading_confirmation: CLAUDE.md v7.4; CLAUDECODE_BRIEF.md (status COMPLETE, skipped per §C.0); CURRENT_STATE_v1_0.md v6.66 §2; ROOT_FILE_POLICY.md; MADHAV_PRODUCT_DEFINITION_v3_0.md §5, §12, §14; 2026-09-17-purna-product-completion-v2.md (full); PRODUCT_ACCEPTANCE_PROTOCOL_v2.json; LIVE_COMPLETION_MATRIX_v1.json; AUTONOMOUS_EXECUTION_CONTROL_v1.json; SUCCESSOR_OWNERSHIP_ADDENDUM_2026-09-19.md; INHERITED_EMPTY_BOOTSTRAP_FINDING_v1.json; MADHAV_PLANNER_CAPABILITY_KNOWLEDGE_AND_INQUIRY_IMPLEMENTATION_v1_0.md §15; the L3 cross-campaign notice; the handoff (all 21 sections)
session_close_note: >
  SESSION_LOG.md was NOT appended and CURRENT_STATE was NOT updated, because the handoff's
  authority boundary forbids repository mutation beyond this artifact and every candidate
  checkout belongs to another active campaign. This is a declared governance residual for the
  Native to discharge (or waive) when this review is adopted; it is not a claim of a well-formed
  close under CLAUDE.md §H.
---

# Pūrṇa Anveṣaṇa — independent review and elevated completion plan

## 0. How to read this

- §1 is the verdict. §2 is the root-cause analysis (the part that changes the plan). §3 is the
  requirements-to-runtime matrix. §4 classifies the nineteen dark bindings. §5 lists what to
  preserve, change, and remove. §6 is the execution plan. §7 lists the decisions only the
  Native or a named owner can make. §8 is the control mechanism that replaces the stalled loop.
  §9 is acceptance and the copy-ready kickoff brief. §10 is the evidence register. §11 audits
  the handoff's own claims. §12 assesses the strategic coordination's contribution.
- Evidence classes follow the handoff: **freshly observed** (this session, with the command or
  file:line), **recorded** (a governed record or a prior audit says so), **implementation
  present**, **hypothesis**, **not verified**. Every material claim below carries one.
- Six bounded read-only audits were delegated to subagents (knowledge/availability model;
  inquiry planning and closure; delivery and channels; collector and campaign records; PR/CI
  state and the near-miss producer; operating loop and release). Their file:line citations are
  reproduced where used. Their full reports were not published; the citations are checkable.
- What this review did **not** do: run the application test suite; run the collector or the
  judge; touch any PR; read raw answers or private evidence; audit bucket ACLs. Those are named
  gaps, not implied passes.

## 1. Independent verdict

### 1.1 Bottom line

The campaign built a real, largely sound inquiry substrate and then spent its last days
accounting for a catalogue while the product was structurally unable to produce a single
complete reading on the canonical chart in production. The reason is not the near-miss band,
not the evidence store, and not PR #2704. The reason is that **every Pūrṇa consumer binds its
evidence to a "build identity" that production has never had.** On the canonical chart, the
"active build" every consumer selects is a run that built one L2 asset on 2026-09-12; zero of
the chart's 143,299 L1 facts, zero of its dasha rows, and one of its provenance receipts sit
under that id. Every producer-output availability contract, the judgment handler's fact reads,
the judgment availability probe, and the wealth reading checklist all filter on it. They cannot
succeed. This is freshly observed in production (§2, RC-1) and explains why the only live
three-door exercises ever recorded produced "matching dark states" and zero delivered facts.

Three further production-side defects compound it, each independently sufficient to block the
wealth reading: a "replacement in progress" fence that fires on 1,477 stale orphan rows left by
failed runs since June (RC-2, confirmed live through the dasha tool); a `ga_strength` receipt
that predates the digest spec the campaign's own migration 1042 activated, with no build of any
kind dispatched since the grant fix landed (RC-3); and the near-miss obligation that the
consumer hardcodes as never computed while L1 stores only fired yogas (RC-4).

Above the data plane, three of the ten required outcomes are not implemented as specified even
in source: "deep reasoning" is a model swap to a *cheaper* model with the reasoning flag never
reaching any provider (RC-5); evidence-driven continuation can only ever re-page the same
capability, never add a new one from observed evidence (RC-5); and the fact register is
computed over evidence the synthesis model does not see, with a mapping rule that production
prose can essentially never satisfy (RC-6).

The operating loop then declared itself blocked on three externally-owned items and emitted 239
identical heartbeats over 46 hours while at least seven safe, in-scope, high-leverage work items
sat unstarted (RC-8). The strategic coordination contributed by specifying consumer
completeness before a producer feasibility pass, by treating source accounting as a milestone,
and by not converting "needs an owner" into a decision packet (§12).

**Salvageable: yes, with four focused replacements, no rewrite.** The failed abstraction is
the chart-wide "latest completed run = active build" proxy and its twin, "receipt build id =
row build id". The smallest replacement is a single shared per-asset generation resolver that
all four consumers call, backed later by the (currently empty) generation-head tables the
data-plane cutover already created. Everything else on the critical path is a bounded repair.

### 1.2 What is sound and must be preserved

Freshly verified in source at `34991645b`:

- The Inquiry Contract compiler, floors, omission challenger, graph traversal, closure
  receipt, and door-parity projection (`platform/src/lib/vidhi/inquiry/`). Closure semantics
  are correct and honest: required dark/failed/unexplored obligations block `COMPLETE`.
- Durable lifecycle: `planner_inquiry_lifecycles`, `planner_inquiry_evidence_receipts`,
  `planner_inquiry_action_reservations`, `planner_managed_prashna_jobs` exist in production
  under `purna_inquiry_owner` with the app role fenced out (freshly observed via `pg_class`);
  cross-instance claim/lease and evidence recovery are implemented and DB-tested
  (`execution_session.ts:39-76`, `migration_1038.db.test.ts:268,287`).
- Response accountability machinery (`response_accountability.ts`) and the in-memory 200th-fact
  regressions (`response_accountability.test.ts:212-224, 565-580`).
- The real three-door collector, anti-fixture and anti-false-live validation, the frozen 5+30
  cases with the recomputed fingerprint `240e78a5…547111`, the independent judge, and the
  deterministic-override scorer (`platform/scripts/purna/`).
- The protected release chain: skipped mutation jobs now fail the run
  (`deployment_outcome_gate.ts:101-115, 155-158`), candidate revisions are smoke-tested and
  SHA-attested before promotion (`deploy.yml:1283-1337, 1786-1847`).
- The catalogue model itself (SCU, four evidence-source requirement kinds, immutable snapshot,
  overlay version binding, fail-closed staleness). It is mis-typed (RC-7), not wrong.
- Migration 1070's builder grants are applied and correct in production (freshly observed:
  `data_plane_builder` holds SELECT on `asset_registry`, `asset_freshness`,
  `asset_output_digest_specs`, `charts`; INSERT/SELECT/UPDATE on `asset_provenance_receipts`;
  ledger `_migrations_applied` shows 1070 at 2026-09-20T05:42Z).
- The canonical chart's `view` grant for a probe principal exists today (freshly observed:
  3 grant rows on `482012f1`, 1 matching `probe`, permission `view`).

### 1.3 What is incomplete, over-engineered, mis-modelled, or unintegrated

| Area | Finding | Class |
|---|---|---|
| Build identity | Chart-wide latest-completed-run proxy; receipt id ≠ row id after no-delta runs | mis-modelled (RC-1) |
| Replacement fence | `queued/building` asset rows in terminal runs count as "in progress" | defect (RC-2) |
| Strength attestation | Spec revised by 1042; no rebuild; no build dispatched since 1070 | producer-data gap (RC-3) |
| Near-miss | Consumer hardcodes `not_computed`; L1 stores only fired rows; the L2 `absence` signal class exists but is never emitted; no ratified candidate/eligibility packet | producer gap + missing decision (RC-4) |
| Deep planning | Reasoning flag unmapped; deep slot routes to `gemini-2.5-flash`; raw door makes no LLM call | not implemented as specified (RC-5) |
| Continuation | Successor join can only admit same-SCU pagination frontier | not implemented as specified (RC-5) |
| Accountability | Register ≠ synthesis-visible; JSON-substring interpretation mapping; Portal not enforced; raw finalize has no answer register; collector reads the wrong wire field | unintegrated (RC-6) |
| Availability model | One evidence-source gate for all capability kinds; 144/146 probes are `LIMIT 0`; binding-level darkness; 156/182 isolated with one boilerplate rationale | over-uniform (RC-7) |
| Operating loop | 239 heartbeats, 0 working turns after a "blocked" verdict that left safe work unstarted | process failure (RC-8) |
| Integration | #2705 regenerated its snapshot without its own acceptance artifact and route goldens, then recorded the failures as a #2704 dependency; the nine scanner failures are allowlist line-drift on pre-existing zero-row probes | self-inflicted coupling (RC-9) |
| Release | Web auto-redeploys on every main merge; MCP/sidecar only on path change; compatibility attestation absent; change detector reads `latestReadyRevisionName` | configuration hazard (RC-10) |

## 2. Root causes and critical path

Each root cause carries: what was observed, where, the class the handoff asked for, confidence,
and the check that would falsify it.

### RC-1 — There is no chart-level generation identity; consumers fake one with "latest completed run" (class: producer-data model gap + consumer proxy; confidence: HIGH)

**Observed (freshly, production, read-only):**

| Query | Result |
|---|---|
| Latest completed `build_runs` row for `482012f1` | `a1a5f7d6…` — `scope=asset`, `scope_target=bo_grounding`, ended 2026-09-12T01:47Z |
| `chart_facts` rows under that build id | **0** of 143,299 (10 distinct build ids; largest is `ga_structural`'s own run with 106,707 facts) |
| `chart_dashas` rows under that build id | **0** of 483,870 |
| `asset_provenance_receipts` under that build id | 1 (bo_grounding's own) |
| Wealth-required receipts (`ga_structural`, `ga_vichara`, `ga_sensitive`, `ga_sensitive_degree`, `ga_strength`) | each under its **own single-asset run id**; `assets_in_that_run = 1` for all |
| Generation tables from migrations 1035/1036 (`l1_data_plane_generation_heads`, `…_generations`, `…_partitions`, `l2_data_plane_generation_*`, `data_plane_l2_producer_generations`) | all exist, all **0 rows** |

**Where the proxy lives (source at `34991645b`):**

- `platform/src/lib/retrieval/registry/knowledge/overlay_loader.ts:713-719` selects
  `latest_build` as the chart's latest `state='completed'` run; `:743-746` joins receipts on
  `p.build_id = latest_build.build_id`; `receiptForRequirement` (`:87-97`) marks every
  chart-build producer requirement `missing` when no receipt matches. Result: all 12
  `producer_output` requirements in the snapshot are unsatisfiable on this chart.
- `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:633-668` selects the same
  proxy ("select the same chart-level generation rule used by the capability overlay") and
  filters every `chart_facts` read on it (`:347, :376, :393, :425`). Result: the judgment
  handler reads zero facts on this chart.
- `source_query_availability.ts:4001-4030` (`source-query:judgment-query-readiness:v1`,
  `required_rows_must_exist`) requires a LAGNA sign fact under that build id. Result:
  `judgment_query` is *unavailable* in the overlay on this chart.
- `reading_checklist.ts:177-238` (`fetchSourceReceiptFence`) requires each wealth asset's
  proven/fresh receipt to carry `build_id = $3` (the judgment's selected build). Result: all
  five wealth assets report `receipt_matches_selected_build = false`.

**Twin defect (same class):** a `skip_no_delta` run writes a *new* receipt under its own run id
while the rows keep the id of the run that wrote them. Freshly observed: `ga_dashas` receipt
build `f2a62f44` (disposition `skip_no_delta`) vs all 483,870 `chart_dashas` rows under
`1f89fd4c` (disposition `build`); `ga_positions` receipt `0ac321ee` vs 1,205 facts under
`1c092ffb`. `get_dashas.ts` pages rows with `JOIN eligible_receipt ON d.build_id =
eligible.build_id` — so after RC-2 is fixed, the dasha tool would return an **empty page with no
error** on this chart.

**Why the campaign did not see it:** every DB test builds the whole fixture in one run
(`get_dashas.pagination.db.test.ts:91-116`, `reading_checklist.build_fence.test.ts:61`), so the
proxy is exact in tests and never in production. PA-R13's "all three doors bound the same active
build and returned required dark obligations" is this defect reported as a pass of dark-state
agreement.

**Falsifying check:** run `SELECT count(*) FROM chart_facts WHERE chart_id=$1 AND build_id =
(latest completed run id)` on any chart that has had at least one single-asset rebuild; if it
returns the full fact count, RC-1 is wrong. On `482012f1` it returns 0.

**Owner:** the generation semantics are the data plane's (migrations 1035/1036 authored the
target model; nothing populates it because no build has completed since they were applied on
2026-09-18). The consumer proxy is Pūrṇa's. The fix is split accordingly (§6, P1 and D3).

### RC-2 — The replacement fence counts orphaned `queued` rows in terminal runs as "in progress" (class: handler defect + orchestrator data hygiene; confidence: HIGH, live-confirmed)

**Observed:** `ganita_dashas_get` (direct MCP, read-only, `limit 1`, as-of 2026-09-22) returned
`code: ga_dashas_replacement_in_progress, restart_required: true, rows: []`. Production
`build_run_assets` holds **1,477** rows in state `queued`/`building` whose parent run is
`failed`/`stopped`/`completed` (3 charts, 83 assets, 2026-06-27 → 2026-08-21). On `482012f1`:
`ga_dashas` 3 (all `failed` runs from 2026-08-06), `ga_structural` 8, `ga_vichara` 7,
`ga_sensitive_degree` 1, and 10–16 each for most `bo_*` assets. **Zero** runs on the chart are
genuinely `planned/running/paused`.

**Where:** the predicate `OR fenced_asset.state IN ('queued','building')` with no run-state
guard appears in four read paths: `get_dashas.ts:687`, `reading_checklist.ts:210`,
`query_mechanisms.ts:407`, `query_classical_texts.ts:161`. It was introduced by Pūrṇa's own PR
#2626 (`079e77ef9`, 2026-09-17; `git log -S replacement_fence`). No test asserts that a queued
asset inside a *failed* run should block; the DB tests only cover the `ended_at`-ordering branch
(`get_dashas.pagination.db.test.ts:134-160`).

**Correction of the record:** the L3 notice and migration 1070's header attribute the stuck
guard to the missing builder grants. That hypothesis is refuted for this chart: the fence
matches rows dated 2026-08-06, five weeks before the ownership cutover, and the chart's
`ga_dashas` receipt is proven, fresh, and bound to a completed run. The grant gap was real and
is fixed; it was not the cause of this guard.

**Falsifying check:** re-run the fence predicate with `fenced_run.state IN
('planned','running','paused') AND fenced_asset.state IN ('queued','building')` in place of the
bare OR; if it still returns true for `ga_dashas` on `482012f1`, RC-2 is wrong.

**Owner:** the predicate is in Pūrṇa-touched handlers (fixable in a PR with a DB test that
inserts a failed run with a queued asset). The orphan rows are orchestrator data
(`runner.py:331-336` aborts only the current asset on failure); their one-time repair is a
production mutation requiring a decision (D3).

### RC-3 — `ga_strength` must be rebuilt under the spec the campaign activated, and nothing has been dispatched since the grants landed (class: producer-data gap; confidence: HIGH)

**Observed:** `asset_output_digest_specs` for `ga_strength`: active `3743484c…` (migration
1042, applied 2026-09-19T23:47Z), retired `7251b119…`. The chart's only proven/fresh
`ga_strength` receipt (2026-09-07, build `aa9602ce`) carries the retired spec. `build_runs`
since 2026-09-18 contains exactly one row (`ga_positions`, 2026-09-19T22:48Z, `failed`,
"orphan-watchdog: run never dispatched" — the pre-1070 permission failure). No run has been
created since 1070 applied on 2026-09-20T05:42Z.

**Consequence:** even after RC-1 and RC-2, the wealth checklist's `ga_strength` leg cannot pass
until one governed `ga_strength` rebuild completes. That rebuild would also be the first
end-to-end proof that migration 1070 unblocks the builder.

**Falsifying check:** a `ga_strength` receipt for `482012f1` with `output_digest_spec_sha256 =
3743484c…`, `receipt_state='proven'`, `freshness_state='fresh'`.

**Owner:** data-plane/L1 build owner (lease per `CAMPAIGN_COORDINATION.md`); Pūrṇa requests it
(D6).

### RC-4 — The near-miss obligation is mandatory for every wealth inquiry and nothing produces it, for want of a decision packet rather than plumbing (class: producer-data gap + missing governance decision; confidence: HIGH)

**Observed (production):** `ga_yoga_firings` for `482012f1` holds 53 rows, all `fired=true`,
`is_partial=false`, `partial_formation_pct` NULL, across 13 distinct yogas of a 233-yoga
catalogue (`reference_yogas` = `brahma_yoga_catalog` = 233). The table's schema already carries
`fired`, `is_partial`, `partial_formation_pct`, `bhanga_active`, `bhanga_rule_fired`,
`bhanga_na_reason`, `grounds_jsonb`. So the non-firing/partial universe is *representable* at
L1 today; the writer simply does not emit it.

**Observed (source):** `register_d9_judgment.ts:1684-1686` hardcodes `{unit:
'notably_absent_yogas', state: 'not_computed'}`; checklist v2 lists it as required
(`reading_checklist.ts:70-79`); `pagination.ts:280-281` treats `not_computed` as
non-exhausted → `next: 'unproven'`; the judgment obligation enters every wealth inquiry through
the omission-challenger rule `OMIT-BHAVA-BHAVAT` (`omission_challenger.ts:6`) as a `required`
obligation (`compiler.ts:460`) → `finalizeInquiryContract` (`compiler.ts:970-989`) can never
return `COMPLETE`. The two uncommitted tests in the candidate worktree assert `served` and "no
hardcode" — red-first, not delivered behaviour.

**Producer-side facts (source, `34991645b`):** `ga_yoga_writer.py:1103-1107` returns `None`
for a non-firing yoga ("one row per fired yoga"); `_evaluate_catalog_rule` computes the
non-fire reason (which leg failed) and discards it; `partial_formation_pct` is always `None`
and no writer sets `is_partial=True`, while the integrity contract (`migrations/746:45-50`) and
the serving filters (`get_yoga_firings.ts:116-130`) already anticipate such rows. The L0
catalogue (`brahma_yoga_catalog`) carries `formation_rule_jsonb` (the leg decomposition),
`partial_formation_threshold` and `bhanga_rules_jsonb`; the last two have **no non-test
reader**. At L2, `bodha_msr_signals.fact_kind` documents an `absence` class that
`bo_laksana._infer_fact_kind` (`:306-330`) never emits, and the governing L2 brief
(`CLAUDECODE_BRIEF_BO_LAKSANA_v1_0.md` §E.5, status `FOR_NATIVE_REVIEW`) already names "a
near-miss yoga (ingredients almost present)" as a curated, deterministic absence class.

**Layer placement:** which legs of a formation rule a chart satisfies is a deterministic
derivation from L1 facts and an L0 rule; *which* non-firings are notable for wealth is an
interpretation. The campaign's own ratified contract (near-miss test docstring;
`CAMPAIGN_STATE.md:49-60`; PA-E0110/E0122) rejects bare L1 non-firings as a substitute and
requires a selected-build **L2 band**. That contract is producible with **zero schema change**:
`bo_laksana` emitting `bodha_msr_signals` rows with `fact_kind='absence'`, `build_id` = the
selected build, `constituent_facts_array` = the L1 fact ids of the legs that are present, and
`configuration_jsonb` carrying the per-leg outcome derived from `formation_rule_jsonb` (a
derivation with an explicit ledger, as CLAUDE.md §B.1/§N.5 require). What is missing is
governance, not plumbing: a ratified closed candidate set, a deterministic eligibility and
incomplete-input policy, and the receipt fence for `bo_laksana` in the wealth checklist. The
handoff's "the L2 owner must deliver the band" was therefore right about the layer and wrong
about the blocker: nobody wrote the decision packet (D2).

**Falsifying check:** find any Pūrṇa-visible source (L1 table, L2 table, or service) that
returns, for a given chart and build, the set of catalogue yogas with a formation state other
than `fired`. None was found in source or data.

**Owner:** the ratification is the Native's (D2); the `bo_laksana` packet is the L2 owner's
(P4); the consumer repair and fence extension are Pūrṇa's.

### RC-5 — "Deep, evidence-driven planning" is not implemented as specified (class: planner/continuation defects; confidence: HIGH)

1. **Reasoning never reaches a provider.** `planning_policy.ts:14-18` returns `reasoning:
   'enable'`; the only adapters that read `req.reasoning` act on `'disable'` alone
   (`adapter_gemini.ts:35-38`, `adapter_deepseek.ts:13-18`); Anthropic/OpenAI adapters on this
   path never read it. `'enable'` ≡ `'auto'`.
2. **The deep slot is the weaker model.** On the live `gemini` stack `planner_deep` routes to
   `gemini-2.5-flash` (fallback `gemini-2.5-pro`) while `planner_fast` routes to
   `gemini-3.7-flash` with `thinking_level: 'high'` (`registry.ts:1267-1281`). Selecting "deep"
   for an interpretive inquiry currently *downgrades* the planner.
3. **The raw door plans with no model at all.** `api/mcp/inquiry/route.ts:182-193` compiles
   deterministically; any AI decomposition is caller-supplied `ai_proposal`. This is defensible
   under the product definition (the client owns its synthesis) but must be stated as such, not
   counted as "deep planning operational across three doors".
4. **Late-hop continuation cannot add a new capability.** The only producer of
   `discovered_frontier` after observation is the pagination path for the *same* SCU
   (`compiler.ts:829-831`); `compileInquirySuccessorContract` admits a frontier item only when
   `discovered_from` equals a served `item_id` (`:623-631`), which compile-time frontier entries
   (SCU ids, `ai_facet:*`, `independent_omission_challenger`) can never satisfy. The one test of
   "evidence-admitted successor" (`compiler.test.ts:28`) proves same-SCU paging only.
5. **Managed continuation stops after one page.** `execution_session.ts:129-135` persists
   observations without `request_position_path`, so `recordInquiryExecution` never re-readies
   the item (`compiler.ts:834`); the loop at `prashna_ask/route.ts:951-955` exits. A required
   paginated obligation then blocks closure. No test covers managed multi-page continuation.
6. **Fallback is logged, not recorded.** `fallback_used` reaches `llm_call_log` and the
   observatory (`pipeline_planner.ts:500-514, 632-638`) but no inquiry-contract field, so an
   inquiry cannot show it ran on the fallback model.

**Falsifying checks:** (1) an adapter wire-body test showing `thinkingConfig` differs between
`reasoning:'enable'` and `'auto'`; (4) a contract test where observation of SCU A's rows yields
an admitted successor item for SCU B ≠ A.

### RC-6 — The fact register does not describe what synthesis saw, and no door enforces it (class: delivery/accountability gap; confidence: HIGH)

- **Real Portal door is `/api/pariprashna`, not `/api/chat/consult`.** The UI posts to
  `/api/pariprashna` (`useLiveStream.ts:205`); `consult/route.ts` is legacy
  (`plan_bridge.ts:12`), compiles a contract it never finalizes, and emits no register.
- **Register over the wrong evidence.** `/api/pariprashna/route.ts:297-303` builds the register
  from the evidence-stage fetch (`evidence.validToolResults`), but synthesis re-fetches tools in
  its own agentic loop (`synthesis_stage.ts:455-463`); pre-fetched results reach synthesis only
  as candidate-signal ids (`:712`). Managed door trims evidence rows before the model
  (`prashna_ask_synthesis.ts:271-321`, 320,000-char budget) while the register is built from the
  untrimmed set (`prashna_ask/route.ts:1217`).
- **Interpretation mapping can essentially never pass.** A finding's `normalized_content` is
  canonical row JSON (`response_accountability.ts:30-40`); mapping requires that JSON to appear
  verbatim in `response_text` (`:306-317, 507-511`). Prose never contains it, so live readings
  routinely carry `interpretation_unmapped_fact_ids = all findings` and status
  `INCOMPLETE_RESUMABLE`. This is a false negative, the mirror image of a fabricated pass.
- **Enforcement:** Portal writes the receipt to an SSE `grade` event and `finish('ok')`
  regardless (`route.ts:355`); the UI does not consume it. Managed flips
  `completeness.status='partial'` and delivers anyway (`:1222-1225`). Raw `inquiry_finalize`
  accepts no prose and returns closure only (`api/mcp/inquiry/route.ts:380-392`).
- **Collector wire mismatch (inference, HIGH):** the Portal emits the envelope as a JSON string
  in `grade.detail` (`receipt_stage.ts:96-103`); `channel_clients.ts:68-74` reads an object at
  `data.response_accountability` → Portal rows carry `responseAccountability: null`. The only
  retained live artifact shows exactly that: Portal `answer` present (3,581 chars),
  accountability absent, facts 0/0.
- **200th-fact regression** exists in-memory only (`response_accountability.test.ts:212-224`);
  no serialized per-door variant.

**Falsifying check:** a Portal run whose persisted `inquiry_response_accountability` shows
`interpretation_unmapped_fact_ids = []` and `status = COMPLETE` for a non-trivial reading.

### RC-7 — The availability model is typed by evidence source, not by capability kind, and proves reachability rather than presence (class: semantic-discovery gap; confidence: HIGH)

- Four requirement kinds (`producer_output`, `service_probe`, `source_query`, `derived`;
  `types.ts:144-201`) and one uniform pass rule (`overlay_loader.ts:612-615`).
  `SemanticCapabilityKind` never drives proof. Planning resources, prompts, discovery services
  and dossiers are simply `deliberately_dark` (10 of 19).
- 144 of 146 `source_query` contracts are `LIMIT 0` with `empty_semantics:
  query_success_is_available`; only 2 require rows. 93 bind only `$1 chart_id`; build id is
  context, not predicate. "Available" therefore means "the handler's SQL is executable for this
  chart", labelled `freshness: 'unknown'` (`:691-693`), and the compiler admits on state alone
  (`compiler.ts:362-366`).
- Darkness is binding-level; `BindingAvailabilityDisposition` has no per-mode facet
  (`types.ts:217-229`). `get_av_transit_gating`, `get_strength`, `graha_portrait`,
  `query_planet` are dark wholesale.
- Graph: 53 edges (38 auto-derived `enables` from drill children; 15 authored, all in the
  finance cluster); 156/182 SCUs isolated with one identical rationale string; 9 authored SCUs
  vs 173 family-reviewed derivations. No concept, edge, or relation type for Bhāvat Bhāvam; no
  event kind; no ordered structure→time→event relation.

**Assessment:** this is the *correct* scaffold with the wrong proof vocabulary. It is
second-order for the first vertical slice (RC-1..4 dominate) and first-order for depth (§3.2).

### RC-8 — The control loop stopped selecting work while safe work remained (class: operating-loop failure; confidence: HIGH)

Freshly observed from the task log (aggregates only): 425 `task_complete` records; the
"blocked" verdict at 2026-09-20T14:25:05Z named three blockers (#2704 owner review; L2 near-miss
delivery; evidence store + chart-grant proof). After it: 239 completions, **all** heartbeats
(195 × "No changed external state…"), **0** working turns, while the monitor prompt (last
edited 04:54Z the same day) says "The upstream blocker must not stall independent
wealth-completeness, collector or capability work."

Safe, in-scope work that was runnable at 14:25Z and is still unstarted (all verifiable in source
without any external decision): the RC-2 fence predicate and its DB test; the RC-1 resolver; the
RC-6 collector wire-field fix and serialized 200th-fact tests; the RC-5 reasoning mapping,
`request_position_path` persistence, and fallback recording; a `ga_yoga_firings` producer
packet; a scanner-finding classification; the #2704 retarget diff analysis. None required the
evidence store, the L2 owner, or #2704.

All three named blockers were mis-stated: #2704 was never a dependency of #2705 (RC-9); the
chart grant was verifiable read-only and exists today; and "L2 must deliver the near-miss band"
named the right layer but the wrong obstacle — a decision packet, not an owner, was missing
(RC-4).

### RC-9 — The #2704 "dependency" was a misdiagnosis; #2705 is self-inconsistent and its scanner failures are allowlist line-drift (class: test/integration; confidence: HIGH)

**Observed (freshly, `gh` + local reproduction):**

- The four unit failures on #2705's head (`route_golden_stream.test.ts:562` ×2,
  `beyond_acarya_acceptance.test.ts:66, :246`) compare against hashes of #2705's **own**
  regenerated snapshot (`generated_at 2026-09-20T13:42:00Z`, file sha `6dcac829…`), while
  `BEYOND_ACARYA_ACCEPTANCE_v5.json` and the two `route_ports/baseline/*.json` goldens in the
  PR are still bound to main's snapshot (`01:38:00Z`, `ae3b0f74…`). #2705 regenerated the
  snapshot and census and did not regenerate the artifact and goldens that pin them.
- #2704 (`889ceaf9b`, base `codex/madhav-l3-claude-code`) is bound to the **L3 branch's**
  snapshot (`05:35:40Z`, `7e3a67a5…`); none of the hashes #2705's CI produced occur in its diff.
  Its four files are untouched on both `main` and the L3 branch relative to main, so it is
  mechanically retargetable — and retargeting it would break main's currently consistent
  goldens without fixing #2705. `CAMPAIGN_STATE.md:164-175` records the opposite.
- #2704's golden diff is not hash-only: obligations renumber (`obl-014 → obl-018`),
  materiality flips (`required → supporting`), labels and rationales change. Any regeneration
  (#2704's or #2705's) needs a semantic diff review, not a blessing.
- The pinning gate: 62 findings, 53 allowlisted, **9 non-allowlisted**, all in
  `source_query_availability.ts` (lines 1522–2136), all `LIMIT 0` queryability probes
  (class i), all authored by #2681 on main. #2705's four-line insertion at `:1431-1434` shifted
  them by +4; their allowlist entries are pinned by exact `line`. The allowlist supports
  `pattern` entries "for cases where line drift is expected"; three sibling probes using
  `pattern` survived. The scanner and allowlist files are byte-identical on main and HEAD; the
  same scanner on a `main` archive reports 0 new findings. No inline pragma exists; none is
  needed.

**Consequence:** there was no cross-campaign deadlock. Pūrṇa owned both failing checks and both
fixes (regenerate its own artifact and goldens against its own snapshot with a reviewed
semantic diff; convert nine allowlist entries from `line` to `pattern`). The blocked verdict's
first-named blocker did not exist.

**Falsifying check:** regenerate `BEYOND_ACARYA_ACCEPTANCE_v5.json` and the two baselines on
#2705's head and run the four tests; if they still fail with the same hashes, RC-9 is wrong.

### RC-10 — Release: a structural web/MCP revision split, not a defect, plus one detector hazard (class: release configuration; confidence: HIGH)

Freshly observed: web serves `c58e8666` (PR #2712, deployed 12:24Z today by `workflow_run`);
MCP and sidecar serve `09d99894` (PR #2698, manual `workflow_dispatch` on 2026-09-20).
`deploy-web` runs on every successful main CI; `deploy-mcp`/`deploy-sidecar` only when their
paths change or `force_all` (`deploy.yml:1078-1082, 1359, 1554-1559`). The split is therefore
permanent by design and needs a **compatibility attestation** (protocol/snapshot hash agreement
across doors), not repeated forced redeploys. Hazard: the change detector diffs against
`latestReadyRevisionName` (`deploy.yml:304-322`), which can be a 0%-traffic candidate that
failed smoke; not currently manifest.

### True authority dependencies (the only items that genuinely need someone else)

| Dependency | Who | What exactly (see §7) |
|---|---|---|
| Restricted evidence store designation | Native / security owner | D1 |
| Near-miss band ratification (candidate set, eligibility, receipt fence) | Native | D2 |
| Orphan-row repair + generation-head population | Native + data-plane owner | D3 |
| `planner_deep` model ruling | Native (model moves are native-ruled) | D4 |
| #2704 integration ownership | none — withdrawn, see D5 | — |
| `ga_strength` rebuild lease | Data-plane/L1 build owner | D6 |
| Judge execution budget | Native (bounded, existing capacity) | D7 |
| `WATCHDOG_SECRET` on tagged revision | Security/runtime owner (separate, unchanged) | carried |

### Critical path

```
D2/D3 decisions ──┐
P1 resolver ──────┼──► P2 fence ──► (D6) P3 ga_strength rebuild ──► first supported-complete
P4 near-miss L1 ──┘        │            wealth reading on candidate (M1)
P5 planner ──────────────── ┤
P6 delivery + collector ────┘
P0 reconcile #2705 (own goldens + allowlist drift; parallel, independent of the above)
P7 candidate 105 ──► P9 live 105 ──► close        P8 availability typing (post-M1, parallel)
```

## 3. Requirements-to-runtime matrix

### 3.1 The ten required outcomes

| # | Outcome | Concepts / output families | Source paths | Availability state (candidate source) | Actual consumer | Tests | Candidate / live evidence | Gap | Owner |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Discover meaningful outputs, relations, prerequisites, drill paths | 182 SCUs, 259 concepts, 53 edges, `drill_children` | `knowledge/compiler.ts`, `editorial.ts`, `editorial_review.ts`, `planner_projection.ts` | source-complete accounting; 9 authored SCUs; 156 isolated | `compiler.ts` floors/search/traversal | `knowledge.test.ts`, `availability_coverage.test.ts` | none | RC-7: no Bhāvat Bhāvam, no event kind, edges only in finance | Pūrṇa semantic worker |
| 2 | Catalogue freshness | snapshot + census generators, `assertPinnedCapabilityKnowledgeCurrent` | `snapshot.ts:15-22`, `codegen:*:check` | PASS (fail-closed staleness) | all doors | CI check jobs | recorded | none material | — |
| 3 | Executable chart/build-correct availability | 167 contracts (142 source_query, 12 producer_output, 9 probe, 7 derived) | `overlay_loader.ts`, `source_query_availability.ts` | source-accounted; **unsatisfiable in production for all 12 producer_output and the judgment probe (RC-1)** | overlay at each door (`api/mcp/inquiry/route.ts:188`, `prashna_ask/route.ts:546`, `api/pariprashna` via `plan_stage.ts:336`) | unit + `overlay_loader.db.test.ts` (single-run fixtures) | PA-R13 "dark-state agreement" = RC-1 symptom | RC-1, RC-2, RC-7 | Pūrṇa + data plane |
| 4 | Deep reasoning for interpretive inquiries | `planner_deep`, `reasoning:'enable'` | `planning_policy.ts`, `pipeline_planner.ts:402-482`, `adapter_gemini.ts:35-38`, `registry.ts:1267-1281` | flag unmapped; deep slot = `gemini-2.5-flash` | Portal + managed only | `planning_policy.test.ts` (helper only) | none | RC-5.1–3 | Pūrṇa inquiry worker + D4 |
| 5 | Evidence-driven continuation | `discovered_frontier`, successor compile | `compiler.ts:786-842, 613-694`, `execution_session.ts:129-135` | same-SCU paging only | Portal/managed loops | `compiler.test.ts:28` (paging) | none | RC-5.4–5 | Pūrṇa inquiry worker |
| 6 | Planning separate from synthesis | separate call types/prompts | `plan_stage.ts:166-169` vs `safety_gate.ts:138-139`; `prashna_ask/route.ts:275-278` vs `:308` | PASS | both managed doors | route tests | recorded | none | — |
| 7 | Every synthesis-visible material fact delivered | `InquiryFactRegister`, coverage receipt | `response_accountability.ts`; `api/pariprashna/route.ts:297-303`; `prashna_ask/route.ts:1214-1225` | present, mis-bound | Portal, managed | in-memory 200th-fact | live: 0 delivered facts on every retained row | RC-6 | Pūrṇa delivery worker |
| 8 | Shared evidence/closure across three doors | `door_parity.ts:86-136` | all three routes | PASS for contract/closure; register/prose not compared | all | `door_parity.test.ts`, `runtime_channel_coverage.test.ts` | PA-R07 partial | raw finalize has no answer register (RC-6) | Pūrṇa |
| 9 | Pagination, interruption, cross-instance | lifecycle tables; `ManagedInquiryExecutionSession` | `lifecycle_store.ts`, `managed_job_store.ts`, `execution_session.ts` | PASS source + disposable DB | managed | `migration_1038.db.test.ts:268,287` | PA-R04/R11 open live | managed one-page (RC-5.5); no live proof | Pūrṇa lifecycle owner |
| 10 | Intended release live + acceptance | `deploy.yml`, collector, judge | §RC-10; `platform/scripts/purna/` | release chain PASS; acceptance NOT_RUN | — | collector/judge unit tests | 0/3 historical | RC-8, RC-10, D1 | integrator + release duty |

### 3.2 The five original cases and the six families — material dependencies

| Case / family | Material evidence dimensions | Blocking root causes today | What must be true to pass |
|---|---|---|---|
| `wealth_mechanism_timing_contradiction` | judgment (bhāva/lord/kāraka grades), D2/D9/D11 pivots, Ashtakavarga, dashas, mechanisms, contradictions, near-miss | RC-1 (judgment reads 0 facts; overlay dark), RC-2 (dashas + checklist fence), RC-3 (strength spec), RC-4 (near-miss), RC-6 (register) | P1+P2+P3+P4+P6 |
| `career_bhava_varga_timing` | D10, judgment, strength, dashas, transits | RC-1, RC-2, RC-3 (`get_strength` dark → career composite fail-closed) | P1+P2+P3 (+ transit contract from P8) |
| `marriage_varga_cancellation_timing` | D9, yoga firing + bhaṅga, judgment, dashas | RC-1, RC-2; bhaṅga rows exist (3 rows `bhanga_active=true` on the chart) | P1+P2 |
| `house_yoga_later_hop` | yoga firing → house/lord follow-up from observed evidence | RC-5.4 (no new-SCU hop) | P5 |
| `long_divisional_continuation` | divisional pagination to exhaustion, resume | RC-5.5 (managed one page); RC-1 for build binding | P1+P5 |
| Wealth W1–W5 | as above + strain/inhibitor contradiction, horizon-bounded window | RC-1..4, RC-6 | P1–P4, P6 |
| Career C1–C5 | profession links, D10, strength, yoga, period/transit | RC-1..3; `call_transit_search` dark (probe family) | P1–P3, P8 |
| Marriage M1–M5 | houses/lords, kārakas, D9, cancellation, timing | RC-1, RC-2 | P1, P2 |
| Family F1–F5 | D7, houses/lords, strength, inhibitors | RC-1..3 | P1–P3 |
| Health H1–H5 | vulnerability/resilience, Bhāvat Bhāvam, vargas, boundaries | RC-1..3; RC-7 (no Bhāvat Bhāvam concept) | P1–P3, P8 |
| Events E1–E5 | LEL intake, frozen chronology, mechanisms, activation windows | RC-1, RC-2; LEL source-query contract present | P1, P2 |

Every deliberately-insufficient case (mode 5) depends on typed receipts the bridge cannot yet
earn (`answers_from_collection.ts:78-81` hard-codes `CHANNEL_<GATE>_RECEIPT_UNAVAILABLE` for
`required_evidence_dimensions`, `named_missing_evidence`, `bounded_insufficiency`). Until those
receipts are produced from the register (P6), **no product case can pass the deterministic gate
even with perfect collection**. This is the single most important fact about the acceptance
harness and was not in the handoff.

## 4. The nineteen dark bindings — classification and grouping

Proof-kind legend: **MP** materialized producer output; **SP** service probe; **SQ** source query
with rows required; **DR** derived composition; **PLAN** planning/resource capability whose
correct proof is "renders/plans correctly", not "answers"; **NONE** genuinely unsupported.

| Binding | Classification | Shared root | Correct proof kind | Disposition |
|---|---|---|---|---|
| `get_strength` | required product dependency | strength group | MP per category (21) + frame facts SQ | repair: spec 1042 covers Ashtakavarga families; add per-category receipts or a category-scoped `partial` state |
| `graha_portrait` | required | strength group | DR over strength + positions | unblock with strength; expose partial portrait as `partial`, not dark |
| `query_planet` | required | strength group | DR | same |
| `get_av_transit_gating` | required (SAV/BAV mode); optional (Kakshya sidecar mode) | multi-mode | per-mode: SQ for SAV/BAV, SP for Kakshya | needs per-mode disposition (RC-7); serve proven mode with a mode flag |
| `call_transit_search` | required for time-bounded cases | sidecar endpoint group | SP (route-specific) | add an authenticated probe for the actual route under the existing probe family |
| `query_muhurat` | optional for the 35 cases | sidecar endpoint group | SP | same mechanism, lower priority |
| `pact_query` | required (events family) | direct-DB composite | DR over judgment + varga SQ + dashas + transit trigger | contract the chain once RC-1 resolver exists |
| `synergy_cross_layer` | required (deep family modes) | direct-DB composite | DR | same |
| `synergy_pipeline` | optional (dry-run is a plan) | direct-DB composite | PLAN (dry-run) / DR (executed) | split modes |
| `compose_large_n` | optional | direct-DB composite | DR (gestalt + tail-watch) | contract or expose components as qualified partial |
| `classical_attribution_lookup` | required for citations | attribution replacement | SQ against the canonical citation source (`ref_classical_citation_get` family) | keep honest failure; route citations to the replacement |
| `intent_classify` | legitimate PLAN (prompt resource) | planning resources | PLAN: template renders with schema | not dark; mark `resource_ok`, exclude from answer readiness |
| `route` | legitimate PLAN | planning resources | PLAN | same |
| `tool_search` | legitimate discovery service | planning resources | SP-lite: index built from the pinned snapshot hash | prove index = snapshot; not circular |
| `maro_profiles` | legitimate dossier | MARO | PLAN (static, labelled unmeasured) | `resource_ok`, exclude from readiness |
| `maro_orchestrate` | planning metadata | MARO | PLAN | same |
| `maro_mcp_surface` | planning metadata | MARO | PLAN | same |
| `channel_chat_dispatch` | descriptor of the legacy `consult` path | channel introspection | NONE for the descriptor; the real Portal door is `/api/pariprashna` (RC-6) | retire the descriptor's promise or repoint it |
| `channel_mcp_wiring` | static wiring map | channel introspection | generated projection from real bindings | generate; do not gate |

Net: 7 required product dependencies in 3 shared roots (strength, sidecar probes, direct-DB
composites) plus the attribution replacement; 8 planning/resource capabilities that need a
different proof type, not implementation; 4 optional. The "uniform gate misclassifies unlike
kinds" hypothesis in the handoff is **confirmed**.

## 5. Preserve, change, remove

**Preserve unchanged:** everything in §1.2; the frozen orchestrator contract; canonical L0/L1
identities; the 5+30 cases and fingerprint; the 34 route obligations; applied migrations
1033–1042 and 1070; the collector's tamper-evidence; the deployment outcome gate; the durable
lifecycle tables and their protected ownership; the two uncommitted red-first tests in the
candidate worktree (do not delete or stage until P4 makes them pass).

**Change (bounded):** build-identity resolution (P1); four fence predicates (P2); `ga_strength`
attestation via rebuild (P3); `bo_laksana` absence signals + judgment consumer + wealth fence (P4); planner
reasoning mapping, deep-slot routing, successor join, managed paging, fallback recording (P5);
register binding, interpretation mapping, Portal enforcement, raw certification, collector wire
field, per-door serialized 200th-fact tests, typed deterministic-gate receipts (P6); availability
proof typing and per-mode dispositions (P8); the monitor (replace with event triggers, §8).

**Remove or retire:** the `channel_chat_dispatch` promise on the legacy consult route (or
repoint the descriptor); the recorded "#2704 dependency" classification of #2705's failures
(`CAMPAIGN_STATE.md:164-175`, PA-E0142) — correct the record; the recorded attribution of the
dasha guard to the grant gap (migration 1070 header and the L3 notice) — correct the record, do
not edit the applied migration; the plan header's `DRAFT — AWAITING NATIVE APPROVAL` line
(reconcile once, P0); the nine exact-`line` allowlist entries for the drifted probes (convert to
`pattern`, do not delete).

## 6. Elevated execution plan

Conventions: one integrator (§8). Effort is in focused engineer-days with stated assumptions;
none is a date. "Exit" is measurable. Each packet names its stop condition and the next action
on failure. Packets marked ∥ can run concurrently with file-disjoint ownership.

### P0 — Reconcile once (integrator; 1–1.5 days)

**Objective.** One current-state projection; #2705 rebased on current main with its own
acceptance artifact and route goldens regenerated against its own snapshot and semantically
reviewed; the nine drifted allowlist entries converted to `pattern`; #2704 left with L3.

**Files.** `docs/superpowers/plans/2026-09-17-purna-product-completion-v2.md` (header status
line only); `LIVE_COMPLETION_MATRIX_v1.json` (add a `review_2026_09_22` pointer, no row
rewrites); `CAMPAIGN_STATE.md` (one correction entry for the #2704 misattribution);
`00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v5.json`;
`platform/tests/pariprashna/route_ports/baseline/{branch-deep-dive,branch-completeness-receipt}.json`;
`platform/scripts/governance/fact_category_pin_allowlist.json` (nine entries: `line` → `pattern`).

**Starting state.** `codex/purna-wealth-near-miss` at `34991645b`; two uncommitted tests
preserved and not staged; main at `50d49e19d` or later.

**Authority.** Existing: Pūrṇa owns its artifact, goldens and allowlist entries. Nothing external.

**Reproduction.** `gh pr checks 2705` → Unit Tests + Fact-Category Pinning Gate failing;
`python3 platform/scripts/governance/check_fact_category_pinning.py --json` on the head → `new
9`; on a `git archive origin/main` extract → `new 0`.

**Repair.** (1) Rebase on main; regenerate snapshot and census once through their generators.
(2) Regenerate `BEYOND_ACARYA_ACCEPTANCE_v5.json` and both route-port baselines against the
rebased snapshot; diff the goldens **semantically** (obligation ids, materiality, labels,
rationales) and record in the PR every non-hash change with a one-line reason; a materiality
flip `required → supporting` on a frozen case is a finding to explain, not to accept silently.
(3) Convert the nine allowlist entries (lines 1518, 1541, 1566, 1595, 1621, 1701, 2000, 2079,
2132 on main) from `line` to a `pattern` anchored on each contract id; keep the justification
text. Do not touch the scanner. (4) Do not cherry-pick #2704; note in the PR that it belongs to
#2695's base branch.

**Tests / exit.** The four tests green on the rebased head; pinning gate `new 0` with the
scanner unchanged; #2705 mergeable with only its own content; the semantic golden diff recorded.

**Dependencies.** None. ∥ with everything.

**Stop / recovery.** If a semantic golden change cannot be explained from #2705's own source
changes, stop and bisect the generator input; do not bless the golden.

### P1 — Chart generation resolver (Pūrṇa evidence worker; 2–3 days; the failed-abstraction replacement)

**Objective.** Replace the chart-wide "latest completed run" proxy with one shared per-asset
resolver that binds each consumer to the run that **wrote the rows it reads**, and make the
overlay version hash that vector.

**Files.** Create `platform/src/lib/retrieval/registry/generation/resolve_chart_generation.ts`
+ `.test.ts` + `.db.test.ts`. Modify `knowledge/overlay_loader.ts:703-760` (replace
`latest_build` CTE and the `p.build_id = latest_build.build_id` join), `knowledge/overlay.ts:50-58`
(hash the per-asset vector), `layers/register_d9_judgment.ts:633-668` (call the resolver; keep
the hard-error behaviour), `layers/reading_checklist.ts:177-238` (`receipt.build_id = ANY of the
resolved per-asset ids`), `knowledge/source_query_availability.ts:4001-4030` (judgment probe uses
the resolved L1 build for `chart_facts`), `layers/L1_ganita/get_dashas.ts` page join (rows under
the resolved *writing* run, not the receipt run).

**Interface (produces).**

```ts
export interface ResolvedAssetGeneration {
  asset_id: string
  receipt_build_id: string        // run that issued the proven+fresh receipt under the active spec
  rows_build_id: string           // run whose rows are current (== receipt_build_id unless a no-delta run re-receipted)
  spec_sha256: string
  observed_at: string
}
export interface ChartGeneration {
  chart_id: string
  assets: Record<string, ResolvedAssetGeneration>
  generation_hash: string         // sha256 over sorted (asset_id, rows_build_id, spec_sha256)
  source: 'per_asset_receipts' | 'generation_heads'   // switch to heads when D3 populates them
}
export function resolveChartGeneration(chartId: string, assetIds: readonly string[], query?: QueryExecutor): Promise<ChartGeneration>
```

`rows_build_id` is derived per asset from the receipt chain: walk `upstream_receipts`/the
asset's completed runs backward from `receipt_build_id` to the most recent run whose
`build_run_assets.disposition = 'build'`. If the data plane later populates the generation
heads, the resolver reads them and sets `source: 'generation_heads'`; consumers do not change.

**Minimal failing reproduction (DB test).** Insert three completed runs for one chart: run A
builds `ga_positions` (rows stamped A), run B builds `ga_dashas`, run C `skip_no_delta`
re-receipts `ga_positions` under C. Assert: overlay marks `ga_positions` producer requirement
`passed`; judgment probe finds the LAGNA fact; `get_dashas` serves rows; `generation_hash`
changes when A is superseded. Current code fails all four.

**Exit.** On `482012f1` in a candidate environment: overlay `producer_output` requirements for
`ga_positions`, `ga_structural`, `ga_vichara`, `ga_sensitive`, `ga_sensitive_degree`, `ga_dashas`
pass; `judgment_query` available; `assess_wealth`'s checklist reports
`receipt_matches_selected_build = true` for four of five assets (fifth after P3).

**Dependencies.** None to start. ∥ with P2, P5, P6. **Stop:** if the per-asset chain cannot
determine `rows_build_id` for an asset (no `build` disposition reachable), the resolver returns
that asset as `unresolved` and the overlay marks it dark with reason `generation_unresolved` —
never guess.

### P2 — Replacement-fence repair (Pūrṇa evidence worker; 0.5–1 day) ∥

**Objective.** A queued/building asset row blocks only while its run is non-terminal.

**Files.** `get_dashas.ts:687`, `reading_checklist.ts:210`, `query_mechanisms.ts:407`,
`query_classical_texts.ts:161`; extend `get_dashas.pagination.db.test.ts` and
`reading_checklist.build_fence.test.ts`.

**Repair.** Replace `OR fenced_asset.state IN ('queued','building')` with
`OR (fenced_run.state IN ('planned','running','paused') AND fenced_asset.state IN
('queued','building'))` in all four; keep the `ended_at` ordering branch unchanged.

**Failing test.** Insert a `failed` run with a `queued` `ga_dashas` asset row dated before the
proven receipt; assert the tool serves rows (today: `ga_dashas_replacement_in_progress`).

**Exit.** Live (after release) `ganita_dashas_get` on `482012f1` returns rows for
vimshottari level 1; `assess_wealth` checklist reports `replacement_in_progress=false` for all
five assets.

**Related decision.** D3 authorises a one-time data repair of the 1,477 orphan rows (marking
them `aborted` with `ended_at = run.ended_at`) as a governed migration owned by the
orchestrator. P2 does not depend on it; it removes a hazard for future consumers that copy the
old predicate.

### P3 — `ga_strength` rebuild under spec 1042 (data-plane/L1 build owner under lease; Pūrṇa verifies; 0.5 day + build time)

**Objective.** One governed `ga_strength` rebuild for `482012f1` producing a proven/fresh
receipt with `output_digest_spec_sha256 = 3743484c…`; simultaneously the first post-1070 build.

**Authority.** D6 (lease claim per `CAMPAIGN_COORDINATION.md`; existing builder identity).

**Verification (read-only SQL, Pūrṇa).** Receipt row as above; `build_runs` row `completed`;
`asset_freshness = fresh`; `asset_throughput.state = lit`.

**Stop.** If the run fails on permissions, that is a new grant gap (report the exact
relation); if it fails on the writer, it is an L1 defect (file to L1 with the run id). Do not
edit migration 1042.

### P4 — Near-miss band: `bo_laksana` absence signals + consumer (L2 owner + Pūrṇa consumer; 2–4 days; gated on D2)

**Objective.** Produce the selected-build L2 near-miss band the campaign's contract requires,
with zero schema change, and consume it honestly.

**Decision packet first (D2, one page, for the Native).** (a) Closed candidate set: the yoga
families relevant to wealth from `yoga_families`/`yoga_family_members` (dhana, rāja, the
pañca-mahāpuruṣa members with wealth signification), enumerated by `canonical_id`. (b)
Eligibility: a candidate is a near-miss when every formation leg of `formation_rule_jsonb` but
one is satisfied by an L1 fact under the resolved build, evaluated by the same leg evaluator
`ga_structural_writer._evaluate_catalog_rule` already uses (read-only reuse, no new rule
authoring); "one leg" is the proposal to ratify, not a threshold invented here. (c)
Incomplete-input policy: if any leg's input fact is absent for the build, the candidate is
`indeterminate`, never near-miss. (d) Receipt: `bo_laksana`'s existing output-digest receipt
(spec at `migrations/929`) becomes a required fence entry for the wealth checklist. The
BO_LAKSANA brief §E.5 is the ratification surface; adopting it closes D2.

**Producer packet (L2, `bo_laksana`).** Emit `bodha_msr_signals` rows with
`fact_kind='absence'`, `signal_type_class='yoga'`, `build_id` = resolved build (P1),
`constituent_facts_array` = the L1 `chart_facts.fact_id`s of the satisfied legs,
`configuration_jsonb` = per-leg outcomes from `formation_rule_jsonb`, `classical_sources_jsonb`
from `brahma_yoga_catalog.classical_citations`, `cancellation_modifier` from
`bhanga_rules_jsonb` where applicable. Idempotency per §N.3. Existing `UNIQUE(chart_id,
ayanamsha_id, signal_type_id, build_id, configuration_jsonb)` holds. `_infer_fact_kind`
(`bo_laksana.py:306-330`) gains the `absence` branch.

**Consumer (Pūrṇa, `register_d9_judgment.ts:1683-1687, 1097-1106, 41-44, 465-467`).** Replace
the hardcode with a read of `absence` signals for the ratified candidate set under the resolved
build: `served` with the array and `count` when the producer ran for this build (rows may be
zero → `empty_for_this_chart` only if the producer's receipt for this build exists);
`source_unproven` when no `bo_laksana` receipt exists for the build. Add `bo_laksana` to the
wealth source fence (`reading_checklist.ts:114-120`). Retire the `notably_absent_not_checked`
flag when the unit is served. The two uncommitted tests become the acceptance tests.

**Optional substrate (L1, later, not blocking):** `ga_yoga_writer.py:1103-1107` could stop
discarding the non-fire reason and emit `fired=false` rows with `grounds_jsonb`, giving the L2
signal leg-level fact ids to cite without re-evaluating the rule. Schema and serving filters
already exist. This is a separate L1 packet with its own digest-spec migration; it is not a
substitute for the L2 band.

**Exit.** `assess_wealth` on the candidate returns the unit `served` with the array; the
`bo_laksana` receipt for the build fences the checklist; `finalizeInquiryContract` reaches
`COMPLETE` on `wealth_mechanism_timing_contradiction` with all required obligations
served/empty.

**Stop.** If D2 is deferred, the wealth case stays honestly non-complete; do not relabel the
unit `not_applicable`, and do not ship an L1 non-firing proxy under the L2 name.

### P5 — Deep planning and real continuation (Pūrṇa inquiry worker; 2–3 days) ∥

**Files.** `adapters/providers/adapter_gemini.ts:35-38` (map `'enable'` → `thinking_level:
'high'`/`thinkingBudget` from quirks; `'auto'` → quirks default; `'disable'` unchanged),
`adapter_anthropic.ts` (map to `thinking` when the model supports it), wire-body tests
(`adapter_gemini_wire_body.test.ts`); `models/registry.ts:1267-1270` (per D4);
`vidhi/inquiry/compiler.ts:613-694, 786-842` (successor join accepts `discovered_from` of the
form `evidence:<item_id>:<rule_id>`), new `vidhi/inquiry/evidence_frontier.ts` (deterministic
rules from observed rows → frontier items: `bhanga_active=true` → `scu.yoga.firing_and_cancellation`
+ `judgment_query`; a served dignity fact with `dignity_state='debilitated'` → nīcha-bhaṅga
check; a served mechanism naming a house → `judgment_query` for that house; a served firing with
`activation_dasha_periods` → `get_dashas` for those periods), `execution_session.ts:129-135`
(persist `request_position_path`), `prashna_ask/route.ts` and `pipeline_planner.ts` (record
`fallback_used` + `active_model_id` into the contract's `planning_provenance`).

**Failing tests.** (a) wire-body: `reasoning:'enable'` yields a `thinkingConfig` different from
`'auto'`; (b) contract: observing rows for SCU A admits a successor item for SCU B via
`evidence_frontier`; (c) managed session: page 2 is dispatched on the same job; (d) contract
carries `planning_provenance.fallback_used`.

**Exit.** `house_yoga_later_hop` produces a later-hop retrieval absent from the initial plan on
the candidate; `long_divisional_continuation` reaches `exhausted:true` through the managed door.

### P6 — Complete delivery and honest receipts (Pūrṇa delivery worker; 3–4 days) ∥ (interfaces fixed with P5 first)

**Files.** `api/pariprashna/route.ts:297-355`, `pariprashna/pipeline/synthesis_stage.ts:241-263,
455-463`, `pipeline/prashna_ask_synthesis.ts:271-321`, `prashna_ask/route.ts:1214-1225`,
`response_accountability.ts:30-40, 306-317`, `api/mcp/inquiry/route.ts` (+ new
`inquiry_certify` operation), `platform-mcp/src/tools/register_inquiry_lifecycle.ts`,
`scripts/purna/channel_clients.ts:68-74, 240-268`, `scripts/purna/answers_from_collection.ts:65-81`.

**Repairs.**
1. Bind the register to what synthesis saw: Portal records every tool result the synthesis loop
   fetched (`synthesis_stage.ts:455-463`) into the evidence set the register is built from;
   managed records the trimmed row set and marks trimmed-away rows `disposition:
   'budget_excluded'` in the register (visible, never silent).
2. Replace JSON-substring interpretation mapping with citation-marker mapping: synthesis emits
   `[[fact:<fact_id>]]` markers (the citation protocol already exists,
   `pariprashna/citations/`); a finding is mapped when its marker appears in a prose span or in a
   structured findings part. Unknown markers fail citation resolution.
3. Portal: the coverage receipt's status becomes the SSE terminal grade and is persisted; the
   UI renders the register beneath the reading (locked layout untouched).
4. Raw: add `inquiry_certify(lifecycle_token, answer_text, fact_register_projection)` that runs
   `buildResponseCoverageReceipt` server-side and returns `certified_complete: boolean`;
   `inquiry_finalize` stays closure-only. A client that never certifies never receives
   `certified_complete`.
5. Collector: read the Portal envelope from `grade.detail` (parsed) and fail closed if absent.
6. Typed gate receipts: derive `required_evidence_dimensions` (from obligation → dimension map),
   `named_missing_evidence` and `bounded_insufficiency` (from `status_reasons` + gaps) so mode-5
   cases can be earned, not hard-coded to fail.
7. Serialized 200th-fact tests: one per door, through NDJSON/SSE/MCP tool result.

**Exit.** A candidate wealth run through each door yields a register whose
`interpretation_unmapped_fact_ids` is empty and status `COMPLETE`; removing one finding from the
serialized envelope fails the collector's validation on all three doors.

### P7 — Candidate acceptance (integrator; 1–2 days after M1)

**Prerequisites.** D1 (store), D7 (budget). Config v3 with per-door expected revisions and
`observedChartId` binding; approved principal's `view` grant on `482012f1` (exists today —
re-verify at run time by the same read-only query).

**Steps.** Three first-slice inquiries (wealth original, marriage original, `events_1`) → cost
and latency measured → full 35 × 3 → judge → acceptance CLI. Failed cases go back to the
closure loop with their first failing boundary; the corpus is not edited.

**Exit.** 105 candidate executions recorded; every supported-complete case COMPLETE with
deterministic gates green; every mode-5 case names the correct missing evidence; four-axis
scores meet the thresholds.

### P8 — Availability typing and dark-binding repair by shared root (Pūrṇa semantic worker; 3–5 days; starts after M1, before P9)

**Files.** `knowledge/types.ts:197-229` (add `proof_kind: 'answer' | 'plan' | 'resource' |
'discovery'` on the declaration; add per-mode facets to dispositions), `editorial_review.ts:68-208`,
`overlay_loader.ts:612-627`, `source_query_availability.ts` (promote chart-scoped fact probes to
`required_rows_must_exist` bound to the resolved build from P1), the strength/probe/composite
groups in §4.

**Exit.** Nineteen rows re-dispositioned per §4 with tests; `get_av_transit_gating` serves its
SAV/BAV mode with a mode flag; `get_strength` reports per-category attestation; the graph gains
a `bhavat_bhavam` relation and an `event` concept with edges to LEL intake and yoga firing; the
census asserts zero `deliberately_dark` among required-product bindings.

### P9 — Live close (integrator + release duty; 1–2 days)

Protected merge of the integrated candidate; compatibility attestation across web/MCP/sidecar
(pinned protocol + snapshot hash, not forced same-SHA); separate 105 live executions; one
longest-inquiry recovery window and one scheduler cycle observed; matrix/state/events updated
once; goal completed only after live acceptance.

### Effort summary (focused engineer-days; assumes one integrator + two workers, no new blockers)

| Packet | Range | Critical path? |
|---|---|---|
| P0 | 1–1.5 | no |
| P1 | 2–3 | yes |
| P2 | 0.5–1 | yes |
| P3 | 0.5 + build | yes (external lease) |
| P4 | 2–4 | yes (D2) |
| P5 | 2–3 | parallel |
| P6 | 3–4 | parallel → yes at M1 |
| P7 | 1–2 | yes |
| P8 | 3–5 | parallel post-M1 |
| P9 | 1–2 | yes |

Roughly 9–14 engineer-days of critical-path work with 2–3 days of external waits (D2, D3, D6),
revisable at M1 from the first supported-complete wealth run. Not a calendar promise.

## 7. Concrete decision requests

| ID | Decision | Owner | Exact ask | What unblocks |
|---|---|---|---|---|
| D1 | Restricted evidence store | Native / security owner | Designate **one** existing GCS prefix (the ledger names `madhav-astrology-chart-documents/purna/acceptance/…`) as the restricted acceptance store with: access limited to the approved principal + Native; retention ≥ 90 days; no public/legacy broad-ACL bucket. Return the prefix and the IAM binding name. No new bucket needed. | P7, P9 |
| D2 | Near-miss band ratification | Native | Ratify the absence class in `CLAUDECODE_BRIEF_BO_LAKSANA_v1_0.md` §E.5 with P4's one-page packet: closed candidate set (wealth families by `canonical_id`), the "all legs but one" eligibility rule using the existing leg evaluator, the indeterminate-input policy, and `bo_laksana`'s receipt as a wealth fence entry. No score, case, or denominator changes. Fallback if deferred: the wealth cases remain honestly non-complete; no relabel. | P4 |
| D3 | Orphan-row repair and generation heads | Native + data-plane owner | (a) Authorise a governed migration (orchestrator-owned, next number in the L3/data-plane range) that sets `build_run_assets.state='aborted', ended_at=run.ended_at` for rows in terminal runs — 1,477 rows, 3 charts, read-only enumeration script first; (b) name the owner and packet for populating `l1/l2_data_plane_generation_heads` on the next completed build so P1's resolver can switch `source`. | P2 hygiene, P1 durability |
| D4 | `planner_deep` routing | Native | Rule which model the deep slot uses on the `gemini` stack (today `gemini-2.5-flash`, weaker than the fast slot). Recommendation: `gemini-3.7-flash` primary with `thinking_level:'high'` and `gemini-3.1-pro-preview` fallback, pending cost check in P7's first slice. | P5 |
| D5 | #2704 ownership | withdrawn | No decision needed: #2704 is bound to the L3 branch's snapshot and stays with #2695; #2705 regenerates its own artifact and goldens (P0). Recorded here so the campaign's "owner review of #2704" blocker is visibly closed. | P0 |
| D6 | `ga_strength` rebuild lease | Data-plane/L1 build owner | Claim a lease, dispatch `ga_strength` rebuild for `482012f1`, confirm receipt under spec `3743484c…`. First post-1070 build; report any permission failure by relation name. | P3 |
| D7 | Judge budget | Native | Confirm 105 candidate + 105 live inquiry executions plus ~210 judge calls at `eval_judge = gemini-2.5-pro` fall within existing authorised capacity, measured after three first-slice runs. | P7, P9 |
| — | `WATCHDOG_SECRET` on `amjis-web-02826-huf` | Security/runtime owner | Unchanged from the successor addendum; not a Pūrṇa gate. | — |

## 8. Execution control mechanism

1. **One integrator** owns the queue, shared routes, generated artifacts, and release. Two
   workers at most, file-disjoint: *evidence worker* (P1, P2, P8 files) and *inquiry/delivery
   worker* (P5, P6 files). Producer packets (P3, P4-L1) go to their layer owners; the integrator
   holds the request and its verification query.
2. **Runnable queue, always non-empty until done.** The queue is the packet list above, each
   item tagged `runnable`, `waiting:<event>`, or `done`. The next item is the highest-priority
   `runnable` item whose files are not held by another worker. A `waiting` item lists the exact
   event that flips it (`PR #N merged`, `build_runs row <id> completed`, `decision D2 recorded`).
3. **Blocked means "queue empty of runnable items"**, and nothing else. Declaring the goal
   blocked requires printing the queue and showing every item is `waiting` or `done`. The
   2026-09-20 verdict would have failed this test.
4. **Review boundaries.** Independent read-only review at: P1 (generation semantics), P6 step 4
   (raw certification is a security surface), P4 producer packet (writer contract), and the
   integrated candidate before P7. Not per commit.
5. **Anti-repeat.** Same failure fingerprint twice → stop that sequence, reproduce at the first
   failing boundary, continue other runnable work. No full-suite runs on unchanged source. No
   snapshot/census regeneration except at a packet boundary.
6. **Waiting is event-driven.** The 10-minute heartbeat is retired. Each `waiting` event gets
   one watcher (GitHub merge event, `build_runs` state change via a read-only query at a
   30-minute cadence, or a decision recorded in the matrix). A watcher fires a single
   notification and re-queues the item; it never narrates unchanged state.
7. **Monitoring is useful** only while an in-flight operation the campaign started (a CI run, a
   build run, a deployment) can change state; it stops when the queue is empty of runnable
   items and every waiting item has a named owner who has acknowledged the ask. At that point
   the correct action is a single decision packet to the Native, not a timer.
8. **Progress reporting** at milestones only: supported-complete cases per door; RC-1..RC-6
   status; deployed SHAs per service; the queue.

## 9. Acceptance and handback

- Denominators preserved: 5 immutable cases, 34 route obligations, 30 product scenarios, 105
  candidate + 105 live executions, four-axis thresholds (mean ≥ 4, min ≥ 3), deterministic
  overrides. Human-expert research remains `NOT_RUN` and separate.
- **No requirement change proposed.** D2 ratifies the L2 absence class the campaign's own
  contract already requires; it does not lower any score, remove any case, or turn a
  supported-complete case into an insufficiency case. The earlier draft of this review
  considered splitting the unit into L1/L2 halves; the PR/CI audit showed the L2 band is
  producible without schema change, so the split is withdrawn.
- **One correction of record proposed:** the dasha-guard attribution in migration 1070's header
  and the L3 notice (documentation only; the applied migration is not edited).
- Milestones: **M1** first supported-complete wealth reading on the candidate through all three
  doors with a COMPLETE register (after P1–P4, P6 steps 1–5); **M2** full candidate 105; **M3**
  live 105 and close.

### Copy-ready kickoff brief (for the Native to issue only after deciding D1–D7; no authority is implied by its presence here)

> You are the sole integrator for Pūrṇa Anveṣaṇa completion. Read
> `00_ARCHITECTURE/briefs/nirmana/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md` and the approved
> plan it revises. Start from freshly verified protected main in a new isolated worktree;
> preserve `codex/purna-wealth-near-miss` and its two uncommitted tests. Execute P0 and P1–P2
> first; request D6 on day one and verify the `ga_strength` receipt read-only when it lands.
> Do not treat the near-miss band, the evidence store, or #2704 as campaign-wide blockers; the
> queue in §8 defines blocked. Do not regenerate goldens to make tests pass; do not disable the
> pinning guard; do not edit applied migrations; do not widen grants. Report at M1 with the
> first supported-complete wealth reading and the register from each door. Retire the
> heartbeat monitor and use event watchers as §8 defines.

## 10. Evidence register

### 10.1 Freshly observed — production (read-only, `amjis` as `amjis_app`, 2026-09-22 12:42–13:15Z)

| # | Query (abridged) | Result |
|---|---|---|
| E1 | `role_table_grants` for `data_plane_builder` | SELECT on `asset_registry`, `asset_freshness`, `asset_output_digest_specs`, `charts`; INSERT/SELECT/UPDATE `asset_provenance_receipts`; full DML on `asset_throughput` |
| E2 | `_migrations_applied` 1033–1070 | 1040 @ 09-19 12:00Z; 1041 @ 13:48Z; 1042 @ 23:47Z; 1070 @ 09-20 05:42Z |
| E3 | `asset_throughput` for `482012f1` | `ga_dashas`, `ga_strength`, `ga_positions`, `bo_laksana`, `bo_bimba` all `lit`; last built 09-07/09-08/09-11 |
| E4 | `ga_dashas` receipts | one proven/fresh, build `f2a62f44` (run `completed`, `skip_no_delta`), spec `573e8aa1a0` = active |
| E5 | fence rows for `ga_dashas` | 3 `failed` runs (2026-08-06) with asset `queued`; no active runs |
| E6 | orphan rows all charts | 1,477 rows, 3 charts, 83 assets, 2026-06-27 → 2026-08-21 |
| E7 | orphan rows per asset on chart | `ga_structural` 8, `ga_vichara` 7, `ga_sensitive_degree` 1, `ga_dashas` 3, `bo_*` 5–16 each |
| E8 | `ganita_dashas_get` (direct MCP, limit 1) | `ga_dashas_replacement_in_progress`, `restart_required: true`, 0 rows |
| E9 | wealth-required receipts vs active spec | `ga_strength`: no receipt under active spec `3743484c…`; others fresh/proven |
| E10 | `build_runs` since 2026-09-18 | one row: `ga_positions` 09-19 22:48Z `failed` ("orphan-watchdog: run never dispatched") |
| E11 | latest completed run for chart | `a1a5f7d6` `bo_grounding` 2026-09-12T01:47Z |
| E12 | facts under E11 | 0 of 143,299; 10 distinct build ids; receipts under E11: 1; dashas: 0 |
| E13 | receipt build vs rows build | `chart_dashas` all under `1f89fd4c` (`build`), receipt `f2a62f44` (`skip_no_delta`); `ga_positions` facts `1c092ffb` vs receipt `0ac321ee` |
| E14 | generation tables | 7 tables from 1035/1036 exist, all 0 rows |
| E15 | `ga_yoga_firings` on chart | 53 rows, all `fired=true`, 13 yogas; catalogue 233 |
| E16 | `chart_grants` on chart | 3 rows, 1 `probe`, permission `view`; 4 charts with grants |
| E17 | lifecycle tables | `planner_inquiry_lifecycles`, `…_evidence_receipts`, `…_action_reservations`, `planner_managed_prashna_jobs` owned by `purna_inquiry_owner`; app cannot SELECT |

### 10.2 Freshly observed — source at `34991645b` (citations as used in §2)

Confirmed by direct read: `overlay_loader.ts:87-112, 703-760`; `register_d9_judgment.ts:338-350,
628-672, 1684-1686`; `source_query_availability.ts:4001-4030`; `reading_checklist.ts:114-120,
177-252`; `get_dashas.ts:640-760`; `query_mechanisms.ts:395-415`; `get_dashas.pagination.db.test.ts:80-160`;
`registry.ts:1263-1290`; `git log -S replacement_fence` → `079e77ef9` (#2626).

### 10.3 Freshly observed — services, PRs, task log

Web `c58e8666` (100% traffic, 12:24Z); MCP/sidecar `09d99894` (100%, 2026-09-20 manual
dispatch); worktree `34991645b` not an ancestor of web's SHA. `gh` authenticated; core rate
limit 5000/5000 at review time. Task log: 425 completions; blocked verdict 2026-09-20T14:25:05Z;
239 heartbeat-only completions after it. Monitor: `FREQ=MINUTELY;INTERVAL=10`, ACTIVE.

### 10.4 PR/CI classification (freshly observed via `gh` and local scanner reproduction)

| Item | Observation |
|---|---|
| #2705 | OPEN, `34991645b`, base `main`, MERGEABLE/BLOCKED; 43 checks: 30 pass, 11 skipped, 2 fail (Unit Tests 106091234309; Fact-Category Pinning Gate 106091234247); merge-base with main `94f75602f` (#2702); 41 commits ahead; 15 files |
| #2704 | OPEN, `889ceaf9b`, base `codex/madhav-l3-claude-code`, CLEAN, 0 checks; 4 files (acceptance v5 JSON, acceptance test, two route-port baselines); goldens bound to L3 snapshot `7e3a67a5…` |
| #2695 | OPEN, `5d8252dbe` (= L3 tip), base `main`, BLOCKED; Unit Tests failing |
| #2709 | MERGED 2026-09-21T22:19Z (`d7ce3b223`) |
| #2700 | MERGED 2026-09-20T05:17Z (`d9070900d`) |
| main | `c58e86662` (#2712) at review start; `50d49e19d` (#2713) by review end |
| Unit failures | `route_golden_stream.test.ts:562` (`branch-deep-dive`, `branch-completeness-receipt`: receipt sha diverges at `$.events[14].detail`); `beyond_acarya_acceptance.test.ts:66` (`report_hash` `5ccb2a7a…` ≠ `22b4f8d5…`), `:246` (artifact pins `01:38:00Z`/`ae3b0f74…`, snapshot is `13:42:00Z`/`6dcac829…`) |
| Pinning findings | 62 total; 53 allowlisted (reported); 9 new, all `source_query_availability.ts` lines 1522, 1545, 1570, 1599, 1625, 1705, 2004, 2083, 2136 — every one a `LIMIT 0` probe (class i), authored by #2681, shifted +4 by #2705's insertion at 1431–1434; allowlist entries pinned by exact `line` (N−4) |
| Allowlisted 53 | 13 zero-row probes in the same file (class i); 14 L1 handler page SELECTs (class ii); 18 sidecar set reads by category (class ii); 4 `COUNT/GROUP BY` (class iv); 2 docstring false positives (class iv); 1 subject-pinned `.find()` in `get_yoga_dosha.ts:227` (class iii-shaped, allowlisted with justification); 1 dead scaffold read (`l2_embeddings.py`) |
| Scanner | `check_fact_category_pinning.py` + `fact_category_pin_allowlist.json` (71 entries; `line` or `pattern`) byte-identical on main and HEAD; no inline pragma mechanism; main archive → 0 new |
| Local dirty state | `register_d9_judgment.integration.test.ts` (+4/−1: expects array + `served` + `count`); untracked `register_d9_judgment.near_miss_contract.test.ts` (asserts source lacks the `not_computed` hardcode); both fail against HEAD; neither in #2705 |

### 10.5 Recorded (not re-earned)

34/34 source-local route obligations; disposable-DB migration replays; live wrap-up
three-door dark-state agreement; 12,441/4 unit result at `371ead2aa`.

### 10.6 Not verified

Bucket ACLs at the named prefix; full application suite on any head; the collector on any
environment; live rendering of the evidence UI; whether `gemini-2.5-flash` on the deep slot is
cheaper per inquiry than the recommendation in D4.

## 11. Audit of the handoff's own claims

| Handoff claim | Disposition | Basis |
|---|---|---|
| Execution task idle; monitor active every 10 min; heartbeats dominate | **Confirmed** | §10.3 |
| #2705 open/blocked at `34991645b`; two failing check categories | **Confirmed** (classification in §10.4) | `gh` |
| 182 SCUs / 186 bindings / 167 contracts / 19 dark / 0 uncovered | **Confirmed** | jq on snapshot |
| 259 concepts / 53 edges / 156 isolated dispositioned | **Confirmed**; rationale is one boilerplate string for all 156 | jq |
| 96 / 5 / 91 pagination | **Confirmed at descriptor level**; binding level is 95 reviewed + 1 unreviewed `mcp_native` binding | jq |
| Web `5ff0030f` | **Superseded**: web now `c58e8666` | gcloud |
| MCP/sidecar `09d99894` | **Confirmed** | gcloud |
| #2700 merged; application/rebuild/consumption not verified | **Corrected**: grants applied (E1, E2); no rebuild attempted (E10); dasha consumption blocked by RC-2, not by the grant | §2 |
| "Guarded replacement/build/receipt/freshness state not proven recovered" (R-D) | **Refuted as stated**: receipt is fresh/proven; the guard fires on orphan rows | E4, E5, E8 |
| `notably_absent_yogas` permanently `not_computed`; L2 near-miss missing | **Confirmed**, layer **corrected** to L1 | E15, §RC-4 |
| "L1 firing storage contains fired rows rather than a classified non-firing universe" | **Confirmed**; schema already supports the universe | E15 |
| Evidence store designation + chart-grant proof both open | **Half-corrected**: grant verifiable and present (E16); store still open | E16 |
| `channel_chat_dispatch` refers to Portal dispatch | **Corrected**: the real Portal door is `/api/pariprashna`; consult is legacy | RC-6 |
| Reasoning policy present in source | **Confirmed present, refuted as effective**: flag unmapped; deep slot weaker | RC-5 |
| Response accountability "in progress" | **Corrected**: present and wired on two doors, mis-bound and unenforced | RC-6 |
| Uniform gate may misclassify unlike capability kinds (hypothesis) | **Confirmed** | RC-7 |
| Product proof arrived too late (§12.1) | **Confirmed** (first receipted collector run 09-19 after 83 merged PRs, 44 release-fix, 28 catalogue, 6 collector) | records audit |
| Accounting concealed unresolved product work (§12.2) | **Confirmed and sharpened**: it also concealed RC-1, which no amount of accounting could reveal | §2 |
| Four unit failures are "the narrow #2704 golden/provenance dependency" (§9.3) | **Refuted**: #2705 did not regenerate its own artifact/goldens; #2704's hashes never match #2705's | RC-9, §10.4 |
| Scanner findings "inherited, zero-row probes" (§9.3) | **Confirmed as zero-row probes; cause corrected**: allowlist exact-`line` drift, fixable in the allowlist without touching the scanner | RC-9 |
| Ownership protection became a deadlock (§12.5) | **Refuted**: no cross-campaign dependency existed; the deadlock was a self-diagnosis recorded without hash evidence | RC-9 |
| "L2 near-miss band missing; needs L2 owner" | **Confirmed layer, corrected blocker**: producible with zero schema change in `bo_laksana`; the missing item is a ratified candidate/eligibility packet (D2) | RC-4 |
| Percentages rejected | **Agreed**; none offered here | — |

## 12. The strategic coordination's contribution

- **Consumer completeness specified before producer feasibility.** The wealth checklist's
  five-asset same-build fence and the near-miss unit were both written against a build model
  that production does not implement and a producer that does not emit the rows. A one-hour
  read-only production query in Task 0 would have exposed both.
- **Source accounting was allowed to read as progress.** "167/186, 0 uncovered" was reported
  daily; "0 facts under the active build" was never asked. The plan's own §4.4 warned against
  this and was not enforced by the strategic layer.
- **Ownership language was over-conservative.** "Never edit another campaign's branch" was
  correct; "wait for its merge order for your own tests" was an inference nobody challenged.
- **Blockers were recorded, not converted.** "Needs the L2 owner", "needs an evidence store" never
  became a packet with fields, an addressee, and an acknowledgement.
- **The monitor's instructions were right and unenforced.** The prompt forbade exactly the
  behaviour that followed; no mechanism checked the queue was empty before "blocked" stood.
- **Two diagnoses were accepted from adjacent campaigns without a falsifying check** (grant gap
  as the dasha-guard cause; "needs the L2 owner" as the near-miss blocker), and **one
  self-diagnosis was recorded without hash evidence** (the #2704 dependency), then repeated in
  195 heartbeats as an unchanged external boundary.

None of this diminishes the substrate the campaign built. It explains why a good substrate
produced no reading.

---

*End of PURNA_ANVESANA_INDEPENDENT_REVIEW v1.0 (2026-09-22). All six delegated audits are
integrated; §10.4 carries the PR/CI classification. No addendum pending.*
