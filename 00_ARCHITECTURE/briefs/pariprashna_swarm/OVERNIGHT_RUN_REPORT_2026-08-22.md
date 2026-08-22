---
artifact: OVERNIGHT_RUN_REPORT
canonical_id: PARIPRASHNA_OVERNIGHT_RUN_REPORT_2026_08_22
version: 1.0
status: FINAL — assembled incrementally through the run, closed 2026-08-23
authority: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §8
---

# Overnight run report — Paripraśna P3 + P4, night of 2026-08-22/23


## END STATE REACHED: **5 — PARTIAL, CLEAN**

**THE FLIP DID NOT FIRE.** **NO DELETION OCCURRED.** Production was never changed by this run.

Both of those are the correct outcome, not a shortfall, and the reason is a single fact that took the
night about forty minutes to establish and one line to state:

> The GitHub Actions repo secret `FIREBASE_ADMIN_CREDENTIALS` contains **one character: `-`**.

The post-deploy behaviour smoke therefore never completed a turn, the green×7 counter never started,
and the counter gates both THE FLIP and the irreversible P4-B deletion. Repairing it is a credential
operation — a §9 hard-never and a §3.3 MUST-PARK — so the run parked it for the native rather than
reaching for it. **See `MORNING_UNBLOCK_SHEET.md`: one command restarts the entire path.**

The charter anticipated this shape of night and ranks it a success (§1). What the run did instead of
flipping was drive every *other* flip precondition toward done, so the morning is one action away
from a running clock.

---

## The night in one paragraph, honestly

Ten lanes were opened or resumed. **Four independent adversarial reviews returned REFUTED**, and every
one of them was right — they caught a dispute-capture path that a single follow-up turn silently
erases, a coverage function that self-certified with a tautology and could be made to publish a
fabricated 59/60 with the full suite green, and a reader-text pipeline whose "citation gate" never
reads the reader text at all and passed nine independently-authored hallucinated readings including a
fabricated mortality claim. **The refuters are the reason this report can be trusted**, and the fact
that four of six reviewed lanes failed their first adversarial pass is the single most useful thing
the night produced.

---

## What the refuters caught — the part most worth the native's time

Recorded in order of how much it would have cost to miss.

### 1. P4-J — a reader-facing artifact that could carry fabricated astrology (PR #1499, REFUTED)

`checkCitationGate` reads only `grounding_note` and `signal.classical_basis`. **It never reads
`reader_text`.** Nine adversarial texts written independently of the lane's own fixtures all passed
with `flags: []` — including a reading about Jupiter debilitated in the 2nd house attached to a signal
about *Saturn exalted in the 7th*; invented degrees, rupas and ashtakavarga points; a **mortality /
death-timing claim**; a deterministic *"both are certain to occur"* prediction; and an **entirely
empty** reader text.

Measured discriminating power of its one real check: because `sourceKeyTerms` reduces
`"BPHS Ch.26 Sl.19"` to the term `"bphs ch"`, the mean false-accept set is **163.5 of 567 signals**;
for 11 of 25 entries it cannot tell the correct signal from more than half the catalog.

And four entries in the **already-frozen** artifact carry real factual errors (§N.5) — including
`SIG.MSR.313`, whose `reader_text` says *"seven of the nine classical planets"* while **its own
`grounding_note`, in the same object, enumerates six**. The lane's own stated safety property — *"no
entry claims a stronger hedge than its catalog confidence licenses"* — is false for 8 of 25 entries, 4
of them overclaims. Remediation dispatched: fix or **drop** the defective entries (§N.4 — 21 correct
entries beat 25 with four wrong ones), add a real hedge-band detector, rename the gate to what it
actually checks.

### 2. P4-H — the dispute survives the write and dies on the next turn (PR #1496, REFUTED)

The write lands. Then two production writers replace the column wholesale
(`metadata_json = EXCLUDED.metadata_json`, with `const metadata = isLastAssistant ? … : {}`), so every
message that is not the current last assistant message is reset to `{}`. Observed end-to-end:

```
AFTER DISPUTE   : {"feedback":{"rating":-1,"comment":"It was a layoff, not a promotion..."}}
TURN 2 verified : true | missing: []
AFTER NEXT TURN : {}
```

