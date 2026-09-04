---
canonical_id: L0_W2_DECIDE
version: 1.0
status: CURRENT
last_updated: 2026-09-04
---

# L0-W2 DECIDE

Step "W2 DECIDE" (`NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` §4) applied to all 40 L0 (Brahmagyan)
assets, on the findings in `L0_W1_ANALYSIS_INDEX_v1_0.md` + `L0_W1_ANALYSIS_BATCH_{A-E}.md`. Per
§4: one route per asset; every finding triaged `MUST` (correctness — gates the capsule) / `NOW`
(in-layer improvement — admitted by clear value, bounded cost, or the last-cheap-chance cascade
rule) / `NEVER/LATER` (logged with reason, closed); chapter/doctrine citation on every `NOW`;
decisions as one-line ledger entries. This step does not implement anything (W3 IMPLEMENT does) —
it rules on route + triage only.

## §1 — Route assignment (40/40)

Routes follow plan §5's own explicit L0 count exactly (2 `verified_reuse` · 2 `probe` ·
3 `producer_covered` · 1 `static` · 1 `empty` · 31 `rebuild_only`) — W1 found no evidence any
asset should deviate from that pre-scoped template.

| asset_id | route | rationale |
|---|---|---|
| bg_sign_medical | `producer_covered` | rider on `bg_medical_mappings`' multi-`@register` writer |
| bg_ephemeris | `rebuild_only` | — |
| bg_reference | `rebuild_only` | — |
| bg_texts | `verified_reuse` | plan §5 named; full lineage proof already in its `integrity_check_sql` (baseline table + content-hash) |
| bg_ontology | `rebuild_only` | — |
| bg_text_index | `verified_reuse` | plan §5 named; corpus + embeddings, non-deterministic external embedding call |
| bg_rules | `rebuild_only` | — |
| bg_remedies | `rebuild_only` | — |
| bg_concordance | `rebuild_only` | — |
| bg_yogas | `rebuild_only` | — |
| bg_dasha_systems | `rebuild_only` | — |
| bg_doshas | `rebuild_only` | — |
| bg_compendium_index | `rebuild_only` | — |
| bg_panchanga | `probe` | service, health-probe verified against FORENSIC anchors |
| bg_ephemeris_engine | `probe` | service, file-hash-pinned health-probe |
| bg_nakshatra | `rebuild_only` | — |
| bg_ghatana | `rebuild_only` | — |
| bg_cohort | `rebuild_only` | — |
| bg_class_lifetime_counts | `rebuild_only` | — |
| bg_prashna_rules | `rebuild_only` | data layer only — horary *facility* stays dormant, native call (§3 below) |
| bg_vastu_directions | `rebuild_only` | — |
| bg_transit_engine | `producer_covered` | sub-table of `bg_transit_rules`' writer (`has_writer=false` correctly modeled) |
| bg_transit_rules | `rebuild_only` | — |
| bg_medical_mappings | `rebuild_only` | — |
| bg_nakshatra_medical | `producer_covered` | rider on `bg_medical_mappings`' multi-`@register` writer |
| bg_dignity_reference | `rebuild_only` | clean pass, no remediation needed |
| bg_class_priors | `rebuild_only` | route unaffected by the MUST finding below (data itself is sound; the finding is a doc/registry reconciliation) |
| bg_vidhi_primitives | `rebuild_only` | — |
| bg_formula_constants | `rebuild_only` | — |
| bg_sky_calendar | `rebuild_only` | — |
| bg_vidhi_floors | `rebuild_only` | route unaffected by the MUST status finding below |
| bg_muhurta_lattice | `rebuild_only` | route unaffected by the MUST serving-gap finding below |
| bg_parihara_rules | `rebuild_only` | — |
| bg_kota_chakra_rings | `rebuild_only` | — |
| bg_sarvatobhadra_grid | `empty` | ADJUDICATION-11, deliberately empty pending school ruling |
| bg_vedha_malefic_scale | `rebuild_only` | already `asset_frozen` (P4); O-wave exit rehearsal exercised it twice more this session, both `skip_no_delta` |
| bg_phaladeepika_latta | `rebuild_only` | — |
| bg_kp_sublord_division | `rebuild_only` | — |
| bg_gochara_arcs | `rebuild_only` | — |
| bg_gochara_citation_resolution | `static` | migration-seeded, `data_disposition: RETAINED_AS_CAPITAL`, not a rebuildable writer output |

