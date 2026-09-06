---
artifact: L1_DEPENDS_ON_AUDIT_v1_0.md
canonical_id: NIRMANA_L1_DEPENDS_ON_AUDIT
version: "0.1"
status: IN PROGRESS — 12 confirmed findings compiled from existing W1/W2 evidence + one new
  cross-layer finding; NOT yet a systematic grep-every-writer sweep of all 19 assets (see §3)
owner: L1 session
campaign_id: nirmana-elevation
produced_on: 2026-09-07
authorized_by: >
  DAG_CORRECTIONS_REGISTER_v1_0.md §2, which lists L1's own audit as outstanding, modeled on
  L3_DEPENDS_ON_AUDIT_v1_0.md's method. Per D-CND-09, depends_on is immutable inside the frozen
  definition (t0-2026-09-01-0e5b06fb) — nothing here is applied this campaign; this artifact
  feeds the next definition freeze per the register's own §4.
---

# NIRMĀṆA — L1 (Gaṇita) `depends_on` AUDIT

## §1 — Why this is IN PROGRESS, not COMPLETE

L3's own audit (`L3_DEPENDS_ON_AUDIT_v1_0.md`) systematically grepped every writer's real SQL
against the live table universe for all 23 of its assets. This artifact does **not** yet do that
for all 19 L1 assets — it consolidates 11 findings L1's own W1 ANALYZE wave already found and
recorded (scattered across 5 batch files + `L1_W2_DECIDE_v1_0.md`'s NEVER-LATER tier, filed
together on issue #1744) plus one new finding surfaced by a different method (cycle 135,
constituent-array resolution rather than direct SQL grep). Both methods are real and complementary
— W1's grep-based method misses edges a writer implies only through a *downstream table*
referencing another asset's output (exactly the class the new finding is), and a
constituent-array method can't see an edge with no stored array at all. **Neither alone is
complete**, matching D-CND-07's own doctrine that a green E-gate is necessary, never sufficient.

## §2 — Confirmed findings (12)

