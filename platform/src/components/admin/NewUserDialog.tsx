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

function NewUserForm({
  onCancel,
  onCreated,
}: {
  onCancel: () => void
  onCreated: () => void
}) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [role, setRole] = useState<'guest' | 'super_admin'>('guest')
  const [submitting, setSubmitting] = useState(false)
  const [resetLink, setResetLink] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email, username, role }),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) {
        toast.error(body?.error ?? 'Could not create user.')
        setSubmitting(false)
        return
      }
      toast.success('User created.')
      setResetLink(body?.reset_link ?? null)
      onCreated()
    } catch {
      toast.error('Network error.')
      setSubmitting(false)
    }
  }

  if (resetLink) {
    return (
      <div className="space-y-4">
        <textarea
          readOnly
          value={resetLink}
          rows={3}
          onFocus={(e) => e.currentTarget.select()}
          className={adminInput + ' break-all font-mono text-xs'}
        />
        <div className="flex justify-end">
          <button onClick={onCancel} className={adminPrimaryBtn}>
            Done
          </button>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className={adminLabel}>Full name</label>
        <input required autoFocus value={fullName} onChange={(e) => setFullName(e.target.value)} className={adminInput + ' mt-1.5'} />
      </div>
      <div>
        <label className={adminLabel}>Email</label>
        <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={adminInput + ' mt-1.5'} />
      </div>
      <div>
        <label className={adminLabel}>Username</label>
        <input required value={username} onChange={(e) => setUsername(e.target.value)} placeholder="3-32 chars · a-z 0-9 _ -" className={adminInput + ' mt-1.5'} />
      </div>
      <div>
        <label className={adminLabel}>Role</label>
        <select value={role} onChange={(e) => setRole(e.target.value as 'guest' | 'super_admin')} className={adminInput + ' mt-1.5'}>
          <option value="guest">guest</option>
          <option value="super_admin">super_admin</option>
        </select>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className={adminGhostBtn} disabled={submitting}>Cancel</button>
        <button type="submit" className={adminPrimaryBtn} disabled={submitting}>
          {submitting ? 'Creating…' : 'Create user'}
        </button>
      </div>
    </form>
  )
}

export function NewUserDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: () => void
}) {
  // Re-mount the form whenever the dialog opens so state is fresh.
  const [openedAt, setOpenedAt] = useState(() => Date.now())
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) setOpenedAt(Date.now())
        onOpenChange(next)
      }}
    >
      <DialogContent className={adminDialog + ' sm:max-w-md'}>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl font-medium tracking-wide text-brand-gold-cream">
            New user
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Direct-create — bypasses the access-request queue.
          </DialogDescription>
        </DialogHeader>
        {open && (
          <NewUserForm
            key={openedAt}
            onCancel={() => onOpenChange(false)}
            onCreated={onCreated}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
