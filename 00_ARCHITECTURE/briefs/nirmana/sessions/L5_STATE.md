---
artifact: L5_STATE.md
canonical_id: NIRMANA_V21_L5_STATE
version: rolling
status: LIVE
session: L5
campaign_id: nirmana-elevation
charter: 00_ARCHITECTURE/briefs/nirmana/sessions/SESSION_CHARTER_V21.md
worktree: ~/nirmana-s/l5
---

# L5 — Mīmāṃsā session state

**Position:** `L5-W3` — W1 (15/15) and W2 (15/15 routed) COMPLETE. **Three PRs open, all auto-merge
armed:** #1745 (docs: W1+W2+audit+state), #1768 (migration 690, registry accuracy), #1769 (writer
honesty fixes: 9 raises + 2 fabricated-value repairs). W3 batch 2 (integrity contracts) in flight.
**W4 blocked on #1715/PR #1736** (receipt spine — now CLEAN and ready to merge) **and #1723**
(per-chart detector).

**Mandate (plan §5, L5):** parked-P7 seam-keeping. STRUCTURAL mode re-documented as deliberate;
prediction provenance retention verified; journal/adjudication-log seams confirmed intact;
insight-embedding serve path noted for the future programme; **no calibration values invented
(§N.8 absolute)**. Routes mostly `verified_reuse`/`static`; `lel_events` is the user-authored
source disposition (L5 exception in the frozen manifest: `execution_obligation:
source_acceptance`). This layer's freeze closes the build arc.

## Standing context carried forward from the Conductor's stub (do not lose on rebase)

- **Coordination issue:** #1713 · **Adjudication:** new issue labeled `nirmana-adjudication`, then
  keep working (C3) · **Migration range:** 690–699 · **Branches:** `codex/nirmana-l5-*` · **PR
  prefix:** `L5:` · **Worktree:** `~/nirmana-s/l5`
- **Freeze predecessor:** L4 Phala must be frozen before L5's W6 ceremony (C2). Asset work is never
  held for this — only the ceremony.
- **Standing ruling D-CND-01** (binding on every Conform-stage check I author): a `count(*) = N` is
  permitted **only** as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table FULL-JOIN
  consistency, NULL/range guards). **Alone it is forbidden** (C12). `expected_volume_formula` is
  REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
  *L5 conformance:* none of the 15 integrity contracts being authored uses a bare count equality;
  all are relational/partition invariants per D-CND-03's `NOT EXISTS (… GROUP BY chart_id HAVING …)`
  shape, and every volume expectation lives in `expected_volume_formula` (migration 690).

## Asset table (15, from frozen definition + live `asset_registry`)

