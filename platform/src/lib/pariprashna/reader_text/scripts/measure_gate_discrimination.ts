/**
 * measure_gate_discrimination.ts — lane P4-J, read-only measurement.
 *
 * Reproduces the false-accept figures quoted in `entry_structure_gate.ts`'s
 * header. The gate's grounding-note check is a source-FAMILY containment test;
 * this script measures exactly how weak that is, so the header states a number
 * somebody ran rather than an adjective somebody chose (§N.8: a claim needs a
 * detector; a claim about a detector's strength needs a measurement).
 *
 * For each authored entry it counts how many OTHER reader-facing catalog
 * signals that same `grounding_note` would ALSO satisfy. A high count means the
 * gate cannot tell the entry's real signal from that many impostors.
 *
 * Run (the `--conditions=react-server` flag is required — this module tree
 * imports `server-only`):
 *   npx tsx --conditions=react-server \
 *     src/lib/pariprashna/reader_text/scripts/measure_gate_discrimination.ts
 *
 * Writes nothing. Reads the committed catalog and the committed entries.
 */
import { loadReaderFacingCatalog } from '../catalog'
import { READER_TEXT_ENTRIES } from '../entries'
import { groundingNoteMatchesSource } from '../entry_structure_gate'

function main(): void {
  const catalog = loadReaderFacingCatalog()
  const others = catalog.length - 1
  const rows: { signal_id: string; falseAccepts: number }[] = []

  for (const entry of READER_TEXT_ENTRIES) {
    let falseAccepts = 0
    for (const signal of catalog) {
      if (signal.signal_id === entry.signal_id) continue
      if (!signal.classical_basis) continue
      if (groundingNoteMatchesSource(entry.grounding_note, signal.classical_basis)) falseAccepts += 1
    }
    rows.push({ signal_id: entry.signal_id, falseAccepts })
  }

  rows.sort((a, b) => b.falseAccepts - a.falseAccepts)
  const total = rows.reduce((sum, r) => sum + r.falseAccepts, 0)
  const mean = total / rows.length
  const overHalf = rows.filter((r) => r.falseAccepts > others / 2).length

  console.log(`reader-facing catalog signals: ${catalog.length} (each note tested against ${others} others)`)
  for (const r of rows) {
    console.log(`  ${r.signal_id}  ${String(r.falseAccepts).padStart(3)}  (${((r.falseAccepts / others) * 100).toFixed(1)}%)`)
  }
  console.log(`MEAN false-accept set: ${mean.toFixed(1)} of ${others} (${((mean / others) * 100).toFixed(1)}%)`)
  console.log(`entries indistinguishable from >50% of the catalog: ${overHalf} of ${rows.length}`)
}

main()
