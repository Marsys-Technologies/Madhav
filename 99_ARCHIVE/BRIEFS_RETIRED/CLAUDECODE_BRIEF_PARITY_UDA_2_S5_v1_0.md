---
session_id: UDA-2-S5
phase: UDA-2
title: "MCP wrappers — cluster_atlas + contradiction_register"
status: pending
---

# UDA-2-S5: MCP Wrappers — cluster_atlas + contradiction_register

## Goal
Create MCP tool wrappers for the two L2.5 meta-structure tools.

## Context
- `platform/src/lib/retrieve/cluster_atlas.ts` (TOOL_NAME='cluster_atlas') — reads
  CLUSTER_ATLAS JSON from 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json.
  ClusterEntry has: cluster_id, cluster_label, dominant_domain, sub_domains[], signal_ids[],
  cluster_size_n. Filters by domain.

- `platform/src/lib/retrieve/contradiction_register.ts` (TOOL_NAME='contradiction_register') —
  reads CONTRADICTION_REGISTER JSON. ContradictionEntry has: contradiction_id,
  contradiction_class, hypothesis_text, domains_implicated[].

Read both portal sources to confirm input interfaces.

## Steps

1. Create `platform-mcp/src/tools/cluster_atlas.ts`:
   - Input: domain? (string), sub_domain? (string), min_size? (int), limit? (1–100, default 20)
   - registerClusterAtlas calls callPlatformPrimitive('cluster_atlas', args, principal)

2. Create `platform-mcp/src/tools/contradiction_register.ts`:
   - Input: domain? (string), contradiction_class? (string), limit? (1–100, default 20)
   - registerContradictionRegister calls callPlatformPrimitive('contradiction_register', args, principal)

3. Register both in server.ts. Update tool count +2.

4. Write tests for both.

5. Commit:
   ```bash
   git add platform-mcp/src/tools/cluster_atlas.ts platform-mcp/src/tools/cluster_atlas.test.ts \
     platform-mcp/src/tools/contradiction_register.ts platform-mcp/src/tools/contradiction_register.test.ts \
     platform-mcp/src/server.ts
   git commit -m "feat(mcp): UDA-2-S5 — cluster_atlas + contradiction_register MCP wrappers"
   ```

## Acceptance criteria
- Both files exist, both registered in server.ts, tsc exits 0
