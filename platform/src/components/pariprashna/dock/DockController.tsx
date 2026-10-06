"use client";
import { useAccountPreferences } from '@/components/account/AccountPreferencesProvider';
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
export type EvidenceTab = "Grounding" | "Windows" | "History";
type ActiveCitation = { turnId: string; n: number };
interface DockControllerValue {
  open: boolean;
  setOpen: (open: boolean) => void;
  leftOpen: boolean;
  setLeftOpen: (open: boolean) => void;
  pinned: boolean;
  leftPinned: boolean;
  setPinned: (pin: boolean) => void;
  setLeftPinned: (pin: boolean) => void;
  tab: EvidenceTab;
  setTab: (tab: EvidenceTab) => void;
  placement: "inline" | "pane";
  setPlacement: (placement: "inline" | "pane") => void;
  activeCitation: ActiveCitation | null;
  mobileSheetCitation: ActiveCitation | null;
  closeMobileSheet: () => void;
  openToCitation: (turnId: string, n: number) => void;
}
const DockContext = createContext<DockControllerValue | null>(null);
const volatile = new Map<string, string>();
function subscribe(notify: () => void) {
  window.addEventListener("storage", notify);
  window.addEventListener("madhav:consultation-preferences", notify);
  return () => {
    window.removeEventListener("storage", notify);
    window.removeEventListener("madhav:consultation-preferences", notify);
  };
}
const narrow = () =>
  typeof window !== "undefined" &&
  window.matchMedia?.("(max-width: 900px)").matches;
export function DockControllerProvider({
  children,
  defaultOpen = false,
  userId = "preview",
}: {
  children: ReactNode;
  defaultOpen?: boolean;
  userId?: string;
}) {
  const account = useAccountPreferences();
  const key = `madhav.pref.consultation.${userId}`;
  const snapshot = useCallback(() => {
    try {
      return localStorage.getItem(key) ?? volatile.get(key) ?? "{}";
    } catch {
      return volatile.get(key) ?? "{}";
    }
  }, [key]);
  const raw = useSyncExternalStore(subscribe, snapshot, () => "{}");
  const preferences = useMemo(() => {
    try {
      return JSON.parse(raw) as {
        rightPinned?: boolean;
        leftPinned?: boolean;
        placement?: string;
      };
    } catch {
      return {};
    }
  }, [raw]);
  const pinned = account?.preferences.evidencePinned ?? (preferences.rightPinned === true),
    leftPinned = account?.preferences.historyPinned ?? (preferences.leftPinned === true);
  const placement: "inline" | "pane" =
    (account?.preferences.grounding ?? preferences.placement) === "inline" ? "inline" : "pane";
  const [openOverride, setOpenState] = useState<boolean | null>(null),
    [leftOverride, setLeftOpenState] = useState<boolean | null>(null);
  const open = openOverride ?? ((pinned || defaultOpen) && !narrow()),
    leftOpen = leftOverride ?? (leftPinned && !narrow());
  const [tab, setTab] = useState<EvidenceTab>("Grounding");
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(
    null,
  );
  const [mobileSheetCitation, setMobileSheetCitation] =
    useState<ActiveCitation | null>(null);
  const save = useCallback(
    (changes: Record<string, unknown>) => {
      let previous: Record<string, unknown> = {};
      try {
        previous = JSON.parse(snapshot());
      } catch {}
      const value = JSON.stringify({ ...previous, ...changes });
      volatile.set(key, value);
      try {
        localStorage.setItem(key, value);
      } catch {}
      window.dispatchEvent(new Event("madhav:consultation-preferences"));
    },
    [key, snapshot],
  );
  const setOpen = useCallback((next: boolean) => {
    setOpenState(next);
    if (next && narrow()) setLeftOpenState(false);
  }, []);
  const setLeftOpen = useCallback((next: boolean) => {
    setLeftOpenState(next);
    if (next && narrow()) setOpenState(false);
  }, []);
  const setPinned = useCallback(
    (next: boolean) => {
      if (next) setOpen(true);
      if (account) void account.update({evidencePinned: next});
      else save({ rightPinned: next });
    },
    [account, save, setOpen],
  );
  const setLeftPinned = useCallback(
    (next: boolean) => {
      if (next) setLeftOpen(true);
      if (account) void account.update({historyPinned: next});
      else save({ leftPinned: next });
    },
    [account, save, setLeftOpen],
  );
  const setPlacement = useCallback(
    (next: "inline" | "pane") => { if(account) void account.update({grounding:next === 'pane' ? 'right' : 'inline'}); else save({ placement: next }); },
    [account, save],
  );
  const openToCitation = useCallback(
    (turnId: string, n: number) => {
      setTab("Grounding");
      setActiveCitation({ turnId, n });
      if (narrow()) setMobileSheetCitation({ turnId, n });
      else setOpen(true);
    },
    [setOpen],
  );
  const closeMobileSheet = useCallback(() => setMobileSheetCitation(null), []);
  const value = useMemo(
    () => ({
      open,
      setOpen,
      leftOpen,
      setLeftOpen,
      pinned,
      leftPinned,
      setPinned,
      setLeftPinned,
      tab,
      setTab,
      placement,
      setPlacement,
      activeCitation,
      mobileSheetCitation,
      closeMobileSheet,
      openToCitation,
    }),
    [
      open,
      setOpen,
      leftOpen,
      setLeftOpen,
      pinned,
      leftPinned,
      setPinned,
      setLeftPinned,
      tab,
      placement,
      setPlacement,
      activeCitation,
      mobileSheetCitation,
      closeMobileSheet,
      openToCitation,
    ],
  );
  return <DockContext.Provider value={value}>{children}</DockContext.Provider>;
}
export function useDockController() {
  const value = useContext(DockContext);
  if (!value)
    throw new Error(
      "useDockController must be used within DockControllerProvider",
    );
  return value;
}
export function useOptionalDockController() {
  return useContext(DockContext);
}
