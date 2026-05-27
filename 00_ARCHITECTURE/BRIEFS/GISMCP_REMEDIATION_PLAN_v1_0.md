---
canonical_id: GISMCP_REMEDIATION_PLAN_v1_0
version: 1.0
status: ACTIVE
authored: 2026-05-26
author: Cowork (Abhisek Mohanty)
project: MARSYS-JIS
workstream: GISMCP Remediation
phase: MCP-R
---

# GISMCP Remediation Plan v1.0

## §1 — Mission

Fix four identified gaps in the GISMCP instrument (MCP sidecar `amjis-mcp`, 40 tools) so that:

1. **All 40 tools are visible to ALL API key tiers** — the 5 ops tools currently hidden behind `if (tier !== 'client')` in `server.ts` are unconditionally registered.
2. **Super_admin (native Abhisek) sees all 40 tools** — tier gating removed so the native's own instrument is fully accessible.
3. **Retrieval engines exist for all 4 stub tools** — `query_tara_balam`, `query_chandra_balam`, `jaimini_chara_dasha`, `jaimini_chara_dasha_full` currently return 500 at platform layer.
4. **All 573 MSR signals are verifiably accessible with complete grounding** — confirm or complete the 100% grounding achieved by MCP Transformation; ensure discovery layer tools surface fully attributed responses.

## §2 — Out of Scope

- Portal planner `expose_to_planner` manifest flags (deferred to portal sprint — out of scope per native directive 2026-05-26)
- Any portal-side (`platform/src/app/`) changes
- New MCP tools beyond the 4 stub engines

## §3 — Clarification: The 573 Signals Question

The MCP Transformation workstream (COMPLETE 2026-05-22) achieved "573/573 MSR signals grounded (100%)" per `STREAM_MCPT_CLOSE_v1_0.md`. All 573 signals in the MSR are accessible via `msr_sql`, `pattern_register`, `resonance_register`, `cluster_atlas`, and `contradiction_register`.

The 74% quality assignment in the prior session was about **citation completeness depth** (whether each signal has explicit FORENSIC fact IDs in its `source_citation` field), NOT about signal count or accessibility. The signals are accessible. R3 verifies and, if any gap was introduced post-MCPT, completes the grounding.

## §4 — Phase Breakdown

### Phase R1 — Tool Visibility De-gating (Stream 1, Sessions 1–2)

**Problem:** `platform-mcp/src/server.ts` contains:
```typescript
if (tier !== 'client') {
  registerToolHealth(server)
  registerDataCoverage(server)
  registerLogPrediction(server)
  registerRecordOutcome(server)
  registerFlagDisagreement(server)
}
```
This hides 5 ops tools from any API key classified as `client` tier, including the native's own key if registered at that tier.

**Fix:** Remove the conditional. All 40 tools register unconditionally for all tiers. The native is the super_admin of his own instrument; there is no reason to hide mutation/observability tools from MCP callers.

**Also audit:** Confirm `read_asset`, `get_trace`, `list_recent_queries` (observability + raw asset group) have no hidden tier gating or secondary conditionals in their individual tool handlers.

**Sessions:**
- R1-S1: Remove `if (tier !== 'client')` block; audit observability tools; update any tool-handler-level tier checks
- R1-T1: Unit tests + integration tests verifying 40 tools visible at every tier

**Acceptance criteria:**
- `! grep -q "tier !== 'client'" platform-mcp/src/server.ts`
- Tool discovery endpoint returns 40 tools for `client` tier API key
- No secondary tier gate in `read_asset`, `get_trace`, `list_recent_queries` handlers
- All prior server.ts tests pass; new tier-visibility tests added

---

### Phase R2 — Stub Engine Implementation (Stream 1, Sessions 3–6)

**Problem:** Four tools are whitelisted in `primitives_registry.ts` and registered in `server.ts` but have no platform retrieval engine. They pass the dispatch whitelist, reach `platform/src/lib/retrieve/`, and fail with retrieval-not-found (500).

**Tool: `query_tara_balam`**
Tara Balam = 9-fold Nakshatra cycle computed from the native's natal Moon nakshatra.
- Native's natal Moon nakshatra: **Purva Bhadrapada (PBh, index 25 in 1-27 count)** per FORENSIC data
- For any date range, look up transit Moon nakshatra from the `ephemeris` table
- Tara number = `((transit_nak_index − 25 + 27) % 27) % 9 + 1`  (1-based, wraps at 9)
- Tara names: 1=Janma, 2=Sampat, 3=Vipat, 4=Kshema, 5=Pratyari, 6=Sadhaka, 7=Vadha, 8=Mitra, 9=Ati-Mitra
- Benefic: 2, 4, 6, 8, 9; Malefic: 1, 3, 5, 7
- Output: per-date Tara number + name + benefic/malefic classification

