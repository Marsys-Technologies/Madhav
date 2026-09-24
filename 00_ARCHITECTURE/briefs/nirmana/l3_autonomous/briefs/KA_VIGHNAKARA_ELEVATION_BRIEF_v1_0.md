---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
canonical_id: KA_VIGHNAKARA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW
approval_record: "<none yet>"
parent_layer_contract: "MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md / DP-SD-017 / commit 793972c754b106688097dbc54536c1a9c270a793"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
synergy_binding: KALA_SYNERGY_BINDING_v1_0.md
synergy_binding_version: "2.2"  # §B1 ruled name is precision_regime (not claim_grain, which was v1.0); values {instant_grain, date_grain}; day_grade aliases date_grain until Sangam D-7 successor condition, NOT for a count of generations
asset_or_interface_ids: ["ka_vighnakara", "SC-5 (the top-500 convergence cap and the 200-anchor cap → coverage)", "SC-7 (Vedha-root reconciliation: this asset and ka_vedha_gochara both speak obstruction)", "SC-8 (its swisseph integration is a FOURTH one, and it is TRUE-node while the ruled convention is mean)", "registry packet: declare bg_ephemeris and ga_dashas; the seeded ka_gochara edge", "B4: independence_group per detector — five detectors are not five witnesses"]
goal_objective: "Make the obstruction detector's testimony countable and its conventions declared: five detectors of very different evidential weight are emitted as flat rows with one severity scale and no independence marking; two caps (top-500 convergence windows, 200 daśā anchors) bound the search undisclosed; one detector silently degrades to a day-modulo proxy when the pañcāṅga engine fails; and its Rāhu is the TRUE node while the layer's ruled convention is mean."
source_revision: "9feac52d7 (l3/kala-layer-briefs); cited code identical at a99300bb7 (2026-09-24)"
accepted_upstream_contract: "ka_sangam's kala_convergence (top-500 by score, peak_date NOT NULL); ka_yojaka's predicates via the SHARED services/ka_temporal date resolver (also used by ka_kalasutra); L0 bg_combustion_orbs (per-graha orbs, with classical Sārāvalī/BPHS fallbacks in-code); L1 chart_facts natal positions; ka_muhurta_seva for the real tithi (the service is instantiated but compute_panchang is called directly)"
implementation_owner: "<one writer, named at stage 3 — not the author>"
independent_review_owner: "Fable 5.1 review agent, fresh context; report at briefs/reviews/REVIEW_KA_VIGHNAKARA_v1_0.md"
release_authority: "NONE"
may_touch: ["platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py", "platform/python-sidecar/tests/l3/test_ka_vighnakara*.py", "one additive migration on kala_obstruction (coverage/qualification columns; independence_group; NO new FK)"]
interface_packet_targets_not_may_touch: ["platform/src/lib/retrieval/registry/layers/L3_kala/query_obstruction_periods.ts and L4_phala/salience_order.ts, register_d5_fanout.ts — Pūrṇa/L4-owned", "platform-mcp/src/tools/retrieval/kala_temporal.ts — Pūrṇa-owned; L3 owns only the sentinel test"]
must_not_touch: ["kala_convergence / ka_sangam (producer; its brief)", "kala_activation_predicates / ka_yojaka (producer; its brief)", "services/ka_temporal/date_resolver.py signature (SHARED with ka_kalasutra — a coordinated packet)", "services/ka_muhurta_seva/** (its own brief)", "panchang_engine/** and panchang_engine/swiss_state.py (shared Swiss-state span)", "bg_combustion_orbs, chart_facts (L0/L1)", "pipeline/orchestrator/writers/ph_pratikara.py, ph_muhurta.py (L4 readers, sealed)", "pipeline/orchestrator/writers/ka_kala_darshana.py (reader; its brief)", "platform-mcp/src/tools/kala_views/**", "applied migrations — incl. 670 and 1033–1070", ".github/workflows/deploy.yml", "WriterBase / orchestrator contract"]
target_state_data_plane: "PRODUCER_READY"
target_state_campaign: "ANALYZED → ENRICHED at stage 3"
wave: "W4"
shape: single asset, rows (chart × obstruction_type × anchor) in two families — convergence-anchored and daśā-anchored
evidence_base: >
  Source read directly on 9feac52d7 [V]; migration 670's ka_vighnakara contract (a)–(e), blueprint
  v5.0 §3.5 row 12 / §4 / §16.2 [A]; no database query.
