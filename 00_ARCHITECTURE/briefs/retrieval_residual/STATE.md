---
artifact: STATE.md
canonical_id: RETRIEVAL_RESIDUAL_STATE
version: 0.3
status: LIVE
governed_by: RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md
---

# Retrieval Residual Closure — Ledger

Conductor session started 2026-07-22. Fully autonomous per brief §D, native
directive 2026-07-22.

**Note on this file's history:** the v0.1/v0.2 revisions of this table
suffered content drift across several parallel merge commits (independent
feature branches each carried their own snapshot of this file from whichever
`main` they forked from; ordinary 3-way merges silently picked one side
rather than reconciling status changes). v0.3 is a full rewrite reconciling
true current state as of this rewrite. Going forward, this file is edited
only in the dedicated integration worktree (`/tmp/retrieval-res-integration`)
immediately before each PR, never inside individual RC lane branches.

## Pre-flight findings

- **D-4b status: ACTIVE throughout this session** (confirmed repeatedly —
  `wave/D-4b/*` worktrees and PRs #708, #709, #712 landed to `main` while
  this campaign ran). Per §J this session is READ-ONLY on D-4b. **RC-14 is
  expected to close BLOCKED**, not merged.
- Real infra confirmed: `gh` authenticated (amonty84), `gcloud` present, repo
  remote `origin` = `github.com/amonty84/Madhav.git`. Deploys and merges to
  main are REAL actions against a real production system — conductor performs
  merge/push/deploy steps itself at reviewed checkpoints (PR + required CI +
  `gh pr merge`) rather than delegating them into unattended background code.
- `retrieval_impl/FINAL_REPORT.md` §H.6 confirmed as residual source (R-1..R-10
  table present).
- Live authenticated MCP connector (`mcp__marsys-jis-direct__*`) already
  available in-session — satisfied RC-01's credential prerequisite with no
  provisioning needed.

## Residual status table

| ID | Status | Branch(es) | Verifier verdict | Notes |
|---|---|---|---|---|
| RC-01 | **ACCEPTED (live)** | — | live traces confirmed | `prashna_ask` predictive/remedial classes verified live on both charts (482012f1, 1c826d5a): `chart_header` populated, correct dasha anchoring, `unresolved_tools:[]`, NO-LEAKAGE flag present, completeness receipt intact |
| RC-02 | **OPEN — REJECTED (genuine FAIL)**, retry in progress | `res/rc02-two-door-parity` (original finding), `res/rc02-rc17-web-door-parity-and-dasha-fix` (fix, combined with RC-17) | FAIL (verified): web door served 2/16 floor items vs MCP door's 10/10, no `judgment_flags`/NO-LEAKAGE signal on web door at all | RC-11's chart_id fix (deployed) should close much of the floor gap; retry attempts full fix + re-verify |
| RC-03 | **ACCEPTED, merged+deployed** | `res/rc03-load-baseline` @ `e3d3f2f7` | ACCEPT | Live 4-point measurement via Native-Proxy-Resolver-adapted method (harness's own HTTP client had no reachable route/credential — confirmed, not a shortcut); 2-of-4 §9.7 axes covered (cache-hit W-28, fairness W-30 not measured — honestly disclosed); QoS no-thinning confirmed by direct inspection |
| RC-04 | **ACCEPTED (fix-cycle 2), merged+deployed** | `res/rc04-census-probe-rerun` @ `266ea935` | ACCEPT (`e7559e16`), after REJECT (`5787cf94`) | Census+probe re-run genuinely un-blocked (prior "Next.js runtime" blocker was a shortcut, not real); 5 dark tables dispositioned; CR-122/CR-123/CR-124 recorded (not fixed, correctly out of scope); 2 more dead-pointer defects found+fixed along the way |
| RC-05 | **ACCEPTED, merged+deployed** | `res/rc05-dead-tool-sweep` @ `07179367` | ACCEPT (`100e1051`) | `resonance_register`/`cluster_atlas` swept from discovery+remedial floors; live discovery+remedy traces both confirm `unresolved_tools:[]` |
| RC-06 | **ACCEPTED (fix-cycle 2), merged+deployed** | `res/rc06-golden-set` @ `9365a616` | ACCEPT (`fc1bb177`), after REJECT (`24d9bb04`) | All 14 WP-1.7 dead capabilities confirmed swept from golden set + baseline |
| RC-07 | **ACCEPTED, merged+deployed** | `res/rc07-synthesis-cost-cap` @ `818b61cc` | ACCEPT (`665764b2`) | Synthesis LLM call wired into `CostCapTracker`, fail-honest degradation |
| RC-08 | **ACCEPTED, merged+deployed** | `res/rc08-synthesis-truncation` @ `87a75921` | ACCEPT (`8e49b7c9`) | Bearing-aware truncation; live traces show flag firing only when genuinely warranted |
| RC-09 | **ACCEPTED, merged+deployed** | `res/rc09-dark-tables` @ `83f881f7` | ACCEPT (`b5d04650`) | 51/51 W1 dark tables terminal (this session, re-verification not re-derivation) |
| RC-10 | **ACCEPTED (fix-cycle 2), merged+deployed** | `res/rc10-namespace-gap` @ `e8376776` | ACCEPT (`e779d3f8`), after REJECT (`faca7ded`: invalid `ganita_condition_get` mapping) | 20/23 bridged + 3 honestly DEFERRED |
| RC-11 | **ACCEPTED, merged+deployed** | `res/rc11-cr118-fastfails` @ `abbe155e` | ACCEPT (`7f06c4ef`) | CR-118 root-caused (missing `chart_id` on web-door + MCP-sidecar query plans) and fixed; regression tests reproduce exact symptom |
| RC-12 | **ACCEPTED, merged+deployed** | `res/rc12-authz-hardening` @ `e7934363` | ACCEPT (`ad62ba90`) | `authorizeChartAccess` existence check for super_admin |
| RC-13 | **ACCEPTED, merged+deployed** | `res/rc13-session-pin-rename` @ `9e5419c8` | ACCEPT (`1ab6a330`) | `session_pin` → `provenance_stamp` rename |
| RC-14 | **EXPECTED BLOCKED** (D-4b active) | `impl/w5-breaking` | — | Branch found badly stale (~26k lines behind `main` — predates W6 synthesis/cost-cap/session_pin work entirely); not "ready to land in one command" as brief assumed. No risky rebuild attempted against a live-moving `main` while D-4b is active. Will close BLOCKED with this documented, per brief's own sanctioned exception. |
| RC-15 | OPEN (after RC-02/RC-17 land) | — | — | Branch/worktree hygiene |
| RC-16 | OPEN (last) | — | — | Final seal |
| RC-17 (new, opened this session per §G) | OPEN, in progress with RC-02 | `res/rc02-rc17-web-door-parity-and-dasha-fix` | — | Web-door dasha-anchoring hallucination bug discovered during RC-02's live investigation (web synthesis said "Mercury MD / Saturn AD" for a chart whose correct anchoring — confirmed by both its own chart_header and the MCP door — is "Saturn MD / Rahu AD"); not covered by the 2df42b61 MCP-only fix |

## Wave close log

- **Wave R-A** (RC-05,07,08,12,13): all 5 ACCEPTED first pass. Merged via PR
  #710 (`res/integration` → `main`, `651c6478`). Deployed; `amjis-web`
  revision `amjis-web-01100-2qk` / `amjis-mcp` revision `amjis-mcp-00451-fk9`
  both confirmed commit-sha `651c6478`.
- **Wave R-B** (RC-06,09,10): RC-09 ACCEPTED first pass; RC-06 and RC-10 each
  REJECTED once then ACCEPTED on fix-cycle 2. Merged in the same PR #710 /
  deploy as Wave R-A (batched).
- Ledger-only PR #711 merged (docs, no deploy trigger beyond what #710
  already covered).
