import { AlertTriangle, BarChart3, LineChart as LineChartIcon, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import {
  Badge,
  Button,
  Card,
  CardHeader,
  CardTitle,
  DataStatusBadge,
  EmptyState,
  ErrorState,
  FeatureDisabledState,
  LoadingState,
  Table,
  Td,
  Th
} from "../components/ui";
import { useHoldings } from "../hooks/useHoldings";
import { useOptimizer } from "../hooks/useOptimizer";
import { usePortfolios } from "../hooks/usePortfolios";
import { ApiError } from "../services/apiClient";
import type { HistoricalPeriod } from "../types/performance";
import type { OptimizerMetricSet, OptimizerResponse, OptimizerStatus } from "../types/optimizer";

const PERIODS: HistoricalPeriod[] = ["1M", "3M", "6M", "1Y", "5Y"];

export function OptimizerPage() {
  const [period, setPeriod] = useState<HistoricalPeriod>("1M");
  const [frontierPoints, setFrontierPoints] = useState(5);
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const holdings = useHoldings(selectedPortfolio?.id);
  const optimizer = useOptimizer(selectedPortfolio?.id);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!selectedPortfolio) {
    return (
      <div className="space-y-6">
        <OptimizerHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before running optimization scenarios." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  const disabledError = getFeatureDisabledError(optimizer.optimization.error);

  function handleRunOptimizer() {
    optimizer.optimization.mutate({
      period,
      frontier_points: frontierPoints
    });
  }

  return (
    <div className="space-y-6">
      <OptimizerHeader />
      <AdviceDisclaimer />

      {disabledError ? (
        <FeatureDisabledState
          feature="Optimizer"
          detail="The backend optimizer feature flag is disabled in this environment."
        />
      ) : null}

      {holdings.isLoading ? (
        <LoadingState label="Loading holdings" />
      ) : holdings.isError ? (
        <ErrorState title="Unable to load holdings" detail={holdings.error.message} />
      ) : !holdings.data?.length ? (
        <EmptyState title="No holdings to optimize" detail="Add priced holdings before running optimizer scenarios." />
      ) : (
        <>
          <OptimizerControls
            period={period}
            frontierPoints={frontierPoints}
            disabled={Boolean(disabledError) || optimizer.optimization.isPending}
            onPeriodChange={setPeriod}
            onFrontierPointsChange={setFrontierPoints}
            onRun={handleRunOptimizer}
          />

          {optimizer.optimization.isPending ? <LoadingState label="Running optimizer" /> : null}
          {optimizer.optimization.isError && !disabledError ? (
            <ErrorState title="Unable to run optimizer" detail={optimizer.optimization.error.message} />
          ) : null}
          {optimizer.optimization.data ? <OptimizerResults response={optimizer.optimization.data} /> : null}
        </>
      )}
    </div>
  );
}

function OptimizerHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Optimizer</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio optimizer</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Compare backend-generated optimization scenarios from historical estimates and explicit assumptions.
        </p>
      </div>
      <Link to="/simulate">
        <Button variant="secondary">Open simulator</Button>
      </Link>
    </section>
  );
}

function AdviceDisclaimer() {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-amber-700" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-amber-900">Optimizer output is not financial advice</h3>
          <p className="mt-1 text-sm text-amber-800">
            Results are hypothetical estimates from backend calculations. They do not execute trades and should be reviewed as analysis inputs only.
          </p>
        </div>
      </div>
    </Card>
  );
}

function OptimizerControls({
  period,
  frontierPoints,
  disabled,
  onPeriodChange,
  onFrontierPointsChange,
  onRun
}: {
  period: HistoricalPeriod;
  frontierPoints: number;
  disabled: boolean;
  onPeriodChange: (period: HistoricalPeriod) => void;
  onFrontierPointsChange: (points: number) => void;
  onRun: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Optimizer run settings</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Choose the historical window and requested frontier density.</p>
        </div>
        <Sparkles className="text-accent" size={22} />
      </CardHeader>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-slate-600">Period</span>
            {PERIODS.map((candidate) => (
              <Button
                key={candidate}
                type="button"
                variant={period === candidate ? "primary" : "secondary"}
                className="h-8 px-3"
                onClick={() => onPeriodChange(candidate)}
                disabled={disabled}
              >
                {candidate}
              </Button>
            ))}
          </div>
          <label className="block max-w-xs">
            <span className="mb-1 block text-sm font-medium text-slate-600">Frontier points</span>
            <input
              className="h-10 w-full rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15 disabled:opacity-60"
              type="number"
              min={2}
              max={20}
              value={frontierPoints}
              onChange={(event) => onFrontierPointsChange(clamp(Number(event.target.value), 2, 20))}
              disabled={disabled}
            />
          </label>
        </div>
        <Button type="button" onClick={onRun} disabled={disabled}>
          <Sparkles size={16} />
          Run optimizer
        </Button>
      </div>
    </Card>
  );
}

