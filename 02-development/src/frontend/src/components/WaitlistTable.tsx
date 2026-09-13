import { Fragment, useState } from "react";
import type { Status, UpdateWaitlistEntryInput, WaitlistEntryView } from "../types/waitlist";
import { isTerminal, nextStatuses, STATUS_LABELS } from "../utils/statusMachine";
import { PriorityBadge } from "./PriorityBadge";
import { StatusBadge } from "./StatusBadge";
import { SlaFlag } from "./SlaFlag";

function variantForTransition(to: Status): string {
  if (to === "seated") return "btn-success";
  if (to === "cancelled" || to === "no_show") return "btn-warning";
  return "btn-secondary";
}

interface WaitlistTableProps {
  entries: WaitlistEntryView[];
  onTransition: (id: string, to: Status) => Promise<{ ok: boolean; message?: string }>;
  onUpdate: (id: string, patch: UpdateWaitlistEntryInput) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function WaitlistTable({ entries, onTransition, onUpdate, onDelete }: WaitlistTableProps) {
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [rowError, setRowError] = useState<{ id: string; message: string } | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);

  async function handleTransition(id: string, to: Status) {
    setPendingId(id);
    setRowError(null);
    const result = await onTransition(id, to);
    if (!result.ok) {
      setRowError({ id, message: result.message ?? "That transition isn't allowed." });
    }
    setPendingId(null);
  }

  async function handleDelete(id: string) {
    setPendingId(id);
    await onDelete(id);
    setPendingId(null);
  }

  if (entries.length === 0) {
    return <p className="empty-state">No parties match the current filters.</p>;
  }

  return (
    <table className="waitlist-table">
      <thead>
        <tr>
          <th>Party</th>
          <th>Priority</th>
          <th>Status</th>
          <th>Wait</th>
          <th>Notes</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <Fragment key={entry.id}>
            <tr className={entry.sla_breached ? "row-breached" : undefined}>
              <td>
                <div className="party-name">{entry.party_name}</div>
                <div className="party-meta">
                  {entry.party_size} guest{entry.party_size === 1 ? "" : "s"}
                  {entry.phone_number ? ` · ${entry.phone_number}` : ""}
                </div>
              </td>
              <td>
                <PriorityBadge priority={entry.priority} />
              </td>
              <td>
                <StatusBadge status={entry.status} />
              </td>
              <td>
                <SlaFlag entry={entry} />
              </td>
              <td className="notes-cell">{entry.notes ?? "—"}</td>
              <td>
                <div className="action-buttons">
                  {nextStatuses(entry.status).map((to) => (
                    <button
                      key={to}
                      type="button"
                      className={`btn btn-small ${variantForTransition(to)}`}
                      disabled={pendingId === entry.id}
                      onClick={() => handleTransition(entry.id, to)}
                    >
                      {STATUS_LABELS[to]}
                    </button>
                  ))}
                  {!isTerminal(entry.status) && (
                    <button
                      type="button"
                      className="btn btn-small btn-ghost"
                      onClick={() => setEditingId(editingId === entry.id ? null : entry.id)}
                    >
                      Edit
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn-small btn-ghost btn-danger"
                    disabled={pendingId === entry.id}
                    onClick={() => handleDelete(entry.id)}
                  >
                    Remove
                  </button>
                </div>
                {rowError?.id === entry.id && <p className="row-error">{rowError.message}</p>}
              </td>
            </tr>
            {editingId === entry.id && (
              <tr className="edit-row">
                <td colSpan={6}>
                  <EditRow
                    entry={entry}
                    onCancel={() => setEditingId(null)}
                    onSave={async (patch) => {
                      await onUpdate(entry.id, patch);
                      setEditingId(null);
                    }}
                  />
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}

function EditRow({
  entry,
  onSave,
  onCancel,
}: {
  entry: WaitlistEntryView;
  onSave: (patch: UpdateWaitlistEntryInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [partySize, setPartySize] = useState(String(entry.party_size));
  const [quotedWait, setQuotedWait] = useState(String(entry.quoted_wait_minutes));
  const [notes, setNotes] = useState(entry.notes ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    await onSave({
      party_size: Number(partySize),
      quoted_wait_minutes: Number(quotedWait),
      notes,
    });
    setSaving(false);
  }

  return (
    <div className="edit-row-fields">
      <label>
        Party size
        <input type="number" min={1} value={partySize} onChange={(e) => setPartySize(e.target.value)} />
      </label>
      <label>
        Quoted wait (min)
        <input type="number" min={1} value={quotedWait} onChange={(e) => setQuotedWait(e.target.value)} />
      </label>
      <label>
        Notes
        <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
      <div className="edit-row-actions">
        <button type="button" className="btn btn-small btn-primary" disabled={saving} onClick={handleSave}>
          {saving ? "Saving…" : "Save"}
        </button>
        <button type="button" className="btn btn-small btn-ghost" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}
