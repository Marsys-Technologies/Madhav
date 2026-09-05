---
artifact: L5_W2_DECIDE_v1_0.md
canonical_id: NIRMANA_L5_W2_DECIDE
version: "1.0"
status: CURRENT — W2 DECIDE output, L5 (Mīmāṃsā)
session: L5
produced_on: 2026-09-05
campaign_id: nirmana-elevation
definition_revision: t0-2026-09-01-0e5b06fb
inputs:
  - L5_W1_ANALYSIS_BATCH_A.md (lel_events, mi_jivanaghatana, mi_bhavisya, mi_pramana)
  - L5_W1_ANALYSIS_BATCH_B.md (mi_abhilekha, mi_pariksha, mi_sambandha, mi_darshana)
  - L5_W1_ANALYSIS_BATCH_C.md (mi_kula, mi_gunanaka, mi_adhilepa, mi_bhara)
  - L5_W1_ANALYSIS_BATCH_D.md (mi_vistara, mi_seva, mi_sankalpa)
authority: >
  Charter C3 (decide yourself and log; escalate cross-layer/shared-surface items to the Conductor
  by adjudication issue and continue). Plan §4 W2 (one route per asset; every finding triaged
  MUST/NOW/NEVER-LATER with a doctrine citation).
---

# L5-W2 — DECIDE: routes, triage, and the two deviations I am logging

**Finding-ID namespacing.** The four W1 batches numbered their findings independently, so `L5-F-01`
occurs in three of them. Throughout this document findings are cited **batch-prefixed** — `A-F-15`,
`B-F-14`, `C-F-05`, `D-F-D09` — and that is the canonical form for the rest of the campaign.

---

## §1 — The headline decision: **no L5 asset takes `verified_reuse`**

Plan §5's L5 paragraph forecasts "Routes: mostly `verified_reuse`/`static` against existing build
evidence." **On the evidence, that forecast is wrong, and I am deviating from it deliberately.**

`verified_reuse` requires (prompt §6.2) "full digest lineage + integrity + consumers proven."
The lineage demonstrably does not hold:

- The **last successful L5 build was 2026-08-12/13.**
- Three narration-fidelity fixes merged **after** it: F-143 (`ca9214f2c`, 2026-08-21), F-147
  (`44f42fe94`, 2026-08-21), F-148 (`e5ef0bc66`, 2026-08-22).
- The **2026-08-21 rebuild was BLOCKED** and never completed (`asset_throughput.last_error`).
- So every served row carries a formula version *behind* its writer's HEAD: `mi_darshana_v1.0` vs
  code `v1.2` on 150/150 insight units; `mi_sambandha_v1.0` vs code `v1.2` on 47/47 grammar rows.

The layer is therefore **serving today the exact defective sentences those PRs were merged to
remove** — verifiable verbatim in `mimamsa_insight_units.statement`:

> *"For career events, the 'ch_career_verbal' channel fires with 0% propensity (n=37, empirical
> learning)."*

That is the sentence F-147's addendum exists to prevent. And 10 `mimamsa_manifestation_grammar` rows
carry `evidence_grade='empirical'` with `scored_count = 0` — the "measured, and it never fires"
invention the same fix replaced with an honest NULL.

**A `verified_reuse` capsule against this data would certify text the codebase itself has
repudiated.** That is not a reuse proof; it is a broadcast of a known-stale claim, and §N.8 forbids
it. Every asset therefore routes `changed` or `rebuild_only`, and `lel_events` alone routes `static`
(it has no writer and no build to reuse).

**Consequence the Conductor should price in:** L5 was forecast as the cheap closing layer. It is
not. It needs a real rebuild pass, and that pass is gated behind L1–L4 ancestor freezes (26–55
unfrozen ancestors per asset) plus adjudication **#1732**. I have raised this as a cost-forecast
note, not as a request for relief.

---

## §2 — Routes (one per asset, all 15)

