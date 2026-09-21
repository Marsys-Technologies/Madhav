---
artifact: KALA_BRIEF_CONFORMANCE
version: "1.0"
status: DRAFT — cycle 3 of the KĀLA READINESS AUDIT
produced_by: L3 Kāla readiness audit (autonomous, Claude Code)
produced_on: 2026-09-22
scope: T4 — structural/shape conformance of the L3 execution brief and native-authored asset
  briefs against their governing contracts. Content/substance is not second-guessed; every gap is
  reported as a question for the native, never as an edit suggestion — the briefs are the
  native's own writing and not this audit's to edit.
method: >
  Produced by one read-only subagent, 13 tool calls, all document reads/greps. Gochara review
  verdict independently spot-verified by the conductor via direct grep before integration — see
  AUDIT_STATE.md cycle 3.
---

# KĀLA BRIEF CONFORMANCE — T4

Documents read:
- Layer-brief contract: `MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT_v1_0.md`
- Asset/interface-brief contract: `MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT_v1_0.md`
- L3 execution brief: `MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md`
- VA §13.3: `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md` lines 447-458
- Native asset briefs dir: `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/`
- Gochara plan: `.../briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`
- Review: `.../briefs/ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md`

## L3 execution brief vs layer-brief-contract (10 sections, section-by-section)

| # | Contract requirement | Classification | Citation / basis |
|---|---|---|---|
| §1 | Admission rule (strategic-parent approval, F/DP inheritance) | PRESENT-CONFORMANT | Frontmatter `approval_record`, `strategy_decision: DP-SD-017`; body §1 "The native has now requested implementation and kickoff. DP-SD-017 approves..." |
| §2 | Required brief header (exact YAML key set) | PRESENT-CONFORMANT | All named keys present verbatim: `artifact, version, status, strategic_parent_task, execution_task, approval_record, product_authority, strategy_version, layer, goal_objective, source_revision, accepted_upstream_contracts, owners, may_touch, must_not_touch, activation_prohibitions`. `status: APPROVED_FOR_EXECUTION` matches contract's example exactly. |
| §3 | Consumer contribution and non-goals | PRESENT-BUT-THIN | §1 states the "distinctive result" and "competent simpler baseline," inherits F01-28/DP01-18, but non-goals are scattered across the §3 authority-matrix table rows rather than collected as the contract's dedicated non-goals statement. No single passage enumerates "specific earned distinctions, prevented errors, uncertainty reductions or exposed limitations expected." |
| §4 | Complete inventory and evidence classification | **MISSING** | §1 lists the 22 active identity names only, with no per-asset source files/tables/registry metadata/generation/dependencies/consumers table, and no evidence-classification tags anywhere. §5 item 2 delegates inventory-building to W0 — the inventory is a future execution deliverable, not something the brief itself supplies. |
| §5 | Demand/offer/internal-interplay contracts (per-field table) | **MISSING** | No field-level table exists. §5 references named edges only in prose ("Preserve actual direct Yojaka→Kalasutra/Vighnakara reads...") — gestures at interplay but does not populate the required per-field fields. |
| §6 | Component dispositions and preserved kernels | **MISSING** | No disposition table. Only `ka_gochara_sweep` receives an explicit disposition-like statement ("protected retired history and never dispatchable"); the other 21 identities carry no individual disposition. |
| §7 | Layer-specific minimums for L3 Kāla | PRESENT-CONFORMANT | §6/§7 directly echo the contract's named boundary: "Calibration-only changes do not change search coverage; coverage-only changes do not create probability" and "never reuse chart-bound semantic results across subjects" track the contract's "activity/intensity ≠ event probability; shared inputs ≠ independent temporal evidence" language closely, not verbatim. |
| §8 | Compatibility, cascade, rebuild, rollback | PRESENT-BUT-THIN | §5 item 5 and §8 "Completion, blockers and handback" address this substantively as narrative obligations, not as the contract's named matrix artifacts (no compatible-generation matrix or correction matrix table appears). |
| §9 | Mandatory tests and proof tiers (13 classes; 3 named verdict categories) | PRESENT-BUT-THIN | §7 "Validation" lists a comparable bulleted set covering most of the contract's 13 items in substance, but never uses or maps to the contract's three named verdict categories (`COMPUTATIONAL_CORRECTNESS`/`EXPLANATORY_DISCRIMINATIVE_VALUE`/`EMPIRICAL_OUTCOME_PERFORMANCE`) anywhere. |
| §10 | Exit gates and evidence packet | PRESENT-BUT-THIN | Frontmatter `delivery_target` uses a **different state vocabulary** than the contract's five canonical states (e.g. `LAYER_DATA_ACCEPTED` vs `PRODUCER_READY`, `DEPLOYED_ACCEPTED` vs `DEPLOYED_OPERATIONALLY_ACCEPTED`). §8 lists terminal-packet content that substantively covers the contract's requirements — content is present, naming is not aligned to the contract's own vocabulary. |

