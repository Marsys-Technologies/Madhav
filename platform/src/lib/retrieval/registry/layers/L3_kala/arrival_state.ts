/** K9-6 Portal handover adapter; the Portal host remains its custodian's code.
 * Labels are verbatim state restatements, scoped to the returned NOW page.
 * Nothing here infers a daśā, release time, verification tier or empty-window
 * verdict. The public NOW caller supplies this payload to ArrivalLine's existing
 * arrival prop only after its own session/authorization checks.
 */
type Data = Record<string, unknown>
const object = (value: unknown): Data | null => value !== null && typeof value === 'object'
  && !Array.isArray(value) ? value as Data : null
const labels = {
  outside_risk_set: 'outside risk set', method_inapplicable: 'method inapplicable',
  information_unavailable: 'information unavailable', evaluated_silent: 'evaluated silence',
  obstruction_in_force: 'obstruction in force', obstruction_cancelled: 'obstruction cancelled',
  obstruction_partly_cancelled: 'obstruction partly cancelled', obstruction_contested: 'obstruction contested',
} as const

export function arrivalFromPublishedNow(chart_id: string, response: unknown) {
  const snapshot = object(response), manifest = object(snapshot?.manifest)
  if (!snapshot || snapshot.view !== 'now' || snapshot.chart_id !== chart_id || snapshot.empty_reason !== null
    || typeof snapshot.manifest_id !== 'string' || !snapshot.manifest_id
    || typeof snapshot.generation !== 'string' || !snapshot.generation
    || manifest?.manifest_id !== snapshot.manifest_id || manifest.generation !== snapshot.generation
    || !Array.isArray(snapshot.rows)) return null
  const states = new Set<keyof typeof labels>()
  for (const value of snapshot.rows) {
    const row = object(value)
    if (row?.source_table !== 'kala_obstruction' || row.qualification !== 'published') continue
    const data = object(row.data), payload = object(object(data?.assertion)?.payload)
    if (data?.generation !== snapshot.generation || typeof payload?.effective_state !== 'string'
      || !Object.hasOwn(labels, payload.effective_state)) return null
    states.add(payload.effective_state as keyof typeof labels)
  }
  if (!states.size) return null
  const effective_states = [...states].sort()
  return { text: `Kāla · ${effective_states.map(state => labels[state]).join(' · ')}`,
    manifest_id: snapshot.manifest_id, generation: snapshot.generation, effective_states }
}
