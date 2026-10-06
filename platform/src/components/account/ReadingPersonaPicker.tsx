"use client";
import { usePersonas } from "@/hooks/usePersonas";
import { CLASSICAL_PERSONA } from "@/lib/account/classical-persona";
export function ReadingPersonaPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const { personas, loading, error, reload } = usePersonas();
  const defaultName =
    personas.find((p) => p.is_default)?.name ?? CLASSICAL_PERSONA.name;
  return (
    <label className="pp-grounding-placement">
      Persona{" "}
      <select
        aria-label="Reading persona"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="default">
          Default · {error ? "unavailable" : loading ? "loading…" : defaultName}
        </option>
        {personas.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      {error && (
        <button type="button" onClick={reload}>
          Retry personas
        </button>
      )}
    </label>
  );
}