A reader disputes a reading, asks one follow-up question, and the dispute is gone — silently, while
`writeConversationMessages`' own read-after-write check reports `verified: true`, because it asserts
row presence and not metadata preservation. **The lane moved the silent discard; it did not remove
it.** Also: `useFeedback` is never invoked anywhere in the codebase, and **no client, mounted or not,
can transmit a dispute comment at all.**

### 3. P3-A — a §N.8 defect asserted as §N.8 compliance (PR #1495, REFUTED → remediated)

`plan_bridge.ts` said of its coverage function: *"it can only report what the map above actually
computed, so it cannot drift from it (§N.8: the signal and its detector are the same code path)."*
**"The signal and its detector are the same code path" is the definition of not having a detector.**
The refuter force-mapped 18 of 19 uncovered tools to a plausible-but-wrong URI and the function
published a **fabricated 59/60 and 39/40 with 1613/1613 green**.

This is the sharpest instance of the §N.8 class the register has recorded: the prior four confirmed
instances were signals with *absent* or *proxy* detectors; this one is a signal whose author
identified the obligation, wrote it down, and satisfied it with a tautology. **Worth considering as a
doctrinal addition to §N.8's instance list, not just a lane finding.** Remediated: a pinned-baseline
detector over all 19 uncovered names, self-verified red-then-green under the refuter's own mutation.

### 4. P4-K — survives, with the harness's own limits named (PR #1498, merged)

Spec ↔ implementation verified 1:1, no missing check — the purest §N.8 defect is *absent* here. But
its self-test is a **one-bit proof**: five of six checks were stubbed to `return []` and it still
printed *"demonstrated capable of both failing and passing."* Its leak table is narrower than the lint
it independently doubles (an adversarial fixture with `SIG.KALA.0012`, `LEL`, `RM` returned PASS). And
a correction that must not enter the record wrong: **the harness is not read-only against the live
surface** — a real run POSTs six turns and issues a direct `UPDATE conversations SET title = …`.

---

## Verified-and-corrected: two errors the run made and fixed in public

Recorded because a run that only reports others' errors is not being audited.

1. **The conductor published a false claim to the shared coordination log** — that
   `platform/migrations/` and `platform/supabase/migrations/` are separate number spaces. They are
   not: `migration_number_guard.ts` enforces **one shared sequence** and hard-fails cross-directory
   duplicates; the 29 apparent duplicates are a frozen legacy baseline. Caught by a refuter,
   re-verified against the guard's source, and **retracted in the same log at the same visibility as
   the error**, because another campaign could reasonably have chosen a colliding number from it.
2. **A killed reviewer's mutations nearly became the next reviewer's baseline.** The P3-A review
   worktree was found dirty on arrival, carrying a force-map mutation from an instance that died with
   the conductor pane — and that instance had saved a measurement of `covered_live_tools: 39`, taken
   **against its own mutated resolver**. Had it reached the conductor it would have corroborated
   exactly the fabricated number the surviving refuter was attacking. Standing correction adopted
   mid-run: every reviewer creates a fresh worktree or verifies `git status --porcelain` empty before
   measuring. **Worth adding to the worktree-isolation protocol: a review worktree is not a safe
   baseline merely because it exists at the right commit.**

---

## Governance and safety posture

- **Production ≡ main held all night**, and was verified structurally rather than assumed:
  `deploy.yml`'s real-deploy trigger is `workflow_run` restricted to `branches: [main]` and gated on
  CI success; the `pull_request` trigger is **build-only, no Cloud Run push**. A lane branch cannot
  reach production.
- **No credential was created, rotated, read, or printed.** The one secret-shaped verification
  performed was metadata-only (`gcloud secrets list` / `versions list`).
- **The native's real chart was never touched.** Every probe used the synthetic chart
  `1c826d5a-41cb-4450-b4dc-59d440e5f75a`; refuters independently confirmed the real chart UUID appears
  in lane diffs only inside comments forbidding its use.
- **No `git stash`, no operation in the shared checkout** beyond worktree creation and read-only
  commands, **no other campaign's files touched**, and a courtesy notice plus a correction were posted
  to `campaign-coordination` with per-merge lease re-reads.
- **Two production migrations with no ledger rows were found and deliberately not touched** — another
  campaign's authorized work. One precaution taken: a read-only byte-preserving backup with sha256
  recorded, so a routine `git clean` cannot destroy the only record of live SQL.


