---
canonical_id: L0_W1_ANALYSIS_INDEX
version: 1.0
status: CURRENT
last_updated: 2026-09-04
---

# L0-W1 Analysis — Index and Cross-Batch Summary

Step "W1 ANALYZE" (`NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` §4) applied to all 40 L0 (Brahmagyan)
assets, per the layer's own §5 mandate. Run concurrently with the O-wave (plan §3's own
authorization: "L0-W1 analysis may run concurrently — it is read-only and needs no orchestrator"),
by 5 parallel read-only agents, one per 8-asset batch. This index does not re-decide anything —
W2 DECIDE is a separate, later step. It exists to (a) point to the 5 batch files, (b) surface
findings that span batches, and (c) record one methodology caveat discovered during this pass.

## Batch files (40/40 assets, 8 per batch)

| Batch | Assets | File |
|---|---|---|
| A | bg_sign_medical, bg_ephemeris, bg_reference, bg_texts, bg_ontology, bg_text_index, bg_rules, bg_remedies | `L0_W1_ANALYSIS_BATCH_A.md` |
| B | bg_concordance, bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index, bg_panchanga, bg_ephemeris_engine, bg_nakshatra | `L0_W1_ANALYSIS_BATCH_B.md` |
| C | bg_ghatana, bg_cohort, bg_class_lifetime_counts, bg_prashna_rules, bg_vastu_directions, bg_transit_engine, bg_transit_rules, bg_medical_mappings | `L0_W1_ANALYSIS_BATCH_C.md` |
| D | bg_nakshatra_medical, bg_dignity_reference, bg_class_priors, bg_vidhi_primitives, bg_formula_constants, bg_sky_calendar, bg_vidhi_floors, bg_muhurta_lattice | `L0_W1_ANALYSIS_BATCH_D.md` |
| E | bg_parihara_rules, bg_kota_chakra_rings, bg_sarvatobhadra_grid, bg_vedha_malefic_scale, bg_phaladeepika_latta, bg_kp_sublord_division, bg_gochara_arcs, bg_gochara_citation_resolution | `L0_W1_ANALYSIS_BATCH_E.md` |

Registry ground truth used by all 5 batches: `L0_ASSET_REGISTRY_SNAPSHOT_2026-09-04.json` (a
read-only export of `asset_registry WHERE layer='brahmagyan'`, 40 rows, taken 2026-09-04 against
production Cloud SQL via the Cloud SQL Auth Proxy — a live snapshot, not a re-derivation).

## ⚠ Methodology caveat: campaign branch staleness (discovered during this pass)

All 5 batch agents worked from this session's primary checkout, `campaign/nirmana-autonomous`,
which was found (2026-09-04, during verification of the Batch E finding below) to be **165 commits
behind `origin/main`**. That branch is this session's long-running tracking/governance branch
(SESSION_LOG, tracker, CAMPAIGN_STATE commits) — it is NOT the branch any O-wave code PR is based
on or merges into (PRs #1696-#1699 are all based on and merge into `origin/main` directly, via
dedicated worktrees). Findings grounded in **code logic and consumer wiring** (grep-based) are
unaffected by this staleness unless one of the 165 missing commits specifically touched an L0
writer or its consumer — plausible for any individual finding but not systematically checked here.
Findings grounded in **file/migration presence** are the ones actually at risk of a false alarm,
as demonstrated below. **Recommendation for W2 / before L0-W3 IMPLEMENT starts:** rebase or refresh
`campaign/nirmana-autonomous` against `origin/main` before it is used as an analysis or work base
again, to retire this risk class rather than re-discover it per finding.

**Confirmed instance:** Batch E's originally-reported MUST finding on `bg_gochara_citation_resolution`
(its integrity check appearing to require migrations 630/631, which were reported absent from this
branch) was verified live against production Cloud SQL (`SELECT status, count(*) FROM
bg_gochara_citation_resolution GROUP BY status` → `resolved=1, unresolved=13`, exactly matching the
integrity check) and downgraded in place in `L0_W1_ANALYSIS_BATCH_E.md` §8 — migrations 630/631
are applied in production and present on `origin/main`; the branch checkout was simply behind.

