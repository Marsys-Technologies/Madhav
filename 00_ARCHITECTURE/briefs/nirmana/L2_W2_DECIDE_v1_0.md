---
canonical_id: L2_W2_DECIDE
version: 1.0
status: CURRENT
layer: L2 (Bodha)
session: L2
last_updated: 2026-09-05
basis: L2_W1_ANALYSIS_v1_0.md
rubric: NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §4 (W2 DECIDE)
charter: SESSION_CHARTER_V21.md v2.1
---

# L2-W2 DECIDE — 22 routes, 47 findings triaged

Plan §4: one route per asset; every finding triaged `MUST` (correctness — gates the capsule) /
`NOW` (in-layer improvement) / `NEVER-LATER` (logged with reason, closed); doctrine citation
required on every `NOW`. This document rules only — W3 implements.

---

## §1 — Route assignment (22/22)

L2 is unlike L0. L0's template was overwhelmingly `rebuild_only` because its writers were correct
and merely needed a re-run. **Nine L2 assets carry a correctness defect in their own writer**, so
`changed` is the majority route here — not from ambition, but because W1 found the defects.

| asset_id | route | rationale |
|---|---|---|
| `bo_laksana` | `changed` | A1/A2 AV units, A3 argala, A4 dead tag detectors, A6/A7/A8/A11, C1 corroboration fabrication. The layer's root and the source of most of them |
| `bo_karanajala` | `changed` | B7 (`cross_system_consensus_count` constant 1 on 849/849) + A13 (§N.5 — re-derives argala instead of reading L1) |
| `bo_samskara` | `changed` | reuse key is `signal_id`, so `bo_laksana`'s delete-then-insert forces 100% Vertex AI re-embedding. Re-key on `embedding_input_summary`. This is a **cost** fix, and the largest single one in the layer |
| `bo_samvada` | `changed` | B8 (`count_sql` cannot read false on writer failure), B9 (docstring names 8 phantom columns), and the D-SYNTHESIS rollups it owns |
| `bo_sudarshana` | `changed` | D5 (no percentile setter → NULL `salience_pctl_in_class`, excluded from the tail predicate) + C1 sibling |
| `bo_nakshatra_semantic` | `changed` | D5 + C1 sibling |
| `bo_arudha` | `changed` | D5 + C1 sibling |
| `bo_special_lagna` | `changed` | D5 + C1 sibling |
| `bo_vargottama_dhana` | `changed` | D5 + **A5** — hardcodes `vargottama_amplification=0.0` while smuggling the amplification through `class_prior=1.15`; the column misreports what the writer computed |
| `bo_laksana_rerank` | `rebuild_only` | its own logic is sound and salience-independent; it re-runs because `bo_laksana`'s rebuild deletes the rows it UPDATEs |
| `bo_bimba` | `rebuild_only` | writer sound; its defect (E1, `expected_volume_formula = ACTUAL(bo_laksana)`, wrong by 130×) is a **registry** correction, not a writer change |
| `bo_sangati` | `rebuild_only` | writer sound; E8 divergence (535 reported vs 280 live) investigated in W5, not pre-emptively "fixed" |
| `bo_drishti` | `rebuild_only` | — |
| `bo_anveshana` | `rebuild_only` | the writer is correct — it *does* emit the 125 `low_salience_high_consequence` rows. D1 is a **serving** defect, and the plug is TS-side |
| `bo_cgm_motifs` | `rebuild_only` | — |
| `bo_cgm_paths` | `rebuild_only` | — |
| `bo_chart_gestalt` | `rebuild_only` | writer sound; E6 (NULL `target_table`) is a registry correction |
| `bo_cdlm_summary` | `rebuild_only` | as above |
| `bo_pratijna` | `rebuild_only` | — |
| `bo_upaya` | `rebuild_only` | needs no change of its own: its `contradiction_factor` term turns itself on once B1 populates the column it already probes |
| `bo_pramana_mapa` | `rebuild_only` | **B10 — no work.** All six previously-unearned flags now have real detectors, proven by the stored `notes.n8_detectors` terms; the three remaining NULLs are correctly NULL |
| `bo_yantra_mechanism` | `rebuild_only` | — |

