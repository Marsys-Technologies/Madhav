---
artifact: MCP_RED_TEAM_v1_0.md
canonical_id: MCP_RED_TEAM
version: 1.0
status: PASS
session_id: MCP-4-S2
red_team_date: 2026-05-21
authored_by: Claude Code sub-agent (MCP-4-S2)
governing_brief: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
scope: MCP workstream §IS.8(b) red-team pass — Phase MCP-4 gate
---

# MCP Workstream — Red-Team Report v1.0

## Summary

- class-1 findings: 0
- class-2 findings: 2
- class-3 findings: 3
- red-team status: PASS

Zero class-1 (blocking) findings. No security vulnerabilities or hard governance
rule violations discovered. Two class-2 findings (significant correctness issues
to address post-merge) and three class-3 findings (minor issues, style/documentation).

---

## Governance checks (G1–G12)

| Check | Rule | Verdict | Notes |
|---|---|---|---|
| G1 | B.11 floor: ≥1 L2.5 tool when mode != "factual" | PASS | `enforceB11Floor()` injects `msr_sql` + `cgm_graph_walk` unconditionally if no L2.5 tool present |
| G2 | Audience tier stamped from API key, never request body | PASS | `plan.audience_tier = audienceTier` (route:405) overwrites any caller-supplied value post-parse |
| G3 | Every MCP call writes to query_trace_steps | PASS | `traceEmitter.emitStep()` called in all paths; primitives tag `source: "mcp_primitive"` |
| G4 | Predictive ask_madhav calls log PPL before returning | PASS | `logPrediction()` called before `buildEnvelope()` at route:564; non-fatal on DB error |
| G5 | Epistemics block mandatory on every response | PASS | `buildEpistemicsBlock()` required param in `buildEnvelope()`; no code path skips it |
| G6 | ask_madhav returns citations | PASS | `extractMcpCitations()` runs post-synthesis; citations array in all `buildEnvelope()` calls |
| G7 | No fabrication (B.10): numerical values from data tables | PASS | MCP introduces zero new compute paths; all values from retrieval tools or FORENSIC/ephemeris |
| G8 | Layer purity (B.1): L1 reads separate from L2.5 synthesis | PASS | Primitives labeled `surgical: true`; ask_madhav has `synthesis_audit` block proving L2.5 fired |
| G9 | Versioning (B.8): platform-mcp carries semver | PASS | `platform-mcp/package.json` version field present; CAPABILITY_MANIFEST.json entry tracks version |
| G10 | Scope boundary: no pre-build for M6+ | PASS | All 10 primitives map to existing retrieval tools; no future-tool references found |
| G11 | Mirror discipline: no Gemini-side surface, no MP.N pair | PASS | No mirror pair declared in CANONICAL_ARTIFACTS; MCP is correctly Claude-side only |
| G12 | Red-team obligation: this session IS the red-team | PASS | Session MCP-4-S2 executes the §IS.8(b) red-team; report is the discharge artifact |

---

## Security checks (SEC.1–SEC.8)

