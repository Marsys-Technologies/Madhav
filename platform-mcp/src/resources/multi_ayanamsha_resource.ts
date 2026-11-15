/**
 * Compatibility notice for the retired legacy multi-ayanamsha contract.
 * Keeps its registered name, URI template and Markdown MIME type; serves no chart data.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

export function registerMultiAyanamshaResource(server: McpServer): void {
  server.resource(
    'multi-ayanamsha',
    new ResourceTemplate('marsys://multi-ayanamsha/{chart_id}', { list: undefined }),
    {
      title: 'Legacy Multi-Ayanamsha Status (retired)',
      description: 'Retired per-ayanamsha progress and consensus resource. Compatibility notice only; no build status or consensus is measured here.',
      mimeType: 'text/markdown',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          mimeType: 'text/markdown',
          text: [
            '# Legacy Multi-Ayanamsha Status — retired',
            '',
            'This legacy per-ayanamsha progress and consensus resource is retired and unavailable. This URI returns a compatibility notice only; it does not retrieve chart data or measure build status.',
            '',
            '## Limited alternatives',
            'Use the current chart-level readiness UI for overall chart readiness; it does not report per-ayanamsha engine versions or step progress.',
            'Use `chart_snapshot` for its separately labelled identity fact cross-check. That cross-check does not measure per-ayanamsha build progress or consensus.',
            'These alternatives do not reproduce the retired status or consensus contract.',
          ].join('\n'),
        },
      ],
    }),
  )
}