## Findings that span batches

- **`bg_concordance` is a confirmed built-but-unplugged instance (Batch B), with a plausible root
  cause surfaced independently by Batch A.** Batch B found `bg_concordance`'s designed MCP consumer,
  `classical_attribution_lookup.ts`, is a hardcoded stub returning `attributions: []` (its own
  docstring: "classical_attributions, classical_chunks, classical_texts dropped in WS-0...
  TODO(ws-2): repoint"), even though the underlying `classical_attributions` table is real,
  populated, and passes its integrity check. Batch A, analyzing `bg_texts` independently, found
  that `bg_concordance`'s writer has a documented BIGINT[] vs TEXT `chunk_id` schema mismatch that
  permanently empties its chunk-level pointer array. These are two symptoms of the same standing
  D-SERVICE defect the plan itself already names (§5: "Concordance bridge... its consumer lands at
  L2 — disposition here is WIRE (not retire)"). This is now corroborated from two independent
  analysis angles (serving-layer stub + writer-layer schema mismatch), not just the plan's prior
  naming of it.
- **Citation/grounding substrate exists but no formal `grounding_tier` column exists anywhere in
  the L0 layer** (confirmed independently by Batches B and C). Multiple classical-rule catalogs
  (`bg_yogas`, `bg_doshas`, `bg_transit_rules`, `bg_vastu_directions`, `bg_medical_mappings`,
  `bg_prashna_rules`, and per Batch E `bg_parihara_rules`/`bg_phaladeepika_latta`/
  `bg_kota_chakra_rings`) carry citation fields but not a `sruti`/`yukti`/`pratyaksa` label. Batch C
  is explicit that this is correctly scoped as L2 future grounding-matcher work (plan §5 L2:
  "Grounding matcher... populates classical_sources_array + corroboration counts + grounding_tier
  on the interpretive signal classes"), not an L0 gap — cited here so W2 doesn't re-litigate it
  independently per batch.
- **Two independent MUST-level "declared dependency exists but yields near-zero" findings, neither
  related to the other:**
  - Batch A: `bg_rules` live-validates a FK dependency on `bg_dasha_systems`, but 0/3,002 rows
    carry a `dasha_system_id` — the dasha-detection pattern in `l0_rules.py` may be incomplete.
  - Batch A (same batch, different asset): `bg_remedies` declares `depends_on: bg_texts` but only
    16% of rows actually derive from it at build time.
- **One MUST-level partial-serving finding (Batch D):** `bg_muhurta_lattice`'s serving capability
  (`query_muhurta_lattice.ts`) only allows filtering on 4 of the 9 factor families the writer
  produces and the DB constraint permits; the capability's own description text is now factually
  wrong about this. A concrete D-SERVICE defect, independent of the `bg_concordance` one above.
- **One MUST-level catalog-status finding (Batch D):** `bg_vidhi_floors` is the only `DRAFT`
  (not `CURRENT`) asset across all 40 — flagged for W2's disposition call on whether that reflects
  genuine content immaturity or a stale tag.
- **Two assets confirmed intentionally, not defectively, inert — do not re-litigate at W2:**
  `bg_prashna_rules` (Batch C: genuinely dormant horary facility, native-confirmed per plan §5 —
  no MCP "ask" surface exists, by design) and `bg_sarvatobhadra_grid` (Batch E: deliberately empty
  per ADJUDICATION-11, pending a school-selection ruling; candidate schools/sources for that
  decision are documented in the batch file for W2 to present).
- **No other MUST-level correctness defects were found** across the remaining ~30 assets not named
  above; batches A, B, C, D, E each record their own NOW/LATER items and clean bills of health
  per-asset in full detail — see the batch files for the complete 8-point rubric answers.

## What this index deliberately does not do

Per plan §4, W1 surfaces findings; it does not decide routes (`changed | rebuild_only |
verified_reuse | probe | producer_covered | static | empty | retired`) or triage findings to
MUST/NOW/NEVER-LATER with binding force — the batch files use that vocabulary as their own
provisional read, but W2 DECIDE is the step that actually rules on each. This index is a navigation
and cross-reference aid for W2, not a substitute for it.