| # | asset | route | one-line justification |
|---|---|---|---|
| 1 | `mi_vistara` | **`rebuild_only`** | **CANARY 1.** Zero deps, two-statement writer, measured 0.287s mean over 39 runs, already terminates honestly at 0 rows. Dispatch via `scope='asset'` (D-F-D01). Captures the campaign's **first `mi_*` provenance receipt**. |
| 2 | `lel_events` | **`static`** | **CANARY 2.** No writer, no build, structurally undispatchable by the wave dispatcher (`execution_obligation='build'` filter). Terminal evidence is a reconciliation + clear-protection proof, emitted as `source_accepted`. `empty` would be wrong — the corpus is populated and load-bearing. |
| 3 | `mi_jivanaghatana` | **`changed`** | **CANARY 3, demoted from 1st.** Its `expected_volume_formula` is wrong on three counts (A-F-09) and `admissible_clean` is an unearned flag (A-F-10). Registry + a two-line writer fix must land before its capsule can be truthful. |
| 4 | `mi_kula` | **`changed`** | Two families carry `CLASSICAL_CITED` while citing MARSYS-internal documents (C-F-01) — a row-value correction needing a writer edit + global re-seed. Dispatch `scope='global'`, `chart_id=NULL`. |
| 5 | `mi_sankalpa` | **`rebuild_only`** | Writer is complete and correct; `target_floor IS NULL` (D-F-D15) must land **first**, else the build re-asserts the wrong `dormant` state. |
| 6 | `mi_seva` | **`rebuild_only`** | **Explicitly not `probe`** — the probe path is unreachable through four independent gates, so routing it `probe` would claim a verification mechanism that does not exist (D-F-D09/D10). |
| 7 | `mi_bhara` | **`changed`** | Registry-only MUSTs: `target_table` names a table it has never written (C-F-21). No writer edit needed. |
| 8 | `mi_bhavisya` | **`changed`** · **HELD** | Held on **#1732**: rebuilding before `anchor_id` is deterministic *executes* the provenance loss the mandate forbids. |
| 9 | `mi_pramana` | **`changed`** · **HELD** | Same hold. Also the STRUCTURAL-mode documentation route (A-F-27) — corrections that move **no number**. |
| 10 | `mi_abhilekha` | **`probe`** | Produces no rows by design; what it needs is a real GREEN health probe (B-F-03), not a rebuild. Unlike `mi_seva`, a truthful probe claim exists for it. |
| 11 | `mi_gunanaka` | **`changed`** | Three literal-valued flags with no detector (C-F-05) live in stored rows — a writer edit plus a per-chart rebuild. |
| 12 | `mi_pariksha` | **`rebuild_only`** | Row correctness needs no writer change; the MUSTs are one serving-plane fix (B-F-07) and one small guard (B-F-08). Canonical data is `state='error'` and must re-run regardless. |
| 13 | `mi_adhilepa` | **`changed`** | `role`/`sensitivity` report rank as measurement (C-F-13); the convergence overlay silently samples 500 of 14,868 with no ORDER BY (C-F-14). |
| 14 | `mi_sambandha` | **`changed`** | The one asset where `verified_reuse` would be *actively* wrong: stored rows carry an unearned `empirical` grade the current code cannot produce (B-F-14). |
| 15 | `mi_darshana` | **`rebuild_only`** | Writer is already correct at HEAD; what is wrong is that no build has run since the fixes merged (B-F-21). |

**Route totals:** `changed` 8 · `rebuild_only` 5 · `probe` 1 · `static` 1 · `verified_reuse` **0**.

---

## §3 — Deviation 2: canary ORDER changed, with reasons

My session prompt nominated the canary order **`lel_events` → `mi_jivanaghatana` → `mi_vistara`**.
W1 evidence inverts it. I am running **`mi_vistara` → `lel_events` → `mi_jivanaghatana`.**

- **`mi_vistara` moves to first.** It is the cheapest possible first execution in the entire campaign
  (0.287s measured), has **zero dependencies**, needs **no code change to build**, already
  demonstrated an honest `lit`-at-0-rows termination, and would capture the first provenance receipt
  any `mi_*` asset has ever had. If the cross-layer gate has a defect, this is the cheapest possible
  place to discover it.
- **`lel_events` moves to second.** Still valuable — it is the campaign's only `source_acceptance`
  obligation and has **zero precedent events in history** — but it is a *disposition*, not an
  execution, so it proves the evidence path and not the build path. It is also fully blocked by
  **#1719** until the receipt spine is generalised.
- **`mi_jivanaghatana` moves to third.** W1 disqualified it as a clean canary: its volume formula is
  wrong (A-F-09) and `admissible_clean` is an unearned flag on 64/64 rows (A-F-10). Running it before
  those land would produce a capsule asserting a volume expectation that is false and a leakage flag
  no code path can falsify. It becomes a good canary *after* its W3 items, not before.

