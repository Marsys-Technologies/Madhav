import 'server-only'
import { query } from '@/lib/db/client'

/** Fetch signal headline + summary from bodha_msr_signals for a list of signal IDs.
 *  Returns a map signal_id → snippet string. Missing IDs get empty string. */
export async function fetchMsrSnippets(signalIds: string[]): Promise<Map<string, string>> {
  if (signalIds.length === 0) return new Map()
  try {
    const placeholders = signalIds.map((_, i) => `$${i + 1}`).join(', ')
    const { rows } = await query<{ signal_id: string; name: string; description: string }>(
      `SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signals WHERE signal_id::text IN (${placeholders})`,
      signalIds,
    )
    return new Map(rows.map(r => {
      const full = r.name
        ? (r.description ? `${r.name} — ${r.description}` : r.name)
        : (r.description ?? '')
      return [r.signal_id, full.length > 295 ? full.slice(0, 294) + '…' : full]
    }))
  } catch {
    return new Map()
  }
}
