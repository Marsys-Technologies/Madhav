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
| RC-02 | **CLOSED via Resolver Ruling RC-02-001, merged+deployed** | `res/rc02-rc17-web-door-parity-and-dasha-fix` @ `4fc1b241` | ACCEPT (`ac9676ce`) + conductor Resolver ruling | DONE bar narrowed to shared-condition gate-flag parity (fixed, live-confirmed: `data-judgment-flags` SSE event live with `no_leakage_capabilities_stripped`) + measured floor-coverage improvement (2/16→8/16, RC-11 consequence). Full receipt-schema/item-set equality WONTFIX'd as genuine architectural difference. Merged via PR #716 (`7dcffa91`), deployed and SHA-confirmed. |
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
| RC-15 | **DONE** | — | conductor, direct | 18 `.claude/worktrees/wf_*` workflow worktrees removed; `res/integration*` (5), `res/rc*` (14), `docs/rc-ledger-*`/`docs/rc17-*` (4) branches deleted local+origin after confirming each merged (except `res/rc02-two-door-parity`, intentionally never-merged — its findings were explicitly restated in the merged v2 doc); `feat/w6-2-prashna-synthesis` + `fix/w6-1-prashna-scope-tuple` (merged W6.x fix branches) deleted from origin. `fix/w6.3-pattern-register-and-temporal-anchor` was already gone (auto-pruned). Final `git worktree list`: only `main` + one legitimately-active D-4b worktree (untouched, per §J) + one unrelated pre-existing worktree outside campaign scope (`badge-honesty-wt`, not `res/*`/`w6*`, left alone). Zero orphaned `res/*`/`w6*` branches remain anywhere. |
| RC-16 | **DONE — campaign COMPLETE** | — | conductor + independent fact-check agent (PASS) | `retrieval_impl/FINAL_REPORT.md` §H.6 rewritten (empty except RC-14 BLOCKED); `CURRENT_STATE_v1_0.md` §2 cross-campaign note added (read-only on D-4b); `SESSION_LOG.md` appended; `RESIDUAL_CLOSURE_FINAL_REPORT.md` written and independently fact-checked (PASS verdict, no unsupported claims found); this brief's own frontmatter `status` flipped ACTIVE→COMPLETE. **`CAPABILITY_MANIFEST.json` regeneration attempted then reverted** — `npm run manifest:build` produced a manifest that broke `drift_detector.py`'s CI gate (10 new HIGH fingerprint_mismatch findings on files this campaign never touched — main baseline is exit=3/216 findings, allowed; the regenerated manifest flipped this to exit=2/225, a hard failure). Root cause: the manifest generator and drift_detector's fingerprint check don't agree on what they hash for these entries — a pre-existing gap the rebuild surfaced, not one this campaign's own work caused. No residual needed a manifest content change, so reverted to `main`'s existing manifest rather than force a fix under seal time pressure. Flagged as a real gap for a dedicated future session (`RESIDUAL_CLOSURE_FINAL_REPORT.md` §5). |
| RC-17 (new, opened this session per §G) | **CLOSED, merged+deployed, live re-probe passed** | fix-cycle 1: `res/rc02-rc17-web-door-parity-and-dasha-fix` @ `bd2c35e1` (insufficient, superseded); fix-cycle 2: `res/rc17-fixcycle2-still-hallucinating` @ `4c6c1ade` | fix-cycle 2: ACCEPT-WITH-CAVEATS (`1af77103`), conductor mandatory 5-run production re-probe: **5/5 clean** | Fix-cycle 1 was independently verifier-ACCEPTED, merged, and deployed (`7dcffa91`) — a conductor live re-check then found the hallucination still present in a new, worse form (fabricated "as per your request" hedge + wrong "actual current period" claim, apparent cross-chart pattern bleed). Fix-cycle 2 rewrote the temporal-anchor wording to remove imperative/"treat this as" framing and prohibit the exact hedge phrases observed; merged+deployed (`ee76ff47`). Conductor performed the verifier-mandated >=5-run live production re-probe post-deploy: 5/5 runs clean, zero hedge-pattern hits, correct dasha stated plainly every time. Full evidence + raw SSE transcripts: `RC-17_WEB_DASHA_HALLUCINATION_v1_0.md` §12, `rc17_reprobe_evidence/`. Recommended (non-blocking) follow-up: wire a production-side hedge detector into `judgment_flags` so any future recurrence is caught mechanically. |

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
- **RC-02+RC-17 retry**: completed. RC-02 ACCEPTED and closed via Resolver
  Ruling RC-02-001. RC-17 fix-cycle 1 ACCEPTED by its verifier. Both merged
  via PR #716 (`7dcffa91`), deployed and SHA-confirmed
  (`amjis-web-01106-259`).
