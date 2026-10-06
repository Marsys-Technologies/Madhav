"use client";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { validateUsername } from "@/lib/auth/username";
import type { AccountProfile } from "@/lib/account/profile";
export function ProfileForm({ initial }: { initial: AccountProfile }) {
  const router = useRouter();
  const [saved, setSaved] = useState(initial),
    [name, setName] = useState(initial.name ?? ""),
    [username, setUsername] = useState(initial.username ?? "");
  const [availability, setAvailability] = useState<
    "idle" | "checking" | "available" | "taken" | "error"
  >("idle");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null),
    [status, setStatus] = useState(""),
    [retry, setRetry] = useState(0);
  const normalized = username.trim().toLowerCase(),
    usernameChanged = normalized !== (saved.username ?? "");
  const invalid = validateUsername(normalized);
  const nameChanged = name.trim() !== (saved.name ?? "");
  useEffect(() => {
    if (!usernameChanged || invalid) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setAvailability("checking");
      fetch(
        `/api/account/username?username=${encodeURIComponent(normalized)}`,
        { signal: controller.signal, cache: "no-store" },
      )
        .then(async (r) => {
          if (!r.ok) throw Error("check");
          return r.json();
        })
        .then((data) => {
          if (!controller.signal.aborted)
            setAvailability(data.available ? "available" : "taken");
        })
        .catch(() => {
          if (!controller.signal.aborted) setAvailability("error");
        });
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [normalized, usernameChanged, invalid, retry]);
  async function save(event: FormEvent) {
    event.preventDefault();
    if (
      busy ||
      invalid ||
      !name.trim() ||
      (usernameChanged && availability !== "available")
    )
      return;
    setBusy(true);
    setError(null);
    setStatus("");
    let usernameSaved = false;
    try {
      if (usernameChanged) {
        const response = await fetch("/api/account/username", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: normalized }),
        });
        if (!response.ok)
          throw Error(
            "Username could not be saved. Check availability and try again.",
          );
        usernameSaved = true;
        setSaved((current) => ({ ...current, username: normalized }));
      }
      if (nameChanged) {
        const response = await fetch("/api/account/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: name.trim() }),
        });
        if (!response.ok)
          throw Error(
            usernameSaved
              ? "Username saved. Name could not be saved. Try saving the name again."
              : "Name could not be saved. Try again.",
          );
        setSaved((current) => ({ ...current, name: name.trim() }));
      }
      setStatus("Profile saved.");
      router.refresh();
    } catch (e) {
      const message =
        e instanceof Error
          ? e.message
          : "Profile could not be saved. Try again.";
      setError(
        usernameSaved && !message.startsWith("Username saved.")
          ? `Username saved. The remaining name update could not be confirmed. Try saving the name again.`
          : message,
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="j5-panel j1-form" onSubmit={save}>
      <label className="j1-field">
        <span>Username</span>
        <input
          aria-label="Username"
          value={username}
          maxLength={32}
          autoComplete="username"
          disabled={busy}
          onChange={(e) => {
            setUsername(e.target.value);
            setAvailability("idle");
            setStatus("");
          }}
          aria-describedby="j5-username-help"
          required
        />
      </label>
      <p id="j5-username-help" className="j1-note" role="status">
        {!usernameChanged
          ? "Your current username"
          : (invalid ??
            {
              idle: "",
              checking: "Checking availability…",
              available: "Available",
              taken: "That username is taken.",
              error: "Availability could not be checked.",
            }[availability])}
      </p>
      <p className="j1-note">
        3–32 characters: letters, numbers, hyphens or underscores. Sign in with
        your username or e-mail.
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
      <label className="j1-field">
        <span>Name</span>
        <input
          aria-label="Name"
          value={name}
          maxLength={100}
          autoComplete="name"
          disabled={busy}
          required
          onChange={(e) => {
            setName(e.target.value);
            setStatus("");
          }}
        />
      </label>
      <label className="j1-field">
        <span>E-mail</span>
        <input
          aria-label="E-mail"
          value={initial.email}
          readOnly
          autoComplete="email"
        />
        <small>Your sign-in and recovery address. It is read-only here.</small>
      </label>
      {error && (
        <p className="j1-error" role="alert">
          {error}
        </p>
      )}
      {status && (
        <p role="status" className="j1-note">
          {status}
        </p>
      )}
      <div className="j5-actions">
        <button
          className="j1-btn"
          disabled={
            busy ||
            !!invalid ||
            !name.trim() ||
            (!usernameChanged && !nameChanged) ||
            (usernameChanged && availability !== "available")
          }
        >
          {busy ? "Saving…" : "Save profile"}
        </button>
        <button
          type="button"
          className="j1-btn j1-btn-secondary"
          disabled={busy || (!usernameChanged && !nameChanged)}
          onClick={() => {
            setName(saved.name ?? "");
            setUsername(saved.username ?? "");
            setError(null);
            setStatus("");
          }}
        >
          Discard changes
        </button>
      </div>
    </form>
  );
}
