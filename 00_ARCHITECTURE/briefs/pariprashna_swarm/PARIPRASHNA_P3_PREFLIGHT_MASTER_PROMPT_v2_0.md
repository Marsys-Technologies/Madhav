---
artifact: PARIPRASHNA_P3_PREFLIGHT_MASTER_PROMPT
canonical_id: PARIPRASHNA_P3_PREFLIGHT_MASTER_PROMPT
version: 2.0
status: CURRENT-FOR-EXECUTION — authored 2026-08-21 (Cowork advisory session), verified against
  `origin/main` @ 211abc463. Supersedes P2_FINAL_WRAPUP_PROMPT v1.0, which covered only Parts A–D.
  Committed 2026-08-22 (PARIPRASHNA-P3-PREFLIGHT-PART-G session) per this document's own §7 item 2
  instruction — it was authored outside the repo and delivered by chat, and had not yet been
  version-controlled. Parts A–F are CLOSED as of this commit (see the DD register and
  `campaign-coordination` for per-part evidence); Parts G (in flight, this commit is part of it)
  and H remain.
  **Deliberately NOT registered as a `CAPABILITY_MANIFEST.json` canonical entry**: a first attempt
  to register it added a `registry_disagreement` finding (`CANONICAL_ARTIFACTS_v1_0.md` doesn't
  name it) that pushed `drift_detector`'s CI-enforced count from 79 to 80, over the DVA-Ruling-4
  baseline ceiling, and CI correctly failed the PR on it. Per the established PURNATA/SAMĀPTI/
  NIḤŚEṢA precedent (see `campaign-coordination`, PARIPRASHNA-P3-PREFLIGHT-PART-G session), the fix
  is not registering the close artifact as canonical, not raising the ceiling. The file is
  committed and discoverable by path; it is intentionally not a `CAPABILITY_MANIFEST` entry.
role: >
  The complete, consolidated instruction set for closing everything that stands between the
  P2 close and P3's opening. Written to be executed cold by a Claude Code session with real
  git + network access and no memory of any prior conversation. Every fact it depends on is
  either restated here or given as a command to re-derive.
supersedes: P2_FINAL_WRAPUP_PROMPT v1.0 (additive — every part of v1.0 is carried forward here)
---

# Paripraśna — P3 Pre-Flight Master Prompt

You are resuming an autonomous build campaign mid-flight. **Read this entire document before
running a single command.** It is ordered, and several parts are sequenced against each other for
reasons that are not obvious from the file names.

---

## §0 — Orientation, and the four preconditions

### 0.1 What this is

**MARSYS-JIS** (repo `/Users/Dev/Vibe-Coding/Apps/Madhav`) is a Jyotish instrument for its native,
Abhisek Mohanty. **Paripraśna** is its conversational surface — the chat interface through which a
reading is asked for and delivered. The product bar, never softened: it must demonstrate
**beyond-acharya-grade insight** while **never exposing internal jargon, nomenclature, or taxonomy
to the reader**. Sanskrit as tradition is correct; Sanskrit as a module name in reader-facing prose
is a leak.

Production: Cloud Run `amjis-web`, region `asia-south1`, project `madhav-astrology`. Live route
`/clients/[id]/pariprashna`.

Phases P0 (IGNITION), P1 (FOUNDATION) and P2 (THE READING MADE TRUE) are **closed and tagged**
(`pariprashna/p0-close`, `p1-close`, `p2-close`). P3 (ONE ENGINE, ONE DOOR) has **not opened**. 53
lanes total; 31 merged. This document covers the pre-flight queue standing in front of P3, plus
every carried obligation that has accumulated behind it.

### 0.2 Mandatory reading, in order

