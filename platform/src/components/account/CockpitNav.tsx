"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { PageName } from "@/components/journey1/Titles";
const root = "/account/ai-cockpit";
const items = [
  ["AI Cockpit", "", "aiCockpit"],
  ["AI Console", "/console", "aiConsole"],
  ["AI Personas", "/personas", "personas"],
  ["My Observatory", "/observatory", "myObservatory"],
  ["Consumption", "/consumption", "consumption"],
] as const;
const activityFilters = [
  "from",
  "to",
  "channel",
  "purpose",
  "provider",
  "model",
  "connectionId",
  "aggregation",
];
export function CockpitNav({ active, consoleEnabled }: { active: PageName; consoleEnabled: boolean }) {
  const search = useSearchParams();
  const scope = new URLSearchParams();
  for (const key of activityFilters) {
    const value = search.get(key);
    if (value) scope.set(key, value);
  }
  return (
    <nav aria-label="AI Cockpit sections" className="j5-tabs">
      {items.filter(([, suffix]) => consoleEnabled || suffix !== "/console").map(([label, suffix, name]) => {
        const href = root + suffix;
        const query =
          ["/observatory", "/consumption"].includes(suffix) && scope.size
            ? "?" + scope.toString()
            : "";
        return (
          <Link
            key={href}
            href={href + query}
            aria-current={active === name ? "page" : undefined}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
