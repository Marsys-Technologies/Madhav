---
asset_id: ka_jivana_parva
layer: L3 Kāla (ka_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L3 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 066c58587"
disposition: "qualify (Q)"
disposition_proposal_approver: "Steward (G16) for qualify; the output changes in FD-2 and FD-3 go to SS (R5)"
decisions_applied: "none specific to L3 yet; L0 rulings by analogy, PROVISIONAL until the J1 review"
track_i_items: [TI-L3-01, TI-L3-07, TI-L3-10, TI-L3-11, TI-L3-13, TI-L3-15, TI-L3-17, TI-L3-18, TI-L3-19, TI-L3-20]
ledger_gap_ids: ["ka_jivana_parva-Earn.build_record", "ka_jivana_parva-Cost.baseline", "ka_jivana_parva-Dens.served", "ka_jivana_parva-Build.history", "ka_jivana_parva-Build.dep_liveness", "ka_jivana_parva-Carr.detector", "new: jivana-N1", "new: jivana-N2", "new: jivana-N3", "new: jivana-N4", "new: jivana-N5", "new: jivana-N6"]
---

# ka_jivana_parva — Life-arc chapters (Vimshottari MD + AD + the running PD) with a convergence-density quality label

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in section 7 and in the INDEX. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py`.*

`ka_jivana_parva.py`: one chapter row per Vimshottari mahadasha (level 1) and antardasha (level 2) at the canonical ayanamsha, plus the pratyantar levels of the currently running antardasha (level 3), clipped at birth (T-9: pre-birth theoretical dasha spans are not served as lived chapters, `:10`); the Vimshottari scope is deliberate (the comment at `:79` explains the 7-system × 5-ayanamsha blend it replaced). Each row carries `parva_level`, `start_year`/`end_year`, `dasha_planet`, `dominant_signal_class` (the most frequent `signature_class` among convergence windows in the span), `high_convergence_count`, `avg_effective_score` (mean of `COALESCE(kala_darshana.effective_score, kala_convergence.convergence_score)` over the windows in the span, `:117`), `parva_quality` (`peak / building / consolidating / receding / transitional` from cuts on that mean, `:356`), `theme_keywords` (three hand-written planet keywords plus the quality label, `:421`) and a one-sentence `narrative.summary` (`:426`: "{planet} daśā ({span}): {quality} phase marked by {themes}. N high-convergence windows in this span."). Light writer. Serving: `query_life_arc.ts:158` (`kala.life_arc`).

**Canonical chart: 100 rows present, throughput `stale`.** Unlike the four cascade-emptied tables this one has no signal key, so the 100 canonical rows survive (floor 100; written 2026-08-13 by run `cbd6ea44`); Abhinandan and the third chart hold the rest of the table's 309 rows. Dependencies 2 of 5 lit (`ka_kala_darshana`, `ka_sangam`, `ka_yojaka` stale); 28 errors and 12 aborts on record (latest error 2026-08-12, a cascade `BLOCKED`). It is in the downstream-not-in-plan set of the rebuild plan (section 1.4: `stale`, not rebuilt by the 26-asset plan). **Order hazard (code-read):** the writer has no precondition on its convergence input — when `kala_convergence` is empty for the chart (as it is now, CF-24) `conv_windows` is empty and every `avg_effective_score` is NULL, so every parva is stamped `transitional` and the existing rows are replaced by rows with no convergence evidence, still a success. A rebuild before `ka_sangam` and `ka_kala_darshana` have re-landed would do that. Output-digest spec present (migration 1021). Not Nirmāṇa-frozen.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2419` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py:53`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_jivana_parva`; count_sql tables: kala_jivana_parva | census |
| live rows / floor | 100 / 100 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_kala_darshana`, `ka_dasha_kala`, `ka_sangam`, `ka_yojaka`, `ga_dashas` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/kala_views/ahead.ts`, `platform-mcp/src/tools/kala_views/register_all.ts`, `platform-mcp/src/tools/kala_views/story.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `registry/layers/L3_kala/query_life_arc.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts:158` reads `kala_jivana_parva`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, section 1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Dens | Dens.served † | FAIL | 1 module(s): query_life_arc.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 28 error(s) and 12 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_kala_darshana, ka_sangam did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 2/5 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_kala_darshana (stale, chart 482012f1)', 'ka_sangam (stale, chart 482012f1)', 'ka_yojaka (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ["narrative.$.summary"] (the cells would be measured by a fresh census; the Null check needs the database, so none could be run offline) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Build.exercised; Ldgr.source_presence.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **NO_DETECTOR** — NO_DETECTOR — 1 serving-root file(s) naming kala_jivana_parva lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/register_p1_synthesis.ts; its served select and density_contract cannot be read — never FAIL, never the closable N/A

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 5 declared edge(s); exists: all 5 are active registry assets (every layer); cycle: ka_jivana_parva is on no dependency cycle (registry-wide graph); reads-match: 4 read(s) of other assets' tables, every one covered by a declared edge; static scan of 1 code unit(s), 4 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_jivana_parva-Dens.served | Dens | Dens rev-1 reading | offline rev-7 NO_DETECTOR: the scanner loses sync on `register_p1_synthesis.ts`; saved rev-1 FAIL (1 module, no `density_contract`) |
| ka_jivana_parva-Build.history | Build | history | 28 errors, 12 aborts; latest error is a cascade `BLOCKED` 2026-08-12 (CF-10) |
| ka_jivana_parva-Build.dep_liveness | Build | stale | 2 of 5 declared dependencies lit; chain order clears it |
| ka_jivana_parva-Earn.build_record | Earn | detector | CF-05 |
| ka_jivana_parva-Cost.baseline | Cost | information | CF-05 |
| ka_jivana_parva-Carr.detector | Carr | detector | CF-07 (D2: parva spans restate `chart_dashas` rows; integrity conjuncts (c)-(f) already test it) |
| census: Ldgr | Ldgr | information | PASS on `source_citation` populated 309/309 rows — table-wide (all charts) and a build tag; CF-08 |
| new: jivana-N1 | Idem / Build | real | DELETE (`:75`) precedes the early returns (`:97`, `:107`); and a missing convergence input is not a precondition at all (`:128`): CF-21 |
| new: jivana-N2 | Narr | real + SS question | `narrative.summary` states "{quality} phase marked by {theme_str}" where the themes are a fixed three-word list per planet (`_PLANET_THEMES`, `:408`), independent of the planet's condition in the chart and of the span's evidence; the quality label is convergence density only (and `theme_keywords` mixes the quality label into the keyword array, `:423`) |
| new: jivana-N3 | honesty | real | `transitional` serves both "no convergence evidence" (`avg_score is None`, `:394`) and a PAST span whose mean is below 0.25 (an ongoing span with any evidence below 0.55 reads `building`): the F-PARVA comment rejects the old 'building for everything ongoing' but the replacement still collapses two states |
| new: jivana-N4 | Null | real | `round(avg_score, 3) if avg_score else None` (`:443`) turns a computed 0.0 into NULL: the falsy-coalescing class of the M9 fix |
| new: jivana-N5 | Build.dag | real | declares `ka_dasha_kala` and never references it (CF-23) |
| new: jivana-N6 | Idem | real | the "ongoing" quality and the level-3 rows depend on `as_of_date = ctx.config.get('as_of_date') or date.today()` (`:60`) and nothing in the orchestrator sets the key (CF-28) |
| census: Null/Narr | Null, Narr | detector | declared `narrative.$.summary`; no fidelity test measured; CF-25 |

## 3 · Disposition

**qualify (Q)** — the asset claims a biographical life-arc chapter; what it computes is a Vimshottari span with a convergence-density label and planet-generic keywords. The claim should be narrowed to what is derived (FD-2), the evidence-free state made distinguishable (FD-3) and the order hazard closed (FD-1). Not retire: it is the only life-arc projection, serves one capability, and its spans are exact L1 spans. Qualify goes to the Steward; the label/narrative changes are output changes and go to SS.

Approver under Track A brief §10: **Steward (G16) for qualify; the output changes in FD-2 and FD-3 go to SS (R5)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Refuse (or flag) a build without convergence input; replace-after-assembly

- **Answers:** new jivana-N1; CF-21, CF-24
- **Change:** assemble the candidate rows first and delete after (CF-21); when `conv_windows` is empty for a chart that has Vimshottari spans, either refuse with a precondition error (like `ka_bhavishya_lekha`) or store `inputs.convergence_windows = 0` on each row so a convergence-free build cannot masquerade as a built one
- **Files / declaration / migration:** `ka_jivana_parva.py:75-128`
- **Failing-first test and mutation:** Failing-first: with empty `kala_convergence` and existing rows, the rows are preserved (refuse) or flagged (`inputs`), never replaced silently; mutation: restore the order → fails.
- **Output change:** none on a healthy rebuild; the additive `inputs` key if that option is chosen
- **Blast radius:** serving `query_life_arc.ts`, `kala_views/story.ts`, `ahead.ts`; no python reader of `kala_jivana_parva`
- **Rebuild:** none (exercised by the next rebuild)
- **Gate it moves:** Idem / Build
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Narrow the chapter claim to what is derived

- **Answers:** new jivana-N2; CF-25
- **Change:** drop `theme_keywords`/`summary` themes that are not derived from the chart, or derive them from the cited L1 condition of the dasha lord (references, never restated values), and word the summary as what it is: a Vimshottari span with a convergence-density quality; keep the exact span and counts
- **Files / declaration / migration:** `ka_jivana_parva.py:408-442`
- **Failing-first test and mutation:** Failing-first: a golden test where two charts with the same MD planet in opposite conditions do not receive identical theme text, or where no theme is claimed; mutation: restore the dictionary → fails.
- **Output change:** yes — `theme_keywords`, `narrative.summary` → SS (R5)
- **Blast radius:** `query_life_arc.ts:158` serves both; `story.ts` (`kala_story_get`) and `ahead.ts` consume them (not traced beyond the grep)
- **Rebuild:** needs production rebuild (REVIEW for SS)
- **Gate it moves:** Narr
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent

### FD-3 · A distinct state for "no evidence" and no falsy coalescing

- **Answers:** new jivana-N3, N4; CF-27
- **Change:** serve a separate `parva_quality` value (for example `no_convergence_evidence`) when `avg_score is None`, keep `transitional` for a real low score, and store `avg_effective_score` as the computed number including 0.0 (`is not None`, not truthiness)
- **Files / declaration / migration:** `ka_jivana_parva.py:356-405`, `:443`
- **Failing-first test and mutation:** Failing-first: a span with no windows reads the new state; a span whose mean is exactly 0.0 stores 0.0; mutation: restore the truthiness test → fails.
- **Output change:** yes — `parva_quality` vocabulary gains a value and a stored 0.0 replaces NULL → SS (R5); the table has a CHECK on `parva_level` only (migration 679), the quality column constraint is not read here
- **Blast radius:** `query_life_arc.ts` returns the label; consumers that switch on the five known values would see a sixth (not traced)
- **Rebuild:** needs production rebuild (REVIEW for SS)
- **Gate it moves:** Null / honesty
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-independent

### FD-4 · Pin the as-of date

- **Answers:** new jivana-N6; CF-28
- **Change:** the run config supplies `as_of_date`; the writer records it; see CF-28
- **Files / declaration / migration:** `ka_jivana_parva.py:60`
- **Failing-first test and mutation:** see CF-28
- **Output change:** none
- **Blast radius:** writer code
- **Rebuild:** none
- **Gate it moves:** Idem
- **Fix class:** writer code; **buildable before J1:** tier-independent

### Landed or in flight (not designs of this lane)

No Track I item touches this asset.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline NO_DETECTOR (scanner sync loss on `register_p1_synthesis.ts`) — a scanner item before the re-measure
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2: spans restate `chart_dashas` (integrity conjuncts (c)-(f))
- **CF-08** — Ldgr: assets with no recognised citation column, and presence read on build tags. *This asset:* build tag in `source_citation`; table-wide denominators
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 28 errors / 12 aborts
- **CF-21** — Replace-after-candidate: DELETE runs before the empty-upstream early return (five writers). *This asset:* FD-1
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* the unread `ka_dasha_kala` edge
- **CF-25** — Narr fidelity (golden-value) tests per L3 narration writer. *This asset:* FD-2
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* FD-3; cuts 0.55/0.60/0.45/0.25
- **CF-28** — Rolling-horizon writers: as-of pin, calendar-safe horizon, floors that move with the build date. *This asset:* FD-4

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, parva_index)` (the writer's serving order; `parva_level` is the level discriminator, migration 679). Volatile columns excluded: `id`, `computed_at`. Values depend on the as-of date (ongoing quality, level-3 rows): fingerprint at a pinned as-of (CF-28). Rebuild expectation: same 100 span rows for the canonical chart if the as-of year and the convergence inputs are unchanged; a rebuild before `ka_sangam` re-lands changes every `parva_quality` (FD-1).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the exact L1 span per chapter with birth clipping, the Vimshottari/lahiri scope decision and its documented reason.
- **Carriage check chosen (T4 §4.1; one only):** D2: each parva span equals a `chart_dashas` row (clipped at birth) — integrity conjuncts (c), (d), (e), (f) of the registry check already assert it; register them as the detector.
- **Opportunities (never blocking):** derive chapter themes from the cited L1 condition of the dasha lord; extend to the other systems as separate, labelled series rather than a blend.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 7):

- **Q-L3-06** — FD-2/FD-3: narrow the narrative claim and add a distinct no-evidence label?

**Track I items arising (see INDEX section 10):** TI-L3-01, TI-L3-07, TI-L3-10, TI-L3-11, TI-L3-13, TI-L3-15, TI-L3-17, TI-L3-18, TI-L3-19, TI-L3-20.
