import { AlertTriangle, BookOpenText, ExternalLink, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

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
  Input,
  LoadingState,
  Table,
  Td,
  Th
} from "../components/ui";
import { useAssetFundamentals, useFundamentals } from "../hooks/useFundamentals";
import { usePortfolios } from "../hooks/usePortfolios";
import { ApiError } from "../services/apiClient";
import type { AssetFundamentals, FundamentalMetrics, PortfolioFundamentals } from "../types/fundamentals";

type MetricDefinition = {
  key: keyof FundamentalMetrics;
  label: string;
  kind: "multiple" | "percent" | "currency" | "number";
};

const VALUATION_METRICS: MetricDefinition[] = [
  { key: "pe_ratio", label: "P/E", kind: "multiple" },
  { key: "forward_pe", label: "Forward P/E", kind: "multiple" },
  { key: "price_to_book", label: "P/B", kind: "multiple" },
  { key: "ev_to_ebitda", label: "EV/EBITDA", kind: "multiple" },
  { key: "peg", label: "PEG", kind: "multiple" },
  { key: "market_cap", label: "Market cap", kind: "currency" }
];
const QUALITY_METRICS: MetricDefinition[] = [
  { key: "roe", label: "ROE", kind: "percent" },
  { key: "roa", label: "ROA", kind: "percent" },
  { key: "operating_margin", label: "Operating margin", kind: "percent" },
  { key: "net_margin", label: "Net margin", kind: "percent" }
];
const GROWTH_METRICS: MetricDefinition[] = [
  { key: "revenue_growth", label: "Revenue growth", kind: "percent" },
  { key: "eps_growth", label: "EPS growth", kind: "percent" }
];
const INCOME_METRICS: MetricDefinition[] = [{ key: "dividend_yield", label: "Dividend yield", kind: "percent" }];
const LEVERAGE_METRICS: MetricDefinition[] = [{ key: "debt_to_equity", label: "Debt/equity", kind: "multiple" }];

export function FundamentalsPage() {
  const [lookupSymbol, setLookupSymbol] = useState("");
  const [submittedSymbol, setSubmittedSymbol] = useState<string | null>(null);
  const portfolios = usePortfolios();
  const selectedPortfolio = portfolios.data?.[0] ?? null;
  const fundamentals = useFundamentals(selectedPortfolio?.id);
  const assetLookup = useAssetFundamentals(submittedSymbol, { enabled: Boolean(submittedSymbol) });

  if (portfolios.isLoading) {
    return <LoadingState label="Loading portfolios" />;
  }

  if (portfolios.isError) {
    return <ErrorState title="Unable to load portfolios" detail={portfolios.error.message} />;
  }

  if (!selectedPortfolio) {
    return (
      <div className="space-y-6">
        <FundamentalsHeader />
        <EmptyState title="No portfolio yet" detail="Create a portfolio before viewing portfolio fundamentals." />
        <Link to="/onboarding">
          <Button>Create portfolio</Button>
        </Link>
      </div>
    );
  }

  const disabledError = getFeatureDisabledError(fundamentals.error ?? assetLookup.error);

  function handleLookup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = lookupSymbol.trim().toUpperCase();
    if (normalized) {
      setSubmittedSymbol(normalized);
    }
  }

  return (
    <div className="space-y-6">
      <FundamentalsHeader />

      {disabledError ? (
        <FeatureDisabledState
          feature="Fundamentals"
          detail="The backend fundamentals feature flag is disabled in this environment."
        />
      ) : null}

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Symbol lookup</CardTitle>
            <p className="mt-1 text-sm text-slate-600">Check backend fundamentals coverage for a single stock.</p>
          </div>
          <Search className="text-accent" size={22} />
        </CardHeader>
        <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={handleLookup}>
          <Input
            value={lookupSymbol}
            onChange={(event) => setLookupSymbol(event.target.value)}
            placeholder="Symbol, for example RELIANCE"
            disabled={Boolean(disabledError) || assetLookup.isLoading}
          />
          <Button type="submit" disabled={Boolean(disabledError) || assetLookup.isLoading}>
            <Search size={16} />
            {assetLookup.isLoading ? "Checking" : "Lookup"}
          </Button>
        </form>
        {assetLookup.isError && !disabledError ? (
          <p className="mt-3 text-sm text-coral">{assetLookup.error.message}</p>
        ) : assetLookup.data ? (
          <AssetLookupResult asset={assetLookup.data} />
        ) : null}
      </Card>

      {fundamentals.isLoading ? (
        <LoadingState label="Loading portfolio fundamentals" />
      ) : fundamentals.isError && !disabledError ? (
        <ErrorState title="Unable to load fundamentals" detail={fundamentals.error.message} />
      ) : fundamentals.data ? (
        <PortfolioFundamentalsContent data={fundamentals.data} currency={selectedPortfolio.base_currency} />
      ) : null}
    </div>
  );
}

