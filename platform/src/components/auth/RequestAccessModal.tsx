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

export function RequestAccessForm() {
  const [fullName, setFullName] = useState(""),
    [email, setEmail] = useState(""),
    [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false),
    [done, setDone] = useState(false),
    [error, setError] = useState<string | null>(null);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/access-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim(),
          reason: reason.trim() || undefined,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(
          typeof body.error === "string"
            ? body.error
            : (body.error?.detail ??
                "Could not submit request. Please try again."),
        );
        return;
      }
      setDone(true);
    } catch {
      setError("Network error. Your details are kept; please try again.");
    } finally {
      setBusy(false);
    }
  }
  if (done)
    return (
      <div className="j1-form">
        <p className="j1-status" role="status">
          Your request has been received. An administrator will review it and
          share account setup instructions after approval.
        </p>
        <Link href="/login">← Back to sign in</Link>
      </div>
    );
  return (
    <form className="j1-form" onSubmit={submit} aria-busy={busy}>
      <p className="j1-note">
        Submit your details for review. You’ll choose your username when setting
        up your approved account.
      </p>
      <label className="j1-field">
        <span>Full name</span>
        <input
          required
          autoComplete="name"
          maxLength={100}
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          disabled={busy}
        />
      </label>
      <label className="j1-field">
        <span>Email</span>
        <input
          required
          type="email"
          autoComplete="email"
          maxLength={254}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={busy}
        />
      </label>
      <label className="j1-field">
        <span>Reason for access (optional)</span>
        <textarea
          maxLength={500}
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          disabled={busy}
        />
      </label>
      {error && (
        <p role="alert" className="j1-error">
          {error}
        </p>
      )}
      <button className="j1-btn" disabled={busy}>
        {busy ? "Submitting…" : "Submit request"}
      </button>
      <Link href="/login">← Back to sign in</Link>
    </form>
  );
}
export function RequestAccessModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="j1">
        <DialogHeader>
          <DialogTitle>Request access</DialogTitle>
          <DialogDescription>
            Administrator approval is required.
          </DialogDescription>
        </DialogHeader>
        {open && <RequestAccessForm />}
      </DialogContent>
    </Dialog>
  );
}
