// ephemeris_daily dropped in WS-0; stub returns empty until WS-2 rebuild.
// TODO(ws-2): repoint to ganita_positions (Brahma ephemeris asset).
import { tool } from 'ai'
import { z } from 'zod'

export const query_planet_position = tool({
  description:
    'Query Swiss Ephemeris-computed planetary positions from the ephemeris_daily table (1900–2100, daily resolution, Lahiri sidereal). ' +
    'Use this when the user asks: "what was Saturn\'s longitude on 2018-03-15?", ' +
    '"was Jupiter retrograde in January 2021?", ' +
    '"what sign was Rahu transiting on the day of my job change (2019-05-15)?", ' +
    '"show all planets for 1984-02-05 (natal chart)", ' +
    '"what nakshatra was the Moon in on 2022-01-03?". ' +
    'Returns longitude_deg, sign, nakshatra, nakshatra_pada, is_retrograde, speed_deg_per_day. ' +
    'For natal chart facts use query_chart_fact instead (more structured, faster).',
  inputSchema: z.object({
    date: z.string().describe(
      'Date in YYYY-MM-DD format. Must be between 1900-01-01 and 2100-12-31.'
    ),
    planet: z.enum([
      'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu',
    ]).optional().describe(
      'Planet to query. Omit to return all 9 planets for the date.'
    ),
  }),
  execute: async ({ date }) => {
    return { date, count: 0, positions: [] }
  },
})
