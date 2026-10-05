"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  adminDialog,
  adminGhostBtn,
  adminInput,
  adminLabel,
  adminPrimaryBtn,
} from "./styles";
import type { AdminAccessRequest } from "./types";

// Inner form is keyed by the request ID so each "open a new request" gets a
// fresh useState set — no useEffect reset (avoids set-state-in-effect anti-pattern).
function ApproveForm({
  request,
  onCancel,
  onApproved,
}: {
  request: AdminAccessRequest;
  onCancel: () => void;
  onApproved: () => void;
}) {
  const [role, setRole] = useState<"guest" | "super_admin">("guest");
  const [submitting, setSubmitting] = useState(false);
  const [approved, setApproved] = useState(false);
  const [resetLink, setResetLink] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(
        `/api/admin/access-requests/${request.id}/approve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        toast.error(
          body?.error?.detail ?? body?.error?.message ?? "Approve failed.",
        );
        setSubmitting(false);
        return;
      }
      toast.success("Request approved. User account created.");
      setResetLink(body?.reset_link ?? null);
      setApproved(true);
      setSubmitting(false);
      onApproved();
    } catch {
      toast.error("Network error.");
      setSubmitting(false);
    }
  }

  if (approved) {
    return (
      <div className="space-y-4">
        {resetLink ? (
          <>
            <p className="text-sm text-brand-gold-cream">
              Share this account-setup link with the user. They will set a
              password, sign in with email, and choose their username. This link
              is not emailed automatically.
            </p>
            <textarea
              readOnly
              value={resetLink}
              rows={3}
              onFocus={(e) => e.currentTarget.select()}
              className={adminInput + " break-all font-mono text-xs"}
            />
          </>
        ) : (
          <p role="alert" className="text-sm text-brand-gold-cream">
            Account created, but the setup link could not be generated. Ask the
            approved user to use Account Recovery with their email before
            signing in and choosing a username. No email has been sent
            automatically.
          </p>
        )}
        <div className="flex justify-end">
          <button onClick={onCancel} className={adminPrimaryBtn}>
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <p className="text-sm text-brand-gold-cream">
        The user chooses an available username after setting their password and
        signing in with email.
      </p>
      <div>
        <label className={adminLabel}>Role</label>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as "guest" | "super_admin")}
          className={adminInput + " mt-1.5"}
        >
          <option value="guest">guest</option>
          <option value="super_admin">super_admin</option>
        </select>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className={adminGhostBtn}
          disabled={submitting}
        >
          Cancel
        </button>
        <button type="submit" className={adminPrimaryBtn} disabled={submitting}>
          {submitting ? "Approving…" : "Approve & create user"}
        </button>
      </div>
    </form>
  );
}

export function ApproveDialog({
  request,
  open,
  onOpenChange,
  onApproved,
}: {
  request: AdminAccessRequest | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApproved: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={adminDialog + " sm:max-w-md"}>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl font-medium tracking-wide text-brand-gold-cream">
            Approve request
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {request ? `${request.full_name} · ${request.email}` : ""}
          </DialogDescription>
        </DialogHeader>
        {request && (
          <ApproveForm
            key={request.id}
            request={request}
            onCancel={() => onOpenChange(false)}
            onApproved={onApproved}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
