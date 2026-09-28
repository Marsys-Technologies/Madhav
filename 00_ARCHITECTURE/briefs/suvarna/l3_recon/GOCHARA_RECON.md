# Gochara family: reconciliation for the Suvarṇa campaign

- **Author:** read-only research session, 2026-09-28, finished about 23:40 IST.
- **Mode:** read only. Nothing was edited, committed, pushed, built or written to the database. The live worktree `/Users/Dev/madhav-l3/gochara-wp0-7` was read with `git`, `ls` and `grep` only.
- **Database access:** production reads went through `pgenv.sh`, which uses the proxy on port 5433, with `default_transaction_read_only=on` and `timeout 120`.
- **Evidence labels:**
  - `[S]` source file:line
  - `[G]` git commit or ref
  - `[L]` live read-only query, 2026-09-28 17:57–18:06 UTC
  - `[D]` governance document
  - `[I]` my inference
  - `[U]` unknown

> **Disclosure: a timing coincidence during this session.** The live lane's production step06b windows write for the canonical chart failed at 23:27:40 IST with `server closed the connection unexpectedly` (`.run/wp10_tranche2/prod_link3_step06b_runreport_482012f1.stderr`). My first read-only query ran 6 seconds later, at 17:57:46 UTC (23:27:46 IST). The two runs used different connection paths: the lane used its own `cloud-sql-proxy` on port 55440 (pid 29800), and mine used port 5433. A read-only SELECT on a separate connection cannot close another session's connection, so I believe this is a coincidence. I am recording it so the lane can rule it out. As of 18:06 UTC there are zero `'4.0'` windows in production and authority is still `'3.0'` on both charts `[L]`. The write rolled back, or never committed.

---

## 0. Summary

The Gochara family currently serves a century-long `'3.0'` projection built by a century writer that is now **held**. The **only active elevation work** is the live WP0–WP7(+WP10) lane, PR #2731, which is **open, unmerged and CONFLICTING**.

That lane has already changed production:

- guard triggers;
- migrations 1080–1084, 1087, 1091 and 1150;
- a registry re-pin;
- a `'4.0'` candidate contact ledger of 138,837 contacts per chart, plus coverage rows and a manifest.

Its next step is **Link 3**: write the `'4.0'` windows, run the flip gates, flip authority on chart 482012f1, soak for 24 hours, then flip chart 1c826d5a, then run N-11. That step started tonight and hit a connection loss on the first write.

Four things will be true even after Link 3 succeeds:

1. The `'4.0'` product exists only as **hand-run cutover scripts**. The registered orchestrator writer `ka_gochara.py` is unchanged and still writes `kala_gochara_windows_v2` `'2.0'`.
2. `'4.0'` covers **2020–2030 only**, while `'3.0'` covered 1984–2084.
3. The serving code that understands `'4.0'` (P-1/P-2/P-4) exists **only on the unmerged branch**.
4. Several documented enrichments are still flags, interims or unbuilt:
   - resonance corrections R-1..R-6;
   - overlays extended to the requested horizon;
   - the M-7 bindu matrix;
   - the Moon channel;
   - time-varying permission.

---

## 1. Inventory

### 1.1 Assets (registry, live `[L]`: `asset_registry` query, 2026-09-28)

| asset_id | active | target_table | count_sql (live) | depends_on (live) | What it computes |
|---|---|---|---|---|---|
| `bg_gochara_arcs` (L0) | t | `bg_gochara_arcs` | `COUNT(*)` (33,933) | `{bg_ephemeris}` | Monotone longitude arcs for 9 bodies, used as an index for transit search. **Built on tropical longitude** (F-07; plan v2.1 §5.1 `[D]`). The kernel deliberately does not consume it. |
| `bg_gochara_citation_resolution` (L0) | t | same | `COUNT(*)` (14) | `{bg_texts}` | Maps gochara rule citations to corpus chunks. Migration 631 is on main `[G]`. |
| `ka_gochara_resonance` | t | `gochara_resonance_map` | per chart | `{bg_transit_rules}` | For each of 27 event classes, the natal "targets" a transit can activate: karaka, dasha lord, lord, bhava, mechanism_node, arudha, yoga_constituent and sensitive_degree. Each has a weight and a citation. 765 rows on the canonical chart. |
| `ka_gochara` | t | `kala_gochara_windows` | `…kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'` | `{bg_ephemeris, bg_transit_rules, ka_gochara_resonance, ka_vedha_gochara, ka_moorti_nirnaya, ga_positions, ga_dashas, ga_yoga}` | Designated owner of the served transit windows (N-5). **Its registered writer still writes `_v2` `'2.0'`** (§4 D-1). |
| `ka_gochara_v3_century_materialize` | **f** | `kala_gochara_windows_v2` | `…_v2 … LIKE 'g3_%'` | resonance, vedha, moorti, kota, tithi, bg_sky_calendar | The λ_v3 century engine. It produced served `'3.0'` (1984–2084) plus `g3_utkarsha` staging. It is held, with `is_active=false` set 2026-09-24 (E-014). |
| `ka_gochara_sweep` | **f** (RETIRED) | `kala_gochara_windows` | `… generation='v1'` | `{ka_gochara_resonance}` | The v1 daily sweep. It is protected history, `superseded_by=ka_gochara`, `RETAINED_AS_CAPITAL`. It has no registered writer (`asset_throughput.last_error = 'no writer registered'`) `[L]`. |
| `ka_vedha_gochara` | t | `kala_vedha_gochara` | per chart | ga_positions, bg_ephemeris, bg_transit_rules, sarvatobhadra grid, malefic scale, latta | Vedha (obstruction) intervals: house vedha, laṭṭā and sarvatobhadra. These feed `quality_gates`. |
| `ka_moorti_nirnaya` | t | `kala_moorti_nirnaya` | per chart | ga_positions, bg_ephemeris, bg_transit_rules | Mūrti (gold/silver/copper/iron) grade of each ingress, from the Moon's nakṣatra offset at ingress. |
| `ka_kota_chakra` | t | `kala_kota_chakra` | per chart | ga_positions, bg_ephemeris, bg_kota_chakra_rings | Kota-chakra ring placements. **Proposed-use only**: the w25 mechanism is not wired, and the corpus has 0 rows (N-8, M-4; plan §5.4 `[D]`). |
| (sibling, not family) `ka_tithi_pravesha` | — | — | — | — | It is a declared century input, but the edge is "retired as an edge" under N-8. That retirement has not been applied: the century row still lists it `[L]`. |

