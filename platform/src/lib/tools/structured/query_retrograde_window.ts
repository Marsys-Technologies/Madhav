// retrogrades dropped in WS-0; stub returns empty until WS-2 rebuild.
import { tool } from 'ai'
import { z } from 'zod'

export const query_retrograde_window = tool({
  description:
    'Query retrograde stations from the retrogrades table (1900–2100, planets: Mercury, Venus, Mars, Jupiter, Saturn). ' +
    'Use this when the user asks: "was Saturn retrograde in 2022?", ' +
    '"when did Mercury go retrograde near my job change in May 2019?", ' +
    '"find all Mars retrograde stations between 2018 and 2024", ' +
    '"what planets stationed direct or retrograde around my marriage (2013)?", ' +
    '"show Saturn retrograde start dates near Sade Sati peak (2022–2025)". ' +
    'Each row is a station event: retrograde_start (planet begins retrograde) or ' +
    'retrograde_end (planet returns direct). Returns planet, station_type, date, longitude_deg, sign.',
  inputSchema: z.object({
    start_date: z.string().describe('Start of window in YYYY-MM-DD format.'),
    end_date: z.string().describe('End of window in YYYY-MM-DD format.'),
    planet: z.enum(['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']).optional().describe(
      'Filter to a specific planet. Omit for all 5 planets.'
    ),
    station_type: z.enum(['retrograde_start', 'retrograde_end']).optional().describe(
      'Filter to start (goes retrograde) or end (goes direct) stations. Omit for both.'
    ),
  }),
  execute: async ({ start_date, end_date }) => {
    return { window: { start_date, end_date }, count: 0, stations: [] }
  },
})