| asset | kind | domain/scope | table | rows (2026-09-05) | anc / unfrozen | route | status |
|---|---|---|---|---|---|---|---|
| lel_events | data (no writer) | chart/per_chart | — (source) | — | 0/0 **E-GATE OPEN** | `static` | W2 ✓ — CANARY 2 — disposition, not build; blocked on #1719 |
| mi_vistara | data | **shared/global** | mimamsa_export_log | 0 | 0/0 **E-GATE OPEN** | `rebuild_only` | W2 ✓ — **CANARY 1** — cheapest in campaign (0.287s), zero deps |
| mi_jivanaghatana | data | chart/per_chart | mimamsa_event_provenance | 64 | 1/0 **E-GATE OPEN** | `changed` | W2 ✓ — CANARY 3 — demoted; needs A-F-09/A-F-10 first |
| mi_kula | data | **shared/global** | mimamsa_signal_families | 11 | 6/3 | `changed` | W2 ✓ — global re-seed; C-F-01 grounding badge |
| mi_bhara | data | chart/per_chart | **kala_field_weight_versions** | 1 | 36/26 | `changed` | W2 ✓ — registry-only; #1743 filed |
| mi_sankalpa | data | chart/per_chart | mimamsa_intervention_ledger | 0 | 36/26 | `rebuild_only` | W2 ✓ — floor fix D-F-D15 must land first |
| mi_bhavisya | data | chart/per_chart | mimamsa_predictions | 195 | 59/49 | `changed` | W2 ✓ — **HELD** on #1732 |
| mi_abhilekha | **service** | chart/per_chart | mimamsa_journal | 0 | 60/50 | `probe` | W2 ✓ — real GREEN probe needed (B-F-03) |
| mi_pramana | data | chart/per_chart | mimamsa_calibration | 57 | 61/50 | `changed` | W2 ✓ — **HELD** on #1732; STRUCTURAL doc route |
| mi_gunanaka | data | chart/per_chart | mimamsa_multipliers | 18 | 62/51 | `changed` | W2 ✓ — C-F-05 literal flags in stored rows |
| mi_pariksha | data | chart/per_chart | mimamsa_qa_eval | 174 | 62/51 | `rebuild_only` | W2 ✓ — B-F-07/B-F-08 |
| mi_adhilepa | data | chart/per_chart | mimamsa_load_bearing | 9 | 63/52 | `changed` | W2 ✓ — C-F-13/C-F-14 |
| mi_sambandha | data | chart/per_chart | mimamsa_manifestation_grammar | 47 | 63/52 | `changed` | W2 ✓ — B-F-14 unearned empirical grade at rest |
| mi_seva | **service** | chart/per_chart | mimamsa_preferences | 0 | 64/53 | `rebuild_only` | W2 ✓ — **not** probe — path unreachable (D-F-D09) |
| mi_darshana | data | chart/per_chart | mimamsa_insight_units | 150 | 66/55 | `rebuild_only` | W2 ✓ — code correct at HEAD; data stale (B-F-21) |

## Decisions log

- **D-L5-01** (2026-09-05) — Bootstrap complete: worktree `~/nirmana-s/l5` at `origin/main`
  `20323fae4`; charter read from the shared checkout (C1: sessions/ not yet on main);
  `NIRMANA_HOLD` absent (standing authorization); coordination issue = **#1713**; no open
  `nirmana-adjudication` issues at open. DB read path = read-only postgres MCP.
- **D-L5-09** (2026-09-05) — The L5 seal's own gates are **re-verified, not inherited**: G8 is a false
  PASS (`structural_no_calibration` exists in no code, only in four markdown files) and G11 has
  regressed (live `mi_seva.count_sql` contradicts the sealed null). A predecessor seal is evidence,
  not authority.
- **D-L5-08** (2026-09-05) — `integrity_check_sql` authored for all 15 assets but shipped as
  **proposals, not gates** (C12: "a check that has never been green is a PROPOSAL"). Where a check
  passes vacuously on an empty table, that caveat ships with it into the capsule.
- **D-L5-07** (2026-09-05) — `mi_sankalpa` is the P7 **substrate**, NOT plan §7.3's parked
  "remedy-efficacy ledger" (which is the *analysis over* it). Recorded because conflating them would
  have wrongly parked a live, tested, correctly-guarded serve-time write path.
- **D-L5-06** (2026-09-05) — `mi_seva` routes `rebuild_only`, **not** `probe`, against the shape its
  `asset_kind='service'` suggests: the probe path is unreachable through four independent gates, so
  `probe` would claim a verification mechanism that does not exist. `mi_abhilekha` *does* route
  `probe` — a truthful probe claim exists for it.
- **D-L5-05 / D-L5-04** — see Route summary above.
- **D-L5-03** (2026-09-05) — Filed adjudication **#1719** (cross-layer). Chose to raise it at W1
  rather than at my own W4 because it is on every layer's critical path and the fix lives in
  Conductor-owned shared surfaces (C5). Explicitly did NOT route around it by relaxing C2.2 —
  weakening a gate to make something pass is a hard-floor violation (C3 / prompt §3.4).
