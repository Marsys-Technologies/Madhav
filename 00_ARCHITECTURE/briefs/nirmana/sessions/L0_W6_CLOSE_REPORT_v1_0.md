---
artifact: L0_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_L0_W6_CLOSE_REPORT
version: "1.0"
status: CLOSED — L0 is 40/40 frozen; W6 stage ceremony executed and receipted
session: L0
layer: L0 — Brahmagyan
produced_on: 2026-09-08
charter_ref: C11 (definition of done)
authored_by: Conductor (cycle 324), on behalf of the ended L0 session
warning: >
  RETRO CLOSE-OUT, Conductor-authored. The L0 session ended (and its lane was retired) after
  completing the work but before publishing this report — Conductor self-assigned the residual
  (RESOLUTION_CONDUCTOR v4 escalation, cycle-322 disposition, tracked on #1770). Every quantitative
  claim below is read from primary sources at composition time: the campaign evidence ledger
  (nirmana_evidence.nirmana_elevation_campaign_events), the committed L0_STATE.md (origin/main,
  last lane-authored update 2026-09-06), the W1 analysis corpus (L0_W1_ANALYSIS_INDEX_v1_0.md +
  batches A–E), and gcloud/DB records. Narrative context is cited to the L0 lane's own decision
  ids (D-L0-*) as committed by that lane; this report does not re-derive or extend those findings,
  and claims nothing the sources do not establish. Where the ended session left a check unrun,
  that is stated as a residual, not silently absorbed (§6).
---

# L0 — Brahmagyan — W6 CLOSE REPORT

## §0 — Status

**CLOSED — 40/40 L0 assets frozen.** Every `asset_frozen` event is verifier-signed
(`recorded_by = nirmana-executor:amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com`),
recorded under definition revision `t0-2026-09-01-0e5b06fb`, spanning
2026-09-03 15:36:55Z (`bg_vedha_malefic_scale`, first) → 2026-09-07 06:39:56Z (`bg_cohort`, last).
The freezes carried across the D-NATIVE-13 mid-campaign definition supersession
(`t1-2026-09-08-be255ffe` FROZEN 2026-09-08 09:34:55Z; t0 superseded same instant) — supersession
preserves asset freeze state by design.

**W6 ceremony executed and receipted:** stage transition `F0_FOUNDATION → L0` accepted
2026-09-08 09:54:54Z under `t1-2026-09-08-be255ffe`, schema `nirmana-stage-transition-receipt/v1`,
`source_kind=server_reconstructed`, submitted by the executor SA — i.e. the server-side
fail-closed freeze-lifecycle verifier (#2428 item 4) passed over the 40/40. The subsequent
`L0 → L1` receipt (10:49:23Z, same spine) proves downstream ordering held. Eligibility was
independently re-verified live by Conductor at cycle 322 (bg 40/40 by direct ledger count).

What this report does NOT claim: per-cycle wall-clock/token telemetry beyond the lane's own
committed cost ledger (§4), and the closure-safe-sync-at-firing-time retro-check (§6, open
residual).

## §1 — Asset table (40/40)

Freeze timestamps are the ledger's `asset_frozen.recorded_at` (UTC), verbatim. Route/blocker
notes for the final ten are from the lane's committed decision log (L0_STATE.md).

| # | asset | frozen at (2026, UTC) | note |
|---|---|---|---|
| 1 | bg_vedha_malefic_scale | 09-03 15:36:55 | first freeze of the campaign resumption arc |
| 2 | bg_sarvatobhadra_grid | 09-04 09:01:39 | |
| 3 | bg_gochara_citation_resolution | 09-04 09:04:36 | W1 Batch-E MUST downgraded in place — live DB matched the check; branch-staleness false alarm (index §caveat) |
| 4 | bg_dignity_reference | 09-04 20:06:36 | |
| 5 | bg_class_priors | 09-04 20:12:58 | |
| 6 | bg_ephemeris | 09-04 20:13:09 | |
| 7 | bg_formula_constants | 09-04 20:13:20 | |
| 8 | bg_ghatana | 09-04 20:13:30 | |
| 9 | bg_kota_chakra_rings | 09-04 20:13:39 | |
| 10 | bg_medical_mappings | 09-04 20:13:50 | |
| 11 | bg_muhurta_lattice | 09-04 20:14:01 | W1 Batch-D partial-serving finding → serving-side backlog (§5), not a freeze blocker |
| 12 | bg_nakshatra | 09-04 20:14:11 | |
| 13 | bg_ontology | 09-04 20:14:21 | |
| 14 | bg_phaladeepika_latta | 09-04 20:14:31 | |
| 15 | bg_prashna_rules | 09-04 20:14:41 | |
| 16 | bg_transit_rules | 09-04 20:15:07 | |
| 17 | bg_vastu_directions | 09-04 20:15:16 | |
| 18 | bg_vidhi_primitives | 09-04 20:15:26 | |
| 19 | bg_sky_calendar | 09-04 21:47:39 | |
| 20 | bg_texts | 09-04 21:47:52 | |
| 21 | bg_panchanga | 09-04 21:48:36 | |
| 22 | bg_ephemeris_engine | 09-04 21:48:39 | `asset_kind=service` — "lit" = current GREEN probe (C12 §3.5 addendum) |
| 23 | bg_sign_medical | 09-04 22:04:37 | |
| 24 | bg_nakshatra_medical | 09-04 22:04:40 | |
| 25 | bg_transit_engine | 09-04 22:04:43 | |
| 26 | bg_class_lifetime_counts | 09-04 22:38:18 | |
| 27 | bg_kp_sublord_division | 09-04 22:38:28 | |
| 28 | bg_reference | 09-04 22:38:38 | |
| 29 | bg_remedies | 09-04 22:38:49 | |
| 30 | bg_vidhi_floors | 09-05 18:54:27 | first freeze after C8-supervised resumption; check-correction migration 693; DRAFT→CURRENT handled in the D-CND-09 arc |
| 31 | bg_doshas | 09-06 10:19:05 | check correction 692 (FULL-JOIN entity_class scope leak) — D-L0-L |
| 32 | bg_gochara_arcs | 09-06 10:27:41 | stale pin → tiling+floor rewrite, migration 694 — D-L0-F/FF |
| 33 | bg_text_index | 09-06 10:36:36 | D-L0-FF delta-skip evidence-chain trap (4th instance), cleared via the Conductor-side receipt re-attribution arc (#1899/#1901) |
| 34 | bg_dasha_systems | 09-06 11:08:24 | check had two bugs (scope leak + mis-authored catalog_hash pin) — migration 700, D-L0-GG; writer verdict: correct |
| 35 | bg_compendium_index | 09-06 11:14:36 | both content-hash pins stale vs evolved corpus — migration 702, D-L0-MM; writer verdict: correct |
| 36 | bg_parihara_rules | 09-06 13:11:39 | ancestor-blocked on bg_doshas only (D-L0-H); C13 blast radius catalogue-verified EMPTY |
| 37 | bg_yogas | 09-06 15:58:26 | scope-leak check fix 701 — D-L0-KK; genuine writer replay = exactly 233/233/233/85, all three content-hash pins byte-for-byte |
| 38 | bg_rules | 09-06 16:07:29 | ancestor-blocked (bg_dasha_systems, bg_yogas), cleared in order |
| 39 | bg_concordance | 09-06 16:13:29 | deepest DAG node, cleared last of the ancestor chain |
| 40 | bg_cohort | 09-07 06:39:56 | D-L0-II service-kind-dependency receipt gap (sole L0 instance); resolved at fleet level after the lane's #1713 escalation — chain then completed genuinely |

## §2 — Findings ledger outcome

**W1 corpus:** 40/40 assets analyzed by 5 parallel read-only batch agents
(`L0_W1_ANALYSIS_BATCH_A..E.md`, indexed by `L0_W1_ANALYSIS_INDEX_v1_0.md`), grounded in a live
production registry snapshot (`L0_ASSET_REGISTRY_SNAPSHOT_2026-09-04.json`). Cross-batch MUSTs
were few and named: the `bg_concordance` built-but-unplugged serving stub (WIRE, not retire —
corroborated independently by batches A and B), two "declared dependency yields near-zero"
findings, the `bg_muhurta_lattice` partial-serving description defect, and the `bg_vidhi_floors`
DRAFT-status anomaly. The index records its own methodology caveat honestly (analysis branch 165
commits stale; one Batch-E MUST false-alarmed on migration presence and was downgraded in place
after live-DB verification).

**C12 integrity-verdict arc — the layer's defining outcome.** The five originally-failing
`integrity_check_sql` gates (bg_yogas, bg_dasha_systems, bg_doshas, bg_vidhi_floors,
bg_gochara_arcs) were initially called "4 of 5 real data defects, fix the writer (MUST)" (D-L0-F).
The lane then did the detector-first work the C12 doctrine demands — replaying writers directly
(read-only) against production, isolating failing subclauses one at a time — and the final,
evidence-backed outcome inverted the initial call: **zero writer fixes were needed.** Every
failure was either stale pre-contract build data or a defect in the CHECK itself: the recurring
FULL-JOIN `entity_class`-in-ON-clause scope leak (692 bg_doshas, 700 bg_dasha_systems,
701 bg_yogas), a mis-authored `catalog_hash` pin (700), stale content-hash pins vs an evolved
corpus (702 bg_compendium_index), a stale pin → real tiling/floor invariant rewrite
(694 bg_gochara_arcs, satisfying C12's rewrite floor test), plus 693 (bg_vidhi_floors). Six
check-correction migrations total (692/693/694/700/701/702), each verified live both directions
(TRUE on genuine writer replay, FALSE fail-closed on stale data) before merge.

**Evidence-chain (not data) defects found and escalated, all since closed at fleet level:**
D-L0-AA (authorization must precede dispatch inside the planned window), D-L0-FF (delta-skip
orphans a genuine build's evidence chain; 4 confirmed instances → Conductor arc #1899/#1901),
D-L0-JJ (multi-asset authorization exact-set-match; lane tooling fixed), D-L0-II (service-kind
dependency can never yield a `proven` upstream receipt — sole L0 instance bg_cohort, defect class
general across layers, escalated on #1713). That all 40 assets nonetheless froze with complete
verifier-signed chains is the measure that these were resolved, not worked around.

## §3 — Pillar movement (per the five doctrines)

L0 is the global reference substrate — one layer deeper than L1's "substrate provider" framing:
it is the layer every doctrine's substrate is itself built FROM.

- **D-GROUNDING (P3).** The classical-text grounding chain (bg_texts, bg_text_index,
  bg_compendium_index, bg_concordance, bg_gochara_citation_resolution) is now frozen with
  content-hash-pinned integrity contracts — citations downstream layers rely on resolve against
  verified, fingerprinted corpora. The known gap is serve-side, not data-side: the
  `classical_attribution_lookup.ts` stub (§5 backlog, WIRE disposition).
- **D-SALIENCE (P5).** bg_class_priors and bg_class_lifetime_counts — the priors salience
  weighting draws on — are frozen with verified volume/content contracts; bg_vidhi_floors' floors
  data (the D-CND-09 arc) closed its DRAFT-status anomaly before freeze.
- **D-SYNTHESIS (P4) / D-TIME (P6).** The timing substrate (bg_ephemeris, bg_ephemeris_engine,
  bg_transit_engine, bg_sky_calendar, bg_gochara_arcs, bg_muhurta_lattice, bg_panchanga) is
  frozen; bg_gochara_arcs specifically moved from a bare stale pin to a real tiling
  (no-gaps/no-overlaps) invariant — a strictly stronger contract per the C12 floor test.
- **D-SERVICE (P8).** L0's W1 pass surfaced the layer's built-but-unplugged instances
  (bg_concordance stub; bg_muhurta_lattice's overclaiming capability description) and routed them
  honestly to the serving backlog rather than blocking data-freeze on serve-side work — the same
  separation the Serving Density Principle (CLAUDE.md §N.6) draws.

Doctrinal export beyond the layer: the C12 arc above is now the campaign-wide worked example of
"a check that has never been green is a PROPOSAL" and "derive, never pick" — cited in the charter
itself (C12 was native-ruled out of L0 wave-1's discoveries).

## §4 — Cost actuals vs forecast

The lane's committed cost ledger (L0_STATE.md, wall-clock; per-asset token telemetry was not
tracked — stated honestly rather than reconstructed):

| item | wall-clock |
|---|---|
| W4 EXECUTE — 29 assets frozen (waves 0 + probes + producer-covered + wave-1 clean 4) | ~several hrs |
| P0 integrity-detector fixes + #1772 tooling | ~1.5 hr |
| depends_on normalization + dispatcher fix (#1728) | ~40 min |
| C12 wave-1 defect investigation (6 assets) | ~50 min |
| C8-supervised resumption, cycles 1–18 (D-L0-J → D-L0-V) | ~3 hrs across 18 bounded cycles |
| Final freeze wave (bg_vidhi_floors → bg_cohort, 09-05 → 09-07) | spread across supervised cycles; not separately metered by the lane |

Forecast slice: the unified plan's L0 estimate assumed a mostly-mechanical Conform pass; the
actuals' overrun concentrated in exactly two places — the C12 detector-first investigations
(which converted a forecast "4 writer fixes" into 6 check-correction migrations) and the
evidence-chain mechanics discovery (authorize-ordering, force-execute, delta-skip). Both are
one-time costs whose tooling and doctrine (C12, the dispatch mechanics now encoded in charter/
PROMPT_EXECUTOR) were inherited free by L1–L5 — visible in L1's materially faster 19/19 close.

## §5 — Backlog handed forward

1. **bg_concordance serve-side WIRE** — `classical_attribution_lookup.ts` is a hardcoded
   `attributions: []` stub over a real, populated, integrity-passing table. Disposition WIRE
   (repoint the tool), owner: serving/MCP layer work, not any nirmana freeze gate.
2. **bg_muhurta_lattice capability description** — serving capability describes more than the
   writer produces; align description (or serve the fuller set). Serving backlog.
3. **D-L0-II defect class** — service-kind dependencies vs `proven` upstream receipts in shared
   orchestrator provenance. L0's instance cleared; the CLASS remains a known trap for any future
   layer/asset whose `depends_on` includes an `asset_kind='service'` row. Reference account:
   L0_STATE D-L0-II.
4. **Migration-range hygiene** — L0's 692/693/694 landed inside L5's declared 690–699 range
   (no functional break; `migrate.ts` sorts by filename). L0's continuation range is 700–709
   (Conductor-assigned); do not renumber the three. Fleet-wide numbering ledger stays with
   Conductor.
5. **Logical (no-FK) serving-side referrers** — D-L0-I's blast-radius catalogue covered DB-level
   FK referrers exhaustively; logical referrers were spot-checked, not exhaustively swept. Flagged
   to per-asset W5 checks for any future destructive L0 rebuild.
6. **W1 branch-staleness caveat** — retired as a risk class by the index's own recommendation
   (work from fresh origin/main worktrees, which the C8-era lanes all do); recorded here so the
   lesson survives the analysis corpus.

## §6 — Ceremony record + open residuals

- `F0_FOUNDATION → L0` stage receipt: 2026-09-08 09:54:54Z, `t1-2026-09-08-be255ffe`,
  `nirmana-stage-transition-receipt/v1`, executor SA, `manifest_sha256` = t1's. Foundation lanes
  A–E all filed under t1 09:44–09:49Z beforehand (#2428 step 2 discharged).
- `L0 → L1` receipt: 2026-09-08 10:49:23Z — downstream ordering held (L1's own close report,
  `L1_W6_CLOSE_REPORT_v1_0.md`, was published 09:55Z the same morning, PR #2436).
- **Open residual (honest):** the *closure-safe-sync-at-firing-time* retro-check — proving no L0
  asset was mid-invalidation at the 09:54:54Z firing instant — has not been run as of this
  report. Conductor's live 40/40 re-verification at cycle 322 (~17:00Z, hours after firing, with
  zero L0 events in between per the ledger) makes a violation implausible but is not the same
  check. Tracked on #1770 as a Conductor follow-up; this report will not be revised to absorb it
  silently — its outcome lands on the coordination issue.

*End L0_W6_CLOSE_REPORT_v1_0 — Conductor cycle 324, 2026-09-08. Primary sources: campaign ledger
(40 asset_frozen + 2 stage receipts), L0_STATE.md @ origin/main 72099492e, W1 analysis corpus,
charter V21 C11/C12/C13.*
