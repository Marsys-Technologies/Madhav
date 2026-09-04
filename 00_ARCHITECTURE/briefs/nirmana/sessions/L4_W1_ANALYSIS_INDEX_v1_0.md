---
artifact: L4_W1_ANALYSIS_INDEX_v1_0.md
canonical_id: NIRMANA_V21_L4_W1_INDEX
version: "1.0"
status: CURRENT
campaign_id: nirmana-elevation
session: L4
wave: W1 ANALYZE — COMPLETE (9/9 assets)
produced_on: 2026-09-05
---

# L4 PHALA — W1 ANALYZE — INDEX (9/9 assets)

Method: four concurrent read-only subagents against live production (canonical chart
`482012f1-…5871aa`, cross-checked on Abhinandan `1c826d5a-…40f75a`), source at `origin/main`
`20323fae4`. **No writes of any kind.** Each batch answered the plan §4 W1 rubric per asset:
instrument fit vs the five doctrines · real-vs-declared dependencies · **leverage** (a designed
consumer reading NULL where the asset already computed the answer) · grounding labelability ·
temporal identity · service (consumer, floor, density, drill) · measured cost · C12 volume
derivation · findings triaged MUST / NOW / NEVER-LATER.

| batch | assets | file |
|---|---|---|
| **A** | `ph_nimitta` (the layer root) | `L4_W1_ANALYSIS_BATCH_A.md` |
| **B** | `ph_muhurta` · `ph_sankrama` (timing surfaces) | `L4_W1_ANALYSIS_BATCH_B.md` |
| **C** | `ph_sodhana` · `ph_suddha_sodhana` · `ph_pratikara` (purification + remedial) | `L4_W1_ANALYSIS_BATCH_C.md` |
| **D** | `ph_pramana` · `ph_phaladesa` · `ph_rectification` (verdict spine + rectification) | `L4_W1_ANALYSIS_BATCH_D.md` |

Total: **9 assets, 4 files, ~95 findings.** Routes and triage: `L4_W2_DECIDE_v1_0.md`.

---

## The five things that matter most

**1. The layer's terminal verdict is invisible.** `phala_phaladesa` (the domain verdict) and
`phala_pramana` (the falsifiability registry) have **zero MCP consumers** — their only readers,
`query_domain_result` / `query_falsifiers`, are registered in the retrieval registry but bridged to no
MCP tool (0 hits in `mcp_surface_profiles.generated.json` / `web_tool_bridge.generated.json`). L4
computes a verdict that `judgment_query` and the `assess_*` family cannot see. *(D/F1)*

**2. A fabricated classical citation is on 100% of remedy rows, and it is laundered into a grade.**
`services/ph_pratikara/engine.py:257` hardcodes `'Brihat Parashara Hora Shastra — Upaya chapter'` as a
`next(…, default)` fallback; `phala_mitigation.classical_citation` is `NOT NULL`, so the invented
string is structurally guaranteed on all 1,277 rows across both charts. `kala_upaya_diagnosis.ts:481`
then grades every one of them `efficacy_tier = 'classically_attested'` on the strength of that string,
and `phala_mitigation_map.ts:219`'s `all_cited: true` is a check that **cannot read false**. Real
chapter-level citations sit populated one hop upstream on all 135 `bodha_rm_remedy_prescriptions`
rows, unpropagated. **This is the layer's hard-floor item.** *(C/F3, F4, F5, F6)*

**3. Four detectors are structurally incapable of returning their negative — and one of them asserts a
refutation anyway.** §N.8 in four live instances: `ph_muhurta`'s `window_quality_verdict` can only ever
read `mediocre` (the tarabala placeholder pins the geometric mean at 0.5, capping composite below the
`adequate` threshold); `ph_pramana`'s `life_event_match` is unreachable code (53 LEL domain slugs vs 13
canonical, exact-equality) so every past-window anchor is stamped `life_event_miss` — *the strongest
negative claim the instrument makes, on no evidence*; `ph_rectification`'s `load_bearing: true` is a
pure function of event *availability* while its actual fit is `0.0000` on all 95 scored candidates with
`win_margin = 0`; and `ph_sodhana`'s `detect_confidence_degenerate` guards the one axis that varies
while the two ceiling inputs it exists to protect are chart-wide constants. *(B/F1, D/F2, D/F3, C/F13)*