- **D-L5-02** (2026-09-05) — E-gate queried live (C10 batch variant), not assumed. Three assets
  open TODAY: `lel_events`, `mi_vistara`, `mi_jivanaghatana`. The other 12 wait on L1–L4 ancestor
  freezes; the C10 query is the calendar, re-run every loop.

## Findings (pre-W1, from the live registry read — carried into W1 for confirmation)

- **F-L5-A (all 15):** `integrity_check_sql IS NULL` for every L5 asset — the layer has zero
  integrity gates. Per C12 an absent check is not a failing check; but a route to terminal needs
  *some* real detector. To be triaged in W2 (MUST vs NOW vs LATER per asset).
- **F-L5-B (all 15):** `catalog_status = 'DRAFT'` for every L5 asset.
- **F-L5-C:** `expected_volume_formula` populated on `mi_jivanaghatana` only
  (`FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md','EVT')`); NULL on the other 14 — per C12
  a NULL derived-volume input is the defect when a volume claim is being made. Most L5 floors are
  `0` (honest, §N.4) so no volume claim is currently being made — confirm in W1.
- **F-L5-D:** `mi_bhara`'s `target_table` is **`kala_field_weight_versions`** — an L3-owned table
  written by an L5 asset. Cross-layer write-set; flag to Conductor if it collides with L3's W3.
- **F-L5-E:** `mi_kula` and `mi_vistara` are `domain='shared'`, `scope='global'` — per WP-3, chart
  and layer scopes exclude `domain='shared'` unless explicitly included. Dispatch mechanics for
  these two differ from the rest; `mi_vistara` is a nominated canary, so resolve this in W2.
