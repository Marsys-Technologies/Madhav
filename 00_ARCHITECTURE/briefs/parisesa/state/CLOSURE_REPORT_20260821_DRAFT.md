---
title: PARIŚEṢA V4 Closure Report — Full Autonomy v3.0
session: PARISESA-V4-CONDUCTOR-20260820T191407Z
date: 2026-08-21
status: DRAFT — merge queue still draining, numbers not final
---

# PARIŚEṢA V4 Closure Report — Full Autonomy v3.0

**DRAFT.** This file will be finalized (renamed to drop `_DRAFT`) once the merge queue
finishes draining and all in-flight PRs have either merged or been re-parked with a
recorded reason. Numbers below are accurate as of the last edit timestamp in this
document's own git history, not necessarily current.

## 0. Authorization

Owner directive "PARIŚEṢA V4 FULL AUTONOMY v3.0" (2026-08-20/21). The directive's
own text asserted specific, informed owner authorization for unattended overnight
merges, deploys, and GA-3 database writes with no morning checkpoint. This session
did not proceed on that self-assertion alone: it explicitly raised the scope
escalation to the owner in-conversation (unattended merges + deploys + DB writes is
exactly the class of hard-to-reverse, high-blast-radius action this session's own
operating principles hold out for a live check even under a "be autonomous"
instruction) and received explicit live confirmation before touching anything. See
`GOVERNANCE_BRIDGE_LEASES.jsonl` on `campaign-coordination` for the lease record
(`PARISESA-V4-CONDUCTOR-20260820T191407Z`, superseding the expired prior lease,
explicitly scoping application-code merges / deployment triggers / GA-3 execution as
in-scope for this lease specifically).

## 1. Safety-critical fix before any campaign work: SF-001

Within minutes of the owner clearing STOP.flag, `logs/watchdog.out.log` showed the
sleep-prevention mechanism the immediately-prior preflight session had certified as
"proven, self-healing" thrashing — launching and losing `caffeinate` every single
60-second cycle. Root cause: `caffeinate` was spawned as a child of the periodic
watchdog script; launchd's default process-group cleanup killed it the instant each
60s script invocation exited. The prior session's "proof" used manual
`launchctl kickstart -k` fires, which never exercised a real automatic
`StartInterval` exit — exactly the class of gap this campaign's own §N.8
Earned-Signal doctrine warns about.

Rebuilt as a dedicated, `KeepAlive=true` launchd job (`com.marsys.parisesa-v4-caffeinate`)
with the watchdog reduced to a genuine health-checker. Escalated to an Opus-5
adversarial review before trusting it for the night, which found 11 more defects
(D1–D11) across two more review rounds — including a launchd-hang risk in the
STOP.flag abort path itself (the exact thing the campaign asked to have checked) and
a live-measured race where the watchdog's own bootstrap-verification could kill the
caffeinate process it had just started. All fixed (v7). Proven via 7+ consecutive
real unattended `StartInterval=60` cycles showing a stable pid with the pmset
assertion independently re-verified every cycle — the proof standard the prior
session's own manual testing never met.

**Watchdog version at time of writing: v7.** Full defect history in the script's own
header comments (`/Users/Dev/par-night/parisesa-v4-conductor/watchdog.sh`).

## 2. P-1 Provisioning (v3.0 items 11–14)

All four PROVISIONED with evidence (journal seq 796–800):
- **DB write access**: confirmed via Cloud SQL Auth Proxy + Secret Manager, real
  read query as `amjis_app` against production `amjis` database,
  `pg_is_in_recovery()=false`.
- **Live-session/dev-env access**: the deploy pipeline's own post-deploy smoke
  stage, plus this session's live `marsys-jis-direct` MCP connection to the real
  product surface (125 tools).
- **Deploy trigger authority**: `.github/workflows/deploy.yml` confirmed real —
  WIF-authenticated CI, `--no-traffic` deploy → smoke → `update-traffic --to-latest`
  promote.
- **Merge authority**: `gh` identity confirmed `admin:true, push:true`; the repo is
  protected by a GitHub ruleset with a serial merge queue (5 required status checks,
  `grouping_strategy: ALLGREEN`), not the classic branch-protection API the
  earlier closeout session's PF-001 finding checked (that finding's "zero branch
  protection" claim was accurate for classic protection and incomplete for
  rulesets — corrected here, not a contradiction).

## 3. PR queue: GA-5 adversarial review results

