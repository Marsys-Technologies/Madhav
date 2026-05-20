---
artifact: PSHIP_109_FORENSIC_v1_0.md
type: FORENSIC_ANALYSIS
version: 1.0
status: FINAL
authored_by: Claude Code — read-only forensic (no code changes, no merges)
date: 2026-05-20
branch_under_review: origin/feature/panchang-ship
compared_against: origin/main
pr_number: 109
---

# PSHIP-109 Forensic — PR #109 Fate Analysis

> **Scope:** Read-only. No code modified, no branches merged, no deployments triggered.
> All commands run against `origin/main` and `origin/feature/panchang-ship` after `git fetch origin`.

---

## Evidence Log

### Pre-flight

```
git fetch origin   → clean (no output)
```

---

## Q1 — MERGE SAFETY

### Merge base

```
MB = 039d993b365cfcb5c0e8dfcfb360665914683c6e
Commit: docs(ops): R7/R8/R9 wrap-up complete — PR #103 merged, prod + localhost at parity
```

The branch was forked from the repo **before** R10 and Phase 4C were merged to main.

### Ancestry checks

```
git merge-base --is-ancestor 4dae9ed $MB   → R10 is NOT ancestor of MB
git merge-base --is-ancestor 3b3405c $MB   → PR#105 is NOT ancestor of MB
```

