---
artifact: CI_EFFICIENCY_AUDIT_v1_0.md
version: 1.0
status: CURRENT
produced_on: 2026-07-31
produced_during: CI efficiency audit (native-commissioned)
authoritative_side: claude
role: >
  Evidence record for the 2026-07-31 audit of the GitHub Actions estate: what each
  workflow costs, which gates were load-bearing, which were unreachable or
  permanently red, and what was changed. Written so the reasoning survives the PR.
implements: >
  Native directive (2026-07-31): "review and correct the continuous integration
  process ... any legacy which are not adding value to be ripped off ... carefully
  so that we don't do a mistake of removing something important and relevant."
supersedes: >
  LEGACY_GOVERNANCE_TEARDOWN_AUDIT_v1_0.md §5's row "brahma-conductor.yml —
  operational but in terminal state (all layers built); KEEP as infra." That row is
  superseded on evidence (§4.3 below) by native decision, 2026-07-31.
changelog:
  - v1.0 (2026-07-31): initial. Landed with PR #963.
---

# CI Efficiency Audit v1.0

## §1 — The headline correction

The audit was commissioned on the premise that "the Ganga gate ... and all other
things that are there in CI are all part of the legacy." The evidence inverts this.

**Ganga is not legacy. It holds the only four checks that protect `main`.**
Branch protection on `main` requires exactly:

| Required check | Time (2026-07-30 baseline) |
|---|---|
| Governance Gates (drift / schema / edge / native-literal / py-sidecar) | 452s |
| Unit Tests | 418s |
| TypeScript (src only) | 73s |
| Secret Scan (unit 0b.2) | 7s |

Every other check in the estate — TAP CI, Elevation gates, Ṣaḍ-Darśana skeletons,
chat-v2 CI, Paripraśna, Density Census, Coverage Gate, Naming Lint, Planner
Regression, ICR PR Gate, the platform-mcp typecheck, the deploy PR build — is
**advisory**. It consumes runner minutes and contributes to the felt wait, but no
outcome of it can block a merge.

The legacy was real, but it lived in the workflows *around* Ganga, not in Ganga.

## §2 — Baseline cost

Per PR, when all triggers fire: **~2,200–3,500 runner-seconds (37–58 min)** across
5–7 workflows, for a **~9.5 min wall clock**.

| Workflow | Jobs | Runner-sec | Wall |
|---|---|---|---|
| ci.yml (Ganga) | 12 | 1257 | 561s |
| chat-v2-ci.yml | 6 | 854 | 521s |
| pariprashna-ci.yml | 5 | 442 | 317s |
| deploy.yml (PR build-check) | 1 | 346 | 356s |
| shad-darshana-ci-skeletons.yml | 6 | 256 | 92s |
| elev-serving-gates.yml | 5 | 233 | 82s |
| tap-ci.yml | 4 | 107 | 65s |

## §3 — Where the time actually went

Two jobs, two causes, neither related to what the jobs assert.

**3.1 Unit Tests — 366s of `npm test`.** `vitest.config.ts` set
`environment: 'jsdom'` globally. The 2026-07-30 main run reports
`tests 61.10s` against `environment 702.66s`: jsdom construction, not assertions,
was essentially the whole job. 710 test files; ~140 touch a DOM.

Measured A/B on `tests/planner` (4 files):

```
jsdom   Duration 496ms (environment 1.31s)
node    Duration 137ms (environment 0ms)
```

**3.2 Governance Gates — 145s pip install + 285s serial pytest.** The install was
uncached and pulled the full runtime requirement set, including
`sentence-transformers` (→ torch), `ragas`, `google-cloud-aiplatform`, `openai`,
`anthropic` and `tiktoken`. An import census over `platform/python-sidecar/**/*.py`
found none of them imported anywhere.

## §4 — Findings: what was actually dead

Each verified against the live repo, not inferred from reading YAML.

**4.1 No workflow had a `concurrency:` group.** All 15. Every push to a PR branch
stacked a full new run set while superseded runs kept burning. Under this repo's
merge-train load this is likely the largest single contributor to felt slowness.

**4.2 chat-v2-ci: 6 of 13 stages unreachable.** Stages 4/10/11/12/14 gated on PR
labels `beta`, `pre-merge`, `mobile-active` — `gh label list` shows **none of those
labels exists**, and none was ever applied. Stage 15 was `if: ${{ false }}`.
Stage 13 (Stryker) fired only on the weekly cron, where it echoed a no-op because
`stryker.conf.json` was never created and stryker is not in `package.json`.

**4.3 brahma-conductor.yml was broken, not dormant.** L0 is SEALED and
`build_state.yaml` reads `complete: 42` of 45, but the workflow's SMOKE step asserts
every L0 Wave-1 asset is still `pending` and `total_sessions == 45` with zero green —
an assertion that can never hold again. Its last three runs all failed (2026-06-18).
`LEGACY_GOVERNANCE_TEARDOWN_AUDIT_v1_0.md §5` had recorded it as "operational but in
terminal state — KEEP as infra"; the "operational" half is not true. Deleted by
native decision 2026-07-31 after the conflict was surfaced. The Smṛti record under
`00_ARCHITECTURE/CONDUCTOR/` is retained.

