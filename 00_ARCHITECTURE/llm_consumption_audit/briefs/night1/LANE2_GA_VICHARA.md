---
artifact: NIGHT1_LANE2_GA_VICHARA
type: IMPLEMENTATION BRIEF (Sonnet-executable, self-contained)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
lane: L2 — new asset `ga_vichara` ("judged structure")
depends_on_lanes: LANE1 (merged first — vichara consumes the modularized ga_structural's facts and must not race its refactor)
blocks_lanes: LANE3, LANE4
register_rows: CR-54 (amended), CR-57, CR-62, CR-60 (capability input), CR-69 (leverage_index)
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §4 (deltas 1–2), §8 (leverage_index), §11 (ratification_factor formula), §2 (fold-vs-build)
---

# LANE 2 — New L1 asset `ga_vichara` (valence pass + varga-ratification + consistency index + leverage_index)

## 0. Why (design §2 fold-vs-build rule)

> *enumeration enriches in place; judgment lands as new registered assets* … "Valence pass, varga-ratification matrix, varga-consistency index → **New sibling L1 asset `ga_vichara`** ('judged structure') — consumes `ga_structural`, feeds MSR."

This is the judgment substrate every downstream D-1 lane ranks on. It is deterministic Python (§N.4 deterministic-first — zero LLM in the data path), consumes only already-stored L1 facts (B.10), and every row carries the fact_ids it judged (B.3).

## 1. Exact scope

- **New asset_id:** `ga_vichara` (underscore convention §N.1 — never `ganita.vichara`).
- **New writer:** `platform/python-sidecar/ga_writers/ga_vichara_writer.py` (logic) + adapter `platform/python-sidecar/pipeline/orchestrator/writers/ga_vichara.py` (registration). Model both on the existing `ga_yoga` pair (`ga_writers/ga_yoga_writer.py` + `pipeline/orchestrator/writers/ga_yoga.py`).
- **New table:** `chart_vichara` (L1 tables follow `chart_*`: chart_facts / chart_dashas / chart_divisionals).
- **New L0 constants table:** `brahma_vichara_constants` (design §11: "Constants (0.2 step, [0.6,1.4] clamp, operative-varga sets) are registry data, not literals").
- **One migration** (see §5).
- **Shape:** heavy writer — `plan_substeps` = one `SubStep` per canonical ayanamsha (mirror `ga_structural.py`'s adapter exactly; `CANONICAL_AYANAMSHAS` from `ga_writers.ga_positions_writer`).
- **DAG:** `depends_on = ['ga_structural', 'ga_strength', 'ga_dashas', 'ga_yoga']` — declared BOTH in the adapter class attr (documentation) and in `asset_registry.depends_on` (authoritative, set in the migration; the scheduler reads the DB).

## 2. The WriterBase contract (quoted — ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2, FROZEN)

> - `ContextSpec{ asset_id, build_id, db_conn (caller-owned; writer never commits/closes), config{chart_id, birth_params}, dry_run }`
> - `WriterResult{ asset_id, rows_inserted, rows_updated, rows_skipped, duration_seconds, notes }`
> - `SubStep{ key, label }` — one savepoint-isolated, heartbeated unit; `key` is the writer's idempotency scope.
> - heavy writer → overrides `plan_substeps(ctx) -> list[SubStep]` + `run_substep(ctx, step) -> WriterResult`
>
> If a future layer appears to need a contract change, **STOP and raise with the native**.

§5 checklist items that bite new assets: discoverable under `pipeline/orchestrator/writers/` (auto-discovery) **and ships in the `brahma-pipeline` job image** (check `Dockerfile.pipeline` includes `ga_writers/` — it does; your new file rides along); registry row with real `depends_on`, `count_sql`, `target_floor`, `sort_order`, `has_substeps=true`; idempotency = delete-then-insert scoped to `(chart_id, ayanamsha_id)` per §N.3; no `asset_throughput` writes; honors `ctx.dry_run`.

## 3. Row families and formulas (the algorithm — quote-level fidelity required)

All rows go to `chart_vichara`. Every row carries: `chart_id`, `ayanamsha_id`, `build_id`, `vichara_family`, `subject` (graha/lord/karaka identifier, UPPERCASE like chart_facts `fact_subject`), `domain` (nullable), `varga_id` (nullable), `value_num`, `value_text`, `value_jsonb`, `constituent_fact_ids uuid[] / text[]` (matching chart_facts.fact_id type — **must resolve**, §N.5), `formula_version`, `source_citation`, `computed_at`.

### 3.1 Family `valence_pass` — functional-lordship valence (CR-54 as AMENDED)

Register §I.1 amendment (authoritative fix direction — the original CR-54 premise was corrected):

> The real defect: the classifier grades the **target house's class**, never the **acting lord's functional nature** — so an 8L-Mars→2H aspect reads `neutral` because H2 isn't kendra/trikona/dusthana. **Corrected fix:** derive valence from the actor's functional lordship × target class, not by extending the vocabulary.

Ground truth (verified): `_bhava_link_type` at `ga_writers/ga_structural_writer.py:5463` already emits the 4-way `kendra_link/trikona_link/dusthana_link/neutral_link` on `bhava_significance_link` rows (emitted by `_build_bhava_web_per_varga_rows`, ~:5545) — target-class only. Leave ga_structural untouched (enumeration-pure); ga_vichara adds the judgment ON TOP.

**Computation.** For every stored lord→house / lord→lord link row (source facts: `bhava_significance_link`, `lord_aspects_lord_per_varga`, the house-lord matrix families) in each varga:

1. **Actor's functional nature** = classify the acting graha by the set of houses it lords **in that varga** (sign lordships from the varga's house-sign layout; D1 lordships from lagna): lords of 6/8/12 → `dusthana_lord`; lords of 1/5/9 → `trikona_lord`; lords of 4/7/10 (non-trikona) → `kendra_lord`; lords of 2/7 additionally flagged `maraka`; lord of 3/11 → `upachaya_lord`; dual lordships resolve by the classical precedence: trikona > dusthana > kendra > maraka > upachaya, with BOTH classes recorded in `value_jsonb.actor_classes`. Cross-check D1 against the stored `graha_functional_class_per_ascendant` facts (BPHS canonical) — if your derived class contradicts the stored fact, the stored L1 fact wins and you log the divergence in `value_jsonb` (§N.5: L1 is the authority; never override it silently).
2. **Target's class** = the existing 4-way target-house classification (kendra/trikona/dusthana/neutral) plus dhana-axis membership (2/11) per domain.
3. **Valence** = matrix over (actor_class × target_class), stored as `value_text ∈ {strong_benefic, benefic, neutral, malefic, strong_malefic}` and `value_num ∈ {+1.0, +0.5, 0.0, −0.5, −1.0}`. Required matrix anchors (encode the full matrix as data in `brahma_vichara_constants`, seeded in the migration, NOT as Python literals):
   - dusthana_lord → wealth-house (2/11) or lagna: **strong_malefic** (the CR-54 type specimen: 8L Mars → H2 must come out strong_malefic, not neutral).
   - trikona_lord → kendra/trikona/2/11: **benefic** (strong_benefic when actor is also a yoga-karaka per stored facts).
   - maraka → 2/7: malefic; upachaya_lord → upachaya: mildly benefic (+0.5)…
   - …fill the rest of the matrix from BPHS functional-nature doctrine; every cell must carry a `citation` string in the constants row. Where doctrine is genuinely ambiguous, use 0.0 with `citation:"ambiguous_default"` — never invent a strong value (B.10).
4. `constituent_fact_ids` = the link fact + the lordship facts consumed.

### 3.2 Family `varga_ratification` — the ratification matrix (CR-57, design §4.2 + §11)

Design §11 formula (quoted, binding):

> replace the flat "cap any non-D1 fact at `supporting`" rule with a multiplier `ratification_factor ∈ [0.6, 1.4]` applied to a per-varga fact's salience, `= 1.0 + 0.2 × (agreeing_operative_vargas − opposing_operative_vargas)` over the domain's operative varga set (e.g. wealth = {D1,D2,D9,D11}), clamped. … one that flips sign between vargas … additionally emits a **`varga_ratification_divergence` signal** (CR-57) — the divergence itself becomes rankable evidence… Constants (0.2 step, [0.6,1.4] clamp, operative-varga sets) are registry data, not literals.

**Computation.** For each domain in the operative-varga registry (seed at minimum: `wealth:{D1,D2,D9,D11}`, `career:{D1,D10,D9}`, `marriage:{D1,D9,D7}`, `health:{D1,D6,D9}`, `general:{D1,D9}` — mark all but wealth `provisional:true`; wealth's set is design-ratified, the others await native review) and for each bhāveśa (lord of each domain-relevant house) and kāraka (domain kāraka graha):

- **Agreement test per varga v:** compare the subject's D1 dignity-direction with its dignity-direction in v, using stored `chart_facts` dignity rows per varga (`graha dignity per varga` family). Direction: {exalted, own_sign, mooltrikona, friend} → positive; {debilitated, enemy} → negative; neutral → abstain. Varga v *agrees* if its direction matches D1's, *opposes* if it inverts it, abstains otherwise. (D1 itself is the reference, not a vote.)
- `ratification_factor = clamp(1.0 + step × (n_agree − n_oppose), lo, hi)` with `step/lo/hi` read from `brahma_vichara_constants` (seeded 0.2 / 0.6 / 1.4).
- One row per (domain × subject): `value_num = ratification_factor`, `value_jsonb = {d1_direction, per_varga: {D2: agree/oppose/abstain + dignity, …}, n_agree, n_oppose}`.
- **Divergence rows:** when any operative varga inverts D1's direction, ALSO emit a row `vichara_family='varga_ratification_divergence'` for that (domain × subject × varga) with the two dignities named in `value_text` (e.g. `"VENUS: D1 own_star/H9 promise vs D9 debilitated — wealth ratification fails in D9"`). These become MSR signals in Lane 4.
- Type-specimen expectations on 482012f1/wealth (from CR-57/CR-71, use as test fixtures): Venus (2L) — D9 debilitated (oppose), D11 exalted (agree), D2 H12 (jsonb must carry it); Saturn (11L) — D9 debilitated (oppose); divergence rows MUST fire for Venus and Saturn in D9.

### 3.3 Family `varga_consistency` — continuous consistency index (design §4.2)

> a continuous **varga-consistency index** over the 9×30 graha-varga matrix (vargottama generalized to a score)

Per graha (9) per ayanamsha: over all stored vargas (up to 30, use whatever `chart_facts`/`chart_divisionals` actually holds — do not compute new varga positions, B.10):
`consistency = w_sign × frac_same_sign_as_D1 + w_dign × frac_same_dignity_direction_as_D1` with `w_sign=0.5, w_dign=0.5` from the constants table. `value_num = consistency ∈ [0,1]`; `value_jsonb` lists per-varga sign + dignity. A true vargottama graha (same sign D1/D9) must score strictly higher than a non-vargottama graha with otherwise identical dignity spread — assert with Mercury on 482012f1 (vargottama, CR-38/71) in a test.

### 3.4 Family `leverage_index` — CR-69, design §8 (quoted, binding)

> `leverage_index` (D-1 deliverable, absorbs CR-69) is defined as **`domain_load_bearing_weight ÷ capability(shadbala_percentile, dignity, varga_ratification)`, forward-weighted by dasha runway** — the number remedy and intervention-timing rank on (a graha that is load-bearing, weak, and about to run a long MD is the highest-leverage target, and the window is the years *before* its dasha opens).

Concrete v1 computation (formula_version `leverage_index_v1`; every operand from stored data):

- `domain_load_bearing_weight(graha, domain)` = normalized sum over: lordship of domain-primary houses in D1 (wealth: 2, 11; weight 1.0 each), domain kārakatva (wealth: Jupiter; weight 0.75), occupancy of domain-primary houses (weight 0.5), participation in a fired domain yoga (from `ga_yoga_firings`; weight 0.75). Weights → constants table. Normalize by the max across grahas so the top load-bearer = 1.0.
- `capability(graha)` = mean of: shadbala percentile within this chart (from `graha_shadbala_total` facts, ranked across the 9 — percentile ∈ (0,1]), dignity score (map exalted 1.0 / mooltrikona 0.85 / own 0.75 / friend 0.6 / neutral 0.5 / enemy 0.35 / debilitated 0.25 — constants table), and the graha's `ratification_factor` for the domain rescaled from [0.6,1.4] to [0,1] (`(rf − 0.6)/0.8`). Floor capability at 0.1 (constants) to avoid division blowups.
- `dasha_runway_weight` = from `chart_dashas` (Vimśottarī L1/L2, the chart's default ayanamsha): if the graha's next/current MD (look forward 30 years from `computed_at`) has duration `Y` years starting in `S` years, weight `= 1.0 + 0.5 × (Y/20) × max(0, 1 − S/15)` — a long MD starting soon maximizes it. Constants table again.
- `leverage_index = domain_load_bearing_weight ÷ max(capability, floor) × dasha_runway_weight`.
- **Type-specimen acceptance (CR-69/CR-60, 482012f1/wealth):** Venus (2L, weakest shadbala 4.64, 20-year MD from 2034) MUST rank #1 by leverage_index among the 7 classical grahas for domain=wealth. If it doesn't, your operands are wrong — debug against CR-71's verified numbers (shadbala order: Sun 8.47 > Saturn 7.83 > Jupiter 7.80 > Mercury 7.55 > Moon 5.65 > Mars 5.57 > Venus 4.64).

## 4. What ga_vichara does NOT contain

No yoga/dosha detection (Lane 3 — stays in ga_yoga/ga_structural detector registry). No MSR/salience changes (Lane 4 reads these rows). No CGM metrics, mechanism objects (D-2). No timing curves (D-3). No serving tool (Lane 5 adds the face). No LLM calls (deterministic-first is absolute here).

## 5. Migration (one file — follow the repo skill exactly)

Convention (from `.claude/skills/create-migration/SKILL.md` + verified repo state): numbered files `platform/migrations/NNN_<description>.sql`; latest numbered migration is `366_system_health_canary.sql` → yours is **367 unless a higher number exists when you start — re-run the `ls | sort -n | tail` check**. Wrap in `BEGIN; … COMMIT;`. Idempotent + additive-only: `CREATE TABLE IF NOT EXISTS`, `INSERT … ON CONFLICT DO NOTHING`. **Surgical migrations only — never deploy.yml-auto or bulk migrate.ts** (§N.4, [[feedback-deploy-migrations-silent-noop]]). After authoring, request the `migration-guard` review (per skill step 4).

Contents:
1. `CREATE TABLE IF NOT EXISTS chart_vichara (…)` per §3 column list + PK uuid default, indexes on `(chart_id, ayanamsha_id)`, `(chart_id, vichara_family, domain)`.
2. `CREATE TABLE IF NOT EXISTS brahma_vichara_constants (constant_key text PRIMARY KEY, value_jsonb jsonb NOT NULL, citation text, version text NOT NULL, updated_at timestamptz DEFAULT now())` + seed rows: `ratification_step` 0.2, `ratification_clamp` [0.6,1.4], `operative_vargas` per-domain map, `valence_matrix` full actor×target matrix with citations, `dignity_score_map`, `leverage_weights`, `consistency_weights`. All `ON CONFLICT (constant_key) DO NOTHING` (L0 upsert idempotency §N.3).
3. `asset_registry` insert:
```sql
INSERT INTO asset_registry (asset_id, display_name, layer, count_sql, target_floor)
VALUES ('ga_vichara', 'Gaṇita — Vichāra (judged structure)', 'L1',
        'SELECT COUNT(*) FROM chart_vichara WHERE chart_id = $1', 0)
ON CONFLICT (asset_id) DO NOTHING;
UPDATE asset_registry SET depends_on = '["ga_structural","ga_strength","ga_dashas","ga_yoga"]'::jsonb,
       has_substeps = true
WHERE asset_id = 'ga_vichara';
```
(**Check the real column types/names on `asset_registry` first** — `SELECT column_name, data_type FROM information_schema.columns WHERE table_name='asset_registry'` or read migration 223/366 — depends_on may be text[] not jsonb; `sort_order` should place ga_vichara after ga_structural. Match reality, not this sketch.)
4. `target_floor` stays 0 — **floors are aspirational, not gates** (§N.4): after the first successful build you may UPDATE target_floor to the achieved count in a follow-up migration; never pad rows to hit a number.
5. `count_sql` is the cockpit's truth (§N.4 "the L1 trap": stats read `count_sql`, NOT `asset_throughput`) — it must be chart-scoped exactly as above.

## 6. Tests

Unit (pure functions, no DB): valence matrix lookup incl. the 8L→2H = strong_malefic anchor; ratification_factor arithmetic incl. clamps at both ends (n_agree−n_oppose = +3 → 1.4, = −3 → 0.6); consistency index vargottama ordering; leverage_index Venus-#1 fixture using CR-71's verified numbers. Integration (if the suite has a DB harness — mirror how ga_yoga tests do it): writer runs on a fixture chart, rows land, `constituent_fact_ids` all resolve against `chart_facts` (a JOIN-count assertion — DEFECT-001 class, must be 0 orphans), delete-then-insert idempotency (run twice → same count).

## 7. Acceptance criteria

- [ ] `ga_vichara` registers (auto-discovery resolves it: `python -c "from pipeline.orchestrator.writers import get_writer; print(get_writer('ga_vichara'))"` or the repo equivalent) and appears in `asset_registry` with real `depends_on`.
- [ ] Runs via the orchestrator on **482012f1** and on **1c826d5a-41cb-4450-b4dc-59d440e5f75a** (Abhinandan) without error, per-ayanamsha substeps, > 0 rows in every family for both charts. (Executed by the CONDUCTOR's rebuild protocol, not ad hoc by you — your integration test may run the writer directly on a dev DB.)
- [ ] Every `ratification_factor` value in `chart_vichara` ∈ [0.6, 1.4]; every valence `value_num` ∈ {−1.0, −0.5, 0.0, +0.5, +1.0}.
- [ ] 482012f1 specimens: 8L-Mars→H2 valence row = `strong_malefic`; D9 divergence rows fire for Venus + Saturn (wealth); Venus = #1 wealth leverage_index; Mercury consistency > non-vargottama peers.
- [ ] 0 orphan `constituent_fact_ids`; idempotent re-run stable; suite green; migration passes `migration-guard`.
- [ ] Zero constants-as-literals for step/clamp/operative-sets/matrix — all read from `brahma_vichara_constants`.

## 8. Known traps

- **CR-54's original text is superseded** — implement the §I.1 AMENDED direction (actor lordship × target class), not "extend link_type vocabulary".
- **§N.5 (MSR drift trap)**: never restate an L1 computed value — reference `fact_id` and inherit. If your derivation disagrees with a stored L1 fact, that is a halt-worthy bug to report, not a divergence to store.
- **B.10**: no new astronomical computation. If a varga position you want isn't stored, you mark the gap in `value_jsonb.known_gaps` and move on — you do not compute it.
- **CR-23 (NB doctrine)** is DEFERRED-EXPLICIT pending native ruling — ga_vichara consumes NBRY facts as stored; it does not adjudicate them.
- **The dead phantom**: chart_id `362f9f17-…` must never be written or used in fixtures (CLAUDE.md §B).
- **Ratification voting**: D1 is the reference, not a voter — do not count D1 in n_agree (a subtle double-count that shifts every factor by +0.2).

## 9. Anti-scope

No orchestrator changes; no MSR edits (Lane 4); no detectors (Lane 3); no serving tools (Lane 5); no CGM/mechanism (D-2); no Kāla Taraṅga (D-3); no calibration (D-4); no chart rebuilds or prod deploys (CONDUCTOR).

## 10. Done-definition / handback

Worktree branch: migration + writer + adapter + tests, suite green, migration-guard sign-off. Report: table DDL as landed, seeded constant keys, per-family row counts from your dev-DB run on 482012f1, the four specimen assertions' results, §7 checklist. Lanes 3 and 4 build on your merged commit — flag it.
