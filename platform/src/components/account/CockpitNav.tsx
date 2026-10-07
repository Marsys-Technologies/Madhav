"use client";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
const root = "/account/ai-cockpit";
const items = [
  ["AI Cockpit", ""],
  ["AI Console", "/console"],
  ["AI Personas", "/personas"],
  ["My Observatory", "/observatory"],
  ["Consumption", "/consumption"],
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
export function CockpitNav() {
  const path = usePathname(),
    search = useSearchParams();
  const scope = new URLSearchParams();
  for (const key of activityFilters) {
    const value = search.get(key);
    if (value) scope.set(key, value);
  }
  return (
    <nav aria-label="AI Cockpit sections" className="j5-tabs">
      {items.map(([label, suffix]) => {
        const href = root + suffix;
        const query =
          ["/observatory", "/consumption"].includes(suffix) && scope.size
            ? "?" + scope.toString()
            : "";
        return (
          <Link
            key={href}
            href={href + query}
            aria-current={path === href ? "page" : undefined}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
