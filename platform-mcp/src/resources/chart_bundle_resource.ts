/**
 * Compatibility notice for the retired legacy chart-bundle contract.
 * Keeps its registered name, URI template and Markdown MIME type; serves no chart data.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

export function registerChartBundleResource(server: McpServer): void {
  server.resource(
    'chart-bundle',
    new ResourceTemplate('marsys://chart-bundle/{chart_id}', { list: undefined }),
    {
      title: 'Legacy Chart Bundle (retired)',
      description: 'Retired legacy five-ayanamsha chart bundle. Compatibility notice only; no bundle data is available from this resource.',
      mimeType: 'text/markdown',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          mimeType: 'text/markdown',
          text: [
            '# Legacy Chart Bundle — retired',
            '',
            'This legacy five-ayanamsha bundle resource is retired and unavailable. This URI returns a compatibility notice only; it does not retrieve chart data.',
            '',
            '## Limited alternatives',
            'Use `marsys://chart-snapshot/{chart_id}` for a bounded chart snapshot (D1 facts, karakas, active dasha and current Panchang where available).',
            'Use `chart_snapshot` for a scoped chart grid, or `query_chart_facts` for filtered chart facts, under their own access and data contracts.',
            'These alternatives do not reproduce the retired five-frame bundle, birth Panchanga, house cusps, yoga strengths or numeric cross-ayanamsha divergence.',
          ].join('\n'),
        },
      ],
    }),
  )
}
