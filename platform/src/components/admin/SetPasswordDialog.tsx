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

function SetPasswordForm({
  user,
  onCancel,
  onSaved,
}: {
  user: AdminUser
  onCancel: () => void
  onSaved: () => void
}) {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const pwError =
    password.length > 0 && password.length < 8
      ? 'Password must be at least 8 characters.'
      : null
  const confirmError =
    confirm.length > 0 && confirm !== password ? 'Passwords do not match.' : null
  const canSubmit = password.length >= 8 && confirm === password && !submitting

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/admin/users/${user.id}/password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) {
        toast.error(body?.error?.message ?? 'Could not set password.')
        setSubmitting(false)
        return
      }
      toast.success('Password updated.')
      onSaved()
    } catch {
      toast.error('Network error.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className={adminLabel}>New password</label>
        <div className="relative mt-1.5">
          <input
            required
            autoFocus
            type={showPw ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={adminInput + ' pr-10'}
          />
          <button
            type="button"
            onClick={() => setShowPw((v) => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-brand-gold-cream"
          >
            {showPw ? 'Hide' : 'Show'}
          </button>
        </div>
        {pwError && <p className="mt-1 text-xs text-red-400">{pwError}</p>}
      </div>
      <div>
        <label className={adminLabel}>Confirm password</label>
        <input
          required
          type={showPw ? 'text' : 'password'}
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          className={adminInput + ' mt-1.5'}
        />
        {confirmError && <p className="mt-1 text-xs text-red-400">{confirmError}</p>}
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className={adminGhostBtn} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" className={adminPrimaryBtn} disabled={!canSubmit}>
          {submitting ? 'Saving…' : 'Set password'}
        </button>
      </div>
    </form>
  )
}

export function SetPasswordDialog({
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
            Set password
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {user?.email ?? ''}
          </DialogDescription>
        </DialogHeader>
        {user && (
          <SetPasswordForm
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
