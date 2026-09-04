---
artifact: L3_STATE.md
canonical_id: NIRMANA_V21_L3_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L3
layer: L3 — Kāla
owner: the L3 session (this file is yours alone — charter C5)
last_updated: 2026-09-05T00:00Z — L3 session bootstrapped, W1 opened
---

# L3 — Kāla — SESSION STATE

Stub created by the CONDUCTOR so this session has a file to rebase onto. **Everything below is
yours to overwrite.** Charter C9: this file is your memory — update it every loop, commit it with
every PR and at every milestone, so re-pasting your prompt into a fresh session is safe at any
moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → this file → `git fetch origin main` →
your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 (run-slot claims, freeze-ordering acks, monster scheduling)
- **Adjudication:** open a new issue labeled `nirmana-adjudication`, then keep working (C3)
- **Migration range:** 670–679 (yours alone, collision-free by construction)
- **Branch namespace:** `codex/nirmana-l3-*` · **PR title prefix:** `L3:`
- **Worktree:** `~/nirmana-s/l3`
- **Standing ruling D-CND-01 (read before your first Conform-stage check):** a `count(*) = N` is
  permitted only as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table
  FULL-JOIN consistency, NULL/range guards). Alone it is forbidden (C12). `expected_volume_formula`
  is REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + the L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
- **Freeze predecessor:** L2 Bodha must be frozen before your W6 ceremony (C2; asset work is never held)

## Position

`L3-W3` — W1 COMPLETE (23/23) · W2 COMPLETE (23/23 routed) · **W3 IN FLIGHT**.

### W3 progress

