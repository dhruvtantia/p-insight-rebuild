import { AlertTriangle, BarChart3, Bot, Clock, PieChart, Plus, RefreshCw, Upload, WalletCards } from "lucide-react";
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

import {
  Badge,
  Button,
  Card,
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
import { useAnalytics } from "../hooks/useAnalytics";
import { useDashboardBundle } from "../hooks/useDashboardBundle";
import { useHoldings } from "../hooks/useHoldings";
import { usePortfolioPrices } from "../hooks/usePortfolioPrices";
import { usePortfolios } from "../hooks/usePortfolios";
import { ApiError } from "../services/apiClient";
import type { PortfolioPriceRefreshResponse } from "../services/marketDataApi";
import type { HoldingAnalytics, PortfolioAnalyticsSummary, RuleInsight } from "../types/analytics";
import type {
  DashboardActionItem,
  DashboardBundleResponse,
  DashboardRiskSummary,
  DashboardTopHolding
} from "../types/dashboard";
import type { Holding } from "../types/holdings";
import type { Portfolio } from "../types/portfolio";

const CHART_COLORS = ["#0f766e", "#d59a1a", "#e05d4f", "#2563eb", "#7c3aed", "#64748b"];

type DashboardFallbackReason = {
  kind: "disabled" | "unavailable";
  message: string;
};

type ChartAllocationItem = {
  name: string;
  value: number;
  weight: number;
  symbols: string[];
};

export function DashboardPage() {
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const dashboardBundle = useDashboardBundle(selectedPortfolio?.id);
  const fallbackReason = getDashboardFallbackReason(dashboardBundle.error);
  const shouldUseLegacyFallback = Boolean(!dashboardBundle.data && fallbackReason);
  const analytics = useAnalytics(selectedPortfolio?.id, { enabled: shouldUseLegacyFallback });
  const holdings = useHoldings(selectedPortfolio?.id);
  const portfolioPrices = usePortfolioPrices(selectedPortfolio?.id);
  const latestPriceUpdatedAt = getLatestPriceUpdatedAt(holdings.data ?? []);

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!portfolios.data?.length) {
    return (
      <div className="space-y-6">
        <DashboardHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio to populate the dashboard." />
        <Link to="/onboarding">
          <Button>
            <Plus size={16} />
            Create portfolio
          </Button>
        </Link>
      </div>
    );
  }

  if (dashboardBundle.isLoading && !dashboardBundle.data) {
    return (
      <div className="space-y-6">
        <DashboardHeader />
        <LoadingState label="Loading dashboard bundle" />
      </div>
    );
  }

  if (dashboardBundle.data) {
    return (
      <DashboardBundleContent
        bundle={dashboardBundle.data}
        portfolio={selectedPortfolio!}
        isRefreshing={portfolioPrices.refreshPrices.isPending}
        refreshResult={portfolioPrices.refreshPrices.data}
        refreshError={portfolioPrices.refreshPrices.error?.message}
        onRefresh={() => portfolioPrices.refreshPrices.mutate()}
      />
    );
  }

  if (shouldUseLegacyFallback) {
    return (
      <LegacyDashboardContent
        portfolio={selectedPortfolio!}
        fallbackReason={fallbackReason!}
        analytics={analytics}
        latestPriceUpdatedAt={latestPriceUpdatedAt}
        isRefreshing={portfolioPrices.refreshPrices.isPending}
        refreshResult={portfolioPrices.refreshPrices.data}
        refreshError={portfolioPrices.refreshPrices.error?.message}
        onRefresh={() => portfolioPrices.refreshPrices.mutate()}
      />
    );
  }

  if (dashboardBundle.isError) {
    return (
      <div className="space-y-6">
        <DashboardHeader />
        <ErrorState title="Unable to load dashboard bundle" detail={dashboardBundle.error.message} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DashboardHeader />
      <EmptyState title="Dashboard unavailable" detail="No dashboard data was returned for this portfolio." />
    </div>
  );
}

function DashboardBundleContent({
  bundle,
  portfolio,
  isRefreshing,
  refreshResult,
  refreshError,
  onRefresh
}: {
  bundle: DashboardBundleResponse;
  portfolio: Portfolio;
  isRefreshing: boolean;
  refreshResult?: PortfolioPriceRefreshResponse;
  refreshError?: string;
  onRefresh: () => void;
}) {
  const isEmptyPortfolio = bundle.kpis.holdings_count === 0;

  return (
    <div className="space-y-6">
      <DashboardHeader dataStatus={bundle.data_status} />
      <PortfolioIdentity portfolio={portfolio} />
      <DashboardDataStatusPanel bundle={bundle} />
      <DashboardSummaryCards bundle={bundle} />
      <PriceActionPanel
        isRefreshing={isRefreshing}
        refreshResult={refreshResult}
        errorMessage={refreshError}
        onRefresh={onRefresh}
      />
      <AIAdvisorCard isEmptyPortfolio={isEmptyPortfolio} actionItem={bundle.action_items[0]} />

      {isEmptyPortfolio ? (
        <EmptyPortfolioCta />
      ) : (
        <>
          <div className="grid gap-6 xl:grid-cols-2">
            <AllocationChart title="Asset allocation" data={bundle.asset_allocation} currency={bundle.kpis.base_currency} />
            <AllocationChart title="Sector allocation" data={bundle.sector_allocation} currency={bundle.kpis.base_currency} />
          </div>
          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <DashboardTopHoldingsCard holdings={bundle.top_holdings} currency={bundle.kpis.base_currency} />
            <ConcentrationSummaryCard risk={bundle.risk} />
          </div>
          <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
            <ActionItemsCard items={bundle.action_items} />
            <DataQualityCard bundle={bundle} />
          </div>
        </>
      )}
    </div>
  );
}

function LegacyDashboardContent({
  portfolio,
  fallbackReason,
  analytics,
  latestPriceUpdatedAt,
  isRefreshing,
  refreshResult,
  refreshError,
  onRefresh
}: {
  portfolio: Portfolio;
  fallbackReason: DashboardFallbackReason;
  analytics: ReturnType<typeof useAnalytics>;
  latestPriceUpdatedAt: string | null;
  isRefreshing: boolean;
  refreshResult?: PortfolioPriceRefreshResponse;
  refreshError?: string;
  onRefresh: () => void;
}) {
  if (analytics.isLoading) {
    return (
      <div className="space-y-6">
        <DashboardHeader />
        <FallbackNotice reason={fallbackReason} />
        <LoadingState label="Loading fallback dashboard analytics" />
      </div>
    );
  }

  if (analytics.isError || !analytics.summary.data || !analytics.allocation.data || !analytics.rules.data) {
    return (
      <div className="space-y-6">
        <DashboardHeader />
        <FallbackNotice reason={fallbackReason} />
        <ErrorState title="Unable to load analytics" detail={analytics.error?.message} />
      </div>
    );
  }

  const summary = analytics.summary.data;
  const allocation = analytics.allocation.data;
  const rules = analytics.rules.data;
  const isEmptyPortfolio = summary.holdings.length === 0;
  const missingDataRules = rules.filter(
    (rule) => rule.rule_id === "MISSING_PRICE_DATA" || rule.rule_id === "MISSING_COST_BASIS"
  );

  return (
    <div className="space-y-6">
      <DashboardHeader />
      <FallbackNotice reason={fallbackReason} />
      <PortfolioIdentity portfolio={portfolio} />
      <SummaryCards summary={summary} latestPriceUpdatedAt={latestPriceUpdatedAt} />
      <PriceActionPanel
        isRefreshing={isRefreshing}
        refreshResult={refreshResult}
        errorMessage={refreshError}
        onRefresh={onRefresh}
      />
      <AIAdvisorCard isEmptyPortfolio={isEmptyPortfolio} topRule={rules[0]} />

      {isEmptyPortfolio ? (
        <EmptyPortfolioCta />
      ) : (
        <>
          <div className="grid gap-6 xl:grid-cols-2">
            <AllocationChart title="Asset allocation" data={allocation.asset_allocation} currency={summary.base_currency} />
            <AllocationChart title="Sector allocation" data={allocation.sector_allocation} currency={summary.base_currency} />
          </div>
          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <LegacyTopHoldingsCard holdings={summary.holdings} currency={summary.base_currency} />
            <PortfolioHistoryPlaceholder />
          </div>
          <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
            <InsightsCard rules={rules} />
            <MissingDataCard rules={missingDataRules} />
          </div>
        </>
      )}
    </div>
  );
}

function DashboardHeader({ dataStatus }: { dataStatus?: DashboardBundleResponse["data_status"] }) {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Dashboard</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio command center</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Portfolio analytics and rule-based insights rendered from backend results.
        </p>
        {dataStatus ? (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <DataStatusBadge status={dataStatus} />
            {dataStatus.warning ? <span className="text-sm text-amber-700">{dataStatus.warning}</span> : null}
          </div>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-2">
        <Link to="/analytics">
          <Button variant="secondary">
            <BarChart3 size={16} />
            Analytics
          </Button>
        </Link>
        <Link to="/holdings">
          <Button variant="secondary">Manage holdings</Button>
        </Link>
      </div>
    </section>
  );
}

function FallbackNotice({ reason }: { reason: DashboardFallbackReason }) {
  if (reason.kind === "disabled") {
    return (
      <FeatureDisabledState
        feature="Dashboard bundle"
        detail="The dashboard bundle endpoint is disabled, so this page is using the existing analytics dashboard fallback."
      />
    );
  }

  return (
    <ErrorState
      title="Dashboard bundle unavailable"
      detail={`${reason.message} Showing the existing analytics dashboard fallback.`}
    />
  );
}

function PortfolioIdentity({ portfolio }: { portfolio: Portfolio }) {
  return (
    <Card>
      <div className="grid gap-4 md:grid-cols-4">
        <SummaryItem label="Selected portfolio" value={portfolio.name} />
        <SummaryItem label="Base currency" value={portfolio.base_currency} />
        <SummaryItem label="Benchmark" value={portfolio.benchmark_symbol ?? "N/A"} />
        <SummaryItem label="Risk-free rate" value={portfolio.risk_free_rate === null ? "N/A" : `${portfolio.risk_free_rate}`} />
      </div>
    </Card>
  );
}

function DashboardDataStatusPanel({ bundle }: { bundle: DashboardBundleResponse }) {
  return (
    <Card>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle>Data status</CardTitle>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Dashboard values were generated by the backend at {formatDateTime(bundle.generated_at)}.
          </p>
        </div>
        <DataStatusBadge status={bundle.data_status} />
      </div>
      {bundle.data_status.warning ? (
        <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {bundle.data_status.warning}
        </p>
      ) : null}
    </Card>
  );
}

function DashboardSummaryCards({ bundle }: { bundle: DashboardBundleResponse }) {
  const { kpis } = bundle;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard title="Total Invested" value={formatCurrency(kpis.total_invested, kpis.base_currency)} icon={WalletCards} />
      <MetricCard title="Current Value" value={formatCurrency(kpis.current_value, kpis.base_currency)} icon={BarChart3} />
      <MetricCard
        title="Unrealized P&L"
        value={formatCurrency(kpis.unrealized_pnl, kpis.base_currency)}
        tone={kpis.unrealized_pnl < 0 ? "negative" : "positive"}
      />
      <MetricCard title="Return %" value={formatPercent(kpis.return_percent)} tone={(kpis.return_percent ?? 0) < 0 ? "negative" : "positive"} />
      <MetricCard title="Largest Holding" value={kpis.largest_holding_symbol ?? "N/A"} detail={formatPercent(kpis.largest_holding_weight)} icon={PieChart} />
      <MetricCard title="Holdings Count" value={String(kpis.holdings_count)} detail={`${kpis.priced_holdings_count} priced`} />
      <MetricCard title="Cash %" value={formatPercent(kpis.cash_weight)} />
      <MetricCard title="Data As Of" value={kpisAsOf(bundle)} icon={Clock} />
    </div>
  );
}

function SummaryCards({
  summary,
  latestPriceUpdatedAt
}: {
  summary: PortfolioAnalyticsSummary;
  latestPriceUpdatedAt: string | null;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard title="Total Value" value={formatCurrency(summary.total_portfolio_value, summary.base_currency)} icon={WalletCards} />
      <MetricCard title="Daily Change" value="N/A" detail="Historical daily returns are not available yet." icon={BarChart3} />
      <MetricCard
        title="Total Gain/Loss"
        value={formatCurrency(summary.total_unrealized_gain_loss, summary.base_currency)}
        tone={summary.total_unrealized_gain_loss < 0 ? "negative" : "positive"}
      />
      <MetricCard title="Total Gain/Loss %" value={formatPercent(summary.total_unrealized_gain_loss_pct)} />
      <MetricCard title="Largest Holding" value={summary.largest_holding?.symbol ?? "N/A"} detail={formatPercent(summary.largest_holding?.weight ?? null)} icon={PieChart} />
      <MetricCard title="Holdings Count" value={String(summary.holdings.length)} />
      <MetricCard title="Cash %" value="N/A" detail="Cash tracking is not available yet." />
      <MetricCard title="Last Updated" value={latestPriceUpdatedAt ? formatDateTime(latestPriceUpdatedAt) : "N/A"} icon={Clock} />
    </div>
  );
}

function PriceActionPanel({
  isRefreshing,
  refreshResult,
  errorMessage,
  onRefresh
}: {
  isRefreshing: boolean;
  refreshResult?: PortfolioPriceRefreshResponse;
  errorMessage?: string;
  onRefresh: () => void;
}) {
  const sources = uniqueSources(refreshResult);

  return (
    <Card>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">Price refresh</p>
          <p className="mt-1 text-sm text-slate-600">Refresh backend prices before reviewing analytics.</p>
        </div>
        <Button type="button" onClick={onRefresh} disabled={isRefreshing} className="whitespace-nowrap">
          <RefreshCw className={isRefreshing ? "animate-spin" : ""} size={16} />
          {isRefreshing ? "Refreshing" : "Refresh Prices"}
        </Button>
      </div>
      {refreshResult ? (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-slate-600">
          <span>
            Refreshed {refreshResult.refreshed_count} holding{refreshResult.refreshed_count === 1 ? "" : "s"}.
          </span>
          {sources.map((source) => (
            <Badge key={source} tone={source.toLowerCase().includes("mock") ? "warning" : "neutral"}>
              {source}
            </Badge>
          ))}
        </div>
      ) : null}
      {errorMessage ? (
        <div className="mt-4">
          <ErrorState title="Price refresh failed" detail={errorMessage} />
        </div>
      ) : null}
    </Card>
  );
}

function uniqueSources(refreshResult?: PortfolioPriceRefreshResponse) {
  return Array.from(
    new Set((refreshResult?.holdings ?? refreshResult?.prices ?? []).map((item) => item.source).filter(Boolean))
  ).sort();
}

function AIAdvisorCard({
  isEmptyPortfolio,
  topRule,
  actionItem
}: {
  isEmptyPortfolio: boolean;
  topRule?: RuleInsight;
  actionItem?: DashboardActionItem;
}) {
  const message = isEmptyPortfolio
    ? "Ask the advisor what data is needed before portfolio analysis becomes useful."
    : actionItem
      ? `Start with this backend action item: ${actionItem.message}`
      : topRule
        ? `Start with this active insight: ${topRule.message}`
        : "Generate a backend-context summary or ask a question about allocation, risk, or missing data.";

  return (
    <Card>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          <Bot className="mt-0.5 text-accent" size={22} />
          <div>
            <CardTitle>AI summary</CardTitle>
            <p className="mt-2 text-sm leading-6 text-slate-600">{message}</p>
          </div>
        </div>
        <Link to="/advisor">
          <Button>
            <Bot size={16} />
            Open AI Advisor
          </Button>
        </Link>
      </div>
    </Card>
  );
}

function EmptyPortfolioCta() {
  return (
    <Card className="border-dashed">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>No holdings yet</CardTitle>
          <p className="mt-2 text-sm text-slate-600">Upload or add holdings to populate dashboard analytics.</p>
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

function AllocationChart({ title, data, currency }: { title: string; data: ChartAllocationItem[]; currency: string }) {
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
      <AllocationLegend data={data} />
    </Card>
  );
}

function AllocationLegend({ data }: { data: ChartAllocationItem[] }) {
  return (
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
  );
}

function DashboardTopHoldingsCard({ holdings, currency }: { holdings: DashboardTopHolding[]; currency: string }) {
  if (!holdings.length) {
    return <EmptyState title="Top holdings" detail="Current prices are needed before holding weights can be displayed." />;
  }

  return (
    <Card>
      <CardTitle>Top holdings</CardTitle>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={holdings} layout="vertical" margin={{ left: 12, right: 24 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} />
            <YAxis type="category" dataKey="symbol" width={60} />
            <Tooltip formatter={(value) => formatPercent(Number(value))} />
            <Bar dataKey="weight" fill="#0f766e" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Value</Th>
            <Th>Weight</Th>
            <Th>P&L</Th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={holding.holding_id}>
              <Td className="font-semibold text-ink">{holding.symbol}</Td>
              <Td>{formatCurrency(holding.market_value, currency)}</Td>
              <Td>{formatPercent(holding.weight)}</Td>
              <Td>{formatCurrency(holding.unrealized_gain_loss, holding.currency)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function LegacyTopHoldingsCard({ holdings, currency }: { holdings: HoldingAnalytics[]; currency: string }) {
  const topHoldings = [...holdings]
    .filter((holding) => holding.market_value !== null)
    .sort((a, b) => (b.market_value ?? 0) - (a.market_value ?? 0))
    .slice(0, 5);

  if (!topHoldings.length) {
    return <EmptyState title="Top holdings" detail="Current prices are needed before holding weights can be displayed." />;
  }

  return (
    <Card>
      <CardTitle>Top holdings</CardTitle>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topHoldings} layout="vertical" margin={{ left: 12, right: 24 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} />
            <YAxis type="category" dataKey="symbol" width={60} />
            <Tooltip formatter={(value) => formatPercent(Number(value))} />
            <Bar dataKey="weight" fill="#0f766e" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Value</Th>
            <Th>Weight</Th>
          </tr>
        </thead>
        <tbody>
          {topHoldings.map((holding) => (
            <tr key={holding.holding_id}>
              <Td className="font-semibold text-ink">{holding.symbol}</Td>
              <Td>{formatCurrency(holding.market_value, currency)}</Td>
              <Td>{formatPercent(holding.weight)}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function ConcentrationSummaryCard({ risk }: { risk: DashboardRiskSummary }) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <CardTitle>Concentration summary</CardTitle>
          <p className="mt-2 text-sm leading-6 text-slate-600">{risk.message}</p>
        </div>
        <Badge tone={risk.concentration_status === "high" ? "danger" : risk.concentration_status === "moderate" ? "warning" : "success"}>
          {risk.concentration_status}
        </Badge>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <SummaryItem label="Largest holding" value={risk.largest_holding_symbol ?? "N/A"} />
        <SummaryItem label="Largest weight" value={formatPercent(risk.largest_holding_weight)} />
        <SummaryItem label="Top 3 weight" value={formatPercent(risk.top_3_weight)} />
        <SummaryItem label="HHI" value={risk.hhi.toFixed(3)} />
      </div>
    </Card>
  );
}

function DataQualityCard({ bundle }: { bundle: DashboardBundleResponse }) {
  const { data_quality: dataQuality } = bundle;
  const warnings =
    dataQuality.warnings.length > 0
      ? dataQuality.warnings
      : dataQuality.missing_price_count || dataQuality.missing_cost_basis_count
        ? [
            `${dataQuality.missing_price_count} holding(s) are missing current prices.`,
            `${dataQuality.missing_cost_basis_count} holding(s) are missing average cost data.`
          ]
        : [];

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle>Missing data warnings</CardTitle>
          <p className="mt-2 text-sm text-slate-600">
            {dataQuality.priced_holdings_count} of {dataQuality.holdings_count} holdings have current prices.
          </p>
        </div>
        <DataStatusBadge status={dataQuality.data_status} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <SummaryItem label="Missing prices" value={String(dataQuality.missing_price_count)} />
        <SummaryItem label="Missing cost" value={String(dataQuality.missing_cost_basis_count)} />
        <SummaryItem label="Stale prices" value={String(dataQuality.stale_price_count)} />
      </div>
      {warnings.length ? (
        <div className="mt-4 grid gap-2">
          {warnings.map((warning) => (
            <p key={warning} className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              {warning}
            </p>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-600">No missing price or cost basis warnings are active.</p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/holdings">
          <Button variant="secondary">Review holdings</Button>
        </Link>
        <Link to="/upload">
          <Button variant="secondary">Upload holdings</Button>
        </Link>
      </div>
    </Card>
  );
}

function ActionItemsCard({ items }: { items: DashboardActionItem[] }) {
  if (!items.length) {
    return <EmptyState title="Backend action items" detail="No backend action items are active for this portfolio." />;
  }

  return (
    <Card>
      <CardTitle>Backend action items</CardTitle>
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-md border border-line p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className={item.priority === "high" ? "text-coral" : "text-gold"} size={16} />
                <div>
                  <p className="text-sm font-semibold text-ink">{item.title}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{item.message}</p>
                  {item.affected_symbols.length ? (
                    <p className="mt-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
                      {item.affected_symbols.join(", ")}
                    </p>
                  ) : null}
                </div>
              </div>
              <Badge tone={item.priority === "high" ? "danger" : item.priority === "medium" ? "warning" : "neutral"}>
                {item.priority}
              </Badge>
            </div>
            {item.recommended_action ? (
              <div className="mt-3">
                <Link to={actionRoute(item.recommended_action)}>
                  <Button variant="secondary">{actionLabel(item.recommended_action)}</Button>
                </Link>
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </Card>
  );
}

function PortfolioHistoryPlaceholder() {
  return (
    <Card>
      <CardTitle>Portfolio value</CardTitle>
      <div className="mt-4 flex h-64 flex-col justify-end gap-3 rounded-md bg-surface p-4">
        <div className="h-20 rounded-md border border-dashed border-line bg-white" />
        <div className="grid grid-cols-5 gap-2">
          <div className="h-12 rounded bg-accent/30" />
          <div className="h-20 rounded bg-gold/40" />
          <div className="h-16 rounded bg-coral/30" />
          <div className="h-28 rounded bg-blue-500/30" />
          <div className="h-24 rounded bg-slate-300" />
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-600">Historical portfolio values are not available yet.</p>
    </Card>
  );
}

function InsightsCard({ rules }: { rules: RuleInsight[] }) {
  const topRules = rules.slice(0, 3);
  if (!topRules.length) {
    return <EmptyState title="Insights" detail="No rule-based insights are active for this portfolio." />;
  }

  return (
    <Card>
      <CardTitle>Top insights</CardTitle>
      <div className="mt-4 grid gap-3">
        {topRules.map((rule) => (
          <InsightRow key={rule.rule_id} rule={rule} />
        ))}
      </div>
    </Card>
  );
}

function MissingDataCard({ rules }: { rules: RuleInsight[] }) {
  if (!rules.length) {
    return <EmptyState title="Missing data" detail="No missing price or cost basis warnings are active." />;
  }

  return (
    <Card>
      <CardTitle>Missing data warnings</CardTitle>
      <div className="mt-4 grid gap-3">
        {rules.map((rule) => (
          <InsightRow key={rule.rule_id} rule={rule} />
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/holdings">
          <Button variant="secondary">Review holdings</Button>
        </Link>
        <Link to="/upload">
          <Button variant="secondary">Upload holdings</Button>
        </Link>
      </div>
    </Card>
  );
}

function InsightRow({ rule }: { rule: RuleInsight }) {
  return (
    <div className="rounded-md border border-line p-3">
      <div className="flex items-start gap-2">
        <AlertTriangle className={rule.severity === "high" ? "text-coral" : "text-gold"} size={16} />
        <div>
          <p className="text-sm font-semibold text-ink">{rule.title}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">{rule.message}</p>
          {rule.affected_symbols.length ? (
            <p className="mt-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
              {rule.affected_symbols.join(", ")}
            </p>
          ) : null}
        </div>
      </div>
    </div>
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
  icon?: typeof WalletCards;
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

function SummaryItem({ label, value }: { label: string; value: string }) {
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

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(value);
}

function getLatestPriceUpdatedAt(holdings: Holding[]) {
  const timestamps = holdings
    .filter((holding) => holding.current_price !== null)
    .map((holding) => new Date(holding.updated_at).getTime())
    .filter((timestamp) => Number.isFinite(timestamp));
  if (!timestamps.length) {
    return null;
  }
  return new Date(Math.max(...timestamps)).toISOString();
}

function kpisAsOf(bundle: DashboardBundleResponse) {
  return bundle.data_status.as_of ? formatDateTime(bundle.data_status.as_of) : formatDateTime(bundle.generated_at);
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function actionRoute(action: NonNullable<DashboardActionItem["recommended_action"]>) {
  switch (action) {
    case "add_holdings":
      return "/holdings";
    case "refresh_prices":
      return "/holdings";
    case "review_holdings":
      return "/holdings";
    case "review_allocation":
      return "/analytics";
    case "review_risk":
      return "/analytics";
    case "review_performance":
      return "/analytics";
    default:
      return "/dashboard";
  }
}

function actionLabel(action: NonNullable<DashboardActionItem["recommended_action"]>) {
  switch (action) {
    case "add_holdings":
      return "Add holdings";
    case "refresh_prices":
      return "Refresh prices";
    case "review_holdings":
      return "Review holdings";
    case "review_allocation":
      return "Review allocation";
    case "review_risk":
      return "Review risk";
    case "review_performance":
      return "Review performance";
    default:
      return "Review";
  }
}

function getDashboardFallbackReason(error: Error | null): DashboardFallbackReason | null {
  if (!error) {
    return null;
  }

  if (error instanceof ApiError) {
    const details = isRecord(error.details) ? error.details : {};
    const feature = typeof details.feature === "string" ? details.feature : "";
    if (error.code === "feature_disabled" || feature === "ENABLE_DASHBOARD_BUNDLE") {
      return { kind: "disabled", message: error.message };
    }
    if (error.status === 0 || error.status === 404) {
      return { kind: "unavailable", message: error.message };
    }
  }

  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
