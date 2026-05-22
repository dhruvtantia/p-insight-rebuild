import { AlertTriangle, RotateCcw, Scale, Trash2 } from "lucide-react";
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
import { useHoldings } from "../hooks/useHoldings";
import { usePortfolios } from "../hooks/usePortfolios";
import { useSimulator } from "../hooks/useSimulator";
import { ApiError } from "../services/apiClient";
import type { Holding } from "../types/holdings";
import type { SimulationResponse, SimulatedAllocationLine } from "../types/simulator";

type TargetWeights = Record<string, number>;

export function SimulatorPage() {
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const holdings = useHoldings(selectedPortfolio?.id);
  const simulator = useSimulator(selectedPortfolio?.id);
  const [targetWeights, setTargetWeights] = useState<TargetWeights>({});
  const [removedSymbols, setRemovedSymbols] = useState<string[]>([]);

  const currentTargets = useMemo(() => buildCurrentTargetWeights(holdings.data ?? []), [holdings.data]);

  useEffect(() => {
    setTargetWeights(currentTargets);
    setRemovedSymbols([]);
  }, [currentTargets]);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!selectedPortfolio) {
    return (
      <div className="space-y-6">
        <SimulatorHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before running a scenario simulation." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  const disabledError = getFeatureDisabledError(simulator.simulation.error);
  const activeTargetTotal = sumActiveWeights(targetWeights, removedSymbols);

  function handleWeightChange(symbol: string, value: string) {
    const parsed = Number(value);
    setTargetWeights((current) => ({
      ...current,
      [symbol]: Number.isFinite(parsed) ? Math.max(parsed, 0) : 0
    }));
  }

  function handleNormalize() {
    const total = activeTargetTotal;
    if (total <= 0) {
      return;
    }
    setTargetWeights((current) => {
      const next = { ...current };
      for (const [symbol, weight] of Object.entries(current)) {
        next[symbol] = removedSymbols.includes(symbol) ? 0 : roundPercent((weight / total) * 100);
      }
      return next;
    });
  }

  function handleReset() {
    setTargetWeights(currentTargets);
    setRemovedSymbols([]);
    simulator.simulation.reset();
  }

  function handleRemove(symbol: string) {
    setRemovedSymbols((current) => (current.includes(symbol) ? current : [...current, symbol]));
    setTargetWeights((current) => ({ ...current, [symbol]: 0 }));
  }

  function handleSubmit() {
    const requestWeights = Object.fromEntries(
      Object.entries(targetWeights)
        .filter(([symbol]) => !removedSymbols.includes(symbol))
        .map(([symbol, weight]) => [symbol, roundPercent(weight)])
    );
    simulator.simulation.mutate({
      target_weights: requestWeights,
      removed_symbols: removedSymbols
    });
  }

  return (
    <div className="space-y-6">
      <SimulatorHeader />
      <NoTradesDisclaimer />

      {disabledError ? (
        <FeatureDisabledState
          feature="Simulator"
          detail="The backend simulator feature flag is disabled in this environment."
        />
      ) : null}

      {holdings.isLoading ? (
        <LoadingState label="Loading holdings" />
      ) : holdings.isError ? (
        <ErrorState title="Unable to load holdings" detail={holdings.error.message} />
      ) : !holdings.data?.length ? (
        <EmptyState title="No holdings to simulate" detail="Add priced holdings before running a portfolio scenario." />
      ) : (
        <>
          <ScenarioEditor
            holdings={holdings.data}
            targetWeights={targetWeights}
            removedSymbols={removedSymbols}
            activeTargetTotal={activeTargetTotal}
            disabled={Boolean(disabledError) || simulator.simulation.isPending}
            onWeightChange={handleWeightChange}
            onNormalize={handleNormalize}
            onReset={handleReset}
            onRemove={handleRemove}
            onSubmit={handleSubmit}
          />

          {simulator.simulation.isPending ? <LoadingState label="Running simulation" /> : null}
          {simulator.simulation.isError && !disabledError ? (
            <ErrorState title="Unable to run simulation" detail={simulator.simulation.error.message} />
          ) : null}
          {simulator.simulation.data ? (
            <SimulationResults response={simulator.simulation.data} currency={selectedPortfolio.base_currency} />
          ) : null}
        </>
      )}
    </div>
  );
}

function SimulatorHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Simulator</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio scenario simulator</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Test hypothetical target weights against the backend simulator without changing current holdings.
        </p>
      </div>
      <Link to="/holdings">
        <Button variant="secondary">Review holdings</Button>
      </Link>
    </section>
  );
}

