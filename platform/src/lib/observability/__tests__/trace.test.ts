import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  parseTraceparent,
  serializeTraceparent,
  startSpan,
  endSpan,
  fetchWithTrace,
  newTraceId,
  newSpanId,
} from '../trace'

describe('observability/trace — W3C traceparent', () => {
  describe('parseTraceparent', () => {
    it('parses a valid traceparent header', () => {
      const v = '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
      const parsed = parseTraceparent(v)
      expect(parsed).toEqual({
        traceId: '0af7651916cd43dd8448eb211c80319c',
        spanId: 'b7ad6b7169203331',
        flags: '01',
      })
    })

    it('lowercases input and tolerates leading/trailing whitespace', () => {
      const v = '  00-0AF7651916CD43DD8448EB211C80319C-B7AD6B7169203331-01  '
      const parsed = parseTraceparent(v)
      expect(parsed?.traceId).toBe('0af7651916cd43dd8448eb211c80319c')
      expect(parsed?.spanId).toBe('b7ad6b7169203331')
    })

    it('returns null for null/undefined/empty input', () => {
      expect(parseTraceparent(null)).toBeNull()
      expect(parseTraceparent(undefined)).toBeNull()
      expect(parseTraceparent('')).toBeNull()
    })

    it('rejects malformed structure', () => {
      expect(parseTraceparent('00-foo-bar-01')).toBeNull()
      expect(parseTraceparent('00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331')).toBeNull()
      expect(parseTraceparent('xx-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01')).toBeNull()
    })

    it('rejects version ff (reserved) and all-zero ids (W3C §3.2.2.3)', () => {
      expect(
        parseTraceparent('ff-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'),
      ).toBeNull()
      expect(
        parseTraceparent('00-00000000000000000000000000000000-b7ad6b7169203331-01'),
      ).toBeNull()
      expect(
        parseTraceparent('00-0af7651916cd43dd8448eb211c80319c-0000000000000000-01'),
      ).toBeNull()
    })
  })

  describe('serializeTraceparent', () => {
    it('produces a W3C-valid string that round-trips through parseTraceparent', () => {
      const ctx = {
        traceId: '0af7651916cd43dd8448eb211c80319c',
        spanId: 'b7ad6b7169203331',
        flags: '01',
      }
      const s = serializeTraceparent(ctx)
      expect(s).toBe('00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01')
      expect(parseTraceparent(s)).toEqual(ctx)
    })
  })

  describe('newTraceId / newSpanId', () => {
    it('newTraceId returns 32 lowercase hex chars; each call differs', () => {
      const a = newTraceId()
      const b = newTraceId()
      expect(a).toMatch(/^[0-9a-f]{32}$/)
      expect(b).toMatch(/^[0-9a-f]{32}$/)
      expect(a).not.toBe(b)
    })

    it('newSpanId returns 16 lowercase hex chars; each call differs', () => {
      const a = newSpanId()
      const b = newSpanId()
      expect(a).toMatch(/^[0-9a-f]{16}$/)
      expect(b).toMatch(/^[0-9a-f]{16}$/)
      expect(a).not.toBe(b)
    })
  })

  describe('startSpan', () => {
    it('mints a fresh trace id when no inbound traceparent is provided', () => {
      const r = startSpan('test.root', null)
      expect(r.parent).toBeNull()
      expect(r.ctx.traceId).toMatch(/^[0-9a-f]{32}$/)
      expect(r.ctx.spanId).toMatch(/^[0-9a-f]{16}$/)
      expect(r.span.parentSpanId).toBeNull()
      expect(r.span.name).toBe('test.root')
    })

    it('continues the inbound trace id but mints a new span id', () => {
      const inbound = '00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01'
      const r = startSpan('test.child', inbound)
      expect(r.ctx.traceId).toBe('0af7651916cd43dd8448eb211c80319c')
      expect(r.ctx.spanId).not.toBe('b7ad6b7169203331')
      expect(r.span.parentSpanId).toBe('b7ad6b7169203331')
      expect(r.traceparent).toBe(
        `00-0af7651916cd43dd8448eb211c80319c-${r.ctx.spanId}-01`,
      )
    })

    it('carries attributes onto the span', () => {
      const r = startSpan('test.route', null, { 'http.route': '/api/x', userTier: 'admin' })
      expect(r.span.attributes).toEqual({ 'http.route': '/api/x', userTier: 'admin' })
    })
  })

  describe('endSpan', () => {
    let logSpy: ReturnType<typeof vi.spyOn>
    beforeEach(() => {
      logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    })
    afterEach(() => {
      logSpy.mockRestore()
    })

    it('emits a structured-log line including the cloud-trace field when GCP_PROJECT set', () => {
      const prev = process.env['GCP_PROJECT']
      process.env['GCP_PROJECT'] = 'test-proj'
      try {
        const r = startSpan('test.end', null)
        const rec = endSpan(r.span, 'ok')
        expect(rec.status).toBe('ok')
        expect(rec.endMs).toBeGreaterThanOrEqual(rec.startMs)
        expect(logSpy).toHaveBeenCalledOnce()
        const payload = JSON.parse(logSpy.mock.calls[0][0] as string)
        expect(payload.severity).toBe('INFO')
        expect(payload.span.name).toBe('test.end')
        expect(payload['logging.googleapis.com/trace']).toBe(
          `projects/test-proj/traces/${rec.traceId}`,
        )
      } finally {
        if (prev === undefined) delete process.env['GCP_PROJECT']
        else process.env['GCP_PROJECT'] = prev
      }
    })

    it('logs ERROR severity when status is error', () => {
      const r = startSpan('test.err', null)
      const rec = endSpan(r.span, 'error', 'boom')
      expect(rec.status).toBe('error')
      expect(rec.error).toBe('boom')
      const payload = JSON.parse(logSpy.mock.calls[0][0] as string)
      expect(payload.severity).toBe('ERROR')
    })
  })

  describe('fetchWithTrace', () => {
    it('injects a traceparent header with the same trace id but a new span id', async () => {
      const captured: { headers: Headers } = { headers: new Headers() }
      const fetchSpy = vi
        .spyOn(globalThis, 'fetch')
        .mockImplementation(async (_input: RequestInfo | URL, init?: RequestInit) => {
          captured.headers = new Headers(init?.headers ?? {})
          return new Response('ok', { status: 200 })
        })
      try {
        const ctx = {
          traceId: '0af7651916cd43dd8448eb211c80319c',
          spanId: 'b7ad6b7169203331',
          flags: '01',
        }
        const res = await fetchWithTrace(ctx, 'https://example.test')
        expect(res.status).toBe(200)
        const sent = captured.headers.get('traceparent')!
        const parsed = parseTraceparent(sent)
        expect(parsed?.traceId).toBe(ctx.traceId)
        expect(parsed?.spanId).not.toBe(ctx.spanId)
        expect(parsed?.flags).toBe('01')
      } finally {
        fetchSpy.mockRestore()
      }
    })

    it('does not clobber a caller-supplied traceparent header', async () => {
      const captured: { headers: Headers } = { headers: new Headers() }
      const fetchSpy = vi
        .spyOn(globalThis, 'fetch')
        .mockImplementation(async (_input: RequestInfo | URL, init?: RequestInit) => {
          captured.headers = new Headers(init?.headers ?? {})
          return new Response('ok', { status: 200 })
        })
      try {
        const ctx = {
          traceId: '0af7651916cd43dd8448eb211c80319c',
          spanId: 'b7ad6b7169203331',
          flags: '01',
        }
        const explicit = '00-11111111111111111111111111111111-2222222222222222-01'
        await fetchWithTrace(ctx, 'https://example.test', {
          headers: { traceparent: explicit },
        })
        expect(captured.headers.get('traceparent')).toBe(explicit)
      } finally {
        fetchSpy.mockRestore()
      }
    })
  })
})
