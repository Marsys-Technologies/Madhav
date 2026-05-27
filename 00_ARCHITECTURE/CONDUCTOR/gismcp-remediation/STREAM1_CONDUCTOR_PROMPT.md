# GISMCP Remediation — Stream 1 Conductor Prompt
# Paste this ENTIRE prompt into a Claude Code chat session.
# Folder: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1
# Branch: fix/gismcp-r1-r2
# Covers: R1 (de-gating) + R2 (4 stub retrieval engines)
# ─────────────────────────────────────────────────────────────────────────────

You are the Stream 1 Conductor for GISMCP Remediation.
You execute 6 sessions autonomously from `session_queue_s1.yaml`.
No human confirmation gates during code execution.
You log progress to `/tmp/gismcp_stream1.log.txt`.

---

## YOUR MANDATE

Fix two categories of MCP tool failures:
1. **R1**: Remove tier-based gating from `server.ts` so all 40 tools are unconditionally visible
2. **R2**: Build retrieval engines for 4 stub tools that currently 500 at the platform layer

Reference document: `00_ARCHITECTURE/BRIEFS/GISMCP_REMEDIATION_PLAN_v1_0.md`
Session queue: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/session_queue_s1.yaml`
All work must be on branch `fix/gismcp-r1-r2` in this worktree.

---

## EXECUTION PROTOCOL

For each session in the queue:

1. **Read the brief** at `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/<ID>_BRIEF.md`
2. **Execute** every step in the brief
3. **Run check_commands** from `session_queue_s1.yaml` for that session
4. If ALL check_commands pass → mark session COMPLETE in the queue YAML, log to `/tmp/gismcp_stream1.log.txt`
5. If ANY check_command fails → retry the session ONCE (re-read brief, fix the issue, re-run checks)
6. If still failing after retry → halt and print `CONDUCTOR_HALT: <session_id> — <failure>`. Do not proceed.

---

## SESSION EXECUTION ORDER

Execute in this exact order. Do not skip. Do not reorder.

### Session 1: R1-S1 — server.ts de-gating

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R1_S1_BRIEF.md`

Key action: Remove the `if (tier !== 'client')` block from `platform-mcp/src/server.ts`.
Audit `read_asset.ts`, `get_trace.ts`, `list_recent_queries.ts` for secondary tier gates.
Commit with message: `fix(R1): remove tier gating from server.ts — all 40 tools unconditional`

Verify:
```bash
! grep -q "tier !== 'client'" /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform-mcp/src/server.ts \
  && echo "R1-S1 PASS: tier gate removed" \
  || echo "R1-S1 FAIL: tier gate still present"
```

---

### Session 2: R1-T1 — Tier visibility tests

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R1_T1_BRIEF.md`

Key action: Create `platform-mcp/src/__tests__/server_tier_visibility.test.ts` asserting all 40 tools for all tiers.
Run `npx vitest run` in `platform-mcp` → must show 0 failures.
Commit.

Verify:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform-mcp
npx vitest run src/__tests__/server_tier_visibility.test.ts 2>&1 | tail -5
```

---

### Session 3: R2-S1 — query_tara_balam + query_chandra_balam engines

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_S1_BRIEF.md`

Key actions:
1. Read `platform/src/lib/retrieve/query_dasha_periods.ts` as pattern reference
2. Check `ephemeris` table schema — find Moon nakshatra and Moon sign columns
3. Create `platform/src/lib/retrieve/query_tara_balam.ts`
4. Create `platform/src/lib/retrieve/query_chandra_balam.ts`
5. Export both from `platform/src/lib/retrieve/index.ts`
6. Register both in RETRIEVAL_TOOLS

**Tara Balam formula:** `tara = ((transit_nak_index - 25 + 27) % 27) % 9 + 1`
**Chandra Balam formula:** `position = ((transit_moon_sign - 12 + 12) % 12) + 1`

Verify:
```bash
test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform/src/lib/retrieve/query_tara_balam.ts \
  && echo "Tara: EXISTS" || echo "Tara: MISSING"
test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform/src/lib/retrieve/query_chandra_balam.ts \
  && echo "Chandra: EXISTS" || echo "Chandra: MISSING"
grep -q 'query_tara_balam' /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform/src/lib/retrieve/index.ts \
  && echo "index.ts: tara exported" || echo "index.ts: tara MISSING"
```

---

### Session 4: R2-S2 — jaimini_chara_dasha + jaimini_chara_dasha_full engines

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_S2_BRIEF.md`

