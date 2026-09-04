---
artifact: L1_W2_DECIDE_v1_0.md
canonical_id: NIRMANA_L1_W2_DECIDE
version: 1.0
status: CURRENT
session: L1
layer: L1 — Gaṇita
wave: W2 DECIDE
produced_on: 2026-09-05
frozen_definition: t0-2026-09-01-0e5b06fb
chart: 482012f1-710e-4a25-994a-93821f5871aa
inputs: L1_W1_ANALYSIS_BATCH_A..E.md (139 findings, F-A1…F-E28)
---

# L1 (Gaṇita) — W2 DECIDE

One route per asset, every W1 finding triaged, per `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` §4/§6.2.
Evidence lives in the W1 batch files; this document decides.

**Nothing here is an acceptance event.** Per the Conductor's ruling on #1715, no L1
`asset_analysis_accepted` / `optimization_verdict_accepted` may be written until PR #1736 merges and
deploys. These are the decisions those events will carry.

## §1 — How routes were assigned

The route answers exactly one question: **does the rebuild need to run against changed writer code?**

- **`changed`** — a *writer* changes, so the build must run after the deploy.
- **`rebuild_only`** — the writer is unchanged; the rebuild re-establishes lineage and provenance.

Serving-layer fixes (`platform/src/lib/retrieval/**`, `platform-mcp/**`) and registry-field fixes do
**not** change the route, because neither alters what the writer produces. They land as their own W3
PRs. This distinction matters: five of L1's MUST findings are serving-side, and routing their assets
`changed` would have implied a writer change that does not exist — which would make the route a
worse description of reality, not a more cautious one.

`verified_reuse` was considered and **rejected for all 19**. It requires full digest lineage plus
proven integrity and consumers; L1 has **0 of 19** assets carrying `integrity_check_sql`, so the
integrity half cannot be evidenced for any of them today. Claiming reuse on assets whose integrity
detector does not exist would be exactly the unearned signal §N.8 forbids.

### Sequencing rule adopted (from #1744)

Registry-contract fields are inside the analysis fingerprint. Therefore **all registry corrections
land BEFORE that asset's W2 acceptance event**, or the accepted analysis immediately needs
re-acceptance under C2 condition 3. Order per asset: registry fix → W2 acceptance → (deploy if
`changed`) → W4 build.

`depends_on` is the exception: it is immutable for the rest of the campaign (#1744 — the frozen
definition can no longer be superseded, 174 events / 11 runs). Every DAG correction below is
therefore triaged **NEVER-LATER (documented)**, not because it is unimportant but because it is
unfixable inside this cohort. Named explicitly so the inaccuracy is on the record rather than
looking intentional.

## §2 — Routes

| # | asset | route | why |
|---|---|---|---|
| 1 | `ga_positions` | `rebuild_only` | Layer root, writer sound. Registry-only fixes (count_sql omits 315 owned rows; floor 50 vs achieved 1,205). **Layer canary.** |
| 2 | `ga_vargas` | **`changed`** | MUST F-A1 longitude computed 5h30m late; F-A2 unique index omits `fact_subject`; F-A3 idempotency delete coarser than insert (39% row loss). |
| 3 | `ga_dashas` | **`changed`** | MUST F-A10 both scope-cap sentinels fail silently; F-A12 dignity vocabulary disagreement with `ga_vargas`; F-A17 bare tier literals. |
| 4 | `ga_nakshatra` | `rebuild_only` | Writer sound. MUST F-B18 is serving-side (`ganita_nakshatra_get` serves the wrong asset). |
| 5 | `ga_panchanga` | **`changed`** | MUST F-B24 `*_arambha_iso` stores the anga's END, 5 emission sites. |
| 6 | `ga_sensitive` | `rebuild_only` | Deficit derived as floor-vintage mismatch, not a defect. Registry-only fixes. |
| 7 | `ga_sensitive_degree` | `rebuild_only` | Writer sound (emits 335). count_sql/floor/serving fixes only. |
| 8 | `ga_strength` | `rebuild_only` | Writer sound and honestly tiered. MUST F-C1 (ṣaḍbala selector) is **serving-side**. |
| 9 | `ga_structural` | `rebuild_only` | Writer sound. Owns the argala corpus; the defects are ownership-registry and downstream consumption. |
| 10 | `ga_condition` | **`changed`** | MUST F-C8 `varga_dignity_composite` NULL on 135/135 — two writer-side causes. |
| 11 | `ga_tajaka` | **`changed`** | MUST F-E16 `DEFAULT_REFERENCE_YEAR = 2026` is a frozen wall-clock literal; the window silently degrades yearly. |
| 12 | `ga_transit_anchors` | **`changed`** | F-D22 FORENSIC assertion contradicts a correct live value under one ayanamsha — resolve before rebuild (see §5). |
| 13 | `ga_medical` | **`changed`** | MUST F-E5 build-fatal gate justified by a false classical claim ("Sun debilitated in Capricorn"; Sun debilitates in Libra). |
| 14 | `ga_vastu` | **`changed`** | F-E12 hardcoded graha→direction dict shadowing the L0 `bg_vastu_directions` table (§N.7 item 3). |
| 15 | `ga_yoga` | `rebuild_only` | Writer sound; 63 firings with real citations. MUST F-D1/F-D2 are serving-side. |
| 16 | `ga_vichara` | `rebuild_only` | Real and mis-labeled; `catalog_status` DRAFT → CURRENT is a registry fix. |
| 17 | `ga_sade_sati` | `rebuild_only` | Deficit reconciles exactly; stale floor from a since-fixed writer. |
| 18 | `ga_ayurdaya` | `rebuild_only` | Writer sound. Floor + serving-projection fixes. |
| 19 | `ga_prashna` | `rebuild_only` + **DORMANT disposition** | R-1 stands: **do not open the facility.** Route is `rebuild_only` because the manifest obligation is `build` and a build legitimately produces 0 rows; the dormancy is recorded in the registry, not by changing the route (§4). |

