import type { Status } from "../types/waitlist";

// Allowed transitions per docs/spec.md section 3.2. Kept in one place so the
// UI and the mock API layer can't drift apart on what counts as valid.
// `waiting -> seated` covers walking a party straight to a table without a
// separate notify step (e.g. a table opened up while they were still at the
// podium).
export const ALLOWED_TRANSITIONS: Record<Status, Status[]> = {
  waiting: ["notified", "seated", "cancelled"],
  notified: ["seated", "no_show", "waiting"],
  seated: [],
  cancelled: [],
  no_show: [],
};

export function nextStatuses(current: Status): Status[] {
  return ALLOWED_TRANSITIONS[current];
}

export function isTransitionAllowed(from: Status, to: Status): boolean {
  return ALLOWED_TRANSITIONS[from].includes(to);
}

export function isTerminal(status: Status): boolean {
  return ALLOWED_TRANSITIONS[status].length === 0;
}

export const STATUS_LABELS: Record<Status, string> = {
  waiting: "Waiting",
  notified: "Notified",
  seated: "Seated",
  cancelled: "Cancelled",
  no_show: "No-show",
};
