---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
version: "4.4"
status: PROPOSED_FOR_NATIVE_RULING
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
asset_or_interface_ids: ["ka_kshetra", "L3-U11 (kala_field retrieval capability)", "L3-U01 (S2 signed-structure seam)"]
goal_objective: >
  Qualify the Interval/trajectory-segment object ka_kshetra already emits (synthetic-vs-calibrated
  baseline on the row; exact null semantics; admitted σ_T input), and give it a reach (an L3-U11
  capability with a sentinel test) — stage by stage, without building on any populated chart.
source_revision: "main @ c58e86662 (services/ka_kshetra/ byte-identical to l3/kala-elevation-readiness @ 86ee604ea)"
accepted_upstream_contract: >
  CURRENT_STATE §3 table. W0 accepted content on main BY CONTENT (REDIRECT_002 §1): Kshetra P0
  3f109869d; DHARA midpoint fix 87cc8c9baf; DHARA_SWEEP_SEMANTIC_VERSION='1.2' (dhara_sweep.py:52).
  Physical L1/L2 generation heads ABSENT in the connected environment.
implementation_owner: "Execution — Data Plane task (codex/madhav-data-plane-execution), the sole execution destination per Strategy §8 — assigned 2026-09-23 on the native's delegation ('do the rest on my behalf'); overridable by native record"
independent_review_owner: >
  PARTIAL — madhav-fc (L3 strategic session) for the parts it did not shape; it declines to certify
  rulings 7/8/9 (node; vedha admission/G-9; G3), whose evidence it co-produced. Reviewer for 7/8/9:
  NATIVE TO NAME. Assigned 2026-09-23 on the native's delegation; overridable by native record. See
  KSHETRA_RULING_SHEET_v1_0.md owners line.