### 1.2 Tables and other objects (`[L]` counts)

| Object | Canonical 482012f1 | Chart 1c826d5a | Other | Notes |
|---|---|---|---|---|
| `kala_gochara_windows` `v1` | 16,297 | 19,323 | cb73cd3d 2,667 | Protected. The guard triggers `trg_kgw_generation_guard_row` / `_truncate` are live, and `build_protected_assets` holds 3 rows `{v1}` `[L]`. |
| `kala_gochara_windows` `'3.0'` | 914 | 916 | — | **The served product today.** Authority `'3.0'` on both charts, flipped 2026-08-11 `[L]`. |
| `kala_gochara_windows` `'4.0'` | **0** | **0** | — | Link 3's write has not landed. |
| `kala_gochara_windows_v2` `'2.0'` | 87 | 76 | — | Written by `ka_gochara.py`. Unserved; its disposition is N-11. |
| `kala_gochara_windows_v2` `g3_utkarsha` | 914 | 916 | — | Century staging / calibration corpus. |
| `kala_gochara_contacts` `'4.0'` | 138,837 (138,697 citation-NULL) | 138,836 (138,696 NULL) | — | New contact ledger (migration 1081 + 1087). Candidate status. |
| `kala_gochara_coverage` `'4.0'` | 48 | 48 | — | `requested_horizon` = [2020-01-01, 2030-01-01) on every row. `unavailable_inputs={}`. |
| `kala_gochara_publication` | manifest d54d899b, `candidate` | 4dc6c74c, `candidate` | — | `row_counts={}`. Not published. |
| `kala_gochara_convention` | 1 row | — | — | mean node, FLG_SIDEREAL, `probe_retflag=258`, **`se1_checksums` empty** (see §4 D-10). |
| `kala_gochara_authority` | `'3.0'` | `'3.0'` | — | Table from migration 527. |
| `gochara_resonance_map` | 765 (built 2026-09-07) | 753 (2026-09-10) | cb73 77 | All rows carry `target_resolution_state='resolved'` (the column default). |
| `kala_vedha_gochara` | 171 | 173 | — | Rebuilt 2026-09-27 (Link 1). Spans 2026-07-29 → 2027-11-01 only. |
| `kala_moorti_nirnaya` | 74 | 74 | — | Same span. `upstream_fingerprint` is populated. |
| `kala_kota_chakra` | 585 | 585 | — | — |
| Services | — | — | — | See below. |

The services behind these tables:

- **On main:**
  - `services/gochara_v3/`: the engine, `resolution_hierarchy.py`, `context.py`, `interval_solver.py` and the mechanism modules w21–w30.
  - `services/gochara_intensity/`: promise, permission and enrichment.
  - `services/gochara_grammar/`: primitives, `SPECIAL_DRISHTI_DEG`.
  - `services/ka_gochara/service.py`: `GocharaTransitService`, compute-only, used by Saṅgam, `kala_trigger` and `ph_muhurta`.
  - `pipeline/transit_search.py`.
  - `services/w2g/`: the old `'2.0'` path.
- **On the branch only:**
  - `services/gochara_kernel/` (13 modules: arcs, contacts, episodes, ids, ledger, overlays, peaks, lifecycle, legacy_semantics, …) `[G]` (branch diff).
  - `scripts/kala_gochara_cutover/step00–step10`, which are the only producer of `'4.0'`.

### 1.3 Consumers

