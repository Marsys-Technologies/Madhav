---
artifact: CLAUDECODE_BRIEF_R6_TOTAL_ELEVATION
type: CLAUDECODE_BRIEF
version: 1.0
status: STAGED  # kickoff AFTER the current B-series acceptance campaign closes; copy to project-root
                # CLAUDECODE_BRIEF.md (or point the conductor here) at kickoff time
authored_by: Cowork (Fable-5), 2026-07-10
session_type: conductor_autonomous_swarm (bypass permissions; ZERO human gates; native reviews retrospectively)
campaign: R6 TOTAL ELEVATION — implement the ENTIRE defect register v3.0, every row verification-closed
backlog: 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md (frontmatter version 3.0 — THE backlog; ~130 open rows)
charts: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek, primary) · 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan, structural control)
may_touch:
  - platform/**
  - platform-mcp/**
  - 00_ARCHITECTURE/**
  - .github/workflows/**
must_not_touch:
  - platform/python-sidecar/pipeline/orchestrator/core/**   # FROZEN orchestrator — writers only, never the contract
  - 99_ARCHIVE/**                                           # oracles, read-only
  - 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md                   # EXCEPTION: the single Ketu-erratum line fix in Phase 4 (T-11)
  - CLAUDE.md
acceptance_criteria_summary:
  - Every open register row FIXED with Ring-3 prod evidence in its Status column, or DEFERRED-WITH-REASON in the seal
  - Golden battery (GOLDEN_SIGNALS_482012f1_v1_0.yaml) PASS >= 18/22, FAIL = 0                    [verify-against: prod]
  - Adversarial battery (register §11.4, 12 questions) >= 6 A-grades, 0 D-grades                  [verify-against: prod]
  - Blinded retrodiction re-run (register Section 10) all 8 metrics improved; Sade Sati hit preserved  [verify-against: prod]
  - TAP CI suite (7 conservation checks + grep set + 8 distribution gates) merged and GREEN
  - FORENSIC 7/7 PASS both charts after every L1 rebuild                                          [verify-against: prod]
  - main green, deployed, revision == final SHA, register + SESSION_LOG + CURRENT_STATE updated, R6_TOTAL_ELEVATION_SEAL_v1_0.md written
---

# R6 TOTAL ELEVATION — CONDUCTOR BRIEF (fully autonomous, verification-gated)

You are the CONDUCTOR. One session, bypass permissions, no human gates. You spin up parallel
executor sub-agents in dedicated git worktrees, each owning one lane; you own merges, deploys,
verification arbitration, and the register. **Nothing is "done" because an implementer says so —
a row closes ONLY when the independent verification protocol (§V) passes against PROD.**

## 0 — MANDATORY READS (in order, before any action)

1. CLAUDE.md §C (session-open discipline; SESSION_OPEN handshake; thread name
   "Madhav R6-TE-S1 — Total Elevation Conductor").
2. `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (v3.0) — READ FULLY. Every row ID cited
   below (Y-*, S-*, T-*, R-*, D-*, G-*, KP-*, K-*, C-*, O-*, M-*, V-*, SC-*, P-*) resolves there
   with evidence + fix approach. The register IS the per-row spec; this brief is the execution contract.
3. `00_ARCHITECTURE/TOTAL_AUDIT_PROTOCOL_v1_0.md` — verification doctrine (TAP batteries).
4. `00_ARCHITECTURE/GOLDEN_SIGNALS_482012f1_v1_0.yaml` — regression corpus (exit gate).
5. `00_ARCHITECTURE/DISCOVERY_ENGINE_ACCURACY_TEST_v1_0.md` — retrodiction re-run protocol.
6. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 + `git log --oneline -20` — live state; memory is stale.
   RECONCILE at kickoff: any register rows already closed by intervening campaigns (e.g. the
   B-series closed R-1's query_remedies size and C-2's D60 note) — verify their evidence, flip
   them, do NOT redo them.
7. `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2 — FROZEN WriterBase contract.
8. `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` — swarm roles (implementer/verifier split).

## R — STANDING RAILS (non-negotiable; embed in every lane prompt verbatim)

- **PyJHora-is-the-engine:** delegation over reimplementation for every M-row. No JH-parity oracle;
  verification = internal consistency + independent recompute + classical-rule re-derivation.
- **Canonical-or-floor:** canonical cited value OR floor NULL+reason. NEVER a computable substitute.
  Deleting a fabricated value (M-9 class) is a FIX, not a regression.
- **B.10:** no fabricated computation, no fabricated citations, and (M-22) no verification stamps
  as string literals — a verifier computes the verification column, or the column is NULL.
- **FROZEN orchestrator:** writers conform to WriterBase (`@register`, `run(ctx)`/substeps,
  `ctx.db_conn` never committed by writer, no build-state writes). A needed contract change = HALT
  the lane, log it, continue others.
- **Deterministic-first:** Python over LLM for data builds; product LLM calls = Gemini default,
  DeepSeek fallback, NEVER Anthropic APIs in product code.
- **L1-is-authority (§N.5):** L2+ cites fact_ids, never restates. Denormalized columns derived-by-JOIN
  at write time (V-1 doctrine).
- **Idempotency:** L1+ scoped delete-then-insert per (chart_id × natural key).
- **Surgical migrations ONLY** via Cloud SQL proxy (port 5433), numbered above main's max,
  ledger-reconciled. deploy.yml migrations are a silent no-op.
- **Destructive ops need reverse-citation:** before any DROP/rm/retire (KP-2, M-9), grep live code
  for every kill target; active citations → KEEP-OR-REPOINT.
- **No audience tier. No pre-building for later phases. dd-MMM-yyyy in any UI touch.**
- **Data regen only after sync-freeze:** prove prod == main (web AND job image, green CI) before
  any L1 rebuild; discard stale data, never salvage.

## W — WORKSPACE TOPOLOGY

Pre-create ALL worktrees up front (`git worktree add .claude/worktrees/r6-<lane> -b r6/<lane>`),
one branch per lane, never cross-write. Conductor owns `main`. Merge protocol per lane:
PR → quality gates → merge and VERIFY the merge (`gh pr view N --json mergeCommit,state` —
mergeCommit null = unclicked; then `git merge-base --is-ancestor <sha> origin/main`) → delete
worktree → `git worktree prune` (disk: worktrees grow 10+GB).

Deploy protocol (conductor-only): merge → CI green → deploy → **verify Cloud Run revision matches
the SHA** (`gcloud run services describe amjis-web --region=asia-south1
--format='value(status.traffic[0].revisionName)'`) BEFORE any prod probe; CDN adds 30-60s.
NEXT_PUBLIC_* needs build-arg + Dockerfile ARG/ENV; removals need `--remove-env-vars`.
Migrations via proxy, ledger row, live verification.

## P — PHASE PLAN (register "PHASED IMPLEMENTATION PLAN v3.0" is normative; this adds mechanics)

### PHASE 0 — HOTFIX BAND (7 parallel lanes; dependency-free; merge as each verifies)

| Lane | Branch | Register rows | Key mechanics |
|---|---|---|---|
| 0g CI-triage | r6/0g-ci | pre-existing CI failures (verify current state — a 2026-07 commit `49a83571 fix(ci)` may have closed them; if green, skip) | Everything downstream needs a trustworthy green. |
| 0a env-auth | r6/0a-envauth | R-15/O-6, R-16/O-5, O-2 | Env/config; verify each dead tool returns real content on prod. |
| 0b dead-tools | r6/0b-deadtools | R-9, R-10, R-12, R-14, T-7, V-8, P-6 | Align serving SQL to live columns; per-tool smoke test into the canary battery. |
| 0c yoga-hotfix | r6/0c-yogahotfix | Y-1 (unevaluable req shape → `(False,"rule_shape_unimplemented:<keys>")`), Y-9, Y-7, D-13 | Rebuild yoga labels both charts. Yoga count DROPPING massively = success. GS-11/GS-12 go RED until 2A — record it. |
| 0d lifetime-clips | r6/0d-clips | T-5, T-9, D-2/V-13 | Clip to [birth, horizon]; uniqueness constraints; rebuild affected assets. |
| 0e dasha-truth | r6/0e-dashameta | V-1 (+G-7, D-1), V-11, V-9, V-12 | lord_natal_* by JOIN; full timestamps; dasha_system key; CI equality gate; rebuild chart_dashas both charts. |
| 0f fallback-kill | r6/0f-fallbackkill | M-7, M-8 | Hard-fail pattern; grep `NATIVE_FALLBACK|FORENSIC hardcoded|482012f1|322\.61|51\.28` in writers → 0 computational hits. |

**Phase-0 exit gate:** all lanes Ring-3 verified; main green; deploy; prod probe of every fixed
tool; register rows flipped with evidence.

### PHASE 1 — COMPUTATION TRUTH (6 parallel lanes; BLOCKS Phases 2 & 4)

Doctrine per lane: read the PyJHora API first; DELEGATE; hand-rolled survives only as labeled
`computed_extension` where PyJHora has no equivalent; rebuilt rows for every replaced method.

| Lane | Branch | Register rows |
|---|---|---|
| 1a strength | r6/1a-strength | M-1 (→ fixes V-2/V-3/V-4), M-2, M-3 |
| 1b vargas | r6/1b-vargas | M-4, M-17, M-18 |
| 1c dashas | r6/1c-dashas | M-5, M-6, M-21 |
| 1d sensitive | r6/1d-sensitive | M-9 (delete/floor + real Pranapada), M-10 (completes S-2/S-10), M-11+V-6+V-7, M-16, D-9, D-10 |
| 1e structural-condition | r6/1e-structcond | M-12, M-13, M-14 (AFTER 1a merges — only intra-phase dependency), M-15, M-19, M-20, V-5 |
| 1f cross-cutting | r6/1f-verifstamp | M-22 (verifier owns the column + CI literal ban), D-3 (REQUIRED by 2A), D-14, D-4 |

**Phase-1 exit gate (mandatory before 2/4):** sync-freeze → full L1 rebuild BOTH charts on prod
(Cloud Run job) → FORENSIC 7/7 both → TAP-3b recompute battery green on derived values →
TAP-7 distinctness gates pass both charts → deploy → register flips.

### PHASE 2 — COMPOSITION (3 parallel streams, sequential inside; blocked by Phase 1)

**2A yoga-engine** (r6/2a-yoga): Y-2 → Y-3 (consumes D-3) → Y-4+Y-8 (+Y-10) → Y-5 → Y-6 → Y-11 →
Y-12+P-11 → K-4. Witness [verify-against: prod]: Sasa fires with real constituents; NBRY evaluated
(fired or honestly-absent+reason) on 482012f1; Anapha fires with Kemadruma correctly suppressed;
GS-11/GS-12/GS-21 → PASS.

**2B kp-restoration** (r6/2b-kp): KP-2 (reverse-citation first) → KP-1 → KP-3 → KP-4 → KP-5 → KP-6.
Witness: wealth query surfaces KP.CUSP.11 Mars(star)/Mercury(sub) + Rahu agency from 2H + Saturn
10L/11L earning channel = FORENSIC v6.0 §4 parity; GS-01/GS-02 → PASS.

**2C cgm-graph** (r6/2c-graph): G-1 → G-2 (uses Phase-1 virupa) → SC-6 → SC-7 → SC-8 → SC-9 →
G-3/G-4 → G-6 → G-8 → D-17/D-18 re-derived. Witness: `paths Saturn→bhava11` returns paths;
the Mercury→Saturn(11L)→11H + Mars→Rahu(2H) chain surfaces in a wealth/bhava-11 judgment with
fact_ids; edge distributions non-degenerate.

### PHASE 3 — SERVING INTEGRITY (6 lanes, parallel WITH Phase 2; conductor sequences the three
judgment_query-touching merges: 2A, 2B, 3f)

| Lane | Branch | Register rows |
|---|---|---|
| 3a param-conformance | r6/3a-params | R-18, R-17, SC-20/SC-21, R-6, R-27, pagination class |
| 3b budgets | r6/3b-budgets | R-1/R-8, T-6, R-24, R-25, R-26 |
| 3c serve-hidden | r6/3c-servehidden | S-1 (GS-03 witness), S-2/S-3, S-12, SC-1..SC-5, SC-11 (fixes R-2 with real data), SC-12, SC-13, SC-22, S-14, S-15, S-13 (live coverage matrix → CI) |
| 3d domain-truth | r6/3d-domains | SC-10 (ratchet 155→<20), P-2, D-5, P-5, P-7, P-8, V-10 |
| 3e honesty | r6/3e-honesty | S-8+S-11+R-28, R-21, R-22, R-5, SC-17/SC-18/SC-19 (boot-time pointer check), D-12, R-29 |
| 3f lateral-judgment | r6/3f-lateral | G-5+P-4, P-10, P-3 (needs S-12), P-9, C-4, C-2 (verify B-series already shipped the D60 note — reconcile, likely flip-only) |

### PHASE 4 — PREDICTION INFRA (one lane, ordered; blocked by Phases 1+2A)

r6/4-prediction: T-1 (sidecar revival, `sidecar_available:true`) → T-4 (activation build both
charts + floors) → T-12 (multi-cycle anchors; ≥60% adult-year coverage; >3 basis cycles) → D-16
(adverse valence from 2A dosha/bhanga; valence gate) → P-1 (pact ACTIVATION rebuild: running-MD/AD
input; "2070" and "twins-invisible" become regression tests) → T-3 (as_of end-to-end, IST,
exclusive boundary) → T-13 → T-14 → T-8 → T-10 → T-11 (LEL intake 57 events + Ketu-erratum fix
per FORENSIC KP §4.2) → C-5 → SC-14/SC-15/SC-16 → K-1, K-2, K-3, K-5, K-6, K-7.
Witness: pact_query(career, as_of 2027-09-01) cites Ketu MD running and completes TRIGGER with
real transit data; ≥1 dated adverse window exists retrodictively in 2000-2026.

### PHASE 5 — VERIFICATION HARNESS + ACCEPTANCE CEREMONY

r6/5-harness (parallel from day 1): TAP CI suite per register §11 + TAP-5 automate-this spec —
7 conservation checks, TAP-6 grep set, TAP-7's 8 gates, S-13 live matrix, per-tool smoke battery,
boot-time pointer validation. Merge early; ratchet as phases land.

**FINAL ACCEPTANCE CEREMONY (sequential, prod, after ALL phases):**
1. Full TAP re-run: golden ≥18/22 PASS 0 FAIL · adversarial ≥6A/0D · blinded retrodiction (fresh
   sub-agent, NO LEL access) all 8 metrics improved + Sade Sati hit preserved · TAP-9 declaration.
2. Register final pass: every row FIXED-with-evidence or DEFERRED-WITH-REASON; version bump.
3. `00_ARCHITECTURE/R6_TOTAL_ELEVATION_SEAL_v1_0.md`: scorecard, before/after, deferrals, risks, ledger.
4. SESSION_LOG append (atomic) + CURRENT_STATE §2 + this brief status → COMPLETE.
**Gate fails → NO gate-lowering. One fix-iteration per failing item, re-run failed battery only;
still failing → honest NOT-MET close with root-cause register (R5.2 discipline). An honest red
ceremony is a valid close; a gamed green is not.**

## V — VERIFICATION DOCTRINE (applies to EVERY lane; no exceptions)

**Three rings. A register row closes at Ring 3, never earlier.**

- **RING 1 — implementer self-check (worktree):** unit tests + tsc/vitest/pytest + lane probes.
  Grep ≠ compile check. Ship-but-don't-mount guard: integration probe reaches the new behavior
  through the real entry point (MCP tool/endpoint), not by importing the function.
- **RING 2 — independent verifier sub-agent:** DIFFERENT sub-agent (Vimarśaka role), receives ONLY
  the register row + branch; must (a) re-derive expected values independently (PyJHora direct /
  classical rule / archive citation), (b) attempt to FALSIFY (adversarial params, second chart,
  boundary dates, distribution checks), (c) confirm through the public surface. Written PASS/FAIL
  with evidence. **Conflicting reports → conductor runs the decisive test itself (R5.1 C3
  precedent) — never trust either self-report.**
- **RING 3 — prod verification (conductor, post-deploy):** merge+deploy+revision-check, then re-run
  the row's witness probe against PROD over the public channel, BOTH charts where chart-scoped.
  Tag `[verify-against: prod] [via: mcp_probe | psql_prod | curl_prod | gcloud]`; record evidence
  in the register row. Worktree-complete ≠ done; branch-complete ≠ prod-true. Per phase exit:
  wave-complete prod gate re-checks headline numbers on live prod.

Data-plane: localhost is code-plane only; DB writes ARE prod writes — writers under test use
scratch chart_ids until Ring-2 passes; never 482012f1 before that.

## K — KICKOFF SEQUENCE (conductor's first hour)

1. §0 reads → SESSION_OPEN → sync-freeze preflight → reconcile already-closed rows (§0 item 6).
2. Spawn Phase-0 lanes + Phase-5 harness lane in parallel worktrees.
3. Ring-2 → merge protocol; batch deploys (2-3 lanes/deploy); each row gets its own Ring-3 probe.
4. Phase-0 gate → spawn 1a-1f (1e waits on 1a for M-14 only).
5. Phase-1 gate (rebuild + FORENSIC + recompute battery) → spawn 2A/2B/2C + 3a-3f.
6. 2A merged → spawn Phase 4.
7. All merged → FINAL ACCEPTANCE CEREMONY → seal → close.
Maintain `00_ARCHITECTURE/R6_RUN_LEDGER_v1_0.md` continuously — per lane: spawn time, Ring-1/2/3
outcomes with evidence pointers, merge SHA, deploy revision, rows flipped. Write as you go.

*End of brief. The register is the spec; the rings are the law; an honest failure beats a gamed pass.*
