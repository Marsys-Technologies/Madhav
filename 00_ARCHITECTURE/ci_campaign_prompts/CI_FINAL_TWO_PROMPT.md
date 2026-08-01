# Claude Code task — execute the two final CI decisions (Madhav)

Abhisek delegated both remaining decisions. They are **made** — execute as specified. The repo is
`Marsys-Technologies/Madhav` (org), `main` is queue-gated: open PRs, let the merge queue land them,
never commit to `main`.

Standing rule that dominates here: **no agent handles production secret values.** A DB connection
string or an MCP URL+key is credential material — you neither create nor paste those. Prefer
repointing to secrets that already exist over introducing new ones (the #895 pattern). Anything that
genuinely needs a new secret value is surfaced for Abhisek, not invented.

---

## Decision 1 — `absence_lint` stays report-only, PERMANENTLY (decided)

The 21 findings were all false positives; narrowing left 2, both working-as-intended
(a search-before-absence tool description; an honest `bhanga_checked reports false, not fabricated`
disclosure). Arming would red-gate `main` on non-defects. **Do not arm it.**

Land only a labelling change so this reads as a closed decision, not a pending TODO:
- Update the job/step name and the workflow header to state it is **report-only by decision
  (2026-07-31)**, with the one-line reason: the 2 residual matches are intended non-defects, and
  arming would block `main` on them. Note the detector remains sound (re-proven: seeded claim
  FAIL 2 → 3) so the report-only run still surfaces a genuine future absence-claim.
- Reconcile any other surface that describes `absence_lint`'s state so they agree (the campaign
  already hit one doc-drift bug — `r18` "PROVEN" vs §6.8 "unproven"; don't leave a matching one
  here). Record the decision in `CI_EFFICIENCY_AUDIT_v1_0.md §6`.

One line to revert. Do not touch the detector logic.

## Decision 2 — arm the three TAP jobs, dispatch-only, by REPOINTING to existing secrets

Decision: the three `workflow_dispatch`-only jobs (`mcp_tool_smoke`, `s13`, `tap7`) should be able to
run against real infra (it exists — `amjis-mcp`, `amjis-postgres` RUNNABLE, `deploy.yml:291–293`
already runs cloud-sql-proxy under WIF). They **stay dispatch-only** — `mcp_tool_smoke` calls every
tool and the DB gates hit live production; correct as a deliberate sweep, wrong as per-PR load.

Execute the credential-free way first:
1. **Enumerate the secrets/vars that already exist** on the repo/org
   (`gh secret list`, `gh variable list`, and grep other workflows for the names they reference —
   e.g. `PROD_DATABASE_URL`, `MARSYS_MCP_URL`, `MARSYS_MCP_KEY`).
2. For each of the three TAP references — `TAP_DATABASE_URL`, `TAP_MCP_SERVER_URL`,
   `TAP7_API_BASE_URL` — if an existing secret already holds the same production value another
   workflow uses, **change `tap-ci.yml` to read that existing secret** instead of the TAP-specific
   name. This is the #895 move: repoint, don't create. Confirm the existing secret genuinely points
   at the same estate before repointing — do not assume from the name alone.
3. For any TAP reference with **no** existing equivalent: leave that one job's guard as-is (it stays
   honestly SKIPPED) and **surface it to Abhisek** — name the exact secret, what it must point at,
   and that only he can set the value. Do not create a placeholder or a blank secret.

Verify: after repointing, run each newly-wired job via `workflow_dispatch` **once** and read the
result at step level (a `continue-on-error`/exit-3 job can still report green — §6 rule 1). A job
that now genuinely executes and passes is armed; one that still can't reach its estate goes back to
honestly SKIPPED with the reason. Do not make any of them a required check or PR-triggered.

`tap5` is untouched — it is the reference pattern (Laws 4 & 7 execute, 5 DB laws honestly skipped).

---

## Guardrails
- No new secret values created or pasted by you; repoint to existing, or surface for Abhisek.
- Nothing becomes a required check or runs per-PR; the three TAP jobs stay `workflow_dispatch`-only.
- `absence_lint` is not armed.
- Branch per decision; open PRs; the queue merges them. Every change one line to revert.

## Deliverable
Prose. For Decision 1: the label/doc change and confirmation the detector is unchanged. For
Decision 2: which of the three TAP references you repointed to which existing secret (and how you
confirmed the estate matches), which — if any — you surfaced to Abhisek as needing a value he must
set, and the step-level result of each dispatched run. End plainly: **is anything at all still open,
and if so is it only "Abhisek sets secret X"** — distinguish "needs a human with credentials" from
"needs more engineering."
