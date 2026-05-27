import { z } from 'zod'
import { defineTool } from '../defineTool'

/**
 * read_classical_text reads from the RAG corpus (BPHS, Jaimini Sutram, KP
 * Reader, Tajaka Neelakanthi). NOT per-chart; NO ayanamsha role — the
 * classical text is independent of any specific ayanamsha frame.
 */
const inputSchema = z.object({
  text_id: z.string().describe('Classical text identifier (e.g. "bphs", "jaimini_sutram").'),
  query: z.string().optional().describe('Optional substring/keyword filter.'),
  chapter: z.string().optional(),
  verse_range: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional().default(20),
})

export const readClassicalTextContract = defineTool({
  canonical_name: 'read_classical_text',
  input_schema: inputSchema,
  description:
    'Raw read of a classical Jyotish text from the indexed corpus ' +
    '(BPHS, Jaimini Sutram, KP Reader, Tajaka Neelakanthi). When to prefer: ' +
    'direct sourcing of a śloka or chapter; quoting classical authority. ' +
    'Prefer vector_search for fuzzy semantic retrieval across the corpus.',
  role: 'text',
  family: 'text',
  data_dependency: 'classical_text',
  ayanamsha_role: null,
  annotations: { layer: 'L1' },
  per_chart: false,
})
