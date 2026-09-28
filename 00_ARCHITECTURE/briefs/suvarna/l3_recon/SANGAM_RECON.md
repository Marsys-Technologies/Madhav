# Saṅgam family: reconciliation for the Suvarṇa campaign

**Scope.** This covers the L3 asset `ka_sangam` and its table `kala_convergence`, plus the assets and tables around them.

**Date and method.**
- Prepared 2026-09-28 in a read-only pass: no edits, commits, database writes or builds.
- Git refs were read at `origin/main` = `d968e889f` (2026-09-28 15:49 UTC) after a fresh `git fetch`.
- Production figures come from read-only `psql` queries against the live database. Each query is quoted beside its result.
- Every claim carries a source. Where something is my own inference, it is labelled **[inference]**.

Two background research passes contributed:
- **The governance sweep** read the design documents across eight refs.
- **The code inventory** read the writer and service on `origin/main` and the stage-3 diff.

I re-checked their load-bearing claims at source and correct one of them in §2.

---

## 0. Summary

**Production state.** Saṅgam has **zero rows for the canonical chart** (`482012f1`). They have been missing since about 2026-09-08. The cause:
- A `bo_laksana` rebuild replaced that chart's `bodha_msr_signals`.
- `kala_convergence.signal_id` references that table `ON DELETE CASCADE`.
- So the replacement deleted every Saṅgam row, along with the rows of the four sibling L3 tables that carry the same foreign key.

The only rows in production are these, and all of them were written by code that is older than today's `main`:

| Chart | Rows | Built |
|---|---|---|
| Abhinandan, `1c826d5a` | 17,957 | 2026-08-12 |
| Kiran Shenoy, `cb73cd3d` | 2,540 (Mode D only) | 2026-07-27 |

**Code state.** A large algorithmic elevation was built on `sangam/stage3` between 2026-09-22 and 2026-09-24:
- six repairs R-1…R-6;
- elevations E2, E4, E5 and E6;
- a kernel split and stable identity;
- five migrations.

It has an independent review verdict of CONFORMS_WITH_AMENDMENTS. But **none of it is merged, deployed or applied**:
- The consolidation PR #2735 is an open draft and fails four CI checks.
- Its migrations 1071/1072 were renumbered to 1092/1093 on a different branch.
- None of the new columns exist in production.

**Stage 4** was written (`204b003ea`) but never executed. Its worktree has zero commits.

**The biggest meaning defect in the shipped rows.** On `main`, Modes A/B measure every transit contact against **0° Aries**:
- 0 of 50,678 canonical predicates carry `target_longitude_deg`, and the engine defaults it to 0.0.
- Stage3's R-1 fixes this, but only partly: DOSHA predicates get no target at all.

**A defect D-K did not catch.** Stage3's E5 episode rows carry `peak_date = NULL`. Main's integrity contract rejects those rows, and downstream readers filter them out. No stage3 test touches a database.

**Direction.** ŚAḌ-DARŚANA documents plan to *retire* Saṅgam into `kala_field`, while the Nirmāṇa/L3 documents plan to *elevate* it. No document reconciles the two.

---

## 1. Inventory

### 1.1 Assets and tables

| Object | Kind | What it is, in plain words | Evidence |
|---|---|---|---|
| `ka_sangam` (Saṅgam, "Convergence engine") | L3 writer asset | Finds date windows where several independent timing "currents" line up for one chart signal, and scores them. The currents are daśā, transit contact, station, aṣṭakavarga, vedha, tārā/panchāṅga, eclipse, tājika and school consensus. It runs four modes: **A**, daśā-prior contact search; **B**, off-daśā sweep; **C**, sign-residence trigger for SUBSYSTEM predicates; **D**, SAV-bindu ingress windows (Jupiter, Saturn and Mars ingresses into strong signs). Each mode runs over two horizons: `near`, about 7 years, and `lifetime`, a 1950–2050 century. | Live `asset_registry` row (query `select … from asset_registry where asset_id='ka_sangam'`): description "Rigor-scored intersection windows (Mode A daśā-prior funnel + Mode B off-daśā sweep) … THE VALUABLE CORE."; `expected_volume_inputs` for Mode D; `has_substeps=t`; `writer_timeout_seconds=10800`; `rung=R3` |
| `kala_convergence` | Production table, 21 columns | One row per convergence window. Columns: `window_start/end`, `peak_date`, `mode`, `horizon_tier`, `signal_id`, `domain`, `convergence_score` (0–1), `orb_strength`, `rarity_years`, `confidence_score`, `confidence_label` (high/moderate/speculative), `confidence_label_relative`, `tier_basis`, `independent_current_count`, `is_off_dasha_discovery`, `constituent_factors` (jsonb, with 23 keys per Mode A row), `source_citation`. | `information_schema.columns` query; constraints from `pg_constraint` (§3.4) |
| `kala_convergence_staging` | Production table, 8 columns, 0 rows | A vestigial staging table from the original seed script. | `select count(*) from kala_convergence_staging` → 0 |
| `convergence_scores` | Production table | An archived predecessor (`_archive/059_convergence_scores.sql`). Not part of the live DAG. | `information_schema.tables`; `git ls-tree origin/main` |
| `brahmagyan/kala/convergence.py` | Standalone CLI seed script | Registry `natural_key_partition` text says it is "never imported by any reachable entrypoint and never orchestrator-registered". | Live `asset_registry.natural_key_partition` |
| `services/ka_sangam/engine.py` + `pipeline/orchestrator/writers/ka_sangam.py` | Code on `main` | The engine and the orchestrator writer. | `git log origin/main -- …` (first commit `a015a8c9e`, 2026-06-21) |
| `services/ka_sangam/identity.py`, `exposure.py`, `services/ka_dasha_kala/intersection.py` | Code on `sangam/stage3` only | The R-5 identity, the E6 exposure and statistical gates, and the R-2 clock-intersection oracle. | `git diff --stat origin/main...origin/sangam/stage3` |
| Stage-3 columns | Not in production, not on main | `target_provenance`, `availability` (1071→1092); `is_episode`, `episode_uuid`, `episode_children`, `episode_hull`, `perfected` (1072→1093); kernel fields (1088); `contact_uuid` / R-5 identity (1089); `comparable_with` (1090). | §2.3 and §3.3 |

**Name collision to avoid.** `origin/ekv/lead-sangama` is *not* this family. "SANGAMA" there is the EKAVAKYATA integration-lead role (governance sweep: `LEDGER_E.md:1-6`).

### 1.2 Upstreams

The live `asset_registry.depends_on` lists 11 upstreams: `{ka_yojaka, ka_dasha_kala, ka_gochara, ka_muhurta_seva, bo_laksana, ga_dashas, ga_strength, ga_positions, ga_tajaka, bg_transit_rules, ka_vedha_gochara}`.

- The `ka_vedha_gochara` edge exists in production through Gochara's migration `1084_wp7_k1_v1_registry_edges.sql` (applied 2026-09-24 11:46 UTC per `_migrations_applied`).
- Native decision 4 assigned that edge to Gochara and withdrew Saṅgam's own seed claim (`origin/l3/kala-layer-briefs:00_ARCHITECTURE/briefs/nirmana/NATIVE_DECISIONS_2026-09-25_v1_0.md:21`).
- The most load-bearing upstream is `ka_yojaka`'s table `kala_activation_predicates`: it is Saṅgam's predicate source, with 50,678 rows for the canonical chart.

