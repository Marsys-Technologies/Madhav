---
artifact: CLAUDECODE_BRIEF_GA3_CHART_FACTS_WRITER_v1_0.md
canonical_id: GA3_CHART_FACTS_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 1, asset ga_positions/ga_strength — the chart_facts spine)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A3_CHART_FACTS_SPEC_v1_0.md (LOCKED — schema authority)
---

# GA3 — chart_facts Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

Read before coding; do not infer:
- `00_ARCHITECTURE/A3_CHART_FACTS_SPEC_v1_0.md` — **the schema authority.** Row schema (§1), fact_id (§2), ~131-category enum (§3, +16 from GA5 → ~147), ayanamsha keying (§4), subject naming (§5), dual citations (§6), verification semantics (§13), prime-directive enforcement (§17). This brief operationalizes that spec; on any conflict the spec wins for *schema*, this brief wins for *current engine/naming reality*.
- `00_ARCHITECTURE/L1_GANITA_BUILD_CAMPAIGN_v1_0.md` — §A principles, §B DAG + storage map, §E agent gate-validators, §G targets.
- `00_ARCHITECTURE/UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md` — asset model, build-state.

## §1 — Reality reconciliation (the spec is older than two decisions — apply these)

A3 was LOCKED 2026-05-29, before two binding native decisions. **Translate as you implement:**

