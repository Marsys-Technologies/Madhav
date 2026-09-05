---
artifact: SESSION_CHARTER_V21.md
canonical_id: NIRMANA_V21_SESSION_CHARTER
version: "2.1"
status: NATIVE-RATIFIED — binding on every v2.1 parallel session
amended: >
  2026-09-05, D-NATIVE-05 (native direct ruling on issue #1770): C13 "Destruction travels to
  descendants" added. The DAG models ancestors and the E-gate is necessary but NOT sufficient;
  every W2 route decision now carries a downstream blast-radius statement, rebuild_only is not
  safe-by-default for an asset with populated descendants, and a fresh verified snapshot before
  any row-destroying dispatch is hard floor rather than discretion. Enforced by WP-6 in the
  shared dispatcher. Nothing else in this charter changed.
produced_on: 2026-09-05
authorized_by: >
  Native, 2026-09-05: Asset-Frontier Pipelining (v2.1) approved as layer-clustered parallel
  sessions; fully autonomous, zero human gates, zero questions to the native; Conductor holds
  surrogate adjudication authority. Amends NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §1 (execution
  topology + E-gate); everything else in that plan, and the v1 execution prompt's §2 authority,
  §3 hard floor, and §7 mechanics, remains binding.
---

# NIRMĀṆA v2.1 — PARALLEL SESSION CHARTER

Read this file first in every session. It is the shared law; your session prompt adds only your
layer's specifics. Until the Conductor lands this file on `main`, read it from the shared
checkout path `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/nirmana/sessions/`
(read-only); after it lands, `origin/main` is authoritative.

## C1 — Topology

Seven sessions: **L0** (pre-existing; finishes L0, then ends) · **CONDUCTOR** (shared surfaces,
adjudication, ordering) · **L1…L5** (one layer each, all six waves W1–W6). Each session runs
Claude Code CLI with permissions bypassed, in its OWN worktree (C4). No session touches another
session's write-set.

## C2 — The E-gate (asset-frontier execution)

An asset may enter W4 EXECUTE iff ALL of:
1. Every DAG ancestor (transitive `depends_on` closure per the FROZEN definition) has
   `asset_frozen` in `nirmana_evidence.nirmana_elevation_campaign_events` — check with the gate
   SQL in C10; never assume, always query.
2. Its own W2 route is recorded (`asset_analysis_accepted` + `optimization_verdict_accepted`).
3. Its analysis generation-pins still match (writer digest + upstream generation); on mismatch,
   delta re-review first (usually minutes, not a redo).
W1/W2 are NEVER gated. W3 is gated only by C6 (capability-deltas) and C5 (write-sets).
W6 LAYER-FREEZE EVENTS remain ordered L0→L1→L2→L3→L4→L5: request the Conductor's ordering ack
(C7 issue) before submitting your layer's `stage_transition_accepted`; asset-level work is never
held for this — only the ceremony is.

## C3 — Absolute autonomy (the no-questions law)

- NEVER use AskUserQuestion, never address the native, never wait for a human. The native is
  asleep; the campaign must not notice.
- Every decision: (1) decide yourself under the delegated authority and log one line in your
  state file; (2) if it is cross-layer, shared-surface, freeze-ordering, or feels reserved →
  file a **GitHub issue labeled `nirmana-adjudication`** with the question, evidence, options,
  and your recommendation — then CONTINUE with other work. The CONDUCTOR is the native
  surrogate: it rules on adjudication issues under the same charter ADHIKĀRIN precedent
  (decide fast, log, binding). You act on its ruling as if native-issued.
- The ONLY things no session (Conductor included) may do remain the v1 hard floor: history
  rewrite/force-push to main; editing applied migrations; credential exposure; weakening a
  gate/check/trigger to pass; destructive ops on irreplaceable data (snapshots dir,
  `ka_gochara_sweep` v1 corpus) without a fresh verified snapshot; fabricated
  measurements/capsules; implementer certifying own asset. Floor conflicts → route around;
  at worst park ONE asset with evidence and continue.
- Kill switch: file `NIRMANA_HOLD` at the SHARED checkout root stops all sessions (check at
  every loop top). Its absence is standing authorization.

## C4 — Worktrees and Git flow

- Create your worktree at session start:
  `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add ~/nirmana-s/<SESSION> origin/main --detach`
  then branch per task from fresh `origin/main`. Branch namespace: `codex/nirmana-l<N>-*`
  (Conductor: `codex/nirmana-conductor-*`). PR title prefix: `L<N>:` / `CONDUCTOR:`.
- `npm ci` (or install) once per worktree under `platform/` before local verification; disk is
  budgeted for this.
- Every change: local verification first (targeted tests + tsc + lint on touched packages),
  then PR → **merge queue** (5 required checks; 0 approvals; auto-merge on). The queue is the
  global serializer — never bypass it, never push to main.
- Deploys are pipeline-automatic on merge. **Execution-safe rule** before any W4 dispatch that
  depends on merged code: verify the serving Cloud Run revision's `commit-sha` CONTAINS your
  commit (ancestry), and the deploy run is green. **Closure-safe rule** at your layer's W6:
  exact `main == production` with the queue drained.
- Rebase-and-retry on queue conflicts; if a sibling's merge invalidates yours, re-verify, don't
  force.

## C5 — Shared/limited resources (hard etiquette)

| Resource | Limit | Mechanism |
|---|---|---|
| **DB connections (max 50 — the scarcest resource)** | **≤3 concurrent build runs campaign-wide**; heavy/monster writers count double (run solo) | Slot claim/release by COMMENT on the Conductor's coordination issue (C7) BEFORE dispatch and AFTER completion; check open claims first; Conductor audits |
| Build dispatch | ≤1 active run per session | self-enforced + visible in coordination issue |
| Migration numbers | per-layer ranges: L1 650–659 · L2 660–669 · L3 670–679 · L4 680–689 · L5 690–699 · Conductor 645–649 | collision-free by construction |
| Shared campaign tooling (batch runner, dispatch scripts, evidence libs) | Conductor-owned | propose changes via adjudication issue; only Conductor merges them |
| Root `CAMPAIGN_STATE.md`, unified plan, tracker/charter files | Conductor-owned | layer sessions never edit |
| Your state file `L<N>_STATE.md` (same dir as this charter) | yours alone | commit it with your PRs; heartbeat line each loop |
| Central retrieval registry index / shared TS surfaces | additive per-layer files only | central-index edits via Conductor |
| gcloud/gh API | be gentle: poll ≥60s intervals | — |

## C6 — Capability-delta registry (cross-layer FEATURE dependencies)

A W3 item that consumes a NEW upstream capability (e.g. L4's verdict agreement-line consumes
L2's populated consensus columns) is HELD until the upstream layer announces that capability
LANDED on main. Announcements: a `## CAPABILITIES LANDED` section in the publishing layer's
`L<N>_STATE.md` (on main), one line per capability with the PR number. Consumers poll
`origin/main` for it. Data dependencies are C2's business; this section is only for features.

## C7 — Conductor coordination surfaces

- **Coordination issue** (Conductor opens at start, pins the number in root CAMPAIGN_STATE):
  run-slot claims/releases, monster scheduling, freeze-ordering acks.
- **Adjudication issues** (`nirmana-adjudication` label): questions → Conductor rules by
  comment, closes. Sessions poll their own issues every loop.
- Liveness: your state-file heartbeat + your gh activity ARE your pulse. Conductor nudges a
  silent-but-unblocked session via issue; honest limit — a dead CLI session cannot be
  resurrected remotely; its lane pauses until the native re-pastes its prompt (resumable by
  design, C9). Everything else continues.

## C8 — No idle, no theater (the scheduler every session loops)

Priority order, every loop:
1. Any asset passing the E-gate → claim slot → W4 dispatch (`force=true` for `rebuild_only` —
   log it; delta-skip honesty preserved).
2. Completed runs → W5: scripted mechanical checks + fresh-context verification subagent →
   verifier-identity capsule (`--include-email`; executor SA for commands, verifier SA for
   `integrity_verified`/`asset_frozen`/`probe_accepted` — never crossed).
3. Unheld W3 items on disjoint write-sets → implement, PR, queue.
4. Remaining W1 analyses (fan out read-only subagents freely) → W2 route decisions → your W2
   decision doc.
5. Blocked-item deepening: pre-write W5 verification scripts, pre-compute digests, draft close
   report sections, reconcile cost ledger.
6. Poll gates (E-gate SQL, capability-deltas, adjudication answers, merge queue) — then sleep
   300–600s (`sleep` is available in your shell) and loop. Waiting states are QUIET: no
   durable writes, no busywork, no governance invention.
Forbidden: manufacturing work to look busy; skipping 1–5 to do 6.

## C9 — Resumability (survive compaction, restart, morning re-paste)

Your `L<N>_STATE.md` is your memory: position (`L3-W4`, asset table with
route/status/capsule refs), decisions log, held items, cost ledger (wall-clock + tokens per
asset), heartbeat. Update every loop; commit with every PR and at milestones. On ANY start:
read charter → your state file → `git fetch origin main` → adjudication issues → continue.
Re-pasting your prompt into a fresh session MUST be safe at any moment.

## C10 — The gate SQL (verbatim tools)

Ancestor-frozen check for `$ASSET` (read-only; run via the campaign's read path):
```sql
WITH RECURSIVE assets AS (
  SELECT a->>'asset_id' id, COALESCE(a->'depends_on','[]'::jsonb) deps
  FROM nirmana_evidence.nirmana_elevation_campaign_definitions d,
       jsonb_array_elements(d.manifest->'assets') a
  WHERE d.definition_status='frozen'
), edges AS (
  SELECT id, jsonb_array_elements_text(deps) dep FROM assets WHERE jsonb_array_length(deps)>0
), anc AS (
  SELECT id, dep ancestor FROM edges
  UNION SELECT a.id, e.dep FROM anc a JOIN edges e ON e.id=a.ancestor
)
SELECT count(*) AS unfrozen_ancestors
FROM anc WHERE id='$ASSET' AND ancestor NOT IN (
  SELECT DISTINCT entity_id FROM nirmana_evidence.nirmana_elevation_campaign_events
  WHERE event_type='asset_frozen' AND entity_type='asset');
-- 0 ⇒ gate OPEN (with C2 conditions 2–3).
```
Batch-eligibility variant: the same query grouped over your layer's unfrozen assets — run it
once per loop, not per asset.

## C11 — Definition of done (per layer session)

All your layer's assets terminal (capsule or valid disposition receipt) · your W6 freeze event
submitted after Conductor's ordering ack · closure-safe sync verified · your
`L<N>_W6_CLOSE_REPORT_v1_0.md` published (40/40-style asset table, findings ledger outcome,
pillar movement per the five doctrines, cost actuals + your slice of the forecast, backlog to
your downstream) · `L<N>_STATE.md` final · then END the session cleanly.

## C12 — Integrity-check doctrine (D-VR-DATA-CORRECTNESS, native-ruled 2026-09-05)

Discovered in L0 wave 1; binding campaign-wide because every layer's Conform work will meet it.

- **A check that has never been green is a PROPOSAL, not a gate.** Before treating an
  `integrity_check_sql` failure as a data defect, check its provenance (git history): the R0-T01
  Conform-stage pilots were authored before the builds they now judge.
- **Bare `count(*) = N` equality pins are forbidden** as volume assertions (M0-T86 / D-126:
  "an equality wearing a floor's name"). Replace with: real invariants (cross-table FULL-JOIN
  consistency, fingerprint distinctness, ordering contiguity, tiling with no gaps/overlaps) PLUS
  a volume expectation that is either DERIVED (`expected_volume_formula` +
  `expected_volume_inputs` populated in `asset_registry` — NULL is the defect) or a floor
  (§N.4 achieved-count discipline).
- **Derive, never pick.** On a writer-vs-spec count mismatch: compute the expected volume from
  first principles, attribute the delta to a named cause, then rule — writer under-produces →
  fix the writer (MUST); pin stale/underived → correct the check with the derivation in the PR;
  genuinely ambiguous → adjudication issue with your recommendation, and continue other work.
- **The rewrite floor test:** a replacement check MUST be able to fail on real corruption the
  old one could not detect. A rewrite that can only pass more easily is a weakening — forbidden
  by the hard floor.
- **Service dependencies** (`asset_kind='service'`) are satisfied for dependency-assert purposes
  by a current GREEN probe / `service_health` — that is what "lit" means for a service
  (freeze-exception §3.5 addendum, native-granted 2026-09-05). Record the addendum in state.

## C13 — Destruction travels to descendants (D-NATIVE-05, native-ruled 2026-09-05)

The DAG models ancestors; **the E-gate is necessary and NOT sufficient.** Every W2 route
decision must include a downstream **blast-radius statement**: cascade children, no-FK
referrers, live row counts. `rebuild_only` is **NOT** "safe by default" for any asset with
populated descendants. Before any dispatch that destroys rows: **fresh verified snapshot,
always** — hard floor, not discretion.

**Why this exists.** An L2 `bo_laksana` MSR rebuild — ordinary, planned, `rebuild_only` work —
cascade-deletes **710,899 rows across five L3 tables** and orphans **~151,777 more**, reaching
`phala_anchors`, the table a separate campaign-wide hold exists to protect. Nothing in the
E-gate, the run-slot protocol, or the writer's own idempotency helper modelled that direction,
and the helper's docstring asserted `NO ACTION` where the schema says `CASCADE`. It was caught
because three sessions cross-checked each other, not because anything detected it.

**How to produce the blast-radius statement.** Query the catalogue — never a code comment
(a comment asserting a schema property is not evidence of that property):

```sql
-- transitive CASCADE closure; run per target table
psql "$DATABASE_URL" -v table=<your table> -f platform/scripts/nirmana/cascade_check.sql
```

Then state, in your W2 route: every cascade child with its layer and live row count, every
no-FK referrer (these **orphan** rather than cascade — the harder failure, since a stale
pointer still resolves and nothing reads false), and whether any of it crosses a layer
boundary. **If it crosses a boundary, the dispatch is HELD**: file an adjudication issue
naming the owning layers and obtain an ordering ruling, and the owning layer must confirm its
data is regenerable *before* the snapshot is spent.

**Enforcement.** WP-6 in the shared dispatcher enumerates the radius and **refuses a committed
dispatch** that would destroy or orphan rows without `--acknowledge-destroys`. The flag asserts
you hold a fresh verified snapshot; **it does not create one.** WP-6 makes destruction
impossible to not-know about — it does not decide whether destruction is acceptable, which
remains a W2 route decision and an adjudication matter.

**No-FK referrers get dispositions, not cascades:** either a real FK with an intended delete
rule, or documented orphan-tolerance **with a detector**. *Silent orphaning is worse than loud
cascade.*
