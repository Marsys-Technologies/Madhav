/** Local-only source component replay. No login bypass, credentials or provider calls. */
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { JourneyShell } from "@/components/journey1/JourneyShell";
import { ObservatoryScope } from "@/components/observatory/ObservatoryScope";
import { AccountHeading } from "@/components/account/AccountHeading";
import { AccountOverview } from "@/components/account/AccountOverview";
import { ProfileForm } from "@/components/account/ProfileForm";
import { SecurityForm } from "@/components/account/SecurityForm";
import { PreferencesForm } from "@/components/account/PreferencesForm";
import { PersonaManager } from "@/components/account/PersonaManager";
import { CockpitIndex } from "@/components/account/CockpitIndex";
import { PersonalActivity } from "@/components/account/PersonalActivity";
import { AIConsole } from "@/components/ai-console/AIConsole";
import { DEFAULT_PREFERENCES } from "@/lib/account/preference-types";
import { fixtureActivity } from "./activity-fixture";
import { usePathname } from "./navigation";
import "@/app/globals.css";
import "@/app/journey1.css";
import "@/app/account/account.css";
const profile = {
  id: "fictional-account",
  name: "Fictional Review User",
  username: "review_user",
  email: "review@example.invalid",
  role: "guest",
  status: "active",
};
let prefs = { ...DEFAULT_PREFERENCES };
let personas: unknown[] = [];
window.fetch = async (input, init) => {
  const raw =
    typeof input === "string"
      ? input
      : input instanceof URL
        ? input.href
        : input.url;
  const u = new URL(raw, window.location.origin);
  if (u.origin !== window.location.origin || !u.pathname.startsWith("/api/"))
    throw Error("Fixture blocks external requests");
  const body = typeof init?.body === "string" ? JSON.parse(init.body) : {};
  if (u.pathname === "/api/account/preferences") {
    if (init?.method === "PATCH") prefs = { ...prefs, ...body };
    return Response.json({ preferences: prefs });
  }
  if (u.pathname === "/api/account/username")
    return Response.json({ available: true, username: body.username });
  if (u.pathname === "/api/account/profile")
    return Response.json({ profile: { ...profile, ...body } });
  if (u.pathname === "/api/personas") {
    if (init?.method === "POST")
      personas = [...personas, { id: crypto.randomUUID(), ...body }];
    return Response.json(
      init?.method === "POST" ? personas.at(-1) : { personas },
    );
  }
  if (u.pathname === "/api/ai-console")
    return Response.json({
      connections: [
        {
          id: "11111111-1111-4111-8111-111111111111",
          providerId: "openrouter",
          name: "Fictional OpenRouter",
          maskedSuffix: "fake",
          validationState: "validated",
          confirmedValid: true,
          lastValidatedAt: new Date().toISOString(),
          lastCheckedAt: new Date().toISOString(),
          deletedAt: null,
          catalogRefreshedAt: new Date().toISOString(),
        },
      ],
      models: [
        {
          connectionId: "11111111-1111-4111-8111-111111111111",
          modelId: "anthropic/fictional",
          displayName: "Fictional reading model",
          compatibleRoles: ["synthesizer", "planner", "deep_planner", "worker"],
          supportsTools: true,
          supportsStructuredOutput: true,
          available: true,
          userSelected: true,
          plainTestedAt: new Date().toISOString(),
        },
      ],
      configurations: [],
      defaultChoice: {
        kind: "provider_model",
        connectionId: "11111111-1111-4111-8111-111111111111",
        modelId: "anthropic/fictional",
      },
      validationDisclosure: "Fictional preview: no provider requests.",
    });
  if (u.pathname === "/api/ai-console/clis") return Response.json({ clis: [] });
  if (u.pathname === "/api/usage")
    return Response.json(fixtureActivity(u.searchParams));
  return Response.json(
    { error: "fixture_action_unavailable" },
    { status: 503 },
  );
};
const client = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});
function App() {
  const path = usePathname(),
    cockpit = path.startsWith("/account/ai-cockpit"),
    name = path.endsWith("preferences")
      ? "preferences"
      : path.endsWith("security")
        ? "security"
        : path.endsWith("observatory")
          ? "myObservatory"
          : path.endsWith("consumption")
            ? "consumption"
            : path.endsWith("console")
              ? "aiConsole"
              : path.endsWith("personas")
                ? "personas"
                : cockpit
                  ? "aiCockpit"
                  : "profile";
  return (
    <QueryClientProvider client={client}>
      <JourneyShell
        user={{ uid: profile.id, name: profile.name, email: profile.email }}
        role="guest"
      >
        <ObservatoryScope userId={profile.id} admin={false}>
          <div className="j5-account">
            <p className="j1-note">
              Fictional component preview · persistence and navigation simulated
              · no authenticated acceptance
            </p>
            {path !== "/account" && (
              <AccountHeading name={name} cockpit={cockpit} />
            )}
            {path === "/account" ? (
              <AccountOverview profile={profile} />
            ) : name === "profile" ? (
              <ProfileForm initial={profile} />
            ) : name === "security" ? (
              <SecurityForm />
            ) : name === "preferences" ? (
              <PreferencesForm />
            ) : name === "personas" ? (
              <PersonaManager />
            ) : name === "aiConsole" ? (
              <AIConsole embedded />
            ) : name === "aiCockpit" ? (
              <CockpitIndex />
            ) : (
              <PersonalActivity
                view={name === "myObservatory" ? "observatory" : "consumption"}
              />
            )}
          </div>
        </ObservatoryScope>
      </JourneyShell>
    </QueryClientProvider>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
