# Domain E — Release and Delivery

## What was checked (with exact reproducing command/query for each)

1. Deploy-gate path patterns — read the full `changes` job in
   `Read /Users/Dev/madhav-l3/audit/.github/workflows/deploy.yml` (lines 172–363), specifically the
   "Detect changed paths" step (lines 269–362).
2. Deployment-outcome earned signal — reproduced via:
   `grep -rn "deployment-outcome\|deployment_outcome\|Require earned deployment" --include="*.yml" --include="*.ts" --include="*.md" .`
   then read `platform/scripts/ci/deployment_outcome_gate.ts` in full (163 lines) and the
   `deployment-outcome` job in `deploy.yml` (lines 2010–2043).
3. Pipeline-image rebuild triggers — read the `PIPELINE_PATTERN` regex directly:
   `grep -n "PIPELINE_PATTERN=" .github/workflows/deploy.yml`
4. Migration ranges — reproduced via:
   `ls platform/migrations/*.sql | xargs -n1 basename | grep -E '^[0-9]' | sort -V | tail -15`
   `ls platform/migrations/ | grep -E '^(10[7-9][0-9]|11[01][0-9])_'` (empty)
   `ls platform/supabase/migrations/*.sql | xargs -n1 basename | sort -V | tail -5`
   `ls platform/supabase/migrations/ | grep -E '^(10[7-9][0-9]|11[01][0-9])_'` (empty)
   Cross-checked campaign docs: `grep -n "1070\|1071\|1033" 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/**`
5. Merge queue — reproduced via:
   `gh api repos/Marsys-Technologies/Madhav/branches/main/protection` (404 — classic API)
   `gh api repos/Marsys-Technologies/Madhav/rulesets` then
   `gh api repos/Marsys-Technologies/Madhav/rulesets/20141220` (full ruleset detail).
6. Generated-artifact regeneration protocol — reproduced via:
   `grep -rl "never hand-edit\|must be regenerated" --include="*.md" --include="*.ts" --include="*.py" .`
   `find platform/src/generated -iname "*capability*"`
   `head -20 platform/scripts/generate_capability_estate_census.ts platform/scripts/generate_capability_knowledge.ts`
   `git log --oneline -8 -- platform/src/generated/`

## Findings

### 1. Deploy-gate path patterns (`.github/workflows/deploy.yml`, the `changes` job)