- **Post-deploy live re-check (conductor, per brief §I deploy-verification
  step) found RC-17's fix-cycle 1 insufficient** — see Incident 4 below.
  RC-17 reopened; fix-cycle 2 launched.
- **RC-17 fix-cycle 2**: ACCEPT-WITH-CAVEATS. Merged via PR #719
  (`ee76ff47`), deployed and SHA-confirmed (`amjis-web-01109-2vp`).
  Conductor performed the verifier-mandated >=5-run live production
  re-probe: 5/5 clean. RC-17 CLOSED.
- **Wave R-C fully closed**: RC-01, RC-02, RC-03, RC-04, RC-11 all ACCEPTED
  and RC-17 (new residual) ACCEPTED — every item in Cluster 1 (Live
  verification) and the RC-11/RC-17 defects it surfaced are now closed with
  live, deploy-confirmed evidence.

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
   than a true isolated worktree. Resolved once the source branch's own
   commit landed on `main` and the primary checkout's stray copy was
   confirmed byte-identical to the merged version, then removed so the
   primary checkout could fast-forward cleanly.
4. **RC-17's fix-cycle 1 was independently verifier-ACCEPTED, merged, and
   deployed to production — and was still wrong.** This is the most
   important finding of the campaign and is recorded here in full rather
   than quietly absorbed into a "fix-cycle 2" line. The verifier's ACCEPT
   for fix-cycle 1 was itself well-evidenced (live pre-fix reproduction,
   a faithful port of the known-working MCP-side fix pattern, 8 passing
   regression tests) — the process was not sloppy. What actually happened:
   the fix added a correct, factual temporal anchor to the synthesis
   prompt, and the regression tests correctly proved that anchor text
   reaches the model. What neither the implementer's regression tests nor
   the verifier checked was the model's *narrative framing* of that fact
   under live conditions — in production, the synthesis model wrapped the
   (correct) anchored fact in a fabricated "as per your request" hedge and
   then appended a wrong "your chart's actual current period is X" coda
   that appears to be cross-chart training-data pattern bleed (X exactly
   matches a *different* real chart's real dasha). This is a live,
   deploy-gated behavior that a unit test asserting "the anchor string is
   present in the prompt" cannot catch — it requires an actual live model
   call. **Caught by the conductor performing the brief §I
   deploy-verification live re-check that both RC-02 and RC-17's fix-cycle
   1 reports themselves flagged as an outstanding, not-yet-performed step**
   — i.e., the campaign's own discipline of never treating a deploy-gated
   claim as closed until independently re-confirmed post-deploy is what
   caught this, not a lucky accident. Fix-cycle 2 launched immediately;
   RC-17 reopened in the status table above. **Lesson for RC-16's final
   seal:** every "deploy-gated, not yet re-confirmed" flag left by any
   verifier in this campaign must be resolved by an actual live check
   before the campaign can claim COMPLETE — not assumed clean by default.

## Resolver rulings

See `RESOLVER_RULINGS.md` — currently RC-09-001/002/003, RC-10-001/002/003,
RC-04-001/002, RC-02-001.

## Outstanding deploy-gated re-checks (must clear before RC-16 seal)

Per Incident 4's lesson, every verifier note below flagged evidence as
"deploy-gated, not yet independently re-confirmed live" — tracked here so
none is silently assumed clean:

- [x] RC-11 (CR-118 fast-fails on `/api/chat/consult`) — confirmed live via
  RC-02's own investigation (0/10 `route_error`, was 6/10).
- [x] RC-02 (`judgment_flags` disclosure on web door) — confirmed live by
  the conductor post-PR#716-deploy (`data-judgment-flags` event present,
  `no_leakage_capabilities_stripped` flag correctly disclosed).
- [x] RC-17 (dasha-anchoring hallucination) — checked live by the conductor
  post-PR#716-deploy, found still present (new hedge form); fix-cycle 2
  deployed (PR #719, `ee76ff47`), conductor performed the mandatory
  >=5-run live production re-probe post-deploy: **5/5 clean**. CLOSED.

All outstanding deploy-gated re-checks are now cleared.
