import type { Priority, WaitlistFilters, WaitlistStats } from "../types/waitlist";
import { PRIORITY_LABELS } from "../utils/priority";

interface StatsPanelProps {
  stats: WaitlistStats | null;
  filters: WaitlistFilters;
  onFilterChange: (filters: WaitlistFilters) => void;
}

const PRIORITY_ORDER: Priority[] = ["vip", "reservation_overflow", "standard"];

export function StatsPanel({ stats, filters, onFilterChange }: StatsPanelProps) {
  if (!stats) return null;

  const slaActive = filters.sla_breached === true;

  function togglePriority(key: Priority) {
    onFilterChange({ ...filters, priority: filters.priority === key ? undefined : key });
  }

  function toggleSlaBreach() {
    onFilterChange({ ...filters, sla_breached: slaActive ? undefined : true });
  }

  return (
    <section className="stats-panel" aria-label="Waitlist stats">
      <div className="stat-tile">
        <span className="stat-value">{stats.queue_length}</span>
        <span className="stat-label">In queue</span>
      </div>
      <div className="stat-tile">
        <span className="stat-value">{stats.avg_wait_minutes}m</span>
        <span className="stat-label">Avg wait</span>
      </div>
      <button
        type="button"
        className={`stat-tile stat-tile-warning stat-tile-clickable ${slaActive ? "active" : ""}`}
        onClick={toggleSlaBreach}
        aria-pressed={slaActive}
        title="Filter the queue to SLA-breached entries"
      >
        <span className="stat-value">{stats.sla_breach_count}</span>
        <span className="stat-label">SLA breaches</span>
      </button>
      <div className="stat-tile stat-tile-breakdown">
        <span className="stat-label">By priority</span>
        <div className="stat-breakdown">
          {PRIORITY_ORDER.map((key) => (
            <button
              key={key}
              type="button"
              className={`stat-breakdown-item ${filters.priority === key ? "active" : ""}`}
              onClick={() => togglePriority(key)}
              aria-pressed={filters.priority === key}
              title={`Filter the queue to ${PRIORITY_LABELS[key]}`}
            >
              {PRIORITY_LABELS[key]} {stats.queue_length_by_priority[key]}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
