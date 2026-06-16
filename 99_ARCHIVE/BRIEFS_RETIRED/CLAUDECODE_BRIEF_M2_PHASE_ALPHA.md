---
brief_id: M2_PHASE_ALPHA
karn_session_name: KARN-W1-R1-PHASE-ALPHA
wave: 1
stream: A
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution (autonomous, long-running)
session_type: diagnostic-audit only — NO code changes, NO deploys, NO tests
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none
  blocks: M2_A1_MSR_ETL, M2_A2_CHART_FACTS_ETL, M2_A_MINOR
parallel_stream_note: |
  Three other Wave-1 briefs run concurrently on the same branch:
  M2_C6_VECTOR_SEARCH_FILTER (Stream B, TypeScript), M2_D56_OBSERVABILITY
  (Stream E, migrations + writers), M2_B3_CLUSTER_RECLUSTER (Stream C,
  discovery JSON). Disjoint paths — no collision possible.
estimated_time: 30–60 min single Claude Code session

scope_summary: |
  Run four diagnostic audits to ground-truth M2 state before downstream
  Stream-A briefs scope. Outputs:
    • M1_M2_ACTIVATION_MATRIX.md — every FORENSIC § mapped to its
      database representation, chunk representation, retrieval tool
    • M2_PHASE_ALPHA_RESULTS_<DATE>.txt — raw probe outputs
  This brief is read-only. No code changes, no migrations, no deploys.

