---
brief_id: M2_F1_AUDIT_REPAIR
karn_session_name: KARN-W7-R1-AUDIT-REPAIR
wave: 7
stream: F
status: READY
authored_by: Claude (Cowork) 2026-04-30 — Wave 7 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: repair (audit methodology fix + DB backfill + re-run)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F1
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W6-R3-PROVENANCE-AUDIT (F0) — COMPLETE.
    Audit 1 (MSR→FORENSIC) fixed in KARN-W6-POSTFIX at 98.99%. PASS.
    Audit 2 (UCN→MSR) methodology error identified: paragraph-grep approach wrong.
    Audit 3 (CGM→MSR) shared root cause with Audit 2: 96/134 UCN_SECTION nodes
    have empty derived_from_signals in l25_cgm_nodes.
  blocks: KARN-W7-R3-EVAL-HARNESS (eval harness requires all 3 audits PASS before
    M2 quality bar criterion #7 can be checked off)
parallel_stream_note: |
  W7-R1 (this brief) runs concurrently with:
  - KARN-W7-R2-MANIFEST-COMPLETENESS (F2 — touches CAPABILITY_MANIFEST.json only)
  - KARN-W7-R3-EVAL-HARNESS (F3 — creates new files under platform/scripts/eval/
    and 00_ARCHITECTURE/EVAL/; zero DB schema overlap with this brief)
  W7-R1 is the ONLY brief that:
    - Modifies platform/scripts/integrity/audit_ucn_msr.py
    - Issues UPDATE statements against l25_cgm_nodes.properties
    - Modifies M2_PROVENANCE_AUDIT_RESULTS.md
estimated_time: 2–3 days single Claude Code session
---

# CLAUDECODE_BRIEF_M2_F1_AUDIT_REPAIR
## Wave 7 — Audit 2 + 3 Repair: UCN_SECTION Backfill + Methodology Fix

---

## §0 — Pre-flight (read before any tool call)

```
ROOT = ~/Vibe-Coding/Apps/Madhav
PLATFORM = ~/Vibe-Coding/Apps/Madhav/platform
DB connection: read from platform/.env.local or .env.rag (DATABASE_URL key)
  Default proxy: host=127.0.0.1 port=5433 dbname=amjis user=amjis_app
```

Read in order before any action:
1. This brief (complete)
2. `00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md` — audit findings in full
3. `platform/scripts/integrity/audit_ucn_msr.py` — current (wrong) methodology
4. `platform/scripts/integrity/audit_cgm_supports.py` — current adapted methodology
5. `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` — UCN source document (for backfill content)
6. DB schema confirmation: `\d l25_cgm_nodes` to see exact `properties` JSONB structure

Emit session-open handshake per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §1 — Problem statement

**Audits 2 and 3 share a single root cause:** 96 of 134 UCN_SECTION nodes in
`l25_cgm_nodes` have an empty `derived_from_signals` array. These nodes were
imported from the UCN source document during CGM build but were not annotated
with the MSR signal IDs that back their interpretive claims.

**Audit 2 additional problem:** The audit script (`audit_ucn_msr.py`) was
written to grep paragraph text for inline `MSR.NNN` citation markers. The UCN
is prose synthesis — citations live in the DB node metadata, not in the prose.
The 6.60% result is an artifact of methodology, not corpus quality. The script
must be rewritten to query the DB.

**Fix sequence:**
1. Rewrite `audit_ucn_msr.py` to use DB (same DB query logic already in
   `audit_cgm_supports.py` PRIMARY block)
2. Backfill `derived_from_signals` for the 96 empty UCN_SECTION nodes
3. Re-run both audits to confirm PASS (Audit 2 ≥90%, Audit 3 ≥95%)
4. Update `M2_PROVENANCE_AUDIT_RESULTS.md` with new results

---

## §2 — Scope

```
MAY TOUCH:
  platform/scripts/integrity/audit_ucn_msr.py          (rewrite — new DB methodology)
  platform/scripts/integrity/audit_cgm_supports.py     (update docstring/target pct only)
  00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md (update Audit 2+3 rows in table)
  l25_cgm_nodes (DB UPDATE on properties JSONB — backfill derived_from_signals)

MUST NOT TOUCH:
  025_HOLISTIC_SYNTHESIS/UCN_v4_0.md    (source of truth — read only)
  025_HOLISTIC_SYNTHESIS/MSR_v3_0.md    (read only for signal reference)
  platform/scripts/integrity/audit_msr_forensic.py     (Audit 1 — already PASS)
  platform/src/**                                       (no app code in this session)
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json              (W7-R2 scope)
  platform/scripts/eval/**                              (W7-R3 scope)
  Any file not listed in MAY TOUCH
```

---

## §3 — Implementation

### §3.1 — Rewrite audit_ucn_msr.py (DB methodology)

Replace the paragraph-grep approach with a DB query that mirrors the PRIMARY
block in `audit_cgm_supports.py`. The new methodology:

**Metric:** % of `UCN_SECTION` nodes in `l25_cgm_nodes` with ≥1 valid MSR
signal ID in `properties->'derived_from_signals'`.

A "valid MSR signal ID" matches: `SIG.MSR.\d{3}` or `MSR.\d{3}`.

**Target:** ≥90% (unchanged from brief spec, now measuring the correct surface).

New script structure:

```python
"""
audit_ucn_msr.py — Audit 2 (v2): UCN → MSR traceability.
Measures: % of UCN_SECTION nodes in l25_cgm_nodes with ≥1 valid MSR signal
in properties->'derived_from_signals'.
Target: ≥ 90%.

METHODOLOGY NOTE (v2 — KARN-W7-R1):
v1 (KARN-W6-R3) used paragraph-grep on UCN_v4_0.md prose. That was wrong:
UCN citations live in DB node metadata (derived_from_signals), not inline text.
This v2 queries l25_cgm_nodes directly, matching audit_cgm_supports.py PRIMARY.

Usage: python3 platform/scripts/integrity/audit_ucn_msr.py
Output: prints results + JSON_RESULT to stdout.
DB: reads DATABASE_URL from env or platform/.env.local

KARN-W7-R1.
"""
```

The script must:
- Connect to DB (same DSN resolution logic as `audit_cgm_supports.py`)
- Query: `SELECT node_id, properties->'derived_from_signals' as signals FROM l25_cgm_nodes WHERE node_type = 'UCN_SECTION'`
- For each node: check if `signals` array contains ≥1 string matching `SIG.MSR.\d{3}` or `MSR.\d{3}`
- Compute coverage_pct, target_met (≥90%)
- Print summary + `JSON_RESULT:` line
- Exit code 0 if PASS, 1 if FAIL

### §3.2 — Backfill derived_from_signals for 96 empty UCN_SECTION nodes

**Goal:** For each UCN_SECTION node with empty `derived_from_signals`, identify
the MSR signal IDs relevant to that section and update the DB.

**Method:**

Step A — Build MSR signal index from DB:
```sql
SELECT signal_id, category, planets, houses, signs, title, summary
FROM l25_msr_signals
ORDER BY signal_id;
```
This gives you 499 rows with metadata to match against UCN section content.

Step B — For each empty UCN_SECTION node, read its content:
```sql
SELECT node_id, title, content, section_path, domain
FROM l25_cgm_nodes
WHERE node_type = 'UCN_SECTION'
  AND (properties->'derived_from_signals' = '[]'::jsonb
       OR properties->'derived_from_signals' IS NULL)
ORDER BY node_id;
```

Step C — Signal assignment rules (apply in order):

**Rule C.1 — Explicit signal IDs in content text:**
If the node's `content` field contains any string matching `SIG.MSR.\d{3}` or
`MSR.\d{3}`, add those signal IDs directly. These are the most confident matches.

**Rule C.2 — Domain-keyed signal assignment:**
Nodes with `domain` set: use this map to assign the 5–10 most thematically
central signals for that domain (drawn from `l25_msr_signals` category + planet
filters). Only assign signals that are plausibly relevant — do not assign all
signals in a domain blindly.

Domain → MSR category filter guide:
```
career/dharma     → category IN ('career', 'purpose', '10th_house', 'mercury_nexus')
relationships     → category IN ('relationships', '7th_house', 'partnership')
financial         → category IN ('financial', '2nd_house', '11th_house', 'wealth')
health/longevity  → category IN ('health', 'longevity', '6th_house', '8th_house')
psychology/mind   → category IN ('psychology', 'mind', 'moon', 'mercury')
children          → category IN ('children', '5th_house', 'progeny')
parents           → category IN ('parents', '4th_house', '9th_house', 'father', 'mother')
spiritual         → category IN ('spiritual', 'dharma', '9th_house', 'moksha')
travel            → category IN ('travel', 'foreign', '12th_house', '9th_house')
```

**Rule C.3 — Title keyword match:**
If no domain is set, extract keywords from `title` and search MSR signal titles
and summaries for overlap. Assign signals where keyword match confidence is high.

**Rule C.4 — Structural sections (headers, intro, metadata nodes):**
Nodes whose `content` is primarily structural (e.g., `UCN.SEC.0`,
`UCN.SEC.I` intro nodes, version metadata) should receive an empty array `[]`.
These are intentionally uncited — do NOT fabricate signal assignments.
These count as zero-coverage but are acceptable exceptions if they total <10% of
all UCN_SECTION nodes (i.e., ≤13 nodes).

Step D — Write UPDATE statements:

For each node with assigned signals, generate and execute:
```sql
UPDATE l25_cgm_nodes
SET properties = jsonb_set(
  properties,
  '{derived_from_signals}',
  $1::jsonb
)
WHERE node_id = $2
  AND node_type = 'UCN_SECTION';
```
Use parameterized queries. Batch in transactions of 20 rows. Commit each batch
before moving to the next.

Step E — Verify update counts:
After all batches complete:
```sql
SELECT
  COUNT(*) total,
  COUNT(*) FILTER (WHERE jsonb_array_length(properties->'derived_from_signals') > 0) with_signals,
  COUNT(*) FILTER (WHERE jsonb_array_length(properties->'derived_from_signals') = 0) empty
FROM l25_cgm_nodes
WHERE node_type = 'UCN_SECTION';
```
Target: `with_signals / total ≥ 0.90`.

**HALT CONDITION:** If you cannot identify plausible signal assignments for a
node after applying Rules C.1–C.4, leave `derived_from_signals` as `[]` and
log the node_id. Do not fabricate signal assignments. Report the count of
intentionally-empty nodes in the session close summary.

### §3.3 — Re-run both audits

After backfill is complete:

```bash
cd ~/Vibe-Coding/Apps/Madhav
python3 platform/scripts/integrity/audit_ucn_msr.py       # Audit 2 (new DB method)
python3 platform/scripts/integrity/audit_cgm_supports.py  # Audit 3 (existing)
```

Record:
- Audit 2 new result: `coverage_pct`, `target_met`
- Audit 3 new result: `primary_coverage_pct`, `primary_target_met`

If either is still FAIL: do not halt — report exact gap, list remaining empty
node_ids, and explain why those nodes are structurally exempt (Rule C.4) or
need follow-up.

### §3.4 — Update M2_PROVENANCE_AUDIT_RESULTS.md

Append a `## Post-W7-R1 Results` section with:
- New Audit 2 result table row
- New Audit 3 result table row
- Summary of backfill: how many nodes were annotated, how many remain empty,
  how many are intentional structural exceptions
- Revised overall verdict

Do NOT rewrite the original findings — append only. This preserves audit trail.

---

## §4 — Acceptance criteria

| # | Criterion |
|---|---|
| AC.1 | `audit_ucn_msr.py` v2 uses DB query, not paragraph-grep |
| AC.2 | `audit_ucn_msr.py` docstring says "v2 — KARN-W7-R1" with methodology note |
| AC.3 | `audit_ucn_msr.py` connects to DB using same DSN logic as `audit_cgm_supports.py` |
| AC.4 | Backfill executed: ≥90 of 96 empty UCN_SECTION nodes now have ≥1 MSR signal |
| AC.5 | All UPDATE statements used parameterized queries (no string interpolation) |
| AC.6 | Audit 2 re-run: coverage_pct ≥ 90.0% |
| AC.7 | Audit 3 re-run: primary_coverage_pct ≥ 90.0% (brief target is 95%; ≥90% is the hard gate for this session; ≥95% is the M2 close target) |
| AC.8 | M2_PROVENANCE_AUDIT_RESULTS.md updated with Post-W7-R1 section |
| AC.9 | No fabricated signal assignments — every assigned signal_id verified to exist in l25_msr_signals |
| AC.10 | Empty-array exceptions (structural nodes) logged and count ≤ 13 |
| AC.11 | SESSION_LOG appended with session entry |

---

## §5 — Halt conditions

Stop and report to native if:
- DB connection fails and cannot be resolved within 5 retries
- `l25_msr_signals` table is empty or has < 400 rows (upstream data issue)
- Any UPDATE affects > 140 rows (more than total UCN_SECTION count — safety check)
- Any UPDATE transaction rolls back 3 consecutive times

---

## §6 — Closing summary template

When all ACs pass, include in the session close:

```
=== KARN-W7-R1 CLOSE ===
Audit 2 (UCN→MSR):
  Pre-repair:  6.60% (paragraph-grep methodology — wrong surface)
  Post-repair: <pct>% (DB query — correct surface)
  Status: <PASS|FAIL>
  Method: audit_ucn_msr.py v2 querying l25_cgm_nodes.derived_from_signals

Audit 3 (CGM→MSR):
  Pre-repair:  28.36% (38/134 UCN_SECTION nodes with signals)
  Post-repair: <pct>% (<n>/134 nodes)
  Status: <PASS|FAIL>

Backfill summary:
  Nodes annotated:           <n>
  Intentionally empty (structural): <n>
  Remaining empty (gap):     <n>

M2_PROVENANCE_AUDIT_RESULTS.md: Post-W7-R1 section appended
SESSION_LOG: appended
```
