// Real HTTP client for the FastAPI backend (docs/spec.md 4, 5.4). Mirrors
// mockWaitlistApi.ts's interface exactly — see waitlistApi.ts for the
// mock/real switch. This is the only file that talks to the network.

import type {
  NewWaitlistEntryInput,
  Status,
  UpdateWaitlistEntryInput,
  WaitlistEntryView,
  WaitlistFilters,
  WaitlistStats,
} from "../types/waitlist";
import { ApiRequestError } from "./errors";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    // Backend errors are {code, message} (docs/spec.md 5.4); FastAPI's
    // default 422 validation errors are {detail: [...]} instead.
    if (body && typeof body.code === "string" && typeof body.message === "string") {
      throw new ApiRequestError(response.status, body.code, body.message);
    }
    const message = Array.isArray(body?.detail)
      ? body.detail.map((d: { msg?: string }) => d.msg).join(", ")
      : "Request failed.";
    throw new ApiRequestError(response.status, "validation_error", message);
  }

  return body as T;
}

function buildQuery(filters: WaitlistFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.sla_breached !== undefined) params.set("sla_breached", String(filters.sla_breached));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const httpWaitlistApi = {
  // GET /waitlist
  listEntries(filters: WaitlistFilters = {}): Promise<WaitlistEntryView[]> {
    return request(`/waitlist${buildQuery(filters)}`);
  },

  // GET /waitlist/{id}
  getEntry(id: string): Promise<WaitlistEntryView> {
    return request(`/waitlist/${id}`);
  },

  // POST /waitlist
  addEntry(input: NewWaitlistEntryInput): Promise<WaitlistEntryView> {
    return request(`/waitlist`, { method: "POST", body: JSON.stringify(input) });
  },

  // PATCH /waitlist/{id}
  updateEntry(id: string, patch: UpdateWaitlistEntryInput): Promise<WaitlistEntryView> {
    return request(`/waitlist/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
  },

  // PATCH /waitlist/{id}/status
  transitionStatus(id: string, to: Status): Promise<WaitlistEntryView> {
    return request(`/waitlist/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: to }),
    });
  },

  // DELETE /waitlist/{id}
  deleteEntry(id: string): Promise<void> {
    return request(`/waitlist/${id}`, { method: "DELETE" });
  },

  // GET /waitlist/stats
  getStats(): Promise<WaitlistStats> {
    return request(`/waitlist/stats`);
  },

  // GET /health
  health(): Promise<{ status: "ok" }> {
    return request(`/health`);
  },
};