---

## THE ONE PRODUCTION CHANGE — `PARIPRASHNA_LIMITS_ENABLED` is now LIVE

**Flip precondition 3 is satisfied.** This is the only thing the run changed in production, and it
was native-authorized unconditionally (§0 ruling 3).

Serving revision is now **`amjis-web-02826-huf`** (tag `limits-canary`). NCD-8 spend caps ($2/turn,
$40/day) and the 120 req/min door limit are armed.

Two hazards were caught before they fired, both because something had been written down earlier in
the night:

1. D-012's clearance rested on *"`ANTHROPIC_API_KEY` is unprovisioned in production"* — a claim from
   a three-week-old document. **Checked live instead.** The service carries `OPENAI_API_KEY`,
   `GOOGLE_GENERATIVE_AI_API_KEY`, `DEEPSEEK_API_KEY`, `NVIDIA_NIM_API_KEY` and **no
   `ANTHROPIC_API_KEY` at all**, so `claude-opus-4-7` — the one model whose worst-case projection
   ($6.72) exceeds the $2 ceiling — cannot be dispatched.
2. The rollback-pin lane had warned that `--set-env-vars` wipes undeclared vars. Enumerated first:
   **64 env vars, 15 of them `MARSYS_FLAG_*`.** `--update-env-vars` was used. **Had that warning not
   been written an hour earlier, the obvious command would have disarmed fifteen feature flags on
   the live product in one stroke.**

**V4 is the result worth keeping** — a demonstrated-can-fail run of the limiter on live
infrastructure, with a negative control, using no credential:

```
CANARY (flag ON):   131 x 401,  9 x 429     retry-after: 56
PROD   (flag OFF):  140 x 401,  0 x 429
{"error":{"code":"LIMIT_RATE_LIMIT_EXCEEDED", ... "Rate limit of 120 requests/minute exceeded."}}
```

**Owed and explicitly NOT claimed:** the authenticated end-to-end normal-turn check and §6.4's
reject demonstration. Both need the probe harness, which is credential-blocked. Rollback is one
command, pinned, with five triggers armed (ledger D-016).

---

## Lanes — what each one honestly is this morning

**On the merge column, read this first.** This report is itself one of the PRs in the queue, so its
merge column was written while the train was still draining and **is a snapshot, not the truth**. The
authoritative state is live:

```bash
gh pr list --state all --search "pariprashna in:head" --limit 20 \
  --json number,title,state --jq '.[]|"\(.state) #\(.number) \(.title)"'
```

**The honest one-line claim per lane does not go stale — that is the column that matters**, and it is
the one this table exists for. Where the two disagree about whether something merged, believe the
command.

| Lane | PR | State | The honest one-line claim |
|---|---|---|---|
| **P4-K** narration audit | #1498 | **MERGED** | Harness built, spec↔implementation verified 1:1; **not run** — its target surface does not exist yet |
| **P3-A** plan bridge | #1495 | queued | Groundwork: adapter + binding map, zero consumers, **DD-21 not claimed**; a real pinned-baseline detector now exists |
| **P3-E** behaviour smoke | #1494 | queued | Assertion layer proven can-fail (9 targeted mutations, each isolated); **NOT a green** — no turn has ever completed |
| **P4-I** digest journal | #1497 | queued | Real DB journal row, read back independently; default-path detector added; migration re-keyed before it applied |
| **P3-C** canonical store | #1502 | CI re-running | User turns + tool parts from **retrieval pass 1 only**; synthesis-loop passes 2..N are not persisted |
| **P4-J** reader text | #1499 | CI re-running | 25 entries frozen and hashed, four catalog-contradicting entries corrected; **meaning still unverified** |
| **DD-1 battery** | #1501 | remediation in flight | 13/13 checks red-proven; **no PASS recorded**; not run against any surface |
| **P3-D prep** | #1504 | CI running | DD-24 enumeration (10 gaps) + wire↔persisted byte-agreement test, RED-proven, runs in ordinary CI |
| **P3-F rollback pin** | #1503 | CI running | Precondition 6 pre-positioned; PRIMARY command dry-run verified |
| **P4-G** window-ask | #1500 | **PARKED** | Server half built and DB-verified; **reaches no reader**, and its dispute answer reaches nothing |
| **P4-H** disputes | #1496 | **PARKED** | Endpoint writes instead of returning a hollow 200; **the write does not survive the next turn** |
| **P4-A/B/C/D, P4-E, P4-F** | — | **never opened** | Flip-gated. The flip is parked. Correctly not opened. |