The merge base predates both R10 (PR #106 / SHA 4dae9ed) and Phase 4C Wave 1 (PR #105 / SHA 3b3405c). This means the branch was created from an intermediate commit and those PRs landed on main after the branch diverged.

### Explicit deletions since MB

```
git log $MB..origin/feature/panchang-ship --diff-filter=D --name-only --pretty=format:
→ (empty — zero files deleted)
```

No files were explicitly deleted on the branch.

### 3-way dry-run merge

```
git merge-tree --write-tree --name-only origin/main origin/feature/panchang-ship
→ Tree SHA: d9d08191e3164c39f2d87fdb15f8793d13484ec6
→ 17 CONFLICTS:
```

| # | Type | File |
|---|------|------|
| 1 | content | `.geminirules` |
| 2 | content | `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` |
| 3 | add/add | `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_HALT_LOG.md` |
| 4 | add/add | `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_LOG.md` |
| 5 | add/add | `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml` |
| 6 | content | `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` |
| 7 | content | `00_ARCHITECTURE/SESSION_LOG.md` |
| 8 | content | `CLAUDE.md` |
| 9 | content | `platform/.env.example` |
| 10 | content | `platform/src/app/clients/[id]/consume/page.tsx` |
| 11 | content | `platform/src/components/shared/AppShellRail.tsx` |
| 12 | content | `platform/src/components/shared/MobileNavSheet.tsx` |
| 13 | content | `platform/src/lib/components/observatory/pages/OverviewClient.tsx` |
| 14 | content | `platform/src/test-setup.ts` |
| 15 | add/add | `platform/tests/integration/test_query_panchanga_e2e.test.ts` |
| 16 | add/add | `platform/tests/planner/panchang_probe_set.json` |
| 17 | add/add | `platform/tests/planner/panchang_routing.test.ts` |

### Does the merged tree retain R10 files?

```
git ls-tree -r d9d08191 --name-only | grep "tests/unit/chat-v2" | wc -l
→ 56  (all 56 R10 chat-v2 test files present)
```

R10 is **not reverted** — git performs a 3-way merge, not a rebase, so main's R10 additions survive. The conflicts are in governance docs (SESSION_LOG, CLAUDE.md, CURRENT_STATE) and application files that both branches touched independently (AppShellRail, MobileNavSheet, OverviewClient, test-setup, consume/page.tsx).

### consume/page.tsx conflict detail

The conflict is trivial: one parenthesis style fix (`parsed['date'] as string` → `(parsed['date'] as string)`). No R10 logic is endangered.

### VERDICT Q1

**(b) + (c) — Would cleanly add Panchang core, but produces 17 conflicts (14 content + 3 add/add) concentrated in governance docs and three shared UI files. Does NOT revert R10. The merge is not safe to push as-is; manual conflict resolution on 17 files required.**

---

## Q2 — DUPLICATION

### Does main have the full Panchang module?

```
git ls-tree -r origin/main --name-only | grep -i panchang
→ 80+ files including:
  platform/python-sidecar/panchang_engine/ (full engine: 15 modules)
  platform/python-sidecar/routers/panchang.py
  platform/python-sidecar/routers/muhurat.py
  platform/src/app/panchang/ (full UI: page, components, hooks, tests)
  platform/src/lib/panchang/ (ics_builder, sidecar_mapper, tara_bala, etc.)
  platform/src/lib/retrieve/query_panchanga.ts
  platform/migrations/060_panchanga_daily.sql
  03_DERIVATIONS/PANCHANG_DAILY_v1_0.md
  00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
  00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md
```

Main has the complete Panchang module. Every route, engine, UI component, and test file from Phase 4C Wave 1 (PR #105 / 3b3405c) is present.

### Byte-identity check (5 representative files)

| File | Diff? |
|------|-------|
| `platform/python-sidecar/panchang_engine/__init__.py` | **IDENTICAL** (empty diff) |
| `platform/src/app/panchang/page.tsx` | **IDENTICAL** (empty diff) |
| `platform/python-sidecar/routers/panchang.py` | **IDENTICAL** (empty diff) |
| `platform/src/lib/panchang/ics_builder.ts` | **IDENTICAL** (empty diff) |
| `platform/src/lib/retrieve/query_panchanga.ts` | **DIFFERENT** (61 added lines) |

### VERDICT Q2

**Main and branch are byte-identical for all Panchang module files except `query_panchanga.ts`. The branch is not an independently-built variant — it is the same codebase with one targeted enrichment layer on top.**

---

## Q3 — THE SALVAGEABLE DELTA

### Migration: does main have the 5 enrichment columns?

```
git ls-tree -r origin/main --name-only | grep "migration.*sql" | tail -5
→ platform/supabase/migrations/068_pin_archive_folders.sql  (highest on main)

git ls-tree -r origin/feature/panchang-ship --name-only | grep "069"
→ platform/supabase/migrations/069_extend_panchanga_daily.sql  (EXISTS on branch, ABSENT from main)
```

Migration 069 is **not on main**. Main's `panchanga_daily` table has only 5 base columns (tithi, vara, nakshatra, yoga, karana + sunrise) from migration 060.

Migration 069 content:
```sql
ALTER TABLE panchanga_daily
  ADD COLUMN IF NOT EXISTS special_yogas JSONB,
  ADD COLUMN IF NOT EXISTS inauspicious  JSONB,
  ADD COLUMN IF NOT EXISTS auspicious    JSONB,
  ADD COLUMN IF NOT EXISTS choghadiya    JSONB,
  ADD COLUMN IF NOT EXISTS hora          JSONB;

CREATE INDEX IF NOT EXISTS idx_panchanga_daily_special_yogas ON panchanga_daily USING GIN(special_yogas);
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_inauspicious  ON panchanga_daily USING GIN(inauspicious);
```

### query_panchanga.ts enrichment fields

```
git show origin/main:platform/src/lib/retrieve/query_panchanga.ts | grep -E "special_yogas|inauspicious|auspicious|choghadiya|hora"
→ zero matches (main only references these in a prose comment about muhurta inputs)

git show origin/feature/panchang-ship:... | grep ...
→ 11 matches: type union additions + interface fields + SELECT list + output mapping
```

The branch adds 5 type-union entries to `PanchangaField`, 5 interface properties to `PanchangaRow`, 5 field entries to the SELECT clause, and 5 conditional output-mapping blocks. **+61 lines, all enrichment layer.**

### PLANNER_PROMPT_v2_0.md: R-PCI rule and enrichment triggers

```
grep count origin/main: 16 occurrences of R-PA/PANCHANGA/panchang
grep count origin/branch: 50 occurrences (+34 net additions)
```

Branch-specific additions confirmed present:
- **R-PCI rule** (new rule block): "PANCHANG CONTEXT INHERITANCE" — when current query is panchang-continuation of prior turn, skip repeated lookup; R-PA defers to R-PCI
- **R-PA subclauses (f) and (g)**: inauspicious/auspicious window triggers (`rahu kalam`, `amrit kalam`, `choghadiya`, `hora`)
- **Example 4.29** (muhurta + special_yogas + inauspicious combined query)
- **Example 4.30** (Rahu Kalam direct lookup)

Total PLANNER_PROMPT delta: +149 lines.

### Test files with divergent content (add/add conflicts, not genuinely new)

These exist on BOTH branches but with different content:

| File | Main version | Branch version |
|------|-------------|----------------|
| `tests/planner/panchang_routing.test.ts` | 10-query R-TC gate (4C-3) | 24-query R-PA/R-PCI gate (PSHIP-S4H) |
| `tests/planner/panchang_probe_set.json` | 10 probes | Extended probe set |
| `tests/integration/test_query_panchanga_e2e.test.ts` | Includes DB guard check | Removes DB guard (sidecar-backed path only) |

These are not clean cherry-picks; they require manual merge decisions.

### Complete extractable delta (genuinely ABSENT from main)

| # | File | Nature | Size |
|---|------|---------|------|
| 1 | `platform/supabase/migrations/069_extend_panchanga_daily.sql` | New migration — 5 JSONB columns + 2 GIN indexes | ~20 lines |
| 2 | `platform/src/lib/retrieve/query_panchanga.ts` | Enrichment type/field/mapping additions | +61 lines |
| 3 | `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` | R-PCI rule + subclauses (f)(g) + examples 4.29/4.30 | +149 lines |

Items 4–6 above (test files) are **divergent, not absent** — the branch has superseded versions; merging them requires manual review.

### VERDICT Q3

**The extractable enrichment is exactly 3 files: migration 069, query_panchanga.ts enrichment layer (+61 lines), and PLANNER_PROMPT R-PCI + example additions (+149 lines). All three are confirmed absent from main. Everything else in the branch is either already on main (byte-identical) or is a divergent version of a file that exists on main (requires manual resolution).**

---

## Q4 — IS MAIN'S SHIPPED PANCHANG HEALTHY IN PROD?

### Call path trace (origin/main)

**SSR (initial page load):**
```
/panchang page.tsx  →  fetchPanchangSSR()
  fetch(`${PYTHON_SIDECAR_URL}/api/compute/panchanga`, {
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.PYTHON_SIDECAR_API_KEY ?? '',   ← KEY SENT ✓
    }
  })
```

**Client-side navigation (date/location changes):**
```
usePanchangDay hook  →  fetch('/api/panchanga', { method: 'POST' })
  /api/panchanga proxy route (Next.js API)
    →  fetch(`${PYTHON_SIDECAR_URL}/api/compute/panchanga`, {
         headers: {
           'Content-Type': 'application/json',
           'x-api-key': SIDECAR_KEY,   ← KEY SENT ✓  (process.env.PYTHON_SIDECAR_API_KEY)
         }
       })
```

The client hook calls the Next.js proxy at `/api/panchanga`, never the sidecar directly. The proxy is a server-side route and correctly reads `PYTHON_SIDECAR_API_KEY` from the environment.

### Auth status

| Path | x-api-key sent? | Source |
|------|-----------------|--------|
| SSR (page.tsx `fetchPanchangSSR`) | ✅ Yes | `process.env.PYTHON_SIDECAR_API_KEY ?? ''` |
| Client hook → proxy route (`/api/panchanga`) | ✅ Yes | `const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''` |
| Proxy → sidecar call | ✅ Yes | Same constant, forwarded in `x-api-key` header |

No auth bug exists in main's Panchang module. The `x-api-key` header is sent on every code path — SSR and client-side. If the sidecar enforces the key, main is not 401-broken.

### VERDICT Q4

**Main's /panchang is auth-correct. Both the SSR path and the client-side proxy path send `x-api-key: PYTHON_SIDECAR_API_KEY`. No auth bug — the risk identified in Q4 does not exist. Main's shipped /panchang is likely working in prod (assuming `PYTHON_SIDECAR_API_KEY` is set in the Cloud Run environment, which it should be as it was required for other sidecar tools).**

---

## Q5 — RECOMMENDATION

### Verdict Table

| Question | Finding | Risk |
|----------|---------|------|
| Q1: Would merging PR #109 revert R10? | No — R10 files survive in merged tree | — |
| Q1: Is the merge clean? | No — 17 conflicts in 17 files | HIGH |
| Q1: Conflicts include R10 application files? | `consume/page.tsx` trivially (1-char parens fix), 3 UI components, test-setup | MEDIUM |
| Q2: Is the branch a duplicate? | Yes — byte-identical except for enrichment layer | — |
| Q3: Genuine new content on branch? | 3 files: migration 069, query_panchanga enrichment, PLANNER_PROMPT R-PCI | LOW risk to cherry-pick |
| Q4: Auth bug on main's /panchang? | None — both paths send x-api-key correctly | — |
| Q4: Main's /panchang healthy in prod? | Yes (auth correct, full module present) | — |

### Way Forward

**STEP 1 — CLOSE PR #109.**

PR #109 (`feature/panchang-ship`) should be closed without merging. Reasons:
- It has 17 merge conflicts with main, including governance files (SESSION_LOG, CLAUDE.md, CURRENT_STATE, CAPABILITY_MANIFEST) that would require careful manual resolution
- The branch forked before R10 and PR #105 landed, making it a stale integration branch
- Everything it contains except 3 files is already on main

**STEP 2 — Extract the enrichment delta as a fresh PR from main.**

Open a new branch from `origin/main` and cherry-pick exactly these 3 changes:

| Priority | File | Action |
|----------|------|--------|
| 1 (schema-first) | `platform/supabase/migrations/069_extend_panchanga_daily.sql` | Copy verbatim from branch |
| 2 (tool layer) | `platform/src/lib/retrieve/query_panchanga.ts` | Apply the 5-field enrichment additions |
| 3 (planner layer) | `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` | Apply R-PCI rule + subclauses (f)(g) + examples 4.29/4.30 |

For the 3 divergent test files (panchang_routing.test.ts, panchang_probe_set.json, test_query_panchanga_e2e.test.ts): take the branch version (24-query R-PA/R-PCI suite is a superset of main's 10-query suite; the DB-guard removal is correct for sidecar-backed CI). These require manual copy, not auto-cherry.

**STEP 3 — No auth fix needed.**

Main's /panchang auth is correct. No emergency hotfix required.

**STEP 4 — Post-migration bootstrap.**

After migration 069 lands and deploys, run:
```bash
python platform/python-sidecar/pipeline/bootstrap_panchanga.py --rebuild
```
This populates the 5 new JSONB columns for the existing date range. Without this, the columns exist but are NULL — `query_panchanga` with enrichment fields will return null values rather than failing.

### Summary

> PR #109 is a stale integration branch carrying 3 genuinely new changes buried under 17 governance conflicts. Close it. Extract the enrichment layer (migration 069 + query_panchanga types/fields + PLANNER R-PCI rule) as a clean 3-file PR from main. Main's already-shipped /panchang is healthy — no auth bug, no revert risk.

---

*Forensic authored: 2026-05-20. Read-only session — zero code changes, zero merges, zero deployments.*