1. `CLAUDE.md` (repo root) — at minimum §C (mandatory reading list), §I (operating principles
   B.1/B.3/B.8/B.10/B.11), §J (the acharya-grade standard), and **§N.8 (the Earned-Signal
   Principle)**. §N.8 is the single most load-bearing rule in this campaign: *every status, grade,
   or PASS must be computed by a detector that measures the specific claim it asserts; a signal
   without such a detector is null, not green.* When you audit any status surface, ask: "what code
   path would have to run — and fail — for this signal to correctly read false?" If none exists,
   the signal is null.
2. `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` §2 —
   the DD register, DD-1..DD-27. The most frequently consulted document in the campaign.
   **Read it from a freshly-fetched `origin/main`, not the working tree** (see 0.3).
3. `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_P2_CLOSE_REPORT_v1_0.md` — the P2 close
   record. §3 (the citation-gate determination), §4 (remedial guidance under-governed = DD-23),
   **§5 (item 4 / DD-22's full ruling and viability evidence — read this before starting Part C
   rather than re-deriving it)**, §6 (lane disposition), §7 (register changes).
4. `00_ARCHITECTURE/briefs/pariprashna_swarm/CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md`
   §7 — rules **X-1..X-7**, non-negotiable. This repo is shared with a second live autonomous
   campaign (**PARIŚEṢA-RĀTRI-V4**, running in Codex, ~21 lanes) plus a standing tracker process.
   Paripraśna broke that campaign once, on 2026-08-19, by merging PR #1341 to `main` without a
   lease.
5. `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md` — the shared checkout is never a build
   surface.

**The durable lesson behind X-1..X-7:** git worktrees isolate FILES ONLY. `main`, the governance
registries, the shared `.git`, and deploy/DB are global surfaces requiring an explicit lease. Two
campaigns can both be correctly "isolated" in worktrees and still collide.

### 0.3 Precondition 1 — fetch before you read anything as current

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git --no-optional-locks rev-parse --short origin/main
```

**Do not trust any cached ref, including `origin/main` itself, without having just run this.** On
2026-08-21, `origin/main` was observed at four different commits across a few hours purely because
different sessions fetched at different times. The shared checkout is also in **detached HEAD** and
lags `origin/main` by dozens of commits — its working-tree copy of the DD register stops at DD-11
even though DD-27 exists. Read every governance file as `git show origin/main:<path>`, never from
the working tree, unless you are inside your own freshly-cut worktree.

### 0.4 Precondition 2 — the lease, and how to verify one honestly

```bash
git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md | tail -200
```

Read the lease log from **the `campaign-coordination` branch** — never from `main`'s mirror (slow
by construction), never from the working copy (X-1). Confirm no open lease covers the paths you are
about to touch.

**Critical method note, learned the hard way on 2026-08-21.** The lease log is prose written by
agents, and it has a known failure mode: **a lease's opening entry can be present with no closing
entry, even though the work is fully merged.** A prior session correctly halted on exactly this and
burned a cycle. Before treating an unclosed-looking lease as a live lock — or before assuming it is
safe to ignore — derive the answer from git rather than from the narration, which is the same
§N.8 discipline the tracker-v2 observatory already applies to lane state:

```bash
# Did anything already merge that touches this lease's declared paths?
git log --oneline --all --since=<lease-open-date> -- <leased paths, space-separated>
# Did that commit actually land on main?
git merge-base --is-ancestor <candidate-commit> origin/main && echo LANDED || echo NOT-LANDED
```

This is the test `WORKTREE_ISOLATION_PROTOCOL` §3 already prescribes for stale-looking worktrees
("unless its owning campaign's PR is independently confirmed merged/closed"), applied to lease
entries. Note that `gh` CLI was **not available** in at least one checked environment — do not
assume `gh pr view` is on hand; plain `git log --all` + `merge-base --is-ancestor` answers the same
question against already-fetched refs.

**Known instance, resolved:** the `PARIPRASHNA-P3-PREFLIGHT-MODEL-TIER-RULING` lease's missing
closing entry was appended in the PARIPRASHNA-P3-PREFLIGHT-PART-G session (2026-08-22), citing
`9789fbf7d` / PR #1434 as the evidence it closed. Future sessions should no longer hit this false
alarm for that specific lease; the general method above still applies to any future recurrence.

### 0.5 Precondition 3 — your worktree

Never work in the shared checkout (X-4, WORKTREE_ISOLATION_PROTOCOL §1). Leave it in detached HEAD
exactly as you found it.

```bash
git worktree prune   # safe: reaps only entries whose directory is already gone.
                     # it cannot touch live work. It is NOT a substitute for `git worktree remove`
                     # on a directory that still exists.