**No deletion occurred. The RETIRE train never opened.** That is the correct outcome: its gate
(green×7) could not start.

---

## The three things most worth your attention today

1. **One character blocks everything.** `FIREBASE_ADMIN_CREDENTIALS` holds `-`. See
   `MORNING_UNBLOCK_SHEET_2026-08-23.md` — one command, then the cadence starts. Note the
   diagnosis worth knowing: `envOrSecret` reads the env **first**, so the placeholder actively
   *suppresses* the Secret Manager fallback designed to save this case. **A malformed secret is
   strictly worse than an absent one here.**
2. **Two production migrations have no ledger rows.** 588 and 589 are applied, untracked, and they
   removed build-protection guardrails; 589 exists because 588's `DROP FUNCTION` names were, by its
   own admission, *"guessed from the trigger names."* NIRMĀṆA's work — **check its record before
   acting.** The run backed both files up read-only and touched nothing else (D-009).
3. **`writeConversationMessages` reports `verified: true` while destroying the metadata it just
   wrote.** It asserts row presence, not preservation. Worse than first found: `persistence_stage.ts`
   passes no `lastAssistantMetadata` at all, so **every Paripraśna turn wipes the prior history's
   metadata.** Filed as DD-28/29/30 with a quarantined already-red detector on the parked P4-H
   branch. This is a candidate for CLAUDE.md §N.8's confirmed-instance list.

---

## Spend

**Estimated ~$273 of $400** (P3 ~$136/$250 · P4 ~$137/$150). **Method: per-lane token estimation.
NOT METERED. Error direction: UNDER** — conductor-session tokens are not itemized per lane and the
conductor is plausibly among the night's largest consumers. **Treat as a lower bound, not a
measurement.**

**No metered source was available to the run**, so no reconciliation was attempted — stated here
because D-010 required the report to say either what reconciliation found or that none was possible.

The P4 subtotal crossed its no-new-lanes checkpoint at ~$105 and **no new P4 lane was opened after
that point**; in-flight lanes drained to their natural close, which is what gating on *opening*
rather than *spending* is designed to permit. **No budget transfer between subtotals was requested
or authorized** — D-010's test requires a P3-critical-path task blocked *purely* on its subtotal, and
P3's blocker was a credential, not money.

---

## Governance posture at close

- **Production ≡ main** held all night and was verified structurally, not assumed: `deploy.yml`'s
  real-deploy trigger is `workflow_run` restricted to `main` and gated on CI success; the
  `pull_request` trigger is build-only with no Cloud Run push. A lane branch cannot reach production.
- **No credential was created, rotated, read, or printed.** The only secret-shaped operations were
  metadata reads (`gcloud secrets list` / `versions list`) and an IAM policy read.
- **The native's real chart was never touched.** Every probe used `1c826d5a-…`; refuters confirmed
  independently that `482012f1-…` appears in lane diffs only inside comments forbidding its use.
- **No `git stash`**, no operation in the shared checkout beyond worktree creation and read-only
  commands, **no other campaign's files touched**. Three entries posted to `campaign-coordination`:
  a courtesy notice, a **public retraction of an error this run made**, and the X-6 revision
  announcement before the traffic shift.
- **A tag was NOT pushed.** `pariprashna/p3-close` and `pariprashna/p4-close` are for closes that
  actually happened; neither did. Tagging either would be exactly the unearned signal this run spent
  the night refusing.

---

## What the SECOND review wave caught — the rollback pin, and why it matters more than the lanes

The last thing the run did before closing was review its own flip-preparation artifacts. That review
produced the night's most consequential findings, because these are the documents someone will act on
**under pressure, on production, after something has already gone wrong**.

