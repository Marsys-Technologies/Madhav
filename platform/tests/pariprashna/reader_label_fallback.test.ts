/**
 * Paripraśna PB-1 (DHĀRĀ), Lane S-2 — reader-label fallback + CI warning.
 * =========================================================================
 * The brief's requirement, verbatim: "any capability with no mapped
 * `reader_label` must fall back to the string 'RETRIEVED — CHART DATA' and
 * must fire a CI warning": (a) an unmapped tool renders the fallback string,
 * never its raw id; (b) the CI warning fires.
 *
 * This suite proves both the unit contract (resolveReaderLabel) AND the
 * estate-wide contract (every one of the ~119 real registry capabilities
 * resolves safely — mapped ones to their exact declared label, unmapped ones
 * to the fallback, NEVER to their own uri).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  FALLBACK_READER_LABEL,
  STATIC_REGISTRY_READER_LABELS,
  resolveReaderLabel,
  isLeakFree,
  type ReaderLabelSource,
} from '@/lib/pariprashna/lexicon'

describe('resolveReaderLabel — unit contract', () => {
  it('(a) an unmapped capability (no register.reader_label at all) falls back, never its uri', () => {
    const cap: ReaderLabelSource = { uri: 'marsys://tool/L1/some_unmapped_tool' }
    const warn = vi.fn()
    const label = resolveReaderLabel(cap, warn)
    expect(label).toBe(FALLBACK_READER_LABEL)
    expect(label).not.toBe(cap.uri)
    expect(label).not.toContain('some_unmapped_tool')
  })

  it('(b) the unmapped path fires the warning callback with the offending uri', () => {
    const cap: ReaderLabelSource = { uri: 'marsys://tool/L1/some_unmapped_tool' }
    const warn = vi.fn()
    resolveReaderLabel(cap, warn)
    expect(warn).toHaveBeenCalledTimes(1)
    const [message, uri] = warn.mock.calls[0]
    expect(uri).toBe(cap.uri)
    expect(message).toContain(cap.uri)
    expect(message.toLowerCase()).toContain('no reader_label mapped')
  })

  it('a mapped capability with a closed-lexicon label returns it verbatim and does not warn', () => {
    const label = [...STATIC_REGISTRY_READER_LABELS][0]
    const cap: ReaderLabelSource = {
      uri: 'marsys://tool/L1/some_mapped_tool',
      register: { reader_label: label },
    }
    const warn = vi.fn()
    expect(resolveReaderLabel(cap, warn)).toBe(label)
    expect(warn).not.toHaveBeenCalled()
  })

  it('a capability declaring a bespoke, non-closed-lexicon string ALSO falls back and warns ' +
    '(defense in depth — a typo or an inline ad-hoc string must not leak through)', () => {
    const cap: ReaderLabelSource = {
      uri: 'marsys://tool/L1/some_mistyped_tool',
      register: { reader_label: 'Fetching ga_chart_facts now' }, // NOT in the closed lexicon
    }
    const warn = vi.fn()
    const label = resolveReaderLabel(cap, warn)
    expect(label).toBe(FALLBACK_READER_LABEL)
    expect(warn).toHaveBeenCalledTimes(1)
    expect(warn.mock.calls[0][0].toLowerCase()).toContain('not a member of the closed lexicon')
  })

  it('the default onUnmapped handler is a console.warn (CI-visible) — no handler needed to fire it', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    try {
      const label = resolveReaderLabel({ uri: 'marsys://tool/L1/no_handler_passed' })
      expect(label).toBe(FALLBACK_READER_LABEL)
      expect(spy).toHaveBeenCalledTimes(1)
      expect(spy.mock.calls[0][0]).toContain('[pariprashna/lexicon]')
      expect(spy.mock.calls[0][0]).toContain('no_handler_passed')
    } finally {
      spy.mockRestore()
    }
  })

  it('resolved label is always leak-free, mapped or not', () => {
    expect(isLeakFree(resolveReaderLabel({ uri: 'marsys://tool/L1/get_dashas' }, vi.fn()))).toBe(
      true
    )
    expect(
      isLeakFree(
        resolveReaderLabel(
          { uri: 'marsys://tool/L1/get_dashas', register: { reader_label: 'Consulting the chart — Daśā structure' } },
          vi.fn()
        )
      )
    ).toBe(true)
  })
})

describe('resolveReaderLabel — estate-wide sweep over the real registry catalog', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('every registered capability resolves to either its exact declared label or the fallback ' +
    '— never to its own uri/name, and the fallback path warns for every unmapped one', async () => {
    const { getCatalog } = await import('@/lib/retrieval/registry/catalog')
    const caps = getCatalog()
    expect(caps.length).toBeGreaterThan(0)

    let mappedCount = 0
    let unmappedCount = 0
    const unmappedWarnings: string[] = []

    for (const cap of caps) {
      const warn = vi.fn((message: string) => unmappedWarnings.push(message))
      const label = resolveReaderLabel(cap, warn)

      // Structural leak guard: the resolved label must never equal or contain the
      // capability's own uri/name — the exact failure mode this lane exists to prevent.
      expect(label).not.toBe(cap.uri)
      expect(label.includes(cap.uri)).toBe(false)
      if (cap.name) expect(label.toLowerCase().includes(cap.name.toLowerCase())).toBe(false)
      expect(isLeakFree(label), `capability "${cap.uri}" resolved to a leaking label: "${label}"`).toBe(
        true
      )

      const declared = cap.register?.reader_label
      if (declared && STATIC_REGISTRY_READER_LABELS.has(declared)) {
        mappedCount += 1
        expect(label).toBe(declared)
        expect(warn).not.toHaveBeenCalled()
      } else {
        unmappedCount += 1
        expect(label).toBe(FALLBACK_READER_LABEL)
        expect(warn).toHaveBeenCalledTimes(1)
      }
    }

    // Sanity: this lane mapped ~30 capabilities; the rest (~90) are unmapped by design.
    expect(mappedCount).toBeGreaterThanOrEqual(25)
    expect(unmappedCount).toBeGreaterThan(mappedCount)
    // Every unmapped capability actually fired a distinct CI-visible warning message.
    expect(unmappedWarnings.length).toBe(unmappedCount)
  })
})
