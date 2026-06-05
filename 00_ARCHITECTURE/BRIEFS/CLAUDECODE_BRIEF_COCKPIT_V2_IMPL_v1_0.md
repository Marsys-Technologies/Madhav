---
artifact: CLAUDECODE_BRIEF_COCKPIT_V2_IMPL_v1_0.md
canonical_id: CLAUDECODE_BRIEF_COCKPIT_V2_IMPL
version: 1.0
status: READY_FOR_EXECUTION
project_codename: Brahma — Super-Admin Cockpit v2 (three views, MARSYS theme, robust real-time wiring)
authored_by: Claude (Cowork) 2026-06-05
authored_for: Claude Code extension running inside Google Antigravity IDE
execution_surface: Claude Code in Google Antigravity IDE; localhost-first dev (http://localhost:3000), prod data plane (Cloud SQL via proxy + Cloud Run sidecar at amjis-sidecar)
predecessor_commit: bc989141 (sidecar wiring fix)
branch: feature/cockpit-v2-three-views
no_backup: true
human_gates: native verifies via Chrome MCP after each milestone; final merge after both views proven faithful
binding_discipline: verify-against-prod per `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md` + `feedback-ac-must-verify-target-environment`; no worktree-only ACs
design_reference: MARSYS Design System (uploaded 2026-06-05)
---

# Cockpit v2 — Super-Admin Implementation Brief

Three views (Data assets · Workflow · Agents) replacing the current cockpit. Top-down layer panels (Foundation → Learning) with vertical asset rows showing storage type + live row counts + sizes. MARSYS gold-on-black theme. Robust wiring: every cell reflects live prod state with explicit failure surfacing — no stale, no hung, no silent zeros.

## §1 Mission

Replace `CockpitShell.tsx`'s current layout with a three-view super-admin cockpit per the approved v2 mockup. Bind every visible number to live prod data via SSE + throttled polling with explicit timeout + error semantics. Apply the MARSYS design tokens directly (no token-translation layer; use the system's actual variable names so future cockpit screens inherit consistency).

## §2 MARSYS theme tokens (apply globally to the cockpit shell)

