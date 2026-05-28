import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock GoogleAuth before importing embedText.
vi.mock('google-auth-library', () => {
  return {
    GoogleAuth: class {
      async getClient() {
        return {
          getAccessToken: async () => ({ token: 'test-token' }),
        }
      }
    },
  }
})

import { embedText, embedTexts, EMBED_DIM } from '../embedText'

function makeVector(seed: number): number[] {
  return new Array(EMBED_DIM).fill(0).map((_, i) => (seed + i) / 1000)
}

interface FetchCall {
  url: string
  body: { instances: Array<{ task_type: string; content: string }> }
  headers: Headers
}

function installFetchMock(): {
  calls: FetchCall[]
  restore: () => void
} {
  const calls: FetchCall[] = []
  const spy = vi
    .spyOn(globalThis, 'fetch')
    .mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const body = init?.body ? JSON.parse(init.body as string) : { instances: [] }
      calls.push({
        url: input.toString(),
        body,
        headers: new Headers(init?.headers ?? {}),
      })
      // Echo one prediction per instance.
      const predictions = body.instances.map((_inst: unknown, i: number) => ({
        embeddings: { values: makeVector(i) },
      }))
      return new Response(JSON.stringify({ predictions }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
  return { calls, restore: () => spy.mockRestore() }
}

describe('embeddings/embedText', () => {
  const ENV = {
    GCP_PROJECT: process.env['GCP_PROJECT'],
    VERTEX_AI_LOCATION: process.env['VERTEX_AI_LOCATION'],
  }

  beforeEach(() => {
    process.env['GCP_PROJECT'] = 'test-proj'
    process.env['VERTEX_AI_LOCATION'] = 'asia-south1'
  })

  afterEach(() => {
    if (ENV.GCP_PROJECT === undefined) delete process.env['GCP_PROJECT']
    else process.env['GCP_PROJECT'] = ENV.GCP_PROJECT
    if (ENV.VERTEX_AI_LOCATION === undefined) delete process.env['VERTEX_AI_LOCATION']
    else process.env['VERTEX_AI_LOCATION'] = ENV.VERTEX_AI_LOCATION
  })

  describe('embedText (single)', () => {
    it('returns one EMBED_DIM-length vector from a single :predict call', async () => {
      const { calls, restore } = installFetchMock()
      try {
        const v = await embedText('hello')
        expect(v).toHaveLength(EMBED_DIM)
        expect(calls).toHaveLength(1)
        expect(calls[0].body.instances).toHaveLength(1)
        expect(calls[0].body.instances[0]).toEqual({
          task_type: 'RETRIEVAL_DOCUMENT',
          content: 'hello',
        })
      } finally {
        restore()
      }
    })

    it('throws on missing env vars', async () => {
      delete process.env['VERTEX_AI_LOCATION']
      const { restore } = installFetchMock()
      try {
        await expect(embedText('x')).rejects.toThrow(/VERTEX_AI_LOCATION/)
      } finally {
        restore()
      }
    })
  })

  describe('embedTexts (batched)', () => {
    it('returns [] for empty input without calling fetch', async () => {
      const { calls, restore } = installFetchMock()
      try {
        const out = await embedTexts([])
        expect(out).toEqual([])
        expect(calls).toHaveLength(0)
      } finally {
        restore()
      }
    })

    it('50-text input produces 1 Vertex request (not 50) — AC.3', async () => {
      const { calls, restore } = installFetchMock()
      try {
        const texts = new Array(50).fill(0).map((_, i) => `text-${i}`)
        const vectors = await embedTexts(texts)
        expect(vectors).toHaveLength(50)
        expect(vectors[0]).toHaveLength(EMBED_DIM)
        // The acceptance criterion: 1 round-trip for ≤ 250 instances.
        expect(calls).toHaveLength(1)
        expect(calls[0].body.instances).toHaveLength(50)
        expect(calls[0].body.instances[7]).toEqual({
          task_type: 'RETRIEVAL_DOCUMENT',
          content: 'text-7',
        })
      } finally {
        restore()
      }
    })

    it('chunks above the 250-instance Vertex limit into multiple :predict calls', async () => {
      const { calls, restore } = installFetchMock()
      try {
        const texts = new Array(600).fill(0).map((_, i) => `t${i}`)
        const vectors = await embedTexts(texts)
        expect(vectors).toHaveLength(600)
        // 600 -> 250 + 250 + 100 = 3 calls
        expect(calls).toHaveLength(3)
        expect(calls[0].body.instances).toHaveLength(250)
        expect(calls[1].body.instances).toHaveLength(250)
        expect(calls[2].body.instances).toHaveLength(100)
      } finally {
        restore()
      }
    })

    it('hits the region-pinned endpoint built from VERTEX_AI_LOCATION', async () => {
      const { calls, restore } = installFetchMock()
      try {
        await embedTexts(['a'])
        expect(calls[0].url).toBe(
          'https://asia-south1-aiplatform.googleapis.com/v1/projects/test-proj/locations/asia-south1/publishers/google/models/text-multilingual-embedding-002:predict',
        )
        expect(calls[0].headers.get('Authorization')).toBe('Bearer test-token')
      } finally {
        restore()
      }
    })

    it('throws on dim mismatch in any returned instance', async () => {
      const spy = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => {
        return new Response(
          JSON.stringify({
            predictions: [
              { embeddings: { values: new Array(EMBED_DIM).fill(0) } },
              { embeddings: { values: [1, 2, 3] } }, // bad dim
            ],
          }),
          { status: 200 },
        )
      })
      try {
        await expect(embedTexts(['ok', 'bad'])).rejects.toThrow(/Unexpected embedding dim/)
      } finally {
        spy.mockRestore()
      }
    })

    it('throws when prediction count mismatches instance count', async () => {
      const spy = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => {
        return new Response(JSON.stringify({ predictions: [] }), { status: 200 })
      })
      try {
        await expect(embedTexts(['only-one'])).rejects.toThrow(/0 predictions for 1 instances/)
      } finally {
        spy.mockRestore()
      }
    })

    it('propagates non-2xx Vertex errors', async () => {
      const spy = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => {
        return new Response('server boom', { status: 503 })
      })
      try {
        await expect(embedTexts(['x'])).rejects.toThrow(/503/)
      } finally {
        spy.mockRestore()
      }
    })
  })
})
