---
artifact: CLAUDECODE_BRIEF_GANITA_NAMING_RECONCILIATION_v1_0.md
canonical_id: GANITA_NAMING_RECONCILIATION
version: 1.0
status: READY_FOR_AUTONOMOUS_EXECUTION
authored_by: Cowork (planning) 2026-06-09
authored_for: Claude Code in Antigravity IDE
scope: L1 Gaṇita canonical naming — asset_registry IDs + code consumers + governance docs
delivery_model: 2 sequenced CC pastes (DB+code, then docs), plan-then-execute
mirrors: CLAUDECODE_BRIEF_BRAHMAGYAN_NAMING_RECONCILIATION_v1_0.md (the proven L0 template)
---

# Gaṇita (L1) Naming Reconciliation — Master Plan v1.0

## §0 — Why this brief exists + the decided shape

We are aligning the **L1 Gaṇita** asset names to the same convention L0 Brahmagyan now uses:
a short, layer-prefixed `asset_id`. L0 changed `brahmagyan.kalapancanga` → `bg_ephemeris`
across the project. L1 does the exact parallel: **`ganita.*` → `ga_*`**.

**Decided scope (native, 2026-06-09):**
- **Prefix: `ga_`** (Gaṇita) — already the documented convention in the L0 brief
  (`CLAUDECODE_BRIEF_BRAHMAGYAN_NAMING_RECONCILIATION_v1_0.md` line 46: *"matches `ga_dashas`,
  `bo_signals`, `ka_timeline`"*) and line 54 (`ga_sensitive`).
- **Depth: asset IDs ONLY.** Exactly what L0 did — rename the `asset_registry.asset_id`
  values; **do NOT rename the physical tables.** `ganita_positions`, `chart_divisionals`,
  `chart_panchanga`, `ganita_dashas`, the `l1_*` tables — all keep their current names. Only
  the registry's logical `asset_id` (and the code/docs that reference it) changes.

This means the blast radius is small and the change is non-destructive to data: it is a
registry relabel + a handful of code-string updates, not a schema migration.

## §1 — Locked canonical naming (the 8 Gaṇita assets)

These 8 assets ARE the L1 Gaṇita layer. Sanskrit display names and backing tables are
**unchanged from the current registry** — only the `asset_id` short-forms are new.

| sort | Sanskrit (display, unchanged) | English (unchanged) | OLD asset_id | **NEW asset_id** | backing table (UNCHANGED) | active? |
|---|---|---|---|---|---|---|
| 1 | Graha-sthāna | Positions | `ganita.graha_sthana` | **`ga_positions`** | `ganita_positions` | ✓ |
| 2 | Varga | Divisional charts | `ganita.varga` | **`ga_vargas`** | `chart_divisionals` | ✓ |
| 3 | Daśākrama | Vimshottari dasha | `ganita.dasakrama` | **`ga_dashas`** | `ganita_dashas` | ✓ |
| 4 | Balatva | Strength tables | `ganita.balatva` | **`ga_strength`** | (null — awaits table) | ⊘ |
| 5 | Sūkṣmabindu | Sensitive points | `ganita.suksmabindu` | **`ga_sensitive`** | (null — awaits table) | ⊘ |
| 6 | Pañcāṅga-janma | Birth panchanga | `ganita.pancanga_janma` | **`ga_panchanga`** | `chart_panchanga` | ✓ |
| 7 | Sāḍesātī | Sade Sati periods | `ganita.sade_sati` | **`ga_sade_sati`** | (null — awaits table) | ⊘ |
| 8 | Tājaka | Tajaka Varshaphal | `ganita.tajaka` | **`ga_tajaka`** | (null — awaits table) | ⊘ |

**New-id rationale (concept-noun, matches L0):** `ga_dashas` + `ga_sensitive` are the exact
spellings the L0 brief already committed; the rest follow the same "English concept noun"
rule (`ga_positions`, `ga_vargas`, `ga_strength`, `ga_panchanga`, `ga_sade_sati`, `ga_tajaka`).
Sanskrit stays as the cockpit display name; `asset_id` is the English concept — identical to
how `bg_rules` kept "Sūtravālī" as display.

> **Note — `ga_sensitive` overlap.** The L0 reconciliation (`§2`) said the dropped
> `brahmagyan.sensitive_point_catalog` "already exists as `ga_sensitive`" in L1. Confirm during
> §3.1 inventory that there is exactly ONE `ga_sensitive` (this asset, sort 5) and no stray
> duplicate from that L0 drop. If a duplicate exists, halt and report — do not silently merge.

## §2 — What is explicitly NOT changing

- **No physical table renamed.** Zero `ALTER TABLE … RENAME`. Data untouched.
- **No `count_sql` / `target_table` value changed** (they point at physical tables, which keep
  their names). Only the `asset_id` column value and code references to it change.
- **No Sanskrit/English display strings changed.**
- **No L0, L2–L5 asset touched.**
- **No relationship to the L1 data wipe** (`CLAUDECODE_BRIEF_L1_DATA_WIPE_v1_0.md`): the wipe
  empties rows; this renames logical ids. Either order is safe; recommended order is **rename
  first, then wipe** so post-wipe verification reads the final `ga_*` ids.

## §3 — File / surface inventory (regenerate at open)

### §3.0 — Inventory commands (run FIRST; act on regenerated output, not this list)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# OLD asset_id usage (the rename sources)
grep -rn "ganita\.\(graha_sthana\|varga\|dasakrama\|balatva\|suksmabindu\|pancanga_janma\|sade_sati\|tajaka\)" \
  --include="*.ts" --include="*.tsx" --include="*.py" --include="*.md" --include="*.sql" \
  --include="*.json" --include="*.yaml" . | grep -v node_modules | grep -v ".next/" \
  > /tmp/ganita_oldid_usage.txt

# Any pre-existing ga_* usage (catch collisions / partial prior work)
grep -rn "ga_\(positions\|vargas\|dashas\|strength\|sensitive\|panchanga\|sade_sati\|tajaka\)" \
  --include="*.ts" --include="*.tsx" --include="*.py" --include="*.md" --include="*.sql" \
  --include="*.json" --include="*.yaml" . | grep -v node_modules | grep -v ".next/" \
  > /tmp/ganita_newid_usage.txt

# DB: current ganita rows
psql "$DB_URL" -c "SELECT asset_id, sort_order, target_table, is_active FROM asset_registry WHERE layer='ganita' ORDER BY sort_order;"
```

### §3.1 — Known surfaces at authoring time (confirm against §3.0 output)

| File | Edit |
|---|---|
| `platform/scripts/seed/asset_registry_seed.ts` | REWRITE the 8 `ganita.*` `asset_id:` values → `ga_*` (table below). Nothing else in those entries changes. |
| `platform/src/lib/retrieve/pyhora_natal_positions.ts` | EDIT — `ganita.graha_sthana` → `ga_positions` |
| `platform/src/lib/retrieve/pyhora_dasha_periods.ts` | EDIT — `ganita.dasakrama` → `ga_dashas` |
| DB `asset_registry` (per §4 migration) | DELETE 8 `ganita.*` rows + INSERT 8 `ga_*` rows |
| Governance docs (Phase 2) | `CLAUDE.md §D` snapshot, `CURRENT_STATE_v1_0.md §2`, `SESSION_LOG.md`, and any A3–A9 spec / handoff referencing `ganita.*` ids |

The §3.0 grep is authoritative — if it surfaces files beyond the three above (likely some
`00_ARCHITECTURE/*` docs + `CONDUCTOR` yaml), include them in the Phase-2 docs commit.

## §4 — Phase 1 — DB + code rename (one CC paste)

**Goal:** prod cockpit shows the 8 L1 assets under `ga_*` ids; the seed script + 2 retrieve
consumers agree, so future re-seeds are idempotent.

### §4.1 — DB migration

Author `platform/supabase/migrations/<NEXT>_ganita_naming_reconciliation.sql`:

```sql
-- Gaṇita (L1) naming reconciliation — relabel asset_registry ids ganita.* → ga_*.
-- Asset IDs ONLY. No physical table renamed. Reversible via the down-block.
BEGIN;

DELETE FROM asset_registry WHERE layer='ganita' AND asset_id IN (
  'ganita.graha_sthana','ganita.varga','ganita.dasakrama','ganita.balatva',
  'ganita.suksmabindu','ganita.pancanga_janma','ganita.sade_sati','ganita.tajaka'
);

-- Re-insert the SAME 8 assets with ga_* ids. All other columns identical to the
-- current asset_registry_seed.ts ganita block (sanskrit/english/target_table/count_sql/
-- size_sql/volume_explanation/depends_on/scope/is_active preserved verbatim).
INSERT INTO asset_registry
  (asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
   storage_type, target_table, count_sql, size_sql, target_floor,
   expected_volume_formula, volume_explanation, depends_on, scope, is_active) VALUES
  ('ga_positions','ganita',1,'Graha-sthāna','Positions',
   'Natal graha positions per ayanamsha (sidereal/tropical longitude, sign, nakshatra)',
   'postgres_table','ganita_positions',
   'SELECT count(*) FROM ganita_positions WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''ganita_positions'')',
   NULL,'GRAHAS * AYANAMSHAS',
   '9 grahas × ayanamsha count — one position row per graha per ayanamsha',
   ARRAY[]::text[],'per_chart',true),

  ('ga_vargas','ganita',2,'Varga','Divisional charts',
   'D1–D60 divisional chart positions per ayanamsha',
   'postgres_table','chart_divisionals',
   'SELECT count(*) FROM chart_divisionals WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''chart_divisionals'')',
   NULL,'VARGAS * GRAHAS * AYANAMSHAS',
   '60 vargas × 9 grahas × ayanamsha count — structural',
   ARRAY[]::text[],'per_chart',true),

  ('ga_dashas','ganita',3,'Daśākrama','Vimshottari dasha',
   'Vimshottari dasha timeline: MD × AD × PD rows per ayanamsha',
   'postgres_table','ganita_dashas',
   'SELECT count(*) FROM ganita_dashas WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''ganita_dashas'')',
   NULL,'(9 + 81 + 729) * AYANAMSHAS',
   'Vimshottari tree: 9 MD + 81 AD + 729 PD = 819 rows × ayanamsha count — structural',
   ARRAY[]::text[],'per_chart',true),

  ('ga_strength','ganita',4,'Balatva','Strength tables',
   'Shadbala, ashtakavarga, and bhava bala per ayanamsha',
   'postgres_table',NULL,NULL,NULL,NULL,
   '(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS',
   'Shadbala: 6 scores × 9 grahas; ashtakavarga: 8 tables × 9 grahas × 12 signs; bhava bala: 6 scores × 12 bhavas — all × ayanamshas',
   ARRAY[]::text[],'per_chart',false),

  ('ga_sensitive','ganita',5,'Sūkṣmabindu','Sensitive points',
   'Per-chart sensitive point positions computed from the catalog × ayanamshas',
   'postgres_table',NULL,NULL,NULL,NULL,
   'ACTUAL(bg_reference) * AYANAMSHAS',
   'Derived from the reference library count × ayanamshas; awaits dedicated per-chart table',
   ARRAY['bg_reference']::text[],'per_chart',false),

  ('ga_panchanga','ganita',6,'Pañcāṅga-janma','Birth panchanga',
   'Natal panchanga (tithi, vara, nakshatra, yoga, karana) per ayanamsha',
   'postgres_table','chart_panchanga',
   'SELECT count(*) FROM chart_panchanga WHERE chart_id = $1',
   'SELECT pg_total_relation_size(''chart_panchanga'')',
   NULL,'AYANAMSHAS',
   'One panchanga row per ayanamsha — structural',
   ARRAY[]::text[],'per_chart',true),

  ('ga_sade_sati','ganita',7,'Sāḍesātī','Sade Sati periods',
   'Saturn transit-over-natal-Moon Sade Sati + Dhaiya window calculations per ayanamsha',
   'postgres_table',NULL,NULL,NULL,NULL,'AYANAMSHAS',
   'One row per ayanamsha for the native''s Sade Sati window; awaits dedicated table',
   ARRAY[]::text[],'per_chart',false),

  ('ga_tajaka','ganita',8,'Tājaka','Tajaka Varshaphal',
   'Annual chart (Varshaphal) and Tajaka aspects per ayanamsha',
   'postgres_table',NULL,NULL,NULL,NULL,NULL,
   'Writer output — row count depends on aspect configurations found; awaits dedicated table',
   ARRAY[]::text[],'per_chart',false);

COMMIT;

-- DOWN (manual rollback): DELETE FROM asset_registry WHERE layer='ganita' AND asset_id LIKE 'ga_%';
--   then re-run the prior asset_registry_seed.ts ganita block to restore ganita.* ids.
```

> Before writing the migration, **verify the current column values** of the live `ganita` rows
> against the INSERT above (`SELECT * FROM asset_registry WHERE layer='ganita'`). If any
> `target_floor`, `is_active`, or `volume_explanation` on prod differs from this brief (e.g. a
> later session activated `ga_strength`), preserve the **live** value, not the brief's — the
> rename must not silently change activation or floors. ([[feedback-floors-are-aspirational-not-gates]])

### §4.2 — Code consumers

- `platform/scripts/seed/asset_registry_seed.ts` — change the 8 `asset_id:` strings in the
  GANITA block to the `ga_*` forms (everything else in those entries stays).
- `platform/src/lib/retrieve/pyhora_natal_positions.ts` — `ganita.graha_sthana` → `ga_positions`.
- `platform/src/lib/retrieve/pyhora_dasha_periods.ts` — `ganita.dasakrama` → `ga_dashas`.
- Any additional consumer surfaced by §3.0 grep.

### §4.3 — Verification `[verify-against: prod]`

```bash
psql "$DB_URL" -c "SELECT asset_id, sort_order, target_table, is_active FROM asset_registry WHERE layer='ganita' ORDER BY sort_order;"
# Expect: ga_positions, ga_vargas, ga_dashas, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati, ga_tajaka
# No 'ganita.*' rows remain. Exactly 8 rows. target_table values UNCHANGED.

# Cockpit reflects the new ids:
curl -s -b "__session=$NATIVE_SESSION" "https://madhav.marsys.in/api/cockpit/stats?chart_id=$CHART_ID" \
  | jq '.data.assets[] | select(.layer=="ganita") | {id: .asset_id, state, rows: .actual_rows}'
```

Acceptance: 8 `ga_*` rows on prod, 0 `ganita.*` rows, `target_table`/`count_sql` unchanged,
cockpit renders the L1 layer with the new ids and the same Sanskrit display names, seed re-run
is idempotent (re-running `asset_registry_seed.ts` produces no diff).

## §5 — Phase 2 — Governance + spec docs (one CC paste, after Phase 1 green)

- Update `CLAUDE.md §D` snapshot table: add `GANITA_NAMING_RECONCILIATION` canonical artifact.
- Append `CURRENT_STATE_v1_0.md §2` state block: L1 ga_ reconciliation closed.
- Append `SESSION_LOG.md`.
- Replace `ganita.*` id references with `ga_*` in any A3–A9 spec / `L1_GANITA_BUILD_CAMPAIGN_
  HANDOFF` / CONDUCTOR yaml surfaced by §3.0 (docs only — physical-table mentions stay).

## §6 — Rollback

- Phase 1: run the migration DOWN block + re-run prior seed; `git revert` the code commit.
  Cockpit reverts to `ganita.*`. ~5 min. Data never touched, so zero data risk.
- Phase 2: `git revert` the docs commit. No runtime impact.

Atomic boundary: never deploy Phase 2 without Phase 1.

## §7 — Branch + delivery

- Branch: `feature/ganita-naming-reconciliation` (cut from main).
- 2 commits (Phase 1 DB+code, Phase 2 docs); 1 PR; merge after Phase 1 verifies green on prod.
- Merge-verify before any "done" claim ([[feedback-phase-sealed-needs-merge-verification]]):
  `gh pr view <N> --json mergeCommit,state`.
- Recommended sequencing vs the wipe: **rename → wipe → A3–A9 review/build.**

---

*End of brief. Executor: run §3.0 inventory first, reconcile live column values per §4.1 note,
then Phase 1 → verify → Phase 2.*
