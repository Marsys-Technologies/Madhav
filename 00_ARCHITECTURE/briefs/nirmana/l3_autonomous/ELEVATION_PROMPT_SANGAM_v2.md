---
artifact: KALA_ELEVATION_PROMPT_SANGAM
version: "2.0"
status: READY_TO_PASTE
date: 2026-09-22
instantiates: KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md for ka_sangam (single asset, chokepoint)
scope: stages 0–2; terminal PROPOSED_FOR_NATIVE_RULING
---

You are elevating **`ka_sangam`** — the convergence engine and the layer's chokepoint: seven
downstream assets consume it, and its rebuild reaches sealed L4. Your scope is **stages 0–2** of
`KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md`. Stop at `PROPOSED_FOR_NATIVE_RULING`. Base branch is
**`main`**; W2 explicitly preserved `ka_sangam` unchanged, so `main`'s Sangam *is* the accepted
source. Read files not yet on `main` with `git show origin/l3/kala-elevation-readiness:<path>`.

## Read, in this order
1. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md` (all); `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md` §2–§12.
2. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/W0_DELTA_SANGAM.md`; `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md`.
3. **Three prior artifacts:** `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md` (June,
   `[ELEVATE]`); `00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md` — its
   **§4.5 and §4.6 carry native rulings of 2026-06-22**; and the two READY prompts beside it.
4. `briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §2 (Q02, Q04, Q05, Q07), §3
   (**Temporal testimony**, **Engagement route**, **Search coverage**), §5 row **P4**, §6.1 row A15,
   cross-layer **L3-U02** and **L3-U07**.
5. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` census #15 (`kala_convergence`, 19 fields); fence 7.
   `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_CURRENT_STATE_AND_DISPOSITION_v1_0.md` §4.1 (`ka_sangam`, `ka_vedha_gochara`), §4.2, §6.3.
6. `l3_autonomous/readiness/_work/LANE_C_HARD_ASSETS.md` F7–F11.