- **F-L5-G (mandate item 1 — the layer's most important open question).** The L5 seal
  (`L5_SEAL_AND_SHIP_REPORT_v1_0.md`, 2026-06-27) justifies the STRUCTURAL honesty label on two
  claims that have BOTH gone stale:
  1. Its stated STRUCTURAL→EMPIRICAL precondition #1 was "L4 Phala layer sealed". **L4 sealed
     2026-06-29**, two days later (CLAUDE.md §E, `L4_PHALA_CLOSE_v1_0.md`). So the seal's framing
     now reads as *unfinished work whose blocker has cleared* — the opposite of the "deliberate"
     framing this campaign's L5 mandate requires. The honest current justification is that no real
     prediction→outcome data exists and **P7 is PARKED by native ruling**, not that L4 is unsealed.
  2. Its evidence sentence — "all 9 multipliers carry `promotion_status='prior_only'`… `gate_passed
     =false` for all 9" — is **factually false live**. `482012f1` now has 7 `prior_only` and
     **2 `promoted` with `gate_passed=true`, `held_out_validity='pass'`, `confidence_high=true`**
     (`LL1:fam_graha_natal` n=271; `LL1:fam_transit` n=14), `updated_at 2026-08-13` — i.e. a harness
     cycle ran AFTER the seal. `1c826d5a` still has 9/9 `prior_only`.
  **The determination that matters (§N.8):** are those `n_observations` prediction→**real lived
  outcome** observations (genuine empirical calibration → the seal's label is stale in the
  permissive direction, a documentation MUST), or prediction→**self-score** observations with no
  outcome ever recorded (→ two multipliers wear an empirical badge they did not earn, a correctness
  MUST and the §N.8 defect class exactly)? Either way a MUST; W1 Batch C (`mi_gunanaka`) and Batch A
  (`mi_pramana`) have both been tasked with the trace. **Nothing may be filled or corrected either
  way — determine and document only.**
- **F-L5-H:** the seal counts 12 `mi_*` assets and 50 `mimamsa_predictions` rows; the frozen
  manifest carries 14 `mi_*` + `lel_events` = 15, and predictions are now 195 across two charts.
  Drift to reconcile in the close report, not a defect on its face.
- **F-L5-F:** `mi_abhilekha` and `mi_seva` are `asset_kind='service'` with `service_health IS NULL`
  — no current probe. C12's service addendum makes a GREEN probe the "lit" condition.

## Per-chart census (2026-09-05, live — grounds W2 floor-setting per §N.4 and volume derivation per C12)

Chart A = `482012f1…` (canonical native) · Chart B = `1c826d5a…` (Abhinandan).

| table | A | B | reading |
|---|---|---|---|
| mimamsa_predictions | 139 | 56 | both charts real |
| mimamsa_qa_eval | 168 | 6 | heavily A-weighted |
| mimamsa_insight_units | 115 | 35 | both real |
| mimamsa_manifestation_grammar | 24 | 23 | symmetric |
| mimamsa_load_bearing | 4 | 5 | symmetric, small |
| **mimamsa_calibration** | 57 | **0** | A-only |
| **mimamsa_event_provenance** | 64 | **0** | A-only |

**F-L5-I — the two A-only tables are honestly A-only, not a build failure.** `mi_jivanaghatana`
derives from the **Life Event Log**, which is the *native's own* life events; chart B has no LEL, so
0 rows is the correct answer, not a gap. `mimamsa_calibration` follows downstream (no events → no
calibration). Consequence for W2: **a per-chart floor is the wrong shape for these two assets** —
setting `target_floor=64` would make chart B permanently and falsely "under-built". Floors here must
be chart-conditional or left at the honest `0` (§N.4: floors are aspirational, never fabricated).
This also means `lel_events`' `source_acceptance` disposition is intrinsically single-chart, which
is a point in favour of it being a disposition rather than a build.

## Route summary (W2, full detail in `L5_W2_DECIDE_v1_0.md`)

`changed` **8** · `rebuild_only` **5** · `probe` **1** · `static` **1** · `verified_reuse` **0**.

**Deviation logged (D-L5-04):** plan §5 forecast "mostly `verified_reuse`/`static`" for L5. **No asset
takes `verified_reuse`.** The served data predates three merged narration fixes (last good build
2026-08-12/13; F-143/F-147/F-148 landed 2026-08-21/22; the intervening rebuild was BLOCKED), so rows
carry `*_v1.0` formula versions against `v1.2` code and the layer is *serving today* sentences those
PRs removed. The digest lineage `verified_reuse` requires does not hold; certifying it would broadcast
repudiated text (§N.8). **Cost consequence: L5 is not the cheap closing layer it was forecast to be.**

**Deviation logged (D-L5-05):** canary order changed to `mi_vistara` → `lel_events` →
`mi_jivanaghatana` (prompt nominated the reverse). `mi_vistara` is the cheapest execution in the whole
campaign, has zero deps, needs no code change, and would capture the first `mi_*` provenance receipt
ever. `mi_jivanaghatana` is disqualified as *first* canary by A-F-09 (volume formula wrong on three
counts) and A-F-10 (`admissible_clean` true 64/64 with no code path that can produce false).

## Findings ledger (W1 → W2)

**~109 findings across 4 batches; 34 MUST, ~60 NOW, 15 NEVER/LATER.** Finding IDs are **batch-prefixed**
(`A-F-15`, `B-F-14`, `C-F-05`, `D-F-D09`) because the batches numbered independently and `L5-F-01`
occurs in three of them. Full triage in `L5_W2_DECIDE_v1_0.md` §4.

**Mandate scorecard (plan §5's five L5 items):** 1 STRUCTURAL re-documentation — *determined, writes in
W3*. 2 provenance retention — **VERIFIED HEALTHY**, 0 orphans on all four links, one live threat
(#1732). 3 journal/adjudication seams — **CONFIRMED with precision**: journal empty because
*unwritable* (no `INSERT INTO mimamsa_journal` exists anywhere in the repo), adjudication log written
correctly but never read back into L5. 4 insight-embedding path — **NOTED in full** (B-F-20): schema
✓, serve path ✓ and honest, producer MISSING, MCP reachability MISSING. 5 no invented calibration
values — **HELD ABSOLUTE**; every evidence-absent case recommends an honest NULL or a rename.

## Rulings received (2026-09-05) — and what each changed for L5

| issue | ruling | effect on L5 |
|---|---|---|
| **#1719 → #1715** | Consolidated; **Option A GRANTED**. L1 built it: **PR #1736**, per-layer pins in a generated `nirmana-analysis-layer-pins.json`, generator + CI `--check`, L0 byte-identical (121 tests unchanged). | **Unblocks all 15 L5 assets at W4** on merge+deploy. I reviewed the PR: no blocking findings. Verified L5's own edge case — `lel_events` is correctly in `non_writer_assets` with `receipt_count: 15`, so my canary is not silently dropped by the `mi_` prefix filter. |
| **#1744** (L1-filed) | The frozen definition **can no longer be superseded** (174 events against it; the lock is one-way). **`depends_on` and `layer` are IMMUTABLE**; every other registry-contract field is **mutable before acceptance**. `target_floor` / `expected_volume_formula` / `expected_volume_inputs` are outside the fingerprint entirely. | **Reshaped my whole W3.** All 32 DAG corrections dropped from W3 and posted to the #1734 register instead. Everything else proceeds. My acceptance window is clean (zero L5 acceptance events), so registry work races nothing. |
| **#1723 / #1727** | **D-CND-03**: per-chart integrity contracts must be chart-partitioned invariants — `SELECT NOT EXISTS (… GROUP BY chart_id HAVING …)` — with **bind placeholders rejected outright**. Each layer authors its own. | Gives W3 batch 2 an exact standard; 15 contracts being authored and **verified live** before shipping (C12: an unrun check is a proposal). |
| **#1738** (mine) | **UPHELD campaign-wide.** `notes` is documentation, never a signal; a writer that cannot do its job must **raise**. Each layer audits its own writers as W3. Conductor is building a CI detector. The orchestrator-side `degraded` flag is **PARKED** to the native (frozen writer contract). | W3 batch 3: audit all 14 L5 writers, convert disguised failures to raises, **report counts** back to #1738. In flight. |
| **#1732** (mine) | **L4 ACK, in flight**, with a material refinement: keying on the existing natural key would NOT be deterministic (it contains two `bigserial`s), so L4 is keying on upstream **content** digests instead — verified unique across all 35,365 `kala_convergence` rows. | `mi_bhavisya` / `mi_pramana` stay HELD, but L4 can lift it without needing anything from me. |
| **#1743** (mine) | **L3 ACK, all three points granted.** `kala_field_weight_versions` + `kala_field_weights` declared L3-owned/L5-read-only; four files fenced; my `mi_bhara.target_table` correction acked. L3 added a measured figure: `ka_kshetra` builds in **22,685 s (6 h 18 m, 308 substeps)**, so the resolve-once rule protects a six-hour straddle window. | `mi_bhara` registry correction proceeds (migration 690). |

**L3's ack contained the sharpest corroboration of the hazard:** its own mechanical `depends_on`
reconciliation had listed `mi_bhara` under `ka_kshetra`'s undeclared reads — i.e. it would have
proposed adding exactly the edge the acyclicity guard exists to refuse, and it would have looked
like exemplary dependency hygiene. Only a decision not to act on automated inference stopped it.

## Adjudication issues filed (4)

| # | subject | blocks |
|---|---|---|
| **#1719** | Evidence ingress is structurally L0-only — **all nine terminal event types** for L1–L5 | **all 15 L5 assets at W4** |
| **#1732** | `ph_nimitta` rebuild destroys the L5 prediction-provenance chain (`anchor_id` = `gen_random_uuid()`) — TIME-CRITICAL, cross-posted to L4's #1718/#1723 | `mi_bhavisya`, `mi_pramana` rebuilds |
| **#1738** | `WriterResult.notes` is write-only — 87 writers report degradation into a void, builds go green | campaign-wide honesty; `mi_seva` capsule |
| **#1743** | `kala_field_weight_versions` L3↔L5 shared write-set + acyclicity guard | `mi_bhara` registry correction only |

Each was **independently re-verified by this session** before filing — not escalated on a subagent's
word. #1719 and #1732 both proved larger than first stated after that re-verification.

## W3 plan (replanned under #1744 / D-CND-09)

| batch | content | status |
|---|---|---|
| **W3-1** registry accuracy | migration **690** — `mi_sankalpa`/`mi_bhara` `target_floor` NULL→0 (ends a perpetual `dormant` re-queue); `mi_bhara.target_table` → `kala_field_skill`; `mi_jivanaghatana` volume formula **corrected** (was wrong on three counts); 4 more volume formulas derived; 5 `estimated_seconds` re-measured | authored, under independent review |
| **W3-2** integrity contracts | 15 chart-partitioned invariants per D-CND-03, each **verified live** before shipping | in flight |
| **W3-3** writer `notes` audit | per #1738 ruling — A 10 / B 17 / C 10 / UNKNOWN 1 over 38 sites; **9 raises + 2 fabricated-value repairs implemented** (A5 held pending Conductor word rather than guessed); counts posted to #1738 | **PR #1769** |
| **W3-4** serving-plane honesty | `empty_reason` + `density_contract` sweep (**0 of 16** L5 capabilities declare one); `qa_fail_count` prefix fix; `compute_spine_bundle` always-NULL filter; `buildEfficacyReport` nulls | queued |
| **W3-5** narration/label + idempotency | label corrections that move no number; the `neg_control` DELETE that also wipes `tail_only` | queued |
| **DROPPED** | all 32 `depends_on` corrections — **immutable per D-CND-09**, recorded in the #1734 register instead | posted |

**Measured-cost correction, self-caught:** one W1 batch claimed `build_run_assets.started_at` is
NULL for every L5 row. **That was false** — it is populated on 38–45 rows per asset. I re-measured
directly rather than write a registry number on a subagent's word, and corrected the claim in
`L5_W1_ANALYSIS_BATCH_C.md` note 7. The batch's *warning* was right and understated: `mi_adhilepa`
measures avg 31.2 s / **max 843 s** against a registry estimate of 11 (77× on the tail), and
`mi_bhara` avg 17.3 s / **max 597 s** against 2 (298×). Those two would break any W4 slot plan built
on the registry's numbers.

## Cross-layer contributions made (not just filings)

- **#1734 DAG register** — L5's complete 32-correction contribution, both directions, with the
  observation that false edges are not merely untidy: `mi_bhavisya`'s canonical build **actually
  failed** blocked on two dependencies it never reads, and `mi_seva` has **12** BLOCKED terminations
  on an edge whose target it does not even probe. Under D-CND-09 those blocks are now permanent for
  this campaign, so W4 must sequence around known-spurious blocks.
- **#1748 (L4's signal-id finding)** — added the surface a column-name sweep cannot see:
  `mimamsa_predictions.driving_signals` holds **975 signal refs across all 195 predictions** inside
  JSONB (L5's true total is 2,409, not the 1,434 their table showed). Also supplied live
  corroboration of their "identity not stable across builds" grading: **my predictions already
  reference signals from two different `bo_laksana` build_ids** (25 + 20), all resolving today
  thanks to accretion, but not comparable across generations.
- **PR #1736 review** — verified the receipt-spine generalisation does not weaken the detector, and
  checked L5's own edge case specifically (`lel_events` correctly in `non_writer_assets`,
  `receipt_count: 15`, so the canary is not silently dropped by the `mi_` prefix filter).
- **#1764** — filed a red-baseline notice: `main` has 3 failing writer tests (L0 ×2, L2 ×1),
  confirmed pre-existing by stashing this entire tree and re-running. Every session's local C4
  verification is red through no fault of its diff.

## Held items

- **H-L5-01 — ALL 15 assets (widened from 12 after tracing the full lifecycle).** Adjudication issue
  **#1719** filed with the Conductor: `asset_analysis_accepted` and `optimization_verdict_accepted`
  are structurally L0-only in the deployed evidence ingress
  (`platform/src/lib/nirmana-elevation/definitions.ts:1223-1231` throws when `input.layer !== 'L0'`;
  the digest fn and receipt schema carry two further `L0` literals; the generated receipt module is
  L0-only with no generator script). Charter C2.2 requires both events before W4, so **no L1–L5
  asset can enter W4 until this lands** — this blocks all five layer sessions, not just L5.
  Recommended Option A (generalize the receipt spine, Conductor-owned per C5). **Widened after
  filing:** `loadCurrentLifecycleContext` calls the same L0-only function and `analysis_digest` is a
  *required* field on the lifecycle binding schema every terminal event extends — so
  `implementation_accepted`, `accepted_rebuild_observed`, `probe_accepted`, `integrity_verified`,
  `asset_frozen`, `static_accepted`, `source_accepted`, `empty_accepted` and `producer_covered` are
  **all** unrecordable for L1–L5, not just the two W2 events. W1/W2 were unaffected and completed.
- **H-L5-02 — `mi_bhavisya`, `mi_pramana` rebuilds** → **#1732** (CD-2, L4-owned).
- **H-L5-03 — every per-chart `integrity_verified` (13 of 15 assets)** → **#1723** (CD-3, L4-raised,
  Conductor-owned). Sequential with #1719: fixing only one moves every layer from blocked-at-W2 to
  blocked-at-W5, burning build slots on runs that cannot be certified.
- **H-L5-05 — any L5 rebuild's signal provenance** → **#1748** (L2-owned). Not blocking (nothing is
  orphaned today, 0/975 unresolvable), but if L2's `signal_id` fix lands after mine I **re-verify the
  975 refs before any L5 rebuild** rather than assume they still resolve.
- **H-L5-04 — `mi_bhara` registry correction** → **#1743** (CD-5, L3 ack). Fallback if held: route
  `probe` and re-decide.

## Capability-delta list (charter C6) — published 2026-09-05

**CONSUMED (I wait on these):** CD-1 generalised receipt spine (Conductor, #1719) · CD-2 deterministic
`anchor_id` (L4, #1732) · CD-3 per-chart `count_sql` parameterisation (Conductor, #1723) · CD-4
`WriterResult.notes` ruling (Conductor, #1738) · CD-5 `kala_field_weight_versions` arbitration (L3,
#1743).

**PUBLISHED: none.** L5 is the terminal layer; no session consumes an L5 capability. My
`## CAPABILITIES LANDED` section will stay empty — that is the correct final state, not an omission.

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| bootstrap + registry/E-gate read | ~10 min | — |
| W1 fan-out (4 read-only SAs, 15 assets) | in flight | — |
| dispatch/evidence-path study + #1719 | ~20 min | found the campaign's top blocker |
| seal re-read + live multiplier check | ~10 min | found F-L5-G (STRUCTURAL staleness) |
| W1 fan-out, 4 SAs, 15 assets | ~13 min wall / ~821k SA tokens | ~109 findings |
| W1 persistence + W2 authoring | ~35 min | 5 docs, 4 adjudication issues |

## Heartbeat

- 2026-09-05 — **W1 COMPLETE (15/15), W2 COMPLETE (15/15 routed).** 4 adjudication issues filed, all
  independently re-verified first. Next: W3 batches (registry corrections, integrity proposals,
  serving-plane honesty sweep, narration/label fixes) — none blocked by #1719, which gates W4 only.
- 2026-09-05 — F-L5-G surfaced and routed to the two owning W1 subagents (no duplication).
- 2026-09-05 — L5-W1 opened; 4 read-only analysis subagents dispatched over the 15 assets.
