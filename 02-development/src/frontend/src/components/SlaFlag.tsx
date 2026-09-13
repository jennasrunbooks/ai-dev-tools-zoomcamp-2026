import { elapsedMinutes } from "../utils/sla";
import type { WaitlistEntryView } from "../types/waitlist";

export function SlaFlag({ entry }: { entry: WaitlistEntryView }) {
  const elapsed = elapsedMinutes(entry.created_at);

  if (!entry.sla_breached) {
    return (
      <span className="wait-time">
        {elapsed}m / {entry.quoted_wait_minutes}m
      </span>
    );
  }

  return (
    <span className="badge badge-sla-breach" title={`Quoted ${entry.quoted_wait_minutes}m, waiting ${elapsed}m`}>
      ⚠ SLA breached · {elapsed}m
    </span>
  );
}
