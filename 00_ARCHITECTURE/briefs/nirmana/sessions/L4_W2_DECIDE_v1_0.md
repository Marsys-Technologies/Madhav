---
artifact: L4_W2_DECIDE_v1_0.md
canonical_id: NIRMANA_V21_L4_W2_DECIDE
version: "1.0"
status: CURRENT
campaign_id: nirmana-elevation
session: L4
wave: W2 DECIDE — COMPLETE (9/9 assets routed, all findings triaged)
produced_on: 2026-09-05
inputs: L4_W1_ANALYSIS_INDEX_v1_0.md + BATCH_A..D
---

# L4 PHALA — W2 DECIDE

One route per asset; every W1 finding triaged `MUST` (correctness — gates the capsule) /
`NOW` (in-layer improvement) / `NEVER-LATER` (logged with reason, closed). Every `NOW` carries a
doctrine citation. Decisions are one-line ledger entries.

---

## §1 — Routes (9/9)

Route vocabulary per plan §4 W2: `changed | rebuild_only | verified_reuse | probe |
producer_covered | static | empty | retired`.

| # | asset | **route** | why this route and not the cheaper one |
|---|---|---|---|
| 1 | `ph_nimitta` | **changed** | 8 MUST findings incl. a spine gate whose stated claim has no detector (A/F1) and a 75% posterior amplification from no evidence (A/F5). Cannot `rebuild_only` — the writer is wrong, not stale. |
| 2 | `ph_muhurta` | **changed** | `window_quality_verdict` is structurally incapable of reading anything but `mediocre` (B/F1); `rows_written` over-reports by exactly the collision count (B/F6). |
| 3 | `ph_sankrama` | **changed** | 250 rows (10% of the asset) destroyed by a stale domain map (B/F5); `trajectory` constant from an `or 0.0` (B/F2). |
| 4 | `ph_sodhana` | **changed** | Detector-integrity defects (C/F12–F14) + a severity-inverting serving sort (C/F10). Registry NULLs need a migration regardless. |
| 5 | `ph_suddha_sodhana` | **changed** | The layer's cleanest asset — but the silent classify-clean path (C/F16) is the exact pattern F-173 removed from its sibling, and the C12 registry NULLs need a migration. |
| 6 | `ph_pratikara` | **changed** | 7 MUST findings including the layer's hard-floor item (C/F3). Also the only asset needing a **rerun after** its code fix — see §6 sequencing. |
| 7 | `ph_pramana` | **changed** | `life_event_miss` is a refutation asserted by a detector that cannot return "match" (D/F2). |
| 8 | `ph_phaladesa` | **changed** | Zero MCP consumers (D/F1) + headline-anchor selection ignores the purification verdict (C/F9). |
| 9 | `ph_rectification` | **changed** | `load_bearing: true` on a fit that is `0.0000` across all 95 scored candidates (D/F3). |

**All nine route `changed`. L4 has no `rebuild_only`, no `verified_reuse`, no `probe`, no
`producer_covered`, no `static`, no `empty`, no `retired`.**

That is worth stating plainly rather than burying, because it is unlike L0 (which routed
overwhelmingly `rebuild_only`) and it is not a stylistic choice: **every one of the nine carries at
least one MUST correctness finding**, so a rebuild of current code would faithfully reproduce the
defect. There are also no services in L4, so C12's service freeze-exception addendum applies to
nothing here.

**Two honest notes on the route assignments:**

- `ph_suddha_sodhana` is the one asset I considered routing `rebuild_only`. Its write path is
  correct — exact 1:1 tiling, label-not-drop, the D43 rail triple-locked and genuinely earned. It
  routes `changed` because C12 obliges a real `integrity_check_sql` (a migration is a code change),
  and because the `try/except → logger.debug` around its flag read can silently classify **every**
  anchor `clean`. I would rather fix a latent silent-suppression path in the layer's best asset than
  argue that its cleanliness excuses it.
- `ph_rectification` is `changed` for its detector, **not** for its scan. The 186-row lattice is a
  genuine derived constant and the writer's geometry is sound; only the LEL fit and the flag that
  reports it are broken.

---

## §2 — Triage summary