**No asset takes `verified_reuse`.** Every one of the 22 is `state='stale'` on the canonical chart
except two (E14), and the layer has never been rebuilt coherently as a unit — there is no build
evidence to reuse. **No `probe`, `producer_covered`, `static`, `empty` or `retired`** — all 22 are
`asset_kind='data'` with a live writer and a live consumer (E12).

---

## §2 — MUST (correctness; gates the capsule)

| # | finding | why it gates |
|---|---|---|
| M-01 | **A1** `_av_multiplier` fed the wrong ashtakavarga scale | The docstring at `bo_laksana.py:957-983` records a *previous* B2 fix of this exact defect class ("every signal got the same AV multiplier"). That fix corrected the house dimension and left the scale wrong, so **the defect survived its own repair** and the multiplier is still constant. Fix by switching the feed to `ashtakavarga_bindu_per_varga` (bhinna 0–8, the scale the buckets were written for) keyed on the signal's own graha — also the classically correct reading: AV support for a Saturn signal is Saturn's bindus, not the undifferentiated sarva total |
| M-02 | **A2** `int(fact_value_num or 28)` | A NULL that silently becomes the *top* bucket. §N.7 item 6 — a favourable-sounding default standing in for "I don't know". Unknown bindus ⇒ `NULL` multiplier + `inputs_complete=False`, never 28 |
| M-03 | **A5** `bo_vargottama_dhana` misreports its own column | §N.7 item 3. The named column says 0.0 while the effect is smuggled through `class_prior` |
| M-04 | **A6** `cancellation_modifier` has no detector | §N.8: a signal with no detector is **NULL**, not `1`. The documented "0.1 = cancelled yoga" semantic was never implemented anywhere |
| M-05 | **A11** `class_prior` 0% hit rate behind a warn-only guard | §N.8. `bo_laksana.py:3282-3299` warns below 50% and ships. A guard that cannot stop a bad build is not a gate, and serving presents the constant as a computed prior (`query_signals.ts:121`) |
| M-06 | **B7** `bodha_cgm_edges.cross_system_consensus_count` ≡ 1 on 849/849 | §N.8, and worse than NULL — an unearned signal wearing a measured value's clothes, with the honest source (`present_in_traditions_array`) populated right beside it |
| M-07 | **B8** `bo_samvada`'s `count_sql` cannot read false | C12 + §N.8. It returns 5 for any chart with any signal row, whether or not the writer ever ran |
| M-08 | **C1** `source_corroboration_count_by_text = 5 if two_pass_verified else 2` | The lane's live fabrication, on 149,706 rows. Writer fix **and** the null-out migration ship in the same PR — a migration that nulls while the writer re-fabricates on next build is theatre |
| M-09 | **E1** the three populated `expected_volume_formula` values are wrong or unevaluable | C12 names a NULL formula as the defect; a *wrong* one is worse, because it reads as done. `EDGE_DENSITY` is an unbound free symbol |
| M-10 | **E3** `bo_laksana` 10,045 below floor, `medical`/`vastu` at zero rows | C12 "derive, never pick": compute the expected volume, attribute the delta to a named cause, then rule. Investigation precedes the fix |
| M-11 | **E6** NULL `target_table` on two assets | Not tidiness: `CHECK asset_registry_natural_key_partition_needs_table` makes the C12 partition key **structurally unsettable**, and both assets are un-clearable from the cockpit (all three fallbacks absent) |
| M-12 | **E11** `A14_ucn_digest` pinned by a passing test | §N.8 in its purest form — a green assertion whose truth is exactly what should be false. A retired asset is still a UI-visible build-DAG node because a test requires it to be |
| M-13 | **D9** `coverage_matrix.ts:428` → `marsys://tool/L2/get_signal_embeddings` | A coverage claim pointing at a tool that does not exist. Either build the serve path or record the honest disposition — not a phantom pointer |
| M-14 | **C12 universal** — 0 of 22 assets have an `integrity_check_sql` | The layer has no data-correctness gate at all. Real invariants per C12, never `count(*) = N` |

