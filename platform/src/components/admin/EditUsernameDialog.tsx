'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { adminDialog, adminGhostBtn, adminInput, adminLabel, adminPrimaryBtn } from './styles'
import type { AdminUser } from './types'

function EditUsernameForm({
  user,
  onCancel,
  onSaved,
}: {
  user: AdminUser
  onCancel: () => void
  onSaved: () => void
}) {
  const [username, setUsername] = useState(user.username ?? '')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await fetch(`/api/admin/users/${user.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username }),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) {
        toast.error(body?.error?.message ?? 'Update failed.')
        setSubmitting(false)
        return
      }
      toast.success('Username updated.')
      onSaved()
    } catch {
      toast.error('Network error.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className={adminLabel}>Username</label>
        <input
          required
          autoFocus
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className={adminInput + ' mt-1.5'}
        />
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className={adminGhostBtn} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" className={adminPrimaryBtn} disabled={submitting}>
          {submitting ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  )
}

export function EditUsernameDialog({
  user,
  open,
  onOpenChange,
  onSaved,
}: {
  user: AdminUser | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={adminDialog + ' sm:max-w-md'}>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl font-medium tracking-wide text-brand-gold-cream">
            Edit username
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {user?.email ?? ''}
          </DialogDescription>
        </DialogHeader>
        {user && (
          <EditUsernameForm
            key={user.id}
            user={user}
            onCancel={() => onOpenChange(false)}
            onSaved={() => {
              onSaved()
              onOpenChange(false)
            }}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
