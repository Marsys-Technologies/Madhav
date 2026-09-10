---
campaign: PARIŚEṢA (परिशेष — "the remainder")
version: 1.1 (Fable-5 review pass: lease-conflict resolution §2.1, worktree/adoption rules §6.0, in-session topology §10)
status: PLAN-OF-RECORD — daytime autonomous execution, 2026-08-16
scope: the 71 Paripūrṇa-2 defects not yet LIVE after EKAVĀKYATĀ (of 114 real defects)
supersedes_nothing: EKAVĀKYATĀ closed CLOSED-PARTIAL; this completes it
mode: FULLY AUTONOMOUS · no human gates · PRATINIDHI holds the native's proxy
core_discipline: TWO-PASS — no code is written until a written remediation spec has
  been independently reviewed as COMPLETE against the finding's full claim
---

# PARIŚEṢA — THE REMAINDER

## §0 WHY THIS PLAN IS SHAPED DIFFERENTLY FROM EKAVĀKYATĀ

EKAVĀKYATĀ shipped 43 of 114 defects in one night with zero regressions. It succeeded
because Wave-0 lanes had **already-completed diagnoses** — the desk had read the code
and pinned file:line before the swarm started. The lanes that stalled (B-01 rebase,
A-09 TAP) stalled on *understanding*, not on typing.

**18 of the remaining 71 findings carry `DIAGNOSIS-INCOMPLETE` in the audit corpus** —
the audit honestly recorded a symptom without a traced cause. A further ~20 have a
mechanism named but no sibling-site census. Building from those directly is how rework
happens.

Therefore: **every lane passes through a five-stage pipeline, and stages 1–3 produce
documents, not code.**

```
D · DIAGNOSE   →  S · SPEC      →  R · REVIEW     →  B · BUILD  →  V · VERIFY
reproduce+     designs the      SECOND PASS:      TDD from     independent
trace to       fix, names       is the spec       the exit     re-run, then
file:line      every file,      COMPLETE?         test         live post-deploy
+ sibling      test, lint       (VERIFIER)        (red→green)
  census                        author≠reviewer
```

The REVIEW stage is this campaign's centre of gravity — it is the "review in a second
pass whether the remediation has everything required to fix the problem" gate, made
mechanical. A spec that fails review returns to S with named deficiencies; it never
proceeds to build.

## §1 SCOPE — THE 71 (verified, and already moving)

**Composition:** TIER1 10 · TIER2 32 · TIER3 22 · TIER4 7.
**Diagnosis-incomplete (18, get 2× diagnosis budget):** F-04, F-13, F-27, F-28, F-31,
F-33, F-35, F-38, F-45, F-50, F-54, F-56, F-61, F-62, F-63, F-93, F-94, F-141.

**PHASE 0 IS MANDATORY AND FIRST — RECONCILIATION.** The desk verified two facts that
change the scope before any lane opens:
- **F-01 is already fixed.** Live probe this morning: `standing_predictions_read`
  returns `is_error:false` with 3 open predictions. It is CLOSED — do not re-open it;
  write its live evidence file and mark it LIVE.
- **33 `ekv/*` branches are pushed to origin**, several of which are lanes the night
  swarm invented and the manifest does not reflect — including
  `ekv/a-25-dasha-sandhi-principal` (covers **F-25**), `ekv/b-07-nimitta-tag`
  (covers **F-68**), `ekv/b-08-ranker`, `ekv/b-09-rebuild-runbook`,
  `ekv/morning-cl00-fixes`. Three branches carry substantial unmerged work:
  `ekv/b-01-dignity-oracle` (22 ahead / 5 behind, CI_FAILED — covers **F-62**),
  `ekv/a-09-sara-kernel` (22/2, MERGED but TAP-held — covers much of CL-05/CL-06),
  `ekv/lead-dharma` (22/2 — D-01…D-08 lints + `ekv_controls.py`, covers CL-22 tooling).

Phase 0 output (conductor, ≤60 min): for each of the 71 → one of
`ALREADY-FIXED` (evidence written, drop) · `BRANCH-EXISTS` (adopt: rebase, finish,
land — do NOT restart) · `OPEN` (full pipeline). Nothing enters D-stage until its
row exists in the board.

## §2 STREAMS — SIX, BY FILE DOMAIN (exclusive leases)

