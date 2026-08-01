# Claude Code task — close out the CI campaign (Madhav)

Everything below is decided. Your job is to **verify, execute, and stop when verification
contradicts the plan.** Three prior passes have each surfaced at least one instruction that could
not be carried out as written; assume this one has a flaw too and report it rather than working
around it silently.

## Standing method rules (earned in this campaign — apply them, don't re-learn them)

1. A job-level `conclusion` is **`success` even when a `continue-on-error` step exited 1.** Read
   step conclusions or the actual command exit, and say which you read.
2. **n=1 is not a measurement.** Observed variance on this repo: 285–422s for the *identical*
   command. ≥3 samples per arm, compare medians, or write "unproven".
3. **"Doesn't fire today" ≠ "the mechanism doesn't exist."** Run the experiment before recording a
   defect as refuted.
4. **A mutation proves nothing until you confirm it reached the code under test.** (The
   `authority_basis` near-miss: the mutation hit `_kala_tool_registration.ts`, which declares its
   own `MCP_TOOLS_ROOT` at line 49, and nearly produced a false "this can't fail either.")
5. **An impossible instruction gets recorded, not silently reordered.**

Log anything new to `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6`.

---

## Item 1 — Merge queue: Abhisek enables it, you verify it

**He performs the UI step** (Settings → Branches → `main` → Require merge queue; batch 1; squash;
`strict: true` stays ON). You already confirmed this cannot be done via REST or GraphQL — do not
create a ruleset.

The precondition is met and verified: `merge_group:` is on `main` in `ci.yml`, the four required
check names are byte-identical, and main's CI is green on all four.

**#968 is the canary.** It is green, armed, and nothing depends on it. Once the queue is on, push it
through and watch:

- **PASS:** the four required checks appear and complete on a `gh-readonly-queue/main/…` ref, and
  #968 merges.
- **ABORT:** the checks do not appear within a few minutes, **or any check on a queue ref reports
  `cancelled`.** A cancellation means the `cancel-in-progress` fix did not fully take and PRs will
  be evicted. Tell Abhisek to untick immediately — no code revert needed.

Read the queue-ref checks with rule 1 in mind: a queue check that "succeeded" while its step exited
non-zero is the same trap in a new place.

**Only after #968 merges cleanly through the queue**, tell Abhisek to untick "Require branches to be
up to date" (`strict`). Do not treat one clean pass as proof of throughput — report what you
observed, not what you expect.

Also record in §6: `strict: true` livelocked this campaign **three times** (#963 once, #964 twice),
each needing a manual update. The audit was repeatedly blocked by the thing it was auditing. That is
the empirical case for the queue and it was arrived at by accident.

---

## Item 2 — PR #895

The `PROD_DATABASE_URL` repoint and the fail-fast are **approved** — same secret `deploy.yml`'s
migration step already reads, so it grants no new access. Do not write a competing PR.

1. Rebase #895 onto current `main`. It will conflict with #967 in `ci.yml`; resolve keeping **both**
   the `merge_group:` trigger and the queue-safe `cancel-in-progress` expression. Losing either
   silently re-arms the eviction bug.
2. The rebase re-runs `Boot-time pointer validation`. **If it goes green, it was staleness. If it
   survives the rebase, it is real — stop and report; do not merge through it.**
3. Review the **Postgres service container** on its own merits and report separately. Un-skipping 6
   DB-integration tests is a real change to what CI covers and to per-PR cost; it arrived attached
   to a secret fix, which is not a reason to wave it through. Say what it adds to wall-clock.
4. Do not merge #895 until #968 has cleared the queue — one change through the new machinery at a
   time.

---

## Item 3 — elev-serving-gates and tap-ci: mutation-test, do not retire on run history

**DECISION: do not retire these on "0 failures across 100 runs."** That measures usage, not
capability — the same error shape as the earlier "21 `feature/**` branches, 0 CI runs → defect
refuted" reversal, which the probe overturned. Retiring on it would delete real coverage.

Test them the way #968's census seeds were tested. For each gate in `elev-serving-gates.yml`
(`smoke_gate`, `budget_census_gate`, `receipt_gate`, `absence_lint_gate`,
`w1_bare_empty_census_gate`) and each in `tap-ci.yml` (`tap6_method_grep`, `sc_pointer_validation`,
and the secret-gated `mcp_tool_smoke` / TAP-5 / TAP-7 / S-13):

- Mutate an input the gate **claims** to check. Record the exact mutation.
- **Confirm the mutation reached the code under test** (rule 4) before believing any result.
- Restore, and confirm it returns to exit 0.

Classify each into exactly one bucket:

- **Has teeth** — mutation goes red. Keep as-is. Say what it caught.
- **Cannot fail** — mutation stays green. Retire to `workflow_dispatch`-only, same treatment as the
  ṢAḌ-DARŚANA gates, with the real reason written into the header. Do not delete the job or script.
- **Cannot be tested from here** — the secret-gated TAP jobs, where the secrets don't exist. These
  are **not** "has teeth"; they are unfalsifiable in this environment. Say so plainly and recommend
  either wiring the secret or retiring the job. A gate that has never been able to run is not a
  passing gate.

One reviewable PR for whatever lands in the retire bucket. Nothing deleted; every change one line.

---

## Guardrails

- Branch per item; never commit to `main`.
- Do not rename or remove any required check.
- Do not create a ruleset.
- Prefer honestly red over silently green.
- If Abhisek has not yet enabled the queue, do Items 2 and 3 first — neither depends on it.

## Deliverable

Prose. What you verified and how; what changed and its one-line revert; timings with sample counts
or the word "unproven"; what is now honestly visible as broken; and — most valuable — anything that
contradicted the instructions above.

At the end, state plainly whether the campaign is **closed** or what remains. If the answer is
"closed except X", name X.