**Tool: `query_chandra_balam`**
Chandra Balam = transit Moon sign relative to natal Moon sign.
- Native's natal Moon sign: **Pisces (Meena, sign 12)** per FORENSIC data
- For any date range, look up transit Moon sign from `ephemeris` table
- Position = `((transit_sign − 12 + 12) % 12) + 1`  (1-based from natal sign)
- Standard benefic positions: 1, 3, 6, 7, 10, 11; Malefic: 2, 4, 5, 8, 9, 12
- Output: per-date Chandra Balam position + classification

**Tool: `jaimini_chara_dasha`**
Jaimini Chara Dasha for the native — current dasha + antardasha periods.
- Computation uses FORENSIC chart data (planet degrees, sign lords, Atmakaraka identification)
- Native AK: **Saturn** (highest degree in sign per standard Jaimini rule) — verify from FORENSIC
- Dasha sequence: Lagna sign onwards, alternating forward/backward by sign parity
- Each rashi dasha length = `(12 − degrees_of_sign_lord_in_sign) + 1` years (standard formula)
- Output: current chara dasha rashi, start date, end date, current antardasha, balance remaining

**Tool: `jaimini_chara_dasha_full`**
Full Jaimini Chara Dasha sequence from birth to current date + 30 years forward.
- Same computation as above but returns the complete sequence, not just current period
- Each entry: rashi, start_date, end_date, lord, antardasha_sequence

**Implementation location:** `platform/src/lib/retrieve/` — one file per tool, following existing retrieve tool patterns (e.g., `query_dasha_periods.ts` as reference).

**Sessions:**
- R2-S1: `query_tara_balam.ts` + `query_chandra_balam.ts` — implement, export from retrieve/index.ts
- R2-S2: `jaimini_chara_dasha.ts` + `jaimini_chara_dasha_full.ts` — implement, export
- R2-T1: Integration tests for all 4 engines using FORENSIC-grounded inputs
- R2-T2: MCP smoke tests (calls via actual platform endpoint) + final seal

**Acceptance criteria (R2-S1):**
- `test -f platform/src/lib/retrieve/query_tara_balam.ts`
- `test -f platform/src/lib/retrieve/query_chandra_balam.ts`
- Both exported in `platform/src/lib/retrieve/index.ts`
- For birth date 1984-02-05: `query_tara_balam` returns tara_number=1 (Janma) — Moon PBh natal = Moon PBh transit = position 1

**Acceptance criteria (R2-S2):**
- `test -f platform/src/lib/retrieve/jaimini_chara_dasha.ts`
- `test -f platform/src/lib/retrieve/jaimini_chara_dasha_full.ts`
- Both exported in retrieve/index.ts
- jaimini_chara_dasha returns a valid current_dasha_rashi, start_date, end_date for native

**Acceptance criteria (R2-T1):**
- `npx vitest run src/lib/retrieve/__tests__/query_tara_balam.test.ts` → 0 failures
- `npx vitest run src/lib/retrieve/__tests__/query_chandra_balam.test.ts` → 0 failures
- `npx vitest run src/lib/retrieve/__tests__/jaimini_chara_dasha.test.ts` → 0 failures
- Integration tests run against DB proxy on 5433 — FORENSIC-grounded spot-checks pass

**Acceptance criteria (R2-T2):**
- All 4 tools return valid JSON (not 500) when called via `/api/mcp/primitives/query_tara_balam` etc.
- `msr_sql`, `query_dasha_periods`, and the 4 new engines return coherent data for native birth date

---

### Phase R3 — MSR Signal Grounding Verification (Stream 2, Sessions 1–4)

**Problem (restated):** MCP Transformation claimed 100% MSR grounding. R3 audits this claim against the current DB state and, if any regression was introduced by subsequent workstreams (DAR, UDA, Universal Parity), completes the grounding.

**Definition of "grounded":** An MSR signal is grounded if its DB record has a non-null `source_citation` field (or equivalent) containing at least one explicit FORENSIC fact ID (e.g., `FORENSIC.ASC.1`, `FORENSIC.MOON.3`) or LEL event ID (`LEL.EV.023`).

**Sessions:**
- R3-S1: Audit — count ungrounded signals, sample 20, produce `MSR_GROUNDING_AUDIT.md`
- R3-S2: Remediate — if gap > 0, complete grounding for all ungrounded signals in batch
- R3-T1: Verify 573/573 grounded; run quality checks; author `MSR_GROUNDING_COMPLETE.md`
- R3-SEAL: Update `CAPABILITY_MANIFEST.json` grounding status; append SESSION_LOG entry

