/**
 * classical_texts_resource.ts
 * MCP Resource: marsys://classical-texts/{text_key}
 *
 * Exposes the metadata and chunk-count summary for a named classical text,
 * verse-addressable by text_key (e.g. bphs, jaimini_sutra).
 *
 * Serves as the resource endpoint for brahmagyan.texts (asset contract 0.3).
 * Calls /api/classical-texts/{text_key}/summary via platform internal API.
 *
 * brahmagyan.texts delta build 2026-06-03
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

interface ClassicalTextSummary {
  text_key: string
  title: string
  author: string | null
  tradition: string
  school: string
  tier: number
  language_original: string
  translation_author: string | null
  chunk_count: number
  attribution_baseline_confidence: number
}

async function fetchClassicalTextSummary(textKey: string): Promise<ClassicalTextSummary | null> {
  try {
    const resp = await fetch(
      `${PLATFORM_URL}/api/classical-texts/${encodeURIComponent(textKey)}/summary`,
      {
        headers: { 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
        signal: AbortSignal.timeout(6000),
      },
    )
    if (!resp.ok) return null
    return (await resp.json()) as ClassicalTextSummary
  } catch {
    return null
  }
}

function summaryToMarkdown(s: ClassicalTextSummary): string {
  return [
    `# Classical Text: ${s.title}`,
    `**text_key:** ${s.text_key}  |  **tradition:** ${s.tradition}  |  **school:** ${s.school}  |  **tier:** ${s.tier}`,
    s.author ? `**Author:** ${s.author}` : '',
    s.translation_author ? `**Translation:** ${s.translation_author}` : '',
    `**Chunks available:** ${s.chunk_count}  |  **Attribution confidence baseline:** ${s.attribution_baseline_confidence}`,
    '',
    `Use \`read_classical_text\` tool with \`query\` to search this text semantically,`,
    `or cite verses as \`${s.text_key.toUpperCase()}.chapter.verse\`.`,
  ].filter(Boolean).join('\n')
}

export function registerClassicalTextsResource(server: McpServer): void {
  const template = new ResourceTemplate(
    'marsys://classical-texts/{text_key}',
    { list: undefined },
  )

  server.resource(
    'classical-texts',
    template,
    async (uri, { text_key }) => {
      const key = Array.isArray(text_key) ? text_key[0] : text_key
      const summary = await fetchClassicalTextSummary(key ?? '')

      const content = summary
        ? summaryToMarkdown(summary)
        : `# Classical Text: ${key}\n\nNot found or not yet ingested. ` +
          `Check brahmagyan.texts licensing_audit for status.`

      return {
        contents: [{
          uri: uri.href,
          mimeType: 'text/markdown',
          text: content,
        }],
      }
    },
  )
}