**8 `changed` · 11 `rebuild_only` · 0 `verified_reuse`.**

## §3 — Findings triage

139 findings. Full evidence in the W1 batch files; the disposition is here.

### MUST — correctness; gates the capsule

| id(s) | asset | what | doctrine |
|---|---|---|---|
| F-A1 | ga_vargas | Graha longitudes computed 5h30m late; Lagna correct, so FORENSIC passes. 21.9% of varga sign rows disagree with `ga_positions`. **Independently re-verified by this session** (Lagna Δ 0.0000; Sun Δ 0.2324° and Moon Δ 2.7169° = the same 0.229 d). Cross-layer notice #1747. | §N.5, §B.10 |
| F-A2, F-A3 | ga_vargas | Unique index omits `fact_subject` (D30 lords 60 → 10); delete grain coarser than insert grain, 38,620 written vs 23,542 live, invisible because `_write_rows_batch` returns `len(rows)`. | §N.3, §N.8 |
| F-A10 | ga_dashas | Both scope-cap sentinels fail; the KP one on an undocumented CHECK violation. The function's "returns 0, 1, or 2" is always 0. | §N.8, §N.7 item 4 |
| F-A12 | ga_dashas + ga_vargas | Two L1 surfaces disagree on the same fact (Sun D1 dignity `Enemy` vs `neutral`), serving 28,923 rows. | §N.5 — halt-worthy, not a stored divergence |
| F-A4, F-B2, F-B12, F-C9 | positions, sensitive, sensitive_degree, structural | `count_sql` omits rows the writer writes **and the serving layer serves** (315 / 210 / 60 / ~5,157). Cockpit truth is wrong in four places. | §N.4 cockpit truth |
| F-A9, F-B1, F-D14, F-E1, F-E15 | dashas, sensitive, sade_sati, ayurdaya, tajaka | Floors wrong in five ways: encoding fabricated rows, vintage mismatch, achieved-by-a-defective-writer, unset (0), and a wall-clock-derived equality. Each re-baselined with a derivation, per C12. | C12, §N.4 |
| F-B24 | ga_panchanga | `*_arambha_iso` stores the anga's END. | §N.7 narration fidelity |
| F-C1 | ga_strength (serving) | Ṣaḍbala weakest-graha selector ranks across incommensurable units; wrong on 2 of 3 production charts. The 2026-07-28 fix and 2026-07-29 re-verification were both run on the only chart where it cannot manifest. | §N.7 item 2, §N.8 |
| F-C2, F-C3, F-C4, F-C5, F-C7 | structural, strength | The D-SALIENCE feed: argala unconsumed (NULL on 150,150), AV term degenerate (49,841/50,104 saturate), vargottama unconsumed with a units mismatch, cancellation modifiers **absent from L1 entirely**. | D-SALIENCE |
| F-C8 | ga_condition | `varga_dignity_composite` NULL on 135/135 rows, served and advertised. | §N.7 item 6 |
| F-C14 | CI guard | `check_fact_category_pinning.py` structurally cannot see the F-C1 defect class (its TS scanner only matches `.find(`/`.filter(`). | §N.8 |
| F-B18, F-B19 | ga_nakshatra (serving) | The tool named for the asset does not serve it; 995 rows have no named capability. | D-SERVICE |
| F-B26, F-B31 | ga_panchanga | Zero `two_pass_verified` on the 4 FORENSIC anchors it owns; floor 221 vs 437 with a formula evaluating to 5. | §N.8, C12 |
| F-D1, F-D2 | ga_yoga (serving) | Citations exist for 233/233 catalog rows but no surface joins them; `paginated: true` with no `offset` makes rows 51–63 unreachable. | D-GROUNDING, §N.6 |
| F-D9 | ga_vichara | `catalog_status = DRAFT` on an asset with 8,249 exact rows and 3 production consumers. | D-SERVICE |
| F-D21, F-D22, F-D23 | ga_transit_anchors | Acharya-floor primitive dispatches an argument no tool reads; FORENSIC assertion contradicts a correct value; zero data-plane consumers. | D-TIME, D-SERVICE |
| F-E5 | ga_medical | Build-fatal assertion justified by a false classical claim. | §B.10 |
| F-E10, F-E11 | ga_vastu | Zero routed consumers; L1's weakened directions and L0's 24 per-direction remedies are never joined. | D-SERVICE |
| F-E16, F-E17 | ga_tajaka | Frozen wall-clock literal; a `volume_explanation` describing on-demand computation that does not exist. | §N.8 |
| F-E21, F-E22 | ga_prashna | The dormant facility is live-mounted and has been used; 5 orphaned served rows with no regroundable chart. | B.3 |
| F-A14/A15, F-B35, F-C15, F-D28, F-E27 | all 19 | `integrity_check_sql` NULL on all 19; `expected_volume_inputs` NULL throughout; three volume formulas provably false. | C12, D-CND-01 |
| F-B32, F-B33 | cross | A coverage gate reading a hand-maintained 169-item list against 219 live categories; an alias file citing a CI check at a path that does not exist. | §N.8 |

