import { useState } from "react";
import type { FormEvent } from "react";
import type { NewWaitlistEntryInput, Priority } from "../types/waitlist";
import { PRIORITY_LABELS } from "../utils/priority";

interface AddPartyFormProps {
  onAdd: (input: NewWaitlistEntryInput) => Promise<void>;
}

const initialState = {
  party_name: "",
  party_size: "2",
  phone_number: "",
  priority: "standard" as Priority,
  quoted_wait_minutes: "15",
  notes: "",
};

export function AddPartyForm({ onAdd }: AddPartyFormProps) {
  const [form, setForm] = useState(initialState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof typeof initialState>(key: K, value: (typeof initialState)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const partySize = Number(form.party_size);
    const quotedWait = Number(form.quoted_wait_minutes);

    if (!form.party_name.trim()) {
      setError("Party name is required.");
      return;
    }
    if (!Number.isInteger(partySize) || partySize <= 0) {
      setError("Party size must be a positive whole number.");
      return;
    }
    if (!Number.isInteger(quotedWait) || quotedWait <= 0) {
      setError("Quoted wait must be a positive whole number of minutes.");
      return;
    }

    setSubmitting(true);
    try {
      await onAdd({
        party_name: form.party_name,
        party_size: partySize,
        phone_number: form.phone_number || undefined,
        priority: form.priority,
        quoted_wait_minutes: quotedWait,
        notes: form.notes || undefined,
      });
      setForm(initialState);
    } catch {
      setError("Failed to add party. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="add-party-form" onSubmit={handleSubmit}>
      <h2>Check in a party</h2>

      <div className="form-row">
        <label>
          <span>Party name</span>
          <input
            type="text"
            value={form.party_name}
            onChange={(e) => update("party_name", e.target.value)}
            placeholder="e.g. Nguyen"
            required
          />
        </label>
        <label>
          <span>Party size</span>
          <input
            type="number"
            min={1}
            value={form.party_size}
            onChange={(e) => update("party_size", e.target.value)}
            required
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          <span>Phone (optional)</span>
          <input
            type="tel"
            value={form.phone_number}
            onChange={(e) => update("phone_number", e.target.value)}
            placeholder="555-0100"
          />
        </label>
        <label>
          <span>Priority</span>
          <select value={form.priority} onChange={(e) => update("priority", e.target.value as Priority)}>
            <option value="standard">{PRIORITY_LABELS.standard}</option>
            <option value="reservation_overflow">{PRIORITY_LABELS.reservation_overflow}</option>
            <option value="vip">{PRIORITY_LABELS.vip}</option>
          </select>
        </label>
      </div>

      <div className="form-row">
        <label>
          <span>Quoted wait (min)</span>
          <input
            type="number"
            min={1}
            value={form.quoted_wait_minutes}
            onChange={(e) => update("quoted_wait_minutes", e.target.value)}
            required
          />
        </label>
        <label>
          <span>Notes (optional)</span>
          <input
            type="text"
            value={form.notes}
            onChange={(e) => update("notes", e.target.value)}
            placeholder="e.g. requested patio"
          />
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}

      <button type="submit" className="btn btn-primary" disabled={submitting}>
        {submitting ? "Adding…" : "Add to waitlist"}
      </button>
    </form>
  );
}
