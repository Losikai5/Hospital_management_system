"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export function useApiData<T>(load: () => Promise<T>, dependencyKey: unknown = "") {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await loadRef.current());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load data.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Callers pass inline loaders; dependencies, not the loader's identity, control reloads.
  useEffect(() => {
    const timer = window.setTimeout(() => { void reload(); }, 0);
    return () => window.clearTimeout(timer);
  }, [reload, dependencyKey]);
  return { data, loading, error, reload };
}