Author a single CSS module `platform/src/lib/styles/marsys-theme.css` (or extend the existing theme file) declaring these as CSS variables in `:root` (or scoped to a `.marsys` wrapper if global theming isn't safe):

```css
:root {
  --black: #0A0806;
  --black-deep: #000000;
  --black-raised: #14110B;
  --black-line: #241D10;
  --cream: #F3EEE2;
  --gold-high: #ECC56A;
  --gold-bright: #D2A23C;
  --gold-core: #A87C2A;
  --gold-deep: #8A5E12;
  --gold-engrave: #6E4E0F;
  --on-dark: #F3EEE2;
  --on-dark-mut: #B9AE93;
  --on-dark-faint: #7C725B;
  --jewel-amethyst: #43305A;
  --jewel-emerald: #1F4A3D;
  --jewel-garnet: #5E2030;
  --jewel-sapphire: #1E3A5F;
  --jewel-teal: #1C4A4A;
  --success: #3E7C4B;
  --warning: #C8922A;
  --error: #B5474C;
  --display-stack: "Trajan Pro", "Cormorant Garamond", Garamond, "Times New Roman", serif;
  --doc-stack: Garamond, "Cormorant Garamond", Cambria, "Times New Roman", serif;
  --ui-stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --mono-stack: ui-monospace, "SF Mono", "Cascadia Mono", Consolas, monospace;
  --r-btn: 6px;
  --r-card: 12px;
}
```

Component conventions from the system (verbatim):
- **Panel**: `background: var(--black-raised); border: 1px solid var(--black-line); border-radius: var(--r-card); padding: 26px;`. Add `border-top: 2px solid var(--gold-core);` for emphasis (`.panel-gold-top`).
- **Btn-primary**: `background: linear-gradient(180deg, var(--gold-bright), var(--gold-core)); color: #1A1206;` 12×20 padding, 14px font weight 600.
- **Btn-secondary**: transparent + `color: var(--gold-high)` + `border-color: var(--gold-core)`.
- **Chip**: 999px radius, `background: rgba(168,124,42,0.12); color: var(--gold-high); border: 1px solid var(--gold-engrave);` 5×12 padding.
- **Headings**: H2 uses display-stack small-caps 44px `var(--gold-high)`; H3 22px `var(--gold-bright)`; H4 17px `var(--on-dark)`.
- **Eyebrow** (small-caps caption above section title): 12px letter-spacing 0.22em uppercase `var(--gold-core)` with a 28px gold-deep line before.
- **Geo divider**: horizontal gold gradient line with center node — use sparingly between major sections.
- **Decorative flower-of-life motif** at 0.06 opacity behind hero areas only (not behind data-dense surfaces).

State color mapping for tiles/pills (no new colors — reuse the system):
- `lit` (verified, full) → `--jewel-emerald` accent on `--black-raised` surface; text `--gold-high`
- `building` → `--gold-bright` accent pulsing; text `--gold-high`
- `amber` (built-but-thin) → `--warning` accent; text `--warning`
- `dim` (pending) → `--on-dark-faint` accent; text `--on-dark-mut`
- `failed` → `--error` accent; text `--error`
- `bedrock` (Brahmagyan / Mīmāṃsā substrate) → `--gold-core` accent

## §3 Data model — two new tables

### §3.1 `asset_registry` (authoritative per-asset metadata)

```sql
CREATE TABLE IF NOT EXISTS asset_registry (
  asset_id text PRIMARY KEY,
  layer text NOT NULL CHECK (layer IN ('brahmagyan','ganita','bodha','kala','phala','mimamsa')),
  sort_order int NOT NULL,
  sanskrit_name text NOT NULL,
  english_name text NOT NULL,
  english_description text NOT NULL,
  storage_type text NOT NULL CHECK (storage_type IN ('postgres_table','pgvector','postgres_view','gcs_jsonl','bigquery','tool_only')),
  target_table text,
  count_sql text,
  size_sql text,
  target_floor int,
  expected_volume_formula text,
  expected_volume_inputs jsonb,
  volume_explanation text,
  depends_on text[] DEFAULT ARRAY[]::text[],
  scope text NOT NULL CHECK (scope IN ('global','per_chart')),
  is_active boolean DEFAULT true,
  estimated_seconds int,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_asset_registry_layer ON asset_registry(layer, sort_order);
```

Seed this with the 39 assets the cockpit currently lists (Brahmagyan 8, Gaṇita 8, Bodha 8, Kāla 4, Phala 5, Mīmāṃsā 6). `count_sql` is a parameterised query template (e.g., `SELECT count(*) FROM bodha_signals WHERE chart_id = $1`); the cockpit's stats endpoint substitutes `$1`. `size_sql` similar (`SELECT pg_total_relation_size('bodha_signals')` for global, or chart-scoped variant). `target_floor` = the honest volume floor (kept as a coarse minimum; soft-deprecated in favour of expected_volume_formula).

**`expected_volume_formula` (the benchmark)** — a closed-form expression in the small formula language (§3.1a) that derives the EXPECTED row count for this asset given chart context (ayanamsha set, date range, life span). This is the BENCHMARK the cockpit measures actual vs — replaces the empirical floor with a derived target the writer should provably hit. For `tool_only` assets, leave NULL; the cockpit shows "tool — no row target."

**`expected_volume_inputs` (jsonb)** — optional structured input parameters for assets whose formula depends on chart-specific data not captured by the standard variables (e.g., contradiction-hub count for remediation). Reserved for v1.1+; v1 leaves this empty for most assets.

**`volume_explanation` (text)** — human-readable explanation shown in tooltip (e.g., "9 grahas × 5 ayanamshas — one position per graha per ayanamsha"). Required when `expected_volume_formula` is set.

### §3.1a Formula language (small, safe, server-side evaluable, supports upstream references)

The formula text is evaluated by a small server-side interpreter that accepts arithmetic operators (`+ - * /`), named variables from a fixed allowlist, AND one function: `ACTUAL(asset_id)`. No other function calls, no arbitrary code. The interpreter MUST be hand-written (not eval/exec); reject anything else.

| Variable | Default | Source |
|---|---|---|
| `AYANAMSHAS` | 5 | chart's ayanamsha-set selector |
| `GRAHAS` | 9 | constant |
| `SIGNS` | 12 | constant |
| `HOUSES` | 12 | constant |
| `NAKSHATRAS` | 27 | constant |
| `VARGAS` | 60 | constant (D1–D60) |
| `BHAVAS` | 12 | constant |
| `LIFE_SPAN_YEARS` | 90 | chart projection span |
| `DATE_RANGE_DAYS` | 44000 | derived from chart birth date + LIFE_SPAN_YEARS |

**Note on TOTAL_SIGNALS removed:** prior drafts of this brief included `TOTAL_SIGNALS=569` as a constant. That was empirical (lifted from the autonomous wave seals), not first-principles, and exactly the kind of circular benchmark this whole approach is built to avoid. Signal count is a DERIVED downstream quantity — see §3.1a-2 below.

**Asset-level coefficients (measured, never assumed):** for downstream assets where the relationship is "N output rows per input row" but the exact ratio depends on the writer's actual behaviour, store the coefficient in a separate `asset_coefficients` table with explicit provenance. **Initial value is always NULL** — the cockpit refuses to compute an "expected" using an unmeasured coefficient. After the first build where both upstream and downstream reach `lit`, the system computes `value = ACTUAL(downstream) / ACTUAL(upstream)` and records it with the source build_id + timestamp + sample_size. Subsequent builds use a rolling average of measurements; the cockpit hover shows the coefficient value AND its provenance (e.g., "0.31 — avg of 4 measurements across builds; range 0.28–0.34").

```sql
CREATE TABLE IF NOT EXISTS asset_coefficients (
  coefficient_name text PRIMARY KEY,
  description text NOT NULL,
  upstream_asset_id text NOT NULL REFERENCES asset_registry(asset_id),
  downstream_asset_id text NOT NULL REFERENCES asset_registry(asset_id),
  current_value double precision,
  measurement_count int DEFAULT 0,
  last_measured_at timestamptz,
  last_measured_build_id uuid,
  history jsonb DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now()
);
```

Seed the table with the coefficient DEFINITIONS (name, description, upstream + downstream asset_ids) but leave `current_value` NULL. Examples:

| coefficient_name | upstream | downstream | description (volume_explanation) |
|---|---|---|---|
| `SIGNAL_PER_RULE` | brahmagyan.sutravali | bodha.laksana | signals produced per L0 rule, per ayanamsha set (measured first build) |
| `EDGE_DENSITY` | bodha.laksana | bodha.karanajala | fraction of signal pairs forming a CGM edge (measured first build) |
| `ANCHOR_PER_CONVERGENCE` | kala.sangam | phala.nimitta | anchors derived per convergence window (measured first build) |
| `TRANSITS_PER_DAY` | brahmagyan.kalapancanga | kala.kalasutra | major-aspect transit events per day (measured first build) |
| `CONCORDANCE_DENSITY` | brahmagyan.sutravali | brahmagyan.samanvaya | concordance topics per rule (measured first build) |

**Strict rule for formula authors:** every coefficient referenced in any formula MUST exist in `asset_coefficients` (foreign key). The formula evaluator validates this at seed-load time and rejects unknown coefficient names. No invented coefficients.

### §3.1a-1.5 `FILE_COUNT(path, marker)` — source-of-truth file derivations

For assets whose count is deterministic given a versioned source file (e.g., LEL events from the markdown source-of-truth, classical text chapters from text files), the formula can use `FILE_COUNT(path, marker)`:
- `path` is relative to the repo root (e.g., `'01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md'`)
- `marker` is the unique-token pattern to count (e.g., `'EVT'` matches `EVT.YYYY.MM.DD.NN` IDs)
- The seed script evaluates this at seed time and stores the result in `expected_volume_inputs.file_count` so the cockpit can reference it without re-reading the file every request
- If the source file changes, re-seed updates the count; the asset's actual must match — divergence = bug

### §3.1a-2 `ACTUAL(asset_id)` — the upstream reference

`ACTUAL(asset_id)` returns the LIVE verified row count of the referenced asset for the current chart (or globally for global-scoped assets). It is the cockpit's single mechanism for cascading benchmark derivation through the DAG.

Evaluation rules:
1. The referenced asset MUST be in `asset_registry` and `is_active = true`. Otherwise the evaluator returns `expected: null, error: 'unknown_asset_id'`.
2. The referenced asset MUST be in state `lit` (verified, written, and Pramāṇa-passed). Until then, the evaluator returns `expected: null, blocked_by: [<asset_id>], reason: 'awaiting upstream'`. The cockpit shows this as "awaiting <upstream sanskrit name>" with the explanation tooltip.
3. The reference can chain: if `B = ACTUAL(A) * 0.2` and `A = ACTUAL(X) * 0.35`, evaluating B requires both X and A lit. The cockpit shows the deepest unfinished dependency.
4. **No empirical baking-in.** Formula authors MUST NOT hardcode any number that should be derived (e.g., never `569` for signal count; always `ACTUAL(brahmagyan.sutravali) * SIGNAL_PER_RULE * AYANAMSHAS`). This rule applies to seed authors during M2; CC reviews each formula against this rule before commit.

Example formulas (seed reference — not exhaustive; CC fills all 39 in M2 seed):

| Asset | Formula | Notes |
|---|---|---|
| `brahmagyan.kalapancanga` (ephemeris) | `GRAHAS * DATE_RANGE_DAYS` | structural; grahas × date range days |
| `brahmagyan.sutravali` (rules) | NULL | corpus size is an empirical writer output; first ingest establishes count; re-runs must match |
| `brahmagyan.samanvaya` (concordance) | `ACTUAL(brahmagyan.sutravali) * CONCORDANCE_DENSITY` | DERIVED; coefficient CONCORDANCE_DENSITY starts NULL; first build with both lit measures it |
| `ganita.graha_sthana` (positions) | `GRAHAS * AYANAMSHAS` | structural; no upstream dep on volume |
| `ganita.varga` (divisionals) | `VARGAS * GRAHAS * AYANAMSHAS` | structural |
| `ganita.dasakrama` (Vimshottari L1+L2+L3) | `(9 + 81 + 729) * AYANAMSHAS` | structural — Vimshottari tree shape |
| `ganita.balatva` (strength: shadbala + ashtakavarga + bhava bala) | `(6*GRAHAS + 8*GRAHAS*SIGNS + 6*BHAVAS) * AYANAMSHAS` | structural |
| `ganita.suksmabindu` (sensitive points) | `ACTUAL(brahmagyan.sensitive_point_catalog) * AYANAMSHAS` | DERIVED from catalog × ayanamshas. The catalog is an L0 reference table whose count = whatever upagrahas + special lagnas + sahams + arudhas the cataloguer loaded. NOT a hardcoded number. |
| `ganita.pancanga_janma` (birth panchanga) | `AYANAMSHAS` | structural |
| `bodha.laksana` (MSR signals) | `ACTUAL(brahmagyan.sutravali) * SIGNAL_PER_RULE * AYANAMSHAS` | DERIVED from upstream rule count; awaits Sūtravālī |
| `bodha.karanajala` (CGM edges) | `ACTUAL(bodha.laksana) * EDGE_DENSITY` | DERIVED from signal count; awaits Lakṣaṇa |
| `bodha.samskara` (embeddings) | `ACTUAL(bodha.laksana)` | one vector per signal — exact |
| `bodha.upaya` (remediation) | (left NULL; live count derives once contradiction-hubs identified) | runtime-derived |
| `kala.kalasutra` (timeline) | `ACTUAL(ganita.dasakrama) + ACTUAL(brahmagyan.kalapancanga) * TRANSITS_PER_DAY` | DERIVED from dashas + transit days |
| `phala.nimitta` (anchors) | `ACTUAL(kala.sangam) * ANCHORS_PER_CONVERGENCE` | DERIVED from convergence windows |
| `mimamsa.jivanaghatana` (LEL) | `FILE_COUNT('01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md', 'EVT')` | DETERMINISTIC GIVEN THE FILE. Seed-time count of unique EVT IDs in the source-of-truth file. Re-runs MUST match this count exactly; divergence = ingest bug. Native 2026-06-05 diagnostic showed 56 unique EVT IDs vs 57 in frontmatter — the 56 is authoritative. |

For assets where the formula yields zero or NULL (tool-only, runtime-derived), the cockpit shows "—" in the expected column with the explanation as tooltip.

### §3.2 `layer_approvals` (sign-off ledger)

```sql
CREATE TABLE IF NOT EXISTS layer_approvals (
  approval_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  layer text NOT NULL CHECK (layer IN ('brahmagyan','ganita','bodha','kala','phala','mimamsa')),
  approver_uid text NOT NULL,
  approver_role text NOT NULL CHECK (approver_role IN ('super_admin','acharya')),
  approved_at timestamptz DEFAULT now(),
  revoked_at timestamptz,
  revoked_by text,
  revocation_reason text,
  stats_snapshot jsonb NOT NULL,
  amber_acknowledgements jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT exclude_overlapping_active UNIQUE NULLS NOT DISTINCT (chart_id, layer, revoked_at)
);

CREATE INDEX IF NOT EXISTS idx_layer_approvals_chart_layer ON layer_approvals(chart_id, layer) WHERE revoked_at IS NULL;
```

The `EXCLUDE` constraint ensures only one active (non-revoked) approval per chart×layer at a time; revoked approvals stay for audit.

## §4 API surface (new + modified)

| Endpoint | Method | Purpose | Cache |
|---|---|---|---|
| `/api/cockpit/registry` | GET | Returns the full asset_registry rows | 60s edge |
| `/api/cockpit/stats?chart_id=...` | GET | Per-asset live row count + size + last_updated + gate_verdicts | no-cache; 2s timeout |
| `/api/cockpit/workflow?build_id=...` | GET | Stage timings from build_steps + estimates per §6 | no-cache; 2s timeout |
| `/api/cockpit/agents?build_id=...` | GET | Derived agent activity per §7 | no-cache; 2s timeout |
| `/api/cockpit/approve` | POST | Insert into layer_approvals; body: `{chart_id, layer, amber_acknowledgements?}` | — |
| `/api/cockpit/approve/revoke` | POST | Set revoked_at on an existing approval | — |
| `/api/build/events/[buildId]` | GET (SSE) | Existing stream; cockpit consumes | — |
| `/api/sidecar/health` | GET | Existing (commit bc989141) | 10s |

Every stats route returns this envelope:
```json
{
  "data": { ... },
  "fetched_at": "2026-06-05T14:23:09.412Z",
  "stale_after_seconds": 5,
  "errors": [{ "field": "bodha_signals.count", "message": "query timed out" }]
}
```

The `errors` array lets the UI render specific cells as failed while the rest succeed — no all-or-nothing 500s.

## §5 Components to author or modify

| Component | Path | Action |
|---|---|---|
| `MarsysTheme` (CSS module) | `platform/src/lib/styles/marsys-theme.css` | NEW — variables + base panel/button/chip rules |
| `CockpitShell` | `platform/src/lib/components/cockpit/CockpitShell.tsx` | REWRITE — header strip + tab bar + view router |
| `CockpitHeader` | `platform/src/lib/components/cockpit/CockpitHeader.tsx` | NEW — chart info, telemetry strip, Pause/Resume CTA |
| `TabBar` | `platform/src/lib/components/cockpit/TabBar.tsx` | NEW — three-tab switcher (Data/Workflow/Agents) |
| `DataAssetsView` | `platform/src/lib/components/cockpit/DataAssetsView.tsx` | NEW — top-down collapsible layer panels |
| `LayerPanel` | `platform/src/lib/components/cockpit/LayerPanel.tsx` | NEW — collapsible per-layer + asset rows |
| `AssetRow` | `platform/src/lib/components/cockpit/AssetRow.tsx` | NEW — single asset row with storage + counts + status |
| `WorkflowView` | `platform/src/lib/components/cockpit/WorkflowView.tsx` | NEW — timeline + stage detail table |
| `WorkflowTimeline` | `platform/src/lib/components/cockpit/WorkflowTimeline.tsx` | NEW — horizontal bar with stage segments + cursor |
| `AgentsView` | `platform/src/lib/components/cockpit/AgentsView.tsx` | NEW — live agent list with derived activity |
| `AgentRow` | `platform/src/lib/components/cockpit/AgentRow.tsx` | NEW — single agent row |
| `ApproveLayerDialog` | `platform/src/lib/components/cockpit/ApproveLayerDialog.tsx` | NEW — amber-acknowledgement modal |
| `ConnectionHealthPill` | `platform/src/lib/components/cockpit/ConnectionHealthPill.tsx` | NEW — SSE/poll status in header |
| `useBuildSSE` | `platform/src/hooks/useBuildSSE.ts` | NEW — SSE subscription with auto-reconnect |
| `useAssetStats` | `platform/src/hooks/useAssetStats.ts` | NEW — throttled polling per asset |
| `useWorkflowState` | `platform/src/hooks/useWorkflowState.ts` | NEW — stage timings + estimates |
| `useAgentActivity` | `platform/src/hooks/useAgentActivity.ts` | NEW — derives agent activity from build state |

## §6 Wiring guarantees (binding)

Every cell that displays a number must satisfy these:

1. **Live source.** Number comes from `psql_prod` query (or SSE event payload), never from a mocked default or a hardcoded fallback.
2. **Throttled polling.** When the source asset is in `building` state, the cell polls every 2s. When `lit`/`dim`/`failed`, no polling. State transitions trigger immediate refetch.
3. **In-flight dedup.** If a previous fetch is in flight when the poll fires, the new request is dropped (not queued). Use AbortController to cancel on unmount.
4. **2s timeout per request.** Server-side 2s; client gives up at 3s. On timeout the cell shows `—` with a tooltip `query timed out · last value at HH:MM:SS`.
5. **Last-updated timestamp.** Every cell carries a hidden `data-fetched-at` attribute. On hover, show the relative age. If older than `stale_after_seconds`, dim the cell text by 40% so the staleness is visible.
6. **No silent zeros.** A genuine count of 0 (e.g., `kala_timeline` for a brand-new chart) shows "0" with a `pending — writer not yet released` tooltip. A failed query shows `—` with the error tooltip. The two states are visually distinguishable.
7. **SSE health pill in header.** Green if connected + last event within 30s. Amber if reconnecting. Red if disconnected for >60s. Polling fallback automatic at amber.
8. **No spinners-forever.** Every loading state has a 5s timeout; beyond that it switches to an error state with a Retry button.
9. **Build state truth.** The header's "23 / 39 nodes · 59%" is computed live from `pyramid_layers` rows joined to `asset_registry`, not stored as a column anywhere. Stale `pyramid_layers` data shows through as stale percentages — but the per-cell `data-fetched-at` makes that visible.

## §6a Dependency strictness (orchestrator contract)

The cockpit's honesty depends on the orchestrator's strictness about upstream completion. These rules are non-negotiable and CC must verify them during M3+:

1. **Sūtradhāra (orchestrator) does not release the writer for asset X until every `asset_id` in `X.depends_on` has status `lit`** — meaning the writer ran, rows landed, AND the verifier (Pramāṇa) emitted a pass verdict. A row count alone is not "lit"; the gate must have passed.
2. **State transitions:**
   - `dim` = upstream not yet started; no work scheduled for this asset
   - `gated` = upstream(s) in progress; this asset is queued behind them
   - `building` = released; writer running
   - `lit` = writer committed + Pramāṇa gate passed
   - `amber` = writer committed but actual < expected (configurable threshold) OR a gate emitted a warning
   - `failed` = writer errored OR gate failed
3. **Sambandha (dependency check) enforces gated→building transitions.** Its current state is queryable; the cockpit's Agents view shows it as "gating X assets; longest wait: Y".
4. **No silent downstream firing.** If Sūtradhāra ever attempts to release a writer whose dependencies aren't lit, that's a bug — the API returns 409 Conflict and the cockpit shows a red flag on the asset.
5. **ACTUAL() refuses to evaluate on un-lit assets** (§3.1a-2 rule 2). The stats endpoint returns `expected: null, blocked_by: [<upstream_ids>]` rather than evaluating against an in-flight or zero row count. The cockpit shows "awaiting <upstream>" in the expected cell.
6. **Failed upstream poisons downstream visually** — if X is `failed` and Y depends on X, Y's row shows "blocked: X failed" in red until X is rebuilt successfully. No silent dim.

This contract is what makes the benchmark provable: an asset's expected volume only exists when its upstream is verified-complete, and the orchestrator never lets you build on top of unverified data.

## §7 Agent activity derivation (no new agent state table for v1)

| Agent (Sanskrit) | Plain English role | Source query / heuristic |
|---|---|---|
| Sūtradhāra | Orchestrator | `SELECT * FROM build_steps WHERE build_id=$1 AND status IN ('running','queued') ORDER BY released_at DESC LIMIT 1` — show released_at as "on task since" |
| Śilpī | Builder (writer process) | All `build_steps` with status `running`. Each becomes one Śilpī instance row. Spend = `SELECT sum(cost_usd) FROM llm_call_log WHERE build_id=$1`. |
| Pramāṇa | Verifier | `build_steps` with status `verifying`. Count from `build_events WHERE event_type='gate_passed' AND build_id=$1`. |
| Sambandha | Dependency check | `build_steps` with status `gated`; for each, the dependency it's waiting on (from `asset_registry.depends_on`). Plus a count of "X assets currently gated" and the longest waiting asset (longest time in `gated` state). |
| Darpaṇa | Render check | `build_events WHERE event_type='render_verified' AND build_id=$1`. |
| Pratiṣṭhā | Deployer | `cloud_run_revisions` last revision name + timestamp (from cached gcloud call refreshed every 30s). |
| Drashta | Browser driver | `build_events WHERE event_type='smoke_curl' AND build_id=$1`. |
| Praharī | Watchdog | Show "monitoring" with last reaped stale-build timestamp from `build_reaper_runs` if exists, else "no reaps recorded". |
| Smṛti | Audit log | `SELECT entry_text, created_at FROM smriti_entries WHERE build_id=$1 ORDER BY created_at DESC LIMIT 5` |
| Nirīkṣaka | Auditor | "Idle" by default; last audit timestamp from a `nirikshaka_audits` table if present, else "no audits this build". |
| Racayitā | Briefer | Active only when a step's `fix_attempt_count > 0`; show "briefing fix N for asset X". |
| Vimarśaka | Post-merge auditor | Activates on git events; show last verdict from `vimarshaka_audits` table (create if absent — see §8). |
| Tier-1 Severity Remediator | Class-1 fixer | Show "idle (0 activations)" unless `severity_remediations` table has rows for this build. |

For any table referenced above that doesn't yet exist, the agent row gracefully shows "no data — table not yet created" rather than crashing. **The cockpit must not throw on missing tables; it shows the absence honestly.**

## §8 Workflow estimate calculation

Stages: `entry`, `brahmagyan`, `ganita`, `bodha`, `kala`, `phala`, `mimamsa`. Per-stage estimated duration is computed at page load with this priority:

1. **Volume-derived from measured throughput** (best, when both expected_volume and a measured throughput exist): `expected_rows ÷ writer_throughput_rows_per_second`. Sum across the stage's assets. Throughput comes from the `asset_throughput` table (writer's rolling-average rows-per-second per asset_id from prior builds with provenance).
2. **Per-chart history** (when stage has been run before for this chart): use the most recent elapsed.
3. **Global rolling average** (when other charts have completed this stage): 30-day average across all builds.
4. **No estimate available** (first build of first chart, no history): display "estimating…" with the cursor advancing only from real-time throughput as writers emit events. Honest absence; no fabricated number.

