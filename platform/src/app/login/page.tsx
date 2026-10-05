"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "@/lib/firebase/client";
import { EntryShell } from "@/components/journey1/EntryShell";
import { PasswordField } from "@/components/journey1/PasswordField";

type Tab = "username" | "email";

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("username");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      // Resolve username → email if necessary.
      let email: string;
      if (tab === "email") {
        email = identifier.trim();
      } else {
        const res = await fetch("/api/auth/resolve-username", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: identifier.trim() }),
        });
        if (!res.ok) {
          // Match the generic error: don't disclose username existence.
          setError("Invalid username or password.");
          setSubmitting(false);
          return;
        }
        const body = (await res.json()) as { email?: string };
        if (!body.email) {
          setError("Invalid username or password.");
          setSubmitting(false);
          return;
        }
        email = body.email;
      }

      // Sign in with Firebase to obtain an ID token.
      const credential = await signInWithEmailAndPassword(
        auth,
        email,
        password,
      );
      const idToken = await credential.user.getIdToken();

      // Exchange the ID token for a session cookie. The session route also
      // checks the profile's status and refuses inactive accounts.
      const sessionRes = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken }),
      });
      if (!sessionRes.ok) {
        const body = await sessionRes.json().catch(() => ({}));
        if (body?.error === "account_inactive") {
          setError(
            "Your account is not active. Please contact the administrator.",
          );
        } else {
          setError("Sign-in failed. Please try again.");
        }
        // Sign out from Firebase since the server refused the session.
        await auth.signOut().catch(() => {});
        setSubmitting(false);
        return;
      }

      const session = (await sessionRes.json()) as {
        username_setup_required?: boolean;
      };
      const requestedSetup =
        new URLSearchParams(window.location.search).get("setup") === "1";
      router.push(
        session.username_setup_required || requestedSetup
          ? "/setup-account"
          : "/dashboard",
      );
      router.refresh();
    } catch (err) {
      // Firebase Auth errors land here (wrong password, user-not-found, etc.).
      // Always show the same generic message — don't leak which factor was wrong.
      const code = (err as { code?: string })?.code;
      const message =
        code === "auth/too-many-requests"
          ? "Too many failed attempts. Try again later."
          : "Invalid username or password.";
      setError(message);
      setSubmitting(false);
    }
  }

  return (
    <EntryShell name="login">
      <form onSubmit={handleSubmit} className="j1-form" aria-busy={submitting}>
        <div>
          <h2 className="j1-note" style={{ fontSize: 24, color: "#ecc56a" }}>
            Welcome back
          </h2>
          <p className="j1-note">The instrument is ready.</p>
        </div>
        <div className="j1-tabs" aria-label="Sign in with">
          {(["username", "email"] as const).map((key) => (
            <button
              key={key}
              type="button"
              disabled={submitting}
              aria-pressed={tab === key}
              onClick={() => {
                setTab(key);
                setIdentifier("");
                setError(null);
              }}
            >
              {key === "username" ? "Username" : "Email"}
            </button>
          ))}
        </div>
        <label className="j1-field">
          <span>{tab === "username" ? "Username" : "Email"}</span>
          <input
            required
            type={tab === "email" ? "email" : "text"}
            autoComplete={tab === "email" ? "email" : "username"}
            maxLength={254}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            disabled={submitting}
          />
        </label>
        <PasswordField
          label="Password"
          value={password}
          onChange={setPassword}
          disabled={submitting}
        />
        {error && (
          <p role="alert" className="j1-error">
            {error}
          </p>
        )}
        <button type="submit" className="j1-btn" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <Link href="/login/recovery">Forgotten password</Link>
          <Link href="/login/request-access">Request access</Link>
        </div>
      </form>
    </EntryShell>
  );
}
