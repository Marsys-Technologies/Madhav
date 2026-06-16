---
brief_id: EXEC_BRIEF_PHASE_14E_L3_REGISTERS
version: 1.2
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
amended_at: 2026-04-28 — v1.1: filename corrections (versioned; CLUSTER_ATLAS not CLUSTER_REGISTER); execution-order tightened per 14E pre-flight halt finding | v1.2: GCS path correction (L3/registers/ per GCS_LAYOUT_v1_0)
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code (multi-session)
trigger_phrase: "Read EXEC_BRIEF_PHASE_14E_L3_REGISTERS_v1_0.md and execute it."
phase: 14E
phase_name: L3 Discovery Layer Registers — pattern_register, resonance_register, cluster_register, contradiction_register
risk_classification: LOW-MEDIUM (registers already exist as JSON; ingestion is mechanical; primary risk is referential integrity to MSR signals + chart_facts)
parallelizable_with: []  # serial after 14D execution; cannot run alongside 14C/14D content phases
must_complete_before: [14G]
depends_on:
  - EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES_v1_0.md (FULLY COMPLETE — chart_facts table populated; IBuildWriter interface evolved at Stream F)
  - EXEC_BRIEF_PHASE_14D_L2_5_PARITY_v1_0.md (FULLY COMPLETE — msr_signals table populated for FK validation)
output_artifacts:
  - 00_ARCHITECTURE/L3_DISCOVERY_REGISTERS_v1_0.md (NEW canonical spec)
  - 00_ARCHITECTURE/PHASE_14E_L3_REGISTERS_REPORT_v1_0.md (NEW execution report)
---

# EXEC_BRIEF — Phase 14E — L3 Discovery Layer Registers

## Mission

Project the four L3 discovery registers from JSON-on-disk into structured Postgres tables that the LLM router can query as deterministic tools. After 14E, queries like "what unresolved contradictions exist in the chart's career domain?" or "find all Cluster patterns with confidence > 0.7" hit indexed tables with referential integrity to L1 facts and L2.5 signals. Four new tables, four pipeline writers, four LLM tools.

L3 is the easiest of the structured projections because the registers already live as JSON files at `035_DISCOVERY_LAYER/REGISTERS/` (pattern, resonance, cluster, contradiction — each as `*_REGISTER.json` + a `.md` companion). 14E parses the JSONs, validates against schemas, writes to Postgres, and adds tool-surface coverage. No structured-extraction-from-markdown required.

Three architectural commitments:

1. **JSON is canonical authoring source for L3.** The `.md` companions are human-readable views of the JSONs; the JSONs are what the pipeline reads. If a `.md` companion drifts from its JSON, the JSON wins.

2. **Referential integrity is enforced.** Every register entry that cites an MSR signal must resolve against `msr_signals` (14D dependency). Every entry that cites a chart fact must resolve against `chart_facts` (14C dependency). Foreign keys in the schema enforce this; violations halt the swap.

3. **Discovery registers are append-only, not regenerated.** Unlike chart_facts (rebuilt each pipeline run from FORENSIC), the registers grow as discoveries accumulate. The pipeline ADDS new entries since the last build but doesn't truncate. Each entry carries a `discovered_at` timestamp + `discovered_in_build_id`.

## Pre-flight gate

1. Verify Phase 14C Stream F is COMPLETE — `IBuildWriter` interface supports row-based writers.
2. Verify Phase 14D msr_signals table is populated (at least staging-validated).
3. Verify Phase 14C chart_facts table is populated (at least staging-validated).
4. Verify the four register JSONs exist in GCS sources bucket at the **layer-prefix path** per `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md`. Filenames are versioned, and the cluster register is named ATLAS, not REGISTER:
   - `gs://madhav-marsys-sources/L3/registers/PATTERN_REGISTER_v1_0.json`
   - `gs://madhav-marsys-sources/L3/registers/RESONANCE_REGISTER_v1_0.json`
   - `gs://madhav-marsys-sources/L3/registers/CLUSTER_ATLAS_v1_0.json` ← named "ATLAS" not "REGISTER" (table name remains `cluster_register`; filename is canonical authoring source)
   - `gs://madhav-marsys-sources/L3/registers/CONTRADICTION_REGISTER_v1_0.json`
   - Plus: `gs://madhav-marsys-sources/L3/registers/INDEX.json` — manifest of register IDs; load and use to cross-validate counts.

   If a register file is missing from GCS, run `gcs_sync.py` (from Phase 14A) to upload from the local source path `035_DISCOVERY_LAYER/REGISTERS/`. **Do NOT rename local files to match an earlier draft of this brief.** The local naming is canonical authoring source.