**1. The rollback pin's verification step is green-either-way for the rollback it is attached to.**
§5.2 proposes an unauthenticated probe whose "rollback succeeded" outcome is producible *only* by
`PARIPRASHNA_ENABLED` being false. But **PRIMARY** — the traffic shift the document lists first, calls
"the standard one," and whose kill criterion says to fire without a second opinion — **does not change
that flag.** The probe returns the same result before and after. So §5.2 verifies SECONDARY only, and
**PRIMARY has no functional detector at all** — while the document states in writing that *"there's no
plausible 'looks green either way' failure mode here."* That sentence is false, and it is §N.8's defect
in the single worst place to put it.

**2. A revision pin is a safety-configuration pin.** Found independently by the conductor and the
reviewer, ninety minutes apart, from opposite directions. The pin records `amjis-web-01671-47n`, which
**predates tonight's limits enablement**. Rolling back to it disarms the $2/turn and $40/day spend
ceilings and the per-user rate limits on both doors, while the operator believes they only undid the
flip. **That is a rollback command routing around a safety gate — what §9 prohibits — reached by
accident.** The document's own §3 says "read fresh, not copied from §4," which is what saves it; but
the literal revision name sits in a copy-paste table under a `<PRE_FLIP_REVISION>` placeholder, and a
tired reader at speed reads the value, not the instruction. **The generalisable rule, worth a DD entry:
a rollback runbook must diff the candidate revision's env against the current one and confirm no
`MARSYS_FLAG_*` safety flag is lost, before any traffic shift.**

**3. The "mechanism-independent kill switch" does not cover the MCP door.** `prashna_ask` has **zero**
feature-flag gating; the web door 404s when the flag is off and the MCP door stays fully live. An
operator pulling that flag believes they closed the surface; one door stays open. Worse, the plan to
re-base `prashna_ask` "onto the shared loop with all gates" would **newly** flag-gate the MCP door,
silently widening the rollback's blast radius — neither document had noticed. A fifth guard site was
also unnamed anywhere: pulling the flag additionally takes down the SAMĪKṢĀ review tab.

**4. A byte-equality headline resting on an identity invariant.** The wire↔persisted test survived
**five independent sabotages** (key reorder, nested value change, field drop, whitespace-only, extra
field), all RED, with a deep-clone control GREEN, and it runs in ordinary CI without skipping — the
guard is real. But both operands trace to **one object reference**, so it cannot fail on a value
divergence; only on a code change producing two objects. That makes it a genuine *single-source-of-
receipt invariant guard* — the right guard to have — but not "byte agreement between two derivations."
Since **CLAUDE.md §N.8 instance 3 is literally "a byte-equality claim with no byte comparison behind
it,"** this artifact above all others could not be allowed to ship that headline. The test is sound and
unchanged; the headline is being corrected.

**5. The env-var hazard was understated 4× in the document that exists to name it.** The pin said 13
`MARSYS_FLAG_PARIPRASHNA_*` vars and scoped `--set-env-vars`'s blast radius to feature flags. Measured:
**11 flags, but 44 plain env vars total** — including `DB_NAME`, `DB_USER`,
`INSTANCE_CONNECTION_NAME`, `WATCHDOG_SECRET` and all six `NEXT_PUBLIC_FIREBASE_*`. `gcloud`'s own help
says *"All existing environment variables will be removed first."*

All five are being corrected on their branches. **None of the five was a code defect** — every one was
a document or a headline asserting something the machinery underneath does not do. That is the shape
of nearly everything this night found.

---

## Independent corroboration, and the limits of it

**§11.4 makes the pulse log — an agent-free record no agent may write to — the tie-breaker over this
report.** A tie-breaker never consulted is not a tie-breaker, so it was consulted. **They agree:**
`origin/main 5aeb24c20`, production revision `amjis-web-01673-665`, HTTP 307 on `/`. No discrepancy to
file. The pulse log also **independently observed the production revision change this run caused**,
without any agent writing to it — which is why the limits-enable record can be trusted against
something other than the conductor's own word.

**But the tie-breaker has a coverage gap, declared rather than quietly relied on.** Its earliest entry
is **22:07Z — the moment the tmux session was recreated after the conductor crash.** It does not cover
the run's first hours at all. For that window this report is **uncorroborated**, and §11.4's
arbitration mechanism has nothing to arbitrate with. *Charter amendment worth making for a future run:
the pulse log should survive a conductor crash, or the report must state the timestamp from which
independent corroboration begins.*

