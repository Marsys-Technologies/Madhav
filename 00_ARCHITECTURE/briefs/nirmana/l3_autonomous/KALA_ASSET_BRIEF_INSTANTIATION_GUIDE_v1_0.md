---
artifact: KALA_ASSET_BRIEF_INSTANTIATION_GUIDE
canonical_id: KALA_ASSET_BRIEF_INSTANTIATION_GUIDE
version: "1.0"
status: CURRENT
date: 2026-09-22
role: >
  How to instantiate ONE Kāla asset elevation brief so that it binds, top to bottom, to the
  Product Definition, the Data-Plane Value Architecture, the Foundation Contract, the L3 Strategy
  and the reusable asset/interface brief contract — and starts from the per-asset evidence the
  campaign already holds. This is a BINDING GUIDE, not a fifth authority: every requirement below
  names the document that imposes it. DP-SD-019 §6 is obeyed — "extend existing records concisely;
  do not build another tracker, scheduler or blanket per-field paperwork system."
governing_shape: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT_v1_0.md (bound by DP-SD-017)
analysis_lenses: .claude/skills/autonomous-asset-elevation/references/asset-elevation-contract.md (A–J)
does_not_authorize: any change. A populated brief is a proposal until the native rules on it.
---

# Kāla asset elevation brief — instantiation guide

Replace `<ASSET_ID>` throughout. Where a section says *cite*, cite the row/line, do not restate.
The brief you produce must be short enough to review and complete enough to execute. Length is
not a virtue; a claim without its source is a defect.

---

## §0 — The hierarchy your brief binds to (read the named sections, nothing else first)

| Level | Authority | The sections that bind an asset brief |
|---|---|---|
| Product | `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` | §1.3 (the unit of value is an *earned distinction*), §3.10 (Kāla), §5.2 (typed confidence — no scalar substitutes), §5.3 (findings survive delivery), §7.1 (nearest vs stronger under a *named* criterion; "none found" carries horizon/resolution/coverage), §9 experience 4 (chapter → interval without changing evidential identity), §10.2 (detectors behind availability claims), §13 (boundaries), §14 (proof obligations) |
| Data plane | `briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md` | §6.4 (the Kāla story), §7.1 (contract envelope), §7.2 (worked structure→time contract and its tests), §10.2 (what to cast away), §10.3 (what to bring in), §11 (compatible dependency sets), §12.2 (tests that distinguish use from value), §13.3 (what an asset brief supplies) |
| Foundation | `briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md` | F01–F28 (F03, F04, F06, F08, F09, F10, F12, F13, F14, F22, F23, F24, F27, F28 are the ones an asset brief most often violates); §3 vocabularies; §4 DP07/DP08 (core for L3); §8 gate matrix ("may not be claimed from") |
| Layer | `briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` + `..._EXECUTION_BRIEF_v1_0.md` | Strategy §2 (L3-Q01–Q13), §3 (the data contract — *Temporal testimony* et al.), §4 (lifecycle steps 1–7), §5 (P0–P6 + benchmark contract), §6.1 (your row L3-Axx), §6.4 (packet contents + wave), §7 (acceptance states), cross-layer U01–U11; Brief §1 (baseline definition), §5 (W0–W8), §6 (proof contract), §7 (minimum proof) |
| Shape | `briefs/nirmana/MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT_v1_0.md` | §1–§8, **verbatim structure**. This is the document your brief must *be*. |
| Lenses | `.claude/skills/autonomous-asset-elevation/references/asset-elevation-contract.md` | A–J as the analysis checklist; disposition-specific terminal rules |
| What changed | `l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md` | Read in full; it supersedes anything older that conflicts |

Two lifecycle ladders exist and your brief declares its target on **both**:
- **Data-plane (Strategy §7):** `PLAN_REVIEWED → PRODUCER_READY → DATA_ACCEPTED → LAYER_DATA_ACCEPTED → CONSUMER_INTEGRATED → DEPLOYED_ACCEPTED → VALUE_EVALUATED → EMPIRICALLY_EVALUATED`.
- **Campaign evidence (t3 / skill):** `RECONCILED → ELIGIBLE → ANALYZED → OPTIMIZED | JUSTIFIED_NO_CHANGE → INTEGRATED → DEPLOYED → REBUILT_ONCE → INDEPENDENTLY_VERIFIED → FROZEN`, evidenced by ledger events under the frozen definition `t3-2026-09-11-8b884eac`.
They are not the same claim. A t3 `asset_frozen` event moves the `Accepted N/22` headline; a Strategy §7 state is what the data-plane gate binds. Name both, honestly.

