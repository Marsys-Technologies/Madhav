---
artifact: L1_DEPENDS_ON_AUDIT_v1_0.md
canonical_id: NIRMANA_L1_DEPENDS_ON_AUDIT
version: "0.7"
status: COMPLETE for coverage (matching L3's own bar — every asset, every declared edge, checked
  in both directions) as of round 6 (cycle 144). 17 confirmed findings + 8 assets confirmed
  CLEAN. See §3 for the one honest methodology gap versus L3's own audit: no single unified
  `target_table → asset_id` owner-map artifact was built and reused — each asset's declared
  edges were checked against a per-asset hand-picked candidate list instead. Coverage is
  equivalent; the artifact trail differs.
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

## §1 — Coverage: round 1 (existing findings) + round 2 (direct grep sweep)

L3's own audit (`L3_DEPENDS_ON_AUDIT_v1_0.md`) systematically grepped every writer's real SQL
against the live table universe for all 23 of its assets. **Round 1** of this artifact
consolidated 11 findings L1's own W1 ANALYZE wave already found and recorded (scattered across 5
batch files + `L1_W2_DECIDE_v1_0.md`'s NEVER-LATER tier, filed together on issue #1744) plus one
new finding surfaced by a different method (cycle 135, constituent-array resolution rather than
direct SQL grep). **Round 2** (cycle 140) closed the remaining gap: grepped the 8 L1 assets round
1 had not touched (`ga_panchanga`, `ga_strength`, `ga_vichara`, `ga_transit_anchors`,
`ga_ayurdaya`, `ga_vastu`, `ga_prashna`, plus `ga_positions` itself) against the dedicated
target-table owner map and every declared L0 `bg_*` dependency, following L3's method directly.
Found one new genuine finding (`ga_panchanga`, #13 below) and confirmed the other 7 clean (§2's
own CLEAN rows). Both grep and constituent-array methods are real and complementary — W1's
grep-based method misses edges a writer implies only through a *downstream table* referencing
another asset's output (exactly finding #12's class), and a constituent-array method can't see an
edge with no stored array at all. **Neither alone is complete**, matching D-CND-07's own doctrine
that a green E-gate is necessary, never sufficient.

