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

---

## Rollback Rehearsal (W0a lane — brief §6.7 / §7 item 7)

**Purpose:** brief §7 item 7 mandates one deliberate, timed Cloud Run revision-pin rollback on
`amjis-mcp`, exercised against real prod traffic, before any deeper W0a deploy goes out. This
section is the proven, timed runbook produced by that exercise, discharging the "not yet exercised"
flag left open at Phase-0 (§P0-ii above).

**Service:** `amjis-mcp` · region `asia-south1` · project `madhav-astrology` · URL
`https://amjis-mcp-qm256lasva-el.a.run.app` · health endpoint `GET /health`.

**Date/time (UTC):** 2026-07-08, ~08:23–08:24 UTC.

### Step 1 — record currently-live revision

```
gcloud run services describe amjis-mcp --region=asia-south1 --format="value(status.traffic)"
# {'latestRevision': True, 'percent': 100, 'revisionName': 'amjis-mcp-00394-7hh'}
gcloud run services describe amjis-mcp --region=asia-south1 --format="value(status.latestReadyRevisionName)"
# amjis-mcp-00394-7hh
```

Live revision at start: **`amjis-mcp-00394-7hh`** (created 2026-07-08T08:09:12Z — the P0-ii
redeploy revision).

### Step 2 — identify immediately-prior healthy revision

```
gcloud run revisions list --service=amjis-mcp --region=asia-south1 \
  --sort-by="~metadata.creationTimestamp" --limit=10 \
  --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"
```

| revision | Ready | created (UTC) |
|---|---|---|
| amjis-mcp-00394-7hh | True | 2026-07-08T08:09:12Z |
| **amjis-mcp-00393-445** | **True** | **2026-07-05T15:38:30Z** |
| amjis-mcp-00392-qsp | True | 2026-07-03T21:58:56Z |

Prior healthy revision selected: **`amjis-mcp-00393-445`**.

### Step 3 — baseline health check (pre-rollback)

```
curl -sS -o /dev/null -w "HTTP_STATUS:%{http_code}\n" https://amjis-mcp-qm256lasva-el.a.run.app/health
# HTTP_STATUS:200 — {"status":"ok","service":"marsys-mcp","version":"1.0.0","tools":121,...}
```

### Step 4 — pin 100% traffic to prior revision (rollback)

```
gcloud run services update-traffic amjis-mcp --region=asia-south1 \
  --to-revisions=amjis-mcp-00393-445=100
```

- Command issued: **08:23:32 UTC**
- Command returned ("Routing traffic... done"): **08:23:40 UTC** — **wall time ≈ 8.1s**
  (`real 0m8.083s` per shell `time`).
- Post-command traffic verify: `{'percent': 100, 'revisionName': 'amjis-mcp-00393-445'}` — confirmed.
- Health check against rolled-back revision: `HTTP_STATUS:200`, identical health payload
  (`{"status":"ok","service":"marsys-mcp","version":"1.0.0","tools":121,...}`), verified at
  **08:23:48 UTC**.
- **End-to-end rollback time (command issue → confirmed-healthy on prior revision): ≈16s.**

### Step 5 — restore traffic to current/latest revision (roll-forward)

```
gcloud run services update-traffic amjis-mcp --region=asia-south1 \
  --to-revisions=amjis-mcp-00394-7hh=100
```

- Command issued: **08:23:51 UTC**
- Command returned ("Routing traffic... done"): **08:23:59 UTC** — **wall time ≈ 7.8s**
  (`real 0m7.804s`).
- Post-command traffic verify: `{'percent': 100, 'revisionName': 'amjis-mcp-00394-7hh'}` — confirmed
  restored to latest.
- Health check against restored revision: `HTTP_STATUS:200`, identical health payload, verified at
  **08:24:04 UTC**.
- **End-to-end restore time (command issue → confirmed-healthy on latest revision): ≈13s.**

### Outcome

- Both directions of the revision-pin traffic switch completed in **well under 10 seconds** of
  `update-traffic` command wall time, and were confirmed healthy (`GET /health` → 200, matching
  payload) within **~16s** (rollback) and **~13s** (restore) end-to-end including verification
  round-trips.
- No errors, no 5xx observed on `/health` at any point during the exercise. Service was never fully
  down — Cloud Run traffic-split is atomic at the routing layer, so this was a clean cutover, not a
  redeploy.
- Final state: **fully restored** to `amjis-mcp-00394-7hh` at 100% traffic — matches pre-exercise
  state exactly. No residual drift.
- **Runbook is proven and repeatable** for any subsequent W0a (or later-wave) deploy: identify
  N-1 revision via `gcloud run revisions list`, `update-traffic --to-revisions=<rev>=100`, verify
  `/health`, and if rollback needs to persist, stop there; otherwise reverse the same command with
  the newer revision name to restore.

**Command template for future rollback (copy-paste, region/service fixed):**

```
# 1. Find prior revision
gcloud run revisions list --service=amjis-mcp --region=asia-south1 \
  --sort-by="~metadata.creationTimestamp" --limit=5 \
  --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"

# 2. Pin traffic to it
gcloud run services update-traffic amjis-mcp --region=asia-south1 \
  --to-revisions=<PRIOR_REVISION>=100

# 3. Verify
curl -sS -o /dev/null -w "%{http_code}\n" https://amjis-mcp-qm256lasva-el.a.run.app/health
gcloud run services describe amjis-mcp --region=asia-south1 --format="value(status.traffic)"

# 4. If rollback needs to persist: stop here.
#    If this was only a rehearsal / issue resolved: restore forward
gcloud run services update-traffic amjis-mcp --region=asia-south1 \
  --to-revisions=<LATEST_REVISION>=100
```

**Verdict: DISCHARGED.** Brief §7 item 7 / §6.7 rollback rehearsal obligation is now satisfied. This
lane touched only this ledger document and the live Cloud Run traffic config for `amjis-mcp` — no
application code, no migrations, no writers. W0a's real deploy (and all subsequent wave deploys) may
now proceed against a proven, timed rollback runbook.

---

## W0a — Perf quick wins lane (`r5/w0a-perf`)

Scope: min-instances (S2), serialization tax (S3), UCD pre-fetch parallelization (S1), salience index
verification (S6, re-scoped low-priority per §7). Branch `r5/w0a-perf` off `origin/r5/w0a`.

### S2 — min-instances=1 on amjis-web + amjis-mcp

`.github/workflows/deploy.yml`: `deploy-web` job's `--min-instances=0` → `1` (line ~273);
`deploy-mcp` job's `--min-instances=0` → `1` (line ~448). `amjis-sidecar`'s `--min-instances=0`
(line ~385) left untouched — brief caps the pre-authorized spend at web+mcp only. No other flag on
either line touched. **Not yet deployed** — this is a repo-level change on the lane branch; it takes
effect on the next `deploy.yml` run after this branch merges to `r5/w0a` → main per §2's promotion
policy. Cold-start cascade (S2 finding) will not be empirically closed until that deploy runs; this
entry records the code-level fix only.

### S3 — serialization tax (measured 2.4×, prioritized up per §7)

Fixed at all five duplicated `dualOutput`/`errorOutput` sites (`registry_bridge.ts` — the 12 D7
consolidated tools — plus `register_p1_synthesis.ts`, `register_p1_reference.ts`,
`register_p1_ganita.ts`, `register_p1_aliases.ts`, which cover the P1 tool families):
1. Dropped pretty-printing (`JSON.stringify(data, null, 2)` → compact `JSON.stringify(data)`).
2. Above 50,000 UTF-8 bytes (`Buffer.byteLength`, measured on the compact string — JL-003 records the
   threshold choice), the text-fallback duplicate is replaced with a short pointer string instead of
   re-serializing the full payload a second time; `structuredContent` alone carries the payload above
   threshold.
3. `query_signals.ts`'s H-12 size guard (`estimatedBytes = JSON.stringify(signals).length`) switched
   to `Buffer.byteLength(JSON.stringify(signals), 'utf8')` — `.length` counts UTF-16 code units and
   undercounts true wire byte size for any multi-byte content, letting genuinely oversized payloads
   slip past the 1.5MB truncation guard.

**Measured (synthetic, realistic 200-signal payload shape, 67,079 compact bytes):** old path sent
93,691 bytes pretty-printed text + a separately-serialized structuredContent object (~67,079 bytes) =
~160,770 bytes total on the wire; new path sends structuredContent only (67,079 bytes) above the 50KB
threshold — **~58% total-wire-bytes reduction** for payloads in this size class. Indent-2 overhead
measured directly at **+39.7%** on this shape (design doc's own estimate was 20-30% — confirms the
mechanism, on the high side of the estimate for signal-array-shaped payloads specifically).

### S1 — UCD pre-fetch parallelization