function NoTradesDisclaimer() {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-amber-700" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-amber-900">No trades executed</h3>
          <p className="mt-1 text-sm text-amber-800">
            This scenario is hypothetical only. It does not place orders, execute trades, or persist holding changes.
          </p>
        </div>
      </div>
    </Card>
  );
}

function ScenarioEditor({
  holdings,
  targetWeights,
  removedSymbols,
  activeTargetTotal,
  disabled,
  onWeightChange,
  onNormalize,
  onReset,
  onRemove,
  onSubmit
}: {
  holdings: Holding[];
  targetWeights: TargetWeights;
  removedSymbols: string[];
  activeTargetTotal: number;
  disabled: boolean;
  onWeightChange: (symbol: string, value: string) => void;
  onNormalize: () => void;
  onReset: () => void;
  onRemove: (symbol: string) => void;
  onSubmit: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Scenario target weights</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Weights are submitted as percentages. Removed holdings stay in the scenario at 0%.</p>
        </div>
        <Badge tone={Math.abs(activeTargetTotal - 100) <= 0.01 ? "success" : "warning"}>
          {formatNumber(activeTargetTotal)}% active
        </Badge>
      </CardHeader>

      <div className="mb-4 flex flex-wrap gap-2">
        <Button type="button" variant="secondary" onClick={onNormalize} disabled={disabled || activeTargetTotal <= 0}>
          <Scale size={16} />
          Normalize weights
        </Button>
        <Button type="button" variant="secondary" onClick={onReset} disabled={disabled}>
          <RotateCcw size={16} />
          Reset scenario
        </Button>
        <Button type="button" onClick={onSubmit} disabled={disabled}>
          Submit simulation
        </Button>
      </div>

      <Table>
        <thead>
          <tr>
            <Th>Holding</Th>
            <Th>Current value</Th>
            <Th>Current weight</Th>
            <Th>Target weight</Th>
            <Th>Status</Th>
            <Th>Action</Th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => {
            const symbol = holding.symbol.toUpperCase();
            const isRemoved = removedSymbols.includes(symbol);
            return (
              <tr key={holding.id}>
                <Td>
                  <div>
                    <p className="font-medium text-ink">{symbol}</p>
                    <p className="text-xs text-slate-500">{holding.sector ?? "Unassigned"}</p>
                  </div>
                </Td>
                <Td>{formatCurrency(holding.market_value, holding.currency)}</Td>
                <Td>{formatPercent(currentWeight(holding, holdings))}</Td>
                <Td>
                  <Input
                    type="number"
                    min={0}
                    step="0.01"
                    value={targetWeights[symbol] ?? 0}
                    onChange={(event) => onWeightChange(symbol, event.target.value)}
                    disabled={disabled || isRemoved}
                    className="max-w-28"
                  />
                </Td>
                <Td>{isRemoved ? <Badge tone="warning">Removed</Badge> : <Badge tone="success">Active</Badge>}</Td>
                <Td>
                  <Button type="button" variant="secondary" onClick={() => onRemove(symbol)} disabled={disabled || isRemoved}>
                    <Trash2 size={15} />
                    Remove
                  </Button>
                </Td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </Card>
  );
}

function SimulationResults({ response, currency }: { response: SimulationResponse; currency: string }) {
  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Simulation result</CardTitle>
            <p className="mt-1 text-sm text-slate-600">
              Persisted: <span className="font-semibold">{response.persisted ? "Yes" : "No"}</span>
            </p>
          </div>
          <Badge tone={response.persisted ? "danger" : "success"}>
            {response.persisted ? "Unexpected persistence" : "No holdings modified"}
          </Badge>
        </div>
      </Card>

      {response.warnings.map((warning) => (
        <WarningBanner key={warning} detail={warning} />
      ))}

      <section className="grid gap-4 xl:grid-cols-2">
        <AllocationTable title="Current allocation" rows={response.current_allocation} currency={currency} />
        <SimulatedAllocationTable rows={response.simulated_allocation} currency={currency} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <ConcentrationChangeCard response={response} />
        <EstimatedDistributionCard rows={response.estimated_value_distribution.symbols} currency={currency} />
      </section>
    </div>
  );
}

function WarningBanner({ detail }: { detail: string }) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-amber-700" size={20} />
        <p className="text-sm text-amber-800">{detail}</p>
      </div>
    </Card>
  );
}