**Landed on `codex/nirmana-l3-w3-serving-honesty` (PR #1751), each with mutation-proved tests:**

| finding | what | verification |
|---|---|---|
| **M7** | the honest-empty that pagination was faking — currency filter pushed into SQL ahead of the row cap on all three horizon capabilities; explicit `truncated`; `now.ts` reports truncation as a distinct cause | 12 tests; reverting the filter + flag turns 2 red |
| **M8** | the field that was never empty — a hardcoded "ka_kshetra has written no rows" over 31,350 live rows; corrected to the true blocker (**no registry capability exists over any `kala_field*` table at all**) | 3 tests; one pre-existing assertion that pinned the false claim retargeted, not weakened |
| **M11** | `service_health` written and read by nothing; `ka_graha_sancara` computed a verdict into a variable and discarded it, so it was `state='lit'` while `unhealthy`. Three writers now raise | 7 tests incl. a shape guard; removing one raise turns its test red |
| **M4** | `ka_avadhi`'s `lord_condition_fact_refs` `[]` on **100.00%** of rows — three independent L1 mismatches (Title-case vs `JUP`/`RAH_MEAN`, no `fact_category` pin, 5 of 7 `fact_key`s nonexistent). Fixed through the L0 SSoT `norm_graha`, not a local map | 12 tests; 8 refs per lord live, up from 0 |
| **M9** | `conv_score or 0.5` — falsy-coalescing rewrote **793 computed zeros** into a favourable neutral; measured 0 NULLs, so the default only ever mangled real data | 3 tests; restoring `or 0.5` turns 2 red |

Full `python-sidecar` suite after these: **6,135 passed, 0 failures.** `platform` + `platform-mcp`
`tsc`: 0 errors. `L3_kala` 107 passed; `kala_views` + `kala_ritual_resonance` 214 passed.

**In flight:** 19 D-CND-03 integrity contracts (14 authored + mutation-proved so far, by three
subagents; 3 authored by me including the **v1-corpus guard**, which is now the only in-database
detector of loss for that irreplaceable corpus since migration 588 removed its triggers) ·
the full both-directions `depends_on` audit that D-CND-07 now requires.

**Not started:** M5 (century `BIRTH_YEAR=1984`), M6 (`ka_gochara` count_sql), M12 (54 orphan
`era_slice_key` rows), M3 (`ka_graha_sancara`'s two defects), M10, migration 670, N1 (the Temporal
Concordance Contract), N2–N12.
**Bootstrap facts established live (not assumed):**
- Worktree `~/nirmana-s/l3` created from `origin/main` = `20323fae4`. Branch `codex/nirmana-l3-w1-analysis`.
- `NIRMANA_HOLD` absent at the shared checkout root — standing authorization confirmed (C3).
- DB read path live via the already-running Cloud SQL proxy (`127.0.0.1:5433`, `amjis_app`).
- Frozen definition `t0-2026-09-01-0e5b06fb` carries **23/23** L3 assets; live `asset_registry`
  also has exactly 23 `ka_*` rows. No manifest/registry count drift at L3.
- L3 wave_index distribution in the frozen manifest: W0=10 · W1=5 · W2=1 · W3=3 · W4=1 · W5=3.
- Charter C10 batch gate run live: **`ka_gochara_resonance` and `ka_graha_sancara` are the only
  two L3 assets with 0 unfrozen ancestors today** — exactly as the session prompt predicted.
  Everything else is gated behind L0/L1/L2 freezes (`ga_positions` alone unblocks 5 more).

## Asset table (23 assets)

Frozen definition `t0-2026-09-01-0e5b06fb`. `E-gate` = live C10 result at the timestamp below
(unfrozen-ancestor count; 0 = OPEN). Routes fill in at W2.

| asset_id | kind | obl. | wave | route | status | E-gate | capsule | notes |
|---|---|---|---|---|---|---|---|---|
| ka_gochara_resonance | data | build | 0 | **rebuild_only** | W2-done | **0 — OPEN** | — | **canary candidate**; fingerprint clean |
| ka_graha_sancara | service | probe | 0 | **probe** | W2-done | **0 — OPEN** | — | **canary candidate**; but `service_health='unhealthy'` — see F-L3-3 |
| ka_kota_chakra | data | build | 0 | **rebuild_only** | W2-done | 1 (ga_positions) | — | quality overlay |
| ka_moorti_nirnaya | data | build | 0 | **rebuild_only** | W2-done | 1 (ga_positions) | — | quality overlay |
| ka_sudarshana_varsha | data | build | 0 | **rebuild_only** | W2-done | 1 (ga_positions) | — | quality overlay |
| ka_tithi_pravesha | data | build | 0 | **verified_reuse** | W2-done | 1 (ga_positions) | — | quality overlay; L4 consumer (D-7) |
| ka_vedha_gochara | data | build | 0 | **rebuild_only** | W2-done | 1 (ga_positions) | — | quality overlay; dep `bg_sarvatobhadra_grid` is empty-by-ruling |
| ka_muhurta_seva | service | probe | 1 | **probe** | W2-done | 1 (ka_graha_sancara) | — | opens the moment the canary freezes |
| ka_gochara_sweep | data | retired_with_disposition | 1 | **retired** | W2-done | 1 (ka_gochara_resonance) | — | **v1 archive — HARD-FLOOR PROTECTED** |
| ka_dasha_kala | service | probe | 0 | **probe** | W2-done | 2 | — | |
| ka_gochara | data | build | 1 | **changed** | W2-done | 2 | — | v2/v3 authority question |
| ka_gochara_v3_century_materialize | data | build | 1 | **changed** | W2-done | 6 | — | **MONSTER — solo slot** |
| ka_avadhi | data | build | 0 | **changed** | W2-done | 20 | — | |
| ka_yojaka | data | build | 0 | **changed** | W2-done | 20 | — | |
| ka_kshetra | data | build | 1 | **changed** | W2-done | 25 | — | **MONSTER — solo slot**; 11.0M rows / 5.0 GB |
| ka_sangam | artifact | build | 2 | **changed** | W2-done | 28 | — | arbiter's likely home |
| ka_kalasutra | artifact | build | 3 | **rebuild_only** | W2-done | 29 | — | 671K rows vs 33s estimate — check |
| ka_vighnakara | artifact | build | 3 | **changed** | W2-done | 29 | — | |
| ka_taranga | data | build | 3 | **changed** | W2-done | 30 | — | **derived-view vs witness decision owed** |
| ka_kala_darshana | artifact | build | 4 | **changed** | W2-done | 31 | — | |
| ka_bhavishya_lekha | artifact | build | 5 | **changed** | W2-done | 32 | — | |
| ka_jivana_parva | artifact | build | 5 | **changed** | W2-done | 32 | — | |
| ka_tulana | service | probe | 5 | **probe** | W2-done | 32 | — | |

E-gate snapshot taken 2026-09-05 at W1 open. Re-run the C10 batch query every loop (C8.6) —
`ga_positions` alone unblocks 5 assets, and `ka_gochara_resonance` freezing unblocks 2 more.

## Decisions log

- **D-L3-1 (2026-09-05)** — Bootstrapped from `origin/main` `20323fae4` rather than waiting for the
  Conductor's governance PR (#1714) to merge. Charter §preamble authorises reading the charter from
  the shared checkout until it lands. I copied the Conductor's `L3_STATE.md` stub verbatim as my
  base so the eventual rebase is a clean fast-forward, not a conflicting parallel authorship.
- **D-L3-2 (2026-09-05)** — Did **not** unilaterally fix the registry-fingerprint ordering defect
  (finding F-L3-1) even though a migration in my own 670–679 range would unblock my 15 assets. The
  correct fix is in `dispatch_nirmana_campaign_wave.py`, which C5 makes Conductor-owned shared
  tooling. Filed adjudication **#1721** with both options costed and continued. Evidence: my two
  E-gate-open assets are unaffected, so this costs L3 zero wall-clock.
- **D-L3-3 (2026-09-05)** — On finding F-L3-2 (integrity detector runs unparameterised) I
  explicitly declined to propose the available tool fix (bind the chart id, letting `count_sql`
  serve as the detector). It would let 81 assets across five layers freeze on a `positive_count`
  verdict — "this table has >0 rows" — which is a gate weakening under the hard floor and exactly
  the un-earned green signal C12/§N.8 forbid. Recommended instead that every per-chart layer author
  real invariants in its own W3, which C12 already requires. Filed as cross-layer **#1724**.
- **D-L3-4 (2026-09-05)** — Accepted the build job's image `7f6ab3add` as execution-safe for L3 W4
  dispatch despite being 4 commits behind `main`, on measured ancestry evidence rather than on the
  version number: `git diff 7f6ab3add..origin/main -- platform/python-sidecar/` is **empty**. The
  intervening commits are docs plus `definitions.ts` (which runs in the web service, already at
  main). Writer code in the image is byte-identical to main. Re-check before every dispatch (C4).

## Held items

| item | blocked on | since | note |
|---|---|---|---|
| **W4 for ALL 23 assets** | **#1730** (dispatcher enforces strict layer sequencing) | 2026-09-05 | the hard blocker: no layer session can dispatch anything |
| **The gate canary itself** | **#1734** (E-gate soundness / DAG truth) | 2026-09-05 | L3 has no honest canary until the DAG is reconciled and superseded |
| W2 acceptance events (all 23) | **#1715** (evidence spine generalisation, RULED — L1 authors) | 2026-09-05 | W2 *decisions* are unaffected and proceed |
| W4 for 15 of 23 assets | **PR #1728** (fingerprint ordering, RULED, auto-merge armed) | 2026-09-05 | resolves on merge; record the SORTED fingerprint |
| Salience temporal-multiplier wiring (D-TIME → D-SALIENCE) | L2 consensus/salience capabilities (C6) | 2026-09-05 | poll `L2_STATE.md` §CAPABILITIES LANDED on `origin/main` |
| 18 of 23 assets' W4 | L0/L1/L2 freezes (E-gate, C2) | 2026-09-05 | `ga_positions` is the single highest-leverage unlock (5 assets) |

## Rulings received (binding — Conductor, ADHIKĀRIN precedent)

- **#1721 → GRANTED (my filing).** Registry-fingerprint ordering: the code is the deviation, the
  data is not. **L0's data-normalisation remedy is explicitly NOT extended to L1–L5 — no layer
  session may normalise `asset_registry.depends_on` to route around it.** The L0 session's unopened
  fix (`4381eb66b`) was opened as **PR #1728** with auto-merge armed, plus a mutation-proof
  regression test the original fix lacked. **Binding on me: record the SORTED fingerprint** in
  analysis receipts — the value the TS authority, the frozen manifest and (post-#1728) the
  dispatcher all agree on. Re-verify deploy ancestry (C4) before the first dispatch that depends
  on it. My 15 deadlocked assets unblock when #1728 lands.
- **#1723 / #1727 → GRANTED as D-CND-03** (my #1724 was the same finding; I withdrew it as a
  duplicate and recorded L3's acceptance there). Binding standard for every integrity contract:
  **prefer chart-partitioned invariants** — `NOT EXISTS (SELECT 1 FROM <t> GROUP BY chart_id
  HAVING <violation>)` — over whole-table aggregates, because a corruption confined to one chart
  can be numerically swamped in a whole-table aggregate and missed. A non-partitionable aggregate
  is permitted only with a SQL comment naming why. **D-CND-01**: `expected_volume_formula` +
  `expected_volume_inputs` are REQUIRED where a count equality is the volume assertion.
  **L3 owns 19 contracts** (23 assets − 4 services, which take the health-probe path). The
  ruling's L3 count matches my independent measurement exactly.
- **#1715 → GRANTED, Option A.** The evidence spine is generalised from L0-only to all layers;
  **L1 authors, Conductor merges**; L4's #1718 folded in (`writer_digest_sha256` carried in the
  `asset_analysis_accepted` payload and compared layer-agnostically). **Binding on me: no W2
  acceptance event may be written until that PR is merged and deployed** — otherwise the payload
  shape changes under us and analyses must be re-accepted. W1 and W2 *decisions* are unaffected
  and continue (C8).
- **#1730 (mine) / #1725 (L4)** — dispatcher strict-layer sequencing vs C2's asset frontier:
  **still open. This is L3's remaining W4 blocker.**

## STANDING CONSTRAINTS — read these before touching any registry row or dispatching anything

1. **`depends_on` is IMMUTABLE for the rest of the campaign** (#1744, L1, verified live: the frozen
   definition has 174 events / 11 build runs and `supersedeNirmanaElevationDefinition` refuses once
   either is non-zero; `acceptNirmanaBaselineCandidate` closes the side door). **My M1 supersession
   plan is withdrawn.** Everything else in the registry contract IS mutable —
   `integrity_check_sql`, `count_sql`, `catalog_status`, `target_floor`,
   `expected_volume_formula/_inputs` — so **D-CND-03 work is not blocked**; it must simply land
   BEFORE that asset's W2 acceptance event, or the accepted analysis needs re-accepting (C2.3).
2. **L3's self-imposed true gate.** For any asset whose real ancestor closure exceeds its declared
   one, L3 waits for the REAL ancestors, not the declared ones. Binding case:
   **`ka_gochara_resonance` is mechanically dispatchable after PR #1737 (1 declared ancestor, 0
   unfrozen) and will NOT be dispatched** until `ga_sensitive_degree`, `ga_yoga`, `ga_dashas` (L1)
   and `bo_arudha` (L2) are frozen. Building it early yields a silently thinner resonance map, and
   it is the root of the whole gochara family. Strictly stricter than the tool's gate, so it needs
   no permission. Cost: zero — nothing in L3's W3 depends on it.