## L3 execution brief vs VA §13.3 (8 required contents)

| # | VA §13.3 requirement | Classification | Citation / basis |
|---|---|---|---|
| 1 | Consumer value, inherited obligations/exclusions | PRESENT-CONFORMANT | §1 "distinctive result" + explicit F01-28/DP01-18 inheritance with DP07/08 as "core production responsibilities" and DP09/13-15/18 as "interface/preservation/firewall obligations, not authority to..." — itself an exclusions statement. |
| 2 | Complete owned inventory, evidence levels separated | **MISSING** | Only the 22-identity name list is given; no capital classification, no evidence-level tagging. Same gap as layer-contract §4. |
| 3 | Internal asset interplay, input/output/use matrix | PRESENT-BUT-THIN | §5 names specific edges in prose and §3's authority matrix draws the L4/L5 boundary, but no matrix artifact exists. |
| 4 | Qualified Jyotish coverage (prerequisites, variants, exceptions, uncertainty, source rights) | PRESENT-BUT-THIN | §7 requires "missing, failed, zero, inapplicable, unqualified, unsearched and bounded negative distinctions" and names Bhavat as an explicit non-promotable exception, but this is test-discipline language, not a doctrine-level coverage inventory per identity. |
| 5 | Component-level preserve/integrate/enrich/qualify/consolidate/restrict/retire decisions | **MISSING** | Only `ka_gochara_sweep` gets an explicit disposition; no per-identity table. Same gap as layer-contract §6. |
| 6 | Upstream demand/downstream offers with field/grain/context/lineage contracts | **MISSING** | Not populated at field level anywhere; §1 defers this detail to the (separately reviewed) strategy's own L3-Q01–Q13/A01–A22/H01/P0–P6/L3-U01–U11 references. |
| 7 | Generation/invalidation, compatibility, retained history, cost, rollback | PRESENT-CONFORMANT | §5 item 5 and §8 cover this substantively, matching the layer-contract §8 finding. |
| 8 | Bounded work packets, dependencies, focused proof, consumer cutover | PRESENT-CONFORMANT | §5 W0–W8 wave table + §7 validation/proof requirements + §3 authority matrix's activation gating together satisfy this. |

**Note:** VA §13.3's final sentence explicitly assigns items 2, 5 and 6 above (inventory,
dispositions, field contracts) to the **asset brief**, not the layer brief. That reallocation is
consistent with what was found: the L3 execution brief is thin exactly where VA's own text says
the asset brief, not the layer brief, should carry the weight. The existing asset brief's own
discharge of that reallocated burden is assessed next.

## Native asset briefs found (list) vs asset/interface-brief-contract (8 sections each)

Directory listing of `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/`:
- `GOCHARA_FAMILY_ELEVATION_PROPOSAL_v0_1.md` (superseded lineage)
- `GOCHARA_FAMILY_ELEVATION_PLAN_v0_2.md` (superseded, sent for review)
- `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md` (current — supersedes v0_2, retained SUPERSEDED)
- `ASTRA_REVIEW_REQUEST_GOCHARA_v0_2.md`
- `ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md`
- `evidence_gochara/` (E1–E8 supporting evidence)

