import type { Status } from "../types/waitlist";
import { STATUS_LABELS } from "../utils/statusMachine";

export function StatusBadge({ status }: { status: Status }) {
  return <span className={`badge badge-status badge-status-${status}`}>{STATUS_LABELS[status]}</span>;
}
