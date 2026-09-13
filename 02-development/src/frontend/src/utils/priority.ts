import type { Priority } from "../types/waitlist";

// "Overflow" = a party bumped from a confirmed reservation (e.g. the prior
// table ran long) rather than a walk-in — ranks above standard, below VIP.
export const PRIORITY_LABELS: Record<Priority, string> = {
  vip: "VIP",
  reservation_overflow: "Overflow",
  standard: "Standard",
};

export const PRIORITY_TITLES: Record<Priority, string> = {
  vip: "VIP",
  reservation_overflow: "Reservation overflow — bumped from a confirmed reservation",
  standard: "Standard walk-in",
};
