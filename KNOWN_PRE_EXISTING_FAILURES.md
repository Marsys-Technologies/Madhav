# Known Pre-Existing Test Failures — Merge Train Baseline

Captured: 2026-05-19T21:12:00Z  
Branch: main @ ccd2aed9ff3420913fcd175e222542ed8f8277a7  
Total pre-existing failures: **21**  
Total passing: varies by run (~2954 per R7 session log)

These failures existed on main BEFORE any R7/R8/R9 merge. Any failure in the post-merge test run that matches this list is background noise, not a regression introduced by the merge train.

---

## Failures

| # | Test Name | File | One-Line Summary | Classification | TODO |
|---|---|---|---|---|---|
| 1 | `renderWithCitations is called with enrichedOnPin (not bare onPin)` | `tests/unit/chat-v2/citation_rich_payload.test.ts` | Test expects enrichedOnPin callback wiring not yet landed on main | appears-broken | TODO: recheck after R7 merge (R7-S4 reworks citation panel) |
| 2 | `renders V2TitleTracker inside runtime` | `tests/unit/chat-v2/sidebar_auto_title_refresh.test.ts` | V2TitleTracker component mount check fails against current ConsumeChatV2 structure | appears-broken | TODO: recheck after R7 merge |
| 3 | `V2TitleTracker subscribes to data-title parts` | `tests/unit/chat-v2/sidebar_auto_title_refresh.test.ts` | data-title subscription not wired per test expectation | appears-broken | TODO: recheck after R7 merge |
| 4 | `V2AssistantText passes data-testid for E2E targeting` | `tests/unit/chat-v2/markdown_render_v2.test.ts` | data-testid attribute not present on component in current shape | appears-broken | TODO: recheck after R7 merge (R7 modifies AssistantMessage/MarkdownContent) |
| 5 | `citation count still computed for drawer badge in V2AssistantText` | `tests/unit/chat-v2/markdown_render_v2.test.ts` | Badge count computation broken in test setup | appears-broken | TODO: recheck after R7 merge |
| 6 | `injects panel_opt_in into transport body and renders PanelModeToggle in composer` | `tests/unit/chat-v2/panel_mode_toggle.test.ts` | PanelModeToggle prop chain not wired | appears-broken | TODO: recheck after R7/R8 merges |
| 7 | `all signals have source_file` | `src/scripts/etl/__tests__/msr_parser.test.ts` | MSR parser signals missing source_file field; likely stale test vs updated MSR schema | appears-broken | TODO: fix in next MSR maintenance session |
| 8 | `renders collapsed by default (no param rows visible)` | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | AIOps component render fails — likely test environment issue (missing mock/provider) | appears-broken | TODO: investigate AIOps test setup |
| 9 | `expands to show all 4 param rows when clicked` | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | Same AIOps test environment issue | appears-broken | TODO: investigate AIOps test setup |
| 10 | `shows all 4 inputs when expanded` | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | Same | appears-broken | TODO: investigate AIOps test setup |
| 11 | `shows reset link when param has current override` | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | Same | appears-broken | TODO: investigate AIOps test setup |
| 12 | `does not show reset link when param uses default (no override)` | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | Same | appears-broken | TODO: investigate AIOps test setup |
| 13 | `shows current override value in label when set` | `src/lib/components/aiops/__tests__/ParamOverrideRow.test.tsx` | Same | appears-broken | TODO: investigate AIOps test setup |
| 14 | `renders the target stack name` | `src/lib/components/aiops/__tests__/CostConfirmDialog.test.tsx` | AIOps dialog render issue — likely test environment | appears-broken | TODO: investigate AIOps test setup |
| 15 | `calls onConfirm when Confirm button clicked` | `src/lib/components/aiops/__tests__/CostConfirmDialog.test.tsx` | Same | appears-broken | TODO: investigate AIOps test setup |
| 16 | `renders the three pills with the right counts` | `tests/consume/PostAnswerProvenance.test.tsx` | Provenance pill counts mismatch current component | appears-broken | TODO: recheck after R7 merge (R7 modifies ConsumeChatV2) |
| 17 | `astrological tab has no internal-jargon labels visible` | `tests/consume/PostAnswerProvenance.test.tsx` | Label visibility assertion broken | appears-broken | TODO: recheck after R7 merge |
| 18 | `renders each audit row action` | `src/lib/components/aiops/__tests__/AuditRail.test.tsx` | AIOps AuditRail render issue | appears-broken | TODO: investigate AIOps test setup |
| 19 | `renders a green arrow for positive delta` | `src/components/performance/__tests__/KpiTile.test.tsx` | KpiTile arrow rendering assertion mismatch | appears-broken | TODO: investigate KpiTile test fixture |
| 20 | `renders a red arrow for negative delta` | `src/components/performance/__tests__/KpiTile.test.tsx` | Same | appears-broken | TODO: investigate KpiTile test fixture |
| 21 | `collapsed strip does NOT contain bg-zinc-950` | `tests/component/chat-v2/r5/sidebar-background.test.tsx` | CSS class assertion stale vs current sidebar implementation | appears-broken | TODO: recheck after R8 merge (R8 modifies ConversationSidebarV2) |

---

## Failure Clusters

- **AIOps test environment (7 failures):** ParamOverrideRow (6) + CostConfirmDialog (2) + AuditRail (1) = 9 AIOps failures. Likely a shared test setup issue (missing mock/provider for AIOps context).
- **Chat V2 stale test expectations (9 failures):** citation_rich_payload, sidebar_auto_title_refresh, markdown_render_v2, panel_mode_toggle, PostAnswerProvenance, sidebar-background. Tests written against an older component shape that R7/R8 are actively updating.
- **MSR parser (1 failure):** Stale schema expectation.
- **KpiTile (2 failures):** CSS/DOM assertion mismatch.

---

*Authored by merge-train conductor. Not under regular governance; informational record only.*