## §2 — Finding triage ledger

### MUST (gates the W5 capsule for the named asset — must resolve before that asset FREEZEs)

1. **`bg_muhurta_lattice`** — `query_muhurta_lattice.ts`'s `FACTOR_FAMILIES` allowlist covers 4 of
   the 9 factor families the writer produces and the DB constraint requires (migration 530 added
   `hora`/`lagna`/`nakshatra`/`tithi`/`vara`, ~72,580 of ~165K rows, unreachable via explicit
   filter); the capability's own description text is now factually wrong. Cite: D-SERVICE
   (plan §2, "built-but-unplugged" defect class). **Action:** W3 extends the allowlist to all 9
   families and corrects the description string — small, well-scoped TS change, no schema touch.
2. **`bg_vidhi_floors`** — `catalog_status: DRAFT`, the only non-`CURRENT` asset among all 40,
   while its dependency `bg_vidhi_primitives` is `CURRENT`. Cite: CLAUDE.md §B.8 (versioning
   discipline — "registries must not disagree"). **Action:** native/W3 confirms whether this
   reflects genuine content immaturity (in which case DRAFT is correct and this MUST closes as
   "status accurate, no change") or a stale tag that should flip to CURRENT alongside its
   dependency. Not resolved unilaterally here — see §3.
3. **`bg_class_priors`** — three disagreeing row-count figures for the same asset: registry
   `target_floor`/`english_description` say 171, the writer module's docstring says 165, the
   writer's own itemized `run()` breakdown (17+12+6+30+99) sums to 164. Cite: CLAUDE.md §B.8.
   **Action:** W3 reconciles against the live count and corrects whichever of the three is wrong
   (registry floor, docstring, or itemization) — an honest "needs reconciliation," not a guess at
   which number is right (§N.8).

### NOW (in-layer improvement, admitted by value/bounded cost — cited per plan §4)

~~D-GROUNDING (P3) — formalize `grounding_tier` where citation substrate already exists in-row:~~

**CORRECTION (2026-09-04, caught during L0-W3 scoping, before any of items 4-11 were
implemented):** items 4-10 below were mis-triaged NOW. Plan §5's own L2 section is explicit:
"populates `classical_sources_array` + corroboration counts + `grounding_tier` **on the
interpretive signal classes** (~15-20 classes, not 50,104 rows uniformly)" — `grounding_tier` is
an L2-Bodha-boundary concept applied to interpretive signal classes, not an L0 catalog/reference-
row property. Batches A and B of the underlying W1 analysis already applied this scoping
correctly for `bg_yogas`/`bg_doshas`/`bg_texts` (see those batch files: "grounding is applied
selectively... the catalog is the source, not the claim being graded" — routed NEVER/LATER for
exactly this reason). Batches C/D/E did not apply the same scoping consistently for the assets
below, and this ledger inherited that inconsistency uncorrected. Re-triaged NEVER/LATER, moved to
§2's NEVER/LATER list at items 30a-30g below, same numbers preserved for traceability rather than
renumbering the whole ledger. Basis: plan §5 (verbatim above) + CLAUDE.md B.1 (facts/interpretation
separation — grounding_tier is an L2+ interpretive-layer concept, assigning it at L0 would blur
that boundary) + the "verify, don't trust, including your own prior output" discipline this
session's decision log already establishes (D-VR-14/24/27/28 precedent). 8 items reclassified
(4-11), now §2 NEVER/LATER items 30a-30h.