| | MUST | NOW | NEVER-LATER | total |
|---|---:|---:|---:|---:|
| A `ph_nimitta` | 8 | 8 | 8 | 24 |
| B `ph_muhurta` + `ph_sankrama` | 7 | 5 | 2 | 14 |
| C purification + remedial | 10 | 13 | 4 | 27 |
| D verdict spine + rectification | 5 | 11 | 4 | 20 |
| **total** | **30** | **37** | **18** | **85** |
| + M-31 (Conductor ruling #1732) | 1 | — | — | 1 |

Plus the two whole-layer registry findings from the session-open read (F-L4-A floors/volume/integrity
all NULL; F-L4-B `catalog_status='DRAFT'` across the layer), both **MUST**, both closed by the §9
registry delta.

---

## §3 — MUST (correctness; each gates its asset's capsule)

Grouped by the defect class they share, because the fixes share a shape.

### §3.1 — Fabricated or unearned grounding (the hard-floor cluster)

| id | asset | finding | doctrine |
|---|---|---|---|
| **M-1** | `ph_pratikara` | The hardcoded `'Brihat Parashara Hora Shastra — Upaya chapter'` fallback on 100% of 1,277 rows, made unavoidable by `classical_citation NOT NULL`. | **Hard floor** (fabricated evidence); D-GROUNDING; §N.7 item 6 |
| **M-2** | `ph_pratikara` | That invented string is laundered into a served *grade*: `efficacy_tier = 'classically_attested'` on every row. | §N.8; §N.7 item 4 |
| **M-3** | `ph_pratikara` | `phala_mitigation_map`'s `all_cited: true` **cannot read false**, while its docstring calls it an enforced "Grounding contract". | §N.8 |
| **M-4** | `ph_pratikara` | No `grounding_tier` / `classical_sources_array` / `source_id` column exists — remedies, a *named required-grounding class*, cannot carry a tier at all. Real chapter-level citations sit unpropagated on 135/135 upstream rows. | D-GROUNDING; §N.5 |

**Decision D-L4-05:** M-1..M-4 are fixed as one unit. `classical_citation` loses `NOT NULL` so an
honest null is *expressible*; a `grounding_tier` column lands; the citation is **propagated by
reference** from `bodha_rm_remedy_prescriptions.classical_sources_jsonb` (with `source_id`), never
restated (§N.5); the tier is assigned per output class exactly as W1 derived — prescription-derived
citation → `sruti`, sequencing → `yukti`, cost tiering → `pratyaksa`, intensity table → `yukti`,
corroboration count → `pratyaksa`. **An honest `yukti`/`pratyaksa` label is the success condition
here, not a downgrade** (plan §2, D-GROUNDING). `assignEfficacyTier` stops treating "a string is
present" as attestation.

### §3.2 — Signals with no detector behind them (§N.8 cluster)

| id | asset | finding | what would have to fail for the signal to read false, today |
|---|---|---|---|
| **M-5** | `ph_pramana` | `life_event_match` is unreachable code (53 LEL domain slugs vs 13 canonical, exact-equality); every past-window anchor is stamped `life_event_miss` — **the strongest negative claim the instrument makes** — on no evidence. 12 + 8 rows. | *nothing* |
| **M-6** | `ph_rectification` | `load_bearing: true` / `calibration_state: 'calibrated'` are pure functions of event *availability*, while the actual fit is `0.0000` on all 95 scored candidates and `win_margin = 0`. | *nothing* |
| **M-7** | `ph_muhurta` | `window_quality_verdict` can only read `mediocre`: the tarabala placeholder pins the geometric-mean factor at exactly 0.5, capping composite below the `adequate` threshold even if every other term were 1.0. 4 CHECK values, 1 reachable. | *nothing* |
| **M-8** | `ph_nimitta` | `_spine_gate`'s docstring claims it verifies `karmic_frame`; the code never checks it. Had it, the gate would fail 100% of builds. | *nothing* (the claim is in prose only) |
| **M-9** | `ph_nimitta` | `karmic_frame` lookup passes a full path label into a bare-planet dict → 0% hit rate on both charts, while two tool descriptions advertise the field per anchor. | *nothing* |
| **M-10** | `ph_sankrama` | `trajectory = 'stable'` on all 2,985 rows because the L2 column it reads is 100% NULL and `or 0.0` converts unknown → flat. Two of three branches dead. | *nothing* |
| **M-11** | `ph_nimitta` | `pratijna_grade = 5.0` applied when **no** `bodha_pratijna` row exists → `promise_lift = 1.75`, a 75% posterior amplification from no evidence, on 54/139 rows. The honest neutral (`no_evidence` → 1.0) already exists in the same function. | *nothing* |
| **M-12** | `ph_nimitta` | `direction` is constant `'mixed'` on all 131 convergence anchors (the upstream key is absent from 14,868/14,868 rows); `derive_anchor_from_discovery` still hardcodes the favourable `'elevated'`. | *nothing* |

**Decision D-L4-06:** every one of M-5..M-12 resolves to **an honest null plus a stored reason**, never
to a repaired-looking value. Concretely: `life_event_miss` becomes `pending_observation` with an
explicit `detector_unavailable` disposition *and* the domain vocabulary is normalised through
`brahmagyan.domain_vocabulary`'s existing synonym map — but **the fix must not silently turn 0 misses
into 0 matches**; the disposition has to be visible. `load_bearing` must consult *discrimination*
(`win_margin`), which the serving layer already computes as `non_discriminating`.
`window_quality_verdict` becomes null with a stored `verdict_ceiling_reason` until the tarabala source
is real. `trajectory` becomes null with the upstream-NULL reason. `promise_lift` uses the existing
`no_evidence` neutral. This is §N.7 item 6 applied nine times: *an honest null beats an invented
judgment.*

### §3.3 — Silent data loss

| id | asset | finding | doctrine |
|---|---|---|---|
| **M-13** | `ph_sankrama` | 250 rows — 10% of the asset — destroyed by `_ANCHOR_TO_CDLM_DOMAIN['transition'] = 'general'`, a domain CDLM does not have, when CDLM *does* have `transition` with 5 material cells that would have matched exactly. The map's own comment misstates CDLM's vocabulary on 4 of 7 terms. | C12 ("derive, never pick"); §N.6 |
| **M-14** | `ph_muhurta` | `rows_written` over-reports by exactly the natural-key collision count (139 claimed / 134 stored; 56 / 49) — `rows_inserted += 1` unconditional after `ON CONFLICT DO NOTHING`. | §N.8; §N.4 |
| **M-15** | `ph_pratikara` | `linked_anchor_id` is a single constant across every row (536 → 1 anchor, from 107 candidates in 4 domains), collapsing P4 proportionality, mis-keying the L5 outcome hook, and breaking the `domain` serving facet. **Survives the F-173 fix.** | §N.7 item 6; D-SYNTHESIS |
| **M-16** | `ph_pratikara` | Consequence of M-15: `query_remedy_program`'s `domain` filter returns 0 rows for every domain except `career`, with no `empty_reason`. | §N.6 item 3; D-SERVICE |
| **M-17** | `ph_pratikara` | 1,277 rows of provably empty remedy programmes — F-173's code fix landed 2026-08-21, the queued rerun never ran, live data is 9 days pre-fix. | §N.8; B.10 |

**Decision D-L4-07 (§N.4, binding on all nine):** `target_floor` is set from **`count_sql`, never from
`rows_written`.** M-14 is the proof this matters — a floor taken from the writer's own return value
would enshrine a fabricated number. This is the achieved-count discipline read strictly.

### §3.4 — Doctrine violations in the serving plane

| id | asset | finding | doctrine |
|---|---|---|---|
| **M-18** | `ph_phaladesa`, `ph_pramana` | **Zero MCP consumers.** The layer's terminal verdict and its entire falsifiability registry are invisible to `judgment_query` and the `assess_*` family. | D-SERVICE (a built-but-unplugged asset is a named defect class) |
| **M-19** | `ph_nimitta` | `ORDER BY magnitude DESC` on a TEXT column inverts the salience ladder: `top_k=50` returns 45 minor + 0 of the 3 `major` anchors. The densest rows are exactly what the trim discards. | §N.6 item 2; D-SALIENCE |
| **M-20** | `ph_sodhana`, `ph_pratikara` | The same inversion twice more: `anomaly_severity DESC` returns **critical last** (3 minor / 90 major / 4 critical, in that order); `obstruction_severity DESC` puts `high` last under `LIMIT 50` of 536. | §N.6 item 2 |
| **M-21** | `ph_nimitta` | `CALIBRATED_CONFIDENCE_BASES` is an empty `Set`, nulling `posterior`/`confidence_*`/`lift_vector` on **139/139** served rows — including inside the retrieval spine bundle — while a second live surface serves the same values raw. Two surfaces, contradictory policy. | D-SYNTHESIS; D-SERVICE |
| **M-22** | `ph_phaladesa` | The domain's headline anchor is chosen by `ORDER BY confidence_high DESC` — the exact field `ph_sodhana` flags as inflated on 90/139 anchors — so 6 of 7 populated domains lead with a `staged_revision` anchor. **The purification verdict is computed and then ignored by the one selection it exists to govern.** | D-SALIENCE; §N.6 item 2 |
| **M-23** | `ph_muhurta`, `ph_sankrama`, `ph_phaladesa`, `ph_pramana` | `grounds_to: { l1_fact_ids: true }` declared on four capabilities whose SELECT lists contain no fact identifier of any kind. | §N.8; §N.5 |

### §3.5 — The named mandate items

| id | finding | disposition |
|---|---|---|
| **M-24** | **D-7: varshaphala / tithi-praveśa consumption into anchors is NOT PROVEN — it is disproven.** Exhaustive grep over the writer and all four `services/ph_nimitta/` files → zero matches, while `l1_tajik_varsha_year_lords` (240), `kala_tithi_pravesha` (120) and `kala_sudarshana_varsha` (120) are all built for this chart. | **HELD (H-4)** on L3's tithi-praveśa verification landing. The proof obligation is discharged *negatively* and honestly now; the consumption itself is the W3 item. |
| **M-25** | **Prediction-provenance hygiene (parked-P7 seam) — verified, and it is half-broken by construction.** `mimamsa_predictions.source_pramana_id` holds an **anchor_id**, not a pramana_id: 195/195 resolve as `phala_anchors.anchor_id`, **0/195** as `phala_pramana.pramana_id` — while five generated projections advertise the ph_pramana link. And **no FK protects any of it**, so `ph_nimitta`'s next rebuild silently orphans all 195 predictions and 195 anchor adjustments. | **VERIFY-ONLY, handed to L5.** See §8. My W3 acts are (a) an integrity check that *detects* the orphan risk and (b) correcting the served descriptor text so the instrument stops claiming a link it does not have. **I will not rename the column or rewire `mi_bhavisya.py` — that is L5's write-set and a P7-programme decision.** |
| **M-26** | **Honest probability surfaces — PRESERVED, verified.** The D5 NO-SCORING gate is three real layers with a genuine build-halt path and a table carrying no numeric column at all. `base_rate` NULL on all 195 predictions is an honest deferral to `mi_pramana`. | **NO CHANGE. Recorded so nobody "completes" it.** §N.8 forbids inventing calibration values; L5 is sealed in STRUCTURAL mode *by design*. |
| **M-27** | `seed_native_phala_anchors()` — a deployed function inserting hand-authored predictions with hand-assigned confidences into `phala_anchors`, citing the deleted FORENSIC v8.0, live-routed at `POST /api/compute/phala/seed_anchors`, held back only by a schema mismatch. Its acceptance gate asserts idempotency PASS over a function that cannot succeed. | **RAISED, not fixed — adjudication #1739.** It straddles the parked-P7 "verify, do not modify" instruction and would require dropping a deployed DB object. |

### §3.6 — Whole-layer registry (F-L4-A / F-L4-B)

| id | finding | doctrine |
|---|---|---|
| **M-28** | All 9 assets: `target_floor` / `expected_volume_formula` / `expected_volume_inputs` / `integrity_check_sql` NULL — C12's named defect condition verbatim. | C12; §N.4 |
| **M-29** | All 9 assets: `catalog_status = 'DRAFT'` while every one has real build history on two charts and live consumers. | B.8 |
| **M-30** | Declared DAG edges that are fiction: `ph_pramana` 5 of 6 unread · `ph_muhurta` 4 of 8 unread · `ph_rectification` 1 of 1 unread with 4 real reads undeclared · `bo_laksana` declared-unread by two assets · `bodha_pratijna` + `kala_activation_predicates` read-undeclared while supplying the two largest posterior multipliers. | §N.8 applied to the DAG — **a declared edge is a claim** |

**Decision D-L4-08 on M-30:** dependency corrections are **additive-then-subtractive and split across
two batches.** Adding a genuinely-read edge (`bodha_pratijna`, `kala_activation_predicates`,
`chart_facts`) is safe. *Removing* a declared edge changes the registry contract fingerprint and
therefore invalidates my own W2 analysis evidence under the dispatcher's binding check
(`registry_fingerprint_sha256`) — so every removal lands in the **same** migration as the C12 registry
delta, before any W4 dispatch, never after. Getting this ordering wrong would force a full W2
re-acceptance for all nine.

### §3.7 — Deterministic anchor identity (Conductor ruling on #1732, binding)

| id | finding | doctrine |
|---|---|---|
| **M-31** | `phala_anchors.anchor_id` defaults to `gen_random_uuid()`, so an `ph_nimitta`-only rebuild orphans **6,606 rows across 9 tables** — **seven of them L4's own** (`phala_sankrama` 2,985 · `phala_mitigation` 1,277 · `phala_pramana` 195 · `phala_suddha_sodhana` 195 · `phala_muhurta` 183 · `phala_sodhana` 138 · `phala_phaladesa` 13), plus L5's `mimamsa_attribution` 1,425 and `mimamsa_manifestation_sets` 195. L4's tables self-heal on a whole-layer rebuild; **L5's never do**, because `mi_bhavisya` deliberately preserves adjudicated rows — the safeguard becomes an orphan generator. | **D-CND-04** (Conductor, binding); parked-P7 ("nothing may make the later loop harder"); §N.8 (the current 0-orphan state is true and *unearned* — nothing would detect its loss) |

**Status:** `ph_nimitta` / `phala_anchors` rebuilds are **HELD campaign-wide** until L4 announces the
deterministic-key capability under `## CAPABILITIES LANDED`. The hold is on one asset, not the layer,
and costs nothing today (37/46 ancestors unfrozen) — which is the point of ruling now.

**Self-correction, recorded rather than quietly fixed:** W1 found this same risk (D/F5) and graded it
*verify-only, handed to L5*, reasoning that the seam repair was L5's. That was wrong — seven of the
nine affected tables are mine. It is an L4-internal referential-integrity problem whose worst
consequence happens to land in L5. Ownership accepted.

**Decision D-L4-12 — the key is content-derived, not row-id-derived.** The obvious implementation,
`uuidv5(ns, phala_anchors_natural_key)`, **does not work**, and I verified that before building it:
that key embeds `convergence_id` and `bhavishya_id`, both **`bigserial`** (`nextval(...)`), and
`ka_sangam` / `ka_bhavishya_lekha` are delete-then-insert — so the ids renumber on L3's next rebuild.
It would satisfy the letter of the hold, pass its own detector today, and silently re-break the chain
the first time L3 rebuilds. **My layer's identity is currently downstream of two sequences**, and
none of `kala_convergence` / `kala_bhavishya` / `bodha_discoveries` declares a natural-key index at all.

So the identity tuple keys on upstream **content**, not upstream **row ids**: `chart_id` +
`anchor_source` + `domain`, plus a content digest of the source row's semantic columns as the writer
reads them (convergence / bhavishya), or `discovery_id` for discovery-sourced anchors. This makes L4's
determinism independent of L3's key regeneration, degrades in the semantically correct direction (a
genuine content change *should* mint a new anchor), and requires nothing from another session — the
hold is on my asset and I can lift it myself.

