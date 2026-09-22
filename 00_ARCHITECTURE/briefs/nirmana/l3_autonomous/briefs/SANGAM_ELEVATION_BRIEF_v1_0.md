---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: SANGAM_ELEVATION_BRIEF
version: "1.4"
status: APPROVED_FOR_EXECUTION_STAGE_3      # native record 2026-09-23T02:42:50+05:30: SANGAM_RULING_SHEET §RULINGS; M-6 n OPEN; E1/E3 gated on Gochara N-7
approval_record: "SANGAM_RULING_SHEET_v1_0.md §RULINGS — M-1…M-7 in writing by the native, 2026-09-23T02:42:50+05:30 (M-6 minimum n OPEN)"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
asset_or_interface_ids: ["ka_sangam", "L3-U02", "L3-U07", "L3-U04/U11"]
goal_objective: "Make kala_convergence emit Strategy §3 Temporal testimony and Engagement route as typed fields — independence group, per-method F06 state, route, coverage, comparability — stratified by evidence grain, so a downstream consumer and the reconciling LLM can tell three witnesses from one echo and a silent method from an absent one."
source_revision: "origin/main; services/ka_sangam/engine.py and pipeline/orchestrator/writers/ka_sangam.py verified byte-identical to origin/main 2026-09-22 (W2 preserved ka_sangam unchanged)"
accepted_upstream_contract: "CURRENT_STATE §1 table — L2 bodha_msr_signals / kala_activation_predicates (ka_yojaka, DP-SD-019 repair 7697c43b3); L1 chart_dashas, chart_facts; no published L1/L2 generation exists to pin (§2.5)"
implementation_owner: "<unassigned — native to appoint; one writer>"
independent_review_owner: "<unassigned; must not be the author>"
release_authority: "NONE"
may_touch:
  - platform/python-sidecar/services/ka_sangam/engine.py
  - platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py
  - platform/migrations/1071+                       # check BOTH trees first (REDIRECT_002 §4)
  - platform/scripts/seed/asset_registry_seed.ts     # the two edge corrections only (§5.4)