Findings are grouped so each stream owns a disjoint file domain. Class labels are the
audit's (CL-nn); every finding's claim/mechanism text is read from the corpus
(`git show audit/paripurna2-evidence:pp2-audit/manifest.json`, jq by id).

### S1 · DVĀRA (gateway: registration, dispatch, pointers) — 10
`F-11 F-25 F-67 F-73` (CL-01 reachability) · `F-09 F-17 F-18 F-43 F-123` (CL-11 dead
pointers) · `F-38` (CL-19 missing existence check).
OWNS: `platform/src/lib/retrieval/registry/tool_name_bridge.ts`,
`platform-mcp/src/server.ts` + tool registration files, the `dualOutput`/pointer
helpers, `platform/src/lib/mcp/bundle_adapters.ts`,
`platform/src/app/api/mcp/primitives/**`.
Known: F-25 has a branch (adopt). F-67 = register `query_pratijna` (also unblocks the
promise rubric). CL-11's root is one shared helper defaulting `toolName='unknown_tool'`
at ~22 sites — one fix + census + lint (D-08 tests may already exist on `lead-dharma`).

### S2 · MĀTRĀ (measure: budget, counts, family parity) — 16
`F-13 F-28 F-56 F-111 F-112 F-122` (CL-05) · `F-12 F-36 F-37 F-45` (CL-06) · `F-44`
(CL-11/05) · `F-14 F-15 F-46 F-124 F-125` (CL-14).
OWNS (HOT — exclusive, one senior builder): `platform-mcp/src/lib/response_budget.ts`,
`platform-mcp/src/tools/registry_bridge.ts`. Plus `platform-mcp/src/tools/kala_views/**`.
Known root cause (desk-verified, do not re-derive): `autoDetectTrimmableSections`
(`response_budget.ts:508-536`) declares only top-level ARRAYS >10 items; `assess_*`'s
dominant sections are OBJECTS (`activating_dasha` ~62KB, `verdict_skeleton` ~43KB), so
the trimmer is structurally blind to ~70% of the payload; ships-anyway at `:280-300`,
flag at `:439`. **`ekv/a-09-sara-kernel` already implements composition for `assess_*` —
adopt and extend, do not restart.** CL-06 counts die structurally under composition
(compute at assembly); CL-14 parity becomes middleware over the Domain Charter
(already LIVE from A-07).

### S3 · SATYA (truth-telling: disclosure, tier honesty, earned signal) — 12
`F-31 F-33 F-34 F-35 F-78 F-134` (CL-13 missing disclosure) · `F-68 F-69 F-117 F-126`
(CL-08 tier leaks) · `F-47 F-48` (CL-09 earned signal).
OWNS: `platform/src/lib/retrieval/registry/layers/L4_phala/**`, `L5_mimamsa/**`,
`platform/python-sidecar/services/ph_nimitta/**`,
`platform/python-sidecar/brahmagyan/phala/muhurta.py`.
Known: CL-13's six share ONE mechanism — the disclosure branch is gated on *total
emptiness* instead of *"did we serve less/other than asked"*; one predicate change with
six beneficiaries (spec it once, apply six times, census for a seventh). F-68's tag is
`engine.py:418` (dataclass default, numerics attached unconditionally at :472/:579/:685);
`ekv/b-07-nimitta-tag` exists — adopt. F-48: `_transit_quality_for_window`
(`muhurta.py:420`) contains no transit computation and takes no `action_type`; the
in-file correct pattern is `_panchanga_quality_for_action` (:231, action-aware :303-329).

### S4 · VĀCA (speech: narration fidelity, register) — 10
`F-50 F-63 F-93 F-116 F-120 F-121 F-135` (CL-12) · `F-129 F-130 F-132` (CL-10).
OWNS: narration/template composers (`synth_chart_brief`, `kala_views/*` reading+thesis
composers, `bodha_remedies` narration, `prashna_ask` synthesis), the v3
`register`/`reading_contract` glossing module.
Known: §N.7 item 5 — every narration layer needs its own golden-value test asserting
the sentence's numbers/labels equal the cited fact row. F-93 (~6-week dāśā drift),
F-120 (drops the level-4 sandhi period), F-121 (four false bands = "not in a junction"
while one is active) are all one class: *prose re-derives instead of restating*. The
positive contrast to copy is F-137's `register`/`reading_contract` pair, already
shipping in `graha_portrait` and `judgment_query` v3.

