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

**6.3 A second-pass re-verification (2026-07-31) refuted three of this audit's own
structural claims and caught two more of its errors.** Recorded here so the pattern is
visible: every one of them came from a plausible inference that nobody had executed.

- **"The `push: [main, feature/**]` triggers double every PR run" — REFUTED.** The
  `feature/**` and `r6/**` branches do exist on origin (21 of them), but **none has run
  CI in the last 200 runs**; all active work uses `samapti/`, `chore/`, `shad-darshana/`
  prefixes. The doubling is latent, not actual. (One apparent counter-example — a `push`
  run of `ci.yml` on `shad-darshana/integration` — resolved to that branch carrying its
  own edited copy of `ci.yml` that adds itself to the trigger list; GitHub uses the
  workflow file from the pushed branch.)
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