Key actions:
1. Check DB for existing Jaimini Chara Dasha tables or chart_facts entries
2. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` for planet degrees
3. Implement both engines (read from DB if precomputed; compute from chart_facts if not)
4. Export and register both

**Critical:** For native (Abhisek Mohanty):
- Lagna = Aries (Mesha) — forward sequence
- AK = Saturn (highest degree in sign among 7 planets)
- Verify AK from actual FORENSIC data before hardcoding

Verify:
```bash
test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform/src/lib/retrieve/jaimini_chara_dasha.ts \
  && echo "ChDa: EXISTS" || echo "ChDa: MISSING"
grep -q 'jaimini_chara_dasha' /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform/src/lib/retrieve/index.ts \
  && echo "index.ts: jaimini exported" || echo "index.ts: jaimini MISSING"
```

---

### Session 5: R2-T1 — Integration tests for all 4 engines

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_T1_BRIEF.md`

Key action: Create 3 integration test files. Run against DB proxy.
Tests must be FORENSIC-grounded: birth date 1984-02-05 checks.

Verify:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/platform
DB_PROXY_PORT=5433 npx vitest run \
  src/lib/retrieve/__tests__/query_tara_balam.test.ts \
  src/lib/retrieve/__tests__/query_chandra_balam.test.ts \
  src/lib/retrieve/__tests__/jaimini_chara_dasha.test.ts \
  2>&1 | tail -10
```

If DB proxy is not running: tests skip (CI-safe). The check_command passes if tests either PASS or SKIP. FAIL is unacceptable.

---

### Session 6: R2-T2 — MCP smoke tests + full vitest + Stream 1 seal

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R2_T2_BRIEF.md`

Key actions:
1. Run full `npx vitest run` in both `platform` and `platform-mcp` → 0 failures
2. Create `platform/src/__tests__/integration/mcp_stub_engines.integration.test.ts`
3. Create `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_COMPLETE.md` seal

Verify:
```bash
test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S1/00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM1_COMPLETE.md \
  && echo "STREAM1_COMPLETE.md: PRESENT" \
  || echo "STREAM1_COMPLETE.md: MISSING"
```

---

## LOGGING

After each session, append to `/tmp/gismcp_stream1.log.txt`:
```
[TIMESTAMP] Session <ID>: <PASS|FAIL|SKIP>
  check_commands: <all passed / N failed>
  commit: <git commit hash>
  note: <any issues encountered>
```

---

## FINAL REPORT

After all 6 sessions complete, print:

```
╔══════════════════════════════════════════════════════════════════╗
║          GISMCP STREAM 1 — EXECUTION SUMMARY                    ║
╠══════════════════════════════════════════════════════════════════╣
║  R1-S1: [PASS/FAIL]  server.ts tier gate removed                ║
║  R1-T1: [PASS/FAIL]  tier visibility tests (N tests)            ║
║  R2-S1: [PASS/FAIL]  query_tara_balam + query_chandra_balam     ║
║  R2-S2: [PASS/FAIL]  jaimini_chara_dasha engines                ║
║  R2-T1: [PASS/FAIL]  integration tests (DB proxy)               ║
║  R2-T2: [PASS/FAIL]  smoke tests + vitest baseline              ║
╠══════════════════════════════════════════════════════════════════╣
║  Branch: fix/gismcp-r1-r2                                       ║
║  STREAM1_COMPLETE.md: [PRESENT/MISSING]                         ║
╠══════════════════════════════════════════════════════════════════╣
║  OPERATOR DEPLOY STEPS (run manually after Stream 2 complete):  ║
║  1. cd /Users/Dev/Vibe-Coding/Apps/Madhav                       ║
║     git merge --no-ff fix/gismcp-r3                             ║
║     git merge --no-ff fix/gismcp-r1-r2                          ║
║     git push origin main                                         ║
║  2. Deploy amjis-web (new retrieve tools — R2):                  ║
║     gcloud builds submit --config cloudbuild.yaml \             ║
║       --project madhav-astrology                                 ║
║  3. Deploy amjis-mcp sidecar (de-gating — R1):                  ║
║     gcloud builds submit --config cloudbuild.yaml \             ║
║       --substitutions=_DEPLOY_TARGET=sidecar \                  ║
║       --project madhav-astrology                                 ║
╚══════════════════════════════════════════════════════════════════╝
```

Run sessions 1–6 now. Stop and report at any CONDUCTOR_HALT.