function FundamentalsHeader() {
  return (
    <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Fundamentals</p>
        <h1 className="mt-1 text-3xl font-semibold">Portfolio fundamentals</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Backend-provided valuation, quality, growth, income, and leverage metrics with explicit coverage status.
        </p>
      </div>
      <Link to="/holdings">
        <Button variant="secondary">
          <ExternalLink size={16} />
          Holdings
        </Button>
      </Link>
    </section>
  );
}

function PortfolioFundamentalsContent({ data, currency }: { data: PortfolioFundamentals; currency: string }) {
  const mockOrStaleWarning = data.data_status.warning ?? (data.data_status.is_mock ? "Fundamentals are mock data." : null);

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <DataStatusBadge status={data.data_status} />
              <Badge tone={data.coverage.missing_symbols.length ? "warning" : data.coverage.coverage_percent === 100 ? "success" : "neutral"}>
                {formatPercent(data.coverage.coverage_percent)} symbol coverage
              </Badge>
              <Badge tone={data.coverage.weighted_coverage_percent === 100 ? "success" : "warning"}>
                {formatPercent(data.coverage.weighted_coverage_percent)} weighted coverage
              </Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Provider coverage is based on available backend fundamentals for current portfolio holdings.
            </p>
          </div>
          <BookOpenText className="text-accent" size={24} />
        </div>
      </Card>

      {mockOrStaleWarning ? <WarningBanner title="Data status warning" detail={mockOrStaleWarning} /> : null}
      {data.warnings.map((warning) => (
        <WarningBanner key={warning} title="Coverage warning" detail={warning} />
      ))}
      {data.missing_symbols.length ? (
        <WarningBanner title="Missing symbols" detail={data.missing_symbols.join(", ")} />
      ) : null}

      {data.fundamentals.length === 0 ? (
        <EmptyState title="No holdings for fundamentals" detail="Add holdings with symbols before portfolio fundamentals can be calculated." />
      ) : data.coverage.covered_symbols.length === 0 ? (
        <EmptyState title="No covered symbols" detail="The backend returned holdings, but none have available fundamentals metrics." />
      ) : (
        <>
          <section className="grid gap-4 xl:grid-cols-2">
            <MetricGroupCard title="Weighted valuation" metrics={VALUATION_METRICS} values={data.weighted_metrics} currency={currency} />
            <MetricGroupCard title="Weighted quality" metrics={QUALITY_METRICS} values={data.weighted_metrics} currency={currency} />
            <MetricGroupCard title="Weighted growth" metrics={GROWTH_METRICS} values={data.weighted_metrics} currency={currency} />
            <MetricGroupCard title="Weighted income" metrics={INCOME_METRICS} values={data.weighted_metrics} currency={currency} />
            <MetricGroupCard title="Weighted leverage" metrics={LEVERAGE_METRICS} values={data.weighted_metrics} currency={currency} />
          </section>

          <StockFundamentalsTable rows={data.fundamentals} />
        </>
      )}
    </div>
  );
}

function AssetLookupResult({ asset }: { asset: AssetFundamentals }) {
  return (
    <div className="mt-4 rounded-md border border-line bg-surface p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">{asset.symbol}</p>
          <p className="text-sm text-slate-600">{asset.company_name ?? "No company name returned"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <DataStatusBadge status={asset.data_status} compact />
          <Badge tone={asset.coverage.is_complete ? "success" : "warning"}>
            {formatPercent(asset.coverage.coverage_ratio * 100)} metrics
          </Badge>
        </div>
      </div>
      {asset.data_status.warning ? <p className="mt-3 text-sm text-amber-800">{asset.data_status.warning}</p> : null}
    </div>
  );
}

function WarningBanner({ title, detail }: { title: string; detail: string }) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 text-amber-700" size={20} />
        <div>
          <h3 className="text-sm font-semibold text-amber-900">{title}</h3>
          <p className="mt-1 text-sm text-amber-800">{detail}</p>
        </div>
      </div>
    </Card>
  );
}

