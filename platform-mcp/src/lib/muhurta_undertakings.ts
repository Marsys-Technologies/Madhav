/** The legacy muhurta_finder action vocabulary, also used by ELECT's public schema.
 * A pure shared declaration keeps the web descriptor from importing MCP execution.
 * These are activity types, not chart-signal domains or stored assertion classes. */
export const MUHURTA_UNDERTAKINGS = [
  'marriage', 'travel', 'business', 'medical', 'education', 'property', 'general',
  'spiritual_initiation', 'remedial_ritual', 'japa_start',
] as const