does_not_authorize: any code, migration, grant, build or serving change.
changelog:
  - "1.0 (2026-09-24): first issue; awaiting independent review."
---

# `ka_vighnakara` elevation brief — obstruction as countable testimony

## §0 — The recommendation, in one paragraph

`ka_vighnakara` is the layer's counter-evidence producer, and it is built with real care: it
**requires swisseph and raises before touching the DB** so a missing library can never wipe the
prior partition (`:145-160` [V]); it resolves the native's own birth location and **refuses to
borrow another chart's coordinates** (`_resolve_native_location`, *"Never falls back to Bhubaneswar
… a resolution failure raises loudly (B.10)"*); it takes per-graha combustion orbs from L0
`bg_combustion_orbs` under a savepoint with cited classical fallbacks (Sārāvalī ch.6 / BPHS ch.3);
and migration 670's contract already pins severity as a restatement of `severity_score`, bounds
`override_score`, and requires each row to name its anchor family. Four things are undeclared or
inconsistent. (1) **Two caps bound the search**: the convergence intake is `ORDER BY
convergence_score DESC … LIMIT 500` (`:177-182`) and the daśā-anchored family stops at
`_MAX_DASHA_ANCHORS = 200` (`:40-43`) — neither appears on a row or in a coverage object. (2) **Five
detectors are emitted as flat rows with one severity scale and no independence marking**: a
gaṇḍānta (the Moon in a 3°20′ junction) and a combustion (a graha within its orb of the Sun) are
different kinds of evidence with different classical weight, and nothing tells a consumer they are
not five independent votes. (3) The pañcāṅga detector **silently degrades to a day-modulo proxy**
when `compute_panchang` fails (`tithi = (peak_date.day % 15) or 15`), and the row records
`source: 'day_mod_proxy'` in its detail — honest at the field level, but the same
`severity_score` 0.35 is emitted either way. (4) Its Rāhu is **`swe.TRUE_NODE`** (`_SWE_IDS` `'Rahu':
11`) while the layer's ruled convention is mean — a **fourth** independent swisseph integration
(SC-8) that no convention vector declares. Recommendation: **`QUALIFY_LIMIT` + `ENRICH_CORRECT`** —
caps → coverage; `independence_group` per detector family; the proxy path typed as a distinct
`source_qualification` rather than an equal-severity row; the node convention declared and
reconciled; and the two undeclared edges declared. Decisions: §10.

---

## §1 — Already established

| record | says | delta on this base |
|---|---|---|
| Register §5 | obstruction / counter-indicator detection | — |
| Strategy §3 *Temporal testimony (opposition)* | counter-evidence is testimony, not a veto | binds §4.3 |
| **Migration 670 (`:1648-1740`)** [V] | (a) accretion on **two** natural keys — convergence-anchored `(chart, convergence_id, obstruction_type)` and daśā-anchored `(chart, signal_id, obstruction_type, detail→>peak_date)`; (b) the FK on `convergence_id` enforces existence but **not chart agreement**, plus *"every chart that has convergence windows must have obstruction rows"* (the F-VIGHNA-4 cascade detector); (c) `severity` must equal the threshold restatement of `severity_score` (§N.7 item 1); (d) `override_score` ∈ (0, `severity_score`] — *"an override that exceeds its own severity, or is zero, is a suppression claim with no detector behind it (§N.8)"*; (e) each row must name its anchor family in its own provenance, and a convergence-anchored row must carry no `detail.anchor` | a strong contract; the elevation must not weaken it |
| Blueprint §3.5 row 12 (`:328`), §4 (`:400`), §16.2 (`:910`) | rows **0** (536 recorded — the cascade); LIMIT 500; double-count; Vedha root; *"cap → coverage; declare `bg_ephemeris` + `ga_dashas`; `independence_group` per detector; Vedha-root reconciliation (SC-7); daśā-anchored rows carry `convergence_available=false`"* | this brief |
| Seed (`asset_registry_seed.ts:2316-2331`) | `depends_on: ['ka_sangam', 'ka_gochara', 'ka_muhurta_seva', 'ga_positions']` | **`bg_ephemeris` and `ga_dashas` are read (via swisseph and the resolver) and undeclared**; `ka_gochara` is seeded — whether it is read is §11.4 |