function OptimizerResults({ response }: { response: OptimizerResponse }) {
  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status={response.status} />
              <DataStatusBadge status={response.data_status} />
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Generated {formatDateTime(response.generated_at)} for {response.period}. Metric availability is controlled by the backend optimizer status.
            </p>
          </div>
          <BarChart3 className="text-accent" size={24} />
        </div>
      </Card>

      {response.status !== "ok" ? (
        <MetricStatusState status={response.status} warnings={response.warnings} />
      ) : null}

      {response.warnings.map((warning) => (
        <WarningBanner key={warning} detail={warning} />
      ))}
      {response.data_status.warning ? <WarningBanner detail={response.data_status.warning} /> : null}

      <section className="grid gap-4 xl:grid-cols-3">
        <MetricCard title="Current portfolio metrics" metrics={response.current_portfolio_metrics} />
        <MetricCard title="Minimum variance portfolio" metrics={response.min_variance_target_weights.metrics} />
        <MetricCard title="Maximum Sharpe portfolio" metrics={response.max_sharpe_target_weights.metrics} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <AllocationComparisonTable response={response} />
        <AssumptionsCard response={response} />
      </section>

      {response.efficient_frontier_points.length ? (
        <EfficientFrontierChart response={response} />
      ) : (
        <EmptyState title="Efficient frontier" detail="No efficient frontier points were returned for this optimizer run." />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: OptimizerStatus }) {
  if (status === "ok") {
    return <Badge tone="success">Optimizer OK</Badge>;
  }
  if (status === "insufficient_history") {
    return <Badge tone="warning">Insufficient history</Badge>;
  }
  return <Badge tone="warning">Unsupported</Badge>;
}

function MetricStatusState({ status, warnings }: { status: OptimizerStatus; warnings: string[] }) {
  return (
    <Card className="border-dashed">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-amber-700" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-ink">{status === "insufficient_history" ? "Insufficient history" : "Optimizer unsupported"}</h3>
          <p className="mt-1 text-sm text-slate-600">
            {warnings[0] ?? "The backend could not produce complete optimizer metrics for this portfolio and period."}
          </p>
        </div>
      </div>
    </Card>
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

function MetricCard({ title, metrics }: { title: string; metrics: OptimizerMetricSet }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <div className="grid gap-3">
        <MetricBlock label="Expected annual return" value={formatPercent(metrics.expected_annual_return)} />
        <MetricBlock label="Annualized volatility" value={formatPercent(metrics.annualized_volatility)} />
        <MetricBlock label="Sharpe ratio" value={formatNumber(metrics.sharpe_ratio)} />
      </div>
    </Card>
  );
}

function AllocationComparisonTable({ response }: { response: OptimizerResponse }) {
  const symbols = Array.from(
    new Set([
      ...Object.keys(response.current_weights),
      ...Object.keys(response.min_variance_target_weights.target_weights),
      ...Object.keys(response.max_sharpe_target_weights.target_weights)
    ])
  ).sort();

  if (!symbols.length) {
    return <EmptyState title="Allocation comparison" detail="No target weights were returned by the optimizer." />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Allocation comparison</CardTitle>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Current</Th>
            <Th>Min variance</Th>
            <Th>Max Sharpe</Th>
          </tr>
        </thead>
        <tbody>
          {symbols.map((symbol) => (
            <tr key={symbol}>
              <Td className="font-medium text-ink">{symbol}</Td>
              <Td>{formatPercent(response.current_weights[symbol] ?? null)}</Td>
              <Td>{formatPercent(response.min_variance_target_weights.target_weights[symbol] ?? null)}</Td>
              <Td>{formatPercent(response.max_sharpe_target_weights.target_weights[symbol] ?? null)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function AssumptionsCard({ response }: { response: OptimizerResponse }) {
  const rows = [
    ["Long-only weights", response.assumptions.long_only],
    ["No tax modeling", response.assumptions.no_taxes],
    ["No transaction costs", response.assumptions.no_transaction_costs],
    ["No liquidity constraints", response.assumptions.no_liquidity_constraints],
    ["Historical estimates only", response.assumptions.historical_estimates_only],
    ["Not investment advice", response.assumptions.not_investment_advice]
  ] as const;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Assumptions and disclaimers</CardTitle>
      </CardHeader>
      <div className="grid gap-3">
        {rows.map(([label, enabled]) => (
          <div key={label} className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface p-3">
            <span className="text-sm font-medium text-ink">{label}</span>
            <Badge tone={enabled ? "success" : "warning"}>{enabled ? "Yes" : "No"}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

function EfficientFrontierChart({ response }: { response: OptimizerResponse }) {
  const data = response.efficient_frontier_points
    .filter((point) => point.annualized_volatility !== null && point.target_return !== null)
    .map((point) => ({
      index: point.index,
      volatility: point.annualized_volatility,
      return: point.target_return,
      sharpe: point.sharpe_ratio
    }));

  if (!data.length) {
    return <EmptyState title="Efficient frontier" detail="Frontier points were returned, but chartable return and volatility values are unavailable." />;
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Efficient frontier</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Chart renders only backend-returned points with return and volatility values.</p>
        </div>
        <LineChartIcon className="text-accent" size={22} />
      </CardHeader>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="volatility"
              tickFormatter={(value) => formatPercent(Number(value))}
              label={{ value: "Volatility", position: "insideBottom", offset: -4 }}
            />
            <YAxis tickFormatter={(value) => formatPercent(Number(value))} />
            <Tooltip
              formatter={(value, name) => [
                name === "sharpe" ? formatNumber(Number(value)) : formatPercent(Number(value)),
                String(name)
              ]}
              labelFormatter={(value) => `Volatility ${formatPercent(Number(value))}`}
            />
            <Legend />
            <Line type="monotone" dataKey="return" stroke="#0f766e" strokeWidth={2} dot />
            <Line type="monotone" dataKey="sharpe" stroke="#d59a1a" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
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

function getFeatureDisabledError(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const details = typeof error.details === "object" && error.details !== null ? error.details : {};
  const feature = "feature" in details ? details.feature : null;
  return error.code === "feature_disabled" || feature === "ENABLE_OPTIMIZER" ? error : null;
}

function formatPercent(value: number | null) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2
  }).format(value);
}

function formatNumber(value: number | null) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 3
  }).format(value);
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function clamp(value: number, min: number, max: number) {
  if (!Number.isFinite(value)) return min;
  return Math.min(Math.max(value, min), max);
}