~~4. `bg_vastu_directions` (32 rows, mostly `sruti`/some `yukti`) — cite D-GROUNDING.~~
~~5. `bg_transit_rules` (+ sibling `bg_transit_moorti`, 75+27 rows, `sruti`) — highest-leverage
   grounding candidate in the batch (feeds live interpretive transit-quality judgments) — cite
   D-GROUNDING.~~
~~6. `bg_medical_mappings` (+ `bg_nakshatra_medical`/`bg_sign_medical`, 60 rows, `sruti`) — cite
   D-GROUNDING + Ethical Framework disclosure-tier relevance (medical-adjacent content).~~
~~7. `bg_formula_constants` (17 rows) — map the existing `class` column
   (CLASSICAL/NATIVE_JUDGMENT/ENGINEERING) onto `grounding_tier` — cite D-GROUNDING; reuses
   existing classification, no new derivation.~~
~~8. `bg_class_priors` (separate from its MUST above) — schema already carries `citation`/
   `prior_basis`; add `grounding_tier='yukti'` — cite D-GROUNDING.~~
~~9. `bg_parihara_rules` — census table's `disposition` field (`computed`/`not_computed`/
   `not_in_corpus`) already encodes what a `grounding_tier` needs; formalize the mapping — cite
   D-GROUNDING.~~
~~10. `bg_prashna_rules` — formalize `grounding_tier` on the citation catalog (data layer only,
    separable from the dormant-facility native call in §3) — cite D-GROUNDING.~~
~~11. `bg_ghatana` — lower priority: formalize `grounding_tier` on the `citations` JSONB field only
    if/when L2+ signal classes start requiring it uniformly — cite D-GROUNDING; not urgent, the
    plan explicitly scopes grounding to ~15-20 L2 interpretive signal classes, not L0 taxonomy rows.~~
(All of 4-11: struck, moved to NEVER/LATER §2 items 30a-30h — see correction note above.)

D-SERVICE (plan §2) — wiring/coverage gaps, none rising to MUST:

12. ~~`bg_concordance` — WIRE `classical_attribution_lookup.ts` to live `classical_attributions`~~
    **RESCOPED to NEVER/LATER, L2 (2026-09-04, L0-W3 Batch 1).** Investigated the actual wiring
    work before implementing it: `classical_attribution_lookup.ts`'s interface is keyed by MSR
    `signal_id` (input: `signal_ids: string[]`; output rows carry `msr_signal_id`,
    `attribution_type`, `content`, `chapter`, `verse_range`), but `classical_attributions`
    (bg_concordance's own table) is keyed by `(topic_id, school)` and has no `signal_id` column
    or join path to one — repointing the stub to bg_concordance's table as originally proposed is
    not a valid fix, it would be a schema mismatch masquerading as a repoint. The real target is
    almost certainly `bodha_msr_signals.classical_sources_jsonb`/`rule_ids`/`text_chunk_ids` (an
    L2-Bodha table, migration 325, explicitly documented as "structured L0 bridge" — this is very
    likely what the stub's own `TODO(ws-2): repoint to... bodha_signals citation scaffolds` names),
    joined against `classical_text_chunks`/`sutravali_rules` for the display fields — plus a real
    design question (how `attribution_type`'s confirms/contradicts/partial/extends/silent grading
    derives from a flat citation list, which nothing in the current schema answers). This is
    genuine L2-Bodha design work, not a bounded L0-W3 repoint. Re-reading the plan's own text
    confirms the original W1/W2 scoping was wrong here too: "its consumer lands at L2" (plan §5)
    means the CONSUMER-SIDE wiring is L2's job — L0's job (already done, verified in W1) is
    keeping `bg_concordance`'s own 720 rows correct and fresh. Handed to L2-W3 with this
    investigation's findings attached so that work starts from a real lead, not a re-derivation.
13. `bg_concordance` — **verified 2026-09-04 (L0-W3 Batch 1), live against production:**
    `bg_text_index` coverage is UNCHANGED — `classical_text_chunks`: 10,651 total, 7,010 tagged
    (still 34% unclassified), 361 distinct topic_tag values, exactly matching the historical
    figure. So the 721-row floor question this item asked about is answered: no, coverage has not
    progressed, the floor doesn't need raising for that reason. **New finding surfaced by this
    verification, not previously known:** live `classical_attributions` row count is **720**, one
    row short of the registry's `target_floor=721` (distinct topic count matches exactly at 361
    on both sides — the discrepancy is specifically in row count, not topic coverage). Small,
    not urgent, but real — added as new item 13a below rather than silently noted and dropped.
14. **DONE (2026-09-04, L0-W3 Batch 1, PR pending).** `bg_sky_calendar` — new capability
    `query_sky_calendar.ts` (table `bg_sky_events`), mirroring `query_muhurta_lattice.ts`'s
    structure exactly: interval filter, `event_type`/`primary_body` optional filters, honest
    `empty_reason` naming the rolling-horizon cause, explicit disclaimer that chart-contact
    interpretation is out of scope. 11 new tests, all passing; full `src/lib/retrieval/` suite
    (1922 tests) unaffected; `tsc`/`eslint` clean. Registered in `L0_brahmagyan/index.ts`.
15. `bg_reference` — re-verify at sub-table granularity whether `reference_houses` and
    `reference_strength_systems` are genuinely INPUT-ONLY-by-design or orphaned — cite D-SERVICE.
16. `bg_reference` — resolve the `reference_nakshatra` vs `reference_nakshatras` one-character
    naming-collision hazard already flagged in `ZERO_CONSUMER_EVIDENCE_v1_0.md` — cite D-SERVICE.
17. **DONE via verification (2026-09-04, L0-W3 Batch 1) — confirmed live, real, reachable, no
    code change needed.** `bg_vidhi_primitives` / `bg_vidhi_floors` — the "V-2 MCP-resource face"
    is real: `platform-mcp/src/resources/vidhi_registry_resource.ts` registers
    `marsys://vidhi/registry` (full registry) and `marsys://vidhi/floor/{intent}` (per-intent,
    all 8 enumerated) as live, listed, readable MCP resources. It serves the TS-vendored mirror
    (`platform-mcp/src/resources/vidhi/`, drift-guarded against `platform/src/lib/vidhi/` by
    `vidhi_registry_parity.test.ts`), not a direct read of the `vidhi_primitives`/
    `vidhi_intent_floors` DB tables — an intentional, established pattern (the same
    mirror-plus-CI-parity-gate design both writers already use), not a gap. The writer docstrings'
    "V-2 MCP-resource face" phrasing is accurate in substance; W2's original framing ("no resource
    registration found... beyond the TS types file") was itself a read-only-pass artifact — the
    actual resource file (`vidhi_registry_resource.ts`) lives one directory up from where that
    pass looked (`resources/vidhi/types.ts`), not inside it.
13a. **NEW (2026-09-04, surfaced by item 13's verification).** `bg_concordance`'s live row count
    (720) is one short of its registry `target_floor` (721), while distinct-topic coverage matches
    exactly (361/361) on both sides. Small, not urgent — cite CLAUDE.md §N.4 (floors track
    achieved counts; a 1-row gap needs a look, not a guess at which side is wrong). W3 follow-up:
    diff the writer's computed topic set against the 361 currently in `classical_attributions` to
    find the specific missing topic/school combination, or confirm 721 was itself a stale
    over-count from before a legitimate single-topic consolidation.
18. `bg_kota_chakra_rings` — confirm the `ka_kota_chakra` → `kala_kota_chakra` serving path reads
    this L0 table's rows correctly end-to-end (lineage-proof exercise, cheap given the existing
    byte-identity check) — cite D-SERVICE.
19. `bg_muhurta_lattice` (separate from its MUST) — reconcile `target_floor` (91,477, stale) against
    the writer's own binding v2-corpus minimum (164,575, post-migration-530) — cite CLAUDE.md §N.4
    (floors are aspirational/achieved-count, never fabricated, and should track what the writer
    itself now guarantees).
20. `bg_sign_medical` — disclose the shared-writer (multi-`@register`) pattern in the W2 ledger
    (this entry) so a future dependency change to `bg_medical_mappings` doesn't silently affect
    `bg_sign_medical`/`bg_nakshatra_medical` — cite D-SERVICE hygiene. Considered closed by this
    disclosure; no code change required.

§N.8 (earned-signal) / B.8 (registry accuracy) — cheap, concrete, checkable:

21. `bg_ephemeris` — distinguish "0 rows because pre-populated" from "0 rows because `pyswisseph`
    unavailable" in `WriterResult.notes` — cite §N.8 (a signal needs a real detector, not an
    inferred proxy); improves O-wave WP-1 receipt/staleness signal quality.
