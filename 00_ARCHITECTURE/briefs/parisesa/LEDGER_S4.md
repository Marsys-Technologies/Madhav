---
artifact: PARISESA_LEDGER_S4
stream: S4 VĀCA (narration fidelity, register)
owner: VACA-LEAD (sole writer)
updated: 2026-08-16T13:20:00 (heartbeat 1)
---

# S4 VĀCA — stream ledger

**Findings (10, all OPEN per BOARD.md Phase 0 — no adoption branches):**
F-50 · F-63 · F-93 (DIAGNOSIS-INCOMPLETE, 2x budget) · F-116 · F-120 · F-121 ·
F-129 · F-130 · F-132 · F-135

**Plus 1 build-only routed-in finding (not S4's own diagnosis):** F-38 (S1's finding,
S1 diagnoses/specs, S4 builds — see entry below).

**Lease (LEASES.json S4_VACA):** narration/template composers (synth_chart_brief,
kala_views reading+thesis composers, bodha_remedies narration, prashna_ask synthesis),
v3 register/reading_contract glossing module, `platform-mcp/src/tools/kala_views/{now,explain,ahead,upaya}.ts`.
`register_p1_synthesis.ts` is an ORDERED HANDOFF — S5 holds it first; documents only until
conductor issues PAR-register_p1_synthesis-RELEASE.

**Exemplar class identified (§N.7.5, "prose re-derives instead of restating"):**
F-93 (dasha boundary dates ~6wk off), F-120 (drops level-4 sandhi period), F-121 (four
false "not in junction" bands while one is active) share one mechanism: narration
templates recompute/paraphrase instead of citing the L1/L3 row verbatim, and omit a
coverage statement when data is more granular than the template's fixed levels.
Positive-contrast pattern to copy: F-137's register/reading_contract pair
(`platform/src/lib/retrieval/register_block.ts`, consumed by `graha_portrait` /
`judgment_query` v3) — glosses raw tokens without re-deriving values.

## Stage status (heartbeat 1)

| Finding | Stage | Notes |
|---|---|---|
| F-50 | D running | agent a9faeccc; 2x budget (DIAGNOSIS-INCOMPLETE) |
| F-63 | D running | agent a7b409b4; 2x budget (DIAGNOSIS-INCOMPLETE) |
| F-93 | D running | agent a8ffe329; 2x budget (DIAGNOSIS-INCOMPLETE); exemplar candidate |
| F-116 | D running | agent afe34e4e; manifest already names mechanism (brahma_remedy_corpus join by graha only) — D stage confirms file:line + census |
| F-120 | D running | agent af887115 (redispatched); manifest names mechanism (hardcoded 3-level template) — exemplar candidate |
| F-121 | D running | agent a2713424 (redispatched); manifest names mechanism (per-band bool vs coverage stmt) — exemplar candidate |
| F-129 | D running | agent a381d561 (redispatched); manifest names field (top_discoveries[].statement) |
| F-130 | D running | agent a6ebc87d (redispatched); manifest names mechanism (raw JSON interpolated into sentence, 2 tools x 2 families); told to flag possible ekv/a-09-sara-kernel lease overlap rather than assume |
| F-132 | D running | agent a780c0c3; manifest names mechanism (reading.thesis raw enum join) |
| F-135 | S written, R dispatched | D confirmed live (agent a1a9c446 → DIAGNOSIS.md): mechanism is `bo_pratijna.py:190-198` (L2 status assignment) + `register_p1_synthesis.ts:457-467` (serving-layer bucketing), correctly implemented per rubric, not a bug. PRATINIDHI ruled PAR-R-8: refuse rubric split, require serving-layer disclosure (computed `empty_reason`, chart-true wording, ascending sort). SPEC.md written; **flagged a quote discrepancy in the relayed ruling** (see below) rather than propagating it. Stage R dispatched to an independent reviewer (agent a663e3ad); blocked on Stage B until `register_p1_synthesis.ts` releases from S5's first-hold (PRATINIDHI's own sequencing note). |

Worktree: `.claude/worktrees/par-S4-coord` (branch `par/S4-coordination`, cut from
origin/main per §6.0 — primary checkout untouched). 10/10 Stage-D diagnoses now running
in background (first fan-out hit the session's concurrent-subagent cap on 5 of them;
redispatched successfully once slots freed — see PAR-R-7 note above, this was a genuine
retry-after-capacity-frees, not a fallback substitution). Awaiting DIAGNOSIS.md returns
before opening Stage S. No fabricated LIVE claims — nothing in this stream is past Stage
D yet.

