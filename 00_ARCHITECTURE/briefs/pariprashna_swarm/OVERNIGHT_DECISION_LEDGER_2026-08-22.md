---
artifact: OVERNIGHT_DECISION_LEDGER
canonical_id: PARIPRASHNA_OVERNIGHT_DECISION_LEDGER_2026_08_22
version: 1.0
status: LIVE — append-only, written throughout the 2026-08-23 overnight run
authority: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §3.4
role: >
  Every decision the NATIVE-SURROGATE made in the native's absence during the P3+P4 combined
  overnight run, plus every conductor operational judgment worth the native's morning review.
  All entries are labelled DELEGATED-OVERNIGHT, native review pending — none is presented as
  the native's own decision. Reviewing this file IS the native's asynchronous verdict on the
  night.
---

# Overnight decision ledger — Paripraśna P3+P4, 2026-08-23

Format per §3.4: sequence · timestamp · question as asked · decision · precedent cited or
principle applied · reversibility note · the falsifier (what would change the native's mind).

---

## D-001 — 2026-08-22T21:28:50Z — CONDUCTOR (operational, not a surrogate ruling)

**Question as asked:** `tracker-health-check` reports OBSERVATORY UNHEALTHY at run open — an
unacknowledged 170s blind window (2026-08-22T20:44:27Z → 20:47:17Z). Acknowledge it and proceed,
or treat an unhealthy observatory as a run-open blocker?

**Decision:** Acknowledged via `tracker-ack-blind` and proceeded. Recorded here and in the
run-open coordination entry rather than left silent.

**Precedent / principle:** The tracker README's own §(d) makes acknowledgement an explicit
operator action, and the gap's provenance is known and benign — it is the daemon restart from
this run's own environment setup (~02:14–02:17 IST), not an unexplained observability hole. The
alternative (silently ignoring a red health check) is the failure class `tracker-health-check`
exists to prevent. Recording the acknowledgement is what keeps it honest (§N.8: a signal that
can never read false is not a signal; this one read false, correctly, and was cleared by a
named human-equivalent action, not by a self-clearing timer).

**Reversibility:** Fully reversible — the acknowledgement is a flag in
`~/.pariprashna-tracker/BLIND_WINDOW.json`; the measured gap itself is preserved in the file
and in this ledger regardless.

**Falsifier:** If the native's own review finds that the 02:14–02:17 gap was NOT the setup
restart — i.e. the daemon was down for an unexplained reason — the acknowledgement was
premature and the window needs re-investigation from `~/.pariprashna-tracker/logs/`.


---

# FULL RUN LEDGER — appended at close


## D-001 — 2026-08-22T21:32Z — CONDUCTOR (operational)

**Question as asked:** The charter's §11.4 says the pulse window records "production's HTTP status
and serving revision" every 30 minutes, and §11.4 makes the pulse log the tie-breaker: *"if the
morning report and the pulse log disagree, the pulse log wins."* But `pulse.sh` shipped with
`PROD_URL=""`, so it was recording neither. Fix the collector mid-run, or leave the night's
independent record incomplete?

**Decision:** Fixed. `PROD_URL` set to the real `amjis-web` URL and a `prod revision:` line added
(reads `status.traffic[0].revisionName`). Only the pulse loop was restarted — the sentinel was left
untouched. The log file itself was not written to, edited, or rotated by any agent; it remains
append-only and agent-free, which is the property the "agent-free" rule actually protects.

**Precedent / principle:** §11.4 states the pulse log's purpose and gives it authority over the
morning report. A tie-breaker that cannot observe the thing it arbitrates (production ≡ main — a
STOP condition, §7) is an unearned signal in exactly the §N.8 sense: it could never have read
false about production because it was never looking at production. Fixing the collector is what
makes the "agent-free record" claim mean something.

**Reversibility:** Trivially reversible — one variable and one echo line in
`/Users/Dev/pariprashna_night/pulse.sh`; the log's prior content is untouched and the gap in
coverage is this entry.

**Falsifier:** If the native intended "agent-free" to mean the *script* is frozen at launch as
well as the log, this was an overstep — the correct action then would have been to note the gap in
the morning report and leave production unobserved by the pulse. I judged an unobserving observer
to be the worse outcome on a night with a flip and a deletion in it.

---

## D-002 — 2026-08-22T21:35Z — CONDUCTOR (lane disposition)

**Question as asked:** Lane DD-19 was dispatched per the charter's §4 Wave P3-1 list. Its builder
returned with **zero diff**, reporting that DD-19 was already fixed, merged (PR #1462, migration
587), deployed, and DD-21-verified by the PARIPRASHNA-P3-PREFLIGHT-PART-E session on 2026-08-22 —
i.e. the charter's own lane list was stale by the time lanes were dispatched. Accept a
zero-diff lane close, or require the lane to produce work?

**Decision:** Accepted as **VERIFIED-ALREADY-CLOSED**, and independently re-verified by the
conductor before accepting: `pipeline_stage: 'interpretation_sets'` confirmed present on
`origin/main` at `platform/src/lib/pariprashna/interpretation/worker.ts:411`, and the DD register's
DD-19 row confirmed carrying its `CLOSED 2026-08-22 (PARIPRASHNA-P3-PREFLIGHT-PART-E session)`
addendum. The builder's live DB read (5 real `interpretation_sets` rows in `llm_usage_events`, all
with non-null `computed_cost_usd`) stands as corroborating evidence, not as the sole basis.

The builder also declined to manufacture a fresh "0 rows → N rows" demonstration, on the grounds
that producing it would require either reverting live production code to reintroduce a real defect
for demo purposes, or re-spending budget to regenerate already-documented evidence. **That was the
correct call** and is recorded here as such rather than as a shortfall.

**Precedent / principle:** §N.8 and DD-21 exist to prevent *unearned* green, not to compel
redundant work; re-deriving a proven fact at real cost would serve the ritual and not the standard.
CLAUDE.md §I: narrow-scoped over broad. The reversibility asymmetry also points here — accepting a
verified-closed lane costs nothing recoverable, while reverting production to stage a demonstration
is destructive.

**Reversibility:** Fully reversible — the lane can be reopened at any time; nothing was built,
merged, or deleted.

**Falsifier:** If the native's review finds that DD-19's Part-E close did not actually cover the
call site the charter meant (the path moved from `platform/src/lib/llm/interpretation/worker.ts` to
`platform/src/lib/pariprashna/interpretation/worker.ts` — if BOTH exist and only one is fixed, this
disposition is wrong). The conductor checked the pariprashna path and found the fix; it did not
exhaustively prove the absence of a second, still-unlogged call site under the old path. **Filed as
an open check for the morning, not claimed as verified.**

---

## FINDING F-N1 — charter lane-list staleness (process note, for the morning report)

DD-19 closed on 2026-08-22, the same day the charter was authored, and the charter's §4 lane list
was written before that close. Dispatch-time lane lists in a fast-moving register should be
reconciled against the fetched tip at run open, not trusted from the charter text. The conductor
did reconcile `PLAN.yaml`'s dependency graph at run open (§ run-open step 2) but did NOT re-check
each lane's DD-register status — that gap is what cost one builder dispatch. **Cheap fix for a
future run: a run-open reconciliation pass over every dispatched lane's register row.**

---

## FINDING F-N2 — RC-10 / NAMESPACE_COVERAGE_v2_0.md is measurably stale (candidate DD entry)

Surfaced by the P3-A builder, pending independent confirmation by a refuter.
`00_ARCHITECTURE/briefs/retrieval_residual/NAMESPACE_COVERAGE_v2_0.md` (RC-10/R-9) records
"20/23 `VIDHI_PRIMITIVES` `live_tool` names bridged + 3 deferred" against a 23-name snapshot. The
live registry has since grown to **40 distinct `live_tool` values across 60 primitives** (ṢAḌ-DARŚANA
W5's `kala_*` views among the additions). Real current coverage measured this session: **21/40
live_tools, 35/60 primitives — 19 uncovered, not 3.**

Two things make this worth a DD entry rather than a footnote. First, it is a **governance artifact
that has drifted from the thing it measures** — the GA.1 registry-disagreement failure class, which
CLAUDE.md §I B.8 names explicitly. Second, and more to the point: the builder **enumerated all 19
uncovered names and force-mapped none of them** to close the gap cosmetically. That is the correct
behaviour under §N.4's floors-are-aspirational rule and §N.7 item 6 (an honest null beats an
invented judgment) — and it is worth recording that the honest path was taken when the dishonest
one would have produced a much better-looking number.

**Not yet a DD entry — awaiting refuter confirmation.** If the refuter independently reproduces the
40/60 measurement, it files. If not, the builder's own coverage figures are in question and so is
the lane.

---

## FINDING F-N3 — a red CI run that looks like a demonstration and is not (P3-E, live)

Recorded because it is the exact failure mode the run's §N.8 discipline exists to catch, and it was
caught by reading the log rather than trusting the label.

Three runs of `Paripraśna Post-Deploy Behaviour Smoke (P3-E / PB-4 F-6)` completed `failure`. The
run JSON carried `"induce_failure_mode": true` — i.e. it *presents* as a successful
demonstrated-can-fail run. The actual content:

```
"chart_id": null, "turn_id": null, "citations_seen_informational_not_gated": 0,
FAIL ask_script_exit_zero:  ask.ts exit code = 1
FAIL turn_record_readable:  no turn record file found ... ask.ts likely never wrote one
summary: { pass: 0, fail: 2, total: 2 }
```

**`ask.ts` never completed a turn at all.** The behaviour assertions never evaluated. What went red
is the harness reporting "the probe did not run" — indistinguishable from what a bad URL or a 404
would report, and therefore evidence only that the smoke detects transport/harness failure, not
that it can detect a behavioural regression. The `induce_failure_mode` flag makes an unrelated real
failure look explained. Banking this as the lane's can-fail evidence would have put a smoke of
unknown sensitivity in front of THE FLIP and, later, the P4 deletion — both of which are gated on
its counter.