---

## §4 — Findings triage

### §4.1 — MUST (correctness; gates the capsule)

| id | asset | finding | doctrine |
|---|---|---|---|
| A-F-15 | `mi_bhavisya` | `anchor_id` churn destroys the P7 provenance chain on any L4 rebuild — **escalated #1732** | plan §0 P7 parking clause; §N.5 |
| A-F-16 | `mi_bhavisya` | `frozen_bundle_hash` mixes `emitted_at` — a per-run nonce, not a fingerprint; defeats WP-1/WP-2 | §N.8; O-wave §3.1/§3.2 |
| A-F-17 | `mi_bhavisya` | 4 false `depends_on` edges — the canonical build **actually failed** on two of them | rubric 2; WP-3 |
| A-F-01 | `mi_jivanaghatana` | `depends_on` omits `lel_events`, its sole source — LEL appends can never mark it stale | rubric 2; WP-1 |
| A-F-02 | `lel_events` | LEL→DB intake drops `magnitude`; root cause of constant `score_magnitude=0.5` | §N.7 item 6; C12 |
| A-F-03 | `lel_events` | A demo row is live ground truth for calibration, `admissible_clean=true` | hard floor §3.6; §N.8 |
| A-F-08 | `mi_jivanaghatana` | `event_class_id` NULL 64/64 — swallowed exception on a non-existent column | §N.8; §N.7 item 4 |
| A-F-09 | `mi_jivanaghatana` | `expected_volume_formula` wrong on three counts; names a source the writer does not read | C12 |
| A-F-10 | `mi_jivanaghatana` | `admissible_clean` true 64/64; **no code path can produce false** — a leakage firewall with every gate un-wired | §N.8 verbatim |
| A-F-23 | `mi_pramana` | `held_out_validity='pass'` over a sample from which held-out rows are excluded by construction | §N.8; §N.7 item 4 |
| A-F-24 | `mi_pramana` | `brier_vs_null` computed against an **invented** 0.10 prior on 57/57 rows | §N.8 (absolute here) |
| A-F-25 | `mi_pramana` | `_score_domain` compares two unreconciled vocabularies — 47/57 rows score 0 on a naming mismatch | §N.7 item 1; C12 |
| A-F-26 | `mi_pramana` | **Seal gate G8 is a false PASS** — `structural_no_calibration` exists in no code | §N.8; C12 |
| A-F-27 | `mi_pramana` | STRUCTURAL justification stale + its stated evidence now false — **mandate item 1** | plan §5 L5 item 1 |
| B-F-01 | `mi_abhilekha` | The journal seam has **no writer anywhere in the repo** | §N.8; hard floor §3.6 |
| B-F-02 | `mi_seva` | Docstring asserts two behaviours the code does not have | §N.7 item 1 |
| B-F-07 | `mi_pariksha` | `qa_fail_count` exact-matches `'FAIL'`, missing 61 live `'FAIL_event_too_close'` rows | §N.8; §N.6 item 1 |
| B-F-08 | `mi_pariksha` | `degenerate_distribution` passes on a chart with **zero** calibration rows | §N.8; §N.7 item 6 |
| B-F-13 | `mi_sambandha` | Prior channel vocabulary has **zero intersection** with the channels that exist | §N.7 item 3; §N.8 |
| B-F-14 | `mi_sambandha` | 10 live rows carry `empirical` with `scored_count=0` — the defect the merged fix removed | §N.8; §N.7 item 6 |
| B-F-20 | `mi_darshana` | Insight-embedding serve path built, producer absent — **mandate item 4** | plan §5 L5 item 4; B.10 |
| B-F-21 | `mi_darshana` | 150/150 rows predate three merged narration fixes; serving repudiated text | §N.7 items 1 & 6 |
| C-F-01 | `mi_kula` | Two families badged `CLASSICAL_CITED` citing MARSYS-internal documents | D-GROUNDING; §N.7 item 6 |
| C-F-05 | `mi_gunanaka` | `gate_passed` / `held_out_validity` / `neg_control_clear` are Python literals | §N.8; §N.7 items 4, 6 |
| C-F-06 | `mi_gunanaka` | Seal's "all 9 prior_only" is factually false live (2 promoted) | §N.8; mandate item 1 |
| C-F-07 | `mi_gunanaka` | `compute_spine_bundle` filters on an always-NULL column, zeroing a section forever | rubric 3; §N.6 item 3 |
| C-F-13 | `mi_adhilepa` | `role`/`sensitivity` report list rank as measurement; the one evidenced family is excluded | §N.8; §N.7 item 2 |
| C-F-14 | `mi_adhilepa` | `LIMIT 500` with no `ORDER BY` over 14,868 rows — silent nondeterministic 3.4% sample | §N.6; §N.8 |
| C-F-21 | `mi_bhara` | `target_table` names a table with zero write callers; `count_sql` already counts another | §N.8; WP-3 |
| C-F-22 | `mi_bhara` | L3↔L5 shared-surface arbitration needed on `kala_field_weight_versions` | C12; plan §4 W3 |
| D-F-D01 | `mi_vistara` | A `scope='layer'` dispatch silently assigns it `out_of_domain` — the canary would not build | WP-3 |
| D-F-D08 | `mi_seva` | Registry contradicts seed **and** regresses sealed gate G11 | §B.8/GA.1; §N.8 |
| D-F-D09 | `mi_seva` | Degradation reported via `notes`, which nothing reads — **escalated #1738** | §N.8 |
| D-F-D15 | `mi_sankalpa` | `target_floor IS NULL` → perpetual `dormant` re-queue; migration 364 predates it | §N.4; §N.8 |
| D-F-D16 | `mi_sankalpa` | Stale in-repo comment asserts no write path exists; one does | §N.7 item 1; C12 |

