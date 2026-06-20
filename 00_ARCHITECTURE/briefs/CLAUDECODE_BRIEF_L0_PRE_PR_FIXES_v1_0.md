# L0 Closure — Pre-PR Fixes + Prod-Verify + Seal (paste into Claude Code / Antigravity)

**Context:** The L0 Brahmagyan Closure Pass ran on branch `fix/l0-closure-integrity` (migrations 295–304,
records under `00_ARCHITECTURE/L0_BRAHMAGYAN_CLOSURE_v1_0.md` + `CONDUCTOR/l0-closure/`). The native reviewed
it. Before the PR to main seals L0, do the steps below IN ORDER. Standards apply: surgical migrations only
(NEVER deploy.yml-auto / bulk migrate.ts); seed-consistency (registry change → patch `asset_registry_seed.ts`);
computed-and-cited / canonical-or-floor; only chart `482012f1-710e-4a25-994a-93821f5871aa`; merge-verify.

---

## STEP 1 — PROD-VERIFY GATE (read-only; the seal is not valid until this passes)

The closure record says migrations "APPLIED" but it's a branch — confirm whether they hit PROD or only the
branch DB. Connect to PROD (Cloud SQL proxy, secret `amjis-db-password/3`). Produce a PASS/FAIL table. NO changes.

1. `SELECT version FROM _migrations_applied WHERE version BETWEEN 295 AND 304 ORDER BY version` (or the actual
   migration-ledger table) — expect 295–304; list missing.
2. `\dt bg_graha_dik` + `SELECT count(*) FROM bg_graha_dik` (expect 9); `\dt bg_transit_vedha` +
   `SELECT count(*) FROM bg_transit_vedha` (expect 33).
3. `SELECT count(*) FROM bg_prashna_tajik_yogas` (expect 16); `SELECT count(*) FROM bg_transit_rules` (expect 50).
4. Execute each of the 4 previously-broken count_sqls AS STORED in prod `asset_registry` (bg_prashna_rules,
   bg_vastu_directions, bg_transit_engine, bg_transit_rules) — each must return a number, not a syntax error.
5. `SELECT asset_id, catalog_status, target_floor FROM asset_registry WHERE layer='brahmagyan' ORDER BY 1` —
   all 22 CURRENT; note any stale floor (expect bg_prashna_rules=36→needs 41, bg_transit_rules=41→needs 50;
   STEP 2 fixes these).
6. bg_dignity_reference present in prod `asset_registry`; its count_sql returns 151.
7. FORENSIC: `reference_nakshatra` nakshatra_id=25 → Purva Bhadrapada, vimshottari_lord=jupiter (native Moon).

**If any migration 295–304 is NOT on prod:** the closure was branch-only. Apply 295–304 to prod surgically
(in order, recorded in the migration ledger) BEFORE proceeding — that IS the real seal action. Re-run checks.

---

## STEP 2 — TWO PRE-PR FIXES (migration 305 + seed patch)

These two are trivial but the seal must not ship with them open.

**Fix A — stale target_floors (closes DEFER-006/007).** Phase B itself made these stale. In migration 305:
```sql
UPDATE asset_registry SET target_floor = 41 WHERE asset_id = 'bg_prashna_rules';  -- 36→41 (tajik_yogas 11→16)
UPDATE asset_registry SET target_floor = 50 WHERE asset_id = 'bg_transit_rules';   -- 41→50 (Venus rows)
```
Patch the same two floors in `asset_registry_seed.ts`. Verify count == floor for both post-update.

**Fix B — REC-004 body_part conflict (correctness — L2 will consume it).** `bg_nakshatra_medical` and
`reference_nakshatra.body_part` disagree on nakshatra→body_part (e.g. Ashwini: bg_nakshatra_medical "feet/knees"
vs reference_nakshatra "head"). The classically authoritative assignment is the **Kalapurusha / Kalanara
body-part scheme** (Ashwini = feet/knees, Bharani = head, … — the standard nakshatra-Kalapurusha mapping per
BPHS / Ashtanga Hridayam). Determine which table matches the Kalapurusha scheme, then in migration 305:
- Pick the authoritative source (likely `bg_nakshatra_medical` for the medical body-part, but VERIFY each
  nakshatra against the Kalapurusha citation — do NOT assume; check the rows).
- Correct the non-authoritative table's values to match, OR (cleaner) point both at one authority and deprecate
  the divergent column with a COMMENT. Whichever, the two tables must AGREE per nakshatra after this.
- Every corrected value carries its classical_citation (computed-and-cited gate). If a specific nakshatra's
  body-part isn't classically assignable (e.g. Abhijit), FLOOR it NULL+reason — never fabricate.
Re-verify: `bg_nakshatra_medical.body_part` and `reference_nakshatra.body_part` are consistent for all 27
nakshatras (Abhijit/28th floored if applicable).

Apply migration 305 to PROD surgically (recorded in the ledger). Seed patched. CI green.

---

## STEP 3 — REC DISPOSITIONS (native-decided; log, mostly don't build)

Record these dispositions in the closure record §6 (update it) — do NOT build REC-002:
- **REC-001 (3 graha/direction tables):** ACCEPT as a **governance note**, not a unified view. Add a short note
  to the closure record / a governance doc: "use bg_graha_dik for Dig Bala strength; bg_vastu_directions for
  Vastu/remedial; reference_nakshatra.disha for nakshatra direction." No view, no migration.
- **REC-002 (transit rules+vedha VIEW):** **DEFER to L1** — build the join in the consuming ga_transit writer,
  not as standing L0 infra (no pre-building later phases). Do NOT create migration 305-view. Log in the L1
  opportunity register.
- **REC-003 (empty associated_remedies[] on 50 doshas):** **LOG as a required pre-L2-Bodha DATA task** (it's
  already L2-OPP-003). Not an L0 blocker. Ensure it's in the L1/L2 opportunity register.

---

## STEP 4 — UPDATE SEAL RECORD + DEFER TRACKING

- Update `L0_BRAHMAGYAN_CLOSURE_v1_0.md`: add migration 305; mark DEFER-006/007 RESOLVED; mark REC-004
  RESOLVED; record the REC-001/002/003 dispositions in §6; confirm the prod-verify PASS table (STEP 1) is
  referenced as the seal basis (so "sealed" now means prod-sealed).
- DEFER-001/002 (no writers for bg_transit_engine, bg_nakshatra_medical) and DEFER-003/004 (table DROPs need
  refactor) and DEFER-005 (bg_nakshatra hash tracking broken) REMAIN as disclosed deferrals — none block seal.
  File DEFER-005 as a tracked follow-up issue (latent silent-staleness risk) so it isn't lost.
- Update CURRENT_STATE: L0 sealed (prod-verified), branch fix/l0-closure-integrity ready to merge.

---

## STEP 5 — PR + MERGE-VERIFY

Open the PR `fix/l0-closure-integrity` → `main` for the native single end-review. PR body = the closure summary
(phases A/B/C + prod-verify PASS table + the 2 pre-PR fixes + rec dispositions + remaining disclosed defers).
After merge: `gh pr view <N> --json mergeCommit,state` to confirm; re-confirm migrations 295–305 are on prod;
confirm the cockpit `/clients/482012f1/nirmana` Brahma Jñāna panel is all-green (no red/stale/overfill).

**Then L0 is validly sealed — prod-verified, for the first time.** Report back with the prod-verify PASS table
and the merge SHA. Next workstream = the L1 closure pass (same template; folds in
`L1_ENRICHMENT_AMENDMENTS_v2_0.md`).
