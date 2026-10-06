"use client";
import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  changeAccountPassword,
  finishAccountSecurity,
  signOutAccountSessions,
} from "@/lib/account/password-flow";
export function SecurityForm() {
  const router = useRouter();
  const [current, setCurrent] = useState(""),
    [next, setNext] = useState(""),
    [repeat, setRepeat] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null),
    [partial, setPartial] = useState(false),
    [confirm, setConfirm] = useState(false);
  const invalid = !current
    ? "Enter your current password."
    : next.length < 12
      ? "Use at least 12 characters for the new password."
      : next === current
        ? "Choose a password different from the current one."
        : repeat !== next
          ? "The new passwords do not match."
          : null;
  const clear = () => {
    setCurrent("");
    setNext("");
    setRepeat("");
  };
  const done = () => {
    router.replace("/login?security=updated");
    router.refresh();
  };
  async function change(event: FormEvent) {
    event.preventDefault();
    if (busy || partial || invalid) {
      setError(invalid);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await changeAccountPassword(current, next);
      if (result.complete) done();
      else {
        setPartial(result.changed);
        setError(result.error ?? "Password could not be changed. Try again.");
      }
    } finally {
      clear();
      setBusy(false);
    }
  }
  async function revoke(retry: boolean) {
    if (busy) return;
    if (!retry && !current) {
      setError("Enter your current password above to verify this sign-out.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const complete = retry
        ? await finishAccountSecurity()
        : await signOutAccountSessions(current);
      if (complete) done();
      else
        setError(
          retry
            ? "Password changed. Session sign-out is still incomplete. Retry, or sign in again and use Sign out of all sessions."
            : "Your current password could not be verified or session sign-out could not be completed. Try again.",
        );
    } finally {
      clear();
      setBusy(false);
      setConfirm(false);
    }
  }
  return (
    <div className="j5-narrow j5-stack">
      <form className="j5-panel j1-form" onSubmit={change}>
        <h2>Change password</h2>
        <ol className="j5-steps">
          <li>Reauthenticate</li>
          <li>Change password</li>
          <li>Revoke sessions</li>
          <li>Sign in again</li>
        </ol>
        <p className="j1-note">
          Confirm your current password, choose a new one, and every signed-in
          session — including this one — will be signed out. Then sign in again
          with the new password.
        </p>
        <label className="j1-field">
          <span>Current password</span>
          <input
            aria-label="Current password"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            disabled={busy || partial}
          />
        </label>
        <label className="j1-field">
          <span>New password</span>
          <input
            aria-label="New password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            value={next}
            onChange={(e) => setNext(e.target.value)}
            disabled={busy || partial}
          />
          <small>At least 12 characters</small>
        </label>
        <label className="j1-field">
          <span>Repeat new password</span>
          <input
            aria-label="Repeat new password"
            type="password"
            autoComplete="new-password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            disabled={busy || partial}
          />
        </label>
        {error && (
          <p className="j1-error" role="alert">
            {error}
          </p>
        )}
        {partial ? (
          <button
            type="button"
            className="j1-btn"
            disabled={busy}
            onClick={() => void revoke(true)}
          >
            Retry sign-out
          </button>
        ) : (
          <button className="j1-btn" disabled={busy || !!invalid}>
            {busy ? "Updating…" : "Change password and sign out everywhere"}
          </button>
        )}
        <Link href="/login/recovery" className="j5-back">
          Forgot the current password? Account Recovery
        </Link>
      </form>
      <section className="j5-panel">
        <h2>Sessions</h2>
        <p className="j1-note">
          Sign out every session at once. Enter your current password above to
          verify the action. You will also sign out of this browser.
        </p>
        {confirm ? (
          <div
            className="j5-actions"
            role="group"
            aria-label="Confirm all-session sign-out"
          >
            <button
              className="j1-btn"
              disabled={busy}
              onClick={() => void revoke(false)}
            >
              Confirm sign-out everywhere
            </button>
            <button
              className="j1-btn j1-btn-secondary"
              disabled={busy}
              onClick={() => setConfirm(false)}
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="j1-btn j1-btn-secondary"
            disabled={busy || partial}
            onClick={() => setConfirm(true)}
          >
            Sign out of all sessions
          </button>
        )}
      </section>
      <p className="j1-note">
        Account Recovery accepts your username or e-mail and keeps account
        existence private.
      </p>
    </div>
  );
}