function AllocationTable({
  title,
  rows,
  currency
}: {
  title: string;
  rows: SimulationResponse["current_allocation"];
  currency: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Value</Th>
            <Th>Weight</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.symbol}>
              <Td className="font-medium text-ink">{row.symbol}</Td>
              <Td>{formatCurrency(row.current_value, currency)}</Td>
              <Td>{formatPercent(row.weight)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function SimulatedAllocationTable({ rows, currency }: { rows: SimulatedAllocationLine[]; currency: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Simulated allocation</CardTitle>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Estimated value</Th>
            <Th>Weight</Th>
            <Th>Status</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.symbol}>
              <Td className="font-medium text-ink">{row.symbol}</Td>
              <Td>{formatCurrency(row.estimated_value, currency)}</Td>
              <Td>{formatPercent(row.weight)}</Td>
              <Td>
                {row.is_removed ? (
                  <Badge tone="warning">Removed</Badge>
                ) : row.is_added ? (
                  <Badge>Added</Badge>
                ) : (
                  <Badge tone="success">Existing</Badge>
                )}
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function ConcentrationChangeCard({ response }: { response: SimulationResponse }) {
  const change = response.concentration_change;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Concentration change</CardTitle>
      </CardHeader>
      <div className="grid gap-3">
        <MetricBlock label="Largest holding" value={`${change.current_largest_symbol ?? "N/A"} to ${change.simulated_largest_symbol ?? "N/A"}`} />
        <MetricBlock label="Largest weight change" value={formatSignedPercent(change.largest_weight_change)} />
        <MetricBlock label="HHI change" value={formatSignedNumber(change.hhi_change)} />
      </div>
    </Card>
  );
}

function EstimatedDistributionCard({ rows, currency }: { rows: SimulatedAllocationLine[]; currency: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Estimated value distribution</CardTitle>
      </CardHeader>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((row) => (
          <MetricBlock
            key={row.symbol}
            label={`${row.symbol} · ${formatPercent(row.weight)}`}
            value={formatCurrency(row.estimated_value, currency)}
          />
        ))}
      </div>
    </Card>
  );
}

function MetricBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-ink">{value}</p>
    </div>
  );
}

function buildCurrentTargetWeights(holdings: Holding[]) {
  const total = holdings.reduce((sum, holding) => sum + (holding.market_value ?? 0), 0);
  if (total <= 0) {
    return Object.fromEntries(holdings.map((holding) => [holding.symbol.toUpperCase(), 0]));
  }
  return Object.fromEntries(
    holdings.map((holding) => [holding.symbol.toUpperCase(), roundPercent(((holding.market_value ?? 0) / total) * 100)])
  );
}

function currentWeight(holding: Holding, holdings: Holding[]) {
  const total = holdings.reduce((sum, row) => sum + (row.market_value ?? 0), 0);
  return total > 0 ? (holding.market_value ?? 0) / total : 0;
}

function sumActiveWeights(weights: TargetWeights, removedSymbols: string[]) {
  return Object.entries(weights).reduce((sum, [symbol, weight]) => (removedSymbols.includes(symbol) ? sum : sum + weight), 0);
}

function getFeatureDisabledError(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const details = typeof error.details === "object" && error.details !== null ? error.details : {};
  const feature = "feature" in details ? details.feature : null;
  return error.code === "feature_disabled" || feature === "ENABLE_SIMULATOR" ? error : null;
}

function roundPercent(value: number) {
  return Math.round(value * 100) / 100;
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2
  }).format(value);
}

function formatSignedPercent(value: number | null) {
  if (value === null) return "N/A";
  const formatted = formatPercent(value);
  return value > 0 ? `+${formatted}` : formatted;
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}

function formatSignedNumber(value: number) {
  return `${value > 0 ? "+" : ""}${formatNumber(value)}`;
}
