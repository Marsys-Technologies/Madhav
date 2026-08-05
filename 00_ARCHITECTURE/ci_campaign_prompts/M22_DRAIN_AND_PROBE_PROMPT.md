# Claude Code task — drain the prohibited residue, check `computed_extension`, probe the divergence path (Madhav)

Repo `Marsys-Technologies/Madhav`, `main` queue-gated (PRs only; re-arm auto-merge after a queue
ejection — a consumed arm reads as "off"). Standing rules `CI_EFFICIENCY_AUDIT_v1_0.md §6`.

**Rule 9, sharpened by your own last pass:** you retracted three Stage-1 claims because your cwd sat
on `parishodhana/dark-corpus-remeasure`, behind `main`. **Before anything else, confirm you are
reading `origin/main`** and state the SHA you worked from in the report. That error is now twice as
likely to repeat as any other.

Three tasks, independent, in one PR or three — your call, but the drain must not wait on the other
two. **Out of scope: the 392,001 unearned rows keep their tier; no new vocabulary member; no CHECK
migration.** Those wait on Abhisek.

---

## Task A — Drain the prohibited + deprecated residue (approved, unblocked)

59,842 rows, **zero claim change** — `isVerifiedPassStatus()` already counts all three as
unverified, so no served grade or warranty sentence moves.

| from | to | rows | why |
|---|---|---|---|
| `PASS` | `single` | 10,591 | PROHIBITED (Ruling 13); chart_facts 5,428 + bodha_msr_signals 5,163 |
| `pass` | `single` | 4,119 | PROHIBITED; 11 bodha tables |
| `single_pass` | `single` | 45,132 | `deprecated_alias_of="single"`; use `canonical()` |

- **Re-verify the counts yourself** against the live DB (read-only, existing `PROD_DATABASE_URL` +
  cloud-sql-proxy) before writing anything. My brief previously said 5,428 when the truth was
  10,591 — do not inherit a number, measure it. Report per-table counts.
- Use the vocabulary module's own `canonical()` / `UNVERIFIED_DEFAULT` rather than string literals.
- **Test against one table (or one chart) first**, show before/after counts, then hand the
  production invocation to Abhisek unless an existing sanctioned rebuild/backfill path covers it.
  No destructive rebuilds. Honest states only.
- **Confirm no CHECK is violated** — `chart_dashas`/`chart_divisionals` permit `single`, so the
  drain is legal there; verify rather than assume, and report if any target table's constraint
  would reject.
- **Verify the claim of zero user-visible change** rather than asserting it: for one affected page,
  compute `grounding_score` and the warranty sentence before and after. If either moves, STOP and
  report — that would mean a consumer treats these values differently than measured.
- After: G7/`gates.py` should stop flagging these; confirm. MV `209` holds 1,515 rows all
  `two_pass_verified` — confirm unchanged.

## Task B — Does an existing vocab member already mean "deterministic single-pass"?

Before any fourteenth member is proposed, settle this on evidence.

- **Quote the `meaning` field of all 13 members** of `VERIFICATION_PASS_STATUS_VOCAB` verbatim.
- For **`computed_extension`** (14,387 rows, 2 tables) specifically: what does its `meaning` say,
  which writer emits it, into which tables, for which fact categories, and — by reading two or
  three actual emit sites — what does it mean *in practice*? Same for `floored` (8,130) and
  `not_defined_for_nodes`, which may also be near-misses.
- Answer plainly: **does any existing member already carry "computed once by a deterministic method
  from canonical inputs, never independently re-derived"?** If yes, name it — the demotion has its
  tier and needs no new member. If no, say precisely which semantic gap remains.

This is the "seventh definition" check: #996 declined to create a new module because the concept
already had a home. Do the same test for the concept before adding a string.

## Task C — Probe the divergence path (the one that may reopen a settled verdict)

`divergent_flagged` has **zero rows across the entire estate**, while 1,873,958 rows claim
`two_pass_verified`. A comparison that has never disagreed is either a flawless engine or a
comparison that does not run. `_verify_vimshottari`'s Pass 2 is gated
`if chart_id == CANONICAL_CHART_ID`, which would produce exactly this signature.

- **Confirm the tier is reachable at all**: in a test/dev context, inject a deliberate divergence
  into a real verification path (`ga_nakshatra`'s `two_pass_verdict` is the known-live one) and
  confirm a row lands `divergent_flagged`. If it cannot be made to fire, that is a defect in the
  verifier, not a property of the data — report it as such.
- **Then the consequential question:** for `chart_dashas`' 1,358,993 rows, how many pass through a
  Pass-2 comparison that actually executes? Read the gate. If Pass 2 runs only for
  `CANONICAL_CHART_ID`, quantify: how many rows belong to the native chart vs. every other chart.
  **Rows whose verification path never executed are not earned, regardless of what the emit site
  looks like.**
- Report the split. **Do not change any row or tier** — this determines whether the "chart_dashas is
  earned" verdict (which shrank the exposure from ~1.7M to 392,001) survives. If it does not, say
  so plainly and give the corrected exposure number.

---

## Guardrails
- Read-only against production except the drain's tested, approved/handed-over backfill.
- No new vocab member, no CHECK migration, no tier change to the 392k in this task.
- Secrets: names only (`TAP_MCP_SERVER_URL`, `TAP_MCP_SMOKE_BEARER_TOKEN`, `TAP7_API_BASE_URL`
  remain unset, out of scope).
- Do not arm TAP-6 (needs ≥7 consecutive green days; earliest 2026-08-08).
- Branch, PR, queue merges.

## Deliverable
Prose. The `origin/main` SHA you read from. Task A: re-measured per-table counts, the tested
before/after, the grounding_score/warranty verification, G7 and MV state. Task B: the 13 `meaning`
fields quoted, and a plain yes/no on whether a member already covers the concept. Task C: whether
`divergent_flagged` can fire, and the executed-vs-skipped split for chart_dashas' 1.36M rows.

End plainly: **is the prohibited residue gone (yes/no), does the estate need a new vocabulary member
(yes/no), and does the "chart_dashas is earned" verdict still stand — and if not, what is the
corrected exposure the demotion decision must be made against.**