---

## §3 — NOW (admitted: clear value, bounded cost, or last-cheap-chance)

Every entry carries its doctrine citation, per plan §4.

| # | work | doctrine | admission basis |
|---|---|---|---|
| N-01 | **argala into stored salience** — 41,760 L1 facts, `fact_value_num` already normalised 0..1; reinstate the term in `SalienceInputsV2` as `(1 + argala)` | D-SALIENCE ("chart-intrinsic terms live in stored salience, computed at build") | The mandate's headline item, and the L1 authority already exists unread |
| N-02 | **AV support from the correct bhinna feed** (`ashtakavarga_bindu_per_varga`, 6,720 facts) | D-SALIENCE | pairs with M-01 |
| N-03 | **vargottama from `graha_vargottama_amplification_factor`** (`factor − 1` → honest 0 or 0.25) | D-SALIENCE | the L1 authority is name-for-name the column's source and is unread |
| N-04 | **A4** remove the four `tags[…]` detectors that cannot fire (0 of 139,471 L1 facts carry those jsonb keys) | §N.8 | last-cheap-chance: they are being replaced by N-01/02/03 in the same pass |
| N-05 | **A7** wire the one *real* `neechabhanga` detector to the main path (today it reaches 135 of 150,150 rows) | D-SALIENCE, §N.8 | the detector exists and is correct; only its reach is wrong |
| N-06 | **A12** delete the dead `_av_mult` / `_HOUSE_WEIGHT` duplicates shadowing `formulas.py` | §N.7 item 3 | zero call sites; drift hazard removed at no risk |
| N-07 | **A13** `bo_karanajala` reads L1 `argala_natal_matrix` instead of re-deriving from house offsets | **§N.5** | an L2 asset re-deriving an L1 authority is the documented MSR-drift trap |
| N-08 | **B1/B2/B3** back-fill `contradicts_signals_array` from `bodha_contradictions`; non-participants stay **NULL, never `'{}'`** | D-SYNTHESIS | 22 rows, but it turns on `bo_upaya`'s `contradiction_factor`, which is currently and correctly disabled. Highest value-per-line in the layer |
| N-09 | **B4** `cross_system_consensus_count` at `chart_facts.fact_subject` level | D-SYNTHESIS, §N.5-clean | 2,808 rows reach ≥2; references an L1 fact rather than re-deriving one |
| N-10 | **the adjudication-rule table** (authority profile × strength-in-chart), generalising `kala_paddhati_profile`'s conventions | D-SYNTHESIS ("adjudication is a stored, reasoned ruling") | named work in plan §5; the precedent table gives the shape |
| N-11 | **grounding matcher** — sutrāvalī antecedent → rule hits, D1-only, per-ayanamsha; graha recovered via `constituent_facts_array` for the graha-anonymous dignity slice | D-GROUNDING | proven, not projected: 70 (planet,house) + 79 (planet,sign) hits across 10 of 14 texts |
| N-12 | **plug the concordance substrate** — `classical_text_chunks.topic_tag` (7,010 chunks / 361 topics), output into the existing `classical_sources_jsonb` shape + a `concordance_topic_ids[]` member | D-GROUNDING, D-SERVICE | that shape is already read by `resolver.ts:481-490`, so output reaches callers with no serving change |
| N-13 | **`grounding_tier` + `citation_granularity` + `bodha_grounding_matches`** (migrations 660/662) | D-GROUNDING | the match table is what makes a tier falsifiable rather than asserted |
| N-14 | **`tail_watch`** as a hard-floored section, declared once in `applyMcpBudget` + populated per umbrella | D-SALIENCE tail clause | `minKeep ≥ 1` **and** `IMMUNE_HONESTY_FIELDS` membership — `hardFloor` alone does not satisfy "no trim may zero it" (D3) |
| N-15 | **plug `bodha_anomalies`** — promote `low_salience_high_consequence` (125 rows) to a first-class serving input rather than a default-false parameter on an unexposed capability | D-SALIENCE, D-SERVICE (built-but-unplugged is a named defect class) | plan §5 names it |
| N-16 | **D5** run the percentile setter in the six satellite writers | D-SALIENCE | without it the rare-class predicate excludes exactly the 149 rows it most wants |
| N-17 | **D6** hand-author `density_contract` + real `empty_reason` on the five L2 umbrella capabilities | **§N.6** | they are the designated `tail_watch` carriers; a derived `empty_reason: true` with no handler behind it is §N.8 at scale |
| N-18 | **D7** extend the grounding spine (`resolver.ts` SELECT + `GroundedSignal`) to carry the new fields | D-SERVICE (≤2 hops to L1, ≤1 more to grounding tier) | small and surgical; the resolver must **not** treat empty citations on a `pratyaksa` row as a defect, or it manufactures pressure to fabricate |
| N-19 | **E4** set the 13 wrong floors to achieved counts | §N.4 | floors are aspirational; never fabricate rows to hit a number |
| N-20 | **E5** one `catalog_status` sweep for the 9 unpromoted assets **plus a CI guard** (`has_writer AND rows>0 ⇒ NOT DRAFT`) | D-SERVICE | migration 294 already swept this exact bug once; eight later migrations reintroduced it. Without the guard, migration N+1 does it a third time |
| N-21 | **E7** resolve the two `sort_order` collisions | C12 (ordering contiguity) | trivial, and it is literally an invariant class C12 names |
| N-22 | **E10** `COMMENT ON TABLE` on the six `__ssv_*` snapshots recording tag, date, PR #846 and expiry | hard floor §3.5 (snapshot protection) | they carry zero self-describing metadata today — which is what let an earlier drain script miscount them |
| N-23 | **A8/A9** `specificity` and `salience_robustness` | §N.8 | both are claims with nothing behind them. Compute in the existing in-memory pre-INSERT pass (never by UPDATE — that path measured 600 s+ on 28K rows), or remove the claim |
| N-24 | **consensus chip** on `bodha_pratijna.varga_confirmation` (135/135 populated) | D-SYNTHESIS (singular verdict voice) | the only real consensus substrate today; it does not wait on N-09 |
| N-25 | **lens drill** extension for the adjudication ruling, gated on explicit request | D-SYNTHESIS ("inspectable via a lens drill only on explicit request") | no `only_on_explicit_request` primitive exists anywhere yet |

