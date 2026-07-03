---
canonical_id: CLAUDECODE_BRIEF_BA_W0_SERVING_TRUTH
version: 1.0
status: READY-FOR-EXECUTION — Wave 0 of the Beyond-Acharya program (serving truth + gate handoff)
created: 2026-07-02
author: Cowork — for execution by Claude Code in Antigravity
governs: BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v2_0.md §6 Wave W0 (=E0)
mode: FULLY AUTONOMOUS · swarm-or-single · worktree-isolated · prod-verified per Brahma AUTONOMOUS_MODE §F
depends_on: CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4_v1_0.md (this brief ABSORBS it — does not duplicate it)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (retrieval FROZEN; MCP adapts)
scope_guard: >
  Read-path / serving / wiring / schema / infra / governance ONLY. This wave does NOT touch the salience
  re-model, verdict synthesis, or any signal RANKING (that is W2+, native-design-gated). If a builder drifts
  toward changing how signals rank or adding verdict-synthesis, HALT — that is out of W0 scope.
---

# BA-W0 — SERVING TRUTH (Beyond-Acharya Wave 0)

## §0 — Why this brief exists (read first)

The Beyond-Acharya program (plan v2.0) cannot build W2's salience-v2 / promise / pratijna layer on top of a
serving surface that is silently broken. W0's job is to make the CURRENT instrument **connect, access,
retrieve cleanly and efficiently on PROD**, and to hand the next wave a clean readiness baseline. Nothing
here changes stored data, seal counts, or ranking.

**W0 is mostly already scoped.** The deterministic serving/schema/infra fixes are the in-flight
`CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4_v1_0.md`. This brief ABSORBS that campaign and adds the four
Beyond-Acharya-specific W0 items the audit swarm did not own. **Do NOT re-author the audit fixes — drive that
campaign to prod-done, then execute §2 here.**

## §1 — Absorbed: the audit-fix swarm (drive to prod-done)

Execute `CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4_v1_0.md` to completion under its own rails (autonomy,
per-wave prod-verify, morning report). Status at authoring (2026-07-02):