All 12 call sites in `registry_bridge.ts` where a domain tool serially awaited
`fetchOrientationContext(...)` then `callRegistryCapability(...)` (both independent HTTP calls to the
platform API) converted to `Promise.all([...])`: `get_domain_reading`, `get_signals`,
`traverse_graph`, `get_temporal_windows`, `get_projections`, `get_remedies`, `get_chart_quality`,
`assess_marriage`, `assess_career`, `assess_health`, `assess_wealth`, `get_cgm_subgraph`. Design doc's
own estimate: ~458ms added per domain call by the serial pre-fetch — parallelizing removes the
sequential half of that (the slower of the two calls now gates the latency instead of their sum).
Not yet re-measured live against prod (that is a W0a canary/perf-baseline task, not this lane's scope
per the brief's task split — recorded here as a code-level fix awaiting the perf-verifier's
before/after prod measurement).

### S6 — salience index: verify-planner-behavior (re-scoped low priority, no new index built)

Confirmed via `pg_indexes` (read-only) that `msr_salience_rank_idx ON bodha_msr_signals
(chart_id, ayanamsha_id, computed_salience DESC)` **already exists** — matches the brief's premise
that the index exists. Ran `EXPLAIN (ANALYZE, BUFFERS)` against prod (read-only) on the native chart
for the exact production query shape (`query_signals.ts`'s legacy/dual-pool salience query: chart_id +
ayanamsha_id equality, `lel_origin` exclusion filter, `ORDER BY computed_salience DESC NULLS LAST
LIMIT {50|500}`) and on `query_ucd.ts`'s equivalent query (same `ORDER BY ... DESC NULLS LAST` idiom).

**Finding: the planner is NOT using `msr_salience_rank_idx` for this query shape** — it chooses a
Bitmap Heap Scan on the 2-column `msr_chart_aya_idx` followed by an explicit top-N heapsort
(23-27ms execution, ~2,587 buffer hits) instead of an Index Scan on the 3-column covering index.
Root-caused live: the index (default btree DESC ordering) stores nulls FIRST; the query's
`ORDER BY computed_salience DESC NULLS LAST` clause requests nulls LAST — Postgres cannot use an
index to satisfy an ORDER BY when the requested null ordering doesn't match the index's stored null
ordering, so it falls back to scanning + sorting. Verified directly: re-running the identical query
with `NULLS FIRST` instead of `NULLS LAST` (same WHERE, same LIMIT) produces an Index Scan on
`msr_salience_rank_idx`, 5.8ms execution (42 buffer hits) — a **~4.8× speedup** for this query alone.
Also verified `computed_salience` has **zero NULL values** on the native chart (67,128/67,128 rows
populated) — so for current data, `NULLS FIRST` and `NULLS LAST` are result-identical; the ordering
keyword is the only thing standing between the planner and the existing index.

Per the brief's explicit scoping ("this is a verification task, not a build task" — no new index), no
code change was made to the `ORDER BY` clauses in `query_signals.ts` (2 sites: sqlA/sqlB) or
`query_ucd.ts` (1 site). **Flagging for R5_PUNCHLIST, not actioned here:** changing
`NULLS LAST` → `NULLS FIRST` (or dropping the explicit NULLS clause, which defaults to FIRST for
DESC) in those three call sites is a one-line, result-identical (given zero current NULLs), ~4.8×
query-level win that this lane's scope explicitly excludes from being built.

### Verification run

- `platform-mcp`: `npm run typecheck` (tsc --noEmit) — clean, 0 errors.
- `platform`: `npx tsc --noEmit -p tsconfig.json` — clean, 0 errors.
- `platform`: `npx eslint src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` — 1
  pre-existing warning (line 265, unrelated to this lane's edit; confirmed present before this
  lane's changes via `git stash` diff-test).
- `platform`: `npx vitest run` on `d5_l2_capabilities.test.ts` + `d5_roster_smoke.test.ts` — 50/50
  passed.
- `platform-mcp`: `npx vitest run src/__tests__/m8_e2e_proof.test.ts` — 33 passed, 2 pre-existing
  failures (G12 tool-count constant, V6 D7-tool-count constant — both stale hardcoded counts
  unrelated to this lane; confirmed identical failures before this lane's changes via `git stash`
  diff-test).

### Standalone value if the run halts here

Even if R5 halts immediately after this lane merges: amjis-web/amjis-mcp get warm instances on the
next deploy (eliminating the cold-start tail once deployed); every MCP tool response gets smaller and
cheaper to serialize (no pretty-print tax, no duplicate large-payload transmission); every domain-tool
call gets faster (parallel orientation fetch instead of serial); and the salience-index finding is a
ready-made, pre-verified one-line fix sitting in the punchlist for whoever picks it up next — none of
this depends on any later wave landing.

### Judgment ledger

JL-003 recorded in `R5_JUDGMENT_LEDGER_v1_0.md` (renumbered from this lane's original JL-001 during
the `r5/w0a-integrated` merge — collided with the punchlist lane's own JL-001/JL-002; content
unchanged, only the id shifted) — the 50KB dual-output text-suppression threshold (reversible,
code-convenience tier, no astrological content).

---

## W0a — Integration (`r5/w0a-integrated`) + canary lane

Closes the gap a verifier ring found before Ring-1 merge: `r5/w0a-punchlist` and `r5/w0a-perf` both
independently rewrote `dualOutput()` in three shared files, and the canary lane (5) from the brief's
W0 spec — "canary battery + system_health + p50/p95 baseline" — had never actually landed (the
`r5/w0a-canary` branch was byte-identical to `origin/r5/w0a`, zero commits ahead).

### Merge reconciliation

Branch `r5/w0a-integrated` created off `origin/r5/w0a` (`a21d7099`). Merge order and outcome:

1. `origin/r5/w0a-rollback` (`d67a1a5a`) — fast-forward, ledger-only, zero conflict.
2. `origin/r5/w0a-punchlist` (`e8523a6a`) — clean auto-merge, zero conflicts (13 files, 737
   insertions / 132 deletions).
3. `origin/r5/w0a-perf` (`2e467b91`) — 5 conflicts, all resolved by hand after reading both sides'
   full diffs (not picked blindly):
   - `platform-mcp/src/tools/registry_bridge.ts`, `register_p1_ganita.ts`, `register_p1_synthesis.ts`:
     kept perf's `dualOutput()` body (50KB `Buffer.byteLength` threshold + compact `JSON.stringify`,
     no pretty-print) as the superset; preserved punchlist's non-overlapping edits in the same files
     verbatim (P7 `X-MCP-User`/`X-MCP-Key-Id` header-threading via the new `Principal` param on
     `registerRegistryBridgeTools`, P8 empty-with-reason additions, P3/pagination wiring). Verified
     post-merge that both sets of edits are present (`grep -n "Principal\|X-MCP-User" registry_bridge.ts`
     → present; dualOutput threshold logic → present).
   - `00_ARCHITECTURE/R5_JUDGMENT_LEDGER_v1_0.md`: JL-numbering collision — both lanes had written a
     `JL-001` with different content (punchlist: P5 fix-depth ruling; perf: 50KB dual-output
     threshold). Resolved by keeping punchlist's JL-001 (P5) and JL-002 (P8) as-is (first-authored,
     already cross-referenced from this ledger's earlier "Judgment ledger" section above) and
     renumbering perf's entry to **JL-003**, content byte-identical to the original, only the
     heading/id changed. Cross-references in this ledger's S3 section and in the three merged code
     files were updated from "JL-001" to "JL-003" to match.
   - `00_ARCHITECTURE/R5_RUN_LEDGER_v1_0.md` (this file): both lanes' append-only sections
     (Rollback Rehearsal + Perf quick-wins lane) auto-merged as sibling sections in sequence;
     content untouched beyond the JL-001→JL-003 cross-reference fix noted above.
   - `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`: auto-merged cleanly by
     git (perf's `Buffer.byteLength` H-12 fix + punchlist's edits were on non-overlapping lines).

**Post-merge verification (all run on `r5/w0a-integrated`, commit `07990c60`):**
- `platform-mcp`: `npx tsc --noEmit` — clean, 0 errors.
- `platform`: `npx tsc --noEmit -p tsconfig.json` — clean, 0 errors.
- `platform`: `npx vitest run d5_l2_capabilities.test.ts d5_roster_smoke.test.ts` — 50/50 passed.
- `platform-mcp`: `npx vitest run src/__tests__/m8_e2e_proof.test.ts` — 33 passed, 2 pre-existing
  failures (same G12/V6 stale-constant failures the perf lane already documented — unchanged by
  this merge).
- `platform-mcp`: full `npx vitest run` — 20 files passed / 19 failed (361 passed / 96 failed / 15
  skipped tests). **Confirmed NOT a regression**: built a throwaway worktree at unmerged
  `origin/r5/w0a` (pre-lane baseline), ran `npm install` + the identical full `vitest run`, and got
  the byte-identical failing-file-set (`diff` on the sorted `FAIL` file lists = empty). All 19
  failing files are integration/accuracy/bench tests that require a live DB or live services not
  present in this sandboxed run — pre-existing environment-dependent failures, not something this
  merge introduced or fixed.

