---
session_id: UDA-2-S4
phase: UDA-2
title: "MCP wrappers — pattern_register + resonance_register"
status: pending
---

# UDA-2-S4: MCP Wrappers — pattern_register + resonance_register

## Goal
Create MCP tool wrappers for the two L2.5 register tools.

## Context
- `platform/src/lib/retrieve/pattern_register.ts` (TOOL_NAME='pattern_register') — reads
  PATTERN_REGISTER JSON from 035_DISCOVERY_LAYER/REGISTERS/. Filters by domain, confidence.
  
- `platform/src/lib/retrieve/resonance_register.ts` (TOOL_NAME='resonance_register') — reads
  RESONANCE_REGISTER JSON. Similar filter structure to pattern_register.

Read both portal sources to derive the exact input interfaces.

## Steps

1. Create `platform-mcp/src/tools/pattern_register.ts`:
   - Input schema: domain? (string), keyword? (string), min_confidence? (0.0–1.0),
     limit? (1–200, default 50)
   - registerPatternRegister calls callPlatformPrimitive('pattern_register', args, principal)

2. Create `platform-mcp/src/tools/resonance_register.ts`:
   - Same input shape as pattern_register (read portal source to confirm)
   - registerResonanceRegister calls callPlatformPrimitive('resonance_register', args, principal)

3. Register both in server.ts. Update tool count +2.

4. Write tests for both.

5. Commit:
   ```bash
   git add platform-mcp/src/tools/pattern_register.ts platform-mcp/src/tools/pattern_register.test.ts \
     platform-mcp/src/tools/resonance_register.ts platform-mcp/src/tools/resonance_register.test.ts \
     platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S4 — pattern_register + resonance_register MCP wrappers"
   ```

## Acceptance criteria
- Both files exist, both registered in server.ts, tsc exits 0