### S5 · MŪLA (root: parameters, vocabularies, dead paths) — 12
`F-03 F-06 F-08 F-10 F-26 F-27 F-133` (CL-03 no-op params) · `F-04 F-05 F-22 F-61 F-70`
(CL-02 dead backends).
OWNS: `platform-mcp/src/tools/register_p1_aliases.ts`,
`register_p1_synthesis.ts`, capability SQL under `layers/L0_*`, `L1_ganita/**`,
`L2_bodha/**` query files.
Known: CL-03 dies to ONE generated harness — a param-parity contract test built from
each tool's JSONSchema asserting every declared parameter changes `result_hash` (or is
marked advisory). `ekv/d-02-param-parity` may exist on `lead-dharma`; adopt. CL-02 is
"real data, no consumer, and a `fallback_reason` that positively asserts the table
doesn't exist" — census every such literal against `information_schema` first.

### S6 · ĀDHĀRA (substrate: classical, corpus, governance, build-state) — 11
`F-62` (CL-20 dignity) · `F-01` (CL-17 — **verify-and-close, already fixed**) ·
`F-23 F-54 F-136` (CL-23 corpus/data debt) · `F-79 F-81 F-94 F-95` (CL-22 governance) ·
`F-139` (stale blocker reason) · `F-141` (lit-beside-error).
OWNS: `platform/python-sidecar/ga_writers/**`, `platform/python-sidecar/pipeline/
orchestrator/writers/**`, `platform/scripts/governance/**`, `00_ARCHITECTURE/**`
governance docs.
Known: F-62 — **`ekv/b-01-dignity-oracle` exists (CI_FAILED, 5 behind main): rebase and
finish; the edge case is the MT-vs-Own degree boundary and the standing ruling is
"choose the option that discloses more."** The correct source data is
`bg_dignity_reference.py`'s degree table; the L1 writer to fix is
`ga_structural_writer.py:4872-4884`; `ga_vargas_writer._compute_dignity` over-emits
(MT before Own, no degree gate) — one oracle consumed by all three. F-141 is confirmed
live (`ka_kshetra` state='lit' beside a `last_error` that literally denies promotion)
and is §N.8's own class. F-94/F-95 need the enumerated fail-closed whitelists; the
morning triage already proved the CL-00 script's own vocabulary list is the defect, not
the data — reuse that finding.

### §2.1 LEASE-CONFLICT RESOLUTION (Fable-5 review — these WOULD have collided)

The stream leases above are by *domain*; the review found four files where two streams'
findings genuinely live in one file. Resolved by **file-level split or ordered handoff**,
never by two concurrent writers:

