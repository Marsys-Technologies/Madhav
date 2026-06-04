// sade_sati_phases dropped in WS-0; stub returns empty until WS-2 rebuild.
// TODO(ws-2): repoint once sade_sati_phases is recreated in Brahma kala schema.
import { tool } from 'ai'
import { z } from 'zod'

export const query_sade_sati = tool({
  description:
    'Query the sade_sati_phases table — Saturn Sade Sati cycle data across all 4 cycles (pre-birth + 3 lifetime). ' +
    'Use this when the user asks: "am I currently in Sade Sati?", ' +
    '"when was the peak of the second Sade Sati cycle?", ' +
    '"what Sade Sati phase was active in 2022?", ' +
    '"show all Sade Sati rising/peak/setting phases", ' +
    '"when does the current Sade Sati end?". ' +
    'Returns cycle_number, phase (rising/peak/setting/pre_birth/gap), start_date, end_date, saturn_sign_at_start, notes.',
  inputSchema: z.object({
    date: z.string().optional().describe(
      'Find phases active on this date (YYYY-MM-DD). Returns phases where start_date <= date <= end_date.'
    ),
    cycle_number: z.number().int().min(0).max(4).optional().describe(
      'Filter to a specific cycle (0=pre-birth, 1–3 = lifetime cycles). Omit for all cycles.'
    ),
    phase: z.enum(['pre_birth', 'rising', 'peak', 'setting', 'gap']).optional().describe(
      'Filter by phase type. Omit for all phases.'
    ),
  }),
  execute: async (_input) => {
    return { count: 0, phases: [] }
  },
})
