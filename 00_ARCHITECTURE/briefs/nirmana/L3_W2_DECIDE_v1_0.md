---
artifact: L3_W2_DECIDE_v1_0.md
canonical_id: NIRMANA_L3_W2_DECIDE
version: "1.0"
status: DECIDED — 23/23 routed, every finding triaged; acceptance events HELD on #1715
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3 — Kāla
definition_revision: t0-2026-09-01-0e5b06fb
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
inputs: [L3_W1_ANALYSIS_INDEX_v1_0.md, L3_W1_ANALYSIS_BATCH_A..E.md]
authorized_by: >
  Delegated authority per SESSION_CHARTER_V21.md C3 (decide yourself, log one line). Every route
  and triage below is this session's decision; none was referred to a human. Cross-layer and
  shared-surface questions went to the Conductor as adjudication issues and are cited inline.
---

# L3 KĀLA — W2 DECIDE

## §0 — Route semantics as L3 applies them

The plan's route vocabulary is shared across layers, so L3 states its reading once rather than
leaving it implicit. The discriminator is **the frozen manifest's `execution_obligation` first, then
whether the asset's own writer output changes**:

- The manifest's `execution_obligation` is frozen and binds: `probe` (4 assets),
  `retired_with_disposition` (1), `build` (18). A route may not contradict it.
- Among `build` assets: **`changed`** = the writer or its registry contract changes such that output
  content changes (`output_contract: correctness_change`). **`rebuild_only`** = no writer change;
  the rebuild earns freshness and an accepted-execution receipt (`digest_identical`).
  **`verified_reuse`** = not even that, on a full lineage proof.
- **A serving-plane fix does not by itself make an asset `changed`.** Several of L3's most serious
  defects live in TypeScript that reads the table, not in the writer that fills it. Those are W3
  work with no rebuild attached, and inflating the route to advertise them would misreport what the
  build actually did.
- Registry metadata (integrity contract, volume formula, floor) is added to **every** asset and does
  not on its own move a route, because it does not change output content.

## §1 — The routes (23/23)

