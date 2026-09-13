import type { Status, WaitlistEntry } from "../types/waitlist";

const ACTIVE_STATUSES: Status[] = ["waiting", "notified"];

// SLA breach per docs/spec.md 3.4: now - created_at > quoted_wait_minutes,
// only meaningful while the entry is still active in the queue.
export function isSlaBreached(entry: WaitlistEntry, now: Date = new Date()): boolean {
  if (!ACTIVE_STATUSES.includes(entry.status)) return false;
  const elapsedMinutes = (now.getTime() - new Date(entry.created_at).getTime()) / 60000;
  return elapsedMinutes > entry.quoted_wait_minutes;
}

export function elapsedMinutes(createdAt: string, now: Date = new Date()): number {
  return Math.max(0, Math.floor((now.getTime() - new Date(createdAt).getTime()) / 60000));
}

// Priority rank per docs/spec.md 3.3: vip > reservation_overflow > standard.
const PRIORITY_RANK = { vip: 0, reservation_overflow: 1, standard: 2 } as const;

function closedAt(entry: WaitlistEntry): number {
  return new Date(entry.seated_at ?? entry.cancelled_at ?? entry.created_at).getTime();
}

// Section 3.3's priority/created_at ordering describes the *active* queue.
// Closed-out entries (seated/cancelled/no_show) aren't waiting for anything
// anymore, so they sink below every active entry regardless of priority,
// most-recently-closed first.
export function compareByQueueOrder(a: WaitlistEntry, b: WaitlistEntry): number {
  const aActive = ACTIVE_STATUSES.includes(a.status);
  const bActive = ACTIVE_STATUSES.includes(b.status);
  if (aActive !== bActive) return aActive ? -1 : 1;

  if (!aActive) return closedAt(b) - closedAt(a);

  const rankDiff = PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];
  if (rankDiff !== 0) return rankDiff;
  return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
}
