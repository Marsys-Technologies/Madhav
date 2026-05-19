'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

export interface Attachment {
  id: string
  filename: string
  mime: string
  /** Alias for mime — present for AC-7 (R8-S7) and GeminiVisionAdapter compat */
  mimeType: string
  size: number
  previewUrl?: string
  url?: string
  storagePath?: string
  status: 'uploading' | 'ready' | 'error'
  errorMsg?: string
}

const MAX_BYTES = 30 * 1024 * 1024
const MAX_FILES = 20

function isSupportedMime(mime: string): boolean {
  return mime.startsWith('image/') || mime === 'application/pdf'
}

export function useAttachments() {
  const [attachments, setAttachments] = useState<Attachment[]>([])
  // Track blob URLs we created so we can revoke them and avoid memory leaks.
  const blobUrlsRef = useRef<string[]>([])

  useEffect(() => {
    return () => {
      blobUrlsRef.current.forEach(url => URL.revokeObjectURL(url))
      blobUrlsRef.current = []
    }
  }, [])

  const upload = useCallback(async (file: File, id: string) => {
    try {
      const body = new FormData()
      body.append('file', file)
      const res = await fetch('/api/chat/upload', { method: 'POST', body })
      if (!res.ok) {
        const j = (await res.json().catch(() => ({ error: `upload ${res.status}` }))) as {
          error?: string
        }
        throw new Error(j.error ?? `upload ${res.status}`)
      }
      const data = (await res.json()) as {
        url: string
        storagePath: string
        mime: string
        filename: string
        size: number
      }
      setAttachments(cur =>
        cur.map(a =>
          a.id === id
            ? { ...a, status: 'ready', url: data.url, storagePath: data.storagePath }
            : a
        )
      )
    } catch (err) {
      setAttachments(cur =>
        cur.map(a =>
          a.id === id
            ? { ...a, status: 'error', errorMsg: err instanceof Error ? err.message : 'Upload failed' }
            : a
        )
      )
    }
  }, [])

  const addFiles = useCallback(
    (incoming: FileList | File[]) => {
      const list = Array.from(incoming)
      setAttachments(current => {
        const next = [...current]
        for (const file of list) {
          if (next.length >= MAX_FILES) break
          if (file.size > MAX_BYTES) {
            const largeMime = file.type || 'application/octet-stream'
            next.push({
              id: crypto.randomUUID(),
              filename: file.name,
              mime: largeMime,
              mimeType: largeMime,
              size: file.size,
              status: 'error',
              errorMsg: 'File too large (max 30 MB)',
            })
            continue
          }
          if (!isSupportedMime(file.type)) {
            const errMime = file.type || 'application/octet-stream'
            next.push({
              id: crypto.randomUUID(),
              filename: file.name,
              mime: errMime,
              mimeType: errMime,
              size: file.size,
              status: 'error',
              errorMsg: 'Unsupported type (images and PDFs only)',
            })
            continue
          }
          const id = crypto.randomUUID()
          const previewUrl = file.type.startsWith('image/')
            ? URL.createObjectURL(file)
            : undefined
          if (previewUrl) blobUrlsRef.current.push(previewUrl)
          next.push({
            id,
            filename: file.name,
            mime: file.type,
            mimeType: file.type,
            size: file.size,
            previewUrl,
            status: 'uploading',
          })
          void upload(file, id)
        }
        return next
      })
    },
    [upload]
  )

  const remove = useCallback((id: string) => {
    setAttachments(cur => cur.filter(a => a.id !== id))
  }, [])

  const clear = useCallback(() => {
    setAttachments([])
  }, [])

  const hasBlocking = attachments.some(a => a.status === 'uploading' || a.status === 'error')
  const canSend = attachments.length === 0 || attachments.every(a => a.status === 'ready')

  return { attachments, addFiles, remove, clear, hasBlocking, canSend }
}