## The asset's value proposition (stage 1)
You own two Strategy §3 objects. **Temporal testimony**: *target structure, exact evidence roots,
method/family, units/polarity, applicability, support/opposition/**silence**, **independence
group**, material uncertainty.* **Engagement route**: *structural binding plus necessary/optional
temporal clauses, satisfying/failed evidence, enablement/inhibition, route identity and
alternatives* — *"complete route rather than a coincident participant."* The consumer questions
are Q02 (nearest vs stronger, *"preserve ties/incomparability"*), Q04 (activity coexisting with
strain), Q05 (*"why do timing methods disagree — without a forced consensus"*) and Q07. Under the
native's model — assets may disagree; the LLM reconciles in context — **you are the asset whose
output makes reconciliation possible or impossible**, because you are where independence is
computed.

## What is physically there — and what is missing (lens 2.1/2.2, measured)
`kala_convergence` has 19 fields: `mode`, `convergence_score`, `orb_strength`, `rarity_years`,
`confidence_score`, `confidence_label`, `confidence_label_relative`, **`tier_basis`** (honest —
extend it), `independent_current_count`, `is_off_dasha_discovery`, `horizon_tier`, `domain`
(**one** domain), `constituent_factors` (JSONB), `signal_id`; `window_start/end`, `peak_date` at
**DATE** grain. Against the two objects you own:
- **Independence is a count, not a group.** `independent_current_count` (SMALLINT) is computed at
  `engine.py:850-889` and read by **zero `ka_*` consumers** — only L4's `ph_nimitta`. Four downstream
  assets inherit `convergence_score` without the detector that qualifies it. L3-U02 is explicit:
  *"another representation of the same origin adds no independent support; zero supporting
  evidence cannot become one independent witness."* The elevation is an **independence group**
  (which roots, which family) as a first-class field that downstream *inherits*, not a scalar
  they ignore.
- **No route, no silence, no per-method applicability** as typed fields — roots live only inside
  `constituent_factors` JSONB. A consumer cannot tell a method that found nothing from a method
  that never ran (F06 `inapplicable` vs `unexplored` vs `applied`-and-silent).
- **The score cut is a mode filter.** Top 500 and top 750 by score are **100% Mode C**;
  `ka_vighnakara` and `ka_kala_darshana` consume exactly those cuts and never see a daśā×transit
  convergence. Mode D is 70% of the table and ~13× duplicated; its guard is vacuous on the
  lifetime path (`pred_dicts=[pred]`). The output contract must be **mode-stratified**; a rank cut
  across modes is a *"reduced cap"* the Strategy forbids as equivalent.
- **`confidence_score = ICC/13`** with a tautological transit term; `confidence_label` is
  **anti-correlated** with evidence count (ICC 2–6 rows 100% `speculative`; ICC-1 rows the only
  `high`). The one discriminating tier is stored and never served. Do not repair the scalar —
  replace it with the typed testimony (Product §5.2 forbids a substitute scalar).
- **`domain` is one column.** A15: *"one domain and missing ayanamsha identity need review";*
  U07: *"preserve zero and exact event subtype."* The signed multidomain structure L2 produces
  (DP06) dies here.

## The June rulings you inherit (native, 2026-06-22) — honor or supersede explicitly, never design past
- **No hard cap** on transit events — *"a count cap truncates to an arbitrary slice."* REJECTED.
- **Gate by high-confidence threshold applied inline during the scan**, so weak events are dropped
  as found, never accumulated; fast lords yield few events *"by merit."*
- **Slow transits only** (Saturn, Jupiter, Rahu/Ketu) via the in-memory overlap model — no
  ephemeris scan, no new persisted transit table (Q1). *"ka_sangam = scorer, not ephemeris engine."*
- **`constituent_factors['planet']` is a LIST** of the slow grahas that fired (Q2); downstream takes
  the strongest by nature weight; never a constant; absent if no rule fires.
- **Cascade scope = the DAG** (Q3); surgical version bump (Q4).
- **Per-signature transit source** (§4.6): DOSHA→Saturn; DIGNITY→the signal's own graha (a lookup,
  not a scan); DISPOSITOR_RELATIONAL→the relevant lord gated by confidence; YOGA→Jupiter;
  SUBSYSTEM→no transit search.
Markers of this redesign exist on `main` (`engine.py`: 7, `writers/ka_sangam.py`: 5). Establish at
the code which rulings are implemented. If one conflicts with the current Strategy, name it as a
supersession decision for the native.

## Efficiency with quality (lens 2.3) — P4
Strategy §5 **P4**: *"Modes and single-predicate lifetime steps repeat geometry; caps leave
predicate coverage incomplete"* → *"reuse geometric search results across compatible
predicates/modes, then apply distinct semantic scoring and eligibility."* Equivalence: *"mode
identity and full applicable predicate coverage. Savings fund broader coverage; reduced caps
cannot pass as equivalent."* The June brief's *generator → interval-narrowing → ephemeris-last*
spine is the same idea; keep it. The inline threshold (June ruling) is the memory fix, not a cap.

## Synergy (lens 2.4) — the seven consumers, each with its own need
**Owes:** Kalasutra all qualified recurrences (A16: *"remove default-eight truncation"*);
Vighnakara a distinct obstruction root that does not attenuate twice (U03); Darshana the complete
route and coverage (A19); Taranga the mode-stratified score with its independence group (A18);
Jivana Parva mechanism links, not keywords (A20); Bhavishya a stable identity that never resets a
delivered forecast (U10); Tulana *matched* candidates with ties and incomparability preserved
(A04/Q02). **Receives:** Yojaka's compiled predicates (79 currently dangle — W1's job, not yours);
Vedha (undeclared — close the edge); the Gochara *service* (not the materialization — correct the
edge); L1 clocks at exact grain. Every edge with its F12 operator role.

## Cascade — both directions (lens 2.6; CURRENT_STATE §4.2; fence 7)
You are a **victim** of L2 rebuilds (five-table CASCADE from `bodha_msr_signals`; 14,868 rows
already lost) and a **source**: deleting convergence cascades obstruction and Darshana, nulls
Bhavishya's reference, and reaches multiple L4 tables through `phala_anchors`. Design generation
binding for both (FOUNDATION_SAFETY §6, frozen; physical W1 held). Fence 7: outcome-bearing or
`phala_anchors`-referenced Bhavishya rows are immutable — your rebuild must not null them.

## Consumer walkthrough (lens 2.5)
Q05 through `kala_explain_get` for the canonical chart and one ordinary period: what reaches
synthesis today (one scalar, one label, `dissent: []`), what would reach it after (typed
testimony with independence group, per-method state, comparability), and what the person can now
distinguish — three witnesses from one echo.

## Decisions to put to the native
Mode-stratified output contract vs mode as a field · the independence-group schema and whether
downstream must inherit it (U02) · which June rulings stand, which are superseded and why ·
generation binding shape given the bidirectional cascade · the served-tier packet (L3-U04/U11).

## Deliver
`SANGAM_ELEVATION_BRIEF_v1_0.md` in contract §1–§8 shape, reconciling **all three** prior
artifacts, with the latent-value register, the P4 equivalence contract, the seven-consumer
obligation table, the bidirectional generation design, and the A–J lenses. Propose; the native
rules.