| Check | Rule | Verdict | Notes |
|---|---|---|---|
| SEC.1 | Auth bypass: unauthenticated caller reaches /api/mcp/* | PASS | Layer 1 (service token) blocks arbitrary internet clients; Layer 2 (principal headers) enforced |
| SEC.2 | Tier escalation: client-tier caller accesses super_admin tools via crafted request | PASS | `plan.audience_tier = audienceTier` overwrites after parse (RT-08); tier is DB-resolved |
| SEC.3 | Plan tampering: execute_plan bypasses tool whitelist | PASS | `PipelinePlanSchema.safeParse()` validates shape; tier overwrite prevents escalation |
| SEC.4 | API key security: keys stored hashed; one-time display enforced | PASS | PBKDF2-SHA256/100k iterations; `key_hash` stored; `full_key` returned only at creation |
| SEC.5 | Rate limiting invoked before tool execution | PASS | `checkRateLimit(keyId, ...)` called before body parse in all three handlers |
| SEC.6 | Prototype pollution: isAllowedSurgicalTool uses Object.hasOwn | PASS | Line 68 of primitives_registry.ts: `return Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)` |
| SEC.7 | Path traversal: read_asset restricts to known canonical paths | PASS | `SAFE_ASSET_MAP` is a hardcoded lookup; canonical_id → path; never user-controlled path construction |
| SEC.8 | Internal token validated (not just present) | PARTIAL PASS — see RT-SEC8 below |

---

## Findings

### RT-01 — Auth bypass: invalid key

**Class:** 3 (PASS — no issue)
**Test method:** Code inspection + Jest tests in `red_team/auth_bypass.test.ts`
**Result:** PASS
**Evidence:**
- `validateMcpKey(null)` returns `null` immediately (line 77 of auth.ts).
- `splitKey()` requires format `mcp_<env>_<40chars>`; arbitrary strings return `null` without DB access.
- DB lookup uses `WHERE key_id = $1 AND revoked_at IS NULL LIMIT 1`; no row means `null` returned.
- Wrong tail: `verifyKeyTail()` uses `crypto.timingSafeEqual()` — timing-safe, returns `false` on mismatch.
- DB errors return `null` (never throw to caller).
- `Authorization: Bearer <key>` prefix enforced; missing prefix rejected before DB.

**Remediation:** None required.

---

### RT-02 — Auth bypass: revoked key

**Class:** 3 (PASS — correct behavior, but no dedicated test in prior sessions)
**Test method:** Code inspection + Jest tests in `red_team/auth_bypass.test.ts` (RT-02 block)
**Result:** PASS
**Evidence:**
- auth.ts line 98–100: `WHERE key_id = $1 AND revoked_at IS NULL` — revoked keys are excluded by the DB query.
- Prior `auth.test.ts` did NOT include a test for the `revoked_at IS NULL` guard specifically.
- New test `RT-02a` captures the SQL call and asserts it contains `revoked_at IS NULL`.

**Class adjustment:** Class 3 (not class 2) because the SQL is correct. The gap was only in test coverage.
**Remediation:** `red_team/auth_bypass.test.ts` adds the missing test.

---

### RT-03 — Audience-tier leakage via primitive

**Class:** 3 (PASS — tier resolved from DB only)
**Test method:** Code inspection of `/api/mcp/primitives/[tool]/route.ts` and `platform-mcp/src/tools/`
**Result:** PASS
**Evidence:**
- `primitives/[tool]/route.ts` line 74: reads `audienceTierHeader` from `X-MCP-Audience-Tier` (Layer 2 header).
- Line 90–91: `audienceTier = audienceTierHeader === 'super_admin' ? 'super_admin' : 'client'` — binary mapping.
- The `X-MCP-Audience-Tier` header is set by the MCP server after it resolves the principal from the DB
  (`mcp_api_keys.audience_tier`). An internet client cannot reach `/api/mcp/primitives/*` directly because
  Layer 1 (`X-MCP-Internal-Token`) blocks it.
- The caller (Claude) passes a Bearer key to the MCP server; the MCP server resolves the tier from DB; the
  tier travels via the service-to-service channel to the platform. The caller never sets the tier directly.

**Remediation:** None required.

---

### RT-04 — Primitive whitelist enforcement

**Class:** 3 (PASS — whitelist correctly enforced)
**Test method:** Code inspection + Jest tests in `red_team/whitelist.test.ts`
**Result:** PASS
**Evidence:**
- `isAllowedSurgicalTool(mcpToolName)` (primitives_registry.ts line 66–68) uses `Object.hasOwn()`.
- A call to `/api/mcp/primitives/pattern_register` returns `{ok: false, error: {class: "validation"}}` 400
  because `isAllowedSurgicalTool("pattern_register")` is `false` (not in `MCP_TO_RETRIEVAL_TOOL`).
- Prior `primitives.test.ts` already covers this. `whitelist.test.ts` adds additional negative cases and
  prototype-pollution guards.

**Remediation:** None required.

---

### RT-05 — SQL injection via tool params

**Class:** 3 (PASS — all user params use parameterized queries)
**Test method:** Code inspection of `msr_sql.ts`, `lel_query.ts`, `chart_facts_query.ts`
**Result:** PASS with one note
**Evidence:**
- `msr_sql.ts`: SQL is a static template with `$1` through `$9` positional parameters (line 79–92).
  User params flow through `query(SQL, [param1, param2, ...])` — fully parameterized.
- `lel_query.ts` `buildQuery()`: Uses `idx` counter and `$${idx++}` — all user-supplied values
  (start_date, end_date, category, significance) use positional params.
- **Note — LIMIT in lel_query.ts (line 97) and chart_facts_query.ts (line 217):** Both use
  `LIMIT ${limit}` with a JavaScript-interpolated integer. The value is computed via
  `Math.min(p.limit ?? 50, 50)` (lel_query) and `Math.min(p.limit ?? 20, 100)` (chart_facts_query).
  Since `Math.min()` of integers can only produce an integer, no SQL injection is possible here.
  However, if a non-numeric value is passed for `limit`, `Math.min(NaN, 50)` returns `NaN`, which
  would produce `LIMIT NaN` — a Postgres syntax error (not injection). This is a class-3 correctness
  gap, not a security vulnerability.

**Remediation (class-3):** Coerce limit to integer before `Math.min()`:
`const limit = Math.min(parseInt(String(p.limit ?? '20'), 10) || 20, 100)`
This prevents `LIMIT NaN` on malformed input.

---

### RT-06 — Rate limit bypass

**Class:** 3 (PASS with known limitation documented)
**Test method:** Code inspection of `rate_limiter.ts`
**Result:** PASS
**Evidence:**
- `checkRateLimit(keyId, ...)` is called with the resolved `keyId` from the principal headers.
  Since principal headers require Layer 1 auth (service token), no anonymous caller can reach
  the rate-limit check. The `keyId` is always the authenticated key's `key_id`.
- There is no bypass by omitting `key_id` — the route handler rejects requests without
  `X-MCP-Key-Id` before calling `checkRateLimit()`.
- **Known limitation (class-3):** The in-process `Map<string, RpmEntry>` resets on service restart.
  On Cloud Run with multiple instances, each instance has its own counter. Rate limit is therefore
  per-instance, not per-key globally. This means a caller could send up to `RPM_LIMIT × N_INSTANCES`
  RPM in the worst case. The brief documents this at §4.4 / rate_limiter.ts header comment. The
  daily token budget check IS DB-backed and cross-instance safe — it provides the harder global cap.

**Remediation (class-3):** Phase 2 hardening: replace in-process Map with Redis-backed counter
(documented in rate_limiter.ts header comment).

---

### RT-07 — PPL write tampering: record_outcome for unowned prediction

**Class:** 2 (GOVERNANCE GAP — cross-key outcome recording is not blocked)
**Test method:** Code inspection of `ppl_writer.ts` `recordOutcome()` and `writes/[action]/route.ts`
**Result:** PARTIAL PASS — governance gap, not a security breach
**Evidence:**
- `recordOutcome()` in `ppl_writer.ts` (lines 188–219) matches by `prediction_id` only:
  `UPDATE mcp_predictions WHERE prediction_id = $1`.
  It does NOT check that `key_id` of the outcome matches the `key_id` of the original prediction.
- A caller with key A could record an outcome for a prediction logged by key B if they know B's
  `prediction_id` format (`PPL.MCP.XXXXXXXX`).
- Per D12, all API keys are issued to trusted principals by the native (super_admin only). This is
  therefore a governance gap, not a security vulnerability — all key holders are trusted parties.
- The `outcome_key_id` column IS written with the recorder's `key_id`, providing an audit trail,
  but no blocking enforcement exists.

**Remediation (class-2):** Add a `key_id` cross-check to `recordOutcome()`:
```sql
UPDATE mcp_predictions
SET outcome_text = $2, ...
WHERE prediction_id = $1
  AND key_id = $3   -- block cross-key outcome recording
RETURNING prediction_id
```
Alternatively, document as an explicit governance exception for the current single-principal model
and add the check when multi-principal access is enabled (Phase 5).

---

### RT-08 — Plan-edit privilege escalation via execute_plan

**Class:** 3 (PASS — tier overwrite at route level prevents escalation)
**Test method:** Code inspection + Jest tests in `red_team/plan_escalation.test.ts`
**Result:** PASS
**Evidence:**
- `execute/route.ts` line 405: `plan.audience_tier = audienceTier` — overwrites the parsed value
  with the route-resolved tier (from `X-MCP-Audience-Tier` header, which is DB-resolved).
- This overwrite happens AFTER `PipelinePlanSchema.safeParse()` (line 386) and BEFORE all
  tier-sensitive logic: `arbitrateBudgets()` (line 414), `enforceB11Floor()` (line 435),
  `synthesis()` (line 472).
- A client-tier caller submitting a plan with `audience_tier: "super_admin"` will have the field
  overwritten to `"client"` before synthesis runs.
- `PipelinePlanSchema` does not enforce tier matching (expected — the enforcement is in the route).

**Remediation:** None required. The stamp-after-parse pattern is the correct defense.

---

### RT-09 — B.11 floor bypass via ask_madhav

**Class:** 2 (CORRECTNESS ISSUE — mode="factual" does not actually bypass B.11)
**Test method:** Code inspection of `execute/route.ts` `enforceB11Floor()` and `isSurgical` logic
**Result:** PARTIAL PASS — G1 is satisfied for non-factual modes, but the factual-mode bypass is not implemented as documented
**Evidence:**
- `enforceB11Floor()` is called at line 435 UNCONDITIONALLY — it runs for all modes including
  `mode="factual"`.
- `isSurgical = modeParam === 'factual'` is computed at line 468, AFTER the B.11 floor enforcement
  has already injected `msr_sql` + `cgm_graph_walk` into the plan.
- AC.1.5 states: `synthesis_audit.holistic_read_passed` should be `false` if B.11 floor was
  bypassed. But in `mode="factual"`, B.11 is NOT bypassed — it is still enforced.
- `holistic_read_passed` will be `true` even for `mode="factual"` calls, because the floor
  injects L2.5 tools regardless.
- The `isSurgical` flag correctly labels the epistemics block `surgical: true`, but this is
  cosmetic — the pipeline still ran L2.5 tools.
- **Effect on G1:** G1 is OVER-satisfied (B.11 runs for all modes, never bypassed). The brief
  intended factual mode to skip B.11, but the implementation enforces it for all modes.

**Classification rationale:** Class 2 (not class 1) because:
- G1 passes (B.11 IS enforced for all modes including factual).
- The brief's intent for factual mode is "single-tool surgical" but the implementation produces
  a more conservative result (full holistic). This is a correctness gap vs. spec, not a security
  or governance violation. The governance rules (B.11) are if anything over-enforced.
- AC.1.5 is violated: `holistic_read_passed=false` will never appear for factual mode.

**Remediation (class-2):** Two options:
1. Add a factual-mode bypass before `enforceB11Floor()`:
   ```typescript
   const modeParam = String(params?.mode ?? 'auto')
   const isSurgical = modeParam === 'factual'
   // ... (derive isSurgical before calling enforceB11Floor)
   if (!isSurgical) {
     const b11Result = enforceB11Floor(plan, toolsAuthorized)
     // ... apply
   }
   ```
2. Retain current behavior (B.11 always enforced) and update AC.1.5 to reflect that
   `holistic_read_passed=false` is impossible — only the epistemics.surgical flag distinguishes
   factual mode.

Option 2 is lower risk and aligns with the governance spirit. Document as a known spec delta.

---

### RT-SEC8 — Internal token: validation method (string equality)

**Class:** 3 (PASS with note — string comparison is correct but not timing-safe)
**Test method:** Code inspection of `validateServiceToken()` in all three route files
**Result:** PASS with note
**Evidence:**
- `validateServiceToken()` in execute/route.ts (line 65), primitives/[tool]/route.ts (line 40), and
  writes/[action]/route.ts (line 57) all use `token === expected` — strict equality.
- This is a shared-secret comparison, not a HMAC or OIDC token. The comparison is NOT timing-safe.
- **Risk assessment:** In the Cloud Run topology, `amjis-mcp` → `amjis-web` communication is over
  HTTPS within Google's network. An attacker cannot observe timing differences across network hops
  of this magnitude (milliseconds vs nanoseconds). Timing attacks on this comparison are not
  practically feasible in this topology.
- **Missing env var in production:** If `MCP_INTERNAL_TOKEN` is not set in production, the route
  logs an error and returns `false` (correctly blocks). The development shortcut (`NODE_ENV=development`
  → allow all) is appropriate for local testing.

**Remediation (class-3, low priority):** Replace `token === expected` with a timing-safe comparison
using `crypto.timingSafeEqual()`. This is defense-in-depth for any future topology where the service
is exposed over a lower-latency channel:
```typescript
function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) { ... }
  if (!token || token.length !== expected.length) return false
  const a = Buffer.from(token)
  const b = Buffer.from(expected)
  return crypto.timingSafeEqual(a, b)
}
```

---

## Test files authored

| File | Tests | Covers |
|---|---|---|
| `platform/src/lib/__tests__/mcp/red_team/auth_bypass.test.ts` | 14 | RT-01, RT-02 |
| `platform/src/lib/__tests__/mcp/red_team/whitelist.test.ts` | 15 | RT-04, RT-06 (prototype pollution) |
| `platform/src/lib/__tests__/mcp/red_team/plan_escalation.test.ts` | 5 | RT-08 |

---

## Post-merge follow-up items (class-2)

These are not blockers for merge but should be addressed in a follow-up session:

| Item | Finding | Suggested fix |
|---|---|---|
| PPL-01 | RT-07: `recordOutcome()` allows cross-key outcome recording | Add `AND key_id = $N` to the UPDATE WHERE clause, or document as explicit governance exception |
| B11-01 | RT-09: `mode="factual"` does not bypass B.11 floor as specified | Move `isSurgical` detection before `enforceB11Floor()` call, or update AC.1.5 to reflect always-on enforcement |

---

## Scope boundary confirmation

All red-team work respected the `must_not_touch` list from CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md:
- No application code was modified (read-only review).
- Three test files created under `platform/src/lib/__tests__/mcp/red_team/` (in `may_touch`).
- `MCP_RED_TEAM_v1_0.md` created under `00_ARCHITECTURE/` (in `may_touch`).

---

*End of MCP_RED_TEAM_v1_0.md (v1.0, 2026-05-21). Red-team session: MCP-4-S2. Status: PASS.*
