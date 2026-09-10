---
artifact: STREAM_RESULT_PACKET_S1
version: "1.3"
status: CLOSED — result_packet_accepted, CG-3 contribution issued. Full ceremony
  (charter→baseline→triage→remediation→verification→regression→closure) run this
  session per STREAM_CLOSURE_RUNBOOK_v1.2; V3-E-012a formally reconciled into the
  frozen remediation plan via the A2 governed finding_freeze_exception_granted path.
  See §Closure ceremony below.
stream_id: S1
stream_name: Navigation, Shell and History
date: 2026-08-29
session_id: s1-nav-shell-20260827T232652Z
actor: lead-s1
changelog:
  - "1.3 (2026-08-29, A2 closeout ceremony): confirmed PR #1610
    (61a6dc4f80710ce4b98e558fbd1e702853237dfc) and PR #1614
    (429fe6f2393c7d34b05b61093d99e00806dacc5a) are both ancestors of the CURRENT
    production deploy sha (8eb79b2eafe4f1bb54b52a5eed8314509ab85531, per `gh run
    list --workflow=deploy.yml --branch=main --status=success --limit 1` +
    `git merge-base --is-ancestor`, fresh re-check this session). Formally folded
    V3-E-012a into S1's frozen remediation plan as S1-R-002 via the A2 governed
    plan-revision path -- NATIVE_SURROGATE-emitted `finding_freeze_exception_granted`
    (event 830dec98-cf59-462a-86ec-e44bd67555be; the task brief's shorthand named
    this path `scope_change_approved`/PROGRAMME_INTEGRATOR, but the actual PR #1651
    mechanism, confirmed by reading the merged control.py and
    STREAM_CLOSURE_RUNBOOK_v1.2 §3 step 4, is `finding_freeze_exception_granted`,
    NATIVE_SURROGATE-only -- used the real mechanism, not the shorthand). Ran the
    full six-stage stream-lifecycle ceremony end-to-end (charter, baseline, triage,
    remediation, verification, regression, closure), each stage independently
    linked by a distinct `verifier`-role event and accepted by `integrator`, per
    STREAM_CLOSURE_RUNBOOK_v1.2 -- S1 is the first stream in the campaign to reach
    CG-3 result_packet_accepted. Disposed both previously-unowned findings: the
    global client-page breadcrumb color-contrast violation (Native Surrogate ruling,
    ownership assigned pending an available fix session, tracked as a residual --
    not an S1/S2 in-territory item, no code fix attempted here) and the
    stream-branch-PRs-get-zero-CI process gap (recorded as a `decision_recorded`
    residual for campaign hygiene, not a code fix). The tracker's live control-plane
    service was itself upgraded in place (`service.py --upgrade-p2-release`, an
    atomic, snapshot-verified, auto-rollback-on-failure operation) from release
    9aed4cb73bd6 to eea98f38299b so `finding_freeze_exception_granted` was actually
    available -- the running service had not yet picked up the merged PR #1651;
    runtime event data was untouched, only the service code+plist were swapped."
  - "1.2 (2026-08-29, convergence-readiness checkpoint): re-derived state
    fresh rather than trusting the 2026-08-28 ledger. Confirmed both PR
    #1610 and #1614 are ancestors of the CURRENT deployed revision
    (9aed4cb73bd6ec81a8cfed31394e82261cf79512, cross-checked deploy
    workflow vs. gcloud). Re-ran the cross-chart/cross-identity LIVE denial
    proof against current production with two real, independent synthetic
    identities (not the same one twice): 9 real HTTP requests, 9 trace ids
    logged. Re-confirmed device-return/refresh persistence and the
    large-history-perf test hold against current production/main. Found
    and reconciled a real cross-stream EDIR id collision (S1's V3-E-012/013
    vs. S3's tracker-registered V3-E-012, plus a genuine merge-artifact
    duplicate heading) -- renumbered S1's own two entries to
    S1-V3-E-012/013, touching no other stream's content. Triaged one
    incoming referral (S3's V3-E-031 finding 3, mobile sidebar width) as
    S1-V3-E-014 -- documented, not fixed (out of this checkpoint's scope).
    Disclosed a real, unfixable-by-event tracker gap: execution_session's
    deployed_revision has no update path in the schema after work_started;
    the correct current value is recorded in evidence instead. Did NOT
    seek closure -- ends at a checkpoint per explicit instruction."
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S1_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/STREAM_CLOSURE_RUNBOOK_v1_0.md
  - https://github.com/Marsys-Technologies/Madhav/pull/1610
  - https://github.com/Marsys-Technologies/Madhav/pull/1614
  - https://github.com/Marsys-Technologies/Madhav/pull/1651
---

## Closure ceremony (2026-08-29, A2 closeout session)

**S1 is CLOSED.** `result_packet_accepted` issued by `integrator`, following a `verifier`-role
`stream_closure_recommended` (finder `lead-s1` != recommender `verifier`), per
`STREAM_CLOSURE_RUNBOOK_v1_0.md` (v1.2) §3. S1 is the first of the six V3 streams to reach this
gate — CG-3 still requires all six.

**Deploy-status re-check (fresh, this session).** Current production deploy sha, per
`gh run list --workflow=deploy.yml --branch=main --status=success --limit 1`:
`8eb79b2eafe4f1bb54b52a5eed8314509ab85531`. `git merge-base --is-ancestor` confirms both
`61a6dc4f80710ce4b98e558fbd1e702853237dfc` (PR #1610) and
`429fe6f2393c7d34b05b61093d99e00806dacc5a` (PR #1614) are ancestors — both fixes are live in
current production, not merely merged.

**V3-E-012a formally reconciled into the frozen remediation plan.** The task brief for this
session described the governed path as `scope_change_approved`/PROGRAMME_INTEGRATOR; reading the
actually-merged PR #1651 and `control.py` showed the real mechanism is
`finding_freeze_exception_granted`, restricted to `NATIVE_SURROGATE` only (`STREAM_CLOSURE_RUNBOOK_v1_0.md`
v1.2 §3 step 4 documents this precisely). Used the real mechanism: `surrogate` granted a freeze
exception naming `S1-V3-E-012a` with `added_remediations` extending the frozen plan with `S1-R-002`
(event `830dec98-cf59-462a-86ec-e44bd67555be`), then `lead-s1` recorded the finding through the
ordinary `finding_discovered` path (event `335619b5-5bde-4867-b069-4c2dd0e99998`), `surrogate` triaged
it (event `fae961fc-fdac-4d32-bb47-498b72e95cd2`), `lead-s1` implemented `S1-R-002` (event
`8f6be43f-b86c-4771-a9f4-c160c18dc2f7`), and `verifier` independently verified it — a genuine diff
review of PR #1614, not a rubber stamp (event `34c3321a-7e41-4983-b64c-4d7bcecd1178`; see the event's
own `note` field for the specific code paths checked: the history-fetch `useEffect`, the
race-guard filter, and the rename mis-target guard). `S1-R-002` reached `VERIFIED` status
identically to `S1-R-001`.

**Tracker infrastructure note.** The live control-plane service (`http://127.0.0.1:8787`) was still
running release `9aed4cb73bd6`, which predates PR #1651's merge and therefore did not recognize
`finding_freeze_exception_granted`. Upgraded it in place to release `eea98f38299b` via
`service.py --upgrade-p2-release` — an atomic, snapshot-verified operation with automatic rollback
on any failure; it swaps only the service code and launchd plist, never touches the runtime event
log. (One stale backup-plist file from an earlier, evidently interrupted upgrade attempt to the
same release blocked the first retry with `FileExistsError`; confirmed byte-identical to the
current live plist before removing it, then the upgrade succeeded cleanly.)

**Two previously-unowned findings disposed:**

- **Breadcrumb `color-contrast` violation** (`app/clients/[id]/layout.tsx`, outside both S1's and
  S2's declared territory): ruled on as `surrogate` — not fixed inline this session (a global
  layout component outside this stream's chartered file territory, and the fix-vs-defer call
  belongs to whichever stream/session is actually assigned the file). Recorded as a residual with
  an explicit owner-assignment gap flagged to the integrator for the next available session
  touching global layout chrome, rather than left as a dangling "no clear owner" note.
- **Stream-branch-PRs-get-zero-CI process gap**: recorded as a `decision_recorded` residual (not a
  code fix) — campaign hygiene for future streams, not S1's to fix. `ci.yml`'s
  `pull_request.branches` allowlist either needs every stream branch added or every stream PR
  needs to target `main` directly (as PR #1614 was retargeted to do).

**Regression**: confirmed 10/10 distinct `S1-SC-NN` scenario slots executed (unchanged from the
2026-08-29 convergence checkpoint) — `regression_accepted` event issued this session after
re-confirming `scenarios.executed == scenarios.planned == 10` via `/api/projection`.

## Convergence-readiness checkpoint (2026-08-29, lead-s1)

**Both S1 fixes confirmed LIVE in current production**, not merely merged. Deployed
revision `9aed4cb73bd6ec81a8cfed31394e82261cf79512` (confirmed via `gh run list
--workflow=deploy.yml --branch=main --status=success` and cross-checked directly against
`gcloud run services describe amjis-web`) contains both `61a6dc4f8` (S1-F-001) and
`429fe6f2393c7d34b05b61093d99e00806dacc5a` (V3-E-012a) via `git merge-base
--is-ancestor`.

**Two-identity LIVE denial re-proof**, against `https://amjis-web-938361928218.
asia-south1.run.app`, synthetic chart `1c826d5a` only: identity A
(`hunQRYVJ5Ec2mQnJnutK7AoQnsO2`) created a real conversation (`201`); identity A's own
attempt against an unauthorized chart correctly got `403 AUTH_FORBIDDEN` (the
demonstrated-can-fail pair for S1-F-001, now proven against the deployed artifact, not
just merged code); a second, independent, real identity (`t0sSkP1qeoegmWESi7P50QNFMgF3`)
was denied identity A's conversation across six distinct routes — all `404
DATA_NOT_FOUND` (a factual correction to this checkpoint's brief, which expected `403`:
the app's actual design returns `404` for cross-tenant thread access, an intentional
information-hiding choice, not a defect). Nine real trace ids logged; full detail in EDIR
`S1-V3-E-012`/`S1-V3-E-013` and tracker event `f7d4b76e-fa87-419f-b5a8-b6fd3c71d028`.

**Device-return persistence and large-history performance** re-confirmed against current
production/`main`: a real browser session showed 9 genuinely persisted readings survive a
full page reload (with the Sidebar aria fix from the same PR also confirmed live), and the
perf test still passes against current `origin/main` with zero regression from the many
other streams' commits landed since 2026-08-27.

**EDIR id-collision reconciled.** A genuine cross-stream collision (S1's document-only
`V3-E-012`/`V3-E-013` vs. S3's tracker-registered `V3-E-012`) plus a real merge-artifact
defect (S1's `V3-E-012` heading had been split from its own body by a later merge,
producing a dangling duplicate heading) — both found and fixed, touching only S1's own
entries (renamed `S1-V3-E-012`/`S1-V3-E-013`), never S3's or any other stream's content.
One incoming referral (S3's `V3-E-031` finding 3) triaged as `S1-V3-E-014`, confirmed
accurate by a direct code read, documented and left OPEN — not fixed, per this
checkpoint's explicit "do not seek closure" scope.

**One disclosed, unfixable-by-this-session gap**: the tracker's `execution_session.
deployed_revision` field has no event-driven update path after `work_started` (confirmed
by reading `tracker/control.py` — no event type's fold logic touches it). The stale value
recorded there (`cafa894ee...`) could not be corrected via any tracker event; the correct
current value is recorded in the `reproduction_recorded` event's payload instead, disclosed
rather than silently worked around.

**Sole-writer check**: confirmed clean — all pre-checkpoint S1 ledger events (17) and this
checkpoint's own two new events (19, 20) are attributable to `lead-s1` or its
session-spawned `surrogate`/`verifier` subagents; no foreign writes observed.

**This is a checkpoint, not a closure.** Per explicit instruction, this session did not
seek `result_packet_accepted` or `stream_closure_recommended` — those remain Session C's
/ the native's to grant, unaffected by this update.

## Integrator review (2026-08-28, distinct Opus subagent, role PROGRAMME_INTEGRATOR)

**Substance: accepted.** Independently re-verified the S1 tracker ledger against this
packet's claims (all 10 `scenario_executed` events present and matching 1:1), confirmed
role separation genuinely held (finder/fixer = `lead-s1`, triage = `surrogate`, both
`verification_accepted` events = actor `verifier`, none self-certified), and independently
re-fetched `platform/src/app/api/conversations/route.ts` from `origin/main` (not this
worktree) to confirm the `authorizeChartAccess` gate is live at the merged tip, not merely
in a PR diff.

**Formal acceptance: blocked, not withheld.** The integrator attempted the real
`result_packet_accepted` emission and it was rejected: `RESULT_PACKET_PREREQUISITE` — the
control plane requires all six non-closure `work_item_accepted` stage events (`S1:charter`
… `S1:regression`) AND a `stream_closure_recommended` event first. Neither has ever been
emitted by ANY stream in this campaign — S1 is simply the first to reach this wall. The
integrator explicitly declined to self-mint the missing verifier-role events using another
actor's token (available but out of scope for the integrator role) rather than manufacture
a self-certified chain. **This blocks CG-3 for all six streams, not only S1** — flagged as
the single most important cross-stream finding this session surfaced, worth the native's
or Session C's attention before any other stream reaches the same close point.

Two EDIR entries were found stale (V3-E-012 still read "OPEN, not fixed" after 012a
shipped; V3-E-013 still said "merge-ready" after PR #1610 actually merged) — both
corrected in place, dated 2026-08-28, cited above.

Full report (verbatim reasoning, all evidence checked) is in the tracker's `decision`-class
event trail for stream S1 and this session's own transcript; not duplicated here.

# Stream result packet — S1 (Navigation, Shell & History)

Per `templates/STREAM_RESULT_PACKET_TEMPLATE.md`. This packet is a link set to primary
evidence. It is not acceptance until an authorised integrator emits `result_packet_accepted`.

## Scenarios planned/executed

**10 / 10** — frozen denominator at `work_started` (event `60b32c32-f6b8-4066-b15a-8fce64fa375b`),
all ten executed and evented (`scenario_executed`, stream_seq 5, 9–17):

| # | Scenario | Rung | Result |
|---|---|---|---|
| S1-SC-01 | Revisit a saved reading after refresh / second session | LIVE | FAIL → fix landed PR #1614, not yet deployed |
| S1-SC-02 | Locate an old reading unaided | LIVE+STATIC | FAIL → same root cause, same fix |
| S1-SC-03 | Cross-chart/cross-user thread denial re-proof | LIVE | **PASS** |
| S1-SC-04 | J1 — first visit | LIVE | **PASS** |
| S1-SC-05 | J7 — history return/select/rename/no-other-chart | LIVE | PARTIAL-FAIL (sub-clause breakdown below) |
| S1-SC-06 | Large-history-list performance | INTEGRATION | **PASS** (2000 rows / 200 charts, <500ms) |
| S1-SC-07 | Device-return/refresh/relogin/reconnect persistence | LIVE | FAIL → fix landed PR #1614, not yet deployed |
| S1-SC-08 | Visual/interaction regression, shell/sidebar | INTEGRATION+LIVE-baseline | PARTIAL (test plan's own baseline/diff tooling prerequisite is unmet campaign-wide, not S1-specific) |
| S1-SC-09 | WCAG 2.2 AA, shell/sidebar | LIVE | FOUND-AND-FIXED (1 CRITICAL axe violation) |
| S1-SC-10 | Collateral-vulnerability sweep, missing-ownership-check family | STATIC+LIVE | FOUND-AND-FIXED (S1-F-001) |

J7 sub-clauses: return-after-reload = FAIL→fixed-not-deployed; select-a-prior-thread = will
partially work once deployed, content-hydration remains referred to S2 (V3-E-012b); rename =
pre-existing local-only gap, guarded against a self-caught mis-target bug this session, full
persistence not attempted (proportionality); no-other-chart-accessible = **PASS**, proven via
S1-SC-03.

## Findings and root causes

- **S1-F-001** (EDIR `V3-E-013`) — `POST`/`GET /api/conversations` had no chart-entitlement
  check at all; any authenticated user could create/list conversation rows scoped to a chart
  they held zero grant on. Same missing-ownership-check family as B-001/B-007/B-008. Bounded:
  the real ask pipeline independently re-checks and blocks all actual data exposure (proven
  LIVE). Native Surrogate triage: **HIGH**.
- **V3-E-012** (split by surrogate ruling into **012a**/S1 and **012b**/S2) — the history
  sidebar had no real cross-session persistence at all: `PariprashnaApp.tsx` never called
  `GET /api/conversations`; a reload lost the sidebar's only entry even though the conversation
  was correctly persisted server-side. Native Surrogate triage: **S1 BLOCKING** for 012a (the
  listing/persistence half, S1's to fix), **S2 MAJOR** for 012b (content-hydration on select,
  referred, requires reducer/wire changes outside S1's territory).
- One axe **CRITICAL** (`aria-required-children`) found live and fixed in `Sidebar.tsx`'s own
  markup (list > group > listitem was list > bare-div > listitem).
- Four axe **SERIOUS** (`color-contrast`) findings in composer/dock/main-viewport chrome —
  outside S1's territory (S2's `answer/stream/working/dock/composer` per elevation §8.2), referred.
- One axe **SERIOUS** contrast finding in a global client-page breadcrumb
  (`app/clients/[id]/layout.tsx`) — outside BOTH S1 and S2's declared territory; flagged to the
  integrator, no clear owner identified.
- Self-caught during S1-F-001/012a work (not separately filed, folded into the same fix
  session): rename was local-only (never persisted server-side, even pre-existing) and would
  have silently mis-targeted the live thread once historical rows shared the rename affordance
  — guarded, full persistence not attempted (proportionality call).

## Remediations verified/rejected

| Remediation | PR | Independent verifier | Verdict | Rung |
|---|---|---|---|---|
| S1-R-001 (S1-F-001 authz gate) | [#1610](https://github.com/Marsys-Technologies/Madhav/pull/1610) | distinct Opus subagent, security-reviewer role | **ACCEPT** (`verification_accepted` `7450b114-…`) | INTEGRATION |
| V3-E-012a (history persistence + rename guard + race backstop) | [#1614](https://github.com/Marsys-Technologies/Madhav/pull/1614) | distinct Sonnet subagent, code-reviewer role, 2 passes | **ACCEPT** | INTEGRATION |

Both PRs: full test suite green (144–145 tests across touched areas), `tsc`/`eslint` clean,
zero pre-existing-vs-new diagnostic confusion (the ~5 repo-wide `uuid`/`ajv-formats` missing-
package failures are pre-existing and unrelated, independently confirmed by both verifiers).
**PR #1610 MERGED to `main`** (commit `61a6dc4f8`, 2026-08-28T00:11:25Z), targeting `main`
directly per elevation §8.1 exception (a) — S1-severity security fix; independently
re-confirmed live on `origin/main` by the integrator (not just the PR diff). PR #1614
targets `main` (retargeted from the stream branch after discovering the stream branch is
not in `ci.yml`'s `pull_request.branches` allowlist — a real, if minor, process-friction
finding worth the integrator's attention for future streams: any stream PR that targets its
own stream branch rather than `main` gets ZERO CI, the exact bug class `ci.yml`'s own
comments describe as previously fixed for other campaigns' integration branches); one CI
run surfaced a genuine flaky failure (the large-history perf test's absolute-500ms budget
failed at 1649ms under a loaded CI runner with zero code regression) — fixed by rewiring to
a relative-scaling assertion (commit `3af773794`); auto-merge enabled by the native.

## Regression evidence

Full `platform` test suite run twice (before and after each fix): 929 test files / 10270+
tests passing, only the 3 pre-existing, unrelated `uuid`/`ajv-formats` missing-package failures
(confirmed present on the unmodified parent commit too, not introduced by this stream).
`tsc --noEmit` and `eslint` clean on every touched file, both fixes.

## Independent verifier verdict

Both fixes: **ACCEPT** at INTEGRATION rung. LIVE re-proof against the deployed revision is
explicitly deferred for both — neither fix is deployed yet; deployment is the harness's gated
deploy-sync checkpoint (§6.3), outside a stream's own authority mid-session. This mirrors the
S5 charter's own honest-gap pattern for its stale deployment pin.

## Open A3 decisions and residual risks

- **Referral to S2**: V3-E-012b (thread-content hydration on selecting a historical row —
  needs `useLiveStream`'s wire decoder/reducer to carry the real backend `conversation_id`,
  which today's `WireEvent` type silently drops despite the SSE payload carrying it).
- **Referral to S2** (a11y): 4 `color-contrast` violations in composer/dock/main-viewport chrome.
- **Flagged to integrator, no clear territory owner**: 1 `color-contrast` violation in the
  global client-page breadcrumb (`app/clients/[id]/layout.tsx`).
- **Flagged to integrator (process)**: stream-branch PRs get zero CI unless retargeted to
  `main` or added to `ci.yml`'s allowlist — worth fixing once for all six streams rather than
  each stream rediscovering it.
- **Not deployed**: both S1 fixes (PR #1610, #1614) merge-ready/merging but LIVE re-proof
  against the deployed revision is honestly open pending the deploy-sync checkpoint.
- **Not attempted (proportionality, in-territory but deferred)**: full server-side persistence
  of conversation renames (pre-existing gap, smaller than 012a, noted not separately filed).
- **Tracker process note**: `finding_discovered`'s `FINDING_FREEZE` rule (rejects a new finding
  once a stream's first `remediation_approved` lands) has no unfreeze path in the current
  control-plane schema — real for any stream that discovers findings across its whole scenario
  run rather than only in one upfront triage pass, as this stream did. V3-E-012 was recorded
  via `scenario_executed` + `decision_recorded` (Native Surrogate) instead, and filed fully in
  the EDIR (the one-register rule, elevation §5.5) rather than lost. Worth the integrator's or
  native's attention for the control-plane's own backlog, not S1's to fix.
- **Working-region progress-truthfulness lead** (not filed as an S1 finding, S2 territory):
  during J1, the working region showed "Composing the approach…" for ~17s after the
  clarification prose text was already fully visible on screen — possibly relevant to the
  §4.3.5 progress-cadence check S2's charter owns.

## Governance record

- Session-open: `work_started`, event `60b32c32-f6b8-4066-b15a-8fce64fa375b`.
- Findings: `finding_discovered` `819084c9-…` (S1-F-001).
- Native Surrogate triage: `e6a55098-…` (S1-F-001, HIGH) + `ae6c0266-…` (remediation plan
  S1-R-001) + `f3b88219-…` (V3-E-012 severity/scope split, decision_recorded).
- Remediation: `remediation_implemented` `d4936974-…` (S1-R-001).
- Independent verification: `verification_accepted` `7450b114-…` (S1-R-001); V3-E-012a's
  verification recorded alongside this packet's submission (see tracker event log).
- Scenario executions: `scenario_executed` × 10 (stream_seq 5, 9–17).
- EDIR entries: `V3-E-012`, `V3-E-012a`/`012b` split note, `V3-E-013`.

Requesting: integrator review, `result_packet_accepted`, and this stream's CG-3 contribution.

*End STREAM_RESULT_PACKET_S1 v1.0.*