**Kshetra and Sangam asset briefs: CONFIRMED ABSENT.** No file matching `*KSHETRA*` or `*SANGAM*`
exists (only 8 entries total, all listed above, all Gochara-scoped). Per the charter's own
instruction this is recorded plainly and is **not treated as a blocker** — an expected, valid
finding for a campaign still in its Gochara-first wave.

Only one native asset brief exists to check: `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`. Its
frontmatter self-declares `status: PROPOSAL_FOR_NATIVE_RULING` and `does_not_authorize: Any
production code change, build, migration, registry edit, lifecycle change or hold release` — it
explicitly presents itself as a pre-execution proposal awaiting a ruling, not as an already-
`APPROVED_FOR_EXECUTION` asset/interface brief. This self-declared status is material context for
every row below: several contract sections describe what a completed execution packet contains,
and this document is, by its own header, upstream of that state.

| # | Contract requirement | Classification | Citation / basis |
|---|---|---|---|
| §1 | Admission and exact authority (required header keys incl. `approval_record, parent_layer_contract, foundation_contract, asset_or_interface_ids, implementation_owner, independent_review_owner, release_authority, may_touch, must_not_touch`; `status: APPROVED_FOR_EXECUTION`) | **MISSING** | Gochara plan frontmatter uses a different, non-overlapping key set (`artifact, version, status, supersedes, incorporates_review, produced_on, produced_by, native_priorities, governing_strategy, governing_execution_brief, evidence, source_revision, does_not_authorize, changelog`). None of the required keys appear. `status` reads `PROPOSAL_FOR_NATIVE_RULING`. Consistent with the document's self-declared pre-execution status, not an omission in a document claiming to be executable. |
| §2 | Current-state evidence (identity/layer/owner, files/tables/services, algorithm/inputs/outputs/grain/failure/idempotency, consumers, generations, epistemic class, source revision) | PRESENT-CONFORMANT | Extremely detailed: §2 decision-delta table cites exact file:line evidence, evidence tags `[X]/[A]/[S]/[R]/[I]/[U]` defined and used throughout, §5's ecosystem table cites file:line per surface, `source_revision`/worktree/branch pinned in frontmatter. |
| §3 | Failure or missing capability | PRESENT-CONFORMANT | §2's D1–D12 table and §5's surface table each give observed defect + evidence + consequence. Non-claims explicit in places (e.g. WP0 exit gate, §9 "Still unknown"). |
| §4 | Semantic change and expected distinction, incl. simpler-baseline value metric | PRESENT-BUT-THIN | §3 "Amended design" and §4 "Rulings" describe new behavior/reasoning at length; §3.7 gives an explicit baseline comparison. However this is comparison-to-legacy-algorithm framing, not the contract's "competent simpler baseline and value metric" applied to consumer-facing value — the value/cost side is not quantified (partly because, per §9, the cold-build number is itself still unknown). |
| §5 | Preservation, migration, history, rollback | PRESENT-CONFORMANT | §3.6 and R1/R6/R9 directly address immutable publication identity, versioned corrections without rewriting issued evidence, a real restore drill covering all 38,287 current v1 rows, and a governed stop-dispatch control. |
| §6 | Focused proof matrix (per-row fixture/command/expected/invariant/detector/evidence) | PRESENT-BUT-THIN | §7 "Work packets" gives exit gates per packet that parallel most of the contract's proof rows plus explicit stop conditions, but this is packet-level, not a literal per-row table — no single test is yet pre-registered with a runnable command, consistent with a pre-execution plan. |
| §7 | Implementation and review discipline | PRESENT-BUT-THIN | §5 "Ownership" names "one integration owner plus non-overlapping A/B/C" streams and "one build lane, one integrator, hub-freeze and transitive-digest rules all still bind" — but does not name the specific isolated worktree/branch for *this* work (only cites the read-analysis worktree, explicitly not an authorization to build). Independent review is present as an already-folded-in input (`incorporates_review`) rather than a forward discipline statement for the proposed work. |
| §8 | Terminal evidence packet | **MISSING, by design** | This document is upstream of execution (`does_not_authorize`; `status: PROPOSAL_FOR_NATIVE_RULING`). No commits/changed files to report because none have been authorized. §9 "Still unknown" and §4's "rulings are the native's to rule" do return unresolved decisions to the strategic parent — the one terminal-packet element a pre-execution document can and does supply. |