Four independent path regexes, each compared against `git diff <deployed-sha> HEAD` where
`<deployed-sha>` is read **live from production itself** (Cloud Run revision label `commit-sha`
for web/sidecar/mcp; the `:<sha>` image tag on the `brahma-build-pipeline-job` for pipeline) — not
from any GitHub API "last successful run" record. This is explicitly documented in-file (lines
269–297) as the fix for a previously-confirmed defect (#2169/#2172): a self-diff against the
run's own SHA silently skipped every component rebuild for ~3.5h across 17 green deploy runs.

- `WEB_PATTERN`: `^(platform/|00_ARCHITECTURE/CAPABILITY_MANIFEST\.json$|00_ARCHITECTURE/manifest_overrides\.yaml$|00_ARCHITECTURE/PLANNER_PROMPT_v.*\.md$|01_FACTS_LAYER/|025_HOLISTIC_SYNTHESIS/|035_DISCOVERY_LAYER/)`
- `SIDECAR_PATTERN`: `^platform/python-sidecar/`
- `MCP_PATTERN`: `^platform-mcp/`
- `PIPELINE_PATTERN`: `^(platform/python-sidecar/Dockerfile\.pipeline|platform/python-sidecar/ga_writers/|platform/python-sidecar/pipeline/|platform/python-sidecar/services/|platform/python-sidecar/brahmagyan/|platform/python-sidecar/pyjhora_adapter/|platform/python-sidecar/bodha_writers/|platform/python-sidecar/panchang_engine/|platform/python-sidecar/muhurat/|platform/python-sidecar/requirements|035_DISCOVERY_LAYER/)`

The gate is **fail-open**: any failure to resolve the deployed sha, or to fetch it, forces
`echo true` (deploy that component) rather than silently skipping (lines 328–338).

**L3-relevant implication**: `ga_writers/` is inside `PIPELINE_PATTERN`. Any L3 `ka_*` writer file
edit under `platform/python-sidecar/ga_writers/` (or `services/`, `pipeline/`) will trigger a
pipeline-image rebuild automatically — no `force_all_services` needed. A change confined to, say,
`00_ARCHITECTURE/briefs/...` docs (this audit's own scope) will NOT trigger any rebuild — none of
the four patterns match `00_ARCHITECTURE/briefs/`.

### 2. The `deployment-outcome` earned signal — real detector, not a proxy

Job `deployment-outcome` ("Require earned deployment outcome", deploy.yml lines 2010–2043) runs
`always()` after `[changes, migrate, deploy-web, deploy-sidecar, deploy-mcp, deploy-pipeline-job]`
and calls `platform/scripts/ci/deployment_outcome_gate.ts`.

Applying the §N.8 test — "what code path would have to run and fail for the signal to correctly
read false?": `evaluateDeploymentOutcome()` builds a `required` map from the **same** `changed.*`
booleans the `changes` job emitted (which are themselves grounded in production's own deployed
revision, not documentation or a marker file), then checks that every job implied by that map
actually has `result === 'success'`. If a required job is `skipped`/`failure`/`cancelled`/missing,
the gate emits `blocked-mutation-skipped` and exits 1 — turning what GitHub Actions would otherwise
report as a passing (mostly-skipped) workflow into a hard failure. This is a real, tested detector:
`platform/scripts/__tests__/deployment_outcome_gate.test.ts` unit-tests the pure function, and a
second test asserts the actual `deployment-outcome` job step literally invokes
`ci/deployment_outcome_gate.ts`. Campaign docs (`MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`
lines 89, 468) record it catching real failures live (4 correctly-failing runs cited: 35435197677,
35435726103, 35437874634, 35438308690). Landed via commit `d4655c9f3` "fix(deploy): require earned
production outcome (#2682)" (confirmed in `git log --oneline`).

Verdict on this specific item: passes §N.8 — the claim ("every source-implied mutation actually
succeeded") is exactly what the code checks, sourced from real job results and a real production
diff, not a hardcoded/proxy value.

### 3. Pipeline-image rebuild without `force_all_services=true`

Yes — confirmed by the `PIPELINE_PATTERN` above. Any push whose diff (against the SHA currently
deployed on `brahma-build-pipeline-job`) touches `platform/python-sidecar/Dockerfile.pipeline`,
`ga_writers/`, `pipeline/`, `services/`, `brahmagyan/`, `pyjhora_adapter/`, `bodha_writers/`,
`panchang_engine/`, `muhurat/`, `requirements*`, or `035_DISCOVERY_LAYER/` triggers a pipeline
rebuild automatically. `force_all_services` (workflow_dispatch input, default `false`) is only
needed to force a rebuild when none of these paths changed.

### 4. Migration ranges

**Correction to the task's stated premise**: the "already-applied range" is **not** 1033–1070 as a
contiguous block. Two migration directories exist and this matters:

- `platform/migrations/` — the directory that actually contains a 1070-numbered file:
  `1070_data_plane_builder_orchestrator_grants.sql` is present and applied (confirmed live and
  independently in `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/_work/F6.md` §5, which cites
  the deploy log line `Applied: 1070_data_plane_builder_orchestrator_grants.sql`). Numbering in
  this directory runs 1000→1042 contiguously, then jumps to 1070 — **1043–1069 do not exist as
  files in this checkout** (that range is documented elsewhere, `STATE.md` line 105, as reserved
  for Pūrṇa: "Pūrṇa 1042–1069; shared ≥1120"). No file in `1071`–`1119` exists yet
  (`ls platform/migrations/ | grep -E '^(10[7-9][0-9]|11[01][0-9])_'` → empty).
- `platform/supabase/migrations/` — a separate, apparently older/parallel migrations tree, highest
  file present is `1041_data_plane_public_schema_migration_grant.sql`. Also empty for 1071–1119.

The governing campaign artifacts (`AUDIT_CHARTER.md` line 89: "Migration range if one is genuinely
needed: 1071–1119. 1033–1070 are applied — never edit."; `STATE.md` line 105: "L3 migration range
1070–1119 (Pūrṇa 1042–1069; shared ≥1120), DP-SD-021, ratified §13") are self-consistent with what
is on disk: nothing above 1070 is applied in the L3-relevant `platform/migrations/` directory, and
1071–1119 is genuinely open. I did not find a second, competing claim to any number in that range.

**Not independently verified**: whether 1043–1069 are truly fully applied in production (only
1070 has independent live confirmation via F6.md); this audit did not query the DB migration
ledger table directly to confirm. If needed, that would require:
`source /Users/Dev/madhav-l3/dbenv.sh && psql -Atq -c "SELECT filename FROM schema_migrations ORDER BY filename DESC LIMIT 40"` (table name assumed, not verified — I did not run this, staying in-budget and because the file-presence + F6.md live-log evidence was already sufficient for the open-range question this audit item asks).

### 5. Merge queue

`gh api repos/.../branches/main/protection` returns 404 "Branch not protected" — this is the
**classic** branch-protection API, which GitHub returns 404 for when the repo has moved to the
newer **rulesets** system (as this repo has). Checking the modern surface:
`gh api repos/Marsys-Technologies/Madhav/rulesets` returns one active ruleset,
id `20141220`, name **"main protection (org migration, merge queue)"**, `enforcement: "active"`,
targeting `refs/heads/main`. Its full rule set
(`gh api repos/Marsys-Technologies/Madhav/rulesets/20141220`) includes:
- `required_status_checks`: TypeScript (src only), Unit Tests, Secret Scan (unit 0b.2), Governance
  Gates (drift/schema/edge/native-literal/py-sidecar), TAP-6 — Method audit grep set.
- `pull_request`: required_approving_review_count 0, allowed_merge_methods [merge, squash, rebase].
- **`merge_queue`**: merge_method SQUASH, max_entries_to_build 5, min/max_entries_to_merge 1,
  grouping_strategy ALLGREEN, check_response_timeout_minutes 60.
- `non_fast_forward`, `deletion` protections.
- `bypass_actors: []`, `current_user_can_bypass: "never"`.

This is genuinely in effect, not just documented: it is an `active`-enforcement ruleset object
returned by the live API, not a markdown description. (I did not separately try to push a
non-fast-forward commit to prove enforcement empirically — that would be a destructive test out of
scope for a read-only audit; the ruleset's `enforcement: "active"` + `current_user_can_bypass:
"never"` is the strongest read-only evidence available.)

### 6. Generated-artifact regeneration protocol

Two load-bearing generated, never-hand-edit artifacts found:

- `platform/src/generated/capability_estate_census.json` — generator
  `platform/scripts/generate_capability_estate_census.ts` (`npm run
  codegen:capability-estate-census` / `:check`). Header explicitly frames it as "a mechanically
  reproducible census... deliberately an accounting artifact, not a semantic-capability catalog."
  Test: `platform/scripts/__tests__/generate_capability_estate_census.test.ts`.
- `platform/src/generated/capability_knowledge.snapshot.json` — generator
  `platform/scripts/generate_capability_knowledge.ts`, a "reproducible compiler for the
  planner-facing capability knowledge snapshot," which throws on integrity-report failure
  (`inspectCapabilityKnowledge`). Provenance logic in
  `platform/scripts/lib/capability_knowledge_provenance.ts`, tested by
  `platform/scripts/__tests__/capability_knowledge_provenance.test.ts`.

Recent PRs that touched these generated files (`git log --oneline -8 -- platform/src/generated/`):
`#2700` (fix(data-plane): restore orchestrator grants for data_plane_builder), `#2698`
(fix(purna): align judgment contract provenance), `#2697` (feat(purna): harden wealth inquiry
acceptance evidence), `#2696` (feat(purna): fence wealth evidence provenance), `#2694` (feat(purna):
earn query-domain-reading availability), `#2681` (feat(purna): expand source availability
contracts), `#2678` (feat(purna): bind direct L1 source contracts). All are Pūrṇa-campaign PRs
regenerating capability registry state as they add/modify capability descriptors — consistent with
the "regenerate, don't hand-edit" doctrine actually being followed in practice, not just stated.
I did not find an L3-specific (`ka_*`) commit touching these generated files yet in this log
window, meaning any L3 writer that changes catalog/capability descriptors will need the same
regeneration step (`npm run codegen:capability-estate-census` and the capability-knowledge compiler)
before merge — this is a real, CI-checkable obligation (`:check` variants exist for both), not
guidance a session could silently skip.

## Verdict: READY

Domain E's release-and-delivery surface is genuinely sound for the L3 campaign to build against:
the deploy-gate path detection is grounded in production's own deployed state (not a stale marker),
the pipeline image rebuilds automatically on any `ga_writers/`-path change (the exact path L3
writers live under), the `deployment-outcome` gate is a real tested detector rather than a
proxy-status green light, migration range 1071–1119 is genuinely unclaimed, and the merge queue is
actively enforced (not merely documented) via GitHub's ruleset API.

## Evidence that could have made this verdict fail (per CLAUDE.md §N.8 — every verdict must name what would have flipped it)

- If `PIPELINE_PATTERN` did **not** include `ga_writers/` (or excluded it), L3 writer changes would
  silently never rebuild the pipeline image without `force_all_services=true` — this would have
  been a live release-readiness blocker. It does include it; verified by direct regex read.
- If `deployment_outcome_gate.ts`'s `required` map were built from a hardcoded/static list instead
  of the live `changed.*` inputs (or if its unit test didn't assert the job wires the real script),
  it would be exactly the §N.8 "signal with no real detector" defect class — this was the specific
  thing checked and it passed (the required-jobs map is built dynamically per-input, and a test
  asserts the job step literally calls the script).
- If `ls platform/migrations/ | grep -E '^(10[7-9][0-9]|11[01][0-9])_'` had returned any file, the
  1071–1119 range would already be partially claimed and the campaign's assumption would be stale
  — it returned empty in both migration directories checked.
- If `gh api .../rulesets` had returned an empty array or an ruleset with `enforcement: "disabled"`
  / `"evaluate"` instead of `"active"`, the merge queue would be documented-only, not real — it
  returned `enforcement: "active"` with `current_user_can_bypass: "never"`.
- If the classic `branches/main/protection` 404 had been taken at face value without checking
  `rulesets`, this audit would have wrongly concluded "no protection exists" — that would have been
  a false NOT-READY finding driven by using the wrong (legacy) API surface.
- Un-verified gap: I did not query the DB's own migration-ledger table to independently confirm
  1043–1069 are actually applied in production (only 1070 has direct live-log confirmation via
  F6.md). If a live query showed one of those numbers still pending, the "1033–1070 already
  applied" framing in the campaign docs would need correction — this is flagged above as
  COULD NOT FULLY VERIFY rather than asserted.