**4. The purification chain is doctrinally correct and then ignored.** `ph_sodhana` /
`ph_suddha_sodhana` **label, never drop** — exact 1:1 tiling, 0 orphans both directions on both
charts, demotion disclosed on-row, the D43 no-auto-apply rail triple-locked and genuinely earned. Then
`ph_phaladesa` picks each domain's headline anchor by `ORDER BY confidence_high DESC` — *the exact
field `ph_sodhana` flagged as inflated on 90 of 139 anchors* — so **6 of 7 populated domains lead with
a `staged_revision` anchor.** The chain's output is available and is not consulted by the one decision
it was built to inform. *(C/§4, C/F9)*

**5. D-7 (varshaphala / tithi-praveśa consumption into anchors): NOT CONSUMED — proven, not
suspected.** Exhaustive grep across `writers/ph_nimitta.py` and all four `services/ph_nimitta/` files
for `varshaphala|varsha|tajaka|tithi_prave|muntha|patyayini|saham|annual` → **zero matches**. None of
the 9 declared deps nor the 3 undeclared reads is a Tajaka/varsha asset. Meanwhile
`l1_tajik_varsha_year_lords` (240), `kala_tithi_pravesha` (120) and `kala_sudarshana_varsha` (120) are
all built for this chart. The nearest miss is one unselected column: `bodha_msr_signals.source_subsystem`
(which `bo_laksana` populates `"ga_tajaka" → "tajaka"`) is absent from `_load_signal_meta`'s SELECT —
which is also why `phala_anchors.subsystem_source` is 0/139. *(A/F16, A/F15)*

---

## Cross-cutting patterns (each appears in ≥3 of the 4 batches)

| pattern | instances |
|---|---|
| **Computed at build, dropped at serve** — the writer is honest, the SELECT list is not | `tarabala_chandrabala_jsonb` with its `placeholder_no_ephemeris` label (B); `posterior`/`lift_vector` nulled on 139/139 by an empty `CALIBRATED_CONFIDENCE_BASES` set (A); `narration_jsonb` — the only prose verdict L4 produces — never served (D); `derivation_ledger_jsonb` unserved on **six** assets, defeating B.3 auditability |
| **TEXT-column `ORDER BY … DESC` inverting the salience ladder** | `magnitude` → `pivotal>moderate>minor>major`, so `top_k=50` returns 45 minor + 0 of 3 major (A/F3); `anomaly_severity` → critical **last** (C/F10); `obstruction_severity` → high **last** (C/F10); `cleanliness_status` → `staged_revision` last (C) |
| **`or 0.0` / `or 'default'` converting "I don't know" into a favourable constant** | `trajectory='stable'` on all 2,985 rows from a 100%-NULL L2 column (B/F2); `promise_lift=1.75` from a fabricated `pratijna_grade=5.0` on 54 rows (A/F5); `direction='mixed'` on all 131 convergence anchors (A/F7); `int(n or 1)` promoting a real 0 (C/F12); `mall or 'semi_influenceable'`, latent (D/F5) |
| **Declared DAG edges that are fiction** | `ph_muhurta` 4 of 8 unread (B); `ph_pramana` **5 of 6** unread (D); `ph_rectification` 1 of 1 unread + 4 real reads undeclared (D); `bo_laksana` declared-unread by both `ph_sodhana` and `ph_phaladesa` (C, D); `bodha_pratijna` + `kala_activation_predicates` read-undeclared while supplying the two largest posterior multipliers (A/F17) |
| **No `density_contract`, no `empty_reason`, no `hardFloor` anywhere in L4** | 8 of 9 capabilities; `grep hardFloor` → **0 phala hits** against 14 in `registry_bridge.ts`, while `phala_outlook` runs a 30 KB cap over a 461 KB payload, so PASS-2 zeroing is the normal path (D/F12) |
| **`rows_inserted += 1` unconditional after `ON CONFLICT DO NOTHING`** | `ph_muhurta` over-reports by exactly the collision count (139 claimed / 134 stored) (B/F6); latent in `ph_nimitta`, `ph_sodhana`, `ph_pratikara`, `ph_sankrama`. **Floors must be set from `count_sql`, never from `rows_written`** |
| **No cost measurement anywhere** | `rows_per_second` NULL, `measurement_count` 0, `history` `[]` on **all 9 assets × both charts**. Every `estimated_seconds` is an undeclared-provenance number |

---

