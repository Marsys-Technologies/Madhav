"use client";
import { useState } from "react";
import Link from "next/link";
import { usePersonas } from "@/hooks/usePersonas";
import { CLASSICAL_PERSONA } from "@/lib/account/classical-persona";
export function DefaultPersonaSelect() {
  const { personas, loading, error, reload, update, create } = usePersonas();
  const [busy, setBusy] = useState(false),
    [saveError, setSaveError] = useState<string | null>(null);
  const current = personas.find((p) => p.is_default)?.id ?? "classical";
  async function choose(id: string) {
    if (busy) return;
    setBusy(true);
    setSaveError(null);
    try {
      const baseline = personas.find(
        (p) =>
          p.system_prompt === CLASSICAL_PERSONA.system_prompt &&
          p.default_stack === null,
      );
      const result =
        id === "classical"
          ? baseline
            ? await update(baseline.id, { is_default: true })
            : await create({
                name: CLASSICAL_PERSONA.name,
                system_prompt: CLASSICAL_PERSONA.system_prompt,
                default_style: CLASSICAL_PERSONA.default_style,
                default_stack: null,
                is_default: true,
              })
          : await update(id, { is_default: true });
      if (!result)
        setSaveError("Default persona could not be saved. Try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="j1-field">
      <label htmlFor="j5-default-persona">Default persona</label>
      <select
        id="j5-default-persona"
        value={current}
        disabled={loading || busy || !!error}
        onChange={(e) => void choose(e.target.value)}
      >
        <option value="classical">
          Classical Parāśari · recommended baseline
        </option>
        {personas.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <p className="j1-note">
        New readings use this default. Manage the same list under{" "}
        <Link href="/account/ai-cockpit/personas">AI Personas</Link>.
      </p>
      {(error || saveError) && (
        <p className="j1-error" role="alert">
          {error ?? saveError}{" "}
          {error && (
            <button type="button" onClick={reload}>
              Retry
            </button>
          )}
        </p>
      )}
    </div>
  );
}
