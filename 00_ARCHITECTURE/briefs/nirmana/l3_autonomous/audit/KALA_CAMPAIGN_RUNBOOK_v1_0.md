---
artifact: KALA_CAMPAIGN_RUNBOOK
version: "1.0"
status: DRAFT
date: 2026-09-22
canonical_id: KALA_CAMPAIGN_RUNBOOK
scope: PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md §6, items 1-8 (deliverable #10 of the KĀLA READINESS AUDIT)
produced_by: L3 Kāla readiness audit (autonomous, Claude Code), read-only-plus-tested-setup subagent, cycle 6
inputs_cited: >
  KALA_DAG_RECONCILIATION_v1_0.md (F3, four-way DAG), _work/DOMAIN_B.md (acceptance machinery),
  _work/DOMAIN_J.md (session/tooling), KALA_PRIVILEGE_MATRIX_v1_0.md (F4), _work/DOMAIN_G.md
  (cross-campaign lease protocol), _work/DOMAIN_H.md (hub list), _work/DOMAIN_C.md (orchestrator/
  build-path proof), KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md (T3, event->gate admissibility),
  KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md (T1), AUDIT_CHARTER.md, AUDIT_STATE.md,
  MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md v1.1 (origin/codex/madhav-l3-claude-code) §3.3-§3.4/§4,
  git log / live psql queries run directly by this packet (cited inline).
conductor_verification: >
  Cycle 6 conductor independently re-ran: `grep -c definition_revision platform/scripts/nirmana/egate.sql`
  -> 4 (confirmed); `grep -n "F1-class fix" platform/scripts/nirmana/capsule_audit.sql` -> confirmed present;
  confirmed nrec/l1_integrity_check_dry_run.sql have zero matches for nirmana_elevation_campaign_events;
  confirmed the v2 SQL artifact file exists and re-ran it live against the read-only replica, reproducing
  the claimed 22x NOT_READY-BLOCKED-ANCESTORS + 1x NOT_READY-BLOCKED-NO-ROUTE output verbatim, including
  the ka_gochara_v3_century_materialize BUILD-PROTECTED/PARISHKARA MR-06 error text. All headline claims
  in this document passed independent spot-verification (see AUDIT_STATE.md cycle 6 log).
---

# KALA_CAMPAIGN_RUNBOOK_v1_0

## 1. F1 status — confirm the fix is present, sweep siblings

**Confirmed present on this branch, not merely on `origin/main`.** Reproducing commands (run this cycle):

```
$ git log --oneline -- platform/scripts/nirmana/egate.sql
9b3c3b219 fix(nirmana): scope egate.sql and capsule_audit.sql to the frozen definition_revision (F1) (#2706)
45f06e68b feat(nirmana): shared read-only E-gate batch-eligibility tool (charter C2/C10) (#1722)

$ git log --oneline -5
008c49e80 Merge remote-tracking branch 'origin/main' into l3/kala-readiness-audit
122e5357e audit: foreground-subagent law after cycle 4 exited with agents pending; preserve cycle 4's orphaned outputs
c21c4d1d4 docs(l3-audit): cycle 3 — ...
9b3c3b219 fix(nirmana): scope egate.sql and capsule_audit.sql to the frozen definition_revision (F1) (#2706)
459496337 docs(l3-audit): cycle 2 — ...

$ grep -c definition_revision platform/scripts/nirmana/egate.sql
4
```

`9b3c3b219` is an ancestor of the current HEAD (`008c49e80`, a merge of `origin/main` into this
branch, performed this cycle) and `egate.sql` on disk literally contains 4 `definition_revision`
filter references. This corrects a claim carried in the orphaned `_work/artifacts/kala_readiness_query.sql`
header (from a prior crashed cycle) that this worktree had "NOT been rebased onto that fix" — that
was true when written, is not true now, and is fixed in this packet's v2 SQL artifact's header (§2
below).

**Sibling sweep** (the four named in F1: `capsule_audit.sql`, `l1_integrity_check_dry_run.sql`,
`nrec`, dispatcher gate reads):

| Sibling | Same defect class present? | Evidence |
|---|---|---|
| `capsule_audit.sql` | **No — already fixed, same PR #2706.** | `grep -n "definition_revision\|nirmana_elevation_campaign_events" platform/scripts/nirmana/capsule_audit.sql` shows every read of `nirmana_evidence.nirmana_elevation_campaign_events` (lines 34, 85, 107) paired with `AND definition_revision = (SELECT definition_revision FROM frozen_def)` on the very next clause, and an explicit in-file comment at line 29: `"-- F1-class fix: scope to the currently-frozen definition_revision. Unscoped, ..."` — i.e. the fix and its rationale are both in the file, not just in the PR title. |
| `l1_integrity_check_dry_run.sql` | **Not applicable — never reads the events table.** | `grep -n "nirmana_elevation_campaign_events\|definition_revision" platform/scripts/nirmana/l1_integrity_check_dry_run.sql` returns zero matches. It operates on L1 tables, not campaign evidence, so the F1 defect class cannot occur in it. |
| `nrec` | **Not applicable — never reads the events table.** | `grep -rn "nirmana_elevation_campaign_events\|definition_revision" platform/scripts/nirmana/nrec` returns zero matches. Per `_work/DOMAIN_B.md` §1, `nrec` is a submission-side CLI (identity derivation, token minting, HTTP POST) — it never queries campaign evidence for eligibility, so it cannot exhibit the F1 defect either. |
| Dispatcher gate reads | **Confirmed as the same two files above; no third dispatcher-side reader found.** | `grep -rln "nirmana_elevation_campaign_events" platform/scripts/nirmana/ platform/pipeline` returns exactly `egate.sql` and `capsule_audit.sql` — both already fixed. No separate "dispatcher" script independently reads the events table outside these two. |

**Conclusion: the F1 defect class is fully closed.** Both files that ever read
`nirmana_elevation_campaign_events` for eligibility (`egate.sql`, `capsule_audit.sql`) are fixed and
merged into this branch; the other two named siblings (`nrec`, `l1_integrity_check_dry_run.sql`)
never had the defect because they never read that table. Nothing is left uncovered by PR #2706
within the sibling set named in F1.

---

## 2. Definition-scoped readiness query — verified, tested, and it does report NOT READY

**Artifact:** `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/_work/artifacts/kala_readiness_query_v2.sql`
(new file, written by this packet; the prior orphaned draft `kala_readiness_query.sql` in the same
directory is **retained in place, not overwritten**, per this campaign's own retain-in-place hygiene
convention — v2 supersedes it for use and corrects one stale header claim, described below).

**What it computes, per L3 asset, in one query:** ancestors frozen under the *current* frozen
definition (`t3-2026-09-11-8b884eac` as of this audit), the asset's own route recorded under that
same definition (`asset_analysis_accepted` + `optimization_verdict_accepted`), producer-ready
evidence under that definition, physical build state for the canonical chart from `asset_throughput`
(rows written, last build time, last error), an F13-rung ceiling and an F14-state ceiling computed
from the exact admissibility mapping in `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` §2, and a single
`gate_verdict` column that is never a bare `OPEN` or `READY`.

**Why this is scoped wider than the (now-fixed) `egate.sql`:** `egate.sql` only ever establishes
C2.1 (ancestors frozen) and C2.2 (route recorded) — it has no visibility into physical data state,
so it cannot itself distinguish "never built" from "built once, now empty" from "genuinely lit."
The PROMPT_0 §6 item 2 requirement ("physical data state, F13/F14 ladder position, gate verdict")
needs a query that reads `asset_throughput` as well as the two campaign-event CTEs — that is this
query's reason to exist alongside, not instead of, `egate.sql`.

**Verification performed by this packet, and independently re-run by the cycle-6 conductor**
(read-only, `amjis_app` role, `default_transaction_read_only=on`):

```
$ source /Users/Dev/madhav-l3/dbenv.sh
$ psql -Atq -c "SELECT current_user, current_setting('default_transaction_read_only')"
amjis_app|on

$ psql -Atq -v chart_id="'482012f1-710e-4a25-994a-93821f5871aa'" \
    -f 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/audit/_work/artifacts/kala_readiness_query_v2.sql
```

**Real output (23 data rows: 22 active `ka_*` + protected `ka_gochara_sweep`), re-confirmed
verbatim by the conductor, excerpt:**

```
L3|ka_muhurta_seva|t3-2026-09-11-8b884eac|0||f|f|f|f|||||none|none|NOT_READY-BLOCKED-NO-ROUTE
L3|ka_dasha_kala|t3-2026-09-11-8b884eac|1|ga_dashas|f|f|f|f|lit|0|2026-09-10 19:26:34.768958+00||none|none|NOT_READY-BLOCKED-ANCESTORS
L3|ka_kalasutra|t3-2026-09-11-8b884eac|15|...|f|f|f|f|stale|335403|2026-08-13 01:15:50.567754+00||none|none|NOT_READY-BLOCKED-ANCESTORS
L3|ka_sangam|t3-2026-09-11-8b884eac|10|...|f|f|f|f|stale|14868|2026-08-13 01:07:13.494312+00||none|none|NOT_READY-BLOCKED-ANCESTORS
L3|ka_gochara_v3_century_materialize|t3-2026-09-11-8b884eac|13|...|f|f|f|f|error|914|2026-08-21 13:37:44.534065+00|RaiseException: BUILD-PROTECTED: kala_gochara_windows row(s) for chart_id 482012f1-... (generation=3.0, asset_id=ka_gochara) are protected — DELETE is refused. ... PARISHKARA MR-06 protection rationale.|none|none|NOT_READY-BLOCKED-ANCESTORS
... (23 rows total)
```

**Aggregate verdict distribution, re-confirmed by the conductor's own run of the same query this
cycle:** 22 rows `NOT_READY-BLOCKED-ANCESTORS`, 1 row (`ka_muhurta_seva`, which declares zero
ancestors under the current manifest) `NOT_READY-BLOCKED-NO-ROUTE`. **Zero rows returned
`OPEN-PENDING-PIN` or any READY-shaped value.** `asset_itself_frozen_under_current_def` is `f`
(false) for all 23 rows; `route_analysis_under_current_def`, `route_verdict_under_current_def` and
`producer_ready_evidence_under_current_def` are all `f` for all 23 rows.

**This is the required proof that the query can report NOT READY, and it does so correctly.** It
also matches, by two independent measurement routes already in the audit, the same conclusion:
F2 found 0 `t3`-scoped campaign events for any `ka_%` entity by direct DB query; T3 independently
derived the same "no L3 asset has cleared any F13/F14 rung under t3" conclusion from the event
vocabulary. This query is a third, independent confirmation via a different query shape (definition
manifest + `asset_throughput` join rather than a bare event-count), and it agrees. A fourth
independent run — by the cycle-6 conductor, from scratch, not copy-pasted from this packet's
transcript — reproduced the identical distribution and the exact `BUILD-PROTECTED`/PARISHKARA
MR-06 error text for `ka_gochara_v3_century_materialize`, a genuinely new finding surfaced by this
query: at least one L3 asset (the century materialiser) has a live, currently-firing build-time
protection guard refusing a DELETE against `kala_gochara_windows` rows for the canonical chart,
citing a named native-decision-required rationale ("PARISHKARA MR-06"). This is a real, previously
undocumented-in-this-audit safety mechanism and should be cross-referenced against T5 Tension 1's
five-way `ka_gochara` table-identity dispute and Q1 (century materialisation) in future work.

**v2's one substantive change from the orphaned v1 draft:** v1's header asserted this audit's own
worktree had not yet been rebased onto the F1 fix — true when written (prior cycle, pre-merge),
false now (§1 above). v2 corrects that claim; the SQL logic itself is unchanged from v1 (copied
verbatim), because it was already correct and did not depend on egate.sql's fix status.

**Promotion path (not self-authorized by this audit):** open a nirmana-adjudication issue proposing
this query for `platform/scripts/nirmana/` per charter C5 — this audit has no standing to self-merge
new shared tooling there.

---

## 3. Stream worktrees — what "correct" requires, and whether this worktree satisfies it

Per `_work/DOMAIN_J.md` §1 (re-verified by this packet by re-reading `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`
v1.1 §5 directly, `git show origin/codex/madhav-l3-claude-code:...`): the governing plan does **not**
mandate a fixed pool of pre-provisioned stream worktrees. Its actual rule (§5 item 4, "one branch per
packet") is that each packet runs in its own, ephemeral worktree, created per packet rather than
maintained as a standing 1:1 stream-worktree inventory. What the plan *does* commit to by name is a
single persistent **integration worktree**.

**What "correct" requires, concretely:**
1. The named integration worktree exists at the plan's stated path/branch.
2. The plan's preserved local-only branches have genuinely reached `origin` (a named top risk in
   the plan itself — "push first, plan second").
3. Each execution packet gets its own branch (`l3/p0-6-kshetra-p0-safety`-shaped, not one branch per
   finding) and, where isolation is warranted, its own worktree — not a shared mutable checkout.
4. A nested/child session spawned from inside a conductor session is resumable, not silently orphaned.

**Does this worktree (`/Users/Dev/madhav-l3/audit`, branch `l3/kala-readiness-audit`) satisfy items 1-3?**

Item 1 — **YES, confirmed in `_work/DOMAIN_J.md`** via `git worktree list`: `/Users/Dev/madhav-l3/integration`
on branch `codex/madhav-l3-claude-code` (tip `5d8252dbe`, descendant of the `STATE.md`-recorded
`cdc701afa`) exists exactly as the plan names it.

Item 2 — **YES.** `git ls-remote origin` (per Domain J) confirmed all 8 named preservation branches
plus one more (9 total, matching `STATE.md`'s "Preservation branches on origin | 9/9") exist on
`origin`, each also checked out locally under `/Users/Dev/.codex/worktrees/`.

Item 3 — **Partially, by construction of this audit's own charter, not by counter-evidence.** This
audit's own charter (`AUDIT_CHARTER.md` §"REPAIR lane") already follows the pattern correctly for its
one BUILD-authorized item (F1: "own worktree (`isolation: 'worktree'`), own branch
`l3/egate-definition-scope`, own PR"). This runbook packet itself runs inside the audit's shared
worktree (not its own), which is consistent with the charter's own design (audit *packets* are
subagent dispatches within one conductor worktree; only production-touching *repairs* get their own
worktree) — not a deviation.

**Verdict for item 4, and for this section overall: NOT READY.** The two worktree facts the
governing plan actually commits to (integration worktree, 9 preserved branches on origin) are both
confirmed live and correct. The session-persistence mechanism the plan's own multi-session model
depends on (a stream launched from inside a conductor session staying resumable) has **zero
mechanical enforcement** anywhere in the repository — per `_work/DOMAIN_J.md` §2's static grep,
`CLAUDE_CODE_FORCE_SESSION_PERSISTENCE`/`CLAUDE_CODE_CHILD_SESSION` appear exactly once in the
entire repo, inside the audit's own prompt file (`PROMPT_0...md:257-258`), as documentation of a
known hazard — not as a setting any launcher script, `.claude/settings.json`, or CI workflow
actually applies. **What would flip this to READY:** a launcher script, settings entry, or
pre-flight hook that sets `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` automatically before spawning
any nested/parallel session, rather than relying on a human or conductor session to remember the
prose warning.

---

## 4. Verified credential runbook

Per operation, per the charter's one permitted DB-access pattern and Domain B's acceptance-machinery
audit. **Never printed:** a secret value, a connection string, or a token.

| Operation | Identity | Secret | Exposure-free loading | Tested proof |
|---|---|---|---|---|
| **Read-only verification** (general reads: DAG facts, event counts, physical build state) | `amjis_app` DB role | Pulled by `dbenv.sh` via `gcloud secrets` (referenced once, per `_work/DOMAIN_J.md` §4's structural line-count check — value never read) | `source /Users/Dev/madhav-l3/dbenv.sh` — exports `PG*` silently, forces `default_transaction_read_only=on`; nothing else needed | **TESTED, this session, live, and re-tested independently by the cycle-6 conductor.** `psql -Atq -c "SELECT current_user, current_setting('default_transaction_read_only')"` -> `amjis_app\|on`. The full §2 readiness query ran to completion against the live replica under this identity twice (packet + conductor) — the most substantial test this runbook performs. |
| **Read-only privilege introspection** (which relations a builder role can/cannot touch) | `data_plane_builder` DB role, read-only | Pulled by `dbenv_builder.sh` via `gcloud secrets` (same structural shape: 4 lines, 1 `gcloud secrets` ref, 3 `PG*` exports, per Domain J) | `source /Users/Dev/madhav-l3/dbenv_builder.sh` | **TESTED, prior cycle, cited not re-run this packet** (`KALA_PRIVILEGE_MATRIX_v1_0.md` §1's `has_table_privilege('data_plane_builder', ...)` sweep across 431 relations, and §3's conductor-independent re-run: `SELECT has_table_privilege('data_plane_builder','public.bg_transit_moorti','SELECT'), has_table_privilege('data_plane_builder','public.phala_rectification','SELECT')` -> `f\|f`, confirming a real, reproducible gap). |
| **Acceptance minting** (`nrec --as executor\|verifier`, submitting a NIRMĀṆA evidence/definition command) | GCP service accounts `amjis-nirmana-executor` / `amjis-nirmana-verifier`, impersonated via `gcloud auth print-identity-token --impersonate-service-account=...` | `serviceAccountTokenCreator` grant on both SAs, held (per `platform/scripts/nirmana/README.md` and `route.ts`'s own "HONEST RESIDUAL" comment, both read by Domain B) **only by the native's own Google identity** — no key file, no standing trigger | `nrec` hardcodes `--include-email` unconditionally (Domain B §1) and refuses to run if `--as` doesn't match the command-derived required identity, before minting or sending anything | **NOT independently tested by this packet, and this is stated explicitly rather than assumed working.** Domain B verified the mechanism structurally (HTTP route fails closed on every branch; DB trigger `nirmana_elevation_guard_server_reconstructed_insert` stamps `writer_identity` from `session_user`, not a self-reported field) but did **not** run a live `gcloud iam service-accounts get-iam-policy` check. **What a real test would require:** the identity that will actually run the campaign (not merely a project owner) holding `serviceAccountTokenCreator` on both SAs, then a `--dry-run` invocation of `nrec` (decide-only, mints/sends nothing) followed by one real dry-run-free `nrec --as executor --file <a genuinely harmless test command>.json` against a scratch/non-canonical entity, observing a real 2xx or a real, diagnosable 4xx. |
| **Dispatch** (`dispatch_frozen_rebuild.py` or any orchestrator-invoking pipeline-job trigger) | Whatever GCP identity is authorized to trigger `brahma-build-pipeline-job` | Not enumerated by this packet — out of scope, and forbidden: the charter prohibits any production mutation, including build dispatch, for this entire audit | N/A — this operation is **not exercised** by this audit under any identity | **NOT tested, and cannot be tested read-only by design** — dispatch is inherently a mutation. Per F8 (re-confirm before ever using this path): PR #2695 (dispatcher hardcoded stale writer-digest path; wrong default ayanamsha in `call_dasha_eligibility`) is blocked on a Pūrṇa-owned baseline as of this audit's last check — **the campaign must not dispatch through `dispatch_frozen_rebuild.py` unpatched**, because until #2695 lands it would write a provenance receipt asserting a code identity that never ran. **What a real test would require:** #2695 landed; then a dispatch against a disposable DB or non-canonical chart (per Domain C's own precedent — see §5 below), never the canonical chart, with an independent post-dispatch re-read of `asset_throughput`/`build_runs` confirming the writer digest actually matches what ran. |
| **Generation** (L1/L2 generation-head functions, `1035`/`1036`-class functions) | `data_plane_builder`, gated by `session_user = 'data_plane_builder'` checks inside the functions themselves (Domain D) | Same `dbenv_builder.sh` route as privilege introspection, but this operation additionally **writes** | N/A for this audit — generation functions mutate `l1_data_plane_generation_heads`/`l2_data_plane_generation_heads`, which is production mutation | **NOT tested by this packet; out of scope by charter.** A real test would require a disposable DB (Domain C's own precedent: it ran a real, disposable, local Postgres 15 instance specifically to exercise the one property that cannot be meaningfully asserted with a fake cursor — the advisory lock) and is the correct model to follow for generation-function proofs too, rather than any canonical-chart or production-DB exercise. |

**Cross-cutting finding worth restating here rather than burying:** Domain B's most consequential
finding is not a defect but a **self-disclosed residual** — the executor and verifier GCP identities
are both impersonable by the same human principal (the native), so "implementer != certifier" is
enforced at the HTTP+DB layer *per call* but not across two separate calls by the same human. This
is accurately documented in-code (`route.ts`'s own "HONEST RESIDUAL" comment) and not a hidden gap,
but any credential runbook for this campaign should say so plainly rather than implying full
access-control disjointness.

---

## 5. Backup + rollback runbook, tested where testable

**The governing distinction (CLAUDE.md §N.3):** L1+ writers use per-chart delete-then-insert scoped
to `(chart_id x natural key)` — a rebuild REPLACES, never accretes. For the campaign's own `kala_*`
asset data, **a clean rebuild from upstream (`chart_facts` -> L1 -> L2 -> L3) is the rollback
mechanism by design**, not a point-in-time restore. This runbook therefore separates two genuinely
different recovery scenarios rather than treating "backup/rollback" as one undifferentiated concern.

### 5.1 Asset data rollback (a bad `ka_*` build) — design is sound; not independently re-tested this packet

Per CLAUDE.md §N.3 and Domain C's confirmation that the orchestrator's per-chart advisory lock and
`build_runs`/`build_run_assets`/`asset_throughput` lifecycle are real (not merely asserted): a bad
`ka_*` writer output for one chart is recovered by **re-running the writer for that chart**, which
delete-then-inserts scoped to `(chart_id, natural key)` and therefore cannot leave a mixture of old
and new rows. This is architecturally the correct answer and does not need a separate DB-level
restore for ordinary "asset X built wrong data" cases. **Not independently re-run by this packet**
(would require a real rebuild dispatch, forbidden by charter); cited from Domain C's verdict
(**READY**) covering "advisory locking, fleet cap, `build_runs`/`build_run_assets`/`asset_throughput`
lifecycle" with a real disposable-Postgres proof of the one property that needed it (the advisory
lock's mutual-exclusion behavior).

**What this does NOT cover, and is a real open question, not resolved here:** the cross-cutting
finding independently corroborated by multiple audit packets — `kala_activation` (`ka_kalasutra`)
and `kala_convergence` (`ka_sangam`) show **0 rows for the canonical chart** despite
`asset_throughput` recording that both writers *ran* and wrote 335,403 / 14,868 rows on 2026-08-13
(`state='stale'`, no `last_error`). `DATA_LOSS_DIAGNOSIS.md`, independently spot-verified by the
cycle-6 conductor (FK type `c` = CASCADE confirmed live for both `signal_id` FKs), identified the
mechanism exactly: both tables carry `signal_id REFERENCES bodha_msr_signals ON DELETE CASCADE`, and
an L2 `bo_laksana` rebuild after the L3 build cascade-deletes the L3 rows it never re-derives. **A
"rebuild is the rollback" doctrine does not by itself prevent this class of loss** — the loss came
from an *upstream* rebuild silently deleting downstream data via an FK cascade the downstream
writer's own re-run does not repair unless it is *also* re-run. This runbook flags it as an open
native decision item (already tracked in the audit's decision list), not something this packet
resolves — see `KALA_EXECUTION_DESIGN_v1_0.md` §3 for the rebuild-order sequencing requirement this
implies for the execution design.

### 5.2 `build_runs`/`asset_throughput` repair for a stuck run — design exists, live check performed

Per Domain C (fleet cap and lifecycle audited directly): "no `running`/`planned`/`paused` rows exist
at time of audit — the fleet cap is currently slack," meaning there is no currently-stuck run to
rehearse repair against live. **What this packet actually tested read-only, this cycle:** the same
`asset_throughput` reads used by the §2 readiness query themselves function as the stuck-run
diagnostic — `state`, `last_built_at`, `last_error` per `(chart_id, asset_id)` are exactly the
columns a repair operator needs to distinguish "genuinely running," "errored and needs a fresh
dispatch," and "stale but not erroring" (the `ka_kalasutra`/`ka_sangam` case above). This query
**does work against the read-only replica** — confirmed by the live run in §2 (run twice: packet
and conductor), which surfaced real `error`/`stale`/`lit` states and one real embedded Python
traceback (`ka_gochara_v3_century_materialize`'s `last_error`, a `BUILD-PROTECTED` guard refusal
citing "PARISHKARA MR-06 protection rationale" — itself informative: at least one L3 asset has a
build-time protection guard against overwriting protected rows, a real, live safety mechanism this
packet did not previously know to look for). **No DML-based "repair" (e.g. manually resetting a
`build_runs` row to `planned`) was tested or is authorized** — the charter forbids DML outright;
any actual stuck-run repair remains a production-mutation operation requiring the same
lease/authorization discipline as any other build.

### 5.3 Cloud SQL point-in-time restore — explicitly documented as unexecuted; not independently re-tested

Per Domain J §5 (cited, not re-run — this would require write access this packet does not have and
should not seek): a real, current, honestly-labeled DR runbook exists
(`00_ARCHITECTURE/briefs/pariprashna_swarm/G1_E_DURABILITY_DR_RUNBOOK_v1_0.md`, `status: CURRENT`)
and correctly scopes **all `kala_*` tables** into its 24h RPO/RTO tier — but its own frontmatter
states plainly: *"PITR enablement and the restore drill this runbook specifies are UNEXECUTED... PITR
on the production instance is disabled and no restore drill has ever been executed."* A separate,
narrower mechanism (`platform/scripts/backup/export_irreplaceable_tables.sh`, plain `pg_dump`-based)
is real and partially tested (a genuine, executed micro-test confirmed `pg_dump` with multiple
`--table` flags tolerates some tables being missing) but covers conversations and the prediction/
outcome/audit ledger — **not** the `kala_*` layer tables.

**Verdict for §5 overall: NOT READY for a Cloud SQL restore path; READY-by-design (not independently
re-tested this cycle) for the asset-rebuild rollback path, with one open unresolved hazard (the
cascade-delete loss above) that a rebuild-is-rollback doctrine does not automatically cover.** What
would flip the Cloud SQL side to READY: either PITR enabled with at least one executed restore drill
against `kala_*` tables specifically (matching the DR runbook's own stated requirement), or an
explicit native ruling that the orchestrator-rebuild path is the intended primary recovery mechanism
for this tier — rather than the runbook naming Cloud SQL restore as "the first resort" while that
resort has never been exercised.

---

## 6. Lane protocol

**One build lane.** Per Domain C, the orchestrator's per-chart advisory lock (`hashtext(chart_id)`,
Postgres session-level) plus a fleet cap enforced *before* the lock is acquired ("so a run that would
exceed the fleet cap doesn't block its own retry") together constitute the one production build lane
this campaign must respect — confirmed real via a disposable local Postgres 15 instance specifically
because mutual exclusion "cannot be meaningfully asserted with a fake cursor."

**Leases.** Production mutation of any of the five shared surfaces (per
`MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` v1.1 §3.3, item 1: migration apply, cutover dispatch,
orchestrator build/rebuild of shared-table assets, traffic promotion) is serialized through exactly
one mechanism: the lease table in `CAMPAIGN_COORDINATION.md` on the unprotected
`origin/campaign-coordination` branch. Per Domain G's own finding (cited, not re-fetched this
packet): claim/release is push-and-hope (non-fast-forward rejection is the only collision guard,
"optimistic concurrency by git," not a real lock), and **at least six Pūrṇa lease rows from
2026-09-19 still literally read `ACTIVE` in the status column despite being hours-to-days expired**
— Domain G's explicit warning applies to every future L3 conductor: *always compute "most recent
row by position, read its expiry, compare to wall-clock in IST" rather than string-matching the
literal word `ACTIVE`.* As of Domain G's last fetch, no lease is genuinely currently held by either
campaign (confirmed by timestamp comparison, not string match).

**Migration sub-ranges per stream.** Per the same plan §3.3 item 2, partitioned by numeric range, no
lease required: **Pūrṇa 1042-1069; L3 1070-1119; anything cross-cutting 1120+ by a logged request.**
The charter independently restates this exact range for L3. **No CI enforcement of this partition was
found** (Domain G grepped `.github/workflows/*.yml` for "1070"/"1120" and found neither) — the range
is honored by convention only. Migrations 1033-1069 (and specifically 1033-1041 per the charter) are
explicitly not this campaign's to touch or edit once applied.

**Regeneration rule.** Per §3.3 item 3: generated artifacts (`src/generated/*`,
`capability_estate_census`, `capability_knowledge`, the writer-digest inventory) are
regenerate-never-hand-edit; a merge-race loser rebases and re-runs the generators
(`npm run codegen:capability-estate-census && npm run codegen:capability-knowledge` [+ `:check`],
`platform/scripts/generate/nirmana_analysis_layer_pins.py`, the writer-digest generator). Domain H
independently confirms the writer-digest half of this mechanism is real and CI-enforced:
`provenance_inventory.py --check` fails CI if the checked-in `nirmana-writer-digests.json` doesn't
match a freshly recomputed hash, and `runner.py:374-390`'s `_verify_sidecar_code_matches_manifest`
hard-aborts at dispatch time on a code/manifest digest mismatch.

**Hub-edit protocol.** Per Domain H's 7-hub audit (`pipeline/transit_search.py`,
`services/ka_dasha_kala/`, `services/ka_temporal/`, `services/ka_graha_sancara/engine.py`,
`services/gochara_grammar/`+`services/gochara_intensity/`, `services/kala_trigger/`,
`services/taranga_kernel/`), before editing any of the 7 named hub modules, a session must:

1. **Re-derive (not assume) the current importer set** for that hub with a fresh `grep -rln`, since
   Domain H found a stale self-declared importer comment even in one hub's own docstring
   (`transit_search.py`'s header cites a nonexistent `services/ka_gochara/writer.py`).
2. **Treat the widest blast-radius assets as the re-validation floor**: `ka_gochara` and `ka_sangam`
   each depend on 3 of the 7 hubs (triple-hub) and are the two highest-risk single assets purely
   from hub-coupling; `services/ka_dasha_kala/` is the single widest hub, invalidating five L3 assets
   *and* the L4 `ph_nimitta` writer (a sealed layer with a live runtime dependency on an L3 service
   module — `services/ph_nimitta/dasha_consensus.py:106,163`) — any edit here needs cross-layer
   sign-off, not just an L3 one.
3. **Know the real detection boundary before trusting it.** The CI writer-digest check and the
   dispatch-time skew guard both correctly detect a *code-identity* change (no writer can silently
   ship a stale hash). Neither detects, nor automatically schedules a rebuild for, the case where a
   hub's code changes but a downstream `ka_*` writer's **already-built DB rows** are now stale as a
   result — `compute_downstream_closure` only sees `asset_registry.depends_on` edges between
   registered assets, and none of the 7 hubs are themselves registered assets. **The bridge from
   "hub digest changed" to "these N sibling writers' data needs rebuilding" is a manual, human,
   grep-and-read step** (Domain H's own method) — a hub-editing session must perform this step by
   hand every time, not assume CI will catch it.
4. Because `pipeline/transit_search.py` reaches the FROZEN L0 writer `bg_sky_calendar`, any edit to
   that hub in service of an L3 need carries **L0 blast radius by construction** and needs L0
   re-validation, not merely an L3 one.

---

## 7. Per-asset packet template

Conformant to the 8-section asset/interface brief contract named in PROMPT_0 §1 (*admission and
exact authority; current-state evidence; failure or missing capability; semantic change and expected
distinction; preservation/migration/history/rollback; focused proof matrix; implementation and review
discipline; terminal evidence packet*) and cross-referencing the ten elevation dimensions D1-D10 (per
`MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md`'s own repeated D1/D2/D8 citations — D1/D2 = contract
work, never gated by the serial build lane; D8 = whether the registered writer/service sits on the
live consumer path, per F5).

### 7a. Blank template

```markdown
# Per-Asset Elevation Packet — <asset_id>

## 1. Admission and exact authority
- Contribution-register disposition + DP obligation(s) mapped: <cite REGISTER:line>
- L3 strategy row and required transformation: <cite STRAT:line, A-nn id>
- L3-Q question(s) improved / product P-nn served / proving journey(s) participated in

## 2. Current-state evidence (measured, not inferred)
- §2 readiness-query row for this asset (paste live output, with the exact command that produced it)
- Physical census (rows, build/generation identity, oldest/newest, definition era) — aggregates only
- F13/F14 ladder ceiling under the CURRENT frozen definition

## 3. Failure or missing capability
- First failing boundary on F02's chain (question -> concept -> rule -> fact -> structural relationship
  -> temporal mechanism -> manifestation/gap -> delivered finding) — cite the proving-journey walkthrough
- Receiving-operator status (LIVE / DARK / DIVERGENT per F5) with file:line evidence

## 4. Semantic change and expected distinction (D1/D2)
- What this elevation adds beyond current behavior — the specific new distinction a consumer earns
- Contract-first note: is T3-T5 downstream source blocked on this asset's output shape being fixed?

## 5. Preservation / migration / history / rollback
- Idempotency pattern confirmed (delete-then-insert scoped to chart_id x natural key, CLAUDE.md §N.3)
- Migration number (if any), drawn from the L3 range 1071-1119, logged per §6 of this runbook
- Rollback path: rebuild-is-rollback, unless a hub/cascade hazard applies (§5.1 of this runbook) — name it if so

## 6. Focused proof matrix
- Type-appropriate acceptance test(s): arbitrary chart/convention, bounds/errors, applicability,
  failed/silent systems (per the plan's P0-8 pattern)
- Disposable-DB or non-canonical-chart proof for anything build-path-touching

## 7. Implementation and review discipline
- Own branch (one branch per packet, not per finding)
- Independent verifier: a different session/subagent than the author, re-running the exact commands
- Generated-artifact regeneration run and committed (writer-digest, capability census/knowledge)

## 8. Terminal evidence packet
- Freeze event id (asset_frozen) under the CURRENT definition
- F13/F14 rung actually reached, with the admissible event_type(s) cited
- Consumer-integration evidence (D8) or an honest `CONSUMER_INTEGRATED: NO EVENT TYPE EXISTS` note
  (per T3 §4 — do not fabricate a rung the event vocabulary cannot support)
- `Accepted N/22` delta this packet contributes, if any
```

### 7b. Filled-in example — `ka_graha_sancara` (Frontier stream, T0)

```markdown
# Per-Asset Elevation Packet — ka_graha_sancara

## 1. Admission and exact authority
- Disposition: "Position/motion service." DP07 (REGISTER:134).
- L3-A01: Ephemeris/Swiss service probe; zero materialized rows. Required: preserve numerical
  service/state safety; prove exact conventions, time, arbitrary-chart input, provenance, failures —
  a canonical probe is not full service qualification. Wave W2 (STRAT:271).
- L3-Q (inferred): Q01, Q03, Q09. P-nn (inferred): P09-10/P22, P09, P13/P19.
- Proving journeys: foundational/indirect in all three — supplies the geometry substrate, not
  named as a row-serving asset in any journey text.

## 2. Current-state evidence (measured)
- §2 readiness-query row (this cycle, live, canonical chart 482012f1-...):
  `L3|ka_graha_sancara|t3-2026-09-11-8b884eac|1|bg_ephemeris|f|f|f|f|||||none|none|NOT_READY-BLOCKED-ANCESTORS`
  — one unfrozen ancestor (`bg_ephemeris`) under the current definition; no physical_state row at all
  (never built under asset_throughput for this chart under a recorded state); f13/f14 ceiling both `none`.
- Ancestor `asset_frozen` = yes, but under `t0-2026-09-01-0e5b06fb` — not under the current `t3` definition.
  Events under t3 for this asset = 0 (independently corroborated by F2's direct DB count).

## 3. Failure or missing capability
- **Receiving-operator status: DIVERGENT (F5, high confidence).** `call_ephemeris_at_t` calls the
  sidecar's own `/api/compute/ephemeris_at_t` route with its own separate `import swisseph`,
  explicitly not `services/ka_graha_sancara/engine.py`. The live consumer path is a parallel
  implementation, not this writer's own code — D8/CONSUMER_INTEGRATED is not reachable through the
  registered writer as things stand.
- No U-nn maps to this asset in the traceability matrix — an orphan-obligation candidate (T1 §"Orphan
  obligations", item 1: "No U-id covers 6 of the 9 Frontier assets," ka_graha_sancara among them).

## 4. Semantic change and expected distinction (D1/D2)
- Elevation must either (a) redirect `call_ephemeris_at_t` to genuinely import and use
  `services/ka_graha_sancara/engine.py`, closing the divergence, or (b) get an explicit native ruling
  that the parallel sidecar route is the sanctioned path and the writer's role is narrower than its
  own strategy row implies. This is a decision for Strategy, not something this packet resolves.

## 5. Preservation / migration / history / rollback
- LIGHT writer per Domain H/Domain C conventions; delete-then-insert not directly applicable (zero
  materialized rows by design — a service probe, not a data materializer).
- No migration needed for the elevation itself; a migration would only be needed if the divergence
  fix in §4 requires a schema change.
- Rollback: trivial — no persisted rows to roll back; a bad service-probe run leaves nothing to clean up.

## 6. Focused proof matrix
- P0-8 pattern (already named in the dual-campaign plan as the sanctioned test for this exact asset):
  arbitrary chart/convention acceptance test, bounds/errors, applicability, failed/silent systems —
  run against the already-deployed sidecar per the plan's Phase 0 slate, not the canonical chart.
- Domain B's acceptance machinery (§4 of this runbook) governs how any resulting freeze event would
  be minted, once a route decision is made per §3 of this runbook.

## 7. Implementation and review discipline
- Own branch, e.g. `l3/p1-3-graha-sancara-consumer-route` (matches the plan's P1-3 packet naming).
- Independent verifier re-runs the divergence check (`grep -n "import swisseph"
  platform/python-sidecar/routers/*.py` and the corresponding grep against
  `services/ka_graha_sancara/engine.py`'s actual callers) fresh, not from this packet's citation.

## 8. Terminal evidence packet
- No freeze event exists under t3 today (0/22 confirmed, §2 above). This asset is the plan's own
  named smallest end-to-end proof candidate (P1-3, "Accepted 1/22") — its terminal packet does not
  yet exist and is Phase 1's first deliverable, not something to fabricate here.
```

---

## 8. Durable state/event ledger design for three streams

**The reporting contract, grounded in what the event vocabulary can actually support** (per
`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` §2, independently spot-verified by the conductor prior
cycle): only two F14/§8 gates have *any* admissible event type today — **Strategy agreed**
(`optimization_verdict_accepted`, as a decision record) and **Producer ready**
(`accepted_rebuild_observed` / `integrity_verified` / `probe_accepted` / the disposition family).
**Integrated, Deployed/operationally accepted, Consumer value demonstrated, and Empirically
evaluated all have zero admissible event types in the current schema** — `CONSUMER_INTEGRATED` and
`VALUE_EVALUATED` specifically have no designed receipt at all, a structural gap this campaign
inherits and must not paper over by inventing a rung the vocabulary cannot support.

**Ledger design, per the three execution streams** (Frontier / Spine / Kshetra+Century, per
`MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` §4's actual partition, confirmed by T1's own
self-correction against that document):

1. **One durable row per (asset_id, definition_revision, event_type, timestamp)** — this is already
   what `nirmana_evidence.nirmana_elevation_campaign_events` stores; the ledger design's job is not
   to invent new storage but to define the **read discipline** every reporting surface must apply:
   filter by the current frozen `definition_revision` before aggregating, per F1's fix, with no
   exceptions. Any new reporting surface built for this campaign inherits the §2 readiness query's
   pattern rather than re-deriving its own unscoped read.
2. **Per-stream state file** (per the dual-campaign plan §5 item 7's own report-format mandate,
   restated here as the ledger's surface contract): each of the three streams maintains its own
   append-only state artifact recording, at every packet close: `Accepted N/22 · Δ · Phase-0
   scorecard · current packet · exact blocker (owner, next action) · evidence ids`. No percentages
   derived from test counts — only from the admissible-event ladder above.
3. **Two metrics, never conflated** (plan §5 item 3, directly applicable to the ledger's schema):
   a **Phase-0 scorecard** (preserved branches N/9, docs PRs N/4, DP-SD-021 signed y/n, triage
   record n/8, safety PRs n/3, field-contract dossiers n/22, service-proofs n/4, baselines) tracked
   entirely separately from the **campaign metric `Accepted N/22`**, which only increments on a real
   terminal freeze event under the current definition — never on Phase-0 activity, however much of
   it completes. The ledger schema should carry these as two distinct top-level counters, not two
   views of one number.
4. **A receipt-gap column, not a silent zero.** Because `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` have
   no admissible event type, any per-asset ledger row reaching Producer-ready must explicitly render
   those two rungs as `NO_ADMISSIBLE_EVENT_TYPE` (or equivalent), not as an empty cell that could be
   misread as "not yet attempted" — this is the direct application of §N.8's Earned-Signal Principle
   to the ledger's own display: a status with no possible detector behind it must say so, not sit
   blank next to statuses that do have detectors.
5. **Cross-stream reconciliation point.** Because `ka_sangam` fans out to 7 downstream assets and sits
   at the T2 tier of the L3-internal critical path (per `KALA_EXECUTION_DESIGN_v1_0.md`'s own tier
   analysis, cited not re-derived here), the ledger must support a query that answers "which streams
   are blocked on Sangam's terminal freeze" without requiring a human to cross-reference three
   separate stream files by hand — a materialized view or a single cross-stream query (structurally
   similar to this runbook's own §2 artifact, generalized across all three streams' current packets)
   is the natural mechanism, not a fourth manually-maintained ledger.
6. **Phase-0 vs. campaign metric separation is not merely a display convention — it is load-bearing
   for honesty**, per the dual-campaign plan's own explicit warning (§5 item 1): "no autonomous
   heartbeat until `Accepted >= 1/22`... a heartbeat is earned by the first terminal asset, not
   assumed." A ledger that let Phase-0 activity inflate the campaign metric would recreate exactly
   the failure mode the plan was written to prevent (the prior Codex conductor's 37 idle branches
   under two shut gates).

**What this section does not do:** it does not propose new database schema or a new table — the
existing `nirmana_evidence.nirmana_elevation_campaign_events` table plus the per-stream state-file
convention already named in the governing plan are sufficient storage. This section's contribution
is the **read discipline and the two-metric separation rule**, both of which are process/reporting
conventions to be enforced by every session that touches the ledger, not a build item for this audit
to dispatch.
