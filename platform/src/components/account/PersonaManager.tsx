"use client";
import { useState } from "react";
import { usePersonas } from "@/hooks/usePersonas";
import { PersonaCard } from "@/app/settings/personas/PersonaCard";
import { PersonaForm } from "@/app/settings/personas/PersonaForm";
import { CLASSICAL_PERSONA } from "@/lib/account/classical-persona";
import { useAiAccountState } from "./useAiAccountState";
import { describeDefault } from "@/components/ai-console/default-summary";
import type { PersonaCreate } from "@/types/personas";
export function PersonaManager() {
  const { personas, loading, error, reload, create, update, remove } =
    usePersonas();
  const [creating, setCreating] = useState(false),
    [failure, setFailure] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  const ai = useAiAccountState();
  async function baseline() {
    setBusy(true);
    setFailure(null);
    try {
      if (
        !(await create({
          name: CLASSICAL_PERSONA.name,
          system_prompt: CLASSICAL_PERSONA.system_prompt,
          default_style: "acharya",
          default_stack: null,
          is_default: true,
        }))
      )
        setFailure("Recommended persona could not be saved. Try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="j5-stack">
      <div className="j5-actions">
        <p className="j1-note">
          Saved instructions and response styles. One default is shared with
          Preferences.
        </p>
        <button
          className="j1-btn"
          onClick={() => setCreating(true)}
          disabled={creating || loading}
        >
          New Persona
        </button>
      </div>
      <p className="j1-note">
        Use account AI default:{" "}
        {ai.error ? "Settings unavailable" : describeDefault(ai.state, ai.clis)}
        . Saved legacy AI overrides remain available for the older reader.
      </p>
      {(error || failure) && (
        <p className="j1-error" role="alert">
          {error ?? failure}{" "}
          {error && (
            <button className="j1-btn j1-btn-secondary" onClick={reload}>
              Retry
            </button>
          )}
        </p>
      )}
      {loading && <p role="status">Loading personas…</p>}
      {creating && (
        <section className="j5-panel">
          <h2>New Persona</h2>
          <PersonaForm
            onCancel={() => setCreating(false)}
            onSave={async (data) => {
              if (!(await create(data as PersonaCreate))) throw Error("save");
              setCreating(false);
            }}
          />
        </section>
      )}
      {!loading && !error && !personas.length && (
        <section className="j5-panel">
          <h2>Classical Parāśari</h2>
          <p className="j1-note">
            This recommended baseline is used until you save a default persona.
            It explains supported evidence and keeps uncertainty visible.
          </p>
          <button
            className="j1-btn j1-btn-secondary"
            disabled={busy}
            onClick={() => void baseline()}
          >
            Save recommended persona
          </button>
        </section>
      )}
      <div className="j5-stack">
        {personas.map((persona) => (
          <PersonaCard
            key={persona.id}
            persona={persona}
            isLast={personas.length === 1}
            onUpdate={async (id, data) => {
              if (!(await update(id, data))) throw Error("save");
            }}
            onDelete={async (id) => {
              const result = await remove(id);
              if (!result.ok) {
                setFailure(
                  result.lastPersona
                    ? "Keep at least one saved persona."
                    : "Persona could not be deleted. Try again.",
                );
                throw Error("delete");
              }
            }}
          />
        ))}
      </div>
    </div>
  );
}
