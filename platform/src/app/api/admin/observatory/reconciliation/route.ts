// POST /api/admin/observatory/reconciliation
//
// Triggers a reconciliation run for one (provider, period) tuple. Gated by
// `MARSYS_FLAG_OBSERVATORY_ENABLED` flag + `requireSuperAdmin()` via the shared
// `guardObservatoryRoute()`.
//
// S2.1 (this session) ships only the framework — the per-provider reconciler
// implementations are stubs that throw `NotImplementedError`. The route
// returns 400 with `manual_upload_required` for DeepSeek/NIM (no admin API)
// and 400 with `not_implemented` for the three auto-reconciled providers
// until S2.2–S2.4 land. Never returns 500 from the not-implemented path —
// 500 is reserved for unexpected internal failures (DB outage, etc).

import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardObservatoryRoute } from '../_guard'
import {
  DEFAULT_RECONCILIATION_CONFIG,
  NotImplementedError,
  type ProviderName,
  type ProviderReconcileInput,
} from '@/lib/observatory/reconciliation/types'
import {
  MANUAL_UPLOAD_PROVIDERS,
  getReconciler,
} from '@/lib/observatory/reconciliation/factory'
import type { ProviderReconciler } from '@/lib/observatory/reconciliation/types'
import { GeminiReconciler } from '@/lib/observatory/reconciliation/gemini'
import { OpenAIReconciler } from '@/lib/observatory/reconciliation/openai'

/** Per-session-merged provider replacements: when a sub-phase ships its
 *  concrete reconciler (S2.2 Anthropic, S2.3 OpenAI, S2.4 Gemini, …) the
 *  factory stub is replaced here without disturbing the not-yet-shipped
 *  provider stubs. Once all five reconcilers are merged, this map collapses
 *  into the factory itself (S2.5 close). */
function resolveReconciler(provider: ProviderName): ProviderReconciler {
  if (provider === 'gemini') return new GeminiReconciler()
  if (provider === 'openai') return new OpenAIReconciler()
  return getReconciler(provider)
}

const VALID_PROVIDERS: ReadonlySet<ProviderName> = new Set([
  'anthropic',
  'openai',
  'gemini',
  'deepseek',
  'nim',
])

const DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/

interface ReconcilePostBody {
  provider?: unknown
  period_start?: unknown
  period_end?: unknown
}

function parseBody(body: ReconcilePostBody): ProviderReconcileInput | string {
  if (
    typeof body.provider !== 'string' ||
    !VALID_PROVIDERS.has(body.provider as ProviderName)
  ) {
    return `provider must be one of: ${Array.from(VALID_PROVIDERS).join('|')}`
  }
  if (
    typeof body.period_start !== 'string' ||
    !DATE_REGEX.test(body.period_start)
  ) {
    return 'period_start must be an ISO date `YYYY-MM-DD`'
  }
  if (
    typeof body.period_end !== 'string' ||
    !DATE_REGEX.test(body.period_end)
  ) {
    return 'period_end must be an ISO date `YYYY-MM-DD`'
  }
  if (body.period_end < body.period_start) {
    return 'period_end must be on or after period_start'
  }
  return {
    provider: body.provider as ProviderName,
    period_start: body.period_start,
    period_end: body.period_end,
  }
}

export async function POST(request: Request) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  let raw: ReconcilePostBody
  try {
    raw = (await request.json()) as ReconcilePostBody
  } catch {
    return res.badRequest('Request body must be valid JSON')
  }

  const parsed = parseBody(raw)
  if (typeof parsed === 'string') return res.badRequest(parsed)

  if (MANUAL_UPLOAD_PROVIDERS.has(parsed.provider)) {
    return NextResponse.json(
      {
        error: 'manual_upload_required',
        provider: parsed.provider,
        instructions:
          parsed.provider === 'deepseek'
            ? 'DeepSeek does not expose an admin/billing API. Upload the monthly invoice CSV via the manual reconciliation UI (S2.5).'
            : 'NIM (managed catalog) does not expose an admin/billing API. Upload the per-day usage CSV via the manual reconciliation UI (S2.5).',
      },
      { status: 400 },
    )
  }

  try {
    const reconciler = resolveReconciler(parsed.provider)
    const result = await reconciler.reconcile(
      parsed,
      DEFAULT_RECONCILIATION_CONFIG,
    )
    if (result.status === 'error' && result.notes?.includes('not yet implemented')) {
      return NextResponse.json(
        {
          error: 'not_implemented',
          provider: parsed.provider,
          message: result.notes,
        },
        { status: 400 },
      )
    }
    return NextResponse.json(result)
  } catch (err) {
    if (err instanceof NotImplementedError) {
      return NextResponse.json(
        {
          error: 'not_implemented',
          provider: err.providerName,
          message: err.message,
        },
        { status: 400 },
      )
    }
    console.error('[admin/observatory/reconciliation] failed', err)
    return res.internal('Failed to run reconciliation.')
  }
}