Upstream build state for the canonical chart:

| Upstream | State | Last built |
|---|---|---|
| `ka_yojaka` | **stale** | 2026-09-10 17:17 |
| `bo_laksana` | lit | 2026-09-08 18:22 |
| `ka_gochara` | lit | 2026-09-10 04:16 |
| `ka_vedha_gochara` | lit | 2026-09-07 |
| `ka_dasha_kala` | lit, rows_written=0 | — |
| `ka_muhurta_seva` | lit, rows_written=0 | — |

Source: `select … from asset_throughput where asset_id in (…)`.

### 1.3 Downstreams

**Registry dependents.** Eleven assets list `ka_sangam` in `depends_on`: `ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_taranga, ka_tulana, ka_vighnakara, mi_adhilepa, ph_muhurta, ph_nimitta, ph_pratikara`. Source: `select asset_id from asset_registry where 'ka_sangam' = any(depends_on)`.

**Hard foreign keys into `kala_convergence.convergence_id`** (from `pg_constraint`):

| Child table | On delete |
|---|---|
| `phala_anchors` | CASCADE (migration 363) |
| `kala_darshana` | CASCADE |
| `kala_obstruction` | CASCADE |
| `kala_bhavishya` | SET NULL |

So any Saṅgam delete-then-insert rebuild deletes the dependent L4 `phala_anchors` rows and L3 `kala_darshana`/`kala_obstruction` rows. Stage 4 lists this as the "migration-363 CASCADE risk" fence.

**Serving on `main`:**
- `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts` (registered in `L3_kala/index.ts`).
- The MCP `platform-mcp/src/tools/retrieval/kala_temporal.ts:6` ("KA-3-2 kala.convergence — convergence windows (kala_convergence, via query_convergence_windows)").
- `query_temporal_activation.ts`, per the Nikaṣa `Dens.served` row.
- Neither declares a `density_contract` (Nikaṣa gap `ka_sangam-Dens.served`, `asset_gaps.jsonl:612`).

