"use client";

import { useSyncExternalStore } from "react";
import { Languages } from "lucide-react";

export const PAGE_NAMES = {
  login: ["Praveśa", "Sign In"],
  request: ["Praveśa Nivedana", "Request Access"],
  recovery: ["Punarpraveśa", "Account Recovery"],
  reset: ["Punarpraveśa", "Reset Password"],
  charts: ["Jātakas", "Birth Charts"],
  new: ["Nava Jātaka", "New Chart"],
  overview: ["Jātaka Darśana", "Chart Overview"],
  details: ["Jātaka Vivaraṇa", "Chart Details"],
  access: ["Jātaka Adhikāra", "Chart Access"],
  consultation: ["Paripraśna", "Consultation"],
  review: ["Samīkṣā", "Prediction Review"],
  preparation: ["Nirmāṇa", "Chart Preparation"],
  almanac: ["Jātaka Pañcāṅga", "Personal Almanac"],
  events: ["Jīvana Vṛttānta", "Life Events"],
  periods: ["Daśā & Gocara", "Periods & Transits"],
  reports: ["Jātaka Prativedana", "Reports"],
  cockpit: ["Niyantraṇa", "Cockpit"],
  consumption: ["Upayoga", "Consumption"],
  atlas: ["Jñānakośa", "Atlas"],
  account: ["Ātmaparicaya", "My Account"],
  admin: ["Praśāsana", "Administration"],
} as const;
export type PageName = keyof typeof PAGE_NAMES;
const KEY = "madhav.pref.titles";
let volatileLanguage: "en" | "sa" = "sa";
function subscribe(fn: () => void) {
  window.addEventListener("storage", fn);
  window.addEventListener("madhav:titles", fn);
  return () => {
    window.removeEventListener("storage", fn);
    window.removeEventListener("madhav:titles", fn);
  };
}
function snapshot(): "en" | "sa" {
  try {
    return localStorage.getItem(KEY) === "en" ? "en" : "sa";
  } catch {
    return volatileLanguage;
  }
}
export function useTitleLanguage() {
  return useSyncExternalStore(subscribe, snapshot, () => "sa" as const);
}
export function TitleToggle() {
  const mode = useTitleLanguage();
  const label = `Show page titles in ${mode === "en" ? "Sanskrit" : "English"}`;
  return (
    <button
      type="button"
      className="j1-icon"
      aria-label={label}
      title={label}
      onClick={() => {
        volatileLanguage = mode === "en" ? "sa" : "en";
        try {
          localStorage.setItem(KEY, volatileLanguage);
        } catch {
          /* Retain the choice in memory when storage is unavailable. */
        }
        window.dispatchEvent(new Event("madhav:titles"));
      }}
    >
      <Languages size={20} aria-hidden="true" />
    </button>
  );
}
export function PageTitle({
  name,
  as: Tag = "h1",
  compact = false,
}: {
  name: PageName;
  as?: "h1" | "h2" | "span";
  compact?: boolean;
}) {
  const mode = useTitleLanguage();
  const [sa, en] = PAGE_NAMES[name];
  return (
    <Tag
      aria-label={`${mode === "en" ? en : sa} ${mode === "en" ? sa : en}`}
      className={`j1-title ${compact ? "j1-title-small" : ""}`}
    >
      <span>{mode === "en" ? en : sa}</span>
      <small>{mode === "en" ? sa : en}</small>
    </Tag>
  );
}
