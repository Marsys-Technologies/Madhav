"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { confirmPasswordReset, verifyPasswordResetCode } from "firebase/auth";
import { auth } from "@/lib/firebase/client";
import { EntryShell } from "@/components/journey1/EntryShell";
import { PasswordField } from "@/components/journey1/PasswordField";

type Phase =
  | { kind: "verifying" }
  | { kind: "invalid"; message: string }
  | { kind: "ready"; email: string }
  | { kind: "submitting"; email: string }
  | { kind: "done" };

function ResetPasswordContent() {
  const params = useSearchParams();
  const oobCode = params.get("oobCode");
  const mode = params.get("mode");

  // Compute the initial phase from URL params synchronously — don't reset
  // state in an effect (cascading-render anti-pattern).
  const initialPhase: Phase =
    !oobCode || mode !== "resetPassword"
      ? {
          kind: "invalid",
          message:
            "This link is invalid or has expired. Please request a new password-reset email.",
        }
      : { kind: "verifying" };
  const [phase, setPhase] = useState<Phase>(initialPhase);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  // External-system sync: verify the oobCode with Firebase. Only fires when
  // the initial phase is 'verifying' (i.e. we have an oobCode worth checking).
  useEffect(() => {
    if (phase.kind !== "verifying" || !oobCode) return;
    verifyPasswordResetCode(auth, oobCode)
      .then((email) => setPhase({ kind: "ready", email }))
      .catch(() => {
        setPhase({
          kind: "invalid",
          message:
            "This link is invalid or has expired. Please request a new password-reset email.",
        });
      });
    // We intentionally only re-verify when oobCode changes; phase.kind is
    // checked above to no-op once verification has settled.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [oobCode]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (phase.kind !== "ready") return;
    setPhase({ kind: "submitting", email: phase.email });
    try {
      await confirmPasswordReset(auth, oobCode!, password);
      setPhase({ kind: "done" });
    } catch (err) {
      const code = (err as { code?: string })?.code;
      const message =
        code === "auth/weak-password"
          ? "Password is too weak. Try a longer one."
          : code === "auth/expired-action-code" ||
              code === "auth/invalid-action-code"
            ? "This link has expired. Please request a new password-reset email."
            : "Could not reset password. Please try again.";
      setError(message);
      setPhase({ kind: "ready", email: phase.email });
    }
  }

  const isSetup = (() => {
    try {
      return (
        new URL(params.get("continueUrl") ?? "", "https://local.invalid")
          .pathname === "/setup-account"
      );
    } catch {
      return false;
    }
  })();
  return (
    <EntryShell name="reset">
      {phase.kind === "verifying" && (
        <p role="status" className="j1-note">
          Verifying link…
        </p>
      )}
      {phase.kind === "invalid" && (
        <div className="j1-form">
          <p className="j1-error" role="alert">
            {phase.message}
          </p>
          <Link href="/login/recovery">Request a new reset link</Link>
          <Link href="/login">← Back to sign in</Link>
        </div>
      )}
      {(phase.kind === "ready" || phase.kind === "submitting") && (
        <form
          className="j1-form"
          onSubmit={handleSubmit}
          aria-busy={phase.kind === "submitting"}
        >
          <p className="j1-note">
            {isSetup
              ? "Set your password to begin account setup."
              : "Set a new password for your account."}
          </p>
          <PasswordField
            label="New password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            disabled={phase.kind === "submitting"}
          />
          <PasswordField
            label="Confirm password"
            value={confirm}
            onChange={setConfirm}
            autoComplete="new-password"
            disabled={phase.kind === "submitting"}
          />
          <p className="j1-note">Use at least eight characters.</p>
          {error && (
            <p role="alert" className="j1-error">
              {error}
            </p>
          )}
          <button
            type="submit"
            className="j1-btn"
            disabled={phase.kind === "submitting"}
          >
            {phase.kind === "submitting" ? "Resetting…" : "Set password"}
          </button>
          <Link href="/login">← Back to sign in</Link>
        </form>
      )}
      {phase.kind === "done" && (
        <div className="j1-form">
          <p role="status" className="j1-status">
            Your password has been updated.
            {isSetup
              ? " Sign in with your email to choose your username."
              : " You can now sign in with your new password."}
          </p>
          <Link href={isSetup ? "/login?setup=1" : "/login"} className="j1-btn">
            {isSetup ? "Continue account setup" : "Back to sign in"}
          </Link>
        </div>
      )}
    </EntryShell>
  );
}
export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="j1 min-h-screen grid place-items-center">Loading…</div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
