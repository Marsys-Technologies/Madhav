/**
 * RIR-S1 + RIR-S2 + RIR-S3 + RIR-S4: Retrieval Interface Register — Standard Envelope Library
 *
 * Defines the standard input/output/citation envelope types for all 55
 * MARSYS-JIS retrieval tools across all 5 channels. Implements the contract
 * specified in RETRIEVAL_INTERFACE_REGISTER_v1_0.md §2–§6.
 *
 * Pure TypeScript — no Zod dependency.
 *
 * [BUILD-ORCH-RIR-S1, RIR-S2, RIR-S3, RIR-S4]
 */

// ── Channel + Tier enums ──────────────────────────────────────────────────────

export const CHANNELS = ['mcp', 'portal', 'consume_hybrid', 'answer_eval', 'api'] as const
export type Channel = (typeof CHANNELS)[number]

export const AUDIENCE_TIERS = ['super_admin', 'acharya_reviewer', 'client', 'public_redacted'] as const
export type AudienceTier = (typeof AUDIENCE_TIERS)[number]

export function isChannel(v: unknown): v is Channel {
  return typeof v === 'string' && (CHANNELS as readonly string[]).includes(v)
}

export function isAudienceTier(v: unknown): v is AudienceTier {
  return typeof v === 'string' && (AUDIENCE_TIERS as readonly string[]).includes(v)
}

// ── RIR-S1: Standard Input Envelope ──────────────────────────────────────────

export interface RetrievalInput<TParams> {
  /** Tool-specific parameters */
  params: TParams
  /** Target chart UUID (optional for classical / global tools) */
  chart_id?: string
  /** Ayanamsha filter — defaults to 'lahiri' if omitted */
  ayanamsha_id: string
  /** Requesting audience tier — controls disclosure depth */
  audience_tier: AudienceTier
  /** Originating channel */
  channel: Channel
  /** Trace correlation ID from query pipeline */
  query_id?: string
  /** Session correlation ID */
  session_id?: string
}

export class InputValidationError extends Error {
  readonly field: string
  constructor(field: string, message: string) {
    super(`RetrievalInput validation failed on '${field}': ${message}`)
    this.name = 'InputValidationError'
    this.field = field
  }
}

/**
 * Parse and validate a raw object as RetrievalInput<TParams>.
 * Applies defaults and validates required fields.
 */
export function parseInput<TParams>(
  paramsValidator: (raw: unknown) => TParams,
  raw: unknown,
): RetrievalInput<TParams> {
  if (!raw || typeof raw !== 'object') {
    throw new InputValidationError('root', 'expected object')
  }
  const obj = raw as Record<string, unknown>

  if (!('audience_tier' in obj) || !isAudienceTier(obj['audience_tier'])) {
    throw new InputValidationError(
      'audience_tier',
      `must be one of: ${AUDIENCE_TIERS.join(', ')}`,
    )
  }
  if (!('channel' in obj) || !isChannel(obj['channel'])) {
    throw new InputValidationError(
      'channel',
      `must be one of: ${CHANNELS.join(', ')}`,
    )
  }

  return {
    params: paramsValidator(obj['params']),
    chart_id: typeof obj['chart_id'] === 'string' ? obj['chart_id'] : undefined,
    ayanamsha_id: typeof obj['ayanamsha_id'] === 'string' ? obj['ayanamsha_id'] : 'lahiri',
    audience_tier: obj['audience_tier'] as AudienceTier,
    channel: obj['channel'] as Channel,
    query_id: typeof obj['query_id'] === 'string' ? obj['query_id'] : undefined,
    session_id: typeof obj['session_id'] === 'string' ? obj['session_id'] : undefined,
  }
}

// ── RIR-S2: Citation Envelope ─────────────────────────────────────────────────

export interface Citation {
  /** Human-readable citation ref, e.g. '[FORENSIC §3.1]' */
  ref: string
  /** Canonical artifact ID: 'FORENSIC' | 'LEL' | 'MSR' | ... */
  source_canonical_id: string
  /** Artifact version string */
  source_version: string
  /** Source confidence 0–1 */
  confidence: number
  /** Optional sub-section reference */
  section?: string
}