function MetricGroupCard({
  title,
  metrics,
  values,
  currency
}: {
  title: string;
  metrics: MetricDefinition[];
  values: FundamentalMetrics;
  currency: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <div className="grid gap-3 sm:grid-cols-2">
        {metrics.map((metric) => (
          <MetricBlock
            key={metric.key}
            label={metric.label}
            value={formatMetric(values[metric.key], metric.kind, currency)}
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

function StockFundamentalsTable({ rows }: { rows: AssetFundamentals[] }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Per-stock fundamentals</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Each row shows backend coverage and source status for that symbol.</p>
        </div>
        <Badge>{rows.length} symbols</Badge>
      </CardHeader>
      <Table>
        <thead>
          <tr>
            <Th>Symbol</Th>
            <Th>Valuation</Th>
            <Th>Quality</Th>
            <Th>Growth</Th>
            <Th>Income</Th>
            <Th>Leverage</Th>
            <Th>Coverage</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((asset) => (
            <tr key={asset.symbol}>
              <Td>
                <div>
                  <p className="font-medium text-ink">{asset.symbol}</p>
                  <p className="text-xs text-slate-500">{asset.company_name ?? "N/A"}</p>
                </div>
              </Td>
              <Td>
                <MetricStack
                  items={[
                    ["P/E", formatMetric(asset.metrics.pe_ratio, "multiple", asset.currency)],
                    ["P/B", formatMetric(asset.metrics.price_to_book, "multiple", asset.currency)],
                    ["M cap", formatMetric(asset.metrics.market_cap, "currency", asset.currency)]
                  ]}
                />
              </Td>
              <Td>
                <MetricStack
                  items={[
                    ["ROE", formatMetric(asset.metrics.roe, "percent", asset.currency)],
                    ["Op margin", formatMetric(asset.metrics.operating_margin, "percent", asset.currency)]
                  ]}
                />
              </Td>
              <Td>
                <MetricStack
                  items={[
                    ["Revenue", formatMetric(asset.metrics.revenue_growth, "percent", asset.currency)],
                    ["EPS", formatMetric(asset.metrics.eps_growth, "percent", asset.currency)]
                  ]}
                />
              </Td>
              <Td>{formatMetric(asset.metrics.dividend_yield, "percent", asset.currency)}</Td>
              <Td>{formatMetric(asset.metrics.debt_to_equity, "multiple", asset.currency)}</Td>
              <Td>
                <div className="space-y-1">
                  <Badge tone={asset.coverage.is_complete ? "success" : "warning"}>
                    {formatPercent(asset.coverage.coverage_ratio * 100)}
                  </Badge>
                  {asset.coverage.missing_metrics.length ? (
                    <p className="text-xs text-amber-700">{asset.coverage.missing_metrics.length} missing metrics</p>
                  ) : null}
                </div>
              </Td>
              <Td>
                <DataStatusBadge status={asset.data_status} compact />
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function MetricStack({ items }: { items: [string, string][] }) {
  return (
    <div className="space-y-1 text-xs">
      {items.map(([label, value]) => (
        <div key={label} className="flex min-w-24 justify-between gap-3">
          <span className="text-slate-500">{label}</span>
          <span className="font-medium text-ink">{value}</span>
        </div>
      ))}
    </div>
  );
}

function getFeatureDisabledError(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const details = typeof error.details === "object" && error.details !== null ? error.details : {};
  const feature = "feature" in details ? details.feature : null;
  return error.code === "feature_disabled" || feature === "ENABLE_FUNDAMENTALS" ? error : null;
}

function formatMetric(value: number | null, kind: MetricDefinition["kind"], currency: string) {
  if (value === null) {
    return "N/A";
  }
  if (kind === "percent") {
    return formatPercent(value * 100);
  }
  if (kind === "currency") {
    return formatCompactCurrency(value, currency);
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  return `${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value)}%`;
}

function formatCompactCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 2
  }).format(value);
}