3. **`ka_kshetra` ↔ `mi_bhara` is a VERSION PIN, NEVER A DAG EDGE, in either direction** (#1743, L5,
   acked by me). Adding the "obvious missing" edge breaks `assert_no_weights_cycle`
   (`services/mi_bhara/weights.py:263`) and makes `topoSort` reject **every future plan containing
   either asset** — not just this campaign's. My own mechanical reconciliation output listed
   `mi_bhara` under `ka_kshetra`'s undeclared reads, so this trap already fired once in L3's tooling
   and was caught only by the rule "never act on an automated dependency inference without reading
   the writer". **Fenced files — I do not edit without L5's ack on #1743:**
   `platform/migrations/491_kala_field_weights_seed.sql`,
   `services/ka_kshetra/stage4_field.py` (the pin read at :1099),
   `services/mi_bhara/weights.py`, `services/mi_bhara/db.py`.
   **Ownership declared:** `kala_field_weight_versions` + `kala_field_weights` are **L3-owned,
   L5-read-only** for this campaign.
4. **SNAPSHOT RULE ABSOLUTE** — no dispatch that could write `kala_gochara_windows` without a fresh
   verified snapshot; `ka_gochara_sweep` is never dispatched (its `@register` was removed at
   retirement — the rows cannot be regenerated).

