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
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [pwError, setPwError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [resetLink, setResetLink] = useState<string | null>(null)
  const [passwordWasSet, setPasswordWasSet] = useState(false)

  function handlePasswordChange(val: string) {
    setPassword(val)
    if (val.length > 0 && val.length < 8) {
      setPwError('Password must be at least 8 characters.')
    } else {
      setPwError(null)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password.length > 0 && password.length < 8) {
      setPwError('Password must be at least 8 characters.')
      return
    }
    setSubmitting(true)
    try {
      const body: Record<string, string> = { full_name: fullName, email, username, role }
      if (password.length > 0) body.password = password
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        toast.error(data?.error?.detail ?? data?.error?.message ?? 'Could not create user.')
        setSubmitting(false)
        return
      }
      toast.success('User created.')
      setPasswordWasSet(password.length > 0)
      setResetLink(data?.reset_link ?? null)
      onCreated()
    } catch {
      toast.error('Network error.')
      setSubmitting(false)
    }
  }

  if (passwordWasSet) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          User created. Share the password with them securely.
        </p>
        <div className="flex justify-end">
          <button onClick={onCancel} className={adminPrimaryBtn}>
            Done
          </button>
        </div>
      </div>
    )
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
      <div>
        <label className={adminLabel}>Initial password <span className="font-normal text-muted-foreground">(optional)</span></label>
        <div className="relative mt-1.5">
          <input
            type={showPw ? 'text' : 'password'}
            value={password}
            onChange={(e) => handlePasswordChange(e.target.value)}
            placeholder="Min 8 chars. Leave blank to send a reset link instead."
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