**4.4 chat-v2-smoke.yml was permanently red from a config bug.** It invoked
`round6-walkthrough.spec.ts` **without** `--config=tests/e2e/chat-v2/playwright.config.ts`,
so it loaded the repo-default Playwright config. It failed *every* run since at
least 2026-07-21 across four unrelated branches. `chat-v2-ci` Stage 3 runs the same
spec with the correct config, green. Its `merge_group` trigger was also dead — no
merge queue is configured (`mergeQueue: null`). Deleted; its three uncovered path
globs folded into chat-v2-ci.

**4.5 Secret-gated gates ran to a fabricated green.** `gh secret list` shows no
`TAP_DATABASE_URL`, `TAP_MCP_SERVER_URL`, `TAP_MCP_SMOKE_BEARER_TOKEN`,
`TAP7_API_BASE_URL`, `MARSYS_MCP_KEY`, `MARSYS_MCP_URL` or `DATABASE_URL`. So TAP-5,
TAP-7, S-13 and the MCP smoke battery started a runner on every push and PR, exited 3
(SKIPPED-WITH-REASON), and were swallowed by `continue-on-error` — a green check
asserting nothing. `samiksha-daily` did the same on a daily cron, after paying for
`npm ci` first. (Note: the repo has `PROD_DATABASE_URL` but not `DATABASE_URL`, which
`samiksha-daily` reads — **open question, flagged in the workflow log.**)

**4.6 One-`npm ci`-per-script job sprawl.** `elev-serving-gates` ran 5 jobs, each
paying ~30s for `npm ci` to execute a ~1-second script: 233 runner-seconds for about
five seconds of gate work. `shad-darshana-ci-skeletons` had the same shape (256s).

**4.7 604 runner-seconds per PR that no test outcome could turn red — and worse,
two of the three were actively BROKEN.** chat-v2 Stage 5 (visual, 101s) ended in
`|| echo`; Stages 6 (a11y, 190s) and 7 (perf, 313s) were `continue-on-error: true`
pending flips ("until γ8", "until γ") that never happened. Stage 5 was additionally
a *duplicate*: `--grep "@visual"` matches exactly one test repo-wide, and it lives
inside `a11y/axe.spec.ts`, which Stage 6 runs in full.

Stages 6 and 7 have **never passed in CI**. Both fail with
`Error: Timed out waiting 120000ms from config.webServer.` — the Playwright dev
server never boots, so neither axe-core nor the perf specs execute at all. The
baseline run 30536476881 shows 1 such timeout in Stage 6 and 4 in Stage 7. Stage 3
boots the same webServer successfully in the same workflow, so this is specific to
these jobs.