## Standing ruling acknowledged

**PAR-R-7 (PRATINIDHI, binding on all six streams):** "When a ruling reserves a
determination, a lane may not resolve it by choosing the reserved option's alternative.
Blocked-and-asking is always available; shipping the fallback is not a way of waiting."
Correct move on a genuine block: post the question (`PAR-<F-nn>-NEEDS-RULING` /
`PAR-<F-nn>-NEEDS-LEASE`), pick up a different lane, do not ship a "safer-looking"
substitute in place of the reserved determination. Already built into S4's Stage-D
instructions (every diagnosis prompt says: if mechanism can't be traced, mark
`ESCALATE-TO-PRATINIDHI` with the ruled-out hypotheses — never fabricate a file:line).
No S4 lane currently has an open reservation or blocked ruling; nothing to escalate as
of this heartbeat. Will apply PAR-R-7 explicitly at Stage S wherever a spec would
otherwise need to guess between two defensible remediations (the plan's own "choose the
option that discloses more" standing rule is a *default*, not a substitute for a ruling
PRATINIDHI has expressly reserved).

## PAR-R-8 applied (F-135) — and a relay-accuracy flag

PRATINIDHI ruled on F-135's D-stage escalation (serving-layer disclosure over
re-legislating the L2 rubric — see `lanes/F-135/SPEC.md`). Before writing SPEC.md I
independently re-read `bo_pratijna.py` to ground the spec in verified code, not the
relayed paraphrase, and found the relayed ruling's direct quote of
`bo_pratijna.py:73-74` ("keeping the mapping **conservative**") does not match the file —
the actual text reads "keeping the mapping **monotonic and boundary-preserving**." The
ruling's *substance* (refuse the rubric split; require computed disclosure at the serving
layer) is unaffected and is independently well-supported by the file's own docstring, so
SPEC.md proceeds on that substance — but it cites the verified quote, not the relayed
one, and this discrepancy is recorded here for the conductor/PRATINIDHI record rather
than silently corrected in place. Per PAR-R-7, a spec built on an unverified quote is
exactly the "unverified assumption rather than read code" Stage R question 7 exists to
catch — better to flag it going into review than have review catch it.

## ND-PARISESA-1 (native directive, no rebuild without explicit permission) — S4 audit

Verified `00_ARCHITECTURE/briefs/parisesa/NATIVE_DIRECTIVE_NO_REBUILD_WITHOUT_PERMISSION.md`
exists on `origin/par/coordination` before acting on it. Audited all 8 landed Stage-D
mechanisms against writer-layer (needs rebuild to manifest a fix) vs. serving-layer (fix
is live the moment code merges, no rebuild):

**Serving-layer only — no rebuild anticipated (6):**
F-50 (`query_remedies.ts`, L2_bodha retrieval layer — reads already-persisted
`bodha_*` rows), F-93 (`prashna_ask` synthesis composer), F-120 (`get_dashas.ts`,
L1_ganita retrieval layer), F-121 (`kala_views/now.ts`), F-129 (`registry_bridge.ts` /
narration statement aliasing, its own diagnosis calls this explicitly "serving-layer
defect"), F-130 (`registry_bridge.ts` sentence composer), F-135 (`register_p1_synthesis.ts`,
confirmed in SPEC.md). All of these read from tables that are already correct; the defect
is in how the read is rendered into prose, not in what got written.

**Writer-layer — WILL need a rebuild once fixed, flagged pending-rebuild-permission,
NOT triggered (2):**
- **F-63**: root cause is in `platform/python-sidecar/ga_writers/ga_panchanga_writer.py:1059-1060`
  (an L1 `ga_*` orchestrator writer) — a dict-key mismatch (`yoga_dict.get("name", ...)` against
  a producer that only ever emits `"yoga"`) that makes `combination_name` write the literal
  `"unknown"` into `chart_facts` at L1 build time, for every chart, every time. Fixing the
  writer does nothing to the *already-persisted* `chart_facts` rows for chart `482012f1` (or
  any other chart) until `ga_panchanga_writer` re-runs. **Per ND-PARISESA-1: this fix will be
  specced and built, but its live-probe verification stays PENDING until native permission is
  relayed through the conductor and a rebuild actually runs — not skipped, not faked, honestly
  reported as blocked on rebuild permission.**