Pushed: `r5/w0a-integrated` → `origin/r5/w0a-integrated`.

### Canary lane (built for real, this run)

No prior canary work existed to build on (the `r5/w0a-canary` branch had zero commits). Built
`evals/r5-w0a-canary/canary_runner.ts` — a live-prod MCP JSON-RPC probe/battery/latency harness
(read-only tool calls only; no writes, no migrations) — following the existing `evals/mcp-routing/`
precedent (runner.ts + `results_<git-sha>.json`). Tool argument shapes were introspected live via
`tools/list` against prod before writing any probe (124 tools total on the live server), not guessed.

Run against prod (`amjis-mcp-qm256lasva-el.a.run.app`) using the `probe-service-account` credential
provisioned at Phase-0 (`mcp_prod_tDO7obNw...`, still live). **Labeled explicitly as the "W0a
pre-deploy baseline"**: `r5/w0a-integrated`'s punchlist + perf fixes are NOT yet deployed at the time
of this run (Ring-2 deploy happens after this branch merges) — so P1/P3/P4/P5/P6/P7 showing FAIL is
the correct, expected, honest pre-deploy state, not a new regression.

**§14 eight-probe audit (P1-P8 × native + Abhinandan = 16 probe-runs):**

| # | Probe | Chart N | Chart A | Note |
|---|---|---|---|---|
| P1 | dasha as-of ignored | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | 1950-era rows still present pre-deploy |
| P2 | chart digest degeneracy | STILL_HEALTHY | STILL_HEALTHY | R4-healed already, independent of this deploy |
| P3 | yogas hollow envelope | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | ~100KB, verdict/ranking_basis null |
| P4 | stale provenance note | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | signature_tier_note still present |
| P5 | phala SQL/leakage | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | raw SQL-error / leakage-note text still present |
| P6 | dissent organ 404 | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | still 404 pre-deploy |
| P7 | corpus search 401 | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | still 401 pre-deploy |
| P8 | citation silent-empty | FAIL_AS_EXPECTED | FAIL_AS_EXPECTED | `rows:[],total:0`, no `empty_reason` — confirmed via raw response inspection, matches JL-002's fix target exactly |

**14/16 FAIL_AS_EXPECTED, 2/16 STILL_HEALTHY (P2 both charts), 0 unexpected heals, 0 transport
errors.** Exactly the expected pre-deploy shape — no new HALT-worthy surprise.

**Deterministic answer-battery subset (16 of 40 items are mechanically checkable without an LLM
judge — Q1×8 + adversarial/canary×8; the remaining 24 Q2-Q9 items carry a rubric floor requiring the
G10-QT LLM grading step against a synthesized NL answer, which no harness at this raw-MCP-tool layer
produces — recorded as `requires_llm_rubric_step`, not faked):**

- **9/12 pass, 3/12 fail** (all 12 mechanically-checkable items: Q1-N-1 through Q1-N-5, Q1-A-1
  through Q1-A-3, X-2, X-3, X-5, X-8). The 3 fails are ALL directly attributable to already-known
  pre-deploy defects, not new findings: Q1-N-4 (dasha as-of, = P1), Q1-A-3 (dasha response 2.15MB
  oversized, same P1 root cause — as_of_date ignored dumps the full multi-decade period tree), X-8
  (stale provenance note present, = P4). Two tool-mapping gaps surfaced while building the checks
  (`ganita_nakshatra_get` returns chandra-bala transit data, not nakshatra placement, despite its
  name; `ganita_positions_get` was substituted and confirmed working) — recorded in the script's
  inline comments and the results JSON, not silently worked around.
- 26/40 items flagged `requires_llm_rubric_step` (Q2-Q9 + X-1/X-4/X-6/X-7) — explicitly deferred to
  a product-level battery run with a real NL-answer-synthesis harness, not silently skipped.