> **⚠️ Methodological trap, recorded because this audit fell into it.** The GitHub
> API reports `steps[].conclusion == "success"` for a `continue-on-error` step **even
> when the command exited 1**. Querying step conclusions therefore showed Stage 6 and
> Stage 7 as fully green, and the first pass of this audit concluded "both pass today,
> so harden them." That was wrong, and the hardening was caught only when Stage 6 went
> red on the audit's own PR. **Only the job LOG shows `Process completed with exit
> code 1`.** Never infer a soft gate's true state from the conclusion field.

## §4.8 — ṢAḌ-DARŚANA W0.6 PLAN-mode gates: green, and measuring nothing

The three PLAN-mode gates (`specificity_gate_v0`, `tri_plane_no_dead_end_gate`,
`mode3_single_route_gate`) print, in their own report line, *"exit 0 always"*. With no
`MCP_SERVER_URL` secret configured (there is none), they cannot fail — confirmed by run
history: `shad-darshana-ci-skeletons.yml` has **0 failures in 100 runs**, as do
`elev-serving-gates.yml` and `tap-ci.yml`. That is 300 runs across three always-on
workflows without a single red.

Their one substantive output is a static registration census, and **that census is wrong
for half its subjects.** The gates report `registered=false` for `kala_now_get`,
`kala_ahead_get`, `kala_priority_get` and `kala_explain_get`, with the diagnostic
"sibling facade lane likely not merged yet." The lanes *have* merged: all eight tools are
implemented (`now.ts` alone is ~1,560 lines) and all eight `register*` functions are
called from `platform-mcp/src/tools/registry_bridge.ts`.

The detector (`_kala_tool_registration.ts`) greps for a string literal adjacent to
`server.tool(` / `regAlias(`. Four files register via `server.tool(TOOL_NAME, …)` with
`const TOOL_NAME = 'kala_now_get'`, and the grep cannot see through that indirection. The
correlation is exact: the four files that declare a `TOOL_NAME` constant are precisely the
four reported unregistered; the four that inline the literal are precisely the four
reported registered.

So the honest status is: **this is a §N.8 earned-signal violation.** The gate cannot fail,
and its only assertion is a false negative on half the surface it claims to census — while
its message actively misdirects a reader toward "the lane hasn't landed." Either fix the
detector to resolve constant indirection and arm the gates, or retire them. They should
not stay as they are.

## §5 — What changed (PR #963)

| Tier | Change | Result (measured on CI) |
|---|---|---|
| 1 | vitest `node`+`jsdom` projects | Unit Tests **418s → 195s** |
| 1 | `requirements-ci.txt` + pip cache (xdist tried and reverted, §6.1) | pip install **145s → ~17s** (deterministic). Governance Gates job total is NOT reliably improved: pytest wall on this runner varies 285s–422s independent of any change (§6.1), which swamps the install saving |
| 1 | `concurrency:` groups on all workflows | superseded PR runs cancel instead of stacking |
| 2 | Removed 7 unreachable chat-v2 stages, `chat-v2-smoke.yml`, `brahma-conductor.yml`; `if:`-guarded the secret-gated TAP gates | −215 lines; honest SKIPPED instead of fabricated green |
| 3 | Collapsed elev-serving-gates 5→1 and shad-darshana 5→1 jobs | ~400 runner-sec/PR |
| 4 | Stage 5 deleted (duplicate); Stages 6 and 7 off the PR path to a HARD nightly | 604 runner-sec/PR removed; two broken harnesses surfaced instead of hidden |

**Net on the required path:** Unit Tests is a solid, repeatable **418s → ~200s**.
Governance Gates is bounded by the sidecar pytest run, which this audit did NOT speed
up — the 145s install saving is real, but pytest's own 285s–422s run-to-run variance
is larger than it. So the honest claim is: **one of the two required long poles was
halved; the other was diagnosed, its fixed overhead removed, and its remaining cost
shown to be test-suite runtime plus runner noise rather than anything CI config can
address.** Speeding it further means making the sidecar suite itself faster.

Separately, ~1,000 runner-sec/PR was removed from the advisory workflows, and
`concurrency:` groups stop superseded runs from stacking — which under this repo's
rebase/force-push load is likely the largest practical improvement of the lot.

## §6 — Corrections this audit had to make to itself

Both were caught by running the changes through CI rather than reasoning about them,
which is the argument for doing that.

**6.1 pytest-xdist was reverted as UNPROVEN — and the first version of this section
overstated that, twice.** The sequence is worth recording because it is a clean
example of drawing conclusions from single samples.

`-n 4 --dist loadfile` measured **2.9× faster locally** (226s → 78s) and was landed
on that basis. The next CI run came in at 323.49s against a 285.77s baseline, and
this section originally read "xdist is SLOWER on CI — 4 vCPU, worker import cost
exceeds the parallel gain." Then the revert run — identical serial command, identical
`4647 passed / 12 skipped / 83 deselected / 7 subtests` — came in at **422.22s**.

| run | configuration | pytest wall |
|---|---|---|
| 30587431953 | serial, full requirements | 285.77s |
| 30594499554 | xdist `-n 4`, slim requirements | 323.49s |
| 30595102066 | serial, slim requirements | **422.22s** |

**Serial alone spans 285s–422s, and the xdist sample sits inside that range.** The
runner's variance is larger than the effect, so n=1 per arm supports no conclusion in
either direction. The honest statement is that xdist is unproven here, not that it is
slower. It stays reverted because unproven complexity is not worth carrying — and
settling it properly needs several samples per arm compared on medians.

**What IS solid in this job is the install**, which is deterministic:
`requirements.txt` → `requirements-ci.txt` took it from 145s to ~17s. That saving is
real and repeatable; the pytest run itself is simply noisy on this hardware.

**Lesson: a local parallelism measurement does not transfer to a 4-vCPU runner —
but neither does a single CI measurement settle anything on a noisy one.**

**6.2 Stages 6 and 7 were hardened on a misread, then corrected.** See the trap box
in §4.7 — the API's `conclusion` field reports `success` for `continue-on-error`
steps that exited 1. The first pass read that field, concluded both stages passed,
and removed their suppression. Stage 6 immediately went red on the audit's own PR,
which is how the error surfaced. Corrected: both are genuinely broken (webServer
never boots), so they are now HARD but nightly-only, with the breakage documented
in-place rather than re-suppressed.

**6.3 A second-pass re-verification (2026-07-31) revisited every structural claim.**
Recorded here so the pattern is visible: each error below came from a plausible
inference that nobody had executed. Note that the FIRST item is a correction to a
correction — the second pass initially over-corrected, and only a direct experiment
settled it. When a claim is cheap to test, test it rather than reason about it twice.

- **"The `push: [main, feature/**]` triggers double every PR run" — HALF-REFUTED, then
  CONFIRMED by experiment. My first answer was wrong and is corrected here.**
  The static evidence said: `feature/**` and `r6/**` branches exist on origin (21 of
  them) but **none has run CI in the last 200 runs**; all active work uses `samapti/`,
  `chore/`, `shad-darshana/`. I recorded that as "refuted." That conclusion confused
  *"does not fire today"* with *"the mechanism does not exist."*
  A direct experiment settled it: a scratch branch `feature/ci-concurrency-probe` with an
  open PR was pushed to, and **commit `d8e82d5` produced BOTH a `push` run and a
  `pull_request` run of all four always-on workflows — 8 runs for one commit.** The
  duplication is real; it is merely dormant because nobody currently names a branch
  `feature/*`. It is a live trap for whoever next does. Removed in PR #964.
  The experiment also established that **concurrency groups cannot dedupe across event
  types**: `github.ref` is `refs/heads/<branch>` for push but `refs/pull/<n>/merge` for
  pull_request, so the two runs land in different groups.
  (One apparent counter-example seen earlier — a `push` run of `ci.yml` on
  `shad-darshana/integration` — resolved separately: that branch carries its own edited
  copy of `ci.yml` adding itself to the trigger list; GitHub uses the workflow file from
  the pushed branch, not main's.)
- **"`services/ka_*/**` in the circularity guard is a dead/mis-written glob" — REFUTED.**
  10 `ka_*` service directories (50 files) and 17 `ka_*.py` writers exist, and GitHub
  Actions path globs support `*` inside a path segment. The filter is correct and live.
- **Two shell errors that produced confident-looking wrong output.** (a) A `for` loop
  matching required-check names printed `MISSING` for all four checks that were in fact
  present and passing — a quoting artifact. (b) A lane-recency loop reported chat-v2 and
  Paripraśna as having **NEVER** been touched, because **zsh does not word-split unquoted
  variables** the way bash does, so multi-path lanes passed one bogus argument and matched
  nothing. Both were caught only by re-running the query directly. Prefer an explicit
  `bash` script over a zsh one-liner when passing path lists to `git log`.
- **A near-miss on the ṢAḌ-DARŚANA registration finding.** The gate reports 4 of 8
  `kala_*` tools as unregistered, and the obvious reading — "four implemented-but-unwired
  views, a real defect" — was wrong. All eight are registered and called from
  `registry_bridge.ts`; see §4.8.

**6.4 Third pass (2026-07-31, parked-decision close-out) — three things worth recording,
two of which contradict the instructions they were executing.**

- **A delegated plan asked for a verification that is impossible in the stated order.**
  Step 1a required confirming the four required checks report on a `merge_group` event
  *before* enabling the merge queue. `merge_group` events are generated **only** by an
  enabled queue, so the trigger cannot be exercised first. Recorded rather than quietly
  reordered. The achievable sequence — merge the trigger, enable the queue, watch ONE PR,
  disable on failure — is what PR #967 documents. Rollback is a UI toggle.

- **An "open question" was already answered in an unmerged PR.** Step 3 commissioned an
  investigation into `samiksha-daily` reading a nonexistent `DATABASE_URL`. The
  investigation confirms the defect (no repo secret, **no environments configured at
  all**, no matching variable; three scheduled runs "succeeded" doing nothing). But
  **PR #895, open since 2026-07-29, already fixes it** — repointing to
  `secrets.PROD_DATABASE_URL` (the same secret `deploy.yml`'s migration step reads) and
  replacing the silent `exit 0` with `exit 1` + a `::error::` annotation, under the same
  §N.8 reasoning, filed as SAMĀPTI A5/G2. No competing PR was written. **Check for an
  existing fix before commissioning an investigation into a known defect.**

- **A "failed" run was a deliberate falsifiability probe, not a defect.** #895's branch
  shows a failing run asserting `PROD_DATABASE_URL` was unconfigured, although the secret
  exists. Its head commit `fec4692a` is *"TEMPORARY can-fail probe — bogus secret name to
  prove visible-failure branch"* (it substituted
  `PROD_DATABASE_URL_CANFAIL_PROBE_DO_NOT_USE`), reverted two minutes later in `1fc3eaad`.
  The author was mutation-proving their own fail-fast path — the same discipline this
  audit applies. **Read the commit before reading a red run as a defect.**

- **One more invalid mutation of my own.** Testing whether `authority_basis_census_seed`
  can fail, I first mutated `_kala_tool_registration.ts`'s `MCP_TOOLS_ROOT` and observed
  exit 0 — and nearly recorded "this gate cannot fail either." That mutation never reached
  the code path: `authority_basis_census_seed.ts` declares its **own** `MCP_TOOLS_ROOT` at
  line 49 and does not import the shared helper's. Mutating the right constant gives
  exit 1 / FAIL=1. Both census seeds are falsifiable and were kept on the PR path for
  that reason. **Confirm a mutation actually reaches the code under test before believing
  a negative result.**

**6.6 `strict: true` livelocked this campaign four times, on the PRs auditing it.**
#963 once, #964 twice, and #968 once — each needing a manual `git merge origin/main` +
push before it could land, because GitHub's auto-merge does not update a behind branch.
At a median 37 merges/day (peak 104) against a ~9.5 min CI wall, a PR cannot reliably stay
current long enough to merge. The empirical case for a merge queue was produced *by
accident*, by the audit repeatedly being blocked by the thing it was auditing.

**6.7 A clean `git merge` produced a silently worse workflow than either parent.**
Merging main into PR #895's branch raised NO conflict, and combined #964's
`if: env.DATABASE_URL != ''` step guards with #895's fix in a way that made the
fail-loud step unreachable: the job-level env still read the nonexistent
`secrets.DATABASE_URL`, so every guard was false and the job would have reported SUCCESS
with all steps skipped — reintroducing precisely the silent no-op #895 exists to remove.
Caught only by reading the merged job body. **A conflict-free merge of two correct changes
is not evidence that the result is correct.**

## §6.8 — Gate-teeth audit (2026-07-31): every testable gate has teeth. Retire bucket EMPTY.

The earlier observation that `elev-serving-gates` and `tap-ci` had **0 failures across 100
runs each** was treated as suspicious. It was not evidence of anything. Run history
measures **usage, not capability** — the same error shape as the "21 `feature/**` branches,
0 CI runs → doubling refuted" reversal in §6.3. Every gate was therefore mutation-tested
the way #968's census seeds were, and **not one belongs in the retire bucket.**

Method for each: mutate an input the gate *claims* to check, confirm the mutation actually
reached the code under test (§6.3's `authority_basis` near-miss), then restore and confirm
return to exit 0. All mutations reverted; working tree verified clean afterwards.

| Gate | Mutation | Mutated | Restored | Verdict |
|---|---|---|---|---|
| `smoke_gate` | `_tool_enumeration.MCP_TOOLS_ROOT` → nonexistent | exit 1, FAIL=1 | exit 0 | **teeth** |
| `budget_census_gate` | same | exit 2 | exit 0 | **teeth** |
| `receipt_gate` | same | exit 1, FAIL=3 | exit 0 | **teeth** |
| `w1_bare_empty_census_gate` | delete one `CENSUS` entry (it asserts `length === 46`) | exit 1, FAIL=1 | exit 0 | **teeth** |
| `absence_lint_gate` | own `REGISTRY_ROOT` → nonexistent | **exit 0** (WARN=10) / `ABSENCE_LINT_STRICT=true`: exit 1, FAIL=10 | exit 0 | **detector sound, NOT ARMED** |
| `tap6_method_grep` | inject a new un-baselined `# rough` + `two_pass_verified` file under python-sidecar | exit 1, named the probe file | exit 0 | **teeth** |
| `sc_pointer_validation` | inject a bogus `instrument:` pointer | exit 1, named the instrument | exit 0 | **teeth** |
| `tap5_seam_conservation` (static half) | same bogus pointer | exit 1, Law-7 FAIL | exit 0 | **teeth** |
| `r18_param_noop_audit` | `TOOLS_DIR` → nonexistent | exit 4 | exit 0 | **responds — see caveat** |

**Stated honestly, three results are not a clean "has teeth":**

- **`absence_lint_gate` cannot fail as wired**, and that is by design, not by accident: it
  is documented report-only and additionally carries `continue-on-error` in the workflow.
  Its detector is provably sound — under `ABSENCE_LINT_STRICT=true` the same mutation
  produces exit 1 with FAIL=10. So this is *not* the ṢAḌ-DARŚANA failure mode (there the
  detector was **wrong**); it is a working detector deliberately left unarmed. Retiring it
  would delete a working report. **Recommend: arm `ABSENCE_LINT_STRICT=true`, or leave it
  and accept that it asserts nothing in CI — but say which.**

- **`r18_param_noop_audit` is only partly proven.** Exit 4 on a missing tools directory
  shows it is not a no-op, but that exercises crash-on-missing-input, **not** its ratchet.
  Whether the baseline ratchet catches a genuinely new param no-op was **unproven** at the
  time of writing. **It has since been proven — see §6.12 item 1.** (This paragraph is left
  in place rather than rewritten, because the sequence matters: §6.8 was written before the
  proof existed, and the workflow comment in tap-ci.yml asserted "Ratchet PROVEN" while this
  section still said "unproven". Two surfaces disagreeing about the same fact is exactly the
  drift this document exists to catch.)

- **Three TAP jobs are unfalsifiable in this environment, and that is not a pass.**
  `mcp_tool_smoke` (exit 3, no live server), `s13_coverage_matrix_live` (exit 3) and
  `tap7_distribution_gates` (exit 3) all need secrets this repo does not have. They have
  **never been able to run**. A gate that has never run is not a passing gate.
  `tap5_seam_conservation` is the honest counter-example worth copying: it splits into 7
  laws, marks the 5 DB-backed ones `SKIPPED` with a reason, and genuinely executes Laws 4
  and 7 — so its exit 0 is earned by the static half rather than fabricated.
  **Recommend: wire the secrets or retire the three jobs.**

**Conclusion: no retirement PR was raised for Item 3, because the retire bucket is empty.**
The decision not to retire on run history was correct, and the earlier framing of these two
workflows as suspect was wrong — recorded here rather than quietly dropped.

## §6.9 — Merge queue is UNAVAILABLE on this repository. The campaign's headline remedy cannot be applied.

Recorded because four passes of this campaign built toward a merge queue, and the reason it
cannot exist here was not discovered until the migration was actually attempted.

**`amonty84/Madhav` is owned by a USER, not an organization.** `gh api repos/.../--jq .owner.type`
returns `User`, and `gh api orgs/amonty84` returns 404. **GitHub's merge queue requires an
organization-owned repository.** That single fact explains every dead end hit along the way:

| Where we looked | What we saw | Why |
|---|---|---|
| Classic branch protection (REST) | no merge-queue key among 11 keys | unsupported |
| GraphQL `BranchProtectionRule` / `UpdateBranchProtectionRuleInput` | no queue fields | unsupported |
| Classic rule's edit page (read in-browser) | no checkbox | unsupported |
| **Rulesets API** | **HTTP 422 `Invalid rule 'merge_queue'`** | **unsupported** |

The ruleset attempt is the decisive one, and it was isolated properly rather than guessed at:

- A **control** ruleset containing only `deletion` + `non_fast_forward` **created successfully**
  (id 20136552, immediately deleted) — so rulesets work on this repo and the token's permissions
  are sufficient. The failure is specific to the rule type.
- `merge_queue` was rejected **with no `parameters` key at all**, not merely with bad parameter
  values. So it is not a schema/tuning problem; the rule type itself is not accepted.
- All probes used `enforcement: "disabled"` against a never-matching ref
  (`refs/heads/__never__`) so nothing could take effect while testing.

**Nothing was applied.** `gh api repos/.../rulesets` returns empty, and classic protection reads
exactly as before: `strict=true`, the same 4 contexts, `enforce_admins=true`, force-pushes and
deletions off. The migration was abandoned at Step 2 and Steps 3–4 are moot.

**The migration should NOT proceed anyway.** Its only purpose was the queue. Without it, moving
`main` to a ruleset would be pure churn — and worse than neutral: merge queue is what *forces*
`pull_request` to be required, and classic protection currently has **Require a pull request:
OFF**. Migrating would therefore impose a real behaviour change (blocking direct pushes to `main`)
in exchange for no benefit at all.

**What remains of the original problem.** The queue was the *means*; the *goal* was ending the
`strict: true` livelock (§6.6 — it blocked this campaign's own PRs four times, at a median 37
merges/day against a ~9.5 min CI wall). With the queue unavailable, the remaining levers are:

1. **Drop `strict: true`**, keeping all four required checks. Directly removes the livelock. Costs
   the "tested against latest main" guarantee — which is already largely illusory at this cadence,
   since main moves during the very CI run that certifies a branch. Post-merge CI on `main` still
   runs, and `deploy.yml` gates on it, so a bad interaction is caught quickly rather than never.
2. **Transfer the repository to a GitHub organization**, which makes merge queue available and
   delivers the original design. Far larger than a CI change; out of scope for this campaign.
3. **Leave `strict: true`** and accept the livelock as the cost of the freshness guarantee.

Native decision required; not taken here.

## §6.10 — `strict` dropped from `main` (2026-07-31). The campaign's closing change.

**What changed.** `required_status_checks.strict` on `main`'s classic branch protection:
`true` → `false`. Nothing else. All four required checks still gate `main`.

**Why.** The merge queue — the remedy this campaign spent four passes building toward — is
unavailable on a User-owned repository (§6.9). `strict` was the thing the queue was meant to
make redundant, so with the queue off the table it was dropped directly.

The cost `strict` was imposing is measured, not asserted: at a median **37 merges/day**
(peak 104) against a **~9.5 min** CI wall, a PR cannot reliably stay current long enough to
merge. It livelocked **this campaign's own PRs four times** — #963 once, #964 twice, #968
once — each needing a manual `git merge origin/main` + push, because GitHub's auto-merge
does not update a behind branch (§6.6). The audit was repeatedly blocked by the thing it was
auditing.

**What was given up, stated plainly.** `strict` guaranteed a branch was tested against the
tip of `main` at merge time. That guarantee is gone: two PRs that each pass independently can
now merge in sequence and interact badly. It is worth being honest that this is a real loss,
not a free win — the argument is that at 37 merges/day the guarantee was already largely
illusory, since `main` moves *during* the very CI run that certifies a branch. The
compensating controls: all four required checks still run on every PR, `ci.yml` runs again on
`main` post-merge, and `deploy.yml` gates on that run's success — so a bad interaction
surfaces in minutes rather than never.

**How it was applied.** The narrow endpoint
(`PATCH .../branches/main/protection/required_status_checks`), deliberately, because a
partial `PUT .../protection` silently drops every omitted protection — the failure mode to
avoid on a branch whose protection is the only thing guarding it.

One correction to the instruction as written: it specified `gh api ... -f strict=false`.
`-f` sends the **string** `"false"`; the typed form `-F strict=false` is required for a JSON
boolean. Used `-F`.

**Verified by diff, not by assumption.** Full protection JSON captured before and after,
normalised and sorted, then diffed. Exactly one line moved:

```
57c57
<   "strict": true,
---
>   "strict": false,
```

Re-asserted on the after-state: the four contexts byte-identical, `checks[]` app_ids
unchanged, `enforce_admins` still true, `required_pull_request_reviews` still absent
(require-PR still OFF), force-pushes/deletions/linear-history/conversation-resolution/lock
all still false. The only top-level key that differs is `required_status_checks`.

**Rollback — one command:**
`gh api --method PATCH repos/amonty84/Madhav/branches/main/protection/required_status_checks -F strict=true`

**Left in place deliberately:** #967's `merge_group:` trigger in `ci.yml`. It is inert without
a queue (it fires only on a `merge_group` event, which cannot occur here) and re-arms
instantly if the repository ever moves to an organization. One dead line is cheaper than a
churn PR.

## §6.11 — Repository moved to an organization; merge queue LIVE. The campaign's real close.

§6.9 recorded that merge queue was impossible here because `amonty84/Madhav` was owned by a
**User**. On 2026-07-31 the native created the **`Marsys-Technologies`** organization and the
repository was transferred. Merge queue is now live and proven end to end.

**The order mattered, and it was chosen to avoid a broken window.** GCP first, transfer second:

1. **GCP prepared BEFORE the transfer, additively.** Workload Identity Federation was
   hard-pinned to the old owner in two places, and either alone would have broken deploys:
   - provider attribute condition: `assertion.repository_owner == 'amonty84'`
   - both service-account bindings (`github-actions@`, `brahma-conductor-bot@`):
     `principalSet://…/attribute.repository/amonty84/Madhav`

   The new `Marsys-Technologies/Madhav` principalSet was **added alongside** the old one on
   both SAs, and the provider condition **widened** to
   `assertion.repository_owner == 'amonty84' || assertion.repository_owner == 'Marsys-Technologies'`.
   Both owners were therefore valid simultaneously, so `deploy.yml`, `fresh_chart_smoke.yml`,
   `iac-apply.yml` and `shad-darshana-circularity-guard.yml` were never dark for a moment.

2. **Transfer.** `POST /repos/amonty84/Madhav/transfer` → `Marsys-Technologies/Madhav`
   (asynchronous; the 202 response still echoes the old name, so completion was polled for).
   Audited afterwards, not assumed: branch protection intact with all four required checks and
   `enforce_admins`; **11 secrets** present; **2 variables** present; **4 open PRs** carried
   over. The old URL still redirects, so other sessions' worktrees kept working.

3. **Ruleset with `merge_queue` — accepted immediately.** The identical rule that returned
   `HTTP 422 Invalid rule 'merge_queue'` on the user account (§6.9) was accepted on the org
   without modification. That is the cleanest possible confirmation that org ownership, and
   nothing else, was the blocker. Ruleset `20141220`, active, empty bypass list: the four
   required checks, `pull_request`, `merge_queue` (batch 1 / SQUASH / ALLGREEN),
   `non_fast_forward`, `deletion`.

**Proven, at step level.** Two PRs went through the queue: #983 (real work, not a test) and
the throwaway canary #984. Checks executed on
`gh-readonly-queue/main/pr-984-8d8cb38b…` under the `merge_group` event — which is #967's
trigger, dormant since the morning, firing for the first time. All four required checks were
`success` at **job** level *and* at **step** level (8 / 11 / 7 / 16 non-skipped steps, zero
non-success), so no `continue-on-error` masking (§6 rule 1).

**Classic protection retired.** Only after the queue was proven. Coverage was verified
field-by-field first — 4 checks → 4 checks; `enforce_admins: true` → empty `bypass_actors`;
`allow_force_pushes: false` → `non_fast_forward`; `allow_deletions: false` → `deletion`. The
classic rule was then deleted; `repos/…/rules/branches/main` confirms all five rule types now
in effect from the ruleset alone.

**One intentional behaviour change.** Classic had **Require a pull request: OFF** — direct
pushes to `main` were permitted. A merge queue *requires* PRs, so the ruleset's `pull_request`
rule turns that ON. Direct pushes to `main` are now blocked. This is a real change and it was
unavoidable, not incidental.

**`strict` stays OFF, deliberately.** §6.10 dropped it to end the livelock. It stays off
*for a different reason now*: the queue builds and tests the actual prospective merge commit,
so requiring branches be up to date beforehand is redundant work rather than added safety —
it would simply reintroduce the rebase treadmill the queue exists to remove. The freshness
guarantee §6.10 gave up is now genuinely restored by the queue, which is the outcome the whole
campaign was aiming at.

**Rollback:** delete ruleset `20141220` and recreate classic protection from
`prot_before.json`; remove the `Marsys-Technologies` principalSets and narrow the provider
condition back to `amonty84`; transfer the repository back. Each step is independent.

## §6.12 — The three parked items, closed (2026-08-01)

Three signals were left honestly labelled but not doing all they claimed. All three are now
resolved. **Nothing was armed that red-gates `main`.**

### Item 1 — `r18` ratchet: PROVEN. No change needed.

Prior evidence was only exit 4 on a missing directory — crash-on-missing-input, not the
ratchet. Now tested properly, and **rule 4 was satisfied before the result was trusted**: r18
globs `platform-mcp/src/tools/**/*.ts` (excluding `*.test.ts`), and the probe was confirmed to
be inside the 45 files it enumerates *before* the run, not merely written to disk.

A probe tool declaring `never_read_param` in its zod schema and never referencing it in its
handler produced **exit 1**, naming `r18_ratchet_probe_tool`, `never_read_param` **and** the
file. Probe removed → exit 0, tree clean. The ratchet genuinely catches new violations.

**Documentation drift found and fixed:** `tap-ci.yml`'s step comment already said "Ratchet
PROVEN" (from the #974 pass) while §6.8 above still said "unproven" — the audit doc was stale
relative to the code. §6.8 now points here.

### Item 2 — `absence_lint`: narrowed 21 → 2, still report-only, 2 findings need native sign-off.

**Triage of all 21 STRICT findings — every one a false positive, in three clusters:**

| Class | Count | Why it is not a defect |
|---|---|---|
| Pure comment / docblock | 13 | prose, never served |
| Postgres error-matching regex | 5 | `/column ".*" does not exist\|.../` — code that DETECTS a DB error; the opposite of claiming absence to a user |
| Trailing `//` on a type-union line | 1 | the match sits in the comment half |
| String literals | 2 | genuinely served — kept in scope deliberately |

**Narrowing applied.** `servedTextOnly()` in `absence_lint_gate.ts` strips whole-line comments,
trailing `//` comments and regex literals before matching, and **deliberately keeps string
literals**, since a string is the one thing that plausibly *is* served. Result: **21 → 2**.

**A bug in my own narrowing, caught by re-checking rather than assuming.** The first version
stripped regex literals *before* trailing comments. The regex-literal pattern is greedy enough
to treat `L1/L2/L3` as a literal, which consumed the `//` and defeated the comment strip — so
`reading_checklist.ts:32` survived when it should not have. Order corrected (comments first,
then regex literals); 3 → 2. Recorded because the failure mode is generic: a sanitiser whose
stages fight each other looks like a detector finding.

**The detector still has teeth after the narrowing — re-proven, not assumed.** A seeded served
claim (`'That reading is not in your data.'`) took FAIL 2 → 3 and was named by file:line;
removed, back to 2. (First probe attempt used "do not exist" and matched nothing — the pattern
is `/does(?:n'?t| not) exist/i`. The probe was wrong, not the detector; checked before drawing
any conclusion.)

**NOT ARMED — and not because of volume. Neither survivor is a defect:**
- `L0_brahmagyan/tool_search.ts:30` — a tool *description* advising the model to search the
  catalog "before assuming a needed capability does not exist". The inverse of an ungrounded
  absence claim.
- `layers/register_d9_judgment.ts:363` — served text disclosing a real gap *and* its handling
  ("bhanga_checked reports false, not fabricated"). Honest disclosure; the grounding token
  merely falls outside the ±25-line window the heuristic can see.

Arming today would red-gate `main` on two non-defects, which §N.8 makes worse than leaving it
honest. **TO ARM: native sign-off on those two specific lines, then `ABSENCE_LINT_STRICT=true`
and drop `continue-on-error`.**

### Item 3 — TAP secrets: the infra EXISTS, and the wiring pattern is already in this repo.

Checked before designing anything (rule 8):

| Need | Exists? | Evidence |
|---|---|---|
| MCP endpoint for `TAP_MCP_SERVER_URL` | **yes, production only** | Cloud Run `amjis-mcp` at `https://amjis-mcp-qm256lasva-el.a.run.app`. `deploy.yml`'s `--no-traffic` step is a pre-smoke *revision* of that same service — there is **no separate staging deployment**. |
| Postgres for `TAP_DATABASE_URL` | **yes, production only** | Cloud SQL `amjis-postgres`, POSTGRES_15, RUNNABLE, asia-south1. Public IP enabled but **zero authorized networks**, so no direct access. |
| A way for a runner to reach it | **yes — already proven here** | `deploy.yml` lines 291–293 download and run `cloud-sql-proxy` on a GitHub runner and connect with `PROD_DATABASE_URL` under WIF. |
| `TAP7_API_BASE_URL` | **yes, production only** | Cloud Run `amjis-web`. |

So this is *not* the merge-queue situation — the capability is real. But **all three point at
PRODUCTION**, because no staging estate exists. That changes the recommendation:

**Recommended: wire the secrets, keep the jobs `workflow_dispatch`-only.** `mcp_tool_smoke`
calls *every* registered tool, and the DB gates query the live database. That is fine as a
deliberate on-demand sweep and wrong as per-PR load on production. Dispatch-only is where they
already are, so this costs nothing and makes them genuinely runnable.

**Not recommended: deleting them.** The capability exists, the scripts are real, and
`TOTAL_AUDIT_PROTOCOL_v1_0.md §3` still wants them.

**Native action — secret values are not mine to handle:** set `TAP_MCP_SERVER_URL` =
the `amjis-mcp` URL; `TAP_DATABASE_URL` = the same DSN as the existing `PROD_DATABASE_URL`
secret (reached via the cloud-sql-proxy pattern above); `TAP7_API_BASE_URL` = the `amjis-web`
URL. No code change is required to arm them — the `if:` guards already key off the secrets.

`tap5` untouched, as instructed — it remains the pattern the others should copy.

## §7 — Verification standard applied

No change was made on reasoning alone. Every claim was measured, and every gate
consolidation was proven falsifiable:

- vitest split: same machine, before/after, **identical** `669 passed | 42 skipped |
  7421 tests`; 30.04s → 14.63s; environment 311.82s → 58.89s.
- `requirements-ci.txt`: built from an import census, then **corrected by running the
  suite** — `geopy` / `geocoder` / `timezonefinder` / `pytz` are required (PyJHora
  imports them internally, invisible to a source grep) and `httpx` is required by
  `starlette.testclient` and was only ever present transitively. Final clean-venv
  run: install 10.6s, **4647 passed, 12 skipped, 7 subtests** — identical to baseline.
- Consolidated gate loops: mutation-tested. Injecting a broken gate produced
  `EXIT=1`, named the failing gate, **and still ran the gates after it** — so
  consolidation did not cost the "see every failure in one run" property.
- `actionlint` across all 13 workflows: single finding is a pre-existing SC2086 in
  `samiksha-daily` (deliberate `$ARGS` word-splitting), confirmed identical on
  `origin/main` by linting the base version.

## §8 — Left open (deliberately not changed)

1. **Branch protection `strict: true`** forces every PR to re-run CI after each merge
   to `main`. A real cost multiplier under merge-train load, but it is a safety
   property — a native call, not an audit's.
2. **26 ESLint errors / 93 warnings** on the chat-v2 paths. The Stage 1 lint step's
   `|| echo "no-op (paths not fully populated yet)"` was false on both counts; it is
   now honestly `continue-on-error` with the real numbers recorded. Fixing the
   backlog is separate work.
3. **`samiksha-daily` reads `DATABASE_URL`; the repo has `PROD_DATABASE_URL`.**
   Someone should confirm which is intended.
4. **`reconciliation-cadence.yml` has never run** (0 runs; dispatch-only, needs
   `MCP_CANARY_KEY`). **`fresh_chart_smoke.yml` ran once and failed** (2026-07-29).
   Both left in place — scheduled/dispatch-only, so near-zero PR cost — but neither
   is currently providing signal.
5. **Stages 6 and 7 fail on `Timed out waiting 120000ms from config.webServer`.**
   This is the highest-value item left open: two harnesses (accessibility and
   performance) that have never actually run in CI. Both are now HARD nightly gates,
   so they will be RED until someone fixes the dev-server boot. Stage 3 boots the
   same server fine, so start by diffing those two job configurations.
