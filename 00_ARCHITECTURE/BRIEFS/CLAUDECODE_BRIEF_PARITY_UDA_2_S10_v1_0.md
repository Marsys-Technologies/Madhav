---
session_id: UDA-2-S10
phase: UDA-2
title: "CAPABILITY_MANIFEST — 14 tools channel:both + holistic_bundle update"
status: pending
---

# UDA-2-S10: CAPABILITY_MANIFEST + holistic_bundle

## Goal
Update CAPABILITY_MANIFEST.json to reflect that all 14 UDA-2 tools are now available
on both channels. Update holistic_bundle to be aware of the new tools.

## Steps

1. Update `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`:
   Find each of the following 14 tool entries by `name` and change `"channel": "portal"` to `"channel": "both"`:
   - msr_sql, temporal, kp_query, query_kp_ruling_planets
   - pattern_register, resonance_register, cluster_atlas, contradiction_register
   - query_ucn_walk, query_cdlm_lookup, query_rm_walk, query_jaimini_drishti
   - timeline_query, query_signal_state
   
   Validate JSON after editing:
   ```bash
   python3 -c "import json; json.load(open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json')); print('JSON valid')"
   ```

2. Update `platform-mcp/src/tools/holistic_bundle_tool.ts`:
   - Find the tool list / coverage comment that describes what holistic_bundle draws from
   - Add a note that the 14 new UDA-2 tools are now available as supplementary surgical tools
   - Do NOT change the bundle's actual computation — just update the description/coverage comment

3. Commit:
   ```bash
   git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json platform-mcp/src/tools/holistic_bundle_tool.ts
   git commit -m "governance(mcp): UDA-2-S10 — CAPABILITY_MANIFEST 14 tools channel:both + holistic_bundle note"
   ```

## Acceptance criteria
- JSON valid
- All 14 tool entries show channel: both
- `python3 -c "..."` prints JSON valid
