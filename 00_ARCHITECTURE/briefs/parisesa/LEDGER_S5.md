---
artifact: LEDGER_S5
stream: S5 · MŪLA (root: parameters, vocabularies, dead paths)
owner: MULA-LEAD (sole writer)
updated: 2026-08-16T13:xx (kickoff)
---

# S5 MŪLA — Stream Ledger

**Findings (12):** CL-03 no-op params: F-03 F-06 F-08 F-10 F-26 F-27 F-133 (7).
CL-02 dead backends: F-04 F-05 F-22 F-61 F-70 (5).

**Owns:** `platform-mcp/src/tools/register_p1_aliases.ts` (S1 CL-11 dualOutput sweep goes
first, ~19 sites — WAITING on `PAR-register_p1_aliases-RELEASE` before S5 edits it; may
diagnose/spec now), `platform-mcp/src/tools/register_p1_synthesis.ts` (S5 holds FIRST for
CL-03 predicate fixes; release to S4 once VERIFIER-passed — S4's F-50/F-135 waiting),
capability SQL under `layers/L0_*`, `L1_ganita/**`, `L2_bodha/**` query files.

**Adoption check (Phase 0):** no `ekv/d-02-param-parity` branch exists on origin (confirmed
via `git branch -a` at kickoff + BOARD.md note) — CL-03 builds from scratch, no adoption.

**Worktree:** `.claude/worktrees/par-s5-lead` on branch `par/s5-mula-lead`, cut from
`origin/main` @ `5ff46c2a0`. D/S/R stages (documents only) run in this shared worktree —
zero file conflict, each lane writes only to its own `lanes/<F-nn>/`. Build stages will get
per-lane worktrees off the same tip once specs are VERIFIER-COMPLETE.

**Lease routing update (conductor, 2026-08-16, LEASES.json pushed):**
- `L3_kala/**` query files ADDED to S5's OWNS — resolves F-26's `PAR-F26-NEEDS-LEASE` (no prior
  owner; S5 already owns 4/5 sibling CL-02 findings, natural fit, conductor's call, not a
  contested conflict). F-26 now fully S5-buildable, no handoff needed.
- **F-08 ROUTES OUT to S3**: mechanism confirmed in S3's `L4_phala` lease
  (`query_phala_calibration.ts`). S5 still writes and posts F-08's spec as normal in
  `lanes/F-08/`; S3's builder applies it once VERIFIER-COMPLETE, not an S5 builder. Track this
  distinction through Stage S/R — do not schedule an S5 build worktree for F-08.

**CORRECTED 2026-08-16 (PAR-R-4, PRATINIDHI, partial reversal of the guidance below):** the
scope-creep rule only applies to a genuinely NEW mechanism. A sibling call site of a mechanism
F-03 already diagnosed is not new work — Stage S rule 4 requires it be covered-or-excluded-with-
reason in F-03's own SPEC.md coverage table, not deferred to a handoff note. `SIBLING_DEFECTS_
OUT_OF_SCOPE.md` deleted; superseded by `lanes/F-03/SPEC.md` §4's coverage table:
`query_tantric_remedies` COVERED (in S5 lease per PRATINIDHI), `query_mantras` EXCLUDED
(`PAR-F-03-NEEDS-LEASE`, matches no S5 glob per PRATINIDHI), `query_remedies_by_planet` left
**unresolved and explicitly flagged** (`PAR-F-03-NEEDS-LEASE-CLARIFICATION`) rather than assumed
either way — PRATINIDHI's ruling named the other two explicitly but not this one, and a literal
glob check shows `register_d7_channel.ts` is flat under `layers/`, not nested in any of S5's
`L0_*/L1_ganita/**/L2_bodha/**` paths, so the in-lease call for `query_tantric_remedies` appears
to be domain-based (remedy capabilities → S5) rather than a strict path match — surfacing this
discrepancy to the conductor rather than resolving it unilaterally.

~~Original (superseded) guidance~~: F-03's 3 newly-discovered sibling defects get NO Stage-D/S/B
lane, documented as a handoff note only. This was wrong per the correction above.

**Pre-staging for the incoming build load (conductor efficiency ask, 2026-08-16):**

**FM-09 check on the ask itself first:** conductor named "F-14-routed pieces" as a priority
alongside F-10. Checked BOARD.md and LEASES.json directly — **F-14 is fully S2's own finding**
(TIER1-CORRECTNESS, Stage S, no S5 routing note anywhere in LEASES.json's `S2_MATRA` or
`S5_MULA` entries). A worktree `par-s2-f14` / branch `par/s2-f14-assess-domain-reading-parity`
already exists — that's S2's own build lane, not S5's. Most likely the conductor meant F-125's
`register_p1_aliases.ts` piece (confirmed real, routed to S5 per S4's LEASES.json note) or F-12
(the largest confirmed S2→S5 route). Not blocking on this — proceeding with what's verified
(F-10 first, then the confirmed F-12/F-36/F-37/F-45/F-117/F-33 group), flagging the mix-up
rather than guessing which one was meant.

**Worktrees pre-cut** (all `git worktree add -b par/s5-<slug> .claude/worktrees/par-s5-<f-id>
origin/main`, tip `7459f8837` at cut time, empty — no code written, Stage B has not started):
F-10, F-03 (S5's own, highest priority), F-12, F-36, F-37, F-45 (S2-routed), F-117, F-33
(S3-routed). **F-05 and F-61 deliberately NOT pre-staged** per the deprioritization ask
(F-05: TIER3, ambiguous scope call already resolved but low urgency; F-61: design fork
unresolved, would need a PRATINIDHI ruling before a builder could even start).

**On "spin up 3-5 sonnet builders ready to take assignments" — honest constraint, not
declining the ask:** this harness's Agent tool dispatches builders as ephemeral, run-to-
completion tasks (matches plan §4's own "Builders... ephemeral" line) — there is no mechanism
to hold agents idle in a standby pool waiting for a future verdict. Spinning up 3-5 agents
*now* with no VERIFIED-COMPLETE spec to build against would mean giving them either no task
(wasted dispatch) or a task before its spec cleared review (violates the no-code-before-
VERIFIED-COMPLETE rule this whole campaign is built on). What actually delivers the
"near-zero latency" outcome the ask is for: worktrees are pre-cut (done, above) so there's no
setup lag, and dispatch itself is a single tool call — demonstrated earlier this session
firing 12 parallel Stage-D agents in one batch. I'll fire each builder the moment its lane's
Stage R verdict lands, worktree already waiting; not holding idle agents in the meantime.

**F-08/F-133 timing (route to S3 to build):** noted, not yet actionable — both are still at
Stage D (F-133) with no SPEC.md posted by S5 yet. Will coordinate exact handoff timing with S3
via the conductor once each spec is VERIFIER-COMPLETE, per the existing routing note in
LEASES.json.

**UPDATE — S2's F-12/PRE_STAGE_REQUEST.md landed (2026-08-16):** confirms F-12 and F-37 share
ONE fix pattern (`get_dignity.ts`/`get_avasthas.ts`/`get_karakas.ts`/`query_yoga_catalog.ts`) —
build together in one worktree, not two. Already have separate `par-s5-f12`/`par-s5-f37`
worktrees cut; no harm, but the actual build will land in `par-s5-f12` for both findings —
`par-s5-f37` stays unused/redundant rather than getting deleted (cheap, no reason to churn git
state over it). F-36 and F-45 confirmed genuinely separate mechanisms, keep their own
worktrees as already cut.

**CORRECTION (coordinator asked to confirm F-117/F-33/F-08 "routing to S5 from S3") — F-08 is
NOT one of these.** Re-verified LEASES.json S3_SATYA notes directly: *"F-08 (S5's finding) is
inbound to S3 to BUILD once S5 posts a VERIFIED-COMPLETE spec against L4_phala."* That's S5→S3
(S5 specs, S3 builds) — the opposite direction from F-117/F-33 (S3 specs, S5 builds). Confirming
worktrees ready for F-117 and F-33 (both cut, above). F-08 doesn't need an S5 build worktree at
all — what it needs from S5 is a finished SPEC.md (still Stage D only, not yet written); S3 is
the one who should pre-stage a build worktree for F-08 once that spec clears VERIFIER, mirroring
this exact same pre-stage discipline on their side.

**Heartbeat response (conductor check, 2026-08-16, 40+min quiet period campaign-wide):** S5
active. Confirmed via fresh `git fetch origin par/coordination` — no new commits from any
stream since S5's own last push, consistent with the conductor's observation. F-10/F-03 remain
DRAFT, unpicked by VERIFIER (checked BOARD.md directly: both still show stage `S`, no verdict).
Nothing blocking S5 specifically — used the wait productively: wrote and synced two more specs
(F-04, F-22, both CL-02 repoints, both ready for Stage R) rather than sitting idle on the two
already posted. 6/12 S5 lanes now have specs (F-03, F-04, F-10, F-22 written; F-06/F-08/F-26/
F-27/F-133 correctly still waiting on F-10's harness verdict per the exemplar-then-replicate
plan; F-05/F-61 deliberately deprioritized). Picking up F-70's shared-helper spec next
(routes to S2+S4 to build, but S5 owns authoring it) as further unblocked work.

**Self-dispatched-reviewer audit (conductor process correction, binding campaign-wide,
2026-08-16 — Stage R belongs to VERIFIER exclusively, a stream's own "independent reviewer"
agent is not VERIFIER's review, caused a real verdict collision on F-135):**

Audited every S5 artifact for this failure mode:
- No `REVIEW.md` exists anywhere under S5's `lanes/` — grepped, zero hits.
- No `SPEC.md` was ever marked `COMPLETE` by S5 — both `F-10/SPEC.md` and `F-03/SPEC.md` carry
  `status: DRAFT — pending VERIFIER review (Stage R)` verbatim, unchanged since written.
- All 12 dispatched Stage-D agents this session were explicitly briefed as DIAGNOSE-role only
  (produce `DIAGNOSIS.md`, no code, no spec judgment); none was tasked with reviewing a SPEC.md
  against the Stage R seven questions or issuing a COMPLETE/INCOMPLETE-RETURN verdict.
- Grepped for any "VERIFIER-COMPLETE" / "Stage R... PASS" / "independently review" strings
  anywhere in S5's tree — the only hits are correct forward-looking references (documenting
  that VERIFIER, not S5, will do this), not a claim of one having already happened.

**Clean — S5 has not self-dispatched a Stage R reviewer at any point.** Both specs remain
genuinely unreviewed, waiting on the real VERIFIER queue. Going forward: continue posting
SPEC.md and waiting, never spin up an S5-side review agent, per the binding correction.

**Native directive ND-PARISESA-1 (no rebuild without explicit native permission, relayed via
conductor, binding campaign-wide, 2026-08-16) — S5 rebuild-scope review, all 12 lanes:**

Reviewed every S5 finding's fix shape against the directive's explicit scope (any orchestrator
`build_runs` dispatch / asset rebuild that recomputes+re-persists `chart_facts`/`chart_dashas`/
`chart_divisionals`/`bodha_*`/`kala_*`/`phala_*`/`mimamsa_*` for any chart — PRATINIDHI ruling
AND native permission both required, code merges unaffected):

| Lane | Fix shape | Rebuild-implicated? |
|---|---|---|
| F-03, F-06, F-10, F-26, F-27 | Pure serving-layer (TS query/schema fix reading pre-existing rows) | NO — verifiable live immediately post-merge, no rebuild |
| F-08, F-133 | Serving-layer SQL predicate fix reading pre-existing `phala_*` rows (route out to S3) | NO |
| F-04, F-22 | Serving-layer repoint to an existing/new capability reading an already-populated GLOBAL reference table (`reference_nakshatra`, `brahma_dasha_systems` — not chart-derived, not orchestrator-built) | NO |
| F-70 | Serving-layer read fix — `kala_field_weight_versions`/`skill`/`gof` are already populated; fix is reading them instead of hardcoding zero, not recomputing them (routes out to S2+S4) | NO |
| **F-05** | Wiring `tantric.yaml` into the *L0 Brahmagyan corpus seeder* (`bg_remedies.py`/`l0_remedy_corpus.py`) — an `ON CONFLICT`-safe global-reference upsert (§N.3), not a per-chart orchestrator `build_runs` dispatch, and `brahma_remedy_corpus` isn't in the directive's named table list | **AMBIGUOUS — flagged, not assumed exempt.** Re-seeding is still a data-layer re-persist even if it's L0-global rather than chart-scoped. Not triggering it; will ask the conductor to confirm whether L0 corpus reseeds fall inside or outside ND-PARISESA-1's scope before F-05's fix is verified live, rather than assuming either way. |
| **F-61** | Depends on which fix shape the eventual SPEC picks: (a) a **serving-layer** on-the-fly aggregation of the 6 `chart_divisionals` pointer values at read time — NO rebuild needed; or (b) a **writer-layer** fix (the L1 asset that computes `graha_saptavargaja_bala_component` changes what it persists to `chart_facts`) — directly touches `chart_facts`, explicitly named in the directive, needs a scoped rebuild of the canonical chart (`482012f1`) to verify live | **PENDING-REBUILD-PERMISSION if (b) is chosen.** Recommending option (a) in F-61's eventual SPEC specifically to avoid the rebuild gate where a serving-layer fix is equally correct — noting this as a design trade-off for whoever specs F-61, not deciding it here. Not triggering any rebuild either way. |

**Net: 10/12 lanes need no rebuild at all (pure serving-layer, verifiable live immediately after
merge). F-05 is flagged ambiguous pending conductor clarification. F-61 is flagged
pending-rebuild-permission conditionally, with a recommendation to spec it as a serving-layer
fix to sidestep the gate entirely.** No rebuild triggered by S5. Will re-flag F-61/F-05 by name
if/when their SPEC.md is written, so the eventual batched-permission request (per the
directive's "streams should keep identifying which findings share rebuild scope" instruction)
has S5's contribution ready.

**FM-09-on-PRATINIDHI catch (S5, 2026-08-16), per the broadcast that FM-09 applies to
PRATINIDHI's own rulings too:** went to `origin/par/pratinidhi-ledger` directly rather than
working from relayed summaries. Found PAR-R-4's "Lease note" states two of F-03's three
siblings "resolve to `L2_bodha/query_remedies.ts` — inside S5's lease." **Verified false**:
`L2_bodha/query_remedies.ts` registers exactly one capability (`query_remedies`, line 233/236)
and does not register any of the three siblings — the real registrations
(`query_tantric_remedies` line 1674, `query_remedies_by_planet` line 1757, `query_mantras` line
1830) are all in `register_d7_channel.ts`, matching what F-03's own Stage D diagnosis already
established independently. Confirmed three separate ways (original Stage D diagnosis, the §4a
grep done for the conductor's `query_remedies_by_planet` question, and a direct re-grep for
`name: '...'` across both files). **Did not act on either implied conclusion** (build all three
as in-lease, or flag all three NEEDS-LEASE) — per PAR-R-7, posted `PAR-R-4-FILE-CORRECTION` and
left `query_tantric_remedies` on HOLD in F-03/SPEC.md §4 rather than resolving the dispute
unilaterally. Full evidence in `lanes/F-03/SPEC.md` §4b.

**RESOLVED (conductor, 2026-08-16):** practically moot — `register_d7_channel.ts` was already
added to S5's lease post-Phase-0 specifically for F-36 + these three F-03 siblings + F-05
(LEASES.json note, per conductor). Whichever file PAR-R-4 actually meant, both are S5's — no
re-ruling needed. **F-03/SPEC.md updated: all three siblings now COVERED**, built in the same
PR as F-03's own fix (all four `register_d7_channel.ts` remedy capabilities get identical
limit/offset treatment). Earlier `PAR-F-03-NEEDS-LEASE` withdrawn — superseded by the lease
grant, not resolved unilaterally by this lane. Conductor crediting the correction in LEASES.json
for the record; verification discipline confirmed sound, no re-work needed on the SPEC beyond
flipping the three dispositions from HOLD/EXCLUDED to COVERED.

**PAR-R-7 compliance check (PRATINIDHI broadcast, binding all streams, 2026-08-16):** "a lane
may not resolve a reserved determination by choosing the reserved option's alternative —
blocked-and-asking is always available, shipping the fallback is not." Verified S5 did not
violate this: `query_remedies_by_planet` was left unbuilt in F-03/SPEC.md pending conductor
routing, not built under either guess. Grepped the 4 candidate files the conductor named
(`register_d7_channel.ts`, `L2_bodha/query_remedies.ts`, `register_p1_aliases.ts`,
`platform-mcp/src/tools/retrieval/remedy_tools.ts`) — definitive answer:
**`register_d7_channel.ts`** is the one live home (same file/pattern as the already-cleared
`query_tantric_remedies`); the `retrieval/remedy_tools.ts` registration of the same raw name is
real but sits in `DEPRECATED_MCP_TOOL_NAMES` (`deprecated_tool_gate.ts`), unconditionally gated
off the live MCP surface — confirmed dead, not a second bug site. Reported to conductor for
routing; F-03/SPEC.md §4a has the full grep table. Still not built — awaiting the routing call,
not treating "found the file" as "cleared to build."

**Incoming (no action yet) — 4 S2 findings route to S5 as build-only once their specs clear
VERIFIER (conductor, 2026-08-16):**
- **F-12, F-37, F-45** — mechanisms in `L1_ganita/**` / `register_p1_aliases.ts` /
  `register_p1_synthesis.ts` / `L3_kala` (S5's lease, incl. the L3_kala addition from F-26's
  routing). F-12/F-37 share ONE mechanism with ~20 sibling sites across the registry — S2's spec
  should cover the census; when it lands, diff it against S5's own F-04/F-22 dead-backend work
  (register_p1_reference.ts) for any overlap before building.
- **F-36** — mechanism in `register_d7_channel.ts`, now added to S5's lease. **Same physical
  file as S5's own F-05** (`queryTantricRemediesCapability`) — will very likely be touched in
  the same PR/pass as F-05 once both specs are ready. Also the same file already carrying F-03's
  4-capability CL-03 fix and the still-unrouted `query_remedies_by_planet`/`query_mantras`
  question — `register_d7_channel.ts` is turning into a genuinely hot shared file across multiple
  S5 findings (F-03, F-05, F-06, F-36) plus at least one still-unresolved cross-stream question;
  worth flagging to the conductor as a file needing its own internal sequencing note once 3+
  lanes are ready to build there, to avoid two S5 builders stepping on each other even within
  one stream's own lease.
No action required until these specs land — logged for visibility only.

**Incoming (no action yet) — F-33 routes to S5 as build-only:** conductor relayed that S3
diagnosed F-33 (pre-birth `as_of_date` silently accepted, no disclosure) with its fix inside
S5's `L1_ganita/**` lease — `get_dashas.ts`'s `ageAtDate()` has no floor/guard against
`birthDate`, `judgment_flags` never gets a pre-birth push. Confirmed both `get_dashas.ts` and
the sibling `get_tajik.ts` (`resolveVarshaYearForDate`, line 22) are real, live files inside
S5's lease. Routes to S5 as **build-only** once S3's own spec clears VERIFIER — S3 authors
D/S/R for F-33, S5 just builds. Not actionable yet; logged for when S3's spec lands.

**CL-02 census:** done, see `lanes/CL02_CENSUS.md`. Verdict: all 5 backends are real/live;
none genuinely absent. F-61 differs — missing aggregation step, not missing wiring.

## Stage log

| Finding | Class | Stage | Notes |
|---|---|---|---|
| F-03 | CL-03 | D dispatched | limit/offset no-op, register_p1_aliases.ts:1576 |
| F-06 | CL-03 | D dispatched | chart_id not in schema, register_p1_aliases.ts:1563 |
| F-08 | CL-03 | D dispatched | domain no-op, register_p1_aliases.ts:1739 |
| F-10 | CL-03 | D dispatched (EXEMPLAR) | action_class missing predicate, register_p1_synthesis.ts:902 |
| F-26 | CL-03 | D dispatched | include_lel_events unread, query_life_arc.ts |
| F-27 | CL-03 | D dispatched (2x budget, DIAGNOSIS-INCOMPLETE) | domain no-op, file:line lost to a race — must re-trace |
| F-133 | CL-03 | D dispatched | mitigations not horizon-filtered, ph_pratikara/PH-4-2 |
| F-04 | CL-02 | D dispatched | reference_nakshatra wiring gap — corpus already has full detail, formalize only |
| F-05 | CL-02 | D dispatched | tantric.yaml dead loader, register_d7_channel.ts:1720 |
| F-22 | CL-02 | D dispatched | brahma_dasha_systems wiring gap, one-URI-string fix per corpus |
| F-61 | CL-02 | D dispatched (2x budget, DIAGNOSIS-INCOMPLETE) | aggregation step never located — must trace |
| F-70 | CL-02 | D dispatched | 8x kala_views hardcode noLelCalibrationMaturity() |

**Exemplar-then-replicate plan:** CL-03's ONE generated harness (param-parity contract test
off each tool's JSONSchema, asserting every declared parameter changes `result_hash` or is
marked advisory) will be specced once against F-10 (cleanest TIER1 case, already has exact
file:line + a working reproduce_cmd with two comparable result_hashes) as exemplar, reviewed
COMPLETE by VERIFIER, then F-03/F-06/F-08/F-26/F-27/F-133 dispatched as haiku replications of
the approved spec + harness generator.

## Heartbeat log
- T0: worktree cut, ledger + census written, Stage D fan-out attempted for all 12 lanes.
  Concurrent-subagent cap (20, shared across the whole PARIŚEṢA session tree) allowed only 6
  through: F-10 (exemplar), F-03, F-06, F-08, F-26, F-27 launched successfully. F-133, F-04,
  F-05, F-22, F-61, F-70 hit "Concurrent subagent limit reached" and were NOT dispatched —
  queued for retry as slots free up (not retried immediately per tool guidance).
- T0+~2min: F-26 DIAGNOSIS.md complete, CONFIRMED-LIVE (not already-fixed). Key results:
  `L3_kala/query_life_arc.ts:39` (lel_capable:false), handler never reads
  include_lel_events (not even in its own input_schema), SQL only selects kala_jivana_parva.
  Bonus: `kala_views/story.ts:59-61,700` and `ahead.ts:826` already self-document this and
  hardcode `include_lel_events:false` as a workaround. `register_p1_synthesis.ts:678-692` is
  the one live site that forwards the user's value into the broken capability.
  **PAR-F-26-NEEDS-LEASE raised**: root-cause fix point is `L3_kala/**`, not in S5's OWNS list
  (register_p1_aliases.ts, register_p1_synthesis.ts, L0_*/L1_ganita/L2_bodha) — only the
  register_p1_synthesis.ts forwarding half is S5-ownable. Sibling count: 0 (pattern unique to
  this param, 4 real call sites total, all inspected).
  Full doc: lanes/F-26/DIAGNOSIS.md.
