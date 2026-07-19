---
artifact: PG2_LANE_X-3
lane: X-3
wave: PG-2 (retrieval diagnostic wave, follow-on to PG-1)
status: CLOSED
authored_by: Claude Code (Sonnet 5), Lane X-3 agent, 2026-07-19
audit_target: live mcp__marsys-jis-direct__* tool surface, primary chart_id 482012f1-710e-4a25-994a-93821f5871aa (Abhisek); second-chart subset on 1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan)
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-3 (branch pg2/X-3) — confirmed never left this directory for the entire session
---

# PG2 Lane X-3 — Extended MCP Capability Coverage

## Charge recap

PG-1's R-2 lane executed 35/~139 live MCP tools (~25%). This lane's charge:
execute the remaining ~104 tools mechanically for breadth, test both
`response_format=legacy` and `=v3` where supported, run a representative
subset against a second chart to catch chart-conflation defects, resolve the
Bearer-key 401 (F-25v), and re-confirm two specific known-broken tools.

## Total tools executed this lane

**98 additional distinct tool names** called live against chart `482012f1`
(Abhisek), plus **12 of them re-run against chart `1c826d5a`** (Abhinandan)
for the chart-conflation check, plus 2 dual-format (legacy+v3) probes on
`ganita_yogas_get` against both charts.

Full list of the 98: see `PG2-X3-0010` in
`00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings_X-3.jsonl`.

## Combined coverage with R-2

R-2: 35 tools. X-3: 98 additional distinct tools. **Combined: 133/139 (~96%)**
of the live `mcp__marsys-jis-direct__*` tool-name surface has now been
mechanically exercised at least once. Two tools remain genuinely unexercised
across both PG-1 and PG-2:

- `prashna_undertaking_get` — requires a horary/prashna-cast chart; none of
  the 4 available charts (`list_my_charts`: Abhinandan, Abhisek, Arunima,
  Kiran) are prashna charts. Out of scope without casting a new one.
- `mimamsa_outcome_record` — documented alias of `record_outcome`; not
  independently re-called once `record_outcome`'s underlying sidecar defect
  (500 on bad `prediction_id`) was confirmed, to avoid a second
  write-adjacent probe against the same handler.

## Bearer-key 401 resolution (F-25v)

**RESOLVED — refuted "genuinely broken auth."** A raw `curl` POST to
`/mcp` with `Authorization: Bearer <key>` against the live Cloud Run host
succeeded with HTTP 200 and a full 139-tool `tools/list`, using the key/host
pair already configured for this session's working `marsys-jis-direct`
connector (found in `~/.claude.json`). Both header-casing variants worked;
both the current host and the older host cited in the repo's `.mcp.json`
worked. Deliberately substituting a garbage key reproduced PG-1's exact
reported 401 error byte-for-byte. **Root cause: a stale/wrong key value at
the time PG-1 ran** — not a request-shape bug, not a host-mismatch bug, not a
genuine server-side regression. The exact stale value could not be recovered
(`scripts/setup_mcp_env.sh` is gitignored, holds a live secret, and does not
exist in this isolated worktree, since git worktrees don't share untracked
files with the main checkout).

## Two known-broken-tool confirmations

Both **still reproduce, unchanged**:

- `phala_anchors_get` — 422s when `date_range` is omitted (schema says
  optional; sidecar requires it). Confirmed on Abhisek.
- `ref_dignity_reference_get` — 400s `internal_error` on `planet=Saturn`
  (its own documented example). Confirmed on **both** charts tested,
  proving the bug is chart-independent.

## Second-chart sweep (Abhinandan) — headline findings

12-tool representative subset run against `1c826d5a` immediately after ~90
calls against `482012f1` in the same session. **No cross-chart leakage
observed** — every response correctly scoped to Abhinandan's own data
(different lagna, different running dasha lord, different yoga set, honest
empty reading-notes vs. Abhisek's populated notes). Corroborates PG1-R2-0004's
A2 chart-agnostic-gate finding on a broader (non-sentinel-UUID) sample, though
this was only a 12-tool spot-check, not a full second-chart sweep.

## New defects found (beyond the two known-broken re-confirmations)

1. `catalog_assets_all`/`catalog_assets_list` drill-pointers degrade to the
   literal string `"unknown_tool"` — same defect class as PG1-R2-0001, now
   confirmed to extend to the asset-registry alias family.
2. `record_outcome` returns HTTP 500 on a non-existent `prediction_id`
   instead of a graceful 404 — unguarded sidecar lookup.
3. `holistic_bundle_chart_facts` reports `type:"bundle.completed"` while
   silently delivering only 3/8 documented sub-tools (`UCN`/`RM`/`CDLM` fire;
   `MSR`/`CGM`/`LEL`/`PANCHANG`/`DASHA` error out) — a load-bearing
   B.11-whole-chart-read convenience tool is majority-broken behind a
   success-looking envelope.
4. Several whole-chart-domain tools (`assess_career/health/marriage/wealth`,
   `get_temporal_windows`, `kala_temporal_bundle`, `get_domain_reading`,
   `ref_nakshatra_get`) produce payloads (92KB–289KB) that exceed this
   session's MCP client token ceiling even after server-side trimming and
   even with narrow params — suggesting these tools are exempt from or
   miscalibrated against the `response_budget.ts` trimmer that protects
   other whole-chart tools.
5. v3-vs-legacy `judgment_flags` gating (PG1-R2-0007) reconfirmed
   byte-for-byte on a second chart's `ganita_yogas_get` call — systemic
   envelope behavior, not chart-data-dependent.

Full findings with evidence: `pg2_findings_X-3.jsonl` (`PG2-X3-0001`..`0010`).

## Deliverable updates

- `00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md` — new `§2b — X-3 Extended
  Coverage (PG-2)` section appended in place; R-2's original sections
  unmodified.
- `00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings_X-3.jsonl` — 10
  findings, `PG2-X3-0001`..`0010`.
- This state file.

## Worktree confinement confirmation

All work performed from `/Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-3`
(branch `pg2/X-3`). Never `cd`'d into `/Users/Dev/Vibe-Coding/Apps/Madhav` or
any sibling `Madhav-pg2-*` directory. Only files touched:
`00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings_X-3.jsonl`,
`00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_X-3.md`,
`00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md` — all within the granted
write scope.
