---
artifact: MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN
version: "1.1"
status: PROPOSED_FOR_NATIVE_RULING
prepared_on: 2026-09-19
prepared_by: "Strategy session (Claude Code, Fable 5.1) — read-only grounding, no repo mutation"
ground_truth_as_of: "2026-09-19 17:02 IST (11:32 UTC)"
protected_main_observed: 32e5a9f0e
coordination_tip_observed: cb425305a2607f97ed641af7dddf0184c007654f
supersedes: none
related:
  - MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19.md
  - purna_anvesana/CAMPAIGN_STATE.md (v0.29.0)
  - purna_anvesana/TRANSFER_HANDOFF_2026-09-19.md
  - purna_anvesana/SUCCESSOR_OWNERSHIP_ADDENDUM_2026-09-19.md
  - MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md (local-only branch; see §1.5)
  - MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0.md (local-only branch; see §1.5)
  - ../CAMPAIGN_COORDINATION.md (origin/campaign-coordination)
changelog:
  - "1.1 (N1-E, 2026-09-20, L3 Kāla conductor): corrects §0 item 7 note, §1.3, Appendix A and
    Appendix B — this plan's 'seven stranded commits, none an ancestor of main' claim was right
    about ancestry (the exact named SHAs are indeed not ancestors of main) but wrong about
    content: PR #2607 (`fa9857f00`, 2026-09-16) squash-merged a later, corrected generation of the
    same work. Measured: 874 of 874 substantive added lines across all seven commits are present
    in `origin/main` (independently confirmed by Wave D subagents D1/D3/D4/D6, each diffing
    against main before assuming salvage was needed — see
    `l3_autonomous/STATE.md` packet rows D1–D6). Original claims retained in place per this
    project's archival/retain-in-place + §N.7/§N.8 discipline; this entry supersedes them with the
    measurement and method, not by deletion. Cost of the error: five Wave D subagent dispatches
    were commissioned against a false premise; all five correctly re-verified against main first
    and closed as no-ops rather than compounding the mistake, but the packet should not have
    existed as scoped."
  - "1.0: First dual-campaign plan after the native's decision to run Pūrṇa Anveṣaṇa in Codex and L3 Kāla elevation in Claude Code. Grounded against live GitHub, Cloud Run, coordination ledger and both campaigns' own state records; not against the handoff's cover claims."
---

# Pūrṇa Anveṣaṇa (Codex) ∥ L3 Kāla elevation (Claude Code) — execution plan

Evidence labels, as in the L3 handoff: **LIVE** = read today through GitHub / gcloud / git;
**RECORDED** = a campaign's own committed state record, cited with its timestamp;
**PLAN** = proposed, not a fact; **INFERRED** = derived from LIVE facts, not directly measured.

## 0. The verdict in ten lines

1. **Run them in parallel.** The contention that hurt was inside one Codex fleet timesharing two
   campaigns (quota, task/goal state, heartbeats, 180+ worktrees) — not at the git layer. A
   platform split removes that at a stroke. The five surfaces worktrees cannot isolate are cheap
   to partition and this repo has done it before (SAMPŪRTI ∥ GOCHARA-UTKARṢA, 2026-08-10).
