---
artifact: NIRMANA_ENGINE_ELEVATION_STATE
canonical_id: NIRMANA_ENGINE_ELEVATION_STATE
version: "0.6"
status: LIVE — rewritten at every packet close
campaign_id: nirmana-engine
authority: 00_ARCHITECTURE/briefs/nirmana/NIRMANA_ENGINE_ELEVATION_PROMPT_v1_0.md
runs_in: /Users/Dev/madhav-engine (branch campaign/nirmana-engine)
last_updated: 2026-09-26T19:40Z
---

# Nirmāṇa engine elevation — STATE

## Where the campaign is

**Phase A CLOSED and gate-checked (PASS). Phase B IN FLIGHT — B1 closed after a REJECT and three rounds; B2 next, carrying B1's C-4.**

| packet | title | status | review verdict | before | after |
|---|---|---|---|---|---|
| A1 | Record how long and how fast | **CLOSED** | ACCEPT_WITH_CORRECTIONS ×2 → cleared on B-1 discharge | coverage was a writer-dependent lottery (bo 0/24, ph 0/8) | **123/123 writers timed by the engine**; production rows unchanged at 0/268 and labelled so |
| A2 | Always record why it failed | **CLOSED** | ACCEPT_WITH_CORRECTIONS → **ACCEPT** on re-review | 301 empty-error records / 82 assets / 46 runs (13.25% of failures) | prospective: every terminating path now writes attributable text; proof re-run independently |
| A3 | Stop one registry change killing a whole run | **CLOSED** | ACCEPT_WITH_CORRECTIONS ×2 → **ACCEPT** | all 8 runs lost 100% of plan; Family A = 11 records / 2 runs | on the real run's own manifest: **10/10 aborted → 1/10 failed**; production **unmeasured** |
| A2b | `mark_asset_error` empty-exception hardening | **carried** (split out of A2 to keep waves disjoint) | — | latent, not inflating the 301 | — |
| A3b | Runs dispatched with no manifest at all | **carried** (split out of A3; 6 of its 8 runs) | — | 7 records / 6 runs | — |
| B1 | Cascade reads as one cause, N blocked | **CLOSED** | REJECT → ACCEPT_WITH_CORRECTIONS → **ACCEPT** | 0 of 10 blocked assets rendered correctly — **9 rendered green** | **8 of 8 render blocked**; 18 badges flip off green |
| B2 | Blocking radius, recorded | **rescoped, next** | — | DAG clean, no cycles; radius does **not** predict observed cascade | — |
| C1 | Crash, orphan and reap | not started | — | — | — |
| C2 | Stuck states | not started | — | — | — |
| D1 | Nine checks applied to the engine | not started (authored last; frozen only if the asset contract has stopped moving) | — | — | — |

## Live failure-rate figures — re-derived this session, not inherited

Every figure below was measured independently by a diagnostician against production on 2026-09-26,
read-only, with its query recorded in `measurements/`. **The inherited headline did not survive
contact with the record**, and the corrections are material:

| inherited claim | measured | verdict |
|---|---|---|
| 2,283 failed/aborted records | **2,271** (`error`=1,565 + `aborted`=706) | off by 12 |
| 1,281 cascade | **1,281** | exact |
| ~127 causal | **128** | essentially exact |
| 543 infra | **561** — the frozen-manifest family (18) was never folded in | undercounted by 18 |
| 307 silent | **301** across 82 assets, 46 runs | overcounted by 6 |
| `rows_per_second` NULL "for all 40 L0 assets" | **268 of 268, every layer** | not an L0 problem; engine-wide |
| L0 has 40 throughput rows | **39** — `bg_gochara_citation_resolution` has no row at all | one asset never recorded |
| 18 assets / 8 runs on frozen-manifest abort | **18 / 8** | exact |

**The inherited claim was also internally inconsistent:** its own four parts sum to 2,258, not the
2,283 it states. The 2,271 figure above is what the record actually holds.

**Three findings that change what the packets are:**

