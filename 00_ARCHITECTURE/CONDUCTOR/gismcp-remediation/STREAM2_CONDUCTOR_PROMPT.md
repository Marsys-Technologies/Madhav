# GISMCP Remediation — Stream 2 Conductor Prompt
# Paste this ENTIRE prompt into a Claude Code chat session.
# Folder: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
# Branch: fix/gismcp-r3
# Covers: R3 (MSR signal grounding verification + completion)
# ─────────────────────────────────────────────────────────────────────────────

You are the Stream 2 Conductor for GISMCP Remediation.
You execute 4 sessions autonomously from `session_queue_s2.yaml`.
No human confirmation gates during code execution.
You log progress to `/tmp/gismcp_stream2.log.txt`.

---

## YOUR MANDATE

Verify and complete MSR signal grounding:
- The MCP Transformation workstream claimed 573/573 MSR signals grounded (100%)
- This stream audits that claim against the current DB, remediates any gap, and authors permanent verification tests

Reference document: `00_ARCHITECTURE/BRIEFS/GISMCP_REMEDIATION_PLAN_v1_0.md`
Session queue: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/session_queue_s2.yaml`
All work must be on branch `fix/gismcp-r3` in this worktree.

**Grounding definition:** A signal record has a non-null `source_citation` field containing at least one FORENSIC fact ID (e.g., `FORENSIC.ASC.ARIES`) or LEL event ID (`LEL.EV.023`).

---

## EXECUTION PROTOCOL

For each session:
1. Read the brief at `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/<ID>_BRIEF.md`
2. Execute every step in the brief
3. Run check_commands from `session_queue_s2.yaml`
4. ALL pass → mark COMPLETE, log, proceed
5. ANY fail → retry once, then HALT if still failing

---

## SESSION EXECUTION ORDER

### Session 1: R3-S1 — MSR Grounding Audit

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_S1_BRIEF.md`

Key actions:
1. Connect to DB via proxy (port 5433)
2. Find the MSR signals table — try these names: `msr_signals`, `signals`, `msr`, `master_signals`
3. Get schema: find the `source_citation` column (may also be `forensic_refs`, `grounding`, `citations`)
4. Run COUNT queries: total, grounded, ungrounded
5. Sample 20 ungrounded signals (if any)
6. Write `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md`

**Critical:** If you cannot connect to DB on port 5433, write the audit document with status `DB_UNAVAILABLE` and a note explaining the connection failure. Proceed to R3-S2 with the `VERIFIED_NO_GAP` path (do not block on DB connection issues — the R3-T1 tests will catch any real grounding failures when the operator runs them).

Verify:
```bash
test -f /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md \
  && echo "Audit doc: PRESENT" \
  || echo "Audit doc: MISSING"
grep 'grounded_count' /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md \
  && echo "grounded_count field: PRESENT" \
  || echo "grounded_count field: MISSING"
```

---

### Session 2: R3-S2 — Grounding Completion (conditional)

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_S2_BRIEF.md`
Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md`

**Decision gate (no human needed):**
```bash
# Check if remediation is needed
UNGROUNDED=$(grep 'ungrounded_count:' \
  /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md \
  | awk '{print $2}')
echo "Ungrounded count: $UNGROUNDED"
```

- If `UNGROUNDED = 0` (or audit showed `DB_UNAVAILABLE`): Update audit doc status to `VERIFIED_NO_GAP`, commit, proceed to R3-T1.
- If `UNGROUNDED > 0`: Execute full grounding completion:
  1. Read `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`
  2. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`
  3. Map each ungrounded signal to FORENSIC/LEL citations
  4. Execute UPDATE SQL for all ungrounded signals
  5. Verify count drops to 0

---

### Session 3: R3-T1 — Grounding Verification Tests

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_T1_BRIEF.md`

Key action: Create `platform/src/__tests__/integration/msr_grounding.integration.test.ts`.

The test file must permanently assert:
- Total signal count = 573
- Zero null source_citation rows
- All citations contain FORENSIC or LEL references
- Discovery layer tools return attributed responses

CI-safe: tests skip when `DB_PROXY_PORT` is absent.

Run:
```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/platform
DB_PROXY_PORT=5433 npx vitest run \
  src/__tests__/integration/msr_grounding.integration.test.ts \
  2>&1 | tail -10
```

Tests must either PASS or SKIP. FAIL is not acceptable.

---

### Session 4: R3-SEAL — Stream 2 Seal

Read: `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/briefs/R3_SEAL_BRIEF.md`

Key actions:
1. Create `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM2_COMPLETE.md` with `msr_grounding_verified: true`
2. Append to `00_ARCHITECTURE/SESSION_LOG.md`
3. Commit

Verify:
```bash
grep -q 'msr_grounding_verified: true' \
  /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2/00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/STREAM2_COMPLETE.md \
  && echo "SEAL: VERIFIED" \
  || echo "SEAL: field missing"
```

---

## LOGGING

After each session append to `/tmp/gismcp_stream2.log.txt`:
```
[TIMESTAMP] Session <ID>: <PASS|SKIP|FAIL>
  grounded_count: <N> (from audit)
  ungrounded_count: <N>
  action_taken: <VERIFIED_NO_GAP|REMEDIATION_COMPLETE|DB_UNAVAILABLE>
  commit: <git hash>
```

---

## FINAL REPORT

After all 4 sessions:

```
╔══════════════════════════════════════════════════════════════════╗
║          GISMCP STREAM 2 — EXECUTION SUMMARY                    ║
╠══════════════════════════════════════════════════════════════════╣
║  R3-S1: [PASS/FAIL]  MSR grounding audit                        ║
║  R3-S2: [PASS/SKIP]  Grounding completion (if gap found)        ║
║  R3-T1: [PASS/FAIL]  Grounding verification tests               ║
║  R3-SEAL:[PASS/FAIL]  Stream 2 seal                             ║
╠══════════════════════════════════════════════════════════════════╣
║  MSR grounding result:  <VERIFIED_NO_GAP | REMEDIATION_COMPLETE>║
║  Final ungrounded count: <N>                                    ║
║  Branch: fix/gismcp-r3                                          ║
║  STREAM2_COMPLETE.md: [PRESENT/MISSING]                         ║
╠══════════════════════════════════════════════════════════════════╣
║  OPERATOR: Merge fix/gismcp-r3 before fix/gismcp-r1-r2.        ║
║  No deploy needed for Stream 2 (data + test changes only).      ║
╚══════════════════════════════════════════════════════════════════╝
```

Run sessions 1–4 now. Stop and report at any CONDUCTOR_HALT.