**X-7 verified at close:** the shared checkout is exactly as found — still `6326cda7a` on `main`, with
its pre-existing untracked set intact. The two unrecorded migrations are present and byte-identical to
the read-only backups taken at 03:53 (sha256 match on both). *Observed and not acted on: NIRMĀṆA
elevation plans v3 and v4 appeared in that checkout during the night, so another campaign is writing
there concurrently. This run touched none of it.*

---

## The governance close (§7)

Performed as a batched registry write in one serialized step, under a lease announced in
`campaign-coordination` **before** the write and closed after it (X-2).

**DD-31 … DD-44 filed, plus an in-place amendment to DD-19.** Numbering was checked live rather than
predicted: `main`'s register topped out at DD-27, and **DD-28/29/30 already exist on the parked
`pariprashna/p4-h` branch** (confirmed by `git ls-remote` + `git show` that the branch has not merged),
so DD-31 was the first genuinely free number. A note is recorded in DD-36 so that whoever later merges
P4-H does not renumber them.

What the entries record: the $400 budget outcome · **the seam-compression record** · the §6.4 reject
demo · the DD-1 battery result · the deletion warrant · every surrogate park · every lane's honest
state · and seven new findings.

**The seam-compression record, quoted, because it is the one the charter singled out:**

> *"The authorization stands as granted and unexercised, not withdrawn and not consumed… **AC-15
> remains open, async, and never claimed** — no AC-15 verdict of any kind, positive or negative, was
> recorded tonight… A later negative AC-15 verdict, whenever it arrives, has a clean record to act
> against: nothing tonight forecloses it, and nothing tonight claims a compression that did not
> occur."*

Ruling 11 authorized the DD-1 battery to substitute for the native's week of use as P4's opening gate.
**The seam was never compressed, because the gate was never reached.** That is a different outcome
from the one the ruling anticipated, and the register says so rather than letting the authorization
read as if it had been used.

**The deletion warrant and its refuter panel: NEITHER EXISTS.** No deletion occurred, no census was
accepted as a warrant, no refuter panel was convened — the RETIRE train never opened. Recorded plainly
so that a later reader does not mistake the absence for an oversight.

**No tag was pushed**, and four separate entries say why.

---

## Merge discipline, verified rather than asserted

Every merge was preceded by an X-1 lease re-read against a freshly-fetched
`origin/campaign-coordination`, including the automated tail of the queue, where the lease tip is
recorded per enqueue.

**This repository squash-merges**, so a branch commit is never an ancestor of `main` — "is the branch
contained in main" is not a valid merged-check here, and was not used. Merge claims were verified by
PR state **plus content presence on `main`**:

```
charter (#1493)                      PRESENT
P4-K harness (#1498)                 PRESENT (4 files)
P3-A plan_bridge (#1495)             PRESENT
P3-A pinned-baseline detector        PRESENT (3 refs)
P3-E park record (#1494)             PRESENT
P3-E temporary diagnostic            ABSENT  (correct — it must not survive the merge)
```

That last line is the one worth having checked: a temporary secret-shape diagnostic, however carefully
written, must not reach `main`, and "the builder said it removed it" is not the same as it being gone.

---

# APPENDIX — the original in-progress skeleton follows

## End state

**IN PROGRESS** — this line is replaced at close with the §1 ranked end state actually reached.
If the flip executed, this section's first line says so. If the deletion executed, its second
line says so with the exact commit hash and the one-command revert.

## Run open

- Charter: `PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md` (landed into the repo by this
  run's own first PR — see below).
- `origin/main` at run open: `07ed2433f`.
- `origin/campaign-coordination` at run open: `47a715197`; run-open lease appended as
  `355458408` — three narrow scopes (T-P3 / T-P4-REMEMBER / T-P4-RETIRE), no collision found
  with any open lease (SALVAGE-RECONCILE closed 2026-08-22; N4-RULING closed 2026-08-23).
- Observatory: HEALTHY at run open (one pre-run 170s blind window acknowledged — ledger D-001).
- Budget ledger opened: $400 combined — $250 P3 / $150 P4.

## Lanes closed

_(appended as lanes close, each with its DD-21 observed-delivery artifact)_

## Parks and findings

_(appended as they occur)_

## Spend

_(both subtotals, updated at every watchdog cycle)_

