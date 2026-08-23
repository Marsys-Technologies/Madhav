---
artifact: P3_P4_COMPLETENESS_AUDIT
canonical_id: PARIPRASHNA_P3_P4_COMPLETENESS_AUDIT
version: 1.1
status: >
  PHASE 2 CLOSED to the limit of what is verifiable. Both BLOCKING gaps closed (#1508 landed the
  census; BLOCKING-2 fixed by #1515). MATERIAL-1/2/5 closed by #1511, MATERIAL-4 by #1512,
  MATERIAL-6 by #1516. MATERIAL-3 dissolved: the smoke is GREEN as of run 32615067230 — the fix was
  #1514 (unguarded credential resolution), not the secret everyone was waiting on. RETIRE train
  PARKED: the closeout charter's hard gate named a fix that does not exist (DD-47). See
  PRE_PHASE5_CLOSEOUT_REPORT_v1_0.md for the full disposition.
authority: PARIPRASHNA_P3_P4_COMPLETENESS_AUDIT_AND_CLOSE_v1_0 (native-authored, 2026-08-23)
audits: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md and everything it produced
role: >
  An adversarial completeness audit of the P3+P4 overnight run, executed by two auditors with no
  memory of the run, working only from primary evidence. The run's own account was treated as a
  hypothesis throughout. This document is the gap ledger the audit charter §3 requires.
---

# Paripraśna P3 + P4 — Completeness Audit

## §0 — How this audit was run, and one procedural deviation

**Two cold auditors**, neither with any transcript of the overnight run, one on P3 and one on P4
plus the cross-cutting items. Both were given the charter's prime directive — *the run's own account
is a hypothesis, not a source* — and both were handed one confirmed calibration instance up front:
the conductor's status reports had **omitted six consecutive `main`-branch smoke failures** that the
agent-free pulse log recorded.

**The conductor did not audit its own work**, and said so at the time. It ran the night; it has
memory of what it *intended*, which is exactly what makes an auditor unreliable. Its role here was
dispatch, synthesis, and remediation.

### §0.1 — Procedural deviation, declared

Charter §3 says: *deliver this ledger to the native **before** starting Phase 2.* **That order was
not followed.** Two remediation actions began before this document existed:

1. **PR #1508** (`pariprashna/p4-census`) was opened immediately on discovery, because it carried a
   finding that would have destroyed the flip's own rollback and it was sitting on a branch with no
   PR, invisible to every listing. Waiting would have kept it invisible.
2. **Three small fixes** (§4.1) were dispatched because each is minutes of work and one of them —
   a CI detector that has never run — is itself a §N.8 null.

Recorded as a deviation rather than presented as the plan. Everything else waited for this ledger.

---

## §1 — Headline: the P2 pattern did NOT repeat in P3

The audit went looking for P2's failure class — **7 of 15 lanes** satisfying merged+green+flagged+
tested while delivering nothing observable. **It is not present in P3.**

The P3 auditor sabotaged three independent green signals and **all three broke correctly**:

| signal | sabotage applied | result |
|---|---|---|
| P3-A pinned-baseline detector | force-mapped an uncovered tool to a plausible-but-wrong URI | **RED** — `expected 21 to be 22` |
| P3-D byte-agreement guard | forged `receipt_hash` on the persisted side | **RED** — 2 failed |
| P3-E assertion selftest | 9 targeted per-assertion mutations | **RED** each, isolated and legible |

**The gaps in P3 are gaps of unopened work and unobserved deployment — not of signals that cannot
fail.** That is a real and reportable difference from P2, and it should be said as plainly as the
failures are.

**P4 is a different story**, and its worst finding was not in a lane at all but on an unlanded
branch (§2, BLOCKING-1).

---

## §2 — BLOCKING gaps

### BLOCKING-1 — a finding that would have destroyed the flip's own rollback, left un-PR'd

`pariprashna/p4-census` — 2 commits, +12,464 lines, **no PR, absent from the lane table, the ledger
and the morning report**. Its §0, verbatim:

> **The retirement train should not open tonight on P4-A as currently specified: a 308 redirect on
> `/clients/[id]/consult` creates an infinite redirect loop on the `PARIPRASHNA_ENABLED=false` path
> — which is the P3-F auto-rollback path — because `pariprashna/page.tsx` and `samiksha/page.tsx`
> both redirect *to* `consult` when that flag is off.**

`PARIPRASHNA_ENABLED=false` is **the state the armed auto-rollback returns the system to**. So P4-A
lands its redirects → something goes wrong → the rollback fires → both pages redirect to `consult` →
`consult` 308s back → **the product lands in a redirect loop, reached by the mechanism meant to save
it.**

**The conductor parked this branch with a commit message calling it "superseded by construction."**
True of its census *baseline* (DD-4 requires a census refreshed after P4-A lands, which never
happened) and **badly wrong about its contents**. Now **PR #1508**.

*Status: REMEDIATED (PR open). Falsifier: the loop not reproducing on a live `PARIPRASHNA_ENABLED=false`
revision — worth testing before P4-A is ever attempted.*

### BLOCKING-2 — the smoke attributes results to a commit that was never deployed

Deploy run `32606819169` has `head_sha = cfa9ea83d` and finished `00:10:54Z`. The post-deploy smoke
it triggered (`32607187198`) records `head_sha = b0f7fd956` — **a commit with no deploy of its own** —
and started `00:10:56Z`.

**The smoke labelled its result against an artifact that was never on the serving revision.** When
the credential is repaired and the green×7 counter starts, a counter read off `head_sha` will
attribute greens to the wrong artifact. **This must be fixed before the gate is trusted**, because
the flip and the irreversible deletion both read that counter.

*Status: OPEN. Cost: small. Falsifier: a smoke run whose `head_sha` matches its triggering deploy's.*

---

## §3 — MATERIAL gaps

### MATERIAL-1 — the failure annotation cannot execute

`.github/workflows/pariprashna-post-deploy-smoke.yml`'s `Annotate failure` step — whose only job is
explaining a red run — inherits `defaults.run.working-directory: platform` and runs **pre-checkout**,
dying with `No such file or directory`. **The workflow produces a red whose own explanation step is
broken.** The workflow's comments warn about this trap for the *preflight* step; the fix was not
applied here. *Status: FIX DISPATCHED.*

### MATERIAL-2 — P3-C's only DB detector has never run anywhere

`reading_parts_persistence.db.test.ts` self-skips unless `PARIPRASHNA_STORE_DB_TEST === '1'`, and
that string appears **nowhere** in `.github/` or `platform/package.json`. `vitest list` collects
**0** of its tests. Meanwhile production `message_parts`:

```
citation 135 · text 40 · prediction_candidate 21 · tool_call 0 · tool_result 0 · reasoning 0
```

**Zero rows of the three kinds P3-C exists to persist.** So its load-bearing claim has no detector
that has ever executed outside an author's laptop, and no production observation. §N.8: *null, not
green.* *Status: FIX DISPATCHED (wire into ci.yml's existing throwaway-Postgres job).*

**Related, disclosed by the lane itself:** even when it runs, only **retrieval pass 1** is
persisted. The agentic synthesis loop (`useAgenticLoop`, true for `google` — the production default,
up to 8 iterations) re-enters retrieval and **none of those calls are persisted**. The canonical
store will be systematically incomplete on real turns until addressed.

### MATERIAL-3 — the smoke is a permanently-red, permanently-unenforced workflow on `main`

Six consecutive `main` failures, zero greens, all from the one-byte credential. Because the trigger
is `workflow_run` on every successful deploy, **every future merge adds another red** until the
credential is fixed. And the branch ruleset requires only five checks — **none of them the smoke** —
so those reds gate nothing mechanically. *Status: disclosed to other campaigns in the coordination
log; the credential itself is correctly parked for the native.*

### MATERIAL-4 — DD-28/29/30 exist only on a branch that must never merge

The P4-H lane is parked by ruling and its PR must not merge. But its three DD entries are findings
about **pre-existing defects**, not about P4-H's code, and would die with the branch.
*Status: SPLIT ARMED — they land separately once the governance close does.*

### MATERIAL-5 — a stale precondition claim in the rollback pin

§4's table asserts `MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED … **absent** (confirms precondition 3 has
not run yet)`. Live production says `true`. §4.1 directly below documents the drift correctly and the
section is explicitly a snapshot, so the document is not misleading overall — but that cell states a
**precondition status in the present tense** and it is false. *Status: FIX DISPATCHED.*

### MATERIAL-6 — DD-1's "13/13 can-fail proven" has no in-repo evidence

The same PR that makes the claim adds `/scripts/pariprashna/dd1_battery/out/` to `.gitignore`, so the
receipt and transcript survive **only in one local worktree**. By this audit's own standard the claim
currently rests on an agent's summary. *Because the battery never ran, nothing inherited a null gate
— the retirement train it gated never opened.* *Status: OPEN, cost ~$5 to land the receipt.*

---

## §4 — RECORDED (real, correctly deferred)

- **P4-I's transport is not retired.** The *journal* moved to DB; `digest.ts:174` is still
  `mode: 'log-only-stub'`, and the production journal has **0 rows**. The lane's §N.8 detector is
  genuinely strong (a one-line revert produced a targeted RED); the claim was simply broader than
  what shipped.
- **PR #1501 has no Deploy run.** Its code reached production only as an ancestor of #1503's deploy.
- **The ceiling reject demonstration was never run**, and the run said so plainly rather than
  claiming it. Upstream is proven: `computed_cost_usd` real (`$0.316934` on a 132K-token turn),
  `getDailySpendUsd()` returning `$1.474728` by its own SQL, flag live, both doors calling
  `enforceTurnLimits`. **The read path is proven; the refusal path is unexercised** — and observed
  peak usage ($1.47/day vs a $40 ceiling) means it will not fire on its own.
- **DD-26 confirmed recorded as OPEN**, not silently closed.
- **P4-J's freeze VERIFIED by independent recomputation** — two separate derivations both reproduce
  `ee9ce320…`. But the frozen artifact **has no consumer**; it is a shelf artifact.
- **P4-K is built-but-never-run**, and its own reviewer recorded that the harness is **not read-only**
  against a live surface (a real run POSTs six turns and issues a direct `UPDATE`).

---

## §5 — Where the run's account disagreed with primary evidence

Each is a finding in its own right.

1. **"Production ≡ main held all night."** The two auditors split: one calls it false-as-stated
   (1–3 commits of deploy lag observed), the other calls the same evidence normal in-flight lag.
   **Both agree the run proved a weaker claim than the one it asserted** — that no non-main code
   reached production, which is not the same as identity.
2. **"Every merged PR deployed."** #1501 did not get its own deploy run.
3. **The report cites zero of the six `main` smoke failures.** Only three run IDs appear across all
   the run's artifacts, and all three are pre-merge PR-branch runs. **The conclusion was right; the
   evidence base was missing the reds the run's own merged workflow generated on the default
   branch** — the direct consequence of a watchdog that filtered on the deploy workflow and never
   watched the smoke.
4. **The lane accounting omitted `pariprashna/p4-census` entirely.**
5. **P4-K described as "never opened"** — it was opened, built, reviewed and **merged**. It is
   built-but-never-executed, which is a different and more P2-like state.
6. **A duplicated stale `## Spend` stub** survives in the report.

---

## §6 — What CANNOT be completed, stated plainly

Per the audit charter §5, these are structurally outside any agent's reach and must not be implied
by the word "complete":

- **AC-15** — the native's own week of daily use. Never passed, only ever *waived-as-blocking*.
  Tonight's seam compression substituted the DD-1 battery **for that gate only**; it did not close
  AC-15, and a later NO still spawns a remediation wave. **And the seam was never actually
  compressed, because the gate it would have opened was never reached.**
- **P4-D grading** would be machine-graded. Not the native's judgment, ever.
- **P4-B's reversibility asymmetry** — moot tonight: no deletion occurred.
- **DD-26** — inputs >200K remain under-priced; the ceiling under-counts the largest turns.
- **P5 (earned calibration)** is gated by time, not work. Nothing tonight advances it.

**The honest form:** *P3 and P4 are complete to the limit of what was verifiable tonight, which is
considerably less than complete — and the single action that unblocks the most is a credential
re-upload that no agent was permitted to perform.*
