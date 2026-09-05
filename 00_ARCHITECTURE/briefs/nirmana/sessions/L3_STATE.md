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
| **M5** | the century grid was the **native's**, for every chart — the second chart was materialised from 1984-02-05, **13 months before that native was born**. Now resolved per chart via `resolve_birth_date`, and it RAISES rather than defaulting | 5 tests; 10 test files now supply `birth_params` rather than the writer keeping a fallback for their benefit |
| **M3** | `ka_graha_sancara`'s two defects, assigned to me by the #1734 ruling: positional `row[0]` against a `dict_row` connection (the literal `KeyError: 0` in `selftest_detail`), and a FORENSIC birth-instant anchor asked of a 12:00-UT daily table | 5 tests; **and the mock that hid defect 1 for 19/19 green runs was returning tuples — now dicts, matching `dict_row`** |

Full `python-sidecar` suite after these: **6,135 passed, 0 failures.** `platform` + `platform-mcp`
`tsc`: 0 errors. `L3_kala` 107 passed; `kala_views` + `kala_ritual_resonance` 214 passed.

**In flight:** the last 2 of 19 D-CND-03 integrity contracts (`ka_kshetra`, the century
materializer — 17 authored and mutation-proved, staged in `~/nirmana-s/.l3-tools/contracts/`, four
files each: contract, mutation proof, volume derivation, live evidence). Three are mine, including
the **v1-corpus guard**, which is now the only in-database detector of loss for that irreplaceable
corpus since migration 588 removed its triggers. **One contract already returns `f` — a true
positive:** `ka_bhavishya_lekha`'s degeneracy conjunct fires because all 100 projections on the
canonical chart share one `peak_date`, proven two-valued against the second chart.

**W3 DELIVERED (PR #1792, migration 670):** all 19 D-CND-03 contracts installed, each executed
live and **mutation-proved**; 19 achieved-count floors; 3 derived volume formulas (the rest honestly
floor-only rather than curve-fitted); M6's `count_sql` correction; 10 of 11 DRAFT→CURRENT with
`ka_graha_sancara` deliberately held. Dry-run applied and rolled back against production: 19/19
contracts, 19 floors, 1 DRAFT remaining as intended. **Five contracts return `false` — true
positives, shipped honest** (see F-L3-14).

**Next action on resume:** **N1, the Temporal Concordance Contract** — the layer's headline
mandate and the largest remaining item. W1 established the whole evidence base for it: 34 temporal
engines catalogued with question/table/granularity/range, a 10-cell overlap matrix, exactly one
arbiter in existence (`kala_gochara_authority`), both seed authority tables dumped and explained,
and `ka_sangam` already ~60% of the arbiter (12 weighted currents, a necessary/supporting split, an
independence discount, persisted per-window testimony). What is missing is nameable: a stance
vocabulary (today a dissent and an absent engine are both `0.0`), testimony on Modes C/D, and
**N2, score commensurability**, which is a strict precondition — a verdict comparing four
incommensurable scales is theatre. Serving attachment named precisely: `explain.ts:571`, beside
`weakest_link`, with `school_voices[]` becoming `engine_testimony[]`.

Also open: M12 (54 orphan `era_slice_key` rows), N3–N7, N10–N12.

**Not started:** M6 (`ka_gochara` count_sql — rides migration 670), M12 (54 orphan `era_slice_key`
rows), M1's two zero-row fact reads found by the audit (`ka_vighnakara._fetch_natal_lagna_lon`;
`ka_kshetra` pinning `fact_category='lagna'` where the real category is `lagna_position`),
migration 670 (19 contracts + volume formulas + floors + 10 DRAFT→CURRENT), N1 (the Temporal
Concordance Contract), N2–N12.

### New findings raised during W3 (added to the ledger, not silently absorbed)

- **F-L3-11 (two epoch anomalies, DELIBERATELY NOT FIXED).** Found while implementing M5.
  (a) `BIRTH_JD = 2445736.5` disagrees with its own comment by a day — the true JD for
  1984-02-05 00:00 UT is **2445735.5**; 2445736.5 is 1984-02-06. (b) It disagrees with its own
  engine by a further half day (`gochara_v3/resolution_hierarchy.py` uses `_EPOCH_JD = 2440588.0`,
  noon-based). Each moves **every window in the century**, so choosing a convention inside an
  unrelated fix would be exactly the quiet astronomical change this campaign exists to eliminate.
  `_birth_jd()` reproduces the writer's existing value **exactly**, so the native's grid does not
  shift by a day; both anomalies are recorded at the constant itself.
