/**
 * Paripraśna pipeline — RECEIPT STAGE (P0-C / RF-1).
 *
 * Port: `TurnProvenance + AcharyaReadingReceipt`.
 *
 * Two receipt surfaces, deliberately kept apart because they have DIFFERENT
 * audiences and different disclosure rules:
 *
 *   · `computeTurnReceiptProvenance` — the D-16 provenance stamp. Computed
 *     fresh per turn from live sources ONLY. It is DATA THAT COMES OUT of the
 *     answer as a record of what produced it: never fed back into planning or
 *     synthesis, and DB-ONLY — it lands in the persisted
 *     `conversation_messages.metadata_json` and is never emitted on the SSE
 *     wire (audit-drawer-only, PB-1 design plan ruling 8c). The ONE exception
 *     is the reader-facing edge-state flag, which carries only the
 *     closed-lexicon display string, never a stamp field or value.
 *
 *   · `emitCompletenessReceipt` — the reader-facing coverage grade.
 *     `coverage` is a {floor_item_total, served, empty, dark} OBJECT, never a
 *     scalar: `String(coverage)` previously put the literal "[object Object]"
 *     on the wire. The served/total fraction is reported instead.
 */

import {
  computeTurnProvenanceStamp,
  getLastTurnStamp,
  detectTurnProvenanceDrift,
  type TurnProvenanceStamp,
} from '@/lib/pariprashna/provenance/stamp'
import type { WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { buildInquiryClosureReceipt, type InquiryContract } from '@/lib/vidhi/inquiry'

export interface TurnReceiptProvenance {
  provenanceStamp: TurnProvenanceStamp
  previousProvenanceStamp: TurnProvenanceStamp | null
}

export async function computeTurnReceiptProvenance(args: {
  em: PariprashnaEmitter
  chartId: string
  conversationId: string
}): Promise<TurnReceiptProvenance> {
  const { em, chartId, conversationId } = args

  const [previousProvenanceStamp, provenanceStamp] = await Promise.all([
    getLastTurnStamp(conversationId),
    computeTurnProvenanceStamp(chartId),
  ])
  const provenanceDrift = detectTurnProvenanceDrift(previousProvenanceStamp, provenanceStamp)
  if (provenanceDrift.drift && provenanceDrift.edge_state_label) {
    em.flag({
      code: 'chart_rebuilt',
      level: 'info',
      detail: provenanceDrift.edge_state_label,
    })
  }

  return { provenanceStamp, previousProvenanceStamp }
}

/** Completeness + aggregated judgment flags (grade/flag — always emitted). */
export function emitCompletenessReceipt(args: {
  em: PariprashnaEmitter
  completenessReceipt: WebCompletenessReceipt | null
  inquiryContract?: InquiryContract | null
}): void {
  const { em, completenessReceipt } = args
  if (completenessReceipt) {
    const { served, floor_item_total } = completenessReceipt.coverage
    em.grade({
      subject: 'completeness',
      grade: `${served}/${floor_item_total}`,
      detail: completenessReceipt.channel_note,
    })
  }
  if (args.inquiryContract) {
    const closureReceipt = buildInquiryClosureReceipt(args.inquiryContract)
    const required = args.inquiryContract.obligations.filter((item) => item.materiality === 'required')
    const dispositioned = required.filter((item) => item.disposition !== 'pending').length
    const unresolvedMaterialFrontier = args.inquiryContract.material_frontier.filter((item) =>
      item.materiality === 'required' && (item.disposition === 'open' || item.disposition === 'capped'))
    em.grade({
      subject: 'inquiry_contract',
      grade: args.inquiryContract.status,
      detail: `${dispositioned}/${required.length} required obligations dispositioned; ${unresolvedMaterialFrontier.length} required frontier items unresolved; receipt ${closureReceipt.receipt_hash}`,
    })
  }
}