22. `bg_rules` — investigate the zero-yield `bg_dasha_systems` linkage (0/3,002 rules carry a
    `dasha_system_id` despite live FK validation against it; only one hardcoded
    `"dasha_system_id": "vimshottari"` literal found in a quick grep, suggesting the
    dasha-detection pattern in `l0_rules.py` may be incomplete) — cite D-GROUNDING + §N.8.
23. `bg_remedies` — disclose that `depends_on: ["bg_texts"]` is accurate for only 16% of rows
    (`corpus_sweep`, 54/341) — the other 84% are static Python literals; a one-line disposition
    note so a future delta-skip/staleness check doesn't over-invalidate on every `bg_texts` change
    — cite D-SERVICE / O-wave WP-1 (truthful invalidation).
24. `bg_cohort` — annotate the `depends_on: ["bg_ephemeris_engine"]` edge as "shared config helper,
    not a data read" so a future DAG reader doesn't assume a table read — cite D-SALIENCE / DAG
    hygiene.
25. `bg_vastu_directions` — correct the registry `english_description`'s "~22 rows" to the actual
    24-row remedials count — cite §B.8.
26. `bg_kp_sublord_division` — correct the writer module's own docstring line ("depends_on: [] —
    pure reference geometry, no upstream dependency") to acknowledge the real, optional,
    fail-open cross-check read of `reference_nakshatra` — editorial-only, very low cost.
27. `bg_parihara_rules` — add `integrity_check_sql` (the only asset in Batch E without one, unlike
    its 5 siblings which all have byte-identity checks) — direct precedent to copy from, bounded
    cost.
28. `bg_gochara_citation_resolution` — once (or since — see D-VR-27) the analysis branch is
    reconciled with `main`'s migration set, re-verify the full byte-identity hash in
    `integrity_check_sql` live. **Status: substantially done** — the row-count *shape* was
    independently re-verified live against production this session (D-VR-27); the exact byte
    hash was not separately re-run and is a trivial follow-up, not a new investigation.
29. `bg_text_index` — the 34% unclassified-chunk gap (3,641/10,651) is a real, disclosed limitation
    of the deterministic keyword classifier; extending the keyword/domain vocabulary is a bounded
    (Python dict additions) NOW candidate — cite D-GROUNDING (this is the substrate the L2
    grounding matcher will consume, plan §5).

### NEVER/LATER (logged, closed, not reopened by this wave)

30. `bg_yogas` — applying `grounding_tier` to catalog-*definition* rows (vs. interpretive firings)
    — LATER. Reason: plan §2 D-GROUNDING is explicit that grounding applies to interpretive signal
    classes, not uniformly to every catalog row; the catalog is the source, not the claim.
31. `bg_dasha_systems` — a dasha-system arbitration/authority-profile surface — LATER. Reason:
    explicitly scoped to L3-W1's Temporal Concordance Contract ("authority profiles generalized
    from the two seed tables," plan §5), not an L0 concern.
32. `bg_doshas` — populating `associated_remedies`/`source_chunk_ids` + `grounding_tier` — LATER.
    Reason: L2 grounding-matcher territory (plan §5); the catalog is internally consistent with
    what it honestly claims today (fields asserted empty, not silently populated).
