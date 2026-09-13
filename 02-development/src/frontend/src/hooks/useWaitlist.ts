import { useCallback, useEffect, useState } from "react";
import { ApiRequestError, waitlistApi } from "../api/waitlistApi";
import type {
  NewWaitlistEntryInput,
  Status,
  UpdateWaitlistEntryInput,
  WaitlistEntryView,
  WaitlistFilters,
  WaitlistStats,
} from "../types/waitlist";

// Recompute elapsed-time / SLA-breach flags periodically since they're
// derived from `created_at` rather than pushed by the backend.
const REFRESH_INTERVAL_MS = 15_000;

export function useWaitlist(filters: WaitlistFilters = {}) {
  const [entries, setEntries] = useState<WaitlistEntryView[]>([]);
  const [stats, setStats] = useState<WaitlistStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [entryList, entryStats] = await Promise.all([
        waitlistApi.listEntries(filters),
        waitlistApi.getStats(),
      ]);
      setEntries(entryList);
      setStats(entryStats);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load waitlist.");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    void refresh();
    const interval = setInterval(refresh, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  const addEntry = useCallback(
    async (input: NewWaitlistEntryInput) => {
      await waitlistApi.addEntry(input);
      await refresh();
    },
    [refresh],
  );

  const updateEntry = useCallback(
    async (id: string, patch: UpdateWaitlistEntryInput) => {
      await waitlistApi.updateEntry(id, patch);
      await refresh();
    },
    [refresh],
  );

  const transitionStatus = useCallback(
    async (id: string, to: Status) => {
      try {
        await waitlistApi.transitionStatus(id, to);
        await refresh();
        return { ok: true as const };
      } catch (err) {
        const message =
          err instanceof ApiRequestError ? err.message : "Failed to update status.";
        return { ok: false as const, message };
      }
    },
    [refresh],
  );

  const deleteEntry = useCallback(
    async (id: string) => {
      await waitlistApi.deleteEntry(id);
      await refresh();
    },
    [refresh],
  );

  return { entries, stats, loading, error, addEntry, updateEntry, transitionStatus, deleteEntry, refresh };
}