| # | asset | obligation | **route** | verdict | why, in one line |
|---|---|---|---|---|---|
| 1 | `ka_gochara_resonance` | build | **rebuild_only** | examined_and_already_efficient | writer sound; its defects are registry metadata and five undeclared DAG edges |
| 2 | `ka_gochara` | build | **changed** | correct | `count_sql` counts 943 gen-3.0 rows its writer never wrote (writer targets v2/gen 2.0 = 83) |
| 3 | `ka_gochara_sweep` | retired_with_disposition | **retired** | non_build_disposition | v1 archive; snapshot-only; **never dispatched** — its `@register` was removed at retirement |
| 4 | `ka_gochara_v3_century_materialize` | build | **changed** | correct | hardcoded `BIRTH_JD`/`BIRTH_YEAR = 1984` materialised Abhinandan 13 months before he was born |
| 5 | `ka_kota_chakra` | build | **rebuild_only** | examined_and_already_efficient | writer correct; the defects are serving pagination + an unwired mechanism; horizon has burned 82/461 days |
| 6 | `ka_moorti_nirnaya` | build | **rebuild_only** | examined_and_already_efficient | same shape as kota |
| 7 | `ka_vedha_gochara` | build | **rebuild_only** | examined_and_already_efficient | the one genuinely consumed overlay; its defect is an uncited-flag drop in `context.py`, not the writer |
| 8 | `ka_sudarshana_varsha` | build | **rebuild_only** | examined_and_already_efficient | writer correct; zero consumers — a wiring/disposition question, not a build one |
| 9 | `ka_tithi_pravesha` | build | **verified_reuse** | examined_and_already_efficient | best-built asset in the layer; `two_pass_verified` has a real detector, 240/240 earned |
| 10 | `ka_kshetra` | build | **changed** | optimize_and_correct | genuinely incomplete on the canonical chart; `stage8` burns 1,224 s for 6 rows nothing reads |
| 11 | `ka_avadhi` | build | **changed** | correct | `lord_condition_fact_refs` empty on **100.00%** of rows — writer queries `'Sun'`, L1 stores `'SUN'` |
| 12 | `ka_taranga` | build | **changed** | correct | SPLIT verdict (§3): domain half is a real witness, event_class half is degenerate |
| 13 | `ka_yojaka` | build | **changed** | correct | 9,347 undatable predicates with only 20 carrying `always_on_reason`; 0.4% reach the engine |
| 14 | `ka_sangam` | build | **changed** | optimize_and_correct | carries the Temporal Concordance arbiter; 0.380 of its 1.000 weight budget is measurably dead |
| 15 | `ka_vighnakara` | build | **changed** | correct | obstruction computed then structurally discarded (max override 0.221 vs Mode-C ≥ 0.70) |
| 16 | `ka_kalasutra` | build | **rebuild_only** | examined_and_already_efficient | honest and non-accreting; its defects are a stale estimate and serving-side NULL ranking |
| 17 | `ka_kala_darshana` | build | **changed** | correct | `conv_score or 0.5` — the §N.7 item-6 computed-zero defect verbatim |
| 18 | `ka_jivana_parva` | build | **changed** | correct | mixes MD/AD/PD with no level column; 100 rows against a registry note of "typically 9" |
| 19 | `ka_bhavishya_lekha` | build | **changed** | correct | all 100 projections share one `peak_date`, one score, one tier; narrates calibration over an uncalibrated substrate |
| 20 | `ka_graha_sancara` | probe | **changed** | correct | *(route corrected 2026-09-05 per the Conductor's ruling on #1734, which upheld the diagnosis and ruled `changed`, not `probe`.)* I had routed it `probe` on the reasoning that the frozen `execution_obligation` binds. Both are true and they are different vocabularies: the **route** is `changed` because real code must change before anything about this asset can be accepted, while its **terminal evidence** is still `probe_accepted` per the frozen obligation. Routing it `probe` understated that the work is a code fix, not a re-run |
| 21 | `ka_muhurta_seva` | probe | **probe** | correct | healthy; its declared edge is fictional and its only consumer gets 0.0 on 1128/1128 rows |
| 22 | `ka_dasha_kala` | probe | **probe** | examined_and_already_efficient | sound, real consumers, best L1 drill path; serving default `ayanamsha_id='lahiri'` returns 0 rows |
| 23 | `ka_tulana` | probe | **probe** | correct | self-test ranks two synthetic objects where all four factors favour A — it cannot fail |

**Distribution:** `changed` **12** · `rebuild_only` 6 · `probe` **3** · `verified_reuse` 1 · `retired` 1.
*(Was 11/6/4/1/1 before `ka_graha_sancara` was re-routed `probe → changed` per the #1734 ruling.)*

**No asset is routed `rebuild_only` merely to look cheap, and none is routed `changed` merely to
look thorough.** The eleven `changed` assets each have a named correctness defect with a measured
blast radius. Note in particular what is *not* routed `changed`: the four overlays whose real
problem is that nothing consumes them, because a rebuild does not fix a missing pipe.

## §2 — Triage

### MUST — correctness; gates the capsule

| id | finding | asset(s) | doctrine |
|---|---|---|---|
| **M1** | Reconcile declared `depends_on` against every writer's actual reads, then supersede. L3's DAG is wrong in both directions; the E-gate cannot mean anything until it is right. | all 23 | C2, §N.5 · **#1734** |
| **M2** | Author 19 chart-partitioned integrity contracts. `integrity_verified` is mandatory on every route and cannot run today. | 19 | **D-CND-03**, C12 |
| **M3** | `ka_graha_sancara`: positional `row[0]` against a `dict_row` connection (`KeyError: 0`), and a self-test asserting a natal Moon sign against a 12:00-UT ephemeris that cannot produce it for a 10:43 birth. | 1 | §N.8, C12 |
| **M4** | `ka_avadhi`: `fact_subject='Sun'` vs L1's `'SUN'` ⇒ `lord_condition_fact_refs` empty on 100.00% of 1,169 rows, served as an empty array, unflagged. 5 of its 7 `fact_key` values do not exist in `chart_facts`. | 1 | §N.5, §N.7.6 |
| **M5** | Century materializer hardcodes `BIRTH_YEAR = 1984`; Abhinandan (b. 1985-03-02) was materialised from 1984-02-05. | 1 | B.10, §N.5 |
| **M6** | `ka_gochara`'s `count_sql` counts 943 rows produced by a different writer. Cockpit truth. | 1 | §N.4 cockpit-truth, §N.8 |
| **M7** | `kala_now_get`'s overlay fields are page-truncated at 50 with no cursor, and the emitted sentence asserts a **classical absence** where the cause is **pagination**. Measured: kota 4/9 current rows reachable (Saturn-in-durgantara excluded), vedha **0/1**. | serving | §N.8, §N.7.4 |
| **M8** | `kala_ritual_resonance.ts:491` returns `not_computed` with reason *"field empty, ka_kshetra has written no rows"* while `kala_field_windows` holds 31,350 live rows. A production test asserts the field is never dispatched. | serving | §N.8 (inverted) |
| **M9** | `kala_darshana`'s `conv_score or 0.5` substitutes a favourable-sounding default for a computed zero. | 1 | §N.7.6 |
| **M10** | `ka_bhavishya_lekha` narrates *"High probability (≥70% convergence)"* and *"probabilistic and calibrated"* over a substrate stamped `tier_basis='relative_uncalibrated'` on 100% of rows. | 1 | §N.7.4/6, Ethical Framework |
| **M11** | `service_health` is written and never read as a gate; `ka_graha_sancara` is `state='lit'` **while** unhealthy — its writer computes the status and discards the variable. One 6-line fix, three sites. | 4 services | §N.8, C12 |
| **M12** | 54 orphan gen-3.0 rows with NULL `era_slice_key` can never be removed by the era-scoped DELETE — permanent cross-build accretion. | 1 | §N.3 |

M7, M8, M9, M10 and M11 are one family: **a signal asserting a state that no code path could ever
make it report correctly.** That is §N.8's defect class, and L3 has five independent instances of it.
Finding five in one layer is itself the finding.

### NOW — admitted in-layer improvement

| id | item | why admitted |
|---|---|---|
| **N1** | **The Temporal Concordance Contract** — engine question-declarations; the arbiter on `kala_explain`/`kala_now` emitting `aligned \| partially_aligned \| disputed(adjudicated_by)`; authority profiles generalised from the two seed tables; per-engine testimony as drill. | the layer's mandate, and W1 proved it is an extension of `ka_sangam` (≈60% built), not a new build |
| **N2** | **Score commensurability** across the four `convergence_score` modes. | strict precondition for N1: a verdict comparing incommensurable scales is theatre. Measured: top-200 = 200/200 Mode C |
| **N3** | Wire the four inert overlays into `ClassContext`, **or** record explicit dispositions. | D-SERVICE built-but-unplugged; the mandate asked specifically for consumed-vs-shelf |
| **N4** | Recover `ka_sangam`'s 0.380 dead weight budget (6 terms, each root-caused). | last-cheap-chance: these are one-line lookups and vocabulary mismatches, and every downstream verdict inherits the error |
| **N5** | Correct `ka_muhurta_seva`'s fictional `depends_on` (real edge `bg_panchanga`, frozen) and its `event='general'` swallow (`c_panchanga_quality` = 0.0 on 1128/1128). | cheapest high-value item in the layer; unblocks the artifact spine's gate honestly |
| **N6** | Disposition the 8 Kāla `__ssv_*` tables: 7 drop-after-snapshot, 1 retain-as-evidence (`…gochara_windows__ssv_20260728c`, real reader + ADJUDICATION-6). 723.4 MiB reclaimable of 727.0. | mandate item (b); the retained one is retained on evidence, not sentiment |
| **N7** | Implement the `ka_taranga` SPLIT (§3). | mandate item (b) requires the decision made and logged either way |
| **N8** | `expected_volume_formula` + `expected_volume_inputs` + achieved-count `target_floor` for all 23. | D-CND-01; NULL is itself the defect |
| **N9** | `catalog_status: DRAFT → CURRENT` for **10 of L3's 11 DRAFT assets**. *(Corrected 2026-09-05: this line first said "the six artifact assets", which was an undercount — that was Batch E's six, not the layer's. Re-measured: **11 DRAFT = 7 artifact + 4 service**, matching L2's independent campaign-wide count on #1753.)* **`ka_graha_sancara` deliberately stays DRAFT** until M3 lands — flipping a service that is genuinely broken to CURRENT would be the unearned-signal move the whole campaign exists to remove. | D-SERVICE: a DRAFT asset real serving code depends on is a mislabel, not a status; but §N.8 forbids promoting one that is actually degraded |
| **N10** | WP-4 tuning: LPT ordering + width in `runner.py` (§3.5 scheduling constants only, logged), and delete `stage8` (1,224 s for 6 rows nothing reads, one substep already over the 600 s timeout). | measured hot spot is `stage5dhara` at 68%, not where anyone assumed |
| **N11** | Declare `density_contract` on the L3 capabilities (**none declares one**) and `hardFloor` the testimony section so a budget trim cannot zero a dissent. | §N.6 items 2 and 4 |
| **N12** | `kala_activation.orb_strength` / `convergence_score` are **99.6% NULL** while `query_temporal_activation` orders by `orb_strength DESC` and `judgment_query` picks its best row by `convergence_score`. `dasha_activation_proximity_score` is 0% NULL on the same rows. | the plan's own headline leverage question — a designed consumer reading NULL where the asset computed the answer |

### NEVER / LATER — logged with reason, closed

| id | item | disposition |
|---|---|---|
| **X1** | `ka_kshetra` / century substep chunk-parallelism | **Closed: impossible without a writer-contract change.** `asset_runner.py` drives substeps serially on the single orchestrator-owned connection; parallelism needs a second connection, forfeiting both frozen invariants (§N.2), and §3.5 grants nothing in `writers/`. WP-4's answer is LPT/width instead (N10). Not raised as a scope extension because the tuning path is sufficient and measured. |
| **X2** | Kota `graha <> 'Moon'` serving default (75% of the table is 1-day Moon rows) | shape preference, not a correctness defect |
| **X3** | `ON CONFLICT … DO NOTHING` after a full per-chart DELETE | correct today; would mask a genuine duplicate-run bug rather than raise it. Logged, not changed — changing it is a behaviour change with no present defect |
| **X4** | Re-key the gochara protection trigger on `(table, generation)` | **Adjudication, not an L3 decision** — it reverses something the native removed by instruction (migration 588), even though 588's own closing line proposes exactly this keying |
| **X5** | Undeclared backward **L3 → L4** read of `phala_rectification` (`uncertainty.py:191`) | layer inversion; **handed to L4**, not fixed here |
| **X6** | D-7: L4 consumption of `kala_tithi_pravesha` / `kala_sudarshana_varsha` | **verified negative** — no `ph_*` writer reads either. L4's item; recorded so it is not assumed proven |
| **X7** | Two-pass verification drives | P2 is PARKED by native ruling |
| **X8** | `ka_kshetra`'s `kala_timeline_spec` (zero consumers) | disposition recorded; no build change |

## §3 — The `ka_taranga` decision (mandate item (b), owed either way)

**Verdict: SPLIT, and it is not a derived view of `kala_field` — it never reads it.**

- The **`domain` half** (43,488 rows/chart) is a **genuine independent witness**: the only
  domain-keyed temporal engine anywhere in the system, 708 distinct transit values against 2 dasha
  values. It can informatively disagree with the field, which is the whole test. **Keep, and declare
  it as an engine in the concordance registry (N1).**
- The **`event_class` half** (48,924 rows/chart, 53% of the table) is a **degenerate duplicate** of
  `kala_field`'s own axis (25/25 class overlap) and *cannot* informatively disagree: its dasha term
  has **one distinct value across 48,924 rows** (a code tautology — `any(d in lord_domains for d in
  _GRAHA_DOMAINS[lord])` evaluated over the set it was derived from), its transit term is
  scope-blind (11 values), and its promise term is time-invariant, so the class ranking is frozen for
  151 years. **Retire this half.**

**What would falsify this verdict:** if the event_class half's dasha term ever produced more than one
distinct value on any chart, or if its ranking changed across the 151-year span, it would be a
witness and not a duplicate. Both are cheap to re-test and are written into the W3 item.

Two further measured facts fold into N7: 22.6% of `kala_taranga` rows are **pre-birth months**, and
`taranga_service.py` already computes this live at arbitrary `t` — the table is a cache, which is a
legitimate thing to be, but should be declared as one. **Standing hazard for W4:** two writers share
this table, and a batch rebuild silently destroys `record_evidence()` rows.

## §4 — Dispositions the mandate asked for, answered

| mandate item | decision |
|---|---|
| gochara v1 archive formally archival | **Route `retired`, never dispatched.** The corpus is 38,287 rows in the *live* table under `generation='v1'` (not a separate archive — the mandate's "17,240" was a mislabelled whole-table count). SNAPSHOT RULE ABSOLUTE stands. Residual carried: chart `cb73cd3d`'s 2,667 rows are outside the in-DB recovery path, and the only full recovery path is one git-ignored local dump. |
| v2/v3 authority confirmed | **v3 (`kala_gochara_windows_v2`, gen `g3_*`) is the serving authority.** `ka_gochara`'s own `count_sql` disagrees with its writer — that is M6, and it is the reason the authority looked ambiguous. |
| `kala_taranga` decided | **§3 above — SPLIT, with falsifiers stated.** |
| all Kāla `__ssv_*` dispositioned | **N6 — 8 tables, 7 drop-after-snapshot, 1 retain-as-evidence.** |
| quality overlays verified as consumed modulation | **Answered, and the answer is mostly no: 1 of 5 consumed** (`ka_vedha_gochara`). The other four are unreachable two layers deep — table built, mechanism written, `ClassContext` field absent. N3. |
| WP-4 heavy pass | **X1 + N10** — parallelism impossible, tuning measured and scoped. |

## §5 — What is held, and on what

| held | on | note |
|---|---|---|
| **`ka_gochara_resonance` + `ka_graha_sancara`** | **#1734 RULED — HELD** | the Conductor upheld the finding in full and ruled both held: *"Do not run a canary through a gate you have proved is not measuring anything. Report zero; that is the honest number and I am accepting it as the layer's status, not as a shortfall."* |
| **every L3 asset, until its `depends_on` is audited** | **D-CND-07** (standing, campaign-wide) | *"A green E-gate is a necessary condition for W4, never a sufficient one… Where it does not [match what the writer reads], or where it has not been checked, the asset is HELD regardless of what the gate says."* L3's full both-directions audit is in flight |
| every W2 **acceptance event** (23) | **#1715** (ruled; L1 authoring) | the routes above are *decided*; only the evidence writes wait. Per the ruling, writing them early would force re-acceptance |
| every W4 dispatch (23) | **#1730** / #1725 | the dispatcher enforces strict layer sequencing, not C2's gate |
| an honest gate canary | **#1734** | L3 has none until the DAG is reconciled; I will not manufacture one |
| the salience temporal multiplier (part of N1) | **L2 capabilities** (C6) | the rest of N1 is upstream-independent and proceeds |
| 15 assets' fingerprints | **PR #1728** (ruled, auto-merge armed) | record the SORTED fingerprint |

**Nothing in W3 is held.** M2 (19 contracts), M3–M12, N1–N12 are all upstream-independent, which is
why W3 opens immediately.

*End L3-W2. Next: W3 implementation, batched on disjoint write-sets.*