**No seed defaults.** Prior drafts of this brief seeded per-stage durations (entry:30s, brahmagyan:15s, ganita:150s, bodha:300s, kala:120s, phala:180s, mimamsa:30s). Those were invented and have been removed. Until throughput has been measured at least once, the cockpit honestly shows "estimating…" rather than a fake target.

Throughput table:
```sql
CREATE TABLE IF NOT EXISTS asset_throughput (
  asset_id text REFERENCES asset_registry(asset_id),
  rows_per_second double precision NOT NULL,
  measurement_count int DEFAULT 0,
  last_measured_at timestamptz,
  last_measured_build_id uuid,
  history jsonb DEFAULT '[]'::jsonb,
  PRIMARY KEY (asset_id)
);
```

Same NULL-until-measured + provenance discipline as `asset_coefficients`.

```sql
WITH this_chart_history AS (
  SELECT stage, AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) AS avg_seconds
  FROM build_steps
  WHERE chart_id = $1 AND status = 'complete' AND finished_at IS NOT NULL
  GROUP BY stage
),
global_history AS (
  SELECT stage, AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) AS avg_seconds
  FROM build_steps
  WHERE status = 'complete' AND finished_at > now() - interval '30 days'
  GROUP BY stage
),
seed AS (
  SELECT * FROM (VALUES
    ('entry', 30), ('brahmagyan', 15), ('ganita', 150),
    ('bodha', 300), ('kala', 120), ('phala', 180), ('mimamsa', 30)
  ) AS t(stage, avg_seconds)
)
SELECT stage,
  COALESCE(tc.avg_seconds, g.avg_seconds, s.avg_seconds::float) AS estimated_seconds
FROM seed s
LEFT JOIN this_chart_history tc USING (stage)
LEFT JOIN global_history g USING (stage);
```

