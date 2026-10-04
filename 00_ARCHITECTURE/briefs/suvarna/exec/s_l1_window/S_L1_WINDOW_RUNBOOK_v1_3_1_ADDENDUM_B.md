# S-L1 window runbook v1.3.1 — ADDENDUM B (W1 package scope, deploy trigger facts, post-window first commit)

Status: addendum only; runbook v1.3.1 (sha256 783536b4ab7289bf06cec65f1766003e0ec4ec2f42d83471d0db55dc0b808131) stays locked. Directed by Strategic Suvarṇa (madhav-06). Complements ADDENDUM A.

## B.1 What the W1 PR (#3122) contains
Branch suvarna/land/TI-s-l1-w1-migrations-001. Diff against main = exactly: the seven SQL files 1221, 1222, 1223, 1224, 1226, 1252, 1254 (byte-identical to the source PR heads), `platform/src/generated/capability_estate_census.json` (check OK, 19eb95ef…), `00_ARCHITECTURE/control/registry_depends_on_migrations.json` (+1 pin line for 1226) and `platform/scripts/governance/__tests__/test_e6_n99_build_completion_integrity.py` (1221 added to DERIVED_ONLY_MIGRATIONS). The last two are the minimal pin edits the governance tests demanded (first CI run was a real red, not rerun, fixed). SS accepted them.

## B.2 Items deliberately NOT in W1
Source PR #2898's `platform/scripts/seed/asset_registry_seed.ts` edit, the asset-registry seed-parity test and the MIGRATION_1226 intent doc stay OUT of W1 (W1 was rehearsed SQL-only).

## B.3 POST-WINDOW, FIRST COMMIT of the tests-only PR (PW.9)
FIRST commit of the tests-only PR: the #2898 seed edit + seed-parity test + intent doc, so main's seed matches the applied migration 1226 soon after SETTLED-1. Then the conditional change-scope guards and the tests of the other source PRs (#2896, #2900, #2943, #2957, #2959).

## B.4 Deploy trigger facts (read from `.github/workflows/deploy.yml` on origin/main, 2026-10-04 02:05Z)
- The routine deploy fires on `workflow_run` of "CI — Ganga Quality Gate" completing on main; job `changes` (and everything after) runs only if that triggering run's conclusion is `success`. DEPLOY_SHA = the triggering run's head_sha.
- A CI run that is CANCELLED (superseded by a later push to main) yields a deploy run whose gate is SKIPPED and whose 'Require earned deployment outcome' ends RED ("change detector did not succeed (result=skipped)"). Harmless: no deploy, no migrate; the later commit's own CI success triggers the real deploy. Seen 2026-10-03 22:43Z (b20bbb520) and 2026-10-04 01:37Z (7a4693408).
- The `migrate` job's `if:` does NOT depend on the changed-path outputs; it runs `scripts/migrate.ts` on the DEPLOY_SHA checkout whenever `changes` and `migration-state` succeeded (state marked/strict, bootstrap skipped). A merge of ONLY platform/migrations/*.sql (+ pins/census) therefore applies those migrations at its deploy.
- WINDOW CONSEQUENCE: W1 applies at the deploy of the W1 merge commit's CI run. Any other push to main while that CI run is in progress cancels it (CI takes ~14 min). The 06:30Z merge FREEZE (all lanes) is what protects this; at W1, before arming: `gh pr list`/merge queue shows no other entry; after the merge, the only main commit after it must be none until the deploy's migrate step finishes.

## B.5 Pre-check at W1 (before arming, with ADDENDUM A.2)
Merge queue (graphql mergeQueue entries) holds only the W1 PR; latest main CI run (workflow "CI — Ganga Quality Gate") is not in progress for a different commit.

## B.6 RECOVERY if the W1 merge commit's CI run is cancelled by a push we do not control (added at SS direction)
Another workstream can still push to main; the freeze binds only the Suvarṇa and Pravāha lanes. If the W1 merge commit's "CI — Ganga Quality Gate" run is CANCELLED (the deploy for it then shows 'Gate & detect changed paths' skipped / 'Require earned deployment outcome' red):
- Do NOT proceed to the next step and do NOT re-trigger anything by hand (no dispatch, no rerun).
- WAIT for the next successful deploy on main (its checkout includes the W1 commit; migrate.ts applies every pending migration).
- THEN verify all seven migrations in `_migrations_applied` by filename + sha256 (read-only, via rq.sh) and the migration-state outputs (ADDENDUM A.1).
- ONLY THEN continue to the image re-verification (on THAT deploy's image) and D6.
- If no deploy follows within 60 minutes: ALERT SS (madhav-06) and Pravāha (madhav-78).
The ledger (`_migrations_applied`), not the deploy label, is the proof either way.
