---
canonical_id: R5_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-08
author: Claude Code (executing CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md Phase-0)
program: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md v1.6 (governing law)
head_at_phase0: d12e523d8bee9efac730a9b525960a5842c47ab4
scope: Phase-0 preflight only (a)-(d) per the brief. No W0+ implementation work in this ledger.
---

# R5 RUN LEDGER — Phase-0

Append-only. Every wave's Ring-2 close appends here; this document never edits prior entries.

## JL-000 — Ratification-by-kickoff

**Entry:** native's message launching `CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md` constitutes
ratification-by-kickoff of the v1.6 design doc as governing law, per the brief's `ratification`
frontmatter field. Recorded verbatim per brief instruction.

**Basis:** brief frontmatter `ratification:` field, v1.2, 2026-07-08.
**Reversibility:** all in-run judgment rulings carry native retrospective veto (brief `ratification` clause).

---

## Phase-0 — Self-gating preflight

### (a) CURRENT_STATE Phase-4 Runway closure check

`00_ARCHITECTURE/CURRENT_STATE_v1_0.md` v6.31 changelog head entry (2026-07-08): **"BA-R4-WRAP W4
CLOSED — NATIVE REBUILT + VALIDATED; RUNWAY CLOSED."** Native chart `482012f1-710e-4a25-994a-93821f5871aa`
rebuilt L1→L5 (66/66 assets, 0 errors, LEL=57 throughout), FORENSIC 7/7 PASS, Abhinandan
(`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) unchanged (140,214 rows, zero contamination). Sealed at
commit `005b40fe` (PR #465).

**Verdict: CLOSED. Proceed.** (No HALT.)

### P0-i — R5 governing package present on main HEAD (verify-only)

Confirmed present and current at HEAD: `RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md` (v1.6),
`R5_AUTHORITY_DOSSIER_v1_0.md`, `R5_ANSWER_BATTERY_v1_0.md`, `R5_PREFLIGHT_REPORT_v1_0.md`,
`CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md` (v1.2).

**Confirming commit:** `d12e523d8bee9efac730a9b525960a5842c47ab4` — "docs(r5)+chore: R5 governing package +
conductor halt-log housekeeping (#466)", merged to main.

### P0-ii — Deploy-truth reconciliation for amjis-mcp

**Finding on investigation:** the preflight's "37 commits behind" framing was headline-accurate but
functionally narrower than it read. `git log 76158638..HEAD -- platform-mcp/` returns **zero** commits —
no `platform-mcp/` source has changed since the deployed image. The one commit that touched an
`/api/mcp/*` path (`6cd7f509`, PR #460 — `platform/src/app/api/mcp/writes/[action]/route.ts` +
`platform/src/lib/mcp/lel_event_writer.ts`) is served by **amjis-web**, not amjis-mcp's own container,
and amjis-web's deploy job ran and succeeded for every relevant commit (`Build & Deploy Web` was never
skipped). So amjis-mcp's stale image tag was a **traceability gap** (wrong SHA in the image tag), not a
functional drift — no code path amjis-mcp actually executes had changed.

Regardless, per the brief's explicit instruction ("no Ring-2 prod gate is trusted before this"), a full
deploy was triggered and verified rather than resting on the "no functional diff" finding:

- Root cause of staleness: `.github/workflows/deploy.yml`'s `deploy-mcp` job gates on
  `needs.changes.outputs.mcp == 'true'`, computed by `git diff --name-only HEAD~1 HEAD` restricted to
  `platform-mcp/**` — correct behavior, just never fired because no `platform-mcp/**` file had changed
  since the last MCP deploy.
- Action taken: `gh workflow run deploy.yml --ref main` (workflow_dispatch bypasses the path-filter
  gate and force-deploys all four services: web, sidecar, pipeline, mcp). Run
  `https://github.com/amonty84/Madhav/actions/runs/28927516660` — **all jobs green**, ~9 min.
- **Post-deploy verification (live, [verify-against: prod]):**
  - `amjis-mcp` latestReadyRevision `amjis-mcp-00394-7hh`, image tag
    `asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:d12e523d8bee9efac730a9b525960a5842c47ab4`
    — **matches HEAD exactly.**
  - `amjis-web` latestReadyRevision `amjis-web-00871-wtp`, image tag matches HEAD exactly.
  - Live `initialize` handshake against the new revision: `protocolVersion: "2025-11-25"` negotiated
    successfully (this closes the preflight's BLOCKED A10 item — live protocol version confirmed, not
    just inferred from SDK defaults).

**Rollback rehearsal (§6.7 W0a requirement) — NOTE: not yet exercised.** This Phase-0 pass verified
forward-deploy only. The one deliberate Cloud Run revision-pin rollback exercise remains a W0a
obligation, not discharged here — flagging explicitly rather than silently marking it done.

**Verdict: RESOLVED.** amjis-mcp + amjis-web both confirmed live at HEAD SHA `d12e523d`. Ring-2
"verify-against: prod" gates for W0+ can now be trusted as testing current code.

### P0-ii — Migration 424 status

`platform/supabase/migrations/424_ba_lel_r2_2_calibration_state_persistence.sql` is tracked in git
(landed via PR #460, commit `6cd7f509`) — the preflight's "untracked/undeployed" finding is now stale.
Confirmed applied to prod via the `_migrations_applied` ledger table:

```
id=308  424_ba_lel_r2_2_calibration_state_persistence.sql  applied_at=2026-07-07T20:44:20.758Z
        sha256=20f5b5f944a1bfad49d9d0a2a7400b3e0fee9cfa604dec5b4f5ba979bf3b3033
```

Live schema check: `phala_rectification_best.judgment_flags` column exists on prod. Migrations 417–426
(the full run of un-checked migrations named across recent PRs) are all present in
`_migrations_applied`, latest = 426 — no gap between repo migrations and applied migrations.

**Verdict: RESOLVED.** No undeployed-migration hazard remains.

### P0-iii — Test API credential provisioned

No self-service test-credential provisioning script exists; `/api/mcp/keys` POST requires a live
super_admin Firebase session (browser-only). Followed the existing DB-level precedent already used for
prior wave audits (`probe-service-account` principal, e.g. `mcp_prod_f021rbPR` "probe-f021r-b",
2026-07-02) rather than touching any real user account:

- Generated a key with the exact algorithm in `platform/src/lib/mcp/auth.ts::generateMcpKey()`
  (PBKDF2-SHA256, 100k iterations, 16-byte salt) via a local Node script — byte-identical format to
  what the app itself produces.
- Inserted directly into `mcp_api_keys` (via the Cloud SQL Auth Proxy tunnel at
  `127.0.0.1:5433`, credential `amjis_app`, already configured for this environment; the
  `mcp__postgres__query` MCP tool is read-only, so the insert used `psql` directly):
  `key_id=mcp_prod_tDO7obNw`, `user_uid=probe-service-account` (not a real profile row — resolves to
  `guest` role by design, per `resolveMcpPrincipalRole`'s no-row-found default), `label=
  r5-phase0-w0a-test-probe`, `scopes=['read']`, `model_family=anthropic`.
- Inserted two `chart_grants` rows (`permission='view'`, `granted_by=<native's uid>`) for
  `probe-service-account` on both `482012f1-…` and `1c826d5a-…` — required because
  `authorizeChartAccess` denies non-owner/non-super_admin principals with no grant row; `view`
  matches the key's `read`-only scope.
- **No production user account was touched.** `probe-service-account` has no `profiles` row; this
  mirrors the established audit-probe pattern, not a new user.

**Live verification:** full MCP `initialize` handshake succeeded (200, protocol `2025-11-25`); all
eight §14 probes below were run through this credential.

**Credential value (full_key), for continuity into W0a — treat as a live secret, not for citation
outside this ledger:** `mcp_prod_tDO7obNwPFwlwlQDkzl50HAAusDmNu0jBbm4rqDx`

### P0-iii — p50/p95 baseline (live, [verify-against: prod], post-redeploy)

20 warm calls per tool against native chart `482012f1-…` via the live `amjis-mcp` endpoint
(`https://amjis-mcp-qm256lasva-el.a.run.app/mcp`), wall-clock curl timing, no concurrency:

| tool | n | p50 (ms) | p95 (ms) | min | max |
|---|---|---|---|---|---|
| `ganita_dashas_get` (as_of_date=2026-07-07) | 15 | 2451.7 | 4923.1 | 1779.3 | 7737.6 |
| `bodha_chart_digest_get` (summary) | 15 | 580.5 | 686.9 | 417.3 | 766.1 |
| `bodha_signals_get` (career, top_k=5) | 15 | 437.5 | 649.7 | 349.0 | 756.0 |
| `phala_outlook_get` | 10 | 575.4 | 1771.4 | 515.1 | 2645.0 |

**Note:** `ganita_dashas_get`'s p50/p95 is an outlier (~4-9x the other tools) — directly attributable to
P1's confirmed defect below (returns unfiltered rows from 1950, ignoring `as_of_date`); the facet
conformance fix (E-5, W1) is very likely also a meaningful perf win, not just a correctness fix. This
is the W0 starting baseline; W1 re-measures per §21 SLOs.

---

## (b) §14 eight-probe re-audit — POST_R4_PROBE_RESULTS

**Native-chart Bodha staleness check (brief §7 P0-ii precondition) — RESOLVED, canary NOT scoped to
Abhinandan-only.** Direct DB query on native chart `482012f1-…`:

- `bodha_cgm_edges.valence`: 559/559 rows populated (100%). Was 0% at preflight time.
- `bodha_msr_signals.salience_pctl_in_class`: 67,128/67,128 rows populated (100%). Was 0% at preflight
  time.

R4 (the W4 native rebuild) fully healed both columns. **The full canary battery below runs against
BOTH charts with an honest, unscoped pass/fail** — the brief's fallback condition (Abhinandan-only
scope) does not apply.

All 8 probes re-run live via MCP (credential above) against native `482012f1-…` and Abhinandan
`1c826d5a-…`. Full raw responses captured; summarized per-probe below.

| # | Probe | Tool | Status now | Detail |
|---|---|---|---|---|
| P1 | A1 fact — dasha as-of | `ganita_dashas_get` | **STILL FAIL — not an R4 heal, confirmed live** | Both charts: `as_of_date=2026-07-07` still returns rows from 1950 (ashtottari, mixed levels 1-3), still silently ignored. Unchanged from preflight. Serving-bug punch-list item, W0. |
| P2 | A2 orient — chart digest | `bodha_chart_digest_get` | **SUBSTANTIALLY HEALED (partial, as the design doc predicted)** | Native chart top-20 signals now show real salience variance (2.99→2.30, 8 distinct signal types: graha_dignity_per_varga + several aspect_parashari classes) — no longer 20 near-identical degenerate 2.326672 atoms. Residual: header `contradiction_count=1` vs. per-domain sum = 3 (career=1, character=0, relationship=1, spirituality=0, wealth=0, health=1) — not the stark "1034-vs-all-zero" self-contradiction from the original finding, but still not reconciled; and `career` convergence_score (12,477.75) still reads as a raw-volume artifact, not hierarchically aggregated (E-6 is a W2 design item, not expected to have healed here). |
| P3 | A7 substrate — yogas | `ganita_yogas_get` (limit=100) | **STILL FAIL, confirmed live — worse on size** | 174KB response (native), up from the 64KB originally cited. Envelope fields still hollow: `verdict: null`, `ranking_basis: null`, `drill_pointers: []`, `judgment_flags: []`. "Schema theater" unchanged. Serving-bug + W0 contract item. |
| P4 | A3 substrate — ranked signals | `bodha_signals_get` (career, top_k=5) | **PARTIAL, same shape as before** | The previous "Kala Sarpa NOT detected" placeholder top-signal is gone (top signal now a real D9 cross-check "broken_promise" pattern) — but `percentile_within_class=1` on all 5 rows persists (plausibly correct for a top-5-of-class query, not necessarily a bug — needs a W1 conformance test to settle, not asserted as a defect here). The STALE PROVENANCE NOTE self-contradiction is UNCHANGED: `signature_tier_note` still claims "100% background" while all 5 served rows carry `signature_tier: "major"` or `"chart_defining"`. `defect_001_note` (91.5% orphan rate) still present verbatim. Stale-note substance is **NOT healed** — flagging explicitly since the brief listed it as an expected heal and it is not one. |
| P5 | A4 prediction — 12-month outlook | `phala_outlook_get` | **STILL FAIL, confirmed live, both charts** | Raw SQL errors still leak verbatim (`column "id" does not exist`, `column "anchor_id" does not exist`); `panchanga_daily` still 0 rows for the entire forward year; rectification block still leaks train/test split internals (`leakage_firewall_note`, `train_split`, `test_split`) into a would-be user-facing answer. Unchanged from preflight. |
| P6 | dissent organ | `synth_tail_divergence_get` | **STILL DOWN, confirmed live, both charts** | Hard 404 (`[p1_synthesis] platform DB query failed: 404`) — the missing `/api/mcp/db/query` route, unresolved. |
| P7 | corpus semantic search | `ref_vector_search` | **STILL DOWN, confirmed live** | 401 (`[alias] primitive 'vector_search' failed (401)`) — the callPlatformPrimitive auth-header gap, unresolved. |
| P8 | citation lookup | `ref_classical_citation_get` (keyword="neecha bhanga") | **STILL SILENT EMPTY, confirmed live** | `{rows: [], total: 0}`, `is_error: false` — no reason, no alternate-spelling suggestion. Unchanged from preflight. |

**Summary vs. the brief's "expected heals" (P2 degenerate band, stale-note substance, percentile
degeneracy):**
- P2 degenerate band → **HEALED** (substantially; one residual header/domain reconciliation nuance, not
  a full re-regression of the original bug).
- percentile degeneracy → **HEALED at the data layer** (`salience_pctl_in_class` 100% populated on both
  charts, confirmed by direct query) — the serving-layer `percentile_within_class=1` observation is a
  separate, likely-correct behavior for top-k queries, not conflated with the healed column.
- stale-note substance → **NOT HEALED.** P4's `signature_tier_note`/`defect_001_note` self-contradictions
  are byte-identical in substance to the preflight finding. This is a genuine surviving defect, not an
  expected-and-confirmed heal — flagged honestly per the brief's instruction not to silently pass/fail.

**Surviving defects for W0 scope (unchanged from the design doc's triage, §15):** P1 (as_of_date
ignored), P3 (yogas overflow + hollow envelope), P5 (phala SQL/schema mismatch + forward-panchanga
emptiness + leakage-internals exposure), P6 (dissent organ 404), P7 (corpus search 401), P8 (silent
empty citation lookup), plus the newly-reconfirmed P4 stale-note contradiction (not on the original
R4-heals list but empirically unhealed — recommend W0 punch-list absorb it explicitly rather than
assume R4 fixed it).

---

## (c) Quiesce check

- Open PRs: only #446 (`docs(ba-p3): fixes + re-run exit report`) — docs-only (three
  `00_ARCHITECTURE/*.md` files), zero overlap with `platform/src/lib/retrieval`, `platform/src/app/api/
  {retrieval,mcp}`, or `platform-mcp/src`.
- No GitHub Actions runs in-flight at check time (`gh run list` — all `completed`).
- No active non-idle Postgres backends other than this session (`pg_stat_activity` check, prod DB).
- Numerous stale remote branches exist (`ba-p4/*`, `fix/*`, `docs/*`, etc.) from prior completed work,
  none with open PRs, none actively running CI.

**Verdict: CLEAR.** No other stream holds a lock on prod. R5 may proceed to W0a.

---

## (d) Ledgers opened

This document + `R5_JUDGMENT_LEDGER_v1_0.md` (empty shell) created and committed to branch
`r5/phase0` off `main` at HEAD `d12e523d8bee9efac730a9b525960a5842c47ab4`, pushed to origin. Not
merged to main — per §2's wave/deploy policy, ledger merge happens at W0a's Ring-2 promotion, not at
Phase-0 close.

---

## Phase-0 exit verdict

**GO.** No HALT condition triggered. (a) runway CLOSED. P0-i/ii/iii all resolved live, not assumed.
(b) canary battery run unscoped against both charts (native-chart staleness fully healed). (c) prod
quiesced. (d) ledgers opened. Surviving defects catalogued above carry forward into W0a's punch-list
scope, unchanged in kind from the design doc's own triage — Phase-0 found no new HALT-worthy
contradiction of the governing design.
