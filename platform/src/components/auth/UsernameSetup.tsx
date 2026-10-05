"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { validateUsername } from "@/lib/auth/username";
export function UsernameSetup({
  initialUsername,
  email,
}: {
  initialUsername: string | null;
  email: string;
}) {
  const [value, setValue] = useState(initialUsername ?? ""),
    [availability, setAvailability] = useState<
      "idle" | "checking" | "available" | "taken" | "error"
    >("idle"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const [retry, setRetry] = useState(0);
  const invalid = validateUsername(value);
  useEffect(() => {
    if (invalid) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setAvailability("checking");
      void fetch(
        `/api/account/username?username=${encodeURIComponent(value.trim().toLowerCase())}`,
        { signal: controller.signal },
      )
        .then(async (r) => {
          if (!r.ok) throw new Error();
          return (await r.json()) as { available: boolean };
        })
        .then((v) => {
          if (!controller.signal.aborted)
            setAvailability(v.available ? "available" : "taken");
        })
        .catch(() => {
          if (!controller.signal.aborted) setAvailability("error");
        });
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value, invalid, retry]);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy || invalid || availability !== "available") return;
    setBusy(true);
    setError(null);
    try {
      const r = await fetch("/api/account/username", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: value.trim().toLowerCase() }),
      });
      const body = await r.json();
      if (!r.ok) {
        setError(body.error ?? "Could not save username.");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="j1-form" onSubmit={submit}>
      <p className="j1-note">{email}</p>
      <p className="j1-note">
        {initialUsername
          ? "Update your username."
          : "Your account is approved. Choose the username you’ll use to sign in."}
      </p>
      <label className="j1-field">
        <span>Username</span>
        <input
          required
          maxLength={32}
          autoComplete="username"
          value={value}
          disabled={busy}
          aria-describedby="username-state"
          onChange={(e) => {
            setValue(e.target.value);
            setAvailability("idle");
            setError(null);
          }}
        />
      </label>
      <p id="username-state" role="status" className="j1-note">
        {invalid ??
          {
            idle: "",
            checking: "Checking availability…",
            available: "Available",
            taken: "That username is taken.",
            error: "Availability could not be checked. Try again.",
          }[availability]}
      </p>
      {availability === "error" && (
        <button
          type="button"
          className="j1-btn j1-btn-secondary"
          onClick={() => setRetry((v) => v + 1)}
        >
          Check availability again
        </button>
      )}
      <p className="j1-note">
        3–32 characters: letters, numbers, hyphens, or underscores.
      </p>
      {error && (
        <p className="j1-error" role="alert">
          {error}
        </p>
      )}
      <button
        className="j1-btn"
        disabled={busy || !!invalid || availability !== "available"}
      >
        {busy ? "Saving…" : "Save username and continue"}
      </button>
      {initialUsername && <Link href="/dashboard">← Birth charts</Link>}
    </form>
  );
}
