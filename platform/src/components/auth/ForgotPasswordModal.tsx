"use client";
import { useState } from "react";
import Link from "next/link";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
export const RECOVERY_SUCCESS =
  "If an active account matches that username or email, a reset link will be sent to its registered email address. Check your inbox.";
export function RecoveryForm({ initialEmail = "" }: { initialEmail?: string }) {
  const [identifier, setIdentifier] = useState(initialEmail),
    [busy, setBusy] = useState(false),
    [done, setDone] = useState(false),
    [error, setError] = useState<string | null>(null);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy || !identifier.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const r = await fetch("/api/auth/recover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifier.trim() }),
      });
      if (!r.ok) {
        setError(
          r.status === 429
            ? "Too many attempts. Try again shortly."
            : "Recovery is temporarily unavailable. Please try again.",
        );
        return;
      }
      setDone(true);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="j1-form" onSubmit={submit} aria-busy={busy}>
      {done ? (
        <p role="status" className="j1-status">
          {RECOVERY_SUCCESS}
        </p>
      ) : (
        <>
          <p className="j1-note">
            Use your username or the email associated with your account.
          </p>
          <label className="j1-field">
            <span>Username or email</span>
            <input
              required
              autoComplete="username"
              maxLength={254}
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              disabled={busy}
            />
          </label>
          {error && (
            <p role="alert" className="j1-error">
              {error}
            </p>
          )}
          <button className="j1-btn" disabled={busy}>
            {busy ? "Sending…" : "Send reset link"}
          </button>
        </>
      )}
      <Link href="/login">← Back to sign in</Link>
    </form>
  );
}
export function ForgotPasswordModal({
  open,
  onOpenChange,
  initialEmail = "",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialEmail?: string;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="j1">
        <DialogHeader>
          <DialogTitle>Account recovery</DialogTitle>
          <DialogDescription>
            Recover using your username or email.
          </DialogDescription>
        </DialogHeader>
        {open && <RecoveryForm initialEmail={initialEmail} />}
      </DialogContent>
    </Dialog>
  );
}
