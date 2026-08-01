# Claude Code task — close the three parked CI items (Madhav)

The CI campaign is otherwise closed: `main` is on ruleset 20141220 with a live merge queue
(repo is now `Marsys-Technologies/Madhav`, an org). Three items were left **honestly labelled but
unresolved**. None is broken; each is a signal not yet doing all it claims. Close them — or, where
closing needs infra or a human decision, establish exactly what's needed and stop there.

Standing rules from `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6` that bite here:
- **A mutation proves nothing until you confirm it reached the code under test** (rule 4 — the
  `authority_basis` near-miss that mutated a file declaring its own `MCP_TOOLS_ROOT`).
- **Confirm the capability exists before designing the path to it** (rule 8 — the merge-queue-on-a-
  User-repo dead end).
- Prefer honestly red / honestly skipped over silently green. An item that can't be closed cleanly
  stays labelled, with the reason — do not force it green.

Assume this brief has a flaw too; record it rather than working around it.

---

## Item 1 — `r18` ratchet: prove it or narrow its claim (cheapest; do first)

`r18_param_noop_audit` exits 4 on a missing directory, so it isn't a no-op — but whether its
ratchet actually catches a **new** violation is unproven.

Inject one real new param-noop violation of the kind it's meant to catch. **Confirm the injection
reaches the code r18 scans** (rule 4 — check the path it globs, not just that a file changed) before
trusting the result.

- **Catches it (exit non-zero, names it):** record that in §6, leave r18 as-is. Done.
- **Misses it:** the ratchet is decorative. Rename the job + header to describe what it actually
  verifies (a presence/exit check, not a ratchet), so it stops overclaiming. One-line revert.

Restore the injection; confirm r18 returns to its baseline exit.

## Item 2 — `absence_lint`: triage the 21, then arm only if earned

The detector is sound — `ABSENCE_LINT_STRICT=true` goes red (exit 1, FAIL=21) — but it's wired
report-only because arming it blind turns CI red on 21 untriaged findings. The prior pass noted most
are **comments and Postgres error regexes**, i.e. likely false positives that need the detector's
scope narrowed before it's armed.

Do the triage, in the PR body so a human can see it:
1. Dump all 21 findings with file:line and the matched text.
2. Classify each: **real** ontological-absence phrasing not backed by a resolver-miss path, vs
   **false positive** (a comment, a Postgres error-string regex, test fixture, etc.).
3. If false positives cluster by kind, **narrow the detector** to exclude that class (e.g. skip
   comments / string literals / specific paths). Re-run; report the new count.

Then decide, and state which:
- **All remaining are real and few:** fix them or, if they're pre-existing debt, arm the gate
  (`STRICT=true` / make blocking) **only** with Abhisek's sign-off, since it turns CI red — flag it
  for him rather than flipping it yourself.
- **Findings are noise the narrowing can't fully kill:** leave report-only, but update the label to
  say *why* it stays unarmed (scope limits), not just *that* it does.

Do **not** arm a gate that would red-gate `main` without Abhisek explicitly approving the specific
findings it will now block.

## Item 3 — three TAP secrets: establish feasibility, don't invent

`mcp_tool_smoke` / `s13` / `tap7` are parked at `workflow_dispatch`, honestly SKIPPED, because
`TAP_MCP_SERVER_URL`, `TAP_DATABASE_URL`, `TAP7_API_BASE_URL` don't exist. Arming them needs backing
infra, not just a secret string — and per rule 8, confirm the infra exists before designing the
wiring.

Investigate and report — **no PR unless the finding is "retire permanently":**
1. Does a staging `platform-mcp` deployment exist that `TAP_MCP_SERVER_URL` could point at? Does a
   reachable Postgres (Cloud SQL Auth Proxy, per `platform/scripts/audit/tap/README.md`) exist for
   the DB gates? Check the deploy workflows / infra, don't assume.
2. **If the infra exists:** document the exact secret values/wiring needed and hand Abhisek the
   one-step to add them (he sets secrets — you don't handle secret values). Then the jobs can drop
   `workflow_dispatch`-only.
3. **If it doesn't:** these gates cannot run and won't for the foreseeable future. Recommend one:
   keep parked as-is (honest, zero cost), or delete the jobs + scripts outright if they're not on
   any roadmap. Present the trade-off; let him choose. Do not delete unilaterally.

`tap5` stays exactly as-is (Laws 4 & 7 execute, 5 DB laws honestly skipped) — the pattern the others
should copy. Don't touch it.

---

## Guardrails

- Branch per item; never commit to `main` (it's queue-gated now — open PRs, let the queue merge).
- Nothing armed that red-gates `main` without Abhisek's explicit approval of the specific findings.
- No secret values handled by you; secrets are Abhisek's to set.
- Every change one line / one field to revert.

## Deliverable

Prose. Per item: what you verified and how; r18's mutation result read at the right scope; the
absence_lint triage table and the arm/hold decision with reason; the TAP-infra finding and your
recommendation. End plainly: **which of the three are now closed, which are decisions parked on
Abhisek, and which are genuinely done-and-labelled** — and confirm nothing you did red-gated `main`
without sign-off.