5. Verify Cloud SQL migrations through 018 (14D) are applied.
6. Confirm git working tree clean.

If any fail, halt with actionable message.

## Scope

**`may_touch` (filesystem / git):**
- `platform/supabase/migrations/019_l3_registers.sql` (NEW — four tables + staging)
- `platform/python-sidecar/pipeline/writers/`:
  - `pattern_register_writer.py` (NEW)
  - `resonance_register_writer.py` (NEW)
  - `cluster_register_writer.py` (NEW)
  - `contradiction_register_writer.py` (NEW)
- `platform/python-sidecar/pipeline/extractors/`:
  - `register_loader.py` (NEW — generic JSON-register loader; one file, all four registers)
- `platform/src/lib/tools/structured/`:
  - `query_patterns.ts` (NEW)
  - `query_resonances_l3.ts` (NEW — distinct from 14D's signal-level query_resonance)
  - `query_clusters.ts` (NEW)
  - `query_contradictions.ts` (NEW)
- `platform/src/lib/tools/registry.ts` (additive — register the 4 new tools)
- `00_ARCHITECTURE/L3_DISCOVERY_REGISTERS_v1_0.md` (NEW canonical spec)
- `00_ARCHITECTURE/PHASE_14E_L3_REGISTERS_REPORT_v1_0.md` (NEW execution report)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (additive — four new table entries; four tool entries)
- `035_DISCOVERY_LAYER/CLAUDE.md` (additive update — STRUCTURED projection pointer)

**`must_not_touch`:**
- `035_DISCOVERY_LAYER/REGISTERS/*.json` — these are canonical authoring source. The `.md` companions are also untouched (read-only).
- 14C tables, 14D tables — separate ownership.
- 14B's `RAGChunksWriter`. `pipeline/main.py` orchestrator core.
- Any L1/L2.5 governance doc.
- Any feature flag.

## Execution model — multi-session

Streams A–F map roughly 1:1 to sessions:

| Order | Stream | Session # | Parallel-safe with |
|---|---|---|---|
| 1 | A — Migration 019 | 1 | (foundation) |
| 2 | B — Generic register_loader.py + Pattern writer | 2 | C, D, E |
| 2 | C — Resonance register writer | 3 | B, D, E |
| 2 | D — Cluster register writer | 4 | B, C, E |
| 2 | E — Contradiction register writer | 5 | B, C, D |
| 3 | F — Tools + registry + verification + close report | 6 | (gated on B–E) |

## Sub-streams

### Stream A — Migration 019

```sql
BEGIN;

-- Pattern Register
CREATE TABLE IF NOT EXISTS pattern_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pattern_id TEXT UNIQUE NOT NULL,       -- 'PAT.001'
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  domain TEXT,                           -- 'self'|'wealth'|... or NULL for cross-domain
  evidence JSONB NOT NULL,               -- {fact_ids: [...], signal_ids: [...], event_ids: [...]}
  source_signal_ids TEXT[],              -- denormalized for FK validation
  source_fact_ids TEXT[],                -- denormalized for FK validation
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded','rejected'))
);
CREATE INDEX idx_pattern_domain ON pattern_register(domain);
CREATE INDEX idx_pattern_confidence ON pattern_register(confidence DESC);
CREATE INDEX idx_pattern_status ON pattern_register(status);
CREATE INDEX idx_pattern_signals ON pattern_register USING GIN(source_signal_ids);
CREATE TABLE IF NOT EXISTS pattern_register_staging (LIKE pattern_register INCLUDING ALL);

-- Resonance Register (L3 — higher abstraction than L2.5's RM)
CREATE TABLE IF NOT EXISTS resonance_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resonance_id TEXT UNIQUE NOT NULL,     -- 'RES.001'
  theme TEXT NOT NULL,                   -- 'shadow_authority'|'split_sustenance'|...
  description TEXT NOT NULL,
  signal_ids TEXT[] NOT NULL,            -- MSR signals in this resonance
  pattern_ids TEXT[],                    -- L3 patterns this resonance ties to
  domains TEXT[],                        -- domains touched
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE INDEX idx_resonance_theme ON resonance_register(theme);
CREATE INDEX idx_resonance_signals ON resonance_register USING GIN(signal_ids);
CREATE INDEX idx_resonance_domains ON resonance_register USING GIN(domains);
CREATE TABLE IF NOT EXISTS resonance_register_staging (LIKE resonance_register INCLUDING ALL);

-- Cluster Register
CREATE TABLE IF NOT EXISTS cluster_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id TEXT UNIQUE NOT NULL,       -- 'CLUS.001'
  name TEXT NOT NULL,
  theme TEXT NOT NULL,
  description TEXT NOT NULL,
  member_signal_ids TEXT[] NOT NULL,
  member_fact_ids TEXT[],
  member_event_ids TEXT[],
  domain TEXT,
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE INDEX idx_cluster_theme ON cluster_register(theme);
CREATE INDEX idx_cluster_domain ON cluster_register(domain);
CREATE INDEX idx_cluster_signals ON cluster_register USING GIN(member_signal_ids);
CREATE TABLE IF NOT EXISTS cluster_register_staging (LIKE cluster_register INCLUDING ALL);

-- Contradiction Register
CREATE TABLE IF NOT EXISTS contradiction_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contradiction_id TEXT UNIQUE NOT NULL, -- 'CON.001'
  statement_a TEXT NOT NULL,
  statement_b TEXT NOT NULL,
  conflict_type TEXT NOT NULL,           -- 'signal_vs_signal'|'fact_vs_signal'|'pattern_vs_event'|'tradition_vs_observation'
  evidence JSONB NOT NULL,               -- {signal_ids: [...], fact_ids: [...], event_ids: [...]}
  source_signal_ids TEXT[],
  source_fact_ids TEXT[],
  resolution_status TEXT NOT NULL CHECK (resolution_status IN ('unresolved','accepted','dismissed','reframed')),
  resolution_notes TEXT,
  domain TEXT,
  confidence NUMERIC NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  discovered_at TIMESTAMPTZ NOT NULL,
  discovered_in_build_id TEXT NOT NULL REFERENCES build_manifests(build_id)
);
CREATE INDEX idx_contradiction_status ON contradiction_register(resolution_status);
CREATE INDEX idx_contradiction_domain ON contradiction_register(domain);
CREATE INDEX idx_contradiction_signals ON contradiction_register USING GIN(source_signal_ids);
CREATE TABLE IF NOT EXISTS contradiction_register_staging (LIKE contradiction_register INCLUDING ALL);

COMMIT;
```

### Stream B — Generic register_loader.py + Pattern writer

`extractors/register_loader.py` is a single file that handles all four registers via a config-driven pattern:

```python
REGISTER_CONFIGS = {
  'pattern': {
    'json_uri': 'gs://madhav-marsys-sources/L3/registers/PATTERN_REGISTER_v1_0.json',
    'pydantic_model': PatternEntry,
    'target_table': 'pattern_register_staging',
    'fk_validations': [
      ('source_signal_ids', 'msr_signals', 'signal_id'),
      ('source_fact_ids', 'chart_facts', 'fact_id'),
    ],
  },
  'resonance': {
    'json_uri': 'gs://madhav-marsys-sources/L3/registers/RESONANCE_REGISTER_v1_0.json',
    'pydantic_model': ResonanceEntry,
    'target_table': 'resonance_register_staging',
    'fk_validations': [
      ('signal_ids', 'msr_signals', 'signal_id'),
      ('pattern_ids', 'pattern_register', 'pattern_id'),
    ],
  },
  'cluster': {
    'json_uri': 'gs://madhav-marsys-sources/L3/registers/CLUSTER_ATLAS_v1_0.json',  # NOTE: filename is "ATLAS"; target table is "cluster_register"
    'pydantic_model': ClusterEntry,
    'target_table': 'cluster_register_staging',
    'fk_validations': [
      ('member_signal_ids', 'msr_signals', 'signal_id'),
      ('member_fact_ids', 'chart_facts', 'fact_id'),
      ('member_event_ids', 'life_events', 'event_id'),
    ],
  },
  'contradiction': {
    'json_uri': 'gs://madhav-marsys-sources/L3/registers/CONTRADICTION_REGISTER_v1_0.json',
    'pydantic_model': ContradictionEntry,
    'target_table': 'contradiction_register_staging',
    'fk_validations': [
      ('source_signal_ids', 'msr_signals', 'signal_id'),
      ('source_fact_ids', 'chart_facts', 'fact_id'),
    ],
  },
}
```

Pattern writer (`writers/pattern_register_writer.py`) inherits `IBuildWriter`, calls `register_loader.load('pattern')`, validates against `PatternEntry` Pydantic model, validates FKs (every signal_id referenced exists in `msr_signals`), inserts into staging.

**Append-only swap semantics** (different from 14B/14C/14D!):
```sql
-- Standard 14B/14C/14D swap: TRUNCATE live, INSERT FROM staging.
-- 14E append-only swap: only NEW entries flow live.
INSERT INTO pattern_register
SELECT * FROM pattern_register_staging
WHERE pattern_id NOT IN (SELECT pattern_id FROM pattern_register);

UPDATE pattern_register
SET status = staged.status,
    confidence = staged.confidence,
    description = staged.description
FROM pattern_register_staging staged
WHERE pattern_register.pattern_id = staged.pattern_id
  AND pattern_register.status != 'rejected';  -- never auto-revive a rejected entry

TRUNCATE pattern_register_staging;
```

This preserves discovery history. A pattern marked `rejected` in a prior build does NOT come back via the JSON re-ingest (manual override required).

### Stream C — Resonance register writer

Same pattern as B, target table `resonance_register_staging`. FK validations: `signal_ids → msr_signals`, `pattern_ids → pattern_register` (cross-table reference within L3).

### Stream D — Cluster register writer

Same pattern. FK validations: `member_signal_ids → msr_signals`, `member_fact_ids → chart_facts`, `member_event_ids → life_events`.

### Stream E — Contradiction register writer

Same pattern. FK validations: `source_signal_ids → msr_signals`, `source_fact_ids → chart_facts`. Plus: every contradiction has both `statement_a` and `statement_b` non-empty; `resolution_status` defaults to `unresolved` for new entries.

### Stream F — Tools + registry + verification + close

Implement four tools at `platform/src/lib/tools/structured/`:

| Tool | Inputs | Returns |
|---|---|---|
| `query_patterns` | `domain?, confidence_min?, status?` | matching pattern_register rows |
| `query_resonances_l3` | `theme?, signal_id?, domain?` | matching resonance_register rows |
| `query_clusters` | `theme?, domain?, confidence_min?` | matching cluster_register rows |
| `query_contradictions` | `unresolved_only?, domain?, conflict_type?` | matching contradiction_register rows |

Register all four. Each description tells the LLM when to choose it (e.g., `query_contradictions(unresolved_only=true)` for "what tensions remain in the chart?").

Verification:
1. Trigger pipeline run.
2. Verify staging row counts match JSON entry counts (per-register).
3. Verify FK integrity: every cited signal_id/fact_id/event_id resolves.
4. Append-only swap: confirm pre-existing entries preserved; new entries added; `rejected` entries not revived.
5. Spot-check tools:
   - `query_patterns(domain='career', confidence_min=0.7)` → returns >0 rows
   - `query_contradictions(unresolved_only=true)` → returns the unresolved set
   - `query_clusters(theme=*)` → returns 12+ rows (per memory note: "12 clusters CLUS.001-012")
   - `query_resonances_l3(theme=*)` → returns the L3 resonance set
6. Run validators; capture deltas vs prior baseline.
7. Author `L3_DISCOVERY_REGISTERS_v1_0.md` + `PHASE_14E_L3_REGISTERS_REPORT_v1_0.md`.
8. Update `035_DISCOVERY_LAYER/CLAUDE.md` with STRUCTURED projection pointer.
9. Update `CAPABILITY_MANIFEST.json`; rotate fingerprint.
10. Atomic commits per stream; final umbrella commit at F.

## Done criteria

1. Migration 019 applied; four tables + four staging tables exist.
2. All four registers ingested from JSONs into Postgres tables.
3. Row counts match source JSON entry counts (per register).
4. Full FK referential integrity: every signal_id, fact_id, event_id reference resolves.
5. Append-only swap semantics verified: rejected entries do not auto-revive.
6. Four writers integrated into 14B pipeline.
7. Four tools implemented, registered, unit-tested.
8. `L3_DISCOVERY_REGISTERS_v1_0.md` + `PHASE_14E_L3_REGISTERS_REPORT_v1_0.md` exist.
9. Validator deltas documented vs prior baseline.
10. CAPABILITY_MANIFEST.json updated; fingerprint rotated.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Register JSON references signal_ids that don't exist in 14D's msr_signals | Medium | Medium | FK validation in Stream B. Halt with actionable message naming the missing signal_ids. Forces 14D to complete first OR signal_id format reconciliation. |
| Append-only swap accidentally re-revives a `rejected` entry | Low | Medium | Stream B's UPDATE clause explicitly excludes `status='rejected'` from auto-update. Test in verification. |
| JSON schema drift between PATTERN_REGISTER.json and Pydantic model | Medium | Low | Pydantic validation halts on schema mismatch with clear error. Re-author Pydantic to match JSON, OR fix JSON; do not silently coerce. |
| Resonance register entry references a `pattern_id` that doesn't exist yet (chicken-and-egg if pattern + resonance reference each other) | Low | Low | Two-pass insert: insert all four registers' staging rows first, validate FKs across the whole set, then swap. If circular dependency unresolvable, log and surface. |
| Discovery cadence: pipeline runs daily, but registers grow monthly. Stale staging confuses the diff. | Low | Low | Append-only swap means re-running with the same JSON is a no-op. Idempotent by design. |

## Concurrency declaration

**Parallel-with**: nothing in the 14C/14D/14E sequence. 14E is strictly serial — must run after 14D is fully complete.

Why the original v1.0 "parallel-with 14D" claim was wrong: 14E's pre-flight gate requires `msr_signals` populated (FK validation references it) AND `chart_facts` populated (FK validation references it). 14D populates msr_signals; 14C populates chart_facts. Both upstream phases must close before 14E's pre-flight passes. Trying to run 14E alongside 14D causes the pre-flight halt that surfaced this v1.1 amendment.

The actual execution order across 14C/14D/14E:
1. **14C Streams A–F** (Stream F is the writer-interface evolution — gates 14D)
2. **14D Streams A–G** (can start as soon as 14C Stream F lands; 14C Streams G/H can run in parallel with 14D)
3. **14E Streams A–F** (only after both 14C and 14D have closed)

**Must complete before**:
- 14G lockdown — needs full L3 register projection.

**Shared-file vigilance**:
- `pipeline/main.py` writer registry — additive entries; rebase on conflict.
- `platform/src/lib/tools/registry.ts` — additive; rebase on conflict.
- `CAPABILITY_MANIFEST.json` — additive; rebase on conflict.

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14E_L3_REGISTERS_v1_0.md and execute it."

## Notes for the executor

- Append-only swap semantics are the load-bearing difference between 14E and 14B/14C/14D. Discovery is cumulative, not regenerated. A pattern dropped from PATTERN_REGISTER.json should NOT auto-disappear from `pattern_register` — that requires a manual `status='rejected'` flip OR a separate cleanup brief.
- Register JSONs are small (12 clusters, 8 contradictions per memory). The whole 14E pipeline run completes in seconds. Do NOT spend cycles optimizing performance; spend them on FK validation.
- Tool descriptions for `query_contradictions` and `query_patterns` matter most — these are the queries that reveal the most non-obvious chart insights ("what's contradicted in this chart?" is one of the strongest LLM-prompts the runtime will see).
- 14E is the lowest-risk of 14C/14D/14E because the source format is already structured. If 14E reveals a JSON schema drift, fix it in place (in the JSON) — the `.md` companion will need a manual sync in a follow-up doc-only brief.