| Consumer | Reads | Where (main) | Declared in registry? |
|---|---|---|---|
| MCP `gochara_forecast_get`, `gochara_activation_get`, `gochara_election_avoidance_get` | `kala_gochara_windows` via the authority filter | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts`. Main has branches only for `'3.0'`/`g3_*`, `:574-598`, and `COALESCE(…,'v1')` at `:641` `[S]`. | n/a |
| `kala_windows_get` | temporal activation, **not** gochara windows. It is only cross-pointed from the gochara tools (`KALA_WINDOWS_CROSS_POINTER_INSTRUMENT`, `register_gochara_windows.ts:1123`) | `register_p1_aliases.ts:1082` `[S]` | n/a |
| `reading_checklist.ts` `fetchGocharaSweep` → D8 assess-domain, D9 judgment | authority-filtered windows | `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` `[S]` | n/a |
| `kala_now_get` | vedha and moorti | `platform-mcp/src/tools/kala_views/now.ts:2142` `[S]` | n/a |
| `query_vedha_gochara.ts`, `query_moorti_nirnaya.ts` | overlays | `platform/src/lib/retrieval/registry/layers/L3_kala/` `[S]`. Nikaṣa: `density_contract` is not declared. | n/a |
| `ka_kshetra` | resonance + vedha (declared); **`kala_gochara_windows` via the authority filter (undeclared: 1084 held out the `ka_kshetra → ka_gochara` edge)** | `services/ka_kshetra/stage4_field.py`, `writer.py`, `hazard.py` `[S]` | partial |
| `ka_sangam` | `ka_gochara` (service `find_aspects`), `kala_vedha_gochara` | `writers/ka_sangam.py:1037-1060`, `services/ka_sangam/engine.py` `[S]` | yes (V-1 edge applied via 1084) |
| `ph_muhurta` | `ka_gochara` (compute-only service) | `writers/ph_muhurta.py:16` `[S]` | yes |
| `kala_trigger`, `scripts/kala_admission/currents.py` | `GocharaTransitService.find_aspects` (duck-typed) | `services/kala_trigger/trigger.py:87,96,150,199` (plan F-25 `[D]`) | n/a |
| Admin / validation scripts | v1 / `_v2` / `'3.0'` corpora | w41–w45, mr20/23/47, w2g_validations (plan §6.1 WP0-2..5 `[D]`) | n/a |
| L5 prospective ledger | `contact_id` (migration 1083 applied; code on branch) | `platform/src/lib/lel/prospective_ledger.ts` | n/a |

---

## 2. What was done, and where it stands

### 2.1 Workstreams and branches

| Branch / PR | Content | State |
|---|---|---|
| `gochara3/*` (w03, w51, w52, w53, w61, i6a-role) | GOCHARA-UTKARṢA (Aug 2026). Built the v3 century engine, cut over to `'3.0'`, retired the sweep (#1192, 2026-08-10) | Merged. The remaining "ahead" commits are squash residue `[G]`. |
| `codex/l0-gochara-citation-integrity` (worktree `/Users/Dev/.codex/worktrees/l0-gochara-citation-integrity`, clean) | Migration 631 citation chunk repair | Content already on main. Only a CI-file diff remains `[G]`. |
| `codex/nirmana-l3-w3-m12-gochara-orphans`, `fix/nirmana-l0-bg-gochara-arcs-floor`, `l3-2527-…`, `l3-2542-…`, `l1-1018-…` | Nirmāṇa fixes: migrations 672, 694 and 1018, resonance ORDER BY, plan_substeps | Merged (squash residue) `[G]`. |
| `l3/kala-elevation-readiness` (#2711/#2714/#2721 merged) | Blueprint, template v2.0, E4 seed-reseed hazard finding (7374d8f71) | Docs merged. The tip has 136 unmerged commits `[G]`. |
| `l3/gochara-elevation` (**PR #2723 merged 2026-09-24**) | Brief v1.0–1.2, plan v0.2 → v2.1 (native-ratified 2026-09-23), ruling sheet v1.0, Kimi K3 review | On main `[G]`. |
| `l3/kala-layer-briefs` | Layer briefs and `kala_elevation_ledger.jsonl` (gochara entries: "blocked", "HOLD", ledger gap) | Unmerged `[G]`. |
| **`l3/gochara-autonomous-wp0-7` (PR #2731, OPEN, `mergeable=CONFLICTING`)** | The live lane: 188 commits, 251 files, +51,246 / −577 vs main `[G]` | See 2.2. |
| PR #2715 `l3/kala-p1-1-b1-clear-guard` | Clear-route B1 guard. Cherry-picked into #2731 at step 0 | Open `[G]`. |
| PR #2734 `fix/century-seed-is-active-false` | Sets the century `is_active=false` in the seed | **Open** `[G]`. |
| PR #2751 `governance/nirmana-supersession` | Records Nirmāṇa superseded by Nikaṣa | Open `[G]`. |
| `strategy/suvarna-plan` (6eece54fa) | The Suvarṇa plan v1.0 draft. It already names this lane and R240 (§7, lines 246, 303, 537–540) | Draft `[G]`. |

### 2.2 The live lane: goal, work packages, delivery

- **Goal (plan v2.1 §0, `[D]`):** stop throwing contacts away. A deterministic kernel should solve each (body × target × relation) contact once per chart on Swiss sidereal arcs. Those contacts are persisted as a ledger (`kala_gochara_contacts`) with a coverage manifest. The λ_v3 score is then served as a projection over the ledger, under a new immutable generation `'4.0'` owned by `ka_gochara`. Nothing is retired.
- **Governance:**
  - Plan v2.1/2.2 (NATIVE_RATIFIED 2026-09-23).
  - Ruling sheet v1.0 (N-1..N-14, M-1..M-8 direction) and v2.0 (M-1..M-8 parameters, N-15..N-22, A-1..A-3).
  - Native rulings of 2026-09-24.
  - Standing mandate of 2026-09-26, with the ADHIKĀRIN surrogate register ADK-0001..0026 and the PRAMĀṆIN verifier.

| WP | Delivered (commit) | Merged? | In production? |
|---|---|---|---|
| WP0 findings / consumer re-enumeration | b262cbf6a; E-004 → plan v2.2 | branch | n/a |
| WP1 contracts + golden cases | 35a419f5d (`WP1_CONTRACTS.md`, 810 lines) | branch | n/a |
| WP2 synthetic fixtures | 46b9529cc | branch | n/a |
| WP3a kernel | f775c2d6e (13/13, FLG_SIDEREAL); ADK-0019 narrow-window refine patch f1ee17c81 | branch | Used to build the `'4.0'` contacts |
| WP3b span-aware legacy algebra | 25aeab607 | branch | n/a |
| WP3c resonance R-1..R-6 | bd65433f8 | branch | **Inert.** No resonance rebuild has run; production still has 154 negative-result `sensitive_degree` targets and 54 dangling yoga targets `[L]`. |
| WP4 decomposed comparison | df8b05576 | branch | n/a |
| WP5 honesty fixes H-1a, H-2..H-6 | 59bebe7dc (E-006 resolved) | branch | Through `'4.0'` only |
| WP6 ledger / coverage / publication | 25aeab607 + migrations 1080/1081/1087 | branch | Schema applied 2026-09-24; rows written 2026-09-28 |
| WP7 packets C-1, P-1..P-4, K-1/V-1, S-1/S-2, T-1 | 7bd66b450, d668e3e87, 6d7c40df3, 273730192, 1019b1f12, f256b24d3, e6a7a50fd, 40441b7a4 | branch only | **Serving code (P-1/P-2/P-4) is NOT deployed.** Registry edges (1084) are applied. |
| WP8 M-1 orb battery, M-2 retrograde ablation, factor deltas | 597b29434, 0481d4565, 73a7cd1a3 | branch | M-1 candidate-1 (`linear_no_box`, 5.0°) ratified |
| WP9 overlays on the kernel, stamps, M-8 vedha exceptions | a5ac0caad, 41e4843cd, 0c876fbe4, 7cca66fa2; migration 1082 | branch | Stamp columns applied. **Production overlays still use the ±460-day horizon** `[L]`. |
| Remainder flags (N-13/N-22, N-14, N-15, N-17, M-1, M-3, M-6) | 6a1c23195 … 98df8bc40 | branch | Active only inside the `'4.0'` candidate flags |
| WP10 tranche 1 (steps 0, 1, 3, 4, 5) | cacc72440, e8cbce231, 8a7f5e692, 4670bebab / 5ee6280bd, 3fcf6a586 | branch | **Applied 2026-09-24:** guard trigger, century `is_active=false`, migrations 1080–1084, 1087, 1091. **Step 2 restore drill NOT_RUN.** |
| WP10 tranche 2, Link 1 (overlay fingerprint rebuild) | `run_wp10_overlay_rebuild.py` | branch | Done 2026-09-27 15:38 UTC `[L]` |
| Link 2 (candidate contacts) | ADK-0019..0023; production verified at 51424f9d5 | branch | **Done 2026-09-28:** 138,837 / 138,836 contacts, 48+48 coverage rows, candidate manifests |
| Link 3 conditioning (a)–(d) | e400de983, 058b2ab3b, 412d99d0c; K3 BLOCK c8169f51a → fixes 419aca944 / 9ef81897c; E-020 → native overrule (ADK-0026) → 3c7bf6947, 1fc8fd2d7; migration 1150 applied 2026-09-28 16:20 UTC (`_migrations_applied` id 885) `[L]`; K3 re-review "NO BLOCKING" ae0743136 | branch | 1150 applied |
| Link 3 execution (steps 6b-prod, 7, 8, 9, 10) | ADK-0023 §3 pre-authorizes auto-execution once (a)–(d) are verified | — | **Started 23:27 IST, first write failed** (connection lost); 0 `'4.0'` windows `[L]` |

**What remains in the lane's own plan:**

1. Production step06b for both charts.
2. Step-7 gates. Their TS sub-gates (provenance P-1a, disclosure) are `NOT_RUN` by design (`step07_flip_gates.py:6-31,70-112` `[S]`).
3. Step-8 flip on 482012f1.
4. A 24-hour soak with the abort triggers written down beforehand.
5. Chart 1c826d5a under the birth-epoch gate.
6. Step 10: N-11 disposition of `_v2 '2.0'`.
7. The 12.10c merge-hygiene runbook (documented, not executed).
8. PR #2731 merge. It is conflicting.
9. Carried non-blocking items: legacy_semantics docstring R1; conjunct (i) vacuity; Venus 35 µs rows; the Kṣetra dangling-edge note.
10. The step-2 restore drill.
11. Rotation of four secrets echoed to a transcript (REMAINDER_FINAL_REPORT §7.B incident).

**Current next step:** re-run the production step06b for 482012f1 after the connection loss, then run step 7.

### 2.3 Timeline

| Date | Event | Source |
|---|---|---|
| 2026-06-10 / 06-21 | `TRANSIT_GOCHARA_SUBSYSTEM_MASTER_PLAN_v1_0` (on-demand service design); `CLAUDECODE_BRIEF_L3_KA_GOCHARA_v1_0` | main `[D]` |
| 2026-07-27 | v1 sweep builds (cb73cd3d) | `asset_throughput` `[L]` |
| 2026-08-10 | UTKARṢA W6.4: `v2_materialize` → `ka_gochara`, sweep RETIRED (#1192) | `[G]` 63435580a |
| 2026-08-11 | Authority flipped to `'3.0'` on both charts (MR-24) | `kala_gochara_authority` `[L]` |
| 2026-08-21 | Century "BUILD-PROTECTED" error; standing order: no gochara re-materialization without fresh authorization | `[L]`, plan §12 `[D]` |
| 2026-08-23 | Migration 588 drops the guard triggers (F-04) | plan F-04 `[D]` |
| 2026-09-05/06 | Nirmāṇa: orphans 672, arcs floor 694 | `[G]` |
| 2026-09-07 / 09-10 | Resonance built (765 / 753); last `ka_gochara` `'2.0'` build; 1018 digest spec; #2546 | `[L]`, `[G]` |
| 2026-09-20 | DP-SD-021: the L3 data plane moves to Claude Code | CURRENT_STATE v6.79 `[D]` |
| 2026-09-22 | Brief v1.0–1.2; plan v1.0 ratified (D-1..D-3) | `[D]` |
| 2026-09-23 | Plan v2.1 ratified (ruling sheet v1.0); lane starts (793a7039f); WP0–WP7 land; ruling sheet v2.0 ratified; L0 repair 1075–1079 applied | `[G]`, `[L]` |
| 2026-09-24 | Remainder campaign; tranche 1 GREEN; century `is_active=false`; 1080–1084, 1087, 1091 applied; tranche 2 halted at step 6 (E-018); native HOLD at 17:51; PR #2723 merged | `[G]`, `[L]` |
| 2026-09-25 | Native Decision 11: domain correctness is not a data-plane obligation | STANDING_MANDATE `[D]` |
| 2026-09-26 | Standing mandate; ADK-0010 releases branch-local work | `[D]` |
| 2026-09-27 | Step-6 driver, `'4.0'` projection writer (E-012), step06a; ledger backfill (E-019); Link 1 overlay rebuild | `[G]`, `[L]` |
| 2026-09-28 early | Link 2 production contacts; ADK-0019..0023 | `[G]`, `[L]` |
| 2026-09-28 day | K3 BLOCK (F1 kakṣyā relation key, F2 reversal orphans); fixes; E-020 conjunct-(e) RED; ADK-0025 **overruled by the native** (ADK-0026: fix data, not detector); migration 1150 applied 16:20 UTC; K3 re-review clear 21:58 IST | `[G]`, `[L]` |
| 2026-09-28 23:27 IST | Production step06b (482012f1) fails with a connection loss | `.run` stderr |

---

## 3. Current production state

- **Row counts.** See §1.2. The known figure of "17,211 vs 1,001" on the canonical chart is `kala_gochara_windows` (v1 16,297 + `'3.0'` 914) against `_v2` (`'2.0'` 87 + `g3_utkarsha` 914) `[L]`. It still holds.
- **Last builds (`asset_throughput`) `[L]`:**
  - `ka_gochara` is `lit`: 87 rows at 2026-09-10 04:16 on 482012f1, 76 rows on 1c826d5a. That records the `'2.0'` write. The live `count_sql` now reads `'4.0'` = 0, so the cockpit shows 0. Nikaṣa records this as `ka_gochara-Count.floor` live=0 against floor 83.
  - Century: `error` (BUILD-PROTECTED, 2026-08-21) on 482012f1 and `stale` on 1c826d5a.
  - Resonance: `lit`, built 2026-09-07 and 2026-09-10.
  - Vedha and moorti: `lit` 2026-09-07 on the canonical chart and `dormant` on 1c826d5a. The rows were re-written on 2026-09-27 by Link 1 **outside the orchestrator**, so the build records disagree with the live counts (vedha 177 recorded vs 171 live; moorti 71 vs 74; Nikaṣa `*-Build.completion`).
  - Sweep: `error`, no writer registered.
  - The family has 59 `build_run_assets` rows for `ka_gochara`; the latest is 2026-09-10.
- **The v1/v2 split** is partly intentional and partly residue.
  - `v1` and `'3.0'` in `kala_gochara_windows` are intentional: protected history and the served product.
  - `g3_utkarsha` in `_v2` is intentional century staging.
  - `'2.0'` in `_v2` is residue. It is unserved and read only by `w2g_equivalence_report.py` (F-16), and its disposition is pending N-11 at step 10.
  - The **registry mismatch R240** was closed in Nikaṣa as "discharged by R20: stays PARTIAL with explicit reason" (`NIKASHA_CHANGE_REGISTER_v2_0.md:450`). Since 1091 it has become a three-way disagreement; see §4 D-2.
- **Migration 1150** changed only `asset_registry.integrity_check_sql` for `ka_gochara`: conjunct (e) now compares dates in UTC (`1150_…sql:52,202` `[S]`). It does not touch the writer/table mismatch.
- **Is a rebuild possible now?** Not safely from main. `[S]` + `[L]` + `[I]`:
  - **`ka_gochara` via the orchestrator** would run main's `ka_gochara.py`. That writer writes `_v2 '2.0'` with a `date.today()` horizon (`ka_gochara.py:120,268`), is identical on the branch, and is not a `'4.0'` producer. The count stays 0, so a "Build" cannot produce the served product for any chart.
  - **Resonance rebuilt from main** would bump `computed_at` without R-1..R-6. That changes an input the `'4.0'` candidate pinned in its generation vector.
  - **Vedha/moorti rebuilt from main** would write NULL stamp columns. Main's writers have 0 references to `source_qualification` / `upstream_fingerprint` against 10 on the branch. That would turn the §12.9 freshness gate RED again, and step06 exits 7.
  - **The century** is blocked by `is_active=false` and by the guard trigger.
  - **`'4.0'`** can be (re)built only by the lane's hand-run cutover chain under native authorization. The 2026-08-21 standing order is still cited as in force (plan §12).

---

## 4. Open problems

### 4.1 Defects and hazards found or re-verified in this reconciliation

| id | Problem | Evidence | Severity |
|---|---|---|---|
| D-1 | **No orchestrator-native `'4.0'` writer.** `@register('ka_gochara')` still writes `_v2 '2.0'`. `'4.0'` is produced only by `scripts/kala_gochara_cutover/step06*/06a/06b` run by hand. This violates the FROZEN-contract premise that "click Build" rebuilds any chart. | `git diff` of `ka_gochara.py` main vs branch = identical `[G]`; `ka_gochara.py:120` `[S]` | High: blocks the product for new charts and blocks idempotent rebuilds |
| D-2 | **Registry, seed and writer disagree three ways.** Production (1091): `kala_gochara_windows` / `'4.0'`, 8 dependencies. Main seed: `kala_gochara_windows` / **`'3.0'`**, deps `[bg_gochara_arcs, ka_gochara_resonance]`, **century `is_active: true`**. Branch seed: `_v2` / `'2.0'`. Writer: `_v2`. A hand-run re-seed would revert 1091 and re-arm the century. The century half is mitigated only by the trigger. | `[L]` registry; main seed lines 2119–2140, 2198–2230 `[G]`; branch seed 2150–2158 `[G]`; E4 commit 7374d8f71 `[G]` | High (R240 successor) |
| D-3 | **Serving code for `'4.0'` is not deployed.** Main's `register_gochara_windows.ts` has no manifest branch, and `'4.0'` falls to the v1 provenance branch (the plan's own risk: "certain without P-1 / high"). Link 3's condition (c) was verified against branch code. The step-7 TS gates are `NOT_RUN`. The lane's documents contain no deploy-before-flip precondition that I could find. | main `:574-598,641,966-977` vs branch `:566-701` `[S]`; `step07_flip_gates.py:70-112` `[S]`; PR #2731 CONFLICTING `[G]` | **High if the flip precedes the merge and deploy** |
| D-4 | **The `'4.0'` horizon is 2020-01-01 → 2030-01-01. `'3.0'` serves 1984–2084.** After the flip, windows before 2020 and after 2029 (including the plan's own marriage-2013 value specimen) are not served from `'4.0'`. The coverage manifest records the requested horizon, but that only reaches users through the undeployed P-1. The plan says "no … narrower horizon is accepted as a speedup". I found no document in the lane that discloses the flip as a served-horizon narrowing. | `step06_enumerate_episodes.py:952-953`, `step06b…:820-821` defaults `[S]`; `kala_gochara_publication.horizon` `[L]`; plan §4.5 `[D]` | High (served-coverage regression) `[I]` on intent |
| D-5 | **The `'4.0'` λ loses time-variation.** The delta report shows PROMISE = 1.000000 for all 27 classes (a noisy-OR over 14–40 weights saturates), tārā = 1.0 "skip" (Moon channel not wired), w30 = 1.0 (N-14), and permission a **static per-class constant** (step06a "static per-class collapse of the time-varying DR-14 plurality", disclosed). Only activity and `quality_gates` vary in time, and `quality_gates` has vedha data for about 15 months of the 10-year horizon. Mean raw λ rises for 25 of 27 classes (up to +0.42). | `.run/wp10_tranche2/link2_delta_report_482012f1.md` per-class table; `step06a_class_context.py:9-27,196` `[S]` | Medium–High (algorithmic depth) `[I]` |
| D-6 | **Resonance corrections are inert in production.** 154 negative-result `sensitive_degree` targets (`not_gandanta` 44, `not_fired` 44, `not_pushkara` 40, `none` 26); `ardhachandra` and `chatra` (27 rows each) have 0 fired rows; all 765 rows carry `target_resolution_state='resolved'` via the column default. That is a signal with no detector behind it (§N.8). | `[L]` queries on `gochara_resonance_map`, `ga_yoga_firings` | Medium |
| D-7 | **Overlays are still ±460 days in production (F-11).** Vedha and moorti span 2026-07-29 → 2027-11-01. WP9's requested-horizon capability is branch-only and was not used by Link 1 (`HORIZON_BACK_DAYS=60`, `FORWARD=400`, `ka_vedha_gochara/writer.py:94-95`). The `'4.0'` rows outside that span are labelled `quality_gates:no_overlay_rows(F-11)`. | `[L]`; `step06b…:519-521` `[S]` | Medium |
| D-8 | **Main's overlay writers erase stamps.** Any orchestrator rebuild of vedha, moorti or resonance from main code would null the stamps and fingerprints and re-break §12.9. | grep counts main 0 / branch 10 / 10 / 36 `[G]` | Medium (latent) |
| D-9 | **Applied migrations exist only on an unmerged branch.** 1080–1084, 1087, 1091 and 1150 are applied in production (`_migrations_applied` ids 872–878, 885), but main has none of these files. Branch files 1071/1072 collide with Saṅgam's 1071/1072 (kala ledger 2026-09-25 entry). | `[L]`; `git ls-tree origin/main` `[G]` | Medium (merge hygiene) |
| D-10 | **The convention row has no checksums.** `kala_gochara_convention.se1_checksums` is empty, although the plan's F-14 gate requires "records backend + three checksums". `probe_retflag=258` is recorded. | `[L]`; plan §10 `[D]` | Low |
| D-11 | **Resonance hidden edges (E-013).** `ka_gochara_resonance` reads `ga_dashas` and `ga_yoga`; registry `depends_on` is `{bg_transit_rules}` only. | `[L]`; ESCALATIONS E-013 `[D]` | Low–Medium |
| D-12 | **Kṣetra and Tithi edges.** `ka_kshetra` reads `'3.0'`/`'4.0'` windows with no `→ka_gochara` edge (held out of 1084). Kṣetra is in `error` on the canonical chart. The century row still lists `ka_tithi_pravesha` (the N-8 edge retirement was not applied). | `[L]` | Medium |
| D-13 | **Nothing verifies that windows cite real contacts.** Conjunct (i) is vacuous: `active_sentences` holds bare `contact_id` strings, and no detector checks that they resolve in the ledger. | K3 re-review obs. 2; step09 checklist `:57-108` `[D]` | Low |

### 4.2 Open register rows and Nikaṣa gaps

Latest row per `gap_id`, all `OPEN` (`/Users/Dev/madhav-nikasha/00_ARCHITECTURE/control/asset_gaps.jsonl`, 2026-09-26/27):

- **`ka_gochara`:**
  - Idem.pattern: "DELETE … deletes `_v2`, not its own table".
  - Build.completion: live 0 vs floor 83.
  - Earn.build_record and Cost.baseline: NO_DETECTOR, pending migration 1094.
  - Count.floor: −83.
  - Complete.depth: `threshold_lambda`, `threshold_percentile`, `implied_density` and `base_rate_cited` are never populated across 40,117 rows.
  - Dens.served: `call_service_wrappers.ts`, no `density_contract`.
  - Build.history: 2 errors, 1 abort; DEP-ASSERT on resonance receipt.
  - Carr.detector.
- **`ka_gochara_resonance`:** Earn, Cost, Complete.depth (`target_qualifier` never populated), Build.history (4 aborts), Carr.
- **`ka_vedha_gochara`:** Build.completion (177 vs 171), Earn, Cost, Count.floor (171 vs 176), Complete.depth (`grid_school_tag` never populated), Dens.served, Build.history (DEP-ASSERT on `bg_sarvatobhadra_grid`), Carr.
- **`ka_moorti_nirnaya`:** Build.completion (71 vs 74), Earn, Cost, Dens.served, Build.history (KeyError 2026-08-08), Carr.
- **`ka_kota_chakra`:** Earn, Cost, Count.floor, Dens.served, Build.history, Carr.
- **L0 assets:**
  - `bg_gochara_arcs`: Idem, Earn, Cost, Carr, Build.history (integrity_check False).
  - `bg_gochara_citation_resolution`: Build.completion (no build record), Earn, Cost, Carr.
- **Layer-wide `_layer_all-BT03`:** `ka_gochara_sweep` has "no writer registered".
- **`NIKASHA_CHANGE_REGISTER_v2_0.md`:** R240 is CLOSED only as a census-reporting fix (`:450`). R136 (shared table, multi-producer: ka_gochara and the sweep credited the same 40,117 rows) is OPEN (`:311`). R06 and R10 (multi-producer vocabulary) are OPEN.

### 4.3 Reviewer findings and design questions not closed

- **K3 re-review:** obs. 1–4 (legacy_semantics divergence note, conjunct (i), Venus zero-width rows, Kṣetra dangling edges after a reversal) `[D]`.
- **Doctrine and data outside the lane (plan §1.5):**
  - G-6: the L0 `ephemeris_daily` knots are TRUE node while the DAR receipt says MEAN. The kernel derives the mean node.
  - G-7: Saṅgam's symmetric aspect set (`ka_sangam/engine.py:464`).
  - G-10: L1 per-contributor BAV matrix. Migration 1086 was renamed to the L1 layer and is not applied `[L]`.
  - F-29: the node-dṛṣṭi citation.
  - Sade-Sati has essentially no primary-text anchor (N-15 demotes it to testimony).
  - M-3's Moon-from-Moon doctrine is `[U]`.
  - The Kota corpus has 0 rows.
- **Method parameters still evidence-gated (ruling sheet v2.0 §1):**
  - M-1 narrower orbs (candidate 2 at 1.0° is refused as unratified);
  - M-2 retrograde weight;
  - M-4 mechanism audit order (w21 → … → w30 retired);
  - M-6 Gulika/Māndi first, then bhāva-ārūḍhas;
  - M-7 bindu study.
- **Scope ruling to reconcile:** Native Decision 11 (2026-09-25) says "domain correctness is not a data-plane obligation" (`STANDING_MANDATE_2026-09-26.md:26-27`). Suvarṇa's "algorithm correctness" scope for this family needs to be read against it.

---

## 5. "Fully enriched" target

### 5.1 Documented intent (plan v2.1/2.2 + ruling sheet v2.0, `[D]`)

1. **Kernel geometry** (§4.2):
   - sidereal arcs built once for all charts, from noon-UT knots;
   - every root bracketed and then refined by Swiss bisection;
   - episodes carry `t_in / t_exact / t_out`, branch (direct, retrograde, station), orb, dwell, truncation at the horizon, and `near_station_unresolved` feeding `completeness_state`;
   - the Moon is solved on demand, with a coverage record.
2. **Contact ledger + coverage + publication** (§4.3–4.4, 4.7):
   - `contact_id` is stable under re-partitioning;
   - rows carry F04/F06/F12 qualification and a convention vector with backend checksums;
   - publications are immutable, with authority carrying `evidence_ref = manifest_id`.
3. **Projection** (§4.5): λ_v3 over interval sets (PROMISE, time-varying PERMISSION, activity per M-1, tārā, `quality_gates`); an era → month → day hierarchy; all peaks admitted, with trimming only at serve time (H-5 / N-17). **Horizon:** the design is century-scale ("qualified compact substrate"). "No cap, coarser grid or narrower horizon is a speedup."
4. **Target resolution** (§5.3):
   - 328 point targets and 229 interval targets;
   - 208 honest nulls, stored in `target_resolution_state`;
   - R-1..R-6 applied at resonance;
   - E-1 enrichment classes admitted by M-6 order.
5. **Overlays** (§5.4, A-1):
   - vedha and moorti computed on the kernel over the requested horizon;
   - mūrti graded at the true ingress instant;
   - M-8 exceptions and vipareeta vedha;
   - the three stamps (`source_qualification`, `precision_regime`, `corpus_verifiable`);
   - G-9 re-citation to Phaladīpikā Adh. XXVI (applied at L0, PR #2727).
6. **Method** (§1.4, ruling sheet v2.0):
   - M-1 linear-in-separation activity;
   - M-7 bindu-qualified kakṣyā and transit quality (gated on G-10);
   - N-13/N-22 unqualified kakṣyā contributes nothing;
   - N-14 no node dṛṣṭi;
   - N-15 Sade-Sati as testimony;
   - M-3 Moon excluded from century λ, with a separate Moon channel;
   - M-4 audited mechanism admission;
   - Kota after the w25 audit.
7. **Serving and ecosystem** (§6):
   - P-1 manifest-driven provenance and coverage, with the `'v1'` COALESCE removed;
   - P-2 checklist carries `contact_id` and completeness;
   - P-3 L5 `contact_id`;
   - P-4 contact-ledger read capability with `density_contract`;
   - S-1 `find_episodes` and S-2 directed contact events for Saṅgam;
   - T-1 for `kala_trigger`;
   - K-1 and V-1 registry edges;
   - C-1 Clear ops across the 3 relations.
8. **Registry** (§6.3):
   - `count_sql` = `'4.0'` on windows;
   - integrity conjuncts (a)–(k);
   - digest spec for `'4.0'`;
   - seed corrected (N-9 ii);
   - `target_floor` set after WP10.
9. **Lifecycle:** century stays held → INVESTIGATE_CONSOLIDATION; retirement only under R1's gates and a Strategy denominator amendment (G-1); N-11 disposes of `'2.0'`.

### 5.2 My inference, beyond the documents

- "Fully enriched" also requires an orchestrator-native `ka_gochara` writer that produces `'4.x'` by itself (D-1), because the FROZEN contract (CLAUDE.md §N.2) makes "click Build" the product path. The plan names the writer as `ka_gochara.py` (`may_touch`) but delivered scripts instead.
- It also requires `'4.x'` coverage at least equal to what `'3.0'` served (1984–2084), or an explicit native ruling that accepts a narrower served horizon (D-4).

---

## 6. Gap and effort

Effort is given in focused agent-days, meaning one lane working with a reviewer. These are rough estimates `[I]`, and each rests on the dependency named.

### 6.1 What the live lane will deliver if Link 3 completes

- `'4.0'` windows plus authority flipped on both charts: 2020–2030, candidate-1 flags, contacts cited by id.
- The N-11 `'2.0'` disposition.
- Eventually, the PR #2731 merge (M-8, the kernel, P-1..P-4, S-1/S-2 code).

Estimate: **2–5 days** to finish, including the 24-hour soak, chart 2 and conflict resolution. It depends on DB connectivity (tonight's failure) and on the merge conflicts.

### 6.2 What remains after the lane

| # | Item | Class | Effort | Rests on |
|---|---|---|---|---|
| 1 | **Deploy P-1/P-2/P-4 serving before, or with, the flip.** If the flip lands first, a hot-fix merge is needed. | must-fix, serving | 1–3 d | PR #2731 conflict resolution; deploy pipeline |
| 2 | **Orchestrator-native `ka_gochara` writer**: fold kernel + step06/06a/06b into a `WriterBase` heavy writer (`plan_substeps`, `ctx.db_conn`, no commit, no `date.today()`); retire the `'2.0'` code path; set `target_floor` after the build | must-fix, correctness / contract | 7–12 d | FROZEN contract; transaction size (about 139k contacts per chart per decade); N-11 |
| 3 | **Registry and seed reconciliation**: `ka_gochara` seed = `'4.0'` plus the 8 dependencies; century `is_active:false` (PR #2734); E-013 resonance edges; K-1 Kṣetra edge; N-8 Tithi edge; retire R240/R136 properly | must-fix, governance | 1–3 d | seed owner (a cross-campaign file); Nikaṣa R06/R10 vocabulary |
| 4 | **Horizon parity**: extend `'4.x'` to 1984–2084 (about 10× contacts, roughly 1.4M rows per chart `[I]`), or get a native ruling that accepts a narrower served horizon | must-fix / decision | 3–7 d including measurement | storage and build cost `[U]` (KALA_COST_PROFILE is PARTIAL) |
| 5 | **Resonance rebuild with R-1..R-6**, then a new candidate `'4.1'` (a published generation is immutable) | correctness | 2–4 d | standing-order authorization; re-flip gates |
| 6 | **Overlays to the requested horizon in production** (F-11), plus a stamp-preserving writer on main | correctness / enrichment | 2–4 d | item 4's horizon; §12.9 fingerprints |
| 7 | **Time-varying permission** (undo the static collapse) and PROMISE saturation analysis; wire tārā | algorithm | 4–8 d | M-4 audit; D-3 method ruling for anything that changes λ semantics |
| 8 | **M-3 Moon channel** (on-demand episodes with coverage) | enrichment | 3–6 d | doctrine `[U]` (Moon-from-Moon); P-4 |
| 9 | **M-7 bindu qualification**: G-10 L1 contributor matrix (migration 1086 in the L1 lane), then replace the sign-level interim | enrichment | 6–10 d across L1 + L3 | L1 owner; WP8 evidence |
| 10 | **M-6 targets** (Gulika/Māndi, bhāva-ārūḍhas), **M-4 mechanism audit**, Kota w25 | enrichment | 5–10 d | native rulings per class; corpus reads |
| 11 | **Nikaṣa closure**: Earn/Cost (migration 1094 instrument), Carr detectors, Dens.served `density_contract` on vedha/moorti/service modules, Complete.depth columns, build records for out-of-band rebuilds | governance | 3–6 d | Nikaṣa census tooling |
| 12 | **Housekeeping**: restore drill (step 2); `se1_checksums`; secrets rotation; legacy_semantics docstring; conjunct (i) real detector; 12.10c merge hygiene | governance | 2–4 d | native (secrets, drill dump) |
| 13 | **Cross-stream**: S-2 consumption by Saṅgam, G-7 Saṅgam aspects, `kala_trigger` T-1, Kṣetra rebuild against `'4.x'` | serving / ecosystem | 3–6 d (sibling owners) | Saṅgam and Kṣetra lanes |

**Totals `[I]`:**

- Must-fix (items 1–4): about **12–25 agent-days**.
- Full enrichment (items 5–13): a further about **30–55 agent-days**.
- Overall "fully enriched" is roughly **6–11 weeks** of lane time, plus native rulings. It excludes century retirement (G-1), which is not decidable here.

---

## 7. Risks and dependencies

1. **Flipping on undeployed serving (D-3), highest immediate risk.**
   - If Link 3 flips authority to `'4.0'` while production MCP runs main's `register_gochara_windows.ts`, provenance falls to the v1 branch and coverage attestation reads the retired sweep.
   - A decade-only generation is then served as if it were the product.
   - ADK-0023 pre-authorizes the flip without returning to the native. Suvarṇa should ask the lane, now, to confirm a deploy-before-flip gate, or to confirm whether production MCP is served from this branch `[U]`.
2. **Coordination with the live lane.**
   - The lane holds the only `'4.0'` machinery, the surrogate governance (ADK/PRAMĀṆIN), migration block 1150–1159 and pre-authorized production writes.
   - Recommended split `[I]`: the lane owns everything through Link 3, N-11 and the PR #2731 merge.
   - Suvarṇa takes ownership afterwards, starting with items 1–3.
   - Until then, Suvarṇa must not:
     - rebuild any family asset from main (D-8);
     - re-seed the registry (D-2);
     - touch `kala_gochara_*` or `gochara_resonance_map`.
   - Relay D-1..D-5 to the lane as findings. D-4 and D-5 are not in its record.
3. **Downstream consumers.**
   - `ka_sangam` (depends on `ka_gochara` and `ka_vedha_gochara`) and `ka_kshetra` (depends on resonance and vedha, and reads windows undeclared) will see `'4.0'` on their next build.
   - Kṣetra pins provenance by window id. A post-soak reversal deletes the `'4.0'` rows and leaves Kṣetra edges dangling (K3 obs. 4).
   - Kṣetra is in `error` on the canonical chart, and the Suvarṇa draft notes it refuses to rebuild a populated chart.
   - `ph_muhurta` depends on `ka_gochara` (service).
   - Any change to `GocharaTransitService.find_aspects` must keep its shape for `kala_trigger` and `currents.py` (F-25).
4. **Input-vector drift.** The `'4.0'` candidate pins resonance, overlays and L1 builds. Any upstream rebuild (resonance R-1..R-6, L1 yoga rebuilds such as F-21, overlay horizon) forces a new candidate label, re-gating and a re-flip.
5. **Merge risk.** 188 commits, `CONFLICTING`. Migrations are applied in production but absent on main. There are migration-number collisions with Saṅgam (1071/1072). The 12.10c digest and pin regeneration is outstanding.
6. **Doctrinal dependencies outside L3:** G-6 (L0 node), G-10 (L1 BAV), G-7 (Saṅgam). The Native Decision 11 boundary may move "algorithm correctness" work above the data plane.
7. **Nirmāṇa → Nikaṣa supersession** (PR #2751 open). The "frozen" status of `ka_gochara`, resonance, vedha and the sweep under Nirmāṇa is not certification. Nikaṣa lists 40+ OPEN gaps across the family (§4.2).

---

## Appendix: key queries run (all read-only via port 5433)

- `asset_registry` rows for `%gochara%`, moorti and kota.
- Windows and `_v2` counts grouped by chart and generation.
- `kala_gochara_authority`.
- Contacts, coverage and publication counts.
- Horizon.
- Resonance by `target_resolution_state` and `target_type`, and `sensitive_degree` values.
- `ga_yoga_firings` for resonance yoga ids.
- Vedha and moorti spans and stamps.
- `_migrations_applied` for 1070–1099 and 1150.
- `pg_trigger` on `kala_gochara%`.
- `build_protected_assets`.
- `asset_throughput`.
- `build_run_assets` aggregates.
- `kala_gochara_convention`.
- `information_schema` column lists.