- **Wave R-C first pass** (RC-02,03,04,11): RC-03 and RC-11 ACCEPTED (RC-03
  with 2 non-fatal doc corrections, applied); RC-04 REJECTED (3-item path to
  ACCEPT given); RC-02 genuinely FAILED (not a process failure — a real
  floor/gate-flag parity gap), surfacing RC-17 as a new defect per §G.
  RC-03+RC-11 merged via PR #713 (`844a23a0`), deployed and SHA-confirmed.
- **RC-04 fix-cycle 2**: ACCEPTED. Merged via PR #714 (`92113dbe`), deployed
  and SHA-confirmed on both `amjis-web` (`amjis-web-01104-5n2`) and
  `amjis-mcp` (`amjis-mcp-00452-r82`).
- **RC-02+RC-17 retry**: in progress (first attempt errored on an
  infrastructure connection drop before any task-specific commit; no work
  lost; respawned once per brief §D.6).

## Incidents (self-corrected)

1. **D-4b file capture in the RC-10 merge commit.** The `res/rc09→rc10`
   merge picked up in-flight, already-staged changes to
   `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/{STATE,REPORT}_D4B.md`
   from the concurrently-running D-4b campaign, which was sharing the primary
   working directory at that point — a must_not_touch violation. Caught
   before any push; both files reverted to pre-merge content in a follow-up
   commit before PR #710 opened. All further integration work moved to a
   dedicated isolated worktree (`/tmp/retrieval-res-integration`); the
   primary checkout was restored to tracking `main` only, never used for
   branch/merge work again this session.
2. **STATE.md content drift (this file).** Because several RC lane branches
   each carried their own copy of this ledger (created before later
   waves' updates existed), ordinary 3-way merges silently regressed some
   rows to stale content across PRs #713/#714. No merge conflict was
   raised (git saw them as non-conflicting line-level changes), so it went
   uncaught until this rewrite. Fixed by this v0.3 full rewrite reconciling
   true state from the actual PR/deploy/verifier record above. Going
   forward, ledger edits happen only in the integration worktree,
   immediately pre-PR.
3. **Unexplained working-tree modifications in the primary checkout**
   (`platform/src/lib/pipelines/shared/run_adapter_dispatch.ts` modified,
   `.../shared/__tests__/rc17_temporal_anchor.test.ts` untracked) observed
   after the RC-02/RC-17 retry launched — plausibly that agent's isolated
   worktree ended up pointing at/leaking into the primary directory rather
   than a true isolated worktree. Left untouched (not staged, not
   committed, not deleted) pending the retry's own completion and report;
   will be reconciled once that workflow returns.

## Resolver rulings

See `RESOLVER_RULINGS.md` — currently RC-09-001/002/003, RC-10-001/002/003,
RC-04-001/002.
