# KĀLA READINESS AUDIT — STATE  (rewritten completely by every cycle)

**Position:** cycle 1 complete (2026-09-22). W1 batch 1 done: 6 of 14 W1 packets (F3, F4, F6, F8,
Domain A, Domain B) DONE — findings verified, two deliverables written. Remaining W1 packets (F5,
F7, Domains D/E/G/H/I/J) are TODO for cycle 2+.
**Branch:** `l3/kala-readiness-audit` from `origin/main@20f4d02dc`. **Worktree:**
`/Users/Dev/madhav-l3/audit`. `origin/main` unchanged since seed — still `20f4d02dc`.

## Cycle 1 — what happened

1. **PR/sync hygiene:** clean. No PRs authored by this audit yet (0 opened). Branch pushed and
   matches HEAD. Most recent L3 lease on `origin/campaign-coordination` was released (not held).
2. **Wave picked:** W1 (parallel, read-only), first batch of 6: F3, F4, F6, F8, Domain A, Domain B.
3. **Fan-out:** dispatched via 6 parallel `Agent` calls (background). **3 of 6 stalled** on first
   attempt (`Agent stalled: no progress for 600s`) — F3, F8, Domain A/B (Domain B on first attempt
   too). Diagnosed as likely open-ended-exploration timeouts (broad greps / multi-file loops with
   no cap), not a rate limit. **Fix that worked:** retried each with a tighter brief — explicit
   "keep every command short-running and capped," a small fixed command budget, one-shot `psql -Atq
   -c` only (no interactive REPL), narrower greps with `head -N`. All 4 retries completed cleanly.
   **Lesson for future cycles:** write W1/W2 subagent briefs with this constraint from the start,
   not as a retry-only fix — it cost real wall-clock this cycle.
4. **Integrate:** every packet's headline claim was independently spot-re-run by the conductor
   (not just read) before being marked DONE — see each packet's own note below and the
   verification logs embedded in `KALA_DAG_RECONCILIATION_v1_0.md` §7 / `KALA_PRIVILEGE_MATRIX_v1_0.md`
   §3. Two deliverables promoted to final form; four remain as `_work/*.md` pending the W4 synthesis
   (`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md`, not yet written — needs the rest of W1 + W2 first).
5. **Commit + push:** this cycle's commit follows this file.

