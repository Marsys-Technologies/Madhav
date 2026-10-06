"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAiAccountState } from "./useAiAccountState";
import { describeDefault } from "@/components/ai-console/default-summary";
import { usePersonas } from "@/hooks/usePersonas";
import { useObservatoryScope } from "@/components/observatory/ObservatoryScope";
import { CLASSICAL_PERSONA } from "@/lib/account/classical-persona";
export function CockpitIndex() {
  const ai = useAiAccountState(),
    personas = usePersonas(),
    scope = useObservatoryScope();
  const usage = useQuery({
    queryKey: ["j5-usage-summary", scope.userId, scope.from, scope.to],
    queryFn: async ({ signal }) => {
      const r = await fetch(
        `/api/usage?from=${encodeURIComponent(scope.from)}&to=${encodeURIComponent(scope.to)}&view=summary`,
        { signal, cache: "no-store" },
      );
      if (!r.ok) throw Error("Activity unavailable");
      return r.json() as Promise<{
        transport_attempts: number;
        cli_executions: number;
        provider_transport_cost_usd: string | null;
      }>;
    },
  });
  const defaultPersona =
    personas.personas.find((p) => p.is_default)?.name ?? CLASSICAL_PERSONA.name;
  const cards = [
    [
      "Saṃyojana",
      "AI Console",
      "Provider connections, local CLI access, custom configurations, four roles and one exact default.",
      ai.error
        ? "AI settings could not be loaded."
        : "Default: " + describeDefault(ai.state, ai.clis),
      "console",
    ],
    [
      "Saṃvāda Śailī",
      "AI Personas",
      "Saved instructions and response styles; the default persona.",
      personas.error ??
        (personas.loading
          ? "Loading personas…"
          : `${personas.personas.length} saved · default ${defaultPersona}`),
      "personas",
    ],
    [
      "Sva Nirīkṣaṇa",
      "My Observatory",
      "Your own activity, outcomes, connection and model.",
      usage.isError
        ? "Activity could not be loaded."
        : usage.data
          ? `${usage.data.transport_attempts.toLocaleString("en-IN")} API calls · ${usage.data.cli_executions.toLocaleString("en-IN")} CLI executions`
          : "Loading activity…",
      "observatory",
    ],
    [
      "Upayoga",
      "Consumption",
      "Usage and cost from conversations to questions to recorded calls.",
      usage.isError
        ? "Cost could not be loaded."
        : usage.data?.provider_transport_cost_usd != null
          ? `$${Number(usage.data.provider_transport_cost_usd).toFixed(4)} provider-reported API cost`
          : "Provider cost not reported",
      "consumption",
    ],
  ] as const;
  return (
    <>
      <p className="j1-note">
        Everything about how Madhav answers for you and what it has done for
        you, at account level.
      </p>
      <div className="j5-grid">
        {cards.map(([sa, title, description, summary, suffix]) => (
          <Link
            className="j5-panel j5-destination"
            key={suffix}
            href={"/account/ai-cockpit/" + suffix}
          >
            <p className="j5-eyebrow">{sa}</p>
            <h2>{title}</h2>
            <p className="j1-note">{description}</p>
            <p className="j5-card-summary">{summary}</p>
          </Link>
        ))}
      </div>
      <p className="j1-note">
        Activity summaries cover the last 30 days. The Sanskrit names for AI
        Cockpit and My Observatory are provisional.
      </p>
    </>
  );
}
