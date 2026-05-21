import type { DataStatus } from "../../types/dataStatus";
import { Badge } from "./Badge";

type DataStatusBadgeProps = {
  status: DataStatus;
  compact?: boolean;
};

export function DataStatusBadge({ status, compact = false }: DataStatusBadgeProps) {
  const tone = status.is_mock || status.is_stale || status.source === "unavailable" ? "warning" : "success";
  const source = status.is_mock ? "Mock" : status.is_stale ? "Stale" : status.source;
  const asOf = status.as_of ? formatDateTime(status.as_of) : null;

  return (
    <Badge tone={tone} title={status.warning ?? undefined}>
      {compact ? source : `${source} · ${status.provider}${asOf ? ` · ${asOf}` : ""}`}
    </Badge>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