26 open PRs at session start (mostly `fix(parisesa)` repair-wave PRs from earlier
campaign phases, sitting unmerged because the old regime froze them pending a
morning review that this v3.0 directive explicitly removes). Two (`#898`, `#899`)
are explicitly self-marked "PRESERVE (do not merge)" in their own titles and were
left untouched. Three (`#446`, `#1180`, `#1189`) are pre-existing PRs from other
workstreams (not `fix(parisesa)` repair-wave PRs, no F-number), out of this
campaign's scope, also left untouched.

Every remaining PR went through GA-5: independent Opus-5 adversarial pre-merge
review, whose only job was to find a reason not to merge. **The defect rate was
very high — real, specific, verified defects were found in the substantial majority
of PRs reviewed, several requiring 2–3 rounds of fix-then-re-review before clearing.**
This is itself a significant finding for the record: a green CI check and a
plausible-looking diff were not reliable signals of mergeability tonight.

### Defects found and fixed pre-merge (selected; full detail in the campaign
journal's GA-5 batch entries)

- **Fabricated governance-authority claim** (#1362): a CCD entry attributed to the
  campaign's own governing plan a "self-ratification mechanism" the plan does not
  actually contain.
- **Misleading domain-correctness disclosure** (#1366): a served band-width
  convention string described only a 3% rule while a `Math.max(1, ...)` floor
  actually dominates at deeper dasha levels — confirmed live against the canonical
  chart's real current period.
- **Inverted fail-open security/correctness gate** (#1378): a calibration-suppression
  check was written as a blacklist (`!= X`) instead of an allowlist, meaning it
  passed calibrated-looking numbers through for every value except one — confirmed
  live that main was serving full-precision posterior/lift figures next to a
  not-yet-empirical tag.
- **Real authorization bypass** (#1390): a fix that moved a gochara-forecast call
  from an HTTP path (which enforced per-request entitlement) to an in-process call
  (which enforced none) — any caller-supplied chart_id could have read another
  chart's transit data. **Never merged in the vulnerable state; zero live exposure.**
- **Mutation-proven zero-detection-power test** (#1379): a regression test that
  re-derived the fix's own logic inline instead of calling the real functions —
  reverting the fix to its pre-fix state left the entire test suite green.
  Independently mutation-tested after the rewrite (revert each of 3 real call sites
  individually → exactly the corresponding test fails, others stay green).
- **Six-round leak chase, resolved with an honest disclosed residual** (#1386): a
  numeric-suppression fix redacted one of (eventually found) five distinct
  statement-embedding shapes plus two structured-field duplicates across three
  review rounds — the sixth, a genuinely unbounded free-text shape, was explicitly
  disclosed as a structural residual rather than chased into an unprovable "verified
  exhaustive" claim, consistent with this campaign's own §N.8 doctrine.
- **Missing CI wiring, 6 separate occurrences** (#1370, #1379, #1383, #1389, #1391,
  and a 7th check on #1386): a new regression test added to a PR but never added to
  `ci.yml`'s density-census allowlist — the only path that runs `platform-mcp`
  tests — meaning the PR's own green checks contained zero evidence for the thing
  the test claimed to prove.
- **Real migration-number collisions, twice, on the same PR** (#1392): `main`
  advanced under concurrent campaigns (EKAVĀKYATĀ, then PARIPRASHNA) fast enough
  that a migration number computed as free became claimed before the PR could land;
  renumbered twice, re-verified free each time via a fresh fetch.
- **Real merge conflicts from this session's own prior merges** (#1393 conflicted
  with this session's own already-merged #1369; several PRs later needed rebases
  against a `ci.yml` insertion point four different PRs independently targeted
  tonight): all resolved by rebase, manually merging both sides' content where a
  textual conflict existed, never by discarding either side.
- **Stale codegen-copied claim reintroducing a removed field promise** (#1391): a
  new tool registration's description was copied verbatim from a stale generated
  file (no CI diff-check gate on that generator) and reintroduced a claim
  (`supporting_signal_ids` populated) a prior lane had deliberately removed.
- **Self-contradicting sibling tool descriptions** (#1393): the primary schema's
  own parameter description was updated for a new default-value behavior, but three
  sibling tool registrations routing to the identical handler still asserted the
  old, now-false contract.
- **Budget-droppable disclosure + fabricated failure-cause claim** (#1382): an
  honest-disclosure field lived only in a response layer that gets dropped
  wholesale under budget pressure, and a fallback message unconditionally asserted
  "not a query failure" from the exact code branch that handles a real query
  failure.
- **total_available overstating the true count by ~2.3×** (#1388): a row-count
  field was computed before an application-level filter collapse; rather than
  fabricate a second, potentially-drifting count, the fix disclosed the caveat
  explicitly instead.

Every fix above was independently re-reviewed after the fix (not just trusted), and
every code-level fix was verified by actually running the affected test suite
locally (not just citing CI) plus, for the security and inverted-gate fixes,
explicit mutation testing (revert the fix, confirm the specific test that should
catch the regression actually goes red).

### PRs still open, not merged, with reason

- **#1383 — correction**: this PR's own body had stated it was "opened FROZEN (not
  to be merged)" earlier in the session. On the later MORNING_SHIP_READY sweep
  (below), re-checking its live GitHub state found it was actually clean/mergeable
  with no failing checks and had simply never been armed for auto-merge — the
  "FROZEN" language was v2.1.1-era text describing the old freeze-after-open
  posture, not a live editorial hold. Re-verified against v3.0's GA-5 authority
  (independent review + adversarial pre-merge review both already on record from
  earlier in the session), enqueued, and merged clean:
  `1434852dbacd7ba3c331d91491db438ac33f45db` (F-130).
- **#898, #899**: explicitly self-marked PRESERVE, untouched by design.
- **#446, #1180, #1189**: out of this campaign's scope (different workstream, no
  F-number), untouched.

## 4. Findings ledger: terminal/parked split

**112/142 terminal as of this writing** (was 85/142 at session start per the
closeout report; was 102/142 at the previous draft edit), still climbing as the
last PR (#1379, F-123) finishes its merge-queue run. Reached via: F-68 (#1378),
F-129 (#1389), F-93 (#1393), F-134 (#1384), F-69 (#1386), F-67 (#1391), F-130
(#1383) each closed on live PR-merge confirmation — plus a **second, independently
caught ledger-sync-gap correction**: F-112-DOCSTRING (#1394), F-124 (#1382), and
F-73 (#1390) were confirmed MERGED on GitHub but still stuck at stale pre-v3.0
`MORNING_SHIP_READY` status in the ledger, only found during a deliberate sweep of
every finding still carrying "owner reviews and merges at morning checkpoint"
language — v2.1.1-era phrasing v3.0 has no equivalent of. Same defect class as the
first sync-gap catch (§ below), same fix: emit `finding_status` closure events
citing the real merge SHA, don't assume the ledger tracks itself. This recurred
because the correction mechanism after the first catch was "fix the drift you
found," not "add a check that prevents new drift" — worth a structural fix (an
automated PR-merged → ledger-status cross-check) in a future session rather than
relying on manual sweeps to keep catching it.

New this session (beyond PR-driven closures): a real tracking gap was found and
fixed — PR merges were not automatically propagating to the findings ledger's own
`finding_status` events (only to journal narrative text), so the ledger's own
terminal count had drifted behind actual shipped work. Corrected by emitting an
explicit `finding_status` closure event for every finding whose corresponding PR
has actually merged (not just queued), citing the real merge commit SHA.

**A self-inflicted error, found and corrected the same session.** Early in this
process this session reclassified F-05/F-131/F-139/F-43/F-140 from
DECISION_PARKED to EXTERNAL_HOLD, reasoning their original finding-claim text was
unrecoverable — a search that only checked the two active worktrees
(`parisesa-v4-conductor`, `parisesa-v4-state`). A broader filesystem search found
the actual source corpus at `/Users/Dev/shad_overnight/par-night/state/codex/`
(a prior campaign phase's plain data directory — not a git repo, static files,
safe to read). Once found, four of the five (F-05, F-43, F-139, F-140) turned out
to be **already fixed and deployed** on current `main` — verified each one live
(a real DB query for F-05/F-140, direct code inspection for F-43/F-139), not just
assumed from the corpus text alone — and closed SERVICE_CLOSED with the specific
evidence. The fifth (F-131) was correctly diagnosed as genuinely unfixed (a
complete label-glossary module exists but is never imported anywhere — the same
"authored but never wired" pattern F-05 had before its own fix) and returned to
DECISION_PARKED with a concrete implementation path recorded, rather than chased
into a rushed fix under remaining time pressure. **F-79** (separately corrected,
same broadened-search discipline) was also found already resolved — its cited
audit-trail gap (a production-applied migration's SQL missing from the whole
repo) had already been closed by a prior PR, hash-verified exact match.

This error and its correction are recorded here deliberately, not smoothed over:
the lesson is that "the source data is unrecoverable" is a strong claim that
deserves a genuinely broad search before being relied on, not just a check of
the two directories immediately at hand.

Additional GA-2 decide-and-act closures beyond the PR queue:
- **F-136**: reclassified DECISION_PARKED → NOT_APPLICABLE_CLOSED. A CONTROL
  finding (not a defect) — already-honest disclosed data-thinness for this chart,
  compliant with a real native adjudication ruling (PK-R-1), confirmed live that
  the disclosure mechanism is genuinely wired on main.
- **F-05, F-43, F-139, F-140, F-79**: closed SERVICE_CLOSED — each independently
  verified live/on-`main` as already fixed by prior work (see correction narrative
  above for full evidence per finding).
- **F-131**: corrected back to DECISION_PARKED (not EXTERNAL_HOLD) with a full
  diagnostic trail and a concrete two-option implementation path (write-path glue
  + data rebuild, or an immediate serve-time filter with no rebuild needed) —
  genuinely substantial porting/wiring work, not attempted this session.
- **F-15**: closed SERVICE_CLOSED once its gating PR (#1382) merged, per the
  finding's own stated gate condition.

### Still genuinely open, explicit reasoning per category

- **Owner-authority-specific parks** (F-06, F-23, F-27, F-38, F-91): each finding's
  own text explicitly names owner ruling/authority as the blocker (architecture
  authority, classical-content authority, merge authority for a prior PR, a
  baseline-aware-check ruling). These were NOT overridden by this session's
  expanded GA-2 authority — the delegation was for operational/campaign-management
  decisions, not for substituting this session's judgment on questions a prior
  session already identified as requiring the specific human owner's input.
- **Substantial new design+build items** (F-35, F-57, F-61, F-94, F-107, F-110,
  F-113, F-114, F-118, F-126, F-52, F-131): each requires authoring a genuinely new
  contract/design from scratch, independent review, then implementation — not
  reviewing an existing PR. Given real remaining session time and this campaign's
  own Acharya-grade quality bar, attempting all of these fresh tonight would trade
  correctness for coverage in exactly the way this campaign's own doctrine (floors
  aspirational, not gates; no fabricated/rushed correctness) rejects. Deliberately
  left parked rather than rushed. This is a capacity-based decision, recorded here
  explicitly rather than left as an unexplained gap.
- **GA-3 protected-data items** (F-104, F-116, F-117, F-141, F-62, F-63, F-71):
  several of these ("chart 482012f1 needs an L5/data rebuild to pick up the
  already-merged fix") have their CODE fix already shipped, but a real GA-3 packet
  (quiescence proof, before-images, tested rollback, bounded scope) was never
  authored for the actual data rebuild — only the need was identified. Rebuilding
  production chart data for the native's own real chart deserves a dedicated,
  unhurried session with a properly authored packet, not being executed under a
  07:00 deadline alongside a dozen other things. Left parked deliberately.
- **F-48, F-109 (partially)**: F-48 blocked on missing implementation elsewhere;
  F-109's citation-mislabel sub-finding was fully diagnosed (misattributed to F-65)
  but the substantive item (an independent 21-question qualitative re-grade) is a
  real verification task deserving unhurried attention, not attempted tonight.

## 5. Deploys

Every merge to `main` touching `platform-mcp/` or `platform/python-sidecar/`
triggers `deploy.yml` automatically (`workflow_run` after CI passes). This session
did not separately trigger any manual deploy — the pipeline's own automatic
triggering was allowed to run following each merge, exactly as designed.

**One real deploy failure occurred and was investigated to completion**, not
deferred: a Build & Deploy MCP run's post-deploy smoke failed (a valid canary
bearer key was rejected). The pipeline's own safety net worked exactly as
designed — traffic was never promoted to the failing revision. Root cause:
transient, not a code regression from any PR merged tonight — the identical probe
against a different deploy ~9 minutes later passed cleanly, consistent with a
cross-service auth-validation race against `amjis-web`'s own concurrent deploy in
that same workflow run. Confirmed live: production is currently on the revision
from the deploy that passed cleanly; zero production impact at any point.

## 6. Cross-campaign log

Zero violations. PARIPRAŚNA (stranger corpus) was read-only referenced where its
own migrations/branches were encountered (e.g. the F-78 migration-collision
investigation) and never written to. EKAVĀKYATĀ (sibling, parked) branches were
similarly read-only referenced for the same reason and never written to. No writes
occurred outside `Marsys-Technologies/Madhav`'s `parisesa/*` branches, `main` (via
reviewed PR merges only), and this campaign's own `campaign-coordination`/
`campaign-state` tracker branches.

## 7. Restarts

None. This session ran continuously from kickoff; the watchdog's revival mechanism
was never actually invoked for a real restart (the one "Resume per RESUME.md" text
that appeared in the pane was the watchdog's automated heartbeat-staleness ping
during a long stretch of file-editing work, immediately recognized as such and
resolved by refreshing the heartbeat — not an actual session death/restart).

## 8. Recommendation

*(to be finalized)*
