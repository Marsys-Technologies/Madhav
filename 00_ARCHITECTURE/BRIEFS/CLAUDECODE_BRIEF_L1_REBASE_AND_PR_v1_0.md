# L1 Closure — Rebase + PR + Post-Merge Prod-Verify (paste into Claude Code / Antigravity)

**Context:** L1 Gaṇita Closure v2.0 is sealed on `feature/l1-phase3-enrichment` (tip `4f34c682`; close commit
`aa6cd122`), CONDITIONAL on a post-merge prod build (`L1_GANITA_CLOSURE_v2_0.md` §6). The branch is BEHIND main
(predates the hygiene merges: G52 elim, brief purge, CI-green fix, ga_structural floor bump). Red-team R6 requires
rebase before merge. Execute in order. Standards: surgical migrations only (≥ 310); ledger-reconcile
(`_migrations_applied` correct SHA); seed-consistency; only `482012f1`; merge-verify; prod-verify-before-claiming-
seal. Do NOT rebuild what's sealed (Gate-3 subsystems, PR #298 enrichment) — verify.

---

## STEP 1 — REBASE on main + reconcile the ga_structural overlap (R6)

```bash
git checkout feature/l1-phase3-enrichment
git fetch origin
git rebase origin/main
```

**⚠️ EXPECTED CONFLICT ZONE — ga_structural floor + AssetRow tests.** The hygiene pass on main ALSO changed
ga_structural's floor (`asset_registry_seed.ts`: 53,953 → 74,644, commit e01dbe10) and fixed
`AssetRow_CockpitPolishR2.test.tsx` (70c55e0c). This branch's migration 309 also touches ga_structural
count_sql + seed. On conflict:
- **ga_structural floor in seed:** take the value consistent with migration 309's intent — 74,644 conservative
  (both main's hygiene bump AND this branch landed on 74,644; confirm they AGREE, not silently diverge). If they
  differ, the branch's 309-aligned value wins, but VERIFY the number matches what migration 309's corrected
  count_sql would produce.
- **AssetRow test:** take MAIN's version (`getByTitle('CURRENT · healthy')`) — the branch must not revert the
  CI-green fix. If the branch has its own AssetRow edits, merge them on top of main's fix, keeping the test green.
- **Migration numbering:** confirm this branch's migrations are 308 + 309 and DON'T collide with anything main
  added in the hygiene pass (main's max — check `_migrations_applied` + the migrations dir). If 308/309 are taken
  on main, renumber this branch's to the next free numbers and update any references.

After rebase: `pytest platform/python-sidecar -q` AND the JS test suite → **0 failures** (incl. the AssetRow test
staying green). Confirm `git log --oneline origin/main..HEAD` shows only this closure's commits cleanly on top.

---

## STEP 2 — OPEN PR for native review

Open PR `feature/l1-phase3-enrichment` → `main`. PR body:
- The 5-phase closure summary + the v2.0 seal verdict.
- **Explicitly state the seal is CONDITIONAL**: prod-verify (§6 checklist) runs post-merge; FORENSIC 7/7 is
  resolved-in-code (static analysis) pending the prod build; ga_condition + ga_structural floors are deferred to
  migration 310 after the build measures them.
- BUG-1 (ga_structural count_sql scope-inflation) + migration 309 fix.
- The two carried red-team caveats (R1 FORENSIC prod-confirm, ga_structural exact floor).
- Link `L1_GANITA_CLOSURE_v2_0.md`.

Native single end-review → merge. After merge: `gh pr view <N> --json mergeCommit,state` to confirm.

---

## STEP 3 — POST-MERGE PROD BUILD + §6 verify (the REAL seal)

After merge, run the orchestrator build for `482012f1` against PROD, then complete `L1_GANITA_CLOSURE_v2_0.md §6`
checklist. Produce a PASS/FAIL table:
1. **FORENSIC 7/7** — no new CONDUCTOR_HALT_LOG entries; all 5 ayanamshas pass the forensic gate (this is the
   prod confirmation the R1 caveat was waiting for).
2. **ga_strength count** ≥ 11,936; **ga_sensitive** ≥ 8,610 (via their count_sql on prod).
3. **ga_structural** — run the corrected (mig 309) count_sql; RECORD the actual value.
4. **ga_condition** — run the combined count_sql; RECORD the actual value.
5. **Floored items ARE floored (not fabricated):** `graha_kala_bala_per_varga` fact_value_num = NULL;
   `special_lagna` VIGHATI_LAGNA fact_value_num = NULL; the D1-only avasthas floored. (The integrity gate, on prod.)
6. **Deeptadi references dignity:** spot-check one graha — per-varga deeptaadi state matches its
   graha_dignity_per_varga dignity (L1-is-authority, on prod).
7. **BUG-1 clean:** ga_structural count no longer overlaps ga_sensitive/ga_strength enrichment rows (the
   scope-inflation is gone).
8. **Cockpit green:** `/clients/482012f1/nirmana` Gaṇita panel — all green, updated counts, no stale/red/overfill;
   ga_prashna no longer false-red if the render fix landed (else log it).

---

## STEP 4 — MIGRATION 310 (the deferred floors — REQUIRED, not optional)

From STEP 3's measured values, emit migration 310 (+ seed patch, + ledger):
- `UPDATE asset_registry SET target_floor = <measured ga_structural count> WHERE asset_id='ga_structural';`
- `UPDATE asset_registry SET target_floor = <measured ga_condition count> WHERE asset_id='ga_condition';`
- Any other floor the build revealed as off. (Floors-aspirational: floor = achieved count.)
Apply to prod surgically + ledger-reconcile. Without this, ga_structural ships with a conservative floor and
ga_condition with NULL — two assets floor-incorrect.

---

## STEP 5 — FLIP THE SEAL TO VERIFIED

When §6 is all-checked + migration 310 applied:
- Update `L1_GANITA_CLOSURE_v2_0.md` frontmatter `prod_verify_status → VERIFIED`; bump 2.0 → 2.1.
- Update CURRENT_STATE: L1 Gaṇita prod-sealed.
- Log the standing rail (red-team R2/R3): the ga_structural `%_per_varga`+exclusion-list and ga_condition
  arithmetic-subquery count_sql are FRAGILE — any future asset adding a new `*_per_varga` category re-introduces
  drift. File as a monitoring note for the next enrichment.

**Then L1 is validly, prod-sealed** — and L2 Bodha is designable on a fully-closed L0+L1 + the opportunity
register (L1_SYNERGY_REGISTER L2-classified entries + the ARCH-1/ARCH-2 patterns in §8.2).

Report back: the rebase-green confirmation, the §6 prod-verify PASS table, the migration-310 floor values, and
the merge SHA.