**Readers of `confidence_label`**, which the brief wants removed: `ka_bhavishya_lekha.py`, `ka_kala_darshana.py`, `ka_tulana/writer.py`, `ka_tulana/ranker.py`, `register_d7_channel.ts`, and the capability census (`origin/sangam/stage3:…/SANGAM_STAGE3_STATE.md`, synergy #9).

### 1.4 How the writer works on `main`

Code inventory at `origin/main` (`d968e889f`). All paths are under `platform/python-sidecar/`.

**Predicate intake**
- The heavy writer is `@register('ka_sangam')` at `pipeline/orchestrator/writers/ka_sangam.py:224`.
- It reads `kala_activation_predicates` joined to `bodha_msr_signals` (`:272-306`) and keeps the top 200 per `signature_class`. There is no ayanamsha filter.
- A per-class quota is applied (`:148-221`): near tier 200, lifetime tier 60.

**Substeps and delete scope**
- One `near` substep, plus one `lifetime:i` substep per lifetime predicate (`:404-407`).
- The resume fingerprint includes today's date (`:464-482`).
- Delete-then-insert happens per tier or per (signal, lifetime) (`:432-437`, `:526-538`, `:577`).
- There is no DB natural-key UNIQUE constraint. Dedup keys on `(mode, peak_date, signal_id)` (`:879-886`).

**Modes** (`services/ka_sangam/engine.py`)
- **A** (`:1048-1327`): the daśā prior from `KaDashaKalaService`, with a static 0.5 fallback (`:1134-1142`), then an aspect-event search. Windows are peak ±15 days.
- **B** (`:1332-1546`): an off-daśā long-horizon search.
- **C** (`:1570-1665`): sign-ingress residence; score = dignity × severity.
- **D** (`:1686-1789`): Jupiter, Saturn and Mars ingresses into signs with SAV ≥ 28; score = SAV/56 × dignity.

**Scoring**
- `convergence_score` = Π(necessary) × (1 − Π(1 − wᵢsᵢ)) over 12 weighted currents (`:696-728`, weights `:42-59`).
- I-21 labels: ≥0.75 high, ≥0.45 moderate.

**Current status on `main`**

| Current | Status | Source |
|---|---|---|
| C7 aṣṭakavarga | Always None | `:103-138` |
| C13 school consensus | Always None | `:588-644`; `school_consensus_by_domain` never populated |
| Panchāṅga | Always None (`event='general'` is not in `EVENTS_MVP`) | `:535-585` |
| C12 tājika | Always None in Mode B | `:1372` |
| Cross-daśā agreement | None in about 96% of Mode A rows | — |
| C8 eclipse | Live since #1887 | — |
| C11 vedha | Live since #1913; reads `kala_vedha_gochara` | writer `:1037-1080` |
| C9, C10, C4 | Live | — |

**Undeclared read.** `bg_transit_rules` is declared as a dependency but no longer read.

**Target point verified live.** Modes A/B find aspects to `target_longitude_deg`, which defaults to 0.0 when absent (`engine.py:1148`, writer `:662`).
- In production, **0 of 50,678** canonical predicates carry `target_longitude_deg` in `transit_trigger_jsonb`. Query: `count(*) filter (where transit_trigger_jsonb ? 'target_longitude_deg')` → 0.
- So on `main` every Mode A/B contact is measured against **0° Aries**, not the natal point. Stage3's R-1 names this "the silent Aries-point default".
- This is the single largest meaning defect in the shipped rows.

**Other shape defects on `main`**
- **Lifetime horizon.** It starts in 1950, not 1984, because birth year is taken from `MIN(chart_dashas.start_date)` (writer `:866-876`; migration 866 `:27-33`).
- **Mode D rows are copies.** They are 25 copies of the same 478 windows, one per qualifying predicate (866 `:17-45`).
- **Aries fallbacks remain.**
  - The house-lord map uses an unpinned LAGNA query with an Aries fallback (`:1149-1162`).
  - Mode C's āyur/vāstu sign lists are hard-coded to an Aries lagna (`engine.py:1557-1567`).
- **Timezone.** The tz offset is taken at `datetime.now()` (`:854`).

### 1.5 How downstream readers use the table

| Reader | How it reads | Source |
|---|---|---|
| `ka_kala_darshana` | Top 750 by `convergence_score`, no tiebreak. Because the scales differ by mode, this intake is 100% Mode C | `ka_kala_darshana.py:20-34,196-197` |
| `ka_vighnakara` | Top 500, `peak_date IS NOT NULL` | `:174-186` |
| `ka_kalasutra` | Best window per signal | `:70-77` |
| `ka_jivana_parva` | Filters `peak_date IS NOT NULL` | `:126` |
| `ka_bhavishya_lekha` | Reads `confidence_label`/`mode`/`tier_basis` | `:160-178,544-584` |
| `ka_taranga` | Domain × month | `:104-120` |
| `ph_nimitta` | Per-domain ranked query | `:334-350` |
| `ph_pratikara` | — | `:205-225` |
| `ph_muhurta` | Via `kala_obstruction` | `:283-304` |
| `mi_adhilepa` | `LIMIT 500`, no ORDER BY | `:293-305` |

**A latent bug in `ph_nimitta`, verified.** Its discovery-path proximity lookup, `ph_nimitta.py:712-713`, runs `ABS(EXTRACT(EPOCH FROM (peak_date - %s::date)))`.
- In Postgres, `date - date` is an `integer`, and `EXTRACT(EPOCH FROM integer)` does not exist. A live test raised "function pg_catalog.extract(unknown, integer) does not exist".
- The savepoint swallows the error at DEBUG (`:722-732`), so discovery-path anchors never link a convergence.

**Serving (TypeScript).**
- `query_convergence_windows.ts:117-130` is the only table reader. It orders by `convergence_score DESC` with no tiebreak, pools all modes, and serves the absolute `confidence_label`.
- It is aliased as `kala_convergence_get` (`tool_name_bridge.ts:595`) and bundled into the MCP `kala_temporal.ts`.
- No API route or UI component references the table.

---

## 2. What was done, and where it stands

### 2.1 Dated timeline

| Date | What | Ref / sha | Merged? | Deployed/applied? |
|---|---|---|---|---|
| 2026-06-21 | `ka_sangam` born: Modes A+B, rigor stratum I-16…I-22, migration 244 | `a015a8c9e` | main | 244 applied 2026-06-21 02:41 |
| 2026-06-22 | U3 currents C7–C13; lifetime horizon tier (340); transit-model redesign rulings §4.5/§4.6 | `4147953b3`, `8b8503ce4`, `04d691dde` | main | 340 applied 2026-06-22 |
| 2026-06-24 → 06-27 | Heavy-writer substep refactor; completeness audit D1–D7, which added SUBSYSTEM mode C and Mode D | `c2aa574a4`, `c9e2d9d3e` | main | 360, 361 applied 06-27 / 06-28 |
| 2026-06-28 | `phala_anchors` → `kala_convergence` CASCADE (363); `ph_muhurta` edge (366) | — | main | applied 06-28 |
| 2026-07-05 → 07-06 | Relative tier (409); writer timeout (420) | — | main | applied |
| 2026-07-16 → 07-18 | D-2/D-3: FIX-PSEL per-signature-class quota; kernel-admission loop | `ab84814a3`, `c40b56c2c` | main | built 07-18 |
| 2026-08-12 / 08-13 | Last successful builds: `1c826d5a` (run `51eaa05c…`, 17,957 rows) and canonical `482012f1` (run `cbd6ea44…`, 14,868 rows) | — | — | canonical rows later cascaded away (§3.2) |
| 2026-09-05 | W1 analysis: F-SANGAM-1…13 (38% of weight budget dead, lagna falls back to Aries, and more) | `main:00_ARCHITECTURE/briefs/nirmana/L3_W1_ANALYSIS_BATCH_E.md:501-598` | main | — |
| 2026-09-05 → 09-06 | N4 honest-null and real-score fixes, all on `main` (see note after this table) | PRs #1877, #1883, #1887, #1890, #1903, #1913 | main (`962188fad`, `6e601dc15`, `475b5a8c3`, `a6691d086`, `d29e0cf00`, `3b95a156e`) | **never built**: no build of `ka_sangam` has run since 08-13 (§3.3) |
| 2026-09-07 | `expected_volume_formula` derived: 25×478 Mode D + 2,918 A/B/C = 14,868 | PR #2197, migration 866 | main | 866 applied 09-07 |
| 2026-09-08 18:20 | Canonical `bo_laksana` rebuild replaces `bodha_msr_signals`. The CASCADE deletes all canonical `kala_convergence` rows **[inference from timestamps and FK, §3.2]** | — | — | — |
| 2026-09-09 | `output_digest_spec` + `natural_key_partition` (976/977, renumbered to 980/981) | PR #2496, #2503 | main | **both** 976/977 and 980/981 are in `_migrations_applied`, with the same `sql_identity` |
| 2026-09-10 | Nirmāṇa t2: `asset_analysis_accepted` and `optimization_verdict_accepted` recorded for `ka_sangam` (not frozen) | `nirmana_evidence.nirmana_elevation_campaign_events` | — | evidence rows only |
| 2026-09-22 | Readiness package; Saṅgam FINAL elevation packet (brief v1.3, algorithm plan v0.4, ruling sheet M-1…M-7, 21 evidence scripts); blueprint §11 node-convention hub defect | PRs #2711, #2714, #2721 | main (docs only) | — |
| 2026-09-23 | **Stage 3** executed on `sangam/stage3` (Kimi Code executor), phases 0–5: R-5 harness; R-1/R-2/R-3(b)/R-4/R-6; E2, E5, E4 + Tājika gate, E6. The E2 edit to the sealed L1 `ga_strength_writer.py` was build-fatal and was **reverted** | `origin/sangam/stage3:…/SANGAM_STAGE3_STATE.md:16-37,243-275` | **no** | DB unreachable all session (`SANGAM_SESSION_CLOSE_v1_0.yaml:322-324`) |
| 2026-09-24 04:18 → 13:11 | D-K merge gate adopted; synergy audit, nine findings; engineering passes 1–3 closed 8 of 10 (#1, #3–#8, #10); #2 closed after session close; migrations renumbered 1085–1087 → 1088–1090; "collision benign" withdrawn (MIG-1); **stage-4 prompt written** | `9ff7d2976` … `204b003ea`; `SANGAM_STAGE3_STATE.md:452-911` | **no** | no |
| 2026-09-24 | Fresh-context D-K review of `204b003ea`: **CONFORMS_WITH_AMENDMENTS**. RRV-01 ABSENT (HIGH), RRV-03 PARTIAL (HIGH), A1–A8 | `origin/l3/kala-layer-briefs:…/briefs/reviews/DK_REVIEW_SANGAM_204b003ea_v1_0.md:23-37` (`d8c008d31`) | no | — |
| 2026-09-24 | Consolidation PR **#2735** opened (merge of `sangam/stage3`, 119 commits) and **held**: D-K undischarged at the time, plus 4 CI failures | `acd05bde8`; PR comments 2026-09-24 12:27 and 14:39 UTC | **OPEN draft** | — |
| 2026-09-24 13:12 | Worktree `/Users/Dev/madhav-l3/sangam-stage4` created on local branch `sangam/stage4` at `204b003ea`. **Zero commits since; clean; no `SANGAM_STAGE4_STATE.md` on any ref** | `git -C … log/status` | — | — |
| 2026-09-25 | Native decisions: #3 D-K discharged by one review; #4 vedha edge owned by Gochara 1084; #6 squash allowed; **#15 renumber 1071→1092, 1072→1093** | `origin/l3/kala-layer-briefs:…/NATIVE_DECISIONS_2026-09-25_v1_0.md:15-32,439-486`; `96347eddb` | layer-briefs branch only (191 behind main) | not applied |
| 2026-09-27 | Nikaṣa L3 census: 8 OPEN gaps on `ka_sangam` | `/Users/Dev/madhav-nikasha/00_ARCHITECTURE/control/asset_gaps.jsonl:608-615` | `campaign/nikasha-test` | — |
| 2026-09-28 | Suvarṇa plan v1.0 draft. It does not name Saṅgam; it notes "six tables are empty for the canonical chart" in L3 | `origin/strategy/suvarna-plan:00_ARCHITECTURE/briefs/suvarna/SUVARNA_CAMPAIGN_PLAN_v1_0.md:454` | draft | — |
| 2026-09-28 16:20 UTC | Gochara migration 1150 applied (a `ka_gochara` integrity-conjunct fix; the associated 39-row data fix went in via E-020) | `_migrations_applied` id 885; commit `1fc8fd2d7` on `origin/l3/gochara-autonomous-wp0-7` | not on main | applied |

**Correction to the governance sweep.** The sweep reported that the F-SANGAM-5/7 fix branches were "not merged into main". The `codex/nirmana-l3-f-sangam7-*-dirty-fix*` heartbeat branches were closed (PRs #1966, #1970, #1976). The fixes themselves did reach `main`:
- `3b95a156e`, F-SANGAM-5 vedha (#1913);
- `475b5a8c3`, C8 eclipse (#1887);
- `6e601dc15`, C12 tājika (#1883);
- `962188fad`, C13 (#1877);
- `d29e0cf00`, cross-daśā (#1903).

Source: `git log origin/main -- …/ka_sangam*` and `gh pr list --search sangam`.

### 2.2 Branches compared with `origin/main`

| Ref | Ahead / behind main | Content | State |
|---|---|---|---|
| `origin/sangam/stage3` (`204b003ea`) | 29 / 119 by `rev-list` from its old merge-base; PR #2735 counts 119 commits ahead | The whole stage-3 build: `engine.py` +989, `ka_sangam.py` +631, `exposure.py` +537, `identity.py` +116, `ka_dasha_kala/intersection.py` +121, `ka_taranga.py` +146, 8 new test files, migrations 1071/1072/1088/1089/1090, seed edit, 21 evidence scripts | Unmerged |
| `origin/consolidation/merge-sangam-stage3` (`acd05bde8`) | 18 / 120 | A real merge of stage3 into main (16 docs-only conflicts) | PR #2735 OPEN, draft; checks failing: Unit Tests, Fact-Category Pinning, Governance Gates, Density Census |
| `origin/l3/kala-layer-briefs` (`08dcf9b23`) | 29 / 191 | Carries the renumbered 1092/1093 (SQL bodies identical to 1071/1072), the D-K review and the native decisions. It holds an **earlier snapshot** of the Saṅgam code: it equals stage3 at `a6cc7528b`/`086b127dd`, with no `identity.py`, no 1088–1090, and the E6 gate still at 35/100. So the two branches disagree on both migration numbers and code | Unmerged |
| `origin/l3/kala-elevation-readiness` (`7374d8f71`) | 29 / 136 | Readiness docs E1–E31, audits | Partly merged via #2711/#2714/#2721; the rest unmerged |
| `origin/campaign/nikasha-test` | — | Also carries 1092/1093 | Unmerged |
| `origin/l0/brahmagyan-exec` | — | Also carries the old-numbered 1071/1072 Saṅgam files | Unmerged; **a second copy of the colliding numbers** |
| `origin/l1-w389-ka-sangam-output-digest-spec` | 194 / 2 | 980/981 | Merged (#2496) |
| `origin/codex/nirmana-l3-f-sangam*` | — | Heartbeat/dirty-fix branches | PRs closed; the fixes landed via other PRs |
| `origin/strategy/suvarna-plan` | 1 / 0 | Suvarṇa plan draft | — |

### 2.3 Worktrees

| Worktree | Branch | Uncommitted work | Notes |
|---|---|---|---|
| `/Users/Dev/madhav-l3/sangam-stage4` | `sangam/stage4` (upstream `origin/sangam/stage3`) at `204b003ea` | none (`status --short` empty); 0 unpushed | Created 2026-09-24 13:12 for stage 4; **never used** |
| `/Users/Dev/madhav-l3/readiness` | `sangam/stage3` (upstream `origin/l3/kala-elevation-readiness`) at `204b003ea` | none tracked; ignored `.superpowers/sdd/SANGAM_STAGE3_AUTONOMOUS_EXECUTION_PROMPT_v1_0/progress.md` | That ledger records that **E4 was narrowed**: "full ṣoḍaśavarga domain table / boundary_distance / lord_condition / nīca-bhaṅga detector … narrowed to four typed boolean lineage fields … Cost if wrong: future phase must re-expand to full E4 semantics before M-4 is claimed complete." "21 unpushed" means relative to the readiness upstream only; the tip equals `origin/sangam/stage3` |
| `/Users/Dev/madhav-l3/integration` | `codex/madhav-l3-claude-code` | untracked `MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md`, `briefs/`, `discussion_prompts/` | Not Saṅgam-specific |
| `/Users/Dev/madhav-l3/strategic` | `strategic/dis031-fix` | 2 unpushed commits (readiness E4, PR #2734) | Not Saṅgam-specific |
| `…/9be989df…/scratchpad/consol-sangam` | — | **does not exist** (removed) | The consolidation work survives as `origin/consolidation/merge-sangam-stage3` |

---

## 3. Current production state

### 3.1 Row counts

Query: `select chart_id, count(*), min(computed_at), max(computed_at), … from kala_convergence group by 1`.

| Chart | Rows | Built | Modes / tiers |
|---|---|---|---|
| `482012f1` Abhisek (canonical) | **0** | — | — |
| `1c826d5a` Abhinandan | 17,957 | 2026-08-12 16:31–16:58 | A/B/C/D × near/lifetime |
| `cb73cd3d` Kiran Shenoy | 2,540 | 2026-07-27 | Mode D, lifetime only |

`cb73cd3d` is the `charts.id`; its `charts.chart_id` is `42a4bbdf…`.

Shape of the `1c826d5a` rows (query grouped by tier and mode):

| Tier / mode | Rows | Avg score | Confidence labels | Avg current count |
|---|---|---|---|---|
| lifetime D | 14,352 (80%) | 0.453 | 0 high | 1.0 |
| lifetime A | 1,223 | 0.130 | all speculative | — |
| lifetime B | 958 | 0.078 | all speculative | — |
| lifetime C | 510 | 0.80 | 170 high / 340 moderate | — |
| near A | 322 | — | — | — |
| near B | 232 | — | — | — |
| near C | 360 | — | — | — |

Across the table, Modes A/B **never** reach "high". The only "high" rows are Mode C, whose score is a constant `dignity × severity`. This is the F-SANGAM-1 non-commensurability, confirmed in the live data.

These rows predate every September fix on `main`.

`asset_throughput` records `ka_sangam` as **stale** on all three charts. For canonical it claims `rows_written=14868` and `last_built_at=2026-08-13 01:07` while live rows are 0. The registry `target_floor=14868`. Nikaṣa records the resulting `Count.floor` delta of −14,868.

### 3.2 Why the canonical chart is empty

- `kala_convergence.signal_id` → `bodha_msr_signals(signal_id)` is `ON DELETE CASCADE` (`pg_constraint`).
- The same cascade foreign key exists on `kala_activation`, `kala_bhavishya`, `kala_darshana` and `kala_obstruction`.
- All five of those tables have 0 canonical rows today, while unrelated L3 tables still have canonical rows (`kala_taranga` 92,412; `kala_jivana_parva` 100).
- Canonical `bodha_msr_signals` rows are all `computed_at` between 2026-09-08 18:20 and 2026-09-11. `bo_laksana` was last built 2026-09-08 18:22. The canonical `ka_sangam` build was 2026-08-13.
- **[inference, high confidence]** The 2026-09-08 `bo_laksana` replacement cascade-deleted Saṅgam's canonical output and that of the other signal-keyed L3 tables. No build has run since.
- Suvarṇa's "six tables are empty for the canonical chart" (`SUVARNA_CAMPAIGN_PLAN_v1_0.md:454`) is consistent with this.

**The reverse coupling that now exists.** `public.assert_l2_msr_delete_safe`, added in the data-plane hardening of 2026-09-14/15 (`f828864a7`, `8bda677aa`, `302591bc0`), makes the L2 data plane **refuse** to replace MSR signals that any `kala_*` row references.

Nikaṣa register **R243** records this as "rebuild refused on 1c826d5a and cb73cd3d". The canonical chart is exempt only *because* its Saṅgam rows are gone (`/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md:458`).

### 3.3 Build history and whether a rebuild is possible now

Query: `build_run_assets` joined to `build_runs` for `asset_id='ka_sangam'`, newest first.

- **Last canonical success:** run `cbd6ea44…`, 2026-08-13 01:04–01:07 (`sampurti-a2prime-chart1-full-dag`).
- **Before that:**
  - 2026-08-12: BLOCKED on `ka_gochara`;
  - 2026-07-28: `worker_crash: OperationalError: the connection is lost`, and a BLOCKED on `ka_yojaka`;
  - 2026-07-18: `orphaned_by_crash`;
  - 2026-07-16: several BLOCKED upstream runs.
- **Nikaṣa `Build.history`:** 32 errors and 8 aborts on record (`asset_gaps.jsonl:613`).
- **No build of any asset has been recorded in `build_runs` since 2026-09-19.** The last run was an `l3-lane-frozen-manifest-rebuild`, which failed. So no code merged after 2026-08-13 has produced Saṅgam rows.

**A rebuild of the canonical chart on today's `main` is mechanically possible but not advisable yet.** Four reasons:

1. **Stale upstream.**
   - `ka_yojaka` is `stale` (Nikaṣa `Build.dep_liveness`, `asset_gaps.jsonl:614`).
   - 79 canonical `kala_activation_predicates` rows (all `CLASSIFY_RESIDUAL`, bound 2026-09-10 17:17) reference `signal_id`s that no longer exist in `bodha_msr_signals`. Query: anti-join, result 79.
   - `CLASSIFY_RESIDUAL` is a Mode D qualifying class. If the writer selects one of these, its insert violates the FK. **[inference]** `ka_yojaka` must be rebuilt first.
2. **It would re-arm the L2 lock.** Once canonical Saṅgam rows exist, any later canonical `bo_laksana` replacement is refused by `assert_l2_msr_delete_safe` (R243 extends to the canonical chart). If it is instead forced via the legacy path, it cascade-deletes Saṅgam again.
3. **Downstream cascade.** A Saṅgam rebuild deletes `phala_anchors`/`kala_darshana`/`kala_obstruction` children. These are mostly already 0 on canonical, so the damage today is small. `phala_anchors` canonical has 4 rows, all with `convergence_id` NULL.
4. **It would build the old algorithm.** Main lacks the stage-3 work, so a rebuild now reproduces the pre-elevation semantics with the September honest-null fixes.

---

## 4. Open problems

### 4.1 Correctness defects

Most defects are fixed on `sangam/stage3` but not on `main`, and therefore still live in production. A few are not fixed anywhere.

| ID | Defect | Status | Source |
|---|---|---|---|
| Aries target (R-1) | **Every Mode A/B contact on main is measured against 0° Aries.** Live: 0 of 50,678 predicates carry `target_longitude_deg`. On stage3, R-1 supplies a target only for DIGNITY/DISPOSITOR/YOGA; DOSHA is refused a scan | Open on main; partial on stage3 | §1.4; code inventory (stage3 writer R-1 hunk) |
| F-SANGAM-1 | Score not commensurable across modes; the top 200 are all Mode C, and `ka_kala_darshana`'s top-750 intake is 100% Mode C | Open on main. On stage3, R-6 adds `activity`, but Mode D shares a `comparability_class` with same-signature A/B rows on a different scale | `L3_W1_ANALYSIS_BATCH_E.md:503`; live data §3.1; stage3 `engine.py:911-992` |
| Stage3 E5 vs main's contracts (new) | Stage3 episode rows set `peak_date=None` (`engine.py:2583`). Main's integrity contract fails any `peak_date IS NULL` row (live `integrity_check_sql` line 94). `peak_date` is in the digest key (980) and the natural key (981). `ka_vighnakara`/`ka_jivana_parva` filter `peak_date IS NOT NULL`, so **episodes would fail integrity and be silently dropped downstream**. An episode takes the max child score with the first child's factors (`:2529,2570-2584`), which breaks re-derivation clause (c). The grouping key omits `mode` (`:2425-2438`). **No stage3 test touches a DB.** | Open; **not caught by D-K** | code inventory §4, verified against the live `integrity_check_sql` |
| Stage3 identity / exposure defects (new) | Writer passes `cf.get('orb_deg')`, which is not a `constituent_factors` key, so orb is always None inside `contact_uuid`. E6 stratum domain reuses the prefix map F-SANGAM-6 showed never matches, so domain is likely always `OTHER`. `ka_taranga` still takes the tz offset at `now()`. `ka_dasha_kala/intersection.py` changes C6 for **every** consumer of `KaDashaKalaService`, not only Saṅgam | Open; inferred from code, not executed | code inventory §4 |
| `ph_nimitta` discovery lookup (new) | `EXTRACT(EPOCH FROM date-date)` always errors and is swallowed | Open on main | §1.5 |
| Constituent-lord static 0.5 | Manufactured support when no daśā window covers the peak (`engine.py:1134-1142`); stage3 R-6 excludes it from the kernel only | Open on main | code inventory |
| F-SANGAM-9 / R-3(b) | Lagna falls back to Aries | Fail-loud fix on stage3 only | `L3_W1…:564`; `SANGAM_STAGE3_STATE.md:191-209` |
| R-1 | Transit target defaults to 0° Aries | Fixed on stage3 only | plan v1.0 `:184-193` |
| F-SANGAM-10 | No `ayanamsha_id` column | Open everywhere (brief target field) | `L3_W1…:570` |
| Synergy #3 | Half-open vs closed date conventions; tz offset taken at run time; `date.today()` crash on 29 Feb | Fixed on stage3 only | `SANGAM_STAGE3_STATE.md:483-511` |
| Synergy #6 | `convergence_id` reissued per rebuild; `mi_adhilepa` binds it | `contact_uuid` column (1089) on stage3 only | same |
| Synergy #8 / RRV-16 | Scanner uses TRUE_NODE while M-1 rules mean node | Interim `comparable_with=different_convention` stamp on stage3; resolved only by adopting `find_episodes` (stage-4 item 1) | same; blueprint §11 |
| Synergy #9 | Brief mandates removing `confidence_score`/`confidence_label`; 5 readers | **Open everywhere**; four-step sequence in stage-4 item 5 | `SANGAM_STAGE3_STATE.md:615-621` |
| D-K RRV-01 / A1 (HIGH) | E2's C7 aṣṭakavarga verdict gates on an `ashtakavarga_completeness_receipt` category **no writer produces**, so it is permanently unavailable on Modes A/B (a §N.8 earned-signal defect) | **Open**, blocks honest merge | `DK_REVIEW_SANGAM_204b003ea_v1_0.md:76,258-281` |
| D-K RRV-03 (HIGH, PARTIAL); RRV-06 (PARTIAL) | `perfected` covariate missing from E6 strata | Open | same, `:78,:81` |
| D-K A2 | Registry cycle `ka_sangam`↔`ka_kalasutra` via migration 224:85 | Open | same, `:283-342` |
| D-K A3/A4/A7 | Evidence harness runs only from a directory named `readiness`; a NOT_RUN script vacuously passes its negative control; S20 loosened by its own author | Open | same |
| Pinning gate | `ka_sangam.py:1267` selects `chart_facts` by `fact_category IN (…)` with no `fact_key` (§N.7 item 2) | Open; fails CI on #2735 | PR #2735 comment 2026-09-24 12:27 |
| Seed/DAG parity | Seed adds the `ka_vedha_gochara` edge, which the migration-governed pin lacks; decision 4 says withdraw the seed claim | Open; fails Unit Tests on #2735 | PR #2735 comment 14:39; decision 4 |
| Census drift | Seed edited without regenerating `capability_estate_census.json` | Open; fails Density Census | same |
| SESSION_LOG | Malformed branch SESSION_LOG entry (schema_validator 42 → 46) | Open; fails Governance Gates | same |
| MIG-1 | stage3/#2735 still carry 1071/1072, which collide with Gochara's 1071/1072 (and `l0/brahmagyan-exec` carries another copy). The fix is 1092/1093, which lives on a different branch. `guard:migration-numbers` has **never actually been run** for 1088–1090 (`tsx` absent on the stage-3 host) | Open | `SANGAM_STAGE3_STATE.md:876-911`; stage-4 item 3 |
| B-4 | E2 producer receipt at `ga_strength_writer`: needs an L1-owner packet, no authority bound | Open | `SANGAM_STAGE3_STATE.md:137` |
| B-5 | `ephemeris_daily` node-frame contract undeclared; L0 lane has no authority | Open | `:138` |
| B-6 | No `evaluation_eligible`/`is_synthetic` source field; E6 defaults them | Open (native/L1) | `:139` |
| Ephemeris | Swiss `.se1` files absent on the stage-3 host; S8 oracle is NOT_RUN, so the suite ceiling is 20/21 | Open (environment) | `SANGAM_SESSION_CLOSE_v1_0.yaml:284-290` |
| E4 narrowing | E4 shipped as 4 boolean lineage flags, not the planned `boundary_distance`/`lord_condition`/`varga_condition` | Open, self-recorded | readiness worktree `.superpowers/…/progress.md` |
| D30 | D30-for-DOSHA falsifier gate held and unopened | Held by ruling M-6 | `SANGAM_STAGE3_STATE.md:91,117` |

### 4.2 Nikaṣa gaps

All 8 are OPEN. Each is the last row per `gap_id`, ts 2026-09-27T21:34, detector `asset_census.py --layer L3`.

| Gap | Measured |
|---|---|
| `Build.completion` (`:608`) | live=0 vs floor 14,868; build record says 14,868 |
| `Earn.build_record` (`:609`) | NO_DETECTOR (instrument migration 1094 absent; 1094 is only on `origin/campaign/nirmana-engine`) |
| `Cost.baseline` (`:610`) | NO_DETECTOR (same) |
| `Count.floor` (`:611`) | delta −14,868 |
| `Dens.served` (`:612`) | 2 serving modules, 0 declare `density_contract` |
| `Build.history` (`:613`) | 32 errors, 8 aborts |
| `Build.dep_liveness` (`:614`) | `ka_yojaka` stale |
| `Carr.detector` (`:615`) | no D1/D2/D3 carry detector for this asset |

**Change register.**
- R152, OPEN, BLOCKS_LAYER: which DP contract (DP08) belongs to `ka_sangam` versus `ka_kalasutra` is unassigned (`NIKASHA_CHANGE_REGISTER_v2_0.md:327`).
- R243, OPEN, annotation-only: chart-conditional L2 rebuilds (`:458`).
- R246, OPEN: DELETE-FK-child detector (`:461`).

### 4.3 Design questions left open

1. **Retire or elevate?**
   - ŚAḌ-DARŚANA plans to retire "legacy middle-layer writers (sangam/yojaka/kalasutra/taranga)" at zero consumers, and to merge them into `kala_field` (`main:…/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md:547-556`; `KALA_TRANSFORMATION_HANDOFF_v1_0.md:246-250`).
   - The Nirmāṇa/L3 packet elevates Saṅgam in place.
   - No document reconciles the two (governance sweep §5).
2. **Contact ownership (stage-4 item 1).** Saṅgam should consume Gochara's `find_episodes` events (N-7 kernel path, `kala_gochara_contacts`) instead of scanning ephemerides itself. The June redesign already said "`ka_sangam` should not scan ephemerides AT ALL" (`main:00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md:18-19`). E1 (four contact contracts) and E3 are gated on this.
3. **§4.5 Q1/Q2 of the June redesign** (`planet` as a LIST) never landed, and the landed code forecloses Q2 (brief v1.5 `:93-121`).
4. **Mode D dominance.** 80% of rows are predicate-agnostic SAV ingress windows repeated identically for each of 25 predicates (25 × 478). Whether they belong in this table at all is an open design question. The brief's class-partitioned top-N (`:222-238`) is its proposed mitigation.
5. **Serving meaning change.** Any change needs an L3-U04/U11 packet plus a material-field sentinel (plan `:344-354`). A D-6 served-tier packet to Pūrṇa is also pending.
6. **House-vedha grade** (stage-4 item 2). 36 verse-cited plus 6 UNSOURCED `bg_transit_rules`; strict cover 35.

---

## 5. The "fully enriched" target

### 5.1 Documented intent

All of this is sourced from the ruled `SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md` and `SANGAM_ELEVATION_BRIEF_v1_0.md` v1.5 on `origin/sangam/stage3`, plus the June design on `main`.

**Output contract.** Each row is a Strategy §3 "Temporal testimony" carrying an engagement route and a search coverage (brief `:175-191`). It carries:
- `evidence_roots text[]` of L1 `fact_id`s, referenced and never restated (§N.5);
- `comparability_class` (`A_B_contact` / `C_residence` / `D_ingress`, ranked only within class);
- `independence_groups` with `basis:'declared_lineage'`;
- `method_states`, a six-state F06 per method;
- `route`, where vedha is an inhibitor;
- `coverage`;
- `uncertainty`, `ayanamsha_id`, `domains[]`.

Two further changes: `confidence_score`/`confidence_label` are **removed**, and `independent_current_count` is renamed to `declared_current_count`. Any projection carrying the score must carry the groups and the class (`:240-247`). Every top-N is class-partitioned (`:222-238`).

**Kernel (R-6).**
- Output is split into `activity`, `valence`, `applicability` and `availability`.
- Dignity moves from the necessary product into valence.
- `kernel_version` is labelled, so legacy rows are never pooled.
- Ordering is `activity DESC, instant ASC` within each class (plan `:193`).

**Method, E1–E6** (plan `:197-254`):
- **E1:** four versioned contact contracts, each with its citation:
  - Moon-gochara with vedha (Phaladīpikā 26.1-8);
  - directed Parāśari dṛṣṭi with fractional aspects (BPHS 26.2-5);
  - Jaimini rāśi-dṛṣṭi (BPHS 8.1-3);
  - Tājika (Hāyanaratna).
- **E2:** a signed own-BAV/SAV verdict (BPHS 72).
- **E3:** a fast-tier refinement.
- **E4:** typed conditions `boundary_distance`, `lord_condition` (BPHS 47) and `varga_condition` (BPHS 7), which feed valence only.
- **E5:** station-loop episodes with child contacts and a `perfected` flag.
- **E6:** `modelled_episode_frequency` over a declared exposure, with a two-axis outcome record. The binomial gate is re-set by the native to n=20 per stratum (critical ≥8) and n=50 instrument-level (critical ≥16). Below either, the output reads `PROVISIONAL_INSUFFICIENT_N`; "EMPIRICALLY_EVALUATED" stays locked.

Native rulings M-1…M-7 (plan `:27-66`) fix the conventions:
- mean node;
- Placidus as stored;
- no node dṛṣṭi (N-14 extends this to the Gochara family);
- BAV 4 leans adverse;
- no 6/8/12 inversion;
- D30-for-DOSHA held.

**Identity (R-5).**
- `contact_uuid` is a UUIDv5 over an 8-field tuple, excluding `peak_date`.
- `episode_uuid` is a member-set hash.
- Split, merge and supersession relations are defined.
- L4 binds to natural key plus generation, not `convergence_id` (brief `:368-382`).

**Cross-stream.**
- `comparable_with` is a 4-value relation: `self`, `same_convention_same_inputs`, `same_convention_newer_inputs`, `different_convention`.
- Saṅgam consumes Gochara's `find_episodes` (`services/ka_gochara/service.py:278`), not `gochara_v3/engine.py:1709`, joined by `window_ref` → `(chart_id, generation, contact_id)` (stage-4 prompt `:79-96`).

**Coverage.**
- The near tier moves to an explicit `as_of_date`.
- The lifetime tier stays at a 100-year horizon over up to 60 predicates.
- `domain` becomes `domains[]`, with cross-domain convergence named as the unlock (brief `:89`, `:218-220`, `:324`).

**Serving.**
- The class-partitioned, group-carrying projection must pass through `query_convergence_windows.ts`, whose current default is 30 rows and maximum 200.
- The handoff names `kala_bundle_get` convergence (`main:…/KALA_TRANSFORMATION_HANDOFF_v1_0.md:168`).
- §N.6 requires a `density_contract` (Nikaṣa `Dens.served`).

### 5.2 My inference beyond the documents

- **"Fully enriched" is not reachable by Saṅgam alone.** It needs:
  - Gochara's contact producer (E1/E3);
  - an L1 aṣṭakavarga receipt (E2/RRV-01, B-4);
  - an L0 node-frame contract (B-5);
  - a consent marker (B-6).
- **Calibration will stay provisional for a long time.** E6's gates cannot pass on one chart's outcome ledger. With n=20 per (domain × route × method_version) stratum, the "calibrated" end state depends on L5 outcome accrual, not on engineering.

---

## 6. Gap and effort

The effort figures are my own estimates. They rest on:
- stage 3 building roughly 22k lines (mostly evidence) in about 2.5 elapsed days by autonomous sessions;
- the four CI failures being mechanical;
- items needing other streams' work being counted only for Saṅgam's own share.

"Session-day" means one focused autonomous session of about 6–10 hours.

### 6.1 Must-fix correctness, to get honest rows back into production

| # | Item | Effort | Basis |
|---|---|---|---|
| C1 | Decide the vehicle: land stage3 (after rebase and fixes) or rebuild on `main` first. In both cases, rebuild `ka_yojaka` before `ka_sangam` on the canonical chart | 0.5 day to decide; build about 1–2 h wall per chart (the last canonical build took about 2.5 min for `ka_sangam`, but the full DAG runs took 30–60 min) | `build_run_assets` timings §3.3 |
| C2 | Resolve the L2↔L3 lock (R243 generalised): either change `kala_*`→`bodha_msr_signals` from CASCADE to generation-bound references, or sequence "all L2 signal rebuilds first, L3 last" as policy | 1–3 days; **needs a native ruling** (touches the L2 data-plane guard and the FK DDL) | §3.2 |
| C3 | Fix the 4 CI failures on #2735: pinning at `ka_sangam.py:1267`, seed withdrawal of the vedha edge, census regeneration, SESSION_LOG entry. Then rebase onto main and swap 1071/1072 → 1092/1093 | 1–2 days | PR #2735 comments; decision 4, decision 15 |
| C4 | RRV-01/A1: build a real receipt producer or source for C7, or keep C7 honestly `None` and correct §10 | 1–2 days Saṅgam-side; plus an L1-owner packet (B-4), 1–2 days | D-K review `:258-281` |
| C5 | Apply 1092/1093/1088/1089/1090 surgically and verify against `_migrations_applied` and the schema (§N.4) | 0.5 day | §N.4 |
| C6 | Reconcile stage3's E5 episode rows with main's integrity contract (670 clause g/c), the 980/981 digest and natural keys, and the downstream `peak_date IS NOT NULL` filters. Add `mode` to the episode key. Add **DB-level** integration tests: none exist for stage3 | 2–3 days | §4.1 "Stage3 E5 vs main's contracts" |
| C7 | Fix the stage3 identity and exposure defects (`orb_deg` key, stratum domain map, `ka_taranga` tz); re-verify the blast radius of the `ka_dasha_kala` C6 change on other consumers; fix the `ph_nimitta` EXTRACT query | 1–2 days | §4.1 |
| C8 | Rebuild the three charts, check integrity (`integrity_check_sql`), refresh `target_floor`, refresh `asset_throughput` | 1 day | Nikaṣa `Count.floor`, `Build.completion` |

**Subtotal: about 8–15 session-days**, plus the native ruling on C2.

### 6.2 Algorithm and enrichment

| # | Item | Effort | Basis |
|---|---|---|---|
| A1 | Stage-4 item 1: adopt `find_episodes` (retire the internal scan, mean node, `comparable_with` self-derives), which also unlocks E1 | 3–5 days, **after** the Gochara producer is merged and live | stage-4 prompt `:79-96`; Gochara is still on an unmerged branch |
| A2 | E1: four contact contracts with citations | 4–7 days | plan `:197-254` |
| A3 | E3: fast-tier refinement | 2–3 days | same |
| A4 | E4 re-expansion (`boundary_distance`, `lord_condition`, `varga_condition`) | 2–4 days | narrowing ledger |
| A5 | Synergy #9: `confidence_*` removal across 5 readers in 4 steps | 2–4 days (touches `ka_bhavishya_lekha`, `ka_kala_darshana`, `ka_tulana`, `register_d7_channel.ts`) | stage-4 item 5 |
| A6 | `ayanamsha_id`, `domains[]`, `evidence_roots`, `method_states`, `route`, `coverage` as columns (brief v1.5 contract, beyond what 1088–1090 add) | 3–5 days | brief `:175-191` |
| A7 | Mode D rethink (predicate-agnostic duplication) and class-partitioned top-N | 1–3 days, plus a design ruling | §4.3 item 4 |
| A8 | E2 house-vedha grade (stage-4 item 2) and restoring S8 (ephemeris files) | 0.5–1 day | stage-4 items 2 and 4 |

**Subtotal: about 18–32 session-days**, with A1 gated on Gochara.

### 6.3 Serving and retrieval

| # | Item | Effort |
|---|---|---|
| S1 | `density_contract` on `query_convergence_windows.ts` and `query_temporal_activation.ts` (Nikaṣa `Dens.served`) | 0.5–1 day |
| S2 | Re-shape `query_convergence_windows.ts` and `kala_temporal.ts` to serve class-partitioned rows carrying their groups, kernel fields and `comparable_with`, with a material-field sentinel test (plan `:344-354`) | 2–4 days |
| S3 | Retarget `mi_adhilepa` and L4 bindings from `convergence_id` to `contact_uuid`/natural key plus generation | 1–3 days |

**Subtotal: about 4–8 session-days.**

### 6.4 Governance

| # | Item | Effort |
|---|---|---|
| G1 | Native ruling: ŚAḌ-DARŚANA retirement versus elevation of Saṅgam | ruling, then 0.5 day to record |
| G2 | Correct the §10 overstatements (D-K A5/A6); fix the evidence-harness defects A3/A4/A7; resolve the A2 registry cycle | 1–2 days |
| G3 | Nikaṣa carry detector (`Carr.detector`), the `Earn`/`Cost` instruments (migration 1094 elsewhere), and R152 DP08 assignment | 1–2 days Saṅgam share |
| G4 | Reconcile the three copies of the 1071/1072 files (stage3, `l0/brahmagyan-exec`, `consolidation`) with 1092/1093 (`kala-layer-briefs`, `nikasha-test`), so exactly one lands | 0.5 day |

**Subtotal: about 3–5 session-days**, plus rulings.

### 6.5 Total

- **Everything: about 33–60 session-days.** Some can run in parallel. The critical path goes through the Gochara producer merge and three native rulings: C2, G1 and A7.
- **Must-fix only (rows back, correct, merged): about 8–15 session-days.**
- **Floor.** Calibrated empirical value (E6 gates passing) is not an engineering quantity. It needs outcome accrual.

---

## 7. Risks and dependencies

1. **The L2↔L3 cascade and lock (highest).**
   - Today any `bo_laksana` signal replacement cascade-deletes Saṅgam's rows. That already happened to the canonical chart.
   - Once Saṅgam is rebuilt, the L2 data plane *refuses* such replacements (R243).
   - So Saṅgam and `bo_laksana` cannot both be kept current on the same chart without a policy or DDL change.
   - Every L2 re-elevation under Suvarṇa's Stage 3 (L1→L5 order) will either wipe Saṅgam or be blocked by it.
2. **`ka_gochara` in flux.**
   - The Gochara stream applied 1091 and 1087 (2026-09-24) and 1150 (2026-09-28, integrity conjunct; the 39-row horizon-edge data fix went in via E-020).
   - Its producer branch `l3/gochara-autonomous-wp0-7` is unmerged.
   - Saṅgam's elevated design depends on Gochara's `find_episodes` contract, which is not yet on `main`. Any change to its `precision_regime`/`window_ref` keys invalidates stage-4 item 1.
   - The `ka_gochara` edge is also Saṅgam's most frequent historical build blocker (BLOCKED 2026-08-12).
3. **`bo_laksana` under Nirmāṇa freeze.**
   - `bo_laksana` was declared FROZEN in L2 cycle #81 (HEAD commit `0cb89e971` in this checkout).
   - Its rebuild is refused on `1c826d5a`/`cb73cd3d` (R243).
   - Rebuilding Saṅgam on those charts on top of their current (August) signals keeps the lock in place. Rebuilding the signals there first requires deleting Saṅgam's rows first.
4. **Stale `ka_yojaka` and orphan predicates.** 79 orphan predicates on canonical; `ka_yojaka` must precede (§3.3).
5. **Migration-number collisions.**
   - 1071/1072 exist on three unmerged refs with two different meanings.
   - MIG-1 hard-fails duplicates, and the guard has not been run for 1088–1090.
   - Numbers above 1125 are being reserved in blocks (Gochara holds 1150–1159 under ADK-0026). Saṅgam's numbers must be re-checked at merge time.
6. **Squash is a one-way door.** Decision 6 allows squashing 119 commits. The evidence then lives only in the review artifacts, which must therefore land in the same merge.
7. **Retire-versus-elevate ambiguity.** Investing 30+ session-days in an asset another plan retires is the largest strategic risk. G1 should precede A-items.
8. **Environment.** Swiss ephemeris `.se1` files are missing on the executor host. Oracles fall back to Moshier; S8 is NOT_RUN.
9. **Self-certification history.** Stage 3 breached its own RRV-01 fence (the sealed L1 writer edit, reverted), and engineering passes 1–3 were written by the plan's author. D-K found one HIGH item absent. Any Suvarṇa re-execution should keep an independent reviewer on the build, not only on the plan.

---

## Appendix: key queries

```sql
-- rows per chart
select chart_id, count(*), min(computed_at), max(computed_at) from kala_convergence group by 1;
-- FKs
select conname, conrelid::regclass, confrelid::regclass, pg_get_constraintdef(oid)
  from pg_constraint where conrelid='kala_convergence'::regclass or confrelid='kala_convergence'::regclass;
select conrelid::regclass, pg_get_constraintdef(oid) from pg_constraint
  where contype='f' and confrelid='bodha_msr_signals'::regclass;
-- migrations
select filename, applied_at from _migrations_applied
  where filename ~* 'convergence|sangam|^10(7|8|9)[0-9]|^11[0-9][0-9]' order by 1 desc;
-- build attempts
select bra.*, br.chart_id, br.triggered_by from build_run_assets bra
  join build_runs br on br.id=bra.run_id where bra.asset_id='ka_sangam' order by br.created_at desc;
-- orphan predicates
select count(*) from kala_activation_predicates k where chart_id='482012f1-…'
  and not exists (select 1 from bodha_msr_signals s where s.signal_id=k.signal_id);   -- 79
```