- T0+~2.5min: F-06 DIAGNOSIS.md complete, CONFIRMED-LIVE. Both cited file:lines match the
  corpus exactly, no drift: `register_p1_aliases.ts:1563-1573` (schema is {affliction, top_k}
  only; description literally claims "Chart-specific"), `register_d7_channel.ts:1437-1526`
  (chart_id documented "provenance logging only," never bound into SQL — table has no
  chart_id column at all). Passing chart_id client-side is hard-rejected (unrecognized_keys).
  Sibling count: 0 — isolated singleton, every other chart_id use in that file is genuinely
  bound into real WHERE predicates. register_p1_aliases.ts half waits on S1's
  PAR-register_p1_aliases-RELEASE; register_d7_channel.ts half is independently fixable now.
  Full doc: lanes/F-06/DIAGNOSIS.md.
- T0+~3.5min: F-10 (EXEMPLAR) DIAGNOSIS.md complete, CONFIRMED-LIVE — byte-identical
  election_windows for domain:health vs career, judgment_flags:[] (no disclosure).
  `register_p1_synthesis.ts` muhurtaResult query ~921-931 has no action_class predicate;
  sibling anchorResult (934-946) correctly filters `AND pa.domain=$2`. **New wrinkle beyond
  the corpus**: `_DOMAIN_TO_ACTION`/actionClass isn't computed until line 968 — AFTER
  muhurtaResult already ran — so the naive fix (just add WHERE) needs a reorder too; this goes
  straight into the exemplar SPEC. Confirmed siblings: F-27 (same shape, different file/table)
  + 1 unverified candidate (phala_mitigation_get / F-08, same alias-forward shape) flagged for
  the CL-03 harness. Full doc: lanes/F-10/DIAGNOSIS.md.