**Acceptance criteria (R3-S1):**
- `test -f 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md`
- Audit document states exact count of grounded vs ungrounded signals with signal IDs

**Acceptance criteria (R3-T1):**
- DB query: `SELECT COUNT(*) FROM msr_signals WHERE source_citation IS NULL` → 0
- (Or equivalent field name as found in the actual schema)

---

## §5 — Stream Topology

```
Stream 1 (worktree: fix/gismcp-r1-r2):
  R1-S1 → R1-T1 → R2-S1 → R2-S2 → R2-T1 → R2-T2

Stream 2 (worktree: fix/gismcp-r3):
  R3-S1 → R3-S2 (conditional) → R3-T1 → R3-SEAL
```

Streams run in parallel. Stream 1 touches `platform-mcp/src/server.ts` and `platform/src/lib/retrieve/`. Stream 2 touches MSR data and `CAPABILITY_MANIFEST.json`. No file overlap.

**Merge order after both streams complete:**
1. `git merge --no-ff fix/gismcp-r3` into main (data/manifest changes only)
2. `git merge --no-ff fix/gismcp-r1-r2` into main (server.ts + new engines)
3. Deploy `amjis-web` (new retrieve tools — FIX-R2)
4. Deploy `amjis-mcp` sidecar (de-gating — FIX-R1)

---

## §6 — Testing Matrix

| Test | Phase | Type | Condition | File |
|------|-------|------|-----------|------|
| All 40 tools registered unconditionally | R1-T1 | Unit | Always | server.test.ts |
| `read_asset` no tier gate | R1-T1 | Unit | Always | read_asset.test.ts |
| Tool list endpoint returns 40 for client tier | R1-T1 | Integration | DB proxy | mcp_visibility.integration.test.ts |
| `query_tara_balam` birth date = Janma | R2-T1 | Integration | DB proxy | query_tara_balam.test.ts |
| `query_chandra_balam` spot-check 3 dates | R2-T1 | Integration | DB proxy | query_chandra_balam.test.ts |
| `jaimini_chara_dasha` current dasha valid | R2-T1 | Integration | DB proxy | jaimini_chara_dasha.test.ts |
| `jaimini_chara_dasha_full` birth→+30y sequence | R2-T1 | Integration | DB proxy | jaimini_chara_dasha.test.ts |
| MCP endpoint /api/mcp/primitives/query_tara_balam → 200 | R2-T2 | Smoke | SMOKE_SESSION_COOKIE | mcp_stubs.smoke.test.ts |
| MSR signals grounded count = 573 | R3-T1 | Integration | DB proxy | msr_grounding.test.ts |
| Discovery tools return source_citation fields | R3-T1 | Integration | DB proxy | msr_grounding.test.ts |

CI-safe guards: integration tests skip when `DB_PROXY_PORT` absent; smoke tests skip when `SMOKE_SESSION_COOKIE` absent.

---

## §7 — Execution Model

- **Autonomous implementation**: Conductor spawns sub-agents per session brief. No human confirmation gates during code + test phase.
- **Human gate only**: (a) DB operations (if new migrations needed), (b) gcloud deploy commands (printed, not executed).
- **Conductor pattern**: `session_queue_s1.yaml` + `session_queue_s2.yaml`, `check_commands` per entry, retry-once on failure.
- **Two Conductor prompts**: `STREAM1_CONDUCTOR_PROMPT.md` (R1+R2), `STREAM2_CONDUCTOR_PROMPT.md` (R3).
- **Prep**: `PREP_PROMPT.md` — creates worktrees, writes `.claude/settings.local.json`, verifies env.

---

## §8 — Files Authored by This Plan

```
00_ARCHITECTURE/BRIEFS/GISMCP_REMEDIATION_PLAN_v1_0.md        ← this file
00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/
  README.md
  PREP_PROMPT.md
  STREAM1_CONDUCTOR_PROMPT.md
  STREAM2_CONDUCTOR_PROMPT.md
  session_queue_s1.yaml
  session_queue_s2.yaml
  briefs/
    R1_S1_BRIEF.md
    R1_T1_BRIEF.md
    R2_S1_BRIEF.md
    R2_S2_BRIEF.md
    R2_T1_BRIEF.md
    R2_T2_BRIEF.md
    R3_S1_BRIEF.md
    R3_S2_BRIEF.md
    R3_T1_BRIEF.md
    R3_SEAL_BRIEF.md
```

---

## §9 — Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-05-26 | Initial — 4 fix items, 3 phases, 10 sessions, 2 streams |
