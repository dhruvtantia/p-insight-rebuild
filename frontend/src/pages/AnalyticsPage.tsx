import { AlertTriangle, BarChart3, PieChart, RefreshCw, ShieldAlert, TrendingUp, Upload } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { Badge, Button, Card, CardTitle, EmptyState, ErrorState, LoadingState, Table, Td, Th } from "../components/ui";
import { useAnalytics } from "../hooks/useAnalytics";
import { usePortfolios } from "../hooks/usePortfolios";
import type {
  AllocationAnalytics,
  AllocationBucket,
  PerformanceAnalytics,
  PortfolioAnalyticsSummary,
  RiskAnalytics,
  RuleInsight
} from "../types/analytics";

const TABS = ["Overview", "Allocation", "Risk", "Performance", "Rules"] as const;
type AnalyticsTab = (typeof TABS)[number];
const CHART_COLORS = ["#0f766e", "#d59a1a", "#e05d4f", "#2563eb", "#7c3aed", "#64748b"];

export function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>("Overview");
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const analytics = useAnalytics(selectedPortfolio?.id);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!portfolios.data?.length) {
    return (
      <div className="space-y-6">
        <AnalyticsHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before viewing analytics." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  if (analytics.isLoading) {
    return (
      <div className="space-y-6">
        <AnalyticsHeader />
        <LoadingState label="Loading analytics" />
      </div>
    );
  }

  if (
    analytics.isError ||
    !analytics.summary.data ||
    !analytics.allocation.data ||
    !analytics.risk.data ||
    !analytics.performance.data ||
    !analytics.rules.data
  ) {
    return (
      <div className="space-y-6">
        <AnalyticsHeader />
        <ErrorState title="Unable to load analytics" detail={analytics.error?.message} />
      </div>
    );
  }

  const summary = analytics.summary.data;
  const allocation = analytics.allocation.data;
  const risk = analytics.risk.data;
  const performance = analytics.performance.data;
  const rules = analytics.rules.data;

  return (
    <div className="space-y-6">
      <AnalyticsHeader
        isRecalculating={analytics.recalculate.isPending}
        recalculatedAt={analytics.recalculate.data?.generated_at}
        errorMessage={analytics.recalculate.error?.message}
        onRecalculate={() => analytics.recalculate.mutate()}
      />

      <Card>
        <div className="flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <Button
              key={tab}
              type="button"
              variant={activeTab === tab ? "primary" : "secondary"}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </Button>
          ))}
        </div>
      </Card>

      {summary.holdings.length === 0 ? <EmptyAnalyticsState /> : null}

      {activeTab === "Overview" ? (
        <OverviewSection summary={summary} risk={risk} rules={rules} />
      ) : activeTab === "Allocation" ? (
        <AllocationSection allocation={allocation} currency={summary.base_currency} />
      ) : activeTab === "Risk" ? (
        <RiskSection risk={risk} />
      ) : activeTab === "Performance" ? (
        <PerformanceSection performance={performance} currency={summary.base_currency} />
      ) : (
        <RulesSection rules={rules} />
      )}
    </div>
  );
}

function AnalyticsHeader({
  isRecalculating,
  recalculatedAt,
  errorMessage,
  onRecalculate
}: {
  isRecalculating?: boolean;
  recalculatedAt?: string;
  errorMessage?: string;
  onRecalculate?: () => void;
}) {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Analytics</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio analytics</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Backend-calculated allocation, risk, performance, and rule-based insights.
        </p>
        {recalculatedAt ? <p className="mt-2 text-sm text-slate-500">Recalculated {formatDateTime(recalculatedAt)}</p> : null}
        {errorMessage ? <p className="mt-2 text-sm text-coral">{errorMessage}</p> : null}
      </div>
      {onRecalculate ? (
        <Button type="button" onClick={onRecalculate} disabled={isRecalculating}>
          <RefreshCw className={isRecalculating ? "animate-spin" : ""} size={16} />
          {isRecalculating ? "Recalculating" : "Recalculate"}
        </Button>
      ) : null}
    </section>
  );
}

function EmptyAnalyticsState() {
  return (
    <Card className="border-dashed">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>No holdings to analyze</CardTitle>
          <p className="mt-2 text-sm text-slate-600">Upload or add holdings to populate analytics sections.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/upload">
            <Button>
              <Upload size={16} />
              Upload holdings
            </Button>
          </Link>
          <Link to="/holdings">
            <Button variant="secondary">Add manually</Button>
          </Link>
        </div>
      </div>
    </Card>
  );
}