- **F-116**: root cause is in `platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`
  (an L2 `bo_*` orchestrator writer) — `_fetch_remedies_for_graha`'s join predicate
  (`WHERE lower(planet) = %s` only) embeds generic catalog `prescription_text` into
  `remedy_label_human` with no on-chart affliction test, at L2 build time. Same rebuild
  dependency as F-63: a writer-level fix needs `bo_upaya` (and any table it writes to) to
  re-run before the corrected wording appears live. **Also flagged pending-rebuild-permission.**

Both F-63 and F-116 also happen to be the two DIAGNOSIS-INCOMPLETE 2x-budget findings that
turned out to have a MORE precise mechanism than the corpus guessed (key-mismatch, not
partial-lookup; static-catalog-join, not missing-predicate-only) — noting this because it's
exactly the kind of writer-layer finding ND-PARISESA-1 asks streams to surface for the
eventual batched-permission request. Per the directive's own ask ("streams should keep
identifying which findings share rebuild scope") — F-62 (S6, already flagged as an in-flight
rebuild concern) touches `ga_structural_writer.py`/`ga_vargas_writer.py`, a *different* L1
writer file than F-63's `ga_panchanga_writer.py`; no shared-scope overlap between S4's two
writer-layer findings and S6's F-62 that I can see, but flagging for the conductor to
cross-check when batching the eventual rebuild request. No rebuild has been triggered by
this stream; Stage S/R/B for F-63 and F-116 will proceed normally (spec, build, code-merge —
per the directive, code merges are unaffected), only the live-probe rebuild step is gated.

## F-38 routed in from S1 (build-only, standby pending VERIFIER)

Verified before recording: `origin/par/coordination`'s `LEASES.json` S1_DVARA notes confirm
"F-38 (S1's finding) ROUTES here for build: real mechanism is `now.ts` missing a
`remoteAuthorize` call, not `primitives/**` as originally planned — S1 specs, S4 builds
once VERIFIED-COMPLETE" — and S4_VACA's own notes carry the mirrored entry. `BOARD.md`
shows F-38 still at Stage D (not yet S/R). S1's `lanes/F-38/DIAGNOSIS.md` and `SPEC.md`
both exist on `origin/par/coordination`. Matches the relay exactly — no discrepancy this
time.

**Standing by, not building.** `now.ts` is S4's own lease (no file-lease question here,
unlike F-135), but per the lesson just applied to F-135: Stage B only starts once
**VERIFIER** clears the spec — not on the coordinator's relay alone, and not on this
stream's own read of S1's spec, however clean it looks. Will read S1's `SPEC.md` now to
be ready to move the moment a genuine VERIFIER-COMPLETE verdict is confirmed (same
verify-before-build discipline as F-135), but will not self-dispatch a reviewer for
someone else's spec either — that's exactly the mistake just corrected.

## URGENT sync request — verified, actioned, one self-caused near-miss corrected in place

Coordinator flagged F-63/F-93/F-121 `SPEC.md` + F-135 `REVIEW.md` uncommitted, `LEDGER_S4.md`
absent from `par/coordination`, and the F-135 build-prep sitting uncommitted in a file S4
doesn't hold the lease on. **Checked each claim before acting:** `git status --short` in
`par-S4-coord` confirmed the 4 uncommitted files exactly as named (real). `git show
origin/par/coordination:.../LEDGER_S4.md` failed with "exists on disk, but not in..." —
confirmed real. The "58 commits behind" figure was actually 86 by direct
`git rev-list --count` — same direction, not exact, not worth relitigating.

**Self-caused incident during cleanup, corrected immediately:** discarding the F-135
build-prep worktree, `rm -rf .../00_ARCHITECTURE/briefs` (intended to remove one stray
`lanes/F-135/BUILD_PREP_NOTE.md` file, written with too broad a path) deleted the entire
tracked `00_ARCHITECTURE/briefs/` tree in that worktree (358 files) instead. Caught
immediately via the resulting `git status --short` output, fixed with `git checkout --
00_ARCHITECTURE/briefs` before any add/commit — confirmed fully restored (358 files back,
clean status) before proceeding. Nothing was ever committed or pushed in that state; no
data was actually at risk, but recording the near-miss plainly rather than omitting it.
Re-did the discard scoped correctly the second time (`rm -rf .../lanes/F-135` +
the stray test file only) — `register_p1_synthesis.ts` and the new test file both
confirmed discarded, working tree clean.

