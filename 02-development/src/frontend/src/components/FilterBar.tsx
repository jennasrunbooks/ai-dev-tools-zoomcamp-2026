import type { Priority, Status, WaitlistFilters } from "../types/waitlist";
import { PRIORITY_LABELS } from "../utils/priority";
import { STATUS_LABELS } from "../utils/statusMachine";

interface FilterBarProps {
  filters: WaitlistFilters;
  onChange: (filters: WaitlistFilters) => void;
}

const STATUS_OPTIONS: Status[] = ["waiting", "notified", "seated", "cancelled", "no_show"];
const PRIORITY_OPTIONS: Priority[] = ["vip", "reservation_overflow", "standard"];

export function FilterBar({ filters, onChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <label>
        Status
        <select
          value={filters.status ?? ""}
          onChange={(e) => onChange({ ...filters, status: (e.target.value || undefined) as Status | undefined })}
        >
          <option value="">All</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Priority
        <select
          value={filters.priority ?? ""}
          onChange={(e) =>
            onChange({ ...filters, priority: (e.target.value || undefined) as Priority | undefined })
          }
        >
          <option value="">All</option>
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p} value={p}>
              {PRIORITY_LABELS[p]}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
