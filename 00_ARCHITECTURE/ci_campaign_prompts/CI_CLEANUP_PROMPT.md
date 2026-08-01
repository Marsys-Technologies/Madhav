# Claude Code task — CI efficiency & relevance cleanup (Madhav)

## Objective

Make CI **fast and relevant to what we build today**. The repo went through a large legacy
teardown; some CI may still be shaped around the old world. Find out which parts, and remove the
drag — **conservatively, reversibly, and only on evidence you have personally verified.**

Do NOT optimise for a big diff. A small change that provably removes wasted wall-clock beats a
large rewrite that "should" help.

---

## Prime directive: verify before you assert

This task exists partly because a previous audit made three confident claims that were wrong. You
are expected to catch this class of error, including in the notes below.

Two specific traps, both previously hit in this repo:

1. **GitHub's `conclusion` field lies about `continue-on-error` steps.** A job containing a
   `continue-on-error: true` step that exited 1 still reports `conclusion: success` at job level.
   Never conclude "this stage passes" from the API's job conclusion. Open the logs, or read
   `steps[].conclusion` together with the actual command exit, and say which one you read.

2. **n=1 is not a measurement.** Runner variance on this repo has been observed at 285s–422s for
   the *identical* command. Do not claim a timing improvement (or regression) from one sample.
   Either take ≥3 samples per arm and compare medians, or state the number as unproven.

For every factual claim in your final report, state **how you verified it**. If you could not
verify something, say so plainly and leave it as an open question. An honest "unverified" is a
better outcome here than a confident guess.

---

## Repo facts

- Repo: `amonty84/Madhav`, default branch `main` (public repo).
- 15 workflows in `.github/workflows/`.
- Prior audit write-up (read it, but treat its claims as hypotheses to re-verify):
  `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md` — its §6 records corrections it made to itself.
- Relevant history: `00_ARCHITECTURE/LEGACY_TEARDOWN_CLOSE_v1_0.md` and
  `LEGACY_TEARDOWN_KILL_LIST_v1_0.md` describe what was torn down (2026-06-02, ~498 files deleted).

---

## Findings handed to you (RE-VERIFY EACH — do not trust this list)

Established by static analysis of `origin/main` on 2026-07-31. Each is stated with how it was
found so you can reproduce or refute it.

1. **No workflow has a `concurrency:` group.** All 15. Every push to a PR stacks a full new run
   set instead of cancelling the superseded one. Under merge-train/force-push load this is likely
   the single largest practical waste. *(Found by grepping `^concurrency:` across all 15 files.)*

2. **Four workflows fire on every PR with no path filter**, ~28 jobs total per PR:
   `ci.yml` (13 jobs), `elev-serving-gates.yml` (5+1), `shad-darshana-ci-skeletons.yml` (6),
   `tap-ci.yml` (4).

3. **Those same four also declare `push: branches: [main, 'feature/**']`.** A PR from a
   `feature/**` branch therefore runs the entire set **twice per push** — once for `push`, once for
   `pull_request`. `tap-ci.yml` adds `r6/**`. *(Verify this actually doubles runs by inspecting two
   runs of the same SHA; GitHub does dedupe in some configurations.)*

4. **11 jobs each pay a full `npm ci` to run one static script** that makes no network or DB call —
   every `*-gate-plan` job in `elev-serving-gates` and `shad-darshana-ci-skeletons`, plus both
   census seeds. Ten of them could be one job.

5. **CI is NOT referencing torn-down code.** All 27 scripts referenced by the 15 workflows exist on
   `main` (checked each path against `git ls-tree -r origin/main`, accounting for
   `working-directory: platform`). The waste is structural, not dead references. **The "it's all
   legacy" hypothesis is mostly false — say so if you confirm it.**

6. **Three genuinely dead path filters:** `platform/src/components/chat/ConversationSidebarV2.tsx`
   (chat-v2-smoke) and `platform/python-sidecar/services/ka_*/**` (circularity-guard — note 50
   `ka_*` service files DO exist, so this glob may simply be mis-written rather than dead; check
   whether Actions glob syntax supports `*` mid-path here). `pb/1/**` in pariprashna-ci is a
   **branch** filter, not a path — not a defect.

7. **Secret-gated gates that never run:** `tap-ci`'s DB gates and MCP smoke depend on
   `TAP_DATABASE_URL` / `TAP_MCP_SERVER_URL` / `TAP7_API_BASE_URL`. Confirm whether those secrets
   exist. If they don't, those jobs burn a runner to print a skip.

8. **Unverified, needs your check:** branch protection on `main` reportedly has `strict: true` and
   exactly four required checks — `TypeScript (src only)`, `Unit Tests`, `Secret Scan`,
   `Governance Gates`. Everything else is advisory and cannot block a merge. **This was not
   verifiable from the previous environment. Verify it first — much of the plan depends on it.**

---

## Work to do, in order

### Step 0 — Verify the ground truth

```
gh api repos/amonty84/Madhav/branches/main/protection
gh pr list --state open --json number,title,headRefName
gh run list --limit 50 --json name,conclusion,createdAt,event,headBranch,databaseId
gh secret list
```