**Conductor action:** flagged to the builder before it could bank the red; required a real GREEN
first (until one exists every red is ambiguous by construction), then per-assertion-targeted reds
where the *other* assertions still pass, plus the counter-reset demonstration. Explicitly instructed
that weakening the smoke's assertions to reach green would be a §9 violation, and that **parking
P3-E with a written finding is an acceptable outcome** while an unfalsifiable green is not.

**The generalizable lesson, for the morning:** an induced-failure flag is a *claim about intent*,
not evidence about cause. A red run counts as a demonstration only when the targeted assertion
failed **and the untargeted ones passed**. A run where everything fails at once proves nothing about
which detector works.

---

## FINDING F-N4 — a migration mutated PRODUCTION with no row in the migration ledger (candidate DD entry, native attention)

**This is the finding of the night so far that most deserves the native's morning attention.**

`platform/migrations/588_remove_asset_build_protection.sql` (and its sibling
`589_drop_orphaned_protection_functions.sql`) sit **untracked** in the shared checkout, created
2026-08-23 ~02:54 IST by the environment-setup session, and 588 was **executed against the
production database via raw `psql`** rather than through `platform/scripts/migrate.ts`.

Verified directly:

```
SELECT id, filename, applied_at FROM _migrations_applied ORDER BY applied_at DESC LIMIT 3;
 446 | 587_llm_usage_events_interpretation_sets_stage.sql | 2026-08-22 03:31:21+00
 445 | 586_f152_asset_throughput_state_audit.sql          | 2026-08-22 02:29:47+00
 444 | 585_mi_gunanaka_count_sql_accretion_fix.sql        | 2026-08-22 01:16:12+00
```

**587 is the highest tracked filename. 588 is absent — yet its effect is live in production.**

**Why this matters beyond bookkeeping.** CLAUDE.md §N.4's doctrine, re-scoped by DVA Ruling 58,
names the hazard as *"migrations silently doing nothing while the deploy reports success."* This is
that hazard running in reverse: **a migration did something, to production, and nothing recorded
it.** The consequences are asymmetric and unpleasant — a future `migrate.ts` run has no way to know
588 already ran; a rebuild from the tracked ledger would produce a schema that differs from
production; and the change itself (removal of asset build protection guards) is exactly the class of
change one wants an audit trail for. The file being untracked means it is also one `git clean` away
from being unrecoverable while its effect persists.

**Scope note — deliberately not acted on tonight.** Committing, reverting, or reconciling those
files is a governance action on another session's artifacts, in a checkout that is never a build
surface (X-4), and touches production schema state. Per §3.3 it is not the surrogate's to decide and
not a lane's to perform. **Filed, not fixed.** Recommended morning action: commit the two files as-is
(preserving their applied SQL verbatim) and backfill their `_migrations_applied` rows, or explicitly
record them as out-of-band operator changes — but by the native's decision, not overnight.

---

## FINDING F-N5 — CORRECTION, recorded because the record should show the error and not only the fix

Acting on F-N4, the conductor instructed the P4-I builder to renumber its migration off 588,
believing the two migration directories shared one number space. **That premise was wrong.**
`platform/migrations/` and `platform/supabase/migrations/` are separate number spaces in practice:
`origin/main` carries **29 numbers present in both directories** (174, 223, 239, 240, 250, …), and
`migrate.ts` reads both directories while tracking by **filename**, so
`588_samiksha_digest_journal.sql` and `588_remove_asset_build_protection.sql` cannot shadow each
other. The instruction was retracted in full before the builder acted on it; P4-I's migration number
is correct as authored and its own pre-authoring check ("588 free on the live tip") was sound.

Recorded rather than quietly dropped, because a conductor's wrong instruction that a builder might
have obeyed is exactly the kind of thing an overnight run should not be able to bury. **The
reservation mechanism worked in both directions**: it surfaced F-N4's genuine hazard, and it cost
one retracted message to discover the hazard did not reach P4-I.

---

## D-003 — 2026-08-22T22:15Z — CONDUCTOR (crash-resume, operational)

**Question as asked:** The conductor session died and tmux session `prp-night` was recreated at
03:37:35 IST with a fresh Claude Code process. Ten lane worktrees, five open PRs, and an
in-flight agent roster existed from the prior session, but every in-flight agent's *result* died
with the pane. Resume from the charter's cold-start run-open sequence, or re-orient from derived
state?