---

## §4 — NEVER / LATER (logged with reason, closed)

| # | item | disposition |
|---|---|---|
| L-01 | **`system_convergence_count`** | **HELD on adjudication #1720.** The only definition available from existing data yields mean 5.93 / max 6 on 50,044 rows and measures the signal's *domain*, not the signal. Shipping it would be §N.7 item 6. An honest NULL until ruled |
| L-02 | **`sruti` tier as literally defined** | **HELD on adjudication #1726.** The corpus has page/column addressing, not verses. `yukti` and `pratyaksa` proceed now; the text-direct tier waits on the ruling. **Under no circumstances** is `chapter` emitted as a chapter |
| L-03 | **`bg_concordance` repair** (`bigint[]` vs `text` chunk-id mismatch; `rule_ids` grouped by text not topic, 497 rules/row; `match_confidence = min(1, n_chunks/5)`) | **LATER — handed back, not routed around.** `bg_concordance.py` is L0's write-set (charter C5: no session touches another's). L2 plugs the substrate instead (N-12) and hands the aggregate's repair to the backlog with evidence |
| L-04 | **dropping the six `__ssv_*` snapshots** (571 MB) | **LATER — Phase Z.** Four of six differ materially from live, and the 49,563-row `bodha_msr_signals` snapshot is the direct witness for M-10's investigation. Discarding it before that closes would destroy the comparison. Comment them now (N-22), drop nothing |
| L-05 | **the 13 UCN→UCD serving/contract residuals** beyond M-12 | **LATER.** The data-layer retirement is genuinely complete. The remaining residuals are contract-vocabulary and generated-projection debris across ≥6 files; M-12 (the false green) is the only one that is a correctness defect. Named list in W1 §5 E11 |
| L-06 | **`cross_ayanamsha_consistency_score`** | **LATER.** 100% NULL and genuinely uncomputed — not a denormalisation gap. It is a *governed grounding metric*, so `resolve_metric` returns `null` for it on every call today; that is honest, and inventing a value would not be |
| L-07 | **`A10` `salience_inputs_complete = false` on 100% of rows** | **Closes itself.** The flag is honest; it reads false because M-01…M-05 and N-01…N-05 are true. It becomes meaningful the moment they land — no separate work |
| L-08 | **`asset_throughput` cost fields** (`rows_per_second`, `measurement_count`, `history` empty on all 22) | **LATER — not L2's surface.** Real cost data exists in `build_run_assets` (E13) and W6 will report from there. The measurement facility's own emptiness is an orchestrator-layer §N.8 finding, handed forward |