function OverviewSection({
  summary,
  risk,
  rules
}: {
  summary: PortfolioAnalyticsSummary;
  risk: RiskAnalytics;
  rules: RuleInsight[];
}) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Total Value" value={formatCurrency(summary.total_portfolio_value, summary.base_currency)} icon={PieChart} />
        <MetricCard title="Cost Basis" value={formatCurrency(summary.total_cost_basis, summary.base_currency)} />
        <MetricCard
          title="Unrealized P/L"
          value={formatCurrency(summary.total_unrealized_gain_loss, summary.base_currency)}
          tone={summary.total_unrealized_gain_loss < 0 ? "negative" : "positive"}
        />
        <MetricCard title="Unrealized P/L %" value={formatPercent(summary.total_unrealized_gain_loss_pct)} icon={TrendingUp} />
        <MetricCard title="Largest Holding" value={summary.largest_holding?.symbol ?? "N/A"} detail={formatPercent(summary.largest_holding?.weight ?? null)} />
        <MetricCard title="Concentration" value={risk.concentration.status} detail={risk.concentration.message} icon={ShieldAlert} />
        <MetricCard title="Rules" value={String(rules.length)} detail="Active backend insights" icon={AlertTriangle} />
        <MetricCard title="Holdings" value={String(summary.holdings.length)} />
      </div>
      <HoldingsAnalyticsTable summary={summary} />
    </div>
  );
}

function AllocationSection({ allocation, currency }: { allocation: AllocationAnalytics; currency: string }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <AllocationChart title="Asset allocation" data={allocation.asset_allocation} currency={currency} />
        <AllocationChart title="Sector allocation" data={allocation.sector_allocation} currency={currency} />
      </div>
      <AllocationTable title="Currency exposure" data={allocation.currency_exposure} currency={currency} />
      <AllocationTable title="Asset allocation detail" data={allocation.asset_allocation} currency={currency} />
      <AllocationTable title="Sector allocation detail" data={allocation.sector_allocation} currency={currency} />
    </div>
  );
}

function RiskSection({ risk }: { risk: RiskAnalytics }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <RiskMetricCard title="Volatility" metric={risk.volatility} />
        <RiskMetricCard title="Sharpe Ratio" metric={risk.sharpe_ratio} />
        <RiskMetricCard title="Max Drawdown" metric={risk.max_drawdown} />
      </div>
      <Card>
        <CardTitle>Concentration risk</CardTitle>
        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <MetricBlock label="Status" value={risk.concentration.status} />
          <MetricBlock label="Largest holding" value={risk.concentration.largest_holding?.symbol ?? "N/A"} />
          <MetricBlock label="Largest weight" value={formatPercent(risk.concentration.largest_holding?.weight ?? null)} />
          <MetricBlock label="Top 5 weight" value={formatPercent(risk.concentration.top_5_weight)} />
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-600">{risk.concentration.message}</p>
      </Card>
    </div>
  );
}

