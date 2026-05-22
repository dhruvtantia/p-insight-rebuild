import { Camera, GitCompareArrows, Plus, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  Badge,
  Button,
  Card,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorState,
  FeatureDisabledState,
  Input,
  LoadingState,
  Table,
  Td,
  Th
} from "../components/ui";
import { usePortfolios } from "../hooks/usePortfolios";
import { useSnapshotComparison, useSnapshots } from "../hooks/useSnapshots";
import { ApiError } from "../services/apiClient";
import type {
  ConcentrationChange,
  HoldingValueChange,
  QuantityChange,
  SectorAllocationChange,
  SnapshotComparisonResponse,
  SnapshotHolding,
  SnapshotSummary
} from "../types/snapshots";

export function ChangesPage() {
  const [label, setLabel] = useState("");
  const [fromSnapshotId, setFromSnapshotId] = useState<string>("");
  const [toSnapshotId, setToSnapshotId] = useState<string>("");
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const snapshots = useSnapshots(selectedPortfolio?.id);
  const snapshotRows = useMemo(() => snapshots.data ?? [], [snapshots.data]);

  useEffect(() => {
    if (!snapshotRows.length) {
      setFromSnapshotId("");
      setToSnapshotId("");
      return;
    }

    setToSnapshotId((current) => (snapshotRows.some((snapshot) => snapshot.id === current) ? current : snapshotRows[0].id));
    setFromSnapshotId((current) => {
      if (snapshotRows.some((snapshot) => snapshot.id === current)) {
        return current;
      }
      return snapshotRows[1]?.id ?? snapshotRows[0].id;
    });
  }, [snapshotRows]);

  const comparison = useSnapshotComparison(selectedPortfolio?.id, fromSnapshotId, toSnapshotId);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!selectedPortfolio) {
    return (
      <div className="space-y-6">
        <ChangesHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before taking snapshots." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  const disabledError = getFeatureDisabledError(snapshots.error ?? comparison.error ?? snapshots.createSnapshot.error);

  function handleCreateSnapshot(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    snapshots.createSnapshot.mutate(
      { label: label.trim() || null },
      {
        onSuccess: (created) => {
          setLabel("");
          setToSnapshotId(created.id);
        }
      }
    );
  }

  return (
    <div className="space-y-6">
      <ChangesHeader />

      {disabledError ? (
        <FeatureDisabledState
          feature="Snapshots"
          detail="The backend snapshots feature flag is disabled in this environment."
        />
      ) : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Create snapshot</CardTitle>
            <p className="mt-1 text-sm text-slate-600">
              Capture the current portfolio holdings, allocation, and concentration for later comparison.
            </p>
          </div>
          <Camera className="text-accent" size={22} />
        </CardHeader>
        <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={handleCreateSnapshot}>
          <Input
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            placeholder="Optional label"
            maxLength={120}
            disabled={snapshots.createSnapshot.isPending || Boolean(disabledError)}
          />
          <Button type="submit" disabled={snapshots.createSnapshot.isPending || Boolean(disabledError)}>
            <Plus size={16} />
            {snapshots.createSnapshot.isPending ? "Creating" : "Create snapshot"}
          </Button>
        </form>
        {snapshots.createSnapshot.isError && !disabledError ? (
          <p className="mt-3 text-sm text-coral">{snapshots.createSnapshot.error.message}</p>
        ) : null}
      </Card>

      {snapshots.isLoading ? (
        <LoadingState label="Loading snapshots" />
      ) : snapshots.isError && !disabledError ? (
        <ErrorState title="Unable to load snapshots" detail={snapshots.error.message} />
      ) : snapshotRows.length ? (
        <SnapshotList snapshots={snapshotRows} currency={selectedPortfolio.base_currency} />
      ) : (
        <EmptyState title="No snapshots yet" detail="Create a snapshot to start tracking portfolio changes." />
      )}

      <ComparePanel
        snapshots={snapshotRows}
        fromSnapshotId={fromSnapshotId}
        toSnapshotId={toSnapshotId}
        onFromChange={setFromSnapshotId}
        onToChange={setToSnapshotId}
        comparison={comparison.data}
        isLoading={comparison.isLoading}
        isError={comparison.isError && !disabledError}
        error={comparison.error}
        disabled={Boolean(disabledError)}
        currency={selectedPortfolio.base_currency}
      />
    </div>
  );
}

function ChangesHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Changes</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio snapshots</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Compare saved portfolio states across holdings, allocation, and concentration.
        </p>
      </div>
      <Link to="/holdings">
        <Button variant="secondary">
          <Upload size={16} />
          Update holdings
        </Button>
      </Link>
    </section>
  );
}

