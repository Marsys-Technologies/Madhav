---
stream: C — ṚTA (the loop's data path)
lead: ṚTA-LEAD of EKAVĀKYATĀ
campaign: EKAVĀKYATĀ
started: 2026-08-16
---

# STREAM C — ṚTA LEDGER

Heartbeat cadence: ≤20 min. Every entry timestamped. DB writes ONLY via migration path through E's deploy — no direct psql writes ever.

---

## HB-01 — 2026-08-16 SESSION OPEN

Stream C lead active. Worktree: ekv/lead-rta. Sequence: C-02 (diagnosis) → C-01 (migration + writer fix) → C-03 (rebase PR #1287) → C-04 (W1: lifecycle smoke) → C-05 (W2: auto-filing spec).

Wave-0 lanes: C-01, C-02, C-03. Target: BUILT+VERIFIED ≤2h.

---

## C-02 — DIAGNOSIS COMPLETE

**Status:** EKV-C-02-BUILT

### Findings

**All 6 empty rows have identical metadata — same batch, same bug:**

| Field | Value |
|---|---|
| generator_class | `engine` |
| filing_method | `explicit_filing_tool` |
| filed_by | `w45_post_fit_rebuild` |
| model | `gochara_v3_w45_builder` |
| formula_version | `gochara_v3_w45` |
| as_of / created_at | `2026-08-11 23:34:13.688808+00` |
| chart_id | 4 native + 2 comparison |
| claim_shape | `interval` |

**Root cause:** `w45_post_fit_rebuild.py::seed_prospective_ledger` calls `daterange(window_start, window_end)` (Postgres default `[)` bounds). When the gochara elevation forecast yields a single-day peak (window_start == window_end), `daterange('d','d')` = EMPTY in Postgres.

The existing `brahma_prospective_ledger_shape_fields_check` constraint requires `upper(observation_window) > lower(observation_window)` for `interval` shape, but `upper(empty) = NULL` and `lower(empty) = NULL`, so `NULL > NULL = NULL`, and Postgres CHECK treats NULL as PASS — allowing broken rows through.

**Source file:** `platform/python-sidecar/scripts/kala_admission/w45_post_fit_rebuild.py:474` (INSERT) + line 67 (missing `timedelta` import).

**Note on "4→6 active leak":** All 6 rows share the same `created_at = 2026-08-11 23:34:13.688808+00`. The "active leak" correctly refers to the latent writer bug that would produce more empty rows on the next run — not to new rows filed tonight.

---

## C-01 — MIGRATION + WRITER FIX BUILT

**Status:** EKV-C-01-BUILT | **Branch:** `ekv/c-01-ledger-repair` | **Commit:** `216fb0024`

### Changes

**1. Migration 572** (`platform/migrations/572_ekv_c01_ledger_empty_daterange_repair.sql`):
- DELETE 6 broken rows (`WHERE isempty(observation_window) AND filed_by='w45_post_fit_rebuild' AND ...`)
- Safety abort if any other-source empty rows remain
- `ADD CONSTRAINT brahma_prospective_ledger_no_empty_window CHECK (NOT isempty(observation_window))` — idempotent (`IF NOT EXISTS`)

**2. Writer fix** (`platform/python-sidecar/scripts/kala_admission/w45_post_fit_rebuild.py`):
- Line 67: added `timedelta` to `from datetime import ...`
- After date coercion: guard `if window_end <= window_start: window_end = window_start + timedelta(days=1)` with warning log

**Cross-stream note:** `w45_post_fit_rebuild.py` is in `platform/python-sidecar/**` (Stream B's lease per §4). This touch is authorised by the C-01 kickoff instruction: "Bundle the C-02 writer fix in the same lane." PRATINIDHI sign-off below covers this.

### Test results
- All 57 `test_w45_post_fit_rebuild.py` unit tests pass ✓
- Migration idempotency: DELETE WHERE is no-op if rows already gone; ADD CONSTRAINT uses `IF NOT EXISTS` ✓
- Constraint logic verified: `NOT isempty(empty) = FALSE` (rejects), `NOT isempty(valid) = TRUE` (passes), `NOT isempty(NULL) = NULL` (chain-shape passthrough) ✓

### §N.4 post-deploy assertions (for E to run)
```sql
-- 1. Migration applied
SELECT count(*) FROM _migrations_applied WHERE filename = '572_ekv_c01_ledger_empty_daterange_repair.sql';
-- → 1

-- 2. No empty rows remain
SELECT count(*) FROM brahma_prospective_ledger WHERE isempty(observation_window);
-- → 0

-- 3. Open-lifecycle count (was 35, minus 6 deleted = 29)
SELECT count(*) FROM brahma_prospective_ledger WHERE lifecycle_status = 'open';
-- → 29

-- 4. Negative-insert: must error with constraint violation
-- INSERT INTO brahma_prospective_ledger (..., observation_window, ...) VALUES (..., 'empty'::daterange, ...);
```

---

## PRATINIDHI SIGN-OFF REQUEST — EKV-R-C01-001

**To:** PRATINIDHI
**From:** ṚTA-LEAD
**Re:** C-01 lane merge authorisation (product-table write)

**What this does:** Migration 572 DELETEs 6 corrupted rows from `brahma_prospective_ledger` and adds a CHECK constraint. The writer fix prevents future empty-range filings.

**Why it's safe:**
1. The 6 rows are permanently broken — can never be matched or resolved, crash the prediction-read path
2. Deletion scoped by `filed_by + generator_class + filing_method` — won't touch rows from other sources
3. Safety DO block aborts migration if unexpected empty rows remain from other sources
4. CHECK constraint is non-data-destructive — only blocks new bad inserts
5. Writer fix tested: 57/57 unit tests pass

**Cross-stream touch:** `w45_post_fit_rebuild.py` (Stream B's python-sidecar lease) — explicitly authorised by C-01 kickoff.

**Requested ruling:** Authorise merge of `ekv/c-01-ledger-repair` (commit `216fb0024`) via E's merge queue.

---

## C-03 — PR #1287 EXTENDED AND BUILT

**Status:** EKV-C-03-BUILT | **Branch:** `fix/prospective-ledger-empty-daterange` | **HEAD:** `3f0ee0908`

### State

PR #1287 (commit 525188467) was already directly on top of current `origin/main` — no rebase required (merge-base = `1d6f3ad5a` = main tip).

### Guards verified

**Read path 1 — `prospective_ledger.ts`:**
- `:592` `deriveWindowFields` — `const parsed = parseDaterange(...)` + `if (!parsed) return null-fields` ✓
- `:718/725` `matchOpenPredictionsForLelEvent` — point + interval paths both guard with `&& parseDaterange(row.observation_window)` ✓
- `parseDaterange` itself returns `null` for `'empty'` literal instead of throwing ✓

**Read path 2 — `query_prospective_ledger.ts` `toServed`:**
- Calls `deriveWindowFields(row)` which inherits the null guard above ✓
- New explicit test added: passes `observation_window='empty'` through handler; verifies no throw + null dates ✓

### Test results
- `prospective_ledger.test.ts`: **38/38** pass ✓
- `query_prospective_ledger.test.ts`: **9/9** pass (new empty-window test included) ✓

### Exit test (post-deploy, run by E)
```
standing_predictions_read({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', status: 'open'})
→ Must return without error; no prediction_id with null claim; open_count = 29 (after C-01 migration)
```

---

## HB-03 — W0 LANES ALL BUILT, AWAITING PRATINIDHI + E

C-01 (migration + writer): `ekv/c-01-ledger-repair` @ `216fb0024` — AWAITING EKV-R-C01-001
C-03 (PR #1287 extended): `fix/prospective-ledger-empty-daterange` @ `3f0ee0908` — READY FOR E MERGE

Proceeding to C-04 (W1): synthetic prediction lifecycle smoke on comparison chart.

---

## C-04 — LIFECYCLE SMOKE (W1)

**Status:** EKV-C-04-BLOCKED

### Block evidence

Full investigation of all write paths into `brahma_prospective_ledger`. Findings:

| Step | Tool/Path | Verdict |
|---|---|---|
| FILE (`→ open`) | `fileProspectivePrediction` / `prospective_ledger_file` | ✓ WORKS |
| READ | `standing_predictions_read` / `query_prospective_ledger` | ✓ WORKS (post C-03 deploy; currently crashes on empty rows) |
| MATCH (`open → matched`) | `matchOpenPredictionsForLelEvent` via `prediction_lifecycle_sweep` | ✓ WORKS — but requires a real LEL event that matches the prediction window |
| RESOLVE / DISMISS | Any MCP tool, API action, or TS function | ✗ **DOES NOT EXIST** |
| WITHDRAW (`→ withdrawn`) | Any path | ✗ **DOES NOT EXIST** — status is in the TS type but zero write paths |

**Root causes of block:**

1. **`mimamsa_outcome_record`** routes to `callPlatformPrim('record_outcome', ...)` → `/api/mcp/primitives/record_outcome` — `record_outcome` is NOT in `MCP_TO_RETRIEVAL_TOOL` whitelist → **400 error**.
2. **`ppl_writer.recordOutcome`** (called by the writes route's `record_outcome` action) is a **RETIRED no-op** — logs a warning, returns `{ok: false}`, writes nothing to `mcp_prediction_outcomes`.
3. **No `withdraw` / `dismiss` action** in `ALLOWED_ACTIONS` on `/api/mcp/writes/[action]/route.ts`.
4. **`withdrawn`** exists in `LifecycleStatus` type but has **no write path anywhere in the codebase** (confirmed: zero UPDATE hits targeting `withdrawn`).
5. **`resolved` / `dismissed`** are not valid lifecycle states for this table at all — not in the DB CHECK constraint.
6. **No cleanup path**: Filing a synthetic prediction cannot be reversed via any exposed MCP tool or API → would leave dirty data; so even the FILE step alone violates the "leave DB clean" requirement.

**Additional block: live stack not yet deployed.**
C-03 (parseDaterange null guard) has not been deployed. `standing_predictions_read` on the comparison chart currently crashes with `parseDaterange: could not parse daterange literal 'empty'` — confirmed by the C-02 diagnosis finding the same 2 empty-window rows on chart `1c826d5a`.

### Proposed degraded scope (for PRATINIDHI ruling)

Reduced C-04 that proves the loop with what exists:

1. **READ-path proof (post-deploy):** After E merges C-01 + C-03, call `standing_predictions_read({chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a', status: 'open'})` — must return without error with 0 empty-window predictions and `open_count >= 0` clean rows. This is the same exit test already contracted at C-03 §Exit test.
2. **MATCH-path proof (dry_run):** Call `prediction_lifecycle_sweep` with `chart_id='1c826d5a...'`, `dry_run: true` to show whether any open predictions are lapsed-eligible for matching — proves the sweep logic runs without error on the comparison chart.
3. **FILE omitted:** Until a `withdraw` / `delete_synthetic` write path exists, filing a synthetic prediction cannot leave the DB clean. Omit.

Full `open → matched → resolved → dismissed` lifecycle cannot be proven with the current codebase. This is a structural gap in the write surface, not a C-stream failure. Blocker disposition → PRATINIDHI.

---

## HB-04 — W0 LANES COMPLETE; C-04 BLOCKED, PROCEEDING TO C-05

C-01: `ekv/c-01-ledger-repair` @ `216fb0024` — AWAITING EKV-R-C01-001
C-03: `fix/prospective-ledger-empty-daterange` @ `3f0ee0908` — READY FOR E MERGE
C-04: EKV-C-04-BLOCKED — lifecycle smoke impossible (no dismiss/withdraw write path); degraded scope proposed above.

Proceeding to C-05 (W2): auto-filing cadence spec.

---

## C-05 — AUTO-FILING CADENCE SPEC (W2)

**Status:** EKV-C-05-BUILT

**Scope:** Spec only — no code diff. Cross-stream touch required (Stream B owns `w45_post_fit_rebuild.py`; Stream E owns cadence/infra). Coordination markers below.

---

### Finding (pre-spec audit, read from source)

`w45_post_fit_rebuild.py::seed_prospective_ledger` files via a **raw psycopg INSERT** that bypasses `fileProspectivePrediction`'s application-layer validation. Specific gaps found:

1. **`configuration_signature` absent from INSERT** — column list in `_insert_ledger_row_with_savepoint` (line ~456) has no `configuration_signature` field. The DB column is nullable (migration 458 confirms), so the INSERT succeeds silently with `configuration_signature = NULL`. But `fileProspectivePrediction` in TS enforces non-null for `generator_class='engine'` at line 494 — the raw INSERT bypasses this gate.

2. **Dedup uses `observation_window` equality, not `configuration_signature`** — `_window_already_filed` checks `WHERE chart_id=$1 AND event_class=$2 AND observation_window = daterange($3, $4)`. This correctly prevents exact-window duplicates on the same run, but it cannot distinguish a **stale window produced by the old fitted weights** from a **fresh window produced by the new fit** — they would have the same bounds but a different underlying engine configuration.

3. **No automatic cadence** — `w45_post_fit_rebuild.py` runs manually. After E-03 rebuilds gochara data (new field with updated λ weights), `seed_prospective_ledger` is not triggered automatically. New field windows are served by `kala_ahead_get` but the standing predictions ledger is only updated on a manual `w45_post_fit_rebuild.py` invocation.

4. **`kala_ahead_get` auto-filing is already working** — `ahead_autofile.ts` handles the `kala_ahead_get` → `brahma_prospective_ledger` path with idempotency by `source_citation`. This is NOT the same as the engine-cadence path and is not the gap C-05 addresses.

---

### SPEC — Part 1: Stream B change (`w45_post_fit_rebuild.py`)

**File:** `platform/python-sidecar/scripts/kala_admission/w45_post_fit_rebuild.py`
**Stream B lease:** `platform/python-sidecar/**`
**Authorisation:** C-05 spec; Stream B pickup via `EKV-C05-SPEC-B` coordination marker.

#### 1a. Add `configuration_signature` computation

Add a Python equivalent of `computeConfigurationSignature` (TypeScript: `platform/src/lib/lel/prospective_ledger.ts`):

```python
import hashlib

def _compute_configuration_signature(
    chart_id: str,
    event_class: str,
    temporal_shape: str,
    window_start: date,
    window_end: date,
    peak_date: date,
    peak_basis: str,
    fact_ids: list[str],
    system_ids: list[str],
) -> str:
    """Python port of computeConfigurationSignature (prospective_ledger.ts).

    Format: `{peak_basis}:{sha256_hex}`
    Hash input: `v1|{chart_id}|{event_class}|{temporal_shape}|{window_start}|{window_end}|
                  {peak_date}|{peak_basis}|{sorted_fact_ids}|{sorted_system_ids}`
    """
    sorted_facts = "|".join(sorted(set(str(f) for f in fact_ids)))
    sorted_systems = "|".join(sorted(set(str(s) for s in system_ids)))
    payload = "|".join([
        "v1",
        str(chart_id),
        str(event_class),
        str(temporal_shape),
        str(window_start),
        str(window_end),
        str(peak_date),
        str(peak_basis),
        sorted_facts,
        sorted_systems,
    ])
    hash_hex = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{peak_basis}:{hash_hex}"
```

The `kala_gochara_windows` SELECT (already querying `TABLE_WINDOWS`) should be extended to include the fields needed:

```sql
SELECT event_class, window_start, window_end, signed_intensity,
       peak_date, peak_basis,
       active_sentences,   -- JSONB: list of {fact_ids: [...]} objects
       contributing_systems  -- JSONB: list of {system_id: "..."} objects
  FROM kala_gochara_windows
 WHERE chart_id = %s AND era_slice_key LIKE 'g3_%%' AND window_end >= %s
 ORDER BY signed_intensity DESC LIMIT %s
```

If `peak_date`, `peak_basis`, `active_sentences`, or `contributing_systems` are NULL for a row, fall back to a degenerate signature: `w45_post_fit_rebuild:v1:{chart_id}:{event_class}:{window_start}:{window_end}` (the current-effective dedup key, honestly labelled).

#### 1b. Add `configuration_signature` to INSERT

```python
cur.execute(
    f"""
    INSERT INTO {TABLE_LEDGER} (
        chart_id, claim, event_class, claim_shape,
        observation_window, model, formula_version,
        confidence, falsifier, as_of,
        generator_class, filed_by, filing_method,
        source_citation,
        configuration_signature        -- ← NEW
    ) VALUES (
        %s, %s, %s, %s,
        daterange(%s, %s),
        %s, %s, %s, %s,
        NOW(), 'engine', %s, 'explicit_filing_tool',
        %s,
        %s                             -- ← NEW
    )
    """,
    (chart_id, claim, event_class, claim_shape,
     window_start, window_end,
     MODEL_TAG, FORMULA_VERSION, confidence, falsifier,
     FILED_BY, SOURCE_CITATION,
     configuration_signature),          # ← NEW
)
```

#### 1c. Upgrade `_window_already_filed` dedup

Replace the current `observation_window = daterange(...)` dedup with a `configuration_signature` dedup:

```python
def _window_already_filed(
    conn, chart_id: str, event_class: str,
    configuration_signature: str | None,
    window_start: date, window_end: date
) -> bool:
    """Dedup by configuration_signature when available; fall back to window bounds.

    configuration_signature dedup: if the EXACT engine configuration that produced
    this window was already filed, skip — even if the window bounds are the same.
    Window-bounds fallback: if configuration_signature is None (schema-level fields
    missing), fall back to exact-bounds dedup.
    """
    if configuration_signature is not None:
        sql = f"""
            SELECT 1 FROM {TABLE_LEDGER}
             WHERE chart_id = %s AND event_class = %s
               AND configuration_signature = %s LIMIT 1
        """
        params = (chart_id, event_class, configuration_signature)
    else:
        sql = f"""
            SELECT 1 FROM {TABLE_LEDGER}
             WHERE chart_id = %s AND event_class = %s
               AND observation_window = daterange(%s, %s) LIMIT 1
        """
        params = (chart_id, event_class, window_start, window_end)
    ...
```

**Why this matters:** After a gochara rebuild (new fitted weights → new `λ` values → different `contributing_systems` / `peak_basis`), the same `(event_class, window_start, window_end)` triple can represent a genuinely different engine configuration. Deduplication by `configuration_signature` ensures:
- Same configuration re-served → skip (idempotent)
- New configuration (post-rebuild) → file new row (the ledger records WHICH configuration produced WHICH claim)
- Old rows coexist with new ones; the lifecycle matcher sees both and can score them independently

#### Unit tests

Add to `test_w45_post_fit_rebuild.py`:
1. `_compute_configuration_signature` produces identical output for identical inputs (reproducibility)
2. `_window_already_filed` with a matching `configuration_signature` returns True (skip)
3. `_window_already_filed` with a different `configuration_signature` for the same window returns False (file new row)
4. `_insert_ledger_row_with_savepoint` includes `configuration_signature` in the persisted row

---

### SPEC — Part 2: Stream E cadence (post-rebuild auto-run)

**Stream E lease:** deploys, jobs, infra.
**Authorisation:** C-05 spec; Stream E pickup via `EKV-C05-SPEC-E` coordination marker.

**Trigger:** `w45_post_fit_rebuild.py` should run automatically after each successful gochara rebuild (E-03: `brahma-build-pipeline-job` gochara field build, both charts). It should NOT run if the gochara build exited non-zero.

**Implementation options (in preference order):**
1. **Post-build step in the Cloud Run job**: add `w45_post_fit_rebuild.py` as a final substep in the existing `brahma-build-pipeline-job` spec, conditional on gochara field build exit 0. This keeps cadence and build in one atomic unit.
2. **Cloud Run job scheduled trigger**: a separate scheduled Cloud Run invocation of `w45_post_fit_rebuild.py` daily at 02:00 IST (following the gochara nightly rebuild window). Simpler but decoupled from build success.

**Option 1 is preferred** — it guarantees the ledger is refreshed with the current field's windows, never with stale ones. Option 2 is the degrade if Option 1's scope is too large for this campaign.

**Command:**
```bash
python3 -m scripts.kala_admission.w45_post_fit_rebuild \
  --run-id $(date +%Y%m%dT%H%M%S)_cadence \
  --chart-ids 482012f1-710e-4a25-994a-93821f5871aa,1c826d5a-41cb-4450-b4dc-59d440e5f75a
```

**Env:** same DB credentials as the build job (`DATABASE_URL` / `DB_PASSWORD` from Cloud Run secrets). No new secrets required.

**Exit codes:**
- `0`: all cadence steps succeeded (0 or more rows filed)
- `1`: partial failure (some charts succeeded, some failed) — log and continue
- `2`: called with no arguments / configuration error (existing orchestrator convention)

**Non-blocking:** a cadence failure MUST NOT block or roll back the gochara rebuild. The cadence step is a best-effort side-effect; the build result is authoritative regardless.

---

### Coordination markers

```
EKV-C05-SPEC-B: Stream B — w45_post_fit_rebuild.py: (1) add _compute_configuration_signature
  Python port of computeConfigurationSignature; (2) include configuration_signature in
  _insert_ledger_row_with_savepoint INSERT; (3) upgrade _window_already_filed to dedup
  by configuration_signature when available. Spec in LEDGER_C.md §C-05. No migration needed
  (DB column already nullable). Tests: 4 new unit tests listed in spec.

EKV-C05-SPEC-E: Stream E — cadence job: run w45_post_fit_rebuild.py after each successful
  gochara rebuild (E-03). Preferred: post-build substep in brahma-build-pipeline-job.
  Degrade: daily scheduled Cloud Run invocation. Non-blocking: failure must not block build.
  Spec in LEDGER_C.md §C-05.
```

---

## HB-05 — ALL C-LANES COMPLETE

C-01: `ekv/c-01-ledger-repair` @ `216fb0024` — AWAITING EKV-R-C01-001
C-03: `fix/prospective-ledger-empty-daterange` @ `3f0ee0908` — READY FOR E MERGE
C-04: EKV-C-04-BLOCKED — degraded scope: read-path proof post-deploy only; no dismiss/withdraw path exists
C-05: EKV-C-05-BUILT — spec complete; coordination markers EKV-C05-SPEC-B and EKV-C05-SPEC-E posted

Stream C ṚTA wave complete. All deliverables at highest achievable confidence given current codebase state. Pending: PRATINIDHI ruling on EKV-R-C01-001 (C-01 merge) + C-04 degraded scope authorisation. Handoff to E + B for implementation.