33. `bg_kota_chakra_rings` — primary-source ingestion (tier-(iii)→tier-(i) upgrade) — LATER. Reason:
    a real, named, separately-tracked corpus-ingestion work item; the writer already files the gap
    honestly rather than fabricating a citation.
34. `bg_phaladeepika_latta` — Ketu's missing Lattā counting rule — LATER. Reason: genuine
    corpus-research item (locating the missing passage), not an L0 writer defect; already an
    honest, disclosed omission.
35. `bg_parihara_rules` — named corpus gaps (mṛtyu-yoga, dagdha-yoga, Śiva-vāsa OCR-translation) —
    LATER. Reason: requires OCR-translation work on `classical_text_chunks`, out of L0 writer
    scope.
36. `bg_gochara_citation_resolution` — the 10 (or more, post-correction) `unresolved` corpus gaps
    — LATER. Reason: real corpus-ingestion work items, already disclosed as gaps, not fabricated.
37. `bg_sky_calendar` / `bg_muhurta_lattice` — the `ka_kshetra` chart-contact join — LATER. Reason:
    explicitly staged as W3 work per `ka_kshetra.py`'s own docstring; tracked there, not forgotten,
    not re-opened here.
38. `bg_nakshatra_medical` — a formal `grounding_tier` column on this specific sub-table — LATER.
    Reason: defer to the L2 grounding-matcher work named in plan §5; L0's job is the citation
    substrate (already present), not the tier label.
30a. `bg_vastu_directions` — formalize `grounding_tier` (mostly `sruti`, some `yukti`) — LATER,
    reclassified from NOW (correction above). Reason: same as items 30-38's `bg_yogas`/`bg_doshas`
    pattern — plan §5 scopes `grounding_tier` to L2 interpretive signal classes, not L0 catalog
    rows; the citation substrate (`classical_citation` per row) is already present and complete
    for L2's grounding matcher to consume when it lands.
30b. `bg_transit_rules` (+ sibling `bg_transit_moorti`) — formalize `grounding_tier` — LATER, same
    reason as 30a. This remains the highest-leverage L2 grounding-matcher input in the batch
    (feeds live interpretive transit-quality judgments) — worth flagging to L2-W1/W2 as a
    priority candidate when that layer opens, not worth building at L0.
30c. `bg_medical_mappings` (+ `bg_nakshatra_medical`/`bg_sign_medical`) — formalize
    `grounding_tier` — LATER, same reason as 30a. The Ethical Framework disclosure-tier relevance
    (medical-adjacent content) makes this a priority candidate for L2, not a reason to build it
    early at L0 — the existing `not_diagnosis`/`jyotish_indication` discipline already carries the
    disclosure obligation independent of a formal tier label.
30d. `bg_formula_constants` — map the existing `class` column onto `grounding_tier` — LATER, same
    reason as 30a; the `class` column (CLASSICAL/NATIVE_JUDGMENT/ENGINEERING) already does the
    informal work this would formalize, and remains available for L2 to consume as-is.
30e. `bg_class_priors` — add `grounding_tier='yukti'` per row — LATER, same reason as 30a; the
    `citation`/`prior_basis` columns already carry what L2 needs.
30f. `bg_parihara_rules` — formalize the census table's `disposition` field into a
    `grounding_tier` mapping — LATER, same reason as 30a.
30g. `bg_prashna_rules` — formalize `grounding_tier` on the citation catalog — LATER, same reason
    as 30a; separable from and does not block the dormant-facility native call in §3 either way.
30h. `bg_ghatana` — formalize `grounding_tier` on the `citations` JSONB field — LATER, same reason
    as 30a (this one already carried the correct caveat in its original W1 finding; reclassified
    here purely for ledger consistency with 30a-30g, not a new finding).

## §3 — Named native decision points (not resolved by this session)

Per plan §4/§5, these are product/adjudication calls presented with costs, not resolved
unilaterally:

- **`bg_prashna_rules` dormant-facility disposition.** Data layer complete, well-cited,
  retrieval-reachable; the horary "ask" facility itself has no serving surface. Cost if opened:
  LOW-to-MODERATE on data/compute (schema + `ga_prashna` computation logic already exist); the
  real cost is serving/UX (a dedicated horary MCP tool) + product decisions about disclosure tier
  for a live horary product (CLAUDE.md Ethical Framework — probabilistic/calibrated/consenting-
  audience framing needs explicit horary-specific treatment). Recommendation if asked: keep
  dormant with the go-live rehearsal plan named in plan §7.3, since nothing about L0 elevation
  requires opening it now.
- **`bg_sarvatobhadra_grid` school-selection ruling (ADJUDICATION-11).** Candidate source threads
  on record: the `school_tag` column design (multi-school-capable schema), two unresolved corpus
  citations in `bg_gochara_citation_resolution` (`Muhurta Chintamani`/`Jyotish Sara Sangraha`,
  `Prasna Marga`), and the current disclosed `algorithmic_approximation` fallback
  (`uncited_extension=true`). Consumer-side plumbing (`ka_vedha_gochara`) is already wired to
  activate on population with zero code change, per W1 — this lowers the cost of a future
  decision. Populate only on a ruling; not populated by this session.
- **`bg_vidhi_floors` catalog_status (MUST §2 item 2, restated here as a decision, not just a
  defect).** Native/W3 to confirm DRAFT is either accurate (genuine content immaturity, e.g. the
  newer `spirituality_deepdive`/`education_deepdive`/`progeny_deepdive` floors carry
  `[MANDATORY]`/`[CANDIDATE]` in-writer notes) or stale (should flip to CURRENT alongside its
  now-CURRENT dependency `bg_vidhi_primitives`).

## §4 — Summary

**Updated 2026-09-04, post-correction (see NOW section header note).** 40/40 assets routed. 3 MUST
findings (all registry/serving-consistency, none a data-correctness defect in the underlying
content) — **all 3 addressed in PR #1705** (L0-W3, first IMPLEMENT wave; open at the time of this
correction, merge status tracked in CAMPAIGN_STATE.md). 18 NOW findings (originally
26; 8 reclassified to NEVER/LATER on correction — see below), all D-SERVICE wiring/coverage gaps or
§N.8/B.8 documentation-accuracy items, none touching `grounding_tier` (that vocabulary is L2-scoped
per plan §5, not L0). 17 NEVER/LATER items (originally 9; +8 from the correction), all correctly
scoped to L2/L3 work named elsewhere in the plan or to genuine out-of-scope corpus-research items,
not reopened here. 3 named native decision points carried forward, not resolved unilaterally. No
asset needed a route change from plan §5's pre-scoped template — W1's findings confirmed the
template rather than overturning it.

**Self-correction recorded, not silently fixed:** the original NOW list (items 4-11) proposed
formalizing `grounding_tier` directly on 8 L0 catalog/reference tables. Plan §5's own text places
`grounding_tier` at L2 ("`grounding_tier` on the interpretive signal classes... not 50,104 rows
uniformly"), and this session's own W1 batches A/B had already applied that scoping correctly for
`bg_yogas`/`bg_doshas`/`bg_texts` — batches C/D/E did not apply it consistently, and this ledger
inherited the inconsistency. Caught before any of the 8 items were implemented (during L0-W3
scoping, immediately after PR #1705 landed the 3 MUST fixes), corrected in place with the
reasoning preserved rather than silently deleted — struck-through original text stays visible, new
NEVER/LATER entries 30a-30h carry the corrected disposition. See CAMPAIGN_STATE.md decision log for
the full account.

**Next:** L0-W3 IMPLEMENT continues with the remaining 18 NOW items, batched on disjoint write-sets
per plan §4, then L0-W4 EXECUTE dispatches the remaining wave-0/1/2 build obligation.