## §1 — Start from what already exists for `<ASSET_ID>` (cite, do not redo)

The campaign already holds five per-asset records. Your brief opens by citing them by row and stating what, if anything, has changed since:

1. **Contribution register row** — `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md` §5 (line ~137–159): preserved kernel, provisional delta (P/E/I/Q/C/H codes), DP references, source anchor.
2. **Current-state producer/use row** — `MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` §4.1: physical output owner, actual material L3 input, **W0 disposition**. Also §3 (live truth table) and §4.2 (replacement blast radius).
3. **Field register partitions** — `MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md`: every persisted column / typed service member with producer path, type, unit, grain, key role, null/empty/failure semantics, qualification code (Q1/Q2/Q4/QX/S1), receiver, falsifying test. **22 identities / 39 partitions / 699 fields already exist. Do not re-inventory; cite rows and mark deltas.**
4. **Strategy row L3-Axx** (§6.1) and, if named, its **P-candidate** (§5) with the exact equivalence contract.
5. **Foundation-safety fences** — `MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md` §3 (shared-owner table fences), §6 (the **frozen** generation/publication/recovery design — reviewed design, not yet physical), §8 (exact next packets and holds).

Then the readiness evidence from this arc: `KALA_ELEVATION_READINESS_PACKAGE_v1_0.md`, its `readiness/_work/LANE_C_HARD_ASSETS.md` / `LANE_D_ASSET_REGISTER.md` rows, and `KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md`. Where a readiness finding and a W0 record disagree, **re-measure at the authority** and record which was stale.

## §2 — Header (contract §1, verbatim fields)

```yaml
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
version: "1.0"
status: PROPOSED_FOR_NATIVE_RULING          # becomes APPROVED_FOR_EXECUTION only by native record
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / <blob>"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
asset_or_interface_ids: ["<ASSET_ID>"]      # plus any U-packet IDs this brief carries
goal_objective: "<one bounded sentence>"
source_revision: "<full commit>"
accepted_upstream_contract: "<the exact blobs from CURRENT_STATE §1 table that this asset consumes>"
implementation_owner: "<one writer>"
independent_review_owner: "<not the author>"
release_authority: "NONE"                    # unless separately granted
may_touch: ["<exact files/tables/services>"]
must_not_touch: ["platform-mcp/src/tools/kala_views/**", "applied migrations 1033–1070",
                 ".github/workflows/deploy.yml", "kala_gochara_windows WHERE generation='v1'",
                 "<every shared-owner table not fenced to you — cite FOUNDATION_SAFETY §3>"]
target_state_data_plane: "<Strategy §7 state this brief can honestly reach>"
target_state_campaign:   "<t3 lifecycle state / event type this brief can honestly earn>"
wave: "<W2–W7 per EXECUTION_BRIEF §5>"
```

Contract §1: *"If implementation owner, exact files/tables/services, accepted upstream contract/version, observed failure, expected consumer distinction or protected scope is missing, do not start."*

## §3 — Current-state evidence (contract §2)

Populate contract §2's seven bullets. L3-specific rules:
- Label every observation `direct_source_read | generated_measurement | runtime_observation | historical_receipt | inference` with revision/time (Layer contract §4).
- **The live-path rule:** for every hazard, state whether a live caller reaches it *today*. "No live caller found within scope: `<scope>`" — never "unused". Unknown use is `UNRESOLVED_USE` (VA §10.2, contract §2).
- Consumers: direct, transitive, dynamic, audit, historical — with the search boundary stated. Served surfaces are Pūrṇa-owned; you *trace* them, you do not edit them.
- State the asset's position on both ladders (§0). Under `t3` the true current state for every Kāla asset is **no event** — say so; do not borrow a superseded-definition freeze.
- Cost: cite `KALA_COST_PROFILE_v1_0.md` when it lands, or the W0 benchmark baseline with its stated boundary ("source-local, no-DB, small fixture; not full-chart"). **Never cite `asset_registry.estimated_seconds`** (F28: no detector).

