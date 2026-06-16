---
artifact: CLAUDECODE_BRIEF_MCPT_V310_S3_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
session_id: v3.1.0-S3
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN
branch: feature/mcpt-foundation
depends_on: [v3.1.0-S1]
parallel_with: [v3.1.0-S2, v3.1.0-S4]
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: 5 MCP resources + tool-description regeneration; tier-conditioned content
---

# v3.1.0-S3 — Resources + Tool Description Regeneration

You are a Claude Code sub-agent on WT-A. Implements the **5 resources** Claude auto-loads at session attach (per arch §4) and finalizes tool-description regeneration started in S1. Runs in parallel with S2 and S4 inside WT-A.

Read: `MCP_ARCH_v3_PROPOSAL_2026-05-22.md §4 (resources), §6 (tier model)`; `MCP_PERF_SYSTEM_BRIEF_2026-05-22.md §6.3 (capabilities resource structure)`; parent brief §4 / v3.1.0-S3.

## §1 — Scope

Implement 5 resources, tier-conditioned per §4 of arch. Resources auto-load at session attach.

| URI | File | Tier conditioning |
|---|---|---|
| `marsys://chart-snapshot` | `platform-mcp/src/resources/chart_snapshot.ts` | All tiers; client glosses Sanskrit inline |
| `marsys://chart-overview` | `platform-mcp/src/resources/chart_overview.ts` | super_admin full; acharya full minus internal-audit; client compact |
| `marsys://house-rules` | `platform-mcp/src/resources/house_rules.ts` + variants under `house_rules_variants/{tier}.md` | tier-specific files |
| `marsys://capabilities` | `platform-mcp/src/resources/capabilities.ts` | super_admin + acharya full; client tool names only (this S3 emits a PLACEHOLDER that S4 wires to real perf views) |
| `marsys://school-conventions` | `platform-mcp/src/resources/school_conventions.ts` | uniform across tiers |

Plus: regenerate every MCP tool's description from a single source via the `description_builder.ts` helper landed in S1.

## §2 — Files in scope

```
platform-mcp/src/resources/chart_snapshot.ts                             # new
platform-mcp/src/resources/chart_overview.ts                             # rewrite
platform-mcp/src/resources/house_rules.ts                                # rewrite
platform-mcp/src/resources/house_rules_variants/super_admin.md           # new content
platform-mcp/src/resources/house_rules_variants/acharya.md               # new content
platform-mcp/src/resources/house_rules_variants/client.md                # new content
platform-mcp/src/resources/house_rules_variants/public_redacted.md       # new (authored, unused)
platform-mcp/src/resources/capabilities.ts                               # PLACEHOLDER for S4 to fill
platform-mcp/src/resources/school_conventions.ts                         # new content
platform-mcp/src/resources/index.ts                                      # register all 5
platform-mcp/src/tools/*.ts                                              # regenerate descriptions via S1 helper (already in scope from S1 work; finalize)
platform-mcp/test/resources/*.test.ts                                    # new tests
```

## §3 — Files NOT in scope

```
platform-mcp/src/bundles/**                                              # S2 territory
platform/src/lib/perf/**, platform/src/app/api/mcp/health/**             # S4 territory
platform/src/app/admin/mcp/health/**                                     # S5 territory
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**                             # FORENSIC + L2.5 untouched
```

## §4 — Per-resource content specification

### `chart-snapshot` (structured L1, ~2.5k tokens, NEW in v3.1)

Generated from `chart_facts` table at attach time. Structure (markdown):

```markdown
# MARSYS-JIS Chart Snapshot (auto-generated, last refresh: <timestamp>)

## Lagna
- Sign: <sign> | Degree: <deg> | Lord: <planet> | State: <dignity> | Nakshatra: <nak> | Nak-Lord: <planet>

## Planetary positions (D1)
| Planet | House | Sign | Degree | Dignity | Nakshatra | Nak-Lord | Retro? |
|---|---|---|---|---|---|---|---|
| Sun | 6 | Magha | 23.45° | Friend's | Magha | Ketu | — |
| ... |

## Karakas (Jaimini, D1)
- Atmakaraka: <planet> (Moon at <deg>)
- Amatyakaraka: ...
- ...

## Active dasha (Vimshottari)
- Maha: <planet>, ends <date>
- Antar: <planet>, ends <date>
- Pratyantar: <planet>, ends <date>

## Current transit highlights (top 5 by significance)
- ... per query_transit_event(...)

## Current panchang (now)
- Tithi, Vara, Nakshatra, Yoga, Karana
```

No prose synthesis. Pure facts. Resource generator reads `chart_facts` + `query_dasha_periods(active_only:true)` + `query_panchanga(today)` + `query_transit_event(now)` at attach time.

### `chart-overview` (synthesis, ~3k super_admin/acharya / ~800 client)

Top 5 themes from MSR (highest-significance), top 2 contradictions from CDLM, operational anchor per CGM, current life-phase per LEL. Tier-specific length.

### `house-rules` (tier-conditioned per variant file)

Authored as 4 markdown files (`super_admin.md`, `acharya.md`, `client.md`, `public_redacted.md`). Each ~3k tokens. Content per arch §7 governance rules + tier-template specifications from arch §6. The super_admin variant explicitly documents:
- Strict cite-allowlist contract (cite only from `provenance.signal_ids_available[]`)
- B.11 floor instruction (consult ≥1 L2.5 tool before non-factual)
- PPL discipline (call `log_prediction` for every forward-looking claim)
- When to use bundles vs primitives
- Audit subsystem behavior (operator-side; not self-audit)
- Per-tier output template specs

### `capabilities` (PLACEHOLDER in S3; S4 wires real data)

Structure per perf brief §6.3. In S3, ship a working generator that returns hardcoded tool descriptions + "perf data pending S4 wiring" note. S4 will replace the hardcoded section with `tool_health()` + `data_coverage()` calls.

### `school-conventions` (static reference, ~2.5k tokens)

Static markdown listing the 4 schools (Parashara / Jaimini / KP / Tajaka), what each is authoritative for, output-form differences, known disagreements, classical anchors. Hand-authored once; rarely changes.

## §5 — Tool description regeneration

For every tool in `platform-mcp/src/tools/*.ts`, call the `buildToolDescription` helper from S1 with `enumSource` pointing to the underlying retrieval enum/registry and `coverageHint` derived from the (not-yet-real) coverage data — for S3, use a static stub; S4 will rewire to real coverage.

## §6 — Acceptance criteria (AC.S3.1 through AC.S3.6)

Per parent brief §4 / v3.1.0-S3.

## §7 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  test -f platform-mcp/src/resources/chart_snapshot.ts && \
  test -f platform-mcp/src/resources/chart_overview.ts && \
  test -f platform-mcp/src/resources/house_rules.ts && \
  test -f platform-mcp/src/resources/capabilities.ts && \
  test -f platform-mcp/src/resources/school_conventions.ts && \
  test -f platform-mcp/src/resources/house_rules_variants/super_admin.md && \
  test -f platform-mcp/src/resources/house_rules_variants/acharya.md && \
  test -f platform-mcp/src/resources/house_rules_variants/client.md && \
  test -f platform-mcp/src/resources/house_rules_variants/public_redacted.md && \
  cd platform-mcp && npm test -- resources/ 2>&1 | tail -10
```

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V310_S3_CLOSE.md`. Body: final house-rules variants attached as appendices, resource sizes in tokens, registration evidence.

---

*End of CLAUDECODE_BRIEF_MCPT_V310_S3_v1_0.md.*