git worktree add -b pariprashna/<lane-name> .clone/worktrees/pariprashna-<lane-name> origin/main
```

Path convention: three coexist in this repo (`.clone/worktrees/<name>`,
`.claude/worktrees/agent-<hash>`, `/private/tmp/pariprashna-<lane>`). The most recent lanes used
`.clone/worktrees/pariprashna-part-<letter>`; follow that. **Cut a separate worktree per Part** —
Parts A–F touch disjoint files, and separate worktrees keep a stall in one from blocking the
others. Remove each with `git worktree remove <path>` once its PR merges; cleanup is part of the
work, not a later hygiene pass.

### 0.6 Precondition 4 — credentials, and what you must not do with them

The production Gemini credential is **`GOOGLE_GENERATIVE_AI_API_KEY`**, consumed via
`@ai-sdk/google`'s **Developer API** — *not* Vertex AI (confirmed in `G1_F_PROVIDER_POSTURE_v1_0.md`
§4.1; the distinction matters because Vertex's enterprise data-residency/no-training guarantees do
not automatically extend to the Developer API surface). It already exists in Cloud Run env / Secret
Manager, since Gemini is the live production default.

**Do not provision a raw plaintext key into any worktree's `.env` for audit work.** Part A's
detector work needs no live key at all (see A.3). Where a genuinely live call is required, use a
**tagged Cloud Run revision at 0% traffic** plus the probe harness against the **synthetic test
chart** — never the native's real chart:

```bash
./platform/scripts/probe/ask.sh "your question here"
# Defaults to synthetic chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty).
# Mints a fresh single-use Firebase session cookie per invocation from a durable root secret —
# nothing to refresh, no token on disk. Tags every turn at source; ledger exclusion proven by
# query, not asserted. Writes an immutable JSON transcript per turn to
# platform/scripts/probe/out/ (gitignored). `probe/show.py <file>` summarises one.
```

**The proof ladder** governs what counts as evidence, and a lower rung never substitutes for a
higher one: **STATIC → REPLAY → INTEGRATION → LIVE (probe harness) → NATIVE ACCEPTANCE** (the
native's own reading; outranks everything).

### 0.7 The rule that binds every part below

**DD-21, in force from P3 onward:** *no lane may be marked closed without an observed-delivery
artifact* — a captured probe transcript, a live browser observation, or a database read showing the
capability reaching a user. **Code review, passing tests, a merged PR, and a live feature flag are
all insufficient on their own.** P2's own audit found **7 of 15 lanes** merged, flagged live, and
reported done while delivering *nothing observable to a reader* — every one of them satisfied all
four of those weaker signals. No exception is carved out for small or obviously-correct changes.

Apply DD-21 to every part of this document, including the ones that look like pure plumbing.

**DD-27, filed 2026-08-22:** the deploy pipeline has been observed running a full `Build & Deploy
Web` for a docs-only PR touching no `platform/**` path. Treat every merge to `main` — including a
governance-registry-only batch write — as a real production deployment: check what is actually on
`main` immediately before merging, announce the resulting Cloud Run revision tag per X-6, and run
the full canary discipline (§10). Do not skip this because the diff "is only docs."

---

## §1 — PART A · The adapter parameter-surface audit (blocks Parts B and D) — CLOSED

*(Full original text preserved for reference; superseded by its own closure. See DD register /
`campaign-coordination` entries around PR #1440 for the closing evidence: lease CLOSED, PR #1440
merged + deployed + live-verified, 2026-08-21.)*

### A.1 Why this is first, and a nuance most readers miss

`adapter_gemini.ts` has been caught **silently dropping outbound parameters twice**, independently:

- **DD-20** — `responseFormat: { type: 'json', schema: req.responseSchema }` was wired at
  `adapter_gemini.ts:54-56`, and that file's own comment claimed the AI SDK forwards it into
  `generationConfig.responseSchema`. It did not. The tell was a markdown ` ```json ` fence in the
  raw response: Gemini's native `responseMimeType: 'application/json'` structured-output mode never
  fences its output, so the call was demonstrably not running schema-constrained.
- **`thinking_level`** — a 2.x-era numeric `thinkingConfig.thinkingBudget` is being sent where 3.x
  models expect `thinking_level`.

**The nuance:** DD-20 is marked **CLOSED**, but read its closing text carefully. It was closed by
adding `parseAndValidateSets` (real Zod validation distinguishing "valid JSON, wrong shape" from
"no sets at all") plus an explicit repair-retry — i.e. **closed at the symptom-handling layer, not
at the adapter-wiring layer.** The underlying question ("why isn't the schema constraint reaching
the model?") may still be live. That is precisely why measuring the repair-retry fire rate matters:
if most calls need the repair retry, that call site costs roughly **2× what the model-tier table
assumes**, and the tier decision in Part B was made on the cheaper assumption.

**Therefore: assume more parameters are being dropped until audited.** Google's own docs note the
Interactions API is now GA and recommended for latest models — the adapter is likely on an older
surface.

### A.2–A.6

See the original audit's evidence trail in `campaign-coordination` (entries around PR #1440) and
the DD register for the parameter-surface enumeration, captured-payload detector, Interactions API
scoping note, and DD-20 repair-retry fire-rate measurement this part produced.

---

## §2 — PART B · The model moves (requires Part A) — CLOSED

*(PR #1442 merged + deployed + live-verified, 2026-08-21 — both new models confirmed serving real
traffic.)*

### B.1 What is already done — check before redoing it

The `PARIPRASHNA-P3-PREFLIGHT-MODEL-TIER-RULING` lease already landed (PR #1434, `9789fbf7d`):
a new `interpretation_sets` CallType + `STACK_ROUTING` entries across all 6 stacks (gemini's primary
**unchanged**), two **catalog-only** `MODELS[]` entries (`gemini-3.1-pro-preview`,
`gemini-3.7-flash`, neither wired to any live CallType), an inert `STAGED_TIER_UPGRADE_ROUTING`
const recording the pinned-fallback design, and the retirement of the
`INTERPRETATION_SETS_MODEL_ID` bypass in favour of
`getEffectiveModel(DEFAULT_STACK_ID, 'interpretation_sets', 'primary')`.

That lease explicitly recorded **"NO MODEL IS BEING MOVED."** Moving them was this part's work.

### B.2 The ruled tier table

| Work class | Primary | Fallback |
|---|---|---|
| synthesis + `interpretation_sets` | `gemini-3.1-pro-preview` | `gemini-2.5-pro` (**GA**) |
| planner + summarizer | `gemini-3.7-flash` | `gemini-2.5-flash` (**GA**) |

**Both fallbacks must be GA, never another preview.** Rationale: preview models get roughly two
weeks' shutdown notice and are replaced by *other previews*. Pinning preview-to-preview relocates
the fragility rather than removing it.

### B.4 Sequencing hazard — resolved

Today's `synthesize` rows in `llm_usage_events` were on `gemini-2.5-pro` with `computed_cost_usd:
null` (DD-25). Confirmed both new catalog models carry correct cost rates in `registry.ts` before
moving call sites onto them, and re-verified `computed_cost_usd` populates on a real post-move turn
— Part D's fix and Part B's move were treated as mutually-verifying, not independent, per this
section's original instruction.

---

## §3 — PART C · DD-22, table-in-prose block promotion — CLOSED

*(PR #1443 merged + deployed + live-verified, 2026-08-21 — all 3 data-layer acceptance criteria
confirmed live against production.)*

### C.1 The ruling — settled

**Approach (c), "annotate rather than split," is APPROVED.** Keep one block per role-shift; attach
table metadata (offset ranges + parsed structure) to the existing block; let the renderer draw a
real table from a span inside it. Zero change to `committedBlocks`' cardinality. Approach (a)
(mid-stream detection touching the streaming loop) and approach (b) (splitting blocks) were
REJECTED — see `PARIPRASHNA_P2_CLOSE_REPORT_v1_0.md` §5 for the full ruling and viability evidence.

### C.2 Acceptance criteria — all four discharged live

1. Byte-exact reconstruction. 2. Regression proof against #1399 (citations), live probe turn. 3.
Regression proof against #1400 (`facts_consumed`), live turn + DB read. 4. Proof the safety scans
ran on the full text before any split/annotation.

### C.3 Sequencing — discharged

DD-22 landed BEFORE P3-B, per the hard ordering constraint ruled in the P3-preflight amendment
session. P3-B, when it opens, must confirm DD-22 has merged (it has).

---

## §4 — PART D · DD-25, the hard precondition — CLOSED

*(PR #1441 merged + deployed + live-verified, 2026-08-21.)*

`computed_cost_usd` was null on **every** `llm_usage_events` row, for every provider and every
pipeline_stage — root-caused to `llm_pricing_versions` having zero rows since its creation
(migration 038); every `computeCost()` call threw `PricingNotFoundError`, silently caught and
returned `null`. Fixed via migration 583, seeding the table from `registry.ts`'s flat rates. A
disclosed, narrower residual (Google's tiered pricing not yet modeled) was filed separately as
**DD-26** rather than absorbed silently. Verified live: `computed_cost_usd` now populates on a real
post-fix turn, and the NCD-8 ceiling is confirmed no longer structurally inert.

---

## §5 — PART E · DD-19, the interpretation_sets usage gap — CLOSED

*(PR #1462 merged + deployed + live-verified, 2026-08-22 — first-ever `interpretation_sets` row
confirmed live, after a migration-number renumbering from 584→587 at merge-queue collision time.)*

`interpretation/worker.ts`'s `callOnce` never set a `pipeline_stage` on its `QueryRequest` — the
field `persist.ts` keys its `llm_usage_events` row on. Fixed to match how `planner`/`title` already
do it. Confirmed live: real rows now appear with real `input_tokens`/`output_tokens`/
`computed_cost_usd` for the `interpretation_sets` call site.

---

## §6 — PART F · DD-13, the mortality phrasing-scan residuals — CLOSED

*(Residual (a): PR #1465 merged + deployed + live-verified, 2026-08-22. Residual (b): investigated
and reported per PR #1467, 2026-08-22, then **closed by native ruling** the same day — see the DD
register's DD-13 entry for the full closure text: option (i) STATUS QUO selected, both residuals
now resolved, DD-13 fully CLOSED.)*

### F.2 Residual (a) — the third-sentence pairing gap — fixed

`EXTENDED_DATE_SHAPE_WINDOW = CROSS_SENTENCE_WINDOW + 1` added as a separate, narrower pass scoped
to `mortality_term_x_date_shape` only, without regressing the round-3 boundary-sweep tests.

### F.3 Residual (b) — the streaming un-send asymmetry — closed by ruling, not by code

Investigated and reported per this document's own original instruction not to resolve the tension
unilaterally. The native then ruled directly: **status quo**, kept as a disclosed, permanently
accepted limitation. See the DD register for the full reasoning and the standing review-trigger
rider.

---

## §7 — PART G · Hygiene and honest bookkeeping (in flight)

These are small, and skipping them is how the last three sessions each created work for the next
one.

1. **Append the missing lease-closing entry** for `PARIPRASHNA-P3-PREFLIGHT-MODEL-TIER-RULING` to
   `campaign-coordination` (append-only — never edit the existing entry), citing `9789fbf7d` /
   PR #1434 as the evidence it closed. — **DONE**, this session.
2. **Commit this prompt** (or its successor) into
   `00_ARCHITECTURE/briefs/pariprashna_swarm/` via your worktree + PR if it should be canonical.
   — **DONE**, this file, this session.
3. **Scope DD-23 as an investigation** — do not fix it inline. — **Already satisfied**: DD-23 was
   filed OWNED/UNDATED/investigation-only at the P2-close session and remains so; no register
   change was needed for this item.
4. **Do not hand-edit lane or phase status in `PLAN.yaml`.** Every phase entry now carries
   `status_note: "DERIVED at projection time from merged-PR evidence; never hand-set"`. The
   observatory derives state from git/`gh`/`gcloud`/filesystem ground truth; agent claims render as
   *claims*, visually distinct, never counted toward completion. Emit lane transitions through
   `tracker_emit.py` (`kind: "lane_state"`, `evidence_class: "CLAIMED"` for states with no artifact
   yet) and let the observatory derive `MERGED`/`CLOSED` independently — it flags an `anomaly` if a
   claim and the derived evidence disagree.
5. **Call `tracker-health-check` at every lane transition** (DD-11, ADVISORY). Stop the tracker
   only via `tracker-stop`, which writes an intentional-stop marker — **never raw `launchctl
   bootout`.** launchd labels are **not** isolated by `$HOME`: an "isolated" test install will boot
   out the production job.
6. **Never run bare `git status` in the main checkout** — always `git --no-optional-locks`. **`git
   stash` is banned repo-wide** (X-5) — use a WIP commit on the lane branch instead.

---

## §8 — PART H · Close and hand off (not yet started)

1. **Regenerate `PARIPRASHNA_ASBUILT_BASELINE`** — bump the minor version, re-verify every
   UNVERIFIED row live, re-date every STATIC row against the then-HEAD, move closed gaps to a dated
   CLOSED table (append-only). **The Baseline never says MUST** — if a row tempts normative
   language, that content belongs in the Architecture instead.
2. **Update the DD register** with what Parts A–G actually closed — dated, evidence-classed, and
   honest. A part that did not fully close is recorded as carried with its real state, never
   rounded up.
3. **Batch every governance-registry write into ONE serialized step** at this close, under an
   announced lease window (X-2): `CURRENT_STATE`, `SESSION_LOG`, `FILE_REGISTRY`,
   `CAPABILITY_MANIFEST`, `NATIVE_DIRECTIVES`. **Read the live version number at write time —
   never predict it.**
   - **Per DD-27: treat this batched write as a real production deploy.** Check what is on `main`
     immediately before merging, announce the Cloud Run revision tag per X-6, run the full canary
     discipline in §10 — do not skip it because the diff is docs-only.
   - Watch the `drift_detector` / `schema_validator` baselines: a prior close pushed
     `drift_detector` over its CI-enforced baseline and the correct fix was **not registering
     the close report as a canonical entry**, **not** raising the ceiling — per DVA Ruling 4,
     "raise only by ruling."
4. **Tag the close** at the merge commit that has every item above as an ancestor. Release your
   lease. Remove your worktrees.
5. **Run one combined verification turn** exercising **table + citations + interpretation sets +
   typed confidence + remedial guidance together**, at **390×844 with true CDP device metrics** —
   the state a real user actually hits. Note: the fixture-based `g-mobile.spec.ts` harness **cannot
   render `RightDock` at all**, so it cannot discharge this. Use a real browser with real device
   metrics.

---

## §9 — Opening P3

**P3 opens when Part H's tag lands.** Not before. Hold the line anyway: DD-22 must precede P3-B
(already discharged), and every additional open lane is more coordination surface in a repo already
carrying two live campaigns plus a standing tracker.

Then, in dependency order:

| Lane | Depends on | Notes that bind it |
|---|---|---|
| **P3-A** | P2-I ✓ | Unified plan type: `PipelinePlan` ↔ `VidhiPlan`, `tool_name` ↔ `primitive_id` map + CI proof. Opens first. |
| **P3-B** | P3-A | Headless loop extraction; `prashna_ask` re-based onto it with all gates. **Requires DD-22 merged first** (already true). **Per DD-24, the lane brief must ENUMERATE the web door's known gaps before propagating web-door behavior onto the MCP door, each gap marked `propagated-knowingly` or `fixed-first`.** |
| **P3-C** | P2-D | Canonical store completion (history/user turns, tool_call/tool_result/reasoning parts). |
| **P3-D** | P3-B | Door-parity contract tests. **Parity hashes the PERSISTED receipt object** — **not** the wire `receipt.define` SSE event. **Precondition: a test proving the wire event and the persisted object agree byte-for-byte on the web door must exist and be green before this lane opens.** |
| **P3-E** | — | CI post-deploy smoke, demonstrated-can-fail (PB-4 F-6). |
| **P3-F** | A+B+C+D+E | **THE FLIP** — default routing everywhere; seven consecutive green smokes (W-1). **DD-25 is a hard precondition** (already closed). |

**DD-24, binding on P3:** *parity proves sameness, not correctness.* A parity test between two doors
will happily certify both as identical when both are identically wrong — converting a tracked gap
into an untracked one. P3-D's assertion is bounded to an enumerated baseline of the web door's known
gaps, not left open-ended.

**On DD-7 (the seven-smoke hold):** it is an autonomous wall-clock wait. The conductor sleeps
between smoke runs; **any red resets the counter**; green×7 is declared by CI history, with no human
in the loop.

**On AC-15 (the human seam):** it sits between P3 and P4 and is **never recorded as passed** — only
as *"waived-as-blocking per native directive 2026-08-19; native verdict welcome asynchronously."*
It is the native's own week of daily use. No agent can close it. A negative verdict at any time
spawns a remediation wave against the then-current phase.

---

## §10 — Standing reminders

- **`NEXT_PUBLIC_PARIPRASHNA_LIVE=1` is a compile-time variable.** Setting it on a running revision
  does nothing; it must be present at `next build`.
- **Parity proves sameness, not correctness** (DD-24). **Capability without a detector isn't
  verified** (§N.8). **"Merged" is not "delivered"** (DD-21). **Every merge to `main` is a real
  deploy, even a docs-only one** (DD-27). These four are the same lesson at four different layers,
  and this campaign has been bitten by each of them separately.
- **Deploy discipline:** every deploy creates a tagged Cloud Run revision at 0% traffic → smoke
  battery against the tagged URL (demonstrated-can-fail) → traffic shift to 100% → post-shift smoke
  → any red = automatic traffic shift back + auto-triage. **Rollback is a traffic command, not a
  build.**
- **Migrations:** never *rely* on the deploy-time bulk runner to apply one blindly — author it
  surgically, **verify it actually applied**, and never edit a migration file after it has been
  applied. Migration numbers are reserved in `campaign-coordination` before authoring (X-6).
- **How this work has gone best.** The most valuable moments in this campaign were not the fixes —
  they were the times a session stopped and said *"this is bigger than the ticket assumed"* or
  *"I could not verify this, so I am not claiming it."* Every significant defect here was found by
  someone looking at real output rather than at code, and disclosed honestly rather than smoothed
  over. **The register is long because nothing was allowed to disappear. Keep it that way.**

*End PARIPRASHNA_P3_PREFLIGHT_MASTER_PROMPT v2.0 (committed 2026-08-22, PARIPRASHNA-P3-PREFLIGHT-PART-G session).*
