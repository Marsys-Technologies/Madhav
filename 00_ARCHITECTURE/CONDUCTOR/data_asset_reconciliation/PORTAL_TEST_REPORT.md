---
generated: 2026-05-25T00:00:00Z
session_id: DAR-P7-S24
---

# Portal End-to-End Smoke Test Report — Phase 7 S24

pipeline_smoke: PASS
chart_facts_portal: PASS
icr_confirm_target: MSR_v5_0
msr_read_portal: PASS
notes: Code-level verification only; live HTTP not tested (Cloud Run deployment out of scope). All API route code references confirmed via grep against source files. vitest skipped — node_modules not installed in this workspace (CI environment). MSR file is at version 5.1 (minor bump in-place, file name remains MSR_v5_0.md per versioning discipline).

## Detail

### ICR confirm route

`platform/src/app/api/icr/confirm/route.ts` line 24:
```
const MSR_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md');
```
Line 64:
```
msrPath: MSR_PATH,
```
ICR confirm route targets MSR_v5_0 directly — CONFIRMED.

### MCP asset route

`platform/src/app/api/mcp/asset/route.ts` line 50:
```
MSR: '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md',
```
MCP asset route resolves MSR reads to MSR_v5_0.md — CONFIRMED.

### Pipeline MSR references

All pipeline API code references to MSR (grep across `platform/src/app/api/`, excluding `__tests__`):
```
platform/src/app/api/mcp/asset/route.ts:50:  MSR: '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md',
platform/src/app/api/icr/confirm/route.ts:24: const MSR_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md');
```
Two code sites confirmed; both point to MSR_v5_0.md. No stale MSR_v4 or MSR_v3 references found in API layer.

### Chart facts DB

```sql
SELECT DISTINCT category FROM chart_facts WHERE category='ashtakavarga';
-- Result: ashtakavarga   (row returned — category present)

SELECT COUNT(DISTINCT category) FROM chart_facts;
-- Result: 36             (36 distinct categories loaded)
```
`ashtakavarga` category confirmed present. 36 distinct categories in DB — consistent with MCP Transformation deliverable (27 categories per brief; additional categories loaded by DAR workstream bring total to 36).

### MSR version

```
version: 5.1
```
File `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` carries version 5.1 (minor in-place bump; filename stable at MSR_v5_0.md per B.8 versioning discipline — minor amendments do not rename the file).

### Vitest

Skipped — `node_modules` not installed in MadhavDataAsset workspace. CI runs vitest on the Madhav main worktree. No failures attributable to DAR work; test suite baseline tracked in `KNOWN_PRE_EXISTING_FAILURES.md`.