### NOW — in-layer improvements admitted this wave

Floors and volume formulas re-baselined with derivations (F-A5, F-B13, F-D4, F-D10, F-E13);
`estimated_seconds` re-measured where stale by 3.7×–20× (F-A16, F-B22, F-C12, F-D12, F-E27);
`target_table` set where NULL (F-B4, F-D16); `density_contract` and `empty_reason` declared on the
capabilities lacking them (F-C21, F-D18, F-D25, F-E8, F-E28); serving projections widened to reach
already-computed data (F-A11 83,740 yogini rows, F-E2 `fact_value_jsonb`, F-B14 verification status);
total `ORDER BY` added where pagination is non-deterministic (F-D5, F-D11, F-D20, F-E19);
`fact_category_ownership` completed (F-C9, F-E4); dead materialised views dropped (F-B6).

### NEVER-LATER — logged with reason, closed

- **All DAG corrections** (F-A7, F-A13, F-B11, F-B15, F-B23, F-C18, F-C23, F-D3, F-D15, F-E7, F-E18)
  — `depends_on` is immutable for this cohort (#1744). Recorded as known-inaccurate; the one with
  live consequences (F-A13, the `ga_dashas`/`ga_vargas` MVCC race) is mitigated by **sequential
  single-asset dispatch** at W4 instead.
- **Verse-level grounding for yogas** (F-D7, F-D8) — `brahma_yoga_source_chunks` has 0 rows and 13
  citations point at text_ids absent from the corpus. L0-owned; chapter-level `sruti` is achievable
  now and is taken, verse-level is not.
- **P2 verification drive** (F-B26's deeper form, F-C19, F-C24) — parked by native ruling; the
  carve-out permits opportunistic normalisation only, and #1729 removed even that (§6).
- **`ga_prashna` build-out** (F-E26) — R-1: dormant by design. Deferred register only.
- Stale doc figures on live surfaces (F-A22, F-B17, F-C22, F-D29) — corrected in place where the
  file is already being touched, otherwise closed as cosmetic.

## §4 — `ga_prashna`: the R-1 dormant disposition (recorded, not opened)

**Native ruling R-1 stands: the horary facility stays dormant. Nothing here proposes opening it.**

What W1 established that the disposition must reflect:

1. **It is not merely unbuilt — the door is open and has been used.** `POST /api/compute/prashna/cast`
   is a mounted endpoint (`main.py:71`), two prashna charts were cast 2026-06-18, and
   `prashna_undertaking_get` is a deployed MCP tool reading `ga_prashna_judgment`. Dormancy is a
   decision, not a property of the code.
2. **Build cost is genuinely ~zero** (5 PK-indexed misses) and should not be "optimised" away — the
   writer's cheap no-op is what keeps the facility rebuildable.
3. **Two real costs**: five orphaned served rows for a chart with no rows in `chart_facts`/`charts`
   (a B.3 break with no FK behind it), and **no machine-readable record that R-1 exists** —
   `data_disposition` is NULL, though the column already carries a `dormant`-style vocabulary in use
   for `mi_sankalpa`.
4. **A naming collision that makes the dormancy unreadable from outside**: `prashna_ask` /
   `prashna_status` are the pariprashna NL pipeline and contain zero `ga_prashna` references, so "is
   horary open?" cannot be answered from the tool list.

**Decision:** record the disposition in the registry (`data_disposition`, plus a
`volume_explanation` naming R-1), re-ground or remove the 5 orphaned rows, and disambiguate the tool
naming. Go-live rehearsal goes to the deferred register (plan §7.3) with its 7 named prerequisites.
**No facility work.**

## §5 — Open questions carried into W3

1. **F-D22 (`ga_transit_anchors`)** — the writer's FORENSIC assertion demands Moon = Aquarius per
   ayanamsha, but the live `surya_siddhanta_classical` row correctly stores Pisces, and the real
   AQ/PI divergence is confirmed elsewhere in the batch. Either the assertion is wrong or it is
   dead. **Resolve before rebuilding**, and do not "fix" it by relaxing the assertion until which
   one is established — a weakened gate is hard-floor territory.
2. **F-C13** — `salience_formula_version` stores `'v1.0'` on 150,150 rows while the executing code
   is `salience_formula_v2`. Flagged by W1 as a lead, not a settled finding. L2's surface; raised
   there rather than assumed here.
3. **F-A3's full magnitude** — the 39% loss mechanism is proven by two exact instances; the
   per-category ledger needs write-path instrumentation and was out of scope for a read-only wave.
   The fix does not depend on the ledger.

## §6 — Scope explicitly NOT taken

- **Status-vocabulary normalisation** — the mandate invites it opportunistically. **Dropped**, not
  deferred: the Conductor's ruling on #1729 makes aliases resolve through `verification_vocab`, at
  which point which spelling a writer emits stops mattering and the cleanup has no purpose. Doing it
  *before* that fix would have demoted 10,316 rows 0.85 → 0.60 — a salience regression shipped as a
  cosmetic cleanup.
- **`bodha_writers/formulas.py`** — L2's write-set (C5). L1's contribution is the 13-member weight
  proposal on #1729.
- **Opening any parked-P2 verification work** beyond the carve-out.

## §7 — Capability deltas published (charter C6)

Announced in `L1_STATE.md` on `main`; consumers poll there.

| capability | consumers | status |
|---|---|---|
| Layer-generic analysis-receipt spine | L2, L3, L4, L5 (all evidence) | PR **#1736**, in review |
| **`chart_divisionals` longitude correction** — ~22% of varga sign assignments change on rebuild | L2, L3, L4 | notice **#1747**; lands with `ga_vargas` |
| **D-SALIENCE source-fact contract** — exact `fact_category` names, live counts and the units trap for argala (41,760 / 43,500), AV bindu+kakshya, vargottama (multiplier **not** increment), and the fact that **cancellation modifiers have no L1 source at all** | L2 (salience completion — the payoff-layer work) | published in `L1_W1_ANALYSIS_BATCH_C.md` §D-SALIENCE certification |
| `ga_condition.varga_dignity_composite` populated (currently NULL on 100% of rows) | L2 | lands with `ga_condition` |
| 19 L1 `integrity_check_sql` contracts under D-CND-03 | campaign verification | W3 |

**L1 consumes no new upstream capability.** L0 declared none, and #1723's detector guard (L4) is a
gate L1 must satisfy rather than a feature it consumes.

## §8 — What W1 found that should NOT change

Recorded because a wave that only reports defects is not reporting accurately.

- **`ga_strength` emits zero `two_pass_verified` and its docstring says exactly why** — honest tier
  over a broadcast claim (§N.4 S7 doctrine working as intended).
- **All three batch-C writers are FROZEN-contract conformant** — `conn.commit()` and telemetry gated
  on `owns_conn`, false on the orchestrator path (§N.2).
- **`get_strength.ts`'s `total` / `total_available` / `total_available_basis` triple** is the best
  density disclosure found anywhere in L1 (§N.6).
- **`ga_sade_sati` and `ga_transit_anchors` both correctly honour the real AQ/PI ayanamsha
  divergence** — a subtle thing to get right, and both do.
- **`prashna_undertaking_get` floors a missing verdict to `null` with a documented reason** — an
  exemplary §N.7 item 6 implementation (spoiled two lines later by a `?? 0`, which is the NOW fix).
- **`salience_inputs_complete = false` on 150,150/150,150 rows** — the system's own honest flag
  already said the salience feed was incomplete before this wave confirmed why.

*End L1_W2_DECIDE v1.0.*
