"use client";
import { useAccountPreferences } from "./AccountPreferencesProvider";
import { DefaultPersonaSelect } from "./DefaultPersonaSelect";
import type { AccountPreferences } from "@/lib/account/preference-types";
export function PreferencesForm() {
  const account = useAccountPreferences();
  if (!account) return null;
  const p = account.preferences,
    update = account.update;
  const pins = [
    ["navPinned", "Navigation rail", "Left · desktop"],
    ["historyPinned", "Reading history", "Consultation · left"],
    ["evidencePinned", "Evidence panel", "Consultation · right"],
  ] as const;
  return (
    <div className="j5-narrow j5-stack">
      <section className="j5-panel j5-stack">
        <h2>Titles and panels</h2>
        {!account.loaded && <p role="status">Loading saved preferences…</p>}
        <label className="j5-setting">
          Page titles{" "}
          <select
            aria-label="Page titles"
            value={p.titles}
            onChange={(e) =>
              void update({ titles: e.target.value as "en" | "sa" })
            }
          >
            <option value="en">English first</option>
            <option value="sa">Sanskrit first</option>
          </select>
        </label>
        <p className="j1-note">
          Mirrors the header control. The other name stays directly beneath the
          heading.
        </p>
        {pins.map(([key, label, note]) => (
          <div key={key}>
            <label className="j5-setting">
              {label}
              <select
                aria-label={label}
                value={p[key] ? "pinned" : "automatic"}
                onChange={(e) =>
                  void update({ [key]: e.target.value === "pinned" })
                }
              >
                <option value="automatic">Automatic</option>
                <option value="pinned">Pinned</option>
              </select>
            </label>
            <small className="j1-note">{note}</small>
          </div>
        ))}
        <label className="j5-setting">
          Grounding placement{" "}
          <select
            aria-label="Grounding placement"
            value={p.grounding}
            onChange={(e) =>
              void update({ grounding: e.target.value as "right" | "inline" })
            }
          >
            <option value="right">Right pane</option>
            <option value="inline">Inline</option>
          </select>
        </label>
        <label className="j5-setting">
          Reduce motion{" "}
          <input
            type="checkbox"
            aria-label="Reduce motion"
            checked={p.reducedMotion}
            onChange={(e) => void update({ reducedMotion: e.target.checked })}
          />
        </label>
        <p className="j1-note">
          Your system motion preference also applies. Panel controls in
          Consultation update these same settings.
        </p>
      </section>
      <section className="j5-panel j5-stack">
        <h2>Reading</h2>
        <label className="j5-setting">
          Reading size{" "}
          <select
            aria-label="Reading size"
            value={p.textScale}
            onChange={(e) =>
              void update({
                textScale: Number(
                  e.target.value,
                ) as AccountPreferences["textScale"],
              })
            }
          >
            <option value={0.875}>Compact</option>
            <option value={1}>Comfortable</option>
            <option value={1.125}>Large</option>
            <option value={1.25}>Extra large</option>
          </select>
        </label>
        <label className="j5-setting">
          Reading depth{" "}
          <select
            aria-label="Reading depth"
            value={p.readingDepth}
            onChange={(e) =>
              void update({
                readingDepth: e.target
                  .value as AccountPreferences["readingDepth"],
              })
            }
          >
            <option value="auto">Auto</option>
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep (Recommended)</option>
          </select>
        </label>
        <p className="j1-note">
          New questions start here; your per-question choice takes precedence.
          Deep requests the completeness path; the other choices currently let
          the planner choose scope.
        </p>
        <DefaultPersonaSelect />
      </section>
      <p className="j1-note">
        Changes save as you make them. AI Personas owns the default persona; AI
        Console owns the exact AI default.
      </p>
    </div>
  );
}
