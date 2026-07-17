/**
 * vidhi_delivery.test.ts — D-2 Lane V-2 self-test (BIND_D-2.md §F1.7 ledger rows 14-18).
 *
 * Covers the delivery surface end to end against the LIVE (vendored) registry — never synthetic
 * stubs (§F1.7 anti-vacuous):
 *   row 14 — registry MCP resource registered, readable, rows match V-1 (see also parity test)
 *   row 15 — vidhi_plan prompt registered; plan_retrieval tool returns a compiled wealth plan
 *   row 16 — scope_tuple echoed for correction (received + fallback paths)
 *   row 17 — completeness receipt (served/empty/dark) VALIDATED by V-0's real validator
 *   row 18 — capability_version served; a stale version triggers tools/list_changed
 */
import { describe, it, expect, vi } from 'vitest';
import { registerResources } from '../resources/index.js';
import { registerPrompts } from '../prompts/index.js';
import { registerVidhiPlanTool } from '../tools/register_vidhi_plan.js';
import { buildRegistryPayload, VIDHI_REGISTRY_URI } from '../resources/vidhi_registry_resource.js';
import { emitCompletenessReceipt } from '../lib/completeness_receipt.js';
import { buildVidhiPlan } from '../resources/vidhi/plan_builder.js';
import {
  VIDHI_CAPABILITY_VERSION,
  notifyIfCapabilityStale,
} from '../resources/vidhi/capability_version.js';
import { VIDHI_PRIMITIVES } from '../resources/vidhi/index.js';
import type { Principal } from '../types.js';

// V-0's REAL validator (read-only, outside this lane's glob) — producer/consumer parity.
import { validateReceipt } from '../../../platform/scripts/audit/doctrine_harness/lib/completeness_receipt.ts';

const CHART = '482012f1-710e-4a25-994a-93821f5871aa';

type Captured = {
  resources: Array<{ name: string; uri: string; cb: (...a: unknown[]) => unknown }>;
  prompts: Array<{ name: string }>;
  tools: Array<{ name: string; cb: (args: Record<string, unknown>) => unknown }>;
  toolListChanged: ReturnType<typeof vi.fn>;
};

function makeMockServer(): { server: unknown; captured: Captured } {
  const captured: Captured = { resources: [], prompts: [], tools: [], toolListChanged: vi.fn() };
  const server = {
    resource: (name: string, uriOrTemplate: unknown, ...rest: unknown[]) => {
      const cb = rest[rest.length - 1] as (...a: unknown[]) => unknown;
      const uri =
        typeof uriOrTemplate === 'string'
          ? uriOrTemplate
          : ((uriOrTemplate as { uriTemplate?: string }).uriTemplate ?? '(template)');
      captured.resources.push({ name, uri, cb });
    },
    prompt: (name: string) => {
      captured.prompts.push({ name });
    },
    tool: (name: string, _desc: string, _schema: unknown, cb: (args: Record<string, unknown>) => unknown) => {
      captured.tools.push({ name, cb });
    },
    sendToolListChanged: captured.toolListChanged,
  };
  return { server, captured };
}

function principal(): Principal {
  return { user_uid: 'u-v2-test', key_id: 'mcp_test_v2', role: 'guest' };
}

// ── row 14: registry resource ────────────────────────────────────────────────
describe('row 14 — vidhi registry as an MCP resource', () => {
  it('registers marsys://vidhi/registry (listed + readable) and the per-intent floor template', () => {
    const { server, captured } = makeMockServer();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerResources(server as any, principal());
    const names = captured.resources.map((r) => r.name);
    expect(names).toContain('vidhi-registry');
    expect(names).toContain('vidhi-floor');
    expect(captured.resources.some((r) => r.uri === VIDHI_REGISTRY_URI)).toBe(true);
  });

  it('registry payload rows match the vendored registry and carry capability_version', async () => {
    const { server, captured } = makeMockServer();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerResources(server as any, principal());
    const reg = captured.resources.find((r) => r.name === 'vidhi-registry')!;
    const out = (await reg.cb({ href: VIDHI_REGISTRY_URI })) as { contents: Array<{ text: string }> };
    const payload = JSON.parse(out.contents[0]!.text) as ReturnType<typeof buildRegistryPayload>;
    expect(payload.primitive_count).toBe(VIDHI_PRIMITIVES.length);
    expect((payload.primitives as unknown[]).length).toBe(VIDHI_PRIMITIVES.length);
    expect((payload.intent_floors as unknown[]).length).toBe(8);
    expect(payload.capability_version).toBe(VIDHI_CAPABILITY_VERSION);
  });
});

// ── row 15: prompt + fallback tool ───────────────────────────────────────────
describe('row 15 — compiled plans as prompt + plan_retrieval fallback tool', () => {
  it('registers the vidhi_plan prompt', () => {
    const { server, captured } = makeMockServer();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(server as any);
    expect(captured.prompts.map((p) => p.name)).toContain('vidhi_plan');
  });

  it('plan_retrieval returns a compiled wealth plan (floor non-empty)', async () => {
    const { server, captured } = makeMockServer();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerVidhiPlanTool(server as any);
    const tool = captured.tools.find((t) => t.name === 'plan_retrieval')!;
    const out = (await tool.cb({ chart_id: CHART, question: 'How is my wealth and money?' })) as {
      structuredContent: { object: { ok: boolean; plan: { scope_tuple: { intent: string }; floor: unknown[] } } };
    };
    const obj = out.structuredContent.object;
    expect(obj.ok).toBe(true);
    expect(obj.plan.scope_tuple.intent).toBe('wealth_deepdive');
    expect(obj.plan.floor.length).toBeGreaterThan(0);
  });
});