**34 MUSTs.** Every one is either a stale-data rebuild, a signal with no possible failure path, an
unearned grade at rest, or an honest recording of a seam that does not exist. **None is fixed by
inventing a value, and none is fixed by weakening a check.**

### §4.2 — NOW (in-layer improvement; admitted by clear value and bounded cost)

Grouped, since they land as batched PRs on disjoint write-sets:

- **W3-1 Registry corrections** (no writer edits): `expected_volume_formula` derivations for
  `mi_jivanaghatana` (A-F-09), `mi_gunanaka` (C-F-10), `mi_adhilepa` (C-F-15), `mi_bhara` (C-F-23),
  `mi_vistara` (D-F-D03), `mi_sankalpa` (D-F-D21), `mi_pariksha` (B-F-11); `target_floor` fixes
  (D-F-D15, C-F-23); `target_table` correction (C-F-21); false/hidden `depends_on` edges (A-F-01,
  A-F-17, B-F-10, B-F-16, B-F-22, C-F-02, C-F-11, C-F-16, C-F-24, D-F-D11, D-F-D17);
  `estimated_seconds` corrections (B-F-11, C-F-17).
- **W3-2 `integrity_check_sql` proposals** — all 15 assets are NULL today. Per C12 each proposal is a
  **proposal, not a gate**, must be a real invariant (never `count(*) = N`), and must pass the
  rewrite floor test. Candidates authored per asset: A-F-06, A-F-13, A-F-31, B-F-11, C-F-04, C-F-10,
  C-F-18, C-F-26, D-F-D02, D-F-D19. **Where a check passes vacuously on an empty table (D-F-D02,
  D-F-D19), that sentence ships with it into the capsule.**
- **W3-3 Serving-plane honesty (TS, no freeze exception):** `empty_reason` + `density_contract`
  sweep across the L5 capabilities — **zero of 16 declare a `density_contract`** (L1 has 8, L2 4,
  L4 2) and only 8/16 have `empty_reason`, with all three headline P7 surfaces in the missing half
  (A-F-04, A-F-21, A-F-32, B-F-18, B-F-25, C-F-05a). Plus `compute_spine_bundle` (C-F-07),
  `qa_fail_count` (B-F-07), `buildEfficacyReport` nulls (D-F-D18), the dead
  `abhilekha-resync` POST (B-F-05), the `calibration_mode` vocabulary (D-F-D05).
- **W3-4 Narration/label corrections that move no number:** A-F-28, A-F-29, A-F-30, B-F-04, B-F-15,
  B-F-17, B-F-23, B-F-24, C-F-08, C-F-09, C-F-25, D-F-D07, D-F-D10, D-F-D14, D-F-D20; plus the
  stale-hardcoded-count sweep (A-F-05, A-F-18) across four surfaces that all say "50" or "57" while
  live values are 139/56 and 64.