---

## §2 — Current-state evidence (contract §2)

### 2.1 Registration [V]
`storage_type: 'postgres_table'`, `target_table: 'kala_obstruction'`, chart-scoped `count_sql`,
`scope: 'per_chart'`.

### 2.2 The code [V]
- **Guard first** (`:145-160`): `import swisseph` or `raise RuntimeError("swisseph not available …")`
  **before** any DB operation, with the reason stated in the comment — *"so that a missing swisseph
  never causes the prior chart's kala_obstruction rows to be silently wiped by the DELETE below"*.
  Then `SET LOCAL statement_timeout = 0` and `DELETE FROM kala_obstruction WHERE chart_id`
  (`:168-172`).
- **Convergence intake** (`:174-182`): `SELECT convergence_id, signal_id, mode, peak_date,
  convergence_score, orb_strength, window_start, window_end FROM kala_convergence WHERE chart_id AND
  peak_date IS NOT NULL ORDER BY convergence_score DESC NULLS LAST **LIMIT 500**`. Empty →
  *"No convergence windows — run ka_sangam first"* (`:184-188`).
- **Daśā anchors** (`:195-201`, `_dasha_anchor_peaks`): for predicates whose signal is **not** already
  covered by a convergence row, resolve activation windows through the **shared**
  `services/ka_temporal` resolver (`:430-458`) and take each `activation_peak`; first signal to claim
  a peak represents it; **stop at `_MAX_DASHA_ANCHORS = 200`** (`:40-43`, break at the cap). The
  whole block is savepoint-guarded.
- **Five detectors** (`_detect_all` `:485-510`):
  1. `malefic_transit` — Saturn/Rāhu in an adversarial sign vs the native lagna, `swe.calc_ut` with
     `FLG_SIDEREAL` + `SIDM_LAHIRI` (`_get_sidereal_lon`, `@serialized_swiss_state`); adverse maps
     score by house relation (6th/8th 0.45, 7th 0.40); `< 0.2` → no row; `override = score × 0.45`.
  2. `panchanga_obstruction` — rikta tithi from `compute_panchang` at the native's location; **on any
     exception, falls back to `tithi = (peak_date.day % 15) or 15`** and still emits a row with
     `severity_score = 0.35`, `override 0.12`, `detail.source = 'day_mod_proxy'` and the citation
     *"Muhurta-Chintamani §Rikta-Tithi"* (`:601-650`).
  3. `gandanta` — the Moon in the last 3°20′ of a water sign (`_GANDANTA_RANGES`).
  4. `papakartari` — the lagna bhāva hemmed between malefics.
  5. `combustion` — a graha within its per-graha orb of the Sun; orbs from `bg_combustion_orbs`
     under `SAVEPOINT sp_comb_orbs`, else the in-code classical map (`_COMBUSTION_ORBS_CLASSICAL`,
     cited).
- **Node convention**: `_SWE_IDS = {'Sun': 0, 'Moon': 1, 'Mars': 4, 'Saturn': 6, **'Rahu': 11**}`
  with the comment `# swe.TRUE_NODE` — a fourth swisseph integration, TRUE-node, undeclared.
- **Severity** (`_SEVERITY_THRESHOLDS` `[(0.70,'severe'), (0.40,'moderate'), (0.0,'mild')]`) —
  restated, as 670(c) requires.
- **Write** (`:281-292`): two row families with distinct `source_citation`
  (`ka_vighnakara:v2.0:conv=<id>` vs `ka_vighnakara:v2.0:dasha_anchor`, the latter also setting
  `detail.anchor='dasha_timeline'`); plain `INSERT` (no `ON CONFLICT`); `convergence_id` NULL on the
  daśā family.
