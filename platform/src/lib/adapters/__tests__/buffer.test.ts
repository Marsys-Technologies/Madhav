import { describe, test, expect } from 'vitest'
import { MarkerBuffer } from '../buffer'

describe('MarkerBuffer — no markers', () => {
  test('plain text with no tags passes through as text', () => {
    const buf = new MarkerBuffer()
    const out = buf.feed('hello world')
    expect(out.text).toBe('hello world')
    expect(out.reasoning).toBeUndefined()
  })

  test('flush on empty buffer returns empty object', () => {
    const buf = new MarkerBuffer()
    buf.feed('done')
    expect(buf.flush()).toEqual({})
  })

  test('multiple chunks without markers concatenate as text', () => {
    const buf = new MarkerBuffer()
    const parts = ['foo ', 'bar ', 'baz']
    const texts = parts.map(c => buf.feed(c).text ?? '').join('')
    expect(texts).toBe('foo bar baz')
  })
})

describe('MarkerBuffer — complete markers in single chunk', () => {
  test('content inside <think>…</think> is emitted as reasoning', () => {
    const buf = new MarkerBuffer()
    const out = buf.feed('<think>step one</think>answer')
    expect(out.reasoning).toBe('step one')
    expect(out.text).toBe('answer')
  })

  test('text before open tag is preserved', () => {
    const buf = new MarkerBuffer()
    const out = buf.feed('prefix<think>reasoning</think>suffix')
    expect(out.text).toBe('prefixsuffix')
    expect(out.reasoning).toBe('reasoning')
  })

  test('content after close tag is plain text', () => {
    const buf = new MarkerBuffer()
    const out = buf.feed('<think>r</think>post text')
    expect(out.text).toBe('post text')
  })
})

describe('MarkerBuffer — tags split across chunks', () => {
  test('open tag split across two chunks', () => {
    const buf = new MarkerBuffer()
    const out1 = buf.feed('<thi')
    const out2 = buf.feed('nk>reasoning</think>text')
    expect((out1.text ?? '') + (out2.text ?? '')).toBe('text')
    expect((out1.reasoning ?? '') + (out2.reasoning ?? '')).toBe('reasoning')
  })

  test('close tag split across two chunks', () => {
    const buf = new MarkerBuffer()
    buf.feed('<think>partial reasoning</thi')
    const out = buf.feed('nk>after')
    expect(out.reasoning).toBeUndefined()  // close tag now completes
    expect(out.text).toBe('after')
  })

  test('tag split into single characters', () => {
    const buf = new MarkerBuffer()
    const chunks = '<think>r</think>t'.split('')
    let reasoning = ''
    let text = ''
    for (const c of chunks) {
      const out = buf.feed(c)
      reasoning += out.reasoning ?? ''
      text += out.text ?? ''
    }
    const flushed = buf.flush()
    reasoning += flushed.reasoning ?? ''
    text += flushed.text ?? ''
    expect(reasoning).toBe('r')
    expect(text).toBe('t')
  })
})

describe('MarkerBuffer — unclosed markers', () => {
  test('partial close tag in buffer at end-of-stream flushes as reasoning with unclosed=true', () => {
    // '</thi' matches the start of '</think>' so it's held in the buffer as a
    // potential tag boundary. On flush the ambiguity resolves to unclosed=true.
    const buf = new MarkerBuffer()
    buf.feed('<think>content</thi')
    const flushed = buf.flush()
    expect(flushed.reasoning).toBe('</thi')
    expect(flushed.unclosed).toBe(true)
    expect(flushed.text).toBeUndefined()
  })

  test('partial open tag at end of stream flushes as text', () => {
    const buf = new MarkerBuffer()
    const out1 = buf.feed('hello ')
    const out2 = buf.feed('<thi')  // '<thi' matches prefix of '<think>' — held in buffer
    expect(out1.text).toBe('hello ')
    expect(out2.text).toBeUndefined()
    const flushed = buf.flush()
    expect(flushed.text).toBe('<thi')
    expect(flushed.unclosed).toBeUndefined()
  })
})

describe('MarkerBuffer — edge cases', () => {
  test('empty stream: feed empty string then flush', () => {
    const buf = new MarkerBuffer()
    const out = buf.feed('')
    expect(out.reasoning).toBeUndefined()
    expect(out.text).toBeUndefined()
    expect(buf.flush()).toEqual({})
  })

  test('custom open/close tags', () => {
    const buf = new MarkerBuffer('[REASON]', '[/REASON]')
    const out = buf.feed('[REASON]think hard[/REASON]answer')
    expect(out.reasoning).toBe('think hard')
    expect(out.text).toBe('answer')
  })

  test('content entirely before marker: no reasoning emitted', () => {
    const buf = new MarkerBuffer()
    const out = buf.feed('just text')
    expect(out.reasoning).toBeUndefined()
    expect(out.text).toBe('just text')
    expect(buf.flush()).toEqual({})
  })

  test('after close tag all subsequent text is plain text', () => {
    const buf = new MarkerBuffer()
    buf.feed('<think>r</think>')
    const out1 = buf.feed('first')
    const out2 = buf.feed('second')
    expect(out1.text).toBe('first')
    expect(out2.text).toBe('second')
    expect(out1.reasoning).toBeUndefined()
    expect(out2.reasoning).toBeUndefined()
  })

  test('currentState tracks transitions', () => {
    const buf = new MarkerBuffer()
    expect(buf.currentState).toBe('before')
    buf.feed('<think>')
    expect(buf.currentState).toBe('inside')
    buf.feed('</think>')
    expect(buf.currentState).toBe('after')
  })
})