must_not_touch:
  - platform-mcp/src/tools/kala_views/**             # Pūrṇa-owned; traced, never edited
  - platform/python-sidecar/pipeline/transit_search.py   # shared with Kshetra, Gochara family, frozen L0 bg_sky_calendar
  - platform/supabase/migrations/1035, 1036          # unmerged data-plane generation candidates
  - applied migrations 1033-1070
  - phala_* / mi_* tables                            # sealed L4/L5; reached only by interface packet
  - kala_gochara_windows WHERE generation='v1'       # protected retired sweep
  - kala_bhavishya outcome-bearing or phala_anchors-referenced rows   # fence 7
target_state_data_plane: "PLAN_REVIEWED. PRODUCER_READY is not claimable from this brief: no pinned input vector (§2.5); freeze never fired (§2.3)."
target_state_campaign: "no t3 event; none earned here. Every Kāla asset's true t3 state is no event; no superseded-definition freeze is borrowed."
wave: W3
scope: stages 0–2 of KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0; terminal PROPOSED_FOR_NATIVE_RULING
reconciles:
  - 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_KA_SANGAM_v1_0.md                        # June kernel — retained
  - 00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md            # §4.5/§4.6 native rulings 2026-06-22
  - 00_ARCHITECTURE/CONDUCTOR/cleanup/CLAUDE_CODE_PROMPT_KA_SANGAM_TRANSIT_REDESIGN.md  # READY — NOT implemented
  - 00_ARCHITECTURE/CONDUCTOR/cleanup/CLAUDE_CODE_PROMPT_KA_SANGAM_PER_SIGNATURE_FIX.md # READY — IMPLEMENTED on main
does_not_authorize: any code, migration, seed, build, grant or evidence event.
---

# ka_sangam — elevation brief (contract §1–§8)

**One sentence.** Saṅgam is where independence is computed, so it is the asset that decides whether
downstream reconciliation is possible; today it emits a count nobody in L3 reads, one domain, no
route, no silence, no coverage, and a score whose top-750 cut is a mode filter — and its rebuild
deletes sealed L4 rows. The elevation is an **output-contract** change: typed testimony, stratified
by grain, inherited downstream.

## §1 — Admission and exact authority

Header above. Three prior artifacts are reconciled, one carrying native rulings; §2.4 establishes at
the code which rulings landed. This brief proposes; the native rules. It stops at stage 2.

## §2 — Current-state evidence

### 2.1 Already established — cited, not re-derived (stage 0)

| Record | Row | Delta since |
|---|---|---|
| Contribution register v2.0 §5 | `:148` — *"Targeted/exploratory convergence and contact search. P/E/I/Q: consume full configuration/domains/conditions, not first domain or missing-dignity 0.5. DP06/08."* anchor `W/ka_sangam.py:331–377` | unchanged; both named defects still live (`:353`, `:348/:360`) |
| CURRENT_STATE §4.1 | `:135` — *"Yojaka, Vedha, services and L1-L2; invokes on-demand Gochara, not materialized `ka_gochara`"* → **"registry edges corrected before build"**; `:128` `ka_vedha_gochara` *"undeclared by Sangam"* | unchanged; closures specified §5.4 |
| CURRENT_STATE §4.2 | blast radius: victim of L2 MSR cascade; source into obstruction/Darshana/Bhavishya/`phala_anchors` | **sharpened** — migration 363 makes the L4 reach `CASCADE`, not `SET NULL` (§5.2) |
| Field register census #15 | `:269-287` — 19 fields, grain *"chart × tier × mode × peak × signal"*, NK = `chart_id, signal_id, mode, peak_date, horizon_tier`; all `Q1 digest-qualified; mode/tier provenance` | no field added since; §4.3 classifies each |
| Strategy §6.1 L3-A15 | *"one domain and missing ayanamsha identity need review … Remove hidden coverage caps and default independent-witness claims"*; P4 named | unchanged |
| FOUNDATION_SAFETY §6 (frozen) / fence 7 | generation design items 1–4; Bhavishya immutability | design frozen, physical W1 **held** |

### 2.2 Identity, files, algorithm

`ka_sangam` → `kala_convergence` (sole live writer; migration 980's four-check investigation,
re-confirmed). Writer `ka_sangam.py` (1,166 LOC); engine `engine.py` (1,812). Four modes sharing
I-16 scoring (`score = Π(necessary) × (1 − Π(1 − wᵢsᵢ))`, `engine.py:696-729`, ratified) but not a
search method: **A** daśā-soft-prior → contact scan; **B** off-daśā sweep; **C** subsystem
sign-residence periods; **D** SAV≥28 sign-ingress, *predicate-agnostic by its own comment*
(`ka_sangam.py:721-726`). Per-substep self-scoped delete-then-insert; cross-attempt resume ledger
(`:408-446`); SAVEPOINT-guarded soft reads (`:997-1034`, `:1055-1079`, `:1098-1126`) — the
codebase's correct example. Fail-loud birth-location (`:813-862`), house-from-Moon vedha frame.

### 2.3 Live state (labels per Layer contract §4)

- `generated_measurement` (LANE C, read-only, 2026-09-22): canonical chart **0 rows**; 20,497 live
  across two charts; `1c826d5a`: A 1,545 · B 1,190 · C 870 · **D 14,352** (→ 1,104 distinct
  tuples, ~13×); top-500/750 by score **100% Mode C**; ICC 2–6 rows 100% `speculative`, ICC-1 the
  only `high`; `peak_date` NULL 0/20,497; `domain` NULL 1,656/17,957.
- `historical_receipt`: 14,868 rows for the canonical chart lost to the L2 cascade
  (migration 403); `ka_sangam` is among 12/23 identities with **no surviving `plan_manifest`**
  across 522 build runs.
- `direct_source_read` (this session, `origin/main`): every `file:line` below.
- **Ladders.** Data-plane: below `PLAN_REVIEWED` until this brief is ruled. Campaign: no t3 event.
- **Cost.** Not `estimated_seconds` (463; F28). Dominant term: per-predicate Swiss
  `find_aspect_events` over a 100-year horizon × ≤60 lifetime predicates. Cite
  `KALA_COST_PROFILE_v1_0.md` when it lands.

### 2.4 The June rulings — what landed on `main` (stage 0 reconciliation of artifact 2)

| Ruling (native 2026-06-22) | On `main` | Evidence |
|---|---|---|
| §4.6 per-signature planet (DOSHA→Saturn, YOGA→Jupiter, DIGNITY→own graha, DISPOSITOR→lord, SUBSYSTEM→none) | **LANDED** | `_resolve_transit_planet` `engine.py:992-1015` (docstring cites §4.6); writer fills `graha_name` `:376`, `dispositor_lord` `:379` |
| §4.6 no hard cap; inline high-confidence gate | **LANDED as wording, NOT as mechanism** | `HIGH_CONFIDENCE_ORB_THRESHOLD=0.45` `:968`; `continue` at `:1171`, `:1400`. The code comment repeats the ruling (*"never accumulate in RAM"*), but `find_aspect_events` returns the full accumulated list before the engine filters (`transit_search.py:351-371`; evidence S7). No memory saving exists. |
| §6 no hardcoded fallback; absent if nothing fires | **LANDED** | `if planet is None: return windows` `:1145`, `:1375` |
| §4.5 Q1 no ephemeris scan; evaluate rules over pre-computed slow-transit events | **NOT LANDED** | `from pipeline.transit_search import find_aspect_events` inside `mode_a_search` `:1087`; `l3_timeline`/`_active_transits_for_period`/`SLOW_TRANSITS` referenced **nowhere** in the asset |
| §4.5 Q2 `planet` is a LIST | **NOT LANDED** | scalar `'planet': planet` `:1251, :1472, :1647, :1771` |
| §4.5 Q3 DAG cascade · Q4 version bump | not verifiable from source | process receipts, not read |

*W0's marker evidence (`per_signature`/`transit_trigger`/`slow_transit`; 7 and 5) does not
reproduce: only `transit_trigger` occurs — 6 and 4. The grep understated what landed; the §4.6
model is present under another name.*

**The conflict.** The two READY prompts are not additive. `PER_SIGNATURE_FIX` (*"apply directly on
main"*) landed; `TRANSIT_REDESIGN` (*"remove ALL ephemeris-scanning"*) did not. §4.6 resolves **one**
planet and scans it (`Optional[str]`); §4.5 Q2 needs the **set** that satisfied a rule, which
exists only under Q1's evaluate-over-events model. **The landed §4.6 structurally forecloses the
unlanded Q2.** Two further divergences: §4.5's *"slow transits only"* is not what the code does —
DISPOSITOR_RELATIONAL (5,145 predicates) resolves to a lord that may be Moon/Mercury/Sun, made
*filtered* by the gate after full accumulation (S7) — not cheap, and not *ratified*; and a missing `graha_name`/`dispositor_lord` returns `[]`
indistinguishable from "searched, found nothing" (F06 `unavailable` masquerading as `applied`).
**Not designed past** — decision **D-3** (§B), broadened in v1.3 to an *integrated* June
reconciliation covering **both** E3's fast tier and E1's new directed geometry (review B.3, D.1;
plan M-3). The redesign's own gate — *"L4 seal … do NOT rebuild
`ph_pratikara` until `kala_convergence` is corrected"* — precedes an L4 seal taken seven days later;
whether the gate was discharged is **D-4**, and its one-query verification criterion (planet
distribution diverse) was not run.

### 2.5 Generations, consumers, search boundary

**Input generations: none pinnable.** `l1_data_plane_generation_heads` = 0, `l2_…` = 0, no L3
head table (measured 2026-09-22). Every read resolves against mutable `public` rows L2's campaign
changes under a running build; the determinism gate is undefined until decision 1 rules.

**Consumers** (grep `FROM kala_convergence` over `writers/`, `services/ka_tulana|ka_temporal|
ph_nimitta|taranga_kernel`, `platform-mcp/src`, `platform/src`; tests excluded). Direct L3:
`ka_kala_darshana` (`LIMIT 750`), `ka_vighnakara` (`LIMIT 500`), `ka_taranga` (`WHERE domain IS NOT
NULL`), `ka_jivana_parva` (unordered `LATERAL … LIMIT 1`), `ka_kalasutra` (max score per signal),
`ka_tulana` (in-memory; `confidence_label` dataclass default `'speculative'`, `ranker.py:135`).
L4: `ph_nimitta` (per-domain `ROW_NUMBER` — the correct pattern; and an unordered `LIMIT 1` at
`:710-715`). L5: `mi_adhilepa` (**unordered `LIMIT 500`** feeding a calibration multiplier,
`:294-309`). Serving: `query_convergence_windows.ts:118-129` (drops `confidence_label_relative`,
`tier_basis`; `density_contract` occurrences 0). **Five `ka_*` writers select `convergence_score`;
zero select `independent_current_count`** — its only readers are `ph_nimitta.py:159,329` and the
serving capability. `UNRESOLVED_USE`: `mi_kula`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`,
`taranga_kernel`, `ka_temporal/date_resolver`, `kala_temporal.ts` — not traced.

**Field authority.** `convergence_score` — computed fact, within-grain, F12 *computes*.
`confidence_score` — `min(1, ICC/13)` `:965`, with `'transit': mode in ('A','B')` `:908` a
tautology and C13 structurally unreachable pre-U4 `:989`: **no detector → null (§N.8)**.
`independent_current_count` — hand-weighted coupling table `engine.py:850-889`: declared lineage,
*not* demonstrated independence (L3-U02). `domain` — `domains_affected_array[0]` `:353`.
Ayanāṃśa — `predicate.get('ayanamsha_id') or 'lahiri'` `engine.py:1097`, never stored.

## §3 — Failure

| Field | Content |
|---|---|
| Observed | `ORDER BY convergence_score DESC LIMIT 750` on `1c826d5a` → **750 Mode C rows**; `ka_kala_darshana`/`ka_vighnakara` consume exactly that cut. Rows with 2–6 declared witnesses are 100% `speculative`; the one discriminating tier is stored, not served. |
| Evidence | `generated_measurement` LANE C §C.4; `ka_kala_darshana.py:26-32`; `ka_vighnakara.py:177-183`; `engine.py:789-849`; `query_convergence_windows.ts:118-129`; re-verified on `origin/main`. |
| Expected contract | Strategy §3 *Temporal testimony* (independence group, silence, applicability); L3-Q05 *non-comparable scales*; F06; F08; P4 *"reduced caps cannot pass as equivalent"*; L3-U02. |
| Defect class | **flattened** (four grains, one key, one scale) → **unqualified** ranking, **duplicate support**, **unserved** tier, **detector mismatch** (`confidence_score`). |
| Impact | No daśā×transit convergence reaches either consumer; every L3 obstruction judgment and temporal view rests on sign-ingress windows alone. The reconciling LLM cannot distinguish three witnesses from one echo, nor a method that found nothing from one that never ran. L3-Q02/Q05 unanswerable from what is served. |
| Non-claim | Does not prove A/B rows improve any downstream answer (the §4.7 ablation, not run); does not judge Jyotish validity of any mode; does not establish live incidence on the canonical chart (0 rows). |

## §4 — Semantic change and expected distinction

### 4.1 The finding that reframes the asset: four grains, one key

Modes A/B: (signal, contact instant) — genuinely predicate-bound. Mode C: (subsystem,
sign-residence period). Mode D: (chart, scan planet, sign ingress) — **predicate-agnostic**, yet
handed `predicate=pred_dict` and stamped with its domain (`:728-737`). Consequences:
(i) the declared NK (migration 981: `chart_id, horizon_tier, mode, peak_date, signal_id`) **licenses**
the 13× duplication — 0 duplicate-key groups is true and uninformative; (ii) migration 866 encodes
it as *"EXACT: 25 × 478 (Mode D) + 2918"* = 14,868 — the vacuous guard `pred_dict is pred_dicts[0]`
(`:726`) against `pred_dicts=[pred]` (`:591`) written as a specification; repair drops the canonical
floor to **≈3,396 (−77%)**, correct under §N.4; (iii) Mode D rows are cascade-bound (403) to a
signal they do not depend on; (iv) F7 is a symptom: `convergence_score` is within-grain used as a
cross-grain rank key. **Partition now; comparability is a separate, possibly unanswerable question.**

### 4.2 Target-state design — the ideal producer (lens 2.2)

Start from the objects, not the columns. The ideal `kala_convergence` row *is* a Strategy §3
**Temporal testimony** carrying an **Engagement route** and a **Search coverage**:

| Object member | Proposed field | Type | Semantics |
|---|---|---|---|
| target structure + exact evidence roots | `signal_id` (A/B/C), `evidence_roots` | UUID; `text[]` of L1 `fact_id` | referenced, never restated (§N.5) |
| method/family + **grain** | `mode`, `comparability_class` | text | `A_B_contact` · `C_residence` · `D_ingress`; extends `tier_basis`'s discipline. A projection may rank only within one class. |
| independence group | `independence_groups` | jsonb `[{group_id, family, roots[], members[], basis:'declared_lineage'}]` | groups, not a count; `basis` never `'demonstrated'` until L5 decorrelation exists. Derived `independence_group_count`. **Inherited** (§4.5). |
| support / opposition / **silence** per method | `method_states` | jsonb `{current_key: applied \| inapplicable \| unavailable \| unqualified \| contradictory_unresolved \| unexplored}` | F06; replaces `_current_stance`'s honest-empty with the full six; `unavailable` when `graha_name`/`dispositor_lord` missing |
| applicability, necessary/optional clauses, enablement/inhibition, alternatives | `route` | jsonb | Engagement route: `{necessary:[…], optional:[…], satisfied:[…], failed:[…], inhibitors:[…], route_id, alternatives:[…]}`; vedha enters as inhibitor, not only as a score multiplier |
| requested vs completed horizon, exclusions, caps | `coverage` | jsonb | `{requested:[s,e], completed:[s,e], resolution:'date', filtered_below_orb:n, failed_modes:[…], caps_applied:[…]}`; L3-Q08 |
| material uncertainty | `uncertainty` | jsonb | orb, boundary convention, ayanāṃśa sensitivity |
| identity | `ayanamsha_id`, `domains` | text; `text[]` | S-E/S-F; `domain` retained one release as alias |
| **removed** | `confidence_score`, `confidence_label` | — | replaced by testimony (Product §5.2: no substitute scalar); `confidence_label_relative`+`tier_basis` retained |
| renamed | `independent_current_count` → `declared_current_count` | smallint | stops claiming what it does not measure (U02) |

Preserved: I-17 orb, I-18 peak/shoulder, `constituent_factors`, `is_off_dasha_discovery`, `horizon_tier`.
**Changed by the method plan (v1.3):** I-16's algebraic form survives only for genuine necessity (orb
presence, route satisfied) — dignity leaves the necessary product and becomes `valence`
(SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4 R-6 / M-7; `score([0,1,1])=0.0` erases adverse activity,
evidence S11). I-19 `rarity_years` is **retired** in favour of `modelled_episode_frequency` on a
declared exposure (plan E6).

### 4.3 Latent-value register (lens 2.1)

| Field / computation | Class | Fix |
|---|---|---|
| `confidence_label_relative`, `tier_basis` | **(a) persisted, discarded by consumers** — trimmed at `query_convergence_windows.ts:118-129` | L3-U04/U11 packet + sentinel test |
| `independent_current_count` | **(a)** — zero `ka_*` readers | §4.5 inheritance rule; rename |
| `constituent_factors` roots, per-current values, `convergence_score_pre_trigger` | **(a)** partially — survives retrieval, not any `ka_*` consumer's projection | typed `method_states`/`route` lift the material members out of JSONB |
| `domains_affected_array[1:]` | **(b) computed, discarded before persistence** (`:343`→`:353`) | `domains text[]` |
| `ayanamsha_id` | **(b)** — used for the daśā query, never stored | column + NK |
| count of sub-threshold events, failed modes | **(b)** — `continue`d / `warning`-logged, never reported (`:1171`, `:1400`, `:654/690/716/738`) | `coverage` |
| `route`, per-method silence | **(c) genuine gap** | §4.2 |
| independence as *groups* | **(c)** — only a count exists | §4.2 |
| `confidence_score` | **(d) available, unqualified** — no detector | remove |
| `max_level=3`, closed-closed daśā test (`engine.py:1124`, `:1138`) | **(d)** — undetermined semantic vs accident | S-G/S-H: one query each |
| `dignity_score` NULL→0.5 in the selection key (`:348/:360`) | **(d)** | F06 `unavailable`; exclude from rank, report in coverage |
| near-tier `as_of_date` (`:540`) | **(b) computed, discarded** — the horizon anchor is never stored | `coverage.requested`; generation vector |
| birth-instant tz offset (`:854`) | **(d) unqualified** — offset at run time | offset at birth instant |

VA §10.3's offensive question: the entities that unlock a new consumer capability are **cross-domain
convergence** ("simultaneously a career and a relationship window" — B.11's Cross-Domain Linkage,
unrepresentable today) and **negative cases** ("no window, and here is the searched range").

### 4.4 Mode stratification + the P4 equivalence contract (lens 2.3)

**Rule:** no ranked or truncated projection of `kala_convergence` may rank across
`comparability_class`. Partition every top-N by class (and by domain where the consumer is
domain-scoped), each with a declared floor. Precedent to copy: `ph_nimitta.py:337-348`.

**Equivalence contract, per Strategy §5 P4:** *mode identity and full applicable predicate
coverage; savings fund broader coverage; reduced caps cannot pass as equivalent.* Therefore:
Σ(partition floors) ≥ current budget (750 must not become 4×150); any total reduction is declared
as a semantic change with its own consumer-effect statement. Pre/post identity method: for each
consumer, the multiset of `(class, signal_id, peak_date)` it receives before vs after — the after-set
must be a superset per class **as a regression check only (v1.3, review F-17 / D.1)**; the acceptance
comparison is a **mapped semantic comparison** over the applicable-universe manifest (plan §6.2),
which may withdraw explicitly invalid old rows (e.g. contacts scanned against a defaulted 0° target). Speed: P4's shared geometry across compatible predicates/modes is
adopted **without** touching `transit_search.py` (S-I, Gochara v0.3 R2 verbatim); the June
inline gate was ratified as the memory fix; as landed it filters after full accumulation (S7), so **no runtime saving is claimed** (v1.3). Free saving from the Mode D repair: 24 of 25 redundant
century ingress scans on the canonical chart.

### 4.5 Inherited independence — the U02 packet's core

Any projection that carries `convergence_score` carries `independence_groups` and
`comparability_class` with it; a projection that drops them is a contract violation the delivery
sentinel detects. U02 verbatim: *"zero supporting evidence cannot become one independent witness;
another representation of the same origin adds no independent support."* The coupling table stays
as **declared lineage** (S-A option a, now) — with its name corrected — until empirical
decorrelation exists (option c, L5-gated).

### 4.6 Synergy — the seven consumers (lens 2.4)

**v1.3:** the authoritative per-consumer disposition is the seven-consumers × six-elevations matrix
adopted in `SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4` §6.2 (from the second review E.1), including its
correction that `kala_views/priority.ts`'s ranking SQL does **not** read `kala_convergence`. The
table below is the contract-level summary.

**Owes** (each edge with F12 role):

| Consumer | Strategy | Needs from Sangam | F12 |
|---|---|---|---|
| `ka_kalasutra` | A16 *"retain all qualified recurrences … remove default-eight truncation"* | every recurrence per signal, not max-score-per-signal; `coverage` so its own absence is bounded | computes |
| `ka_vighnakara` | U03 *"a duplicate representation does not attenuate twice"* | a **distinct obstruction root** — vedha as `route.inhibitors` with root id, not a second multiplier | counterevidence |
| `ka_kala_darshana` | A19 *"expose complete qualified route and coverage; resolve top-750"* | `route`, `coverage`, class-partitioned cut | computes / navigates |
| `ka_taranga` | A18 | class-stratified score **with** `independence_groups`; `domains[]` (stops dropping 9.2% NULL-domain rows) | computes |
| `ka_jivana_parva` | A20 *"mechanism links, not keywords"* | `route.route_id` + `evidence_roots`; a total `ORDER BY` on its `LATERAL … LIMIT 1` | interprets |
| `ka_bhavishya_lekha` | U10 *"candidate regeneration does not reset a delivered forecast"* | a **stable identity** — natural key, not `convergence_id` (§5.2) | evaluates |
| `ka_tulana` | A04/Q02 *"ties and incomparable states"* | matched candidates within one class; `comparability_class` so cross-class pairs are `incomparable`, never ranked; `domains[]` its model already declares | navigates |

**Receives** — and where richness dies on the way in (the seams): Yojaka predicates (79 dangle —
W1's, not this packet's); `bodha_msr_signals` domains → **one** at `:353`; dignity NULL → 0.5 in
the rank key at `:348/:360`; Vedha (**undeclared** — close, §5.4); Gochara **service**, not the
materialization (edge type wrong — correct, §5.4); L1 clocks via `KaDashaKalaService` at
`max_level=3` with a closed-closed test (S-G/S-H); ayanāṃśa defaulted at `engine.py:1097`; Mode D
stamped with a signal it never read (`:728-737`).

### 4.7 Consumer walkthrough — Q05 through `kala_explain_get` (lens 2.5)

*Trace boundary:* `explain.ts` has no direct `kala_convergence` read; it initialises
`reading.dissent = []` (`:302`) and only a KP-voice path can append (`:433-447`). Convergence
content reaches it through Pūrṇa-owned services not traced here.

**Today, canonical chart, "why do timing methods disagree?"** — nothing from `kala_convergence`
(0 rows). On `1c826d5a`: one `convergence_score`, one degenerate label, a count nobody reads, one
domain, and a `dissent: []` no convergence detector could ever populate. The person cannot tell a
five-witness dated window from a one-witness sign residence.

**After:** per row — class, `independence_groups` (e.g. *daśā+nakṣatra = one lineage; Saturn
contact = second; tājika = third*), `method_states` (*pāñcāṅga: inapplicable; school consensus:
unexplored*), `route` (*necessary: daśā-eligible ∧ contact; inhibitor: vedha root #…*),
`coverage` (*searched 2019–2029 at date grain; 14 events filtered below orb 0.45*). The person can
now distinguish **three witnesses from one echo**, and **"no window in the searched range"** from
**"this method did not run here."**

**Ordinary period (Product §9):** a month with no Mode A/B contact and one Mode C residence —
today: top-N shows the residence as a "high-confidence convergence"; after: one `C_residence` row
with one lineage, `coverage` stating A/B searched and silent. That is the honest ordinary answer.

### 4.8 Old vs new · baseline · ablation · questions

| Input | Old | New |
|---|---|---|
| positive (A contact in eligible daśā) | scored, `speculative`, one domain | scored within class; groups; route satisfied; domains[] |
| negative (no contact in horizon) | no row — indistinguishable from failure | no row **and** `coverage` on the predicate's search record; `method_states.transit=applied` |
| boundary (daśā boundary date) | closed-closed double-membership | convention declared in `uncertainty`; S-H rules which |
| missing (`graha_name` absent) | `[]`, silent | `method_states.transit=unavailable` |
| duplicated (Mode D per substep) | 25 rows per window | one row, no signal id |
| same chart rebuilt a day later | near tier silently differs; lifetime resume invalidated | identical under the same `as_of_date`; lifetime resume survives midnight |

**Simpler baseline** (Execution Brief §1): the current scalar/truncated projection — top-750 by
`convergence_score`, one label, one domain — under the same chart, question, horizon and budget.
**Value metric:** count of consumer distinctions expressible (class, witnesses, silence, coverage)
and the Q02/Q05 primary proofs. **Ablations:** (1) rebuild `ka_kala_darshana` on current vs
class-partitioned top-750; if identical, Mode C carried the signal — itself a finding; (2) remove
one "independent" and one "coupled" current from an ICC-5 row — if the score moves identically, the
coupling table is decorative; (3) count rows whose `domain` changes using `[1]` instead of `[0]`;
(4) dedupe Mode D, re-run every consumer.

**L3-Q served:** Q02 primary; Q01, Q04, Q07 contributor. **Partial:** Q05 (holds the material,
flattens it). **Cannot today:** Q08 (no coverage object). `VALUE_EVALUATED` is N for every L3-Q.

**Time discipline (lens 2.6) — three time-of-run reads, three classes:**

| Site | What it does | Class | Disposition |
|---|---|---|---|
| `ka_sangam.py:540-548` | near tier horizon = `[date.today(), today+7y]` | **implicit today** — the defect class Strategy A16/P5 names for Kalasutra, here on Sangam. Legitimate *purpose* (next seven years), illegitimate *mechanism*: the as-of date is an input to the generation vector (§5.2 item 1) and to `coverage.requested`, and must be explicit and recorded, never read at run time. | `as_of_date` explicit parameter; stored in `coverage`; part of the content address |
| `:546` `date(today.year+7, today.month, today.day)` | | **boundary bug**: a build started on **29 February** raises `ValueError` (no Feb 29 seven years on). Live path: every near-tier build; incidence: one day in ~1,461. | proof-matrix boundary row |
| `:478` | `today` deliberately in the resume fingerprint (docstring: *"a build that legitimately crosses midnight should replan its near tier rather than resume it stale"*) | honest, and a consequence: the **lifetime** tier — 60 substeps, not date-relative — is also invalidated at midnight because one fingerprint covers both tiers | per-tier fingerprint; falls out of `as_of_date` |
| `:854` `ZoneInfo(tzid).utcoffset(datetime.now())` | timezone offset taken at **run time**, not at the birth instant | **wrong context** — the input-side twin of the measured 5.5-hour `kala_tithi_pravesha` defect. Benign for Asia/Kolkata (no DST since 1945): both live charts. Wrong for any DST or historically-shifted zone. No live incidence measured; hazard on every build of such a chart. | `utcoffset(birth_instant)` |

No naive-into-`timestamptz` write found (`computed_at` is SQL `NOW()`, migration 981). Rows at
DATE grain. A rebuildable projection; never reads L4/L5 (§5.1); no rectification input read.

## §5 — Preservation, migration, history, rollback

### 5.1 Dispositions

| Component | Disposition | Why |
|---|---|---|
| I-17/I-18, `constituent_factors`, resume ledger, SAVEPOINT reads, CR-87 (birth location — **not** the lagna read, which defaults to Aries at `:1149`), CR-102 | **PRESERVE** | correct engineering |
| I-16 kernel | **ENRICH_CORRECT** (plan R-6) | necessity-only; dignity → valence; legacy generation `kernel_version=legacy_i16`, never pooled |
| D-3 per-class quota selector; self-scoped delete policy | **PRESERVE mechanism, QUALIFY_LIMIT policy** | a capped selector is not the applicable universe; delete safety depends on the generation/cascade design (review A-01) |
| Modes A, B | **ENRICH_CORRECT** | typed testimony; class |
| Mode C | **QUALIFY_LIMIT** | distinct meaning (S-D); own class |
| Mode D | **ENRICH_CORRECT** or **QUALIFY_LIMIT** (native) | regrain to `(chart, tier, scan_planet, sign, ingress_peak)`; modifier or excluded from ranked projections |
| `confidence_score`, `confidence_label` | **RETIRE_AFTER_MIGRATION** | §N.8; consumers `ka_tulana`/`ka_kala_darshana` migrate first |
| `independent_current_count` | **QUALIFY_LIMIT** (rename) | U02 |
| `domain` | **RETIRE_AFTER_MIGRATION** → `domains[]` | one-release alias |
| `rarity_years` | **UNRESOLVED_USE** | unaudited (§C) |
| registry edges `ka_gochara`, `ka_vedha_gochara` | **ENRICH_CORRECT** | §5.4 |
| near-tier horizon anchor, tz offset | **ENRICH_CORRECT** | §4.8 time discipline |
| `transit_search.py` | **PRESERVE — must not touch** | S-I |

### 5.2 Cascade, both directions, and the bidirectional generation design

**Victim (above):** five `kala_*` tables `ON DELETE CASCADE` from `bodha_msr_signals`
(403); `kala_convergence` fired — 14,868 rows. **Source (below), citing CURRENT_STATE §4.2 and
adding what this session measured at the constraint:** `kala_obstruction` (`245:12`) and
`kala_darshana` (`247:6`) CASCADE; `kala_bhavishya.convergence_id` SET NULL (`249:28`);
**`phala_anchors.convergence_id` CASCADE — migration 363 changed it from SET NULL** → deletes
sealed L4 rows → `phala_suddha_sodhana` CASCADE (`334:18`), `phala_muhurta`/`phala_mitigation`
SET NULL (`331:26`, `332:10`), `phala_phaladesa.top_anchor_id` **FK-free → silent orphan** (`339:34`).
363's rationale (*"L4 rebuild regenerates them"*) holds only if an L4 rebuild follows.

**Root cause, structural:** L4 binds to `convergence_id`, a bigint sequence **surrogate** not in
the INSERT list — new on every rebuild. The writer's byte-identical resume is idempotent inside the
table and **cannot be across the layer boundary**; every lifetime substep's own delete (`:576-579`)
erodes L4 incrementally.

**Design, under FOUNDATION_SAFETY §6 items 1–4 (frozen):**
1. Each `kala_convergence` generation is content-addressed from (asset contract digest, chart,
   ayanāṃśa, the L2 `bodha_msr_signals` **generation** and `kala_activation_predicates` partition,
   the L1 clock/fact partitions, engine semantic version). Empty partition = explicit result.
2. Rows carry `generation_id`; **upward** binding replaces the live `signal_id` FK as the
   integrity mechanism — a new L2 generation does not delete, it makes the old convergence
   generation *not selected*. **Downward**, L4 binds to the **natural key + generation**, not
   `convergence_id` — an **L3-U07 packet with a test** (L4 is sealed; never an L3 edit).
3. Candidate ≠ selected head; selection only after every partition (per class, per tier) and the
   U02 inheritance check pass.
4. Correction = new generation; rollback = repoint the head.
**If decision 1 rules no L3 generations:** the Mode D regrain matters *more* (the only thing that
removes predicate-agnostic geometry from the cascade); `bodha_signal_identity` determinism
mitigates re-attachment, not deletion; A/B/C rows are then destructible by any L2 rebuild and every
Sangam rebuild on a chart with L4 rows must be paired with authorized L4 regeneration — or not run.

**The dependent map must cover every entity, not only the final table's surrogate (v1.3, review
F-19 / RR-08):** `kala_obstruction`, `kala_darshana` (CASCADE), `kala_bhavishya` (SET NULL),
`phala_anchors` (CASCADE), `phala_suddha_sodhana` (CASCADE), `phala_muhurta` / `phala_mitigation`
(SET NULL), and `phala_phaladesa.top_anchor_id` (**FK-free**, resolved semantically) — compared by
exact content per original stable id, never by count or unframed hash; the real Bhaviṣya columns
are `outcome_recorded` / `outcome_notes` (plan §6.3).

**Fence 7 binds:** outcome-bearing or `phala_anchors`-referenced Bhavishya rows are immutable
absent a generation schema; a rebuild that nulls their `convergence_id` violates it. **Not binding
on the canonical chart (0/0 rows); binding on `1c826d5a`.**

### 5.3 Keys and the atomic Nirmāṇa set

**v1.3 (review F-12 / RR-04):** a `peak_date`-anchored key is unstable under any algorithm change
that moves a peak. The tuples below are **superseded as the identity** by the method plan's R-5 —
stable **contact / episode identity + generation** (`SANGAM_ALGORITHM_ELEVATION_PLAN_v0_4` §3
R-3(b), R-5) with explicit split / merge / supersession relations published before any key change.
They remain the *geometry cache key* (R-3(a)) and the migration-facing partition, not the testimony
identity.

| Rows | Proposed NK |
|---|---|
| A / B | `(chart_id, ayanamsha_id, horizon_tier, mode, signal_id, peak_date)` |
| C | `(chart_id, ayanamsha_id, horizon_tier, mode, subsystem, period_start)` |
| D | `(chart_id, ayanamsha_id, horizon_tier, mode, scan_planet, sign, ingress_peak_date)` — **signal_id leaves** |

Any key change re-issues, **in the same change**: migration **866** (`target_floor`
14,868 → achieved count; formula), **980** (`asset_output_digest_specs` key/value columns), **981**
(`natural_key_partition`). Authored at `platform/migrations/1071+` after checking both trees
(`migrate.ts:834-835` reads them as one sequence; never collide with `1035/1036`). *Observation:*
the seed file carries `target_floor: null` while 866 sets it live — a reseed divergence path.

### 5.4 The two registry edges (CURRENT_STATE §4.1 "corrected before build")

| Edge | Live | Correction | F12 |
|---|---|---|---|
| `ka_gochara` | declared (`asset_registry_seed.ts:2313`); never reads `kala_gochara_windows*` — constructs `KaGocharaService(swe)` `ka_sangam.py:317-320` | reclassify **scheduling**, not computational | relevance_navigation |
| `ka_vedha_gochara` | read `:1055-1073`, **undeclared**; asset at `:2586` | **declare** computational | counterevidence — a veto on necessary conditions |

### 5.5 Rollback and history

Nothing in `kala_convergence` is protected history; the first canonical build is also the first
freeze — **one captured, verified `plan_manifest` dispatch before elevation** (S-J). Per-substep
self-scoped delete predicate moves with the key. Rollback unit = generation head + 866/980/981.
Retirement of `confidence_*`/`domain` only after consumer migration is proved (contract §5).

## §6 — Focused proof matrix

| Proof | Fixture / command | Expected · invariant | Detector that returns false |
|---|---|---|---|
| Positive | synthetic chart, one YOGA predicate, Jupiter contact inside eligible daśā | one `A_B_contact` row; `independence_groups` = 2 (daśā lineage, contact); `route.satisfied` lists both | row absent, group count ≠ 2, or route empty |
| Negative | predicate with `graha_name=None` (DIGNITY) | zero rows; `coverage.method_states.transit = unavailable` recorded on the predicate's search record | state reads `applied` or record absent |
| Relevant influence | flip vedha present→absent | `route.inhibitors` empties; score rises; unrelated rows byte-identical | any unrelated row changes |
| Irrelevant control | permute `domains_affected_array`, predicate insertion order | rows and digest identical | digest differs |
| Duplication/correlation | Mode D over 25 lifetime substeps | 478 rows, not 11,950; daśā+nakṣatra counted as one group | count > 478, or groups = 2 |
| Context/missingness | wrong `chart_id`; missing ayanāṃśa | fail-loud (CR-87 pattern), never default `'lahiri'` | a row with defaulted ayanāṃśa exists |
| Boundary/precision | daśā boundary date; **build dated 29 Feb**; a DST-zone chart | membership follows the declared convention (S-H); near horizon computed without error; tz offset equals the birth-instant offset | double membership undeclared; `ValueError` at `:546`; offset ≠ `utcoffset(birth_instant)` |
| Delivery | sentinel value only in `independence_groups` on a low-ranked row | survives SQL projection → `query_convergence_windows` → budget trim → synthesis → saved result (Execution Brief §7) | sentinel absent at any hop |
| Revision | new L2 generation | old convergence generation retained, unselected; L4 `phala_anchors` rows untouched | any L4 row count changes |
| Value | Q02/Q05 on `1c826d5a`, current vs after, same budget | consumers receive ≥ per-class multiset (P4); distinctions expressible ↑; ablation (1) recorded either way | per-class superset violated |
| Evaluation | — | separately governed; **NOT_RUN** | — |

Tiers kept separate (F24): rows 1–9 are `COMPUTATIONAL_CORRECTNESS`; row 10 is
`EXPLANATORY_DISCRIMINATIVE_VALUE`; `EMPIRICAL_OUTCOME_PERFORMANCE` is not claimed.

## §7 — Implementation and review discipline

One writer surface, an isolated worktree named in the approved brief; never `transit_search.py`;
frozen orchestrator contract (`ctx.db_conn` never committed; no `asset_throughput` writes).
Absence of authority is `NOT_RUN`. Independent reviewer ≠ author; must attack §4.1(ii)'s
arithmetic and §2.4's audit first. Green CI, a PR, a row count are not terminal proof.

## §8 — Terminal evidence packet (owed by stage 3; not produced here)

Approved brief + upstream pin · exact commits/files/migrations (1071+) · old/new examples per
§4.8 · generation/invalidation/rollback evidence incl. 866/980/981 · raw commands for §6 ·
reviewer identity and findings · state reached (`PRODUCER_READY` at most) and states unreached ·
residual risks and decisions returned · confirmation `must_not_touch` untouched.

---

## Appendix A — lenses A–J

**A** §4.1: four grains, one asset; intent = dated convergence testimony. **B** §2.5, §5.4: no
pinnable generation; two edges corrected. **C** §2.5 field authority, §4.2: scalar retired,
testimony typed. **D** §4.3 register. **E** §4.6, §4.4. **F** §4.7 walkthrough; Q-map §4.8.
**G** §4.4 P4 contract. **H** §5.2 cascade; fence 7. **I** §5.3 atomic set; 1071+. **J** §6, §C.

## Appendix B — decisions for the native

| # | Decision | Recommendation |
|---|---|---|
| D-1 | Mode-stratified output contract (class partitions every cut) vs mode as a mere field | stratified; a cross-class cut is a *reduced cap* (P4) |
| D-2 | `independence_groups` schema (§4.2) and mandatory downstream inheritance (§4.5) | adopt; name `basis:'declared_lineage'`; rename the count |
| D-3 | **June rulings:** §4.5 Q1/Q2 re-affirmed (then `_resolve_transit_planet` is replaced and `TRANSIT_REDESIGN` scheduled) **or** explicitly superseded by the landed §4.6 (then both marked SUPERSEDED). Not by silence. | no position on which; refusal of drift |
| D-4 | Was the L4 seal's gate discharged? Run the planet-distribution query and read the `ph_pratikara` receipt | before Sangam moves; an L4 matter if not |
| D-5 | Generation binding shape: upward L2-generation, downward natural-key (L3-U07 packet) | adopt; state fallback (§5.2) |
| D-6 | Served-tier packet L3-U04/U11 to Pūrṇa: `confidence_label_relative`, `tier_basis`, `independence_groups`, `comparability_class`, `coverage` | raise; L3 owns the sentinel test |
| S-A…S-J | carried from LANE C §C.8 unchanged | S-A (a) now, (c) later; S-B `judgment_flags`; S-C partition now; S-D modifier; S-E/S-F yes; S-G/S-H one query each; S-I verbatim; S-J first |
| S-K/S-L | four keys, one table; accept the −77% floor with 866/980/981 atomic | yes / yes |

## Appendix C — not established

1. `rarity_years` unaudited (measured base rate vs formula). 2. §4.5's verification query not run;
Q3/Q4 receipts not read. 3. No live DB query this session — live figures are LANE C's or 866's own
arithmetic; code re-verified on `origin/main`. 4. Five-vs-four inheriting consumers: measured five
(`jivana_parva`, `kala_darshana`, `kalasutra`, `taranga`, `vighnakara`). 5. S-G/S-H: one query each,
not run. 6. `UNRESOLVED_USE` list in §2.5. 7. `explain.ts` convergence path beyond the stated
boundary. 8. Every method question — convergence, independence, whether a residence and an aspect
share a scale — remains the native's. 9. Independent reviewer unassigned. 10. **Retracted in this issue:** v1.2's first draft
asserted "no `date.today()` in this asset"; a grep found three time-of-run reads (§4.8). Recorded
so the reviewer knows the claim was checked, not assumed.

## Changelog

- **1.4** (2026-09-23) — Native rulings M-1…M-7 recorded on the sheet and applied; status → APPROVED_FOR_EXECUTION_STAGE_3 with conditions (M-6 minimum n open; E1/E3 gated on the Gochara N-7 ruling; D30-for-DOSHA held; 6/8/12 inversion does not ship; legacy scan one generation; no node dṛṣṭi). No content change beyond frontmatter and this entry.

- **1.3** (2026-09-23) — Companion amendments required by the method plan (SANGAM_ALGORITHM_
  ELEVATION_PLAN_v0_4 §7) after two independent reviews: streaming/memory claims corrected (S7);
  I-16 re-dispositioned ENRICH_CORRECT (R-6), `rarity_years` retired (E6); §5.3 identity superseded
  by contact/episode identity + generation; §5.2 dependent map extended to nullable and FK-free
  references with real outcome columns; §4.4 superset test relabelled a regression check with a
  mapped semantic comparison; D-3 broadened to the integrated June reconciliation; §4.6 pointed at
  the adopted 7×6 matrix. No new claim added.

- **1.2** (2026-09-22) — Reshaped to contract §1–§8; **time discipline corrected** — three
  time-of-run reads found (`:540` implicit today, `:546` 29-Feb `ValueError`, `:854` tz offset at
  run time) after a first draft wrongly asserted none. per `ELEVATION_PROMPT_SANGAM_v2` and
  `KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0`. Added: target-state design from the two owned §3
  objects (§4.2); latent-value register (§4.3); P4 equivalence contract (§4.4); U02 inheritance
  rule (§4.5); seven-consumer obligation table with F12 roles and the receive-side seams (§4.6);
  Q05 walkthrough incl. ordinary period (§4.7); bidirectional generation design under
  FOUNDATION_SAFETY §6 with both rulings of decision 1 (§5.2); proof matrix with detectors (§6).
  Carried from 1.1: June audit (§2.4), migration-363 CASCADE and the surrogate-id root cause,
  registry edges, 1071+ placement. Carried from 1.0: four-grains/one-key (§4.1) and the 866
  expected-volume finding.
- **1.1** — three-artifact reconciliation; June audit; cascade to L4; edges; P4 binding.
- **1.0** — first issue, §6.4 packet shape.