## §4 — The failure (contract §3): ONE falsifiable problem

| Field | Your content |
|---|---|
| Observed behavior | exact input/context → actual output/state |
| Evidence | `file:line` / SQL / receipt, with revision and time |
| Expected contract | the F/DP/L3-Q/U ID it violates |
| Defect class | missing · flattened · unqualified · unused · wrong authority · wrong context · stale/mixed generation · unserved · duplicate support · unsafe flow · detector mismatch |
| Impact | the specific wrong or missing **consumer distinction** (name the L3-Q) |
| Non-claim | what the evidence does *not* prove (live incidence, doctrine validity, causation) |

If you have several, rank them by the skill §5 order (§9 below) and lead with one.

## §5 — The semantic delta (contract §4) — this is where value is earned or faked

State the **smallest sufficient** change. Then bind it:

1. **Which L3-Q it serves** (Strategy §2), the *required added distinction* verbatim, and the *primary proof* named there. If your asset serves a real need no L3-Q covers, raise a strategy amendment; do not adopt a local question.
2. **Typed qualification, not a scalar** (Product §5.2, Foundation F04/F06/F12, Strategy §3 *Temporal testimony*): every emitted claim carries epistemic class, per-method F06 completeness state, F12 operator role, **independence group**, support/opposition/**silence**, material uncertainty, and a **comparability flag** (L3-Q05 "non-comparable scales"; F08). No `confidence` / `salience` field is invented. If the asset already stamps `tier_basis='relative_uncalibrated'` or equivalent, extend that.
3. **DP07/DP08 fields** actually present (Foundation §4): parent/child clock, start/end/instant precision, timezone, hierarchy, geometry, tolerance, recurrence, horizon; structural identity, applicable clocks, enabling/inhibiting conditions, interval intersection, route, alternatives, coverage, gap.
4. **Time discipline** (Product §3.10; VA §5; the measured 5.5-hour defect): timezone-explicit instants, explicit boundary convention, no `date.today()`, no naive datetime into `timestamptz`, hour grain and sandhi preserved from L1 (`start_iso/end_iso`, `sandhi_flag`).
5. **Old vs new** for positive, negative, boundary, missing and duplicated inputs (contract §4).
6. **Competent simpler baseline** = "the current scalar/truncated projection under the same subject, question, method, horizon and evidence budget" (Execution Brief §1). Name it concretely for this asset.
7. **Ablation:** what you would remove to test that the elevation adds a distinction rather than rows (Product §14; F03).

Contract §4: *"No new field is 'used' until the receiving transformation and served finding are proven."*

## §6 — Preservation, migration, history, rollback (contract §5) + the L3 fences

- Preserved kernels: algorithm, sources, stable IDs/natural keys, relationships, interfaces, tests, receipts, historical readings/claims. One foundation disposition per altered component (Layer contract §6 vocabulary: `PRESERVE / INTEGRATE / ENRICH_CORRECT / QUALIFY_LIMIT / INVESTIGATE_CONSOLIDATION / HISTORICAL_RESTRICTED / RETIRE_AFTER_MIGRATION / UNRESOLVED_USE`).
- **Protected classes** (never disposable): the retired sweep snapshot (`kala_gochara_windows WHERE generation='v1'`, Strategy §4), issued claims/observations (F17, U10), `kala_bhavishya` retained outcomes (L3-A21).
- **Shared-owner fences** (FOUNDATION_SAFETY §3): gen2/century share `kala_gochara_windows_v2`; sweep/century share `kala_gochara_windows`; Kshetra owns only `kala_insights.lel_derived=false`; Taranga service/writer share natural keys. One writer, one publication owner per packet.
- **CASCADE inventory** (Strategy §4; CURRENT_STATE §4.2): L2 MSR deletion reaches five core L3 tables. State which of yours, and how the brief binds to an **L2 generation** under the frozen W0 design (FOUNDATION_SAFETY §6) rather than a live surrogate id. State what changes if physical generations are not yet available when you execute.
- Generation binding: input generations, partition plan, empty-partition-as-explicit-result, candidate vs selected head, rollback by head re-pointing (FOUNDATION_SAFETY §6 items 1–4). Reuse the accepted 1035/1036 machinery; no orchestrator change (F26, §N.2 — STOP and raise if it seems needed).

## §7 — Proof matrix (contract §6) — executable, with detector named

Populate all eleven contract §6 rows (Positive · Negative · Relevant influence · Irrelevant control · Duplication/correlation · Context/missingness · Boundary/precision · Delivery · Revision · Value · Evaluation-if-governed). For each: fixture/data boundary, command, expected result, invariant, **detector that can return false**, evidence path.

L3 minimums to include explicitly (Strategy §7 last paragraph; Execution Brief §7): source-qualified positive capability; failed/inapplicable/silent methods; signed cancellation; complete domains/roots; rare contacts; arbitrary input order; duplicate evidence; wrong subject/context/generation; mixed snapshots; corrupt/missing partitions; dependency change during build; stale resume; rollback; bounded search negatives; consumer sentinels; matched performance evidence.

Three verdict tiers, kept separate (F24): `COMPUTATIONAL_CORRECTNESS`, `EXPLANATORY_DISCRIMINATIVE_VALUE`, `EMPIRICAL_OUTCOME_PERFORMANCE`. A producer perturbation cannot satisfy the third. A planned test is not a pass (F23).

**The served-evidence sentinel is yours even though serving is not:** "a sentinel only in a low-ranked, non-default field reaches the allowed consumer and saved result" (Brief §7). Express the serving change as an L3-U04/U11 interface packet for Pūrṇa; own the test.

## §8 — Analysis lenses A–J (skill contract) — each answered, or `not_applicable` with reason

A Identity/intent · B Inputs/DAG/lineage · C Correctness/epistemic integrity · D Data sufficiency/enrichment · E Consumers/reuse/duplication · F AI/product readiness · G Implementation/build efficiency · H Reliability/operations · I Change/release packet · J Final evidence.
Do not force a service or source asset through row-build lenses. VA §10.2's eight cast-away categories are the checklist for C/E/F; the six measured Kāla instances in `KALA_ASSET_BRIEF_CONTEXT` §6 are the examples.

## §9 — Prioritization (what to do first inside this asset, and where it sits in the layer)

Order within the asset (skill master plan §5): (1) correctness/security defects that invalidate the layer → (2) blockers on the longest DAG path → (3) greatest downstream unlock/fan-out → (4) high build-time or failure-cost → (5) canonicalization/reuse → (6) short independents.
Then place the asset: its **wave** (Execution Brief §5 W2–W7), its **P-candidate** if any (Strategy §5 P0–P6, in study order), its **fan-out** (CURRENT_STATE §4.1), and its **hold** if any (century v3; populated Kshetra replacement until W7; Bhavishya until W6). DP-SD-019 §6: *"Prioritize measured hotspots P1–P6 … Record justified no-change when no material hotspot exists."*

## §10 — Disposition and target state

Declare one disposition (skill §5 list) and its **disposition-specific terminal rule** (skill contract, last section). Declare the target state on **both** ladders (§0). Then the honest non-claims: Strategy §7 — *"It cannot earn full completion solely by returning unavailable states"*; `CONSUMER_INTEGRATED` and `VALUE_EVALUATED` currently have no admissible event type (native decision 2); `VALUE-EVALUATED` is `N` for every L3-Q today.

## §11 — What the brief must not do

Invent a confidence/salience scalar (Product §5.2) · adopt a question outside L3-Q01–Q13 without a strategy amendment · edit `kala_views/` or any Pūrṇa-owned surface · weaken a guard (B1 is what an assumed guard looks like) · change `convergence_commit` or the orchestrator contract · touch the protected classes · claim a state it did not earn on either ladder · cite `estimated_seconds` · decide any of the five open native decisions (`KALA_PHASE2_DECISIONS_v1_0.md`).

## §12 — Deliverable

`<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` in contract §1–§8 order, §8 lenses as an appendix, ≤ ~400 lines, every material claim cited. Independent review by someone other than the author (contract §7) before it goes to the native. It ends in `PROPOSED_FOR_NATIVE_RULING`. The native rules.