may_touch:
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md                     # CREATE — the activation matrix
  - 00_ARCHITECTURE/BRIEFS/M2_PHASE_ALPHA_RESULTS_<DATE>.txt        # CREATE — raw audit output
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_PHASE_ALPHA.md       # status flip at end
  - platform/scripts/m2_phase_alpha_probes.sql                      # CREATE — new probe file (do NOT modify retrieval_diagnostic_probes.sql)
  # Read-only references:
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md
  - platform/migrations/**                                          # READ schemas only
  - platform/python-sidecar/pipeline/extractors/**                  # READ extractor logic only

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                      # UI/UX stream
  - Any other CLAUDECODE_BRIEF_M2_*.md                              # other Wave-1 briefs
  - 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md              # parent plan, reference only
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT.md      # parent strategy, reference only
  - 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md       # historical reference
  - All historical RETRIEVAL_PROBE_RESULTS_*.txt
  - platform/src/**                                                 # ALL TypeScript off-limits
  - platform/python-sidecar/**                                      # NO code edits
  - platform/migrations/**                                          # NO new migrations
  - 025_HOLISTIC_SYNTHESIS/**                                       # source-of-truth, read-only
  - 035_DISCOVERY_LAYER/**                                          # off-limits
  - 03_DOMAIN_REPORTS/, 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/    # off-limits
  - Any retrieval-tool TypeScript file
  - platform/scripts/retrieval_diagnostic_probes.sql                # do NOT edit; read-only reference

acceptance_criteria:
  AC.1: |
    Audit 1 — chart_facts schema introspection completed.
    Output captured: \\d chart_facts; SELECT category, COUNT(*) FROM chart_facts WHERE is_stale=false GROUP BY category;
    plus 5 sample rows. Documented in M1_M2_ACTIVATION_MATRIX.md §1.
  AC.2: |
    Audit 2 — msr_signals column inventory completed.
    Output captured: \\d msr_signals; full column list + per-column data type.
    Compare to MSR_v3_0.md source fields. Documented in matrix §2.
    Identifies which source fields are MISSING as columns. Specifically check for:
    signal_type, temporal_activation, valence, classical_source, falsifier,
    supporting_rules, rpt_deep_dive, entities_involved, v6_ids_consumed, prior_id.
  AC.3: |
    Audit 3 — classifier output audit on factual queries.
    Sample 10 most recent query_trace_steps rows where step_name='classify' and
    the resulting query_plan had query_class='factual'. For each, capture:
    - The full payload JSONB (planets[], domains[], tools_authorized[], graph_seed_hints[]).
    - Whether msr_sql is in tools_authorized.
    - Whether planets[] is populated when query text names a planet.
    Documented in matrix §3.
  AC.4: |
    Audit 4 — FORENSIC §1–§27 vs database round-trip matrix.
    For each of the 27 sections, fill in:
    - Has structured table representation? (chart_facts? msr_signals? l25_*? Which?)
    - Has rag_chunks representation? (which doc_type, how many chunks?)
    - Has retrieval tool? (which? Or NONE?)
    - Coverage % vs source content (rough estimate based on row counts).
    Documented as the activation matrix in M1_M2_ACTIVATION_MATRIX.md §4.
  AC.5: |
    M1_M2_ACTIVATION_MATRIX.md created at 00_ARCHITECTURE/.
    Frontmatter includes: canonical_id, status (LIVING), authored_at, parent_plan ref.
    Sections §1 (chart_facts) §2 (msr_signals) §3 (classifier audit) §4 (FORENSIC §1-§27 matrix) §5 (gap summary).
  AC.6: |
    Closing summary printed in session output per M1_M2_EXECUTION_PLAN §3.4.
    Halt-and-report flag for any blocker.
  AC.7: |
    No source code modified. No deploys. No tests. No migrations.
    git status post-session shows ONLY:
      00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md (new)
      00_ARCHITECTURE/BRIEFS/M2_PHASE_ALPHA_RESULTS_<DATE>.txt (new)
      00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_PHASE_ALPHA.md (modified — status flip only)
      platform/scripts/m2_phase_alpha_probes.sql (new)
  AC.8: |
    This brief's frontmatter `status` flipped to COMPLETE.

halt_conditions:
  - Auth Proxy unreachable on 127.0.0.1:5433 after 30s wait following bash platform/scripts/start_db_proxy.sh
  - gcloud auth not active or ADC missing
  - DB authentication failure on amjis_app user
  - Branch is not redesign/r0-foundation (DO NOT switch branches)
  - git status shows pre-existing uncommitted modifications to files this brief intends to create
  - Pre-existing test failures count not at expected baseline (~9 failures per prior session reports)
---

# CLAUDECODE_BRIEF — M2_PHASE_ALPHA (Wave 1, Stream A)

## §1 — Why this session

The M1/M2 master plan and execution plan both depend on knowing exactly what's in the database today. PROBE 9 (chart_facts) and PROBE 2 (msr_signals.signal_type) errored on column-name mismatches in prior sessions, so we still don't know:

- Which FORENSIC sections (§1–§27) actually became chart_facts rows.
- Which MSR source fields actually became msr_signals columns.
- What the classifier emits for factual queries (verification Q1 from 2026-04-29 had msr_sql=0; we suspect the classifier isn't passing planet hints to msr_sql on factual class — verify).

This brief audits all four. It produces an activation matrix that scopes M2_A1, M2_A2, M2_A_MINOR, and several other downstream briefs precisely. Without this audit, those briefs scope approximately.

**Read-only.** No code, no migrations, no deploys.

## §2 — Pre-flight self-diagnostics (mandatory)

Run these checks. If ANY fails, halt with a 5-line summary naming the failed check + suggested remediation.

### §2.1 — Branch state
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"
```

### §2.2 — Working tree state
```bash
git status --short
# Expected: any combination of uncommitted UI/UX work + this brief's expected outputs (which don't exist yet).
# HALT if there are uncommitted modifications to files this brief plans to create:
#   00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md
#   00_ARCHITECTURE/BRIEFS/M2_PHASE_ALPHA_RESULTS_<DATE>.txt
#   platform/scripts/m2_phase_alpha_probes.sql
```

### §2.3 — gcloud auth
```bash
gcloud config list account --format="value(core.account)" | grep -q . || HALT "gcloud not authenticated"
gcloud auth application-default print-access-token > /dev/null 2>&1 || HALT "ADC missing"
```

### §2.4 — Auth Proxy
```bash
nc -z 127.0.0.1 5433 || {
  bash platform/scripts/start_db_proxy.sh &
  PROXY_PID=$!
  for i in {1..30}; do nc -z 127.0.0.1 5433 && break; sleep 1; done
  nc -z 127.0.0.1 5433 || HALT "proxy failed to start"
}
```

### §2.5 — DB connectivity
```bash
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "SELECT 1;" -t >/dev/null || HALT "DB auth failed"
```

If §2.5 needs a password, retrieve via:
```bash
PGPASSWORD=$(gcloud secrets versions access latest --secret="amjis-app-db-password" --project=madhav-astrology 2>/dev/null) || HALT "secret unavailable"
```

## §3 — Implementation steps

### §3.1 — Compose the audit probe file

Create `platform/scripts/m2_phase_alpha_probes.sql` containing the four audits below. Use the same `\echo` + heading pattern as `retrieval_diagnostic_probes.sql`.

**Audit 1 — chart_facts schema:**
```sql
\d chart_facts
SELECT column_name, data_type FROM information_schema.columns WHERE table_name='chart_facts' ORDER BY ordinal_position;
SELECT category, COUNT(*) AS row_count FROM chart_facts WHERE is_stale=false GROUP BY category ORDER BY row_count DESC;
SELECT * FROM chart_facts WHERE is_stale=false ORDER BY category, id LIMIT 20;
```

**Audit 2 — msr_signals columns:**
```sql
\d msr_signals
SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='msr_signals' ORDER BY ordinal_position;
-- Per-column NULL rate to see which "exist but are dropped":
SELECT
  COUNT(*) FILTER (WHERE signal_type IS NOT NULL) AS signal_type_filled,
  COUNT(*) FILTER (WHERE temporal_activation IS NOT NULL) AS temporal_activation_filled,
  COUNT(*) FILTER (WHERE valence IS NOT NULL) AS valence_filled,
  COUNT(*) FILTER (WHERE classical_source IS NOT NULL) AS classical_source_filled,
  COUNT(*) FILTER (WHERE falsifier IS NOT NULL) AS falsifier_filled,
  COUNT(*) AS total
FROM msr_signals
WHERE native_id='abhisek_mohanty';
-- Note: any of these column refs that fail confirms the column is missing.
-- Set ON_ERROR_STOP=off so subsequent audits still run.
```

**Audit 3 — Classifier output on factual queries:**
```sql
-- Pull last 10 classify steps where the resulting plan was factual class.
-- Note: the classify step writes to query_trace_steps.payload as JSONB.
WITH factual_classify AS (
  SELECT
    query_id,
    created_at,
    payload
  FROM query_trace_steps
  WHERE step_name = 'classify'
    AND status = 'done'
    AND payload->'data_summary'->>'result' = 'factual'
  ORDER BY created_at DESC
  LIMIT 10
)
SELECT
  query_id,
  created_at,
  payload->'data_summary'->>'result' AS query_class,
  payload->'plan_emitted'->'planets' AS planets,
  payload->'plan_emitted'->'domains' AS domains,
  payload->'plan_emitted'->'tools_authorized' AS tools_authorized,
  payload->'plan_emitted'->'graph_seed_hints' AS graph_seed_hints
FROM factual_classify;
-- If the payload structure differs, adapt the JSON path. Document the actual structure.
```

**Audit 4 — FORENSIC §1–§27 round-trip:** This is performed in the matrix document itself (§3.3 below), NOT as SQL.

### §3.2 — Run the probes

```bash
DATE=$(date +%Y-%m-%d)
OUT="00_ARCHITECTURE/BRIEFS/M2_PHASE_ALPHA_RESULTS_${DATE}.txt"

PGPASSWORD="${PGPASSWORD}" psql \
  -h 127.0.0.1 -p 5433 \
  -U amjis_app -d amjis \
  -v ON_ERROR_STOP=off \
  -f platform/scripts/m2_phase_alpha_probes.sql \
  > "$OUT" 2>&1

echo "Exit code: $?" >> "$OUT"

# Verify outputs:
test -s "$OUT" || HALT "probe output empty"
grep -q "chart_facts" "$OUT" || HALT "Audit 1 didn't run"
```

### §3.3 — Read FORENSIC v8.0 + compose the matrix

Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` end-to-end. For each of the 27 numbered sections (§1 Core Identity through §27 Document Completeness Ledger), determine:

- **Source content density** — number of subsections, cells, signals, etc.
- **Structured table representation** — which DB table holds this content? (chart_facts? msr_signals? l25_*?) Cross-reference with Audit 1 + 2 outputs.
- **rag_chunks representation** — `SELECT doc_type, COUNT(*) FROM rag_chunks WHERE source_file LIKE '%FORENSIC_v8_0%' GROUP BY doc_type` — captures which sections were chunked.
- **Retrieval tool** — which of the 10 existing tools queries this section's data? (Or NONE?)
- **Coverage % estimate** — rough estimate of source-vs-DB completeness for this section.

Use cross-reference grep where helpful:
```bash
grep -n "^## §" 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
```

### §3.4 — Write the activation matrix

Create `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md` with frontmatter:
```yaml
---
canonical_id: M1_M2_ACTIVATION_MATRIX
status: LIVING
authored_at: <ISO timestamp>
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
intended_disposition: |
  This is the M2-close acceptance gate. Every row green = M2 corpus
  fully activated. Updated by every M2 brief that lands new structured
  representation or new retrieval surface.
---
```

Body sections:

**§1 — chart_facts schema (Audit 1).** Column list + category breakdown table + 5 sample rows.

**§2 — msr_signals columns (Audit 2).** Source-vs-DB column comparison. Mark each source field as PRESENT, MISSING, or PARTIAL.

**§3 — Classifier output audit (Audit 3).** Table of 10 sample factual queries with their emitted plans. Identify pattern: are planets[] / tools_authorized populated correctly?

**§4 — FORENSIC §1–§27 activation matrix (Audit 4).** A 27-row table:

| § | Section | Source density | Structured table | rag_chunks | Retrieval tool | Coverage |
|---|---|---|---|---|---|---|
| §1 | Core Identity | 5 fields | chart_facts (cat=metadata?) | l1_fact | manifest_query / vector_search | ?% |
| ... |

**§5 — Gap summary.** Aggregate findings:
- N FORENSIC sections fully activated (table + chunks + tool)
- N partially activated
- N fully dark (no DB representation, no tool)
- The list of dark/partial sections ranked by source content density

**§6 — Implications for downstream briefs.** A short list of scope adjustments for:
- M2_A1 (msr_signals ETL): exact list of columns to add per Audit 2
- M2_A2 (chart_facts ETL): exact list of FORENSIC sections to add coverage for per Audit 4
- M2_C1 (chart_facts_query): exact set of categories the tool needs to support
- A1's findings on classifier audit (Audit 3): does B1 (vector_search filter) need additional fixes for the factual-query gap?

### §3.5 — Closing summary

Print to session output per M1_M2_EXECUTION_PLAN §3.4 standardized format:

```
SESSION CLOSE — M2_PHASE_ALPHA — <ISO timestamp>

ACs result:
  AC.1: PASS — Audit 1 documented in matrix §1
  AC.2: PASS — Audit 2 documented in matrix §2; <N> source fields missing from DB
  AC.3: PASS — Audit 3 documented in matrix §3; <observation>
  AC.4: PASS — Audit 4 matrix complete; <N> sections fully activated, <M> partial, <K> dark
  AC.5: PASS — M1_M2_ACTIVATION_MATRIX.md created
  AC.6: PASS — closing summary in standardized format
  AC.7: PASS — git status shows only the 4 expected files
  AC.8: PASS — brief status flipped to COMPLETE

Files created:
  00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md (~<KB>)
  00_ARCHITECTURE/BRIEFS/M2_PHASE_ALPHA_RESULTS_<DATE>.txt (~<KB>)
  platform/scripts/m2_phase_alpha_probes.sql

DB changes:
  None (read-only audit)

Cloud Run revisions:
  None (no deploy)

Tests:
  Not run (audit-only)

Halt-and-report cases:
  None

Brief status: COMPLETE
Next brief in stream: M2_A1_MSR_ETL (depends on this brief's findings)
```

### §3.6 — Update brief status

Edit this brief's frontmatter `status: PENDING` → `status: COMPLETE`.

## §4 — Hard constraints

- **No code edits, no migrations, no deploys, no tests.** Audit only.
- **No edits to retrieval_diagnostic_probes.sql.** This brief creates a NEW probe file at `platform/scripts/m2_phase_alpha_probes.sql`.
- **No edits to other Wave-1 brief files.** Disjoint scope.
- **Halt and report on any pre-flight failure.** Do not improvise.

## §5 — Closing checklist

- [ ] Pre-flight §2.1–§2.5 all PASS
- [ ] m2_phase_alpha_probes.sql created
- [ ] M2_PHASE_ALPHA_RESULTS_<DATE>.txt has audit output
- [ ] M1_M2_ACTIVATION_MATRIX.md exists with all 6 sections
- [ ] §6 implications list explicitly names downstream brief scope adjustments
- [ ] Closing summary in standardized format
- [ ] git status shows only expected 4 files
- [ ] This brief's `status` flipped to COMPLETE

---

*End of M2_PHASE_ALPHA. Status: COMPLETE (closed KARN-W1-R1-PHASE-ALPHA 2026-04-30).*

## Kickoff prompt (paste into fresh Claude Code session)

```
You are running KARN-W1-R1-PHASE-ALPHA.

Read 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_PHASE_ALPHA.md as the
governing scope for this session. Branch is redesign/r0-foundation.
Do NOT read CLAUDECODE_BRIEF.md at the project root — UI/UX stream owns it.

This session is part of Project KARN. For cross-session context:
- 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md (operating rules)
- 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md (history)
- 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §3 (autonomous brief contract)

This is a read-only audit session: NO code edits, NO migrations, NO deploys,
NO tests. Produce M1_M2_ACTIVATION_MATRIX.md as the primary deliverable.
Run autonomously per the brief's §3 implementation steps. Halt and report
only on conditions enumerated in halt_conditions. Otherwise complete fully.

At session close, append a standardized closing entry to
PROJECT_KARN_SESSION_LOG.md per the protocol §2 entry format. Use
karn_session_name = KARN-W1-R1-PHASE-ALPHA.
```