function SnapshotList({ snapshots, currency }: { snapshots: SnapshotSummary[]; currency: string }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Snapshot list</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Newest saved portfolio states are shown first.</p>
        </div>
        <Badge>{snapshots.length} saved</Badge>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Snapshot</Th>
            <Th>As of</Th>
            <Th>Holdings</Th>
            <Th>Total value</Th>
            <Th>Cost basis</Th>
          </tr>
        </thead>
        <tbody>
          {snapshots.map((snapshot) => (
            <tr key={snapshot.id}>
              <Td>
                <div>
                  <p className="font-medium text-ink">{snapshot.label || "Untitled snapshot"}</p>
                  <p className="text-xs text-slate-500">{snapshot.id}</p>
                </div>
              </Td>
              <Td>{formatDateTime(snapshot.as_of)}</Td>
              <Td>{snapshot.holdings_count}</Td>
              <Td>{formatCurrency(snapshot.total_value, currency)}</Td>
              <Td>{formatCurrency(snapshot.cost_basis, currency)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function ComparePanel({
  snapshots,
  fromSnapshotId,
  toSnapshotId,
  onFromChange,
  onToChange,
  comparison,
  isLoading,
  isError,
  error,
  disabled,
  currency
}: {
  snapshots: SnapshotSummary[];
  fromSnapshotId: string;
  toSnapshotId: string;
  onFromChange: (id: string) => void;
  onToChange: (id: string) => void;
  comparison?: SnapshotComparisonResponse;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  disabled: boolean;
  currency: string;
}) {
  const hasEnoughSnapshots = snapshots.length >= 2;
  const hasDifferentSnapshots = Boolean(fromSnapshotId && toSnapshotId && fromSnapshotId !== toSnapshotId);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Compare snapshots</CardTitle>
            <p className="mt-1 text-sm text-slate-600">Choose two saved states to inspect backend-calculated changes.</p>
          </div>
          <GitCompareArrows className="text-accent" size={22} />
        </CardHeader>
        <div className="grid gap-3 md:grid-cols-2">
          <SnapshotSelect
            label="From"
            snapshots={snapshots}
            value={fromSnapshotId}
            onChange={onFromChange}
            disabled={disabled || !hasEnoughSnapshots}
          />
          <SnapshotSelect
            label="To"
            snapshots={snapshots}
            value={toSnapshotId}
            onChange={onToChange}
            disabled={disabled || !hasEnoughSnapshots}
          />
        </div>
      </Card>

      {!hasEnoughSnapshots ? (
        <EmptyState title="Need two snapshots" detail="Create at least two snapshots before comparing portfolio changes." />
      ) : !hasDifferentSnapshots ? (
        <EmptyState title="Choose different snapshots" detail="Select two different saved states to compare." />
      ) : isLoading ? (
        <LoadingState label="Comparing snapshots" />
      ) : isError ? (
        <ErrorState title="Unable to compare snapshots" detail={error?.message} />
      ) : comparison ? (
        <ComparisonResult comparison={comparison} currency={currency} />
      ) : null}
    </div>
  );
}

function SnapshotSelect({
  label,
  snapshots,
  value,
  onChange,
  disabled
}: {
  label: string;
  snapshots: SnapshotSummary[];
  value: string;
  onChange: (id: string) => void;
  disabled: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-600">{label}</span>
      <select
        className="h-10 w-full rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15 disabled:opacity-60"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        {snapshots.map((snapshot) => (
          <option key={snapshot.id} value={snapshot.id}>
            {snapshot.label || "Untitled snapshot"} - {formatDateTime(snapshot.as_of)}
          </option>
        ))}
      </select>
    </label>
  );
}

function ComparisonResult({ comparison, currency }: { comparison: SnapshotComparisonResponse; currency: string }) {
  return (
    <div className="space-y-4">
      <Card>
        <div className="grid gap-4 md:grid-cols-3">
          <MetricBlock label="From value" value={formatCurrency(comparison.value_changes.from_total_value, currency)} />
          <MetricBlock label="To value" value={formatCurrency(comparison.value_changes.to_total_value, currency)} />
          <MetricBlock label="Value change" value={formatSignedCurrency(comparison.value_changes.total_value_change, currency)} />
        </div>
      </Card>

      <section className="grid gap-4 lg:grid-cols-2">
        <HoldingsChangeCard title="Added holdings" holdings={comparison.added_holdings} emptyDetail="No holdings were added." />
        <HoldingsChangeCard title="Removed holdings" holdings={comparison.removed_holdings} emptyDetail="No holdings were removed." />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <QuantityChangesCard changes={comparison.quantity_changes} />
        <ValueChangesCard changes={comparison.value_changes.holdings} currency={currency} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <SectorChangesCard changes={comparison.sector_allocation_changes} currency={currency} />
        <ConcentrationChangesCard changes={comparison.concentration_changes} />
      </section>
    </div>
  );
}

function MetricBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface p-4">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}

function HoldingsChangeCard({ title, holdings, emptyDetail }: { title: string; holdings: SnapshotHolding[]; emptyDetail: string }) {
  if (!holdings.length) {
    return <EmptyState title={title} detail={emptyDetail} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <Badge>{holdings.length}</Badge>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Quantity</Th>
            <Th>Value</Th>
            <Th>Sector</Th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={holding.holding_id}>
              <Td>
                <div>
                  <p className="font-medium text-ink">{holding.symbol}</p>
                  <p className="text-xs text-slate-500">{holding.company_name ?? "N/A"}</p>
                </div>
              </Td>
              <Td>{formatNumber(holding.quantity)}</Td>
              <Td>{formatCurrency(holding.market_value, holding.currency)}</Td>
              <Td>{holding.sector ?? "Unassigned"}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function QuantityChangesCard({ changes }: { changes: QuantityChange[] }) {
  if (!changes.length) {
    return <EmptyState title="Quantity changes" detail="No shared holdings changed quantity." />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quantity changes</CardTitle>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>From</Th>
            <Th>To</Th>
            <Th>Change</Th>
          </tr>
        </thead>
        <tbody>
          {changes.map((change) => (
            <tr key={change.symbol}>
              <Td className="font-medium text-ink">{change.symbol}</Td>
              <Td>{formatNumber(change.from_quantity)}</Td>
              <Td>{formatNumber(change.to_quantity)}</Td>
              <Td>{formatSignedNumber(change.quantity_change)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function ValueChangesCard({ changes, currency }: { changes: HoldingValueChange[]; currency: string }) {
  if (!changes.length) {
    return <EmptyState title="Value changes" detail="No holding values changed between these snapshots." />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Value changes</CardTitle>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>From</Th>
            <Th>To</Th>
            <Th>Change</Th>
          </tr>
        </thead>
        <tbody>
          {changes.map((change) => (
            <tr key={change.symbol}>
              <Td className="font-medium text-ink">{change.symbol}</Td>
              <Td>{formatCurrency(change.from_value, currency)}</Td>
              <Td>{formatCurrency(change.to_value, currency)}</Td>
              <Td>{formatSignedCurrency(change.value_change, currency)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function SectorChangesCard({ changes, currency }: { changes: SectorAllocationChange[]; currency: string }) {
  if (!changes.length) {
    return <EmptyState title="Sector allocation changes" detail="No sector allocation changed between these snapshots." />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sector allocation changes</CardTitle>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Sector</Th>
            <Th>Value change</Th>
            <Th>Weight change</Th>
            <Th>To weight</Th>
          </tr>
        </thead>
        <tbody>
          {changes.map((change) => (
            <tr key={change.name}>
              <Td className="font-medium text-ink">{change.name}</Td>
              <Td>{formatSignedCurrency(change.value_change, currency)}</Td>
              <Td>{formatSignedPercent(change.weight_change)}</Td>
              <Td>{formatPercent(change.to_weight)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function ConcentrationChangesCard({ changes }: { changes: ConcentrationChange | null }) {
  if (!changes) {
    return <EmptyState title="Concentration changes" detail="No concentration comparison is available for these snapshots." />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Concentration changes</CardTitle>
      </CardHeader>
      <div className="grid gap-3">
        <MetricBlock label="Status" value={`${formatStatus(changes.from_status)} to ${formatStatus(changes.to_status)}`} />
        <MetricBlock
          label="Largest holding"
          value={`${changes.from_largest_symbol ?? "N/A"} to ${changes.to_largest_symbol ?? "N/A"}`}
        />
        <MetricBlock label="Top 5 weight change" value={formatSignedPercent(changes.top_5_weight_change)} />
      </div>
    </Card>
  );
}

function getFeatureDisabledError(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const details = typeof error.details === "object" && error.details !== null ? error.details : {};
  const feature = "feature" in details ? details.feature : null;
  return error.code === "feature_disabled" || feature === "ENABLE_SNAPSHOTS" ? error : null;
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function formatSignedCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  const formatted = formatCurrency(value, currency);
  return value > 0 ? `+${formatted}` : formatted;
}

function formatPercent(value: number | null) {
  if (value === null) return "N/A";
  return `${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value)}%`;
}

function formatSignedPercent(value: number | null) {
  if (value === null) return "N/A";
  return `${value > 0 ? "+" : ""}${formatPercent(value)}`;
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 6
  }).format(value);
}

function formatSignedNumber(value: number) {
  return `${value > 0 ? "+" : ""}${formatNumber(value)}`;
}

function formatStatus(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