## Independent review record status

Two distinct "ASTRA_REVIEW"-named artifacts exist:
1. `MADHAV_DATA_PLANE_L3_ASTRA_REVIEW_RECORD_v1_0.md` — a **strategy-level** review record
   (`status: REVIEWED_PROPOSAL`), not the Gochara-plan-specific review; not the subject of this
   verdict question.
2. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md` — the
   Gochara-plan-specific independent adversarial review.

For file 2, frontmatter reads:

```
artifact: ASTRA_REVIEW_GOCHARA_PLAN
version: "0.2"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewed_revision: "5d8252dbefc053f9faa92aab693ad46310e0c5c5"
reviewer: "Codex — independent adversarial review"
date: "2026-09-20"
verdict: PROCEED_WITH_AMENDMENTS
reviewed_plan_sha256: "964b7f9ec13ea5678f8948262cd74fec9b84d69bf74da1f58711ce4c6b581921"
review_request_sha256: "acc4cb1b98a9716225a2d53aa460b14277ead52a094f4e370871b14b2802945e"
authority: "Review only; this artifact authorizes no implementation, build, migration, database write, publication or hold release."
```

**Confirmed by both the subagent and independently re-confirmed by the conductor:** the file's own
`verdict` field reads exactly `PROCEED_WITH_AMENDMENTS`. The review is present, reaches this clear
machine-readable verdict, and is pinned to a specific reviewed-plan SHA256 and reviewed revision.
`GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`'s own frontmatter restates the same verdict and same
SHA256 prefix consistently.

## Questions for the native

1. §3 of the layer-brief-contract asks for a dedicated non-goals/earned-distinctions statement;
   the L3 execution brief's non-goal content is present but distributed across the §3
   authority-matrix table rather than collected in one place. Is that distribution intentional, or
   would a consolidated non-goals passage be expected before this brief is treated as fully
   conformant?
2. The layer-brief-contract's §4 inventory and §5 field-contract table are not populated inside
   the L3 execution brief itself — they are deferred to W0. Is it intended that the layer-execution
   brief carry this inventory directly, or is deferring it to the first execution packet (W0) the
   accepted pattern for this campaign?
3. §6's per-component disposition table is populated for `ka_gochara_sweep` only, not the other 21
   active identities. Should each of the 22 identities carry an explicit disposition in the layer
   brief, or is that intentionally left to each identity's own asset brief?
4. The L3 execution brief's `delivery_target` field uses a different state vocabulary
   (`LAYER_DATA_ACCEPTED`, `CONSUMER_INTEGRATED`, `DEPLOYED_ACCEPTED`, `VALUE_EVALUATED`) than the
   layer-brief-contract's own named exit-gate states (`PRODUCER_READY`, `INTEGRATED`,
   `DEPLOYED_OPERATIONALLY_ACCEPTED`, `CONSUMER_VALUE_DEMONSTRATED`, `EMPIRICALLY_EVALUATED`). Is
   this an intentional campaign-specific relabeling, or should the two vocabularies be reconciled?
5. VA §13.3's closing line assigns per-asset inventory, dispositions and field contracts to the
   asset brief, not the layer brief. Given that, is `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`
   intended to itself become the formal `ASSET_INTERFACE_EXECUTION_BRIEF` for the Gochara family
   once ruled on and approved — or is a separately headed document (using the contract's own
   required header keys) expected before execution begins?
6. The Gochara plan's frontmatter key set does not overlap the asset/interface-brief-contract's
   required header keys at all. Is this because the plan is deliberately a different document type
   (a pre-ruling proposal) that will be superseded by a contract-conformant brief once the native
   rules on it, or is the intent for this same document to be amended in place once approved?
7. Kshetra and Sangam asset briefs are confirmed absent — no file, no draft, no placeholder. Given
   the strategy names Kshetra work starting as early as W2 and Sangam at W3, is an asset brief for
   either expected to exist before their respective wave begins, or is brief production
   intentionally sequenced to trail wave readiness?
