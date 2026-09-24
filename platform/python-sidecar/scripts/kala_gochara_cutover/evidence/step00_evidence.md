# Step 0 evidence — Phase 1.1

Runbook step 0 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Phase 1.1 — Clear is_active filter + (table, generation) guard (consumes origin/l3/kala-p1-1-b1-clear-guard, cherry-pick eb00da67d with attribution)
- **Gate:** route test green; stale migration-540 comment at clear/route.ts:95-96 gone
- **Reversal:** revert cherry-pick
- **DSN target:** n/a — git/TS-layer step, no DSN; tranche branch l3/gochara-autonomous-wp0-7
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, §7.B tranche 1) — git + vitest only

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-24 — GREEN

- Branch state: `git merge-base --is-ancestor eb00da67d origin/main` → NOT merged → cherry-pick required.
- Cherry-pick: `git cherry-pick -x eb00da67d` → clean, landed as **cacc72440**
  ("fix(kala-l3): close the live Clear path into the protected Gochara v1 snapshot (B1)",
  attribution `-x` trailer present). Carries the B1 change set including migrations
  1071/1072 (no collision with origin/main, whose head migration is 1070; the
  migration-number guard passes — `npm run guard:migration-numbers` PASS, only the
  three inherited supabase header-mismatch advisories). Applying 1071/1072 to
  production is NOT in this tranche's step-4 scope (1080/1081 only, per the A-2
  native-rulings reading).
- Stale migration-540 comment at `clear/route.ts:95-96`: GONE — the comment block now
  carries the corrected wording referencing migration 1072 (`route.ts:148-150`); the
  `is_active` filter is present (`route.ts:143`, `WHERE COALESCE(is_active, TRUE)`).
- Gate test: `npx vitest run src/app/api/cockpit/clear/__tests__/route.protected-assets.test.ts`
  → **2 passed (2/2)**, file 1 passed.

**Verdict: step 0 GREEN.**
