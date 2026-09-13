import { z } from 'zod'
import type { Principal } from '../types.js'
import { callInquiryLifecycle } from '../lib/inquiry_bridge.js'

export interface InquiryRegisteringServer {
  tool(name: string, description: string, schema: Record<string, unknown>, handler: (args: unknown) => Promise<unknown>): void
}

const scopeSchema = z.object({
  intent: z.enum(['dasha_timing', 'transit_analysis', 'yoga_identification', 'planet_strength', 'house_analysis', 'remedy_lookup', 'panchanga', 'classical_rule', 'chart_overview', 'prediction_calibration', 'domain_assessment', 'unknown']),
  domains: z.array(z.enum(['wealth', 'career', 'marriage', 'health', 'children', 'education', 'spirituality', 'litigation', 'property', 'travel', 'general'])),
  width: z.enum(['narrow', 'standard', 'broad']),
  depth: z.enum(['shallow', 'standard', 'deep']),
  horizon: z.enum(['past', 'present', 'near', 'far', 'atemporal']),
  intervention: z.enum(['none', 'remedy', 'muhurta', 'mitigation']),
  entitlement: z.enum(['reference', 'native', 'restricted']),
}).strict()

const aiProposalSchema = z.object({
  question_facets: z.array(z.object({
    label: z.string().trim().min(1).max(160),
    terms: z.array(z.string().trim().min(1).max(80)).max(32),
    materiality: z.enum(['required', 'supporting']),
  }).strict()).max(16),
  uncommon_adjacencies: z.array(z.object({
    from_scu_id: z.string().trim().min(1).max(200),
    to_scu_id: z.string().trim().min(1).max(200),
    rationale: z.string().trim().min(1).max(500),
  }).strict()).max(16),
  hypotheses: z.array(z.string().trim().min(1).max(500)).max(16),
}).strict()

const startSchema = z.object({
  chart_id: z.string().uuid(), question: z.string().trim().min(1).max(4000),
  scope_tuple: scopeSchema, ai_proposal: aiProposalSchema.optional(),
}).strict()

function output(payload: Record<string, unknown>) {
  const result = { content: [{ type: 'text' as const, text: JSON.stringify(payload) }], structuredContent: payload }
  return payload['ok'] === false ? { ...result, isError: true as const } : result
}

export function registerInquiryLifecycleTools(server: InquiryRegisteringServer, principal: Principal, profile: string): void {
  const restricted = () => profile !== 'full'
  server.tool('inquiry_start', 'Start a durable, versioned Inquiry Contract. Returns required obligations, executable next actions, and a short-lived principal/chart-bound lifecycle token. Raw MCP receives evidence and closure receipts but no synthesis.', {
    chart_id: z.string().uuid(), question: z.string().trim().min(1).max(4000), scope_tuple: scopeSchema, ai_proposal: aiProposalSchema.optional(),
  }, async (args) => {
    if (restricted()) return output({ ok: false, error: 'inquiry lifecycle requires the full MCP profile' })
    const parsed = startSchema.parse(args)
    return output(await callInquiryLifecycle(principal, { action: 'start', ...parsed }))
  })

  server.tool('inquiry_execute_next', 'Execute exactly one server-authorized Inquiry Contract action. The server pins tool identity and arguments, records raw evidence durably, proves pagination state, consumes the one-use token, and returns the next token.', {
    lifecycle_token: z.string().min(1).max(16384), action_id: z.string().regex(/^item-[0-9]{3}$/),
  }, async (args) => {
    if (restricted()) return output({ ok: false, error: 'inquiry lifecycle requires the full MCP profile' })
    const parsed = z.object({ lifecycle_token: z.string().min(1).max(16384), action_id: z.string().regex(/^item-[0-9]{3}$/) }).strict().parse(args)
    return output(await callInquiryLifecycle(principal, { action: 'execute', ...parsed }))
  })

  server.tool('inquiry_finalize', 'Validate deterministic closure. COMPLETE is returned only when all required obligations have evidence and the material frontier is closed; otherwise the receipt remains INCOMPLETE or BLOCKED with reasons.', {
    lifecycle_token: z.string().min(1).max(16384),
  }, async (args) => {
    if (restricted()) return output({ ok: false, error: 'inquiry lifecycle requires the full MCP profile' })
    const parsed = z.object({ lifecycle_token: z.string().min(1).max(16384) }).strict().parse(args)
    return output(await callInquiryLifecycle(principal, { action: 'finalize', ...parsed }))
  })
}