- **Test-only proxy**: `_test_proxy_windows` is documented as never populated in production.

### 2.3 Consumers [V]
| consumer | reads | role |
|---|---|---|
| `writers/ka_kala_darshana.py` | obstructions by `convergence_id`; `override_score` and `severity` drive the effective score and net label | `counterevidence` — the main integrator |
| `writers/ph_pratikara.py`, `ph_muhurta.py` (L4) | obstruction rows | L4 |
| `brahmagyan/kala/obstruction.py`; `kala_derivation_completeness_guard.py` | the table | service / guard |
| `query_obstruction_periods.ts`; `L4_phala/salience_order.ts`; `register_d5_fanout.ts`; `kala_temporal.ts` | served | served |

**Live-path statement.** The obstruction rows drive Darshana's effective score and net label, reach
two L4 writers and four served surfaces. The caps, the proxy path and the node convention are live
on all of them.

### 2.4 Epistemic class
| field | class | authority | note |
|---|---|---|---|
| `obstruction_type` | rule identity | this writer (CHECK-constrained; two of seven values reserved) | — |
| `severity_score` | `INTERPRETIVE_INFERENCE` — engineered per detector | this writer | five detectors, one scale, no independence marking |
| `severity` | restatement of the score | 670(c) | correct |
| `override_score` | engineered suppression weight (`score × 0.45` etc.) | this writer | bounded by 670(d); it is what Darshana multiplies by |
| `detail.source` | provenance | this writer | `'panchang_engine'` vs `'day_mod_proxy'` — the **same** severity either way |
| Rāhu's position | computed fact | this writer's own swisseph call, **TRUE node** | the ruled convention is mean (SC-8/B6) |
| the two caps | search bounds | this writer | undeclared |

### 2.5 Ladders
`PLAN_REVIEWED`; rows **0** live (the cascade), 536 recorded [A]. t3: no event.

---

## §3 — The failure (contract §3): one falsifiable problem

| field | content |
|---|---|
| Observed behavior | A chart with 900 convergence windows gets obstruction testimony for the **top 500 by score** and no record that 400 were never examined; a chart with 600 uncovered predicates gets daśā anchors for **200** of them and no record of the rest. Within what is examined, a window that draws a gaṇḍānta, a combustion and a rikta tithi produces three rows that a consumer counts as three obstructions — while the rikta row may have been produced by `(peak_date.day % 15)` rather than a real pañcāṅga, at the identical `severity_score` of 0.35. And the Rāhu used by the malefic-transit detector is the **true** node while the layer's ruled convention is mean |
| Evidence | `ka_vighnakara.py:40-43,:177-182,:195-201,:430-458,:485-510,:601-650`, `_SWE_IDS`, `_SEVERITY_THRESHOLDS`, `:281-292` [V]; 670 `:1648-1740` |
| Expected contract | SC-5/B5 (every cap disclosed); B4 (`independence_group` on anything a concurrence counts); B6 + D6 (mean node); SC-8 (one declared convention vector per integration); §N.7 item 6 (a proxy must not wear the same grade as the measurement); F09/DP06 (declared dependencies) |
| Defect class | **undisclosed caps** + **uncountable testimony** (no independence) + **proxy wearing the measurement's grade** + **undeclared convention** (TRUE node) + **undeclared dependencies** |
| Impact | Darshana's effective score is computed from a max over rows whose number is capped and whose independence is unknown; a "three obstructions" reading may be one mechanism seen three ways, or two real detections plus a day-modulo guess; a mean-node consumer and this writer disagree about where Rāhu is |
| Non-claim | no claim that the proxy path fires in production (unmeasured — it requires `compute_panchang` to raise); no claim that any chart exceeds either cap (unmeasured); the 0-row live state is upstream; no claim about which node convention is doctrinally right — only that the layer ruled one and this writer uses the other |

---

## §4 — The semantic delta (contract §4)

