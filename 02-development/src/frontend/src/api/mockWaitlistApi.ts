// Mock-first service layer (docs/spec.md 6.2). Backed by an in-memory
// fixture store with simulated network latency and the same
// status-transition/validation errors the real API returns. Useful for
// frontend-only work without a running backend — see waitlistApi.ts for the
// mock/real switch.

import type {
  NewWaitlistEntryInput,
  Priority,
  Status,
  UpdateWaitlistEntryInput,
  WaitlistEntry,
  WaitlistEntryView,
  WaitlistFilters,
  WaitlistStats,
} from "../types/waitlist";
import { compareByQueueOrder, isSlaBreached } from "../utils/sla";
import { isTransitionAllowed } from "../utils/statusMachine";
import { ApiRequestError } from "./errors";

const SIMULATED_LATENCY_MS = 250;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), SIMULATED_LATENCY_MS));
}

function minutesAgo(minutes: number): string {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

function withView(entry: WaitlistEntry): WaitlistEntryView {
  return { ...entry, sla_breached: isSlaBreached(entry) };
}

// --- Fixture data -----------------------------------------------------
// Shaped to exercise every priority/status combination the UI needs to
// render, including an already-breached entry.

let store: WaitlistEntry[] = [
  {
    id: "e-1001",
    party_name: "Nguyen",
    party_size: 4,
    phone_number: "555-0101",
    priority: "vip",
    status: "waiting",
    quoted_wait_minutes: 15,
    created_at: minutesAgo(6),
    notified_at: null,
    seated_at: null,
    cancelled_at: null,
    notes: "Anniversary dinner, requested corner booth.",
  },
  {
    id: "e-1002",
    party_name: "Okafor",
    party_size: 2,
    phone_number: "555-0102",
    priority: "standard",
    status: "waiting",
    quoted_wait_minutes: 10,
    created_at: minutesAgo(22),
    notified_at: null,
    seated_at: null,
    cancelled_at: null,
    notes: null,
  },
  {
    id: "e-1003",
    party_name: "Alvarez",
    party_size: 6,
    phone_number: null,
    priority: "reservation_overflow",
    status: "notified",
    quoted_wait_minutes: 20,
    created_at: minutesAgo(18),
    notified_at: minutesAgo(2),
    seated_at: null,
    cancelled_at: null,
    notes: "Reservation ran long ahead of them.",
  },
  {
    id: "e-1004",
    party_name: "Petrov",
    party_size: 3,
    phone_number: "555-0104",
    priority: "standard",
    status: "waiting",
    quoted_wait_minutes: 12,
    created_at: minutesAgo(35),
    notified_at: null,
    seated_at: null,
    cancelled_at: null,
    notes: null,
  },
  {
    id: "e-1005",
    party_name: "Chen",
    party_size: 2,
    phone_number: "555-0105",
    priority: "standard",
    status: "seated",
    quoted_wait_minutes: 15,
    created_at: minutesAgo(50),
    notified_at: minutesAgo(40),
    seated_at: minutesAgo(35),
    cancelled_at: null,
    notes: null,
  },
  {
    id: "e-1006",
    party_name: "Whitfield",
    party_size: 5,
    phone_number: "555-0106",
    priority: "vip",
    status: "cancelled",
    quoted_wait_minutes: 10,
    created_at: minutesAgo(60),
    notified_at: null,
    seated_at: null,
    cancelled_at: minutesAgo(55),
    notes: "Called to cancel.",
  },
];

let nextIdSeed = 1007;

function findEntryOrThrow(id: string): WaitlistEntry {
  const entry = store.find((e) => e.id === id);
  if (!entry) {
    throw new ApiRequestError(404, "not_found", `No waitlist entry with id "${id}".`);
  }
  return entry;
}

export const mockWaitlistApi = {
  // GET /waitlist
  async listEntries(filters: WaitlistFilters = {}): Promise<WaitlistEntryView[]> {
    let views = store.map(withView);
    if (filters.status) views = views.filter((e) => e.status === filters.status);
    if (filters.priority) views = views.filter((e) => e.priority === filters.priority);
    if (filters.sla_breached !== undefined) {
      views = views.filter((e) => e.sla_breached === filters.sla_breached);
    }
    views.sort(compareByQueueOrder);
    return delay(views);
  },

  // GET /waitlist/{id}
  async getEntry(id: string): Promise<WaitlistEntryView> {
    const entry = findEntryOrThrow(id);
    return delay(withView(entry));
  },

  // POST /waitlist
  async addEntry(input: NewWaitlistEntryInput): Promise<WaitlistEntryView> {
    const entry: WaitlistEntry = {
      id: `e-${nextIdSeed++}`,
      party_name: input.party_name.trim(),
      party_size: input.party_size,
      phone_number: input.phone_number?.trim() || null,
      priority: input.priority,
      status: "waiting",
      quoted_wait_minutes: input.quoted_wait_minutes,
      created_at: new Date().toISOString(),
      notified_at: null,
      seated_at: null,
      cancelled_at: null,
      notes: input.notes?.trim() || null,
    };
    store = [...store, entry];
    return delay(withView(entry));
  },

  // PATCH /waitlist/{id}
  async updateEntry(id: string, patch: UpdateWaitlistEntryInput): Promise<WaitlistEntryView> {
    const entry = findEntryOrThrow(id);
    Object.assign(entry, patch);
    return delay(withView(entry));
  },

  // PATCH /waitlist/{id}/status
  async transitionStatus(id: string, to: Status): Promise<WaitlistEntryView> {
    const entry = findEntryOrThrow(id);
    if (!isTransitionAllowed(entry.status, to)) {
      throw new ApiRequestError(
        409,
        "invalid_transition",
        `Cannot move "${entry.party_name}" from "${entry.status}" to "${to}".`,
      );
    }
    entry.status = to;
    const now = new Date().toISOString();
    if (to === "notified") entry.notified_at = now;
    if (to === "seated") entry.seated_at = now;
    if (to === "cancelled" || to === "no_show") entry.cancelled_at = now;
    if (to === "waiting") entry.notified_at = null;
    return delay(withView(entry));
  },

  // DELETE /waitlist/{id}
  async deleteEntry(id: string): Promise<void> {
    findEntryOrThrow(id);
    store = store.filter((e) => e.id !== id);
    return delay(undefined);
  },

  // GET /waitlist/stats
  async getStats(): Promise<WaitlistStats> {
    const active = store.filter((e) => e.status === "waiting" || e.status === "notified");
    const byPriority: Record<Priority, number> = {
      vip: 0,
      reservation_overflow: 0,
      standard: 0,
    };
    for (const entry of active) byPriority[entry.priority] += 1;

    const avgWaitMinutes = active.length
      ? Math.round(
          active.reduce((sum, e) => sum + (Date.now() - new Date(e.created_at).getTime()), 0) /
            active.length /
            60_000,
        )
      : 0;

    const slaBreachCount = active.filter((e) => isSlaBreached(e)).length;

    return delay({
      queue_length: active.length,
      queue_length_by_priority: byPriority,
      avg_wait_minutes: avgWaitMinutes,
      sla_breach_count: slaBreachCount,
    });
  },

  // GET /health
  async health(): Promise<{ status: "ok" }> {
    return delay({ status: "ok" });
  },
};