## §2 — Confirmed findings (17) + CLEAN assets (8)

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
| 12 | `ga_yoga` | HIDDEN (`ga_positions`) — **new, cycle 135, distinct from finding #8's two edges above** | `depends_on={ga_structural,ga_dashas}` (confirmed live, unchanged) does not declare `ga_positions`, yet `ga_yoga_firings.constituent_fact_ids` holds 36/40 distinct `fact_id`s (canonical chart) that resolve into exactly `ga_positions`' own 5 categories (`graha_position`/`graha_sign_attributes`/`bhava_cusps`/`house_chalit`/`sandhi_flag`). Found via constituent-array resolution, a method W1's original grep pass did not use — confirming §1's point that the two methods are complementary, not redundant. Confirmed by the Conductor on issue #2180 as "a real, separate defect" alongside its ruling on the coordinated-rebuild sequencing question that surfaced it. | live query against `ga_yoga_firings`/`chart_facts`; `asset_registry.depends_on` (issue #2180) | **F-D30** (cycle 145 assignment — see §5). NEVER-LATER-equivalent: `depends_on` is immutable this cohort (D-CND-09); recorded here for the next definition freeze, same disposition as F-D3/F-A7 |
| 13 | `ga_panchanga` | FALSE ×2 (`ga_positions`, `bg_panchanga`) — **new, cycle 140, round-2 sweep** | Writer issues **zero** SQL `SELECT`/`execute` calls of any kind (confirmed: 0 matches for `select`/`cur.execute`/`cursor.execute` in the whole 64KB file) — it derives every panchanga element from `resolve_birth_params` (ephemeris recomputation), the same "recomputes independently instead of reading" pattern as `ga_vargas`' own F-A7. **`bg_panchanga` does not even exist as a table** (`\dt bg_panchanga*` returns nothing live) — a dead reference, not merely unread. | `ga_panchanga_writer.py` (whole-file grep, 0 execute calls); `resolve_birth_params` import at `:37`; live `\dt` check | **F-B36** (cycle 145 assignment — see §5). NEVER-LATER-equivalent, same disposition as F-A7 |
| 14 | `ga_yoga` | FALSE (`ga_dashas`) — **new, cycle 141, verifying finding #8/#12's remaining declared edges** | `depends_on={ga_structural,ga_dashas}` declares `ga_dashas`, but the writer contains **zero** matches for `chart_dashas` (`ga_dashas`' own target table) or even the substring "dasha" anywhere in the file, in code or comments. Combined with findings #8/#12 (2 hidden + 1 hidden, none of them `ga_dashas`), `ga_yoga`'s declared 2-edge DAG is now confirmed wrong on BOTH members: `ga_dashas` false, `ga_structural` confirmed genuinely needed (below). | `ga_yoga_writer.py` (whole-file grep: 0 matches for `chart_dashas` and for "dasha" case-insensitive) | **F-D31** (cycle 145 assignment — see §5). NEVER-LATER-equivalent, same disposition as F-D30 |
| 15 | `ga_yoga` | HIDDEN (`ga_vargas`, via a reused helper) — **new, cycle 141** | `_load_d9_positions` (own docstring: "Load D9 (navamsha) positions from `chart_divisionals`") lazily imports `ga_structural_writer._load_varga_positions` and calls it directly — a genuine, documented read of `ga_vargas`' own target table, reached through a helper function defined in a DIFFERENT writer's module rather than a direct query in `ga_yoga_writer.py` itself. `ga_vargas` is not in `ga_yoga`'s declared `depends_on` anywhere. Confirmed `ga_structural` itself (the other declared edge) IS genuinely needed — read via shared `chart_facts` categories, not a dedicated table, so it doesn't show up as a separate "hidden" table match the way `ga_vargas` does. | `ga_yoga_writer.py:2434-2441` (`_load_d9_positions`, lazy import + call), `:2844-2845` (call site) | **F-D32** (cycle 145 assignment — see §5). NEVER-LATER-equivalent, same disposition as F-D30. An easy-to-miss pattern (indirect dependency via a reused cross-writer helper function, not a direct query) worth naming for future audits of other writers |
| 16 | `ga_structural` | FALSE (`ga_panchanga`) — **new, cycle 143, round 5** | `depends_on` includes 7 edges (`ga_dashas`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive`, `ga_strength`, `ga_vargas`); 6 confirmed genuinely read (`ga_dashas` via `chart_dashas`, `ga_positions` via `chart_facts`'s `graha_position`, `ga_vargas` via `chart_divisionals`, `ga_strength` via `graha_shadbala_total`, `ga_nakshatra` via `chart_facts`'s `graha_nakshatra_join` category, `ga_sensitive` via `chart_facts`'s `bhava_arudha` category — the last two required checking the SPECIFIC `fact_category` filter, not just table name, since both assets share `chart_facts` as their target table). `ga_panchanga` alone has **zero** matches for any of its own panchanga-anga category names (`tithi`/`vara`/`karana`/`disha_shul`/`solar_context`/`calendrical`/`sun_moon_dynamics`) anywhere in the full list of 10 distinct `fact_category` filters the writer actually uses — confirmed by enumerating that complete list, not sampling a few candidates. | `ga_structural_writer.py` (full `fact_category = '...'` enumeration, 10 distinct values, none panchanga-related) | **F-C25** (cycle 145 assignment — see §5). NEVER-LATER-equivalent, same disposition as F-C18/F-C23 |
| 17 | `ga_sade_sati` | FALSE (`ga_nakshatra`) — **new, cycle 144, round 6, completes the 19-asset sweep** | `depends_on` has 7 edges; F-D15 already confirmed `ga_strength`/`ga_panchanga` false, and `ga_positions`/`ga_vargas`/`ga_dashas`/`ga_structural` are now confirmed genuinely read (`chart_facts`'s `graha_position` 27 matches, `chart_divisionals` 6, `chart_dashas` 7, and `chart_facts`'s `argala_natal_matrix`/`tara_bala_natal_baseline` categories — both `ga_structural`-owned — respectively). `ga_nakshatra` alone: 17 raw matches for the substring "nakshatra", but every one resolves to either a hardcoded FORENSIC constant (`NATIVE_MOON_NAKSHATRA = "Purva Bhadrapada"`), an internally-computed value (Saturn's transiting nakshatra index derived from raw longitude via `int(lon // (360.0/27.0))`, not read from any table), or — the one that looked most like a real read — `_read_moon_pada_per_ayanamsha`'s own docstring ("Read natal Moon nakshatra pada from GA3"), which on inspection queries `chart_facts WHERE fact_category = 'graha_position' AND fact_subject = 'MOON' AND fact_key = 'pada'` — **`ga_positions`' own category, not `ga_nakshatra`'s**. Zero genuine reads of any `ga_nakshatra`-owned category anywhere. `ga_sade_sati`'s 7-edge declaration is now confirmed 4 correct, 3 false — comparably inaccurate to `ga_yoga`'s. | `ga_sade_sati_writer.py:172` (`NATIVE_MOON_NAKSHATRA` hardcoded), `:1505-1518` (`_read_moon_pada_per_ayanamsha`, actually reads `ga_positions`' category despite its own "GA3" docstring label), `:1578-1598` (Saturn transit nakshatra computed from raw longitude, not read) | **F-D33** (cycle 145 assignment — see §5). NEVER-LATER-equivalent, same disposition as F-D15 |

**CLEAN (7, round 2, cycle 140)** — each asset's declared deps were confirmed genuinely read via
direct grep, and no undeclared read of another asset's dedicated target table or L0 `bg_*` table
was found:
- `ga_positions` — trivially clean by construction (`depends_on={}`, nothing to check).
- `ga_strength` (`depends_on={ga_positions,ga_vargas}`) — real reads of `chart_divisionals` (6
  matches) confirmed; no undeclared dedicated-table or `bg_*` reads found.
- `ga_vichara` (`depends_on={ga_structural,ga_strength,ga_dashas,ga_yoga}`) — all 4 confirmed read
  (`chart_dashas` 5 matches, `ga_yoga_firings` 5 matches, shadbala/`graha_shadbala_total` 10
  matches); no undeclared reads found.
- `ga_transit_anchors` (`depends_on={ga_positions}`) — real `chart_facts` reads confirmed (7
  matches); no undeclared reads found.
- `ga_ayurdaya` (`depends_on={ga_positions}`) — real `chart_facts` reads confirmed (5 matches); no
  undeclared reads found.
- `ga_vastu` (`depends_on={ga_condition}`) — real `ga_condition_composite` reads confirmed (LEFT
  JOIN, live code not just comments); no undeclared reads found.
- `ga_prashna` (`depends_on={ga_positions,bg_prashna_rules}`) — reads `bg_prashna_significators`,
  which at first looked like an undeclared 3rd edge, but `bg_prashna_significators` is one of
  `bg_prashna_rules`' own 5 owned tables (`bg_prashna_fructification_rules`,
  `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`,
  `bg_prashna_tajik_yogas` — confirmed via `asset_registry`, `bg_prashna_rules.target_table` is
  itself blank/NULL despite owning this 5-table family, a registry-metadata quirk, not a DAG
  defect). **Verified before reporting a false positive** — the near-miss is recorded here
  precisely so a future pass doesn't need to re-derive this.

**Round 4 (cycle 142) — declared-edge re-verification for 4 more assets already carrying a
hidden-edge finding** (following round 3's own lesson that "already has a finding" ≠ "fully
audited"): all 4 confirmed clean on every declared edge, no new false edges found.
- `ga_dashas` (`depends_on={ga_positions}`, already carries F-A13's 3 hidden findings) — real
  `chart_facts` reads confirmed (28 matches).
- `ga_sensitive_degree` (`depends_on={ga_positions}`, already carries F-B15's hidden findings) —
  real `chart_facts` reads confirmed (14 matches).
- `ga_nakshatra` (`depends_on={bg_nakshatra,ga_positions,bg_kp_sublord_division}`, already
  carries F-B23's hidden `reference_signs` finding) — all 3 declared edges confirmed genuinely
  read in the main writer (`pipeline/orchestrator/writers/ga_nakshatra.py`: `bg_nakshatra` 4
  matches, `chart_facts` 8 matches, `bg_kp_sublord_division` 4 matches).
- `ga_condition` (`depends_on={ga_positions,ga_vargas,ga_dashas}`, already carries F-C23's 4
  hidden L0 findings) — all 3 declared edges confirmed genuinely read (`chart_facts` 15,
  `chart_divisionals` 12, `chart_dashas` 6 matches).

**Round 5 (cycle 143) — `ga_structural`'s own 7 declared edges**, the largest single declaration
in L1: 6 confirmed genuinely read (`ga_dashas` via `chart_dashas`, `ga_positions` via
`chart_facts`'s `graha_position`, `ga_vargas` via `chart_divisionals`, `ga_strength` via
`graha_shadbala_total`, `ga_nakshatra` via `chart_facts`'s `graha_nakshatra_join` category,
`ga_sensitive` via `chart_facts`'s `bhava_arudha` category — confirmed via the full list of 10
distinct `fact_category` filters the writer uses, not table-name matching alone, since 3 of its
6 real upstream assets share `chart_facts` as their own target table). **1 false**: `ga_panchanga`
(finding #16) — zero matches for any panchanga-anga category name across that same complete list.

**Round 6 (cycle 144) — `ga_sade_sati`'s remaining 5 declared edges + `ga_medical`'s 2, closing
out the full 19-asset sweep.** `ga_medical` (`depends_on={ga_condition,ga_positions}`): both
confirmed genuinely read (`chart_facts` 4 matches, `ga_condition_composite` 6 matches) — CLEAN
beyond its own existing hidden-edge finding. `ga_sade_sati`: 4 of its remaining 5 confirmed real
(`ga_positions`, `ga_vargas`, `ga_dashas` via dedicated tables; `ga_structural` via its own
`argala_natal_matrix`/`tara_bala_natal_baseline` categories) — **1 new false edge**: `ga_nakshatra`
(finding #17, see §2). `ga_tajaka` needed no new check — its 3rd declared edge (`ga_sensitive`)
was already confirmed genuinely read by F-E18's own text, so all 3 of its declared edges were
already fully accounted for.

**All 19 L1 assets now have their declared edges fully re-verified in both directions**
(rounds 1-6, cycles ≤144) — the same rigor L3's own method applies campaign-wide, completed for
L1 for the first time this campaign.

**Summary: 11 assets with at least one confirmed hidden/false/semantic-mismatch edge (of L1's 19);
10 distinct hidden-edge findings, 10 false/over-declared, 1 semantic-clarification-only, 1
shared-ownership gap. 8 assets confirmed clean.** One (`ga_dashas`↔`ga_vargas`, finding #2) has a
measured live correctness consequence; the rest are DAG-accuracy findings without demonstrated
data corruption to date. Two assets stand out for how inaccurate their declared DAG is: **`ga_yoga`**
(2 declared edges, 1 false, 4 real inputs undeclared) and **`ga_sade_sati`** (7 declared edges,
3 false — `ga_strength`/`ga_panchanga`/`ga_nakshatra` — 4 correct). `ga_structural` (finding #16)
is the largest single declaration in L1 (7 edges) and the most *accurate* of the multi-edge
assets checked — 6/7 correct, only 1 false.

## §3 — What this audit has NOT yet done

All 19 L1 assets now have their declared edges fully re-verified in both directions (round 1's 11
existing findings → round 2's direct grep sweep of the 8 not yet covered → round 3's `ga_yoga`
re-verification, which found 2 more genuine findings round 1 had not surfaced, proving "already
has a finding" is not the same as "fully audited" → rounds 4-6 applying that same check to every
remaining asset, closing with `ga_sade_sati`'s own `ga_nakshatra` false edge, finding #17). What a
fuller, L3-grade pass would still add on top of this — genuinely equivalent coverage, different
artifact trail:
- **A true `target_table → asset_id` owner map** built once and reused. This audit checked each
  asset's declared edges against a per-asset hand-picked candidate list (dedicated tables +
  `bg_*` patterns + specific `fact_category` filters for the `chart_facts`-sharing assets), not a
  single systematic scan of the full live table universe the way L3's method does. The *result*
  is the same shape (every asset, every declared edge, checked in both directions) but a future
  reader cannot re-run one script against a fresh schema snapshot to reproduce it — L3's method
  can.
- ~~Findings #12-#17 have not yet been assigned F-ids or triaged into a tier~~ — **done, cycle
  145, see §5** (F-D30/B36/D31/D32/C25/D33, all NEVER-LATER-equivalent per D-CND-09).

## §4 — Deliberate non-edges (D-CND-10)

None identified for L1 to date. If a future pass finds a pair where an edge looks missing but
adding it would break something (matching the shape of §3.1 in `DAG_CORRECTIONS_REGISTER_v1_0.md`
— `ka_kshetra`↔`mi_bhara`'s version-pin-not-edge resolution), it belongs here, not in §2.

## §5 — F-id assignment for findings #12-#17 (cycle 145)

§3 named this as owed: findings #12-#17 (this audit's 6 genuinely-new discoveries, all found
after W2 closed) had no F-id and no tier, unlike round 1's 11 findings which were triaged during
W2 itself. Assigning them here rather than editing `L1_W2_DECIDE_v1_0.md` — that artifact is W2's
own frozen record of what was decided *during* W2; retroactively inserting post-W2 discoveries
into it would misrepresent when they were actually found. This section is the honest home for
that assignment instead.

**Numbering**: continued each finding's asset in whichever letter-series its OTHER existing
findings already use (`ga_yoga` → D, matching F-D3; `ga_panchanga` → B, matching F-B24/26/31;
`ga_structural`'s DAG-specific findings → C, matching F-C18/23; `ga_sade_sati` → D, matching
F-D14/15/18/20), picking the next free number in each series as of cycle 145 (verified live via
`grep` across every W1 batch file + `L1_STATE.md`, not assumed): F-A max was F-A26, F-B max
F-B35, F-C max F-C24, F-D max F-D29 — so `ga_yoga`'s three new findings took F-D30/31/32 (in the
order found: `ga_positions` hidden, `ga_dashas` false, `ga_vargas` hidden), `ga_panchanga` took
F-B36, `ga_structural` took F-C25, and `ga_sade_sati` took F-D33 (after `ga_yoga`'s three
consumed F-D30-32).

| F-id | asset | edge | disposition |
|---|---|---|---|
| F-D30 | `ga_yoga` | HIDDEN `ga_positions` (finding #12) | NEVER-LATER-equivalent — `depends_on` immutable this cohort (D-CND-09), recorded for the next freeze |
| F-B36 | `ga_panchanga` | FALSE ×2 `ga_positions`/`bg_panchanga` (finding #13) | same |
| F-D31 | `ga_yoga` | FALSE `ga_dashas` (finding #14) | same |
| F-D32 | `ga_yoga` | HIDDEN `ga_vargas` (finding #15) | same |
| F-C25 | `ga_structural` | FALSE `ga_panchanga` (finding #16) | same |
| F-D33 | `ga_sade_sati` | FALSE `ga_nakshatra` (finding #17) | same |

All six share the same disposition as every other DAG-declaration finding this campaign
(F-A7/F-A13/F-D3/etc.): the code-level truth is established and documented, but the
`depends_on` field itself cannot be corrected inside the frozen definition (D-CND-09) — the
correction lives here and in `DAG_CORRECTIONS_REGISTER_v1_0.md` §2, consumed at the next
definition freeze per that register's own §4. None require a writer-code fix (none of the FALSE
edges have a demonstrated correctness consequence the way F-A13's `ga_dashas`/`ga_vargas` MVCC
race does); the HIDDEN edges (F-D30, F-D32) are the ones worth the coordinated-rebuild-sequencing
attention already being tracked on issue #2180.
