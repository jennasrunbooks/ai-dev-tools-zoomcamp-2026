// Mirrors the entities described in docs/spec.md section 3.1.

export type Priority = "vip" | "reservation_overflow" | "standard";

export type Status = "waiting" | "notified" | "seated" | "cancelled" | "no_show";

export interface WaitlistEntry {
  id: string;
  party_name: string;
  party_size: number;
  phone_number: string | null;
  priority: Priority;
  status: Status;
  quoted_wait_minutes: number;
  created_at: string; // ISO 8601 UTC
  notified_at: string | null;
  seated_at: string | null;
  cancelled_at: string | null;
  notes: string | null;
}

// sla_breached is computed on read (spec 3.4), so it travels alongside the
// entry rather than living on the stored record.
export interface WaitlistEntryView extends WaitlistEntry {
  sla_breached: boolean;
}

export interface NewWaitlistEntryInput {
  party_name: string;
  party_size: number;
  phone_number?: string;
  priority: Priority;
  quoted_wait_minutes: number;
  notes?: string;
}

export interface UpdateWaitlistEntryInput {
  party_size?: number;
  quoted_wait_minutes?: number;
  notes?: string;
}

export interface WaitlistFilters {
  status?: Status;
  priority?: Priority;
  sla_breached?: boolean;
}

export interface WaitlistStats {
  queue_length: number;
  queue_length_by_priority: Record<Priority, number>;
  avg_wait_minutes: number;
  sla_breach_count: number;
}

export interface ApiError {
  code: string;
  message: string;
}