release_authority: "NONE"
may_touch: >
  services/ka_kshetra/{hazard,layer1,writer,stage2_promise,stage3_clocks,uncertainty}.py;
  dhara_null.py (docstring only); platform/python-sidecar/tests/l3/**; ONE migration at
  platform/migrations/1071+ (check BOTH directories); FIELD_CONTRACT_REGISTER deltas (§2.3).
must_not_touch: >
  platform-mcp/src/tools/kala_views/** (Pūrṇa); platform/src/lib/retrieval/registry/** (U11 packet
  — Pūrṇa implements, L3 owns the test); api/mcp/db/query/route.ts; applied migrations 1033-1070 and
  supabase/migrations/1035,1036; deploy.yml; kala_gochara_windows WHERE generation='v1';
  kala_insights WHERE lel_derived=true (fence 4); kala_field_weight_versions/weights (INPUTS, fence 6);
  build_substep_progress (orchestrator, fence 6); ANY populated writer-owned slice (KshetraReplacementHeld).
target_state_data_plane: "PRODUCER_READY. DATA_ACCEPTED needs a build; populated-chart builds are held to W7."
target_state_campaign: "Under t3-2026-09-11-8b884eac ka_kshetra has NO EVENT. This brief earns ANALYZED only."
scope_stages: "Template v2.0 stages 0-2 (Reconcile · Frame the value · Brief). Stage 3 is a separate execution session."
shape: "Staged internal DAG — the frozen stage plan is the packet boundary (FOUNDATION_SAFETY §6 item 5)."
governed_by: KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md · KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md §2-§12 · ELEVATION_PROMPT_KSHETRA_v2.md · W0_DELTA_KSHETRA.md · KALA_ASSET_BRIEF_CONTEXT_v1_0.md
does_not_authorize: "Any change. A populated brief is a proposal until the native rules."
changelog:
  - "4.4 (2026-09-23) — independent_review_owner amended: madhav-fc declared a conflict on rulings 7/8/9 (co-produced evidence) and accepts only the non-conflicted scope; the 7/8/9 reviewer is left for the native to name. Kimi files given frontmatter; interior rules in the review rendered as *** ."
  - "4.3 (2026-09-23) — owners assigned on the native's delegation (implementation: the Execution — Data Plane task per Strategy §8; independent review: madhav-fc, not the author). Rulings NOT self-approved: status stays PROPOSED_FOR_NATIVE_RULING; the native signs KSHETRA_RULING_SHEET_v1_0.md (contract §8: a packet never approves itself)."
  - "4.2 (2026-09-23) — Gochara-session corrections, verified: vedha chain → bg_transit_rules + Phaladīpikā Ch.26 (no bg_phaladeepika_vedha relation exists); second v1 COALESCE site stage4_field.py:1386-1389."
  - "4.1 (2026-09-23) — post independent review (Kimi K3 max; KIMI_RECONCILIATION_KSHETRA_v1_0.md). CORRECTED an overclaim of my own: suppression is route-scoped only in layer1.project_layer1, a projection; the stored field and its null both evaluate through FieldEvaluator.terms_at with every active obstruction (G3) — now rank 0. BPHS Ch.29 struck (corpus Ch.29 = Bhāva Padas; inherited from W0 §5:207). mi_bhara path made full. PK-P4 defined. Ablation → three arms + rubric + judge. P1 contract pins tolerance and grid. U11 fields extended. Q07 proof row reworded (attenuation)."
  - "4.0 (2026-09-23) — ecosystem review. ADDED: the declared-vs-actual edge register (both directions, verified); L5's unordered LIMIT 1 snapshot bind; Kshetra's internal re-derivation of vedha/moorti while the layer's accepted assets go unread, and the AV-gate / lattā not_in_corpus gaps; three unlisted consumers. CORRECTED: 'sandhi has no term' (it is covariate x9, derived from own S3 boundaries, not L1 sandhi_flag). REFUTED a sibling session's 'provenance has no detector' — assert_provenance_reconciles fires before write (window-peak scope). Umbrella plan: KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md."
  - "3.0 (2026-09-22) — re-packeted BY STAGE per ELEVATION_PROMPT_KSHETRA_v2 / template v2.0; value proposition re-framed on the Interval/trajectory-segment object (Q06 primary); latent-value register, P1/P2/P6 contracts, U11 packet, synergy seams, consumer walkthrough added; register delta on null_resolution filed."
  - "2.0 — contract §1-§8 shape; three v1.0 findings withdrawn (Appendix B)."
  - "1.0 — first authorship, written without the W0 tier."
---

# `ka_kshetra` — elevation brief (stages 0–2, staged-internal-DAG shape)

**Paths.** Bare filenames resolve under `platform/python-sidecar/services/ka_kshetra/` (no repo-root
`services/` exists); bare governance names under `00_ARCHITECTURE/briefs/nirmana/`.

**What it is for — before anything else.** VA §6.4: Kshetra contributes its search/temporal-
integration engineering as *"a mechanism-qualified candidate substrate, not … a universal authority."*
The Strategy §3 object it owns is the **Interval/trajectory segment** — *onset/peak/decay/
recurrence, boundaries, component witnesses, null/missing states, evaluation resolution/error
bounds, generation and horizon* — the only Kāla producer that gives a consumer a **shape over time**
rather than a window. That shape, with its four-term composition retained per segment, uniquely
serves **L3-Q06 — "how does this chapter differ from the preceding one?"** — and the shared knot
grid serves **L3-Q07** strongly. **L3-Q08** is where the null model earns or loses its keep. The
asset is not short of richness; **its richness is unqualified (85.7% synthetic baseline, unmarked
on the row), unreachable (no retrieval capability), and unpublished (no manifest).** The
elevation is qualification, reach and a complete generation — not more columns. §4 gives the
distinction, the baseline (Sangam's windows) and the ablation; if the ablation fails, the honest
disposition is park-with-preservation and P1 is never funded.

---

## §1 — Admission and exact authority

Header above. This brief implements **only** the §4 deltas and infers no authority from the layer
plan, existing code, W0 acceptance, a migration number or a test. **Holds obeyed, not argued:**
(1) **populated-chart replacement is held to W7** — `prepare:replace` raises `KshetraReplacementHeld`
before any DML when any owned table is populated (`writer.py:543-550`); *"preservation by refusal"*
(FOUNDATION_SAFETY §4.1); no rebuild trial on the canonical chart is proposed; (2) **the fifteen-
table stage plan is frozen** — `S0 + S2 → S3 → S1 → S4 → S5 → S6 → S6.5 → S8 → snapshot`, direct S0
also into S4 (§6 item 5) — and *is* the packet boundary; S0/S2's independent prerequisites *"do not
authorize changing the frozen scheduler's present serial behavior"*; (3) **no full-chart rebuild is
authorized by W0** (§8); (4) Q2/Q4/QX are closed gates — *"QX cannot be promoted by prose alone."*
**Not decided here:** the five open native decisions (guide §11).

---

## §2 — Current-state evidence (Stage 0 · Reconcile)

Labels per Layer contract §4. **The DB was unreachable from the authoring session
(`ECONNREFUSED 127.0.0.1:5433`); every row count is `historical_receipt` from Lane C.** Source
claims are `direct_source_read` at main @ c58e86662.

### 2.1 Already established — cited, not re-derived

| Record | Row | Delta since |
|---|---|---|
| Contribution register §5 | line 151: *typed stages, integration/search, provenance and uncertainty/selection machinery; preserve signed edges, complete lineage, occurrence/condition and qualified clock jurisdiction before expanding model authority* (DP06/07/08) | none |
| CURRENT_STATE §4.1 | line 142: *15-table field family; staged L0–L3 inputs; W0 disposition "P0 planning repair before any trial"* | **discharged** (`3f109869d`, ACCEPT) |
| CURRENT_STATE §3 | 10,966,448 `kala_field` rows / 5.62 GB: *"not accepted useful coverage or a rebuild warrant"* | none |
| Field register | **221 rows across 15 relations; 13 Q1, 2 QX** (`kala_field_routes`, `kala_field_boundaries`); fences 4, 6 | **three deltas — §2.3** |
| Strategy §6.1 row L3-A22; §5 P0/P1/P2/P6 | *"staged data system, not one opaque writer … apply P0/P1/P2/P6 before expensive rebuilds"* | P0 done |
| FOUNDATION_SAFETY §4.1, §5, §6 item 5, §8 | P0 accepted; W0 baseline; frozen plan; W7 packet named | none |
| DHARA numerical contract; DP-SD-019 | semantic 1.2, left-limit rule (+4.656% on the reference integral, Decimal-60 / 4,096-Simpson oracle); midpoint fix (oracle 1515 vs 300) | inherited as baseline |

### 2.2 The stages — what each is, what it holds today, what this brief does to it

| Stage | Relations · producer | Q | Canonical chart today (`historical_receipt`) | This brief's delta |
|---|---|---|---|---|
| **S0** kinematics | `kala_field_kinematics` · `stage0_kinematics.py` | Q1 | present; `computed_at` **after** the field it fed (2026-09-11 01:49 vs 09-10 19:40) — no `field_snapshot_id` column | none; ayanāṃśa coverage marker requested (§4.5) |
| **S2** promise/routes | `_promise_nodes`, `_promise_edges`, `_routes` · `stage2_promise.py` | Q1/Q1/**QX** | present | **name the signed→unsigned seam** (§4.4); routes QX gate cited |
| **S3** clocks/boundaries | `_clocks`, `_boundaries` · `stage3_clocks.py` + `uncertainty.py` | Q1/**QX** | present; **stage cannot run today** (§3 rank 2) | **replace the upward σ_T read; cite the ayanāṃśa-ambiguity gate** (§4.3) |
| **S1** primitives | `_primitives` · `stage1_symbolization.py` | Q1 | present | none |
| **S4** field | `kala_field` · `stage4_field.py`, `layer0/1.py`, `hazard.py`, `writer.py` | Q1 | 8,570,075 rows, 25 classes, 342,803 seg/class, `refinement_depth`=0 everywhere; all → dangling `kfs_1805…8e5f` | **thread `baseline_is_synthetic` to the row** (§3, §4.2) |
| **S5** null/windows/prov. | `_null`, `_windows`, `_provenance` · `stage5_null.py`, `dhara_null*.py`, `writer.py` | Q1 | 15 / 14 classes; 17,528 windows, **85.7% synthetic**; **pre-`87cc8c9baf` null output** | **null contract + denominator prose; register delta** (§4.3) |
| **S6** salience | `_salience` · `stage6_salience.py` | Q1 | **0 rows** | none (W7) |
| **S6.5** insights | `kala_insights` WHERE `lel_derived=false` · `stage65_insights.py` | Q1 | **0 rows** | none (W7); fence 4 |
| **S8** timeline | `kala_timeline_spec` · `stage8_spec.py` | Q1 | **0 rows** | none (W7); its `expected_count` suppression (`:136`) is the precedent §4.2 cites |
| **snapshot** | `kala_field_snapshots` · `writer.py` | Q1 | **0 rows — unpublished** | P6 contract (§4.6); publication is W7 |

The other chart (`1c826d5a`) holds a **complete, calibrated, published 6-class run** through
snapshot. **Two configurations, not two runs.**

### 2.3 Register deltas filed by this brief

1. **`kala_field_windows.null_resolution` (row 488) declares `1/(R+1)`. Stale.** The writer binds
   `null_result.resolution` = **1/R** (`writer.py:1001`; `contracts.py:250-257`, the F-01 correction).
   `S5.null_resolution()` still returns `1/(R+1)` (`stage5_null.py:144-146`) — **no live caller found
   within scope `services/ka_kshetra/*.py`**. The prompt inherited the stale unit.
2. **Undeclared upward read** `stage3_clocks.py:1012 → phala_rectification` — REDIRECT_002 §3 files
   it; recorded here as the S3 packet's precondition.
3. **`kala_field.baseline_is_synthetic` is absent** from the 21 registered rows (§3).

### 2.4 Algorithm, identity, inputs, consumers, cost

**Algorithm.** `ln λ_e(t) = ln λ⁰_e + ln P̃_e + Σ w_s·A_s·r_{s,e}(t) + Σ β_j·x_j(t) + Σ ln(1 − ρ_m·u_m(t))`
(`layer1.py:22-30`, impl `:60-165`). λ⁰ is actuarial, **not classical**; the clock term is the only
classical operand. **Suppression: the documented contract is route-scoped (SM-R-7 Option B, `layer1.py:140-160`), but that filter lives in `layer1.project_layer1` — a projection. The stored field is built via `dhara_build_segments` → `evaluator.terms_at` (`dhara_sweep.py:43,55`), and `FieldEvaluator.terms_at` passes every active obstruction to `hazard.evaluate` (`stage4_field.py:866-873`); the null (`dhara_null.py:159-163`) does the same. Field and null are consistent — and chart-wide. v4.0's "route-scoped" was an overclaim (G3).** §N.3 delete-then-insert in
`prepare:replace`, `kala_insights` predicated `lel_derived = FALSE`.
**Identity.** `field_snapshot_id` is a **pin hash** (`stage4_field.py:186-212`) over chart, corpus,
weights, x-schema, cohort and `config_pin` — which includes `null_replicates`, `segment_engine` and
`dhara_sweep_semantic_version`. The §7.4 content hash lands separately in the manifest. **Pin
identity without content identity is what "unpublished" means.**
**Inputs — the edge register, declared vs actual (VERIFIED by `FROM`-census over
`services/ka_kshetra/*.py`).** Eight declared edges; ~30 tables actually read. The mismatch runs both
ways, the same defect class the Sangam delta flagged:
- **Declared, never read:** `bo_sangati` (→ `bodha_cdlm_cells`, 0 reads), `bo_upaya`
  (→ `bodha_rm_resonances`, 0 reads). `bg_class_lifetime_counts` has **no `target_table` in the
  seed**; the real read is `brahma_class_priors`, owned by `bg_class_priors` — the declared name is
  stale.
- **Read, never declared:** `bodha_msr_signals` (bo_vargottama_dhana), `bodha_cgm_nodes/_edges`
  (bo_bimba), `brahma_event_ontology` (bg_ghatana), `ephemeris_daily` (bg_ephemeris),
  `bg_transit_rules` (L0, vedha rules), `bg_kp_sublord_division`, `kala_gochara_authority`
  (migration 527, no seed owner), plus direct L1 `chart_facts`/`chart_dashas`/`charts`.
  (`gochara_resonance_map` is covered by declared `ka_gochara_resonance`; `ka_kshetra_tier_basis` is
  self-owned config.) An undeclared input cannot be scheduled, pinned or invalidated.
- **Read, forbidden:** `phala_rectification` (§4.3).
- **Read, protected:** `kala_gochara_windows` — the retired never-rebuildable sweep, as a read-only
  cross-check corpus; `generation` resolved from `kala_gochara_authority` with `'v1'` as COALESCE
  default at two sites (`writer.py:2330-2347`; `stage4_field.py:1386-1389`), so the corpus is authority-resolved, not hard-pinned — and its
  Clear-guard is Lane C's open F1.
`bg_sky_calendar`/`mi_bhara` deliberately non-edges. Cohort read under `try/except` **without
SAVEPOINT** (`writer.py:1754-1770`; correct pattern at `ka_sangam.py:997,1028,1033`).
**Classical assets of its own layer that Kshetra does NOT read (0 hits each):** `kala_vedha_gochara`,
`kala_moorti_nirnaya`, `kala_kota_chakra`, `kala_sudarshana`, `kala_tithi_pravesha`,
`kala_av_transit_gating`. It **re-derives** vedha (`build_vedha_primitive`, from `bg_transit_rules`)
and moorti (`build_moorti_primitive`, from its own ingress kinematics) internally, while the
`ka_vedha_gochara` (admitted chain: **L0 `bg_transit_rules` (`rule_type='favourable' AND vedha_house IS NOT NULL`, `services/ka_vedha_gochara/writer.py:100-101`), co-cited Phaladīpikā Ch.26 — the "BPHS Ch.29" half of that co-citation is a miscitation in the L0 data and in `logic.py:13,105` (Gochara F-23/G-8, L0 owner strikes it); sarvatobhadra from `bg_sarvatobhadra_grid`, lattā from `bg_phaladeepika_latta`, the malefic scale from `bg_vedha_malefic_scale` (Phaladīpikā PG353, ADJUDICATION-11). There is **no `bg_phaladeepika_vedha` relation** — that is a writer *filename*; earlier versions had named it as a table** — **not** "BPHS Ch.29", which in the corpus is Bhāva Padas; the phrase is inherited from FOUNDATION_SAFETY §5:207 and the L0 headers; 41 tests) and `ka_moorti_nirnaya` sit unread beside
it; `av_kaksha_gate` and `latta` are honest `not_in_corpus` gaps (`stage1_symbolization.py:346-362`).
**Two vedha verdicts and two moorti verdicts can exist in one layer for one instant** — a §N.5
authority split inside L3 and a VA §10.2 duplicate-evidence hazard the moment both reach synthesis.
**Consumers** (search bounded to `platform-mcp/src`, `platform/src`, `platform/python-sidecar` minus
`services/ka_kshetra/**` and tests). `resolveFieldSnapshot` (`platform-mcp/src/lib/kala_envelope.ts:196`)
is one funnel for `elect.ts:1013`, `ahead.ts:2151`, `explain.ts:747`; `priority.ts` reads
`kala_field_salience`; `ahead_autofile.ts:283` runs a `kala_field_windows` overlap query;
`platform-mcp/src/lib/kala_ritual_resonance.ts` reads the field. **`mi_bhara` (L5, sealed) binds to
the field with `SELECT field_snapshot_id FROM kala_field WHERE chart_id = %s LIMIT 1` — no `ORDER BY`
(`platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py:403`)**: an unordered pick (§N.7 item 2) that on the canonical chart returns the
dangling, unpublished `kfs_1805…`; it also reads `DISTINCT event_class` and `max(replicates)`, and
**never reads `baseline_is_synthetic`** — a calibrated and a fabricated hazard are byte-identical to
L5. `services/mi_bhara/living_lel.py` files predictions against `kala_field_windows.window_id` and
publishes L5-owned `kala_field_skill`/`kala_field_gof`. `resolveFieldSnapshot` returns
`FIELD_NOT_YET_BUILT` for the canonical chart (textbook F06). Its comment at `:186-194` discloses a whitelist gap that is
**closed** (`route.ts:109,118,124,130`) — stale, the `ahead.ts:740` class. **No retrieval-registry
projection exists**: thirteen siblings each have a `query_*.ts` under
`platform/src/lib/retrieval/registry/layers/L3_kala/`; Kshetra has none.
**Cost.** **Never `estimated_seconds`** (F28). W0 baseline, with its boundary (*source-local, no-DB,
small fixture, Moshier, not full-chart*): null 0.31 s, prep/recovery 0.47 s, publication 6.99 s,
build 0.315 s median, five matched repeats on field hash `kfh_8fa468f9…`. `KALA_COST_PROFILE_v1_0.md`
has not landed. Full-chart: **one crashed run**, ~7.5 h from `computed_at` spans
(`worker_crash: OperationalError: the connection is lost`, 2026-09-11, `amjis_app`, 600 s idle
killer) — hypothesis, not reproduced.
**Live-path.** §3: live on every row. S3 upward read: **live and build-blocking** (stage 3 is
mandatory; builder lacks SELECT). SAVEPOINT: live when the cohort read raises (it does).
`ungraded_default` conductance: **no live assignment found within scope `stage2_promise.py`** (type
annotation only, `:113`).

---

## §3 — Failure or missing capability

**One falsifiable problem**, ranked first (skill §5: correctness defect invalidating consumer reads).

| Field | Content |
|---|---|
| **Observed** | `hazard.baseline_rate()` returns `(rate, baseline_is_synthetic)` and `hazard.py:150-155` asserts the tag is *"a queryable field on every downstream row."* `layer1.py:89` receives it as `lam0, _baseline_is_synthetic = …` and **discards it by underscore in the hot path that writes every field row**; `_KALA_FIELD_INSERT_SQL` (`writer.py:631-638`) has 21 columns and the tag is not one. |
| **Evidence** | `direct_source_read` main @ c58e86662: `hazard.py:139-170`, `layer1.py:89`, `writer.py:631-638`. `historical_receipt`: tag present on `kala_field_windows` only; 15,024/17,528 = 85.7% `true`. Register: 21 `kala_field` rows, none is the tag. |
| **Expected contract** | §N.8; §N.7 item 4; **F04** (computed fact ≠ structural prior), **F06** (`unqualified` is a state, not a default); Strategy §6.2 `kala_field` row. |
| **Defect class** | **Unqualified + detector mismatch** (lens 2.1 class **(d)** — available but unqualified). |
| **Impact** | Q06's distinction is *how* two chapters' activations differ in composition; with λ⁰ fabricated for 19 of 25 classes and unmarked, a consumer cannot tell whether an inter-chapter level difference is structure or an invented base rate. For Q08, *"λ is defined here and low"* is uninterpretable in absolute terms. **`null_p` is scale-invariant within class** (both sides scale with λ⁰), so within-class rank survives — **absolute `expected_count` does not.** |
| **Non-claim** | No user was misled (no capability reaches `kala_field`; `resolveFieldSnapshot` returns not-built); the synthetic baselines are not shown astrologically wrong; within-class rank invariance is **untested** (A1). |

**Rank 0, found by independent review and verified here — G3:** the stored field applies chart-wide suppression while the contract (and v4.0 of this brief) says route-scoped; field and null agree with each other and not with the contract (§2.4). Native ruling on which governs, then a byte-equality test field ≡ null ≡ projection before any `null_p` is served. **Ranked behind it, addressed by this brief:** (2) **S3 cannot run** — the upward read (§4.3);
(3) **S3/S2 QX gates** — ayanāṃśa-ambiguous `rows[0]` and reminted surrogate edge ids (§4.3, §4.4);
(4) **the edge register** (§2.4) — declared-never-read and read-never-declared, both directions;
(5) **L5's unordered snapshot bind** (§2.4) — an L3-U10 interface packet, not L3 code;
(6) **no reach** — U11 packet (§4.7). **Not addressed (W7):** the missing manifest.
**Refuted, for the record:** a sibling session reported the registry's *"every factor persisted as a
provenance edge that must reconstruct the value it explains"* has no detector. It has one —
`S4.assert_provenance_reconciles(edges, w.lambda_peak, …)` at `writer.py:954,1065`, tolerance
`1e-9`, asserted **before** any write (§5.4 RECONCILIATION INVARIANT, `contracts.py:120-132`).
Honest scope: it fires at **window peaks**, not at every segment.

---

## §4 — Semantic change and expected distinction (Stage 1 · Frame the value)

### 4.1 Value proposition — question, distinction, baseline, ablation

**Primary — L3-Q06** *"How does this chapter differ from the preceding one?"* Required distinction:
*"recurrence with changes in participants, conditions, clocks, relationships and uncertainty."*
Primary proof: *"matched mechanism identities across intervals; no universal narrative template."*
The trajectory segment answers it with data no window carries: two intervals at equal λ with
different `clock_term`/`modifier_term`/`suppression_term` composition **are** matched mechanism
identity across intervals, continuously, with onset/peak/decay shape (`temporal_shape`,
read-never-derived from `brahma_event_ontology`, `stage4_field.py:1178-1188`).
**Secondary — L3-Q07** *"which domains interact over time?"*: all classes share one knot grid
(342,803 identical segments per class), so cross-class simultaneity is exact and free. Q07's proof
— *destroy the structural bridge, keep coincident dates, the inference must disappear* — is native
here: routes come from the S2 promise graph, so removing an L2 bridge removes a route and its
clock-term relevance — but under noisy-OR over K routes it may **attenuate rather than remove**; the
proof row must assert disappearance, or declare attenuation a failure of the proof, not the asset.
**L3-Q08** *"is no window a real negative?"* — the null's test. The field is total (λ defined on
0…36,525 with no gaps) and `q_threshold` comes from the null; a class with no exceedance is a real
negative **only if `q_threshold` is meaningful**, and it is scale-invariant within class — so Q08 is
earnable *within* class today and *across* classes only once baselines are calibrated.
**Partial:** Q01 (the "why"). **Cannot:** Q10; **Q11** (Circularity Guard — `mi_bhara` owns
`lel_derived=true`); Q13 (Pūrṇa). **Q05:** must declare non-comparability (§4.5).

**Competent simpler baseline — Sangam's windows** (`kala_convergence`: `window_start/end`,
`convergence_score`, `mode`, `peak_date`, `orb_strength`, `confidence_*`, `tier_basis`,
`independent_current_count`). A window has an interval, a score and witnesses. It has **no shape
inside the interval, no per-term composition, no null, no totality outside found windows.**

**THE ABLATION (primary, Q06) — pre-registered.** Several adjacent-MD chapter pairs across calibrated
classes, **including one ordinary, undramatic period**. Ask *"what changed between these two
chapters?"* — **Arm A:** Sangam's windows. **Arm A′:** Sangam + Taranga's monthly waveform (the
stronger baseline — shape but no per-term composition and no null). **Arm B:** A′ plus the field's
segments and term composition. A **rubric keyed to Q06's own distinction text** ("recurrence with
changes in participants, conditions, clocks, relationships and uncertainty") and a **named judge**
(the native's to name), both fixed before any arm is read. **If Arm A′ conveys the *driver* change — which classical operand moved — and not merely which
witnesses, the segment earns nothing and the asset loses its unique claim** → park-with-preservation; P1 never funded. Supporting: **A1** within-class rank
invariance, 2 calibrated vs 12 synthetic classes (one aggregate query — λ⁰ is a multiplier, rank
*should* be invariant; never run); **A2** zero the clock term, regenerate the top-10 mechanism
sentence (unchanged ⇒ the only classical operand does no work); **A3** R=128 vs 1024 by `null_p`
rank — **a cost probe, never an equivalence proof** (replicates are in `config_pin`).

### 4.2 Latent-value register (lens 2.1) — four classes, four fixes

| Class | Field / computation | Fix |
|---|---|---|
| **(a) persisted, discarded by consumers** | the four term columns on 8.57M rows — `promise_term`, `clock_term_start`, `modifier_term_start`, `suppression_term_start`; `signed_obstruction_start` ∈ [−1,0] | a receiving operator (U11 packet, §4.7); A2 decides value; until then **`UNRESOLVED_USE`** |
| **(b) computed, discarded before persistence** | `baseline_is_synthetic` at `layer1.py:89` | **§4.2 delta** — thread to `kala_field` |
| **(c) genuine gap** | calibrated λ⁰ for 19 of 25 classes; the manifest; a retrieval capability | priors: the **Pūrṇa priors lane (PK-P4)** — `PURNA_KSHETRA_PLAN_v1_1.md` §2 P4, citation-backed per-class demographic sourcing on the protocol that ratified the six `ne_v01` rows; not Strategy §5's P4; manifest: W7; capability: U11 |
| **(d) available, unqualified** | `null_p`/`q_threshold` on synthetic classes (absolute); `kala_field_boundaries` σ_T (QX); `kala_field_routes` (QX) | §4.3 null contract; §4.3 σ_T; QX gates cited, **not promoted by prose** |

**Offensive question (VA §10.3):** the one missing comparison operator that would unlock a new
consumer capability is **segment-vs-segment mechanism diff** — same class, two intervals, per-term
delta — consumer `kala_story`/experience 4; basis: the four columns already exist; cost: a query;
test: A2.

**Delta 1 (S4).** `layer1.py:89` stops discarding the tag (`HazardTerms` carries it, `hazard.py:425`);
`_KALA_FIELD_INSERT_SQL` gains the column; one migration at `platform/migrations/1071+` (both
directories checked; `migrate.ts:834-835` reads them as one sequence). **No new field invented.**
Serving-side suppression/relabel per consumer is **Pūrṇa P3-b's census**; the precedent to hand it
is `stage8_spec.py:136` (`expected_count: None if baseline_is_synthetic`).

### 4.3 S3 and S5 packets — σ_T, the QX gate, the null contract

**σ_T — replace, do not grant, do not merely guard.** Strategy §6.2 rules: *"Rectification and L5
weight inputs require separately admitted, purpose-compatible immutable artifacts. An earlier
timestamp does not make an event-derived rectification posterior admissible under the event-free
prospective contract."* REDIRECT_002 §3: *grant the three `bg_*`; hold the fourth; cite §6.2.* The
read selects `lel_fit_score` (`uncertainty.py:189-193`) — a fit to the Life Event Log — and σ_T
sets boundary uncertainty → window brackets → prospective forecasts: an **L3-U09 firewall breach
dressed as a privilege fix.** **Is birth-time uncertainty an L1 fact? Yes — of the birth *record*,
not of any inference about it.** σ_A already comes from L1 (`compute_sigma_a_degrees`,
`uncertainty.py:110-137`, *"a fixed, always-available L1 computation"*); σ_T is the same kind of
quantity, and `DEFAULT_SIGMA_T_DAYS` (`uncertainty.py:57`) is a wrapper-local constant shadowing a
value L1 should supply (§N.7 item 3). **Old:** unguarded SELECT; builder lacks SELECT; **the asset
cannot build.** **New:** consume an admitted immutable artifact where one exists; otherwise the
documented default with `sigma_t_source='default_120s_assumption'` and F06 **`unavailable`** —
`compute_sigma_t_days` already has that branch (`uncertainty.py:170-173`), and the robustness
dimension reads σ_T from the already-guarded `kala_field_boundaries` path (`writer.py:2231-2251`),
so nothing downstream regresses. **Target** (bounded L1 amendment, not authorized here): L1
declares birth-time precision. **Admitted-artifact source — decision for the native (§9).**

**The `_boundaries` QX gate is in the same chain.** Migration 1002:20-38: every `chart_dashas`
query in `stage3_clocks.py` except one omits `ayanamsha_id`; on the canonical chart the five
ayanāṃśa copies of Vimśottarī's earliest MD row **disagree on `lord_graha` (Moon vs Mars)** with
no tiebreak in `_system_sigma_t`'s `rows[0]` pick; the dedup key `(level_n, start_iso)` collapses
tied rows in up to 1,434 groups. **That is §N.7 item 2 (pin the key, total `ORDER BY`) inside the
σ_T function itself.** The S3 packet must close both: scope every `chart_dashas` read by
`DEFAULT_AYANAMSHA_ID` as the module's own `chart_facts` reads already do, and add the third sort
key. QX lifts only by the register's own gate, not by this prose.

**Null contract (S5).** Resolved from `dhara_null.py:6-45, 90-166`:
> Holding the natal structure and daśā ladder **fixed**, how often does a rigid **circular**
> re-phasing of the transit stream produce a window maximum at least this high?
`ln λ_r(t) = C(t) + E((t − δ_r) mod H)`; 1-day grid, n = 36,525; **only E is shifted** (`:28`); no
RNG; δ_r = r·H/R, r = 1…R−1; `coarse_mode=True` at ~819 knots. **Denominator R = 1024 = 1
observation + 1023 shifts** — `(1+exceed)/(len+1)`, `len = R−1` (`stage5_null.py:130-141`).
**Not** event probability; **not a test of the natal structure or the ladder** (held fixed); not
calibrated; binds to F04 and carries `tier_basis='relative_uncalibrated'`-style
**non-comparability** (Q05, F08). **Falsifiable:** a class dominated by `C(t)` gets no
discriminating power. **Prose defect (§N.7 item 5):** `dhara_null.py:39` writes `/(R+1)`, which
under `DEFAULT_REPLICATES=1024` reads 1025 — R is overloaded (1024 / 1023) across three files.
**Independent oracle:** the full circular group on a 1-day grid has exactly **36,525** elements; the
R-grid is a 1023-point subsample — so **exhaustively enumerate all integer-day shifts on a reduced
horizon** for a synthetic known-λ process, plus one closed-form sinusoid. Enumerates what the
estimator samples; never runs the estimator. **Pin for the native:** P1's *"full shift set"* must
mean the declared R-grid, not the 36,525-element group.

### 4.4 S2 packet — the seam where signed structure becomes unsigned conductance

`stage2_promise.py:457` normalizes L2 `computed_strength` into a conductance in (floor, 1];
`:351-355`: status and grade are *"MODIFIERS (scaling factors on conductance), never … binary
gates"* and *"'denied' rows produce low-conductance edges."* Routing is shortest-path over
`cost = −log(conductance)` (`:170`). **So an opposing or cancelling L2 relation becomes a longer
path, never a signed opposition.** This is exactly Strategy §6.2's *"restore complete signed
mechanism/cancellation semantics rather than unsigned grade"* and L3-U01's *"unsigned conductance
loses meaning."* The S2 packet's delta: carry the L2 sign and occurrence/condition on the edge and
route (`kala_field_routes.suppressed_by` already carries the *inhibiting* half for SM-R-7); the
`_routes` QX gate — `path_edge_ids` embeds a bigserial surrogate reassigned every rebuild
(migration 1002) — must be closed by a natural edge key **first**, or signed routes are
non-reproducible too. **Owner of the upstream half:** L3-U01 (L2→Yojaka/Kshetra).

### 4.5 Synergy (lens 2.4) — owes / receives, with F12 roles and the seams

| Direction | Edge (F12 role) | Distinction needed | Seam where it dies |
|---|---|---|---|
| **receives** | L2 `bodha_pratijna`/`bo_sangati`/`bo_upaya` → S2 (`computation`, `counterevidence`) | signed multidomain mechanism + cancellation | **§4.4** — sign → unsigned conductance |
| **receives** | L1 `chart_dashas` → S3 (`computation`) | hour grain + `sandhi` | `start_iso/end_iso` **survive** (`stage3_clocks.py:418-437`). Sandhi **is** a term — covariate x9 `sandhi_band` — but it is derived from Kshetra's **own** S3 boundaries (`stage1_symbolization.py:299-330`), never from L1's `sandhi_flag`: the two layers can disagree about where a sandhi is (§N.5). The null collapses to a **1-day grid**; windows declare `day_grade` |
| **receives (should, does not)** | `ka_vedha_gochara`, `ka_moorti_nirnaya`, `ganita_av_transit_gating`, `ka_kota_chakra`, `ka_sudarshana`, `ka_tithi_pravesha` → S1 covariates (`computation`, `applicability`) | source-qualified vedha; accepted moorti; AV kakṣā gate; kota/sudarshana/tithi applicability | **0 reads**; vedha and moorti re-derived internally; `av_kaksha_gate` and `latta` `not_in_corpus`. The layer's classical suite does not feed the field. |
| **owes** | `field_snapshot_id` → `mi_bhara` (`evaluation`, L3-U10) | a **published** snapshot, selected by manifest | L5 picks `LIMIT 1` unordered from `kala_field` (`mi_bhara.py:403`) and today binds to an unpublished id |
| **receives** | `ka_gochara_resonance` → S1/S4 (`computation`) | resonance targets | — |
| **receives** | `ephemeris_daily` (L0) → S0 (`computation`) | 9 daily bodies incl. Rāhu/Ketu at a **declared** node frame and epoch | **Store is TRUE-node at NOON-UT knots, Swiss-exact** — stored tropical Rāhu 73.629058 = Swiss TRUE at 1984-02-05 12:00 UT to 6 dp (verified in-session); `l0_ephemeris.py:77,290` use `swe_id 11` = `TRUE_NODE`. Yet migration 624:30 asserts `node_mode:"mean"` and the code comment says "mean North Node" — §N.8, a convention with no detector. L1 natal is mean, so S0 splines true-node knots against mean-node targets. Neither the node frame nor the noon-UT epoch is carried on the row. Scanner amendments do **not** land here (only `MEAN_MOTIONS`, `:746`). Dependency on the hub ruling |
| **receives** | legacy `kala_gochara_windows` → cross-check (`evaluation`, never `computation`) | *validation input, not a λ contributor* (`writer.py:2255`) | honest by design |
| **receives** | `kala_field_weight_versions/weights` (`computation`, **input owned outside**, fence 6) | pinned weights version | — |
| **owes** | `kala_timeline_spec`, `kala_field_snapshots` → experience 4 (`relevance_navigation`) | one selectable complete generation | **no manifest** |
| **owes** | `kala_field_salience` → `kala_priority_get` (`relevance_navigation`) | five-axis vector | S6 never ran |
| **owes** | `kala_insights` (`lel_derived=false`) → discovery (`interpretation`) | event-free insight | fence 4 |
| **owes** | `mi_bhara` (`evaluation`) | calibration loop across builds | pinned by weights version |
| **owes** | ayanāṃśa coverage marker on S0 → `ayanamsha_robust` | `None` below 2 ayanāṃśas (`stage5_null.py:606-624`) | if `weakest_link` is uniformly `ayanamsha_robust`, S0 is the cause |

**Typed qualification, no scalar invented.** `confidence_tier` is two-valued by design
(`contracts.py:219-227`; Circularity Guard); `weakest_link` names the failed dimension; each
detector returns `None` rather than passing. **Not the Sangam degenerate-label defect** — a symptom
whose distribution was never queried. DP07/DP08 present. Time: `t` is days-from-birth, so the
naive-into-`timestamptz` class does not arise in `kala_field`. **Knowledge-time (lens 2.6):**
event time = `t`; knowledge time = pinned upstream vector; publication time = manifest `built_at`;
rectification and L5 weights only as admitted artifacts; the field never rewrites issued claims.

### 4.6 P1 / P2 / P6 — each with its exact equivalence contract (lens 2.3)

Order fixed by Strategy §5: *repeated preparation, scalar inner loops, redundant searches and dense
storage BEFORE time resolution or method coverage.* **P0 is accepted — not re-proved.**

| Cand. | Avoidable work (Strategy §5) | Candidate | **Equivalence contract (verbatim) + identity method** |
|---|---|---|---|
| **P6 publication** — *first* | O(windows × legacy rows) cross-check; repeated presentation loads | interval-indexed matching; bounded streaming publication; one timeline payload; optional exact complement for divergence | *"Every agreement/counterexample remains recoverable; evidence interpretation is part of segment equivalence. No top-K deletion of contrary evidence."* Identity: §7.4 content hash equal pre/post on the fixture; complement set byte-equal. |
| **P2 shared context/sweep** | full-century preparation per class; repeated envelope/clock searches | immutable chart preparation; lightweight class projections; event/clock sweep; sparse obstruction support; direct segment reader | *"Same class/method meaning, numerical function, breakpoints, evidence roots and null scope. Suppressed/empty classes must remain explicit."* Identity: Layer0→Layer1 pointwise ≤1e-12 vs `terms_at()`; breakpoint set equal; field hash equal. |
| **P1 DHARA null** — *last, only after the §4.1 ablation passes* | ~372M sliding-window differences and ~37M heap visits per class | exact numeric slice maximum + exact blocked order-statistic reducer | *"Same finite-value policy, float64/rank/ties, full shift set, duration buckets and statistical denominator. Analyze midpoint origin separately before selecting the reference oracle."* **Plus, pinned here because they are semantics: `_EXCEEDANCE_REL_TOL = 1e-12` (`stage5_null.py:93`) and the grid construction `range(1, R)`, δ_r = r·H/R.** Reference: DHARA 1.2 + accepted midpoint fix; oracle §4.3. Identity: `max_stats[]`, `q_threshold`, `null_p` bit-equal per bucket. |

*"Fewer simulations, approximate quantiles or fewer years are not equivalent."* Why P6 first: the
pin rule makes publication the only order that preserves capital, and an unpublishable artefact
cannot pay back optimisation. **P1's ~4× cost is paid only if the segment earns Q06.**

### 4.7 Interface packet — L3-U11 `kala_field` retrieval capability (Pūrṇa implements; L3 owns the test)

The asset is **not** research-only; it owes a served shape. Packet, in L3-U11 form (*publish
material fields, exact access path, prerequisites, contexts, method/coverage and unknowns to the
existing capability authority*): **capability** `query_field_trajectory` under
`platform/src/lib/retrieval/registry/layers/L3_kala/`, modelled on `query_activation_waveform.ts`
(summary/drill modes, scope filters, bounded limit); **prerequisite** a manifest row
(`resolveFieldSnapshot` ≠ not-built); **material fields** per segment: `t_start/t_end`, `alpha`,
`gamma`, `lambda_start/end`, the four term columns, `signed_obstruction_start`,
**`baseline_is_synthetic`**, `field_snapshot_id`, **`weights_version`, `x_schema_version`**; per window: `t_peak`, `lambda_peak`, `null_p`,
`null_r`, `null_resolution` (**1/R**), `precision_regime`, `promise_state`, `weakest_link`;
**`density_contract`**: `paginated`, facets `event_class`/`baseline_is_synthetic`/`precision_regime`,
`empty_reason` ∈ {`not_built`, `class_skipped`, `synthetic_baseline_suppressed`};
**comparability flag** on every row. **Sentinel test (L3-owned):** a segment whose only
distinguishing value is a non-default `suppression_term_start` in a low-ranked class reaches the
allowed consumer and the saved result — absent ⇒ fail. Until this lands, Strategy §7 caps the
asset below `CONSUMER_INTEGRATED` regardless of data.

### 4.8 Consumer walkthrough (lens 2.5) — Product §9 experience 4, the temporal landscape

*"Distinguish enduring structure, active mechanisms, overlapping windows, recurrence and possible
manifestations. Move between a life chapter and a narrow interval without changing evidential
identity."* **Today:** the person asks why 2027 differs from 2024 for career; `kala_ahead_get`
reaches synthesis with Sangam windows and Darshana; `resolveFieldSnapshot` returns
`FIELD_NOT_YET_BUILT`; **nothing from the field reaches them.** **After elevation** (manifest +
U11): the same question returns two segment sets with term composition — *"the 2027 rise is
clock-term (Saturn AD on a route to `career`) with suppression inactive; 2024's equal-height peak
was modifier-driven"* — and the interval can be narrowed to the segment without changing
`field_snapshot_id`. **What they can now distinguish:** mechanism composition across chapters
(Q06). **Ordinary-period case:** a chapter with no exceedance — today silence; after: *"λ defined,
below `q_threshold` throughout; synthetic baseline; within-class rank only"* — an honest quiet, not
an absence. If the ablation shows Sangam already conveys the mechanism change, this walkthrough
collapses to internal plumbing and the brief says so.

---

## §5 — Preservation, migration, history and rollback

**Preserved kernels** (`PRESERVE`): the term decomposition; the SM-R-7 route-scoped suppression *contract* (`layer1.py`) — pending the G3 ruling on whether it, or the live chart-wide behaviour, governs; the
`brahma_class_priors` selection (`stage4_field.py:1155-1168` — four coordinates pinned, total
`ORDER BY`, `LIMIT 1`; **the pattern S3 must copy**); `temporal_shape` read-never-derived; the five
`None`-returning detectors; the frozen stage plan; DHARA 1.2 and the midpoint fix; the `lel_derived
= FALSE` predicate (`writer.py:2493-2496`) — **the cross-layer guard working; never widen**.
**Dispositions by stage:** S4 tag — `ENRICH_CORRECT`; S3 σ_T read — `QUALIFY_LIMIT`; S3 ayanāṃśa
scope + sort key — `ENRICH_CORRECT`; S2 sign/edge key — `INTEGRATE` (L3-U01 owns the upstream
half); S5 docstring — `ENRICH_CORRECT`; four term columns — `UNRESOLVED_USE`; weights tables —
inputs, untouched (fence 6); `build_substep_progress` — orchestrator's (fence 6).
**Protected classes:** retired sweep `generation='v1'`; issued claims/observations (F17, U10);
`kala_bhavishya` outcomes (L3-A21). **Cascade** (CURRENT_STATE §4.2, cited): MSR deletion reaches
five core L3 tables; Kshetra's cross-stage IDs are non-FK referrers; *"fifteen tables have no
database-enforced internal DAG, so deletion/reconstruction order and content-bound resume must be
proved explicitly."*
**Generation binding** (FOUNDATION_SAFETY §6 items 1–4): input generations pinned; empty partition
explicit; candidate ≠ selected head; rollback re-points a head. **If physical generations are
absent at execution (they are):** the pin vector remains the identity and this brief's deltas are
source-only. `DHARA_SWEEP_SEMANTIC_VERSION` sits in `config_pin`, so 1.1→1.2 already superseded
the existing snapshot id; `_RESUME_VERSION` (10; contract ≥9) **rejects pre-correction checkpoints**
— the 8,570,075 rows **cannot be resumed into**. No orchestrator change (F26, §N.2).
**Rollback.** One additive nullable column; drop it. No delivered reading depends on it. **Open:**
nothing verified prevents a late worker publishing over a newer accepted generation.

---

## §6 — Focused proof matrix

Fixture boundary for every row: the disposable small fixture of the W0 baseline (no production DB,
no person data). A planned test is not a pass (F23).

| Proof | Test | Detector that can return false |
|---|---|---|
| **Positive** | Shape-only class ⇒ every `kala_field` row `baseline_is_synthetic=true`; calibrated ⇒ `false`. S3 with no admitted artifact ⇒ `sigma_t_source='default_120s_assumption'`, state `unavailable`. | per-row assertion; state assertion |
| **Negative** | `baseline_rate` on a non-positive count **raises**; `shape_only=True` with a real prior rejected; S3 refuses a live L4 table as a σ_T source. | a test passing any of these must fail |
| **Relevant influence** | Flip one class calibrated↔shape-only: tag changes; λ, geometry, windows, `null_p` **byte-stable — invariant by construction** (λ⁰ is a constant multiplier; replicates, `q_threshold`, window bounds and maxima scale identically; `null_p` is a rank statistic). Scope `chart_dashas` by `DEFAULT_AYANAMSHA_ID`: on a fixture whose five copies disagree on `lord_graha`, `_system_sigma_t` selects the pinned one. | invariant diff; lord assertion |
| **Irrelevant control** | Class/dict/segment order cannot change any tag or value; field hash `kfh_…` equal. | hash compare |
| **Duplication/correlation** | Row tag equals class-context tag on every row (single source at `baseline_rate`); a promise edge represented twice does not lower path cost twice. | disagreement ⇒ fail |
| **Context/missingness** | σ_T `applied` / `unavailable` / fabricated-zero are three distinct states; `null_p=None` when no replicates; `ayanamsha_robust=None` below 2 ayanāṃśas. | state assertions |
| **Boundary/precision** | DHARA 1.2 endpoints at internal knots and terminal `H`; tolerances `5e-13` / `0.003` day / `0.3%` / `0.5%` vs the Decimal-60 / 4,096-Simpson reference; closed forms `11/40`, `5/9`, `5/24`. Null oracle: exhaustive 36,525-shift enumeration on a short horizon matches the R-grid estimator's exceedance ordering. | accepted reference; enumeration |
| **Delivery** | **U11 sentinel** (§4.7): non-default `suppression_term_start` in a low-ranked class reaches consumer and saved result. L3 owns the test; Pūrṇa the code. | sentinel absent ⇒ fail |
| **Revision** | Changing `DHARA_SWEEP_SEMANTIC_VERSION` or `null_replicates` mints a new id and **rejects** stale resume (`writer.py:2456`); prior snapshot preserved. | resume returns `None` |
| **Value** | §4.1 ablation vs Sangam's windows, same subject/question/horizon/budget. | Arm A conveys the mechanism change ⇒ **asset fails to earn Q06** |
| **Evaluation** | `not_applicable` — not separately governed. | — |

Cheap diagnostics to run **before** any design conclusion: `weakest_link` distribution; **A1**.
Verdict tiers (F24): all rows `COMPUTATIONAL_CORRECTNESS` except Value = `EXPLANATORY_DISCRIMINATIVE_VALUE`;
`EMPIRICAL_OUTCOME_PERFORMANCE` not claimed.

---

## §7 — Implementation and review discipline

One writer surface: the execution task's isolated worktree; foreign worktrees preserved. Frozen
orchestrator/transaction/§N.3 contracts obeyed — **STOP and raise if a delta seems to need a
contract change** (§N.2). Migrations at `platform/migrations/1071+` after checking both directories
and reserving the number in `origin/campaign-coordination`; never touch `supabase/1035–1036`.
Absence of authority is `NOT_RUN`. **Independent review is unassigned; the packet is incomplete
without it** (contract §7). Green CI, a PR or a row count is not terminal proof.

## §8 — Terminal evidence packet (what execution would return)

1. approved brief/authority + upstream pin; 2. commits and changed files/tables/migrations;
3. old/new examples — a row that can and cannot declare its baseline; a boundary with its
`sigma_t_source`; 4. preservation/generation/rollback evidence; 5. raw commands and results per §6
row; 6. reviewer identity, findings, re-check; 7. **state reached — `PRODUCER_READY`; unreached —
`DATA_ACCEPTED` … `EMPIRICALLY_EVALUATED`**; 8. runtime/deploy/data evidence only if separately
authorized — none is; 9. residuals returned to the strategic parent (§9–§10); 10. protected
surfaces untouched; W7 unauthorized.

---

## §9 — Disposition, and the five decisions for the native

**Disposition: `ENRICH_CORRECT` + `QUALIFY_LIMIT` at source, packeted by stage (S4, S3, S2, S5).
No populated-chart build. Terminal state `PRODUCER_READY`; campaign `ANALYZED`.**

| Decision | Recommendation — on the value proposition, not sunk cost |
|---|---|
| **Product configuration: 6-class calibrated or 25-class incomplete?** | **The 6-class calibrated run is the product** until PK-P4 ratifies more priors. It needs no §N.8 waiver; it is a *demonstrated* path (the other chart's published manifest); four of its six classes are in the eleven the crashed run never reached. The 25-class run is substrate for P3, not a product. |
| **Complete, re-scope, or park?** | **Re-scope, at W7.** *Completing* the existing rows is unavailable: resume ≥9 rejects them, DHARA 1.2 superseded their id, and their null layer is **pre-`87cc8c9baf` output under an accepted HIGH finding** (*"could corrupt null maxima, thresholds and p-values"*). **Park-with-preservation is already in force** (`KshetraReplacementHeld`) and needs no act. A complete generation is built fresh under the corrected contract at `L3-W7-KSHETRA-COHERENT-PUBLICATION-01`. |
| **Serving capability's shape** | §4.7 — `query_field_trajectory`, summary/drill, faceted on class / synthetic / precision regime, comparability flag, sentinel test L3-owned. |
| **Admitted-artifact source for σ_T** | **L1 birth-time precision** (bounded upstream amendment), with `default_120s_assumption` + F06 `unavailable` as interim. A rectification posterior is admissible only as a separately admitted, event-free-qualified immutable artifact — and the brief does not see how an LEL-fitted posterior could qualify as event-free. |
| **P1 / P2 / P6 order** | **P6 → P2 → P1**, with the §4.1 ablation gating P1. |

**Non-claims.** Strategy §7: *"It cannot earn full completion solely by returning unavailable
states."* `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` have no admissible event type (native decision 2);
`VALUE_EVALUATED` is `N` for every L3-Q. **Q1 — is the continuous-field abstraction worth
preserving — is decided by the ablation, not by this brief and not by 8.57M rows existing.**

## §10 — Not settled

1. Q1 (the ablation). 2. `weakest_link` distribution; A1 — two aggregate queries, never run.
3. `refinement_depth=0` everywhere — dormant vs disabled; trigger unread; `UNRESOLVED_USE`.
4. Late-worker publication protection. 5. 25 vs 27 classes — set discovered per chart from
`bodha_pratijna` (`writer.py:2395-2400`); one query; not asserted. 6. The crash cause —
unreproduced. 7. `kala_envelope.ts:186-194` stale comment (Pūrṇa-owned). 8. Every live figure is
Lane C's; DB unreachable. 9. Owners unassigned. 10. P0's Bhavishya half — outside this asset.

---

## Appendix A — Lenses A–J

**A Identity/intent.** L3-A22; staged fifteen-table system; owns the Interval/trajectory segment;
Q06 unique, Q07 strong, Q08 via the null; cannot Q10/Q11/Q13.
**B Inputs/DAG/lineage.** Eight declared edges + one undeclared upward read; frozen stage plan;
two QX gates on identity (surrogate edge ids; ayanāṃśa-ambiguous boundary selection).
**C Correctness.** §3; both QX defects; the S2 sign seam; the S3 `sandhi` gap. Against VA §10.2 the
asset is otherwise unusually clean — no favourable default (`baseline_rate` *raises*), no
first-domain-only, no polarity-erasing aggregation. **Arithmetic honesty exceeds publication honesty.**
**D Data sufficiency.** §4.2 register. 19 of 25 priors are PK-P4's lane.
**E Consumers/duplication.** Four MCP consumers via one funnel; zero registry projections; term
columns `UNRESOLVED_USE`.
**F Product readiness.** Blocked on publication + reach, not volume; no scalar invented.
**G Build efficiency.** §4.6. P0 done; P6 → P2 → P1; P1 only if Q06 is earned.
**H Reliability.** Missing SAVEPOINT; unreproduced crash; inherited rails (900 s idle bound,
two-substep stage-5 commits).
**I Change/release.** One additive migration; source-only otherwise; `release_authority: NONE`.
**J Final evidence.** §6; reviewer unassigned; `PRODUCER_READY`.

## Appendix B — Corrections register (v1.0 → v3.0)

- **WITHDRAWN** (v1.0) *"the 8.57M rows are deleted by the next pin-changing run"* —
  `KshetraReplacementHeld` raises first (`writer.py:543-550`); a reading error (window opened one
  line below the guard). **WITHDRAWN** *"a correction to Strategy §5's P0 row"* — accepted W0 work
  (`3f109869d`). **WITHDRAWN** *"resume to completion is mechanically supported"* — false under
  DHARA 1.2 / resume ≥9.
- **RE-FRAMED** (v2.0→3.0) the unique question from Q08 to **Q06**: the object owned is the
  trajectory segment, and shape-with-composition across chapters is what no window carries; Q08
  is the null's test, earnable within class only. **CORRECTED** the consumer picture (four via one
  funnel; whitelist closed) and the benchmark target (W0 baseline exists). **FILED** the
  `null_resolution` register delta — the register and the prompt both carry the pre-F-01 `1/(R+1)`.
- **NEW** the stored null layer is pre-fix under an accepted HIGH finding; `_system_sigma_t`'s
  ayanāṃśa-ambiguous `rows[0]` sits in the same chain as the inadmissible read.
