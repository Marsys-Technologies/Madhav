"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  DEFAULT_PREFERENCES,
  preferencePatchSchema,
  readPreferences,
  type AccountPreferences,
} from "@/lib/account/preference-types";

type ContextValue = {
  ownerId: string;
  preferences: AccountPreferences;
  loaded: boolean;
  error: string | null;
  update: (patch: Partial<AccountPreferences>) => Promise<void>;
  retry: () => void;
};
const Context = createContext<ContextValue | null>(null);
export const useAccountPreferences = () => useContext(Context);

export function AccountPreferencesProvider({
  children,
  userId,
}: {
  children: ReactNode;
  userId: string;
}) {
  return (
    <OwnedPreferences key={userId} userId={userId}>
      {children}
    </OwnedPreferences>
  );
}
function OwnedPreferences({
  children,
  userId,
}: {
  children: ReactNode;
  userId: string;
}) {
  const [preferences, setPreferences] =
    useState<AccountPreferences>(DEFAULT_PREFERENCES);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const dirty = useRef<Partial<AccountPreferences>>({});
  const chosen = useRef<Partial<AccountPreferences>>({});
  const fieldVersions = useRef<
    Partial<Record<keyof AccountPreferences, number>>
  >({});
  const queue = useRef(Promise.resolve());
  const version = useRef(0);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/account/preferences", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw Error("load");
        return response.json();
      })
      .then((data) => {
        if (controller.signal.aborted) return;
        // A saved acknowledgement can arrive before this older GET. Retain choices
        // made while it was pending even when their PATCH has already succeeded.
        setPreferences({
          ...readPreferences(data.preferences),
          ...chosen.current,
          ...dirty.current,
        });
        chosen.current = {};
        setLoaded(true);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError("Preferences could not be loaded.");
          setLoaded(true);
        }
      });
    return () => controller.abort();
  }, [userId, revision]);
  const update = useCallback((patch: Partial<AccountPreferences>) => {
    const parsed = preferencePatchSchema.parse(patch);
    const thisVersion = ++version.current;
    dirty.current = { ...dirty.current, ...parsed };
    chosen.current = { ...chosen.current, ...parsed };
    const keys = Object.keys(parsed) as (keyof AccountPreferences)[];
    for (const key of keys) fieldVersions.current[key] = thisVersion;
    setPreferences((current) => ({ ...current, ...parsed }));
    const save = async () => {
      if (!alive.current) return;
      try {
        const response = await fetch("/api/account/preferences", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(parsed),
        });
        if (!response.ok) throw Error("save");
        const data = await response.json();
        const saved = readPreferences(data.preferences);
        if (!alive.current) return;
        for (const key of keys)
          if (fieldVersions.current[key] === thisVersion)
            delete dirty.current[key];
        if (thisVersion === version.current)
          setPreferences({ ...saved, ...dirty.current });
        if (!Object.keys(dirty.current).length) setError(null);
      } catch {
        if (alive.current)
          setError("Your preference was not saved. Try again.");
        throw Error("Preferences not saved");
      }
    };
    // Keep writes in user order; only outstanding fields are retried.
    const result = queue.current.then(save);
    queue.current = result.catch(() => {});
    return result.catch(() => {});
  }, []);
  const retry = () => {
    if (Object.keys(dirty.current).length) void update(dirty.current);
    else {
      setError(null);
      setRevision((r) => r + 1);
    }
  };
  return (
    <Context.Provider
      value={{ ownerId: userId, preferences, loaded, error, update, retry }}
    >
      {children}
      {error && (
        <div className="j5-save-error" role="alert">
          {error}{" "}
          <button type="button" onClick={retry}>
            Retry
          </button>
        </div>
      )}
    </Context.Provider>
  );
}
