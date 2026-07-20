/**
 * register_vidhi_plan.ts — D-2 Lane V-2. The `plan_retrieval` meta-tool + capability staleness
 * kill (BIND_D-2.md §F1.7 ledger rows 15, 16, 17, 18).
 *
 * `plan_retrieval` is the fallback path to a compiled vidhi plan (the primary path is the
 * `vidhi_plan` MCP prompt). Given a question and/or a DR-8 scope tuple, it returns:
 *   - the resolved + echoed scope_tuple (row 16), for correction before execution;
 *   - the compiled floor + machine band (row 15);
 *   - a completeness receipt (served/empty/dark per floor item; dark cites its CR — row 17);
 *   - the served capability_version (row 18).
 *
 * Staleness kill (row 18): a caller may pass its cached `client_capability_version`. When that
 * no longer matches the live version, the response carries `capability_stale: true` and a
 * `notifications/tools/list_changed` is emitted on this request's server so a compliant host
 * re-fetches the tool/resource/prompt list. (The server is stateless-per-request — server.ts —
 * so this per-request comparison IS the staleness signal.)
 *
 * A NEW, self-contained file (own helpers, no shared imports from other register_*.ts) per
 * this lane's `may_touch` glob (`register_vidhi*.ts`) and the anti-collision discipline the
 * other register_*.ts files follow. `lib/authz.ts` is a shared M0 helper (not a register_*.ts
 * file), same import every other chart-scoped tool in this codebase uses — see S-3 fix below.
 *
 * S-3 (RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §1.5, GT-35): `plan_retrieval` used to compile a
 * plan for ANY chart_id with zero authorize/entitle hits. Gated now via the same M0
 * `remoteAuthorize` helper every other per-chart tool uses (e.g. phala_outlook.ts,
 * mimamsa_lel_intake.ts, register_gochara_windows.ts) — checked BEFORE `buildVidhiPlan` runs.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { buildVidhiPlan } from '../resources/vidhi/plan_builder.js';
import { notifyIfCapabilityStale } from '../resources/vidhi/capability_version.js';
import { remoteAuthorize } from '../lib/authz.js';
import type { Principal } from '../types.js';
import { budgetMcpContent } from '../lib/response_budget.js';

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000;

// W3-L5 (budget unification): route through the shared auto-detect budget mechanism
// keyed off the `tool` field this file's handler stamps on every response.
function dualOutput(data: unknown, isError = false) {
  let finalData = data;
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>;
    const toolName = typeof obj['tool'] === 'string' ? obj['tool'] : 'unknown_tool';
    finalData = budgetMcpContent(obj, toolName);
  }
  const structuredContent = { type: 'object' as const, object: finalData };
  const json = JSON.stringify(finalData);
  const content =
    Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES
      ? [{ type: 'text' as const, text: '[large payload — see structuredContent]' }]
      : [{ type: 'text' as const, text: json }];
  return isError ? { structuredContent, content, isError: true as const } : { structuredContent, content };
}

/** DR-8 scope_tuple shape (from intent_classify) — all fields optional so a caller may pass a partial. */
const scopeTupleSchema = z
  .object({
    intent: z.string().optional(),
    domains: z.array(z.string()).optional(),
    width: z.string().optional(),
    depth: z.string().optional(),
    horizon: z.string().optional(),
    intervention: z.boolean().optional(),
    entitlement: z.string().optional(),
  })
  .optional();

const observationSchema = z
  .array(
    z.object({
      floor_item_id: z.string(),
      status: z.enum(['served', 'empty']),
      source: z.string().optional(),
      empty_reason: z.string().optional(),
    }),
  )
  .optional();

export function registerVidhiPlanTool(server: McpServer, principal: Principal): void {
  server.tool(
    'plan_retrieval',
    'Vidhi Engine (D-2): compile a retrieval PLAN for a chart question. Returns the resolved ' +
      'scope_tuple (echoed for correction before you execute), the non-skippable acharya floor + ' +
      'machine band (each item names its live tool + args), a completeness receipt (served/empty/' +
      'dark per floor item — every dark item cites the OPEN/LOGGED CR that makes it a known gap), ' +
      'and the capability_version. Pass a scope_tuple from intent_classify (DR-8) for an ' +
      'authoritative classification; otherwise a coarse keyword fallback resolves one (e.g. a ' +
      'wealth question → wealth_deepdive). This is the fallback path; the `vidhi_plan` prompt is ' +
      'the primary one.',
    {
      chart_id: z.string().uuid().describe('UUID of the chart to plan retrieval for. Required.'),
      question: z
        .string()
        .optional()
        .describe('The natural-language question. Used by the fallback resolver when no scope_tuple is given.'),
      scope_tuple: scopeTupleSchema.describe(
        'Pre-classified DR-8 scope tuple {intent, domains[], width, depth, horizon, intervention, ' +
          'entitlement} from intent_classify. When present it is used + echoed verbatim.',
      ),
      observations: observationSchema.describe(
        'Post-execution per-floor-item results ({floor_item_id, status: served|empty, source?/' +
          'empty_reason?}) to record a truthful post-synthesis completeness receipt. Omit at plan ' +
          'issuance.',
      ),
      client_capability_version: z
        .string()
        .optional()
        .describe('Your cached capability_version. If stale, the response flags it and a tools/list_changed is emitted.'),
    },
    async (args) => {
      // M0 entitlement gate (S-3) — checked BEFORE any plan compilation, same helper +
      // same denial shape as every other per-chart tool (remoteAuthorize, lib/authz.ts).
      const authorized = await remoteAuthorize(principal, args.chart_id);
      if (!authorized) {
        return dualOutput(
          {
            ok: false,
            tool: 'plan_retrieval',
            error: { class: 'entitlement_denied', message: 'AUTHZ_DENIED: not authorized to access this chart' },
            chart_id: args.chart_id,
          },
          true,
        );
      }
      try {
        const plan = buildVidhiPlan({
          chart_id: args.chart_id,
          question: args.question,
          scope_tuple: args.scope_tuple,
          observations: args.observations,
        });
        const staleness = notifyIfCapabilityStale(args.client_capability_version, server);
        return dualOutput({
          ok: true,
          tool: 'plan_retrieval',
          capability_version: staleness.live,
          capability_stale: staleness.stale,
          tools_list_changed_emitted: staleness.notified,
          plan,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return dualOutput(
          { ok: false, tool: 'plan_retrieval', error: { class: 'compile_error', message } },
          true,
        );
      }
    },
  );
}
