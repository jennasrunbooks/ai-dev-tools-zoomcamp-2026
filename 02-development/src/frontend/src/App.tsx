import { useState } from "react";
import { AddPartyForm } from "./components/AddPartyForm";
import { FilterBar } from "./components/FilterBar";
import { StatsPanel } from "./components/StatsPanel";
import { WaitlistTable } from "./components/WaitlistTable";
import { useWaitlist } from "./hooks/useWaitlist";
import type { WaitlistFilters } from "./types/waitlist";
import "./App.css";

export default function App() {
  const [filters, setFilters] = useState<WaitlistFilters>({});
  const { entries, stats, loading, error, addEntry, updateEntry, transitionStatus, deleteEntry } =
    useWaitlist(filters);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>WaitFlow</h1>
        <p className="app-subtitle">Restaurant waitlist manager</p>
      </header>

      <StatsPanel stats={stats} filters={filters} onFilterChange={setFilters} />

      <main className="app-main">
        <section className="queue-section">
          <div className="queue-section-header">
            <h2>Current queue</h2>
            <FilterBar filters={filters} onChange={setFilters} />
          </div>

          {error && <p className="banner banner-error">{error}</p>}
          {loading ? (
            <p className="empty-state">Loading waitlist…</p>
          ) : (
            <WaitlistTable
              entries={entries}
              onTransition={transitionStatus}
              onUpdate={updateEntry}
              onDelete={deleteEntry}
            />
          )}
        </section>

        <aside className="form-section">
          <AddPartyForm onAdd={addEntry} />
        </aside>
      </main>
    </div>
  );
}
