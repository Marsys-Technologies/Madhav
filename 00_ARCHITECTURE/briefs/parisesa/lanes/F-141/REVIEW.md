---
lane: F-141
stream: S6_ADHARA
stage: R (REVIEW) — Stage R second pass
reviewer: VERIFIER (author != reviewer — DIAGNOSIS.md/SPEC.md authored by ADHARA-LEAD)
reviewed_artifact: PR #1312, head 6ea6dd4d3
verdict: COMPLETE (as a disclosure-only remediation, not a defect fix — see scope note)
---

# F-141 — REVIEW (Stage R)

## Scope note

This lane is explicitly NOT a code-defect fix. PRATINIDHI ruled (PAR-R-9 — independently
re-fetched and read directly from `origin/par/pratinidhi-ledger`, not taken on the corpus's
word) that no DB write is authorized, and rescoped F-141 to: widen and wire a real detector,
disclose the actual anomaly (5 rows, not 1; a wider overstatement than first measured), and
leave the still-untraced mechanism honestly open. Reviewing against that rescoped bar, not
against "is the underlying row fixed" — it is explicitly, correctly, not.

## Independent verification (all re-derived, not inherited)

1. **PAR-R-9 is genuine.** Fetched `origin/par/pratinidhi-ledger` fresh, found the actual
   ruling text: "NO DB WRITE. Both options refused; the question was malformed" — matches
   what DIAGNOSIS.md/SPEC.md cite.
2. **The widened SQL predicate is correct and matches live production, checked myself via
   direct read-only query** (`mcp__postgres__query`), not by trusting the "verified this
   session" claim in either document:
   ```sql
   SELECT count(*) FROM asset_throughput WHERE state IN ('lit', 'mature') AND last_error IS NOT NULL AND last_error != ''
   ```
   → `5`, exactly matching the claim. Row-level query confirms the exact 5 rows named:
   `ka_kshetra`/`482012f1` plus four `chart_id IS NULL` singletons (`bg_reference`,
   `bg_transit_rules`, `bg_transit_engine`, `bg_ghatana`), all currently `state='lit'`
   (confirms the claim that widening to include `'mature'` doesn't change today's PASS/FAIL —
   it's a forward-looking correctness fix, not currently load-bearing). `bg_transit_rules`
   and `bg_transit_engine` share `last_built_at` within 44ms of each other — consistent with
   the diagnosis's "likely one failed build event, not two."
3. **`evidence/F-141_pre_write.json` matches** the live query, independently confirmed.
4. **The actual PR diff matches what SPEC.md describes**, pulled via `gh pr diff 1312`:
   `_check_f102`'s SQL widened exactly as claimed, `CHEAP_IDS` gains `F-102`, docstring
   correctly documents the CI-wiring gap (`ekv_controls.py` called by zero
   `.github/workflows/*` files) as a separate, real finding from the query-scope fix.
5. **CI**: all 5 required status checks (per the branch ruleset) pass. Failing non-required
   checks (`D-01a`, `D-01c`, `D-01d`, `D-08`) are the same set already independently
   confirmed pre-existing-red on `origin/main`'s own tip during F-62's review this session —
   re-applies here since this diff (one Python governance file) shares no surface with any
   of those checks' subject matter. No new regression. `mergeable: MERGEABLE`.

## The seven questions

**1. Mechanism vs symptom** — mechanism, and honestly bounded. The root cause named is a
compound one (detector scoped too narrow + never wired into CI) and the fix closes both
without overclaiming the underlying anomaly is understood.

**2. Sub-claims mapped** — yes. SPEC.md §7's table maps all four of PAR-R-9's rescoped
remediation items (detector / disclosure / continued trace / pre-write snapshot) to a real
status each — including marking item 3 (mechanism trace) as "attempted, inconclusive,
honestly open" rather than padding it to look closed. That's the right call, not a gap.

**3. Exit test genuinely fails/reflects reality** — not a red→green unit test by design (a
live-data detector, per SPEC.md's own reasoning, which matches VERIFIER's PAR-R-10 standing
rule against treating in-worktree assertions as live evidence for data-layer claims).
Independently ran the actual live query myself (not the script, no DB-URL in this
environment either, same constraint SPEC.md discloses) — confirmed `FAIL, count=5` is the
honest, correct, currently-true result.

**4. Sibling sites** — correctly scoped as not applicable in the usual code-defect sense;
the "sibling" question here is really "is there a second mechanism," and DIAGNOSIS.md/
SPEC.md honestly report that trace as inconclusive rather than asserting closure.

**5. Recurrence guard** — real, and its own docstring names its own limitation plainly:
widening + cheap-subset-wiring is the guard for the *detection* gap; it explicitly does not
and cannot guard the underlying 5-row anomaly without DB-write authorization nobody has
given. The CI-wiring gap (function exists, nothing calls it) is itself flagged as a
separate, still-open item for SENTINEL/conductor, not silently left implicit.

**6. Regression risk** — none found. Diff is confined to one Python governance script;
independently confirmed all 5 required checks pass and non-required failures are
pre-existing. `platform/src/app/api/cockpit/watchdog/route.ts` — the file DIAGNOSIS.md
traced as the origin of the `last_error` text — is correctly NOT touched (traced and found
already-correct; the stale row predates the current code, not caused by it).

**7. Unverified assumption vs read code** — the one place I'd flag as worth double-checking
in a future pass: SPEC.md concedes "VERIFIER or a session with real DB-URL access should
still run the actual script end-to-end before marking this LIVE." I don't have the
production `DATABASE_URL` in this environment either, but I do have direct read-only
`mcp__postgres__query` access, which I used to independently re-run the equivalent SQL
predicate directly against the live table — same data source the script itself would query,
different execution path (script vs. direct query). That's a meaningful independent check,
not a rubber stamp, but it is not literally "ran `ekv_controls.py --control F-102`" — noting
the distinction rather than overclaiming exact-command reproduction.

## Verdict: COMPLETE

As a disclosure-only remediation (not a defect fix — see scope note), this lane does exactly
what PAR-R-9 asked and no more: real detector, correctly wired, independently verified
against live production; honest disclosure matching live data exactly; the still-open
mechanism trace reported as open, not padded to look closed. No DB write attempted or
implied. Expected close state remains `PARKED-WITH-DETECTOR`, not full LIVE — that is the
correct, honest outcome for this lane, not a shortfall.
