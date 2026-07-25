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
import {
  COMPOSITION_SEQUENCE,
  MANDATORY_GESTALT_VOLUNTEER,
} from '../resources/vidhi/composition_doctrine.js';

/**
 * EL-61 + EL-29 + EL-05 (Elevation Campaign v2.1, Lane I). For a DEEPDIVE plan, the floor is the
 * gather stage; the compose stage is Ω5's `dossier` gather-then-compose gate. This block wires the
 * plan to that gate: it names the dossier handle to page the domain's ENTIRE slice, the STRUCTURAL
 * rule (do not compose until synthesis_gate: OPEN), and the EL-29 composition SEQUENCE the reading
 * follows once OPEN — stage 1 of which is the mandatory EL-05 top-N gestalt volunteering. Pure
 * doctrine text over the vendored composition_doctrine constants; it does not call dossier here
 * (that is the consumer's runtime move) and reimplements no computation (B.10).
 */
function gatherThenComposeBlock(domain: string): string[] {
  const seq = COMPOSITION_SEQUENCE.map((s, i) => `${i + 1}. ${s}`).join(' → ');
  const gestaltTools = MANDATORY_GESTALT_VOLUNTEER.serving_tools.map((t) => t.tool).join(', ');
  return [
    '── GATHER-THEN-COMPOSE (Ω5 dossier · EL-61) ──',
    'The floor above is the GATHER stage. For a full composed reading, page the whole domain',
    `slice through the Ω5 gate before composing: dossier({ domain: "${domain}", chart_id }).`,
    'Follow its `cursor` to exhaustion. The interpretive surfaces are WITHHELD by construction',
    'until synthesis_gate reads OPEN (100% accounted) — this is a STRUCTURAL gate, not advice.',
    'Do NOT compose from page 1; a premature composition is visibly missing its scaffold.',
    '',
    '── COMPOSITION SEQUENCE (EL-29; only once synthesis_gate: OPEN) ──',
    `Compose in this fixed order: ${seq}.`,
    `  • gestalt (stage 1) is MANDATORY and served UNPROMPTED (EL-05): open with the chart's own`,
    `    top-${MANDATORY_GESTALT_VOLUNTEER.top_n} laksana/gestalt findings via ${gestaltTools}`,
    '    — orient on who the chart IS before answering the question.',
    '  • tensions are ADJUDICATED, not just listed; carry cross-ayanamsha agreement (n/5) as a',
    '    confidence discount where a finding is ayanamsha-fragile (EL-27).',
    'The deliverable is the synthesis over the WHOLE slice — not a narration of the parts.',
  ];
}

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

      // EL-61/EL-29/EL-05: attach the gather-then-compose + composition doctrine for a deepdive
      // plan (the depth at which a full composed reading — not a lookup — is the deliverable).
      const st = plan.scope_tuple as { depth?: string; domains?: readonly string[] };
      const composeDomain = st.domains?.[0] ?? 'general';
      const composeLines = st.depth === 'deepdive' ? gatherThenComposeBlock(composeDomain) : [];

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
                ...(composeLines.length > 0 ? ['', ...composeLines] : []),
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
