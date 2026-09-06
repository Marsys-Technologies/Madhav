---
artifact: L1_DEPENDS_ON_AUDIT_v1_0.md
canonical_id: NIRMANA_L1_DEPENDS_ON_AUDIT
version: "0.4"
status: IN PROGRESS — 15 confirmed findings + 7 assets confirmed CLEAN via a direct grep sweep
  (round 2); 1 asset (ga_positions) trivially clean by construction (zero declared deps). All 19
  L1 assets now have at least one pass of coverage; ga_yoga's own declared edges (round 3, cycle
  141) and 4 more assets' declared edges (round 4, cycle 142) fully re-verified in both
  directions, all clean beyond their existing findings. See §3 for what a fuller L3-style sweep
  would still add — 4 assets (`ga_structural`, `ga_sade_sati`, `ga_medical`, `ga_tajaka`) remain
  to be re-verified this way.
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

## §2 — Confirmed findings (15) + CLEAN assets (8)

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
| 13 | `ga_panchanga` | FALSE ×2 (`ga_positions`, `bg_panchanga`) — **new, cycle 140, round-2 sweep** | Writer issues **zero** SQL `SELECT`/`execute` calls of any kind (confirmed: 0 matches for `select`/`cur.execute`/`cursor.execute` in the whole 64KB file) — it derives every panchanga element from `resolve_birth_params` (ephemeris recomputation), the same "recomputes independently instead of reading" pattern as `ga_vargas`' own F-A7. **`bg_panchanga` does not even exist as a table** (`\dt bg_panchanga*` returns nothing live) — a dead reference, not merely unread. | `ga_panchanga_writer.py` (whole-file grep, 0 execute calls); `resolve_birth_params` import at `:37`; live `\dt` check | Open — feeds this register; new finding, not yet triaged into a tier |
| 14 | `ga_yoga` | FALSE (`ga_dashas`) — **new, cycle 141, verifying finding #8/#12's remaining declared edges** | `depends_on={ga_structural,ga_dashas}` declares `ga_dashas`, but the writer contains **zero** matches for `chart_dashas` (`ga_dashas`' own target table) or even the substring "dasha" anywhere in the file, in code or comments. Combined with findings #8/#12 (2 hidden + 1 hidden, none of them `ga_dashas`), `ga_yoga`'s declared 2-edge DAG is now confirmed wrong on BOTH members: `ga_dashas` false, `ga_structural` confirmed genuinely needed (below). | `ga_yoga_writer.py` (whole-file grep: 0 matches for `chart_dashas` and for "dasha" case-insensitive) | Open — feeds this register; new finding |
| 15 | `ga_yoga` | HIDDEN (`ga_vargas`, via a reused helper) — **new, cycle 141** | `_load_d9_positions` (own docstring: "Load D9 (navamsha) positions from `chart_divisionals`") lazily imports `ga_structural_writer._load_varga_positions` and calls it directly — a genuine, documented read of `ga_vargas`' own target table, reached through a helper function defined in a DIFFERENT writer's module rather than a direct query in `ga_yoga_writer.py` itself. `ga_vargas` is not in `ga_yoga`'s declared `depends_on` anywhere. Confirmed `ga_structural` itself (the other declared edge) IS genuinely needed — read via shared `chart_facts` categories, not a dedicated table, so it doesn't show up as a separate "hidden" table match the way `ga_vargas` does. | `ga_yoga_writer.py:2434-2441` (`_load_d9_positions`, lazy import + call), `:2844-2845` (call site) | Open — feeds this register; new finding, an easy-to-miss pattern (indirect dependency via a reused cross-writer helper function, not a direct query) worth naming for future audits of other writers |

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

**Still not re-verified in both directions** (declared-edge validity, beyond their own already-
known hidden/false findings): `ga_structural` (7 declared edges — the largest), `ga_sade_sati`
(2 of 7 already confirmed false via F-D15, 5 remain), `ga_medical` (2 declared edges, not yet
checked beyond its own hidden-edge finding), `ga_tajaka` (1 of 3 already confirmed genuinely read
via F-E18's own text, `ga_sensitive`; 2 already confirmed false). `ga_vargas` and `ga_sensitive`
need no further declared-edge check — F-A7 and F-B11 already cover their single declared edge
each exhaustively.

**Summary: 9 assets with at least one confirmed hidden/false/semantic-mismatch edge (of L1's 19);
10 distinct hidden-edge findings, 8 false/over-declared, 1 semantic-clarification-only, 1
shared-ownership gap. 8 assets confirmed clean** (7 via direct grep + `ga_positions` trivially).
One (`ga_dashas`↔`ga_vargas`, finding #2) has a measured live correctness consequence; the rest
are DAG-accuracy findings without demonstrated data corruption to date. **`ga_yoga` is now the
single worst-audited asset in this exercise**: of its 2 declared edges, 1 is false (`ga_dashas`,
finding #14) and the other is genuinely correct (`ga_structural`); of its real inputs, 4 are
undeclared (`ga_strength`, `ga_sensitive` — finding #8; `ga_positions` — finding #12; `ga_vargas`
— finding #15) — a 2-edge declaration understating reality by 4 real hidden reads while also
getting one of its 2 declared edges wrong.

## §3 — What this audit has NOT yet done

All 19 L1 assets now have at least one pass of coverage (round 1's 11 existing findings + round
2's direct grep sweep of the remaining 8 + round 3's full both-directions verification of
`ga_yoga`'s own declared edges, which found 2 more genuine findings round 1 had not surfaced —
proof that "already has a finding" is not the same as "fully audited," the same lesson L3's own
method embeds by checking every asset regardless of prior findings). Round 4 (cycle 142) applied
the same both-directions check to 4 more assets (`ga_dashas`, `ga_sensitive_degree`,
`ga_nakshatra`, `ga_condition`) — all confirmed clean beyond their existing findings, no new
edges found this time. `ga_vargas` and `ga_sensitive` need no further check (F-A7/F-B11 already
cover their single declared edge each exhaustively). What a fuller, L3-grade systematic pass
would still add, not yet done here:
- **The same both-directions re-verification, still owed to 4 assets**: `ga_structural` (7
  declared edges — the largest declaration in L1), `ga_sade_sati` (5 of 7 declared edges not yet
  re-checked beyond F-D15's 2 confirmed false), `ga_medical` (2 declared edges, not yet checked
  beyond its own hidden-edge finding), `ga_tajaka` (its 3rd declared edge, `ga_sensitive`, already
  confirmed genuinely read via F-E18's own text — only the 2 already-false ones are settled).
- **A true `target_table → asset_id` owner map** built once and reused (rounds 2/3 checked
  against a hand-picked list of dedicated tables + `bg_*` patterns per asset, not the full live
  table universe L3's method scans).
- **Findings #12/#13/#14/#15 have not yet been assigned F-ids** or triaged into a tier (MUST/NOW/
  NEVER-LATER) the way round 1's 11 findings already were during W2 — all four are genuinely new
  (found after W2 closed) and open.

## §4 — Deliberate non-edges (D-CND-10)

None identified for L1 to date. If a future pass finds a pair where an edge looks missing but
adding it would break something (matching the shape of §3.1 in `DAG_CORRECTIONS_REGISTER_v1_0.md`
— `ka_kshetra`↔`mi_bhara`'s version-pin-not-edge resolution), it belongs here, not in §2.