- **W1 ✅ DONE + prod-verified** — ayanamsha default/alias unblock (F-006/011/031). Insight surface serves on
  default ayanamsha. (This is the plan's "max_lenses / serves-on-default" E0 concern — already closed.)
- **W2 ✅ DONE + prod-verified** — serving wiring (catalog import, migration-365 VIEW→TABLE guard,
  mitigation_map whitelist; F-001/002/003/004/015/016/018).
- **W2.5 (verify landed)** — d7/d8 reasoning-unit registration (F-032, gates G10) + strip
  `audience_tier:"client"` leak (F-033). Recent commits (`271f0735`, `47279c5d`, `8c1f4aa0`) touch exactly
  this — **confirm on prod that `assess_marriage/career/health/wealth`, `yoga_activation_by_dasha`,
  `query_chart_facts`, `vector_search`, `get_cgm_subgraph` return structured responses (not 404), and no
  envelope contains `audience_tier`.**
- **W3 (OPEN — drive to done)** — output bounding: `response_format` must actually branch
  (digest/summary/full — F-026 currently inert); `get_domain_reading` must not return 17 MB (F-021); dedup
  `signal_id_refs` (F-023); bound `get_projections` (F-008); ~25k-token default cap + pagination; uniform
  error envelope (F-028). **This is the plan §1's "W3 bounding NOT live / 17.3 MB" item.**
- **W4 (OPEN — drive to done)** — L4 + sidecar repair: L4 schema drift missing `id`/`anchor_id` (F-005 —
  migration 365 targets it; confirm applied on prod-web, not just merged); `panchanga_daily` relation
  (F-014); re-provision corrupted `sepl_18.se1` ephemeris + sidecar image integrity (F-012/F-030 — the "kala
  sidecar down" item); root-cause L5 mimamsa 500s (F-013).

Deploy-truth rule (the migration-desync scar): a wave is done only when **BOTH `amjis-web` AND `amjis-mcp`
live Cloud Run revision image SHAs == the merged SHA**, verified with
`gcloud run services describe <svc> --region asia-south1 --format='value(status.traffic[0].revisionName)'`.
If the web deploy's "Run database migrations" step failed, the wave is BLOCKED regardless of MCP status.

## §2 — Beyond-Acharya-specific W0 items (NEW here; not in the audit swarm)

These four items exist because the Beyond-Acharya build depends on them, and the audit swarm did not own them.
Each is `[verify-against: <target>]`.

- **BA-W0.1 — Migration-numbering baseline `[verify-against: repo]`.** Confirm and record the true next-free
  migration number = `max(platform/migrations, platform/supabase/migrations) + 1`. At authoring: `platform/`
  max = 365, `supabase/` max = 384 → **next = 385**. Every subsequent BA wave brief must re-derive this at
  brief time (two-dir lexical-collision trap). Deliverable: one line in the run report stating the verified
  next number.

- **BA-W0.2 — `charts.chart_type` gap logged `[verify-against: db]`.** Confirm that `charts` has NO
  `chart_type` column (only `role CHECK (native/tertiary/fixture)`). **Do NOT add it in W0** — the prashna
  (W4) and synastry (W8) paths add it as their first migration. W0 only records the gap + the intended
  column shape (`chart_type TEXT NOT NULL DEFAULT 'natal'` with a backfill of all existing rows) in the run
  report so W4 does not rediscover it. This closes plan v2.0 correction C2.

- **BA-W0.3 — count_sql / stale-display invariant `[verify-against: db+prod]`.** Confirm the cockpit `Clear`
  path nulls `asset_throughput.rows_written`, so `count_sql` (chart-scoped `$1`) — not the poll-cache
  `rows_written` — is the source of truth after a Clear. If Clear does not null `rows_written`, file it as a
  W2 prerequisite (the tracker will otherwise lie after the L2 regeneration). This closes correction C4.
  (Note: `stats/route.ts` uses `rows_written` on the hot poll path and `count_sql` on `?mode=live` — the
  live path must be correct for every new scoring asset.)

- **BA-W0.4 — Governance sync `[verify-against: repo]`.** Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` to
  (a) reference the audit-fix campaign + its `MCP_AUDIT_FIX_W1_W4_RUN_REPORT`, and (b) register the
  Beyond-Acharya program as the active strategic arc pointing at
  `BEYOND_ACHARYA_MASTER_IMPLEMENTATION_PLAN_v2_0.md`. Closes correction C8.

## §3 — Invariants (every step)

1. **Frozen §4 seam:** retrieval chart-agnostic + FROZEN; entitlement at the channel; consume the registry,
   don't re-implement it or run MCP-side chart SQL. On conflict, retrieval wins.
2. **No stored-data / count / ranking change.** Confirm stored counts UNCHANGED after W0 (audit-swarm
   scorecard baseline; the swarm cites 64,765 for its surface). W0 changes serving/wiring/schema/infra/docs
   only.
3. **Model policy:** Gemini/DeepSeek only in any narration path; Anthropic banned unless native asks;
   scoring paths LLM-free (not exercised in W0).
4. **Prod, not worktree:** every acceptance criterion below is `[verify-against: prod]` unless tagged
   otherwise.

## §4 — ACCEPTANCE (W0 is done when ALL pass)

- `[verify-against: prod]` All 45 MCP tools return a structured response (no 404 "Unknown capability URI", no
  500, no schema-error) — the retrievability matrix is 45/45, INCLUDING `assess_marriage/career/health/wealth`
  and `yoga_activation_by_dasha`.
- `[verify-against: prod]` No `audience_tier` in any served envelope.
- `[verify-against: prod]` `response_format` demonstrably changes payload size (digest < summary < full); no
  default payload exceeds ~25k tokens; `get_domain_reading` bounded (no 17 MB); uniform error envelope.
- `[verify-against: prod]` `phala_outlook` / `event_anchors` / `query_special_lagnas` / `query_calibration`
  return data (not 500/schema-error); L4 `id`/`anchor_id` columns present; `panchanga_daily` populated; kala
  sidecar up (ephemeris `sepl_18.se1` valid).
- `[verify-against: prod]` BOTH `amjis-web` and `amjis-mcp` live revision SHAs == the merged SHA.
- `[verify-against: db]` `charts.chart_type` gap confirmed + shape recorded (BA-W0.2); Clear-nulls-rows_written
  invariant confirmed or filed (BA-W0.3).
- `[verify-against: repo]` Next-free migration number recorded (BA-W0.1); CURRENT_STATE synced (BA-W0.4).
- Retrieval FROZEN (git diff `lib/retrieval` minimal, serving-normalization only); chart-agnostic gate green;
  reverse-citation report for any delete; **Goal-Keeper confirms zero W2+ ranking/synthesis work crept in.**

## §5 — Exit artifact (the handoff into W1/W2)

Emit `BA_W0_SERVING_TRUTH_RUN_REPORT.md`:
- The before→after 45-tool retrievability matrix + the specific prod-prove evidence per item.
- Both services' live revision SHAs; stored-counts-unchanged confirmation.
- The four BA-W0.x deliverables (next-migration number, chart_type gap + shape, count_sql/Clear invariant
  status, CURRENT_STATE sync commit).
- A one-line **GO/NO-GO for W1 (judgment sitting)** — W1 is Cowork-led and needs no code, but it should not
  start until the serving surface it will design against is known-clean.

## §6 — Kickoff

Open Claude Code in Antigravity, bypass permissions, point the Conductor at THIS brief. It reads this + the
absorbed `CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4_v1_0.md` + the frozen §4 seam + plan v2.0 §1/§1.5, snapshots
at run-start, drives the absorbed W1–W4 to prod-done, then executes §2's four BA-W0 items, and emits §5's
report. Native reviews the report and schedules the W1 judgment sitting.

*End of CLAUDECODE_BRIEF_BA_W0_SERVING_TRUTH v1.0. Next: W1 judgment sitting (Cowork-led) → BA_W2A/W2B.*
