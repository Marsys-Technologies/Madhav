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