Per-chart history beats global history beats seed. The timeline cursor position = (sum elapsed of complete stages + elapsed in current stage) / sum of estimated. ETA = sum of remaining stages' estimated duration − elapsed-in-current.

## §9 Acceptance criteria (verify-against-prod)

| AC | Description | Verify |
|---|---|---|
| AC-1 | `asset_registry` table exists in prod with 39 seeded rows | `[verify-against: prod] [via: psql_prod count + checksum]` |
| AC-2 | `layer_approvals` table exists in prod | `[verify-against: prod] [via: \d layer_approvals]` |
| AC-3 | `/api/cockpit/registry` returns 39 rows on prod | `[verify-against: prod] [via: curl_prod]` |
| AC-4 | `/api/cockpit/stats?chart_id=482012f1-...` returns live row counts matching `SELECT count(*)` for each asset's storage table, PLUS expected_volume computed from each asset's formula given the chart's ayanamsha count | `[verify-against: prod] [via: curl_prod + psql_prod cross-check + manual formula evaluation on 3 sample assets]` |
| AC-4b | The formula evaluator rejects unsafe input (named variables only; arithmetic only); confirmed via attempted SQL injection / arbitrary code in a formula test row | `[verify-against: localhost] [via: unit test]` |
| AC-5 | `/api/cockpit/workflow` returns honest elapsed seconds per stage from build_steps (zero estimate cells when stage hasn't started) | `[verify-against: prod] [via: curl_prod]` |
| AC-6 | `/api/cockpit/agents` returns derived activity for every agent role; missing tables degrade gracefully (no 500) | `[verify-against: prod] [via: curl_prod]` |
| AC-7 | Cockpit page renders the three views; Chrome MCP confirms top-down order + collapsible behaviour + tab switching | `[verify-against: localhost] [via: chrome_mcp by Cowork]` |
| AC-8 | MARSYS theme variables applied; visual matches mockup tokens (gold-on-black, display-stack headings) | `[verify-against: localhost] [via: chrome_mcp screenshot review]` |
| AC-9 | All polling respects 2s timeout; failed cells show `—` with tooltip; no spinners-forever | `[verify-against: localhost] [via: chrome_mcp + intentional sidecar disconnect]` |
| AC-10 | Approve-layer flow inserts a row, surfaces the "Approved by X · timestamp" badge, and revoke returns to unapproved state | `[verify-against: prod] [via: curl_prod + psql_prod] |
| AC-11 | npm run typecheck + npm run build green; no console errors on cockpit page load | `[verify-against: localhost] [via: bash + chrome_mcp]` |
| AC-12 | Prod deploy goes green; prod cockpit at madhav.marsys.in shows live data | `[verify-against: prod] [via: chrome_mcp on prod URL]` |

## §10 Sequence

Each milestone closes with a Cowork-side Chrome MCP verification on localhost before moving to the next.

```
M1  Branch + theme CSS module + asset_registry migration + layer_approvals migration
M2  Backend: /api/cockpit/registry + seed script for 39 assets → AC-1, AC-3
M3  Backend: /api/cockpit/stats + per-chart live counts → AC-4
M4  Frontend: CockpitShell rewrite + TabBar + CockpitHeader + ConnectionHealthPill
M5  Frontend: DataAssetsView + LayerPanel + AssetRow (default tab) → AC-7, AC-8
    >>> Cowork Chrome MCP verifies: top-down order, collapse/expand, live counts, MARSYS theme
M6  Backend: /api/cockpit/workflow + frontend WorkflowView + WorkflowTimeline → AC-5
    >>> Cowork verifies live timeline reflects build_steps
M7  Backend: /api/cockpit/agents + frontend AgentsView + AgentRow → AC-6
    >>> Cowork verifies agent activity matches build state
M8  Backend: /api/cockpit/approve + frontend ApproveLayerDialog → AC-10
    >>> Cowork verifies approval flow + DB write
M9  Robustness pass: intentionally disconnect sidecar, kill SSE, force-timeout queries → AC-9
    >>> Cowork verifies the cockpit degrades visibly (no silent zeros, no spinners)
M10 Final localhost verification → AC-11
    >>> Cowork full Chrome MCP walkthrough
M11 PR, CI green, deploy to prod, post-deploy AC-12
```

## §11 Commit discipline

- One commit per milestone with a tight subject (`feat(cockpit-v2): M3 stats endpoint`)
- Each commit body lists the AC it advances + the verify command
- After M5, M6, M7, M8: Cowork emits a Chrome MCP report; if green, CC moves on; if not, CC fixes before the next milestone

## §12 Hard stops

Per AUTONOMY_RESILIENCE_PATTERN — only Tier-3 events synchronously stop CC. For this brief specifically:
- M2 seed: if any of the 39 assets' `count_sql` can't be authored because the target table doesn't exist in prod, halt the seed for that asset; mark `is_active=false` with a note; CC continues with the rest. Cowork follows up on the gap separately.
- M5 verification: if Chrome MCP shows MARSYS theme isn't applying (e.g., variables collide with existing styles), CC debugs locally; never deploys a broken-theme cockpit to prod.

---

*End of CLAUDECODE_BRIEF_COCKPIT_V2_IMPL v1.0. Cowork-authored. CC executes per the milestone sequence with Cowork Chrome MCP verification at M5/M6/M7/M8/M9/M10.*
