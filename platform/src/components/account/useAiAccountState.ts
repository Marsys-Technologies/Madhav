"use client";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAccountPreferences } from "./AccountPreferencesProvider";
import type {
  AiConsoleStateDto,
  CliStateDto,
} from "@/components/ai-console/types";
export function useAiAccountKeys() {
  const owner = useAccountPreferences()?.ownerId;
  return useMemo(
    () => ({
      state: owner ? ["ai-console", "state", owner] : ["ai-console", "state"],
      clis: owner ? ["ai-console", "clis", owner] : ["ai-console", "clis"],
    }),
    [owner],
  );
}
async function get<T>(path: string, signal: AbortSignal): Promise<T> {
  const r = await fetch(path, { signal, cache: "no-store" });
  if (!r.ok) throw Error("AI settings could not be loaded.");
  return r.json();
}
export function useAiAccountState() {
  const keys = useAiAccountKeys();
  const state = useQuery({
    queryKey: keys.state,
    queryFn: ({ signal }) => get<AiConsoleStateDto>("/api/ai-console", signal),
  });
  const clis = useQuery({
    queryKey: keys.clis,
    queryFn: ({ signal }) => get<CliStateDto>("/api/ai-console/clis", signal),
  });
  return {
    state: state.data,
    clis: clis.data?.clis ?? [],
    loading: state.isPending || clis.isPending,
    error: state.isError || clis.isError,
  };
}