- T0+~4min: F-27 DIAGNOSIS.md complete (2x budget spent, file:line RECOVERED — no longer
  DIAGNOSIS-INCOMPLETE). result_hash byte-identical with/without domain; DB confirms 57 rows/4
  verdict classes. Root: `register_p1_aliases.ts:1849-1861` forwards domain to
  `query_calibration.ts` (L5_mimamsa), whose input_schema never declares domain and none of its
  4 SQL blocks filter on it — deeper cause: `mimamsa_calibration` table has NO domain column;
  a real fix needs `JOIN mimamsa_predictions ON prediction_id` (that table has domain, used
  correctly elsewhere e.g. query_predictions.ts:82). Bonus: limit/offset are equally silent
  no-ops in the same primitive. Does NOT share a file with F-10 but is the same defect class —
  reinforces the shared harness case. Full doc: lanes/F-27/DIAGNOSIS.md.
- T0+~5min: F-08 DIAGNOSIS.md complete, CONFIRMED-LIVE (result_hash matches corpus exactly).
  **Real fix point is NOT in S5 territory**: `L4_phala/query_phala_calibration.ts`
  (queryRemedyProgramCapability) never declares/reads `domain` — S5's own files
  (register_p1_aliases.ts:1738-1749, tool_name_bridge.ts:573) forward it correctly. **PAR-F-08-
  NEEDS-LEASE query_phala_calibration.ts** raised for S3 (L4_phala is S3's lease). Also flags a
  cross-file sibling: mimamsa_calibration_get (= F-27, L5_mimamsa) has the identical shape —
  **PAR-F-08-SIBLING-NEEDS-LEASE**, ownership of L5_mimamsa TBD (not in any stream's OWNS list
  per plan §2 — conductor should resolve). Full doc: lanes/F-08/DIAGNOSIS.md.
- T0+~6min: F-03 DIAGNOSIS.md complete, CONFIRMED-LIVE, result_hash matches corpus exactly.
  **Corpus citation corrected**: `remedy_tools.ts:171-188` is stale/retired dead code,
  unreachable from the live call path. Real bug site: `register_d7_channel.ts:1528-1608`
  (listRemediesByCategoryCapability) — input_schema never declares limit/offset, SQL has no
  LIMIT/OFFSET (1584-1591). Alias half (register_p1_aliases.ts:1570-1580) is correctly wired.
  **3 NEW sibling defects found beyond the original finding list**: query_tantric_remedies,
  query_remedies_by_planet, query_mantras — all same file/family, all reached via
  GlobalBase-limit/offset-spreading aliases, all confirmed live via the same census method. Not
  in the audit corpus's 71 — flag to conductor as bonus CL-03 catches for the harness to cover
  (or a new finding number if PRATINIDHI wants them tracked separately). response_budget.ts (S2
  HOT file) confirmed NOT implicated as a fix target. Full doc: lanes/F-03/DIAGNOSIS.md.
  **UPDATE 2026-08-16 (conductor + PRATINIDHI standing ruling): the 3 siblings are scope-creep,
  refused** — no lane opened, documented in `lanes/F-03/SIBLING_DEFECTS_OUT_OF_SCOPE.md` for a
  future campaign to pick up cold. F-03 itself proceeds to spec unaffected.
- T0+~7min: F-04 DIAGNOSIS.md complete, CONFIRMED-LIVE (board's DIAGNOSIS-INCOMPLETE label was
  stale — corpus's RESOLVED write-up re-verified accurate). `fallback_reason` still actively
  claims "No structured bg_nakshatra catalog table exists" while `reference_nakshatra` (28 rows)
  sits unused. **Correction to corpus's "one-URI-string change" framing**: unlike F-22, no
  ready-made `query_nakshatra_catalog`-style capability already exists — the fix needs one new
  small capability file targeting `reference_nakshatra`/`reference_nakshatra_pada` PLUS the
  repoint, not a pure repoint. F-22 confirmed adjacent/same-shape in `register_p1_reference.ts`.
  Full doc: lanes/F-04/DIAGNOSIS.md.
- T0+~7min: F-05 DIAGNOSIS.md complete, CONFIRMED-LIVE. Query logic itself
  (`register_d7_channel.ts:1670-1721`, queryTantricRemediesCapability) is correct and honest
  (real `empty_reason`) — bug is entirely upstream in seeding. Confirmed `l0_remedy_loader.py`'s
  `load_remedies()` has zero callers; sibling YAML files (gemstone/mantra/etc.) ARE wired through
  the real production pipeline, tantric.yaml is uniquely orphaned. **Fix dependency found**: a
  real content-quality gate (`remedy_review_queue`, `is_acceptable_tantric_source()` allow-list,
  `REQUIRED_TANTRIC_COLUMNS`) exists and must NOT be bypassed — wiring tantric.yaml in is not a
  pure data change, rows must pass this gate first. Full doc: lanes/F-05/DIAGNOSIS.md.
- T0+~7.5min: F-22 DIAGNOSIS.md complete, CONFIRMED-LIVE — worse than originally scoped: the
  `fallback_reason` doesn't just omit the structured table, it actively asserts absence
  ("confirmed absent from the migration set") contradicting the same codebase's own populated
  table. Table discrepancy resolved: `brahma_dasha_systems` (20 rows) is correct/canonical;
  `reference_dasha_systems` is a legacy/unrelated table (not the target). **Corpus's
  "one-URI-string change" claim downgraded**: `query_dasha_systems.ts` exists and is tested, but
  wiring it in is a ~20-30 line `server.tool(...)` rewrite (schema + envelope invert of
  `structured_filter_applied`/`fallback_reason` on success), not literally one line — flag
  precisely for the spec's effort estimate. F-04 confirmed adjacent/same-shape. Full doc:
  lanes/F-22/DIAGNOSIS.md.
- T0+~8min: F-61 DIAGNOSIS.md complete (2x budget spent, RESOLVED — writer located, no longer
  DIAGNOSIS-INCOMPLETE, not escalated). Confirmed every `graha_saptavargaja_bala_component` row
  chart-wide has `fact_value_num=null` + a `fact_value_jsonb` pointer to 6
  `chart_divisionals.id`s; direct SQL resolution for SUN sums to 93.75, matching claim exactly.
  **This is Confirmed Instance #5 for CLAUDE.md §N.8 (Earned-Signal Principle)** — a fact_key
  literally named "...score" that no code path ever computes, structurally identical to the
  orchestrator no-op-completion defect and the two bo_pramana_mapa flags already in that list.
  Sibling found: `vimsopaka_bala_per_graha` has the identical null-with-pointer pattern — not
  unique to saptavargaja. Fix shape flagged as informational only (PRATINIDHI's call): a small
  aggregator + re-pointing `constituent_facts_array` at real `chart_facts.fact_id`s instead of
  raw `chart_divisionals.id`s. Full doc: lanes/F-61/DIAGNOSIS.md.
- T0+~9min: F-133 DIAGNOSIS.md complete, CONFIRMED-LIVE — only 2/10 served mitigation rows
  actually overlap the requested horizon; one row (obstruction 32489, window 1966-04-08 to
  1968-09-21) predates the native's birth by ~17.8 years, matching the audit exactly. Mechanism:
  live serving path is `register_p1_aliases.ts:1781-1803` (verified clean, S5's own forwarding
  is correct) → sidecar `/api/compute/phala/outlook` →
  `platform/python-sidecar/brahmagyan/phala/outlook.py`. `_fetch_anchors` correctly threads
  date_range into a real overlap predicate; `_fetch_mitigations` calls `mitigation_map()` with
  **no date argument in its signature at all** — `mitigation.py:700-849`'s SQL has no
  date/horizon predicate, just `chart_id` + severity sort + LIMIT 100. The generic
  `trim_report.recover_via.hint` ("narrower... date_range") is itself false here since no such
  param exists on this query. **PAR-F-133-NEEDS-LEASE** raised: both the CL-03 half (add the
  predicate) and CL-13 half (disclose the gap) live entirely in
  `platform/python-sidecar/brahmagyan/phala/**`, outside S5's OWNS list. Sibling found:
  `L4_phala/query_phala_calibration.ts:330-424` shares the same `phala_mitigation` table and
  unwindowed-sort defect as F-08's `PAR-F-08-NEEDS-LEASE` — recommend conductor bundle both into
  one S3 spec/lease request. Full doc: lanes/F-133/DIAGNOSIS.md.
- T0+~10min: F-70 DIAGNOSIS.md complete, CONFIRMED-LIVE — contradiction still present today
  (kala_now_get/kala_priority_get both zero-stub calibration_maturity for the native chart while
  mimamsa_insight_get reports 57 real, internally-consistent calibration matches for the same
  chart_id). All 8 kala_views file:line sites confirmed. **PAR-F-70-NEEDS-LEASE raised for both
  S2 (elect.ts/story.ts/ritual.ts/priority.ts/shared.ts) and S4 (now.ts/explain.ts/ahead.ts/
  upaya.ts)** as expected — this finding was never S5-buildable, only S5-diagnosable per plan
  §2's "Known" line. **Recommendation to conductor**: one shared helper
  (`resolveCalibrationMaturity(chartId, dbConn)`, proposed home
  `platform-mcp/src/lib/kala_envelope.ts`) rather than 8 independent repairs — needs S2+S4
  coordination, and `kala_envelope.ts`'s own ownership needs verifying before either builds.
  Full doc: lanes/F-70/DIAGNOSIS.md.

**ALL 12 STAGE-D LANES NOW COMPLETE.** 0 ALREADY-FIXED, 0 ESCALATE-TO-PRATINIDHI needed (F-27 and
F-61 both self-resolved their DIAGNOSIS-INCOMPLETE within budget). 4 NEEDS-LEASE flags outstanding
(F-08→S3, F-70→S2+S4, F-133→S3, F-03's query_mantras→TBD + query_remedies_by_planet resolved-
pending-routing). Next: F-10 CL-03 exemplar SPEC.

- T0+~14min: **F-10 SPEC.md (CL-03 exemplar) written**, `lanes/F-10/SPEC.md`. Two parts: (1)
  F-10's own point fix — hoist `_DOMAIN_TO_ACTION`/`actionClass` above `muhurtaResult`, add a
  nullable `action_class` bind, add a `judgment_flags` entry on fallback/mismatch; (2) the
  reusable CL-03 param-parity harness — a generated test suite off each tool's own JSONSchema,
  asserting every declared non-allowlisted param changes `result_hash` between two calls or is
  registered in a new `ADVISORY_PARAMS` file with a written reason. Coverage table maps all 6
  siblings: F-27 own-spec + harness-as-guard; F-03 excluded from harness scope (own point fix
  already covers limit/offset, avoiding duplicate mechanism); F-06/F-26/F-133 flagged as
  different defect shapes not harness-coverable the same way (missing-param, unread-flag,
  missing-date-predicate respectively) — own specs needed regardless of the harness. Status:
  DRAFT, posting to VERIFIER next per Stage R (author≠reviewer).