---

## §5 — Capability deltas L2 publishes (charter C6)

Published here immediately so L1/L3/L4/L5 can plan against it. Each is announced in
`L2_STATE.md` § CAPABILITIES LANDED the moment its PR merges — that section, on `main`, is the
only surface a consumer should poll.

| capability | what a consumer gains | blocked on |
|---|---|---|
| **consensus columns populated** | `cross_system_consensus_count` non-NULL on ~2,808 signal rows (canonical chart); `contradicts_signals_array` on the 22 contradiction participants. L4's "one agreement line per verdict" becomes computable | N-08, N-09 |
| **grounding fields populated** | `grounding_tier` (`yukti`/`pratyaksa` now; text-direct on #1726), `grounding_evidence_jsonb`, `citation_granularity`, and honest — i.e. mostly NULL — corroboration counts | N-11…N-13, M-08 |
| **`tail_watch` shipped** | a hard-floored, trim-immune tail section available to every bridged envelope | N-14, N-15 |
| **adjudication table live** | `bodha_adjudication_rules` — stored, reasoned rulings, drillable | N-10 |

**L2 holds nothing inbound.** No L2 item waits on another layer's capability; L2 is the publisher.
Its only external dependency is the **E-gate** (C2), which is data, not capability: no L2 asset has
an L0-only ancestor set, so every W4 dispatch waits on L1 freezes. `bo_sudarshana` is the frontier
at 1 unfrozen ancestor (`ga_positions`) and is the designated canary.

---

## §6 — Sequencing consequence for W4 (recorded here so W3 does not have to rediscover it)

`registry_fingerprint_sha256` in the campaign's evidence payload is computed over
`REGISTRY_CONTRACT_FIELDS`, which includes `integrity_check_sql`, `count_sql`, `catalog_status`
and `target_table` (`dispatch_nirmana_campaign_wave.py:36-49`, `:246-269`). The dispatcher rejects
any `asset_analysis_accepted` whose recorded fingerprint no longer matches live (`:325`).

**Therefore: every registry-mutating migration (M-09, M-11, M-14, N-19, N-20, N-21) must land
BEFORE the W2 analysis/verdict events are recorded**, or C2 condition 3 fails on every asset and
forces a delta re-review of all 22. Recorded as decision **D-L2-003**.

*End L2_W2_DECIDE v1.0 — 22 routes, 14 MUST, 25 NOW, 8 LATER, 3 adjudications open (#1716, #1720, #1726).*
