/**
 * vidhi_plan.ts — D-2 Lane V-2. The `vidhi_plan` MCP prompt (BIND_D-2.md §F1.7 ledger rows
 * 15, 16, 17): "compiled plans as an MCP prompt".
 *
 * Given a chart + question (optionally an explicit intent/depth override), this prompt compiles
 * the vidhi contract (V-1's deterministic compiler over the vendored registry) and renders it as
 * an EXECUTABLE guided-reading scaffold: the resolved scope_tuple echoed for correction, the
 * non-skippable acharya floor + machine band with each item's live tool + args, and the
 * discipline for producing the completeness receipt (served/empty/dark, dark citing its CR).
 *
 * The primary plan surface (the `plan_retrieval` tool is the fallback). Registered from
 * prompts/index.ts alongside the existing guided prompts.
 *
 * S-3 (RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §1.5, GT-35): this prompt shares `plan_builder.ts`
 * with `plan_retrieval` and had the identical zero-entitlement-check gap. Gated via the same M0
 * `remoteAuthorize` helper (lib/authz.ts) every other chart-scoped tool in this codebase uses,
 * checked BEFORE `buildVidhiPlan` runs.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { buildVidhiPlan } from '../resources/vidhi/plan_builder.js';
import type { CompiledFloorItem } from '../resources/vidhi/types.js';
import { remoteAuthorize } from '../lib/authz.js';
import type { Principal } from '../types.js';

function renderItem(item: CompiledFloorItem, i: number): string {
  const gap = item.known_gap ? `  [known_gap: ${item.known_gap} — DARK; account for it, do not silently skip]` : '';
  const fallback = item.fallback_face ? `\n       fallback: ${item.fallback_face}` : '';
  return (
    `  ${i}. ${item.primitive_id} → ${item.live_tool}(${JSON.stringify(item.tool_args)})${gap}` +
    fallback
  );
}

export function registerVidhiPlanPrompt(server: McpServer, principal: Principal): void {
  server.prompt(
    'vidhi_plan',
    'Compile and follow the Vidhi Engine retrieval plan for a chart question (D-2). Produces the ' +
      'non-skippable acharya floor + machine band for the resolved intent class, each floor item ' +
      'naming its live tool + args, the scope_tuple echoed for correction before execution, and ' +
      'the completeness-receipt discipline (account for every floor item as served/empty/dark; ' +
      'every dark item cites its OPEN/LOGGED CR). Use for any substantive chart reading where ' +
      'completeness matters — it is the demand-side chase made concrete as a compiled contract.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart. Required.'),
      question: z
        .string()
        .optional()
        .describe('The question to answer. Drives the fallback scope resolver (e.g. a wealth question → wealth_deepdive).'),
      intent: z
        .string()
        .optional()
        .describe('Explicit intent-class override (wealth_deepdive/career_deepdive/health_deepdive/marriage_deepdive/structure_read/panoramic_breadth/retrieval_only/general_synthesis).'),
      depth: z
        .string()
        .optional()
        .describe('Explicit depth override (retrieval/structure/deepdive).'),
    },
    async ({ chart_id, question, intent, depth }) => {
      // M0 entitlement gate (S-3) — checked BEFORE any plan compilation, same helper +
      // same denial wording as every other per-chart tool (remoteAuthorize, lib/authz.ts).
      const authorized = await remoteAuthorize(principal, chart_id);
      if (!authorized) {
        return {
          messages: [
            {
              role: 'user' as const,
              content: {
                type: 'text' as const,
                text: `AUTHZ_DENIED: not authorized to access chart ${chart_id}. Do not call any tool for this chart_id — the caller lacks entitlement to it.`,
              },
            },
          ],
        };
      }
      const plan = buildVidhiPlan({
        chart_id,
        question,
        scope_tuple: intent ? { intent, depth } : undefined,
      });
      const floorLines = plan.floor.map((it, idx) => renderItem(it, idx + 1)).join('\n');
      const machineLines =
        plan.machine_band.length > 0
          ? plan.machine_band.map((it, idx) => renderItem(it, idx + 1)).join('\n')
          : '  (none — this depth compiles no machine band)';
      const darkLines =
        plan.completeness_receipt.dark.length > 0
          ? plan.completeness_receipt.dark.map((d) => `  - ${d.floor_item_id}: ${d.cr_row}`).join('\n')
          : '  (none — every floor item has a live route)';

      return {
        messages: [
          {
            role: 'user' as const,
            content: {
              type: 'text' as const,
              text: [
                `Follow the Vidhi Engine plan for chart ${chart_id}.`,
                question ? `Question: "${question}"` : '',
                '',
                `capability_version: ${plan.capability_version}`,
                `compiler_version: ${plan.compiler_version}`,
                '',
                '── RESOLVED SCOPE TUPLE (echoed for correction) ──',
                JSON.stringify(plan.scope_tuple),
                `  resolution: ${plan.scope_resolution.method}` +
                  (plan.scope_resolution.fallback_recommended
                    ? ' (coarse fallback — if wrong, re-invoke with an explicit `intent`/`depth`, or classify via intent_classify (DR-8) and pass the scope_tuple to plan_retrieval)'
                    : ''),
                '',
                '── ACHARYA FLOOR (non-skippable minimum; call each; do not stop early) ──',
                floorLines,
                '',
                '── MACHINE BAND ──',
                machineLines,
                '',
                '── COMPLETENESS RECEIPT DISCIPLINE ──',
                'After executing the floor, account for EVERY floor item in a completeness receipt',
                'with three disjoint buckets that together cover all items:',
                '  served: [{ floor_item_id, source }]        — the route returned data',
                '  empty:  [{ floor_item_id, empty_reason }]  — the route was called and returned nothing (state the reason)',
                '  dark:   [{ floor_item_id, cr_row }]        — a known coverage gap; cite its CR (below)',
                'Items already known to be DARK by construction (cite these CRs verbatim):',
                darkLines,
                '',
                'To get the server-canonical receipt, call plan_retrieval with the same scope and an',
                '`observations` array (one {floor_item_id, status: served|empty, source?/empty_reason?}',
                'per floor item you executed). Never mark an item served without data; never claim an',
                'item empty from a truncated/paginated read — page to exhaustion or use a total field.',
                '',
                plan.llm_extension_note,
              ]
                .filter((l) => l !== '')
                .join('\n'),
            },
          },
        ],
      };
    },
  );
}