1. **A2 is a plumbing defect, not a capture defect.** 295 of the 301 silent records resolve to one
   message, `orphan-watchdog: run never dispatched`, that the engine *already computes one statement
   earlier* in the same function and fails to pass into the companion `build_run_assets` UPDATE.
   `build_events` and `orchestrator_noop_events` are empty for all 46 runs, so nothing else knows more.
2. **A3's 18 records are two unrelated bugs sharing an error prefix.** Family A (11 records, 2 runs) is
   the real registry-drift case. Family B (7 records, **6 of the 8 runs**) is one-off dispatch scripts
   inserting `build_runs` with no `plan_manifest` at all — there is no manifest to have drifted and none
   to re-freeze. A3 as scoped fixes 2 of 8 runs, and the report will say exactly that.
3. **A1 is mostly "stop discarding a value the engine already receives."** The frozen `WriterResult`
   already carries `duration_seconds`; `rows_per_second` has existed as a column since migration 169
   (2026-06-06) and is written by **zero** code paths.

**Two families the record blames on the engine that this repository cannot account for:**
`guardian_cleanup` (310 records) and `manual reap: …` (77 records) have **zero source hits** anywhere
in this codebase. `NOT ATTRIBUTABLE` from `madhav-engine` — an external process, ad-hoc operator SQL,
or deleted code. Material to C1, and recorded now so C1 does not start by assuming the code is here.

**One data-integrity anomaly, registered and deliberately not fixed:** 7 `build_run_assets` rows carry
`BLOCKED:` cascade text while `state='complete'`. It belongs to B1, not to A2.


## A2 — closed 2026-09-26, reviewer ACCEPT

**What landed.** One shared helper, `platform/src/lib/build/terminalizeFailedRun.ts`, mirroring the CTE
already proven in `runner.py`, with all seven call sites routed through it so the message the engine
already computes reaches `build_run_assets.error` instead of being dropped. That closes the 295-of-301
dominant defect at its source.

**What the gate changed.** The first submission was **not** accepted. It had corrected a dead predicate
(`state = 'running'`, an illegal enum value) and thereby *resurrected* logic that stamped
`"writer never reported back"` onto healthy, heartbeating assets on any run older than 30 minutes —
and its own test asserted that falsehood as correct. A confidently-wrong error is worse than the empty
one this packet exists to remove. M-5 was **deleted**, not repaired.

**Why deletion was safe, and how that was established rather than assumed.** The reviewer queried
production: `SELECT count(*) FROM build_run_assets WHERE error LIKE 'orphan-watchdog%'` returns **0**,
and M-5 never changed `state`, so any row it had ever written would still be there. It never fired once
in its life. Deleting it removes nothing the engine ever actually had.

**Proof quality.** The second proof re-inserted the deleted block and watched the two new tests fail on
the real text. The first proof had failed on `undefined` imports instead — the right conclusion for the
wrong reason. The difference is the packet's chief lesson: a proof must fail *for the reason it claims*.

**Carried to A2b, none silently absorbed:** site 2 cannot reach global (`chart_id IS NULL`) assets;
`terminalizeFailedRun` skips the asset abort when a run is already terminal, where pre-fix code aborted
unconditionally; the `vi.clearAllMocks()` mock-leak hazard is real and **still open** (a prior claim to
have fixed it was unsupported); and `asset_runner.py`'s `mark_asset_error` can still write an empty
`str(exc)` as a literal.

**One observation for a governance lane, not A2:** the test bed pins `chart_id NOT NULL` in its own DDL,
so it would not notice production drifting away from that constraint.


## A1 — closed 2026-09-26, two correction rounds

**What landed.** The orchestrator now measures its own monotonic wall-clock around its invocation of
the writer, and is the sole timing authority. `WriterResult.duration_seconds` still exists on the
frozen contract and writers may still set it — the engine simply no longer reads it. Migration 1094
adds the missing duration column; the completion write degrades gracefully when that column is absent,
and says so once per process rather than degrading silently.