- **W3-5 Idempotency scars:** `mi_pariksha`'s `neg_control` DELETE also wipes `tail_only` rows and
  survives only on substep ordering (B-F-09) — §N.3.

### §4.3 — NEVER / LATER (logged with reason, closed)

Every item here would **add calibration or learning machinery**, which plan §5's L5 mandate places
out of scope and plan §7.3 already parks. Recorded, not actioned:

| id | item | deferred-register citation |
|---|---|---|
| A-F-07 | LEL data-ization / richer intake schema | §7.3 "LEL data-ization" |
| A-F-14 | Restore a markdown-source branch / re-pin `lel_file_sha` | §7.3 — and it would reopen the cross-chart leakage hole the v2.0 rewrite closed |
| A-F-22 | Reconcile the two prediction stores | §7.3 — duplication **already** explicitly dispositioned; D-TIME item 4 is satisfied |
| A-F-33 | Real ECE / log-loss / CIs / outcome intake / per-class base rates / **calibration-history table** | §7.3 "journal/outcome intake, retrodiction pass" |
| B-F-06 | The journal *producer* | §7.3 "journal/outcome intake" |
| B-F-12 | Making ablation/tail_only real; synthetic-injection negative controls | §7.3 |
| B-F-19 | Genuine channel priors; widening the channel vocabulary | §7.3; multi-chart |
| B-F-26 | Splitting `verdict_object`'s grounding tier from its derivation tier | D-GROUNDING workstream, spans L2→L5 |
| C-F-05b | `prior_source` provenance column | §7.3 — path is dormant today |
| C-F-12 | Hold-out scorer, negative-control harness, real leakage detector | §7.3 |
| C-F-20 | A genuine sensitivity analysis behind `mi_adhilepa` | §7.3 — in-scope fix is honest **relabelling** |
| C-F-27 | Wiring `insert_weights_version` | §7.3 / ṢAḌ-DARŚANA; the refusal to fabricate a basis is **correct** and is recorded as deliberate |
| D-F-D06 | Export→ledger write path | §7.3 |
| D-F-D13 | The `mi_seva` serve-time resolver | §7.3 |
| D-F-D22 | MCP read path + `state:'computed'` efficacy branch | §7.3 "remedy-efficacy ledger" |