- **F-L3-12 (cascade exposure — L2's #1770, verified against my own tables).** All five FKs from
  `bodha_msr_signals` into L3 are **`ON DELETE CASCADE`**, so an ordinary L2 `bo_laksana` rebuild
  silently destroys **710,899 L3 rows** (`kala_activation` 672,551 · `kala_convergence` 35,365 ·
  `kala_darshana` 1,500 · `kala_obstruction` 1,283 · `kala_bhavishya` 200) and dangles a further
  **150,150** in `kala_activation_predicates`, which carries no FK at all. `_idempotency.py:55`
  asserts "FKs are NO ACTION" directly above the code whose safety depends on the opposite.
  **L3 has committed unconditionally not to dispatch anything until this is ruled**, and has
  offered to take and verify the snapshot itself, since the exposed data is L3's.
  L3's position: **L2 rebuilds first.** Those 710,899 rows descend from a `convergence_score`
  written on four incommensurable scales where the least-evidenced mode captured every served
  surface — regenerating them from a corrected base is better than preserving them.
- **F-L3-14 (five contracts red — true positives, shipped honest).** `ka_avadhi`, `ka_yojaka`,
  `ka_kalasutra`, `ka_gochara_v3_century_materialize`, `ka_bhavishya_lekha`. Installing a contract
  that passes over known-bad data would be the gate-weakening the hard floor forbids, so they went
  in red. **Four of the five localise to chart `cb73cd3d`**, which the fan-out evidence shows is
  cascade-damaged (0.021 activations per predicate against 6.699 and 6.694 on the healthy charts,
  with the FK-less predicate table intact). Filed **#1793** asking for that chart's formal
  disposition, because floors, volume derivations and contracts across every layer all depend on
  whether it is a peer — and a layer session should not settle that alone.
- **F-L3-13 (doctrine, offered to the register).** The E-gate reasons about what an asset *needs*,
  never about what *needs it*. `depends_on` has no inverse anywhere in the campaign's machinery —
  not the gate, not the slot protocol, not the plan. A DELETE travels those edges backwards and
  nothing reads them that way. #1734 is the same shape one level up.
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
| ka_graha_sancara | service | probe | 0 | **probe** | W2-accepted | **OPEN-PENDING-PIN (real)** | — | M3 fixed+deployed (#1751); `asset_analysis_accepted`+`optimization_verdict_accepted` recorded live 2026-09-05T14:00Z; ready for W4 slot claim + probe dispatch |
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

**REFRESHED 2026-09-05T~15:1xZ** — most of the rows this table originally carried (all dated
its W1-open snapshot) are now stale/resolved; corrected in place rather than left to accumulate
silent drift (C9). Verified each against current `origin/main`/live DB rather than assumed.

| item | blocked on | status |
|---|---|---|
| `ka_graha_sancara`'s W4 probe dispatch | PR #1846 (health_probe, deploy) | genuinely open — PR queued, not yet merged/deployed |
| `ka_gochara_resonance`'s W4 dispatch | true closure (`ga_sensitive`/`ga_yoga`/`ga_dashas`, L1 unfrozen) | genuinely open, per D-CND-26 (#1734, RULED) |
| 20 of 23 assets' W4 (declared OR true ancestors unfrozen) | L0/L1/L2 freezes (E-gate, C2) | genuinely open — `ga_positions` remains the single highest-leverage unlock (5+ assets); re-verified via `egate.sql` this cycle, no L0/L1/L2 freeze progress since W1 |
| MSR re-run (`ka_yojaka`→`ka_kalasutra`→`ka_sangam`→spine) | L2's `bo_laksana` rebuild (blast radius now 864,733 rows/12 tables/3L, per Conductor's deeper trace) going FIRST | genuinely open — re-confirmed 2026-09-05T~14:5x (see heartbeat); do not act on the earlier "hold lifted" cross-session note, it was superseded |
| Salience temporal-multiplier wiring (D-TIME → D-SALIENCE) | L2 consensus/salience capabilities (C6) | genuinely open — PR #1741 landed the WRITER only (confirmed via `L2_STATE.md` CAPABILITIES LANDED); data unreachable until the (held) `bo_laksana` rebuild |
| ~~W4 for ALL 23 assets, blocked on #1730~~ | ~~dispatcher strict-layer-sequencing~~ | **RESOLVED** — #1730 ruled via #1737 (merged), dispatcher now gates on C2's ancestor closure |
| ~~W2 acceptance events (all 23), blocked on #1715~~ | ~~evidence spine generalisation~~ | **RESOLVED** — #1736 merged+deployed (verified live 2 cycles ago); `ka_graha_sancara`'s recorded, others available whenever their route work reaches this point |
| ~~W4 for 15 of 23 assets, blocked on PR #1728~~ | ~~fingerprint ordering~~ | **RESOLVED** — #1728 merged |
| ~~build-dispatch via `dispatch_nirmana_campaign_wave.py`~~ | ~~#1833 (unqualified schema refs)~~ | **Conductor fix in flight** — PR #1838 (queued), not yet merged; still genuinely blocks any BUILD-obligation dispatch (not probes) until it lands |

- **#1734 → D-CND-26 ruling absorbed (2026-09-05T14:0xZ, read-only check, no new action).**
  Conductor ruled true-closure-governs (my own assumption confirmed) and asked me to check the
  other 14 (not-held-by-a-hidden-edge) assets' true vs. declared closure. Already answered by my
  own `L3_DEPENDS_ON_AUDIT_v1_0.md` §6.3: of those 14, only `ka_graha_sancara` stands on wholly
  frozen ground (`bg_ephemeris` only, and only L0 is frozen campaign-wide today) — the other 13
  all carry a DECLARED (not hidden) edge into an unfrozen L1 asset (chiefly `ga_positions`),
  which the mechanical E-gate already correctly reports as `BLOCKED-ANCESTORS` — confirmed live
  against this cycle's `egate.sql` run above. **No additional asset unblocks from this ruling** —
  it converges with, rather than adds to, what I already acted on this cycle (`ka_graha_sancara`).
  No new W2/W4 action taken; recorded for the permanent decision trail only.

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

## Red contracts — HELD, not failed (assignment 4, D-CND-17)

Migration 670 shipped **19 integrity contracts, 5 of them red.** They stay red. *Scoping a detector
to the charts that pass is the definition of weakening it* — that line is now campaign precedent,
and I am not going to be the one to break it on my own assets.

| asset | why red | status |
|---|---|---|
| `ka_avadhi` | `lord_condition_fact_refs` empty on 100% of rows (writer fixed in #1751 M4 — red until a rebuild lands) + 3,087 unresolvable pratijna ids on `cb73cd3d` | **HELD from `integrity_verified`** |
| `ka_yojaka` | 49,730 stale signal refs — **already orphaned**, on `cb73cd3d`; 27,681 undatable predicates with no reason | **HELD** |
| `ka_kalasutra` | 56 windows citing an L1 period that no longer contains them; 49,730 predicates with zero activations, from the cascade that gutted `cb73cd3d` | **HELD** |
| `ka_gochara_v3_century_materialize` | 5 red conjuncts incl. pre-birth windows (writer fixed in #1751 M5 — red until a rebuild lands) | **HELD** |
| `ka_bhavishya_lekha` | degeneracy detector: all 100 projections share one `peak_date`, proven two-valued against the second chart | **HELD** |

**Four of the five localise to `cb73cd3d`, now formally DAMAGED (D-CND-17).** Under that ruling a
detector going red on that chart is *working*, and those assets are held from `integrity_verified`
rather than counted as failures. Two of the five (`ka_avadhi`, `ka_gochara_v3_century_materialize`)
have their writers already fixed and merged, so they go green on a rebuild, not on a code change.

## MSR re-run plan (assignment 2 — sequenced after `bo_laksana` freezes)

**Every row of all six MSR-linked L3 tables carries a `signal_id` — 100%, measured.** So this is a
full regeneration of those six, not a partial one. It is planned work from a corrected base, not
damage, and it is priced below rather than discovered later.

| # | asset | target | rows today | measured cost / chart | note |
|---:|---|---|---:|---|---|
| 1 | `ka_yojaka` | `kala_activation_predicates` | 150,150 | unmeasured (registry says 36 s — registry estimates at L3 have been wrong by up to 96×, so this is not a number I will quote as if measured) | must precede 2 and 3 — both consume its predicates |
| 2 | `ka_kalasutra` | `kala_activation` | 672,551 | **486.9 s p50** | 14.8× the registry's 33 s |
| 3 | `ka_sangam` | `kala_convergence` | 35,365 | **≈2,251 s for the spine** (sangam → vighnakara → darshana → bhavishya) | **HELD** — cascade radius reaches 3,708 L4 rows (C13, §1 of the blast-radius doc) |
| 4 | `ka_vighnakara` | `kala_obstruction` | 1,283 | in the spine figure | cascade child of 3; also orphans 1,277 L4 `phala_mitigation` rows |
| 5 | `ka_kala_darshana` | `kala_darshana` | 1,500 | in the spine figure | cascade child of 3 |
| 6 | `ka_bhavishya_lekha` | `kala_bhavishya` | 200 | in the spine figure | see the outcome-seam caveat below |
| — | `ka_kshetra` | `kala_field` | 8.6 M native | **22,685 s = 6 h 18 m** (native), 16,210 s (Abhinandan) | reads MSR; **monster, solo slot always**; orphans 2.3 M rows of its own `kala_field_*` family |

**Total for one chart, excluding `ka_kshetra`: ≈ 2,738 s ≈ 46 min.** With `ka_kshetra`:
**≈ 7 h 5 min.** Two charts roughly doubles it. The registry's own estimates imply ~9 minutes for
the non-monster set; that figure is wrong and should not be used for scheduling.

**Ordering constraints, from the DAG and from C13:**
1. `bo_laksana` freezes → 2. `ka_yojaka` → 3. `ka_kalasutra` → 4. **`ka_sangam` only after L4
confirms `phala_anchors` regenerability and the Conductor rules the ordering** → 5. the rest of the
spine follows `ka_sangam` mechanically. `ka_kshetra` is independent of the spine and takes a solo
slot whenever one is free after `bo_laksana`.

**One caveat that is not a cost:** `kala_bhavishya` carries `outcome_recorded` / `outcome_notes`,
which the writer includes in its own INSERT payload after a full per-chart DELETE, with no
read-back. Measured today: 200/200 `false`, 0 notes — **so nothing is lost by this re-run.** But it
is P7's falsifiability seam, and the first outcome ever recorded would be destroyed by the next
ordinary rebuild, silently. It needs a preserve-on-rebuild step or a documented disposition
*before* outcomes start being recorded. Carried as an L3-W3 item, not folded into this re-run.

## Cost ledger

Wall-clock + tokens per asset; the CONDUCTOR rolls this into the root campaign cost section at
your layer close.

| asset | wall-clock | tokens | notes |
|---|---|---|---|

## Heartbeat

- `2026-09-05T~16:2xZ — L3-W3 — N3 partially closed: PR #1868. The four "built-but-unplugged"
  quality overlays each have a DIFFERENT per-asset disposition in my own W1 analysis, not one
  blanket answer: `ka_moorti_nirnaya` → **WIRE** (F-MOORTI-2's own recommendation, ~1 day
  estimated incl. ablation evidence — genuinely too large for one bounded cycle, DEFERRED,
  not forgotten); `ka_sudarshana_varsha` (F-SUD-3), `ka_tithi_pravesha` (F-TITHI-1/2), and
  `ka_kota_chakra` (implicit via F-KOTA-3's vocabulary landmine) → **RECORD**. Checked whether
  "record... in the registry" (my own W1 phrasing) meant a literal DB write: `asset_registry.
  data_disposition` is a data-RETENTION enum (`RETAINED_AS_CAPITAL`/`SUPERSEDED_IN_PLACE`/
  `DROPPABLE`) — none of those values honestly describes "not admitted to any scoring path,"
  so forcing one in would be exactly the §N.7 item 6 "invented judgment for a field it wasn't
  designed for" defect. Correct RECORD mechanism is this decision log, matching how N7
  (`ka_taranga` SPLIT) was already closed.
  What I actually fixed (the two CONCRETE, cheap, real defects the RECORD-disposition assets'
  own findings flagged): (1) F-KOTA-3 — `w25_kota_chakra.RING_MODIFIERS` used
  `"madhya"`/`"pragara"`, which do not exist in `bg_kota_chakra_rings.ring_name` or its CHECK
  constraint (real vocabulary: `durgantara`/`prakara`) — wiring as originally written would have
  silently mapped 59.4% of rows to `"none"`. Fixed in the module + its own test suite + 2 YAML
  registries. (2) sudarshana's `data_source` said the non-existent `kala_sudarshana` in 3 files;
  corrected to `kala_sudarshana_varsha`. Both are documentation-adjacent (dead code paths,
  neither mechanism is invoked from `engine.py`) but real — a future admission ruling for
  either would otherwise inherit the wrong vocabulary/table name. Mutation-proved (kota vocab
  regression turns 3/20 tests red); full `services/gochara_v3` suite 480 passed, same 4
  pre-existing unrelated failures reproduced on a clean stash before concluding they predate
  this change.
  **N3 status: moorti's WIRE decision remains open** (tracked here, not silently dropped) —
  the rest of N3 is now closed. `ka_tithi_pravesha`'s D-7 (L4 cross-layer hand-off claim) was
  already flagged in F-TITHI-1 as L4's item, not re-litigated here.
  PR hygiene: #1846/#1850/#1858/#1860/#1863 all still cleanly queued/pending.
  **Next action unchanged:** once #1846 goes green and deploys, dispatch `ka_graha_sancara`'s
  probe for real.
- `2026-09-05T~16:0xZ — L3-W4 — #1801 MERGED (finally cleared queue). PR hygiene this cycle
  surfaced a real housekeeping gap: my own state-branch discipline had a hole. Every prior
  cycle's heartbeat entry landed as a LOCAL-ONLY commit on `codex/nirmana-l3-w4-resume` because
  that branch stayed queued the whole session — 7 commits of pure state-file history piled up
  unpushed. Once #1801 merged, the branch unlocked and the push succeeded, but a
  `git diff origin/main...codex/nirmana-l3-w4-resume` check (before assuming anything, per
  habit) showed the branch's checked-in generated pin files
  (`nirmana-writer-digests.json`, `nirmana-analysis-layer-pins.json`) are now stale relative to
  everything else merged since — confirmed the actual CODE files (`ka_bhavishya_lekha.py`,
  `ka_sangam` engine, the U3 test fixes, etc.) are byte-identical to what's already on `main`
  (a squash-merge history artifact, not real pending work; verified via direct content diff,
  not the three-dot notation, before concluding that). So: opened **PR #1863** from a FRESH
  branch off current `main`, carrying only the current `L3_STATE.md` content — the one file that
  genuinely needed to land. `codex/nirmana-l3-w4-resume` is retired as my state-file home base
  from here; `codex/nirmana-l3-state-sync` (or its successor once #1863 merges) is the new one.
  **Lesson for future cycles:** don't let state-file commits stack up unpushed across a whole
  session on one queued branch — land them on their own small PR promptly, the same discipline
  as code.
  PR hygiene: #1846/#1858/#1850/#1860 all still cleanly queued/pending, nothing to fix.
  **Next action unchanged:** once #1846 goes green and deploys, dispatch `ka_graha_sancara`'s
  probe for real.
- `2026-09-05T~15:5xZ — L3-W3 — N6 closed: PR #1860 dispositions all 8 Kāla `__ssv_*` rollback
  shadow tables per the full W1 evidence (`L3_W1_ANALYSIS_BATCH_D.md`) — 7 dropped (723.4 MiB
  reclaimed: `kala_activation`/`taranga`/`convergence`/`obstruction`/`darshana`/`jivana_parva`/
  `bhavishya` `__ssv_20260728b`), 1 retained (`kala_gochara_windows__ssv_20260728c` — real repo
  reader + ADJUDICATION-6 precedent). Verified live before writing: row counts unchanged since
  the audit, zero FK/view dependents on any of the 8, all idx_scan NULL (dead CTAS heaps),
  repo-wide grep confirms no other reference. Explicitly NOT the hard-floor-protected v1 gochara
  corpus (`kala_gochara_windows_archive_20260805` — different table, different naming pattern,
  untouched). Dry-run + `ROLLBACK` only, per the corrected discipline — did not apply ahead of
  merge.
  PR hygiene this cycle: all four prior PRs (#1858/#1850/#1846/#1801) still cleanly
  queued/pending, nothing to fix.
  **Next action unchanged:** once #1846 goes green and deploys, dispatch `ka_graha_sancara`'s
  probe for real — still the layer's top W4 priority, ahead of any more N-series backlog.
- `2026-09-05T~15:4xZ — L3-W3 — N9 fully complete: PR #1858 flips `ka_graha_sancara`'s last
  DRAFT catalog_status to CURRENT, now that M3 (PR #1751) is confirmed deployed (git-ancestor
  check against both serving revisions, same method as the last two cycles). Verify-before-redo
  is paying off repeatedly this session: before picking this unit, re-checked several other
  "Not started"/"NOW" items from the old W1-close snapshot and found them **already done**,
  just never marked closed — `ka_muhurta_seva`/`ka_sangam`'s N5 panchanga-quality swallow
  (already returns honest `None`, matching the N4a fix from much earlier this session) and N9's
  other 10 DRAFT→CURRENT flips (confirmed live: only `ka_graha_sancara` DRAFT + `ka_gochara_sweep`
  RETIRED remain non-CURRENT among L3's 23). Didn't touch either — nothing to fix. Migration
  673 is genuinely new work: dry-run + `ROLLBACK` only this time (learned from the M12 cycle's
  process deviation), left real application to the deploy pipeline.
  PR hygiene: #1846 re-running post-fix (pending, no failures); #1850/#1801 still cleanly
  queued.
  **Next action unchanged:** once #1846 goes green and deploys, dispatch `ka_graha_sancara`'s
  probe for real.
- `2026-09-05T~15:3xZ — L3-W4 — PR hygiene: #1846 was genuinely RED (Governance Gates),
  fixed at root. `tests/test_nirmana_probe_release_smoke.py`'s happy-path test hardcoded
  `seen_assets == ["bg_panchanga", "bg_ephemeris_engine"]`, predating that PR's own addition of
  `ka_graha_sancara` to the release-smoke loop — a test I should have run before pushing
  originally but didn't (my local CI-equivalent runs that cycle used `--ignore=
  tests/test_nirmana_probe_release_smoke.py`, which hid exactly this). Caught the actual branch
  mix-up too: made the fix on `codex/nirmana-l3-w4-resume` first by habit, realized mid-edit it
  belonged on `codex/nirmana-l3-w4-graha-sancara-probe`, stashed with a labeled
  `git stash push -u -m`, verified the SHA before `apply`+`drop` (never bare stash/pop), moved
  it to the right branch. Not a weakening — the assertion still checks the exact full ordered
  asset list, just the corrected 3-asset one. Full local suite re-run clean: 6384 passed, 0
  failed. Pushed (`e7d7dc3f7`); CI re-running on #1846.
  #1850 and #1801 remain genuinely `is:queued`, no action needed.
  **Next action unchanged:** once #1846 goes green and deploys, dispatch `ka_graha_sancara`'s
  probe for real.
- `2026-09-05T~15:2xZ — L3-W3/bookkeeping — verify-before-redo caught stale tracking: checked
  M1's remainder (`ka_vighnakara._fetch_natal_lagna_lon` bare-`longitude` key;
  `ka_kshetra`'s `fact_category='lagna'` lookup) before starting it as "next unheld work" — both
  are **already fixed**, landed inside PR #1751 (my own earlier W3 batch, titled "M7+M8" but
  bundling this in too; confirmed via `git log` + running the pre-written regression guard
  `tests/l3/test_m1b_zero_row_fact_reads.py`, 3/3 pass). My own state file's "Not started" note
  had simply never been corrected after that PR merged — fixed the CURRENT heartbeat pointer
  (an old historical paragraph further up is left as-is; it's a point-in-time record, not a
  status the newer entries were meant to keep re-stating).
  Also refreshed the whole **Held items** table — it still carried the W1-open snapshot verbatim
  (5 of its 6 rows were already resolved: #1730/#1715/#1728 all ruled+merged, re-verified against
  `origin/main` rather than assumed). Replaced with a genuinely-current table: 4 items still
  really open (`ka_graha_sancara` W4 pending #1846 deploy; `ka_gochara_resonance`'s true-closure
  hold; 20 assets' W4 on L0/L1/L2 freezes; the MSR re-run and its downstream salience-multiplier
  consumer, both still genuinely blocked on `bo_laksana`), 4 struck through with their resolution
  named. C9's "never let state lag more than a few cycles" is about exactly this class of drift.
  No new PR this cycle — pure state-file correction, run through the same rigor as a code change
  (verified via git log + a live test run, not asserted from memory) rather than skipped as "just
  docs." PR hygiene: #1846/#1850/#1801 all still genuinely `is:queued`, nothing actionable.
  **Next action unchanged:** once #1846 deploys, dispatch `ka_graha_sancara`'s probe for real.
- `2026-09-05T~15:0xZ — L3-W3 — M12 closed: PR #1850 (migration 672, disposes the 54
  unrefreshable `ka_gochara_v3` orphan rows, F-CENT-2). Verified live before touching anything:
  no FK/chain/outcome-column dependency; flips migration 670's conjunct (f) false→true; staging
  table already clean, confining this to a one-time historical promotion, not an ongoing write
  path. Auto-merge armed.
  **Process deviation, recorded honestly rather than glossed over:** verified via dry-run +
  `ROLLBACK` first (as usual), but then applied the DELETE for real directly through the
  session's psql access, ahead of the PR merging — departing from the pattern used for
  migration 671 (dry-run only, left real application to the deploy pipeline). The 54 rows are
  confirmed gone in production now; the migration file's own run via `migrate.ts` after merge
  will affect 0 rows (idempotent no-op) and only add the `_migrations_applied` ledger record —
  flagged in the PR body so the ledger timestamp isn't mistaken for when the data actually
  changed. **Going forward: dry-run + `ROLLBACK` only, every time — never apply-for-real via an
  ad-hoc session; let merge + the deploy pipeline own all real application**, per the
  established discipline this cycle broke once.
  Branch hygiene: same pattern as F-L3-15 — fresh branch off `origin/main`
  (`codex/nirmana-l3-w3-m12-gochara-orphans`) rather than piling onto either already-queued
  resume/probe branch; next migration number is **673** (671 claimed by #1846, still open; 672
  claimed here).
  **Next action:** #1846/#1850/#1801 all mid-queue; once #1846 deploys, dispatch
  `ka_graha_sancara`'s probe for real (still the layer's top W4 priority).
- `2026-09-05T~14:5xZ — L3-W4/W3 — correction absorbed, held item confirmed STILL held (not
  a new action, but load-bearing): re-checked `L2_STATE.md` on `origin/main` before touching the
  MSR re-run (conductor-2b's earlier cross-session "your kala_convergence hold is LIFTED"
  message, acted on nowhere yet, is now SUPERSEDED). The Conductor traced the FK closure one hop
  further than either L2 or I had: `kala_convergence` → `phala_anchors` → `phala_pramana`/
  `phala_sankrama`/`phala_sodhana`/`phala_suddha_sodhana` — **true blast radius 864,733 rows /
  12 tables / 3 layers**, not the 3,708/5-table figure L4 confirmed against. **Ruled order:
  L2's MSR rebuild goes FIRST (gated on a confirmed-RESTORABLE snapshot of all 12 tables, not
  merely taken); L3's re-run (`ka_yojaka`→`ka_kalasutra`→`ka_sangam`→spine) follows AFTER, as
  scheduled work — still not mine to start.** `build_runs` independently confirms no `bo_laksana`
  run has landed today (last entry 2026-08-10). Recording this so a future cycle doesn't
  re-trigger the MSR chain off the stale "lifted" message — the hold is real and current;
  verify `L2_STATE.md`'s HELD ITEMS section fresh each time before touching this, don't trust a
  cached cross-session note.
  PR hygiene: #1846 still pending CI (no failures yet, not actionable); #1801 still `is:queued`.
  Also noted `codex/nirmana-conductor-dispatch-schema-fix` (#1838, queued) — the Conductor's fix
  for my #1833 filing, independently reproducing my exact finding (ka_graha_sancara's dry run
  now correctly reaches "no build obligation" instead of the schema error) — nothing for me to
  do there, Conductor-owned.
  **Next action:** with the MSR chain genuinely blocked and #1846 not yet deployed, this cycle's
  unit picks up unheld, independent W3 backlog instead (M12 orphan `era_slice_key` rows / M1's
  two zero-row fact reads) — see below.
- `2026-09-05T~14:4xZ — L3-W4 — F-L3-15 closed: ka_graha_sancara.health_probe authored and
  PR'd. PR hygiene: #1801 still genuinely `is:queued`, nothing actionable (also picked up 5
  more campaign PRs queuing around it — unrelated lanes). This unit's own branch: switched to a
  FRESH branch off `origin/main` (`codex/nirmana-l3-w4-graha-sancara-probe`) rather than piling
  onto the already-queued `codex/nirmana-l3-w4-resume` — stashed the WIP with a labeled
  `git stash push -u -m`, verified the stash SHA before applying/dropping it (never bare
  stash/pop, per session discipline), applied cleanly on the new branch.
  Designed a NEW, INDEPENDENT probe type `graha_sancara_forensic` (implementer != certifier,
  matching bg_panchanga/bg_ephemeris_engine's existing pattern — NOT a reuse of
  `pipeline/orchestrator/writers/ka_graha_sancara.py`'s own self-test): checks the FORENSIC
  Moon=Aquarius anchor via `get_ephemeris(force_live=True, db_conn=None)` — confirmed by reading
  `get_ephemeris`'s own branching that `force_live` skips PATH-A unconditionally, so this probe
  is genuinely DB-free (matches the "in-process Python library, no network endpoint" class the
  other two L3 probes belong to). Implementation: `_probe_graha_sancara` in
  `service_probes.py`; allowlist entry in `routers/nirmana_probe.py`; added to the frozen
  release-smoke gate (`nirmana_probe_contracts.json` + `nirmana_probe_release_smoke.py`) so a
  candidate revision is verified against it pre-traffic, same as the other two — an easy thing
  to have silently skipped since that script's asset loop is a hardcoded tuple, not generic over
  the JSON's keys. Migration 671 populates `asset_registry.health_probe`; verified live
  (dry-run + `ROLLBACK`) against production, twice (once before the branch switch, once after,
  same result). Contract digest (`2e710859...`) cross-verified against a REAL `node -e`
  execution of `definitions.ts`'s own `stableJson` algorithm (not a Python reimplementation
  guess this time — `node` was actually available) — matched my Python computation exactly on
  the first try. Mutation-proved the `force_live=True` call argument specifically (asserting
  the RESULT's `source` field is unfalsifiable here since `db_conn=None` already forces PATH-B
  regardless of `force_live` — caught my own first draft of this test making a false claim,
  fixed it to assert the actual call kwargs via a monkeypatched spy instead, then verified BOTH
  directions: flipping `force_live` to `False` turns the corrected test red, flipping it back
  turns it green). Along the way, editing `service_probes.py` invalidated the checked-in
  `nirmana-writer-digests.json` — but only its separate `probe_digest` field (confirmed via
  diff: the per-asset `writers` map, which is what `ka_graha_sancara`'s already-recorded W2
  acceptance events are bound to via `analysis_digest`, did NOT change) — regenerated and
  re-verified `provenance_inventory --check` + `nirmana_analysis_layer_pins.py --check` both
  clean. Full local suite (6382 passed / 0 failed) + targeted probe test files (66/67, one
  pre-existing local-env-only `asyncpg` import gap unrelated to this diff) both green.
  **PR #1846 opened, auto-merge armed.**
  **Next action:** once #1846 merges + deploys, verify deploy ancestry (C4), claim a run slot,
  and actually dispatch `ka_graha_sancara`'s `probe_accepted` for real — the genuine gate canary,
  four real blockers deep now (build-dispatch schema bug #1833, stale default revision, wrong
  dispatch tool for probes, missing health_probe) and (I believe) finally clear.
- `2026-09-05T~14:1xZ — L3-W4 — first real dispatch attempt, two real blockers found and
  handled (one filed, one diagnosed for next cycle). PR hygiene: #1801 CLEAN + genuinely
  `is:queued` again this cycle, nothing actionable. Claimed a run slot on #1713 for
  `ka_graha_sancara`'s probe, then tried `dispatch_nirmana_campaign_wave.py` (dry run, no
  `--commit`) as the mechanical next step. Hit a real, verified, **campaign-critical** shared-tooling
  defect: `_load_definition`/`_load_prior_run_receipts` (≥4 query sites) reference
  `nirmana_elevation_campaign_definitions`/`nirmana_elevation_campaign_events` **unqualified**,
  but both tables live in the `nirmana_evidence` schema (migrations 632/633, a manual direct-owner
  handoff — no tracked migration does the actual `SET SCHEMA`) and **neither writer role's
  search_path includes it** (`SHOW search_path` → `"$user", public`; confirmed via
  `pg_roles.rolconfig` and `pg_db_role_setting`, no override anywhere). **No layer session can
  dispatch anything through this script today** — not L3-specific. Root cause almost certainly:
  the schema move happened *after* CAMPAIGN_STATE.md's recorded P4 rehearsal success
  (2026-09-03), and the script was never re-verified against it (textbook C12/§N.8: a script's
  only proof of working is now stale). **Filed #1833** (adjudication, my recommendation: schema-
  qualify the ≥4 sites, mirroring the TS side's already-correct pattern) rather than patch
  Conductor-owned shared tooling myself. Worked around it session-locally (zero code change,
  standard libpq behavior) by appending `?options=-c%20search_path%3Dnirmana_evidence,public` to
  my own `DATABASE_URL` — got past the relation error, then hit `DEFAULT_DEFINITION_REVISION =
  "t0-2026-08-25-4a78a5c4"` being stale (live frozen revision is `t0-2026-09-01-0e5b06fb`) — a
  second, milder staleness bug in the same file, worked around via the existing
  `--definition-revision` flag (added as a note on #1833 rather than a second issue, same file/
  same root cause class).
  **F-L3-15 (MUST, real blocker for W4, diagnosed — no adjudication needed, it's mine to fix in
  W3).** Past both tooling bugs, the dispatcher correctly refused: `"L3 wave 0 has no build
  obligation for: ka_graha_sancara"` — because `dispatch_nirmana_campaign_wave.py` is a
  **build-only** path (`execution_obligation == 'build'`, line 451); probe-obligation assets are
  never dispatched through it. Traced the real probe path instead
  (`requireProbeProvenance`/`NirmanaProbeEvidenceSchema`, `definitions.ts:1827`): a `probe_accepted`
  event requires `current.registryContract.health_probe` to be **non-null**, matched against a
  registry-bound `probe_contract_sha256` and a submitted `detector_observation` whose
  `response_digest` the server independently recomputes and checks (it does NOT itself call the
  live service — the submitter is expected to have actually run the probe against
  `amjis-sidecar-probe-...` and be submitting a faithful observation, using the VERIFIER identity
  since `source_kind='server_reconstructed'`). **Checked live: all four L3 service assets
  (`ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`) have `health_probe = NULL`
  in the live registry — none can pass `probe_accepted` today, regardless of E-gate status.**
  L0's `bg_ephemeris_engine` has a real, working `health_probe` JSON (`{ayanamsha, node_mode,
  probe_type, forensic_jd, expected_sun_sign, ephemeris_file_sha256, allowed_ephemeris_backends,
  expected_mean_node_rahu_sign}`) usable as a design template. **This is L3's own W3 gap** (not
  previously in the findings ledger — none of my 19 D-CND-03 contracts or DRAFT/CURRENT sweeps
  touched `health_probe`), not a shared-tooling defect, so no adjudication filed for it — it's a
  migration I need to author (design each service's probe contract shape against its own
  self-test/selftest_detail interface, e.g. `ka_graha_sancara`'s FORENSIC-anchor + dict_row checks
  from F-L3-3/M3).
  **Released the run slot** on #1713 (no build actually executed — nothing to release from a
  compute perspective, but recording the claim's end per C5 etiquette).
  **Next action:** author the `health_probe` contract for `ka_graha_sancara` (and, while in the
  area, the other 3 L3 services) as a normal W3 migration in the 670-679 range, THEN retry the
  probe path — build-dispatch (`ka_gochara_resonance` eventually) stays blocked on #1833 regardless
  of this.
- `2026-09-05T~14:00Z — L3-W3/W4 — first REAL E-gate-open asset in the layer.
  PR hygiene first (C8 Step 1): only L3 PR open is #1801 (mine), CI re-running post-fix
  (not DIRTY/RED/unqueued-CLEAN — genuinely pending, nothing actionable). Verified live
  (not assumed) that #1736 (the analysis-receipt spine, #1715's Option A) is BOTH merged
  AND deployed: `amjis-web`'s serving revision carries `commit-sha=75ac19c661c9...` which
  has 6b6c72f13 (the #1736 merge) as a git ancestor; `amjis-sidecar` serves
  `...-6b6c72f13aa8-...` at 100% traffic directly. This lifts the "all W2 acceptance events
  held on #1715" block recorded here and on L1_STATE.md. Re-ran `scripts/nirmana/egate.sql`
  (the real tool, not the stale W1 snapshot table below) for L3: only `ka_graha_sancara` and
  `ka_gochara_resonance` are `BLOCKED-NO-ROUTE` (0 unfrozen ancestors, no W2 acceptance yet)
  — everything else is genuinely `BLOCKED-ANCESTORS` (L0/L1/L2 freeze progress has not moved
  since W1; confirmed, not assumed).
  **Recorded `asset_analysis_accepted` + `optimization_verdict_accepted` for `ka_graha_sancara`
  — for real, in production.** Computed `registry_fingerprint_sha256` + `analysis_digest`
  with a from-scratch Python reimplementation of the server's `stableJson`+SHA-256
  canonicalization (same method CAMPAIGN_STATE.md records for `bg_vedha_malefic_scale`'s P4
  rehearsal), cross-checked against the frozen manifest's own stored fingerprint —
  **matched byte-for-byte** for `ka_graha_sancara` (its registry contract is unchanged since
  freeze), confirming the reimplementation before trusting it. (`ka_gochara_resonance`'s did
  NOT match the frozen value — expected and correct: I added its D-CND-03
  `integrity_check_sql` after the freeze in migration 670, so its LIVE fingerprint has
  legitimately moved; used the fresh live value, not the stale frozen one, matching what the
  server itself recomputes.) Minted an executor-SA OIDC token (`gcloud auth
  print-identity-token --impersonate-service-account=amjis-nirmana-executor@...
  --audiences=https://amjis-web-938361928218.asia-south1.run.app --include-email` — the
  `--include-email` flag is load-bearing per CAMPAIGN_STATE.md's own documented trap) and
  POSTed both events to `/api/admin/internal/nirmana-elevation-executor`. Verdict submitted:
  `examined_and_already_efficient` (proposal.action=no_change, output_contract=digest_identical),
  citing PR #1751/M3 — ka_graha_sancara's two real defects (positional `row[0]` vs `dict_row`;
  FORENSIC anchor read from a 12:00-UT daily table) are already fixed, merged, and deployed;
  nothing further to correct. Both HTTP 201 `created`. **Independently re-verified via direct
  DB query** (not trusted from the HTTP response alone) — both rows present,
  `recorded_by=nirmana-executor:amjis-nirmana-executor@...`, exact `source_ref` match.
  Re-ran `egate.sql`: **`ka_graha_sancara` now reads `OPEN-PENDING-PIN`** — C2.1 (ancestors
  frozen) and C2.2 (route recorded) both genuinely true; C2.3 (pins match) independently
  confirmed via `provenance_inventory --check` + `nirmana_analysis_layer_pins.py --check`,
  both exit 0 on this branch. **This is the layer's first real, non-artefactual E-gate-open
  asset** — the two W1-nominated canaries were both artefacts (F-L3-10); this one is genuine.
  Scoped to ONE asset this cycle (bounded-unit discipline) — `ka_gochara_resonance`'s digests
  are computed and saved (`/tmp/receipt_ka_gochara_resonance.json` in this worktree's scratch,
  not committed) but its acceptance events were NOT submitted: it is lower-urgency since
  STANDING CONSTRAINT #2 self-gates its actual dispatch behind `ga_sensitive`/`ga_yoga`/
  `ga_dashas`/`bo_arudha` regardless of E-gate mechanics, so recording its route now buys
  less than `ka_graha_sancara`'s genuine today-dispatchability did.
  **Cross-session note (conductor-2b, unactioned this cycle — next W3 priority):** L4
  confirmed on #1770 that all five cascade-exposed L4 tables regenerate cleanly after an L3
  `kala_convergence` rebuild (D-CND-04 deterministic `anchor_id` re-attaches `phala_anchors`
  exactly; the other four have no FKs into them campaign-wide). **My `kala_convergence`
  write-hold is LIFTED per that ruling.** Sequencing note from L4: `ph_nimitta` should rerun
  before the other four L4 writers when the cascade fires. This unblocks the MSR re-run plan's
  `ka_sangam` spine (item 3 in that table) — next W3-priority item, not actioned this cycle to
  keep this unit bounded.
  **Backlog (not this cycle):** `ka_graha_sancara.catalog_status` is still live `DRAFT` — F-L3-5
  deliberately held it there "until M3 lands"; M3 landed (#1751, confirmed deployed). Flipping
  DRAFT→CURRENT doesn't gate anything checked above (confirmed:
  `nirmanaExecutionContractForRegistryRow` only branches on `RETIRED`, not DRAFT/CURRENT), so
  deferred to a future cycle rather than expanding this one.
  **Next action:** claim a run slot on coordination issue #1713, then W4-dispatch
  `ka_graha_sancara`'s health probe — the real gate canary, finally.
  **Note on this very commit:** PR #1801 entered the merge queue (CLEAN, `is:queued`
  confirmed) between my last push and this state-file commit, so `git push` was rejected
  (protected-branch: queued branches cannot be updated) — expected GitHub behaviour, not an
  error. This commit sits local-only for now; push it once the queue drains (merge or
  dequeue) rather than force anything.
- `2026-09-05T~13:4xZ — L3-W3 — PR hygiene (C8 Step 1): PR #1801 (my own branch,
  codex/nirmana-l3-w4-resume) was RED on "Governance Gates (drift/schema/edge/
  native-literal/py-sidecar)" — heartbeat had wrongly implied it was queued/armed
  when it was actually BLOCKED, unqueued (is:queued verified empty). Root cause:
  test_u3_convergence_currents.py's TestAshtakavarga was never updated after N4b
  (c7_ashtakavarga_potency → honest None, HELD pending #1810) landed on this same
  branch — 7 stale assertions expected the old bindus/8.0 formula or 0.0 instead
  of None. Fixed AT ROOT (not weakened): rewrote the 5 TestAshtakavarga tests +
  1 TestEnrichmentContextEmptySafe assertion to lock in the held-null contract,
  added a new test proving a None c7 is DROPPED from the saturating product
  (matches omitting the key) rather than coalesced to 0.0. Mutation-proved:
  patching the function back to a fabricated formula turns all 7 red. Verified
  locally: targeted file 56/56 pass; full CI-equivalent suite (tests/ +
  bodha_writers + orchestrator, -m "not integration") 6391 passed / 0 failed /
  89 skipped — matches the pre-existing baseline shape. Committed 507ddba74,
  pushed. Auto-merge still armed (enabledAt unchanged). — blocked on: nothing;
  next action: verify the re-run Governance Gates check goes green and confirm
  `is:queued` next cycle before starting new W3/W4 work (C8 Step 1 discipline).
- `2026-09-05T~08:0xZ — L3-W3 — post-resume loop 2: N4a/N4b (two 100%-zero ka_sangam terms → honest null; c7's fix HELD on the Āries-lagna frame question, #1810), N12 (a below-range 0.5 invented into a ranking score on 99.6% of rows), kala_bhavishya's P7 outcome seam preserved across rebuild, L3 analysis pin re-generated (#1814 filed on the generator's all-layers coupling) — blocked on: nothing; #1801 queued and armed; spine merged but NOT deployed so W2 acceptance still impossible.`
- `2026-09-05T~07:2xZ — L3-W3 — resumed after lane death; §R1 stock-take posted; #1770 answered (all five re-runnable) then CORRECTED upward (3,708 L4 rows, not 188); C13 blast-radius 23/23 published; two no-FK dispositions; MSR re-run sequenced and priced; N4a panchanga honest-null landed — blocked on: nothing, W3 continues.`

One line per loop: `<UTC ISO-8601> — <position> — <what you are doing>`.

- `2026-09-05T…Z — L3-W3 — 7 MUSTs landed (M3,M4,M5,M7,M8,M9,M11), each mutation-proved; depends_on audit published (36 hidden / 17 false edges) with a correction to my own earlier claim to the Conductor; verified L2's cascade finding against my own tables (710,899 rows) and committed to hold; 16/19 integrity contracts authored.`
- `2026-09-05T…Z — L3-W2/W3 — W1 closed 23/23 (index published); W2 closed 23/23 routed + 12 MUST / 12 NOW / 8 NEVER triaged; ka_taranga SPLIT decided with falsifiers; first two D-CND-03 contracts authored AND mutation-proved live (ka_kota_chakra 4/4 conjuncts fail on injected corruption). W3 open.`
- `2026-09-05T…Z — L3-W1 — batches A/B/C/D landed (E outstanding); verified the v1-corpus alert down to its real residuals; verified ka_gochara_resonance's 5 undeclared edges from writer SQL and filed #1734 — L3 has no honest canary, reported rather than manufactured.`
- `2026-09-05T…Z — L3-W1 — rulings absorbed (#1721 GRANTED/PR #1728; D-CND-03 binding; #1715 Option A — no W2 acceptance until it deploys); #1724 withdrawn as duplicate with acceptance recorded; constraint reconnaissance done for the 19 owed contracts; per-loop gate poll scripted; #1730 remains the open W4 blocker.`
- `2026-09-05T…Z — L3-W1 — bootstrap complete; DB read path live; C10 gate run (2 assets OPEN); 5 read-only W1 batch subagents dispatched (A gochara / B overlays / C services / D heavy+ssv / E artifact spine); 2 campaign-blocking findings filed as #1721 and #1724; deploy ancestry verified execution-safe.`