**What the gate changed, twice.** The first submission summed what writers *self-reported*, so coverage
was a lottery — `bo 0/24`, `ph 0/8`, roughly 201 of 268 rows would have stayed NULL. The reviewer
established that by reading the code, and stated that had the *code* claimed that coverage rather than
the documentation, it would have been a REJECT. The second round was cleared only after a blocking
finding: the digest inventory had gone stale again for exactly A1's 37 writers, and committing a
mismatched inventory would have made the follow-up re-pin pin a **wrong** one — a knowingly-red gate
turning into a permanently-wrong receipt spine.

**The hazard that was closed pre-emptively.** Duration and rate are pinned *before* the
no-op-completion reclassification can overwrite `rows_written` with a presence-probe count from prior
runs. Pairing an inherited count with this run's near-zero duration would have produced a confident,
fabricated throughput number — the §N.8 defect class this campaign exists to remove. The reviewer
verified the ordering by reading every line between pin and write, across both rounds.

**Honest partial, and it is genuinely partial.** The legacy `ga_writers/_telemetry.py` path — 8 writer
call sites — still records NULL, because closing it means editing writers (stop condition §8(2)). That
is decision **D-1** for the native. Five other paths also yield NULL and always will: health-probe
service assets, `_mark_probe_green`, `_skip_no_delta`, the degraded branch, and fully-resumed writers.
**NULL rate remains a normal, correct reading** — two drafts of D-1 asserted otherwise and the gate
caught both.

**Commit sequence, declared not discovered.** A1 commits with `capability_estate_census.json` and the
three `nirmana-analysis-receipts` pins knowingly stale. Neither can be regenerated before the commit
exists: the census generator refuses without an explicit `--source-revision`, and the layer-pins
generator resolves content from committed git blobs. A follow-up commit reconciles both. **No `bg_*`
digest changed**, so the native-ratified L0 frozen pin is untouched.


## A3 — closed 2026-09-26, three correction rounds

**What landed.** A registry change mid-run no longer destroys the run. The validator reports *every*
divergence instead of raising on the first, the diverged asset alone fails, its dependents block
through the existing cascade, and every unaffected asset completes. The freeze/check predicate
asymmetry — where the same field was computed with different rules at each end, so an asset whose own
row never moved could still be failed — is closed; `route.ts` was the only one of four sites out of
step.

**What the gate changed, three times.** Round one: the terminal write was deferred past the claim, and
a hard-exit path in that window could detect a divergence and then silently discard it — *a campaign
about ending silent failures had introduced one.* Round two closed it by moving the check earlier, but
**the executor's own exit enumeration was incomplete** — neither executor nor implementer looked at the
caller, which wraps everything in `except Exception: sys.exit(1)`. Round three wrapped the window
properly.

**The finding that justifies the whole review apparatus.** The implementer called its `conn.rollback()`
"defensive and untested". The reviewer tested it against real psycopg: after a genuine in-transaction
fault the connection is `INERROR` and the next statement raises `InFailedSqlTransaction`. **Without
that rollback the record-writing would have failed too** — the fix would have worked only against the
test double. The caveat was over-modest, and the thing it hedged was load-bearing.

**Figures, at three honest strengths** (`measurements/A3_after_*.json`): production before = all 8 runs
losing 100% of plan; production after = **UNMEASURED**, and stays so until a real divergence occurs;
counterfactual on the real run's own frozen manifest = **10/10 aborted → 1/10 failed**, because no asset
in that plan depended on the diverged one. **A3 fixes 2 of the 8 runs**, not 8 — Family B is 6 of them
and is carried as A3b.

**Carried, not absorbed:** `G-1` — the orphan-cleanup statements just past the fixed window are guarded
by neither handler, so a fault there still loses a divergence; explicitly *not* charged against A3,
since the correction's boundary was specified as ending at the claim. `F-5` — A3 writes build-state
where HEAD wrote nothing, and round three **widened** that surface while narrowing its own loss;
bounded by a measured self-heal. These lie in opposite directions and are reported as a pair.

**`G-2`, a reviewer correcting itself:** a lost divergence is not lost forever — the watchdog still
terminalizes the row. The honest claim is that the *reason* is lost and the row is **misattributed**
into `"orphan-watchdog: run never dispatched"` — Family B's signature, the exact bucket this packet's
before-measurement worked to separate from Family A.