Report: the real required-check list, the real `strict` setting, how many PRs are open, and which
workflows actually consume runner time (not which ones look expensive in YAML).

**Stop and report if the required checks differ from item 8** — the rest of the plan assumes them.

### Step 1 — Merge PR #963

It is open, green (28 passing / 0 failing), and already implements much of the above: concurrency
groups on all 15 workflows, deletion of `chat-v2-smoke.yml` and `brahma-conductor.yml`, and
collapsing the npm-ci-per-script jobs. **Abhisek has approved merging it.**

Before merging:
- Re-run or confirm its checks are still green against current `main`.
- Confirm none of the check names it renames is a required check (it claims none was — verify).
- Note the open-PR count: if `strict: true` is real, merging forces a full re-run on every open PR.
  If that count is high, say so and let Abhisek pick the moment.

After merging, confirm the concurrency groups actually take effect by pushing twice quickly to a
scratch branch and checking the first run cancels.

### Step 2 — Determine which lanes are actually live

Abhisek knows the **ṢAḌ-DARŚANA W0.6** lane. He does **not** know the current status of Elevation
K1, TAP/R6, chat-v2, or Pariprāśna — **do not ask him, find out.** Evidence to gather per lane:

| Lane | Workflow | Guarded code |
|---|---|---|
| Elevation K1 | `elev-serving-gates.yml` | `platform/scripts/census/elev_gates/` |
| ṢAḌ-DARŚANA W0.6 | `shad-darshana-ci-skeletons.yml` | `platform/scripts/census/shad_darshana_gates/`, `platform-mcp/src/__tests__/shad_darshana_w0_*` |
| TAP / R6 | `tap-ci.yml` | `platform/scripts/audit/tap/` |
| chat-v2 | `chat-v2-ci.yml` | `platform/src/components/consume/`, `components/chat/` |
| Pariprāśna | `pariprashna-ci.yml` | `platform/src/lib/pariprashna/`, `platform/tests/pariprashna/` |

For each: last commit date to the guarded code, commit count in the last 30/90 days, whether the
gate has ever actually failed a build (i.e. does it have teeth), and whether it is wired to
anything live. A lane whose guarded code has not moved in months and whose gate has never failed is
dormant **regardless of what its YAML header claims about itself.**

**Specific lead on ṢAḌ-DARŚANA:** its header states the three PLAN-mode gates "always exit 0"
because sibling `kala_*` facade lanes had not merged yet. Check whether those lanes have since
landed. If they have, those three gates are either real gates that should now be armed, or pure
waste — they cannot be both, and today they are silently the latter. This is the §N.8
Earned-Signal problem: a green check that measures nothing. Report which.

### Step 3 — Triggers-only cleanup (the approved scope)

Abhisek chose **triggers only**. One PR, minimal diff:

- Remove the redundant `push:` triggers (`feature/**`, `r6/**`) from the four always-on workflows,
  **if and only if** you confirmed in Step 1 that they genuinely cause duplicate runs. Keep
  `push: [main]` where a workflow legitimately needs to run post-merge.
- Add path filters so each lane fires only when its own guarded code changes. Use the table above.
  Be careful: a required check that stops firing on a PR will leave that PR **permanently pending**
  under branch protection, blocking the merge. **Never add a path filter to a required check** —
  `ci.yml`'s four required jobs must keep running on every PR.
- Fix or remove the dead path filters from item 6.

Explicitly **out of scope** unless you find something egregious and ask first: deleting workflow
files, restructuring jobs beyond what #963 already does, touching branch protection.

### Step 4 — Evaluate branch protection (recommend, do not change)

Assess whether `strict: true` (require branches up to date before merging) is worth its cost. Model
it: with N open PRs and M merges/day it forces roughly N×M full re-runs/day. Weigh that against
what it actually prevents — semantic conflicts that pass independently but break when combined.

Consider intermediate options: GitHub merge queue, or dropping `strict` while keeping the required
checks. **Present the trade-off with real numbers from Step 0 and let Abhisek decide.** Do not
change branch protection.

---

## Guardrails

- Work on a branch. Never commit to `main` directly.
- One reviewable PR for Step 3, separate from the #963 merge.
- Every change must be revertible in one line. Prefer changing a trigger to deleting a file.
- Do not rename or remove any required check.
- If a workflow is broken, prefer making it **honestly red** over suppressing it. A green check
  that measures nothing is worse than a red one that tells the truth.
- If you find yourself about to write "this should be faster" — measure it or don't claim it.

## Deliverable

A short report, prose not bullet-soup:

1. What you verified, and how (name the command or the log you read).
2. What you changed, and the one-line revert for each.
3. What actually got faster, with sample counts. Say "unproven" where it is unproven.
4. What is still broken or dormant and now visible.
5. Open questions for Abhisek — including the branch-protection recommendation and the
   `samiksha-daily` secret question (it reads `DATABASE_URL`; the repo only defines
   `PROD_DATABASE_URL` — which is intended?).

Record any self-corrections in `CI_EFFICIENCY_AUDIT_v1_0.md §6`, as the previous audit did, so the
next pass does not repeat them.
