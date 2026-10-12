/** Leaf-capability fixtures for the graha_portrait identity tests: positions + dignity carry rows for SAT and MOON. */
interface Leaf { handler: { mockResolvedValue: (v: unknown) => unknown } }
export interface PortraitLeaves {
  positions: Leaf; dignity: Leaf; strength: Leaf; avasthas: Leaf; yogaDosha: Leaf; dashas: Leaf; signals: Leaf; traverse: Leaf
}

const posRow = (subject: string, sign: string) => ({
  fact_id: `p-${subject}`, fact_category: 'graha_position', fact_subject: subject, ayanamsha_id: 'lahiri_chitrapaksha',
  fact_key: 'sign', fact_value_text: sign, fact_value_num: null,
})
const dignityRow = (subject: string) => ({
  fact_id: `dg-${subject}`, fact_category: 'graha_dignity_per_varga', fact_subject: subject, fact_key: 'dignity_state',
  fact_value_text: 'neutral', fact_value_jsonb: { varga: 'D1' },
})

export function installPortraitLeaves(l: PortraitLeaves): void {
  l.positions.handler.mockResolvedValue({ content: { rows: [posRow('SAT', 'Libra'), posRow('MOON', 'Aquarius'), posRow('SUN', 'Capricorn')] }, is_error: false })
  l.dignity.handler.mockResolvedValue({ content: { rows: [dignityRow('SAT'), dignityRow('MOON')] }, is_error: false })
  for (const cap of [l.strength, l.avasthas, l.yogaDosha, l.dashas]) cap.handler.mockResolvedValue({ content: { rows: [] }, is_error: false })
  l.signals.handler.mockResolvedValue({ content: { signals: [] }, is_error: false })
  l.traverse.handler.mockResolvedValue({ content: { nodes: [], edges: [], node_count: 0, edge_count: 0 }, is_error: false })
}