**Decision:** Re-oriented from derived state, per charter §11.3 ("crash recovery is a first-class
path: on resume, first action is re-orientation … then resume the queue from derived state, never
from memory"). Executed in order: `git fetch origin` · read the pending decision ledger in full ·
enumerated all 15 worktrees with per-branch commit and dirty state · read the five open PRs' CI
status check-by-check · read the coordination lease tail · confirmed tmux session integrity (4
windows, no dead panes) · `tracker-health-check` (OBSERVATORY HEALTHY, heartbeat 28s, selftest
pass, no unacknowledged blind window).

The run-open sequence was NOT re-executed: the charter has already landed (PR #1493), the lease
courtesy entry already exists, and re-running those steps would have duplicated governance
artifacts. The one run-open item genuinely re-done is this fetch-and-verify pass, which §11.3
requires anyway.

**Ten agents were then re-dispatched**, because a crashed agent's *work* survives in its worktree
but its *verdict* does not — and no verdict may be assumed. Nothing in-flight was treated as
returned.

**Precedent / principle:** §11.3 crash-recovery path, applied literally. Also §N.8, in the
direction that matters here: an agent whose result was never observed has not passed — treating a
dispatched-but-unreturned refuter as "cleared" would be exactly an unearned signal, and four of
tonight's five open PRs are gated on refuter verdicts.

**Reversibility:** Fully reversible; re-dispatch costs budget, not correctness. The
counter-decision (trusting the prior session's unreturned verdicts) would have been irreversible
in the way that matters — merges admitted on refutations nobody read.

**Falsifier:** If the prior session's agent verdicts are recoverable from its transcript and all
returned SURVIVES, this re-dispatch was pure cost. Judged worth paying: the alternative is
admitting merges to `main` on unread adversarial reviews, on a night whose stated standard is
"never a claim without a detector that could have called it false."

---

## D-004 — 2026-08-22T22:15Z — CONDUCTOR (critical path, escalated to surrogate)

**Question as asked:** P3-E's smoke — the run's critical clock, gating both THE FLIP and the P4
deletion — has never once been green. What is the actual cause, and does it change the night?

**Finding (root cause, now precise).** CI run 32600417256 on PR #1494:

```
[ask] minting fresh session cookie for uid=probe-service-account …
[ask] fatal: SyntaxError: No number after minus sign in JSON at position 1
    at mintSessionCookie (platform/scripts/probe/ask.ts:195:22)
FAIL ask_script_exit_zero:   ask.ts exit code = 1
FAIL turn_record_readable:   no turn record file found — ask.ts likely never wrote one
```

"No number after minus sign at position 1" means the string handed to `JSON.parse` **begins with
`-`** — the signature of a raw PEM (`-----BEGIN PRIVATE KEY-----`) where a service-account JSON
object was expected. The env var is `FIREBASE_ADMIN_CREDENTIALS`.

**This confirms finding F-N3 at the level of cause, not just symptom.** The prior conductor
observed that the reds were transport failures rather than behavioural ones and refused to bank
them as §N.8 can-fail evidence. That judgment is now demonstrated correct: `ask.ts` dies before
authenticating, so no behaviour assertion has ever evaluated, in any run, red or otherwise. The
smoke's *sensitivity to a behavioural regression* remains entirely unmeasured.

**Decision:** One bounded DIAGNOSTICIAN attempt (RF-8), with the fork ruled in advance by the
NATIVE-SURROGATE rather than at the moment of discovery, so the run cannot stall on it. Explicit
standing instruction to the diagnostician: **if the only correct repair is a credential
operation, that is a §9 hard-never and a §3.3 MUST-PARK — park it, do not perform it**, and
weakening any smoke assertion to reach green is a §9 violation regardless.

**Reversibility:** The park branch is fully reversible (the native performs one credential action
in the morning and the cadence starts). The forbidden branch is not: a credential rotated
overnight by an agent is exactly the class of act §9 exists to prevent.

**Falsifier:** If the secret is well-formed and the defect is purely `ask.ts` failing to
base64-decode what it is handed, this is a small code fix and the clock starts tonight. That is
the outcome to hope for; it is not the one to assume.

**Consequence, stated plainly for the morning:** the flip's precondition 2 (green×7 on the
cadence, CI history as declarer) needs ≈4.5–5.25 hours *from the first green*. At 03:45 IST no
first green exists. **THE FLIP is very unlikely to fire before the native wakes**, and P4-E, P4-F
and the entire RETIRE train (A→B→C→D) are gated on it. The charter anticipates exactly this as
end state 4 and calls it a success. The run is being conducted toward that, not against it.

---

## FINDING F-N6 — P4-H REFUTED: the dispute does not survive the next turn (the night's most consequential catch)

**Lane P4-H, PR #1496 — merge BLOCKED on an independent refuter's verdict.** Recorded in full
because this is precisely the outcome the adversarial role exists to produce, and because the
defect it uncovered is worth more than the lane that uncovered it.

The lane's read-back leg is sound: a real throwaway Postgres, a real `psql` SELECT by a second
party using its own container and its own UUIDs, and a mutation test (the `UPDATE … jsonb_set`
replaced with a no-op returning `rowCount = 1`) that correctly turned the suite red. The detector
is real. DD-21 satisfied on that leg.

**The durability claim is false.** Two production writers replace the column wholesale —
`src/lib/persistence/conversation_writer.ts` and `src/lib/pariprashna/store/writer.ts`, both
`ON CONFLICT (id) DO UPDATE SET … metadata_json = EXCLUDED.metadata_json`, with
`const metadata = isLastAssistant ? lastAssistantMetadata : {}`. Every message is re-upserted by
id on every turn, so every message that is not the current last assistant message has its
metadata reset to `{}`. Observed end-to-end:

```
DISPUTE POST status: 200
AFTER DISPUTE      : {"feedback":{"rating":-1,"comment":"It was a layoff, not a promotion..."}}
TURN 2 verified    : true | missing: []
AFTER NEXT TURN    : {}
```

A reader disputes a reading, asks one follow-up question, and the dispute is gone — silently.
**The lane moved the silent discard; it did not remove it.**

**A fresh §N.8 instance, and a clean one.** `writeConversationMessages`' read-after-write check —
hardened by SAMĀPTI F-24 specifically to eliminate unreachable-false signals — reports
`verified: true` while performing the destruction, because it asserts *row presence*, not
*metadata preservation*. The detector measures a proxy rather than the claim. This is the exact
defect class CLAUDE.md §N.8 names, and a direct sibling of the SATYA-DĪPA no-op-completion defect.
Anyone storing out-of-band data on `conversation_messages.metadata_json` inherits it.

**Second DD-worthy finding: the JSONB sub-object convention is unsafe for out-of-band writers.**
`provenance_stamp` and `acharya_reading_receipt` are safe under this convention only because the
turn pipeline writes them *in-band* with the message. A dispute arrives *after* the turn — it is
the one payload class the convention structurally cannot protect. The lane cited those two as
precedent and copied the storage shape without the lifecycle that makes the shape safe. Given
that disputes also require history and non-folding (a thumbs-up from the only existing client
nulls a prior dispute's text; a `super_admin` overwrites a reader's dispute and re-stamps
`user_id` as their own), a dedicated table is likely the correct design.

**Third: the close claim overreached.** `useFeedback` is never invoked anywhere in the codebase
(`grep -rn "useFeedback(" src` returns only its definition), and **no client, mounted or
unmounted, can transmit a `comment` at all** — the free-text dispute field has no producer. The
charter's standard is "a dispute submitted end-to-end … on the live surface"; what was
demonstrated is an in-process route test under vitest.

**Conductor disposition (no discretion exercised — this is enforcement, not judgment):** PR #1496
does not merge tonight. Verdict posted to the PR so the record is durable and legible in the
morning. The re-scope question — whether to fix the turn writers tonight (a small, surgical
`metadata_json = conversation_messages.metadata_json || EXCLUDED.metadata_json`, but on the core
turn write path) or to park the lane and file the design finding — is a §3.3 surrogate call and
has been routed there. **Reversibility points at parking:** the filler queue means parking costs
the run nothing, while merging a false durability claim into the record is the expensive error.

**Said plainly, because it should not be buried:** the builder did real work, filed its own
residual honestly, and its honesty is what pointed the refuter at the right place. The lane
failed; the process worked.

---

## D-005 — 2026-08-22T22:25Z — CONDUCTOR (watchdog, deploy-invariant verification)

**Question as asked:** Branch pushes are appearing in the `Deploy to Cloud Run` workflow's run
history (commits `535caa34c`, `e6bfd85f4` — both lane branches, not `main`). Production ≡ main is
a STOP condition (§7). Is the invariant broken?

**Decision: not broken — verified structurally, not assumed.** `.github/workflows/deploy.yml`
carries three triggers: `workflow_run` on `["CI — Ganga Quality Gate"]` **restricted to
`branches: [main]`** and gated on `conclusion == 'success'`; `pull_request` which is
**build-only — no push, no Cloud Run deploy** (its stated purpose is catching Dockerfile/Next.js
build failures before merge); and `workflow_dispatch`, which since SAMĀPTI is held to the same CI
gate unless an operator explicitly selects `EMERGENCY-OVERRIDE-CI-NOT-GREEN` and supplies a
written reason (Dvārapāla RULING 71 / 73-CLOSE). A lane branch therefore cannot reach production.

Confirmed live: last successful deploy was `7e5f478bd`, which **is** the current `origin/main`
tip; serving revision `amjis-web-01671-47n` at 100%.

**Precedent / principle:** §N.8 applied to the conductor's own watchdog — "production ≡ main" is a
claim, and a claim needs a detector. Reading the run list alone would have produced either false
alarm or false comfort; reading the trigger gating produced an answer that could have come back
either way.

**Reversibility:** N/A — a read-only verification. Nothing changed.

**Falsifier:** If a `workflow_dispatch` with the emergency override fires overnight, or if
`deploy.yml` is edited on a lane branch and merged, this verification goes stale. The pulse log's
independent 30-minute production-revision sampling is the standing detector; §11.4 gives it
authority over the morning report if the two disagree.

---

## FINDING F-N7 — P3-A REFUTED: a §N.8 defect asserted as §N.8 compliance (DD register entry)

**Lane P3-A, PR #1495 — merge blocked pending remediation.** The second REFUTED verdict of the
night, and the more instructive of the two.

**What survived, recorded first because it came out in the lane's favour under direct attack.**
The coverage measurement is correct — reproduced three mutually-independent ways (source-text
grep; a probe importing `VIDHI_PRIMITIVES`/`resolveLiveTool` that never imports `plan_bridge`; the
lane's own function): **60 primitives, 40 distinct `live_tool`, 21/40 live_tools and 35/60
primitives covered, 19 uncovered.** The refuter looked specifically for quiet mapping to flatter
the number and found **zero force-maps**; `resolved_but_unregistered = []`; no `??`/`||` fallback
manufactures an answer. That restraint is correct under §N.4 and §N.7 item 6 and stands as a
credit to the lane. **F-N2 is CONFIRMED and files as a DD entry** — `NAMESPACE_COVERAGE_v2_0.md`
claims "23/23 accounted for (100% dispositioned)"; 16 additional `live_tool` names have since
appeared with no disposition of any kind. GA.1 registry-disagreement class (§I B.8).

**The blocking defect.** `plan_bridge.ts` says of `getPlanBridgeCoverage()`: *"it can only report
what the map above actually computed, so it cannot drift from it (§N.8: the signal and its
detector are the same code path)."*

**"The signal and its detector are the same code path" is not §N.8 compliance — it is the
definition of not having a detector.** §N.8's own question is *"what code path would have to run,
and fail, for this signal to correctly read false?"* Here: none. The refuter demonstrated the
consequence rather than arguing it — force-mapping 18 of the 19 uncovered tools to a
plausible-but-wrong URI produced a **fabricated 59/60 and 39/40, published as truth, with
1613/1613 green**. Exactly one test pins an uncovered name; evading that single pin defeated the
entire proof.

**This is the sharpest instance of the §N.8 class the register has yet recorded**, and it belongs
in the doctrine's own list of confirmed instances alongside the four already there. The prior four
were signals with *absent* or *proxy* detectors. This one is a signal whose author identified the
§N.8 obligation, wrote it down, and then satisfied it with a tautology — the detector and the
claim being the same code path is precisely the property that makes a signal unearned, stated as
though it were the property that makes it earned. Worth the native's attention as a doctrinal
addition, not just a lane finding.

**Mutation matrix (four run, nothing pushed):** M1 partial-builder → **CAUGHT**; M2b new primitive
with real MCP `live_tool` and no web mapping → **NOT CAUGHT**; M3c force-map 18/19 → **NOT
CAUGHT**; M4 `BAND_BUDGET` drift 600/400→700/450 → **NOT CAUGHT**. M4 is separately a §N.7 item 3
violation: `plan_bridge.ts` hardcodes constants mirroring module-private `BAND_BUDGET`/
`BAND_PRIORITY` rather than referencing them.

**Third finding: the title claims something not built.** `VidhiPlan` lives only in `platform-mcp`,
which the diff does not touch. What shipped is a `ToolCallItem` ↔ `CompiledFloorItem` adapter —
both already inside `platform`. The PR *body* discloses the re-scope honestly; the *title* does
not, and the title is what a register inherits.

**Conductor disposition:** remediation dispatched, narrowly scoped to three fixes — retitle to
what shipped; replace the self-certifying comment with a **pinned-baseline assertion over all 19
uncovered names that fails loudly in both directions** (the RC-10 pattern), self-verified by
applying the M3c mutation and observing the new test go red; export and reference the shadow
constants. The builder is explicitly instructed **not** to wire a consumer — that is real blast
radius at this hour — and to re-word the close as **groundwork, DD-21 not claimed**, rather than
as a closed lane. An honestly-labelled groundwork PR is mergeable; a groundwork PR wearing a
closed-lane label is not.

---

## FINDING F-N8 — run-ops: a killed agent's mutations became the next agent's baseline (process defect, fix tonight)

The P3-A refuter found `.clone/worktrees/p3-a-refute` **dirty on arrival** — a leftover force-map
mutation in `compiled_floor_adapter.ts` plus an untracked probe file, left ~7 minutes earlier by an
earlier instance of the same refuter task that died with the conductor pane. That instance had
saved a measurement of `covered_live_tools: 39` — **taken against its own mutated resolver, and
therefore invalid.** Had it reached the conductor, it would have corroborated exactly the
fabricated number the surviving refuter was attacking.

This is a crash-resume hazard the charter does not name: §11.3 covers re-orienting the *conductor*
from derived state, but says nothing about **verifying a shared review worktree is clean before a
replacement agent measures in it**. A mutation-based refuter necessarily dirties its worktree; if
it dies mid-attack, its mutations persist and silently become the next reviewer's baseline.

**Standing correction adopted for the rest of this run:** every refuter either creates a fresh
detached worktree of its own, or verifies `git status --porcelain` is empty and HEAD is the
intended commit before measuring anything. The P4-J refuter was already dispatched with
create-your-own-worktree instructions; the P4-I and P4-K reviewers are to be checked on return for
whether they inherited dirty state.

**Worth a DD entry** as a durable addition to the worktree-isolation protocol: *a review worktree
is not a safe baseline merely because it exists at the right commit.*

---
---

# NATIVE-SURROGATE RULINGS — ROUND 1 (D-006 … D-010)

*All five entries: **DELEGATED-OVERNIGHT, native review pending.** None is the native's own decision.*

---

## D-006 — 2026-08-22T22:22Z — NATIVE-SURROGATE — the P3-E credential fork

**Question as asked:** Rule in advance on both branches of the diagnostician's RF-8 attempt — (a) a
code fix in `ask.ts`, or (b) a credential operation, which is §9 hard-never and §3.3 MUST-PARK. On
branch (b), what happens to THE FLIP, and is any substitute for green×7 acceptable?

**Decision, in four parts.**

**Part 1 — the fork was already resolved by evidence, and it is branch (b).** The surrogate did not
wait for the diagnostician; the answer was in CI. Run `32601926862` carries the lane's own shape
diagnostic:

```
[p3-e-smoke] FIREBASE_ADMIN_CREDENTIALS length=1 chars; does NOT start with '{'
[ask] fatal: SyntaxError: No number after minus sign in JSON at position 1
```

Two independent signals agreeing: the GitHub Actions repo secret is **one character long**, and that
character is `-` (`node -e 'JSON.parse("-")'` reproduces the error byte for byte). Not a PEM, not
truncated JSON, not base64 — **a one-character placeholder**, created 2026-05-18 and never corrected.
*Independently re-confirmed by the conductor via `gh secret list` and a direct re-read of the
diagnostic output.*

**There is therefore no code fix, and branch (a) is foreclosed on fact, not on judgment.**
Base64-decoding `-` yields nothing; there is no credential to accept. The one helper that works
elsewhere (`envOrSecret` → Secret Manager) is unavailable in CI because the CI WIF identity lacks
`secretmanager.secretAccessor` on that secret — and granting it would be a credential operation with
a *wider* blast radius.

**PARKED. Not the surrogate's to decide.** Both repairs are "credential creation/rotation of any
kind." Two options for the native, neither chosen, narrower first:
- **Option A (narrower, recommended, not decided):** upload the existing Secret Manager value into
  the GitHub repo secret. No rotation, no new material, no IAM change. One command.
- **Option B (wider):** grant the CI WIF SA `secretmanager.secretAccessor` on
  `firebase-admin-credentials` plus a `google-github-actions/auth` step. This permanently broadens
  which principal can read a production admin credential.

**Part 2 — THE FLIP PARKS.** §4 precondition 2 is unreachable; per §0 ruling 2 the preconditions
*are* the approval, so unmet preconditions are a refusal, not a formality. A park, not a failure —
§1 says the analogous case ("a retirement train that never opens because the battery stayed red is a
correct night") explicitly.

**Part 3 — NO SUBSTITUTE FOR green×7 IS ACCEPTABLE.** Named individually because each will be
tempting at 05:00: a smoke with the failing assertion removed (§9, over the line, not near it); a
locally-run green (§4 names CI history as the declarer precisely so no local run can supply it); a
manually-attested green (the purest §N.8 defect); counting the existing reds as the can-fail
demonstration (already refused in F-N3 — every red is `ask.ts` exit 1 with zero assertions
evaluated).

**The teeth, stated plainly:** the counter is not one gate but two — §4 precondition 2 gates THE
FLIP, and **§10.3 DD-4 precondition 2 gates the irreversible P4-B deletion off the same counter.** An
unearned green would propagate from a reversible traffic change into a code-tree deletion.
Manufacturing that number tonight would be the single most expensive dishonest act available to this
run.

**Part 4 — what P3-E should do instead.** The credential blocks the *transport*, not the *assertion
layer*. The lane should produce a **fixture-fed, per-assertion red proof** — feed the smoke a
synthesized turn record violating exactly one assertion, observe that assertion fail while the others
pass, repeat per assertion. Precedent: §10.1 requires the DD-1 battery's can-fail proof to be
fixture-fed by construction. **The standard, so this does not become a loophole: the fixture proof
establishes the assertion layer can fail; the counter still may not start until one real, live,
CI-produced green exists.** Value: when the native supplies the credential, the first live green
counts immediately instead of costing another 45-minute cycle.

**Precedent:** §3.3 MUST-PARK · §9 · §0 ruling 2 · §4 precondition 2 · §10.3 DD-4 precondition 2 ·
§N.8 · §10.1 · F-N3.
**Reversibility:** The park is cheap and fully reversible — one native action reopens the path. The
alternative is not: a fabricated green would sit in CI history as the declarer for two gates, one of
which deletes code.
**Falsifier:** (1) If a CI-available principal already holds `secretAccessor` and the workflow's IAM
claim is stale, branch (a) reopens as an ordinary workflow fix and this park was over-cautious — the
surrogate read the workflow's assertion but did **not** independently re-read the live IAM policy,
and says so. (2) If the native holds that re-uploading an existing, unrotated value is not a
"credential operation" in §9's sense — a defensible reading, since no new material is created. The
conservative reading was taken on reversibility grounds. **If the native disagrees, the carve-out is
worth making explicit for future runs, because this exact blocker cost the run its critical clock.**

---

## D-007 — 2026-08-22T22:26Z — NATIVE-SURROGATE — the honest end state, and re-prioritisation

**Decision (i): the honest target is END STATE 5 — PARTIAL, CLEAN.** Not 4, and the surrogate was
exact about why, because 4 is the flattering answer and it is wrong. End state 4 reads: *"P3 A–E
closed, green×7 not yet elapsed by morning; **the hold continues autonomously and the flip fires when
it completes**."* Two clauses fail — P3-E cannot close, and **the hold does not continue
autonomously; it has never started and cannot start without a human action.** Reporting end state 4
would describe a running clock that is not running: precisely the class of claim §N.8 forbids.

**The objective, restated in actionable form: *reduce THE FLIP's remaining preconditions from six to
one.*** Preconditions 1, 3, 4, 5 and 6 are all reachable tonight without the credential. If the
morning report can say *"every flip precondition is met except the smoke counter, and the smoke
counter is blocked on one GitHub secret,"* the native's first action converts end state 5 into a
running hold and the flip fires by early afternoon. **That is worth far more than any cosmetic
upgrade of the label.**

**Decision (ii): THE CADENCE MAY NOT BE COMPRESSED — under any circumstance, binding for the night,
binding on the surrogate too.** Made specific so no agent finds a gap at 05:00: no interval shorter
than 45 minutes for any reason including "we lost hours to the credential"; seven means seven
*consecutive*, any red resetting to zero (W-1) including a red later understood to be unrelated; runs
predating the first real green count toward nothing in any direction; concurrent dispatches to
accumulate greens faster are compression by another name and are forbidden; the counter is read from
CI history at the moment of the flip commit, never carried in an agent's or document's state.

**Why the rule exists, restated because "the cadence" sounds like ceremony and is not:** the smoke
samples the deployed revision **across time**, catching intermittent and warm-up-dependent
regressions that seven rapid-fire runs against one warm instance would all miss identically. **A
compressed green×7 is one observation wearing seven hats.**

**Decision (iii): re-prioritisation.** P4-A/B/C/D, P4-E and P4-F are gated on P3-F and are **closed
for the night**; stop holding capacity for them. Priority order: P3-B (opens on P3-A's close; its
DD-24 gap enumeration is a document and can start immediately) → P3-D's wire↔persisted
byte-agreement precondition (independent of P3-B) → limits enablement (§0 ruling 3, pulled forward;
flip precondition 3) → the flip's rollback pin (precondition 6, written while nobody is in a hurry) →
P4-J as the designated capacity sink → the DD-1 battery → P3-E's fixture red proof and park artifact
→ the morning report, whose highest-value artifact is a **one-page morning unblock sheet** → P4-K
harness, build only.

**Explicitly NOT to be spent on:** any P4-B census work presented as *the gating census*. §10.3
requires a census re-derived after P4-A's redirects land; a census built tonight is superseded by
construction. Building census *tooling* is fine; recording a census *result* is not.

**Precedent:** §1's six end states applied honestly rather than favourably · §N.8 applied to the
run's own end-state label · §4's no-compression sentence · §2's priority order · §11.3 · §3.3
(queue reordering is expressly within surrogate authority).
**Reversibility:** Wholly reversible — a queue ordering and a label. The one item with production
effect (limits enablement) is native-ruled unconditional, so it is being *scheduled*, not authorized.
**Falsifier:** (1) If the credential is trivially available overnight through a channel not
considered, end state 4 returns. (2) If the native reads "the hold continues autonomously" as intent
rather than mechanism, 4 is defensible and 5 is over-strict. **5 was chosen because a native waking
to "the hold is running" and finding no clock would be the exact deception the ledger exists to
prevent — and under-claiming is the cheaper error to correct at breakfast.**

---

## D-008 — 2026-08-22T22:30Z — NATIVE-SURROGATE — build the DD-1 battery tonight?

**Decision: BUILD IT, FINISH THE CAN-FAIL PROOF, COMMIT, PUSH — and RECORD NO PASS.**

**The scope-boundary objection does not apply, and the reason is precise rather than hand-waved.**
MACRO_PLAN's Scope Boundary forbids pre-building for **macro-phases later than the active one** — the
M1–M10 arc. P4 is not a later macro-phase: §0 ruling 7 states *"P4 IS AUTHORIZED IN THE SAME
WINDOW."* The battery is a named deliverable (§10.1) of a phase the native explicitly opened.

**The sharper objection — "a gate whose gated event may not occur" — is answered by the charter's own
design.** The gated event not occurring is one of six ranked outcomes the charter enumerates in
advance, and the charter keeps building through it: §1 end state 2 calls a parked retirement train
with the rest closed a **success**; §7 lists "DD-1 battery red" under PARK-not-STOP with "continue
remembering + fillers." A charter that plans to continue past a red battery expects the battery to
exist whether or not it opens anything. Reversibility is one-sided: an unused battery costs budget
that is not the binding constraint; a missing battery costs a full serial cycle whenever the flip
does fire — very likely today, given the blocker is one secret.

**On fixture-vs-live:** §10.1 requires the battery's *real run* to be against the post-flip live
surface, and requires the can-fail proof to precede the first real pass. It does **not** require the
proof itself to be live — and could not, because "feed it one deliberately register-broken reading"
is not something a live surface produces. **The can-fail proof is fixture-fed by construction.**

**Three binding conditions:** (1) **NO PASS IS RECORDED TONIGHT** — the fixture run is a *self-test
of the battery*, never a battery result; the receipt's `"target"` stays null; a fixture green recorded
as the gate outcome would gate an irreversible deletion on a fixture. (2) The worktree must not be
left mid-edit (§1). (3) It is a filler, queues as one, draws on the **P4 $150 subtotal**.

**Precedent:** §0 ruling 7 · §10.1 · §7 PARK-not-STOP · §1 end state 2 · §3.2 · §N.8 · §0 ruling 11.
**Reversibility:** Fully reversible; condition 1 means no claim is created that would need retracting.
**Falsifier:** (1) If the native intends P4 stood down entirely once the flip parks. (2) **If the
fixture corpus is authored such that the detectors could only ever fail those specific strings — a
fixture that proves the detector matches its own fixture and nothing more.** The surrogate explicitly
did not audit the fixture generator and did not claim to. *That audit was assigned to the battery's
refuter as the single most valuable refutation available on the lane.*

---

## D-009 — 2026-08-22T22:34Z — NATIVE-SURROGATE — F-N4 (migrations 588/589)

**Decision: "filed, not fixed" CONFIRMED on the governance question — and the finding is materially
WORSE than filed. One action authorized, and it is deliberately not a governance action.**

**Correction 1 — two applied migrations, not one.** 589 is applied too; its purpose is to drop three
functions 588's own `DROP FUNCTION` statements failed to name correctly. A live read confirms all
three gone. `_migrations_applied` still ends at `587_…` (id 446). **Two production schema mutations,
zero ledger rows.**

**Correction 2 — the change removed database guardrails, and 589 exists because 588 was partly
wrong.** 588 drops the per-asset build protection triggers installed by migrations 540/566. 589's own
header states 588's `DROP FUNCTION` names were *"guessed from the trigger names, not read from
migrations 540/566,"* so they no-oped. **A migration authored partly by guesswork, removing
destructive-write protection, applied to production, with no ledger row.**

**Correction 3 — and this is what makes "filed, not fixed" right rather than merely cautious.** 588's
header carries *"Native instruction, 2026-08-23"* and attributes the work to **NIRMĀṆA ELEVATION**.
It is not an anonymous stray: it is another live campaign's work, under what it records as the
native's own direction, with a documented pg_restore-verified snapshot taken beforehand. Reconciling
it would mean **rewriting a second campaign's audit trail** — §3.3 MUST-PARK, §9.

**Does tonight make it worse? Yes, specifically.** Not via deploy (`migrate.ts` runs against the
repository; these exist only in the local checkout). The elevation is **housekeeping risk**: a
many-agent night whose close discipline involves worktree removal and tidying, where a `git clean
-fd` in the shared checkout destroys the only record of SQL whose effect is live and unrecorded
anywhere else. Low probability, total and silent loss.

**The one authorized action — a byte-preserving read-only copy outside the repository.** It runs no
git command, mutates no tracked or untracked file, alters no index, touches no other campaign's
decision, and forecloses **no** morning option. It removes only the irreversibility. *Executed by the
conductor; both files copied with `cp -p` to `run/salvage/` and sha256-recorded.*

**The morning action for the native (not to be run tonight):** read `_migrations_applied` for `58%`;
then preserve the applied SQL on a branch (never onto main directly) and decide — **backfill the two
rows** (asserting they went through the tracked path, which they did not) **or record them as
out-of-band operator changes** pointing at the campaign that made them. The second is the honest
option (§N.7 item 6 — a backfilled row is a small invented judgment about provenance). Risk of
leaving it unreconciled: a future `migrate.ts` cannot know these ran, and a schema rebuilt from the
tracked ledger will differ from production in exactly the guardrails these removed.

**Falsifier:** (1) If the native's direction to NIRMĀṆA already included the ledger disposition, the
right action is to close F-N4 by pointing at NIRMĀṆA's record. The surrogate did **not** read
NIRMĀṆA's artifacts — `NIRMANA_ELEVATION_PLAN_v2_0.md` is itself untracked here and was treated as
another campaign's live working state, out of bounds. **Check that first in the morning.** (2) If a
read-only copy-out of another campaign's untracked files is itself a boundary violation, the backup
was an overstep and naming the `git clean` risk in the report was the correct action instead.

---

## D-010 — 2026-08-22T22:38Z — NATIVE-SURROGATE — budget method and checkpoints

**Part 1 — the method is acceptable; the *label* is not.** The morning report must never print
"**Spend: $52 / $400**". It must read: **"Estimated spend: ~$X of $400 … Method: per-lane token
estimation. NOT METERED. Error direction: UNDER"** — because conductor-session tokens are not
itemized per lane and the conductor is plausibly among the night's largest consumers. **Treat as a
lower bound, not a measurement.** This is not pedantry: §7 makes "combined ledger ≥ $400" a **STOP
condition**, and a STOP condition driven by an unmetered estimate that errs UNDER is a guard that can
fail to fire when the real threshold is crossed — §N.8's defect sitting on the run's own safety rail.
**The honest response to an estimator that errs UNDER is not more prose; it is margin.**

**Part 2 — checkpoints, binding.** Keyed to the estimate with a deliberate 30% haircut. Gating on
**opening** rather than spending is what makes each subtotal halt at a lane boundary per §0 ruling 10
— a lane opened below its checkpoint runs to its natural close.

| | Nominal | NO NEW LANES above | DRAIN-ONLY above |
|---|---|---|---|
| P3 half | $250 | **$175** | **$210** |
| P4 half | $150 | **$105** | **$126** |
| Combined | $400 | **$280** | **$340** (governance close begins here regardless of subtotals) |

The *combined* checkpoint binds even if both subtotals are individually under (the UNDER bias is
common-mode). "New lane" = a new dispatch against a lane not already open; continuing an open lane is
never blocked. **Nothing in this table may be relaxed by the conductor.**

**Part 3 — the budget is NOT tonight's binding constraint, and the conductor should stop conducting
as though it were.** ~$9.5/hour observed. **The binding constraint is wall clock and queue depth, not
money.** Concretely: P4-J's parallel generation should be **widened, not rationed**. §2's WATCHDOG
names an under-filled queue a *conducting error*. **Under-spending a $400 authorization while the
queue starves would be a failure to execute the charter, not thrift.**

**Part 4 — two things that stay MUST-PARK.** Raising the $400 total (§3.3 — if the estimate reaches
$400 the run STOPS per §7; it does not ask for more, because more is not the surrogate's to give).
Moving allocation between subtotals — not pre-authorized; the test would be (a) a P3-critical-path
task blocked *purely* on its subtotal, (b) the donating half already parked for a non-budget reason,
(c) bounded to one named lane, no rise in the combined total. **Tonight (a) is unsatisfiable — P3's
lanes are blocked by a credential, not money — so no transfer is expected or authorized.**

**Falsifier:** (1) **If a real metered figure is obtainable, the estimate should be replaced outright
and these haircuts are unnecessary. The morning report must state whether reconciliation against a
metered source was attempted and what it found, or state plainly that no such source was available.
An estimate that never tried to check itself is a weaker artifact than one that tried and could
not.** (2) If the native's intent was that the $400 be *spent* — a cap sized for a two-phase run —
the 70% checkpoints are too conservative and should move to 85%.

---
---

# NATIVE-SURROGATE RULINGS — ROUND 2 (D-011 … D-015)

*All five: **DELEGATED-OVERNIGHT, native review pending.***

---

## D-011 — 2026-08-22T22:40Z — NATIVE-SURROGATE — P4-H disposition

**Decision: (a) PARK — with a specified deliverable, not an empty park. (b) re-scope and (c)
merge-with-honest-wording are both REFUSED, on different grounds.**

**(c) is refused, and this is the substance of the ruling.** *Is a durable-looking-but-not-durable
path an improvement over an obviously-hollow one?* **No**, for three compounding reasons:
1. **The honest re-wording does not travel with the code.** The caveat lives in GitHub; the endpoint
   lives in the repo. **The over-claim is not in the sentence — it is in the artifact.**
2. **Intermittent correctness is a worse defect class than uniform failure.** An unconditional hollow
   200 is greppable and provably broken by one test. A write that survives zero-to-one turns
   depending on what the reader does next is the worst debugging profile, and it **silently corrupts
   a record rather than leaving it empty**.
3. **For disputes the corrupted-record cost is not symmetric with the empty-record cost.** A dispute
   is the native saying *"this reading was wrong about my life"* — the input substrate of the L5
   calibration loop, sealed in STRUCTURAL mode precisely so it fills from real outcome data. Partial
   silent loss does not merely fail to help; it puts unrepresentative data into the loop that fills
   it. §N.7 item 6 at the data layer: **a dispute row that sometimes exists is an invented judgment
   about what the reader said.**

**(b) is refused independently of whether the fix is correct.** The `||` merge is directionally
right, but: it sits on the core turn write path of the live product, unattended, at 04:00; it is a
**semantic change for every existing consumer** (under `||` a key can no longer be *removed*;
`provenance_stamp`/`acharya_reading_receipt` become sticky on non-last-assistant messages, and nobody
has enumerated who reads them); `||` is a **shallow** merge. **Decisively: (b) does not close the lane
anyway** — no client can transmit a `comment`, so the DD-21 artifact remains unobtainable. **(b) would
spend the largest blast radius of the night on a lane that still parks.**

**What the park must produce:** (1) a **quarantined, already-red** regression test encoding
write-dispute → one follow-up turn → assert retention, marked expected-fail so CI stays green — this
hands the morning **a detector that already demonstrates it can call the claim false, §N.8 discharged
in advance of the fix, which is the correct order and the one this campaign keeps getting backwards**;
(2) a DD entry with three root-cause findings, none of them P4-H's — the two writers' `{}` reset; the
`writeConversationMessages` `verified: true` defect (**a fresh confirmed §N.8 instance for the
doctrine's own list**); and the JSONB sub-object convention being structurally unsafe for out-of-band
writers; (3) a one-paragraph design note recommending a dedicated `conversation_disputes` table —
**recommended, not built, a native call**; (4) standard park mechanics + retitle per D-015.

**Recorded plainly:** the builder did real work, its read-back leg is sound, and it filed its own
residual honestly — which is what pointed the refuter at the right place. **The lane failed; the
process worked.**

**Falsifier:** an enumeration showing `metadata_json` has exactly one consumer (making `||` blast-
radius-nil), or a client that can actually transmit a `comment` (making the lane closeable). **Neither
exists tonight and neither was assumed.** What would NOT falsify it: *"the SQL is obviously right."*
The correctness of the SQL was never the question.

---

## D-012 — 2026-08-22T22:43Z — NATIVE-SURROGATE — `PARIPRASHNA_LIMITS_ENABLED`

**Decision: ENABLE — under canary discipline, with a verification package built entirely from paths
that touch no production credential, substantially executed read-only in the ruling itself.**

**On the reading.** The claim that "unconditionally" removes only the reject-demo gate, leaving
normal-turns as a live pre-gate, **misreads §4's grammar**: *"VERIFIER confirms normal turns still
succeed **post-enable**"* is a post-condition, not a precondition. Treating it as a gate would park a
recorded native ruling — **§3.3 forbids reversing one, and deferral is reversal wearing a softer
word.**

**But authority alone is insufficient, and the §N.8 concern is real** — so: ENABLE **plus**:

**V1 — static projection sweep (executed, credential-free, deterministic).** The only fail-*closed*
branch is `projectTurnCostUsd` → `turn_ceiling_exceeded`, a pure function over a static registry.
Swept every entry of `platform/src/lib/models/registry.ts`:

| model | worst-case projection | verdict |
|---|---|---|
| `claude-opus-4-7` | 128K×$15 + 64K×$75 = **$6.72** | **EXCEEDS $2 — blanket-refused** |
| `claude-sonnet-4-6` | $1.34 | pass |
| `gemini-3.1-pro-preview` | $1.04 | pass |
| `gemini-2.5-pro` | $0.82 | pass |
| gpt-4.1 / gpt-4o / deepseek / flash / NIM | ≤ $0.49 | pass |

**Exactly one model would be blanket-refused, and per CLAUDE.md v7.2's close record
`ANTHROPIC_API_KEY` is entirely unprovisioned in production (default stack is `gemini`), so it cannot
be dispatched today.** *This is the verification that was called impossible. It was not impossible;
it was in a different place than the credential.*

**V2 — fail-open audit (executed).** `getDailySpendUsd` fails open; `checkSpendCeilings` does not
breach on `known: false`; `projectTurnCostUsd` returns `null` — not `0` — for an unpriced model, which
therefore cannot be refused. **A DB outage, pricing gap, or unknown model does not refuse turns.**

**V3 (owed, live, credential-free)** — unauthenticated POST to the web door must return **401, not
429** on the tagged revision (`checkDoorRateLimit` sits *after* the session gate in `proxy.ts`).
**V4 (owed, live, credential-free)** — `/api/mcp/*` is in the proxy's `isPublic` allowlist, so >120
POSTs/min to `MCP_DOOR` must return 429 + `LIMIT_RATE_LIMIT_EXCEEDED` + `Retry-After`. **This is an
actual demonstrated-can-fail run of the limiter on live infrastructure with no credential.**
**V5 (owed)** — absence of `[limits:spend_ceiling] … failing open` in the tagged revision's logs;
recorded as **weak** evidence, not banked as green.

**NOT verifiable tonight, owed and never claimed:** the authenticated end-to-end normal turn, and
§6.4's reject demo. The report must say: *"limits enabled; proxy leg demonstrated capable of failing
live; spend leg verified statically and by fail-mode audit; the authenticated end-to-end turn remains
unobserved and is owed."*

**Mandatory sequence, no compression:** rollback pin written and syntax-tested **first** → tagged
revision at 0% → V3 → V4 → V5 → announce revision tag (X-6) → 100% → post-shift V3 + V5 → confirm
serving revision.

**Five automatic rollback triggers, any one executed without deliberation:** (1) unauthenticated
web-door POST returns 429 instead of 401; (2) any `LIMIT_*_EXCEEDED` on the 100% revision on a
non-probe request; (3) `failing open` in production logs; (4) measurable 5xx increase on door paths;
(5) the native reports a refused or failed turn, at any hour.

**Two residuals, neither blocking:** DD-26 (>200K-token inputs under-priced, so the ceiling
under-projects on very large inputs — recorded honestly per §6.4); and the proxy's fallback bucket
chain, where MCP callers presenting neither a key id nor `X-Forwarded-For` share one 120/min bucket.

**Falsifier:** **`claude-opus-4-7` turning out to be dispatchable in production** (every Opus turn
would be pre-emptively refused, and V1 becomes a blocker not a clearance), or a model reaching
production absent from the pricing registry (V1's sweep is only as complete as that registry). **Both
checkable in one command each; both on the unblock sheet.** What would NOT falsify it: *"no one
verified it end-to-end"* — that is disclosed and owed, not hidden.

---

## D-013 — 2026-08-22T22:46Z — NATIVE-SURROGATE — migration 588's UNIQUE key

**Decision: CONFIRM the direction — and EXTEND it, because the schema change alone is insufficient
and, landed alone, would have been strictly worse than the bug.**

Both conductor reasons verified rather than accepted: 588 is genuinely unapplied (`_migrations_applied`
tops out at 587; `to_regclass` = `f`), so §N.4's *"NEVER EDIT A MIGRATION AFTER IT HAS BEEN APPLIED"*
does not bind and the alternative is strictly more expensive; and a green exit hiding a suppressed
digest is §N.8 verbatim — the claim is *"the digest was dispatched"* while the detector only asked
*"did a row exist for this `as_of`."*

**The extension is the load-bearing half.** A migration change without the matching application change
would have produced a **runtime failure on every write** (`ON CONFLICT (as_of)` cannot infer against a
two-column constraint — SQLSTATE 42P10). And **the bug actually lived in the read path**:
`hasSent(asOf)` never mentioned `run_chart_id` at all. **A unique key does not scope a query that does
not mention the column.** All three must land: the constraint, `hasSent`/`readByAsOf` scoping, and
`ON CONFLICT (as_of, run_chart_id)`. **Merge admission: all three in one PR, or none.**

*(Conductor note: the P4-I remediation builder independently discovered the same read-path gap and
fixed all three together before this ruling reached it. The two arrived at the identical conclusion
from opposite directions.)*

**Three close conditions:** (1) `NULLS NOT DISTINCT` is PG15+ — **verified, not assumed**: migrations
170 and 218 already use it and are applied, CI runs `postgres:16`. (2) The two-chart same-day
reproduction must be re-run **unmodified** and observed to produce two rows — *a rewritten
reproduction proves nothing about the original*. (3) DD-21 remains a journal row read back from a
real database.

**The latency point, stated so it is not mistaken for a reason to relax:** the cron passes no
`--chart` today, so the flaw is latent. **That makes this cheap to fix, not optional to fix.**

**Falsifier:** if `_migrations_applied` is not the authoritative apply record for
`platform/supabase/migrations/`, this edit violates §N.4 and owes a 590 instead. **The conductor must
re-confirm `to_regclass` = `f` immediately before the merge rather than rely on this reading —
because F-N4 already established tonight that this repo has at least one migration whose effect is
live with no ledger row.** What would NOT falsify it: *"the cron doesn't use `--chart`."*

---

## D-014 — 2026-08-22T22:49Z — NATIVE-SURROGATE — remaining capacity

**Priority order, ranked against the unchanged objective — reduce the flip's preconditions from six
to one:** (1) **the morning unblock sheet — start now, maintain continuously, never compose at 06:20;
if everything else collapses, this ships**; (2) the flip rollback pin — cheapest precondition on the
board, and *syntax-tested means dry-run output pasted into the ledger, not "it looks right"*;
(3) limits enable per D-012; (4) P3-D's wire↔persisted byte-agreement test, demonstrated-can-fail
first; (5) DD-24 gap enumeration; (6) land what has survived review — *unlanded verified work is work
a crash erases*; (7) widen P4-J, last, only into capacity that would otherwise idle.

**Drop order if short: 7, then 5, then 4. Never 1, 2, or 3.**

**Do not open at all:** the RETIRE train, P4-E, P4-F, P4-K's live execution — all flip-gated.

**On the budget, and why no money moves.** P4's remainder has little to buy with RETIRE never opening,
and the temptation is a transfer. **Declined, because no transfer is needed:** items 1–5 are documents,
offline tests and one env var, and P3 has its own subtotal left. §0 ruling 10 permits a transfer only
with a written safety rationale, and ***"the other half has spare" is not a safety rationale — it is a
convenience one.***

**Hard close at 06:30 IST regardless of state.** Lead the report with the end state **as a success,
not an apology**.

---

## D-015 — 2026-08-22T22:52Z — NATIVE-SURROGATE — **STANDING RULE: THE HEADLINE RULE**

**Binds every builder, verifier, refuter, integrator and scribe for the rest of this run, and files to
the register as a standing rule.**

> **A headline may assert only what was observed, at the layer it was observed, and may never assert a
> capability the reader could not exercise. Everything else goes in the body. If the honest headline
> is uglier, ship the uglier one.**

"Headline" = every short surface met before the body: PR title, commit subject, tracker status,
register row, close claim, first line of any report, summary sentence of any return.

**The three-question test — answer all three, or the headline cannot say that thing:**
1. **Name the observation.** Quote the transcript line, DB row, screenshot, CI log line — the thing
   itself, not a description. **If you cannot paste it, the headline cannot claim it.**
2. **Name the layer, and put it in the headline.** Protocol · persistence · UI · end-to-end. *"SSE
   emits the event"* is not *"it reaches the conversation."* *"The row was written"* is not *"the row
   is durable."* *"The map exists"* is not *"the plan types are unified."* **A layer word in the
   headline is not clutter; it is the claim.**
3. **Name the missing half.** Search your own body for *however*, *not yet*, *does not*, *no client*,
   *only at*, *pending*. **If one exists, its consequence belongs in the headline. A disclosure that
   lives only in the body is not a disclosure — it is an over-claim with an alibi.**

**Two always-safe forms:** `groundwork: <what shipped>; <what is not claimed>` · `<X> proven at
<layer>; <Y> not reachable`.

**Why this is enforcement, not style.** A headline is a claim and §N.8 binds claims. Ask it directly:
*what would have to be false for this headline to be wrong?* **If the answer is "something the body
already admits is false," the headline is refuted before the refuter arrives.** All three of tonight's
over-claims fail that in a single read. And **the register inherits the title, not the body** — an
over-claiming headline is the *mechanism* by which an unearned signal enters the permanent record.

**Procedural hook, effective immediately:** every VERIFIER and REFUTER reads **the headline against
the body first, before reading any code**, and reports a mismatch as a finding in its own right. It
costs sixty seconds. **All three of tonight's refutations would have been caught in that one read.**
A headline/body mismatch alone is sufficient grounds to withhold merge admission.

**The counterpart, so this is not read as a rule against builders:** in all three cases the builder
**disclosed honestly in the body. The honesty was there; only the compression was wrong.** A lane that
discloses fully and titles badly needs one word changed — bounce it in those terms.

**Falsifier:** if the resulting titles read as unreadably hedged, the dial is question 2's layer word,
relaxable to "state the layer only when the headline could otherwise be read as end-to-end."
**Questions 1 and 3 do not move under any reading.** What would NOT falsify it: *"the body said so."*
That objection is the defect.

---

## F-N9 — CONDUCTOR — the credential re-check (D-014 item 12), and what it found

**Discharged, and it found something sharper than expected.** `ask.ts` has **no base64 decode
anywhere** — line 195 is a bare `JSON.parse(credsRaw)`. So the failure was never a decoding bug and
branch (a) is closed on code as well as on the secret's length.

**The additional finding:** `envOrSecret` (`ask.ts:160-170`) reads the environment **first**:

```ts
const fromEnv = process.env[envVar]
if (fromEnv) return fromEnv
console.error(`[ask] ${envVar} not set — fetching Secret Manager:${secretName} …`)
```

`'-'` is truthy. **The one-character placeholder therefore short-circuits the Secret Manager fallback
that would otherwise have run.** This explains the asymmetry cleanly: production works because it
binds `firebase-admin-credentials:1` directly and never consults the GitHub secret; CI fails because
the placeholder is present and actively suppresses the fallback path designed to save it.

**A malformed secret is strictly worse than an absent one here** — and that yields a third morning
option worth naming: *deleting* the GitHub secret would let `envOrSecret` fall through to Secret
Manager. Whether that succeeds depends on the CI identity holding `secretmanager.secretAccessor`,
which the surrogate reports it does not — so this is offered as a diagnosis, not a recommendation.
Added to the unblock sheet with that caveat stated.

---

## D-016 — 2026-08-22T22:45–23:00Z — CONDUCTOR / DEPLOY WARDEN — `PARIPRASHNA_LIMITS_ENABLED` ENABLED IN PRODUCTION (executed)

**The run's only production change tonight. Flip precondition 3 is now satisfied.**

Executed per native ruling §0.3 (*"ENABLE UNCONDITIONALLY"*) and surrogate ruling D-012, in D-012's
mandatory sequence with no compression.

**Before touching anything, D-012's own falsifier was checked live rather than taken from the
document that asserted it.** D-012's clearance rested on *"`ANTHROPIC_API_KEY` is entirely
unprovisioned in production"* — sourced from CLAUDE.md's v7.2 close record, three weeks old. Verified
directly against the live service: the env carries `OPENAI_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`,
`DEEPSEEK_API_KEY`, `NVIDIA_NIM_API_KEY` — **and no `ANTHROPIC_API_KEY` at all.** So
`claude-opus-4-7`, the single model whose worst-case projection ($6.72) exceeds the $2 turn ceiling,
cannot be dispatched. V1's clearance holds on live evidence, not on a document's memory of it.

**A second hazard was caught before it fired.** The rollback-pin lane had warned that
`--set-env-vars` would silently wipe live flag vars not declared in `deploy.yml`. Enumerated before
acting: **64 env vars, 15 of them `MARSYS_FLAG_*`**, and the limits flag was not among them.
`--update-env-vars` used. Had the warning not been written down an hour earlier, the obvious command
would have disarmed fifteen feature flags on the native's live product in one stroke.

**Sequence executed:** rollback pin committed first (PR #1503) → pre-state captured
(`amjis-web-01671-47n`, 100%, 22:45:40Z) → canary revision `amjis-web-02826-huf` created at **0%
traffic** with tag `limits-canary` → V3, V4, V5 on the canary → X-6 announcement to
`campaign-coordination` **before** any shift → 100% → post-shift V3 + V5 → serving revision confirmed.

**V4 is the result worth keeping.** 140 rapid POSTs to `/api/mcp/*`, run against both revisions from
the same source in the same window:

```
CANARY (flag ON):   131 x 401,  9 x 429
PROD   (flag OFF):  140 x 401,  0 x 429
retry-after: 56
{"error":{"code":"LIMIT_RATE_LIMIT_EXCEEDED","message":"Too many requests. Please slow down.",
 "retry":true,"detail":"Rate limit of 120 requests/minute exceeded. Retry in 56s."}}
```

**A demonstrated-can-fail run of the limiter on live infrastructure, with a negative control, using
no credential of any kind.** The surrogate predicted this path existed when the reading that said
"post-enable verification is impossible" had concluded otherwise; the prediction was correct. V3
passed on both revisions (401, never 429 — the session gate precedes the limiter). V5 found no
fail-open warning and no 5xx, recorded as **weak** evidence per D-012's own instruction.

**Post-shift state:** serving `amjis-web-02826-huf` at 100%; `/api/pariprashna` and
`/api/chat/consult` return 401 unauthenticated; `/login` returns 200; zero 5xx; no fail-open warning.

**Owed and explicitly NOT claimed:** the authenticated end-to-end normal-turn check and §6.4's
spend-ceiling reject demonstration. Both require the probe harness, which is blocked on the malformed
CI credential. **This enable does not claim them.** Carried to the morning sheet as owed.

**Rollback armed and pinned:**
`gcloud run services update-traffic amjis-web --to-revisions=amjis-web-01671-47n=100 --region=asia-south1`
Five triggers armed (D-012), any one executed without deliberation.

**Reversibility:** one traffic command, no build, no schema, no data.
**Falsifier:** if a model reaches production that is absent from `platform/src/lib/models/registry.ts`'s
pricing, V1's sweep is incomplete by exactly that model — the sweep is only as complete as the
registry. Re-run it whenever a model is added. On the unblock sheet.

---

## F-N10 — the limits enable is durable, but only by an UNDECLARED default (found while watching the next deploy)

**Caught by asking whether the run's own production change would survive the next deploy — rather than
assuming it would.**

#1498's merge queued a `Deploy to Cloud Run` from `main`. That deploy re-deploys the web service, so
the question is whether it would silently revert `MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED=true`.

**Answer: no — and the evidence is empirical, not doctrinal.** `deploy.yml` uses
`google-github-actions/deploy-cloudrun@v2` with an `env_vars:` block and **does not declare
`env_vars_update_strategy`**. Its runtime block names exactly four `MARSYS_FLAG_*` vars
(`BUILD_TRIGGER`, `HISTORY_COMPRESSION`, `OBSERVATORY`, `VECTOR_SEARCH`). The live service carries
**sixteen**, including eleven `MARSYS_FLAG_PARIPRASHNA_*` vars that appear nowhere in the workflow:

```
declared in deploy.yml : 4
live on the service    : 16   (11 PARIPRASHNA_* undeclared)
```

Those eleven have survived many deploys. **That is proof by observation that the action merges rather
than replaces**, and therefore that tonight's flag will carry forward.

**But the property is unearned in exactly the §N.8 sense.** It holds because of an action's *default*
that this repository never declared, never pinned, and does not test. Nothing would fail if the
default changed in a future action release — eleven feature flags, including the safety gate, the
voice enforcement, and now the spend limits, would silently revert on the next deploy, and the first
symptom would be a behaviour change nobody could attribute. Ask §N.8's question: *what code path
would have to run, and fail, for "the flags survived the deploy" to correctly read false?* There is
none.

**Recommended, not done tonight** (it edits the deploy pipeline, which is not this run's scope at
05:00 with no human awake): declare `env_vars_update_strategy: merge` explicitly in `deploy.yml`, or
promote the eleven undeclared flags into the workflow's own `env_vars:` block so their values are
version-controlled rather than resident only in Cloud Run's mutable state. Either turns an incidental
property into a pinned one.

**What the run DID do about it:** treated the in-flight deploy as a live detector and verified the
flag's survival against the post-deploy revision rather than asserting durability. Result recorded
below.

**Falsifier:** if the post-deploy revision does not carry the flag, then the limits enable was
reverted by the deploy, "flip precondition 3 satisfied" is false as of that moment, and the morning
report must say so. This is checked, not assumed.

## F-N10 — RESULT: VERIFIED, the flag survived a real deploy — and the rollback target is now STALE IN A DANGEROUS DIRECTION

**F-N10's falsifier was checked, not assumed.** `Deploy to Cloud Run` for `898f53c37` (main, from
#1498's merge) completed **success**, created a new revision, and:

```
serving revision : amjis-web-01673-665   100%
MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED = true
MARSYS_FLAG_* count on template        : 16
```

**The flag survived a genuine deploy from main.** `deploy-cloudrun@v2` merges. The limits enable is
durable in practice — and the property is now confirmed by observation of an actual deploy rather
than by inference from persistence. F-N10's recommendation stands unchanged: it is still an
undeclared default, still unpinned, still worth declaring explicitly.

**But the verification surfaced a second, sharper problem.** The serving revision has moved twice
since the rollback pin was written:

```
amjis-web-01671-47n   <- the pin's recorded target (pre-limits)
amjis-web-02826-huf   <- the limits canary this run shifted to
amjis-web-01673-665   <- what is serving NOW, after main's deploy
```

`P3F_FLIP_ROLLBACK_PIN_v1_0.md` records `amjis-web-01671-47n` as the known-good target. **That
revision predates the limits enable.** Rolling back to it would un-flip *and silently disarm the
spend caps* — reverting a native-authorized change nobody asked to revert, as an invisible side
effect of a rollback aimed at something else.

The pin does label its captured revision **"illustrative only, must be re-read fresh at flip time,"**
which is the right instruction and is what saves it. But an instruction is weaker than a correct
value sitting on the page, and a tired reader at speed reads the value. **This is the exact trap a
stale pin sets**, and it materialised within ninety minutes of the pin being written — which is
itself the argument for the instruction.

**Recorded, not silently patched:** the correction is carried into the morning unblock sheet, where
someone reaching for a rollback will actually be looking. Amending the pin document itself is left
for the morning, alongside its own §6 human-confirmation step — the pin is under review on PR #1503
and rewriting a document mid-review would erase what the reviewer is currently reading.

---

## F-N11 — the rollback pin's verification is green-either-way for the rollback it is attached to (§N.8, in the flip's highest-stakes document)

Found by the prep-PR reviewer, independently of the conductor's own stale-revision finding, and it is
the sharper of the two.

`P3F_FLIP_ROLLBACK_PIN_v1_0.md` §5.2 proposes an unauthenticated `curl -sI` against
`/clients/<synthetic>/pariprashna`, with "rollback succeeded" = `307 → /clients/…/consult`. That
outcome is producible **only** by `PARIPRASHNA_ENABLED` being false — `page.tsx:42–44` is the only
code path that emits it. But **PRIMARY** (the traffic shift, which the document lists first, calls
"the standard one," and whose §7 kill criterion tells the operator to fire without a second opinion)
**does not change that flag**: both `amjis-web-01671-47n` and `amjis-web-02826-huf` carry
`MARSYS_FLAG_PARIPRASHNA_ENABLED = true`. The flip changes *default routing*, not the pariprashna
page's own guard.

So the check returns `307 → /login` identically before and after PRIMARY. **§5.2 verifies SECONDARY
only; PRIMARY has no functional detector at all.**

And the document forecloses the possibility in writing:

> *"What would make this check silently pass when the rollback failed: nothing obvious — the two
> locations are textually distinct and the check requires no auth, so there's no plausible 'looks
> green either way' failure mode here."*

**That sentence is false.** It is §N.8's defect in its most dangerous location: the verification step
of a rollback runbook, asserting its own unfalsifiability. Fix dispatched.

---

## F-N12 — a revision pin is a SAFETY-CONFIGURATION pin (DD entry; §9 reached by accident)

The conductor and the prep reviewer found this independently, ninety minutes apart, from opposite
directions — which is itself worth recording.

```
amjis-web-01671-47n  <- the pin's §4 recorded target   LIMITS_ENABLED  ABSENT
amjis-web-02826-huf  <- the limits canary                              = true
amjis-web-01673-665  <- serving now, post main-deploy                  = true
```

Rolling back to the recorded target **silently disarms the $2/turn and $40/day pre-dispatch spend
ceilings and the per-user rate limits on both doors** (`enforceTurnLimits` short-circuits to allowed
when the flag is off — `src/lib/limits/index.ts:53`), while the operator believes they only undid the
flip. **That is a rollback command routing around a safety gate — the thing §9 prohibits — reached by
accident rather than intent.**

The document's §4 even records `LIMITS_ENABLED: absent` as *positive* evidence of a clean pre-flip
state, and never notices that this is exactly what makes the revision unsafe to return to once limits
are armed. Its §3 instruction — *"read fresh, not copied from §4"* — is what saves it and is correct;
but the literal revision name sits in a bordered copy-paste table directly under a
`<PRE_FLIP_REVISION>` placeholder, and **a tired reader at speed reads the value, not the
instruction.**

**Generalisable rule, worth a DD entry:** a rollback runbook must require an **env diff of the
candidate revision against the current one, confirming no `MARSYS_FLAG_*` safety flag is lost**,
before any traffic shift. A revision is not just a code pin — it pins the safety configuration that
shipped with it.

---

## F-N13 — the byte-agreement test's two operands are one object reference (§N.8 sixth-instance candidate)

The P3-D-prep byte-agreement test survived **five independent sabotages** (wire-side key reorder,
persisted-side nested value change, wire-side field drop, whitespace-only change, extra field), each
different from the lane's own, **all RED**, with a deep-clone control **GREEN**. It runs in ordinary
CI with no DB and does not skip. The guard is real and the mocks are not hollow — editing the real
`persistence_stage.ts` flipped the outcome in five of six runs.

**But both sides trace to a single object reference** (`persistence_stage.ts:499` and `:507`;
`receipt/store.ts:46` stores by reference). So it cannot fail on a *value* divergence — there is no
second derivation to diverge — only on a *code* change that produces two objects, which is precisely
why every sabotage had to edit source.

**That makes it a single-source-of-receipt invariant guard — genuinely valuable, and the right guard
to have — but not "byte agreement between two independently-assembled derivations,"** which is what
its headline says. **CLAUDE.md §N.8 instance 3 is literally "a byte-equality claim with no byte
comparison behind it,"** so this artifact above all others must not leave a byte-equality headline
resting on an unstated identity invariant. Headline fix dispatched; the test itself is sound and
unchanged.

Also filed: its fourth assertion (*"receipt_hash identical on both sides"*) stayed GREEN under all
five sabotages including a whole-field deletion — it can only fail under the lane's own sabotage and
adds no detection the byte assertion doesn't already give. To be labelled a documentation assertion
or dropped.

---

## F-N14 — the MCP door has NO feature-flag gating, and the "kill switch" does not cover it

```
grep -n "getFlag(" src/app/api/mcp/prashna_ask/route.ts src/lib/pipeline/prashna_ask_synthesis.ts
  -> no matches
grep -rn "getFlag('PARIPRASHNA_ENABLED')" src/
  -> clients/[id]/pariprashna/page.tsx:42 · clients/[id]/samiksha/page.tsx:27
     api/pariprashna/resume/route.ts:80   · lib/pariprashna/pipeline/safety_gate.ts:107
```

The web door **404s** when `PARIPRASHNA_ENABLED` is off; `prashna_ask` stays fully live. Two
consequences neither document had noticed:

1. **The flag the rollback pin calls a "mechanism-independent kill switch" does not cover the MCP
   door at all.** An operator pulling it believes they have closed the surface; one door stays open.
2. G3/G4 were marked `fixed-first` *"by construction once P3-B re-bases `prashna_ask` onto the shared
   loop with all gates"* — but the shared gate **is** `safety_gate.ts`, so that re-base would
   **newly flag-gate the MCP door**, silently expanding the rollback pin's SECONDARY blast radius.

Being added to the DD-24 enumeration with the re-base consequence stated, before P3-B opens. Also
being added: the auth/principal asymmetry (web = Firebase session; MCP = service token +
`X-MCP-User`/`X-MCP-Key-Id`, rate limiting keyed on `keyId`, spend attributed to `userUid`) — adjacent
to G8 but not covered by it, and it affects limits keying, which parity will touch.

**Fifth guard site, also unnamed anywhere until now:** `clients/[id]/samiksha/page.tsx:27` reads the
same flag, so pulling it also takes down the SAMĪKṢĀ review tab.

---

## F-N15 — §11.4 pulse-log cross-check: NO DISAGREEMENT — and the tie-breaker's own coverage gap, declared

Charter §11.4 gives the pulse log authority over the morning report: *"if the morning report and the
pulse log disagree, the pulse log wins and the discrepancy files as a finding."* A tie-breaker that is
never consulted is not a tie-breaker, so it was consulted.

**Result: they agree, on every fact the pulse log independently observed.**

| fact | pulse log (agent-free) | this run's report |
|---|---|---|
| `origin/main` | `5aeb24c20` | `5aeb24c20` |
| production revision | `amjis-web-01673-665` | `amjis-web-01673-665` |
| production HTTP | `307` on `/` | `307` on `/`, `200` on `/login` |
| disk | 965Gi free | not claimed |

**No discrepancy to file.** Recorded as performed rather than assumed, because "the report and the
pulse log agree" is itself a claim, and it is one nobody would have checked if the conductor had not
gone and looked.

**But the tie-breaker has a coverage gap, and it must be declared rather than quietly relied upon.**
The pulse log holds **9 entries, the earliest timestamped 22:07Z** — the moment the tmux session was
recreated after the conductor crash. **It therefore does not cover the run's first hours at all**: the
entire pre-crash period, including the original Wave-1 dispatch and the work that produced the
salvaged lanes, has **no independent agent-free record**. For that window the morning report is
uncorroborated, and §11.4's arbitration mechanism simply has nothing to arbitrate with.

This is not a defect in the pulse script — it is the mechanical consequence of the sentinel and pulse
windows being recreated with the session. But it means the authority §11.4 grants is real only from
22:07Z forward, and the report must not imply otherwise. **Worth a small charter amendment for a
future run: the pulse log should survive a conductor crash (write to a path outside the tmux session's
lifecycle), or the report must state the exact timestamp from which independent corroboration begins.**

Also worth noting for the record: the pulse log correctly captured `prod revision:
amjis-web-01671-47n` at 22:37Z and `amjis-web-01673-665` at 23:07Z — i.e. **it independently observed
the production revision change this run caused**, without any agent writing to it. That is the
mechanism working exactly as designed, and it is the reason the limits-enable record can be trusted
against something other than the conductor's own word.