**Uniqueness measured, not assumed:** a digest over `kala_convergence`'s full semantic row (every
column except `convergence_id` and `computed_at`) is unique across all **35,365 rows — 0
fully-identical groups**. The narrower tuples are genuinely insufficient:
`(chart_id, mode, domain, window_start, window_end, peak_date, signal_id)` collides on 402 tuples, and
adding `source_citation` *and* `constituent_factors` leaves those same 402 — which is why the wide
form is taken.

**M-31 is the layer's highest-priority unheld W3 item**, ahead of everything in §3.1–§3.6, because it
gates my own W4 canary and because the damage it prevents grows with exactly the data P7 exists to
accumulate.

---

## §4 — NOW (in-layer improvement; admitted by clear value, bounded cost, or the last-cheap-chance rule)

Consolidated; each cites the doctrine that admits it.

**N-1 · The unserved-honesty cluster (§N.6 item 4; D-GROUNDING).** Six assets compute honesty
metadata and drop it at the SELECT list: `tarabala_chandrabala_jsonb` carrying
`source: 'placeholder_no_ephemeris'`; `ph_sodhana`'s `check_basis:
'confidence_high_proxy_not_convergence_score'`; `bridge_path_jsonb` / `cascade_chain_jsonb`;
`derivation_ledger_jsonb` on **six** assets, defeating B.3 auditability entirely; and
`narration_jsonb` — *the only prose verdict L4 produces*, computed 13/13 and never served, while the
capability serves `narration_status`, the status of a thing it never returns. **The writers are
honest; the readers are not. This is a SELECT-list fix, not a writer fix** — which is why it is
cheap enough to admit now.

**N-2 · Density contracts + empty-reasons (§N.6 item 4; D-SERVICE).** No L4 capability except
`query_prospective_ledger` declares a `density_contract`; `grep hardFloor` returns **zero** phala hits
against 14 in `registry_bridge.ts`, while `phala_outlook` runs a 30 KB cap over a 461 KB payload — so
PASS-2 zeroing is the *normal* path, not the edge case. Two sibling templates already exist in-tree
(`ELECTION_AVOIDANCE_DENSITY_CONTRACT`; `query_prospective_ledger.ts:143`). Admitted under the
last-cheap-chance rule: the trim behaviour is wrong *now*, and it gets more expensive to fix once
downstream L5 surfaces depend on the current shapes.

**N-3 · Pagination honesty (§N.6 items 1 and 4).** `query_auspicious_windows` hard-`LIMIT 100` with
`count: rows.length` — a caller reading `count: 100` on a 134-row chart believes it has everything,
with no cursor and no truncation flag. `query_spillover_cascades` has **no LIMIT at all** on 2,510
rows × ~20 columns, marked `cost_class: 'cheap'` and pre-fetched. `query_rectification` paginates a
total tie with no tiebreak, so page 2 can repeat or skip page-1 rows (§N.7 item 2).

**N-4 · Detector repairs that are not MUST (§N.8).** `ph_sodhana`'s `detect_confidence_degenerate`
guards the one axis that varies while the two ceiling inputs it exists to protect are chart-wide
constants; its LEAKAGE-FIREWALL passes silently on a NULL/empty `confidence_basis`; its G-LADDER
`expected_value_text` narrates a per-anchor calibration over inputs that never vary; `int(n or 1)`
promotes a genuine `0` to `1`. Graded NOW rather than MUST because the *registry* is honest — these
mis-measure, they do not fabricate.

**N-5 · Latent contamination and silent-suppression paths (§N.5; the F-173 precedent).**
`ph_pramana` reads `life_events` with **no `chart_id` predicate** while its docstring asserts the
column does not exist — false since migration 423, and its sibling `ph_rectification` explicitly
firewalls exactly this (JL-017). Latent only because one chart has events. Separately,
`ph_suddha_sodhana`'s `try/except → logger.debug` around its flag read would classify **every** anchor
`clean` on failure — the identical pattern F-173 removed from `ph_pratikara`, which that writer's own
comment now names "the bug pattern."

**N-6 · Leverage the system can already answer (D-TIME; leverage).** `initiation_muhurta_ref` NULL on
100% of rows despite an FK to `phala_muhurta` and 134 live muhurta rows, with an engine comment
saying the writer sets it — it never does. `recommended_tier_jsonb[*].estimated_time_min`
structurally always null because the upstream column is never SELECTed. `subsystem_source` 0/139
because `source_subsystem` is one unselected column away — **the same omission that makes D-7
unreachable.** `trigger_lift = 1.0` justified by "no source anywhere in the codebase" while
`sav_bindhu`/`sav_score`/`sav_threshold` sit in the JSONB the writer already fetched. `ka_gochara`'s
17,240 real transit windows unread behind a docstring that says the table does not exist.

**N-7 · Registry and description truth (B.8).** Row-count claims wrong by an order of magnitude
("phala_sankrama (73 rows)" vs 2,510) propagating into four generated projection files, so a planning
LLM budgets against the wrong number; three `volume_explanation`s describing the wrong asset or the
wrong grain; `ph_sankrama`'s description advertising multi-hop cascades and mitigation routing, both
verified unreachable; stale "7 domain declarations" docstrings; `provides_apis` NULL across the entire
temporal fleet, so **no L4 engine declares its question** (D-TIME condition 1).

**N-8 · Vocabulary drift at the serving boundary (D-SERVICE).** `ph_pratikara` stores a *mapped*
severity vocabulary, so a caller filtering on kala's `mild/moderate/severe` matches nothing,
undisclosed; two different plausible-sounding defaults for the same unknown severity (writer `'low'`,
engine `'medium'`); `phala_mitigation_map` forwards two filters `query_remedy_program` does not accept
and drops both without notice.

**N-9 · `mitigation_ref` / `estimated_time_min` / `linked_sodhana_id` — three advertised fields with
no writer** (§N.8). Either wire them or drop the column *and the claim*. `mitigation_ref` is the
tractable one: `ph_pratikara` → `phala_sankrama.mitigation_ref` is a real, wanted link.

**N-10 · Duplicate/idempotency hygiene.** `phala_anchors_domain_idx` and `idx_phala_anchors_domain`
are byte-identical duplicate indexes (a free drop); `_LINKAGE_THRESHOLD` is defined twice on a number
that appears in the volume formula; `phala_mitigation_natural_key` pins the *derived* `intensity_tier`
when the honest key is `(chart_id, obstruction_id)`.

---

## §5 — NEVER / LATER (logged with reason, closed)

**Closed as design, not defect:**

- **13 and 186 are genuine derived structural constants** with chart-dependent payloads. Repeatedly
  flagged as suspicious across two batches and verified clean in both. Closed.
- **`causal_chain_jsonb` is chart-constant** — correctly documented in code as CONTRACT-3. The field
  *shape* implies per-anchor causality it does not have, but per-anchor CGM causality is a real L2
  modelling question, not an L4 defect. Closed to L2's backlog.
- **`ph_pramana`'s D5 gate being name-based** (it would not catch `score`, `p_hit`, or a value smuggled
  into JSONB). Honest scope, correctly stated in its own docstring. A stronger gate is a P7-programme
  question. Closed.

**Closed as latent-and-masked — record, do not fix blind:**

- **`ph_muhurta`'s engine ignores the writer's career-lord override.** Both live charts have Aries
  lagna → 10th = Capricorn → Saturn = the static default, so the bug is masked on 134/134 rows. It
  will fire on the first non-Aries chart. **Fixing it blind today would be untestable** — there is no
  chart on which the correct and incorrect answers differ. Deferred to the arrival of a third chart,
  with a golden-value test per §N.7 item 5.
- **`ph_suddha_sodhana`'s `informational_count` has no DB column.** A genuine silent-loss path, but no
  detector emits `informational` today, so it cannot be exercised. Recorded against the day one does.
- **`ph_pratikara`'s `obstruction_severity DESC` sort putting `high` last.** Real §N.6 item-2 defect in
  code; neither chart currently has a `severe` obstruction. Folded into the N-2/N-3 serving batch
  rather than treated as its own item.

**Closed as out-of-scope by ownership:**

- **`mimamsa_anchor_adjustment` applies `multiplier = 0.95` to all 195 rows with `evidence_n = 0` and
  `leakage_status = 'not_assessed'`** — a non-neutral numeric adjustment on zero evidence. **L5's
  asset, L5's write-set.** Handed forward in §8 so the P7 programme inherits it rather than
  rediscovers it. Not mine to change.
- **`bodha_cdlm_cells.cell_evolution_gradient_score` is 100% NULL upstream.** My fix (M-10) is to stop
  converting that NULL into a favourable constant — correct regardless. Whether the L2 column *should*
  be populated is `bo_sangati`'s disposition. Handed to L2.

**Closed as measurement, not correctness:**

- **No build-cost measurement exists on any of the nine assets, on either chart** (`rows_per_second`
  NULL, `measurement_count` 0, `history` `[]`), and every `estimated_seconds` is therefore an
  undeclared-provenance number. This resolves itself at W4: the campaign rebuild *is* the first real
  measurement. Recorded as an expected W4 output, not as work.

---

## §6 — W3 batch plan (disjoint write-sets)

Four batches. Batches 1–3 are unheld and proceed now; batch 4 is held per §7.

| batch | write-set | contents | held? |
|---|---|---|---|
| **W3-0 — deterministic anchor identity** | `platform/migrations/680_*.sql`, `writers/ph_nimitta.py`, `services/ph_nimitta/engine.py` | M-31: the one-time remap of the existing 195 cascaded across all nine referencing tables in one transaction; the content-derived `anchor_id`; the D-CND-03 partitioned referential-integrity detector; the C6 announcement that lifts the hold. **Lands first.** | no |
| **W3-1 — registry + migration** | `platform/migrations/680*.sql` – `689*.sql` (my range, collision-free by construction) | The complete §9 registry delta for all nine: `integrity_check_sql`, `expected_volume_formula`, `expected_volume_inputs`, `volume_explanation`, `target_floor`, `catalog_status`, **and every `depends_on` correction in the same migration** per D-L4-08. Plus the `grounding_tier` column and dropping `classical_citation NOT NULL` (M-4), the duplicate-index drop, and the `confidence_low` range CHECK (D/F11). | no |
| **W3-2 — serving plane (TS)** | `platform/src/lib/retrieval/registry/layers/L4_phala/*`, `platform-mcp/src/tools/phala_*.ts` | M-18 (MCP bridging), M-19/M-20 (the three inverted sorts), M-21 (posterior policy), M-23 (`grounds_to`), N-1 (unserved honesty columns), N-2 (density contracts + `hardFloor`), N-3 (pagination honesty), N-7 (description truth), M-25's descriptor correction. | no |
| **W3-3 — writers (Python)** | `platform/python-sidecar/pipeline/orchestrator/writers/ph_*`, `platform/python-sidecar/services/ph_*` | M-1..M-2 (citation propagation + tier), M-5..M-12 (honest nulls + reasons), M-13 (the domain map), M-14 (`rows_inserted`), M-15 (anchor linkage), M-22 (headline selection consults the purification verdict), N-4, N-5, N-6, N-8, N-10. | no |
| **W3-4 — doctrine consumption** | writers + serving, narrow | agreement line, strongest śruti quote, `tail_watch`, varshaphala/tithi-praveśa consumption. | **YES — §7** |

**Sequencing constraints, stated because getting them wrong is expensive:**

1. **W3-1 lands before any W4 dispatch, and `depends_on` removals land inside it** — a registry
   contract change invalidates my own accepted analysis evidence under the dispatcher's
   `registry_fingerprint_sha256` binding, forcing a full W2 re-acceptance for all nine (D-L4-08).
2. **`ph_pratikara`'s rerun (M-17) lands AFTER W3-3, never before.** Rerunning today would replace
   1,277 obviously-empty rows with 1,277 rows carrying *real* remedy content still linked to one wrong
   anchor and still stamped with a fabricated citation — **a worse state than an obviously-empty
   one**, because it would look correct.
3. **`target_floor` is set from `count_sql` after the W4 rebuild, never from `rows_written`** (D-L4-07,
   §N.4). M-14 is the live proof.
4. **`ph_pramana`'s `target_floor` stays NULL until M-5 is fixed** — a floor set now would enshrine a
   count a dead detector produced.

**One cross-session write-set risk, declared rather than discovered:**
`platform-mcp/src/lib/kala_upaya_diagnosis.ts` and `platform-mcp/src/tools/kala_views/upaya.ts` carry
**Kāla tool names while serving L4 `phala_mitigation` data**, and M-2's fix lives there. Likewise
`kala_elect_get` / `muhurta_finder.ts` are documented as **asset PH-4-4** — an L4 asset behind an L3
name. I have not touched either and will not until L3 and I agree who owns them; the C6 declaration in
§8 states this so L3 does not discover it as a merge conflict.

---

## §7 — Held items (charter C6)

| # | held W3 item | waits on | why it cannot proceed |
|---|---|---|---|
| **H-1** | one agreement line per verdict | **L2** — `bo_samvada` populating `system_convergence_count` / `cross_system_consensus_count` | The columns exist and are unpopulated. An agreement line written now would have nothing to agree about, and D-SYNTHESIS forbids a verdict layer that looks populated but is hollow (§N.6 item 3). |
| **H-2** | strongest śruti quote per verdict | **L2** — `grounding_tier` + `classical_sources_array` on the interpretive signal classes | `grep -rl grounding_tier` returns **no matches anywhere in the codebase**. Quoting before the matcher exists would mean selecting a quote by proxy — the exact defect M-2 is about. |
| **H-3** | `tail_watch` in outlooks | **L2** — `low_salience_high_consequence` promoted to a first-class serving input | `grep -rl tail_watch` → no matches. **The L4 population is already identifiable** (the `life_event_miss` rows; the 6 zero-anchor domains carrying 170–315 incoming spillovers), so this unblocks fast once L2 lands. |
| **H-4** | varshaphala / tithi-praveśa consumption into anchors (D-7) | **L3** — tithi-praveśa verification landing | The three upstream tables are built. The plumbing gap is one unselected column (`bodha_msr_signals.source_subsystem`). Consuming an unverified temporal surface into predictive anchors is exactly the authority inversion §N.5 exists to prevent. |

**Productive-wait work already done against these** (charter C8.5): the `tail_watch` population is
identified and quantified (H-3); the D-7 plumbing gap is traced to a specific line (H-4); the
grounding-tier assignment per output class is derived and written down for all of `ph_pratikara`'s
remedy classes and all seven of `ph_nimitta`'s output classes (H-2). Each lands within hours of its
capability unlocking rather than starting from analysis.

---

## §8 — Contract and capability declarations (C6)

### What L4 CONSUMES from upstream (the four holds above)

Polling `origin/main` for a `## CAPABILITIES LANDED` section in `L2_STATE.md` and `L3_STATE.md` each
loop.

### What L4 PUBLISHES for downstream (L5 Mīmāṃsā is my only consumer)

*(none yet — will be announced in `L4_STATE.md` under `## CAPABILITIES LANDED` with PR numbers as
W3 lands.)* Two are already scoped: a `grounding_tier` vocabulary on `phala_mitigation` (M-4), and
`phala_phaladesa` / `phala_pramana` becoming MCP-reachable (M-18).

### What L4 HANDS ACROSS to other sessions (not mine to fix)

| to | item | evidence |
|---|---|---|
| **L5** | `mi_bhavisya.py:178` writes an **anchor_id into `source_pramana_id`** (`anchor_id,  # source_pramana_id`). 195/195 resolve as `phala_anchors.anchor_id`, 0/195 as `phala_pramana.pramana_id`, both written in the same build 8 s apart — never staleness. Five generated projections advertise the ph_pramana link. | D/F4 |
| **L5** | **No FK anywhere on the P7 seam.** `phala_pramana.anchor_id` is `ON DELETE CASCADE` from a delete-then-insert parent, so `ph_nimitta`'s next rebuild silently orphans all 195 predictions and 195 anchor adjustments — no constraint, no cascade, no detector. **This fires at my own W4.** I am landing the *detector* (§9); the seam repair is L5's. | D/F5 |
| **L5** | `mimamsa_anchor_adjustment.multiplier = 0.95` on all 195 rows with `evidence_n = 0`. | D/F20 |
| **L2** | `bodha_cdlm_cells.cell_evolution_gradient_score` is 100% NULL across 280 and 75 cells — disposition needed (by design, or unbuilt?). My M-10 fix is correct either way. | B/F2 |
| **L2** | The CDLM domain vocabulary and the L4 anchor vocabulary genuinely diverge on `wealth` (26 anchors, 0 cells). An honest empty, but nothing records it. | B/§B8 |
| **L2** | `bo_upaya`'s `classical_sources_jsonb` / `citation_ref` / `citation_human` / `estimated_time_minutes_daily` / `phase_duration_days` are populated on 135/135 rows and entirely unpropagated downstream — L4 will start consuming them in W3-3. | C/F6 |
| **L3** | **The election seam.** Four live surfaces answer election-adjacent questions (`ph_muhurta`, `kala_elect_get`/PH-4-4, `gochara_election_avoidance_get`, `ka_vighnakara`); **no arbiter exists anywhere** — `grep partially_aligned|adjudicated_by|temporal_concordance` returns 0 matches across all three trees. `kala_elect_get` declares itself "the SOLE server of Mode 3" and has never heard of `phala_muhurta`; the only wire between them queries three columns that do not exist and has been dead since the schema changed. **The fix is not to merge them — it is to declare each engine's question and stand up one arbiter.** D-TIME's contract is 0% implemented for this domain. | B/§C, F-3, F-4 |
| **L3** | Write-set overlap to agree before either of us touches it: `kala_upaya_diagnosis.ts`, `kala_views/upaya.ts`, `kala_views/elect.ts`, `muhurta_finder.ts` — Kāla names over L4 assets. | §6 |
| **Conductor** | #1718, #1723 (campaign-blocking, 81/128 assets), #1725, #1739. | §3.5, W1 |

---

## §9 — The C12 registry delta (all nine, exact)

Every value below is **derived**, and every proposed check is a **real invariant** — cross-table
FULL-JOIN consistency, fingerprint distinctness, ordering contiguity, no-gap tiling, or a
re-derivation — plus a derived-or-floor volume expectation. **No bare `count(*) = N` equality pin
appears anywhere in this delta** (C12: "an equality wearing a floor's name").

| asset | `expected_volume_formula` | `target_floor` | headline invariants |
|---|---|---|---|
| `ph_nimitta` | `Σ_domain min(50,|kala_convergence(d)|) + |kala_bhavishya| + min(100,|bodha_discoveries|)` less clip/dedup attrition | from `count_sql` post-W4 | FK resolution; attrition disclosed rather than stdout-only |
| `ph_muhurta` | `count(DISTINCT (map_domain_to_action(domain), normalized_start))` over influenceable anchors | from `count_sql` | no-silent-drop (an absent key must be a *duplicate*, never a *missing* one); `window_start <= window_end`; verdict liveness |
| `ph_sankrama` | `Σ_d anchors(d) × cells(domain_row = map(d), linkage ≥ 0.25)` | from `count_sql` | **tiling with no gaps/overlaps — the single invariant that catches all 250 destroyed rows**; §N.5 drift check (L4 must not have drifted from the L2 value it copied); vocabulary closure (fails today on `general`, which is the point) |
| `ph_sodhana` | `BETWEEN 0 AND (5 × n_anchors) + 1` — **a ceiling, not a floor** | **none, deliberately** | firewall earned-signal; chart-scope integrity (the FK omits `chart_id`); ceiling re-derivation; detector-input non-degeneracy |
| `ph_suddha_sodhana` | `= n_anchors` (derived equality against a live upstream count) | from `count_sql` | no-gap tiling both directions; status re-derivation; cross-table flag-count consistency; the D43 rail |
| `ph_pratikara` | `= n_obstructions` — **not anchors** | from `count_sql` **post-rerun** | tiling over `kala_obstruction`; anchor-link non-degeneracy; programme non-emptiness; **citation provenance** (no citation may be asserted that does not trace to a prescription actually scheduled on that row) |
| `ph_pramana` | `= count(phala_anchors)` | **NULL until M-5 is fixed** | FULL-JOIN one-row-per-anchor; grain assertion; `window_status` agreement as of `computed_at`; D5 re-asserted in SQL; **"a `life_event_miss` must cite a resolvable LEL comparison" — fails 12/12 today** |
| `ph_phaladesa` | `card(canonical_domains)` | **13** | complete non-duplicated tiling of the canonical vocabulary; `anchor_count` equals the true population; `top_anchor_id` present iff `anchor_count > 0` and resolves |
| `ph_rectification` | `(floor(2·half_width/step)+1) × card(ayanamshas) + 1` | **186** | contiguous gap-free symmetric lattice; complete cross-product; **fingerprint distinctness across charts** (the chart-independence detector this asset lacks); confidence must be a probability band (fails today at −0.2); **"`load_bearing` may not be true on a non-discriminating fit" — fails 1/1 today** |

**Two checks fail on the real defect today, deliberately.** C12's rewrite floor test says a
replacement check must be able to fail on real corruption the old one could not detect. `ph_pramana`'s
LEL-citation invariant and `ph_rectification`'s discrimination invariant do exactly that, right now,
on live data — which is the proof they are gates rather than proposals. They land **with** their
fixes, not before, so no asset is left holding a knowingly-red gate.

**Also in W3-1 (a note on the ADJ-L4-02 dependency):** every check above is written **chart-agnostic**
(quantified over all charts) because the freeze-time detector executes with no parameters — the
finding filed as #1723. That quantification is a weaker *attribution* ("some chart is broken", not
"this one is") and I am labelling it as such in each `volume_explanation` rather than letting it read
as chart-scoped. If the Conductor rules differently on #1723, these checks are re-scoped, not rewritten.

---

## §9.5 — C13 / D-CND-15 downstream blast-radius review (added 2026-09-05, post-#1770)

Charter C13 and D-CND-15 require, before any dispatch, the transitive `ON DELETE CASCADE` closure
of every table a writer deletes from — because **the campaign's DAG models ancestors and the E-gate
gates on ancestors, while CASCADE makes descendants a destruction surface that nothing in the E-gate,
the slot protocol, or a writer's own idempotency helper models.**

**First, the direct answer to "which routes assumed `rebuild_only` was safe by default": none.**
All nine L4 assets route `changed` (§1), so no route rested on a rebuild-is-safe assumption. That is
luck rather than foresight, though — the routes are `changed` because every asset has a MUST
correctness finding, not because anyone had modelled the destruction direction. The statement below
is the modelling that was missing.

**Method.** `pg_constraint` where `contype='f' AND confdeltype='c'`, followed transitively to depth 6,
over every table each L4 writer deletes from. Each writer's `DELETE` targets were read from source,
not assumed: eight delete from their own single target table; `ph_rectification` deletes from
`phala_rectification` and `phala_rectification_best`.

| # | asset | deletes from | CASCADE descendants | crosses a layer? |
|---|---|---|---|---|
| 1 | **`ph_nimitta`** | `phala_anchors` | **`phala_sankrama` 2,985 · `phala_pramana` 195 · `phala_suddha_sodhana` 195 · `phala_sodhana` 138** | **no — all L4** |
| 2 | `ph_muhurta` | `phala_muhurta` | none | no |
| 3 | `ph_sankrama` | `phala_sankrama` | none | no |
| 4 | `ph_sodhana` | `phala_sodhana` | none | no |
| 5 | `ph_suddha_sodhana` | `phala_suddha_sodhana` | none | no |
| 6 | `ph_pratikara` | `phala_mitigation` | none | no |
| 7 | `ph_pramana` | `phala_pramana` | none | no |
| 8 | `ph_phaladesa` | `phala_phaladesa` | none | no |
| 9 | `ph_rectification` | `phala_rectification`, `_best` | none | no |

**8 of 9 L4 writers delete from a table that is a CASCADE parent of nothing.** `ph_nimitta` is the
sole exception, and its four cascade children are all L4's own — regenerated by the layer's own W4
cascade. **No L4 delete cascades outside L4.**

### The cross-layer surface is an ORPHAN surface, not a cascade

Two referrers to `phala_anchors` carry **no FK**, so they dangle rather than cascade — the harder
failure to detect, since nothing errors:

| referrer | rows | layer |
|---|---:|---|
| `phala_phaladesa.top_anchor_id` | 13 | L4 (in-layer) |
| **`mimamsa_predictions.source_pramana_id`** | **195** | **L5 — crosses the boundary** |

That is exactly the D-CND-04 hazard, and it is already held. **The closure confirms the hold is
correctly placed rather than merely assuming it was.**

### Two things this review changes

1. **`phala_anchors` is reachable by CASCADE from L2**, not only from `ph_nimitta` —
   `bodha_msr_signals → kala_convergence → phala_anchors → {4 L4 children}`. So W3-0's deterministic
   `anchor_id` gains a second, stronger motivation than the one it was built for: after an L2 rebuild
   empties the table by cascade, re-running `ph_nimitta` restores **the same ids**, so L5's 195
   pointers resolve again by construction. With random ids they never would. It makes the L4 tail
   *regenerable* rather than merely re-creatable.
2. **`phala_anchors.signal_id` (188 rows) is one of the campaign's no-FK five** and orphans on an L2
   MSR rebuild. **Disposition: no repair, by design.** It is a provenance pointer to the signal
   generation an anchor was derived from; if that generation is replaced, the honest state is a stale
   pointer, not a silently re-aimed one. What it needs is a detector, not a fix — W3-0's referential
   check is extended to cover it once #1748 settles whether `signal_id` becomes stable.

### An honest limit of this review

The closure was computed from `pg_constraint`, which is authoritative for CASCADE. It does **not**
find referrers that carry no FK — those had to be enumerated by column-name search, which is a
heuristic. I found two for `phala_anchors` (above) plus `signal_id`; a referrer under an
unguessable column name would not appear. That is the same class of gap that let #1748 under-grade
the L2 hazard, so it is stated rather than left implicit.

---

## §10 — Decisions ledger (this wave)

- **D-L4-05** — M-1..M-4 fixed as one unit; the citation is **propagated by reference** from
  `bodha_rm_remedy_prescriptions`, never restated (§N.5); an honest `yukti`/`pratyaksa` tier is the
  success condition, not a downgrade.
- **D-L4-06** — every unearned signal resolves to **an honest null plus a stored reason**, never to a
  repaired-looking value; and no fix may silently convert "0 misses" into "0 matches" without the
  disposition being visible (§N.7 item 6).
- **D-L4-07** — `target_floor` is set from `count_sql`, never from `rows_written` (§N.4). M-14 is the
  live proof this matters.
- **D-L4-08** — `depends_on` removals land in the **same migration** as the C12 delta, before any W4
  dispatch; a registry contract change invalidates my own accepted analysis evidence.
- **D-L4-09** — `ph_pratikara`'s rerun lands **after** its writer fixes. An obviously-empty asset is a
  safer resting state than a plausible-looking wrong one.
- **D-L4-10** — M-25 (the P7 seam) and M-26 (the D5 gate) are **verify-only**. I am landing a detector
  for the orphan risk and correcting a false descriptor; I am not rewiring L5 or completing a
  deliberately-structural calibration surface.
- **D-L4-15** — C13/D-CND-15 closure computed for all nine (§9.5). No L4 delete cascades outside
  L4; the one cross-layer surface is an orphan surface already held by D-CND-04. **No route assumed
  `rebuild_only` was safe by default — all nine are `changed`** — but that was not the result of
  modelling the destruction direction, and §9.5 is the modelling that was missing.
- **D-L4-16** — my #1748 grading ("accretion, not orphaning; no hold warranted") is **WITHDRAWN**.
  L2's #1770 is correct: `bodha_msr_signals` replaces via an explicit DELETE, and all eight FKs are
  CASCADE. I inferred a system property from one mechanism, and my own row arithmetic contradicted
  my conclusion in the sentence I wrote it in. Corrected on both issues.
- **D-L4-12** — the deterministic anchor key is **content-derived, not row-id-derived**; the obvious
  form was verified non-deterministic before being built, and the uniqueness of the chosen form was
  measured across 35,365 live rows rather than assumed.
- **D-L4-13** — W1's grading of the orphan risk as *verify-only, handed to L5* is **withdrawn**; L4
  owns it. Recorded as a correction rather than silently re-graded.
- **D-L4-11** — all nine route `changed`, and I am saying so plainly rather than routing the cleanest
  asset `rebuild_only` to make the layer look cheaper.