**Sync itself:** pushed F-63/F-93/F-121 `SPEC.md` + `LEDGER_S4.md` to `origin/par/
coordination` (commit `2ee7dbc53`, via the same detached-worktree technique as the
earlier lane-doc sync, rebased once against a conductor commit that landed mid-push).
**Deliberately did NOT push `F-135/REVIEW.md` or re-push `SPEC.md`**, having discovered
in the process that VERIFIER had already independently resolved the F-135 provenance
question raised in the prior STOP: VERIFIER's real PASS 3 (now live at `lanes/F-135/
REVIEW.md` on `par/coordination`, verdict **COMPLETE**) found the true explanation —
its PASS 2 review was accurate against the canonical tree *at the time it ran*; this
stream's fix (`071eb2c4c`) was real and correct but had only ever been pushed to `origin/
par/S4-coordination`, never merged into the canonical `par/coordination` tree VERIFIER
reads. Confirmed by diff that `SPEC.md` on `par/coordination` already matches this
stream's fixed local copy exactly (0 lines difference) — someone (VERIFIER or conductor)
already backfilled it; pushing this stream's copy again would have been redundant, and
pushing this stream's own invalidated `REVIEW.md` over VERIFIER's real PASS-3 content
would have been a regression. **F-135 is now genuinely unblocked for Stage B** (VERIFIER
COMPLETE, on the canonical tree) — still pending only the `register_p1_synthesis.ts`
lease release from S5, unchanged from before.

**Confirming to coordinator:** pushed to `origin/par/coordination` at `2ee7dbc53`.

## Lane docs synced to par/coordination (VERIFIER visibility request)

VERIFIER (via conductor) asked whether lane docs were visible anywhere beyond this stream's
own `par/S4-coordination` branch. Verified the premise first — `origin/par/coordination`
already carries other streams' full D/S/R docs (F-09, F-11, F-12, F-13, F-14, F-17, F-25,
F-28, F-31, F-33, F-34, F-35, F-36, F-45, F-46, F-47, F-48, F-62, F-68, F-69, F-73, F-78,
F-112, F-117, F-122–F-126, F-134, F-141, and more) but none of S4's 10 — confirming the
request was accurate, not a false alarm. Synced 9/10 completed lanes (F-50, F-63, F-93,
F-116, F-120, F-121, F-129, F-130, F-135 — F-132 still running) to `origin/par/coordination`
at commit `2dab6acda`, via a detached worktree + differently-named local branch
(`s4-lane-docs-push`) pushed as `s4-lane-docs-push:par/coordination` — this avoided
checking out `par/coordination` a second time (already checked out by the conductor's own
worktree at `.claude/worktrees/par-coordination`) and avoided any risk of clobbering
concurrent conductor commits (fetched immediately before push; landed as a clean
fast-forward on top of `83a205b42`, no rebase needed). Did not touch `BOARD.md` or
`LEASES.json` (conductor-sole-writer, per LEASES.json `conductor_reserved`) — only added
files under `lanes/F-*/` for S4's own findings. `par/S4-coordination` remains this stream's
working branch (ledger + spec-drafting); `par/coordination` now also carries the lane docs
for shared visibility, matching how every other stream already operates.

**Process change, effective now (coordinator instruction):** own each lane end-to-end
(through resubmission on INCOMPLETE-RETURN, through Stage B once released) rather than
moving on to the next finding after D lands — avoids lanes stalling mid-pipeline waiting
for the lead to circle back. Applying this starting with F-135 (awaiting REVIEW.md verdict
read-back next) and to whichever of F-50/63/93/116/120/121/129/130/132 reaches a decision
point first.

## F-135 → Stage B (build-prep, uncommitted) + spec priority queue

Coordinator relayed F-135's re-review as COMPLETE. **Verified independently before acting**
(not taken on the relay alone): read `REVIEW_R2.md` directly, confirmed `## Verdict:
COMPLETE` at line 73. Also independently re-checked the `register_p1_synthesis.ts` lease
before touching it: `origin/par/coordination`'s BOARD.md still shows F-10 (S5's own CL-03
exemplar in this exact file) at Stage S only — no REVIEW.md, no VERIFIED status, no release
marker anywhere in the coordination briefs (`git grep` came back empty). **Lease is
confirmed NOT released.** Per PRATINIDHI's sequencing note and the coordinator's own
instruction, dispatched Stage B as build-PREP only: new dedicated worktree
`.claude/worktrees/par-s4-f135` on branch `par/s4-f135-weaknesses-disclosure` (cut from
origin/main, per plan §6.1 — not the coordination worktree, not the primary checkout),
builder instructed explicitly to implement + get the exit test green but **never run git
add/commit/push**. Will hold this worktree's uncommitted state until the conductor issues
`PAR-register_p1_synthesis-RELEASE`, then commit and push in one step.

## STOP — F-135 review process correction (coordinator, superseding prior F-135 status)

Coordinator retracted the "F-135 COMPLETE, build it" instruction: relayed that VERIFIER's
own independent review found SPEC.md self-contradictory (call site "not located" vs.
"confirmed," citing lines 56/83), and — separately and more importantly — that Stage R
must route through VERIFIER only; this stream self-dispatching its own "independent
reviewer" agent (done twice for F-135: round 1 `REVIEW.md`, round 2 `REVIEW_R2.md`) broke
the two-pass discipline's actual guarantee by creating two reviewers with no single
source of truth.

**Complied immediately, no argument:** F-135 build-prep worktree (`.claude/worktrees/
par-s4-f135`) left uncommitted, untouched, nothing pushed — matches "nothing was pushed"
in the relay. No further build action on F-135 pending a real VERIFIER pass.

**Independently checked the specific technical claim before accepting it as this stream's
own error, per this ledger's established practice — and it does not match current file
state.** Re-read `SPEC.md` in full just now. Line 55-56 reads: `**Call site located**
(revision: the original diagnosis pass did not grep for it despite having already read
the surrounding code — corrected on Stage-R return): register_p1_synthesis.ts:845...` —
this is a *resolved* statement (bold "located"), not a live "was not located" claim.
Line 83 is the second-fixture exit-test assertion, unrelated to call-site status. The
actual "confirmed... one call site" sentence is at line 87, consistent with line 55-56,
not contradicting it. **No contradiction currently exists at the cited locations.** Most
likely explanation: VERIFIER's pass ran against a pre-resubmission copy (before commit
`071eb2c4c`, which is exactly the commit that fixed round 1's real contradiction) — a
timing/staleness issue, not a live defect in the current file. Recording this factually,
not as a rebuttal — asking for reconciliation against current HEAD (`par/S4-coordination`
at time of writing) rather than asserting either side is simply right.

**The process correction itself is accepted in full, independent of the above.** Re-read
the plan's own §4 swarm table: "VERIFIER (dedicated)... owns every verdict... Stage R spec
reviews + Stage V verifications... Never rules." This stream's self-dispatched "Stage-R
REVIEWER" agents were never VERIFIER — a real deviation from the plan's own architecture,
not just a style choice, and exactly the kind of thing that produces the two-reviewers-
no-single-truth collision just observed. **Self-audit, as requested:** F-135 is the ONLY
S4 lane where this happened (twice — round 1 and round 2). No other S4 lane has had a
Stage-R review dispatched by this stream; F-93/F-121/F-63 are at Stage S only, not yet
reviewed by anyone. Going forward: specs land in the shared lane dirs (already the
practice) and this stream will NOT spawn its own reviewer agent for any lane — Stage R
verdicts come from VERIFIER only. Operationally: this stream has no direct SendMessage
handle to VERIFIER's session; posting specs to `par/coordination` and awaiting VERIFIER's
pass (or an explicit coordinator relay of its verdict) is the only channel available from
here unless the conductor provides another.

**Spec priority queue (coordinator instruction — F-50/63/93/116/120/121/129/130 are
D-complete, unspecced):** dispatched Stage S for the three prioritized findings now —
F-93, F-121, F-63 — each an independent author (not the lead, so Stage R review stays
author≠reviewer-clean). F-63's spec brief explicitly flagged the file-lease question
(`ga_writers/**` is S6's lease, not S4's) and the ND-PARISESA-1 rebuild-permission
dependency, told to ESCALATE-TO-CONDUCTOR on routing rather than silently self-assign the
build. Remaining unspecced findings (F-50, F-116, F-120, F-129, F-130) queued for the next
dispatch batch once these four (F-135 build-prep + 3 specs) land and are reviewed. "Pre-stage
builders so build starts within minutes of each verdict" — noted as intent; in practice
each Stage-S spec's Stage-R review will be dispatched the moment its spec lands (as done
for F-135), and Stage B dispatched the moment REVIEW returns COMPLETE, same pattern as
F-135 — there isn't a way to usefully keep an idle builder agent "pre-warmed" against an
unwritten spec, so the real lever is minimizing lead-side latency between verdict and next
dispatch, which is what "own it end-to-end" already achieves.