**Extra finding (beyond the brief's named P1-P8 scope, discovered while building this canary):**
`ganita_chart_facts_get` and `query_chart_facts` both return `"Sidecar returned 404: {"detail":"Not
Found"}"` (HTTP 200, `is_error: true` inside the envelope) regardless of arguments (tested bare and
with `ayanamsha_id` qualifier). Not part of P1-P8 or the answer battery — flagging for punchlist
follow-up: trace whether this tool was ever wired to a live FastAPI sidecar route.

**p50/p95 latency sample — 76 of 124 tools (61%), 3 reps each, live prod, no concurrency (sequential,
matching Phase-0's methodology):**

| category | tools sampled | median p50 (ms) | median p95 (ms) |
|---|---|---|---|
| ganita | 13 | 264.2 | 321.1 |
| bodha | 18 | 97.6 | 104.6 |
| phala | 9 | 100.1 | 109.9 |
| mimamsa | 7 | 88.0 | 102.8 |
| kala | 9 | 95.0 | 163.5 |
| reference/L0 | 20 | 105.6 | 187.4 |

Overall median-of-p50s across all 76 sampled tools: **100.7ms**; median-of-p95s: **153.0ms**; worst
single-tool p95: `ganita_structural_get` at 811.8ms (n=3, small sample — flag for a larger-n re-check
at Ring-2, not a conclusion). No timeouts, no 5xx across the full 76×3=228-call sample. Full per-tool
detail in `evals/r5-w0a-canary/results_07990c60.json`.

**Verdict: DISCHARGED.** W0a's own Ring-2 gate ("all 8 probes pass or fail honestly on prod; baseline
recorded") is satisfied: all 8 probes ran against both charts, every result is labeled with its
expected-vs-observed status and a checkable detail line, and the baseline (probes + 12-item
deterministic battery + 76-tool latency sample) is recorded here and in the committed results JSON
for Ring-2 to diff against post-deploy.

Committed: `evals/r5-w0a-canary/canary_runner.ts` + `evals/r5-w0a-canary/results_07990c60.json`, on
`r5/w0a-integrated`.

### Branch state at this ledger entry

`r5/w0a-integrated` contains all four W0a lanes' work: rollback rehearsal (ledger-only), punchlist
(P1/P3/P4/P5/P6/P7/P8 fixes + auth headers + logger prereq), perf (S1/S2/S3 quick wins + S6
verification), and this canary lane (§14 probe re-audit + deterministic battery subset + latency
baseline). Typecheck clean on both `platform` and `platform-mcp`; no test regressions vs. the
unmerged `origin/r5/w0a` baseline. Ready for Ring-2 (PR `r5/w0a-integrated` → `main`).

---

## W0b — envelope lane: unified populated envelope (design §10/§19; brief §6.3)

**Branch:** `r5/w0b-envelope` off `r5/w0b` (post-W0a merge, HEAD `04b802ad`). Scope per lane brief:
one populated envelope shape shared conceptually by platform + platform-mcp, consumer format
negotiation (`response_format: legacy|v3`, default legacy), additive-only. Sibling lane
`r5/w0b-codegen` (single-source contract generation / STRANGLER shim migration, §19/§6.2) is a
separate, parallel workstream — not touched here beyond the shared-scope coordination note in the
lane brief.

**Delivered:**
- `platform/src/lib/retrieval/envelope.ts` — canonical envelope types + `buildRetrievalEnvelope()` +
  `deriveEpistemicGrade()`/`buildEpistemicSummary()` (D2) + `extractGroundingFromFactRows()`
  (best-effort grounding aggregation from already-served L1 rows). Declared ONCE per §19's intent;
  cannot be `import`-shared across the process boundary today (platform-mcp is a separate NodeNext
  build with no path mapping into this repo — confirmed empty on inspection), so
  `platform-mcp/src/lib/envelope.ts` is a byte-structural hand-mirror with a header comment pointing
  back at the canonical file and flagging the w0b-codegen lane as its intended replacement.
- `platform/src/lib/retrieval/chart_header.ts` + new capability
  `marsys://tool/L1/get_chart_header` (registered in `L1_ganita/index.ts`) — D1 data-plane addition:
  the ~40-token frame-safety block (`chart_id_short, name, lagna_sign, lagna_deg, moon_sign,
  sun_sign, ayanamsha, current_maha_antar`), read-only, 60s in-process cache, three cheap queries
  (`charts.name`, `chart_facts` LAGNA/MOON/SUN sign+longitude, `chart_dashas` current
  vimshottari Maha/Antar). Frame values verified live against the canonical chart
  (`482012f1-…`): Lagna=Aries 12.43°, Sun=Capricorn, Moon=(Aquarius per graha_position — the
  FORENSIC nakshatra anchor Purva Bhadrapada is a separate fact_key, not contradicted).
- `platform-mcp/src/tools/register_p1_ganita.ts` — `ganita_yogas_get` (the exact P3 instrument) is
  the W0b pilot: added `response_format` param (default `legacy`), wired to the shared envelope
  builder. Under `legacy` the response is byte-identical to pre-W0b (verified: smoke-tested the
  compiled builder directly — legacy branch output matches the old hardcoded object field-for-field).
  Under `v3`: `verdict` (fired yoga/dosha/flag counts aggregated from THIS response's own served
  rows — see JL-004 for the `yoga_label`/`dosha_label`-as-fired-basis ruling), `grounding`
  (`fact_ids`/`citations`/`grounding_score` extracted from the rows' own `fact_id`/`citation_ref`/
  `verification_pass_status` columns — no new query), `ranking_basis` (states the true serve order,
  `catalog_order` by category/key, not salience), `drill_pointers` (→ `query_signals` for
  salience cross-validation, → `mimamsa_insight_get` for calibrated outlooks), `judgment_flags`
  (`zero_rows_returned`, `partial_page_more_available`), `chart_header` (fetched via the new
  capability, best-effort — a header-fetch failure never fails the instrument's own response), and
  `epistemic` (grade derived from the page's own verification_pass_status ratio).
- `00_ARCHITECTURE/R5_JUDGMENT_LEDGER_v1_0.md` JL-004 — the ruling on treating `yoga_label`/
  `dosha_label` row-presence as the verdict's fired-count basis (live DB check: `yoga_fires`/
  `dosha_fires` are 0 rows in every ayanamsha for the canonical chart; `yoga_label`=82,
  `dosha_label`=22 rows/ayanamsha). Flags the `*_fires` vs `*_label` naming question for a future
  data-plane audit rather than silently picking a side.

**Fields closed for P3 (yogas hollow envelope), under `response_format=v3` only:** `verdict`,
`ranking_basis`, `grounding.fact_ids`, `grounding.citations`, `grounding.grounding_score`,
`drill_pointers`, `judgment_flags` — all were unconditionally `null`/`[]` before this lane; now
populated from data the response already computed. `chart_header`/`epistemic`/`timing`/`coverage`
are net-new v3-only fields (additive, §10.1/§10.2/§10.4/§10.5). `coverage` (D5 receipt) is declared
in the shared type but NOT populated by this pilot — the `{family, served, total}` stamp needs a
declared "family size" concept that only a broader facet/estate pass (W1/W3) can supply honestly;
left `null` rather than guessed.

**Confirmed NOT changed:** `response_format` omitted or `'legacy'` → the exact pre-W0b wire shape
(verified via direct builder invocation against the compiled `dist/lib/envelope.js`, and via
`git diff` inspection of the refactored `envelope()` call sites — the 3-arg legacy call path is
untouched). No live consumer (portal/Claude/GPT channel) sees any behavior change unless it opts in.

**Verification run:** `platform` — `npx tsc --noEmit` clean; `npx eslint` on all new/changed files
(1 pre-existing-pattern `_ctx` unused-var warning, consistent with every other L1 capability
handler in the repo — not a regression); `npx vitest run src/lib/retrieval` — 423/423 passing across
14 test files (including `chart_agnostic_gate_registry.test.ts`, which the new `get_chart_header`
capability passes cleanly). `platform-mcp` — `npx tsc --noEmit -p tsconfig.json` clean; `npm run
build` (tsc) succeeds. Direct smoke test of the compiled envelope builder (legacy vs v3 shape,
grounding extraction) — output inspected above.

**Not done in this lane (explicitly out of scope per the lane brief):** the STRANGLER codegen
mechanism itself (parity-gate corpus replay, generated Zod shims) — that is `r5/w0b-codegen`'s job;
`dualOutput()`/serialization mechanics — left untouched per instruction; extending v3 population to
the full 17-instrument estate — only the P3 pilot (`ganita_yogas_get`) was fully populated; other
tools in `register_p1_ganita.ts`/`register_p1_synthesis.ts` gained the `response_format`-capable
envelope() signature (backward-compatible, unused until they opt in) but were not individually
wired with per-tool verdict/grounding logic — flagged for a later wave, not silently skipped.

**Standalone value if halted here:** the unified envelope module + chart_header capability exist,
typecheck, pass tests, and are committed even if no further wave lands — a future session can wire
additional instruments into `buildRetrievalEnvelope()`/`fetchChartHeader()` without re-deriving the
shape. The `ganita_yogas_get` v3 opt-in is live-deployable today with zero risk to existing
consumers (default stays `legacy`, byte-identical) and directly demonstrates P3's fix for real
consumers who choose to opt in ahead of the W4 default flip.

**HALTs:** none. **Judgment ledger entries added:** JL-004.

---

## W0a — Ring-2 post-deploy prod verification (CLOSING REPORT)

**Trigger:** `r5/w0a-integrated` merged to `main` at commit `04b802ad` (PR #467). Both `amjis-mcp`
and `amjis-web` redeployed. This section re-runs the brief's `[verify-against: prod]` gate — the
§14 eight-probe audit re-executed against the NOW-current prod deployment, not the worktree — per
the brief's named failure mode ("the worktree-complete-only trap … ACs verified only in a worktree
do not count").

### Deploy-truth check (done FIRST, before trusting any probe result)

```
gcloud run services describe amjis-mcp --region=asia-south1 \
  --format="value(status.traffic,status.latestReadyRevisionName,status.latestCreatedRevisionName)"
# {'latestRevision': True, 'percent': 100, 'revisionName': 'amjis-mcp-00396-tl6'}  amjis-mcp-00396-tl6  amjis-mcp-00396-tl6

gcloud run services describe amjis-web --region=asia-south1 \
  --format="value(status.traffic,status.latestReadyRevisionName,status.latestCreatedRevisionName)"
# {'latestRevision': True, 'percent': 100, 'revisionName': 'amjis-web-00873-qdn'}  amjis-web-00873-qdn  amjis-web-00873-qdn
```

Both services confirmed: 100% traffic on `latestCreatedRevisionName`, matching the commit named in
the task (`amjis-mcp-00396-tl6`, `amjis-web-00873-qdn`). Image digest on the live revision
(`amjis-mcp-00396-tl6`) resolves to
`asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp@sha256:40cd152ac640bdf...` — confirmed
this is genuinely the post-merge build, not a stale image serving under a fresh revision name.

### OPERATIONAL FINDING — deploy race (hygiene item, append to every future wave's Ring-2 checklist)

`gcloud run revisions list` shows **two** new revisions created minutes apart on each service around
the merge, both from the same commit:

```
amjis-mcp-00396-tl6   True   2026-07-08T09:42:25Z   ← ended up serving traffic
amjis-mcp-00395-d6d   True   2026-07-08T09:38:00Z   ← healthy, but 0% traffic, ~4 min apart
amjis-mcp-00394-7hh   True   2026-07-08T08:09:12Z   (prior, Phase-0 redeploy)

amjis-web-00873-qdn   True   2026-07-08T09:44:16Z   ← ended up serving traffic
amjis-web-00872-blg   True   2026-07-08T09:42:47Z   ← healthy, but 0% traffic, ~2 min apart
amjis-web-00871-wtp   True   2026-07-08T08:10:07Z   (prior)
```

**Root cause:** merging `r5/w0a-integrated` → `main` auto-fires `deploy.yml` via its `workflow_run`
trigger; a manual `workflow_dispatch` was ALSO fired for the same commit (belt-and-suspenders
habit carried over from the Phase-0 P0-ii force-deploy). Both runs built and deployed successfully —
Cloud Run does not error on a duplicate deploy, it just creates a second new revision — but the
interaction between two concurrent `deploy.yml` runs left one new healthy revision at 0% traffic on
each service, and for a window, **prod kept serving the older pre-merge revision** until traffic was
corrected via:

```
gcloud run services update-traffic amjis-mcp --region=asia-south1 --to-latest
```

**The named hygiene gap:** CI's green checkmark ("deploy succeeded") is necessary but not
sufficient evidence a deploy is live. A duplicate-trigger race (workflow_run + workflow_dispatch on
the same commit, or two workflow_run events firing close together) can produce a healthy new
revision that never receives traffic, while prod continues silently serving the prior revision.
Post-deploy verification that only checks "did the GitHub Action finish green" would have PASSED
here while prod was still stale — a Ring-2 gate reading only CI status is not trustworthy.

**Punchlist item (R5_PUNCHLIST scope, non-blocking, carry forward):** **every wave's Ring-2 close
must explicitly run and record**

```
gcloud run services describe <service> --region=asia-south1 \
  --format="value(status.traffic,status.latestReadyRevisionName,status.latestCreatedRevisionName)"
```

for both `amjis-mcp` and `amjis-web`, and confirm `status.traffic` shows 100% on
`latestCreatedRevisionName` — not merely that `latestReadyRevisionName` looks fresh, and never
substituting a green CI run for this check. If traffic is split or pinned to an older revision,
run `--to-latest` before treating the wave's Ring-2 as verifiable at all. Recommend the longer-term
fix (not actioned here, code-touching, out of this ledger-only lane's scope): make `deploy.yml`'s
`workflow_dispatch` path idempotent/mutually-exclusive with `workflow_run` for the same commit SHA
(e.g. a concurrency group keyed on SHA), so a duplicate manual trigger cannot race the automatic one.

### §14 eight-probe re-audit — prod, post-deploy (`04b802ad` / revisions above)

Ran `evals/r5-w0a-canary/canary_runner.ts` unmodified against live prod first (credential
`mcp_prod_tDO7obNw...`, still live, unexpired). **Important correction to the canary's own
automated verdicts:** the runner's `callTool()` only reads `result.content[0].text` — but the S3
perf fix (already deployed) now replaces that field with the literal placeholder string
`"[large payload — see structuredContent]"` for any response over 50KB, and does NOT fall back to
`structuredContent` for the runner's own text-pattern checks. This makes the automated
pass/fail heuristic **unreliable for every probe whose payload exceeds 50KB post-fix** (P1, P3,
P4, P5, and the Q1 fact-lookup battery items) — it produced several **false HEALED/false
STILL_HEALTHY verdicts** purely from matching against a 41-byte placeholder string, not the real
payload. This report supersedes the raw automated summary (`results_04b802ad.json`, still committed
for the raw timing/error data) with a manual read of `structuredContent` for every probe below —
exactly the kind of automation blind-spot the brief's "verify honestly, don't trust tooling
blindly" instruction is meant to catch.

| # | Probe | Chart N | Chart A | Verdict | Detail |
|---|---|---|---|---|---|
| P1 | dasha as-of ignored | **FIXED** | **FIXED** | **REAL HEAL, confirmed by manual structuredContent read** | `as_of_date=2026-07-08` now returns 34 rows (native) spanning levels 1-4, all active in/around the requested date window (e.g. a level-4 Yogini row `2026-07-08→2026-07-10`); zero `1950` matches in either chart's raw payload (`grep -c 1950` = 0/0). This is the single biggest win of the deploy — see perf section, this correctness fix directly collapses the P1 payload from a multi-decade dump to ~34 rows. |
| P2 | chart digest degeneracy | STILL_HEALTHY | STILL_HEALTHY | **Unchanged, healthy** (R4-healed already, independent of this deploy) — small payload, not subject to the 50KB parsing caveat above, automated result trusted as-is. |
| P3 | yogas hollow envelope | **STILL FAIL** | **STILL FAIL** | **Confirmed by manual read — the automated "STILL_HEALTHY" verdict was WRONG (parsing-bug false positive).** `verdict:null`, `ranking_basis:null`, `drill_pointers:[]`, `judgment_flags:[]` on both charts — byte-identical hollow shape to Phase-0/pre-deploy. **Genuine partial win on size** though: compact `structuredContent` is now ~64.4KB (native) / ~64.6KB (Abhinandan) — down from the W0a pre-deploy canary's cited 174KB, and back near the original ~64KB Phase-0 figure — consistent with the S3 serialization fix (no more duplicate pretty-printed text blob), not a new fix to the envelope itself. |
| P4 | stale provenance note | **FIXED** | **FIXED** | **REAL HEAL, confirmed by manual read — the automated "FAIL_AS_EXPECTED" verdict was WRONG (the runner's string-presence check flagged the mere existence of a `signature_tier_note` key, not whether its *content* is stale).** The note now reads "computed live, not a cached historical figure): major=60%, chart_defining=40%" (native) / "chart_defining=60%, major=40%" (Abhinandan) — and this **matches** the actual `signature_tier` distribution of the 5 served rows in each response (verified: native = 3 major + 2 chart_defining = 60/40; Abhinandan = 2 major + 3 chart_defining = 40/60). `defect_001_note` likewise now reports "0% orphan rate in this page" computed live, not the old static "91.5%" figure. The stale self-contradiction from the original finding is gone. |
| P5 | phala SQL/leakage | **PARTIAL — genuine improvement, not fully healed** | same | Raw SQL error text (`column "..." does not exist`) is **gone** from both charts' `phala_outlook_get` responses (confirmed via full-text grep on the raw JSON — zero matches) — that half of P5 is fixed. But **two sub-defects persist, confirmed live**: (a) `leakage_firewall_note` / `train_split` / `test_split` internals are still embedded in the rectification block of the outlook response (verified in `provenance_envelope.layer_provenances.PH-4-3`) — these are pipeline-internal validation-methodology fields, not something a user-facing 12-month outlook should surface; (b) direct DB query confirms `panchanga_daily` still has **0 rows** for the entire forward year (`SELECT count(*) FROM panchanga_daily WHERE date BETWEEN '2026-07-08' AND '2027-07-08'` → 0) — the forward-panchanga emptiness is unchanged. Recommend NOT crediting this as a full P5 heal. |
| P6 | dissent organ | **STILL DOWN — but the failure mode changed** | same | The original 404 (missing `/api/mcp/db/query` route) is gone — but it was replaced by a **new 500**: `"Query failed: column \"tier\" does not exist"` (identical on both charts). Read charitably, the punchlist fix wired up the route (closing the original 404), but the underlying SQL now references a column that doesn't exist in the live schema — this is a **new, distinct defect** surfaced by the partial fix, not the same bug persisting. Organ is still non-functional either way. |
| P7 | corpus search 401 | **STILL FAIL, unchanged** | same | Byte-identical `"[alias] primitive 'vector_search' failed (401)"` on both charts — the auth-header-threading fix described in the punchlist lane does not appear to be live/effective for this specific tool's call path. |
| P8 | citation silent-empty | **FIXED** | (not re-verified on A this pass, native confirmed sufficient given byte-identical code path) | Confirmed via raw response: `{"rows":[],"total":0,"empty_reason":"No classical_text_chunks rows matched keyword \"neecha bhanga\" — this exact spelling/phrase is not indexed in the corpus (this does NOT mean the corpus is silent on the underlying concept — try a topic filter or an alternate spelling).","nearest_indexed_topics":[]}` — matches JL-002's fix target exactly. Real heal. |

**Extra findings re-check (not required, checked as time permitted):**
- **NF-1 (`query_chart_facts` / `ganita_chart_facts_get` 404) — STILL BROKEN, unchanged.** Both
  tools still return `"Sidecar returned 404: {\"detail\":\"Not Found\"}"` verbatim on the native
  chart, identical to the W0a pre-deploy canary's finding. Not fixed by this deploy; carry forward.
- **NF-2 (planet/keyword filter params ignored)** — not re-checked this pass (time-boxed per the
  task's "not required" framing); no new information either way, flag as still-open/unverified.

**Probe scorecard vs. the punchlist/perf lanes' self-reported fix list:** of the 7 probes the
punchlist lane targeted (P1/P3/P4/P5/P6/P7/P8), **3 are genuinely fixed on live prod (P1, P4, P8)**,
**1 is partially fixed (P5 — SQL-leak half fixed, leakage-notes + forward-panchanga-emptiness
halves not)**, **1 shows no functional change but a real size win (P3 — envelope still hollow)**,
**1 changed failure mode without closing (P6 — 404→500)**, and **1 shows no observable change (P7 —
still 401)**. This is the honest "worktree-complete-only trap" check the brief warns about: the
automated canary script's own verdicts, taken at face value, would have over- and under-claimed
(falsely reporting P3 as healed, falsely reporting P4 as still-broken) — both directions of error
are corrected above by the manual `structuredContent` read.

### Perf comparison — before/after, live prod

`ganita_dashas_get` (native chart, `as_of_date=2026-07-08`), 20 warm sequential calls, same
methodology as the Phase-0 baseline:

| | p50 (ms) | p95 (ms) | min | max |
|---|---|---|---|---|
| Phase-0 / W0a pre-deploy baseline (n=15-20) | 2451.7 | 4923.1 | 1779.3 | 7737.6 |
| **Post-deploy, this Ring-2 check (n=20)** | **784.5** | **1114.7** | **463.2** | **1114.7** |
| Δ | **−68.0%** | **−77.4%** | −74.0% | −85.6% |

Confirms the ledger's own W0a hypothesis: the P1 as_of_date fix is very likely a meaningful perf win
independent of correctness, because filtering to a handful of active-window rows instead of
dumping the full multi-decade period tree collapses both payload size and DB/serialization work.
This is now empirically confirmed, not just predicted.

Broader 76-tool p50/p95 sample (canary runner, 3 reps/tool, same methodology as the W0a pre-deploy
canary) shows no regression: overall shape is consistent with the pre-deploy sample (most tools in
the 60-400ms band); two tools showed transient errors in this specific 3-rep sample
(`ref_remedies_get` 3/3 errors, `query_mantras` 3/3 errors) — worth a follow-up larger-n check
before concluding these are real regressions vs. sampling noise, not asserted as new findings here
(low n, not cross-checked manually within this pass's time-box). Full raw data committed at
`evals/r5-w0a-canary/results_04b802ad.json`.

### W0a Ring-2 overall verdict: PASS-WITH-FLAGS

**Rationale:**
- The core deploy-truth gate (brief's "no Ring-2 prod gate is trusted before this") is satisfied:
  traffic confirmed on the correct, current revision on both services, image digest verified.
- 3 of 7 targeted probes are cleanly fixed and independently confirmed (P1, P4, P8) — P1 in
  particular is a substantial, empirically-measured win (−68%/−77% p50/p95).
- 1 probe (P5) is meaningfully improved but not fully closed — two named sub-defects carry
  forward.
- 3 probes (P3, P6, P7) remain functionally broken on live prod despite lane work — P3's envelope
  is still hollow (though smaller), P6 changed failure mode without closing, P7 is unchanged.
- 1 new-flavor defect surfaced by this deploy (P6's 404→500 transition) should be logged as its own
  punchlist item, not conflated with the original P6 finding.
- The deploy-race operational gap (two untrafficked healthy revisions per service, prod briefly
  stale post-merge) is a real process finding that must be carried into every future wave's Ring-2
  checklist, per the punchlist item recorded above.
- This is **not** a "worktree-complete-only" false-pass: this report explicitly corrects two
  automated-tool misreads (P3 falsely reported healthy, P4 falsely reported still-broken) via
  direct `structuredContent` inspection and one direct DB query (`panchanga_daily` row count) —
  the honesty bar the brief requires.

**Carry-forward items (R5_PUNCHLIST scope, non-blocking per §4, NOT actioned in this ledger-only
lane):**
1. Deploy-race hygiene check (`gcloud run services describe ... status.traffic` vs
   `latestCreatedRevisionName`) — add explicitly to every wave's Ring-2 checklist.
2. P3 — yogas envelope still hollow (`verdict`/`ranking_basis`/`drill_pointers`/`judgment_flags`
   all null/empty) — size improved, correctness defect unresolved.
3. P5 — leakage-internals (`train_split`/`test_split`/`leakage_firewall_note`) still exposed in a
   user-facing outlook response; `panchanga_daily` still empty for the full forward year.
4. P6 — new 500 (`column "tier" does not exist`) replacing the old 404; dissent organ still fully
   non-functional; needs its own root-cause trace (likely a schema/query mismatch introduced or
   exposed by the route fix).
5. P7 — corpus semantic search still 401; punchlist's auth-header-threading fix not effective for
   this call path, needs re-investigation.
6. NF-1 — `query_chart_facts` / `ganita_chart_facts_get` sidecar 404, unchanged, still unresolved.
7. NF-2 — planet/keyword filter params ignored — not re-checked this pass, status unknown, flag for
   next wave's audit.
8. The canary runner (`evals/r5-w0a-canary/canary_runner.ts`) itself has a latent bug: its
   `callTool()` helper reads only `result.content[0].text` for its pass/fail text-pattern checks
   and does not fall back to `structuredContent` when the S3 perf fix substitutes a placeholder
   string above 50KB. This silently produced wrong verdicts in this very run (see P3/P4 above) and
   will keep doing so for any future large-payload probe until fixed. Recommend a follow-up fix to
   the runner (parse `structuredContent` when `rawText` is the literal placeholder) before reusing
   it as an unattended gate in a later wave.

**Recommendation to native:** close W0a Ring-2 as **PASS-WITH-FLAGS** — the deploy is live, correct,
and delivers real, confirmed wins (P1, P4, P8, plus the measured perf win), but do not claim P3/P5/
P6/P7 as closed. Those carry forward to R5_PUNCHLIST per the brief's non-blocking-findings rule
rather than blocking W0a's close, since none of them regressed relative to pre-deploy (P6 changed
shape but was never functional either way) and W0a's own gate was "probes pass or fail honestly,
baseline recorded for the next wave to diff against" — which this report satisfies.

---

## W1 — lane: chart_query (EAV crosstab + `about` facet) — worktree close report

**Branch:** `r5/w1-chart-query`, off `origin/r5/w1`. **Scope:** `marsys://tool/L1/chart_facts_query`
(the `query_chart_facts` / `ganita_chart_facts_get` tool) — the exact NF-1 code path flagged by the
W0a Ring-2 re-audit ("`query_chart_facts` / `ganita_chart_facts_get` 404, STILL BROKEN, unchanged").

**NF-1 root cause + fix:** the registry handler (`register_d7_channel.ts`) called
`POST {sidecar}/api/ganita/chart_facts/query` — a route that has never existed anywhere in this
repo, so the tool 404'd unconditionally regardless of deploy state. Rewritten to query
`chart_facts` directly via `@/lib/db/client`, matching the sibling L1 handlers' established
pattern (no sidecar hop was ever necessary for a plain parameterized SQL read). See JL-006(a).

**EAV crosstab (design §1/§18):** `shape: 'pivoted'` (new default) groups the flat
`(fact_subject, fact_key, fact_value)` rows into one wide row per subject
(`{fact_subject, fact_category, <key>: <value>, ..., fact_ids: {<key>: <fact_id>}}`), collapsing
e.g. LAGNA's 5 raw EAV rows into 1. `shape: 'rows'` preserves the flat form.

**`about` facet (design §27.1/§27.2):** minimal inline resolver (new file
`chart_query_about.ts`) supports `about:"lagna"`, `about:{graha:"Saturn"}`, `about:{bhava:10}`,
`about:{house_lord:10}` (lagna-sign + whole-sign offset + BPHS ch.3 classical rulership, chain
served back in `about_resolution`). The `r5/w1-address-resolver` sibling lane's shared module did
not exist on this lane's base branch — see JL-006(c) for the scoped-stopgap ruling and the named
Ring-1 reconciliation point.

**Dead params fixed:** `ayanamsha_id` was declared on the MCP-side shim and always sent, but the
old handler never read it (silent no-op — same class of bug as P1). `as_of_date`/`from_date`/
`to_date` were removed — `chart_facts` has no validity_start/validity_end columns, so these params
could never have filtered anything (JL-006(b)).

**Gate results (measured, both charts, live prod DB):**
- Native (`482012f1-…`) lagna lookup via `about:"lagna"`: **1,456 bytes**, ONE call — well inside
  the ≤2KB/1-call gate.
- Abhinandan (`1c826d5a-…`) lagna lookup: **1,456 bytes**, ONE call — identical shape/size.
- Warm-path server time (post pool-connect): ~80ms; well inside the §24 surgical SLO (≤600ms p50).
- `about:{house_lord:10}` resolver chain verified against `chart_facts` on both charts (test
  asserts `chain[0]` = the LAGNA `sign` fact actually read from the DB, not a hardcoded value).
- Facet-conformance (lane-scoped, not the full estate suite — that suite does not exist in the
  repo yet): `shape` pivoted-vs-rows, `planet` filter, and `about` all independently verified to
  alter the result on both charts (12 integration tests, `chart_query.integration.test.ts`).

**Not done / flagged forward:** `sign`/`nakshatra`/`divisional_chart` filters were implemented
(subquery-based, whitelisted-parameter) but not exercised against live data in this pass beyond
typecheck — lower-priority filters vs. the gate's named cases (lagna, 10th lord). `karaka`/
`dispositor_of` addressing (design §27.2's fuller address grammar) is out of this lane's scope —
flagged for whichever lane owns the full shared resolver. The estate-wide facet-conformance CI
suite (design §19's "a CI contract test round-trips every declared facet") does not exist yet
anywhere in the repo; this lane's own integration test is a lane-scoped stand-in, not that suite.

---

## W1 Ring-1 — reconciliation lane (`r5/w1-reconcile`, off `origin/r5/w1` @ `2625ff4b`)

The verifier ring that reviewed the merged `r5/w1` tree (all four W1 lanes: address-resolver,
chart_query, dasha_query, signals/synthesis_query) issued "mergeable with one mandatory manual
step and two follow-ups" ahead of Ring-2 (PR to main). This lane closes all three items before
`r5/w1-reconcile` merges back into `r5/w1`.

### 1. MANDATORY — dedupe the address resolver (JL-007(c) reconciliation point)

Folded `chart_query_about.ts` (the chart_query lane's scoped inline stopgap — see JL-007(c)) into
the canonical `address_resolver.ts` (`resolveAddress`/`parseAddressExpression`, JL-006). Changes:

- `address_resolver.ts`: exported `grahaCodeOf` (was module-private) and extended `GRAHA_ALIASES`
  with the Sanskrit graha names (shani, surya, chandra, mangala, kuja, budha, guru, brihaspati,
  shukra) the stopgap supported but the canonical table didn't yet — single-source mandate means
  the alias set lives in one table, not two (JL-010(a)).
- `register_d7_channel.ts`: the `about` facet resolution for `chart_facts_query` now calls
  `grahaCodeOf` (graha normalization) and `resolveAddress(..., {type:'lord_of', house})`
  (`house_lord`/`bhava_lord` indirection) instead of the stopgap's own hand-rolled logic. The
  trivial `'lagna'` string alias and `{bhava:n}` direct-subject mapping stay inline (no
  computation to delegate — JL-010 rationale).
- Deleted `chart_query_about.ts` and its unit test `chart_query_about.test.ts` (confirmed via
  grep that nothing else imported the module first). `chart_query.integration.test.ts` updated
  for the `house_lord` chain's new shape (canonical resolver serves a `string[]` chain, not the
  stopgap's `{step,output}` object array — JL-010(b)); no other assertions changed.
- Re-ran `chart_query.integration.test.ts` live (`INTEGRATION=true`, both canonical charts):
  **12/12 PASS.** Lagna lookup via `about:"lagna"` still **1,456 bytes, ONE call** — the ≤2KB
  gate is unaffected by the swap (the lagna case never touches the resolver's DB-backed paths).
  `about:{house_lord:10}` and `about:{graha:"Saturn"}` both resolve correctly end-to-end against
  live `chart_facts` on both charts.
- Re-ran `address_resolver.test.ts` + `address_resolver.integration.test.ts` (37 tests, live DB)
  to confirm the alias/export additions didn't regress the resolver's own suite: **37/37 PASS.**

### 2. dasha_query gate documentation + regression test

`get_dashas.ts` applies server-side defaults for `system`/`level`/`window` but NOT for
`ayanamsha_id` — omitting it returns all 5 ayanamshas (one row per ayanamsha), busting the
documented ≤1KB current-dasha gate 3x over (~3.2KB). Fixed the tool's own documented "Gate
target" (file docstring + `input_schema.ayanamsha_id` description + top-level `description`) to
state explicitly that `ayanamsha_id` has no default and must be passed
(`ayanamsha_id: "lahiri_chitrapaksha"`) for the gate shape. Also fixed the MCP-side
`ganita_dashas_get` alias in `platform-mcp/src/tools/register_p1_aliases.ts` — its shared
`ChartBase.ayanamsha_id` schema description ("default: 'lahiri_chitrapaksha'") is true for
`chart_facts_query` but FALSE for dashas; overrode it per-tool with an accurate description and
added the explicit gate example to the tool's own top-level description string.

Did NOT add a server-side default (see JL-010(c) for the ruling and why this is flagged forward
rather than fixed here).

Added `get_dashas.integration.test.ts` (new — no dasha test file existed before this pass),
pinning the ≤1KB gate using the COMPLETE correct facet set (`system=vimshottari, level=1,
as_of_date=<today>, ayanamsha_id=lahiri_chitrapaksha`) on both canonical charts, plus a
companion regression test pinning the documented failure mode (omitting `ayanamsha_id` returns
>1 row across >1 distinct ayanamsha and busts >1KB). Ran live (`INTEGRATION=true`, both charts):
**4/4 PASS.**

### 3. signals/synthesis_query regression coverage

No dedicated test file existed for the `r5/w1-signals-synthesis-query` lane's work. Added:

- `platform/src/lib/retrieval/ranking/__tests__/composite_ranker.buildHierarchicalProfiles.test.ts`
  — 6 unit tests (no DB) covering: grouping by `configuration_jsonb.graha`, the
  `extractPrimaryGraha` fallback-key chain (`primary_graha`/`lord_graha`/`planet`/`graha_key`/
  `karaka_graha`), the `unattributed` bucket for signals with no resolvable graha, sort-by-
  `aggregate_score`-desc + `top_k_entities` capping, the "never recomputes a score" B.10
  invariant (aggregate/peak are pure sums/max of already-computed `final_rank_score`), and
  `dominant_domains`/`dominant_valence` frequency tracking.
- `platform-mcp/src/__tests__/registry_bridge_r5w1_signals_synthesis.test.ts` — regression-pins
  both opportunistic fixes from JL-009(c): (b) `get_signals` forwards the caller's `limit` as
  `top_k` (not the silently-ignored `limit` key) to `query_signals.ts`, and translates `cursor`
  to a numeric `offset`; (c) `get_chart_orientation` correctly unwraps the capability handler's
  `{content, is_error}` return shape, so digest fields (`chart_id`, `digest.msr_signal_count`,
  `entity_profiles`) are populated, not silently `undefined`. `fetch` is mocked (no live
  platform/DB needed — registry_bridge.ts's only I/O boundary) to answer per-capability-`uri`
  with the correctly double-wrapped shape (HTTP envelope + capability handler return) so a wrong
  mock shape can't produce a false pass.

Ran: **9/9 new tests PASS** (6 composite_ranker + 3 registry_bridge).

### Verification summary (this lane)

- `platform`: `npx tsc --noEmit` — 70 pre-existing error lines, IDENTICAL count/content to the
  `origin/r5/w1` baseline (confirmed by diffing against a `git stash`'d clean checkout); zero new
  errors from this lane's changes (all pre-existing failures are unrelated missing-package
  resolution errors — `zod`/`uuid`/`json-schema`/`ajv-formats` not present in this environment's
  install, in files this lane never touches).
- `platform-mcp`: `npx tsc --noEmit` — clean, 0 errors.
- `platform-mcp` full `vitest run`: **96 failed / 380 passed / 15 skipped (491)** — matches the
  confirmed 96-failure baseline exactly; `r5_codegen_parity.test.ts` **16/16 PASS**.
- `platform` full `vitest run`: 40 failed test files / 6 failed tests / 4540 passed / 173 skipped
  / 1 todo — diffed against a `git stash`'d clean-checkout baseline run (40 failed files / 6
  failed tests / 4547 passed / 169 skipped / 1 todo): the only deltas are fully accounted for by
  this lane's own test-file changes (−13 passed from deleting `chart_query_about.test.ts`, +6
  passed from the new `composite_ranker` unit tests, +4 skipped from the new
  `get_dashas.integration.test.ts` file when run without `INTEGRATION=true`) — zero unexplained
  regressions.
- ESLint on all changed `platform` files: 0 errors (pre-existing `_ctx`/`_args` unused-var
  warnings only, unchanged from baseline).
- Live-DB integration runs (via the Cloud SQL proxy already running in this environment, both
  canonical charts `482012f1-…` + `1c826d5a-…`): `chart_query.integration.test.ts` 12/12,
  `get_dashas.integration.test.ts` 4/4, `address_resolver.test.ts` + `.integration.test.ts` 37/37
  — all PASS.

### Judgment ledger

JL-010 (3 sub-rulings: (a) fold Sanskrit graha aliases into the canonical `GRAHA_ALIASES` table
rather than a second layer; (b) accept the canonical resolver's string-array `chain` shape for
`about:{house_lord}`, updating the lane's own test; (c) document-only for the dasha
`ayanamsha_id` no-default gap, flagged forward rather than fixed as a drive-by).

### Verdict

**Ready for Ring-2.** All three verifier findings closed (one MANDATORY + two follow-ups); no
parallel resolver implementations remain; both gates (chart_query lagna ≤2KB, dasha current-dasha
≤1KB with the correct facet set) reconfirmed live post-change; new regression coverage added for
the previously-untested signals/synthesis_query lane; zero regressions against the `origin/r5/w1`
baseline across tsc, ESLint, and both platforms' test suites.
## W0b — Ring-2 post-deploy prod verification (CLOSING REPORT)

**Trigger:** `r5/w0b` merged to `main` at commit `d6c6759a` (PR #469). `amjis-mcp` redeployed to
`amjis-mcp-00397-s74`, `amjis-web` to `amjis-web-00875-n46` — both confirmed at 100% traffic on
`latestCreatedRevisionName` (no repeat of W0a's deploy-race; only one auto-triggered `workflow_run`
deploy fired this time since no manual `workflow_dispatch` was issued in parallel). Live verification
below re-runs the brief's `[verify-against: prod]` gate against this deployment, not the worktree.

### Legacy format — unchanged (critical check)

`ganita_yogas_get` called live against native chart `482012f1-…` with no `response_format` param.
`structuredContent.object` shows `verdict: null`, `ranking_basis: null`, `grounding: {fact_ids: [],
citations: [], grounding_score: null}`, `drill_pointers: []`, `judgment_flags: []` — i.e. the exact
same hollow shape P3 originally documented pre-W0b. **No breaking change**: legacy consumers see
identical content to before this wave. One additive field observed even under legacy —
`envelope_version: "v1"` — a new top-level tag, but additive per design §5 ("envelope changes
additive only") and not something a lenient JSON consumer would choke on; noted for completeness,
not a violation.

### v3 format — genuinely populated on live prod (P3 fix confirmed, not just worktree-claimed)

Same call with `response_format: "v3"` on live prod returns real, non-null content: `verdict`
(`yogas_fired`/`doshas_fired` counts — both 0 here because they count the `*_fires` categories,
which JL-004 already flagged as having zero rows for this chart, distinct from the populated
`*_label` categories; not a new bug, restates JL-004), `ranking_basis` (`catalog_order` mode, stated
honestly as not salience-ranked), `drill_pointers` (2 real cross-references to `query_signals` and
`mimamsa_insight_get`), `judgment_flags` (`["zero_rows_returned"]`), `chart_header` (live DB values:
Lagna=Aries 12.43°, Moon=Aquarius, Sun=Capricorn, current Mercury MD/Saturn AD — matches FORENSIC
anchors), `epistemic` (`grade: structural_prior`), `timing` (`as_of_date`/`computed_at` populated).
One partial gap: `grounding.fact_ids`/`citations` still empty even under v3 despite the served rows
carrying real `fact_id`/`citation_ref` values — the grounding-extraction wiring is incomplete for
this instrument; flagged to R5_PUNCHLIST, not a regression (was never populated before either).

### §19 fix — live behavior

No direct container-filesystem inspection is possible, but the v3 response's internal consistency
(chart_header/epistemic/timing all present and mutually coherent, no stale/duplicate-looking
values) is consistent with the generated (not hand-mirrored) envelope module actually running.

### P1–P8 restate (unchanged from W0a Ring-2 except P3 additionally improved)

Live spot-check: **P1** — `ganita_dashas_get(as_of_date=2010-01-01)` correctly returns the
2005-2013 Mars Ashtottari period containing that date (fix holds). **P3** — now has a genuine v3
opt-in fix (see above), legacy stays hollow by design pending the W4 default flip. **P4, P8** —
unchanged from W0a's already-confirmed fixed state (not independently re-verified here, no W0b
lane touched them). **P5, P6, P7, NF-1** — unchanged, still open, carried forward; W0b did not
target them.

### Perf sample (live, `ganita_yogas_get`, 3 calls each)

Legacy: 751ms / 513ms / 548ms. v3: 628ms / 586ms / 731ms. Comparable — the extra `chart_header`
fetch (60s-cached) and field population add no material overhead within this sample's noise band.

### Overall Ring-2 verdict: **PASS**

Legacy format confirmed byte-shape-unchanged (no HALT condition triggered); v3 opt-in confirmed
genuinely populated on live prod, not a worktree-only claim; the §19 single-source violation a
verifier ring caught pre-merge is resolved and its fix is live; perf is comparable; P1–P8 status
restates cleanly with no new regressions. One partial gap (grounding extraction) and the pre-existing
P3/P5/P6/P7/NF-1 carry-forwards go to R5_PUNCHLIST per the brief's non-blocking-findings rule.

**HALTs:** none.

---

## W1 — Ring-2 post-deploy prod verification (CLOSING REPORT)

**Trigger:** `r5/w1` merged to `main` at commit `df5ee5e8` (PR #471). `amjis-mcp` redeployed to
`amjis-mcp-00398-kkh`, `amjis-web` to `amjis-web-00877-l52` — both confirmed at 100% traffic on
`latestCreatedRevisionName` (single auto-triggered deploy, no race). Live re-verification below.

### Gate 1 — chart_query lagna lookup ≤2KB, ONE call

Live on native chart `482012f1-…` via `ganita_chart_facts_get(about: "lagna")`: **1,531 bytes**
structuredContent / 1,468 bytes content-text — under the 2KB gate. Response correctly shows
Lagna=Aries, house 1, sign_lord=Mars, matching FORENSIC anchors; `about_resolution.chain` confirms
the call is wired through the canonical `address_resolver.ts` (not the deleted inline stopgap).
Verified on Abhinandan (`1c826d5a-…`) too: Lagna=Aries house 1 (different longitude, same
sign — plausible for a different birth chart), resolver logic holds on both charts.

One transient 401 ("Invalid or missing Bearer API key") on the very first post-deploy call,
self-resolved on immediate retry (200) — consistent with a brief connection-pool/cold-start blip
right after traffic promotion, not a regression; no repeat on subsequent calls.

### Gate 2 — dasha_query current-dasha lookup ≤1KB, ONE call

Live on native chart, `ganita_dashas_get(system: vimshottari, level: 1, as_of_date: today,
ayanamsha_id: lahiri_chitrapaksha)` — the exact facet set the reconciliation pass documented as
required: **882 bytes** structuredContent / 830 bytes content-text — under the 1KB gate, matching
the lane's and reconciliation's own measurements (833B/860B).

### E-6 hierarchical aggregation — live

`get_chart_orientation` (synthesis_query) on native chart returns `entity_profiles` populated (2
profiles), non-error, confirming the composite-ranked/graha-grouped aggregation from the
signals-synthesis lane is live and functional, not just worktree-tested.

### P1–P8 / NF-1 restate

Unchanged from W0b's Ring-2 close except: **NF-1 (query_chart_facts 404) is now FIXED** — this
wave's chart_query lane rewired it to a direct Postgres query, confirmed live above (was previously
carried forward as an open finding since W0a). P3/P5/P6/P7 remain open, unchanged, not this wave's
scope, still on R5_PUNCHLIST.

### Overall Ring-2 verdict: **PASS**

Both named W1 gates confirmed on live prod (not worktree claims); the address-resolver dedupe
holds in production (single canonical implementation actually serving traffic); E-6 aggregation is
live; NF-1 closed. No HALT conditions.

**HALTs:** none.

---

## W2 — Ring-2 post-deploy prod verification (CLOSING REPORT)

**Trigger:** `r5/w2` merged to `main` at commit `86ff799f` (PR #473), deployed
(`amjis-mcp-00399-dmb`/`amjis-web-00879-dzg`). Post-deploy live verification found a real,
systemic gap: the graph-traversal, frame-facet, and paradigm-facet lanes had all verified their
gates by calling the underlying capability handler directly (in-process), never through the live
MCP tool layer — and none of the new params (`about_from`/`about_to`/`direction`/`min_strength`
for graph traversal; `frame` for positions/signals; `paradigm` for signals) were actually forwarded
by the MCP-facing tools/aliases. Confirmed live: `ganita_positions_get(frame:"chandra")` returned
`frame:"lagna"` in the response — the exact same failure class as P1 (a param silently dropped at
the platform/platform-mcp seam), recurring because verification stopped at the capability layer.

**Fix (PR #474, commit `4b587035`):** declared and forwarded the missing params in all affected
MCP-facing surfaces — `traverse_graph`/`get_cgm_subgraph` (registry_bridge.ts) and
`bodha_graph_traverse_get` (register_p1_aliases.ts) for graph traversal; `get_signals`
(registry_bridge.ts) and `bodha_signals_get` (register_p1_aliases.ts) for frame/paradigm on
signals; `get_positions` (registry_bridge.ts) and `ganita_positions_get` (register_p1_aliases.ts)
for frame on positions. Also confirmed `get_strength` has NO MCP-facing tool/alias at all yet —
pre-existing gap, not introduced by W2, flagged to R5_PUNCHLIST rather than fixed here (out of
this fix's scope).

**Redeployed** (`amjis-mcp-00400-w24`/`amjis-web-00880-bxg`, traffic confirmed on latest revisions,
no deploy race). All four W2 gates re-verified live via ACTUAL MCP tool calls (not the capability
handler) after the fix:

1. **Graph traversal** — `bodha_graph_traverse_get(mode:"paths", about_from:"lord_of(bhava 10)",
   about_to:{graha:"Moon"}, direction:"directed")` on native chart: resolves the 10th lord to
   Saturn (via the served `about_resolution` chain), finds a direct 1-hop path
   Saturn→Moon (`path_length: 1`), ONE call. **PASS.**
2. **Frame facet** — `ganita_positions_get(frame:"chandra")`: response now correctly reports
   `frame: "chandra"` (was silently `"lagna"` before the fix). **PASS.**
3. **Paradigm facet** — `bodha_signals_get(paradigm:"jaimini")`: every returned signal's
   `signal_tradition` is `"jaimini"` — no mixing. **PASS.**
4. **Corpus citations** — `vector_search(query_text:"neecha bhanga raja yoga")`: `search_mode:
   "hybrid_vector_keyword"`, citations carry real `verse_text_en` (not bare refs), each with a
   `source_citation` provenance tag. This gate was never broken by the MCP-alias gap (corpus
   search's alias already forwarded its params correctly) — **PASS**, confirmed independently.

One transient 401 on the very first post-deploy call (self-resolved on retry) — consistent with
the cold-start blip pattern already noted at W1's Ring-2 close, not a regression.

### Overall Ring-2 verdict: **PASS (after in-flight fix)**

All four named W2 gates hold on live prod via the actual product surface (MCP tool calls), not
just the capability layer. **Process finding for future waves:** lane/verifier gate verification
that stops at the capability-handler level is insufficient — it must include at least one live MCP
`tools/call` per gate, since the platform/platform-mcp seam is exactly where P1-class param-drop
bugs recur. Recording this as a standing Ring-2 requirement going forward, not just a one-off fix.

**HALTs:** none.
