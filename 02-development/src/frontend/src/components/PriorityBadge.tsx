import type { Priority } from "../types/waitlist";
import { PRIORITY_LABELS, PRIORITY_TITLES } from "../utils/priority";

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`badge badge-priority badge-priority-${priority}`} title={PRIORITY_TITLES[priority]}>
      {PRIORITY_LABELS[priority]}
    </span>
  );
}
