import Link from "next/link";
import type { AccountProfile } from "@/lib/account/profile";
import { AccountHeading } from "./AccountHeading";
const destinations = [
  [
    "Vyakti Vivaraṇa",
    "Profile",
    "Username, name and your sign-in e-mail.",
    "profile",
  ],
  [
    "Surakṣā",
    "Security",
    "Change your password; sign out of all sessions.",
    "security",
  ],
  [
    "Abhiruci",
    "Preferences",
    "Page titles, panels, motion, reading size and depth.",
    "preferences",
  ],
  [
    "Niyantraṇa Kakṣa",
    "AI Cockpit",
    "AI Console, AI Personas, My Observatory and Consumption.",
    "ai-cockpit",
  ],
] as const;
export function AccountOverview({ profile }: { profile: AccountProfile }) {
  return (
    <>
      <AccountHeading name="account" />
      <section className="j5-panel j5-identity">
        <span className="j5-avatar" aria-hidden>
          {(profile.name ?? profile.username ?? "A").slice(0, 1)}
        </span>
        <div>
          <h2>{profile.name ?? profile.username ?? "My Account"}</h2>
          <p className="j1-note">
            {profile.username ? "@" + profile.username + " · " : ""}
            {profile.email}
          </p>
          {profile.role && (
            <p className="j1-note">{profile.role.replaceAll("_", " ")}</p>
          )}
        </div>
        <Link className="j1-btn j1-btn-secondary" href="/account/profile">
          Edit profile
        </Link>
      </section>
      <div className="j5-grid">
        {destinations.map(([sa, en, description, suffix]) => (
          <Link
            className="j5-panel j5-destination"
            key={suffix}
            href={"/account/" + suffix}
          >
            <p className="j5-eyebrow">{sa}</p>
            <h2>{en}</h2>
            <p className="j1-note">{description}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