1. **Engine = PyJHora, not `natal_engine/`.** Every "natal_engine" reference in A3 (including `engine_version` examples like `natal_engine/0.2.0` and file paths like `natal_engine/panchanga.py`) maps to the PyJHora adapter (`platform/python-sidecar/pyjhora_adapter/`, PyJHora==4.8.6) ([[project-pyjhora-is-the-engine]]). `engine_version` strings written to rows use the real adapter version (read it at runtime — do not hardcode `0.2.0`). **No JH-parity oracle anywhere** ([[feedback-no-jh-parity-anywhere]]); verification is internal-consistency + FORENSIC grounding only.
2. **Asset IDs are `ga_*`, not `ganita.*` or `A*`.** This writer's registry rows are `ga_positions`, `ga_strength`, `ga_sensitive`, `ga_dashas`, `ga_vargas`, `ga_panchanga`, `ga_sade_sati`, `ga_tajaka`. GA3 *itself* is the chart_facts **table + schema + the writers that populate the chart_facts-resident categories** (positions, strength, sensitive, panchanga, sade_sati, structural). Vargas → `chart_divisionals`; dashas → `ganita_dashas`; positions → `ganita_positions`. See §3 storage map.
3. **Postgres-direct writers, no JSONL/md dump.** PyJHora computes in-process; the writer does parameterized `INSERT INTO chart_facts (...)`. There is no intermediate `chart_output.JSONL` file to parse (the A3/A4 "chart_output.JSONL" input references mean: read the engine's in-memory result object). Confirmed against `graha_sthana_writer.py` pattern.
4. **No audience tier** anywhere ([[feedback-no-audience-tier]]). The 4 channel adapters in A3 §11/§12 are retrieval-shape variants (bundle vs specific, row caps) — NOT tier gates. Keep them as response-shape config; strip any `audience_tier` branch on sight.
5. **Floors are aspirational** ([[feedback-floors-are-aspirational-not-gates]]). The "~131 categories / 75K–110K rows" are targets to chase with genuine deterministic data. Never fabricate a row to hit a count. Never halt a build for being under a floor. The ONLY hard gate is integrity (prime directive + FORENSIC + two-pass).

## §2 — Branch + topology

- Branch `feature/ga3-chart-facts-writer` off `main` (main HEAD `c78c0d45`, Phase 0 complete). One PR when green.
- This brief is **load-bearing for all of L1**: it creates `chart_facts`/`chart_dashas`/the `l25_*` and audit tables (if Phase 0 created only `chart_facts`, create the rest here), declares `CHART_FACTS_SCHEMA.json`, and ships the **positions + strength** writers (the spine other GA writers extend). GA4/GA5/GA6/GA7/GA8/GA9 are mechanical extensions emitting their category subset into this table — they depend on this brief landing first.
- **Target chart_id (RESOLVED):** the canonical native chart is **`482012f1-710e-4a25-994a-93821f5871aa`** (confirmed on prod 2026-06-10 — the only real `charts` row for Abhisek Mohanty; for this row `charts.id == charts.chart_id`, and the L1 tables' FK is on `charts.id`). `asset_throughput` is **already correctly keyed** to it (17 per-chart `ga_*`/`bg_*` rows, dormant) — **no re-keying needed.** Pass it as a parameter (`build(chart_id='482012f1-…', build_id)`) — don't scatter the literal through logic, but it is no longer a halt condition.
- **`362f9f17-…` is a DEAD phantom UUID** — it never existed on prod. It appears throughout the LOCKED specs as illustrative `chart=362f9f17` citation examples; treat every such example as a placeholder, NOT a real id. Write `482012f1-…` in real rows.

## §3 — Storage map (which category lands in which table)

Per A3 §3 + §7 + §8 and the campaign §B. **chart_facts is NOT the only L1 table.** Atomic-grain rule (§5 below) governs all of them.

| GA asset | Categories (A3 §3 groups) | Target table | Target (aspirational) |
|---|---|---|---|
| `ga_positions` | birth_metadata, ayanamsha context, lagna/cusps, per-graha core (28 cats) | `ganita_positions` | ~50 (5 ay × 10 bodies core) → extend toward full per-graha category set in chart_facts |
| `ga_strength` | shadbala (7), vimsopaka, ishta/kashta, bhava_bala, ashtakavarga (7) | `chart_facts` | ~11,000 |
| `ga_sensitive` | esoteric+sensitive (GA5 — 30 cats) | `chart_facts` | ~13,000 |
| `ga_panchanga` | panchanga birth-day (GA4 — ~33 cats) | `chart_facts` (+ persisted instant) | ~600–800 |
| `ga_sade_sati` | sade_sati_natal_baseline (GA9) | `chart_facts` | ~875 |
| `ga_vargas` | varga_* (GA6 — 30 vargas) | `chart_divisionals` | ~78,000 |
| `ga_dashas` | dasha hierarchy (GA7 — 7 systems, 4-level Sukshma) | `ganita_dashas` | ~2.5–3M |
| `ga_tajaka` | Tajaka/varshphal | (awaits table — out of this brief) | TBD |

**GA3's own writer scope in this brief:** create all tables + schema + `CHART_FACTS_SCHEMA.json`, then ship **`ga_positions` (into `ganita_positions`)** and **`ga_strength` (into `chart_facts`)**. The other writers are separate briefs (GA4/GA5 in this batch; GA6–GA9 later) that consume the schema this brief locks.

## §4 — Tables to create (if not already present from Phase 0)

Phase 0 created `chart_facts` (migration 204, 18 columns, confirmed on prod). **Verify its DDL matches A3 §1 exactly** (`\d chart_facts`); if Phase 0's 18-column version diverges from A3 §1, author a corrective migration — A3 §1 is authority. Then author migration(s) for the remaining tables A3 declares, IF absent on prod (check first, [[feedback-brief-schema-promise-audit]] — read the migration file, grep `CREATE TABLE`, verify against `\dt`):

- `chart_dashas` (A3 §8 — self-FK hierarchy, depth 5 in spec; **campaign decision = 4-level Sukshma**, see GA7 brief — table supports both via `level_n`).
- `chart_facts_history` (A3 §15 — append-only, 30-day retention).
- `chart_facts_supersedence` (A3 §15).
- `l25_msr_signals`, `l25_cdlm_cells`, `l25_cgm_nodes`, `l25_cgm_edges`, `l25_rm_resonances`, `l25_ucn_digests` (A3 §7) — **create the tables (DDL) but DO NOT populate** (L2 Bodha writers own these; out of L1 scope). Creating empty keeps the FK target stable for `constituent_facts_array`.
- Indexes per A3 §9 (all of them). `chart_divisionals`, `ganita_positions`, `ganita_dashas` already exist (Phase 0 / prior) — verify columns, don't recreate.

All migrations: reversible down-block, idempotent (`IF NOT EXISTS` / guarded), `[verify-against: prod]`.

## §5 — The single hard storage rule: atomic grain

**Every queryable sub-value is its own row. `fact_value_jsonb` is reserved for irreducible composites only.** This is the campaign's one non-negotiable storage rule and the atomic-grain gate (§7) enforces it.

- Shadbala's 6 sub-balas → **6 rows**, never 1 JSONB blob (A3 §1).
- Ashtakavarga bindus per house → **12 rows**.
- A graha's longitude / sign / nakshatra / pada → **4 rows** (each a `fact_key`).
- JSONB allowed ONLY where the value is genuinely irreducible (e.g., `chart_output` provenance metadata, an eclipse's `natal_points_within_1deg_array` where the array is the atom). If a reviewer can write a SQL `WHERE` that should match a value buried in JSONB, it must be a column/row instead.

`fact_id = sha256(f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}")[:16]` (A3 §2). Stable per build.

## §6 — Writer scope detail (this brief ships these two writers)

### 6.1 — `ga_positions` writer → `ganita_positions`

Source: PyJHora `pyjhora_adapter` graha positions, **per ayanamsha** (5 canonical: `lahiri_chitrapaksha`, `true_chitra`, `krishnamurti`, `raman`, `surya_siddhanta_classical`). Existing reference: `platform/python-sidecar/brahmagyan/ganita/graha_sthana_writer.py` (Postgres-direct INSERT pattern — reuse the connection/transaction shape, NOT necessarily its row content; [[feedback-rebuild-skepticism-of-existing-code]]).

Bodies (A3 §5 subject set, ≥10 core, extend toward 23): SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN, RAH_TRUE, KET_TRUE, plus outer/asteroid/Lilith where PyJHora supplies them (URA, NEP, PLU, LIL_MEAN, LIL_TRUE, CER, PAL, JUN, VES, CHI…). Floor ~50 is 5×10; chase the full body set with genuine engine values.

Per body, per ayanamsha, emit atomic rows for: `longitude_sidereal`, `longitude_tropical`, `sign`, `sign_lord`, `nakshatra`, `nakshatra_lord`, `pada`, `speed`, `retrograde_flag`, `combustion_state`, `house_d1`, dignity, `kp_star_lord`, `kp_sub_lord` (A3 §3 per-graha core categories). Use `ayanamsha_id='INVARIANT'` only for truly ayanamsha-independent keys (none in positions — positions are all ayanamsha-dependent).

### 6.2 — `ga_strength` writer → `chart_facts`

Source: PyJHora shadbala + ashtakavarga + bhava_bala. **two_pass_verified MANDATORY** (A3 §13 — shadbala/ashtakavarga require it).

- **Shadbala** (A3 §3 per-graha strength): per graha (7 classical: Sun–Saturn), emit `graha_shadbala_sthana`, `_dig`, `_kala`, `_cheshta`, `_naisargika`, `_drik`, `_total` as **7 separate rows** (atomic). Unit `rupa`. Plus `graha_ishta_phala`, `graha_kashta_phala`, vimsopaka (shadvarga/saptavarga/dasavarga/shodasavarga).
- **Ashtakavarga** (A3 §3): `ashtakavarga_bindu` per (graha, house) — atomic per house; `_pinda_sodhita`, `_pinda_bhinna`, `_pinda_sarva`, `_kakshya`, `_trikona_shodhana`, `_ekadhipathya_shodhana`. Sarvashtakavarga rollups.
- **Bhava bala** (A3 §3 per-house): `house_bhava_bala_subscore` (atomic per component) + `house_bhava_bala_total`, per 12 houses.

Two-pass method: pass-1 = PyJHora computation; pass-2 = independent re-derivation (classical formula reconstruction OR algebraic invariant — e.g., sum of bindus in a sarvashtakavarga = 337; shadbala sub-balas sum to total within ε). On mismatch beyond tolerance → `verification_pass_status='divergent_flagged'`, write `CONDUCTOR_HALT_LOG.md`, halt. (Integrity is the hard gate.)

## §7 — Prime-directive + atomic-grain enforcement (A3 §17 — implement all)

1. `CHART_FACTS_SCHEMA.json` declares per-key `value_type` ∈ {num, text_enum, bool, jsonb_atomic} — **never `prose`**. Writers fail on mismatch.
2. `fact_value_text` enum-validated for categorical keys (sign, nakshatra, dignity) against the schema enum.
3. **No-narration linter**: scan `fact_value_text` for forbidden patterns (`indicates|suggests|implies|means|denotes|yields|results in|leads to`). Halt on hit.
4. No `interpretation`/`meaning`/`narrative` columns — schema literally can't store opinion.
5. `drift_detector` samples rows at build close, verifies value↔schema.
6. Hard gate `G7_only_facts` runs per-build + nightly.

## §8 — Dual citations (A3 §6 — both forms on every row)

- `citation_ref = "{category}.{subject}.{key}@chart={chart_id}:ay={ayanamsha_id}:eng={engine_version}"` — machine-stable slug.
- `citation_human` = rendered from the per-category `render_template` in `CHART_FACTS_SCHEMA.json` — a complete sentence, sentence case, units shown, ayanamsha parenthesized, period-terminated. LLM panels drop it directly into prose. (A3 §6 examples — but **correct the stale example**: Sun is in **Capricorn/Makara**, nakshatra range is around **Shravana/Dhanishta** for Sun — verify against the engine, do NOT copy A3's "Sun in Shravana" line uncritically; FORENSIC anchors §9 are authority.)

## §9 — FORENSIC grounding gate (the L1 acceptance bedrock — assert every build)

Every L1 writer asserts the engine's output against these anchors before any row is committed. **These are the hard correctness gate** (campaign §E FORENSIC validator):

- Sun in **Capricorn (Makara)**.
- Moon nakshatra **Purva Bhadrapada** (lord Jupiter).
- Lagna **Aries (Mesha)** — *not Scorpio* (MET.LAGNA.SIGN = Aries per FORENSIC v6.0; a known trap).
- Tithi **Shukla Tritiya**; Vara **Ravivara**; Yoga **Shiva**; Karana **Garaja**.

If PyJHora's output for the native disagrees with any anchor → halt build, write `CONDUCTOR_HALT_LOG.md`, escalate. No rows from a chart that fails FORENSIC.

## §10 — Materialized views (A3 §10 — natal-fixed only)

Create the MV DDL for the views GA3's categories feed: `mv_chart_planet_summary`, `mv_chart_shadbala_summary`, `mv_chart_ashtakavarga_summary`, `mv_chart_bhava_bala_summary`, `mv_cross_ayanamsha_consensus`. Refresh **synchronous at build close** — the build-state row does not flip to a built/lit state until MVs refresh. (Other GA writers add their own MVs.) NO MV for time-varying queries.

## §11 — Build-state wiring (cockpit progress bars must move)

On successful build, update `asset_throughput` for `ga_positions` + `ga_strength` (keyed to the canonical chart_id from the reconciliation): set row counts + state transition (dormant → built/lit per the registry lifecycle). The cockpit Nirmāṇa progress bars read these. **The chart_id the writer targets MUST equal the chart_id the `asset_throughput` rows are keyed to** — otherwise bars won't move (this is exactly the discrepancy Cowork is resolving; honor whatever it declares canonical).

## §12 — Acceptance criteria (all `[verify-against: prod]`)

1. `chart_facts` DDL matches A3 §1 exactly; `chart_dashas`, history, supersedence, 6× `l25_*` tables exist on prod (empty `l25_*` OK). `[verify: \d + \dt]`
2. All A3 §9 indexes present. `[verify: \di]`
3. `CHART_FACTS_SCHEMA.json` exists, declares every category this brief writes, validates against DB. `drift_detector` GREEN. `[verify: drift_detector run]`
4. `ga_positions` populated `ganita_positions` for the native, ≥5 ayanamsha × ≥10 bodies, atomic rows, both citations non-null. `[verify: psql count + sample]`
5. `ga_strength` populated `chart_facts`: shadbala 7-subscore-atomic per 7 grahas, ashtakavarga atomic-per-house, all `two_pass_verified` (zero `single`, zero `divergent_flagged`). `[verify: psql GROUP BY verification_pass_status]`
6. FORENSIC 7/7 PASS (§9). `[verify: assertion log]`
7. No-narration linter + `G7_only_facts` GREEN; zero rows with forbidden text patterns; zero `value_type:prose`. `[verify: linter run]`
8. Atomic-grain gate GREEN: no JSONB blob holds a value a `WHERE` should match (sample audit). `[verify: jsonb audit]`
9. MVs refresh at build close; `asset_throughput` rows for ga_positions/ga_strength updated, keyed to canonical chart_id; cockpit bars move. `[verify: cockpit + psql]`
10. CI green; merge-verify (`gh pr view --json mergeCommit,state`) before claiming done ([[feedback-pr-quality-gate-is-not-a-merge]]).

## §13 — Rails

Reversibility (backup before destructive migration; reversible down-blocks), verify-before-promote, merge-verify before done, no JH-parity, Postgres-only, atomic-grain, deterministic accuracy over volume, floors aspirational. Halt-and-report on FORENSIC failure, two-pass divergence, prod-state surprise, or unresolved canonical chart_id.

---

*End of GA3 brief v1.0. The chart_facts spine: tables + schema + positions + strength. GA4/GA5/GA6–GA9 extend it.*
