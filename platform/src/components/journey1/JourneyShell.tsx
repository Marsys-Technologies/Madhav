"use client";
import { useState, useSyncExternalStore, useRef, useEffect } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutGrid,
  ChartLine,
  Map,
  UserRound,
  Shield,
  Pin,
  PinOff,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { Signature } from "./Signature";
import { PageTitle, TitleToggle, PAGE_NAMES, type PageName } from "./Titles";
const PIN_KEY = "madhav.pref.global-nav-pinned";
function subscribe(fn: () => void) {
  window.addEventListener("storage", fn);
  window.addEventListener("madhav:pins", fn);
  return () => {
    window.removeEventListener("storage", fn);
    window.removeEventListener("madhav:pins", fn);
  };
}
function pinSnapshot() {
  try {
    return localStorage.getItem(PIN_KEY) === "true";
  } catch {
    return false;
  }
}
export function JourneyShell({
  children,
  user,
  role,
  chartId,
  fallback,
}: {
  children: ReactNode;
  user: { uid: string; name?: string; email?: string };
  role: string;
  chartId?: string;
  fallback?: ReactNode;
}) {
  const path = usePathname();
  const router = useRouter();
  const pinned = useSyncExternalStore(subscribe, pinSnapshot, () => false);
  const [hover, setHover] = useState(false),
    [mobile, setMobile] = useState(false);
  const isJourney1 =
    !chartId ||
    path === `/clients/${chartId}` ||
    path === `/clients/${chartId}/edit` ||
    path === `/clients/${chartId}/reports` ||
    path === `/clients/${chartId}/pariprashna`;
  const railRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!mobile) return;
    const previous = document.activeElement as HTMLElement | null;
    railRef.current?.querySelector<HTMLElement>("button,a")?.focus();
    function trap(event: KeyboardEvent) {
      if (event.key !== "Tab") return;
      const targets = Array.from(
        railRef.current?.querySelectorAll<HTMLElement>("button,a[href]") ?? [],
      );
      const first = targets[0],
        last = targets.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      }
      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [mobile]);
  if (!isJourney1 && fallback) return fallback;
  const open = pinned || hover || mobile;
  const items: { name: PageName; href: string; icon: typeof LayoutGrid }[] = [
    { name: "charts", href: "/dashboard", icon: LayoutGrid },
  ];
  if (process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_METERING_ENABLED === "true")
    items.push({ name: "consumption", href: "/usage", icon: ChartLine });
  if (role === "super_admin")
    items.push(
      { name: "atlas", href: "/information/atlas", icon: Map },
      { name: "admin", href: "/admin", icon: Shield },
    );
  // Account setup is a real self-service route; unreviewed account work remains deferred.
  items.push({ name: "account", href: "/setup-account", icon: UserRound });
  return (
    <div
      className="j1 j1-shell"
      data-testid="chart-page-frame"
      data-chart-id={chartId}
      data-workspace={path === `/clients/${chartId}/pariprashna` ? "consultation" : undefined}
    >
      <a
        href="#journey-main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[60] focus:bg-black focus:p-3"
      >
        Skip to main content
      </a>
      {mobile && (
        <button
          aria-label="Close navigation"
          className="j1-veil"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="j1-rail-space" data-pinned={pinned}>
        <nav
          ref={railRef}
          className="j1-rail"
          aria-label="Primary navigation"
          data-open={open}
          data-mobile={mobile}
          onMouseEnter={() => setHover(true)}
          onMouseLeave={() => setHover(false)}
          onFocus={() => setHover(true)}
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node))
              setHover(false);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setMobile(false);
              setHover(false);
            }
          }}
        >
          <button
            className="j1-icon j1-mobile-dismiss"
            aria-label="Close navigation"
            onClick={() => setMobile(false)}
          >
            <X size={20} />
          </button>
          <button
            className="j1-icon"
            aria-label={
              pinned ? "Release navigation pin" : "Pin navigation open"
            }
            aria-pressed={pinned}
            onClick={() => {
              try {
                localStorage.setItem(PIN_KEY, String(!pinned));
              } catch {}
              window.dispatchEvent(new Event("madhav:pins"));
            }}
          >
            {pinned ? <PinOff size={18} /> : <Pin size={18} />}
          </button>
          {items.map(({ name, href, icon: Icon }) => (
            <Link
              key={name}
              href={href}
              aria-label={PAGE_NAMES[name][1]}
              title={PAGE_NAMES[name][1]}
              aria-current={path === href ? "page" : undefined}
              onClick={() => setMobile(false)}
            >
              <Icon size={22} />
              <PageTitle name={name} as="span" compact />
            </Link>
          ))}
          <button
            type="button"
            className="j1-icon"
            aria-label="Sign out"
            style={{ marginTop: "auto" }}
            onClick={async () => {
              const r = await fetch("/api/auth/session", { method: "DELETE" });
              if (!r.ok) return;
              const [{ signOut }, { auth }] = await Promise.all([
                import("firebase/auth"),
                import("@/lib/firebase/client"),
              ]);
              await signOut(auth).catch(() => {});
              router.push("/login");
              router.refresh();
            }}
          >
            <LogOut size={20} />
          </button>
        </nav>
      </div>
      <div className="j1-shell-body">
        <header className="j1-topbar">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              className="j1-icon j1-mobile-menu"
              aria-label="Open navigation"
              aria-expanded={mobile}
              onClick={() => setMobile(true)}
            >
              <Menu size={20} />
            </button>
            <Link href="/dashboard" aria-label="Madhav — Birth Charts">
              <Signature />
            </Link>
          </div>
          <div className="j1-topbar-actions">
            <span className="j1-note">{user.name ?? user.email}</span>
            <TitleToggle />
            <Link
              className="j1-icon"
              href="/setup-account"
              aria-label="My Account"
            >
              <UserRound size={20} />
            </Link>
          </div>
        </header>
        <main className="j1-content" id="journey-main">
          {children}
        </main>
      </div>
    </div>
  );
}