## Observed at seed (carried forward, still accurate as re-measured this cycle)
| Fact | Value |
|---|---|
| `origin/main` | `20f4d02dc` (#2703) — unchanged since seed |
| Leases on `origin/campaign-coordination` | none ACTIVE (re-confirmed cycle 1) |
| PR #2695 | OPEN / BLOCKED — **re-confirmed cycle 1, see F8 below, with exact failing-check evidence** |
| Current campaign definition | `t3-2026-09-11-8b884eac`; frozen under t3: L0 0/40 · L1 0/19 · L2 8/22 · L3 0/23 |

## Cycle 1 findings summary (full detail in each deliverable / `_work` file)

- **F3 (DAG reconciliation) — DONE.** → `KALA_DAG_RECONCILIATION_v1_0.md`. 5 real sources (seed
  splits into stale MIG345 + current SEED-TS). 2 of 4 previously-known discrepancies confirmed
  (worse than stated); 2 traced to a misread CI self-test fixture, not a real source, and
  corrected. New highest-severity finding: MIG345's `ka_gochara` row describes a service migration
  563 deleted and renamed over — stale identity, inert against current DB but a documentation
  hazard. New process finding: frozen-manifest protection has **never fired** for 12/23 assets
  including `ka_sangam`. `dag_edge_guard.py` structurally cannot see seed-vs-live drift (compares
  live-vs-code only) — confirmed by direct read, not inference.
- **F4 (privilege matrix) — DONE.** → `KALA_PRIVILEGE_MATRIX_v1_0.md`. Charter numbers re-verified
  exactly except "258/431" → corrected to **253/431**. **Two active assets confirmed hard-fail on
  build today**: `ka_moorti_nirnaya` (`bg_transit_moorti`, zero guard) and `ka_kshetra`
  (`phala_rectification` in mandatory stage3, zero guard; separately `bg_synthetic_cohort*` has a
  try/except with no `SAVEPOINT`, same net failure). `ka_bhavishya_lekha` safe on first build,
  fails on rebuild (existence-check, not privilege-check, guard). Independently re-verified via
  live `has_table_privilege` query this cycle. **Repair candidate for native queue: grant SELECT
  on 4 named tables to `data_plane_builder`** — small, targeted, not yet authorized.
- **F6 (deploy lag) — DONE**, in `_work/F6.md`. Corrects the brief's premise: **web is already
  current** (`20f4d02dc`), only MCP/sidecar/builder image remain at `09d998940` (5 commits behind).
  None of those 5 commits touch L3 writer/consumer paths (confirmed by path-glob check + the
  deploy workflow's own live gate log, `pipeline=false`, correctly). The one substantively
  important commit in the gap (`d9070900d`, migration 1070's `data_plane_builder` grants) is a DB
  migration, path-filter-exempt by design, and independently confirmed applied+successful via CI
  log (fail-closed self-check). Verdict: **READY, conditionally** — flips to NOT READY if a future
  commit touches builder-image paths without a deploy, or if the live grant re-check (blocked this
  session, DB proxy at the *wrong port* was tried — 5433 not 5434 — worth re-attempting cycle 2)
  contradicts the CI log.
- **F8 (PR #2695 state) — DONE**, in `_work/F8.md`. Confirmed exactly: OPEN, MERGEABLE but
  `BLOCKED`, sole failing check is `Unit Tests` — hash/receipt divergence against Pūrṇa-owned
  `BEYOND_ACARYA_ACCEPTANCE_v4/v5.json` and `tests/pariprashna/route_ports/baseline/*`, unrelated
  to PR #2695's own diff. **Both bugs it fixes are confirmed still live on `main`** (independently
  re-grepped by the conductor): `dispatch_frozen_rebuild.py`'s hardcoded dev-absolute
  `WRITER_DIGESTS_PATH` (resolves to a demonstrably stale/divergent file on at least this machine)
  and `call_dasha_eligibility`'s `'lahiri'` default (should be `DEFAULT_AYANAMSHA` =
  `'lahiri_chitrapaksha'`, matching the other 4 wrappers in the same file). **Verdict: campaign
  must not dispatch `dispatch_frozen_rebuild.py` through unpatched `main` today** — would commit a
  provenance receipt asserting a code identity that never ran (§N.8 violation, not hypothetical).
- **Domain A (campaign evidence integrity) — DONE**, in `_work/DOMAIN_A.md`. **NOT READY.**
  Definition lineage clean (6 definitions, no gaps/overlaps). **New finding beyond F1**:
  `capsule_audit.sql` — the tool whose own header claims it exists specifically to prevent this
  failure mode — shares F1's exact defect class: zero `definition_revision` filtering in any of
  its 3 queries. Not hypothetical: `asset_frozen` fired 111 times against only 98 currently-frozen
  assets (≥13 entities frozen under more than one definition), so §1/§2's "0 violations" PASS
  cannot currently distinguish "verified under `t3`" from "verified at some point under some
  definition." §2 (identity-separation) is structurally sounder (per-event, not cross-revision) —
  its PASS is more trustworthy. Secondary: the two earliest superseded definitions have zero
  traceable events (6-day evidence blind spot, non-blocking).
- **Domain B (acceptance machinery) — DONE**, in `_work/DOMAIN_B.md`. **READY**, one non-blocking
  follow-up. `nrec` refuses identity mismatches before minting (exit 2) and hardcodes
  `--include-email` — the previously-costly silent-403 footgun cannot be triggered through the
  sanctioned tool. HTTP route fails closed at every branch (401/403/400). DB trigger
  `nirmana_elevation_guard_server_reconstructed_insert` stamps `writer_identity` from
  `session_user` (DB-role-authoritative). One self-disclosed residual (both service accounts'
  `serviceAccountTokenCreator` resolve to the same human principal — procedural, not credential,
  separation) not independently re-checked against live IAM this cycle — queued for cycle 2+.

## Packet table

| Packet | Wave | Status | Output | Notes |
|---|---|---|---|---|
| F3 four-way DAG reconciliation | W1 | **DONE** | `KALA_DAG_RECONCILIATION_v1_0.md` | verified cycle 1 |
| F4 privilege matrix | W1 | **DONE** | `KALA_PRIVILEGE_MATRIX_v1_0.md` | verified cycle 1; repair candidate queued |
| F5 consumer-path trace ×22 | W1 | TODO | `_work/F5.md` | feeds T1; not attempted cycle 1 |
| F6 deploy lag | W1 | **DONE** | `_work/F6.md` | verified cycle 1; feeds W4 synthesis |
| F7 data census | W1 | TODO | `_work/F7.md` → `KALA_DATA_CENSUS_v1_0.md` | aggregates only; not attempted cycle 1 |
| F8 PR #2695 state | W1 | **DONE** | `_work/F8.md` | verified cycle 1; feeds W4 synthesis |
| Domain A | W1 | **DONE** | `_work/DOMAIN_A.md` | verified cycle 1; NOT READY verdict |
| Domain B | W1 | **DONE** | `_work/DOMAIN_B.md` | verified cycle 1; READY verdict |
| Domain D E G H I J | W1 | TODO | `_work/DOMAIN_<x>.md` | not attempted cycle 1 |
| F1 egate repair + sibling sweep | REPAIR | TODO | PR `l3/egate-definition-scope` | **now also covers `capsule_audit.sql` per Domain A finding — sibling sweep scope confirmed non-empty, not hypothetical** |
| F2 inheritance quantification | W2 | TODO | `_work/F2.md` | options with cost/risk; do NOT choose |
| T1 traceability ×3 clusters | W2 | TODO | `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md` | needs F3/F5 first |
| T2 proving journeys | W2 | TODO | `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md` | |
| T3 acceptance-regime mapping | W2 | TODO | `KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md` | Domain A's capsule_audit finding is directly relevant input |
| T4 brief conformance | W2 | TODO | `KALA_BRIEF_CONFORMANCE_v1_0.md` | Gochara v0.3 present |
| T5 tensions · T6 boundaries | W2 | TODO | `_work/T5.md`, `_work/T6.md` | |
| Domains C F | W2 | TODO | `_work/DOMAIN_<x>.md` | C on a disposable DB only |
| §5 execution/velocity design | W3 | TODO | `KALA_EXECUTION_DESIGN_v1_0.md` | |
| §6 setup + runbook | W3 | TODO | `KALA_CAMPAIGN_RUNBOOK_v1_0.md` | tested, not asserted |
| Readiness audit synthesis | W4 | TODO | `KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` | needs rest of W1+W2 |
| Verdict + native decision list | W4 | TODO | in the readiness audit + this file's list below | F2 first |

## In flight

None — all cycle 1 dispatches completed (after retries) and were integrated before cycle close.
No PR opened this cycle, no deploy dispatched.

## Budget

| Resource | Used | Ceiling |
|---|---|---|
| Cycles | 1 | 40 |
| Subagent dispatches | 10 (6 initial + 4 retries) | 120 |
| PRs opened | 0 | 6 |
| Deploy dispatches | 0 | 2 |
| Production mutations | 0 | **0** |

## Native decision list (accumulates, ordered by work unblocked)

1. **F2** — how does definition `t3` relate to freezes recorded under superseded definitions?
   (still to be quantified — cycle 2+ packet, unstarted).
2. **F4 repair candidate** — grant `SELECT` on `bg_transit_moorti`, `phala_rectification`,
   `bg_synthetic_cohort`, `bg_synthetic_cohort_md` to `data_plane_builder`. Small, targeted,
   unblocks `ka_moorti_nirnaya` and `ka_kshetra` builds today. Not yet authorized or migrated.
3. **F8 / PR #2695** — needs either the Pūrṇa-owned `BEYOND_ACARYA_ACCEPTANCE_v5.json` baseline
   regeneration (separate owner/track) or an explicit scoped governance override to merge despite
   the one unrelated failing check. Until one happens, `dispatch_frozen_rebuild.py` must not be run
   through unpatched `main`.
4. **Domain A / capsule_audit.sql** — needs the same `definition_revision`-scoping repair as F1
   (`egate.sql`). Now confirmed non-hypothetical (111 `asset_frozen` events vs 98 currently-frozen
   assets). Recommend folding into the existing F1 repair PR's sibling sweep rather than opening a
   second PR — same defect class, same fix shape, same reviewers needed.

## Known trap encountered this cycle (add to future subagent briefs)

Unconstrained subagents (broad multi-file exploration, interactive-style `psql` sessions, unbounded
greps) stalled 4 of 10 dispatches on a 600s no-progress watchdog. Every retry with an explicit
"small fixed command budget, one-shot queries only, cap output with head -N" instruction completed
in well under the timeout. Write this constraint into every W1/W2 subagent brief from cycle 2
onward rather than discovering it via stall-and-retry each time.