## B1 — closed 2026-09-26, one REJECT and three rounds

**The premise was inverted, and that was the executor's error.** The before-measurement I commissioned
said seven surfaces *"count a blocked asset as a failure."* For the whole `deriveState` chain the
truth was the opposite: `fetchAllCounts` hard-coded `error: null` on **both** paths, so the blocked
branch was unreachable and cascade victims rendered **green**. Measured: **9 of 10 real production
blocked assets rendered `lit`**, 7 of them on the native's own chart.

My census was wrong three ways — it **named a dead surface** (`AssetNode.tsx`, zero live importers),
**missed live ones** (`AgentsView`, `AtlasView`, `AssetProgressBar`, `PlanTimeline`,
`runs/[id]/assets`, `ArmillaryGraph`), and **mischaracterised the direction** for those it did name.
It was found only because the gate refused the packet twice.

**What landed.** A cause is no longer recorded as a consequence: a writer timeout was being passed
through as `blocking_deps=["timeout:600s"]`, a fabricated dependency; it now writes an honest
`TIMEOUT:` cause. Blocked assets carry `disposition='blocked_dependency'` (a value that already
existed in the schema with zero rows and zero references) plus a prospective root column. The
governance census stops grading a chart FAIL from cascade-only history — and no longer grades an asset
that has **never once built** as PASS. **8 of 8** currently-blocked assets now render blocked;
**18 badges flip off green**, of which 4 are pre-existing false-greens repaired as a side effect.

**An instruction of mine was correctly refused.** I said "carry the signal through." The builder
checked production first, found `bg_transit_engine` — *healthy* — carrying a stale never-cleared
error, and gated on computed state instead. The reviewer's ruling: it would have called the
unconditional pass-through **a defect**. Computed state over stale text, §N.8, applied against the
executor.

**Proof discipline.** 16 mutations across three gates, every file byte-restored. The second round's
"decisive assertion" was **decorative** — deleting the fix left 4/4 green. It now fails under the same
mutation that exposed it.

**Certified honestly:** counting surfaces **complete**; labelling surfaces **not** — `PlanTimeline`,
`runs/[id]/assets` and `ArmillaryGraph.stateColor` remain, three unmapped-default sites survive, and
R-6 is one-third done. Carried to B2 as C-3 and C-4.

## Branch head

A2's engine change is committed; A1's remains uncommitted in the working tree pending its
re-review, and is staged out of A2's commit by explicit path rather than by staging the tree.

**Wave sequencing**, forced by the same-file rule (prompt §4): A3 needs both
`pipeline/orchestrator/runner.py` and `app/api/cockpit/runs/route.ts`; A2 needs the latter. So
**wave 1 = A1 (Python) ∥ A2 (TypeScript)**, fully disjoint; **wave 2 = A3**, once A2 releases
`runs/route.ts`. A1 deliberately does not edit `runner.py`: its failure paths already leave
`rows_written` untouched, which is the shape A1 must preserve, so preserving it means not editing it.

## Environment, confirmed at session open

- cwd `/Users/Dev/madhav-engine`, branch `campaign/nirmana-engine`, head `975370eb5`.
- `.claude/agents/nirmana-{engine-builder,engine-diagnostician,packet-reviewer}.md` all present.
- DB posture: `transaction_read_only = on`, database `amjis`, `PGPORT=5433`, PostgreSQL 15.18.

## Blockers

None. One tooling deviation, recorded and worked around (see EVENTS.jsonl, `subagent_dispatch_workaround_adopted`):
this session's agent registry loaded from the prior working directory and does not resolve the
`nirmana-*` subagent types by name, so each is dispatched as `general-purpose` with an explicit model
override (Sonnet for diagnostician and builder, Opus for the packet reviewer) and its definition file
inlined verbatim as the role preamble. §4 routing and role separation are preserved; a fresh session
started in this worktree resolves the definitions natively, so resumability is unaffected.

## Stop conditions — none triggered

No packet has required a `WriterBase` contract change, an asset's data/writer/algorithm, or exposed a
secret. `DECISIONS_FOR_THE_NATIVE.md` not yet created; it is created only when a stop condition fires.