| File | Conflict | Resolution |
|---|---|---|
| `platform-mcp/src/tools/kala_views/*` | S2 (budget: F-13 ritual, F-122 elect) vs S4 (narration: F-120/F-121 in `now.ts`, F-132 thesis in `now.ts`/`explain.ts`) | **Split by file.** S2 owns `elect.ts`, `story.ts`, `ritual.ts`, `priority.ts`, `shared.ts`. S4 owns `now.ts`, `explain.ts`, `ahead.ts`, `upaya.ts`. |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | S5 (F-10 SQL predicate) vs S4 (F-50 remedy narration, F-135 brief weaknesses) | **Ordered handoff.** S5 holds it first — its CL-03 predicate fixes are small; the moment S5's lanes in this file are VERIFIED, conductor re-leases the file to S4. S4 diagnoses/specs meanwhile (documents only). |
| `platform-mcp/src/tools/registry_bridge.ts` (HOT) | S2 owns; S1's F-38 and S3's disclosure lanes must not touch it | F-38 is built as **route-level middleware** in `platform/src/app/api/mcp/primitives/**` (S1's lease) — never in `now.ts`/bridge. S3's CL-13 predicate flips live in the L4/L5 capability files (S3's lease); if a flip is needed inside the bridge, S3 posts a spec and S2's builder applies it. |
| `platform-mcp/src/tools/register_p1_aliases.ts` | S5 (CL-03: F-03/F-06/F-08/F-26/F-27/F-133 param plumbing) vs S1 (CL-11 `dualOutput` toolName sites, ~19 in this file) | **Ordered handoff.** S1's `dualOutput` fix is one mechanical sweep — S1 goes FIRST (haiku census + one commit), then the file is re-leased to S5. Both diagnose in parallel. |

Rule: a lane that discovers its mechanism lives in another stream's file does not edit it
— it posts `PAR-<F-nn>-NEEDS-LEASE <path>` and the conductor either re-leases or routes the
build to the owning stream with the completed spec attached. Specs travel; leases don't.

## §3 THE PIPELINE — STAGE CONTRACTS (this is the plan's substance)

Each lane produces `briefs/parisesa/lanes/<F-nn>/` containing DIAGNOSIS.md, SPEC.md,
REVIEW.md, then code. **A lane may not skip a document.**

### Stage D — DIAGNOSE (sonnet, medium; 2× budget for the 18)
Required in DIAGNOSIS.md, or the stage fails:
1. **Live reproduction** — run the finding's `reproduce_cmd` verbatim; paste output;
   save raw JSON to the lane dir. If it does NOT reproduce → `ALREADY-FIXED`, write
   evidence, close the lane (this is a win, not a failure).
2. **Claim decomposition** — the finding's `claim` field broken into every distinct
   assertion it makes. (Findings routinely carry 2–4 sub-claims; a fix closing one and
   not the others is the classic partial remediation.)
3. **Mechanism to file:line** — the actual code path, read and quoted. `DIAGNOSIS-
   INCOMPLETE` in the corpus is not inherited; it is *closed here*. If it genuinely
   cannot be traced in 45 min, escalate to PRATINIDHI rather than guessing.
4. **Sibling census** — `grep`/`rg` for every other site with the same pattern. A count
   and a file:line list. (Sarvatra: the campaign's most-repeated lesson.)
5. **Blast radius** — which of the 27 CL-00 controls could this touch; which other
   lanes share these files.

### Stage S — SPEC (sonnet, medium)
Required in SPEC.md:
1. Root-cause statement, one sentence, mechanism-level (not symptom-level).
2. Files to change, each with what changes and why.
3. **Exit test**: the exact command/test, written to FAIL on today's code and PASS
   after. Name the file it lives in.
4. Sibling sites covered (from D-4) — all of them, or a written reason a site is
   excluded.
5. Recurrence guard: the lint/contract test that makes the next divergence fail closed.
6. Dependencies (other lanes, deploys, rebuilds) and rollback note.
7. Which sub-claims from D-2 each element closes — a coverage table. **Every sub-claim
   must map to something.**

### Stage R — REVIEW · THE SECOND PASS (VERIFIER; author ≠ reviewer, always)
The reviewer answers seven questions in REVIEW.md and issues COMPLETE or
INCOMPLETE-RETURN with named deficiencies:
1. Does the spec address the **mechanism** or merely the symptom?
2. Does every sub-claim from D-2 map to a spec element? (Any unmapped → INCOMPLETE.)
3. Would the exit test genuinely **fail today**? (Reviewer reasons about it; for T1
   lanes, reviewer *runs* it and confirms red.)
4. Are all sibling sites from D-4 covered, or excluded with a stated reason?
5. Is there a recurrence guard, and does it actually detect the defect class?
6. Could this regress any of the 27 controls, or another stream's lane?
7. Is anything in the spec **unverified assumption** rather than read code?

INCOMPLETE-RETURN is normal and cheap — expect ~30% first-pass return; that is the
gate working. Two returns on one lane → PRATINIDHI ruling.

### Stage B — BUILD (sonnet, medium; TDD)
Exit test first (confirm red) → implement → green → all siblings → lint added →
`git commit` in the lane worktree → push branch.

### Stage V — VERIFY (VERIFIER)
In-worktree: re-run the exit test + the finding's original `reproduce_cmd` + the CL-00
cheap subset. Post-merge/deploy: re-run the reproduce_cmd LIVE, write
`briefs/parisesa/evidence/<F-nn>_live.json`. Only then is the lane LIVE.

## §4 THE SWARM

| Role | Count | Model · effort | Charge |
|---|---|---|---|
| SŪTRADHĀRA (conductor) | 1 | sonnet · high | Phase 0 reconciliation; board + TODO; stream launch; sequencing; sole coordination writer; merge scheduling with INTEGRATOR |
| **PRATINIDHI** (human replacement) | 1 | **opus · high** | Every question/clarification/judgment a human would field. Numbered PAR-R rulings. Doctrine authority: plan §0/§3, CLAUDE.md §N, the corpus. Standing rule: *when two remediations are defensible, choose the one that discloses more.* |
| **VERIFIER** (dedicated) | 1 session, fans out sonnet sub-verifiers, owns every verdict | sonnet · high | Stage R spec reviews + Stage V verifications + gate re-runs + 15% reproduce_cmd sampling. Never authors code. Never rules — disputes go to PRATINIDHI. |
| Stream leads | 6 | sonnet · high | Own lane board, file leases, review diffs vs lease before commit |
| Builders | 3–5 per stream, ephemeral | sonnet · medium | One worktree per lane |
| Census/mechanical | 1–2 per stream | haiku · low | grep sweeps, sibling lists, evidence filing, boilerplate replication |
| INTEGRATOR | 1 | sonnet · high | **Single writer on main**: merge queue, deploy liturgy, prod-sync assertion, rollback |

Base is sonnet everywhere; opus only for PRATINIDHI (highest-leverage judgment).
Never Fable. Never opus for building.

## §5 PARALLELISM AND SEQUENCING

**Parallel by default** — six streams run concurrently; within a stream, every lane in
D/S/R stages runs concurrently (they only produce documents — zero file conflict).
**Sequential where necessary:**
- Build stages serialize on shared files via the lease board. S2's two hot files are
  one builder's, always.
- CL-13's six lanes share one predicate: spec ONCE (F-34 as the exemplar), then the
  other five are replications — cheap haiku work after one sonnet spec.
- Same pattern for CL-11 (one helper, ~22 sites), CL-03 (one generated harness),
  CL-12 (one golden-test pattern). **Exemplar-then-replicate is the cost lever.**
- S6's F-62 must land before any Ṣaḍbala-consuming lane re-tests.
- Deploys are batched (§6), never per-lane.

**Pipelined, not phase-gated:** a lane moves D→S→R→B→V as soon as its own prior stage
clears. Streams do not wait for each other. The board is the only global state.

## §6 ISOLATION, COMMITS, MERGE, DEPLOY, PROD-SYNC

0. **WORKTREE + ADOPTION RULES (Fable-5 review — a live run WOULD have tripped these):**
   - The primary checkout `/Users/Dev/Vibe-Coding/Apps/Madhav` is currently on
     `ekv/b-01-dignity-oracle-fix` with the prior session's state. **Nobody forks from the
     primary HEAD and nobody edits the primary working tree.** Do NOT rely on the Agent
     tool's `isolation:'worktree'` (it forks from the primary HEAD). Create every worktree
     explicitly: `git worktree add -b par/<stream>-<finding>-<slug>
     .claude/worktrees/par-<stream>-<finding> origin/main`.
   - `git worktree prune` at T0 (3 prunable entries exist). 23 `ekv-*` worktrees remain
     from the night run — **leave them alone** except as below.
   - Adopted `ekv/*` branches are ALREADY CHECKED OUT in ekv worktrees; git refuses a
     second checkout. **Reuse the existing worktree** for an adopted branch
     (`git worktree list` → cd there → `git fetch && git rebase origin/main`). Known:
     `ekv/a-09-sara-kernel` → `.claude/worktrees/ekv-a-09`; `ekv/a-25-…` → `ekv-a-25`;
     `ekv/lead-dharma` → `ekv-lead-dharma`; `ekv/b-01-dignity-oracle` → nested under
     `ekv-lead-shastra/.claude/worktrees/agent-a9166cfa`, AND a newer variant
     `ekv/b-01-dignity-oracle-fix` is on the primary checkout — Phase 0 decides which is
     ahead, adopts that one, and works it in a fresh worktree cut from that branch (not
     in the primary).
   - CL-00 status: `ekv/morning-cl00-fixes` (F-83 table name, F-85 vocab) and the
     Stream-D battery merged as #1310 — verify both are on `origin/main` at T0; if not,
     they are the first merge. The remaining CL-00 red (F-102/F-141 lit-beside-error) is
     IN SCOPE (S6, F-141) — build it early so the gate's baseline goes green naturally
     rather than by ruling.

1. Branch per lane: `par/<stream>-<finding>` (e.g. `par/s3-f34-horizon-disclosure`);
   worktree per lane: `.claude/worktrees/par-<stream>-<finding>`. Cut from
   `origin/main` at claim time. **Adopted branches keep their `ekv/*` name** (rebase
   onto main; never re-fork).
2. Path leases from §2's OWNS map, in `briefs/parisesa/LEASES.json` (conductor is sole
   writer). Every commit is preceded by `git diff --name-only` vs lease; a violation
   fails the lane, not the file.
3. One file per writer, always. Lane docs live in that lane's own directory. Stream
   ledgers are lead-only. The board is conductor-only.
4. **Merge cadence (daytime — tighter than the night run):** INTEGRATOR merges a batch
   when 3–5 lanes are V-verified, or every 90 minutes, whichever first. Rebase-based.
   Push to origin immediately.
5. **Deploy liturgy per batch** (non-negotiable): push main → pipeline → verify
   `_migrations_applied` delta if any migration → **assert deployed sha == origin/main
   tip** (write `deployed_main_sha` in the gate manifest; note: `catalog_version`'s
   `+r` suffix is a hash of tool names, NOT a git sha — EKV-R-2) → run CL-00 cheap
   subset → run each batch lane's live probe → write evidence → mark LIVE.
   Any red → `git revert` the merge, redeploy, quarantine the lane back to its stream.
6. Production is in sync with main after every batch, not once at the end.

## §7 PROGRESS VISIBILITY (explicit ask)

`00_ARCHITECTURE/briefs/parisesa/BOARD.md` — conductor-maintained, rewritten at every
phase transition and at least every 30 minutes:
- a per-lane table: finding · stream · stage (D/S/R/B/V/LIVE) · owner · age
- **a TODO list in checkbox form**, grouped by stream, so progress is legible at a glance
- counts: `LIVE n/71 · in-build n · in-review n · in-diagnosis n · blocked n`
- the blocked list with one-line reasons and who is deciding
Conductor also emits the same TODO snapshot into its session output at each transition.

## §8 BUDGET AND DEGRADE

Target **$450** · warn **$540** · hard cap **$650**. VERIFIER meters hourly and posts
PAR-COST markers. Degrade order (cut from the bottom; **never cut Stage R or V**):
1. All T1 (10) → 2. CL-13 disclosure six + CL-05 composition (highest user-visible
value per unit) → 3. CL-11 + CL-03 + CL-14 (single-mechanism classes, cheap once
specced) → 4. CL-12 narration goldens → 5. CL-08/CL-09 tier+earned-signal →
6. CL-02 dead paths → 7. CL-22 governance → 8. CL-23 corpus (data debt; honest
disclosure already correct) → 9. CL-10 register (needs S2's kernel).

## §9 GATE AND CLOSE

`parisesa_gate.py verify` (same shape as `ekv_gate.py`, plus a **spec-review check**:
every LIVE lane must have REVIEW.md with verdict COMPLETE). Exit 0 requires: every
claimed lane LIVE-with-evidence or honestly parked with a handoff note · lease_ok ·
exit test PASS · REVIEW COMPLETE · deployed sha == main tip · CL-00 cheap subset PASS.
Terminal marker `RUN-TERMINAL: SESSION-PARISESA-COMPLETE` only after gate exit 0 +
VERIFIER independent re-run + PRATINIDHI countersign. A partial close with honest state
is a success; a dressed-up completion is the one forbidden outcome.

*The corpus is the spec. The second pass is the discipline. The gate is the judge.*

## §10 IN-SESSION TOPOLOGY (this run is ONE interactive Claude Code session, not scripts)

The conductor IS the interactive session. Everything else is a subagent it spawns:
- Standing roles (PRATINIDHI opus · VERIFIER sonnet · INTEGRATOR sonnet) = long-lived
  background agents; the conductor talks to them with SendMessage, keeping their context.
- Stream leads = six background agents; each lead spawns its own builders/census agents.
  Prefer background agents everywhere; the conductor never idle-polls — completion
  notifications wake it. Where a fan-out is naturally pipelined (D→S→R for a class of
  siblings), a lead MAY use the Workflow tool; the Agent tool is the default.
- **Context hygiene (the in-session risk):** every agent writes its output to files under
  `briefs/parisesa/` and returns ≤15 lines. The conductor never pastes diffs or logs into
  its own context; it reads BOARD/ledgers. Standing agents are told the same.
- Progress visibility: the conductor prints the TODO snapshot (plan §7) into the session
  at every stage transition and ≥ every 30 min — that is what the native watches.
- Resumability: worktrees + pushed branches + BOARD.md are the durable state; if the
  session must be resumed, the same conductor prompt re-enters at Phase 0 step 5
  (re-read BOARD, re-spawn standing roles, re-attach to lanes by branch name).