// ── row 16: scope tuple echo ─────────────────────────────────────────────────
describe('row 16 — scope tuple echoed for correction', () => {
  it('a received DR-8 tuple is echoed verbatim (method=received_scope_tuple)', () => {
    const plan = buildVidhiPlan({
      chart_id: CHART,
      scope_tuple: { intent: 'career_deepdive', domains: ['career'], depth: 'structure' },
    });
    expect(plan.scope_tuple.intent).toBe('career_deepdive');
    expect(plan.scope_tuple.depth).toBe('structure');
    expect(plan.scope_resolution.method).toBe('received_scope_tuple');
    expect(plan.scope_resolution.fallback_recommended).toBe(false);
  });

  it('a question with no tuple falls back and flags fallback_recommended', () => {
    const plan = buildVidhiPlan({ chart_id: CHART, question: 'career prospects?' });
    expect(plan.scope_tuple.intent).toBe('career_deepdive');
    expect(plan.scope_resolution.method).toBe('v2_fallback_keyword');
    expect(plan.scope_resolution.fallback_recommended).toBe(true);
  });
});

// ── row 17: completeness receipt validated by V-0's real validator ───────────
describe('row 17 — completeness receipt served/empty/dark, validated by V-0', () => {
  it('plan-issuance receipt (no observations) passes V-0 validateReceipt', () => {
    const plan = buildVidhiPlan({ chart_id: CHART, question: 'wealth deep dive' });
    const r = validateReceipt(plan.completeness_receipt);
    expect(r.valid).toBe(true);
    // every floor item accounted for exactly once
    const total = r.served + r.empty + r.dark;
    expect(r.floor_item_total).toBe(total);
    // dark items exist for wealth_deepdive and each cites a CR-\d+ (validator already checked)
    expect(plan.completeness_receipt.dark.every((d) => /^CR-\d+$/.test(d.cr_row))).toBe(true);
  });

  it('post-synthesis receipt with observations partitions served/empty and validates', () => {
    const plan = buildVidhiPlan({ chart_id: CHART, question: 'wealth deep dive' });
    // Observe the first two non-dark floor items as served / empty.
    const nonDark = plan.floor.filter((f) => f.known_gap === null);
    const obs = [
      { floor_item_id: nonDark[0]!.primitive_id, status: 'served' as const, source: nonDark[0]!.live_tool },
      { floor_item_id: nonDark[1]!.primitive_id, status: 'empty' as const, empty_reason: 'route_empty' },
    ];
    // emitCompletenessReceipt reads only contract.floor + contract.machine_band; the plan
    // carries both, so it is a valid contract-like input for the emitter.
    const receipt = emitCompletenessReceipt(plan as never, obs);
    expect(receipt.served.some((s) => s.floor_item_id === nonDark[0]!.primitive_id)).toBe(true);
    expect(receipt.empty.some((e) => e.floor_item_id === nonDark[1]!.primitive_id && e.empty_reason === 'route_empty')).toBe(true);
    expect(validateReceipt(receipt).valid).toBe(true);
  });
});

// ── row 18: capability_version + staleness kill ──────────────────────────────
describe('row 18 — capability_version + tools/list_changed staleness kill', () => {
  it('capability_version is deterministic and vidhi-prefixed', () => {
    expect(VIDHI_CAPABILITY_VERSION).toMatch(/^vidhi-\d+\.\d+\.\d+\+r[0-9a-f]{12}$/);
  });

  it('a stale client version triggers sendToolListChanged; a matching one does not', () => {
    const changed = vi.fn();
    const server = { sendToolListChanged: changed } as never;

    const stale = notifyIfCapabilityStale('vidhi-0.0.0+rdeadbeef0000', server);
    expect(stale.stale).toBe(true);
    expect(stale.notified).toBe(true);
    expect(changed).toHaveBeenCalledTimes(1);

    const fresh = notifyIfCapabilityStale(VIDHI_CAPABILITY_VERSION, server);
    expect(fresh.stale).toBe(false);
    expect(changed).toHaveBeenCalledTimes(1); // unchanged

    const none = notifyIfCapabilityStale(undefined, server);
    expect(none.stale).toBe(false);
    expect(changed).toHaveBeenCalledTimes(1);
  });

  it('the plan_retrieval tool emits the notification on a stale client version', async () => {
    const { server, captured } = makeMockServer();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerVidhiPlanTool(server as any);
    const tool = captured.tools.find((t) => t.name === 'plan_retrieval')!;
    const out = (await tool.cb({
      chart_id: CHART,
      question: 'wealth',
      client_capability_version: 'vidhi-0.0.0+rstale00000000',
    })) as { structuredContent: { object: { capability_stale: boolean; tools_list_changed_emitted: boolean } } };
    expect(out.structuredContent.object.capability_stale).toBe(true);
    expect(out.structuredContent.object.tools_list_changed_emitted).toBe(true);
    expect(captured.toolListChanged).toHaveBeenCalled();
  });
});