**One determination worth recording explicitly:** `mi_sankalpa` is **not** §7.3's parked
"remedy-efficacy ledger." It is the *substrate* (attestation tier, arm assignment, outcome links);
the parked item is the *analysis over* it (`buildEfficacyReport`'s absent `computed` branch). The two
share a name in casual use, and conflating them would have wrongly parked a live, tested,
correctly-guarded write path.

---

## §5 — Mandate scorecard (plan §5, L5's five items)

| # | mandate item | status after W1/W2 |
|---|---|---|
| 1 | STRUCTURAL mode re-documented as **deliberate** | **Determined, not yet written.** The seal's justification is stale (its precondition "L4 sealed" cleared two days later) and its stated evidence is false (2 promoted multipliers, not 0). The honest justification: *no prediction in the instrument has a recorded outcome* — 195/195 `pending`, journal empty, no outcome column — **and** P7 is PARKED. Lands in W3 as A-F-27 + C-F-06 + the seal-record correction A-F-26. |
| 2 | Prediction provenance retention **verified** | **VERIFIED HEALTHY — with one live threat.** Every field retained (what generated it, from which facts, which window, what confidence); referential integrity perfect, 0 orphans on all four links. The threat is A-F-15 (`anchor_id` churn), escalated as **#1732**. |
| 3 | Journal / adjudication-log seams **confirmed intact** | **CONFIRMED, with precision.** *Journal:* schema ✓, read/serve ✓, build-drain ✓, **append path does not exist** — empty because unwritable, not because parked. *Adjudication:* `mimamsa_adjudication_log` written correctly behind a real permission gate, but **nothing reads `verdict_mapped` back into L5**; the one bridge targets an unregistered sidecar route and 404s silently. Intact structurally, severed functionally. 0 rows, so nothing is lost yet. |
| 4 | Insight-embedding serve path **noted** | **NOTED in full (B-F-20):** schema+index DONE; serve path DONE and honest (it refuses to embed a query string it cannot honestly embed — B.10 conduct to preserve); **producer MISSING**; **MCP reachability MISSING**. Embeddings are always zero after any build by construction, since the insight substep DELETEs them. |
| 5 | **No calibration values invented** | **HELD ABSOLUTE.** Not one finding proposes filling, adjusting, or "correcting" a calibration value. Where evidence is absent the recommendation is an honest NULL or a rename to what the field actually measures (A-F-10, A-F-23, A-F-24, C-F-05, C-F-08, D-F-D18). Three existing pieces of §N.8 conduct are flagged for **verbatim preservation**: `mi_pariksha`'s `structural_proxy`/`not_implemented` statuses, `mi_sambandha`'s `_PROPENSITY_UNMEASURED` null, and `query_insight_embeddings.ts`'s refusal to embed. |

---

## §6 — Contract / capability-delta list (charter C6), published now

**What L5 CONSUMES from upstream (I am held until these land on `main` with a
`## CAPABILITIES LANDED` line):**

| # | from | capability | my held items |
|---|---|---|---|
| CD-1 | **Conductor** | Generalised analysis-receipt spine so non-L0 layers can record any terminal event (**#1719**, dup **#1715**) | **all 15 assets** — nothing can reach W4 without it |
| CD-2 | **L4** | Deterministic `phala_anchors.anchor_id` (**#1732**) | `mi_bhavisya`, `mi_pramana` rebuilds |
| CD-3 | **Conductor** | Per-chart `count_sql` parameterisation (**#1723**, L4-raised) | every per-chart `integrity_verified` in L5 (13 of 15 assets) |
| CD-4 | **Conductor** | Ruling on `WriterResult.notes` (**#1738**) | `mi_seva`'s capsule honesty; not blocking its build |
| CD-5 | **L3** | Write-set arbitration on `kala_field_weight_versions` (C-F-22 — **to be filed**) | `mi_bhara` registry correction |

**What L5 PUBLISHES to downstream: nothing.** L5 is the terminal layer; no session consumes an L5
capability. My `## CAPABILITIES LANDED` section will therefore stay empty, and that is the correct
final state, not an omission.

---

## §7 — Decisions log (this document's own entries)

- **D-L5-04** — **No asset routes `verified_reuse`**, deviating from plan §5's forecast. Basis: the
  served data predates three merged narration fixes and the intervening rebuild was BLOCKED, so the
  digest lineage `verified_reuse` requires does not hold; certifying it would broadcast text the
  codebase has repudiated (§N.8). Cost consequence flagged to the Conductor.
- **D-L5-05** — **Canary order changed** to `mi_vistara` → `lel_events` → `mi_jivanaghatana`. Basis:
  §3 above. `mi_jivanaghatana` is disqualified as a *first* canary by A-F-09/A-F-10 until its W3
  items land.
- **D-L5-06** — **`mi_seva` routes `rebuild_only`, not `probe`**, against the shape its
  `asset_kind='service'` suggests. Basis: the probe path is unreachable through four independent
  gates (D-F-D09/D10); routing it `probe` would claim a verification mechanism that does not exist.
  `mi_abhilekha` *does* route `probe`, because a truthful probe claim exists for it.
- **D-L5-07** — **`mi_sankalpa` is the P7 substrate, not §7.3's parked remedy-efficacy ledger.**
  Basis: it computes no rate, no confidence, no calibration value; the parked item is the analysis
  over it. Recorded because conflating them would have wrongly parked a live, tested write path.
- **D-L5-08** — **`integrity_check_sql` proposals are authored for all 15 assets but shipped as
  proposals, not gates**, per C12's "a check that has never been green is a PROPOSAL." Where a check
  passes vacuously on an empty table, that caveat ships with it into the capsule.
- **D-L5-09** — **The L5 seal's own gates are re-verified, not inherited.** Basis: G8 is a false PASS
  (A-F-26) and G11 has regressed (D-F-D08). A predecessor seal is evidence, not authority.

---

*End of L5_W2_DECIDE_v1_0 — 15 assets routed, 34 MUSTs, 5 capability-deltas published, 2 deviations
logged with evidence. Nothing here invents a calibration value; nothing here weakens a check.*