## Findings ledger (W1 — running; batch analyses fold in as they land)

- **F-L3-1 (MUST, campaign-blocking, filed #1721)** — Registry-fingerprint ordering deadlock. The
  TS authority sorts `depends_on` (`definitions.ts:135`); the Python dispatcher does not
  (`dispatch_nirmana_campaign_wave.py:246`), though the same file *does* sort when comparing
  dependency sets (line 518). For an asset whose live `depends_on` is not already alphabetical,
  **no single fingerprint value satisfies both**: the sorted value makes the dispatcher refuse to
  dispatch (line 325 skips the receipt, then raises); the unsorted value makes `snapshot.ts:854`
  report permanent contract drift. Same defect class L0 hit on `bg_yogas`; L0 fixed the *data* for
  5 assets and left the *code* defect armed. Measured live over all 23 L3 assets:
  **sorted fingerprint == frozen manifest for 23/23** (so L3 has zero real contract drift — the
  divergence is purely array order), live/unsorted matches for only 8/23. The 15 affected are
  listed in #1721. Both canary candidates are in the clean 8.
- **F-L3-2 (MUST, cross-layer, filed #1724)** — `integrity_verified` is mandatory on every route
  (all 30 frozen L0 assets show it), and its detector executes registry SQL **with no bind
  parameters** (`definitions.ts:1594`). Every per-chart layer's `count_sql` is `$1`-bound, so the
  `integrity_check_sql ?? count_sql` fallback cannot fire for L1–L5 at all. Measured: L0 has 0
  parameterised `count_sql` and 37 integrity contracts; L1/L2/L3/L4/L5 have 19/22/19/9/12
  parameterised and **0/0/0/0/0** contracts. Consequence for L3: **19 real integrity contracts must
  be authored in W3** (the 4 services take the health-probe path instead and are unaffected).
  Declined the tool-side shortcut — see D-L3-3.
- **F-L3-3 (MUST — DIAGNOSED, batch C).** `ka_graha_sancara` is **genuinely broken**, not stale
  state. Two independent real defects: (1) `services/ka_graha_sancara/engine.py::_read_from_bg_ephemeris()`
  indexes rows positionally (`row[0]`…) while the orchestrator connection is `row_factory=dict_row`
  (`pipeline/orchestrator/db.py:57`) → `KeyError: 0`, which is literally what `selftest_detail`
  records (`"ephemeris computation failed: 0"` = `str(KeyError(0))`). Corroborated in-repo:
  `brahmagyan/phala/muhurta.py`'s docstring says it deliberately opens a tuple-row connection
  because that helper indexes positionally — a different author hit this and worked around it
  instead of fixing it. (2) Surviving the first fix: self-test check 4 asserts natal Moon =
  Aquarius, but PATH-A reads `ephemeris_daily`, computed at **12:00 UT**, which for a 10:43 birth
  gives sidereal Moon 330.41° = **Pisces** against L1's 327.06° Aquarius — the 6.8-hour
  birth-to-noon gap. **This check has never been green in the real path**; the 19/19 green tests
  pass because they feed a tuple-returning mock. Textbook C12: a check that has never been green is
  a proposal, not a gate. **Route `changed`, not `probe`. Not usable as the canary.**
- **F-L3-10 (MUST, filed #1734) — the E-gate is only as sound as `depends_on`, and L3's DAG is
  wrong in both directions.** I verified this from the writer SQL myself rather than inherit it.
  `ka_gochara_resonance` declares `{bg_transit_rules}` and actually reads six tables
  (`writer.py` lines 369/375/382/389/396/412): `brahma_event_ontology` (`bg_ghatana`, L0, frozen),
  `bg_transit_rules` (declared), `chart_facts` ×2 (L1, **unfrozen**), `ga_yoga_firings` (`ga_yoga`,
  L1, **unfrozen**), `chart_dashas` (`ga_dashas`, L1, **unfrozen**). **Five undeclared edges, four
  into unfrozen L1.** The failure mode is silent: a rebuild ordered by this DAG can run the
  resonance map before `ga_yoga`/`ga_dashas` and produce a thinner map with no error and no flag.
  The mirror defect also exists — **fictional** edges holding true gates shut: `ka_muhurta_seva`
  declares `{ka_graha_sancara}` while its own package docstring says *"Depends on: ka_graha_sancara
  (planned)"* (read directly) and its real read is the panchāṅga engine (`bg_panchanga`, **frozen**);
  `ka_gochara_v3_century_materialize` has 4 dead declared edges; `ka_tulana` all 3 unread;
  `ka_yojaka`'s `bg_transit_rules` unread; and `ka_kshetra`'s stack contains an undeclared
  **backward L3→L4 read** of `phala_rectification` (`uncertainty.py:191`) — a layer inversion.
  **Consequence, stated plainly: L3 has ZERO genuinely E-gate-open assets today.** Both assets the
  session prompt nominated as canaries are artefacts — one of a missing edge, one of a broken
  service. I filed this rather than run a canary through a gate I had just proved measures nothing.
- **F-L3-4 (NOW)** — All 23 L3 assets have `expected_volume_formula` NULL and
  `expected_volume_inputs` NULL; 0 have a non-zero `target_floor`. C12 names the NULL itself the
  defect. Volume expectations must be DERIVED or set as achieved-count floors (§N.4) in W3.
- **F-L3-5 (NOW)** — **11 L3 assets are `catalog_status='DRAFT'`: 7 artifact + 4 service** (measured
  2026-09-05; corrects an earlier note here that said "6 artifact-kind", which was Batch E's subset
  mistaken for the layer's total). Matches L2's independent campaign-wide count on **#1753**, which
  finds L3, L4 and L5 DRAFT in their entirety while `CLAUDE.md` §E records all three as
  CLOSED/SEALED, and traces the mechanism to `asset_registry.catalog_status DEFAULT 'DRAFT'` plus
  24 migrations that omit the column. The cockpit filters on it (migration 294's own root-cause
  note). **L3's decision: flip 10, hold `ka_graha_sancara` at DRAFT until M3 lands** — promoting a
  service that is genuinely broken would be precisely the unearned signal §N.8 forbids.
- **F-L3-6 (MUST, filed #1730, OPEN)** — The shared dispatcher enforces pre-v2.1 strict layer/wave
  sequencing (`campaign_prerequisite_asset_ids`, hard `raise` at line 770), not C2's asset frontier.
  An L3 wave-0 dispatch demands **all 81 L0+L1+L2 assets frozen (52 unfrozen)**, while
  `ka_gochara_resonance`'s true transitive closure is **one asset, already frozen**. Two further
  conflicts in the same neighbourhood: a campaign-wide **single**-active-run lock (line 797) against
  C5's ≤3, and a one-shot-per-wave guard (line 806) upstream of C8's `force=true`. L4 filed the same
  finding independently as #1725.
- **F-L3-7 (NOW, raw material gathered — CORRECTED 2026-09-05)** — Constraint reconnaissance for
  the 19 D-CND-03 contracts. **My first pass was wrong and I am recording the correction rather
  than quietly restating it:** I queried `pg_constraint` only, which misses natural keys
  implemented as UNIQUE **indexes**. A W3 contract-authoring subagent caught it. Re-measured
  against `pg_index`, the genuinely keyless L3 tables are only **four**, not nine:
  `kala_convergence` (`ka_sangam`), `kala_obstruction` (`ka_vighnakara`), `kala_bhavishya`
  (`ka_bhavishya_lekha`), and — effectively — `kala_darshana` (`ka_kala_darshana`), which carries
  only a **partial** unique index (`WHERE convergence_id IS NOT NULL`), so every NULL-`convergence_id`
  row is unconstrained and accretion can hide there specifically.
  Five assets I had briefed as keyless in fact have real natural keys and were re-briefed mid-flight:
  `kala_activation` (chart, signal, ayanamsha, source_citation) · `kala_activation_predicates`
  (chart, signal, ayanamsha) · `kala_gochara_windows` and `kala_gochara_windows_v2` (chart,
  event_class, window_start, peak_date, milestone, resolution, **generation**) · `kala_jivana_parva`
  (chart, parva_index).
  **The doctrine consequence is unchanged and is why the correction mattered:** where the DB already
  enforces the key, a distinctness conjunct **cannot fail** and so fails C12's rewrite-floor test —
  such contracts must assert what the index cannot (tiling/contiguity, cross-table agreement with
  the upstream L0/L1 fact, per-group cardinality, range/NULL guards). Where it does not, distinctness
  is the only detector of the cross-build accretion §N.3 forbids.
- **F-L3-8 (NOW)** — `natural_key_partition` is NULL on all 23 L3 assets. Not L3-specific (L1 0/19,
  L2 0/22, L4 0/9, L5 0/15 — only L0 populates it, 21/40), so this is a campaign-wide pattern rather
  than an L3 omission; recorded here so W2 rules on it deliberately rather than by silence.

## CAPABILITIES LANDED

Charter C6 — announce here, on `main`, each NEW capability downstream layers may consume.
One line per capability with its PR number. Consumers poll `origin/main` for this section.

**LANDED:** _(none yet — nothing has merged)_

### PLANNED (published early per the session prompt's "publish your capability-delta list immediately")

This is L3's side of the C6 contract, declared at W1 so L4/L5 can plan against it rather than
discover it. Nothing here is consumable until it appears under **LANDED** with a PR number.

| capability | shape | who would consume it | status |
|---|---|---|---|
| **Temporal engine question-declarations** | a per-engine declaration in the registry: the one question each temporal engine answers, its granularity and range (D-TIME item 1) | L4 verdict surfaces choosing which clock to cite; any layer disambiguating two timing answers | planned, W3 |
| **Concordance verdict** on the arbiter surface | `aligned \| partially_aligned(reasons) \| disputed(adjudicated_by, reasons)` per (domain, range), with per-engine testimony as a drill (D-TIME item 2) | L4 outlook/anchor surfaces wanting one temporal voice instead of N | planned, W3 |
| **Authority profiles as stored data** | generalised from `kala_gochara_authority` + `kala_paddhati_profile` into a per-engine authority × strength-in-chart profile (D-TIME item 3) | anything needing to know *why* one engine outranked another | planned, W3 |
| **Temporal-confidence multiplier** | the concordance verdict exposed as a salience multiplier (D-TIME item 5) | **this one is a consumer, not a product**: it is HELD on L2's consensus/salience capabilities (C6) | held on L2 |
| **19 chart-partitioned integrity contracts** (D-CND-03) | a worked, live-verified set of `NOT EXISTS (… GROUP BY chart_id HAVING …)` invariants | not a runtime capability — a **pattern** L1/L2/L4/L5 can copy rather than re-derive, per the ruling on #1723 | planned, W3 |

### What L3 CONSUMES from upstream (the other side of the same contract)

| needed from | capability | blocks |
|---|---|---|
| **L2** | populated consensus / salience columns | the temporal-confidence multiplier wiring only. Everything else in the L3 mandate is upstream-independent — confirmed against the mandate item by item, not assumed. |

## Cost ledger

Wall-clock + tokens per asset; the CONDUCTOR rolls this into the root campaign cost section at
your layer close.

| asset | wall-clock | tokens | notes |
|---|---|---|---|

## Heartbeat

One line per loop: `<UTC ISO-8601> — <position> — <what you are doing>`.

- `2026-09-05T…Z — L3-W2/W3 — W1 closed 23/23 (index published); W2 closed 23/23 routed + 12 MUST / 12 NOW / 8 NEVER triaged; ka_taranga SPLIT decided with falsifiers; first two D-CND-03 contracts authored AND mutation-proved live (ka_kota_chakra 4/4 conjuncts fail on injected corruption). W3 open.`
- `2026-09-05T…Z — L3-W1 — batches A/B/C/D landed (E outstanding); verified the v1-corpus alert down to its real residuals; verified ka_gochara_resonance's 5 undeclared edges from writer SQL and filed #1734 — L3 has no honest canary, reported rather than manufactured.`
- `2026-09-05T…Z — L3-W1 — rulings absorbed (#1721 GRANTED/PR #1728; D-CND-03 binding; #1715 Option A — no W2 acceptance until it deploys); #1724 withdrawn as duplicate with acceptance recorded; constraint reconnaissance done for the 19 owed contracts; per-loop gate poll scripted; #1730 remains the open W4 blocker.`
- `2026-09-05T…Z — L3-W1 — bootstrap complete; DB read path live; C10 gate run (2 assets OPEN); 5 read-only W1 batch subagents dispatched (A gochara / B overlays / C services / D heavy+ssv / E artifact spine); 2 campaign-blocking findings filed as #1721 and #1724; deploy ancestry verified execution-safe.`