/** Build a citation from a canonical artifact and optional section. */
export function makeCitation(
  canonicalId: string,
  version: string,
  confidence: number,
  section?: string,
): Citation {
  const refParts = [canonicalId]
  if (section) refParts.push(section)
  return {
    ref: `[${refParts.join(' ')}]`,
    source_canonical_id: canonicalId,
    source_version: version,
    confidence: Math.min(1, Math.max(0, confidence)),
    section,
  }
}

// ── RIR-S2: Standard Output Envelope ──────────────────────────────────────────

export interface RetrievalOutput<TResult> {
  /** Tool-specific result data */
  data: TResult
  /** Source citations for B.11 compliance tracking */
  citations: Citation[]
  /** Channel this result was served from */
  channel: Channel
  /** Ayanamsha used for this retrieval */
  ayanamsha_id: string
  /** Number of data rows returned */
  rows_returned: number
  /** Latency in milliseconds */
  latency_ms: number
  /** Whether result was served from cache */
  cache_hit: boolean
  /** Whether disclosure was filtered by audience_tier */
  tier_filtered: boolean
  /** Envelope schema version */
  schema_version: '1.0'
}

/** Construct a standard output envelope with sensible defaults. */
export function makeOutput<TResult>(
  data: TResult,
  options: Partial<Omit<RetrievalOutput<TResult>, 'data' | 'schema_version'>> = {},
): RetrievalOutput<TResult> {
  return {
    data,
    citations: options.citations ?? [],
    channel: options.channel ?? 'portal',
    ayanamsha_id: options.ayanamsha_id ?? 'lahiri',
    rows_returned: options.rows_returned ?? 0,
    latency_ms: options.latency_ms ?? 0,
    cache_hit: options.cache_hit ?? false,
    tier_filtered: options.tier_filtered ?? false,
    schema_version: '1.0',
  }
}

// ── RIR-S3: Channel Adapter ────────────────────────────────────────────────────

export interface ChannelAdapter<TInput, TOutput> {
  channel: Channel
  execute(input: RetrievalInput<TInput>): Promise<RetrievalOutput<TOutput>>
}

/** Wrap a tool function in a channel adapter with standard timing. */
export function makeChannelAdapter<TInput, TOutput>(
  channel: Channel,
  fn: (params: TInput, chartId?: string, ayanamshaId?: string) => Promise<TOutput>,
  options: {
    citationsFn?: (output: TOutput) => Citation[]
    rowsFn?: (output: TOutput) => number
  } = {},
): ChannelAdapter<TInput, TOutput> {
  return {
    channel,
    async execute(input: RetrievalInput<TInput>): Promise<RetrievalOutput<TOutput>> {
      const t0 = Date.now()
      const data = await fn(input.params, input.chart_id, input.ayanamsha_id)
      const latency_ms = Date.now() - t0
      return makeOutput(data, {
        citations: options.citationsFn?.(data) ?? [],
        channel,
        ayanamsha_id: input.ayanamsha_id,
        rows_returned: options.rowsFn?.(data) ?? 0,
        latency_ms,
      })
    },
  }
}

// ── RIR-S4: Tier-filter utilities ────────────────────────────────────────────

const TIER_RANK: Record<AudienceTier, number> = {
  super_admin: 4,
  acharya_reviewer: 3,
  client: 2,
  public_redacted: 1,
}

/** Returns true if the requested tier is at least as privileged as the required tier. */
export function tierAtLeast(requested: AudienceTier, required: AudienceTier): boolean {
  return TIER_RANK[requested] >= TIER_RANK[required]
}

/** Filter items to those permitted by the audience tier. */
export function filterByTier<T extends { min_tier?: AudienceTier }>(
  items: T[],
  tier: AudienceTier,
): { filtered: T[]; was_filtered: boolean } {
  const filtered = items.filter(
    (item) => !item.min_tier || tierAtLeast(tier, item.min_tier),
  )
  return { filtered, was_filtered: filtered.length < items.length }
}
