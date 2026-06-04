// TODO(ws-2): eclipses dropped WS-0; repoint to Brahma kala_eclipses once recreated.
import { tool } from 'ai'
import { z } from 'zod'

export const query_eclipse_window = tool({
  description:
    'Query solar and lunar eclipses from the eclipses table (1900–2100, Swiss Ephemeris, Lahiri sidereal). ' +
    'Use this when the user asks: "were there any eclipses around my marriage date (May 2013)?", ' +
    '"find total solar eclipses near my birth", "any eclipses in Aquarius or Pisces in 2022–2025?", ' +
    '"which eclipses fell within 6 months of 2024-02-16?", ' +
    '"show all lunar eclipses between 2019 and 2022 visible from Bhubaneswar". ' +
    'Returns date, type (solar_total/solar_annular/solar_partial/lunar_total/lunar_partial/lunar_penumbral), ' +
    'longitude_deg, sign, nakshatra, visibility_region.',
  inputSchema: z.object({
    start_date: z.string().describe('Start of window in YYYY-MM-DD format.'),
    end_date: z.string().describe('End of window in YYYY-MM-DD format.'),
    type: z.enum([
      'solar_total', 'solar_annular', 'solar_partial',
      'lunar_total', 'lunar_partial', 'lunar_penumbral',
    ]).optional().describe('Filter by eclipse type. Omit for all types.'),
    sign: z.string().optional().describe(
      'Filter to eclipses in this sidereal sign (e.g. Aquarius, Capricorn, Scorpio).'
    ),
  }),
  execute: async ({ start_date, end_date }) => {
    return { window: { start_date, end_date }, count: 0, eclipses: [] }
  },
})
