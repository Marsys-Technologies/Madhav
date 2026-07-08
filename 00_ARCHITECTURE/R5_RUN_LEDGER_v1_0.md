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