function PerformanceSection({ performance, currency }: { performance: PerformanceAnalytics; currency: string }) {
  const chartData = [
    ...performance.top_gainers.map((holding) => ({ ...holding, type: "Gainer" })),
    ...performance.top_losers.map((holding) => ({ ...holding, type: "Loser" }))
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard title="Total Cost Basis" value={formatCurrency(performance.total_cost_basis, currency)} />
        <MetricCard
          title="Unrealized P/L"
          value={formatCurrency(performance.total_unrealized_gain_loss, currency)}
          tone={performance.total_unrealized_gain_loss < 0 ? "negative" : "positive"}
        />
        <MetricCard title="Unrealized P/L %" value={formatPercent(performance.total_unrealized_gain_loss_pct)} />
      </div>
      {chartData.length ? (
        <Card>
          <CardTitle>Top gainers and losers</CardTitle>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="symbol" />
                <YAxis tickFormatter={(value) => formatCompactCurrency(Number(value), currency)} />
            <Tooltip formatter={(value) => formatCurrency(Number(value), currency)} />
                <Bar dataKey="unrealized_gain_loss" radius={[4, 4, 0, 0]}>
                  {chartData.map((item) => (
                    <Cell key={`${item.symbol}-${item.type}`} fill={item.unrealized_gain_loss < 0 ? "#e05d4f" : "#0f766e"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : (
        <EmptyState title="Performance" detail="Price and cost basis data are needed before gainers and losers can be displayed." />
      )}
      <PerformanceTable performance={performance} currency={currency} />
    </div>
  );
}

function RulesSection({ rules }: { rules: RuleInsight[] }) {
  if (!rules.length) {
    return <EmptyState title="Rules" detail="No rule-based insights are active for this portfolio." />;
  }

  return (
    <div className="grid gap-4">
      {rules.map((rule) => (
        <Card key={rule.rule_id}>
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>{rule.title}</CardTitle>
                <Badge>{rule.severity}</Badge>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">{rule.message}</p>
              {rule.affected_symbols.length ? (
                <p className="mt-3 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
                  {rule.affected_symbols.join(", ")}
                </p>
              ) : null}
            </div>
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{rule.rule_id}</span>
          </div>
        </Card>
      ))}
    </div>
  );
}

function AllocationChart({ title, data, currency }: { title: string; data: AllocationBucket[]; currency: string }) {
  if (!data.length) {
    return <EmptyState title={title} detail="No priced holdings are available for this allocation." />;
  }

  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsPieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={92} paddingAngle={2}>
              {data.map((bucket, index) => (
                <Cell key={bucket.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => formatCurrency(Number(value), currency)} />
          </RechartsPieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid gap-2">
        {data.slice(0, 6).map((bucket, index) => (
          <div key={bucket.name} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex min-w-0 items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
              <span className="truncate text-slate-700">{bucket.name}</span>
            </span>
            <span className="font-medium text-ink">{formatPercent(bucket.weight)}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function AllocationTable({ title, data, currency }: { title: string; data: AllocationBucket[]; currency: string }) {
  if (!data.length) {
    return <EmptyState title={title} detail="No allocation rows are available." />;
  }

  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <div className="mt-4">
        <Table>
          <thead>
            <tr>
              <Th>Name</Th>
              <Th>Value</Th>
              <Th>Weight</Th>
              <Th>Symbols</Th>
            </tr>
          </thead>
          <tbody>
            {data.map((bucket) => (
              <tr key={bucket.name}>
                <Td className="font-semibold text-ink">{bucket.name}</Td>
                <Td>{formatCurrency(bucket.value, currency)}</Td>
                <Td>{formatPercent(bucket.weight)}</Td>
                <Td>{bucket.symbols.join(", ") || "N/A"}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </Card>
  );
}

function HoldingsAnalyticsTable({ summary }: { summary: PortfolioAnalyticsSummary }) {
  if (!summary.holdings.length) {
    return <EmptyState title="Holdings analytics" detail="No holdings are available." />;
  }

  return (
    <Card>
      <CardTitle>Holdings analytics</CardTitle>
      <div className="mt-4">
        <Table>
          <thead>
            <tr>
              <Th>Symbol</Th>
              <Th>Market Value</Th>
              <Th>Weight</Th>
              <Th>Cost Basis</Th>
              <Th>Unrealized P/L</Th>
              <Th>Unrealized P/L %</Th>
            </tr>
          </thead>
          <tbody>
            {summary.holdings.map((holding) => (
              <tr key={holding.holding_id}>
                <Td className="font-semibold text-ink">{holding.symbol}</Td>
                <Td>{formatCurrency(holding.market_value, summary.base_currency)}</Td>
                <Td>{formatPercent(holding.weight)}</Td>
                <Td>{formatCurrency(holding.cost_basis, summary.base_currency)}</Td>
                <Td>{formatCurrency(holding.unrealized_gain_loss, summary.base_currency)}</Td>
                <Td>{formatPercent(holding.unrealized_gain_loss_pct)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </Card>
  );
}

function PerformanceTable({ performance, currency }: { performance: PerformanceAnalytics; currency: string }) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <PerformanceList title="Top gainers" holdings={performance.top_gainers} currency={currency} />
      <PerformanceList title="Top losers" holdings={performance.top_losers} currency={currency} />
    </div>
  );
}

function PerformanceList({
  title,
  holdings,
  currency
}: {
  title: string;
  holdings: Array<{ symbol: string; unrealized_gain_loss: number; unrealized_gain_loss_pct: number | null }>;
  currency: string;
}) {
  if (!holdings.length) {
    return <EmptyState title={title} detail="No rows are available." />;
  }

  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <div className="mt-4">
        <Table>
          <thead>
            <tr>
              <Th>Symbol</Th>
              <Th>Unrealized P/L</Th>
              <Th>Unrealized P/L %</Th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((holding) => (
              <tr key={holding.symbol}>
                <Td className="font-semibold text-ink">{holding.symbol}</Td>
                <Td>{formatCurrency(holding.unrealized_gain_loss, currency)}</Td>
                <Td>{formatPercent(holding.unrealized_gain_loss_pct)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </Card>
  );
}

function RiskMetricCard({ title, metric }: { title: string; metric: { value: number | null; status: string; message: string } }) {
  return (
    <Card>
      <p className="text-sm text-slate-600">{title}</p>
      <p className="mt-2 text-xl font-semibold text-ink">{metric.value === null ? "N/A" : String(metric.value)}</p>
      <p className="mt-1 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{metric.status}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{metric.message}</p>
    </Card>
  );
}

function MetricCard({
  title,
  value,
  detail,
  tone,
  icon: Icon
}: {
  title: string;
  value: string;
  detail?: string;
  tone?: "positive" | "negative";
  icon?: typeof PieChart;
}) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-600">{title}</p>
          <p className={["mt-2 text-xl font-semibold", tone === "negative" ? "text-coral" : tone === "positive" ? "text-emerald-700" : "text-ink"].join(" ")}>
            {value}
          </p>
          {detail ? <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p> : null}
        </div>
        {Icon ? <Icon className="text-accent" size={22} /> : null}
      </div>
    </Card>
  );
}

function MetricBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className="mt-1 text-base font-semibold text-ink">{value}</p>
    </div>
  );
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function formatCompactCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(value);
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
