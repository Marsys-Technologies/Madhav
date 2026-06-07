/**
 * adapters/bulk_context/bundler.ts
 *
 * Clips and structures pre-fetched results into a system context bundle.
 * Output is injected into the LLM system prompt as structured context.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { clipResult } from '../shared/result_clipper'
import type { PrefetchResult } from './prefetcher'

export interface BundleSection {
  uri: string
  heading: string
  content: string
  clipped: boolean
}

export interface BulkContextBundle {
  sections: BundleSection[]
  total_size_kb: number
  assembled_at: string
}

const SECTION_MAX_KB = 16  // max 16KB per section
const BUNDLE_MAX_KB = 128  // max 128KB total bundle

/**
 * Clip and structure pre-fetch results into a bundle.
 */
export function buildBundle(results: PrefetchResult[]): BulkContextBundle {
  const sections: BundleSection[] = []
  let totalBytes = 0

  for (const result of results) {
    if (result.error || result.data === null) continue

    const serialized = typeof result.data === 'string'
      ? result.data
      : JSON.stringify(result.data, null, 2)

    const sizeBytes = new TextEncoder().encode(serialized).length
    const clipped = sizeBytes > SECTION_MAX_KB * 1024

    const content = clipped
      ? clipResult(result.data, { max_kb: SECTION_MAX_KB, strategy: 'truncate_end' })
      : serialized

    const contentBytes = new TextEncoder().encode(content).length

    // Stop if we'd exceed bundle max
    if (totalBytes + contentBytes > BUNDLE_MAX_KB * 1024) break

    const heading = result.uri.replace('marsys://', '').replace(/\//g, ' › ')

    sections.push({
      uri: result.uri,
      heading,
      content,
      clipped,
    })

    totalBytes += contentBytes
  }

  return {
    sections,
    total_size_kb: Math.round(totalBytes / 1024),
    assembled_at: new Date().toISOString(),
  }
}

/**
 * Format bundle as a system context block for LLM injection.
 */
export function formatBundleForPrompt(bundle: BulkContextBundle): string {
  if (bundle.sections.length === 0) return ''

  const lines: string[] = [
    '## Marsys Retrieval Context',
    `*${bundle.sections.length} sources · ${bundle.total_size_kb}KB · assembled ${bundle.assembled_at}*`,
    '',
  ]

  for (const section of bundle.sections) {
    lines.push(`### ${section.heading}`)
    if (section.clipped) {
      lines.push('*[result clipped to fit context window]*')
    }
    lines.push('```')
    lines.push(section.content)
    lines.push('```')
    lines.push('')
  }

  return lines.join('\n')
}
