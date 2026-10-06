import { useSyncExternalStore } from "react";
const subscribe = (fn: () => void) => {
  window.addEventListener("popstate", fn);
  return () => window.removeEventListener("popstate", fn);
};
const snapshot = () => window.location.search;
export function useSearchParams() {
  return new URLSearchParams(
    useSyncExternalStore(subscribe, snapshot, snapshot),
  );
}
export function usePathname() {
  return useSearchParams().get("screen") ?? "/account/profile";
}
export function navigate(href: string) {
  const next = new URL(href, window.location.origin),
    query = new URLSearchParams(next.search);
  query.set("screen", next.pathname);
  window.history.pushState({}, "", `${window.location.pathname}?${query}`);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
export function useRouter() {
  return {
    replace: navigate,
    push: navigate,
    refresh: () => window.dispatchEvent(new PopStateEvent("popstate")),
  };
}
