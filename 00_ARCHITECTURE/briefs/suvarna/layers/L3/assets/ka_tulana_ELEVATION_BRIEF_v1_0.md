---
asset_id: ka_tulana
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "none specific to L3 yet; L0 rulings by analogy, PROVISIONAL until the J1 review. The I-11 weights are NATIVE-RATIFIED 2026-06-21 (ranker header): a ratified judgment seed (Carr N/A by cause `ratified_judgment`, the L0 Q13 reading by analogy)"
track_i_items: [TI-L3-07, TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-17, TI-L3-19, TI-L3-21]
ledger_gap_ids: ["ka_tulana-Idem.pattern", "ka_tulana-Build.count_integrity", "ka_tulana-Earn.build_record", "ka_tulana-Cost.baseline", "ka_tulana-Dens.served", "ka_tulana-Build.history", "ka_tulana-Build.dep_liveness", "ka_tulana-Carr.detector", "new: tulana-N1", "new: tulana-N2", "new: tulana-N3", "new: tulana-N4", "new: tulana-N6", "new: tulana-N5"]
---

# ka_tulana — Cross-pattern prioritization service: I-11 composite ranking of windows, and its self-test writer

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository, the saved census and the saved read-only evidence named in the section they appear in (B.10); no figure here was invented. No SS answer exists yet for L3: the open questions are in `INDEX.md` section 9. Every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/services/ka_tulana/writer.py`.*

Registry: kind service, per-chart, no table. The service (`services/ka_tulana/ranker.py`, `KaTulanaService`) ranks caller-supplied windows (`WindowInput`: convergence score, mode, peak date, confidence label, cycle length in years, domains, dissonance) by an I-11 composite: 0.40 × convergence + 0.25 × rarity (years / 30, capped) + 0.20 × confidence (high 1.0, moderate 0.6, speculative 0.2) + 0.15 × a piecewise proximity factor (`ranker.py:38`, `ranker.py:46`, `ranker.py:198`); it buckets by the 13 canonical domains (`brahmagyan.domain_vocabulary`) and explains each rank in a rationale string (`ranker.py:240`). It reads nothing itself ("reads only" the data a caller supplies). Served by `call_priority_ranking` in `call_service_wrappers.ts`, `kala_views/priority.ts` and `register_p1_aliases.ts`. The registered writer (`services/ka_tulana/writer.py`) is a self-test over TWO synthetic windows (a rare high-convergence window must outrank a common low one; `writer.py:25`), writes `service_health` and `selftest_detail`, and raises on failure.

**Canonical chart: `stale`, `service_health` healthy.** Registry state: throughput `stale`, spec absent; latest run `cbd6ea44` complete 2026-08-13; 27 errors and 12 aborts on record (latest error 2026-08-12 `BLOCKED: upstream dependency(ies) ka_kala_darshana, ka_sangam, ka_vighnakara did not complete`); 0 of 3 declared dependencies lit. The self-test reads none of those three, so the staleness and the blocking are both artefacts of declared edges (CF-23), not of the service. In the rebuild plan's downstream-not-in-plan set (`stale`, section 1.4) and Nirmāṇa-frozen under t2 (2026-09-10), so removing its edges stales that manifest.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | service | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2455` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/services/ka_tulana/writer.py:87`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `none (service)`; count_sql tables: none | census |
| live rows / floor | n/a (service) / 0 (service) | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec ABSENT; service_health `healthy` | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_sangam`, `ka_vighnakara`, `ka_kala_darshana` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 0 / transitive 0 (census blocking_radius, every layer); named (REG 2026-09-30): none | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: none; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): none | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | service: served by `call_service_wrappers.ts` (a service call, not a read of rows); declarations `served_surface` null | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | frozen under t2, 2026-09-10 | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PARTIAL | no write to the asset's own table(s) (none declared) anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: services/ka_tulana/writer.py, services/ka_tulana/ranker.py] |
| Build | Build.target † | N/A | no target_table; asset_kind='service', has_writer=True |
| Build | Build.count_integrity | PARTIAL | count_sql=no, integrity_check_sql=yes |
| Build | Build.completion | N/A | no count_sql and nothing to count: has_writer=True, asset_kind='service', no target_table; build state='stale' |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=unmeasured) |
| Dens | Dens.served † | FAIL | 1 module(s): call_service_wrappers.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 27 error(s) and 12 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_kala_darshana, ka_sangam, ka_vighnakara did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 0/3 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_sangam (stale, chart 482012f1)', 'ka_vighnakara (stale, chart 482012f1)', 'ka_kala_darshana (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Build.dag †; Build.exercised.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **NO_DETECTOR** — NO_DETECTOR — 3 module(s) reach it by code: L3_kala/call_service_wrappers.ts, platform-mcp/src/tools/kala_views/priority.ts, platform-mcp/src/tools/register_p1_aliases.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 3 declared edge(s); exists: all 3 are active registry assets (every layer); cycle: ka_tulana is on no dependency cycle (registry-wide graph); reads-match: 0 read(s) of other assets' tables, every one covered by a declared edge; static scan of 4 code unit(s), 0 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface (including cascade-shaped zeros and phantom edges); **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state the saved census read that a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens FAIL, whose meaning changed at rev 4 (offline re-measure in section 1); **+ SS question** = the fix changes output or rests on a ruling. Gap ids beginning `new:` were found by reading the code in this lane and are in no ledger.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, census cell, or `new:`) | gate | class | note |
|---|---|---|---|
| ka_tulana-Idem.pattern | Idem | detector | service: nothing to replace (PARTIAL by rev-2 reading); N-22 service rule |
| ka_tulana-Build.count_integrity | Build | detector | `count_sql` none by design; `integrity_check_sql` present |
| ka_tulana-Dens.served | Dens | Dens rev-1 reading | offline rev-7 NO_DETECTOR (3 modules, no served select of rows) |
| ka_tulana-Build.history | Build | history | 27 errors, 12 aborts; latest is the cascade `BLOCKED` above (CF-10) |
| ka_tulana-Build.dep_liveness | Build | real (phantom edges) | 0 of 3 declared dependencies lit — and none is read (CF-23) |
| ka_tulana-Earn.build_record | Earn | detector | CF-05 |
| ka_tulana-Cost.baseline | Cost | information | CF-05 |
| ka_tulana-Carr.detector | Carr | detector | N/A by cause `ratified_judgment` for the weights (SS approval for the rule); D3 for the arithmetic: recompute the composite for a sample (CF-07) |
| new: tulana-N1 | Build.dag | real | the three declared edges are never read at build time (CF-23); `ranker.py:268` takes caller-supplied windows and the self-test uses synthetic ones |
| new: tulana-N2 | registry | real | no output-digest spec (same class as 1213, not covered by PR #2826); the builder grant gap applies to `selftest_detail` (CF-26) |
| new: tulana-N3 | Narr / Vocab | real | `_rationale` prints the weights as literals ("weight 40%", "25%", "20%", "15%", `ranker.py:240-249`) instead of reading `I11_WEIGHTS`, so a change to a weight (or a ratified revision) leaves the explanation stating the old one; `rarity_years or 'unknown'` prints a computed 0.0 as "unknown" |
| new: tulana-N4 | Null / honesty | information | a missing `rarity_years` scores a neutral 0.5 (`ranker.py:192`) — a constant for a missing term (CF-27); the validator rejects an unknown confidence label (`ranker.py:81`), so the `.get(label, 0.2)` fallbacks (`ranker.py:222`) are unreachable through `rank_windows` and only matter if a caller bypasses validation. The 0.5 is inside the ratified composite, but the default itself is not part of the ratification as far as the header says |
| new: tulana-N6 | Build.dag / honesty | information | `_validate_window` accepts only `mode` A or B and raises on anything else (`ranker.py:61`), while the Saṅgam table carries more modes and the Kāla Darśana intake of that table is 100% Mode C (`ka_kala_darshana.py` M9 comment): convergence windows passed to the ranker without a mode mapping are rejected rather than ranked. Whether any caller maps the mode was not traced in this lane (the service takes caller-supplied windows); an SS/acharya question on whether Mode C/D windows are in scope for the I-11 ranking |
| new: tulana-N5 | Idem | information | ties keep input order (`scored.sort(key=..., reverse=True)` is stable, `ranker.py:294`), so the ranking of equal composites depends on the order the caller supplies; no secondary key such as `window_id` |
| census: Null/Narr | Null, Narr | detector | stored text: none (the self-test writes health only); the SERVED `rationale` string is prose composed from the weights and values — a service-output Narr question for the declarations file (state whether served, unstored text is in scope); proposed `prose_fields: []` with that note; CF-06 |

## 3 · Disposition

**keep (P)** — a deterministic, ratified, well-bounded ranker. Defects: phantom edges, a missing spec, a rationale that restates the weights as literals, and tie order. None argues for a different disposition; the weights are not a gap (ratified).

Approver under Track A brief §10: **Steward (G16)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L3-020).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Remove the three unread edges (or declare them serve-time)

- **Answers:** new tulana-N1; CF-23
- **Change:** registry migration removing `ka_sangam`, `ka_vighnakara`, `ka_kala_darshana` from `depends_on`, OR an SS ruling that these edges mean "needed at serve time" and a declared edge kind so the dep-liveness gate does not treat them as build-time (no such kind exists today)
- **Files / declaration / migration:** a registry migration (CF-23 batch)
- **Failing-first test and mutation:** CF-23 over-declaration report; the dep_liveness cell no longer names the three
- **Output change:** none
- **Blast radius:** the Nirmāṇa t2 manifest of this asset goes stale (frozen asset, campaign OFF); one upstream hash changes once; the service stops being blocked by `ka_sangam`/`ka_vighnakara`/`ka_kala_darshana` in a coherent rebuild
- **Rebuild:** none
- **Gate it moves:** Build.dag, dep_liveness
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent in content, a DAG change: own review

### FD-2 · Render the rationale from the weights

- **Answers:** new tulana-N3, N5; CF-25
- **Change:** format the weight text from `I11_WEIGHTS` and print `rarity_years` with `is None` rather than truthiness; add a deterministic tiebreak `(composite desc, peak_date, window_id)` to `rank_windows` (`ranker.py:294`)
- **Files / declaration / migration:** `services/ka_tulana/ranker.py:240-249`, `ranker.py:294`
- **Failing-first test and mutation:** Failing-first: changing a weight changes the rationale text; two input orders of tied windows rank identically; mutation: restore the literals → fails.
- **Output change:** yes — the served `rationale` text and the order of tied windows → SS (R5, text-only plus tie order)
- **Blast radius:** served by `call_priority_ranking`, `kala_views/priority.ts`, `register_p1_aliases.ts`; no stored rows
- **Rebuild:** none (service code; no data)
- **Gate it moves:** Narr (service output)
- **Fix class:** writer/service code; **buildable before J1:** tier-independent

### FD-3 · Digest spec and N-22 declarations

- **Answers:** new tulana-N2; CF-26, CF-06
- **Change:** a spec in the 1213 shape after a determinism check (the self-test detail must be byte-identical across runs); declare `prose_fields: []` with the served-text note and the service N-22 rules as for `ka_dasha_kala` FD-4; Carr N/A by cause `ratified_judgment` for the weights (SS approval for the rule)
- **Files / declaration / migration:** a spec migration; `asset_declarations.json`
- **Failing-first test and mutation:** CF-26 shape; declarations validation
- **Output change:** none
- **Blast radius:** registry rows only
- **Rebuild:** a service run (REVIEW for SS)
- **Gate it moves:** Earn, Carr, Null, Narr
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent; the N/A rule is SS-approved only

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed `catalog_status` DRAFT vs CURRENT live
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline NO_DETECTOR; N/A by cause
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-06** — prose_fields declarations for the L3 assets that have none (Null and Narr gates). *This asset:* declare `[]` with the served-text note
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* `ratified_judgment`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 27 / 12
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* FD-1: three unread edges
- **CF-25** — Narr fidelity (golden-value) tests per L3 narration writer. *This asset:* FD-2
- **CF-26** — Service self-test assets: output-digest specs, source_paths and builder grants (I-4 / I-5 and the same class left open). *This asset:* FD-3
- **CF-27** — Documented-approximation constants and favourable defaults in the L3 temporal chain (the L2 CF-20 class). *This asset:* ratified weights; neutral defaults for missing terms

## 5 · Semantic fingerprint contract (for E5.5)

No table. Stored output: `service_health`/`selftest_detail` on the registry row (deterministic: the two synthetic windows rank in a fixed order); `last_selftest_at` volatile, excluded. The ranker's output for supplied windows is a pure function of the inputs and the reference date (default today: pin the reference date in any comparison).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the ratified I-11 composite and its documented factor definitions; the canonical 13-domain vocabulary.
- **Carriage check chosen (T4 §4.1; one only):** Carr N/A by cause `ratified_judgment` for the weights (SS approval for the rule); D3 for the arithmetic: recompute the composite for a sample of windows by an independent fixture.
- **Opportunities (never blocking):** add the window id as a tiebreak; a calibrated rarity/confidence mapping needs L5 outcome data.

## 7 · Decisions applied and open questions

No SS answer exists yet for L3 (this is the first set). The SS rulings of 2026-10-01 given for L0 (Q1 completion by count, Q2 Dens applicability and `uniform_authority`, Q11 Build.history window, Q13 Carr D1/N-A) are named in the sections where they would apply, **by analogy only**; whether they carry to L3 is itself Q-L3-16 in the INDEX. Items marked (R) in those rulings changed a verdict or criterion definition and are PROVISIONAL until the J1 review.

Open questions for Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L3-08** — CF-23: may the three unread edges be removed or declared serve-time?
- **Q-L3-10** — CF-26: digest spec for this service?

**Track I items arising (see INDEX section 10):** TI-L3-07, TI-L3-09, TI-L3-10, TI-L3-12, TI-L3-17, TI-L3-19, TI-L3-21.