2. **There is exactly one hard serial dependency, and it is in flight right now.** Migration 1040
   / the Pūrṇa ownership lifecycle gates `migrate`, which gates web, MCP and the builder image.
   Until it applies, L3 cannot reach `DATA_ACCEPTED` (builder image predates the generation
   tables) or `DEPLOYED_ACCEPTED`. Codex owns that fix, holds a lease bound to the current main
   tip, and the fix PR (#2684) merged at 11:31 UTC.
3. **0/22 was arithmetic, not performance.** Two of the four terminal states were structurally
   unreachable for every asset. The same is true of Pūrṇa's matrix: every product outcome is
   `source_ready` and every `candidate_verified` / `live_verified` is `NOT_RUN` for the same
   reason. Both campaigns have been producing source into a closed pipe since 2026-09-16.
4. **Claude Code must not idle while the gate is shut.** L3 has a full Phase-0 slate that is
   genuinely unblocked and is the work Codex never finished: preservation, governance, W0
   safety, field contracts, salvage. None of it moves `Accepted N/22`; use a Phase-0 scorecard.
5. **The four service-type L3 assets are the bridge.** Their terminal acceptance is service
   proof, not a physical generation; they do not wait on W1 generation heads, and the sidecar
   that hosts them deploys on `needs: [changes]` — it shipped `49eb14a6e` today while web/MCP
   stayed at `93a3a5eb8`. `ka_graha_sancara` / `ka_dasha_kala` are the smallest end-to-end proofs
   and they light Pūrṇa SCUs (`call_ephemeris_at_t`, `query_active_dashas`).
6. **Pūrṇa depends on L3, not the other way round.** 23 SCUs bind to `ka_*` producers; its own
   state says the active build has "only one proven `ka_gochara` receipt". Its live 5+30
   acceptance will stall on time-bounded and life-event cases until L3 supplies accepted receipts.
   That interlock needs a named channel, not ad-hoc discovery.
7. **The single largest risk in the picture is not technical.** All nine branches carrying L3's
   preserved work *and* the strategy branch holding L3's four governing documents are
   **local-only** — never pushed. Their only off-machine copy is a ZIP. Push first, plan second.
   **[v1.1 correction]** This push-risk framing understated how much of the actual *content* was
   already safe: PR #2607 had already squash-merged a corrected generation of most of the named
   work onto `main` a day earlier. The push (done, per A1) remained the right precaution for what
   genuinely was local-only, but "stranded" overstated the danger for content that had, in fact,
   already landed through a different path. See §1.3 and Appendix A/B for the measurement.
8. **The authority gap must be closed by one amendment (DP-SD-021)**, because the approved brief
   names the Codex task as "the sole execution destination". Everything Claude Code does before
   that is improvised.
9. **Serialize at exactly one point:** production mutation, under the existing coordination
   lease. Nothing else — not merges, not CI, not disposable-DB work.
10. **Phase gates are exits, not dates.** Pūrṇa's own plan estimates 4–7 engineering days for
    its remainder; L3's strategy deliberately withdrew estimates. Neither is a calendar promise.

---

## 1. Ground truth at 17:02 IST, 2026-09-19

### 1.1 Production delivery — LIVE

| Fact | Value |
|---|---|
| `origin/main` | `32e5a9f0e` — `fix(deploy): bridge Purna schema ownership (#2684)`, merged 11:31:18 UTC |
| `amjis-web` ready revision | `amjis-web-probe-93a3a5eb8d85-35069281039-1` → source `93a3a5eb8` (2026-09-16 07:11 UTC) |
| `amjis-mcp` ready revision | `amjis-mcp-probe-93a3a5eb8d85-35069281039-1` → same source |
| `amjis-sidecar` ready revision | `amjis-sidecar-probe-49eb14a6e6e9-35438308690-1` → **`49eb14a6e`, deployed today 10:46 UTC** |
| `brahma-build-pipeline-job` image | `brahma-pipeline:c63cb8048` (2026-09-16 04:21 UTC) — **predates migrations 1035/1036 by 4 h** |
| Undeployed commits on main (web/MCP) | 65+ ; 321 runtime files, +31,821 / −6,564 |
| Deploy runs for `32e5a9f0e` | **none yet** at 17:02 IST; CI for that SHA is the trigger |
| Last four deploy runs on main | all `failure` — correctly, since #2682 |

The mechanism, verified in `.github/workflows/deploy.yml` at `32e5a9f0e`:

- `migrate` requires `data_plane=marked ∧ isolation=strict ∧ nirmana=marked ∧ purna=marked ∧ bootstrap skipped`, **or** bootstrap `success` (bootstrap only runs on `workflow_dispatch` with `data_plane_cutover=true`).
- `deploy-web`, `deploy-mcp`, `deploy-pipeline-job` all `needs: [changes, migrate]`. Skipped `migrate` skips them.
- `deploy-sidecar` `needs: [changes]` only — which is why the sidecar shipped today and nothing else did.
- **#2682 (merged 09:09 UTC)** added `deployment-outcome` under `always()`: if the deployed-revision diff implies web/MCP/pipeline mutation and those jobs did not `success`, the run **fails** (`blocked-mutation-skipped`). A genuinely no-change push still passes (`no-deployable-change`). This is the §N.8 repair; it is live and proven by the four failing runs.
- **#2683 (10:12 UTC)** narrowed the Nirmāṇa re-attest condition.
- **#2684 (11:31 UTC)** grants `purna_inquiry_owner` temporary `USAGE, CREATE` on `public` through the existing `data_plane_schema_owner` delegate, revoked in an `always()` step before bootstrap postflight; migrations 1033–1040 unchanged. This is the exact fix for the observed failure (`Purna successor migration requires temporary owner CREATE on public`, run 35438308690). It is a scoped one-shot, not a gate loosening.

Database markers — **RECORDED by Codex through its authorized read-only route, 14:27 IST**:
`data_plane=marked`, `nirmana=marked`, `purna=rearm_required`; migration 1040 absent;
`purna_inquiry_bootstrap` role absent. Not independently re-read by this session (no proxy
was stood up). INFERRED: unchanged at 17:02 IST, since no deploy has run for `32e5a9f0e`.

### 1.2 Pūrṇa Anveṣaṇa — real state (RECORDED, `CAMPAIGN_STATE.md` v0.29.0, 14:27 IST; LIVE where noted)

**What it is.** A *product-completion* campaign, not a data campaign: Portal / managed MCP / raw
MCP "three doors"; a frozen denominator of 5 original cases + 30 product scenarios (six
families × five modes) + 34 Beyond-Ācārya route obligations; authority CCD-011 → CCD-012 →
native `TAKEOVER_GO` to successor task `01a0b7d8-…` on `codex/purna-product-completion-v3`.
Its plan §1.2 **explicitly excludes "L3–L5 asset elevation"**.

**Where it actually is.**

| Dimension | State |
|---|---|
| Waves W0–W7 | all COMPLETE at source/local; W7 candidate merged and live-delivered 2026-09-16 at `ac3ef565` (web), later superseded by `93a3a5eb8` |
| Four successor source packets (temporal closure, classical texts/contradictions, judgment_query, classical cursor) | merged to main via #2682's 40-commit squash; **source-ready only** |
| `LIVE_COMPLETION_MATRIX_v1.json` product outcomes | every row: `source_ready` PASS/IN_PROGRESS; `candidate_verified` **NOT_RUN**; `live_verified` **NOT_RUN** |
| Catalogue | 182 SCUs / 186 executable bindings / 157 availability contracts / 24 uncovered / 5 deliberate-dark |
| Wealth checklist | honestly `INCOMPLETE` (salience-sampled) |
| Feature frontier | **quiesced** at `34e3abf6b`; "wealth/capability Batch 5" paused for the delivery redirect |
| Successor branch vs main — LIVE | 2 files (the #2684 delta, now merged) → frontier fully integrated |
| Open PRs #2597–#2605 (stacked waves) — LIVE | historical, preserved, `#2597` CONFLICTING; Pūrṇa's own handoff: "do not drain mechanically" |
| Leases — LIVE (`origin/campaign-coordination@cb425305a`) | three ACTIVE rows today; newest `MADHAV-PURNA-DELIVERY-SCHEMA-SUCCESSOR-20260919`, opened **17:02 IST**, expires 21:00 IST, bound to the post-#2684 tip; scope = backup, one-shot bootstrap, exact dispatch, 1040, backlog delivery, ready-revision proof, cleanup, barrier decision. Its text **explicitly preserves "L3/Kāla source and data"**. |
| Redirect | accepted (`PRODUCTION_DELIVERY_PRIORITY_REDIRECT_ACCEPTED`, then `EARNED_DEPLOYMENT_SIGNAL_SOURCE_REPAIRED_AND_VERIFIED`) — the state file quotes this session's drift numbers verbatim |
| Remaining after the gate | candidate receipts → protected release → live 5+30 three-door automated acceptance → M4 close; human-expert empirical research separately `NOT_RUN` |
| Security incident | literal legacy `WATCHDOG_SECRET` in tagged zero-traffic revision `amjis-web-02826-huf`; needs an authorized human owner to rotate/revoke + audit; **neither campaign may touch it** |

**Its dependency on L3 (the interlock).** `capability_knowledge.snapshot.json` binds **23 SCUs to
`ka_*` producers** — e.g. `query_planet_transit` → `ka_gochara`/`ka_graha_sancara`,
`query_active_dashas` → `ka_dasha_kala`, `scu.kala.temporal_activation` → `ka_yojaka`/
`ka_kalasutra`/`ka_bhavishya_lekha`, `query_predictive_anchors` → `ka_kshetra`. Its state
records that "the active build has only one proven `ka_gochara` receipt and lacks current
receipts … needed to light the relevant query SCUs". Its plan §15 forbids self-serving by
rebuilding producers. **Pūrṇa's live acceptance of time-bounded / life-event cases is therefore
downstream of L3's accepted receipts.**

**Its overlap with L3's territory.** Plan Task 3 may edit "targeted handlers under
`registry/layers/L3_kala/` … only where their actual served contract needs repair". L3's
brief `may_touch` includes `platform/src/lib/retrieval/registry/layers/L3_kala/**`. One
directory, two authorized writers → needs a rule (§3.3).

**A Codex-side friction worth naming.** Codex binds each lease to an exact main SHA; every
merge — including its own — drifts the tip and self-terminates the lease. Three leases in two
hours today. Exact-SHA binding is a deliberate safety property (DP042 precedent); it is not
wrong, but merging all delivery-repair PRs *before* leasing would have cost one lease, not three.

### 1.3 L3 Kāla — real state

| Dimension | State | Label |
|---|---|---|
| Accepted assets | 0 / 22 at current definition `t3-2026-09-11-8b884eac` | RECORDED (handoff) |
| Current-definition L3 events / freezes | 0 / 0 | RECORDED |
| Canonical-chart L3 tables | 6 checked tables at 0 rows; **but** `kala_activation_predicates` 50,678 rows with 79 unmatched MSR refs, and `ka_kshetra` ~8.6 M field rows with a served surface hard-coding "field empty" (PARK-5) — partially populated with referential rot, not a clean slate | RECORDED |
| L1 / L2 selected-generation heads (canonical chart) | 0 / 0 → W1 has not happened | RECORDED |
| Builder image | `c63cb8048` — cannot populate generation tables it predates; cannot be rebuilt until `migrate` runs | LIVE |
| The seven "preserved achievement" commits named in handoff §5 (`3f109869d`, `a3e518864`, `87cc8c9`, `47131772b`, `7697c43b3`/`fbf7803dc`, `475f5ab5a`, `66a85047`) | **all stranded — none is an ancestor of main**; content-level diff confirms (e.g. `services/ka_kshetra/dhara_null_vec.py` +207 only on `codex/data-plane-l3-yojaka`). **[v1.1 correction, N1-E]** The ancestry claim is correct — none of these exact SHAs is an ancestor of `main` — but the *content* claim does not follow from it: PR #2607 (`fa9857f00`, 2026-09-16) squash-merged a later, independently-corrected generation of this same work from `codex/madhav-data-plane-execution`. Measured directly (Wave D subagents D1/D3/D4/D6, each diffing against `main` before assuming salvage was needed, per `l3_autonomous/STATE.md`): **874/874 substantive added lines across all seven commits are present in `origin/main`**, several as *strict supersets or corrected revisions* of the branch version (e.g. D5's W0 field register on main has 35 row-level type/nullability fixes the branch draft lacked). "Not an ancestor" did not mean "not present." | LIVE (ancestry) / **SUPERSEDED (content — see correction)** |
| Branches carrying that work | 8 local worktree branches, **all LOCAL-ONLY, never pushed** (`codex/l3-bhavishya-p0`, `l3-dhara-correction`, `l3-kshetra-p0`, `l3-kshetra-p0-correction`, `l3-kshetra-w0-preservation`, `l3-u05-registry`, `l3-w0-field-contract`, `data-plane-l3-yojaka` — up to 118 commits ahead) | LIVE |
| Other unmerged L3 branches on origin | ~105 `codex/nirmana-l3-*` (37 are `heartbeat-idle-*`); **newest last-commit 2026-09-08**, i.e. all predate the 2026-09-15 strategy → old-fleet history, not data-plane packets | LIVE |
| PR #2655 | open, superseded by #2656, no auto-merge; close, never merge | LIVE |
| Codex L3 task | stopped; continuation automation PAUSED; not independently verifiable from here | RECORDED |

### 1.4 Shared infrastructure state — LIVE

| Surface | State |
|---|---|
| Migration numbers, single numeric sequence across both trees (runner orders numerically since G1 repair) | high-water: `platform/migrations` **1040**; `platform/supabase/migrations` **1041**; nothing ≥1042 reserved on any remote branch |
| Generated artifacts | `src/generated/*` touched by **28 of the last 40** main commits; `nirmana-analysis-layer-pins.json` keyed `layers.{L0..L5}`; `nirmana-writer-digests.json` keyed by 123 writers of which exactly **22 are `ka_*`**; `capability_knowledge.snapshot.json` / `capability_estate_census.json` are Pūrṇa's generators' outputs but change whenever an L3 descriptor/handler changes |
| Coordination ledger | `origin/campaign-coordination`, 7,966 lines, LIVE, prime rule = deploy/rebuild lease; L3 has **no current row** |
| Merge-queue supervisor | `platform/scripts/ci/merge_queue_supervisor.ts` (Pūrṇa, #2675/#2679): read-only classifier; no cancel/merge/dispatch authority; reusable by L3 verbatim |
| CI/deploy triggers | pipeline image rebuild is path-gated on `diff(deployed-image-sha..HEAD)` ∩ `PIPELINE_PATTERN` (includes `python-sidecar/pipeline/`, `services/`, `bodha_writers/`) — the backlog already matches, so the first successful `migrate` will rebuild the builder image without `force_all` |

### 1.5 Governance surfaces — LIVE

| Surface | State | Consequence |
|---|---|---|
| `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` (476 L), `…_EXECUTION_BRIEF_v1_0.md` (374 L), `…_ASTRA_REVIEW_RECORD_v1_0.md` (256 L), `…_UNBLOCK_AND_RESUME_AMENDMENT_v1_0.md` / DP-SD-018 (364 L) | **not on main**; tracked only on `codex/madhav-data-plane-strategy`, which is **local-only** and carries **25 commits / 627 stale runtime-source files** vs main | extract the four files; never merge the branch |
| Execution brief §2/§8 | names Codex task `Execution — Data Plane` on `codex/madhav-data-plane-execution` as "the sole execution destination. No replacement task is created."; pins `execution_worktree: …/c9bd/Madhav` (gone) | Claude Code has no standing until amended |
| `CLAUDE.md` §E line 192 | `L3 ✓ CLOSED, 12 ka_* assets, 12/12` | wrong denominator at mandatory reading |
| `CLAUDE.md` §C item 5 | "Currently **L2 Bodha**" | ~3 months stale |
| `CURRENT_STATE_v1_0.md` §2 | top banner = the 2026-08-23 six-agent Nirmāṇa fleet; no mention of the data-plane campaign, DP-SD-*, or Pūrṇa Anveṣaṇa | the "you are here" file does not know where we are |
| `CLAUDECODE_BRIEF.md` | `status: COMPLETE` (PŪRṆATĀ, 2026-08-01) | §C item 0 currently governs nothing |
| `CAMPAIGN_COORDINATION.md` | Pūrṇa rows present; no L3 row; no partition rules for this pair | §3.3 |

---

## 2. Structural diagnosis — why both campaigns show "everything ready, nothing accepted"

Terminal acceptance for an L3 asset is `LAYER_DATA_ACCEPTED + CONSUMER_INTEGRATED +
DEPLOYED_ACCEPTED + VALUE_EVALUATED`. Pūrṇa's is `candidate_verified` then `live_verified`
against a deployed revision. Since 2026-09-16 07:11 UTC:

```
source merged to main ──► deploy.yml ──► migrate SKIPPED (purna != marked)
                                       └─► web / MCP / pipeline-job SKIPPED
                                       └─► (until #2682) workflow SUCCESS  ← unearned signal
production web/MCP frozen at 93a3a5eb8; builder image frozen at c63cb8048 (pre-generation-tables)
        │
        ├─► L3: DEPLOYED_ACCEPTED unreachable; W1 unreachable (builder lacks generation code)
        │        → DATA_ACCEPTED unreachable → 0/22 guaranteed regardless of execution quality
        │        → autonomous conductor found no eligible work → 37 heartbeat-idle branches
        └─► Pūrṇa: candidate_verified / live_verified unreachable → every row NOT_RUN
                 → successor kept producing source packets into a closed pipe
```

Both campaigns' operators saw the symptom ("do not manufacture busywork", "a successful
workflow with skips is not acceptance") and treated it as discipline. It was plumbing. The
plumbing is being fixed now; the plan below assumes it lands and states what to do if it does not.

---

## 3. Decision: parallel, with one serial point — and the exact shape

### 3.1 What is genuinely parallel (no coordination required)

| Claude Code — L3 | Codex — Pūrṇa |
|---|---|
| `python-sidecar/pipeline/orchestrator/writers/ka_*.py`, `services/ka_*`, `services/gochara_v3`, `services/w2g`, `pipeline/transit_search.py`, `tests/l3/**` | `retrieval/registry/knowledge/**`, `register_prashna_*`, `purna/**`, `managed_prashna_jobs.ts`, `prashna_ask_bridge.ts`, planner/inquiry lifecycle |
| `platform-mcp/src/tools/kala_views/**`, `promise_spine.ts` | Portal / managed MCP / raw MCP door code |
| DB tables `kala_*`, `gochara_resonance_map`; L1/L2 generation tables for W1 | DB tables `planner_*`, `inquiry_*` |
| 22 `ka_*` keys in `nirmana-writer-digests.json`; `layers.L3` in `nirmana-analysis-layer-pins.json` | `capability_*` generators (see §3.3 rule 4) |
| Disposable-DB benchmarks, reference oracles, field contracts, salvage, governance | Collector, judge, acceptance harness, three-door corpus |

### 3.2 The one serial dependency

```
Codex: #2684 merged ──► fresh lease (17:02 IST) ──► exact dispatch, data_plane_cutover=true
      ──► bootstrap: purna_inquiry_owner gets temporary CREATE ──► 1040 applies ──► purna=marked
      ──► routine migrate runs on every push ──► web / MCP / pipeline-job deploy
                                                       │
                              L3 W1 (needs builder image ≥ 1035/1036 code) ◄─┘
                              L3 DEPLOYED_ACCEPTED for any asset ◄──────────┘
                              Pūrṇa candidate_verified / live_verified ◄─────┘
```

Owner: **Codex**, under its active lease. Claude Code does not touch `deploy.yml`, the
ownership scripts, or migrations 1033–1041 during this window. The native does not need to
dispatch manually — Codex's lease scope includes "exact protected manual dispatch" under
DP-SD-020 automated-cutover authority — **unless** Codex reports a genuine external block
(credential, IAM, role topology). §7 lists what that would look like.

### 3.3 The five shared surfaces — partition rule for each

| Surface | Rule | Mechanism |
|---|---|---|
| **1. Production mutation** (migration apply, cutover dispatch, orchestrator build/rebuild of shared-table assets, traffic promotion) | **Serialize.** One exclusive lease at a time, held only for the minutes of the operation. | Existing `CAMPAIGN_COORDINATION.md` §1 lease table on `origin/campaign-coordination`; L3 registers as a party (§7 action N-5). PR merges, CI, and disposable-DB work are **not** leased. |
| **2. Migration numbering** (single numeric sequence across both trees) | **Partition by range; no lease.** Pūrṇa **1042–1069**; L3 **1070–1119**; anything cross-cutting **1120+** by a logged request. Never edit an applied migration. | One row in the coordination file §0; each brief cites it. |
| **3. Generated artifacts** | **Regenerate, never hand-edit; loser of a merge race rebases and re-runs the generators.** Every PR that changes a descriptor, writer, handler or pin runs *all* generators and commits their output. Conflicts in `src/generated/*` are resolved only by re-running on the rebased head. | `npm run codegen:capability-estate-census && npm run codegen:capability-knowledge` (+ `:check`), `platform/scripts/generate/nirmana_analysis_layer_pins.py`, the writer-digest generator. Deterministic ⇒ mechanical. |
| **4. `registry/layers/L3_kala/**` handlers** (the one real source overlap) | **L3 owns the directory.** Pūrṇa may change *availability contracts / knowledge-layer metadata* that reference L3 handlers without touching handler semantics. Any change to an L3 handler's served contract is an **L3 receipt request** (rule 5), not a Pūrṇa PR. | Coordination file §6 LOG entry `L3-REQ-nn`; L3 answers with a packet id or an honest `unavailable` disposition. |
| **5. Asset territory / DB tables** | Disjoint by construction (`ka_*`/`kala_*` vs `planner_*`/`inquiry_*`). Pūrṇa **must not** build, rebuild or backfill any `ka_*` producer to light an SCU (its own plan §15 already says so). | No mechanism needed beyond the two briefs. |

### 3.4 The two explicit interlocks

**I-1 — Pūrṇa → L3 receipt requests.** When a Pūrṇa product case cannot reach `live_verified`
because a `ka_*`-bound SCU lacks an accepted receipt, Pūrṇa records the case as
`BLOCKED_ON_L3_RECEIPT(<asset_id>)` in its matrix and appends `L3-REQ-nn` to the coordination
§6 LOG naming the asset, the SCU, and the case ids. L3 uses the request set to order its
frontier *within* the strategy's dependency waves (it may not skip an upstream wave to satisfy
a request). This is the only cross-campaign priority signal.

**I-2 — L3 → Pūrṇa consumer proof.** L3's `CONSUMER_INTEGRATED` / `VALUE_EVALUATED` for an
asset requires an actual receiving operator. Pūrṇa's three-door collector and independent
judge are the natural instruments for the managed/portal doors. L3 may *use* them read-only
against its own fixtures; it may not modify them. If L3 needs a collector change, that is a
`PA-REQ-nn` in the same LOG.

---

## 4. Phase plan — gated by exits, not dates

Each phase lists three lanes: **Codex / Pūrṇa**, **Claude Code / L3**, **Native**. A phase
exits when *its own exit criteria* are evidenced; lanes do not wait for each other except where
a dependency is drawn.

### Phase 0 — "the pipe is shut" (now → first earned deployment)

**Codex / Pūrṇa lane (release duty — already in motion)**

| Step | Exit evidence |
|---|---|
| Hold lease `MADHAV-PURNA-DELIVERY-SCHEMA-SUCCESSOR-20260919`; exact dispatch on `32e5a9f0e` with `data_plane_cutover=true` | run id; `One-time Protected DB Bootstrap` = success |
| 1040 applies; `purna` marker = `marked`; bootstrap memberships/ACLs cleaned by postflight | `schema_migrations` row for 1040; marker read; postflight log |
| Routine `migrate` succeeds; web / MCP / pipeline-job deploy for `32e5a9f0e` | `deployment-outcome` = `earned-deployment`; **ready revision + `NIRMANA_DEPLOYED_SHA` read from Cloud Run** for web, MCP; job image tag = `32e5a9f0e` |
| Post-deploy smoke; regression check across the 321-file drift window, not just the last PR | smoke run ids; a written regression note (possibly "none found") |
| Release lease; barrier decision recorded; feature frontier (Batch 5) resumes | coordination row RELEASED |

Stop conditions (Codex's own, restated): protected-tip drift; failed exact-main CI; backup failure;
role-topology mismatch; rollback ambiguity. At most two identical attempts, then a root-cause
packet — not a third dispatch.

**Claude Code / L3 lane — all genuinely unblocked; none moves Accepted N/22**

| # | Packet | Exit evidence |
|---|---|---|
| P0-1 | **Push the nine local-only branches to origin, unchanged** (`codex/l3-*` ×7, `codex/data-plane-l3-yojaka`, `codex/madhav-data-plane-strategy`). Preservation, not integration. | `git ls-remote --heads origin` lists all nine; SHAs match local |
| P0-2 | **Extract the four governing documents onto main** as a docs-only PR from a fresh branch off `32e5a9f0e` (copy the files; do not merge the strategy branch). Add the L3 handoff itself. | PR merged; `deployment-outcome` = `no-deployable-change` |
| P0-3 | **DP-SD-021 amendment** (§Appendix C): Claude Code = L3 execution destination; Codex = Pūrṇa; supersedes the `c9bd` pin and the "sole destination" clause; records the platform-split rationale; incorporates §3.3 partition rules and §3.4 interlocks. Native signs. | merged with native approval recorded in the strategic ledger |
| P0-4 | **Governance surface refresh**: `CLAUDE.md` §E L3 row (22 active / 0 accepted / campaign pointer), §C item 5 (active campaigns = Pūrṇa Anveṣaṇa ∥ L3 Kāla data-plane); `CURRENT_STATE` §2 new banner; new `CLAUDECODE_BRIEF.md` for L3 (`may_touch` / `must_not_touch` lifted from the brief + §3.3); coordination file: L3 party row, migration ranges, interlock LOG format. | drift/schema validators pass; PR merged |
| P0-5 | **Stranded-branch triage record** (Appendix B classes): the 8 preserved branches → per-packet disposition (land / supersede / retire) with the exact reviewed commits; the ~105 `nirmana-l3-*` → one bulk `SUPERSEDED_BY_STRATEGY_2026-09-15` disposition (37 `heartbeat-idle-*` retired outright); #2655 closed. No merges in this packet. | a versioned triage artifact; #2655 closed |
| P0-6 | **W0 safety on disposable DBs**: Kshetra P0 (mutation-free planning, 15-table referrer preflight — salvage from `l3-kshetra-p0*` / `l3-kshetra-w0-preservation`), Bhavishya P0 (history preservation — `l3-bhavishya-p0`), DHARA midpoint correction (`l3-dhara-correction`, `87cc8c9`). Land each as its own PR against current main, re-reviewed, tests re-run — **the old green is not evidence**. | 3 PRs merged; focused suites green on the merged head; pipeline image rebuild will queue behind Phase 1 |
| P0-7 | **Field-contract dossiers** for the four service identities first (`ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`) against the 699-field register: producer path, grain, unit, context, null semantics, receiving operator, falsifying test. | 4 dossiers in the packet format of handoff §8.1 |
| P0-8 | **Service-proof candidates**: for `ka_graha_sancara` and `ka_dasha_kala`, write the type-appropriate acceptance test (arbitrary chart/convention, bounds/errors, applicability, failed/silent systems). Run against the **already-deployed sidecar `49eb14a6e`** for service-side proof; consumer-side proof waits for Phase 1. | tests green against live sidecar; consumer half explicitly `NOT_RUN` |
| P0-9 | **Baselines**: Kshetra null / preparation / publication and transit-search microbenchmarks re-run on current main with the strategy §5 benchmark contract (hardware, ephemeris, cache regime recorded). | benchmark artifact; no speedup claimed |

**Native lane**

| # | Action |
|---|---|
| N-1 | Sign DP-SD-021 (P0-3). Everything Claude Code does before this is improvised. |
| N-2 | Assign a human owner for the `WATCHDOG_SECRET` incident (`amjis-web-02826-huf`): rotate/revoke, audit tagged-revision exposure, return redacted evidence. Neither campaign may act. |
| N-3 | Decide the migration ranges (§3.3 rule 2) or accept the proposed ones. |
| N-4 | Decide whether Claude Code may stand up a read-only Cloud SQL proxy for verification (the handoff did; this session did not without asking). |
| N-5 | Confirm Claude Code's L3 party row in the coordination file. |

**Phase 0 exit:** Codex reports an earned deployment with ready revisions read from Cloud Run
**and** Claude Code independently re-reads the same revisions (doctrine: builders never
self-certify). Plus P0-1, P0-2, P0-3 done. P0-4…P0-9 may spill into Phase 1 without blocking it.

**If the gate does not open** (two identical Codex failures or an external block): Phase 0
continues for L3 unchanged — the slate above is ~1–2 weeks of real work — and the native
receives Codex's precise external request. Do not let L3 "help" with `deploy.yml`.

### Phase 1 — "the pipe is open" (first earned deployment → first accepted L3 asset)

**Codex / Pūrṇa:** candidate receipts on the deployed revision → three-door collector runs the
5+30 corpus → cases that fail on `ka_*`-bound SCUs become `L3-REQ-nn` (I-1) → protected
release of the successor candidate → live acceptance for cases not blocked on L3 → M2/M3 by its
own plan. It must not resume Batch 5 before its own release-verification items are evidenced.

**Claude Code / L3:**

| # | Packet | Exit evidence |
|---|---|---|
| P1-1 | **Independent re-verification** of Phase 0's deployment: ready revision, env SHA, image tag, `schema_migrations` (via N-4 route), markers. Record as L3's own evidence, not a copy of Codex's. | evidence artifact |
| P1-2 | **W1 — physical upstream truth**: materialize/select accepted L0 → L1 → L2 generations for the canonical chart using the **rebuilt** builder image; verify every contributing producer partition (seven L2 producers share MSR; `bo_bimba`/`bo_karanajala` share CGM nodes). Under a deploy/rebuild lease. Any semantic gap in L0–L2 returns as a bounded amendment — L3 does not invent rich fields. | `l1_generation_heads` / `l2_generation_heads` populated for `482012f1`; partition acceptance record |
| P1-3 | **Smallest end-to-end proof — `ka_graha_sancara`** to terminal: service proof (P0-8) + consumer route (`call_ephemeris_at_t` / `query_planet_transit` handler in `L3_kala/`) + deployed MCP revision + value test through the managed door (I-2) + authenticated freeze event at definition `t3-…`. **Accepted 1/22.** | freeze event id; `Accepted 1/22` |
| P1-4 | **`ka_dasha_kala`** by the same route (reads L1 `chart_dashas`; no L3 generation needed). **Accepted 2/22.** Lights Pūrṇa `query_active_dashas`, `call_dasha_eligibility`. | freeze event id |
| P1-5 | Resolve the 79 unmatched MSR references in `kala_activation_predicates` **only after** P1-2's accepted L2 generation exists (they may resolve by rebinding, or require Yojaka's W2 rebuild). | disposition record |
| P1-6 | Consume the first `L3-REQ-nn` set to order the W2 frontier. | ordered W2 queue |

**Native:** rule on any bounded upstream amendment P1-2 surfaces; nothing else.

**Phase 1 exit:** `Accepted ≥ 1/22` with a real freeze event; W1 heads populated; Pūrṇa's
first live-verified cases recorded (any number > 0).

### Phase 2 — scaling L3; Pūrṇa closing

**Claude Code / L3:** W2 (resonance, overlays, Yojaka, Avadhi, `ka_muhurta_seva`/`ka_tulana`
data-bound, Kshetra S0/S2) → W3 (v2 windows, Sangam, century hold *decision*, Kshetra S3) → W4
(Kalasutra, Vighnakara, Taranga, Kshetra S1) → W5–W7 per the strategy §6.4, **one asset carried
to terminal at a time within a wave**, in `L3-REQ` order where the DAG permits. Performance
programme P1–P6 runs alongside on disposable DBs with the §5 benchmark contract; production
rebuild only with matched before/after evidence.

**Codex / Pūrṇa:** M3 automated acceptance → M4 live close → `PRODUCT_DELIVERY_COMPLETE_AUTOMATED_ACCEPTANCE`.
Cases still `BLOCKED_ON_L3_RECEIPT` at Pūrṇa's close are recorded as such — an honest limitation,
not lowered requirements, not an L3 obligation to rush.

**Phase 2 exit:** Pūrṇa closed; L3 `Accepted N/22` rising with per-wave data acceptance.

### Phase 3 — L3 completion (W8, U01–U11, 22/22)

Per the handoff §12.3 W8 and strategy §7: receiving operators, U01–U11 interface packets,
century hold legitimately resolved, cross-asset coherence, final exact-source/deployed/
generation manifest, **22/22**. Returns to Strategy for L4/L5 planning. Not planned in detail
here — its inputs do not exist yet.

---

## 5. The Claude Code L3 execution model — what must differ from Codex's

The Codex conductor was well-designed for a world where eligible work always exists. It was run
against two shut gates and produced 37 idle branches. These rules exist to prevent the same shape:

1. **No autonomous heartbeat until `Accepted ≥ 1/22`.** Phase 0 and Phase 1 run as bounded,
   human-checkpointed packets (one Claude Code session per packet or small group; the strategy
   session — this one — as conductor). A heartbeat is earned by the first terminal asset, not
   assumed.
2. **"Structurally blocked" is a terminal state for a cone, not a wait state.** If a packet's
   exit depends on an unopened gate, the packet records `BLOCKED_STRUCTURAL(<gate>)` and stops;
   the conductor picks a different cone. No adjacent-work manufacturing.
3. **Two metrics, never conflated.** Phase-0 scorecard (preserved 9/9 · docs 4/4 · DP-SD-021 ·
   triage n/8 · safety 3 · dossiers n/22 · service-proofs n/4 · baselines) vs the campaign metric
   `Accepted N/22` with per-state columns (producer / data / integrated / deployed / value).
4. **One branch per packet.** `l3/p0-6-kshetra-p0-safety`, not one per finding. The 113-branch
   sprawl is a salvage cost we are paying now.
5. **Independent verification is a different session.** A packet's PR is reviewed by a
   read-only Claude Code session (or subagent) that did not write it, inspecting the exact
   candidate and raw evidence — mirroring Pūrṇa's own "builders never self-certify".
6. **Reuse, don't rebuild, coordination primitives.** `merge_queue_supervisor.ts` for CI-wait
   classification; the coordination file for leases; Pūrṇa's collector/judge for consumer proof.
7. **Report format** at every packet close: `Accepted N/22 · Δ · Phase-0 scorecard · current
   packet · exact blocker (owner, next action) · evidence ids`. No percentages from test counts.
8. **Salvaged work is re-earned.** Every stranded commit is re-reviewed and re-tested on current
   main. "482 focused tests passed on 2026-09-16" is history, not evidence.

---

## 6. Day-to-day protocol between the two campaigns

| Situation | Rule |
|---|---|
| Either campaign needs to merge a PR | Merge queue only; no lease; run the generators; rebase-and-regenerate on conflict. |
| Either campaign needs a migration number | Take the next in your range; append one line to coordination §0. |
| Either campaign needs production mutation | Claim a lease in §1 bound to the operation and the SHA policy you choose; hold ≤ the operation; release with evidence; never revive an expired row. |
| Pūrṇa needs an L3 handler/receipt | `L3-REQ-nn` in §6 LOG; do not edit `ka_*` or `L3_kala/` handler semantics. |
| L3 needs the collector/judge changed | `PA-REQ-nn` in §6 LOG. |
| Main tip drifts under an active lease | The lease holder's own policy applies (Codex: exact-SHA, self-terminate). The other campaign does **not** pause merging to protect someone else's lease — that is the serialization tax we are refusing. Lease holders should merge before leasing. |
| CI takes 6–14 minutes | It is not a stall. `merge_queue_supervisor` thresholds: soft 15 / hard 20 / confirm 5 / max 2 identical. |
| A `deployment-outcome` failure on main | Whoever merged the triggering PR owns the first look; if it is the Pūrṇa marker, Codex; if a pipeline/sidecar build failure from `ka_*` code, L3. Never bypass. |
| Reporting cadence | Each campaign updates its own state file at milestones; the strategy session reads both plus Cloud Run at least daily during Phase 0/1. |

---

## 7. Native decisions and actions required

| # | Decision / action | Unblocks |
|---|---|---|
| N-1 | **Sign DP-SD-021** (Appendix C) | Claude Code's standing; P0-3 |
| N-2 | **Own or assign the `WATCHDOG_SECRET` incident** (`amjis-web-02826-huf`) | Pūrṇa PA-R06 evidence; security hygiene |
| N-3 | **Ratify migration ranges** (proposed: Pūrṇa 1042–1069, L3 1070–1119, shared 1120+) | rule 2 |
| N-4 | **Authorize a read-only Cloud SQL proxy for Claude Code verification**, or name the alternative route | P1-1; independent verification doctrine |
| N-5 | **Confirm the L3 coordination party row** | rule 1 |
| N-6 | **Rule on the first-asset choice** (`ka_graha_sancara` then `ka_dasha_kala`) or name another | P1-3 |
| N-7 | **Bulk-retirement policy** for the 37 `heartbeat-idle-*` and the ~68 pre-strategy `nirmana-l3-*` branches (one disposition record vs per-branch) | P0-5 |
| N-8 | **If Codex reports an external block on 1040** (credential, IAM, role topology): perform the one exact action it names. Do not perform it pre-emptively. | Phase 0 exit |

---

## 8. Risks and stop conditions

| Risk | Signal | Response |
|---|---|---|
| Local-only branches lost (laptop failure, worktree prune) | — | P0-1 today, before anything else |
| Gate does not open; Codex loops | third identical dispatch; lease churn > 3/day | Native N-8; L3 continues Phase 0; nobody touches `deploy.yml` from the L3 side |
| First earned deployment ships 3 days of drift with a regression | smoke failure; Paripraśna post-deploy behaviour smoke red | Codex owns rollback/forward-fix under its lease; L3 does not deploy anything until green |
| W1 reveals an L0–L2 semantic gap | producer partition fails acceptance | bounded amendment to Strategy; L3 does not fabricate fields |
| Generated-artifact conflict storm | > 2 rebase-regenerate cycles per PR | move to regenerate-on-merge (CI job) — a small, separately authorized change |
| Pūrṇa self-serves a `ka_*` rebuild to light an SCU | any Pūrṇa PR touching `writers/ka_*` or `services/ka_*` | block at review; convert to `L3-REQ` |
| L3 "helps" with release recovery | any L3 PR touching `deploy.yml`, ownership scripts, migrations 1033–1041 | block at review; it is Codex's lease |
| Claude Code replicates the idle-loop | packets closing with no evidence delta; `BLOCKED_STRUCTURAL` not being declared | conductor stops the heartbeat (if any) and re-scopes |
| Two contradictory truths persist in governance files | any session opening with "L3 is CLOSED, 12 assets" | P0-4 |

---

## 9. First 24 hours — concrete

**Codex / Pūrṇa (already leased):** dispatch → 1040 → migrate → deploy → read revisions → smoke →
release lease → report the §Phase-0 exit table filled in.

**Claude Code / L3 (this strategy session conducts; execution sessions do the work):**

1. P0-1 — push nine branches (≈10 minutes; zero risk; highest value per minute in this plan).
2. P0-2 — docs-only PR: four governing docs + the L3 handoff + this plan, from a branch off `32e5a9f0e`.
3. P0-3 — draft DP-SD-021 for native signature (Appendix C is the skeleton).
4. P0-5 — triage artifact for the 8 preserved branches (read-only; no merges).
5. P0-4 — governance refresh PR (CLAUDE.md §E/§C, CURRENT_STATE §2, CLAUDECODE_BRIEF, coordination rows).
6. Start P0-6 on `l3-kshetra-p0` salvage in a disposable DB.

**Native:** N-1, N-2, N-3, N-4 (four decisions; N-1 is the one that matters today).

---

## Appendix A — evidence index (LIVE unless noted)

| Id | Value |
|---|---|
| main | `32e5a9f0e` (#2684, 11:31:18 UTC) ← `49eb14a6e` (#2683) ← `d4655c9f3` (#2682) ← `4adcf0497` (#2681) |
| coordination tip | `cb425305a` |
| deployed web/MCP source | `93a3a5eb8` (2026-09-16 07:11 UTC) |
| deployed sidecar source | `49eb14a6e` (run 35438308690, today) |
| builder image | `brahma-pipeline:c63cb8048` (2026-09-16 04:21 UTC) |
| 1035/1036 on main | 2026-09-16 08:18 UTC (#2607) |
| deploy runs today on main | 35435197677 F · 35435726103 F (dispatch) · 35437874634 F · 35438308690 F (dispatch, force_all, cutover) — all correctly failing under `deployment-outcome` |
| 1040 failure text | `Purna successor migration requires temporary owner CREATE on public` (run 35438308690, PL/pgSQL line 23) |
| Pūrṇa leases today | `…-REPAIR-20260919` 15:13→19:30 · `…-REPAIR-SUCCESSOR-20260919` 15:57→20:15 · `…-SCHEMA-SUCCESSOR-20260919` 17:02→21:00 IST |
| Pūrṇa state | `CAMPAIGN_STATE.md` v0.29.0, last event PA-E0104, 14:27 IST |
| L3 definition | `t3-2026-09-11-8b884eac`, manifest `8b884eac…a0b6` (RECORDED) |
| Stranded L3 commits | `3f109869d` `a3e518864` `87cc8c9` `47131772b` `7697c43b3` `fbf7803dc` `475f5ab5a` `66a85047` — none an ancestor of main. **[v1.1 correction]** Content is a different question: 874/874 substantive added lines across all seven are present on `origin/main` via PR #2607's later, corrected re-delivery — see §1.3. |
| Local-only branches | `codex/l3-bhavishya-p0` `codex/l3-dhara-correction` `codex/l3-kshetra-p0` `codex/l3-kshetra-p0-correction` `codex/l3-kshetra-w0-preservation` `codex/l3-u05-registry` `codex/l3-w0-field-contract` `codex/data-plane-l3-yojaka` `codex/madhav-data-plane-strategy` |
| Migration high-water | 1040 / 1041 |
| Generated-artifact churn | 28 / 40 recent main commits |
| SCU→`ka_*` bindings | 23 |

## Appendix B — stranded L3 branch triage classes

| Class | Members | Proposed disposition |
|---|---|---|
| B-1 preserved data-plane packets (LOCAL-ONLY) | 8 branches above | push unchanged; per-packet land/supersede/retire with exact reviewed commits (P0-5 → P0-6). **[v1.1 outcome, N1-E]** Executed 2026-09-20: pushed 9/9 (A1), then 6 packets (D1–D6) each independently diffed against `main` before assuming salvage was needed, per this table's own instruction — every one found its target content already on `main` via PR #2607 and closed as a verified no-op (0 PRs opened, 0 regressions risked). The proposed methodology was correct; the premise it was applied to ("stranded") was not — see §1.3. |
| B-2 strategy branch (LOCAL-ONLY) | `codex/madhav-data-plane-strategy` | push unchanged; **extract** the four docs; never merge (627 stale runtime files) |
| B-3 delivery-repair leftovers | `codex/madhav-data-plane-l3-closure` (#2655), `…-isolation-admin-env-fix`, `…-isolation-region-fix`, `…-pgcrypto-successor` | superseded by #2656/#2670/#2673/#2684; close #2655; retire |
| B-4 old-fleet heartbeat noise | 37 × `codex/nirmana-l3-heartbeat-idle-*` (+ 2 heartbeat-*) | retire in one disposition record |
| B-5 old-fleet finding fixes (pre-2026-09-15) | ~66 × `codex/nirmana-l3-{f,n1,n3,n4,n5,n6,w1..w5,state}-*` | `SUPERSEDED_BY_STRATEGY_2026-09-15` in one record; re-open individually only if a Phase-2 packet cites one by SHA |

## Appendix C — DP-SD-021 skeleton (for native signature)

```
DP-SD-021 — Execution platform split for the L3 Kāla data-plane campaign
Supersedes (only): MADHAV_DATA_PLANE_L3_KALA_EXECUTION_BRIEF_v1_0 §2 "sole execution
  destination … No replacement task is created", §8 task/branch continuity wording,
  and the header pins execution_task / execution_branch / execution_worktree.
Retains: every other clause of the brief, DP-SD-017/018/019/020, may_touch/must_not_touch,
  activation prohibitions, delivery target, L4/L5 hold.
Decision:
  1. L3 Kāla execution destination = Claude Code sessions conducted from the
     "Strategy — Data Plane" thread; integration branch codex/madhav-l3-claude-code
     (created from verified protected main ≥ 32e5a9f0e).
  2. Pūrṇa Anveṣaṇa execution destination = Codex task 01a0b7d8-… (unchanged).
  3. The Codex task "Execution — Data Plane" and its continuation automation remain
     PAUSED; they are not a second conductor.
  4. Shared-surface partition rules per MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN §3.3;
     interlocks per §3.4; lease rule per CAMPAIGN_COORDINATION §1.
  5. Migration ranges: Pūrṇa 1042–1069; L3 1070–1119; shared ≥1120 by logged request.
Rationale: platform-level isolation of quota, task state and automation; the git-level
  surfaces are partitionable; recorded 0/22 was structurally forced by the delivery gate
  and empty upstream heads, not by execution quality.
Evidence: this plan's Appendix A.
```