1. **L3-Q served.** Q04 (activity coexisting with strain — *"a decisive second-domain opposition
   survives compilation"*), Q-K06 as a blueprint cross-reference.
2. **Caps → coverage (SC-5/B5).** `coverage = {requested_horizon: the chart's convergence span,
   completed_horizon, resolution: 'anchor', partitions_searched: ['convergence_top_500',
   'dasha_anchor_200'], exclusions: [{reason:'above_convergence_cap', dropped: n},
   {reason:'above_anchor_cap', dropped: m}], unsearched_regions: [], completion_detector:
   'all_anchors_examined_or_capped'}`, plus `convergence_available: bool` on every daśā-anchored row
   (the blueprint's own ask) so a consumer knows that family had no window to attach to.
3. **`independence_group` per detector family (B4).** The five detectors do not share a root in
   equal measure: `malefic_transit`, `gandanta` and `combustion` all read **transiting graha
   longitudes at the same instant** from one ephemeris call set — one group, `basis=
   'declared_lineage'`, `declared_current_count = 1` for that family — while `panchanga_obstruction`
   (a tithi) and `papakartari` (a natal-lagna relation) are separate groups. A consumer counting
   obstructions counts **groups**, not rows.
4. **The proxy is not the measurement (§N.7 item 6).** When `compute_panchang` fails, the row keeps
   `detail.source='day_mod_proxy'` **and** carries `source_qualification='algorithmic_approximation'`
   with a distinct, lower `severity_score`, or — recommended — is **not emitted at all** and instead
   recorded in `coverage.exclusions` with `reason='panchanga_unavailable'`. A day-modulo tithi is not
   a pañcāṅga; emitting it at the measured detector's severity is exactly the invented-grade defect
   §N.7 item 6 names (§10.2 decides).
5. **Convention declared (SC-8, B6).** Every row carries the detector's convention vector —
   `node_convention` (today `'true'`, honestly), `ayanamsa_application` (`apparent_flg_sidereal`,
   since `_get_sidereal_lon` uses `FLG_SIDEREAL`), `ephemeris_backend` observed. The **reconciliation
   to mean** is a coordinated item with the Graha Sañcāra reference (that brief's §10.3), not a
   silent flip here: this is a fourth independent integration and changing it alone would put it out
   of step with the scanner, which is frozen and Gochara-owned.
6. **SC-7 (the Vedha root).** `ka_vedha_gochara` also speaks obstruction (vedha). The two must not
   be counted as independent opposition when they derive from the same transit; the reconciliation is
   SC-7's and this brief's rows carry the `independence_group` that makes it possible.
7. **Declared dependencies.** `bg_ephemeris` (swisseph is used directly, but the *stored* ephemeris
   is not — see §11.3) and `ga_dashas` (via the resolver) are declared by registry packet; whether
   `ka_gochara` is actually read is checked at stage 3 and the edge kept or dropped.
8. **Qualification (B2).** `epistemic_class='INTERPRETIVE_INFERENCE'` on the scores;
   `operator_role='counterevidence'`; `tier_basis='relative_uncalibrated'`; `comparable_with='self'`
   within a detector, `different_convention` across detectors (their scales are engineered
   separately); `completeness_state='applied'`, or `'unavailable'` with a reason where a detector
   could not run.
9. **Old vs new.** Positive: a window with a real rikta tithi and a combustion → two rows, two
   groups, coverage complete. Negative: swisseph missing → the existing raise, before the DELETE.
   Boundary: a chart with 501 convergence windows → 500 examined, `dropped: 1` declared. Missing:
   `compute_panchang` raises → per §10.2 either no row and a coverage exclusion, or a qualified
   lower-severity row — never an equal-severity guess. Duplicated: three transit-derived detectors on
   one instant → **one** group.
10. **Simpler baseline.** Today's rows.
11. **Ablation.** Feed a fixture where the pañcāṅga engine raises: today a 0.35 obstruction appears
    and Darshana's effective score drops; after, the reading either loses that obstruction with a
    stated reason or keeps it visibly qualified — the difference is whether a day-modulo guess can
    move a served verdict.

---

## §5 — Preservation, fences, migration, rollback

- `PRESERVE`: the swisseph guard **before** the DELETE (the reason it exists is exactly §N.3's
  hazard); `_resolve_native_location`'s refusal to borrow coordinates; the L0 combustion orbs under
  a savepoint with cited fallbacks; the two-family `source_citation` discipline 670(e) pins; the
  severity restatement.
- `ENRICH_CORRECT`: coverage; `independence_group`; the proxy's disposition; the convention vector.
- `QUALIFY_LIMIT`: `tier_basis`; `comparable_with`; the caps.
- **Shared-code fence**: the `ka_temporal` resolver is `ka_kalasutra`'s too — no signature change.
- **Swiss-state fence**: `@serialized_swiss_state` is preserved; `panchang_engine` untouched.
- **Migration**: one additive migration on `kala_obstruction`; **no new FK** (the existing nullable
  `convergence_id` FK is what 670(b) exploits).
- Rollback: additive columns.

---

## §6 — Lenses A–J *(appendix)*

| lens | answer |
|---|---|
| A | L3 rows; five engineered detectors over L0/L1 facts and one live ephemeris; `QUALIFY_LIMIT + ENRICH_CORRECT` |
| B | four declared edges; `bg_ephemeris`/`ga_dashas` read and undeclared; fan-out: Darshana, two L4 writers, four served surfaces |
| C | invariants: 670 (a)–(e); every cap disclosed; transit-derived detectors share one group; a proxy never carries a measurement's grade; the node convention declared |
| D | the 0-row live state is upstream |
| E | Darshana is the load-bearing consumer (its effective score multiplies by `override_score`) |
| F | coverage, `independence_group`, `convergence_available`, the convention vector machine-readable |
| G | one ephemeris call set per anchor; the 200-anchor cap is a cost guard — its cost basis should be measured, not assumed |
| H | idempotent; the guard-before-DELETE is exemplary |
| I | files in `may_touch`; one additive migration; W4; a coordinated SC-8 item |
| J | this brief; §7; the review |

---

## §7 — Proof matrix

Columns: **verdict tier** F24; **scope** `[U]` unit, `[I]` DB fixture, `[S]` served.

| proof | verdict tier | scope | fixture / command | expected | invariant | detector fails when… | evidence path |
|---|---|---|---|---|---|---|---|
| Positive | COMPUTATIONAL_CORRECTNESS | I | a window with a real rikta tithi + a combustion | two rows, two `independence_group`s, coverage complete; 670 (a)–(e) TRUE | the contract | any conjunct FALSE | integrity SQL |
| Negative | COMPUTATIONAL_CORRECTNESS | I | swisseph unimportable | `RuntimeError` **before** the DELETE; the prior partition intact | the guard | the DELETE fires first | writer test |
| Relevant influence | COMPUTATIONAL_CORRECTNESS | I | move Saturn into an adversarial sign at the anchor | `malefic_transit` appears with the mapped score; other detectors unchanged | isolation | a second detector moves | writer test |
| Irrelevant control | COMPUTATIONAL_CORRECTNESS | I | reorder the convergence rows with identical scores | identical row set (the intake's `ORDER BY` needs a total tiebreak to guarantee this) | order-invariant | the top-500 membership changes | writer test |
| Duplication | COMPUTATIONAL_CORRECTNESS | I | one anchor producing `malefic_transit` + `gandanta` + `combustion` | **one** `independence_group` across the three; `declared_current_count = 1` | shared ephemeris root | counted as three witnesses | writer test |
| Context | COMPUTATIONAL_CORRECTNESS | I | `compute_panchang` raises | per §10.2: no row + `coverage.exclusions[panchanga_unavailable]`, **or** a row with `source_qualification='algorithmic_approximation'` and a distinct severity | a proxy never wears the measurement's grade | an equal-severity 0.35 row (today) | writer test |
| Boundary | COMPUTATIONAL_CORRECTNESS | I | 501 convergence windows; 201 uncovered predicates | 500 / 200 examined; both `dropped` counts declared | caps disclosed | a silent cap | writer test |
| Convention | COMPUTATIONAL_CORRECTNESS | U | the Rāhu used by `malefic_transit` | `node_convention='true'` declared on the row (honest today); the mean reconciliation is a coordinated item | declared, not silent | the row asserts `mean` while computing TRUE | unit test |
| Delivery | COMPUTATIONAL_CORRECTNESS | S | sentinel `convergence_available=false` on one daśā-anchored row | reaches `query_obstruction_periods`'s envelope and Darshana's input | survives | absent | route test |
| Revision | COMPUTATIONAL_CORRECTNESS | I | Saṅgam rebuilds | rows replaced; 670(a) TRUE | no accretion | accretion | integrity SQL |
| Value | EXPLANATORY_DISCRIMINATIVE_VALUE | S | frozen Q04 question | the answer distinguishes one mechanism seen three ways from three independent obstructions; the baseline cannot | — | no distinction | baseline record |
| Evaluation | — | — | `not_applicable` (obstruction is testimony, not an outcome claim) | — | — | — | — |

Binding: **OFFERS** B2 (`epistemic_class`, `completeness_state`, `operator_role='counterevidence'`,
`source_qualification`, `tier_basis`, `comparable_with`), B4 (`independence_group`,
`declared_current_count` — the load-bearing offer), B5 (`coverage`), and the SC-8 convention vector.
**DEMANDS** the mean-node reconciliation (coordinated with the position reference) and SC-7's
Vedha-root reconciliation. B1: the rows are anchored at a `peak_date` (DATE) — `precision_regime=
'date_grain'`, `time_basis='event_instant'` for the swisseph calls at `jd` midnight, declared.
**Asset-local:** `convergence_available`, `detail.source`, `detail.anchor`, `override_score`.

---

## §8 — Prioritization

(1) `independence_group` per detector family (Darshana's max-over-rows is only sound once testimony
is countable) → (2) the proxy's disposition → (3) caps → coverage → (4) the convention vector
declared → (5) the two undeclared edges → (6) SC-7 reconciliation. W4.

---

## §9 — Disposition and target state

`QUALIFY_LIMIT` + `ENRICH_CORRECT`. Data-plane: `PRODUCER_READY`; `DATA_ACCEPTED` requires the
upstream cascade resolved; `CONSUMER_INTEGRATED` when Darshana and the served surfaces carry the
independence and coverage fields. Campaign: `ANALYZED → ENRICHED`. Non-claims: the 0-row state is
upstream; no `VALUE_EVALUATED`; the node reconciliation is not this brief's to execute alone.

**Walkthrough (ordinary period).** "Is anything working against this window?" → two obstructions in
two groups: a rikta tithi (real pañcāṅga, cited) and a transit group (Saturn adversarial + a
combustion, counted once), with `coverage` showing every window examined and nothing capped. The
reader learns what opposes, how independent it is, and that nothing was guessed.

---

## §10 — Decisions for the native

| # | decision | recommendation |
|---|---|---|
| 1 | **`independence_group` per detector family, with the three transit-derived detectors as one group** | yes — Darshana's max-over-rows depends on it |
| 2 | **The day-modulo tithi fallback: drop the row and record a coverage exclusion, or emit it qualified at a distinct lower severity?** | **drop and record** — a day-modulo tithi is not a pañcāṅga, and it currently moves a served verdict at the measured detector's weight |
| 3 | Caps → coverage; and is 500/200 the right bound? (Q8's portfolio question) | disclose now; the numbers are Q8's |
| 4 | Declare `node_convention='true'` now and reconcile to mean with the position reference (coordinated), rather than flipping this integration alone | yes |
| 5 | Declare `bg_ephemeris`/`ga_dashas`; verify and keep-or-drop the seeded `ka_gochara` edge | yes, by registry packet |

---

## §11 — Not verified here

1. Whether the day-modulo fallback ever fires in production — unmeasured.
2. Whether any chart exceeds 500 convergence windows or 200 uncovered predicates — unmeasured, and
   it bounds the caps' materiality.
3. Whether the writer reads **stored** `ephemeris_daily` at all, or only live swisseph — the
   dependency wording in §4.7 turns on this and it must be settled at stage 3.
4. Whether the seeded `ka_gochara` edge corresponds to a real read.
5. The 0-row live state and the 536 recorded count [A].
6. No database query; no test run.