## F-L4-A closed: the C12 answer for all nine

Every L4 asset has `target_floor` / `expected_volume_formula` / `expected_volume_inputs` /
`integrity_check_sql` NULL — the C12 defect condition verbatim. W1 derived an honest volume expectation
**from first principles** for all nine, and none is a bare `count(*) = N` pin:

| asset | derived expectation | verified against live data |
|---|---|---|
| `ph_nimitta` | `Σ_domain min(50,|kala_convergence(d)|) + |kala_bhavishya| + min(100,|bodha_discoveries|)` minus clip/dedup attrition | ~460 derived → 139 stored (≈70% rejected, currently logged to stdout only) |
| `ph_muhurta` | `count(DISTINCT (map_domain_to_action(domain), normalized_start))` over influenceable anchors | 134 = 134 ✓ (and exposes the 5-row over-report) |
| `ph_sankrama` | `Σ_d anchors(d) × cells(domain_row = map(d), linkage ≥ 0.25)` | **exact on both charts**: 2510 = 2510, 475 = 475 ✓ — and the formula is what exposed the 250 destroyed rows |
| `ph_sodhana` | `BETWEEN 0 AND (5 × n_anchors) + 1` — a **ceiling**, not a floor: it is an anomaly registry, and a floor here would incentivise fabricating findings | 97 ≤ 696 ✓ · 41 ≤ 281 ✓ |
| `ph_suddha_sodhana` | `= n_anchors` (a derived equality against a live upstream count) | 139 = 139 ✓ · 56 = 56 ✓ |
| `ph_pratikara` | `= n_obstructions` — **not** anchors | 536 = 536 ✓ · 741 = 741 ✓; explains the apparent chart inversion |
| `ph_pramana` | `= count(phala_anchors)` | 139 · 56 ✓ — but `target_floor` stays **NULL until the dead detector is fixed**; a floor would enshrine a count a dead detector produced |
| `ph_phaladesa` | `card(canonical_domains)` = 13 | 13 · 13 ✓ — genuine derived constant, not a chart-independence bug |
| `ph_rectification` | `(floor(2·half_width/step)+1) × card(ayanamshas) + 1` = 37×5+1 | 186 · 186 ✓ — likewise genuine; lagna values differ per chart |

Two of the proposed integrity checks are deliberately **currently-failing** invariants — `ph_pramana`'s
"a `life_event_miss` must cite a resolvable LEL comparison" (fails 12/12) and `ph_rectification`'s
"`load_bearing` may not be true on a non-discriminating fit" (fails 1/1). Per C12's rewrite floor test,
a replacement check must be able to fail on real corruption the old one could not detect; these two
fail *today*, on the real defect, which is the proof they are gates rather than proposals.

---

## Verified-clean — do not "fix"

- **The `ph_pramana` D5 NO-SCORING gate.** Three real layers (forbidden-name set, per-record
  `_d5_gate` raising before every INSERT, and a table with **no numeric column at all**), with a genuine
  build-halt path. **The honest-probability surface is preserved. Do not add a score.**
- **`base_rate` NULL on all 195 predictions** — explicitly deferred to `mi_pramana`. An honest null.
- **`lel_entry_id` NULL** with a documented uuid-vs-bigint rationale, the uuid carried auditably in jsonb.
- **`'(see falsifier_text)'`** in place of an invented criterion.
- **The D43 NO-AUTO-OVERRIDE rail** in `ph_suddha_sodhana` and `ph_rectification` — engine constant +
  runtime raise + DB CHECK + `native_adopted = false`. Earned in the §N.8 sense.
- **`query_rectification`'s `non_discriminating` / `lel_match_explanation` / structural-resting-state
  note** — the best §N.6/§N.8 work in the L4 serving plane, and the template the other capabilities
  should be brought up to.
- **13 and 186** — genuine derived structural constants with chart-dependent payloads.
- **`ph_sodhana` / `ph_suddha_sodhana`'s label-not-drop semantics** — exact 1:1 tiling, disclosed
  demotion. The doctrinally correct shape; the defect is downstream non-consumption, not the chain.
- **§N.5's inversion trap is clean across the layer** — no case was found of an L4 asset re-deriving an
  L1 computed value as its own truth. The gap is the opposite one: L4 references L3/L2 but rarely
  reaches an L1 `fact_id`, so the ≤2-hop drill is transitive rather than direct.