| # | asset | edge type | detail | evidence | disposition |
|---|---|---|---|---|---|
| 1 | `ga_vargas` | FALSE (`ga_positions`) + HIDDEN (`bg_shashtiamsha_deities`, L0) | `depends_on={ga_positions}` is declared but the writer never reads `chart_facts` (recomputes independently instead) — the same false edge is why two uncrossed-checked D1 computations exist (F-A1). | `ga_vargas_writer.py:814-850` (recomputes), `:584` (only external read); no `chart_facts` query anywhere in the file (F-A7) | NOW-tier, closed as documentation |
| 2 | `ga_dashas` | HIDDEN ×2 (`ga_strength` via `graha_shadbala_total`; `ga_vargas` via D1 `varga_dignity`) + hidden L0 (`reference_nakshatras`) | Because `ga_vargas` is undeclared, the orchestrator schedules the two concurrently — measured live on build `6479bb56…`: both started `00:20:27`, `ga_vargas` finished `00:21:56`, `ga_dashas` wrote from `00:20:28`, so `ga_dashas` silently read the *previous* build's divisionals under MVCC. **The one finding here with a measured live correctness consequence.** | `ga_dashas_writer.py:525,549,563`, `:110`; `build_run_assets` timestamps (F-A13) | **MUST**-severity by consequence; mitigated by sequential single-asset dispatch at W4 (workaround, not a fix — #1744) |
| 3 | `ga_sensitive` | semantic, not hidden/false | `depends_on: ga_positions` is an **ordering** edge, not a read edge — the writer re-derives positions from `birth_params` via `compute_chart` rather than reading L1's stored longitudes. No drift measured. | `ga_sensitive_writer.py:2616`, `:3088`; no `SELECT … FROM chart_facts` (F-B11) | NEVER-LATER — document the edge's real semantics, don't remove it |
| 4 | `ga_sensitive_degree` | HIDDEN (`reference_nakshatra`/`reference_signs`, L0; `ga_yoga` via best-effort import) | If the `ga_yoga` import fails, 7 rows/ayanamsha vanish with no error and no `detector_unavailable` row. | `ga_sensitive_degree_writer.py:695-698`, `:750`, `:769` (F-B15) | NOW-tier |
| 5 | `ga_nakshatra` | HIDDEN (`reference_signs`, L0) | Undeclared read, `bg_reference`-owned table. | `pipeline/orchestrator/writers/ga_nakshatra.py` `FROM reference_signs` (F-B23) | NEVER-LATER |
| 6 | `ga_structural` / `ga_condition` | shared-ownership, no declared edge between the pair | Avasthā ownership split across two assets with no cross-edge; both writers contain all five avasthā-family names; `ga_condition` owns 2 categories but counts 7. | `fact_category_ownership`; both writer files (F-C18) | NOW-tier, closed via `fact_category_ownership` backfill |
| 7 | `ga_condition` | HIDDEN ×4 (L0 reference tables: dignity, motion thresholds, combustion orbs, naisargika friendships) | DAG understates real inputs by 4 undeclared L0 edges. | `ga_condition_writer.py:606,635,657,684` (F-C23) | NOW-tier |
| 8 | `ga_yoga` | HIDDEN ×2 (`ga_strength` via `graha_shadbala_total`; `ga_sensitive` via `karakamsa_position`) | `depends_on={ga_structural,ga_dashas}` — neither of these two reads is declared. | `ga_yoga_writer.py:183-206`, `:384-392` (F-D3) | NOW-tier |
| 9 | `ga_sade_sati` | FALSE ×2, over-declared (`ga_strength`, `ga_panchanga`) | Zero shadbala reads; the `ga_panchanga` edge is a code import of the transit engine, not a data edge — inflates the DAG and delays the asset behind non-consumed upstreams. | grep of `ga_sade_sati_writer.py`; `_verify_upstream_rows:1435-1483` gates only GA3/4/6/7/8 (F-D15) | NOW-tier |
| 10 | `ga_medical` | HIDDEN ×2 (`bg_medical_mappings`, `bg_nakshatra_medical`, both L0) | Both read inside `try/except` degrading to empty while still inserting 45 rows reporting success — no detector distinguishes "45 correct" from "45 empty". | `depends_on={ga_condition,ga_positions}`; reads at `:139-143`/`:213-217`; swallow at `:153-156` (F-E7) | NOW-tier |
| 11 | `ga_tajaka` | FALSE ×2 (`ga_dashas`, `ga_positions`) + §N.5 authority inversion | Neither read: no `chart_dashas` reference exists; the natal chart is re-derived via `compute_chart(bp)` rather than referenced from stored L1 longitudes. Only `ga_sensitive` (`tajik_triraashipathi`) is genuinely consumed. | `_read_trirashipathi:450-458` (F-E18) | NOW-tier |
| 12 | `ga_yoga` | HIDDEN (`ga_positions`) — **new, cycle 135, distinct from finding #8's two edges above** | `depends_on={ga_structural,ga_dashas}` (confirmed live, unchanged) does not declare `ga_positions`, yet `ga_yoga_firings.constituent_fact_ids` holds 36/40 distinct `fact_id`s (canonical chart) that resolve into exactly `ga_positions`' own 5 categories (`graha_position`/`graha_sign_attributes`/`bhava_cusps`/`house_chalit`/`sandhi_flag`). Found via constituent-array resolution, a method W1's original grep pass did not use — confirming §1's point that the two methods are complementary, not redundant. Confirmed by the Conductor on issue #2180 as "a real, separate defect" alongside its ruling on the coordinated-rebuild sequencing question that surfaced it. | live query against `ga_yoga_firings`/`chart_facts`; `asset_registry.depends_on` (issue #2180) | Open — feeds this register; not yet given its own F-id since it was found post-W2 |

**Summary: 8 assets with at least one confirmed hidden/false/semantic-mismatch edge (of L1's 19);
9 distinct edge findings hidden, 5 false/over-declared, 1 semantic-clarification-only, 1 shared-
ownership gap.** One (`ga_dashas`↔`ga_vargas`, finding #2) has a measured live correctness
consequence; the rest are DAG-accuracy findings without demonstrated data corruption to date.

## §3 — What this audit has NOT yet done

Unlike L3's systematic sweep, this pass has **not** grepped the remaining ~11 L1 assets not named
above (`ga_positions`, `ga_panchanga`, `ga_strength`, `ga_vichara`, `ga_transit_anchors`,
`ga_ayurdaya`, `ga_vastu`, `ga_prashna`, plus `ga_yoga`/`ga_sade_sati`/`ga_tajaka`'s *remaining*
declared edges beyond the ones already flagged above) against their writers' real SQL for
undeclared reads, the way L3's method does for every asset regardless of whether W1 already
flagged something. That is the natural next expansion of this artifact, following L3's own
stated method exactly (§2 of `DAG_CORRECTIONS_REGISTER_v1_0.md`): pull the declared side from
`asset_registry`, build the `target_table → asset_id` owner map, then grep each writer's real SQL
for `\b(from|join|update|into|delete from)\s+<table>\b` against the live table universe,
longest-match-first, reporting both hidden and false edges.

## §4 — Deliberate non-edges (D-CND-10)

None identified for L1 to date. If a future pass finds a pair where an edge looks missing but
adding it would break something (matching the shape of §3.1 in `DAG_CORRECTIONS_REGISTER_v1_0.md`
— `ka_kshetra`↔`mi_bhara`'s version-pin-not-edge resolution), it belongs here, not in §2.
